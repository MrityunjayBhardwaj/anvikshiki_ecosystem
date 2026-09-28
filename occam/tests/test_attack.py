"""Stage 3: attack edges, typed, majority-kept, and never dangling (#140)."""

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from occam.argue import argue_from_replies
from occam.attack import (
    FALLACY_OF_TYPE,
    Attack,
    attack,
    attack_from_replies,
    attack_prompt,
    check_edges,
    majority_threshold,
)
from occam.model import ScriptedModel
from occam.snapshot import capture

T0 = datetime(2026, 9, 28, tzinfo=timezone.utc)
TEXT = ("Growth without positive unit economics is borrowed time. "
        "Some investors argue growth itself creates value through network effects.")
SNAP = capture(url="https://example.com/a", body=b"a", text=TEXT, fetched_at=T0)


def _args():
    steps = [
        {"id": "q1", "kind": "quote", "source": 1,
         "quote": "Growth without positive unit economics is borrowed time.",
         "conclusion": "Growth without unit economics is unsustainable."},
        {"id": "q2", "kind": "quote", "source": 1,
         "quote": "growth itself creates value through network effects",
         "conclusion": "Growth creates value on its own."},
        {"id": "i1", "kind": "inference", "from": ["q1"],
         "conclusion": "Growth alone is not enough."},
        {"id": "i2", "kind": "inference", "from": ["q2"],
         "conclusion": "Growth alone is enough."},
    ]
    r = argue_from_replies([json.dumps({"answer": "i1", "steps": steps})], [SNAP])
    by = {a.conclusion: a.id for a in r.arguments}
    return r, by["Growth without unit economics is unsustainable."], \
        by["Growth creates value on its own."], by["Growth alone is not enough."], \
        by["Growth alone is enough."]


R, Q1, Q2, I1, I2 = _args()


def edges(*triples, rationale="because"):
    return json.dumps({"attacks": [
        {"attacker": a, "target": t, "type": ty, "rationale": rationale}
        for a, t, ty in triples]})


def test_majority_threshold_is_strict_majority_and_asserted():
    assert [majority_threshold(k) for k in (1, 2, 3, 4, 5)] == [1, 2, 2, 3, 3]
    r = attack_from_replies([edges()] * 3, R.arguments)
    assert r.threshold == 2


def test_an_edge_proposed_by_a_majority_is_kept_with_its_sample_count():
    rep = edges((I1, I2, "rebutting"))
    r = attack_from_replies([rep, rep, edges()], R.arguments)
    assert [a.key for a in r.attacks] == [(I1, I2, "rebutting")]
    assert r.attacks[0].sample_ids == (0, 1)


def test_an_edge_proposed_by_a_minority_is_excluded_but_recorded():
    r = attack_from_replies([edges((I1, I2, "rebutting")), edges(), edges()], R.arguments)
    assert r.attacks == ()
    assert [a.key for a in r.minority] == [(I1, I2, "rebutting")]


def test_duplicates_in_one_sample_collapse_and_count_once():
    rep = edges((I1, I2, "rebutting"), (I1, I2, "rebutting"))
    r = attack_from_replies([rep, edges(), edges()], R.arguments)
    assert r.minority[0].sample_ids == (0,)


def test_rationale_does_not_split_an_edge():
    """Two samples with the same edge and different reasons are one edge.
    Keying on the rationale would make the words of a model part of the graph."""
    a = edges((I1, I2, "rebutting"), rationale="one reason")
    b = edges((I1, I2, "rebutting"), rationale="a different reason")
    r = attack_from_replies([a, b, edges()], R.arguments)
    assert len(r.attacks) == 1 and r.attacks[0].sample_ids == (0, 1)


def test_self_attack_is_dropped_and_counted():
    rep = edges((I1, I1, "rebutting"))
    r = attack_from_replies([rep, rep, rep], R.arguments)
    assert r.attacks == () and r.self_attacks == 3


def test_a_dangling_edge_raises_naming_the_unknown_id():
    bad = Attack(attacker=I1, target="A9999", type="rebutting", fallacy="viruddha")
    with pytest.raises(ValueError, match="A9999"):
        check_edges([bad], [a.id for a in R.arguments])


def test_a_sample_with_a_dangling_edge_is_rejected_whole_with_the_message():
    rep = edges((I1, I2, "rebutting"), (I1, "A9999", "rebutting"))
    r = attack_from_replies([rep, rep, rep], R.arguments)
    assert r.attacks == ()
    assert len(r.malformed) == 3 and "A9999" in r.malformed[0][1]


def test_an_undercut_cannot_target_a_quote():
    """Undercuts always defeat. Aimed at a quote they would delete verified
    evidence by assertion; a quote has no inference to undercut."""
    rep = edges((I2, Q1, "undercutting"))
    r = attack_from_replies([rep, rep, rep], R.arguments)
    assert r.attacks == () and len(r.type_mismatch) == 3


def test_an_undermine_cannot_target_an_inference():
    rep = edges((Q2, I1, "undermining"))
    r = attack_from_replies([rep, rep, rep], R.arguments)
    assert r.attacks == () and r.type_mismatch


def test_well_typed_edges_of_each_kind_are_kept():
    rep = edges((I1, I2, "rebutting"), (Q1, I2, "undercutting"), (Q1, Q2, "undermining"))
    r = attack_from_replies([rep, rep], R.arguments)
    assert {a.type for a in r.attacks} == {"rebutting", "undercutting", "undermining"}
    assert all(a.fallacy == FALLACY_OF_TYPE[a.type] for a in r.attacks)


def test_the_fallacy_follows_from_the_type():
    with pytest.raises(ValidationError, match="does not follow"):
        Attack(attacker="a", target="b", type="rebutting", fallacy="asiddha")


def test_a_non_json_reply_is_malformed():
    r = attack_from_replies(["no"], R.arguments)
    assert r.malformed and r.attacks == ()


def test_attack_is_deterministic_over_replies_and_uses_low_temperature():
    rep = edges((I1, I2, "rebutting"), (I2, I1, "rebutting"))
    m = ScriptedModel([rep] * 3)
    calls = []
    orig = m.complete
    m.complete = lambda p, temperature: calls.append(temperature) or orig(p, temperature=temperature)
    replies, r = attack(m, "Is growth enough?", R, k=3)
    assert attack_from_replies(replies, R.arguments) == r
    assert calls == [0.2, 0.2, 0.2]


def test_the_prompt_lists_every_argument_with_its_kind():
    p = attack_prompt("q", R.arguments)
    for a in R.arguments:
        assert a.id in p
    assert "[quote]" in p and "[inference from" in p


def test_no_arguments_means_no_model_call():
    m = ScriptedModel([])
    empty = argue_from_replies(['{"answer": null, "steps": []}'], [SNAP])
    replies, r = attack(m, "q", empty, k=3)
    assert replies == [] and r.attacks == () and m.prompts == []
