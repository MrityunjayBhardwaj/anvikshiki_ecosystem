# Ideal Architecture Properties: Design Criteria for Anvikshiki Engine

**Date:** 2026-03-06
**Context:** After critical audit of v4 implementation (35+ magic numbers, dead code, false claims), stepping back to define what the architecture SHOULD look like before choosing a framework.

---

## The Central Problem

**We hand-specify HOW confidence composes, instead of letting it emerge from structure.**

Everything else — the 35 magic numbers, the false semiring claim, the dead code, the Frankenstein layers — is a symptom of this one problem.

Currently:
- We **specify** how beliefs chain: `new_b = a.belief * b.belief` (tensor formula)
- We **specify** how beliefs combine: cumulative fusion + overlap interpolation (oplus formula)
- We **specify** how beliefs map to status: `if belief > 0.8 and uncertainty <= 0.1` (thresholds)
- We **specify** how defeat works: `attacker.tag.strength >= target.tag.strength` (comparison)
- We **specify** how metadata propagates: `min()` for tensor, `max()` for oplus (lattice rules)
- We **specify** how trust composes: `formulation * existence` (product)
- We **specify** how decay works: `exp(-0.693 * age / half_life)` (formula)

Each specification is independent. Each introduces parameters. Each must be justified separately. None derives from the others. When you fix one, you need new parameters for the fix. The debt grows linearly with feature count because there's no shared foundation to derive from.

### The Nyaya Framing

In Nyaya epistemology, epistemic status EMERGES from the dialectical process — from what pramanas support a claim, what hetvabhasas attack it, and what survives the debate. You don't compute a number and threshold it. You assess the argument structure.

Our engine does the opposite: it computes numbers through a chain of hand-specified formulas, then thresholds the result back into categories. A round trip through unnecessary complexity that loses the structural information Nyaya cares about.

---

## Properties of the Ideal Architecture

### P1: Single Governing Principle

Everything — acceptance, defeat, confidence, composition — should derive from **one mechanism**. Not a semiring + a lattice + thresholds + heuristic cascades. One thing.

**Why:** If there's one governing principle, adding a feature means extending that principle, not bolting on a new mechanism. The parameter count grows logarithmically, not linearly.

### P2: Structure from Theory, Magnitudes from Data

The **what** (argument types, attack types, preference ordering) comes from Nyaya theory. The **how much** (base scores, edge weights, decay rates) comes from optimization against data.

**Why:** Currently both structure AND magnitudes are hand-specified. 35 parameters exist because someone had to pick a number for each interaction type. If magnitudes are learned, the only design decisions are structural — and those are grounded in 2000 years of Nyaya epistemology.

**Current violation:** `BELIEF_MAP = {ESTABLISHED: (0.95, 0.0, 0.05), ...}` — structure (4 epistemic classes) is from theory, but magnitudes (0.95, 0.0, 0.05) are invented.

### P3: Composition Derives, Not Specified

When you chain inferences A→B→C, the confidence of C should **follow from the governing principle**, not from a hand-designed tensor formula. When you have independent evidence for the same conclusion, accumulation should follow from the same principle.

**Why:** This is the core Frankenstein problem. tensor and oplus are separate hand-specified operations with separate justifications (Josang 10.3 vs Josang 12.3). They don't share axioms. Changing one doesn't constrain the other. Any pair of operations could be swapped in with equal justification.

**What "derives" means concretely:** In an energy model, chain attenuation happens because each link adds attack surfaces — the energy landscape naturally penalizes long chains without a separate "tensor" operation. In a proper algebraic structure, composition would follow from the algebra's axioms.

### P4: Graded Acceptance is Native

The engine should produce continuous confidence as its primary output. Not binary IN/OUT that gets post-processed. Not continuous values that get thresholded into categories.

**Why:** The downstream LLM needs calibrated confidence ("How sure are you?"). Binary labels lose information. Thresholding re-discretizes what was already categorical, adding 7 parameters for no reason.

**Current violation:** Grounded semantics produces IN/OUT/UNDECIDED (binary). Then `epistemic_status()` thresholds continuous tag values to recover gradedness. Two steps that should be zero steps.

### P5: No Dead Paths

Every component should be consumed. Every computation should affect the output. No config modules that nothing reads. No analysis functions that always return the same value. No inference engines that the main path never invokes.

**Why:** Dead code is the symptom of a composite architecture where pieces were added to satisfy a checklist ("we need a config module") rather than because the governing principle demanded them.

### P6: Provenance is Structural, Not Numerical

Explaining WHY a conclusion is accepted means pointing to the argument tree: which vyaptis, which pramanas, which hetvabhasas. Not showing `trust_score=0.72, decay_factor=0.89, belief=0.68`.

**Why:** The user (the synthesis LLM) can't act on `0.72`. It CAN act on "supported by pratyaksa evidence from chapters 3 and 7, with one savyabhicara scope violation detected."

### P7: Debate Protocols = Same Mechanism, Different Parameters

Vada, jalpa, vitanda should be **one algorithm with different settings**, not three separate algorithms (grounded, preferred, stable) with different complexity classes.

**Why:** Currently, vada is polynomial and always works, jalpa is NP-hard and silently times out, vitanda is coNP-hard and silently times out. The user thinks they're getting three modes of analysis; they're often getting the same mode three times (grounded fallback).

### P8: Falsifiable Claims Only

The architecture should claim only what the implementation delivers. If it's a composite, say "composite." If there's no grammar-constrained decoding, don't list it as a layer.

---

## The Ideal Architecture in One Sentence

**A single governing equation over a bipolar argument graph, where structure comes from Nyaya theory, magnitudes are learned from data, and acceptance degrees emerge from equilibrium — not from hand-specified formulas.**

---

## Property Dependencies

The 8 properties are not independent:

```
P1 (single principle)
├── implies P3 (composition derives from the principle)
├── implies P5 (no dead paths — everything connects to the principle)
└── implies P7 (debate modes = parameter variation of the principle)

P2 (theory + data)
├── implies P7 (debate = parameter variation)
└── implies fewer magic numbers

P4 (graded native)
└── eliminates threshold parameters that violate P5

P8 (falsifiable claims)
└── eliminates false documentation that masks violations of P1-P7
```

They're all facets of the same design: **stop specifying behavior, start letting it emerge from structure.**

---

## Scorecard: Candidate Architectures

### Current: ASPIC+ over Provenance Semirings

| Property | Score | Reason |
|---|---|---|
| P1: Single principle | FAIL | 9 independent mechanisms |
| P2: Theory + data | FAIL | Both structure and magnitudes hand-specified |
| P3: Composition derives | FAIL | tensor and oplus are independently specified |
| P4: Graded native | PARTIAL | Continuous values exist but get thresholded |
| P5: No dead paths | FAIL | config.py, _check_contested(), DatalogEngine unused |
| P6: Structural provenance | PARTIAL | Argument tree exists but drowned in numerical metadata |
| P7: Debate = parameter variation | FAIL | Three separate algorithms, two silently timeout |
| P8: Falsifiable claims | FAIL | "semiring" (not one), "five-layer" (four at best) |

### Proposed Path B: ASPIC+ Categorical + Post-hoc UQ

| Property | Score | Reason |
|---|---|---|
| P1: Single principle | PARTIAL | ASPIC+ is one principle, UQ layer is separate |
| P2: Theory + data | PARTIAL | Structure from Nyaya, ~5 fixed parameters |
| P3: Composition derives | PASS | Defeat from ASPIC+ weakest-link, no separate ops |
| P4: Graded native | FAIL | Binary IN/OUT, gradedness only in post-hoc layer |
| P5: No dead paths | PASS | Clean architecture, no dead code |
| P6: Structural provenance | PASS | Provenance IS the argument tree |
| P7: Debate = parameter variation | FAIL | Still three separate algorithms |
| P8: Falsifiable claims | PASS | Honest about what it is |

### Proposed Path C: Energy-Based (DBN-Inspired QBAF)

| Property | Score | Reason |
|---|---|---|
| P1: Single principle | PASS | One energy function E(sigma) |
| P2: Theory + data | PASS | Structure from Nyaya, ~14 magnitudes learned via DSPy |
| P3: Composition derives | PASS | Chain attenuation and accumulation emerge from energy landscape |
| P4: Graded native | PASS | sigma(a) in [0,1] is the primary output |
| P5: No dead paths | PASS | Everything connects to the energy function |
| P6: Structural provenance | PASS | Argument graph is the explanation |
| P7: Debate = parameter variation | PARTIAL | Temperature analogy plausible but unproven |
| P8: Falsifiable claims | PASS (if honest about P7 gap) | Novel but documented as such |

---

## Decision Framework

- If this is an **engineering project** (ship something that works): Path B
- If this is a **research project** (publish something novel): Path C
- If this is **neither** (just clean up): Path A (honest composite, documented debt)

The energy-based path (C) is the only one that satisfies P1-P6 fully. Its gap is P7 (debate protocols as temperature variation needs formal proof). But it's also the most work and the most novel.

---

## References

- Potyka (2018). "Continuous dynamical systems for weighted bipolar argumentation." AAAI.
- Baroni, Rago, Toni (2019). "From fine-grained properties to broad principles for gradual argumentation." IJAR.
- Amgoud, Ben-Naim (2016). "Axiomatic foundations of acceptability semantics." KR.
- Rago et al. (2016). "Discontinuity-free decision support with quantitative argumentation debates." KR.
- Bench-Capon (2003). "Value-based argumentation frameworks." Artificial Intelligence.
- Modgil, Prakken (2013). "A general account of argumentation with preferences." Artificial Intelligence.
- Tran, Garcez (2023). "Logical Boltzmann Machines." AAAI.
- Oren, Norman, Preece (2007). "Subjective logic and arguing with evidence." AIJ.
