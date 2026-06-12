"""Environment-based settings for the production Helpdesk Agent."""
import logging
import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    app_name: str = field(
        default_factory=lambda: os.getenv("APP_NAME", "Production Helpdesk Agent")
    )
    app_version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "2.0.0"))
    agent_source: str = field(
        default_factory=lambda: os.getenv(
            "AGENT_SOURCE",
            "VinUni Day 9 CS + IT Helpdesk Supervisor-Worker",
        )
    )

    agent_api_key: str = field(
        default_factory=lambda: os.getenv("AGENT_API_KEY", "dev-key-change-me")
    )
    openai_api_key: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "")
    )
    openai_model: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    )
    allowed_origins: list[str] = field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
            if origin.strip()
        ]
    )

    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    )
    monthly_budget_usd: float = field(
        default_factory=lambda: float(os.getenv("MONTHLY_BUDGET_USD", "10.0"))
    )
    redis_url: str = field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    conversation_ttl_seconds: int = field(
        default_factory=lambda: int(os.getenv("CONVERSATION_TTL_SECONDS", "86400"))
    )
    conversation_max_messages: int = field(
        default_factory=lambda: int(os.getenv("CONVERSATION_MAX_MESSAGES", "20"))
    )

    def validate(self):
        if self.environment == "production" and self.agent_api_key == "dev-key-change-me":
            raise ValueError("AGENT_API_KEY must be changed in production")
        if self.rate_limit_per_minute < 1:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be positive")
        if self.monthly_budget_usd <= 0:
            raise ValueError("MONTHLY_BUDGET_USD must be positive")
        logging.getLogger(__name__).info(
            "Configuration loaded for environment=%s", self.environment
        )
        return self


settings = Settings().validate()
