# tests/test_entity_consensus_and_divergence.py
"""One query naming a subject two ways, handled differently at two sites.

Both sites concern the same fact — nothing normalises the entity binding — and
they need opposite treatment, which is why the normaliser reports rather than
repairs and each caller decides what to do with the answer.

The ensemble (`_consensus`)
───────────────────────────
N samplings of ONE query. Two spellings there cannot be two subjects, so
agreement is safe to infer. Measured live before the fix, on
"The firm has superior information — does it therefore have pricing power?":

    4 of 5 members: superior_information(firm)
    1 of 5:         superior_information(the_firm), pricing_power(the_firm)

    set.intersection over full strings  →  0 / 3  →  confidence 0.00
    engine's answer: "Grounding confidence too low — requesting clarification"

Four of five agreed exactly and the engine told the user their question was
unclear. Two defects compounded: votes keyed on the raw entity, and unanimity
rather than majority — intersection over all N lets one rollout at temperature
0.7 delete what every other member found.

The engine boundary (`_entity_divergence`)
──────────────────────────────────────────
Here the predicates are the finished grounding of one query, and two spellings
may genuinely be two companies. So this one refuses to proceed and asks, rather
than resolving: the binding decides chaining, rebuttal and scope, and `acme` /
`Acme` silently partitions the framework so V08 stops chaining and the engine
reports no conclusion with no reason given. A missed inference reads as "no
conclusion follows".

It returns a clarification rather than a warning because grounding warnings are
computed and read by nothing on the query path — a loud failure routed through
a dead channel is not loud.

Neither site rewrites a binding. `predicate_entity` still returns exactly what
was written.
"""

import pytest

from anvikshiki_v4.grounding import (
    CONSENSUS_THRESHOLD,
    GroundingPipeline,
    _consensus,
)
from anvikshiki_v4.predicate_contrariness import (
    entity_divergence,
    normalize_entity,
    predicate_entity,
)
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

KB_PATH = "anvikshiki_v4/data/business_expert.yaml"

# The five member outputs captured from the live run, verbatim.
Q2_LIVE = [
    {"superior_information(firm)"},
    {"superior_information(the_firm)", "pricing_power(the_firm)"},
    {"superior_information(firm)"},
    {"superior_information(firm)"},
    {"superior_information(firm)"},
]


@pytest.fixture(scope="module")
def checker():
    gp = GroundingPipeline.__new__(GroundingPipeline)
    gp.ks = load_knowledge_store(KB_PATH)
    return gp


# ── the normaliser ───────────────────────────────────────────

@pytest.mark.parametrize("spelling", ["acme", "Acme", "( acme )", "acme_corp",
                                      "ACME Inc", " acme "])
def test_the_four_spellings_of_one_company_normalise_alike(spelling):
    assert normalize_entity(spelling) == "acme"


def test_two_real_companies_do_not_normalise_alike():
    """The whole objection to canonicalising. If this ever fails, the
    normaliser has started merging entities rather than comparing them."""
    assert normalize_entity("acme") != normalize_entity("globex")


def test_a_bare_predicate_normalises_to_none():
    """Absence of a binding is a binding, not a spelling of one."""
    assert normalize_entity(None) is None


def test_normalising_does_not_rewrite_what_was_written():
    """The load-bearing property: this is a comparison, not a repair."""
    assert predicate_entity("value_creation(Acme)") == "Acme"


def test_entity_divergence_reports_only_genuine_collisions():
    assert entity_divergence(["a(acme)", "b(globex)"]) == {}
    assert entity_divergence(["a(firm)", "b(the_firm)"]) == {
        "firm": {"firm", "the_firm"}
    }


# ── the ensemble ─────────────────────────────────────────────

def test_the_live_four_of_five_agreement_now_survives():
    """The headline, replayed on the exact captured output."""
    consensus, disputed = _consensus(Q2_LIVE)
    assert "superior_information(firm)" in consensus
    confidence = len(consensus) / max(len(consensus) + len(disputed), 1)
    assert confidence >= 0.4, "would still trigger a clarification request"


def test_the_old_algorithm_would_have_failed_this():
    """The mutation check, asserting the mutation applies.

    Replays `set.intersection` over the same input. If it does not produce a
    different answer, the law above proves nothing.
    """
    old = set.intersection(*Q2_LIVE)
    assert old == set(), (
        "the mutation did not apply — intersection must be empty here, or "
        "the consensus law is vacuous"
    )
    new, _ = _consensus(Q2_LIVE)
    assert new != old


def test_one_outlier_cannot_delete_a_predicate_everyone_else_produced():
    """Unanimity vs majority, isolated from the spelling question — every
    member here writes the same entity."""
    sets = [{"p(acme)"}] * 4 + [{"q(acme)"}]
    consensus, _ = _consensus(sets)
    assert "p(acme)" in consensus


def test_a_minority_predicate_stays_disputed():
    """The threshold has to exclude something, or it is not a threshold."""
    sets = [{"p(acme)"}] * 4 + [{"q(acme)"}]
    consensus, disputed = _consensus(sets)
    assert "q(acme)" in disputed and "q(acme)" not in consensus


def test_votes_are_pooled_across_spellings_of_one_subject():
    """Three members writing the subject three ways still agree on the
    finding; keyed on the raw string they would each be a minority of one."""
    sets = [{"p(firm)"}, {"p(the_firm)"}, {"p(Firm)"}]
    consensus, _ = _consensus(sets)
    assert len(consensus) == 1
    assert normalize_entity(predicate_entity(next(iter(consensus)))) == "firm"


def test_the_surviving_spelling_is_the_most_voted_one():
    sets = [{"p(firm)"}, {"p(firm)"}, {"p(the_firm)"}]
    consensus, _ = _consensus(sets)
    assert consensus == {"p(firm)"}


def test_consensus_is_deterministic_across_runs():
    """An ensemble that grounds differently on reruns cannot be compared
    against itself, and set iteration order is not stable across processes."""
    sets = [{"p(firm)"}, {"p(the_firm)"}]
    assert len({frozenset(_consensus(sets)[0]) for _ in range(20)}) == 1


def test_two_real_companies_are_counted_separately():
    """The ensemble normalises spellings; it must not merge subjects."""
    sets = [{"p(acme)", "p(globex)"}] * 3
    consensus, _ = _consensus(sets)
    assert consensus == {"p(acme)", "p(globex)"}


def test_unanimous_agreement_still_reaches_consensus():
    sets = [{"p(acme)"}] * 5
    assert _consensus(sets)[0] == {"p(acme)"}


def test_an_empty_ensemble_yields_nothing_rather_than_raising():
    assert _consensus([]) == (set(), set())


def test_the_threshold_is_a_majority():
    assert 0 < CONSENSUS_THRESHOLD < 1


# ── the engine boundary ──────────────────────────────────────

def test_two_spellings_of_one_subject_stop_the_query(checker):
    result = checker._entity_divergence(
        ["positive_unit_economics(acme)", "binding_constraint_identified(Acme)"]
    )
    assert result is not None and result.clarification_needed


def test_the_refusal_names_both_spellings(checker):
    """"Something was ambiguous" is not answerable; the two spellings are."""
    result = checker._entity_divergence(
        ["positive_unit_economics(acme)", "value_creation(acme_corp)"]
    )
    assert "acme_corp" in result.warnings[0] and "acme" in result.warnings[0]


def test_two_real_companies_proceed(checker):
    """The comparative query is what this engine is for. Q1 produced exactly
    this shape live and must not start asking for clarification."""
    assert checker._entity_divergence(
        ["positive_unit_economics(acme)", "not_positive_unit_economics(globex)"]
    ) is None


def test_a_single_entity_proceeds(checker):
    assert checker._entity_divergence(["positive_unit_economics(acme)"]) is None


def test_bare_predicates_proceed(checker):
    """Every knowledge base in the tree writes rules as bare names, and two
    bare predicates matching is the case that has always worked."""
    assert checker._entity_divergence(
        ["positive_unit_economics", "value_creation"]
    ) is None


def test_the_refusal_does_not_rewrite_the_predicates(checker):
    """Fail loudly, normalise nothing — the returned predicates are what was
    grounded, not a repaired version."""
    preds = ["positive_unit_economics(acme)", "value_creation(Acme)"]
    result = checker._entity_divergence(preds)
    assert sorted(result.predicates) == sorted(preds)


def test_the_refusal_is_not_routed_through_the_dead_warning_channel(checker):
    """Grounding warnings are computed and read by nothing on the query path,
    so a divergence reported only there would be invisible. The clarification
    flag is the path the engine actually renders."""
    result = checker._entity_divergence(
        ["positive_unit_economics(acme)", "value_creation(Acme)"]
    )
    assert result.clarification_needed is True
