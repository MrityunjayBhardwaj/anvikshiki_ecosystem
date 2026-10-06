"""Contested is shown above open (#191).

Both are undecided sceptically. A contested answer is defended in some
preferred extension, a coherent case for it; an open one is defended in none.
So when nothing better survives, the answer shown, and the order of the
positions, put contested first. Only the choice of what to show changes: the
status lattice, which sets ceilings and attack strength, does not.
"""

import json

from occam.answer import Artifact, Params, canonical, replay, run
from occam.argue import norm_conclusion
from occam.model import ScriptedModel
from occam.tests.test_answer import (AS_OF, QUERIES, SUPPORT_ALL, VIABLE, argue_reply, attacks,
                                     wiki)
from occam.tests.test_equiv import SAME, v
from occam.tests.test_answer import made_before_rules

ANSWERS = ["Growth is the first cause of viability.", "Growth is the second cause of viability.",
           "Growth is the third cause of viability.", "Margins alone decide viability.",
           "Pricing alone decides viability."]
REPLIES = [argue_reply([VIABLE, {"id": "i", "kind": "inference", "from": ["q1"],
                                 "conclusion": c}], "i") for c in ANSWERS]
# A0001..A0003 attack each other in a cycle of three: open, no coherent case.
# A0004 and A0005 defeat each other: contested, each has a case.
GRAPH = attacks(("A0001", "A0002", "rebutting"), ("A0002", "A0003", "rebutting"),
                ("A0003", "A0001", "rebutting"),
                ("A0004", "A0005", "rebutting"), ("A0005", "A0004", "rebutting"))


def shown(order, same_replies=None):
    p = Params(k_argue=5, k_attack=1, judge_same=same_replies is not None, shown_order=order)
    model = ScriptedModel([QUERIES] + REPLIES + [SUPPORT_ALL, GRAPH] + (same_replies or []))
    ans, art = run("Is growth alone enough to make a business viable?", model, params=p,
                   as_of=AS_OF, http_get=wiki)
    assert model._replies == []                       # every scripted reply was asked for
    return ans, art


def statuses(ans):
    return {a: p["status"] for p in ans.positions for a in p["argument_ids"]
            if a == p["best_argument"]}


def test_contested_is_shown_above_open():
    ans, _ = shown(2)
    assert ans.answer_id == "A0004" and ans.status.value == "contested"
    assert [p["status"] for p in ans.positions] == ["contested"] * 2 + ["open"] * 3


def test_order_1_is_what_every_earlier_artifact_showed():
    ans, _ = shown(1)
    assert ans.answer_id == "A0001" and ans.status.value == "open"


def test_no_argument_changes_status_only_what_is_shown():
    one, _ = shown(1)
    two, _ = shown(2)
    assert statuses(one) == statuses(two)
    assert one.status_bound_by != two.status_bound_by     # a different answer, bound as before


def test_an_artifact_without_the_field_shows_what_it_showed():
    ans, art = shown(1)
    old = made_before_rules(json.loads(art.model_dump_json()))
    del old["params"]["shown_order"]
    stored = Artifact.model_validate(old)
    assert stored.params.shown_order == 1
    assert canonical(replay(stored)) == canonical(ans)


def test_inside_a_merged_position_the_contested_wording_is_shown():
    """Run 3's q04: the judge merged an open and a contested answer into one
    position; it showed the open one, and the position read as open."""
    keys = sorted(norm_conclusion(c) for c in ANSWERS)
    merge = {norm_conclusion(ANSWERS[0]), norm_conclusion(ANSWERS[3])}       # A0001 + A0004
    replies = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            replies += [SAME] * 2 if {a, b} == merge else [v("different", "x")] * 2
    one, _ = shown(1, replies)
    two, _ = shown(2, replies)
    pos1 = next(p for p in one.positions if "A0001" in p["argument_ids"])
    pos2 = next(p for p in two.positions if "A0001" in p["argument_ids"])
    assert sorted(pos1["argument_ids"]) == ["A0001", "A0004"]
    assert (pos1["best_argument"], pos1["status"]) == ("A0001", "open")
    assert (pos2["best_argument"], pos2["status"]) == ("A0004", "contested")
