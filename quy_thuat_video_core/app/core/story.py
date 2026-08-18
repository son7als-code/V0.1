"""Story orchestration through replaceable providers."""
from __future__ import annotations

from pathlib import Path

from app.core.character import CharacterManager
from app.core.scene import SceneManager
from app.core.validator import ValidationError, validate_story
from app.providers.base import BaseAIProvider
from app.storage.project import ProjectStore


class StoryCore:
    def __init__(self, provider: BaseAIProvider, project_store: ProjectStore | None = None, scene_manager: SceneManager | None = None) -> None:
        self.provider = provider
        self.project_store = project_store or ProjectStore()
        self.scene_manager = scene_manager or SceneManager()

    def generate_project_story(self, project_path: Path, request: dict) -> dict:
        self.project_store.log(project_path, "generation start", "Story generation started")
        story = self.provider.generate_story(request)
        validate_story(story)
        character_manager = CharacterManager()
        characters = character_manager.merge_provider_characters(story["characters"])
        scenes = self.scene_manager.normalize_scenes(story["scenes"], character_manager, request["visual_style"])
        self.project_store.save_outputs(project_path, story, characters, scenes)
        self.project_store.log(project_path, "generation success", "Story, characters, scenes, and prompts saved")
        return {"story": story, "characters": characters, "scenes": scenes}

    def retry_scene(self, project_path: Path, request: dict, scene_id: str) -> dict:
        self.project_store.log(project_path, "retry", f"Retry requested for {scene_id}")
        loaded = self.project_store.load_project(project_path)
        existing_scene = self._find_existing_scene(loaded["scenes"], scene_id)
        character_manager = CharacterManager(loaded["characters"])
        raw_scene = self.provider.generate_scene(request, scene_id)
        retry_payload = self._preserve_retry_identity(raw_scene, existing_scene)
        replacement = self.scene_manager.normalize_scene(retry_payload, int(existing_scene["order"]), character_manager, request["visual_style"])
        scenes = self.scene_manager.replace_scene(loaded["scenes"], replacement)
        self.project_store.save_outputs(project_path, loaded["story"], loaded["characters"], scenes)
        self.project_store.log(project_path, "generation success", f"Retry succeeded for {scene_id}")
        return replacement

    def _find_existing_scene(self, scenes: list[dict], scene_id: str) -> dict:
        existing_scene = next((scene for scene in scenes if scene["id"] == scene_id), None)
        if existing_scene is None:
            raise ValidationError(f"Cannot retry missing scene: {scene_id}")
        return existing_scene

    def _preserve_retry_identity(self, raw_scene: dict, existing_scene: dict) -> dict:
        """Provider content may change, but retry must keep the existing scene id and order."""
        return {**raw_scene, "id": existing_scene["id"], "order": existing_scene["order"]}
