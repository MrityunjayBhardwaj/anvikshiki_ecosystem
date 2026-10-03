"""What an answer shows its reader (#201): the chain down to the bytes with
each link's check, what the status means, the question's details, and a
blind view for labelling. All read when shown, never stored, so every stored
answer replays as it was."""

import json

from occam.__main__ import MEANING, _show
from occam.answer import Params, canonical, contradicted_quotes, replay, run
from occam.model import ScriptedModel
from occam.tests.test_answer import (AGREE, AS_OF, GROW_INFER, GROWTH, INFER, NO_ATTACKS,
                                     QUERIES, SUPPORT_ALL, VIABLE, _two_sides, argue_reply, ask,
                                     attacks, wiki)
from occam.types import Status


def ask_q(question, argue_replies, attack_replies=NO_ATTACKS):
    model = ScriptedModel([QUERIES] + list(argue_replies) + [SUPPORT_ALL] + list(attack_replies))
    return run(question, model, as_of=AS_OF, http_get=wiki,
               params=Params(k_argue=len(argue_replies), k_attack=len(attack_replies)))


def shown(capsys, ans, art=None, blind=False):
    _show(ans, art, blind=blind)
    return capsys.readouterr().out


# ── the chain, down to the bytes ───────────────────────────

def test_every_link_down_to_the_bytes_is_printed_with_its_own_check(capsys):
    ans, art = ask(AGREE, NO_ATTACKS)
    out = shown(capsys, ans, art)
    leaf = ans.derivation["sub_arguments"][0]
    sp = leaf["span"]
    assert f'"{VIABLE["quote"]}"' in out
    assert f"verbatim: ok · support: supports · {sp['url']} characters {sp['start']}–{sp['end']}" in out
    assert f"text sha256 {sp['text_sha256']} · snapshot {sp['snapshot_id']}" in out   # whole, never cut
    assert f"{ans.answer_id} inference [hypothesis]: {ans.conclusion}" in out
    assert out.count("attacked by: none") == 2                # said for each link, zero included


MUTUAL = [attacks(("A0002", "A0000", "undermining"), ("A0000", "A0002", "undermining"))] * 3


def test_an_attack_on_a_link_says_whether_it_succeeded(capsys):
    """#193's fixture: two quotes defeat each other and the answer rests on
    one. And an inference attacking a verbatim quote fails: said as failed."""
    ans, art = ask(_two_sides(), MUTUAL)
    assert "attacked by A0002 (undermining): succeeded — r" in shown(capsys, ans, art)
    verbatim = {**VIABLE, "conclusion": VIABLE["quote"]}
    ans, art = ask([argue_reply([verbatim, INFER], "i1")] * 2 +
                   [argue_reply([GROWTH, GROW_INFER], "i2")],
                   [attacks(("A0003", "A0000", "undermining"))] * 3)
    assert "attacked by A0003 (undermining): failed — r" in shown(capsys, ans, art)


def test_support_says_not_judged_apart_from_not_shown(capsys):
    """'The judge was never asked' and 'this view had no stored run to look
    in' are different facts and must not print alike."""
    ans, art = ask(AGREE, NO_ATTACKS)
    unjudged = art.model_copy(update={"support_replies": ()})
    assert "support: not judged" in shown(capsys, replay(unjudged), unjudged)
    assert "support: not shown (no stored run given)" in shown(capsys, ans)


def test_a_step_two_others_rest_on_is_shown_once_and_counted_once(capsys):
    both = {"id": "i2", "kind": "inference", "from": ["i1", "q1"],
            "conclusion": "So growth is not what makes it viable."}
    ans, art = ask([argue_reply([VIABLE, INFER, both], "i2")] * 3, NO_ATTACKS)
    out = shown(capsys, ans, art)
    q1 = ans.derivation["sub_arguments"][0]["sub_arguments"][0]["id"]
    assert out.count(f"{q1} (shown above)") == 1
    assert out.count(f'"{VIABLE["quote"]}"') == 1
    assert contradicted_quotes(ans)[1] == 1


# ── what the status means ──────────────────────────────────

def test_every_status_has_a_meaning():
    assert set(MEANING) == set(Status)


def test_the_meaning_follows_the_status_not_the_wording_of_its_bounds(capsys):
    ans, art = ask(AGREE, NO_ATTACKS)
    assert f"meaning: {MEANING[Status.HYPOTHESIS]}" in shown(capsys, ans, art)


# ── the question's details ─────────────────────────────────

def test_a_detail_the_question_supplied_and_no_quote_states_is_named(capsys):
    q1940 = dict(VIABLE, conclusion="In 2026, viability requires LTV to exceed CAC.")
    ans, art = ask_q("Is growth alone enough to make a business viable in 2026 with 3 founders?",
                     [argue_reply([q1940], "q1")] * 3)
    out = shown(capsys, ans, art)
    assert ("question detail 2026: carried by the answer, but no quote beneath it states "
            "it: the question supplied it, nothing observed it") in out
    assert "question detail 3: not carried by the answer" in out


def test_a_question_with_no_number_says_the_check_cannot_fire(capsys):
    ans, art = ask(AGREE, NO_ATTACKS)
    assert "the question has no whole number, so this check cannot fire" in shown(capsys, ans, art)


# ── the blind view, for labelling ──────────────────────────

def test_the_blind_view_shows_the_chain_and_nothing_the_pipeline_decided(capsys):
    ans, art = ask(_two_sides(), MUTUAL)
    full, blind = shown(capsys, ans, art), shown(capsys, ans, art, blind=True)
    for decided in ("status:", "bound by", "meaning:", "attacked by", "support:",
                    "counters:", "position [", "[contested]", "defeated"):
        assert decided in full                      # the control: the full view has it
        assert decided not in blind
    assert f'"{VIABLE["quote"]}"' in blind and ans.derivation["sub_arguments"][0]["span"][
        "text_sha256"] in blind


def test_showing_an_answer_never_changes_it(capsys):
    ans, art = ask(AGREE, NO_ATTACKS)
    before = canonical(ans)
    shown(capsys, ans, art)
    shown(capsys, ans, art, blind=True)
    assert canonical(ans) == before == canonical(replay(art))


def test_a_shared_step_with_steps_of_its_own_is_not_walked_twice(capsys):
    """i1 rests on q1, and both i2 and the answer rest on i1: i1's subtree is
    shown where i1 is first met, and only its name the second time."""
    i2 = {"id": "i2", "kind": "inference", "from": ["i1"], "conclusion": "Growth is not enough."}
    top = {"id": "i3", "kind": "inference", "from": ["i1", "i2"],
           "conclusion": "So growth alone does not make a business viable, twice over."}
    ans, art = ask([argue_reply([VIABLE, INFER, i2, top], "i3")] * 3, NO_ATTACKS)
    out = shown(capsys, ans, art)
    assert out.count("(shown above)") == 1
    assert out.count(f'"{VIABLE["quote"]}"') == 1
