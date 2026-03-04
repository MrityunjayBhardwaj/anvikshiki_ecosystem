# Knowledge Bank and Agent Council — Revised for Hybrid Computer Architecture

## What Changed From the Previous Formulation

The original framing left the "agent council" as four unresolved options (A/B/C/D) and treated RAG as the primary retrieval mechanism. Both assumptions are now replaced.

The hybrid computer architecture resolves both problems:
- Each domain expert agent is **not** a standalone LLM — it is a **domain hybrid computer** (logic engine + vector RAG + LLM) wrapped in an agent interface
- RAG is demoted from primary to **last resort** — structural and inference queries go to the logic engine first; prose retrieval only supplements

---

## Why RAG Alone Is the Wrong Foundation

Ānvīkṣikī guides are designed for **progressive sequential reading** where concept B is only meaningful after concept A. The spaced returns mechanism, forward reference matrix, and threshold concept structure create meaning through *temporal separation between chapters*.

Standard RAG collapses this:

```
User query: "How do I evaluate evidence quality?"
RAG retrieves: Chapter 7, paragraph 3 — "When evaluating evidence,
consider effect size and replication..."
```

That chunk assumes the reader has already absorbed the pramāṇa framework from Chapter 1, the failure ontology from the opening, the causal vs. correlation distinction from Chapter 4, and the hetvābhāsa on single-study extrapolation from Chapter 3. The retrieved passage looks complete. It isn't. The agent using it doesn't know what it's missing.

More fundamentally: **RAG is a similarity retrieval system. Ānvīkṣikī is an inference system.** Using RAG as the primary query mechanism is using the wrong tool for the framework's native operation.

---

## The Three-Layer Knowledge Bank

Before the agent council can be designed, the knowledge bank must be understood as three distinct layers with different confidence levels, query types, and update cadences.

```
┌──────────────────────────────────────────────────────────────┐
│  LAYER 1 — LOGIC ENGINE (Stage 2 Architecture as Program)    │
│                                                              │
│  Source: Stage 2 outputs (vyāptis, hetvābhāsas, dependency  │
│          DAG, threshold concepts, epistemic status,          │
│          decay markers, isomorphism map)                     │
│                                                              │
│  Form: Prolog / Datalog / Answer Set Programming             │
│        — vyāptis as Horn clauses                            │
│        — hetvābhāsas as hard constraints (block inference)  │
│        — dependency graph as prerequisite relations          │
│        — epistemic status as metadata on rules               │
│        — decay markers as validity preconditions             │
│        — isomorphism map as cross-domain structural links    │
│                                                              │
│  Queries: inference, prerequisite traversal, constraint      │
│           checking, derivation tracing, cross-domain         │
│           structural matching                                │
│                                                              │
│  Confidence: determined by provenance class of each rule     │
│  Update: when new guide volumes are generated or sourcing    │
│          reconciliation (Step 2Q) revises the architecture   │
└──────────────────────────────────────────────────────────────┘
                          ↓ enriches with context
┌──────────────────────────────────────────────────────────────┐
│  LAYER 2 — REFERENCE BANK (Stage 3 Sourced Facts)           │
│                                                              │
│  Source: Stage 3 outputs — verified, read sources per        │
│          chapter, vyāpti, hetvābhāsa, tacit skill            │
│                                                              │
│  Form: structured citation store with provenance class       │
│        (Class 1–6), direct quotes, inference gaps noted      │
│                                                              │
│  Queries: "What does the evidence actually say about X?"     │
│           "Which sources verify vyāpti V?"                   │
│           "What is the current status of decay marker D?"    │
│                                                              │
│  Confidence: highest — externally verified, source-read      │
│  Update: live search triggered by decay marker activation    │
└──────────────────────────────────────────────────────────────┘
                          ↓ enriches with explanation
┌──────────────────────────────────────────────────────────────┐
│  LAYER 3 — PROSE RAG (Guide Text + Chapter Fingerprints)    │
│                                                              │
│  Source: Stages 4–6 guide prose, chunked by chapter with    │
│          rich metadata from fingerprints:                    │
│          - domain_type (Type 1–5)                           │
│          - chapter_position (foundational/intermediate/etc)  │
│          - vyapti_anchors[] (structural regularities)        │
│          - prerequisite_concepts[] (from Layer 1 graph)      │
│          - epistemic_status (from Layer 1 metadata)          │
│          - provenance_class (1–6, from sourcing protocol)   │
│          - decay_flags[] (links to Layer 1 decay markers)   │
│                                                              │
│  Queries: worked examples, analogies, tacit knowledge prose, │
│           threshold concept explanations, narrative content  │
│                                                              │
│  Confidence: medium — guide prose may include Working        │
│              Hypotheses (Class 6) clearly marked             │
│  Update: immutable per guide version; new versions add       │
│          versioned chunks alongside old ones                 │
└──────────────────────────────────────────────────────────────┘
```

**The critical rule:** Layers are queried in order — 1 → 2 → 3. An agent never reaches Layer 3 (prose) without first having established the structural context from Layer 1 and the evidence grounding from Layer 2. Prose without structural context is how RAG fails.

---

## The Domain Hybrid Computer

Each guide volume produces one **Domain Hybrid Computer** — not a standalone LLM with a system prompt, but a three-subsystem stack:

```
DOMAIN HYBRID COMPUTER: [Domain Name]
═══════════════════════════════════════════════════════════

SUBSYSTEM 1 — LOGIC ENGINE
  Program: Stage 2 architecture encoded as Prolog rules

  Core rules example (corporate strategy domain):

    % Vyāpti V1 — CAUSAL, Class 1 provenance
    strategy_fails(Org) :-
        incentive_structure(Org, S),
        goal_structure(Org, G),
        misaligned(S, G),
        valid_for_inference(v1).   % checks decay + provenance

    % Hetvābhāsa H2 as hard constraint (not advisory)
    :- infers_causation(_, A, B),
       only_correlation_shown(A, B).
       % This BLOCKS the inference — does not just warn

    % Prerequisite chain
    requires(strategic_options, competitive_advantage).
    requires(competitive_advantage, value_creation).
    requires(competitive_advantage, barrier_to_imitation).

    % Epistemic status attached to rules
    confidence(v1, high).
    evidence_quality(v1, experimental).
    provenance_class(v1, class1).
    source_ref(v1, "Jensen & Meckling 1976 (→ Ch4-F1)").

    % Decay validity check
    valid_for_inference(Rule) :-
        \+ decay_risk(Rule, high).
    valid_for_inference(Rule) :-
        decay_risk(Rule, high),
        last_verified(Rule, Date),
        within_threshold(Date).
    % If decay triggered → inference HALTS, Layer 2 live
    % search invoked for current status before proceeding

SUBSYSTEM 2 — REFERENCE BANK (Layer 2)
  Store: structured citation records keyed by RefCode
  Live search: triggered when decay_risk(Rule, high) fires
  Decay resolver: updates last_verified(Rule, Date) after
                  search confirms or corrects the claim

SUBSYSTEM 3 — PROSE RAG (Layer 3)
  Index: chapter chunks with fingerprint metadata
  Always contextualized: Layer 1 prerequisites injected
                         into retrieval query before search
  Provenance-filtered: Class 6 (Working Hypothesis) chunks
                       surfaced with mandatory disclosure

GROUNDING INTERFACE (LLM — Haiku-class, fast)
  Input: natural language query
  Output: predicate form for Layer 1 + retrieval query for Layer 3
  Function: translates "Should I enter this market?" into
            evaluate(market_entry, current_context) and
            populates fact assertions from query context

VERBALIZATION INTERFACE (LLM — Sonnet-class)
  Input: Layer 1 proof trace + Layer 2 citations + Layer 3 prose
  Output: natural language response with derivation visible
  Function: converts proof_trace(T) + source_refs into
            "Following V1 (incentive-outcome alignment),
            supported by Jensen & Meckling (→ Ch4-F1)..."
```

**The key property:** The LLM cannot override the logic engine. If the logic engine's constraint checker fires a hetvābhāsa, the inference is blocked — the LLM verbalization receives a blocked proof trace and must surface the fallacy, not work around it. Hetvābhāsa protection is structural, not instructional.

---

## The Agent Council Architecture (Resolved)

The council is a **federation of Domain Hybrid Computers** with three cross-domain coordination layers:

```
                    USER QUERY
                         │
                         ▼
          ┌──────────────────────────┐
          │     QUERY CLASSIFIER     │
          │   (Haiku-class, fast)    │
          │                          │
          │  Classifies into:        │
          │  [S] Structural/Inference│
          │  [F] Factual             │
          │  [P] Prose/Explanation   │
          │  [N] Novel Problem       │
          │  [X] Cross-domain        │
          │  [C] Contested/Vāda      │
          └────────────┬─────────────┘
                       │
          ┌────────────▼─────────────┐
          │    DOMAIN ROUTER         │
          │                          │
          │  Identifies which        │
          │  domain(s) apply         │
          │  using domain_type       │
          │  classification from     │
          │  Layer 1 of each DHC     │
          └──┬──────────────────┬────┘
             │                  │
    ┌────────▼──────┐  ┌────────▼──────┐
    │  DOMAIN DHC 1 │  │  DOMAIN DHC 2 │  ...
    │  (e.g., Econ) │  │  (e.g., Law)  │
    │               │  │               │
    │ Logic Engine  │  │ Logic Engine  │
    │ Reference Bank│  │ Reference Bank│
    │ Prose RAG     │  │ Prose RAG     │
    └────────┬──────┘  └────────┬──────┘
             │                  │
             └─────────┬────────┘
                       │
          ┌────────────▼─────────────┐
          │     META-REASONER        │
          │   (Opus-class)           │
          │                          │
          │  Manages:                │
          │  - Cross-domain queries  │
          │  - Isomorphism map       │
          │  - Vāda deliberation     │
          │  - Synthesis arbitration │
          └────────────┬─────────────┘
                       │
          ┌────────────▼─────────────┐
          │  DECAY WATCHDOG          │
          │  (background process)    │
          │                          │
          │  Monitors all proof      │
          │  traces for decay-flagged│
          │  nodes; triggers live    │
          │  search before response  │
          │  is finalized            │
          └────────────┬─────────────┘
                       │
                  RESPONSE
              (with provenance,
               derivation trace,
               decay notices)
```

---

## Query Routing by Type

### [S] Structural / Inference Queries
*"Is X derivable from this domain's principles?" / "Does this reasoning violate a principle?"*

```
Route: Query Classifier → Domain Router → DHC Logic Engine
Path: Grounding Interface → Layer 1 (forward/backward chain)
      → Verbalization (proof trace → natural language)

Example: "Our competitor has stronger distribution but our
          product quality is higher — do we have a moat?"

Grounding:  has_advantage(us, product_quality).
            has_advantage(competitor, distribution).
            ?- competitive_moat(us).

Logic engine: applies V3 (moat definition rule), checks
              scope conditions, runs H4 constraint
              (survivorship bias check — is this based on
              past data only?), returns proof trace

Verbalization: "Following V3 (sustainable advantage requires
               barrier to imitation), your quality advantage
               constitutes a moat only if it is difficult to
               replicate. The logic engine flagged H4:
               check whether this assessment is based on
               current competitors only (survivorship bias
               risk). Source: Porter 1985 (→ Ch6-F1)."
```

**Critically:** The hetvābhāsa check (H4) fires as a hard constraint — the logic engine does not produce the conclusion "you have a moat" and then add a caveat. It produces "cannot confirm moat without ruling out H4" and the verbalization reflects that structure.

### [F] Factual Queries
*"What does the evidence say about X?" / "What are the sourced findings on Y?"*

```
Route: Query Classifier → Domain Router → DHC Layer 2
Path: Reference Bank lookup by concept/vyāpti
      → Provenance class surfaced with result
      → Decay Watchdog checks decay_risk before returning

Decay behavior:
  IF decay_risk(claim, low) → return citation directly
  IF decay_risk(claim, high) → PAUSE, trigger live search
    → Update Reference Bank with current status
    → Return updated citation with "verified [date]" note
    → If live search contradicts stored claim → flag conflict
      and surface both the stored claim and current status
```

### [P] Prose / Explanation Queries
*"Explain X in plain language" / "Give me an example of Y"*

```
Route: Query Classifier → Domain Router → DHC all layers
Path: Layer 1 (establish prerequisites + confidence level)
      → Layer 2 (check sourcing for the concept)
      → Layer 3 RAG (retrieve with prerequisite context injected)
      → Verbalization

Layer 3 retrieval is NEVER called without Layer 1 context.
The retrieval query is:
  "Retrieve chunks about [X], filtered to:
   - prerequisite_concepts already established: [list from Layer 1]
   - provenance_class != class6 (unless Working Hypothesis
     disclosure is active)
   - decay_flags not triggered"
```

### [N] Novel Problem Queries
*"How do I approach situation Z that isn't in the guide?"*

```
Route: Query Classifier → Domain Router → DHC full pipeline
Path: Grounding Interface (parse situation into predicates)
      → Layer 1 forward chain (what can we derive about Z?)
      → Layer 1 prerequisite check (what must be true to apply
        relevant vyāptis?)
      → Layer 2 (what does the evidence say about similar cases?)
      → Layer 3 (retrieve analogous worked examples)
      → Verbalization (synthesize derivation + evidence + examples)

This is where the logic engine earns its keep — it can reason
about situations never explicitly covered by the guide by
applying vyāpti chains to new fact combinations.
```

### [X] Cross-Domain Queries
*"Does what I know about epidemiology apply to economics here?"*

```
Route: Query Classifier → Meta-Reasoner (not Domain Router)
Path: Meta-Reasoner queries its isomorphism map (Step 2K
      from Stage 2 of each guide — stored as logic rules):

  isomorphism(
    domain(epidemiology), vyapti(confounding_variable_rule),
    domain(economics), concept(endogeneity),
    shared_structure(hidden_common_cause),
    holds_where([observational_studies, policy_analysis]),
    breaks_where([randomized_controlled_trials])
  ).

Meta-Reasoner:
  1. Finds structural parallels between the two domains
  2. Identifies precisely WHERE the correspondence holds
  3. Identifies WHERE it breaks — and what is UNIQUE to
     the target domain that the source domain can't predict
  4. Invokes both DHCs for their respective Layer 1 + Layer 2
  5. Synthesizes: "The confounding variable logic transfers,
     but breaks here because randomization is possible in
     economics in a way it isn't in epidemiology..."

The cross-domain capability is not LLM pattern-matching —
it is formal structural comparison of two logic programs.
```

### [C] Contested / Vāda Queries
*"Smart people disagree about X — what's the actual crux?"*

```
Route: Query Classifier → Meta-Reasoner → multiple DHCs
Path: Meta-Reasoner identifies:
      - Which domain(s) the question falls under
      - Whether the disagreement is in the Resolution Ledger
        (as an OPEN entry) or the Debate plans (Step 2G)
      - The crux type (Empirical / Values-based / Scope-based /
        Definitional) from the architecture

  IF Scope-based crux → Meta-Reasoner converts to contextual
    analysis: "Position A holds in context [X], Position B
    holds in context [Y]. This is not a genuine debate."

  IF Empirical crux → both positions retrieved from respective
    DHC Logic Engines + Reference Banks; evidence weight
    surfaced; current state of debate from Layer 2 live search

  IF Values-based crux → both positions stated with their
    underlying value commitments made explicit; no false
    resolution attempted; reader directed to the crux

Models Vāda (both sides seeking truth) not Jalpa
(advocacy). The council does not pick winners in genuine
empirical or values-based debates.
```

---

## The Meta-Reasoner in Detail

The Meta-Reasoner is the one agent that does not correspond to a single domain guide. It holds:

**1. The Ānvīkṣikī Framework as a Logic Program**

The five domain types, the pramāṇa hierarchy, and the Kārya-Kāraṇa-Bhāva classification are encoded as meta-rules:

```prolog
% Meta-rule: what counts as valid knowledge in each domain
valid_knowledge(Domain, Claim) :-
    domain_type(Domain, type1_formal),
    provable_from_axioms(Claim, Domain).

valid_knowledge(Domain, Claim) :-
    domain_type(Domain, type3_probabilistic),
    evidence_strength(Claim, S),
    S >= moderate,
    mechanism_partial_or_known(Claim).

% Meta-rule: when to treat a claim as causal vs. observational
infer_as_causal(Claim) :-
    intervention_evidence(Claim),
    mechanism_documented(Claim),
    \+ confounders_unresolved(Claim).
```

**2. The Cross-Domain Isomorphism Map**

All Step 2K outputs across all guide volumes, indexed for fast structural lookup. When a cross-domain query arrives, the Meta-Reasoner traverses this map — it does not ask an LLM to "think about parallels."

**3. Vāda Protocol**

When a contested query arrives, the Meta-Reasoner applies the crux identification procedure from Stage 2G (Debate Planning) before routing to domain DHCs. It filters out false debates (scope-based and definitional cruxes) before they reach the deliberation layer, ensuring only genuine empirical and values-based disagreements are treated as debates.

---

## How the Decay Watchdog Works Computationally

The Decay Watchdog is a background process that runs in parallel with every proof trace. It does not post-process — it intercepts:

```prolog
% Watchdog intercept at inference time
valid_for_inference(Rule) :-
    decay_risk(Rule, high),
    last_verified(Rule, VerifiedDate),
    current_date(Today),
    days_since(VerifiedDate, Today, Days),
    Days =< decay_threshold(Rule).

% If Days > threshold → clause FAILS → inference HALTS
% Watchdog invokes: live_search(Rule, CurrentStatus)
%   → updates: last_verified(Rule, today)
%   → IF search contradicts stored claim:
%        assert conflict_flag(Rule, stored_claim, new_finding)
%        inference uses new_finding, surfaces conflict to user
%   → IF search confirms stored claim:
%        inference continues, "verified [today]" appended to citation

% Decay thresholds by domain type
decay_threshold(Rule) :-
    domain_of(Rule, Domain),
    domain_type(Domain, type4_craft),
    T = 180.  % regulatory/market claims: 6 months
decay_threshold(Rule) :-
    domain_of(Rule, Domain),
    domain_type(Domain, type1_formal),
    T = 1825.  % mathematical facts: 5 years
```

The result: decay is enforced at inference time, not flagged in documentation. A stale claim cannot pass through the logic engine undetected.

---

## What This Means for "Online" Operation

With the hybrid computer architecture, the "online" latency concerns from the original formulation are substantially resolved:

| Component | Latency | Notes |
|-----------|---------|-------|
| Query Classifier | ~100ms | Small model, fast classification |
| Domain Router | ~50ms | Logic lookup, not LLM |
| Layer 1 (Logic Engine) | ~200ms | Prolog inference, deterministic |
| Layer 2 (Reference Bank) | ~100ms | Structured database lookup |
| Layer 2 (Live Search, if decay triggered) | ~3–5s | Only when decay fires — not every query |
| Layer 3 (RAG retrieval) | ~500ms | Vector search |
| Verbalization (LLM) | ~2–4s | Main latency cost |
| **Total (no decay trigger)** | **~3s** | Acceptable for most use cases |
| **Total (decay trigger)** | **~8–10s** | User notified: "verifying current status..." |

The logic engine and reference bank are the **fast path** — most structural queries never reach the LLM verbalization layer until the proof trace is complete. The LLM is called once at the end to render the result, not continuously throughout the reasoning chain.

---

## What Each Domain Guide Volume Produces

When a new guide is generated using the Ānvīkṣikī meta-prompt, it produces three artifacts that slot directly into the three-layer knowledge bank:

```
Guide Volume → Three Deployable Artifacts:

ARTIFACT 1: Logic Program (Layer 1)
  Generated from: Stage 2 architecture outputs
  Format: Prolog/Datalog file per domain
  Contains: vyāpti rules, hetvābhāsa constraints,
            prerequisite relations, threshold concept
            markers, epistemic metadata, decay conditions,
            isomorphism map entries

ARTIFACT 2: Sourced Fact Store (Layer 2)
  Generated from: Stage 3 Reference Bank + Step 3H
                  verification records
  Format: structured citation database
  Contains: RefCode → (source, passage, provenance class,
                       inference gap, decay_risk, last_verified)

ARTIFACT 3: Prose RAG Index (Layer 3)
  Generated from: Stages 4–6 guide text + chapter fingerprints
  Format: vector index with rich metadata per chunk
  Contains: chapter text with vyapti_anchors, prerequisite_concepts,
            provenance_class, decay_flags, and fingerprint data
```

A new domain volume integrates into the existing council by:
1. Deploying its Logic Program into the Logic Engine registry
2. Loading its Sourced Fact Store into the Reference Bank
3. Indexing its Prose into the RAG layer
4. Registering its isomorphism map entries with the Meta-Reasoner

No council retraining. No architecture changes. Pure extension.

---

## What the Council Cannot Do (Honest Limits)

**Cannot reason about domains without a guide volume.** The logic engine only contains what was encoded from Stage 2. A query about a domain with no guide returns: "No domain program loaded for this topic — response would rely on LLM training knowledge only. Proceed with caution."

**Cannot resolve genuine empirical disagreements.** The council models Vāda — it presents both positions with evidence weights, identifies the crux, and specifies what evidence would settle it. It does not fabricate resolution where none exists.

**Cannot make Class 6 (Working Hypothesis) claims invisible.** The Verbalization interface always surfaces provenance class. A Working Hypothesis appears in the response with its disclosure, regardless of how confident the LLM verbalization would otherwise sound.

**Cannot override a blocked hetvābhāsa constraint.** If the logic engine blocks an inference because H3 fires, the LLM cannot route around it. The response states that the inference is invalid and names the fallacy — it does not "helpfully" produce the conclusion anyway.

---

## Summary: What Changed From the Original Formulation

| Original | Revised |
|----------|---------|
| RAG as primary retrieval | Logic engine as primary; RAG as context enrichment only |
| Four unresolved council options (A/B/C/D) | Resolved: federated Domain Hybrid Computers + Meta-Reasoner |
| Hetvābhāsas as reminders | Hetvābhāsas as hard constraints blocking invalid inference |
| Decay markers as documentation flags | Decay as inference-time validity preconditions triggering live search |
| LLM does the reasoning | Logic engine does the reasoning; LLM grounds and verbalizes |
| Cross-domain by LLM pattern-matching | Cross-domain by formal isomorphism map traversal |
| "Online" as a complication | Online latency managed by fast logic path; LLM called once at end |
| New volume = RAG ingestion | New volume = three deployable artifacts slotting into existing layers |
| Agent council as LLMs with domain system prompts | Agent council as domain hybrid computers with agent interfaces |
