"""Production API for the Day 9 CS + IT Helpdesk Supervisor-Worker agent."""
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import check_and_record_cost, get_monthly_spend
from app.helpdesk_agent import run_helpdesk_agent
from app.rate_limiter import check_rate_limit
from app.storage import (
    append_history,
    close_storage,
    get_history,
    redis_available,
)


logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)
START_TIME = time.time()
STATIC_DIR = Path(__file__).resolve().parent / "static"
_is_ready = False
_request_count = 0
_error_count = 0


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _is_ready
    logger.info(json.dumps({"event": "startup", "agent": settings.agent_source}))
    _is_ready = True
    yield
    # Uvicorn catches SIGTERM and enters this lifespan shutdown block.
    _is_ready = False
    logger.info(json.dumps({"event": "graceful_shutdown"}))
    close_storage()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Productionized Day 9 CS + IT Helpdesk Supervisor-Worker agent.",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count, _error_count
    started = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
    except Exception:
        _error_count += 1
        raise
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    logger.info(
        json.dumps(
            {
                "event": "request",
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.time() - started) * 1000, 1),
            }
        )
    )
    return response


class AskRequest(BaseModel):
    user_id: str = Field(default="demo-user", min_length=1, max_length=100)
    question: str = Field(..., min_length=1, max_length=2000)


class AskResponse(BaseModel):
    user_id: str
    question: str
    answer: str
    route: str
    route_reason: str
    sources: list[str]
    confidence: float
    workers_called: list[str]
    trace_id: str
    history_count: int
    timestamp: str


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/ask", response_model=AskResponse)
def ask_agent(body: AskRequest, _api_key: str = Depends(verify_api_key)):
    check_rate_limit(body.user_id)
    history = get_history(body.user_id)
    input_tokens = max(1, len(body.question.split()) * 2)
    check_and_record_cost(body.user_id, input_tokens, 0)

    result = run_helpdesk_agent(
        body.question,
        history,
        openai_api_key=settings.openai_api_key,
        openai_model=settings.openai_model,
    )
    output_tokens = max(1, len(result.answer.split()) * 2)
    check_and_record_cost(body.user_id, 0, output_tokens)

    now = datetime.now(timezone.utc).isoformat()
    append_history(
        body.user_id,
        {"role": "user", "content": body.question, "timestamp": now},
    )
    append_history(
        body.user_id,
        {"role": "assistant", "content": result.answer, "timestamp": now},
    )
    logger.info(
        json.dumps(
            {
                "event": "agent_completed",
                "user_id": body.user_id,
                "trace_id": result.trace_id,
                "route": result.route,
                "workers": result.workers_called,
            }
        )
    )
    return AskResponse(
        user_id=body.user_id,
        question=body.question,
        answer=result.answer,
        route=result.route,
        route_reason=result.route_reason,
        sources=result.sources,
        confidence=result.confidence,
        workers_called=result.workers_called,
        trace_id=result.trace_id,
        history_count=len(history) + 2,
        timestamp=now,
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": settings.app_version,
        "agent": "support-supervisor-worker",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
    }


@app.get("/ready")
def ready():
    if not _is_ready:
        raise HTTPException(503, "Agent is not ready")
    return {
        "ready": True,
        "redis": "connected" if redis_available() else "local-fallback",
        "llm": "configured" if settings.openai_api_key else "rule-fallback",
    }


@app.get("/metrics")
def metrics(user_id: str = "demo-user", _api_key: str = Depends(verify_api_key)):
    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "error_count": _error_count,
        "monthly_spend_usd": round(get_monthly_spend(user_id), 6),
        "monthly_budget_usd": settings.monthly_budget_usd,
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
