"""FastAPI backend for the Ānvīkṣikī webapp.

Endpoints:
  GET  /health                  — liveness check
  POST /kb/load                 — load a KB YAML into the engine singleton
  GET  /kb/inspect              — inspect the loaded KB
  POST /api/query               — synchronous query (full result JSON)
  GET  /api/query/stream        — SSE stream (stage events + complete)
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .models import (
    EngineResult,
    HealthResponse,
    KBInfo,
    KBLoadRequest,
    QueryRequest,
)
from . import engine_state as _es
from .sse_pipeline import stream_query, _prediction_to_dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Could auto-load a default KB here if env var set
    yield


app = FastAPI(
    title="Ānvīkṣikī Engine API",
    version="0.4.0",
    description="Neurosymbolic reasoning engine — ASPIC+ argumentation + Subjective Logic",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        engine_loaded=_es.state.loaded,
        kb_name=_es.state.kb_name,
    )


# ── KB management ────────────────────────────────────────────────────────────

@app.post("/kb/load", response_model=KBInfo)
async def kb_load(req: KBLoadRequest) -> KBInfo:
    if not Path(req.kb_yaml_path).exists():
        raise HTTPException(status_code=404, detail=f"KB file not found: {req.kb_yaml_path}")
    try:
        info = _es.state.load(kb_yaml_path=req.kb_yaml_path, guide_dir=req.guide_dir)
        engine = _es.state.require()
        # Best-effort: get vyapti count from engine artifacts
        vyapti_count = 0
        arg_count = 0
        if _es.state.artifacts:
            arts = _es.state.artifacts
            vyapti_count = getattr(arts, "vyapti_count", 0)
            arg_count = getattr(arts, "argument_count", 0)
        return KBInfo(
            kb_name=info["kb_name"],
            vyapti_count=vyapti_count,
            argument_count=arg_count,
            loaded=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/kb/inspect", response_model=KBInfo)
async def kb_inspect() -> KBInfo:
    if not _es.state.loaded:
        return KBInfo(kb_name="", vyapti_count=0, argument_count=0, loaded=False)
    arts = _es.state.artifacts
    return KBInfo(
        kb_name=_es.state.kb_name or "",
        vyapti_count=getattr(arts, "vyapti_count", 0) if arts else 0,
        argument_count=getattr(arts, "argument_count", 0) if arts else 0,
        loaded=True,
    )


# ── Query ─────────────────────────────────────────────────────────────────────

@app.post("/api/query")
async def query(req: QueryRequest) -> dict:
    """Synchronous query — blocks until full result ready. Returns EngineResult JSON."""
    try:
        engine = _es.state.require()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    import asyncio
    try:
        result = await asyncio.to_thread(engine.forward_with_coverage, req.query)
        return _prediction_to_dict(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/query/stream")
async def query_stream(query: str, mode: str = "partial") -> StreamingResponse:
    """
    SSE endpoint — emits stage events as the pipeline executes.
    Events: stage:grounding, stage:coverage, stage:compilation,
            stage:extension, stage:synthesis, complete, error
    """
    try:
        _es.state.require()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return StreamingResponse(
        stream_query(query, mode),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── Dev entrypoint ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
