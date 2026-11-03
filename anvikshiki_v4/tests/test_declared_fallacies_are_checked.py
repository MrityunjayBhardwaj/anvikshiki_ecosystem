# tests/test_declared_fallacies_are_checked.py
"""A knowledge base's declared fallacies are checked when the engine answers (#252).

H01 "The Revenue Vanity Trap" — inferring business health from growth alone —
was declared in the business base and read by nothing on the answering path,
so it could not fire on "Is growth alone enough to make a business viable?",
the question it was written for. The live grounder produced
`organizational_growth(business)` for that question (openrouter/z-ai/glm-5.2,
shipped business base, 2026-10-31), which is the replay below.

When the base's own reasoning concludes against the fallacy (a `rebutted_by`
predicate is accepted) the match is reported as guarded, not as the fallacy
(#261).

Decided: a match is an advisory, never an attack. It must change no label and
no status, and it must arrive on both answering paths.
"""

import dspy
import pytest
from pydantic import ValidationError

from anvikshiki_v4.advisories import (
    Advisory,
    AdvisoryKind,
    declared_fallacy_advisories,
)
from anvikshiki_v4.engine_v4 import AnvikshikiEngineV4
from anvikshiki_v4.grounding import GroundingResult
from anvikshiki_v4.schema import (
    CausalStatus,
    Confidence,
    DomainType,
    EpistemicStatus,
    Hetvabhasa,
    KnowledgeStore,
    Vyapti,
)
from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store

BUSINESS = "anvikshiki_v4/data/business_expert.yaml"
GROWTH = ("organizational_growth(business)",)
# On GROWTH alone V11 "The Growth Trap" concludes `not_value_creation`, the
# base reasoning against H01, so H01 is guarded there (#261). A small team
# with direct contact excludes V11, which leaves H01 unanswered and firing.
UNGUARDED = GROWTH + ("small_team_direct_contact(business)",)
BOTH_PATHS = pytest.mark.parametrize("path", ["forward", "forward_with_coverage"])


@pytest.fixture(scope="module")
def business():
    return load_knowledge_store(BUSINESS)


def _without_patterns(ks):
    """The same base with every `detection_pattern` removed."""
    return ks.model_copy(update={"hetvabhasas": {
        hid: h.model_copy(update={"detection_pattern": None})
        for hid, h in ks.hetvabhasas.items()
    }})


class _Grounding:
    def __init__(self, predicates):
        self._result = GroundingResult(
            predicates=list(predicates), confidence=1.0, disputed=[],
            warnings=[], advisories=[], clarification_needed=False,
        )

    def __call__(self, query):
        return self._result


def _run(ks, predicates, path):
    engine = AnvikshikiEngineV4(knowledge_store=ks,
                                grounding_pipeline=_Grounding(predicates))
    engine.synthesizer = lambda **kw: dspy.Prediction(
        response="An answer.", sources_cited=[])
    return (engine.forward("q", retrieved_chunks=[]) if path == "forward"
            else engine.forward_with_coverage("q"))


def _fallacies(pred):
    return [a for a in pred.advisories if a["kind"] == "fallacy"]


def _af(ks, *predicates):
    af = compile_t2(ks, [{"predicate": p, "confidence": 1.0} for p in predicates])
    return af, af.compute_grounded()


# ── the reported case, through the engine ─────────────────────

@BOTH_PATHS
def test_h01_fires_on_growth_when_nothing_rebuts_it(business, path):
    pred = _run(business, UNGUARDED, path)
    (advisory,) = _fallacies(pred)
    assert advisory["hetvabhasa_id"] == "H01"
    assert advisory["vyapti_id"] is None
    assert advisory["subject"] == "organizational_growth(business)"
    h01 = business.hetvabhasas["H01"]
    assert h01.name in advisory["message"]
    assert h01.description in advisory["message"]
    assert "positive_unit_economics" in advisory["message"]


@BOTH_PATHS
def test_h01_is_silent_when_unit_economics_is_accepted(business, path):
    pred = _run(business, GROWTH + ("positive_unit_economics(business)",), path)
    assert _fallacies(pred) == []


@BOTH_PATHS
def test_the_check_changes_no_label_and_no_status(business, path):
    """Advisory, never an attack: everything but the advisory list is the
    same whether the base carries the pattern or not."""
    with_check = _run(business, UNGUARDED, path)
    without = _run(_without_patterns(business), UNGUARDED, path)
    assert _fallacies(with_check) and not _fallacies(without)
    for field in ("labels", "arguments", "attacks", "violations",
                  "provenance", "uncertainty", "derivation", "extension_size"):
        assert with_check[field] == without[field], field
    assert [a for a in with_check.advisories if a["kind"] != "fallacy"] == (
        without.advisories)


@BOTH_PATHS
def test_a_base_without_patterns_carries_no_fallacy_advisory(business, path):
    pred = _run(_without_patterns(business), GROWTH, path)
    assert _fallacies(pred) == []


@pytest.mark.parametrize("path_", [
    "anvikshiki_v4/data/copywriting_expert.yaml",
    "anvikshiki_v4/data/nonfiction_expert.yaml",
])
def test_the_other_shipped_bases_load_unchanged(path_):
    ks = load_knowledge_store(path_)
    assert ks.hetvabhasas
    assert all(h.detection_pattern is None for h in ks.hetvabhasas.values())


def test_only_h01_carries_a_pattern_in_the_business_base(business):
    """H02–H08's signatures name nothing this base has a predicate for, so
    they are left unpatterned rather than given invented predicates."""
    patterned = {hid for hid, h in business.hetvabhasas.items()
                 if h.detection_pattern is not None}
    assert patterned == {"H01"}
    pattern = business.hetvabhasas["H01"].detection_pattern
    assert pattern.present == ["organizational_growth"]
    assert pattern.absent == ["positive_unit_economics"]


# ── what "accepted" means ─────────────────────────────────────

def test_an_absent_predicate_that_is_defeated_does_not_silence_it(business):
    """Two contradictory suppositions about unit economics defeat each other;
    neither is accepted, so unit economics is not established and H01 holds."""
    af, labels = _af(business, *GROWTH, "positive_unit_economics(business)",
                     "not_positive_unit_economics(business)")
    assert any(a.conclusion == "positive_unit_economics(business)"
               for a in af.arguments.values())
    (advisory,) = declared_fallacy_advisories(business, af, labels)
    assert advisory.hetvabhasa_id == "H01"


def test_a_defeated_present_predicate_does_not_fire_it(business):
    af, labels = _af(business, "organizational_growth(business)",
                     "not_organizational_growth(business)")
    assert declared_fallacy_advisories(business, af, labels) == []


def _vyapti(vid, antecedents, consequent):
    return Vyapti(
        id=vid, name=vid, statement=f"{antecedents} implies {consequent}",
        causal_status=CausalStatus.EMPIRICAL,
        confidence=Confidence(existence=0.9, formulation=0.9,
                              evidence="theoretical"),
        epistemic_status=EpistemicStatus.ESTABLISHED,
        antecedents=antecedents, consequent=consequent,
    )


def _fallacy(hid, present, absent=(), rebutted_by=()):
    return Hetvabhasa(
        id=hid, name=f"name {hid}", description=f"description {hid}",
        detection_signature="free text", correction_pattern="fix it",
        detection_pattern={"present": list(present), "absent": list(absent),
                           "rebutted_by": list(rebutted_by)},
    )


@pytest.fixture
def small():
    return KnowledgeStore(
        domain_type=DomainType.CRAFT,
        vyaptis={v.id: v for v in (
            _vyapti("V01", ["a"], "b"),
            _vyapti("V02", ["c"], "d"),
        )},
        hetvabhasas={h.id: h for h in (
            _fallacy("H01", ["a", "b"]),
            _fallacy("H02", ["a"], ["c", "d"]),
        )},
    )


def test_every_present_predicate_is_required(small):
    af, labels = _af(small, "c(x)")
    assert declared_fallacy_advisories(small, af, labels) == []
    af, labels = _af(small, "b(x)")
    assert declared_fallacy_advisories(small, af, labels) == []


def test_a_derived_conclusion_counts_as_present(small):
    af, labels = _af(small, "a(x)")  # V01 derives b(x)
    assert [a.hetvabhasa_id for a in declared_fallacy_advisories(
        small, af, labels)] == ["H01", "H02"]


def test_any_absent_predicate_silences_it(small):
    af, labels = _af(small, "a(x)", "c(y)")
    assert [a.hetvabhasa_id for a in declared_fallacy_advisories(
        small, af, labels)] == ["H01"]


def test_an_internal_conclusion_is_not_a_finding():
    """Arguments whose conclusion starts with `_` are the framework's own
    bookkeeping, excluded the way every other advisory producer excludes
    them. Pinned on a hand-built framework because no shipped base names
    such a predicate in a rule."""
    from types import SimpleNamespace

    from anvikshiki_v4.schema_v4 import Label

    ks = KnowledgeStore(
        domain_type=DomainType.CRAFT,
        vyaptis={"V01": _vyapti("V01", ["_internal"], "b")},
        hetvabhasas={"H01": _fallacy("H01", ["_internal"])},
    )
    af = SimpleNamespace(arguments={
        "A0": SimpleNamespace(conclusion="_internal(x)", top_rule=None)})
    assert declared_fallacy_advisories(ks, af, {"A0": Label.IN}) == []


def test_an_unlabelled_framework_raises(small):
    af = compile_t2(small, [{"predicate": "a(x)", "confidence": 1.0}])
    with pytest.raises(ValueError, match="unlabelled"):
        declared_fallacy_advisories(small, af, {})


# ── the schema ────────────────────────────────────────────────

def test_a_pattern_must_name_something_present():
    with pytest.raises(ValidationError):
        _fallacy("H09", [], ["a"])


@pytest.mark.parametrize("present,absent,rebutted_by", [
    (["a", "typo"], [], []),
    (["a"], ["typo"], []),
    (["a"], [], ["typo"]),
], ids=["present", "absent", "rebutted_by"])
def test_a_pattern_naming_an_unknown_predicate_is_refused(present, absent,
                                                           rebutted_by):
    with pytest.raises(ValidationError, match="typo"):
        KnowledgeStore(
            domain_type=DomainType.CRAFT,
            vyaptis={"V01": _vyapti("V01", ["a"], "b")},
            hetvabhasas={"H01": _fallacy("H01", present, absent, rebutted_by)},
        )


def test_scope_conditions_and_exclusions_are_vocabulary():
    """A pattern may name what a rule declares as its scope, not only what it
    reasons over: scope names reach the grounder's vocabulary too."""
    v = _vyapti("V01", ["a"], "b").model_copy(update={
        "scope_conditions": ["in_scope"], "scope_exclusions": ["excluded"],
    })
    for present, absent in [(["in_scope"], []), (["a"], ["excluded"])]:
        KnowledgeStore(
            domain_type=DomainType.CRAFT, vyaptis={"V01": v},
            hetvabhasas={"H01": _fallacy("H01", present, absent)},
        )


def test_a_fallacy_without_a_pattern_still_loads():
    h = Hetvabhasa(id="H01", name="n", description="d",
                   detection_signature="free text", correction_pattern="c")
    assert h.detection_pattern is None


def test_a_fallacy_advisory_names_a_fallacy_and_no_rule():
    with pytest.raises(ValidationError):
        Advisory(kind=AdvisoryKind.FALLACY, message="m")
    with pytest.raises(ValidationError):
        Advisory(kind=AdvisoryKind.FALLACY, hetvabhasa_id="H01",
                 vyapti_id="V01", message="m")
    with pytest.raises(ValidationError):
        Advisory(kind=AdvisoryKind.DECAY, vyapti_id="V01",
                 hetvabhasa_id="H01", message="m")
    with pytest.raises(ValidationError):
        Advisory(kind=AdvisoryKind.DECAY, message="m")
    with pytest.raises(ValidationError):
        Advisory(kind=AdvisoryKind.FALLACY_GUARDED, vyapti_id="V01", message="m")
    Advisory(kind=AdvisoryKind.FALLACY_GUARDED, hetvabhasa_id="H01", message="m")


# ── the warning reaches the answer (#259) ──────────────────────
#
# Advisories never reach the synthesizer, so a matched fallacy was computed
# and dropped. It is prepended to the response, like NO_DERIVATION_NOTICE.

WARNING = "Warning: this reasoning has the shape of a fallacy"


@BOTH_PATHS
def test_the_answer_opens_with_the_matched_fallacy(business, path):
    pred = _run(business, UNGUARDED, path)
    h01 = business.hetvabhasas["H01"]
    blocks = pred.response.split("\n\n")
    (warning,) = [b for b in blocks if b.startswith(WARNING)]
    (line,) = warning.splitlines()[1:]
    assert line.startswith(f"- H01 '{h01.name}' — {h01.description}")
    assert line.endswith(f"Correction: {h01.correction_pattern}")
    assert blocks[-1] == "An answer."


@BOTH_PATHS
@pytest.mark.parametrize("silenced", ["unit_economics", "no_patterns"])
def test_no_warning_when_no_fallacy_matched(business, path, silenced):
    if silenced == "unit_economics":
        pred = _run(business, GROWTH + ("positive_unit_economics(business)",), path)
    else:
        pred = _run(_without_patterns(business), GROWTH, path)
    assert WARNING not in pred.response


def test_the_warning_names_only_fallacies():
    from anvikshiki_v4.advisories import (
        AdvisoryKind, scope_exclusion_advisory)
    from anvikshiki_v4.engine_v4 import fallacy_notice
    other = scope_exclusion_advisory("V01", "x(a)")
    assert fallacy_notice([]) is None
    assert fallacy_notice([other]) is None
    fallacy = Advisory(kind=AdvisoryKind.FALLACY, hetvabhasa_id="H09",
                       message="FALLACY: H09 'N' — d. Correction: c")
    assert fallacy_notice([other, fallacy]).splitlines()[1:] == [
        "- H09 'N' — d. Correction: c"]


# ── guarded: the base's own reasoning rejects the fallacy (#261) ──
#
# The pattern matches what the reasoning starts from. On the question H01 was
# written for, V11 concludes the growth is not value creation, which is H01's
# own correction, and the warning read as if the answer committed it.

@BOTH_PATHS
def test_h01_is_guarded_on_the_growth_question(business, path):
    pred = _run(business, GROWTH, path)
    assert _fallacies(pred) == []
    (guarded,) = [a for a in pred.advisories if a["kind"] == "fallacy_guarded"]
    assert guarded["hetvabhasa_id"] == "H01"
    assert guarded["vyapti_id"] is None
    assert "not_value_creation(business)" in guarded["message"]
    assert WARNING not in pred.response


def test_an_accepted_rebuttal_guards_and_an_unaccepted_one_does_not():
    ks = KnowledgeStore(
        domain_type=DomainType.CRAFT,
        vyaptis={v.id: v for v in (_vyapti("V01", ["a"], "b"),
                                   _vyapti("V02", ["c"], "d"))},
        hetvabhasas={"H01": _fallacy("H01", ["a"], rebutted_by=["d", "b"])},
    )
    af, labels = _af(ks, "a(x)")  # V01 derives b(x); nothing derives d
    (adv,) = declared_fallacy_advisories(ks, af, labels)
    assert adv.kind is AdvisoryKind.FALLACY_GUARDED
    assert "concludes b(x), against" in adv.message
    ks2 = ks.model_copy(update={"hetvabhasas": {
        "H01": _fallacy("H01", ["a"], rebutted_by=["d"])}})
    (adv,) = declared_fallacy_advisories(ks2, af, labels)
    assert adv.kind is AdvisoryKind.FALLACY


def test_a_guarded_fallacy_is_not_prepended():
    from anvikshiki_v4.engine_v4 import fallacy_notice
    guarded = Advisory(kind=AdvisoryKind.FALLACY_GUARDED, hetvabhasa_id="H01",
                       message="GUARDED: H01 'N' — x")
    assert fallacy_notice([guarded]) is None
