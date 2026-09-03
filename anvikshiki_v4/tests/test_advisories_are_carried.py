# tests/test_advisories_are_carried.py
"""Findings about rules reach the caller, and a rule's declared scope is one.

Two halves of one channel, and neither works without the other.

  #92  `_check_scope` and `_check_decay` run on every query and attach their
       output to a `GroundingResult` whose only production readers sit inside
       the `clarification_needed` branch — which those two return paths never
       take. The right warning, computed correctly, dropped one frame later.

  #89  `scope_conditions` is authored on every rule in both shipped bases,
       extracted, evaluated, and printed into the grounder's prompt, and
       nothing in the reasoning path checks it. V03 declares
       `heterogeneous_quality_market` and concludes `pricing_power` from
       `superior_information` alone, in a market never established to be
       heterogeneous.

The decision taken was **advisory now, gate later on evidence**: the rule
still fires, the conclusion is still returned, and the engine says what it
did. Gating would break 43 tests across 9 files — sampled and found to be
fixture omissions rather than assertions that scope should be ignored — so it
is a cost rather than 43 decisions, and it is a separate decision from this
one.

The parametrised laws below are the ones that matter. A single-path version of
the equivalent test in `test_empty_extension_is_a_state.py` passed while the
field was deleted from the other path, and only a mutation found it. A caller
should not have to know which method it called before trusting a field.
"""

from datetime import datetime, timedelta
from types import SimpleNamespace

import dspy
import pytest

from anvikshiki_v4.advisories import (
    Advisory,
    AdvisoryKind,
    as_wire,
    unestablished_scope_advisories,
)
from anvikshiki_v4.engine_v4 import AnvikshikiEngineV4, AnvikshikiEngineV4Phase1
from anvikshiki_v4.grounding import GroundingPipeline, GroundingResult
from anvikshiki_v4.schema import (
    CausalStatus,
    Confidence,
    DecayRisk,
    DomainType,
    EpistemicStatus,
    KnowledgeStore,
    Vyapti,
)
from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store

BOTH_PATHS = pytest.mark.parametrize(
    "path", ["forward", "forward_with_coverage"]
)


def _vyapti(vid, antecedents, consequent, **kw):
    return Vyapti(
        id=vid, name=vid, statement=f"{antecedents} implies {consequent}",
        causal_status=CausalStatus.EMPIRICAL,
        confidence=Confidence(existence=0.9, formulation=0.9,
                              evidence="theoretical"),
        epistemic_status=EpistemicStatus.ESTABLISHED,
        antecedents=antecedents, consequent=consequent, **kw
    )


@pytest.fixture
def ks():
    """V01 declares a scope condition nothing in the base can derive.

    `market_is_heterogeneous` is no rule's consequent and no rule's
    antecedent, which is the shape every scope condition in both shipped
    bases actually has — 0 of 5 in business, 0 of 4 in copywriting. It can
    only ever arrive as a grounded fact from the query, and that is what
    makes the advisory worth having rather than a formality.

    V02 declares none, so it is the control: the same machinery must stay
    silent about it however many times it fires.
    """
    return KnowledgeStore(
        domain_type=DomainType.CRAFT,
        vyaptis={v.id: v for v in (
            _vyapti("V01", ["gate_open"], "derived_value",
                    scope_conditions=["market_is_heterogeneous"]),
            _vyapti("V02", ["second_gate"], "other_value"),
        )},
    )


def _af(ks, *predicates):
    af = compile_t2(ks, [
        {"predicate": p, "confidence": 0.9} for p in predicates
    ])
    return af, af.compute_grounded()


# ── #89: the framework's half ────────────────────────────────

class TestUnestablishedScope:

    def test_a_rule_that_fires_outside_its_declared_scope_says_so(self, ks):
        af, labels = _af(ks, "gate_open(acme)")
        (advisory,) = unestablished_scope_advisories(ks, af, labels)
        assert advisory.kind == AdvisoryKind.UNESTABLISHED_SCOPE
        assert advisory.vyapti_id == "V01"
        assert advisory.subject == "market_is_heterogeneous(acme)"
        assert "derived_value(acme)" in advisory.message, (
            "the advisory has to name the conclusion it is about; without it "
            "a reader cannot tell which of several findings it qualifies"
        )

    def test_the_rule_still_fires(self, ks):
        """Advisory, not a gate. The decision was explicit and this is the
        line that records it — if firing is ever gated on scope, this test is
        the one that must be argued with first."""
        af, labels = _af(ks, "gate_open(acme)")
        assert unestablished_scope_advisories(ks, af, labels)
        assert any(
            a.conclusion == "derived_value(acme)"
            for a in af.arguments.values() if a.top_rule == "V01"
        )

    def test_establishing_the_condition_for_that_entity_silences_it(self, ks):
        af, labels = _af(
            ks, "gate_open(acme)", "market_is_heterogeneous(acme)"
        )
        assert unestablished_scope_advisories(ks, af, labels) == []

    def test_a_bare_condition_establishes_it_for_any_entity(self, ks):
        """A deliberate leniency, safe only because nothing is gated on the
        result. The shipped bases write rules in bare names while facts
        arrive bound, so a query asserting the condition unbound is read as a
        statement about the world the rule reasons in. The strict reading
        would advise on every rule in every base written that way."""
        af, labels = _af(ks, "gate_open(acme)", "market_is_heterogeneous")
        assert unestablished_scope_advisories(ks, af, labels) == []

    def test_establishing_it_for_a_different_entity_does_not(self, ks):
        """The entity binding decides chaining, rebuttal and scope everywhere
        else in the engine; an advisory that ignored it would report a market
        established about globex as covering a conclusion about acme."""
        af, labels = _af(
            ks, "gate_open(acme)", "market_is_heterogeneous(globex)"
        )
        (advisory,) = unestablished_scope_advisories(ks, af, labels)
        assert advisory.subject == "market_is_heterogeneous(acme)"

    def test_a_rule_declaring_no_scope_is_never_advised_about(self, ks):
        af, labels = _af(ks, "second_gate(acme)")
        assert [a for a in af.arguments.values() if a.top_rule == "V02"], (
            "fixture no longer fires the control rule"
        )
        assert unestablished_scope_advisories(ks, af, labels) == []

    def test_a_defeated_rule_is_not_advised_about(self, ks):
        """A rule argument labelled OUT has already been answered by the
        framework. Reporting its scope too would put a second finding on a
        conclusion the engine is not making — the same test `derivation_state`
        applies, for the same reason."""
        from anvikshiki_v4.schema_v4 import Label

        af, labels = _af(ks, "gate_open(acme)")
        fired = [
            aid for aid, a in af.arguments.items() if a.top_rule == "V01"
        ]
        assert fired, "fixture no longer fires V01"
        defeated = {aid: Label.OUT for aid in fired}
        assert unestablished_scope_advisories(
            ks, af, {**labels, **defeated}
        ) == []

    def test_the_shipped_base_reproduces_the_reported_case(self):
        """#89 as filed, against the real business base rather than a fixture.

        V03 declares `heterogeneous_quality_market` and concludes
        `pricing_power` from `superior_information` alone.
        """
        business = load_knowledge_store(
            "anvikshiki_v4/data/business_expert.yaml"
        )
        af, labels = _af(business, "superior_information(acme)")
        v03 = [a for a in unestablished_scope_advisories(business, af, labels)
               if a.vyapti_id == "V03"]
        assert len(v03) == 1
        assert v03[0].subject == "heterogeneous_quality_market(acme)"
        assert "pricing_power(acme)" in v03[0].message


# ── #92: the grounding half, and that the two lists cannot drift ──

class TestGroundingCarriesTypedAdvisories:

    def test_the_scope_check_returns_advisories(self):
        business = load_knowledge_store(
            "anvikshiki_v4/data/business_expert.yaml"
        )
        vid, excl = next(
            (v.id, e) for v in business.vyaptis.values()
            for e in v.scope_exclusions
        )
        (advisory,) = GroundingPipeline(business)._check_scope(
            [f"{excl}(acme)"]
        )
        assert isinstance(advisory, Advisory)
        assert advisory.kind == AdvisoryKind.SCOPE_EXCLUSION
        assert advisory.vyapti_id == vid
        assert advisory.subject == f"{excl}(acme)"

    def test_the_decay_check_returns_advisories(self, ks):
        ks.vyaptis["V01"].decay_risk = DecayRisk.CRITICAL
        ks.vyaptis["V01"].decay_condition = "regime change"
        (advisory,) = GroundingPipeline(ks)._check_decay(["V01"])
        assert advisory.kind == AdvisoryKind.DECAY
        assert advisory.vyapti_id == "V01"
        assert "NEVER verified" in advisory.message

    def test_a_stale_rule_is_reported_with_its_age(self, ks):
        ks.vyaptis["V01"].decay_risk = DecayRisk.HIGH
        ks.vyaptis["V01"].decay_condition = "regime change"
        ks.vyaptis["V01"].last_verified = datetime.now() - timedelta(days=400)
        (advisory,) = GroundingPipeline(ks)._check_decay(["V01"])
        assert advisory.kind == AdvisoryKind.DECAY
        assert "400 days ago" in advisory.message

    def test_warnings_are_exactly_the_advisory_messages(self, ks):
        """One source of truth. `warnings` is kept because the clarification
        paths legitimately put something else in it — a message about the
        grounding rather than a finding about a rule — but on the paths where
        both exist, one is derived from the other at the single site that
        builds them, so they cannot drift."""
        ks.vyaptis["V01"].decay_risk = DecayRisk.CRITICAL
        ks.vyaptis["V01"].decay_condition = "regime change"
        pipeline = GroundingPipeline(ks)
        pipeline.grounder = lambda **kw: SimpleNamespace(
            predicates=["gate_open(acme)"], relevant_vyaptis=["V01"],
        )
        result = pipeline._forward_minimal("q", "snippet")
        assert result.advisories
        assert result.warnings == [a.message for a in result.advisories]


# ── #92: the channel reaches the caller ──────────────────────

class _Grounding:
    def __init__(self, predicates, advisories=(), clarify=False):
        self._result = GroundingResult(
            predicates=list(predicates), confidence=0.85, disputed=[],
            warnings=[a.message for a in advisories],
            advisories=list(advisories),
            clarification_needed=clarify,
        )

    def __call__(self, query):
        return self._result


def _engine(ks, predicates, advisories=(), clarify=False):
    engine = AnvikshikiEngineV4(
        knowledge_store=ks,
        grounding_pipeline=_Grounding(predicates, advisories, clarify),
    )
    engine.synthesizer = lambda **kw: dspy.Prediction(
        response="An answer.", sources_cited=[],
    )
    return engine


def _run(engine, path):
    return (engine.forward("q", retrieved_chunks=[]) if path == "forward"
            else engine.forward_with_coverage("q"))


class TestTheAdvisoryChannelIsLive:

    @BOTH_PATHS
    def test_the_framework_finding_reaches_the_prediction(self, ks, path):
        pred = _run(_engine(ks, ["gate_open(acme)"]), path)
        (advisory,) = pred.advisories
        assert advisory["kind"] == "unestablished_scope"
        assert advisory["vyapti_id"] == "V01"

    @BOTH_PATHS
    def test_the_grounding_finding_reaches_the_prediction(self, ks, path):
        """The half that was computed on every query and read by nothing.
        Passing it through an answering path is the whole of #92."""
        decayed = Advisory(
            kind=AdvisoryKind.DECAY, vyapti_id="V02",
            message="DECAY: V02 NEVER verified (regime change)",
        )
        pred = _run(_engine(ks, ["second_gate(acme)"], [decayed]), path)
        assert [a["message"] for a in pred.advisories] == [decayed.message]

    @BOTH_PATHS
    def test_a_clean_query_carries_an_empty_list_not_a_missing_field(
        self, ks, path
    ):
        """Absence has to be readable as absence. A caller that has to guard
        every read with `getattr(pred, 'advisories', None)` learns nothing
        from a missing attribute, and an engine that answers with no findings
        is a different state from one that never looked."""
        pred = _run(_engine(ks, ["second_gate(acme)"]), path)
        assert pred.advisories == []

    @BOTH_PATHS
    def test_the_clarification_return_carries_the_field_too(self, ks, path):
        pred = _run(_engine(ks, [], clarify=True), path)
        assert pred.advisories == []

    def test_the_out_of_domain_decline_carries_the_field(self, ks):
        """The one return path with neither a framework nor a grounding
        finding behind it, and the easiest to forget."""
        from anvikshiki_v4.coverage import SemanticCoverageAnalyzer

        class _Decline:
            def __call__(self, **kw):
                return SimpleNamespace(
                    augmented=False, reason="out of domain", merged_kb=None,
                    framework_score=0.0, new_vyaptis=[],
                    validation_warnings=[],
                )

        engine = _engine(ks, ["utterly_unrelated_concept(acme)"])
        engine.coverage_analyzer = SemanticCoverageAnalyzer(ks)
        engine.augmentation_pipeline = _Decline()
        pred = engine.forward_with_coverage("q")
        assert pred.coverage["decision"] == "DECLINE", (
            "fixture no longer reaches the decline path"
        )
        assert pred.advisories == []

    def test_the_phase_1_baseline_carries_the_field(self, ks):
        """Phase 1 is the ungrounded baseline the others are measured
        against. Its shape has to match theirs or the comparison reads a
        missing field as a missing finding."""
        engine = AnvikshikiEngineV4Phase1(ks, _Grounding(["gate_open(acme)"]))
        engine.reasoner = lambda **kw: dspy.Prediction(
            response="An answer.", sources_cited=[],
        )
        assert engine.forward("q", retrieved_chunks=[]).advisories == []

    @BOTH_PATHS
    def test_both_producers_arrive_together(self, ks, path):
        """The join is the point. A caller reading one field gets what the
        grounding boundary noticed AND what the framework noticed, and does
        not have to know there were two."""
        decayed = Advisory(
            kind=AdvisoryKind.DECAY, vyapti_id="V01",
            message="DECAY: V01 NEVER verified (regime change)",
        )
        pred = _run(_engine(ks, ["gate_open(acme)"], [decayed]), path)
        assert {a["kind"] for a in pred.advisories} == {
            "decay", "unestablished_scope"
        }

    @BOTH_PATHS
    def test_advisories_are_not_violations(self, ks, path):
        """Alongside, not inside. A rule firing outside its declared scope is
        not an attack on its conclusion, and folding it into `violations`
        would make an advisory read as a defeat."""
        pred = _run(_engine(ks, ["gate_open(acme)"]), path)
        assert pred.advisories
        assert pred.violations == []


class TestTheWireForm:

    def test_advisories_go_out_as_plain_dicts(self, ks):
        """`violations` beside it is a list of dicts and one output field
        should not need two unpacking rules."""
        wire = as_wire([Advisory(
            kind=AdvisoryKind.DECAY, vyapti_id="V01", message="DECAY: V01",
        )])
        assert wire == [{
            "kind": "decay", "vyapti_id": "V01",
            "message": "DECAY: V01", "subject": None,
        }]

    def test_the_kind_serialises_as_its_value_not_its_repr(self):
        """A string enum that reaches JSON as `AdvisoryKind.DECAY` is not
        readable by anything downstream."""
        import json

        wire = as_wire([Advisory(
            kind=AdvisoryKind.UNESTABLISHED_SCOPE, vyapti_id="V01",
            message="m",
        )])
        assert json.loads(json.dumps(wire))[0]["kind"] == (
            "unestablished_scope"
        )
