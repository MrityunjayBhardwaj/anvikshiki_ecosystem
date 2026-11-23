"""Singleton engine state — holds the loaded KB and engine instance."""

from __future__ import annotations

import sys
import os
import time
from pathlib import Path

# Add project root to path so anvikshiki_v4 is importable
_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root))

from dotenv import load_dotenv

import dspy

from .debug import get_logger
from anvikshiki_v4 import initialize_engine, GroundingMode
from anvikshiki_v4 import lm_config

log = get_logger("anvikshiki.engine_state")


# ── LM configuration ─────────────────────────────────────────────────────────

def _configure_lm() -> None:
    """Configure DSPy LM from environment variables (and the repo's .env)."""
    log.debug("─" * 50)
    log.debug("LM CONFIGURATION START")
    load_dotenv(_root / ".env")  # never overrides a variable already set

    # Provider selection lives in anvikshiki_v4.lm_config so it is in the
    # repository and under test. Set ANVI_LM_PROVIDER to name one explicitly
    # (see lm_config.PROVIDERS for the names, kie among them); otherwise the
    # first provider with a key present wins, in lm_config.PROVIDER_ORDER.
    # ANVI_LM_MODEL overrides the model, ANVI_LM_MAX_TOKENS the output budget.
    #
    # Whether a key is set is all this logs. Any part of a key in a log is a
    # part of a secret in a file that gets pasted into issues.
    for _p in lm_config.PROVIDERS:
        _set = bool(os.environ.get(_p.env_key))
        log.debug(f"  {_p.env_key:20s}: {'SET' if _set else 'NOT SET'}")
    log.debug(f"  {lm_config.PROVIDER_ENV:20s}: "
              f"{os.environ.get(lm_config.PROVIDER_ENV) or 'NOT SET'}")

    provider, model_id = lm_config.configure_lm()
    log.debug(f"  → Provider : {provider.name}")
    log.debug(f"  → Model    : {model_id}")

    log.debug(f"  dspy.configure(lm={model_id!r}, adapter=JSONAdapter()) — done")
    log.debug("LM CONFIGURATION COMPLETE")
    log.debug("─" * 50)


def ensure_lm() -> None:
    """Configure the language model once, on the first query that needs it.

    Not at import: importing the backend then needed a provider key, so a
    machine without one could not even load a knowledge base, and every test
    importing the app got a process-wide model as a side effect. A missing
    key now fails the query that needed it, naming the variable.

    Call it from the event-loop thread, not a worker: DSPy only lets the
    thread that first configured it change its settings.
    """
    if dspy.settings.lm is None:
        _configure_lm()


# ── Engine singleton ──────────────────────────────────────────────────────────

class _EngineState:
    def __init__(self) -> None:
        self.engine = None
        self.artifacts = None
        self.kb_yaml_path: str | None = None
        self.kb_name: str | None = None
        self.loaded: bool = False

    def load(self, kb_yaml_path: str, guide_dir: str | None = None) -> dict:
        """Load (or reload) an engine from a KB YAML file."""
        log.debug("─" * 50)
        log.debug(f"KB LOAD START")
        log.debug(f"  kb_yaml_path : {kb_yaml_path}")
        log.debug(f"  guide_dir    : {guide_dir!r}")

        t0 = time.perf_counter()
        self.engine, self.artifacts = initialize_engine(
            kb_yaml_path=kb_yaml_path,
            guide_dir=guide_dir,
        )
        elapsed = time.perf_counter() - t0

        self.kb_yaml_path = kb_yaml_path
        self.kb_name = Path(kb_yaml_path).stem
        self.loaded = True

        # Log artifact summary
        if self.artifacts:
            arts = self.artifacts
            try:
                vyapti_count = len(arts.active_ks.vyaptis)
                hetvabhasa_count = len(arts.active_ks.hetvabhasas)
                chapter_count = len(arts.active_ks.chapter_fingerprints)
                chunk_count = len(arts.chunks) if arts.chunks else 0
                synonym_count = len(arts.synonym_table) if arts.synonym_table else 0
                log.debug(f"  artifacts.active_ks.vyaptis           : {vyapti_count}")
                log.debug(f"  artifacts.active_ks.hetvabhasas       : {hetvabhasa_count}")
                log.debug(f"  artifacts.active_ks.chapter_fingerprints: {chapter_count}")
                log.debug(f"  artifacts.chunks                      : {chunk_count}")
                log.debug(f"  artifacts.synonym_table               : {synonym_count} entries")
                log.debug(f"  t2b_result present                    : {arts.t2b_result is not None}")
                if arts.t2b_result is not None:
                    t2b = arts.t2b_result
                    log.debug(f"    t2b.augmented_ks.vyaptis          : {len(t2b.augmented_ks.vyaptis)}")
            except AttributeError as e:
                log.debug(f"  [artifact inspection error: {e}]")

        log.debug(f"KB LOAD COMPLETE  kb_name={self.kb_name!r}  elapsed={elapsed:.3f}s")
        log.debug("─" * 50)

        return {"kb_name": self.kb_name, "loaded": True}

    def require(self):
        """Raise if engine is not loaded."""
        if not self.loaded or self.engine is None:
            raise RuntimeError("No KB loaded. POST /kb/load first.")
        return self.engine


# Module-level singleton
state = _EngineState()
