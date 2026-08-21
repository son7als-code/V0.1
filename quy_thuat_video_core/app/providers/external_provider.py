"""Minimal external provider adapter using a generic JSON HTTP endpoint."""
from __future__ import annotations

import json
import urllib.error
import urllib.request

from app.providers.base import BaseAIProvider, ProviderError


class ExternalProvider(BaseAIProvider):
    def __init__(self, api_key: str | None, base_url: str | None, model: str | None, timeout_seconds: int = 30) -> None:
        if not api_key:
            raise ProviderError("Missing AI_API_KEY. Use --mock or set AI_API_KEY in the environment.")
        if not base_url:
            raise ProviderError("Missing AI_BASE_URL. Use --mock or set AI_BASE_URL in the environment.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate_story(self, request: dict) -> dict:
        return self._post("/generate_story", request)

    def generate_scene(self, request: dict, scene_id: str) -> dict:
        return self._post("/generate_scene", {"request": request, "scene_id": scene_id})

    def _post(self, path: str, payload: dict) -> dict:
        body = json.dumps({"model": self.model, "input": payload}).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + path,
            data=body,
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + self.api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ProviderError("Provider returned invalid JSON.") from exc
        except urllib.error.URLError as exc:
            raise ProviderError("Provider network request failed or timed out.") from exc
