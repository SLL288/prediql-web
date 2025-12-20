from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict

from fastapi import HTTPException

from app.core.models import Progress, RunConfig, RunStatus, settings
from app.core.storage import RunRegistry


async def run_job(run_id: str, config: RunConfig, registry: RunRegistry) -> None:
    """Run the legacy PrediQL pipeline (main.py) as a subprocess with per-run isolation."""
    run_dir = Path(settings.RUNS_DIR) / run_id
    legacy_dir = Path(__file__).resolve().parent.parent / "prediql_legacy"

    async def log(msg: str) -> None:
        await registry.append_log(run_id, msg)

    async def update_progress(pct: float, stage: str, detail: str | None = None) -> None:
        await registry.update_status(run_id, progress=Progress(pct=min(max(pct, 0.0), 1.0), stage=stage, detail=detail))

    if config.llm_provider not in {"openai_compatible", "gemini"}:
        raise HTTPException(status_code=400, detail="Only openai_compatible or gemini supported in legacy runner")
    if not config.api_key:
        raise HTTPException(status_code=400, detail="apiKey is required for this provider")

    try:
        await registry.update_status(run_id, status=RunStatus.running)
        await update_progress(0.05, "initializing")

        env = os.environ.copy()
        env.update(
            {
                "PREDIQL_RUN_ID": run_id,
                "PREDIQL_RUN_ROOT": str(settings.RUNS_DIR),
                "PREDIQL_LLM_PROVIDER": config.llm_provider,
                "PREDIQL_API_KEY": config.api_key or "",
                "PREDIQL_LLM_MODEL": config.model,
                "PREDIQL_OPENAI_BASE_URL": settings.OPENAI_BASE_URL,
                "PREDIQL_GEMINI_BASE_URL": settings.GEMINI_BASE_URL,
            }
        )

        cmd = [
            "python",
            "main.py",
            "--url",
            config.endpoint_url,
            "--requests",
            str(config.requests_per_node),
            "--rounds",
            str(config.rounds),
        ]
        await log(f"Starting legacy pipeline: {' '.join(cmd)}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(legacy_dir),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        line_count = 0
        if process.stdout:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                decoded = line.decode(errors="ignore").rstrip()
                await log(decoded)
                line_count += 1
                if line_count % 5 == 0:
                    await update_progress(min(0.8, 0.05 + line_count * 0.01), "running")

        returncode = await process.wait()
        if returncode != 0:
            await log(f"Legacy pipeline failed with code {returncode}")
            await registry.update_status(run_id, status=RunStatus.failed, error=f"Legacy pipeline exited {returncode}")
            return

        await update_progress(0.9, "saving")
        summary, raw = await _collect_outputs(run_dir)
        await registry.save_results(run_id, summary=summary, raw_json=raw)
        await registry.update_status(run_id, status=RunStatus.done, progress=Progress(pct=1.0, stage="done"))
        await log("Run complete. Artifacts written.")

    except HTTPException as exc:
        await registry.append_log(run_id, f"Validation failed: {exc.detail}")
        await registry.update_status(run_id, status=RunStatus.failed, error=str(exc.detail))
    except Exception as exc:  # noqa: BLE001
        await registry.append_log(run_id, f"Run failed: {exc}")
        await registry.update_status(run_id, status=RunStatus.failed, error=str(exc))


async def _collect_outputs(run_dir: Path) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Gather summary/raw outputs from the legacy pipeline."""
    summary: Dict[str, Any] = {}
    raw: Dict[str, Any] = {}
    output_dir = run_dir / "prediql-output"

    stats_file = output_dir / "stats_table_allrounds.txt"
    if stats_file.exists():
        target = run_dir / "stats_table_allrounds.txt"
        target.write_text(stats_file.read_text(encoding="utf-8"), encoding="utf-8")
        summary["statsTable"] = str(target)
    if output_dir.exists():
        raw["outputDir"] = str(output_dir)
    return summary, raw
