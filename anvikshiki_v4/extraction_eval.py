"""
Evaluation metrics and MIPROv2 optimization for the Predicate Extraction Pipeline.

Composite metric combining precision, recall, naming quality, vyapti completeness,
DAG validity, coverage ratio, and zero-section rate.

Soft predicate matching is Jaccard token overlap under a contrariness veto. It
is not BERTScore, and never was — this docstring and the design doc both
claimed BERTScore for a semantic matcher that has no implementation anywhere in
the package, which meant the crude path was described everywhere as the
fallback from something that was never built. Whether a semantic encoder is
needed here is an empirical question for instrument validation, not an
assumption to restate in a docstring.

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
from .predicate_contrariness import match_veto, text_veto
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

    Catches cases like 'ltv_above_cac' ~ 'ltv_exceeds_cac'. It is also blind to
    negation and to argument order, which is why every use of it goes through
    the veto in `_best_match_score` rather than through this function alone.
    """
    tokens_a = set(a.split("_"))
    tokens_b = set(b.split("_"))
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union > 0 else 0.0


# Function words carry no signal and every description contains them, so
# leaving them in makes any two descriptions look similar.
_STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "of", "to", "in", "on", "at", "by", "for", "with", "from", "as",
    "that", "this", "these", "those", "it", "its", "and", "or", "but",
    "than", "then", "when", "which", "while", "each", "per", "over",
})

MATCH_ON = ("name", "description", "either")


def _description_overlap(a: str, b: str) -> float:
    """Jaccard over content words of two natural-language descriptions."""
    tokens_a = {t for t in re.split(r"[^a-z0-9]+", a.lower()) if t} - _STOPWORDS
    tokens_b = {t for t in re.split(r"[^a-z0-9]+", b.lower()) if t} - _STOPWORDS
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def _best_match_score(
    predicted: str,
    gold_set: set[str],
    threshold: float = 0.5,
    knowledge_store=None,
    match_on: str = "name",
    subject_description: str = "",
    candidate_descriptions: dict[str, str] | None = None,
) -> float:
    """Best soft-match score for a predicted predicate against gold, or 0.0.

    A candidate that contradicts the gold predicate scores 0.0 no matter how
    many tokens it shares with it. Token overlap cannot see negation or
    argument order — `ltv_exceeds_cac` against `cac_exceeds_ltv` scores a
    perfect 1.000 — so no threshold excludes those pairs and the refusal has to
    sit above the score rather than inside it.

    `match_on` selects what is compared. Names are snake_case labels a human
    or a model invented, and none of the fourteen gold names appear literally
    in the prose they are gold for, so the extractor has to guess the label and
    the matcher has to accept the guess. Descriptions are the natural language
    both sides already carry and were being discarded.

    The default stays "name". Whether descriptions match better is an empirical
    question about this corpus, and switching the default on an untested belief
    that a looser comparison is a better one is how the original defect got in.
    Instrument validation against human judgment decides it.
    """
    if match_on not in MATCH_ON:
        raise ValueError(f"match_on must be one of {MATCH_ON}, got {match_on!r}")

    if predicted in gold_set:
        return 1.0

    candidate_descriptions = candidate_descriptions or {}
    best = 0.0

    for gold in gold_set:
        if match_veto(predicted, gold, knowledge_store=knowledge_store):
            continue

        gold_description = candidate_descriptions.get(gold, "")
        both_described = bool(subject_description and gold_description)

        if both_described and text_veto(subject_description, gold_description):
            continue

        scores = []
        if match_on in ("name", "either"):
            scores.append(_token_overlap(predicted, gold))
        if match_on in ("description", "either") and both_described:
            scores.append(
                _description_overlap(subject_description, gold_description)
            )

        if scores and max(scores) > best:
            best = max(scores)

    return best if best >= threshold else 0.0


# ─── Component Metrics ───────────────────────────────────────


def predicate_precision(
    extracted: list[str],
    gold: set[str],
    threshold: float = 0.5,
    *,
    match_on: str = "name",
    extracted_descriptions: dict[str, str] | None = None,
    gold_descriptions: dict[str, str] | None = None,
    knowledge_store=None,
) -> float:
    """Fraction of extracted predicates that match a gold predicate."""
    if not extracted:
        return 0.0
    extracted_descriptions = extracted_descriptions or {}
    matches = sum(
        1 for p in extracted
        if _best_match_score(
            p, gold, threshold,
            knowledge_store=knowledge_store,
            match_on=match_on,
            subject_description=extracted_descriptions.get(p, ""),
            candidate_descriptions=gold_descriptions,
        ) > 0
    )
    return matches / len(extracted)


def predicate_recall(
    extracted: list[str],
    gold: set[str],
    threshold: float = 0.5,
    *,
    match_on: str = "name",
    extracted_descriptions: dict[str, str] | None = None,
    gold_descriptions: dict[str, str] | None = None,
    knowledge_store=None,
) -> float:
    """Fraction of gold predicates matched by at least one extracted predicate.

    The sides swap here relative to precision: each gold predicate is the
    subject and the extracted set holds the candidates, so the description
    maps swap with them.
    """
    if not gold:
        return 0.0
    gold_descriptions = gold_descriptions or {}
    extracted_set = set(extracted)
    matches = sum(
        1
        for g in gold
        if _best_match_score(
            g, extracted_set, threshold,
            knowledge_store=knowledge_store,
            match_on=match_on,
            subject_description=gold_descriptions.get(g, ""),
            candidate_descriptions=extracted_descriptions,
        ) > 0
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
    """1.0 if validation ran and found no cycles, 0.0 otherwise.

    A validation that never ran scores 0.0 rather than 1.0. It used to return
    `1.0 if not validation.cycle_errors else 0.0`, and an empty error list
    means "no cycles found" whether or not anything looked — so a default
    `ValidationResult()` scored a clean pass while its own `is_valid` field
    said False, which the function never consulted.

    That is unearned credit, and it was the only component that gave any: a
    wholly empty run scored 0.1000 composite, every point of it from here.
    """
    if not validation.ran:
        return 0.0
    return 1.0 if not validation.cycle_errors else 0.0


def zero_section_rate(stage_a: StageAOutput) -> float:
    """1.0 minus the fraction of *answered* sections that produced nothing.

    Low zero-section rate = good (we're extracting from most sections).

    The denominator excludes sections we never got an answer for — ones that
    raised, and ones the token budget cut off. Both yield no parseable
    predicates, so counting them here scored our own configuration as a
    property of the prose: the same chapter measured 2 zero-sections at
    max_tokens=4096 and 0 at 16000, and this component carries 0.10 of the
    composite, so a setting was lowering a quality score.

    A section that was truncated *and* still parsed some predicates is
    excluded too. It was read partially, and a partial reading is not
    evidence about how much the section contained.
    """
    unanswered = stage_a.failed_sections + stage_a.truncated_sections
    answered = stage_a.section_count - unanswered
    if answered <= 0:
        return 0.0
    return 1.0 - (stage_a.zero_predicate_sections / answered)


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
        gold_descriptions: dict[str, str] | None = None,
        match_on: str = "name",
        knowledge_store=None,
    ):
        self.gold_predicates = gold_predicates
        self.gold_vyapti_count = gold_vyapti_count
        self.match_threshold = match_threshold
        self.gold_descriptions = gold_descriptions or {}
        self.match_on = match_on
        self.knowledge_store = knowledge_store

    @classmethod
    def from_gold_set(cls, gold, **kwargs) -> "ExtractionEvaluator":
        """Build an evaluator from a loaded GoldSet, descriptions included.

        `evaluate()` used to compute `[c.name for c in candidates]` and throw
        the descriptions away on both sides, which is why matching had only
        snake_case labels to work with.
        """
        return cls(
            gold_predicates=gold.names,
            gold_vyapti_count=len(gold.expected_vyaptis),
            gold_descriptions=gold.descriptions,
            **kwargs,
        )

    def evaluate(
        self,
        stage_a: StageAOutput,
        stage_d: StageDOutput,
        validation: ValidationResult,
    ) -> dict[str, object]:
        """Compute all metrics, the composite, and what went unmeasured.

        Every value is a float except "unmeasured", which lists the components
        whose input was absent. Their 0.0 is not a low score, it is the absence
        of a score, and a composite assembled from both without saying so
        reports missing inputs as poor quality.
        """
        extracted = [c.name for c in stage_a.candidates]
        extracted_descriptions = {
            c.name: c.description for c in stage_a.candidates if c.description
        }
        match_kwargs = dict(
            match_on=self.match_on,
            extracted_descriptions=extracted_descriptions,
            gold_descriptions=self.gold_descriptions,
            knowledge_store=self.knowledge_store,
        )

        metrics = {
            "precision": predicate_precision(
                extracted, self.gold_predicates, self.match_threshold,
                **match_kwargs
            ),
            "recall": predicate_recall(
                extracted, self.gold_predicates, self.match_threshold,
                **match_kwargs
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
        metrics["unmeasured"] = self._unmeasured(stage_a, stage_d, validation)

        return metrics

    @staticmethod
    def _unmeasured(
        stage_a: StageAOutput,
        stage_d: StageDOutput,
        validation: ValidationResult,
    ) -> list[str]:
        """Components whose input was absent, so their 0.0 means "not measured".

        Every component scores 0.0 on absent input, which is the safe
        direction — no unearned credit — but it makes "measured and bad"
        indistinguishable from "never measured", and a composite assembled
        from both reads as a quality figure when it is partly a report on
        missing inputs. Naming them keeps the number honest without changing
        it.
        """
        absent = []
        if not stage_a.candidates:
            absent += ["precision", "recall", "naming"]
        if not (stage_d.new_vyaptis or stage_d.refinement_vyaptis):
            absent.append("completeness")
        if not validation.ran:
            absent += ["dag_valid", "coverage"]
        if stage_a.section_count == 0:
            absent.append("zero_section")
        elif stage_a.section_count <= (
            stage_a.failed_sections + stage_a.truncated_sections
        ):
            # Sections existed but none of them was answered, so the rate has
            # no denominator left and its 0.0 is an absence, not a low score.
            absent.append("zero_section")
        if not stage_a.truncation_checked:
            # A third state, and the reason it has to be named: the run could
            # not read finish_reason, so it cannot tell a section that holds
            # no predicates from one whose answer it cut off. The figure is
            # uninterpretable rather than low, which is exactly the
            # distinction this list exists to preserve.
            absent.append("zero_section")
        return sorted(set(absent))

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
