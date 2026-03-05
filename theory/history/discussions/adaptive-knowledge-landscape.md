# Adaptive Knowledge Landscape

## The Problem

The Anvikshiki engine has a curated knowledge base (KB) of 11 vyaptis covering ~20 predicates about business strategy. When a user asks "How should I think about supply chain resilience?" the engine runs query refinement, finds coverage_ratio ≈ 0.15, and honestly says: "I don't know."

This is correct but wasteful. The engine *does* know how to think about this problem. V02 (Constraint Cascade) applies directly — supply chain resilience is fundamentally about identifying binding constraints in a supply network. V06 (Optionality-Commitment) applies — resilience is about maintaining optionality vs over-committing to single suppliers. The engine has the *frameworks* but lacks the *specific predicates* to reason about supply chains.

The current system treats "not in KB" as "not answerable." But the real situation is often "in-domain, under-represented" — the domain frameworks apply, but the fine-grained knowledge needed for this specific question hasn't been encoded.

**The gap:** Between a general principle ("identify the binding constraint → resource allocation becomes effective") and a specific application ("in supply chains, single-source dependency is a common binding constraint that dual-sourcing can relieve") lies the knowledge the engine is missing.

---

## Brainstormed Solutions

### Solution 1: Broader KB (Rejected)

Just add more vyaptis manually. Cover supply chains, marketing, hiring, etc.

**Why it fails:** Combinatorial explosion. The domain of "business strategy" has thousands of sub-topics. Manual curation doesn't scale. You'd need a dedicated knowledge engineer maintaining the KB, and you'd always be behind user needs.

### Solution 2: Generic RAG Augmentation (Rejected)

When coverage is low, retrieve relevant documents from the web, stuff them into the LLM context, and generate an answer.

**Why it fails:** This is what every other system does. The retrieved text has no formal structure. The LLM generates a plausible-sounding answer, but there's no argumentation, no epistemic status, no provenance tracking, no uncertainty decomposition. You lose everything that makes Anvikshiki different from ChatGPT. The answer can't be contested via Vāda/Jalpa/Vitaṇḍā because there are no formal arguments to attack.

### Solution 3: Pre-computed Exhaustive Extraction (Rejected)

Run the predicate extraction pipeline (Stages A–E) over the entire guide upfront, generating hundreds of fine-grained predicates to cover every possible sub-topic.

**Why it fails:** Over-investment. Most of these predicates would never be queried. The shadow KB bloats with low-quality, untested knowledge. And you still can't cover topics the guide doesn't discuss — the guide talks about constraints in general but doesn't specifically cover supply chain constraints.

### Solution 4: Adaptive Knowledge Landscape (Proposed)

Use the base KB as a *coordinate system* — it defines the conceptual dimensions through which all domain knowledge is organized. When a query lands in an area with insufficient resolution, dynamically generate fine-grained predicates using:
1. The base KB's frameworks as structural templates
2. The LLM's parametric knowledge, interpreted through those frameworks
3. (Later) Web-retrieved evidence for sourcing and verification

Generated predicates enter the argumentation framework as full participants — same attack/defense rights as curated predicates, with confidence derived from evidence quality rather than KB layer of origin.

---

## Related Work and Why It Falls Short

### RAG Systems (Perplexity, Google AI Overview)

Retrieve text, generate answer. No formal knowledge representation, no argumentation, no uncertainty decomposition. The "answer" is just text — it can't be attacked, defended, or contested. There's no epistemic status on individual claims. When sources contradict, the LLM picks one without formal conflict resolution.

### GraphRAG (Microsoft, 2024)

Builds a community-hierarchical knowledge graph from a corpus, uses Leiden clustering for multi-level retrieval. Better than flat RAG because it captures relationships. But the graph is built at indexing time, not query time. If the corpus doesn't cover supply chains, the graph doesn't either. There's no mechanism for *generating* new graph structure on demand.

### Generate-on-Graph / GoG (EMNLP 2024)

Closest existing system. The LLM acts as both KG navigator and KG — generating missing triples from parametric knowledge when the graph has gaps. Robust even when 80% of crucial triples are missing. But GoG has no notion of *frameworks* guiding generation. It generates triples based on general LLM knowledge, not through a domain-specific reasoning lens. The generated triples have no epistemic status, no decay tracking, no scope conditions.

### LeanRAG (2025)

Multi-resolution KG with bottom-up retrieval: fine-grained entities → semantic clusters → community summaries. Explicit relations between levels (unlike GraphRAG's disconnected communities). Captures the quadtree-like resolution idea. But it's a retrieval architecture, not a knowledge generation architecture. It navigates existing knowledge at different resolutions — it doesn't *create* knowledge at fine resolution when it's missing.

### Self-RAG / Adaptive-RAG (ICLR 2024, NAACL 2024)

Selective retrieval: the model decides when external information is needed. Self-RAG uses reflection tokens; Adaptive-RAG routes queries to no-retrieval / single-step / multi-step. Important insight: always-retrieve hurts performance (SIGIR 2024 "Power of Noise" paper). But these systems don't generate structured knowledge — they retrieve text and decide whether to use it. No formal argumentation over the retrieved content.

### KARMA (NeurIPS 2025 Spotlight)

Multi-agent KG enrichment with conflict resolution agents. 83.1% correctness on PubMed, 18.6% reduction in contradictions. Impressive for batch KG construction, but designed for corpus-driven enrichment, not query-driven augmentation. The agents work over a fixed corpus, not in response to a specific user question.

### Dynamic Argumentation Frameworks (DYNARG Project)

Formal theory of how acceptability semantics evolve when arguments are added/removed. AGM-style revision operators for Dung frameworks. Probabilistic argumentation with source-weighted arguments. This gives us the theoretical foundation for dynamically adding arguments, but no existing system combines this with LLM-driven knowledge generation or framework-guided retrieval.

### OG-RAG (Microsoft, EMNLP 2025)

Ontology-Grounded RAG: uses a domain ontology to structure retrieval into hypergraph clusters. 55% improvement in fact recall. This validates the core insight that ontology-guided retrieval beats naive vector similarity. But OG-RAG retrieves from an existing corpus — it doesn't generate new ontological concepts when the corpus has gaps.

### The Common Gap

Every existing system either:
- **Retrieves** existing text/triples (RAG, GraphRAG, LeanRAG, OG-RAG) — fails when the corpus doesn't cover the query
- **Generates** new triples without domain structure (GoG) — produces knowledge without framework alignment
- **Enriches** KGs from fixed corpora (KARMA) — not query-driven

None of them use *domain reasoning frameworks as structural templates for knowledge generation*. None combine framework-guided generation with formal argumentation over the results.

---

## Why This Approach Is Needed

### The Insight: Base KB as Coordinate System

The base KB (11 vyaptis) doesn't just store facts — it defines a **conceptual coordinate system** for the domain:

- **Value creation axis** (V01, V08): Does this create or destroy value?
- **Organizational complexity axis** (V04, V05, V07): How does scale/structure affect this?
- **Competitive dynamics axis** (V03, V09): What's the information/positioning advantage?
- **Decision quality axis** (V10, V06): How should one decide about this?

A query like "supply chain resilience" gets *projected* onto these axes:
- Value creation: How does resilience affect unit economics?
- Organizational complexity: How does resilience interact with coordination overhead?
- Competitive dynamics: Is resilience a moat?
- Decision quality: How do you decide the right resilience investment level?

The augmentation fills in fine-grained detail *within each relevant axis*. The base KB provides the conceptual coordinate system through which all new knowledge is organized.

**This is fundamentally different from generic RAG, which has no coordinate system — it just retrieves "similar text."**

### The Framework Question: Diagnostic Questions or Structural Patterns?

There's a deeper question about what a "framework" is operationally.

Consider V02 (Constraint Cascade): `binding_constraint_identified → resource_allocation_effective`

**As diagnostic questions**, this becomes:
> "What is the binding constraint? Where are resources being wasted? What would improve if we relaxed this one thing?"

**As structural patterns**, this becomes:
> "In any system with flow, there exists a bottleneck node. The bottleneck determines total throughput. Relieving the bottleneck improves the whole system's efficiency."

The structural pattern is more general — it applies to supply chains, software systems, hiring pipelines, anything with flow. The diagnostic questions are domain-specific instantiations of that pattern.

If frameworks are structural patterns, then augmentation doesn't just ask "what's the bottleneck in supply chains?" — it asks "what is the system? what flows through it? where does flow get constrained?" and generates predicates at *that* level of abstraction, then instantiates them for the specific query domain.

**For v1, we treat frameworks as "existing vyaptis + chapter context included in the LLM prompt."** The LLM implicitly captures both the diagnostic questions and the structural patterns. Formalizing the distinction can wait.

---

## Emerging Properties

### The Engine Becomes a Domain Expert

With adaptive augmentation, the engine stops being a "QA system that checks its knowledge base" and becomes something closer to **a domain expert that reasons through problems using internalized frameworks**.

Real experts don't memorize every fact about every sub-topic. They have mental models (constraint theory, optionality analysis, competitive dynamics) and apply them to whatever situation they encounter. When a business strategist encounters a supply chain question, they don't look it up in a database — they think: "This is a constraint problem. Where's the bottleneck? What's the optionality structure?"

The base KB encodes "the way of thinking." The augmented KB encodes "the specific knowledge applied to this specific problem." The engine reasons like an expert: general frameworks + specific investigation = structured answer with provenance.

### Self-Healing, Self-Evolving Knowledge Map

Over time, as users ask diverse questions:
- Query about supply chains → generates 5 provisional predicates
- Query about pricing strategy → generates 4 provisional predicates
- Query about hiring → generates 6 provisional predicates

The knowledge landscape gains resolution where users need it. Frequently queried regions accumulate detail. Rarely queried regions stay coarse. The system allocates its knowledge budget based on actual demand — like a quadtree that subdivides only where queries land.

If an augmented predicate turns out to be wrong (gets defeated in argumentation repeatedly, or HITL rejects it), the system prunes it. The landscape heals.

As shadow predicates get HITL-promoted, the base KB grows. The coarse grid becomes finer globally. This is **domain knowledge acquisition through use**.

### Equal Standing for New Knowledge

Augmented predicates aren't second-class citizens. They participate in argumentation with the same attack/defense rights as curated predicates. A well-evidenced augmented finding about supply chain dynamics might be *more* specific and reliable than a general principle applied to supply chains by analogy.

The confidence comes from **evidence quality**, not from which KB layer a predicate originated. The ASPIC+ framework resolves conflicts through argumentation — if a specific finding contradicts a general rule in a specific context, it generates scope exclusions naturally.

This means the augmented KB can discover **boundary conditions** for general rules: "V01 says positive unit economics → value creation, but in supply chains with single-source dependency, positive unit economics can coexist with fragility that destroys long-term value." That's genuine knowledge discovery.

---

## Design Decisions Made

| Question | Decision | Rationale |
|----------|----------|-----------|
| Trust model for augmented predicates | Equal rights, confidence from evidence quality | ASPIC+ already handles varying argument strength |
| Domain boundary test | Framework applicability (can the guide's reasoning templates illuminate this?) | Tighter than "is this business?", only augment when frameworks are useful |
| Augmentation trigger | Selective (epistemic status as signal) | Self-RAG research shows always-retrieve hurts; use ESTABLISHED/HYPOTHESIS/OPEN as triggers |
| Cross-domain chaining | LLM generates connections naturally | LLM sees existing KB + new topic, generates predicates that chain into existing structure |
| Pramana type | SABDA (testimony) with evidence-quality confidence | Simpler than adding UPAMANA; reuses existing type |
| Search strategy | 2-pass: LLM parametric first, web search second | GoG validates LLM-as-KB approach; web adds sourcing |
| Storage | Persistent shadow KB with HITL promotion | Knowledge accumulates where users need it |

---

## Research Foundation

| Component | Key Paper | Finding |
|-----------|-----------|---------|
| Selective augmentation | Self-RAG (ICLR 2024), Adaptive-RAG (NAACL 2024) | Don't always retrieve; selective > always-retrieve |
| Source reliability | RA-RAG (2024), ReliabilityRAG (NeurIPS 2025) | Cross-source agreement + graph-based contradiction detection |
| LLM as KB | GoG (EMNLP 2024) | LLM can generate missing KG triples; robust at 80% gaps |
| Ontology-guided retrieval | OG-RAG (EMNLP 2025) | 55% better fact recall with ontology structure |
| Multi-resolution KG | LeanRAG (2025) | Bottom-up navigable hierarchy with explicit inter-level links |
| KG conflict resolution | KARMA (NeurIPS 2025) | Multi-agent debate resolves contradictions (83.1% correctness) |
| Dynamic argumentation | DYNARG, AGM for Dung (IJCAI 2015) | Principled operators for adding/removing arguments |
| Retrieval noise | SIGIR 2024 "Power of Noise" | Irrelevant retrieval from strong retrievers actively hurts |
| Hallucination rates | Multiple surveys (2024-2025) | 28-82% hallucination for structured extraction; multi-layer defense essential |

---

## v1: Minimal Viable Version

### What v1 Does

When query refinement returns PARTIAL or DECLINE but the query is in-domain (framework applicability > threshold):

1. **Domain check** (1 LLM call): Score framework applicability — can the guide's reasoning templates illuminate this query?
2. **Generate predicates** (1 LLM call): Ask LLM to generate relevant predicates using existing vyaptis as structural templates + chapter context as domain grounding
3. **Validate** (0 LLM calls): Cycle detection, Datalog compilation test (reuse existing Stage E logic)
4. **Merge and run** (0 additional LLM calls): Add augmented predicates as HYPOTHESIS to a merged KB, run the engine normally

Total additional cost: **2 LLM calls** beyond the existing pipeline.

### What v1 Doesn't Do (Yet)

- No web search (Pass 2) — LLM parametric knowledge alone proves the concept
- No source reliability scoring — mark everything HYPOTHESIS
- No shadow KB persistence — ephemeral, per-query augmentation
- No HITL promotion — no shadow KB to promote from
- No formalized framework YAML — existing vyaptis + chapter context in the prompt is sufficient
- No Vitaṇḍā stress test — existing argumentation already handles weak predicates via belief ordering

### What v1 Proves

If the engine can take "How should I think about supply chain resilience?" and generate:
- `supply_chain_bottleneck` (via V02 constraint pattern)
- `single_source_dependency → supply_chain_fragility` (new vyapti, HYPOTHESIS)
- `supplier_diversification → supply_chain_resilience` (new vyapti, HYPOTHESIS)
- `supply_chain_resilience + resource_allocation_effective → long_term_value` (chains to V08)

...and then run ASPIC+ argumentation over the merged KB with uncertainty decomposition and provenance tracking — then the core idea works. Everything else is optimization.

### Implementation Path

```
v1: Ephemeral augmentation (LLM parametric only)
  → Proves: framework-guided predicate generation works

v2: Add web search (Pass 2) for sourcing
  → Proves: external evidence improves confidence

v3: Shadow KB persistence + HITL review
  → Proves: knowledge accumulation through use

v4: Source reliability scoring + Vitaṇḍā stress test
  → Proves: quality control at scale

v5: Formalized framework templates + multi-domain
  → Proves: generalizes beyond business strategy
```

### Where It Plugs In

```
query_refinement.py  →  NEW: kb_augmentation.py  →  engine_v4.py
         |                        |                       |
   CoverageAnalyzer         AugmentationPipeline    runs with merged KB
   returns PARTIAL/         - domain_check()
   DECLINE + in_domain      - generate_predicates()
                            - validate()
                            - merge_kb()
```

One new file. ~200-300 lines. Reuses existing Stage E validation, existing KnowledgeStore merge, existing engine pipeline. The augmented predicates are regular Vyapti objects with `epistemic_status=HYPOTHESIS` — the rest of the engine doesn't know or care that they were dynamically generated.
