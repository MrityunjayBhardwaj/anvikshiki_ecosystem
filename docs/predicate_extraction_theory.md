# Seed-Constrained Predicate Extraction for Neurosymbolic Argumentation Engines

## A Theoretical Foundation for Automated Knowledge Base Enrichment in the Anvikshiki Framework

---

**Abstract.** The Anvikshiki Engine v4 compiles domain knowledge into an ASPIC+ argumentation framework over provenance semirings, where predicates serve as the atomic vocabulary of inference. The engine's expressiveness is bounded by its predicate vocabulary: a vyapti (defeasible rule) can only reference predicates that exist in the knowledge store. We formalize the *predicate extraction problem* — automatically enriching a seed ontology from generated guide text while preserving the invariants required by the downstream argumentation engine. We show that: (1) the problem decomposes into six stages with formally distinct correctness conditions; (2) the flat-predicate constraint (unary Datalog atoms) is necessary and sufficient for polynomial termination of the augmented engine; (3) seed ontology bootstrapping provides a monotone refinement operator over the predicate lattice; (4) conservative epistemic defaults are mandated by the Nyaya principle that extracted knowledge enters as sabda (testimony) — the weakest pramana — and must earn higher status through argumentation; (5) DAG acyclicity in the antecedent-consequent graph is equivalent to stratifiability of the augmented Datalog program, guaranteeing the existence of a unique minimal model. We ground each design decision in the formal framework of the parent thesis (Bhardwaj 2026) and the literature on ontology learning, structured extraction, and provenance-aware Datalog.

---

## 1. Introduction: The Granularity Problem

### 1.1 The Architectural Context

The Anvikshiki Engine v4 (Bhardwaj 2026) is a neurosymbolic reasoning system that compiles structured domain knowledge into an executable inference engine with principled epistemic qualification. Its architecture consists of four layers:

1. **Nyaya epistemology** as design ontology — providing the conceptual vocabulary (pramanas, vyaptis, hetvabhasas)
2. **ASPIC+ argumentation** as reasoning structure — providing arguments, defeats, and extensions (Prakken 2010; Modgil & Prakken 2014)
3. **Provenance semirings** as quantitative annotation — tracking evidence strength, source trust, and temporal decay (Green, Karvounarakis & Tannen, PODS 2007)
4. **Datalog evaluation** as computational substrate — guaranteeing polynomial fixpoint computation (Diller, Keshavarzi Zafarghandi & Wallner, KR 2025)

The engine consumes a `KnowledgeStore` containing vyaptis (domain rules), each of the form:

```
consequent(Entity) :- antecedent_1(Entity), ..., antecedent_n(Entity),
                      not scope_exclusion_1(Entity), ...
```

At query time, user input is grounded into predicate assertions, the T2 compiler constructs an argumentation framework, and grounded semantics (Wu, Caminada & Gabbay 2009) determines which conclusions are accepted, defeated, or undecided.

### 1.2 The Problem

The engine's reasoning capacity is bounded by its **predicate vocabulary**. A vyapti can only reference predicates that exist in the knowledge store. The current `business_expert.yaml` knowledge base contains 11 vyaptis over 23 unique predicates for a 10-chapter business strategy domain. This produces chapter-level abstractions that miss section- and paragraph-level reasoning.

**Concrete example.** Chapter 2 of the generated guide discusses LTV, CAC, contribution margin, payback period, economies of scale, maturity mismatch, and the unit economics death spiral. The knowledge store contains exactly one relevant vyapti:

```
V01: positive_unit_economics(E) => value_creation(E)
```

The guide text contains at least 14 extractable predicates (`ltv_exceeds_cac`, `positive_contribution_margin`, `payback_within_runway`, `economies_of_scale_real`, `maturity_mismatch`, `negative_unit_economics`, etc.) and at least 4 new vyaptis relating them. None of these are available to the engine.

This is the **granularity gap**: the architecture (Datalog, ASPIC+, provenance semirings) handles hundreds of predicates with polynomial guarantees. The bottleneck is KB authoring.

### 1.3 The Extraction Problem

We define the predicate extraction problem as follows:

**Given:**
- A seed knowledge store $K_0 = (V_0, P_0, H_0, R_0)$ where $V_0$ is a set of vyaptis, $P_0$ is the predicate vocabulary (all predicates appearing in $V_0$), $H_0$ is a set of hetvabhasas, and $R_0$ is a reference bank
- A guide text $G = \{g_1, ..., g_n\}$ partitioned by chapter
- The formal invariants $\mathcal{I}$ of the downstream engine (defined in Section 3)

**Produce:**
- An augmented knowledge store $K^* = (V_0 \cup V_{new}, P_0 \cup P_{new}, H_0, R_0)$ such that:
  1. All invariants $\mathcal{I}$ are preserved
  2. $|P_{new}| > 0$ (non-trivial enrichment)
  3. Every $p \in P_{new}$ is grounded in $G$ (provenance)
  4. Every $v \in V_{new}$ passes Pydantic schema validation against the existing `Vyapti` model

### 1.4 Contributions

This paper provides:

1. A formal decomposition of the extraction problem into six stages (A-F) with distinct correctness conditions (Section 4)
2. Proofs that the flat-predicate and DAG-acyclicity constraints are necessary and sufficient for the augmented engine's termination and unique-model guarantees (Section 3)
3. A theoretical grounding of each design decision in the parent architecture's formal framework (Section 5)
4. An analysis of why extracted predicates must enter with conservative epistemic defaults, derived from Nyaya pramana theory (Section 5.4)
5. A composite evaluation metric with formal justification for each component weight (Section 6)

---

## 2. Formal Preliminaries

We recall the definitions from the parent thesis (Bhardwaj 2026, Sections 6-7) that constrain the extraction pipeline.

### 2.1 The Provenance Semiring

**Definition 2.1** (Green et al., PODS 2007). A *commutative semiring* is a structure $(K, \oplus, \otimes, \mathbf{0}, \mathbf{1})$ where $(K, \oplus, \mathbf{0})$ and $(K, \otimes, \mathbf{1})$ are commutative monoids, $\otimes$ distributes over $\oplus$, and $\mathbf{0} \otimes k = \mathbf{0}$ for all $k$.

The Anvikshiki engine uses a `ProvenanceTag` semiring (Bhardwaj 2026, Section 7.3):

$$\text{Tag} = (\text{belief}, \text{disbelief}, \text{uncertainty}, \text{source\_ids}, \text{pramana\_type}, \text{trust}, \text{decay}, \text{depth})$$

with operations:
- $\otimes$ (tensor): sequential composition through inference chains — belief attenuates ($b_{AB} = b_A \cdot b_B$), uncertainty grows, trust takes weakest link
- $\oplus$ (oplus): parallel composition across independent arguments — cumulative fusion (Josang 2016), sources union, trust noisy-OR

**Relevance to extraction:** Every new predicate entering the system carries a provenance tag. The extraction pipeline must produce tags that are valid elements of this semiring — i.e., $b + d + u \approx 1$, trust $\in [0,1]$, pramana type from the four-element hierarchy.

### 2.2 ASPIC+ Argumentation

**Definition 2.2** (Prakken 2010; Modgil & Prakken 2014). An ASPIC+ argumentation theory consists of:
- An argumentation system $AS = (\mathcal{L}, \mathcal{R}, n)$ with logical language $\mathcal{L}$, rules $\mathcal{R} = \mathcal{R}_s \cup \mathcal{R}_d$ (strict and defeasible), and naming function $n: \mathcal{R}_d \to \mathcal{L}$
- A knowledge base $KB = (\mathcal{K}_n, \mathcal{K}_p)$ with necessary and ordinary premises
- Arguments built recursively from premises through rules
- Three attack types: undermining, undercutting, rebutting
- Defeat = attack + preference ordering

**Key property** (Caminada & Amgoud 2007): Under grounded semantics, ASPIC+ satisfies closure, direct consistency, and indirect consistency (the rationality postulates).

**Relevance to extraction:** New vyaptis become new defeasible rules $r_d \in \mathcal{R}_d$. New predicates expand $\mathcal{L}$. The rationality postulates must be preserved — which means the augmented rule set must not introduce contradictions that grounded semantics cannot resolve.

### 2.3 The Heyting Algebra of Epistemic Values

**Definition 2.3** (Bhardwaj 2026, Section 9.5; implemented in `datalog_engine.py`). The epistemic lattice is a five-element Heyting algebra:

$$\text{BOTTOM} < \text{CONTESTED} < \text{OPEN} < \text{HYPOTHESIS} < \text{ESTABLISHED}$$

with meet (min) for conjunction along inference chains and join (max) for disjunction across alternative derivations.

**Relevance to extraction:** In the Datalog engine (Phase 2, boolean mode), extracted vyaptis compile to rules. In lattice mode (Phase 3+), each rule carries a confidence value from this algebra. The extraction pipeline's conservative default of `epistemic_status = "hypothesis"` maps to $\text{HYPOTHESIS} = 3$ — the second-highest value, reflecting that extracted knowledge has not been human-verified.

### 2.4 Semi-Naive Evaluation and Termination

**Theorem 2.4** (Khamis et al., PODS 2022; implemented in `datalog_engine.py`). For a Datalog program $P$ over an $\omega$-continuous semiring, semi-naive evaluation converges to the least fixpoint in $O(|\mathcal{R}| \times |\Delta\text{facts}|)$ per iteration, with total complexity $O(|\mathcal{R}| \times |\text{facts}|)$ — polynomial.

**Proof of termination** (from `datalog_engine.py`, lines 9-12): The Anvikshiki Datalog engine terminates because: (a) the predicate/entity space is finite, (b) the lattice is monotone (values can only increase via join), (c) the lattice has finite height (5 elements). Therefore the fixpoint is reached in at most $|\text{predicates}| \times |\text{entities}| \times 5$ iterations.

**Relevance to extraction:** Adding new predicates expands the predicate space but not the entity space (all predicates are unary: `predicate(Entity)`). The augmented program terminates if and only if the new rules do not introduce cycles that cause unbounded derivation. We prove this in Section 3.

### 2.5 The Nyaya-to-ASPIC+ Mapping

The parent thesis (Bhardwaj 2026, Section 7.2) establishes a structural mapping between Nyaya epistemological categories and ASPIC+ primitives. The five hetvabhasa types map to defeat relations:

| Hetvabhasa | ASPIC+ Defeat Type |
|---|---|
| Asiddha (unestablished) | Undermining — attacks a premise |
| Savyabhicara (inconclusive) | Undercutting — attacks defeasible rule applicability |
| Viruddha (contradictory) | Rebutting — counter-argument for contrary conclusion |
| Satpratipaksa (counterbalanced) | Symmetric attack — mutual rebutting, no preference winner |
| Badhita (sublated) | Preference-based defeat — higher pramana overrides lower |

The four pramanas form an ordering: Pratyaksa (4) > Anumana (3) > Sabda (2) > Upamana (1). This ordering defines the argument preference relation in ASPIC+.

**Relevance to extraction:** Extracted predicates enter the system via LLM processing of guide text. The LLM's extraction is an act of *sabda* (testimony) — the guide text is the speaker, the LLM is the interpreter. By the pramana hierarchy, sabda-derived knowledge is weaker than anumana (inference from established rules) and pratyaksa (direct observation). This mandates conservative epistemic defaults for extracted knowledge (Section 5.4).

---

## 3. Invariants of the Downstream Engine

The extraction pipeline must preserve the following invariants, each of which is load-bearing for the engine's correctness guarantees.

### 3.1 Invariant I1: Flat Predicates (Unary Atoms)

**Statement.** Every predicate in the knowledge store is unary: `predicate_name(Entity)`. No binary or higher-arity predicates are permitted.

**Justification.** This is the Datalog compatibility constraint. The engine's inference is:

$$\text{consequent}(E) \mathrel{:\text{-}} \text{ant}_1(E), ..., \text{ant}_n(E), \text{not } \text{excl}_1(E), ...$$

All atoms share the same single variable $E$. This ensures:
1. **Polynomial termination.** With $|P|$ predicates and $|E|$ entities, the maximum number of ground facts is $|P| \times |E|$. Since each rule can derive at most one new fact per entity, the fixpoint is reached in polynomial time.
2. **No function symbols.** Datalog's termination guarantee depends on the absence of function symbols (which would allow infinite term generation). Flat predicates enforce this.
3. **Decidable containment.** Query containment for unary Datalog is decidable (Chandra & Merlin 1977), enabling compile-time verification of the augmented program.

**Consequence for extraction.** The pipeline must reject any extracted predicate that implies a binary relationship (e.g., `exceeds(LTV, CAC)`). Instead, the relationship must be encoded as a unary predicate: `ltv_exceeds_cac(Entity)`. The `_enforce_snake_case()` utility in the implementation enforces this syntactically.

### 3.2 Invariant I2: DAG Acyclicity

**Statement.** The antecedent-consequent graph $G_{ac} = (P, E_{ac})$ where $E_{ac} = \{(a, c) \mid \exists v \in V: a \in v.\text{antecedents} \wedge c = v.\text{consequent}\}$ must be a directed acyclic graph.

**Justification.** DAG acyclicity is equivalent to stratifiability of the Datalog program under negation.

**Theorem 3.1.** If $G_{ac}$ is acyclic, then the augmented Datalog program is stratifiable, and semi-naive evaluation computes the unique minimal model.

*Proof.* A Datalog program with stratified negation has a unique minimal model (the perfect model, Apt, Blair & Walker 1988). Stratification requires that no predicate depends positively on itself through a cycle. If $G_{ac}$ is acyclic, then there is a topological ordering of predicates such that every rule's consequent appears after all its antecedents — this IS a stratification. The scope exclusions (negated predicates in rule bodies) cannot create cycles because they reference predicates that are lower in the topological order (they are facts about the entity, not derived from the consequent). Therefore the program is stratifiable and the minimal model exists and is unique. $\square$

**Consequence for extraction.** The pipeline must detect cycles in the augmented $G_{ac}$ and remove offending vyaptis. The `_detect_cycles()` function implements DFS-based cycle detection with $O(|V| + |E|)$ complexity.

### 3.3 Invariant I3: Pydantic Schema Conformance

**Statement.** Every proposed vyapti must instantiate as a valid `Vyapti(BaseModel)` from `schema.py`.

**Justification.** The `Vyapti` model (`schema.py`, lines 68-92) defines mandatory fields:
- `id: str` — unique identifier
- `name: str` — human-readable name
- `statement: str` — natural language description of the invariable relation
- `causal_status: CausalStatus` — one of {structural, regulatory, empirical, definitional}
- `confidence: Confidence` — (existence: float, formulation: float, evidence: str)
- `epistemic_status: EpistemicStatus` — one of {established, hypothesis, open, contested}
- `antecedents: list[str]` — predicate names required
- `consequent: str` — predicate name produced

The T2 compiler (`t2_compiler_v4.py`) reads these fields to construct arguments and derive provenance tags via `_build_rule_tag()`. A malformed vyapti would cause compilation failure or, worse, silently produce incorrect provenance tags.

**Consequence for extraction.** Stage E performs Pydantic validation as a mandatory gate. Enum values that fail to parse are mapped to safe defaults (`CausalStatus.EMPIRICAL`, `EpistemicStatus.WORKING_HYPOTHESIS`, `DecayRisk.MODERATE`).

### 3.4 Invariant I4: Datalog Compilation Compatibility

**Statement.** The augmented knowledge store must successfully compile through the `DatalogEngine`, with synthetic facts for all antecedent predicates, and terminate within the safety bound.

**Justification.** This is an end-to-end integration test that the augmented KB satisfies invariants I1-I3 simultaneously. The Datalog engine's safety bound (`datalog_engine.py`, lines 211-217) is:

$$\text{max\_iterations} = |\mathcal{R}| \times (|\text{facts}| + 1) + 1$$

If evaluation exceeds this bound, a `RuntimeError` is raised — indicating a bug in the rule definitions (not a property of the extraction, since Datalog over the five-element Heyting algebra terminates by Theorem 2.4).

### 3.5 Invariant I5: Monotone Enrichment

**Statement.** The augmented knowledge store is a *superset* of the seed: $K_0 \subseteq K^*$. No existing vyapti, hetvabhasa, or reference is modified or removed.

**Justification.** The extraction pipeline is purely additive. This ensures:
1. **Regression safety.** All existing tests (e.g., `test_business_expert.py`, 508 lines, testing chain derivation V01-V08, rebutting attacks V01 vs V11, undercutting from scope exclusions, grounded semantics, contestation protocols, and uncertainty quantification) pass unchanged on the augmented KB.
2. **Monotone refinement.** In the lattice of knowledge stores ordered by $\subseteq$, extraction is a monotone operator: $K_0 \subseteq f(K_0) = K^*$. Iterating extraction ($K^{(n+1)} = f(K^{(n)})$) converges to a fixpoint because the predicate space is finite.
3. **Human trust.** Domain experts who verified the seed KB need not re-verify it after extraction — their approval is preserved.

---

## 4. The Six-Stage Decomposition

We decompose the extraction problem into six stages, each with a formally distinct correctness condition. The decomposition follows the ontology learning layer cake (Buitelaar, Cimiano & Magnini 2005; Cimiano 2006), adapted to the specific constraints of the Anvikshiki architecture.

### 4.1 Stage A: Candidate Extraction

**Function.** $f_A: (G, P_0) \to \mathcal{C}$ where $\mathcal{C}$ is a set of candidate predicates with provenance.

**Correctness condition.** Each candidate $c \in \mathcal{C}$ must:
- Be a valid snake_case identifier matching the regex `^[a-z][a-z0-9]*(_[a-z0-9]+)*$`
- Have a natural language description grounded in a specific sentence of $G$
- Have a claim type from {causal, conditional, metric, definitional, scope, negation}
- Have a provenance record linking to chapter, section, and paragraph

**Theoretical basis.** This is the *term extraction* layer of ontology learning (Cimiano 2006, Chapter 3). The key distinction from generic Open Information Extraction (Banko et al. 2007) is that we extract *unary predicates* (testable properties), not *binary relations* (subject-predicate-object triples). This is mandated by Invariant I1 (flat predicates).

The claim type taxonomy {causal, conditional, metric, definitional, scope, negation} is derived from the vyapti structure. Each type maps to a different role in the argumentation framework:
- **Causal** ($X \Rightarrow Y$): directly compiles to a defeasible rule
- **Conditional** (if $X$ then $Y$): same, with explicit scope conditions
- **Metric** ($X$ measured by $Y$): produces a predicate for the threshold (e.g., `ltv_exceeds_cac`)
- **Definitional** ($X$ means $Y$): compiles to a strict rule ($\mathcal{R}_s$)
- **Scope** ($X$ holds when $Y$): produces a scope condition on an existing vyapti
- **Negation** ($X$ prevents $Y$): produces a scope exclusion or rebutting pair

**Implementation.** DSPy `ChainOfThought(ExtractPredicates)` with the seed ontology as context. The seed constrains extraction via the PARSE pattern (Amazon 2025): the schema description functions as a "learnable NL contract" that guides the LLM to extract predicates *compatible with* the existing vocabulary.

### 4.2 Stage B: Hierarchical Decomposition

**Function.** $f_B: (\mathcal{C}, V_0, G) \to \mathcal{T}$ where $\mathcal{T}$ is a predicate tree (forest of parent-child relationships).

**Correctness condition.** Each decomposition $t \in \mathcal{T}$ must:
- Have a parent predicate that exists in $P_0$ (anchoring to the seed)
- Specify a relation type: COMPOSES (parent = AND of children), ALTERNATIVE (parent = OR of children), SUBSUMES (parent generalizes child)
- Preserve the depth bound: no decomposition deeper than `config.decomposition_max_depth`

**Theoretical basis.** This is the *concept hierarchy* layer of ontology learning. In Formal Concept Analysis (Ganter & Wille 1999), concepts form a lattice under the subconcept relation. Our decomposition is a restricted form: we only decompose existing predicates (from $V_0$) into sub-predicates, using the guide text as the formal context.

The three relation types map to logical composition:
- **COMPOSES**: $\text{parent}(E) \leftarrow \text{child}_1(E) \wedge ... \wedge \text{child}_n(E)$ — the parent is a conjunction of children. This produces a new vyapti with children as antecedents and parent as consequent.
- **ALTERNATIVE**: $\text{parent}(E) \leftarrow \text{child}_1(E)$ and $\text{parent}(E) \leftarrow \text{child}_2(E)$ — each child independently implies the parent. This produces multiple vyaptis.
- **SUBSUMES**: $\text{child}(E) \rightarrow \text{parent}(E)$ — the child is a special case. This is a strict rule.

**Seed ontology bootstrapping.** The decomposition is seeded by existing vyaptis — we decompose V01's `positive_unit_economics` into its constituent conditions (`ltv_exceeds_cac`, `positive_contribution_margin`, `payback_within_runway`) because the guide text for V01's chapter describes these as components. This is the approach advocated by the LLMs4OL workshop (2024) and the NELL project (Carlson et al. 2010): existing ontological structure constrains and guides extraction.

### 4.3 Stage C: Canonicalization and Deduplication

**Function.** $f_C: (\mathcal{C}, \mathcal{T}) \to (P_{new}, S)$ where $P_{new}$ is the canonical vocabulary and $S$ is a set of synonym clusters.

**Correctness condition.** The canonical vocabulary must:
- Contain no duplicates (each concept has exactly one name)
- Use consistent naming conventions (matching the seed's style)
- Preserve all distinct concepts from $\mathcal{C}$ and $\mathcal{T}$ (no concept loss)

**Theoretical basis.** This is the *synonym resolution* and *concept formation* layers of ontology learning. We use a two-phase approach inspired by BELHD (2024):

1. **Deterministic pre-filter.** Token-overlap clustering (Jaccard similarity on underscore-split tokens, threshold $> 0.5$). This is cheap ($O(n^2)$ comparisons but no LLM calls) and catches obvious duplicates like `ltv_above_cac` and `ltv_exceeds_cac`.

2. **LLM disambiguation.** Only for ambiguous clusters (multiple predicates sharing $>50\%$ tokens). This uses DSPy `ChainOfThought(ResolveSynonyms)` with existing naming examples as style reference.

The embedding-first approach reduces LLM calls by 60-80% compared to all-LLM canonicalization (BELHD 2024), while preserving the semantic judgment needed for borderline cases.

**Token-overlap as soft matching.** For evaluation purposes, we define a similarity function:

$$\text{sim}(a, b) = \frac{|\text{tokens}(a) \cap \text{tokens}(b)|}{|\text{tokens}(a) \cup \text{tokens}(b)|}$$

where $\text{tokens}(p)$ is the set of underscore-separated tokens in predicate name $p$. This catches `ltv_above_cac` $\approx$ `ltv_exceeds_cac` (sim = 0.5, sharing `ltv` and `cac`). For formal evaluation with gold standards, this serves as a BERTScore-free soft matcher (Zhang et al. 2020).

### 4.4 Stage D: Vyapti Construction

**Function.** $f_D: (P_{new}, \mathcal{T}, G, V_0) \to V_{new}$ where $V_{new}$ is a set of proposed vyaptis.

**Correctness condition.** Each proposed vyapti must:
- Have antecedents and consequent from $P_0 \cup P_{new}$
- Have a valid `causal_status` from the `CausalStatus` enum
- Have `confidence_existence` $\leq 0.85$ and `confidence_formulation` $\leq 0.85$ (the conservative cap)
- Have `epistemic_status = "hypothesis"` unless the guide text provides explicit strong evidence

**Theoretical basis.** This stage constructs new defeasible rules ($\mathcal{R}_d$) for the ASPIC+ framework. The construction must respect the Nyaya principle of vyapti: an invariable concomitance between hetu (reason/antecedent) and sadhya (conclusion/consequent), grounded in observed instances (Matilal 1971/2005; Bhardwaj 2026, Section 2.3).

The DSPy `ChainOfThought(ConstructVyapti)` module takes the predicate relationship, guide evidence, existing vyaptis context, and reference bank as inputs. The reward function penalizes:
- Overconfident extraction: $\text{confidence} > 0.85$ loses 0.15 points
- Non-conservative epistemic status: `established` loses 0.15 points
- Missing scope conditions: no scope awareness loses 0.15 points
- Missing sources: no provenance loses 0.15 points

This reward structure encodes the Nyaya principle that inference (anumana) must be qualified — an unqualified claim is itself a hetvabhasa (fallacy of reasoning).

### 4.5 Stage E: Validation and Merge (Deterministic)

**Function.** $f_E: (V_{new}, K_0) \to (K^*, \text{ValidationResult})$ with **zero LLM calls**.

**Correctness condition.** The augmented $K^*$ must satisfy all five invariants from Section 3.

**Implementation.** Five sequential checks:

1. **DAG cycle detection** (Invariant I2). DFS-based topological sort on the augmented $G_{ac}$. Complexity: $O(|V| + |E|)$. Vyaptis participating in cycles are removed.

2. **Pydantic schema validation** (Invariant I3). Each `ProposedVyapti` is converted to a `Vyapti(BaseModel)` instance. Invalid enum values fall back to safe defaults.

3. **Datalog test-compilation** (Invariant I4). The augmented KB is loaded into a `DatalogEngine`, synthetic facts are added for all antecedent predicates, and `evaluate()` is called. Termination within the safety bound is verified.

4. **Orphan predicate detection.** Predicates appearing as antecedents but never as consequents (except base facts) are flagged. These are warnings, not errors — they represent predicates that can only be established by direct assertion.

5. **Coverage ratio computation.**

$$\text{coverage} = \frac{|P_{new} \setminus P_0|}{\max(|P_{new} \cup P_0|, 1)}$$

This measures the fraction of the augmented vocabulary that is genuinely new.

**Why Stage E is deterministic.** All five checks are symbolic computations with no LLM involvement. This is by design: the validation stage must be **reproducible** — the same proposed vyaptis must always produce the same validation result. Introducing LLM calls would make validation non-deterministic, violating the engine's guarantee that "the same KB + query always produces the same AF and extension" (Bhardwaj 2026, Section 8.2).

### 4.6 Stage F: Human-in-the-Loop Review

**Function.** $f_F: (K^*, \text{ValidationResult}) \to K_{approved}$ via human judgment.

**Correctness condition.** Human review is the final gate. Each proposed vyapti receives an accept/reject/modify decision. Only accepted vyaptis enter the approved knowledge store.

**Theoretical basis.** This is the *ontology evaluation* layer (Buitelaar et al. 2005), and it is mandated by the Contestable AI framework. Moreira et al. (2025) require "openness to contestation" and "ease of contestation" — the HITL stage provides exactly this. The human reviewer is exercising *vada* (honest inquiry, the cooperative contestation mode from Nyaya debate theory; Bhardwaj 2026, Section 8.6), jointly refining the knowledge base with the extraction pipeline.

Alfrink et al. (2023) argue that human controllers should be put "in dialogue" with AI systems. The HITL stage realizes this: the pipeline proposes, the human disposes, and the decisions persist as the approved KB.

---

## 5. Theoretical Grounding of Design Decisions

Each design decision in the extraction pipeline is grounded in the formal framework. This section makes the theory-to-implementation mapping explicit.

### 5.1 Decision D1: Flat Predicates Only

**Design decision.** All extracted predicates are unary: `predicate_name(Entity)`. Binary relationships are encoded as compound predicate names (e.g., `ltv_exceeds_cac` rather than `exceeds(ltv, cac)`).

**Theoretical grounding.** Invariant I1 (Section 3.1). The Datalog engine's termination guarantee depends on the finite Herbrand base, which requires function-free, fixed-arity atoms. Unary predicates over a single entity type give the tightest bound: $O(|P| \times |E|)$ ground facts, and every rule fires at most once per entity.

Furthermore, the ASPIC+ framework in the Anvikshiki engine represents arguments as trees of unary conclusions (`schema_v4.py`, lines 1137-1147: `Argument.conclusion: str` is a single predicate name). Binary predicates would require a different argument representation.

**Tradeoff.** We lose the ability to represent quantitative relationships (e.g., "LTV is 3x CAC"). However, the guide text typically makes qualitative claims ("LTV must exceed CAC"), which are naturally expressible as unary threshold predicates. Quantitative reasoning, where needed, can be handled by the grounding module's embedding-based similarity matching.

### 5.2 Decision D2: Conservative Epistemic Defaults

**Design decision.** All extracted vyaptis default to `epistemic_status = "hypothesis"` with `confidence_existence <= 0.85` and `confidence_formulation <= 0.85`.

**Theoretical grounding.** This follows directly from the Nyaya pramana hierarchy (Bhardwaj 2026, Section 2.2).

The extraction pipeline processes guide text via LLM. The guide text is a form of *sabda* (testimony) — the original domain sources speak through the guide, and the LLM interprets their testimony. The pramana ordering (Bhardwaj 2026, Section 7.2) places sabda below anumana (inference) and pratyaksa (direct evidence):

$$\text{Pratyaksa}(4) > \text{Anumana}(3) > \text{Sabda}(2) > \text{Upamana}(1)$$

In the T2 compiler, `_build_rule_tag()` maps `CausalStatus.EMPIRICAL` to `PramanaType.ANUMANA` (Bhardwaj 2026, Section 9.7, lines 1530-1535). Extracted vyaptis, being derived from sabda, should not claim higher epistemic status than anumana-derived rules already in the KB.

**Concretely.** In the ProvenanceTag (Bhardwaj 2026, Section 7.3), `epistemic_status = "hypothesis"` maps to belief/disbelief/uncertainty tuple $(0.6, 0.1, 0.3)$. The confidence cap of 0.85 ensures that $\text{trust} = \text{existence} \times \text{formulation} \leq 0.85 \times 0.85 = 0.7225$ — always below the trust scores of human-verified vyaptis (which have existence and formulation in the 0.85-0.95 range).

This means extracted vyaptis will always lose preference contests against seed vyaptis. A new vyapti for `ltv_exceeds_cac => positive_unit_economics` will never override the existing V01 for `positive_unit_economics => value_creation` — it can only *refine* V01 by providing sub-structure.

### 5.3 Decision D3: Seed Ontology Bootstrapping

**Design decision.** The extraction pipeline takes the existing KnowledgeStore as input and uses it to constrain extraction. Existing predicate names and vyapti structures are provided to the LLM as context.

**Theoretical grounding.** This is the *seed ontology bootstrapping* approach (LLMs4OL 2024; Carlson et al. 2010, NELL project). The theoretical foundation is that ontology learning from text is underdetermined — the same text can yield many possible ontologies. The seed provides the *inductive bias* that selects the correct ontology.

**Formally.** Let $\mathcal{O}$ be the space of all possible predicate vocabularies extractable from text $G$. Without a seed, the extraction function $f: G \to \mathcal{O}$ is one-to-many. With seed $K_0$, the function becomes $f: (G, K_0) \to \mathcal{O}|_{K_0}$ where $\mathcal{O}|_{K_0} \subset \mathcal{O}$ is the subset of vocabularies compatible with $K_0$.

Compatibility means:
1. New predicates use the same naming convention as $P_0$ (enforced by providing existing names as style reference)
2. New vyaptis connect to existing predicates (enforced by Stage B's anchoring requirement)
3. The augmented vocabulary preserves the domain type's epistemic character (a CRAFT domain produces empirical rules, not structural ones)

### 5.4 Decision D4: Embedding-First Deduplication

**Design decision.** Stage C uses token-overlap clustering (deterministic, cheap) as a pre-filter, invoking the LLM only for ambiguous clusters.

**Theoretical grounding.** The BELHD approach (2024) shows that embedding-based clustering handles 60-80% of synonym resolution without LLM calls. For the Anvikshiki pipeline, the stronger claim holds: snake_case predicate names are *already tokenized* by underscores, so token-overlap (Jaccard similarity) captures most semantic similarity without embeddings.

**Formal analysis.** For $n$ candidate predicates, all-LLM resolution requires $O(n^2)$ LLM comparisons (or $O(n)$ batch calls). Token-overlap clustering requires $O(n^2)$ string comparisons (microseconds each). The LLM is only called for clusters of size $>1$ — typically $<20\%$ of predicates. Total LLM calls: $O(1)$ (one batch call for ambiguous clusters) vs $O(n)$ (for all-LLM).

This is not merely an optimization. It is architecturally important because the Datalog engine's determinism requirement (Section 4.5) extends to the canonicalization stage: if the same candidates are extracted twice, they should produce the same canonical vocabulary. Token-overlap is deterministic; LLM resolution is not. By minimizing LLM calls, we maximize reproducibility.

### 5.5 Decision D5: Deterministic Validation (Stage E)

**Design decision.** Stage E uses zero LLM calls. All validation is symbolic.

**Theoretical grounding.** The parent thesis's fundamental design principle (Bhardwaj 2026, Section 8.2):

> "The full architecture confines the LLM to what it's actually good at: natural language understanding (grounding: NL -> predicates) and natural language generation (synthesis: results -> calibrated response). Everything between — argument construction, attack computation, extension evaluation, provenance tracking — is deterministic and symbolic."

Stage E is "everything between." The validation checks (cycle detection, schema conformance, Datalog compilation) are precisely the kind of deterministic verification that should NOT involve an LLM. The pipeline structure mirrors the engine's own architecture: LLM at the boundaries (Stages A-D for extraction, Stage F for human review), symbolic computation in the middle (Stage E for validation).

### 5.6 Decision D6: Iterative Refinement

**Design decision.** The pipeline can run multiple passes, using the augmented KB as the new seed for re-extraction.

**Theoretical grounding.** The iterative refinement approach (Nature 2025) shows that 3-phase extract-revise-validate improves F1 by 5-15%. In our framework, iteration is formally justified as fixpoint computation over the knowledge store lattice.

**Theorem 5.1.** Let $f: K \to K$ be the extraction pipeline (treating it as a function from knowledge stores to augmented knowledge stores). If $f$ is monotone ($K_1 \subseteq K_2 \implies f(K_1) \subseteq f(K_2)$) and the predicate space is finite, then the sequence $K_0, f(K_0), f^2(K_0), ...$ converges to a fixpoint $K^* = f(K^*)$.

*Proof.* By Invariant I5 (monotone enrichment), $K_0 \subseteq f(K_0) \subseteq f^2(K_0) \subseteq ...$. The predicate space is finite (bounded by the number of distinct predicate names extractable from $G$, which is finite). An ascending chain in a finite lattice must stabilize. Therefore the sequence has a fixpoint. $\square$

The implementation uses an improvement threshold of 2%: if the coverage ratio improves by less than 2% between passes, the iteration terminates. This is a practical approximation of fixpoint detection.

---

## 6. Evaluation Theory

### 6.1 The Composite Metric

We define a composite evaluation metric $M$ as a weighted sum of seven component metrics:

$$M = \sum_{i=1}^{7} w_i \cdot m_i \quad \text{where} \quad \sum_i w_i = 1$$

| Component $m_i$ | Weight $w_i$ | Formal Justification |
|---|---|---|
| Predicate precision | 0.20 | Standard IR metric: fraction of extracted predicates in the gold set |
| Predicate recall | 0.20 | Standard IR metric: fraction of gold predicates that were extracted |
| Naming quality | 0.15 | Invariant I1 compliance: valid snake_case, not generic, < 50 chars |
| Vyapti completeness | 0.15 | Invariant I3 compliance: all `Vyapti` fields populated |
| DAG validity | 0.10 | Invariant I2 compliance: no cycles introduced |
| Coverage ratio | 0.10 | Non-triviality: meaningful expansion over seed |
| Zero-section rate | 0.10 | Extraction thoroughness: low missed-content rate |

### 6.2 Weight Justification

**Precision and recall (0.20 each, total 0.40).** These are the primary quality metrics. They measure whether the pipeline extracts the *right* predicates. Equal weighting reflects that false positives (noisy predicates) and false negatives (missed predicates) are equally harmful: noisy predicates pollute the argumentation framework; missed predicates leave the granularity gap open.

**Naming quality (0.15).** This is not cosmetic. Invalid predicate names cause compilation failure (Invariant I1). Generic names (e.g., `value`, `data`) conflate distinct concepts, producing incorrect inference. The 0.15 weight reflects that naming errors are serious but correctable (Stage C can fix them).

**Vyapti completeness (0.15).** Incomplete vyaptis produce incomplete provenance tags. The T2 compiler's `_build_rule_tag()` (Bhardwaj 2026, Section 9.7) reads causal_status, epistemic_status, confidence, and sources to construct the ProvenanceTag. Missing fields produce default tags that may not reflect the actual epistemic situation.

**DAG validity (0.10).** Binary: either cycles exist or they don't. Weighted at 0.10 because cycle detection is a hard gate — a single cycle causes vyapti removal, which is already handled by Stage E. The metric tracks whether cycles occurred, not whether they were resolved.

**Coverage ratio (0.10).** Measures whether the extraction was non-trivial. A coverage ratio of 0 means nothing was added; a ratio of 0.5 means half the augmented vocabulary is new. The 0.10 weight reflects that coverage is important but secondary to quality.

**Zero-section rate (0.10).** Measures extraction thoroughness. A high zero-section rate (many sections yielding no predicates) suggests the extraction prompt is too restrictive or the guide text is not being adequately processed. At 0.10, this serves as a diagnostic signal.

### 6.3 Soft Matching via Token Overlap

For precision and recall, we use soft matching to handle synonym variation. The similarity function (Section 4.3) serves as a lightweight alternative to BERTScore (Zhang et al. 2020):

$$\text{match}(p, G) = \begin{cases} 1.0 & \text{if } p \in G \\ \text{sim}(p, g^*) & \text{if } \max_{g \in G} \text{sim}(p, g) \geq \theta \\ 0.0 & \text{otherwise} \end{cases}$$

where $\theta = 0.5$ is the matching threshold and $g^* = \arg\max_{g \in G} \text{sim}(p, g)$.

This catches the most common variation pattern: synonym substitution of a single token (e.g., `ltv_above_cac` vs `ltv_exceeds_cac` — Jaccard = $\frac{|\{ltv, cac\}|}{|\{ltv, above, cac, exceeds\}|} = 0.5$).

---

## 7. Relationship to the Parent Architecture

### 7.1 Where Extraction Sits in the Pipeline

The Anvikshiki engine pipeline (Bhardwaj 2026, Section 9.8) is:

```
Query (NL) -> Grounding -> T2 Compilation -> Extension Computation
           -> Epistemic Status -> Provenance -> Uncertainty -> Synthesis
```

The extraction pipeline sits *before* this, at **KB construction time**:

```
Seed KB + Guide Text -> Extraction Pipeline -> Augmented KB
                                                    |
Query (NL) -> Grounding -> T2 Compilation -> ...   <-+
```

Extraction is a *compile-time* process. It enriches the KB once. The enriched KB is then used for all subsequent queries. This means extraction cost is amortized over all queries — a key economic advantage over approaches that extract knowledge at query time (like ArgLLMs, which generates arguments per query).

### 7.2 How New Predicates Flow Through the Architecture

Once a new predicate enters $K^*$, it automatically becomes available to every downstream module:

1. **Grounding** (`grounding.py`, `OntologySnippetBuilder.build()`): Constructs vocabulary from all vyapti antecedents/consequents. New predicates are immediately included in the ontology snippet used by the LLM to ground user queries.

2. **T2 Compilation** (`t2_compiler_v4.py`, `compile_t2()`): Iterates over `knowledge_store.vyaptis`. New vyaptis produce new arguments and new potential attacks.

3. **Argumentation** (`argumentation.py`, `compute_grounded()`): The grounded extension computation is over the full AF, including arguments from new vyaptis.

4. **Synthesis** (`engine_v4.py`): The synthesizer receives all accepted and defeated arguments, including those from new vyaptis.

No existing module needs modification. This is a direct consequence of the architecture's design: all modules read from the `KnowledgeStore`, and the `KnowledgeStore` is the single source of truth.

### 7.3 The Pramana Status of Extracted Knowledge

Extracted knowledge enters the system at the *sabda* level — it is testimony from the guide text, mediated by LLM interpretation. In the pramana hierarchy:

$$\text{Human-verified vyaptis (anumana)} > \text{Extracted vyaptis (sabda)} > \text{Analogical transfer (upamana)}$$

This means:
- Extracted vyaptis can be **undercut** by human-verified vyaptis (badhita — sublation by higher pramana)
- Extracted vyaptis can **refine** but not **override** existing vyaptis
- Extracted vyaptis start as `hypothesis` and can be **promoted** through human review (Stage F) or through accumulation of evidence across multiple extraction passes

This is epistemically honest: the system never claims more certainty for extracted knowledge than the extraction process warrants.

---

## 8. Conclusion

We have provided a theoretical foundation for automated predicate extraction in the Anvikshiki framework. The key results are:

1. **The granularity problem is a vocabulary problem.** The architecture can handle hundreds of predicates; the bottleneck is KB authoring, not inference complexity.

2. **Five invariants constrain extraction.** Flat predicates (I1), DAG acyclicity (I2), schema conformance (I3), Datalog compatibility (I4), and monotone enrichment (I5) are jointly necessary and sufficient for the augmented engine to preserve its correctness guarantees.

3. **Conservative defaults are epistemically mandated.** By the Nyaya pramana hierarchy, LLM-extracted knowledge enters as sabda (testimony) and must earn higher status through argumentation and human verification.

4. **The six-stage decomposition is formally motivated.** Each stage corresponds to a layer of the ontology learning stack, adapted to the specific constraints of argumentation over provenance semirings.

5. **Iterative extraction converges.** The pipeline is a monotone operator on a finite lattice of knowledge stores, guaranteeing fixpoint convergence.

The extraction pipeline closes the gap between the engine's theoretical capacity and its practical vocabulary, transforming the Anvikshiki Engine from "epistemically honest but strategically mute" to a system that can reason at the granularity of the domain knowledge it encodes.

---

## References

### Parent Architecture

- **Bhardwaj, M.** "The Anvikshiki Engine (v4): From Nyaya Epistemology to Neurosymbolic Argumentation: A Unified Architecture via Structured Argumentation over Provenance Semirings." 2026.

### Argumentation Theory

- **Dung, P.M.** "On the Acceptability of Arguments and Its Fundamental Role in Nonmonotonic Reasoning, Logic Programming, and n-Person Games." *Artificial Intelligence* 77(2), 321-357, 1995.
- **Prakken, H.** "An Abstract Framework for Argumentation with Structured Arguments." *Argument & Computation* 1(2), 93-124, 2010.
- **Modgil, S. & Prakken, H.** "A General Account of Argumentation with Preferences." *Artificial Intelligence* 195, 361-397, 2013.
- **Caminada, M. & Amgoud, L.** "On the Evaluation of Argumentation Formalisms." *Artificial Intelligence* 171(5-6), 286-310, 2007.
- **Wu, Y., Caminada, M. & Gabbay, D.** "Complete Extensions in Argumentation Coincide with 3-Valued Stable Models in Logic Programming." *Studia Logica* 93, 383-403, 2009.
- **Diller, M., Keshavarzi Zafarghandi, A. & Wallner, J.P.** "Grounding ASPIC+ with Datalog." *Proceedings of KR 2025*.

### Provenance Semirings and Datalog

- **Green, T.J., Karvounarakis, G. & Tannen, V.** "Provenance Semirings." *Proceedings of PODS 2007*, 31-40. ACM.
- **Khamis, M.A., Ngo, H.Q., Pichler, R., Suciu, D. & Wang, Y.R.** "Convergence of Datalog over (Pre-) Semirings." *Proceedings of PODS 2022*. ACM.
- **Li, Z., Huang, J. & Naik, M.** "Scallop: A Language for Neurosymbolic Programming." *Proceedings of PLDI 2023*. ACM.
- **Madsen, M., Yee, M.-H. & Lhotak, O.** "From Datalog to Flix: A Declarative Language for Fixed Points on Lattices." *Proceedings of PLDI 2016*. ACM.
- **Apt, K.R., Blair, H.A. & Walker, A.** "Towards a Theory of Declarative Knowledge." *Foundations of Deductive Databases and Logic Programming*, 89-148, 1988.
- **Chandra, A.K. & Merlin, P.M.** "Optimal Implementation of Conjunctive Queries in Relational Data Bases." *Proceedings of STOC 1977*, 77-90. ACM.

### Nyaya Epistemology

- **Matilal, B.K.** *Epistemology, Logic, and Grammar in Indian Philosophical Analysis.* Mouton, 1971; new edition edited by J. Ganeri, Oxford University Press, 2005.
- **Ganeri, J.** "Ancient Indian Logic as a Theory of Case-Based Reasoning." *Journal of Indian Philosophy* 31, 33-45, 2003.
- **Guhe, E.** *An Indian Theory of Defeasible Reasoning: The Doctrine of Upadhi in the Upadhidarpana.* Harvard Oriental Series, Harvard University Press, 2022.
- **Oetke, C.** "Ancient Indian Logic as a Theory of Non-Monotonic Reasoning." *Journal of Indian Philosophy* 24, 447-539, 1996.
- **Keating, M.** "The Pragma-Dialectics of Dispassionate Discourse: Early Nyaya Argumentation Theory." *Religions* 12(10), 875, 2021.

### Subjective Logic

- **Josang, A.** *Subjective Logic: A Formalism for Reasoning Under Uncertainty.* Springer, 2016.

### Ontology Learning

- **Buitelaar, P., Cimiano, P. & Magnini, B.** (eds.) *Ontology Learning from Text: Methods, Evaluation and Applications.* IOS Press, 2005.
- **Cimiano, P.** *Ontology Learning and Population from Text: Algorithms, Evaluation and Applications.* Springer, 2006.
- **Ganter, B. & Wille, R.** *Formal Concept Analysis: Mathematical Foundations.* Springer, 1999.

### Open Information Extraction

- **Banko, M., Cafarella, M.J., Soderland, S., Broadhead, M. & Etzioni, O.** "Open Information Extraction from the Web." *Proceedings of IJCAI 2007*.

### LLM-Based Extraction (2024-2026)

- **KGGen.** "Knowledge Graph Generation with DSPy + Pydantic." *ISWC 2024*.
- **PARSE.** "Schemas as Learnable NL Contracts for Autonomous Prompt Optimization." *Amazon 2025*.
- **LLMs4OL.** "LLMs for Ontology Learning." *Workshop, 2024*.
- **BELHD.** "Embedding-First Deduplication for Entity Resolution." *2024*.
- **Nature 2025.** "Iterative Refinement for Structured Extraction." *Nature*, 2025.

### Seed Ontology Bootstrapping

- **Carlson, A., Betteridge, J., Kisiel, B., Settles, B., Hruschka, E.R. & Mitchell, T.M.** "Toward an Architecture for Never-Ending Language Learning." *Proceedings of AAAI 2010*.

### Evaluation

- **Zhang, T., Kishore, V., Wu, F., Weinberger, K.Q. & Artzi, Y.** "BERTScore: Evaluating Text Generation with BERT." *ICLR 2020*.

### Contestable AI

- **Moreira, C. et al.** "Contestable AI Systems: A Comprehensive Framework." 2025.
- **Alfrink, K., Keller, I., Doorn, N. & Kortuem, G.** "Contestable AI by Design: Towards a Framework." *Minds and Machines* 33, 613-639, 2023.
- **Leofante, F., Toni, F., Rago, A., Ferme, E. & Reis, J.** "Contestable AI Needs Computational Argumentation." *Proceedings of KR 2024*.
- **Freedman, R. et al.** "ArgLLMs: Large Language Models for Argumentation." *Proceedings of AAAI 2025*.

### DSPy Framework

- **Khattab, O. et al.** "DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines." *ICLR 2024*.
