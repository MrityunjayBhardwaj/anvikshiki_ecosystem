# The Ānvīkṣikī Engine (v4)

## From Nyāya Epistemology to Neurosymbolic Argumentation: A Minimal Complete Architecture via Structured Argumentation with Subjective Logic Annotation

---

**Abstract.** This thesis presents a revised architecture for the Ānvīkṣikī Engine — a neurosymbolic reasoning system that compiles structured domain knowledge into an executable inference engine with principled epistemic qualification. The prior architecture (v3, this thesis's predecessor) achieved its goals through a composite of six independent formalisms — a Heyting lattice for epistemic status, a cellular sheaf for consistency checking, hand-specified trust tables for source authority, keyword-based hetvābhāsa detection, identity restriction maps, and hand-tuned uncertainty thresholds — producing a system that works but does not cohere. We term this the *Frankenstein problem*: each concern is solved by the best tool from a different intellectual tradition, and the resulting architecture has no single organizing principle.

This thesis proposes a minimal complete alternative: **structured argumentation (ASPIC+) with Subjective Logic annotation**, using Nyāya epistemology as the design ontology. We show that: (1) Nyāya concepts map naturally to argumentation concepts — vyāptis to defeasible rules, hetvābhāsas to defeat relations, pramāṇa hierarchy to argument preferences, epistemic status to extension membership; (2) Subjective Logic opinions (Jøsang 2016) combined with a product lattice for metadata handle quantitative aspects — evidence accumulation, trust propagation, temporal decay — as a principled composite of two well-defined algebraic structures; (3) the sheaf layer, Heyting lattice, trust table, and separate fallacy detection module all become unnecessary, as their functions are subsumed by the argumentation semantics; (4) Datalog can compute grounded argumentation semantics in polynomial time (Diller et al., KR 2025), preserving the tractability guarantees of the prior architecture. Furthermore, we show that the resulting architecture is **natively contestable** in the sense of the emerging Contestable AI literature (Leofante, Toni et al., KR 2024; Moreira et al. 2025) — satisfying all formal requirements for contestability through its argumentation structure, without requiring any additional post-hoc explanation mechanism.

We first establish why Nyāya epistemology — not Bayesian probability, not Dempster-Shafer theory, not reliabilism — is the correct philosophical framework for this class of problems, through a structured debate across five candidate epistemologies. We then conduct a systematic audit of the v3 architecture's hand-specified decisions, identifying 16 arbitrary choices across three severity tiers. We survey related work in neurosymbolic reasoning, computational argumentation, provenance-aware Datalog, and Contestable AI, identifying the specific shortcomings of each. We develop the mathematical foundations of provenance semirings and structured argumentation independently before showing how they compose. We present the unified architecture with an implementation sketch and complexity analysis. Finally, we compare the proposed system against both a simpler LLM+ASPIC+ baseline (ArgLLMs) and the requirements of the Contestable AI framework, demonstrating that the architecture is simultaneously the strongest existing instantiation of contestable AI principles for domain reasoning.

**Key contributions:**
1. A formal mapping between Nyāya epistemological categories and ASPIC+ argumentation primitives, filling a gap identified in the comparative philosophy literature
2. A minimal complete neurosymbolic architecture where epistemic status derives from argumentation semantics (extension membership) rather than being hand-assigned to lattice elements, with quantitative annotation via Subjective Logic
3. Elimination of 6 independent formalisms in favor of 2 that compose (argumentation structure + SL annotation with product lattice metadata), with a three-level property framework (formal guarantees, architectural principles, impossibility constraints) justifying the design
4. Preservation of all 7 desiderata from v3 (infer, constrain, qualify, decompose uncertainty, ground to sources, respect scope, decay gracefully) with stronger theoretical foundations
5. Native contestability — the architecture satisfies all 8 Contestable AI properties (Moreira et al. 2025) and all 4 requirements of the computational argumentation approach to contestability (Leofante et al., KR 2024), through its argumentation structure rather than post-hoc mechanisms
6. Three formally distinct contestation protocols derived from Nyāya debate theory (vāda/jalpa/vitaṇḍā), mapping to grounded/preferred/stable semantics — a vocabulary for different *modes* of contestation that no existing Contestable AI system provides

---

## Table of Contents

1. Why Bother? — Motivation, Objectives, Constraints
2. Ānvīkṣikī: The Framework
   - 2.1 Why Nyāya Epistemology?
   - 2.2 The Four Pramāṇas as Typed Epistemic Channels
   - 2.3 Vyāpti, Hetvābhāsa, and the Pañcāvayava
   - 2.4 The Meta-Prompt and Compilation Targets
3. The Epistemological Debate: Choosing the Right Framework
   - 3.1 Candidate 1: Bayesian Epistemology
   - 3.2 Candidate 2: Dempster-Shafer / Subjective Logic
   - 3.3 Candidate 3: Reliabilism
   - 3.4 Candidate 4: Argumentation Theory (ASPIC+)
   - 3.5 Candidate 5: Nyāya Epistemology
   - 3.6 The Verdict: Nyāya as Ontology, Argumentation as Calculus
4. The Prior Architecture and Its Shortcomings
   - 4.1 Summary of v3 Architecture
   - 4.2 The Frankenstein Problem
   - 4.3 Systematic Audit of Hand-Specified Decisions
   - 4.4 The Sheaf That Does Nothing
5. Related Work
   - 5.1 Neurosymbolic LLM Reasoning Systems
   - 5.2 Computational Argumentation
   - 5.3 Provenance-Aware Datalog
   - 5.4 LLM + Argumentation
   - 5.5 Contestable AI
   - 5.6 Nyāya in Formal Methods
6. Mathematical Foundations
   - 6.1 Provenance Semirings
   - 6.2 Structured Argumentation (ASPIC+)
   - 6.3 Gradual Semantics and Annotation-Valued Strength
   - 6.4 Computing Argumentation via Datalog
7. The Unified Architecture
   - 7.1 Design Principle: Nyāya Ontology → Argumentation Calculus
   - 7.2 The Nyāya-to-ASPIC+ Mapping
   - 7.3 The Provenance Tag
   - 7.4 What Becomes Unnecessary
   - 7.5 Why This Is Optimal
8. Comparison: Full Architecture vs. LLM+ASPIC+ and Contestable AI
   - 8.1 The LLM+ASPIC+ Baseline (ArgLLMs)
   - 8.2 Detailed Comparison with ArgLLMs / ArgRAG
   - 8.3 The Contestable AI Requirements
   - 8.4 Satisfying the Leofante et al. (KR 2024) Requirements
   - 8.5 The Henin & Le Métayer Hierarchy: Explainability < Justifiability < Contestability
   - 8.6 Nyāya Debate Types as Contestation Protocols
   - 8.7 Comparative Summary
   - 8.8 When the Baseline Suffices
9. Implementation Sketch
   - 9.1 Phase 1: DSPy Only (Baseline)
   - 9.2 Phase 2: DSPy + Abstract Argumentation
   - 9.3 Phase 3: DSPy + ASPIC+ over Provenance Semirings
   - 9.4 Phase 4: Full System with GraphRAG
   - 9.5 Core Data Structures
   - 9.6 The Argumentation Engine
   - 9.7 The Complete Pipeline
10. Further Directions
11. References

---

## 1. Why Bother? — Motivation, Objectives, Constraints

### 1.1 The Gap

There is a gap in how knowledge systems work today that most practitioners feel but few articulate precisely.

Large language models are extraordinary pattern matchers. They can write plausible essays on corporate strategy, generate code that compiles, and mimic the style of domain experts convincingly. But they cannot *reason* over a knowledge base with guarantees. Ask an LLM "given that this company has misaligned incentives and is in a declining market, what can we derive about its strategic position?" and it will generate a plausible paragraph. It will not — because it cannot — chain domain-specific rules, check whether the reasoning violates known fallacy patterns, verify that the claims are grounded in cited evidence, or decompose its uncertainty into "I don't have enough evidence" versus "the domain is inherently uncertain here."

Retrieval-Augmented Generation (RAG) addresses the grounding problem by retrieving relevant text chunks and feeding them to an LLM for synthesis. But RAG is similarity retrieval, not inference. It finds text that *looks* relevant. It cannot derive consequences, check prerequisites, detect scope violations, or prove that a conclusion follows from premises.

Knowledge graphs improve on flat retrieval by encoding relationships, but standard knowledge graphs have Boolean truth: an edge exists or it doesn't. In practice, domain knowledge carries epistemic qualification ("this is well-established," "this is a working hypothesis," "experts actively contest this"), scope conditions ("holds for private firms but not public ones"), decay markers ("this depends on the current regulatory environment"), and multiple inference modes ("this follows by causal mechanism" versus "this is observed empirical regularity" versus "this is expert consensus").

### 1.2 Objectives

The Ānvīkṣikī Engine exists to close this gap. It takes a structured domain knowledge base and compiles it into a system that can:

1. **Infer**, not just retrieve — chain domain rules to derive novel conclusions
2. **Constrain**, not just generate — detect and reject fallacious reasoning patterns
3. **Qualify**, not just assert — carry epistemic status through every inference step
4. **Decompose uncertainty** — separate "we don't know" from "nobody can know" from "the LLM might be wrong"
5. **Ground to sources** — trace every claim to its evidence
6. **Respect scope** — know when a rule applies and when it doesn't
7. **Decay gracefully** — halt inference on stale knowledge and trigger verification

### 1.3 Constraints

Any architecture must satisfy:

- **Model-agnostic**: No dependency on specific LLM capabilities (no fine-tuning required, no logit access assumed)
- **Polynomial termination**: Every query terminates in bounded time with formal guarantees
- **Inspectable**: Every conclusion carries a human-readable proof trace
- **Epistemically honest**: The system never claims more certainty than the evidence warrants
- **Incrementally buildable**: Can start simple and add capabilities without rewriting
- **Practically deployable**: Reasonable latency, cost, and infrastructure requirements

### 1.4 Usage

The engine serves as the reasoning backend for domain-specific knowledge systems. Given a pedagogical guide produced by the Ānvīkṣikī meta-prompt (a 3,963-line specification for generating expert-level instructional content), the engine compiles it into two subsystems:

- **T2** (Logic Engine): Executable inference over formalized domain rules
- **T3** (Retrieval Corpus): Graph-structured RAG over guide prose with rich metadata

At query time, a user poses a natural language question. The engine grounds it into structured predicates, performs formal inference, detects fallacies, traces provenance, decomposes uncertainty, and synthesizes a calibrated natural language response. The LLM handles what it's good at (language understanding and generation). The symbolic engine handles what it's good at (deterministic inference, constraint checking, proof construction).

---

## 2. Ānvīkṣikī: The Framework

### 2.1 Why Nyāya Epistemology?

The Ānvīkṣikī framework draws on Nyāya epistemology, one of the six orthodox schools of Indian philosophy, systematized by Gautama (c. 2nd century BCE) in the *Nyāya Sūtras* and refined over two millennia by Vātsyāyana, Uddyotakara, Vācaspati Miśra, Udayana, and Gaṅgeśa.

The choice of Nyāya is not decorative. It is load-bearing. Here is why:

**Nyāya is fundamentally about justified belief, not truth.** The central concept is *pramā* (valid cognition) — cognition that corresponds to reality AND is produced by a reliable means (*pramāṇa*). A belief can be accidentally true without being *pramā* if it wasn't produced by a valid means. This maps precisely to the engine's requirement: we need to know not just WHAT was derived, but HOW it was derived and WHETHER the derivation process was reliable.

**Nyāya classifies knowledge sources categorically, not just numerically.** Western Bayesian epistemology treats all evidence as fungible — everything gets a probability, and Bayes' theorem combines them. Nyāya insists that the *source type* matters categorically. Perception (pratyakṣa), inference (anumāna), testimony (śabda), and analogy (upamāna) are fundamentally different kinds of epistemic access with different failure modes. A claim backed by direct data fails differently than a claim backed by expert testimony, which fails differently than an analogical inference. For a system that needs to explain WHY it's uncertain — not just HOW MUCH — this distinction is essential.

**Nyāya has a native theory of inference failure.** The hetvābhāsa (fallacies of reasoning) are not a bolt-on quality check — they are integral to the theory of inference. Every valid inference (anumāna) must satisfy conditions that, when violated, produce specific, classifiable failure modes. This maps directly to integrity constraints in a reasoning engine.

**Nyāya's theory of testimony (śabda) formalizes source trust.** The two conditions for valid testimony — *āptavacana* (speaker competence) and *abhiyoga* (communicative sincerity) — provide a principled framework for treating source authority as an epistemic input, not an afterthought.

**Nyāya's debate theory provides the structure for conflict resolution.** The three types of debate — *vāda* (honest inquiry), *jalpa* (adversarial disputation), and *vitaṇḍā* (pure critique) — provide a vocabulary for different modes of reasoning under disagreement. As we will show, these map naturally to different argumentation semantics.

### 2.2 The Four Pramāṇas as Typed Epistemic Channels

The Nyāya school accepts four *pramāṇas* (valid means of knowledge), each with distinct computational analogues and failure modes:

| Pramāṇa | Meaning | Computational Analogue | Failure Mode | Defeat Type |
|----------|---------|----------------------|--------------|-------------|
| **Pratyakṣa** | Direct perception | Ground truth data, direct KB lookup, empirical measurement | Data quality, measurement error, sampling bias | Undermining (bad data) |
| **Anumāna** | Inference | Rule chaining, logical derivation, Datalog evaluation | Rule validity, scope violation, chain degradation | Undercutting (bad rule) |
| **Śabda** | Testimony | Expert claims, LLM generation, citations, published literature | Hallucination, authority misattribution, outdated claims | Rebutting (contradictory testimony) |
| **Upamāna** | Analogy | Embedding similarity, case-based reasoning, analogical transfer | False analogy, distribution shift, surface similarity | Undercutting (bad analogy) |

This is not merely a taxonomy. Each pramāṇa defines a *channel* through which knowledge enters the system, and each channel has a characteristic reliability profile and defeat condition. A Bayesian system would assign P=0.7 to outputs from all four channels indiscriminately. Nyāya says: the kind of justification matters for how you should doubt it.

**Gap identified:** No published work formally maps the four pramāṇas to computational knowledge representation formalisms (Ganeri 2003, Matilal 1971/2005, Guhe 2022 address the philosophical formalization but not the computational mapping). This is a contribution of the present work.

### 2.3 Vyāpti, Hetvābhāsa, and the Pañcāvayava

Three Nyāya constructs form the engine's core:

**Vyāpti** (invariable concomitance): The production rule. "Wherever there is smoke, there is fire" — formalized as `smoke(X) → fire(X)`. Each vyāpti has a causal status (structural, regulatory, empirical, definitional), scope conditions, confidence ratings, evidence quality markers, and decay characteristics. Vyāptis are the executable rules of the engine.

Crucially, a vyāpti is NOT merely a logical conditional. It is a *metaphysical* claim about the nature of the connection between *hetu* (reason) and *sādhya* (conclusion). The *pañcāvayava* (five-membered syllogism) includes the *udāharaṇa* (example) as a structural requirement — you must ground inference in observed instances. This is a built-in empirical grounding requirement that purely formal systems lack.

**Hetvābhāsa** (fallacious reason): The constraint. Gautama's *Nyāya Sūtra* classifies five types (Matilal 1971; Guhe 2022):

| Type | Sanskrit | Meaning | Argumentation Equivalent |
|------|----------|---------|--------------------------|
| 1 | **Savyabhicāra** | Inconclusive — the reason occurs with and without the conclusion | Undercutting defeat (attacks the inferential link) |
| 2 | **Viruddha** | Contradictory — the reason proves the opposite | Rebutting defeat (direct counter-argument) |
| 3 | **Satpratipakṣa** | Counterbalanced — equally strong counter-reason exists | Symmetric attack (neither argument prevails) |
| 4 | **Asiddha** | Unestablished — the reason itself is not proven | Undermining defeat (attacks the premise) |
| 5 | **Bādhita** | Sublated — overridden by a higher pramāṇa | Preference-based defeat (cross-modal override) |

Three of these five types map exactly to ASPIC+'s three attack types: asiddha = undermining, viruddha = rebutting, savyabhicāra ≈ undercutting (specifically scope-based undercutting). The remaining two — *bādhita* (cross-channel preference defeat) and *satpratipakṣa* (named symmetric deadlock) — have no direct ASPIC+ counterpart. Bādhita is handled in ASPIC+ via the generic preference relation, but Nyāya provides a *substantive theory* of what that preference should be (pramāṇa hierarchy). Satpratipakṣa is handled implicitly by grounded semantics (UNDECIDED), but Nyāya elevates it to a first-class pathology worth detecting and reporting. The five-way classification is thus not categorically richer in formal expressiveness — everything compiles to ASPIC+ — but it provides two additional named concepts with engineering value for explanation generation. Guhe (2022) draws explicit connections between the Navya-Nyāya doctrine of *upādhi* (defeating conditions) and Pollock's theory of defeasible reasoning.

**Pañcāvayava** (five-membered argument): The proof trace format:
1. *Pratijñā* — the proposition (claim to be established)
2. *Hetu* — the reason (evidence/premises)
3. *Udāharaṇa* — the example (grounding in observed instances)
4. *Upanaya* — the application (connecting example to the case)
5. *Nigamana* — the conclusion (derivation complete)

Every engine output carries this trace, making reasoning inspectable. In the argumentation framework, this becomes the *argument tree* — a structured sub-argument chain from premises through defeasible rules to conclusion.

### 2.4 The Meta-Prompt and Compilation Targets

The Ānvīkṣikī meta-prompt (v3.26) is a 3,963-line natural-language specification that instructs a large language model to generate a pedagogical guide through eight sequential stages. The meta-prompt is a *compiler* — its input is a domain specification, its output is a structured knowledge artifact.

The engine consumes this artifact and compiles it into:
- **T1** (Guide): Human-readable pedagogical document
- **T2** (Logic Engine): Executable inference over formalized domain rules — *this is what this thesis redesigns*
- **T3** (Retrieval Corpus): Graph-structured RAG over guide prose

The grounding module (NL → structured predicates) and synthesis module (inference results → calibrated NL response) remain unchanged from v3. This thesis concerns itself exclusively with T2 — the logic engine — and its surrounding uncertainty, provenance, and consistency machinery.

---

## 3. The Epistemological Debate: Choosing the Right Framework

Before specifying an architecture, we must answer a foundational question: which epistemological framework best serves the engine's objectives? We consider five candidates and conduct a structured debate.

### 3.1 Candidate 1: Bayesian Epistemology

**The proposal:** Represent all epistemic states as probability distributions. Use Bayes' theorem for belief revision. Combine evidence via the product rule. Decompose uncertainty via posterior variance.

**Strengths:**
- One number (probability) instead of discrete categories
- One update rule (Bayes' theorem) instead of ad-hoc propagation
- Mathematically optimal (Cox's theorem, Dutch book arguments)
- Massive tooling ecosystem (probabilistic programming, variational inference, MCMC)
- Handles everything Nyāya handles: source reliability → prior on source accuracy; conflicting evidence → posterior reflects balance; chain degradation → multiplication of conditional probabilities

**Fatal weaknesses for this application:**

**(1) Probability collapses distinctions that matter.** P(X)=0.5 could mean "we have strong evidence for and against" (CONTESTED in Nyāya terms) or "we have no evidence at all" (OPEN in Nyāya terms). These are categorically different epistemic situations requiring different responses. Bayesians handle this with second-order uncertainty (distributions over probabilities), but this reintroduces the categorical distinctions Nyāya provides natively — with extra mathematical machinery.

**(2) Where do the numbers come from?** Bayesian inference requires calibrated probability parameters for every rule. When rules are compiled from expert domain knowledge — not learned from data — there is no principled source for these parameters. Asking an LLM "what's the probability that concentrated ownership enables long-horizon investment?" produces a confident-sounding number with no epistemic grounding. The Nyāya framework avoids this: it classifies the *kind* of evidence, not its numerical strength.

**(3) Complexity.** Exact Bayesian inference over logic programs is #P-hard (BetaProbLog, Verreet et al., AAAI 2022). Monte Carlo approximation introduces statistical noise. The engine requires deterministic, polynomial-time inference. Bayesian approaches cannot guarantee this.

**(4) "CONTESTED" is not a probability distribution.** "Experts actively disagree about this claim" is a *social fact about scholarly debate*, not a statement about frequency or degree of belief. It is closer to a bimodal distribution, or not a probability distribution at all. The Bayesian framework has no natural representation for "the evidence is inherently conflicted" as opposed to "the evidence is weak."

### 3.2 Candidate 2: Dempster-Shafer / Subjective Logic

**The proposal:** Use belief functions (mass assignments over power sets) instead of probabilities. Represent ignorance explicitly via m({true, false}) ≠ 0.

**Strengths:**
- Distinguishes uncertainty (weak evidence) from conflict (contradictory evidence) — unlike Bayesian probability
- Subjective Logic (Jøsang 2016) extends this to (belief, disbelief, uncertainty, base_rate) tuples with well-defined fusion operators
- Cumulative fusion handles independent source combination
- The OPEN vs. CONTESTED distinction falls out naturally: high *u* (uncertainty) = OPEN; low *u* with balanced *b/d* = CONTESTED

**Weaknesses:**

**(1) Dempster's rule of combination is problematic.** When sources strongly disagree, Dempster's rule can produce counter-intuitive results (the Zadeh paradox). Alternative rules (Yager, Dubois-Prade, PCR) exist but there is no consensus on which to use.

**(2) No native notion of *inference*.** Dempster-Shafer provides combination operators for evidence but no inference mechanism. You still need a separate logic engine to chain rules. The belief functions annotate the results; they don't produce them.

**(3) Still requires numerical parameters.** Where does the initial (b, d, u, a) come from for each rule? The same calibration problem as Bayesian approaches.

**Assessment:** Subjective Logic is a strong candidate for the *annotation layer* — tracking evidence strength and source combination. But it is not a reasoning framework. It provides the *tags*, not the *inference*.

### 3.3 Candidate 3: Reliabilism

**The proposal:** A belief is justified if and only if it was produced by a reliable process (Goldman 1979). Track pipeline reliability empirically.

**Strengths:**
- Beautifully direct for computational systems: each pipeline stage has a measured reliability
- Output justification = reliability of the process that produced it
- No lattice, no semiring, no sheaf — just calibrated process reliability scores
- This is essentially what ML model cards and evaluation benchmarks already do

**Weaknesses:**

**(1) Process reliability is a single number, not a structure.** Reliabilism says "this process has 85% reliability." It doesn't say "this conclusion depends on a hypothetical premise, combines testimony from two sources of different authority, and applies a rule outside its validated scope." The engine needs structured epistemic qualification, not just a reliability score.

**(2) No decomposition of uncertainty types.** The engine must distinguish "we don't have enough evidence" (epistemic) from "the domain is inherently noisy" (aleatoric) from "the LLM might have mistranslated" (inference). Reliabilism collapses these into one number.

**(3) No native conflict handling.** When two reliable processes disagree, reliabilism provides no mechanism for resolution beyond "pick the more reliable one." The engine needs to represent and reason about conflict.

**Assessment:** Reliabilism provides the right *framing* for the grounding module (track pipeline reliability) but is too thin for the reasoning engine.

### 3.4 Candidate 4: Argumentation Theory (ASPIC+)

**The proposal:** Model domain reasoning as construction and evaluation of arguments. Arguments are built from premises via rules. Arguments attack each other. Semantics determine which arguments are *acceptable* (in, out, undecided).

**Strengths:**

**(1) Handles defeat as a first-class citizen.** Conflict, contradiction, and override are not bolted on — they are the core mechanism. Hetvābhāsas become the *defeat relation*, not a separate checking module.

**(2) Epistemic status *emerges*.** An argument is IN (accepted), OUT (defeated), or UNDECIDED — corresponding to ESTABLISHED, CONTESTED, and OPEN. This is not hand-assigned; it falls out of the global computation over the attack graph.

**(3) Multiple semantics for different reasoning dispositions.** Grounded semantics (skeptical, polynomial) for cautious reasoning. Preferred semantics (credulous, NP-hard) for exploratory reasoning. The same knowledge base supports both, controlled by a parameter — matching Nyāya's vāda (honest inquiry → grounded) vs. jalpa (adversarial → preferred).

**(4) Natural proof traces.** An argument IS its proof trace — a tree of sub-arguments from premises through rules to conclusion.

**(5) Polynomial grounded semantics.** Grounded semantics is computable in P-time (Dvořák & Dunne 2018), matching the Datalog tractability requirement.

**Weaknesses:**

**(1) No native quantitative reasoning.** Standard ASPIC+ arguments are either accepted or not. There is no "this argument is 0.7 strong." For quantitative evidence strength, trust levels, and temporal decay, we need an annotation layer.

**(2) Preferred semantics is coNP-complete.** Only grounded semantics is polynomial. This limits the reasoning dispositions available at query time.

**(3) Grounding step can be exponential.** First-order ASPIC+ rules generate arguments through instantiation, which can be exponential. Diller et al. (KR 2025) address this using Datalog, but the approach is recent.

**Assessment:** Argumentation provides the right *structure* for the reasoning engine. But it needs a quantitative annotation layer for evidence strength.

### 3.5 Candidate 5: Nyāya Epistemology

**The proposal:** Use Nyāya's four pramāṇas, vyāpti inference, hetvābhāsa constraints, and pañcāvayava proof traces as the engine's conceptual foundation.

**Strengths:**
- Categorizes knowledge sources (pramāṇa types)
- Classifies inference failures (five hetvābhāsa types)
- Provides principled conflict resolution (pramāṇa hierarchy: pratyakṣa > anumāna > śabda)
- Native theory of testimony with trust conditions (āptavacana, abhiyoga)
- Richer defeat taxonomy than Western frameworks (five types vs. two-three)
- The entire śāstric tradition IS argumentation — vāda, jalpa, vitaṇḍā are argument evaluation protocols

**Weaknesses:**

**(1) Nyāya gives you an ontology, not a calculus.** It tells you WHAT the epistemic categories are, but not HOW TO COMPUTE with them. How much does a vyāpti degrade when chained through 4 inference steps? Nyāya doesn't say. How do you combine the testimony of 3 sources who partially agree? Nyāya doesn't say.

**(2) No formal semantics in the Western sense.** Nyāya has no completeness theorems, no model theory, no complexity bounds. The modern formalizations (Guhe 2022, Ganeri 2003, Oetke 1996) import Western formal methods to provide these.

**(3) The categories are extensible but not computable.** Adding a new pramāṇa or hetvābhāsa type is philosophically straightforward but computationally undefined without an implementation framework.

**Assessment:** Nyāya provides the right *vocabulary* — the conceptual architecture for what the system needs to represent and reason about. But it requires a computational substrate.

### 3.6 The Verdict: Nyāya as Ontology, Argumentation as Calculus

The five candidates are not competing alternatives — they operate at different levels:

| Level | What It Provides | Best Candidate |
|-------|-----------------|----------------|
| **Design ontology** — what concepts exist, what distinctions matter | Categories of knowledge, failure types, source trust, conflict types | **Nyāya** |
| **Reasoning structure** — how to chain, defeat, and evaluate inferences | Arguments, attacks, extensions, acceptance semantics | **Argumentation (ASPIC+)** |
| **Quantitative annotation** — how to track evidence strength, trust, decay | Numerical tags that propagate through inference | **Subjective Logic / Provenance Semirings** |
| **Process monitoring** — how to track pipeline reliability | Calibrated reliability scores for grounding, synthesis | **Reliabilism** |

The optimal architecture uses each framework at its appropriate level:

> **Use Nyāya as the design ontology** (the conceptual vocabulary for requirements), but **implement via structured argumentation with semiring-valued strength** (ASPIC+ over provenance tags).

This works because:
- Nyāya concepts map 1-to-1 to argumentation concepts (genuinely natural, not forced)
- The semiring handles all quantitative aspects (evidence accumulation, trust, decay)
- Argumentation semantics handles all qualitative aspects (conflict, defeat, status)
- Datalog can compute grounded argumentation semantics in polynomial time
- The "epistemic status" *emerges* from the argumentation semantics rather than being hand-assigned to a lattice element

Bayesian epistemology is the wrong framework because the problem is fundamentally about *defeasible reasoning with categorical epistemic distinctions*, not about *probability estimation over stochastic processes*. Nyāya is not "less formalized Bayesianism" — it is tracking a different thing entirely. "This is a HYPOTHESIS" ≠ "This has probability 0.3 ± 0.15." The first is the logical status of a derivation. The second is frequentist confidence in truth.

---

## 4. The Prior Architecture and Its Shortcomings

### 4.1 Summary of v3 Architecture

The Ānvīkṣikī Engine v3 (this thesis's predecessor; see `thesis_v3(1).md`) proposed a four-phase architecture:

- **Phase 1:** DSPy-only baseline (pure LLM reasoning)
- **Phase 2:** DSPy + Boolean Datalog (deterministic forward chaining, no epistemic values)
- **Phase 3:** DSPy + Lattice Datalog + UQ (Heyting-valued inference, three-way uncertainty decomposition, provenance tracing)
- **Phase 4:** DSPy + Lattice Datalog + Sheaf + UQ (cellular sheaf consistency checking, cohomological hetvābhāsa detection, source authority model)

The v3 architecture achieved all seven desiderata (infer, constrain, qualify, decompose uncertainty, ground to sources, respect scope, decay gracefully) and represented a genuine advance over existing neurosymbolic systems (Logic-LM, LINC, ChatLogic, VERUS-LM, DSPy+ASP), none of which provide epistemic status propagation, formal fallacy detection, or inspectable proof traces with epistemic qualification.

### 4.2 The Frankenstein Problem

The v3 architecture solves each concern with the best tool from a different intellectual tradition:

| Concern | v3 Solution | Intellectual Tradition |
|---------|-------------|----------------------|
| Epistemic status propagation | 6-element Heyting lattice with meet/join | Intuitionistic logic (Brouwer, Heyting) |
| Consistency checking | Cellular sheaf coboundary operator δ | Algebraic topology (Curry, Ghrist) |
| Source trust | Hand-specified trust tier × venue tier lookup table | Ad hoc |
| Fallacy detection | Keyword-based pattern matching + sheaf H¹ | Hybrid (ad hoc + algebraic topology) |
| Uncertainty decomposition | Three-way split with hand-tuned domain_base dict | Ad hoc |
| Evidence combination | Lattice meet (min) for conjunction, join (max) across paths | Lattice theory |

These six formalisms do not naturally compose. The sheaf operates *on top of* the Datalog engine but doesn't communicate with the trust model. The Heyting lattice propagates epistemic status but doesn't interact with the hetvābhāsa detector (which uses keywords, not lattice values). The trust table assigns initial lattice values but the lattice doesn't feed back into the trust model. The uncertainty decomposition takes the lattice value as one input, the domain type as another, and the grounding confidence as a third — combining them with `min()`, the simplest possible aggregation.

The result: a system that works but does not cohere. Each component was optimized independently. No single mathematical principle explains why the system is correct.

### 4.3 Systematic Audit of Hand-Specified Decisions

A systematic review of the v3 architecture identifies **16 hand-specified decisions** across three severity tiers:

#### Tier 1: Structurally Load-Bearing (architectural consequences)

**H1. Total ordering of epistemic values.** The `EpistemicValue(IntEnum)` imposes: BOTTOM < CONTESTED < OPEN < PROVISIONAL < HYPOTHESIS < ESTABLISHED. But CONTESTED (experts disagree) and OPEN (no evidence) are not naturally comparable. "We have conflicting evidence" is not categorically below "we have no evidence" — they are different kinds of epistemic situations requiring different responses.

*Potential fix:* Product lattice (evidence_level × consensus_level) where CONTESTED = (high_evidence, low_consensus) and OPEN = (low_evidence, high_consensus). These become incomparable, as they should be. Fitting (1991) and Straccia (2022) provide the mathematical foundation.

**H2. Meet-only propagation.** Conjunction within a chain uses `min()` (meet). This means evidence can only *degrade* through inference — it can never accumulate. Three independent paths each providing HYPOTHESIS evidence still yield HYPOTHESIS, not something stronger. The join (max) across derivation paths partially compensates, but this is idempotent — adding more evidence of the same quality achieves nothing.

*Potential fix:* Provenance semiring with non-idempotent ⊕. Green et al. (PODS 2007) showed that the provenance semiring PosBool[X] is the most general annotation for positive Datalog. Scallop (Li et al., PLDI 2023) implements 18 pluggable tag spaces including non-idempotent ones.

**H3. Trust tier × venue tier → epistemic status table.** Twenty-plus hand-specified entries in Section 13.3 of v3. Each entry is a judgment call with no systematic derivation. Why does (Canonical, Book, Empirical) → HYPOTHESIS while (Canonical, Peer-reviewed, Empirical) → ESTABLISHED? The table provides no formal justification.

*Potential fix:* Subjective Logic opinions per source with cumulative fusion (Jøsang 2016) or a parameterized scoring function with 3 tunable weights (Dong et al. 2015).

**H4. Domain-base uncertainty dictionary.** A hand-specified dictionary maps each of 8 domain types to a base uncertainty: Formal → 0.0, Craft → 0.5, Interpretive → 0.6, etc. These numbers are plausible but arbitrary. Why 0.5 and not 0.45?

*Potential fix:* Derive from KB statistics: fraction_empirical_rules, fraction_contested_rules, average_scope_condition_count.

#### Tier 2: Functionally Important Thresholds

**H5. Grounding confidence threshold at 0.4.** Below this, the system requests clarification.

**H6. Round-trip threshold at 0.9.** Below this, Layer 4 verification triggers.

**H7. Ensemble N=5.** Five parallel grounding attempts for consensus measurement.

**H8. Max refinement rounds = 3.** Solver-feedback refinement stops after 3 attempts.

**H9. Decay threshold = 180 days.** Rules verified more than 180 days ago trigger decay warnings.

**H10. Sheaf coboundary threshold = 0.1.** Residual norms below this are considered consistent.

**H11. Global consistency normalization by /10.0.** The `global_consistency_score()` divides the spectral gap by 10.0 to normalize to [0,1]. This constant is arbitrary.

*Potential fix for H5-H11:* All are DSPy-optimizable hyperparameters. Use μ+2σ from KB distribution statistics as starting points, then optimize via MIPROv2 (Khattab et al., ICLR 2024).

#### Tier 3: Implementation Assumptions

**H12. Stalk dimension = 8.** The sheaf stalks are 8-dimensional vectors. Why 8?

**H13. Identity restriction maps.** All sheaf restriction maps are initialized as identity matrices. This means the coboundary δ reduces to a trivial difference check between stalk vectors — the sheaf machinery is present but functionally inert.

**H14. Stalk encoding uses 2-of-8 dimensions.** `section[node][0] = value.value / 5.0` and `section[node][1] = 1.0`. Dimensions 2-7 are zero. The sheaf operates over 8D vectors but only 2D carry information.

**H15. Keyword-based hetvābhāsa detection.** The `_build_hetvabhasa_check()` function uses `if "survivorship" in sig` — string matching on detection signatures.

**H16. Calibration metric uses string matching.** The `calibration_metric()` parses confidence from text: `if "high" in conf_text: stated_conf = 0.9`.

### 4.4 The Sheaf That Does Nothing

The most critical finding from the audit: **the sheaf machinery is architecturally present but functionally inert.**

Here's why: with identity restriction maps (H13), the coboundary operator reduces to:

```
δ(section)(u,v) = I · section(u) - section(v) = section(u) - section(v)
```

This is a simple vector difference. With 2-of-8 encoding (H14), the "sheaf consistency check" is checking whether `(value_u/5.0, 1.0, 0, 0, 0, 0, 0, 0)` equals `(value_v/5.0, 1.0, 0, 0, 0, 0, 0, 0)`. This is equivalent to checking whether two concepts have the same epistemic value — something the Datalog engine already knows from its derived facts.

The sheaf Laplacian, spectral gap, H¹ cohomology — all the sophisticated algebraic topology — degenerates to a trivial difference check because the restriction maps are identity matrices. To make the sheaf do real work, you need non-trivial restriction maps derived from the knowledge base structure (Bodnar et al. 2022, Gebhart et al. 2023). The v3 architecture promises to do this ("The restriction maps encode how concepts relate across vyāpti edges") but the code initializes them as `np.eye(stalk_dim)` and never updates them.

This is the poster child for the Frankenstein problem: a sophisticated mathematical object imported from algebraic topology, correctly described in theory, but producing trivial results in practice because the bridge between theory and implementation was never built.

---

## 5. Related Work

### 5.1 Neurosymbolic LLM Reasoning Systems

All major neurosymbolic LLM reasoning systems follow the same pipeline: NL → symbolic formulation → deterministic solver → NL response. The critical differences are what logic each uses and what it does with the solver output.

| System | Solver | Logic | Epistemic UQ | Fallacy Detection | Proof Traces | Defeat Handling |
|--------|--------|-------|-------------|-------------------|-------------|-----------------|
| Logic-LM (Pan et al., EMNLP 2023) | SAT/FOL/CSP | Boolean | No | No | No | No |
| LINC (Olausson et al., EMNLP 2023) | Prover9 | FOL, Boolean | No | No | No | No |
| ChatLogic (Wang et al., 2024) | pyDatalog | Datalog, Boolean | No | No | No | No |
| VERUS-LM (Callewaert et al., 2025) | IDP-Z3 | Multi-paradigm, Boolean | No | No | No | No |
| DSPy+ASP (Wang et al., 2024) | Clingo | ASP, Boolean | No | No | No | No |
| Ānvīkṣikī v3 | Custom Lattice Datalog | Heyting-valued | Yes (lattice) | Yes (sheaf δ + keywords) | Yes | No (hand-coded) |
| **Ānvīkṣikī v4 (this thesis)** | **ASPIC+ over Semirings** | **Argumentation** | **Yes (emergent)** | **Yes (native defeat)** | **Yes (argument trees)** | **Yes (native)** |

**Key finding:** No existing neurosymbolic LLM framework handles defeat — the fundamental mechanism by which domain reasoning fails or is overridden. The v3 architecture handles it via keyword matching and sheaf checks (two separate ad-hoc mechanisms). The v4 architecture handles it natively through the argumentation semantics.

**Shortcomings shared by all existing systems:**
- Boolean truth (no epistemic qualification)
- No mechanism for representing "experts disagree" vs. "no evidence"
- No proof traces with epistemic qualification
- No formal conflict resolution between contradictory derivations
- No source trust model

### 5.2 Computational Argumentation

**Dung (1995)** introduced abstract argumentation frameworks (AFs): a set of arguments and a binary attack relation. Four key semantics:

| Semantics | Intuition | Complexity (credulous acceptance) | Complexity (skeptical) |
|-----------|-----------|----------------------------------|----------------------|
| Grounded | Maximally skeptical — accept only what must be accepted | P-complete | P-complete |
| Complete | Self-defending — every attacked argument is defended | P | P |
| Preferred | Maximally credulous — accept as much as consistently possible | NP-complete | Π₂ᵖ-complete |
| Stable | Everything not in is attacked by something in | NP-complete | coNP-complete |

**ASPIC+** (Prakken 2010; Modgil & Prakken 2014, 2018) extends abstract AFs with:
- Strict rules (certain knowledge — definitional, analytical truths)
- Defeasible rules (uncertain knowledge — empirical regularities, expert opinions)
- Three defeat types: undermining (attack on premise), undercutting (attack on defeasible inference), rebutting (attack on conclusion)
- Preference orderings (last-link, weakest-link)
- Sub-argument structure (arguments built from other arguments)

**Shortcoming for our purposes:** ASPIC+ provides qualitative reasoning (in/out/undecided) but no quantitative annotation. Evidence strength, source trust, and temporal decay have no native representation.

**Gradual/weighted argumentation** addresses this:
- **h-categorizer** (Besnard & Hunter 2001): Assigns numerical strength to arguments based on attacker/supporter strength
- **DF-QuAD** (Rago et al., KR 2016): Discontinuity-free quantitative argumentation debates
- **Semiring-based argumentation** (Bistarelli & Santini, ECAI 2010): Arguments carry semiring-valued weights; attack strength is computed via semiring operations
- **Weighted argument systems** (Dunne et al. 2011): Arguments have intrinsic weights; acceptability depends on weight comparison

**Shortcoming of gradual semantics:** Most use ad-hoc numerical schemes (real-valued weights) without algebraic structure. The semiring approach (Bistarelli & Santini) provides algebraic structure but has limited implementations.

### 5.3 Provenance-Aware Datalog

**Green, Karvounarakis & Tannen (PODS 2007)** proved the foundational result: the **provenance semiring PosBool[X]** is the most general annotation structure for positive Datalog. Every other annotation scheme — Boolean, fuzzy, probabilistic, access control, trust — is a **homomorphic image** of the free provenance semiring.

This means: if you parameterize Datalog over a commutative semiring (K, ⊕, ⊗, 0, 1), you get:
- ⊗ for conjunction (combining evidence along a chain)
- ⊕ for disjunction (combining evidence across alternative derivations)
- Semiring homomorphisms give you any specific annotation scheme

**Scallop** (Li et al., PLDI 2023): A Datalog-based neurosymbolic programming language with 18 built-in provenance tag spaces (4 discrete + 6 probabilistic + 8 differentiable). Key features:
- Provenance semirings parameterize the evaluation
- Differentiable tags enable end-to-end gradient flow through logic
- GPU-accelerated evaluation
- Demonstrated on visual QA, NLP, planning tasks

**Flix** (Madsen et al., PLDI 2016): Datalog with first-class lattice semantics. Proves that lattice Datalog terminates and computes the least fixpoint — the existence proof that the v3 Heyting lattice approach is mathematically sound.

**Khamis et al. (PODS 2022):** Prove convergence conditions for Datalog over semirings, extending Green et al.'s results to recursive Datalog programs over ordered semirings.

**Shortcoming for our purposes:** Provenance-aware Datalog provides the quantitative annotation structure but has no native notion of *defeat*. Arguments cannot attack other arguments. Contradiction must be handled externally.

### 5.4 LLM + Argumentation

Recent work combining LLMs with formal argumentation:

**ArgLLMs** (Freedman et al., AAAI 2025): Uses LLMs to generate arguments and counter-arguments, then evaluates them using Dung's semantics. Key finding: LLMs can generate plausible arguments but struggle with systematic counter-argument generation.

**Chen et al. (ACL 2024):** Survey of LLMs in computational argumentation — argument mining, argument generation, argument quality assessment.

**Li et al. (2024):** Benchmark for argumentation computation with LLMs — tests whether LLMs can correctly compute grounded/preferred/stable extensions. Finding: LLMs perform poorly on extension computation, confirming the need for symbolic argumentation engines.

**MQArgEng** (Castagna et al. 2024): Multi-quality argumentation engine combining LLM argument generation with formal evaluation.

**ARGORA** (2025): Framework for LLM-based argumentation with retrieval-augmented generation.

**Shortcoming shared by all:** These systems use argumentation to evaluate LLM outputs *post-hoc*. None uses argumentation as the *core inference engine* for a compiled knowledge base. None has provenance semiring tags, source authority integration, or Nyāya-grounded epistemic categories.

**Diller et al. (KR 2025):** Critically, this paper shows how to ground ASPIC+ with Datalog — computing the arguments and attacks from first-order defeasible rules using Datalog evaluation. This provides the missing bridge between Datalog's polynomial evaluation and ASPIC+'s structured argumentation.

### 5.5 Contestable AI

Contestable AI is an emerging paradigm asserting that AI systems should be **open and responsive to human intervention and dispute throughout their entire lifecycle** — not merely explainable after the fact, but structurally amenable to challenge, scrutiny, and revision (Hirsch et al. 2017; Mulligan, Kluttz & Kohli 2019; Almada 2019).

**The explainability-justifiability-contestability hierarchy.** Henin & Le Métayer (2021, 2022) established a conceptual hierarchy: *explainability* (understanding what the system did) is necessary but insufficient for *justifiability* (showing the decision was correct), which is insufficient for *contestability* (enabling affected parties to challenge the decision with formal consequences). Most XAI work stops at explainability. Contestability requires that challenges have *causal effects* on the system's behavior — not just that explanations are provided.

**Contestable AI needs computational argumentation.** The key position paper is Leofante, Toni et al. (KR 2024), "Contestable AI Needs Computational Argumentation." They identify four requirements for contestable systems:
- **(E) Explanations** of outputs and reasoning — via dispute trees, defence sets, attribution scores
- **(G) Grounds** — articulating the formal basis for contestation
- **(I) Interaction** — structured human-machine dialogue using argument schemes
- **(R) Redress** — revising the system in response to successful contestation via argumentation-based KB repair

They argue that computational argumentation "organically covers" all four requirements, unlike post-hoc XAI methods (SHAP, LIME) which provide explanations but no mechanism for grounds, interaction, or redress.

**ArgLLMs** (Freedman, Toni et al., AAAI 2025) is the first system to combine LLMs with formal contestability. LLMs construct Quantitative Bipolar Argumentation Frameworks (QBAFs) in three stages: argument generation, strength attribution, and DF-QuAD gradual semantics evaluation. The paper proves two formal contestability properties:
- *Base Score Contestability:* Increasing pro-argument strength does not decrease final strength
- *Argument Relation Contestability:* Adding pro-arguments increases root strength; adding con-arguments decreases it

Users can modify argument confidence scores, and the change propagates predictably through the semantics — demonstrated experimentally to flip classification labels.

**ArgRAG** (2025) applies the same principle to RAG: replace black-box retrieval-augmented reasoning with QBAF-structured inference, enabling contestation of retrieved evidence and its influence on conclusions.

**Moreira et al. (2025)** provide the most rigorous formal definition and the **Contestability Assessment Scale (CAS)** — a composite metric across 8 properties:
1. Explainability (intrinsic preferred over post-hoc)
2. Openness to contestation (broad access, not expert-only)
3. Traceability (granular audit logging)
4. Built-in safeguards (proportional to risk)
5. Adaptivity (learn from contestation patterns)
6. Auditing (independent external capability)
7. Ease of contestation (accessible challenge routes)
8. Explanation quality (faithfulness and robustness)

**Alfrink et al. (2023)** provide the most comprehensive *design* framework for Contestable AI, proposing that human controllers and decision subjects should be put "in dialogue" with AI systems — not positioned as passive recipients of explanations.

**Shortcomings of existing Contestable AI work for our purposes:**
- ArgLLMs trusts the LLM to construct the AF — reintroducing the reliability problem
- QBAFs are flat (no rules, no sub-arguments, no typed defeat) — weaker than full ASPIC+
- No provenance tracking or source authority model
- No epistemic categories — only numerical strength
- No domain-compiled knowledge base — arguments are generated on-the-fly
- Contestation is limited to score modification — no vocabulary for *different kinds* of contestation
- No connection to epistemological traditions that would ground the contestation process

The present architecture addresses all of these: arguments are compiled from a verified KB, defeat is fully typed (5 Nyāya hetvābhāsa categories), provenance is tracked via semiring tags, epistemic categories emerge from semantics, and three formally distinct contestation protocols are derived from Nyāya debate theory (Section 8.6).

### 5.6 Nyāya in Formal Methods

**Guhe (2022)** — *An Indian Theory of Defeasible Reasoning: The Doctrine of Upādhi in the Upādhidarpaṇa* — draws explicit connections between Navya-Nyāya's upādhi (defeating conditions) and Pollock's undercutting/rebutting defeaters. This is the most directly relevant work for the present thesis.

**Oetke (1996)** — "Ancient Indian Logic as a Theory of Non-Monotonic Reasoning" — argues that Indian inference is fundamentally non-monotonic, analogous to default logic in AI.

**Ganeri (2003)** — argues that ancient Indian logic is best understood as case-based reasoning (reasoning by example), not syllogistic deduction.

**Keating (2021)** — juxtaposes early Nyāya debate theory with van Eemeren's pragma-dialectics, showing overlap in the concern for justified argumentation norms.

**Gap identified:** No published work formally maps Nyāya's five hetvābhāsa types to argumentation-theoretic defeat types, Nyāya's three debate types (vāda/jalpa/vitaṇḍā) to argumentation semantics, or the four pramāṇas to typed epistemic channels in a computational framework. These mappings are contributions of the present work.

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

**Key examples:**

| Semiring | K | ⊕ | ⊗ | 0 | 1 | Models |
|----------|---|---|---|---|---|--------|
| Boolean | {0, 1} | ∨ | ∧ | 0 | 1 | Classical Datalog |
| Counting | ℕ | + | × | 0 | 1 | Number of derivations |
| Tropical | ℝ⁺ ∪ {∞} | min | + | ∞ | 0 | Shortest path / minimum cost |
| Viterbi | [0, 1] | max | × | 0 | 1 | Most probable derivation |
| Access control | {P, C, S, T, ⊥} | ⊓ | ⊔ | ⊥ | P | Security clearance levels |
| PosBool[X] | Polynomials | + | × | 0 | 1 | Universal provenance |

**The universality theorem** (Green et al. 2007): PosBool[X] (positive Boolean polynomials over a set of variables X, one variable per base fact) is the *most informative* semiring for positive Datalog. Every other semiring annotation is obtained by applying a semiring homomorphism h: PosBool[X] → K. This means: if you can evaluate over PosBool[X], you can obtain any specific annotation by post-processing.

**Convergence** (Khamis et al. 2022): For recursive Datalog over an ω-continuous semiring, semi-naive evaluation converges to the least fixpoint. This guarantees termination for the class of semirings we use.

### 6.2 Structured Argumentation (ASPIC+)

**Definition.** An ASPIC+ argumentation theory consists of:

1. **Argumentation system** AS = (L, R, n) where:
   - L is a logical language with a contrariness function (defining what contradicts what)
   - R = Rₛ ∪ Rₐ is a set of strict (Rₛ) and defeasible (Rₐ) inference rules
   - n: Rₐ → L names each defeasible rule (enabling reference to the rule itself)

2. **Knowledge base** KB = (Kₙ, Kₚ) where:
   - Kₙ is necessary (axiom) premises — always accepted
   - Kₚ is ordinary premises — can be attacked

3. **Arguments** are trees built recursively:
   - An axiom premise φ ∈ Kₙ is an argument for φ
   - An ordinary premise φ ∈ Kₚ is an argument for φ
   - If A₁, ..., Aₙ are arguments for φ₁, ..., φₙ and there is a rule φ₁, ..., φₙ → ψ (strict) or φ₁, ..., φₙ ⇒ ψ (defeasible), then the tree with root ψ and children A₁, ..., Aₙ is an argument for ψ

4. **Attacks** — three types:
   - **Undermining**: argument A attacks B by attacking a premise of B
   - **Undercutting**: argument A attacks B by attacking the *applicability* of a defeasible rule used in B (attacking the name n(r))
   - **Rebutting**: argument A attacks B by concluding the contrary of B's conclusion

5. **Defeat**: attack + preference. An attack from A on B succeeds as a defeat if A is not strictly weaker than B according to a preference ordering ≤.

6. **Semantics**: The arguments and defeats define a Dung abstract argumentation framework. Grounded, preferred, complete, and stable semantics determine which arguments are accepted.

**Key property** (Caminada & Amgoud 2007): Under grounded semantics, ASPIC+ satisfies:
- *Closure*: the set of conclusions of accepted arguments is closed under strict rules
- *Direct consistency*: the set of conclusions is consistent
- *Indirect consistency*: the closure is consistent
- *Rationality postulates*: no two accepted arguments attack each other

### 6.3 Gradual Semantics and Annotation-Valued Strength

Standard ASPIC+ produces categorical outputs: IN / OUT / UNDECIDED. For quantitative reasoning, we need gradual semantics that assign *strength values* to arguments.

**The h-categorizer** (Besnard & Hunter 2001) assigns a value v(A) to each argument A:
- If A has no attackers: v(A) = 1 (base strength)
- If A has attackers B₁, ..., Bₖ: v(A) = 1 / (1 + Σᵢ v(Bᵢ))

This converges to a unique fixpoint (Besnard & Hunter proved this).

**Semiring-based argumentation** (Bistarelli & Santini, ECAI 2010) generalizes this:
- Arguments carry semiring-valued weights
- Attack success depends on comparing semiring values
- Acceptability is computed over the semiring rather than over {in, out, undecided}

**Our synthesis:** We combine ASPIC+ structure (arguments from rules, three defeat types, sub-argument structure) with provenance semiring tags (evidence accumulation, source tracking, trust propagation). The semiring provides the quantitative layer that standard ASPIC+ lacks. The argumentation structure provides the defeat handling that provenance Datalog lacks.

### 6.4 Computing Argumentation via Datalog

**Diller et al. (KR 2025)** show how to compute ASPIC+ argumentation using Datalog:

1. **Argument construction**: Represent rules as Datalog facts. Arguments are derived facts — each derived fact corresponds to an argument for the consequent from the antecedents.

2. **Attack computation**: For each pair of arguments where one's conclusion contradicts the other's premise or conclusion, derive an attack relation.

3. **Labeling**: Compute the grounded labeling (IN/OUT/UNDECIDED) using a fixpoint computation that is itself expressible in Datalog.

The key result: **grounded semantics is computable in polynomial time** via Datalog fixpoint evaluation. This means we preserve the tractability guarantee from v3 while gaining the full power of structured argumentation.

**Wu, Caminada & Gabbay (2009)** showed that grounded semantics can be computed by iterative propagation — starting from unattacked arguments (IN), labeling their targets (OUT), and propagating until fixpoint. This is essentially semi-naive evaluation.

**ASPARTIX** (Egly et al., ICLP 2008) implements argumentation semantics in Answer Set Programming (ASP). For grounded semantics, the ASP encoding is equivalent to Datalog (no disjunction or negation-as-failure needed beyond stratified negation).

---

## 7. The Unified Architecture

### 7.1 Design Principle: Nyāya Ontology → Argumentation Calculus

The architectural principle is separation of concerns at the right level:

```
NYĀYA EPISTEMOLOGY (design ontology)
    │
    │   provides: concepts, categories, distinctions
    │   does NOT provide: computation, semantics, complexity bounds
    │
    ▼
ASPIC+ ARGUMENTATION (reasoning structure)
    │
    │   provides: arguments, defeats, extensions, proof traces
    │   does NOT provide: quantitative strength, evidence accumulation
    │
    ▼
PROVENANCE SEMIRING (quantitative annotation)
    │
    │   provides: evidence tags, trust propagation, decay tracking
    │   does NOT provide: conflict resolution, defeat handling
    │
    ▼
DATALOG EVALUATION (computational substrate)
        provides: polynomial fixpoint computation, semi-naive evaluation
```

Each layer does exactly one thing. No layer duplicates another's function. The composition is natural because each layer provides what the next needs.

### 7.2 The Nyāya-to-ASPIC+ Mapping

We classify each mapping by its formal status: **exact** (structural isomorphism — the concepts have the same formal content), **approximate** (reasonable correspondence that compiles down correctly but loses some nuance), or **novel** (Nyāya concept that has no direct ASPIC+ counterpart and requires extension or design decision).

#### Exact Mappings (1:1 structural correspondence)

| Nyāya Concept | ASPIC+ Equivalent | Formal Definition | Why Exact |
|---|---|---|---|
| **Vyāpti** (definitional/structural) | **Strict rule** rₛ ∈ Rₛ | φ₁, ..., φₙ → ψ | Both are non-defeasible inference rules. Vyāpti with causal status "definitional" or "structural" cannot be attacked, matching strict rules exactly. |
| **Vyāpti** (empirical/regulatory) | **Defeasible rule** rₐ ∈ Rₐ | φ₁, ..., φₙ ⇒ ψ | Both are attackable inference rules. Vyāpti scope conditions correspond to the defeasibility — the rule holds unless an exception (undercutter) is established. |
| **Pratyakṣa** (direct evidence) | **Necessary premise** Kₙ | Ground fact from data/observation | Both are unattackable base facts. Pratyakṣa provides the strongest epistemic grounding; necessary premises are axiomatically certain. |
| **Asiddha** (unestablished reason) | **Undermining attack** | Attack on ordinary premise | Exact match. Asiddha says "your premise is not established"; undermining attacks a premise. Same formal effect: removes support for the argument. |
| **Viruddha** (contradictory) | **Rebutting attack** | Counter-argument for contrary conclusion | Exact match. Viruddha says "your reason proves the opposite"; rebutting provides a counter-conclusion. Both target the claim, not the inference rule. |
| **Anumāna** (inference chain) | **Argument tree** | Tree of sub-arguments from premises through rules | Both are recursive derivation structures: premises → rules → intermediate conclusions → more rules → final conclusion. |
| **Pañcāvayava** (proof trace) | **Argument structure** | (Conclusion, TopRule, DirectSubArgs, Premises) | The five-membered syllogism maps to the four-tuple of ASPIC+ argument structure. Pratijñā = conclusion, hetu = premises, nigamana = derivation. See note below on udāharaṇa/upanaya. |

#### Approximate Mappings (reasonable correspondence, some nuance lost)

| Nyāya Concept | ASPIC+ Equivalent | What's Lost | Severity |
|---|---|---|---|
| **Śabda** (testimony) | **Ordinary premise** Kₚ | Nyāya's śabda has *two independent conditions* for validity: āptavacana (speaker competence) and abhiyoga (communicative sincerity). ASPIC+ ordinary premises are simply "attackable" — no internal structure for *why* they might fail. The trust conditions compile to a single trust_score, losing the two-dimensional structure. | Low — the lost structure can be recovered via two separate attack points on testimony premises. |
| **Savyabhicāra** (inconclusive) | **Undercutting attack** | Savyabhicāra specifically means "the reason occurs both with and without the conclusion" — it is about *scope violation* (the hetu is present in cases where the sādhya is absent). ASPIC+ undercutting attacks the rule's *applicability* more broadly. Savyabhicāra is a specific *type* of undercutting (scope-based), not all undercutting. | Low — savyabhicāra is a subset of undercutting. The mapping is sound (every savyabhicāra is an undercutting), but not complete (not every undercutting is a savyabhicāra). |
| **ESTABLISHED / CONTESTED / OPEN / PROVISIONAL** | **IN / OUT / UNDECIDED** | Nyāya has 4-5 epistemic categories; grounded semantics has 3 labels. The within-IN disambiguation (ESTABLISHED vs HYPOTHESIS vs PROVISIONAL) requires examining tag values — it is not purely from the labeling. CONTESTED (OUT in grounded, IN in preferred) requires computing preferred semantics (NP-hard) to verify. | Medium — the 3-label to 5-category mapping requires either tag-based heuristics (current implementation) or expensive preferred semantics computation. |
| **Vāda / Jalpa / Vitaṇḍā** | **Grounded / Preferred / Stable semantics** | The Nyāya debate types are *social protocols* (normative rules for how debaters should behave). The argumentation semantics are *mathematical operators* over static graphs. Vāda includes norms about fairness and good faith that grounded semantics does not model. Jalpa permits rhetorical tricks (chala, jāti) with no analogue in preferred semantics. Vitaṇḍā is purely destructive (no thesis), but stable semantics does require total assignment. | Medium — useful as a design heuristic for mode selection, but not a formal equivalence. The mapping operates at different levels: pragmatics (Nyāya) vs. semantics (ASPIC+). |

#### Novel Mappings (Nyāya concepts with no direct ASPIC+ counterpart)

| Nyāya Concept | What We Map It To | Why It's Novel | Engineering Value |
|---|---|---|---|
| **Bādhita** (sublated by higher pramāṇa) | Preference-based defeat via pramāṇa ordering | ASPIC+ has a generic preference relation ≤ but does not prescribe *what* it should be based on. Bādhita provides a specific, substantive preference theory: evidence type determines the ordering. This is not an ASPIC+ attack type — it is a *constraint on the preference relation* that ASPIC+ leaves parametric. | **High** — provides a principled, non-arbitrary preference ordering instead of "choose your own." |
| **Satpratipakṣa** (counterbalanced) | Symmetric mutual rebutting with no preference winner → UNDECIDED | ASPIC+ handles this case implicitly — symmetric attacks without preference lead to UNDECIDED under grounded semantics. Nyāya elevates this to a *named pathology* worth detecting and reporting. No ASPIC+ system flags this as a specific condition. | **High for explanation** — enables the engine to report "this is genuinely contested — equally strong arguments exist on both sides" rather than silently returning UNDECIDED. |
| **Pramāṇa hierarchy** as total ordering | `PramanaType(IntEnum)`: pratyakṣa > anumāna > śabda > upamāna | ASPIC+ allows any preference ordering. Nyāya mandates a *specific* one based on epistemological theory. This is a design decision, not a formal extension — but it is a decision grounded in 2000 years of epistemological argument rather than arbitrary choice. | **High for design** — eliminates the "which preference ordering?" question that every ASPIC+ implementation must answer ad hoc. |
| **Udāharaṇa** (example in pañcāvayava) | No ASPIC+ equivalent | The third step of the five-membered syllogism requires grounding the inference in an observed instance: "like in the kitchen" (where smoke and fire co-occur). ASPIC+ arguments do not require exemplification. This is a built-in *empirical grounding requirement* that purely formal systems lack. | **Medium** — could be implemented as a constraint requiring at least one grounded instance for each defeasible rule, but this is not currently enforced. |
| **Pre-inferential validation** (pramāṇa applicability checking) | Not in ASPIC+ | Nyāya insists that before applying inference (anumāna), you verify that inference is the appropriate pramāṇa for this type of knowledge. ASPIC+ assumes all arguments in the graph are legitimate candidates. This is conceptually a type-checking pass before computation. | **Medium** — currently implemented as pramāṇa-type metadata on rules, not as a pre-computation validation gate. Future work. |

#### Summary Assessment

Of the 19 concepts in the original mapping table:
- **7 are exact** (1:1 structural correspondence — the formal content is identical)
- **5 are approximate** (sound but incomplete mappings — Nyāya concept compiles to ASPIC+ correctly, but some structure is lost or some nuance conflated)
- **5 are novel** (Nyāya provides something ASPIC+ does not — substantive preference theory, named pathologies, empirical grounding requirements, pre-inferential validation)
- **2 are design heuristics** (vāda/jalpa/vitaṇḍā → semantics selection — useful for mode choice, not formal equivalence)

The mapping is **not an isomorphism** — it is a structure-preserving embedding with genuine additions. Everything in Nyāya can be *expressed* in ASPIC+ (with appropriate parameter choices), but the Nyāya framework provides specific parameter values, named special cases, and design constraints that ASPIC+ leaves open. The engineering value is real: it constrains the design space from "arbitrary ASPIC+ with arbitrary preferences" to "ASPIC+ with pramāṇa-ordered preferences, typed defeat, and pre-inferential validation."

### 7.3 The Provenance Tag

We define a provenance tag as a tuple that tracks everything the engine needs for quantitative reasoning:

```
ProvenanceTag = (
    belief:          float ∈ [0,1],    — evidence strength FOR
    disbelief:       float ∈ [0,1],    — evidence strength AGAINST
    uncertainty:     float ∈ [0,1],    — genuine ignorance (b + d + u = 1)
    source_ids:      FrozenSet[str],   — provenance tracking
    pramana_type:    PramanaType,      — pratyaksa | anumana | sabda | upamana
    trust_score:     float ∈ [0,1],    — source authority
    decay_factor:    float ∈ [0,1],    — temporal freshness
    derivation_depth: int               — chain length
)
```

This is a Subjective Logic opinion (Jøsang 2016) extended with provenance metadata. The two composition operations:

**⊗ (sequential composition — chaining):** When argument A supports premise of argument B:
- `belief_AB = belief_A × belief_B` (evidence attenuates through chains — Jøsang 2016, §12.3 trust discounting)
- `uncertainty_AB = uncertainty_A + uncertainty_B - uncertainty_A × uncertainty_B` (uncertainty grows)
- `trust_AB = min(trust_A, trust_B)` (weakest link)
- `decay_AB = min(decay_A, decay_B)` (weakest link)
- `source_ids_AB = source_ids_A ∪ source_ids_B` (union of provenances)
- `depth_AB = depth_A + depth_B`
- `pramana_AB = lower_pramana(A, B)` (chain quality limited by weakest link)

**⊕ (parallel composition — accrual):** When arguments A and B independently support the same conclusion:
- Cumulative fusion (Jøsang 2016, §12.6): `belief_A⊕B = (belief_A × uncertainty_B + belief_B × uncertainty_A) / κ` where κ normalizes
- `source_ids_A⊕B = source_ids_A ∪ source_ids_B`
- `depth_A⊕B = min(depth_A, depth_B)` (shortest derivation)
- `pramana_A⊕B = higher_pramana(A, B)` (best source type)
- `trust_A⊕B = 1 - (1-trust_A)(1-trust_B)` (noisy-OR: multiple independent sources increase trust)

**Algebraic status — honest assessment:** The (b,d,u) components under ⊗ (trust discounting) and ⊕ (cumulative fusion) satisfy associativity, commutativity of ⊕, left-unitality of ⊗, and annihilation. However, **⊗ does not distribute over ⊕** — Jøsang's trust discounting applied to a cumulative fusion does not equal the fusion of individual discountings. This is a known property of Subjective Logic (Jøsang 2016, §12.7 discusses operation ordering). The structure is therefore a **principled composite** of two well-defined SL operations, not a semiring in the strict algebraic sense.

The metadata fields (trust_score, decay_factor, pramana_type, derivation_depth) propagate via a **product lattice** — min/max operations that are formally separate from the SL operations on (b,d,u). This is consistent with how practical argumentation systems compose quantitative and qualitative annotations (cf. Modgil & Prakken 2018).

We retain the term "provenance tag" but do not claim semiring closure. The tag is a pragmatic annotation structure where (b,d,u) follows Jøsang's SL algebra and metadata follows monotone lattice propagation.

### 7.4 What Becomes Unnecessary

| v3 Component | Status in v4 | Why |
|--------------|-------------|-----|
| **Heyting lattice** (6-element IntEnum) | **Eliminated** | Epistemic status emerges from extension membership: IN → ESTABLISHED/HYPOTHESIS, OUT → CONTESTED, UNDECIDED → OPEN. No hand-assigned lattice values. |
| **Cellular sheaf** (coboundary δ, Laplacian, H¹) | **Eliminated** | Argumentation extensions are globally consistent by construction (Caminada & Amgoud 2007, rationality postulates). No separate consistency layer needed. |
| **Trust lookup table** (20+ entries) | **Eliminated** | Source trust is encoded in the provenance tag's trust_score field. Argument preferences are derived from pramāṇa type and trust_score — 3 parameters vs. 20+ table entries. |
| **Keyword hetvābhāsa detection** | **Eliminated** | Hetvābhāsas ARE the defeat relation. Savyabhicāra = undercutting attack exists. Viruddha = rebutting attack exists. Asiddha = premise not established. Satpratipakṣa = symmetric attack. Bādhita = preference override. No separate detection module. |
| **Hand-specified domain_base uncertainty** | **Eliminated** | Aleatoric uncertainty is modeled by the uncertainty component of provenance tags on base facts — derived from domain type at compile time, not hand-tuned per query. |
| **meet-only propagation** | **Eliminated** | Evidence accumulates through the non-idempotent ⊕ (cumulative fusion). Three independent HYPOTHESIS arguments for the same conclusion yield a stronger-than-HYPOTHESIS tag. |
| **Identity restriction maps** | **N/A** | No sheaf, no restriction maps. |
| **2-of-8 stalk encoding** | **N/A** | No stalks. |
| **Spectral gap normalization /10.0** | **N/A** | No Laplacian. |

**Net effect:** 6 independent formalisms → 2 that compose (argumentation structure + SL annotation), plus a product lattice for metadata propagation. The architectural reduction is genuine: the sheaf, Heyting lattice, trust table, and keyword detection module are all eliminated. The remaining hand-specified decisions fall into two categories: (1) **structural** — the pramāṇa preference ordering, the mapping from KB epistemic status to initial (b,d,u) values, the contrariness relation — these derive from Nyāya theory; (2) **numerical** — belief thresholds for within-IN disambiguation, decay half-life, timeout values, confidence caps — these are DSPy-optimizable hyperparameters whose structure (what to parameterize) comes from theory even though their magnitudes remain empirical.

### 7.5 Why This Architecture — Formal Justification

We justify this architecture through three complementary arguments: elimination (minimality), subsumption (expressiveness), and impossibility-awareness (respecting proven tradeoffs).

#### 7.5.1 Minimality: No Simpler Architecture Achieves All 7 Desiderata

**(1) Pure LLM (no symbolic component):** Fails objectives 1 (no formal inference), 2 (no constraint enforcement), 3 (no epistemic propagation), 4 (no structured uncertainty), 5 (no provenance), 7 (no decay awareness). This is Phase 1 — the baseline that motivates the engine.

**(2) LLM + Boolean Datalog (Logic-LM style):** Achieves 1 (inference) and partially 5 (simple provenance), but fails 2 (no defeat handling), 3 (Boolean only), 4 (no uncertainty decomposition), 6 (no scope-as-defeat), 7 (no decay in inference).

**(3) LLM + Lattice Datalog (v3 without sheaf):** Achieves 1, 3, 5, but needs bolt-on mechanisms for 2 (hetvābhāsa detection), 4 (uncertainty decomposition), 6 (scope handling), 7 (decay). This is the path to the Frankenstein problem (Section 4.2).

**(4) LLM + ASPIC+ (no annotation):** Achieves 1, 2, 3 (qualitative only), 6, but fails 4 (no quantitative uncertainty), 5 (no source tracking), 7 (no decay modeling). Argumentation alone is qualitative.

**(5) LLM + Provenance Datalog (no argumentation):** Achieves 1, 4, 5, 7, but fails 2 (no defeat), 3 (no epistemic categories — just numbers), 6 (no scope-as-defeat).

**(6) LLM + ASPIC+ with SL annotation (this thesis):** Achieves all 7. Argumentation provides 1 (inference via argument construction), 2 (defeat as native mechanism), 3 (extension membership as epistemic status), 6 (scope violations as attacks). SL annotation provides 4 (uncertainty in tags), 5 (source_ids in tags), 7 (decay_factor in tags).

**No subset of components suffices.** Remove the annotation layer and you lose quantitative reasoning. Remove the argumentation and you lose defeat handling. Both are necessary. Neither alone is sufficient.

#### 7.5.2 Subsumption: The Architecture Expresses All Alternatives as Special Cases

| Alternative System | Expressible in Our Architecture? | Can It Express Ours? |
|---|---|---|
| ArgLLMs (QBAF + DF-QuAD) | Yes — QBAF is ASPIC+ with no rules, binary relations | No — no provenance, no typed defeat, no sub-arguments |
| DeLP (Garcia & Simari 2004) | Yes — DeLP arguments are a subset of ASPIC+ | No — no quantitative tags |
| Carneades proof standards (Gordon) | Yes — proof standards map to tag threshold conditions | Partially — no SL composition |
| Plain ASPIC+ (Modgil & Prakken 2014) | Yes — set annotation to Boolean | No — no quantitative reasoning |
| Provenance Datalog (Green et al. 2007) | Yes — Datalog is the evaluation substrate | No — no defeat, no argumentation |
| Hunter epistemic graphs (2020) | Yes — probability intervals subsumable by SL opinions | No — no argument structure |

Each alternative is recoverable from our architecture by restricting one or more components. This is a form of **representation theorem**: the architecture is general enough to express all known alternatives as projections.

#### 7.5.3 Three-Level Property Framework

We organize the system's properties into three levels — formal guarantees (provable), architectural principles (design criteria), and impossibility constraints (proven tradeoffs that bound what any system can achieve):

**Level 1: Formal Guarantees (non-negotiable, provable)**

| ID | Property | Formal Basis |
|---|---|---|
| F1 | Decidability — every query terminates | Datalog data complexity ∈ PTIME (Vardi 1982) |
| F2 | Polynomial data complexity for grounded semantics | O(\|args\| × \|attacks\|) (Dvořák & Dunne 2018) |
| F3 | Soundness — accepted arguments are conflict-free | Dung 1995, Definition 6 |
| F4 | Rationality postulates — closure, direct/indirect consistency | Caminada & Amgoud 2007, Theorems 3-5 |
| F5 | Convergence — grounded labeling reaches unique fixpoint | Wu, Caminada & Gabbay 2009 |

**Level 2: Architectural Principles (design criteria, grounded in Nyāya epistemology and argumentation theory)**

| ID | Principle | What It Demands |
|---|---|---|
| P1 | Argumentation as single structural principle | Defeat, acceptance, and epistemic status from one mechanism |
| P2 | Structure from theory, magnitudes from data | Nyāya → what to parameterize; DSPy → how much |
| P3 | Composition derives from the framework | Tag propagation follows SL algebra, not hand-specified formulas |
| P4 | Graded acceptance native | Continuous tag values, not binary thresholded |
| P5 | No dead paths | Every component consumed by the inference pipeline |
| P6 | Structural provenance | Trace every conclusion to sources via argument tree |
| P7 | Debate modes as parameter variation | Vāda/jalpa/vitaṇḍā = grounded/preferred/stable |
| P8 | Falsifiable claims only | Claim only what the implementation delivers |

**Level 3: Impossibility Constraints (proven tradeoffs this architecture respects)**

| ID | Constraint | How We Respond |
|---|---|---|
| I1 | No semantics satisfies all desirable principles simultaneously (Baroni & Giacomin 2007) | Choose grounded (satisfies admissibility, reinstatement, conflict-freeness; sacrifice I-maximality) |
| I2 | Cardinality Precedence and Quality Precedence are incompatible (Bonzon et al. 2016) | Choose QP — matches pramāṇa hierarchy (evidence quality > count) |
| I3 | Six gradual semantics are pairwise incompatible (Amgoud & Beuselinck 2021) | Pick one (SL-based); don't mix |
| I4 | Why-provenance for recursive Datalog is NP-complete (Bourgaux et al. 2024) | Lazy/on-demand provenance computation, not eager |
| I5 | Preferred/stable semantics are coNP/NP-complete (Dvořák & Dunne 2018) | Default to grounded (polynomial); preferred/stable for offline analysis only |
| I6 | No differentiable relaxation of logic is simultaneously differentiable, sound, and tautology-preserving (Giannini et al. 2023) | Keep Datalog symbolic; differentiate only through neural grounding layer |
| I7 | Conformal prediction gives marginal, not conditional, coverage (Vovk et al. 2005) | Use coverage groups for approximate conditional guarantees |

#### 7.5.4 Architectural Honesty

The architecture is a **principled composite**: ASPIC+ provides the argumentation skeleton, Subjective Logic provides the uncertainty calculus, a product lattice propagates provenance metadata. These components compose pragmatically, not algebraically — the SL operations on (b,d,u) and the lattice operations on metadata are formally separate structures.

This is consistent with how practical argumentation systems are built in the literature (cf. Modgil & Prakken 2018, Toni 2014). Every working argumentation system bolts on preference mechanisms, trust models, and temporal handling. None are "pure." The contribution is not algebraic unification but **architectural minimality**: two composing formalisms instead of six independent ones, with the structural decisions grounded in Nyāya epistemology and the numerical magnitudes amenable to optimization.

#### 7.5.5 Nyāya as Design Ontology — Not Formal Novelty

The Nyāya-to-ASPIC+ mapping (Section 7.2) is a structural correspondence, not a formal isomorphism. The formal content of the engine is standard ASPIC+ with SL-annotated tags computed over Datalog. What Nyāya provides is:

1. **A substantive preference theory** (pramāṇa hierarchy) where ASPIC+ leaves preferences parametric
2. **Named defeat pathologies** (5 hetvābhāsa types) that improve explanation generation beyond ASPIC+'s 3 generic attack types
3. **Pre-inferential validation** — the principle that evidence channel applicability should be checked before inference, not after
4. **Design vocabulary** that constrains architectural decisions and provides principled defaults

These are engineering advantages grounded in 2000 years of epistemological refinement, not claims of new mathematical expressiveness. Every Nyāya concept compiles to an ASPIC+ construct. The value is in the *design guidance*, not in the *formal power*.

---

## 8. Comparison: Full Architecture vs. LLM+ASPIC+ and Contestable AI

This section conducts three comparisons: (1) against the LLM+ASPIC+ baseline (ArgLLMs/ArgRAG), (2) against the formal requirements of Contestable AI, and (3) a unified comparative summary.

### 8.1 The LLM+ASPIC+ Baseline (ArgLLMs)

The simplest possible argumentation-based system:
1. LLM generates arguments from a natural language query
2. LLM assigns base scores (0-1 confidence) to each argument
3. LLM identifies support and attack relations between arguments
4. DF-QuAD gradual semantics compute final acceptability
5. LLM verbalizes accepted arguments

This is what ArgLLMs (Freedman, Toni et al., AAAI 2025) implements using QBAFs. ArgRAG (2025) extends this to retrieval-augmented settings.

### 8.2 Detailed Comparison with ArgLLMs / ArgRAG

| Dimension | ArgLLMs / ArgRAG | Ānvīkṣikī v4 |
|-----------|-----------------|---------------|
| **Where arguments come from** | LLM generates them at query time — may hallucinate, miss relevant rules, invent attacks | Pre-compiled from verified KB — every argument traceable to a vyāpti with source attribution |
| **Argumentation formalism** | QBAFs (flat — no rules, no sub-arguments, 2 relations: support/attack) | Full ASPIC+ (strict/defeasible rules, sub-argument structure, 3 defeat types mapped to 5 Nyāya hetvābhāsas) |
| **Quantitative layer** | LLM-assigned base scores (single float, 0-1) | Provenance semiring tags (belief, disbelief, uncertainty, trust, decay, source_ids, pramāṇa type, derivation depth) |
| **Provenance** | None — LLM-generated arguments have no source attribution | Every tag carries source_ids tracing to Reference Bank, with pramāṇa classification |
| **Source authority** | None | Pramāṇa-typed channels with trust scores — formalized śabda (Nyāya testimony theory) |
| **Determinism** | Non-deterministic — different LLM runs produce different AFs | Deterministic — same KB + query always produces same AF and extension |
| **LLM role** | Generates arguments, assigns scores, AND constructs attack relations | Only grounding (NL→predicates) and synthesis (results→NL) — everything else is symbolic |
| **Defeat taxonomy** | Binary (support/attack) | Five-type (asiddha, savyabhicāra, viruddha, satpratipakṣa, bādhita) — richer than Pollock's two-type or ASPIC+'s three-type |
| **Epistemic categories** | None — just numerical strength | ESTABLISHED / HYPOTHESIS / PROVISIONAL / OPEN / CONTESTED — emergent from extension membership + tag values |
| **Semantics** | DF-QuAD gradual semantics only | Grounded extension (skeptical, polynomial) + provenance semiring gradual strength |
| **Contestability** | Score modification (proven monotone via DF-QuAD properties) | Four contestation mechanisms: add counter-arguments, undercut rules, challenge premises, invoke higher pramāṇa. Three contestation protocols (vāda/jalpa/vitaṇḍā) |
| **Cost per query** | Multiple LLM calls (argument generation + attack identification + verbalization) | 1-2 LLM calls (grounding + synthesis) — all reasoning is symbolic |

**The fundamental issue:** ArgLLMs trusts the LLM to *construct* the argumentation framework. Li et al. (2024) benchmarked LLMs on argumentation computation — they perform poorly on extension computation, confirming that LLMs cannot reliably build or evaluate argumentation frameworks. The Ānvīkṣikī Engine exists precisely because LLMs cannot be trusted to reason correctly. Having the LLM generate arguments and attacks reintroduces the problem the engine was designed to solve.

The full architecture confines the LLM to what it's actually good at: natural language understanding (grounding: NL → predicates) and natural language generation (synthesis: results → calibrated response). Everything between — argument construction, attack computation, extension evaluation, provenance tracking — is deterministic and symbolic.

### 8.3 The Contestable AI Requirements

Moreira et al. (2025) define 8 properties for contestable AI systems. We evaluate three architectures against each:

| Property | Standard LLM/RAG | ArgLLMs (LLM+ASPIC+) | Ānvīkṣikī v4 |
|----------|-----------------|---------|---------------|
| **1. Explainability** | Post-hoc (SHAP/LIME) — unfaithful approximations of black-box reasoning | Argument trees from LLM — faithful to LLM's reasoning but LLM reasoning itself is opaque | Argument trees from compiled KB — faithful to the actual inference, fully inspectable, machine-checkable |
| **2. Openness to contestation** | No mechanism — black box | Modify argument base scores to flip outcomes — demonstrated experimentally by Freedman et al. | Native: add counter-arguments (viruddha), undercut rules (savyabhicāra), challenge premises (asiddha), invoke higher evidence (bādhita), present equal counter-evidence (satpratipakṣa) |
| **3. Traceability** | Token-level attention — not semantically meaningful | Argument tree structure — traceable but without source attribution | Provenance semiring tags — every conclusion traces through argument tree to specific sources, with pramāṇa type and trust score at each step |
| **4. Built-in safeguards** | None | DF-QuAD formal properties guarantee monotone response to score modification | Grounded semantics rationality postulates (Caminada & Amgoud 2007): closure, direct consistency, indirect consistency. Hetvābhāsa detection as native defeat — 5 formally classified safeguard types |
| **5. Adaptivity** | Requires retraining | Can modify base scores at runtime | Can add new facts, rules, or attacks at runtime — the AF recomputes incrementally via Datalog delta |
| **6. Auditing** | Requires separate explanation tool | QBAF is auditable | Full AF + provenance tags + extension labels + defeat relations = complete audit trail |
| **7. Ease of contestation** | Requires technical expertise | Modify numerical scores — requires understanding gradual semantics | Five natural contestation types mapped from Nyāya hetvābhāsas (Section 2.3), three debate protocols (Section 8.6) |
| **8. Explanation quality** | Often unfaithful to model reasoning (Rudin 2019) | Faithful to QBAF structure, but QBAF itself is LLM-generated — the explanation is faithful to the LLM's (possibly wrong) reasoning | Faithful to compiled KB structure — the explanation IS the reasoning, not an approximation. Faithfulness guaranteed because the symbolic engine IS the reasoner |

### 8.4 Satisfying the Leofante et al. (KR 2024) Requirements

Leofante, Toni et al. (KR 2024) identify four specific requirements for computational argumentation to support contestability:

**(E) Explanations of outputs and reasoning:**
- ArgLLMs: QBAF structure provides explanations, but the arguments themselves are LLM-generated text — ungrounded.
- Ānvīkṣikī v4: Argument trees with provenance tags and pramāṇa classification. Each argument node carries: the vyāpti ID it was derived from, the source_ids supporting it, the trust_score of those sources, the decay_factor indicating freshness, and the pramāṇa type classifying the kind of epistemic access.

**(G) Grounds — articulating the basis for contestation:**
- ArgLLMs: Grounds are implicit — a user can modify scores but has no formal vocabulary for *why*.
- Ānvīkṣikī v4: Five formal ground types from Nyāya hetvābhāsas:
  1. "The premise is not established" (asiddha → undermining)
  2. "The rule has exceptions in this scope" (savyabhicāra → undercutting)
  3. "I have evidence for the opposite conclusion" (viruddha → rebutting)
  4. "There is equally strong evidence for an opposing view" (satpratipakṣa → symmetric attack)
  5. "A more direct form of evidence overrides this inference" (bādhita → preference defeat)

These are not ad-hoc categories — they are the result of two millennia of epistemological refinement in the Nyāya tradition. Three map exactly to ASPIC+ defeat types (asiddha/savyabhicāra/viruddha → undermining/undercutting/rebutting); two are novel named concepts (bādhita = preference defeat, satpratipakṣa = named deadlock) that ASPIC+ handles implicitly but does not elevate to first-class contestation grounds (Section 7.2).

**(I) Interaction — structured human-machine dialogue:**
- ArgLLMs: Score modification interface — single interaction mode.
- Ānvīkṣikī v4: Three debate protocols derived from Nyāya (Section 8.6), each with different argumentation semantics and appropriate for different stakeholders and purposes.

**(R) Redress — revising the system in response to successful contestation:**
- ArgLLMs: Recompute DF-QuAD after score modification — the QBAF itself doesn't change structure.
- Ānvīkṣikī v4: Recompute grounded extension after adding/removing arguments or attacks — polynomial, deterministic, and structurally meaningful. A successful contestation (e.g., establishing that a rule has scope exceptions) results in a new undercutting argument being added to the AF, which persists across queries and affects all future inferences through that rule.

### 8.5 The Henin & Le Métayer Hierarchy: Explainability < Justifiability < Contestability

Henin & Le Métayer (2021, 2022) established that contestability is strictly stronger than justifiability, which is strictly stronger than explainability:

- **Explainability** = "understand what the system did"
- **Justifiability** = "the system can demonstrate its decision was correct given its inputs and rules"
- **Contestability** = "affected parties can challenge the decision, and the challenge has formal consequences on the system's behavior"

| Level | Standard LLM/RAG | v3 (Frankenstein) | ArgLLMs | v4 (this thesis) |
|-------|-----------------|-------------------|---------|-------------------|
| **Explainability** | Partial (attention, CoT) | Yes (Datalog trace) | Yes (QBAF trees) | Yes (argument trees + provenance tags) |
| **Justifiability** | No (no formal reasoning) | Partial (lattice propagation justifies epistemic status, but sheaf/trust/keyword detection are black boxes to the user) | Partial (DF-QuAD justifies strength, but argument content is unjustified LLM text) | Yes (grounded extension + provenance chain — the accepted arguments ARE the justification, traceable to sources) |
| **Contestability** | No | Partial (would require changing Heyting values, re-running sheaf, updating trust table — 3 separate mechanisms with no unified semantics) | Yes (modify scores — formally monotone via DF-QuAD properties) | Yes (add arguments/attacks — formally guaranteed via grounded semantics rationality postulates + 5 typed contestation grounds + 3 debate protocols) |

In v3, contestation would mean: change a Heyting lattice value, re-run the sheaf check, update the trust table — three separate mechanisms with no unified semantics and no formal guarantee that the contestation has the intended effect. In v4, contestation IS adding arguments or attacks to the AF and recomputing. One mechanism. One semantics. Formally guaranteed consequences.

### 8.6 Nyāya Debate Types as Contestation Protocols

This is where Nyāya adds something that neither standard ASPIC+ nor existing Contestable AI frameworks provide. The three classical Nyāya debate types (Nyāya Sūtra 1.2.1-3; Keating 2021) map to three formally distinct *modes of contestation*, each with its own argumentation semantics and appropriate use case:

| Nyāya Debate Type | Contestation Mode | Argumentation Semantics | Use Case | Stakeholder |
|-------------------|-------------------|------------------------|----------|-------------|
| **Vāda** (honest inquiry) | Cooperative contestation — user and engine jointly refine the argument, both contributing evidence and counter-evidence toward truth | Grounded semantics (maximally skeptical — accept only what must be accepted) | Domain expert reviewing engine outputs, collaborative knowledge refinement | Expert, educator, researcher |
| **Jalpa** (adversarial disputation) | Adversarial contestation — engine generates the strongest possible counter-arguments to stress-test a conclusion, using all available attacks | Preferred semantics (maximally credulous — accept what can be defended, exposing all defensible positions) | Risk analysis, devil's advocate testing, robustness evaluation | Risk analyst, auditor, regulator |
| **Vitaṇḍā** (pure critique) | Pure attack mode — engine only attacks, never defends, seeking to expose every vulnerability in a position | Stable semantics (everything not accepted must be attacked — no gaps in the critique) | Regulatory review, adversarial audit, pre-publication review of claims | External auditor, opposing counsel, peer reviewer |

**Why this matters for Contestable AI:** Existing systems (ArgLLMs, ArgRAG) have one contestation mode: modify scores. The user can increase or decrease confidence in individual arguments. But this conflates fundamentally different activities:

- A domain expert saying "I have new evidence that contradicts this rule" (viruddha attack — vāda mode) is a different kind of contestation from
- A risk analyst saying "show me every way this conclusion could fail" (comprehensive attack enumeration — jalpa mode), which is different from
- A regulator saying "prove that no reasonable challenge to this claim succeeds" (exhaustive critique — vitaṇḍā mode)

These require different computational processes (different argumentation semantics), produce different outputs (single extension vs. all extensions vs. attack enumeration), and serve different institutional functions. The Nyāya tradition provides the conceptual vocabulary; ASPIC+ provides the computational semantics; the provenance semiring provides the quantitative tracking. All three layers contribute.

**Computational note:** Vāda (grounded semantics) is polynomial — this is the default query mode. Jalpa (preferred semantics) is coNP-complete for skeptical reasoning — appropriate for offline analysis. Vitaṇḍā (stable semantics) is coNP-complete — appropriate for formal audit. The cost hierarchy matches the use case hierarchy: routine queries are cheap, deep analysis is expensive, and exhaustive audit is most expensive. This is architecturally correct: you should not pay audit-level computational costs for routine queries.

### 8.7 Comparative Summary

| Architecture | What It Is | Inference | Defeat | Epistemic Status | Contestability | Provenance |
|-------------|-----------|-----------|--------|-----------------|----------------|------------|
| **Standard LLM+RAG** | Black box generation from retrieved chunks | No formal inference | None | None | None | None |
| **Logic-LM / LINC / ChatLogic** | LLM → Boolean solver → LLM | Formal (Boolean) | None | Boolean only | None | None |
| **Ānvīkṣikī v3** | Lattice Datalog + Sheaf + Trust table | Formal (Heyting-valued) | Ad hoc (keywords + sheaf) | Hand-assigned lattice | Partial (3 unrelated mechanisms) | Deterministic trace |
| **ArgLLMs / ArgRAG** | LLM → QBAF → DF-QuAD → LLM | Gradual semantics | Bipolar (support/attack) | Numerical only | Score modification (monotone) | None |
| **Contestable AI by Design** | Design framework (Moreira et al.) | N/A (requirements only) | N/A | N/A | 8-property framework | Required but unspecified |
| **Ānvīkṣikī v4 (this thesis)** | ASPIC+ over provenance semirings | Formal (argumentation + semiring) | Native (5-type, from Nyāya) | Emergent (5 categories from semantics) | Native (5 grounds + 3 protocols) | Semiring tags with sources |

**The v4 architecture is, to our knowledge, the first system that is simultaneously:**
1. A neurosymbolic reasoning engine (inference, not just retrieval)
2. A natively contestable system (argumentation, not post-hoc explanation)
3. A provenance-tracked system (semiring tags, not just citations)
4. An epistemically qualified system (5 categories emerging from semantics, not hand-assigned)
5. A system with formally distinct contestation modes (3 Nyāya debate protocols, not one-size-fits-all)

### 8.8 When the Baseline Suffices

The LLM+ASPIC+ baseline (ArgLLMs) is adequate when:
- The knowledge base is small enough for the LLM to hold in context
- Formal provenance is not required
- Quantitative uncertainty decomposition is not needed
- Reproducibility across runs is not important
- The application tolerates LLM-level reasoning errors (~10-30% depending on domain)
- Only score-based contestation is needed (no typed defeat, no debate protocols)
- Regulatory or audit requirements for contestability are not in scope

For the Ānvīkṣikī Engine's target applications — epistemically qualified domain reasoning with formal guarantees and native contestability — the baseline is insufficient.

---

## 9. Implementation Sketch

### 9.1 Phase 1: DSPy Only (Baseline)

Identical to v3 Phase 1. Pure LLM reasoning with DSPy orchestration. Establishes the baseline.

### 9.2 Phase 2: DSPy + Abstract Argumentation

Replace LLM reasoning with formal argumentation over the compiled KB:
- Vyāptis compiled as defeasible rules
- Hetvābhāsas compiled as attack generators
- Grounded extension computed via Datalog fixpoint
- Arguments carry Boolean tags (present/absent) — no quantitative reasoning yet

This is the argumentation analogue of v3 Phase 2 (Boolean Datalog).

### 9.3 Phase 3: DSPy + ASPIC+ over Provenance Semirings

Add provenance semiring tags to arguments:
- Each base fact carries a ProvenanceTag from the KB
- Argument construction computes tags via ⊗ (sequential composition)
- Multiple arguments for the same conclusion combine via ⊕ (parallel accumulation)
- Defeat comparison uses tag strength (not just categorical preference)
- Epistemic status derived from extension membership + tag values

This is the core contribution of this thesis.

### 9.4 Phase 4: Full System with GraphRAG

Add T3 (retrieval corpus) integration:
- Argument premises linked to retrieved text chunks
- Provenance chains include T3 source attributions
- Retrieved prose provides the exposition layer for synthesis

### 9.5 Core Data Structures

```python
# anvikshiki/schema_v4.py
"""Core data structures for the argumentation-based engine."""

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Optional, FrozenSet
from datetime import datetime


class PramanaType(IntEnum):
    """Pramāṇa hierarchy — higher value = stronger epistemic channel."""
    UPAMANA = 1      # Analogy (weakest)
    SABDA = 2        # Testimony
    ANUMANA = 3      # Inference
    PRATYAKSA = 4    # Direct evidence (strongest)


class RuleType(Enum):
    STRICT = "strict"           # Definitional, structural — cannot be attacked
    DEFEASIBLE = "defeasible"   # Empirical, regulatory — can be undercut


class EpistemicStatus(Enum):
    """Derived from argumentation semantics — NOT hand-assigned."""
    ESTABLISHED = "established"     # IN grounded, strong tag
    HYPOTHESIS = "hypothesis"       # IN grounded, moderate tag
    PROVISIONAL = "provisional"     # IN grounded, from ordinary premises only
    OPEN = "open"                   # UNDECIDED in grounded extension
    CONTESTED = "contested"         # OUT in grounded, IN in preferred


@dataclass(frozen=True)
class ProvenanceTag:
    """
    Semiring-valued annotation on arguments.
    Extends Subjective Logic opinions with provenance metadata.
    """
    belief: float = 1.0              # Evidence FOR [0,1]
    disbelief: float = 0.0           # Evidence AGAINST [0,1]
    uncertainty: float = 0.0         # Ignorance [0,1] (b + d + u ≈ 1)
    source_ids: FrozenSet[str] = frozenset()
    pramana_type: PramanaType = PramanaType.ANUMANA
    trust_score: float = 1.0         # Source authority [0,1]
    decay_factor: float = 1.0        # Temporal freshness [0,1]
    derivation_depth: int = 0

    @staticmethod
    def tensor(a: 'ProvenanceTag', b: 'ProvenanceTag') -> 'ProvenanceTag':
        """⊗: Sequential composition (chaining through inference)."""
        return ProvenanceTag(
            belief=a.belief * b.belief,
            disbelief=min(1.0, a.disbelief + b.disbelief
                         - a.disbelief * b.disbelief),
            uncertainty=min(1.0, a.uncertainty + b.uncertainty
                           - a.uncertainty * b.uncertainty),
            source_ids=a.source_ids | b.source_ids,
            pramana_type=PramanaType(min(a.pramana_type, b.pramana_type)),
            trust_score=min(a.trust_score, b.trust_score),
            decay_factor=min(a.decay_factor, b.decay_factor),
            derivation_depth=a.derivation_depth + b.derivation_depth,
        )

    @staticmethod
    def oplus(a: 'ProvenanceTag', b: 'ProvenanceTag') -> 'ProvenanceTag':
        """⊕: Parallel composition (accrual of independent arguments)."""
        # Cumulative fusion (Jøsang 2016)
        kappa = a.uncertainty + b.uncertainty \
            - a.uncertainty * b.uncertainty
        if kappa < 1e-10:
            # Both fully certain — weighted average
            new_b = (a.belief + b.belief) / 2
            new_d = (a.disbelief + b.disbelief) / 2
            new_u = 0.0
        else:
            new_b = (a.belief * b.uncertainty
                     + b.belief * a.uncertainty) / kappa
            new_d = (a.disbelief * b.uncertainty
                     + b.disbelief * a.uncertainty) / kappa
            new_u = (a.uncertainty * b.uncertainty) / kappa

        return ProvenanceTag(
            belief=min(1.0, new_b),
            disbelief=min(1.0, new_d),
            uncertainty=max(0.0, new_u),
            source_ids=a.source_ids | b.source_ids,
            pramana_type=PramanaType(max(a.pramana_type, b.pramana_type)),
            trust_score=1 - (1 - a.trust_score) * (1 - b.trust_score),
            decay_factor=max(a.decay_factor, b.decay_factor),
            derivation_depth=min(a.derivation_depth, b.derivation_depth),
        )

    @staticmethod
    def zero() -> 'ProvenanceTag':
        """Additive identity — no evidence."""
        return ProvenanceTag(belief=0, disbelief=0, uncertainty=1.0)

    @staticmethod
    def one() -> 'ProvenanceTag':
        """Multiplicative identity — certain, no degradation."""
        return ProvenanceTag(belief=1.0, disbelief=0, uncertainty=0)

    @property
    def strength(self) -> float:
        """Scalar strength for comparison: belief × trust × decay."""
        return self.belief * self.trust_score * self.decay_factor

    def epistemic_status(self) -> EpistemicStatus:
        """Derive epistemic status from tag values."""
        if self.belief > 0.8 and self.uncertainty < 0.1:
            return EpistemicStatus.ESTABLISHED
        elif self.belief > 0.5 and self.uncertainty < 0.3:
            return EpistemicStatus.HYPOTHESIS
        elif self.disbelief > 0.4 and self.belief > 0.3:
            return EpistemicStatus.CONTESTED
        elif self.uncertainty > 0.6:
            return EpistemicStatus.OPEN
        else:
            return EpistemicStatus.PROVISIONAL


# ─── ARGUMENTS ───────────────────────────────────────────────

@dataclass(frozen=True)
class Argument:
    """A structured argument in the ASPIC+ framework."""
    id: str
    conclusion: str                    # Predicate concluded
    top_rule: Optional[str]            # Vyāpti ID (None for premise arguments)
    sub_arguments: tuple = ()          # Sub-argument IDs
    premises: FrozenSet[str] = frozenset()  # Base fact predicates
    is_strict: bool = False            # Strict vs defeasible top rule
    tag: ProvenanceTag = field(
        default_factory=ProvenanceTag.one)


@dataclass
class Attack:
    """An attack between arguments."""
    attacker: str       # Argument ID
    target: str         # Argument ID
    attack_type: str    # "undermining" | "undercutting" | "rebutting"
    hetvabhasa: str     # Nyāya fallacy type this corresponds to


class Label(Enum):
    IN = "in"           # Accepted — all attackers are OUT
    OUT = "out"         # Defeated — at least one attacker is IN
    UNDECIDED = "undecided"  # Neither accepted nor defeated
```

### 9.6 The Argumentation Engine

```python
# anvikshiki/argumentation_engine.py
"""
Argumentation engine computing ASPIC+ grounded semantics
via Datalog-style fixpoint evaluation over provenance semirings.
"""

from dataclasses import dataclass, field
from .schema_v4 import (
    Argument, Attack, Label, ProvenanceTag, PramanaType
)


@dataclass
class ArgumentationFramework:
    """
    The instantiated argumentation framework.

    Computed from KB at compile time (arguments + attacks).
    Evaluated at query time with query-specific facts added.
    """
    arguments: dict[str, Argument] = field(default_factory=dict)
    attacks: list[Attack] = field(default_factory=list)
    labels: dict[str, Label] = field(default_factory=dict)

    # Index structures for efficient lookup
    _attackers_of: dict[str, list[str]] = field(default_factory=dict)
    _attacks_on: dict[str, list[Attack]] = field(default_factory=dict)

    def add_argument(self, arg: Argument):
        self.arguments[arg.id] = arg

    def add_attack(self, attack: Attack):
        self.attacks.append(attack)
        self._attackers_of.setdefault(attack.target, []).append(
            attack.attacker)
        self._attacks_on.setdefault(attack.target, []).append(attack)

    def compute_grounded(self) -> dict[str, Label]:
        """
        Compute grounded labeling via iterative propagation.

        Algorithm (Wu, Caminada & Gabbay 2009):
        1. Label all unattacked arguments IN
        2. Label all arguments attacked by an IN argument OUT
        3. For remaining: if all attackers are OUT, label IN
        4. Repeat until fixpoint
        5. Everything unlabeled is UNDECIDED

        Complexity: O(|arguments| × |attacks|) — polynomial.
        """
        labels = {}

        # Initialize: all unlabeled
        remaining = set(self.arguments.keys())

        changed = True
        while changed:
            changed = False

            for arg_id in list(remaining):
                attackers = self._attackers_of.get(arg_id, [])

                # No attackers → IN
                if not attackers:
                    labels[arg_id] = Label.IN
                    remaining.discard(arg_id)
                    changed = True
                    continue

                # All attackers OUT → IN
                if all(labels.get(a) == Label.OUT
                       for a in attackers):
                    labels[arg_id] = Label.IN
                    remaining.discard(arg_id)
                    changed = True
                    continue

                # Any attacker IN → check defeat with preferences
                if any(labels.get(a) == Label.IN
                       for a in attackers):
                    # Check preference: does the target survive?
                    defeated = False
                    for atk in self._attacks_on.get(arg_id, []):
                        if labels.get(atk.attacker) != Label.IN:
                            continue
                        attacker_arg = self.arguments[atk.attacker]
                        target_arg = self.arguments[arg_id]
                        if self._defeats(attacker_arg, target_arg):
                            defeated = True
                            break

                    if defeated:
                        labels[arg_id] = Label.OUT
                        remaining.discard(arg_id)
                        changed = True

        # Everything remaining is UNDECIDED
        for arg_id in remaining:
            labels[arg_id] = Label.UNDECIDED

        self.labels = labels
        return labels

    def _defeats(self, attacker: Argument, target: Argument) -> bool:
        """
        Does the attack from attacker succeed as defeat?

        Uses pramāṇa-based preference:
        Attack succeeds unless target's pramāṇa type
        is strictly higher than attacker's.
        When equal, compare tag strength.
        """
        a_pramana = attacker.tag.pramana_type
        t_pramana = target.tag.pramana_type

        # Higher pramāṇa always wins (bādhita override)
        if t_pramana > a_pramana:
            return False  # Target survives — higher epistemic channel
        if a_pramana > t_pramana:
            return True   # Attacker wins — higher epistemic channel

        # Same pramāṇa — compare tag strength
        return attacker.tag.strength >= target.tag.strength

    def get_epistemic_status(self, conclusion: str) -> tuple:
        """
        Derive epistemic status for a conclusion from the extension.

        Returns (EpistemicStatus, ProvenanceTag, list[Argument]).
        """
        # Find all arguments for this conclusion
        args_for = [
            a for a in self.arguments.values()
            if a.conclusion == conclusion
        ]

        if not args_for:
            return (None, ProvenanceTag.zero(), [])

        # Combine tags of accepted arguments via ⊕
        accepted = [
            a for a in args_for
            if self.labels.get(a.id) == Label.IN
        ]

        if not accepted:
            # Check if any are UNDECIDED
            undecided = [
                a for a in args_for
                if self.labels.get(a.id) == Label.UNDECIDED
            ]
            if undecided:
                combined = undecided[0].tag
                for a in undecided[1:]:
                    combined = ProvenanceTag.oplus(combined, a.tag)
                return (combined.epistemic_status(), combined, undecided)
            else:
                # All OUT — contested
                from .schema_v4 import EpistemicStatus
                combined = args_for[0].tag
                for a in args_for[1:]:
                    combined = ProvenanceTag.oplus(combined, a.tag)
                return (EpistemicStatus.CONTESTED, combined, args_for)

        # Combine accepted arguments
        combined = accepted[0].tag
        for a in accepted[1:]:
            combined = ProvenanceTag.oplus(combined, a.tag)

        return (combined.epistemic_status(), combined, accepted)
```

### 9.7 The Compilation Pipeline (T2 Compiler)

```python
# anvikshiki/t2_compiler_v4.py
"""
T2 Compiler v4: Compile verified architecture into
an argumentation framework over provenance semirings.
"""

from datetime import datetime
from .schema_v4 import (
    Argument, Attack, ProvenanceTag, PramanaType, RuleType
)
from .argumentation_engine import ArgumentationFramework


def compile_t2(knowledge_store, query_facts: list[dict]) -> ArgumentationFramework:
    """
    Build the argumentation framework:
    1. Create premise arguments from base facts
    2. Create rule-based arguments from vyāptis
    3. Derive attacks from contradictions, scope violations, hetvābhāsas
    """
    af = ArgumentationFramework()
    arg_counter = 0

    # ── Step 1: Premise arguments from grounded query facts ──
    for fact in query_facts:
        arg_id = f"A{arg_counter:04d}"
        arg_counter += 1

        tag = ProvenanceTag(
            belief=fact.get("confidence", 0.9),
            disbelief=0.0,
            uncertainty=1.0 - fact.get("confidence", 0.9),
            source_ids=frozenset(fact.get("sources", [])),
            pramana_type=PramanaType.PRATYAKSA,
            trust_score=1.0,
            decay_factor=1.0,
            derivation_depth=0,
        )

        af.add_argument(Argument(
            id=arg_id,
            conclusion=fact["predicate"],
            top_rule=None,
            premises=frozenset([fact["predicate"]]),
            is_strict=True,
            tag=tag,
        ))

    # ── Step 2: Rule-based arguments from vyāptis ──
    for vid, v in knowledge_store.vyaptis.items():
        # Check if antecedents are available
        available = {
            a.conclusion for a in af.arguments.values()
        }

        if not all(ant in available for ant in v.antecedents):
            continue  # Can't build this argument yet

        # Find sub-arguments for antecedents
        sub_arg_ids = []
        sub_tags = []
        for ant in v.antecedents:
            # Pick the strongest available argument for this antecedent
            candidates = [
                a for a in af.arguments.values()
                if a.conclusion == ant
            ]
            if candidates:
                best = max(candidates, key=lambda a: a.tag.strength)
                sub_arg_ids.append(best.id)
                sub_tags.append(best.tag)

        # Build the rule's own tag from KB metadata
        rule_tag = _build_rule_tag(v, knowledge_store)

        # Compute argument tag: ⊗ of rule tag with all sub-argument tags
        combined_tag = rule_tag
        for st in sub_tags:
            combined_tag = ProvenanceTag.tensor(combined_tag, st)

        arg_id = f"A{arg_counter:04d}"
        arg_counter += 1

        is_strict = v.causal_status.value in ("definitional", "structural")

        af.add_argument(Argument(
            id=arg_id,
            conclusion=v.consequent,
            top_rule=vid,
            sub_arguments=tuple(sub_arg_ids),
            premises=frozenset().union(*(
                af.arguments[sa].premises for sa in sub_arg_ids
            )),
            is_strict=is_strict,
            tag=combined_tag,
        ))

    # ── Step 3: Derive attacks ──

    # 3a. Rebutting attacks (viruddha): arguments with contradictory conclusions
    conclusions = {}
    for a in af.arguments.values():
        conclusions.setdefault(a.conclusion, []).append(a.id)

    for conc, arg_ids in conclusions.items():
        neg_conc = f"not_{conc}" if not conc.startswith("not_") \
            else conc[4:]
        if neg_conc in conclusions:
            for pos_id in arg_ids:
                for neg_id in conclusions[neg_conc]:
                    af.add_attack(Attack(
                        attacker=neg_id, target=pos_id,
                        attack_type="rebutting",
                        hetvabhasa="viruddha"
                    ))
                    af.add_attack(Attack(
                        attacker=pos_id, target=neg_id,
                        attack_type="rebutting",
                        hetvabhasa="viruddha"
                    ))

    # 3b. Undercutting attacks (savyabhicāra): scope violations
    for a in af.arguments.values():
        if a.top_rule is None:
            continue
        v = knowledge_store.vyaptis.get(a.top_rule)
        if not v:
            continue
        for excl in v.scope_exclusions:
            # If the excluded condition is established as a fact
            if any(arg.conclusion == excl
                   for arg in af.arguments.values()):
                # Create an undercutting attack
                scope_arg_id = f"A{arg_counter:04d}"
                arg_counter += 1
                af.add_argument(Argument(
                    id=scope_arg_id,
                    conclusion=f"_undercut_{a.top_rule}",
                    top_rule=None,
                    premises=frozenset([excl]),
                    is_strict=True,
                    tag=ProvenanceTag(
                        belief=1.0, disbelief=0.0, uncertainty=0.0,
                        pramana_type=PramanaType.PRATYAKSA,
                        trust_score=1.0, decay_factor=1.0,
                    ),
                ))
                af.add_attack(Attack(
                    attacker=scope_arg_id, target=a.id,
                    attack_type="undercutting",
                    hetvabhasa="savyabhicara"
                ))

    # 3c. Undermining attacks (asiddha): decay-expired premises
    for a in af.arguments.values():
        if a.tag.decay_factor < 0.3:
            decay_arg_id = f"A{arg_counter:04d}"
            arg_counter += 1
            af.add_argument(Argument(
                id=decay_arg_id,
                conclusion=f"_stale_{a.id}",
                top_rule=None,
                premises=frozenset(["_temporal_decay"]),
                is_strict=True,
                tag=ProvenanceTag(
                    belief=1.0 - a.tag.decay_factor,
                    pramana_type=PramanaType.PRATYAKSA,
                    trust_score=1.0, decay_factor=1.0,
                ),
            ))
            af.add_attack(Attack(
                attacker=decay_arg_id, target=a.id,
                attack_type="undermining",
                hetvabhasa="asiddha"
            ))

    # ── Step 4: Forward chain (iterate until no new arguments) ──
    # Re-run Step 2 with newly derived conclusions until fixpoint
    # (omitted for brevity — same logic in a loop with delta tracking)

    return af


def _build_rule_tag(vyapti, knowledge_store) -> ProvenanceTag:
    """Build a provenance tag for a vyāpti from its KB metadata."""
    from .schema import EpistemicStatus, CausalStatus

    # Map causal status to pramāṇa type
    pramana_map = {
        CausalStatus.DEFINITIONAL: PramanaType.PRATYAKSA,
        CausalStatus.STRUCTURAL: PramanaType.PRATYAKSA,
        CausalStatus.EMPIRICAL: PramanaType.ANUMANA,
        CausalStatus.REGULATORY: PramanaType.SABDA,
    }

    # Map epistemic status to belief/uncertainty
    belief_map = {
        EpistemicStatus.ESTABLISHED: (0.95, 0.0, 0.05),
        EpistemicStatus.WORKING_HYPOTHESIS: (0.6, 0.1, 0.3),
        EpistemicStatus.PROVISIONAL: (0.4, 0.1, 0.5),
        EpistemicStatus.GENUINELY_OPEN: (0.2, 0.2, 0.6),
        EpistemicStatus.ACTIVELY_CONTESTED: (0.4, 0.4, 0.2),
    }
    b, d, u = belief_map.get(
        vyapti.epistemic_status, (0.5, 0.1, 0.4))

    # Trust from source authority
    trust = vyapti.confidence.formulation * vyapti.confidence.existence

    # Decay from time since verification
    decay = 1.0
    if vyapti.last_verified:
        age_days = (datetime.now() - vyapti.last_verified).days
        import math
        half_life = 365  # 1 year default
        decay = math.exp(-0.693 * age_days / half_life)

    return ProvenanceTag(
        belief=b,
        disbelief=d,
        uncertainty=u,
        source_ids=frozenset(vyapti.sources),
        pramana_type=pramana_map.get(
            vyapti.causal_status, PramanaType.ANUMANA),
        trust_score=trust,
        decay_factor=decay,
        derivation_depth=0,
    )
```

### 9.8 The Complete Engine

```python
# anvikshiki/engine_v4.py
"""
The Ānvīkṣikī Engine v4 — Argumentation over Provenance Semirings.

Pipeline:
1. Grounding (NL → predicates) — two-layer defense, unchanged from v3
2. Argument construction (predicates + KB → argumentation framework)
3. Extension computation (grounded semantics — polynomial)
4. Epistemic status derivation (extension membership + tag values)
5. Provenance extraction (argument trees → source attribution)
6. Uncertainty decomposition (from provenance tags — structural, not hand-tuned)
7. Synthesis (everything → calibrated NL response)
"""

import dspy
from .schema_v4 import EpistemicStatus, ProvenanceTag, Label
from .argumentation_engine import ArgumentationFramework
from .t2_compiler_v4 import compile_t2


class SynthesizeResponse(dspy.Signature):
    """Produce a calibrated response from argumentation results."""

    query: str = dspy.InputField()
    accepted_arguments: str = dspy.InputField(
        desc="Arguments accepted under grounded semantics")
    defeated_arguments: str = dspy.InputField(
        desc="Arguments defeated and why (hetvābhāsa type)")
    uncertainty_report: str = dspy.InputField(
        desc="Three-way uncertainty decomposition from provenance tags")
    retrieved_prose: str = dspy.InputField(
        desc="Relevant guide text for exposition")

    response: str = dspy.OutputField(
        desc="Natural language response with epistemic qualification")
    sources_cited: list[str] = dspy.OutputField(
        desc="Reference Bank entries supporting claims")


class AnvikshikiEngineV4(dspy.Module):
    """The complete Ānvīkṣikī Engine v4."""

    def __init__(self, knowledge_store, grounding_pipeline):
        super().__init__()
        self.ks = knowledge_store
        self.grounding = grounding_pipeline
        self.synthesizer = dspy.ChainOfThought(SynthesizeResponse)

    def forward(self, query: str, retrieved_chunks: list[str]):
        # ═══ STEP 1: Ground query ═══
        grounding = self.grounding(query)
        if grounding.clarification_needed:
            return dspy.Prediction(
                response=f"I need clarification. "
                         f"Disputed: {grounding.disputed}",
                uncertainty={"type": "grounding_ambiguity"},
            )

        # ═══ STEP 2: Build argumentation framework ═══
        query_facts = [
            {"predicate": p.split("(")[0],
             "confidence": grounding.confidence,
             "sources": []}
            for p in grounding.predicates
        ]
        af = compile_t2(self.ks, query_facts)

        # ═══ STEP 3: Compute grounded extension ═══
        labels = af.compute_grounded()

        # ═══ STEP 4: Derive epistemic status per conclusion ═══
        conclusions = set(a.conclusion for a in af.arguments.values())
        results = {}
        for conc in conclusions:
            if conc.startswith("_"):  # Skip internal predicates
                continue
            status, tag, args = af.get_epistemic_status(conc)
            results[conc] = {
                "status": status,
                "tag": tag,
                "arguments": args,
            }

        # ═══ STEP 5: Extract provenance ═══
        provenance = {}
        for conc, info in results.items():
            provenance[conc] = {
                "sources": list(info["tag"].source_ids),
                "pramana": info["tag"].pramana_type.name,
                "derivation_depth": info["tag"].derivation_depth,
                "trust": info["tag"].trust_score,
                "decay": info["tag"].decay_factor,
            }

        # ═══ STEP 6: Uncertainty decomposition ═══
        # (structural — derived entirely from provenance tags)
        uncertainty = {}
        for conc, info in results.items():
            tag = info["tag"]
            uncertainty[conc] = {
                "epistemic": {
                    "status": info["status"].value if info["status"] else "none",
                    "belief": tag.belief,
                    "uncertainty": tag.uncertainty,
                },
                "aleatoric": {
                    "disbelief": tag.disbelief,
                    "explanation": (
                        "High disbelief indicates inherent domain "
                        "disagreement" if tag.disbelief > 0.3
                        else "Low domain-level contestation"
                    ),
                },
                "inference": {
                    "grounding_confidence": grounding.confidence,
                    "decay_factor": tag.decay_factor,
                    "derivation_depth": tag.derivation_depth,
                },
                "total_confidence": tag.strength,
            }

        # ═══ STEP 7: Collect defeated arguments (hetvābhāsas) ═══
        violations = []
        for atk in af.attacks:
            if labels.get(atk.attacker) == Label.IN:
                violations.append({
                    "hetvabhasa": atk.hetvabhasa,
                    "type": atk.attack_type,
                    "attacker": atk.attacker,
                    "target": atk.target,
                    "target_conclusion": af.arguments[atk.target].conclusion,
                })

        # ═══ STEP 8: Synthesize response ═══
        accepted_str = "\n".join(
            f"- {conc}: {info['status'].value if info['status'] else 'none'} "
            f"(belief={info['tag'].belief:.2f}, "
            f"trust={info['tag'].trust_score:.2f}, "
            f"sources={list(info['tag'].source_ids)[:3]})"
            for conc, info in results.items()
            if info["status"] and info["status"] != EpistemicStatus.CONTESTED
        )

        defeated_str = "\n".join(
            f"- {v['target_conclusion']} defeated by {v['hetvabhasa']} "
            f"({v['type']})"
            for v in violations
        )

        response = self.synthesizer(
            query=query,
            accepted_arguments=accepted_str or "No conclusions derived",
            defeated_arguments=defeated_str or "No fallacies detected",
            uncertainty_report=str(uncertainty),
            retrieved_prose="\n".join(retrieved_chunks),
        )

        return dspy.Prediction(
            response=response.response,
            sources=response.sources_cited,
            uncertainty=uncertainty,
            provenance=provenance,
            violations=violations,
            grounding_confidence=grounding.confidence,
            extension_size=sum(
                1 for l in labels.values() if l == Label.IN),
        )
```

---

## 10. Further Directions

**1. Preferred semantics for exploratory reasoning.** Grounded semantics is maximally skeptical — appropriate for the engine's default "cautious" mode (Nyāya's vāda). For exploratory queries ("what if we assume X?"), preferred semantics would accept more arguments at the cost of NP-hard computation. Approximation algorithms (Nofal et al. 2014) or GPU-accelerated solvers could make this practical.

**2. Differentiable provenance tags.** Scallop (Li et al., PLDI 2023) demonstrates that differentiable semirings enable end-to-end gradient flow through Datalog evaluation. Applying this to argumentation would allow learning optimal tag parameters from query-outcome pairs — the provenance tag's belief/trust/decay mappings would be *learned*, not hand-specified.

**3. Multi-domain argumentation via geometric morphisms.** When two domain guides exist (e.g., corporate strategy + financial accounting), their argumentation frameworks are independent. A geometric morphism between their underlying topoi would formalize how arguments transfer across domains — which strategic arguments are relevant to financial reasoning and vice versa. This preserves the topos-theoretic contribution from v3 while giving it real computational content.

**4. Temporal argumentation for decay.** Instead of a scalar decay_factor, model temporal decay as a separate argument: "This rule was verified 2 years ago" is an undercutting attacker on the rule. The decay *creates attacks* rather than degrading tags — which is semantically more honest (staleness is a reason to doubt, not a reduction in evidence strength).

**5. Active learning for the knowledge base.** When the grounded extension is small relative to the argument set (many UNDECIDED conclusions), the system could identify which specific evidence — if provided — would maximally extend the grounded extension. This is the argumentation-theoretic version of active learning: "what question should I ask the expert to resolve the most arguments?"

**6. Adversarial robustness via stable semantics.** Stable semantics (which is NP-hard) provides a guarantee: everything not accepted is attacked by something accepted. This is relevant for adversarial settings where an agent might try to inject misleading arguments. Under stable semantics, there are no "gaps" — every claim is either defended or refuted.

**7. Argumentation-based explanation generation.** The argument tree is already a proof trace. But for human consumption, the engine could generate natural language *dialectical* explanations: "The claim X is supported by arguments A and B, but challenged by argument C (which raises the concern of survivorship bias). Argument C is itself defeated because D provides base-rate evidence. Therefore X is accepted with moderate confidence." This is richer than the v3 flat proof trace.

**8. Integration with DSPy optimization.** Define an end-to-end metric over the full argumentation pipeline: grounding accuracy × extension quality × synthesis faithfulness × calibration. Use MIPROv2 or SIMBA to jointly optimize the grounding module, tag-value mappings, and synthesis prompts. The argumentation engine remains symbolic and deterministic — only the LLM-dependent components are optimized.

**9. Nyāya debate protocols as meta-argumentation.** The three Nyāya debate types (vāda, jalpa, vitaṇḍā) could be implemented as meta-level argumentation protocols: vāda = cooperative query mode (both user and engine contribute arguments), jalpa = adversarial testing mode (engine generates strongest counter-arguments to stress-test conclusions), vitaṇḍā = pure critique mode (engine only attacks, never defends — useful for risk assessment).

---

## 11. References

### Argumentation Theory

- **Dung, P.M.** "On the Acceptability of Arguments and Its Fundamental Role in Nonmonotonic Reasoning, Logic Programming, and n-Person Games." *Artificial Intelligence* 77(2), 321–357, 1995.
- **Prakken, H.** "An Abstract Framework for Argumentation with Structured Arguments." *Argument & Computation* 1(2), 93–124, 2010.
- **Modgil, S. & Prakken, H.** "A General Account of Argumentation with Preferences." *Artificial Intelligence* 195, 361–397, 2013.
- **Modgil, S. & Prakken, H.** "Abstract Rule-Based Argumentation." In Baroni et al. (eds.), *Handbook of Formal Argumentation*, College Publications, 2018.
- **Caminada, M. & Amgoud, L.** "On the Evaluation of Argumentation Formalisms." *Artificial Intelligence* 171(5–6), 286–310, 2007.
- **Wu, Y., Caminada, M. & Gabbay, D.** "Complete Extensions in Argumentation Coincide with 3-Valued Stable Models in Logic Programming." *Studia Logica* 93, 383–403, 2009.
- **Dvořák, W. & Dunne, P.E.** "Computational Problems in Formal Argumentation and Their Complexity." In *Handbook of Formal Argumentation*, Chapter 5, 2018.
- **Diller, M., Keshavarzi Zafarghandi, A. & Wallner, J.P.** "Grounding ASPIC+ with Datalog." *Proceedings of KR 2025*, 28.

### Gradual and Weighted Argumentation

- **Besnard, P. & Hunter, A.** "A Logic-Based Theory of Deductive Arguments." *Artificial Intelligence* 128(1–2), 203–235, 2001.
- **Rago, A., Toni, F., Aurisicchio, M. & Baroni, P.** "Discontinuity-Free Decision Support with Quantitative Argumentation Debates." *Proceedings of KR 2016*.
- **Bistarelli, S. & Santini, F.** "A Conarg-Based Library for Abstract Argumentation Frameworks." *Proceedings of ECAI 2010*.
- **Dunne, P.E., Hunter, A., McBurney, P., Parsons, S. & Wooldridge, M.** "Weighted Argument Systems: Basic Definitions, Algorithms, and Complexity Results." *Artificial Intelligence* 175(2), 457–486, 2011.

### Provenance Semirings and Datalog

- **Green, T.J., Karvounarakis, G. & Tannen, V.** "Provenance Semirings." *Proceedings of PODS 2007*, 31–40. ACM.
- **Khamis, M.A., Ngo, H.Q., Pichler, R., Suciu, D. & Wang, Y.R.** "Convergence of Datalog over (Pre-) Semirings." *Proceedings of PODS 2022*. ACM.
- **Bourgaux, C., Ozaki, A., Peñaloza, R. & Predoiu, L.** "Revisiting Semiring Provenance for Description Logics." *Proceedings of KR 2022*.
- **Li, Z., Huang, J. & Naik, M.** "Scallop: A Language for Neurosymbolic Programming." *Proceedings of PLDI 2023*. ACM.
- **Li, Z., Huang, J. & Naik, M.** *Neurosymbolic Programming with Scallop*. Foundations and Trends in Programming Languages, 2024.
- **Madsen, M., Yee, M.-H. & Lhoták, O.** "From Datalog to Flix: A Declarative Language for Fixed Points on Lattices." *Proceedings of PLDI 2016*. ACM.

### Subjective Logic

- **Jøsang, A.** *Subjective Logic: A Formalism for Reasoning Under Uncertainty.* Springer, 2016.
- **Dong, X.L., Gabrilovich, E., Murphy, K., Dang, V., Horn, W., Luber, C., Sun, S. & Zhang, W.** "Knowledge-Based Trust: Estimating the Trustworthiness of Web Sources." *Proceedings of the VLDB Endowment* 8(9), 938–949, 2015.

### Nyāya Epistemology and Indian Logic

- **Gautama.** *Nyāya Sūtras.* c. 2nd century BCE.
- **Matilal, B.K.** *Epistemology, Logic, and Grammar in Indian Philosophical Analysis.* Mouton, 1971; new edition edited by J. Ganeri, Oxford University Press, 2005.
- **Ganeri, J.** "Ancient Indian Logic as a Theory of Case-Based Reasoning." *Journal of Indian Philosophy* 31, 33–45, 2003.
- **Ganeri, J.** *The Lost Age of Reason: Philosophy in Early Modern India 1450–1700.* Oxford University Press, 2011.
- **Guhe, E.** *An Indian Theory of Defeasible Reasoning: The Doctrine of Upādhi in the Upādhidarpaṇa.* Harvard Oriental Series, Harvard University Press, 2022.
- **Guhe, E.** "The Logic of Late Nyāya: A Property-Theoretic Framework for a Formal Reconstruction." In *Handbook of Logical Thought in India*, Springer.
- **Oetke, C.** "Ancient Indian Logic as a Theory of Non-Monotonic Reasoning." *Journal of Indian Philosophy* 24, 447–539, 1996.
- **Taber, J.** "Is Indian Logic Nonmonotonic?" *Philosophy East and West* 54(2), 143–170, 2004.
- **Keating, M.** "The Pragma-Dialectics of Dispassionate Discourse: Early Nyāya Argumentation Theory." *Religions* 12(10), 875, 2021.

### Neurosymbolic LLM Reasoning

- **Pan, L., Alber, A., Cai, C., et al.** "Logic-LM: Empowering Large Language Models with Symbolic Solvers for Faithful Logical Reasoning." *Findings of EMNLP 2023*.
- **Olausson, T.X., Gu, A., Lipkin, B., et al.** "LINC: A Neurosymbolic Approach for Logical Reasoning by Combining Language Models with First-Order Logic Provers." *EMNLP 2023*.
- **Wang, W. et al.** "ChatLogic: Integrating Logic Programming with Large Language Models for Multi-Step Reasoning." 2024.
- **Callewaert, K. et al.** "VERUS-LM: A Versatile Framework for Combining LLMs with Symbolic Reasoning." 2025.
- **Wang, Y. et al.** "DSPy-based Neural-Symbolic Pipeline to Enhance Spatial Reasoning in LLMs." arXiv:2411.18564, 2024.

### LLM + Argumentation

- **Freedman, R. et al.** "ArgLLMs: Large Language Models for Argumentation." *Proceedings of AAAI 2025*. arXiv:2405.02079.
- **Chen, Y. et al.** "Exploring the Potential of Large Language Models in Computational Argumentation." *Proceedings of ACL 2024*.
- **Li, X. et al.** "Argumentation Computation Benchmark with LLMs." arXiv:2412.16725, 2024.
- **Castagna, F. et al.** "MQArgEng: Multi-Quality Argumentation Engine." arXiv:2405.13036, 2024.

### Sheaf Theory in ML

- **Gebhart, T., Hansen, J. & Schrater, P.** "Knowledge Sheaves: A Sheaf-Theoretic Framework for Knowledge Graph Embedding." *AISTATS 2023*, PMLR 206, 9094–9116.
- **Bodnar, C. et al.** "Neural Sheaf Diffusion: A Topological Perspective on Heterophilic Graph Learning." *NeurIPS 2022*.

### Bilattices and Multi-Valued Logic

- **Fitting, M.** "Bilattices and the Semantics of Logic Programming." *Journal of Logic Programming* 11(2), 91–116, 1991.
- **Belnap, N.D.** "A Useful Four-Valued Logic." In Dunn & Epstein (eds.), *Modern Uses of Multiple-Valued Logic*, Reidel, 5–37, 1977.
- **Arieli, O. & Avron, A.** "Reasoning with Logical Bilattices." *Journal of Logic, Language and Information* 5(1), 25–63, 1996.

### Uncertainty and Epistemic Logic

- **Verreet, V. et al.** "BetaProbLog: Beta-Distributed Random Variables in ProbLog." *Proceedings of AAAI 2022*.
- **Goldman, A.** "What Is Justified Belief?" In Pappas (ed.), *Justification and Knowledge*, Reidel, 1–23, 1979.

### Frameworks and Tools

- **Khattab, O. et al.** "DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines." *ICLR 2024*.
- **Egly, U., Gaggl, S.A. & Woltran, S.** "ASPARTIX: Implementing Argumentation Frameworks Using Answer-Set Programming." *ICLP 2008*.
- **Strass, H.** "Approximating Operators and Semantics for Abstract Dialectical Frameworks." *Artificial Intelligence* 205, 39–70, 2013.

### Contestable AI

- **Hirsch, T., Merced, K., Kraut, R. & Hantsoo, L.** "Designing Contestability: Interaction Design, Machine Learning, and Mental Health." *Proceedings of DIS 2017*, 95–99. ACM.
- **Mulligan, D.K., Kluttz, D. & Kohli, N.** "Shaping Our Tools: Contestability as a Means to Promote Responsible Algorithmic Decision Making in the Professions." *Draft, UC Berkeley*, 2019.
- **Almada, M.** "Human Intervention in Automated Decision-Making: Toward the Construction of Contestable Systems." *Proceedings of ICAIL 2019*, 2–11. ACM.
- **Ploug, T. & Holm, S.** "The Right to Contest AI Diagnostics." In Burr & Milano (eds.), *The 2019 Yearbook of the Digital Ethics Lab*, Springer, 2020.
- **Henin, C. & Le Métayer, D.** "Beyond Explainability: Justifiability and Contestability of Algorithmic Decision Systems." *AI & Society* 37, 1397–1410, 2022.
- **Cyras, K., Rago, A., Albini, E., Baroni, P. & Toni, F.** "Argumentative XAI: A Survey." *Proceedings of IJCAI 2021*, 4392–4399.
- **Alfrink, K., Keller, I., Doorn, N. & Kortuem, G.** "Contestable AI by Design: Towards a Framework." *Minds and Machines* 33, 613–639, 2023.
- **Leofante, F., Toni, F., Rago, A., Fermé, E. & Reis, J.** "Contestable AI Needs Computational Argumentation." *Proceedings of KR 2024*.
- **Freedman, R., Toni, F., Rago, A. et al.** "ArgLLMs: Leveraging Large Language Models for Argumentation Frameworks." *Proceedings of AAAI 2025*. arXiv:2405.02079.
- **Moreira, C. et al.** "Contestable AI Systems: A Comprehensive Framework." 2025.
- **ArgRAG.** "ArgRAG: Argumentation-Driven Retrieval-Augmented Generation." 2025.

### Pedagogical Theory

- **Meyer, J.H.F. & Land, R.** "Threshold Concepts and Troublesome Knowledge." 2003.
- **Sweller, J.** "Cognitive Load During Problem Solving." *Cognitive Science* 12(2), 1988.
- **Polanyi, M.** *The Tacit Dimension.* 1966.
