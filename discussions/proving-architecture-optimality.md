# Proving Architecture Optimality: Are P1-P8 the Best Properties?

**Date:** 2026-03-06
**Context:** After defining 8 ideal architecture properties (P1-P8) and surveying 15+ existing argumentation engines, the question: are these the right properties, and can we prove the Ānvīkṣikī direction is optimal?

---

## 1. The Landscape Survey Result

**No existing system satisfies all P1-P8 with provenance + calibrated UQ + model agnosticism.**

### The Trifecta Nobody Has Solved

| System | Proof Trace | Calibrated UQ | Model-Agnostic | Grounded Theory |
|--------|:-----------:|:-------------:|:--------------:|:---------------:|
| **Scallop/Lobster** (UPenn, PLDI 2023 / ASPLOS 2026) | Provenance semirings | Probabilistic, not calibrated | Yes | Yes (Green et al. 2007) |
| **Potyka QEM** (King's College) | Influence attribution only | None | Yes | Yes (contraction mapping) |
| **ArgRAG** (Imperial, PMLR 2025) | QBAF structure | None (LLM point estimates) | Yes (tested GPT-3.5/4o) | Yes |
| **ARGORA** (Jan 2026) | Causal argument traces | Strengths, not calibrated | Yes (multi-agent) | Partial |
| **Carneades** (Gordon) | Full argument graphs | Weights, not calibrated | N/A (Go engine) | Yes |
| **Conformal Coherent Factuality** (IBM, ICLR 2025) | Deducibility graphs | Yes (coverage guarantees) | Yes | Yes |
| **Semantic Entropy** (Nature 2024) | None | Yes (calibrated) | Yes | Yes |
| **DeepProbLog** (KU Leuven) | Full proof trees + probs | Exact, not calibrated | No (IS the engine) | Yes |
| **s(CASP)** | Full justification trees | None | N/A (Prolog) | Yes |

**The gap is architectural, not mathematical.** All the mathematical pieces exist in published, peer-reviewed work. Nobody has assembled them.

### System-Level Assessment

**Best existing systems by property:**

| Property | Best Existing System | Assessment |
|----------|---------------------|------------|
| P1: Single principle | Potyka QEM (energy minimization) | Strong |
| P2: Learnable params | DeepProbLog (end-to-end differentiable) | Works but not argumentation-native |
| P3: Composition from principle | DeLP, ABA (derivation from rules) | Strong for symbolic; QEM for numerical |
| P4: Graded/continuous | Potyka QEM, Hunter epistemic | QEM is cleanest |
| P5: No dead paths | QEM, DeLP, ABA | Several achieve this |
| P6: Structural provenance | s(CASP) (justification trees), DeLP, ASPIC+ | s(CASP) is strongest |
| P7: Multiple reasoning modes | Carneades (proof standards as modes) | Elegant design |
| P8: Falsifiable claims | Most symbolic systems | Not a differentiator |

**Carneades** is the closest overall (6/8 partially or fully), failing mainly on P2 (learnable parameters) and rigorous UQ. But it's Go-only, small community, no learning.

---

## 2. Is Nyāya the Right Organizing Principle?

### Honest Assessment: ~85% Isomorphic to ASPIC+ with Preferences

| Nyāya Contribution | ASPIC+ Equivalent | Genuine Addition? |
|---|---|---|
| Pramāṇa hierarchy (4 evidence types) | Parametric preference ordering | **Design clarity** — gives specific, philosophically grounded preference theory that ASPIC+ leaves open |
| Bādhita (cross-channel override) | Regular preference defeat | **Explanation value** — names WHY a defeat happened |
| Satpratipakṣa (counter-balanced) | UNDECIDED label | **Detection value** — flags genuine contests as first-class pathologies |
| Pre-inferential validation | Not present in ASPIC+ | **Architecturally novel** — type-check evidence channel BEFORE running inference |
| Vyāpti with scope conditions | Defeasible rule + metadata | Same formal structure, better defaults |
| Hetvābhāsa (5 fallacy types) | 3 attack types (undermining/undercutting/rebutting) | 2 novel categories (bādhita, satpratipakṣa); 3 map 1:1 |
| Vāda/Jalpa/Vitaṇḍā | Grounded/Preferred/Stable semantics | Useful heuristic for mode selection, not formal correspondence |

### What Nyāya Genuinely Adds

1. **A substantive preference theory** (pramāṇa hierarchy) where ASPIC+ says "bring your own"
2. **Named pathological cases** that improve explanation generation
3. **Pre-inferential validation** as a design principle (check applicability before reasoning)
4. **Design vocabulary** — constrains decisions, provides defaults, motivates specific architectural choices

### What Nyāya Does NOT Add

- No new formal expressiveness (everything compiles to ASPIC+ with preferences)
- No new computational structures (same complexity classes)
- No representation-theoretic novelty

**Verdict:** The value is in *epistemological design philosophy* that shapes good implementation choices, not in *mathematical structures* which are equivalent. Worth keeping as organizing vocabulary. Don't claim formal novelty from Nyāya — claim it from the *integration* of QEM + provenance semirings + conformal prediction.

---

## 3. What P1-P8 Are Missing

### Properties Not Covered by P1-P8

| Missing Property | Why It Matters | Source |
|---|---|---|
| **Convergence guarantee** | Energy minimization must converge to unique fixpoint | Potyka 2018 |
| **Computational complexity bound** | Grounded = P, preferred = NP-complete | Dvořák & Dunne 2018 |
| **Calibration guarantee** | UQ must have coverage guarantees | Vovk et al. 2005 |
| **Robustness to adversarial input** | LLM can inject malformed predicates | Practical concern |
| **Decidability** | Must terminate on all inputs | Rice 1953 / Datalog guarantees |
| **Rationality postulates** | Closure, consistency | Caminada & Amgoud 2007 |
| **Scalability** | Provenance tracking for recursive Datalog is NP-complete | Bourgaux et al. 2024 |

**P1-P8 are design criteria (what the architecture should look like), not formal properties (what the system must mathematically guarantee).** They mix levels of analysis.

---

## 4. The Three-Level Property Framework

### Level 1: FORMAL GUARANTEES (provable, non-negotiable)

| ID | Property | Formal Statement | Reference |
|---|---|---|---|
| F1 | Decidability | Every query terminates | Datalog data complexity ∈ PTIME (Vardi 1982) |
| F2 | Polynomial data complexity | Grounded semantics computable in O(\|args\| × \|attacks\|) | Dvořák & Dunne 2018 |
| F3 | Soundness | Accepted arguments are conflict-free | Dung 1995, Def. 6 |
| F4 | Convergence | Fixpoint computation reaches unique solution | QEM: contraction mapping (Potyka 2018); Datalog: Khamis et al. 2022 |
| F5 | Calibration coverage | P(Y ∈ C(X)) ≥ 1-α | Conformal prediction (Vovk et al. 2005) |
| F6 | Rationality postulates | Closure + direct/indirect consistency | Caminada & Amgoud 2007, Thms 3-5 |

### Level 2: ARCHITECTURAL PRINCIPLES (design criteria)

| ID | Property | What It Demands |
|---|---|---|
| P1 | Single governing principle | One mechanism, not bolted-together heuristics |
| P2 | Structure from theory, magnitudes from data | Theory → what; optimization → how much |
| P3 | Composition derives from principle | No hand-specified tensor/oplus |
| P4 | Graded acceptance native | Continuous [0,1] output, not binary thresholded |
| P5 | No dead paths | Every component consumed |
| P6 | Structural provenance | Trace to source via argument tree |
| P7 | Debate modes as parameter variation | One algorithm, different settings |
| P8 | Falsifiable claims only | Claim only what implementation delivers |

### Level 3: IMPOSSIBILITY CONSTRAINTS (proven tradeoffs)

| ID | Constraint | Formal Statement | Reference |
|---|---|---|---|
| I1 | Grounded minimality | Many arguments stay UNDECIDED; no semantics satisfies all desirable principles | Baroni & Giacomin 2007 |
| I2 | CP vs QP incompatible | Cannot respect both cardinality and quality of attackers simultaneously | Bonzon et al. 2016 (AAAI) |
| I3 | Gradual semantics pairwise incompatible | Hbs, Mbs, Cbs, EMbs, TB, IS produce conflicting rankings — must pick ONE | Amgoud & Beuselinck 2021 (KR), Theorem 3 |
| I4 | Marginal, not conditional coverage | Conformal prediction guarantees marginal P(Y∈C(X)) ≥ 1-α, NOT conditional P(Y∈C(X)\|X=x) | Vovk et al. 2005 |
| I5 | Why-provenance is NP-complete | For linear recursive Datalog, computing minimal witness is NP-complete | Bourgaux, Munoz & Thomazo 2024 |
| I6 | Differentiability vs soundness vs tautology-preservation | No differentiable relaxation of Boolean logic satisfies all three | Giannini et al. 2023 |
| I7 | Arrow-style aggregation impossibility | No aggregation of multiple agent labellings satisfies all fairness axioms | Caminada & Pigozzi 2011 |
| I8 | Calibration failure is topologically typical | The set of sequences on which any forecaster is calibrated is meager (first-category) | Dawid 1982 / Belot 2013 |

---

## 5. Four Ways to "Prove" the Architecture is Optimal

### Method 1: Elimination (Minimality Proof)

**Strategy:** Show no subset of components achieves all 7 desiderata.

Already done in thesis2_v1.md Section 7.5:
- Pure LLM: fails 1, 2, 3, 4, 5, 7
- LLM + Boolean Datalog: fails 2, 3, 4, 6, 7
- LLM + Lattice Datalog: needs bolt-ons for 2, 4, 6, 7 → Frankenstein
- LLM + ASPIC+ (no semiring): fails 4, 5, 7
- LLM + Provenance Datalog (no argumentation): fails 2, 3, 6
- LLM + ASPIC+ over Provenance Semirings: achieves all 7

**This proves NECESSITY, not optimality among complete architectures.**

### Method 2: Axiomatic Characterization

**Strategy:** Show the architecture uniquely satisfies a maximal consistent subset of established axioms.

Using Amgoud & Ben-Naim (2016, 2018) axioms for gradual semantics:
- Anonymity, Independence, Directionality, Monotonicity, Balance, Proportionality
- Counting (CP), Quality Precedence (QP) — these two are incompatible (Bonzon et al. 2016)

**Proof sketch:**
1. Choose QP over CP (quality-based evaluation matches Nyāya pramāṇa hierarchy — evidence quality matters more than count)
2. Show QEM satisfies QP + Balance + Monotonicity + Directionality (Potyka 2018 proves 12/13 Amgoud-BN properties)
3. Show that any alternative satisfying CP instead of QP loses the pramāṇa hierarchy mapping
4. Conclude: the architecture satisfies the maximal consistent subset of axioms compatible with Nyāya-grounded reasoning

### Method 3: Formal Subsumption

**Strategy:** Show the architecture can express everything alternatives can, plus more.

| Alternative | Can our architecture express it? | Can it express ours? |
|---|---|---|
| ArgLLMs (QBAF + DF-QuAD) | Yes — QBAF is a special case of ASPIC+ with no rules | No — no provenance, no typed defeat |
| DeLP | Yes — DeLP arguments are a subset of ASPIC+ | No — no quantitative tags |
| Carneades proof standards | Yes — proof standards map to tag thresholds | Partially — no semiring composition |
| Potyka QEM alone | Yes — QEM is the gradual evaluation layer | No — no structured provenance |
| Plain ASPIC+ (no semiring) | Yes — set semiring to Boolean | No — no quantitative reasoning |
| Scallop (provenance Datalog) | Yes — Datalog is the evaluation substrate | No — no defeat, no argumentation |
| Hunter epistemic graphs | Yes — probability intervals subsumable by SL opinions | No — no argument structure |

**If formalized: each alternative is a homomorphic image of the full architecture under some projection. This is a representation theorem.**

### Method 4: Empirical Benchmarking

**Strategy:** Demonstrate superior performance on standard benchmarks.

| Benchmark | What It Tests | Metric |
|---|---|---|
| PubHealth | Fact verification with provenance | Accuracy + trace quality |
| ProofWriter | Logical rule chaining | Proof accuracy |
| FEVER | Claim-to-source tracing | Provenance F1 |
| Calibration suite | Are confidence scores meaningful? | Expected Calibration Error (ECE) |
| Contestability | Does modifying an argument have predicted effect? | Monotonicity + faithfulness |
| Custom domain KB | Full pipeline end-to-end | Quality vs. ArgLLM/RAG baseline |

---

## 6. What You Can and Cannot Prove

### What You CAN Prove

1. **Minimality** — no subset of components achieves all desiderata (Section 7.5 of thesis already does this)
2. **Subsumption** — the architecture can express every alternative as a special case (representation theorem)
3. **Maximal axiom satisfaction** — among architectures satisfying F1-F6, yours satisfies the largest consistent subset of Amgoud-Ben Naim axioms
4. **Impossibility-awareness** — respects I1-I8 by design:
   - I1: Accept UNDECIDED labels, don't force resolution
   - I2: Choose QP (quality) over CP (counting), document the choice
   - I3: Pick one gradual semantics (QEM), don't mix
   - I4: Use coverage groups for approximate conditional coverage
   - I5: Lazy/on-demand provenance via SAT solver
   - I6: Keep Datalog symbolic, differentiate only neural components
   - I7: Single semantics across all agents
   - I8: Adaptive recalibration, not fixed curves

### What You CANNOT Prove

- That P1-P8 are the "right" design criteria — they are value judgments, not theorems
- That energy-based > extension-based for every use case — this is empirical
- That Nyāya gives formal advantages over ASPIC+ with custom preferences — it doesn't (design vocabulary, not new math)
- That the specific semiring is optimal among all semirings — requires universality theorem (Green et al. 2007) + proof that your semiring is the right homomorphic image

---

## 7. The Strongest Defensible Claim

> The Ānvīkṣikī architecture is the **minimal complete** neurosymbolic reasoning system for epistemically qualified domain inference with native contestability, provenance, and calibrated UQ. It satisfies formal guarantees F1-F6, respects impossibility constraints I1-I8, and subsumes all existing alternatives (ArgLLMs, DeLP, Carneades, plain ASPIC+, provenance Datalog) as special cases. The design criteria P1-P8 are grounded in 2000 years of Nyāya epistemological tradition and 30 years of computational argumentation theory. Whether this is "best" depends on objectives — for the specific objectives (infer, constrain, qualify, decompose uncertainty, ground to sources, respect scope, decay gracefully, contest), no simpler architecture suffices.

---

## 8. Architectural Recommendations from Impossibility Results

| Impossibility | Impact | Mitigation |
|---|---|---|
| Grounded is minimal (I1) | Many vyaptis stay UNDECIDED | Accept this; preferred costs NP |
| CP vs QP (I2) | Can't respect both count and quality | Choose QP (matches pramāṇa hierarchy); document |
| Gradual semantics incompatible (I3) | Must pick ONE | QEM; don't mix semantics |
| Conformal marginal only (I4) | Per-vyapti coverage varies | Coverage groups by topic |
| Why-provenance NP-complete (I5) | Can't eagerly compute all traces | Lazy/on-demand via SAT solver |
| Differentiable vs sound vs tautology (I6) | Can't have all three in one layer | Separate: symbolic Datalog (sound) + neural grounding (differentiable) + conformal (calibrated) |
| Arrow-style aggregation (I7) | Multi-agent labellings can't be fairly aggregated | Single semantics across all agents |
| Calibration topologically fragile (I8) | Fixed calibration procedures can be adversarially defeated | Adaptive recalibration |

---

## References

### Argumentation Theory
- Dung (1995). "On the acceptability of arguments and its fundamental role in nonmonotonic reasoning." AIJ.
- Amgoud & Ben-Naim (2016, 2018). "Axiomatic foundations of acceptability semantics." KR.
- Baroni & Giacomin (2007). "On principle-based evaluation of extension-based argumentation semantics." AIJ.
- Baroni, Rago, Toni (2019). "From fine-grained properties to broad principles for gradual argumentation." IJAR.
- Bonzon, Delobelle, Konieczny & Maudet (2016). "A Comparative Study of Ranking-based Semantics." AAAI.
- Amgoud & Beuselinck (2021). "Equivalence of Semantics in Argumentation." KR.
- Caminada & Amgoud (2007). "On the evaluation of argumentation formalisms." AIJ.
- Caminada & Pigozzi (2011). "On judgment aggregation in abstract argumentation." AAMAS.
- Dvořák & Dunne (2018). "Computational problems in formal argumentation." Handbook of Formal Argumentation.
- Modgil & Prakken (2013, 2018). "A general account of argumentation with preferences." AIJ.
- Potyka (2018). "Continuous dynamical systems for weighted bipolar argumentation." AAAI.
- Rago et al. (2016). "Discontinuity-free decision support with quantitative argumentation debates." KR.

### Provenance & Datalog
- Green, Karvounarakis & Tannen (2007). "Provenance Semirings." PODS.
- Khamis et al. (2022). "Convergence of Datalog over semirings." PODS.
- Bourgaux, Munoz & Thomazo (2024). "The Complexity of Why-Provenance for Datalog Queries." ACM SIGMOD.
- Li et al. (2023). "Scallop: A Language for Neurosymbolic Programming." PLDI.

### UQ & Calibration
- Vovk, Gammerman & Shafer (2005). Algorithmic Learning in a Random World. Springer.
- Gneiting, Balabdaoui & Raftery (2007). "Probabilistic forecasts, calibration and sharpness." JRSS-B.
- Dawid (1982). "The Well-Calibrated Bayesian." JASA.
- Belot (2013). "Failure of Calibration is Typical." Statistics & Probability Letters.
- Margossian et al. (2024). "Variational Inference for Uncertainty Quantification." JMLR.

### Knowledge Representation
- Levesque & Brachman (1987). "Expressiveness and tractability in knowledge representation." Computational Intelligence.
- Rice (1953). "Classes of Recursively Enumerable Sets." Trans. AMS.

### Neurosymbolic
- Giannini et al. (2023). "T-norms driven loss functions for machine learning." Applied Intelligence.

### Existing Systems
- Freedman, Toni et al. (2025). "ArgLLMs." AAAI.
- Zhu et al. (2025). "ArgRAG." PMLR.
- ARGORA (2026). arXiv:2601.21533.
- Gordon. Carneades 4. github.com/carneades/carneades-4.
- Kuhn, Gal et al. (2024). "Semantic Entropy." Nature.
- IBM (2025). "Conformal Language Model Reasoning with Coherent Factuality." ICLR.

### Nyāya
- Ganeri (2003). "Ancient Indian Logic as a Theory of Case-Based Reasoning."
- Matilal (1998). The Character of Logic in India.
- Guhe (2022). An Indian Theory of Defeasible Reasoning.
- Oetke (1996). "Ancient Indian Logic as a Theory of Non-Monotonic Reasoning."
