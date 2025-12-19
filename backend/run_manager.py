from __future__ import annotations

import asyncio
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List, Optional

from models import LogsResponse, RunConfig, RunRecord, RunStatus, RunStatusResponse

from config import settings


class RunManager:
    def __init__(self, runs_root: Optional[Path] = None) -> None:
        self.runs_root = runs_root or settings.runs_dir
        self.runs_root.mkdir(parents=True, exist_ok=True)
        self._runs: Dict[str, RunRecord] = {}
        self._logs: Dict[str, List[str]] = {}
        self._lock = asyncio.Lock()

    async def create_run(self, run_id: str, config: RunConfig) -> RunRecord:
        async with self._lock:
            run_dir = self.runs_root / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            record = RunRecord(
                runId=run_id,
                status=RunStatus.queued,
                logs_path=str(run_dir / "logs.txt"),
                result_path=str(run_dir / "results.json"),
                summary_path=str(run_dir / "summary.txt"),
                config=config.model_dump(by_alias=True, exclude={"apiKey", "api_key"}),
            )
            self._runs[run_id] = record
            self._logs[run_id] = []
            return record

    async def append_log(self, run_id: str, message: str) -> None:
        async with self._lock:
            self._logs.setdefault(run_id, []).append(message)
            record = self._runs.get(run_id)
            if record and record.logs_path:
                log_path = Path(record.logs_path)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with log_path.open("a", encoding="utf-8") as f:
                    f.write(message + "\n")
            if record:
                record.updated_at = dt.datetime.utcnow()

    async def update_status(
        self,
        run_id: str,
        *,
        status: Optional[RunStatus] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> Optional[RunRecord]:
        async with self._lock:
            record = self._runs.get(run_id)
            if not record:
                return None
            if status:
                record.status = status
            if progress is not None:
                record.progress = max(0.0, min(progress, 1.0))
            if message:
                record.message = message
            if summary:
                record.summary = summary
            record.updated_at = dt.datetime.utcnow()
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
                message=record.message,
                summary=record.summary,
                created_at=record.created_at,
                updated_at=record.updated_at,
            )

    async def get_logs(self, run_id: str, start: int = 0) -> Optional[LogsResponse]:
        async with self._lock:
            if run_id not in self._logs:
                return None
            logs = self._logs.get(run_id, [])
            subset = logs[start:]
            return LogsResponse(runId=run_id, logs=subset, next_cursor=start + len(subset))

    async def get_record(self, run_id: str) -> Optional[RunRecord]:
        async with self._lock:
            return self._runs.get(run_id)

    async def save_results(self, run_id: str, summary: str, result_json: dict) -> Optional[RunRecord]:
        async with self._lock:
            record = self._runs.get(run_id)
            if not record:
                return None
            record.summary = summary
            record.updated_at = dt.datetime.utcnow()
            record.status = RunStatus.done
            self._runs[run_id] = record
            # Persist artifacts to disk without secrets.
            if record.result_path:
                path = Path(record.result_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(result_json, indent=2), encoding="utf-8")
            if record.summary_path:
                path = Path(record.summary_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(summary, encoding="utf-8")
            return record

    async def mark_failed(self, run_id: str, message: str) -> Optional[RunRecord]:
        await self.append_log(run_id, f"ERROR: {message}")
        return await self.update_status(run_id, status=RunStatus.failed, message=message)
