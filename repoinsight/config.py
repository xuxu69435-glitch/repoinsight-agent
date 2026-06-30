"""Project-wide configuration constants and environment loading."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field

DEFAULT_MAX_DEPTH = 3
DEFAULT_MAX_FILE_CHARS = 12_000
DEFAULT_MAX_SEARCH_RESULTS = 50
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"

IGNORED_DIRECTORIES = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        "dist",
        "build",
        ".next",
        ".idea",
        ".vscode",
    }
)


class AppConfig(BaseModel):
    """Application settings loaded from environment variables."""

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = DEFAULT_OPENAI_MODEL
    temperature: float = Field(default=0.0, ge=0.0)


def load_config(*, load_env: bool = True) -> AppConfig:
    """Load application configuration from .env and process environment."""
    if load_env:
        load_dotenv()

    return AppConfig(
        openai_api_key=_empty_to_none(os.getenv("OPENAI_API_KEY")),
        openai_base_url=_empty_to_none(os.getenv("OPENAI_BASE_URL")),
        openai_model=os.getenv("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL,
        temperature=_parse_temperature(os.getenv("OPENAI_TEMPERATURE")),
    )


def _empty_to_none(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return value.strip()


def _parse_temperature(value: str | None) -> float:
    if value is None or not value.strip():
        return 0.0
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError("OPENAI_TEMPERATURE must be a number.") from exc
