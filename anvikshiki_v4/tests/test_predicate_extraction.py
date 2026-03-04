"""
Tests for the Automated Predicate Extraction Pipeline.

Three test categories:
  1. Unit tests: Schema validation, utilities, reward functions (no LLM)
  2. Stage E integration: Validate/merge against real business_expert.yaml
  3. Evaluation metrics: Precision, recall, naming, completeness
"""

import pytest

from anvikshiki_v4.extraction_schema import (
    CandidatePredicate,
    ClaimType,
    ExtractionConfig,
    PredicateNode,
    PredicateRelation,
    ProposedVyapti,
    Provenance,
    ReviewDecision,
    ReviewItem,
    StageAOutput,
    StageDOutput,
    SynonymCluster,
    ValidationResult,
)
from anvikshiki_v4.predicate_extraction import (
    SNAKE_CASE_RE,
    StageEValidator,
    _detect_cycles,
    _enforce_snake_case,
    _normalize_predicate_name,
    _split_into_sections,
)
from anvikshiki_v4.extraction_eval import (
    ExtractionEvaluator,
    _best_match_score,
    _token_overlap,
    dag_validity,
    naming_quality,
    predicate_precision,
    predicate_recall,
    vyapti_completeness,
    zero_section_rate,
)
from anvikshiki_v4.extraction_hitl import (
    HITLReviewer,
    _vyapti_to_yaml_dict,
    render_validation_summary,
    render_vyapti_diff,
)
from anvikshiki_v4.schema import (
    CausalStatus,
    Confidence,
    DomainType,
    EpistemicStatus,
    KnowledgeStore,
    Vyapti,
)


# ── Fixtures ──


@pytest.fixture
def minimal_ks():
    """A minimal KnowledgeStore for unit tests (no LLM needed)."""
    return KnowledgeStore(
        domain_type=DomainType.CRAFT,
        pramanas=["pratyaksa", "anumana"],
        vyaptis={
            "V01": Vyapti(
                id="V01",
                name="Unit Economics Test",
                statement="Positive unit economics indicates value creation",
                causal_status=CausalStatus.EMPIRICAL,
                confidence=Confidence(
                    existence=0.9, formulation=0.85, evidence="observational"
                ),
                epistemic_status=EpistemicStatus.ESTABLISHED,
                antecedents=["positive_unit_economics"],
                consequent="value_creation",
                scope_exclusions=["subsidized_entity"],
                sources=["R01"],
            ),
            "V02": Vyapti(
                id="V02",
                name="Resource Allocation",
                statement="Binding constraint leads to effective allocation",
                causal_status=CausalStatus.EMPIRICAL,
                confidence=Confidence(
                    existence=0.85, formulation=0.8, evidence="observational"
                ),
                epistemic_status=EpistemicStatus.ESTABLISHED,
                antecedents=["binding_constraint_identified"],
                consequent="resource_allocation_effective",
                sources=["R02"],
            ),
        },
        reference_bank={"R01": {"title": "Test ref 1"}, "R02": {"title": "Test ref 2"}},
        chapter_fingerprints={
            "ch01": pytest.importorskip("anvikshiki_v4.schema").ChapterFingerprint(
                chapter_id="ch01",
                title="Test Chapter",
                vyaptis_introduced=["V01", "V02"],
            )
        },
    )


@pytest.fixture
def sample_stage_a():
    """Sample StageAOutput for testing downstream stages."""
    return StageAOutput(
        candidates=[
            CandidatePredicate(
                name="ltv_exceeds_cac",
                description="Lifetime value exceeds customer acquisition cost",
                claim_type=ClaimType.METRIC,
                provenance=Provenance(chapter_id="ch02", confidence=0.7),
                related_existing_vyapti="V01",
            ),
            CandidatePredicate(
                name="positive_contribution_margin",
                description="Revenue minus variable costs is positive",
                claim_type=ClaimType.METRIC,
                provenance=Provenance(chapter_id="ch02", confidence=0.8),
                related_existing_vyapti="V01",
            ),
            CandidatePredicate(
                name="payback_within_runway",
                description="CAC payback period is within funding runway",
                claim_type=ClaimType.CONDITIONAL,
                provenance=Provenance(chapter_id="ch02", confidence=0.65),
            ),
        ],
        chapter_id="ch02",
        section_count=5,
        zero_predicate_sections=2,
    )


@pytest.fixture
def sample_stage_d():
    """Sample StageDOutput for testing evaluation and HITL."""
    return StageDOutput(
        new_vyaptis=[
            ProposedVyapti(
                id="V12",
                name="LTV-CAC Viability Test",
                statement="When LTV exceeds CAC, unit economics are viable",
                causal_status="empirical",
                antecedents=["ltv_exceeds_cac"],
                consequent="positive_unit_economics",
                scope_conditions=["post_product_market_fit"],
                confidence_existence=0.8,
                confidence_formulation=0.7,
                epistemic_status="hypothesis",
                sources=["R01"],
            ),
        ],
        refinement_vyaptis=[
            ProposedVyapti(
                id="V13",
                name="Contribution Margin Requirement",
                statement="Positive contribution margin is necessary for unit economics",
                causal_status="empirical",
                antecedents=["positive_contribution_margin"],
                consequent="positive_unit_economics",
                confidence_existence=0.85,
                confidence_formulation=0.75,
                epistemic_status="hypothesis",
                parent_vyapti="V01",
            ),
        ],
    )


# ── 1. Utility Tests ──


class TestSnakeCaseEnforcement:
    def test_already_snake_case(self):
        assert _enforce_snake_case("ltv_exceeds_cac") == "ltv_exceeds_cac"

    def test_camel_case_conversion(self):
        assert _enforce_snake_case("LtvExceedsCac") == "ltv_exceeds_cac"

    def test_spaces_to_underscores(self):
        assert _enforce_snake_case("ltv exceeds cac") == "ltv_exceeds_cac"

    def test_special_characters(self):
        result = _enforce_snake_case("LTV-CAC > 3x")
        assert SNAKE_CASE_RE.match(result)

    def test_empty_string(self):
        assert _enforce_snake_case("") == "unknown_predicate"

    def test_truncation(self):
        long_name = "a" * 100
        result = _enforce_snake_case(long_name)
        assert len(result) <= 60

    def test_normalize_returns_empty_for_invalid(self):
        assert _normalize_predicate_name("123invalid") == ""

    def test_normalize_valid(self):
        assert _normalize_predicate_name("good_name") == "good_name"


class TestSplitIntoSections:
    def test_respects_heading_boundaries(self):
        text = "### Section 1\nContent here.\n### Section 2\nMore content."
        sections = _split_into_sections(text, max_tokens=100)
        assert len(sections) == 2

    def test_splits_long_sections(self):
        # Each line has 10 words, so 10 lines = 100 words, split at 30 tokens
        text = "\n".join([" ".join(["word"] * 10)] * 10)
        sections = _split_into_sections(text, max_tokens=30)
        assert len(sections) >= 3

    def test_single_short_section(self):
        text = "Just a short paragraph."
        sections = _split_into_sections(text, max_tokens=100)
        assert len(sections) == 1

    def test_empty_text(self):
        sections = _split_into_sections("", max_tokens=100)
        assert sections == [""]


class TestCycleDetection:
    def test_no_cycles(self):
        adj = {"a": {"b"}, "b": {"c"}}
        assert _detect_cycles(adj) == []

    def test_simple_cycle(self):
        adj = {"a": {"b"}, "b": {"a"}}
        cycles = _detect_cycles(adj)
        assert len(cycles) >= 1

    def test_self_loop(self):
        adj = {"a": {"a"}}
        cycles = _detect_cycles(adj)
        assert len(cycles) >= 1

    def test_complex_dag_no_cycle(self):
        adj = {"a": {"b", "c"}, "b": {"d"}, "c": {"d"}}
        assert _detect_cycles(adj) == []

    def test_diamond_with_cycle(self):
        adj = {"a": {"b", "c"}, "b": {"d"}, "c": {"d"}, "d": {"a"}}
        cycles = _detect_cycles(adj)
        assert len(cycles) >= 1


# ── 2. Schema Validation Tests ──


class TestExtractionSchemaModels:
    def test_candidate_predicate_creation(self):
        cp = CandidatePredicate(
            name="test_pred",
            description="A test predicate",
            claim_type=ClaimType.CAUSAL,
            provenance=Provenance(chapter_id="ch01", confidence=0.7),
        )
        assert cp.name == "test_pred"
        assert cp.claim_type == ClaimType.CAUSAL

    def test_provenance_confidence_bounds(self):
        with pytest.raises(Exception):
            Provenance(chapter_id="ch01", confidence=1.5)

        with pytest.raises(Exception):
            Provenance(chapter_id="ch01", confidence=-0.1)

    def test_proposed_vyapti_defaults(self):
        pv = ProposedVyapti()
        assert pv.causal_status == "empirical"
        assert pv.epistemic_status == "hypothesis"
        assert pv.confidence_existence == 0.7
        assert pv.confidence_formulation == 0.6

    def test_validation_result_default(self):
        vr = ValidationResult()
        assert not vr.is_valid
        assert vr.coverage_ratio == 0.0

    def test_extraction_config_defaults(self):
        cfg = ExtractionConfig()
        assert cfg.ensemble_n == 3
        assert cfg.similarity_threshold == 0.85
        assert cfg.min_confidence == 0.3

    def test_predicate_node_tree(self):
        parent = PredicateNode(
            predicate="parent_pred",
            depth=0,
            children=["child_a", "child_b"],
        )
        child = PredicateNode(
            predicate="child_a",
            parent="parent_pred",
            relation_to_parent=PredicateRelation.COMPOSES,
            depth=1,
        )
        assert child.parent == parent.predicate
        assert child.predicate in parent.children

    def test_synonym_cluster(self):
        sc = SynonymCluster(
            canonical="ltv_exceeds_cac",
            alternatives=["ltv_above_cac", "ltv_greater_than_cac"],
            merge_reason="Same concept",
        )
        assert len(sc.alternatives) == 2

    def test_review_item(self):
        pv = ProposedVyapti(id="V12", name="Test")
        vr = ValidationResult(is_valid=True)
        ri = ReviewItem(vyapti=pv, validation=vr)
        assert ri.decision is None


# ── 3. Stage E Integration Tests ──


class TestStageEValidator:
    def test_valid_proposed_vyaptis_merge(self, minimal_ks, sample_stage_d):
        validator = StageEValidator(minimal_ks)
        augmented, validation = validator.validate_and_merge(sample_stage_d)

        # Should have original + new vyaptis
        assert len(augmented.vyaptis) > len(minimal_ks.vyaptis)
        assert "V12" in augmented.vyaptis
        assert "V13" in augmented.vyaptis

    def test_cycle_detection_removes_bad_vyaptis(self, minimal_ks):
        """A proposed vyapti creating a cycle should be removed."""
        cyclic = StageDOutput(
            new_vyaptis=[
                ProposedVyapti(
                    id="V99",
                    name="Cyclic Rule",
                    statement="Creates a cycle",
                    antecedents=["value_creation"],
                    consequent="positive_unit_economics",
                    confidence_existence=0.7,
                    confidence_formulation=0.6,
                ),
            ],
        )
        validator = StageEValidator(minimal_ks)
        augmented, validation = validator.validate_and_merge(cyclic)

        assert len(validation.cycle_errors) > 0
        # Cyclic vyapti should be removed
        assert "V99" not in augmented.vyaptis

    def test_empty_stage_d_passes(self, minimal_ks):
        empty = StageDOutput()
        validator = StageEValidator(minimal_ks)
        augmented, validation = validator.validate_and_merge(empty)

        assert len(augmented.vyaptis) == len(minimal_ks.vyaptis)
        assert validation.coverage_ratio == 0.0

    def test_coverage_ratio_increases(self, minimal_ks, sample_stage_d):
        validator = StageEValidator(minimal_ks)
        _, validation = validator.validate_and_merge(sample_stage_d)
        assert validation.coverage_ratio > 0.0

    def test_orphan_predicate_detection(self, minimal_ks):
        """Predicates not produced by any rule should be flagged as orphans."""
        orphan_vyapti = StageDOutput(
            new_vyaptis=[
                ProposedVyapti(
                    id="V20",
                    name="Orphan Test",
                    statement="Uses an orphan antecedent",
                    antecedents=["completely_unknown_pred"],
                    consequent="some_result",
                    confidence_existence=0.7,
                    confidence_formulation=0.6,
                ),
            ],
        )
        validator = StageEValidator(minimal_ks)
        _, validation = validator.validate_and_merge(orphan_vyapti)
        assert "completely_unknown_pred" in validation.orphan_predicates

    def test_invalid_causal_status_falls_back(self, minimal_ks):
        """Invalid causal_status string should fall back to EMPIRICAL."""
        bad_status = StageDOutput(
            new_vyaptis=[
                ProposedVyapti(
                    id="V21",
                    name="Bad Status Test",
                    statement="Has invalid causal status",
                    causal_status="not_a_real_status",
                    antecedents=["positive_unit_economics"],
                    consequent="test_output",
                    confidence_existence=0.7,
                    confidence_formulation=0.6,
                ),
            ],
        )
        validator = StageEValidator(minimal_ks)
        augmented, validation = validator.validate_and_merge(bad_status)
        if "V21" in augmented.vyaptis:
            assert augmented.vyaptis["V21"].causal_status == CausalStatus.EMPIRICAL


# ── 4. Evaluation Metric Tests ──


class TestTokenOverlap:
    def test_identical(self):
        assert _token_overlap("ltv_exceeds_cac", "ltv_exceeds_cac") == 1.0

    def test_partial_overlap(self):
        score = _token_overlap("ltv_exceeds_cac", "ltv_above_cac")
        assert 0.3 < score < 1.0  # 'ltv' and 'cac' overlap

    def test_no_overlap(self):
        assert _token_overlap("foo_bar", "baz_qux") == 0.0

    def test_empty(self):
        assert _token_overlap("", "foo") == 0.0


class TestBestMatchScore:
    def test_exact_match(self):
        assert _best_match_score("foo", {"foo", "bar"}) == 1.0

    def test_soft_match(self):
        score = _best_match_score(
            "ltv_exceeds_cac",
            {"ltv_above_cac", "something_else"},
            threshold=0.3,
        )
        assert score > 0

    def test_no_match(self):
        assert _best_match_score("xyz", {"abc", "def"}, threshold=0.5) == 0.0


class TestPredicatePrecisionRecall:
    def test_perfect_precision(self):
        assert predicate_precision(["a", "b"], {"a", "b"}) == 1.0

    def test_zero_precision(self):
        assert predicate_precision(["x", "y"], {"a", "b"}) == 0.0

    def test_partial_precision(self):
        p = predicate_precision(["a", "x"], {"a", "b"})
        assert p == 0.5

    def test_perfect_recall(self):
        assert predicate_recall(["a", "b", "c"], {"a", "b"}) == 1.0

    def test_zero_recall(self):
        assert predicate_recall(["x"], {"a", "b"}) == 0.0

    def test_empty_extracted(self):
        assert predicate_precision([], {"a"}) == 0.0
        assert predicate_recall([], {"a"}) == 0.0


class TestNamingQuality:
    def test_perfect_names(self):
        score = naming_quality(["good_name", "another_good_one"])
        assert score == 1.0

    def test_generic_names_penalized(self):
        score = naming_quality(["predicate", "value"])
        assert score < 1.0

    def test_empty_list(self):
        assert naming_quality([]) == 0.0


class TestVyaptiCompleteness:
    def test_complete_vyapti(self, sample_stage_d):
        score = vyapti_completeness(sample_stage_d)
        assert score > 0.5

    def test_empty_stage_d(self):
        assert vyapti_completeness(StageDOutput()) == 0.0


class TestDAGValidity:
    def test_valid(self):
        assert dag_validity(ValidationResult(is_valid=True)) == 1.0

    def test_invalid(self):
        vr = ValidationResult(cycle_errors=["cycle: a -> b -> a"])
        assert dag_validity(vr) == 0.0


class TestZeroSectionRate:
    def test_no_zero_sections(self):
        sa = StageAOutput(section_count=10, zero_predicate_sections=0)
        assert zero_section_rate(sa) == 1.0

    def test_all_zero_sections(self):
        sa = StageAOutput(section_count=10, zero_predicate_sections=10)
        assert zero_section_rate(sa) == 0.0

    def test_half_zero(self):
        sa = StageAOutput(section_count=10, zero_predicate_sections=5)
        assert zero_section_rate(sa) == 0.5


class TestCompositeEvaluator:
    def test_composite_score_range(self, sample_stage_a, sample_stage_d):
        gold = {"ltv_exceeds_cac", "positive_contribution_margin", "payback_within_runway"}
        evaluator = ExtractionEvaluator(gold)
        validation = ValidationResult(is_valid=True, coverage_ratio=0.3)

        metrics = evaluator.evaluate(sample_stage_a, sample_stage_d, validation)
        assert 0.0 <= metrics["composite"] <= 1.0
        assert "precision" in metrics
        assert "recall" in metrics

    def test_perfect_extraction(self, sample_stage_a, sample_stage_d):
        """When gold exactly matches extracted, precision and recall should be 1.0."""
        gold = {c.name for c in sample_stage_a.candidates}
        evaluator = ExtractionEvaluator(gold)
        validation = ValidationResult(is_valid=True, coverage_ratio=0.5)

        metrics = evaluator.evaluate(sample_stage_a, sample_stage_d, validation)
        assert metrics["precision"] == 1.0
        assert metrics["recall"] == 1.0


# ── 5. HITL Tests ──


class TestHITLReviewer:
    def test_batch_accept_all(self, minimal_ks, sample_stage_d):
        validation = ValidationResult(is_valid=True)
        reviewer = HITLReviewer(minimal_ks, minimal_ks, sample_stage_d, validation)

        decisions = {
            "V12": ReviewDecision.ACCEPT,
            "V13": ReviewDecision.ACCEPT,
        }
        approved = reviewer.review_batch(decisions)
        assert "V12" in approved.vyaptis
        assert "V13" in approved.vyaptis
        assert len(approved.vyaptis) == 4  # 2 original + 2 new

    def test_batch_reject_all(self, minimal_ks, sample_stage_d):
        validation = ValidationResult(is_valid=True)
        reviewer = HITLReviewer(minimal_ks, minimal_ks, sample_stage_d, validation)

        decisions = {
            "V12": ReviewDecision.REJECT,
            "V13": ReviewDecision.REJECT,
        }
        approved = reviewer.review_batch(decisions)
        assert "V12" not in approved.vyaptis
        assert "V13" not in approved.vyaptis
        assert len(approved.vyaptis) == 2

    def test_mixed_decisions(self, minimal_ks, sample_stage_d):
        validation = ValidationResult(is_valid=True)
        reviewer = HITLReviewer(minimal_ks, minimal_ks, sample_stage_d, validation)

        decisions = {
            "V12": ReviewDecision.ACCEPT,
            "V13": ReviewDecision.REJECT,
        }
        approved = reviewer.review_batch(decisions)
        assert "V12" in approved.vyaptis
        assert "V13" not in approved.vyaptis

    def test_summary_counts(self, minimal_ks, sample_stage_d):
        validation = ValidationResult(is_valid=True)
        reviewer = HITLReviewer(minimal_ks, minimal_ks, sample_stage_d, validation)

        reviewer.review_batch({
            "V12": ReviewDecision.ACCEPT,
            "V13": ReviewDecision.REJECT,
        })
        summary = reviewer.summary()
        assert summary["accepted"] == 1
        assert summary["rejected"] == 1


class TestHITLRendering:
    def test_render_vyapti_diff(self):
        v = ProposedVyapti(
            id="V12",
            name="Test Vyapti",
            statement="A test statement",
            antecedents=["pred_a"],
            consequent="pred_b",
        )
        output = render_vyapti_diff(v, 1, 5)
        assert "V12" in output
        assert "Test Vyapti" in output

    def test_render_validation_summary(self):
        vr = ValidationResult(
            is_valid=False,
            cycle_errors=["cycle: a -> b -> a"],
            coverage_ratio=0.25,
        )
        output = render_validation_summary(vr)
        assert "Valid: False" in output
        assert "25.0%" in output

    def test_vyapti_to_yaml_dict(self):
        v = ProposedVyapti(
            id="V12",
            name="Test",
            antecedents=["a", "b"],
            consequent="c",
        )
        d = _vyapti_to_yaml_dict(v)
        assert d["id"] == "V12"
        assert d["antecedents"] == ["a", "b"]
        assert d["consequent"] == "c"


# ── 6. Reward Function Tests ──


class TestRewardFunctions:
    def test_extraction_reward_perfect(self):
        from anvikshiki_v4.predicate_extraction import _extraction_reward

        class MockPred:
            predicates = ["good_name", "another_pred"]
            descriptions = ["desc 1", "desc 2"]
            claim_types = ["causal", "metric"]
            reasoning = "This is a substantial reasoning about the predicates extracted."

        score = _extraction_reward(
            {"existing_predicates": "some_other_pred"},
            MockPred(),
        )
        assert score > 0.7

    def test_extraction_reward_empty(self):
        from anvikshiki_v4.predicate_extraction import _extraction_reward

        class MockPred:
            predicates = []
            descriptions = []
            reasoning = ""

        score = _extraction_reward({}, MockPred())
        assert score == 0.0

    def test_vyapti_reward_conservative(self):
        from anvikshiki_v4.predicate_extraction import _vyapti_construction_reward

        class MockPred:
            name = "Good Vyapti Name"
            statement = "A sufficiently long statement about the relationship"
            causal_status = "empirical"
            epistemic_status = "hypothesis"
            confidence_existence = 0.7
            confidence_formulation = 0.6
            scope_conditions = ["market_maturity"]
            scope_exclusions = []
            sources = ["R01"]
            reasoning = "Good reasoning."

        score = _vyapti_construction_reward({}, MockPred())
        assert score >= 0.8

    def test_vyapti_reward_overconfident_penalized(self):
        from anvikshiki_v4.predicate_extraction import _vyapti_construction_reward

        class MockPred:
            name = "Overconfident"
            statement = "A sufficiently long statement"
            causal_status = "empirical"
            epistemic_status = "established"  # Not conservative
            confidence_existence = 0.95  # Too high
            confidence_formulation = 0.95  # Too high
            scope_conditions = []
            scope_exclusions = []
            sources = []
            reasoning = ""

        score = _vyapti_construction_reward({}, MockPred())
        # Should lose points for overconfidence and established status
        assert score < 0.7
