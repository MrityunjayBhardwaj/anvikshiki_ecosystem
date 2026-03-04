# Automated Predicate Extraction Pipeline — Design Document

## Context

The Anvikshiki Engine v4 has **23 predicates** for a 10-chapter business strategy domain — chapter-level abstractions that miss section/paragraph-level reasoning. Chapter 2 discusses LTV, CAC, contribution_margin, payback_period, but the only predicate is `positive_unit_economics`. The predicate vocabulary is manually authored in Stage 2 of the meta-prompt and never enriched from the generated guide text. This makes the engine **epistemically honest but strategically mute** — it qualifies confidence correctly but can't reason about the granular concepts the guide actually teaches.

The architecture (Datalog, T2 compiler, grounding, argumentation) handles hundreds of predicates. The bottleneck is KB authoring. This pipeline automates predicate extraction from guide text to close the gap.

## Research Summary

Best approaches (2024-2026 literature):
- **DSPy + Pydantic** structured extraction with MIPROv2 optimization (KGGen, ISWC 2024)
- **PARSE pattern** (Amazon 2025): schemas as learnable NL contracts — autonomous prompt optimization
- **Iterative refinement** (Nature 2025): 3-phase (extract → revise → validate) improves F1 by 5-15%
- **Seed ontology bootstrapping** (LLMs4OL 2024): existing vyaptis as seed, expand from text
- **Embedding-first dedup** (BELHD 2024): cosine clustering + LLM reranking for canonicalization
- **BERTScore** + F1 on realistic data (include zero-predicate passages) for evaluation

## Architecture Overview

```
Guide Text (ch01-ch10 markdown) + Existing KnowledgeStore (seed)
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Stage A: Extract Candidate Predicates          │  LLM calls: 1 per section
│  DSPy ChainOfThought(ExtractPredicates)         │  (~40-60 sections total)
│  Input: section text + seed ontology snippet     │
│  Output: CandidatePredicate[] with provenance    │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  Stage B: Hierarchical Decomposition            │  LLM calls: 1 per vyapti
│  DSPy ChainOfThought(DecomposeVyapti)           │  (~11 for business_expert)
│  Input: existing vyapti + guide excerpt          │
│  Output: PredicateNode tree (parent→children)    │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  Stage C: Canonicalize & Deduplicate            │  LLM calls: 0-1
│  Embedding clustering + LLM synonym resolution   │  (only if ambiguous clusters)
│  Output: clean vocabulary, synonym clusters       │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  Stage D: Construct New Vyaptis                 │  LLM calls: 1 per new vyapti
│  DSPy Refine(ConstructVyapti, N=3)              │  (~15-30 new vyaptis)
│  Output: ProposedVyapti[] with all fields        │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  Stage E: Validate & Merge (DETERMINISTIC)      │  LLM calls: 0
│  DAG cycle detection, Pydantic validation,       │
│  Datalog test-compilation, coverage metrics      │
│  Output: augmented KnowledgeStore YAML           │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  Stage F: Human-in-the-Loop Review              │  LLM calls: 0
│  YAML diff, accept/reject/modify per vyapti     │
│  Output: final approved KnowledgeStore           │
└─────────────────────────────────────────────────┘
```

## New Files

```
anvikshiki_v4/
  extraction_schema.py         # Pydantic models for all stages
  predicate_extraction.py      # Core pipeline: Stages A-E + orchestrator
  extraction_eval.py           # Evaluation metrics + MIPROv2 optimization
  extraction_hitl.py           # Stage F: human review CLI
  tests/
    test_predicate_extraction.py  # Unit + integration tests
    fixtures/
      guide_ch2_excerpt.md        # Test excerpt
      expected_predicates.yaml    # Gold standard
```

**No existing files are modified.** The pipeline is purely additive — it produces `KnowledgeStore` objects that pass existing Pydantic validation.

## Pydantic Models (extraction_schema.py)

### Stage A Output
```python
class ClaimType(str, Enum):
    CAUSAL = "causal"            # "X causes Y"
    CONDITIONAL = "conditional"  # "If X then Y"
    METRIC = "metric"            # "X is measured by Y"
    DEFINITIONAL = "definitional"
    SCOPE = "scope"              # "X holds only when Y"
    NEGATION = "negation"        # "X prevents Y"

class Provenance(BaseModel):
    chapter_id: str
    section_header: str = ""
    paragraph_index: int = 0
    sentence: str               # Exact source sentence
    confidence: float           # 0.0-1.0

class CandidatePredicate(BaseModel):
    name: str                   # snake_case
    description: str            # One-sentence NL
    claim_type: ClaimType
    provenance: Provenance
    related_existing_vyapti: Optional[str] = None
```

### Stage B Output
```python
class PredicateRelation(str, Enum):
    SUBSUMES = "subsumes"      # Parent generalizes child
    COMPOSES = "composes"      # Parent = AND of children
    ALTERNATIVE = "alternative" # Children are OR paths

class PredicateNode(BaseModel):
    predicate: str             # snake_case
    description: str
    parent: Optional[str] = None
    relation_to_parent: Optional[PredicateRelation] = None
    children: list[str] = []
    depth: int = 0             # 0=chapter, 1=section, 2=paragraph
    source_vyapti: Optional[str] = None
```

### Stage D Output
```python
class ProposedVyapti(BaseModel):
    id: str
    name: str
    statement: str
    causal_status: str          # validated against CausalStatus enum
    antecedents: list[str]
    consequent: str
    scope_conditions: list[str] = []
    scope_exclusions: list[str] = []
    confidence_existence: float  # 0.0-1.0
    confidence_formulation: float
    evidence_type: str = "observational"
    epistemic_status: str = "hypothesis"  # CONSERVATIVE default
    sources: list[str] = []
    parent_vyapti: Optional[str] = None
```

### Stage E Output
```python
class ValidationResult(BaseModel):
    is_valid: bool = False
    cycle_errors: list[str] = []
    orphan_predicates: list[str] = []
    datalog_errors: list[str] = []
    coverage_ratio: float = 0.0
```

### Pipeline Config
```python
class ExtractionConfig(BaseModel):
    ensemble_n: int = 3
    decomposition_max_depth: int = 2
    similarity_threshold: float = 0.85
    min_confidence: float = 0.3
    max_new_vyaptis_per_chapter: int = 15
    model_tier: str = "large"  # "large" for API, "small" for 3-7B local
```

## DSPy Signatures

### Stage A: ExtractPredicates
```python
class ExtractPredicates(dspy.Signature):
    """Extract domain predicates from instructional text. A predicate is a
    testable property. Look for causal claims, conditionals, metric relationships,
    scope conditions. Use ONLY snake_case. Return empty list if none found."""
    section_text: str = dspy.InputField()
    chapter_id: str = dspy.InputField()
    existing_predicates: str = dspy.InputField()  # seed ontology snippet
    domain_context: str = dspy.InputField()
    reasoning: str = dspy.OutputField()
    candidates: list[CandidatePredicate] = dspy.OutputField()
```

- **Small models**: `dspy.BestOfN(N=5)` with shorter sections (512 tokens)
- **Large models**: `dspy.Refine(N=3, threshold=0.4)` with longer sections (2000 tokens)
- **Reward function**: valid snake_case (0.20) + novel vs existing (0.15) + provenance quality (0.20) + non-empty (0.20) + reasoning present (0.15) + count cap (0.10)

### Stage B: DecomposeVyapti
```python
class DecomposeVyapti(dspy.Signature):
    """Given a high-level vyapti and guide text, identify sub-predicates that
    compose the vyapti's antecedents or consequent. What specific conditions,
    metrics, or sub-concepts does the text mention?"""
    vyapti_summary: str = dspy.InputField()
    guide_excerpt: str = dspy.InputField()
    stage_a_candidates: str = dspy.InputField()
    reasoning: str = dspy.OutputField()
    sub_predicates: list[PredicateNode] = dspy.OutputField()
    relation_type: str = dspy.OutputField()  # "composes" | "alternative" | "none"
```

### Stage C: ResolveSynonyms
```python
class ResolveSynonyms(dspy.Signature):
    """Identify synonym predicates and choose canonical names. Prefer specific
    over generic, consistent with existing naming, under 40 characters."""
    candidate_list: str = dspy.InputField()
    existing_naming_examples: str = dspy.InputField()
    synonym_groups: list[SynonymCluster] = dspy.OutputField()
    unique_predicates: list[str] = dspy.OutputField()
```

Algorithm: embedding cosine clustering (deterministic, cheap) → LLM only for ambiguous clusters.

### Stage D: ConstructVyapti
```python
class ConstructVyapti(dspy.Signature):
    """Construct a complete vyapti from a predicate relationship. Be conservative:
    epistemic_status='hypothesis' unless text provides strong evidence."""
    predicate_relationship: str = dspy.InputField()
    guide_evidence: str = dspy.InputField()
    existing_vyaptis_context: str = dspy.InputField()
    reference_bank: str = dspy.InputField()
    vyapti: ProposedVyapti = dspy.OutputField()
    reasoning: str = dspy.OutputField()
```

- Uses `dspy.Refine(N=3, threshold=0.5)` with reward penalizing overconfident extraction

## Stage E: Validation (Deterministic)

1. **DAG cycle detection**: DFS topological sort on predicate adjacency graph. Vyaptis participating in cycles are removed.
2. **Pydantic validation**: Each `ProposedVyapti` → `Vyapti(BaseModel)` from existing `schema.py`
3. **Datalog test-compilation**: Load augmented KB into `DatalogEngine`, add synthetic facts for all antecedents, call `evaluate()` — must terminate within safety bound
4. **Coverage ratio**: `(new_predicates - old_predicates) / new_predicates`

## Stage F: Human Review

- Renders YAML diff (additions only, since no existing vyaptis are modified)
- Per-vyapti accept/reject/modify decisions
- Apply decisions → final `KnowledgeStore`

## Iterative Refinement

```python
def run_iterative_extraction(pipeline, guide_text, max_passes=3):
    for pass_num in range(max_passes):
        augmented, validation, _ = pipeline(guide_text)
        if validation.coverage_ratio improvement < 2%: break
        pipeline = PredicateExtractionPipeline(augmented, config)  # use augmented as new seed
```

Re-extraction triggers: coverage < 30%, >50% zero-predicate sections, cycle removals.

## Evaluation Metrics (extraction_eval.py)

Composite metric (weights sum to 1.0):
| Component | Weight | Measures |
|-----------|--------|----------|
| Predicate precision | 0.20 | Extracted predicates in gold set |
| Predicate recall | 0.20 | Gold predicates that were extracted |
| Naming quality | 0.15 | Valid snake_case, not generic, <50 chars |
| Vyapti completeness | 0.15 | All required fields populated |
| DAG validity | 0.10 | No cycles introduced |
| Coverage ratio | 0.10 | Meaningful expansion over seed |
| Zero-section rate | 0.10 | Low missed-content rate |

BERTScore semantic similarity for soft matching (catches `ltv_above_cac` ≈ `ltv_exceeds_cac`).

MIPROv2 optimization: DSPy signature descriptions + few-shot examples evolve across runs (PARSE "schema as learnable NL contract" pattern).

## Integration Points (NO changes to existing files)

| Existing Module | Integration | How |
|----------------|-------------|-----|
| `schema.py` (Vyapti, KnowledgeStore) | Pipeline produces valid instances | Stage E constructs `Vyapti()` objects |
| `t2_compiler_v4.py` (compile_t2) | Stage E test-compiles augmented KB | Read-only call to verify arguments |
| `datalog_engine.py` (DatalogEngine) | Stage E validates predicates + compilation | Read-only `evaluate()` + `validate_predicates()` |
| `grounding.py` (OntologySnippetBuilder) | Automatically picks up new predicates | No change — reads from KnowledgeStore |
| `t3_compiler.py` (compile_t3) | Auto-detects new vyapti references | No change — pattern-matches vyapti names |

## Concrete Example: Ch2 Unit Economics

**Before**: 1 vyapti (V01), 2 predicates (`positive_unit_economics`, `value_creation`)

**After Stage A extracts from guide text**:
- `ltv_exceeds_cac`, `positive_contribution_margin`, `payback_within_runway`
- `maturity_mismatch`, `negative_unit_economics`, `economies_of_scale_real`

**After Stage B decomposes V01**:
```
positive_unit_economics (depth 0)
  ├── ltv_exceeds_cac (depth 1, composes)
  ├── positive_contribution_margin (depth 1, composes)
  └── payback_within_runway (depth 1, composes)
```

**After Stage D constructs new vyaptis**:
```yaml
V12:
  name: "LTV-CAC Viability Test"
  antecedents: ["ltv_exceeds_cac", "positive_contribution_margin"]
  consequent: "positive_unit_economics"
  epistemic_status: hypothesis  # conservative
  confidence: {existence: 0.85, formulation: 0.8}
```

**Result**: 11 → ~20 vyaptis, 23 → ~50 predicates. Section-level reasoning enabled.

## Key Design Decisions

1. **Flat predicates only** — Datalog compatibility, polynomial termination
2. **Conservative epistemic defaults** — all extracted vyaptis default to `hypothesis`, confidence ≤ 0.85
3. **Embedding-first dedup** — 60-80% cost reduction vs all-LLM
4. **No existing file modifications** — purely additive pipeline
5. **Stage E fully deterministic** — reproducible validation
6. **Seed ontology bootstrapping** — existing vyaptis constrain extraction, preventing drift

## Verification

1. **Unit tests**: Schema validation, snake_case enforcement, cycle detection (no LLM needed)
2. **Stage E integration**: Load `business_expert.yaml`, propose valid/invalid vyaptis, verify accept/reject
3. **Full pipeline**: Run against Ch2 excerpt, compare extracted predicates to hand-authored gold standard
4. **Regression**: Augmented KB must pass all existing `test_business_expert.py` tests unchanged
5. **Coverage metric**: Verify predicate count increases from ~23 to ~40-60 for business domain
