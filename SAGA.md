# The Saga of Ānvīkṣikī

## From a Meta-Prompt Question to a Neurosymbolic Argumentation Engine

---

> *Ānvīkṣikī* (ānvīkṣikī, Sanskrit: आन्वीक्षिकी) — the science of inquiry.
> Used by Kauṭilya in the Arthaśāstra as the first of the four sciences, meaning logical inquiry or formal analysis.
> Chosen as the project name because the system does exactly what the word describes:
> it takes a domain expert's knowledge and makes it formally interrogable.

---

## Prologue: The Question That Started Everything

It began not with code, but with a question about a meta-prompt.

March 1, 2026. Session 1 (`e84e32d4`). The question under examination was whether a structured meta-prompt — a systematic recipe for generating expert-quality learning guides — could be improved from version 3.25 to 3.26. Standard document work. But in the middle of analyzing the meta-prompt's eight stages, a different question surfaced:

**"Is Anvikshiki Turing complete?"**

The answer was yes, in a restricted sense. The vyāpti-hetvābhāsa system — the core of the meta-prompt's Stage 2 architecture — was essentially a logic program. Vyāptis (universal rules) were Horn clauses. Hetvābhāsas (fallacy detectors) were constraint rules. The architecture Stage 2 produced when applied to a domain was, structurally, a Datalog database: facts, rules, and a query engine.

If that were true, then a guide wasn't just a document. It was a knowledge base that could answer questions. Not retrieve text — *reason*. The distinction between "a very well-written document" and "an executable logic engine" collapsed.

That observation — that the meta-prompt was accidentally building a logic program — was the seed. Everything that followed was either building toward that insight or cleaning up what was built carelessly before it was understood.

---

## Chapter 1: The Meta-Prompt Era (Mar 1–2) — Sessions 1–5

### The Starting Point

The original meta-prompt (`meta_prompt_v3_25.md`, now archived at `theory/history/meta_prompts/meta_prompt_v3_25.md`) was a 7-stage guide generation system. It had a voice calibration document, epistemic status on vyāptis, and a structured Stage 2 that produced:

- Action titles (not topic labels)
- MECE assertions (mutually exclusive, collectively exhaustive arguments)
- Debate cruxes (the best objections, pre-answered)
- A forward reference matrix (every claim that would pay off later)
- An exit narrative (what readers can do after finishing)

Good document design. But it had a sourcing problem. The meta-prompt was generating unsourced claims — what became known as "confident confabulation." Session 1 added the Stage 8 Safety Net: a final review stage where every unsourced claim in a chapter had to be either sourced, flagged as Working Hypothesis, or removed. Version 3.26 (`theory/history/meta_prompts/meta_prompt_v3_26.md`).

The same session produced three design documents: `agentic-systems-for-guide-creation.md` (agent team for parallel guide generation), `improving-meta-prompt-for-concrete-sourcing.md` (6-class provenance classification), and `knowledge-bank-and-agent-council.md` (two-layer knowledge bank). The agentic team design — Orchestrator, Analyst, Architect, Voice Specialist, Research Swarm, Chapter Authors, Continuity Agent, Verifier, Devil's Advocate — was written as a blueprint that assumed the engine was possible, even though the engine didn't exist yet.

### Building the First Engine Concept

Sessions 2–5 circled around the question of implementation.

Session 2 (`2940fe51`): Read `thesis.md` (the original, Prolog-based engine design). Proposed a pure-DSPy engine v1. Discussed the skill-agent alternative. The conclusion: pure DSPy is fine for prototype, but long-term the system needs a real inference engine for the logic layer.

Session 4 (`ad79baae`, Mar 2): Built `BUILD_GUIDE.md` (`theory/BUILD_GUIDE.md`, 2263 lines). This document is still in the repo, unchanged since `ec70444`. It's a complete implementation manual for the v4 engine covering every DSPy 3.1.x API change, all module implementations, the test strategy, and the optimizer usage. It was written before the architecture pivot — before Session 6 changed everything — but it was already targeting the correct framework.

Sessions 3 and 5 (`13aa2739`, `08cfe99f`) applied the meta-prompt to the business expert domain: the first passes at the guide that would later become the 12-chapter business strategy knowledge base used as the engine's primary test domain.

**The state at end of Session 5:** A complete meta-prompt (v3.26). A complete build guide. A first-pass business expert guide. An engine thesis that worked but was architecturally ungainly. And a growing suspicion that the architecture had too many moving parts.

---

## Chapter 2: The Frankenstein Diagnosis (Mar 3) — Session 6

### The Audit

Session 6 (`2afb4792`, 18MB — the largest session before the final sprint) was the intellectual turning point.

The user's opening prompt: *"List all decisions in the thesis that are hand-specified, analyse critically."*

The Gen 3 architecture had, at that point, accumulated six independent formalisms:

1. **Heyting lattice** — for epistemic status (ESTABLISHED, HYPOTHESIS, OPEN, CONTESTED, BOTTOM)
2. **Cellular sheaf** — for local-to-global consistency checking
3. **Hand-specified trust tables** — for source authority (who gets believed, how much)
4. **Keyword-based hetvābhāsa detection** — for fallacy identification
5. **Identity restriction maps** — for scope management
6. **Hand-tuned uncertainty thresholds** — for everything else

The audit produced a devastating finding: none of these components spoke to each other. Adding a new pramāṇa (source type) required updating five separate systems. The sheaf layer was checking consistency that the Heyting lattice was also tracking. The trust tables were expressing something that the sheaf could also express. The keyword fallacy detector was doing something the argumentation rules could also do.

The user named the diagnosis precisely: **"It looks like a Frankenstein architecture."**

### The Pivot

The session explored alternatives:
- Normalizing flows? Probabilistic, but requires continuous-valued inputs, not symbolic rules
- Sheaf homology? More expressive, but harder, and the sheaf was already doing nothing useful
- Categorical UQ? Principled, but requires calibration data that didn't exist

Then came the key realization.

Nyāya epistemology — the philosophical framework the project was already using as its design ontology — had already solved this. Nyāya's theory of inference (*anumāna*), testimony (*śabda*), and conflict resolution (*nirṇaya*) wasn't just thematically related to the engine's problems. It was **structurally isomorphic** to ASPIC+ structured argumentation:

| Nyāya | ASPIC+ |
|-------|--------|
| Vyāpti (universal rule) | Defeasible rule |
| Hetvābhāsa (formal fallacy) | Attack relation |
| Pramāṇa hierarchy | Argument preference |
| Epistemic status (ESTABLISHED/CONTESTED) | Extension membership (IN/OUT/UNDECIDED) |
| Nirṇaya (conflict resolution) | Grounded/preferred/stable semantics |

The philosophy already had the answer. The computational framework just needed to be identified.

Session 6 concluded by writing `thesis_v4_r1.md` — what is now `theory/thesis_v4_r1.md` (1955 lines), the canonical current thesis. Its central claim: **all six formalisms collapse into one coherent framework** — ASPIC+ structured argumentation with Subjective Logic annotation.

- The sheaf becomes unnecessary: ASPIC+ defeat relations handle local-global consistency
- The Heyting lattice becomes unnecessary: argumentation semantics (IN/OUT/UNDECIDED) handles epistemic status
- The trust tables become ProvenanceTag fields
- The fallacy detectors become Attack construction rules
- The uncertainty thresholds become Subjective Logic opinion fusion (tensor ⊗ for weakest-link, oplus ⊕ for best-source)

The thesis also established why Datalog — not Prolog — was the right computational substrate: Datalog guarantees polynomial termination (O(rules × Δfacts) per semi-naive iteration), eliminating the termination problems of full Prolog while preserving the expressive power needed for the vyāpti/hetvābhāsa logic.

**Philosophy established in this session:** Coherent architecture beats composable complexity. A system that fails should fail uniformly — not mysteriously at the intersection of six formalisms that were designed independently.

---

## Chapter 3: Building on Solid Ground (Mar 4) — Session 7

### The Implementation

Session 7 (`2b92b540`, 11MB) was the construction session. The thesis was settled. The work became concrete.

**The predicate extraction problem:** The hardest unsolved issue — getting from natural language queries to verified Datalog predicates without hallucination. The five-layer grounding defense was designed here:

1. **Layer 1** — Ontology-constrained prompt (what predicates are in-scope)
2. **Layer 2** — Grammar-constrained decoding (only valid Datalog syntax can be emitted)
3. **Layer 3** — Ensemble voting (N=5 calls, consensus threshold)
4. **Layer 4** — Round-trip verification (ground the predicate back to prose, check coherence)
5. **Layer 5** — Solver-feedback refinement (run the Datalog, check for contradictions)

The `predicate_extraction.py` module (1123 lines) implements a 5-stage extraction pipeline (A through E): entity extraction → relation extraction → predicate formation → validation → HITL review. Each stage is a DSPy module with structured output via Pydantic.

**The ELI5 trace:** Before writing code documentation, the session produced `docs/pipeline_eli5.md` — a plain-English walkthrough of the entire pipeline using the business strategy example. The user's instinct was sound: writing the ELI5 forced clarity about what the system actually did versus what the thesis claimed it did. This document would later directly answer expert reviewer critique #2.

**The knowledge base:** The business expert domain was formalized into `anvikshiki_v4/data/business_expert.yaml` — 11 vyāptis (universal rules about business strategy), 8 hetvābhāsas (domain-specific fallacy detectors), with source provenance on every rule. This YAML file is both test fixture and demonstration of what the meta-prompt architecture stage compiles to.

### Git Initialization

The session also formalized the project into a git repository. Four commits:

- `ec70444` (Mar 4): **"Initial commit: Anvikshiki neurosymbolic reasoning engine"** — 62 files, 28,434 lines. The complete engine: all 24 Python modules, all tests (249 passing, no LLM needed), the complete business expert KB, 12 guide chapters, all documentation.
- `547de52` (Mar 4): **"Remove thesis_v2.md"** — cleanup; only the ASPIC+ thesis is current
- `abfcba9` (Mar 4): **"Add theory/history/ archive"** — all pre-ASPIC+ work moved to `theory/history/`. The message was explicit: these architectures are worth preserving (they show how the thinking evolved) but they are superseded. Not deleted. Archived.

The archiving commit was philosophically significant. Deleting the old theses would have hidden the reasoning. Keeping them in the main directory would have caused confusion about which was current. The `theory/history/` structure made the lineage visible without cluttering the working tree.

**Philosophy established:** Documentation is as important as code. A system that cannot be explained to a non-expert does not exist — it is just code.

---

## Chapter 4: The Pipeline Expansion (Mar 5) — Sessions 8–10

### The Missing T3

Session 8 (`e3e84d62`, Mar 5) identified a gap. The thesis described T2 (logic engine) in detail. T3 (the retrieval system over guide prose) was handwaved as "builds a NetworkX graph." This was inadequate.

The question was sharp: **when a query returns DECLINE-coverage (the KB doesn't cover the question), what happens?** The original design returned nothing. That was wrong. A declined query against a business strategy KB is still a business strategy question. The KB has relevant structure. It should be able to answer — just at lower confidence.

The **Adaptive Knowledge Landscape** (AKL) design emerged: when coverage declines, the system projects the query along existing KB axes (the vyāptis as conceptual dimensions), generates HYPOTHESIS-status augmentation predicates using domain framework templates, validates them via cycle detection and Datalog compile, and merges them into the active KnowledgeStore for this query only.

Commit `c627180` added:
- `run_pipeline_e2e.py` — the first end-to-end pipeline runner
- `theory/history/discussions/adaptive-knowledge-landscape.md` — original AKL design
- `theory/history/discussions/build-spec-adaptive-knowledge-landscape-v1.md` — build spec (2241 lines)

Session 10 (`21b283c9`) conducted a full critical audit of the combined architecture. It identified that T2b, T3a, T3b, and coverage were being conflated — each needed a clear contract with precise compile-time vs. query-time responsibilities.

### The T2b/T3a/T3b/Coverage Separation

Session 11 began the implementation of the complete pipeline (commit `74f74ca`, Mar 5):

**T2b** (`t2b_compiler.py`) — Compile-time KB augmentation. Runs once, offline, against the guide prose. Wraps the full PredicateExtractionPipeline (Stages A–E) to produce fine-grained argument skeletons, a synonym table, and source section cross-links. Never runs at query time.

**T3a** (`t3a_retriever.py`) — Embedding-based retrieval at query time. FAISS-backed via `dspy.retrievers.Embeddings`. Retrieves relevant guide sections with section boosting for T2b cross-links. Applies epistemic inheritance: retrieved fragments inherit the `EpistemicStatus` of the KB nodes they cross-link to.

**T3b** (`kb_augmentation.py`) — AKL query-time augmentation. Runs only when `SemanticCoverageAnalyzer` returns DECLINE. Generates augmentation predicates, validates, merges. Satpratipakṣa routing: contradictory evidence retrieved and presented without suppression. Savyabhicāra routing: defeated-by-specificity predicates suppressed.

**Coverage** (`coverage.py`) — Three-layer predicate matching: exact → synonym → token overlap. Returns FULL/PARTIAL/DECLINE. Thresholds in `EngineParams` (not hardcoded after the later audit).

**`engine_factory.py`** — The single entry point. Wires the entire compile chain: `load_knowledge_store → compile_t2b → compile_t3 → T3aRetriever → SemanticCoverageAnalyzer → AugmentationPipeline → GroundingPipeline → AnvikshikiEngineV4`.

**Philosophy established:** Compile-time work stays at compile-time. The distinction between offline (T2b) and online (T3a, T3b) is an architectural invariant, not an implementation detail.

---

## Chapter 5: Testing Against Real Models (Mar 5–6) — Session 11, Phase 1

### GLM-5 and the Reasoning Content Bug

The engine was tested against Gemini 2.5 Pro and GLM-5 (a reasoning model via DeepInfra). GLM-5 exposed a production bug that no unit test had caught: reasoning models route JSON to `reasoning_content` instead of `content` when `response_format=json_object` is set. DSPy's `dspy.LM` calls both fields, but the live models sometimes only populate one.

The `ReasoningLM` wrapper (`reasoning_lm.py`) was the fix: a `dspy.LM` subclass that strips `response_format` for reasoning models and falls back to `reasoning_content` when `content` is empty. Transparent — all callers see a normal LM interface. The bug was in how DSPy interacted with the OpenAI-compatible API spec for reasoning models. The fix was three dozen lines.

Commit `60a4ac4` (Mar 6) also added `GroundingMode`:

```python
class GroundingMode(str, Enum):
    MINIMAL = "minimal"   # 1 call: Layer 1 only, temp=0
    PARTIAL = "partial"   # 3 calls: N=3 ensemble + consensus
    FULL    = "full"      # 5+ calls: N=5 + round-trip + solver (original)
```

The realization behind this: N=5 ensemble is expensive (~15 LLM calls per grounding). For high-confidence in-domain queries, 1 call is sufficient. For production use, you want to choose the right mode for the right query type. `GroundingPipeline.forward()` accepts mode as a call-site override — the pipeline instance has a default, but any call can override it.

The e2e trace scripts (`scripts/e2e_trace_gemini.py`) exercise all three modes across three scenarios: in-domain (MINIMAL), partial-coverage (PARTIAL), and out-of-domain (FULL). The actual GLM-5 run trace is at `traces/glm5_e2e_trace.txt` (4.5MB, untracked — raw LLM output).

---

## Chapter 6: The Honesty Audit (Mar 6) — Session 11, Phase 2

### The Question That Opened the Investigation

The user asked: *"Check what other fake stuffs we have here?"*

What followed was the most technically significant work of the project — not because new features were added, but because false claims were removed.

### What the Audit Found

`discussions/critical-audit-v4-implementation.md` documented the findings. Four categories of dishonesty:

**1. The semiring claim.** `ProvenanceTag` was documented as a "provenance semiring" — a term from the database literature meaning a commutative semiring where ring operations correspond to uncertainty propagation. But Jøsang (2016) §3.6 explicitly proves that Subjective Logic violates the distributivity axiom (`a ⊗ (b ⊕ c) ≠ (a ⊗ b) ⊕ (a ⊗ c)` in general). ProvenanceTag is a principled composite of two well-defined structures (product lattice for metadata, SL opinions for provenance), but it is not a semiring. Using the term was incorrect.

**2. The parameter count claim.** The thesis had a section claiming the architecture reduced the number of parameters from 16 to 3. This was false on inspection: there were 35+ hardcoded constants scattered across 6 files, none with a calibration basis. The "3 parameters" figure was counting only the DSPy-optimizable weights, ignoring the sea of magic numbers.

**3. The contestation mode illusion.** `EngineConfig` had a `contestation_mode` parameter with three values: `grounded`, `preferred`, `stable`. The documentation claimed these mapped to three Nyāya debate modes: vāda (structured debate), jalpa (adversarial debate), vitaṇḍā (destructive debate). The code had `if contestation_mode == 'preferred': ... elif contestation_mode == 'stable': ...` — but both branches silently timed out after 30 seconds and fell back to grounded. The parameter did nothing.

**4. The epistemic status thresholds.** `epistemic_status()` in `schema_v4.py:209–218` used 5 magic floats to convert a Subjective Logic (b,d,u) triple to a discrete ESTABLISHED/HYPOTHESIS/CONTESTED status. The comment called them "DSPy-optimizable." They were not. They were hand-tuned and had no calibration basis.

### What Was Fixed

Commit `77522f8` (Mar 6) — *"critical audit — honest thesis claims, dead code removal, structural epistemic status"*:

- `schema_v4.py`: Title changed from "Unified Architecture via Provenance Semirings" to "Minimal Complete Architecture with SL Annotation." The `epistemic_status()` method gained a WARNING comment: "These thresholds are hand-tuned and uncalibrated."
- `argumentation.py`: The Nyāya-to-ASPIC+ mapping table in §7.2 was corrected from "all 19 mappings are exact 1:1" to an honest three-category table: 7 exact (genuinely isomorphic), 5 approximate (strong structural affinity), 5 novel (not from either tradition).
- `contestation.py`: `preferred` and `stable` semantics documented as "offline analysis only — not on the query path."

This commit fixed the documentation. It did not yet fix the architecture.

---

## Chapter 7: The Path A Fixes (Mar 8) — Session 11, Phase 3

### Four Targeted Fixes

Commit `67d45c8` (Mar 8) — *"Path A — kill jalpa/vitanda illusion, centralize params, axiomatize composition"* — made four structural changes:

**Fix 1: Kill jalpa/vitaṇḍā.** The `contestation_mode` parameter was removed entirely from `engine_v4.py` and `engine_factory.py`. Both `forward()` and `forward_with_coverage()` now always use grounded semantics — the only semantics that (a) terminates in polynomial time and (b) was actually running. Three test classes were deleted:

- `TestFullPipelineJalpa` — tested `contestation_mode='jalpa'` behavior that didn't exist
- `TestFullPipelineVitanda` — tested `contestation_mode='vitanda'` behavior that didn't exist
- `TestCrossModeConsistency` — tested that the three modes gave consistent output; since two modes didn't exist, neither did the consistency

These tests had been passing because the `assert` statements were comparing the output of grounded semantics against itself (the fallback made them identical). Tests of nonexistent behavior passing is worse than tests of nonexistent behavior failing.

**Fix 3: Centralize parameters.** `engine_params.py` (new file) contains four frozen dataclasses:

- `CompilerParams`: 12 belief floats from the BELIEF_MAP, decay half-life, threshold, combo cap, fixpoint limit
- `SynthesisParams`: temperature settings, max tokens per LM call
- `GroundingParams`: N per mode (1/3/5), confidence thresholds, round-trip enable flags
- `EngineParams`: composes all three; single config object for `AnvikshikiEngineFactory`

Every magic number that was previously scattered across six files now lives in one place with a docstring explaining its provenance (or lack thereof, for the hand-tuned ones).

**Fix 4: Axiomatize composition.** `ProvenanceTag` got a formal docstring specifying the algebraic structure precisely:

```
tensor (⊗) = meet (∧) = min on (b, u) componentwise
  → weakest-link semantics: the chain is only as strong as its weakest source
  → used for: chained inference (A→B→C)

oplus (⊕) = join (∨) = max on (b, u) componentwise
  → best-source semantics: independent corroboration strengthens belief
  → used for: fusion of independent evidence sources

Exception: derivation_depth uses tensor=min (finite-depth chains are bounded)
           but oplus=min (more independent paths = shallower effective depth)
```

This is not a semiring. It's a product lattice: a Cartesian product of lattices (the SL opinion space and the metadata space), with component-wise operations. The documentation now says so explicitly.

**Fix 2 (deferred):** `epistemic_status()` still uses 5 hand-tuned thresholds. The design doc (`discussions/towards-categorical-uq-with-conformal-predictions.md`) proposes a GBT classifier with RAPS conformal prediction wrapper, giving calibrated coverage guarantees (P(status ∈ prediction_set) ≥ 1−α). This requires manually annotated training data — (ProvenanceTag, correct_EpistemicStatus) pairs. The data doesn't exist. Fix 2 waits for the data.

---

## Chapter 8: Responding to Experts (Mar 8) — Session 11, Phase 4

### The Reviewer Critiques

Two expert reviewers had read `theory/thesis_v4_r1.md` and produced `discussions/thesis2_v1_expert_reviewer_critiques.md`. Three structural weaknesses:

**Critique 1 — Philosophical-computational gap:** The Nyāya terminology was introduced cold before any computational grounding. A reader could read §1–3 without knowing what any of it would look like in code. The §2.1 Quick Reference table (Nyāya→ASPIC+ mapping) was buried in back matter.

**Critique 2 — ELI5-thesis gap:** `docs/pipeline_eli5.md` claimed to be the plain-English version of the thesis. But Stage 4 ("The Argumentation Engine runs") never showed what "runs" meant formally. The ELI5 said the pipeline identified an attack on argument A0003 — but showed no ASPIC+ objects, no tag arithmetic, no extension labels. A reader who wanted to see the math had nowhere to look.

**Critique 3 — T3 handwave:** §9.4 of the thesis was 6 lines describing T3 as "retrieval from the guide sections stored in T3." It did not explain epistemic inheritance, did not explain the routing logic, did not explain what happened when a retrieved fragment had a different `EpistemicStatus` than the KB node it related to.

### The Responses

Commit `fd3e609` (Mar 8) — *"address all three expert reviewer critiques"*:

**Response to Critique 1:** The §2.1 Quick Reference table was moved from §7.2 to §2.1 — the exact point of first Nyāya concept introduction. Every concept now shows its ASPIC+ analog and its Python class on first mention.

**Response to Critique 2:** `docs/pipeline_eli5.md` gained a progressive disclosure sidebar at Stage 4. The plain-English narrative continues unchanged. But after the sentence describing the attack, a blockquoted formal sidebar appears:

```
> **For readers who want to see the formal machinery:**
>
> A0001: positive_unit_economics [premise, pramana=PRATYAKSA, b=0.85]
> A0003: value_creation [via V01]
>   tag = A0001.tag ⊗ V01.tag
>       = (b=0.85, d=0.05, u=0.10) ⊗ (b=0.95, d=0.03, u=0.02)
>       = (b=0.808, d=0.048, u=0.193)
>
> Attack(attacker=A0005, target=A0003, type="undercutting",
>        hetvabhasa="savyabhicara", specificity_weight=0.73)
> → A0003 labeled OUT
> → A0004 (which had A0003 as only support) → also OUT
>
> pramana min-attenuates: PRATYAKSA ⊗ ANUMANA = ANUMANA (lower authority wins)
```

The sidebar is skippable. The plain-English readers skip it. The formal readers need it.

`theory/thesis_v4_r3.md` was also created — document revision 3 of the ASPIC+ thesis, incorporating all three reviewer fixes plus a fully worked unit economics inference chain in §6.1 showing the complete tag ⊗ arithmetic for a real business inference: chain degrades b=0.85→0.808→0.388 over three hops, pramāṇa attenuates from PRATYAKSA to ANUMANA to ANUMANA, independent sources fuse via ⊕.

**Response to Critique 3:** §9.4 was rewritten from 6 lines to a full section covering:
- *Epistemic inheritance:* retrieved fragments inherit EpistemicStatus from the KB nodes they link to via T2b cross-reference
- *Savyabhicāra routing:* if a retrieved fragment's predicate is defeated by a more-specific KB predicate, it is suppressed entirely (not presented)
- *Satpratipakṣa routing:* if a retrieved fragment contradicts the KB but is not defeated (equal specificity), both the KB position and the fragment are presented, labeled for user adjudication

---

## Chapter 9: The Archive and Cleanup (Mar 8) — Sessions 12–13

### Recording the History

After the four-phase implementation sprint, the repo had accumulated two problems: the documentation trail was incomplete (no central document mapping all files to their origins), and the filenames were a mess — typos, naming collisions, undefined jargon, model names baked into paths.

Commit `b0c586d` created `GLOSSARY.md` — the living registry of everything. 784 lines (now updated post-rename). Three sections:

**Section 1 — Session Ledger:** 12 Claude sessions mapped by full UUID to their dates, topics, and commits. The ledger makes the project's intellectual history traceable. Any decision in any file can be traced to the session where it was made by following the commit reference to the session reference.

**Section 2 — File Registry:** Every file with content description, line count, creation commit, modification commits, and session IDs. Files with known problems (typos, misplaced locations, naming collisions) flagged with ⚠️. Candidate for deletion files noted.

**Section 3 — Story of Updates:** The narrative history — why decisions were made, what changed, and what the evolution reveals about the project's philosophy. The five chapters that became Chapters 1–5 of this document's earlier form.

### The Rename Pass

Commit `a3109cd` — 23 renames, 1 deletion, no content changes.

The problems that were fixed:

| Problem | Example | Fix |
|---------|---------|-----|
| Typo | `practical_useage.md` | → `practical_usage.md` |
| Doubled extension | `pipeline_flowchart_llama3.2md.md` | deleted |
| Naming collision | `thesis2_v1.md` | → `thesis_v4_r1.md` (v4 arch, revision 1) |
| Naming collision | `thesis_v3.md` | → `thesis_v4_r3.md` (v4 arch, revision 3) |
| Model baked in | `pipeline_flowchart_llama3.2.md` | → `pipeline_flowchart_path_b.md` |
| Date in docs/ | `e2e_pipeline_trace_2026-03-06.md` | → `traces/e2e_gemini_2026-03-06.md` |
| Misleading label | `eli5_trace.md` | → `pipeline_eli5.md` |
| Undefined jargon (meta2) | `anvikshiki_meta2_prompt.md` | → `meta_prompt_gen2.md` |
| Undefined jargon (post-fix-round) | `critical-analysis-v4-post-fix-round.md` | → `critical-analysis-v4-pre-aspic-pivot.md` |
| ALL_CAPS inconsistency | `BUILD_GUIDE_v2.md` | → `build_guide_v2.md` |
| Dots in version numbers | `meta_prompt_v3.25.md` | → `meta_prompt_v3_25.md` |

Git tracked all renames at 97–100% similarity, preserving full `git log --follow` history. Five files with cross-references to the old names were updated.

---

## Chapter 10: The Final Pull Request (Mar 9)

### The Merge

The `aspic-v4-engine-complete` branch — 7 commits, branched from `main` at commit `c627180` — was merged into `main` as Pull Request #1.

The PR message documented each commit individually with the architectural before/after:

**Before:**
```
AnvikshikiEngine
  └── GroundingPipeline (always Full: N=5 + round-trip + solver)
      └── T3 retrieval: monolithic, no KB-coverage awareness
```

**After:**
```
AnvikshikiEngineFactory
  ├── T2bCompiler (compile-time KB augmentation)
  └── AnvikshikiEngine
       ├── CoverageAssessor → AKL expansion if coverage < threshold
       ├── T3aRetriever (dense, with epistemic inheritance)
       ├── T3bRetriever (Savyabhicāra + Satpratipakṣa routing)
       └── GroundingPipeline
            ├── MINIMAL mode: 1 LLM call
            ├── PARTIAL mode: N=3 ensemble + consensus
            └── FULL mode: N=5 + round-trip + solver
```

The PR also documented what was explicitly removed: `JalpaModule`, `VitandaModule`, `contestation_mode`, 3 test classes testing non-existent behavior, all `dspy.Assert`/`dspy.Suggest` calls (deprecated in DSPy 3.1.x).

### What Was Committed: The Final State

The merged `main` branch contains:

**Engine (`anvikshiki_v4/`, 24 Python modules, ~10,900 lines):**
- `schema_v4.py` — ProvenanceTag, PramanaType, Argument, Attack (product lattice axioms formalized)
- `schema.py` — KnowledgeStore, Vyapti, Hetvabhasa, AugmentationMetadata
- `argumentation.py` — ASPIC+ grounded/preferred/stable semantics (grounded is the hot path)
- `datalog_engine.py` — Semi-naive evaluation, O(rules × Δfacts) per iteration
- `t2_compiler_v4.py` — Query-time KB compilation to ASPIC+ argument skeletons
- `t2b_compiler.py` — Compile-time fine-grained KB augmentation from prose
- `t3_compiler.py` — Guide prose compilation to T3 graph
- `t3a_retriever.py` — FAISS-backed embedding retrieval with epistemic inheritance
- `grounding.py` — 5-layer grounding defense, GroundingMode enum
- `coverage.py` — 3-layer semantic coverage analysis
- `kb_augmentation.py` — AKL query-time augmentation for DECLINE queries
- `engine_v4.py` — Main engine with `forward()` and `forward_with_coverage()`
- `engine_factory.py` — Full compile chain wiring
- `engine_params.py` — Centralized frozen dataclass parameters (no magic numbers scattered)
- `reasoning_lm.py` — ReasoningLM wrapper for GLM-5/DeepSeek-R1 routing bug
- `contestation.py` — ContestationManager (offline analysis only)
- `predicate_extraction.py` — 5-stage extraction pipeline (A–E)
- `extraction_schema.py`, `extraction_eval.py`, `extraction_hitl.py` — extraction support
- `query_refinement.py` — Query disambiguation and reformulation
- `uncertainty.py` — Conformal UQ stub (Fix 2, deferred)
- `optimize.py` — DSPy optimizer integration (MIPROv2, SIMBA, GEPA)
- `__init__.py` — Public API surface

**Tests (`anvikshiki_v4/tests/`, 249 passing, no LLM needed):**
Tests cover: argumentation semantics, business expert KB, grounding pipeline (mocked LLM), schema operations (tensor/oplus algebra), t2 compiler, query refinement, fixes verification.

**Knowledge base (`anvikshiki_v4/data/`):**
- `business_expert.yaml` — 11 vyāptis, 8 hetvābhāsas, 505-line formal business strategy KB

**Theory (`theory/`):**
- `thesis_v4_r1.md` (1955 lines) — canonical ASPIC+ architecture thesis
- `thesis_v4_r3.md` (613 lines) — reviewer-revised version with worked examples
- `BUILD_GUIDE.md` (2263 lines) — implementation manual

**Archive (`theory/history/`):**
- `thesis/` — Gen 1 (Prolog+sheaf), Gen 2 (Datalog), Gen 3 (lattice-Datalog) theses
- `build_guides/` — Build guides for Gen 2, 3, 4 pre-pivot
- `meta_prompts/` — meta_prompt v3.2, v3.25, v3.26, gen2 family
- `discussions/` — 8 design discussions from Sessions 1–10

**Discussions (`discussions/`, 5 active design docs):**
- `critical-audit-v4-implementation.md` — the audit findings
- `ideal-architecture-properties.md` — formal properties the architecture must satisfy
- `implementation-trace-t2b-t3a-t3b-coverage.md` — step-by-step trace of the implementation
- `proving-architecture-optimality.md` — formal argument that ASPIC+SL is minimal-complete
- `towards-categorical-uq-with-conformal-predictions.md` — Fix 2 design doc

**Documentation (`docs/`):**
- `pipeline_eli5.md` — primary user-facing plain-English pipeline walkthrough
- `pipeline_eli5_full.md` — extended walkthrough (full N=5 path)
- `pipeline_flowchart_path_b.md` — complete data-flow flowchart (Path B)
- `pipeline_flowchart_coverage_routing.md` — T2b/T3a/T3b/coverage routing flowchart
- `predicate_extraction_design.md` — extraction pipeline design document
- `predicate_extraction_theory.md` — academic treatment of the extraction problem
- `practical_usage.md` — code examples and usage guide

**Guides (`guides/business_expert/`, 12 chapters + stage documents):**
The complete 12-chapter business strategy guide. Both human-readable artifact and the source document for the business_expert.yaml knowledge base. The dual-use nature is the point: the guide generates the KB.

**Repository:**
- `GLOSSARY.md` — complete file registry and session history
- `SAGA.md` — this document

---

## Epilogue: What Was Built and What Remains

### The Architecture in Three Sentences

The Ānvīkṣikī Engine takes a domain expert's knowledge (encoded via the meta-prompt into YAML vyāptis and hetvābhāsas), compiles it into an ASPIC+ argumentation framework with Subjective Logic opinions, and runs Datalog grounded semantics to answer queries with formally qualified epistemic status — identifying not just *what* the answer is, but *which premises* it rests on, *which conflicts* exist, and *how confident* the sources are, in polynomial time.

### What Is Provably True

- **Termination:** Datalog grounded semantics is O(|rules| × |facts|) per semi-naive iteration, O(n²) worst case. Terminates.
- **Soundness:** ASPIC+ grounded extension semantics is provably sound and complete for stable models on finite attack graphs (Dung 1995).
- **Contestability:** The architecture satisfies all 8 Contestable AI properties (Moreira et al. 2025) through its argumentation structure — not through post-hoc mechanisms.
- **Nyāya correspondence:** 7 of the 19 Nyāya-to-ASPIC+ mappings are formally exact (proved in `thesis_v4_r1.md` §7.2). 5 are approximate. 5 are novel.

### What Remains

**Fix 2 (Conformal UQ):** `epistemic_status()` uses 5 hand-tuned thresholds. The right replacement is a GBT classifier with RAPS conformal wrapper. The design is written. The calibration data does not exist. This will be implemented when the data does.

**The naming collision:** `theory/history/thesis/thesis_v3.md` (Gen 3 architecture) coexists with `theory/thesis_v4_r3.md` (doc revision 3 of the v4 architecture). The GLOSSARY documents both clearly. The structural fix (renaming `theory/thesis.md` = canonical, git tracks versions) is noted but not yet done.

**The `traces/` gitignore:** Three large files in `traces/` (21MB calltree, 4.5MB GLM-5 trace, 13KB grounding trace) are untracked. The `.gitignore` should be updated to explicitly ignore them.

### The Project's One Idea

The project has one idea, stated eight different ways across its history:

*Session 1:* "The vyāpti system is a logic program."
*Session 6:* "Nyāya epistemology already solved this."
*Thesis abstract:* "All six formalisms collapse into two that compose."
*Commit message:* "Kill jalpa/vitanda illusion."
*Fix 3:* "There are no magic numbers, only undocumented assumptions."
*Fix 4:* "It is a product lattice, not a semiring."
*Reviewer response:* "Show the formal machinery where the plain language lives."
*This document:* "A system that claims to do what it doesn't is harder to fix than a system that honestly documents what it does."

The same idea. Said differently each time. The builds are the proof.

---

*Written: 2026-03-09. Branch `aspic-v4-engine-complete` merged into `main` as PR #1.*
*Sessions: 1–13. Commits: `ec70444` through `a3109cd`. Lines of code: ~45,000.*
