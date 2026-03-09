"""Singleton engine state — holds the loaded KB and engine instance."""

from __future__ import annotations

import sys
import os
from pathlib import Path

# Add project root to path so anvikshiki_v4 is importable
_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root))

from anvikshiki_v4 import initialize_engine, GroundingMode


class _EngineState:
    def __init__(self) -> None:
        self.engine = None
        self.artifacts = None
        self.kb_yaml_path: str | None = None
        self.kb_name: str | None = None
        self.loaded: bool = False

    def load(self, kb_yaml_path: str, guide_dir: str | None = None) -> dict:
        """Load (or reload) an engine from a KB YAML file."""
        self.engine, self.artifacts = initialize_engine(
            kb_yaml_path=kb_yaml_path,
            guide_dir=guide_dir,
        )
        self.kb_yaml_path = kb_yaml_path
        self.kb_name = Path(kb_yaml_path).stem
        self.loaded = True
        return {
            "kb_name": self.kb_name,
            "loaded": True,
        }

    def require(self):
        """Raise if engine is not loaded."""
        if not self.loaded or self.engine is None:
            raise RuntimeError("No KB loaded. POST /kb/load first.")
        return self.engine


# Module-level singleton
state = _EngineState()
