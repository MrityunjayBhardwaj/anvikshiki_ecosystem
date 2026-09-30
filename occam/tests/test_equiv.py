"""The same-answer judge (#172): what merges, under which lens, and what never does.

Real wordings from run 2 are used where they carry the point: q01's question
contains the year one answer repeats, q03's asks for the date.
"""

import json

import pytest

from occam.answer import Artifact, Params, canonical, replay, run
from occam.equiv import EquivResult, Pair, Verdict, equiv_from_replies, judge_same, veto
from occam.model import ScriptedModel
from occam.status import derive
from occam.tests.test_answer import AS_OF, QUERIES, SUPPORT_ALL, VIABLE, attacks, argue_reply, wiki
from occam.tests.test_status import LONG1, NOW, q, second, world
from occam.types import Status

Q01 = "Why did the Challenger space shuttle break apart in 1986?"
Q03 = "Who proposed the theory of continental drift, and when?"


# ── the veto: mechanical, and only ever a refusal ─────────────

def test_a_number_the_question_asked_about_is_context_under_the_question_lens():
    a = "Challenger broke apart in 1986 because its O-ring seals failed in the cold."
    b = "Challenger broke apart because its O-ring seals failed in the cold."
    assert veto(a, b, "question", Q01) == ""
    assert veto(a, b, "claim", Q01) == "numbers differ: 1986"


def test_a_number_the_question_did_not_supply_still_vetoes():
    a = "Alfred Wegener proposed the theory of continental drift on 6 January 1912."
    b = "Alfred Wegener proposed the theory of continental drift in 1912."
    assert veto(a, b, "question", Q03) == "numbers differ: 6"


@pytest.mark.parametrize("a,b", [
    ("Water boils at 100 degrees at sea level.", "Water boils at 50 degrees at sea level."),
    ("The O-rings caused the failure.", "The O-rings did not cause the failure."),
    ("The O-rings caused the failure.", "The O-rings didn't cause the failure."),
    ("The seals held.", "The seals never held."),
])
def test_number_and_negation_swaps_are_refused_under_both_lenses(a, b):
    assert veto(a, b, "question", "What happened?") and veto(a, b, "claim", "What happened?")


def test_nothing_vetoed_means_nothing_decided():
    assert veto("It rose.", "It fell.", "claim", "?") == ""       # the judge's job, not the veto's


# ── the judge: both orders, doubt keeps apart ─────────────────

def pair(pid="P0000", lens="question", a="a", b="b", v=""):
    return Pair(id=pid, lens=lens, a=a, b=b, text_a=a, text_b=b, veto=v)


def v(verdict, differs_on=""):
    return json.dumps({"verdict": verdict, "differs_on": differs_on, "asked_by_question": True})


SAME = v("same")


def test_a_merge_needs_same_in_both_orders():
    p = pair()
    assert equiv_from_replies([SAME, SAME], [p]).verdicts[0].same
    one = equiv_from_replies([SAME, v("different", "date")], [p])
    assert not one.verdicts[0].same
    assert one.verdicts[0].why_apart == "the two orders disagreed (same / different)"


@pytest.mark.parametrize("replies", [
    [v("cannot_tell"), v("cannot_tell")],
    ["not json", SAME],
    [SAME],                                                    # second order missing
    [json.dumps({"verdict": "identical"}), SAME],              # a verdict it was never offered
])
def test_doubt_malformed_or_missing_never_merges(replies):
    assert not equiv_from_replies(replies, [pair()]).verdicts[0].same


def test_a_vetoed_pair_is_never_sent_to_the_judge():
    m = ScriptedModel([])                    # any call would raise
    assert judge_same(m, Q01, [pair(v="numbers differ: 50")]) == [] and m.prompts == []


def test_the_judge_sees_the_question_the_lens_and_both_orders():
    m = ScriptedModel(["{}", "{}"])
    judge_same(m, Q03, [Pair(id="P0000", lens="question", a="x", b="y", text_a="X-text", text_b="Y-text")])
    first, second_ = m.prompts
    assert Q03 in first and "LENS question" in first
    assert first.index("X-text") < first.index("Y-text")
    assert second_.index("Y-text") < second_.index("X-text")


# ── grouping: no chaining ────────────────────────────────────

def verdict(a, b, same):
    v = "same" if same else "different"
    return Verdict(pair=pair(a=a, b=b), forward=v, backward=v)


def test_no_chaining_through_a_middle_answer():
    r = EquivResult(verdicts=(verdict("a", "b", True), verdict("b", "c", True),
                              verdict("a", "c", False)), malformed=())
    g = r.groups("question", ["a", "b", "c"])
    assert g["a"] == g["b"] and g["c"] != g["a"]


def test_a_group_whose_every_pair_is_same_merges():
    r = EquivResult(verdicts=(verdict("a", "b", True), verdict("b", "c", True),
                              verdict("a", "c", True)), malformed=())
    assert len(set(r.groups("question", ["a", "b", "c"]).values())) == 1


def test_lenses_do_not_leak_into_each_other():
    r = EquivResult(verdicts=(verdict("a", "b", True),), malformed=())    # question lens
    assert r.groups("claim", ["a", "b"]) == {"a": "a", "b": "b"}


# ── end to end: three wordings of one answer ─────────────────

WORDINGS = ["Viability requires LTV to exceed CAC.",
            "A business is only viable when LTV exceeds CAC.",
            "LTV must exceed CAC for a business to be viable."]


def run_with(same_replies, judge_same_on=True):
    argue = [argue_reply([{**VIABLE, "conclusion": w}], "q1") for w in WORDINGS]
    model = ScriptedModel([QUERIES] + argue + [SUPPORT_ALL] + [attacks()] * 3 + same_replies)
    ans, _ = run("Is growth alone enough to make a business viable?", model,
                 params=Params(k_argue=3, k_attack=3, judge_same=judge_same_on),
                 as_of=AS_OF, http_get=wiki)
    return ans, model


def all_same(n):
    return [SAME] * (2 * n)


def test_three_wordings_judged_same_are_one_position_with_three_samples():
    ans, model = run_with(all_same(3))
    assert len(ans.positions) == 1 and ans.positions[0]["samples"] == 3
    assert ans.counters["agree_frac"].n == 3
    assert sorted(ans.positions[0]["wordings"]) == sorted(WORDINGS)
    assert ans.counters["same_question_merged"].n == 3 and model._replies == []


def test_the_merge_replays_with_no_model():
    argue = [argue_reply([{**VIABLE, "conclusion": w}], "q1") for w in WORDINGS]
    model = ScriptedModel([QUERIES] + argue + [SUPPORT_ALL] + [attacks()] * 3
                          + all_same(3))
    ans, artifact = run("Is growth alone enough to make a business viable?", model,
                        params=Params(k_argue=3, k_attack=3, judge_same=True),
                        as_of=AS_OF, http_get=wiki)
    stored = Artifact.model_validate_json(artifact.model_dump_json())
    assert len(stored.same_replies) == 6
    assert canonical(replay(stored)) == canonical(ans)


def test_kept_apart_says_why():
    ans, _ = run_with([v("different", "adds 'only'")] * 2 + [SAME] * 4)
    whys = [k["why"] for p in ans.positions for k in p["kept_apart"]]
    assert "adds 'only'" in whys
    assert ans.counters["agree_frac"].n < 3


def test_without_the_judge_nothing_new_appears():
    """Every artifact made before #172 carries judge_same=False: exact-wording
    groups and no new fields, so it replays exactly as it did."""
    ans, model = run_with([], judge_same_on=False)
    assert len(ans.positions) == 3
    assert all("wordings" not in p for p in ans.positions)
    assert not any(k.startswith("same_") for k in ans.counters)


def test_the_judges_reply_cannot_set_a_status():
    sneaky = json.dumps({"verdict": "same", "status": "established"})
    ans, _ = run_with([sneaky] * 6)
    plain, _ = run_with(all_same(3))
    assert ans.status == plain.status and canonical(ans) == canonical(plain)


# ── corroboration: only the claim lens, only what was judged same ──

TEXT3 = "A different page altogether. Customer lifetime value has to exceed what it costs to acquire the customer."
REWORDED = "Customer lifetime value has to exceed what it costs to acquire the customer."


def _two_host_wordings():
    store, s = world()
    f = second(store, text=TEXT3)
    return store, [q("Q", s, LONG1), q("R", f, REWORDED)]


def test_two_hosts_in_different_words_corroborate_only_when_judged_same_under_the_claim_lens():
    from occam.argue import norm_conclusion
    store, args = _two_host_wordings()
    a, b = norm_conclusion(LONG1), norm_conclusion(REWORDED)
    assert derive(args, [], store, as_of=NOW).statuses["Q"].status == Status.HYPOTHESIS
    joined = {a: a, b: a}
    r = derive(args, [], store, as_of=NOW, claim_group=joined)
    assert r.statuses["Q"].status == Status.ESTABLISHED and r.statuses["R"].status == Status.ESTABLISHED


def test_a_question_lens_merge_never_reaches_corroboration():
    """Replay builds claim groups from claim-lens verdicts only."""
    r = EquivResult(verdicts=(verdict("a", "b", True),), malformed=())    # question lens
    assert r.groups("claim", ["a", "b"]) == {"a": "a", "b": "b"}


# ── each comparison fresh (#174) ─────────────────────────────

def test_every_call_sees_one_pair_and_nothing_else():
    # Statements distinctive enough that no prompt wording can contain them.
    A, B, C, D, E, F = (f"Statement {w} zq." for w in
                        ("alpha", "bravo", "charlie", "delta", "echo", "foxtrot"))
    ps = [pair("P0000", a=A, b=B), pair("P0001", a=C, b=D, v="numbers differ: 5"),
          pair("P0002", a=E, b=F)]
    m = ScriptedModel([SAME] * 4)
    judge_same(m, "Q?", ps)
    assert len(m.prompts) == 4                               # 2 open pairs x 2 orders
    for prompt in m.prompts:
        assert prompt.count("\nX: ") == 1 and prompt.count("\nY: ") == 1
    assert f"X: {A}" in m.prompts[0] and f"X: {B}" in m.prompts[1] and f"X: {E}" in m.prompts[2]
    own = [{A, B}, {A, B}, {E, F}, {E, F}]
    for prompt, mine in zip(m.prompts, own):
        for other in {A, B, C, D, E, F} - mine:
            assert other not in prompt, "a prompt carries another pair's statement"


def test_one_malformed_reply_costs_only_its_own_pair():
    ps = [pair("P0000", a="a", b="b"), pair("P0001", a="c", b="d")]
    r = equiv_from_replies(["garbage", v("different"), SAME, SAME], ps)
    assert not r.verdicts[0].same and r.verdicts[1].same     # P0001 still reads replies 2 and 3
    assert r.malformed == ((0, "reply for P0000 is not a JSON object with a verdict"),)
