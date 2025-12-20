from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

from fastapi import HTTPException

from app.core.graphql_client import GraphQLClient
from app.core.models import Progress, RunConfig, RunStatus, settings
from app.core.ollama_client import OllamaClient
from app.core.openai_client import OpenAIClient
from app.core.gemini_client import GeminiClient
from app.core.storage import RunRegistry
from app.core.utils import parse_headers


def _build_llm_client(config: RunConfig):
    if config.llm_provider == "ollama":
        return OllamaClient(model=config.model or settings.DEFAULT_MODEL)
    if config.llm_provider == "openai_compatible":
        if not config.api_key:
            raise HTTPException(status_code=400, detail="apiKey required for openai_compatible")
        return OpenAIClient(api_key=config.api_key, model=config.model or "gpt-4o-mini", base_url=settings.OPENAI_BASE_URL)
    if config.llm_provider == "gemini":
        if not config.api_key:
            raise HTTPException(status_code=400, detail="apiKey required for gemini")
        return GeminiClient(api_key=config.api_key, model=config.model or "gemini-1.5-flash", base_url=settings.GEMINI_BASE_URL)
    raise HTTPException(status_code=400, detail="Unsupported llmProvider")


async def run_job(run_id: str, config: RunConfig, registry: RunRegistry) -> None:
    headers = parse_headers(config.graphql_headers_json)
    graph_client = GraphQLClient(config.endpoint_url, headers=headers)
    llm_client = _build_llm_client(config)

    async def log(msg: str) -> None:
        await registry.append_log(run_id, msg)

    async def update_progress(pct: float, stage: str, detail: str | None = None) -> None:
        await registry.update_status(run_id, progress=Progress(pct=min(max(pct, 0.0), 1.0), stage=stage, detail=detail))

    try:
        await registry.update_status(run_id, status=RunStatus.running)
        await update_progress(0.02, "initializing")
        await log("Fetching GraphQL introspection...")
        introspection = await graph_client.fetch_introspection()
        schema_summary = summarize_introspection(introspection)
        await log(f"Introspection summary: {schema_summary.get('counts')}")

        await update_progress(0.15, "generating_candidates")
        candidates: List[Dict[str, Any]] = []
        for r in range(config.rounds):
            if await registry.is_cancelled(run_id):
                raise CancelledError()
            await log(f"Round {r + 1}/{config.rounds}: asking LLM for candidates")
            batch = await llm_client.generate_candidates(json.dumps(schema_summary), config.requests_per_node)
            candidates.extend(batch)
            await update_progress(0.15 + (0.25 * (r + 1) / max(config.rounds, 1)), "generating_candidates")
            await asyncio.sleep(0.2)

        await log(f"Generated {len(candidates)} candidate queries")

        await update_progress(0.45, "executing_candidates")
        executions = []
        for idx, cand in enumerate(candidates[: config.requests_per_node * config.rounds]):
            if await registry.is_cancelled(run_id):
                raise CancelledError()
            q = cand.get("query") or cand.get("ql") or ""
            if not q:
                continue
            resp = await graph_client.execute_query(q)
            status = "ok" if resp is not None else "error"
            executions.append({"index": idx, "query": q, "response": resp, "status": status})
            await log(f"Executed candidate #{idx + 1}: status={status}")
            await update_progress(0.45 + 0.4 * (idx + 1) / max(len(candidates), 1), "executing_candidates")
            await asyncio.sleep(0.1)

        summary = {
            "endpoint": config.endpoint_url,
            "counts": schema_summary.get("counts", {}),
            "candidates": len(candidates),
            "executions": len(executions),
            "notes": config.notes,
        }

        raw = {
            "schema": schema_summary,
            "candidates": candidates,
            "executions": executions,
            "summary": summary,
        }

        await update_progress(0.9, "saving")
        await registry.save_results(run_id, summary=summary, raw_json=raw)
        await registry.update_status(run_id, status=RunStatus.done, progress=Progress(pct=1.0, stage="done"))
        await log("Run complete. Artifacts written.")

    except CancelledError:
        await log("Run cancelled")
        await registry.update_status(run_id, status=RunStatus.cancelled, progress=Progress(pct=0.0, stage="cancelled"))
    except HTTPException as exc:
        await registry.append_log(run_id, f"Validation failed: {exc.detail}")
        await registry.update_status(run_id, status=RunStatus.failed, error=str(exc.detail))
    except Exception as exc:  # noqa: BLE001
        await registry.append_log(run_id, f"Run failed: {exc}")
        await registry.update_status(run_id, status=RunStatus.failed, error=str(exc))


class CancelledError(Exception):
    """Raised when a cancel request is detected."""


def summarize_introspection(introspection: dict | None) -> Dict[str, Any]:
    if not introspection or "data" not in introspection:
        return {"counts": {"types": 0, "queries": 0, "mutations": 0}, "raw": introspection}
    schema = introspection.get("data", {}).get("__schema", {})
    types = schema.get("types") or []
    counts = {
        "types": len(types),
        "queries": 1 if schema.get("queryType") else 0,
        "mutations": 1 if schema.get("mutationType") else 0,
    }
    return {"counts": counts, "raw": introspection}
