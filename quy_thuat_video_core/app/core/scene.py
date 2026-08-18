"""Scene normalization, validation, and independent retry support."""
from __future__ import annotations

from app.core.character import CharacterManager
from app.core.prompt import PromptBuilder
from app.core.validator import ValidationError, validate_scene


class SceneManager:
    def __init__(self, prompt_builder: PromptBuilder | None = None) -> None:
        self.prompt_builder = prompt_builder or PromptBuilder()

    def normalize_scenes(self, raw_scenes: list[dict], characters: CharacterManager, visual_style: str) -> list[dict]:
        scenes: list[dict] = []
        for index, raw_scene in enumerate(raw_scenes, start=1):
            scene = self.normalize_scene(raw_scene, index, characters, visual_style)
            scenes.append(scene)
        return scenes

    def normalize_scene(self, raw_scene: dict, index: int, characters: CharacterManager, visual_style: str) -> dict:
        scene_id = raw_scene.get("id") or f"scene_{index:03d}"
        scene_character_ids = []
        scene_character_profiles = []
        for name_or_id in raw_scene.get("characters", []):
            profile = characters.find_by_name(str(name_or_id))
            if profile:
                scene_character_ids.append(profile["id"])
                scene_character_profiles.append(profile)
            else:
                raise ValidationError(f"Scene {scene_id} references missing character: {name_or_id}")
        scene = {
            "id": scene_id,
            "order": int(raw_scene.get("order", index)),
            "duration_seconds": int(raw_scene.get("duration_seconds", 12)),
            "location": raw_scene.get("location", "Unspecified location"),
            "time_of_day": raw_scene.get("time_of_day", "unspecified time"),
            "characters": scene_character_ids,
            "action": raw_scene.get("action", "No action provided"),
            "narration": raw_scene.get("narration", ""),
            "dialogue": raw_scene.get("dialogue", []),
            "image_prompt": raw_scene.get("image_prompt", ""),
            "video_prompt": raw_scene.get("video_prompt", ""),
            "negative_prompt": raw_scene.get("negative_prompt", ""),
        }
        prompts = self.prompt_builder.build(scene, scene_character_profiles, visual_style)
        for key, value in prompts.items():
            scene[key] = scene[key] or value
        validate_scene(scene)
        return scene

    def replace_scene(self, scenes: list[dict], replacement: dict) -> list[dict]:
        validate_scene(replacement)
        if not any(scene["id"] == replacement["id"] for scene in scenes):
            raise ValidationError(f"Cannot retry missing scene: {replacement['id']}")
        return [replacement if scene["id"] == replacement["id"] else scene for scene in scenes]
