"""Live HTTP integration test for security and Redis-backed reliability."""
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from uuid import uuid4


BASE_URL = "http://127.0.0.1:8765"
API_KEY = "ci-agent-key"


def request(path: str, method: str = "GET", body: dict | None = None, key: str | None = None):
    headers = {}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if key:
        headers["X-API-Key"] = key
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


def wait_until_ready() -> None:
    for _ in range(50):
        try:
            status, data = request("/ready")
            if status == 200 and data.get("redis") == "connected":
                return
        except (OSError, ValueError):
            pass
        time.sleep(0.2)
    raise AssertionError("API did not become ready with Redis")


def main() -> int:
    env = os.environ.copy()
    env.update(
        {
            "PORT": "8765",
            "ENVIRONMENT": "test",
            "AGENT_API_KEY": API_KEY,
            "OPENAI_API_KEY": "",
            "REDIS_URL": "redis://127.0.0.1:6379/15",
            "RATE_LIMIT_PER_MINUTE": "3",
            "MONTHLY_BUDGET_USD": "10",
        }
    )
    process = subprocess.Popen(
        [sys.executable, "-m", "app.main"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=(
            subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        ),
    )
    try:
        wait_until_ready()
        assert request("/health")[0] == 200

        status, _ = request(
            "/ask",
            "POST",
            {"user_id": "unauthorized", "question": "hello"},
        )
        assert status == 401, f"Expected 401, got {status}"

        user_id = f"ci-{uuid4().hex[:8]}"
        status, first = request(
            "/ask",
            "POST",
            {"user_id": user_id, "question": "What is the SLA for a P1 incident?"},
            API_KEY,
        )
        assert status == 200
        assert first["history_count"] == 2

        status, follow_up = request(
            "/ask",
            "POST",
            {"user_id": user_id, "question": "Summarize that previous answer"},
            API_KEY,
        )
        assert status == 200
        assert follow_up["route"] == "conversation_context"
        assert follow_up["history_count"] == 4

        status, _ = request(
            "/ask",
            "POST",
            {"user_id": user_id, "question": "One more request"},
            API_KEY,
        )
        assert status == 200
        status, _ = request(
            "/ask",
            "POST",
            {"user_id": user_id, "question": "This request must be limited"},
            API_KEY,
        )
        assert status == 429, f"Expected 429, got {status}"

        print("[PASS] /health and /ready")
        print("[PASS] API key flow: 401 then 200")
        print("[PASS] Redis history persisted across follow-up")
        print("[PASS] Rate limiter returned 429")
    finally:
        if os.name == "nt":
            os.kill(process.pid, signal.CTRL_BREAK_EVENT)
        else:
            process.terminate()
        try:
            return_code = process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            raise AssertionError("Graceful shutdown exceeded 10 seconds")
        logs = process.stdout.read() if process.stdout else ""
        if return_code != 0 and os.name != "nt":
            raise AssertionError(f"App shutdown returned {return_code}\n{logs}")
        if "graceful_shutdown" not in logs:
            raise AssertionError(f"Graceful shutdown log not found\n{logs}")
        print("[PASS] Graceful shutdown completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
