"""Small validation helpers for project, story, character, and scene data."""
from __future__ import annotations


class ValidationError(ValueError):
    """Raised when user/provider data is incomplete or malformed."""


def require_fields(data: dict, fields: list[str], label: str) -> None:
    missing = [field for field in fields if field not in data or data[field] is None]
    if missing:
        raise ValidationError(f"{label} is missing required field(s): {', '.join(missing)}")


def validate_project_request(data: dict) -> None:
    require_fields(data, ["project_name", "story_title", "story_topic", "language", "target_duration", "genre", "visual_style", "number_of_scenes"], "Project request")
    if int(data["number_of_scenes"]) < 1:
        raise ValidationError("Project request number_of_scenes must be at least 1")


def validate_story(data: dict) -> None:
    require_fields(data, ["title", "summary", "characters", "scenes"], "Story")
    if not isinstance(data["characters"], list):
        raise ValidationError("Story characters must be a list")
    if not isinstance(data["scenes"], list):
        raise ValidationError("Story scenes must be a list")


def validate_character(data: dict) -> None:
    require_fields(data, ["id", "name", "role", "appearance", "clothing", "personality", "visual_identity"], "Character")


def validate_scene(data: dict) -> None:
    require_fields(data, ["id", "order", "duration_seconds", "location", "time_of_day", "characters", "action", "narration", "dialogue", "image_prompt", "video_prompt", "negative_prompt"], "Scene")
    if not isinstance(data["characters"], list):
        raise ValidationError("Scene characters must be a list")
    if not isinstance(data["dialogue"], list):
        raise ValidationError("Scene dialogue must be a list")
    if int(data["duration_seconds"]) <= 0:
        raise ValidationError("Scene duration_seconds must be positive")
