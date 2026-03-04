# ELI5: How the Full Anvikshiki Pipeline Actually Works — End to End

> A plain-English walkthrough of **every** pipeline stage, from raw guide text
> through predicate extraction to final query response.
> For each stage: **What** it does, **Why** it exists, and **How** it works.
>
> This document covers **two pipelines**:
> 1. **Offline:** The Predicate Extraction Pipeline (Stages A-F) — runs once per guide version
> 2. **Online:** The Query Pipeline (Stages 0-11) — runs per user query (~3.8s)
>
> Based on: Ch2 Unit Economics guide text, `business_expert.yaml` seed KB,
> Llama-3.2-3B-Instruct-4bit, lightweight grounding path.

---

## The Big Picture

Imagine you're building a reasoning engine for business strategy. You start with a textbook (the guide) and a small set of hand-written rules (the seed KB). The problem: the rules are too coarse. Your textbook has an entire chapter about LTV, CAC, contribution margin, and payback periods — but your rule set just says "positive_unit_economics → value_creation." That's like summarizing all of chemistry as "atoms exist."

The Predicate Extraction Pipeline reads your textbook and automatically discovers the finer-grained concepts hiding inside your coarse rules. Then the Query Pipeline uses those richer rules to answer questions with more precise, traceable reasoning.

**Two key insights:**
1. The LLM is used for **extraction** (finding concepts in text) and **translation** (English ↔ predicates) and **writing** (composing the final response). It never decides what's true.
2. All actual reasoning — forward chaining, conflict detection, evidence weighing — is done by the symbolic engine. Deterministic, auditable, grounded in formal logic.

---

# PART 1: THE OFFLINE PIPELINE — Teaching the Engine New Concepts

> This runs once per guide version. It takes ~5-10 minutes and ~70-100 LLM calls.
> The output is an enriched knowledge base with 2-3x more predicates and rules.

---

## The Setup (Before We Start)

**The guide text:** Chapter 2 of a business strategy guide — "Unit Economics: The Physics of Business Viability." Six sections covering LTV-CAC, contribution margin, payback period, economies of scale, death spirals, and maturity mismatch.

**The seed KB:** `business_expert.yaml` — 11 rules (vyaptis), 23 predicates, 8 fallacy detectors, 22 academic sources. Hand-authored by a domain expert.

**The problem:**

```
What the guide teaches:             What the KB knows:
  Section 2.1: LTV must exceed CAC     positive_unit_economics
  Section 2.2: Contribution margin       (that's it — one predicate
  Section 2.3: Payback period < runway    for an entire chapter)
  Section 2.4: Real vs imagined scale
  Section 2.5: Death spiral dynamics
  Section 2.6: Maturity mismatch

The guide has ~14 distinct testable concepts.
The KB has 2 predicates for this chapter.
```

The KB is **epistemically honest but strategically mute**. It qualifies confidence correctly but can't reason about the concepts the guide actually teaches. If a user asks "Does having a strong LTV-CAC ratio matter?", the engine can't even represent `ltv_exceeds_cac` as a predicate — it doesn't exist in the vocabulary.

**The goal:** Automatically extract those ~14 concepts from the guide text, connect them to the existing rules, validate everything, and produce an enriched KB that the query pipeline can use.

---

## Stage A: Extract Candidate Predicates — "Read the Textbook and Take Notes"

### What
Scan each section of the guide text and extract **testable domain predicates** — claims that can be true or false about a specific entity. Look for causal claims ("X causes Y"), conditionals ("if X then Y"), metrics ("X is measured by Y"), scope conditions ("X holds only when Y"), and negations ("X prevents Y").

### Why
The seed KB was written by a human who made chapter-level abstractions. That human read "LTV must exceed CAC" and "contribution margin must be positive" and "payback period must be within runway" and compressed all of that into one predicate: `positive_unit_economics`. Useful for high-level reasoning, but you lose the ability to reason about the individual components.

Stage A reverses this compression. It reads the same text the human read and extracts the section-level concepts that were compressed away.

Think of it like this: the human wrote the table of contents. Stage A reads the actual chapters and writes the index.

### How
The pipeline splits the guide into sections (at `###` boundaries), then sends each section to the LLM with a DSPy `ChainOfThought` signature:

```
For each section of guide text:

  INPUT:
    section_text:       "### 2.1 The LTV-CAC Relationship
                         The most fundamental equation: LTV must exceed CAC.
                         When LTV > CAC, each new customer adds value..."
    chapter_id:         "ch02"
    existing_predicates: "positive_unit_economics, value_creation, ..."
    domain_context:     "CRAFT — business strategy"

  LLM TASK:
    "Extract domain predicates from this text. A predicate is a testable
     property. Look for causal claims, conditionals, metrics. Use snake_case.
     Return empty list if none found."

  OUTPUT:
    candidates: [
      {name: "ltv_exceeds_cac",
       description: "Lifetime value exceeds customer acquisition cost",
       claim_type: "metric",
       provenance: {section: "2.1", sentence: "LTV must exceed CAC",
                    confidence: 0.92},
       related_existing_vyapti: "V01"},

      {name: "high_arpu",
       description: "Average revenue per user is above threshold",
       claim_type: "metric",
       provenance: {section: "2.1", ...}},

      {name: "high_retention_rate",
       description: "Customer retention rate is high (low churn)",
       claim_type: "metric", ...}
    ]
```

Each candidate comes with:
- A **snake_case name** (enforced by regex — the system rewrites `HighARPU` to `high_arpu` automatically)
- A **one-sentence description** (what does this predicate mean?)
- A **claim type** (how does this predicate relate to others?)
- A **provenance** record (where exactly in the text did this come from?)
- A link to the **existing vyapti** it relates to (if any)

The LLM's output is scored by a reward function:

| Criterion | Weight | What It Checks |
|-----------|--------|----------------|
| Valid snake_case | 0.20 | No spaces, CamelCase, or special characters |
| Novel (not in existing KB) | 0.15 | Don't re-extract what we already have |
| Provenance quality | 0.20 | Exact sentence cited, not vague reference |
| Non-empty extraction | 0.20 | Don't return empty list for content-rich sections |
| Reasoning present | 0.15 | The LLM showed its work |
| Count within cap | 0.10 | Not more than 15 per chapter |

**What you get from Chapter 2:** ~14 candidate predicates across 6 sections:
- From 2.1: `ltv_exceeds_cac`, `high_arpu`, `high_retention_rate`
- From 2.2: `positive_contribution_margin`, `gross_margin_not_contribution_margin`
- From 2.3: `payback_within_runway`, `short_payback_period`
- From 2.4: `economies_of_scale_real`, `imagined_economies_of_scale`, `network_effects_present`
- From 2.5: `negative_unit_economics`, `unit_economics_death_spiral`
- From 2.6: `maturity_mismatch`, `cohort_ltv_declining`

**What you DON'T get:** `positive_unit_economics` and `value_creation` — these already exist in the seed KB. The reward function penalizes re-extracting known predicates.

**Claim types (6-class taxonomy) — why they matter:**

| Type | Pattern | Why It Matters |
|------|---------|----------------|
| CAUSAL | "X causes Y" | Becomes a vyapti rule: X → Y |
| CONDITIONAL | "If X then Y" | Becomes a scoped vyapti |
| METRIC | "X is measured by Y" | Becomes a composing antecedent |
| DEFINITIONAL | "X means Y" | Links to existing predicates |
| SCOPE | "X only when Y" | Becomes a scope_condition |
| NEGATION | "X prevents Y" | Becomes a rebutting relationship |

The claim type tells Stage D how to wire the predicate into a rule.

**Source:** `predicate_extraction.py:ExtractPredicates`, `predicate_extraction.py:_stage_a()`

---

## Stage B: Hierarchical Decomposition — "What's Inside Each Rule?"

### What
For each existing vyapti in the seed KB, identify the sub-predicates that **compose** its antecedents or consequent. Build a predicate hierarchy: depth 0 = chapter-level (existing), depth 1 = section-level (new), depth 2 = paragraph-level (new).

### Why
Stage A found ~14 new predicates. But they're floating — they're not connected to the existing rules yet. We know `ltv_exceeds_cac` exists in the text, and we know `positive_unit_economics` exists in the KB, but we haven't formally established that one composes the other.

Stage B does the connecting. It asks: "V01 says `positive_unit_economics → value_creation`. But what *is* positive unit economics? The guide text says it's composed of LTV exceeding CAC, positive contribution margin, and payback within runway. Let's make that structure explicit."

Think of it like taking a box labeled "TOOLS" and listing what's actually inside: hammer, screwdriver, wrench. Now you can reason about individual tools instead of just "do I have tools?"

### How

```
For each existing vyapti (11 in business_expert.yaml):

  INPUT:
    vyapti_summary:     "V01: positive_unit_economics → value_creation
                         (empirical, established, conf=0.95x0.9)"
    guide_excerpt:       (the chapter text relevant to this vyapti)
    stage_a_candidates:  (candidates that cited this vyapti)

  LLM TASK:
    "What sub-predicates compose this vyapti's antecedents?
     What specific conditions or metrics does the text mention?"

  OUTPUT (for V01):
    sub_predicates: [
      {predicate: "ltv_exceeds_cac",
       parent: "positive_unit_economics",
       relation: COMPOSES,    ← parent = AND of children
       depth: 1},

      {predicate: "positive_contribution_margin",
       parent: "positive_unit_economics",
       relation: COMPOSES,
       depth: 1},

      {predicate: "payback_within_runway",
       parent: "positive_unit_economics",
       relation: COMPOSES,
       depth: 1}
    ]
    relation_type: "composes"
```

**The result — a predicate hierarchy:**
```
positive_unit_economics (depth 0, existing)
  ├── ltv_exceeds_cac (depth 1, composes)    ← NEW
  ├── positive_contribution_margin (depth 1, composes)  ← NEW
  └── payback_within_runway (depth 1, composes)  ← NEW
```

**Three relation types:**

| Relation | Meaning | In Datalog |
|----------|---------|------------|
| **COMPOSES** | Parent = AND of children | `parent :- child1, child2, child3.` |
| **ALTERNATIVE** | Children are OR paths | `parent :- child1.` and `parent :- child2.` |
| **SUBSUMES** | Parent generalizes child | Child implies parent (no new rule needed) |

COMPOSES is the most common: "positive unit economics = LTV exceeds CAC AND contribution margin is positive AND payback is within runway."

**Source:** `predicate_extraction.py:DecomposeVyapti`, `predicate_extraction.py:_stage_b()`

---

## Stage C: Canonicalize & Deduplicate — "Are These the Same Thing?"

### What
Find predicates that mean the same thing but have different names. Pick the best name. Merge them.

### Why
Stage A processes each section independently. Section 2.1 might extract `ltv_above_cac`. Section 2.3 might extract `ltv_exceeds_cac`. Section 2.5 might extract `ltv_greater_than_cac`. These are the same concept with three different names. If we keep all three, the Datalog engine fragments its reasoning across synonyms — a rule using `ltv_above_cac` won't fire when only `ltv_exceeds_cac` is asserted as a fact.

Deduplication ensures one concept = one name, everywhere.

### Why embedding-first?
The naive approach: send all ~60 candidates to an LLM and ask "which are synonyms?" This works but costs a lot of tokens. The smart approach: compute embedding vectors for all candidate names, cluster by cosine similarity, and only ask the LLM about ambiguous clusters.

```
Step 1: Compute embeddings for all predicate names
Step 2: Cosine similarity matrix

  ltv_above_cac ↔ ltv_exceeds_cac      = 0.97  ← clearly synonyms
  ltv_above_cac ↔ high_arpu             = 0.41  ← clearly different
  positive_cm   ↔ positive_contribution_margin = 0.89  ← ambiguous

Step 3: Unambiguous clusters (similarity > 0.95) → merge automatically
        Ambiguous clusters (0.75-0.95) → ask LLM to resolve
        Distinct (< 0.75) → keep separate
```

### How

```
INPUT:
  All candidates from Stage A + Stage B decompositions
  Existing predicate names from seed KB

PROCESSING:
  1. Collect all unique predicate names (~60 across all chapters)
  2. Compute embedding vectors
  3. Cluster by cosine similarity (threshold=0.85)
  4. Auto-merge clear synonyms (>0.95 similarity)
  5. LLM resolves ambiguous clusters (0.75-0.95)
  6. Build rename map: old_name → canonical_name

  Example:
    Cluster: {ltv_above_cac, ltv_exceeds_cac, ltv_greater_than_cac}
    Canonical: "ltv_exceeds_cac"
      (picked because it matches the existing naming convention
       and is the most descriptive)

OUTPUT:
  unique_predicates: 14 (was ~18 before dedup)
  synonym_clusters: [{canonical: "ltv_exceeds_cac",
                       synonyms: ["ltv_above_cac", "ltv_greater_than_cac"]}]
  rename_map: {"ltv_above_cac": "ltv_exceeds_cac", ...}
```

**Cost savings:** For a 60-candidate vocabulary, the all-LLM approach would need ~1 long-context LLM call (or multiple pairwise calls). The embedding-first approach uses 0 LLM calls for clear clusters and ~1 call for the handful of ambiguous ones. 60-80% cost reduction.

**Source:** `predicate_extraction.py:ResolveSynonyms`, `predicate_extraction.py:_stage_c()`

---

## Stage D: Construct New Vyaptis — "Write the Rules"

### What
From the deduplicated predicates and their relationships (from Stages A-C), construct complete **vyapti** objects — the inference rules the symbolic engine uses to chain facts together.

### Why
Raw predicates are vocabulary. Without rules connecting them, the engine can't derive anything. If we have `ltv_exceeds_cac` and `positive_contribution_margin` as predicates but no rule saying "when both are true, positive_unit_economics follows," the engine just stores two isolated facts and shrugs.

Stage D reads the guide text to understand the *relationships* between predicates and formalizes them as vyaptis. The guide says "LTV must exceed CAC AND contribution margin must be positive for unit economics to work." Stage D turns that into:

```yaml
V12:
  name: "LTV-CAC Viability Test"
  IF: ltv_exceeds_cac AND positive_contribution_margin
  THEN: positive_unit_economics
```

Now the engine can *reason*: if someone asserts `ltv_exceeds_cac(acme)` and `positive_contribution_margin(acme)`, the engine fires V12 and derives `positive_unit_economics(acme)`, then fires V01 and derives `value_creation(acme)`. A two-step inference chain — impossible with the seed KB alone.

### How

```
For each predicate relationship identified:

  INPUT:
    predicate_relationship: "ltv_exceeds_cac AND positive_contribution_margin
                             → positive_unit_economics"
    guide_evidence:          (the section text supporting this relationship)
    existing_vyaptis_context: (V01 summary for reference)
    reference_bank:           (relevant academic sources)

  LLM TASK (DSPy Refine, N=3 candidates):
    "Construct a complete vyapti. Be CONSERVATIVE:
     epistemic_status = 'hypothesis' unless text provides strong evidence."

  REWARD FUNCTION:
    Penalizes overconfidence:
      epistemic_status MUST be "hypothesis" (not "established")
      confidence_existence ≤ 0.85 (capped — extracted rules are never
        as certain as hand-authored ones)
      confidence_formulation ≤ 0.85 (capped)
      All required fields populated
      Antecedents ⊆ known predicates (no references to non-existent predicates)
      No circular references

  OUTPUT:
    ProposedVyapti(
      id="V12",
      name="LTV-CAC Viability Test",
      statement="When LTV exceeds CAC and contribution margin is positive,
                 unit economics are positive",
      causal_status="empirical",
      antecedents=["ltv_exceeds_cac", "positive_contribution_margin"],
      consequent="positive_unit_economics",
      scope_conditions=["commercial_enterprise"],
      scope_exclusions=["subsidized_entity"],
      confidence_existence=0.85,     ← CAPPED, never higher
      confidence_formulation=0.80,   ← CAPPED
      evidence_type="observational",
      epistemic_status="hypothesis", ← CONSERVATIVE default
      sources=["src_hbs_unit_economics"],
      parent_vyapti="V01"            ← traces back to original
    )
```

**Why the conservative defaults?** An LLM reading a textbook passage is less reliable than a human expert carefully authoring a rule. The confidence caps (≤0.85) and the `hypothesis` default mean that extracted vyaptis are always treated as less certain than the original hand-authored ones (which can be `established` with confidence 0.95). This is epistemically honest: the extraction process adds uncertainty, and the system should reflect that.

**What Stage D produces for Chapter 2:**

| New Vyapti | Antecedents | Consequent | Status |
|------------|------------|------------|--------|
| V12 | ltv_exceeds_cac, positive_contribution_margin | positive_unit_economics | hypothesis |
| V13 | negative_unit_economics | unit_economics_death_spiral | hypothesis |
| V14 | maturity_mismatch | negative_unit_economics | hypothesis |
| V15 | payback_within_runway | positive_unit_economics | hypothesis |
| ... | ... | ... | ... |

**Source:** `predicate_extraction.py:ConstructVyapti`, `predicate_extraction.py:_stage_d()`

---

## Stage E: Validate & Merge — "Check the Math"

### What
Before adding anything to the knowledge base, check that the proposed vyaptis don't break anything. Five checks, all deterministic (zero LLM calls):

1. **No cycles in the predicate graph** — prevents infinite loops in Datalog evaluation
2. **All fields pass Pydantic validation** — correct types, valid enums, confidence in [0,1]
3. **Everything compiles in Datalog** — the augmented KB produces a terminating evaluation
4. **No existing rules were modified** — the pipeline is purely additive
5. **Meaningful expansion** — we actually gained new predicates

### Why
LLMs make mistakes. Stage D might produce a vyapti that creates a cycle: A → B and B → A. In Datalog, this means the engine would loop forever (or hit the safety bound). Stage E catches this before it reaches the KB.

LLMs also hallucinate field values. A vyapti with `causal_status="very_strong"` would crash the engine — `very_strong` isn't a valid enum value. Pydantic catches this.

Stage E is the **safety gate**. Nothing enters the KB without passing all five checks. And because Stage E is fully deterministic, it's reproducible — run it twice on the same input, get the same result.

### How

```
INPUT:
  Original KnowledgeStore (11 vyaptis, 23 predicates)
  Proposed vyaptis from Stage D (~15 new vyaptis)

STEP E1: Cycle Detection
  Build a directed graph: predicate → predicate (from all vyapti rules)
  Run DFS topological sort
  If any cycle found → remove the offending vyaptis

  Example check:
    V12: ltv_exceeds_cac → positive_unit_economics    ✓ (no cycle)
    V01: positive_unit_economics → value_creation      ✓ (no cycle)
    V14: maturity_mismatch → negative_unit_economics   ✓ (no cycle)
    V13: negative_unit_economics → death_spiral         ✓ (no cycle)
    No cycles detected.

  WHY THIS MATTERS:
    Datalog with no cycles = stratifiable program = unique minimal model.
    This is a theorem (Apt, Blair & Walker 1988). No cycles → the engine
    always computes the same answer, always terminates. Guaranteed.

STEP E2: Pydantic Validation
  For each ProposedVyapti, convert to schema.Vyapti:
    CausalStatus("empirical")      → valid ✓
    EpistemicStatus("hypothesis")  → valid ✓
    Confidence(0.85, 0.80)         → both in [0,1] ✓

  If conversion fails → reject that vyapti (but keep the others)

STEP E3: Datalog Test-Compilation
  Load the augmented KB into the DatalogEngine
  Add synthetic facts for ALL antecedent predicates
  Call evaluate() with safety bound (MAX_ITERATIONS=100)
  Must terminate within bound

  This catches subtle issues like:
    - Predicates referenced in antecedents but never defined anywhere
    - Rule interactions that cause fixpoint blowup

STEP E4: Monotone Enrichment Check
  Verify: original_vyaptis ⊆ augmented_vyaptis
  No existing vyapti was modified or deleted
  Only additions allowed

STEP E5: Coverage Ratio
  coverage = (new_predicates - old_predicates) / new_predicates
  23 old → 50 new → (50-23)/50 = 54%

OUTPUT:
  ValidationResult(
    is_valid=True,
    cycle_errors=[],
    orphan_predicates=[],
    datalog_errors=[],
    coverage_ratio=0.54
  )

  augmented_ks: KnowledgeStore(
    vyaptis: V01..V11 (original) + V12..V25 (new)
    predicates: 23 → ~50
    All Pydantic-validated, all Datalog-compilable, DAG-acyclic
  )
```

**The five invariants in plain English:**

| # | Name | Plain English | What Breaks Without It |
|---|------|---------------|----------------------|
| I1 | Flat predicates | No nested structures — just `name(entity)` | Datalog can't handle function symbols |
| I2 | DAG acyclicity | No circular rule chains | Engine loops forever |
| I3 | Schema conformance | All fields have correct types | Runtime crashes |
| I4 | Datalog compatibility | Rules compile and terminate | Engine hangs or errors |
| I5 | Monotone enrichment | Only additions, no deletions | Existing queries break |

**Source:** `predicate_extraction.py:_stage_e()`, `predicate_extraction.py:_detect_cycles()`

---

## Stage F: Human-in-the-Loop Review — "Does This Look Right?"

### What
Present each proposed vyapti as a YAML diff for a human domain expert to review. They accept, reject, or flag for modification.

### Why
LLM extraction is imperfect. A human expert catches things Stage E can't:

- "This rule says contribution margin → profitability, but that's only true if fixed costs are covered. Missing scope condition."
- "This confidence of 0.85 is too high — the text hedges this claim heavily."
- "These two vyaptis are redundant — V12 already covers what V15 says."

Stage E checks *formal* correctness (no cycles, valid types). Stage F checks *semantic* correctness (does the rule accurately capture what the text says?).

### How

```
The HITL reviewer renders each proposed vyapti as a diff:

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
  + confidence:
  +   existence: 0.85
  +   formulation: 0.80
  + epistemic_status: hypothesis

  [a]ccept  [r]eject  [m]odify  [q]uit
  Decision: a
  -> Accepted

============================================================
  Proposed Vyapti 2/14: V13
============================================================
  ...
```

The reviewer sees every proposed vyapti, one by one. They can:
- **Accept** — add it to the KB as-is
- **Reject** — discard it entirely
- **Modify** — flag for later manual editing

After all decisions, the reviewer gets a summary:

```
Done: {accepted: 12, rejected: 1, modified: 1, pending: 0}
```

The result is the **final approved KnowledgeStore** — the enriched KB that the query pipeline will use.

**Two usage modes:**

```bash
# Interactive CLI (for domain experts)
python -m anvikshiki_v4.extraction_hitl \
  --kb business_expert.yaml \
  --proposed extraction_output.yaml \
  --output approved_kb.yaml

# Programmatic batch (for testing)
reviewer = HITLReviewer(original_ks, augmented_ks, stage_d, validation)
approved = reviewer.review_batch({
    "V12": ACCEPT, "V13": ACCEPT, "V14": REJECT, ...
})
```

**Source:** `extraction_hitl.py:HITLReviewer`

---

## What Changed — Before vs After the Extraction Pipeline

Let's see the concrete difference for Chapter 2 (Unit Economics):

```
BEFORE (seed KB):                  AFTER (augmented KB):
  1 vyapti (V01)                     5+ vyaptis (V01, V12-V15+)
  2 predicates:                      16 predicates:
    positive_unit_economics            positive_unit_economics (existing)
    value_creation                     value_creation (existing)
                                       ltv_exceeds_cac (NEW)
                                       high_arpu (NEW)
                                       high_retention_rate (NEW)
                                       positive_contribution_margin (NEW)
                                       gross_margin_not_contribution_margin (NEW)
                                       payback_within_runway (NEW)
                                       short_payback_period (NEW)
                                       economies_of_scale_real (NEW)
                                       imagined_economies_of_scale (NEW)
                                       network_effects_present (NEW)
                                       negative_unit_economics (NEW)
                                       unit_economics_death_spiral (NEW)
                                       maturity_mismatch (NEW)
                                       cohort_ltv_declining (NEW)
```

The reasoning depth changes too:

```
BEFORE:                             AFTER:
  User asks about LTV-CAC             User asks about LTV-CAC
    ↓ can only ground to:               ↓ can ground to:
  positive_unit_economics                ltv_exceeds_cac
    ↓ V01                               positive_contribution_margin
  value_creation                           ↓ V12 (NEW)
  (1 rule, no sub-components)           positive_unit_economics
                                           ↓ V01
                                         value_creation
                                         (2 rules, sub-component reasoning)
```

---

# PART 2: THE ONLINE PIPELINE — Answering Questions with the Enriched KB

> This runs per user query. Uses the augmented KnowledgeStore produced
> by Part 1. The query pipeline is architecturally unchanged — it
> automatically benefits from the richer vocabulary and rules.

---

## The Setup

**The question:** "Does a company with strong LTV-CAC ratio and positive contribution margin have viable unit economics?"

**The knowledge base:** The augmented KB from Part 1 — ~25 vyaptis, ~50 predicates.

**The model:** Llama-3.2-3B-Instruct-4bit running locally on MLX.

**What's different from the original ELI5 trace:** The original trace asked "Does a company with positive unit economics always create value?" — a question the seed KB could answer (barely). Our new question asks about LTV-CAC ratio and contribution margin — concepts that **only exist** in the enriched KB. With the seed KB, the engine couldn't even represent these concepts, let alone reason about them.

---

## Stage 0: Accept the Request

### What
Same as before — accept HTTP request, authenticate user, configure LLM, pick execution path.

### How
```
HTTP POST /api/queries/
├── JWT decoded → user identified
├── LLM config: Llama-3.2-3B, is_small_model=true
├── Route: Path B (lightweight grounding — 2 LLM calls)
└── QueryRecord created with status="processing"
```

No change from the original. The enriched KB doesn't affect routing.

**Source:** `routers/queries.py:22-31`

---

## Stage 1: Load the Knowledge Base

### What
Load the augmented KB YAML file. This is the enriched version from Part 1.

### Why this matters now
With the seed KB, this stage loaded 11 rules and 23 predicates. With the augmented KB, it loads ~25 rules and ~50 predicates. Everything downstream gets richer input.

### How
```
yaml.safe_load(file) → KnowledgeStore(**data)

Output:
  domain_type: CRAFT
  25 vyaptis:
    V01: positive_unit_economics → value_creation
         (empirical, established, conf=0.95x0.9)
    V12: ltv_exceeds_cac + positive_contribution_margin          ← NEW
         → positive_unit_economics
         (empirical, hypothesis, conf=0.85x0.80)
    V13: negative_unit_economics → unit_economics_death_spiral   ← NEW
         (empirical, hypothesis, conf=0.80x0.75)
    V14: maturity_mismatch → negative_unit_economics             ← NEW
         (empirical, hypothesis, conf=0.80x0.70)
    ...14 more new vyaptis
    ...V02-V11 unchanged

  50 predicates (was 23)
  8 hetvabhasas (unchanged)
  22+ academic sources
```

**Source:** `t2_compiler_v4.py:310-315`

---

## Stage 2: Build the Ontology Snippet

### What
Same as before — build the constrained vocabulary "cheat sheet" for the LLM. But now the cheat sheet has ~50 predicates instead of ~23.

### Why this matters now
With the seed KB, if a user asked about "LTV-CAC ratio," the LLM had no valid predicate to map it to. The closest option was `positive_unit_economics` — losing all the specificity. Now the LLM sees `ltv_exceeds_cac(Entity)` in the vocabulary and can map directly.

### How
```
OntologySnippetBuilder iterates all 25 vyaptis and produces:

VALID PREDICATES — use ONLY these:

RULE V01: The Value Equation
  IF: positive_unit_economics
  THEN: value_creation
  SCOPE: commercial_enterprise
  EXCLUDES: subsidized_entity

RULE V12: LTV-CAC Viability Test                    ← NEW
  IF: ltv_exceeds_cac, positive_contribution_margin
  THEN: positive_unit_economics
  SCOPE: commercial_enterprise
  EXCLUDES: subsidized_entity

RULE V13: Unit Economics Death Spiral                ← NEW
  IF: negative_unit_economics
  THEN: unit_economics_death_spiral

RULE V14: Maturity Mismatch Warning                  ← NEW
  IF: maturity_mismatch
  THEN: negative_unit_economics

...(21 more rules)

ALL VALID PREDICATE NAMES:
  - cohort_ltv_declining(Entity)                     ← NEW
  - economies_of_scale_real(Entity)                  ← NEW
  - high_arpu(Entity)                                ← NEW
  - high_retention_rate(Entity)                      ← NEW
  - ltv_exceeds_cac(Entity)                          ← NEW
  - maturity_mismatch(Entity)                        ← NEW
  - negative_unit_economics(Entity)                  ← NEW
  - positive_contribution_margin(Entity)             ← NEW
  - positive_unit_economics(Entity)
  - unit_economics_death_spiral(Entity)              ← NEW
  - value_creation(Entity)
  ...(39 more)
```

The ontology snippet roughly **doubled** in size. The LLM now has a much richer vocabulary to work with.

**Source:** `grounding.py:98-143`

---

## Stage 3: LLM Grounding — Translate English to Predicates

### What
Send the user's question + ontology snippet to the LLM. The LLM reads the question, looks at the valid predicates, and picks the ones that match.

### Why this matters now — THE KEY DIFFERENCE

With the seed KB:
```
Query: "Does a company with strong LTV-CAC ratio and positive
        contribution margin have viable unit economics?"

Available predicates: positive_unit_economics, value_creation, ...
(no ltv_exceeds_cac, no positive_contribution_margin)

LLM output: ["positive_unit_economics(acme)"]
  → Collapsed everything into one coarse predicate
  → Lost all the specificity of the question
  → The user asked about LTV-CAC and contribution margin
     specifically, but the engine can't represent those concepts
```

With the augmented KB:
```
Query: same

Available predicates: ..., ltv_exceeds_cac, positive_contribution_margin, ...

LLM output: ["ltv_exceeds_cac(acme)",
             "positive_contribution_margin(acme)"]
  → Mapped directly to the specific concepts the user asked about
  → V12 will fire and DERIVE positive_unit_economics
  → The engine can now reason about sub-components
```

This is the payoff of the entire extraction pipeline. The user's question can now be represented precisely.

### How
```
DSPy ChainOfThought(GroundQuery):

  Input:
    query:           "Does a company with strong LTV-CAC ratio and
                      positive contribution margin have viable
                      unit economics?"
    ontology_snippet: (50 predicates, 25 rules)
    domain_type:     "CRAFT"

  Output:
    predicates:       ["ltv_exceeds_cac(acme)",
                       "positive_contribution_margin(acme)"]
    relevant_vyaptis: ["V12", "V01"]

Packaged as query facts:
  [
    {predicate: "ltv_exceeds_cac(acme)",
     confidence: 0.7, sources: ["lightweight_grounding"]},
    {predicate: "positive_contribution_margin(acme)",
     confidence: 0.7, sources: ["lightweight_grounding"]}
  ]
```

**Source:** `grounding.py:46-66`, `engine_service.py:240-291`

---

## Stage 4: T2 Compilation — Build the Argumentation Framework

### What
Take the rules + query facts and construct the argumentation framework. Forward-chain through applicable vyaptis, then derive attacks.

### Why this matters now — DEEPER INFERENCE CHAINS

With the seed KB, the user asserted `positive_unit_economics` directly and the engine fired one rule (V01) to derive `value_creation`. Shallow reasoning: one step.

With the augmented KB, the user asserts the *sub-components* (`ltv_exceeds_cac`, `positive_contribution_margin`) and the engine fires V12 to *derive* `positive_unit_economics`, then fires V01 to derive `value_creation`. Deep reasoning: two steps.

The difference is huge. Now the engine can explain *why* positive unit economics holds — because LTV exceeds CAC AND contribution margin is positive. Before, it just asserted it.

### How

```
STEP 4a: Create Premise Arguments

  A0000: ltv_exceeds_cac(acme)
    Type: premise
    Tag: belief=0.70, pramana=PRATYAKSA (direct evidence)
    Strength: 0.70

  A0001: positive_contribution_margin(acme)
    Type: premise
    Tag: belief=0.70, pramana=PRATYAKSA
    Strength: 0.70


STEP 4b: Forward-Chain Through Rules

  Check V12: ltv_exceeds_cac + positive_contribution_margin
             → positive_unit_economics
    ltv_exceeds_cac available? YES (A0000) ✓
    positive_contribution_margin available? YES (A0001) ✓
    → Fire rule → Create argument:

  A0002: positive_unit_economics(acme)
    Via: V12 ("LTV-CAC Viability Test")
    Sub-arguments: (A0000, A0001)
    Tag: tensor(V12_rule_tag, tensor(A0000_tag, A0001_tag))

      V12 rule tag: belief=0.60, pramana=ANUMANA, trust=0.68
      (0.60 because V12 is hypothesis with conf 0.85×0.80=0.68,
       and epistemic_status=hypothesis maps to belief=0.60)

      Combined via semiring ⊗ (tensor):
        belief = 0.60 × 0.70 × 0.70 = 0.294
        pramana = min(ANUMANA, PRATYAKSA, PRATYAKSA) = ANUMANA
        sources = {lightweight_grounding, src_hbs_unit_economics}
        derivation_depth = 1

  Check V01: positive_unit_economics → value_creation
    Antecedent available? YES (A0002) ✓
    → Fire rule → Create argument:

  A0003: value_creation(acme)
    Via: V01 ("The Value Equation")
    Sub-arguments: (A0002)
    Tag: tensor(V01_rule_tag, A0002_tag)

      V01 rule tag: belief=0.95, pramana=ANUMANA, trust=0.855
      Combined: belief = 0.95 × 0.294 = 0.279
      derivation_depth = 2

  Other rules checked:
    V08: needs resource_allocation → SKIP
    V04: needs organizational_growth → SKIP
    ...


STEP 4c: Derive Attacks

  REBUTTING: No not_value_creation or not_positive_unit_economics → none
  UNDERCUTTING: No scope exclusions triggered → none
  UNDERMINING: All decay factors = 1.0 → none

  (But if the user ALSO asserted maturity_mismatch(acme):
    V14 fires → negative_unit_economics(acme)
    negative_unit_economics REBUTS positive_unit_economics → viruddha!
    This conflict was INVISIBLE with the seed KB.)


RESULT:
  4 arguments, 0 attacks
  (Was 3 arguments with seed KB — deeper chain now)
```

**The belief attenuation is important.** Notice how confidence *drops* through the chain:
- Base facts: belief = 0.70 (directly asserted)
- After V12: belief = 0.294 (attenuated through one rule)
- After V01: belief = 0.279 (attenuated through two rules)

This is the provenance semiring doing its job. A conclusion derived through a chain of uncertain rules *should* be less certain than the starting facts. The tensor operation (⊗) ensures this mathematically — it multiplies beliefs, never inflates them. The engine is being honest: "I can derive this, but each step adds uncertainty."

**Source:** `t2_compiler_v4.py:92-307`

---

## Stage 5: Grounded Semantics — The Judge Decides

### What
Same algorithm as before — label each argument IN, OUT, or UNDECIDED. No attacks exist in this query, so everything is IN.

### How
```
Grounded semantics (vada mode):
  A0000: ltv_exceeds_cac(acme) — no attackers → IN
  A0001: positive_contribution_margin(acme) — no attackers → IN
  A0002: positive_unit_economics(acme) — no attackers → IN
  A0003: value_creation(acme) — no attackers → IN
  Fixpoint reached.

Result: {A0000: IN, A0001: IN, A0002: IN, A0003: IN}
Extension size: 4 (was 2 with seed KB — more conclusions reached)
```

**Source:** `argumentation.py:53-109`, `contestation.py:45-81`

---

## Stage 6: Epistemic Status — How Confident Are We?

### What
Classify confidence for each conclusion. This is where the enriched KB produces **different and more honest** results.

### Why this is different now
With the seed KB, `positive_unit_economics` was a base fact with belief=0.70 → PROVISIONAL. Decent confidence.

With the augmented KB, `positive_unit_economics` is a *derived* conclusion with belief=0.294 → OPEN. Lower confidence. Because it was derived through a chain (V12), and the chain attenuated the belief.

This is *more accurate*. The user didn't directly assert "this company has positive unit economics" — they said it has strong LTV-CAC and positive contribution margin. The engine correctly reflects that deriving positive unit economics from sub-components is *less certain* than directly observing it.

### How
```
ltv_exceeds_cac(acme):
  Argument A0000: belief=0.70, uncertainty=0.30
  belief > 0.5, uncertainty ≥ 0.3 → PROVISIONAL
  (Same as before — base fact with lightweight grounding confidence)

positive_contribution_margin(acme):
  Argument A0001: belief=0.70, uncertainty=0.30
  → PROVISIONAL

positive_unit_economics(acme):
  Argument A0002: belief=0.294, uncertainty=0.706
  belief < 0.5 → doesn't meet HYPOTHESIS or PROVISIONAL
  uncertainty > 0.6 → OPEN
  (With seed KB this was PROVISIONAL at belief=0.70!)

  WHY THE CHANGE:
    Before: user asserted positive_unit_economics directly → belief=0.70
    After:  engine DERIVED it through V12 → belief=0.294
    The derivation chain honestly reduced confidence.

value_creation(acme):
  Argument A0003: belief=0.279, uncertainty=0.721
  → OPEN (two-rule chain — even more attenuated)
```

**Source:** `schema_v4.py:154-169`, `argumentation.py:154-196`

---

## Stage 7: Provenance — Where Did This Come From?

### What
Extract the audit trail. Now the provenance chains are richer because they flow through more rules.

### How
```
ltv_exceeds_cac(acme):
  sources:          ["lightweight_grounding"]
  pramana:          PRATYAKSA (direct evidence — strongest type)
  derivation_depth: 0 (base fact)
  trust:            1.0
  decay:            1.0

positive_unit_economics(acme):
  sources:          ["lightweight_grounding", "src_hbs_unit_economics"]
  pramana:          ANUMANA (inference — weaker than direct evidence)
  derivation_depth: 1 (one inference step through V12)
  trust:            0.68 (V12's confidence: 0.85×0.80)
  decay:            1.0

  BEFORE (seed KB):
    sources: ["lightweight_grounding"]
    pramana: PRATYAKSA (it was a base fact!)
    derivation_depth: 0
    → Made it look like direct evidence when it wasn't

  AFTER (augmented KB):
    pramana correctly shows ANUMANA (inference, not observation)
    derivation_depth correctly shows 1 (derived, not base)
    trust correctly reflects V12's confidence
    → Honest about the derivation chain

value_creation(acme):
  sources:          ["lightweight_grounding", "src_hbs_unit_economics",
                     "src_ries_2011"]
  pramana:          ANUMANA
  derivation_depth: 2 (two inference steps: V12 → V01)
  trust:            0.58 (compounded: 0.68 × 0.855)
  decay:            1.0
```

**Source:** `engine_v4.py:172-184`

---

## Stage 8: Uncertainty Decomposition — Three Kinds of "Not Sure"

### What
Break uncertainty into three components. Same algorithm, but now the inputs reflect the deeper inference chains.

### How
```
positive_unit_economics(acme):

  Epistemic:
    belief: 0.294, uncertainty: 0.706
    → "insufficient evidence"
    (Was "moderate evidence" with seed KB when belief=0.70)
    WHY: The derivation chain reduced belief. The engine is saying
         "I can derive this, but I'm not very confident."

  Aleatoric:
    disbelief: 0.0
    → "low domain-level contestation"
    (No one is arguing against it — there's just not enough evidence)

  Inference:
    grounding_confidence: 0.70
    decay_factor: 1.0
    derivation_depth: 1            ← was 0 with seed KB
    → "grounding=0.70, freshness=1.00, chain_depth=1"
    The chain_depth=1 tells users: "this conclusion was derived
    through one inference step, which adds uncertainty."

  Total confidence: 0.200 (was 0.70 with seed KB!)

WHAT THIS MEANS FOR THE USER:
  Before: "positive unit economics is provisional" (sounds OK)
  After:  "positive unit economics is an open question with
           confidence 0.20" (honest about derivation uncertainty)

  The user should respond: "I need to provide more direct evidence
  for positive unit economics, or verify that V12's antecedents
  (LTV-CAC and contribution margin) are strongly established."
```

**Source:** `uncertainty.py:7-57`

---

## Stage 9: Fallacy Detection

### What
Same as before — scan for defeated arguments. No attacks in this query.

### What's different with the enriched KB
More *potential* conflicts are now detectable. With the seed KB, the only conflict was V01 vs V11 (value_creation vs not_value_creation). With the augmented KB:

```
NEW conflicts the enriched KB can detect:

1. V12 vs V14:
   If user asserts ltv_exceeds_cac + positive_contribution_margin
   AND maturity_mismatch:
     V12 derives → positive_unit_economics
     V14 derives → negative_unit_economics
     → VIRUDDHA (contradiction) at the sub-component level!
   This was INVISIBLE with the seed KB.

2. economies_of_scale_real vs imagined_economies_of_scale:
   These are explicitly contradictory predicates. If both are
   asserted, the engine detects the conflict.

3. cohort_ltv_declining → suggests maturity_mismatch
   → which triggers V14 → negative_unit_economics
   → which rebuts positive_unit_economics from V12
   A three-step chain of conflict — impossible to detect with
   only the coarse seed KB predicates.
```

**Source:** `engine_v4.py:192-204`

---

## Stage 10: LLM Synthesis — Write the Final Answer

### What
Feed all structured results to the LLM for a calibrated natural language response.

### Why this is better now
The LLM has **more to work with**. Instead of "value_creation is provisional" and "positive_unit_economics is provisional" (two vague items), the LLM now sees:

```
BEFORE (seed KB inputs to synthesis):
  accepted_arguments:
    "- positive_unit_economics(acme): provisional (belief=0.70)
     - value_creation(acme): provisional (belief=0.70)"

  → LLM output: "Positive unit economics is provisionally
     associated with value creation."
  (Vague, no sub-component reasoning)


AFTER (augmented KB inputs to synthesis):
  accepted_arguments:
    "- ltv_exceeds_cac(acme): provisional (belief=0.70)
     - positive_contribution_margin(acme): provisional (belief=0.70)
     - positive_unit_economics(acme): open (belief=0.294)
     - value_creation(acme): open (belief=0.279)"

  → LLM output: "Based on the evidence, when a company demonstrates
     both an LTV-CAC ratio above breakeven and positive contribution
     margin, there is provisional support for these individual
     conditions. However, the derived conclusion of viable unit
     economics carries open epistemic status (confidence 0.20)
     because it depends on a multi-step inference chain. Additional
     evidence — such as payback period data — would strengthen
     this conclusion."
  (Specific, explains sub-components, honest about derivation,
   suggests what evidence would help)
```

The enriched KB enables the synthesis to be specific about *which* sub-components are supported and *which* are derived. It can also suggest what additional evidence would help — because it knows what other predicates exist (like `payback_within_runway`) that could strengthen the case.

### How
Same mechanism: `dspy.Refine(N=3, reward_fn=_synthesis_reward, threshold=0.5)`. The reward function is unchanged — it still checks for hedging language, source citations, no overconfidence, and hetvabhasa warnings.

**Source:** `engine_v4.py:16-74`

---

## Stage 11: Response Assembly

### What
Package everything into the final JSON response.

### How
```json
{
  "query_text": "Does a company with strong LTV-CAC ratio and
                 positive contribution margin have viable
                 unit economics?",
  "status": "completed",

  "response": "Based on the evidence, when a company demonstrates
    both an LTV-CAC ratio above breakeven and positive contribution
    margin, there is provisional support for these individual
    conditions. However, the derived conclusion of viable unit
    economics carries open epistemic status (confidence 0.20)
    because it depends on a multi-step inference chain...",

  "sources": ["lightweight_grounding", "src_hbs_unit_economics"],

  "uncertainty": {
    "ltv_exceeds_cac(acme)":              {"total_confidence": 0.70},
    "positive_contribution_margin(acme)": {"total_confidence": 0.70},
    "positive_unit_economics(acme)":      {"total_confidence": 0.20},
    "value_creation(acme)":               {"total_confidence": 0.19}
  },

  "provenance": {
    "positive_unit_economics(acme)": {
      "sources": ["lightweight_grounding", "src_hbs_unit_economics"],
      "pramana": "ANUMANA",
      "derivation_depth": 1,
      "trust": 0.68
    },
    "value_creation(acme)": {
      "sources": ["lightweight_grounding", "src_hbs_unit_economics",
                   "src_ries_2011"],
      "pramana": "ANUMANA",
      "derivation_depth": 2,
      "trust": 0.58
    }
  },

  "violations": [],
  "grounding_confidence": 0.7,
  "extension_size": 4,
  "contestation": {"mode": "vada", "open_questions": []}
}
```

**Source:** `routers/queries.py:73-86`

---

# PART 3: THE COMPLETE PICTURE

## Summary — Offline Pipeline

```
  GUIDE TEXT (Chapter 2: Unit Economics, 6 sections)
  + SEED KB (11 vyaptis, 23 predicates)
     │
     │  Stage A:  Read sections, extract candidates         (~6 LLM calls)
     │  Stage B:  Decompose existing rules into sub-parts   (~11 LLM calls)
     │  Stage C:  Merge synonyms via embeddings             (0-1 LLM calls)
     │  Stage D:  Build new rules from relationships        (~15 LLM calls)
     │  Stage E:  Validate: cycles, types, Datalog, ≤       (0 LLM calls)
     │  Stage F:  Human expert reviews each rule            (0 LLM calls)
     │
     ▼
  AUGMENTED KB (~25 vyaptis, ~50 predicates)
  All new rules conservative: epistemic_status=hypothesis, confidence≤0.85
  All Pydantic-validated, Datalog-compilable, DAG-acyclic
  Total: ~30-35 LLM calls per chapter, ~5-10 minutes
```

## Summary — Online Pipeline

```
  QUERY: "Does a company with strong LTV-CAC ratio and positive
          contribution margin have viable unit economics?"
     │
     │  Stage 0:  Accept request, pick path                 (0 LLM calls)
     │  Stage 1:  Load augmented KB (50 predicates)         (0 LLM calls)
     │  Stage 2:  Build vocabulary (50 predicates for LLM)  (0 LLM calls)
     │  Stage 3:  LLM translates English → predicates       (1 LLM call)
     │            → ltv_exceeds_cac, positive_contribution_margin
     │  Stage 4:  Build arguments, fire V12→V01, attacks    (0 LLM calls)
     │            → 4 arguments (deeper chain than before)
     │  Stage 5:  Judge: all IN (no conflicts)              (0 LLM calls)
     │  Stage 6:  Epistemic: sub-components PROVISIONAL,    (0 LLM calls)
     │            derived conclusions OPEN (honest!)
     │  Stage 7:  Provenance: ANUMANA, depth=1-2, trust<1   (0 LLM calls)
     │  Stage 8:  Uncertainty: chain_depth reveals WHY       (0 LLM calls)
     │  Stage 9:  Violations: none (but more detectable)    (0 LLM calls)
     │  Stage 10: LLM writes response with sub-components   (1 LLM call)
     │  Stage 11: Save and return JSON                      (0 LLM calls)
     │
     ▼
  TOTAL: 2 LLM calls. 10 of 12 stages are pure symbolic computation.
  Duration: ~3.8 seconds.
  But now with sub-component reasoning, deeper provenance, and
  more honest epistemic status.
```

## The Key Insight

The predicate extraction pipeline doesn't change **how** the query engine works. It changes **what** the query engine works *with*.

Same algorithm. Same LLM calls. Same 3.8 seconds. But the reasoning is qualitatively different:

| Dimension | Before (seed KB) | After (augmented KB) |
|-----------|-------------------|----------------------|
| **Vocabulary** | 23 predicates (chapter-level) | ~50 predicates (section-level) |
| **Rules** | 11 vyaptis | ~25 vyaptis |
| **Grounding precision** | "LTV-CAC" → `positive_unit_economics` (lossy) | "LTV-CAC" → `ltv_exceeds_cac` (precise) |
| **Inference depth** | 1 rule max | 2-3 rules chained |
| **Epistemic honesty** | Derived conclusions look like base facts | Derived conclusions correctly attenuated |
| **Conflict detection** | Only chapter-level conflicts | Section-level conflicts too |
| **Synthesis quality** | Vague: "provisional support" | Specific: names sub-components, suggests evidence |
| **Provenance** | 1 source, depth=0 | Multiple sources, depth=1-2, trust < 1.0 |

The LLM is still just a translator and writer. All reasoning is still symbolic. But the symbolic engine now has a much richer vocabulary to reason with — and it uses that vocabulary to produce more precise, more traceable, more epistemically honest conclusions.

---

## Appendix: Mapping to the Thesis

> How each pipeline stage maps to claims in `thesis2_v1.md` — *The Ānvīkṣikī Engine (v4):
> From Nyāya Epistemology to Neurosymbolic Argumentation*.

---

### Stages A-D → §2.4 Compilation Targets + Ontology Learning Layer Cake

**Thesis claim (§2.4, lines 196-200):** "T2 (Logic Engine): Executable inference over formalized domain rules — *this is what this thesis redesigns*."

**Implementation:** The predicate extraction pipeline is the **automated T2 authoring** complement. The thesis designs the engine; the pipeline feeds it. The seed KB had manually-authored T2 rules. The pipeline reads the T1 output (guide text) and automatically generates additional T2 rules.

This follows the **Ontology Learning Layer Cake** (Buitelaar, Cimiano & Magnini 2005): term extraction (Stage A) → concept formation (Stage B) → taxonomy (Stage C dedup) → relation extraction (Stage D).

---

### Stage A → §6.3 Five-Layer Grounding Defense (adapted for extraction)

**Thesis (§6.3, Strategy 4):** "Ontology-constrained prompting: The LLM sees ONLY valid predicates."

**Implementation:** Stage A inverts this. Instead of constraining the LLM to existing predicates, it uses existing predicates as *seed context* and asks the LLM to propose *new* ones. The seed ontology prevents drift — extracted predicates must relate to existing ones (the `related_existing_vyapti` field).

---

### Stage B → §7.3 Provenance Semiring Tensor Operation

**Thesis (§7.3, lines 770-777):** "⊗ (tensor): sequential composition. When facts chain through rules, the result attenuates."

**Implementation:** Stage B's decomposition directly enables deeper tensor chains. Before: `positive_unit_economics ⊗ V01_tag → value_creation` (1 tensor). After: `ltv_exceeds_cac ⊗ positive_contribution_margin ⊗ V12_tag → positive_unit_economics ⊗ V01_tag → value_creation` (2 tensors). The attenuation is stronger — and more honest.

---

### Stage E → §3.5 Datalog Decidability + §7.4 What Becomes Unnecessary

**Thesis (§3.5, line 321):** "Datalog evaluation is polynomial in the size of the EDB."

**Implementation:** Stage E's DAG cycle check + Datalog test-compilation ensures the augmented KB maintains this guarantee. New vyaptis cannot introduce cycles (which would break stratifiability) or non-terminating evaluation patterns. This is Invariant I2 from the theory paper: *DAG acyclicity ⟹ stratifiability ⟹ unique minimal model* (Apt, Blair & Walker 1988).

**Thesis (§7.4, line 795):** "Keyword hetvabhasa detection ELIMINATED."

**Implementation:** Stage E validates that new vyaptis produce structural attacks (via scope_exclusions and contradictory consequents), not keyword-based detection. The pipeline generates rules that participate in the ASPIC+ defeat relation — it doesn't create ad-hoc fallacy detectors.

---

### Stage F → §8.4-8.5 Contestable AI (Leofante et al., KR 2024)

**Thesis (§8.4, lines 881-906):** Four requirements for contestable AI: Explanations, Grounds, Interaction, Redress.

**Implementation:** Stage F is the *authoring-time* counterpart to *query-time* contestation. At query time, users contest engine conclusions via jalpa/vitanda. At authoring time, domain experts contest proposed vyaptis via the HITL review. Both embody the same principle: formal structures that humans can challenge.

---

### Query Pipeline Stages 0-11 → Same thesis mapping as original ELI5 trace

The query pipeline stages map identically to the original ELI5 trace appendix (see `docs/eli5_trace.md`). The only difference is that the augmented KB produces:
- **Deeper inference chains** (Stage 4) → more tensor operations → more honest attenuation
- **More precise grounding** (Stage 3) → sub-component predicates → richer vocabulary
- **More detectable conflicts** (Stage 9) → section-level contradictions visible
- **More informative synthesis** (Stage 10) → sub-components named, evidence gaps identified

The architecture is unchanged. The *content* flowing through it is richer.
