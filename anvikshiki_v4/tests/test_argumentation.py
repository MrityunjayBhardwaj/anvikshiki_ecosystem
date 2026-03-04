# tests/test_argumentation.py
import pytest
from anvikshiki_v4.schema_v4 import (
    Argument, Attack, Label, ProvenanceTag, PramanaType, EpistemicStatus
)
from anvikshiki_v4.argumentation import ArgumentationFramework


def _make_arg(aid, conclusion, pramana=PramanaType.ANUMANA,
              belief=0.7, trust=0.8, decay=0.9, depth=1, strict=False):
    return Argument(
        id=aid, conclusion=conclusion, top_rule=None,
        premises=frozenset([conclusion]), is_strict=strict,
        tag=ProvenanceTag(
            belief=belief, disbelief=round(1-belief-0.1, 2),
            uncertainty=0.1,
            pramana_type=pramana, trust_score=trust,
            decay_factor=decay, derivation_depth=depth,
        ),
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
    af.add_argument(_make_arg("A0", "p", belief=0.8))
    af.add_argument(_make_arg("A1", "q", belief=0.6))
    af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.IN
    assert labels["A1"] == Label.OUT


def test_defense():
    """A0 attacks A1, A1 attacks A2 → A0 IN, A1 OUT, A2 IN (defended)."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p", belief=0.8))
    af.add_argument(_make_arg("A1", "q", belief=0.7))
    af.add_argument(_make_arg("A2", "r", belief=0.6))
    af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
    af.add_attack(Attack("A1", "A2", "rebutting", "viruddha"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.IN
    assert labels["A1"] == Label.OUT
    assert labels["A2"] == Label.IN


def test_odd_cycle_undecided():
    """A0 ↔ A1 with equal strength → both UNDECIDED (satpratipakṣa)."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p", belief=0.7))
    af.add_argument(_make_arg("A1", "not_p", belief=0.7))
    af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
    af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.UNDECIDED
    assert labels["A1"] == Label.UNDECIDED


def test_pramana_preference():
    """PRATYAKSA attacker defeats SABDA target regardless of belief."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p", pramana=PramanaType.PRATYAKSA,
                              belief=0.5))
    af.add_argument(_make_arg("A1", "q", pramana=PramanaType.SABDA,
                              belief=0.9))
    af.add_attack(Attack("A0", "A1", "undermining", "asiddha"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.IN
    assert labels["A1"] == Label.OUT


def test_equal_pramana_strength_wins():
    """Same pramāṇa, higher strength wins."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p", belief=0.8, trust=0.9))
    af.add_argument(_make_arg("A1", "not_p", belief=0.5, trust=0.7))
    af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
    af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.IN
    assert labels["A1"] == Label.OUT


def test_epistemic_status_established():
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p", belief=0.9,
                              pramana=PramanaType.PRATYAKSA))
    af.compute_grounded()
    status, tag, args = af.get_epistemic_status("p")
    assert status == EpistemicStatus.ESTABLISHED


def test_epistemic_status_contested():
    """All arguments for conclusion are OUT → CONTESTED."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p", belief=0.6))
    af.add_argument(_make_arg("A1", "attacker",
                              pramana=PramanaType.PRATYAKSA, belief=0.9))
    af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
    af.compute_grounded()
    status, tag, args = af.get_epistemic_status("p")
    assert status == EpistemicStatus.CONTESTED


def test_oplus_accumulation():
    """Multiple IN arguments for same conclusion → combined belief > individual."""
    af = ArgumentationFramework()
    for i in range(3):
        af.add_argument(_make_arg(
            f"A{i}", "p", belief=0.5,
            trust=0.8, decay=0.9, depth=1,
        ))
    af.compute_grounded()
    status, tag, args = af.get_epistemic_status("p")
    assert tag.belief > 0.5


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
