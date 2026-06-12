"""Production adaptation of the Day 9 CS + IT Helpdesk agent."""
import json
import logging
from dataclasses import dataclass
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

logger = logging.getLogger(__name__)
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


KNOWLEDGE_BASE = [
    {
        "source": "sla_p1_2026.txt",
        "keywords": {"p1", "sla", "ticket", "escalation", "incident"},
        "text": (
            "P1 incidents require an initial response within 15 minutes and a "
            "target resolution within 4 hours. Escalate to the senior engineer "
            "team when there is no response after 10 minutes."
        ),
    },
    {
        "source": "policy_refund_v4.txt",
        "keywords": {"refund", "return", "flash sale", "license", "subscription"},
        "text": (
            "Refund requests are accepted within 7 working days for defective, "
            "unused products. Flash Sale orders, activated license keys, and "
            "subscriptions are excluded from refunds."
        ),
    },
    {
        "source": "access_control_sop.txt",
        "keywords": {"access", "permission", "level 3", "admin", "emergency"},
        "text": (
            "Level 3 admin access requires approval from the line manager, IT "
            "administrator, and IT Security. Level 3 has no emergency bypass."
        ),
    },
    {
        "source": "it_helpdesk_faq.txt",
        "keywords": {"password", "login", "vpn", "email", "helpdesk"},
        "text": (
            "For login failures, verify account status, reset the password, and "
            "check VPN connectivity before creating a helpdesk ticket."
        ),
    },
]


@dataclass
class AgentResult:
    answer: str
    route: str
    route_reason: str
    sources: list[str]
    confidence: float
    workers_called: list[str]
    trace_id: str
    latency_ms: int
    llm_status: str


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _supervisor(question: str) -> tuple[str, str, bool]:
    text = _normalize(question)
    policy_terms = ("refund", "return", "flash sale", "license", "access", "level 3")
    risk_terms = ("err-", "unknown error", "khong ro", "emergency")
    if any(term in text for term in risk_terms) and "err-" in text:
        return "human_review", "unknown high-risk error requires review", True
    if any(term in text for term in policy_terms):
        return "policy_tool_worker", "policy or access-control intent detected", False
    return "retrieval_worker", "knowledge retrieval intent detected", False


def _retrieve(question: str, top_k: int = 2) -> list[dict]:
    terms = set(_normalize(question).replace("?", "").split())
    scored = []
    for document in KNOWLEDGE_BASE:
        score = len(terms.intersection(document["keywords"]))
        if score:
            scored.append({**document, "score": min(0.95, 0.65 + score * 0.1)})
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k] or [{**KNOWLEDGE_BASE[3], "score": 0.55}]


def _policy_check(question: str) -> list[str]:
    text = _normalize(question)
    exceptions = []
    if "flash sale" in text:
        exceptions.append("Flash Sale orders are not refundable.")
    if "license" in text or "subscription" in text:
        exceptions.append("Activated digital products are not refundable.")
    if "level 3" in text or "admin access" in text:
        exceptions.append(
            "Level 3 requires Line Manager, IT Admin, and IT Security approval."
        )
    return exceptions


def _extract_output_text(response: dict) -> str:
    direct_text = response.get("output_text")
    if direct_text:
        return direct_text.strip()
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                return content["text"].strip()
    return ""


def _generate_llm_answer(
    question: str,
    history: list[dict],
    evidence: str,
    policy_exceptions: list[str],
    api_key: str,
    model: str,
) -> tuple[str, str]:
    recent_history = history[-6:]
    context = "\n".join(
        f"{message.get('role', 'user')}: {message.get('content', '')}"
        for message in recent_history
    )
    policy_text = "\n".join(policy_exceptions) or "No policy exception detected."
    payload = {
        "model": model,
        "instructions": (
            "You are a CS and IT Helpdesk Supervisor-Worker agent. Answer the "
            "user's question directly and practically in the same language as "
            "the user. Use supplied company evidence for policy-specific claims. "
            "If the evidence does not contain a company policy answer, say so "
            "briefly, then provide safe general technical guidance. Never invent "
            "company rules, credentials, or completed actions. Keep the answer "
            "under 250 words."
        ),
        "input": (
            f"Recent conversation:\n{context or '(none)'}\n\n"
            f"Retrieved company evidence:\n{evidence}\n\n"
            f"Policy checks:\n{policy_text}\n\n"
            f"Current user question:\n{question}"
        ),
        "max_output_tokens": 500,
    }
    request = Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            answer = _extract_output_text(json.load(response))
    except HTTPError as exc:
        if exc.code == 401:
            status = "invalid_openai_key"
        elif exc.code == 429:
            status = "openai_quota_or_rate_limit"
        elif exc.code == 404:
            status = "openai_model_unavailable"
        else:
            status = f"openai_http_{exc.code}"
        logger.warning("OpenAI synthesis unavailable; using rule fallback: %s", exc)
        return "", status
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("OpenAI synthesis unavailable; using rule fallback: %s", exc)
        return "", "openai_connection_error"
    if not answer:
        return "", "openai_empty_response"
    return answer, "openai_success"


def run_helpdesk_agent(
    question: str,
    history: list[dict] | None = None,
    openai_api_key: str = "",
    openai_model: str = "gpt-4o-mini",
) -> AgentResult:
    start = perf_counter()
    normalized = _normalize(question)
    follow_up_terms = ("that", "again", "previous", "summarize", "nhac lai", "tom tat")
    previous_answers = [
        message.get("content", "")
        for message in history or []
        if message.get("role") == "assistant"
    ]
    if previous_answers and any(term in normalized for term in follow_up_terms):
        previous = previous_answers[-1]
        answer = f"Summary of the previous answer: {previous}"
        return AgentResult(
            answer=answer,
            route="conversation_context",
            route_reason="follow-up question resolved from Redis conversation history",
            sources=[],
            confidence=0.9,
            workers_called=["supervisor", "conversation_history", "synthesis_worker"],
            trace_id=f"trace-{uuid4().hex[:12]}",
            latency_ms=int((perf_counter() - start) * 1000),
            llm_status="conversation_context",
        )

    route, reason, hitl = _supervisor(question)
    workers = ["supervisor"]
    if hitl:
        workers.append("human_review")

    documents = _retrieve(question)
    workers.append("retrieval_worker")
    exceptions = []
    if route == "policy_tool_worker":
        exceptions = _policy_check(question)
        workers.append("policy_tool_worker")

    evidence = " ".join(document["text"] for document in documents)
    if exceptions:
        answer = f"{' '.join(exceptions)} Supporting policy: {evidence}"
    else:
        answer = evidence

    sources = list(dict.fromkeys(document["source"] for document in documents))
    confidence = round(sum(document["score"] for document in documents) / len(documents), 2)
    llm_status = "openai_not_configured"
    if openai_api_key:
        llm_answer, llm_status = _generate_llm_answer(
            question,
            history or [],
            evidence,
            exceptions,
            openai_api_key,
            openai_model,
        )
        if llm_answer:
            answer = llm_answer
            workers.append("openai_synthesis_worker")
            confidence = max(confidence, 0.8)
    workers.append("synthesis_worker")
    return AgentResult(
        answer=answer,
        route=route,
        route_reason=reason,
        sources=sources,
        confidence=confidence,
        workers_called=workers,
        trace_id=f"trace-{uuid4().hex[:12]}",
        latency_ms=int((perf_counter() - start) * 1000),
        llm_status=llm_status,
    )
