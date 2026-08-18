"""Provider interface for external AI services."""
from __future__ import annotations

from abc import ABC, abstractmethod


class ProviderError(RuntimeError):
    """Readable provider failure that does not expose secrets."""


class BaseAIProvider(ABC):
    @abstractmethod
    def generate_story(self, request: dict) -> dict:
        """Return structured story JSON with title, summary, characters, scenes."""

    @abstractmethod
    def generate_scene(self, request: dict, scene_id: str) -> dict:
        """Regenerate one scene only."""
