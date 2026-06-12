"""Unit tests for the production Helpdesk Supervisor-Worker agent."""
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import redis
from fastapi import HTTPException

from app import cost_guard, rate_limiter, storage
from app.auth import verify_api_key
from app.helpdesk_agent import run_helpdesk_agent


class HelpdeskAgentTests(unittest.TestCase):
    def test_p1_question_routes_to_retrieval(self):
        result = run_helpdesk_agent("What is the SLA for a P1 incident?")

        self.assertEqual(result.route, "retrieval_worker")
        self.assertIn("15 minutes", result.answer)
        self.assertIn("sla_p1_2026.txt", result.sources)

    def test_refund_question_routes_to_policy(self):
        result = run_helpdesk_agent("Can I refund a Flash Sale license?")

        self.assertEqual(result.route, "policy_tool_worker")
        self.assertIn("not refundable", result.answer)

    def test_openai_failure_uses_safe_fallback(self):
        error = HTTPError(
            "https://api.openai.com/v1/responses",
            429,
            "quota",
            {},
            None,
        )
        with patch("app.helpdesk_agent.urlopen", side_effect=error):
            result = run_helpdesk_agent(
                "Help me debug an import error",
                openai_api_key="test-key",
                openai_model="gpt-4o-mini",
            )

        self.assertEqual(result.llm_status, "openai_quota_or_rate_limit")
        self.assertTrue(result.answer)

    def test_cost_guard_returns_402_when_budget_is_exceeded(self):
        with (
            patch.object(cost_guard.settings, "monthly_budget_usd", 0.000001),
            patch(
                "app.cost_guard.redis_client",
                side_effect=redis.RedisError("offline"),
            ),
        ):
            with self.assertRaisesRegex(Exception, "402"):
                cost_guard.check_and_record_cost("budget-test", 1000, 1000)

    def test_api_key_authentication(self):
        with patch("app.auth.settings.agent_api_key", "expected-key"):
            self.assertEqual(verify_api_key("expected-key"), "expected-key")
            with self.assertRaises(HTTPException) as context:
                verify_api_key("wrong-key")
        self.assertEqual(context.exception.status_code, 401)

    def test_rate_limit_local_fallback_returns_429(self):
        user_id = "rate-limit-test"
        rate_limiter._local_windows.pop(user_id, None)
        with (
            patch.object(rate_limiter.settings, "rate_limit_per_minute", 2),
            patch(
                "app.rate_limiter.redis_client",
                side_effect=redis.RedisError("offline"),
            ),
        ):
            rate_limiter.check_rate_limit(user_id)
            rate_limiter.check_rate_limit(user_id)
            with self.assertRaises(HTTPException) as context:
                rate_limiter.check_rate_limit(user_id)
        self.assertEqual(context.exception.status_code, 429)

    def test_storage_local_fallback_preserves_history(self):
        user_id = "storage-test"
        storage._local_history.pop(user_id, None)
        with patch(
            "app.storage.redis_client",
            side_effect=redis.RedisError("offline"),
        ):
            storage.append_history(user_id, {"role": "user", "content": "hello"})
            history = storage.get_history(user_id)
        self.assertEqual(history, [{"role": "user", "content": "hello"}])


if __name__ == "__main__":
    unittest.main()
