# Ānvīkṣikī Ecosystem — File Registry & History

> A living document tracking every file in the ecosystem: what it contains, when it was created,
> which Claude session produced it, which git commit recorded it, and why it exists.
>
> **Last updated:** 2026-03-08 (Session 8 · `31879926`)

---

## Table of Contents

1. [Session Ledger](#1-session-ledger) — map of every Claude session to its work and commits
2. [File Registry](#2-file-registry) — every file: content summary, git lifecycle, session reference
   - [Engine Package `anvikshiki_v4/`](#21-engine-package-anvikshiki_v4)
   - [Tests `anvikshiki_v4/tests/`](#22-tests-anvikshiki_v4tests)
   - [Knowledge Base Data `anvikshiki_v4/data/`](#23-knowledge-base-data-anvikshiki_v4data)
   - [Theory `theory/`](#24-theory)
   - [Theory History Archive `theory/history/`](#25-theory-history-archive-theoryhist)
   - [Discussions `discussions/`](#26-discussions)
   - [Documentation `docs/`](#27-documentation-docs)
   - [Scripts `scripts/`](#28-scripts)
   - [Guides `guides/`](#29-guides)
   - [Root Files](#210-root-files)
3. [Story of Updates](#3-story-of-updates) — narrative history, philosophy evolution, what/why/when

---

## 1. Session Ledger

Every meaningful Claude session mapped to its topic, commits, and files touched.

| # | Session ID | Date | Label | Key Work | Git Commit(s) |
|---|-----------|------|-------|----------|---------------|
| 1 | `e84e32d4` | Mar 1 | Meta-Prompt Design | Meta-prompt v3.25→v3.26 comparison; agentic system design; Turing completeness discussion; sourcing improvements | pre-git |
| 2 | `2940fe51` | Mar 2 | Engine Concept | Read thesis.md; proposed pure-DSPy engine v1; discussed skill-agent alternative | pre-git |
| 3 | `13aa2739` | Mar 2 | Guide Gen A | Applied meta-prompt v3.26 to non-fiction writing domain | pre-git |
| 4 | `ad79baae` | Mar 2 | BUILD_GUIDE | Read thesis_v2.md; created technical BUILD_GUIDE; first engine implementation attempt | pre-git |
| 5 | `08cfe99f` | Mar 2 | Guide Gen B | Continued guide generation with v3.26 meta-prompt | pre-git |
| 6 | `2afb4792` | Mar 3 | Architecture Overhaul | Critical audit of hand-specified decisions; normalizing flows debate; Frankenstein diagnosis; ASPIC+ discovery; new thesis written (thesis2_v1.md) | pre-git |
| 7 | `2b92b540` | Mar 4 | Implementation + Docs | Predicate extraction design; flowcharts; ELI5 trace; **git init + initial commit**; history archive | `ec70444`, `547de52`, `abfcba9` |
| 8 | `e3e84d62` | Mar 5 | AKL Design | T3/T2/T1 pipeline discussion; Adaptive Knowledge Landscape integration design | `c627180` |
| 9 | `16b48804` | Mar 5 | Guide Gen C | Business expert guide expert treatment; AKL topics; chapter generation | — |
| 10 | `21b283c9` | Mar 5 | Critical Audit Sprint | Full codebase audit; combined architecture critique; branch `feat/t2b-t3a-t3b-architecture` | — |
| 11 | `31879926` | Mar 5–8 | **Full Implementation Sprint** | T2b/T3a/T3b/coverage; ReasoningLM; GLM-5 testing; Gemini testing; Path A fixes; thesis_v3; eli5 sidebar | `74f74ca`, `60a4ac4`, `77522f8`, `67d45c8`, `fd3e609` |
| 12 | `25909790` | Mar 5–8 | Guide Gen Sprint | Business expert guide chapter-by-chapter generation | — |

> **How to read a session ID:** The full UUID identifies the exact transcript. Files are at
> `/Users/mrityunjaybhardwaj/.claude/projects/-Users-mrityunjaybhardwaj-Documents-Anvikshiki/<uuid>.jsonl`

---

## 2. File Registry

### 2.1 Engine Package `anvikshiki_v4/`

---

#### `anvikshiki_v4/__init__.py`
- **What:** Public API surface of the engine package. Re-exports all symbols from submodules into a single importable namespace. Also serves as the authoritative list of what the engine considers stable API.
- **Lines:** 37
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `67d45c8` · 2026-03-08 · Session 11 (`31879926`)
- **Modification history:**
  - `ec70444` — initial set: schema_v4, argumentation, t2_compiler_v4
  - `74f74ca` — added: coverage, kb_augmentation, t2b_compiler, t3a_retriever, engine_factory
  - `60a4ac4` — added: GroundingMode, ReasoningLM
  - `77522f8` — added: AugmentationOrigin, AugmentationMetadata (from schema.py split)
  - `67d45c8` — added: EngineParams, CompilerParams, SynthesisParams, GroundingParams

---

#### `anvikshiki_v4/schema_v4.py`
- **What:** Core data structures for the ASPIC+ argumentation engine. Defines `ProvenanceTag` (Subjective Logic opinion + product lattice metadata, with `tensor(⊗)` and `oplus(⊕)` operations), `PramanaType` (Nyāya epistemic source hierarchy), `RuleType`, `EpistemicStatus`, `Label`, `Argument`, `Attack`. The mathematical heart of the system.
- **Lines:** 275
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `67d45c8` · 2026-03-08 · Session 11 (`31879926`)
- **Modification history:**
  - `ec70444` — initial definition of all types; tensor/oplus operations
  - `77522f8` — corrected "semiring" claim to "commutative monoid pair"; `epistemic_status()` WARNING added; SL distributivity failure documented (Jøsang 2016 §3.6)
  - `67d45c8` — full product lattice axioms in ProvenanceTag docstring; tensor/oplus docstrings formalized as meet(∧)=min / join(∨)=max; derivation_depth exception (+/min vs min/max) documented

---

#### `anvikshiki_v4/schema.py`
- **What:** KB-level data structures separate from argumentation. Defines `KnowledgeStore`, `Vyapti` (rules), `Hetvabhasa` (fallacy detectors), `EpistemicStatus` as used by the KB (distinct from argumentation `EpistemicStatus`), `AugmentationOrigin`, `AugmentationMetadata`. The interface between YAML knowledge bases and the compiler.
- **Lines:** 192
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `77522f8` · 2026-03-06 · Session 11 (`31879926`)
- **Modification history:**
  - `ec70444` — initial: KnowledgeStore, Vyapti, Hetvabhasa
  - `77522f8` — AugmentationOrigin, AugmentationMetadata added to support T2b fine-grained extraction; KBEpistemicStatus renamed to avoid collision with argumentation EpistemicStatus

---

#### `anvikshiki_v4/argumentation.py`
- **What:** The argumentation framework engine. Computes ASPIC+ grounded/preferred/stable semantics over a set of Arguments and Attacks. Implements the defeat relation (strict rules override defeasible; tag strength as tiebreaker). `ArgumentationFramework.compute_grounded()` is the hot path — polynomial fixpoint computation.
- **Lines:** 490
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `77522f8` · 2026-03-06 · Session 11 (`31879926`)
- **Modification history:**
  - `ec70444` — initial: grounded + preferred + stable semantics
  - `77522f8` — fixed ghost argument cleanup; hardened defeat relation for strict rules; removed dead code paths

---

#### `anvikshiki_v4/t2_compiler_v4.py`
- **What:** T2 compiler — translates a KnowledgeStore + grounded query facts into an ArgumentationFramework. Three sub-steps: (a) premise arguments from query facts, (b) forward-chaining through vyaptis, (c) attack derivation (undermining/undercutting/rebutting mapped to Nyāya fallacies). Uses semi-naive evaluation for polynomial termination.
- **Lines:** 401
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `67d45c8` · 2026-03-08 · Session 11 (`31879926`)
- **Modification history:**
  - `ec70444` — initial: BELIEF_MAP, decay constants, forward-chaining logic
  - `77522f8` — fixed decay formula (was incorrect log); hardened scope exclusion logic
  - `67d45c8` — all magic numbers (BELIEF_MAP, DECAY_HALF_LIFE_DAYS, etc.) removed to `engine_params.py`; `0.693` replaced with `math.log(2)` via `params.LN2`; `params: CompilerParams` argument added to all functions

---

#### `anvikshiki_v4/engine_v4.py`
- **What:** The main engine orchestrator. `AnvikshikiEngineV4` is a DSPy module with `forward()` and `forward_with_coverage()`. Wires together: grounding → T2 compilation → contestation → T3a retrieval → synthesis. Uses `dspy.Refine` for synthesis with a reward function. The primary query-answering entry point.
- **Lines:** 480
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `67d45c8` · 2026-03-08 · Session 11 (`31879926`)
- **Modification history:**
  - `ec70444` — initial: three-mode contestation (vada/jalpa/vitanda), synthesis via Refine
  - `74f74ca` — added `forward_with_coverage()` integrating T2b/T3a/coverage pipeline
  - `67d45c8` — **Fix 1**: `contestation_mode` parameter removed entirely; jalpa/vitanda branching deleted; always uses vāda (grounded semantics); synthesis reward function now accepts `SynthesisParams`

---

#### `anvikshiki_v4/engine_params.py`
- **What:** Centralized parameter dataclasses for the entire engine. `CompilerParams` (BELIEF_MAP, decay, combo limits, fixpoint max), `SynthesisParams` (Refine config, reward weights), `GroundingParams` (ensemble size, temperature, thresholds), `EngineParams` (combines all three). `DEFAULT_PARAMS` singleton used throughout. **Replaces 35+ scattered magic numbers.**
- **Lines:** 113
- **Created:** `67d45c8` · 2026-03-08 · Session 11 (`31879926`)
- **Last modified:** `67d45c8` · 2026-03-08 (same commit as creation)

---

#### `anvikshiki_v4/engine_factory.py`
- **What:** Factory function `initialize_engine()` that wires the full compile-time pipeline: load KnowledgeStore → T2b augmentation → T3 compilation → T3a embedding index → engine instantiation. `load_guide_dir()` reads all markdown chapters from a directory. Returns a `CompileArtifacts` dataclass with all compiled components.
- **Lines:** 199
- **Created:** `74f74ca` · 2026-03-05 · Session 11 (`31879926`)
- **Last modified:** `67d45c8` · 2026-03-08 · Session 11 (`31879926`)
- **Modification history:**
  - `74f74ca` — initial: full pipeline wiring
  - `67d45c8` — removed `contestation_mode` parameter (Fix 1)

---

#### `anvikshiki_v4/contestation.py`
- **What:** `ContestationManager` implementing three Nyāya debate protocols. `vada()` (honest inquiry) runs grounded semantics — the only live path. `jalpa()` (preferred, NP-hard) and `vitanda()` (stable, coNP-hard) exist for offline/research use only. Returns `VadaResult` with open questions and suggested evidence gaps.
- **Lines:** 218
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `67d45c8` · 2026-03-08 · Session 11 (`31879926`)
- **Modification history:**
  - `ec70444` — initial: three modes all wired to engine hot path
  - `67d45c8` — jalpa/vitanda demoted to offline; docstrings clarify NP/coNP complexity cost

---

#### `anvikshiki_v4/grounding.py`
- **What:** Five-layer grounding defense: Layer 1 (ontology-constrained prompt), Layer 3 (N-ensemble with temperature), Layer 4 (round-trip verification), Layer 5 (solver-feedback refinement). `GroundingMode` enum (MINIMAL/PARTIAL/FULL) controls how many layers run. Translates natural language queries into verified Datalog predicates.
- **Lines:** 356
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `60a4ac4` · 2026-03-06 · Session 11 (`31879926`)
- **Modification history:**
  - `ec70444` — initial: full 5-layer defense only
  - `60a4ac4` — `GroundingMode` enum added; MINIMAL (1 call), PARTIAL (N=3), FULL (N=5+round-trip+solver) routing

---

#### `anvikshiki_v4/datalog_engine.py`
- **What:** Custom Python Datalog engine supporting semi-naive evaluation. Two modes: `boolean_mode=True` (Phase 2: classical Datalog, facts derived or not) and `boolean_mode=False` (Phase 3+: Heyting-valued epistemic qualification). Implements fixpoint iteration with delta tracking for O(rules × Δfacts) per iteration.
- **Lines:** 368
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `ec70444` (unchanged since initial commit)

---

#### `anvikshiki_v4/uncertainty.py`
- **What:** Three-way uncertainty decomposition from a ProvenanceTag. Produces a structured dict with `epistemic` (belief/uncertainty/status), `aleatoric` (disbelief/domain disagreement), and `inference` (grounding confidence, decay, derivation depth) components, plus `total_confidence` (tag.strength). Epistemic status is passed in from the argumentation layer — not recomputed here.
- **Lines:** 54
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `67d45c8` · 2026-03-08 · Session 11 (`31879926`)
- **Modification history:**
  - `ec70444` — initial: full decomposition with threshold commentary in docstring
  - `67d45c8` — threshold commentary removed from docstring (thresholds live in schema_v4.py); docstring clarified that epistemic_status is passed in

---

#### `anvikshiki_v4/t2b_compiler.py`
- **What:** T2b compiler — compile-time fine-grained KB extraction from guide prose. Wraps PredicateExtractionPipeline (Stages A–E) to produce augmented KnowledgeStore with fine-grained vyaptis tagged with `AugmentationOrigin.T2B`. Also produces synonym table for semantic coverage matching.
- **Lines:** 204
- **Created:** `74f74ca` · 2026-03-05 · Session 11 (`31879926`)
- **Last modified:** `74f74ca` (unchanged since introduction)

---

#### `anvikshiki_v4/t3a_retriever.py`
- **What:** T3a retriever — embedding-based prose retrieval over guide text chunks. Uses `dspy.retrievers.Embeddings` (FAISS-backed). `retrieve_for_predicates()` boosts chunks from sections referenced by activated vyaptis (T2b cross-linking). Returns ranked `TextChunk` list.
- **Lines:** 183
- **Created:** `74f74ca` · 2026-03-05 · Session 11 (`31879926`)
- **Last modified:** `74f74ca` (unchanged since introduction)

---

#### `anvikshiki_v4/t3_compiler.py`
- **What:** T3 compiler — splits guide prose markdown into `TextChunk` objects with heading-based boundaries and chapter metadata. The input stage for T3a embedding indexing. Produces the corpus that T3a retrieves from at query time.
- **Lines:** 260
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `ec70444` (unchanged since initial commit)

---

#### `anvikshiki_v4/coverage.py`
- **What:** Semantic coverage analyzer. Three-layer predicate matching: (1) exact match against KB vocabulary, (2) synonym lookup via T2b synonym table, (3) semantic gap detection for predicates that decline against both. Returns `CoverageResult` with covered/partially-covered/declined predicate sets.
- **Lines:** 185
- **Created:** `74f74ca` · 2026-03-05 · Session 11 (`31879926`)
- **Last modified:** `74f74ca` (unchanged since introduction)

---

#### `anvikshiki_v4/kb_augmentation.py`
- **What:** Adaptive Knowledge Landscape (AKL) — T3b query-time augmentation. When a query declines against the KB, generates HYPOTHESIS vyaptis by projecting the query onto the domain's framework axes using existing vyaptis as conceptual templates. `AugmentationPipeline` is the entry point; returns `AugmentationResult` with new predicates and vyaptis.
- **Lines:** 443
- **Created:** `74f74ca` · 2026-03-05 · Session 11 (`31879926`)
- **Last modified:** `74f74ca` (unchanged since introduction)

---

#### `anvikshiki_v4/predicate_extraction.py`
- **What:** Five-stage predicate extraction pipeline (Stages A–E). Stage A: text chunking. Stage B: concept extraction. Stage C: relationship mapping. Stage D: vyapti construction. Stage E: validation and deduplication. The largest single file in the engine (1123 lines). Powers both T2b (compile-time) and interactive extraction.
- **Lines:** 1123
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `ec70444` (unchanged since initial commit)

---

#### `anvikshiki_v4/query_refinement.py`
- **What:** Multi-turn query refinement pipeline. When initial grounding fails or produces low-confidence predicates, iteratively refines the query via DSPy modules. Includes clarification generation, predicate re-extraction, and confidence-gated stopping.
- **Lines:** 406
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `ec70444` (unchanged since initial commit)

---

#### `anvikshiki_v4/reasoning_lm.py`
- **What:** `ReasoningLM` — DSPy LM wrapper for reasoning models (GLM-5, DeepSeek-R1). Strips `response_format=json_object` flag that causes reasoning models to route JSON to `reasoning_content` instead of `content`. Transparent wrapper: all other LM calls pass through unchanged.
- **Lines:** 52
- **Created:** `60a4ac4` · 2026-03-06 · Session 11 (`31879926`)
- **Last modified:** `60a4ac4` (unchanged since introduction)

---

#### `anvikshiki_v4/optimize.py`
- **What:** DSPy optimizer configuration stubs. MIPROv2, SIMBA, and GEPA optimizer setup for future parameter tuning. Currently unused in the live pipeline — the `engine_params.py` defaults are manually chosen. Placeholder for when calibration data exists.
- **Lines:** 72
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `ec70444` (unchanged since initial commit)

---

#### `anvikshiki_v4/extraction_schema.py`
- **What:** Pydantic schemas for the predicate extraction pipeline's structured outputs. Defines `ExtractedConcept`, `ExtractedRelationship`, `ExtractedVyapti`, `ExtractionResult`. Used by `predicate_extraction.py` for grammar-constrained decoding via `dspy.JSONAdapter`.
- **Lines:** 201
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `ec70444` (unchanged since initial commit)

---

#### `anvikshiki_v4/extraction_eval.py`
- **What:** Evaluation harness for the predicate extraction pipeline. Loads fixture predicates, runs extraction, computes precision/recall/F1 against expected outputs. Used for benchmarking extraction quality before KB integration.
- **Lines:** 365
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `ec70444` (unchanged since initial commit)

---

#### `anvikshiki_v4/extraction_hitl.py`
- **What:** Human-in-the-loop extraction interface. Interactive CLI for reviewing and correcting extracted predicates before committing them to the KB. Supports accept/reject/edit per predicate with diff display.
- **Lines:** 368
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `ec70444` (unchanged since initial commit)

---

### 2.2 Tests `anvikshiki_v4/tests/`

| File | Lines | What it tests | Created | Last modified |
|------|-------|--------------|---------|---------------|
| `test_schema_v4.py` | 130 | ProvenanceTag tensor/oplus invariants; b+d+u=1; lattice axioms | `ec70444` | `77522f8` |
| `test_argumentation.py` | 155 | Grounded/preferred/stable semantics; defeat relation; cycle handling | `ec70444` | `77522f8` |
| `test_contestation.py` | 96 | VadaResult structure; open_question detection | `ec70444` | `ec70444` |
| `test_t2_compiler_v4.py` | 78 | Premise argument creation; forward-chaining; attack derivation | `ec70444` | `ec70444` |
| `test_uncertainty.py` | 39 | Three-way decomposition output structure | `ec70444` | `ec70444` |
| `test_engine_v4.py` | 44 | Basic engine forward pass (unit) | `ec70444` | `ec70444` |
| `test_engine_v4_l3.py` | 846 | Full pipeline integration L3 tests; forward_with_coverage; synthesis | `ec70444` | `67d45c8` |
| `test_business_expert.py` | 512 | business_expert.yaml KB full evaluation; real vyaptis + hetvabhasas | `ec70444` | `77522f8` |
| `test_predicate_extraction.py` | 695 | Stages A–E extraction pipeline; fixture-based quality checks | `ec70444` | `ec70444` |
| `test_query_refinement.py` | 518 | Multi-turn refinement; stopping conditions | `ec70444` | `ec70444` |
| `test_fixes.py` | 470 | Regression tests for audit-fix round (schema corrections, dead code) | `ec70444` | `77522f8` |
| `test_audit_fixes.py` | 314 | Post-audit invariant checks (b+d+u, strict rule immunity, etc.) | `77522f8` | `77522f8` |

> **Total tests:** 263 passing, 4 skipped as of 2026-03-08.
> `test_engine_v4_l3.py` had 3 classes removed in `67d45c8`: `TestFullPipelineJalpa`, `TestFullPipelineVitanda`, `TestCrossModeConsistency` — these tested behavior that never actually existed.

---

### 2.3 Knowledge Base Data `anvikshiki_v4/data/`

---

#### `anvikshiki_v4/data/business_expert.yaml`
- **What:** The primary knowledge base. 11 vyaptis (inference rules) covering business strategy — unit economics, market dynamics, growth constraints, value creation, organizational limits. 8 hetvabhasa detectors. Each vyapti has pramana type, trust scores, scope conditions, and academic citations (Harvard Business School, Goldratt, Christensen, Dunbar, Ries 2011).
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `ec70444` (unchanged since initial commit)

---

#### `anvikshiki_v4/data/sample_architecture.yaml`
- **What:** Template/example YAML showing the full KB schema structure for a software architecture domain. Used as a reference for building new domain KBs.
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `ec70444` (unchanged since initial commit)

---

#### `anvikshiki_v4/data/business_expert_query_trace.md`
- **What:** Trace artifact — query-by-query trace output from running the business expert KB against test queries. Shows predicate extraction, argumentation graph, and synthesis output per query.
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `ec70444` (trace artifact, not updated programmatically)

---

#### `anvikshiki_v4/data/business_expert_trace.md`
- **What:** Trace artifact — full pipeline trace for the business expert domain. Earlier format than `query_trace.md`. Shows KB loading, vyapti compilation, and first-pass grounding.
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `ec70444` (trace artifact)

---

#### `anvikshiki_v4/data/practical_useage.md` ⚠️
- **What:** Usage guide — code examples for instantiating the engine, running queries, interpreting results. Should live in `docs/` not `data/`. Filename has a typo ("useage" → "usage").
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `67d45c8` · 2026-03-08 — removed `contestation_mode` example
- **Note:** Candidate for relocation to `docs/usage.md`

---

### 2.4 Theory

---

#### `theory/thesis2_v1.md` ← **Canonical current thesis**
- **What:** The primary architecture thesis. Proposes replacing the Frankenstein multi-formalism architecture with ASPIC+ structured argumentation + Subjective Logic annotation using Nyāya epistemology as the design ontology. Shows: (1) Nyāya maps naturally to argumentation; (2) SL + product lattice replaces all ad-hoc quantification; (3) sheaf, Heyting lattice, trust tables, keyword fallacy detection all eliminated; (4) Datalog computes grounded semantics in polynomial time. Satisfies all 8 Contestable AI properties (Moreira et al. 2025).
- **Created:** `77522f8` · 2026-03-06 · Session 11 (`31879926`) — committed, but written in Session 6 (`2afb4792`)
- **Last modified:** `77522f8` (unchanged since commit)
- **Predecessor:** `theory/history/thesis/thesis_v3.md` (architecture gen 3, different system)

---

#### `theory/thesis_v3.md` ← **Structural revision of thesis2_v1** ⚠️ naming issue
- **What:** Document revision 3 of thesis2_v1 — NOT a third-generation architecture (see naming note). Addresses three expert reviewer critiques: (1) §2.1 Quick Reference table at point of first Nyāya concept introduction; (2) §6.1 fully worked unit economics inference chain; (3) §9.4 complete T3 retrieval mechanics (epistemic inheritance, Savyabhicāra routing, Satpratipakṣa routing). Appendix A contains the ELI5 progressive disclosure sidebar.
- **Lines:** ~614
- **Created:** `fd3e609` · 2026-03-08 · Session 11 (`31879926`)
- **Last modified:** `fd3e609` (same commit as creation)
- **⚠️ Naming conflict:** `theory/history/thesis/thesis_v3.md` is a completely different document (architecture generation 3, lattice-Datalog system). This file should be renamed `thesis_v4_r3.md` or the convention should be established as `theory/thesis.md` = canonical current.

---

#### `theory/BUILD_GUIDE.md`
- **What:** Complete implementation manual for the engine. Covers all DSPy 3.1.x API changes (dspy.Refine replacing Assert/Suggest, LM config, structured output), all module implementations, test strategy, optimizer usage. Written to enable a fresh implementation from the thesis alone.
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`) — based on research from Session 4 (`ad79baae`)
- **Last modified:** `ec70444` (unchanged since initial commit)

---

#### `theory/ecosystem_evolution.md`
- **What:** Narrative evolution log — "how a meta-prompt for generating expert guides became a neurosymbolic reasoning engine." Chronicles the philosophical decisions: why Nyāya, why ASPIC+ over sheaves, why Datalog over Prolog, why vāda over jalpa/vitanda. The "why" companion to BUILD_GUIDE's "how."
- **Created:** `abfcba9` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `abfcba9` (unchanged since introduction)

---

### 2.5 Theory History Archive `theory/history/`

The archive captures the architecture's earlier generations. All files added in a single archiving commit `abfcba9` (Mar 4) by Session 7 (`2b92b540`).

#### `theory/history/thesis/`

| File | What | Architecture Gen |
|------|------|-----------------|
| `thesis_v1.md` | Original engine thesis — Prolog-based, Heyting lattice, sheaf | Gen 1 |
| `thesis_v2.md` | Revised thesis — Prolog→Datalog, five-layer grounding, semi-naive eval | Gen 2 |
| `thesis_v2_patch.md` | Incremental patches to v2 before full v3 rewrite | Gen 2 patch |
| `thesis_v3.md` | Gen 3 thesis — lattice-Datalog + normalizing flows (pre-ASPIC+ pivot) | Gen 3 |

> **Critical note:** These version numbers (v1, v2, v3) refer to architecture generations, not document revisions. They are fully superseded by `theory/thesis2_v1.md` and `theory/thesis_v3.md` which describe the current ASPIC+ system.

#### `theory/history/build_guides/`

| File | What |
|------|------|
| `BUILD_GUIDE_v2.md` | Build guide for Gen 2 (Datalog) engine |
| `BUILD_GUIDE_v3.md` | Build guide for Gen 3 (lattice-Datalog) engine |
| `BUILD_GUIDE_v4.md` | Build guide for Gen 4 pre-pivot (DSPy + egglog) |
| `BUILD_V4_PROMPT.md` | The exact prompt used to generate BUILD_GUIDE_v4 |

#### `theory/history/meta_prompts/`

| File | What |
|------|------|
| `meta_prompt_v3.2.md` | Meta-prompt v3.2 — 7 stages, basic sourcing |
| `meta_prompt_v3.25.md` | Meta-prompt v3.25 — added epistemic status on vyāptis |
| `meta_prompt_v3.26.md` | Meta-prompt v3.26 — 8 stages, Stage 8 Safety Net, voice calibration |
| `anvikshiki_meta2_design_doc.md` | Design document for the second meta-prompt generation |
| `anvikshiki_meta2_prompt.md` | Second-generation meta-prompt |
| `anvikshiki_meta2_prompt_v3_26.md` | v3.26 applied to meta2 framework |

#### `theory/history/discussions/`

| File | What | Session |
|------|------|---------|
| `adaptive-knowledge-landscape.md` | Original AKL design — graph-structured KB with dynamic node creation | `e3e84d62` |
| `build_spec_adaptive_knowledge_landscape_v1.md` | Build spec for AKL v1 | `e3e84d62` |
| `agentic-systems-for-guide-creation.md` | Agent team design (Orchestrator, Analyst, Architect, Verifier) | `e84e32d4` |
| `critical-analysis-v4-post-fix-round.md` | Critical analysis of the engine after first fix round | `21b283c9` |
| `improving-meta-prompt-for-concrete-sourcing.md` | Discussion on 6-class provenance classification | `e84e32d4` |
| `is-anvikshiki-turing-complete.md` | Formal analysis of Turing completeness; why Datalog's limits are features | `e84e32d4` |
| `knowledge-bank-and-agent-council.md` | Two-layer knowledge bank design + online agent council proposal | `e84e32d4` |
| `v3-25-vs-v3-26-comparison.md` | Side-by-side comparison of meta-prompt versions | `16b48804` |

---

### 2.6 Discussions

Active design documents for the current (v4/ASPIC+) system. All created in Session 11 (`31879926`) unless noted.

---

#### `discussions/critical-audit-v4-implementation.md`
- **What:** Full line-by-line audit of all anvikshiki_v4 modules post-implementation. Documents 35+ magic numbers, dead code, unsupported claims ("semiring" for SL), false API documentation (contestation_mode claiming to switch semantics). The document that triggered Path A fixes.
- **Created:** `77522f8` · 2026-03-06 · Session 11 (`31879926`)

---

#### `discussions/ideal-architecture-properties.md`
- **What:** Defines 8 design properties (P1–P8) the engine should satisfy: polynomial termination, epistemic traceability, defeat monotonicity, contestable AI compliance, etc. Written after the audit to define the target before choosing fixes.
- **Created:** `77522f8` · 2026-03-06 · Session 11 (`31879926`)

---

#### `discussions/proving-architecture-optimality.md`
- **What:** Survey of 15+ existing argumentation engines (Tweety, Carneades, ASPIC-END, etc.). Proves that the Ānvīkṣikī direction (ASPIC+ + SL + Datalog) satisfies P1–P8 better than any single alternative. The theoretical justification for not adopting an off-the-shelf engine.
- **Created:** `77522f8` · 2026-03-06 · Session 11 (`31879926`)

---

#### `discussions/implementation-trace-t2b-t3a-t3b-coverage.md`
- **What:** Detailed implementation trace of the T2b/T3a/T3b/coverage pipeline addition. Records decisions made during `74f74ca` — why T2b runs at compile-time, why T3a uses FAISS, why coverage uses three layers, why AKL (T3b) is query-time.
- **Created:** `74f74ca` · 2026-03-05 · Session 11 (`31879926`)

---

#### `discussions/towards-categorical-uq-with-conformal-predictions.md`
- **What:** Design document for Fix 2 (deferred). Proposes replacing threshold-based `epistemic_status()` (5 magic floats in schema_v4.py) with a GBT classifier + RAPS conformal prediction wrapper. Would give calibrated coverage guarantees on epistemic status classification. Implementation not yet started.
- **Created:** `67d45c8` · 2026-03-08 · Session 11 (`31879926`)

---

### 2.7 Documentation `docs/`

---

#### `docs/eli5_trace.md` ← **Primary user-facing explanation**
- **What:** Plain-English walkthrough of the entire pipeline using the business strategy example. Every stage (0–9+): What it does, Why it exists, How it works, Source code reference. Based on a real test run (Llama-3.2-3B). The canonical document for understanding the system end-to-end without reading code.
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `fd3e609` · 2026-03-08 · Session 11 (`31879926`)
- **Modification history:**
  - `ec70444` — initial: Stages 0–7 covering the lightweight grounding path
  - `fd3e609` — Stage 4 progressive disclosure sidebar added: formal ASPIC+ argument objects + tag ⊗ arithmetic + undercutting attack (addressing reviewer critique 2)

---

#### `docs/eli5_trace_e2e.md`
- **What:** Extended ELI5 trace covering the full N=5 ensemble grounding path (Path C). Companion to `eli5_trace.md` which covers Path B (lightweight). Shows the additional layers 3–5 with actual model call traces.
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `ec70444` (unchanged since initial commit)

---

#### `docs/predicate_extraction_design.md`
- **What:** Design document for the automated predicate extraction pipeline. Research-backed design decisions: why 5 stages, why HITL validation, which DSPy modules to use, expected precision/recall targets.
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`) — produced in Session 7 (`2b92b540`)
- **Last modified:** `ec70444` (unchanged since initial commit)

---

#### `docs/predicate_extraction_theory.md`
- **What:** Adjacent theory paper — "Predicate Extraction for the Ānvīkṣikī Engine." Academic-style treatment of the extraction problem: related work (OpenIE, FrameNet, AMR), theoretical framing, design decision justifications with citations.
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`)
- **Last modified:** `ec70444` (unchanged since initial commit)

---

#### `docs/pipeline_flowchart_llama3.2.md`
- **What:** Full end-to-end pipeline flowchart for the Llama-3.2-3B path (Path B: lightweight grounding). Shows every function call, data transformation, and output at each stage. The "how does data flow" document.
- **Created:** `ec70444` · 2026-03-04 · Session 7 (`2b92b540`) — produced in Session 7
- **Last modified:** `ec70444` (unchanged)

---

#### `docs/pipeline_flowchart_llama3.2md.md` ⚠️
- **What:** Duplicate or near-duplicate of `pipeline_flowchart_llama3.2.md`. Filename has `.md` appearing twice — likely a naming accident. Content may be identical or slightly variant.
- **Created:** `ec70444` · 2026-03-04
- **Note:** Candidate for deletion after diff verification.

---

#### `docs/pipeline_flowchart_coverage_routing.md`
- **What:** Updated pipeline flowchart showing the full T2b/T3a/T3b/coverage routing logic. Extension of `pipeline_flowchart_llama3.2.md` to include the compile-time augmentation path and query-time AKL fallback.
- **Created:** `74f74ca` · 2026-03-05 · Session 11 (`31879926`)
- **Last modified:** `74f74ca` (unchanged since introduction)

---

#### `docs/e2e_pipeline_trace_2026-03-06.md`
- **What:** Dated e2e run trace artifact — full input/processing/output trace from a specific pipeline run on 2026-03-06. Includes raw model outputs. A snapshot, not a maintained document.
- **Created:** `60a4ac4` · 2026-03-06 · Session 11 (`31879926`)

---

#### `docs/run_trace_gemini_full_2026-03-05.md`
- **What:** Full Gemini 2.5 Pro run trace from 2026-03-05. Dated artifact showing the pipeline with a large API model.
- **Created:** `74f74ca` · 2026-03-05 · Session 11 (`31879926`)

---

#### `docs/run_trace_gemini_2.5_pro_2026-03-05.txt` ⚠️
- **What:** Raw `.txt` run output from Gemini 2.5 Pro test. Not markdown — a raw terminal capture. Artifact.
- **Created:** `74f74ca` · 2026-03-05 · Session 11 (`31879926`)
- **Note:** Should be in `traces/` not `docs/`

---

### 2.8 Scripts

---

#### `scripts/e2e_trace_gemini.py`
- **What:** The canonical end-to-end trace script. Runs three scenarios (in-domain, partial/decline, out-of-domain) through the full pipeline using Gemini as the LM. Produces formatted markdown trace output. The go-to script for verifying pipeline behavior end-to-end.
- **Created:** `74f74ca` · 2026-03-05 (first version) → `60a4ac4` · 2026-03-06 (updated for 3-mode grounding)
- **Last modified:** `60a4ac4` · 2026-03-06 · Session 11 (`31879926`)

---

#### `scripts/e2e_trace_coverage_pipeline.py`
- **What:** E2e trace script focused on coverage routing — exercises the T2b/T3a/coverage/AKL path specifically. Shows how queries that partially or fully decline against the KB get handled.
- **Created:** `74f74ca` · 2026-03-05 · Session 11 (`31879926`)
- **Last modified:** `74f74ca` (unchanged since introduction)

---

#### `scripts/trace_calltree.py`
- **What:** Diagnostic script — instruments the engine to capture a full call tree trace (every function call, args, return values). Produces `traces/calltree_trace.txt` (21MB). One-off diagnostic, not a maintained script.
- **Created:** `60a4ac4` · 2026-03-06 · Session 11 (`31879926`)

---

#### `scripts/trace_glm5_grounding.py`
- **What:** GLM-5 specific grounding trace script. Isolates just the grounding layer (Layer 1–5) with GLM-5 as the LM. Produced `traces/glm5_grounding_trace.txt`. One-off diagnostic for reasoning model compatibility testing.
- **Created:** `60a4ac4` · 2026-03-06 · Session 11 (`31879926`)

---

#### `scripts/test_glm5.py`
- **What:** Quick test script for GLM-5 integration. Verifies the ReasoningLM wrapper, JSON routing, and basic engine forward pass. One-off compatibility test.
- **Created:** `60a4ac4` · 2026-03-06 · Session 11 (`31879926`)

---

#### `scripts/test_glm5_discrepancy.py`
- **What:** Discrepancy investigation script — isolates specific behaviors where GLM-5 output differed from expected. One-off diagnostic.
- **Created:** `60a4ac4` · 2026-03-06 · Session 11 (`31879926`)

---

### 2.9 Guides

The `business_expert` guide is the primary worked example of the full guide-generation pipeline. Generated using meta-prompt v3.26 applied to business strategy domain.

| File | What | Session |
|------|------|---------|
| `stage1.md` | Stage 1 output: domain scoping, audience definition, learning objectives | `16b48804` / `25909790` |
| `stage2_part1_vyaptis.md` | Stage 2 Part 1: the 11 inference rules (vyāptis) with sources | `16b48804` / `25909790` |
| `stage2_part2_hetvabhasas.md` | Stage 2 Part 2: 8 fallacy detectors (hetvābhāsas) | `16b48804` / `25909790` |
| `stage2_part3_architecture.md` | Stage 2 Part 3: knowledge architecture (KB schema, rule relationships) | `16b48804` / `25909790` |
| `stage2_part4_registries.md` | Stage 2 Part 4: source registry, expert registry, concept registry | `16b48804` / `25909790` |
| `stage3_reference_bank.md` | Stage 3: full reference bank with academic citations and abstracts | `16b48804` / `25909790` |
| `guide_opening_ch1.md` | Guide Chapter 1: opening narrative + framing | `25909790` |
| `guide_ch2.md` | Guide Chapter 2: unit economics foundations | `25909790` |
| `guide_ch3_ch4.md` | Guide Chapters 3–4: market dynamics + growth constraints | `25909790` |
| `guide_ch5_ch6.md` | Guide Chapters 5–6: value creation + organizational limits | `25909790` |
| `guide_ch7_ch8.md` | Guide Chapters 7–8: competitive dynamics + disruption | `25909790` |
| `guide_ch9_ch10.md` | Guide Chapters 9–10: synthesis + frameworks | `25909790` |
| `guide_ch11_ch12.md` | Guide Chapters 11–12: advanced applications + closing | `25909790` |
| `business_expert_v3.2_pure_prompt.md` | The raw v3.2 meta-prompt application (pre-v3.26 version of the guide) | `2b92b540` |

---

### 2.10 Root Files

---

#### `README.md`
- **What:** Project overview, quick-start, architecture diagram, and code examples for instantiating and querying the engine.
- **Created:** `ec70444` · 2026-03-04
- **Last modified:** `67d45c8` · 2026-03-08 — removed `contestation_mode` from example

---

#### `pyproject.toml`
- **What:** Package metadata and dependencies. DSPy 3.1.x, NetworkX, NumPy, FAISS, egglog-python.
- **Created:** `ec70444` · 2026-03-04
- **Last modified:** `ec70444` (unchanged)

---

#### `run_pipeline_e2e.py` ⚠️
- **What:** Standalone e2e pipeline runner at repo root. Loads business_expert.yaml, runs a test query, prints full output. Should logically live in `scripts/`.
- **Created:** `c627180` · 2026-03-05 · Session 8 (`e3e84d62`)
- **Last modified:** `67d45c8` · 2026-03-08 — `contestation_mode` reference updated to `semantics: grounded`

---

#### `.gitignore`
- **What:** Ignores Python artifacts (`__pycache__`, `.pyc`, `.egg-info`), virtual environments, IDE files, OS files, `.env`, test caches, and `.db` files. Does **not** currently ignore `traces/`.
- **Created:** `ec70444` · 2026-03-04
- **Last modified:** `ec70444` (unchanged — `traces/` should be added)

---

#### `GLOSSARY.md` ← this file
- **What:** This document.
- **Created:** Session 11 (`31879926`) · 2026-03-08

---

## 3. Story of Updates

The narrative history — why decisions were made, what changed, and what the evolution reveals about the project's philosophy.

---

### Chapter 1: The Meta-Prompt Era (Mar 1–2) — Sessions 1–5

The project began as an instructional design problem. The question: can you build a meta-prompt systematic enough to produce expert-quality learning guides? Session 1 (`e84e32d4`) examined meta-prompt v3.25 vs v3.26 and immediately ran into deeper questions:

- **Turing completeness:** "Is Anvikshiki Turing complete?" — the discussion revealed that the vyāpti/hetvābhāsa system was essentially a logic program. If guides compile to logic rules, can they power a reasoning engine? This single question seeded the entire engine.
- **Agentic systems:** The guide generation process was too slow for a single model. An agent team was designed (Orchestrator, Analyst, Architect, Verifier) that would apply each meta-prompt stage in parallel.
- **Sourcing quality:** The meta-prompt was generating unsourced claims. The session added a 6-class provenance classification system and the Stage 8 Safety Net to catch pre-publication epistemic failures.

Sessions 2–5 (`2940fe51`, `13aa2739`, `ad79baae`, `08cfe99f`) explored what building the engine actually required. Session 4 (`ad79baae`) produced `BUILD_GUIDE.md` — a complete implementation manual based on the early thesis (Prolog-based, Heyting lattice, sheaf consistency). At this stage the system was Gen 1/Gen 2: theoretically sound, practically complex.

**Philosophy:** The meta-prompt is the *interface* for experts to encode their knowledge. The engine is the *runtime* that makes that knowledge queryable. The guide is both human-readable artifact and machine-readable knowledge source.

---

### Chapter 2: The Frankenstein Diagnosis (Mar 3) — Session 6

Session 6 (`2afb4792`, 18MB, the largest early session) was the intellectual pivot of the project.

The user asked: "list all decisions in the thesis that are hand-specified, analyse critically." The audit revealed that the Gen 3 system had accumulated six independent formalisms patched together:
1. Heyting lattice for epistemic status
2. Cellular sheaf for consistency
3. Hand-specified trust tables for source authority
4. Keyword-based hetvābhāsa detection
5. Identity restriction maps
6. Hand-tuned uncertainty thresholds

None of these components spoke to each other. Adding a new pramāṇa type required updating five separate systems. The user's diagnosis: "it looks like a Frankenstein architecture."

The session explored alternatives — normalizing flows, sheaf homology, categorical UQ — before landing on ASPIC+ structured argumentation as the answer. The key realization: **Nyāya's existing theory of inference, testimony, and conflict resolution maps directly onto ASPIC+ concepts**. The philosophy already had the solution. The computational framework just needed to be identified.

The session concluded with writing `thesis2_v1.md` — the ASPIC+ thesis. This document claims: all six formalisms collapse into one coherent framework. The sheaf becomes unnecessary because ASPIC+ defeat relations handle local-global consistency. The Heyting lattice becomes unnecessary because argumentation semantics (IN/OUT/UNDECIDED) handles epistemic status. The trust tables become ProvenanceTag fields. The fallacy detectors become Attack construction rules.

**Philosophy:** Coherent architecture beats composable complexity. A system that fails in one place should fail uniformly, not mysteriously at the intersection of six formalisms.

---

### Chapter 3: Building on Solid Ground (Mar 4) — Session 7

Session 7 (`2b92b540`, 11MB) was the implementation session. With the thesis settled, the work became concrete: build the system, write the documentation, organize the history.

Key decisions made:
- **Predicate extraction pipeline (5 stages A–E):** The hardest unsolved problem — getting from natural language queries to verified Datalog predicates without hallucination. The 5-layer grounding defense was designed here, with ensemble voting (N=5) as the consensus mechanism.
- **ELI5 trace:** The user insisted on a plain-English walkthrough before the formal thesis. The `eli5_trace.md` was written to explain every pipeline stage using the business strategy example — a decision that later directly addressed reviewer critique 2.
- **Git initialization:** The repo was formally initialized. The initial commit (`ec70444`) captured the full engine implementation plus documentation. Three subsequent commits (`547de52`, `abfcba9`) cleaned up artifacts and organized the history archive.

The archiving commit `abfcba9` was philosophically significant — it explicitly moved all pre-ASPIC+ work into `theory/history/`. The message: those architectures were worth preserving (they show how the thinking evolved) but they are superseded.

**Philosophy:** The documentation is as important as the code. A system that cannot be explained to a non-expert doesn't exist — it's just code.

---

### Chapter 4: The Pipeline Expansion (Mar 5) — Sessions 8–10

Sessions 8 (`e3e84d62`) and 10 (`21b283c9`) addressed a gap in the original thesis: the T2 logic engine was detailed, but the T3 retrieval system was handwaved as "builds a NetworkX graph." This became explicit in Session 8: **how does prose retrieval interact with the epistemically-qualified logic output?**

The Adaptive Knowledge Landscape design emerged: when a query declines against the KB, instead of returning nothing, the system should use existing vyāptis as "conceptual axes" to project the query into the domain and generate HYPOTHESIS vyāptis. This was commit `c627180`.

Session 10 (`21b283c9`) ran a full critical audit of the combined architecture: T2b (compile-time fine-grained extraction) + T3a (embedding retrieval) + T3b (query-time AKL augmentation) + coverage routing. The audit identified that these four systems were being conflated — each needed a clear contract.

The implementation sprint in Session 11 (`31879926`, commit `74f74ca`) separated them formally:
- **T2b** = compile-time KB augmentation (runs once, produces augmented KnowledgeStore)
- **T3a** = embedding retrieval (runs at query time, FAISS-backed)
- **T3b** = AKL query-time augmentation (runs only when query declines)
- **Coverage** = three-layer predicate matching (exact → synonym → gap)

**Philosophy:** Compile-time work should stay at compile-time. Query-time work should be as fast as possible. The distinction between offline (T2b) and online (T3a, T3b) components is an architectural invariant, not an implementation detail.

---

### Chapter 5: The Honest Architecture Sprint (Mar 5–8) — Session 11

Session 11 (`31879926`, 26MB) was the longest and most significant session. Four separate phases:

**Phase 1: GLM-5 + Gemini Testing (Mar 5–6)**

The engine was tested with Gemini 2.5 Pro and GLM-5 (a reasoning model). GLM-5 exposed a bug: reasoning models route JSON to `reasoning_content` instead of `content` when `response_format=json_object` is set. The fix was `ReasoningLM` — a transparent wrapper that strips that flag. Commit `60a4ac4`.

The 3-mode grounding (MINIMAL/PARTIAL/FULL) was also added in this commit — recognizing that N=5 ensemble is expensive and unnecessary for high-confidence queries.

**Phase 2: Critical Audit → Honest Fixes (Mar 6)**

The user asked: "check what other fake stuffs we have here?" This triggered the deep audit (`discussions/critical-audit-v4-implementation.md`). Findings:
- `epistemic_status()` had 5 magic floats with a comment claiming they were "DSPy-optimizable" — they weren't
- `contestation_mode` parameter claimed to switch between grounded/preferred/stable semantics — preferred and stable silently timed out and fell back to grounded
- ProvenanceTag docstring called the structure a "semiring" — Jøsang (2016) explicitly shows SL violates distributivity
- 35+ constants scattered across files, none with calibration basis

Commit `77522f8` fixed the honest claims (schema_v4.py corrected, dead code removed, `epistemic_status()` WARNING added). But the structural problems remained.

**Phase 3: Path A Fixes (Mar 8)**

Four architectural fixes in commit `67d45c8`:
- **Fix 1:** Kill jalpa/vitanda illusion — `contestation_mode` parameter removed entirely, always vāda
- **Fix 3:** Centralize parameters — `engine_params.py` created with frozen dataclasses
- **Fix 4:** Axiomatize composition — ProvenanceTag formally documented as product lattice, not semiring
- (Fix 2 deferred — conformal UQ classifier design doc written, implementation pending)

Three test classes deleted: `TestFullPipelineJalpa`, `TestFullPipelineVitanda`, `TestCrossModeConsistency`. These tested behavior that was claimed to exist but never did.

**Phase 4: Reviewer Critique Response (Mar 8)**

The user had shared `discussions/thesis2_v1_expert_reviewer_critiques.md` — a detailed critique from two expert reviewers identifying three structural weaknesses. Commit `fd3e609` addressed all three:
- **Critique 1** (philosophical-computational gap): §2.1 Quick Reference table moved to point of first Nyāya concept introduction
- **Critique 2** (ELI5-thesis gap): §6.1 unit economics worked example + eli5_trace.md Stage 4 formal sidebar
- **Critique 3** (T3 handwave): §9.4 rewritten from 6 lines to full section covering epistemic inheritance, Savyabhicāra routing, Satpratipakṣa routing

**Philosophy of this session:** Honesty as a design constraint. A system that claims to do what it doesn't is harder to fix than a system that honestly documents what it does. The Path A fixes weren't about adding features — they were about removing claims that the code didn't support. The reviewer response was about making the documentation's internal connections as explicit as the code's.

---

### Pending: Fix 2 — Conformal UQ (Not yet implemented)

The one remaining structural issue: `epistemic_status()` in `schema_v4.py:209–218` still uses 5 hand-tuned thresholds. The design doc (`discussions/towards-categorical-uq-with-conformal-predictions.md`) proposes replacing them with a GBT classifier + RAPS conformal wrapper, giving calibrated coverage guarantees.

This is deferred because it requires labeled training data (manually annotated epistemic status labels for a set of ProvenanceTags), which doesn't yet exist. It cannot be implemented correctly without calibration data — and implementing it incorrectly would be dishonest.

**Philosophy:** The right time to implement Fix 2 is when there is data to calibrate it. Not before.

---

### The Naming Problem (Still Open)

`theory/thesis_v3.md` (this session's doc revision of the ASPIC+ thesis) collides with `theory/history/thesis/thesis_v3.md` (architecture generation 3). Both are correctly named by their own logic but create confusion together. The fix is to establish a clear convention:

- `theory/thesis.md` = canonical current (no version number — version tracking is git's job)
- `theory/history/thesis/` = all historical versions, labeled by architecture generation

This rename has not yet happened.

---

*End of GLOSSARY.md — updated 2026-03-08*
