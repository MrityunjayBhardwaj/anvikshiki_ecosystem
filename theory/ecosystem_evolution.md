# Anvikshiki Ecosystem: Evolution Log

## How a meta-prompt for generating expert guides became a neurosymbolic reasoning engine — and why every architectural decision was made.

---

## Table of Contents

1. [Origin: The Problem](#1-origin-the-problem)
2. [Era 1: The Meta-Prompt (v3.2 → v3.25 → v3.26)](#2-era-1-the-meta-prompt)
3. [Era 2: The Meta-Meta-Prompt (meta^2)](#3-era-2-the-meta-meta-prompt)
4. [Interlude: Is Anvikshiki Turing Complete?](#4-interlude-is-anvikshiki-turing-complete)
5. [Era 3: The Engine — Thesis v1 (Prolog + Sheaf)](#5-era-3-the-engine--thesis-v1)
6. [Era 4: The Critical Revision — Thesis v2 (Prolog → Datalog)](#6-era-4-the-critical-revision--thesis-v2)
7. [Era 5: KB Bootstrapping — Thesis v3](#7-era-5-kb-bootstrapping--thesis-v3)
8. [Era 6: The Frankenstein Problem — Thesis v4 (ASPIC+ Unification)](#8-era-6-the-frankenstein-problem--thesis-v4)
9. [Era 7: Implementation & Hardening (v4 Codebase)](#9-era-7-implementation--hardening)
10. [Era 8: Automated Predicate Extraction](#10-era-8-automated-predicate-extraction)
11. [Era 9: Query Refinement & Honest Decline](#11-era-9-query-refinement--honest-decline)
12. [The Knowledge Bank Architecture](#12-the-knowledge-bank-architecture)
13. [Architecture Decision Log](#13-architecture-decision-log)
14. [File Genealogy](#14-file-genealogy)

---

## 1. Origin: The Problem

LLMs are extraordinary pattern matchers. They generate plausible text about any domain. But they cannot:

- **Infer**: Chain domain rules to derive conclusions
- **Constrain**: Detect and reject fallacious reasoning
- **Qualify**: Carry epistemic status ("established" vs "hypothesis" vs "contested") through inference
- **Decompose uncertainty**: Separate "we don't have evidence" from "the domain is inherently uncertain"
- **Ground to sources**: Trace every claim to cited evidence
- **Respect scope**: Know when a rule applies and when it doesn't
- **Decay gracefully**: Halt inference on stale knowledge

RAG doesn't solve this — it's similarity retrieval, not inference. Knowledge graphs are Boolean (edge exists or doesn't). No existing system does all seven.

The Anvikshiki project started from a different angle: *what if we could generate expert-level guides so structured that they could be compiled into a reasoning engine?*

---

## 2. Era 1: The Meta-Prompt

**Files:** `theory/history/meta_prompts/meta_prompt_v3.2.md` → `v3.25` → `v3.26`

The project began as a meta-prompt — a specification for generating expert-level instructional guides. The name comes from *Ānvīkṣikī* (Sanskrit: आन्वीक्षिकी), the ancient Indian science of critical inquiry described by Kautilya as "the lamp of all sciences, the means of all actions, the foundation of all dharmas."

The meta-prompt uses three core constructs from Nyāya epistemology:

- **Pramāṇa** (means of valid knowledge): How do we know something is true in this domain?
- **Vyāpti** (invariable concomitance): Domain rules — "wherever there is smoke, there is fire"
- **Hetvābhāsa** (fallacious reason): Formal constraints on how reasoning can fail

### v3.2 — The Foundation (7 stages, 2,660 lines)

The initial stable version. Seven enforced stages with hard gates:

1. **Stage 1**: Domain & Reader Calibration
2. **Stage 2**: Knowledge Architecture (vyāptis, hetvābhāsas, dependency DAG)
3. **Stage 3**: Research Gate (source verification)
4. **Stages 4–6**: Guide Generation (chapters, sessions, prose)
5. **Stage 7**: Quality Verification

Key innovation: **enforced stage gate protocol** — no stage can begin until its predecessor's outputs are verified. This prevents the common LLM failure of generating plausible text without proper structural foundation.

### v3.25 — Incremental Enhancement (7 stages, 2,816 lines)

Added tier classification for tracking elements (Tier 1/2/3), enhanced element tracking (19 categories), and clearer derivation proof requirements.

**Same fundamental architecture as v3.2**, but tighter verification loops.

### v3.26 — The Prevention Revolution (8 stages, 3,962 lines)

**The biggest philosophical shift in the meta-prompt's history.**

**v3.25's problem**: Quality control was *post-hoc*. Stage 7 caught problems after 20,000+ words of generation. By then, voice had drifted, terminology was inconsistent, forward references were forgotten.

**v3.26's solution**: 21 prevention controls (C1–C21) built into the generation process itself, so Stage 8's error manifest should theoretically be empty.

Key additions:

| Control | What It Does | Problem It Prevents |
|---------|-------------|---------------------|
| **C1: Action Titles** | Every title must pass 3 tests (Disagreement, Domain Specificity, Compression) | Vague chapter titles that don't encode insights |
| **C2: MECE Assertions** | Exhaustive coverage mandatory at every branching point | Missing domain areas |
| **C3: Emotional Beats** | 5-beat arc with sequencing constraints per chapter | Too many hard chapters in a row |
| **C4: Debate Cruxes** | Every debate must have a genuine crux statement | False debates that dissolve on examination |
| **C5: Forward Reference Matrix** | Pre-plans all cross-chapter connections | Forward references that get forgotten |
| **C8: Epistemic Status** | Every vyāpti carries confidence level + evidence quality + rendering rule | Overconfident claims |
| **C9: Voice Calibration** | 500–800 word voice sample before any prose | Voice inconsistency across chapters |
| **C10: Session Start Protocol** | 6-step checklist before each generation session | Context loss between sessions |
| **C11: Chapter Fingerprints** | 13-section structured summary after every chapter (~200–300 words) | Terminology drift, concept inconsistency |
| **C12: Forward Hook Ledger** | OPEN/RESOLVED tracking of all planted forward references | Unkept promises |
| **C13: Simulation Quality** | 5-point check before finalizing any transfer test | Weak simulations that don't create productive confusion |
| **C14: Tacit Knowledge Test** | Derivability test — if explicit knowledge could write it, it's not tacit | Fake tacit knowledge |

**New Stage 8**: Safety Net Revision — checks 6 failure types and diagnoses *why* prevention failed for each.

**Why this matters for the engine**: The guide's Stage 2 output (vyāptis, hetvābhāsas, dependency DAG, epistemic status) becomes the knowledge base that the engine compiles. The meta-prompt's precision directly determines the engine's knowledge quality.

> See: `theory/history/discussions/v3-25-vs-v3-26-comparison.md`

---

## 3. Era 2: The Meta-Meta-Prompt

**Files:** `theory/history/meta_prompts/anvikshiki_meta2_design_doc.md`, `anvikshiki_meta2_prompt.md`, `anvikshiki_meta2_prompt_v3_26.md`

A self-referential step: a prompt that generates the meta-prompt itself. This enables:

- Adapting the meta-prompt to new domain types without manual rewriting
- Systematically evolving the prevention controls
- Generating guides that generate guides

The meta^2 prompt encodes the *design principles* behind v3.26 — not the content of any particular guide, but the structural rules that make any guide pedagogically sound.

---

## 4. Interlude: Is Anvikshiki Turing Complete?

**File:** `theory/history/discussions/is-anvikshiki-turing-complete.md`

This discussion shaped a critical architectural decision. The answer:

**As Kautilya described it: No.** Vyāptis are syllogistic (modus ponens). Syllogistic logic is decidable, has no general recursion, and cannot simulate a Turing machine.

**But vyāptis map to Horn clauses — the foundation of Prolog:**

```prolog
% Vyāpti V1
fire(X) :- smoke(X).

% Vyāpti V2
strategic_reinvestment_possible(Co) :-
    concentrated_ownership(Co).
```

With function symbols, Horn clauses become Turing complete. Without them (Datalog), they remain decidable and polynomial.

**The architectural implication**: Anvikshiki's vyāptis don't need function symbols — they're purely relational. This means **Datalog is sufficient**, and we get guaranteed termination + polynomial complexity for free.

This insight drove the Prolog → Datalog migration in Era 4.

---

## 5. Era 3: The Engine — Thesis v1

**Files:** `theory/history/thesis/thesis_v1.md` (2,628 lines), `theory/history/build_guides/BUILD_GUIDE_v2.md`

**Subtitle**: "From Philosophical Epistemology to Neurosymbolic Inference: Building a Sheaf-Theoretic Knowledge Engine for Domain-Specific Reasoning"

The first formal thesis. The engine compiles a guide's Stage 2 architecture into two subsystems:
- **T2**: Logic engine (domain rules as executable inference)
- **T3**: GraphRAG corpus (guide prose as retrievable context)

### Four-Phase Architecture

| Phase | Components | What It Adds |
|-------|-----------|-------------|
| 1 | DSPy only | Baseline LLM reasoning — no symbolic engine |
| 2 | DSPy + Prolog | Rule chaining, constraint checking, scope conditions |
| 3 | DSPy + Prolog + UQ | Uncertainty decomposition (epistemic / aleatoric / inference) |
| 4 | DSPy + Heyting + UQ | Sheaf-theoretic consistency checking over Heyting-valued logic |

### Key Design Decisions

**Prolog for inference**: Vyāptis map to Horn clauses. Prolog provides unification, recursive rules, and unbounded inference depth. The engine uses Prolog's SLD resolution for forward chaining through the vyāpti graph.

**Heyting lattice for epistemic status**: Five truth values — ESTABLISHED, HYPOTHESIS, OPEN, CONTESTED, BOTTOM — carried through every inference step. Not Boolean (true/false) but intuitionistic (what can we *construct* evidence for?).

**Cellular sheaf for consistency**: Scope conditions ("holds for private firms but not public ones") create local/global consistency problems. Sheaf cohomology detects when locally valid reasoning produces globally inconsistent conclusions.

**Seven desiderata**: Infer, constrain, qualify, decompose uncertainty, ground to sources, respect scope, decay gracefully.

### What Was Missing

The thesis identified the grounding problem (NL query → KB predicates) but didn't solve it systematically. It noted that LLMs would hallucinate predicates, but proposed no defense beyond careful prompting.

---

## 6. Era 4: The Critical Revision — Thesis v2

**Files:** `theory/history/thesis/thesis_v2.md` (2,925 lines), `theory/history/thesis/thesis_v2_patch.md` (1,669 lines)

**Subtitle**: "Building a Lattice-Datalog Knowledge Engine with Layered Grounding Defense"

Three critical changes from v1:

### 6.1 Prolog → Datalog

**Why**: After the Turing completeness analysis, it became clear that Prolog's power was unnecessary and dangerous:

| Property | Prolog | Datalog |
|----------|--------|---------|
| Termination | Not guaranteed (unbounded recursion) | Guaranteed (finite domain, no function symbols) |
| Complexity | Undecidable in general | Polynomial (PTIME for fixed rules) |
| Evaluation | Top-down SLD resolution | Bottom-up semi-naive evaluation |
| Inference cost | O(rules × facts) per iteration | O(rules × Δfacts) per iteration |
| Lattice extension | Semantic strain | Natural composition with Heyting values |

Vyāptis are purely relational ("positive_unit_economics → value_creation"). No function symbols, no complex term manipulation. Datalog captures this exactly, with guaranteed termination.

**Semi-naive evaluation** was a key performance insight: instead of re-checking all rules against all facts each iteration, only newly derived facts (Δfacts) trigger rule re-evaluation. Cost drops from O(rules × facts) to O(rules × Δfacts).

### 6.2 Five-Layer Grounding Defense

The thesis identified grounding (NL → predicates) as the **single point of failure**. A hallucinated predicate silently poisons the entire inference chain. Defense-in-depth:

1. **Ontology-constrained prompting**: LLM can only emit predicates from the KB vocabulary
2. **Grammar-constrained decoding**: XGrammar/Instructor forces valid JSON with KB predicate names
3. **Ensemble consensus**: N=5 independent groundings; only predicates in majority survive
4. **Round-trip verification**: Ground → verbalize → re-ground; discard if round-trip disagrees
5. **Solver-feedback refinement**: Run inference, check for contradictions, revise grounding

No single layer is sufficient. Together they eliminate silent hallucinations.

### 6.3 Phase Architecture Simplification

The Boolean → Heyting transition (Phase 2 → Phase 3) is now a **dimension addition** (add lattice values to existing Datalog), not an **engine migration** (replace Prolog with Heyting engine). This eliminates the riskiest transition in v1.

> See: `theory/history/thesis/thesis_v2_patch.md` for detailed Prolog→Datalog migration notes

---

## 7. Era 5: KB Bootstrapping — Thesis v3

**Files:** `theory/history/thesis/thesis_v3.md` (3,356 lines), `theory/history/build_guides/BUILD_GUIDE_v3.md`

**Subtitle**: "Building a Lattice-Datalog Knowledge Engine with Epistemic Qualification, Sheaf Consistency, and Automated KB Bootstrapping"

Five revisions from v2:

### 7.1 Grounding Cost Reduction

v2's five-layer defense required 5–7 LLM calls per query. v3 introduces a **two-layer default** (ontology-constrained prompting + solver-feedback) with **three-layer escalation** only for high-uncertainty queries. Cost drops to 1–2 LLM calls for typical queries.

### 7.2 Conformal Prediction → Provenance Chain Tracing

v2 used split conformal prediction for source verification (statistical guarantees on source reliability). v3 replaces this with **deterministic provenance chain tracing** through Datalog proof trees — 0 LLM calls, exact rather than statistical, and directly inspectable.

### 7.3 PROVISIONAL Epistemic Status

The Heyting lattice expands from 5 to 6 values, adding PROVISIONAL — for auto-generated rules awaiting expert review.

### 7.4 Automated KB Bootstrapping

v1 and v2 required domain experts to author the entire KB (vyāptis, hetvābhāsas, scope conditions). v3 automates this: the engine extracts candidate rules from guide prose and presents them for expert validation. Expert involvement drops from authoring to **targeted validation of ~15–20% of auto-generated rules**.

### 7.5 Source Authority Model (Śabda)

Formalizes classical Nyāya testimony conditions (śabda) as trust-based epistemic defaults: a source's credibility depends on expertise, track record, and domain relevance. Sheaf consistency overrides trust when structural inconsistencies are detected.

### The v3 Implementation (anvikshiki/)

The first complete codebase: 12 modules, ~2,600 LOC, 9 test files.

| Module | LOC | Purpose |
|--------|-----|---------|
| `schema.py` | 149 | KnowledgeStore, Vyapti, Hetvabhasa models |
| `datalog_engine.py` | 368 | Semi-naive Datalog with lattice values |
| `t2_compiler.py` | 289 | Vyāptis → Datalog rules |
| `t3_compiler.py` | 260 | GraphRAG corpus builder |
| `grounding.py` | 302 | Five-layer NL→predicate defense |
| `uncertainty.py` | 165 | UQ decomposition |
| `conformal.py` | 121 | Split conformal prediction |
| `sheaf.py` | 197 | Cellular sheaf (coboundary, Laplacian, H^1) |
| `engine.py` | 465 | 7-step pipeline orchestrator |
| `optimize.py` | 148 | MIPROv2 DSPy optimizer |
| `cli.py` | 128 | Command-line interface |

**65 tests passing.** All seven desiderata met.

But there was a problem.

---

## 8. Era 6: The Frankenstein Problem — Thesis v4

**Files:** `theory/thesis2_v1.md` (3,294 lines — **current thesis**), `theory/history/build_guides/BUILD_GUIDE_v4.md`

**Subtitle**: "From Nyāya Epistemology to Neurosymbolic Argumentation: A Unified Architecture via Structured Argumentation over Provenance Semirings"

### The Problem

The v3 engine worked. But it used **six independent formalisms** to achieve its seven desiderata:

1. **Heyting lattice** for epistemic status tracking
2. **Cellular sheaf** for consistency checking
3. **Hand-specified trust tables** for source authority
4. **Keyword-based hetvābhāsa detection** for fallacy catching
5. **Identity restriction maps** for scope conditions
6. **Hand-tuned uncertainty thresholds** (DOMAIN_BASE_UNCERTAINTY dict)

Each concern was solved by the best tool from a different intellectual tradition. The resulting architecture had **no single organizing principle**. Modifying one formalism required understanding five others. Adding a new domain rule required updates in multiple unrelated subsystems.

This is the Frankenstein problem: the creature works, but it doesn't cohere.

### The Insight

Nyāya concepts map naturally to **ASPIC+ argumentation** (Wu, Caminada, Gabbay 2009):

| Nyāya | ASPIC+ | What It Does |
|-------|--------|-------------|
| Vyāpti | Defeasible rule | Domain inference rules |
| Hetvābhāsa | Defeat relation | Attack on arguments (rebutting, undercutting, undermining) |
| Pramāṇa hierarchy | Argument preference | Source of knowledge determines strength |
| Epistemic status | Extension membership | *Emerges* from which arguments survive attacks |
| Pañcāvayava | Argument tree | Structured proof trace |

And **provenance semirings** (Green et al., PODS 2007) handle all quantitative aspects:

- **Belief / Disbelief / Uncertainty** as a Subjective Logic opinion triple
- **⊗ (tensor)**: Combining evidence along an inference chain (belief attenuates, uncertainty accumulates)
- **⊕ (oplus)**: Accumulating evidence from multiple independent sources (belief grows, uncertainty shrinks)
- **Trust, pramāṇa type, source tracking**: Native fields on the semiring tag

### What Became Unnecessary

| v3 Formalism | v4 Replacement | Why |
|-------------|----------------|-----|
| Heyting lattice | Extension membership + tag values | Epistemic status *emerges* from argumentation |
| Cellular sheaf | Rationality postulates | ASPIC+ guarantees consistency structurally |
| Trust tables | ProvenanceTag.trust_score | Trust propagates through the semiring |
| Keyword hetvābhāsa | Defeat relations | Hetvābhāsas *are* attacks — rebutting, undercutting, undermining |
| Identity restriction maps | Undercutting attacks | Scope exclusions generate undercutters automatically |
| DOMAIN_BASE_UNCERTAINTY | Derives from tag fields | Uncertainty is algebraic, not hand-tuned |

**Six formalisms → two that naturally compose.** Same seven desiderata. Stronger theoretical foundation.

### Native Contestability

A bonus: the architecture satisfies all 8 Contestable AI properties (Moreira et al. 2025) through its argumentation structure. No post-hoc explanation mechanism needed.

Three debate protocols from Nyāya tradition:

- **Vāda** (cooperative inquiry) → **Grounded semantics**: What can we all agree on?
- **Jalpa** (adversarial stress test) → **Preferred semantics**: What positions are defensible?
- **Vitaṇḍā** (vulnerability audit) → **Stable semantics**: Where are the weaknesses?

> See: `theory/history/discussions/critical-analysis-v4-post-fix-round.md` for post-implementation audit

---

## 9. Era 7: Implementation & Hardening

**Files:** `anvikshiki_v4/` (17 modules, ~5,200 LOC, 249 tests)

The v4 codebase was built in three phases:

### Phase 1: Foundation
- `schema_v4.py` — ProvenanceTag semiring with ⊗/⊕ operators
- `argumentation.py` — ArgumentationFramework with grounded/preferred/stable semantics
- `t2_compiler_v4.py` — Vyāptis → arguments + attacks + provenance tags

### Phase 2: Compilation + UQ
- `engine_v4.py` — 8-step pipeline orchestrator
- `uncertainty.py` — Derives from ProvenanceTag fields (no hand-tuned thresholds)
- Reused: `schema.py`, `datalog_engine.py`, `grounding.py`, `t3_compiler.py`

### Phase 3: Contestation + Engine
- `contestation.py` — Vāda/Jalpa/Vitaṇḍā protocols
- `optimize.py` — DSPy optimizer for argumentation metrics

### Post-Implementation Audit

Three parallel research agents cross-referenced every thesis specification against implementation code. Results from `critical-analysis-v4-post-fix-round.md`:

**No hard bugs or ASPIC+ violations.** Issues found:

| Issue | Severity | Resolution |
|-------|----------|-----------|
| Tensor normalization breaks exact associativity | Medium | Documented — engineering tradeoff, error within 0.05 tolerance |
| oplus clamping | Low | Safety net, rarely activates |
| BELIEF_MAP missing PROVISIONAL | Low | By design — v4 KB schema doesn't use it yet |
| 3 dead code items | Low | Cleanup |
| 4 robustness gaps | 2 medium, 2 low | Defensive hardening |

**65 tests passing** (pre-extraction pipeline). All seven desiderata verified.

---

## 10. Era 8: Automated Predicate Extraction

**Files:** `anvikshiki_v4/predicate_extraction.py` (1,123 lines), `anvikshiki_v4/extraction_schema.py`, `anvikshiki_v4/extraction_eval.py`, `anvikshiki_v4/extraction_hitl.py`

**The problem**: The seed KB (`business_expert.yaml`) has 20 predicates at chapter-level granularity. The guide has section-level detail. The engine can only reason about what's in the KB.

**Before** (seed KB):
```
20 core predicates → 11 vyāptis (V01–V11)
Query: "Does a company with positive unit economics always create value?"
→ Coarse reasoning at chapter level
```

**After** (augmented KB):
```
~50 predicates → ~25 vyāptis (V01–V15+)
Query: "Does a company with strong LTV-CAC ratio and positive contribution margin have viable unit economics?"
→ Granular reasoning at section level, with sub-component decomposition
```

### Extraction Pipeline Architecture

A four-stage pipeline using DSPy signatures:

1. **ExtractPredicates**: Guide prose → candidate predicates with claim types
2. **DeduplicatePredicates**: Remove near-duplicates, merge overlapping concepts
3. **ComposeVyaptis**: Relate new predicates to existing KB via antecedent/consequent structure
4. **HumanInTheLoop**: Present candidates for expert review (approve/reject/modify)

### Evaluation Framework

Gold-standard evaluation against `expected_predicates.yaml`:
- Precision/recall at token overlap threshold
- Claim type accuracy
- Vyāpti composition correctness

**67 additional tests** added to the suite, covering all extraction pipeline stages.

> See: `docs/predicate_extraction_design.md`, `docs/predicate_extraction_theory.md`

---

## 11. Era 9: Query Refinement & Honest Decline

**Files:** `anvikshiki_v4/query_refinement.py` (407 lines)

**The problem**: Users submit vague queries like "How do I improve customer retention?" The engine force-maps these to the nearest KB predicates — even when the KB doesn't cover the topic. This produces confident-sounding answers about things the KB barely knows.

**The solution**: A pre-pipeline stage that:

1. **Clarifies intent** (1 LLM call): Maps user concepts to KB predicates, identifies unmapped concepts
2. **Checks coverage** (0 LLM calls): Deterministic Jaccard token overlap + vyāpti matching
3. **Routes honestly**:
   - Coverage ≥ 0.6 → **PROCEED** (run full pipeline)
   - Coverage 0.2–0.6 → **PARTIAL** (explain gaps, proceed with caveat)
   - Coverage < 0.2 → **DECLINE** ("I don't have relevant info about X. Closest is Y, but I need Z.")

### Example: Honest Decline

```
Query: "What's the best marketing channel for B2B SaaS?"

→ mapped_predicates: []
→ unmapped_concepts: [marketing_channel, b2b_saas, channel_effectiveness]
→ coverage_ratio: 0.0
→ closest_predicates: {"marketing_channel": "distorted_market_signal"}

→ "I don't have relevant information about marketing channels.
   The closest thing in my knowledge base is distorted_market_signal (V05).
   To answer your question, I would need information about
   marketing_channel_effectiveness and acquisition_cost_by_channel."
```

This is the engine *saying "I don't know"* — a capability that most AI systems lack.

**38 additional tests**, bringing the total to **249 tests passing**.

---

## 12. The Knowledge Bank Architecture

**File:** `theory/history/discussions/knowledge-bank-and-agent-council.md`

A pivotal discussion that established how the engine relates to the guide:

### Why RAG Alone Fails

Anvikshiki guides are designed for progressive sequential reading. Concept B requires Concept A. RAG collapses this — it retrieves Chapter 7, paragraph 3, which assumes the reader absorbed the pramāṇa framework from Chapter 1, the failure ontology from the opening, and the causal/correlation distinction from Chapter 4.

**RAG is similarity retrieval. Anvikshiki is an inference system.** Using RAG as primary is using the wrong tool.

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────┐
│  LAYER 1: Logic Engine (Stage 2 as program)     │
│  Vyāptis as Horn clauses, hetvābhāsas as        │
│  constraints, dependency graph as prerequisites  │
│  Queries: inference, constraint checking,         │
│           derivation tracing                     │
└──────────────────────┬──────────────────────────┘
                       ↓
┌──────────────────────┴──────────────────────────┐
│  LAYER 2: Reference Bank (Stage 3 sources)      │
│  Verified citations with 6-class provenance      │
│  Queries: "What does the evidence say about X?"  │
└──────────────────────┬──────────────────────────┘
                       ↓
┌──────────────────────┴──────────────────────────┐
│  LAYER 3: Prose RAG (Guide text + fingerprints) │
│  Chunked by chapter with rich metadata           │
│  Queries: worked examples, analogies, narrative  │
└─────────────────────────────────────────────────┘
```

**Critical rule**: Layers queried in order — 1 → 2 → 3. An agent never reaches Layer 3 (prose) without first establishing structural context from Layer 1.

---

## 13. Architecture Decision Log

A chronological record of every major decision and its rationale.

### ADR-001: Use Nyāya Epistemology as Design Ontology

**Context**: Need a philosophical framework for domain-specific reasoning with epistemic qualification.

**Decision**: Nyāya, not Bayesian, not Dempster-Shafer, not reliabilism.

**Rationale**: Nyāya provides:
- Typed knowledge sources (pramāṇa) that distinguish HOW we know, not just confidence
- Formal fallacy taxonomy (hetvābhāsa) for constraint checking
- Structured proof format (pañcāvayava) for inspectable reasoning
- Scope conditions native to the framework
- 2,500 years of refinement on exactly this problem

**Alternatives rejected**:
- Bayesian: treats all evidence as fungible probabilities, can't distinguish epistemic failure modes
- Dempster-Shafer: lacks structured debate theory
- Reliabilism: focuses on individual belief, not knowledge-seeking community

### ADR-002: Build Meta-Prompt Before Engine

**Context**: Could start with the engine and generate knowledge manually.

**Decision**: Build the guide generation system first.

**Rationale**: The meta-prompt's Stage 2 output (vyāptis, hetvābhāsas, dependency DAG) is precisely the knowledge base the engine needs. By building the meta-prompt first, we ensure the KB format is pedagogically grounded — not an arbitrary schema invented for the engine.

### ADR-003: Prevention-First Quality Control (v3.26)

**Context**: v3.25 relied on post-hoc Stage 7 repair.

**Decision**: 21 prevention controls (C1–C21) built into generation.

**Rationale**: By Stage 7, 20,000+ words of prose exist. Rewriting voice, fixing terminology, and resolving broken forward references is expensive. Prevention at source is cheaper and more reliable.

### ADR-004: Replace Prolog with Datalog

**Context**: Vyāptis are Horn clauses. Prolog implements Horn clauses. Obvious choice?

**Decision**: Datalog (function-free Horn clauses) instead of full Prolog.

**Rationale**: Vyāptis are purely relational ("positive_unit_economics → value_creation"). No function symbols needed. Datalog gives us:
- Guaranteed polynomial termination (vs. Prolog's potential non-termination)
- Semi-naive evaluation: O(rules × Δfacts) instead of O(rules × facts)
- Natural lattice extension for Heyting values
- Phase transitions become dimension additions, not engine migrations

### ADR-005: Five-Layer Grounding Defense

**Context**: NL → predicate mapping is the architecture's weakest link. A single hallucinated predicate silently poisons the entire inference chain.

**Decision**: Five-layer defense-in-depth.

**Rationale**: No single technique is reliable enough. Ontology-constrained prompting can be bypassed by creative paraphrasing. Grammar constraints can be too rigid. Ensemble consensus catches most errors but not all. Round-trip verification is expensive but thorough. Solver-feedback catches logical contradictions. Together: defense-in-depth.

### ADR-006: Unify via ASPIC+ (The Frankenstein Fix)

**Context**: v3 uses six independent formalisms with no organizing principle.

**Decision**: Replace all six with ASPIC+ argumentation + provenance semirings.

**Rationale**:
- Nyāya concepts map directly to ASPIC+ (vyāpti → defeasible rule, hetvābhāsa → attack, pramāṇa → preference)
- Epistemic status *emerges* from extension membership instead of being hand-assigned
- Provenance semirings handle all quantitative aspects through algebra instead of hand-tuned thresholds
- Sheaf consistency checking becomes unnecessary — argumentation rationality postulates provide the same guarantees

### ADR-007: Honest Decline (Query Refinement)

**Context**: Engine produces confident answers even when KB doesn't cover the query topic.

**Decision**: Pre-pipeline coverage check that says "I don't know" when appropriate.

**Rationale**: A system that confidently answers questions outside its knowledge is worse than one that honestly declines. Coverage ratio < 0.2 triggers honest decline with closest KB predicates and explicit gaps. One LLM call overhead, zero false confidence.

### ADR-008: Automated Predicate Extraction

**Context**: Seed KB has 20 predicates (chapter-level). Guide prose has section-level detail.

**Decision**: DSPy pipeline to extract predicates from prose and compose them into vyāptis.

**Rationale**: Manual predicate authoring doesn't scale. But fully automatic extraction is unreliable. Solution: automated extraction + human-in-the-loop review. Expert involvement drops from authoring to validation (~15–20% of candidates).

---

## 14. File Genealogy

### Thesis Evolution

```
thesis_v1.md (2,628 lines)
│  "Sheaf-Theoretic Knowledge Engine"
│  Prolog + Heyting lattice + Sheaf
│  Four phases: DSPy → +Prolog → +UQ → +Sheaf
│
├── thesis_v2.md (2,925 lines)
│   "Lattice-Datalog Knowledge Engine with Layered Grounding Defense"
│   Prolog → Datalog, five-layer grounding added
│   Semi-naive evaluation
│   │
│   ├── thesis_v2_patch.md (1,669 lines)
│   │   Companion document: why Prolog was replaced
│   │
│   └── thesis_v3.md (3,356 lines)
│       "+Epistemic Qualification, Sheaf Consistency, Automated KB Bootstrapping"
│       Conformal → provenance tracing, PROVISIONAL status
│       Automated KB bootstrapping, source authority model
│       12 modules, competitive analysis
│
└── thesis2_v1.md (3,294 lines) ← CURRENT
    "Neurosymbolic Argumentation via Structured Argumentation over Provenance Semirings"
    The Frankenstein fix: ASPIC+ unifies 6 formalisms into 2
    Native contestability, Nyāya debate protocols
    17 modules, 249 tests
```

### Meta-Prompt Evolution

```
meta_prompt_v3.2.md (2,660 lines, 7 stages)
│  Foundation: enforced stage gates, element tracking
│
├── meta_prompt_v3.25.md (2,816 lines, 7 stages)
│   Tier classification, enhanced tracking
│
└── meta_prompt_v3.26.md (3,962 lines, 8 stages) ← CURRENT
    21 prevention controls (C1–C21)
    Voice calibration, chapter fingerprints, forward hook ledger
    Stage 8: Safety Net Revision
```

### Build Guide Evolution

```
BUILD_GUIDE_v2.md (2,263 lines)
│  10 modules, aligned with thesis_v2
│
├── BUILD_GUIDE_v3.md (2,103 lines)
│   12 modules, provenance tracing, source authority
│
└── BUILD_GUIDE_v4.md (3,294 lines) ← CURRENT
    17 modules, ASPIC+ + provenance semirings
    Appendices: Nyāya→ASPIC+ tables, semiring math, contestable AI checklist
```

### Engine Codebase Evolution

```
anvikshiki/        (v3: 2,605 LOC, 12 modules, 65 tests)
│  Heyting lattice + sheaf + conformal + keyword hetvābhāsa
│
├── anvikshiki_p2/ (experimental: boolean Datalog phase)
│   Phase 2 substrate, pure forward chaining
│
└── anvikshiki_v4/ (v4: ~5,200 LOC, 17 modules, 249 tests) ← CURRENT
    ASPIC+ argumentation + provenance semirings
    + Predicate extraction pipeline
    + Query refinement with honest decline
    + Three contestation protocols
```

### Business Expert Guide

```
guides/v325/business_expert/     (earlier iteration, stage-based)
│
└── guides/business_expert/      (v3.25 final, 14 files) ← CURRENT
    12 chapters covering business strategy
    Stage 1 (calibration) + Stage 2 (architecture) + Stage 3 (sourcing)
    Compiled into business_expert.yaml (11 vyāptis, 8 hetvābhāsas)
```

---

## Summary: From Meta-Prompt to Reasoning Engine

```
2024–2025                           2026 (Feb)                    2026 (Mar 2)
Meta-prompt v3.2                    Engine thesis v1              Engine thesis v2
"Generate expert guides"            "Compile guides into          "Prolog → Datalog
 with enforced stage gates"          inference engines"            Five-layer grounding"
         │                                   │                           │
         ▼                                   ▼                           ▼
Meta-prompt v3.25                   BUILD_GUIDE v2                 BUILD_GUIDE v3
"Tighter verification"              "10 modules, Prolog"           "12 modules, provenance"
         │                                                               │
         ▼                                                               ▼
Meta-prompt v3.26                                                  Engine thesis v3
"21 prevention controls                                            "Automated KB bootstrap
 C1–C21, Stage 8"                                                   Source authority"
         │                                                               │
         │                              ┌────────────────────────────────┘
         │                              ▼
         │                       Engine thesis v4 (thesis2_v1.md)
         │                       "The Frankenstein Fix"
         │                       ASPIC+ + Provenance Semirings
         │                       6 formalisms → 2
         │                              │
         ▼                              ▼
Business Expert Guide              anvikshiki_v4/ codebase
(12 chapters, Stage 2 arch)        65 tests → 211 tests (v4 core)
         │                              │
         │                              ├── + Predicate Extraction (67 tests)
         │                              │   "Extract section-level predicates
         │                              │    from guide prose"
         │                              │
         ▼                              ├── + Query Refinement (38 tests)
business_expert.yaml                │   "Say 'I don't know' when
(11 vyāptis, 8 hetvābhāsas)        │    KB doesn't cover the query"
         │                              │
         └──────────────────────────────┘
                                   249 tests passing
                                   0 LLM calls needed for tests
```

The journey: a meta-prompt for generating pedagogical guides → a realization that the guide's architecture IS a knowledge base → a series of increasingly principled engines to compile and reason over that knowledge → honest epistemic humility when the knowledge runs out.

---

*Last updated: 2026-03-04*
