"""Rules versions (#223): the seven reading rules default from one row of a
table, a run records the row, and a rule set by hand for a what-if is
recorded beside it as a departure. Stored artifacts made before rows existed
read exactly as they did."""

import json

import pytest

from occam.answer import LATEST_RULES, RULE_FIELDS, RULES, Artifact, Params, canonical, replay
from occam.tests.test_answer import argue_reply, ask, made_before_rules


def test_each_row_extends_the_one_before():
    """No rule ever goes back to an older reading, and each row changes one."""
    rows = [RULES[n] for n in sorted(RULES)]
    assert sorted(RULES) == list(range(1, LATEST_RULES + 1))
    assert all(set(r) == set(RULE_FIELDS) for r in rows)
    for before, after in zip(rows, rows[1:]):
        assert all(after[f] >= before[f] for f in RULE_FIELDS)
        assert after != before


def test_params_take_their_rules_from_the_row():
    assert Params().rules == LATEST_RULES
    assert {f: getattr(Params(), f) for f in RULE_FIELDS} == RULES[LATEST_RULES]
    assert {f: getattr(Params(rules=1), f) for f in RULE_FIELDS} == RULES[1]


def test_an_unknown_row_is_refused():
    with pytest.raises(ValueError, match="rules 99: no such row"):
        Params(rules=99)


def test_a_new_artifact_stores_its_row_and_none_of_the_seven():
    _, art = ask([argue_reply([], None)] * 3, [])
    stored = json.loads(art.model_dump_json())["params"]
    assert stored["rules"] == LATEST_RULES
    assert not set(RULE_FIELDS) & set(stored)


def test_a_rule_set_by_hand_is_stored_as_a_departure_and_replays():
    ans, art = ask([argue_reply([], None)] * 3, [],
                   params=Params(k_argue=3, k_attack=3, veto_words=1))
    stored = json.loads(art.model_dump_json())
    departures = set(RULE_FIELDS) & set(stored["params"])
    assert departures == {"veto_words"} and stored["params"]["veto_words"] == 1
    back = Artifact.model_validate(stored)
    assert back.params.veto_words == 1 and back.params.rules == LATEST_RULES
    assert canonical(replay(back)) == canonical(ans)


def test_an_artifact_made_before_rows_is_named_by_the_row_it_matches():
    _, art = ask([argue_reply([], None)] * 3, [], params=Params(k_argue=3, k_attack=3, rules=3))
    old = made_before_rules(json.loads(art.model_dump_json()))
    assert "rules" not in old["params"]
    assert Artifact.model_validate(old).params.rules == 3


def test_one_that_matches_no_row_reads_as_row_1_with_its_own_as_departures():
    """As a field missing from it was always read: as the first rule."""
    _, art = ask([argue_reply([], None)] * 3, [])
    old = made_before_rules(json.loads(art.model_dump_json()))
    del old["params"]["covers_check"]                      # as runs 1-5 had no such field
    p = Artifact.model_validate(old).params
    assert p.rules == 1 and p.covers_check == 1
    assert {f: getattr(p, f) for f in RULE_FIELDS} == {**RULES[LATEST_RULES], "covers_check": 1}
