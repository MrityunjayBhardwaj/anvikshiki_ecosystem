# tests/test_instrument_validation.py
"""The harness grades extraction; this is what grades the harness.

Until something does, a precision figure means "the matcher said so" rather
than "this is right" — and the matcher previously said an extractor emitting
the exact inverse of every gold predicate scored 1.000/1.000.
"""

import pytest

from anvikshiki_v4.instrument_validation import (
    AGREE,
    DISAGREE,
    MatcherDecision,
    agreement,
    build_decision_sheet,
    read_decision_sheet,
    write_decision_sheet,
)

GOLD = {"ltv_exceeds_cac", "high_retention_rate", "value_creation"}
GOLD_DESCRIPTIONS = {
    "ltv_exceeds_cac": "Lifetime value exceeds customer acquisition cost",
    "high_retention_rate": "Customer retention rate is high (low churn)",
    "value_creation": "The business creates value",
}
CANDIDATES = [
    ("ltv_above_cac", "Lifetime value is above acquisition cost"),
    ("cac_exceeds_ltv", "Acquisition cost exceeds lifetime value"),
    ("customers_stay_subscribed", "Customer retention rate is high (low churn)"),
]


# ── what lands on the sheet ──

def test_the_sheet_carries_the_matches_as_precision_claims():
    sheet = build_decision_sheet(GOLD, GOLD_DESCRIPTIONS, CANDIDATES)
    matched = [d for d in sheet if d.kind == "matched"]
    assert matched, "no matched pairs reached the sheet"
    assert all(d.matcher_says_match for d in matched)
    assert any(
        d.gold == "ltv_exceeds_cac" and d.candidate == "ltv_above_cac"
        for d in matched
    )


def test_the_sheet_carries_near_misses_as_recall_claims():
    """The half a review built around extractor output cannot produce.

    Without these, the sheet finds only false positives — the same blindness
    the HITL reviewer has, and recall is made of the other kind.
    """
    sheet = build_decision_sheet(GOLD, GOLD_DESCRIPTIONS, CANDIDATES)
    near = [d for d in sheet if d.kind == "near_miss"]
    assert near
    assert all(not d.matcher_says_match for d in near)
    # value_creation matched nothing, so its nearest candidates must be offered
    assert any(d.gold == "value_creation" for d in near)


def test_a_refused_pair_carries_the_reason_it_was_refused():
    """The judge should see why, not just that."""
    sheet = build_decision_sheet(GOLD, GOLD_DESCRIPTIONS, CANDIDATES)
    reversed_pair = [
        d for d in sheet
        if d.gold == "ltv_exceeds_cac" and d.candidate == "cac_exceeds_ltv"
    ]
    if reversed_pair:
        assert "argument order" in reversed_pair[0].veto_reason


def test_the_sheet_round_trips_through_yaml(tmp_path):
    sheet = build_decision_sheet(GOLD, GOLD_DESCRIPTIONS, CANDIDATES)
    path = write_decision_sheet(sheet, tmp_path / "sheet.yaml")
    assert read_decision_sheet(path) == sheet


# ── agreement ──

def _decision(matcher_match: bool, human: str) -> MatcherDecision:
    return MatcherDecision(
        gold="g", candidate="c", matcher_says_match=matcher_match, human=human
    )


def test_an_unjudged_sheet_reports_no_agreement_rather_than_perfect():
    """The defect this whole phase is about, in its own machinery.

    A sheet nobody filled in must not come back as agreement, for the same
    reason a validation that never ran must not score 1.0.
    """
    report = agreement(build_decision_sheet(GOLD, GOLD_DESCRIPTIONS, CANDIDATES))
    assert report.judged == 0
    assert report.observed_agreement is None
    assert report.cohens_kappa is None
    assert report.kappa_undefined_reason == "nothing was judged"
    assert report.semantic_encoder_is_indicated is None


def test_unjudged_rows_are_excluded_not_counted_as_agreement():
    report = agreement([
        _decision(True, AGREE),
        _decision(True, ""),
        _decision(False, ""),
    ])
    assert report.judged == 1
    assert report.unjudged == 2


def test_the_two_disagreement_classes_are_reported_separately():
    """They are not symmetric and only one of them argues for an encoder."""
    report = agreement([
        _decision(True, AGREE),       # both say match
        _decision(False, AGREE),      # both reject
        _decision(True, DISAGREE),    # matcher yes, human no — precision failure
        _decision(False, DISAGREE),   # matcher no, human yes — semantics needed
    ])
    assert report.both_match == 1
    assert report.both_reject == 1
    assert report.matcher_only == 1
    assert report.human_only == 1
    assert report.observed_agreement == 0.5


def test_a_semantic_encoder_is_indicated_only_by_human_yes_matcher_no():
    """A precision failure is not evidence for an encoder; the veto handles it."""
    precision_failures_only = agreement([
        _decision(True, DISAGREE), _decision(True, AGREE), _decision(False, AGREE)
    ])
    assert precision_failures_only.human_only == 0
    assert precision_failures_only.semantic_encoder_is_indicated is False

    missed_a_true_match = agreement([
        _decision(False, DISAGREE), _decision(True, AGREE), _decision(False, AGREE)
    ])
    assert missed_a_true_match.human_only == 1
    assert missed_a_true_match.semantic_encoder_is_indicated is True


def test_kappa_is_undefined_rather_than_one_when_chance_agreement_is_total():
    """Perfect agreement on a single answer is not a kappa of 1.0.

    If both raters say match to everything, chance agreement is already 1.0
    and kappa divides by zero. Reporting 1.0 there would be the strongest
    possible claim drawn from the weakest possible evidence.
    """
    report = agreement([_decision(True, AGREE), _decision(True, AGREE)])
    assert report.observed_agreement == 1.0
    assert report.cohens_kappa is None
    assert "chance agreement is 1.0" in report.kappa_undefined_reason


def test_kappa_is_computed_when_the_raters_vary():
    report = agreement([
        _decision(True, AGREE), _decision(True, AGREE),
        _decision(False, AGREE), _decision(False, AGREE),
        _decision(True, DISAGREE), _decision(False, DISAGREE),
    ])
    assert report.cohens_kappa is not None
    assert -1.0 <= report.cohens_kappa <= 1.0
    assert report.observed_agreement == pytest.approx(4 / 6)
