# anvikshiki_v4/query_refinement.py
"""
Query Refinement & Coverage Check Pipeline.

Pre-pipeline stage that:
  1. Clarifies vague user queries into specific, KB-grounded questions
  2. Checks whether the KB actually covers the query direction
  3. Honestly declines when coverage is insufficient

Architecture:
  STEP 1: ClarifyIntent (1 LLM call) — map query concepts to KB predicates
  STEP 2: CoverageAnalyzer (0 LLM calls) — deterministic coverage check
  STEP 3: Route decision — PROCEED / PARTIAL / DECLINE
"""

from __future__ import annotations

from typing import Optional

import dspy
from pydantic import BaseModel, Field

from .grounding import OntologySnippetBuilder
from .schema import KnowledgeStore


# ─── DSPy Signature ─────────────────────────────────────────


class ClarifyIntent(dspy.Signature):
    """You are a query clarification assistant for a domain-specific reasoning engine.

    Given a user's question and the engine's knowledge vocabulary, your job is to:
    1. Understand what the user is REALLY asking
    2. Map their concepts to predicates the engine knows about
    3. Identify concepts the engine does NOT know about
    4. Suggest 2-3 more specific versions of the query using KB vocabulary

    Be honest: if the query touches topics not in the vocabulary, say so.
    For mapped_predicates, use ONLY predicate names from the vocabulary.
    For unmapped_concepts, use short snake_case concept names."""

    query: str = dspy.InputField(
        desc="User's original natural language question",
    )
    kb_vocabulary: str = dspy.InputField(
        desc="All predicates and rules the engine knows, with descriptions",
    )
    chapter_overview: str = dspy.InputField(
        desc="Chapter titles and key terms showing what the domain guide covers",
    )

    reasoning: str = dspy.OutputField(
        desc="Step-by-step: which query concepts map to which predicates, and which don't?",
    )
    interpreted_intent: str = dspy.OutputField(
        desc="One sentence: what is the user really trying to understand?",
    )
    mapped_predicates: list[str] = dspy.OutputField(
        desc="KB predicate names that relate to this query (empty list if none match)",
    )
    unmapped_concepts: list[str] = dspy.OutputField(
        desc="Concepts from the query that have NO matching KB predicate (snake_case)",
    )
    suggested_queries: list[str] = dspy.OutputField(
        desc="2-3 more specific versions of the query using KB vocabulary",
    )


# ─── Pydantic Models ────────────────────────────────────────


class CoverageReport(BaseModel):
    """Deterministic coverage analysis of a query against the KB."""

    matched_predicates: list[str] = Field(
        default_factory=list,
        description="KB predicates confirmed to exist",
    )
    matched_vyaptis: dict[str, str] = Field(
        default_factory=dict,
        description="vyapti_id → vyapti name for matched predicates",
    )
    unmatched_concepts: list[str] = Field(
        default_factory=list,
        description="Query concepts with no KB predicate",
    )
    closest_predicates: dict[str, str] = Field(
        default_factory=dict,
        description="unmapped_concept → nearest KB predicate",
    )
    coverage_ratio: float = Field(
        default=0.0,
        description="|matched| / (|matched| + |unmatched|)",
    )
    relevant_chapters: list[str] = Field(
        default_factory=list,
        description="Chapter IDs that cover matched predicates",
    )


class RefinementResult(BaseModel):
    """Final output of the query refinement pipeline."""

    original_query: str
    interpreted_intent: str = ""
    suggested_queries: list[str] = Field(default_factory=list)
    coverage: CoverageReport = Field(default_factory=CoverageReport)
    can_proceed: bool = False
    decline_message: str = ""


# ─── Coverage Analyzer (deterministic, 0 LLM calls) ────────


class CoverageAnalyzer:
    """Check KB coverage for a set of mapped/unmapped concepts."""

    def __init__(self, knowledge_store: KnowledgeStore):
        self.ks = knowledge_store
        self._vocab = self._build_vocabulary()
        self._pred_to_vyaptis = self._build_predicate_index()

    def _build_vocabulary(self) -> set[str]:
        """All predicates from antecedents + consequents."""
        vocab: set[str] = set()
        for v in self.ks.vyaptis.values():
            vocab.update(v.antecedents)
            if v.consequent:
                vocab.add(v.consequent)
        return vocab

    def _build_predicate_index(self) -> dict[str, list[str]]:
        """Map each predicate → list of vyapti IDs that use it."""
        index: dict[str, list[str]] = {}
        for vid, v in self.ks.vyaptis.items():
            for pred in list(v.antecedents) + [v.consequent]:
                if pred:
                    index.setdefault(pred, []).append(vid)
        return index

    def analyze(
        self,
        mapped_predicates: list[str],
        unmapped_concepts: list[str],
    ) -> CoverageReport:
        """
        Verify mapped predicates exist in KB, find closest for unmapped,
        compute coverage ratio.
        """
        # Verify mapped predicates actually exist in KB
        confirmed = [p for p in mapped_predicates if p in self._vocab]
        # Predicates the LLM claimed exist but don't — treat as unmapped
        false_matches = [p for p in mapped_predicates if p not in self._vocab]
        all_unmapped = unmapped_concepts + false_matches

        # Find vyaptis for confirmed predicates
        matched_vyaptis: dict[str, str] = {}
        for pred in confirmed:
            for vid in self._pred_to_vyaptis.get(pred, []):
                if vid not in matched_vyaptis:
                    v = self.ks.vyaptis.get(vid)
                    if v:
                        matched_vyaptis[vid] = v.name

        # Find closest KB predicate for each unmapped concept
        closest: dict[str, str] = {}
        for concept in all_unmapped:
            best_pred, best_score = self._find_closest_predicate(concept)
            if best_pred and best_score > 0.0:
                closest[concept] = best_pred

        # Coverage ratio
        total = len(confirmed) + len(all_unmapped)
        ratio = len(confirmed) / max(total, 1)

        # Relevant chapters
        chapters = self._find_relevant_chapters(confirmed)

        return CoverageReport(
            matched_predicates=confirmed,
            matched_vyaptis=matched_vyaptis,
            unmatched_concepts=all_unmapped,
            closest_predicates=closest,
            coverage_ratio=ratio,
            relevant_chapters=chapters,
        )

    def _find_closest_predicate(self, concept: str) -> tuple[str, float]:
        """
        Jaccard token overlap between concept and KB predicates.
        Split on underscores to get tokens.
        Returns (closest_predicate, similarity_score).
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

    def _find_relevant_chapters(self, predicates: list[str]) -> list[str]:
        """Which chapters introduce vyaptis that use these predicates."""
        relevant_vyapti_ids: set[str] = set()
        for pred in predicates:
            for vid in self._pred_to_vyaptis.get(pred, []):
                relevant_vyapti_ids.add(vid)

        chapters: list[str] = []
        for cid, fp in self.ks.chapter_fingerprints.items():
            if any(vid in relevant_vyapti_ids for vid in fp.vyaptis_introduced):
                chapters.append(cid)

        return sorted(chapters)


# ─── Query Refinement Pipeline ──────────────────────────────


class QueryRefinementPipeline:
    """Pre-pipeline stage: clarify query + check KB coverage."""

    COVERAGE_PROCEED = 0.6   # >= this → run full pipeline
    COVERAGE_PARTIAL = 0.2   # >= this → explain gaps, still can proceed
    # < COVERAGE_PARTIAL     → decline honestly

    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        proceed_threshold: float = 0.6,
        partial_threshold: float = 0.2,
    ):
        self.ks = knowledge_store
        self.analyzer = CoverageAnalyzer(knowledge_store)
        self.snippet_builder = OntologySnippetBuilder()
        self.clarifier = dspy.ChainOfThought(ClarifyIntent)
        self.COVERAGE_PROCEED = proceed_threshold
        self.COVERAGE_PARTIAL = partial_threshold

    def build_kb_vocabulary_prompt(self) -> str:
        """Rich vocabulary: predicate list + vyapti rule descriptions."""
        # Reuse OntologySnippetBuilder for the predicate list
        base_snippet = self.snippet_builder.build(self.ks)

        # Add vyapti statement summaries for richer context
        lines = [base_snippet, "\nRULE DESCRIPTIONS:"]
        for vid, v in self.ks.vyaptis.items():
            status = v.epistemic_status.value if v.epistemic_status else "unknown"
            lines.append(
                f"  {vid} ({v.name}): \"{v.statement}\" "
                f"[{status}]"
            )

        return "\n".join(lines)

    def build_chapter_overview(self) -> str:
        """Chapter titles + key_terms from ChapterFingerprint."""
        lines = ["DOMAIN GUIDE CHAPTERS:"]
        for cid in sorted(self.ks.chapter_fingerprints.keys()):
            fp = self.ks.chapter_fingerprints[cid]
            terms = ", ".join(fp.key_terms[:8]) if fp.key_terms else "none"
            vyaptis = ", ".join(fp.vyaptis_introduced) if fp.vyaptis_introduced else "none"
            lines.append(
                f"  {cid}: {fp.title}\n"
                f"    Key terms: {terms}\n"
                f"    Rules introduced: {vyaptis}"
            )
        return "\n".join(lines)

    def refine(self, query: str) -> RefinementResult:
        """
        1. Build vocabulary + chapter overview from KB
        2. Call ClarifyIntent (1 LLM call)
        3. Run CoverageAnalyzer on the LLM's mapped/unmapped predicates
        4. Route: PROCEED / PARTIAL / DECLINE
        """
        kb_vocab = self.build_kb_vocabulary_prompt()
        chapter_overview = self.build_chapter_overview()

        # STEP 1: Clarify intent (1 LLM call)
        clarification = self.clarifier(
            query=query,
            kb_vocabulary=kb_vocab,
            chapter_overview=chapter_overview,
        )

        mapped = clarification.mapped_predicates or []
        unmapped = clarification.unmapped_concepts or []
        intent = clarification.interpreted_intent or ""
        suggestions = clarification.suggested_queries or []

        # STEP 2: Deterministic coverage analysis (0 LLM calls)
        coverage = self.analyzer.analyze(mapped, unmapped)

        # STEP 3: Route decision
        can_proceed = coverage.coverage_ratio >= self.COVERAGE_PARTIAL
        decline_message = ""

        if coverage.coverage_ratio < self.COVERAGE_PARTIAL:
            decline_message = self._build_decline_message(coverage, intent)
        elif coverage.coverage_ratio < self.COVERAGE_PROCEED:
            decline_message = self._build_partial_message(coverage, intent)

        return RefinementResult(
            original_query=query,
            interpreted_intent=intent,
            suggested_queries=suggestions,
            coverage=coverage,
            can_proceed=can_proceed,
            decline_message=decline_message,
        )

    def _build_decline_message(
        self, coverage: CoverageReport, intent: str,
    ) -> str:
        """Honest 'I don't know' message when coverage < PARTIAL threshold."""
        parts = [
            f"I don't have relevant information in my knowledge base "
            f"about {', '.join(coverage.unmatched_concepts)}."
        ]

        # Show closest predicates if any
        if coverage.closest_predicates:
            closest_items = []
            for concept, pred in coverage.closest_predicates.items():
                # Find which vyapti uses this predicate
                vyapti_ids = self.analyzer._pred_to_vyaptis.get(pred, [])
                vyapti_name = ""
                if vyapti_ids:
                    v = self.ks.vyaptis.get(vyapti_ids[0])
                    if v:
                        vyapti_name = f" ({v.name})"
                closest_items.append(f"{pred}{vyapti_name}")

            parts.append(
                f"\nThe closest things in my knowledge base are: "
                f"{'; '.join(closest_items)}."
            )

        # Say what we'd need
        parts.append(
            f"\nTo answer your question about '{intent}', I would need "
            f"information about: {', '.join(coverage.unmatched_concepts)}."
        )

        return "\n".join(parts)

    def _build_partial_message(
        self, coverage: CoverageReport, intent: str,
    ) -> str:
        """Partial coverage message — explain what's covered and what's missing."""
        # What we know
        known_items = []
        for pred in coverage.matched_predicates:
            vyapti_ids = self.analyzer._pred_to_vyaptis.get(pred, [])
            if vyapti_ids:
                v = self.ks.vyaptis.get(vyapti_ids[0])
                if v:
                    chapters = ", ".join(coverage.relevant_chapters) or "?"
                    known_items.append(f"{pred} ({v.name}, {chapters})")
                    continue
            known_items.append(pred)

        parts = [
            f"I can partially answer this. My knowledge base covers:"
        ]
        for item in known_items:
            parts.append(f"  - {item}")

        # What we don't know
        if coverage.unmatched_concepts:
            parts.append(
                f"\nHowever, I don't have specific rules about: "
                f"{', '.join(coverage.unmatched_concepts)}."
            )

        # Closest matches for gaps
        if coverage.closest_predicates:
            closest_str = ", ".join(
                f"{concept} → {pred}"
                for concept, pred in coverage.closest_predicates.items()
            )
            parts.append(
                f"The closest related concepts I have: {closest_str}."
            )

        return "\n".join(parts)
