# tests/test_t2_compiler_v4.py
import pytest
from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store, _build_rule_tag
from anvikshiki_v4.schema_v4 import Label, PramanaType


@pytest.fixture
def sample_ks():
    return load_knowledge_store("anvikshiki_v4/data/sample_architecture.yaml")


def test_basic_compilation(sample_ks):
    """compile_t2 produces AF with correct argument count."""
    facts = [{"predicate": "concentrated_ownership", "confidence": 0.9}]
    af = compile_t2(sample_ks, facts)
    assert len(af.arguments) > 1  # At least premise + some rule args


def test_premise_arguments(sample_ks):
    """Query facts produce premise arguments with PRATYAKSA."""
    facts = [{"predicate": "concentrated_ownership", "confidence": 0.85}]
    af = compile_t2(sample_ks, facts)
    premise_args = [a for a in af.arguments.values() if a.top_rule is None
                    and a.conclusion == "concentrated_ownership"]
    assert len(premise_args) == 1
    assert premise_args[0].tag.pramana_type == PramanaType.PRATYAKSA
    assert premise_args[0].tag.derivation_depth == 0


def test_chain_derivation(sample_ks):
    """V01: A→B, V02: B→C — both B and C derived."""
    facts = [{"predicate": "concentrated_ownership", "confidence": 0.9}]
    af = compile_t2(sample_ks, facts)
    conclusions = {a.conclusion for a in af.arguments.values()}
    assert "long_horizon_possible" in conclusions
    assert "capability_building_possible" in conclusions


def test_scope_exclusion_generates_attack(sample_ks):
    """public_firm in V01.scope_exclusions → undercutting attack."""
    facts = [
        {"predicate": "concentrated_ownership", "confidence": 0.9},
        {"predicate": "public_firm", "confidence": 0.95},
    ]
    af = compile_t2(sample_ks, facts)
    undercut_attacks = [
        atk for atk in af.attacks if atk.attack_type == "undercutting"
    ]
    assert len(undercut_attacks) > 0
    assert undercut_attacks[0].hetvabhasa == "savyabhicara"


def test_rebutting_attacks(sample_ks):
    """V03 derives not_good_governance — should rebut any good_governance."""
    facts = [
        {"predicate": "concentrated_ownership", "confidence": 0.9},
        {"predicate": "good_governance", "confidence": 0.7},
    ]
    af = compile_t2(sample_ks, facts)
    rebutting = [atk for atk in af.attacks if atk.hetvabhasa == "viruddha"]
    assert len(rebutting) > 0


def test_fixpoint_convergence(sample_ks):
    """Transitive chain terminates."""
    facts = [{"predicate": "concentrated_ownership", "confidence": 0.9}]
    af = compile_t2(sample_ks, facts)
    # Should not hang — if we get here, fixpoint converged
    assert len(af.arguments) < 1000  # Sanity bound


def test_build_rule_tag(sample_ks):
    """_build_rule_tag maps KB metadata correctly."""
    v = sample_ks.vyaptis["V01"]
    tag = _build_rule_tag(v, sample_ks)
    assert tag.pramana_type == PramanaType.ANUMANA  # EMPIRICAL → ANUMANA
    assert tag.belief == pytest.approx(0.95)  # ESTABLISHED
    assert tag.trust_score == pytest.approx(0.9 * 0.85)
