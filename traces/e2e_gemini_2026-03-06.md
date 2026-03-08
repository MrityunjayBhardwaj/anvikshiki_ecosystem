# Anvikshiki Engine — End-to-End Pipeline Trace

**Date:** 2026-03-06
**Model:** GLM-5 via DeepInfra (`openai/zai-org/GLM-5`) with `ReasoningLM` wrapper
**Adapter:** `dspy.JSONAdapter` (structured output)
**Wall time:** 465.5s
**Guide chapter:** ch02 — Unit Economics & the Core Transaction (16,211 chars)

---

## Table of Contents

1. [Setup](#1-setup)
2. [Phase 0 — Knowledge Store + Guide Compilation](#2-phase-0--knowledge-store--guide-compilation)
   - [T2 Base KB](#t2-base-knowledge-store)
   - [T2b Fine-Grained Extraction](#t2b-fine-grained-extraction-from-guide-prose)
   - [T3 Chunk Compilation](#t3-chunk-compilation)
3. [Component Initialization](#3-component-initialization)
4. [Scenario 1 — Full Coverage (In-Domain)](#4-scenario-1--full-coverage-in-domain-query)
5. [Scenario 2 — Partial Coverage (Tesla Query)](#5-scenario-2--partial-coverage-tesla-query)
6. [Scenario 3 — Out-of-Domain (Decline)](#6-scenario-3--out-of-domain-decline)
7. [Pipeline Summary](#7-pipeline-summary)

---

## 1. Setup

| Parameter | Value |
|-----------|-------|
| LM model | `openai/zai-org/GLM-5` |
| LM wrapper | `ReasoningLM` (strips `response_format`, fallback to `reasoning_content`) |
| Adapter | `dspy.JSONAdapter` |
| `max_tokens` | 4096 |
| `temperature` | 0.7 |
| API base | `https://api.deepinfra.com/v1/openai` |

---

## 2. Phase 0 — Knowledge Store + Guide Compilation

### T2: Base Knowledge Store

**Source:** `anvikshiki_v4/data/business_expert.yaml`
**Domain:** CRAFT
**Vyaptis:** 11 (V01–V11) | **Hetvabhasas:** 8

| ID | Antecedents | Consequent | Type | Status | Confidence |
|----|-------------|------------|------|--------|------------|
| V01 | `positive_unit_economics` | `value_creation` | empirical | established | 0.95 x 0.90 |
| V02 | `binding_constraint_identified` | `resource_allocation_effective` | empirical | established | 0.90 x 0.85 |
| V03 | `superior_information` | `pricing_power` | structural | established | 0.95 x 0.90 |
| V04 | `organizational_growth` | `coordination_overhead` | empirical | established | 0.85 x 0.75 |
| V05 | `coordination_overhead` | `distorted_market_signal` | empirical | established | 0.90 x 0.85 |
| V06 | `strategic_commitment` | `capability_gain` | structural | established | 0.95 x 0.85 |
| V07 | `incentive_alignment` | `organizational_effectiveness` | empirical | established | 0.90 x 0.90 |
| V08 | `value_creation`, `resource_allocation_effective` | `long_term_value` | empirical | established | 0.85 x 0.80 |
| V09 | `incumbent_rational_allocation`, `low_margin_market_entrant` | `disruption_vulnerability` | empirical | contested | 0.75 x 0.70 |
| V10 | `calibration_accuracy` | `decision_quality` | empirical | established | 0.85 x 0.80 |
| V11 | `organizational_growth`, `coordination_overhead` | `not_value_creation` | empirical | hypothesis | 0.70 x 0.65 |

### Guide Text Loaded

| Chapter | Size | Title |
|---------|------|-------|
| ch02 | 16,211 chars | Unit Economics & the Core Transaction |

### T2b: Fine-Grained Extraction from Guide Prose

**Time:** 0.1s (cached) | **New vyaptis:** 17 | **Synonyms:** 5 | **Source sections:** 8

| ID | Predicate | Effect | Source |
|----|-----------|--------|--------|
| V12 | `cash_burn_acceleration` | `cash_burn_acceleration_effect` | guide_extracted |
| V13 | `scale_profitability_evaluable` | `scale_profitability_evaluable_effect` | guide_extracted |
| V14 | `economies_of_scale_present` | `economies_of_scale_present_effect` | guide_extracted, ch02 |
| V15 | `diseconomies_of_scale` | `diseconomies_of_scale_effect` | guide_extracted |
| V16 | `growth_amplifies_economics_sign` | `growth_amplifies_economics_sign_effect` | guide_extracted, ch02 |
| V17 | `negative_unit_economics` | `negative_unit_economics_effect` | guide_extracted, ch02 |
| V18 | `compound_failure_mode` | `compound_failure_mode_effect` | guide_extracted |
| V19 | `revenue_vanity_trap` | `revenue_vanity_trap_effect` | guide_extracted, ch02 |
| V20 | `cycle_sensitivity` | `cycle_sensitivity_effect` | guide_extracted |
| V21 | `self_computation_enables_learning` | `self_computation_enables_learning_effect` | guide_extracted, ch10 |
| V22 | `weak_unit_economics` | `weak_unit_economics_effect` | guide_extracted, ch02 |
| V23 | `fast_growth` | `fast_growth_effect` | guide_extracted, ch07 |
| V24 | `slow_growth` | `slow_growth_effect` | guide_extracted |
| V25 | `value_destruction` | `value_destruction_effect` | guide_extracted, ch07 |
| V26 | `cohort_based_ltv_model` | `cohort_based_ltv_model_effect` | guide_extracted |
| V27 | `geometric_decay_assumption` | `geometric_decay_assumption_effect` | guide_extracted |
| V28 | `survival_analysis_applied` | `survival_analysis_applied_effect` | guide_extracted |

**Synonym Table (Stage C canonicalization):**

| Extracted Term | Canonical Predicate |
|----------------|-------------------|
| `ltv_cac_ratio_indicates_unit_economics` | `positive_unit_economics` |
| `negative_unit_economics` | `positive_unit_economics` |
| `unit_economics_failure` | `positive_unit_economics` |
| `unit_economics_understood` | `positive_unit_economics` |
| `weak_unit_economics` | `positive_unit_economics` |

**Source Section Cross-Links (T2b -> T3a):**

| Vyapti | Chapters |
|--------|----------|
| V14, V16, V17, V19, V22 | ch02 |
| V21 | ch10 |
| V23, V25 | ch07 |

### T3: Chunk Compilation

**Time:** 0.0s | **Chunks:** 10 | **Chapters:** 1

Sample chunks:

| Chunk ID | Vyapti Anchors | Preview |
|----------|---------------|---------|
| `ch02_s000` | V14, V15, V20 | `# CHAPTER 2: Unit Economics & the Core Transaction...` |
| `ch02_s001` | V01, V08, V11, V12, V14, V15, V16, V17, V19, V20, V22, V23, V24, V27 | `### Paksa (The Problem) — MoviePass story...` |
| `ch02_s002` | V01, V05, V08, V11, V14, V15, V16, V17, V20, V21, V23, V24, V27 | `### Hetu (The Principle) — V1 THE VALUE EQUATION...` |

---

## 3. Component Initialization

| Component | Config |
|-----------|--------|
| Coverage Analyzer | 54 predicates in vocabulary |
| T3a Retriever | 10 chunks (real guide text), fallback=True |
| T3b Augmentation | `AugmentationPipeline` ready |
| Grounding Pipeline | 3 modes: MINIMAL (1 call), PARTIAL (N=3), FULL (N=5+RT+solver) |
| Ontology snippet | 7,100 chars, 28 rules |

<details>
<summary>Full Ontology Snippet (Layer 1 Defense) — 28 rules</summary>

```
VALID PREDICATES — use ONLY these:

RULE V01: The Value Equation
  IF: positive_unit_economics
  THEN: value_creation
  SCOPE: commercial_enterprise
  EXCLUDES: subsidized_entity, network_effect_building_phase

RULE V02: The Constraint Cascade
  IF: binding_constraint_identified
  THEN: resource_allocation_effective
  SCOPE: serial_dependency_system
  EXCLUDES: highly_parallel_system

RULE V03: The Information Asymmetry Premium
  IF: superior_information
  THEN: pricing_power
  SCOPE: heterogeneous_quality_market
  EXCLUDES: perfectly_commoditized_market, regulated_disclosure_market

RULE V04: The Organizational Entropy Principle
  IF: organizational_growth
  THEN: coordination_overhead
  EXCLUDES: active_structural_intervention

RULE V05: The Market Signal Decay Law
  IF: coordination_overhead
  THEN: distorted_market_signal
  EXCLUDES: small_team_direct_contact

RULE V06: The Optionality-Commitment Tradeoff
  IF: strategic_commitment
  THEN: capability_gain
  EXCLUDES: abundant_resources_relative_to_opportunity

RULE V07: The Incentive-Behavior Isomorphism
  IF: incentive_alignment
  THEN: organizational_effectiveness
  EXCLUDES: strong_intrinsic_motivation_org

RULE V08: The Capital Allocation Identity
  IF: value_creation, resource_allocation_effective
  THEN: long_term_value
  SCOPE: significant_free_cash_flow
  EXCLUDES: limited_allocation_discretion, regulated_industry

RULE V09: The Disruption Asymmetry
  IF: incumbent_rational_allocation, low_margin_market_entrant
  THEN: disruption_vulnerability
  SCOPE: sustaining_innovation_trajectory
  EXCLUDES: attentive_incumbent, scale_barrier_to_entry

RULE V10: The Judgment Calibration Principle
  IF: calibration_accuracy
  THEN: decision_quality
  EXCLUDES: decisions_under_near_certainty

RULE V11: The Growth Trap
  IF: organizational_growth, coordination_overhead
  THEN: not_value_creation
  EXCLUDES: active_structural_intervention, small_team_direct_contact

RULE V12–V28: [Fine-grained rules extracted from ch02 guide prose]
  (See T2b table above for full list)

ALL VALID PREDICATE NAMES (54):
  binding_constraint_identified, calibration_accuracy, capability_gain,
  cash_burn_acceleration, cash_burn_acceleration_effect,
  cohort_based_ltv_model, cohort_based_ltv_model_effect,
  compound_failure_mode, compound_failure_mode_effect,
  coordination_overhead, cycle_sensitivity, cycle_sensitivity_effect,
  decision_quality, diseconomies_of_scale, diseconomies_of_scale_effect,
  disruption_vulnerability, distorted_market_signal,
  economies_of_scale_present, economies_of_scale_present_effect,
  fast_growth, fast_growth_effect, geometric_decay_assumption,
  geometric_decay_assumption_effect, growth_amplifies_economics_sign,
  growth_amplifies_economics_sign_effect, incentive_alignment,
  incumbent_rational_allocation, long_term_value,
  low_margin_market_entrant, negative_unit_economics,
  negative_unit_economics_effect, not_value_creation,
  organizational_effectiveness, organizational_growth,
  positive_unit_economics, pricing_power, resource_allocation_effective,
  revenue_vanity_trap, revenue_vanity_trap_effect,
  scale_profitability_evaluable, scale_profitability_evaluable_effect,
  self_computation_enables_learning, self_computation_enables_learning_effect,
  slow_growth, slow_growth_effect, strategic_commitment,
  superior_information, survival_analysis_applied,
  survival_analysis_applied_effect, value_creation, value_destruction,
  value_destruction_effect, weak_unit_economics, weak_unit_economics_effect

OUTPUT FORMAT:
  Return predicates as: predicate_name(entity)
  Entity names should be lowercase with underscores.
  Use ONLY predicate names from the list above.
```

</details>

---

## 4. Scenario 1 — Full Coverage (In-Domain Query)

> **Query:** *"Does a company with strong LTV-CAC ratio and positive contribution margin have viable unit economics?"*

### Stage 0: Grounding Pipeline — MINIMAL mode

| Parameter | Value |
|-----------|-------|
| Mode | MINIMAL (1 LLM call, temperature=0) |
| Layers active | L1 ontology constraint, L2 grammar constraint |
| Ensemble | N=1 (no consensus) |
| Round-trip | No |
| Solver feedback | No |
| **Time** | **34.8s** |

**Output:**

```json
{
  "predicates": ["positive_unit_economics(company)"],
  "confidence": 1.00,
  "disputed": [],
  "refinement_rounds": 0,
  "clarification_needed": false
}
```

### Stage 1: Semantic Coverage Analysis

| Predicate | Match Type |
|-----------|-----------|
| `positive_unit_economics(company)` | exact |

**Coverage ratio:** 1 / 1 = **1.00**

| Threshold | Value | Decision |
|-----------|-------|----------|
| FULL | >= 0.60 | **FULL** |
| PARTIAL | >= 0.20 | |
| DECLINE | < 0.20 | |

**Relevant vyaptis:** V01

### Stage 2: Coverage Routing

**Decision: FULL** -> T2 Compilation with augmented KB (no T3b needed)

### Stage 3: T2 Compilation (Facts + Rules -> Argumentation Framework)

**Input facts:**

```json
[{"predicate": "positive_unit_economics", "confidence": 1.0, "sources": []}]
```

**Processing:**

```
Step 3a: Create Premise Arguments
  A0000: positive_unit_economics [premise]
    tag: b=1.000, d=0.000, u=0.000 | pramana=PRATYAKSA

Step 3b: Forward Chain
  V01: positive_unit_economics -> value_creation
    All antecedents available
    -> A0001: value_creation via V01
       sub_arguments: (A0000)
       tag: b=0.9500, d=0.0000, u=0.0500
       pramana: ANUMANA | trust: 0.8550 | decay: 1.0000

Step 3c: Derive Attacks
  (none)

Fixpoint reached — no new arguments. Time: 0.0003s
```

**Argumentation Framework:**

| Argument | Conclusion | Top Rule | Sub-args | Tag (b/d/u) | Pramana | Sources |
|----------|-----------|----------|----------|-------------|---------|---------|
| A0000 | `positive_unit_economics` | [premise] | — | 1.00 / 0.00 / 0.00 | PRATYAKSA | — |
| A0001 | `value_creation` | V01 | (A0000) | 0.95 / 0.00 / 0.05 | ANUMANA | src_ries_2011, src_hbs_unit_economics |

### Stage 4: T3a Retrieval

**Query:** (same as above) | **k:** 3

| Chunk | Chapter | Epistemic | Key Anchors | Preview |
|-------|---------|-----------|-------------|---------|
| `ch02_s002` | ch02 | established | V01, V05, V08, V11, V14–V17, V20, V21, V23, V24, V27 | **V1 — THE VALUE EQUATION:** A business survives if and only if it creates more economic value... |
| `ch02_s005` | ch02 | established | V01, V05, V11, V12, V14–V17, V19, V20, V22, V27 | *High-contrast debate:* Is it ever rational to fund a company with negative unit economics?... |
| `ch02_s001` | ch02 | established | V01, V08, V11, V12, V14–V17, V19, V20, V22–V24, V27 | **Paksa (The Problem):** In 2019, MoviePass offered unlimited movie tickets for $9.95/month... |

### Stage 5: Contestation (Vada)

```
Grounded Semantics — Iteration 1:
  A0000: positive_unit_economics -> no attackers -> IN
  A0001: value_creation           -> no attackers -> IN
  Fixpoint reached.
```

| Argument | Label | Extension |
|----------|-------|-----------|
| A0000 | **IN** | grounded |
| A0001 | **IN** | grounded |

### Stage 6: Epistemic Status

| Predicate | Status | Belief | Disbelief | Uncertainty | Pramana |
|-----------|--------|--------|-----------|-------------|---------|
| `positive_unit_economics` | **established** | 1.00 | 0.00 | 0.00 | PRATYAKSA |
| `value_creation` | **established** | 0.95 | 0.00 | 0.05 | ANUMANA |

### Stage 7: Provenance

| Predicate | Sources | Trust | Decay | Depth |
|-----------|---------|-------|-------|-------|
| `positive_unit_economics` | — | 1.00 | 1.00 | 0 |
| `value_creation` | src_hbs_unit_economics, src_ries_2011 | 0.855 | 1.00 | 0 |

### Stage 8: Uncertainty Decomposition

| Predicate | Epistemic | Aleatoric | Inference | **Total Confidence** |
|-----------|-----------|-----------|-----------|---------------------|
| `positive_unit_economics` | established, u=0.00 | d=0.00 | grounding=1.00, decay=1.00, depth=0 | **1.0000** |
| `value_creation` | established, u=0.05 | d=0.00 | grounding=1.00, decay=1.00, depth=0 | **0.8122** |

### Stage 9: Violations / Hetvabhasa

**Violations: 0** (no conflicts in this query)

### Stage 10: LLM Synthesis

**Time:** 57.8s

**Input fields:**

| Field | Value |
|-------|-------|
| `accepted_arguments` | positive_unit_economics: established (belief=1.00); value_creation: established (belief=0.95) |
| `defeated_arguments` | (none) |
| `uncertainty_report` | positive_unit_economics: confidence=1.00; value_creation: confidence=0.81 |
| `retrieved_prose` | V1 — THE VALUE EQUATION + Paksa (MoviePass) + High-contrast debate (3 chunks) |

**LLM Reasoning:**

> The query asks whether strong LTV-CAC ratio combined with positive contribution margin indicates viable unit economics. The accepted arguments show positive_unit_economics as established (belief=1.00) and value_creation as established (belief=0.95). The retrieved prose confirms that LTV:CAC >= 3:1 is the benchmark for viable unit economics, and explains that the fundamental question is whether the business creates more economic value than it consumes in resources.

**Response:**

> **Yes — established with high confidence.**
>
> A company with a strong LTV-CAC ratio (>=3:1) and positive contribution margin demonstrates viable unit economics. This conclusion rests on two established principles:
>
> **1. The Value Inequality (LTV > CAC):** The fundamental test of business viability at the unit level is whether each customer generates more economic value than it costs to acquire and serve them. The 3:1 benchmark provides a margin of safety against estimation error and accounts for fixed costs not captured in unit calculations.
>
> **2. Contribution Margin as Unit-Level Profitability:** Positive contribution margin confirms the core transaction creates surplus value — each incremental customer adds to business value rather than consuming it.
>
> **Important nuance:** These metrics establish *unit-level* viability. They do not guarantee overall business success, which also depends on fixed costs, market dynamics, and execution. However, they confirm the atomic foundation is sound — growth compounds value rather than accelerating insolvency.
>
> The contrast with MoviePass illustrates why this matters: 3 million subscribers with negative unit economics meant every new customer accelerated failure. Strong LTV-CAC and positive contribution margin indicate the opposite — growth builds genuine value.

**Sources cited:** V1 — THE VALUE EQUATION, Paksa (The Problem)

---

## 5. Scenario 2 — Partial Coverage (Tesla Query)

> **Query:** *"How does Tesla's vertical integration strategy affect its competitive position in the EV market?"*

### Stage 0: Grounding Pipeline — PARTIAL mode

| Parameter | Value |
|-----------|-------|
| Mode | PARTIAL (N=3 ensemble, round-trip if conf < 0.9) |
| **Time** | **150.0s** |

**Output:**

```json
{
  "predicates": [
    "capability_gain(tesla)",
    "economies_of_scale_present(tesla)",
    "strategic_commitment(tesla)",
    "value_creation(tesla)"
  ],
  "confidence": 1.00,
  "disputed": [
    "incumbent_rational_allocation(tesla)",
    "long_term_value(tesla)",
    "positive_unit_economics(tesla)",
    "pricing_power(tesla)",
    "superior_information(tesla)"
  ],
  "refinement_rounds": 0,
  "clarification_needed": false
}
```

4 consensus predicates + 5 disputed predicates across the 3-member ensemble.

### Stage 1: Coverage Analysis

| Predicate | Match |
|-----------|-------|
| `capability_gain(tesla)` | exact |
| `economies_of_scale_present(tesla)` | exact |
| `strategic_commitment(tesla)` | exact |
| `value_creation(tesla)` | exact |

**Coverage:** 4/4 = **1.00** -> **FULL**

### Stage 2: Routing -> T2 Compilation (no T3b needed)

### Stage 3: T2 Compilation

**Input facts:**

```json
[
  {"predicate": "capability_gain", "confidence": 1.0},
  {"predicate": "economies_of_scale_present", "confidence": 1.0},
  {"predicate": "strategic_commitment", "confidence": 1.0},
  {"predicate": "value_creation", "confidence": 1.0}
]
```

**Processing:**

```
Step 3a: Premise Arguments
  A0000: capability_gain           [premise] b=1.00
  A0001: economies_of_scale_present [premise] b=1.00
  A0002: strategic_commitment      [premise] b=1.00
  A0003: value_creation            [premise] b=1.00

Step 3b: Forward Chain
  V06: strategic_commitment -> capability_gain
    -> A0004: capability_gain via V06 (sub: A0002)
       b=0.9500, pramana=ANUMANA
  V14: economies_of_scale_present -> economies_of_scale_present_effect
    -> A0005: economies_of_scale_present_effect via V14 (sub: A0001)
       b=0.8000, pramana=ANUMANA

Step 3c: Attacks — (none)
Fixpoint: Time 0.0003s
```

**Argumentation Framework:** 6 arguments, 0 attacks

| Argument | Conclusion | Rule | Tag (b/d/u) |
|----------|-----------|------|-------------|
| A0000 | `capability_gain` | premise | 1.00/0.00/0.00 |
| A0001 | `economies_of_scale_present` | premise | 1.00/0.00/0.00 |
| A0002 | `strategic_commitment` | premise | 1.00/0.00/0.00 |
| A0003 | `value_creation` | premise | 1.00/0.00/0.00 |
| A0004 | `capability_gain` | V06 | 0.95/0.00/0.05 |
| A0005 | `economies_of_scale_present_effect` | V14 | 0.80/0.00/0.20 |

### Stages 4–9 (abbreviated)

- **T3a Retrieval:** 3 chunks from ch02 (same corpus)
- **Contestation:** All 6 arguments -> **IN** (no attacks)
- **Epistemic:** All conclusions **established**
- **Uncertainty:** Total confidence range 0.64–1.00
- **Violations:** 0

### Stage 10: LLM Synthesis

**Time:** 89.2s

**Response:**

> Tesla's vertical integration strategy creates competitive advantages through multiple reinforcing mechanisms, though with important caveats:
>
> **Strategic Commitment -> Capability Gain (V06, established):** Tesla's decision to vertically integrate battery manufacturing (Gigafactory), chip design (FSD computer), and charging infrastructure represents deep strategic commitment. This generates capability gains that competitors cannot easily replicate.
>
> **Economies of Scale (V14, established):** Vertical integration at Tesla's scale improves unit economics by internalizing margins that would otherwise go to suppliers, and by achieving manufacturing efficiencies.
>
> **Value Creation (V01, established):** The combination of proprietary technology and manufacturing scale contributes to positive unit economics.
>
> **Applicable framework:** The unit economics lens (LTV:CAC, marginal cost analysis) would be needed to determine if vertical integration creates genuine moats or merely operational complexity. Without transparent cost structure data, this remains open.

**Sources cited:** (none — T3a chunks from ch02 didn't directly cite Tesla sources)

---

## 6. Scenario 3 — Out-of-Domain (Decline)

> **Query:** *"What is the best recipe for chocolate souffle?"*

### Stage 0: Grounding Pipeline — FULL mode

| Parameter | Value |
|-----------|-------|
| Mode | FULL (N=5 ensemble + round-trip + solver feedback) |
| **Time** | **~90s** |

**Output:**

```json
{
  "predicates": [],
  "confidence": 0.00,
  "disputed": [],
  "clarification_needed": true
}
```

### Stage 1: Coverage

**Coverage:** 0/0 = **0.00** -> **DECLINE**

### Stage 2b: T3b Domain Check

**Time:** 12.6s

| Field | Value |
|-------|-------|
| `augmented` | false |
| `framework_score` | 0.00 |
| `reason` | Framework applicability too low (0.00 < 0.4) |
| `new_vyaptis` | 0 |

**Decision:** `framework_score` (0.00) < threshold (0.4) -> **DECLINE**

### Decline Response

> *"This query falls outside my domain's reasoning framework."*
> *"Framework applicability too low (0.00 < 0.4)"*

---

## 7. Pipeline Summary

### Totals

| Metric | Value |
|--------|-------|
| **Wall time** | 465.5s |
| **LM** | GLM-5 (DeepInfra) via `ReasoningLM` |
| **KB size** | 28 vyaptis (11 base + 17 fine-grained) |
| **Predicate vocabulary** | 54 predicates |

### Scenario Comparison

| | Scenario 1 | Scenario 2 | Scenario 3 |
|--|-----------|-----------|-----------|
| **Query** | LTV-CAC + contribution margin | Tesla vertical integration | Chocolate souffle |
| **Grounding mode** | MINIMAL | PARTIAL | FULL |
| **Coverage** | 1.00 | 1.00 | 0.00 |
| **Route** | FULL | FULL | DECLINE |
| **Arguments** | 2 | 6 | — |
| **Attacks** | 0 | 0 | — |
| **Grounding confidence** | 1.00 | 1.00 | 0.00 |
| **Disputed predicates** | 0 | 5 | 0 |
| **LLM calls** | grounding (1) + synthesis (1) | grounding (3+RT) + synthesis (1) | grounding (5+RT+solver) + domain check (1) |

### Stage Reference

| Stage | Name | LLM? | Processing |
|-------|------|------|------------|
| 0 | Grounding Pipeline | Yes | 3 modes: MINIMAL / PARTIAL / FULL |
| 0a | — L1: Ontology Constraint | No | All modes |
| 0b | — L2: Grammar Constraint | No | All modes (transparent) |
| 0c | — L3: Ensemble | Yes | MINIMAL=1, PARTIAL=N=3, FULL=N=5 |
| 0d | — L4: Round-trip Verify | Yes | PARTIAL + FULL (if conf < 0.9) |
| 0e | — L5: Solver Feedback | Yes | FULL only (up to 3 rounds) |
| 1 | Coverage Analysis | No | 3-layer match (exact/syn/token) |
| 2 | Coverage Routing | No | FULL/PARTIAL/DECLINE threshold |
| 2b | T3b Augmentation | Yes | ScoreApplicability + Generate |
| 3 | T2 Compilation | No | Forward chain + attacks |
| 4 | T3a Retrieval | No | Embedding/fallback retrieval |
| 5 | Contestation | No | Grounded semantics |
| 6 | Epistemic Status | No | Tag threshold classification |
| 7 | Provenance | No | Tag field extraction |
| 8 | Uncertainty | No | 3-way decomposition |
| 9 | Violations | No | Attack graph scan |
| 10 | LLM Synthesis | Yes | ChainOfThought(SynthesizeResponse) |