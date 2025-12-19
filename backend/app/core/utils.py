from __future__ import annotations

import json
from typing import Any, Dict
from urllib.parse import urlparse

from fastapi import HTTPException


def validate_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="endpointUrl must be http or https")
    if not parsed.netloc:
        raise HTTPException(status_code=400, detail="endpointUrl is missing host")


def parse_headers(raw: str | None) -> Dict[str, str] | None:
    if not raw:
        return None
    try:
        obj: Any = json.loads(raw)
    except json.JSONDecodeError as exc:  # pragma: no cover - runtime validation
        raise HTTPException(status_code=400, detail=f"Invalid headers JSON: {exc}")
    if not isinstance(obj, dict):
        raise HTTPException(status_code=400, detail="graphqlHeadersJson must be a JSON object")
    # Coerce values to strings
    return {str(k): str(v) for k, v in obj.items()}
