import logging
import os
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_llm_model(prompt: str) -> str:
    provider = os.getenv("PREDIQL_LLM_PROVIDER", "openai_compatible")
    api_key = os.getenv("PREDIQL_API_KEY", "")
    model = os.getenv("PREDIQL_LLM_MODEL", "gpt-4o-mini")

    if provider == "gemini":
        return _call_gemini(prompt, api_key, model)
    return _call_openai_compatible(prompt, api_key, model)


def _call_openai_compatible(prompt: str, api_key: str, model: str) -> str:
    base_url = os.getenv("PREDIQL_OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "temperature": 0.2,
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices") or []
        if choices:
            return choices[0].get("message", {}).get("content", "")
    except Exception as exc:
        logger.error("OpenAI-compatible call failed: %s", exc)
    return ""


def _call_gemini(prompt: str, api_key: str, model: str) -> str:
    base_url = os.getenv("PREDIQL_GEMINI_BASE_URL", "https://generativelanguage.googleapis.com").rstrip("/")
    url = f"{base_url}/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates") or []
        if candidates:
            parts = candidates[0].get("content", {}).get("parts") or []
            if parts:
                return parts[0].get("text", "")
    except Exception as exc:
        logger.error("Gemini call failed: %s", exc)
    return ""
