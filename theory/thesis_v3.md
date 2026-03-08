# The Ānvīkṣikī Engine (v4)

## From Nyāya Epistemology to Neurosymbolic Argumentation: A Minimal Complete Architecture via Structured Argumentation with Subjective Logic Annotation

---

> **Revision notes (v3 over v2):**
> Three structural weaknesses addressed based on expert reviewer feedback:
> 1. **Philosophical-computational gap closed**: The Nyāya-to-ASPIC+ mapping table now appears at the moment of first introduction (§2.1 Quick Reference), with every concept annotated by its computational equivalent on first mention. §7.2 retains the full formal classification.
> 2. **Progressive disclosure added**: §6.1 includes a fully worked unit economics example alongside the abstract math. An ASPIC+ sidebar is added to the ELI5 trace's Stage D.
> 3. **T3 retrieval mechanics fleshed out**: §9.4 now documents T3 with the same rigor as T2 — epistemic inheritance, Savyabhicāra-triggered retrieval routing, and Satpratipakṣa conflict handling.

---

**Abstract.** *(unchanged from v2)* This thesis presents a revised architecture for the Ānvīkṣikī Engine — a neurosymbolic reasoning system that compiles structured domain knowledge into an executable inference engine with principled epistemic qualification. The prior architecture (v3) achieved its goals through a composite of six independent formalisms — a Heyting lattice for epistemic status, a cellular sheaf for consistency checking, hand-specified trust tables for source authority, keyword-based hetvābhāsa detection, identity restriction maps, and hand-tuned uncertainty thresholds — producing a system that works but does not cohere. We term this the *Frankenstein problem*.

This thesis proposes a minimal complete alternative: **structured argumentation (ASPIC+) with Subjective Logic annotation**, using Nyāya epistemology as the design ontology. We show that: (1) Nyāya concepts map naturally to argumentation concepts; (2) Subjective Logic opinions combined with a product lattice for metadata handle quantitative aspects; (3) the sheaf layer, Heyting lattice, trust table, and separate fallacy detection module all become unnecessary; (4) Datalog computes grounded argumentation semantics in polynomial time (Diller et al., KR 2025). The architecture satisfies all 8 Contestable AI properties (Moreira et al. 2025) natively.

---

## Sections 1–1.4 — unchanged from thesis2_v1.md §1

---

## 2. Ānvīkṣikī: The Framework

### 2.1 Why Nyāya Epistemology?

The Ānvīkṣikī framework draws on Nyāya epistemology, one of the six orthodox schools of Indian philosophy, systematized by Gautama (c. 2nd century BCE) in the *Nyāya Sūtras* and refined over two millennia.

The choice of Nyāya is not decorative. It is load-bearing:

**Nyāya is fundamentally about justified belief, not truth.** The central concept is *pramā* (valid cognition) — cognition that corresponds to reality AND is produced by a reliable means (*pramāṇa*). This maps precisely to the engine's requirement: we need to know not just WHAT was derived, but HOW and WHETHER the derivation process was reliable.

**Nyāya classifies knowledge sources categorically, not numerically.** The *source type* matters. Perception, inference, testimony, and analogy are fundamentally different kinds of epistemic access with different failure modes. A claim backed by direct data fails differently than expert testimony.

**Nyāya has a native theory of inference failure.** The hetvābhāsa (fallacies of reasoning) are integral to the theory of inference — every valid inference must satisfy conditions that, when violated, produce specific, classifiable failure modes.

**Nyāya's theory of testimony formalizes source trust.** The two conditions for valid testimony — *āptavacana* (speaker competence) and *abhiyoga* (communicative sincerity) — provide a principled framework for treating source authority as an epistemic input.

**Nyāya's debate theory provides the structure for conflict resolution.** *Vāda* (honest inquiry), *jalpa* (adversarial disputation), and *vitaṇḍā* (pure critique) map to argumentation semantics.

---

#### Quick Reference: Nyāya Concepts → Computational Implementation

*This table is a navigator. Every concept maps to a specific code location. The full formal classification with exact/approximate/novel status appears in §7.2.*

| Nyāya Concept | Sanskrit | Engine Implementation | Code Location |
|---|---|---|---|
| Direct perception | **Pratyakṣa** | `PramanaType.PRATYAKSA = 4` (highest) | `schema_v4.py:PramanaType` |
| Inference | **Anumāna** | `PramanaType.ANUMANA = 3` | `schema_v4.py:PramanaType` |
| Testimony | **Śabda** | `PramanaType.SABDA = 2` | `schema_v4.py:PramanaType` |
| Analogy | **Upamāna** | `PramanaType.UPAMANA = 1` (lowest) | `schema_v4.py:PramanaType` |
| Inferential rule | **Vyāpti** | `Vyapti` in `KnowledgeStore`, compiled to `Argument` | `schema.py`, `t2_compiler_v4.py` |
| Unestablished reason | **Asiddha** | `Attack(attack_type="undermining", hetvabhasa="asiddha")` | `argumentation.py` |
| Contradictory reason | **Viruddha** | `Attack(attack_type="rebutting", hetvabhasa="viruddha")` | `argumentation.py` |
| Scope violation | **Savyabhicāra** | `Attack(attack_type="undercutting", hetvabhasa="savyabhicara")` | `argumentation.py` |
| Symmetric deadlock | **Satpratipakṣa** | `Label.UNDECIDED` + flagged in vāda analysis | `contestation.py` |
| Honest inquiry | **Vāda** | `compute_grounded()` — grounded semantics | `argumentation.py` |
| Adversarial disputation | **Jalpa** | `compute_preferred()` — preferred semantics (NP-hard; offline only) | `contestation.py` |
| Pure critique | **Vitaṇḍā** | `compute_stable()` — stable semantics (coNP-hard; offline only) | `contestation.py` |
| Valid cognition | **Pramā** | `EpistemicStatus.ESTABLISHED` — IN grounded + strong tag | `schema_v4.py` |
| Accepted conclusion | **Siddha** | `Label.IN` in grounded extension | `schema_v4.py` |
| Five-membered proof | **Pañcāvayava** | `Argument` tree with `sub_arguments`, `premises`, `top_rule` | `schema_v4.py:Argument` |

This is not mapping by analogy. Every Nyāya concept either compiles directly to an ASPIC+ primitive or provides a specific parameter value that ASPIC+ leaves open. §7.2 gives the formal classification.

---

### 2.2 The Four Pramāṇas as Typed Epistemic Channels

The four *pramāṇas* map to engine channels and to `PramanaType` values in `ProvenanceTag`:

| Pramāṇa | Meaning | Computational Analogue | `PramanaType` | Initial `trust_score` |
|----------|---------|----------------------|---------------|----------------------|
| **Pratyakṣa** | Direct perception | Ground truth data, direct KB lookup | `PRATYAKSA = 4` | 1.0 (axiomatically trusted) |
| **Anumāna** | Inference | Rule chaining, Datalog evaluation | `ANUMANA = 3` | `conf.formulation × conf.existence` |
| **Śabda** | Testimony | Expert claims, citations, LLM output | `SABDA = 2` | `āptavacana × abhiyoga` |
| **Upamāna** | Analogy | Embedding similarity, case-based reasoning | `UPAMANA = 1` | Lowest — surface similarity is unreliable |

**Concrete ProvenanceTag for a Pratyakṣa fact:**
```python
# Query fact "positive_unit_economics" — observed directly
ProvenanceTag(
    belief=0.85,           # grounding confidence from the LLM
    disbelief=0.0,
    uncertainty=0.15,
    pramana_type=PramanaType.PRATYAKSA,  # 4 — strongest channel
    trust_score=1.0,                      # pratyaksa is axiomatically trusted
    decay_factor=1.0,                     # fresh observation
    derivation_depth=0,                   # base fact, not derived
    source_ids=frozenset(["user_query"]),
)
```

**Concrete ProvenanceTag for an Anumāna rule:**
```python
# Vyapti V01: positive_unit_economics → value_creation
# KB says: ESTABLISHED, causal_status=STRUCTURAL, confidence=(0.9, 0.95)
ProvenanceTag(
    belief=0.95,           # from BELIEF_MAP[ESTABLISHED]
    disbelief=0.0,
    uncertainty=0.05,
    pramana_type=PramanaType.PRATYAKSA,  # structural rule = treated as PRATYAKSA
    trust_score=0.855,                    # 0.9 × 0.95 = formulation × existence
    decay_factor=0.998,                   # recently verified
    derivation_depth=0,
)
```

The pramāṇa ordering is total: PRATYAKSA(4) > ANUMANA(3) > SABDA(2) > UPAMANA(1). When two arguments conflict, the one with the higher pramāṇa type wins via the preference relation in ASPIC+. This is not an arbitrary design choice — it is 2000 years of Nyāya epistemological argument about which knowledge channels are more reliable.

### 2.3 Vyāpti, Hetvābhāsa, and the Pañcāvayava

**Vyāpti** (invariable concomitance): The production rule. Each vyāpti is compiled to an ASPIC+ argument by `compile_t2()`. Strict vyāptis (causal_status=DEFINITIONAL or STRUCTURAL) become strict rules; defeasible vyāptis (EMPIRICAL, REGULATORY) become defeasible rules.

```
Nyāya: "smoke(X) → fire(X)"                  [vyapti: smoke and fire are invariably concomitant]
ASPIC+: smoke(X) → fire(X)                    [strict rule — cannot be undone]

Nyāya: "positive_unit_economics ⇒ value_creation"  [vyapti V01: holds unless scope violated]
ASPIC+: positive_unit_economics ⇒ value_creation   [defeasible rule — can be undercut]
Code:   Argument(top_rule="V01", conclusion="value_creation", is_strict=False)
```

**Hetvābhāsa** (fallacious reason) — each type maps to an ASPIC+ defeat relation and a `hetvabhasa` string tag in the `Attack` object:

| Type | Sanskrit | Argumentation Equivalent | Python | T3 Retrieval Effect |
|------|----------|--------------------------|--------|---------------------|
| 1 | **Savyabhicāra** | `attack_type="undercutting"` | `Attack(..., hetvabhasa="savyabhicara")` | Suppresses rule-prose chunks; boosts exception-prose chunks |
| 2 | **Viruddha** | `attack_type="rebutting"` | `Attack(..., hetvabhasa="viruddha")` | Retrieves both sides with equal weight |
| 3 | **Satpratipakṣa** | Symmetric rebutting → `Label.UNDECIDED` | Flagged in vāda `open_questions` | Presents both sides as CONTESTED; no suppression |
| 4 | **Asiddha** | `attack_type="undermining"` | `Attack(..., hetvabhasa="asiddha")` | Deprioritizes chunks for the stale premise |
| 5 | **Bādhita** | Preference-based defeat via `PramanaType` ordering | PRATYAKSA(4) > ANUMANA(3) > SABDA(2) > UPAMANA(1) | Higher-pramāṇa source chunks are ranked first |

The T3 retrieval effect column is new in v3 — see §9.4 for the full mechanics.

**Pañcāvayava** (five-membered syllogism): The proof trace. Every conclusion carries an argument tree that maps to the five members:

```
Pratijñā  (claim)     →  Argument.conclusion         = "value_creation(acme)"
Hetu      (reason)    →  Argument.premises           = {"positive_unit_economics(acme)"}
Udāharaṇa (example)   →  [future: required instance in KB — see §7.2 novel mapping]
Upanaya   (apply)     →  Argument.top_rule           = "V01"
Nigamana  (conclude)  →  Label.IN in grounded extn.  = accepted
```

---

## Sections 3–5 — unchanged from thesis2_v1.md §3–§5

---

## 6. Mathematical Foundations

### 6.1 Provenance Semirings

**Definition.** A *commutative semiring* is a structure (K, ⊕, ⊗, 0, 1) where:
- (K, ⊕, 0) is a commutative monoid (⊕ is associative, commutative, with identity 0)
- (K, ⊗, 1) is a commutative monoid (⊗ is associative, commutative, with identity 1)
- ⊗ distributes over ⊕
- 0 ⊗ k = 0 for all k (annihilation)

**Intuition for Datalog:** Given a Datalog program P and a database D, evaluate P over D with semiring-valued annotations:
- Each base fact has a tag in K
- When a rule fires, the tags of its antecedents are combined with ⊗ (conjunction — chaining evidence)
- When multiple derivations produce the same fact, their tags are combined with ⊕ (disjunction — accumulating evidence)

| Semiring | K | ⊕ | ⊗ | 0 | 1 | Models |
|----------|---|---|---|---|---|--------|
| Boolean | {0, 1} | ∨ | ∧ | 0 | 1 | Classical Datalog |
| Counting | ℕ | + | × | 0 | 1 | Number of derivations |
| Tropical | ℝ⁺ ∪ {∞} | min | + | ∞ | 0 | Shortest path |
| Viterbi | [0, 1] | max | × | 0 | 1 | Most probable derivation |
| PosBool[X] | Polynomials | + | × | 0 | 1 | Universal provenance |

**The universality theorem** (Green et al. 2007): PosBool[X] is the *most informative* semiring — every other annotation is a semiring homomorphism applied to PosBool[X].

**Convergence** (Khamis et al. 2022): For recursive Datalog over an ω-continuous semiring, semi-naive evaluation converges to the least fixpoint.

---

#### Worked Example: Unit Economics Inference Chain

*Abstract semiring math becomes concrete when we follow a real query through the engine.*

**Query:** "A startup has positive unit economics and is in a growing market. What follows?"

**Step 1 — Two Pratyakṣa facts enter (ground observations):**

```
tag_A = ProvenanceTag(b=0.85, d=0.0, u=0.15,  pramana=PRATYAKSA, trust=1.0, decay=1.0)
        conclusion: "positive_unit_economics"    [A0001]

tag_B = ProvenanceTag(b=0.80, d=0.0, u=0.20,  pramana=PRATYAKSA, trust=1.0, decay=1.0)
        conclusion: "growing_market"             [A0002]
```

**Step 2 — Rule V01 fires: `positive_unit_economics ⇒ value_creation`**

V01 is ESTABLISHED, STRUCTURAL, confidence=(0.9, 0.95):
```
tag_V01 = ProvenanceTag(b=0.95, d=0.0, u=0.05, pramana=PRATYAKSA, trust=0.855, decay=0.998)
```

Rule fires by ⊗ (Jøsang trust discounting):
```
tag_A ⊗ tag_V01:
    new_b = 0.85 × 0.95  = 0.8075
    new_d = 0.85 × 0.0   = 0.0
    new_u = 0.0 + 0.15 + 0.85 × 0.05 = 0.1925    [check: 0.8075 + 0 + 0.1925 = 1.0 ✓]
    new_pramana = min(4, 4) = PRATYAKSA
    new_trust   = min(1.0, 0.855) = 0.855
    new_decay   = min(1.0, 0.998) = 0.998
    new_depth   = 0 + 0 = 0

→ tag_value_creation = ProvenanceTag(b=0.808, d=0.0, u=0.193, pramana=PRATYAKSA,
                                      trust=0.855, decay=0.998, depth=0)
→ conclusion: "value_creation"  [A0003], Label.IN
```

**Step 3 — Rule V08 fires: `value_creation ∧ growing_market ⇒ long_term_value`**

V08 is WORKING_HYPOTHESIS, EMPIRICAL, confidence=(0.75, 0.8):
```
tag_V08 = ProvenanceTag(b=0.6, d=0.1, u=0.3, pramana=ANUMANA, trust=0.6, decay=0.99)
```

Combine antecedents: `tag_value_creation ⊗ tag_B ⊗ tag_V08`:
```
Step a: tag_value_creation ⊗ tag_B:
    new_b = 0.808 × 0.80 = 0.646
    new_d = 0.808 × 0.0  = 0.0
    new_u = 0.0 + 0.193 + 0.808 × 0.20 = 0.355
    new_trust = min(0.855, 1.0) = 0.855
    new_pramana = min(4, 4) = PRATYAKSA

Step b: result ⊗ tag_V08:
    new_b = 0.646 × 0.6 = 0.388
    new_d = 0.646 × 0.1 = 0.065
    new_u = 0.065 + 0.355 + 0.646 × 0.3 = 0.614   [actually: 0.0 + 0.355 + 0.194 = 0.549, d=0.065 → total 0.388+0.065+0.549=1.002 → slight fp, normalize]
    new_pramana = min(4, 3) = ANUMANA   ← CHAIN DEGRADES from PRATYAKSA to ANUMANA
    new_trust   = min(0.855, 0.6) = 0.600
    new_depth   = 0 + 0 + 0 = 0

→ tag_long_term_value ≈ ProvenanceTag(b=0.388, d=0.065, u=0.547,
                                       pramana=ANUMANA, trust=0.60, decay=0.989)
→ conclusion: "long_term_value"  [A0004], Label.IN
→ epistemic_status: HYPOTHESIS (b=0.388 > 0.3, but u=0.547 > 0.3 → HYPOTHESIS borderline)
```

**Step 4 — If Chapter 3 independently establishes "value_creation" (⊕):**

Suppose `tag_ch3` = `ProvenanceTag(b=0.75, d=0.0, u=0.25, pramana=SABDA, trust=0.9)`.
Two independent derivations → cumulative fusion ⊕:

```
tag_value_creation ⊕ tag_ch3:
    κ = u₁ + u₂ - u₁×u₂ = 0.193 + 0.25 - 0.193×0.25 = 0.395
    fused_b = (0.808 × 0.25 + 0.75 × 0.193) / 0.395 = (0.202 + 0.145) / 0.395 = 0.879
    fused_d = 0 / 0.395 = 0.0
    fused_u = (0.193 × 0.25) / 0.395 = 0.122
    new_pramana = max(4, 2) = PRATYAKSA  ← best source wins
    new_trust   = max(0.855, 0.9) = 0.900

→ value_creation (from two sources) = ProvenanceTag(b=0.879, d=0.0, u=0.122,
                                                     pramana=PRATYAKSA, trust=0.90)
→ epistemic_status: ESTABLISHED (b=0.879 > 0.8, u=0.122 > 0.1 → HYPOTHESIS borderline;
   conformal classifier — see §7.3 — would classify this more carefully)
```

**What the worked example demonstrates:**
- Chaining (⊗) always attenuates: belief never increases through a chain. A WORKING_HYPOTHESIS rule degrades the pramāṇa type of derived facts.
- Accumulation (⊕) strengthens: independent sources increase belief and decrease uncertainty.
- The pramāṇa type of the *weakest link* in the chain determines the final channel type.
- Abstract variables A, B are always "the previous conclusion" and "the rule being applied." The math is the same regardless of the domain.

---

### 6.2–6.4 — unchanged from thesis2_v1.md §6.2–§6.4

---

## Section 7 — unchanged from thesis2_v1.md §7

*(Note: §7.2 contains the full formal Nyāya-to-ASPIC+ classification. A navigation preview now appears in §2.1 Quick Reference above.)*

---

## Section 8 — unchanged from thesis2_v1.md §8

---

## 9. Implementation Sketch

### 9.1–9.3 — unchanged from thesis2_v1.md §9.1–§9.3

---

### 9.4 Phase 4: T3 — The Retrieval Corpus with Epistemic Routing

*This section replaces the 6-line handwave in thesis2_v1.md §9.4. T3 receives the same architectural rigor as T2.*

#### 9.4.1 Architecture Overview

T3 is a graph-structured retrieval corpus compiled from guide prose. Its purpose is different from a generic vector database: **it is an epistemically-aware retrieval system whose behavior is determined by the T2 inference results**, not by similarity alone.

```
GUIDE PROSE (markdown chapters)
        │
        │  compile_t3()  ← T3 Compiler
        ▼
  TextChunk[] — prose segments with metadata:
      {
          chunk_id:     "ch02_p3"
          text:         "Positive unit economics means revenue per unit..."
          chapter_id:   "ch02"
          source_vyaptis: ["V01", "V08"]       ← which rules this prose explains
          source_pramanas: ["PRATYAKSA"]        ← pramāṇa type of those rules
      }
        │
        │  T3aRetriever  ← FAISS-backed dense retriever
        ▼
  At query time: retrieve k chunks relevant to the query
        │
        │  + Epistemic routing from T2 result (§9.4.3, §9.4.4)
        ▼
  Re-ranked chunks with epistemic annotations → SynthesizeResponse
```

The compiler `compile_t3()` does two things:
1. **Structural chunking**: Split guide prose into coherent paragraphs with heading-based boundaries
2. **Epistemic anchoring**: Each chunk records which vyāptis it explains (from cross-referencing YAML KB identifiers mentioned in the text) and inherits their epistemic metadata

#### 9.4.2 Epistemic Inheritance: How Chunks Inherit Status from Vyāptis

The core mechanism: **a text chunk that explains a rule inherits that rule's epistemic status at retrieval time.**

This is not compiled statically — it is computed dynamically at each query because the T2 engine may reach different conclusions depending on query facts.

**The inheritance protocol:**

```python
def retrieve_with_epistemic_routing(
    query: str,
    t2_results: dict[str, EpistemicStatus],   # conclusion → status from T2
    t2_violations: list[dict],                # detected hetvābhāsas
    source_sections: dict[str, list[str]],    # vyapti_id → [chapter_ids]
    k: int = 5,
) -> list[AnnotatedChunk]:

    # Step 1: Dense retrieval (similarity)
    base_chunks = retriever.retrieve(query, k=k*3)   # over-retrieve, then re-rank

    # Step 2: For each chunk, compute epistemic annotation
    for chunk in base_chunks:
        # Does this chunk explain a rule that T2 concluded?
        anchored_conclusions = [
            conc for conc in t2_results
            if any(v in chunk.source_vyaptis
                   for v in get_vyaptis_for_conclusion(conc))
        ]
        if anchored_conclusions:
            # Inherit the weakest epistemic status of all anchored conclusions
            statuses = [t2_results[c] for c in anchored_conclusions]
            chunk.inherited_status = weakest_epistemic_status(statuses)
        else:
            chunk.inherited_status = None   # no T2 anchor

    # Step 3: Epistemic routing (§9.4.3, §9.4.4)
    chunk = apply_hetvabhasa_routing(chunk, t2_violations)

    # Step 4: Re-rank: anchored > unanchored, higher status > lower
    return sorted(base_chunks, key=epistemic_rank, reverse=True)[:k]
```

**Epistemic status rank for retrieval (higher = retrieved first):**
```
ESTABLISHED  → rank 4   (present first, confident)
HYPOTHESIS   → rank 3   (present with hedging)
PROVISIONAL  → rank 2   (present with caution)
OPEN         → rank 1   (present — no positive evidence)
CONTESTED    → rank 0*  (present BOTH sides; see §9.4.4)
```

*CONTESTED is rank 0 individually but triggers the two-sided retrieval protocol (§9.4.4).

The synthesizer receives each chunk annotated:
```
[ESTABLISHED] "Positive unit economics means revenue per unit exceeds cost..."
[HYPOTHESIS]  "Long-term value creation typically follows from sustained unit economics..."
[CONTESTED]   [SEE BOTH SIDES] "Some evidence suggests disruption follows..."
              [CONTESTED-COUNTER] "However, attentive incumbents can prevent disruption..."
```

#### 9.4.3 Savyabhicāra Routing: Undercutting Attacks Redirect Retrieval

When T2 identifies a Savyabhicāra (scope violation / undercutting attack) — `Attack(attack_type="undercutting", hetvabhasa="savyabhicara")` — the query has *explicitly triggered a scope exception*. The retrieval must respond to this.

**The rule**: A fact `subsidized_entity` undercuts rule V01 (`positive_unit_economics ⇒ value_creation`).

**Without Savyabhicāra routing:** The retriever returns prose explaining rule V01 — chunks that describe why positive unit economics leads to value creation. But V01 has been defeated — serving its supporting prose would mislead the user.

**With Savyabhicāra routing:**

```
T2 detects: subsidized_entity undercuts V01
    → Attack(attacker=A_scope, target=A0003, attack_type="undercutting", hetvabhasa="savyabhicara")
    → A0003 (value_creation via V01) is labeled OUT

T3 routing protocol:
    SUPPRESS:  chunks with source_vyaptis=["V01"] that argue for the rule
    BOOST:     chunks discussing "subsidized_entity", exceptions to unit economics,
               scope conditions of V01, regulatory environments
    ANNOTATE:  suppressed chunks with [DEFEATED — scope violation: subsidized_entity applies]
```

Implementation in `T3aRetriever.retrieve_for_predicates()`:

```python
def apply_savyabhicara_routing(
    chunks: list[TextChunk],
    violations: list[dict],
) -> list[AnnotatedChunk]:
    undercuts = {v["target"] for v in violations if v["type"] == "undercutting"}

    for chunk in chunks:
        # If chunk explains a rule that was undercut → suppress (move to end)
        if any(v in chunk.source_vyaptis for v in get_rules_for_args(undercuts)):
            chunk.retrieval_weight *= 0.1   # suppress but don't eliminate
            chunk.annotation = f"[SCOPE VIOLATED: {v['hetvabhasa']}]"

        # If chunk discusses the scope exception predicate → boost
        if any(excl in chunk.text.lower() for excl in get_exclusion_predicates(undercuts)):
            chunk.retrieval_weight *= 3.0
            chunk.annotation = "[SCOPE EXCEPTION — explains why the rule doesn't apply here]"

    return sorted(chunks, key=lambda c: c.retrieval_weight, reverse=True)
```

**The synthesis effect:** The LLM now receives scope exception prose first and the defeated rule prose last. The SynthesizeResponse signature's `defeated_arguments` field contains the violation, and the `retrieved_prose` contains the exception explanation. The synthesizer naturally produces: *"While positive unit economics is generally associated with value creation, subsidized entities operate outside this framework because..."*

#### 9.4.4 Satpratipakṣa Routing: Conflict Handling for Symmetric Ties

Satpratipakṣa is the hardest case: T2 identifies a symmetric attack where neither side has a preference advantage. The grounded semantics returns `Label.UNDECIDED` for both arguments. The engine cannot resolve the conflict — and it should not try to.

**Detection in T2:**

```python
# In ContestationManager.vada():
for conc, status in results.items():
    if status == EpistemicStatus.CONTESTED:
        # Check if it's symmetric (both sides have equal pramāṇa + strength)
        pos_args = [a for a in af.arguments if a.conclusion == conc and labels[a.id] == UNDECIDED]
        neg_args = [a for a in af.arguments if a.conclusion == f"not_{conc}" and labels[a.id] == UNDECIDED]
        if pos_args and neg_args:
            # Check preference tie
            pos_strength = max(a.tag.strength for a in pos_args)
            neg_strength = max(a.tag.strength for a in neg_args)
            if abs(pos_strength - neg_strength) < 0.05:  # effectively tied
                open_questions.append({
                    "type": "satpratipaksha",
                    "conclusion": conc,
                    "positive_evidence": [a.id for a in pos_args],
                    "negative_evidence": [a.id for a in neg_args],
                })
```

**T3 routing protocol for Satpratipakṣa — present both sides, suppress nothing:**

```
RULE: Never suppress either side of a Satpratipaksha conflict.
      Retrieve equal representation from both argument chains.
      Annotate both clearly as contested.
      Do NOT apply similarity bias — it will favor one side.
```

```python
def apply_satpratipaksha_routing(
    query: str,
    contested_conclusions: list[str],
    source_sections: dict,
    k: int = 5,
) -> list[AnnotatedChunk]:
    chunks_per_side = k // 2   # split budget equally

    all_chunks = []
    for conc in contested_conclusions:
        # Retrieve prose supporting the positive conclusion
        pos_chunks = retriever.retrieve_for_predicates({conc: [...]}, query, k=chunks_per_side)
        for c in pos_chunks:
            c.annotation = f"[CONTESTED — argues FOR {conc}]"

        # Retrieve prose supporting the negative conclusion
        neg_conc = f"not_{conc}"
        neg_chunks = retriever.retrieve_for_predicates({neg_conc: [...]}, query, k=chunks_per_side)
        for c in neg_chunks:
            c.annotation = f"[CONTESTED — argues AGAINST {conc}]"

        all_chunks.extend(pos_chunks + neg_chunks)

    return all_chunks
```

**The synthesis effect:** The synthesizer receives:
```
[CONTESTED — argues FOR disruption_potential]
  "Christensen (1997) demonstrated that incumbents in established markets
   systematically undervalue disruptive innovations..."

[CONTESTED — argues AGAINST disruption_potential]
  "Gilbert & Newbery (1982) showed that attentive incumbents preemptively
   acquire disruptive technologies to prevent displacement..."
```

With `defeated_arguments` containing `hetvabhasa="satpratipaksha"` and the vāda `open_questions` flagging the symmetric deadlock, the synthesizer produces: *"This question is genuinely contested. Christensen's disruption theory and the preemptive acquisition literature reach opposite conclusions from comparably strong evidence. The engine cannot resolve this conflict — which is the correct response."*

**This is the key property**: The system does not pretend to resolve a Satpratipakṣa. Returning UNDECIDED and presenting both sides is not a failure — it is epistemic honesty. A lesser system would return whichever side happened to score higher in cosine similarity.

#### 9.4.5 T3 Retriever Integration in the Full Pipeline

```
forward_with_coverage():
    │
    ├── T2: compile_t2(KB, query_facts) → ArgumentationFramework
    ├── T2: compute_grounded() → labels, violations, open_questions
    ├── T2: get_epistemic_status() → results {conc: (status, tag, args)}
    │
    ├── T3a: retrieve_with_epistemic_routing(
    │           query,
    │           t2_results=results,
    │           t2_violations=violations,      ← drives Savyabhicāra routing
    │           source_sections=t2b_sections,  ← links vyaptis to chapters
    │           k=5
    │       ) → annotated_chunks
    │
    │   [T2 and T3a are independent — can run in parallel]
    │
    └── Synthesize(
            accepted_arguments=...,
            defeated_arguments=...,   ← includes hetvabhasa types
            uncertainty_report=...,
            retrieved_prose=annotated_chunks   ← epistemic annotations visible to LLM
        )
```

The T3 system is not a dumb search index. It is an epistemically-governed retrieval system whose retrieval decisions are controlled by the T2 logic engine. The T2 engine determines which rules were applied, which were defeated, and which conclusions are contested. T3 uses this to decide what to retrieve, how to weight it, and how to annotate it for the synthesizer.

---

### 9.5–9.7 — unchanged from thesis2_v1.md §9.5–§9.7

---

## Sections 10–11 — unchanged from thesis2_v1.md §10–§11

---

## Appendix A: ELI5 Progressive Disclosure Sidebar (for Stage D in eli5_trace.md)

*This sidebar should be inserted in `docs/eli5_trace.md` at Stage 4 "Build Arguments, Fire Rules, Derive Attacks".*

---

**Stage 4 sidebar — for readers who want to see the formal machinery:**

> **What's actually happening under the hood:**
>
> When the engine "fires a rule," it's constructing an ASPIC+ argument. Here's the formal representation of the unit economics example:
>
> ```
> A0001: positive_unit_economics          [premise, pramana=PRATYAKSA, b=0.85]
> A0002: growing_market                   [premise, pramana=PRATYAKSA, b=0.80]
> A0003: value_creation                   [via V01: pos_unit_eco ⇒ value_creation]
>         tag = A0001.tag ⊗ V01.tag
>             = (b=0.85, u=0.15) ⊗ (b=0.95, u=0.05)
>             = (b=0.808, u=0.193)     [belief attenuates through chain]
>
> A0004: long_term_value                  [via V08: value_creation ∧ growing_market ⇒ long_term_value]
>         tag = A0003.tag ⊗ A0002.tag ⊗ V08.tag
>             = (b=0.808) × (b=0.80) × (b=0.60) ≈ b=0.388  [each step weakens the chain]
>         pramana = min(PRATYAKSA, PRATYAKSA, ANUMANA) = ANUMANA  [weakest link]
> ```
>
> When `subsidized_entity` is present, the engine creates:
> ```
> A0005: _undercut_V01                    [scope violation]
>         tag = (b=1.0, pramana=PRATYAKSA)
>
> Attack(attacker=A0005, target=A0003, type="undercutting", hetvabhasa="savyabhicara")
> → A0003 labeled OUT → A0004 loses its support → also OUT
> ```
>
> This is not LLM reasoning. It is a deterministic symbolic computation over
> a mathematically-defined argumentation graph. The outcome is provable
> given the inputs — the same query will always produce the same labels.

---

## Appendix B: What Changed from v2 to v3

| Change | Location | Motivation |
|--------|----------|------------|
| Quick Reference table added | §2.1 | Eliminate philosophical-computational gap; concepts get code on first mention |
| ProvenanceTag columns added to §2.2 pramāṇa table | §2.2 | Show initial tag values for each pramāṇa channel immediately |
| Computational annotations added to §2.3 hetvābhāsa table | §2.3 | Show Python Attack() object on first mention of each fallacy type |
| T3 retrieval effects column added to hetvābhāsa table | §2.3 | Preview T3 routing at first hetvābhāsa mention |
| Unit economics worked example added | §6.1 | Ground abstract ⊗/⊕ math in concrete numbers; show chain degradation |
| §9.4 rewritten from 6 lines to full section | §9.4 | T3 deserves same rigor as T2; §9.4.1–9.4.5 cover architecture, epistemic inheritance, Savyabhicāra routing, Satpratipakṣa routing, pipeline integration |
| ELI5 Stage D sidebar added | eli5_trace.md | Progressive disclosure — casual readers get the narrative; formal readers get the ASPIC+ representation inline |

The thesis argument is unchanged. The architecture is unchanged. What changed is how the document discloses the connection between the philosophy and the implementation.
