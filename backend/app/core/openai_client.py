from __future__ import annotations

import json
from typing import Any, Dict, List

import httpx

from app.core.models import settings

JSON_PROMPT = (
    "You are PrediQL assistant. Given a GraphQL schema summary, propose concise candidate queries or mutations. "
    "Return STRICT JSON with an array under key 'candidates', each item with fields name, type, and query."
)


class OpenAIClient:
    def __init__(self, api_key: str, model: str, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or settings.OPENAI_BASE_URL).rstrip("/")

    async def generate_candidates(self, schema_summary: str, count: int) -> List[Dict[str, Any]]:
        prompt = f"{JSON_PROMPT}\nSchema summary:\n{schema_summary}\nReturn exactly {count} candidates."
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "temperature": 0.2,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            return []

        content = None
        if isinstance(data, dict):
            choices = data.get("choices") or []
            if choices:
                content = choices[0].get("message", {}).get("content")
        if not content:
            return []
        try:
            parsed = json.loads(content)
            candidates = parsed.get("candidates") if isinstance(parsed, dict) else None
            if isinstance(candidates, list):
                return [c for c in candidates if isinstance(c, dict)]
        except Exception:
            return []
        return []
