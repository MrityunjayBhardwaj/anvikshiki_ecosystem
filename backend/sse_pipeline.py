"""SSE event generator — wraps engine pipeline stages and yields ServerSentEvent objects."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterable

from fastapi.responses import StreamingResponse

from . import engine_state as _es
from anvikshiki_v4 import GroundingMode


def _mode_enum(mode: str) -> GroundingMode:
    try:
        return GroundingMode(mode)
    except ValueError:
        return GroundingMode.FULL


def _sse(event: str, data: dict) -> str:
    """Format a single SSE message as a string."""
    payload = json.dumps(data)
    return f"event: {event}\ndata: {payload}\n\n"


async def stream_query(query: str, mode: str) -> AsyncIterable[str]:
    """
    Runs engine pipeline stages, yielding SSE-formatted strings per stage.
    Using asyncio.Queue so the blocking engine calls run in a thread pool.
    """
    engine = _es.state.require()
    grounding_mode = _mode_enum(mode)
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def run() -> None:
        try:
            # Stage 1 — Grounding
            grounding_result = await asyncio.to_thread(
                engine.grounding.forward,
                query,
                grounding_mode,
            )
            await queue.put(_sse("stage:grounding", {
                "predicates": getattr(grounding_result, "predicates", []),
                "confidence": getattr(grounding_result, "confidence", 0.0),
                "mode": mode,
            }))

            # Stage 2 — Coverage
            predicates = getattr(grounding_result, "predicates", [])
            coverage_result = await asyncio.to_thread(
                engine.coverage_analyzer.analyze,
                predicates,
            )
            await queue.put(_sse("stage:coverage", {
                "coverage_ratio": getattr(coverage_result, "coverage_ratio", 0.0),
                "decision": getattr(coverage_result, "decision", "FULL"),
                "matched": getattr(coverage_result, "matched_predicates", []),
                "unmatched": getattr(coverage_result, "unmatched_predicates", []),
            }))

            # Stage 3 — Compilation (T2b)
            compilation_result = await asyncio.to_thread(
                engine.t2b_compiler.compile,
                predicates,
            )
            await queue.put(_sse("stage:compilation", {
                "argument_count": getattr(compilation_result, "argument_count", 0),
                "rule_count": getattr(compilation_result, "rule_count", 0),
            }))

            # Stage 4 — Extension (argumentation semantics)
            extension_result = await asyncio.to_thread(
                engine.argumentation.compute_extension,
            )
            await queue.put(_sse("stage:extension", {
                "extension_size": len(getattr(extension_result, "grounded_extension", [])),
                "labels": {k: v.value if hasattr(v, "value") else str(v)
                           for k, v in getattr(extension_result, "labels", {}).items()},
            }))

            # Stage 5 — Synthesis (full forward pass)
            full_result = await asyncio.to_thread(
                engine.forward_with_coverage,
                query,
            )
            await queue.put(_sse("stage:synthesis", {
                "response_preview": (full_result.response or "")[:200],
            }))

            # Complete — send full serialisable result
            result_dict = _prediction_to_dict(full_result)
            await queue.put(_sse("complete", result_dict))

        except Exception as exc:
            await queue.put(_sse("error", {"message": str(exc)}))
        finally:
            await queue.put(None)  # sentinel

    asyncio.create_task(run())

    while True:
        item = await queue.get()
        if item is None:
            break
        yield item


def _prediction_to_dict(pred) -> dict:
    """Convert a dspy.Prediction to a JSON-serialisable dict."""
    def _safe(val):
        if hasattr(val, "model_dump"):
            return val.model_dump()
        if hasattr(val, "__dict__"):
            return {k: _safe(v) for k, v in val.__dict__.items() if not k.startswith("_")}
        if isinstance(val, (list, tuple)):
            return [_safe(v) for v in val]
        if isinstance(val, dict):
            return {k: _safe(v) for k, v in val.items()}
        if hasattr(val, "value"):  # Enum
            return val.value
        return val

    fields = [
        "response", "sources", "uncertainty", "provenance", "violations",
        "grounding_confidence", "extension_size", "coverage",
        "augmentation", "contestation", "arguments", "attacks", "labels",
    ]
    return {f: _safe(getattr(pred, f, None)) for f in fields}
