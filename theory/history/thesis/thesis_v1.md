# The Ānvīkṣikī Engine

## From Philosophical Epistemology to Neurosymbolic Inference: Building a Sheaf-Theoretic Knowledge Engine for Domain-Specific Reasoning

---

**Abstract.** This thesis presents the design, architecture, and incremental construction of the Ānvīkṣikī Engine — a neurosymbolic reasoning system that compiles structured domain knowledge into an executable inference engine with principled uncertainty quantification. The system takes as input a pedagogical guide produced by the Ānvīkṣikī meta-prompt (a 3,963-line specification for generating expert-level instructional content) and compiles it into two subsystems: T2, a logic engine implementing domain-specific rules as executable inference; and T3, a graph-structured retrieval corpus that serves the prose layer. We develop the engine in four incremental stages — DSPy-only, DSPy+Prolog, DSPy+Prolog+UQ, and DSPy+Heyting+UQ — each addressing fundamental limitations of the prior. We demonstrate that the final architecture, grounded in cellular sheaf theory over Heyting-valued logic, provides a formally correct treatment of epistemic qualification, scope-dependent reasoning, and uncertainty decomposition that no existing RAG or LLM system achieves. The contribution is both theoretical (connecting 2,500-year-old Indian epistemology to modern topos theory through production rule systems) and practical (a buildable system with complete specifications).

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
6. Developing the Engine
   - 6.1 Architecture Overview
   - 6.2 Phase 1: DSPy Only
   - 6.3 Phase 2: DSPy + Prolog
   - 6.4 Phase 3: DSPy + Prolog + UQ
   - 6.5 Phase 4: DSPy + Heyting + UQ
7. What Is Truly Novel
8. Limitations
9. Further Directions
10. References

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

A natural question arises: is the Ānvīkṣikī framework — as a formal system — powerful enough to express arbitrary computation?

### The Core Primitive

The computational primitive of Ānvīkṣikī is the vyāpti — invariable concomitance. "Wherever A, necessarily B. A is present here. Therefore B is present here." This is modus ponens. Chained vyāptis create inference chains: A → B → C → D. The pañcāvayava (five-limbed argument) is a structured proof trace.

**This is syllogistic logic.** Aristotelian syllogism. Syllogistic logic alone is decidable, has no general recursion, and cannot simulate a Turing machine. So Ānvīkṣikī as Kautilya described it is **not Turing complete**.

### The Horn Clause Connection

But Ānvīkṣikī maps almost exactly onto Horn clause logic — the foundation of Prolog:

```prolog
% Vyāpti V1
fire(X) :- smoke(X).

% Vyāpti V2
strategic_reinvestment_possible(Co) :-
    concentrated_ownership(Co),
    long_time_horizon(Co).

% Hetvābhāsa H2 as an integrity constraint
:- infers_causation(X, A, B), only_correlation_shown(A, B).

% Concept dependency
can_understand(Reader, advanced_synthesis) :-
    can_understand(Reader, foundational_A),
    can_understand(Reader, foundational_B).
```

Prolog is Turing complete. When you add variable binding (unification), recursive rules, and unbounded inference depth, the system crosses the threshold. The vyāpti IS the production rule. The pañcāvayava IS the proof trace. The hetvābhāsa IS the integrity constraint.

### The Two Computational Layers

```
Layer 1: Meta-prompt execution (Stage 1 → Stage 2 → ... → Stage 8)
  This is a FINITE STATE MACHINE. Bounded states, bounded transitions.
  Not Turing complete.

Layer 2: Content reasoning (vyāpti chains applied to novel situations)
  This is SYLLOGISTIC LOGIC by default.
  Becomes TURING COMPLETE when implemented as Horn clauses
  with recursive rules and unification.
```

### Why This Matters for the Engine

The Turing completeness of the Horn clause implementation means the engine can, in principle, derive any computable consequence of the domain's rule base. But more practically, it means we face the halting problem: some queries may not terminate. The engine needs depth bounds, timeout mechanisms, and loop detection — engineering concerns that arise precisely because the system is computationally powerful enough to be useful.

The more important practical consequence is that the logic engine is the **native representation** of the Ānvīkṣikī framework. RAG is a workaround for not having an inference engine. The engine IS what the framework was always designed to be.

---

## 6. Developing the Engine

We now present the complete technical specification for the Ānvīkṣikī Engine, developed in four incremental phases. Each phase addresses specific limitations of the prior, and we motivate each transition explicitly.

### 6.1 Architecture Overview

The engine has three compilation targets and two runtime components:

**Compilation Targets:**
- **T1** (Guide): Human-readable pedagogical document (produced by meta-prompt, consumed by T3 compiler)
- **T2** (Logic Engine): Executable inference over formalized domain rules
- **T3** (Retrieval Corpus): Graph-structured RAG over guide prose with rich metadata

**Runtime Components:**
- **Grounding Module**: Translates natural language queries into structured predicates
- **Synthesis Module**: Translates inference results + retrieved prose into calibrated natural language responses

**Data Flow:**

```
          COMPILE TIME                          RUNTIME
    ┌────────────────────────┐      ┌──────────────────────────────┐
    │                        │      │                              │
    │  Meta-prompt           │      │  User Query (NL)             │
    │      │                 │      │      │                       │
    │      ▼                 │      │      ▼                       │
    │  Verified Architecture │      │  Grounding Module            │
    │      │                 │      │      │                       │
    │   ┌──┴──┐              │      │  ┌───┴───┐                   │
    │   │     │              │      │  │       │                   │
    │   ▼     ▼              │      │  ▼       ▼                   │
    │  T2    T1 Guide        │      │ T2      T3                   │
    │  Rules  │              │      │ Infer   Retrieve             │
    │         │              │      │  │       │                   │
    │         ▼              │      │  └───┬───┘                   │
    │        T3              │      │      ▼                       │
    │        Corpus          │      │  Synthesis Module            │
    │                        │      │      │                       │
    └────────────────────────┘      │      ▼                       │
                                    │  Calibrated Response         │
                                    └──────────────────────────────┘
```

### 6.2 Phase 1: DSPy Only — The Baseline

**What this phase builds:** A fully LLM-based reasoning system using DSPy as the orchestration framework. No symbolic reasoning, no logic engine, no formal constraints. This is the simplest possible implementation and establishes the baseline against which all subsequent phases are measured.

**Why start here:** DSPy (Khattab et al., ICLR 2024) provides the critical infrastructure — typed signatures, optimizable modules, automatic prompt compilation, and assertion-based self-refinement — that every subsequent phase builds on. Starting with DSPy-only forces us to confront what LLMs can and cannot do for domain reasoning before adding symbolic components.

#### 6.2.1 Dependencies

```bash
pip install dspy-ai graphrag networkx numpy
```

#### 6.2.2 The Knowledge Store

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
    formal_representation: Optional[str] # Prolog/logic form (Phase 2+)

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

#### 6.2.3 The T2 Compiler (Phase 1 — Schema Only)

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

#### 6.2.4 The T3 Compiler (Phase 1 — GraphRAG Index)

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

#### 6.2.5 The DSPy Reasoning Pipeline

Now the core: the DSPy modules that perform grounding, reasoning, and synthesis.

```python
# anvikshiki/engine_phase1.py
"""
Phase 1 Engine: Pure DSPy implementation.
All reasoning is performed by LLM modules with typed signatures.
"""

import dspy
from .schema import KnowledgeStore, Vyapti, Hetvabhasa


# ─── SIGNATURES ───────────────────────────────────────────────

class GroundQuery(dspy.Signature):
    """Translate a natural language query into structured predicates
    that the knowledge store can process."""
    
    query: str = dspy.InputField(desc="User's natural language question")
    domain_type: str = dspy.InputField(desc="Domain classification")
    available_vyaptis: str = dspy.InputField(
        desc="List of available rule names and their scope conditions")
    
    entities: list[str] = dspy.OutputField(
        desc="Entities mentioned or implied in the query")
    predicates: list[str] = dspy.OutputField(
        desc="Structured predicates extracted from the query")
    relevant_vyaptis: list[str] = dspy.OutputField(
        desc="IDs of vyāptis potentially relevant to this query")
    query_type: str = dspy.OutputField(
        desc="One of: derivation, validation, prerequisite, "
             "explanation, comparison")


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
        self.grounder = dspy.ChainOfThought(GroundQuery)
        self.reasoner = dspy.ChainOfThought(ReasonOverDomain)
        self.synthesizer = dspy.ChainOfThought(SynthesizeResponse)
    
    def forward(self, query: str, retrieved_chunks: list[str]):
        # Step 1: Ground the query
        vyapti_summary = self._format_vyaptis()
        grounding = self.grounder(
            query=query,
            domain_type=self.ks.domain_type.name,
            available_vyaptis=vyapti_summary
        )
        
        # Step 2: Gather relevant rules and constraints
        active_rules = self._get_active_rules(
            grounding.relevant_vyaptis)
        active_constraints = self._get_active_constraints(
            grounding.relevant_vyaptis)
        
        # Step 3: Check scope conditions (deterministic)
        scope_warnings = self._check_scope(
            grounding.predicates, active_rules)
        
        # Step 4: Check decay markers (deterministic)
        decay_warnings = self._check_decay(active_rules)
        
        # Step 5: Reason over domain
        context = '\n'.join(retrieved_chunks)
        if scope_warnings:
            context += f"\n\nSCOPE WARNINGS: {scope_warnings}"
        if decay_warnings:
            context += f"\n\nDECAY WARNINGS: {decay_warnings}"
        
        reasoning = self.reasoner(
            predicates=grounding.predicates,
            active_vyaptis=active_rules,
            active_hetvabhasas=active_constraints,
            retrieved_context=context
        )
        
        # Step 6: Hetvābhāsa check via assertion
        for hid, h in self.ks.hetvabhasas.items():
            dspy.Suggest(
                not self._pattern_match_fallacy(
                    h, reasoning.reasoning_chain),
                f"Possible {h.name}: {h.correction_pattern}"
            )
        
        # Step 7: Synthesize response
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
            scope_warnings=scope_warnings,
            decay_warnings=decay_warnings
        )
    
    # ─── DETERMINISTIC HELPERS ─────────────────────────────
    
    def _format_vyaptis(self) -> str:
        """Format all vyāptis for LLM context."""
        lines = []
        for vid, v in self.ks.vyaptis.items():
            lines.append(
                f"{vid} [{v.causal_status.value}] "
                f"({v.epistemic_status.value}): {v.statement}\n"
                f"  Scope: {', '.join(v.scope_conditions)}\n"
                f"  Excludes: {', '.join(v.scope_exclusions)}"
            )
        return '\n'.join(lines)
    
    def _get_active_rules(self, vyapti_ids: list[str]) -> str:
        """Get full rule descriptions for relevant vyāptis."""
        rules = []
        for vid in vyapti_ids:
            v = self.ks.vyaptis.get(vid)
            if v:
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
    
    def _get_active_constraints(self, vyapti_ids: list[str]) -> str:
        """Get hetvābhāsa descriptions relevant to active rules."""
        constraints = []
        for hid, h in self.ks.hetvabhasas.items():
            constraints.append(
                f"CONSTRAINT {hid} ({h.name}):\n"
                f"  Detection: {h.detection_signature}\n"
                f"  Correction: {h.correction_pattern}"
            )
        return '\n'.join(constraints)
    
    def _check_scope(
        self, predicates: list[str], rules: str
    ) -> list[str]:
        """Deterministic scope check — no LLM involved."""
        warnings = []
        for vid, v in self.ks.vyaptis.items():
            if vid in rules:
                for exclusion in v.scope_exclusions:
                    if any(exclusion.lower() in p.lower() 
                           for p in predicates):
                        warnings.append(
                            f"{vid} ({v.name}): scope exclusion "
                            f"'{exclusion}' matches query predicates"
                        )
        return warnings
    
    def _check_decay(self, rules: str) -> list[str]:
        """Deterministic decay check — no LLM involved."""
        warnings = []
        for vid, v in self.ks.vyaptis.items():
            if vid in rules and v.decay_risk in (
                DecayRisk.HIGH, DecayRisk.CRITICAL
            ):
                if v.last_verified:
                    age_days = (
                        datetime.now() - v.last_verified
                    ).days
                    if age_days > 180:  # 6 months
                        warnings.append(
                            f"{vid} ({v.name}): HIGH decay risk, "
                            f"last verified {age_days} days ago. "
                            f"Condition: {v.decay_condition}"
                        )
                else:
                    warnings.append(
                        f"{vid} ({v.name}): HIGH decay risk, "
                        f"NEVER verified. "
                        f"Condition: {v.decay_condition}"
                    )
        return warnings
    
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

#### 6.2.6 DSPy Optimization

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
        prediction.scope_warnings or prediction.decay_warnings
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

#### 6.2.7 What Phase 1 Gets Right and Wrong

**Gets right:**
- Clean separation of knowledge store, grounding, reasoning, synthesis
- Deterministic scope and decay checking (no LLM needed)
- Optimizable pipeline (DSPy compiler improves with data)
- Source tracking through the full chain
- Epistemic status propagation to output

**Gets wrong — and this is why we need Phase 2:**
- *Hetvābhāsa detection is unreliable*: Asking an LLM to detect its own reasoning fallacies is asking the system that makes errors to detect its own errors. The `dspy.Suggest` assertions are soft constraints — the LLM can override them.
- *Reasoning is not verifiable*: The LLM's "reasoning chain" is a text string, not a formal proof. We cannot verify that the conclusion actually follows from the premises. The chain of thought might skip steps, apply rules incorrectly, or introduce information not in the knowledge base.
- *No formal inference*: The "engine" is really just a structured prompt. It doesn't chain rules — it asks the LLM to chain rules and hopes it does so correctly.
- *Uncertainty is self-reported*: The confidence assessment is the LLM's own judgment, which is known to be poorly calibrated (LLMs are overconfident on wrong answers and underconfident on easy questions).

These limitations motivate Phase 2.

---

### 6.3 Phase 2: DSPy + Prolog — Why Boolean Logic with LLMs?

**The core question:** If the LLM can "reason" (sort of), why do we need a symbolic logic engine at all?

**The answer in one sentence:** Because an LLM that generates a plausible-sounding reasoning chain that contains a subtle scope violation is *more dangerous* than an LLM that says "I don't know" — and only a deterministic checker can guarantee the violation is caught.

#### 6.3.1 The Case for Symbolic Reasoning

Consider a concrete example. The knowledge store contains:

```
V3: Concentrated ownership enables long-horizon strategic investment
    Scope: private firms, family-controlled firms
    Excludes: public firms with activist investors, SPACs
    
V7: Long-horizon strategic investment creates sustainable competitive advantage
    Scope: stable market conditions
    Excludes: markets undergoing technological disruption
```

A user asks: "Will this SPAC's long-term investment strategy create a competitive advantage?"

Phase 1 (DSPy-only) will generate a plausible reasoning chain that might correctly identify V3 and V7 as relevant, might correctly chain them (V3 → V7), and might even mention the scope conditions. But "might" is the operative word. The LLM might also:
- Apply V3 despite the SPAC exclusion
- Chain V3 → V7 without checking that V7's scope (stable markets) is satisfied
- Generate a confident answer that sounds right but violates two scope conditions

Phase 2 (DSPy + Prolog) makes these errors **impossible**:

```prolog
% V3 formalized
long_horizon_investment_possible(Co) :-
    concentrated_ownership(Co),
    \+ public_with_activists(Co),
    \+ spac(Co).

% V7 formalized
sustainable_advantage(Co) :-
    long_horizon_investment_possible(Co),
    stable_market(Co),
    \+ technological_disruption(Co).

% Query: SPAC asks about competitive advantage
?- sustainable_advantage(the_spac).
% Prolog: FAILS at V3 (spac exclusion fires)
% Returns: NO — with trace showing exactly where and why
```

The Prolog engine doesn't "reason" about scope conditions — it enforces them as logical preconditions. The SPAC exclusion isn't a suggestion; it's a hard constraint that makes the proof fail. The trace shows exactly which precondition was unmet. No LLM judgment involved.

#### 6.3.2 The Architecture

```
User Query (NL)
      │
      ▼
┌──────────────────────────────┐
│  DSPy Module: QueryGrounding  │  ← LLM translates NL → predicates
│  (optimizable via MIPROv2)    │
└──────────┬───────────────────┘
           │ structured predicates
           ▼
┌──────────────────────────────┐
│  DETERMINISTIC LAYER          │  ← No LLM
│  ┌─────────────────────────┐ │
│  │ Scope Checker           │ │  Do predicates violate exclusions?
│  │ Decay Checker           │ │  Are rules stale?
│  │ Prerequisite Checker    │ │  Does the query assume unmet prereqs?
│  │ Query Type Router       │ │  Structural → Prolog, Semantic → RAG
│  └─────────────────────────┘ │
└──────────┬───────────────────┘
           │
      ┌────┴────┐
      │         │
      ▼         ▼
┌──────────┐ ┌──────────────────┐
│ PROLOG   │ │ GraphRAG         │
│ ENGINE   │ │ (T3 Corpus)      │
│          │ │                  │
│ Vyāptis  │ │ Chunks with      │
│ as rules │ │ metadata         │
│          │ │                  │
│ Hetvāb-  │ │ Graph structure  │
│ hāsas as │ │ from dependency  │
│ integrity│ │ DAG              │
│ constrnts│ │                  │
│          │ │                  │
│ Returns: │ │ Returns:         │
│ proof    │ │ relevant chunks  │
│ trace or │ │ with prereq      │
│ failure  │ │ checking         │
│ + reason │ │                  │
└────┬─────┘ └───────┬──────────┘
     │               │
     └───────┬───────┘
             ▼
┌──────────────────────────────┐
│  DSPy Module: Synthesizer     │  ← LLM verbalizes proof + prose
│  (optimizable via MIPROv2)    │
│                               │
│  dspy.Assert(                 │  ← Catches SYNTHESIS errors
│    response_matches_proof()   │     (not reasoning errors —
│  )                            │      Prolog catches those)
└──────────────────────────────┘
```

#### 6.3.3 Formalizing Vyāptis as Prolog Rules

The T2 compiler now includes a formalization step:

```python
# anvikshiki/t2_compiler_phase2.py
"""
T2 Compiler Phase 2: Formalize vyāptis as Prolog rules.

Uses the LLM to assist formalization, but the human
reviews and approves each rule. The LISP spec provides
the schema; the LLM fills in the specific predicates.
"""

import dspy


class FormalizeVyapti(dspy.Signature):
    """Convert a natural-language vyāpti into Prolog syntax."""
    
    vyapti_statement: str = dspy.InputField(
        desc="The vyāpti in natural language")
    scope_conditions: list[str] = dspy.InputField(
        desc="Conditions under which this rule applies")
    scope_exclusions: list[str] = dspy.InputField(
        desc="Conditions under which this rule does NOT apply")
    antecedents: list[str] = dspy.InputField(
        desc="Predicate names that must be true")
    consequent: str = dspy.InputField(
        desc="Predicate name that becomes true")
    
    prolog_rule: str = dspy.OutputField(
        desc="The vyāpti as a Prolog rule with scope guards")
    auxiliary_predicates: list[str] = dspy.OutputField(
        desc="Any helper predicates needed")


def generate_prolog_knowledge_base(
    knowledge_store: 'KnowledgeStore'
) -> str:
    """
    Generate the complete Prolog knowledge base from
    the verified architecture.
    
    Returns a .pl file contents string.
    """
    formalizer = dspy.ChainOfThought(FormalizeVyapti)
    
    rules = []
    rules.append("% ═══ ĀNVĪKṢIKĪ KNOWLEDGE BASE ═══")
    rules.append(f"% Domain: {knowledge_store.domain_type.name}")
    rules.append(f"% Generated from verified architecture")
    rules.append("")
    
    # Vyāptis as rules
    rules.append("% ─── VYĀPTIS (Domain Rules) ───")
    for vid, v in knowledge_store.vyaptis.items():
        result = formalizer(
            vyapti_statement=v.statement,
            scope_conditions=v.scope_conditions,
            scope_exclusions=v.scope_exclusions,
            antecedents=v.antecedents,
            consequent=v.consequent
        )
        rules.append(f"\n% {vid}: {v.name}")
        rules.append(f"% Status: {v.epistemic_status.value}")
        rules.append(f"% Confidence: {v.confidence.formulation}")
        rules.append(result.prolog_rule)
        for aux in result.auxiliary_predicates:
            rules.append(aux)
    
    # Hetvābhāsas as integrity constraints
    rules.append("\n% ─── HETVĀBHĀSAS (Integrity Constraints) ───")
    for hid, h in knowledge_store.hetvabhasas.items():
        rules.append(f"\n% {hid}: {h.name}")
        rules.append(f"% Detection: {h.detection_signature}")
        # Integrity constraints fire when violated
        rules.append(
            f"hetvabhasa_violation({hid.lower()}, Claim) :-"
        )
        rules.append(f"    {h.formal_constraint}.")
    
    # Epistemic metadata as facts
    rules.append("\n% ─── EPISTEMIC METADATA ───")
    for vid, v in knowledge_store.vyaptis.items():
        rules.append(
            f"epistemic_status({vid.lower()}, "
            f"{v.epistemic_status.value})."
        )
        rules.append(
            f"confidence({vid.lower()}, "
            f"{v.confidence.formulation})."
        )
        rules.append(
            f"decay_risk({vid.lower()}, "
            f"{v.decay_risk.value})."
        )
    
    # Dependency graph as facts
    rules.append("\n% ─── CONCEPT DEPENDENCIES ───")
    for concept, prereqs in knowledge_store.dependency_graph.items():
        for prereq in prereqs:
            rules.append(
                f"requires({concept.lower()}, "
                f"{prereq.lower()})."
            )
    
    # Validity check (decay-aware inference)
    rules.append("\n% ─── DECAY-AWARE INFERENCE ───")
    rules.append("valid_for_inference(Rule) :-")
    rules.append("    decay_risk(Rule, low).")
    rules.append("valid_for_inference(Rule) :-")
    rules.append("    decay_risk(Rule, moderate).")
    rules.append("valid_for_inference(Rule) :-")
    rules.append("    decay_risk(Rule, high),")
    rules.append("    last_verified(Rule, Date),")
    rules.append("    not_stale(Date).")
    rules.append("% Rules with high decay and no verification")
    rules.append("% CANNOT be used in inference — this is enforced.")
    
    return '\n'.join(rules)
```

#### 6.3.4 The Prolog Interface

```python
# anvikshiki/prolog_engine.py
"""
Interface to SWI-Prolog for deterministic inference.
Uses pyswip for Python-Prolog interop.
"""

from pyswip import Prolog


class PrologEngine:
    """Deterministic inference engine over formalized vyāptis."""
    
    def __init__(self, knowledge_base_path: str):
        self.prolog = Prolog()
        self.prolog.consult(knowledge_base_path)
    
    def query(self, goal: str) -> list[dict]:
        """
        Execute a Prolog query and return all solutions.
        Each solution is a dict of variable bindings.
        """
        try:
            results = list(self.prolog.query(goal, maxresult=100))
            return results
        except Exception as e:
            return [{"error": str(e)}]
    
    def prove(self, goal: str) -> tuple[bool, list[str]]:
        """
        Attempt to prove a goal. Returns (success, trace).
        The trace shows which rules were applied.
        """
        # Enable trace collection
        self.prolog.assertz(
            "trace_rule(Rule) :- "
            "assert(used_rule(Rule))"
        )
        
        results = self.query(goal)
        success = len(results) > 0 and "error" not in results[0]
        
        # Collect trace
        trace = [
            str(r["Rule"]) 
            for r in self.query("used_rule(Rule)")
        ]
        
        # Clean up
        self.prolog.retractall("used_rule(_)")
        
        return success, trace
    
    def check_hetvabhasas(
        self, claim: str
    ) -> list[dict]:
        """
        Check if a claim violates any hetvābhāsa constraint.
        Returns list of violations with fallacy ID and explanation.
        """
        violations = self.query(
            f"hetvabhasa_violation(H, {claim})"
        )
        return [
            {"hetvabhasa": v["H"], "claim": claim}
            for v in violations
            if "error" not in v
        ]
    
    def get_prerequisites(self, concept: str) -> list[str]:
        """
        Traverse the dependency graph to get ALL prerequisites
        for a concept, transitively.
        """
        results = self.query(
            f"requires({concept}, X)"
        )
        prereqs = [str(r["X"]) for r in results]
        
        # Transitive closure
        all_prereqs = set(prereqs)
        frontier = list(prereqs)
        while frontier:
            current = frontier.pop()
            deeper = self.query(f"requires({current}, X)")
            for r in deeper:
                x = str(r["X"])
                if x not in all_prereqs:
                    all_prereqs.add(x)
                    frontier.append(x)
        
        return sorted(all_prereqs)
    
    def check_validity(self, rule_id: str) -> tuple[bool, str]:
        """
        Check if a rule is currently valid for inference.
        Returns (valid, reason).
        """
        results = self.query(
            f"valid_for_inference({rule_id})"
        )
        if results and "error" not in results[0]:
            return True, "Valid"
        else:
            # Check why it failed
            decay = self.query(
                f"decay_risk({rule_id}, Risk)"
            )
            if decay:
                risk = str(decay[0].get("Risk", "unknown"))
                return False, (
                    f"Rule {rule_id} has {risk} decay risk "
                    f"and is not verified as current"
                )
            return False, f"Rule {rule_id} not found"
```

#### 6.3.5 What Phase 2 Achieves Over Phase 1

| Capability | Phase 1 (DSPy only) | Phase 2 (DSPy + Prolog) |
|-----------|---------------------|------------------------|
| Scope enforcement | LLM checks (unreliable) | Prolog preconditions (deterministic) |
| Fallacy detection | dspy.Suggest (soft) | Integrity constraints (hard) |
| Proof traces | CoT text (unverifiable) | Prolog proof tree (formal) |
| Prerequisite traversal | LLM guesses | Graph traversal (complete) |
| Decay checking | Python code (correct) | Prolog precondition (correct) |
| Novel inference | LLM generation | Forward/backward chaining |
| Grounding (NL → predicates) | DSPy (optimizable) | DSPy (optimizable) — unchanged |
| Verbalization | DSPy (optimizable) | DSPy (optimizable) — unchanged |

**The key architectural insight:** DSPy handles what LLMs are good at (natural language understanding and generation). Prolog handles what symbolic systems are good at (deterministic inference, constraint checking, proof construction). Each component does what it's actually good at.

**But Phase 2 has a fundamental limitation:** Prolog uses Boolean logic. A vyāpti either holds or it doesn't. A proof either succeeds or it fails. There is no room for "this rule holds with moderate confidence based on observational evidence" or "this conclusion is 70% certain because it depends on a working hypothesis." The epistemic metadata exists in the knowledge store but Prolog cannot use it during inference — it's carried alongside the proof, not integrated into the proof.

This motivates Phase 3.

---

### 6.4 Phase 3: DSPy + Prolog + UQ — Why Three Kinds of Uncertainty?

**The core question:** The engine now produces formally correct proofs. But the user doesn't just want to know *that* a conclusion follows — they want to know *how much they should trust it*. And "trust" decomposes into at least three distinct questions.

#### 6.4.1 The Three Uncertainties

**Epistemic Uncertainty (Type 1): "Do we have enough knowledge?"**

This is reducible uncertainty — it comes from gaps in the knowledge base. A vyāpti with `confidence.formulation = 0.4` is epistemically uncertain: we're not sure the rule is correctly stated. A claim that depends on an unverified source in the Reference Bank is epistemically uncertain. More evidence could reduce this uncertainty.

In the engine: computed deterministically from knowledge base metadata. No LLM involved.

```python
def compute_epistemic_uncertainty(proof_trace, knowledge_store):
    rules_used = [knowledge_store.vyaptis[r] for r in proof_trace]
    return {
        'weakest_confidence': min(
            r.confidence.formulation for r in rules_used),
        'unsourced_rules': [
            r.id for r in rules_used if not r.sources],
        'hypothesis_dependence': [
            r.id for r in rules_used 
            if r.epistemic_status == EpistemicStatus.WORKING_HYPOTHESIS],
        'contested_dependence': [
            r.id for r in rules_used 
            if r.epistemic_status == EpistemicStatus.ACTIVELY_CONTESTED],
    }
```

**Aleatoric Uncertainty (Type 2): "Is the domain inherently unpredictable here?"**

This is irreducible uncertainty — it comes from the nature of the domain itself. Business strategy (Type 4 Craft) has genuinely stochastic elements: market outcomes, competitor behavior, organizational dynamics. No amount of additional evidence eliminates this. The engine must communicate: "even if every rule is perfectly established, the outcome is uncertain because the world is uncertain."

In the engine: computed from domain type, scenario forks, and scope condition sensitivity.

```python
def compute_aleatoric_uncertainty(proof_trace, knowledge_store):
    rules_used = [knowledge_store.vyaptis[r] for r in proof_trace]
    return {
        'domain_base_uncertainty': {
            DomainType.FORMAL: 0.0,
            DomainType.MECHANISTIC: 0.1,
            DomainType.EMPIRICAL: 0.3,
            DomainType.CRAFT: 0.5,
            DomainType.INTERPRETIVE: 0.6,
        }.get(knowledge_store.domain_type, 0.5),
        'scope_sensitivity': sum(
            len(r.scope_conditions) for r in rules_used) / 
            max(len(rules_used), 1),
        'decay_exposure': sum(
            1 for r in rules_used 
            if r.decay_risk in (DecayRisk.HIGH, DecayRisk.CRITICAL)
        ) / max(len(rules_used), 1),
    }
```

**Inference Uncertainty (Type 3): "Did the LLM correctly translate between natural language and formal reasoning?"**

This is the uncertainty introduced by the grounding and synthesis modules — the LLM layers that translate NL→predicates and proof traces→NL. The Prolog proof is deterministic, but was the query correctly grounded? Did the synthesizer faithfully represent the proof?

In the engine: estimated via ensemble sampling of the grounding step and consistency checking of the synthesis step.

```python
def compute_inference_uncertainty(
    query, engine, n_samples=5
):
    """
    Run grounding multiple times and measure agreement.
    High agreement → low inference uncertainty.
    Low agreement → query is ambiguous or grounding is unreliable.
    """
    groundings = []
    for _ in range(n_samples):
        g = engine.grounder(
            query=query,
            domain_type=engine.ks.domain_type.name,
            available_vyaptis=engine._format_vyaptis()
        )
        groundings.append(set(g.relevant_vyaptis))
    
    # Measure agreement: Jaccard similarity across all pairs
    total_sim = 0
    pairs = 0
    for i in range(len(groundings)):
        for j in range(i+1, len(groundings)):
            intersection = groundings[i] & groundings[j]
            union = groundings[i] | groundings[j]
            if union:
                total_sim += len(intersection) / len(union)
            pairs += 1
    
    avg_similarity = total_sim / max(pairs, 1)
    
    return {
        'grounding_agreement': avg_similarity,
        'consensus_vyaptis': list(
            set.intersection(*groundings)),
        'disputed_vyaptis': list(
            set.union(*groundings) - set.intersection(*groundings)),
        'inference_uncertainty': 1.0 - avg_similarity,
    }
```

#### 6.4.2 Conformal Prediction for Source Grounding

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

#### 6.4.3 The Complete UQ-Aware Response

```python
# anvikshiki/engine_phase3.py (excerpt)

def produce_calibrated_response(
    self, query, proof_result, retrieved_chunks
):
    """Produce a response with full uncertainty decomposition."""
    
    # Three uncertainty types
    epistemic = compute_epistemic_uncertainty(
        proof_result.trace, self.ks)
    aleatoric = compute_aleatoric_uncertainty(
        proof_result.trace, self.ks)
    inference = compute_inference_uncertainty(
        query, self)
    
    # Source verification with conformal guarantee
    claim_verifications = []
    for claim in proof_result.derived_claims:
        sources = self._get_sources_for_claim(claim)
        verification = self.conformal.verify_claim(
            claim, sources)
        claim_verifications.append(verification)
    
    # Compose uncertainty report
    uncertainty_report = {
        'epistemic': epistemic,
        'aleatoric': aleatoric,
        'inference': inference,
        'source_verification': claim_verifications,
        'total_confidence': self._aggregate_confidence(
            epistemic, aleatoric, inference,
            claim_verifications
        ),
    }
    
    # Synthesize with uncertainty awareness
    response = self.synthesizer(
        query=query,
        reasoning_chain=proof_result.trace_text,
        retrieved_prose='\n'.join(retrieved_chunks),
        epistemic_statuses=str(epistemic),
        uncertainty_report=str(uncertainty_report),
    )
    
    return response, uncertainty_report
```

#### 6.4.4 What Phase 3 Achieves Over Phase 2

Phase 3 transforms the engine from a system that says "yes/no" to one that says "yes with this much confidence, for these reasons, with these caveats":

- **Epistemic**: "This depends on V7, which is a working hypothesis — treat as tentative"
- **Aleatoric**: "Business strategy is inherently uncertain; even a perfect analysis can't predict market reactions"
- **Inference**: "The grounding was stable (5/5 samples agreed), so the NL→logic translation is reliable"
- **Source**: "With 90% statistical confidence, this claim is grounded in the Reference Bank"

**But Phase 3 still has the Boolean problem.** Prolog's inference is all-or-nothing. The epistemic metadata is computed *after* inference — it annotates the proof but doesn't affect it. A vyāpti with `epistemic_status = WORKING_HYPOTHESIS` is treated identically to one with `epistemic_status = ESTABLISHED` during the proof itself. The uncertainty is bolt-on, not structural.

This motivates Phase 4.

---

### 6.5 Phase 4: DSPy + Heyting + UQ — Why Topos?

**The core question:** What if uncertainty were not an annotation on a Boolean proof, but a *structural property of the logic itself*?

#### 6.5.1 The Boolean Limitation

In Prolog (and all classical logic), a proposition is either true or false. The law of excluded middle holds: P ∨ ¬P is always true. This means:

- A vyāpti either fires or it doesn't. There's no "fires with moderate confidence."
- A proof either succeeds or fails. There's no "mostly proven, with a gap at step 3."
- A scope condition is either met or not. There's no "partially in scope."
- Negation-as-failure means anything not provable is assumed false — the closed-world assumption.

But domain knowledge isn't Boolean. "Concentrated ownership enables long-horizon strategy" is not simply true or false — it's ESTABLISHED in some contexts, a WORKING HYPOTHESIS in others, and GENUINELY OPEN in edge cases. A proof that chains through a working hypothesis should carry that qualification through to its conclusion, not lose it.

#### 6.5.2 Heyting Algebras: The Right Truth Values

A Heyting algebra is a generalization of Boolean algebra where the law of excluded middle may fail. Instead of {true, false}, truth values form a lattice where implications are defined by the "relative pseudo-complement":

```
a → b = greatest c such that c ∧ a ≤ b
```

The Ānvīkṣikī epistemic status markers form a natural Heyting algebra:

```
ESTABLISHED > WORKING_HYPOTHESIS > GENUINELY_OPEN > ACTIVELY_CONTESTED

With lattice operations:
  ∧ (meet/AND): min of two statuses
  ∨ (join/OR):  max of two statuses
  →(implication): if a ≤ b then ESTABLISHED, else b
  ¬ (negation):  ¬ESTABLISHED = ACTIVELY_CONTESTED
                 ¬ACTIVELY_CONTESTED ≠ ESTABLISHED  (!)
```

The critical difference: `¬¬ESTABLISHED ≠ ESTABLISHED` in general. Double negation elimination fails. This is correct! "It's not the case that this is not established" does NOT mean "this is established" — it might be a working hypothesis. Intuitionistic logic captures this naturally.

#### 6.5.3 Implementation: The Heyting-Valued Logic Engine

```python
# anvikshiki/heyting.py
"""
Heyting-valued logic engine for epistemic reasoning.

Replaces Boolean Prolog with a lattice-valued inference
engine where truth values carry epistemic qualification.
"""

from enum import IntEnum
from dataclasses import dataclass
from typing import Optional


class EpistemicValue(IntEnum):
    """
    Heyting algebra of epistemic truth values.
    Ordered: ESTABLISHED > HYPOTHESIS > OPEN > CONTESTED > BOTTOM
    """
    BOTTOM = 0          # Definitely false / no evidence
    CONTESTED = 1       # ⚡ Actively contested
    OPEN = 2            # ? Genuinely open
    HYPOTHESIS = 3      # ~ Working hypothesis
    ESTABLISHED = 4     # ✓ Established
    
    def __and__(self, other):
        """Meet (AND): minimum epistemic value."""
        return EpistemicValue(min(self.value, other.value))
    
    def __or__(self, other):
        """Join (OR): maximum epistemic value."""
        return EpistemicValue(max(self.value, other.value))
    
    def implies(self, other):
        """
        Heyting implication: a → b.
        If a ≤ b: returns ESTABLISHED (implication trivially true)
        Else: returns b (implication is as strong as consequent)
        """
        if self.value <= other.value:
            return EpistemicValue.ESTABLISHED
        return other
    
    def negate(self):
        """
        Intuitionistic negation: ¬a = a → BOTTOM.
        Note: ¬¬a ≠ a in general!
        """
        return self.implies(EpistemicValue.BOTTOM)


@dataclass
class HeytingFact:
    """A fact with an epistemic truth value."""
    predicate: str
    arguments: tuple
    value: EpistemicValue
    provenance: str = ""  # Which vyāpti/source established this


@dataclass 
class HeytingRule:
    """A vyāpti as a Heyting-valued rule."""
    vyapti_id: str
    name: str
    antecedents: list[str]       # Predicate patterns
    consequent: str              # Predicate pattern
    rule_confidence: EpistemicValue  # The rule's own epistemic status
    scope_conditions: list[str]
    scope_exclusions: list[str]
    
    def apply(
        self, 
        fact_base: dict[str, HeytingFact]
    ) -> Optional[HeytingFact]:
        """
        Apply this rule to the fact base.
        
        The resulting fact's epistemic value is the MEET (minimum) of:
        1. The rule's own epistemic status
        2. All antecedent facts' epistemic values
        
        This is the key insight: epistemic qualification
        propagates THROUGH inference, not alongside it.
        """
        antecedent_values = []
        
        for ant_pattern in self.antecedents:
            matching_facts = [
                f for f in fact_base.values()
                if self._matches(ant_pattern, f.predicate)
            ]
            
            if not matching_facts:
                return None  # Antecedent not satisfied
            
            # Take the best matching fact
            best = max(matching_facts, key=lambda f: f.value)
            antecedent_values.append(best.value)
        
        # Consequent value = meet of rule confidence 
        # and all antecedent values
        result_value = self.rule_confidence
        for av in antecedent_values:
            result_value = result_value & av  # Meet operation
        
        return HeytingFact(
            predicate=self.consequent,
            arguments=(),
            value=result_value,
            provenance=f"Derived via {self.vyapti_id}: "
                       f"rule={self.rule_confidence.name}, "
                       f"antecedents={[v.name for v in antecedent_values]}"
        )
    
    def _matches(self, pattern: str, predicate: str) -> bool:
        """Simple pattern matching for predicate names."""
        return pattern.lower() in predicate.lower()


class HeytingEngine:
    """
    Forward-chaining inference engine with Heyting-valued logic.
    
    Unlike Prolog (which is backward-chaining and Boolean),
    this engine:
    1. Chains forward from known facts
    2. Carries epistemic values through inference
    3. Propagates qualification: a chain through a HYPOTHESIS
       produces at most a HYPOTHESIS
    4. Detects when epistemic value degrades below threshold
    """
    
    def __init__(self):
        self.facts: dict[str, HeytingFact] = {}
        self.rules: list[HeytingRule] = []
        self.inference_trace: list[str] = []
    
    def add_fact(self, fact: HeytingFact):
        """Add a fact to the knowledge base."""
        key = f"{fact.predicate}({','.join(str(a) for a in fact.arguments)})"
        # If fact already exists, take the JOIN (maximum value)
        if key in self.facts:
            existing = self.facts[key]
            self.facts[key] = HeytingFact(
                predicate=fact.predicate,
                arguments=fact.arguments,
                value=existing.value | fact.value,
                provenance=f"{existing.provenance} | {fact.provenance}"
            )
        else:
            self.facts[key] = fact
    
    def add_rule(self, rule: HeytingRule):
        """Add a rule to the rule base."""
        self.rules.append(rule)
    
    def forward_chain(
        self, max_iterations: int = 100
    ) -> list[HeytingFact]:
        """
        Run forward chaining until fixpoint or max iterations.
        Returns all newly derived facts.
        """
        new_facts = []
        
        for i in range(max_iterations):
            any_new = False
            
            for rule in self.rules:
                result = rule.apply(self.facts)
                
                if result is not None:
                    key = f"{result.predicate}({','.join(str(a) for a in result.arguments)})"
                    
                    if key not in self.facts or \
                       result.value > self.facts[key].value:
                        self.add_fact(result)
                        new_facts.append(result)
                        self.inference_trace.append(
                            f"Step {len(self.inference_trace)+1}: "
                            f"{rule.vyapti_id} → "
                            f"{result.predicate} = "
                            f"{result.value.name}\n"
                            f"  {result.provenance}"
                        )
                        any_new = True
            
            if not any_new:
                break  # Fixpoint reached
        
        return new_facts
    
    def query(
        self, predicate: str, min_confidence: EpistemicValue = EpistemicValue.BOTTOM
    ) -> list[HeytingFact]:
        """
        Query the knowledge base for facts matching a predicate,
        filtered by minimum epistemic value.
        """
        results = [
            f for f in self.facts.values()
            if predicate.lower() in f.predicate.lower()
            and f.value >= min_confidence
        ]
        return sorted(results, key=lambda f: f.value, reverse=True)
    
    def explain(self, predicate: str) -> str:
        """
        Produce a human-readable explanation of how a fact
        was derived, including epistemic qualification at each step.
        """
        facts = self.query(predicate)
        if not facts:
            return f"No facts matching '{predicate}' in the knowledge base."
        
        explanations = []
        for fact in facts:
            explanations.append(
                f"FACT: {fact.predicate}\n"
                f"  VALUE: {fact.value.name}\n"
                f"  PROVENANCE: {fact.provenance}\n"
            )
        
        return '\n'.join(explanations)
```

#### 6.5.4 Cellular Sheaf Structure

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
from .heyting import EpistemicValue, HeytingFact


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

#### 6.5.5 The Complete Phase 4 Engine

```python
# anvikshiki/engine_phase4.py
"""
Phase 4: The complete Ānvīkṣikī Engine.

DSPy (grounding + synthesis) 
+ Heyting-valued logic (epistemic inference)
+ Cellular sheaf (consistency + hetvābhāsa detection)
+ Conformal prediction (source verification)
+ Three-way uncertainty decomposition

This is the target architecture.
"""

import dspy
from .schema import KnowledgeStore
from .heyting import HeytingEngine, HeytingFact, HeytingRule, EpistemicValue
from .sheaf import KnowledgeSheaf
from .conformal import ConformalSourceVerifier
from .engine_phase1 import GroundQuery, SynthesizeResponse


class AnvikshikiEngineV4(dspy.Module):
    """
    The complete neurosymbolic engine.
    
    Architecture:
    
    DSPy Grounding (optimizable, ensemble for UQ)
         │
         ▼
    Deterministic Guards (scope, decay, prerequisite)
         │
         ▼
    ┌────┴────┐
    │         │
    ▼         ▼
    Heyting   GraphRAG
    Engine    Retrieval
    (infer)   (retrieve)
    │         │
    └────┬────┘
         │
         ▼
    Sheaf Consistency Check (cohomological)
         │
         ▼
    Conformal Source Verification
         │
         ▼
    DSPy Synthesis (optimizable, assertion-guarded)
         │
         ▼
    Calibrated Response + Uncertainty Decomposition
    """
    
    def __init__(
        self, 
        knowledge_store: KnowledgeStore,
        sheaf: KnowledgeSheaf,
        conformal: ConformalSourceVerifier,
    ):
        super().__init__()
        self.ks = knowledge_store
        self.sheaf = sheaf
        self.conformal = conformal
        
        # Heyting engine with loaded rules
        self.heyting = HeytingEngine()
        self._load_heyting_rules()
        
        # DSPy modules (the NL interface)
        self.grounder = dspy.ChainOfThought(GroundQuery)
        self.synthesizer = dspy.ChainOfThought(SynthesizeResponse)
    
    def _load_heyting_rules(self):
        """Load vyāptis as Heyting-valued rules."""
        epistemic_map = {
            'established': EpistemicValue.ESTABLISHED,
            'hypothesis': EpistemicValue.HYPOTHESIS,
            'open': EpistemicValue.OPEN,
            'contested': EpistemicValue.CONTESTED,
        }
        
        for vid, v in self.ks.vyaptis.items():
            rule = HeytingRule(
                vyapti_id=vid,
                name=v.name,
                antecedents=v.antecedents,
                consequent=v.consequent,
                rule_confidence=epistemic_map.get(
                    v.epistemic_status.value,
                    EpistemicValue.HYPOTHESIS
                ),
                scope_conditions=v.scope_conditions,
                scope_exclusions=v.scope_exclusions,
            )
            self.heyting.add_rule(rule)
    
    def forward(self, query: str, retrieved_chunks: list[str]):
        # ── STEP 1: Grounding with ensemble UQ ──
        groundings = []
        for _ in range(5):
            g = self.grounder(
                query=query,
                domain_type=self.ks.domain_type.name,
                available_vyaptis=self._format_vyaptis()
            )
            groundings.append(g)
        
        # Consensus grounding
        all_vyapti_sets = [
            set(g.relevant_vyaptis) for g in groundings
        ]
        consensus = set.intersection(*all_vyapti_sets)
        disputed = set.union(*all_vyapti_sets) - consensus
        grounding_confidence = (
            len(consensus) / 
            max(len(consensus) + len(disputed), 1)
        )
        
        # If grounding too uncertain, ask for clarification
        if grounding_confidence < 0.4:
            return dspy.Prediction(
                response=(
                    "I need clarification to answer precisely. "
                    "The question could involve: "
                    f"{', '.join(disputed)}. "
                    "Could you specify which aspect?"
                ),
                uncertainty={
                    'type': 'inference',
                    'grounding_confidence': grounding_confidence,
                    'action': 'clarification_requested'
                }
            )
        
        # Use consensus grounding
        grounding = groundings[0]  # Take first, replace vyaptis
        grounding.relevant_vyaptis = list(consensus | disputed)
        
        # ── STEP 2: Deterministic guards ──
        scope_warnings = self._check_scope(
            grounding.predicates, grounding.relevant_vyaptis)
        decay_warnings = self._check_decay(
            grounding.relevant_vyaptis)
        
        # ── STEP 3: Assert grounded facts into Heyting engine ──
        for pred in grounding.predicates:
            self.heyting.add_fact(HeytingFact(
                predicate=pred,
                arguments=(),
                value=EpistemicValue.ESTABLISHED,
                provenance="query_grounding"
            ))
        
        # ── STEP 4: Forward chain with epistemic propagation ──
        derived = self.heyting.forward_chain()
        
        # ── STEP 5: Sheaf consistency check ──
        # Build a section from the inference results
        section = self._build_section_from_inference(derived)
        hetvabhasa_violations = self.sheaf.detect_hetvabhasas(
            section)
        
        # ── STEP 6: Conformal source verification ──
        verifications = []
        for fact in derived:
            sources = self._get_sources(fact)
            if sources:
                v = self.conformal.verify_claim(
                    fact.predicate, sources)
                verifications.append(v)
        
        # ── STEP 7: Compose uncertainty ──
        uncertainty = {
            'epistemic': {
                'weakest_rule': min(
                    (f.value.name for f in derived),
                    default="N/A"
                ),
                'hypothesis_chain': any(
                    f.value <= EpistemicValue.HYPOTHESIS 
                    for f in derived
                ),
            },
            'aleatoric': {
                'domain_type': self.ks.domain_type.name,
                'scope_sensitivity': len(scope_warnings),
                'decay_exposure': len(decay_warnings),
            },
            'inference': {
                'grounding_confidence': grounding_confidence,
                'disputed_vyaptis': list(disputed),
            },
            'consistency': {
                'hetvabhasa_violations': len(
                    hetvabhasa_violations),
                'violations': [
                    v['interpretation'] 
                    for v in hetvabhasa_violations
                ],
            },
            'source_verification': {
                'verified_claims': sum(
                    1 for v in verifications if v['supported']
                ),
                'total_claims': len(verifications),
                'coverage_guarantee': (
                    self.conformal.alpha 
                    if verifications else None
                ),
            },
        }
        
        # ── STEP 8: Synthesize with full context ──
        context = '\n'.join(retrieved_chunks)
        trace = '\n'.join(self.heyting.inference_trace)
        
        # Add warnings to context
        if scope_warnings:
            context += (
                f"\n\nSCOPE WARNINGS: "
                f"{'; '.join(scope_warnings)}"
            )
        if decay_warnings:
            context += (
                f"\n\nDECAY WARNINGS: "
                f"{'; '.join(decay_warnings)}"
            )
        if hetvabhasa_violations:
            context += (
                f"\n\nCONSISTENCY VIOLATIONS: "
                f"{'; '.join(v['interpretation'] for v in hetvabhasa_violations)}"
            )
        
        response = self.synthesizer(
            query=query,
            reasoning_chain=trace,
            retrieved_prose=context,
            epistemic_statuses=str(uncertainty),
        )
        
        # Assert synthesis faithfulness
        dspy.Assert(
            self._synthesis_matches_proof(
                response.response, derived),
            "Response must faithfully represent "
            "the proof trace — no hallucinated claims"
        )
        
        return dspy.Prediction(
            response=response.response,
            confidence=response.stated_confidence,
            sources=response.sources_cited,
            uncertainty=uncertainty,
            proof_trace=self.heyting.inference_trace,
            hetvabhasa_violations=hetvabhasa_violations,
        )
    
    # ... helper methods from previous phases ...
```

#### 6.5.6 Why Topos Theory Matters Here

The Phase 4 architecture is, mathematically, a **presheaf of Heyting-valued facts over the vyāpti graph, equipped with a sheaf condition that detects reasoning inconsistencies as cohomological obstructions**.

In simpler language:

1. **The Heyting algebra** replaces Boolean truth with epistemic qualification. A proof through a HYPOTHESIS produces at most a HYPOTHESIS. This is structurally correct — uncertainty propagates through inference, not alongside it.

2. **The cellular sheaf** replaces flat constraint checking with local-to-global consistency. A hetvābhāsa is not just a keyword match — it's a formal obstruction to extending local reasoning to a global conclusion. Survivorship bias means: your reasoning works in the scope of successful companies (local section) but fails when you include failures (no global section). The sheaf cohomology group H¹ measures exactly these obstructions.

3. **The subobject classifier Ω** of the topos is the Heyting algebra itself. In classical logic, Ω = {true, false}. In our topos, Ω = {ESTABLISHED, HYPOTHESIS, OPEN, CONTESTED, BOTTOM}. This means the logic of the entire system — not just the facts, but the rules of inference — operates over qualified truth values.

4. **The topology** (in the categorical sense) encodes scope conditions. An "open set" is a scope — "private companies," "stable markets," "post-2020 regulatory environment." The sheaf condition says: you can claim a vyāpti globally only if it glues consistently across all relevant scopes. If it doesn't, the system knows the claim is scope-dependent and reports which scopes it holds in.

This is not a metaphor — it's the mathematical content. The engine IS a presheaf topos over a finite site, and the inference IS computing sections.

---

## 7. What Is Truly Novel

Several aspects of this architecture have no precedent in the literature:

**1. Epistemic-status-propagating inference.**
No existing neurosymbolic system propagates epistemic qualification *through* inference chains. Logic engines use Boolean truth. LLMs report confidence as a separate channel. The Heyting-valued engine makes epistemic qualification structural: a chain through a hypothesis yields at most a hypothesis, by the rules of the logic itself, not by a post-hoc annotation.

**2. Hetvābhāsa as cohomological obstruction.**
The identification of reasoning fallacies with sheaf cohomology classes is, to our knowledge, new. Survivorship bias, scope violation, and scale extrapolation — traditionally treated as informal warning labels — become computable invariants of the knowledge graph's sheaf structure. H¹ ≠ 0 is a mathematical certificate that the reasoning contains a gluing failure.

**3. Decay-as-inference-precondition.**
Existing knowledge systems treat temporal validity as metadata. The Ānvīkṣikī engine makes validity a precondition for inference: a stale rule cannot fire. The Prolog implementation makes this a hard constraint; the Heyting implementation degrades the rule's epistemic value over time, which propagates through any chain that uses it.

**4. Three-way uncertainty decomposition with heterogeneous methods.**
The decomposition into epistemic (metadata computation), aleatoric (domain classification), and inference (ensemble sampling) uncertainty, each using the method appropriate to its nature, is not found in existing UQ frameworks for LLMs. Most LLM UQ methods estimate total uncertainty from output distributions. We compute each component from its natural source.

**5. Conformal prediction over a structured Reference Bank.**
Applying conformal prediction not to generic RAG retrieval but to a reference bank with known provenance chains gives statistical guarantees that are meaningful — the guarantee is not just "a relevant chunk was retrieved" but "this specific claim is supported by this specific source with this coverage level."

**6. The Ānvīkṣikī-to-Horn-clause correspondence.**
The observation that Nyāya vyāptis map directly to Horn clauses, hetvābhāsas to integrity constraints, and the pañcāvayava to structured proof traces connects a 2,500-year-old epistemological framework to modern logic programming in a way that is both historically interesting and practically useful.

---

## 8. Limitations

**The grounding problem is unsolved.** The LLM-based translation from natural language to structured predicates is the weakest link. DSPy makes it optimizable, but correctness is never guaranteed. Adversarial or deeply ambiguous queries will be misgrounded, and the engine will produce formally correct but practically wrong answers. Garbage in, garbage out — with formal proofs attached.

**The knowledge base is manually constructed.** The T2 compiler requires a human expert to verify the architecture output. The LLM-assisted formalization (NL vyāpti → Prolog rule) needs human review. This is by design (domain experts should validate domain rules) but limits scalability.

**The Heyting algebra is coarse.** Four epistemic values (plus bottom) is a very simple lattice. Real epistemic qualification is more nuanced — a claim might be "established in the American context but contested in the European context" in ways that a single lattice value cannot capture. A richer Heyting algebra (or a proper sheaf of Heyting algebras over the scope topology) would be more accurate but significantly more complex.

**Sheaf cohomology on large graphs is expensive.** The sheaf Laplacian is a dense matrix of dimension (n_nodes × stalk_dim)². For a knowledge base with thousands of concepts and dozens of dimensions, this becomes computationally prohibitive. Sparse approximations (sheaf sparsifiers, à la Hansen & Ghrist) would be needed for production scale.

**The system does not learn from interaction.** DSPy optimization improves prompts, but the Heyting engine and sheaf structure are static after compilation. A truly adaptive system would update rule confidences, add new vyāptis, and refine scope conditions based on query outcomes. This is a clear direction for future work.

**Type 4 (Craft) domains resist complete formalization.** Business strategy — the motivating domain — relies heavily on tacit knowledge, analogical reasoning, and practitioner judgment that cannot be fully captured in production rules. The T3 (prose retrieval) layer exists precisely to cover this gap, but the division between "what's formalizable" and "what's ineffable" is itself a matter of judgment.

---

## 9. Further Directions

**1. Temporal sheaves for decay.** Instead of binary "stale/fresh" markers, model decay as a sheaf over a time category. A vyāpti's truth value varies with time, and the restriction maps along the time axis encode how confidence degrades. This would give decay-aware inference where the engine doesn't just check "is this stale?" but "how much has this degraded since verification?" — a continuous, not discrete, question.

**2. Bayesian sheaf neural networks for learned restriction maps.** Rather than hand-specifying the restriction maps (how concepts relate across vyāpti edges), learn them from data using the Bayesian sheaf neural network framework (Gillespie et al., 2024). This would let the engine discover relational structure in the knowledge base that the human architect missed, with principled uncertainty over the learned structure itself.

**3. Multi-domain topos composition via geometric morphisms.** When two domain guides exist (e.g., corporate strategy + financial accounting), their knowledge bases are different topoi. A geometric morphism between them would formalize how knowledge transfers: what accounting facts are relevant to strategy reasoning, and vice versa. Caramello's "toposes as bridges" methodology provides the theoretical framework; implementation would require defining appropriate sites for each domain and constructing the functors.

**4. Active learning for the grounding module.** When the grounding ensemble disagrees (high inference uncertainty), instead of just asking for clarification, the system could identify *which specific ambiguity* would most reduce uncertainty and ask a targeted question. This connects to the "underspecification uncertainty" framework (position paper, ICML 2025).

**5. DSPy optimization over the full pipeline.** Currently, DSPy optimizes the grounding and synthesis modules independently. A future version could define an end-to-end metric that jointly optimizes grounding accuracy, inference depth, and synthesis faithfulness, using the Heyting engine's epistemic values as a differentiable signal.

**6. Integration with the meta-prompt as a feedback loop.** When the engine discovers a gap (query touches an area with no relevant vyāptis, or decay markers fire across an entire subgraph), it could trigger a targeted re-run of Stage 3 (Research Gate) to update the knowledge base. This would close the loop between query-time inference and compile-time knowledge construction.

---

## 10. References

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


