"""Configuration loaded from environment variables only."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(RuntimeError):
    """Raised when environment configuration is invalid."""


@dataclass(frozen=True)
class AppConfig:
    projects_dir: Path = Path("projects")
    ai_api_key: str | None = None
    ai_model: str | None = None
    ai_base_url: str | None = None
    timeout_seconds: int = 30
    debug: bool = False

    @classmethod
    def from_env(cls) -> "AppConfig":
        timeout_raw = os.getenv("AI_TIMEOUT_SECONDS", "30")
        try:
            timeout_seconds = int(timeout_raw)
        except ValueError as exc:
            raise ConfigError("AI_TIMEOUT_SECONDS must be a positive integer.") from exc
        if timeout_seconds <= 0:
            raise ConfigError("AI_TIMEOUT_SECONDS must be a positive integer.")
        return cls(
            projects_dir=Path(os.getenv("PROJECTS_DIR", "projects")),
            ai_api_key=os.getenv("AI_API_KEY") or None,
            ai_model=os.getenv("AI_MODEL") or None,
            ai_base_url=os.getenv("AI_BASE_URL") or None,
            timeout_seconds=timeout_seconds,
            debug=os.getenv("DEBUG", "").lower() in {"1", "true", "yes"},
        )
