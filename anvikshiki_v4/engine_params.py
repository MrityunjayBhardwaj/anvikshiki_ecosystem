# anvikshiki_v4/engine_params.py
"""
Centralized tunable parameters for the Ānvīkṣikī engine.

Every hand-tuned constant lives here. None are "DSPy-optimizable" yet —
they are manually chosen defaults. When we add optimizer support, this
dataclass becomes the search space.

Grouped by subsystem:
  - Compiler: BELIEF_MAP, decay, argument limits
  - Synthesis: reward weights, Refine config
  - Grounding: ensemble size, temperature, confidence thresholds
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


# The hand-authored map from KB status to a belief triple used to live
# here. A KB status is now carried into the reasoning as itself, through
# `lattice.from_kb` — there is no triple to invent, and the four magnitudes
# that were the system's largest block of unjustified numbers are gone
# with the arithmetic that consumed them.


@dataclass(frozen=True)
class CompilerParams:
    """Parameters for the T2 compiler (t2_compiler_v4.py)."""

    # Temporal decay: half-life in days for evidence freshness
    decay_half_life_days: int = 365
    # ln(2) — used in exponential decay formula, NOT a tunable parameter
    LN2: float = field(default=math.log(2), init=False, repr=False)

    # Decay below this threshold triggers undermining attack (asiddha)
    decay_undermine_threshold: float = 0.3

    # Max sub-argument combinations per rule (caps combinatorial explosion)
    max_argument_combos_per_rule: int = 5

    # Fixpoint iteration limit
    max_fixpoint_iterations: int = 100


@dataclass(frozen=True)
class SynthesisParams:
    """Parameters for the response synthesizer (engine_v4.py)."""

    # dspy.Refine configuration
    refine_n: int = 3
    refine_threshold: float = 0.5

    # Minimum response length (characters) to count as substantive
    min_response_length: int = 50

    # Reward function weights (must sum to 1.0)
    reward_substantive: float = 0.20
    reward_sources: float = 0.15
    reward_hedging: float = 0.20
    reward_hetvabhasa_warning: float = 0.15
    reward_no_overconfidence: float = 0.15
    reward_extension_quality: float = 0.15


@dataclass(frozen=True)
class GroundingParams:
    """Parameters for the grounding pipeline (grounding.py)."""

    # Ensemble size per grounding mode
    ensemble_n_full: int = 5
    ensemble_n_partial: int = 3
    ensemble_n_minimal: int = 1

    # LLM temperature for ensemble diversity
    ensemble_temperature: float = 0.7

    # Below this confidence → clarification_needed
    low_confidence_threshold: float = 0.4

    # Below this agreement → trigger round-trip verification
    round_trip_threshold: float = 0.9


@dataclass(frozen=True)
class EngineParams:
    """Top-level parameter container for the entire engine."""

    compiler: CompilerParams = field(default_factory=CompilerParams)
    synthesis: SynthesisParams = field(default_factory=SynthesisParams)
    grounding: GroundingParams = field(default_factory=GroundingParams)


# Singleton default — import this where needed
DEFAULT_PARAMS = EngineParams()
