"""
Semantic Coverage Analyzer for the Ānvīkṣikī Engine.

Three-layer predicate matching against base + fine-grained KB:
  1. Exact match against known vocabulary
  2. Synonym lookup (from T2b synonym table)
  3. Jaccard token overlap (fallback)

Produces a routing decision: FULL / PARTIAL / DECLINE.
Zero LLM calls — fully deterministic.

── Policy on negation, decided rather than inherited ─────────

A query asserting `not_X` against a knowledge base that knows `X` **counts as
covered**, and its match is labelled `negated_*` rather than `exact`.

*Why it matters as a policy.* This module asks whether the knowledge base has
reasoning machinery for a concept, not whether the query makes the same claim.
A base that reasons about value creation does have something to say about its
absence — and `not_X` against a rule about `X` is exactly what raises a
rebutting attack, which is the engine's most informative behaviour. Declining
would refuse the queries it handles best.

*Why the label matters anyway.* Reporting it as `exact` was wrong regardless of
the policy. The strings differ, and they differ on the token that reverses the
meaning, so the trace told a reader the query was found verbatim in the
vocabulary when it was not.

*The apparent contradiction with the token layer, stated so it is not mistaken
for an oversight.* Layer 3 refuses `positive_unit_economics` against
`negative_unit_economics` outright, while layer 1 accepts `not_value_creation`
against `value_creation`. Both are intended, and they are different cases: the
first is an accidental token collision between two unrelated predicates that
happen to share three tokens out of four, where a match would route the query
to a rule asserting the opposite of what was asked and nothing would announce
it. The second is a deliberate polarity inversion of a predicate the base
knows, which the argumentation layer is built to reason about — and which the
match type now announces.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .predicate_contrariness import (
    affirmative,
    get_contrary,
    match_veto,
    negation_differs,
    normalize_negation,
    predicate_name,
)
from .schema import KnowledgeStore


# ─── Thresholds (aligned with query_refinement.py) ───────────

FULL_THRESHOLD = 0.6     # >= this → full coverage path
PARTIAL_THRESHOLD = 0.2  # >= this → partial coverage path
TOKEN_OVERLAP_MIN = 0.4  # minimum Jaccard score for token match


# ─── Result Model ────────────────────────────────────────────


class CoverageResult(BaseModel):
    """Output of semantic coverage analysis."""

    coverage_ratio: float = 0.0
    matched_predicates: list[str] = Field(default_factory=list)
    unmatched_predicates: list[str] = Field(default_factory=list)
    match_details: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "predicate -> match_type: exact/synonym/token, each also in a "
            "negated_* form meaning the vocabulary holds this predicate and "
            "the query asserts its negation. See the module docstring for why "
            "that still counts as covered."
        ),
    )
    relevant_vyaptis: list[str] = Field(default_factory=list)
    inert_predicates: list[str] = Field(
        default_factory=list,
        description=(
            "Matched predicates the base cannot do anything with as stated. "
            "A predicate is inert when no rule takes it as an antecedent, no "
            "rule concludes it, and no rule concludes its contrary — so it "
            "can neither fire a rule nor rebut one. Matching is about "
            "vocabulary and this is about machinery; the two are different "
            "questions and a predicate can pass the first and fail the "
            "second. Kept out of `unmatched_predicates` on purpose: the "
            "vocabulary really does hold it, and saying otherwise would lose "
            "the routing to `relevant_vyaptis` that retrieval depends on."
        ),
    )
    decision: str = "DECLINE"  # FULL / PARTIAL / DECLINE


# ─── Analyzer ────────────────────────────────────────────────


class SemanticCoverageAnalyzer:
    """
    Three-layer predicate matching against base + fine-grained KB.

    Layer 1 — Exact: predicate name exists in KB vocabulary.
    Layer 2 — Synonym: predicate maps to a canonical name via synonym table.
    Layer 3 — Token overlap: Jaccard similarity on underscore-split tokens.
    """

    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        synonym_table: dict[str, str] | None = None,
    ):
        self.ks = knowledge_store
        self._synonym_table = synonym_table or knowledge_store.synonym_table
        self._vocab = self._build_vocabulary()
        self._pred_to_vyaptis = self._build_predicate_index()
        self._antecedents = {
            a for v in knowledge_store.vyaptis.values() for a in v.antecedents
        }
        self._consequents = {
            v.consequent for v in knowledge_store.vyaptis.values() if v.consequent
        }

    def _build_vocabulary(self) -> set[str]:
        """All predicates from antecedents + consequents across all vyaptis."""
        vocab: set[str] = set()
        for v in self.ks.vyaptis.values():
            vocab.update(v.antecedents)
            if v.consequent:
                vocab.add(v.consequent)
        return vocab

    def _build_predicate_index(self) -> dict[str, list[str]]:
        """Map each predicate -> list of vyapti IDs that use it."""
        index: dict[str, list[str]] = {}
        for vid, v in self.ks.vyaptis.items():
            for pred in list(v.antecedents) + [v.consequent]:
                if pred:
                    index.setdefault(pred, []).append(vid)
        return index

    def _is_inert(self, pred: str) -> bool:
        """Can any rule in this base do anything with `pred` as stated?

        Three ways it can, and inert means none of them holds:

          * some rule takes it as an antecedent  → it can help fire a rule
          * some rule concludes it               → it can be derived, or agree
          * some rule concludes its contrary     → it can raise a rebuttal

        The third is why negation is not the test. `not_value_creation`
        against a base whose rule concludes `value_creation` is the case the
        module docstring calls the engine's most informative behaviour, and it
        is not inert — the rebutting attack is exactly what the base has
        machinery for. `not_attention_captured` against a base where
        `attention_captured` is only ever an antecedent has no such
        counterpart: nothing concludes it, so nothing can be rebutted, and
        nothing takes the negation as an input. The base holds the word and
        owns no reasoning that can consume it in this polarity.
        """
        return not (
            pred in self._antecedents
            or pred in self._consequents
            or get_contrary(pred) in self._consequents
        )

    def analyze(self, grounded_predicates: list[str]) -> CoverageResult:
        """
        Analyze coverage of grounded predicates against the KB.

        For each predicate, tries matching in order:
          1. Exact match against vocabulary
          2. Synonym table lookup
          3. Jaccard token overlap (>= TOKEN_OVERLAP_MIN)

        Returns CoverageResult with routing decision.
        """
        if not grounded_predicates:
            return CoverageResult(decision="DECLINE")

        matched: list[str] = []
        unmatched: list[str] = []
        inert: list[str] = []
        details: dict[str, str] = {}
        relevant_vyapti_ids: set[str] = set()

        for pred in grounded_predicates:
            hit = self._match(pred)
            if hit is None:
                unmatched.append(pred)
                continue

            layer, kb_name, query_name = hit
            matched.append(pred)
            details[pred] = self._match_type(layer, query_name, kb_name)
            if self._is_inert(query_name):
                inert.append(pred)
            for vid in self._pred_to_vyaptis.get(kb_name, []):
                relevant_vyapti_ids.add(vid)

        total = len(matched) + len(unmatched)
        ratio = len(matched) / max(total, 1)

        if ratio >= FULL_THRESHOLD:
            decision = "FULL"
        elif ratio >= PARTIAL_THRESHOLD:
            decision = "PARTIAL"
        else:
            decision = "DECLINE"

        # FULL is a claim that the base can reason about this query, not just
        # that it recognises the words. When every predicate it matched is one
        # the base owns no machinery for, that claim is false however high the
        # ratio is — nothing can fire and nothing can be rebutted, so the
        # argumentation layer will come back empty.
        #
        # Demoted rather than declined, and the difference is deliberate:
        # DECLINE diverts to augmentation, which answers "can we invent a rule
        # for this?" — a different question from "should we admit we have
        # none?" The ratio, the matched list and the vyāpti routing are all
        # left exactly as they were, because the vocabulary match is real and
        # retrieval still wants the chapters these predicates point at.
        if decision == "FULL" and matched and len(inert) == len(matched):
            decision = "PARTIAL"

        return CoverageResult(
            coverage_ratio=ratio,
            matched_predicates=matched,
            unmatched_predicates=unmatched,
            match_details=details,
            relevant_vyaptis=sorted(relevant_vyapti_ids),
            inert_predicates=inert,
            decision=decision,
        )

    def _match(self, pred: str) -> tuple[str, str, str] | None:
        """Find the KB predicate this query matches: (layer, kb_name, query).

        Two forms are tried for every layer: the predicate **as written**, then
        its affirmative form. The order matters twice over.

        *As-written first*, because the vocabulary can hold a negated predicate
        literally — `not_value_creation` is V11's consequent in the knowledge
        base shipped here. Stripping before the lookup routed a query for that
        predicate to the rules producing its affirmative and never surfaced the
        rule whose conclusion it actually is.

        *Layer-major*, because an exact match on either form must beat a
        synonym on either, which must beat token overlap. Running all three
        layers on the as-written form before trying the affirmative would let a
        fuzzy token match on `not_X` outrank an exact match on `X`.

        Double negation is eliminated first: `not_not_X` is `X`, and a
        single-shot prefix strip left `not_X` — which in this knowledge base is
        a real and *opposite* predicate, so a doubly-negated query matched the
        rule concluding the negation of what it asked about.
        """
        normalized = normalize_negation(predicate_name(pred))
        unnegated = affirmative(normalized)
        # Deduplicated: for an affirmative query the two forms are the same,
        # and looking twice would be wasted work rather than wrong.
        forms = [normalized] if unnegated == normalized else [
            normalized, unnegated
        ]

        for layer in ("exact", "synonym", "token"):
            for form in forms:
                kb_name = self._lookup(layer, form)
                if kb_name:
                    return (layer, kb_name, normalized)
        return None

    def _lookup(self, layer: str, name: str) -> str:
        """The KB predicate this name matches at this layer, or "" for none."""
        if layer == "exact":
            return name if name in self._vocab else ""
        if layer == "synonym":
            canonical = self._synonym_table.get(name)
            return canonical if canonical and canonical in self._vocab else ""
        closest, score = self._find_closest_predicate(name)
        return closest if closest and score >= TOKEN_OVERLAP_MIN else ""

    @staticmethod
    def _match_type(layer: str, query: str, matched: str) -> str:
        """Which layer matched, and whether the polarity survived it.

        Two facts, so two parts: `negated_exact` says the vocabulary contains
        this predicate *and* the query asserts its negation. Collapsing them to
        a bare `negated` would lose which layer fired, and reporting only the
        layer is what made the trace claim an exact match on a string that
        differed by the token reversing its meaning.

        Determined by `negation_differs` rather than by remembering whether a
        prefix was stripped, so the whole package answers this question in one
        place — the same predicate the compiler uses to raise a rebutting
        attack and the evaluator uses to refuse a match.
        """
        return f"negated_{layer}" if negation_differs(query, matched) else layer

    def _find_closest_predicate(self, concept: str) -> tuple[str, float]:
        """
        Jaccard token overlap between concept and KB predicates.
        Split on underscores to get tokens.

        A KB predicate that contradicts the concept is skipped outright,
        whatever it scores. Token overlap cannot see negation or argument
        order: `positive_unit_economics` and `negative_unit_economics` score
        0.5 against this layer's 0.4 threshold, so coverage would report a
        match on a predicate's own negation and route the query to a vyāpti
        asserting the opposite of what was asked.
        """
        concept_tokens = set(concept.lower().replace("-", "_").split("_"))
        concept_tokens.discard("")

        if not concept_tokens:
            return ("", 0.0)

        best_pred = ""
        best_score = 0.0

        for pred in self._vocab:
            if match_veto(concept, pred, knowledge_store=self.ks):
                continue

            pred_tokens = set(pred.lower().split("_"))
            pred_tokens.discard("")

            if not pred_tokens:
                continue

            intersection = concept_tokens & pred_tokens
            union = concept_tokens | pred_tokens
            score = len(intersection) / len(union) if union else 0.0

            if score > best_score:
                best_score = score
                best_pred = pred

        return (best_pred, best_score)
