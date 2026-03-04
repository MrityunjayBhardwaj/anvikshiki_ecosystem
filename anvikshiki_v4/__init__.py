# anvikshiki_v4 — Neurosymbolic argumentation engine (ASPIC+ over provenance semirings)

from .schema_v4 import (
    ProvenanceTag, PramanaType, RuleType, EpistemicStatus,
    Label, Argument, Attack,
)
from .argumentation import ArgumentationFramework
from .t2_compiler_v4 import compile_t2, load_knowledge_store
from .uncertainty import compute_uncertainty_v4
from .contestation import ContestationManager

__all__ = [
    "ProvenanceTag", "PramanaType", "RuleType", "EpistemicStatus",
    "Label", "Argument", "Attack",
    "ArgumentationFramework",
    "compile_t2", "load_knowledge_store",
    "compute_uncertainty_v4",
    "ContestationManager",
]
