"""Stage 5: grounded + preferred over arguments with no knowledge base (#141, #150)."""

import random

import pytest

from occam.argue import Argument
from occam.attack import FALLACY_OF_TYPE, Attack
from occam.solve import MAX_UNDECIDED, Label, chain_pramana, solve, solve_graph
from occam.spans import SpanRef
from occam.types import Pramana

IN, OUT, UND = Label.IN, Label.OUT, Label.UNDECIDED


def quote(aid):
    span = SpanRef(snapshot_id="sha256:x", text_sha256="t", start=0, end=1,
                   quote="q", checked=True, verdict="ok")
    return Argument(id=aid, conclusion=aid, kind="quote", span=span,
                    pramana=Pramana.SABDA, sample_ids=(0,))


def step(aid, *subs, kind="inference"):
    return Argument(id=aid, conclusion=aid, kind=kind, sub_arguments=subs,
                    pramana={"inference": Pramana.ANUMANA, "analogy": Pramana.UPAMANA}[kind],
                    sample_ids=(0,))


def atk(a, t, ty="rebutting"):
    return Attack(attacker=a, target=t, type=ty, fallacy=FALLACY_OF_TYPE[ty])


# ── the defeat relation ────────────────────────────────────

def test_an_undercut_from_the_weakest_pramana_still_defeats():
    """An analogy (UPAMANA) undercutting an inference over a quote (SABDA)."""
    args = [quote("Q"), step("I", "Q"), quote("P"), step("U", "P", kind="analogy")]
    r = solve(args, [atk("U", "I", "undercutting")])
    assert chain_pramana({a.id: a for a in args})["U"] == Pramana.UPAMANA
    assert r.grounded["I"] == OUT and r.grounded["U"] == IN


def test_a_weaker_rebut_fails_and_a_stronger_one_succeeds():
    args = [quote("Q"), quote("P"), step("U", "P", kind="analogy")]
    assert solve(args, [atk("U", "Q")]).grounded["Q"] == IN      # UPAMANA < SABDA
    assert solve(args, [atk("Q", "U")]).grounded["U"] == OUT     # SABDA > UPAMANA


def test_an_inference_is_no_stronger_than_its_quoted_premise():
    """Chain minimum: ANUMANA over SABDA is SABDA for preference. Without it
    the inference (3) would beat the very testimony (2) it was built from."""
    args = [quote("Q"), step("I", "Q"), quote("R")]
    assert chain_pramana({a.id: a for a in args})["I"] == Pramana.SABDA
    r = solve(args, [atk("I", "R"), atk("R", "I")])
    assert r.grounded["I"] == UND and r.grounded["R"] == UND     # equal: standoff


def test_a_strict_target_survives_a_rebut_from_the_strongest_attacker():
    r = solve_graph({"S": (), "X": ()}, [atk("X", "S")],
                    pramana={"S": Pramana.UPAMANA, "X": Pramana.PRATYAKSA},
                    strict=frozenset({"S"}))
    assert r.grounded["S"] == IN


def test_equal_pramana_breaks_on_strength():
    subs = {"A": (), "B": ()}
    p = {"A": Pramana.SABDA, "B": Pramana.SABDA}
    assert solve_graph(subs, [atk("A", "B")], pramana=p, strength={"A": 1, "B": 3}).grounded["B"] == IN
    assert solve_graph(subs, [atk("A", "B")], pramana=p, strength={"A": 3, "B": 3}).grounded["B"] == OUT


# ── attacks on premises reach the arguments built on them ───

def test_rebutting_a_premise_defeats_the_inference_resting_on_it():
    args = [quote("Q"), step("I", "Q"), quote("R")]
    r = solve(args, [atk("R", "Q", "undermining")])
    assert r.grounded["Q"] == OUT and r.grounded["I"] == OUT
    assert ("R", "I") in r.defeats


def test_the_lifted_defeat_is_decided_against_the_premise():
    """Preference compares the attacker with the attacked sub-argument, not the
    argument containing it."""
    args = [quote("Q"), step("A", "Q", kind="analogy"), quote("P"),
            step("W", "P", kind="analogy")]
    # W (UPAMANA) rebuts Q (SABDA): fails against Q, so A survives too,
    # even though A itself is UPAMANA.
    r = solve(args, [atk("W", "Q")])
    assert r.grounded["Q"] == IN and r.grounded["A"] == IN


# ── the two semantics ──────────────────────────────────────

def test_mutual_attack_neither_defeating_leaves_both_in():
    r = solve([quote("A"), quote("B")], [], strength={})
    assert r.grounded == {"A": IN, "B": IN}


def test_mutual_defeat_is_undecided_and_each_credulously_accepted():
    """Even cycle: a real case each way. This is what `contested` reports."""
    r = solve([quote("A"), quote("B")], [atk("A", "B"), atk("B", "A")])
    assert r.grounded == {"A": UND, "B": UND}
    assert set(r.preferred) == {frozenset({"A"}), frozenset({"B"})}
    assert r.credulous == {"A", "B"}


def test_an_odd_cycle_is_undecided_and_accepted_nowhere():
    """No coherent position holds any of them: this is `open`, not contested."""
    r = solve([quote("A"), quote("B"), quote("C")],
              [atk("A", "B"), atk("B", "C"), atk("C", "A")])
    assert set(r.grounded.values()) == {UND}
    assert r.preferred == (frozenset(),) and r.credulous == frozenset()


def test_a_dangling_attack_is_refused_by_the_solver():
    with pytest.raises(ValueError, match="Z"):
        solve([quote("A")], [atk("A", "Z")])


def test_sub_argument_cycles_do_not_recurse_without_bound():
    # Built by hand: argue() cuts cycles, but the solver must not depend on it.
    a = step("A", "B")
    b = step("B", "A")
    assert chain_pramana({"A": a, "B": b})["A"] == Pramana.ANUMANA
    assert solve([a, b], []).grounded == {"A": IN, "B": IN}


def test_too_many_undecided_skips_preferred_and_says_so():
    n = MAX_UNDECIDED + 2
    ids = [f"A{i}" for i in range(n)]
    attacks = [atk(ids[i], ids[(i + 1) % n]) for i in range(n)] + \
              [atk(ids[(i + 1) % n], ids[i]) for i in range(n)]
    r = solve([quote(i) for i in ids], attacks)
    assert r.preferred is None and r.credulous is None
    assert "exceeds the limit" in r.preferred_note


# ── randomised laws ────────────────────────────────────────

def _random_graph(rng, n, flat):
    ids = [f"A{i}" for i in range(n)]
    subs = {i: () for i in ids}
    if not flat:
        for j, i in enumerate(ids[1:], 1):
            if rng.random() < 0.4:
                subs[i] = tuple(rng.sample(ids[:j], rng.randint(1, min(2, j))))
    attacks = []
    for _ in range(rng.randint(0, 2 * n)):
        a, t = rng.sample(ids, 2)
        attacks.append(atk(a, t, rng.choice(list(FALLACY_OF_TYPE))))
    pramana = {i: Pramana(rng.randint(1, 4)) for i in ids}
    strength = {i: rng.randint(0, 4) for i in ids}
    strict = frozenset(i for i in ids if rng.random() < 0.15)
    return subs, attacks, pramana, strength, strict


def test_grounded_matches_the_engine_on_300_random_flat_frameworks():
    """The copy is held to the original. The engine's frameworks are flat, so
    the comparison is over flat ones; lifting is Occam's own and tested above."""
    from anvikshiki_v4.argumentation import ArgumentationFramework
    from anvikshiki_v4.lattice import STATUS_ORDER
    from anvikshiki_v4.schema_v4 import Argument as EArg, Attack as EAtk
    from anvikshiki_v4.schema_v4 import PramanaType, ProvenanceTag

    rng = random.Random(150)
    for trial in range(300):
        subs, attacks, pramana, strength, strict = _random_graph(rng, rng.randint(2, 9), flat=True)
        af = ArgumentationFramework()
        for i in subs:
            af.add_argument(EArg(id=i, conclusion=i, top_rule="r", is_strict=i in strict,
                                 tag=ProvenanceTag(pramana_type=PramanaType(pramana[i])),
                                 status=STATUS_ORDER[strength[i]]))
        for a in attacks:
            af.add_attack(EAtk(attacker=a.attacker, target=a.target,
                               attack_type=a.type, hetvabhasa=a.fallacy))
        theirs = {k: v.value for k, v in af.compute_grounded().items()}
        ours = solve_graph(subs, attacks, pramana=pramana, strength=strength,
                           strict=strict).grounded
        assert {k: v.value for k, v in ours.items()} == theirs, trial


def test_grounded_out_is_never_credulously_accepted():
    """The theorem the status stage rests on, over trees and flat graphs:
    `OUT in grounded, IN in preferred` cannot happen."""
    rng = random.Random(142)
    seen_credulous_undecided = 0
    for _ in range(400):
        subs, attacks, pramana, strength, strict = _random_graph(rng, rng.randint(2, 9), flat=rng.random() < 0.5)
        r = solve_graph(subs, attacks, pramana=pramana, strength=strength, strict=strict)
        out = {a for a, l in r.grounded.items() if l == OUT}
        grounded_in = {a for a, l in r.grounded.items() if l == IN}
        assert not (out & r.credulous)
        assert all(grounded_in <= p for p in r.preferred)
        seen_credulous_undecided += len(r.credulous - grounded_in)
    assert seen_credulous_undecided > 0, "the random graphs never produced the interesting case"


def test_every_preferred_extension_is_admissible_and_maximal():
    from occam.solve import _admissible
    rng = random.Random(7)
    for _ in range(200):
        subs, attacks, pramana, strength, strict = _random_graph(rng, rng.randint(2, 7), flat=False)
        r = solve_graph(subs, attacks, pramana=pramana, strength=strength, strict=strict)
        defeaters = {a: set() for a in subs}
        for x, b in r.defeats:
            defeaters[b].add(x)
        for p in r.preferred:
            assert _admissible(p, defeaters)
            for extra in set(subs) - p:
                assert not _admissible(p | {extra}, defeaters) or \
                    any(p | {extra} <= q for q in r.preferred if q != p)


def test_solving_is_deterministic():
    rng = random.Random(3)
    subs, attacks, pramana, strength, strict = _random_graph(rng, 8, flat=False)
    a = solve_graph(subs, attacks, pramana=pramana, strength=strength, strict=strict)
    b = solve_graph(subs, list(reversed(attacks)), pramana=pramana, strength=strength, strict=strict)
    assert a == b
