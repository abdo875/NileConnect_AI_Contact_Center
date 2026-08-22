from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings
from typing import List

# ── Backend root directory (absolute, regardless of CWD) ──────────────────────
# This file lives at: backend/app/core/config.py
# BACKEND_ROOT  →  backend/
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # App
    APP_NAME: str = "NileConnect AI Contact Center"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/nileconnect"
    # JWT
    SECRET_KEY: str = "change-me-to-a-long-random-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:8501"

    # Storage — relative values from .env are resolved against BACKEND_ROOT
    UPLOAD_DIR: str = "uploads"

    # URLs
    FRONTEND_URL: str = "http://localhost:8501"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    # Public base URL used by Twilio webhooks — set to your ngrok/tunnel URL in production
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    # ── AI / LLM ──────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    WHISPER_MODEL: str = "whisper-large-v3-turbo"
    TAVILY_API_KEY: str = ""

    # ── RAG ───────────────────────────────────────────────────────────────────
    RAG_DOCS_DIR: str = "uploads/rag_docs"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ── Resolved absolute paths ────────────────────────────────────────────────
    @property
    def upload_dir_abs(self) -> str:
        """Absolute path to the uploads directory."""
        p = Path(self.UPLOAD_DIR)
        return str(p if p.is_absolute() else _BACKEND_ROOT / p)

    @property
    def rag_docs_dir_abs(self) -> str:
        """Absolute path to the RAG documents directory."""
        p = Path(self.RAG_DOCS_DIR)
        return str(p if p.is_absolute() else _BACKEND_ROOT / p)

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    # ── Telephony — Vonage ────────────────────────────────────────────────────────
    # Application ID (public) — safe to put in .env.example
    VONAGE_APPLICATION_ID: str = ""
    # Path to the private key FILE — content is never stored in env
    VONAGE_PRIVATE_KEY_PATH: str = ""
    # Fixed caller/callee numbers — not the customer's number
    VONAGE_FROM_NUMBER: str = ""
    VONAGE_TO_NUMBER: str = ""

    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "ignore"}


settings = Settings()

