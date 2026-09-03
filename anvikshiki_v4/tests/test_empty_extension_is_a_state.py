# tests/test_empty_extension_is_a_state.py
"""When the framework derives nothing, saying so is the engine's job.

Two defects, found together by running an ordinary query against a knowledge
base the engine had never seen, and separable:

  #112  `accepted_str` fell back to the literal string "No accepted
        conclusions." and the synthesizer was asked the question anyway. It
        answered fluently, at length, and without a hedge — confident prose at
        exactly the moment the engine had nothing behind it. The only outward
        signal was an empty `sources` list, which reads as "no citations
        needed" rather than "no reasoning happened", and nothing read it.

  #109  Coverage counted a predicate as covered when the base holds the word
        and owns no machinery that can consume it in the polarity asked. The
        polarity was computed — `_match_type` exists for that — and then put
        in `match_details`, which the routing decision never reads.

The second is one route into the first and not the only one, which is why
both are tested here and why the coverage tests below include an affirmative
case that stays FULL: a query matching one antecedent of a two-antecedent
rule derives nothing while being perfectly covered, and coverage is not the
tool for that.

What is deliberately NOT changed: `not_X` against a base that concludes `X`
stays FULL. `test_coverage_negation.py` decided that on purpose — the
rebutting attack is the engine's most informative behaviour — and asserted it
"so a later change has to argue with it". This change does not have to. The
test is not polarity, it is whether any rule can consume the predicate, and a
base concluding the contrary can: that is what a rebuttal is made of.
"""

import dspy
import pytest

from anvikshiki_v4.coverage import SemanticCoverageAnalyzer
from anvikshiki_v4.engine_v4 import (
    NO_DERIVATION_NOTICE,
    AnvikshikiEngineV4,
    derivation_state,
)
from anvikshiki_v4.grounding import GroundingResult
from anvikshiki_v4.schema import (
    CausalStatus,
    Confidence,
    DomainType,
    EpistemicStatus,
    KnowledgeStore,
    Vyapti,
)
from anvikshiki_v4.t2_compiler_v4 import compile_t2


def _vyapti(vid, antecedents, consequent):
    return Vyapti(
        id=vid, name=vid, statement=f"{antecedents} implies {consequent}",
        causal_status=CausalStatus.EMPIRICAL,
        confidence=Confidence(existence=0.9, formulation=0.9,
                              evidence="theoretical"),
        epistemic_status=EpistemicStatus.ESTABLISHED,
        antecedents=antecedents, consequent=consequent,
    )


@pytest.fixture
def ks():
    """A base with the three shapes that matter.

    V01  one antecedent, and its consequent has a contrary producer (V03), so
         `not_derived_value` can rebut and is NOT inert.
    V02  TWO antecedents — the shape that lets a fully-covered query derive
         nothing without any negation involved.
    V03  concludes `not_derived_value`, which is what makes the negation
         consumable. Without it the negated query would be inert, and that is
         the whole distinction under test.

    `gate_open` is only ever an antecedent and nothing concludes it, so
    `not_gate_open` is the inert case: no rule takes it, no rule concludes it,
    no rule concludes its contrary.
    """
    return KnowledgeStore(
        domain_type=DomainType.CRAFT,
        vyaptis={v.id: v for v in (
            _vyapti("V01", ["gate_open"], "derived_value"),
            _vyapti("V02", ["first_half", "second_half"], "both_halves"),
            _vyapti("V03", ["value_blocked"], "not_derived_value"),
        )},
    )


@pytest.fixture
def analyzer(ks):
    return SemanticCoverageAnalyzer(ks)


# ── #109: covered is not the same as usable ──────────────────

class TestCoverageSeparatesVocabularyFromMachinery:

    def test_a_predicate_no_rule_can_consume_is_reported_inert(self, analyzer):
        r = analyzer.analyze(["not_gate_open"])
        assert r.inert_predicates == ["not_gate_open"]

    def test_full_is_not_claimed_when_every_match_is_inert(self, analyzer):
        """FULL is a claim the base can reason about this query, not that it
        recognises the words. With nothing consumable the claim is false
        however high the ratio is."""
        r = analyzer.analyze(["not_gate_open"])
        assert r.coverage_ratio == 1.0
        assert r.decision == "PARTIAL"

    def test_the_match_itself_is_left_alone(self, analyzer):
        """The vocabulary match is real and the routing is what retrieval
        depends on. Only the decision moves — demoting the match too would
        lose the chapter this query is actually about."""
        r = analyzer.analyze(["not_gate_open"])
        assert r.matched_predicates == ["not_gate_open"]
        assert r.unmatched_predicates == []
        assert r.relevant_vyaptis == ["V01"]

    def test_a_negation_the_base_can_rebut_is_not_inert(self, analyzer):
        """The case test_coverage_negation.py protects, asserted here too so
        the distinction is explicit rather than incidental. V03 concludes
        `not_derived_value`, so the base owns machinery for this polarity."""
        r = analyzer.analyze(["not_derived_value"])
        assert r.inert_predicates == []
        assert r.decision == "FULL"

    def test_one_inert_among_usable_ones_does_not_demote(self, analyzer):
        """Only a query with nothing usable at all loses FULL. One dead
        predicate beside a live one is still a query the base can reason
        about."""
        r = analyzer.analyze(["gate_open", "not_gate_open"])
        assert r.inert_predicates == ["not_gate_open"]
        assert r.decision == "FULL"

    def test_an_affirmative_half_of_a_rule_is_not_inert(self, analyzer):
        """This is the case coverage must NOT try to catch. `first_half` is a
        real antecedent, so the base can consume it — it just needs the other
        half too. Fully covered, FULL, and it derives nothing. That is #112's
        job, and conflating the two would demote honest queries."""
        r = analyzer.analyze(["first_half"])
        assert r.inert_predicates == []
        assert r.decision == "FULL"
        af = compile_t2(r_ks := analyzer.ks, [
            {"predicate": "first_half", "confidence": 0.9}])
        assert not [a for a in af.arguments.values() if a.top_rule], (
            "fixture no longer demonstrates the case it exists for"
        )
        assert r_ks is not None


# ── #112: a premise is not a derivation ──────────────────────

class TestDerivationState:

    def test_nothing_derived_is_reported_as_nothing_derived(self, ks):
        af = compile_t2(ks, [{"predicate": "first_half", "confidence": 0.9}])
        d = derivation_state(af, af.compute_grounded())
        assert d["rule_backed"] is False
        assert d["derived_count"] == 0
        assert d["derived_conclusions"] == []

    def test_premises_are_counted_separately_from_derivations(self, ks):
        """The trap `extension_size` fell into. It counts every argument
        labelled IN, and premises are arguments — so a query that derived
        nothing reported an extension of 3: the facts handed in, counted back
        out. A caller watching it for "did the engine do anything" gets a
        non-zero number in exactly the case where it did not."""
        af = compile_t2(ks, [{"predicate": "first_half", "confidence": 0.9}])
        d = derivation_state(af, af.compute_grounded())
        assert d["premise_count"] == 1
        assert d["derived_count"] == 0

    def test_a_real_derivation_is_reported_as_one(self, ks):
        af = compile_t2(ks, [{"predicate": "gate_open", "confidence": 0.9}])
        d = derivation_state(af, af.compute_grounded())
        assert d["rule_backed"] is True
        assert d["derived_conclusions"] == ["derived_value"]
        assert d["premise_count"] == 1


# ── #112: the engine says so, without being asked nicely ─────

class _MockGrounding:
    def __init__(self, predicates):
        self._predicates = predicates

    def __call__(self, query):
        return GroundingResult(
            predicates=self._predicates, confidence=0.85,
            disputed=[], warnings=[], clarification_needed=False,
        )


def _engine(ks, predicates):
    engine = AnvikshikiEngineV4(
        knowledge_store=ks, grounding_pipeline=_MockGrounding(predicates)
    )
    # A synthesizer that answers confidently no matter what it is told, which
    # is what the real one did and the reason a prepended notice beats an
    # instruction the model is free to ignore.
    engine.synthesizer = lambda **kw: dspy.Prediction(
        response="Absolutely, here is what you should do.", sources_cited=[],
    )
    return engine


class TestTheEngineDeclaresTheFallback:

    def test_the_notice_is_prepended_when_nothing_was_derived(self, ks):
        pred = _engine(ks, ["first_half"]).forward_with_coverage("q")
        assert pred.response.startswith(NO_DERIVATION_NOTICE)
        assert pred.derivation["rule_backed"] is False

    def test_the_notice_does_not_depend_on_the_model_cooperating(self, ks):
        """The synthesizer above ignores every instruction it is given and
        answers confidently regardless — which is the realistic case, since
        the live one did exactly that when handed "No accepted conclusions."
        The notice still arrives, because it is prepended rather than
        requested."""
        pred = _engine(ks, ["first_half"]).forward_with_coverage("q")
        assert "did not derive this" in pred.response
        assert "Absolutely, here is what you should do." in pred.response

    def test_no_notice_when_the_framework_did_derive_something(self, ks):
        pred = _engine(ks, ["gate_open"]).forward_with_coverage("q")
        assert not pred.response.startswith(NO_DERIVATION_NOTICE)
        assert NO_DERIVATION_NOTICE not in pred.response
        assert pred.derivation["rule_backed"] is True
        assert pred.derivation["derived_conclusions"] == ["derived_value"]

    def test_the_plain_forward_path_declares_it_too(self, ks):
        """Both answering paths had the defect, so both are asserted. The
        non-coverage path is the one the older callers use."""
        pred = _engine(ks, ["first_half"]).forward("q", retrieved_chunks=[])
        assert pred.response.startswith(NO_DERIVATION_NOTICE)
        assert pred.derivation["rule_backed"] is False

    def test_an_empty_sources_list_is_no_longer_the_only_signal(self, ks):
        """What made this invisible: `sources` came back empty and empty reads
        as "no citations needed". Now the same case is distinguishable without
        reading the prose at all."""
        pred = _engine(ks, ["first_half"]).forward_with_coverage("q")
        assert pred.sources == []
        assert pred.derivation["derived_count"] == 0

    @pytest.mark.parametrize("path", ["forward", "forward_with_coverage"])
    def test_every_return_path_carries_derivation(self, ks, path):
        """Including the early ones, on BOTH answering paths.

        Parametrised because the single-path version of this test passed
        while `derivation` was deleted from the other path's clarification
        return — a mutation check caught that, not the test. A caller should
        not have to know which method it called before trusting the field.
        """
        class _Clarify:
            def __call__(self, query):
                return GroundingResult(
                    predicates=[], confidence=0.1, disputed=[],
                    warnings=["ambiguous"], clarification_needed=True,
                )
        engine = AnvikshikiEngineV4(
            knowledge_store=ks, grounding_pipeline=_Clarify()
        )
        pred = (engine.forward("q", retrieved_chunks=[])
                if path == "forward" else engine.forward_with_coverage("q"))
        assert pred.derivation == {
            "rule_backed": False, "derived_conclusions": [],
            "derived_count": 0, "premise_count": 0,
        }


def test_an_unlabelled_framework_raises_instead_of_reporting_nothing(ks):
    """The helper's own version of the defect it exists to stop.

    `af.labels` is empty until something computes it, so a caller that forgot
    would have been told "nothing was derived" — the framework's silence read
    as a fact about the query. It raises now, loudly, rather than answering
    plausibly and wrongly.
    """
    af = compile_t2(ks, [{"predicate": "gate_open", "confidence": 0.9}])
    assert af.labels == {}, "fixture no longer demonstrates the unlabelled case"
    with pytest.raises(ValueError, match="unlabelled framework"):
        derivation_state(af, af.labels)
