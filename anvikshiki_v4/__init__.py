# anvikshiki_v4 — Neurosymbolic argumentation engine (ASPIC+ over provenance semirings)

from .schema_v4 import (
    ProvenanceTag, PramanaType, RuleType, EpistemicStatus,
    Label, Argument, Attack,
)
from .schema import AugmentationOrigin, AugmentationMetadata
from .argumentation import ArgumentationFramework
from .t2_compiler_v4 import compile_t2, precompile_kb, load_knowledge_store
from .t2b_compiler import compile_t2b, T2bResult
from .coverage import SemanticCoverageAnalyzer, CoverageResult
from .kb_augmentation import AugmentationPipeline, AugmentationResult
from .t3a_retriever import T3aRetriever
from .engine_factory import initialize_engine, load_guide_dir, CompileArtifacts
from .uncertainty import compute_uncertainty_v4
from .contestation import ContestationManager
from .grounding import GroundingMode
from .reasoning_lm import ReasoningLM

__all__ = [
    "ProvenanceTag", "PramanaType", "RuleType", "EpistemicStatus",
    "Label", "Argument", "Attack",
    "AugmentationOrigin", "AugmentationMetadata",
    "ArgumentationFramework",
    "compile_t2", "precompile_kb", "load_knowledge_store",
    "compile_t2b", "T2bResult",
    "SemanticCoverageAnalyzer", "CoverageResult",
    "AugmentationPipeline", "AugmentationResult",
    "T3aRetriever",
    "initialize_engine", "load_guide_dir", "CompileArtifacts",
    "compute_uncertainty_v4",
    "ContestationManager",
    "GroundingMode",
    "ReasoningLM",
]
