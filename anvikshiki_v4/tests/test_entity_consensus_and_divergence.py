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

from anvikshiki_v4.schema import DecayRisk
from anvikshiki_v4.grounding import (
    CONSENSUS_THRESHOLD,
    GroundingPipeline,
    _consensus,
)
from anvikshiki_v4.predicate_contrariness import (
    entity_divergence,
    normalize_entity,
    predicate_entity,
    predicate_name,
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


# ── a vote belongs to a member, not to an occurrence ─────────
#
# Every majority law above gives each member exactly one spelling, so the case
# where ONE member names the subject two ways inside its own predicate list is
# never constructed — the laws pass and the defect is live. The blind spot was
# in the test domain, not in the reading of it.

def _by_occurrence(pred_sets, threshold=CONSENSUS_THRESHOLD):
    """The pooling as first written — votes summed per occurrence.

    Kept as the mutation, so the law below cannot pass vacuously.
    """
    votes: dict = {}
    for pred_set in pred_sets:
        for pred in pred_set:
            key = (predicate_name(pred), normalize_entity(predicate_entity(pred)))
            votes.setdefault(key, {})
            votes[key][pred] = votes[key].get(pred, 0) + 1
    needed = len(pred_sets) * threshold
    consensus = set()
    for spellings in votes.values():
        if sum(spellings.values()) > needed:
            consensus.add(min(sorted(spellings), key=lambda p: (-spellings[p], p)))
    return consensus


ONE_MEMBER_TWO_SPELLINGS = [
    {"superior_information(firm)", "superior_information(the_firm)"},
    {"pricing_power(acme)"},
    {"pricing_power(acme)"},
]


def test_one_member_naming_a_subject_twice_cannot_reach_consensus_alone():
    """Pooling spellings must not let a minority of one manufacture a
    majority — the mirror image of the unanimity defect this fix removes."""
    consensus, disputed = _consensus(ONE_MEMBER_TWO_SPELLINGS)
    assert not any(p.startswith("superior_information") for p in consensus)
    assert "superior_information(firm)" in disputed


def test_counting_occurrences_instead_of_members_would_promote_it():
    """The mutation check, asserting the mutation applies. If per-occurrence
    counting does NOT promote here, the law above proves nothing."""
    promoted = _by_occurrence(ONE_MEMBER_TWO_SPELLINGS)
    assert any(p.startswith("superior_information") for p in promoted), (
        "the mutation did not apply — per-occurrence counting must promote "
        "the single member here, or the law above is vacuous"
    )
    consensus, _ = _consensus(ONE_MEMBER_TWO_SPELLINGS)
    assert not any(p.startswith("superior_information") for p in consensus)


def test_a_member_repeating_itself_does_not_inflate_confidence():
    """Confidence is consensus / (consensus + disputed), so a manufactured
    majority moves a predicate from the denominator into the numerator."""
    consensus, disputed = _consensus(ONE_MEMBER_TWO_SPELLINGS)
    confidence = len(consensus) / max(len(consensus) + len(disputed), 1)
    assert confidence < 0.5, f"one member of three should not carry it: {confidence}"


def test_pooling_still_rescues_a_real_majority():
    """The fix above must not undo the fix it guards. Three DIFFERENT members
    writing the subject three ways is still agreement."""
    consensus, _ = _consensus([{"p(firm)"}, {"p(the_firm)"}, {"p(Firm)"}])
    assert len(consensus) == 1


# ── the refusal is reached from the query path ───────────────
#
# Every divergence law above calls `_entity_divergence` directly, so they prove
# the comparison is right and prove nothing about whether the query path
# reaches it. Delete either call site and they all stay green.

class _StubGrounder:
    """Returns fixed predicates, so the path is exercised with no LM call."""

    def __init__(self, predicates):
        self.predicates = predicates

    def __call__(self, **kwargs):
        import types
        return types.SimpleNamespace(
            predicates=list(self.predicates), relevant_vyaptis=[]
        )


DIVERGENT = ["positive_unit_economics(acme)", "value_creation(Acme)"]


def _piped(predicates):
    gp = GroundingPipeline.__new__(GroundingPipeline)
    gp.ks = load_knowledge_store(KB_PATH)
    gp.grounder = _StubGrounder(predicates)
    gp.engine = None
    return gp


def test_the_minimal_path_reaches_the_refusal():
    result = _piped(DIVERGENT)._forward_minimal("q", "snippet")
    assert result.clarification_needed is True


def test_the_ensemble_path_reaches_the_refusal():
    result = _piped(DIVERGENT)._forward_ensemble("q", "snippet", n=3,
                                                 use_solver=False)
    assert result.clarification_needed is True


@pytest.mark.parametrize("path", ["_forward_minimal", "_forward_ensemble"])
def test_an_unambiguous_grounding_still_proceeds_on_both_paths(path):
    """The guard must not be reached by everything — a check that always
    fires is not a check."""
    gp = _piped(["positive_unit_economics(acme)",
                 "not_positive_unit_economics(globex)"])
    args = ("q", "snippet") if path == "_forward_minimal" else \
           ("q", "snippet", 3, False)
    result = getattr(gp, path)(*args)
    assert result.clarification_needed is False


def test_every_non_clarifying_return_path_is_guarded():
    """A source-level law with the path count asserted, so it cannot pass by
    matching nothing. If a third return path is added without the guard, the
    two behavioural laws above will not see it."""
    import ast
    import inspect

    from anvikshiki_v4 import grounding as grounding_module

    tree = ast.parse(inspect.getsource(grounding_module))
    cls = next(n for n in ast.walk(tree)
               if isinstance(n, ast.ClassDef) and n.name == "GroundingPipeline")

    producers = [m for m in cls.body
                 if isinstance(m, ast.FunctionDef)
                 and m.name in ("_forward_minimal", "_forward_ensemble")]
    assert len(producers) == 2, (
        f"expected 2 grounding paths, found {len(producers)} — the scan is "
        "measuring something other than what it was written for"
    )
    for method in producers:
        calls = [n for n in ast.walk(method)
                 if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "_entity_divergence"]
        assert calls, f"{method.name} returns a grounding without the guard"


# ── the sibling field, which kept unanimity ──────────────────
#
# `relevant_vyaptis` sat one line below the predicate consensus and was not
# touched when that line gave up `set.intersection`, because an issue written
# from one field names one field. It cost nothing at the time: the ids reached
# only the decay check, and the decay check's output reached nothing. Now that
# the advisory channel is live, one member of five omitting an id deletes a
# finding four members produced.

class _PerMemberGrounder:
    """A different vyāpti list per ensemble member, predicates held fixed.

    Fixed predicates because this is a law about the OTHER field: letting the
    predicates vary too would make a failure ambiguous between the two.
    """

    def __init__(self, vyapti_sets):
        self._vyapti_sets = list(vyapti_sets)
        self.calls = 0

    def __call__(self, **kwargs):
        import types
        relevant = self._vyapti_sets[self.calls % len(self._vyapti_sets)]
        self.calls += 1
        return types.SimpleNamespace(
            predicates=["superior_information(acme)"],
            relevant_vyaptis=list(relevant),
        )


FOUR_OF_FIVE = [["V01"], ["V01"], ["V01"], ["V01"], []]


def _piped_vyaptis(vyapti_sets):
    gp = GroundingPipeline.__new__(GroundingPipeline)
    gp.ks = load_knowledge_store(KB_PATH)
    gp.ks.vyaptis["V01"].decay_risk = DecayRisk.CRITICAL
    gp.ks.vyaptis["V01"].decay_condition = "regime change"
    gp.ks.vyaptis["V01"].last_verified = None
    gp.grounder = _PerMemberGrounder(vyapti_sets)
    gp.engine = None
    return gp


def test_four_of_five_naming_a_vyapti_reaches_consensus():
    result = _piped_vyaptis(FOUR_OF_FIVE)._forward_ensemble(
        "q", "snippet", n=5, use_solver=False
    )
    assert [a.vyapti_id for a in result.advisories] == ["V01"], (
        "the decay check is the only reader of these ids, and it can only "
        "report on an id that survived the vote"
    )


def test_unanimity_would_have_deleted_it():
    """The counterfactual, stated as its own law so the fix is not merely
    asserted to be a fix. Same five members, the rule the line used to use."""
    assert set.intersection(*[set(s) for s in FOUR_OF_FIVE]) == set()


def test_a_genuine_minority_is_still_dropped():
    """Majority, not "anyone said it". One member out of five naming a vyāpti
    the others did not is exactly the divergent rollout the threshold exists
    to discard."""
    result = _piped_vyaptis(
        [["V01"], [], [], [], []]
    )._forward_ensemble("q", "snippet", n=5, use_solver=False)
    assert result.advisories == []
