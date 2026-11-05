# tests/test_question_verdict.py
"""A yes/no question gets a verdict the engine derived (#197).

"Is growth alone enough to make a business viable?" came back headed "No",
written by the synthesizer: nothing recorded which fact a yes/no question asks
about. The grounder now names it (`asks`), the base maps concepts no predicate
is named for (`question_targets`: "viable" is V01's `value_creation`), and the
verdict comes from the labels:

  * yes     — the target is accepted and nothing against it is;
  * no      — something contrary to it is accepted and the target is not;
  * unknown — anything else. "Not derived" is never "no".

The target is never a supposition, or every yes/no question would answer itself.
"""

from types import SimpleNamespace

import dspy
import pytest
from pydantic import ValidationError

from anvikshiki_v4.engine_v4 import (
    AnvikshikiEngineV4,
    bind_asks,
    question_verdict,
    verdict_notice,
)
from anvikshiki_v4.grounding import (
    GroundingPipeline,
    GroundingResult,
    OntologySnippetBuilder,
    _asks_consensus,
    _asks_of,
    _checked_asks,
)
from anvikshiki_v4.schema import KnowledgeStore, QuestionTarget
from anvikshiki_v4.schema_v4 import EpistemicStatus
from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store

BUSINESS = "anvikshiki_v4/data/business_expert.yaml"
GROWTH = ("organizational_growth(business)",)
VIABLE = "value_creation(business)"


@pytest.fixture(scope="module")
def ks():
    return load_knowledge_store(BUSINESS)


def _verdict(ks, preds, asks):
    af = compile_t2(ks, [{"predicate": p, "confidence": 1.0} for p in preds])
    af.compute_grounded()
    return question_verdict(af, ks, asks)


# ── the verdict, from the labels ──────────────────────────────

def test_the_growth_question_is_no_as_a_hypothesis_given_growth(ks):
    """As measured on all seven stored live runs: V11 derives
    not_value_creation at hypothesis, and value_creation never appears."""
    v = _verdict(ks, GROWTH, VIABLE)
    assert v == {"asks": VIABLE, "answer": "no",
                 "by": "not_value_creation(business)", "status": "hypothesis",
                 "given": [["organizational_growth(business)"]],
                 "reason": "contrary_accepted"}


def test_unit_economics_makes_it_yes(ks):
    v = _verdict(ks, ("positive_unit_economics(acme)",), "value_creation(acme)")
    assert (v["answer"], v["status"], v["reason"]) == ("yes", "established", "accepted")


def test_the_stronger_side_decides_when_both_are_argued(ks):
    """V01 at established defeats V11 at hypothesis, so it is yes."""
    v = _verdict(ks, ("positive_unit_economics(b)", "organizational_growth(b)"),
                 "value_creation(b)")
    assert v["answer"] == "yes"


@pytest.mark.parametrize("preds", [
    ("superior_information(acme)",),
    # V11 excluded: the contrary is not derived, and that is not a yes
    ("organizational_growth(acme)", "small_team_direct_contact(acme)"),
], ids=["unrelated", "contrary_excluded"])
def test_not_derived_is_unknown_never_no(ks, preds):
    v = _verdict(ks, preds, "value_creation(acme)")
    assert (v["answer"], v["reason"], v["by"]) == ("unknown", "neither", None)


def test_no_target_no_verdict(ks):
    assert _verdict(ks, GROWTH, None) is None


def _fake_af(statuses, given=()):
    """A framework reduced to what the verdict reads."""
    args = {f"A{i}": SimpleNamespace(conclusion=c) for i, c in enumerate(statuses)}
    return SimpleNamespace(
        arguments=args,
        get_epistemic_status=lambda c: (statuses.get(c), None, []),
        given=lambda c: list(given),
    )


def test_both_accepted_is_unknown(ks):
    af = _fake_af({VIABLE: EpistemicStatus.HYPOTHESIS,
                   "not_value_creation(business)": EpistemicStatus.HYPOTHESIS})
    v = question_verdict(af, ks, VIABLE)
    assert (v["answer"], v["reason"], v["by"]) == (
        "unknown", "both", "not_value_creation(business)")


@pytest.mark.parametrize("status", [EpistemicStatus.OPEN, EpistemicStatus.CONTESTED])
def test_an_undecided_target_is_unknown(ks, status):
    v = question_verdict(_fake_af({VIABLE: status}), ks, VIABLE)
    assert (v["answer"], v["reason"], v["status"]) == ("unknown", "undecided", status.value)


def test_an_unaccepted_contrary_is_not_a_no(ks):
    af = _fake_af({"not_value_creation(business)": EpistemicStatus.OPEN})
    assert question_verdict(af, ks, VIABLE)["answer"] == "unknown"


def test_the_strongest_contrary_is_named(ks):
    ks2 = ks.model_copy(update={"contrariness_pairs": [["value_creation", "value_destruction"]]})
    af = _fake_af({"not_value_creation(business)": EpistemicStatus.PROVISIONAL,
                   "value_destruction(business)": EpistemicStatus.ESTABLISHED})
    v = question_verdict(af, ks2, VIABLE)
    assert (v["by"], v["status"]) == ("value_destruction(business)", "established")


def test_another_subjects_contrary_is_not_against_it(ks):
    af = _fake_af({"not_value_creation(rival)": EpistemicStatus.ESTABLISHED})
    assert question_verdict(af, ks, VIABLE)["answer"] == "unknown"


def test_the_target_takes_the_question_facts_spelling():
    assert bind_asks("value_creation(the_business)", list(GROWTH)) == VIABLE
    assert bind_asks("value_creation(acme)", list(GROWTH)) == "value_creation(acme)"
    assert bind_asks(None, list(GROWTH)) is None


# ── what the reader sees ──────────────────────────────────────

NO = {"asks": VIABLE, "answer": "no", "by": "not_value_creation(business)",
      "status": "hypothesis", "given": [["organizational_growth(business)"]],
      "reason": "contrary_accepted"}


def test_a_no_is_stated_with_what_it_rests_on():
    assert verdict_notice(NO, "No — growth alone is not enough.") == (
        "Verdict: No — not_value_creation(business) is accepted (hypothesis), "
        "against value_creation(business); this holds only if what your "
        "question assumes is true: organizational_growth(business).")


def test_a_disagreeing_opening_is_called_out():
    notice = verdict_notice(NO, "Yes, growth is enough.")
    assert notice.splitlines()[1] == (
        'The "Yes" that opens the answer below disagrees with this verdict; '
        "it is the model's reading.")


def test_a_yes_without_suppositions():
    v = {"asks": VIABLE, "answer": "yes", "by": VIABLE, "status": "established",
         "given": [], "reason": "accepted"}
    assert verdict_notice(v, "It is.") == (
        "Verdict: Yes — value_creation(business) is accepted (established).")


@pytest.mark.parametrize("reason, by, status, text", [
    ("neither", None, None, "my knowledge base derives neither "
     "value_creation(business) nor anything against it"),
    ("both", "not_value_creation(business)", "hypothesis",
     "my knowledge base accepts both value_creation(business) and "
     "not_value_creation(business)"),
    ("undecided", None, "open", "value_creation(business) is open, neither "
     "accepted nor rejected"),
])
def test_unknown_says_why(reason, by, status, text):
    v = {"asks": VIABLE, "answer": "unknown", "by": by, "status": status,
         "given": [], "reason": reason}
    assert verdict_notice(v, "It depends.") == f"Verdict: unknown — {text}."
    assert verdict_notice(v, "No — it is not.").splitlines()[1] == (
        'The "No" that opens the answer below is the model\'s reading, '
        "not a verdict the engine reached.")


def test_without_a_target_the_stopgap_note_stands():
    assert verdict_notice(None, "The derived reasoning suggests.") is None
    assert verdict_notice(None, "No — it is not.").startswith(
        "Note: my knowledge base does not decide yes or no here.")


# ── the grounder's target ─────────────────────────────────────

@pytest.mark.parametrize("raw, expected", [
    ("value_creation(acme)", "value_creation(acme)"),
    ("  'value_creation(acme)' ", "value_creation(acme)"),
    ("", None), ("None", None), ("null", None), ("n/a", None), (None, None),
])
def test_a_members_none_is_folded(raw, expected):
    assert _asks_of(SimpleNamespace(asks=raw)) == expected


@pytest.mark.parametrize("values, expected", [
    (["v(a)", "v(a)", "v(a)", None, None], "v(a)"),
    (["v(a)", "v(the_a)", "v(a)"], "v(a)"),                 # spellings pool
    (["v(a)", "v(a)", None, None, None], None),             # no majority
    (["v(a)", "v(a)", None, None], None),                   # half is not a majority
    (["v(a)", "w(a)", "x(a)"], None),                        # split
    ([None, None, None], None),
])
def test_the_ensemble_votes_on_the_target(values, expected):
    assert _asks_consensus(values) == expected


def test_a_target_must_be_concluded_and_bound(ks):
    assert _checked_asks(VIABLE, ks) == (VIABLE, None)
    # only an antecedent: no rule concludes it
    assert _checked_asks("positive_unit_economics(acme)", ks) == (
        None, "positive_unit_economics(acme)")
    assert _checked_asks("value_creation", ks) == (None, "value_creation")
    assert _checked_asks("made_up(acme)", ks) == (None, "made_up(acme)")
    assert _checked_asks(None, ks) == (None, None)


def test_the_grounder_is_told_what_viable_means(ks):
    snippet = OntologySnippetBuilder().build(ks)
    v01 = ks.vyaptis["V01"].statement
    assert ("  - asking whether something is viable, survives, a sustainable "
            f"business: use value_creation (RULE V01: {v01})") in snippet
    assert "value_creation" in snippet.split("Concluded names: ")[1].splitlines()[0]
    assert "positive_unit_economics" not in snippet.split(
        "Concluded names: ")[1].splitlines()[0]


class _Grounder:
    """Stands in for the GroundQuery module: one reply per rollout."""

    def __init__(self, replies):
        self.replies = list(replies)

    def __call__(self, **kw):
        return self.replies.pop(0)


def _reply(asks, preds=GROWTH):
    return dspy.Prediction(reasoning="", predicates=list(preds),
                           relevant_vyaptis=[], asks=asks)


@pytest.mark.parametrize("mode, replies, asks, rejected", [
    ("minimal", [_reply(VIABLE)], VIABLE, None),
    ("minimal", [_reply("positive_unit_economics(business)")], None,
     "positive_unit_economics(business)"),
    ("minimal", [_reply("")], None, None),
    ("partial", [_reply(VIABLE), _reply(VIABLE), _reply("")], VIABLE, None),
    ("partial", [_reply(VIABLE), _reply(""), _reply("")], None, None),
])
def test_both_grounding_modes_carry_the_target(ks, mode, replies, asks, rejected):
    from anvikshiki_v4.grounding import GroundingMode
    pipe = GroundingPipeline(knowledge_store=ks, mode=GroundingMode[mode.upper()])
    pipe.grounder = _Grounder(replies)
    result = pipe("q")
    assert (result.asks, result.asks_rejected) == (asks, rejected)


# ── the base's mapping ────────────────────────────────────────

@pytest.mark.parametrize("target, match", [
    ({"concept": "viable", "predicate": "positive_unit_economics", "basis": "V01"},
     "no rule concludes"),
    ({"concept": "viable", "predicate": "value_creation", "basis": "V99"},
     "not a rule"),
])
def test_a_bad_question_target_is_refused(ks, target, match):
    with pytest.raises(ValidationError, match=match):
        KnowledgeStore(**{**ks.model_dump(), "question_targets": [target]})


def test_bases_without_targets_load_unchanged():
    for path in ("anvikshiki_v4/data/copywriting_expert.yaml",
                 "anvikshiki_v4/data/nonfiction_expert.yaml"):
        assert load_knowledge_store(path).question_targets == []


# ── through the engine, both paths ────────────────────────────

class _Grounding:
    def __init__(self, predicates, asks):
        self._result = GroundingResult(
            predicates=list(predicates), confidence=1.0, disputed=[],
            warnings=[], advisories=[], clarification_needed=False, asks=asks,
        )

    def __call__(self, query):
        return self._result


def _run(ks, preds, asks, text, path):
    engine = AnvikshikiEngineV4(knowledge_store=ks,
                                grounding_pipeline=_Grounding(preds, asks))
    engine.synthesizer = lambda **kw: dspy.Prediction(response=text, sources_cited=[])
    return (engine.forward("q", retrieved_chunks=[]) if path == "forward"
            else engine.forward_with_coverage("q"))


BOTH_PATHS = pytest.mark.parametrize("path", ["forward", "forward_with_coverage"])


@BOTH_PATHS
def test_the_growth_answer_carries_the_engines_no(ks, path):
    text = "No — growth alone is not enough."
    pred = _run(ks, GROWTH, VIABLE, text, path)
    assert pred.verdict == NO
    blocks = pred.response.split("\n\n")
    assert blocks[-1] == text
    assert blocks[-2] == verdict_notice(NO, text)
    assert "does not decide yes or no" not in pred.response


@BOTH_PATHS
def test_the_target_is_not_a_supposition(ks, path):
    """A question that states its own target does not answer itself yes."""
    pred = _run(ks, ("value_creation(acme)",), "value_creation(acme)", "Yes.", path)
    assert pred.verdict["answer"] == "unknown"
    assert "value_creation(acme)" not in pred.provenance
    assert 'The "Yes" that opens the answer below' in pred.response


@BOTH_PATHS
def test_no_target_keeps_the_old_answer(ks, path):
    pred = _run(ks, GROWTH, None, "No — it is not.", path)
    assert pred.verdict is None
    assert "Verdict:" not in pred.response
    assert "does not decide yes or no here" in pred.response


@BOTH_PATHS
def test_a_differently_spelt_target_still_meets_its_contrary(ks, path):
    pred = _run(ks, GROWTH, "value_creation(the_business)", "No.", path)
    assert pred.verdict == NO
