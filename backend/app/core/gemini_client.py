from __future__ import annotations

import json
from typing import Any, Dict, List

import httpx

from app.core.models import settings

JSON_PROMPT = (
    "You are PrediQL assistant. Given a GraphQL schema summary, propose concise candidate queries or mutations. "
    "Return STRICT JSON with an array under key 'candidates', each item with fields name, type, and query."
)


class GeminiClient:
    def __init__(self, api_key: str, model: str, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or settings.GEMINI_BASE_URL).rstrip("/")

    async def generate_candidates(self, schema_summary: str, count: int) -> List[Dict[str, Any]]:
        prompt = f"{JSON_PROMPT}\nSchema summary:\n{schema_summary}\nReturn exactly {count} candidates."
        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            return []

        text = None
        if isinstance(data, dict):
            cands = data.get("candidates") or []
            if cands:
                parts = cands[0].get("content", {}).get("parts") or []
                if parts:
                    text = parts[0].get("text")
        if not text:
            return []
        try:
            parsed = json.loads(text)
            candidates = parsed.get("candidates") if isinstance(parsed, dict) else None
            if isinstance(candidates, list):
                return [c for c in candidates if isinstance(c, dict)]
        except Exception:
            return []
        return []
