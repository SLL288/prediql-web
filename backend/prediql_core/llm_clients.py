from __future__ import annotations

import httpx


class BaseLLMClient:
    async def generate(self, prompt: str) -> str:  # pragma: no cover - interface only
        raise NotImplementedError


class OllamaClient(BaseLLMClient):
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict):
                    message = data.get("message") or data.get("choices", [{}])[0].get("message")
                    if message:
                        return message.get("content") or ""
                return ""
        except Exception as exc:  # noqa: BLE001
            return f"[ollama-error] {exc}"


class OpenAICompatibleClient(BaseLLMClient):
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict):
                    choices = data.get("choices")
                    if choices and isinstance(choices, list):
                        message = choices[0].get("message", {})
                        return message.get("content") or ""
                return ""
        except Exception as exc:  # noqa: BLE001
            return f"[openai-compatible-error] {exc}"
