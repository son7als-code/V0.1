"""Structured prompt builder. It does not generate media."""
from __future__ import annotations


class PromptBuilder:
    def build(self, scene: dict, characters: list[dict], visual_style: str) -> dict:
        identity = "; ".join(
            f"{c['name']}: {c['appearance']}, wearing {c['clothing']}, {c['visual_identity']}"
            for c in characters
        ) or "No visible named character"
        environment = f"{scene['location']} at {scene['time_of_day']}"
        continuity = f"Scene {scene['order']} continuity: preserve stable character identities and costumes."
        image_prompt = f"{visual_style}. {identity}. Environment: {environment}. Action: {scene['action']}. Cinematic camera, dramatic lighting. {continuity}"
        video_prompt = f"{visual_style}. Camera follows the action in {environment}: {scene['action']}. Maintain continuity and smooth motion."
        negative_prompt = "low quality, inconsistent face, duplicate characters, broken anatomy, unreadable text, watermark"
        return {"image_prompt": image_prompt, "video_prompt": video_prompt, "negative_prompt": negative_prompt}
