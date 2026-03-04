# tests/test_business_expert.py
"""
Integration tests for the Business Expert knowledge base.

Tests the full v4 engine pipeline against business_expert.yaml:
- T2 compilation (KB + facts → argumentation framework)
- Chain derivation (V01→V08, V04→V05)
- Rebutting attacks (V01 vs V11: value_creation vs not_value_creation)
- Undercutting attacks (scope exclusions)
- Grounded semantics (label computation)
- Contestation protocols (vāda, jalpa, vitaṇḍā)
- Uncertainty quantification
"""

import pytest
from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store
from anvikshiki_v4.schema_v4 import Label, PramanaType, EpistemicStatus
from anvikshiki_v4.contestation import ContestationManager
from anvikshiki_v4.uncertainty import compute_uncertainty_v4


# ── Fixtures ──

@pytest.fixture
def business_ks():
    return load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")


@pytest.fixture
def growing_startup_facts():
    """A growing startup with positive unit economics and identified constraints."""
    return [
        {"predicate": "positive_unit_economics", "confidence": 0.9},
        {"predicate": "binding_constraint_identified", "confidence": 0.85},
        {"predicate": "organizational_growth", "confidence": 0.8},
    ]


@pytest.fixture
def disruption_facts():
    """Facts for testing disruption theory."""
    return [
        {"predicate": "incumbent_rational_allocation", "confidence": 0.85},
        {"predicate": "low_margin_market_entrant", "confidence": 0.8},
    ]


# ── Knowledge Store Loading ──

class TestKnowledgeStoreLoading:
    """Verify the business expert YAML loads correctly."""

    def test_domain_type(self, business_ks):
        from anvikshiki_v4.schema import DomainType
        assert business_ks.domain_type == DomainType.CRAFT

    def test_pramana_count(self, business_ks):
        assert len(business_ks.pramanas) == 4
        assert "pratyaksa" in business_ks.pramanas
        assert "upamana" in business_ks.pramanas

    def test_vyapti_count(self, business_ks):
        assert len(business_ks.vyaptis) == 11

    def test_hetvabhasa_count(self, business_ks):
        assert len(business_ks.hetvabhasas) == 8

    def test_threshold_concepts(self, business_ks):
        assert len(business_ks.threshold_concepts) == 3

    def test_chapter_fingerprints(self, business_ks):
        assert len(business_ks.chapter_fingerprints) == 10

    def test_reference_bank(self, business_ks):
        assert len(business_ks.reference_bank) == 29

    def test_contested_vyapti(self, business_ks):
        """V09 (Disruption Asymmetry) should be CONTESTED."""
        from anvikshiki_v4.schema import EpistemicStatus as KBEpistemic
        v09 = business_ks.vyaptis["V09"]
        assert v09.epistemic_status == KBEpistemic.ACTIVELY_CONTESTED

    def test_structural_vyapti(self, business_ks):
        """V03 and V06 should be STRUCTURAL causal status."""
        from anvikshiki_v4.schema import CausalStatus
        assert business_ks.vyaptis["V03"].causal_status == CausalStatus.STRUCTURAL
        assert business_ks.vyaptis["V06"].causal_status == CausalStatus.STRUCTURAL


# ── Basic Compilation ──

class TestBasicCompilation:
    """Verify compile_t2 produces correct AF structure."""

    def test_premise_arguments_created(self, business_ks, growing_startup_facts):
        af = compile_t2(business_ks, growing_startup_facts)
        premise_args = [a for a in af.arguments.values() if a.top_rule is None
                        and not a.conclusion.startswith("_")]
        assert len(premise_args) == 3

    def test_premise_tags_are_pratyaksa(self, business_ks, growing_startup_facts):
        af = compile_t2(business_ks, growing_startup_facts)
        for a in af.arguments.values():
            if a.top_rule is None and not a.conclusion.startswith("_"):
                assert a.tag.pramana_type == PramanaType.PRATYAKSA

    def test_rule_arguments_derived(self, business_ks, growing_startup_facts):
        af = compile_t2(business_ks, growing_startup_facts)
        rule_args = [a for a in af.arguments.values() if a.top_rule is not None]
        assert len(rule_args) >= 5  # V01, V02, V04, V05, V08, V11

    def test_fixpoint_convergence(self, business_ks, growing_startup_facts):
        af = compile_t2(business_ks, growing_startup_facts)
        assert len(af.arguments) < 100  # Sanity bound


# ── Chain Derivation ──

class TestChainDerivation:
    """Test that vyāpti chains fire correctly."""

    def test_value_chain_v01_to_v08(self, business_ks):
        """V01: positive_unit_economics → value_creation
           V02: binding_constraint → resource_allocation_effective
           V08: value_creation + resource_allocation_effective → long_term_value"""
        facts = [
            {"predicate": "positive_unit_economics", "confidence": 0.9},
            {"predicate": "binding_constraint_identified", "confidence": 0.85},
        ]
        af = compile_t2(business_ks, facts)
        conclusions = {a.conclusion for a in af.arguments.values()}
        assert "value_creation" in conclusions
        assert "resource_allocation_effective" in conclusions
        assert "long_term_value" in conclusions

    def test_entropy_chain_v04_to_v05(self, business_ks):
        """V04: organizational_growth → coordination_overhead
           V05: coordination_overhead → distorted_market_signal"""
        facts = [{"predicate": "organizational_growth", "confidence": 0.8}]
        af = compile_t2(business_ks, facts)
        conclusions = {a.conclusion for a in af.arguments.values()}
        assert "coordination_overhead" in conclusions
        assert "distorted_market_signal" in conclusions

    def test_chain_strength_decreases_with_depth(self, business_ks):
        """Strength should decrease along derivation chains due to tensor."""
        facts = [
            {"predicate": "positive_unit_economics", "confidence": 0.9},
            {"predicate": "binding_constraint_identified", "confidence": 0.85},
        ]
        af = compile_t2(business_ks, facts)
        args_by_conc = {}
        for a in af.arguments.values():
            args_by_conc[a.conclusion] = a

        # Premise > rule-derived > chain-derived
        assert args_by_conc["positive_unit_economics"].tag.strength > \
               args_by_conc["value_creation"].tag.strength > \
               args_by_conc["long_term_value"].tag.strength

    def test_independent_vyaptis_dont_fire_without_antecedents(self, business_ks):
        """V09 (disruption) shouldn't fire without its specific antecedents."""
        facts = [{"predicate": "positive_unit_economics", "confidence": 0.9}]
        af = compile_t2(business_ks, facts)
        conclusions = {a.conclusion for a in af.arguments.values()}
        assert "disruption_vulnerability" not in conclusions

    def test_v08_requires_both_antecedents(self, business_ks):
        """V08 needs BOTH value_creation AND resource_allocation_effective."""
        # Only provide one antecedent chain
        facts = [{"predicate": "positive_unit_economics", "confidence": 0.9}]
        af = compile_t2(business_ks, facts)
        conclusions = {a.conclusion for a in af.arguments.values()}
        assert "value_creation" in conclusions
        assert "long_term_value" not in conclusions  # V08 can't fire


# ── Rebutting Attacks (V01 vs V11) ──

class TestRebuttingAttacks:
    """Test the value_creation vs not_value_creation conflict."""

    def test_rebutting_attacks_exist(self, business_ks, growing_startup_facts):
        """V01→value_creation and V11→not_value_creation should rebutt."""
        af = compile_t2(business_ks, growing_startup_facts)
        rebutting = [a for a in af.attacks if a.hetvabhasa == "viruddha"]
        assert len(rebutting) == 2  # Mutual rebutting

    def test_value_creation_wins_over_growth_trap(self, business_ks, growing_startup_facts):
        """V01 (stronger tag) should beat V11 in grounded semantics."""
        af = compile_t2(business_ks, growing_startup_facts)
        af.compute_grounded()

        # Find argument conclusions and their labels
        for a in af.arguments.values():
            if a.conclusion == "value_creation":
                assert af.labels[a.id] == Label.IN
            elif a.conclusion == "not_value_creation":
                assert af.labels[a.id] == Label.OUT

    def test_v11_needs_both_antecedents(self, business_ks):
        """V11 needs organizational_growth AND coordination_overhead.
           coordination_overhead is derived from V04, so V11 only fires
           when organizational_growth is present (V04 derives the second)."""
        facts = [
            {"predicate": "positive_unit_economics", "confidence": 0.9},
            {"predicate": "organizational_growth", "confidence": 0.8},
        ]
        af = compile_t2(business_ks, facts)
        conclusions = {a.conclusion for a in af.arguments.values()}
        # V04 derives coordination_overhead, V11 can now fire
        assert "not_value_creation" in conclusions


# ── Undercutting Attacks (Scope Exclusions) ──

class TestUndercuttingAttacks:
    """Test scope exclusion-triggered undercutting attacks."""

    def test_subsidized_entity_undercuts_v01(self, business_ks):
        """subsidized_entity is in V01.scope_exclusions → undercut V01."""
        facts = [
            {"predicate": "positive_unit_economics", "confidence": 0.9},
            {"predicate": "subsidized_entity", "confidence": 0.95},
        ]
        af = compile_t2(business_ks, facts)
        af.compute_grounded()

        undercuts = [a for a in af.attacks if a.attack_type == "undercutting"]
        assert len(undercuts) >= 1

        # V01's conclusion should be OUT (undercut)
        for a in af.arguments.values():
            if a.conclusion == "value_creation" and a.top_rule == "V01":
                assert af.labels[a.id] == Label.OUT

    def test_active_intervention_undercuts_v04_and_v11(self, business_ks):
        """active_structural_intervention is in V04 AND V11 scope_exclusions."""
        facts = [
            {"predicate": "positive_unit_economics", "confidence": 0.9},
            {"predicate": "organizational_growth", "confidence": 0.8},
            {"predicate": "active_structural_intervention", "confidence": 0.85},
        ]
        af = compile_t2(business_ks, facts)
        af.compute_grounded()

        # V04's coordination_overhead should be OUT (undercut)
        for a in af.arguments.values():
            if a.conclusion == "coordination_overhead" and a.top_rule == "V04":
                assert af.labels[a.id] == Label.OUT

    def test_attentive_incumbent_undercuts_disruption(self, business_ks, disruption_facts):
        """attentive_incumbent undercuts V09 (Disruption Asymmetry)."""
        facts = disruption_facts + [
            {"predicate": "attentive_incumbent", "confidence": 0.7},
        ]
        af = compile_t2(business_ks, facts)
        af.compute_grounded()

        for a in af.arguments.values():
            if a.conclusion == "disruption_vulnerability":
                assert af.labels[a.id] == Label.OUT

    def test_multiple_scope_exclusions_compound(self, business_ks):
        """V08 has two exclusions; either one should undercut it."""
        facts = [
            {"predicate": "positive_unit_economics", "confidence": 0.9},
            {"predicate": "binding_constraint_identified", "confidence": 0.85},
            {"predicate": "regulated_industry", "confidence": 0.9},
        ]
        af = compile_t2(business_ks, facts)
        af.compute_grounded()

        for a in af.arguments.values():
            if a.conclusion == "long_term_value" and a.top_rule == "V08":
                assert af.labels[a.id] == Label.OUT


# ── Grounded Semantics Integration ──

class TestGroundedSemantics:
    """Test grounded extension computation on business expert KB."""

    def test_all_premise_arguments_accepted(self, business_ks, growing_startup_facts):
        """Premise (fact) arguments should always be IN."""
        af = compile_t2(business_ks, growing_startup_facts)
        af.compute_grounded()
        for a in af.arguments.values():
            if a.top_rule is None and not a.conclusion.startswith("_"):
                assert af.labels[a.id] == Label.IN

    def test_epistemic_status_derivation(self, business_ks, growing_startup_facts):
        """get_epistemic_status should return correct statuses."""
        af = compile_t2(business_ks, growing_startup_facts)
        af.compute_grounded()

        # value_creation is IN → should have a defined status
        status, tag, args = af.get_epistemic_status("value_creation")
        assert status is not None
        assert tag is not None
        assert len(args) > 0

        # not_value_creation is OUT → should be CONTESTED
        status_nv, _, _ = af.get_epistemic_status("not_value_creation")
        assert status_nv == EpistemicStatus.CONTESTED

    def test_long_term_value_has_multiple_sources(self, business_ks):
        """V08's tag should combine sources from V01 and V02 chains."""
        facts = [
            {"predicate": "positive_unit_economics", "confidence": 0.9,
             "sources": ["src_hbs"]},
            {"predicate": "binding_constraint_identified", "confidence": 0.85,
             "sources": ["src_goldratt"]},
        ]
        af = compile_t2(business_ks, facts)
        for a in af.arguments.values():
            if a.conclusion == "long_term_value":
                # V08's tag combines sources from V01, V02, and the premise facts
                assert len(a.tag.source_ids) > 0


# ── Contestation Protocols ──

class TestContestationProtocols:
    """Test all three debate protocols on business expert KB."""

    def test_vada_cooperative(self, business_ks, growing_startup_facts):
        """Vāda (grounded) should produce accepted conclusions."""
        af = compile_t2(business_ks, growing_startup_facts)
        cm = ContestationManager()
        result = cm.vada(af)

        assert result.extension_size >= 7  # Most args should be IN
        assert "value_creation" in result.accepted
        assert "long_term_value" in result.accepted
        assert result.accepted["value_creation"]["status"] is not None

    def test_vada_contested_conclusion(self, business_ks, growing_startup_facts):
        """not_value_creation should appear as CONTESTED in vāda."""
        af = compile_t2(business_ks, growing_startup_facts)
        cm = ContestationManager()
        result = cm.vada(af)

        assert "not_value_creation" in result.accepted
        assert result.accepted["not_value_creation"]["status"] == EpistemicStatus.CONTESTED

    def test_jalpa_adversarial(self, business_ks, growing_startup_facts):
        """Jalpa (preferred) should produce at least one extension."""
        af = compile_t2(business_ks, growing_startup_facts)
        cm = ContestationManager()
        result = cm.jalpa(af, timeout_seconds=5.0)

        assert len(result.preferred_extensions) >= 1
        # Should identify counter-arguments for the value_creation conflict
        assert len(result.counter_arguments) >= 1

    def test_vitanda_critique(self, business_ks, growing_startup_facts):
        """Vitaṇḍā (stable) should identify vulnerabilities."""
        af = compile_t2(business_ks, growing_startup_facts)
        cm = ContestationManager()
        result = cm.vitanda(af, timeout_seconds=5.0)

        # Should identify vulnerability for value_creation (attacked by V11)
        assert len(result.vulnerability_inventory) >= 1

    def test_apply_user_contestation(self, business_ks, growing_startup_facts):
        """User should be able to contest a specific argument."""
        af = compile_t2(business_ks, growing_startup_facts)
        af.compute_grounded()

        # Find the value_creation argument
        vc_arg = None
        for a in af.arguments.values():
            if a.conclusion == "value_creation":
                vc_arg = a
                break
        assert vc_arg is not None

        cm = ContestationManager()
        pre_attack_count = len(af.attacks)

        # Contest value_creation with counter-evidence
        new_id = cm.apply_contestation(
            af=af,
            contestation_type="viruddha",
            target_arg_id=vc_arg.id,
            evidence={
                "conclusion": "not_value_creation",
                "belief": 0.95,
                "pramana_type": "PRATYAKSA",
                "sources": ["user_evidence"],
            },
        )

        assert new_id is not None
        assert len(af.attacks) > pre_attack_count  # New attacks added


# ── Uncertainty Quantification ──

class TestUncertaintyQuantification:
    """Test UQ on business expert KB scenarios."""

    def test_basic_uncertainty(self, business_ks, growing_startup_facts):
        af = compile_t2(business_ks, growing_startup_facts)
        af.compute_grounded()

        # Get the value_creation argument for UQ
        vc_arg = next(
            a for a in af.arguments.values() if a.conclusion == "value_creation"
        )
        status, tag, _ = af.get_epistemic_status("value_creation")
        report = compute_uncertainty_v4(
            tag=vc_arg.tag,
            grounding_confidence=0.9,
            conclusion="value_creation",
            epistemic_status=status,
        )

        assert "epistemic" in report
        assert "aleatoric" in report
        assert "inference" in report
        assert report["total_confidence"] > 0

    def test_higher_uncertainty_for_deeper_chains(self, business_ks):
        """V08 (depth=2 chain) should have higher uncertainty than V01 (depth=1)."""
        facts = [
            {"predicate": "positive_unit_economics", "confidence": 0.9},
            {"predicate": "binding_constraint_identified", "confidence": 0.85},
        ]
        af = compile_t2(business_ks, facts)
        af.compute_grounded()

        v01_arg = None
        v08_arg = None
        for a in af.arguments.values():
            if a.conclusion == "value_creation" and a.top_rule == "V01":
                v01_arg = a
            if a.conclusion == "long_term_value" and a.top_rule == "V08":
                v08_arg = a

        assert v01_arg is not None and v08_arg is not None
        # Deeper chain → higher uncertainty (lower strength)
        assert v08_arg.tag.uncertainty > v01_arg.tag.uncertainty


# ── Disruption Theory (Contested Vyāpti) ──

class TestDisruptionTheory:
    """Test V09 which is explicitly CONTESTED in the KB."""

    def test_disruption_fires_with_both_antecedents(self, business_ks, disruption_facts):
        af = compile_t2(business_ks, disruption_facts)
        conclusions = {a.conclusion for a in af.arguments.values()}
        assert "disruption_vulnerability" in conclusions

    def test_disruption_tag_reflects_contested_status(self, business_ks, disruption_facts):
        """CONTESTED epistemic status → higher disbelief in tag."""
        af = compile_t2(business_ks, disruption_facts)
        for a in af.arguments.values():
            if a.conclusion == "disruption_vulnerability":
                # CONTESTED: b=0.4, d=0.4, u=0.2 → significant disbelief
                assert a.tag.disbelief > 0.1

    def test_disruption_not_fires_without_antecedents(self, business_ks):
        """V09 needs both incumbent_rational_allocation AND low_margin_market_entrant."""
        facts = [{"predicate": "incumbent_rational_allocation", "confidence": 0.85}]
        af = compile_t2(business_ks, facts)
        conclusions = {a.conclusion for a in af.arguments.values()}
        assert "disruption_vulnerability" not in conclusions


# ── Argument Tree Rendering ──

class TestArgumentTree:
    """Test argument tree construction for business expert scenarios."""

    def test_argument_tree_structure(self, business_ks, growing_startup_facts):
        af = compile_t2(business_ks, growing_startup_facts)
        af.compute_grounded()

        # Get tree for long_term_value (deepest chain)
        ltv_arg = None
        for a in af.arguments.values():
            if a.conclusion == "long_term_value":
                ltv_arg = a
                break

        assert ltv_arg is not None
        tree = af.get_argument_tree(ltv_arg.id)

        assert tree["conclusion"] == "long_term_value"
        assert tree["top_rule"] == "V08"
        assert len(tree["sub_arguments"]) == 2  # V01's output + V02's output
        assert tree["label"] == "in"

    def test_argument_tree_premise_is_leaf(self, business_ks, growing_startup_facts):
        af = compile_t2(business_ks, growing_startup_facts)
        af.compute_grounded()

        # Get tree for a premise argument
        for a in af.arguments.values():
            if a.conclusion == "positive_unit_economics" and a.top_rule is None:
                tree = af.get_argument_tree(a.id)
                assert len(tree["sub_arguments"]) == 0  # Leaf
                assert tree["top_rule"] is None
                break
