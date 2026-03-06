# tests/test_fixes.py
"""Tests for all critical analysis fixes — ASPIC+ compliance, bug fixes."""
from anvikshiki_v4.schema_v4 import (
    Argument, Attack, Label, ProvenanceTag, PramanaType, EpistemicStatus
)
from anvikshiki_v4.argumentation import ArgumentationFramework
from anvikshiki_v4.contestation import ContestationManager
from anvikshiki_v4.t2_compiler_v4 import _get_contrary, _are_contrary
from anvikshiki_v4.uncertainty import compute_uncertainty_v4


def _make_arg(aid, conclusion, pramana=PramanaType.ANUMANA,
              belief=0.7, trust=0.8, decay=0.9, depth=1, strict=False):
    return Argument(
        id=aid, conclusion=conclusion, top_rule=None,
        premises=frozenset([conclusion]), is_strict=strict,
        tag=ProvenanceTag(
            belief=belief, disbelief=max(0.0, round(1-belief-0.1, 4)),
            uncertainty=round(1.0 - belief - max(0.0, round(1-belief-0.1, 4)), 4),
            pramana_type=pramana, trust_score=trust,
            decay_factor=decay, derivation_depth=depth,
        ),
    )


# ══════════════════════════════════════════════════════════════
# FIX 1: _defeats — undercutting bypasses preference
# ══════════════════════════════════════════════════════════════

class TestUndercuttingBypassesPreference:
    """Undercutting attacks always succeed regardless of strength/pramāṇa."""

    def test_weak_undercutter_defeats_strong_target(self):
        """UPAMANA undercutter defeats PRATYAKSA target — no preference check."""
        af = ArgumentationFramework()
        af.add_argument(_make_arg("A0", "p", pramana=PramanaType.PRATYAKSA,
                                  belief=0.95, trust=0.95))
        af.add_argument(_make_arg("A1", "_undercut_rule",
                                  pramana=PramanaType.UPAMANA,
                                  belief=0.3, trust=0.5))
        af.add_attack(Attack("A1", "A0", "undercutting", "savyabhicara"))
        labels = af.compute_grounded()
        assert labels["A1"] == Label.IN
        assert labels["A0"] == Label.OUT

    def test_undermining_still_uses_preference(self):
        """Undermining attack from weak to strong → target survives."""
        af = ArgumentationFramework()
        af.add_argument(_make_arg("A0", "p", pramana=PramanaType.PRATYAKSA,
                                  belief=0.9))
        af.add_argument(_make_arg("A1", "_stale_A0",
                                  pramana=PramanaType.UPAMANA,
                                  belief=0.3))
        af.add_attack(Attack("A1", "A0", "undermining", "asiddha"))
        labels = af.compute_grounded()
        # UPAMANA underminer cannot defeat PRATYAKSA target
        assert labels["A0"] == Label.IN
        assert labels["A1"] == Label.IN  # Unattacked itself


# ══════════════════════════════════════════════════════════════
# FIX 2: _defeats — strict argument protection
# ══════════════════════════════════════════════════════════════

class TestStrictArgumentProtection:
    """Strict arguments cannot be rebutted per ASPIC+."""

    def test_strict_arg_survives_rebutting(self):
        """A strict argument should not be defeated by a rebutting attack."""
        af = ArgumentationFramework()
        # A0 is strict with HIGHER strength than A1
        af.add_argument(_make_arg("A0", "p", belief=0.9, trust=0.95,
                                  strict=True))
        af.add_argument(_make_arg("A1", "not_p", belief=0.8, trust=0.8))
        af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
        af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
        labels = af.compute_grounded()
        # A0 is strict → rebutting attack on it fails
        # A0 can still rebut A1 (A1 is defeasible, and A0 is stronger)
        assert labels["A0"] == Label.IN
        assert labels["A1"] == Label.OUT

    def test_strict_arg_vulnerable_to_undermining(self):
        """Strict args can still be undermined (premise attack)."""
        af = ArgumentationFramework()
        af.add_argument(_make_arg("A0", "p", belief=0.6, strict=True))
        af.add_argument(_make_arg("A1", "_stale_A0",
                                  pramana=PramanaType.PRATYAKSA,
                                  belief=0.9))
        af.add_attack(Attack("A1", "A0", "undermining", "asiddha"))
        labels = af.compute_grounded()
        # Undermining bypasses strict protection — attacks the premise
        assert labels["A0"] == Label.OUT

    def test_strict_arg_vulnerable_to_undercutting(self):
        """Undercutting always succeeds, even against strict args."""
        af = ArgumentationFramework()
        af.add_argument(_make_arg("A0", "p", belief=0.9, strict=True))
        af.add_argument(_make_arg("A1", "_undercut",
                                  pramana=PramanaType.UPAMANA,
                                  belief=0.3))
        af.add_attack(Attack("A1", "A0", "undercutting", "savyabhicara"))
        labels = af.compute_grounded()
        assert labels["A0"] == Label.OUT


# ══════════════════════════════════════════════════════════════
# FIX 3: Contestation — negative disbelief
# ══════════════════════════════════════════════════════════════

class TestContestationDisbeliefClamping:
    """apply_contestation must not produce negative disbelief."""

    def test_high_belief_no_negative_disbelief(self):
        """belief=0.95 should not produce disbelief=-0.05."""
        cm = ContestationManager()
        af = ArgumentationFramework()
        af.add_argument(_make_arg("A0", "p"))
        new_id = cm.apply_contestation(af, "asiddha", "A0", {
            "conclusion": "_stale_A0",
            "belief": 0.95,
            "pramana_type": "PRATYAKSA",
        })
        new_arg = af.arguments[new_id]
        assert new_arg.tag.disbelief >= 0.0
        assert abs(new_arg.tag.belief + new_arg.tag.disbelief
                    + new_arg.tag.uncertainty - 1.0) < 0.05

    def test_belief_one_no_crash(self):
        """belief=1.0 should produce valid tag with d=0, u=0."""
        cm = ContestationManager()
        af = ArgumentationFramework()
        af.add_argument(_make_arg("A0", "p"))
        new_id = cm.apply_contestation(af, "asiddha", "A0", {
            "conclusion": "_stale_A0",
            "belief": 1.0,
            "pramana_type": "PRATYAKSA",
        })
        new_arg = af.arguments[new_id]
        assert new_arg.tag.disbelief >= 0.0
        assert new_arg.tag.uncertainty >= 0.0


# ══════════════════════════════════════════════════════════════
# FIX 4: Vitanda labels preservation
# ══════════════════════════════════════════════════════════════

class TestVitandaLabelsPreservation:
    """vitanda() should not permanently overwrite af.labels."""

    def test_labels_restored_after_vitanda(self):
        af = ArgumentationFramework()
        af.add_argument(_make_arg("A0", "p", belief=0.8))
        af.add_argument(_make_arg("A1", "not_p", belief=0.7))
        af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
        af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))

        # Compute grounded first
        af.compute_grounded()
        original_labels = af.labels.copy()

        # Run vitanda — should not permanently change af.labels
        cm = ContestationManager()
        cm.vitanda(af, timeout_seconds=5.0)

        assert af.labels == original_labels


# ══════════════════════════════════════════════════════════════
# FIX 5: Contrariness function — double negation
# ══════════════════════════════════════════════════════════════

class TestContrarinessFunction:
    """Proper negation handling including double negation elimination."""

    def test_simple_negation(self):
        assert _get_contrary("p") == "not_p"
        assert _get_contrary("not_p") == "p"

    def test_double_negation_elimination(self):
        # not_not_p normalizes to p, contrary of p is not_p
        assert _get_contrary("not_not_p") == "not_p"

    def test_are_contrary_simple(self):
        assert _are_contrary("p", "not_p")
        assert _are_contrary("not_p", "p")

    def test_are_contrary_double_negation(self):
        """not_not_p and not_p should be contrary."""
        assert _are_contrary("not_not_p", "not_p")

    def test_not_contrary_same(self):
        assert not _are_contrary("p", "p")
        assert not _are_contrary("p", "q")

    def test_triple_negation(self):
        """not_not_not_p normalizes to not_p, so contrary is p."""
        # _get_contrary normalizes first: not_not_not_p → not_p → contrary = p
        assert _get_contrary("not_not_not_p") == "p"
        # not_not_not_p ≈ not_p, which is contrary to p
        assert _are_contrary("not_not_not_p", "p")


# ══════════════════════════════════════════════════════════════
# FIX 6: Uncertainty — conclusion in output, threshold consistency
# ══════════════════════════════════════════════════════════════

class TestUncertaintyFixes:
    """uncertainty.py now uses conclusion param and consistent thresholds."""

    def test_conclusion_in_output(self):
        tag = ProvenanceTag(belief=0.9, disbelief=0.05, uncertainty=0.05,
                            trust_score=0.9, decay_factor=0.95,
                            derivation_depth=1)
        result = compute_uncertainty_v4(
            tag, 0.9, "my_conclusion", EpistemicStatus.ESTABLISHED)
        assert result["conclusion"] == "my_conclusion"
        assert "my_conclusion" in result["epistemic"]["explanation"]

    def test_threshold_boundary_established(self):
        """Tag with uncertainty=0.1 exactly should say well-established."""
        tag = ProvenanceTag(belief=0.85, disbelief=0.05, uncertainty=0.1)
        result = compute_uncertainty_v4(
            tag, 0.9, "p", EpistemicStatus.ESTABLISHED)
        assert "well-established" in result["epistemic"]["explanation"]


# ══════════════════════════════════════════════════════════════
# FIX 7: Preferred semantics with new _defeats
# ══════════════════════════════════════════════════════════════

class TestPreferredWithNewDefeats:
    """compute_preferred works correctly with attack-aware _defeats."""

    def test_preferred_includes_grounded(self):
        """Grounded extension is a subset of every preferred extension."""
        af = ArgumentationFramework()
        af.add_argument(_make_arg("A0", "p", belief=0.8))
        af.add_argument(_make_arg("A1", "q", belief=0.6))
        af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
        preferred = af.compute_preferred(timeout_seconds=5.0)
        grounded = af.compute_grounded()
        grounded_in = {a for a, l in grounded.items() if l == Label.IN}
        for ext in preferred:
            ext_in = {a for a, l in ext.items() if l == Label.IN}
            assert grounded_in.issubset(ext_in)

    def test_preferred_with_undercutting(self):
        """Undercutting attack in preferred semantics still bypasses preference."""
        af = ArgumentationFramework()
        af.add_argument(_make_arg("A0", "p", pramana=PramanaType.PRATYAKSA,
                                  belief=0.95))
        af.add_argument(_make_arg("A1", "_uc", pramana=PramanaType.UPAMANA,
                                  belief=0.3))
        af.add_attack(Attack("A1", "A0", "undercutting", "savyabhicara"))
        preferred = af.compute_preferred(timeout_seconds=5.0)
        # A1 should be IN in all preferred extensions (undercutting always succeeds)
        for ext in preferred:
            assert ext.get("A1") == Label.IN


# ══════════════════════════════════════════════════════════════
# FIX 8: Cycle detection in forward chaining
# ══════════════════════════════════════════════════════════════

class TestCycleDetectionInForwardChaining:
    """_derive_rule_arguments must not re-derive (rule, sub-args) pairs."""

    def test_same_rule_same_subargs_not_duplicated(self):
        """Calling _derive_rule_arguments twice doesn't create duplicates."""
        from anvikshiki_v4.t2_compiler_v4 import _derive_rule_arguments
        from unittest.mock import MagicMock
        from anvikshiki_v4.schema import (
            KnowledgeStore, Vyapti,
            CausalStatus, EpistemicStatus as KBEpistemicStatus,
        )

        # Minimal KB with one vyapti: p → q
        v = MagicMock(spec=Vyapti)
        v.antecedents = ["p"]
        v.consequent = "q"
        v.scope_exclusions = []
        v.causal_status = CausalStatus.EMPIRICAL
        v.epistemic_status = KBEpistemicStatus.ESTABLISHED
        v.confidence = MagicMock()
        v.confidence.formulation = 0.9
        v.confidence.existence = 0.9
        v.last_verified = None
        v.sources = []

        ks = MagicMock(spec=KnowledgeStore)
        ks.vyaptis = {"V1": v}

        af = ArgumentationFramework()
        af.add_argument(_make_arg("A0", "p", belief=0.9))

        # First derivation — should create one argument for q
        _derive_rule_arguments(af, ks)
        count_after_first = len(af.arguments)
        assert count_after_first == 2  # A0 (p) + derived (q)

        # Second derivation — same (rule, sub-args), should NOT create duplicate
        _derive_rule_arguments(af, ks)
        assert len(af.arguments) == count_after_first

    def test_fixpoint_terminates_with_cyclic_rules(self):
        """Cyclic KB rules (p→q, q→p) should not create unbounded arguments."""
        from anvikshiki_v4.t2_compiler_v4 import (
            _derive_rule_arguments, _derive_attacks
        )
        from unittest.mock import MagicMock
        from anvikshiki_v4.schema import (
            KnowledgeStore, Vyapti, CausalStatus,
            EpistemicStatus as KBEpistemicStatus,
        )

        def make_vyapti(ant, cons):
            v = MagicMock(spec=Vyapti)
            v.antecedents = [ant]
            v.consequent = cons
            v.scope_exclusions = []
            v.causal_status = CausalStatus.EMPIRICAL
            v.epistemic_status = KBEpistemicStatus.WORKING_HYPOTHESIS
            v.confidence = MagicMock()
            v.confidence.formulation = 0.8
            v.confidence.existence = 0.8
            v.last_verified = None
            v.sources = []
            return v

        ks = MagicMock(spec=KnowledgeStore)
        ks.vyaptis = {
            "V1": make_vyapti("p", "q"),
            "V2": make_vyapti("q", "p"),
        }

        af = ArgumentationFramework()
        af.add_argument(_make_arg("A0", "p", belief=0.9))

        # Simulate fixpoint loop
        for _ in range(20):
            prev = len(af.arguments)
            _derive_rule_arguments(af, ks)
            if len(af.arguments) == prev:
                break

        # With all-arguments construction, cyclic rules create more
        # arguments (each new conclusion becomes a candidate for the
        # other rule), but still bounded by iterations × combos_per_rule.
        # Key property: it terminates, not that count is minimal.
        assert len(af.arguments) <= 50  # Bounded, not unbounded


# ══════════════════════════════════════════════════════════════
# FIX 9: Recursion guard in get_argument_tree
# ══════════════════════════════════════════════════════════════

class TestArgumentTreeRecursionGuard:
    """get_argument_tree must not stack-overflow on cycles."""

    def test_normal_tree_rendering(self):
        """Normal (non-cyclic) tree still renders correctly."""
        af = ArgumentationFramework()
        af.add_argument(Argument(
            id="A0", conclusion="p", top_rule=None,
            premises=frozenset(["p"]), is_strict=True,
            tag=ProvenanceTag(belief=0.9, disbelief=0.0, uncertainty=0.1),
        ))
        af.add_argument(Argument(
            id="A1", conclusion="q", top_rule="V1",
            sub_arguments=("A0",),
            premises=frozenset(["p"]), is_strict=False,
            tag=ProvenanceTag(belief=0.7, disbelief=0.1, uncertainty=0.2),
        ))
        af.compute_grounded()

        tree = af.get_argument_tree("A1")
        assert tree["id"] == "A1"
        assert tree["conclusion"] == "q"
        assert len(tree["sub_arguments"]) == 1
        assert tree["sub_arguments"][0]["id"] == "A0"

    def test_cycle_detected_gracefully(self):
        """Cyclic sub-argument references produce cycle_detected marker."""
        af = ArgumentationFramework()
        # Manually create a cycle: A0 → A1 → A0 (shouldn't happen
        # normally, but guards against malformed AFs)
        af.add_argument(Argument(
            id="A0", conclusion="p", top_rule="V1",
            sub_arguments=("A1",),
            premises=frozenset(["p"]), is_strict=False,
            tag=ProvenanceTag(belief=0.7, disbelief=0.1, uncertainty=0.2),
        ))
        af.add_argument(Argument(
            id="A1", conclusion="q", top_rule="V2",
            sub_arguments=("A0",),
            premises=frozenset(["q"]), is_strict=False,
            tag=ProvenanceTag(belief=0.6, disbelief=0.1, uncertainty=0.3),
        ))
        af.compute_grounded()

        # Should NOT raise RecursionError — should detect and short-circuit
        tree = af.get_argument_tree("A0")
        assert tree["id"] == "A0"
        # A0 → A1 → A0 (cycle) → should have cycle_detected
        sub_a1 = tree["sub_arguments"][0]
        assert sub_a1["id"] == "A1"
        sub_a0_again = sub_a1["sub_arguments"][0]
        assert sub_a0_again.get("cycle_detected") is True

    def test_missing_argument_returns_empty(self):
        """get_argument_tree with nonexistent ID returns empty dict."""
        af = ArgumentationFramework()
        assert af.get_argument_tree("NOPE") == {}


# ══════════════════════════════════════════════════════════════
# FIX 10: Phase 1 engine output compatibility
# ══════════════════════════════════════════════════════════════

class TestPhase1OutputCompatibility:
    """Phase 1 engine output must have same fields as Phase 2+."""

    def test_phase1_output_has_all_fields(self):
        """Phase 1 Prediction includes all Phase 2+ fields with defaults."""
        from unittest.mock import MagicMock, patch
        import dspy

        # Mock grounding pipeline
        grounding = MagicMock()
        grounding.predicates = ["test_pred"]
        grounding.confidence = 0.85
        grounding.clarification_needed = False

        grounding_pipeline = MagicMock(return_value=grounding)
        ks = MagicMock()

        # Mock ChainOfThought to avoid needing an LM
        mock_response = MagicMock()
        mock_response.response = "Test response"
        mock_response.sources_cited = ["src1"]

        with patch("dspy.ChainOfThought", return_value=MagicMock(
            return_value=mock_response
        )):
            from anvikshiki_v4.engine_v4 import AnvikshikiEngineV4Phase1
            engine = AnvikshikiEngineV4Phase1(ks, grounding_pipeline)

        engine.reasoner = MagicMock(return_value=mock_response)
        result = engine.forward("test query", ["chunk1"])

        # All Phase 2+ fields must be present
        assert hasattr(result, "response")
        assert hasattr(result, "sources")
        assert hasattr(result, "uncertainty")
        assert hasattr(result, "provenance")
        assert hasattr(result, "violations")
        assert hasattr(result, "grounding_confidence")
        assert hasattr(result, "extension_size")
        assert hasattr(result, "contestation")

        # Check defaults
        assert result.uncertainty == {}
        assert result.provenance == {}
        assert result.violations == []
        assert result.extension_size == 0
        assert result.contestation is None
        assert result.grounding_confidence == 0.85
        assert result.response == "Test response"
        assert result.sources == ["src1"]
