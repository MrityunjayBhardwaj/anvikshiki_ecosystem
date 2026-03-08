# Ānvīkṣikī Engine — Coverage-Based Routing Pipeline Flowchart

> End-to-end trace of the **updated pipeline** with T2b compile-time extraction,
> semantic coverage analysis, T3b query-time augmentation, T3a retrieval,
> and coverage-based routing in the engine.
>
> **Branch:** `feat/t2b-t3a-t3b-architecture`
> **Date:** 2026-03-05
> **KB:** `business_expert.yaml` (11 base vyāptis, 20 predicates)
> **Trace script:** `scripts/e2e_trace_coverage_pipeline.py`

---

## Master Architecture Overview

```
═══════════════════════════════════════════════════════════════════════════
                     OFFLINE: COMPILE-TIME PIPELINE
                     (runs once per guide version)
═══════════════════════════════════════════════════════════════════════════

  Guide Text (ch01-ch10 markdown)
  + Seed KnowledgeStore YAML (11 vyāptis, 20 predicates)
         │
         ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │  T2b COMPILER (wraps PredicateExtractionPipeline)          [NEW]   │
  │                                                                     │
  │   Stage A: Extract Candidate Predicates (LLM: 1/section)           │
  │       ▼                                                             │
  │   Stage B: Hierarchical Decomposition  (LLM: 1/vyāpti)            │
  │       ▼                                                             │
  │   Stage C: Canonicalize & Deduplicate   (embeddings + LLM)         │
  │       ▼ → synonym_table (alias → canonical name)                   │
  │   Stage D: Construct New Vyāptis        (LLM: 1/vyāpti)           │
  │       ▼                                                             │
  │   Stage E: Validate & Merge             (deterministic)            │
  │       ▼                                                             │
  │   Origin tagging: GUIDE_EXTRACTED + source_chapter_ids             │
  └────────────────────────────┬────────────────────────────────────────┘
                               │
                    T2bResult:
                      augmented_ks (14 vyāptis, 25 predicates)
                      synonym_table (5 entries)
                      source_sections (vyapti_id → [chapter_ids])
                      fine_grained_vyapti_ids: [V12, V13, V14]
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
  ┌─────────────┐     ┌──────────────┐     ┌──────────────────────┐
  │ Coverage    │     │ T3 Compiler  │     │  T3a Retriever       │
  │ Analyzer    │     │ KB+Guide →   │     │  FAISS index over    │
  │ (at query)  │     │ GraphRAG     │     │  TextChunks          │
  └─────────────┘     └──────────────┘     └──────────────────────┘


═══════════════════════════════════════════════════════════════════════════
                     ONLINE: QUERY PIPELINE
                     (runs per user query)
═══════════════════════════════════════════════════════════════════════════

  User Query (natural language)
  + Augmented KnowledgeStore (from T2b)
  + SemanticCoverageAnalyzer (vocabulary + synonym table)
  + T3aRetriever (TextChunks + FAISS index)
  + AugmentationPipeline (optional, for DECLINE queries)
         │
         ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Stage 0: LLM Grounding (NL → predicates)                         │
  │  Stage 1: Semantic Coverage Analysis               [NEW]           │
  │  Stage 2: Coverage-Based Routing                   [NEW]           │
  │            ├── FULL/PARTIAL → base+fine KB path                    │
  │            ├── DECLINE+in-domain → T3b augmentation path [NEW]     │
  │            └── DECLINE+out-of-domain → decline response  [NEW]     │
  │  Stage 3: T2 Compilation (facts + rules → AF)                     │
  │  Stage 4: T3a Retrieval (parallel, cross-linked)   [NEW]           │
  │  Stage 5: Contestation (vāda/jalpa/vitaṇḍā)                      │
  │  Stage 6: Epistemic Status Derivation                              │
  │  Stage 7: Provenance Extraction                                    │
  │  Stage 8: Uncertainty Decomposition                                │
  │  Stage 9: Violation Detection (hetvābhāsa)                        │
  │  Stage 10: LLM Synthesis (calibrated response)                     │
  └─────────────────────────────────────────────────────────────────────┘
         │
         ▼
  Final Response (with coverage, augmentation metadata,
  epistemic qualification, provenance, uncertainty)
```

---

# PART 1: OFFLINE COMPILE-TIME PIPELINE

> Runs once per guide version. Produces augmented KB with fine-grained
> vyāptis, synonym table, source section mappings, and T3a retrieval index.

---

## T2b COMPILER — Compile-Time Fine-Grained KB Extraction

**What:** Wraps the existing `PredicateExtractionPipeline` (Stages A-E, 1124 lines) and adds origin tagging, synonym table extraction, and source section tracking.

**Why:** The seed KB has chapter-level abstractions only (e.g., `positive_unit_economics`). T2b extracts section-level concepts (e.g., `ltv_exceeds_cac`, `positive_contribution_margin`) that enable deeper inference chains at query time.

**Key insight:** The extraction pipeline already exists — T2b adds ~150 lines of framing, not reimplementation.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ knowledge_store: KnowledgeStore (11 vyāptis, 20 predicates)      │
│ guide_text: {                                                    │
│   "ch02": "### 2.1 The LTV-CAC Relationship\n..."               │
│   "ch03": "### 3.1 Identifying the Binding Constraint\n..."     │
│   ...                                                            │
│ }                                                                │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Processing ▼

1. Run PredicateExtractionPipeline(ks, ExtractionConfig())
   Stages A-E: extract predicates → decompose → canonicalize →
   construct vyāptis → validate (cycles + Datalog compile)

2. Tag new vyāptis with AugmentationMetadata:
   origin: AugmentationOrigin.GUIDE_EXTRACTED
   source_chapter_ids: ["ch02"] (from Stage D provenance)
   parent_vyapti_id: "V01" (parent in decomposition hierarchy)

3. Build synonym_table from Stage C SynonymClusters:
   ltv_above_cac        → ltv_exceeds_cac
   ltv_greater_than_cac → ltv_exceeds_cac
   organizational_entropy → coordination_overhead
   supply_chain_bottleneck → binding_constraint_identified
   unit_econ_positive   → positive_unit_economics

4. Track source_sections for T3a cross-linking:
   V12 → ["ch02"]
   V13 → ["ch02"]
   V14 → ["ch02"]

5. Store metadata on augmented KnowledgeStore:
   fine_grained_vyapti_ids: ["V12", "V13", "V14"]
   synonym_table: {5 entries}

┌─ OUTPUT: T2bResult ──────────────────────────────────────────────┐
│ augmented_ks: KnowledgeStore(                                    │
│   vyaptis: 14 (base: 11, fine-grained: 3)                       │
│   predicates: 25 (was 20)                                        │
│   NEW predicates:                                                │
│     ltv_exceeds_cac, maturity_mismatch, negative_unit_economics, │
│     positive_contribution_margin, unit_economics_death_spiral    │
│ )                                                                │
│                                                                  │
│ New vyāptis:                                                     │
│   V12: ltv_exceeds_cac + positive_contribution_margin            │
│        → positive_unit_economics                                 │
│        (empirical, hypothesis, conf=0.85×0.80)                   │
│        origin: GUIDE_EXTRACTED, source: ch02, parent: V01        │
│                                                                  │
│   V13: negative_unit_economics                                   │
│        → unit_economics_death_spiral                             │
│        (empirical, hypothesis, conf=0.80×0.75)                   │
│        origin: GUIDE_EXTRACTED, source: ch02, parent: V01        │
│                                                                  │
│   V14: maturity_mismatch                                         │
│        → negative_unit_economics                                 │
│        (empirical, hypothesis, conf=0.80×0.70)                   │
│        origin: GUIDE_EXTRACTED, source: ch02, parent: V01        │
│                                                                  │
│ synonym_table: {                                                 │
│   "ltv_above_cac": "ltv_exceeds_cac",                            │
│   "ltv_greater_than_cac": "ltv_exceeds_cac",                    │
│   "organizational_entropy": "coordination_overhead",             │
│   "supply_chain_bottleneck": "binding_constraint_identified",    │
│   "unit_econ_positive": "positive_unit_economics"                │
│ }                                                                │
│                                                                  │
│ source_sections: {                                               │
│   "V12": ["ch02"], "V13": ["ch02"], "V14": ["ch02"]             │
│ }                                                                │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `t2b_compiler.py:compile_t2b()`, `predicate_extraction.py:PredicateExtractionPipeline`

---

## SemanticCoverageAnalyzer — Build at Compile Time

**What:** Three-layer predicate matching against base + fine-grained KB. Zero LLM calls — fully deterministic.

**Why:** Determines whether a query's predicates are covered by the KB vocabulary, routing to FULL (inference), PARTIAL (inference with gaps), or DECLINE (augmentation or rejection).

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ knowledge_store: augmented KnowledgeStore (14 vyāptis)           │
│ synonym_table: {5 entries}                                       │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Build ▼

1. Build vocabulary (all predicates from antecedents + consequents):
   25 predicates:
   binding_constraint_identified, calibration_accuracy,
   capability_gain, coordination_overhead, decision_quality,
   disruption_vulnerability, distorted_market_signal,
   incentive_alignment, incumbent_rational_allocation,
   long_term_value, low_margin_market_entrant,
   ltv_exceeds_cac,          ← NEW from T2b
   maturity_mismatch,        ← NEW from T2b
   negative_unit_economics,  ← NEW from T2b
   not_value_creation, organizational_effectiveness,
   organizational_growth,
   positive_contribution_margin,  ← NEW from T2b
   positive_unit_economics, pricing_power,
   resource_allocation_effective, strategic_commitment,
   superior_information,
   unit_economics_death_spiral,  ← NEW from T2b
   value_creation

2. Build predicate→vyapti index:
   positive_unit_economics → [V01, V12]
   binding_constraint_identified → [V02]
   value_creation → [V01, V08, V11]
   ...

3. Store synonym_table (5 entries)

┌─ OUTPUT: SemanticCoverageAnalyzer (ready for query time) ────────┐
│ Vocabulary: 25 predicates                                        │
│ Synonym table: 5 entries                                         │
│ Predicate index: pred → [vyapti_ids]                             │
│                                                                  │
│ Three matching layers (applied per predicate):                   │
│   Layer 1: Exact match against vocabulary                        │
│   Layer 2: Synonym lookup in synonym_table                       │
│   Layer 3: Jaccard token overlap (threshold ≥ 0.4)               │
│                                                                  │
│ Routing thresholds:                                              │
│   FULL_THRESHOLD = 0.6    (coverage ≥ 60%)                       │
│   PARTIAL_THRESHOLD = 0.2 (coverage ≥ 20%)                       │
│   Below 0.2 → DECLINE                                           │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `coverage.py:SemanticCoverageAnalyzer`

---

## T3a Retriever — Build at Compile Time

**What:** Embedding-based retriever over guide text chunks from T3 compiler. Supports section boosting for T2b→T3a cross-linking.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ chunks: list[TextChunk] from compile_t3()                        │
│   ch02_s001: "### 2.1 The LTV-CAC Relationship..."              │
│              vyapti_anchors: [V01, V12]                          │
│   ch02_s002: "### 2.2 The Death Spiral..."                       │
│              vyapti_anchors: [V13]                               │
│   ch03_s001: "### 3.1 Identifying the Binding Constraint..."    │
│              vyapti_anchors: [V02]                               │
│   ... (8 chunks total in this trace)                             │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Build ▼

1. Build corpus: [chunk.text for chunk in chunks]
2. Build FAISS index via dspy.retrievers.Embeddings
   (Falls back to keyword-based retrieval if unavailable)
3. Map index positions back to TextChunk objects

┌─ OUTPUT: T3aRetriever (ready for query time) ────────────────────┐
│ Corpus: 8 chunks                                                 │
│ FAISS index: available / fallback mode                           │
│                                                                  │
│ Key methods:                                                     │
│   retrieve(query, k, boost_sections)                             │
│   retrieve_for_predicates(activated_sections, query, k)          │
│     → cross-linked retrieval with section boosting               │
│                                                                  │
│ Boosting logic:                                                  │
│   Chunks from boosted sections in top 2*k → moved to front      │
│                                                                  │
│ Fallback (no embeddings):                                        │
│   Token overlap scoring + 1.5x section boost + 1.2x vyapti boost│
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `t3a_retriever.py:T3aRetriever`

---

# PART 2: ONLINE QUERY PIPELINE — COVERAGE-BASED ROUTING

> Runs per user query. Uses augmented KnowledgeStore, coverage analyzer,
> T3a retriever, and optional T3b augmentation pipeline.
> Four routing outcomes shown across four query scenarios.

---

## Query-Time Data Flow

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

---

# SCENARIO 1: FULL Coverage — In-Domain Query

**Query:** "Does a company with strong LTV-CAC ratio and positive contribution margin have viable unit economics?"

This query maps directly to predicates in the augmented KB. All 3 predicates match exactly. Forward chaining derives `value_creation` through a 2-rule chain.

---

## Stage 0: LLM Grounding

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ query: "Does a company with strong LTV-CAC ratio and positive   │
│         contribution margin have viable unit economics?"        │
│ ontology_snippet: (25 predicates, 14 rules)                     │
│ domain_type: "CRAFT"                                             │
└──────────────────────────────────────────────────────────────────┘

                    ▼ LLM Grounding (1 call) ▼

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ predicates: [                                                    │
│   "positive_unit_economics(acme)",                               │
│   "ltv_exceeds_cac(acme)",          ← from T2b fine-grained KB  │
│   "positive_contribution_margin(acme)"  ← from T2b fine KB      │
│ ]                                                                │
│ confidence: 0.70                                                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## Stage 1: Semantic Coverage Analysis [NEW]

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ grounded_predicates: [                                           │
│   "positive_unit_economics(acme)",                               │
│   "ltv_exceeds_cac(acme)",                                      │
│   "positive_contribution_margin(acme)"                           │
│ ]                                                                │
│ SemanticCoverageAnalyzer:                                        │
│   vocabulary: 25 predicates                                      │
│   synonym_table: 5 entries                                       │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Three-Layer Matching ▼

  positive_unit_economics(acme):
    Strip entity → "positive_unit_economics"
    Layer 1 (exact): "positive_unit_economics" ∈ vocabulary ✓
    → MATCHED (exact)
    → Relevant vyāptis: [V01, V12]

  ltv_exceeds_cac(acme):
    Strip entity → "ltv_exceeds_cac"
    Layer 1 (exact): "ltv_exceeds_cac" ∈ vocabulary ✓
    → MATCHED (exact)
    → Relevant vyāptis: [V12]

  positive_contribution_margin(acme):
    Strip entity → "positive_contribution_margin"
    Layer 1 (exact): "positive_contribution_margin" ∈ vocabulary ✓
    → MATCHED (exact)
    → Relevant vyāptis: [V12]

  Coverage = 3/3 = 1.00

┌─ OUTPUT: CoverageResult ─────────────────────────────────────────┐
│ coverage_ratio: 1.00                                             │
│ decision: "FULL"          (1.00 ≥ FULL_THRESHOLD 0.6)           │
│ matched_predicates: [                                            │
│   "positive_unit_economics(acme)",                               │
│   "ltv_exceeds_cac(acme)",                                      │
│   "positive_contribution_margin(acme)"                           │
│ ]                                                                │
│ unmatched_predicates: []                                         │
│ match_details: {                                                 │
│   "positive_unit_economics(acme)": "exact",                     │
│   "ltv_exceeds_cac(acme)": "exact",                             │
│   "positive_contribution_margin(acme)": "exact"                  │
│ }                                                                │
│ relevant_vyaptis: ["V01", "V12"]                                 │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `coverage.py:SemanticCoverageAnalyzer.analyze()`

---

## Stage 2: Routing → FULL [NEW]

```
  Coverage decision: FULL (1.00 ≥ 0.6)
  → Route: proceed with base+fine KB (14 vyāptis)
  → No T3b augmentation needed
  → active_ks = augmented_ks (from T2b)
```

---

## Stage 3: T2 Compilation (Facts + Rules → AF)

**What:** Build ASPIC+ argumentation framework via forward chaining. With the enriched KB, forward chaining now produces a deeper inference chain.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ Augmented KnowledgeStore (14 vyāptis, 25 predicates)             │
│ query_facts: [                                                   │
│   {predicate: "positive_unit_economics", conf: 0.7},            │
│   {predicate: "ltv_exceeds_cac", conf: 0.7},                   │
│   {predicate: "positive_contribution_margin", conf: 0.7}       │
│ ]                                                                │
└──────────────────────────────────────────────────────────────────┘

         ▼ Step 3a: Premise Arguments ▼

  A0000: positive_unit_economics [premise]
    tag: Tag(b=0.700, d=0.000, u=0.300, pramana=PRATYAKSA,
            trust=1.0, decay=1.0, depth=0)

  A0001: ltv_exceeds_cac [premise]
    tag: Tag(b=0.700, d=0.000, u=0.300, pramana=PRATYAKSA,
            trust=1.0, decay=1.0, depth=0)

  A0002: positive_contribution_margin [premise]
    tag: Tag(b=0.700, d=0.000, u=0.300, pramana=PRATYAKSA,
            trust=1.0, decay=1.0, depth=0)

         ▼ Step 3b: Forward-Chain ▼

  V01: positive_unit_economics → value_creation
    Antecedent: positive_unit_economics available (A0000) ✓
    → Create A0003: value_creation
      top_rule: V01
      sub_arguments: (A0000,)
      tag: tensor(V01_rule_tag, A0000_tag)
           V01 rule tag: Tag(b=0.95, pramana=ANUMANA,
                             trust=0.855, sources=[src_hbs, src_ries])
           Combined: b=0.665, depth=0
           sources: [src_hbs_unit_economics, src_ries_2011]

  V12: ltv_exceeds_cac + positive_contribution_margin
       → positive_unit_economics
    Both antecedents: A0001 + A0002 ✓
    → Create A0004: positive_unit_economics
      top_rule: V12 (GUIDE_EXTRACTED, hypothesis)
      sub_arguments: (A0001, A0002)
      tag: tensor(V12_rule_tag, tensor(A0001_tag, A0002_tag))
           V12 rule tag: Tag(b=0.60, pramana=ANUMANA,
                             trust=0.680, sources=[src_hbs])
           Combined: b=0.277, depth=0
           sources: [src_hbs_unit_economics]

         ▼ Step 3c: Derive Attacks ▼

  REBUTTING: No contradictory conclusions
  UNDERCUTTING: No scope violations
  UNDERMINING: All decay_factors fresh

         ▼ Fixpoint: no new arguments → STOP ▼

┌─ OUTPUT: ArgumentationFramework ─────────────────────────────────┐
│ arguments: {                                                     │
│   A0000: positive_unit_economics [premise, b=0.700]              │
│   A0001: ltv_exceeds_cac [premise, b=0.700]                     │
│   A0002: positive_contribution_margin [premise, b=0.700]         │
│   A0003: value_creation [via V01, b=0.665]        ← DERIVED     │
│   A0004: positive_unit_economics [via V12, b=0.277] ← DERIVED   │
│ }                                                                │
│ attacks: []                                                      │
│                                                                  │
│ Key: A0003 derives value_creation through V01 from the premise   │
│ A0004 re-derives positive_unit_economics through V12 from the    │
│ sub-component predicates — showing the decomposition works.      │
│                                                                  │
│ Epistemic note: A0004 (b=0.277) via V12 is weaker than          │
│ A0000 (b=0.700) premise — correctly reflects uncertainty         │
│ accumulation through the inference chain.                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Stage 4: T3a Retrieval (parallel with T2) [NEW]

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ query: "Does a company with strong LTV-CAC ratio..."            │
│ coverage.relevant_vyaptis: ["V01", "V12"]                        │
│ t2b_source_sections: {"V12": ["ch02"]}                           │
│                                                                  │
│ Cross-link: V12 activated → boost ch02 sections                  │
└──────────────────────────────────────────────────────────────────┘

                    ▼ retrieve_for_predicates() ▼

  Activated sections: {"V12": ["ch02"]}
  Boost chapters: {"ch02"}

  Fallback retrieval (no FAISS available):
    Token overlap scoring:
      ch02_s001: score = (query ∩ chunk) / query × 1.5 (section boost)
                                                × 1.2 (vyapti anchor)
      ch02_s002: score = overlap × 1.5 (section boost) × 1.2 (anchor)
      ch04_s001: score = overlap × 1.0 (no boost)

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ retrieved_chunks: [                                              │
│   [ch02_s001] "### 2.1 The LTV-CAC Relationship..."             │
│     chapter=ch02, vyaptis=[V01, V12]  ← BOOSTED (ch02)          │
│                                                                  │
│   [ch02_s002] "### 2.2 The Death Spiral..."                      │
│     chapter=ch02, vyaptis=[V13]       ← BOOSTED (ch02)          │
│                                                                  │
│   [ch04_s001] "### 4.1 Information Asymmetry..."                 │
│     chapter=ch04, vyaptis=[V03]       (not boosted)              │
│ ]                                                                │
│                                                                  │
│ T2b cross-link effect: ch02 chunks promoted to top of results    │
│ because V12 (activated predicate) has source_section ch02.       │
└──────────────────────────────────────────────────────────────────┘
```

---

## Stage 5: Contestation (vāda)

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ ArgumentationFramework (5 arguments, 0 attacks)                  │
│ contestation_mode: "vada"                                        │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Grounded Semantics ▼

  Iteration 1:
    A0000: no attackers → IN
    A0001: no attackers → IN
    A0002: no attackers → IN
    A0003: no attackers → IN
    A0004: no attackers → IN
  Fixpoint reached.

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ labels: {A0000: IN, A0001: IN, A0002: IN, A0003: IN, A0004: IN}│
│ contestation: {mode: "vada", open_questions: []}                 │
│ extension_size: 5                                                │
└──────────────────────────────────────────────────────────────────┘
```

---

## Stage 6: Epistemic Status Derivation

```
┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ results: {                                                       │
│   "ltv_exceeds_cac": {                                          │
│     status: PROVISIONAL                                          │
│     belief: 0.7000, disbelief: 0.0000, uncertainty: 0.3000      │
│     derivation_depth: 0, sources: []                             │
│   },                                                             │
│   "positive_contribution_margin": {                              │
│     status: PROVISIONAL                                          │
│     belief: 0.7000, disbelief: 0.0000, uncertainty: 0.3000      │
│     derivation_depth: 0, sources: []                             │
│   },                                                             │
│   "positive_unit_economics": {                                   │
│     status: HYPOTHESIS                                           │
│     belief: 0.7070, disbelief: 0.0383, uncertainty: 0.2548      │
│     ↑ Two arguments (premise + V12): ⊕ combines beliefs         │
│       A0000 premise (b=0.7) ⊕ A0004 via V12 (b=0.277)          │
│       → oplus raises belief slightly, adds disbelief             │
│     derivation_depth: 0                                          │
│     sources: [src_hbs_unit_economics]                            │
│   },                                                             │
│   "value_creation": {                                            │
│     status: PROVISIONAL                                          │
│     belief: 0.6650, disbelief: 0.0000, uncertainty: 0.3350      │
│     derivation_depth: 0                                          │
│     sources: [src_hbs_unit_economics, src_ries_2011]             │
│   }                                                              │
│ }                                                                │
└──────────────────────────────────────────────────────────────────┘
```

---

## Stages 7-9: Provenance, Uncertainty, Violations

```
┌─ PROVENANCE (Stage 7) ───────────────────────────────────────────┐
│ ltv_exceeds_cac:                                                 │
│   pramana: PRATYAKSA (direct observation), trust: 1.0, decay: 1.0│
│ positive_contribution_margin:                                    │
│   pramana: PRATYAKSA, trust: 1.0, decay: 1.0                    │
│ positive_unit_economics:                                         │
│   pramana: PRATYAKSA, trust: 1.0, decay: 1.0                    │
│   sources: [src_hbs_unit_economics]                              │
│ value_creation:                                                  │
│   pramana: ANUMANA (inference), trust: 0.8550, decay: 1.0       │
│   sources: [src_hbs_unit_economics, src_ries_2011]               │
└──────────────────────────────────────────────────────────────────┘

┌─ UNCERTAINTY (Stage 8) ──────────────────────────────────────────┐
│ ltv_exceeds_cac:                                                 │
│   total_confidence: 0.7000                                       │
│   epistemic: provisional — moderate evidence, working hypothesis │
│ positive_contribution_margin:                                    │
│   total_confidence: 0.7000                                       │
│   epistemic: provisional                                         │
│ positive_unit_economics:                                         │
│   total_confidence: 0.7070                                       │
│   epistemic: hypothesis — two supporting arguments combined      │
│ value_creation:                                                  │
│   total_confidence: 0.5686                                       │
│   epistemic: provisional — derived via inference chain           │
│   ↑ Lower total_confidence reflects derivation uncertainty       │
└──────────────────────────────────────────────────────────────────┘

┌─ VIOLATIONS (Stage 9) ───────────────────────────────────────────┐
│ No violations detected.                                          │
│ No hetvābhāsa attacks with IN label.                             │
└──────────────────────────────────────────────────────────────────┘
```

---

# SCENARIO 2: SYNONYM Coverage — Synonym Table Matching

**Query:** "How does a supply chain bottleneck affect a company's unit economics?"

This query uses a term ("supply_chain_bottleneck") not in the KB vocabulary, but matched via the synonym table built by T2b.

---

## Stage 1: Semantic Coverage Analysis

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ grounded_predicates: [                                           │
│   "supply_chain_bottleneck(acme)",                               │
│   "positive_unit_economics(acme)"                                │
│ ]                                                                │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Three-Layer Matching ▼

  supply_chain_bottleneck(acme):
    Strip entity → "supply_chain_bottleneck"
    Layer 1 (exact): NOT in vocabulary ✗
    Layer 2 (synonym): synonym_table["supply_chain_bottleneck"]
                       = "binding_constraint_identified" ∈ vocabulary ✓
    → MATCHED (synonym)
    → Relevant vyāptis: [V02]

  positive_unit_economics(acme):
    Layer 1 (exact): "positive_unit_economics" ∈ vocabulary ✓
    → MATCHED (exact)
    → Relevant vyāptis: [V01, V12]

  Coverage = 2/2 = 1.00

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ coverage_ratio: 1.00                                             │
│ decision: "FULL"                                                 │
│ match_details: {                                                 │
│   "supply_chain_bottleneck(acme)": "synonym",   ← T2b synonym   │
│   "positive_unit_economics(acme)": "exact"                       │
│ }                                                                │
│ relevant_vyaptis: ["V01", "V02", "V12"]                          │
└──────────────────────────────────────────────────────────────────┘
```

**Key insight:** Without the synonym table from T2b, `supply_chain_bottleneck` would NOT match `binding_constraint_identified` via exact or token overlap (Jaccard = 0.0). The synonym table bridges this gap.

---

## Stage 3: T2 Compilation — Chain Derivation

```
  query_facts: [
    {predicate: "binding_constraint_identified", conf: 0.65},
    {predicate: "positive_unit_economics", conf: 0.70}
  ]

  Forward chain with augmented KB (14 vyāptis):

    A0000: binding_constraint_identified [premise, b=0.650]

    A0001: positive_unit_economics [premise, b=0.700]

    V01 fires: positive_unit_economics → value_creation
      A0002: value_creation [via V01, b=0.665]

    V02 fires: binding_constraint_identified → resource_allocation_effective
      A0003: resource_allocation_effective [via V02, b=0.618]

    V08 fires: value_creation + resource_allocation_effective → long_term_value
      A0004: long_term_value [via V08, b=0.390]

  → 5 arguments, 0 attacks
  → 3-rule chain: premise → V01/V02 → V08 → long_term_value

  Inference chain:
    binding_constraint_identified ──V02──▶ resource_allocation_effective ─┐
                                                                          ├──V08──▶ long_term_value
    positive_unit_economics ──V01──▶ value_creation ──────────────────────┘
```

---

# SCENARIO 3: DECLINE — T3b Augmentation Path

**Query:** "How does Tesla's vertical integration strategy affect its competitive position in the EV market?"

All 3 predicates have 0.0 coverage. T3b augmentation generates new HYPOTHESIS vyāptis, merges into KB copy, then runs T2.

---

## Stage 1: Semantic Coverage Analysis

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ grounded_predicates: [                                           │
│   "vertical_integration(tesla)",                                 │
│   "ev_market_position(tesla)",                                   │
│   "manufacturing_efficiency(tesla)"                              │
│ ]                                                                │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Three-Layer Matching ▼

  vertical_integration(tesla):
    Layer 1 (exact): NOT in vocabulary ✗
    Layer 2 (synonym): NOT in synonym_table ✗
    Layer 3 (token): best Jaccard = "strategic_commitment" (0.0) ✗
    → UNMATCHED

  ev_market_position(tesla):
    Layer 1-3: all fail → UNMATCHED

  manufacturing_efficiency(tesla):
    Layer 1-3: all fail → UNMATCHED

  Coverage = 0/3 = 0.00

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ coverage_ratio: 0.00                                             │
│ decision: "DECLINE"          (0.00 < PARTIAL_THRESHOLD 0.2)     │
│ matched_predicates: []                                           │
│ unmatched_predicates: [                                          │
│   "vertical_integration(tesla)",                                 │
│   "ev_market_position(tesla)",                                   │
│   "manufacturing_efficiency(tesla)"                              │
│ ]                                                                │
└──────────────────────────────────────────────────────────────────┘
```

---

## Stage 2: Routing → DECLINE + in-domain → T3b Augmentation [NEW]

```
┌─ T3b AugmentationPipeline ──────────────────────────────────────┐
│                                                                  │
│ STEP 1: ScoreFrameworkApplicability (1 LLM call)                 │
│   Input: query = "How does Tesla's vertical integration..."     │
│   Input: framework_summary = "Domain: CRAFT, 14 vyāptis,        │
│          axes: value creation, constraint cascade, information   │
│          asymmetry, organizational entropy, optionality..."      │
│   Input: domain_type = "CRAFT"                                   │
│                                                                  │
│   Output: applicability_score = 0.65                             │
│           applicable_vyaptis = ["V01", "V02", "V03", "V06","V08"]│
│           applicable_chapters = ["ch02", "ch06"]                 │
│                                                                  │
│   → Score 0.65 ≥ 0.4 threshold → PROCEED                        │
│                                                                  │
│ STEP 2: GenerateAugmentationPredicates (1 LLM call)              │
│   Input: applicable_vyaptis (full text of V01, V02, V03, V06,V08)
│   Input: existing_predicates (25 names)                          │
│   Input: chapter_context (ch02, ch06 titles + key terms)         │
│                                                                  │
│   Output (parallel lists):                                       │
│     V15: "Vertical Integration Value Test"                       │
│       antecedents: [vertical_integration,manufacturing_efficiency]│
│       consequent: competitive_advantage_sustainable              │
│       confidence_existence: 0.65 (≤ 0.75 cap ✓)                 │
│       epistemic_status: WORKING_HYPOTHESIS                       │
│       origin: LLM_PARAMETRIC                                     │
│       parent: V06 (template vyāpti)                              │
│                                                                  │
│     V16: "Manufacturing Scale Advantage"                         │
│       antecedents: [manufacturing_efficiency]                    │
│       consequent: cost_leadership                                │
│       confidence_existence: 0.60 (≤ 0.75 cap ✓)                 │
│       epistemic_status: WORKING_HYPOTHESIS                       │
│       origin: LLM_PARAMETRIC                                     │
│       parent: V02 (template vyāpti)                              │
│                                                                  │
│ STEP 3: Validate (0 LLM calls)                                   │
│   Cycle detection: no cycles with V15, V16 ✓                     │
│   Datalog compile: all rules terminate ✓                         │
│                                                                  │
│ STEP 4: Merge into KB copy                                       │
│   merged_kb = augmented_ks.model_copy(deep=True)                 │
│   merged_kb.vyaptis["V15"] = V15                                 │
│   merged_kb.vyaptis["V16"] = V16                                 │
│   → merged_kb: 16 vyāptis (11 base + 3 fine + 2 augmented)      │
│                                                                  │
│ AugmentationResult:                                              │
│   augmented: True                                                │
│   framework_score: 0.65                                          │
│   new_vyapti_count: 2                                            │
│   merged_kb: KnowledgeStore (16 vyāptis)                         │
└──────────────────────────────────────────────────────────────────┘
```

---

## Stage 3: T2 Compilation with Augmented KB

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ merged_ks: KnowledgeStore (16 vyāptis, includes V15, V16)       │
│ query_facts: [                                                   │
│   {predicate: "vertical_integration", conf: 0.65},              │
│   {predicate: "manufacturing_efficiency", conf: 0.60}           │
│ ]                                                                │
└──────────────────────────────────────────────────────────────────┘

         ▼ Forward Chain ▼

  A0000: vertical_integration [premise, b=0.650]
  A0001: manufacturing_efficiency [premise, b=0.600]

  V15 fires: vertical_integration + manufacturing_efficiency
             → competitive_advantage_sustainable
    A0002: competitive_advantage_sustainable [via V15, b=0.218]
           origin: LLM_PARAMETRIC ← augmented
           epistemic_status: WORKING_HYPOTHESIS
           ↑ Low belief (0.218) because:
             V15 confidence = 0.65×0.55 trust
             × premise beliefs (0.65 × 0.60) = attenuated

  V16 fires: manufacturing_efficiency → cost_leadership
    A0003: cost_leadership [via V16, b=0.346]
           origin: LLM_PARAMETRIC ← augmented

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ arguments: {                                                     │
│   A0000: vertical_integration [premise, b=0.650]                │
│   A0001: manufacturing_efficiency [premise, b=0.600]            │
│   A0002: competitive_advantage_sustainable [via V15, b=0.218]   │
│          [LLM_PARAMETRIC]                                        │
│   A0003: cost_leadership [via V16, b=0.346]                     │
│          [LLM_PARAMETRIC]                                        │
│ }                                                                │
│ attacks: []                                                      │
│                                                                  │
│ Key: Augmented conclusions have LOW belief (0.218, 0.346)        │
│ because confidence capped at 0.75 and HYPOTHESIS status gives    │
│ base belief=0.60. These will be flagged as OPEN/PROVISIONAL      │
│ in epistemic status — never appearing as ESTABLISHED.            │
└──────────────────────────────────────────────────────────────────┘
```

---

## Stage 5-6: Epistemic Status for Augmented Results

```
┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ competitive_advantage_sustainable:                               │
│   status: OPEN                                                   │
│   belief: 0.2177 → below ESTABLISHED (0.8) or even              │
│                     PROVISIONAL (0.5) threshold                  │
│   ↑ Correctly reflects HIGH UNCERTAINTY for LLM-generated       │
│     conclusions. Response will use heavy hedging language.        │
│                                                                  │
│ cost_leadership:                                                 │
│   status: PROVISIONAL                                            │
│   belief: 0.3462 → moderate uncertainty                          │
│   ↑ Derived through single augmented vyāpti, moderate confidence │
│                                                                  │
│ manufacturing_efficiency:                                        │
│   status: PROVISIONAL (belief: 0.6000)                           │
│                                                                  │
│ vertical_integration:                                            │
│   status: PROVISIONAL (belief: 0.6500)                           │
│                                                                  │
│ NOTE: No augmented conclusion reaches ESTABLISHED status.        │
│ This is BY DESIGN — confidence cap (0.75) + HYPOTHESIS status    │
│ ensures generated predicates never outrank curated KB in defeat. │
└──────────────────────────────────────────────────────────────────┘
```

---

## Stage 4: T3a Retrieval (DECLINE path — no cross-link)

```
  No activated predicate sections (coverage DECLINE → no relevant vyaptis)
  → Plain retrieval without section boosting

  Fallback token overlap scoring (no FAISS):
    ch02_s001: "LTV-CAC", "economics", "value" → low overlap
    ch06_s001: "Capital", "value", "allocation" → moderate overlap
    ch07_s001: "Disruption", "Incumbents" → some overlap ("strategy")

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ retrieved_chunks: [                                              │
│   [ch02_s001] "### 2.1 The LTV-CAC Relationship..."             │
│   [ch06_s001] "### 6.1 Capital Allocation..."                    │
│   [ch07_s001] "### 7.1 Disruption Theory..."                     │
│ ]                                                                │
│ Note: Less targeted than FULL coverage path (no cross-link boost)│
└──────────────────────────────────────────────────────────────────┘
```

---

# SCENARIO 4: DECLINE + Out-of-Domain

**Query:** "What is the best recipe for chocolate soufflé?"

All predicates unmatched. T3b domain check scores below threshold → decline response.

---

## Stage 1: Semantic Coverage Analysis

```
  grounded_predicates: [
    "chocolate_preparation(recipe)",
    "baking_technique(souffle)"
  ]

  All layers fail for both predicates:
    Layer 1 (exact): NOT in vocabulary ✗
    Layer 2 (synonym): NOT in synonym_table ✗
    Layer 3 (token): max Jaccard = 0.0 ✗

  Coverage = 0/2 = 0.00 → DECLINE
```

---

## Stage 2: Routing → DECLINE → T3b Domain Check → STOP

```
┌─ T3b AugmentationPipeline ──────────────────────────────────────┐
│                                                                  │
│ STEP 1: ScoreFrameworkApplicability (1 LLM call)                 │
│   Input: query = "What is the best recipe for chocolate soufflé?"│
│   Input: framework_summary = "Domain: CRAFT (business strategy), │
│          value creation, constraint cascade, information          │
│          asymmetry, organizational entropy..."                   │
│                                                                  │
│   Output:                                                        │
│     reasoning: "This is a culinary question. None of the         │
│                 framework's business strategy axes (unit          │
│                 economics, constraints, information asymmetry,   │
│                 organizational growth) apply to recipe creation." │
│     applicability_score: 0.05                                    │
│     applicable_vyaptis: []                                       │
│                                                                  │
│   → Score 0.05 < 0.4 threshold → STOP (out-of-domain)           │
│                                                                  │
│ AugmentationResult:                                              │
│   augmented: False                                               │
│   reason: "Framework applicability too low (0.05 < 0.4)"        │
│                                                                  │
│ Engine returns decline response:                                 │
│   "This query falls outside my domain's reasoning framework.    │
│    Framework applicability too low (0.05 < 0.4)"                 │
└──────────────────────────────────────────────────────────────────┘
```

---

# SUMMARY: Coverage Routing Decisions

```
┌──────────────────────────────────────────────────────────────────┐
│ Scenario │ Coverage │ Decision │ LLM Calls │ Route              │
├──────────────────────────────────────────────────────────────────┤
│ 1: FULL  │  1.00    │ FULL     │ 0         │ base+fine → T2→AF  │
│ 2: SYN   │  1.00    │ FULL     │ 0         │ synonym → T2→AF   │
│ 3: T3b   │  0.00    │ DECLINE  │ 2         │ T3b → merge → T2  │
│ 4: OOD   │  0.00    │ DECLINE  │ 1         │ decline response   │
└──────────────────────────────────────────────────────────────────┘

Coverage analysis: 0 LLM calls (fully deterministic)
T3b in-domain: 2 LLM calls (domain check + generate)
T3b out-of-domain: 1 LLM call (domain check only, stops early)
T3a retrieval: 0 LLM calls (embedding similarity only)
```

---

# ARCHITECTURE: Key Properties

## 1. Confidence Attenuation Through Chains

The provenance semiring ⊗ (tensor) operation ensures that confidence naturally decreases through longer inference chains. This is epistemically honest by construction.

```
  Scenario 1 (FULL): 3 premises → V01 derives value_creation
    positive_unit_economics:  b=0.700 (premise)
    value_creation:           b=0.665 (1-step chain via V01)
    positive_unit_economics:  b=0.277 (re-derived via V12, 2 sub-args)

  Scenario 3 (T3b): 2 premises → augmented V15/V16 derive conclusions
    vertical_integration:                     b=0.650 (premise)
    manufacturing_efficiency:                 b=0.600 (premise)
    competitive_advantage_sustainable (V15):  b=0.218 (augmented chain)
    cost_leadership (V16):                    b=0.346 (augmented chain)

  Augmented conclusions ALWAYS have lower belief than premises.
  Confidence cap (0.75) + HYPOTHESIS status ensures this.
```

## 2. T2b→T3a Cross-Linking

```
  compile_t2b() produces:
    source_sections: {"V12": ["ch02"], "V13": ["ch02"], "V14": ["ch02"]}

  At query time (Scenario 1):
    Coverage says relevant_vyaptis = ["V01", "V12"]
    V12 ∈ source_sections → activated_sections = {"V12": ["ch02"]}
    T3a boosts ch02 chunks → LTV-CAC chapter appears first

  At query time (Scenario 3):
    Coverage DECLINE → no relevant_vyaptis
    → T3a runs without cross-link (plain retrieval)
```

## 3. Augmented Vyāpti Safety Guarantees

| Property | Mechanism |
|----------|-----------|
| Confidence cap | `MAX_CONFIDENCE = 0.75` — never exceeds curated KB |
| Epistemic status | Always `WORKING_HYPOTHESIS` — never `ESTABLISHED` |
| Decay risk | Always `MODERATE` — signals impermanence |
| Evidence type | `"theoretical"` — clearly not empirical |
| Cycle detection | `_detect_cycles()` from `predicate_extraction.py` |
| Datalog compile | Full compile test with `DatalogEngine` |
| KB isolation | `model_copy(deep=True)` — no in-place mutation |
| Origin tracking | `AugmentationMetadata.origin = LLM_PARAMETRIC` |
| Domain gate | `APPLICABILITY_THRESHOLD = 0.4` — rejects out-of-domain |

## 4. Coverage Thresholds

| Threshold | Value | Meaning |
|-----------|-------|---------|
| `FULL_THRESHOLD` | 0.6 | ≥ 60% predicates matched → full inference |
| `PARTIAL_THRESHOLD` | 0.2 | ≥ 20% predicates matched → partial inference |
| `TOKEN_OVERLAP_MIN` | 0.4 | Minimum Jaccard score for token-based match |
| `APPLICABILITY_THRESHOLD` | 0.4 | Minimum framework applicability for T3b |

---

# FILES INVOLVED

| File | Role | Lines | LLM Calls |
|------|------|-------|-----------|
| `t2b_compiler.py` | Compile-time fine-grained extraction | ~150 | via Pipeline |
| `coverage.py` | 3-layer semantic coverage analysis | ~120 | 0 |
| `kb_augmentation.py` | T3b query-time augmentation | ~300 | 2/query |
| `t3a_retriever.py` | Embedding-based prose retrieval | ~100 | 0 |
| `engine_v4.py` | `forward_with_coverage()` orchestration | ~200 new | varies |
| `schema.py` | `AugmentationOrigin`, `AugmentationMetadata` | ~30 new | 0 |
| `predicate_extraction.py` | Stages A-E (reused by T2b) | 1124 | via Pipeline |
| `t2_compiler_v4.py` | Facts + rules → AF (unchanged) | 316 | 0 |
| `argumentation.py` | ASPIC+ framework (unchanged) | ~470 | 0 |
| `contestation.py` | vāda/jalpa/vitaṇḍā (unchanged) | ~300 | 0 |

---

# WHAT'S DEFERRED

| Item | Status | Notes |
|------|--------|-------|
| A-04: Depth-aware coverage | Deferred | Needs depth signal beyond coverage_ratio |
| A-05: Fine-grained KB versioning | Deferred | Needs incremental update pipeline |
| A-07: T3b→T2 backprop evaluation | Deferred | Needs ablation study framework |
| Web search in T3b (v2) | Deferred | `AugmentationOrigin.WEB_SOURCED` ready |
| Shadow KB persistence (v3) | Deferred | `shadow_kb.py` + SQLite TBD |
| Sequential T3a (informed by AF) | Deferred | T3a currently runs parallel |
| Domain-aware contrariness | Deferred | Needs compiled contrariness relation |
