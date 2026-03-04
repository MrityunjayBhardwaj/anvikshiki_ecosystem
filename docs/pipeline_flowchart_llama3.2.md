# Ānvīkṣikī Engine — Pipeline Flowchart (Llama-3.2-3B-Instruct-4bit)

> Detailed trace of every stage: inputs, processing, outputs, and rationale.
> Based on real test run against `business_expert.yaml` knowledge base.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLIENT REQUEST                                  │
│  POST /api/queries/                                                     │
│  {kb_id, query, contestation_mode, retrieved_chunks, ?query_facts}      │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    ROUTE SELECTION (queries.py)                          │
│                                                                         │
│   query_facts provided? ──YES──▶ Path A: execute_symbolic               │
│         │ NO                         (LLM: synthesis only — 1 call)      │
│         ▼                                                               │
│   is_small_model? ────YES──▶ Path B: execute_lightweight_grounding      │
│         │ NO                     (LLM: 1 grounding + 1 synthesis)       │
│         ▼                                                               │
│   Path C: execute_query                                                 │
│       (LLM: N=5 grounding + round-trip + synthesis)                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Path B: Lightweight Grounding (Llama-3.2-3B + `is_small_model=true`)

This is the primary path for local LLMs. Tested and verified working.

### Test Parameters Used

```
Model:              mlx-community/Llama-3.2-3B-Instruct-4bit
MLX Server:         localhost:8080, --chat-template-args '{"enable_thinking":false}'
KB:                 business_expert.yaml (11 vyāptis, 8 hetvābhāsas, domain=CRAFT)
Query:              "Does a company with positive unit economics always create value?"
Contestation Mode:  vada (cooperative inquiry — grounded semantics, polynomial)
Retrieved Chunks:   2 prose passages
Total Duration:     3,803 ms
LLM Calls:          2 (1 grounding + 1 synthesis)
```

---

### STAGE 0: Request Ingestion & LLM Configuration

**What:** Accept the HTTP request, authenticate user, configure DSPy to use their LLM, determine execution path.

**Why:** Each user can configure their own LLM provider. The `is_small_model` flag determines whether to use the full N=5 ensemble (expensive, requires capable model) or the lightweight single-call grounding.

**Processing:** Pure Python — no LLM calls.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ HTTP POST /api/queries/                                          │
│ Headers:  Authorization: Bearer <JWT>                            │
│ Body:                                                            │
│   kb_id:              "3aab9fef-de49-435f-9617-dce78c764490"     │
│   query:              "Does a company with positive unit         │
│                        economics always create value?"           │
│   contestation_mode:  "vada"                                     │
│   retrieved_chunks:   [                                          │
│     "A company with positive unit economics demonstrates         │
│      value creation through sustainable margins.",               │
│     "However, organizational growth can lead to coordination     │
│      overhead and distorted market signals."                     │
│   ]                                                              │
│   query_facts:        null (not provided → triggers grounding)   │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Processing ▼

1. JWT decoded → user_id = "a6e48ab7-..."
2. User's llm_config loaded from DB:
   {
     "provider": "openai/mlx-community/Llama-3.2-3B-Instruct-4bit",
     "api_key": "no-key",
     "api_base": "http://localhost:8080/v1",
     "is_small_model": true,
     "max_tokens": 4096
   }
3. dspy.LM() instantiated with these params
4. dspy.configure(lm=lm) sets global LM for this request
5. KB record fetched → yaml_path = "kb_store/<user_id>/<kb_id>.yaml"
6. QueryRecord created in DB with status="processing"

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ Route Decision:  is_small_model=true, no query_facts             │
│                  → execute_lightweight_grounding()                │
│ DB Record:       query_id="1ac4dd7b-...", status="processing"    │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `routers/queries.py:111-169`, `services/engine_service.py:23-34`

---

### STAGE 1: Knowledge Store Loading

**What:** Parse the YAML knowledge base into a structured `KnowledgeStore` object. Cached per `kb_id`.

**Why:** The KB defines the domain's valid predicates, inference rules (vyāptis), scope conditions, and source references. Everything downstream depends on this structured representation.

**Processing:** YAML parsing + Pydantic validation. No LLM.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ yaml_path: "kb_store/<user_id>/3aab9fef-....yaml"                │
│ (Contents: business_expert.yaml — 506 lines)                     │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Processing ▼

yaml.safe_load(file) → KnowledgeStore(**data)
Cached in engine_service._knowledge_stores[kb_id]

┌─ OUTPUT: KnowledgeStore ─────────────────────────────────────────┐
│ domain_type: CRAFT                                               │
│ pramanas:    [pratyaksa, anumana, sabda, upamana]                │
│                                                                  │
│ vyaptis (11 rules):                                              │
│   V01: positive_unit_economics → value_creation                  │
│         (empirical, established, conf=0.95×0.9)                  │
│   V04: organizational_growth → coordination_overhead             │
│         (empirical, established, conf=0.85×0.75)                 │
│   V05: coordination_overhead → distorted_market_signal           │
│   V08: value_creation + resource_allocation → long_term_value    │
│   V11: organizational_growth + coordination_overhead             │
│         → not_value_creation (HYPOTHESIS, conf=0.7×0.65)         │
│         ▲ This creates a REBUTTING CONFLICT with V01             │
│   ... (V02, V03, V06, V07, V09, V10)                            │
│                                                                  │
│ hetvabhasas: H01-H08 (fallacy detection patterns)                │
│ reference_bank: 22 academic sources                              │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `t2_compiler_v4.py:310-315`, `schema.py`

---

### STAGE 2: Ontology Snippet Construction (Layer 1 of Grounding)

**What:** Build a constrained vocabulary prompt from the KB's vyāptis. The LLM will ONLY see valid predicate names, rules, and scope conditions.

**Why:** This is the cheapest defense against hallucinated predicates. By enumerating every valid predicate, the LLM can only select from known vocabulary. Zero LLM calls — pure string construction.

**Processing:** String concatenation from KnowledgeStore. No LLM.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ KnowledgeStore (from Stage 1)                                    │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Processing ▼

OntologySnippetBuilder().build(ks)
Iterates all 11 vyāptis, extracts antecedents + consequents

┌─ OUTPUT: ontology_snippet (string) ──────────────────────────────┐
│ VALID PREDICATES — use ONLY these:                               │
│                                                                  │
│ RULE V01: The Value Equation                                     │
│   IF: positive_unit_economics                                    │
│   THEN: value_creation                                           │
│   SCOPE: commercial_enterprise                                   │
│   EXCLUDES: subsidized_entity, network_effect_building_phase     │
│                                                                  │
│ RULE V02: The Constraint Cascade                                 │
│   IF: binding_constraint_identified                              │
│   THEN: resource_allocation_effective                            │
│   SCOPE: serial_dependency_system                                │
│   EXCLUDES: highly_parallel_system                               │
│                                                                  │
│ RULE V04: The Organizational Entropy Principle                   │
│   IF: organizational_growth                                      │
│   THEN: coordination_overhead                                    │
│   SCOPE: (none)                                                  │
│   EXCLUDES: active_structural_intervention                       │
│                                                                  │
│ RULE V11: The Growth Trap                                        │
│   IF: organizational_growth, coordination_overhead               │
│   THEN: not_value_creation                                       │
│   SCOPE: (none)                                                  │
│   EXCLUDES: active_structural_intervention, small_team...        │
│                                                                  │
│ ... (V03, V05, V06, V07, V08, V09, V10)                         │
│                                                                  │
│ ALL VALID PREDICATE NAMES:                                       │
│   - binding_constraint_identified(Entity)                        │
│   - calibration_accuracy(Entity)                                 │
│   - capability_gain(Entity)                                      │
│   - coordination_overhead(Entity)                                │
│   - decision_quality(Entity)                                     │
│   - disruption_vulnerability(Entity)                             │
│   - distorted_market_signal(Entity)                              │
│   - incentive_alignment(Entity)                                  │
│   - incumbent_rational_allocation(Entity)                        │
│   - long_term_value(Entity)                                      │
│   - low_margin_market_entrant(Entity)                            │
│   - not_value_creation(Entity)                                   │
│   - organizational_effectiveness(Entity)                         │
│   - organizational_growth(Entity)                                │
│   - positive_unit_economics(Entity)                              │
│   - pricing_power(Entity)                                        │
│   - resource_allocation_effective(Entity)                        │
│   - strategic_commitment(Entity)                                 │
│   - superior_information(Entity)                                 │
│   - value_creation(Entity)                                       │
│                                                                  │
│ OUTPUT FORMAT:                                                   │
│ Return predicates as: predicate_name(entity)                     │
│ Entity names should be lowercase with underscores.               │
│ Use ONLY predicate names from the list above.                    │
│ Include negation as: not_predicate_name(entity)                  │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `grounding.py:98-143`

---

### STAGE 3: LLM Grounding Call (1 call — Lightweight Path)

**What:** Send the query + ontology snippet to Llama-3.2-3B via DSPy's `ChainOfThought(GroundQuery)`. The model extracts structured predicates from the natural language query.

**Why:** This is the bridge between natural language and the symbolic engine. The symbolic engine only understands predicates like `positive_unit_economics(acme)` — it can't process "Does a company with positive unit economics always create value?" directly. The LLM's job is to identify which predicates from the constrained vocabulary match the query's entities and relationships.

**Why Lightweight (1 call instead of 5):** The full pipeline uses N=5 ensemble consensus to filter hallucinations. But small models (3B params) are too inconsistent across runs for ensemble consensus to work — they produce different predicates each time, leading to empty consensus sets. A single call with Chain-of-Thought reasoning works better: the model reasons step-by-step, then outputs predicates.

**Processing:** 1 LLM call via DSPy → MLX server → Llama-3.2-3B.

```
┌─ INPUT TO DSPy ──────────────────────────────────────────────────┐
│ Signature: GroundQuery (dspy.Signature)                          │
│                                                                  │
│ Input Fields:                                                    │
│   query:            "Does a company with positive unit economics │
│                      always create value?"                       │
│   ontology_snippet:  (full snippet from Stage 2, ~60 lines)     │
│   domain_type:       "CRAFT"                                     │
│                                                                  │
│ Expected Output Fields:                                          │
│   reasoning:         str  (step-by-step analysis)                │
│   predicates:        list[str]  (structured predicates)          │
│   relevant_vyaptis:  list[str]  (rule IDs)                       │
└──────────────────────────────────────────────────────────────────┘

                    ▼ DSPy constructs prompt ▼

DSPy's ChainOfThought wraps GroundQuery into a prompt like:

┌─ ACTUAL PROMPT SENT TO LLM ─────────────────────────────────────┐
│ Translate a natural language query into structured predicates.   │
│ Use ONLY predicates from the provided ontology snippet.          │
│ Think step by step about which entities and relationships the    │
│ query mentions.                                                  │
│                                                                  │
│ ---                                                              │
│                                                                  │
│ Follow the following format.                                     │
│                                                                  │
│ Query: User's natural language question                          │
│ Ontology Snippet: Valid predicates and rules — use ONLY these    │
│ Domain Type: Domain classification                               │
│                                                                  │
│ Reasoning: Let's think step by step. Step-by-step: which         │
│   predicates match the entities and relationships?               │
│ Predicates: Structured predicates, e.g.                          │
│   ['concentrated_ownership(acme)', 'private_firm(acme)']         │
│ Relevant Vyaptis: IDs of vyāptis relevant to this query         │
│                                                                  │
│ ---                                                              │
│                                                                  │
│ Query: Does a company with positive unit economics always        │
│        create value?                                             │
│ Ontology Snippet: VALID PREDICATES — use ONLY these: ...         │
│   (full snippet)                                                 │
│ Domain Type: CRAFT                                               │
│                                                                  │
│ Reasoning: Let's think step by step.                             │
└──────────────────────────────────────────────────────────────────┘

                    ▼ LLM generates ▼

HTTP POST http://localhost:8080/v1/chat/completions
{
  "model": "mlx-community/Llama-3.2-3B-Instruct-4bit",
  "messages": [{"role": "user", "content": "<prompt above>"}],
  "max_tokens": 4096
}

                    ▼ DSPy parses response ▼

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ grounding.reasoning:        (step-by-step analysis text)         │
│ grounding.predicates:       [                                    │
│     "positive_unit_economics(acme)",                             │
│     "value_creation(acme)"                                       │
│ ]                                                                │
│ grounding.relevant_vyaptis: ["V01"]                              │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Convert to query_facts ▼

┌─ QUERY FACTS (for symbolic pipeline) ────────────────────────────┐
│ [                                                                │
│   {                                                              │
│     "predicate": "positive_unit_economics(acme)",                │
│     "confidence": 0.7,       ← fixed at 0.7 for lightweight     │
│     "sources": ["lightweight_grounding"]                         │
│   },                                                             │
│   {                                                              │
│     "predicate": "value_creation(acme)",                         │
│     "confidence": 0.7,                                           │
│     "sources": ["lightweight_grounding"]                         │
│   }                                                              │
│ ]                                                                │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `engine_service.py:240-291`, `grounding.py:46-66`

---

### STAGE 4: Build Argumentation Framework (T2 Compiler)

**What:** Compile the knowledge base rules + query facts into an ASPIC+ argumentation framework. Forward-chain through all applicable vyāptis, then derive all attacks between arguments.

**Why:** This is where the symbolic reasoning happens. The argumentation framework captures not just what follows from the evidence, but also what conflicts exist, what attacks what, and why. This is fundamentally different from an LLM just "reasoning" — it's provably correct formal logic with explicit conflict resolution.

**Processing:** Pure computation — no LLM. Three sub-steps iterated to fixpoint.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ KnowledgeStore (11 vyāptis with full metadata)                   │
│ query_facts: [                                                   │
│   {predicate: "positive_unit_economics(acme)", conf: 0.7},       │
│   {predicate: "value_creation(acme)", conf: 0.7}                 │
│ ]                                                                │
└──────────────────────────────────────────────────────────────────┘

         ▼ Step 4a: Create Premise Arguments ▼

For each query fact, create a premise argument:

  A0000: positive_unit_economics(acme)
    top_rule: None (premise)
    tag: Tag(b=0.70, d=0.00, u=0.30, pramana=PRATYAKSA,
            trust=1.0, decay=1.0, depth=0)
    sources: {lightweight_grounding}

  A0001: value_creation(acme)
    top_rule: None (premise)
    tag: Tag(b=0.70, d=0.00, u=0.30, pramana=PRATYAKSA,
            trust=1.0, decay=1.0, depth=0)
    sources: {lightweight_grounding}

         ▼ Step 4b: Forward-Chain Rule Arguments ▼

Check every vyāpti: are ALL antecedents available?

  V01: positive_unit_economics → value_creation
    antecedents: [positive_unit_economics] ✓ (A0000 provides it)
    → Create A0002: value_creation(acme)
      top_rule: V01
      sub_arguments: (A0000,)
      tag: tensor(V01_rule_tag, A0000_tag)
           V01 rule tag: Tag(b=0.95, d=0.00, u=0.05,
                            pramana=ANUMANA, trust=0.855,
                            decay=1.0)
           Combined via semiring ⊗:
             b = 0.95 × 0.70 = 0.665 (attenuated through chain)
             sources = {src_hbs_unit_economics, src_ries_2011,
                        lightweight_grounding}

  V08: value_creation + resource_allocation → long_term_value
    antecedents: [value_creation ✓, resource_allocation ✗]
    → SKIP (not all antecedents available)

  V04, V05, V11: need organizational_growth → not in facts
    → SKIP

  ... (all other rules checked similarly)

         ▼ Step 4c: Derive Attacks ▼

Three attack types checked:

  REBUTTING (viruddha): contradictory conclusions?
    No not_value_creation argument exists → no viruddha attacks

  UNDERCUTTING (savyabhicāra): scope violations?
    V01 excludes: subsidized_entity, network_effect_building_phase
    Neither present in arguments → no undercutting attacks

  UNDERMINING (asiddha): decay-expired premises?
    All decay_factors = 1.0 → no undermining attacks

         ▼ Fixpoint: no new arguments added → STOP ▼

┌─ OUTPUT: ArgumentationFramework ─────────────────────────────────┐
│ arguments: {                                                     │
│   A0000: positive_unit_economics(acme) [premise, b=0.70]         │
│   A0001: value_creation(acme) [premise, b=0.70]                  │
│   A0002: value_creation(acme) [via V01, b=0.665]                 │
│ }                                                                │
│ attacks: []   (no conflicts in this query)                       │
│ Total arguments: 3                                               │
│ Total attacks: 0                                                 │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `t2_compiler_v4.py:92-145` (compile_t2), `t2_compiler_v4.py:148-206` (_derive_rule_arguments), `t2_compiler_v4.py:209-307` (_derive_attacks)

---

### STAGE 5: Contestation — Compute Extension (Vada Mode)

**What:** Apply the selected debate protocol to compute which arguments are accepted (IN), defeated (OUT), or undecided. Vada = cooperative inquiry using grounded semantics.

**Why:** Different debate protocols produce different results:
- **Vada** (grounded semantics): Conservative — only accepts arguments that are unambiguously defended. Polynomial time. Used for routine queries.
- **Jalpa** (preferred semantics): Adversarial — finds all defensible positions even if not grounded. NP-hard. Used for stress-testing claims.
- **Vitanda** (stable semantics): Pure critique — finds all vulnerabilities. coNP-hard. Used for audit/red-teaming.

**Processing:** Graph labeling algorithm (fixpoint iteration). No LLM.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ ArgumentationFramework (from Stage 4)                            │
│ contestation_mode: "vada"                                        │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Processing ▼

ContestationManager.vada(af):
  1. af.compute_grounded() — iterative labeling:
     Iteration 1:
       A0000: no attackers → IN
       A0001: no attackers → IN
       A0002: no attackers → IN
     Fixpoint reached (all labeled).

  2. Collect accepted conclusions:
     positive_unit_economics(acme): status, tag, args
     value_creation(acme): status, tag, args

  3. Identify open questions: (none — all resolved)
  4. Suggest evidence for UNDECIDED args: (none)

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ labels: {A0000: IN, A0001: IN, A0002: IN}                       │
│                                                                  │
│ contestation_analysis: {                                         │
│   "mode": "vada",                                                │
│   "open_questions": [],                                          │
│   "suggested_evidence": []                                       │
│ }                                                                │
│                                                                  │
│ extension_size: 2  (user-facing arguments labeled IN,            │
│                     excluding internal _undercut_* args)          │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `contestation.py:45-81` (vada), `argumentation.py:53-109` (compute_grounded)

---

### STAGE 6: Epistemic Status Derivation

**What:** For each non-internal conclusion, derive its epistemic status from the argumentation labeling + provenance tag values.

**Why:** Raw IN/OUT labels are too coarse. The epistemic status tells the user HOW confident we are and WHY:
- **ESTABLISHED** (belief > 0.8, uncertainty ≤ 0.1): Well-supported, low uncertainty
- **HYPOTHESIS** (belief > 0.5, uncertainty < 0.3): Moderate support, working theory
- **PROVISIONAL** (belief > 0.5, doesn't meet above): Accepted but weakly
- **OPEN** (UNDECIDED in extension): Insufficient evidence either way
- **CONTESTED** (OUT in grounded, IN in preferred): Defensible but challenged

**Processing:** Threshold checks on ProvenanceTag values. No LLM.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ ArgumentationFramework with labels                               │
│ All non-internal conclusions:                                    │
│   positive_unit_economics(acme), value_creation(acme)            │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Processing ▼

For each conclusion, call af.get_epistemic_status(conc):
  Find all arguments for this conclusion
  Pick the strongest (highest tag.strength)
  Derive status from tag thresholds

  positive_unit_economics(acme):
    Best argument: A0000 (premise, b=0.70, u=0.30)
    b=0.70 > 0.5, u=0.30 ≥ 0.3 → doesn't meet HYPOTHESIS
    b=0.70 > 0.5 → PROVISIONAL
    (Note: confidence=0.7 from lightweight grounding is lower
     than the 0.95 from the KB's own rule confidence)

  value_creation(acme):
    Best argument: A0001 (premise, b=0.70, u=0.30) or
                   A0002 (via V01, b=0.665, u=...)
    A0001 stronger (b=0.70 vs 0.665)
    b=0.70 > 0.5, u=0.30 ≥ 0.3 → PROVISIONAL

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ results: {                                                       │
│   "positive_unit_economics(acme)": {                             │
│     "status": PROVISIONAL,                                       │
│     "tag": Tag(b=0.70, d=0.00, u=0.30, ...),                    │
│     "arguments": [A0000]                                         │
│   },                                                             │
│   "value_creation(acme)": {                                      │
│     "status": PROVISIONAL,                                       │
│     "tag": Tag(b=0.70, d=0.00, u=0.30, ...),                    │
│     "arguments": [A0001]                                         │
│   }                                                              │
│ }                                                                │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `schema_v4.py:154-169` (epistemic_status), `argumentation.py` (get_epistemic_status)

---

### STAGE 7: Provenance Extraction

**What:** For each accepted conclusion, extract its full provenance chain: which sources support it, what type of evidence (pramāṇa), how deep the derivation chain is, and how fresh the evidence is.

**Why:** Provenance is the "show your work" of the engine. Users need to know not just WHAT the engine concluded, but WHERE the evidence came from, HOW it was derived, and whether the sources can be trusted. This enables auditability — a user can trace any conclusion back to specific academic sources.

**Processing:** Direct field extraction from ProvenanceTag. No LLM.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ results dict from Stage 6 (each conclusion's tag)                │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Processing ▼

For each conclusion, extract from its tag:
  sources:           sorted(tag.source_ids)
  pramana:           tag.pramana_type.name
  derivation_depth:  tag.derivation_depth
  trust:             tag.trust_score
  decay:             tag.decay_factor

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ provenance: {                                                    │
│   "value_creation(acme)": {                                      │
│     "sources": ["lightweight_grounding"],                        │
│     "pramana": "PRATYAKSA",   ← direct evidence (strongest)     │
│     "derivation_depth": 0,    ← base fact, no inference chain   │
│     "trust": 1.0,             ← full source authority            │
│     "decay": 1.0              ← temporally fresh                 │
│   },                                                             │
│   "positive_unit_economics(acme)": {                             │
│     "sources": ["lightweight_grounding"],                        │
│     "pramana": "PRATYAKSA",                                      │
│     "derivation_depth": 0,                                       │
│     "trust": 1.0,                                                │
│     "decay": 1.0                                                 │
│   }                                                              │
│ }                                                                │
│                                                                  │
│ Pramāṇa hierarchy (strongest → weakest):                        │
│   PRATYAKSA (4) — direct evidence/observation                    │
│   ANUMANA (3)   — logical inference                              │
│   SABDA (2)     — authoritative testimony                        │
│   UPAMANA (1)   — analogy (weakest)                              │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `engine_service.py:175-184` (in execute_symbolic)

---

### STAGE 8: Uncertainty Decomposition

**What:** Decompose each conclusion's uncertainty into three independent dimensions: epistemic (how much we know), aleatoric (inherent domain disagreement), and inference (how confident the grounding + derivation chain is).

**Why:** A single "confidence score" is misleading. A conclusion can be uncertain for completely different reasons:
- **Epistemic uncertainty**: We don't have enough evidence (solvable — get more data)
- **Aleatoric uncertainty**: The domain itself is contested (may be unsolvable)
- **Inference uncertainty**: The grounding from NL→predicates may be wrong, or the derivation chain is long/stale

Separating these helps users decide what to DO about the uncertainty.

**Processing:** Arithmetic on ProvenanceTag fields. No LLM.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ For each conclusion: its ProvenanceTag + grounding_confidence    │
│ grounding_confidence: 0.7 (average of query fact confidences)    │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Processing ▼

compute_uncertainty_v4(tag, grounding_confidence, conclusion, status)

  For positive_unit_economics(acme):
    tag.belief = 0.70, tag.uncertainty = 0.30, tag.disbelief = 0.0

    Epistemic component:
      belief=0.70, uncertainty=0.30
      0.70 > 0.5 → "moderate evidence — working hypothesis"

    Aleatoric component:
      disbelief=0.0
      0.0 ≤ 0.3 → "low domain-level contestation"

    Inference component:
      grounding_confidence=0.70
      decay_factor=1.0 (fresh)
      derivation_depth=0 (base fact)
      → "grounding=0.70, freshness=1.00, chain_depth=0"

    total_confidence = tag.strength
                     = belief × trust × decay
                     = 0.70 × 1.0 × 1.0 = 0.70

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ uncertainty: {                                                   │
│   "positive_unit_economics(acme)": {                             │
│     "conclusion": "positive_unit_economics(acme)",               │
│     "epistemic": {                                               │
│       "status": "provisional",                                   │
│       "belief": 0.7,                                             │
│       "uncertainty": 0.3,                                        │
│       "explanation": "moderate evidence — working hypothesis"    │
│     },                                                           │
│     "aleatoric": {                                               │
│       "disbelief": 0.0,                                          │
│       "explanation": "low domain-level contestation"             │
│     },                                                           │
│     "inference": {                                               │
│       "grounding_confidence": 0.7,                               │
│       "decay_factor": 1.0,                                       │
│       "derivation_depth": 0,                                     │
│       "explanation": "grounding=0.70, freshness=1.00,            │
│                       chain_depth=0"                              │
│     },                                                           │
│     "total_confidence": 0.7                                      │
│   },                                                             │
│   "value_creation(acme)": { ... same structure ... }             │
│ }                                                                │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `uncertainty.py:7-57`

---

### STAGE 9: Violation Detection (Hetvābhāsa Collection)

**What:** Scan the argumentation framework for defeated arguments — arguments that were attacked by an IN-labeled attacker with a successful defeat. Collect the fallacy type (hetvābhāsa) for each violation.

**Why:** Violations are the engine's "red flags." If the KB contains rules that contradict each other, and the evidence triggers both sides, the engine detects this as a formal logical conflict rather than silently ignoring it. Each violation is classified by its Nyāya fallacy type:
- **viruddha** (rebutting): Two arguments reach contradictory conclusions
- **savyabhicāra** (undercutting): A scope condition is violated
- **asiddha** (undermining): A premise's evidence has decayed/expired

**Processing:** Graph traversal of attacks. No LLM.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ ArgumentationFramework with labels (from Stage 5)                │
│ All attacks in af.attacks                                        │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Processing ▼

For each attack in af.attacks:
  If attacker is IN (accepted):
    If target's conclusion is non-internal:
      → Record violation with hetvabhasa type

In this test: af.attacks = [] (no conflicts)
  → violations = []

(With query_facts [positive_unit_economics, organizational_growth],
 V01 fires → value_creation, V04 fires → coordination_overhead,
 V11 fires → not_value_creation.
 not_value_creation REBUTS value_creation → viruddha detected!)

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ violations: []                                                   │
│                                                                  │
│ (In a richer query with organizational_growth, you'd see:)       │
│ violations: [{                                                   │
│   "hetvabhasa": "viruddha",                                      │
│   "type": "rebutting",                                           │
│   "attacker": "A0005",                                           │
│   "target": "A0002",                                             │
│   "target_conclusion": "value_creation(acme)"                    │
│ }]                                                               │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `engine_service.py:199-211` (in execute_symbolic)

---

### STAGE 10: LLM Synthesis (1 call — Final Response Generation)

**What:** Feed all the symbolic results (accepted arguments, defeated arguments, uncertainty report, retrieved prose) into the LLM to generate a calibrated natural language response.

**Why:** The symbolic pipeline produces precise but unreadable output (predicates, tags, labels). Users need a natural language response that correctly reflects the epistemic uncertainty, flags violations, and cites sources. This is the ONLY stage where the LLM adds creative value — everything before was deterministic symbolic computation.

**Processing:** 1 LLM call via DSPy `dspy.Refine(N=3, reward_fn, threshold=0.5)`.

`dspy.Refine` generates up to 3 candidate responses, scores each with the reward function, and returns the best one above the threshold.

```
┌─ INPUT TO DSPy ──────────────────────────────────────────────────┐
│ Signature: SynthesizeResponse                                    │
│                                                                  │
│ query: "Does a company with positive unit economics always       │
│         create value?"                                           │
│                                                                  │
│ accepted_arguments:                                              │
│   "- value_creation(acme): provisional                           │
│      (belief=0.70, sources=['lightweight_grounding'])            │
│    - positive_unit_economics(acme): provisional                  │
│      (belief=0.70, sources=['lightweight_grounding'])"           │
│                                                                  │
│ defeated_arguments:                                              │
│   "No defeated conclusions."                                     │
│                                                                  │
│ uncertainty_report:                                              │
│   "- value_creation(acme): confidence=0.70,                      │
│      epistemic=provisional                                       │
│    - positive_unit_economics(acme): confidence=0.70,             │
│      epistemic=provisional"                                      │
│                                                                  │
│ retrieved_prose:                                                 │
│   "A company with positive unit economics demonstrates value     │
│    creation through sustainable margins.                         │
│                                                                  │
│    However, organizational growth can lead to coordination       │
│    overhead and distorted market signals."                        │
└──────────────────────────────────────────────────────────────────┘

         ▼ DSPy constructs prompt ▼

┌─ ACTUAL PROMPT SENT TO LLM ─────────────────────────────────────┐
│ Produce a calibrated response from argumentation results.        │
│                                                                  │
│ ---                                                              │
│                                                                  │
│ Follow the following format.                                     │
│                                                                  │
│ Query: ${query}                                                  │
│ Accepted Arguments: Formatted list of accepted conclusions       │
│   with epistemic status                                          │
│ Defeated Arguments: Formatted list of defeated conclusions       │
│   with hetvābhāsa types                                         │
│ Uncertainty Report: Structured uncertainty decomposition         │
│ Retrieved Prose: Relevant text from the knowledge base           │
│                                                                  │
│ Reasoning: Let's think step by step.                             │
│ Response: Calibrated response with epistemic qualification.      │
│   Use hedging language for HYPOTHESIS/PROVISIONAL claims.        │
│   Explicitly flag CONTESTED and OPEN items.                      │
│ Sources Cited: Source IDs actually used in the response           │
│                                                                  │
│ ---                                                              │
│                                                                  │
│ Query: Does a company with positive unit economics always        │
│        create value?                                             │
│ Accepted Arguments:                                              │
│   - value_creation(acme): provisional (belief=0.70, ...)         │
│   - positive_unit_economics(acme): provisional (belief=0.70)     │
│ Defeated Arguments: No defeated conclusions.                     │
│ Uncertainty Report:                                              │
│   - value_creation(acme): confidence=0.70, epistemic=provisional │
│   - positive_unit_economics(acme): confidence=0.70               │
│ Retrieved Prose: A company with positive unit economics...       │
│                                                                  │
│ Reasoning: Let's think step by step.                             │
└──────────────────────────────────────────────────────────────────┘

         ▼ dspy.Refine generates up to 3 candidates ▼
         ▼ Scores each with _synthesis_reward()      ▼

Reward function scoring (0.0-1.0):
  +0.20  response length > 50 chars (substantive)
  +0.15  sources_cited not empty
  +0.20  contains epistemic hedging language
         ("established", "hypothesis", "provisional", etc.)
  +0.15  hetvabhasa warnings when violations present
  +0.15  no overconfidence (no "certainly")
  +0.15  extension quality (accepted conclusions exist)

Best candidate selected (score ≥ 0.5 threshold).

         ▼ LLM Response ▼

┌─ OUTPUT ─────────────────────────────────────────────────────────┐
│ response.response:                                               │
│   "Please note that this response is based on provisional        │
│    beliefs and should be taken as a hypothetical scenario."       │
│                                                                  │
│ response.sources_cited:                                          │
│   ["lightweight_grounding"]                                      │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `engine_v4.py:16-34` (SynthesizeResponse signature), `engine_v4.py:36-74` (_synthesis_reward), `engine_service.py:213-244` (synthesis in execute_symbolic)

---

### STAGE 11: Response Assembly & DB Persistence

**What:** Combine all outputs from Stages 3-10 into a single JSON response, update the DB record, and return to the client.

**Why:** The API contract requires all reasoning artifacts (response, sources, uncertainty, provenance, violations, contestation, grounding_confidence, extension_size) in a single response. The DB record is updated for query history and the frontend's polling mechanism (for async jalpa/vitanda queries).

**Processing:** Dict construction + DB write. No LLM.

```
┌─ INPUT ──────────────────────────────────────────────────────────┐
│ All outputs from Stages 3-10                                     │
└──────────────────────────────────────────────────────────────────┘

                    ▼ Processing ▼

1. Assemble result dict
2. Update QueryRecord: status="completed", result_json=json.dumps(result)
3. db.commit()
4. Build QueryResponse via _build_response(record)

┌─ FINAL API RESPONSE (HTTP 201) ──────────────────────────────────┐
│ {                                                                │
│   "id": "1ac4dd7b-e1e1-4800-aa21-6fc068741f11",                 │
│   "kb_id": "3aab9fef-de49-435f-9617-dce78c764490",              │
│   "query_text": "Does a company with positive unit economics     │
│                  always create value?",                          │
│   "contestation_mode": "vada",                                   │
│   "status": "completed",                                         │
│                                                                  │
│   "response": "Please note that this response is based on        │
│                provisional beliefs and should be taken as a       │
│                hypothetical scenario.",                           │
│                                                                  │
│   "sources": ["lightweight_grounding"],                          │
│                                                                  │
│   "uncertainty": {                                               │
│     "value_creation(acme)": {                                    │
│       "epistemic": {status: "provisional", belief: 0.7, ...},    │
│       "aleatoric": {disbelief: 0.0, ...},                        │
│       "inference": {grounding_confidence: 0.7, ...},             │
│       "total_confidence": 0.7                                    │
│     },                                                           │
│     "positive_unit_economics(acme)": { ... same ... }            │
│   },                                                             │
│                                                                  │
│   "provenance": {                                                │
│     "value_creation(acme)": {                                    │
│       sources: ["lightweight_grounding"],                        │
│       pramana: "PRATYAKSA",                                      │
│       derivation_depth: 0, trust: 1.0, decay: 1.0               │
│     },                                                           │
│     "positive_unit_economics(acme)": { ... same ... }            │
│   },                                                             │
│                                                                  │
│   "violations": [],                                              │
│   "grounding_confidence": 0.7,                                   │
│   "extension_size": 2,                                           │
│   "contestation": {                                              │
│     "mode": "vada",                                              │
│     "open_questions": [],                                        │
│     "suggested_evidence": []                                     │
│   },                                                             │
│   "error_message": null,                                         │
│   "duration_ms": 3803,                                           │
│   "created_at": "2026-03-04T05:03:31.980426"                    │
│ }                                                                │
└──────────────────────────────────────────────────────────────────┘
```

**Files:** `routers/queries.py:73-86`, `routers/queries.py:88-108`

---

## Summary: What Happens at Each Stage

| Stage | Name | Processing | LLM? | Time | Why Necessary |
|-------|------|-----------|------|------|---------------|
| 0 | Request Ingestion | Auth, LLM config, route selection | No | <1ms | Determines which of 3 execution paths to use |
| 1 | KB Loading | YAML parse + validation | No | <10ms | Everything downstream needs the structured KB |
| 2 | Ontology Snippet | String construction | No | <1ms | Constrains LLM to valid vocabulary (Layer 1 defense) |
| 3 | LLM Grounding | 1 ChainOfThought call | **Yes** | ~1.5s | Bridges natural language → structured predicates |
| 4 | T2 Compilation | Forward chaining + attack derivation | No | <5ms | Builds formal argumentation framework from facts + rules |
| 5 | Contestation | Grounded semantics fixpoint | No | <1ms | Determines which arguments survive challenges |
| 6 | Epistemic Status | Threshold checks on tags | No | <1ms | Classifies confidence level (ESTABLISHED/HYPOTHESIS/...) |
| 7 | Provenance | Tag field extraction | No | <1ms | Traces conclusions back to sources for auditability |
| 8 | Uncertainty | 3-way decomposition arithmetic | No | <1ms | Explains WHY uncertainty exists (epistemic/aleatoric/inference) |
| 9 | Violations | Attack graph scan | No | <1ms | Detects logical fallacies and contradictions |
| 10 | LLM Synthesis | dspy.Refine(N=3) | **Yes** | ~2s | Produces calibrated natural language response |
| 11 | Response Assembly | Dict + DB write | No | <5ms | Persists result and returns to client |

**Total: 2 LLM calls, 9 symbolic/deterministic stages, ~3.8s end-to-end**

---

## Path Comparison

### Path A: Symbolic (query_facts provided)

Skips Stage 3 entirely. Client supplies predicates directly.

```
Stage 0 → Stage 1 → Stage 4 → Stage 5 → Stage 6 → Stage 7 →
Stage 8 → Stage 9 → Stage 10 → Stage 11

LLM calls: 1 (synthesis only)
Duration:  ~1.8s
Use case:  Frontend pre-populates predicates from previous queries
           or when the user manually selects predicates from the KB
```

### Path B: Lightweight Grounding (is_small_model=true)

All stages. 1 grounding call + 1 synthesis call.

```
Stage 0 → Stage 1 → Stage 2 → Stage 3 → Stage 4 → Stage 5 →
Stage 6 → Stage 7 → Stage 8 → Stage 9 → Stage 10 → Stage 11

LLM calls: 2 (1 grounding + 1 synthesis)
Duration:  ~3.8s
Use case:  Local LLMs (3B-7B params) that can't sustain N=5
           ensemble consistency
```

### Path C: Full N=5 Grounding (is_small_model=false)

Replaces Stage 3 with the full 5-layer grounding defense.

```
Stage 0 → Stage 1 → Stage 2 → Stage 3 (×5 + consensus +
  ?round-trip + ?solver-feedback) → Stage 4 → ... → Stage 11

LLM calls: 5-9 (5 grounding + 0-2 round-trip + 0-3 solver + 1 synthesis)
Duration:  ~30-120s (depending on model and layers triggered)
Use case:  Large API models (GPT-4, Gemini-Pro, Claude) that produce
           consistent structured output across ensemble runs
```

---

## Data Flow Diagram

```
                  Natural Language Query
                          │
                          ▼
              ┌───────────────────────┐
              │   ONTOLOGY SNIPPET    │ ← KnowledgeStore (YAML)
              │   (Layer 1 defense)   │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   LLM GROUNDING       │ ← Llama-3.2-3B (1 call)
              │   NL → Predicates     │
              └───────────┬───────────┘
                          │
                  Structured Predicates
                  [positive_unit_economics(acme),
                   value_creation(acme)]
                          │
                          ▼
              ┌───────────────────────┐
              │   T2 COMPILER         │ ← KnowledgeStore rules
              │   Facts + Rules → AF  │
              └───────────┬───────────┘
                          │
                  Argumentation Framework
                  (Arguments + Attacks)
                          │
                          ▼
              ┌───────────────────────┐
              │   CONTESTATION        │ ← vada/jalpa/vitanda
              │   Compute Extension   │
              └───────────┬───────────┘
                          │
                  Labels (IN/OUT/UNDECIDED)
                          │
              ┌───────────┼───────────┐
              │           │           │
              ▼           ▼           ▼
         ┌─────────┐ ┌────────┐ ┌──────────┐
         │Epistemic│ │Provn.  │ │Uncertain.│
         │ Status  │ │Extract │ │Decompose │
         └────┬────┘ └───┬────┘ └────┬─────┘
              │          │           │
              └──────────┼───────────┘
                         │
              ┌──────────┴───────────┐
              │                      │
              ▼                      ▼
         ┌─────────┐        ┌──────────────┐
         │Violation│        │LLM SYNTHESIS │ ← Llama-3.2-3B
         │ Detect  │        │(dspy.Refine) │   (1 call)
         └────┬────┘        └──────┬───────┘
              │                    │
              └────────┬───────────┘
                       │
                       ▼
              ┌───────────────────────┐
              │   FINAL RESPONSE      │
              │   JSON + DB persist   │
              └───────────────────────┘
```
