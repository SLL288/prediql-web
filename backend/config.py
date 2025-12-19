from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PREDIQL_", env_file=".env", env_file_encoding="utf-8")

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    runs_dir: Path = Path(__file__).resolve().parent / "runs"

    max_rounds: int = 5
    max_requests_per_node: int = 10

    default_ollama_model: str = "llama3"
    ollama_base_url: str = "http://localhost:11434"

    openai_compat_base_url: str = "https://api.openai.com/v1"


settings = Settings()
