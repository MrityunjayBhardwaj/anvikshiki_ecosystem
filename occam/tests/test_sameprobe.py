"""The same-answer judge's probe (#172) and rejudging stored runs.

The flips are run 2's real wordings; their labels come from how they were
made, so the laws pin the construction, not a judgement.
"""

import hashlib
import json

import pytest

from occam.answer import Artifact, Params, canonical, rejudge, replay, run
from occam.model import ScriptedModel
from occam.sameprobe import (ProbePair, flip_pairs, flips, kill_criteria, paws_pairs,
                             run_probe, score)
from occam.equiv import Pair
from occam.tests.test_answer import AS_OF, QUERIES, SUPPORT_ALL, VIABLE, attacks, argue_reply, wiki
from occam.tests.test_equiv import SAME, WORDINGS, all_same, run_with, v

Q01 = "Why did the Challenger space shuttle break apart in 1986?"
Q03 = "Who proposed the theory of continental drift, and when?"
Q06 = "When and where was the first successful powered airplane flight?"
Q09 = "What was the Rosetta Stone used to decipher?"
C01 = ("Challenger broke apart in 1986 because its O-ring seals failed in the cold, leading "
       "to a chain of structural failures that subjected the orbiter to fatal aerodynamic forces.")
C03 = "Alfred Wegener proposed the theory of continental drift on 6 January 1912."
C06 = ("The first successful powered airplane flight occurred on December 17, 1903, four miles "
       "south of Kitty Hawk, North Carolina, at what is now known as Kill Devil Hills.")
C09 = "The Rosetta Stone was used to decipher the Egyptian scripts."


def kinds(question, conclusion):
    return {(k, lens) for k, _, lenses in flips(question, conclusion) for lens in lenses}


# ── labels by construction ────────────────────────────────────

def test_a_date_flip_is_labelled_under_the_question_lens_only_when_the_question_asks_when():
    assert ("number swapped", "question") in kinds(Q03, C03)      # "…, and when?"
    assert ("number swapped", "claim") in kinds(Q01, C01)
    assert ("number swapped", "question") not in kinds(Q01, C01)  # 1986 is not asked


def test_cause_and_effect_is_reversed_only_on_why_or_cause_questions():
    assert ("cause and effect reversed", "question") in kinds(Q01, C01)
    reversed_ = [t for k, t, _ in flips(Q01, C01) if k == "cause and effect reversed"]
    assert reversed_ == ["Its O-ring seals failed in the cold, leading to a chain of structural "
                         "failures that subjected the orbiter to fatal aerodynamic forces "
                         "because Challenger broke apart in 1986."]
    assert not any(k == "cause and effect reversed" for k, _ in
                   kinds("Who wrote it?", "It failed because it was cold."))


def test_a_framing_clause_stays_in_front_when_cause_and_effect_are_reversed():
    q = "What caused the extinction of the dinosaurs according to the leading hypothesis?"
    c = "According to the leading hypothesis, the extinction was caused by an asteroid."
    assert [t for k, t, _ in flips(q, c) if k == "cause and effect reversed"] == [
        "According to the leading hypothesis, an asteroid was caused by the extinction."]


def test_not_is_inserted_in_the_main_clause_only():
    """q06's first copula sits in "at what is now known as …": negating it
    changes a detail, not the answer, so it would not be `different` by
    construction under the question lens."""
    assert not any(k == "not inserted" for k, _ in kinds(Q06, C06))
    assert [t for k, t, _ in flips(Q09, C09) if k == "not inserted"] == [
        "The Rosetta Stone was not used to decipher the Egyptian scripts."]


def test_antonyms_are_claim_lens_only():
    assert {lens for k, lens in kinds(Q06, C06) if k == "antonym swapped"} == {"claim"}
    texts = [t for k, t, _ in flips(Q06, C06) if k == "antonym swapped"]
    assert any("four miles north of" in t for t in texts)
    assert any("South Carolina" in t for t in texts)


def test_every_flip_changes_the_text():
    for q, c in ((Q01, C01), (Q03, C03), (Q06, C06), (Q09, C09)):
        assert all(t != c for _, t, _ in flips(q, c))


def test_number_and_not_flips_are_vetoed_and_the_others_reach_the_judge():
    """The judge's own figure rests on the flips the veto cannot see."""
    ps = flip_pairs([("q01", Q01, C01), ("q03", Q03, C03), ("q09", Q09, C09)])
    for p in ps:
        assert bool(p.pair.veto) == (p.kind in ("number swapped", "not inserted")), p
    assert all(p.expected == "different" and p.source == "flip" for p in ps)
    assert len({p.pair.id for p in ps}) == len(ps)


# ── PAWS: the registered bytes, the registered draw ─────────────

def _paws_file(tmp_path, monkeypatch, n_each=5):
    rows = [{"id": i, "label": i % 2, "sentence1": f"s{i} one", "sentence2": f"s{i} two"}
            for i in range(1, 4 * n_each + 1)]
    f = tmp_path / "paws.jsonl"
    f.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    monkeypatch.setattr("occam.sameprobe.PAWS_SHA256",
                        hashlib.sha256(f.read_bytes()).hexdigest())
    return f


def test_paws_refuses_bytes_other_than_the_registered_ones(tmp_path):
    f = tmp_path / "paws.jsonl"
    f.write_text('{"id": 1, "label": 1, "sentence1": "a", "sentence2": "b"}\n')
    with pytest.raises(ValueError, match="registered"):
        paws_pairs(f, n=1)


def test_paws_draw_is_seeded_balanced_and_claim_lens(tmp_path, monkeypatch):
    f = _paws_file(tmp_path, monkeypatch)
    a, b = paws_pairs(f, n=3), paws_pairs(f, n=3)
    assert [p.origin for p in a] == [p.origin for p in b]
    assert [p.expected for p in a] == ["same"] * 3 + ["different"] * 3
    assert {p.pair.lens for p in a} == {"claim"} and {p.question for p in a} == {""}
    assert [p.origin for p in paws_pairs(f, n=3, seed=1)] != [p.origin for p in a]


# ── running and scoring ───────────────────────────────────────

class ByPrompt:
    """Answers from the prompt, so replies do not depend on call order — the
    probe runs its calls concurrently."""
    name = "by-prompt"

    def __init__(self, same_if, fail_if=None):
        self.same_if, self.fail_if = same_if, fail_if

    def complete(self, prompt, *, temperature):
        if self.fail_if and self.fail_if in prompt:
            raise RuntimeError("HTTP 500")
        return SAME if self.same_if in prompt else v("different", "x")


def probe_pairs():
    def pp(pid, a, b, expected, source="flip", veto=""):
        return ProbePair(pair=Pair(id=pid, lens="claim", a=a, b=b, text_a=a, text_b=b,
                                   veto=veto),
                         question="", expected=expected, source=source, kind="k", origin="o")
    return [pp("F0", "zqalpha one", "zqalpha two", "different"),
            pp("F1", "zqbeta one", "zqbeta two", "different", veto="numbers differ: 1"),
            pp("W0", "zqgamma one", "zqgamma two", "same", source="paws"),
            pp("W1", "zqdelta one", "zqdelta two", "different", source="paws")]


def test_replies_land_on_their_own_pair_whatever_order_the_calls_finish():
    run_ = run_probe(ByPrompt("zqgamma"), probe_pairs(), as_of="t", workers=4)
    assert len(run_.replies) == 6                    # the vetoed pair is never asked
    _, rows = score(run_)
    merged = {(r["source"], r["expected"]): r["merged"] for r in rows}
    assert merged == {("flip", "different"): 0, ("paws", "same"): 1, ("paws", "different"): 0}
    assert kill_criteria(rows) == []


def test_any_flip_merged_is_a_stop():
    _, rows = score(run_probe(ByPrompt("zqalpha"), probe_pairs(), as_of="t", workers=1))
    assert any(g.startswith("STOP") and "flip" in g for g in kill_criteria(rows))


def test_paws_allows_five_wrong_merges_of_its_non_paraphrases_and_stops_at_six():
    def neg(i, merge):
        a, b = f"zqx{i} first", f"zqx{i} {'zqmerge' if merge else 'second'}"
        return ProbePair(pair=Pair(id=f"W{i}", lens="claim", a=a, b=b, text_a=a, text_b=b),
                         question="", expected="different", source="paws", kind="k", origin="o")
    for n, stops in ((5, False), (6, True)):
        pairs = [neg(i, i < n) for i in range(100)]
        _, rows = score(run_probe(ByPrompt("zqmerge"), pairs, as_of="t"))
        assert sum(r["merged"] for r in rows) == n
        assert bool(kill_criteria(rows)) is stops


def test_a_call_that_never_returned_is_not_counted_as_the_judge_keeping_pairs_apart():
    run_ = run_probe(ByPrompt("zqnever", fail_if="zqdelta"), probe_pairs(), as_of="t",
                     retries=1)
    assert len(run_.failures) == 2
    _, rows = score(run_)
    neg = [r for r in rows if r["source"] == "paws" and r["expected"] == "different"][0]
    assert (neg["unanswered"], neg["judged"], neg["apart"]) == (1, 0, 0)
    assert any(g.startswith("INCOMPLETE") for g in kill_criteria(rows))


# ── rejudging a stored run ────────────────────────────────────

def judge_off_run():
    argue = [argue_reply([{**VIABLE, "conclusion": w}], "q1") for w in WORDINGS]
    return run("Is growth alone enough to make a business viable?",
               ScriptedModel([QUERIES] + argue + [SUPPORT_ALL] + [attacks()] * 3),
               params=Params(k_argue=3, k_attack=3, judge_same=False),
               as_of=AS_OF, http_get=wiki)


def test_rejudging_a_stored_run_gives_what_a_live_run_with_the_judge_gives():
    _, off = judge_off_run()
    ans, judged = rejudge(off, ScriptedModel(all_same(3)))
    live, _ = run_with(all_same(3))
    assert canonical(ans) == canonical(live)
    assert canonical(replay(Artifact.model_validate_json(judged.model_dump_json()))) \
        == canonical(ans)


def test_rejudging_changes_nothing_but_the_judge():
    _, off = judge_off_run()
    _, judged = rejudge(off, ScriptedModel(all_same(3)))
    a, b = off.model_dump(), judged.model_dump()
    assert b["params"].pop("judge_same") is True and a["params"].pop("judge_same") is False
    assert b.pop("same_replies") and a.pop("same_replies") == ()
    assert a == b


def test_rejudging_refuses_a_judged_run_and_a_different_model():
    _, off = judge_off_run()
    _, judged = rejudge(off, ScriptedModel(all_same(3)))
    with pytest.raises(ValueError, match="already"):
        rejudge(judged, ScriptedModel([]))
    with pytest.raises(ValueError, match="misattribute"):
        rejudge(off, ScriptedModel([], name="another-model"))


def test_same_in_one_order_only_does_not_merge_and_is_counted_as_disagreeing():
    """X/Y says same, Y/X says different: a first-position bias, not agreement."""
    pairs = [ProbePair(pair=Pair(id="F0", lens="claim", a="zqfirst", b="zqsecond",
                                 text_a="zqfirst", text_b="zqsecond"),
                       question="", expected="different", source="flip", kind="k", origin="o")]
    _, rows = score(run_probe(ByPrompt("X: zqfirst"), pairs, as_of="t"))
    assert (rows[0]["merged"], rows[0]["orders_disagree"]) == (0, 1)
    assert kill_criteria(rows) == []


class Recording(ScriptedModel):
    def __init__(self, replies):
        super().__init__(replies)
        self.temperatures = []

    def complete(self, prompt, *, temperature):
        self.temperatures.append(temperature)
        return super().complete(prompt, temperature=temperature)


def test_rejudging_asks_at_the_temperature_the_run_recorded():
    argue = [argue_reply([{**VIABLE, "conclusion": w}], "q1") for w in WORDINGS]
    _, off = run("Is growth alone enough to make a business viable?",
                 ScriptedModel([QUERIES] + argue + [SUPPORT_ALL] + [attacks()] * 3),
                 params=Params(k_argue=3, k_attack=3, judge_same=False, t_same=0.3),
                 as_of=AS_OF, http_get=wiki)
    m = Recording(all_same(3))
    rejudge(off, m)
    assert m.temperatures == [0.3] * 6


# ── an empty reply is a call that returned nothing, not a verdict (#175) ──

class FakeHTTP:
    """Serves OpenRouter response bodies in order and counts the calls."""

    def __init__(self, contents, finish="stop"):
        self.contents, self.finish, self.calls = list(contents), finish, 0

    def __call__(self, req, timeout):
        import io
        self.calls += 1
        body = {"choices": [{"message": {"content": self.contents.pop(0)},
                             "finish_reason": self.finish}]}

        class R(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False
        return R(json.dumps(body).encode())


def test_an_empty_reply_is_asked_again_and_a_real_one_is_returned(monkeypatch):
    from occam.model import OpenRouterModel
    http = FakeHTTP(["", "  \n", SAME])
    monkeypatch.setattr("occam.model.urllib.request.urlopen", http)
    assert OpenRouterModel(api_key="k").complete("p", temperature=0) == SAME
    assert http.calls == 3


def test_a_reply_that_stays_empty_fails_the_call_and_says_why(monkeypatch):
    from occam.model import OpenRouterModel
    http = FakeHTTP([None, "", ""], finish="length")
    monkeypatch.setattr("occam.model.urllib.request.urlopen", http)
    with pytest.raises(RuntimeError, match="empty reply 3 times.*'length'"):
        OpenRouterModel(api_key="k").complete("p", temperature=0)
    assert http.calls == 3


def test_a_stored_empty_reply_scores_as_unanswered_not_kept_apart():
    """How amendment 3's first run stored its three empty replies: as "" with
    no failure recorded. Scoring reads the bytes, so it is unanswered."""
    run_ = run_probe(ByPrompt("zqnever"), probe_pairs(), as_of="t")
    replies = list(run_.replies)
    replies[0] = ""                                       # F0, X/Y
    old = run_.model_copy(update={"replies": tuple(replies)})
    assert old.failures == ()
    _, rows = score(old)
    flip = [r for r in rows if r["source"] == "flip"][0]   # F0 asked, F1 vetoed
    assert (flip["vetoed"], flip["unanswered"], flip["judged"], flip["apart"]) == (1, 1, 0, 0)
    assert any(g.startswith("INCOMPLETE") for g in kill_criteria(rows))
