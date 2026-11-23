"""SSE event generator — wraps engine pipeline stages and yields ServerSentEvent objects."""

from __future__ import annotations

import asyncio
import enum
import json
import time
import traceback
from collections.abc import AsyncIterable

from . import engine_state as _es
from .debug import DEBUG_MODE, get_logger
from anvikshiki_v4 import GroundingMode

log = get_logger("anvikshiki.sse_pipeline")


# ── Helpers ───────────────────────────────────────────────────────────────────

def mode_enum(mode: str) -> GroundingMode:
    """The grounding mode a request names.

    An unknown name raises rather than quietly running in full mode: a
    request that asked for something else and got full would report its
    timing and confidence as if they were what it asked for.
    """
    try:
        return GroundingMode(mode)
    except ValueError:
        known = ", ".join(m.value for m in GroundingMode)
        raise ValueError(f"unknown mode {mode!r}; known: {known}") from None


def client_message(exc: BaseException, limit: int = 300) -> str:
    """What a client is told when the engine fails: the type and first line.

    `str(exc)` of a provider error is the whole chained traceback with the
    response headers, about 20 KB from litellm, and the webapp showed every
    byte of it. The full traceback goes to the server log instead.
    """
    first = next((ln.strip() for ln in str(exc).splitlines() if ln.strip()), "")
    if len(first) > limit:
        first = first[:limit] + "…"
    return f"{type(exc).__name__}: {first}" if first else type(exc).__name__


def _sse(event: str, data: dict) -> str:
    payload = json.dumps(data)
    return f"event: {event}\ndata: {payload}\n\n"


def _safe(val):
    """Recursively convert any value to a JSON-serialisable form.

    Handles: None, callables, Enums, Pydantic, dspy.Prediction (_store),
    dicts, lists, objects with __dict__, primitives.
    """
    if val is None:
        return None

    # ── Callables (functions, methods, built-ins) ────────────────────────────
    # Must come BEFORE __dict__ check — functions have __dict__ too.
    if callable(val) and not isinstance(val, type):
        return f"<callable:{type(val).__name__}:{getattr(val, '__name__', '?')}>"

    # ── Pydantic models ──────────────────────────────────────────────────────
    if hasattr(val, "model_dump"):
        try:
            return val.model_dump()
        except Exception:
            pass

    # ── DSPy Prediction / modules (check _store before __dict__) ────────────
    if hasattr(val, "_store") and isinstance(getattr(val, "_store", None), dict):
        try:
            return {k: _safe(v) for k, v in val._store.items()}
        except Exception:
            pass

    # ── Enum ─────────────────────────────────────────────────────────────────
    if isinstance(val, enum.Enum):
        return val.value

    # ── set / frozenset (provenance tags carry source ids as frozensets) ─────
    if isinstance(val, (set, frozenset)):
        return sorted(_safe(v) for v in val)

    # ── dict ─────────────────────────────────────────────────────────────────
    if isinstance(val, dict):
        result = {}
        for k, v in val.items():
            try:
                result[k] = _safe(v)
            except Exception:
                result[k] = str(v)
        return result

    # ── list / tuple ─────────────────────────────────────────────────────────
    if isinstance(val, (list, tuple)):
        return [_safe(v) for v in val]

    # ── General objects with __dict__ (excluding internals) ──────────────────
    if hasattr(val, "__dict__") and not isinstance(val, type):
        result = {}
        for k, v in val.__dict__.items():
            if k.startswith("_"):
                continue
            try:
                result[k] = _safe(v)
            except Exception:
                result[k] = str(v)
        return result

    # ── Primitives (int, float, str, bool) ───────────────────────────────────
    return val


# Always sent, as null when the engine path did not set them, because the
# webapp's schema requires them. Every other field the engine returns is sent
# too: a fixed list here is how the verdict, the derivation and the
# advisories were dropped without anything noticing.
_REQUIRED_FIELDS = (
    "response", "sources", "uncertainty", "provenance", "violations",
    "grounding_confidence", "extension_size", "coverage",
    "augmentation", "contestation", "arguments", "attacks", "labels",
)


def _prediction_to_dict(pred) -> dict:
    """Convert a dspy.Prediction to a fully JSON-serialisable dict."""
    fields = list(dict.fromkeys([*_REQUIRED_FIELDS, *pred.keys()]))
    result = {}
    for f in fields:
        try:
            # pred.get, not getattr: dspy.Prediction inherits Example.labels(),
            # so getattr(pred, "labels") returns the bound method and never the
            # field — silently. .get reads the store, where the engine's fields
            # actually live.
            result[f] = _safe(pred.get(f))
        except Exception as e:
            result[f] = f"<error serializing {f}: {e}>"
    return result


# ── DSPy LM call logger ───────────────────────────────────────────────────────

def _log_dspy_history(n: int = 20) -> None:
    """Log the last N DSPy LM calls (prompts + responses) at DEBUG level."""
    if not DEBUG_MODE:
        return
    try:
        import dspy as _dspy
        lm = _dspy.settings.lm
        history = getattr(lm, "history", None)
        if not history:
            log.debug("[DSPy LM history] — no calls recorded yet")
            return

        recent = history[-n:]
        log.debug("╔══════════════════════════════════════════════════════════╗")
        log.debug("║  DSPy LM CALL HISTORY  (last %d of %d total)  ║", len(recent), len(history))
        log.debug("╚══════════════════════════════════════════════════════════╝")

        for idx, call in enumerate(recent, 1):
            log.debug("┌─ LM Call #%d %s", idx, "─" * 42)

            # ── Input messages (prompt) ──────────────────────────────────
            messages = call.get("messages") or []
            for msg in messages:
                role    = (msg.get("role") or "unknown").upper()
                content = msg.get("content") or ""
                if isinstance(content, str):
                    lines = content.splitlines()
                    log.debug("│  [%s] (%d chars, %d lines)", role, len(content), len(lines))
                    for line in content.splitlines():
                        log.debug("│    %s", line[:200])
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text = part.get("text", "")
                            log.debug("│  [%s] (%d chars)", role, len(text))
                            for line in text.splitlines():
                                log.debug("│    %s", line[:200])

            # ── Model + params ───────────────────────────────────────────
            kwargs = call.get("kwargs") or {}
            log.debug("│  model        : %s", call.get("model") or kwargs.get("model") or "?")
            log.debug("│  temperature  : %s", kwargs.get("temperature", "?"))
            log.debug("│  max_tokens   : %s", kwargs.get("max_tokens", "?"))

            # ── Response ─────────────────────────────────────────────────
            response = call.get("response")
            if response is not None:
                if hasattr(response, "choices") and response.choices:
                    choice  = response.choices[0]
                    content = getattr(getattr(choice, "message", None), "content", None) or ""
                    usage   = getattr(response, "usage", None)
                    log.debug("│  [RESPONSE] (%d chars)", len(content))
                    for line in content.splitlines():
                        log.debug("│    %s", line[:300])
                    if usage:
                        log.debug("│  tokens: prompt=%s  completion=%s  total=%s",
                                  getattr(usage, "prompt_tokens", "?"),
                                  getattr(usage, "completion_tokens", "?"),
                                  getattr(usage, "total_tokens", "?"))
                elif isinstance(response, dict):
                    for k, v in response.items():
                        log.debug("│  response.%s : %s", k, str(v)[:200])
                else:
                    log.debug("│  [RESPONSE] %s", str(response)[:400])

            # ── Cost + timing ────────────────────────────────────────────
            cost = call.get("cost")
            if cost is not None:
                log.debug("│  cost : $%.6f", cost)

            log.debug("└%s", "─" * 54)

    except Exception as e:
        log.debug("[DSPy LM history logging failed: %s: %s]", type(e).__name__, e)


# ── Main SSE generator ────────────────────────────────────────────────────────

async def stream_query(query: str, mode: str) -> AsyncIterable[str]:
    """
    Runs the full engine pipeline in a thread, serializes the result, then
    emits 5 stage SSE events + 'complete'. All events fire after the single
    engine.forward_with_coverage() call returns.
    """
    engine = _es.state.require()
    grounding_mode = mode_enum(mode)
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    log.debug("═" * 60)
    log.debug("STREAM QUERY RECEIVED")
    log.debug("  query  : %r", query[:200])
    log.debug("  mode   : %s", mode)
    log.debug("  engine : %s", type(engine).__name__)
    log.debug("═" * 60)

    async def run() -> None:
        t_total = time.perf_counter()
        try:
            # ── 1. Engine call ────────────────────────────────────────────────
            log.debug("→ [ENGINE] forward_with_coverage() starting ...")
            t0 = time.perf_counter()
            full_result = await asyncio.to_thread(
                engine.forward_with_coverage, query, mode=grounding_mode,
            )
            t_engine = time.perf_counter() - t0
            log.debug("← [ENGINE] forward_with_coverage() done  [%.3fs]", t_engine)

            # ── 2. DSPy LM call history ───────────────────────────────────────
            _log_dspy_history(n=20)

            # ── 3. Serialize result safely (MUST come before any field access) ─
            log.debug("→ [SERIALIZE] Converting dspy.Prediction to dict ...")
            result_dict = _prediction_to_dict(full_result)
            log.debug("← [SERIALIZE] done  keys=%s", list(result_dict.keys()))

            # ── 4. Log every field of the serialized result ───────────────────
            if DEBUG_MODE:
                log.debug("┌─ FULL RESULT DUMP %s", "─" * 40)
                for field, val in result_dict.items():
                    if val is None:
                        log.debug("│  %-25s : None", field)
                    elif isinstance(val, str):
                        log.debug("│  %-25s : %r  (%d chars)", field, val[:120], len(val))
                    elif isinstance(val, dict):
                        log.debug("│  %-25s : dict(%d keys)  keys=%s",
                                  field, len(val), list(val.keys())[:10])
                    elif isinstance(val, list):
                        log.debug("│  %-25s : list(%d items)", field, len(val))
                    else:
                        log.debug("│  %-25s : %r", field, val)
                log.debug("└%s", "─" * 59)

            # ── Extract stage data from safe dict ─────────────────────────────
            conf       = result_dict.get("grounding_confidence") or 0.0
            cov_dict   = result_dict.get("coverage") or {}
            args       = result_dict.get("arguments") or {}
            attacks    = result_dict.get("attacks") or []
            labels     = result_dict.get("labels") or {}
            response   = result_dict.get("response") or ""
            sources    = result_dict.get("sources") or []
            violations = result_dict.get("violations") or []
            uncertainty  = result_dict.get("uncertainty") or {}
            provenance   = result_dict.get("provenance") or {}
            ext_size     = result_dict.get("extension_size") or 0
            augmentation = result_dict.get("augmentation")
            contestation = result_dict.get("contestation")

            label_vals = list(labels.values()) if isinstance(labels, dict) else []
            in_count   = sum(1 for v in label_vals if v in ("in",  "Label.in"))
            out_count  = sum(1 for v in label_vals if v in ("out", "Label.out"))
            und_count  = len(label_vals) - in_count - out_count

            # ── STAGE 1: Grounding ────────────────────────────────────────────
            log.debug("┌─ STAGE 1: GROUNDING %s", "─" * 38)
            log.debug("│  grounding_confidence : %.6f", conf)
            log.debug("│  mode                 : %s", mode)
            log.debug("└%s", "─" * 59)
            grounding_data = {"confidence": conf, "mode": mode}
            await queue.put(_sse("stage:grounding", grounding_data))

            # ── STAGE 2: Coverage ─────────────────────────────────────────────
            # No coverage means it never ran (grounding asked for
            # clarification first). That is said as such: defaulting to FULL
            # at 0.0 reported a check that did not happen as one that passed.
            ran              = isinstance(cov_dict, dict) and bool(cov_dict)
            coverage_ratio   = cov_dict.get("coverage_ratio") if ran else None
            decision         = cov_dict.get("decision") if ran else "NOT_RUN"
            matched          = cov_dict.get("matched_predicates", []) if ran else []
            unmatched        = cov_dict.get("unmatched_predicates", []) if ran else []
            match_details    = cov_dict.get("match_details", {}) if ran else {}
            relevant_vyaptis = cov_dict.get("relevant_vyaptis", []) if ran else []

            log.debug("┌─ STAGE 2: COVERAGE %s", "─" * 39)
            log.debug("│  coverage_ratio   : %s", coverage_ratio)
            log.debug("│  decision         : %s", decision)
            log.debug("│  matched_preds    : %s", matched)
            log.debug("│  unmatched_preds  : %s", unmatched)
            log.debug("│  relevant_vyaptis : %s", relevant_vyaptis)
            if match_details:
                log.debug("│  match_details:")
                for pred_name, detail in match_details.items():
                    log.debug("│    %-25s → %s", pred_name, detail)
            log.debug("└%s", "─" * 59)

            coverage_data = {
                "coverage_ratio": coverage_ratio,
                "decision": decision,
                "matched": matched,
                "unmatched": unmatched,
            }
            await queue.put(_sse("stage:coverage", coverage_data))

            # ── STAGE 3: Compilation ──────────────────────────────────────────
            log.debug("┌─ STAGE 3: COMPILATION %s", "─" * 36)
            log.debug("│  argument_count : %d", len(args))
            log.debug("│  attack_count   : %d", len(attacks))
            if isinstance(args, dict) and args:
                log.debug("│  arguments (all %d):", len(args))
                for arg_id, arg in args.items():
                    if isinstance(arg, dict):
                        conc  = arg.get("conclusion", "?")
                        lbl   = arg.get("label", "?")
                        rt    = arg.get("rule_type", "?")
                        prems = arg.get("premises", [])
                        tag   = arg.get("tag") or {}
                        pram  = tag.get("pramana_type", "?") if isinstance(tag, dict) else "?"
                        ep    = arg.get("epistemic_status", "?")
                        log.debug("│  [%s]", str(arg_id)[:12])
                        log.debug("│    label     : %s", lbl)
                        log.debug("│    rule_type : %s", rt)
                        log.debug("│    epistemic : %s", ep)
                        log.debug("│    status    : %s", arg.get("status", "?"))
                        log.debug("│    pramana   : %s", pram)
                        log.debug("│    premises  : %s", prems)
                        log.debug("│    conclusion: %s", str(conc)[:120])
            if isinstance(attacks, list) and attacks:
                log.debug("│  attacks (all %d):", len(attacks))
                for atk in attacks:
                    if isinstance(atk, dict):
                        log.debug("│    [%s] %s → %s  hetvabhasa=%s",
                                  atk.get("attack_type", "?"),
                                  str(atk.get("attacker", "?"))[:12],
                                  str(atk.get("target", "?"))[:12],
                                  atk.get("hetvabhasa", "none"))
            log.debug("└%s", "─" * 59)

            compilation_data = {"argument_count": len(args)}
            await queue.put(_sse("stage:compilation", compilation_data))

            # ── STAGE 4: Extension ────────────────────────────────────────────
            log.debug("┌─ STAGE 4: EXTENSION %s", "─" * 38)
            log.debug("│  extension_size : %d", ext_size)
            log.debug("│  IN       : %d", in_count)
            log.debug("│  OUT      : %d", out_count)
            log.debug("│  UNDECIDED: %d", und_count)
            if isinstance(labels, dict) and labels:
                log.debug("│  label map (all %d):", len(labels))
                for arg_id, lbl in labels.items():
                    log.debug("│    %-15s → %s", str(arg_id)[:15], lbl)
            if uncertainty:
                log.debug("│  uncertainty (all %d):", len(uncertainty))
                for conc, u in uncertainty.items():
                    log.debug("│    %-25s : %s", str(conc)[:25], u)
            if provenance:
                log.debug("│  provenance (all %d):", len(provenance))
                for conc, p in provenance.items():
                    log.debug("│    %-25s : %s", str(conc)[:25], p)
            log.debug("└%s", "─" * 59)

            extension_data = {"extension_size": ext_size, "in_count": in_count, "out_count": out_count}
            await queue.put(_sse("stage:extension", extension_data))

            # ── STAGE 5: Synthesis ────────────────────────────────────────────
            log.debug("┌─ STAGE 5: SYNTHESIS %s", "─" * 38)
            log.debug("│  response (%d chars):", len(response))
            for line in response.splitlines():
                log.debug("│    %s", line[:300])
            log.debug("│  sources (%d):", len(sources))
            for s in sources:
                log.debug("│    %s", s)
            log.debug("│  violations (%d):", len(violations))
            for v in violations:
                log.debug("│    %s", v)
            log.debug("│  augmentation : %s", augmentation)
            log.debug("│  contestation : %s", contestation)
            log.debug("└%s", "─" * 59)

            synthesis_data = {"response_preview": response[:200]}
            await queue.put(_sse("stage:synthesis", synthesis_data))

            # ── Complete ──────────────────────────────────────────────────────
            t_total_elapsed = time.perf_counter() - t_total
            log.debug("┌─ COMPLETE %s", "─" * 48)
            log.debug("│  engine wall time : %.3fs", t_engine)
            log.debug("│  total wall time  : %.3fs", t_total_elapsed)
            log.debug("│  sending complete event ...")
            log.debug("└%s", "─" * 59)

            await queue.put(_sse("complete", result_dict))
            log.debug("═" * 60)
            log.debug("STREAM QUERY DONE  engine=%.3fs  total=%.3fs", t_engine, t_total_elapsed)
            log.debug("═" * 60)

        except Exception as exc:
            log.error("╔═ STREAM QUERY ERROR ══════════════════════════════════╗")
            log.error("║  %s: %s", type(exc).__name__, exc)
            log.error("╚═══════════════════════════════════════════════════════╝")
            log.error("Full traceback:\n%s", traceback.format_exc())
            await queue.put(_sse("error", {"message": client_message(exc),
                                           "type": type(exc).__name__}))
        finally:
            await queue.put(None)  # sentinel

    asyncio.create_task(run())

    while True:
        item = await queue.get()
        if item is None:
            break
        yield item
