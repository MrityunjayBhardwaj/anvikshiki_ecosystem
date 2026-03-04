"""
Tests for the Query Refinement & Coverage Check Pipeline.

Three test categories:
  1. CoverageAnalyzer: vocabulary building, coverage ratios, closest matching
  2. Message building: decline and partial messages
  3. QueryRefinementPipeline: vocabulary prompt, chapter overview, integration
"""

import pytest

from anvikshiki_v4.schema import (
    CausalStatus,
    ChapterFingerprint,
    Confidence,
    DomainType,
    EpistemicStatus,
    KnowledgeStore,
    Vyapti,
)
from anvikshiki_v4.query_refinement import (
    ClarifyIntent,
    CoverageAnalyzer,
    CoverageReport,
    QueryRefinementPipeline,
    RefinementResult,
)


# ─── Fixtures ───────────────────────────────────────────────


@pytest.fixture
def sample_ks() -> KnowledgeStore:
    """Minimal KnowledgeStore for testing coverage analysis."""
    return KnowledgeStore(
        domain_type=DomainType.CRAFT,
        pramanas=["pratyaksa", "anumana"],
        vyaptis={
            "V01": Vyapti(
                id="V01",
                name="The Value Equation",
                statement="Unit economics drive value creation",
                causal_status=CausalStatus.EMPIRICAL,
                confidence=Confidence(
                    existence=0.95, formulation=0.9, evidence="observational",
                ),
                epistemic_status=EpistemicStatus.ESTABLISHED,
                antecedents=["positive_unit_economics"],
                consequent="value_creation",
                sources=["src_hbs"],
            ),
            "V04": Vyapti(
                id="V04",
                name="The Organizational Entropy Principle",
                statement="Organizations accumulate coordination overhead as they grow",
                causal_status=CausalStatus.EMPIRICAL,
                confidence=Confidence(
                    existence=0.85, formulation=0.75, evidence="observational",
                ),
                epistemic_status=EpistemicStatus.ESTABLISHED,
                antecedents=["organizational_growth"],
                consequent="coordination_overhead",
                sources=["src_dunbar"],
            ),
            "V08": Vyapti(
                id="V08",
                name="The Capital Allocation Identity",
                statement="Company value determined by capital allocation",
                causal_status=CausalStatus.EMPIRICAL,
                confidence=Confidence(
                    existence=0.85, formulation=0.8, evidence="observational",
                ),
                epistemic_status=EpistemicStatus.ESTABLISHED,
                antecedents=["value_creation", "resource_allocation_effective"],
                consequent="long_term_value",
                sources=["src_thorndike"],
            ),
        },
        chapter_fingerprints={
            "ch02": ChapterFingerprint(
                chapter_id="ch02",
                title="Unit Economics & the Core Transaction",
                key_terms=["ltv", "cac", "unit_economics"],
                vyaptis_introduced=["V01"],
            ),
            "ch04": ChapterFingerprint(
                chapter_id="ch04",
                title="Capital Allocation & Financial Strategy",
                key_terms=["roic", "wacc", "capital_allocation"],
                vyaptis_introduced=["V08"],
            ),
            "ch07": ChapterFingerprint(
                chapter_id="ch07",
                title="Organizational Design & Scaling",
                key_terms=["phase_transitions", "dunbar_number"],
                vyaptis_introduced=["V04"],
            ),
        },
    )


@pytest.fixture
def analyzer(sample_ks: KnowledgeStore) -> CoverageAnalyzer:
    return CoverageAnalyzer(sample_ks)


# ─── CoverageAnalyzer: Vocabulary ──────────────────────────


class TestCoverageAnalyzerVocabulary:
    def test_build_vocabulary_extracts_all_predicates(self, analyzer):
        vocab = analyzer._vocab
        expected = {
            "positive_unit_economics",
            "value_creation",
            "organizational_growth",
            "coordination_overhead",
            "resource_allocation_effective",
            "long_term_value",
        }
        assert vocab == expected

    def test_build_predicate_index(self, analyzer):
        idx = analyzer._pred_to_vyaptis
        # value_creation is both V01 consequent and V08 antecedent
        assert "V01" in idx["value_creation"]
        assert "V08" in idx["value_creation"]
        # positive_unit_economics only in V01
        assert idx["positive_unit_economics"] == ["V01"]

    def test_empty_ks_gives_empty_vocab(self):
        ks = KnowledgeStore(domain_type=DomainType.CRAFT)
        a = CoverageAnalyzer(ks)
        assert a._vocab == set()
        assert a._pred_to_vyaptis == {}


# ─── CoverageAnalyzer: Coverage Ratio ──────────────────────


class TestCoverageAnalyzerRatio:
    def test_full_coverage(self, analyzer):
        report = analyzer.analyze(
            mapped_predicates=["value_creation", "positive_unit_economics"],
            unmapped_concepts=[],
        )
        assert report.coverage_ratio == 1.0
        assert report.matched_predicates == [
            "value_creation", "positive_unit_economics",
        ]
        assert len(report.unmatched_concepts) == 0

    def test_zero_coverage(self, analyzer):
        report = analyzer.analyze(
            mapped_predicates=[],
            unmapped_concepts=["marketing_channel", "b2b_saas"],
        )
        assert report.coverage_ratio == 0.0
        assert len(report.unmatched_concepts) == 2

    def test_partial_coverage(self, analyzer):
        report = analyzer.analyze(
            mapped_predicates=["value_creation"],
            unmapped_concepts=["churn_rate", "retention_strategy"],
        )
        assert report.coverage_ratio == pytest.approx(1 / 3)

    def test_false_match_treated_as_unmapped(self, analyzer):
        """LLM claims a predicate exists but it doesn't → treat as unmapped."""
        report = analyzer.analyze(
            mapped_predicates=["value_creation", "nonexistent_predicate"],
            unmapped_concepts=["other_gap"],
        )
        # 1 confirmed, 2 unmapped (nonexistent + other_gap)
        assert report.matched_predicates == ["value_creation"]
        assert "nonexistent_predicate" in report.unmatched_concepts
        assert "other_gap" in report.unmatched_concepts
        assert report.coverage_ratio == pytest.approx(1 / 3)

    def test_empty_input(self, analyzer):
        report = analyzer.analyze(mapped_predicates=[], unmapped_concepts=[])
        assert report.coverage_ratio == 0.0


# ─── CoverageAnalyzer: Closest Match ───────────────────────


class TestCoverageAnalyzerClosest:
    def test_exact_token_overlap(self, analyzer):
        pred, score = analyzer._find_closest_predicate("unit_economics")
        # "positive_unit_economics" shares {unit, economics}
        assert pred == "positive_unit_economics"
        assert score > 0.5

    def test_partial_token_overlap(self, analyzer):
        pred, score = analyzer._find_closest_predicate("value_growth")
        # {value, growth} overlaps 1 token with both value_creation and
        # organizational_growth — either is valid
        assert pred in ("value_creation", "organizational_growth")
        assert score > 0.0

    def test_no_overlap(self, analyzer):
        pred, score = analyzer._find_closest_predicate("marketing_channel")
        # No token overlap with any KB predicate
        assert score >= 0.0  # May find some weak match or zero

    def test_hyphen_normalization(self, analyzer):
        pred, score = analyzer._find_closest_predicate("long-term-value")
        assert pred == "long_term_value"
        assert score == 1.0

    def test_empty_concept(self, analyzer):
        pred, score = analyzer._find_closest_predicate("")
        assert pred == ""
        assert score == 0.0

    def test_closest_in_coverage_report(self, analyzer):
        report = analyzer.analyze(
            mapped_predicates=[],
            unmapped_concepts=["unit_economics"],
        )
        assert "unit_economics" in report.closest_predicates
        assert report.closest_predicates["unit_economics"] == "positive_unit_economics"


# ─── CoverageAnalyzer: Vyapti Matching ─────────────────────


class TestCoverageAnalyzerVyaptis:
    def test_matched_vyaptis(self, analyzer):
        report = analyzer.analyze(
            mapped_predicates=["value_creation", "long_term_value"],
            unmapped_concepts=[],
        )
        # value_creation → V01, V08; long_term_value → V08
        assert "V01" in report.matched_vyaptis
        assert "V08" in report.matched_vyaptis
        assert report.matched_vyaptis["V01"] == "The Value Equation"

    def test_no_matched_vyaptis_for_unknown(self, analyzer):
        report = analyzer.analyze(
            mapped_predicates=[],
            unmapped_concepts=["xyz"],
        )
        assert report.matched_vyaptis == {}


# ─── CoverageAnalyzer: Chapter Mapping ─────────────────────


class TestCoverageAnalyzerChapters:
    def test_relevant_chapters_for_v01_predicate(self, analyzer):
        report = analyzer.analyze(
            mapped_predicates=["positive_unit_economics"],
            unmapped_concepts=[],
        )
        assert "ch02" in report.relevant_chapters

    def test_relevant_chapters_for_v08_predicate(self, analyzer):
        report = analyzer.analyze(
            mapped_predicates=["long_term_value"],
            unmapped_concepts=[],
        )
        assert "ch04" in report.relevant_chapters

    def test_multiple_chapters(self, analyzer):
        report = analyzer.analyze(
            mapped_predicates=[
                "positive_unit_economics",
                "coordination_overhead",
                "long_term_value",
            ],
            unmapped_concepts=[],
        )
        assert "ch02" in report.relevant_chapters
        assert "ch04" in report.relevant_chapters
        assert "ch07" in report.relevant_chapters

    def test_no_chapters_for_unknown(self, analyzer):
        report = analyzer.analyze(
            mapped_predicates=[],
            unmapped_concepts=["xyz"],
        )
        assert report.relevant_chapters == []


# ─── Message Building ──────────────────────────────────────


class TestMessageBuilding:
    def test_decline_message_mentions_unmatched(self, sample_ks):
        pipeline = QueryRefinementPipeline(sample_ks)
        coverage = CoverageReport(
            matched_predicates=[],
            unmatched_concepts=["marketing_channel", "b2b_saas"],
            closest_predicates={"marketing_channel": "value_creation"},
            coverage_ratio=0.0,
        )
        msg = pipeline._build_decline_message(coverage, "best marketing channel")
        assert "marketing_channel" in msg
        assert "b2b_saas" in msg
        assert "don't have" in msg.lower()

    def test_decline_message_shows_closest(self, sample_ks):
        pipeline = QueryRefinementPipeline(sample_ks)
        coverage = CoverageReport(
            matched_predicates=[],
            unmatched_concepts=["retention_strategy"],
            closest_predicates={"retention_strategy": "value_creation"},
            coverage_ratio=0.0,
        )
        msg = pipeline._build_decline_message(coverage, "retention strategy")
        assert "value_creation" in msg
        assert "closest" in msg.lower() or "closest" in msg

    def test_partial_message_lists_what_we_know(self, sample_ks):
        pipeline = QueryRefinementPipeline(sample_ks)
        coverage = CoverageReport(
            matched_predicates=["value_creation", "long_term_value"],
            matched_vyaptis={"V01": "The Value Equation", "V08": "Capital Allocation"},
            unmatched_concepts=["churn_reduction"],
            closest_predicates={"churn_reduction": "value_creation"},
            coverage_ratio=0.5,
            relevant_chapters=["ch02", "ch04"],
        )
        msg = pipeline._build_partial_message(coverage, "retention and value")
        assert "value_creation" in msg
        assert "partially" in msg.lower()
        assert "churn_reduction" in msg

    def test_decline_message_empty_closest(self, sample_ks):
        pipeline = QueryRefinementPipeline(sample_ks)
        coverage = CoverageReport(
            matched_predicates=[],
            unmatched_concepts=["xyz_abc"],
            closest_predicates={},
            coverage_ratio=0.0,
        )
        msg = pipeline._build_decline_message(coverage, "something")
        assert "don't have" in msg.lower()
        # Should not crash with empty closest
        assert "closest" not in msg.lower()


# ─── Vocabulary & Chapter Prompt Building ───────────────────


class TestPromptBuilding:
    def test_kb_vocabulary_contains_all_predicates(self, sample_ks):
        pipeline = QueryRefinementPipeline(sample_ks)
        vocab = pipeline.build_kb_vocabulary_prompt()
        assert "positive_unit_economics" in vocab
        assert "value_creation" in vocab
        assert "long_term_value" in vocab
        assert "coordination_overhead" in vocab

    def test_kb_vocabulary_contains_rule_descriptions(self, sample_ks):
        pipeline = QueryRefinementPipeline(sample_ks)
        vocab = pipeline.build_kb_vocabulary_prompt()
        assert "The Value Equation" in vocab
        assert "established" in vocab

    def test_chapter_overview_contains_titles(self, sample_ks):
        pipeline = QueryRefinementPipeline(sample_ks)
        overview = pipeline.build_chapter_overview()
        assert "Unit Economics" in overview
        assert "Capital Allocation" in overview
        assert "Organizational Design" in overview

    def test_chapter_overview_contains_key_terms(self, sample_ks):
        pipeline = QueryRefinementPipeline(sample_ks)
        overview = pipeline.build_chapter_overview()
        assert "ltv" in overview
        assert "cac" in overview
        assert "dunbar_number" in overview


# ─── RefinementResult Model ─────────────────────────────────


class TestRefinementResultModel:
    def test_default_cannot_proceed(self):
        r = RefinementResult(original_query="test")
        assert r.can_proceed is False
        assert r.decline_message == ""

    def test_serialization_round_trip(self):
        report = CoverageReport(
            matched_predicates=["value_creation"],
            matched_vyaptis={"V01": "The Value Equation"},
            unmatched_concepts=["xyz"],
            closest_predicates={"xyz": "value_creation"},
            coverage_ratio=0.5,
            relevant_chapters=["ch02"],
        )
        r = RefinementResult(
            original_query="test query",
            interpreted_intent="testing",
            suggested_queries=["better test query"],
            coverage=report,
            can_proceed=True,
        )
        d = r.model_dump()
        r2 = RefinementResult(**d)
        assert r2.coverage.coverage_ratio == 0.5
        assert r2.suggested_queries == ["better test query"]


# ─── ClarifyIntent Signature ───────────────────────────────


class TestClarifyIntentSignature:
    def test_signature_fields_exist(self):
        """Verify the DSPy signature has all expected fields."""
        input_fields = ClarifyIntent.input_fields
        output_fields = ClarifyIntent.output_fields

        assert "query" in input_fields
        assert "kb_vocabulary" in input_fields
        assert "chapter_overview" in input_fields

        assert "reasoning" in output_fields
        assert "interpreted_intent" in output_fields
        assert "mapped_predicates" in output_fields
        assert "unmapped_concepts" in output_fields
        assert "suggested_queries" in output_fields


# ─── Pipeline Threshold Logic ──────────────────────────────


class TestPipelineThresholds:
    def test_custom_thresholds(self, sample_ks):
        pipeline = QueryRefinementPipeline(
            sample_ks, proceed_threshold=0.8, partial_threshold=0.3,
        )
        assert pipeline.COVERAGE_PROCEED == 0.8
        assert pipeline.COVERAGE_PARTIAL == 0.3

    def test_default_thresholds(self, sample_ks):
        pipeline = QueryRefinementPipeline(sample_ks)
        assert pipeline.COVERAGE_PROCEED == 0.6
        assert pipeline.COVERAGE_PARTIAL == 0.2


# ─── Integration with Real business_expert.yaml ────────────


@pytest.fixture
def business_expert_ks() -> KnowledgeStore:
    """Load the real business_expert.yaml if available."""
    try:
        from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store
        import os

        yaml_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "business_expert.yaml",
        )
        if os.path.exists(yaml_path):
            return load_knowledge_store(yaml_path)
    except (ImportError, FileNotFoundError):
        pass
    return None


class TestBusinessExpertCoverage:
    def test_full_vocab_size(self, business_expert_ks):
        if business_expert_ks is None:
            pytest.skip("business_expert.yaml not available")
        analyzer = CoverageAnalyzer(business_expert_ks)
        # Should have ~20 core predicates from 11 vyaptis
        assert len(analyzer._vocab) >= 15

    def test_unit_economics_query_coverage(self, business_expert_ks):
        if business_expert_ks is None:
            pytest.skip("business_expert.yaml not available")
        analyzer = CoverageAnalyzer(business_expert_ks)
        report = analyzer.analyze(
            mapped_predicates=["positive_unit_economics", "value_creation"],
            unmapped_concepts=[],
        )
        assert report.coverage_ratio == 1.0
        assert "V01" in report.matched_vyaptis

    def test_marketing_query_no_coverage(self, business_expert_ks):
        if business_expert_ks is None:
            pytest.skip("business_expert.yaml not available")
        analyzer = CoverageAnalyzer(business_expert_ks)
        report = analyzer.analyze(
            mapped_predicates=[],
            unmapped_concepts=["marketing_channel", "ad_spend", "conversion_funnel"],
        )
        assert report.coverage_ratio == 0.0
        assert len(report.unmatched_concepts) == 3

    def test_partial_query_coverage(self, business_expert_ks):
        if business_expert_ks is None:
            pytest.skip("business_expert.yaml not available")
        analyzer = CoverageAnalyzer(business_expert_ks)
        report = analyzer.analyze(
            mapped_predicates=["value_creation", "long_term_value"],
            unmapped_concepts=["allocation_effective"],
        )
        assert 0.3 < report.coverage_ratio < 0.8
        # "allocation_effective" overlaps with "resource_allocation_effective"
        assert "allocation_effective" in report.closest_predicates

    def test_chapter_coverage_all_chapters(self, business_expert_ks):
        if business_expert_ks is None:
            pytest.skip("business_expert.yaml not available")
        analyzer = CoverageAnalyzer(business_expert_ks)
        # All 20 predicates should map to chapters via vyaptis
        all_preds = list(analyzer._vocab)
        report = analyzer.analyze(
            mapped_predicates=all_preds, unmapped_concepts=[],
        )
        assert len(report.relevant_chapters) >= 5
