from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models import LogsResponse, RunConfig, RunResponse, RunStatus, RunStatusResponse, ResultsResponse
from prediql_core.llm_clients import OllamaClient, OpenAICompatibleClient
from prediql_core.runner import run_prediql
from run_manager import RunManager

app = FastAPI(title="PrediQL Web API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

run_manager = RunManager()


def _sanitize_endpoint(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="endpointUrl must start with http or https")
    if not parsed.netloc:
        raise HTTPException(status_code=400, detail="endpointUrl is missing host")
    return url


def _validate_limits(config: RunConfig) -> None:
    if config.rounds < 1 or config.rounds > settings.max_rounds:
        raise HTTPException(status_code=400, detail=f"rounds must be between 1 and {settings.max_rounds}")
    if config.requests_per_node < 1 or config.requests_per_node > settings.max_requests_per_node:
        raise HTTPException(
            status_code=400,
            detail=f"requestsPerNode must be between 1 and {settings.max_requests_per_node}",
        )


def _build_llm_client(config: RunConfig):
    if config.llm_provider == "ollama":
        return OllamaClient(settings.ollama_base_url, config.model or settings.default_ollama_model)
    if config.llm_provider == "openai_compatible":
        if not config.api_key:
            raise HTTPException(status_code=400, detail="apiKey is required for openai_compatible provider")
        return OpenAICompatibleClient(settings.openai_compat_base_url, config.api_key, config.model)
    raise HTTPException(status_code=400, detail="Unsupported llmProvider")


def _log_for_run(run_id: str):
    def _log(message: str) -> None:
        asyncio.create_task(run_manager.append_log(run_id, message))

    return _log


async def _execute_run(run_id: str, config: RunConfig) -> None:
    logger = _log_for_run(run_id)
    await run_manager.update_status(run_id, status=RunStatus.running, progress=0.02, message="starting")
    logger("Run queued; initializing")

    try:
        client = _build_llm_client(config)
    except HTTPException as exc:
        await run_manager.mark_failed(run_id, exc.detail)
        return

    try:
        progress_cb = lambda value: asyncio.create_task(  # noqa: E731
            run_manager.update_status(run_id, status=RunStatus.running, progress=value)
        )
        result = await run_prediql(config, client, logger, progress_cb=progress_cb)
        summary = result.get("summary", "PrediQL run completed")
        await run_manager.save_results(run_id, summary=summary, result_json=result)
        await run_manager.update_status(run_id, status=RunStatus.done, progress=1.0, message="completed")
        logger("Artifacts saved")
    except Exception as exc:  # noqa: BLE001
        await run_manager.mark_failed(run_id, f"Run failed: {exc}")


@app.post("/api/runs", response_model=RunResponse)
async def create_run(config: RunConfig) -> RunResponse:
    _sanitize_endpoint(config.endpoint_url)
    _validate_limits(config)
    run_id = uuid.uuid4().hex
    await run_manager.create_run(run_id, config)
    asyncio.create_task(_execute_run(run_id, config))
    return RunResponse(runId=run_id)


@app.get("/api/runs/{run_id}", response_model=RunStatusResponse)
async def get_run(run_id: str) -> RunStatusResponse:
    status = await run_manager.get_status(run_id)
    if not status:
        raise HTTPException(status_code=404, detail="Run not found")
    return status


@app.get("/api/runs/{run_id}/logs", response_model=LogsResponse)
async def get_logs(run_id: str, cursor: int = Query(0, ge=0)) -> LogsResponse:
    logs = await run_manager.get_logs(run_id, start=cursor)
    if not logs:
        raise HTTPException(status_code=404, detail="Run not found")
    return logs


@app.get("/api/runs/{run_id}/results", response_model=ResultsResponse)
async def get_results(run_id: str) -> ResultsResponse:
    record = await run_manager.get_record(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    if not record.result_path or not Path(record.result_path).exists():
        raise HTTPException(status_code=404, detail="Results not ready")

    result_json = json.loads(Path(record.result_path).read_text(encoding="utf-8"))
    summary_text: Optional[str] = None
    if record.summary_path and Path(record.summary_path).exists():
        summary_text = Path(record.summary_path).read_text(encoding="utf-8")

    return ResultsResponse(
        runId=run_id,
        summary=summary_text or "",
        resultJson=result_json,
        artifactPaths={
            "results": record.result_path,
            "summary": record.summary_path or "",
            "logs": record.logs_path or "",
        },
    )
