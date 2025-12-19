from __future__ import annotations

import asyncio
import datetime as dt
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from app.core.models import LogsResponse, Progress, RunConfig, RunRecord, RunStatus, RunStatusResponse, settings


class RunRegistry:
    def __init__(self, runs_dir: Path | None = None) -> None:
        self.runs_dir = Path(runs_dir or settings.RUNS_DIR)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self._runs: Dict[str, RunRecord] = {}
        self._logs: Dict[str, List[str]] = {}
        self._lock = asyncio.Lock()

    def new_run_id(self) -> str:
        return uuid.uuid4().hex

    async def create_run(self, run_id: str, config: RunConfig) -> RunRecord:
        async with self._lock:
            run_path = self.runs_dir / run_id
            run_path.mkdir(parents=True, exist_ok=True)
            record = RunRecord(
                runId=run_id,
                status=RunStatus.queued,
                progress=Progress(pct=0.0, stage="queued"),
                logs_path=run_path / "logs.txt",
                results_path=run_path / "raw_results.json",
                summary_path=run_path / "summary.json",
                config=config.model_dump(exclude_none=True, by_alias=True, exclude={"apiKey", "api_key"}),
            )
            self._runs[run_id] = record
            self._logs[run_id] = []
            return record

    async def append_log(self, run_id: str, message: str) -> None:
        async with self._lock:
            lines = self._logs.setdefault(run_id, [])
            timestamp = dt.datetime.utcnow().isoformat()
            line = f"[{timestamp}] {message}"
            lines.append(line)
            record = self._runs.get(run_id)
            if record and record.logs_path:
                record.logs_path.parent.mkdir(parents=True, exist_ok=True)
                with record.logs_path.open("a", encoding="utf-8") as f:
                    f.write(line + "\n")

    async def update_status(
        self,
        run_id: str,
        *,
        status: Optional[RunStatus] = None,
        progress: Optional[Progress] = None,
        error: Optional[str] = None,
    ) -> Optional[RunRecord]:
        async with self._lock:
            record = self._runs.get(run_id)
            if not record:
                return None
            if status:
                record.status = status
                if status == RunStatus.running and not record.started_at:
                    record.started_at = dt.datetime.utcnow()
                if status in {RunStatus.done, RunStatus.failed, RunStatus.cancelled}:
                    record.finished_at = dt.datetime.utcnow()
            if progress:
                record.progress = progress
            if error:
                record.error = error
            self._runs[run_id] = record
            return record

    async def get_status(self, run_id: str) -> Optional[RunStatusResponse]:
        async with self._lock:
            record = self._runs.get(run_id)
            if not record:
                return None
            return RunStatusResponse(
                runId=record.run_id,
                status=record.status,
                progress=record.progress,
                started_at=record.started_at,
                finished_at=record.finished_at,
                error=record.error,
            )

    async def get_record(self, run_id: str) -> Optional[RunRecord]:
        async with self._lock:
            return self._runs.get(run_id)

    async def get_logs(self, run_id: str, cursor: int = 0) -> Optional[LogsResponse]:
        async with self._lock:
            if run_id not in self._logs:
                return None
            lines = self._logs[run_id]
            subset = lines[cursor:]
            return LogsResponse(lines=subset, next_cursor=cursor + len(subset))

    async def save_results(self, run_id: str, summary: Dict, raw_json: Dict) -> None:
        async with self._lock:
            record = self._runs.get(run_id)
            if not record:
                return
            if record.summary_path:
                record.summary_path.parent.mkdir(parents=True, exist_ok=True)
                record.summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
            if record.results_path:
                record.results_path.parent.mkdir(parents=True, exist_ok=True)
                record.results_path.write_text(json.dumps(raw_json, indent=2), encoding="utf-8")
            self._runs[run_id] = record

    async def request_cancel(self, run_id: str) -> None:
        async with self._lock:
            record = self._runs.get(run_id)
            if record:
                record.cancel_requested = True
                self._runs[run_id] = record

    async def is_cancelled(self, run_id: str) -> bool:
        async with self._lock:
            record = self._runs.get(run_id)
            return bool(record and record.cancel_requested)
