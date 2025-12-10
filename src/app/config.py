# src/app/config.py

"""
Config module:
- .env file se saare env vars load karta hai
- 'settings' object expose karta hai jo baaki project me use hoga

Ye file sabse pehle import honi chahiye jahan bhi config chahiye.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# .env file load karo (project root pe)
load_dotenv()


@dataclass
class Settings:
    # ---- LLM / Groq ----
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")

    # ---- Postgres ----
    POSTGRES_DSN: str | None = os.getenv("POSTGRES_DSN")

    # ---- Redis ----
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # ---- Misc (future use) ----
    # e.g. LOG_LEVEL, GMAIL_USER, etc.
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
