"""Automated rubric for Day 12 Parts 03, 04, and 05."""
import argparse
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent
APP = ROOT / "06-lab-complete"


class Grader:
    def __init__(self, title: str):
        self.title = title
        self.score = 0
        self.total = 0

    def check(self, label: str, condition: bool, points: int) -> None:
        self.total += points
        if condition:
            self.score += points
        print(f"[{'PASS' if condition else 'FAIL'}] {label} ({points} points)")

    def finish(self) -> bool:
        print(f"\n{self.title}: {self.score}/{self.total}")
        return self.score == self.total


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def grade_part_03() -> bool:
    grader = Grader("Part 03 - Cloud Deployment")
    dockerfile = text(APP / "Dockerfile")
    render = yaml.safe_load(text(ROOT / "render.yaml"))
    railway = text(APP / "railway.toml")
    cloudbuild = yaml.safe_load(
        text(ROOT / "03-cloud-deployment/production-cloud-run/cloudbuild.yaml")
    )

    grader.check("Multi-stage Dockerfile", "AS builder" in dockerfile, 4)
    grader.check("Non-root runtime user", "USER agent" in dockerfile, 3)
    grader.check("Docker health check", "HEALTHCHECK" in dockerfile, 3)
    grader.check("Render Blueprint web service", render["services"][0]["type"] == "web", 4)
    grader.check(
        "Render health endpoint",
        render["services"][0].get("healthCheckPath") == "/health",
        3,
    )
    grader.check(
        "Render Redis/Key Value service",
        any(service.get("type") == "keyvalue" for service in render["services"]),
        3,
    )
    grader.check("Railway health check configured", 'healthcheckPath = "/health"' in railway, 3)
    step_ids = {step.get("id") for step in cloudbuild.get("steps", [])}
    grader.check("Cloud Build test/build/push/deploy stages", {"test", "build", "push", "deploy"} <= step_ids, 4)
    grader.check("Deployment documentation", (APP / "DEPLOYMENT.md").exists(), 3)
    workflow = text(ROOT / ".github/workflows/day12-cicd.yml")
    grader.check("GitHub Actions CD job", "deploy-render:" in workflow, 3)
    grader.check("Public deployment smoke test", "Demo deployed endpoints" in workflow, 3)
    return grader.finish()


def grade_part_04() -> bool:
    grader = Grader("Part 04 - API Gateway & Security")
    main = text(APP / "app/main.py")
    auth = text(APP / "app/auth.py")
    limiter = text(APP / "app/rate_limiter.py")
    guard = text(APP / "app/cost_guard.py")
    config = text(APP / "app/config.py")

    grader.check("X-API-Key authentication", "X-API-Key" in auth, 5)
    grader.check("Unauthorized requests return 401", "status_code=401" in auth, 4)
    grader.check("Protected /ask endpoint", "Depends(verify_api_key)" in main, 4)
    grader.check("Redis-backed rate limiting", "zremrangebyscore" in limiter and "429" in limiter, 5)
    grader.check("Cost guard returns 402", "402" in guard and "monthly_budget_usd" in guard, 5)
    grader.check("Input validation limits", "max_length=2000" in main, 3)
    grader.check("Secrets loaded from environment", "os.getenv" in config, 3)
    grader.check("No real .env tracked by template", "OPENAI_API_KEY=" in text(APP / ".env.example"), 1)
    workflow = text(ROOT / ".github/workflows/day12-cicd.yml")
    grader.check("CI lint stage", "ruff check" in workflow, 3)
    grader.check("Unit test coverage stage", "coverage report" in workflow, 3)
    return grader.finish()


def grade_part_05() -> bool:
    grader = Grader("Part 05 - Scaling & Reliability")
    main = text(APP / "app/main.py")
    storage = text(APP / "app/storage.py")
    compose = yaml.safe_load(text(APP / "docker-compose.yml"))

    grader.check("/health liveness endpoint", '@app.get("/health")' in main, 4)
    grader.check("/ready readiness endpoint", '@app.get("/ready")' in main, 4)
    grader.check("Lifespan graceful shutdown", "graceful_shutdown" in main and "close_storage" in main, 5)
    grader.check("Redis-backed conversation state", "lrange" in storage and "rpush" in storage, 5)
    grader.check("Conversation TTL", "expire" in storage and "conversation_ttl_seconds" in storage, 3)
    grader.check("Agent depends on healthy Redis", compose["services"]["agent"]["depends_on"]["redis"]["condition"] == "service_healthy", 4)
    grader.check("Redis persistence volume", bool(compose["services"]["redis"].get("volumes")), 3)
    grader.check("Container restart policy", compose["services"]["agent"].get("restart") == "unless-stopped", 2)
    return grader.finish()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--part", choices=["03", "04", "05", "all"], default="all")
    args = parser.parse_args()
    graders = {
        "03": grade_part_03,
        "04": grade_part_04,
        "05": grade_part_05,
    }
    selected = graders if args.part == "all" else {args.part: graders[args.part]}
    passed = all(grade() for grade in selected.values())
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
