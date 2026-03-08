"""
Semantic Coverage Analyzer for the Ānvīkṣikī Engine.

Three-layer predicate matching against base + fine-grained KB:
  1. Exact match against known vocabulary
  2. Synonym lookup (from T2b synonym table)
  3. Jaccard token overlap (fallback)

Produces a routing decision: FULL / PARTIAL / DECLINE.
Zero LLM calls — fully deterministic.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

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
        description="predicate -> match_type (exact/synonym/token)",
    )
    relevant_vyaptis: list[str] = Field(default_factory=list)
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
        details: dict[str, str] = {}
        relevant_vyapti_ids: set[str] = set()

        for pred in grounded_predicates:
            # Strip entity from predicate(entity) format
            pred_name = pred.split("(")[0].strip() if "(" in pred else pred
            # Strip not_ prefix for matching
            base_name = pred_name[4:] if pred_name.startswith("not_") else pred_name

            # Layer 1: Exact match
            if base_name in self._vocab:
                matched.append(pred)
                details[pred] = "exact"
                for vid in self._pred_to_vyaptis.get(base_name, []):
                    relevant_vyapti_ids.add(vid)
                continue

            # Layer 2: Synonym lookup
            canonical = self._synonym_table.get(base_name)
            if canonical and canonical in self._vocab:
                matched.append(pred)
                details[pred] = "synonym"
                for vid in self._pred_to_vyaptis.get(canonical, []):
                    relevant_vyapti_ids.add(vid)
                continue

            # Layer 3: Jaccard token overlap
            closest, score = self._find_closest_predicate(base_name)
            if closest and score >= TOKEN_OVERLAP_MIN:
                matched.append(pred)
                details[pred] = "token"
                for vid in self._pred_to_vyaptis.get(closest, []):
                    relevant_vyapti_ids.add(vid)
                continue

            unmatched.append(pred)

        total = len(matched) + len(unmatched)
        ratio = len(matched) / max(total, 1)

        if ratio >= FULL_THRESHOLD:
            decision = "FULL"
        elif ratio >= PARTIAL_THRESHOLD:
            decision = "PARTIAL"
        else:
            decision = "DECLINE"

        return CoverageResult(
            coverage_ratio=ratio,
            matched_predicates=matched,
            unmatched_predicates=unmatched,
            match_details=details,
            relevant_vyaptis=sorted(relevant_vyapti_ids),
            decision=decision,
        )

    def _find_closest_predicate(self, concept: str) -> tuple[str, float]:
        """
        Jaccard token overlap between concept and KB predicates.
        Split on underscores to get tokens.
        """
        concept_tokens = set(concept.lower().replace("-", "_").split("_"))
        concept_tokens.discard("")

        if not concept_tokens:
            return ("", 0.0)

        best_pred = ""
        best_score = 0.0

        for pred in self._vocab:
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
