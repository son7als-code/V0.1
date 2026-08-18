"""Character extraction and stable identity management."""
from __future__ import annotations

from app.core.validator import validate_character


def _key(name: str) -> str:
    return " ".join(name.casefold().split())


class CharacterManager:
    def __init__(self, existing: list[dict] | None = None) -> None:
        self.characters: list[dict] = []
        self._by_name: dict[str, dict] = {}
        for character in existing or []:
            self.add_or_reuse(character)

    def add_or_reuse(self, character: dict) -> dict:
        name = character.get("name", "")
        existing = self._by_name.get(_key(name))
        if existing:
            return existing
        if not character.get("id"):
            character = {**character, "id": f"char_{len(self.characters) + 1:03d}"}
        validate_character(character)
        self.characters.append(character)
        self._by_name[_key(character["name"])] = character
        return character

    def merge_provider_characters(self, provider_characters: list[dict]) -> list[dict]:
        return [self.add_or_reuse(character) for character in provider_characters]

    def find_by_name(self, name: str) -> dict | None:
        return self._by_name.get(_key(name))
