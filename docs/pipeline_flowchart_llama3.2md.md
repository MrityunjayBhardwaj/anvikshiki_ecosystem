# Ānvīkṣikī Engine — End-to-End Pipeline Flowchart

> Complete trace from raw guide text + seed KB through predicate extraction,
> compilation, grounding, argumentation, and final response synthesis.
> Covers both the **offline KB enrichment pipeline** and the **online query pipeline**.

---

## Master Architecture Overview

```
═══════════════════════════════════════════════════════════════════════════
                     OFFLINE: KB ENRICHMENT PIPELINE
                     (runs once per guide version)
═══════════════════════════════════════════════════════════════════════════

  Guide Text (ch01-ch10 markdown)
  + Seed KnowledgeStore YAML (11 vyāptis, 23 predicates)
         │
         ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │              PREDICATE EXTRACTION PIPELINE                          │
  │                                                                     │
  │   Stage A: Extract Candidate Predicates (LLM: 1/section)           │
  │       ▼                                                             │
  │   Stage B: Hierarchical Decomposition  (LLM: 1/vyāpti)            │
  │       ▼                                                             │
  │   Stage C: Canonicalize & Deduplicate   (embeddings + LLM)         │
  │       ▼                                                             │
  │   Stage D: Construct New Vyāptis        (LLM: 1/vyāpti)           │
  │       ▼                                                             │
  │   Stage E: Validate & Merge             (deterministic)            │
  │       ▼                                                             │
  │   Stage F: Human-in-the-Loop Review     (interactive CLI)          │
  └────────────────────────────┬────────────────────────────────────────┘
                               │
                    Augmented KnowledgeStore YAML
                    (~20 vyāptis, ~50 predicates)
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
  ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
  │ T2 Compiler │     │ T3 Compiler  │     │  MIPROv2     │
  │ KB → AF     │     │ KB+Guide →   │     │  Optimizer   │
  │ (at query)  │     │ GraphRAG     │     │  (optional)  │
  └─────────────┘     └──────────────┘     └──────────────┘


═══════════════════════════════════════════════════════════════════════════
                     ONLINE: QUERY PIPELINE
                     (runs per user query, ~3.8s)
═══════════════════════════════════════════════════════════════════════════

  User Query (natural language)
  + Augmented KnowledgeStore (from offline pipeline)
  + Retrieved Chunks (from T3 GraphRAG)
         │
         ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Stage 0: Request Ingestion & Route Selection                       │
  │  Stage 1: KB Loading (cached)                                       │
  │  Stage 2: Ontology Snippet Construction (Layer 1)                   │
  │  Stage 3: LLM Grounding (NL → predicates)                          │
  │  Stage 4: T2 Compilation (facts + rules → AF)                      │
  │  Stage 5: Contestation (vāda/jalpa/vitaṇḍā)                       │
  │  Stage 6: Epistemic Status Derivation                               │
  │  Stage 7: Provenance Extraction                                     │
  │  Stage 8: Uncertainty Decomposition                                 │
  │  Stage 9: Violation Detection (hetvābhāsa)                         │
  │  Stage 10: LLM Synthesis (calibrated response)                      │
  │  Stage 11: Response Assembly & Persistence                          │
  └─────────────────────────────────────────────────────────────────────┘
         │
         ▼
  Final JSON Response (with epistemic qualification,
  provenance, uncertainty decomposition, violations)
```

---

# PART 1: OFFLINE KB ENRICHMENT PIPELINE

> Transforms a seed KB (manually authored, ~23 predicates) into a rich KB
> (~50+ predicates) by extracting domain knowledge from guide text.
> Runs once per guide version. All outputs are purely additive — no
> existing vyāptis are modified.

---

## STAGE A: Extract Candidate Predicates

**What:** Scan each section of guide text and extract testable domain predicates — causal claims, conditionals, metrics, scope conditions, and negations.

**Why:** The seed KB has chapter-level abstractions only. Chapter 2 discusses LTV, CAC, contribution margin, payback period, but the only predicate is `positive_unit_economics`. Stage A extracts the section-level concepts the guide actually teaches.

**Processing:** 1 LLM call per section (~40-60 sections total). DSPy `ChainOfThought(ExtractPredicates)` with reward-scored selection.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ For each guide section:                                          │
│   section_text:        "### 2.1 The LTV-CAC Relationship         │
│                         The most fundamental equation in startup  │
│                         economics: LTV must exceed CAC..."        │
│   chapter_id:          "ch02"                                     │
│   existing_predicates: "positive_unit_economics, value_creation,  │
│                         binding_constraint_identified, ..."       │
│   domain_context:      "CRAFT — business strategy domain"         │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Processing ▼

1. _split_into_sections(guide_text, max_tokens=512)
   Splits at ### boundaries, respects token limits.
   Ch2 → 6 sections (2.1 through 2.6)

2. For each section, DSPy ChainOfThought(ExtractPredicates):
   - Receives section text + seed ontology snippet
   - Extracts CandidatePredicate[] with:
     name (snake_case), description, claim_type, provenance

3. Reward function scores candidates (sum to 1.0):
   +0.20  valid snake_case format
   +0.15  novel (not in existing predicates)
   +0.20  provenance quality (exact sentence cited)
   +0.20  non-empty extraction
   +0.15  reasoning chain present
   +0.10  count within cap (≤15/chapter)

4. _enforce_snake_case() normalizes all names
5. Filter: min_confidence ≥ 0.3

┌─ OUTPUT: StageAOutput ───────────────────────────────────────────┐
│ candidates: [                                                    │
│   CandidatePredicate(                                            │
│     name="ltv_exceeds_cac",                                      │
│     description="Lifetime value exceeds customer acquisition     │
│                  cost",                                           │
│     claim_type=ClaimType.METRIC,                                 │
│     provenance=Provenance(                                       │
│       chapter_id="ch02",                                         │
│       section_header="2.1 The LTV-CAC Relationship",             │
│       sentence="LTV must exceed CAC",                            │
│       confidence=0.92                                            │
│     ),                                                           │
│     related_existing_vyapti="V01"                                │
│   ),                                                             │
│   CandidatePredicate(                                            │
│     name="high_arpu", ...                                        │
│   ),                                                             │
│   CandidatePredicate(                                            │
│     name="high_retention_rate", ...                               │
│   ),                                                             │
│   CandidatePredicate(                                            │
│     name="positive_contribution_margin", ...                      │
│   ),                                                             │
│   CandidatePredicate(                                            │
│     name="payback_within_runway", ...                             │
│   ),                                                             │
│   CandidatePredicate(                                            │
│     name="economies_of_scale_real", ...                           │
│   ),                                                             │
│   CandidatePredicate(                                            │
│     name="negative_unit_economics", ...                           │
│   ),                                                             │
│   CandidatePredicate(                                            │
│     name="maturity_mismatch", ...                                 │
│   ),                                                             │
│   ... (~14 candidates from Ch2)                                  │
│ ]                                                                │
│ sections_processed: 6                                            │
│ empty_sections: 0                                                │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `predicate_extraction.py:ExtractPredicates`, `predicate_extraction.py:_stage_a()`

**Claim Types (6-class taxonomy):**
| Type | Pattern | Example |
|------|---------|---------|
| CAUSAL | "X causes Y" | economies_of_scale → lower_per_unit_cost |
| CONDITIONAL | "If X then Y" | payback_within_runway → sustainable_growth |
| METRIC | "X is measured by Y" | ltv_exceeds_cac (LTV > CAC ratio) |
| DEFINITIONAL | "X is defined as Y" | contribution_margin = revenue - variable_costs |
| SCOPE | "X holds only when Y" | maturity_mismatch (long-term model, short-cycle market) |
| NEGATION | "X prevents Y" | negative_unit_economics (each customer destroys value) |

---

## STAGE B: Hierarchical Decomposition

**What:** For each existing vyāpti, identify sub-predicates that compose its antecedents or consequent. Builds a predicate hierarchy (depth 0 = chapter, depth 1 = section, depth 2 = paragraph).

**Why:** The existing V01 says `positive_unit_economics → value_creation`. But the guide text reveals that positive_unit_economics is actually *composed of* three testable conditions: `ltv_exceeds_cac AND positive_contribution_margin AND payback_within_runway`. Stage B captures this compositional structure.

**Processing:** 1 LLM call per existing vyāpti (~11 for business_expert). DSPy `ChainOfThought(DecomposeVyapti)`.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ For each existing vyāpti:                                        │
│   vyapti_summary:    "V01: positive_unit_economics →              │
│                       value_creation (empirical, established)"    │
│   guide_excerpt:     (relevant chapter text for this vyāpti)     │
│   stage_a_candidates: (candidates related to this vyāpti)        │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Processing ▼

DSPy ChainOfThought(DecomposeVyapti):
  LLM identifies sub-predicates from guide text
  Classifies relation: COMPOSES | ALTERNATIVE | SUBSUMES

  V01 decomposition example:
    positive_unit_economics is composed of:
      ltv_exceeds_cac (depth 1, composes)
      positive_contribution_margin (depth 1, composes)
      payback_within_runway (depth 1, composes)

┌─ OUTPUT: StageBOutput ───────────────────────────────────────────┐
│ decompositions: {                                                │
│   "V01": [                                                       │
│     PredicateNode(                                               │
│       predicate="ltv_exceeds_cac",                               │
│       parent="positive_unit_economics",                          │
│       relation_to_parent=COMPOSES,                               │
│       depth=1,                                                   │
│       source_vyapti="V01"                                        │
│     ),                                                           │
│     PredicateNode(                                               │
│       predicate="positive_contribution_margin",                  │
│       parent="positive_unit_economics",                          │
│       relation_to_parent=COMPOSES,                               │
│       depth=1,                                                   │
│       source_vyapti="V01"                                        │
│     ),                                                           │
│     PredicateNode(                                               │
│       predicate="payback_within_runway",                         │
│       parent="positive_unit_economics",                          │
│       relation_to_parent=COMPOSES,                               │
│       depth=1,                                                   │
│       source_vyapti="V01"                                        │
│     )                                                            │
│   ]                                                              │
│ }                                                                │
│                                                                  │
│ Predicate hierarchy:                                             │
│   positive_unit_economics (depth 0)                              │
│     ├── ltv_exceeds_cac (depth 1, composes)                      │
│     ├── positive_contribution_margin (depth 1, composes)         │
│     └── payback_within_runway (depth 1, composes)                │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `predicate_extraction.py:DecomposeVyapti`, `predicate_extraction.py:_stage_b()`

**Relation Types:**
| Relation | Meaning | Datalog Pattern |
|----------|---------|-----------------|
| COMPOSES | Parent = AND of children | parent :- child1, child2, child3. |
| ALTERNATIVE | Children are OR paths | parent :- child1. parent :- child2. |
| SUBSUMES | Parent generalizes child | (no new rule — child implies parent) |

---

## STAGE C: Canonicalize & Deduplicate

**What:** Merge equivalent predicates from Stages A and B using embedding similarity clustering, then resolve ambiguous clusters with LLM synonym resolution.

**Why:** Stage A may extract `ltv_above_cac` from one section and `ltv_exceeds_cac` from another. Stage B may produce `positive_cm` while Stage A found `positive_contribution_margin`. Without deduplication, the vocabulary bloats and Datalog rules fragment across synonyms.

**Processing:** Embedding-first (0 LLM calls for unambiguous clusters), LLM only for ambiguous cases (cosine similarity between 0.75-0.95). ~60-80% cost reduction vs all-LLM dedup.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ All candidates from Stage A + Stage B decompositions             │
│ Existing predicate names from seed KB                            │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Processing ▼

1. Collect all unique predicate names
2. Compute embeddings (dspy.retrievers.Embeddings)
3. Cosine similarity matrix → cluster at threshold=0.85
4. Unambiguous clusters (similarity > 0.95):
     Merge automatically → pick the name matching existing convention
5. Ambiguous clusters (similarity 0.75-0.95):
     DSPy ResolveSynonyms(candidate_list, existing_naming_examples)
     LLM picks canonical name

   Example cluster:
     {ltv_above_cac, ltv_exceeds_cac, ltv_greater_than_cac}
     → canonical: ltv_exceeds_cac (matches existing naming style)

6. Build rename map: old_name → canonical_name
7. Apply renames to all Stage A/B outputs

┌─ OUTPUT: StageCOutput ───────────────────────────────────────────┐
│ synonym_clusters: [                                              │
│   SynonymCluster(                                                │
│     canonical="ltv_exceeds_cac",                                 │
│     synonyms=["ltv_above_cac", "ltv_greater_than_cac"]           │
│   )                                                              │
│ ]                                                                │
│ unique_predicates: [                                             │
│   "ltv_exceeds_cac",                                             │
│   "high_arpu",                                                   │
│   "high_retention_rate",                                         │
│   "positive_contribution_margin",                                │
│   "payback_within_runway",                                       │
│   "short_payback_period",                                        │
│   "economies_of_scale_real",                                     │
│   "imagined_economies_of_scale",                                 │
│   "network_effects_present",                                     │
│   "negative_unit_economics",                                     │
│   "unit_economics_death_spiral",                                 │
│   "maturity_mismatch",                                           │
│   "cohort_ltv_declining",                                        │
│   "gross_margin_not_contribution_margin"                         │
│ ]                                                                │
│ rename_map: {"ltv_above_cac": "ltv_exceeds_cac", ...}           │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `predicate_extraction.py:ResolveSynonyms`, `predicate_extraction.py:_stage_c()`

---

## STAGE D: Construct New Vyāptis

**What:** From the deduplicated predicates and their relationships (from Stages A-C), construct complete vyāpti objects with all required fields: antecedents, consequent, scope conditions, epistemic status, confidence scores, and source references.

**Why:** Raw predicates aren't useful until they're connected by inference rules. The guide text says "if LTV exceeds CAC AND contribution margin is positive, then unit economics are positive." Stage D formalizes this as a vyāpti that the T2 compiler can use for forward chaining.

**Processing:** 1 LLM call per new vyāpti (~15-30 new vyāptis). DSPy `Refine(N=3, threshold=0.5)` with reward penalizing overconfident extraction.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ For each predicate relationship identified:                      │
│   predicate_relationship: "ltv_exceeds_cac AND                   │
│     positive_contribution_margin → positive_unit_economics"      │
│   guide_evidence:          (relevant guide excerpt)              │
│   existing_vyaptis_context: (V01 summary for context)            │
│   reference_bank:          (relevant academic sources)           │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Processing ▼

DSPy Refine(N=3, threshold=0.5):
  Generates 3 candidate vyāptis, scores each, picks best.

  Reward penalizes overconfidence:
    epistemic_status MUST be "hypothesis" (conservative default)
    confidence_existence ≤ 0.85 (cap)
    confidence_formulation ≤ 0.85 (cap)
    All required fields populated
    Antecedents ⊆ known predicates
    No circular references

┌─ OUTPUT: StageDOutput ───────────────────────────────────────────┐
│ new_vyaptis: [                                                   │
│   ProposedVyapti(                                                │
│     id="V12",                                                    │
│     name="LTV-CAC Viability Test",                               │
│     statement="When LTV exceeds CAC and contribution margin      │
│       is positive, unit economics are positive",                 │
│     causal_status="empirical",                                   │
│     antecedents=["ltv_exceeds_cac",                              │
│                   "positive_contribution_margin"],                │
│     consequent="positive_unit_economics",                        │
│     scope_conditions=["commercial_enterprise"],                  │
│     scope_exclusions=["subsidized_entity"],                      │
│     confidence_existence=0.85,                                   │
│     confidence_formulation=0.80,                                 │
│     evidence_type="observational",                               │
│     epistemic_status="hypothesis",  ← CONSERVATIVE default      │
│     decay_risk="moderate",                                       │
│     sources=["src_hbs_unit_economics"],                          │
│     parent_vyapti="V01"                                          │
│   ),                                                             │
│   ProposedVyapti(                                                │
│     id="V13",                                                    │
│     name="Unit Economics Death Spiral",                           │
│     antecedents=["negative_unit_economics"],                     │
│     consequent="unit_economics_death_spiral",                    │
│     epistemic_status="hypothesis",                               │
│     confidence_existence=0.80,                                   │
│     ...                                                          │
│   ),                                                             │
│   ProposedVyapti(                                                │
│     id="V14",                                                    │
│     name="Maturity Mismatch Warning",                            │
│     antecedents=["maturity_mismatch"],                           │
│     consequent="negative_unit_economics",                        │
│     ...                                                          │
│   ),                                                             │
│   ... (~15-30 new vyāptis total)                                 │
│ ]                                                                │
│ refinement_vyaptis: [                                            │
│   (existing vyāptis with updated sub-predicate structure)        │
│ ]                                                                │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `predicate_extraction.py:ConstructVyapti`, `predicate_extraction.py:_stage_d()`

---

## STAGE E: Validate & Merge (Deterministic)

**What:** Validate all proposed vyāptis against five invariants, then merge into the augmented KnowledgeStore. Zero LLM calls — fully deterministic and reproducible.

**Why:** LLM-generated vyāptis can introduce cycles, reference non-existent predicates, or fail Pydantic validation. Stage E is the safety gate that ensures the augmented KB is formally sound before any human sees it.

**Processing:** Pure computation — graph algorithms + Pydantic validation + Datalog test-compilation.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ Original KnowledgeStore (seed)                                   │
│ StageDOutput (proposed vyāptis)                                  │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Processing ▼

Step E1: DAG Cycle Detection
  Build predicate adjacency graph from all vyāptis (old + new)
  DFS topological sort:
    If cycle found → remove offending vyāptis
    Guarantees: Datalog stratifiability → unique minimal model

  Example check:
    V12: ltv_exceeds_cac → positive_unit_economics  ✓
    V14: maturity_mismatch → negative_unit_economics ✓
    V13: negative_unit_economics → death_spiral       ✓
    No cycles detected.

Step E2: Pydantic Validation
  For each ProposedVyapti → convert to schema.Vyapti:
    CausalStatus(proposed.causal_status)   ← must be valid enum
    EpistemicStatus(proposed.epistemic_status) ← must be valid
    Confidence(existence, formulation)     ← must be in [0, 1]
    All antecedents must be known predicates

Step E3: Datalog Test-Compilation
  Load augmented KB into DatalogEngine
  Add synthetic facts for ALL antecedent predicates
  Call evaluate() with safety bound (MAX_ITERATIONS=100)
  Must terminate within bound → guarantees polynomial evaluation

Step E4: Coverage Ratio
  coverage = (new_predicates - old_predicates) / new_predicates
  23 old → 50 new → coverage = (50-23)/50 = 54%

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ ValidationResult(                                                │
│   is_valid=True,                                                 │
│   cycle_errors=[],                                               │
│   orphan_predicates=[],                                          │
│   datalog_errors=[],                                             │
│   coverage_ratio=0.54                                            │
│ )                                                                │
│                                                                  │
│ augmented_ks: KnowledgeStore(                                    │
│   vyaptis: {V01..V11} ∪ {V12..V25}  (original + new)            │
│   predicates: 23 → ~50                                           │
│   All Pydantic-validated                                         │
│   All Datalog-compilable                                         │
│   DAG-acyclic                                                    │
│ )                                                                │
└──────────────────────────────────────────────────────────────────┘
```

**Five Invariants Enforced:**

| Invariant | What | How Checked |
|-----------|------|-------------|
| I1: Flat predicates | No function symbols, no nested terms | snake_case regex + no parens in names |
| I2: DAG acyclicity | No cycles in predicate dependency graph | DFS topological sort |
| I3: Schema conformance | All fields valid, enums correct | Pydantic BaseModel validation |
| I4: Datalog compatibility | Augmented KB compiles and terminates | DatalogEngine.evaluate() with safety bound |
| I5: Monotone enrichment | No existing vyāptis modified or deleted | set difference check: old ⊆ new |

**Files:** `predicate_extraction.py:_stage_e()`, `predicate_extraction.py:_detect_cycles()`

---

## STAGE F: Human-in-the-Loop Review

**What:** Present each proposed vyāpti as a YAML diff for human review. Accept, reject, or mark for modification.

**Why:** LLM extraction is imperfect. A human domain expert reviews each proposed vyāpti to catch: incorrect causal relationships, wrong scope conditions, missing exclusions, inappropriate confidence levels. This is the final quality gate.

**Processing:** Interactive CLI — no LLM calls.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ Original KnowledgeStore                                          │
│ Augmented KnowledgeStore                                         │
│ StageDOutput (proposed vyāptis)                                  │
│ ValidationResult                                                 │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Interactive Review ▼

Predicate Extraction Review: 14 proposed vyaptis

Validation Summary:
  Valid: True
  Coverage ratio: 54.0%

============================================================
  Proposed Vyapti 1/14: V12
============================================================
  + id: V12
  + name: LTV-CAC Viability Test
  + statement: When LTV exceeds CAC and contribution margin
  +   is positive, unit economics are positive
  + causal_status: empirical
  + antecedents:
  +   - ltv_exceeds_cac
  +   - positive_contribution_margin
  + consequent: positive_unit_economics
  + epistemic_status: hypothesis
  + confidence:
  +   existence: 0.85
  +   formulation: 0.80

  Confidence: existence=0.85, formulation=0.80
  Epistemic: hypothesis

  [a]ccept  [r]eject  [m]odify  [q]uit
  Decision: a
  -> Accepted

============================================================
  Proposed Vyapti 2/14: V13
============================================================
  ...

                    ▼ Apply Decisions ▼

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ Final approved KnowledgeStore:                                   │
│   Accepted:  12 vyāptis                                          │
│   Rejected:  1 vyāpti                                            │
│   Modified:  1 vyāpti                                            │
│                                                                  │
│ Exported to: approved_kb.yaml                                    │
│                                                                  │
│ Summary: {accepted: 12, rejected: 1, modified: 1, pending: 0}   │
└──────────────────────────────────────────────────────────────────┘
```

**Usage:**
```bash
# Interactive CLI
python -m anvikshiki_v4.extraction_hitl \
  --kb anvikshiki_v4/data/business_expert.yaml \
  --proposed extraction_output.yaml \
  --output approved_kb.yaml

# Programmatic (batch)
reviewer = HITLReviewer(original_ks, augmented_ks, stage_d, validation)
approved = reviewer.review_batch({"V12": ACCEPT, "V13": ACCEPT, "V14": REJECT})
```

**Files:** `extraction_hitl.py:HITLReviewer`

---

## Iterative Refinement (Optional)

**What:** Re-run Stages A-E using the augmented KB as the new seed, extracting even finer-grained predicates in subsequent passes.

**Why:** First pass may miss predicates that only become apparent in context of newly extracted ones. Coverage plateau detection stops iteration when marginal gain < 2%.

```
┌─ ITERATIVE LOOP ─────────────────────────────────────────────────┐
│                                                                  │
│  Pass 1: seed KB (23 predicates) → augmented KB (50 predicates)  │
│    coverage gain: 54%                                            │
│                                                                  │
│  Pass 2: augmented KB (50) → further augmented (58)              │
│    coverage gain: 14%                                            │
│                                                                  │
│  Pass 3: further augmented (58) → final (60)                     │
│    coverage gain: 3% → below 2% relative improvement?            │
│    If gains diminish → STOP                                      │
│                                                                  │
│  Re-extraction triggers:                                         │
│    - Coverage < 30%                                              │
│    - >50% zero-predicate sections                                │
│    - Cycle removals invalidated significant branches             │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `predicate_extraction.py:run_iterative_extraction()`

---

## T3 Compilation (Graph-Structured Retrieval)

**What:** Build a NetworkX knowledge graph + chunked text corpus from the guide text anchored to the augmented KB's vyāptis, hetvābhāsas, and concepts.

**Why:** The query pipeline needs to retrieve relevant prose passages at query time. T3 creates rich metadata on each text chunk: which vyāptis it discusses, which fallacies it illustrates, what its epistemic status is. With the augmented KB, T3 can now anchor to ~50 predicates instead of ~23.

**Processing:** Pure computation — no LLM calls. Benefits automatically from richer KB.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ Guide text (ch01-ch10 markdown)                                  │
│ Augmented KnowledgeStore (from predicate extraction pipeline)    │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Processing ▼

compile_t3(guide_text, augmented_ks):

  1. _build_knowledge_graph(ks):
     - Vyāpti nodes (V01-V25): type, epistemic_status, confidence
     - Concept nodes from dependency_graph
     - Hetvābhāsa nodes (H01-H08)
     - Chapter nodes with prerequisites
     - Threshold concept nodes
     - Edges: prerequisite_for, introduces, forward_reference,
              monitors, reorganizes

  2. _chunk_guide_text(guide_text, ks):
     For each section of each chapter:
     - _detect_vyapti_refs(): now matches ~25 vyāptis (was ~11)
     - _detect_hetvabhasa_refs(): matches H01-H08
     - _detect_concept_refs(): matches dependency graph concepts
     - Attach epistemic_status from chapter fingerprint

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ graph: nx.DiGraph                                                │
│   Nodes: ~80 (vyāptis + concepts + hetvābhāsas + chapters)      │
│   Edges: ~150 (prerequisite, introduces, monitors, etc.)         │
│                                                                  │
│ chunks: list[TextChunk]                                          │
│   ~60 chunks with rich metadata:                                 │
│   TextChunk(                                                     │
│     chunk_id="ch02_s001",                                        │
│     chapter_id="ch02",                                           │
│     text="### 2.1 The LTV-CAC Relationship...",                  │
│     vyapti_anchors=["V01", "V12"],  ← now includes new V12      │
│     concept_anchors=["unit_economics", "ltv_cac"],               │
│     epistemic_status="established",                              │
│     difficulty_tier="intermediate"                               │
│   )                                                              │
└──────────────────────────────────────────────────────────────────┘
```

**Impact of Predicate Extraction:** Before enrichment, T3 could anchor text to ~11 vyāptis. After enrichment, it anchors to ~25 vyāptis, creating denser retrieval pathways and more precise chunk selection at query time.

**Files:** `t3_compiler.py:compile_t3()`

---

## Evaluation & Optimization (Optional)

**What:** Score extraction quality using a composite metric and optimize DSPy signatures with MIPROv2.

**Why:** The extraction pipeline's DSPy signatures (ExtractPredicates, DecomposeVyapti, ConstructVyapti) can be optimized via MIPROv2 to improve extraction quality over time.

```
┌─ EVALUATION METRIC (weighted sum = 1.0) ─────────────────────────┐
│ Predicate precision:     0.20   (extracted ∩ gold / extracted)   │
│ Predicate recall:        0.20   (extracted ∩ gold / gold)        │
│ Naming quality:          0.15   (valid snake_case, <50 chars)    │
│ Vyapti completeness:     0.15   (all required fields populated)  │
│ DAG validity:            0.10   (no cycles introduced)           │
│ Coverage ratio:          0.10   (meaningful expansion over seed) │
│ Zero-section rate:       0.10   (low missed-content rate)        │
│                                                                  │
│ Soft matching: token_overlap() for approximate predicate match   │
│   ltv_above_cac ≈ ltv_exceeds_cac → score 0.67 (not zero)       │
└──────────────────────────────────────────────────────────────────┘

MIPROv2 optimization:
  DSPy signature descriptions + few-shot examples evolve
  across optimization runs (PARSE "schema as learnable NL contract")
```

**Files:** `extraction_eval.py:ExtractionEvaluator`, `extraction_eval.py:optimize_pipeline()`

---

# PART 2: ONLINE QUERY PIPELINE

> Runs per user query. Uses the augmented KnowledgeStore produced
> by Part 1. The query pipeline is unchanged from the original
> architecture — it automatically benefits from the richer predicate
> vocabulary and additional vyāptis.

---

## STAGE 0: Request Ingestion & Route Selection

**What:** Accept HTTP request, authenticate, configure DSPy LM, determine execution path.

**Processing:** Pure Python — no LLM calls.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ POST /api/queries/                                               │
│ {                                                                │
│   kb_id: "3aab9fef-...",                                         │
│   query: "Does a company with strong LTV-CAC ratio and          │
│           positive contribution margin have viable               │
│           unit economics?",                                      │
│   contestation_mode: "vada",                                     │
│   retrieved_chunks: [chunk1, chunk2]                              │
│ }                                                                │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Route Selection ▼

  query_facts provided? ──YES──▶ Path A: execute_symbolic (1 LLM)
        │ NO
        ▼
  is_small_model? ────YES──▶ Path B: lightweight grounding (2 LLM)
        │ NO
        ▼
  Path C: full N=5 grounding (5-9 LLM calls)

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ Route: Path B (lightweight grounding)                            │
│ LM: Llama-3.2-3B-Instruct-4bit via MLX                          │
└──────────────────────────────────────────────────────────────────┘
```

---

## STAGE 1: KB Loading

**What:** Load the augmented KnowledgeStore YAML. Cached per `kb_id`.

**Impact of Predicate Extraction:** The loaded KB now has ~25 vyāptis and ~50 predicates (vs 11 vyāptis and 23 predicates in the seed). All downstream stages benefit from this richer vocabulary.

```
┌─ OUTPUT: Augmented KnowledgeStore ───────────────────────────────┐
│ domain_type: CRAFT                                               │
│                                                                  │
│ vyaptis (25 rules):                                              │
│   V01: positive_unit_economics → value_creation                  │
│         (empirical, established, conf=0.95×0.9)                  │
│   V12: ltv_exceeds_cac + positive_contribution_margin            │
│         → positive_unit_economics                                │
│         (empirical, hypothesis, conf=0.85×0.80)    ← NEW         │
│   V13: negative_unit_economics → unit_economics_death_spiral     │
│         (empirical, hypothesis, conf=0.80×0.75)    ← NEW         │
│   V14: maturity_mismatch → negative_unit_economics               │
│         (empirical, hypothesis, conf=0.80×0.70)    ← NEW         │
│   ... (V02-V11 unchanged, V15-V25 new)                           │
│                                                                  │
│ predicates: ~50 (was 23)                                         │
│   NEW: ltv_exceeds_cac, positive_contribution_margin,            │
│        payback_within_runway, short_payback_period,              │
│        economies_of_scale_real, imagined_economies_of_scale,     │
│        network_effects_present, negative_unit_economics,         │
│        unit_economics_death_spiral, maturity_mismatch,           │
│        cohort_ltv_declining, high_arpu, high_retention_rate,     │
│        gross_margin_not_contribution_margin, ...                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## STAGE 2: Ontology Snippet Construction (Layer 1)

**What:** Build constrained vocabulary prompt from the augmented KB.

**Impact of Predicate Extraction:** The ontology snippet now lists ~50 valid predicates instead of ~23. The LLM has a richer vocabulary to map the query to, enabling more precise grounding.

```
┌─ OUTPUT: ontology_snippet (string) ──────────────────────────────┐
│ VALID PREDICATES — use ONLY these:                               │
│                                                                  │
│ RULE V01: The Value Equation                                     │
│   IF: positive_unit_economics                                    │
│   THEN: value_creation                                           │
│   ...                                                            │
│                                                                  │
│ RULE V12: LTV-CAC Viability Test                      ← NEW     │
│   IF: ltv_exceeds_cac, positive_contribution_margin              │
│   THEN: positive_unit_economics                                  │
│   SCOPE: commercial_enterprise                                   │
│   EXCLUDES: subsidized_entity                                    │
│                                                                  │
│ RULE V13: Unit Economics Death Spiral                  ← NEW     │
│   IF: negative_unit_economics                                    │
│   THEN: unit_economics_death_spiral                              │
│   ...                                                            │
│                                                                  │
│ ALL VALID PREDICATE NAMES:                                       │
│   - binding_constraint_identified(Entity)                        │
│   - cohort_ltv_declining(Entity)                      ← NEW     │
│   - economies_of_scale_real(Entity)                   ← NEW     │
│   - high_arpu(Entity)                                 ← NEW     │
│   - high_retention_rate(Entity)                       ← NEW     │
│   - ltv_exceeds_cac(Entity)                           ← NEW     │
│   - maturity_mismatch(Entity)                         ← NEW     │
│   - negative_unit_economics(Entity)                   ← NEW     │
│   - positive_contribution_margin(Entity)              ← NEW     │
│   - positive_unit_economics(Entity)                              │
│   - unit_economics_death_spiral(Entity)               ← NEW     │
│   - value_creation(Entity)                                       │
│   ... (50 total predicates)                                      │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `grounding.py:OntologySnippetBuilder.build()`

---

## STAGE 3: LLM Grounding (NL → Predicates)

**What:** Translate the natural language query into structured predicates using the constrained vocabulary.

**Impact of Predicate Extraction:** The query "Does a company with strong LTV-CAC ratio and positive contribution margin have viable unit economics?" now maps to `ltv_exceeds_cac` and `positive_contribution_margin` directly — predicates that didn't exist in the seed KB. Before enrichment, the grounding would collapse everything to just `positive_unit_economics`.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ query:           "Does a company with strong LTV-CAC ratio and   │
│                   positive contribution margin have viable        │
│                   unit economics?"                                │
│ ontology_snippet: (50 predicates, 25 rules — from Stage 2)      │
│ domain_type:     "CRAFT"                                         │
└──────────────────────────────────────────────────────────────────┘

                    ▼ LLM Grounding (1 call) ▼

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ predicates: [                                                    │
│   "ltv_exceeds_cac(acme)",              ← WAS IMPOSSIBLE before │
│   "positive_contribution_margin(acme)"  ← WAS IMPOSSIBLE before │
│ ]                                                                │
│ relevant_vyaptis: ["V12", "V01"]                                 │
│                                                                  │
│ BEFORE predicate extraction:                                     │
│   predicates: ["positive_unit_economics(acme)"]   (only option)  │
│   relevant_vyaptis: ["V01"]                                      │
│   → No sub-component reasoning possible                         │
│                                                                  │
│ AFTER predicate extraction:                                      │
│   predicates: ["ltv_exceeds_cac(acme)",                          │
│                "positive_contribution_margin(acme)"]              │
│   relevant_vyaptis: ["V12", "V01"]                               │
│   → V12 fires → derives positive_unit_economics                 │
│   → V01 fires → derives value_creation                          │
│   → Full inference chain reconstructed                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## STAGE 4: T2 Compilation (Facts + Rules → AF)

**What:** Build ASPIC+ argumentation framework via forward chaining through applicable vyāptis.

**Impact of Predicate Extraction:** With the enriched KB, forward chaining now produces a deeper inference chain. Two base facts trigger V12, which derives `positive_unit_economics`, which triggers V01, which derives `value_creation`. Before enrichment, the grounding had to assert `positive_unit_economics` directly (no sub-component reasoning).

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ Augmented KnowledgeStore (25 vyāptis)                            │
│ query_facts: [                                                   │
│   {predicate: "ltv_exceeds_cac(acme)", conf: 0.7},              │
│   {predicate: "positive_contribution_margin(acme)", conf: 0.7}  │
│ ]                                                                │
└──────────────────────────────────────────────────────────────────┘

         ▼ Step 4a: Premise Arguments ▼

  A0000: ltv_exceeds_cac(acme) [premise]
    tag: Tag(b=0.70, d=0.00, u=0.30, pramana=PRATYAKSA)

  A0001: positive_contribution_margin(acme) [premise]
    tag: Tag(b=0.70, d=0.00, u=0.30, pramana=PRATYAKSA)

         ▼ Step 4b: Forward-Chain ▼

  V12: ltv_exceeds_cac + positive_contribution_margin
       → positive_unit_economics
    Both antecedents available (A0000, A0001) ✓
    → Create A0002: positive_unit_economics(acme)
      top_rule: V12
      sub_arguments: (A0000, A0001)
      tag: tensor(V12_rule_tag, tensor(A0000_tag, A0001_tag))
           V12 rule tag: Tag(b=0.60, pramana=ANUMANA, trust=0.68)
           Combined: b = 0.60 × 0.70 × 0.70 = 0.294
           derivation_depth: 1

  V01: positive_unit_economics → value_creation
    Antecedent available (A0002) ✓
    → Create A0003: value_creation(acme)
      top_rule: V01
      sub_arguments: (A0002,)
      tag: tensor(V01_rule_tag, A0002_tag)
           Combined: b = 0.95 × 0.294 = 0.279
           derivation_depth: 2

         ▼ Step 4c: Derive Attacks ▼

  REBUTTING: No contradictory conclusions
  UNDERCUTTING: No scope violations
  UNDERMINING: All decay_factors fresh

         ▼ Fixpoint: no new arguments → STOP ▼

┌─ OUTPUT: ArgumentationFramework ─────────────────────────────────┐
│ arguments: {                                                     │
│   A0000: ltv_exceeds_cac(acme) [premise, b=0.70]                │
│   A0001: positive_contribution_margin(acme) [premise, b=0.70]   │
│   A0002: positive_unit_economics(acme) [via V12, b=0.294]       │
│   A0003: value_creation(acme) [via V01→V12, b=0.279]            │
│ }                                                                │
│ attacks: []                                                      │
│                                                                  │
│ BEFORE: 3 arguments, derivation_depth=1, max chain: 1 rule      │
│ AFTER:  4 arguments, derivation_depth=2, max chain: 2 rules     │
│ → Sub-component reasoning now visible                           │
└──────────────────────────────────────────────────────────────────┘
```

**Key Insight:** The belief attenuation through the chain (`b = 0.60 × 0.70 × 0.70 = 0.294`) correctly reflects that the conclusion is derived through multiple uncertain steps. The provenance semiring ⊗ (tensor) operation ensures that confidence *naturally decreases* through longer chains — epistemically honest by construction.

**Files:** `t2_compiler_v4.py:compile_t2()`

---

## STAGE 5: Contestation — Compute Extension

**What:** Apply debate protocol (vāda/jalpa/vitaṇḍā) to label arguments IN/OUT/UNDECIDED.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ ArgumentationFramework (4 arguments, 0 attacks)                  │
│ contestation_mode: "vada"                                        │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Grounded Semantics ▼

  Iteration 1:
    A0000: no attackers → IN
    A0001: no attackers → IN
    A0002: no attackers → IN
    A0003: no attackers → IN
  Fixpoint reached.

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ labels: {A0000: IN, A0001: IN, A0002: IN, A0003: IN}            │
│ contestation: {mode: "vada", open_questions: []}                 │
│ extension_size: 4  (was 2 before enrichment)                     │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `contestation.py:vada()`, `argumentation.py:compute_grounded()`

---

## STAGE 6: Epistemic Status Derivation

```
┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ results: {                                                       │
│   "ltv_exceeds_cac(acme)": {                                    │
│     status: PROVISIONAL, tag: Tag(b=0.70, ...)                   │
│   },                                                             │
│   "positive_contribution_margin(acme)": {                        │
│     status: PROVISIONAL, tag: Tag(b=0.70, ...)                   │
│   },                                                             │
│   "positive_unit_economics(acme)": {                             │
│     status: OPEN, tag: Tag(b=0.294, u=0.706, ...)               │
│     ↑ Derived through chain → belief attenuated → OPEN status    │
│   },                                                             │
│   "value_creation(acme)": {                                      │
│     status: OPEN, tag: Tag(b=0.279, u=0.721, ...)               │
│     ↑ Two-rule chain → further attenuated                        │
│   }                                                              │
│ }                                                                │
│                                                                  │
│ Key difference from seed KB:                                     │
│   BEFORE: positive_unit_economics = PROVISIONAL (directly given) │
│   AFTER:  positive_unit_economics = OPEN (derived through chain) │
│   → Engine correctly reflects that derived conclusions are less  │
│     certain than direct assertions. Epistemically honest.         │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `argumentation.py:get_epistemic_status()`

---

## STAGES 7-9: Provenance, Uncertainty, Violations

These stages work identically but produce richer outputs:

```
┌─ PROVENANCE (Stage 7) ───────────────────────────────────────────┐
│ "positive_unit_economics(acme)": {                               │
│   sources: ["lightweight_grounding", "src_hbs_unit_economics"],  │
│   pramana: "ANUMANA",          ← inference (not direct)          │
│   derivation_depth: 1,         ← one rule in chain              │
│   trust: 0.68,                 ← V12 trust score                 │
│   decay: 1.0                                                     │
│ }                                                                │
│ "value_creation(acme)": {                                        │
│   sources: ["lightweight_grounding", "src_hbs_unit_economics",   │
│             "src_ries_2011"],                                     │
│   pramana: "ANUMANA",                                            │
│   derivation_depth: 2,         ← TWO rules in chain             │
│   trust: 0.58,                 ← compounded trust                │
│   decay: 1.0                                                     │
│ }                                                                │
└──────────────────────────────────────────────────────────────────┘

┌─ UNCERTAINTY (Stage 8) ──────────────────────────────────────────┐
│ "positive_unit_economics(acme)": {                               │
│   epistemic: {status: "open", belief: 0.294, uncertainty: 0.706},│
│   aleatoric: {disbelief: 0.0},                                   │
│   inference: {grounding: 0.7, decay: 1.0, chain_depth: 1},      │
│   total_confidence: 0.200                                        │
│ }                                                                │
│                                                                  │
│ → Uncertainty decomposition reveals WHY confidence dropped:      │
│   inference.chain_depth=1 means the conclusion was derived,      │
│   not directly observed. Epistemic uncertainty is HIGH (0.706)   │
│   because the semiring ⊗ attenuated belief through the chain.    │
└──────────────────────────────────────────────────────────────────┘

┌─ VIOLATIONS (Stage 9) ───────────────────────────────────────────┐
│ violations: []   (no conflicts in this query)                    │
│                                                                  │
│ But with enriched KB, MORE violations become detectable:         │
│   If query also asserts maturity_mismatch(acme):                 │
│     V14 fires → negative_unit_economics(acme)                    │
│     → REBUTS positive_unit_economics(acme)                       │
│     → viruddha detected! (contradiction at sub-component level) │
│   This conflict was INVISIBLE with the seed KB.                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## STAGE 10: LLM Synthesis

**What:** Generate calibrated natural language response from all symbolic results.

**Impact of Predicate Extraction:** The synthesis now has richer inputs — more accepted arguments with sub-component reasoning, deeper provenance chains, and more granular uncertainty decomposition. The response can explain *why* unit economics are positive (LTV > CAC + positive contribution margin) rather than just asserting it.

```
┌─ INPUT TO DSPy ──────────────────────────────────────────────────┐
│ accepted_arguments:                                              │
│   "- ltv_exceeds_cac(acme): provisional (belief=0.70)            │
│    - positive_contribution_margin(acme): provisional (b=0.70)    │
│    - positive_unit_economics(acme): open (belief=0.294)          │
│    - value_creation(acme): open (belief=0.279)"                  │
│                                                                  │
│ BEFORE enrichment (only had):                                    │
│   "- positive_unit_economics(acme): provisional (belief=0.70)    │
│    - value_creation(acme): provisional (belief=0.70)"            │
│ → Much less reasoning visible to the LLM                        │
└──────────────────────────────────────────────────────────────────┘

         ▼ dspy.Refine(N=3, reward_fn) ▼

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ response:                                                        │
│   "Based on the evidence, when a company demonstrates both       │
│    an LTV-CAC ratio above breakeven and positive contribution    │
│    margin, there is provisional support for viable unit           │
│    economics. However, the derived conclusion of value creation  │
│    carries open epistemic status (confidence 0.28) because it    │
│    depends on a multi-step inference chain through two rules.    │
│    Additional evidence — such as payback period data —           │
│    would strengthen this conclusion."                            │
│                                                                  │
│ sources_cited:                                                   │
│   ["lightweight_grounding", "src_hbs_unit_economics"]            │
│                                                                  │
│ BEFORE enrichment:                                               │
│   "Positive unit economics is provisionally associated with      │
│    value creation."  (no sub-component reasoning)                │
└──────────────────────────────────────────────────────────────────┘
```

---

## STAGE 11: Response Assembly

```
┌─ FINAL API RESPONSE (HTTP 201) ──────────────────────────────────┐
│ {                                                                │
│   "query_text": "Does a company with strong LTV-CAC ratio and   │
│                  positive contribution margin have viable         │
│                  unit economics?",                                │
│   "contestation_mode": "vada",                                   │
│   "status": "completed",                                         │
│                                                                  │
│   "response": "Based on the evidence, when a company             │
│     demonstrates both an LTV-CAC ratio above breakeven and       │
│     positive contribution margin, there is provisional support   │
│     for viable unit economics. However, the derived conclusion   │
│     of value creation carries open epistemic status..."          │
│                                                                  │
│   "sources": ["lightweight_grounding",                           │
│               "src_hbs_unit_economics"],                         │
│                                                                  │
│   "uncertainty": {                                               │
│     "ltv_exceeds_cac(acme)":             {conf: 0.70},           │
│     "positive_contribution_margin(acme)": {conf: 0.70},         │
│     "positive_unit_economics(acme)":      {conf: 0.20},         │
│     "value_creation(acme)":               {conf: 0.19}          │
│   },                                                             │
│                                                                  │
│   "provenance": {                                                │
│     "value_creation(acme)": {                                    │
│       "sources": ["lightweight_grounding",                       │
│                    "src_hbs_unit_economics",                     │
│                    "src_ries_2011"],                              │
│       "pramana": "ANUMANA",                                      │
│       "derivation_depth": 2,                                     │
│       "trust": 0.58                                              │
│     }                                                            │
│   },                                                             │
│                                                                  │
│   "violations": [],                                              │
│   "grounding_confidence": 0.7,                                   │
│   "extension_size": 4,                                           │
│   "contestation": {                                              │
│     "mode": "vada",                                              │
│     "open_questions": [],                                        │
│     "suggested_evidence": []                                     │
│   }                                                              │
│ }                                                                │
└──────────────────────────────────────────────────────────────────┘
```

---

# PART 3: BEFORE vs AFTER COMPARISON

## Predicate Vocabulary

```
BEFORE (seed KB):                AFTER (augmented KB):
  23 predicates                    ~50 predicates
  11 vyāptis                      ~25 vyāptis
  Chapter-level only               Section/paragraph-level
  "positive_unit_economics"        "ltv_exceeds_cac",
    (single predicate)               "positive_contribution_margin",
                                     "payback_within_runway",
                                     "short_payback_period",
                                     "economies_of_scale_real",
                                     "imagined_economies_of_scale",
                                     "network_effects_present",
                                     "negative_unit_economics",
                                     "unit_economics_death_spiral",
                                     "maturity_mismatch",
                                     "cohort_ltv_declining",
                                     "high_arpu",
                                     "high_retention_rate",
                                     "gross_margin_not_contribution_margin"
```

## Reasoning Depth

```
BEFORE:                            AFTER:
  User query                         User query
    ↓ ground                           ↓ ground
  positive_unit_economics              ltv_exceeds_cac
    ↓ V01                              positive_contribution_margin
  value_creation                         ↓ V12 (NEW)
    (1 inference step)                 positive_unit_economics
                                         ↓ V01
                                       value_creation
                                         (2 inference steps)
                                         (sub-component reasoning)
```

## Conflict Detection

```
BEFORE:                            AFTER:
  Only detects V01 ↔ V11            Detects V01 ↔ V11 AND:
  (chapter-level conflict)             V12 ↔ V14 (sub-component:
                                         positive_cm vs maturity_mismatch)
                                       V13 → death_spiral detection
                                       imagined_economies ≠ real_economies
                                       (section-level conflicts)
```

---

# PART 4: COMPLETE DATA FLOW DIAGRAM

```
                    Guide Text (ch01-ch10 markdown)
                    + Seed KB YAML (11 vyāptis)
                              │
          ════════════════════╪════════════════════════
          OFFLINE: PREDICATE EXTRACTION PIPELINE
          ════════════════════╪════════════════════════
                              │
                              ▼
                  ┌───────────────────────┐
                  │  STAGE A: Extract     │ LLM: 1/section
                  │  Candidate Predicates │ (~40-60 calls)
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  STAGE B: Decompose   │ LLM: 1/vyāpti
                  │  Existing Vyāptis     │ (~11 calls)
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  STAGE C: Canonicalize│ Embeddings + 0-1
                  │  & Deduplicate        │ LLM call
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  STAGE D: Construct   │ LLM: 1/vyāpti
                  │  New Vyāptis          │ (~15-30 calls)
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  STAGE E: Validate    │ 0 LLM calls
                  │  DAG + Pydantic +     │ (deterministic)
                  │  Datalog compilation  │
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  STAGE F: Human       │ 0 LLM calls
                  │  Review (HITL)        │ (interactive)
                  └───────────┬───────────┘
                              │
                    Augmented KB YAML
                    (~25 vyāptis, ~50 predicates)
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
  ┌─────────────┐   ┌──────────────┐   ┌──────────────┐
  │ T3 Compiler │   │   Stored as  │   │  MIPROv2     │
  │ → GraphRAG  │   │ YAML for     │   │  Optimizer   │
  │   corpus    │   │ query-time   │   │  (optional)  │
  └──────┬──────┘   └──────┬───────┘   └──────────────┘
         │                 │
         │    ═════════════╪════════════════════
         │    ONLINE: QUERY PIPELINE (~3.8s)
         │    ═════════════╪════════════════════
         │                 │
         │          User NL Query
         │                 │
         │                 ▼
         │     ┌───────────────────────┐
         │     │  ONTOLOGY SNIPPET     │ ← Augmented KB
         │     │  (Layer 1 defense)    │   (50 predicates)
         │     └───────────┬───────────┘
         │                 │
         │                 ▼
         │     ┌───────────────────────┐
         │     │  LLM GROUNDING        │ ← LLM (1-5 calls)
         │     │  NL → Predicates      │
         │     └───────────┬───────────┘
         │                 │
         │         Structured Predicates
         │         [ltv_exceeds_cac(acme),
         │          positive_contribution_margin(acme)]
         │                 │
         │                 ▼
         │     ┌───────────────────────┐
         │     │  T2 COMPILER          │ ← Augmented KB rules
         │     │  Facts + Rules → AF   │   (25 vyāptis)
         │     └───────────┬───────────┘
         │                 │
         │         Argumentation Framework
         │         (Arguments + Attacks)
         │                 │
         │                 ▼
         │     ┌───────────────────────┐
         │     │  CONTESTATION         │ ← vāda/jalpa/vitaṇḍā
         │     │  Compute Extension    │
         │     └───────────┬───────────┘
         │                 │
         │         Labels (IN/OUT/UNDECIDED)
         │                 │
         │     ┌───────────┼───────────┐
         │     │           │           │
         │     ▼           ▼           ▼
         │ ┌─────────┐ ┌────────┐ ┌──────────┐
         │ │Epistemic│ │Provn.  │ │Uncertain.│
         │ │ Status  │ │Extract │ │Decompose │
         │ └────┬────┘ └───┬────┘ └────┬─────┘
         │      │          │           │
         │      └──────────┼───────────┘
         │                 │
         │     ┌───────────┴───────────┐
         │     │                       │
         │     ▼                       ▼
         │ ┌─────────┐        ┌──────────────┐
         │ │Violation│        │LLM SYNTHESIS │ ← LLM (1 call)
         │ │ Detect  │        │(dspy.Refine) │
         │ └────┬────┘        └──────┬───────┘
         │      │                    │
         │      └────────┬───────────┘
         │               │
         │               ▼
         └──────▶ ┌───────────────────────┐
     Retrieved    │  FINAL RESPONSE       │
     Chunks       │  JSON + DB persist    │
                  └───────────────────────┘
```

---

## Summary: Stage Reference

### Offline Pipeline (Predicate Extraction)

| Stage | Name | Processing | LLM Calls | Invariants Enforced |
|-------|------|-----------|-----------|---------------------|
| A | Extract Candidates | DSPy ChainOfThought per section | ~40-60 | snake_case, provenance |
| B | Decompose Vyāptis | DSPy ChainOfThought per vyāpti | ~11 | depth ≤ 2, valid relations |
| C | Canonicalize | Embedding clustering + LLM | 0-1 | no duplicates |
| D | Construct Vyāptis | DSPy Refine(N=3) per vyāpti | ~15-30 | epistemic_status=hypothesis |
| E | Validate & Merge | DAG check, Pydantic, Datalog | 0 | I1-I5 (all five) |
| F | Human Review | Interactive CLI | 0 | domain expert approval |

### Online Pipeline (Query)

| Stage | Name | Processing | LLM? | Time |
|-------|------|-----------|------|------|
| 0 | Request Ingestion | Auth, route | No | <1ms |
| 1 | KB Loading | YAML parse (cached) | No | <10ms |
| 2 | Ontology Snippet | String construction | No | <1ms |
| 3 | LLM Grounding | ChainOfThought (1-5 calls) | **Yes** | ~1.5s |
| 4 | T2 Compilation | Forward chain + attacks | No | <5ms |
| 5 | Contestation | Grounded/preferred/stable semantics | No | <1ms |
| 6 | Epistemic Status | Tag threshold checks | No | <1ms |
| 7 | Provenance | Tag field extraction | No | <1ms |
| 8 | Uncertainty | 3-way decomposition | No | <1ms |
| 9 | Violations | Attack graph scan | No | <1ms |
| 10 | LLM Synthesis | dspy.Refine(N=3) | **Yes** | ~2s |
| 11 | Response Assembly | Dict + DB write | No | <5ms |

### Key Files

| Module | Role |
|--------|------|
| `extraction_schema.py` | Pydantic models for extraction pipeline |
| `predicate_extraction.py` | Stages A-E + orchestrator |
| `extraction_eval.py` | Composite metric + MIPROv2 optimization |
| `extraction_hitl.py` | Stage F: human review CLI |
| `schema.py` | Core KnowledgeStore, Vyapti, CausalStatus |
| `schema_v4.py` | ProvenanceTag, Argument, Attack, Label |
| `grounding.py` | Five-layer grounding defense |
| `t2_compiler_v4.py` | KB + facts → ArgumentationFramework |
| `argumentation.py` | ASPIC+ grounded/preferred/stable semantics |
| `contestation.py` | Vāda/Jalpa/Vitaṇḍā debate protocols |
| `uncertainty.py` | Three-way uncertainty decomposition |
| `engine_v4.py` | Top-level engine orchestrator |
| `t3_compiler.py` | Guide text → GraphRAG corpus |
| `optimize.py` | MIPROv2 calibration metric + optimization |
