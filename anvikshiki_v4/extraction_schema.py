"""
Pydantic models for the Automated Predicate Extraction Pipeline.

Defines data contracts between all six pipeline stages (A-F).
Follows the pattern of schema.py — Pydantic BaseModel with Field descriptors.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

_SHA256_RE = re.compile(r"[0-9a-fA-F]{64}")


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
    """Where a claim was found — in the guide corpus, or in a fetched document.

    Two locator families, because the two kinds of source are addressed
    differently and neither can address the other. A guide chapter is addressed
    by position inside a corpus we hold; a retrieved document is addressed by
    URL plus a content hash, because the thing at that URL can change under us
    and a locator that cannot notice that is not a locator.

    `quote` is the span itself, and it is what makes the record checkable rather
    than merely descriptive: given a locator and a quote, a later pass can go
    back to the source and confirm the words are there. That check is not in
    this model — it is the validation gate — but the fields it needs are.

    A note on what this model does *not* yet guarantee. Nothing in the pipeline
    currently populates `quote`: the extraction signature has no output field
    for it, the construction site does not set it, and the one real run on disk
    has 24 candidates with an empty span in all 24. So the fields below are the
    surface a verification gate needs, and the gate has nothing to verify until
    extraction is asked to quote. Adding fields does not add evidence.
    """

    model_config = ConfigDict(populate_by_name=True)

    # ── Guide-corpus locator ──
    chapter_id: str = Field(
        default="",
        description=(
            "Chapter in the guide corpus, e.g. 'ch02'. Defaulted rather than "
            "required so a document-sourced claim does not have to invent one; "
            "the model validator below requires *a* locator instead."
        ),
    )
    section_header: str = ""
    paragraph_index: int = 0

    # ── Fetched-document locator ──
    doc_url: str = Field(
        default="",
        description="Absolute URL of the document the claim was read from.",
    )
    retrieved_at: Optional[datetime] = Field(
        default=None,
        description=(
            "When the document was fetched. Absent means nobody recorded it, "
            "which is different from the document being fresh — decay reads "
            "this, so a missing value must not read as 'just now'."
        ),
    )
    content_sha256: str = Field(
        default="",
        description=(
            "SHA-256 of the exact bytes the quote was taken from. Without it a "
            "URL locates a moving target: the page can change and the quote "
            "will simply stop being found, with nothing to say whether it was "
            "fabricated or the source was edited."
        ),
    )

    quote: str = Field(
        default="",
        validation_alias=AliasChoices("quote", "sentence"),
        description=(
            "The claim's span, verbatim from the source. Named `quote` rather "
            "than `sentence` because it is a citation to be checked, not "
            "incidental context, and because it need not be one sentence. "
            "`sentence` is still accepted when parsing so traces written "
            "before the rename keep loading."
        ),
    )
    quote_found_in_source: Optional[bool] = Field(
        default=None,
        description=(
            "Whether the quote was found verbatim in the text it was read "
            "from. Three states, and the third is the point: None means "
            "nobody checked — either no quote was given or no source was in "
            "hand — while False means someone looked and the words were not "
            "there. Collapsing None into False would report every unchecked "
            "record as a fabrication; collapsing it into True would let an "
            "unchecked quote stand as a verified citation, which is the "
            "direction that flatters us."
        ),
    )
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)

    @field_validator("content_sha256")
    @classmethod
    def _sha256_is_a_hash_or_absent(cls, value: str) -> str:
        """A malformed digest must fail loudly rather than sit there unusable.

        The failure this prevents is a placeholder — "TODO", "unknown", a
        truncated paste — occupying the field that later decides whether a
        quote can be re-checked. Empty is a legitimate value meaning nobody
        hashed anything; 63 hex characters is not.
        """
        if value and not _SHA256_RE.fullmatch(value):
            raise ValueError(
                f"content_sha256 must be 64 hex characters or empty, "
                f"got {len(value)} character(s): {value[:16]!r}"
            )
        return value.lower()

    @field_validator("doc_url")
    @classmethod
    def _doc_url_is_absolute_or_absent(cls, value: str) -> str:
        """A relative URL cannot be re-fetched from anywhere but here."""
        if value and "://" not in value:
            raise ValueError(
                f"doc_url must be absolute (scheme://host/...), got {value!r}"
            )
        return value

    @model_validator(mode="after")
    def _at_least_one_locator(self) -> Provenance:
        """A provenance record that locates nothing is not provenance.

        `chapter_id` used to be required, which enforced this for the guide
        path by accident. Defaulting it so a fetched document need not fake a
        chapter opens the hole, so the requirement is stated instead of relying
        on one field's arity — and it is stated as "at least one", because
        which family applies depends on where the claim came from.
        """
        if not self.chapter_id and not self.doc_url:
            raise ValueError(
                "Provenance needs a locator: set chapter_id for a guide claim "
                "or doc_url for a fetched document"
            )
        return self


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
    failed_sections: int = Field(
        default=0,
        description=(
            "Sections where extraction raised. Counted apart from "
            "zero_predicate_sections: a section the model never answered for "
            "and a section that genuinely holds no predicate are different "
            "facts, and only the second is a statement about the prose. "
            "Folding them together makes an outage look like a thin chapter."
        ),
    )
    failures: list[str] = Field(
        default_factory=list,
        description="Why each failed section failed, for the run report.",
    )
    truncated_sections: int = Field(
        default=0,
        description=(
            "Sections where the model's answer was cut off by the token "
            "budget. Counted apart from zero_predicate_sections for the same "
            "reason failed_sections is: an answer we stopped the model from "
            "finishing yields no parseable predicates either, so a small "
            "budget was being recorded as 'this section of the guide contains "
            "no predicates' — a claim about our configuration, reported as a "
            "claim about the prose. Unlike an exception, truncation does not "
            "raise: the response arrives, it is simply incomplete."
        ),
    )
    truncations: list[str] = Field(
        default_factory=list,
        description="Which sections were truncated, for the run report.",
    )
    quotes_checked: bool = Field(
        default=False,
        description=(
            "Whether spans were checked against their sections at all. "
            "Defaults to False, unlike `truncation_checked`, because the "
            "conservative direction is the other way round here: a run "
            "predating span capture checked nothing, and its "
            "`quoteless_candidates` of 0 would otherwise read as '0 "
            "candidates lacked a quote' when in truth every one of them did. "
            "The counters below mean nothing unless this is True."
        ),
    )
    quoteless_candidates: int = Field(
        default=0,
        description=(
            "Candidates the model returned no quote for. Counted apart from "
            "the ones whose quote could not be found, because 'declined to "
            "cite' and 'cited something that is not there' are different "
            "facts about the model and only the second is evidence of "
            "fabrication."
        ),
    )
    unverified_quote_candidates: int = Field(
        default=0,
        description=(
            "Candidates whose quote was checked against the section and not "
            "found verbatim. The predicate is kept, not dropped: dropping "
            "here would remove the very thing the rate is meant to measure, "
            "and the validation gate is where a drop belongs."
        ),
    )
    quote_failures: list[str] = Field(
        default_factory=list,
        description=(
            "Which candidates failed and how — 'absent' versus 'punctuation' "
            "versus 'too short to discriminate'. A bare count cannot separate "
            "a model that invents sentences from one that types curly "
            "apostrophes, and those call for opposite responses."
        ),
    )
    truncation_checked: bool = Field(
        default=True,
        description=(
            "Whether truncation could be detected at all. It is read from the "
            "completion's finish_reason, which reaches us through the LM's "
            "call history — and that history can be switched off "
            "(`dspy.settings.disable_history`, `max_history_size=0`). When it "
            "is off, this run cannot rule truncation out, which is a third "
            "state and not the same as having found none. False makes the "
            "zero-section figure uninterpretable rather than merely low."
        ),
    )


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
    provenance_attached: bool = Field(
        default=False,
        description=(
            "Whether the candidate-to-rule step tried to carry provenance "
            "across. Needed because an empty `provenance` list meant two "
            "different things and nothing could tell them apart: no "
            "contributing candidate had a record, or the construction site "
            "never passed one. Every rule extraction has ever produced was "
            "the second, and a citation tier computed over those lists would "
            "have reported the same value after every source gained a DOI — "
            "measuring our own plumbing and calling it the state of the "
            "corpus.\n\n"
            "False is the conservative default here because it is the "
            "conservative reading of data written *before* this flag existed: "
            "those rules had nothing attached, and a True default would claim "
            "retroactively that they had been checked. Construction sites set "
            "it True when they have looked, whether or not they found "
            "anything.\n\n"
            "A rule with no provenance stays constructible on purpose. The "
            "sub-rule path can legitimately find none — its consequent may be "
            "an existing knowledge-base predicate that no candidate in this "
            "run introduced — so refusing to build it would discard a real "
            "rule to enforce a record-keeping rule. The flag makes that case "
            "visible instead of forbidding it."
        ),
    )
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
    """Result of DAG and Datalog validation.

    `ran` exists because an empty `cycle_errors` list meant two different
    things and nothing could tell them apart: validation ran and found no
    cycles, or validation never ran. `dag_validity` read that empty list as a
    clean pass and scored a default object 1.0 — an object whose own
    `is_valid` said False.

    Anything that performs validation sets `ran=True`. Anything that merely
    constructs a result leaves it False and earns no credit.
    """

    ran: bool = Field(
        default=False,
        description="Whether validation was actually performed.",
    )
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
