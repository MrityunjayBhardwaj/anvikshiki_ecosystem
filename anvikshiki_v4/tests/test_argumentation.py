# tests/test_argumentation.py
import pytest
from anvikshiki_v4.schema_v4 import (
    Argument, Attack, Label, ProvenanceTag, PramanaType, EpistemicStatus
)
from anvikshiki_v4.argumentation import ArgumentationFramework


def _make_arg(aid, conclusion, pramana=PramanaType.ANUMANA,
              trust=0.8, decay=0.9, depth=1, strict=False,
              status=EpistemicStatus.HYPOTHESIS):
    return Argument(
        id=aid, conclusion=conclusion, top_rule=None,
        premises=frozenset([conclusion]), is_strict=strict,
        tag=ProvenanceTag(
            pramana_type=pramana, trust_score=trust,
            decay_factor=decay, derivation_depth=depth,
        ),
        status=status,
    )


def test_empty_framework():
    af = ArgumentationFramework()
    labels = af.compute_grounded()
    assert labels == {}


def test_single_unattacked():
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.IN


def test_single_attack_defeat():
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p"))
    af.add_argument(_make_arg("A1", "q"))
    af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.IN
    assert labels["A1"] == Label.OUT


def test_defense():
    """A0 attacks A1, A1 attacks A2 → A0 IN, A1 OUT, A2 IN (defended)."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p"))
    af.add_argument(_make_arg("A1", "q"))
    af.add_argument(_make_arg("A2", "r"))
    af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
    af.add_attack(Attack("A1", "A2", "rebutting", "viruddha"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.IN
    assert labels["A1"] == Label.OUT
    assert labels["A2"] == Label.IN


def test_odd_cycle_undecided():
    """A0 ↔ A1 with equal strength → both UNDECIDED (satpratipakṣa)."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p"))
    af.add_argument(_make_arg("A1", "not_p"))
    af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
    af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.UNDECIDED
    assert labels["A1"] == Label.UNDECIDED


def test_pramana_preference():
    """PRATYAKSA attacker defeats SABDA target regardless of belief."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p", pramana=PramanaType.PRATYAKSA))
    af.add_argument(_make_arg("A1", "q", pramana=PramanaType.SABDA))
    af.add_attack(Attack("A0", "A1", "undermining", "asiddha"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.IN
    assert labels["A1"] == Label.OUT


def test_equal_pramana_strength_wins():
    """Same pramāṇa, higher status wins.

    Strength is a place in the lattice now rather than a product of floats,
    so the preference this exercises is stated as ESTABLISHED over
    HYPOTHESIS. The relation being tested is unchanged — an argument defeats
    a rival it is not strictly less preferred than.
    """
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p", trust=0.9,
                              status=EpistemicStatus.ESTABLISHED))
    af.add_argument(_make_arg("A1", "not_p", trust=0.7,
                              status=EpistemicStatus.HYPOTHESIS))
    af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
    af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.IN
    assert labels["A1"] == Label.OUT


def test_epistemic_status_established():
    """An accepted ESTABLISHED argument carries its status to the conclusion."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p", pramana=PramanaType.PRATYAKSA,
                              status=EpistemicStatus.ESTABLISHED))
    af.compute_grounded()
    status, tag, args = af.get_epistemic_status("p")
    assert status == EpistemicStatus.ESTABLISHED


def test_epistemic_status_contested():
    """All arguments for conclusion are OUT → CONTESTED."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p"))
    af.add_argument(_make_arg("A1", "attacker",
                              pramana=PramanaType.PRATYAKSA))
    af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
    af.compute_grounded()
    status, tag, args = af.get_epistemic_status("p")
    assert status == EpistemicStatus.CONTESTED


def test_accrual_takes_the_best_argument():
    """Multiple IN arguments for one conclusion → the join of their statuses.

    This used to assert that three arguments fused to a belief higher than
    any one of them. That was the double-counting the source-overlap
    discount then had to correct for. Accrual is max now: three HYPOTHESIS
    arguments leave a conclusion at HYPOTHESIS, and one ESTABLISHED among
    them carries it.
    """
    af = ArgumentationFramework()
    for i in range(3):
        af.add_argument(_make_arg(
            f"A{i}", "p", trust=0.8, decay=0.9, depth=1))
    af.compute_grounded()
    status, tag, args = af.get_epistemic_status("p")
    assert len(args) == 3
    assert status == EpistemicStatus.HYPOTHESIS

    af.add_argument(_make_arg("A3", "p", status=EpistemicStatus.ESTABLISHED))
    af.compute_grounded()
    status, tag, args = af.get_epistemic_status("p")
    assert status == EpistemicStatus.ESTABLISHED


def test_grounded_is_conflict_free():
    """Property: no two IN arguments attack each other."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p"))
    af.add_argument(_make_arg("A1", "not_p"))
    af.add_argument(_make_arg("A2", "q"))
    af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
    af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
    labels = af.compute_grounded()
    in_args = [aid for aid, lbl in labels.items() if lbl == Label.IN]
    for a in in_args:
        for b in in_args:
            if a != b:
                assert b not in af._attackers_of.get(a, [])


def test_argument_tree():
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p"))
    af.add_argument(_make_arg("A1", "q"))
    af.add_attack(Attack("A1", "A0", "undermining", "asiddha"))
    af.compute_grounded()
    tree = af.get_argument_tree("A0")
    assert tree["id"] == "A0"
    assert len(tree["attacks_received"]) == 1
