from __future__ import annotations

import asyncio
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.models import (
    CreateRunResponse,
    LogsResponse,
    ResultsResponse,
    Progress,
    RunConfig,
    RunStatus,
    RunStatusResponse,
    settings,
)
from app.core.runner import run_job
from app.core.storage import RunRegistry
from app.core.utils import parse_headers, validate_http_url

router = APIRouter(prefix="/api/runs")


async def get_registry() -> RunRegistry:
    # In-memory singleton stored on the router object
    return router.registry  # type: ignore[attr-defined]


@router.post("", response_model=CreateRunResponse)
async def create_run(config: RunConfig, registry: RunRegistry = Depends(get_registry)) -> CreateRunResponse:
    validate_http_url(config.endpoint_url)
    if config.rounds > settings.MAX_ROUNDS:
        raise HTTPException(status_code=400, detail=f"rounds cannot exceed {settings.MAX_ROUNDS}")
    if config.requests_per_node > settings.MAX_REQUESTS_PER_NODE:
        raise HTTPException(status_code=400, detail=f"requestsPerNode cannot exceed {settings.MAX_REQUESTS_PER_NODE}")
    parse_headers(config.graphql_headers_json)

    run_id = registry.new_run_id()
    await registry.create_run(run_id, config)
    asyncio.create_task(run_job(run_id, config, registry))
    return CreateRunResponse(runId=run_id, status=RunStatus.queued)


@router.get("/{run_id}", response_model=RunStatusResponse)
async def get_run(run_id: str, registry: RunRegistry = Depends(get_registry)) -> RunStatusResponse:
    status = await registry.get_status(run_id)
    if not status:
        raise HTTPException(status_code=404, detail="Run not found")
    return status


@router.get("/{run_id}/logs", response_model=LogsResponse)
async def get_logs(run_id: str, cursor: int = Query(0, ge=0), registry: RunRegistry = Depends(get_registry)) -> LogsResponse:
    logs = await registry.get_logs(run_id, cursor)
    if not logs:
        raise HTTPException(status_code=404, detail="Run not found")
    return logs


@router.get("/{run_id}/results", response_model=ResultsResponse)
async def get_results(run_id: str, registry: RunRegistry = Depends(get_registry)) -> ResultsResponse:
    record = await registry.get_record(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    if not record.results_path or not record.results_path.exists():
        raise HTTPException(status_code=404, detail="Results not ready")
    raw_json = record.results_path.read_text(encoding="utf-8")
    summary_json = record.summary_path.read_text(encoding="utf-8") if record.summary_path and record.summary_path.exists() else "{}"
    return ResultsResponse(
        summary=_safe_load(summary_json),
        rawJson=_safe_load(raw_json),
        artifacts=[
            _artifact(run_id, "raw_results.json"),
            _artifact(run_id, "summary.json"),
            _artifact(run_id, "logs.txt"),
        ],
    )


@router.get("/{run_id}/artifacts/{filename}")
async def get_artifact(run_id: str, filename: str, registry: RunRegistry = Depends(get_registry)):
    record = await registry.get_record(run_id)
    if not record or not record.logs_path:
        raise HTTPException(status_code=404, detail="Run not found")
    run_dir = record.logs_path.parent
    target = (run_dir / filename).resolve()
    if run_dir not in target.parents and target != run_dir:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not target.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(target)


@router.post("/{run_id}/cancel")
async def cancel_run(run_id: str, registry: RunRegistry = Depends(get_registry)):
    record = await registry.get_record(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    await registry.request_cancel(run_id)
    await registry.update_status(run_id, status=RunStatus.cancelled, progress=Progress(pct=0.0, stage="cancelled"))
    await registry.append_log(run_id, "Cancellation requested")
    return {"status": "cancelled"}


def _artifact(run_id: str, name: str):
    return {"name": name, "url": f"/api/runs/{run_id}/artifacts/{name}"}


def _safe_load(raw: str):
    try:
        return json.loads(raw)
    except Exception:
        return {}
