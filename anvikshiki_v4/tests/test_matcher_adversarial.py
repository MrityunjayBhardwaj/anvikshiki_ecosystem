# tests/test_matcher_adversarial.py
"""Adversarial regression suite for predicate matching.

The seven pairs below are the ones that defeated the old matcher, kept
verbatim from the harness audit so the fix is measured against the cases that
found the defect rather than against cases invented after it.

Three must match and four must not. The old matcher passed 3 of 7 — it matched
everything, which is the specific failure mode that looks like success:
precision and recall inflate together, and staring at the aggregate cannot
catch it. An extractor emitting the exact inverse of every gold predicate
scored precision 1.000, recall 1.000.

Two of the should-not pairs are not exotic. `economies_of_scale_real` and
`imagined_economies_of_scale` are both entries in the repo's own gold fixture,
authored deliberately as a contrast pair. `ltv_exceeds_cac` and
`cac_exceeds_ltv` score a perfect 1.000 under any bag-of-tokens measure,
because bag-of-tokens discards the relation the predicate exists to express.
"""

import pytest

from anvikshiki_v4.coverage import TOKEN_OVERLAP_MIN, SemanticCoverageAnalyzer
from anvikshiki_v4.schema import (
    CausalStatus,
    Confidence,
    DomainType,
    EpistemicStatus,
    KnowledgeStore,
    Vyapti,
)
from anvikshiki_v4.extraction_eval import (
    _best_match_score,
    _token_overlap,
    predicate_precision,
    predicate_recall,
)
from anvikshiki_v4.predicate_contrariness import match_veto
from anvikshiki_v4.t2_compiler_v4 import _are_contrary

# (a, b, should_match, why) — verbatim from the audit's table.
PAIRS = [
    ("ltv_exceeds_cac", "ltv_above_cac", True, "synonym"),
    ("short_payback_period", "payback_period_short", True, "reordered, no relation"),
    ("value_creation", "value_creation", True, "identical"),
    ("positive_unit_economics", "negative_unit_economics", False, "antonym"),
    ("value_creation", "not_value_creation", False, "negation"),
    ("high_retention_rate", "high_churn_rate", False, "domain inverse"),
    ("economies_of_scale_real", "imagined_economies_of_scale", False, "opposites"),
    ("ltv_exceeds_cac", "cac_exceeds_ltv", False, "operands reversed"),
]

SHOULD_MATCH = [(a, b, why) for a, b, m, why in PAIRS if m]
SHOULD_NOT_MATCH = [(a, b, why) for a, b, m, why in PAIRS if not m]


@pytest.mark.parametrize("a,b,why", SHOULD_MATCH)
def test_pairs_that_must_match(a, b, why):
    assert _best_match_score(a, {b}) > 0, f"{a} ~ {b} should match ({why})"


@pytest.mark.parametrize("a,b,why", SHOULD_NOT_MATCH)
def test_pairs_that_must_not_match(a, b, why):
    assert _best_match_score(a, {b}) == 0.0, f"{a} ~ {b} must not match ({why})"


@pytest.mark.parametrize("a,b,why", SHOULD_NOT_MATCH)
def test_the_refusal_is_a_veto_not_a_low_score(a, b, why):
    """These pairs are refused outright, not scored below a threshold.

    Recorded because it is the load-bearing property: `ltv_exceeds_cac` and
    `cac_exceeds_ltv` have identical token sets, so no threshold in (0, 1]
    separates them. Tuning cannot reach these cases and the veto has to.
    """
    assert match_veto(a, b), f"{a} ~ {b} passes the veto ({why})"


@pytest.mark.parametrize("a,b,why", SHOULD_NOT_MATCH)
def test_similarity_alone_would_still_admit_these(a, b, why):
    """The underlying similarity has not changed — the veto is what changed.

    If this ever fails, the token overlap was altered rather than gated, and
    the suite above would be passing for a different reason than intended.
    """
    if a == b:
        return
    assert _token_overlap(a, b) >= 0.4, (
        f"{a} ~ {b} no longer scores highly, so this pair is no longer "
        f"adversarial and the suite is weaker than it looks"
    )


def test_a_text_carrying_both_sides_of_a_pair_is_not_its_own_opposite():
    """Found by the gold fixture, which contains exactly this.

    "Customer retention rate is high (low churn)" holds high and low, and
    retention and churn. Checking pair membership across the two texts without
    first removing what they share made that description oppose itself, so it
    matched nothing — including an identical copy of itself. Opposition has to
    come from the tokens that distinguish the two.
    """
    both_sides = "Customer retention rate is high (low churn)"
    assert match_veto(both_sides, both_sides) is None
    assert _best_match_score("high_retention_rate", {"high_retention_rate"}) == 1.0

    # and the pair is still opposed when the tokens really do distinguish them
    assert match_veto("high_retention_rate", "high_churn_rate")


def test_an_inverted_extractor_no_longer_scores_perfectly():
    """The audit's decisive experiment, kept as a regression.

    An extractor emitting the exact logical inverse of every gold predicate
    scored precision 1.000, recall 1.000. That result is what voided every
    number the harness could produce.
    """
    gold = {
        "economies_of_scale_real",
        "ltv_exceeds_cac",
        "positive_unit_economics",
        "value_creation",
    }
    inverted = [
        "imagined_economies_of_scale",
        "cac_exceeds_ltv",
        "negative_unit_economics",
        "not_value_creation",
    ]

    assert predicate_precision(inverted, gold) == 0.0
    assert predicate_recall(inverted, gold) == 0.0


def test_a_correct_extractor_still_scores_perfectly():
    """The other half of the control: the veto must not suppress true matches.

    A fix that scored everything 0.0 would pass the test above and be useless.
    """
    gold = {"ltv_exceeds_cac", "positive_unit_economics", "value_creation"}
    correct = ["ltv_above_cac", "positive_unit_economics", "value_creation"]

    assert predicate_precision(correct, gold) == 1.0
    assert predicate_recall(correct, gold) == 1.0


def test_the_evaluator_and_the_compiler_now_agree():
    """They disagreed, and the engine's own semantics were on the losing side.

    `_are_contrary` treats X and not_X as contradictory — the trigger for every
    rebutting attack in the argumentation layer — while the evaluator scored
    the same pair 0.667 and called it a match.
    """
    for a, b, should_match, _ in PAIRS:
        if _are_contrary(a, b):
            assert not should_match
            assert _best_match_score(a, {b}) == 0.0, (
                f"the compiler calls {a} and {b} contradictory while the "
                f"evaluator matches them"
            )


# ── coverage routing, which runs in production ──

def _StubKS(predicates):
    """A real `KnowledgeStore`, built from real `Vyapti` objects.

    This was a pair of hand-built stand-ins carrying the four attributes the
    analyzer happened to read. #47 filed that shape and predicted exactly what
    followed: the analyzer learned to read `scope_conditions`, and a test about
    token overlap and negation broke with an `AttributeError` about a field it
    has no opinion on. A hand-built stub is a second definition of the model
    that drifts silently and reports the drift somewhere unrelated.

    The real objects are cheap, carry their own defaults, and cannot drift.
    """
    return KnowledgeStore(
        domain_type=DomainType.CRAFT,
        vyaptis={
            f"V{i:02d}": Vyapti(
                id=f"V{i:02d}", name=f"V{i:02d}",
                statement=f"{p} implies some_consequent",
                causal_status=CausalStatus.EMPIRICAL,
                confidence=Confidence(existence=0.9, formulation=0.9,
                                      evidence="theoretical"),
                epistemic_status=EpistemicStatus.ESTABLISHED,
                antecedents=[p], consequent="some_consequent",
            )
            for i, p in enumerate(predicates)
        },
    )


def test_coverage_does_not_match_a_predicate_to_its_own_negation():
    """This one runs in production, and mis-routing picks the wrong vyāpti.

    `positive_unit_economics` and `negative_unit_economics` score 0.5 against
    this layer's 0.4 threshold, so coverage reported a match and the engine
    reasoned with a rule asserting the opposite of the query.
    """
    analyzer = SemanticCoverageAnalyzer(_StubKS(["positive_unit_economics"]))

    closest, score = analyzer._find_closest_predicate("negative_unit_economics")
    assert closest == "", f"matched {closest!r} at {score}"

    result = analyzer.analyze(["negative_unit_economics"])
    assert result.matched_predicates == []
    assert result.decision == "DECLINE"


def test_coverage_still_matches_a_genuine_near_miss():
    """The veto must not turn coverage into a permanent DECLINE."""
    analyzer = SemanticCoverageAnalyzer(_StubKS(["positive_unit_economics"]))

    closest, score = analyzer._find_closest_predicate("positive_unit_metrics")
    assert closest == "positive_unit_economics"
    assert score >= TOKEN_OVERLAP_MIN
