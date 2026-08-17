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
              trust=0.8, decay=0.9, depth=1, strict=False,
              source_ids=frozenset(),
              status=EpistemicStatus.HYPOTHESIS):
    return Argument(
        id=aid, conclusion=conclusion, top_rule=None,
        premises=frozenset([conclusion]), is_strict=strict,
        tag=ProvenanceTag(
            pramana_type=pramana, trust_score=trust,
            decay_factor=decay, derivation_depth=depth,
            source_ids=source_ids,
        ),
        status=status,
    )


# ══════════════════════════════════════════════════════════════
# WS1: Josang SL deduction — disbelief/uncertainty attenuate
# ══════════════════════════════════════════════════════════════

class TestMetadataLatticeComposition:
    """What survives of the two composition operators.

    The tests that used to live here checked Jøsang trust discounting and
    cumulative fusion — that disbelief attenuated through a chain, that
    belief stayed nonzero at depth 20, that overlapping sources were
    discounted so restated evidence did not compound. All of it is gone
    with the opinion it operated on.

    What the operators still do is compose provenance metadata, by min
    along a chain and max across accrual. Those are the laws now, and
    `test_algebra_laws.py` states them over a generated domain; these two
    keep the specific behaviours the audit originally asked for.
    """

    def test_chaining_takes_the_weakest_trust(self):
        a = ProvenanceTag(trust_score=0.9, decay_factor=0.9)
        b = ProvenanceTag(trust_score=0.5, decay_factor=0.8)
        result = ProvenanceTag.tensor(a, b)
        assert result.trust_score == 0.5
        assert result.decay_factor == 0.8

    def test_accrual_takes_the_best_trust(self):
        """max, not noisy-OR: two sources at 0.5 and 0.7 give 0.7, not 0.85.

        The source-overlap discount this class used to test is gone too. It
        existed to stop cumulative fusion double-counting one argument
        restated, and it silently failed to fire when neither tag carried a
        source id. max needs no discount — accruing a tag against itself
        returns it, whatever its provenance says.
        """
        a = ProvenanceTag(trust_score=0.5, source_ids=frozenset(["src_a"]))
        b = ProvenanceTag(trust_score=0.7, source_ids=frozenset(["src_b"]))
        assert ProvenanceTag.oplus(a, b).trust_score == 0.7
        assert ProvenanceTag.oplus(a, a) == a


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
        af.add_argument(_make_arg("A0", "p"))
        af.add_argument(_make_arg("A1", "p"))

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
        af.add_argument(_make_arg("A0", "p"))  # Would be ESTABLISHED by threshold
        af.add_argument(_make_arg("A1", "not_p"))
        af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
        af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
        af.compute_grounded()

        status, tag, args = af.get_epistemic_status("p")
        # Both UNDECIDED (symmetric attack) → OPEN
        assert status == EpistemicStatus.OPEN

    def test_all_out_is_contested(self):
        """All OUT arguments → CONTESTED status."""
        af = ArgumentationFramework()
        af.add_argument(_make_arg("A0", "p"))
        af.add_argument(_make_arg("A1", "attacker",
                                  pramana=PramanaType.PRATYAKSA))
        af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
        af.compute_grounded()

        status, tag, args = af.get_epistemic_status("p")
        assert status == EpistemicStatus.CONTESTED

    def test_in_strong_is_established(self):
        """IN with an ESTABLISHED argument → ESTABLISHED.

        Previously "IN with a strong tag": the label still gates the
        outcome, and what it is joined with is now a lattice element rather
        than a belief read through a cutoff.
        """
        af = ArgumentationFramework()
        af.add_argument(_make_arg("A0", "p", status=EpistemicStatus.ESTABLISHED))
        af.compute_grounded()

        status, tag, args = af.get_epistemic_status("p")
        assert status == EpistemicStatus.ESTABLISHED
