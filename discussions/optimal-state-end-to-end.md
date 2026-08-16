# The optimal state of the Ānvīkṣikī engine, end to end

**Date:** 2026-08-17
**Subject:** `anvikshiki_ecosystem` at `ccd4b08`
**Status of this document:** design target + proofs. Not a description of the current system.

---

## 0. How to read the claims in this document

"With proof" is a strong word and most architecture documents abuse it. Every claim below carries one of four labels, and the label is load-bearing:

| Label | Means |
|---|---|
| **[PROVEN]** | A mathematical proof is given here, or a cited theorem applies directly |
| **[OBSERVED]** | I ran it against this tree; the command and output are shown |
| **[DESIGN]** | A deliberate choice. Justified, but a choice — another system could choose otherwise |
| **[OPEN]** | Not established. Stated so it cannot be mistaken for settled |

Anything not labelled is exposition. If a claim you care about carries **[DESIGN]** or **[OPEN]**, do not cite it as proven — that is the failure mode this whole document exists to prevent.

---

## 1. The target in one sentence

**A system whose epistemic outputs are computed from argument structure rather than judged by a model, whose every quantitative claim is either derived from a discrete algebra with a propagation guarantee or carries a distribution-free coverage guarantee, and whose one unverified input — extraction — is measured by an instrument that has itself been validated against human judgment.**

Three clauses, three sections of proof. The third clause is the one currently missing, and it is upstream of the other two.

---

## 2. What is already settled — do not re-litigate

This tree has accumulated real decisions. Reopening them is waste. For the record:

- **The architecture is ASPIC+ over annotated arguments, not Heyting-lattice Datalog.** The v4 pivot happened. Sheaf consistency, `H¹ ≠ 0`, and BetaProbLog comparisons describe a system that no longer exists.
- **Nyāya adds design vocabulary, not formal power.** ~85% isomorphic to ASPIC+ with preferences (`proving-architecture-optimality.md` §2). Claim novelty from the *integration*, never from the Sanskrit.
- **Accrual double-counting is fixed.** `oplus` consults source overlap. **[OBSERVED]** — a tag accrued against itself four times holds at `b=0.9000`, invariant.
- **Jøsang discounting replaced the renormalised tensor.** `b+d+u=1` is preserved exactly, not by division. Associativity is no longer broken by normalisation.
- **The "semiring" claim was retracted in the code itself.** The docstring now says plainly it is a commutative monoid pair, because distributivity fails for Subjective Logic.
- **The decision to go discrete was taken on 2026-08-16.** The continuous opinion arithmetic is scheduled for removal, not repair.

Section 4 proves *why* that last decision is correct rather than merely decided.

---

## 3. The pipeline in its optimal state

Thirteen stages. For each: what it does, what changes from today, and what guarantee it carries.

### S0 — Knowledge authoring

**Optimal:** A vyāpti carries a discrete `epistemic_status` from the lattice **L**, plus structural metadata (`causal_status`, scope conditions/exclusions, sources, decay). No hand-authored belief triples anywhere.

**Changes:** `DEFAULT_BELIEF_MAP` — the table mapping four KB statuses to invented `(0.95, 0.0, 0.05)` triples — is deleted. It is the largest single source of unjustified magnitudes in the system and it exists only to feed arithmetic that is itself being removed.

**Lattice L, totally ordered:**

```
BOTTOM  <  CONTESTED  <  OPEN  <  PROVISIONAL  <  HYPOTHESIS  <  ESTABLISHED
```

`PROVISIONAL` is the addition, and it is not cosmetic — see Theorem 4. It comes from thesis_v3 §12.4, and it is currently **absent from the KB-level enum**:

```
KB-level (schema.py)   : ESTABLISHED, WORKING_HYPOTHESIS, GENUINELY_OPEN, ACTIVELY_CONTESTED
PROVISIONAL present    : False                                                    [OBSERVED]
```

### S1 — Extraction (T2b), and its measurement

**Optimal:** Extraction remains as-is structurally — Stages A–E over guide prose. What changes is that it is **measured**, by an instrument that has been validated.

This is the load-bearing stage. Everything downstream consumes what it produces, so an unmeasured extractor makes every downstream number a measurement of extraction noise. The full audit is in `extraction-harness-audit.md`; the two facts that matter here:

- The matcher scores a predicate and its exact negation as a match. **[OBSERVED]** — an extractor emitting the inverse of every gold predicate scores precision 1.000, recall 1.000.
- The gold fixture is referenced by **0 of 51** Python files, while its own header claims otherwise. **[OBSERVED]**

**Optimal instrument:**

1. Match on the `description` field (natural language), not the `name` field (snake_case). Both sides already carry descriptions; `evaluate()` computes `[c.name for c in candidates]` and discards them. **[OBSERVED]**
2. Similarity via a negation-aware encoder (`tum-nlp/NegMPNet` or equivalent). **[DESIGN]** — no training required; the model is pretrained and CC-BY-SA-4.0.
3. A **hard polarity veto** above the similarity score, because negation-aware encoders *reduce* but do not *zero* negated-pair similarity. The veto makes the guarantee absolute rather than statistical.
4. Argument-order check for relational predicates only. **[OBSERVED]** — 4 of 14 gold predicates contain a relational token; the CaRB slot-matching principle applies to those and only those.
5. Gold produced by a human reading the **source**, never by the extractor or by a reviewer looking only at extractor output.

**Guarantee:** none, inherently — this is an empirical measurement, and its trustworthiness rests on the instrument validation in §6, not on a theorem.

### S2 — Grounding

**Optimal:** Unchanged in structure — ontology-constrained prompt, N-way ensemble, round-trip verification, solver feedback. Honest about layer count.

**Changes:** the docstring claims five layers; Layer 2 (grammar-constrained decoding) is "applied at serving level — transparent," which means it is not implemented here. Call it four. **P8 violation, trivially fixable.**

`confidence` from ensemble agreement stays — it is a legitimate frequency (fraction of ensemble members agreeing), not an invented magnitude. It feeds the conformal feature vector (S7), not a belief triple.

### S3 — Coverage routing

**Optimal:** Unchanged. This is the best-engineered component in the system: deterministic, zero LLM calls, three named match layers, an explicit DECLINE. It is the honest-refusal behaviour that distinguishes this engine from a RAG pipeline.

**One change:** its Jaccard matcher (`_find_closest_predicate`) has the same negation blindness as the eval matcher. `positive_unit_economics` and `negative_unit_economics` score 0.5 against a 0.4 threshold — **coverage would report a match on a predicate's own negation.** Same fix as S1, same 40 lines, and it matters more here because this one runs in production.

### S4 — Compilation (T2)

**Optimal:** Unchanged in structure. Forward-chain to fixpoint, derive rebutting / undercutting / undermining attacks. Cap combinations per rule.

**Changes:** arguments carry a **status** from L and a **pramāṇa** from the ordered enum, not a `(b,d,u)` triple. `_build_rule_tag`'s belief lookup disappears with `DEFAULT_BELIEF_MAP`.

Decay stays as metadata and continues to trigger undermining attacks below threshold — that is a *structural* consequence (an attack in the graph), not a numerical one, and it survives the subtraction intact.

### S5 — Labelling

**Optimal:** Unchanged. Grounded semantics, iterative propagation to fixpoint. Preferred and stable remain available for offline analysis behind explicit timeouts.

This is the part of the system that already works the way the whole system should.

### S6 — Status derivation ← **the central change**

**Optimal:** Status is a function of the labelling and the discrete lattice. No thresholds, no floats.

```
status(c) =
    ⊥                                        if no argument concludes c
    CONTESTED                                if every argument for c is OUT
    OPEN                                     if some argument for c is UNDECIDED and none is IN
    ⋁ { σ(a) : a ∈ args(c), label(a) = IN }  otherwise

σ(a) = ⋀ ( status(top_rule(a)), { σ(s) : s ∈ sub_args(a) } )
```

Where **⋀ = meet = min** over L (chaining: weakest link) and **⋁ = join = max** over L (accrual: best supporting argument).

Pramāṇa remains a **separate** ordered lattice on the same discipline — min along a chain, max across accrual — and continues to drive defeat preference in `_defeats`. It is already correct today and is untouched by the subtraction.

**What is deleted:** `ProvenanceTag.belief/disbelief/uncertainty`, `tensor`'s opinion arithmetic, `oplus`'s cumulative fusion, the `b+d+u=1` invariant and its 0.05 tolerance, `strength`, and the four numeric cutoffs in `epistemic_status()`. The code's own comment already flags these as *"hand-tuned thresholds with no calibration guarantee."*

**Coupling check, from the improvement plan and confirmed here:** `PramanaType`, `Label`, `RuleType` reference no float. `Attack` is four string fields. **Exactly one function bridges the discrete and continuous halves — `epistemic_status()` — and it is the one whose output is wrong.** The subtraction is clean.

### S7 — Calibration

**Optimal:** A conformal predictor over L, producing **prediction sets** with a distribution-free coverage guarantee.

This is what makes the discrete design lose nothing. The objection to going discrete is that you give up graded output (P4). You do not — you replace an uncalibrated point estimate with a *calibrated set*:

> At α=0.1: "this conclusion is {ESTABLISHED, HYPOTHESIS}, coverage ≥ 90%"
> When genuinely uncertain: "{ESTABLISHED, HYPOTHESIS, PROVISIONAL}" — and `|C(x)|` is itself the calibrated uncertainty measure.

Design already exists in `towards-categorical-uq-with-conformal-predictions.md`. Practical minimum ~200 calibration examples for 5 classes.

**The dependency nobody has written down:** conformal calibration needs labelled data. Labelled data needs a validated labelling apparatus. **The apparatus is the thing today's audit found broken.** So:

```
S1 instrument validation  →  gold labels  →  conformal calibration  →  calibrated status
```

Calibration cannot proceed before extraction measurement. That ordering is forced, not preferential. **[OPEN]** until the classifier is trained and its empirical coverage measured on this domain.

### S8 — Retrieval (T3a)

**Optimal:** Unchanged. Embedding retrieval with section boosting cross-linked from activated vyāptis, keyword fallback when embeddings are unavailable. Zero LLM calls.

One honesty note: the fallback is silent. A retriever that degrades to keyword overlap should say so in the trace, or a degraded run is indistinguishable from a healthy one — the same class of defect as `dag_validity` returning 1.0 for a validation that never ran.

### S9 — Synthesis

**Optimal:** Consumes statuses and prediction sets, not floats. The reward function's six weights are either derived, learned, or reported separately — not asserted to sum to 1.0 as though that were justification.

The synthesizer should render `{ESTABLISHED, HYPOTHESIS} @ 90%` rather than `belief=0.68`. A downstream LLM cannot act on `0.68`; it can act on a set and a coverage level. **This is P6 — provenance is structural, not numerical.**

### S10 — Serialization / API

**Optimal:** The engine returns what the contract promises.

Today it does not, and this is a live break, not a design aspiration:

```
_prediction_to_dict requests : response, sources, uncertainty, provenance, violations,
                               grounding_confidence, extension_size, coverage,
                               augmentation, contestation, arguments, attacks, labels
forward_with_coverage returns: augmentation, contestation, coverage, extension_size,
                               grounding_confidence, provenance, response, sources,
                               uncertainty, violations                        [OBSERVED]
```

`arguments`, `attacks`, `labels` are never returned → serialize to `null` → the frontend's Zod schema requires them → `EngineResultSchema.parse` throws → `api.ts` swallows it in `catch { /* ignore parse errors */ }`. **The stages animate and the result never arrives.**

Two further mismatches sit behind it: the compiler emits `"rebutting"` where the frontend enum says `"rebuttal"`, and `UncertaintyEntrySchema.aleatoric` expects a number where `compute_uncertainty_v4` returns `{disbelief, explanation}`.

**Optimal:** one shared schema, generated from one source, with a contract test asserting `returned_fields ⊇ schema_fields`. Three mismatches of this kind in one interface is not bad luck; it is the absence of a contract test.

### S11 — UI

**Optimal:** Unchanged in shape — the provenance chain graph is the right primary view, because it renders the argument tree, which *is* the explanation. It needs S10 fixed to receive data at all.

### S12 — Contestation

**Optimal:** Vāda online (grounded, polynomial). Jalpa and vitaṇḍā offline only, with **explicit reporting when a timeout causes a fallback to grounded** — otherwise the user believes they received three modes of analysis and received the same mode three times. P7 is not achievable (three different complexity classes cannot be one algorithm with a parameter), so the honest move is to stop claiming it.

---

## 4. The proofs

### Notation

L is the totally ordered lattice of §S0 with ⋀ = min and ⋁ = max. A *restatement* of evidence `t` is its composition with itself under the chaining operator.

---

### Theorem 1 — The current design violates restatement monotonicity

**Desideratum (R).** Restating the same evidence must not lower a conclusion's status. Nothing is learned, contradicted, or added by repetition; therefore nothing should degrade.

**Claim.** The current implementation violates (R).

**Proof — by counterexample, executed against this tree. [OBSERVED] [PROVEN]**

Take `t = (b=0.9, d=0.0, u=0.1)` and chain it against itself:

```
n=1  b=0.9000  u=0.1000  depth=0  status=established
n=2  b=0.8100  u=0.1900  depth=0  status=hypothesis
n=3  b=0.7290  u=0.2710  depth=0  status=hypothesis
n=4  b=0.6561  u=0.3439  depth=0  status=provisional
n=5  b=0.5905  u=0.4095  depth=0  status=provisional
```

Since `tensor` sets `new_b = a.b × b.b`, chaining yields `bⁿ`, and for `b < 1` this is strictly decreasing with `bⁿ → 0`. The thresholds at 0.8 and 0.5 are therefore crossed from above in finite steps for any `b < 1`. Status decays two levels under pure repetition. ∎

**This is not a tuning problem.** No choice of thresholds repairs it: for any threshold τ ∈ (0,1) and any b < 1, ∃n such that bⁿ < τ. The defect is that a strictly decreasing function is being read through fixed cutoffs.

**Corollary — it was predicted.** thesis_v3 §11.3, Problem 3:

> *"chain three HYPOTHESIS rules → result guaranteed ≤ HYPOTHESIS (by meet operation). With binned-Beta: propagate via sampling → bin result → **NO guarantee that bin assignment respects monotonicity**. Probability arithmetic does not respect binning thresholds."*

Written in March, against a continuous-then-bin architecture. v4 built that architecture. Theorem 1 is that warning, instantiated.

---

### Theorem 2 — The discrete design satisfies restatement monotonicity, unconditionally

**Claim.** Under §S6, `status(c)` is invariant under restatement — both along a chain and across accrual.

**Proof. [PROVEN]**

Chaining composes by ⋀ = min. min is idempotent: `min(s, s) = s` for all `s ∈ L`. By induction, the n-fold meet of `s` with itself is `s` for all n ≥ 1.

Accrual composes by ⋁ = max, likewise idempotent: `max(s, s) = s`.

Therefore restating evidence changes nothing, for every element of L and every n. ∎

**[OBSERVED]** — confirmation:

```
chained x5 under meet : ESTABLISHED   (invariant)
accrued x5 under join : ESTABLISHED   (invariant)
mixed ESTABLISHED ⋀ HYPOTHESIS ⋀ ESTABLISHED = HYPOTHESIS  (weakest link preserved)
```

**The significance is the asymmetry of effort.** The continuous design must be *patched* to achieve idempotence — that is exactly what the source-overlap discount in `oplus` is, and it works: **[OBSERVED]** a tag accrued against itself holds at `b=0.9000` across four rounds. But it is a special case bolted on to restore a law. In the discrete design the same law is a one-line consequence of `min(s,s) = s`, holds for chaining as well as accrual, and needs no parameter. **That difference — patched versus free — is the argument for the subtraction.**

---

### Theorem 3 — Depth accounting is broken today and is trivially correct in the target

**Claim.** `derivation_depth` never increments.

**Proof. [OBSERVED]** In the trace above, `depth=0` at n=5. `tensor` computes `a.depth + b.depth`; both operands originate at 0, so `0 + 0 = 0` for all compositions. The docstring states the axiom *"derivation_depth uses + for tensor (chains add depth)"* — **the code's own stated axiom and its behaviour disagree**, and the field that would have exposed Theorem 1 is the one that never moves. ∎

**Target:** depth is a property of the argument, not of the tag: `depth(a) = 1 + max{ depth(s) : s ∈ sub_args(a) }`, with premise arguments at 0. Well-founded because the argument graph is acyclic by construction (cycle detection at Stage E). Survives the subtraction — depth is metadata, not opinion.

---

### Theorem 4 — Augmentation containment (why PROVISIONAL beats a numeric cap)

**Setup.** Auto-generated rules today get `epistemic_status = WORKING_HYPOTHESIS` and `MAX_CONFIDENCE = 0.75`. **[OBSERVED]** — `kb_augmentation.py:45, 354, 374`.

**Claim (target).** Assign every rule with `augmentation_metadata.origin ≠ CURATED` a status ≤ PROVISIONAL. Then: if *every* argument supporting `c` passes through at least one such rule, `status(c) ≤ PROVISIONAL`.

**Proof. [PROVEN]** For an argument `a` whose derivation includes a rule with status `p ≤ PROVISIONAL`, `σ(a) = ⋀(...) ≤ p ≤ PROVISIONAL`, since min is bounded above by each of its arguments. If every `a ∈ args(c)` with `label(a) = IN` satisfies this, then `status(c) = ⋁ σ(a) ≤ PROVISIONAL`, since max over a set bounded by PROVISIONAL is bounded by PROVISIONAL. ∎

**Corollary (and this is the desirable half).** If *some* IN argument reaches `c` without passing through an augmented rule, the join exceeds PROVISIONAL — correctly, because an independent curated derivation exists. The guarantee is tight, not blunt.

**Why the numeric cap cannot do this.** `confidence.existence ≤ 0.75` constrains one input to a product; it does not constrain the *output* of `epistemic_status()`. Because trust, decay and belief multiply and then get thresholded, a conclusion derived entirely through unvalidated LLM-generated rules can still be labelled `established` if the arithmetic lands above 0.8. **A cap on an input to a non-monotone pipeline is not a guarantee on the output.** The lattice bound is.

This is thesis_v3 §12.3's circularity argument, made operational: an LLM proposing rules must not be able to launder its own proposals into ESTABLISHED status through arithmetic.

---

### Inherited formal guarantees

These are cited, not re-proven. All hold for the target design, and none depends on the continuous arithmetic — **which is itself an argument that the arithmetic was never load-bearing.**

| ID | Guarantee | Basis | Status |
|---|---|---|---|
| F1 | Every query terminates | Datalog data complexity ∈ PTIME (Vardi 1982) | **[PROVEN]** cited |
| F2 | Grounded semantics in O(\|args\| × \|attacks\|) | Dvořák & Dunne 2018 | **[PROVEN]** cited |
| F3 | Accepted arguments are conflict-free | Dung 1995, Def. 6 | **[PROVEN]** cited |
| F4 | Closure + direct/indirect consistency | Caminada & Amgoud 2007, Thms 3–5 | **[PROVEN]** cited |
| F5 | Grounded labelling reaches a unique fixpoint | Wu, Caminada & Gabbay 2009 | **[PROVEN]** cited |
| F6 | Conformal coverage P(Y ∈ C(X)) ≥ 1−α | Vovk et al. 2005 | **[PROVEN]** cited, **[OPEN]** unrealised here |

### Impossibility constraints the target respects

| ID | Constraint | Response |
|---|---|---|
| I1 | No semantics satisfies all principles (Baroni & Giacomin 2007) | Accept UNDECIDED as OPEN; do not force resolution |
| I2 | Cardinality vs Quality Precedence incompatible (Bonzon et al. 2016) | Choose QP — pramāṇa ordering. **[DESIGN]**, documented |
| I3 | Gradual semantics pairwise incompatible (Amgoud & Beuselinck 2021) | Moot under discrete status — the constraint binds only continuous designs |
| I4 | Conformal coverage is marginal, not conditional (Vovk et al. 2005) | Coverage groups; never claim per-conclusion guarantees |
| I5 | Why-provenance NP-complete for recursive Datalog (Bourgaux et al. 2024) | Lazy/on-demand traces, not eager |
| I6 | Preferred/stable are NP/coNP-hard (Dvořák & Dunne 2018) | Grounded online; jalpa/vitaṇḍā offline with reported fallback |
| I7 | No differentiable relaxation is sound + tautology-preserving (Giannini et al. 2023) | Symbolic core; differentiate only the neural grounding layer |
| I8 | Calibration failure is topologically typical (Dawid 1982 / Belot 2013) | Adaptive recalibration, not a fixed curve |

**Note on I3.** Going discrete *dissolves* an impossibility constraint rather than navigating it. Six gradual semantics being pairwise incompatible is a problem only if you must choose one. That is a real, if modest, argument for the subtraction beyond Theorem 2.

---

### What cannot be proven, and must not be claimed

- **That P1–P8 are the right design criteria.** Value judgments, not theorems. **[DESIGN]**
- **That this architecture is optimal among all complete architectures.** The elimination argument in thesis §7.5.1 proves *necessity* of each component, not *optimality* of the assembly. The strongest honest claim remains **minimal complete**, not best.
- **That Nyāya confers formal advantage.** It does not. Settled in `proving-architecture-optimality.md` §2.
- **That the specific lattice L is optimal among lattices.** Requires a universality theorem plus a proof that L is the right homomorphic image. **[OPEN]**
- **That calibration will hold on this domain.** Conformal coverage is guaranteed under exchangeability; whether guide-extracted predicates satisfy exchangeability with query-time predicates is an empirical question nobody has tested. **[OPEN]**
- **That extraction is accurate.** Unmeasured. Everything downstream inherits this. **[OPEN]**

---

## 5. Against the field: what the target buys

[SAVeR (arXiv:2604.08401, April 2026)](https://arxiv.org/abs/2604.08401) audits LLM-agent beliefs before commitment, with six violation types that map closely onto this engine's attack taxonomy — `Contradiction` ↔ rebutting, `Invalid_Precondition` ↔ undermining, `Overgeneralization` ↔ undercutting via scope exclusion, `Circular_Reasoning` ↔ Stage E cycle detection.

The difference is the decision procedure. SAVeR prompts an LLM to stress-test a trajectory. This engine computes defeat from graph structure — polynomial, deterministic, terminating (F1–F3, F5). Their own limitation #3 concedes that auditing *"relies on the underlying LLM, and biases present in the base model may still affect verification outcomes."*

**The defensible claim is: our violations are computed, not judged.**

**The condition on claiming it:** in the sections I could read, SAVeR's faithfulness metrics appear to be produced by the auditor that also drives the repair — no human-annotated validation reported. That is a self-confirming loop. But this engine is not entitled to point at it yet, because its own arguments are built from predicates produced by an unmeasured extractor and graded by an instrument that scores `value_creation` against `not_value_creation` as a match. **Their unvalidated layer is the judge; ours is the input.** The claim becomes available the day S1 is measured — and not before.

---

## 6. The measurement layer — what makes any of this falsifiable

Proofs constrain the design. They say nothing about whether the running system matches it. Six executable gates, in CI:

**G1 — Algebra laws, property-based.** Restatement monotonicity (Theorem 2), accrual idempotence, identity, associativity within tolerance, depth accounting (Theorem 3). Generate tags/statuses; assert laws. **Write these before the subtraction** — two fail today, and their failure is the evidence that the subtraction is right rather than preferred. After removal they pass by construction; if they do not, the discrete design has its own defect and that is worth finding immediately.

**G2 — Matcher adversarial suite.** The seven pairs from the audit, as a permanent regression: three that must match, four that must not. The current matcher passes 3/7. **[OBSERVED]**

**G3 — Instrument validation.** Human-judged decisions on one extraction run become the test set for the matcher. Report agreement (Cohen's κ) between matcher and human. This is the step that makes the harness itself falsifiable, and it is the step CaRB took when replacing OIE2016 — where the two benchmarks produced *contradictory system rankings*, and human assessment settled it. A loose matcher does not add noise; it inverts conclusions.

**G4 — Interface contract.** Assert `set(returned_fields) ⊇ set(schema_fields)`, and enum agreement across the boundary. Would have caught all three S10 breaks.

**G5 — Degenerate-input suite.** Every metric on empty input. Specifically: `dag_validity(ValidationResult())` returns **1.0** while that same object reports `is_valid=False`. **[OBSERVED]** No component may score a pass on an absence of evidence.

**G6 — Determinism.** The suite currently reports 4 failed or 4 skipped depending on the directory pytest was launched from, because `litellm/__init__.py:82` calls `dotenv.load_dotenv()` and the skip condition reads the environment at import. **[OBSERVED]** Pin the environment explicitly; a suite whose result depends on cwd cannot gate anything.

---

## 7. Migration order

Forced by dependency, not preference. Each step is verifiable on completion.

1. **G4 + the S10 contract break.** Smallest, and the system is currently unusable end-to-end without it.
2. **G6 determinism.** Until the suite is deterministic, no later gate means anything.
3. **G1 law tests.** Before the subtraction. Two must fail.
4. **The subtraction (S6).** Delete the opinion arithmetic; re-derive status from labelling + lattice. Theorem 1's bug disappears with it — do not patch `epistemic_status()`, it is scheduled for deletion. Track the line count going down.
5. **Depth (Theorem 3).** Separate from the subtraction; depth is metadata and survives it.
6. **PROVISIONAL + Theorem 4.** One enum value, one origin check, one guarantee. Replaces `MAX_CONFIDENCE`.
7. **S1/S3 matcher — polarity veto + descriptions + relational order check.** Fixes coverage routing *and* the eval harness with the same code.
8. **G3 instrument validation**, then the first real extraction number.
9. **S7 conformal calibration** — gated on step 8, which supplies the labels.
10. **Honesty pass:** four grounding layers not five; report reward components not a composite; announce retrieval fallback and contestation timeouts.

Steps 1–3 are days. Steps 4–6 are the architectural work. Steps 7–8 unblock every empirical claim the project wants to make.

---

## 8. What would falsify this design

Stated so the document is refutable:

- **G1 passes today.** If the law tests pass against the current continuous implementation, Theorem 1 is somehow not reachable through the real pipeline, and the subtraction loses its empirical motivation. (Theorem 1 was observed on `ProvenanceTag` directly, not through a full engine run — that gap is real and step 3 closes it.)
- **Discrete status proves too coarse in practice.** If synthesis quality measurably degrades with six lattice values plus a prediction set versus continuous belief, P4 wins over §11 and the decision should be revisited. This is empirical and untested. **[OPEN]**
- **Exchangeability fails.** If guide-extracted and query-time predicates are not exchangeable, conformal coverage does not hold here and S7 needs replacing rather than implementing.
- **Extraction measures well below the kill line.** If recall < 0.5 once measured properly, the bottleneck is not the reasoning core at all, and the architectural work in steps 4–6 is premature optimisation of a layer whose input is noise.
- **A cheaper architecture achieves F1–F6.** The minimality argument enumerates six alternatives; it does not enumerate all architectures. A seventh that achieves all seven desiderata with fewer components refutes the minimality claim.

---

## 9. What this document did not examine

The reasoning core, the extraction harness, the API boundary, and the theory documents. Not examined: `webapp/` beyond the schema contract, `predicate_extraction.py` beyond its stage boundaries and the two helpers the evaluator imports, `t3_compiler.py`, `traces/`, performance (nothing was profiled; no speed claim is made anywhere above), and the `anvikshiki/` and `anvikshiki_p2/` trees.

Theorem 1 was observed on `ProvenanceTag` in isolation. Theorems 2 and 4 are proofs about a design that does not yet exist in code. Everything marked **[DESIGN]** is a choice, and everything marked **[OPEN]** is a debt.
