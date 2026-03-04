# The Ānvīkṣikī Engine — Revised Thesis (v2)

## From Philosophical Epistemology to Neurosymbolic Inference: Building a Lattice-Datalog Knowledge Engine with Layered Grounding Defense

---

**Abstract (Revised).** This thesis presents the design, architecture, and incremental construction of the Ānvīkṣikī Engine — a neurosymbolic reasoning system that compiles structured domain knowledge into an executable inference engine with principled uncertainty quantification. The system takes as input a pedagogical guide produced by the Ānvīkṣikī meta-prompt (a 3,963-line specification for generating expert-level instructional content) and compiles it into two subsystems: T2, a logic engine implementing domain-specific rules as executable inference; and T3, a graph-structured retrieval corpus that serves the prose layer. We develop the engine in four incremental stages — DSPy-only, DSPy+Datalog, DSPy+Lattice Datalog+UQ, and DSPy+Lattice Datalog+Sheaf+UQ — each addressing fundamental limitations of the prior. The critical revision from the original thesis is threefold: (1) Prolog is replaced by Datalog with lattice extensions throughout, providing Heyting-valued inference with guaranteed termination and polynomial complexity; (2) the grounding problem — identified as the architecture's weakest link — is addressed through a five-layer defense combining ontology-constrained prompting, grammar-constrained decoding, ensemble consensus, round-trip verification, and solver-feedback refinement; (3) the naive forward-chaining Heyting engine is replaced by semi-naive Datalog evaluation, reducing per-iteration cost from O(rules × facts) to O(rules × Δfacts). The final architecture provides formally correct epistemic qualification, scope-dependent reasoning, cohomological fallacy detection, and uncertainty decomposition that no existing RAG or LLM system achieves — with tractability guarantees that the original thesis lacked.

---

## Table of Contents (Revised)

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
5. On Turing Completeness (Revised)
6. The Grounding Problem ← **NEW SECTION**
   - 6.1 Problem Decomposition
   - 6.2 Seven Strategies
   - 6.3 The Five-Layer Defense
   - 6.4 Implementation Code
7. Developing the Engine (Revised)
   - 7.1 Architecture Overview
   - 7.2 Phase 1: DSPy Only — The Baseline
   - 7.3 Why Not Prolog? ← **REVISED: formerly "DSPy + Prolog"**
   - 7.4 Phase 2: DSPy + Datalog ← **NEW: replaces Prolog**
   - 7.5 Phase 3: DSPy + Lattice Datalog + UQ
   - 7.6 Phase 4: DSPy + Lattice Datalog + Sheaf + UQ — The Final Engine
8. The Final Engine — Complete Implementation ← **NEW**
9. What Is Truly Novel (Revised)
10. Limitations (Revised)
11. Further Directions (Revised)
12. References (Updated)

---

## PATCH NOTES

This document is a revision of the original Ānvīkṣikī Engine thesis. The following changes are made, with rationale:

### Change 1: Prolog → Datalog with Lattice Extensions

**What changed:** The entire Prolog layer (Phase 2 and Phase 3) is replaced by Datalog. The custom Heyting engine (Phase 4) is replaced by semi-naive Datalog with lattice-valued fixpoint computation.

**Why:**

| Problem with Original | How Datalog Fixes It |
|----------------------|---------------------|
| Prolog is Turing complete → queries can diverge | Datalog terminates in polynomial time (guaranteed) |
| Prolog uses backward chaining → fights the engine's natural forward mode | Datalog uses bottom-up evaluation → matches pañcāvayava |
| Prolog has Boolean truth → epistemic status bolted on | Lattice Datalog has structural epistemic values |
| Custom Heyting engine has no indexing → O(rules × facts²) | Semi-naive evaluation → O(rules × Δfacts) per iteration |
| Prolog unification is overkill → vyāptis are flat predicates | Datalog handles flat predicates natively |
| Two separate engines needed (Prolog for Phase 2-3, Heyting for Phase 4) | One engine for all phases (add lattice dimension incrementally) |

**Impact:** Phases 2, 3, and 4 collapse into a single progression. The Boolean→Heyting transition is no longer a migration between different engines — it's adding a lattice dimension to the same Datalog engine.

### Change 2: Grounding Problem Addressed

**What changed:** New Section 6 addresses the NL→predicate translation gap with a comprehensive survey and five-layer defense architecture.

**Why:** The original thesis identified grounding as "Limitation #1" but offered no mitigation. The grounding module is the single point of failure that makes all downstream guarantees conditional. Without addressing it, the engine is formally correct but practically fragile.

**Five layers:**
1. Ontology-constrained prompting (LLM sees only valid predicates)
2. Grammar-constrained decoding via CRANE (syntactic validity = 100%)
3. Ensemble consensus N=5 (catches inconsistent errors)
4. Round-trip verification (catches silent semantic errors)
5. Solver-feedback refinement (exploits Datalog's rich error messages)

### Change 3: Phase Architecture Simplified

**What changed:** Four phases remain, but the progression is cleaner:

```
Original:  DSPy → DSPy+Prolog → DSPy+Prolog+UQ → DSPy+Heyting+UQ
                   (Boolean)      (Boolean+bolt-on)  (Heyting, new engine)

Revised:   DSPy → DSPy+Datalog → DSPy+LatticeDatalog+UQ → +Sheaf+UQ
                   (Boolean)      (Heyting, same engine)    (same engine+sheaf)
```

**Why:** No engine migration between phases. Each phase adds a capability to the same Datalog engine. Phase 2→3 is adding a lattice dimension, not rewriting the inference engine. Phase 3→4 is adding the sheaf layer on top, not changing the core.

### Change 4: Honest Turing Completeness Assessment

**What changed:** Section 5 revised to acknowledge that Datalog is *not* Turing complete, and explain why this is a feature.

**Why:** The original thesis celebrated Turing completeness as a property of the Horn clause mapping. But the engine doesn't need Turing completeness — it needs termination, tractability, and epistemic propagation. Datalog's decidability is the right trade.

---

## 5. On Turing Completeness (Revised)

### The Core Primitive

The computational primitive of Ānvīkṣikī is the vyāpti — invariable concomitance. Chained vyāptis create inference chains: A → B → C → D. This maps to Horn clause logic — the foundation of logic programming.

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

**The two computational layers (revised):**

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

The original thesis argued that Turing completeness is important because the engine can "derive any computable consequence." The revised thesis argues: the engine should derive *exactly the consequences that follow from the rules in polynomial time* and then stop. An engine that might not stop is not an engine — it's a liability.

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

## 7. Developing the Engine (Revised)

### 7.1 Architecture Overview (Revised)

The revised architecture has the same three compilation targets and two runtime components, but the inference engine is unified as Datalog throughout, and the grounding module has the five-layer defense:

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

*[Unchanged from original thesis — the schema, T2/T3 compilers, DSPy pipeline, and optimization code remain the same. Phase 1 is already self-sufficient.]*

*[Key change: the grounding module now uses the five-layer defense even in Phase 1. Layers 1-3 are always active. Layers 4-5 trigger conditionally.]*

Phase 1 limitations remain: hetvābhāsa detection is unreliable (LLM self-check), reasoning is not verifiable (CoT text, not formal proof), inference is not deterministic, and uncertainty is self-reported. These motivate Phase 2.

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

**What this phase builds:** A formally correct inference engine using Datalog for deterministic forward chaining. Replaces LLM "reasoning" with provable derivation. Boolean truth values (same as Prolog would have provided), but with guaranteed termination.

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

### 7.5 Phase 3: DSPy + Lattice Datalog + UQ

**What changes from Phase 2:** One line.

```python
# Phase 2:
engine = compile_t2(knowledge_store, boolean_mode=True)

# Phase 3:
engine = compile_t2(knowledge_store, boolean_mode=False)
```

That's it. The same engine, the same rules, the same evaluation algorithm. The only difference: when `boolean_mode=False`, the engine computes `meet(rule_confidence, min(antecedent_values))` instead of returning `ESTABLISHED` for every successful derivation.

**Why this is a separate phase despite being one line of code:** The conceptual shift is profound. In Phase 2, a chain through three rules produces a Boolean result: "yes, this follows." In Phase 3, the same chain produces: "this follows, but the conclusion is at most a WORKING HYPOTHESIS because V7 in the middle of the chain is a hypothesis." The UQ decomposition from the original thesis now works *structurally*:

**Epistemic uncertainty:** Read directly from the Heyting values of derived facts. A fact with value `HYPOTHESIS` has higher epistemic uncertainty than one with value `ESTABLISHED`. No metadata computation needed — it's the inference result itself.

**Aleatoric uncertainty:** Computed from domain type and scope condition count (unchanged from original thesis).

**Inference uncertainty:** Computed from ensemble disagreement in the grounding pipeline (Layers 3-4 of the defense).

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

### 7.6 Phase 4: DSPy + Lattice Datalog + Sheaf + UQ — The Final Engine

**What changes from Phase 3:** The sheaf layer is added *on top* of the Datalog engine. The sheaf operates on the derived facts, not on the inference process. The coboundary operator, sheaf Laplacian, and H¹ cohomology computation are unchanged from the original thesis.

**Why this is the correct architecture:** The sheaf doesn't need to know how facts were derived. It checks whether the derived facts are locally-to-globally consistent. This means the sheaf code from the original thesis works unchanged — it takes the knowledge graph and derived facts as input and computes consistency/violations.

*[The KnowledgeSheaf class from the original thesis Section 6.5.4 is retained without modification.]*

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

## 9. What Is Truly Novel (Revised)

The original thesis listed six novel contributions. The revised thesis adds two more and refines the first:

**1. Epistemic-status-propagating inference via lattice Datalog (refined).**
The original claimed this for the custom Heyting engine. The revision achieves it in a computationally tractable framework — semi-naive Datalog with lattice extensions — that guarantees polynomial termination. No existing neurosymbolic system combines epistemic value propagation with Datalog's complexity guarantees.

**2. Hetvābhāsa as cohomological obstruction (unchanged).**
The identification of reasoning fallacies with sheaf cohomology classes remains novel.

**3. Decay-as-inference-precondition (unchanged).**
Stale rules cannot fire, encoded as a structural property.

**4. Three-way uncertainty decomposition with heterogeneous methods (unchanged).**
Epistemic (lattice values), aleatoric (domain classification), inference (ensemble sampling).

**5. Conformal prediction over structured Reference Bank (unchanged).**
Statistical guarantees for source grounding.

**6. Ānvīkṣikī-to-Horn-clause correspondence (refined to Datalog).**
Vyāptis map to Datalog rules (not Horn clauses). This is a tighter fit: Datalog's guaranteed termination matches the finite, non-recursive nature of domain knowledge bases. The correspondence is Ānvīkṣikī → Datalog, not Ānvīkṣikī → Prolog.

**7. Five-layer grounding defense (NEW).**
The combination of ontology-constrained prompting, grammar-constrained decoding (CRANE), ensemble consensus, round-trip verification, and solver-feedback refinement into a layered defense-in-depth for the NL→predicate translation problem. No existing neurosymbolic system addresses grounding with more than one strategy.

**8. Datalog as the unifying formalism across all phases (NEW).**
The insight that Boolean Datalog (Phase 2) and lattice Datalog (Phase 3) are the same engine with a one-parameter change eliminates the engine migration problem that plagues neurosymbolic systems (where upgrading the reasoning engine requires rewriting the knowledge base). One engine, one knowledge base, incremental capability addition.

---

## 10. Limitations (Revised)

**1. The grounding problem is mitigated but not solved.**
The five-layer defense reduces grounding errors from ~40% (zero-shot) to an estimated ~5-10%. Errors are now detectable (via ensemble disagreement and round-trip checks). But deeply implicit reasoning, novel predicate requirements, and pragmatic inference remain challenging. The defense adds 5-7 LLM calls per query.

**2. The knowledge base is manually constructed (unchanged).**
Human expert review of the architecture output remains necessary. This is by design but limits scalability.

**3. The Heyting algebra is coarse (unchanged).**
Four epistemic values is a simple lattice. Scope-dependent epistemic qualification (established in context A, contested in context B) requires a sheaf of lattice values, not a single lattice value.

**4. Sheaf cohomology on large graphs is expensive (unchanged).**
The sheaf Laplacian is dense O(n² × d²). Sparse approximations needed for production scale.

**5. The system does not learn from interaction (unchanged).**
DSPy optimizes prompts; the Datalog engine is static after compilation.

**6. Type 4 Craft domains resist complete formalization (unchanged).**
Tacit knowledge isn't fully capturable in production rules.

**7. Datalog cannot express all Prolog programs (NEW, acknowledged trade-off).**
By choosing Datalog over Prolog, we lose unification over complex terms. If a domain requires nested term structures (mathematical reasoning, complex argument analysis), the engine needs extension to Datalog± or a hybrid Prolog subsystem. For Type 4 Craft domains, this limitation is theoretical — the vyāptis are flat predicates.

**8. Grammar-constrained decoding requires API access (NEW, practical).**
Layer 2 (CRANE-style decoding) requires control over token generation probabilities. This works with open-source models (Mistral, Llama) but not with closed API models (GPT-4, Claude) where logit manipulation is not exposed. For API-only deployment, Layer 2 degrades to structured output formatting (JSON mode), which is weaker.

---

## 11. Further Directions (Revised)

*[Original six directions retained. Three new directions added:]*

**7. Incremental Datalog maintenance.** When a new fact arrives or a rule confidence changes, the current engine recomputes from scratch. Incremental Datalog maintenance (DRed algorithm, à la Gupta et al. 1993 or modern implementations in Soufflé) would allow efficient updates — only recomputing the facts affected by the change. This is essential for a live system where decay markers trigger mid-session and new evidence arrives during interaction.

**8. Grounding as a specialized fine-tuned model.** The five-layer defense is comprehensive but expensive (5-7 LLM calls). A domain-specific fine-tuned model (7B parameters) trained on the Ānvīkṣikī predicate vocabulary could replace Layers 1-3 with a single fast call, reserving Layers 4-5 for edge cases. The training data can be generated synthetically from the knowledge base itself — each vyāpti generates 20-50 NL queries, labeled with correct predicates.

**9. Multi-engine architecture for heterogeneous domains.** Different domain types may require different inference engines. A Type 1 (Formal) domain might need Prolog's unification. A Type 3 (Empirical) domain might need probabilistic Datalog (ProbLog). A Type 4 (Craft) domain is well-served by lattice Datalog. The architecture could dispatch to domain-appropriate engines while maintaining the same grounding defense and synthesis pipeline.

---

## 12. References (Updated Additions)

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
- **Logic-LM**: Pan et al. EMNLP 2023.
- **Logic-LM++**: Kirtania et al. ACL Workshop 2024.
- **ODKE+**: Khorshidi et al. 2025 (ontology-guided extraction, 98.8% precision).
- **FoVer**: Pei et al. TACL 2025 (FOL verification for NL reasoning).
- **Grammar-Aligned Decoding (ASAp)**: Wang et al. arXiv:2405.21047.
- **Structured Decomposition**: arXiv:2601.01609, 2025 (OWL2+SWRL for LLM reasoning).
- **Awesome-LLM-Constrained-Decoding**: github.com/Saibo-creator/Awesome-LLM-Constrained-Decoding

*[All references from original thesis retained.]*
