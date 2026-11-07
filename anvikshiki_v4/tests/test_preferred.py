"""Preferred extensions are the maximal admissible sets, over defeats (#153)."""

import random
from itertools import combinations

from anvikshiki_v4.argumentation import MAX_UNDECIDED, ArgumentationFramework
from anvikshiki_v4.contestation import ContestationManager
from anvikshiki_v4.lattice import STATUS_ORDER
from anvikshiki_v4.schema_v4 import (
    Argument, Attack, EpistemicStatus, Label, PramanaType, ProvenanceTag,
)

KINDS = {"rebutting": "viruddha", "undermining": "asiddha", "undercutting": "savyabhicara"}


def _arg(aid, pramana=PramanaType.ANUMANA, status=EpistemicStatus.HYPOTHESIS, strict=False,
         conclusion=None):
    return Argument(id=aid, conclusion=conclusion or aid, top_rule="r", is_strict=strict,
                    tag=ProvenanceTag(pramana_type=pramana), status=status)


def _af(args, attacks):
    af = ArgumentationFramework()
    for a in args:
        af.add_argument(a if isinstance(a, Argument) else _arg(a))
    for attacker, target, kind in attacks:
        af.add_attack(Attack(attacker=attacker, target=target, attack_type=kind,
                             hetvabhasa=KINDS[kind]))
    return af


def _sets(extensions):
    return {frozenset(k for k, v in e.items() if v == Label.IN) for e in extensions}


def _brute_force(af):
    """Every subset, read from `_defeats` directly: shares no search with the
    code under test."""
    ids = list(af.arguments)
    defeats = {(a.attacker, a.target) for a in af.attacks
               if af._defeats(af.arguments[a.attacker], af.arguments[a.target], a)}

    def admissible(s):
        for x, y in defeats:
            if x in s and y in s:
                return False
            if y in s and not any((d, x) in defeats for d in s):
                return False
        return True
    good = [frozenset(c) for r in range(len(ids) + 1) for c in combinations(ids, r)
            if admissible(frozenset(c))]
    return {s for s in good if not any(s < o for o in good)}


def _random_af(rng):
    ids = [f"A{i}" for i in range(rng.randint(2, 8))]
    args = [_arg(i, pramana=PramanaType(rng.randint(1, 4)), status=rng.choice(STATUS_ORDER),
                 strict=rng.random() < 0.15) for i in ids]
    attacks = [(*rng.sample(ids, 2), rng.choice(list(KINDS)))
               for _ in range(rng.randint(0, 2 * len(ids)))]
    return _af(args, attacks)


def _mutual_pairs(n_pairs):
    ids = [f"A{i}" for i in range(2 * n_pairs)]
    attacks = [t for i in range(0, 2 * n_pairs, 2)
               for t in ((ids[i], ids[i + 1], "undercutting"),
                         (ids[i + 1], ids[i], "undercutting"))]
    return _af(ids, attacks)


def test_the_case_the_old_search_got_wrong():
    """Its answer, {A1, A3}, was not even maximal: A2 could join it."""
    A, P = PramanaType.ANUMANA, PramanaType.PRATYAKSA
    H = STATUS_ORDER
    af = _af([_arg("A0", A, H[0]), _arg("A1", P, H[1]), _arg("A2", A, H[0]), _arg("A3", P, H[3])],
             [("A2", "A3", "rebutting"), ("A0", "A2", "undermining"), ("A0", "A3", "rebutting"),
              ("A3", "A0", "undercutting"), ("A2", "A1", "undermining"),
              ("A0", "A1", "undermining"), ("A0", "A3", "undercutting")])
    assert _sets(af.compute_preferred()) == {frozenset({"A0", "A1"}),
                                             frozenset({"A1", "A2", "A3"})}


def test_extensions_are_the_maximal_admissible_sets_on_300_random_frameworks():
    rng = random.Random(153)
    seen = 0
    for trial in range(300):
        af = _random_af(rng)
        got = _sets(af.compute_preferred())
        assert got == _brute_force(af), trial
        seen += len(got) > 1
    assert seen > 20                       # the law saw real choices, not one set each time


def test_grounded_is_inside_every_extension_and_its_out_in_none():
    rng = random.Random(11)
    for trial in range(300):
        af = _random_af(rng)
        g = af.compute_grounded()
        for ext in _sets(af.compute_preferred()):
            assert {a for a, l in g.items() if l == Label.IN} <= ext, trial
            assert not {a for a, l in g.items() if l == Label.OUT} & ext, trial


def test_an_attack_that_fails_is_not_a_conflict():
    """A weaker attacker's rebuttal fails. Over attacks this pair could never
    share an extension, though grounded accepts both."""
    af = _af([_arg("weak", PramanaType.UPAMANA), _arg("strong", PramanaType.PRATYAKSA)],
             [("weak", "strong", "rebutting")])
    [ext] = af.compute_preferred()
    assert ext == {"weak": Label.IN, "strong": Label.IN}
    assert {a for a, l in af.compute_grounded().items() if l == Label.IN} == {"weak", "strong"}


def test_out_means_defeated_by_a_member_and_undecided_means_not():
    af = _af(["a", "b", "c", "d"],
             [("a", "b", "undercutting"), ("b", "a", "undercutting"),
              ("b", "c", "undercutting"),
              ("d", "d", "undercutting")])
    by_in = {frozenset(k for k, v in e.items() if v == Label.IN): e
             for e in af.compute_preferred()}
    assert set(by_in) == {frozenset({"a", "c"}), frozenset({"b"})}
    assert by_in[frozenset({"b"})] == {"a": Label.OUT, "b": Label.IN, "c": Label.OUT,
                                       "d": Label.UNDECIDED}


def test_a_members_failed_attack_does_not_put_its_target_out():
    """`t` sits in an odd cycle, so it is undecided. A weak member's rebuttal of
    it fails, which leaves it undecided, not OUT."""
    af = _af([_arg("t", PramanaType.PRATYAKSA), _arg("x", PramanaType.PRATYAKSA),
              _arg("y", PramanaType.PRATYAKSA), _arg("weak", PramanaType.UPAMANA)],
             [("t", "x", "undercutting"), ("x", "y", "undercutting"), ("y", "t", "undercutting"),
              ("weak", "t", "rebutting")])
    assert af.compute_preferred() == [{"t": Label.UNDECIDED, "x": Label.UNDECIDED,
                                       "y": Label.UNDECIDED, "weak": Label.IN}]


def test_extensions_come_back_in_one_order():
    af = _af(["b", "a"], [("a", "b", "undercutting"), ("b", "a", "undercutting")])
    assert [sorted(k for k, v in e.items() if v == Label.IN)
            for e in af.compute_preferred()] == [["a"], ["b"]]


def test_an_odd_cycle_has_the_empty_extension_and_nothing_is_out():
    af = _af(["a", "b", "c"], [("a", "b", "undercutting"), ("b", "c", "undercutting"),
                               ("c", "a", "undercutting")])
    assert af.compute_preferred() == [{"a": Label.UNDECIDED, "b": Label.UNDECIDED,
                                       "c": Label.UNDECIDED}]


def test_at_the_limit_it_computes_and_past_it_it_says_it_did_not():
    assert MAX_UNDECIDED % 2 == 0
    at = _mutual_pairs(MAX_UNDECIDED // 2)
    assert len(at.compute_preferred()) == 2 ** (MAX_UNDECIDED // 2)
    past = _mutual_pairs(MAX_UNDECIDED // 2 + 1)
    assert past.compute_preferred() is None


def test_jalpa_says_when_preferred_was_not_computed():
    result = ContestationManager().jalpa(_mutual_pairs(MAX_UNDECIDED // 2 + 1))
    assert result.preferred_extensions is None
    assert result.defensible_positions is None             # not looked, so not "none found"
    assert result.preferred_note.startswith("preferred not computed")


def test_jalpa_names_each_side_of_a_real_dispute_as_defensible():
    af = _af([_arg("a"), _arg("b"), _arg("c", conclusion="_internal"), _arg("solid")],
             [("a", "b", "undercutting"), ("b", "a", "undercutting"),
              ("c", "a", "rebutting"), ("a", "c", "rebutting")])
    result = ContestationManager().jalpa(af)
    # "_" conclusions stay internal; grounded already accepts "solid", so no
    # one has to defend it.
    assert result.defensible_positions == ["a", "b"]
    assert result.preferred_note == ""
