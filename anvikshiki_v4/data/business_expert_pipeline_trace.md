# End-to-End Engine Trace: Business Expert Knowledge Base

**Scenario:** A growing AI startup with positive unit economics,
identified binding constraint, and organizational growth.

**Query Facts:**
1. `positive_unit_economics` (confidence: 0.90)
2. `binding_constraint_identified` (confidence: 0.85)
3. `organizational_growth` (confidence: 0.80)

---

## Stage 0: Load Knowledge Store from YAML

**Source:** `anvikshiki_v4/data/business_expert.yaml`
**Domain type:** CRAFT
**Pramāṇas:** ['pratyaksa', 'anumana', 'sabda', 'upamana']
**Vyāptis loaded:** 11
**Hetvābhāsas loaded:** 8
**Threshold concepts:** 3
**Reference bank:** 29 sources

### Vyāpti Inventory

| ID | Name | Antecedents | Consequent | Causal | Epistemic | Scope Exclusions |
|-----|------|-------------|------------|--------|-----------|-----------------|
| V01 | The Value Equation | positive_unit_economics | value_creation | empirical | established | subsidized_entity, network_effect_building_phase |
| V02 | The Constraint Cascade | binding_constraint_identified | resource_allocation_effective | empirical | established | highly_parallel_system |
| V03 | The Information Asymmetry Premium | superior_information | pricing_power | structural | established | perfectly_commoditized_market, regulated_disclosure_market |
| V04 | The Organizational Entropy Principle | organizational_growth | coordination_overhead | empirical | established | active_structural_intervention |
| V05 | The Market Signal Decay Law | coordination_overhead | distorted_market_signal | empirical | established | small_team_direct_contact |
| V06 | The Optionality-Commitment Tradeoff | strategic_commitment | capability_gain | structural | established | abundant_resources_relative_to_opportunity |
| V07 | The Incentive-Behavior Isomorphism | incentive_alignment | organizational_effectiveness | empirical | established | strong_intrinsic_motivation_org |
| V08 | The Capital Allocation Identity | value_creation, resource_allocation_effective | long_term_value | empirical | established | limited_allocation_discretion, regulated_industry |
| V09 | The Disruption Asymmetry | incumbent_rational_allocation, low_margin_market_entrant | disruption_vulnerability | empirical | contested | attentive_incumbent, scale_barrier_to_entry |
| V10 | The Judgment Calibration Principle | calibration_accuracy | decision_quality | empirical | established | decisions_under_near_certainty |
| V11 | The Growth Trap | organizational_growth, coordination_overhead | not_value_creation | empirical | hypothesis | active_structural_intervention, small_team_direct_contact |

### Hetvābhāsa Inventory

| ID | Name | Detection Signature |
|-----|------|-------------------|
| H01 | The Revenue Vanity Trap | `revenue_growth_cited_without_unit_economics` |
| H02 | The Framework Reification Error | `single_framework_treated_as_complete_model` |
| H03 | The Survivorship Inference | `success_stories_only` |
| H04 | The Correlation-Strategy Confusion | `correlational_claim_presented_as_causal` |
| H05 | The Scalability Presumption | `linear_extrapolation_across_scale_thresholds` |
| H06 | The Sunk Cost Anchor | `prior_investment_cited_as_reason_to_continue` |
| H07 | The Moat Mirage | `no_competitors_equated_with_competitive_advantage` |
| H08 | The Metric Goodhart | `metric_improvement_without_goal_verification` |

### Chain & Conflict Map (derived from antecedent/consequent overlap)

**Chains (consequent of one feeds antecedent of another):**
- V01 (`value_creation`) → V08
- V02 (`resource_allocation_effective`) → V08
- V04 (`coordination_overhead`) → V05
- V04 (`coordination_overhead`) → V11

**Rebutting conflicts (X vs not_X):**
- `value_creation` (from ['V01']) ⚔ `not_value_creation` (from ['V11'])

---

## Stage 1: Create Premise Arguments from Query Facts

**Input:** 3 query facts

**Processing:** For each fact, create a premise argument with:
- `is_strict = True` (premises are axioms)
- `pramana_type = PRATYAKSA` (direct observation)
- `trust_score = 1.0`, `decay_factor = 1.0`
- `belief = confidence`, `uncertainty = 1 - confidence`

**Output:** Premise arguments

| Arg ID | Conclusion | Strict | Tag (b, d, u) | Pramāṇa | Strength |
|--------|-----------|--------|---------------|---------|----------|
| A0000 | `positive_unit_economics` | True | (0.90, 0.00, 0.10) | PRATYAKSA | 0.9000 |
| A0001 | `binding_constraint_identified` | True | (0.85, 0.00, 0.15) | PRATYAKSA | 0.8500 |
| A0002 | `organizational_growth` | True | (0.80, 0.00, 0.20) | PRATYAKSA | 0.8000 |

---

## Stage 2: Forward Chaining — Rule Argument Derivation

### Iteration 1

**Available conclusions:** `['binding_constraint_identified', 'organizational_growth', 'positive_unit_economics']`

**Rule matching:**

- V01 (The Value Equation): needs `['positive_unit_economics']` → ✓ FIRES
- V02 (The Constraint Cascade): needs `['binding_constraint_identified']` → ✓ FIRES
- V03 (The Information Asymmetry Premium): needs `['superior_information']` → ✗ skipped (missing: ['superior_information'])
- V04 (The Organizational Entropy Principle): needs `['organizational_growth']` → ✓ FIRES
- V05 (The Market Signal Decay Law): needs `['coordination_overhead']` → ✗ skipped (missing: ['coordination_overhead'])
- V06 (The Optionality-Commitment Tradeoff): needs `['strategic_commitment']` → ✗ skipped (missing: ['strategic_commitment'])
- V07 (The Incentive-Behavior Isomorphism): needs `['incentive_alignment']` → ✗ skipped (missing: ['incentive_alignment'])
- V08 (The Capital Allocation Identity): needs `['value_creation', 'resource_allocation_effective']` → ✗ skipped (missing: ['value_creation', 'resource_allocation_effective'])
- V09 (The Disruption Asymmetry): needs `['incumbent_rational_allocation', 'low_margin_market_entrant']` → ✗ skipped (missing: ['incumbent_rational_allocation', 'low_margin_market_entrant'])
- V10 (The Judgment Calibration Principle): needs `['calibration_accuracy']` → ✗ skipped (missing: ['calibration_accuracy'])
- V11 (The Growth Trap): needs `['organizational_growth', 'coordination_overhead']` → ✗ skipped (missing: ['coordination_overhead'])

**New arguments derived:** 3

**Tag construction detail (for each fired rule):**

**V01 → `value_creation`**
  1. Causal status `empirical` → pramāṇa `ANUMANA`
  2. Epistemic status `established` → (b=0.95, d=0.0, u=0.05)
  3. Trust = formulation(0.9) × existence(0.95) = 0.8550
  4. Rule tag: Tag(b=0.95, d=0.00, u=0.05, pramana=ANUMANA, trust=0.8550)
  5. Sub-arguments: ['A0000']
     - A0000: `positive_unit_economics` tag strength=0.9000
  6. Tensor composition (rule ⊗ sub-arg₁ ⊗ sub-arg₂ ...):
     Combined tag: Tag(b=0.8550, d=0.0000, u=0.1450)
     Strength: 0.7310
  7. is_strict = False (causal_status=empirical)

**V02 → `resource_allocation_effective`**
  1. Causal status `empirical` → pramāṇa `ANUMANA`
  2. Epistemic status `established` → (b=0.95, d=0.0, u=0.05)
  3. Trust = formulation(0.85) × existence(0.9) = 0.7650
  4. Rule tag: Tag(b=0.95, d=0.00, u=0.05, pramana=ANUMANA, trust=0.7650)
  5. Sub-arguments: ['A0001']
     - A0001: `binding_constraint_identified` tag strength=0.8500
  6. Tensor composition (rule ⊗ sub-arg₁ ⊗ sub-arg₂ ...):
     Combined tag: Tag(b=0.8075, d=0.0000, u=0.1925)
     Strength: 0.6177
  7. is_strict = False (causal_status=empirical)

**V04 → `coordination_overhead`**
  1. Causal status `empirical` → pramāṇa `ANUMANA`
  2. Epistemic status `established` → (b=0.95, d=0.0, u=0.05)
  3. Trust = formulation(0.75) × existence(0.85) = 0.6375
  4. Rule tag: Tag(b=0.95, d=0.00, u=0.05, pramana=ANUMANA, trust=0.6375)
  5. Sub-arguments: ['A0002']
     - A0002: `organizational_growth` tag strength=0.8000
  6. Tensor composition (rule ⊗ sub-arg₁ ⊗ sub-arg₂ ...):
     Combined tag: Tag(b=0.7600, d=0.0000, u=0.2400)
     Strength: 0.4845
  7. is_strict = False (causal_status=empirical)

### Iteration 1 — Attack Derivation

**Checking for rebutting attacks (contradictory conclusions):**


**Checking for undercutting attacks (scope exclusions):**

- V01 (`value_creation`): exclusion `subsidized_entity` not present → no attack
- V01 (`value_creation`): exclusion `network_effect_building_phase` not present → no attack
- V02 (`resource_allocation_effective`): exclusion `highly_parallel_system` not present → no attack
- V04 (`coordination_overhead`): exclusion `active_structural_intervention` not present → no attack

**Checking for undermining attacks (decay-expired):**

- No arguments below decay threshold (0.3)

**New attacks this iteration:** 0

### Iteration 2 (fixpoint check)

New arguments: 3. Continuing...

### Complete Argumentation Framework After Compilation

**Total arguments:** 9
**Total attacks:** 2

| Arg ID | Conclusion | Rule | Sub-Args | Strict | Tag (b, d, u) | Strength | Sources |
|--------|-----------|------|----------|--------|---------------|----------|---------|
| A0000 | `positive_unit_economics` | premise | — | True | (0.9000, 0.0000, 0.1000) | 0.9000 | 0 |
| A0001 | `binding_constraint_identified` | premise | — | True | (0.8500, 0.0000, 0.1500) | 0.8500 | 0 |
| A0002 | `organizational_growth` | premise | — | True | (0.8000, 0.0000, 0.2000) | 0.8000 | 0 |
| A0003 | `value_creation` | V01 | A0000 | False | (0.8550, 0.0000, 0.1450) | 0.7310 | 2 |
| A0004 | `resource_allocation_effective` | V02 | A0001 | False | (0.8075, 0.0000, 0.1925) | 0.6177 | 2 |
| A0005 | `coordination_overhead` | V04 | A0002 | False | (0.7600, 0.0000, 0.2400) | 0.4845 | 3 |
| A0006 | `distorted_market_signal` | V05 | A0005 | False | (0.7220, 0.0000, 0.2780) | 0.4603 | 5 |
| A0007 | `long_term_value` | V08 | A0003, A0004 | False | (0.6559, 0.0000, 0.3441) | 0.4460 | 7 |
| A0008 | `not_value_creation` | V11 | A0002, A0005 | False | (0.3494, 0.0958, 0.5548) | 0.1590 | 3 |

**Attack graph:**

- A0003 (`value_creation`, str=0.731) —[rebutting/viruddha]→ A0008 (`not_value_creation`, str=0.159)
- A0008 (`not_value_creation`, str=0.159) —[rebutting/viruddha]→ A0003 (`value_creation`, str=0.731)

---

## Stage 3: Grounded Semantics — Label Computation

**Algorithm:** Wu, Caminada & Gabbay (2009) iterative propagation

**Steps:**
1. Initialize all labels to UNDECIDED
2. Label arguments with no attackers as IN
3. If all attackers of an argument are OUT, label it IN
4. If any attacker of an argument is IN, label it OUT
5. For rebutting attacks between IN candidates, use `_defeats()` (pramāṇa preference + strength)
6. Repeat until stable

**Result:**

| Arg ID | Conclusion | Label | Strength | Reason |
|--------|-----------|-------|----------|--------|
| A0000 | `positive_unit_economics` | **in** | 0.9000 | no attackers |
| A0001 | `binding_constraint_identified` | **in** | 0.8500 | no attackers |
| A0002 | `organizational_growth` | **in** | 0.8000 | no attackers |
| A0003 | `value_creation` | **in** | 0.7310 | all attackers OUT: [('A0008', <Label.OUT: 'out'>)] |
| A0004 | `resource_allocation_effective` | **in** | 0.6177 | no attackers |
| A0005 | `coordination_overhead` | **in** | 0.4845 | no attackers |
| A0006 | `distorted_market_signal` | **in** | 0.4603 | no attackers |
| A0007 | `long_term_value` | **in** | 0.4460 | no attackers |
| A0008 | `not_value_creation` | **out** | 0.1590 | attacked by IN: ['A0003'] |

### Defeat Analysis: value_creation vs not_value_creation

- `value_creation` (A0003): pramāṇa=ANUMANA(3), strength=0.7310
- `not_value_creation` (A0008): pramāṇa=ANUMANA(3), strength=0.1590

**_defeats() logic for rebutting:**
  1. Both are rebutting (not undercutting) → check strict protection
  2. Target `value_creation` is_strict=False → not protected
  3. Target `not_value_creation` is_strict=False → not protected
  4. Compare pramāṇa types: ANUMANA(3) vs ANUMANA(3)
  5. Same pramāṇa → compare strength: 0.7310 vs 0.1590
     Strength comparison → `value_creation` wins

**Outcome:** `value_creation` is IN, `not_value_creation` is OUT

---

## Stage 4: Epistemic Status Derivation

**Algorithm:** `get_epistemic_status(conclusion)` applies:
- If all arguments for conclusion are IN → use tag thresholds
- If any argument is OUT → CONTESTED
- If all UNDECIDED → OPEN

**Tag → Status thresholds:**
- ESTABLISHED: belief > 0.8 AND uncertainty ≤ 0.1
- HYPOTHESIS: belief > 0.5 AND uncertainty < 0.3
- PROVISIONAL: belief > 0.5 (but doesn't meet HYPOTHESIS)
- OPEN: otherwise

| Conclusion | Epistemic Status | Tag (b, d, u) | Label | Reasoning |
|-----------|-----------------|---------------|-------|-----------|
| `binding_constraint_identified` | **hypothesis** | (0.85, 0.00, 0.15) | in | b=0.85>0.5, u=0.15<0.3 → HYPOTHESIS |
| `coordination_overhead` | **hypothesis** | (0.76, 0.00, 0.24) | in | b=0.76>0.5, u=0.24<0.3 → HYPOTHESIS |
| `distorted_market_signal` | **hypothesis** | (0.72, 0.00, 0.28) | in | b=0.72>0.5, u=0.28<0.3 → HYPOTHESIS |
| `long_term_value` | **provisional** | (0.66, 0.00, 0.34) | in | b=0.66>0.5 but u=0.34≥0.3 → PROVISIONAL |
| `not_value_creation` | **contested** | (0.35, 0.10, 0.55) | out | OUT → CONTESTED (attacked and defeated) |
| `organizational_growth` | **hypothesis** | (0.80, 0.00, 0.20) | in | b=0.80>0.5, u=0.20<0.3 → HYPOTHESIS |
| `positive_unit_economics` | **established** | (0.90, 0.00, 0.10) | in | b=0.90>0.8, u=0.10≤0.1 → ESTABLISHED |
| `resource_allocation_effective` | **hypothesis** | (0.81, 0.00, 0.19) | in | b=0.81>0.5, u=0.19<0.3 → HYPOTHESIS |
| `value_creation` | **hypothesis** | (0.85, 0.00, 0.15) | in | b=0.85>0.5, u=0.15<0.3 → HYPOTHESIS |

---

## Stage 5: Contestation Protocols

### 5a: Vāda (Cooperative Inquiry — Grounded Semantics)

**Semantics:** Grounded extension (polynomial, unique)
**Purpose:** What can we agree on? What's open?

**Extension size:** 8 arguments IN
**Open questions:** none
**Suggested evidence:** none

**Accepted conclusions:**

| Conclusion | Status | Belief | Arguments |
|-----------|--------|--------|-----------|
| `binding_constraint_identified` | hypothesis | 0.85 | ['A0001'] |
| `coordination_overhead` | hypothesis | 0.76 | ['A0005'] |
| `distorted_market_signal` | hypothesis | 0.72 | ['A0006'] |
| `long_term_value` | provisional | 0.66 | ['A0007'] |
| `not_value_creation` | contested | 0.35 | ['A0008'] |
| `organizational_growth` | hypothesis | 0.80 | ['A0002'] |
| `positive_unit_economics` | established | 0.90 | ['A0000'] |
| `resource_allocation_effective` | hypothesis | 0.81 | ['A0004'] |
| `value_creation` | hypothesis | 0.85 | ['A0003'] |

### 5b: Jalpa (Adversarial Disputation — Preferred Semantics)

**Semantics:** Preferred extensions (NP-hard offline, may find multiple)
**Purpose:** What positions are defensible under adversarial pressure?

**Preferred extensions found:** 1
**Defensible positions (IN preferred, OUT grounded):** []

**Counter-arguments identified:**
- `not_value_creation`: ['viruddha: value_creation (rebutting)']
- `value_creation`: ['viruddha: not_value_creation (rebutting)']

### 5c: Vitaṇḍā (Pure Critique — Stable Semantics)

**Semantics:** Stable extensions (coNP-hard offline)
**Purpose:** Where are the vulnerabilities? What can't be defended?

**Stable extensions found:** 2
**Undefended arguments:** []

**Vulnerability inventory:**
- `not_value_creation`: ['A0003→A0008 (rebutting)']
- `value_creation`: ['A0008→A0003 (rebutting)']

---

## Stage 6: Uncertainty Quantification (Three-Way Decomposition)

**Components:**
1. **Epistemic uncertainty** — from belief/uncertainty in the tag (reducible with more evidence)
2. **Aleatoric uncertainty** — from disbelief in the tag (inherent domain disagreement)
3. **Inference uncertainty** — from grounding confidence, decay, derivation depth

### `value_creation`

- **Total confidence (strength):** 0.7310
- **Epistemic:** status=hypothesis, belief=0.8550, uncertainty=0.1450
  - 'value_creation': moderate evidence — working hypothesis
- **Aleatoric:** disbelief=0.0000
  - 'value_creation': low domain-level contestation
- **Inference:** grounding=0.90, decay=1.00, depth=0
  - 'value_creation': grounding=0.90, freshness=1.00, chain_depth=0

### `long_term_value`

- **Total confidence (strength):** 0.4460
- **Epistemic:** status=provisional, belief=0.6559, uncertainty=0.3441
  - 'long_term_value': moderate evidence — working hypothesis
- **Aleatoric:** disbelief=0.0000
  - 'long_term_value': low domain-level contestation
- **Inference:** grounding=0.90, decay=1.00, depth=0
  - 'long_term_value': grounding=0.90, freshness=1.00, chain_depth=0

### `coordination_overhead`

- **Total confidence (strength):** 0.4845
- **Epistemic:** status=hypothesis, belief=0.7600, uncertainty=0.2400
  - 'coordination_overhead': moderate evidence — working hypothesis
- **Aleatoric:** disbelief=0.0000
  - 'coordination_overhead': low domain-level contestation
- **Inference:** grounding=0.90, decay=1.00, depth=0
  - 'coordination_overhead': grounding=0.90, freshness=1.00, chain_depth=0

### `distorted_market_signal`

- **Total confidence (strength):** 0.4603
- **Epistemic:** status=hypothesis, belief=0.7220, uncertainty=0.2780
  - 'distorted_market_signal': moderate evidence — working hypothesis
- **Aleatoric:** disbelief=0.0000
  - 'distorted_market_signal': low domain-level contestation
- **Inference:** grounding=0.90, decay=1.00, depth=0
  - 'distorted_market_signal': grounding=0.90, freshness=1.00, chain_depth=0

### `not_value_creation`

- **Total confidence (strength):** 0.1590
- **Epistemic:** status=contested, belief=0.3494, uncertainty=0.5548
  - 'not_value_creation': insufficient evidence
- **Aleatoric:** disbelief=0.0958
  - 'not_value_creation': low domain-level contestation
- **Inference:** grounding=0.90, decay=1.00, depth=0
  - 'not_value_creation': grounding=0.90, freshness=1.00, chain_depth=0

---

## Stage 7: Scenario Comparison — Effect of Scope Exclusions

| Conclusion | Baseline (growing startup) | Subsidized entity (undercuts V01) | Active structural intervention (undercuts V04, V11) | Regulated industry (undercuts V08) |
|-----------|-------|-------|-------|-------|
| `value_creation` | **in** | **out** | **in** | **in** |
| `resource_allocation_effective` | **in** | **in** | **in** | **in** |
| `long_term_value` | **in** | **in** | **in** | **out** |
| `coordination_overhead` | **in** | **in** | **out** | **in** |
| `distorted_market_signal` | **in** | **in** | **in** | **in** |
| `not_value_creation` | **out** | **in** | **out** | **out** |
| _Total args_ | 9 | 11 | 12 | 11 |
| _Total attacks_ | 2 | 3 | 4 | 3 |

**Key observations:**
- Subsidized entity undercuts V01 → value_creation goes OUT → V11's not_value_creation goes IN
- Active structural intervention undercuts V04 AND V11 → coordination_overhead and not_value_creation go OUT → value_creation stays IN cleanly
- Regulated industry undercuts V08 only → long_term_value goes OUT, but value_creation and its chain still hold

**Known limitation (sub-argument defeat propagation):**
In the "Subsidized entity" scenario, `long_term_value` remains IN even though its sub-argument
`value_creation` is OUT. This is because the current engine only checks **direct attacks** on an
argument — it does not propagate defeat through the sub-argument tree. In full ASPIC+ semantics,
an attack on a sub-argument should also count as an attack on the parent argument. This is
documented as item B1 in the critical analysis (`discussions/critical-analysis-v4-post-fix-round.md`).

---

## Stage 8: User Contestation Walk-Through

**Scenario:** User contests the `not_value_creation` conclusion with direct evidence

**Before contestation:**
- `not_value_creation` (A0008): label=out, strength=0.1590

**Contestation applied:**
- Type: viruddha (rebutting)
- New argument: A0009 (`value_creation_confirmed`)
- Evidence: belief=0.95, pramāṇa=PRATYAKSA, source=direct_observation_q4_financials

**After recomputing grounded extension:**
- `not_value_creation` (A0008): label=out
- `value_creation_confirmed` (A0009): label=in, strength=0.7600

**Total arguments now:** 10
**Total attacks now:** 4

---

## Summary: Pipeline Stage Map

```
YAML KB ─→ [Stage 0: Load KS] ─→ KnowledgeStore (11 vyāptis, 8 hetvābhāsas)
              │
Query Facts ──┘
              │
         [Stage 1: Premise Args] ─→ 3 premise arguments (PRATYAKSA, strict)
              │
         [Stage 2: Forward Chain] ─→ 6 rule arguments via fixpoint
              │                       ├─ V01: positive_unit_economics → value_creation
              │                       ├─ V02: binding_constraint → resource_allocation_effective
              │                       ├─ V04: organizational_growth → coordination_overhead
              │                       ├─ V05: coordination_overhead → distorted_market_signal
              │                       ├─ V08: value_creation + resource_alloc → long_term_value
              │                       └─ V11: growth + overhead → not_value_creation
              │
         [Stage 2b: Attack Derivation] ─→ 2 rebutting attacks
              │                            value_creation ⟺ not_value_creation
              │
         [Stage 3: Grounded Semantics] ─→ Labels: 8 IN, 1 OUT
              │                            value_creation=IN (stronger)
              │                            not_value_creation=OUT (defeated)
              │
         [Stage 4: Epistemic Status] ─→ Status per conclusion
              │                          ESTABLISHED, HYPOTHESIS, CONTESTED
              │
         [Stage 5: Contestation] ─→ Vāda (cooperative)
              │                     Jalpa (adversarial)
              │                     Vitaṇḍā (pure critique)
              │
         [Stage 6: UQ] ─→ Three-way decomposition per conclusion
              │             epistemic / aleatoric / inference
              │
         [Stage 7: Scenarios] ─→ Scope exclusions change outcomes
              │
         [Stage 8: User Contest] ─→ AF modified, recomputed
```