"""
Pydantic models for the Automated Predicate Extraction Pipeline.

Defines data contracts between all six pipeline stages (A-F).
Follows the pattern of schema.py — Pydantic BaseModel with Field descriptors.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ─── Stage A: Candidate Extraction ─────────────────────────────


class ClaimType(str, Enum):
    """Type of domain claim extracted from guide text."""

    CAUSAL = "causal"              # "X causes Y"
    CONDITIONAL = "conditional"    # "If X then Y"
    METRIC = "metric"              # "X is measured by Y"
    DEFINITIONAL = "definitional"  # "X means Y"
    SCOPE = "scope"                # "X holds only when Y"
    NEGATION = "negation"          # "X prevents Y"


class Provenance(BaseModel):
    """Where in the guide text a claim was found."""

    chapter_id: str
    section_header: str = ""
    paragraph_index: int = 0
    sentence: str = Field(
        default="", description="The exact sentence containing the claim"
    )
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class CandidatePredicate(BaseModel):
    """A raw predicate extracted from guide text."""

    name: str = Field(description="snake_case predicate name")
    description: str = Field(description="One-sentence natural language description")
    claim_type: ClaimType
    provenance: Provenance
    related_existing_vyapti: Optional[str] = Field(
        default=None,
        description="Existing vyapti ID this relates to, e.g. 'V01'",
    )


class StageAOutput(BaseModel):
    """Output of Stage A: candidate extraction."""

    candidates: list[CandidatePredicate] = Field(default_factory=list)
    chapter_id: str = ""
    section_count: int = 0
    zero_predicate_sections: int = 0


# ─── Stage B: Hierarchical Decomposition ───────────────────────


class PredicateRelation(str, Enum):
    """How a child predicate relates to its parent."""

    SUBSUMES = "subsumes"        # Parent generalizes child
    COMPOSES = "composes"        # Parent = AND of children
    ALTERNATIVE = "alternative"  # Children are OR paths
    NEGATION = "negation"        # Child negates parent


class PredicateNode(BaseModel):
    """A node in the hierarchical predicate tree."""

    predicate: str = Field(description="snake_case predicate name")
    description: str = ""
    parent: Optional[str] = None
    relation_to_parent: Optional[PredicateRelation] = None
    children: list[str] = Field(default_factory=list)
    depth: int = 0  # 0=chapter-level (existing), 1=section, 2+=finer
    source_vyapti: Optional[str] = None


class StageBOutput(BaseModel):
    """Output of Stage B: hierarchical decomposition."""

    nodes: dict[str, PredicateNode] = Field(default_factory=dict)
    decomposition_count: int = 0


# ─── Stage C: Canonicalization ─────────────────────────────────


class SynonymCluster(BaseModel):
    """A cluster of synonymous predicate names."""

    canonical: str = Field(description="The chosen canonical name")
    alternatives: list[str] = Field(default_factory=list)
    merge_reason: str = ""


class StageCOutput(BaseModel):
    """Output of Stage C: clean predicate vocabulary."""

    vocabulary: list[str] = Field(default_factory=list)
    synonym_clusters: list[SynonymCluster] = Field(default_factory=list)
    removed_count: int = 0


# ─── Stage D: Vyapti Construction ──────────────────────────────


class ProposedVyapti(BaseModel):
    """A new vyapti constructed from extracted predicates."""

    id: str = ""
    name: str = ""
    statement: str = ""
    causal_status: str = "empirical"
    antecedents: list[str] = Field(default_factory=list)
    consequent: str = ""
    scope_conditions: list[str] = Field(default_factory=list)
    scope_exclusions: list[str] = Field(default_factory=list)
    confidence_existence: float = Field(ge=0.0, le=1.0, default=0.7)
    confidence_formulation: float = Field(ge=0.0, le=1.0, default=0.6)
    evidence_type: str = "observational"
    epistemic_status: str = "hypothesis"  # Conservative default
    decay_risk: str = "moderate"
    sources: list[str] = Field(default_factory=list)
    provenance: list[Provenance] = Field(default_factory=list)
    parent_vyapti: Optional[str] = None


class StageDOutput(BaseModel):
    """Output of Stage D: new vyaptis."""

    new_vyaptis: list[ProposedVyapti] = Field(default_factory=list)
    refinement_vyaptis: list[ProposedVyapti] = Field(
        default_factory=list,
        description="Vyaptis that decompose existing ones into sub-rules",
    )


# ─── Stage E: Validation ──────────────────────────────────────


class ValidationResult(BaseModel):
    """Result of DAG and Datalog validation."""

    is_valid: bool = False
    cycle_errors: list[str] = Field(default_factory=list)
    orphan_predicates: list[str] = Field(default_factory=list)
    datalog_errors: list[str] = Field(default_factory=list)
    coverage_ratio: float = 0.0


# ─── Stage F: HITL Review ─────────────────────────────────────


class ReviewDecision(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    MODIFY = "modify"


class ReviewItem(BaseModel):
    """A single item for human review."""

    vyapti: ProposedVyapti
    validation: ValidationResult
    decision: Optional[ReviewDecision] = None
    reviewer_notes: str = ""


# ─── Pipeline Config ──────────────────────────────────────────


class ExtractionConfig(BaseModel):
    """Configuration for the extraction pipeline."""

    ensemble_n: int = Field(default=3, description="Ensemble size for extraction")
    decomposition_max_depth: int = Field(
        default=2, description="Max depth for hierarchical decomposition"
    )
    similarity_threshold: float = Field(
        default=0.85, description="Cosine threshold for deduplication"
    )
    min_confidence: float = Field(
        default=0.3, description="Minimum confidence to keep a candidate"
    )
    max_new_vyaptis_per_chapter: int = Field(
        default=15, description="Cap on new vyaptis per chapter"
    )
    model_tier: str = Field(
        default="large",
        description="'large' for API models, 'small' for 3-7B local",
    )
