"""
Adaptive Knowledge Landscape (AKL) — T3b query-time augmentation pipeline.

Generates structured predicates for queries that DECLINE against the KB.
Uses existing vyaptis as conceptual templates to project the query onto
the domain's framework axes, then generates new HYPOTHESIS vyaptis.

Hybrid approach: LLM parametric knowledge (v1). Web search deferred to v2.

Key properties:
  - Augmented predicates are regular Vyapti objects (no special-casing)
  - Confidence capped at 0.75 (never exceeds curated KB confidence)
  - Validation reuses Stage E (cycle detection + Datalog compile)
  - Selective: only triggers on DECLINE + in-domain queries
  - 2 LLM calls per augmentation (domain check + generate)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import dspy
from pydantic import BaseModel, Field

from .coverage import CoverageResult
from .grounding import OntologySnippetBuilder
from .predicate_extraction import _detect_cycles, _enforce_snake_case
from .schema import (
    AugmentationMetadata,
    AugmentationOrigin,
    CausalStatus,
    Confidence,
    DecayRisk,
    EpistemicStatus,
    KnowledgeStore,
    Vyapti,
)


# ─── Constants ───────────────────────────────────────────────

APPLICABILITY_THRESHOLD = 0.4
MAX_NEW_VYAPTIS = 8
MAX_CONFIDENCE = 0.75


# ─── Result Model ────────────────────────────────────────────


class AugmentationResult(BaseModel):
    """Output of the AKL augmentation pipeline."""

    augmented: bool = False
    reason: str = ""
    framework_score: float = 0.0
    new_vyaptis: list[Vyapti] = Field(default_factory=list)
    merged_kb: Optional[KnowledgeStore] = None
    validation_warnings: list[str] = Field(default_factory=list)


# ─── DSPy Signatures ────────────────────────────────────────


class ScoreFrameworkApplicability(dspy.Signature):
    """Score how applicable the domain's reasoning framework is to a query.

    Consider whether the domain's vyaptis (causal rules) and conceptual axes
    can meaningfully analyze this query, even if specific predicates are missing.
    Score 0.0-1.0 where >= 0.4 means the framework can contribute useful analysis."""

    query: str = dspy.InputField(desc="User's natural language question")
    interpreted_intent: str = dspy.InputField(
        desc="One-sentence interpretation of what the user wants to understand"
    )
    framework_summary: str = dspy.InputField(
        desc="Summary of the domain's vyaptis (causal rules) and conceptual axes"
    )
    domain_type: str = dspy.InputField(desc="Domain classification")

    reasoning: str = dspy.OutputField(
        desc="Which framework axes apply and why? Which don't?"
    )
    applicability_score: float = dspy.OutputField(
        desc="0.0-1.0: how much can the framework contribute? >= 0.4 means worthwhile"
    )
    applicable_vyaptis: list[str] = dspy.OutputField(
        desc="IDs of vyaptis whose conceptual axes apply (e.g. ['V02', 'V06'])"
    )
    applicable_chapters: list[str] = dspy.OutputField(
        desc="IDs of relevant chapters (e.g. ['ch03', 'ch10'])"
    )


class GenerateAugmentationPredicates(dspy.Signature):
    """Generate new predicates using existing vyaptis as structural templates.

    The existing vyaptis define conceptual axes. Project the query domain
    onto these axes to create specific predicates. Be conservative:
    - confidence_existence MUST be <= 0.75
    - epistemic_status MUST be 'hypothesis'
    - Scope conditions MUST include the query's specific domain
    - New predicates should chain into existing vyapti consequents/antecedents

    Return parallel lists (same length for all output fields)."""

    query: str = dspy.InputField(desc="User's natural language question")
    interpreted_intent: str = dspy.InputField(
        desc="What the user wants to understand"
    )
    applicable_vyaptis: str = dspy.InputField(
        desc="Full text of applicable vyaptis (ID, name, statement, antecedents, consequent)"
    )
    chapter_context: str = dspy.InputField(
        desc="Relevant chapter titles and key terms"
    )
    existing_predicates: str = dspy.InputField(
        desc="All existing predicate names in the KB"
    )

    reasoning: str = dspy.OutputField(
        desc="How do existing axes project onto the query domain?"
    )
    vyapti_names: list[str] = dspy.OutputField(
        desc="Short descriptive name for each new vyapti"
    )
    vyapti_statements: list[str] = dspy.OutputField(
        desc="Precise English statement of each invariable relation"
    )
    antecedents_list: list[str] = dspy.OutputField(
        desc="Comma-separated antecedent predicates for each vyapti"
    )
    consequents: list[str] = dspy.OutputField(
        desc="Consequent predicate for each vyapti"
    )
    causal_statuses: list[str] = dspy.OutputField(
        desc="One of: structural, regulatory, empirical, definitional"
    )
    scope_conditions_list: list[str] = dspy.OutputField(
        desc="Comma-separated scope conditions for each vyapti"
    )
    confidence_existences: list[float] = dspy.OutputField(
        desc="Confidence existence for each (MUST be <= 0.75)"
    )
    base_vyaptis_used: list[str] = dspy.OutputField(
        desc="Which existing vyapti ID was the template for each"
    )


# ─── Pipeline ────────────────────────────────────────────────


class AugmentationPipeline(dspy.Module):
    """
    T3b query-time augmentation pipeline.

    Steps:
      1. Score framework applicability (1 LLM call)
      2. Generate predicates using base KB axes as templates (1 LLM call)
      3. Validate: cycle detection + Datalog compile (0 LLM calls)
      4. Merge into KnowledgeStore copy (0 LLM calls)
    """

    def __init__(self, knowledge_store: KnowledgeStore):
        super().__init__()
        self.ks = knowledge_store
        self.snippet_builder = OntologySnippetBuilder()
        self.score_framework = dspy.ChainOfThought(ScoreFrameworkApplicability)
        self.generate = dspy.ChainOfThought(GenerateAugmentationPredicates)

    def forward(
        self,
        query: str,
        interpreted_intent: str = "",
        coverage_result: Optional[CoverageResult] = None,
    ) -> AugmentationResult:
        """Run the augmentation pipeline."""
        intent = interpreted_intent or query

        # STEP 1: Domain check (1 LLM call)
        framework_summary = self._build_framework_summary()
        domain_check = self.score_framework(
            query=query,
            interpreted_intent=intent,
            framework_summary=framework_summary,
            domain_type=self.ks.domain_type.value,
        )

        score = getattr(domain_check, "applicability_score", 0.0) or 0.0
        if score < APPLICABILITY_THRESHOLD:
            return AugmentationResult(
                augmented=False,
                reason=f"Framework applicability too low ({score:.2f} < {APPLICABILITY_THRESHOLD})",
                framework_score=score,
            )

        applicable_vyapti_ids = getattr(domain_check, "applicable_vyaptis", []) or []
        applicable_chapter_ids = getattr(domain_check, "applicable_chapters", []) or []

        # STEP 2: Generate predicates (1 LLM call)
        applicable_text = self._build_applicable_vyaptis_text(applicable_vyapti_ids)
        chapter_ctx = self._build_chapter_context(applicable_chapter_ids)
        existing_preds = self._get_all_predicates()

        generation = self.generate(
            query=query,
            interpreted_intent=intent,
            applicable_vyaptis=applicable_text,
            chapter_context=chapter_ctx,
            existing_predicates=existing_preds,
        )

        # STEP 3: Parse and validate
        new_vyaptis, warnings = self._parse_and_validate(
            generation, query, applicable_vyapti_ids
        )

        if not new_vyaptis:
            return AugmentationResult(
                augmented=False,
                reason="No valid vyaptis generated after validation",
                framework_score=score,
                validation_warnings=warnings,
            )

        # STEP 4: Merge into KB copy
        merged_kb = self._merge_kb(new_vyaptis)

        return AugmentationResult(
            augmented=True,
            reason=f"Generated {len(new_vyaptis)} augmentation vyaptis",
            framework_score=score,
            new_vyaptis=new_vyaptis,
            merged_kb=merged_kb,
            validation_warnings=warnings,
        )

    # ── Helper Methods ──

    def _build_framework_summary(self) -> str:
        """Build a summary of the domain's vyaptis for the domain check."""
        lines = [f"Domain: {self.ks.domain_type.value}", "Framework axes:"]
        for vid, v in self.ks.vyaptis.items():
            lines.append(
                f"  {vid}: {v.name} — {v.statement[:100]}"
            )
        return "\n".join(lines)

    def _build_applicable_vyaptis_text(self, vyapti_ids: list[str]) -> str:
        """Build full text of applicable vyaptis for predicate generation."""
        ids = vyapti_ids or list(self.ks.vyaptis.keys())
        lines = []
        for vid in ids:
            v = self.ks.vyaptis.get(vid)
            if not v:
                continue
            lines.append(
                f"VYAPTI {vid}: {v.name}\n"
                f"  Statement: {v.statement}\n"
                f"  Antecedents: {', '.join(v.antecedents)}\n"
                f"  Consequent: {v.consequent}\n"
                f"  Scope: {', '.join(v.scope_conditions)}\n"
                f"  Status: {v.epistemic_status.value}"
            )
        return "\n\n".join(lines) if lines else "No applicable vyaptis found."

    def _build_chapter_context(self, chapter_ids: list[str]) -> str:
        """Build chapter context string."""
        ids = chapter_ids or list(self.ks.chapter_fingerprints.keys())
        lines = []
        for cid in ids:
            fp = self.ks.chapter_fingerprints.get(cid)
            if fp:
                terms = ", ".join(fp.key_terms[:6])
                lines.append(f"{cid}: {fp.title} (terms: {terms})")
        return "\n".join(lines) if lines else "No chapter context available."

    def _get_all_predicates(self) -> str:
        """Get all existing predicate names."""
        preds: set[str] = set()
        for v in self.ks.vyaptis.values():
            preds.update(v.antecedents)
            if v.consequent:
                preds.add(v.consequent)
        return ", ".join(sorted(preds))

    def _parse_and_validate(
        self,
        generation: dspy.Prediction,
        query: str,
        framework_vyaptis: list[str],
    ) -> tuple[list[Vyapti], list[str]]:
        """Parse LLM output into Vyapti objects, validate, return survivors."""
        warnings: list[str] = []

        names = getattr(generation, "vyapti_names", []) or []
        statements = getattr(generation, "vyapti_statements", []) or []
        antecedents_raw = getattr(generation, "antecedents_list", []) or []
        consequents = getattr(generation, "consequents", []) or []
        causal_statuses = getattr(generation, "causal_statuses", []) or []
        scope_raw = getattr(generation, "scope_conditions_list", []) or []
        conf_existences = getattr(generation, "confidence_existences", []) or []
        base_vyaptis = getattr(generation, "base_vyaptis_used", []) or []

        if not names:
            return [], ["No vyapti names generated"]

        # Determine next vyapti ID
        existing_ids = sorted(self.ks.vyaptis.keys())
        next_num = max((int(vid[1:]) for vid in existing_ids if vid[1:].isdigit()), default=0) + 1

        vyaptis: list[Vyapti] = []
        now = datetime.now()

        for i in range(min(len(names), MAX_NEW_VYAPTIS)):
            try:
                name = names[i] if i < len(names) else ""
                statement = statements[i] if i < len(statements) else ""
                if not name or not statement:
                    continue

                # Parse antecedents (comma-separated string)
                ant_str = antecedents_raw[i] if i < len(antecedents_raw) else ""
                antecedents = [
                    _enforce_snake_case(a.strip())
                    for a in ant_str.split(",") if a.strip()
                ]
                if not antecedents:
                    warnings.append(f"Skipped '{name}': no antecedents")
                    continue

                consequent = _enforce_snake_case(
                    consequents[i] if i < len(consequents) else ""
                )
                if not consequent:
                    warnings.append(f"Skipped '{name}': no consequent")
                    continue

                # Parse causal status
                cs_str = causal_statuses[i] if i < len(causal_statuses) else "empirical"
                try:
                    causal_status = CausalStatus(cs_str)
                except ValueError:
                    causal_status = CausalStatus.EMPIRICAL

                # Parse scope conditions
                scope_str = scope_raw[i] if i < len(scope_raw) else ""
                scope_conditions = [
                    s.strip() for s in scope_str.split(",") if s.strip()
                ]

                # Cap confidence
                raw_conf = conf_existences[i] if i < len(conf_existences) else 0.6
                conf_existence = min(float(raw_conf), MAX_CONFIDENCE)
                conf_formulation = min(conf_existence * 0.85, MAX_CONFIDENCE)

                base_v = base_vyaptis[i] if i < len(base_vyaptis) else ""

                vid = f"V{next_num:02d}"
                next_num += 1

                vyapti = Vyapti(
                    id=vid,
                    name=name,
                    statement=statement,
                    causal_status=causal_status,
                    scope_conditions=scope_conditions,
                    scope_exclusions=[],
                    confidence=Confidence(
                        existence=conf_existence,
                        formulation=conf_formulation,
                        evidence="theoretical",
                    ),
                    epistemic_status=EpistemicStatus.WORKING_HYPOTHESIS,
                    decay_risk=DecayRisk.MODERATE,
                    sources=[],
                    antecedents=antecedents,
                    consequent=consequent,
                    augmentation_metadata=AugmentationMetadata(
                        origin=AugmentationOrigin.LLM_PARAMETRIC,
                        generated_at=now,
                        generating_query=query,
                        framework_vyaptis_used=framework_vyaptis,
                        parent_vyapti_id=base_v if base_v in self.ks.vyaptis else None,
                    ),
                )
                vyaptis.append(vyapti)

            except Exception as e:
                warnings.append(f"Failed to parse vyapti {i}: {e}")
                continue

        # Cycle detection
        adj: dict[str, set[str]] = {}
        for v in self.ks.vyaptis.values():
            for ant in v.antecedents:
                adj.setdefault(ant, set()).add(v.consequent)
        for v in vyaptis:
            for ant in v.antecedents:
                adj.setdefault(ant, set()).add(v.consequent)

        cycles = _detect_cycles(adj)
        if cycles:
            cycle_preds: set[str] = set()
            for c in cycles:
                cycle_preds.update(c)
            before = len(vyaptis)
            vyaptis = [v for v in vyaptis if v.consequent not in cycle_preds]
            warnings.append(
                f"Removed {before - len(vyaptis)} vyaptis due to cycles"
            )

        # Datalog compile test
        try:
            from .datalog_engine import DatalogEngine, EpistemicValue, Fact, Rule

            engine = DatalogEngine(boolean_mode=True)
            all_vyaptis = list(self.ks.vyaptis.values()) + vyaptis
            for v in all_vyaptis:
                engine.add_rule(Rule(
                    vyapti_id=v.id, name=v.name, head=v.consequent,
                    body_positive=v.antecedents,
                    body_negative=v.scope_exclusions,
                    confidence=EpistemicValue.ESTABLISHED,
                ))
            # Add synthetic facts
            all_ants: set[str] = set()
            for v in all_vyaptis:
                all_ants.update(v.antecedents)
            for ant in all_ants:
                engine.add_fact(Fact(predicate=ant, entity="test"))
            engine.evaluate()
        except Exception as e:
            warnings.append(f"Datalog compile warning: {e}")

        return vyaptis, warnings

    def _merge_kb(self, new_vyaptis: list[Vyapti]) -> KnowledgeStore:
        """Merge augmented vyaptis into a KnowledgeStore copy."""
        merged = self.ks.model_copy(deep=True)
        for v in new_vyaptis:
            merged.vyaptis[v.id] = v
        return merged
