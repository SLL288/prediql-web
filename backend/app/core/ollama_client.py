from __future__ import annotations

import json
from typing import Any, Dict, List

import httpx

from app.core.models import settings

PROMPT_TEMPLATE = (
    "You are PrediQL assistant. Given a GraphQL schema summary, propose concise candidate queries or mutations. "
    "Return STRICT JSON with an array under key 'candidates', each item with fields name, type, and query. Do not include any text outside JSON."
)


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.DEFAULT_MODEL

    async def generate_candidates(self, schema_summary: str, count: int) -> List[Dict[str, Any]]:
        prompt = f"{PROMPT_TEMPLATE}\nSchema summary:\n{schema_summary}\nReturn exactly {count} candidates."
        data = await self._chat(prompt)
        candidates = data.get("candidates") if isinstance(data, dict) else None
        if isinstance(candidates, list):
            return [c for c in candidates if isinstance(c, dict)]
        return []

    async def _chat(self, prompt: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.2},
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

        # Extract message content
        content = None
        if isinstance(data, dict):
            content = data.get("message", {}).get("content") or data.get("content")
        if not content:
            return {"error": "no content"}

        for attempt in range(2):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Retry with an explicit JSON-only prompt
                content = await self._retry_json_only(content)
        return {"error": "invalid json response"}

    async def _retry_json_only(self, prior: str) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prior},
                {"role": "system", "content": "Return ONLY valid JSON."},
            ],
            "stream": False,
            "options": {"temperature": 0.2},
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data.get("message", {}).get("content", "{}")
