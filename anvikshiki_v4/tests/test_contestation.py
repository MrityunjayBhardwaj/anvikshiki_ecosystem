# tests/test_contestation.py
import pytest
from anvikshiki_v4.schema_v4 import (
    Argument, Attack, Label, ProvenanceTag, PramanaType
)
from anvikshiki_v4.argumentation import ArgumentationFramework
from anvikshiki_v4.contestation import ContestationManager


def _simple_af():
    """AF with one accepted argument."""
    af = ArgumentationFramework()
    af.add_argument(Argument(
        id="A0", conclusion="p", top_rule=None,
        premises=frozenset(["p"]), is_strict=False,
        tag=ProvenanceTag(belief=0.7, disbelief=0.2, uncertainty=0.1,
                          pramana_type=PramanaType.ANUMANA,
                          trust_score=0.8, decay_factor=0.9),
    ))
    return af


def test_vada_returns_grounded():
    cm = ContestationManager()
    af = _simple_af()
    result = cm.vada(af)
    assert result.extension_size == 1
    assert "p" in result.accepted


def test_jalpa_returns_preferred():
    cm = ContestationManager()
    af = _simple_af()
    result = cm.jalpa(af, timeout_seconds=5.0)
    assert len(result.preferred_extensions) >= 1


def test_vitanda_returns_vulnerabilities():
    cm = ContestationManager()
    af = _simple_af()
    af.add_argument(Argument(
        id="A1", conclusion="not_p", top_rule=None,
        premises=frozenset(["not_p"]),
        tag=ProvenanceTag(belief=0.6, disbelief=0.3, uncertainty=0.1,
                          pramana_type=PramanaType.SABDA,
                          trust_score=0.7, decay_factor=0.9),
    ))
    af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
    af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
    result = cm.vitanda(af, timeout_seconds=5.0)
    assert "p" in result.vulnerability_inventory or \
           "not_p" in result.vulnerability_inventory


def test_contestation_asiddha():
    """Undermining contestation → target becomes OUT."""
    cm = ContestationManager()
    af = _simple_af()
    new_id = cm.apply_contestation(af, "asiddha", "A0", {
        "conclusion": "_stale_A0",
        "belief": 0.9,
        "pramana_type": "PRATYAKSA",
    })
    labels = af.compute_grounded()
    assert labels["A0"] == Label.OUT


def test_contestation_viruddha_creates_mutual_attack():
    """Rebutting contestation creates attacks in both directions."""
    cm = ContestationManager()
    af = _simple_af()
    new_id = cm.apply_contestation(af, "viruddha", "A0", {
        "conclusion": "not_p", "belief": 0.7,
    })
    # Both directions should have attacks
    attacks_on_a0 = [atk for atk in af.attacks if atk.target == "A0"]
    attacks_on_new = [atk for atk in af.attacks if atk.target == new_id]
    assert len(attacks_on_a0) >= 1
    assert len(attacks_on_new) >= 1


def test_contestation_idempotent():
    """Same contestation twice doesn't change outcome."""
    cm = ContestationManager()
    af = _simple_af()
    cm.apply_contestation(af, "asiddha", "A0", {
        "conclusion": "_stale1", "belief": 0.9,
        "pramana_type": "PRATYAKSA",
    })
    labels1 = af.compute_grounded()
    cm.apply_contestation(af, "asiddha", "A0", {
        "conclusion": "_stale2", "belief": 0.9,
        "pramana_type": "PRATYAKSA",
    })
    labels2 = af.compute_grounded()
    assert labels1["A0"] == labels2["A0"]
