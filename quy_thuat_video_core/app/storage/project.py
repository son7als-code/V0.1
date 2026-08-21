"""Project directory creation, persistence, and lightweight logging."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.core.validator import validate_project_request
from app.storage.json_store import JsonStore


class ProjectStore:
    def __init__(self, projects_dir: Path | str = "projects", json_store: JsonStore | None = None) -> None:
        self.projects_dir = Path(projects_dir)
        self.json_store = json_store or JsonStore()

    def create_project(self, request: dict) -> Path:
        validate_project_request(request)
        slug = self._slug(request["project_name"])
        path = self.projects_dir / slug
        suffix = 1
        while path.exists():
            suffix += 1
            path = self.projects_dir / f"{slug}_{suffix:03d}"
        (path / "prompts").mkdir(parents=True)
        (path / "logs").mkdir()
        metadata = {**request, "id": path.name, "created_at": datetime.now(timezone.utc).isoformat()}
        self.json_store.save(path / "project.json", metadata)
        self.log(path, "project creation", "Project created")
        return path

    def save_outputs(self, path: Path, story: dict, characters: list[dict], scenes: list[dict]) -> None:
        self.json_store.save(path / "story.json", story)
        self.json_store.save(path / "characters.json", characters)
        self.json_store.save(path / "scenes.json", scenes)
        for scene in scenes:
            self.json_store.save(path / "prompts" / f"{scene['id']}.json", {"image_prompt": scene["image_prompt"], "video_prompt": scene["video_prompt"], "negative_prompt": scene["negative_prompt"]})

    def load_project(self, path: Path) -> dict:
        return {
            "project": self.json_store.load(path / "project.json"),
            "story": self.json_store.load(path / "story.json"),
            "characters": self.json_store.load(path / "characters.json"),
            "scenes": self.json_store.load(path / "scenes.json"),
        }

    def log(self, path: Path, event: str, message: str) -> None:
        (path / "logs").mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        with (path / "logs" / "project.log").open("a", encoding="utf-8") as file:
            file.write(f"{timestamp} | {event} | {message}\n")

    def _slug(self, value: str) -> str:
        cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")
        return cleaned or "project"
