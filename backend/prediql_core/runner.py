from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import httpx

from models import RunConfig

INTROSPECTION_QUERY = {
    "query": """
    query PrediQLIntrospection { __schema { queryType { name } mutationType { name } types { name kind } } }
    """,
    "variables": {},
}


async def _test_endpoint(endpoint_url: str, headers: Optional[Dict[str, str]], log):
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            response = await client.post(endpoint_url, json=INTROSPECTION_QUERY, headers=headers)
            response.raise_for_status()
            json_resp = response.json()
            log(f"Introspection response keys: {list(json_resp.keys())}")
            return json_resp
        except Exception as exc:  # noqa: BLE001
            log(f"Introspection attempt failed: {exc}")
            return None


async def run_prediql(config: RunConfig, llm_client, log, progress_cb=None) -> Dict[str, Any]:
    """MVP runner that approximates the PrediQL pipeline without disk secrets."""

    log("Starting PrediQL lightweight run")
    log(f"Target endpoint: {config.endpoint_url}")
    log(f"Rounds: {config.rounds}, Requests per node: {config.requests_per_node}")

    schema_info = await _test_endpoint(config.endpoint_url, config.headers, log)

    findings: List[Dict[str, Any]] = []
    total_steps = max(1, config.rounds * config.requests_per_node)
    completed = 0

    for round_index in range(config.rounds):
        log(f"Round {round_index + 1}/{config.rounds}: exploring schema")
        await asyncio.sleep(0.05)
        for req_index in range(config.requests_per_node):
            hint_prompt = (
                f"Given the GraphQL schema insights {schema_info}, suggest a potential test query "
                f"({req_index + 1}/{config.requests_per_node}) for round {round_index + 1}."
            )
            suggestion = await llm_client.generate(hint_prompt) if llm_client else "(LLM disabled)"
            finding = {
                "round": round_index + 1,
                "request": req_index + 1,
                "suggestion": suggestion,
            }
            findings.append(finding)
            log(f"Generated query idea #{req_index + 1}: {suggestion[:120]}")
            await asyncio.sleep(0.02)
            completed += 1
            if progress_cb:
                progress_cb(min(0.95, completed / total_steps))

    summary_lines = [
        "PrediQL exploration finished.",
        f"Endpoint: {config.endpoint_url}",
        f"Rounds: {config.rounds}",
        f"Requests per node: {config.requests_per_node}",
    ]
    if schema_info:
        summary_lines.append("Schema introspection succeeded.")
    else:
        summary_lines.append("Schema introspection failed; proceeded with heuristic generation.")

    summary = "\n".join(summary_lines)
    log("Run complete; compiling summary and artifacts")

    return {
        "endpoint": config.endpoint_url,
        "llmProvider": config.llm_provider,
        "model": config.model,
        "rounds": config.rounds,
        "requestsPerNode": config.requests_per_node,
        "schemaIntrospection": schema_info,
        "findings": findings,
        "summary": summary,
    }
