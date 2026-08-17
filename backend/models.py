"""Pydantic request/response models for the FastAPI backend."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


# ── Requests ────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    mode: str = "full"  # minimal | partial | full


class KBLoadRequest(BaseModel):
    kb_yaml_path: str
    guide_dir: str | None = None


# ── Responses ────────────────────────────────────────────────────────────────

class ProvenanceEntry(BaseModel):
    sources: list[str]
    pramana: str
    derivation_depth: int
    trust: float
    decay: float


class UncertaintyEntry(BaseModel):
    """The three components, reported separately.

    `total_confidence` is gone with the arithmetic behind it: it was
    belief × trust × decay, three quantities measuring different things
    multiplied under weights nobody derived. The components fail for
    different reasons and are shown as such.
    """
    conclusion: str
    epistemic: dict[str, Any]
    aleatoric: dict[str, Any]
    inference: dict[str, Any]


class CoverageResult(BaseModel):
    coverage_ratio: float
    matched_predicates: list[str]
    unmatched_predicates: list[str]
    match_details: dict[str, str]
    relevant_vyaptis: list[str]
    decision: str  # FULL | PARTIAL | DECLINE


class ProvenanceTag(BaseModel):
    pramana_type: str
    source_ids: list[str]
    trust_score: float
    decay_factor: float
    derivation_depth: int
    timestamp: str | None = None


class ArgumentNode(BaseModel):
    id: str
    conclusion: str
    rule_type: str
    label: str
    epistemic_status: str | None   # the conclusion's, shared by its arguments
    status: str                    # this argument's own place in the lattice
    tag: ProvenanceTag
    premises: list[str]
    vyapti_id: str | None = None


class AttackEdge(BaseModel):
    id: str
    attacker: str
    target: str
    attack_type: str
    hetvabhasa: str | None
    specificity_weight: float | None = None


class Violation(BaseModel):
    hetvabhasa: str | None
    type: str
    attacker: str
    target: str
    target_conclusion: str


class AugmentationInfo(BaseModel):
    augmented: bool
    reason: str
    framework_score: float
    new_vyapti_count: int
    warnings: list[str]


class ContestationInfo(BaseModel):
    mode: str
    open_questions: list[str]
    suggested_evidence: list[str]


class EngineResult(BaseModel):
    response: str
    sources: list[str]
    uncertainty: dict[str, UncertaintyEntry]
    provenance: dict[str, ProvenanceEntry]
    violations: list[Violation]
    grounding_confidence: float
    extension_size: int
    coverage: CoverageResult | None
    augmentation: AugmentationInfo | None
    contestation: ContestationInfo | None
    arguments: dict[str, ArgumentNode]
    attacks: list[AttackEdge]
    labels: dict[str, str]


class KBInfo(BaseModel):
    kb_name: str
    vyapti_count: int
    argument_count: int
    loaded: bool


class HealthResponse(BaseModel):
    status: str
    engine_loaded: bool
    kb_name: str | None
