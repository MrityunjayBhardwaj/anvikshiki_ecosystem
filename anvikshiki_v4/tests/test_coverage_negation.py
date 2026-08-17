# anvikshiki_v4/tests/test_coverage_negation.py
"""Coverage's policy on negation, and the label that stops overstating it.

Two questions live here, and they were deliberately separated when the matcher
was fixed:

1. *Should `not_X` count as covered when the base knows only `X`?* Yes. This
   module asks whether the knowledge base has reasoning machinery for a
   concept, and `not_X` against a rule about `X` is what raises a rebutting
   attack — the engine's most informative behaviour. Declining would refuse
   the queries it handles best. Decided, not inherited from a comment.

2. *Was reporting it as `"exact"` wrong?* Yes, regardless of (1). The strings
   differ, and they differ on the token that reverses the meaning, so the
   trace claimed the query was found verbatim in the vocabulary.

The tension with the token layer is asserted here too, because it reads like
an inconsistency and is not one: layer 3 refuses two unrelated predicates that
collide on tokens, layer 1 accepts a deliberate polarity inversion of a
predicate the base holds.
"""

import pytest

from anvikshiki_v4.coverage import SemanticCoverageAnalyzer
from anvikshiki_v4.schema import (
    CausalStatus,
    Confidence,
    DomainType,
    EpistemicStatus,
    KnowledgeStore,
    Vyapti,
)


def _vyapti(vid, antecedents, consequent):
    return Vyapti(
        id=vid, name=vid, statement=f"{antecedents} implies {consequent}",
        causal_status=CausalStatus.EMPIRICAL,
        confidence=Confidence(
            existence=0.9, formulation=0.9, evidence="theoretical"
        ),
        epistemic_status=EpistemicStatus.ESTABLISHED,
        antecedents=antecedents, consequent=consequent,
    )


@pytest.fixture
def analyzer():
    """A base that knows value_creation and the two unit-economics predicates.

    `positive_unit_economics` and `negative_unit_economics` are both in the
    vocabulary on purpose — they are the pair that collides on three tokens
    out of four and is the reason the token layer has a veto.
    """
    ks = KnowledgeStore(
        domain_type=DomainType.CRAFT,
        vyaptis={
            v.id: v for v in (
                _vyapti("V01", ["positive_unit_economics"], "value_creation"),
                _vyapti("V02", ["negative_unit_economics"], "value_erosion"),
            )
        },
        synonym_table={"customer_value_generation": "value_creation"},
    )
    return SemanticCoverageAnalyzer(ks)


# ── The label ────────────────────────────────────────────────

def test_a_negated_query_is_not_reported_as_an_exact_match(analyzer):
    """The observed case from the issue.

    Before: match_details = {"not_value_creation": "exact"}. The vocabulary
    does not contain that string.
    """
    result = analyzer.analyze(["not_value_creation"])
    assert result.match_details["not_value_creation"] == "negated_exact"
    assert "exact" not in result.match_details.values()


def test_an_affirmative_query_is_still_reported_as_exact(analyzer):
    """The label must change only for the case that was being misreported."""
    result = analyzer.analyze(["value_creation"])
    assert result.match_details["value_creation"] == "exact"


def test_the_label_says_which_layer_matched_as_well_as_the_polarity(analyzer):
    """Two facts, so two parts.

    A bare "negated" would answer the polarity question and lose which layer
    fired — and knowing a match came from token overlap rather than the
    vocabulary is the difference between a routing decision to trust and one
    to look at.
    """
    exact = analyzer.analyze(["not_value_creation"])
    synonym = analyzer.analyze(["not_customer_value_generation"])

    assert exact.match_details["not_value_creation"] == "negated_exact"
    assert (synonym.match_details["not_customer_value_generation"]
            == "negated_synonym")


def test_the_token_layer_gets_a_negated_label_too(analyzer):
    """All three layers are reachable in negated form, so none is dead code.

    A label the code can produce but no input can reach is a claim about
    behaviour nothing verifies.
    """
    from anvikshiki_v4.schema import DomainType, KnowledgeStore

    ks = KnowledgeStore(
        domain_type=DomainType.CRAFT,
        vyaptis={"V01": _vyapti(
            "V01", ["binding_constraint_identified"], "value_creation"
        )},
    )
    fuzzy = SemanticCoverageAnalyzer(ks)
    result = fuzzy.analyze(["not_binding_constraint_found"])
    assert (result.match_details["not_binding_constraint_found"]
            == "negated_token")
    assert result.relevant_vyaptis == ["V01"]


def test_a_negated_query_with_an_entity_argument_is_labelled_too(analyzer):
    """The entity is stripped before the polarity is read, not after."""
    result = analyzer.analyze(["not_value_creation(acme_corp)"])
    assert (result.match_details["not_value_creation(acme_corp)"]
            == "negated_exact")


# ── The policy ───────────────────────────────────────────────

def test_a_negated_query_still_counts_as_covered(analyzer):
    """Decision (1), asserted so a later change has to argue with it.

    The base has machinery for this concept. Routing the query to the vyāptis
    that mention it is what lets the argumentation layer raise a rebutting
    attack, which is the outcome worth having.
    """
    result = analyzer.analyze(["not_value_creation"])
    assert result.coverage_ratio == 1.0
    assert result.decision == "FULL"
    assert result.matched_predicates == ["not_value_creation"]
    assert result.unmatched_predicates == []


def test_a_negated_query_routes_to_the_same_vyaptis_as_its_affirmative(
    analyzer,
):
    """Coverage is about vocabulary, so the relevant rules are the same ones."""
    negated = analyzer.analyze(["not_value_creation"])
    affirmative = analyzer.analyze(["value_creation"])
    assert negated.relevant_vyaptis == affirmative.relevant_vyaptis == ["V01"]


def test_the_ratio_is_unchanged_by_the_relabelling(analyzer):
    """The label was the bug; the routing was the policy. Only one moved."""
    mixed = analyzer.analyze(
        ["value_creation", "not_value_creation", "something_unknown_entirely"]
    )
    assert mixed.coverage_ratio == pytest.approx(2 / 3)
    assert mixed.unmatched_predicates == ["something_unknown_entirely"]


# ── Double negation ──────────────────────────────────────────

def test_a_doubly_negated_query_is_the_affirmative(analyzer):
    """not_not_X is X, so it matches exactly and is not labelled negated.

    A single-shot prefix strip left `not_X`, which is in no vocabulary, so the
    query fell past layers 1 and 2 to token overlap — scoring a fuzzy match on
    a predicate it is literally equivalent to.
    """
    result = analyzer.analyze(["not_not_value_creation"])
    assert result.match_details["not_not_value_creation"] == "exact"
    assert result.relevant_vyaptis == ["V01"]


def test_a_triply_negated_query_is_negated(analyzer):
    result = analyzer.analyze(["not_not_not_value_creation"])
    assert (result.match_details["not_not_not_value_creation"]
            == "negated_exact")


# ── The tension with the token layer, asserted ───────────────

def test_the_token_layer_still_refuses_an_accidental_polarity_collision(
    analyzer,
):
    """Layer 3 must keep vetoing, and this is the pair it was written for.

    `positive_unit_economics` and `negative_unit_economics` share three tokens
    of four and score 0.5 against a 0.4 threshold. They are different
    predicates that collide, not one predicate negated — matching them would
    route a query to a rule asserting the opposite of what was asked, with
    nothing in the trace to say so.
    """
    closest, score = analyzer._find_closest_predicate(
        "positive_unit_economics"
    )
    assert closest != "negative_unit_economics"

    # Confirm the collision is real, so the veto is not being credited for a
    # match that would have failed the threshold anyway.
    tokens_a = set("positive_unit_economics".split("_"))
    tokens_b = set("negative_unit_economics".split("_"))
    jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
    assert jaccard >= 0.4


def test_the_two_layers_disagree_deliberately_and_both_are_reachable():
    """The whole point of writing the policy down.

    Layer 1 accepts a negated predicate the base holds; layer 3 refuses an
    unrelated predicate that merely collides on polarity tokens. Both are
    exercised against one base, so neither can be "fixed" into the other
    without a test failing and pointing at the docstring.

    The base here holds only the *positive* unit-economics predicate, so the
    negative-polarity query has nothing to match but its own opposite — which
    is the situation the veto exists for.
    """
    ks = KnowledgeStore(
        domain_type=DomainType.CRAFT,
        vyaptis={"V01": _vyapti(
            "V01", ["positive_unit_economics"], "value_creation"
        )},
    )
    one_sided = SemanticCoverageAnalyzer(ks)

    # Layer 1 accepts the negation of a predicate the base holds.
    accepted = one_sided.analyze(["not_value_creation"])
    assert accepted.decision == "FULL"
    assert accepted.match_details["not_value_creation"] == "negated_exact"

    # Layer 3 refuses a different predicate whose only near neighbour
    # disagrees with it on positive/negative.
    refused = one_sided.analyze(["negative_unit_economics_trend"])
    assert refused.unmatched_predicates == ["negative_unit_economics_trend"]
    assert refused.decision == "DECLINE"


# ── The KB can hold a negated predicate literally (#53) ──────
#
# `not_value_creation` is not hypothetical: it is V11's consequent in
# `anvikshiki_v4/data/business_expert.yaml` — "The Growth Trap", where
# organizational growth plus coordination overhead concludes the *absence* of
# value creation. Stripping the prefix before the lookup routed a query for
# that predicate to the rules producing its affirmative, and never surfaced
# the rule whose conclusion it is.

@pytest.fixture
def two_sided():
    """A base holding both an affirmative predicate and its literal negation.

    Modelled on the shipped knowledge base rather than invented, because this
    is the shape that exposed the defect and a fixture without a literal
    `not_` predicate cannot reach it — the same blind spot as a generated
    domain that never produces the branch under test.
    """
    ks = KnowledgeStore(
        domain_type=DomainType.CRAFT,
        vyaptis={
            v.id: v for v in (
                _vyapti("V01", ["positive_unit_economics"], "value_creation"),
                _vyapti(
                    "V11",
                    ["organizational_growth", "coordination_overhead"],
                    "not_value_creation",
                ),
            )
        },
    )
    return SemanticCoverageAnalyzer(ks)


def test_a_literal_negated_predicate_matches_itself_not_its_affirmative(
    two_sided,
):
    """The defect, as a routing assertion.

    Before: relevant_vyaptis was ["V01"] — the rule that produces value
    creation — for a query asking about its absence, while V11 sat unused in
    the vocabulary.
    """
    result = two_sided.analyze(["not_value_creation"])
    assert result.relevant_vyaptis == ["V11"]
    # And it really is exact — the string is in the vocabulary verbatim, so
    # labelling it negated_* would understate the match in the other direction.
    assert result.match_details["not_value_creation"] == "exact"


def test_the_affirmative_still_routes_to_its_own_rules(two_sided):
    result = two_sided.analyze(["value_creation"])
    assert result.relevant_vyaptis == ["V01"]
    assert result.match_details["value_creation"] == "exact"


def test_double_negation_routes_to_the_affirmative_not_to_the_negation(
    two_sided,
):
    """`not_not_X` is `X`, and this is where the single-shot strip did harm.

    One strip left `not_value_creation`, which in this base is a real and
    *opposite* predicate — so a query about value creation was routed to the
    rule concluding its absence and reported as an exact match.
    """
    result = two_sided.analyze(["not_not_value_creation"])
    assert result.relevant_vyaptis == ["V01"]
    assert result.match_details["not_not_value_creation"] == "exact"


def test_negation_depth_alternates_correctly(two_sided):
    """Odd depths are the negation, even depths the affirmative."""
    expected = {
        "value_creation": ["V01"],
        "not_value_creation": ["V11"],
        "not_not_value_creation": ["V01"],
        "not_not_not_value_creation": ["V11"],
        "not_not_not_not_value_creation": ["V01"],
    }
    wrong = {
        query: two_sided.analyze([query]).relevant_vyaptis
        for query, vyaptis in expected.items()
        if two_sided.analyze([query]).relevant_vyaptis != vyaptis
    }
    assert not wrong, f"routed to the wrong rules: {wrong}"


def test_the_fallback_only_applies_when_the_negation_is_not_in_the_vocabulary(
    two_sided,
):
    """The two behaviours are ordered, and both are reachable in one base.

    `not_value_creation` is held literally, so it matches itself exactly.
    `not_positive_unit_economics` is not, so it falls back to the affirmative
    and is labelled for it.
    """
    literal = two_sided.analyze(["not_value_creation"])
    fallback = two_sided.analyze(["not_positive_unit_economics"])

    assert literal.match_details["not_value_creation"] == "exact"
    assert (fallback.match_details["not_positive_unit_economics"]
            == "negated_exact")
    assert fallback.relevant_vyaptis == ["V01"]


def test_an_exact_match_on_either_form_beats_token_overlap(two_sided):
    """Layer-major order, asserted.

    Running all three layers on the as-written form before trying the
    affirmative would let a fuzzy token match on `not_X` outrank an exact
    match on `X`. The loop is layer-major to prevent exactly that.
    """
    # Not in the vocabulary in either form; its affirmative is, exactly.
    result = two_sided.analyze(["not_positive_unit_economics"])
    assert result.match_details["not_positive_unit_economics"].endswith(
        "exact"
    ), "an exact match on the affirmative lost to a fuzzier layer"


def test_the_real_knowledge_base_exercises_this():
    """Guard against the fixture drifting away from the shipped data.

    This defect was found on `business_expert.yaml`, not on a fixture. If that
    base ever stops holding a literal negated predicate, the tests above go on
    passing while nothing real is covered by them.
    """
    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

    ks = load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")
    literal_negations = {
        pred
        for v in ks.vyaptis.values()
        for pred in list(v.antecedents) + [v.consequent]
        if pred.startswith("not_")
    }
    assert literal_negations, (
        "the shipped knowledge base no longer holds a literal negated "
        "predicate, so the fixtures above no longer model real data"
    )

    analyzer = SemanticCoverageAnalyzer(ks)
    for pred in sorted(literal_negations):
        result = analyzer.analyze([pred])
        assert result.match_details[pred] == "exact", pred
        owners = [
            vid for vid, v in ks.vyaptis.items()
            if pred in list(v.antecedents) + [v.consequent]
        ]
        assert result.relevant_vyaptis == sorted(owners), pred
