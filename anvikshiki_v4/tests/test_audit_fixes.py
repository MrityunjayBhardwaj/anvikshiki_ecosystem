# tests/test_audit_fixes.py
"""Tests for the audit-driven fixes (WS1–WS6).

WS1: Josang SL deduction, source overlap in oplus
WS3: All-arguments construction
WS4: Domain contrariness, predicate name extraction, scope fix
WS6: Pre-compilation
WS2: Label-based epistemic status
"""

import pytest
from anvikshiki_v4.schema_v4 import (
    Argument, Attack, ProvenanceTag, PramanaType, EpistemicStatus
)
from anvikshiki_v4.argumentation import ArgumentationFramework
from anvikshiki_v4.t2_compiler_v4 import (
    _predicate_name, _are_contrary,
    compile_t2, precompile_kb, _derive_rule_arguments,
)


def _make_arg(aid, conclusion, pramana=PramanaType.ANUMANA,
              belief=0.7, disbelief=None, uncertainty=None,
              trust=0.8, decay=0.9, depth=1, strict=False,
              source_ids=frozenset()):
    if disbelief is None:
        disbelief = max(0.0, round(1 - belief - 0.1, 4))
    if uncertainty is None:
        uncertainty = round(1.0 - belief - disbelief, 4)
    return Argument(
        id=aid, conclusion=conclusion, top_rule=None,
        premises=frozenset([conclusion]), is_strict=strict,
        tag=ProvenanceTag(
            belief=belief, disbelief=disbelief, uncertainty=uncertainty,
            pramana_type=pramana, trust_score=trust,
            decay_factor=decay, derivation_depth=depth,
            source_ids=source_ids,
        ),
    )


# ══════════════════════════════════════════════════════════════
# WS1: Josang SL deduction — disbelief/uncertainty attenuate
# ══════════════════════════════════════════════════════════════

class TestJosangTensorAttenuation:
    """Disbelief and uncertainty should ATTENUATE through chains, not grow."""

    def test_disbelief_attenuates_through_chain(self):
        """10-step chain with d=0.1 each → final d < 0.3 (was 0.65 with noisy-OR)."""
        tag = ProvenanceTag(belief=0.8, disbelief=0.1, uncertainty=0.1)
        result = tag
        for _ in range(9):
            result = ProvenanceTag.tensor(result, tag)
        assert result.disbelief < 0.3, (
            f"Disbelief should attenuate, got {result.disbelief:.3f}"
        )

    def test_uncertainty_accumulates_correctly(self):
        """Trust discounting: uncertainty grows through chains (correct behavior).

        Each uncertain link adds to total ignorance about the conclusion.
        u_result = a.d + a.u + a.b * b.u — uncertainty absorbs both the
        source's disbelief and uncertainty plus the rule's uncertainty.
        This is NOT a bug — it correctly reflects accumulated ignorance.
        The key fix is that DISBELIEF attenuates (not grows).
        """
        tag = ProvenanceTag(belief=0.8, disbelief=0.1, uncertainty=0.1)
        result = tag
        for _ in range(9):
            result = ProvenanceTag.tensor(result, tag)
        # Uncertainty grows (correct): absorbed from disbelief + uncertainty
        assert result.uncertainty > 0.5
        # b + d + u = 1.0 preserved exactly
        assert abs(result.belief + result.disbelief + result.uncertainty - 1.0) < 1e-10

    def test_chain_depth_20_still_nonzero(self):
        """After 20 steps, belief should still be > 0 (not collapsed to zero).

        Trust discounting: b = 0.8^20 ≈ 0.012.  This is low but nonzero,
        which is correct — long chains legitimately lose confidence.
        """
        tag = ProvenanceTag(belief=0.8, disbelief=0.1, uncertainty=0.1)
        result = tag
        for _ in range(19):
            result = ProvenanceTag.tensor(result, tag)
        assert result.belief > 0.005, (
            f"Belief should be nonzero at depth 20, got {result.belief:.4f}"
        )
        # Disbelief should be tiny (attenuated through chain)
        assert result.disbelief < 0.01


class TestSourceOverlapInOplus:
    """Overlapping sources → discounted fusion (not full cumulative)."""

    def test_independent_sources_full_fusion(self):
        """No overlap → standard cumulative fusion."""
        a = ProvenanceTag(belief=0.6, disbelief=0.1, uncertainty=0.3,
                          source_ids=frozenset(["src_a"]))
        b = ProvenanceTag(belief=0.6, disbelief=0.1, uncertainty=0.3,
                          source_ids=frozenset(["src_b"]))
        result = ProvenanceTag.oplus(a, b)
        assert result.belief > 0.6  # Fusion strengthens

    def test_identical_sources_averaging(self):
        """Full overlap → simple averaging (no double-counting)."""
        a = ProvenanceTag(belief=0.6, disbelief=0.1, uncertainty=0.3,
                          source_ids=frozenset(["shared"]))
        b = ProvenanceTag(belief=0.8, disbelief=0.1, uncertainty=0.1,
                          source_ids=frozenset(["shared"]))
        result = ProvenanceTag.oplus(a, b)
        # With full overlap, should be close to average (0.7), not fused higher
        assert result.belief == pytest.approx(0.7, abs=0.05)

    def test_partial_overlap_intermediate(self):
        """Partial overlap → between full fusion and averaging."""
        shared = frozenset(["shared"])
        a = ProvenanceTag(belief=0.6, disbelief=0.1, uncertainty=0.3,
                          source_ids=shared | frozenset(["a_only"]))
        b = ProvenanceTag(belief=0.6, disbelief=0.1, uncertainty=0.3,
                          source_ids=shared | frozenset(["b_only"]))

        independent = ProvenanceTag.oplus(
            ProvenanceTag(belief=0.6, disbelief=0.1, uncertainty=0.3,
                          source_ids=frozenset(["x"])),
            ProvenanceTag(belief=0.6, disbelief=0.1, uncertainty=0.3,
                          source_ids=frozenset(["y"])),
        )
        result = ProvenanceTag.oplus(a, b)
        # Partial overlap → less boost than fully independent
        assert result.belief <= independent.belief + 0.01

    def test_oplus_trust_uses_max(self):
        """trust_score in oplus should use max (lattice), not noisy-OR."""
        a = ProvenanceTag(belief=0.6, disbelief=0.1, uncertainty=0.3,
                          trust_score=0.5)
        b = ProvenanceTag(belief=0.6, disbelief=0.1, uncertainty=0.3,
                          trust_score=0.7)
        result = ProvenanceTag.oplus(a, b)
        assert result.trust_score == 0.7  # max, not noisy-OR (0.85)


# ══════════════════════════════════════════════════════════════
# WS3: All-arguments construction
# ══════════════════════════════════════════════════════════════

class TestAllArgumentsConstruction:
    """All sub-argument combos should be built, not just the strongest."""

    def test_two_subargs_both_used(self):
        """Two sub-args for same antecedent → both produce arguments."""
        from unittest.mock import MagicMock
        from anvikshiki_v4.schema import (
            KnowledgeStore, Vyapti, CausalStatus,
            EpistemicStatus as KBEpistemicStatus,
        )

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
        af.add_argument(_make_arg("A1", "p", belief=0.6))

        _derive_rule_arguments(af, ks)

        # Both A0 and A1 should be used as sub-args for V1
        q_args = [a for a in af.arguments.values() if a.conclusion == "q"]
        assert len(q_args) == 2, (
            f"Expected 2 arguments for q (from A0 and A1), got {len(q_args)}"
        )


# ══════════════════════════════════════════════════════════════
# WS4: Domain contrariness + predicate name extraction
# ══════════════════════════════════════════════════════════════

class TestPredicateName:
    """_predicate_name extracts name from pred(entity) format."""

    def test_with_entity(self):
        assert _predicate_name("binding_constraint(acme)") == "binding_constraint"

    def test_without_entity(self):
        assert _predicate_name("positive_unit_economics") == "positive_unit_economics"

    def test_nested_parens(self):
        assert _predicate_name("f(g(x))") == "f"


class TestDomainContrariness:
    """_are_contrary checks domain pairs from KnowledgeStore."""

    def test_syntactic_still_works(self):
        assert _are_contrary("p", "not_p")
        assert _are_contrary("not_p", "p")

    def test_domain_pair_detected(self):
        from unittest.mock import MagicMock
        from anvikshiki_v4.schema import KnowledgeStore
        ks = MagicMock(spec=KnowledgeStore)
        ks.contrariness_pairs = [["value_creation", "value_destruction"]]
        assert _are_contrary("value_creation", "value_destruction", ks)
        assert _are_contrary("value_destruction", "value_creation", ks)

    def test_domain_pair_with_entities(self):
        from unittest.mock import MagicMock
        from anvikshiki_v4.schema import KnowledgeStore
        ks = MagicMock(spec=KnowledgeStore)
        ks.contrariness_pairs = [["growth", "decline"]]
        assert _are_contrary("growth(acme)", "decline(acme)", ks)

    def test_no_false_positive(self):
        from unittest.mock import MagicMock
        from anvikshiki_v4.schema import KnowledgeStore
        ks = MagicMock(spec=KnowledgeStore)
        ks.contrariness_pairs = [["growth", "decline"]]
        assert not _are_contrary("growth", "stagnation", ks)


# ══════════════════════════════════════════════════════════════
# WS6: Pre-compilation
# ══════════════════════════════════════════════════════════════

class TestPrecompilation:
    """precompile_kb() + incremental compile_t2()."""

    @pytest.fixture
    def sample_ks(self):
        from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store
        return load_knowledge_store("anvikshiki_v4/data/sample_architecture.yaml")

    def test_precompile_then_query_same_result(self, sample_ks):
        """Pre-compiled + query should produce same results as full compile."""
        facts = [{"predicate": "concentrated_ownership", "confidence": 0.9}]

        # Full compile (no pre-compilation)
        af_full = compile_t2(sample_ks, facts)

        # Pre-compile + incremental
        cached = precompile_kb(sample_ks)
        af_incr = compile_t2(sample_ks, facts, precompiled_af=cached)

        # Same conclusions should be derivable
        conc_full = {a.conclusion for a in af_full.arguments.values()}
        conc_incr = {a.conclusion for a in af_incr.arguments.values()}
        assert conc_full == conc_incr

    def test_precompile_does_not_mutate(self, sample_ks):
        """Using precompiled_af should not mutate the cached copy."""
        cached = precompile_kb(sample_ks)
        original_count = len(cached.arguments)

        facts = [{"predicate": "concentrated_ownership", "confidence": 0.9}]
        compile_t2(sample_ks, facts, precompiled_af=cached)

        # Original cached AF should be unchanged
        assert len(cached.arguments) == original_count


# ══════════════════════════════════════════════════════════════
# WS2: Label-based epistemic status
# ══════════════════════════════════════════════════════════════

class TestLabelBasedEpistemicStatus:
    """Epistemic status derives from IN/OUT/UNDECIDED, not just thresholds."""

    def test_undecided_is_open(self):
        """UNDECIDED arguments → OPEN status (not threshold-derived)."""
        af = ArgumentationFramework()
        af.add_argument(_make_arg("A0", "p", belief=0.9))  # Would be ESTABLISHED by threshold
        af.add_argument(_make_arg("A1", "not_p", belief=0.9))
        af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
        af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
        af.compute_grounded()

        status, tag, args = af.get_epistemic_status("p")
        # Both UNDECIDED (symmetric attack) → OPEN
        assert status == EpistemicStatus.OPEN

    def test_all_out_is_contested(self):
        """All OUT arguments → CONTESTED status."""
        af = ArgumentationFramework()
        af.add_argument(_make_arg("A0", "p", belief=0.6))
        af.add_argument(_make_arg("A1", "attacker",
                                  pramana=PramanaType.PRATYAKSA, belief=0.9))
        af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
        af.compute_grounded()

        status, tag, args = af.get_epistemic_status("p")
        assert status == EpistemicStatus.CONTESTED

    def test_in_strong_is_established(self):
        """IN with strong tag → ESTABLISHED."""
        af = ArgumentationFramework()
        af.add_argument(_make_arg("A0", "p", belief=0.9,
                                  disbelief=0.05, uncertainty=0.05))
        af.compute_grounded()

        status, tag, args = af.get_epistemic_status("p")
        assert status == EpistemicStatus.ESTABLISHED
