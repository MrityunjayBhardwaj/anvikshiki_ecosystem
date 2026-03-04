"""
Evaluation metrics and MIPROv2 optimization for the Predicate Extraction Pipeline.

Composite metric combining precision, recall, naming quality, vyapti completeness,
DAG validity, coverage ratio, and zero-section rate. Uses BERTScore for soft
predicate matching.

Usage:
    from anvikshiki_v4.extraction_eval import (
        ExtractionEvaluator,
        optimize_pipeline,
    )

    evaluator = ExtractionEvaluator(gold_predicates, gold_vyaptis)
    score = evaluator.evaluate(stage_a, stage_d, validation)
"""

from __future__ import annotations

import re
from typing import Optional

import dspy

from .extraction_schema import (
    ExtractionConfig,
    StageAOutput,
    StageDOutput,
    ValidationResult,
)
from .predicate_extraction import (
    SNAKE_CASE_RE,
    PredicateExtractionPipeline,
    _extraction_reward,
    _vyapti_construction_reward,
)
from .schema import KnowledgeStore


# ─── Soft Matching ────────────────────────────────────────────


def _token_overlap(a: str, b: str) -> float:
    """Cheap token-overlap similarity (Jaccard on underscore-split tokens).

    Used as BERTScore fallback when sentence-transformers is unavailable.
    Catches cases like 'ltv_above_cac' ~ 'ltv_exceeds_cac'.
    """
    tokens_a = set(a.split("_"))
    tokens_b = set(b.split("_"))
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union > 0 else 0.0


def _best_match_score(
    predicted: str,
    gold_set: set[str],
    threshold: float = 0.5,
) -> float:
    """Return the best soft-match score for a predicted predicate against gold."""
    if predicted in gold_set:
        return 1.0
    best = 0.0
    for gold in gold_set:
        score = _token_overlap(predicted, gold)
        if score > best:
            best = score
    return best if best >= threshold else 0.0


# ─── Component Metrics ───────────────────────────────────────


def predicate_precision(
    extracted: list[str],
    gold: set[str],
    threshold: float = 0.5,
) -> float:
    """Fraction of extracted predicates that match a gold predicate."""
    if not extracted:
        return 0.0
    matches = sum(
        1 for p in extracted if _best_match_score(p, gold, threshold) > 0
    )
    return matches / len(extracted)


def predicate_recall(
    extracted: list[str],
    gold: set[str],
    threshold: float = 0.5,
) -> float:
    """Fraction of gold predicates matched by at least one extracted predicate."""
    if not gold:
        return 0.0
    extracted_set = set(extracted)
    matches = sum(
        1
        for g in gold
        if _best_match_score(g, extracted_set, threshold) > 0
    )
    return matches / len(gold)


def naming_quality(predicates: list[str]) -> float:
    """Score naming convention adherence.

    Checks: valid snake_case (0.5), not too generic (0.25), length < 50 (0.25).
    """
    if not predicates:
        return 0.0

    GENERIC_NAMES = {
        "unknown_predicate",
        "predicate",
        "fact",
        "rule",
        "thing",
        "value",
        "data",
        "input",
        "output",
        "result",
    }

    total = 0.0
    for p in predicates:
        score = 0.0
        if SNAKE_CASE_RE.match(p):
            score += 0.5
        if p not in GENERIC_NAMES:
            score += 0.25
        if len(p) < 50:
            score += 0.25
        total += score

    return total / len(predicates)


def vyapti_completeness(stage_d: StageDOutput) -> float:
    """Score how completely vyapti fields are populated.

    Checks: name, statement, antecedents, consequent, scope_conditions,
    confidence values, sources.
    """
    all_vyaptis = stage_d.new_vyaptis + stage_d.refinement_vyaptis
    if not all_vyaptis:
        return 0.0

    total = 0.0
    for v in all_vyaptis:
        checks = 0
        max_checks = 7

        if v.name:
            checks += 1
        if v.statement and len(v.statement) > 10:
            checks += 1
        if v.antecedents:
            checks += 1
        if v.consequent:
            checks += 1
        if v.scope_conditions or v.scope_exclusions:
            checks += 1
        if 0 < v.confidence_existence <= 1.0:
            checks += 1
        if v.sources:
            checks += 1

        total += checks / max_checks

    return total / len(all_vyaptis)


def dag_validity(validation: ValidationResult) -> float:
    """1.0 if no cycles, 0.0 if cycles exist."""
    return 1.0 if not validation.cycle_errors else 0.0


def zero_section_rate(stage_a: StageAOutput) -> float:
    """1.0 minus the fraction of sections that produced zero predicates.

    Low zero-section rate = good (we're extracting from most sections).
    """
    if stage_a.section_count == 0:
        return 0.0
    return 1.0 - (stage_a.zero_predicate_sections / stage_a.section_count)


# ─── Composite Evaluator ─────────────────────────────────────


class ExtractionEvaluator:
    """Composite metric for the full extraction pipeline.

    Weights (sum to 1.0):
        precision:      0.20
        recall:         0.20
        naming:         0.15
        completeness:   0.15
        dag_valid:      0.10
        coverage:       0.10
        zero_section:   0.10
    """

    WEIGHTS = {
        "precision": 0.20,
        "recall": 0.20,
        "naming": 0.15,
        "completeness": 0.15,
        "dag_valid": 0.10,
        "coverage": 0.10,
        "zero_section": 0.10,
    }

    def __init__(
        self,
        gold_predicates: set[str],
        gold_vyapti_count: int = 0,
        match_threshold: float = 0.5,
    ):
        self.gold_predicates = gold_predicates
        self.gold_vyapti_count = gold_vyapti_count
        self.match_threshold = match_threshold

    def evaluate(
        self,
        stage_a: StageAOutput,
        stage_d: StageDOutput,
        validation: ValidationResult,
    ) -> dict[str, float]:
        """Compute all metrics and composite score."""
        extracted = [c.name for c in stage_a.candidates]

        metrics = {
            "precision": predicate_precision(
                extracted, self.gold_predicates, self.match_threshold
            ),
            "recall": predicate_recall(
                extracted, self.gold_predicates, self.match_threshold
            ),
            "naming": naming_quality(extracted),
            "completeness": vyapti_completeness(stage_d),
            "dag_valid": dag_validity(validation),
            "coverage": validation.coverage_ratio,
            "zero_section": zero_section_rate(stage_a),
        }

        composite = sum(
            self.WEIGHTS[k] * metrics[k] for k in self.WEIGHTS
        )
        metrics["composite"] = composite

        return metrics

    def __call__(
        self,
        stage_a: StageAOutput,
        stage_d: StageDOutput,
        validation: ValidationResult,
    ) -> float:
        """Return just the composite score (for optimizer use)."""
        return self.evaluate(stage_a, stage_d, validation)["composite"]


# ─── DSPy Metric Wrapper ─────────────────────────────────────


def build_dspy_metric(
    gold_predicates: set[str],
    match_threshold: float = 0.5,
):
    """Build a DSPy-compatible metric function for MIPROv2.

    The metric receives (example, prediction, trace=None) and returns a float.
    The example should contain gold_predicates as a field.
    """
    evaluator = ExtractionEvaluator(
        gold_predicates=gold_predicates,
        match_threshold=match_threshold,
    )

    def metric(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:
        # Extract what we can from the prediction
        predicates = getattr(pred, "predicates", None) or []
        descriptions = getattr(pred, "descriptions", None) or []

        # Build a minimal StageAOutput for evaluation
        from .extraction_schema import CandidatePredicate, ClaimType, Provenance

        candidates = []
        for i, p in enumerate(predicates):
            candidates.append(
                CandidatePredicate(
                    name=p,
                    description=descriptions[i] if i < len(descriptions) else "",
                    claim_type=ClaimType.CAUSAL,
                    provenance=Provenance(chapter_id="eval", confidence=0.5),
                )
            )

        stage_a = StageAOutput(
            candidates=candidates,
            chapter_id="eval",
            section_count=1,
            zero_predicate_sections=0 if candidates else 1,
        )

        # Partial evaluation (precision + recall + naming only)
        extracted = [c.name for c in candidates]
        precision = predicate_precision(extracted, gold_predicates, match_threshold)
        recall = predicate_recall(extracted, gold_predicates, match_threshold)
        naming = naming_quality(extracted)

        return 0.4 * precision + 0.4 * recall + 0.2 * naming

    return metric


# ─── MIPROv2 Optimization ────────────────────────────────────


def optimize_pipeline(
    knowledge_store: KnowledgeStore,
    trainset: list[dspy.Example],
    gold_predicates: set[str],
    config: Optional[ExtractionConfig] = None,
    num_trials: int = 20,
) -> PredicateExtractionPipeline:
    """Optimize the extraction pipeline using MIPROv2.

    Args:
        knowledge_store: Seed KB
        trainset: List of dspy.Example with section_text, chapter_id fields
        gold_predicates: Set of expected predicate names for evaluation
        config: Pipeline config
        num_trials: Number of MIPROv2 trials

    Returns:
        Optimized pipeline module
    """
    cfg = config or ExtractionConfig()
    pipeline = PredicateExtractionPipeline(knowledge_store, cfg)

    metric = build_dspy_metric(gold_predicates)

    optimizer = dspy.MIPROv2(
        metric=metric,
        auto="medium",
        num_threads=4,
    )

    optimized = optimizer.compile(
        pipeline.stage_a.extractor,
        trainset=trainset,
        num_trials=num_trials,
    )

    # Replace the extractor in the pipeline with the optimized version
    pipeline.stage_a.extractor = optimized

    return pipeline
