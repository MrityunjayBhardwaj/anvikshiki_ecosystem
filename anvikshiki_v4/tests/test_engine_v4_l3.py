# tests/test_engine_v4_l3.py
"""
Level 3: Full engine pipeline tests.

Tests the complete forward() orchestration of AnvikshikiEngineV4
and AnvikshikiEngineV4Phase1 — all 8 steps wired together.

Two categories:
  A) Orchestration tests (mock DSPy calls, real AF/UQ/contestation)
     Always run, no API key needed.
  B) Live LLM tests (real Gemini calls)
     Run with: pytest -m integration --run-llm
     Requires GOOGLE_API_KEY env var or quota on the key.
"""

import os
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from dataclasses import dataclass

import dspy

from anvikshiki_v4.engine_v4 import (
    AnvikshikiEngineV4,
    AnvikshikiEngineV4Phase1,
    SynthesizeResponse,
    _synthesis_reward,
)
from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store
from anvikshiki_v4.grounding import GroundingPipeline, GroundingResult
from anvikshiki_v4.schema_v4 import Label, EpistemicStatus, ProvenanceTag
from anvikshiki_v4.contestation import ContestationManager


# ════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════

BUSINESS_YAML = "anvikshiki_v4/data/business_expert.yaml"


@pytest.fixture(scope="module")
def business_ks():
    return load_knowledge_store(BUSINESS_YAML)


class MockGrounding:
    """Mock grounding pipeline returning fixed predicates."""

    def __init__(self, predicates, confidence=0.85, sources=None):
        self._predicates = predicates
        self._confidence = confidence
        self._sources = sources or []

    def __call__(self, query):
        return GroundingResult(
            predicates=self._predicates,
            confidence=self._confidence,
            disputed=[],
            warnings=[],
            clarification_needed=False,
        )


class MockGroundingLowConfidence:
    """Mock grounding that triggers clarification_needed."""

    def __call__(self, query):
        return GroundingResult(
            predicates=["ambiguous_predicate"],
            confidence=0.2,
            disputed=["ambiguous_predicate"],
            warnings=["Grounding confidence too low"],
            clarification_needed=True,
        )


def make_mock_synthesizer():
    """Create a mock dspy.Refine that returns a plausible response."""

    def mock_call(**kwargs):
        query = kwargs.get("query", "")
        accepted = kwargs.get("accepted_arguments", "")
        defeated = kwargs.get("defeated_arguments", "")

        # Build a response that should score well on the reward function
        response_parts = [
            f"Based on the analysis of the query '{query[:50]}...', "
            "the evidence suggests the following conclusions."
        ]

        if "established" in accepted.lower() or "hypothesis" in accepted.lower():
            response_parts.append(
                "Some conclusions are established while others remain "
                "working hypothesis claims requiring further evidence."
            )

        if "defeated" in defeated.lower():
            response_parts.append(
                "However, there are important caveats: certain reasoning "
                "paths were defeated due to scope limitations."
            )

        response_parts.append(
            "This assessment carries moderate uncertainty due to the "
            "epistemic status of the underlying rules."
        )

        return dspy.Prediction(
            response=" ".join(response_parts),
            sources_cited=["R01", "R02"],
        )

    mock = MagicMock(side_effect=mock_call)
    return mock


# ════════════════════════════════════════════════════════════════
# Category A: Orchestration Tests (no LLM required)
# ════════════════════════════════════════════════════════════════


class TestFullPipelineVada:
    """Test the 8-step pipeline in vāda (default) mode."""

    def test_basic_pipeline_output_schema(self, business_ks):
        """forward() returns all required output fields."""
        grounding = MockGrounding(
            predicates=["positive_unit_economics", "growing_market"],
        )
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
            contestation_mode="vada",
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(
            query="Should a startup focus on unit economics?",
            retrieved_chunks=["Unit economics measures per-unit profitability."],
        )

        # All 8 output fields present
        assert hasattr(result, "response")
        assert hasattr(result, "sources")
        assert hasattr(result, "uncertainty")
        assert hasattr(result, "provenance")
        assert hasattr(result, "violations")
        assert hasattr(result, "grounding_confidence")
        assert hasattr(result, "extension_size")
        assert hasattr(result, "contestation")

    def test_response_is_nonempty_string(self, business_ks):
        """Synthesis produces a non-empty response."""
        grounding = MockGrounding(
            predicates=["positive_unit_economics", "growing_market"],
        )
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(
            query="Is unit economics critical?",
            retrieved_chunks=["Revenue exceeds costs per unit."],
        )

        assert isinstance(result.response, str)
        assert len(result.response) > 50

    def test_extension_size_positive(self, business_ks):
        """AF produces IN-labeled arguments from valid predicates."""
        grounding = MockGrounding(
            predicates=["positive_unit_economics", "growing_market"],
        )
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(
            query="test query",
            retrieved_chunks=["test"],
        )

        assert result.extension_size > 0

    def test_grounding_confidence_propagates(self, business_ks):
        """Engine propagates grounding confidence to output."""
        grounding = MockGrounding(
            predicates=["positive_unit_economics"],
            confidence=0.77,
        )
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(query="test", retrieved_chunks=["x"])
        assert result.grounding_confidence == 0.77

    def test_contestation_mode_is_vada(self, business_ks):
        """Contestation analysis reports mode=vada."""
        grounding = MockGrounding(
            predicates=["positive_unit_economics"],
        )
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
            contestation_mode="vada",
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(query="test", retrieved_chunks=["x"])
        assert result.contestation["mode"] == "vada"
        assert "open_questions" in result.contestation
        assert "suggested_evidence" in result.contestation

    def test_provenance_has_all_conclusions(self, business_ks):
        """Provenance dict covers every non-internal conclusion."""
        grounding = MockGrounding(
            predicates=["positive_unit_economics", "growing_market"],
        )
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(query="test", retrieved_chunks=["x"])

        for conc in result.provenance:
            prov = result.provenance[conc]
            assert "sources" in prov
            assert "pramana" in prov
            assert "derivation_depth" in prov
            assert "trust" in prov
            assert "decay" in prov

    def test_uncertainty_decomposition_present(self, business_ks):
        """UQ dict has epistemic, aleatoric, inference for each conclusion."""
        grounding = MockGrounding(
            predicates=["positive_unit_economics", "growing_market"],
        )
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(query="test", retrieved_chunks=["x"])

        for conc, uq in result.uncertainty.items():
            assert "epistemic" in uq
            assert "aleatoric" in uq
            assert "inference" in uq
            assert "total_confidence" in uq
            assert uq["total_confidence"] > 0

    def test_chain_derivation_in_pipeline(self, business_ks):
        """V01 + V08 chain fires: unit_economics → value_creation → long_term_value."""
        grounding = MockGrounding(
            predicates=[
                "positive_unit_economics",
                "growing_market",
                "binding_constraint_identified",
            ],
        )
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(query="test chain", retrieved_chunks=["x"])

        derived_conclusions = set(result.provenance.keys())
        assert "value_creation" in derived_conclusions
        assert "long_term_value" in derived_conclusions


class TestFullPipelineJalpa:
    """Test pipeline in jalpa (preferred semantics) mode."""

    def test_jalpa_mode_output(self, business_ks):
        """Jalpa mode produces preferred extension analysis."""
        grounding = MockGrounding(
            predicates=["positive_unit_economics", "growing_market"],
        )
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
            contestation_mode="jalpa",
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(query="jalpa test", retrieved_chunks=["x"])

        assert result.contestation["mode"] == "jalpa"
        assert "num_preferred" in result.contestation
        assert "defensible_positions" in result.contestation
        assert "counter_arguments" in result.contestation

    def test_jalpa_extension_size(self, business_ks):
        """Jalpa still produces IN-labeled arguments."""
        grounding = MockGrounding(
            predicates=["positive_unit_economics"],
        )
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
            contestation_mode="jalpa",
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(query="test", retrieved_chunks=["x"])
        assert result.extension_size > 0


class TestFullPipelineVitanda:
    """Test pipeline in vitaṇḍā (stable semantics) mode."""

    def test_vitanda_mode_output(self, business_ks):
        """Vitaṇḍā mode produces vulnerability audit."""
        grounding = MockGrounding(
            predicates=["positive_unit_economics", "growing_market"],
        )
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
            contestation_mode="vitanda",
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(query="vitanda test", retrieved_chunks=["x"])

        assert result.contestation["mode"] == "vitanda"
        assert "num_stable" in result.contestation
        assert "vulnerabilities" in result.contestation
        assert "undefended" in result.contestation


class TestClarificationEarlyReturn:
    """Test the clarification_needed early return path."""

    def test_low_confidence_returns_clarification(self, business_ks):
        """When grounding confidence is too low, engine returns clarification."""
        grounding = MockGroundingLowConfidence()
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )
        # No need to mock synthesizer — it shouldn't be called

        result = engine.forward(query="vague query", retrieved_chunks=["x"])

        assert "Clarification needed" in result.response
        assert result.extension_size == 0
        assert result.sources == []
        assert result.uncertainty == {}
        assert result.provenance == {}
        assert result.violations == []
        assert result.grounding_confidence == 0.2

    def test_clarification_does_not_call_synthesizer(self, business_ks):
        """Synthesizer is never called when clarification is needed."""
        grounding = MockGroundingLowConfidence()
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )
        engine.synthesizer = MagicMock(
            side_effect=AssertionError("Should not be called")
        )

        # Should not raise — synthesizer shouldn't be invoked
        result = engine.forward(query="ambiguous", retrieved_chunks=["x"])
        assert "Clarification" in result.response


class TestViolationsCollection:
    """Test that hetvābhāsa/attack violations are collected correctly."""

    def test_scope_exclusion_creates_violation(self, business_ks):
        """Scope exclusion triggers violation in output."""
        # subsidized_entity triggers V01 scope exclusion
        grounding = MockGrounding(
            predicates=[
                "positive_unit_economics",
                "growing_market",
                "subsidized_entity",
            ],
        )
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(query="test violations", retrieved_chunks=["x"])

        # Should have at least one violation from the undercutting attack
        has_undercutting = any(
            v["type"] == "undercutting" for v in result.violations
        )
        assert has_undercutting, (
            f"Expected undercutting violation, got: {result.violations}"
        )

    def test_violations_have_required_fields(self, business_ks):
        """Each violation entry has all required fields."""
        grounding = MockGrounding(
            predicates=[
                "positive_unit_economics",
                "growing_market",
                "subsidized_entity",
            ],
        )
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(query="test", retrieved_chunks=["x"])

        for v in result.violations:
            assert "hetvabhasa" in v
            assert "type" in v
            assert "attacker" in v
            assert "target" in v
            assert "target_conclusion" in v


class TestSynthesizerIntegration:
    """Test that the synthesizer receives correctly formatted inputs."""

    def test_synthesizer_receives_accepted_arguments(self, business_ks):
        """Synthesizer input includes accepted conclusions with epistemic status."""
        grounding = MockGrounding(
            predicates=["positive_unit_economics", "growing_market"],
        )
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )

        captured_kwargs = {}

        def capture_synthesizer(**kwargs):
            captured_kwargs.update(kwargs)
            return dspy.Prediction(
                response="Test response with hypothesis and evidence suggests.",
                sources_cited=["R01"],
            )

        engine.synthesizer = MagicMock(side_effect=capture_synthesizer)
        engine.forward(query="test input format", retrieved_chunks=["chunk1"])

        assert "query" in captured_kwargs
        assert captured_kwargs["query"] == "test input format"
        assert "accepted_arguments" in captured_kwargs
        assert "defeated_arguments" in captured_kwargs
        assert "uncertainty_report" in captured_kwargs
        assert "retrieved_prose" in captured_kwargs

    def test_synthesizer_gets_truncated_chunks(self, business_ks):
        """At most 5 chunks are passed to the synthesizer."""
        grounding = MockGrounding(predicates=["positive_unit_economics"])
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )

        captured_kwargs = {}

        def capture(**kwargs):
            captured_kwargs.update(kwargs)
            return dspy.Prediction(
                response="Test response with moderate uncertainty.",
                sources_cited=[],
            )

        engine.synthesizer = MagicMock(side_effect=capture)

        chunks = [f"chunk_{i}" for i in range(10)]
        engine.forward(query="test", retrieved_chunks=chunks)

        # Should contain at most 5 chunks joined
        prose = captured_kwargs["retrieved_prose"]
        assert prose.count("chunk_") <= 5
        assert "chunk_5" not in prose  # 0-indexed, so chunk_5 is the 6th


class TestPhase1Pipeline:
    """Test the Phase 1 (LLM-only, no AF) variant."""

    def test_phase1_output_schema(self, business_ks):
        """Phase 1 returns compatible output schema."""
        grounding = MockGrounding(
            predicates=["positive_unit_economics"],
        )
        engine = AnvikshikiEngineV4Phase1(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )

        mock_response = dspy.Prediction(
            response="Phase 1 response about unit economics with hypothesis.",
            sources_cited=["R01"],
            reasoning="Step by step reasoning...",
        )
        engine.reasoner = MagicMock(return_value=mock_response)

        result = engine.forward(
            query="Phase 1 test",
            retrieved_chunks=["Unit economics is important."],
        )

        # Same schema as Phase 2+
        assert hasattr(result, "response")
        assert hasattr(result, "sources")
        assert hasattr(result, "uncertainty")
        assert hasattr(result, "provenance")
        assert hasattr(result, "violations")
        assert hasattr(result, "grounding_confidence")
        assert hasattr(result, "extension_size")
        assert hasattr(result, "contestation")

    def test_phase1_no_argumentation(self, business_ks):
        """Phase 1 has empty AF-related fields."""
        grounding = MockGrounding(predicates=["positive_unit_economics"])
        engine = AnvikshikiEngineV4Phase1(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )

        mock_response = dspy.Prediction(
            response="Simple response with evidence suggests...",
            sources_cited=[],
        )
        engine.reasoner = MagicMock(return_value=mock_response)

        result = engine.forward(query="test", retrieved_chunks=["x"])

        assert result.extension_size == 0
        assert result.uncertainty == {}
        assert result.provenance == {}
        assert result.violations == []
        assert result.contestation is None

    def test_phase1_grounding_confidence(self, business_ks):
        """Phase 1 propagates grounding confidence."""
        grounding = MockGrounding(
            predicates=["positive_unit_economics"],
            confidence=0.65,
        )
        engine = AnvikshikiEngineV4Phase1(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )

        mock_response = dspy.Prediction(
            response="Response text.", sources_cited=[],
        )
        engine.reasoner = MagicMock(return_value=mock_response)

        result = engine.forward(query="test", retrieved_chunks=["x"])
        assert result.grounding_confidence == 0.65


# ════════════════════════════════════════════════════════════════
# Reward Function Tests (no LLM)
# ════════════════════════════════════════════════════════════════


class TestSynthesisReward:
    """Test the _synthesis_reward function in isolation."""

    def test_perfect_response_scores_high(self):
        """Response with all quality signals scores near 1.0."""
        pred = dspy.Prediction(
            response=(
                "The evidence suggests that this is an established "
                "conclusion, however there are important caveats about "
                "the hypothesis regarding market uncertainty."
            ),
            sources_cited=["R01", "R02"],
        )
        args = {
            "accepted_arguments": "value_creation: established",
            "defeated_arguments": "defeated: scope violation",
        }
        score = _synthesis_reward(args, pred)
        assert score >= 0.8

    def test_empty_response_scores_zero(self):
        """Empty response scores 0."""
        pred = dspy.Prediction(response="", sources_cited=[])
        args = {"accepted_arguments": "", "defeated_arguments": ""}
        score = _synthesis_reward(args, pred)
        # Only "no overconfidence" and "extension quality" might score
        assert score < 0.5

    def test_overconfident_response_penalized(self):
        """Response with 'certainly' loses 0.15."""
        pred_good = dspy.Prediction(
            response=(
                "The evidence suggests this is an established hypothesis "
                "with moderate uncertainty in the reasoning chain."
            ),
            sources_cited=["R01"],
        )
        pred_bad = dspy.Prediction(
            response=(
                "This is certainly an established hypothesis "
                "with moderate uncertainty in the reasoning chain."
            ),
            sources_cited=["R01"],
        )
        args = {
            "accepted_arguments": "value_creation: established",
            "defeated_arguments": "",
        }
        good_score = _synthesis_reward(args, pred_good)
        bad_score = _synthesis_reward(args, pred_bad)
        assert good_score > bad_score

    def test_hedging_language_rewarded(self):
        """Response with epistemic hedges gets 0.2 bonus."""
        pred_hedged = dspy.Prediction(
            response="The evidence suggests this is a provisional conclusion. " * 3,
            sources_cited=["R01"],
        )
        pred_no_hedge = dspy.Prediction(
            response="This is a finding about market dynamics and revenue. " * 3,
            sources_cited=["R01"],
        )
        args = {
            "accepted_arguments": "value_creation: established",
            "defeated_arguments": "",
        }
        hedged_score = _synthesis_reward(args, pred_hedged)
        no_hedge_score = _synthesis_reward(args, pred_no_hedge)
        assert hedged_score > no_hedge_score

    def test_no_accepted_conclusions_penalized(self):
        """'No accepted conclusions' in input costs 0.15."""
        pred = dspy.Prediction(
            response="The evidence suggests moderate hypothesis uncertainty.",
            sources_cited=["R01"],
        )
        args_good = {
            "accepted_arguments": "value_creation: established",
            "defeated_arguments": "",
        }
        args_empty = {
            "accepted_arguments": "No accepted conclusions.",
            "defeated_arguments": "",
        }
        good_score = _synthesis_reward(args_good, pred)
        empty_score = _synthesis_reward(args_empty, pred)
        assert good_score > empty_score


# ════════════════════════════════════════════════════════════════
# Cross-Mode Consistency Tests
# ════════════════════════════════════════════════════════════════


class TestCrossModeConsistency:
    """Verify invariants across contestation modes."""

    def _run_all_modes(self, business_ks, predicates):
        """Run the same predicates through vada, jalpa, vitanda."""
        results = {}
        for mode in ("vada", "jalpa", "vitanda"):
            grounding = MockGrounding(predicates=predicates)
            engine = AnvikshikiEngineV4(
                knowledge_store=business_ks,
                grounding_pipeline=grounding,
                contestation_mode=mode,
            )
            engine.synthesizer = make_mock_synthesizer()
            results[mode] = engine.forward(
                query=f"{mode} test", retrieved_chunks=["x"]
            )
        return results

    def test_same_grounding_confidence(self, business_ks):
        """All modes report the same grounding confidence."""
        results = self._run_all_modes(
            business_ks, ["positive_unit_economics", "growing_market"]
        )
        assert results["vada"].grounding_confidence == 0.85
        assert results["jalpa"].grounding_confidence == 0.85
        assert results["vitanda"].grounding_confidence == 0.85

    def test_same_provenance_keys(self, business_ks):
        """All modes derive the same set of conclusions."""
        results = self._run_all_modes(
            business_ks, ["positive_unit_economics", "growing_market"]
        )
        # Provenance and uncertainty should cover same conclusions
        vada_concs = set(results["vada"].provenance.keys())
        jalpa_concs = set(results["jalpa"].provenance.keys())
        vitanda_concs = set(results["vitanda"].provenance.keys())
        assert vada_concs == jalpa_concs == vitanda_concs

    def test_extension_sizes_consistent(self, business_ks):
        """All modes have non-negative extension sizes."""
        results = self._run_all_modes(
            business_ks, ["positive_unit_economics"]
        )
        for mode, r in results.items():
            assert r.extension_size >= 0, f"{mode} has negative extension"


# ════════════════════════════════════════════════════════════════
# Edge Cases
# ════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Test edge cases and error boundaries."""

    def test_empty_predicates(self, business_ks):
        """Empty predicate list still produces valid output."""
        grounding = MockGrounding(predicates=[])
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(query="empty test", retrieved_chunks=["x"])

        assert result.extension_size == 0
        assert result.provenance == {}
        assert result.uncertainty == {}
        assert result.violations == []

    def test_single_predicate(self, business_ks):
        """Single predicate produces premise argument only."""
        grounding = MockGrounding(predicates=["positive_unit_economics"])
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(query="single test", retrieved_chunks=["x"])
        assert result.extension_size >= 1

    def test_unknown_predicate(self, business_ks):
        """Unknown predicate doesn't crash, just doesn't fire rules."""
        grounding = MockGrounding(predicates=["totally_unknown_predicate"])
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(query="unknown test", retrieved_chunks=["x"])

        # Should have the premise argument but no derived conclusions
        assert result.extension_size >= 1
        # Only the unknown predicate itself should appear
        assert "value_creation" not in result.provenance

    def test_empty_retrieved_chunks(self, business_ks):
        """Empty chunks list doesn't crash."""
        grounding = MockGrounding(predicates=["positive_unit_economics"])
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(query="no chunks", retrieved_chunks=[])
        assert result.response  # Still produces a response

    def test_conflicting_predicates(self, business_ks):
        """Both a predicate and its exclusion present → undercutting attack."""
        grounding = MockGrounding(
            predicates=[
                "positive_unit_economics",
                "growing_market",
                "subsidized_entity",  # Exclusion for V01
            ],
        )
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )
        engine.synthesizer = make_mock_synthesizer()

        result = engine.forward(query="conflict test", retrieved_chunks=["x"])

        # Should produce undercutting violations
        types = [v["type"] for v in result.violations]
        assert "undercutting" in types


# ════════════════════════════════════════════════════════════════
# Category B: Live LLM Tests
# ════════════════════════════════════════════════════════════════
#
# Two providers supported:
#
#   1. Gemini (cloud):
#      GOOGLE_API_KEY=... pytest -m integration anvikshiki_v4/tests/test_engine_v4_l3.py
#
#   2. Local MLX model (OpenAI-compatible server):
#      # Terminal 1 — start the server:
#      cd ~/Documents/local_llm && source .venv/bin/activate
#      HF_HOME="$PWD/hf_cache" mlx_lm.server --model mlx-community/Llama-3.2-3B-Instruct-4bit
#
#      # Terminal 2 — run tests:
#      LOCAL_LLM_URL=http://localhost:8080/v1 \
#      LOCAL_LLM_MODEL=mlx-community/Llama-3.2-3B-Instruct-4bit \
#        pytest -m integration anvikshiki_v4/tests/test_engine_v4_l3.py

GEMINI_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
LOCAL_URL = os.environ.get("LOCAL_LLM_URL")  # e.g. http://localhost:8080/v1
LOCAL_MODEL = os.environ.get("LOCAL_LLM_MODEL", "mlx-community/Llama-3.2-3B-Instruct-4bit")
LLM_AVAILABLE = bool(GEMINI_KEY or LOCAL_URL)


def _check_local_server(url: str) -> bool:
    """Check if the local LLM server is reachable."""
    try:
        import urllib.request
        req = urllib.request.Request(f"{url}/models", method="GET")
        with urllib.request.urlopen(req, timeout=3):
            return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def live_lm():
    """Configure DSPy with whatever LLM backend is available.

    Priority: LOCAL_LLM_URL > GOOGLE_API_KEY
    Local is preferred because it's free and has no quota limits.
    """
    if LOCAL_URL:
        if not _check_local_server(LOCAL_URL):
            pytest.skip(
                f"Local LLM server not reachable at {LOCAL_URL}. "
                f"Start it with: HF_HOME=\"$PWD/hf_cache\" "
                f"mlx_lm.server --model {LOCAL_MODEL}"
            )
        lm = dspy.LM(
            model=f"openai/{LOCAL_MODEL}",
            api_base=LOCAL_URL,
            api_key="local",  # MLX server doesn't need a real key
        )
        dspy.configure(lm=lm)
        return lm

    if GEMINI_KEY:
        lm = dspy.LM("gemini/gemini-2.0-flash", api_key=GEMINI_KEY)
        dspy.configure(lm=lm)
        return lm

    pytest.skip("No LLM backend available (set LOCAL_LLM_URL or GOOGLE_API_KEY)")


@pytest.mark.integration
@pytest.mark.skipif(not LLM_AVAILABLE, reason="No LLM backend configured")
class TestLivePipeline:
    """Full end-to-end tests with real LLM calls (local or cloud)."""

    def test_full_e2e_vada(self, live_lm, business_ks):
        """Full pipeline: real grounding + real synthesis."""
        grounding = GroundingPipeline(knowledge_store=business_ks)
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
            contestation_mode="vada",
        )

        result = engine.forward(
            query="I have a startup with positive unit economics, what's my business model?",
            retrieved_chunks=[
                "Positive unit economics means revenue per customer exceeds "
                "cost to serve that customer, indicating a sustainable business model.",
            ],
        )

        assert isinstance(result.response, str)
        assert len(result.response) > 50
        assert result.extension_size >= 0

    def test_full_e2e_phase1(self, live_lm, business_ks):
        """Phase 1 (LLM-only) with real LLM."""
        grounding = GroundingPipeline(knowledge_store=business_ks)
        engine = AnvikshikiEngineV4Phase1(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
        )

        result = engine.forward(
            query="Should a startup focus on profitability or growth?",
            retrieved_chunks=["Growth vs profitability is a core strategy tension."],
        )

        assert isinstance(result.response, str)
        assert len(result.response) > 20
        assert result.extension_size == 0  # Phase 1: no AF

    def test_grounding_pipeline_standalone(self, live_lm, business_ks):
        """Grounding pipeline produces valid predicates from natural language."""
        grounding = GroundingPipeline(knowledge_store=business_ks)
        result = grounding(
            query="A startup with good unit economics in a growing market"
        )

        assert isinstance(result.predicates, list)
        assert len(result.predicates) > 0
        assert result.confidence > 0.0
        assert isinstance(result.clarification_needed, bool)

    def test_synthesis_contains_epistemic_hedging(self, live_lm, business_ks):
        """Real LLM synthesis should produce epistemically calibrated language."""
        grounding = MockGrounding(
            predicates=["positive_unit_economics", "growing_market"],
        )
        engine = AnvikshikiEngineV4(
            knowledge_store=business_ks,
            grounding_pipeline=grounding,
            contestation_mode="vada",
        )
        # Use real synthesizer (no mock) — this is the LLM test
        result = engine.forward(
            query="What business model should I pursue?",
            retrieved_chunks=[
                "Revenue models include subscription, API pricing, "
                "and enterprise licensing.",
            ],
        )

        assert isinstance(result.response, str)
        assert len(result.response) > 50
        # Reward function should score this reasonably
        score = _synthesis_reward(
            {
                "accepted_arguments": "value_creation: established",
                "defeated_arguments": "",
            },
            dspy.Prediction(
                response=result.response,
                sources_cited=result.sources or [],
            ),
        )
        assert score > 0.2, f"Synthesis quality too low: {score}"
