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
from .predicate_contrariness import (
    entity_divergence,
    normalize_entity,
    predicate_entity,
    predicate_name,
    with_entity,
)
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
        scope_predicates: set[str] = set()

        for vid in vyapti_ids:
            v = knowledge_store.vyaptis.get(vid)
            if not v:
                continue
            all_predicates.update(v.antecedents)
            if v.consequent:
                all_predicates.add(v.consequent)
            # Printed per rule below as SCOPE:/EXCLUDES: and, until now, never
            # permitted — see the section built after the main list.
            scope_predicates.update(v.scope_conditions)
            scope_predicates.update(v.scope_exclusions)

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

        # A scope predicate that is also an antecedent or consequent is
        # already assertable above; listing it twice would say two different
        # things about one word.
        scope_only = sorted(scope_predicates - all_predicates)
        if scope_only:
            snippet += (
                "\nSCOPE PREDICATES — the conditions named above under "
                "SCOPE and EXCLUDES:\n"
            )
            for p in scope_only:
                snippet += f"  - {p}(Entity)\n"
            snippet += (
                "These say when a rule does or does not apply. Assert one "
                "ONLY if the query itself states that the condition holds — "
                "they are not findings to volunteer. Asserting one the query "
                "does not state will suppress a rule that should have "
                "applied.\n"
            )

        snippet += (
            "\nOUTPUT FORMAT:\n"
            "Return predicates as: predicate_name(entity)\n"
            "Entity names should be lowercase with underscores.\n"
            "Use ONLY predicate names from the lists above.\n"
            "Include negation as: not_predicate_name(entity)\n"
        )

        return snippet



# ─── Ensemble consensus ──────────────────────────────────────


CONSENSUS_THRESHOLD = 0.5


def _consensus(
    pred_sets: list[set[str]],
    threshold: float = CONSENSUS_THRESHOLD,
) -> tuple[set[str], set[str]]:
    """Predicates the ensemble agrees on, and the rest.

    This replaces `set.intersection(*pred_sets)`, which had two failures that
    compounded, both measured on one live query.

    *It compared full predicate strings, entity included.* The ensemble is N
    samplings of ONE query, so two spellings of the subject cannot be two
    subjects — but `superior_information(firm)` and
    `superior_information(the_firm)` are different strings, so identical
    findings failed to intersect. Votes are therefore counted per
    `(predicate name, normalised entity)`, which is exactly the question the
    ensemble is entitled to ask. Normalising here cannot merge two companies,
    because there is only ever one query being sampled.

    *It required unanimity.* Intersection over all N means a single divergent
    rollout at temperature 0.7 deletes a predicate every other member
    produced. Observed: four of five members emitted
    `superior_information(firm)`, the fifth wrote `the_firm`, the intersection
    was empty, confidence was 0.00, and the engine told the user their
    question needed clarification. It did not. A majority threshold is what
    the field named `consensus` always implied.

    The surviving spelling is the one the most members wrote, ties broken by
    sort order so the result does not depend on set iteration order — an
    ensemble that grounds differently on reruns cannot be compared against
    itself.
    """
    if not pred_sets:
        return set(), set()

    votes: dict[tuple[str, str | None], dict[str, int]] = {}
    for pred_set in pred_sets:
        for pred in pred_set:
            key = (predicate_name(pred), normalize_entity(predicate_entity(pred)))
            votes.setdefault(key, {})
            votes[key][pred] = votes[key].get(pred, 0) + 1

    needed = len(pred_sets) * threshold
    consensus: set[str] = set()
    disputed: set[str] = set()
    for spellings in votes.values():
        total = sum(spellings.values())
        # Most-voted spelling, ties broken lexicographically for determinism.
        winner = min(sorted(spellings), key=lambda p: (-spellings[p], p))
        if total > needed:
            consensus.add(winner)
        else:
            disputed.update(spellings)
    return consensus, disputed


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

        divergence = self._entity_divergence(candidate_preds)
        if divergence is not None:
            return divergence

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

        consensus_preds, disputed_preds = _consensus(all_pred_sets)

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

        divergence = self._entity_divergence(candidate_preds)
        if divergence is not None:
            return divergence

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

    def _entity_divergence(
        self, predicates: list[str]
    ) -> Optional[GroundingResult]:
        """Refuse to proceed when one query names a subject two ways.

        Fail loudly; normalise nothing. `predicate_entity` still returns what
        was written, and nothing here rewrites a binding — two spellings may
        genuinely be two companies, and silently merging them is the failure
        the entity work exists to prevent.

        What it prevents is the *other* silence. The entity decides rule
        chaining, rebuttal and scope, so `acme` and `Acme` partition the
        framework: V08 stops chaining, the engine reports no conclusion, and
        nothing says why. A missed inference reads as "no conclusion follows".
        Asking which was meant is the only answer that is neither a guess nor a
        silence.

        This returns a clarification rather than appending to `warnings`
        because grounding warnings are computed and read by nothing on the
        query path — a loud failure routed through a dead channel is not loud.
        The clarification path is the one the engine already renders.

        Distinct from the ensemble's normalisation above, and deliberately so:
        there, N samplings of one query cannot be about two subjects, so
        agreement is safe to infer. Here the predicates are the finished
        grounding of one query, and two spellings in it are a real ambiguity.
        """
        divergence = entity_divergence(predicates)
        if not divergence:
            return None

        detail = "; ".join(
            f"{canonical}: " + ", ".join(sorted(spellings))
            for canonical, spellings in sorted(divergence.items())
        )
        return GroundingResult(
            predicates=sorted(predicates),
            confidence=0.0,
            disputed=sorted(
                p for p in predicates
                if predicate_entity(p) in
                {s for spellings in divergence.values() for s in spellings}
            ),
            warnings=[
                f"ENTITY: one query named the same subject more than one way "
                f"({detail}). The binding decides rule chaining, rebuttal and "
                f"scope, so these are treated as different entities and no "
                f"rule will chain across them."
            ],
            clarification_needed=True,
        )

    def _check_scope(self, predicates: list[str]) -> list[str]:
        """Deterministic scope checking — no LLM.

        An exclusion applies the way the compiler says it applies
        (`t2_compiler_v4`): matched by predicate *name*, and bound to the
        entity it was observed of.

        The lowercase substring test this replaces answered a different
        question and got both halves wrong. `not_subsidized_entity(acme)`
        contains the exclusion as a substring, so a query stating the
        exclusion does **not** hold warned exactly as though it did — the
        warning inverted the query's meaning. And `subsidized_entity(globex)`
        warned without saying whose exclusion it was, which is the
        entity-blindness already fixed in the compiler for this same field.

        A bare exclusion fact binds to `None`, which is a binding like any
        other, so a base written entirely in bare names reads as before.
        """
        warnings: list[str] = []
        for vid, v in self.ks.vyaptis.items():
            for excl in v.scope_exclusions:
                excl_name = predicate_name(excl)
                excluded_entities = {
                    predicate_entity(p)
                    for p in predicates
                    if predicate_name(p) == excl_name
                }
                for entity in sorted(
                    excluded_entities, key=lambda e: (e is not None, e or "")
                ):
                    subject = with_entity(excl_name, entity)
                    warnings.append(
                        f"SCOPE: {vid} excludes '{subject}', "
                        f"which the query asserts"
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
