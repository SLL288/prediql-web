from __future__ import annotations

import datetime as dt
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RUNS_DIR: Path = Path("/app/runs")
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com"
    DEFAULT_MODEL: str = "llama3"
    CORS_ORIGINS: str = "http://localhost:3000"
    MAX_ROUNDS: int = 5
    MAX_REQUESTS_PER_NODE: int = 5


class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"
    cancelled = "cancelled"


class Progress(BaseModel):
    pct: float = 0.0
    stage: str = "queued"
    detail: Optional[str] = None


class RunConfig(BaseModel):
    endpoint_url: str = Field(..., alias="endpointUrl")
    llm_provider: str = Field("ollama", alias="llmProvider")
    model: str = "llama3"
    api_key: Optional[str] = Field(None, alias="apiKey")
    graphql_headers_json: Optional[str] = Field(None, alias="graphqlHeadersJson")
    rounds: int = 2
    requests_per_node: int = Field(2, alias="requestsPerNode")
    notes: Optional[str] = None

    @field_validator("llm_provider")
    def validate_provider(cls, v: str) -> str:
        if v not in {"ollama", "openai_compatible", "gemini"}:
            raise ValueError("Unsupported llmProvider")
        return v


class RunRecord(BaseModel):
    run_id: str = Field(..., alias="runId")
    status: RunStatus = RunStatus.queued
    progress: Progress = Field(default_factory=Progress)
    started_at: Optional[dt.datetime] = Field(default=None, alias="startedAt")
    finished_at: Optional[dt.datetime] = Field(default=None, alias="finishedAt")
    error: Optional[str] = None
    logs_path: Optional[Path] = None
    results_path: Optional[Path] = None
    summary_path: Optional[Path] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    cancel_requested: bool = False


class CreateRunResponse(BaseModel):
    run_id: str = Field(..., alias="runId")
    status: RunStatus


class RunStatusResponse(BaseModel):
    run_id: str = Field(..., alias="runId")
    status: RunStatus
    progress: Progress
    started_at: Optional[dt.datetime] = Field(default=None, alias="startedAt")
    finished_at: Optional[dt.datetime] = Field(default=None, alias="finishedAt")
    error: Optional[str] = None


class LogsResponse(BaseModel):
    lines: List[str]
    next_cursor: int


class Artifact(BaseModel):
    name: str
    url: str


class ResultsResponse(BaseModel):
    summary: Dict[str, Any]
    artifacts: List[Artifact]
    rawJson: Dict[str, Any]


settings = Settings()
