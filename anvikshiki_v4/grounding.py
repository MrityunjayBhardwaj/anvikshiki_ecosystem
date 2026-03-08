"""
Five-layer grounding defense for the Ānvīkṣikī Engine.

Translates natural language queries into verified Datalog predicates.

Layers:
  1. Ontology-constrained prompt (always on, zero cost)
  2. Grammar-constrained decoding (at serving level — transparent to DSPy)
  3. Ensemble consensus N=5 (always on, 5x grounding cost)
  4. Round-trip verification (conditional: ensemble agreement < 0.9)
  5. Solver-feedback refinement (conditional: Datalog validation errors)

DSPy 3.x: Uses dspy.ChainOfThought with typed signatures.
           dspy.Assert/Suggest are deprecated — constraints are structural.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

import dspy
from pydantic import BaseModel, Field


class GroundingMode(str, Enum):
    """Configurable grounding rigor."""
    MINIMAL = "minimal"   # 1 call: Layer 1 + single GroundQuery (temp=0)
    PARTIAL = "partial"   # N=3 ensemble + round-trip (no solver)
    FULL = "full"         # N=5 ensemble + round-trip + solver feedback

from .datalog_engine import DatalogEngine
from .schema import KnowledgeStore


# ─── Result Model ────────────────────────────────────────────


class GroundingResult(BaseModel):
    """Output of the grounding pipeline."""

    predicates: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    disputed: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    refinement_rounds: int = 0
    clarification_needed: bool = False


# ─── DSPy 3.x Signatures ────────────────────────────────────


class GroundQuery(dspy.Signature):
    """Translate a natural language query into structured predicates.
    Use ONLY predicates from the provided ontology snippet.
    Think step by step about which entities and relationships the query mentions."""

    query: str = dspy.InputField(desc="User's natural language question")
    ontology_snippet: str = dspy.InputField(
        desc="Valid predicates and rules — use ONLY these predicate names"
    )
    domain_type: str = dspy.InputField(desc="Domain classification")

    reasoning: str = dspy.OutputField(
        desc="Step-by-step: which predicates match the entities and relationships?"
    )
    predicates: list[str] = dspy.OutputField(
        desc="Structured predicates, e.g. ['concentrated_ownership(acme)', 'private_firm(acme)']"
    )
    relevant_vyaptis: list[str] = dspy.OutputField(
        desc="IDs of vyāptis relevant to this query, e.g. ['V01', 'V02']"
    )


class VerbalizePredicates(dspy.Signature):
    """Translate structured predicates back to natural language.
    This is used for round-trip verification of grounding accuracy."""

    predicates: list[str] = dspy.InputField(desc="Structured predicates to verbalize")
    ontology_snippet: str = dspy.InputField(desc="Predicate descriptions for context")

    verbalization: str = dspy.OutputField(
        desc="Natural language description of what these predicates assert"
    )


class CheckFaithfulness(dspy.Signature):
    """Check whether a round-trip translation preserves the original meaning.
    Compare the original query with the verbalized predicates."""

    original_query: str = dspy.InputField()
    verbalized_predicates: str = dspy.InputField()

    faithful: bool = dspy.OutputField(
        desc="Do the verbalized predicates capture the same meaning as the original query?"
    )
    discrepancies: list[str] = dspy.OutputField(
        desc="Specific meaning differences, if any"
    )


# ─── Layer 1: Ontology Snippet Builder ───────────────────────


class OntologySnippetBuilder:
    """
    LAYER 1: Build constrained vocabulary from the knowledge store.

    The LLM sees ONLY valid predicates and their descriptions.
    Cost: zero extra LLM calls. Always on.
    """

    def build(
        self,
        knowledge_store: KnowledgeStore,
        relevant_vyaptis: Optional[list[str]] = None,
    ) -> str:
        snippet = "VALID PREDICATES — use ONLY these:\n\n"
        vyapti_ids = relevant_vyaptis or list(knowledge_store.vyaptis.keys())
        all_predicates: set[str] = set()

        for vid in vyapti_ids:
            v = knowledge_store.vyaptis.get(vid)
            if not v:
                continue
            all_predicates.update(v.antecedents)
            if v.consequent:
                all_predicates.add(v.consequent)

            snippet += f"RULE {vid}: {v.name}\n"
            snippet += f"  IF: {', '.join(v.antecedents)}\n"
            snippet += f"  THEN: {v.consequent}\n"
            snippet += f"  SCOPE: {', '.join(v.scope_conditions)}\n"
            if v.scope_exclusions:
                snippet += f"  EXCLUDES: {', '.join(v.scope_exclusions)}\n"
            snippet += "\n"

        snippet += "\nALL VALID PREDICATE NAMES:\n"
        for p in sorted(all_predicates):
            snippet += f"  - {p}(Entity)\n"

        snippet += (
            "\nOUTPUT FORMAT:\n"
            "Return predicates as: predicate_name(entity)\n"
            "Entity names should be lowercase with underscores.\n"
            "Use ONLY predicate names from the list above.\n"
            "Include negation as: not_predicate_name(entity)\n"
        )

        return snippet


# ─── Grounding Pipeline ──────────────────────────────────────


class GroundingPipeline(dspy.Module):
    """
    Five-layer grounding defense with configurable rigor.

    Modes:
      MINIMAL — 1 LLM call (Layer 1 + single GroundQuery, temperature=0)
      PARTIAL — N=3 ensemble (Layers 1-4, no solver feedback)
      FULL    — N=5 ensemble + round-trip + solver feedback (Layers 1-5)

    Mode can be set at init time or overridden per forward() call.
    """

    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        datalog_engine: Optional[DatalogEngine] = None,
        mode: GroundingMode = GroundingMode.FULL,
    ):
        super().__init__()
        self.ks = knowledge_store
        self.engine = datalog_engine
        self.mode = mode

        # Layer 1
        self.snippet_builder = OntologySnippetBuilder()

        # Layer 3: Ensemble grounding
        self.grounder = dspy.ChainOfThought(GroundQuery)

        # Layer 4: Round-trip verification
        self.verbalizer = dspy.ChainOfThought(VerbalizePredicates)
        self.checker = dspy.ChainOfThought(CheckFaithfulness)

    def forward(
        self,
        query: str,
        mode: Optional[GroundingMode] = None,
    ) -> GroundingResult:
        active_mode = mode or self.mode

        # ── LAYER 1: Build ontology-constrained prompt (always on) ──
        snippet = self.snippet_builder.build(self.ks)

        if active_mode == GroundingMode.MINIMAL:
            return self._forward_minimal(query, snippet)
        elif active_mode == GroundingMode.PARTIAL:
            return self._forward_ensemble(query, snippet, n=3, use_solver=False)
        else:
            return self._forward_ensemble(query, snippet, n=5, use_solver=True)

    # ── MINIMAL: 1 call, temperature=0 ──

    def _forward_minimal(self, query: str, snippet: str) -> GroundingResult:
        g = self.grounder(
            query=query,
            ontology_snippet=snippet,
            domain_type=self.ks.domain_type.value,
            config={"temperature": 0},
        )
        candidate_preds = g.predicates
        candidate_vyaptis = g.relevant_vyaptis

        warnings: list[str] = []
        warnings.extend(self._check_scope(candidate_preds))
        warnings.extend(self._check_decay(candidate_vyaptis))

        return GroundingResult(
            predicates=candidate_preds,
            confidence=1.0,
            disputed=[],
            warnings=warnings,
            refinement_rounds=0,
            clarification_needed=False,
        )

    # ── PARTIAL / FULL: N-ensemble + optional round-trip + optional solver ──

    def _forward_ensemble(
        self,
        query: str,
        snippet: str,
        n: int,
        use_solver: bool,
    ) -> GroundingResult:
        # Layer 2 (grammar constraint) applied at serving level — transparent.
        groundings = []
        for i in range(n):
            g = self.grounder(
                query=query,
                ontology_snippet=snippet,
                domain_type=self.ks.domain_type.value,
                config={"rollout_id": i, "temperature": 0.7},
            )
            groundings.append(g)

        # Compute consensus
        all_pred_sets = [set(g.predicates) for g in groundings]
        all_vyapti_sets = [set(g.relevant_vyaptis) for g in groundings]

        consensus_preds = set.intersection(*all_pred_sets) if all_pred_sets else set()
        all_preds = set.union(*all_pred_sets) if all_pred_sets else set()
        disputed_preds = all_preds - consensus_preds

        consensus_vyaptis = set.intersection(*all_vyapti_sets) if all_vyapti_sets else set()

        total = len(consensus_preds) + len(disputed_preds)
        confidence = len(consensus_preds) / max(total, 1)

        # Low confidence → request clarification
        if confidence < 0.4:
            return GroundingResult(
                predicates=sorted(consensus_preds),
                confidence=confidence,
                disputed=sorted(disputed_preds),
                warnings=["Grounding confidence too low — requesting clarification"],
                clarification_needed=True,
            )

        candidate_preds = sorted(consensus_preds | disputed_preds)
        candidate_vyaptis = sorted(consensus_vyaptis)

        # ── LAYER 4: Round-trip verification ──
        # (only if ensemble agreement < 0.9)
        if confidence < 0.9 and candidate_preds:
            verb = self.verbalizer(
                predicates=candidate_preds,
                ontology_snippet=snippet,
            )
            faith = self.checker(
                original_query=query,
                verbalized_predicates=verb.verbalization,
            )
            if not faith.faithful:
                candidate_preds = sorted(consensus_preds)
                confidence = 1.0 if consensus_preds else 0.0

        # ── LAYER 5: Solver-feedback refinement (FULL only) ──
        refinement_rounds = 0
        if use_solver and self.engine is not None:
            for _ in range(3):
                errors = self.engine.validate_predicates(candidate_preds)
                if not errors:
                    break

                error_ctx = (
                    f"The following predicates caused errors: {errors}. "
                    f"Please fix them using ONLY predicates from the ontology."
                )
                refined = self.grounder(
                    query=query + "\n\n" + error_ctx,
                    ontology_snippet=snippet,
                    domain_type=self.ks.domain_type.value,
                )
                candidate_preds = refined.predicates
                refinement_rounds += 1

        # Deterministic scope/decay checks (no LLM)
        warnings: list[str] = []
        warnings.extend(self._check_scope(candidate_preds))
        warnings.extend(self._check_decay(candidate_vyaptis))

        return GroundingResult(
            predicates=candidate_preds,
            confidence=confidence,
            disputed=sorted(disputed_preds),
            warnings=warnings,
            refinement_rounds=refinement_rounds,
            clarification_needed=False,
        )

    def _check_scope(self, predicates: list[str]) -> list[str]:
        """Deterministic scope checking — no LLM."""
        warnings: list[str] = []
        for vid, v in self.ks.vyaptis.items():
            for excl in v.scope_exclusions:
                if any(excl.lower() in p.lower() for p in predicates):
                    warnings.append(
                        f"SCOPE: {vid} excludes '{excl}' but query matches"
                    )
        return warnings

    def _check_decay(self, vyapti_ids: list[str]) -> list[str]:
        """Deterministic decay checking — no LLM."""
        warnings: list[str] = []
        now = datetime.now()
        for vid in vyapti_ids:
            v = self.ks.vyaptis.get(vid)
            if v and v.decay_risk.value in ("high", "critical"):
                if v.last_verified:
                    age = (now - v.last_verified).days
                    if age > 180:
                        warnings.append(
                            f"DECAY: {vid} last verified {age} days ago "
                            f"({v.decay_condition})"
                        )
                else:
                    warnings.append(
                        f"DECAY: {vid} NEVER verified ({v.decay_condition})"
                    )
        return warnings
