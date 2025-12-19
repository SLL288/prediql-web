from __future__ import annotations

import asyncio
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.runs import router as runs_router
from app.core.models import settings
from app.core.storage import RunRegistry

app = FastAPI(title="PrediQL Backend", version="0.1.0")

allowed_origins: List[str] = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

registry = RunRegistry(settings.RUNS_DIR)
runs_router.registry = registry  # type: ignore[attr-defined]
app.include_router(runs_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    registry.runs_dir.mkdir(parents=True, exist_ok=True)
