# Implementation Trace: T2b / T3a / T3b / Coverage / Engine Orchestration

**Date:** 2026-03-05
**Branch:** `feat/t2b-t3a-t3b-architecture`
**Audit addressed:** `discussions/critical-audit-combined-architecture.md`
**Tests:** 249 passed, 4 skipped (unchanged)

---

## What Was Built

### Audit Findings Addressed

| Finding | Severity | Status | Implementation |
|---------|----------|--------|----------------|
| A-01: T2b compiler unspecified | HIGH | Done | `t2b_compiler.py` — wraps `PredicateExtractionPipeline` |
| A-02: Coverage analysis fragile | HIGH | Done | `coverage.py` — 3-layer semantic matching |
| A-03: T3b scope gap | MEDIUM | Done | `kb_augmentation.py` — hybrid LLM parametric (web search ready for v2) |
| A-06: T2b/T3a cross-linking | MEDIUM | Done | `T3aRetriever.retrieve_for_predicates()` + `t2b_source_sections` |
| Engine routing missing | — | Done | `engine_v4.py` — `forward_with_coverage()` |
| T3a retriever missing | — | Done | `t3a_retriever.py` — embedding + fallback |

### Files Created

#### 1. `anvikshiki_v4/t2b_compiler.py` (~150 lines)

**Purpose:** Compile-time fine-grained KB extraction from guide prose.

**Key insight:** The existing `PredicateExtractionPipeline` (Stages A-E in `predicate_extraction.py`, 1124 lines) already does the heavy lifting — extract predicates from guide text, decompose vyaptis into sub-predicates, canonicalize, construct new vyaptis, validate via cycle detection + Datalog compile. T2b is a thin wrapper that adds origin tagging, synonym table extraction, and source section tracking.

**Public API:**
```python
def compile_t2b(
    knowledge_store: KnowledgeStore,
    guide_text: dict[str, str],
    config: Optional[ExtractionConfig] = None,
) -> T2bResult
```

**T2bResult fields:**
- `augmented_ks` — KnowledgeStore with base + fine-grained vyaptis
- `synonym_table` — `dict[str, str]` alias → canonical predicate name
- `validation` — ValidationResult from Stage E
- `fine_grained_vyapti_ids` — IDs of newly extracted vyaptis
- `source_sections` — `dict[str, list[str]]` vyapti_id → chapter_ids (for T3a cross-linking)

**How synonym table is built:**
1. Stage C `SynonymCluster` objects → direct alias mappings
2. Token overlap between new predicates and base KB predicates (>60% Jaccard) → additional mappings

**Origin tagging:** Each new vyapti gets `augmentation_metadata` with `origin=GUIDE_EXTRACTED`, `source_chapter_ids`, `parent_vyapti_id`.

#### 2. `anvikshiki_v4/coverage.py` (~120 lines)

**Purpose:** Semantic coverage analysis — deterministic, zero LLM calls.

**Three matching layers (applied in order per predicate):**
1. **Exact:** predicate name exists in KB vocabulary
2. **Synonym:** predicate maps to canonical name via synonym table
3. **Token overlap:** Jaccard similarity on underscore-split tokens (threshold ≥ 0.4)

**Thresholds (aligned with `query_refinement.py`):**
- `FULL_THRESHOLD = 0.6` → full coverage path
- `PARTIAL_THRESHOLD = 0.2` → partial coverage path
- Below 0.2 → `DECLINE`

**CoverageResult fields:**
- `coverage_ratio`, `matched_predicates`, `unmatched_predicates`
- `match_details` — `dict[str, str]` predicate → match_type (exact/synonym/token)
- `relevant_vyaptis` — vyapti IDs involved in matched predicates
- `decision` — "FULL" / "PARTIAL" / "DECLINE"

**Verified behavior:**
```
positive_unit_economics(acme) → exact match → ratio=1.0
supply_chain_bottleneck(acme) → no match → ratio=0.5 (PARTIAL)
With synonym_table={'supply_chain_bottleneck': 'binding_constraint_identified'}:
supply_chain_bottleneck(acme) → synonym match → ratio=1.0 (FULL)
```

#### 3. `anvikshiki_v4/kb_augmentation.py` (~300 lines)

**Purpose:** T3b / AKL query-time augmentation. Generates structured predicates for queries that DECLINE against the KB.

**DSPy Signatures:**
1. `ScoreFrameworkApplicability` — scores how applicable the domain framework is (1 LLM call). Threshold: ≥ 0.4 to proceed.
2. `GenerateAugmentationPredicates` — generates new predicates using existing vyaptis as templates (1 LLM call). Returns parallel lists.

**AugmentationPipeline steps:**
1. Domain check → applicability score (below 0.4 = out-of-domain, stop)
2. Generate predicates using base KB axes as templates
3. Parse parallel lists into Vyapti objects:
   - Confidence capped at 0.75
   - `epistemic_status = WORKING_HYPOTHESIS`
   - `decay_risk = MODERATE`
   - `evidence = "theoretical"`
4. Validate: cycle detection (`_detect_cycles`) + Datalog compile test
5. Merge into KnowledgeStore copy

**Constants:**
- `APPLICABILITY_THRESHOLD = 0.4`
- `MAX_NEW_VYAPTIS = 8`
- `MAX_CONFIDENCE = 0.75`

**AugmentationResult fields:**
- `augmented` (bool), `reason`, `framework_score`
- `new_vyaptis` — list of Vyapti objects with `augmentation_metadata.origin = LLM_PARAMETRIC`
- `merged_kb` — KnowledgeStore with augmented vyaptis added
- `validation_warnings`

#### 4. `anvikshiki_v4/t3a_retriever.py` (~100 lines)

**Purpose:** Embedding-based retriever over guide text chunks.

**T3aRetriever:**
- Wraps `dspy.retrievers.Embeddings` (FAISS-backed)
- Graceful fallback to keyword-based retrieval when embeddings unavailable
- Section boosting for T2b→T3a cross-linking

**Key methods:**
- `retrieve(query, k, boost_sections)` — basic retrieval with optional section boost
- `retrieve_for_predicates(activated_predicate_sections, query, k)` — cross-linked retrieval: collects chapter IDs from activated predicates, passes them as boost sections

**Boosting logic:** Chunks from boosted sections that appear in top 2*k results get moved to front of results list.

**Fallback retrieval:** Token overlap scoring (query tokens ∩ chunk tokens), with 1.5x boost for matching sections and 1.2x boost for vyapti-anchored chunks.

### Files Modified

#### 5. `anvikshiki_v4/schema.py`

**Added:**
- `AugmentationOrigin` enum: `CURATED`, `GUIDE_EXTRACTED`, `LLM_PARAMETRIC`, `WEB_SOURCED`, `HITL_PROMOTED`
- `AugmentationMetadata` model: `origin`, `generated_at`, `generating_query`, `framework_vyaptis_used`, `source_chapter_ids`, `parent_vyapti_id`, `generation_model`
- `Vyapti.augmentation_metadata: Optional[AugmentationMetadata] = None` — backward-compatible, None for base KB vyaptis
- `KnowledgeStore.fine_grained_vyapti_ids: list[str]` — IDs of T2b-extracted vyaptis
- `KnowledgeStore.synonym_table: dict[str, str]` — alias → canonical predicate name

**Backward compatibility:** All new fields have defaults (None, empty list, empty dict). Existing YAML loading and all 249 tests pass unchanged.

#### 6. `anvikshiki_v4/engine_v4.py`

**Added `__init__` parameters (all optional, backward-compatible):**
- `coverage_analyzer: Optional[SemanticCoverageAnalyzer]`
- `augmentation_pipeline: Optional[AugmentationPipeline]`
- `t3a_retriever: Optional[T3aRetriever]`
- `t2b_source_sections: Optional[dict[str, list[str]]]`

**Added `forward_with_coverage()` method — 8 steps:**

1. **Ground query** → predicates (same as `forward()`)
2. **Coverage analysis** → CoverageResult with FULL/PARTIAL/DECLINE decision
3. **Route:**
   - FULL/PARTIAL → proceed with base+fine KB
   - DECLINE + augmentation pipeline available → T3b generates predicates → merge into KB
   - DECLINE + augmentation fails (out-of-domain) → decline response
4. **Build AF** with active_ks (base+fine or base+fine+augmented)
5. **T3a retrieval** — parallel, with cross-linked section boosting via `t2b_source_sections`
6. **Contestation** — same vada/jalpa/vitanda logic as `forward()`
7. **Epistemic status + provenance + uncertainty** — same as `forward()`
8. **Synthesis** — same as `forward()`, but uses T3a chunks for `retrieved_prose`

**Return value additions:** `coverage` (CoverageResult dict), `augmentation` (dict or None)

**Original `forward()` unchanged** — no behavioral changes for existing callers.

#### 7. `anvikshiki_v4/__init__.py`

**New exports:** `compile_t2b`, `T2bResult`, `SemanticCoverageAnalyzer`, `CoverageResult`, `AugmentationPipeline`, `AugmentationResult`, `T3aRetriever`, `AugmentationOrigin`, `AugmentationMetadata`

---

## Architecture: Query-Time Data Flow

```
query
  │
  ▼
GroundingPipeline (5-layer defense)
  │ predicates, confidence
  ▼
SemanticCoverageAnalyzer (base + fine-grained KB, synonym table)
  │ CoverageResult: FULL / PARTIAL / DECLINE
  ▼
┌─────────────────────────────────────────────────────┐
│ ROUTING                                             │
│                                                     │
│ FULL/PARTIAL ──────────────────────► compile_t2()   │
│                                     (base + fine)   │
│                                                     │
│ DECLINE + in-domain ──► AugmentationPipeline        │
│                          │ (2 LLM calls)            │
│                          ▼                          │
│                       merge KB ──────► compile_t2() │
│                       (base+fine+aug)               │
│                                                     │
│ DECLINE + out-of-domain ──► decline response        │
└─────────────────────────────────────────────────────┘
  │                              │
  ▼                              ▼ (parallel)
ArgumentationFramework      T3aRetriever
  │ grounded semantics        │ prose chunks
  │ epistemic status          │ (boosted by T2b cross-link)
  ▼                           │
┌──────────────────────────────┘
│
▼
SynthesizeResponse (1 LLM call)
  │
  ▼
dspy.Prediction (response, sources, uncertainty, provenance,
                 violations, coverage, augmentation)
```

## Architecture: Compile-Time Data Flow

```
guide.md + business_expert.yaml
  │
  ▼
load_knowledge_store() ──► base KnowledgeStore (11 vyaptis)
  │
  ▼
compile_t2b()
  │ PredicateExtractionPipeline (Stages A-E)
  │   A: Extract predicates from guide sections
  │   B: Decompose vyaptis into sub-predicates
  │   C: Canonicalize + deduplicate → synonym_clusters
  │   D: Construct new vyaptis
  │   E: Validate (cycles + Datalog compile)
  │
  ▼
T2bResult
  ├── augmented_ks (base + fine-grained vyaptis, tagged GUIDE_EXTRACTED)
  ├── synonym_table (from Stage C clusters + token overlap)
  ├── source_sections (vyapti_id → chapter_ids, for T3a cross-linking)
  └── fine_grained_vyapti_ids
  │
  ▼
compile_t3(guide_text, augmented_ks) ──► (NetworkX graph, TextChunks)
  │
  ▼
T3aRetriever(chunks) ──► FAISS index (ready for query-time retrieval)
```

## Key Design Decisions

1. **T2b wraps existing pipeline** rather than reimplementing. The `PredicateExtractionPipeline` (1124 lines) already handles Stages A-E. T2b adds ~150 lines of framing: origin tagging, synonym table extraction, source section tracking.

2. **Origin on Vyapti, not on KnowledgeStore.** `Vyapti.augmentation_metadata` (Optional, default None) keeps augmented predicates as regular Vyaptis flowing through all downstream code unchanged. No special-casing needed in `t2_compiler_v4.py`, `argumentation.py`, or `contestation.py`.

3. **KB merge = `model_copy(deep=True)`** — no in-place mutation. Same pattern as `StageEValidator.validate_and_merge()`. Each query gets a fresh merged KB if augmentation triggers.

4. **T3a runs parallel** with T2 inference (independent retrieval). Sequential mode (informed by surviving predicates from AF) deferred — adds latency without clear quality improvement at this stage.

5. **Synonym table built at compile time** — stored on KnowledgeStore, used by coverage analyzer at query time. Built from two sources: Stage C synonym clusters + token-overlap mappings (>60% Jaccard) between new and base KB predicates.

6. **Confidence cap at 0.75** for all augmented vyaptis. Ensures generated predicates never outrank curated KB predicates in ASPIC+ defeat comparisons.

## Engine Factory: `engine_factory.py` (added 2026-03-05)

**Problem:** The e2e pipeline only loaded the YAML KB file but never loaded the actual guide markdown files through the compile chain. `compile_t2b()`, `compile_t3()`, and `T3aRetriever` existed but nothing wired them together. The e2e script (`e2e_trace_gemini.py`) hardcoded fake T2b output (V12/V13/V14) and fake SAMPLE_CHUNKS instead of processing real guide text.

**Fix:** Created `anvikshiki_v4/engine_factory.py` with:

- `load_guide_dir(guide_dir)` — loads `guide_ch*.md` files, infers chapter IDs from filenames
- `initialize_engine(kb_yaml_path, guide_dir)` — runs the full compile chain:
  1. `load_knowledge_store(yaml)` → base KB
  2. `load_guide_dir(dir)` → guide text dict
  3. `compile_t2b(ks, guide_text)` → augmented KB + synonym table + source sections
  4. `compile_t3(guide_text, augmented_ks)` → knowledge graph + text chunks
  5. `T3aRetriever(chunks)` → FAISS index
  6. `SemanticCoverageAnalyzer(augmented_ks, synonym_table)`
  7. `AugmentationPipeline(augmented_ks)` for T3b
  8. `GroundingPipeline(augmented_ks)` for grounding
  9. Returns `(AnvikshikiEngineV4, CompileArtifacts)`

**Updated `e2e_trace_gemini.py`:** Removed all hardcoded vyaptis and SAMPLE_CHUNKS. Now loads real guide text from `guides/business_expert/`, runs `compile_t2b()` and `compile_t3()` with the LLM, and traces the real output.

**Usage:**
```python
from anvikshiki_v4 import initialize_engine

engine, artifacts = initialize_engine(
    kb_yaml_path="anvikshiki_v4/data/business_expert.yaml",
    guide_dir="guides/business_expert",
)
result = engine.forward_with_coverage("How do unit economics work?")
```

## What's NOT Yet Built (from audit)

| Item | Status | Notes |
|------|--------|-------|
| A-04: Depth-aware coverage | Deferred | Needs depth signal beyond coverage_ratio |
| A-05: Fine-grained KB versioning/staleness | Deferred | Needs incremental update pipeline |
| A-07: T3b→T2 backprop evaluation | Deferred | Needs ablation study framework |
| Web search in T3b (v2) | Deferred | `AugmentationOrigin.WEB_SOURCED` ready, `evidence_search.py` TBD |
| Shadow KB persistence (v3) | Deferred | `shadow_kb.py` + SQLite TBD |
| Source reliability scoring (v4) | Deferred | `source_reliability.py` TBD |
| Framework templates (v5) | Deferred | `framework_templates.py` + YAML TBD |
| Domain-aware contrariness (III-02) | Deferred | Needs compiled contrariness relation, not `not_` prefix |
| Sequential T3a (informed by AF) | Deferred | T3a currently runs parallel |

## Test Verification

```
$ python -m pytest anvikshiki_v4/tests/ -v
249 passed, 4 skipped in 1.87s
```

All existing tests pass unchanged. The 4 skipped tests require live LLM connections (`@pytest.mark.llm`).

**Manual verification performed:**
- Schema extensions: Vyapti with augmentation_metadata round-trips correctly
- KnowledgeStore with fine_grained_vyapti_ids and synonym_table loads from YAML
- SemanticCoverageAnalyzer: exact/synonym/token matching verified with business_expert.yaml
- T3aRetriever: fallback retrieval, section boosting, cross-linked retrieval all work
- Engine initialization with all coverage routing components succeeds

## Reused Existing Code

| Reused From | Used In | What |
|-------------|---------|------|
| `predicate_extraction.PredicateExtractionPipeline` | `t2b_compiler.py` | Complete Stages A-E pipeline |
| `predicate_extraction._detect_cycles` | `kb_augmentation.py` | Cycle detection for augmented vyaptis |
| `predicate_extraction._enforce_snake_case` | `kb_augmentation.py` | Predicate name normalization |
| `predicate_extraction.StageEValidator` pattern | `kb_augmentation.py` | Datalog compile test |
| `grounding.OntologySnippetBuilder` | `kb_augmentation.py` | KB vocabulary builder |
| `query_refinement.CoverageAnalyzer._find_closest_predicate` pattern | `coverage.py` | Jaccard token overlap |
| `t3_compiler.TextChunk` | `t3a_retriever.py` | Chunk data structure |
| `t3_compiler.compile_t3` | compile-time flow | Graph + chunks construction |
