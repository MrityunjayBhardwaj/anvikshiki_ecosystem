"""FastAPI backend for the Ānvīkṣikī webapp.

Endpoints:
  GET  /health                  — liveness check
  POST /kb/load                 — load a KB YAML into the engine singleton
  GET  /kb/inspect              — inspect the loaded KB
  POST /api/query               — synchronous query (full result JSON)
  GET  /api/query/stream        — SSE stream (stage events + complete)
"""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .models import (
    HealthResponse,
    KBInfo,
    KBLoadRequest,
    QueryRequest,
)
from . import engine_state as _es
from .debug import get_logger
from anvikshiki_v4.lm_config import NoProviderAvailable
from .sse_pipeline import stream_query, _prediction_to_dict, mode_enum, client_message

log = get_logger("anvikshiki.api")

# Project root = directory containing `backend/` (i.e. anvikshiki_ecosystem/)
_PROJECT_ROOT = Path(__file__).parent.parent


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log.debug("FastAPI lifespan start — the LM is configured on the first query")
    yield
    log.debug("FastAPI lifespan end")


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


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    log.debug("GET /health  engine_loaded=%s  kb_name=%r",
              _es.state.loaded, _es.state.kb_name)
    return HealthResponse(
        status="ok",
        engine_loaded=_es.state.loaded,
        kb_name=_es.state.kb_name,
    )


# ── KB management ─────────────────────────────────────────────────────────────

def _kb_counts(arts) -> tuple[int, int]:
    """Rules and declared fallacies in the active base.

    A freshly loaded base has no arguments: those are built per query. The
    second count used to be sent as `argument_count`, which named it as
    something it is not.
    """
    if arts is None:
        return 0, 0
    ks = arts.active_ks
    return len(ks.vyaptis), len(ks.hetvabhasas)


@app.post("/kb/load", response_model=KBInfo)
async def kb_load(req: KBLoadRequest) -> KBInfo:
    log.debug("POST /kb/load  path=%r  guide_dir=%r", req.kb_yaml_path, req.guide_dir)

    # A relative path is the repo's, as the loader reads it, never the
    # process's cwd: otherwise a backend started elsewhere 404s on a path the
    # loader would have found, naming the file as missing (#108).
    kb_path = Path(req.kb_yaml_path)
    if not kb_path.is_absolute():
        kb_path = _PROJECT_ROOT / kb_path
        log.debug("  resolved relative path → %s", kb_path)

    if not kb_path.exists():
        log.error("KB file not found: %s", kb_path)
        raise HTTPException(status_code=404, detail=f"KB file not found: {kb_path}")

    t0 = time.perf_counter()
    try:
        info = _es.state.load(kb_yaml_path=str(kb_path), guide_dir=req.guide_dir)
        _es.state.require()

        vyapti_count, hetvabhasa_count = _kb_counts(_es.state.artifacts)

        elapsed = time.perf_counter() - t0
        log.debug("POST /kb/load COMPLETE  kb=%r  vyaptis=%d  hetvabhasas=%d  [%.3fs]",
                  info["kb_name"], vyapti_count, hetvabhasa_count, elapsed)

        return KBInfo(
            kb_name=info["kb_name"],
            vyapti_count=vyapti_count,
            hetvabhasa_count=hetvabhasa_count,
            loaded=True,
        )
    except Exception as exc:
        log.error("POST /kb/load FAILED: %s: %s", type(exc).__name__, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/kb/inspect", response_model=KBInfo)
async def kb_inspect() -> KBInfo:
    log.debug("GET /kb/inspect  loaded=%s", _es.state.loaded)
    if not _es.state.loaded:
        return KBInfo(kb_name="", vyapti_count=0, hetvabhasa_count=0, loaded=False)
    vyapti_count, hetvabhasa_count = _kb_counts(_es.state.artifacts)
    log.debug("  kb=%r  vyaptis=%d  hetvabhasas=%d",
              _es.state.kb_name, vyapti_count, hetvabhasa_count)
    return KBInfo(
        kb_name=_es.state.kb_name or "",
        vyapti_count=vyapti_count,
        hetvabhasa_count=hetvabhasa_count,
        loaded=True,
    )


# ── Query ─────────────────────────────────────────────────────────────────────

@app.post("/api/query")
async def query(req: QueryRequest) -> dict:
    """Synchronous query — blocks until full result ready. Returns EngineResult JSON."""
    log.debug("POST /api/query  query=%r  mode=%r", req.query[:80], req.mode)
    try:
        engine = _es.state.require()
    except RuntimeError as exc:
        log.error("POST /api/query — engine not loaded: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        mode = mode_enum(req.mode)
        _es.ensure_lm()
    except (ValueError, NoProviderAvailable) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    t0 = time.perf_counter()
    try:
        result = await asyncio.to_thread(
            engine.forward_with_coverage, req.query, mode=mode,
        )
        elapsed = time.perf_counter() - t0
        result_dict = _prediction_to_dict(result)
        log.debug("POST /api/query COMPLETE  args=%d  attacks=%d  conf=%.4f  [%.3fs]",
                  len(result_dict.get("arguments") or {}),
                  len(result_dict.get("attacks") or []),
                  result_dict.get("grounding_confidence") or 0.0,
                  elapsed)
        return result_dict
    except Exception as exc:
        log.error("POST /api/query FAILED: %s: %s", type(exc).__name__, exc)
        raise HTTPException(status_code=500, detail=client_message(exc)) from exc


@app.get("/api/query/stream")
async def query_stream(query: str, mode: str = "partial") -> StreamingResponse:
    """
    SSE endpoint — emits stage events as the pipeline executes.
    Events: stage:grounding, stage:coverage, stage:compilation,
            stage:extension, stage:synthesis, complete, error
    """
    log.debug("GET /api/query/stream  query=%r  mode=%r", query[:80], mode)
    try:
        _es.state.require()
    except RuntimeError as exc:
        log.error("GET /api/query/stream — engine not loaded: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        mode_enum(mode)
        _es.ensure_lm()
    except (ValueError, NoProviderAvailable) as exc:
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
