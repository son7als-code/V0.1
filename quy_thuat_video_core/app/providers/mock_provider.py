"""No-key deterministic provider used by tests and demos."""
from __future__ import annotations

from app.providers.base import BaseAIProvider


class MockProvider(BaseAIProvider):
    def generate_story(self, request: dict) -> dict:
        count = int(request.get("number_of_scenes", 3))
        characters = [
            {"id": "char_001", "name": "Long Dạ", "role": "main_character", "age": 18, "appearance": "young cultivator with bright dragon-like eyes", "clothing": "plain dark training robe", "personality": "persistent and humble", "visual_identity": "ancient dragon bloodline aura"},
            {"id": "char_002", "name": "Mộc Lan", "role": "mentor", "age": 32, "appearance": "calm swordswoman with silver hair", "clothing": "white-and-blue sect robe", "personality": "wise and protective", "visual_identity": "moonlit sword energy"},
        ]
        scenes = []
        for i in range(1, count + 1):
            scenes.append({"id": f"scene_{i:03d}", "order": i, "duration_seconds": 12, "location": "ancient mountain sect", "time_of_day": "dawn", "characters": ["Long Dạ", "Mộc Lan"] if i % 2 else ["Long Dạ"], "action": f"Long Dạ advances through trial step {i}", "narration": f"The dragon bloodline stirs during scene {i}.", "dialogue": []})
        return {"title": request.get("story_title", "Mock Story"), "summary": "A weak cultivator awakens an ancient dragon bloodline.", "characters": characters, "scenes": scenes}

    def generate_scene(self, request: dict, scene_id: str) -> dict:
        order = int(scene_id.split("_")[-1]) if "_" in scene_id else 1
        return {"id": scene_id, "order": order, "duration_seconds": 12, "location": "ancient mountain sect", "time_of_day": "dawn", "characters": ["Long Dạ"], "action": f"Retry regeneration for {scene_id}: Long Dạ regains focus.", "narration": "The failed moment is rebuilt without touching earlier scenes.", "dialogue": []}
