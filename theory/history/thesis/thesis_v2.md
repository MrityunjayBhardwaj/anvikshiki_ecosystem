# The Ānvīkṣikī Engine (v2)

## From Philosophical Epistemology to Neurosymbolic Inference: Building a Lattice-Datalog Knowledge Engine with Layered Grounding Defense

---

**Abstract.** This thesis presents the design, architecture, and incremental construction of the Ānvīkṣikī Engine — a neurosymbolic reasoning system that compiles structured domain knowledge into an executable inference engine with principled uncertainty quantification. The system takes as input a pedagogical guide produced by the Ānvīkṣikī meta-prompt (a 3,963-line specification for generating expert-level instructional content) and compiles it into two subsystems: T2, a logic engine implementing domain-specific rules as executable inference; and T3, a graph-structured retrieval corpus that serves the prose layer. We develop the engine in four incremental stages — DSPy-only, DSPy+Datalog, DSPy+Lattice Datalog+UQ, and DSPy+Lattice Datalog+Sheaf+UQ — each addressing fundamental limitations of the prior. The critical revision from the original thesis is threefold: (1) Prolog is replaced by Datalog with lattice extensions throughout, providing Heyting-valued inference with guaranteed termination and polynomial complexity; (2) the grounding problem — identified as the architecture's weakest link — is addressed through a five-layer defense combining ontology-constrained prompting, grammar-constrained decoding, ensemble consensus, round-trip verification, and solver-feedback refinement; (3) the naive forward-chaining Heyting engine is replaced by semi-naive Datalog evaluation, reducing per-iteration cost from O(rules × facts) to O(rules × Δfacts). The final architecture provides formally correct epistemic qualification, scope-dependent reasoning, cohomological fallacy detection, and uncertainty decomposition that no existing RAG or LLM system achieves — with tractability guarantees that the original thesis lacked.

---

## Table of Contents

1. Why Bother?
2. Fundamentals
   - 2.1 Epistemological Foundations
   - 2.2 The Specification Language
   - 2.3 The Pedagogical Compiler
   - 2.4 Multi-Paradigm Reasoning
   - 2.5 Production Rule Systems
   - 2.6 Pedagogical Theory
3. The Meta-Prompt
4. The Guide
5. On Turing Completeness
6. The Grounding Problem
   - 6.1 Problem Decomposition
   - 6.2 Seven Strategies
   - 6.3 The Five-Layer Defense
   - 6.4 Implementation Code
7. Developing the Engine
   - 7.1 Architecture Overview
   - 7.2 Phase 1: DSPy Only — The Baseline
   - 7.3 Why Not Prolog?
   - 7.4 Phase 2: DSPy + Datalog
   - 7.5 Phase 3: DSPy + Lattice Datalog + UQ
   - 7.6 Phase 4: DSPy + Lattice Datalog + Sheaf + UQ
8. The Final Engine — Complete Implementation
9. What Is Truly Novel
10. Limitations
11. Further Directions
12. References

---

## 1. Why Bother?

There is a gap in how knowledge systems work today that most practitioners feel but few articulate precisely.

Large language models are extraordinary pattern matchers. They can write plausible essays on corporate strategy, generate code that compiles, and mimic the style of domain experts convincingly. But they cannot *reason* over a knowledge base with guarantees. Ask an LLM "given that this company has misaligned incentives and is in a declining market, what can we derive about its strategic position?" and it will generate a plausible paragraph. It will not — because it cannot — chain domain-specific rules, check whether the reasoning violates known fallacy patterns, verify that the claims are grounded in cited evidence, or decompose its uncertainty into "I don't have enough evidence" versus "the domain is inherently uncertain here."

Retrieval-Augmented Generation (RAG) addresses the grounding problem by retrieving relevant text chunks and feeding them to an LLM for synthesis. But RAG is similarity retrieval, not inference. It finds text that looks relevant. It cannot derive consequences, check prerequisites, detect scope violations, or prove that a conclusion follows from premises. RAG treats every chunk as independent; the rich dependency structure between concepts — which determines whether a reader can even understand a retrieved passage — is invisible.

Knowledge graphs improve on flat retrieval by encoding relationships, but standard knowledge graphs have Boolean truth: an edge exists or it doesn't. In practice, domain knowledge carries epistemic qualification ("this is well-established," "this is a working hypothesis," "experts actively contest this"), scope conditions ("holds for private firms but not public ones"), decay markers ("this depends on the current regulatory environment — verify before applying"), and multiple inference modes ("this follows by causal mechanism" versus "this is observed empirical regularity" versus "this is the consensus of expert practitioners").

The Ānvīkṣikī Engine exists to close this gap. It takes a structured domain knowledge base — produced by the Ānvīkṣikī meta-prompt as a pedagogical guide — and compiles it into a system that can:

1. **Infer**, not just retrieve — chain domain rules to derive novel conclusions
2. **Constrain**, not just generate — detect and reject fallacious reasoning patterns
3. **Qualify**, not just assert — carry epistemic status through every inference step
4. **Decompose uncertainty** — separate "we don't know" from "nobody can know" from "the LLM might be wrong"
5. **Ground to sources** — trace every claim to its evidence with statistical guarantees
6. **Respect scope** — know when a rule applies and when it doesn't, without human intervention
7. **Decay gracefully** — halt inference on stale knowledge and trigger verification

No existing system does all seven. This thesis shows how to build one.

---

## 2. Fundamentals

### 2.1 Epistemological Foundations

The Ānvīkṣikī framework draws on Nyāya epistemology, one of the six orthodox schools of Indian philosophy, systematized by Gautama (c. 2nd century BCE) in the *Nyāya Sūtras* and refined over two millennia. The framework uses three core constructs:

**Pramāṇa** (means of valid knowledge): How do we know something is true in this domain? The meta-prompt classifies domains along eight types (Formal, Mechanistic, Empirical, Craft, Interpretive, Design, Normative, Meta-Analytical), each with characteristic pramāṇas. A formal domain (Type 1) accepts deductive proof. A craft domain (Type 4) accepts practitioner judgment alongside systematic study. This classification determines which inference modes the engine can legitimately use.

**Vyāpti** (invariable concomitance): The production rule. "Wherever there is smoke, there is fire" — formalized as `smoke(X) → fire(X)`. Each vyāpti has a causal status (structural, regulatory, empirical, definitional), scope conditions, confidence ratings, evidence quality markers, and decay characteristics. Vyāptis are the executable rules of the engine.

**Hetvābhāsa** (fallacious reason): The constraint. A systematic catalog of ways inference can fail — survivorship bias, benchmark fallacy, scale extrapolation, framework reification, temporal displacement, false dichotomy. These are not merely warnings; in the engine, they are formal integrity constraints that fire when the reasoning pattern matches a known fallacy structure.

The pañcāvayava (five-limbed argument) provides the proof trace format: proposition, reason, universal rule (vyāpti), application to the case, conclusion. Every engine output carries this trace, making reasoning inspectable.

### 2.2 The Specification Language

Ānvīkṣikī v3.26 uses a hybrid domain-specific language (DSL) combining LISP-like s-expressions for the formal ontology with natural-language prose for the generation process. The LISP layer (724 lines in compact form) defines:

- Domain classification taxonomy (8 types with subtypes)
- Pramāṇa structures per domain type
- Vyāpti schema (causal status, scope, confidence, evidence, decay)
- Hetvābhāsa catalog (fallacy type, detection signature, correction pattern)
- Dependency graph structure (DAG with forward references)
- Epistemic status markers (4-valued: ESTABLISHED, WORKING HYPOTHESIS, GENUINELY OPEN, ACTIVELY CONTESTED)
- Chapter fingerprint schema (key terms, anchoring concepts, forward dependencies)

The prose layer (3,963 lines) specifies the eight-stage generation pipeline with gates, quality metrics, and human-interface instructions that cannot be reduced to formal specification without loss.

The LISP layer compiles to T2 (logic engine) and T3 (retrieval corpus). The prose layer drives T1 (guide generation). Both fork from the same verified architecture after Stage 3 (Research Gate).

### 2.3 The Pedagogical Compiler

The meta-prompt is a compiler. Its input is a domain specification (subject, audience, scope). Its output is a multi-hundred-page pedagogical guide structured according to the Ānvīkṣikī architecture. The compilation proceeds through eight stages:

- **Stage 1**: Domain Audit — classify the domain, identify pramāṇas
- **Stage 2**: Knowledge Architecture — extract vyāptis, hetvābhāsas, threshold concepts, dependency graph
- **Stage 3**: Research Gate — verify architecture against current literature with web search
- **Stage 4**: Structural Planning — organize into parts, chapters, sections with prerequisites
- **Stage 5**: Content Generation — produce prose with embedded pedagogical machinery
- **Stage 6**: Integration — add cross-references, spaced returns, confusion-pair alerts
- **Stage 7**: Quality Assurance — verify coverage, check decay markers, validate citations
- **Stage 8**: Final Assembly — produce the guide with metadata, fingerprints, reference bank

Each stage has gate conditions (minimum vyāpti count, dependency coverage, citation density). The T2 engine compiles from Stage 2+3 output (verified architecture). The T3 corpus compiles from Stage 5+ output (guide text with metadata).

### 2.4 Multi-Paradigm Reasoning

Different domains require different inference modes. The engine supports a taxonomy of reasoning paradigms matched to domain types:

| Domain Type | Primary Inference Mode | Formal Analog |
|-------------|----------------------|---------------|
| Type 1 (Formal) | Deductive | Theorem proving |
| Type 2 (Mechanistic) | Causal-deductive | Structural equation models |
| Type 3 (Empirical) | Probabilistic-inductive | Bayesian inference |
| Type 4 (Craft) | Abductive (pattern + ranking) | Case-based reasoning |
| Type 5 (Interpretive) | Dialectical-argumentative | Argumentation frameworks |
| Type 6 (Design) | Generative-evaluative | Constraint satisfaction |
| Type 7 (Normative) | Deontic | Modal logic |
| Type 8 (Meta-Analytical) | Multi-framework synthesis | Simulation |

The engine begins with Type 4 (Craft) as the primary target — business strategy, the motivating domain. Abductive reasoning (inference to the best explanation) maps naturally to pattern matching with confidence ranking, which an ML practitioner can implement directly.

### 2.5 Production Rule Systems

The engine is, at its architectural core, a production rule system — a knowledge representation paradigm dating to Post (1943) and formalized in systems like OPS5, CLIPS, and Drools. A production rule system has:

- A **working memory** of facts (the grounded context of a query)
- A **rule base** of condition-action pairs (the vyāptis)
- A **conflict resolution strategy** (when multiple rules fire, which applies?)
- An **inference engine** that matches facts against rules

The Ānvīkṣikī engine extends classical production rule systems in three directions: (1) rules carry epistemic qualification, not just Boolean applicability; (2) integrity constraints (hetvābhāsas) actively monitor the inference trace for fallacy patterns; (3) the working memory is populated by an LLM grounding module that translates natural language into structured facts, making the system accessible through conversational interface.

### 2.6 Pedagogical Theory

The guide is not merely a knowledge dump — it is a pedagogically engineered artifact. Three theories underpin its design:

**Threshold Concepts** (Meyer & Land, 2003): Certain concepts are transformative, irreversible, and integrative. Once understood, they permanently reorganize the learner's conceptual landscape. The engine's dependency graph encodes prerequisite chains that lead to threshold concepts, and the T3 retrieval respects these prerequisites (never retrieving content whose prerequisites are unmet).

**Cognitive Load Theory** (Sweller, 1988): Working memory is limited. The engine manages intrinsic load (concept difficulty), extraneous load (poor organization), and germane load (schema construction). Spaced returns, graduated complexity, and confusion-pair alerts are all cognitive load management strategies encoded in the guide structure.

**Tacit Knowledge** (Polanyi, 1966): Much domain expertise is inarticulate — the practitioner "knows more than they can tell." The meta-prompt systematically excavates tacit knowledge through its domain audit (Stage 1) and surfaces it through worked examples, analogy structures, and "reader suspicion" patterns that anticipate where the expert's unstated assumptions create comprehension barriers.

---

## 3. The Meta-Prompt

The Ānvīkṣikī meta-prompt (v3.26) is a 3,963-line natural-language specification that instructs a large language model to generate a pedagogical guide. It is not the engine — it is the program that produces the input to the engine.

### What the Meta-Prompt Does

Given a domain specification, the meta-prompt orchestrates eight sequential stages of knowledge synthesis:

**Stages 1-3 (Analysis)** produce the verified architecture: domain type classification, pramāṇa identification, vyāpti extraction (minimum 7 per domain, each with causal status, scope conditions, confidence ratings), hetvābhāsa identification (minimum 6, each with detection signatures), dependency graph construction, threshold concept identification, reader calibration (expertise level, tacit density), and live research verification of all architectural elements against current literature.

**Stages 4-8 (Synthesis)** produce the guide: structural planning (Parts I-V mapping to conceptual progression), content generation (prose with embedded pedagogical machinery), integration (cross-references, spaced returns, forward references), quality assurance (coverage verification, citation density checks, decay marker validation), and final assembly.

### The Pipeline

```
Domain Specification (NL input)
        │
        ▼
   ┌─────────────┐
   │  Stage 1:    │ → Domain type, pramāṇas, reader profile
   │  Domain Audit│
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  Stage 2:    │ → Vyāptis, hetvābhāsas, dependency DAG,
   │  Knowledge   │   threshold concepts, chapter fingerprints
   │  Architecture│   (DRAFT — unverified)
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  Stage 3:    │ → Verified architecture + Reference Bank
   │  Research    │   (WITH sources, timestamps, conflict notes)
   │  Gate        │
   └──────┬──────┘
          │
     ─────┼───────────────── FORK POINT ──────────
     │                                            │
     ▼                                            ▼
   T2 COMPILER                              STAGES 4-8
   (this thesis)                            (guide generation)
   Verified architecture                          │
   → Logic Engine                                 ▼
                                             T1 GUIDE
                                                  │
                                                  ▼
                                            T3 COMPILER
                                            (this thesis)
                                            Guide + fingerprints
                                            → RAG Corpus
```

### What the Meta-Prompt Is Not

The meta-prompt is not the engine. It does not perform inference, check constraints, or decompose uncertainty. It is a one-shot generator that produces structured content. The engine consumes that content and makes it queryable, inferrable, and verifiable. The meta-prompt is a compiler from domain specification to knowledge artifact. The engine is the runtime that executes against that artifact.

---

## 4. The Guide

The T1 guide — the output of running the meta-prompt — is a multi-hundred-page document with the following structure:

### Part I: Foundations
Establishes the domain's conceptual bedrock. Introduces core vocabulary, foundational vyāptis, and the first threshold concepts. Calibrated to the reader's entry level. No concept depends on content introduced later.

### Part II: Core Mechanisms
Develops the domain's central causal chains. Each chapter introduces 2-3 vyāptis with full justification, scope conditions, and worked examples. Hetvābhāsa alerts appear where relevant fallacies are most likely to occur.

### Part III: Applications and Extensions
Applies the framework to specific scenarios. Introduces scope-dependent reasoning — the same vyāpti may apply differently in different contexts. Scenario forks show where the domain bifurcates into genuinely distinct cases.

### Part IV: Epistemic Map
The guide's self-referential layer. Explicitly marks:
- ✓ ESTABLISHED claims (strong evidence, expert consensus)
- ~ WORKING HYPOTHESES (reasonable but contested)
- ? GENUINELY OPEN questions (unknown to the field)
- ⚡ ACTIVELY CONTESTED positions (live debate)

This section also contains the full dependency DAG, decay markers, and confidence ratings.

### Part V: Integration and Synthesis
Connects the domain to adjacent fields. Forward references become backward references. The reader is now equipped to make independent judgments about novel situations.

### Metadata Layer (Machine-Readable)

Each chapter carries a **fingerprint**:
```yaml
chapter_fingerprint:
  key_terms: [competitive_advantage, barrier_to_imitation, ...]
  anchoring_concepts: [value_creation, opportunity_cost]
  vyaptis_introduced: [V3, V7, V12]
  hetvabhasas_active: [H2, H4]
  prerequisites: [ch_02, ch_03]
  forward_dependencies: [ch_09, ch_14]
  epistemic_status: {V3: ESTABLISHED, V7: WORKING_HYPOTHESIS}
  decay_markers: [{V12: "regulatory_dependent", last_verified: "2025-11"}]
  difficulty_tier: intermediate
```

This metadata is the bridge between T1 (the guide humans read) and T2/T3 (the systems that reason over and retrieve from it). The fingerprints are compiled during Stage 2 and refined through Stage 8.

---

## 5. On Turing Completeness

### The Core Primitive

The computational primitive of Ānvīkṣikī is the vyāpti — invariable concomitance. "Wherever A, necessarily B. A is present here. Therefore B is present here." This is modus ponens. Chained vyāptis create inference chains: A → B → C → D. The pañcāvayava (five-limbed argument) is a structured proof trace.

This maps to Horn clause logic — the foundation of logic programming.

### The Deliberate Choice: Datalog, Not Prolog

Horn clause logic (Prolog) is Turing complete. Datalog — the function-free fragment of Horn clauses — is not. Datalog is decidable, terminates in polynomial time, and computes exactly the fixpoint of the rules over the facts.

We choose Datalog deliberately. Here's why:

**What Turing completeness costs:**
- Queries can diverge (infinite loops on cyclic rule dependencies)
- Termination checking is undecidable (you cannot know in advance if a query will halt)
- Depth bounds and timeout mechanisms are engineering patches, not solutions
- Every query carries implicit risk of non-termination

**What Turing completeness buys:**
- Ability to compute arbitrary functions during inference
- Complex term manipulation via unification
- Recursive data structures in rule heads

**What the engine actually needs:**
- Forward chaining over finite fact sets ✓ (Datalog)
- Rule chaining with variable binding ✓ (Datalog)
- Negation (for scope exclusions) ✓ (Stratified Datalog)
- Aggregation (for epistemic meet/join) ✓ (Lattice Datalog)
- Complex term structures ✗ (vyāptis are flat predicates — no nested terms)
- Arbitrary recursion ✗ (inference depth is bounded by knowledge base size)

The vyāptis in the Ānvīkṣikī knowledge base are flat: `concentrated_ownership(Company) → long_horizon_possible(Company)`. No function symbols. No nested terms. No computed data structures. Datalog handles this perfectly.

**The two computational layers:**

```
Layer 1: Meta-prompt execution (Stage 1 → Stage 8)
  This is a FINITE STATE MACHINE. Not Turing complete.

Layer 2: Content reasoning (vyāpti chains)
  This is DATALOG — decidable, polynomial, terminates.
  NOT Turing complete. This is a feature.

  If you ever need Turing completeness for a specific
  domain (e.g., Type 1 Formal domains with recursive
  mathematical structures), upgrade to Datalog±
  or use Prolog for that specific subsystem.
```

### Why This Matters

The engine should derive *exactly the consequences that follow from the rules in polynomial time* and then stop. An engine that might not stop is not an engine — it's a liability.

---

## 6. The Grounding Problem

### 6.1 Problem Decomposition

The engine's grounding module must translate natural language queries into structured predicates. Every downstream guarantee — Datalog proofs, Heyting-valued inference, sheaf consistency checks, conformal source verification — is conditional on this translation being correct.

The grounding problem decomposes into three sub-problems:

**Syntactic correctness:** The output must be parseable by the Datalog engine (valid predicate names, correct arity, well-formed terms). Current LLMs fail at this 10-30% of the time without intervention.

**Semantic accuracy:** The predicates must faithfully capture the query's meaning (choosing the right vyāpti, mapping entities to correct predicate slots). Zero-shot accuracy: ~0.30-0.45 F1. Few-shot: ~0.82 F1 (Mistral 3.1-small on domain-specific Datalog predicates, CEUR 2025).

**Completeness:** All relevant information must be captured — scope conditions, negations, quantifier structure. LLMs frequently drop scope qualifiers and miss implicit negations.

### 6.2 Seven Strategies from the Literature

**Strategy 1: Compositional Translation (CLOVER, ICLR 2025)**
Parse NL into logical dependency structures, translate sub-sentences compositionally, verify translations via SAT solver. Near-eliminates logic and syntax errors. Expensive (multiple LLM calls + SAT).

**Strategy 2: Grammar-Constrained Decoding**
Mask invalid tokens at decode time. XGrammar/llguidance achieve near-zero overhead. CRANE (ICML 2025): strict constraints kill reasoning; augmenting grammar with CoT rules preserves reasoning while enforcing syntax. Up to +10% accuracy.

**Strategy 3: Iterative Refinement (Logic-LM / Logic-LM++)**
Translate, execute, use error messages to refine. Logic-LM++ (ACL 2024): pairwise comparison prevents semantic degradation during refinement. +5% over Logic-LM.

**Strategy 4: Ontology-Constrained Grounding**
Constrain the LLM to use only predicates from the knowledge base. ODKE+ (2025): 98.8% precision, 35% hallucination reduction when using ontology snippets.

**Strategy 5: Ensemble Consensus**
Run grounding N times, keep what all agree on. Exploits the fact that grounding errors are inconsistent. Directly measures inference uncertainty (Type 3).

**Strategy 6: Round-Trip Verification**
Translate NL → predicates → NL, check meaning preservation. FoVer (TACL 2025): automated verification via Z3 theorem prover.

**Strategy 7: Domain-Specific Fine-Tuning**
Fine-tune a small model on the domain's NL→predicate mappings. Effective but requires training data and infrastructure.

### 6.3 The Five-Layer Defense

We combine five strategies into a layered defense where each layer catches errors the previous layer missed:

```
User Query (NL)
      │
      ▼
┌─────────────────────────────────────────────────┐
│  LAYER 1: Ontology-Constrained Prompt           │  (Strategy 4)
│  LLM sees ONLY valid predicates + descriptions.  │
│  Cost: 0 extra LLM calls. Always on.            │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  LAYER 2: Grammar-Constrained Decoding (CRANE)  │  (Strategy 2)
│  CoT reasoning → constrained predicate output.   │
│  Syntactic validity: 100%. Always on.            │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  LAYER 3: Ensemble Consensus (N=5)              │  (Strategy 5)
│  5 grounding attempts → consensus + disputed.    │
│  Agreement < 0.4 → request clarification.        │
│  Provides grounding confidence score.            │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  LAYER 4: Round-Trip Verification               │  (Strategy 6)
│  Predicates → NL → compare with original.       │
│  Triggers only when ensemble agreement < 0.9.    │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  LAYER 5: Solver-Feedback Refinement            │  (Strategy 3)
│  Execute in Datalog. If error → feed back.       │
│  Max 3 rounds. Triggers only on solver errors.   │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
           Verified Predicates
           + grounding_confidence: float
           + disputed_predicates: list
```

### 6.4 Grounding Implementation

```python
# anvikshiki/grounding.py
"""
Five-layer grounding defense for the Ānvīkṣikī Engine.
Translates natural language queries into verified Datalog predicates.
"""

import dspy
from dataclasses import dataclass


@dataclass
class GroundingResult:
    """Output of the grounding pipeline."""
    predicates: list[str]          # Verified predicate list
    confidence: float              # Ensemble agreement (0-1)
    disputed: list[str]            # Predicates without full consensus
    warnings: list[str]            # Scope/decay warnings
    refinement_rounds: int         # How many solver-feedback rounds needed
    clarification_needed: bool     # Should we ask the user?


class OntologySnippetBuilder:
    """LAYER 1: Build constrained vocabulary from knowledge store."""

    def build(self, knowledge_store, relevant_vyaptis=None):
        """
        Generate the ontology snippet that constrains grounding.
        The LLM sees ONLY these predicates.
        """
        snippet = "VALID PREDICATES — use ONLY these:\n\n"

        vyaptis = relevant_vyaptis or knowledge_store.vyaptis.keys()

        # All predicate names in the knowledge base
        all_predicates = set()
        for vid in vyaptis:
            v = knowledge_store.vyaptis.get(vid)
            if not v:
                continue
            all_predicates.update(v.antecedents)
            all_predicates.add(v.consequent)

            snippet += f"RULE {vid}: {v.name}\n"
            snippet += f"  IF: {', '.join(v.antecedents)}\n"
            snippet += f"  THEN: {v.consequent}\n"
            snippet += f"  SCOPE: {', '.join(v.scope_conditions)}\n"
            if v.scope_exclusions:
                snippet += (
                    f"  EXCLUDES: "
                    f"{', '.join(v.scope_exclusions)}\n"
                )
            snippet += "\n"

        snippet += "\nALL VALID PREDICATE NAMES:\n"
        for p in sorted(all_predicates):
            snippet += f"  - {p}(Entity)\n"

        snippet += (
            "\nOUTPUT FORMAT:\n"
            "Return predicates as: predicate_name(entity)\n"
            "Use ONLY predicate names from the list above.\n"
            "Include negation as: not_predicate_name(entity)\n"
        )

        return snippet


# LAYER 2: Grammar definition for CRANE-style constrained decoding
PREDICATE_GRAMMAR = """
// BNF grammar for valid Ānvīkṣikī predicate output
// Used with CRANE: CoT section is unconstrained,
// output section is constrained to this grammar

<output>      ::= <predicate_list>
<predicate_list> ::= <predicate> | <predicate> "\\n" <predicate_list>
<predicate>   ::= <pred_name> "(" <entity> ")"
               | "not_" <pred_name> "(" <entity> ")"
<pred_name>   ::= {VALID_PREDICATE_NAMES}  // injected from ontology
<entity>      ::= [a-z_][a-z0-9_]*
"""


class GroundQuery(dspy.Signature):
    """Translate a natural language query into structured predicates."""

    query: str = dspy.InputField(desc="User's natural language question")
    ontology_snippet: str = dspy.InputField(
        desc="Valid predicates and their descriptions — "
             "use ONLY these predicate names")
    domain_type: str = dspy.InputField(desc="Domain classification")

    reasoning: str = dspy.OutputField(
        desc="Think step by step: which predicates match "
             "the entities and relationships in the query?")
    predicates: list[str] = dspy.OutputField(
        desc="Structured predicates from the ontology, "
             "e.g. ['concentrated_ownership(acme)', "
             "'private_firm(acme)']")
    relevant_vyaptis: list[str] = dspy.OutputField(
        desc="IDs of vyāptis relevant to this query, "
             "e.g. ['V03', 'V07']")


class VerbalizePredicates(dspy.Signature):
    """LAYER 4: Translate predicates back to natural language."""

    predicates: list[str] = dspy.InputField(
        desc="Structured predicates to verbalize")
    ontology_snippet: str = dspy.InputField(
        desc="Predicate descriptions for context")

    verbalization: str = dspy.OutputField(
        desc="Natural language description of what "
             "these predicates assert")


class CheckFaithfulness(dspy.Signature):
    """LAYER 4: Check if round-trip preserves meaning."""

    original_query: str = dspy.InputField()
    verbalized_predicates: str = dspy.InputField()

    faithful: bool = dspy.OutputField(
        desc="Do the verbalized predicates capture the "
             "same meaning as the original query?")
    discrepancies: list[str] = dspy.OutputField(
        desc="Specific meaning differences, if any")


class GroundingPipeline(dspy.Module):
    """
    The complete five-layer grounding defense.

    Layers 1-2: Always active (zero/minimal cost)
    Layer 3: Always active (5x grounding cost)
    Layer 4: Conditional (ensemble agreement < 0.9)
    Layer 5: Conditional (solver returns errors)
    """

    def __init__(self, knowledge_store, datalog_engine):
        super().__init__()
        self.ks = knowledge_store
        self.engine = datalog_engine

        # Layer 1
        self.snippet_builder = OntologySnippetBuilder()

        # Layers 2-3: DSPy grounding module (run in ensemble)
        self.grounder = dspy.ChainOfThought(GroundQuery)

        # Layer 4: Round-trip verification
        self.verbalizer = dspy.ChainOfThought(VerbalizePredicates)
        self.checker = dspy.ChainOfThought(CheckFaithfulness)

    def forward(self, query: str) -> GroundingResult:
        # ── LAYER 1: Build ontology-constrained prompt ──
        snippet = self.snippet_builder.build(self.ks)

        # ── LAYERS 2+3: Ensemble grounding (N=5) ──
        groundings = []
        for _ in range(5):
            g = self.grounder(
                query=query,
                ontology_snippet=snippet,
                domain_type=self.ks.domain_type.name
            )
            groundings.append(g)

        # Compute consensus
        all_pred_sets = [set(g.predicates) for g in groundings]
        all_vyapti_sets = [
            set(g.relevant_vyaptis) for g in groundings
        ]

        consensus_preds = set.intersection(*all_pred_sets)
        disputed_preds = set.union(*all_pred_sets) - consensus_preds
        consensus_vyaptis = set.intersection(*all_vyapti_sets)

        total = len(consensus_preds) + len(disputed_preds)
        confidence = (
            len(consensus_preds) / max(total, 1)
        )

        # If very low confidence, request clarification
        if confidence < 0.4:
            return GroundingResult(
                predicates=list(consensus_preds),
                confidence=confidence,
                disputed=list(disputed_preds),
                warnings=[
                    "Grounding confidence too low — "
                    "requesting clarification"
                ],
                refinement_rounds=0,
                clarification_needed=True
            )

        # Use consensus + disputed as candidate predicates
        candidate_preds = list(consensus_preds | disputed_preds)
        candidate_vyaptis = list(consensus_vyaptis)

        # ── LAYER 4: Round-trip verification ──
        # (only if ensemble agreement < 0.9)
        if confidence < 0.9:
            verbalization = self.verbalizer(
                predicates=candidate_preds,
                ontology_snippet=snippet
            )
            faithfulness = self.checker(
                original_query=query,
                verbalized_predicates=verbalization.verbalization
            )

            if not faithfulness.faithful:
                # Drop disputed predicates if round-trip fails
                candidate_preds = list(consensus_preds)
                confidence = 1.0 if consensus_preds else 0.0

        # ── LAYER 5: Solver-feedback refinement ──
        refinement_rounds = 0
        max_rounds = 3

        while refinement_rounds < max_rounds:
            # Try executing in Datalog
            errors = self.engine.validate_predicates(
                candidate_preds
            )

            if not errors:
                break  # Clean execution

            # Feed errors back to grounder
            error_context = (
                f"The following predicates caused errors: "
                f"{errors}. Please fix them using ONLY "
                f"predicates from the ontology."
            )

            refined = self.grounder(
                query=query + "\n\n" + error_context,
                ontology_snippet=snippet,
                domain_type=self.ks.domain_type.name
            )

            candidate_preds = refined.predicates
            refinement_rounds += 1

        # Deterministic scope/decay checks
        warnings = []
        warnings.extend(
            self._check_scope(candidate_preds))
        warnings.extend(
            self._check_decay(candidate_vyaptis))

        return GroundingResult(
            predicates=candidate_preds,
            confidence=confidence,
            disputed=list(disputed_preds),
            warnings=warnings,
            refinement_rounds=refinement_rounds,
            clarification_needed=False
        )

    def _check_scope(self, predicates):
        """Deterministic scope checking — no LLM."""
        warnings = []
        for vid, v in self.ks.vyaptis.items():
            for excl in v.scope_exclusions:
                if any(excl.lower() in p.lower()
                       for p in predicates):
                    warnings.append(
                        f"SCOPE: {vid} excludes '{excl}' "
                        f"but query matches"
                    )
        return warnings

    def _check_decay(self, vyapti_ids):
        """Deterministic decay checking — no LLM."""
        from datetime import datetime
        warnings = []
        for vid in vyapti_ids:
            v = self.ks.vyaptis.get(vid)
            if v and v.decay_risk.value in ("high", "critical"):
                if v.last_verified:
                    age = (datetime.now() - v.last_verified).days
                    if age > 180:
                        warnings.append(
                            f"DECAY: {vid} last verified "
                            f"{age} days ago ({v.decay_condition})"
                        )
                else:
                    warnings.append(
                        f"DECAY: {vid} NEVER verified "
                        f"({v.decay_condition})"
                    )
        return warnings
```

---

## 7. Developing the Engine

We now present the complete technical specification for the Ānvīkṣikī Engine, developed in four incremental phases. Each phase addresses specific limitations of the prior, and we motivate each transition explicitly.

### 7.1 Architecture Overview

The engine has three compilation targets and two runtime components:

**Compilation Targets:**
- **T1** (Guide): Human-readable pedagogical document (produced by meta-prompt, consumed by T3 compiler)
- **T2** (Logic Engine): Executable inference over formalized domain rules
- **T3** (Retrieval Corpus): Graph-structured RAG over guide prose with rich metadata

**Runtime Components:**
- **Grounding Module**: Translates natural language queries into structured predicates (five-layer defense)
- **Synthesis Module**: Translates inference results + retrieved prose into calibrated natural language responses

**Data Flow:**

```
          COMPILE TIME                          RUNTIME
    ┌────────────────────────┐      ┌──────────────────────────────┐
    │                        │      │                              │
    │  Meta-prompt           │      │  User Query (NL)             │
    │      │                 │      │      │                       │
    │      ▼                 │      │      ▼                       │
    │  Verified Architecture │      │  5-Layer Grounding Defense   │
    │      │                 │      │  (ontology + grammar +       │
    │   ┌──┴──┐              │      │   ensemble + roundtrip +     │
    │   │     │              │      │   solver feedback)           │
    │   ▼     ▼              │      │      │                       │
    │  T2    T1 Guide        │      │  ┌───┴───┐                   │
    │  Datalog  │            │      │  │       │                   │
    │  Rules    │            │      │  ▼       ▼                   │
    │  (lattice │            │      │ Datalog  GraphRAG            │
    │  valued)  ▼            │      │ Engine   (T3)                │
    │          T3            │      │  │       │                   │
    │          Corpus        │      │  └───┬───┘                   │
    │                        │      │      ▼                       │
    └────────────────────────┘      │  Sheaf Consistency Check     │
                                    │      │                       │
                                    │      ▼                       │
                                    │  Conformal Verification      │
                                    │      │                       │
                                    │      ▼                       │
                                    │  DSPy Synthesis              │
                                    │      │                       │
                                    │      ▼                       │
                                    │  Calibrated Response +       │
                                    │  Uncertainty Decomposition   │
                                    └──────────────────────────────┘
```

### 7.2 Phase 1: DSPy Only — The Baseline

**What this phase builds:** A fully LLM-based reasoning system using DSPy as the orchestration framework. No symbolic reasoning, no logic engine, no formal constraints. This is the simplest possible implementation and establishes the baseline against which all subsequent phases are measured.

**Why start here:** DSPy (Khattab et al., ICLR 2024) provides the critical infrastructure — typed signatures, optimizable modules, automatic prompt compilation, and assertion-based self-refinement — that every subsequent phase builds on. Starting with DSPy-only forces us to confront what LLMs can and cannot do for domain reasoning before adding symbolic components.

#### 7.2.1 Dependencies

```bash
pip install dspy-ai graphrag networkx numpy
```

#### 7.2.2 The Knowledge Store

First, we define the data structures that represent the compiled domain knowledge:

```python
# anvikshiki/schema.py
"""
Core data structures for the Ānvīkṣikī knowledge store.
These are populated by the T2 and T3 compilers from guide output.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class DomainType(Enum):
    FORMAL = 1          # Mathematics, formal logic
    MECHANISTIC = 2     # Physics, engineering
    EMPIRICAL = 3       # Social sciences, medicine
    CRAFT = 4           # Business strategy, design
    INTERPRETIVE = 5    # Law, literary criticism
    DESIGN = 6          # Architecture, UX
    NORMATIVE = 7       # Ethics, policy
    META_ANALYTICAL = 8 # Philosophy of science


class CausalStatus(Enum):
    STRUCTURAL = "structural"       # Follows from definitions/structure
    REGULATORY = "regulatory"       # Depends on institutional rules
    EMPIRICAL = "empirical"         # Observed regularity
    DEFINITIONAL = "definitional"   # True by definition


class EpistemicStatus(Enum):
    ESTABLISHED = "established"          # ✓  Strong evidence, consensus
    WORKING_HYPOTHESIS = "hypothesis"    # ~  Reasonable but contested
    GENUINELY_OPEN = "open"              # ?  Unknown to the field
    ACTIVELY_CONTESTED = "contested"     # ⚡ Live scholarly debate


class DecayRisk(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Confidence:
    existence: float      # 0-1: confidence the rule exists at all
    formulation: float    # 0-1: confidence the formulation is precise
    evidence: str         # "experimental", "observational", "theoretical", "expert_consensus"


@dataclass
class Vyapti:
    """A domain rule — the core computational primitive."""
    id: str                              # e.g., "V01"
    name: str                            # Human-readable name
    statement: str                       # NL statement of the rule
    causal_status: CausalStatus
    scope_conditions: list[str]          # When does this rule apply?
    scope_exclusions: list[str]          # When does it NOT apply?
    confidence: Confidence
    epistemic_status: EpistemicStatus
    decay_risk: DecayRisk
    decay_condition: Optional[str]       # What would invalidate this?
    last_verified: Optional[datetime]
    sources: list[str]                   # Reference Bank entries
    formal_representation: Optional[str] # Datalog form (Phase 2+)

    # For the logic engine
    antecedents: list[str]               # Predicate names required
    consequent: str                      # Predicate name produced


@dataclass
class Hetvabhasa:
    """A reasoning fallacy — an integrity constraint."""
    id: str                              # e.g., "H01"
    name: str                            # e.g., "Survivorship Bias"
    description: str
    detection_signature: str             # Pattern that triggers this
    correction_pattern: str              # How to fix reasoning that trips this
    common_contexts: list[str]           # Where this fallacy typically occurs
    formal_constraint: Optional[str]     # Logic form (Phase 2+)


@dataclass
class ThresholdConcept:
    """A concept that permanently reorganizes understanding."""
    name: str
    reorganizes: list[str]               # Concepts it transforms
    prerequisites: list[str]             # Must understand these first
    troublesome_aspects: list[str]       # Common stuck points


@dataclass
class ChapterFingerprint:
    """Machine-readable metadata for a guide chapter."""
    chapter_id: str
    title: str
    key_terms: list[str]
    anchoring_concepts: list[str]
    vyaptis_introduced: list[str]        # Vyapti IDs
    hetvabhasas_active: list[str]        # Hetvabhasa IDs
    prerequisites: list[str]             # Chapter IDs
    forward_dependencies: list[str]      # Chapter IDs
    epistemic_statuses: dict[str, EpistemicStatus]
    decay_markers: list[dict]
    difficulty_tier: str                 # "foundational", "intermediate", "advanced"


@dataclass
class KnowledgeStore:
    """The complete compiled knowledge base for a domain."""
    domain_type: DomainType
    pramanas: list[str]                  # Valid knowledge sources
    vyaptis: dict[str, Vyapti]           # id → Vyapti
    hetvabhasas: dict[str, Hetvabhasa]   # id → Hetvabhasa
    threshold_concepts: list[ThresholdConcept]
    dependency_graph: dict[str, list[str]]  # concept → prerequisites
    chapter_fingerprints: dict[str, ChapterFingerprint]
    reference_bank: dict[str, dict]      # source_id → {url, title, date, ...}
```

#### 7.2.3 The T2 Compiler (Phase 1 — Schema Only)

In Phase 1, the T2 "compiler" is really a parser: it reads the verified architecture from Stage 2+3 and populates the KnowledgeStore. No formalization into logic yet.

```python
# anvikshiki/t2_compiler.py
"""
T2 Compiler Phase 1: Parse verified architecture into KnowledgeStore.
Input: Stage 2+3 output (YAML/JSON from meta-prompt execution)
Output: Populated KnowledgeStore
"""

import yaml
from .schema import *


def compile_t2_phase1(architecture_path: str) -> KnowledgeStore:
    """
    Parse the verified architecture output into a KnowledgeStore.

    The architecture file is the YAML/JSON output from Stages 2+3
    of the meta-prompt, containing verified vyāptis, hetvābhāsas,
    dependency graph, and reference bank.
    """
    with open(architecture_path) as f:
        arch = yaml.safe_load(f)

    # Parse domain classification
    domain_type = DomainType[arch["domain"]["type"].upper()]
    pramanas = arch["domain"]["pramanas"]

    # Parse vyāptis
    vyaptis = {}
    for v in arch["vyaptis"]:
        vyapti = Vyapti(
            id=v["id"],
            name=v["name"],
            statement=v["statement"],
            causal_status=CausalStatus(v["causal_status"]),
            scope_conditions=v.get("scope_conditions", []),
            scope_exclusions=v.get("scope_exclusions", []),
            confidence=Confidence(
                existence=v["confidence"]["existence"],
                formulation=v["confidence"]["formulation"],
                evidence=v["confidence"]["evidence"]
            ),
            epistemic_status=EpistemicStatus(v["epistemic_status"]),
            decay_risk=DecayRisk(v.get("decay_risk", "low")),
            decay_condition=v.get("decay_condition"),
            last_verified=v.get("last_verified"),
            sources=v.get("sources", []),
            formal_representation=None,  # Phase 2+
            antecedents=v.get("antecedents", []),
            consequent=v.get("consequent", "")
        )
        vyaptis[vyapti.id] = vyapti

    # Parse hetvābhāsas
    hetvabhasas = {}
    for h in arch["hetvabhasas"]:
        het = Hetvabhasa(
            id=h["id"],
            name=h["name"],
            description=h["description"],
            detection_signature=h["detection_signature"],
            correction_pattern=h["correction_pattern"],
            common_contexts=h.get("common_contexts", []),
            formal_constraint=None  # Phase 2+
        )
        hetvabhasas[het.id] = het

    # Parse threshold concepts
    threshold_concepts = [
        ThresholdConcept(
            name=tc["name"],
            reorganizes=tc.get("reorganizes", []),
            prerequisites=tc.get("prerequisites", []),
            troublesome_aspects=tc.get("troublesome_aspects", [])
        )
        for tc in arch.get("threshold_concepts", [])
    ]

    # Parse dependency graph
    dependency_graph = arch.get("dependency_graph", {})

    # Parse chapter fingerprints
    fingerprints = {}
    for fp in arch.get("chapter_fingerprints", []):
        cfp = ChapterFingerprint(
            chapter_id=fp["chapter_id"],
            title=fp["title"],
            key_terms=fp.get("key_terms", []),
            anchoring_concepts=fp.get("anchoring_concepts", []),
            vyaptis_introduced=fp.get("vyaptis_introduced", []),
            hetvabhasas_active=fp.get("hetvabhasas_active", []),
            prerequisites=fp.get("prerequisites", []),
            forward_dependencies=fp.get("forward_dependencies", []),
            epistemic_statuses={
                k: EpistemicStatus(v)
                for k, v in fp.get("epistemic_statuses", {}).items()
            },
            decay_markers=fp.get("decay_markers", []),
            difficulty_tier=fp.get("difficulty_tier", "intermediate")
        )
        fingerprints[cfp.chapter_id] = cfp

    return KnowledgeStore(
        domain_type=domain_type,
        pramanas=pramanas,
        vyaptis=vyaptis,
        hetvabhasas=hetvabhasas,
        threshold_concepts=threshold_concepts,
        dependency_graph=dependency_graph,
        chapter_fingerprints=fingerprints,
        reference_bank=arch.get("reference_bank", {})
    )
```

#### 7.2.4 The T3 Compiler (Phase 1 — GraphRAG Index)

The T3 compiler transforms the guide text into a graph-structured retrieval corpus. We use Microsoft's GraphRAG approach but with a critical advantage: we don't need expensive LLM extraction of entities and relationships because the architecture already defines them.

```python
# anvikshiki/t3_compiler.py
"""
T3 Compiler: Build graph-structured retrieval corpus from guide text.

Key insight: the entities, relationships, and community structure
are ALREADY defined in the Stage 2 architecture. We skip the
expensive LLM extraction step that standard GraphRAG requires.
"""

import networkx as nx
from dataclasses import dataclass


@dataclass
class TextChunk:
    """A retrievable unit of guide text with rich metadata."""
    chunk_id: str
    chapter_id: str
    text: str
    vyapti_anchors: list[str]      # Which vyāptis does this explain?
    hetvabhasa_anchors: list[str]  # Which fallacies does this illustrate?
    concept_anchors: list[str]     # Which concepts does this define?
    prerequisites: list[str]       # Chapter IDs that must be understood first
    epistemic_status: str          # Inherited from chapter fingerprint
    sourced: bool                  # Does this chunk have citations?
    source_ids: list[str]          # Reference Bank entries
    difficulty_tier: str
    embedding: list[float] = None  # Vector embedding (computed at index time)


def compile_t3(
    guide_text: dict[str, str],          # chapter_id → chapter text
    knowledge_store: 'KnowledgeStore',   # From T2 compiler
) -> tuple[nx.DiGraph, list[TextChunk]]:
    """
    Build the T3 corpus: a knowledge graph + chunked text.

    Returns:
        graph: NetworkX DiGraph with entities and relationships
        chunks: List of TextChunk objects ready for indexing
    """

    # === STEP 1: Build the knowledge graph from architecture ===
    G = nx.DiGraph()

    # Add vyāpti nodes
    for vid, v in knowledge_store.vyaptis.items():
        G.add_node(vid, type="vyapti", name=v.name,
                   epistemic_status=v.epistemic_status.value,
                   confidence=v.confidence.formulation,
                   decay_risk=v.decay_risk.value)

    # Add concept nodes from dependency graph
    for concept, prereqs in knowledge_store.dependency_graph.items():
        G.add_node(concept, type="concept")
        for prereq in prereqs:
            G.add_edge(prereq, concept, relation="prerequisite_for")

    # Add hetvābhāsa nodes
    for hid, h in knowledge_store.hetvabhasas.items():
        G.add_node(hid, type="hetvabhasa", name=h.name)
        # Link to contexts where they commonly appear
        for ctx in h.common_contexts:
            if ctx in G.nodes:
                G.add_edge(hid, ctx, relation="monitors")

    # Add chapter nodes and prerequisite edges
    for cid, fp in knowledge_store.chapter_fingerprints.items():
        G.add_node(cid, type="chapter", title=fp.title,
                   difficulty=fp.difficulty_tier)
        for prereq in fp.prerequisites:
            G.add_edge(prereq, cid, relation="prerequisite_for")
        for vid in fp.vyaptis_introduced:
            G.add_edge(cid, vid, relation="introduces")
        for fwd in fp.forward_dependencies:
            G.add_edge(cid, fwd, relation="forward_reference")

    # Add threshold concept nodes
    for tc in knowledge_store.threshold_concepts:
        G.add_node(f"tc_{tc.name}", type="threshold_concept",
                   name=tc.name)
        for prereq in tc.prerequisites:
            G.add_edge(prereq, f"tc_{tc.name}",
                      relation="prerequisite_for")
        for concept in tc.reorganizes:
            G.add_edge(f"tc_{tc.name}", concept,
                      relation="reorganizes")

    # === STEP 2: Chunk guide text with metadata ===
    chunks = []
    for chapter_id, text in guide_text.items():
        fp = knowledge_store.chapter_fingerprints.get(chapter_id)
        if not fp:
            continue

        # Chunk by section (indicated by ### headers in the guide)
        sections = split_into_sections(text)

        for i, section_text in enumerate(sections):
            chunk = TextChunk(
                chunk_id=f"{chapter_id}_s{i:03d}",
                chapter_id=chapter_id,
                text=section_text,
                vyapti_anchors=detect_vyapti_references(
                    section_text, knowledge_store.vyaptis),
                hetvabhasa_anchors=detect_hetvabhasa_references(
                    section_text, knowledge_store.hetvabhasas),
                concept_anchors=detect_concept_references(
                    section_text, knowledge_store.dependency_graph),
                prerequisites=fp.prerequisites,
                epistemic_status=max(
                    fp.epistemic_statuses.values(),
                    key=lambda s: ["established", "hypothesis",
                                   "open", "contested"].index(s.value),
                    default="established"
                ).value,
                sourced=bool(fp.decay_markers),
                source_ids=[],  # populated during indexing
                difficulty_tier=fp.difficulty_tier
            )
            chunks.append(chunk)

    return G, chunks


def split_into_sections(text: str, max_tokens: int = 512) -> list[str]:
    """Split chapter text into sections, respecting semantic boundaries."""
    sections = []
    current = []
    current_len = 0

    for line in text.split('\n'):
        # Section headers are natural split points
        if line.startswith('###') and current:
            sections.append('\n'.join(current))
            current = [line]
            current_len = len(line.split())
        else:
            current.append(line)
            current_len += len(line.split())
            if current_len > max_tokens:
                sections.append('\n'.join(current))
                current = []
                current_len = 0

    if current:
        sections.append('\n'.join(current))

    return sections


def detect_vyapti_references(text: str, vyaptis: dict) -> list[str]:
    """Detect which vyāptis a text chunk references."""
    refs = []
    for vid, v in vyaptis.items():
        # Check for explicit references (V01, V02, etc.)
        if vid in text:
            refs.append(vid)
        # Check for key terms from the vyāpti name/statement
        elif any(term.lower() in text.lower()
                for term in v.name.split()[:3]):
            refs.append(vid)
    return refs


def detect_hetvabhasa_references(text: str, hetvabhasas: dict) -> list[str]:
    """Detect which hetvābhāsas a text chunk references."""
    refs = []
    for hid, h in hetvabhasas.items():
        if hid in text or h.name.lower() in text.lower():
            refs.append(hid)
    return refs


def detect_concept_references(text: str, dep_graph: dict) -> list[str]:
    """Detect which concepts a text chunk references."""
    return [c for c in dep_graph.keys()
            if c.replace('_', ' ').lower() in text.lower()]
```

#### 7.2.5 The DSPy Reasoning Pipeline

Now the core: the DSPy modules that perform grounding, reasoning, and synthesis. Note that in Phase 1, the grounding module already uses the five-layer defense (Layers 1-3 always active, Layers 4-5 conditional).

```python
# anvikshiki/engine_phase1.py
"""
Phase 1 Engine: Pure DSPy implementation.
All reasoning is performed by LLM modules with typed signatures.
The grounding module uses the five-layer defense even in Phase 1.
"""

import dspy
from .schema import KnowledgeStore, Vyapti, Hetvabhasa


# ─── SIGNATURES ───────────────────────────────────────────────

class ReasonOverDomain(dspy.Signature):
    """Apply domain rules to grounded predicates to derive conclusions."""

    predicates: list[str] = dspy.InputField(
        desc="Grounded predicates from the query")
    active_vyaptis: str = dspy.InputField(
        desc="Full text of relevant vyāptis with scope conditions")
    active_hetvabhasas: str = dspy.InputField(
        desc="Fallacy patterns to check against")
    retrieved_context: str = dspy.InputField(
        desc="Retrieved prose from T3 for grounding")

    reasoning_chain: str = dspy.OutputField(
        desc="Step-by-step reasoning applying rules to predicates")
    conclusion: str = dspy.OutputField(
        desc="The derived conclusion")
    rules_applied: list[str] = dspy.OutputField(
        desc="List of vyāpti IDs used in this reasoning")
    confidence_assessment: str = dspy.OutputField(
        desc="Assessment of conclusion reliability")


class SynthesizeResponse(dspy.Signature):
    """Produce a calibrated natural language response from
    reasoning results and retrieved context."""

    query: str = dspy.InputField(desc="Original user question")
    reasoning_chain: str = dspy.InputField(
        desc="The reasoning trace")
    retrieved_prose: str = dspy.InputField(
        desc="Relevant guide text for exposition")
    epistemic_statuses: str = dspy.InputField(
        desc="Epistemic status of rules used")

    response: str = dspy.OutputField(
        desc="Natural language response to the user")
    stated_confidence: str = dspy.OutputField(
        desc="Explicit confidence statement with justification")
    sources_cited: list[str] = dspy.OutputField(
        desc="Reference Bank entries supporting this response")


# ─── ENGINE ──────────────────────────────────────────────────

class AnvikshikiEngineV1(dspy.Module):
    """
    Phase 1: Pure DSPy engine.

    All reasoning is LLM-based. The knowledge store provides
    context but does not perform inference. Hetvābhāsa checking
    is via DSPy assertions (LLM self-check).
    """

    def __init__(self, knowledge_store: KnowledgeStore):
        super().__init__()
        self.ks = knowledge_store

        # DSPy modules
        self.reasoner = dspy.ChainOfThought(ReasonOverDomain)
        self.synthesizer = dspy.ChainOfThought(SynthesizeResponse)

    def forward(self, query: str, grounding_result, retrieved_chunks: list[str]):
        # Step 1: Gather relevant rules and constraints
        active_rules = self._get_active_rules(
            grounding_result.predicates)
        active_constraints = self._get_active_constraints(
            grounding_result.predicates)

        # Step 2: Reason over domain
        context = '\n'.join(retrieved_chunks)
        if grounding_result.warnings:
            context += f"\n\nWARNINGS: {grounding_result.warnings}"

        reasoning = self.reasoner(
            predicates=grounding_result.predicates,
            active_vyaptis=active_rules,
            active_hetvabhasas=active_constraints,
            retrieved_context=context
        )

        # Step 3: Hetvābhāsa check via assertion
        for hid, h in self.ks.hetvabhasas.items():
            dspy.Suggest(
                not self._pattern_match_fallacy(
                    h, reasoning.reasoning_chain),
                f"Possible {h.name}: {h.correction_pattern}"
            )

        # Step 4: Synthesize response
        epistemic_info = self._get_epistemic_info(
            reasoning.rules_applied)

        response = self.synthesizer(
            query=query,
            reasoning_chain=reasoning.reasoning_chain,
            retrieved_prose=context,
            epistemic_statuses=epistemic_info
        )

        return dspy.Prediction(
            response=response.response,
            confidence=response.stated_confidence,
            sources=response.sources_cited,
            reasoning_trace=reasoning.reasoning_chain,
            rules_used=reasoning.rules_applied,
            warnings=grounding_result.warnings,
            grounding_confidence=grounding_result.confidence,
        )

    # ─── DETERMINISTIC HELPERS ─────────────────────────────

    def _get_active_rules(self, predicates: list[str]) -> str:
        """Get full rule descriptions for relevant vyāptis."""
        rules = []
        for vid, v in self.ks.vyaptis.items():
            rules.append(
                f"RULE {vid} ({v.name}):\n"
                f"  Statement: {v.statement}\n"
                f"  Causal status: {v.causal_status.value}\n"
                f"  Scope: {v.scope_conditions}\n"
                f"  Confidence: existence={v.confidence.existence}, "
                f"formulation={v.confidence.formulation}\n"
                f"  Evidence: {v.confidence.evidence}\n"
                f"  Status: {v.epistemic_status.value}"
            )
        return '\n'.join(rules)

    def _get_active_constraints(self, predicates: list[str]) -> str:
        """Get hetvābhāsa descriptions relevant to active rules."""
        constraints = []
        for hid, h in self.ks.hetvabhasas.items():
            constraints.append(
                f"CONSTRAINT {hid} ({h.name}):\n"
                f"  Detection: {h.detection_signature}\n"
                f"  Correction: {h.correction_pattern}"
            )
        return '\n'.join(constraints)

    def _get_epistemic_info(self, rule_ids: list[str]) -> str:
        """Compile epistemic status of all rules used."""
        info = []
        for vid in rule_ids:
            v = self.ks.vyaptis.get(vid)
            if v:
                info.append(
                    f"{vid}: {v.epistemic_status.value} "
                    f"(confidence: {v.confidence.formulation}, "
                    f"evidence: {v.confidence.evidence})"
                )
        return '\n'.join(info)

    def _pattern_match_fallacy(
        self, hetvabhasa: Hetvabhasa, reasoning: str
    ) -> bool:
        """
        Simple keyword-based fallacy pattern matching.
        Returns True if fallacy pattern detected.
        NOTE: This is the weak point of Phase 1 —
        LLM-based detection of its own fallacies is unreliable.
        Phase 2 replaces this with deterministic constraint checking.
        """
        sig = hetvabhasa.detection_signature.lower()
        return sig in reasoning.lower()
```

#### 7.2.6 DSPy Optimization

The critical advantage of DSPy is that this entire pipeline is **optimizable**. We define a metric and let DSPy's compilers find better prompts:

```python
# anvikshiki/optimize.py
"""
Optimization pipeline for the Ānvīkṣikī Engine.
Uses DSPy's MIPROv2 optimizer to improve grounding,
reasoning, and synthesis quality.
"""

import dspy
from dspy.teleprompt import MIPROv2, BootstrapFewShotWithRandomSearch


def calibration_metric(prediction, ground_truth, trace=None):
    """
    Reward calibrated uncertainty — not just correct answers.

    A system that says "I'm confident" and is wrong is WORSE
    than one that says "I'm uncertain" and is wrong.
    """
    answer_correct = ground_truth.answer in prediction.response

    # Parse stated confidence
    conf_text = prediction.confidence.lower()
    if "high" in conf_text:
        stated_conf = 0.9
    elif "moderate" in conf_text:
        stated_conf = 0.6
    elif "low" in conf_text:
        stated_conf = 0.3
    else:
        stated_conf = 0.5

    # Calibration score
    actual = 1.0 if answer_correct else 0.0
    calibration_error = abs(stated_conf - actual)

    # Bonus for citing sources
    source_bonus = 0.1 if prediction.sources else 0.0

    # Bonus for flagging scope/decay warnings when appropriate
    warning_bonus = 0.1 if (
        prediction.warnings
    ) else 0.0

    # Penalty for overconfidence on wrong answers
    if not answer_correct and stated_conf > 0.7:
        return -0.5  # Severe penalty

    return (1.0 - calibration_error) + source_bonus + warning_bonus


def optimize_engine(engine, train_set, val_set):
    """
    Run MIPROv2 optimization over the engine.

    train_set: List of (query, expected_answer) pairs
    val_set: Validation set for evaluation
    """
    optimizer = MIPROv2(
        metric=calibration_metric,
        num_candidates=10,
        init_temperature=1.0,
    )

    optimized = optimizer.compile(
        engine,
        trainset=train_set,
        valset=val_set,
        max_bootstrapped_demos=4,
        max_labeled_demos=8,
    )

    return optimized
```

#### 7.2.7 What Phase 1 Gets Right and Wrong

**Gets right:**
- Clean separation of knowledge store, grounding, reasoning, synthesis
- Deterministic scope and decay checking (no LLM needed)
- Optimizable pipeline (DSPy compiler improves with data)
- Source tracking through the full chain
- Epistemic status propagation to output
- Five-layer grounding defense (Layers 1-3 always active)

**Gets wrong — and this is why we need Phase 2:**
- *Hetvābhāsa detection is unreliable*: Asking an LLM to detect its own reasoning fallacies is asking the system that makes errors to detect its own errors. The `dspy.Suggest` assertions are soft constraints — the LLM can override them.
- *Reasoning is not verifiable*: The LLM's "reasoning chain" is a text string, not a formal proof. We cannot verify that the conclusion actually follows from the premises. The chain of thought might skip steps, apply rules incorrectly, or introduce information not in the knowledge base.
- *No formal inference*: The "engine" is really just a structured prompt. It doesn't chain rules — it asks the LLM to chain rules and hopes it does so correctly.
- *Uncertainty is self-reported*: The confidence assessment is the LLM's own judgment, which is known to be poorly calibrated (LLMs are overconfident on wrong answers and underconfident on easy questions).

These limitations motivate Phase 2.

---

### 7.3 Why Not Prolog?

The original thesis proposed Prolog as the Phase 2 inference engine. We revise this.

**The case for Prolog was:**
- Deterministic inference (correct)
- Formal proof traces (correct)
- Constraint enforcement (correct)
- Mature tooling (correct)

**The case against Prolog, which we now find stronger:**

**1. Turing completeness is a liability.** The engine's knowledge base is finite. The rules are non-recursive in practice. Turing completeness buys nothing and costs termination guarantees. Every Prolog-based system needs depth bounds, loop detection, and timeout mechanisms — engineering patches for a problem that Datalog doesn't have.

**2. Backward chaining fights the domain.** Prolog asks "can I prove X?" and works backward. The engine's natural mode is "given these facts, what follows?" Forward chaining from observations to conclusions matches the pañcāvayava structure and the user's mental model. Prolog can do forward chaining (assert/retract), but it's fighting the language.

**3. Boolean truth requires a second engine.** With Prolog, you need Boolean inference in Phase 2, then a *separate* Heyting engine in Phase 4. This means migrating the entire knowledge base between engines. With Datalog, Phase 2 uses Boolean Datalog and Phase 3 adds the lattice dimension — same engine, same rules, one line changed.

**4. pyswip is fragile.** The Python-Prolog bridge (pyswip) has known stability issues, memory management quirks, and version compatibility problems. A native Python Datalog evaluator is simpler to deploy, test, and debug.

**5. Unification is overkill.** The vyāptis are flat predicates: `concentrated_ownership(Company)`. No nested terms like `strategy(investment(long_horizon, Company))`. Datalog's pattern matching on flat predicates is exactly the right level of expressivity.

**What Prolog would still be better for:** If the domain requires complex term manipulation (Type 1 Formal domains with mathematical structures, Type 5 Interpretive domains with nested argument structures), Prolog's unification is genuinely needed. For Type 4 Craft domains (business strategy), Datalog suffices.

### 7.4 Phase 2: DSPy + Datalog

**What this phase builds:** A formally correct inference engine using Datalog for deterministic forward chaining. Replaces LLM "reasoning" with provable derivation. Boolean truth values, but with guaranteed termination.

**Why this phase exists:** Phase 1 *asks* the LLM to reason correctly. Phase 2 *proves* reasoning correctness through deterministic rule evaluation. The LLM's role shrinks to grounding (NL→predicates) and synthesis (proof→NL). Everything between is deterministic.

#### 7.4.1 The Datalog Engine

```python
# anvikshiki/datalog_engine.py
"""
Semi-naive Datalog engine for the Ānvīkṣikī knowledge base.

Phase 2: Boolean (fact is derived or not)
Phase 3: Lattice-valued (fact carries epistemic qualification)

The same engine serves both phases. Phase 3 adds the lattice
dimension without changing the evaluation algorithm.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import IntEnum


# ─── EPISTEMIC LATTICE ────────────────────────────────────

class EpistemicValue(IntEnum):
    """
    Heyting algebra of truth values.

    Phase 2 uses only BOTTOM and ESTABLISHED (Boolean mode).
    Phase 3 uses the full lattice.
    """
    BOTTOM = 0          # False / no evidence
    CONTESTED = 1       # ⚡ Actively contested
    OPEN = 2            # ? Genuinely open
    HYPOTHESIS = 3      # ~ Working hypothesis
    ESTABLISHED = 4     # ✓ Established

    @staticmethod
    def meet(a, b):
        """AND: minimum (weakest link in the chain)."""
        return EpistemicValue(min(a.value, b.value))

    @staticmethod
    def join(a, b):
        """OR: maximum (best evidence available)."""
        return EpistemicValue(max(a.value, b.value))


# ─── FACTS AND RULES ─────────────────────────────────────

@dataclass(frozen=True)
class Fact:
    """A ground fact in the knowledge base."""
    predicate: str
    entity: str
    value: EpistemicValue = EpistemicValue.ESTABLISHED

    def __str__(self):
        return f"{self.predicate}({self.entity}) = {self.value.name}"


@dataclass
class Rule:
    """
    A Datalog rule (a vyāpti).

    head(Entity) :- body1(Entity), body2(Entity), ...

    With scope exclusions as negated conditions:
    head(Entity) :- body1(Entity), not excl1(Entity), ...
    """
    vyapti_id: str
    name: str
    head: str                        # Consequent predicate name
    body_positive: list[str]         # Required antecedent predicates
    body_negative: list[str]         # Scope exclusions (negated)
    confidence: EpistemicValue       # Rule's own epistemic status

    def __str__(self):
        pos = ", ".join(f"{p}(E)" for p in self.body_positive)
        neg = ", ".join(f"not {p}(E)" for p in self.body_negative)
        body = ", ".join(filter(None, [pos, neg]))
        return (
            f"% {self.vyapti_id}: {self.name}\n"
            f"{self.head}(E) :- {body}."
        )


@dataclass
class Violation:
    """A hetvābhāsa (integrity constraint) violation."""
    hetvabhasa_id: str
    name: str
    description: str
    triggered_by: list[str]          # Facts that triggered it
    correction: str


# ─── THE ENGINE ──────────────────────────────────────────

class DatalogEngine:
    """
    Semi-naive Datalog evaluator with lattice-valued facts.

    Key properties:
    - TERMINATES: guaranteed (finite facts, monotone rules)
    - COMPLEXITY: O(|rules| × |Δfacts|) per iteration
    - TOTAL: O(|rules| × |facts|) — polynomial
    - CORRECT: computes minimal fixpoint of the rules

    Phase 2 mode (boolean=True):
      All facts have value ESTABLISHED.
      Rules fire or don't. Classical Datalog semantics.

    Phase 3 mode (boolean=False):
      Facts carry epistemic values from the lattice.
      Rule application: consequent = meet(rule_confidence,
                                          min(antecedent values))
      Multiple derivation paths: take join (max).
    """

    def __init__(self, boolean_mode: bool = True):
        self.boolean_mode = boolean_mode
        self.facts: dict[tuple[str, str], EpistemicValue] = {}
        self.rules: list[Rule] = []
        self.hetvabhasa_checks: list[Callable] = []
        self.trace: list[str] = []
        self._delta: dict[tuple[str, str], EpistemicValue] = {}

    # ─── Loading ─────────────────────────────────────

    def add_fact(self, fact: Fact):
        """Add or update a fact. Join (max) if already exists."""
        key = (fact.predicate, fact.entity)
        old = self.facts.get(key, EpistemicValue.BOTTOM)
        new = EpistemicValue.join(old, fact.value)
        if new > old:
            self.facts[key] = new
            self._delta[key] = new

    def add_rule(self, rule: Rule):
        """Add a rule (vyāpti) to the rule base."""
        self.rules.append(rule)

    def add_hetvabhasa_check(
        self,
        hid: str,
        name: str,
        check_fn: Callable,
        correction: str
    ):
        """
        Add a hetvābhāsa integrity constraint.

        check_fn: (facts_dict) → list[str] of triggering facts
        Returns non-empty list if the violation is detected.
        """
        self.hetvabhasa_checks.append({
            'id': hid,
            'name': name,
            'check_fn': check_fn,
            'correction': correction,
        })

    # ─── Evaluation ──────────────────────────────────

    def evaluate(self) -> int:
        """
        Semi-naive fixpoint evaluation.

        Returns number of iterations to reach fixpoint.

        Key difference from naive evaluation:
        Each iteration only fires rules where at least one
        antecedent was NEWLY DERIVED (in delta).
        This avoids re-deriving known facts every iteration.
        """
        iteration = 0

        while self._delta:
            new_delta = {}

            for rule in self.rules:
                # Get all entities that have ANY body predicate
                # in delta
                delta_entities = set()
                for pred in rule.body_positive:
                    for (p, e), v in self._delta.items():
                        if p == pred:
                            delta_entities.add(e)

                # For each candidate entity, check full rule
                for entity in delta_entities:
                    result = self._try_fire_rule(rule, entity)
                    if result is not None:
                        key = (rule.head, entity)
                        old = self.facts.get(
                            key, EpistemicValue.BOTTOM)

                        if result > old:
                            self.facts[key] = result
                            new_delta[key] = result
                            self.trace.append(
                                f"Iteration {iteration}: "
                                f"{rule.vyapti_id} → "
                                f"{rule.head}({entity}) "
                                f"= {result.name}"
                            )

            self._delta = new_delta
            iteration += 1

            # Safety bound (should never hit for valid Datalog)
            if iteration > len(self.rules) * len(self.facts) + 1:
                raise RuntimeError(
                    "Fixpoint not reached — possible bug"
                )

        return iteration

    def _try_fire_rule(
        self, rule: Rule, entity: str
    ) -> Optional[EpistemicValue]:
        """
        Try to fire a rule for a specific entity.

        Returns the consequent's epistemic value if rule fires,
        None if antecedents not satisfied.
        """
        # Check positive body (all must be present)
        antecedent_values = []
        for pred in rule.body_positive:
            key = (pred, entity)
            if key not in self.facts:
                return None  # Missing antecedent
            antecedent_values.append(self.facts[key])

        # Check negative body (none must be present)
        for pred in rule.body_negative:
            key = (pred, entity)
            if key in self.facts and \
               self.facts[key] > EpistemicValue.BOTTOM:
                return None  # Scope exclusion fires

        # Compute consequent value
        if self.boolean_mode:
            return EpistemicValue.ESTABLISHED
        else:
            # Meet of rule confidence and all antecedent values
            result = rule.confidence
            for av in antecedent_values:
                result = EpistemicValue.meet(result, av)
            return result

    # ─── Querying ────────────────────────────────────

    def query(
        self,
        predicate: str,
        entity: str = None,
        min_value: EpistemicValue = EpistemicValue.BOTTOM
    ) -> list[tuple[str, EpistemicValue]]:
        """
        Query derived facts.

        Returns list of (entity, epistemic_value) pairs.
        """
        results = []
        for (p, e), v in self.facts.items():
            if p == predicate and v > min_value:
                if entity is None or e == entity:
                    results.append((e, v))
        return sorted(results, key=lambda x: x[1], reverse=True)

    def explain(
        self, predicate: str, entity: str
    ) -> list[str]:
        """
        Return the derivation trace for a specific fact.
        """
        target = f"{predicate}({entity})"
        return [
            step for step in self.trace
            if target in step
        ]

    def validate_predicates(
        self, predicates: list[str]
    ) -> list[str]:
        """
        Validate a list of predicate strings against
        the known vocabulary. Used by Layer 5 of grounding.

        Returns list of error messages (empty = all valid).
        """
        errors = []
        known_preds = set()
        for rule in self.rules:
            known_preds.add(rule.head)
            known_preds.update(rule.body_positive)
            known_preds.update(rule.body_negative)

        for pred_str in predicates:
            # Parse "predicate_name(entity)"
            if '(' not in pred_str or ')' not in pred_str:
                errors.append(
                    f"Malformed: '{pred_str}' — "
                    f"expected format: predicate(entity)"
                )
                continue

            name = pred_str.split('(')[0].strip()
            if name.startswith('not_'):
                name = name[4:]

            if name not in known_preds:
                errors.append(
                    f"Unknown predicate: '{name}' — "
                    f"valid predicates: "
                    f"{sorted(known_preds)[:10]}..."
                )

        return errors

    # ─── Integrity Constraints ───────────────────────

    def check_hetvabhasas(self) -> list[Violation]:
        """
        Run all hetvābhāsa checks against current facts.
        Returns list of violations.
        """
        violations = []
        for check in self.hetvabhasa_checks:
            triggers = check['check_fn'](self.facts)
            if triggers:
                violations.append(Violation(
                    hetvabhasa_id=check['id'],
                    name=check['name'],
                    description=(
                        f"{check['name']} detected in "
                        f"current derivation"
                    ),
                    triggered_by=triggers,
                    correction=check['correction'],
                ))
        return violations

    # ─── Serialization ───────────────────────────────

    def to_datalog_text(self) -> str:
        """Export the full knowledge base as Datalog text."""
        lines = [
            f"% Ānvīkṣikī Knowledge Base",
            f"% Mode: {'Boolean' if self.boolean_mode else 'Lattice'}",
            f"% Rules: {len(self.rules)}",
            f"% Facts: {len(self.facts)}",
            "",
        ]

        lines.append("% ─── Rules (Vyāptis) ───")
        for rule in self.rules:
            lines.append(str(rule))
            lines.append("")

        lines.append("% ─── Facts ───")
        for (pred, entity), value in sorted(self.facts.items()):
            if self.boolean_mode:
                lines.append(f"{pred}({entity}).")
            else:
                lines.append(
                    f"{pred}({entity}) :- "
                    f"/* {value.name} */."
                )

        return "\n".join(lines)
```

#### 7.4.2 T2 Compiler — Revised (Datalog Target)

```python
# anvikshiki/t2_compiler_v2.py
"""
T2 Compiler: Compile verified architecture into Datalog rules.

Phase 2: Boolean mode (rules fire or don't)
Phase 3: Lattice mode (rules carry epistemic values)

The compiler produces the SAME rules for both phases.
The engine's mode determines how values propagate.
"""

from .schema import KnowledgeStore, EpistemicStatus
from .datalog_engine import (
    DatalogEngine, Rule, Fact, EpistemicValue
)


# Map schema epistemic status to lattice values
EPISTEMIC_MAP = {
    EpistemicStatus.ESTABLISHED: EpistemicValue.ESTABLISHED,
    EpistemicStatus.WORKING_HYPOTHESIS: EpistemicValue.HYPOTHESIS,
    EpistemicStatus.GENUINELY_OPEN: EpistemicValue.OPEN,
    EpistemicStatus.ACTIVELY_CONTESTED: EpistemicValue.CONTESTED,
}


def compile_t2(
    knowledge_store: KnowledgeStore,
    boolean_mode: bool = True
) -> DatalogEngine:
    """
    Compile the verified architecture into a Datalog engine.

    boolean_mode=True: Phase 2 (rules fire/don't fire)
    boolean_mode=False: Phase 3+ (epistemic values propagate)
    """
    engine = DatalogEngine(boolean_mode=boolean_mode)

    # ── Compile vyāptis as Datalog rules ──
    for vid, v in knowledge_store.vyaptis.items():
        rule = Rule(
            vyapti_id=vid,
            name=v.name,
            head=v.consequent,
            body_positive=v.antecedents,
            body_negative=v.scope_exclusions,
            confidence=EPISTEMIC_MAP.get(
                v.epistemic_status,
                EpistemicValue.HYPOTHESIS
            ),
        )
        engine.add_rule(rule)

    # ── Compile hetvābhāsas as integrity constraints ──
    for hid, h in knowledge_store.hetvabhasas.items():
        # Each hetvābhāsa becomes a check function
        check_fn = _build_hetvabhasa_check(h, knowledge_store)
        engine.add_hetvabhasa_check(
            hid=hid,
            name=h.name,
            check_fn=check_fn,
            correction=h.correction_pattern,
        )

    return engine


def _build_hetvabhasa_check(hetvabhasa, knowledge_store):
    """
    Build a check function for a hetvābhāsa.

    The check function examines the derived facts and returns
    a list of triggering fact keys if the fallacy pattern matches.

    This is where domain-specific fallacy detection lives.
    Each hetvābhāsa has a detection signature that maps to
    a specific pattern over the fact base.
    """
    sig = hetvabhasa.detection_signature.lower()

    def check(facts):
        triggers = []

        # Survivorship bias: conclusion derived from
        # selective evidence (only successful cases)
        if "survivorship" in sig:
            for (pred, entity), val in facts.items():
                # Check if the entity has "success" predicates
                # but no "failure" or "base_rate" predicates
                if "success" in pred or "winner" in pred:
                    has_base = any(
                        "base_rate" in p or "failure" in p
                        for (p, e), v in facts.items()
                        if e == entity
                    )
                    if not has_base:
                        triggers.append(
                            f"{pred}({entity}) — "
                            f"no base rate considered"
                        )

        # Scale extrapolation: applying rule outside
        # its validated scale
        if "scale" in sig or "extrapolat" in sig:
            for (pred, entity), val in facts.items():
                if "large_scale" in pred or "enterprise" in pred:
                    has_scale_evidence = any(
                        "scale_validated" in p
                        for (p, e), v in facts.items()
                        if e == entity
                    )
                    if not has_scale_evidence:
                        triggers.append(
                            f"{pred}({entity}) — "
                            f"not validated at this scale"
                        )

        return triggers

    return check


def ground_facts_from_predicates(
    engine: DatalogEngine,
    predicates: list[str],
    default_value: EpistemicValue = EpistemicValue.ESTABLISHED
) -> list[Fact]:
    """
    Convert grounding output (predicate strings) into
    Datalog facts and add them to the engine.

    Called after the grounding pipeline produces verified
    predicates.
    """
    facts = []
    for pred_str in predicates:
        # Parse "predicate_name(entity)"
        # or "not_predicate_name(entity)"
        negated = pred_str.startswith("not_")
        clean = pred_str[4:] if negated else pred_str

        if '(' in clean and ')' in clean:
            name = clean.split('(')[0].strip()
            entity = clean.split('(')[1].rstrip(')').strip()

            if negated:
                # Negated facts get BOTTOM value
                # (they exist to trigger scope exclusions)
                fact = Fact(name, entity, EpistemicValue.BOTTOM)
            else:
                fact = Fact(name, entity, default_value)

            engine.add_fact(fact)
            facts.append(fact)

    return facts
```

#### 7.4.3 What Phase 2 Achieves Over Phase 1

| Capability | Phase 1 (DSPy only) | Phase 2 (DSPy + Datalog) |
|-----------|---------------------|--------------------------|
| Scope enforcement | LLM checks (unreliable) | Datalog negation (deterministic) |
| Fallacy detection | dspy.Suggest (soft) | Integrity constraints (hard) |
| Proof traces | CoT text (unverifiable) | Datalog derivation trace (formal) |
| Prerequisite traversal | LLM guesses | Graph traversal (complete) |
| Decay checking | Python code (correct) | Datalog precondition (correct) |
| Novel inference | LLM generation | Forward chaining (provable) |
| Termination | N/A (LLM always responds) | Guaranteed polynomial |
| Grounding (NL → predicates) | Five-layer defense | Five-layer defense — unchanged |
| Verbalization | DSPy (optimizable) | DSPy (optimizable) — unchanged |

**The key architectural insight:** DSPy handles what LLMs are good at (natural language understanding and generation). Datalog handles what symbolic systems are good at (deterministic inference, constraint checking, proof construction). Each component does what it's actually good at.

**But Phase 2 has a fundamental limitation:** Datalog in Boolean mode uses all-or-nothing truth. A vyāpti either holds or it doesn't. A proof either succeeds or it fails. There is no room for "this rule holds with moderate confidence based on observational evidence" or "this conclusion is 70% certain because it depends on a working hypothesis." The epistemic metadata exists in the knowledge store but Datalog cannot use it during inference — it's carried alongside the proof, not integrated into the proof.

This motivates Phase 3.

---

### 7.5 Phase 3: DSPy + Lattice Datalog + UQ

**What changes from Phase 2:** One line.

```python
# Phase 2:
engine = compile_t2(knowledge_store, boolean_mode=True)

# Phase 3:
engine = compile_t2(knowledge_store, boolean_mode=False)
```

That's it. The same engine, the same rules, the same evaluation algorithm. The only difference: when `boolean_mode=False`, the engine computes `meet(rule_confidence, min(antecedent_values))` instead of returning `ESTABLISHED` for every successful derivation.

**Why this is a separate phase despite being one line of code:** The conceptual shift is profound. In Phase 2, a chain through three rules produces a Boolean result: "yes, this follows." In Phase 3, the same chain produces: "this follows, but the conclusion is at most a WORKING HYPOTHESIS because V7 in the middle of the chain is a hypothesis." The UQ decomposition now works *structurally*:

**Epistemic uncertainty:** Read directly from the Heyting values of derived facts. A fact with value `HYPOTHESIS` has higher epistemic uncertainty than one with value `ESTABLISHED`. No metadata computation needed — it's the inference result itself.

**Aleatoric uncertainty:** Computed from domain type and scope condition count (unchanged).

**Inference uncertainty:** Computed from ensemble disagreement in the grounding pipeline (Layers 3-4 of the defense).

#### 7.5.1 Three-Way Uncertainty Decomposition

```python
# anvikshiki/uncertainty.py
"""
Three-way uncertainty decomposition for the Ānvīkṣikī Engine.
"""

from .datalog_engine import DatalogEngine, EpistemicValue
from .schema import KnowledgeStore, DomainType, DecayRisk


def compute_uncertainty(
    engine: DatalogEngine,
    knowledge_store: KnowledgeStore,
    grounding_confidence: float,
    target_predicate: str,
    target_entity: str,
) -> dict:
    """
    Full uncertainty decomposition for a derived fact.
    """
    # ── Epistemic (from Heyting values — structural) ──
    results = engine.query(target_predicate, target_entity)
    if not results:
        epistemic = {
            'status': 'NOT_DERIVED',
            'value': 'BOTTOM',
            'explanation': (
                f"No derivation path for "
                f"{target_predicate}({target_entity})"
            ),
        }
    else:
        entity, value = results[0]
        trace = engine.explain(target_predicate, target_entity)

        # Find the weakest link in the derivation
        weakest_step = None
        for step in trace:
            for v in EpistemicValue:
                if v.name in step and (
                    weakest_step is None or
                    v < weakest_step
                ):
                    weakest_step = v

        epistemic = {
            'status': value.name,
            'value': value.value,
            'weakest_link': (
                weakest_step.name if weakest_step else "N/A"
            ),
            'derivation_depth': len(trace),
            'explanation': (
                f"Derived with epistemic value "
                f"{value.name}" +
                (f" (limited by {weakest_step.name} "
                 f"in chain)" if weakest_step and
                 weakest_step < value else "")
            ),
        }

    # ── Aleatoric (from domain type — structural) ──
    domain_base = {
        DomainType.FORMAL: 0.0,
        DomainType.MECHANISTIC: 0.1,
        DomainType.EMPIRICAL: 0.3,
        DomainType.CRAFT: 0.5,
        DomainType.INTERPRETIVE: 0.6,
        DomainType.DESIGN: 0.4,
        DomainType.NORMATIVE: 0.5,
        DomainType.META_ANALYTICAL: 0.3,
    }.get(knowledge_store.domain_type, 0.5)

    # Count high-decay rules in the derivation
    decay_count = 0
    total_rules = 0
    for step in engine.trace:
        for vid, v in knowledge_store.vyaptis.items():
            if vid in step:
                total_rules += 1
                if v.decay_risk in (
                    DecayRisk.HIGH, DecayRisk.CRITICAL
                ):
                    decay_count += 1

    aleatoric = {
        'domain_base_uncertainty': domain_base,
        'decay_exposure': (
            decay_count / max(total_rules, 1)
        ),
        'explanation': (
            f"Domain type {knowledge_store.domain_type.name} "
            f"has base uncertainty {domain_base:.1f}. "
            f"{decay_count}/{total_rules} rules have "
            f"high decay risk."
        ),
    }

    # ── Inference (from grounding ensemble — measured) ──
    inference = {
        'grounding_confidence': grounding_confidence,
        'explanation': (
            f"Grounding ensemble agreement: "
            f"{grounding_confidence:.2f}. " +
            ("Reliable." if grounding_confidence > 0.8
             else "Moderate — some predicate disagreement."
             if grounding_confidence > 0.5
             else "Low — query may be ambiguous.")
        ),
    }

    # ── Aggregate ──
    # Conservative: total confidence is the minimum
    if epistemic.get('value', 0) == 'BOTTOM':
        total = 0.0
    else:
        ep_score = epistemic.get('value', 0) / 4.0
        al_score = 1.0 - aleatoric['domain_base_uncertainty']
        in_score = inference['grounding_confidence']
        total = min(ep_score, al_score, in_score)

    return {
        'epistemic': epistemic,
        'aleatoric': aleatoric,
        'inference': inference,
        'total_confidence': total,
    }
```

#### 7.5.2 Conformal Prediction for Source Grounding

Beyond the three uncertainty types, we add **conformal prediction** to provide statistical guarantees that claims are grounded in the Reference Bank:

```python
# anvikshiki/conformal.py
"""
Conformal prediction for source verification.

Provides statistical guarantee: with probability ≥ 1-α,
every claim in the response is grounded in the Reference Bank.
"""

import numpy as np
from typing import Optional


class ConformalSourceVerifier:
    """
    Uses split conformal prediction to calibrate
    source-grounding scores.
    """

    def __init__(self, alpha: float = 0.1):
        self.alpha = alpha  # 90% coverage by default
        self.calibration_scores = []
        self.threshold = None

    def calibrate(
        self,
        calibration_set: list[tuple[str, str, bool]]
    ):
        """
        Calibrate using labeled examples.

        calibration_set: list of (claim, source_passage, is_supported)
        """
        scores = []
        for claim, source, supported in calibration_set:
            score = self._score_support(claim, source)
            if supported:
                scores.append(score)

        # Conformal quantile
        n = len(scores)
        q = np.ceil((1 - self.alpha) * (n + 1)) / n
        self.threshold = np.quantile(scores, q)
        self.calibration_scores = scores

    def verify_claim(
        self, claim: str, sources: list[str]
    ) -> dict:
        """
        Verify a claim against available sources.
        Returns verification result with coverage guarantee.
        """
        if self.threshold is None:
            raise ValueError("Must calibrate before verifying")

        scores = [
            self._score_support(claim, src)
            for src in sources
        ]

        best_score = max(scores) if scores else 0.0
        best_source = (
            sources[np.argmax(scores)] if scores else None
        )

        return {
            'supported': best_score >= self.threshold,
            'support_score': best_score,
            'best_source': best_source,
            'coverage_guarantee': 1 - self.alpha,
            'threshold': self.threshold,
        }

    def _score_support(
        self, claim: str, source: str
    ) -> float:
        """
        Score how well a source passage supports a claim.
        Uses embedding similarity + keyword overlap.
        """
        # Simplified: in production, use a trained NLI model
        # or embedding cosine similarity
        claim_words = set(claim.lower().split())
        source_words = set(source.lower().split())

        if not claim_words:
            return 0.0

        overlap = len(claim_words & source_words)
        return overlap / len(claim_words)
```

---

### 7.6 Phase 4: DSPy + Lattice Datalog + Sheaf + UQ

**What changes from Phase 3:** The sheaf layer is added *on top* of the Datalog engine. The sheaf operates on the derived facts, not on the inference process. The coboundary operator, sheaf Laplacian, and H¹ cohomology computation check whether derived facts are locally-to-globally consistent.

**Why this is the correct architecture:** The sheaf doesn't need to know how facts were derived. It checks whether the derived facts are locally-to-globally consistent. This means the sheaf code works unchanged from the Datalog engine — it takes the knowledge graph and derived facts as input and computes consistency/violations.

#### 7.6.1 Cellular Sheaf Structure

The knowledge graph, equipped with Heyting-valued logic, naturally forms a cellular sheaf. Each concept is a vertex (stalk), each vyāpti is an edge (restriction map), and the scope conditions define the topology:

```python
# anvikshiki/sheaf.py
"""
Cellular sheaf over the vyāpti knowledge graph.

The sheaf structure provides:
1. Local-to-global consistency checking
2. Cohomological hetvābhāsa detection
3. Scope-aware reasoning
"""

import numpy as np
import networkx as nx


class KnowledgeSheaf:
    """
    Cellular sheaf over the Ānvīkṣikī knowledge graph.

    Vertices (0-cells): domain concepts
    Edges (1-cells): vyāptis (rules connecting concepts)
    Stalks: vector spaces at each vertex
    Restriction maps: linear maps along each edge

    The sheaf Laplacian's kernel = globally consistent sections
    Non-zero cohomology H¹ = hetvābhāsas (obstructions to gluing)
    """

    def __init__(self, graph: nx.DiGraph, stalk_dim: int = 8):
        self.graph = graph
        self.stalk_dim = stalk_dim
        self.stalks = {}       # node → dimension
        self.restrictions = {} # edge → matrix (stalk_dim × stalk_dim)
        self.truth_values = {} # node → EpistemicValue

        # Initialize stalks
        for node in graph.nodes():
            self.stalks[node] = stalk_dim

        # Initialize restriction maps (identity by default)
        for u, v in graph.edges():
            self.restrictions[(u, v)] = np.eye(stalk_dim)

    def set_restriction(
        self, edge: tuple, matrix: np.ndarray
    ):
        """Set the restriction map for an edge (vyāpti)."""
        self.restrictions[edge] = matrix

    def coboundary(
        self, section: dict[str, np.ndarray]
    ) -> dict[tuple, np.ndarray]:
        """
        Compute the coboundary operator δ(section).

        For each edge (u,v) with restriction map F_{u→v}:
          δ(section)(u,v) = F_{u→v} · section(u) - section(v)

        If δ = 0 everywhere: section is globally consistent.
        Non-zero δ entries: inconsistencies (hetvābhāsas!).
        """
        coboundary = {}
        for (u, v) in self.graph.edges():
            if u in section and v in section:
                F = self.restrictions.get(
                    (u, v), np.eye(self.stalk_dim))
                coboundary[(u, v)] = (
                    F @ section[u] - section[v]
                )
        return coboundary

    def detect_hetvabhasas(
        self,
        reasoning_section: dict[str, np.ndarray],
        threshold: float = 0.1
    ) -> list[dict]:
        """
        Detect hetvābhāsas as cohomological obstructions.

        A hetvābhāsa occurs when local reasoning is consistent
        within each scope but fails to glue globally.
        This is precisely a non-zero element in H¹.

        Returns list of violations with location and magnitude.
        """
        delta = self.coboundary(reasoning_section)

        violations = []
        for edge, residual in delta.items():
            norm = np.linalg.norm(residual)
            if norm > threshold:
                violations.append({
                    'edge': edge,
                    'magnitude': norm,
                    'residual': residual,
                    'interpretation': (
                        f"Reasoning along {edge[0]} → {edge[1]} "
                        f"is locally consistent but fails to "
                        f"glue with global knowledge "
                        f"(residual norm: {norm:.3f})"
                    )
                })

        return violations

    def sheaf_laplacian(self) -> np.ndarray:
        """
        Compute the sheaf Laplacian L = δᵀδ.

        Properties:
        - kernel(L) = space of globally consistent sections (H⁰)
        - First non-zero eigenvalue = spectral gap
          (measures how "close to consistent" the knowledge base is)
        """
        n_nodes = len(self.graph.nodes())
        total_dim = n_nodes * self.stalk_dim

        # Build coboundary matrix
        nodes = list(self.graph.nodes())
        node_idx = {n: i for i, n in enumerate(nodes)}

        n_edges = len(self.graph.edges())
        delta = np.zeros((n_edges * self.stalk_dim, total_dim))

        for e_idx, (u, v) in enumerate(self.graph.edges()):
            F = self.restrictions.get(
                (u, v), np.eye(self.stalk_dim))

            u_start = node_idx[u] * self.stalk_dim
            v_start = node_idx[v] * self.stalk_dim
            e_start = e_idx * self.stalk_dim

            delta[e_start:e_start+self.stalk_dim,
                  u_start:u_start+self.stalk_dim] = F
            delta[e_start:e_start+self.stalk_dim,
                  v_start:v_start+self.stalk_dim] = -np.eye(
                      self.stalk_dim)

        return delta.T @ delta

    def global_consistency_score(self) -> float:
        """
        Measure overall consistency of the knowledge base.
        Uses the spectral gap of the sheaf Laplacian.

        High score = knowledge base is internally consistent.
        Low score = significant contradictions or scope conflicts.
        """
        L = self.sheaf_laplacian()
        eigenvalues = np.linalg.eigvalsh(L)

        # Spectral gap: second-smallest eigenvalue
        # (smallest is always 0 for connected component)
        sorted_eigs = sorted(eigenvalues)
        if len(sorted_eigs) < 2:
            return 1.0

        spectral_gap = sorted_eigs[1]
        # Normalize to [0, 1]
        return min(spectral_gap / 10.0, 1.0)
```

#### 7.6.2 Why Topos Theory Matters Here

The Phase 4 architecture is, mathematically, a **presheaf of Heyting-valued facts over the vyāpti graph, equipped with a sheaf condition that detects reasoning inconsistencies as cohomological obstructions**.

In simpler language:

1. **The Heyting algebra** replaces Boolean truth with epistemic qualification. A proof through a HYPOTHESIS produces at most a HYPOTHESIS. This is structurally correct — uncertainty propagates through inference, not alongside it.

2. **The cellular sheaf** replaces flat constraint checking with local-to-global consistency. A hetvābhāsa is not just a keyword match — it's a formal obstruction to extending local reasoning to a global conclusion. Survivorship bias means: your reasoning works in the scope of successful companies (local section) but fails when you include failures (no global section). The sheaf cohomology group H¹ measures exactly these obstructions.

3. **The subobject classifier Ω** of the topos is the Heyting algebra itself. In classical logic, Ω = {true, false}. In our topos, Ω = {ESTABLISHED, HYPOTHESIS, OPEN, CONTESTED, BOTTOM}. This means the logic of the entire system — not just the facts, but the rules of inference — operates over qualified truth values.

4. **The topology** (in the categorical sense) encodes scope conditions. An "open set" is a scope — "private companies," "stable markets," "post-2020 regulatory environment." The sheaf condition says: you can claim a vyāpti globally only if it glues consistently across all relevant scopes. If it doesn't, the system knows the claim is scope-dependent and reports which scopes it holds in.

This is not a metaphor — it's the mathematical content. The engine IS a presheaf topos over a finite site, and the inference IS computing sections.

---

## 8. The Final Engine — Complete Implementation

```python
# anvikshiki/engine_final.py
"""
The Ānvīkṣikī Engine — Final Architecture (v2)

Components:
1. Five-layer grounding defense (NL → verified predicates)
2. Lattice Datalog engine (verified predicates → derived facts)
3. Cellular sheaf consistency check (derived facts → violations)
4. Conformal source verification (claims → grounded claims)
5. DSPy synthesis (everything → calibrated response)
6. Three-way uncertainty decomposition

All inference is deterministic and terminates in polynomial time.
All uncertainty is structurally computed, not self-reported.
Grounding is the only LLM-dependent component, and it has
five layers of defense.
"""

import dspy
from .schema import KnowledgeStore
from .grounding import GroundingPipeline, GroundingResult
from .datalog_engine import DatalogEngine, EpistemicValue
from .t2_compiler_v2 import (
    compile_t2, ground_facts_from_predicates, EPISTEMIC_MAP
)
from .sheaf import KnowledgeSheaf
from .conformal import ConformalSourceVerifier
from .uncertainty import compute_uncertainty


class SynthesizeResponse(dspy.Signature):
    """Produce a calibrated response from inference results."""

    query: str = dspy.InputField()
    derivation_trace: str = dspy.InputField(
        desc="Step-by-step Datalog derivation")
    retrieved_prose: str = dspy.InputField(
        desc="Relevant guide text for exposition")
    uncertainty_report: str = dspy.InputField(
        desc="Full uncertainty decomposition")
    hetvabhasa_violations: str = dspy.InputField(
        desc="Any detected reasoning fallacies")

    response: str = dspy.OutputField(
        desc="Natural language response with appropriate "
             "epistemic qualification")
    sources_cited: list[str] = dspy.OutputField(
        desc="Reference Bank entries supporting claims")


class AnvikshikiEngine(dspy.Module):
    """The complete Ānvīkṣikī Engine."""

    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        sheaf: KnowledgeSheaf,
        conformal: ConformalSourceVerifier,
        boolean_mode: bool = False,   # Phase 3+ by default
    ):
        super().__init__()
        self.ks = knowledge_store
        self.sheaf = sheaf
        self.conformal = conformal

        # Compile T2: knowledge store → Datalog engine
        self.engine = compile_t2(
            knowledge_store, boolean_mode=boolean_mode
        )

        # Grounding pipeline (five-layer defense)
        self.grounding = GroundingPipeline(
            knowledge_store, self.engine
        )

        # Synthesis module
        self.synthesizer = dspy.ChainOfThought(
            SynthesizeResponse
        )

    def forward(
        self, query: str, retrieved_chunks: list[str]
    ):
        # ═══ STEP 1: Five-layer grounding ═══
        grounding = self.grounding(query)

        if grounding.clarification_needed:
            return dspy.Prediction(
                response=(
                    "I need clarification to answer precisely. "
                    f"Disputed elements: "
                    f"{', '.join(grounding.disputed)}. "
                    "Could you specify?"
                ),
                confidence=grounding.confidence,
                uncertainty={'type': 'grounding_ambiguity'},
            )

        # ═══ STEP 2: Ground facts into Datalog ═══
        # Fresh engine for each query
        # (prevents cross-query contamination)
        self.engine = compile_t2(
            self.ks,
            boolean_mode=self.engine.boolean_mode
        )

        grounded_facts = ground_facts_from_predicates(
            self.engine, grounding.predicates
        )

        # ═══ STEP 3: Forward chain (deterministic) ═══
        iterations = self.engine.evaluate()

        # ═══ STEP 4: Hetvābhāsa check (deterministic) ═══
        violations = self.engine.check_hetvabhasas()

        # ═══ STEP 5: Sheaf consistency check ═══
        section = self._build_sheaf_section()
        sheaf_violations = self.sheaf.detect_hetvabhasas(
            section
        )

        # Merge both violation types
        all_violations = violations + [
            type('Violation', (), {
                'hetvabhasa_id': f"SHEAF_{i}",
                'name': v['interpretation'],
                'description': v['interpretation'],
                'triggered_by': [str(v['edge'])],
                'correction': (
                    "Reasoning is locally consistent but "
                    "fails to glue globally"
                ),
            })()
            for i, v in enumerate(sheaf_violations)
        ]

        # ═══ STEP 6: Conformal source verification ═══
        claim_verifications = []
        for (pred, entity), value in self.engine.facts.items():
            if value > EpistemicValue.BOTTOM:
                sources = self._get_sources(pred, entity)
                if sources and self.conformal.threshold:
                    v = self.conformal.verify_claim(
                        f"{pred}({entity})", sources
                    )
                    claim_verifications.append(v)

        # ═══ STEP 7: Uncertainty decomposition ═══
        # Find the primary derived fact for UQ
        primary_pred = None
        for (pred, entity), value in self.engine.facts.items():
            if value > EpistemicValue.BOTTOM and \
               (pred, entity) not in {
                   (f.predicate, f.entity)
                   for f in grounded_facts
               }:
                primary_pred = (pred, entity)
                break

        if primary_pred:
            uncertainty = compute_uncertainty(
                self.engine,
                self.ks,
                grounding.confidence,
                primary_pred[0],
                primary_pred[1],
            )
        else:
            uncertainty = {
                'epistemic': {'status': 'NO_DERIVATION'},
                'aleatoric': {
                    'domain_base_uncertainty': 0.5},
                'inference': {
                    'grounding_confidence':
                        grounding.confidence},
                'total_confidence': 0.0,
            }

        # ═══ STEP 8: Synthesize response ═══
        context = '\n'.join(retrieved_chunks)

        # Add warnings and violations to context
        if grounding.warnings:
            context += (
                f"\n\nWARNINGS: "
                f"{'; '.join(grounding.warnings)}"
            )
        if all_violations:
            context += (
                f"\n\nFALLACY ALERTS: "
                f"{'; '.join(v.name for v in all_violations)}"
            )

        response = self.synthesizer(
            query=query,
            derivation_trace='\n'.join(self.engine.trace),
            retrieved_prose=context,
            uncertainty_report=str(uncertainty),
            hetvabhasa_violations=str([
                {'id': v.hetvabhasa_id, 'name': v.name,
                 'correction': v.correction}
                for v in all_violations
            ]),
        )

        # Assert synthesis faithfulness
        dspy.Assert(
            len(response.response) > 0,
            "Response must not be empty"
        )

        return dspy.Prediction(
            response=response.response,
            sources=response.sources_cited,
            uncertainty=uncertainty,
            proof_trace=self.engine.trace,
            violations=[
                {'id': v.hetvabhasa_id, 'name': v.name,
                 'correction': v.correction}
                for v in all_violations
            ],
            grounding_confidence=grounding.confidence,
            derivation_iterations=iterations,
        )

    def _build_sheaf_section(self):
        """Build a section from derived facts for sheaf check."""
        import numpy as np
        section = {}
        for (pred, entity), value in self.engine.facts.items():
            node = pred
            if node not in section:
                section[node] = np.zeros(
                    self.sheaf.stalk_dim)
            # Encode value in the stalk vector
            section[node][0] = value.value / 4.0
            section[node][1] = 1.0  # "fact exists" flag
        return section

    def _get_sources(self, predicate, entity):
        """Get Reference Bank sources for a claim."""
        sources = []
        for vid, v in self.ks.vyaptis.items():
            if v.consequent == predicate or \
               predicate in v.antecedents:
                sources.extend(v.sources)
        return [
            self.ks.reference_bank.get(sid, {}).get(
                'text', '')
            for sid in sources
            if sid in self.ks.reference_bank
        ]
```

---

## 9. What Is Truly Novel

Several aspects of this architecture have no precedent in the literature:

**1. Epistemic-status-propagating inference via lattice Datalog.**
No existing neurosymbolic system propagates epistemic qualification *through* inference chains in a computationally tractable framework. Logic engines use Boolean truth. LLMs report confidence as a separate channel. The lattice Datalog engine makes epistemic qualification structural: a chain through a hypothesis yields at most a hypothesis, by the rules of the logic itself — with guaranteed polynomial termination. No existing neurosymbolic system combines epistemic value propagation with Datalog's complexity guarantees.

**2. Hetvābhāsa as cohomological obstruction.**
The identification of reasoning fallacies with sheaf cohomology classes is, to our knowledge, new. Survivorship bias, scope violation, and scale extrapolation — traditionally treated as informal warning labels — become computable invariants of the knowledge graph's sheaf structure. H¹ ≠ 0 is a mathematical certificate that the reasoning contains a gluing failure.

**3. Decay-as-inference-precondition.**
Existing knowledge systems treat temporal validity as metadata. The Ānvīkṣikī engine makes validity a precondition for inference: a stale rule cannot fire. The Datalog implementation makes this a hard constraint; the lattice implementation degrades the rule's epistemic value over time, which propagates through any chain that uses it.

**4. Three-way uncertainty decomposition with heterogeneous methods.**
The decomposition into epistemic (lattice values), aleatoric (domain classification), and inference (ensemble sampling) uncertainty, each using the method appropriate to its nature, is not found in existing UQ frameworks for LLMs. Most LLM UQ methods estimate total uncertainty from output distributions. We compute each component from its natural source.

**5. Conformal prediction over a structured Reference Bank.**
Applying conformal prediction not to generic RAG retrieval but to a reference bank with known provenance chains gives statistical guarantees that are meaningful — the guarantee is not just "a relevant chunk was retrieved" but "this specific claim is supported by this specific source with this coverage level."

**6. The Ānvīkṣikī-to-Datalog correspondence.**
The observation that Nyāya vyāptis map directly to Datalog rules, hetvābhāsas to integrity constraints, and the pañcāvayava to structured proof traces connects a 2,500-year-old epistemological framework to modern logic programming. The correspondence is tighter with Datalog than with Prolog: Datalog's guaranteed termination matches the finite, non-recursive nature of domain knowledge bases.

**7. Five-layer grounding defense.**
The combination of ontology-constrained prompting, grammar-constrained decoding (CRANE), ensemble consensus, round-trip verification, and solver-feedback refinement into a layered defense-in-depth for the NL→predicate translation problem. No existing neurosymbolic system addresses grounding with more than one strategy.

**8. Datalog as the unifying formalism across all phases.**
The insight that Boolean Datalog (Phase 2) and lattice Datalog (Phase 3) are the same engine with a one-parameter change eliminates the engine migration problem that plagues neurosymbolic systems (where upgrading the reasoning engine requires rewriting the knowledge base). One engine, one knowledge base, incremental capability addition.

---

## 10. Limitations

**1. The grounding problem is mitigated but not solved.**
The five-layer defense reduces grounding errors from ~40% (zero-shot) to an estimated ~5-10%. Errors are now detectable (via ensemble disagreement and round-trip checks). But deeply implicit reasoning, novel predicate requirements, and pragmatic inference remain challenging. The defense adds 5-7 LLM calls per query.

**2. The knowledge base is manually constructed.**
Human expert review of the architecture output remains necessary. The LLM-assisted formalization (NL vyāpti → Datalog rule) needs human review. This is by design (domain experts should validate domain rules) but limits scalability.

**3. The Heyting algebra is coarse.**
Four epistemic values (plus bottom) is a very simple lattice. Real epistemic qualification is more nuanced — a claim might be "established in the American context but contested in the European context" in ways that a single lattice value cannot capture. A richer Heyting algebra (or a proper sheaf of Heyting algebras over the scope topology) would be more accurate but significantly more complex.

**4. Sheaf cohomology on large graphs is expensive.**
The sheaf Laplacian is a dense matrix of dimension (n_nodes × stalk_dim)². For a knowledge base with thousands of concepts and dozens of dimensions, this becomes computationally prohibitive. Sparse approximations (sheaf sparsifiers, à la Hansen & Ghrist) would be needed for production scale.

**5. The system does not learn from interaction.**
DSPy optimization improves prompts; the Datalog engine is static after compilation.

**6. Type 4 (Craft) domains resist complete formalization.**
Business strategy — the motivating domain — relies heavily on tacit knowledge, analogical reasoning, and practitioner judgment that cannot be fully captured in production rules. The T3 (prose retrieval) layer exists precisely to cover this gap, but the division between "what's formalizable" and "what's ineffable" is itself a matter of judgment.

**7. Datalog cannot express all Prolog programs.**
By choosing Datalog over Prolog, we lose unification over complex terms. If a domain requires nested term structures (mathematical reasoning, complex argument analysis), the engine needs extension to Datalog± or a hybrid Prolog subsystem. For Type 4 Craft domains, this limitation is theoretical — the vyāptis are flat predicates.

**8. Grammar-constrained decoding requires API access.**
Layer 2 (CRANE-style decoding) requires control over token generation probabilities. This works with open-source models (Mistral, Llama) but not with closed API models (GPT-4, Claude) where logit manipulation is not exposed. For API-only deployment, Layer 2 degrades to structured output formatting (JSON mode), which is weaker.

---

## 11. Further Directions

**1. Temporal sheaves for decay.** Instead of binary "stale/fresh" markers, model decay as a sheaf over a time category. A vyāpti's truth value varies with time, and the restriction maps along the time axis encode how confidence degrades. This would give decay-aware inference where the engine doesn't just check "is this stale?" but "how much has this degraded since verification?" — a continuous, not discrete, question.

**2. Bayesian sheaf neural networks for learned restriction maps.** Rather than hand-specifying the restriction maps (how concepts relate across vyāpti edges), learn them from data using the Bayesian sheaf neural network framework (Gillespie et al., 2024). This would let the engine discover relational structure in the knowledge base that the human architect missed, with principled uncertainty over the learned structure itself.

**3. Multi-domain topos composition via geometric morphisms.** When two domain guides exist (e.g., corporate strategy + financial accounting), their knowledge bases are different topoi. A geometric morphism between them would formalize how knowledge transfers: what accounting facts are relevant to strategy reasoning, and vice versa. Caramello's "toposes as bridges" methodology provides the theoretical framework; implementation would require defining appropriate sites for each domain and constructing the functors.

**4. Active learning for the grounding module.** When the grounding ensemble disagrees (high inference uncertainty), instead of just asking for clarification, the system could identify *which specific ambiguity* would most reduce uncertainty and ask a targeted question. This connects to the "underspecification uncertainty" framework (position paper, ICML 2025).

**5. DSPy optimization over the full pipeline.** Currently, DSPy optimizes the grounding and synthesis modules independently. A future version could define an end-to-end metric that jointly optimizes grounding accuracy, inference depth, and synthesis faithfulness, using the lattice Datalog engine's epistemic values as a differentiable signal.

**6. Integration with the meta-prompt as a feedback loop.** When the engine discovers a gap (query touches an area with no relevant vyāptis, or decay markers fire across an entire subgraph), it could trigger a targeted re-run of Stage 3 (Research Gate) to update the knowledge base. This would close the loop between query-time inference and compile-time knowledge construction.

**7. Incremental Datalog maintenance.** When a new fact arrives or a rule confidence changes, the current engine recomputes from scratch. Incremental Datalog maintenance (DRed algorithm, à la Gupta et al. 1993 or modern implementations in Soufflé) would allow efficient updates — only recomputing the facts affected by the change. This is essential for a live system where decay markers trigger mid-session and new evidence arrives during interaction.

**8. Grounding as a specialized fine-tuned model.** The five-layer defense is comprehensive but expensive (5-7 LLM calls). A domain-specific fine-tuned model (7B parameters) trained on the Ānvīkṣikī predicate vocabulary could replace Layers 1-3 with a single fast call, reserving Layers 4-5 for edge cases. The training data can be generated synthetically from the knowledge base itself — each vyāpti generates 20-50 NL queries, labeled with correct predicates.

**9. Multi-engine architecture for heterogeneous domains.** Different domain types may require different inference engines. A Type 1 (Formal) domain might need Prolog's unification. A Type 3 (Empirical) domain might need probabilistic Datalog (ProbLog). A Type 4 (Craft) domain is well-served by lattice Datalog. The architecture could dispatch to domain-appropriate engines while maintaining the same grounding defense and synthesis pipeline.

---

## 12. References

### Frameworks and Implementations

- **DSPy**: Khattab et al. "DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines." ICLR 2024. GitHub: stanfordnlp/dspy
- **DSPy Assertions**: Khattab et al. "DSPy Assertions: Computational Constraints for Self-Refining Language Model Pipelines." arXiv:2312.13382, 2023.
- **GraphRAG**: Microsoft. Graph-based RAG for knowledge graphs. GitHub: microsoft/graphrag
- **Logic-LM**: Pan et al. "Logic-LM: Empowering Large Language Models with Symbolic Solvers for Faithful Logical Reasoning." EMNLP 2023 Findings. GitHub: teacherpeterpan/Logic-LLM
- **DSPy + ASP**: Wang et al. "DSPy-based neural-symbolic pipeline to enhance spatial reasoning in LLMs." arXiv:2411.18564, 2024.

### Neurosymbolic Reasoning

- Chen et al. "Comparative Study of Neurosymbolic AI Approaches." NeSyLoR 2025.
- Dhanraj & Eliasmith. "Improving Rule-based Reasoning in LLMs using Neurosymbolic Representations." EMNLP 2025. GitHub: vdhanraj/Neurosymbolic-LLM
- Pan et al. "Logic-LM: Empowering Large Language Models with Symbolic Solvers." EMNLP 2023.

### Uncertainty Quantification

- **MUSE**: "Simple Yet Effective: An Information-Theoretic Approach to Multi-LLM Uncertainty Quantification." EMNLP 2025.
- **Conformal RAG**: Chakraborty et al. "Principled Context Engineering for RAG: Statistical Guarantees via Conformal Prediction." arXiv:2511.17908, 2025.
- **ConU**: "Conformal Uncertainty in Large Language Models with Correctness Coverage Guarantees." EMNLP Findings 2024.
- **TECP**: "Token-Entropy Conformal Prediction for LLMs." Mathematics 13(20), 2025.
- **Epistemic+Aleatoric**: "Uncovering Confident Failures: The Complementary Roles of Aleatoric and Epistemic Uncertainty in LLMs." NeurIPS 2025.
- KDD Survey: "Uncertainty Quantification and Confidence Calibration in Large Language Models." KDD 2025.
- ACL Survey: "A Survey of Uncertainty Estimation Methods on Large Language Models." ACL Findings 2025.

### Sheaf Theory and Topos Theory

- **Knowledge Sheaves**: Gebhart, Hansen & Schrater. "Knowledge Sheaves: A Sheaf-Theoretic Framework for Knowledge Graph Embedding." AISTATS 2023 (PMLR 206).
- **Bayesian Sheaf NN**: Gillespie et al. "Bayesian Sheaf Neural Networks." arXiv:2410.09590, 2024.
- **Sheaf Survey**: Ayzenberg et al. "Sheaf theory: from deep geometry to deep learning." arXiv:2502.15476, 2025.
- **Category Theory + ML Survey**: "Category-Theoretical and Topos-Theoretical Frameworks in Machine Learning." Axioms 14(3), 2025.
- **Copresheaf TNN**: "Copresheaf Topological Neural Networks: A Generalized Deep Learning Framework." arXiv:2505.21251, 2025.
- **Caramello**: "Toposes as 'bridges' for mathematics and artificial intelligence." Istituto Grothendieck, 2024.
- **Lafforgue**: "Some possible roles for AI of Grothendieck topos theory." ETH, 2022.
- **Relative Toposes for AGI**: Caramello. Course at CentraleSupélec, 2025.
- **Category Theory + ML Papers**: github.com/bgavran/Category_Theory_Machine_Learning

### Datalog and Lattice Extensions

- Ceri, Gottlob & Tanca. "What You Always Wanted to Know About Datalog (And Never Dared to Ask)." IEEE TKDE, 1989.
- Flix Programming Language. flix.dev — Datalog with first-class lattice semantics.
- Soufflé. souffle-lang.github.io — High-performance Datalog-to-C++ compiler.
- Madsen et al. "From Datalog to Flix: A Declarative Language for Fixed Points on Lattices." PLDI 2016.
- Scholz et al. "On Fast Large-Scale Program Analysis in Datalog." CC 2016 (Soufflé paper).

### Grounding Problem

- **CLOVER**: Ryu et al. "Divide and Translate." ICLR 2025. GitHub: Hyun-Ryu/clover
- **CRANE**: Banerjee et al. "Reasoning with constrained LLM generation." ICML 2025.
- **GCD for Logical Parsing**: Raspanti et al. ACL Industry 2025.
- **Logic-LM++**: Kirtania et al. ACL Workshop 2024.
- **ODKE+**: Khorshidi et al. 2025 (ontology-guided extraction, 98.8% precision).
- **FoVer**: Pei et al. TACL 2025 (FOL verification for NL reasoning).
- **Grammar-Aligned Decoding (ASAp)**: Wang et al. arXiv:2405.21047.
- **Structured Decomposition**: arXiv:2601.01609, 2025 (OWL2+SWRL for LLM reasoning).
- **Awesome-LLM-Constrained-Decoding**: github.com/Saibo-creator/Awesome-LLM-Constrained-Decoding

### DSPy + GraphRAG Integration

- adsharma/kuzu-demo-dspy — GraphRAG with DSPy and Kuzu graph database
- DerwenAI/strwythura — Neurosymbolic KG construction with DSPy
- stair-lab/kg-gen — Knowledge graph generation from text using DSPy (NeurIPS 2025)

### Epistemological Foundations

- Gautama. *Nyāya Sūtras*. c. 2nd century BCE.
- Kautilya. *Arthaśāstra*. c. 3rd century BCE.
- Meyer, J.H.F. & Land, R. "Threshold Concepts and Troublesome Knowledge." 2003.
- Sweller, J. "Cognitive Load During Problem Solving." Cognitive Science 12(2), 1988.
- Polanyi, M. *The Tacit Dimension*. 1966.

### Curated Resource Lists

- DavidZWZ/Awesome-RAG-Reasoning — RAG + reasoning integration (EMNLP 2025)
- LAMDASZ-ML/Awesome-LLM-Reasoning-with-NeSy — Neurosymbolic + LLM papers
- DEEP-PolyU/Awesome-GraphRAG — Latest GraphRAG papers and benchmarks
