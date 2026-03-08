"""
Core data structures for the Ānvīkṣikī knowledge store.

These are populated by the T2 compiler from Stage 2+3 YAML output.
All models use Pydantic BaseModel for validation, JSON serialization,
and compatibility with DSPy 3.x typed output fields.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum, IntEnum
from typing import Optional

from pydantic import BaseModel, Field


# ─── Domain Taxonomy ──────────────────────────────────────────


class DomainType(str, Enum):
    """Eight domain types from the Ānvīkṣikī taxonomy."""

    FORMAL = "FORMAL"                    # Mathematics, formal logic
    MECHANISTIC = "MECHANISTIC"          # Physics, engineering
    EMPIRICAL = "EMPIRICAL"              # Social sciences, medicine
    CRAFT = "CRAFT"                      # Business strategy, design
    INTERPRETIVE = "INTERPRETIVE"        # Law, literary criticism
    DESIGN = "DESIGN"                    # Architecture, UX
    NORMATIVE = "NORMATIVE"              # Ethics, policy
    META_ANALYTICAL = "META_ANALYTICAL"  # Philosophy of science


class CausalStatus(str, Enum):
    STRUCTURAL = "structural"       # Follows from definitions/structure
    REGULATORY = "regulatory"       # Depends on institutional rules
    EMPIRICAL = "empirical"         # Observed regularity
    DEFINITIONAL = "definitional"   # True by definition


class EpistemicStatus(str, Enum):
    """Four epistemic values (plus BOTTOM in the Datalog engine)."""

    ESTABLISHED = "established"          # ✓ Strong evidence, consensus
    WORKING_HYPOTHESIS = "hypothesis"    # ~ Reasonable but contested
    GENUINELY_OPEN = "open"              # ? Unknown to the field
    ACTIVELY_CONTESTED = "contested"     # ⚡ Live scholarly debate


class DecayRisk(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class AugmentationOrigin(str, Enum):
    """How a vyapti was produced."""

    CURATED = "curated"                    # Hand-authored in base KB
    GUIDE_EXTRACTED = "guide_extracted"     # T2b: extracted from guide prose
    LLM_PARAMETRIC = "llm_parametric"      # T3b v1: LLM parametric knowledge
    WEB_SOURCED = "web_sourced"            # T3b v2: web search evidence
    HITL_PROMOTED = "hitl_promoted"        # T3b v3: promoted from shadow KB


# ─── Component Models ────────────────────────────────────────


class AugmentationMetadata(BaseModel):
    """Provenance metadata for non-curated vyaptis."""

    origin: AugmentationOrigin
    generated_at: Optional[datetime] = None
    generating_query: str = ""
    framework_vyaptis_used: list[str] = Field(default_factory=list)
    source_chapter_ids: list[str] = Field(default_factory=list)
    parent_vyapti_id: Optional[str] = None
    generation_model: str = ""


class Confidence(BaseModel):
    """Confidence ratings for a vyāpti."""

    existence: float = Field(ge=0.0, le=1.0, description="Confidence the rule exists at all")
    formulation: float = Field(ge=0.0, le=1.0, description="Confidence the formulation is precise")
    evidence: str = Field(description="Evidence type: experimental, observational, theoretical, expert_consensus")


class Vyapti(BaseModel):
    """
    A domain rule — the core computational primitive.

    Maps to a Datalog rule:
        consequent(Entity) :- antecedent1(Entity), antecedent2(Entity), ...
                              not scope_exclusion1(Entity), ...
    """

    id: str
    name: str
    statement: str
    causal_status: CausalStatus
    scope_conditions: list[str] = Field(default_factory=list)
    scope_exclusions: list[str] = Field(default_factory=list)
    confidence: Confidence
    epistemic_status: EpistemicStatus
    decay_risk: DecayRisk = DecayRisk.LOW
    decay_condition: Optional[str] = None
    last_verified: Optional[datetime] = None
    sources: list[str] = Field(default_factory=list)

    # Datalog-compilable fields
    antecedents: list[str] = Field(default_factory=list, description="Predicate names required")
    consequent: str = Field(default="", description="Predicate name produced")

    # Origin tracking (None = curated base KB, backward-compatible)
    augmentation_metadata: Optional[AugmentationMetadata] = None


class Hetvabhasa(BaseModel):
    """A reasoning fallacy — an integrity constraint."""

    id: str
    name: str
    description: str
    detection_signature: str
    correction_pattern: str
    common_contexts: list[str] = Field(default_factory=list)


class ThresholdConcept(BaseModel):
    """A concept that permanently reorganizes understanding (Meyer & Land)."""

    name: str
    reorganizes: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    troublesome_aspects: list[str] = Field(default_factory=list)


class ChapterFingerprint(BaseModel):
    """Machine-readable metadata for a guide chapter."""

    chapter_id: str
    title: str
    key_terms: list[str] = Field(default_factory=list)
    anchoring_concepts: list[str] = Field(default_factory=list)
    vyaptis_introduced: list[str] = Field(default_factory=list)
    hetvabhasas_active: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    forward_dependencies: list[str] = Field(default_factory=list)
    epistemic_statuses: dict[str, EpistemicStatus] = Field(default_factory=dict)
    decay_markers: list[dict] = Field(default_factory=list)
    difficulty_tier: str = "intermediate"


# ─── Top-Level Knowledge Store ────────────────────────────────


class KnowledgeStore(BaseModel):
    """
    The complete compiled knowledge base for a domain.

    This is the central data structure. Every other module reads from it.
    Populated by the T2 compiler from Stage 2+3 YAML output.
    """

    domain_type: DomainType
    pramanas: list[str] = Field(default_factory=list)
    vyaptis: dict[str, Vyapti] = Field(default_factory=dict)
    hetvabhasas: dict[str, Hetvabhasa] = Field(default_factory=dict)
    threshold_concepts: list[ThresholdConcept] = Field(default_factory=list)
    dependency_graph: dict[str, list[str]] = Field(default_factory=dict)
    chapter_fingerprints: dict[str, ChapterFingerprint] = Field(default_factory=dict)
    reference_bank: dict[str, dict] = Field(default_factory=dict)

    # Domain-aware contrariness pairs (fixes audit III-02)
    # Each pair is [pred_a, pred_b] meaning they are domain-contradictory
    # e.g. ["value_creation", "value_destruction"]
    contrariness_pairs: list[list[str]] = Field(
        default_factory=list,
        description="Domain-specific contradictory predicate pairs beyond syntactic not_ negation",
    )

    # T2b compile-time extensions (populated by compile_t2b)
    fine_grained_vyapti_ids: list[str] = Field(
        default_factory=list,
        description="IDs of vyaptis extracted from guide prose (not base KB)",
    )
    synonym_table: dict[str, str] = Field(
        default_factory=dict,
        description="Predicate alias → canonical name, for semantic coverage matching",
    )
