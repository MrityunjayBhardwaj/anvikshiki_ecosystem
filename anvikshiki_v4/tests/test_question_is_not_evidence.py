# tests/test_question_is_not_evidence.py
"""What the question supposes is context, never evidence (#195, #196).

Every fact `compile_t2` receives was extracted from the question; on the query
path there is no other input. They used to enter as PRATYAKSA — perception,
the strongest evidence kind — at ESTABLISHED, strict, so:

  * "Why does the Varenna Accord allocate meltwater by population?" came back
    with `binding_constraint_identified(varenna_accord)` established, a false
    premise vouched for by the engine (#195);
  * "Is growth alone enough to make a business viable?" came back with
    `organizational_growth(business)` as perceived and established, bound
    "asserted", although the question was its only source (#196);
  * a supposition the knowledge base contradicts won every conflict, because
    a strict, perceived premise cannot lose one.

The predicates below are the ones the live grounder produced for those two
questions on 2026-10-31 (openrouter/z-ai/glm-5.2, shipped business base), so
these are replays of the reported cases, not fixtures shaped to the fix.

What follows *from* a supposition keeps the grade the reasoning earns: a
supposition is the condition a derivation holds under, not a link in it. The
laws that pin that are in test_algebra_laws.py and test_origin_ceiling.py;
the last test here pins it on the reported case.
"""

import dspy
import pytest

from anvikshiki_v4.engine_v4 import AnvikshikiEngineV4
from anvikshiki_v4.grounding import GroundingResult
from anvikshiki_v4.schema_v4 import EpistemicStatus, Label, PramanaType
from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store

BUSINESS = "anvikshiki_v4/data/business_expert.yaml"

VARENNA = (
    "binding_constraint_identified(varenna_accord)",
    "resource_allocation_effective(varenna_accord)",
)
GROWTH = ("organizational_growth(business)",)


@pytest.fixture(scope="module")
def ks():
    return load_knowledge_store(BUSINESS)


def _af(ks, *predicates):
    af = compile_t2(ks, [{"predicate": p, "confidence": 1.0} for p in predicates])
    af.compute_grounded()
    return af


def _premise(af, conclusion):
    (arg,) = [a for a in af.arguments.values()
              if a.top_rule is None and a.conclusion == conclusion]
    return arg


def _label(af, conclusion):
    return {af.labels[a.id] for a in af.arguments.values()
            if a.conclusion == conclusion}


# ── the question's facts themselves ────────────────────────────

@pytest.mark.parametrize("predicates", [VARENNA, GROWTH], ids=["varenna", "growth"])
def test_a_fact_from_the_question_is_not_perceived(ks, predicates):
    """#196 as reported: the question is testimony, never perception."""
    af = _af(ks, *predicates)
    for p in predicates:
        assert _premise(af, p).tag.pramana_type is PramanaType.SABDA, p


def test_a_premise_the_question_alone_supplies_is_not_established(ks):
    """#195's first fact. Nothing in the base concludes
    `binding_constraint_identified`, so the question is its only support, and
    the status the engine reports for it must say so."""
    af = _af(ks, *VARENNA)
    status, tag, _ = af.get_epistemic_status(VARENNA[0])
    assert status is EpistemicStatus.PROVISIONAL
    assert tag.pramana_type is not PramanaType.PRATYAKSA


def test_the_growth_premise_is_not_established(ks):
    """#196's case: `organizational_growth(business)` came back established."""
    af = _af(ks, *GROWTH)
    status, _, _ = af.get_epistemic_status(GROWTH[0])
    assert status is EpistemicStatus.PROVISIONAL


# ── a supposition can lose ─────────────────────────────────────

def test_a_supposition_the_base_contradicts_is_defeated(ks):
    """The question supposes no value is created; it also supplies positive
    unit economics, from which V01 — an established, curated rule — derives
    that value is. A perceived, strict premise used to win that conflict by
    construction and put V01 out. A supposition is an ordinary premise: the
    derivation defeats it."""
    af = _af(ks, "positive_unit_economics(acme)", "not_value_creation(acme)")
    assert _label(af, "value_creation(acme)") == {Label.IN}
    assert _label(af, "not_value_creation(acme)") == {Label.OUT}
    status, _, _ = af.get_epistemic_status("not_value_creation(acme)")
    assert status is EpistemicStatus.CONTESTED


def test_two_contradictory_suppositions_are_not_both_accepted(ks):
    """A question that supposes a thing and its negation. Two strict premises
    could not attack each other, so both used to be labelled IN — a
    contradictory extension. As ordinary premises of equal standing they
    defeat each other and neither is accepted."""
    af = _af(ks, "value_creation(acme)", "not_value_creation(acme)")
    assert Label.IN not in _label(af, "value_creation(acme)")
    assert Label.IN not in _label(af, "not_value_creation(acme)")


# ── the scope-exclusion door ───────────────────────────────────

def test_an_exclusion_the_question_supplies_does_not_reach_established(ks):
    """The second door. A scope exclusion builds its own undercutting
    argument, which used to enter as PRATYAKSA at ESTABLISHED whatever the
    exclusion rested on — here, the question's word. It still undercuts:
    undercutting needs no preference."""
    af = _af(ks, "superior_information(acme)", "perfectly_commoditized_market(acme)")
    (undercutter,) = [a for a in af.arguments.values()
                      if a.conclusion == "inapplicable_V03(acme)"]
    excl = _premise(af, "perfectly_commoditized_market(acme)")
    assert undercutter.status is EpistemicStatus.PROVISIONAL
    assert undercutter.tag.pramana_type is PramanaType.SABDA
    assert undercutter.status_bound_by == (f"sub:{excl.id}",)
    assert _label(af, "pricing_power(acme)") == {Label.OUT}


# ── what follows from a supposition ────────────────────────────

def test_what_follows_from_a_supposition_keeps_the_rules_grade(ks):
    """The growth case's derivations. V04 is an established curated rule and
    V11 a working hypothesis; they must still grade apart, as they did, with
    the supposition below both. Folding the supposition into the meet would
    put all three at PROVISIONAL on every live query."""
    af = _af(ks, *GROWTH)
    for conclusion, rule, expected in [
        ("coordination_overhead(business)", "V04", EpistemicStatus.ESTABLISHED),
        ("not_value_creation(business)", "V11", EpistemicStatus.HYPOTHESIS),
    ]:
        (arg,) = [a for a in af.arguments.values() if a.top_rule == rule]
        assert arg.conclusion == conclusion
        assert arg.status is expected, (rule, arg.status)
        assert arg.tag.pramana_type is PramanaType.ANUMANA, rule


# ── through the engine, both paths ─────────────────────────────

class _Grounding:
    def __init__(self, predicates):
        self._result = GroundingResult(
            predicates=list(predicates), confidence=1.0, disputed=[],
            warnings=[], advisories=[], clarification_needed=False,
        )

    def __call__(self, query):
        return self._result


@pytest.mark.parametrize("path", ["forward", "forward_with_coverage"])
def test_the_engine_reports_the_premise_as_supposed_not_perceived(ks, path):
    """What a caller reads: `provenance` and `uncertainty` for the Varenna
    premise, on both answering paths."""
    engine = AnvikshikiEngineV4(knowledge_store=ks,
                                grounding_pipeline=_Grounding(VARENNA))
    engine.synthesizer = lambda **kw: dspy.Prediction(
        response="An answer.", sources_cited=[])
    result = (engine.forward("q", retrieved_chunks=[]) if path == "forward"
              else engine.forward_with_coverage("q"))
    premise = VARENNA[0]
    assert result.provenance[premise]["pramana"] == "SABDA"
    assert result.uncertainty[premise]["epistemic"]["status"] == "provisional"
    assert result.arguments[_premise_id(result, premise)]["status_bound_by"] == ["asserted"]


def _premise_id(result, conclusion):
    (aid,) = [aid for aid, a in result.arguments.items()
              if a["conclusion"] == conclusion and a["vyapti_id"] is None]
    return aid


# ── what the supposition leaves out of a derivation, and what it keeps ──

def _rule(vid, antecedents, consequent, status, **kw):
    from anvikshiki_v4.schema import CausalStatus, Confidence, Vyapti
    return Vyapti(
        id=vid, name=vid, statement=f"{antecedents} implies {consequent}",
        causal_status=CausalStatus.EMPIRICAL,
        confidence=Confidence(existence=1.0, formulation=1.0,
                              evidence="theoretical"),
        epistemic_status=status, antecedents=antecedents,
        consequent=consequent, **kw,
    )


def _store(*rules):
    from anvikshiki_v4.schema import DomainType, KnowledgeStore
    return KnowledgeStore(domain_type=DomainType.CRAFT,
                          vyaptis={r.id: r for r in rules})


def test_a_suppositions_sources_still_travel_to_what_follows(ks):
    """Left out of the grade, not out of the record: a caller that passes
    sources with a fact still finds them on every derivation from it, as it
    did when the fact was folded into the tag."""
    af = compile_t2(ks, [{"predicate": "organizational_growth(acme)",
                          "confidence": 1.0, "sources": ["q_src"]}])
    (v04,) = [a for a in af.arguments.values() if a.top_rule == "V04"]
    assert "q_src" in v04.tag.source_ids


def test_a_derivation_names_only_what_it_reasoned_through_as_its_bound():
    """`status_bound_by` answers "what holds this down?". V02 needs the
    supposition `w` and `y`, which V01 — a provisional rule — derived. `y` is
    what holds V02's conclusion at PROVISIONAL; `w` sits at the same rank but
    is the condition, not a link, and naming it would point a reader at
    something whose removal changes nothing."""
    from anvikshiki_v4.schema import EpistemicStatus as KB
    store = _store(_rule("V01", ["w"], "y", KB.PROVISIONAL),
                   _rule("V02", ["w", "y"], "z", KB.ESTABLISHED))
    af = compile_t2(store, [{"predicate": "w", "confidence": 1.0}])
    (y,) = [a for a in af.arguments.values() if a.top_rule == "V01"]
    (z,) = [a for a in af.arguments.values() if a.top_rule == "V02"]
    assert z.status is EpistemicStatus.PROVISIONAL
    assert z.status_bound_by == (f"sub:{y.id}",)


def test_the_combination_cap_keeps_the_supposition_over_a_weaker_derivation():
    """The cap keeps the strongest combinations per rule. `y` is both
    supposed and derived by V01, a working hypothesis. A supposition weakens
    nothing reasoned under it, so V02 through it is the strongest
    combination there is and, at a cap of one, the only one built."""
    from dataclasses import replace as dc_replace
    from anvikshiki_v4.engine_params import DEFAULT_PARAMS
    from anvikshiki_v4.schema import EpistemicStatus as KB
    store = _store(_rule("V01", ["w"], "y", KB.WORKING_HYPOTHESIS),
                   _rule("V02", ["y"], "z", KB.ESTABLISHED))
    af = compile_t2(
        store,
        [{"predicate": "w", "confidence": 1.0},
         {"predicate": "y", "confidence": 1.0}],
        params=dc_replace(DEFAULT_PARAMS.compiler,
                          max_argument_combos_per_rule=1),
    )
    v02 = [a for a in af.arguments.values() if a.top_rule == "V02"]
    assert v02, "fixture no longer fires V02"
    assert all(set(a.sub_arguments) <= af.supposed for a in v02), [
        (a.id, a.sub_arguments) for a in v02]


def test_an_exclusion_the_base_also_derives_undercuts_at_the_derivations_grade():
    """The undercutter accrues over every argument for the excluding fact.
    Here `ex` is both supposed and derived by V02, an established rule; the
    supposition alone would put the undercutter at PROVISIONAL and SABDA, the
    derivation lifts it to what the base actually concludes — and it is the
    derivation, not the supposition, that holds it there."""
    from anvikshiki_v4.schema import EpistemicStatus as KB
    store = _store(
        _rule("V01", ["a"], "b", KB.ESTABLISHED, scope_exclusions=["ex"]),
        _rule("V02", ["c"], "ex", KB.ESTABLISHED),
    )
    af = compile_t2(store, [{"predicate": p, "confidence": 1.0}
                            for p in ("ex", "a", "c")])
    (undercutter,) = [x for x in af.arguments.values()
                      if x.conclusion == "inapplicable_V01"]
    (derived_ex,) = [x for x in af.arguments.values() if x.top_rule == "V02"]
    assert undercutter.status is EpistemicStatus.ESTABLISHED
    assert undercutter.tag.pramana_type is PramanaType.ANUMANA
    assert undercutter.status_bound_by == (f"sub:{derived_ex.id}",)


# ── what a conclusion holds only given (#195) ──────────────────
#
# A supposition does not lower what follows from it, so "established" on a
# conclusion V02 derived from a premise only the question supplied read as a
# finding — the false premise the engine then explained. The status stands;
# what it holds given is said beside it.

def test_the_varenna_conclusion_holds_only_given_the_supposed_constraint(ks):
    """#195 as reported: V02 derives `resource_allocation_effective` at
    established from `binding_constraint_identified`, which nothing in the
    base concludes."""
    af = _af(ks, *VARENNA)
    effective, constraint = VARENNA[1], VARENNA[0]
    assert af.get_epistemic_status(effective)[0] is EpistemicStatus.ESTABLISHED
    assert af.given(effective) == [frozenset([constraint])]
    assert af.given(constraint) == [frozenset([constraint])]


@pytest.mark.parametrize("path", ["forward", "forward_with_coverage"])
def test_the_engine_says_what_the_status_holds_given_on_both_paths(ks, path):
    """What the synthesizer reads and what a caller reads, on both paths."""
    engine = AnvikshikiEngineV4(knowledge_store=ks,
                                grounding_pipeline=_Grounding(VARENNA))
    seen = {}

    def synth(**kw):
        seen.update(kw)
        return dspy.Prediction(response="An answer.", sources_cited=[])

    engine.synthesizer = synth
    result = (engine.forward("q", retrieved_chunks=[]) if path == "forward"
              else engine.forward_with_coverage("q"))
    effective, constraint = VARENNA[1], VARENNA[0]
    assert result.provenance[effective]["given"] == [[constraint]]
    (line,) = [x for x in seen["accepted_arguments"].splitlines()
               if x.startswith(f"- {effective}:")]
    assert line.startswith(f"- {effective}: established")
    assert line.endswith(f"; holds only given what the question supposed: {constraint}")


def _hand_af():
    """A framework built by hand, so every shape `given` must read is present
    and nothing else: S1, S2 supposed; rules over them; one conclusion per
    case. Statuses and labels are set, not computed."""
    from anvikshiki_v4.argumentation import ArgumentationFramework
    from anvikshiki_v4.schema_v4 import Argument, ProvenanceTag
    E, H = EpistemicStatus.ESTABLISHED, EpistemicStatus.HYPOTHESIS
    tag = ProvenanceTag(pramana_type=PramanaType.ANUMANA, trust_score=1.0,
                        decay_factor=1.0)
    af = ArgumentationFramework()
    rows = [  # id, conclusion, rule, subs, status, label
        ("S1", "s1", None, (), EpistemicStatus.PROVISIONAL, Label.IN),
        ("S2", "s2", None, (), EpistemicStatus.PROVISIONAL, Label.IN),
        ("O1", "either", "R", ("S1",), E, Label.IN),
        ("O2", "either", "R", ("S2",), E, Label.IN),
        ("B1", "both", "R", ("S1", "S2"), E, Label.IN),
        ("P1", "fewest", "R", ("S1",), E, Label.IN),
        ("P2", "fewest", "R", ("S1", "S2"), E, Label.IN),
        ("F1", "free", "R", ("S1",), E, Label.IN),
        ("F2", "free", "R", (), E, Label.IN),
        ("W1", "weaker_free", "R", ("S1",), E, Label.IN),
        ("W2", "weaker_free", "R", (), H, Label.IN),
        ("X1", "out_free", "R", ("S1",), E, Label.IN),
        ("X2", "out_free", "R", (), E, Label.OUT),
        ("D1", "defeated", "R", ("S1",), E, Label.OUT),
        ("U1", "undercut", None, ("O1", "O2"), E, Label.IN),
        ("U2", "undercut_redundant", None, ("O1", "B1"), E, Label.IN),
        ("C1", "chained", "R", ("U1",), E, Label.IN),
    ]
    for aid, conc, rule, subs, status, label in rows:
        af.add_argument(Argument(id=aid, conclusion=conc, top_rule=rule,
                                 sub_arguments=subs, premises=frozenset([conc]),
                                 tag=tag, status=status, status_bound_by=()))
        af.labels[aid] = label
    af.supposed |= {"S1", "S2"}
    return af


@pytest.mark.parametrize("conclusion, expected", [
    ("either", [{"s1"}, {"s2"}]),      # two arguments: given either one
    ("both", [{"s1", "s2"}]),          # one rule needing both: given both
    ("fewest", [{"s1"}]),              # {s1, s2} is redundant beside {s1}
    ("free", []),                      # one argument at the status needs none
    ("weaker_free", [{"s1"}]),         # a weaker free argument does not lift it
    ("out_free", [{"s1"}]),            # nor a defeated one
    ("defeated", []),                  # nothing IN: nothing to be conditional
    ("undercut", [{"s1"}, {"s2"}]),    # no rule: accrues, any one carries it
    ("undercut_redundant", [{"s1"}]),  # accrual drops the superset too
    ("chained", [{"s1"}, {"s2"}]),     # alternatives travel through a rule
], ids=lambda x: x if isinstance(x, str) else None)
def test_given_reads_every_shape(conclusion, expected):
    assert _hand_af().given(conclusion) == [frozenset(s) for s in expected]


def test_an_undercutter_says_what_supposed_exclusion_it_holds_given(ks):
    """The scope undercutter takes its status from the excluding fact; it
    must also say what that fact was supposed on, or it reads as a finding."""
    af = _af(ks, "superior_information(acme)", "perfectly_commoditized_market(acme)")
    assert af.given("inapplicable_V03(acme)") == [
        frozenset(["perfectly_commoditized_market(acme)"])]


def test_an_undercutter_from_a_derived_exclusion_holds_given_what_that_rests_on():
    """When the base derives the exclusion, the undercutter rests on what the
    derivation rests on — here the supposition `c` V02 reasoned from."""
    from anvikshiki_v4.schema import EpistemicStatus as KB
    store = _store(
        _rule("V01", ["a"], "b", KB.ESTABLISHED, scope_exclusions=["ex"]),
        _rule("V02", ["c"], "ex", KB.ESTABLISHED),
    )
    af = compile_t2(store, [{"predicate": p, "confidence": 1.0}
                            for p in ("ex", "a", "c")])
    af.compute_grounded()
    assert af.given("inapplicable_V01") == [frozenset(["c"])]
