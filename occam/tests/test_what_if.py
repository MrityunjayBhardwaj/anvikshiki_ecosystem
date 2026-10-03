"""Dispute one edge and recompute (#143, #206): edit stored replies, replay,
and refuse any edit the stored replies cannot answer for."""

import json

import pytest

from occam.__main__ import main
from occam.answer import (Params, WhatIfRefused, canonical, replay, run, stored_run,
                          unread_judge_pairs, what_if)
from occam.model import ScriptedModel
from occam.tests.test_answer import (AGREE, AS_OF, GROW_INFER, GROWTH, INFER, NO_ATTACKS,
                                     QUERIES, SUPPORT_ALL, VIABLE, _two_sides, argue_reply, ask,
                                     attacks, wiki)
from occam.tests.test_equiv import WORDINGS, all_same
from occam.types import Status

MUTUAL = [attacks(("A0002", "A0000", "undermining"), ("A0000", "A0002", "undermining"))] * 3


def test_dropping_the_attack_on_a_quote_beneath_the_answer_lifts_it():
    """#193's fixture: the answer rests on A0000, which A0002 defeats and is
    defeated by. Without A0002's attack, A0000 stands and the answer with it."""
    ans, art = ask(_two_sides(), MUTUAL)
    assert ans.answer_id == "A0001" and ans.status == Status.CONTESTED
    after = replay(what_if(art, drop_attacks=[("A0002", "A0000")]))
    assert after.answer_id == "A0001" and after.status == Status.HYPOTHESIS


def test_rejecting_the_only_quote_drops_what_rests_on_it():
    ans, art = ask(AGREE, NO_ATTACKS)
    after = replay(what_if(art, reject_quotes=["A0000"]))
    assert after.abstained and after.abstain_reason.startswith("support:")


def test_an_edge_or_quote_that_is_not_there_is_refused():
    _, art = ask(AGREE, NO_ATTACKS)
    with pytest.raises(WhatIfRefused, match="no stored attack reply proposes A0000:A0001"):
        what_if(art, drop_attacks=[("A0000", "A0001")])
    with pytest.raises(WhatIfRefused, match="no quote argument A0009"):
        what_if(art, reject_quotes=["A0009"])
    with pytest.raises(WhatIfRefused, match="never asked"):
        what_if(art.model_copy(update={"support_replies": ()}), reject_quotes=["A0000"])


def judged_three():
    """Three wordings of one quote's conclusion, so the same-answer judge is
    asked about three pairs, in a fixed order."""
    argue = [argue_reply([{**VIABLE, "conclusion": w}], "q1") for w in WORDINGS]
    model = ScriptedModel([QUERIES] + argue + [SUPPORT_ALL] + [attacks()] * 3 + all_same(10))
    return run("Is growth alone enough to make a business viable?", model,
               params=Params(k_argue=3, k_attack=3), as_of=AS_OF, http_get=wiki)


def test_an_edit_that_shifts_the_judges_pairs_is_refused_and_one_that_trims_them_is_not():
    """The judge's replies are read by position. A0000's wording is in the
    second and third pairs, so rejecting it leaves the first, still read
    against its own reply. A0001's is in the first, so rejecting it moves the
    third pair onto the first reply."""
    _, art = judged_three()
    edited = what_if(art, reject_quotes=["A0000"])
    assert unread_judge_pairs(art, edited) == 2
    with pytest.raises(WhatIfRefused, match="judge's stored replies"):
        what_if(art, reject_quotes=["A0001"])


def test_a_what_if_writes_nothing_and_leaves_the_stored_run_as_it_was(tmp_path, capsys):
    ans, art = ask(_two_sides(), MUTUAL)
    f = tmp_path / "run.json"
    f.write_text(stored_run(ans, art))
    before = f.read_bytes()
    assert main(["replay", str(f), "--drop-attack", "A0002:A0000"]) == 0
    out = capsys.readouterr().out
    assert "what if: no attack A0002 → A0000  (computed by replay; nothing written)" in out
    assert "same-answer judge pairs this edit removed, whose stored replies are not read: 0" in out
    assert "status: contested" in out and "status: hypothesis" in out
    assert "the answer changes" in out
    assert f.read_bytes() == before and [p.name for p in tmp_path.iterdir()] == ["run.json"]
    assert canonical(replay(art)) == canonical(ans)


def test_the_command_refuses_with_exit_2_and_says_why(tmp_path, capsys):
    _, art = judged_three()
    ans = replay(art)
    f = tmp_path / "run.json"
    f.write_text(stored_run(ans, art))
    assert main(["replay", str(f), "--reject-quote", "A0001"]) == 2
    assert "refused: this edit changes the pairs" in capsys.readouterr().err
    assert main(["replay", str(f), "--drop-attack", "A0001"]) == 2
    assert "takes ATTACKER:TARGET" in capsys.readouterr().err


def test_a_what_if_that_moves_nothing_says_so_in_full(tmp_path, capsys):
    """An inference attacking a verbatim quote fails (#193's fixture), so
    dropping that attack changes nothing: said as the answer, its status and
    what binds it all the same."""
    verbatim = {**VIABLE, "conclusion": VIABLE["quote"]}
    ans, art = ask([argue_reply([verbatim, INFER], "i1")] * 2 +
                   [argue_reply([GROWTH, GROW_INFER], "i2")],
                   [attacks(("A0003", "A0000", "undermining"))] * 3)
    f = tmp_path / "run.json"
    f.write_text(stored_run(ans, art))
    assert main(["replay", str(f), "--drop-attack", "A0003:A0000"]) == 0
    out = capsys.readouterr().out
    assert out.rstrip().endswith("the answer, its status and what binds it are the same")
