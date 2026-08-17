# tests/test_degenerate_input.py
"""No component may score a pass on an absence of evidence.

Most metrics already degraded safely to 0.0 on empty input. One did not:
`dag_validity(ValidationResult())` returned **1.0** while that same object's
`is_valid` field said False — because it read an empty `cycle_errors` list as
"no cycles found", which is also what a validation that never ran looks like.

That is the whole class. A check that never ran, a retriever that fell back to
keyword overlap, a validation constructed as a literal — each produces output
indistinguishable from the healthy case, and each reads as success.
"""

import pytest

from anvikshiki_v4.extraction_eval import (
    ExtractionEvaluator,
    dag_validity,
    naming_quality,
    predicate_precision,
    predicate_recall,
    vyapti_completeness,
    zero_section_rate,
)
from anvikshiki_v4.extraction_hitl import render_validation_summary
from anvikshiki_v4.extraction_schema import (
    CandidatePredicate,
    ClaimType,
    Provenance,
    StageAOutput,
    StageDOutput,
    ValidationResult,
)
from anvikshiki_v4.t3a_retriever import T3aRetriever


# ── every metric on absent input ──

@pytest.mark.parametrize(
    "label,value",
    [
        ("precision, no extraction", predicate_precision([], {"a"})),
        ("recall, no extraction", predicate_recall([], {"a"})),
        ("precision, no gold", predicate_precision(["x"], set())),
        ("recall, no gold", predicate_recall(["x"], set())),
        ("naming, no predicates", naming_quality([])),
        ("completeness, no vyaptis", vyapti_completeness(StageDOutput())),
        ("zero_section, no sections", zero_section_rate(StageAOutput())),
        ("dag_validity, validation never ran", dag_validity(ValidationResult())),
    ],
)
def test_no_metric_scores_above_zero_on_absent_input(label, value):
    assert value == 0.0, f"{label} scored {value} on nothing"


def test_a_validation_that_never_ran_does_not_score_as_valid():
    """The specific defect: the object says False and the metric said 1.0."""
    never_ran = ValidationResult()
    assert never_ran.ran is False
    assert never_ran.is_valid is False
    assert dag_validity(never_ran) == 0.0


def test_a_validation_that_ran_and_found_no_cycles_still_scores_one():
    """The other half — the fix must not punish a genuine clean pass."""
    clean = ValidationResult(ran=True, is_valid=True)
    assert dag_validity(clean) == 1.0


def test_a_validation_that_ran_and_found_cycles_scores_zero():
    assert dag_validity(ValidationResult(ran=True, cycle_errors=["a→b→a"])) == 0.0


def test_the_composite_of_a_wholly_empty_run_is_zero():
    """It was 0.1000, every point of it unearned credit from dag_valid."""
    evaluator = ExtractionEvaluator(gold_predicates={"a", "b"})
    metrics = evaluator.evaluate(
        StageAOutput(), StageDOutput(), ValidationResult()
    )
    assert metrics["composite"] == 0.0


def test_an_empty_run_names_what_it_could_not_measure():
    """0.0 from absent input and 0.0 from bad output must be distinguishable."""
    evaluator = ExtractionEvaluator(gold_predicates={"a", "b"})
    metrics = evaluator.evaluate(
        StageAOutput(), StageDOutput(), ValidationResult()
    )
    unmeasured = metrics["unmeasured"]
    assert set(unmeasured) == {
        "completeness", "coverage", "dag_valid", "naming",
        "precision", "recall", "zero_section",
    }


def test_a_real_run_reports_nothing_unmeasured():
    """A run with real inputs must not be flagged — otherwise the flag is noise."""
    stage_a = StageAOutput(
        candidates=[
            CandidatePredicate(
                name="ltv_exceeds_cac",
                description="Lifetime value exceeds customer acquisition cost",
                claim_type=ClaimType.METRIC,
                provenance=Provenance(chapter_id="ch02", confidence=0.7),
            )
        ],
        chapter_id="ch02",
        section_count=3,
    )
    evaluator = ExtractionEvaluator(gold_predicates={"ltv_exceeds_cac"})
    metrics = evaluator.evaluate(
        stage_a, StageDOutput(), ValidationResult(ran=True, is_valid=True)
    )
    assert metrics["unmeasured"] == ["completeness"]   # no vyaptis supplied
    assert metrics["precision"] == 1.0


# ── the HITL summary ──

def test_the_review_summary_says_when_validation_never_ran():
    """A reviewer deciding what to accept needs "not checked", not "invalid"."""
    summary = render_validation_summary(ValidationResult())
    assert "NOT RUN" in summary
    assert "Valid: False" not in summary


def test_the_review_summary_reports_a_real_validation_normally():
    summary = render_validation_summary(
        ValidationResult(ran=True, is_valid=True, coverage_ratio=0.8)
    )
    assert "NOT RUN" not in summary
    assert "Valid: True" in summary


# ── the retriever's silent fallback ──

def test_a_retriever_with_no_chunks_says_it_is_degraded():
    retriever = T3aRetriever(chunks=[])
    assert retriever.is_degraded
    assert "no chunks" in retriever.degraded_reason


def test_a_retriever_that_cannot_build_an_index_says_why():
    """Keyword fallback answers every query and used to report nothing."""
    from anvikshiki_v4.t3_compiler import TextChunk

    chunks = [
        TextChunk(
            chunk_id="ch02-1",
            chapter_id="ch02",
            text="unit economics are per-customer profitability",
        )
    ]
    retriever = T3aRetriever(chunks=chunks, model="not/a-real-embedding-model")

    if retriever.is_degraded:
        assert "keyword overlap" in retriever.degraded_reason
    else:
        # An index built, which is the healthy path — then nothing is degraded.
        assert retriever.degraded_reason is None
