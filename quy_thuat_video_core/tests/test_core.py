from __future__ import annotations

import pytest

from app.core.character import CharacterManager
from app.core.prompt import PromptBuilder
from app.core.scene import SceneManager
from app.core.story import StoryCore
from app.core.validator import ValidationError, validate_scene, validate_story
from app.providers.mock_provider import MockProvider
from app.storage.json_store import JsonStore, StorageError
from app.storage.project import ProjectStore


def request(scene_count: int = 3) -> dict:
    return {"project_name": "Long Thanh Thuc Tinh", "story_title": "Long Thanh Thức Tỉnh", "story_topic": "A weak young cultivator awakens the bloodline of an ancient dragon.", "language": "Vietnamese", "target_duration": "5 minutes", "genre": "Xianxia / cultivation", "visual_style": "Cinematic Chinese fantasy", "number_of_scenes": scene_count}


def test_project_creation(tmp_path):
    path = ProjectStore(tmp_path).create_project(request())
    assert (path / "project.json").exists()
    assert (path / "prompts").is_dir()
    assert (path / "logs" / "project.log").exists()


def test_character_creation_and_reuse():
    manager = CharacterManager()
    first = manager.add_or_reuse({"id": "char_001", "name": "Long Dạ", "role": "main_character", "age": 18, "appearance": "eyes", "clothing": "robe", "personality": "brave", "visual_identity": "dragon aura"})
    second = manager.add_or_reuse({"id": "char_999", "name": " long  dạ ", "role": "duplicate", "appearance": "x", "clothing": "x", "personality": "x", "visual_identity": "x"})
    assert first is second
    assert len(manager.characters) == 1


def test_scene_creation_and_validation():
    manager = CharacterManager([{"id": "char_001", "name": "Long Dạ", "role": "main_character", "age": 18, "appearance": "eyes", "clothing": "robe", "personality": "brave", "visual_identity": "dragon aura"}])
    scene = SceneManager().normalize_scene({"characters": ["Long Dạ"], "action": "trains"}, 1, manager, "fantasy")
    assert scene["id"] == "scene_001"
    assert scene["characters"] == ["char_001"]
    validate_scene(scene)


def test_invalid_scene_validation():
    with pytest.raises(ValidationError):
        validate_scene({"id": "scene_001"})


def test_prompt_generation():
    prompt = PromptBuilder().build({"order": 1, "location": "sect", "time_of_day": "dawn", "action": "awakens"}, [{"name": "Long Dạ", "appearance": "dragon eyes", "clothing": "robe", "visual_identity": "gold aura"}], "cinematic")
    assert "dragon eyes" in prompt["image_prompt"]
    assert "awakens" in prompt["video_prompt"]
    assert prompt["negative_prompt"]


def test_invalid_story_json_handling():
    with pytest.raises(ValidationError):
        validate_story({"title": "bad"})


def test_mock_provider():
    story = MockProvider().generate_story(request(2))
    assert story["title"] == "Long Thanh Thức Tỉnh"
    assert len(story["scenes"]) == 2


def test_project_save_load(tmp_path):
    store = ProjectStore(tmp_path)
    path = store.create_project(request(1))
    result = StoryCore(MockProvider(), store).generate_project_story(path, request(1))
    loaded = store.load_project(path)
    assert loaded["story"]["title"] == result["story"]["title"]
    assert loaded["characters"][0]["id"] == "char_001"
    assert loaded["scenes"][0]["id"] == "scene_001"
    assert (path / "prompts" / "scene_001.json").exists()


def test_retry_behavior_replaces_only_one_scene(tmp_path):
    store = ProjectStore(tmp_path)
    path = store.create_project(request(3))
    core = StoryCore(MockProvider(), store)
    core.generate_project_story(path, request(3))
    before = store.load_project(path)["scenes"]
    replacement = core.retry_scene(path, request(3), "scene_002")
    after = store.load_project(path)["scenes"]
    assert replacement["id"] == "scene_002"
    assert after[0] == before[0]
    assert after[1]["action"] != before[1]["action"]
    assert after[2] == before[2]


def test_corrupted_project_file(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(StorageError):
        JsonStore().load(bad)


def test_scene_rejects_missing_character():
    with pytest.raises(ValidationError, match="missing character"):
        SceneManager().normalize_scene({"characters": ["Unknown"], "action": "appears"}, 1, CharacterManager(), "fantasy")


def test_retry_rejects_missing_scene(tmp_path):
    store = ProjectStore(tmp_path)
    path = store.create_project(request(1))
    core = StoryCore(MockProvider(), store)
    core.generate_project_story(path, request(1))
    with pytest.raises(ValidationError, match="Cannot retry missing scene"):
        core.retry_scene(path, request(1), "scene_999")


def test_main_mock_creates_project_without_api_key(tmp_path, monkeypatch):
    from app import main as cli

    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("AI_BASE_URL", raising=False)
    monkeypatch.setenv("PROJECTS_DIR", str(tmp_path))
    code = cli.main(["--mock", "--project-name", "Mock CLI Project", "--number-of-scenes", "1"])
    assert code == 0
    assert (tmp_path / "mock_cli_project" / "project.json").exists()


def test_main_missing_api_key_returns_error_without_traceback(monkeypatch, capsys):
    from app import main as cli

    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("AI_BASE_URL", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)
    code = cli.main([])
    captured = capsys.readouterr()
    assert code == 1
    assert "Error: Missing AI_API_KEY" in captured.err
    assert "Traceback" not in captured.err


def test_invalid_timeout_config_returns_error_without_traceback(monkeypatch, capsys):
    from app import main as cli

    monkeypatch.setenv("AI_TIMEOUT_SECONDS", "not-an-int")
    code = cli.main(["--mock"])
    captured = capsys.readouterr()
    assert code == 1
    assert "Error: AI_TIMEOUT_SECONDS must be a positive integer." in captured.err
    assert "Traceback" not in captured.err


def test_retry_preserves_existing_scene_id_and_order(tmp_path):
    class WrongOrderProvider(MockProvider):
        def generate_scene(self, request: dict, scene_id: str) -> dict:
            scene = super().generate_scene(request, scene_id)
            scene["id"] = "scene_999"
            scene["order"] = 999
            return scene

    store = ProjectStore(tmp_path)
    path = store.create_project(request(3))
    core = StoryCore(WrongOrderProvider(), store)
    core.generate_project_story(path, request(3))
    replacement = core.retry_scene(path, request(3), "scene_002")
    scenes = store.load_project(path)["scenes"]
    assert replacement["id"] == "scene_002"
    assert replacement["order"] == 2
    assert [scene["id"] for scene in scenes] == ["scene_001", "scene_002", "scene_003"]
    assert [scene["order"] for scene in scenes] == [1, 2, 3]


def test_retry_preserves_story_characters_metadata_and_other_scenes(tmp_path):
    store = ProjectStore(tmp_path)
    path = store.create_project(request(3))
    core = StoryCore(MockProvider(), store)
    core.generate_project_story(path, request(3))
    before = store.load_project(path)
    core.retry_scene(path, request(3), "scene_002")
    after = store.load_project(path)
    assert after["project"] == before["project"]
    assert after["story"] == before["story"]
    assert after["characters"] == before["characters"]
    assert after["scenes"][0] == before["scenes"][0]
    assert after["scenes"][1] != before["scenes"][1]
    assert after["scenes"][2] == before["scenes"][2]


def test_mock_mode_does_not_call_network(tmp_path, monkeypatch):
    from app import main as cli

    def fail_urlopen(*args, **kwargs):
        raise AssertionError("network should not be called in mock mode")

    monkeypatch.setattr("urllib.request.urlopen", fail_urlopen)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("AI_BASE_URL", raising=False)
    monkeypatch.setenv("PROJECTS_DIR", str(tmp_path))
    assert cli.main(["--mock", "--project-name", "Offline Mock", "--number-of-scenes", "1"]) == 0
