from __future__ import annotations

import json
from typing import Any, Dict, List

from app.core.gemini_client import GeminiClient
from app.core.openai_client import OpenAIClient
from app.core.models import RunConfig


async def generate_candidates_from_api(config: RunConfig, schema_summary: str, count: int) -> List[Dict[str, Any]]:
    if config.llm_provider == "openai_compatible":
        client = OpenAIClient(api_key=config.api_key or "", model=config.model or "gpt-4o-mini")
    elif config.llm_provider == "gemini":
        client = GeminiClient(api_key=config.api_key or "", model=config.model or "gemini-1.5-flash")
    else:
        return []
    return await client.generate_candidates(schema_summary, count)
