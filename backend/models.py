from __future__ import annotations

import datetime as dt
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class RunConfig(BaseModel):
    endpoint_url: str = Field(..., alias="endpointUrl")
    llm_provider: str = Field(..., alias="llmProvider")
    model: str
    api_key: Optional[str] = Field(None, alias="apiKey")
    requests_per_node: int = Field(5, alias="requestsPerNode")
    rounds: int = 1
    headers: Optional[Dict[str, str]] = None

    model_config = ConfigDict(populate_by_name=True)


class RunRecord(BaseModel):
    run_id: str = Field(..., alias="runId")
    status: RunStatus = RunStatus.queued
    created_at: dt.datetime = Field(default_factory=lambda: dt.datetime.utcnow())
    updated_at: dt.datetime = Field(default_factory=lambda: dt.datetime.utcnow())
    progress: float = 0.0
    message: Optional[str] = None
    summary: Optional[str] = None
    result_path: Optional[str] = None
    summary_path: Optional[str] = None
    logs_path: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(populate_by_name=True)


class RunResponse(BaseModel):
    run_id: str = Field(..., alias="runId")
    model_config = ConfigDict(populate_by_name=True)


class RunStatusResponse(BaseModel):
    run_id: str = Field(..., alias="runId")
    status: RunStatus
    progress: float
    message: Optional[str] = None
    summary: Optional[str] = None
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = ConfigDict(populate_by_name=True)


class LogsResponse(BaseModel):
    run_id: str = Field(..., alias="runId")
    logs: List[str]
    next_cursor: int
    model_config = ConfigDict(populate_by_name=True)


class ResultsResponse(BaseModel):
    run_id: str = Field(..., alias="runId")
    summary: str
    result_json: Dict[str, Any] = Field(..., alias="resultJson")
    artifact_paths: Dict[str, str] = Field(..., alias="artifactPaths")
    model_config = ConfigDict(populate_by_name=True)
