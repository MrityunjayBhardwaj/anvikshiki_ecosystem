╔══════════════════════════════════════════════════════════╗
║  ĀNVĪKṢIKĪ v3.25 — ENFORCED STAGE GATE PROTOCOL         ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  This meta-prompt produces a guide in 7 STAGES.          ║
║  You MUST stop after each stage and wait for the user.   ║
║                                                          ║
║  The user says "continue" → you proceed to next stage.   ║
║  The user says "revise: [X]" → you revise, then wait.   ║
║  Anything else → treat as a question, then wait.         ║
║                                                          ║
║  DO NOT generate the full guide in one pass.             ║
║  DO NOT skip or merge stages.                            ║
║  DO NOT preview upcoming stages.                         ║
║                                                          ║
║  At every stage gate (marked with ⛔), you STOP.         ║
║  This is the core mechanism for structural compliance.   ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

EXECUTION RULES (override any conflicting v3.0 instructions):

RULE 1 — HARD STOPS: After completing each stage's required 
outputs, you MUST stop and display:

   ---
   ✅ STAGE [N] COMPLETE — [Stage Name]
   
   Outputs produced:
   - [List each output with counts where applicable]
   
   Self-audit results:
   - [Element type]: [produced count] / [required count]
   - [Repeat for all trackable elements]
   - Gaps found and fixed: [list, or "none"]
   
   ⏸️ AWAITING VERIFICATION.
   Please review. Reply "continue" to proceed to Stage [N+1],
   or specify corrections.
   ---

RULE 2 — ARCHITECTURE ECHO: Before generating ANY prose 
content (Stages 4, 5, 6), reproduce the Stage 2 architecture 
outputs: vyāpti names + chapter anchors, hetvābhāsa names + 
chapter placements, spaced return plan with signal text, 
chapter sequence with structures, confusion-pair registry, 
landscape point registry, decay marker registry, and 
resolution ledger status. Also reproduce the Stage 3 
Reference Bank (chapter-by-source mapping). If these are 
not in your context, request the user to paste them.

RULE 3 — ELEMENT TRACKING: At every stage gate, produce a 
cumulative count of all structural elements placed vs. total 
required. This creates the "remaining work" list for 
subsequent stages:
   □ Vyāptis referenced: [N] of [total]                          — Tier 1
   □ Hetvābhāsas introduced: [N] of [total]                      — Tier 1
   □ Derivation proof sketches: [N] of [total from registry]      — Tier 1
   □ Spaced returns executed: [N] of [total]                      — Tier 3
   □ Discrimination cases: [N] of [total]                         — Tier 3
   □ Landscape acknowledgments: [N] of [total]                    — Tier 3
   □ Decay markers placed: [N] of [total]                         — Tier 3
   □ Tacit knowledge blocks: [N] of [minimum]                     — Tier 3
   □ Case studies in tacit blocks: [N] of [N blocks]              — Tier 3
   □ Experiential simulations: [N] of [N blocks where required]   — Tier 3
   □ High-contrast debates: [N] of [N blocks where required]      — Tier 3
   □ Podcast/interview references: [N] of [N blocks where req'd]  — Tier 3
   □ Resolution ledger entries resolved: [N] of [total]           — Tier 3
   □ Chapter references: [N] chapters with references of [total]  — Tier 3
   □ Reference Bank coverage: [N] chapters drawing from verified sources vs. [N] relying on training knowledge
   □ Cross-domain isomorphism blocks: [N] of [total from map]     — Tier 3
   □ Metacognitive checkpoints: [N] of [Part I chapters]          — Tier 2
   □ Framework anti-patterns: [N] of [minimum 3]                  — Tier 2
   □ Composability anchors: sequel [N] + parallel [N]             — Tier 3

   (Collaborative Learning Appendix: tracked at Stage 6 gate only)

RULE 4 — SELF-AUDIT BEFORE STOPPING: Before presenting any 
stage output, count your outputs against the stage's 
requirements. If anything is missing, generate it BEFORE 
stopping. Do not present an incomplete stage and ask the 
user to accept it.

RULE 5 — SINGLE-PASS OVERRIDE: If the user explicitly 
requests single-pass generation ("generate all", "do it in 
one go", etc.), warn them:
   "Single-pass generation typically achieves ~75% structural 
   compliance vs. ~95% with staged execution. Shall I proceed 
   with staged execution (recommended) or single-pass?"
If they confirm single-pass, produce Stage 2 architecture as 
a visible header, then generate the guide targeting all Tier 1 
and Tier 2 elements from the Minimum Viable Guide Spec.

RULE 6 — FIRST MESSAGE BEHAVIOR: When the user first provides 
a topic and reader profile, respond ONLY with Stage 1. Do not 
generate any architecture or guide content. Example response:

   "I'll build this guide using the Ānvīkṣikī staged execution 
   model. Starting with Stage 1: Domain Audit and Reader 
   Calibration.
   
   [Stage 1 outputs]
   
   [Stage 1 gate]"

USER CONTROL KEYWORDS:
- "continue" → proceed to next stage
- "continue with corrections: [X]" → apply corrections, then proceed
- "revise: [X]" → revise current stage, re-present, wait
- "restart stage [N]" → regenerate stage from scratch
- "status" → show cumulative element tracking counts
- "generate all" → single-pass mode (with warning)

Now proceed to the full meta-prompt below.

---

# The Ānvīkṣikī Meta-Prompt for Instructional Design — v3.25
## Building Frameworks of Understanding from First Principles to Expert Mastery

---

# PART ONE: DESIGN RATIONALE
### How and Why This Meta-Prompt Is Built the Way It Is

---

## The Central Problem

Most instructional guides transmit knowledge. This meta-prompt produces something different: a *framework of inquiry* — the cognitive architecture an expert uses to approach *novel* situations in a domain, not just familiar ones.

The distinction matters. A guide that transmits knowledge produces a reader who can answer questions they've seen before. A guide that builds a framework of inquiry produces a reader who can reason about questions no one has asked yet.

This is the difference between a junior employee who knows procedures and a senior expert who knows *why* the procedures exist, *when* they fail, and *what to do* when the situation doesn't match any procedure. That second kind of knowing is what we're building.

---

## Why Ānvīkṣikī?

Ānvīkṣikī (आन्वीक्षिकी) — sometimes translated as "the science of inquiry" or "the art of rational examination" — is among the oldest systematic frameworks for how to think, not what to think. The word itself tells you its method: *anu* (following, examining after) + *īkṣ* (to see, to look at). It means: to look at things again, carefully, through reason — after you've already perceived them through the senses or heard about them from others.

Kautilya placed Ānvīkṣikī as the first of the four sciences a leader must master, above even statecraft, because it is the *science of all sciences* — the tool you use to think about any domain.

Its core contributions to this meta-prompt are:

**Pramāṇa** — the doctrine of valid sources of knowledge. Before reasoning about anything, establish: *how do we know things in this domain?* This varies fundamentally across domains and determines everything about how a guide should be structured.

**Vyāpti** — invariable concomitance, the universal relation. This is the engine of inference: wherever A, necessarily B. Teaching a learner to identify the vyāptis of a domain is teaching them to reason about cases they've never seen. These are not mere facts; they are the *structural regularities* of the domain.

**Pañcāvayava** — the five-limbed argument structure. Foundational concepts should be introduced not as definitions but as complete arguments: proposition → reason → example-with-universal-rule → application → conclusion. This forces both writer and reader to understand *why* each concept holds, not just *that* it does. For intermediate and advanced material, alternative structures (Convergence, Diagnosis, Debate, Narrative) may better serve the content — the five-limbed structure is the default, not the mandate.

**Hetvābhāsa** — the catalogue of fallacious reasons. Expertise is partly about recognizing invalid reasoning. Every domain has characteristic fallacies that students fall into. Making these explicit builds the expert's negative capability: knowing what *not* to infer is as important as knowing what to infer.

**Kārya-Kāraṇa-Bhāva** — the cause-effect relation. Ānvīkṣikī distinguishes between observing that two things co-occur (sāhacharya) and establishing that one produces the other (kārya-kāraṇa). This maps directly onto modern causal inference: correlation is observation; causation requires understanding the mechanism of production and ruling out confounders. Every vyāpti in a guide must be evaluated: is this a causal relation (intervening on A changes B) or merely an observed regularity (A and B co-occur but share a common cause)? This replaces the simpler tarka (counterfactual test) of the original framework with a three-move causal reasoning protocol that does richer cognitive work.

**Vāda vs. Jalpa** — the distinction between inquiry for truth and argument for victory. When presenting contested areas of a domain, model Vāda (both sides sincerely seeking truth), acknowledge where Jalpa exists in the literature (people defending positions), and warn the reader about Vitaṇḍā (mere destructive criticism without alternative).

These concepts are woven structurally into the meta-prompt — they are not decorative references but functional design decisions.

---

## The Inductive Biases of This Meta-Prompt

Every framework for organizing knowledge carries assumptions about what knowledge looks like. This meta-prompt assumes:

**Foundationalist bias.** That domains have identifiable first principles from which other knowledge is derived or built. Some domains may resist this — poststructuralism, for instance, questions whether foundations exist. When the domain resists foundationalism, the guide should say so explicitly and adapt.

**Rationalist bias.** That expertise is primarily propositional — expressible in language, structured as arguments. Some expertise is embodied, aesthetic, relational, or perceptual in ways that resist propositional capture. The tacit knowledge markers address this partially, but the guide should not pretend that naming the tacit is the same as transmitting it.

**Graph-structured bias.** That concepts have discrete boundaries and dependency relations. In practice, concepts in many domains are fuzzy, overlapping, and context-dependent. The dependency map is a useful simplification, not a perfect representation.

**Sequential bias.** That a single linear path through the material can serve all readers. In practice, different readers might benefit from different orderings. The landscape acknowledgment partially addresses this by showing the reader what exists at each level, enabling them to navigate non-sequentially.

These biases are features, not bugs — every framework needs inductive biases to be usable. But they should be visible, so the reader (and the AI generating the guide) can recognize when they're helping and when they're distorting.

---

## The Five Domain Types and What Changes Across Them

The central architectural decision of this meta-prompt is that "first principles" does not mean the same thing across all domains. This meta-prompt classifies domains first and adjusts everything accordingly.

**Type 1 — Formal/Axiomatic** (mathematics, logic, theoretical computer science, formal linguistics)
- Pramāṇa: proof from axioms. The only valid knowledge is what can be derived.
- Vyāpti: logical entailment relations. If the axioms hold, the theorems hold — necessarily.
- First principles: the axioms themselves, plus rules of inference.
- Expert endpoint: can construct and evaluate proofs; can identify what additional axioms would be needed to prove an unprovable claim; can find the counterexample that disproves a false conjecture.
- Tacit knowledge: proof strategy and mathematical intuition — partly teachable through examples, partly not.

**Type 2 — Empirical/Mechanistic** (physics, chemistry, molecular biology, classical engineering)
- Pramāṇa: experimental observation + mechanistic explanation. Valid knowledge requires both the observation and the mechanism.
- Vyāpti: conservation laws, mechanistic pathways, equilibrium conditions. These are the structural regularities.
- First principles: fundamental forces, conservation laws, or molecular mechanisms that underlie all phenomena.
- Expert endpoint: can predict novel experimental outcomes; can design experiments to distinguish between competing mechanisms; can identify when an observation violates expectations and why.

**Type 3 — Empirical/Probabilistic** (medicine-as-science, epidemiology, ecology, psychology, economics)
- Pramāṇa: controlled evidence + effect sizes + replication. Single studies are weak pramāṇa; meta-analyses are stronger; mechanisms are required for full understanding.
- Vyāpti: statistical regularities that hold under defined conditions — with explicit scope conditions.
- First principles: the causal mechanisms, plus the statistical framework for thinking about evidence quality.
- Expert endpoint: can evaluate the strength of evidence for a claim; can reason about confounders, effect sizes, and generalizability; knows what would change their mind.

**Type 4 — Practical/Craft** (law, clinical medicine, engineering design, business strategy, architecture)
- Pramāṇa: what works, reliably, in what contexts — verified by experienced practitioners and systematic study. Judgment is valid pramāṇa here in a way it is not elsewhere.
- Vyāpti: pattern-to-outcome relations ("in situations with characteristic X, approach Y reliably produces result Z").
- First principles: the goal structure (what are we trying to achieve and for whom?), the constraint structure (what are we bounded by?), and the failure modes (what causes things to go wrong?).
- Expert endpoint: can exercise judgment in novel situations; knows which patterns apply and which don't; can reason under time pressure and incomplete information; knows when to break a rule and why.

**Type 5 — Interpretive/Humanistic** (history, philosophy, literary theory, anthropology)
- Pramāṇa: primary sources + interpretive frameworks + coherence of argument. Multiple valid interpretations can coexist; the question is which is better-supported and more illuminating.
- Vyāpti: structural patterns within texts or historical processes — not universal laws, but tendencies that hold within specific contexts.
- First principles: the primary sources themselves and the methodological frameworks for reading them.
- Expert endpoint: can construct original interpretations; can critique existing ones; can see what a framework reveals and what it conceals; understands that all interpretation is perspectival.

---

## What "Expert-Level Thinking" Actually Means

This meta-prompt specifies the endpoint as a set of transferable intellectual virtues that characterize expertise across all five domain types:

1. **Calibrated uncertainty**: knowing what you know confidently, what you know provisionally, and what you genuinely don't know — and being able to say so clearly.
2. **Pattern recognition with scope awareness**: recognizing which known pattern a situation matches, *and* knowing the boundaries of that pattern — where it stops applying.
3. **Failure mode fluency**: knowing the characteristic ways things go wrong in this domain, and being able to spot early signs of those failure modes.
4. **First-principles recovery**: when no known pattern applies, being able to reason from foundational principles to a reasonable approach for the novel case.
5. **Source evaluation**: knowing which sources of knowledge are authoritative in this domain, which are contested, and which are unreliable — and why.
6. **Productive engagement with disagreement**: understanding why smart people in this domain disagree, what the crux of disagreement is, and what evidence or argument would resolve it.
7. **Inductive bias awareness**: knowing what your own frameworks assume, when those assumptions help, and when they distort — the ability to see the lens you're looking through.

A guide built by this meta-prompt should leave the reader able to demonstrate all seven of these for the domain in question.

---

## The Engagement/Conciseness Resolution

These are not opposites. The apparent conflict arises when *rhetorical decoration* is confused with *genuine engagement*. Real engagement comes from:

- **Stakes**: why does understanding this matter, specifically?
- **Surprise**: what does this domain reveal that contradicts naive expectation? Every part of the guide should contain at least one genuine surprise — a finding or connection that contradicts a common assumption.
- **Productive confusion**: encountering the problem before the solution, so the concept arrives as an answer to a felt question rather than an abstract definition.
- **Difficulty made visible**: showing that something is hard, and then showing how to handle the hardness — this is more engaging than pretending things are easy.
- **The reasoning, not just the conclusion**: watching a mind work through a problem is inherently engaging; announcing an answer is not.

None of these require extra words. They require that the writing model genuine inquiry rather than deliver packaged conclusions.

The rule for length: a section is the right length when removing any sentence weakens the reader's understanding. Not when a word count is satisfied.

---

## Threshold Concepts: Not All Concepts Are Equal

Some concepts are not just difficult — they are portals. Once understood, the reader cannot un-see them. Their entire prior understanding of the domain reorganizes around the threshold concept. Crossing it is irreversible and transformative.

Examples: Natural selection in biology. Opportunity cost in economics. The limit in calculus. Jurisdiction in law. Voice in literary theory.

Most guides treat all concepts as equivalent in pedagogical weight. They are not. Threshold concepts deserve completely different treatment: more preparation before (readying the reader for the reorganization that's coming), and explicit acknowledgment after ("notice that you now see [X] differently than you did before"). In domains where the threshold concept requires the reader not just to add knowledge but to change what kinds of things they think exist (an ontological shift), the guide must warn: "What you're about to encounter will not fit into your current understanding — because your current understanding needs to change, not just expand."

This meta-prompt requires threshold concepts to be identified in Phase 2 and treated structurally differently in Phase 3.

---

## Metacognitive Scaffolding: Teaching the Reader to Monitor Understanding

Expertise includes a second-order skill: knowing what you know, what you don't know, and how confident to be in the difference. This is metacognition — cognition about cognition — and it is trainable.

Most guides build first-order knowledge (understanding the domain) without building the metacognitive layer (knowing how well you understand it). The result is the Dunning-Kruger pattern: readers who have absorbed the vocabulary and can pattern-match to familiar problems believe they understand more deeply than they do. Their confidence is uncalibrated.

This meta-prompt addresses this with two mechanisms:

**Calibration probes.** At chapter boundaries, the reader rates their confidence before checking the expert answer, then compares. Over the course of the guide, this trains the reader to notice the gap between "I feel like I understand" and "I can apply this to a novel case." Research on expert calibration (Keren, 1991; Dunning & Kruger, 1999) shows this gap is systematic and correctable with practice.

**Self-explanation prompts.** The reader is asked to articulate *why* a principle holds — in their own words, not the guide's words. Research on the self-explanation effect (Chi et al., 1989) shows this doubles retention and transfer compared to re-reading, because it forces the reader to actively construct the reasoning chain rather than passively recognizing it.

These are not decorative. They are structural mechanisms for building the first expert virtue: calibrated uncertainty.

**v3.25 change:** Metacognitive checkpoints are scoped to **Part I (foundational) chapters only**, where miscalibration is most dangerous and the reader's self-model is least accurate. For Parts II–IV, the calibration function is carried forward via the Part-transition recalibration checks (which now include a calibration carry-forward based on the reader's Part I checkpoint pattern), and the self-explanation function is absorbed into the existing Transfer Tests. This reduces per-chapter overhead while preserving the developmental arc of calibration skill.

---

## Derivation Transparency: Ānvīkṣikī-Native Claim Verification

A guide built by an AI system faces a unique epistemic challenge: the reader cannot inspect the system's sources directly. Unlike a human author whose reputation, institutional affiliation, and citation practices provide indirect evidence of reliability, an AI system's claims arrive without provenance.

Naive approaches to this problem — such as having the AI self-report confidence levels ("HIGH / MEDIUM / LOW") — fail because language models are not Bayesian reasoners. They do not have calibrated access to their own epistemic uncertainty. A model can state a falsehood with the same fluency as a truth. Self-reported confidence is confidence theatre, not confidence.

The solution is **derivation transparency**: for every non-trivially-sourced claim, show the reasoning chain that produces it, using Ānvīkṣikī's own epistemic machinery. This makes the claim *tractable* (the reader can follow it), *structured* (it has a defined format), and *verifiable* (the reader can check each node).

The full derivation framework uses six components that the guide itself teaches:

1. **Pramāṇa basis** — What valid source of knowledge grounds each premise? Is it pratyakṣa (direct observation/data), anumāna (inference from established principles), śabda (authoritative testimony/citation), or upamāna (structural analogy)? This makes the knowledge *type* explicit.

2. **Vyāpti chain** — Which structural regularities of the domain connect the premises to the conclusion? Each inferential step maps to a named vyāpti from the guide's own architecture. If no vyāpti supports a step, the step is unsupported.

3. **Kārya-kāraṇa-bhāva** — Is each link in the chain causal (intervening on A changes B), structural (A and B are connected by domain architecture), or an empirical regularity (A and B co-occur but the mechanism is partial)? This determines how confident the conclusion can be.

4. **Graph position** — Where in the concept dependency DAG does this claim sit? What are its parent premises? This makes the claim's logical dependencies visible. If a parent is wrong, the claim falls.

5. **Hetvābhāsa check** — Which characteristic fallacies of the domain could produce this conclusion *invalidly*? Naming the specific reasoning error the derivation must avoid is a strong test of validity.

6. **Source grounding** — Which nodes of the derivation are grounded in the Reference Bank (verified against external sources in Stage 3) and which rely on unverified training knowledge? This is the one factual, binary signal: sourced or unsourced.

This mechanism is meta-circular by design: the reader, having learned pramāṇa, vyāpti, kārya-kāraṇa-bhāva, and hetvābhāsa from the guide, can verify the guide's own claims using the tools the guide taught them. The guide practices what it preaches.

**v3.25 change — Three-layer derivation system:** The full 6-component derivation is too heavy for both architecture planning and reader-facing prose. v3.25 splits the derivation into three layers:

- **Proof sketch** (Stage 2 architecture): A compact 5-line format capturing premises, inference mechanism (named vyāptis), fallacy risk, and source grounding. Used for architectural planning and registry tracking.
- **Reader-facing summary** (inline in guide chapters): A natural-language derivation that preserves every epistemic function — the reader can evaluate premises, check inference validity, learn error awareness, and assess source reliability — without typed notation or structural formalism.
- **Full derivation expansion** (on demand via Appendix F): The complete 6-component derivation, generated by a standalone prompt that takes the guide, architecture, and claim number as input. Recovers the full verification depth when needed.

This preserves the meta-circular verification property — the reader can still use the guide's tools to verify the guide's claims — while reducing per-claim token cost by approximately 60%.

Derivations are not required for every sentence — only for claims identified in the Derivation Registry (Stage 2, Step 2J) as non-obvious: claims that rest on multi-step inference, combine multiple vyāptis, or lack direct source grounding.

---

## Cross-Domain Transfer: Structural Isomorphisms as Depth Markers

One hallmark of deep understanding is the ability to see structural parallels between domains — to recognize that natural selection, market competition, and gradient descent are instances of the same abstract pattern (iterative selection under pressure), while also knowing precisely where the analogy breaks.

The reader calibration (Phase 1, Q2) identifies the reader's adjacent knowledge domains. The analogy pool uses this to make individual concepts more accessible. But analogies and structural isomorphisms are different:

- An **analogy** says: "Think of X as being *like* Y." It serves comprehension.
- An **isomorphism** says: "X and Y share the same abstract structure [Z]. Here is precisely where the structure holds and where it diverges." It serves *transfer* — the ability to apply structural insight from one domain to novel situations in another.

This meta-prompt adds a Cross-Domain Isomorphism Map (Stage 2, Step 2K) that systematically identifies where vyāptis in the guide's domain have structural twins in the reader's background domain, and where the correspondence breaks. The breakdown is as important as the match — it reveals what is *unique* to this domain that the reader's prior knowledge cannot predict.

---

## v3.0 Changes: The Staged Execution Model

### The Problem with Single-Pass Generation

v2.0 assumed the generating system could hold a complex architectural plan (Phase 2 outputs: vyāpti list, hetvābhāsa list, dependency map, threshold concepts, spaced returns, resolution ledger) in working memory across 10,000–20,000 words of output while simultaneously producing high-quality domain content and self-monitoring for structural compliance.

In practice, this produces a characteristic failure pattern: Part I executes faithfully against the architecture, compliance degrades through Parts II–III as architectural scaffolding fades from active context, and structural elements specified in Phase 2 (landscape acknowledgments, discrimination cases, spaced returns, decay markers) are partially or wholly omitted.

### The Solution: Verified Staged Execution

v3.0 decomposes the meta-prompt into **seven execution stages**, each producing a verifiable output. Each stage's output becomes explicit context for the next stage. No stage begins until the previous stage's output has been produced and (ideally) verified.

This mirrors Ānvīkṣikī's own method: examine each step carefully, verify it holds, then proceed.

```
STAGE 1: Phase 0 (Domain Audit) + Phase 1 (Reader Calibration)
   → Output: Domain classification + Failure ontology + Calibration profile
   → Verify before proceeding

STAGE 2: Phase 2 (Knowledge Architecture)
   → Output: Vyāpti list + Hetvābhāsa list + Dependency map + 
             Threshold concepts + Spaced return plan + Resolution ledger +
             Chapter sequence + Structure assignments
   → Verify before proceeding

STAGE 3: Phase 2.5 (Research Gate)
   → Input: Full Stage 2 architecture (chapter sequence, vyāptis, 
            hetvābhāsas, threshold concepts)
   → Action: Web search to gather real sources for each chapter's 
             core concept, each vyāpti, each hetvābhāsa, and each 
             threshold concept
   → Output: Reference Bank organized by chapter, with annotated 
             sources and sourcing gap flags
   → Verify before proceeding

STAGE 4: Phase 3a (Guide Opening + Part I: Foundations)
   → Input: Full Stage 1 + Stage 2 outputs restated as header + 
            Stage 3 Reference Bank
   → Output: Opening + Foundational chapters (with references 
             drawn from the Reference Bank)
   → Run inline quality assertions before proceeding

STAGE 5: Phase 3b (Part II: Intermediate Synthesis + Part III: Advanced Integration)
   → Input: Stage 2 architecture + Stage 3 Reference Bank + 
            Stage 4 output summary 
            (chapter titles, core insights, vyāptis covered) + 
            recalibration note
   → Output: Synthesis + Advanced chapters
   → Run inline quality assertions before proceeding

STAGE 6: Phase 3c (Part IV: Frontier + Part V: Framework)
   → Input: Stage 2 architecture + Stage 3 Reference Bank + 
            resolution ledger status + 
            cumulative structural element checklist
   → Output: Frontier section + Expert's Framework chapter
   → Run inline quality assertions

STAGE 7: Phase 4 (Quality Verification + Assembly)
   → Input: Full guide assembled from Stages 4–6
   → Output: Verified final guide with all gaps identified and filled
```

**If single-pass generation is unavoidable** (e.g., limited to one prompt), the minimum viable guide specification (Section below) defines which elements are non-negotiable.

### Recalibration at Part Transitions

Reader calibration is not a one-time input. The reader's relationship to the material changes as they progress. At the boundary between Part I and Part II, and again between Part II and Part III, the generating system must briefly recalibrate:

```
RECALIBRATION CHECK (at each Part transition):

The reader who began at [calibration level] has now absorbed 
[N foundational concepts]. Their analogy needs may have shifted:

- Part I analogies drew from: [reader's original background]
- Part II analogies should additionally draw from: [concepts 
  now available from Part I that can serve as analogies for 
  more advanced material]
- New skip markers: Readers who already understood [Part I 
  concepts] can now additionally skip [specific sections]
```

This prevents the common failure where a guide calibrated for a beginner in Chapter 1 still writes at beginner level in Chapter 8.

---

## Minimum Viable Guide Specification

If generation constraints (context window, token limits, single-pass execution) prevent the full guide from being produced, these are the non-negotiable elements, in priority order:

**TIER 1 — Must be present for the guide to have value:**
1. Domain classification with correct pramāṇa (Phase 0)
2. Reader calibration with analogy anchor (Phase 1)
3. Vyāpti list with causal classification (Phase 2A) — may be abbreviated to 5
4. Hetvābhāsa list (Phase 2B) — may be abbreviated to 3
5. Part I: At least 3 foundational chapters using Structure A
6. Part V: The Inquiry Protocol and Structural Regularities Quick-Reference
7. Derivation proof sketches: minimum 1 per Part (3 total) — may use reader-facing summary format only

**TIER 2 — Should be present for the guide to build a framework:**
8. Threshold concept identification and treatment (at least 1)
9. Part III: Failure Mode Catalogue (at least 3 modes using Structure C)
10. Part IV: Frontier section with epistemic status markers
11. Transfer tests for all foundational chapters
12. Framework anti-patterns: minimum 3 in Part III
13. Metacognitive checkpoints in Part I foundational chapters only
14. Framework stress-tests: minimum 2 in Part III

**TIER 3 — Required for full structural compliance:**
15. All landscape acknowledgments
16. All discrimination cases
17. Full spaced return plan executed
18. All decay markers on condition-dependent claims
19. Resolution ledger fully resolved
20. Part II: Full synthesis chapters
21. Error Museum
22. Compression exercise
23. All tacit knowledge markers (minimum 1 per Part for Craft domains)
24. Cross-domain isomorphism blocks: all entries from map
25. Composability anchors: sequel hooks + parallel perspectives in Part V Section VII
26. Collaborative Learning Appendix (collected discussion/teaching prompts for all chapters)

If the guide must be shortened, cut from Tier 3 upward. Never cut Tier 1 elements.

---

## Composability: Guides as Nodes in a Knowledge Graph

No guide exists in isolation. Every domain borders other domains; every guide covers a finite scope. This meta-prompt builds composability into the guide's structure through two mechanisms:

**Sequel hooks.** The guide explicitly names its exit boundary — what the reader has mastered and what lies beyond. It identifies 1–2 follow-up directions with specific entry prerequisites, so a reader (or a future guide) knows exactly where to begin the next ascent.

**Parallel guide references.** The same topic can often be classified under multiple domain types. Machine learning, for instance, is Type 1 (Formal) when studying learning theory, Type 2 (Mechanistic) when studying optimization, Type 3 (Probabilistic) when studying generalization, and Type 4 (Craft) when studying ML engineering. A parallel guide reference tells the reader: "This guide treated [topic] as [Type X]. For a complementary perspective, a guide built as [Type Y] would emphasize [different aspects]." This models the seventh expert virtue: inductive bias awareness — seeing the lens you're looking through.

Composability anchors are architectural decisions, not afterthoughts. They are planned in Stage 2 (Step 2L) and rendered in Part V of the guide.

---

## Framework Anti-Patterns: Proactive Failure Detection

The v3.1 meta-prompt includes a "Where the Framework Breaks Down" section in Part III. But this is *reactive* — it tells the reader about failure conditions in the abstract. Expert practitioners don't just know that their frameworks can fail; they recognize *specific behavioral signatures* that indicate a framework is actively misleading them.

Anti-patterns are these signatures: "If you find yourself doing [specific behavior], the framework is distorting your view. The likely cause is [specific inductive bias]. The corrective is [specific action]." They are the metacognitive equivalent of code smells — they don't prove something is wrong, but they strongly suggest it.

Framework stress-tests go further: they are scenarios *designed to make the framework fail*, so the reader experiences the limit firsthand rather than being told about it. This is the difference between knowing a bridge has a weight limit (abstract) and feeling the bridge flex underfoot (experiential).

Both are required in Part III of the guide.

---

## Collaborative and Social Learning: Completing the Epistemic Loop

The guide is designed for individual study, but understanding is partly social. Three mechanisms that individual reading cannot replicate:

**Discussion crystallizes understanding.** Articulating a position to someone who pushes back forces you to distinguish between "I've absorbed this" and "I can defend this." The guide includes discussion prompts — not generic "what do you think?" questions but structured debates that exercise the Vāda mode (inquiry for truth) the guide teaches.

**Teaching reveals gaps.** Asking a reader to explain a concept to someone who hasn't read the guide is the highest-fidelity test of genuine understanding. Where the reader stumbles is exactly where their knowledge is receptive (they can recognize it) but not yet generative (they can produce it). This maps directly to the Tacit Knowledge Transmission Block's Receptive→Generative bridge.

**Peer calibration.** Comparing your transfer test answers and confidence ratings with peers reveals systematic biases that self-assessment alone cannot detect. The research on peer instruction (Mazur, 1997) shows that peer discussion after individual attempt — specifically on conceptual questions where students disagree — produces larger learning gains than lecture.

**v3.25 change:** Collaborative hooks are collected in a dedicated **Collaborative Learning Appendix** at the end of the guide rather than embedded per-chapter. This keeps the main guide focused for solo readers while giving study groups a single reference point for all discussion and teaching exercises, indexed by chapter. Discussion prompts include both-sides structure with explicit crux; teaching prompts include predicted stumble points.

---
---

# PART TWO: THE META-PROMPT

---

```
╔══════════════════════════════════════════════════════════════════════════╗
║        THE ĀNVĪKṢIKĪ INSTRUCTIONAL DESIGN META-PROMPT v3.25             ║
║        For: AI Systems Generating Long-Form Learning Guides             ║
║        Goal: Framework of Thinking, First Principles to Expert Mastery  ║
║        Execution Model: Staged with Verified Handoffs                   ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## INSTRUCTIONS FOR THE AI SYSTEM

You are about to generate a comprehensive long-form learning guide on [TOPIC]. This meta-prompt uses a **staged execution model**. Complete each stage fully and produce its required output before proceeding to the next. Do not skip stages. Do not merge stages. The quality of the guide depends entirely on the quality of the upstream thinking — and on the upstream outputs remaining visible and available as you proceed downstream.

### EXECUTION MODEL

**If you can execute in multiple turns** (recommended): Complete each stage as a separate response. Present your output for verification. Proceed only when confirmed.

**If you must execute in a single pass**: Complete Stages 1–3 first (Domain Audit, Architecture, and Research Gate) and reproduce their outputs verbatim as a reference header before beginning Stage 4. At minimum, deliver all Tier 1 elements from the Minimum Viable Guide Specification.

### TERMINOLOGY PROTOCOL

The Ānvīkṣikī terms (pramāṇa, vyāpti, hetvābhāsa, pañcāvayava, kārya-kāraṇa-bhāva, vāda, jalpa) are your structural anchors — high-specificity reference labels for the structural elements of the guide. Use them in your Stage 1–2 reasoning and as internal markers during generation. In the reader-facing prose of the guide (Stage 4+), translate to domain-appropriate plain language. The Sanskrit terms anchor your structural fidelity; the plain language serves the reader.

Exception: If the guide is about philosophy, Indian intellectual traditions, or a domain where the reader would benefit from the methodological vocabulary, use the terms with definitions in reader-facing prose.

---

# ═══════════════════════════════════════════
# STAGE 1: DOMAIN AUDIT + READER CALIBRATION
# ═══════════════════════════════════════════

## STEP 0A: SCOPE CALIBRATION SEARCH
### (Light Pre-Search — Calibration, Not Discovery)

Before classifying the domain, perform 3–5 targeted web searches to calibrate the LLM's internal model of the domain against current reality. This is NOT discovery research — it is a quick check for blind spots, recent shifts, or structural changes in the domain that may have occurred since training.

**Search targets:**
1. "[TOPIC] current curriculum / body of knowledge" — to verify the domain landscape hasn't reorganized
2. "[TOPIC] recent changes / emerging areas [current year]" — to catch structural shifts
3. "[TOPIC] + [reader's specific context]" — to surface domain-specific dynamics the LLM might underweight (e.g., "AI creative agency business model" for a reader building one)

**What to produce:**

```
LANDSCAPE CALIBRATION NOTE:

Domain landscape confirmed: [Areas where LLM internal model 
  aligns with current search results]

Blind spots caught: [Areas where search revealed something 
  the LLM's internal model underweights or misses entirely. 
  If none, state "none identified."]

Emerging areas: [Topics that appear in current results but 
  may not be well-represented in training data]

Context-specific dynamics: [Anything surfaced by the 
  reader-context search that should inform domain 
  classification or calibration]

Impact on classification: [Will any of the above change 
  which domain type is selected, or how the failure ontology 
  is framed? If yes, note how. If no, state "Classification 
  proceeds from internal model — no adjustment needed."]
```

**Critical framing:** This search informs classification — it does not replace the LLM's structural reasoning about the domain. If search results suggest a different classification than the LLM's integrated knowledge, note the tension and let the user decide. Do not auto-override architectural reasoning with search results.

---

## PHASE 0: DOMAIN AUDIT
### (The Pramāṇa Question — How Do We Know Things Here?)

Before anything else, classify [TOPIC] by domain type. This classification controls everything that follows.

**Read each type carefully and select the one that best fits [TOPIC]. If [TOPIC] spans multiple types, identify the primary type and note secondary types.**

---

**TYPE 1 — FORMAL/AXIOMATIC**
Applies to: Mathematics, formal logic, theoretical computer science, formal linguistics, proof-based physics.
Signature: Truth is established by proof from accepted axioms. A claim is either proven or not. Counterexamples definitively refute.
What "first principles" means here: The axiom system. Everything else is derived.
How concepts relate: Strict logical dependency. B cannot be true unless A is established.
Expert endpoint: Can prove new results, construct counterexamples, identify what additional axioms would be needed.

**TYPE 2 — EMPIRICAL/MECHANISTIC**
Applies to: Physics, chemistry, classical engineering, cell biology, biochemistry.
Signature: Truth is established by experimental observation + mechanistic explanation. Mechanism without observation is speculation; observation without mechanism is incomplete.
What "first principles" means here: Fundamental forces, conservation laws, or established mechanisms.
How concepts relate: Causal chains and mechanisms. Understanding A helps explain B because A causes B.
Expert endpoint: Can predict experimental outcomes, design experiments, explain why observations occur.

**TYPE 3 — EMPIRICAL/PROBABILISTIC**
Applies to: Clinical medicine (evidence-based), epidemiology, ecology, psychology, macroeconomics.
Signature: Truth is probabilistic. Evidence has strength. Single studies are weak; meta-analyses with consistent replication are stronger; mechanisms add further confidence.
What "first principles" means here: Causal mechanisms (partial) + statistical framework for reasoning about evidence.
How concepts relate: Overlapping causal networks. Multiple factors interact. Scope conditions matter enormously.
Expert endpoint: Can evaluate evidence quality, reason about confounders and effect sizes, know what would change their position.

**TYPE 4 — PRACTICAL/CRAFT**
Applies to: Law, clinical medicine (as practice), business strategy, engineering design, architecture, surgery, teaching.
Signature: Truth is pragmatic — what reliably works in what contexts, established by practitioner experience and systematic study. Judgment is a valid cognitive tool here.
What "first principles" means here: The goal structure (what are we trying to achieve?), constraint structure (what limits us?), and failure mode catalogue (what makes things go wrong?).
How concepts relate: Pattern-to-outcome relationships. Situation X calls for approach Y because of mechanism Z.
Expert endpoint: Can exercise judgment in novel situations; knows which patterns apply and their limits; can reason well under time pressure and incomplete information.

**TYPE 5 — INTERPRETIVE/HUMANISTIC**
Applies to: History, philosophy, literary criticism, anthropology, cultural studies, theology.
Signature: Multiple valid interpretations coexist. Arguments are evaluated by their coherence, their fidelity to primary sources, and their illuminating power. "Proof" is not the right concept here.
What "first principles" means here: Primary sources and the methodological frameworks through which we read them.
How concepts relate: Frameworks illuminate different aspects of the same phenomena. Understanding one framework makes others legible by contrast.
Expert endpoint: Can construct and defend original interpretations; can critique existing ones fairly; understands what any given framework reveals and what it necessarily conceals.

---

**→ DOMAIN CLASSIFICATION OUTPUT:**

State:
- Primary domain type: [TYPE X]
- Secondary domain types (if any): [TYPE Y, reason why]
- Implication for "first principles": [What this means concretely for this topic]
- Implication for "expert endpoint": [What the reader will be able to do upon completion]
- Implication for valid knowledge claims: [What counts as pramāṇa in this specific domain — be concrete, not generic]

**→ FAILURE ONTOLOGY OUTPUT:**

Define explicitly for this domain:
- What counts as failure: Is failure binary (works/doesn't) or graded (degree of fit)? Is failure objective (measurable against a standard) or perspectival (depends on who's evaluating)? Is failure reversible or irreversible?
- Failure relative to what: What is the benchmark — a goal, a prediction, a prior state, a competing alternative, a theoretical expectation? Whose benchmark — the practitioner's, the client's, the field's, the public's?
- Failure on what timescale: When can success at T1 become failure at T2, or vice versa?
- Failure vs. insufficient information: When can you conclude something has failed vs. you haven't waited long enough or measured the right thing?

Every subsequent claim in the guide about something "working," "failing," "breaking," or "underperforming" must be traceable to this failure ontology.

---

## PHASE 1: READER CALIBRATION
### (Calibration That Actually Changes the Guide)

Determine the reader's starting level. This is not cosmetic — it changes the guide's structure, not just its tone. Calibration must produce visible artifacts that constrain the guide.

Ask the following and use the answers to determine the starting chapter:

**Q1: Prior exposure to [TOPIC]?**
- None — begin at conceptual ground zero; no jargon without definition; no assumed background
- Casual (read articles, heard of it) — can use some field vocabulary but must be explained; skip only the most elementary basics
- Undergraduate formal study — can assume foundational concepts; begin at intermediate synthesis
- Graduate/practitioner — can assume most concepts; focus on advanced integration and expert frameworks
- Active researcher — focus on frontier problems and the framework-of-thinking chapter only

**Q2: Adjacent knowledge the reader has?** (Use this to select analogies and connection points)
Examples: biology background, programming experience, legal training, business experience, mathematical sophistication.
The guide must use analogies drawn from what the reader already knows — not generic analogies.

**Q3: Primary learning goal?**
- Build intuitive understanding → weight worked examples and analogies heavily
- Prepare to read primary literature → weight technical precision and field-specific vocabulary
- Apply to [specific problem] → weight practical/craft reasoning and failure modes
- Teach this subject → weight conceptual clarity and common student misconceptions
- Understand the expert's mindset → weight the Framework chapter heavily

**Q4: Operating context?** (Optional — primarily relevant for Type 4 Craft and Type 3 Probabilistic domains)
- Jurisdiction, regulatory environment, or institutional type (e.g., EU healthcare, US fintech, Indian public sector)
- Cultural or organizational context that shapes how this domain's knowledge applies (e.g., startup vs. enterprise, academic vs. clinical)
- If not specified or not applicable, state: "No context-specific adaptation needed — guide addresses the domain generally."
- When specified, this constrains examples, failure modes, and practical recommendations to the reader's operating reality.

**→ CALIBRATION OUTPUT:**

State:
- Starting chapter (based on prior exposure): [Chapter N]
- Analogy pool (domains to draw from): [List]
- Depth emphasis (based on goal): [Technical precision / Intuitive understanding / Practical application]
- What to abbreviate: [Concepts the reader already knows well]
- What to expand: [Areas directly relevant to the reader's goal]
- Operating context (if specified): [Context → specific constraints on examples, failure modes, and recommendations]

**→ CALIBRATION ARTIFACTS (must appear visibly in the guide):**

1. ANALOGY ANCHOR: State explicitly in the opening: "This guide draws analogies from [reader's domains]. If you have a background in [X], you'll recognize parallels."
2. SKIP MARKERS: For readers above beginner level, mark sections as skippable: "If you already understand [concept], skip to [section]. You can safely skip if you can [specific test]."
3. DEPTH MODULATION: For each major section, include a brief "Going Deeper" note that either expands (for readers who need more) or points to external resources (for readers who want more than the guide provides).

**→ TACIT KNOWLEDGE DENSITY ESTIMATE:**

Estimate the tacit knowledge density for [TOPIC]. **This applies to ALL domain types**, not just Craft and Interpretive — even Formal domains have tacit knowledge (proof strategy, mathematical taste, design intuition) that benefits from structured treatment.

**Density levels and required vehicles:**

**Low** (mostly articulable — typical for Type 1, Type 2):
- Minimum: 1 tacit knowledge block per Part
- Required vehicles: Case study only
- Optional: Experiential simulation if applicable

**Medium** (significant judgment component — typical for Type 3, and some Type 1/2):
- Minimum: 1 tacit knowledge block per 2 chapters
- Required vehicles: Case study + Experiential simulation
- Optional: High-contrast debate if contested judgment areas exist

**High** (heavily judgment-dependent, embodied, or perceptual — typical for Type 4, Type 5):
- Minimum: 1 tacit knowledge block per chapter, plus an explicit "Limits of Propositional Instruction" section in Part III
- Required vehicles: ALL four — Case study + Experiential simulation + High-contrast debate + Podcast/interview references
- These domains have the most to gain from enriched tacit knowledge treatment

**Density estimate output:**
```
TACIT KNOWLEDGE DENSITY: [Low / Medium / High]
Justification: [Why this level — what makes the tacit 
  knowledge in this domain more or less articulable?]
Minimum block count: [number]
Required vehicles per block: [list]
Specific tacit skills anticipated: [list 3–5 tacit skills 
  that the guide will need to address — these become the 
  search targets for Stage 3 Step 3G]
```

This estimate determines both the minimum number of tacit knowledge blocks and the vehicles each block must contain.

---

═══════════════════════════════════════════
⛔ STAGE 1 GATE — HARD STOP
═══════════════════════════════════════════

SELF-AUDIT before stopping:
□ Landscape Calibration Note produced (Step 0A)?
□ Domain classification with type + justification
□ Pramāṇa specified concretely (not generically)
□ Failure ontology (all 4 dimensions)
□ Reader calibration (starting chapter, analogy pool, depth, 
  abbreviation/expansion plan)
□ Operating context (Q4) addressed? (specified or explicitly 
  marked as not applicable)
□ Calibration artifacts (analogy anchor, skip markers, 
  depth modulation)
□ Tacit knowledge density estimate with:
  - Density level + justification
  - Minimum block count
  - Required vehicles per block
  - Anticipated tacit skills list (for Stage 3 search)

Fix any gaps. Then STOP and present outputs using the 
format from Rule 1. DO NOT begin Stage 2.

---

# ═══════════════════════════════════════════
# STAGE 2: KNOWLEDGE ARCHITECTURE
# ═══════════════════════════════════════════

## PHASE 2: KNOWLEDGE ARCHITECTURE
### (The Vyāpti Map — Structural Regularities of the Domain)

This phase produces the backbone of the guide. It is the most important phase.

### Step 2A: Identify the Vyāptis

Vyāptis are the invariable structural regularities of the domain — the relations that hold universally (or near-universally with defined exceptions). These are not merely important facts. They are the principles that allow an expert to reason about cases they've never seen.

For each domain type, vyāptis take different forms:
- Type 1 (Formal): Theorems that hold for all instances of a class. If P then Q, always.
- Type 2 (Mechanistic): Conservation laws, mechanistic necessities. Energy is conserved; concentration gradients drive diffusion.
- Type 3 (Probabilistic): Robust effect-cause relations with explicit scope conditions and known moderators.
- Type 4 (Craft): If-situation-then-approach patterns with known scope limits.
- Type 5 (Interpretive): Cross-cutting structural patterns in texts, historical processes, or social phenomena.

**Identify 5–10 vyāptis for [TOPIC].** These become the spine of the guide. Every concept introduced should connect back to at least one vyāpti.

**Classify each vyāpti by causal status (kārya-kāraṇa-bhāva):**

Format:
```
VYĀPTI 1: [Name]
Statement: [Precise statement of the invariable relation]
Causal status:
  ☐ CAUSAL — Intervening on A reliably changes B. 
    [State the intervention and predicted effect]
  ☐ STRUCTURAL — A and B are connected by domain architecture, 
    not direct causation. [State the structural link]
  ☐ EMPIRICAL REGULARITY — A and B co-occur reliably, but 
    the causal pathway is complex or partially understood. 
    [State what's known and unknown about the mechanism]
Domain type form: [How this manifests as Type 1/2/3/4/5 knowledge]
Scope conditions: [Where this holds; where it breaks down]
Why it matters: [What becomes possible once you grasp this]
Chapter it anchors: [Which chapter in the guide builds to this]
```

Use the strongest vyāptis (causal) as the primary spine of the guide. Use structural vyāptis as secondary support. Present empirical regularities with explicit caveats about the limits of the evidence.

### Step 2B: Identify the Hetvābhāsas (Characteristic Fallacies)

Every domain has reasoning errors that are so common they deserve names. These are not random mistakes — they are attractive-looking inferences that seem valid but aren't. Experts recognize them immediately; beginners fall into them repeatedly.

**Identify 5–8 hetvābhāsas for [TOPIC].** These will be introduced at the point in the guide where the reader is most at risk of falling into them — not bundled at the end.

Format:
```
HETVĀBHĀSA 1: [Name — memorable, field-appropriate]
The fallacy: [What the invalid inference looks like]
Why it's attractive: [What makes it seem valid]
Why it's wrong: [The precise error in reasoning]
Counter-example: [A case where following this reasoning 
  clearly fails]
Where in the guide to introduce it: [Chapter/concept where 
  the reader is at maximum risk]
```

### Step 2C: Map Concept Dependencies

List all major concepts the guide must cover. Then map their dependencies.

**Dependency notation:**
- A → B means: A must be understood before B can be introduced
- A ⟺ B means: A and B are mutually illuminating — introduce them together or in close proximity
- A | B means: A and B are siblings at the same level — parallel, neither prerequisite to the other
- [A, B] → C means: C requires both A and B
- A ≈ B means: A and B are easily confused — when introducing either, construct a DISCRIMINATION CASE

**Handle circular dependencies explicitly:**
When A → B and B → A, you have genuine circularity. The solution is not to pretend it away but to:
1. Introduce A in a simplified form ("A₀") adequate to introduce B
2. Introduce B using A₀
3. Return to A in its full form ("A₁") now that B is available
4. Make this explicitly visible to the reader: "We introduced a simplified version of A earlier. Now that you understand B, we can complete A."

**Granularity rule:** A concept is ONE concept (not two or five) if:
- It has exactly one core insight
- Removing it from the map would leave exactly one gap
- A reader who understands it can be expected to derive its corollaries

If a "concept" has multiple core insights, split it. If a "concept" is a corollary of another, absorb it.

### Step 2D: Identify Threshold Concepts

Of the concepts mapped in Step 2C, identify 1–3 that are THRESHOLD CONCEPTS — concepts that, once understood, irreversibly reorganize the reader's understanding of the domain.

Markers of a threshold concept:
- Understanding it changes how you see PRIOR concepts, not just subsequent ones
- Before/after understanding it, the same facts look different
- Students commonly resist it because it requires letting go of a comfortable prior framework
- In the strongest cases, the reader must change what kinds of things they think exist (ontological shift)

For each threshold concept:
```
THRESHOLD CONCEPT: [Name]
What reorganizes: [Which prior concepts now look different]
What the reader currently believes: [The pre-threshold understanding]
What replaces it: [The post-threshold understanding]
Why resistance is expected: [What makes the old view comfortable]
Chapter placement: [Where in the guide — allocate 1.5x normal space]
```

### Step 2E: Plan Spaced Returns

**For each foundational concept** (every concept in Part I), identify one point in Part II, III, or IV where it reappears in a deeper or expanded form. The reader's understanding of early concepts should deepen as they progress, not remain frozen at its first-encounter level.

**This means: if Part I has N chapters, produce N spaced return entries.** No foundational concept may go without a return.

```
SPACED RETURN: [Concept from Chapter N]
Returns in: [Chapter M]
Simple form (Chapter N): [How the concept is first understood]
Expanded form (Chapter M): [What the reader now sees that 
  they couldn't before]
Signal text: [The exact sentence that will appear in 
  Chapter M to mark this return]
```

### Step 2F: Initialize the Resolution Ledger

Identify questions that will be raised early in the guide and resolved later. Track each one explicitly. By the guide's end, every entry must be either resolved or explicitly marked as an open question in Part IV (Frontier).

**Minimum: identify at least 3 resolution entries.** Domains where concepts interlock deeply should have more.

```
RESOLUTION LEDGER:
Question 1: [Question raised in Chapter X] → Resolved in [Chapter Y]
Question 2: [Question raised in Chapter X] → Resolved in [Chapter Y]
Question 3: [Question raised in Chapter X] → Marked OPEN in Part IV
```

### Step 2G: Assign Chapter Structures

**NEW IN v3.0** — For each chapter in the planned sequence, assign a structure using the decision table below. Do not leave structure selection to generation-time judgment.

**STRUCTURE DECISION TABLE:**

| Chapter characteristic | Assign structure |
|---|---|
| Introduces a single foundational concept from first principles | **A: Pañcāvayava** |
| Shows how 2+ previously established concepts converge into a new capability | **B: Convergence** |
| Teaches failure diagnosis, troubleshooting, or "what goes wrong" | **C: Diagnosis** |
| Addresses a genuinely contested area where smart people disagree | **D: Debate (Vāda)** |
| Teaches through a specific case where tacit knowledge is central | **E: Narrative** |

**Minimum structure diversity requirement:** The guide must use at least 3 different structures. If all chapters are Structure A, the guide lacks synthesis and diagnostic content.

**Required structures by domain type:**

| Domain Type | Must include |
|---|---|
| Type 1 (Formal) | At least 1× Structure A, 1× Structure B |
| Type 2 (Mechanistic) | At least 1× Structure A, 1× Structure C |
| Type 3 (Probabilistic) | At least 1× Structure A, 1× Structure D |
| Type 4 (Craft) | At least 1× Structure A, 1× Structure C, 1× Structure D or E |
| Type 5 (Interpretive) | At least 1× Structure A, 1× Structure D, 1× Structure E |

### Step 2H: Identify Confusion-Pairs and Landscape Points

**Confusion-pairs** (A ≈ B from Step 2C): For each pair, note the chapter where the discrimination case must appear.

**Landscape points**: Identify every branching point where sibling concepts (A | B) exist at the same level. Each requires a landscape acknowledgment before diving into the first sibling. **Count and list these explicitly.**

```
CONFUSION-PAIRS:
Pair 1: [Concept A] ≈ [Concept B] → Discrimination case in Chapter [N]
Pair 2: ...

LANDSCAPE POINTS:
Branch 1: [Concept A] | [Concept B] | [Concept C] at [position in sequence]
  → Landscape acknowledgment before Chapter [N]
Branch 2: ...
```

### Step 2I: Identify Condition-Dependent Claims

**NEW IN v3.0** — Before writing the guide, identify claims that are likely to be condition-dependent (true now but subject to change). Each must receive a decay marker in the guide.

```
DECAY MARKER REGISTRY:
Claim 1: [Claim] — Depends on [condition] — Check [verification method]
Claim 2: ...
```

**Minimum: 3 decay markers for any domain. More for fast-changing domains (technology, policy, markets).**

### Step 2J: Derivation Registry

**NEW IN v3.2, REVISED IN v3.25** — Identify claims in the planned guide that are non-obvious: they rest on multi-step inference, combine multiple vyāptis, or lack direct source grounding. These claims require explicit derivation proof sketches in the architecture and reader-facing derivation summaries in the guide text.

For each chapter, identify 1–3 claims that meet at least one criterion:
- The claim requires combining 2+ vyāptis or concepts from different chapters
- The claim is not directly stated by any single source in the Reference Bank
- The claim involves causal inference that could be confused with correlation
- The claim's validity depends on scope conditions that may not be obvious

For each, pre-write the derivation proof sketch:

```
DERIVATION ENTRY [N]: [Claim statement]
Chapter: [Where this claim appears]
Proof sketch:
  From: [Premise 1 — one line] + [Premise 2 — one line]
  Via: [Vyāpti name(s) that carry the inference]
  Therefore: [Conclusion — one line]
  Risk: [Named hetvābhāsa] — avoided because: [one line]
  Grounding: [Sourced / Partially sourced / Unsourced]
```

The proof sketch captures premises, inference mechanism, fallacy risk, and source status compactly. Full 6-component derivations (with typed pramāṇas, explicit graph positions, and step-by-step vyāpti chains) can be generated on demand using the Derivation Expansion Prompt (Appendix F).

**Minimum: 1 derivation entry per Part (3 total). More for domains where multi-step inference is central (Types 1, 2, 3).**

### Step 2K: Cross-Domain Isomorphism Map

**NEW IN v3.2** — Using the analogy pool from Phase 1 (Q2) and the vyāpti list from Step 2A, identify structural correspondences between the guide's domain and the reader's background domain(s).

For each vyāpti, ask: Does this structural regularity have a twin in the reader's background domain? If yes, map the correspondence and its limits.

```
ISOMORPHISM [N]:
This domain's vyāpti: [Name — from Step 2A]
Reader's domain concept: [Corresponding concept from analogy pool]
Abstract shared structure: [What both instantiate]
Where the correspondence holds: [What transfers]
Where it breaks: [What is unique to this domain — and why]
What the breakdown teaches: [What the reader's prior knowledge 
  cannot predict about this domain]
Chapter placement: [Where to introduce this isomorphism]
```

**Minimum: 3 isomorphism entries (or 1 per Part), provided the reader has identified adjacent knowledge in Q2. If no adjacent knowledge is specified, note: "No cross-domain isomorphisms mapped — reader did not identify adjacent domains."**

### Step 2L: Composability Anchors

**NEW IN v3.2** — Define the guide's position in the broader knowledge graph: what it presumes the reader already knows, what it certifies, and where it points next.

```
COMPOSABILITY ANCHORS:

ENTRY PREREQUISITES:
  What the guide assumes the reader can do before Chapter 1:
  - [Prerequisite 1 — with a test: "You should be able to [X]"]
  - [Prerequisite 2]

EXIT COMPETENCIES:
  What the reader can do after completing the guide:
  - [Competency 1 — mapped to specific chapters]
  - [Competency 2]
  - [Competency 3]

SEQUEL DIRECTIONS (1–2):
  Direction 1: [Advanced subtopic]
    — Entry point: [Which exit competencies are prerequisite]
    — What this follow-up guide would cover: [scope]
    — Suggested domain type for the sequel: [Type X]
  Direction 2: [Different advanced subtopic]
    — [Same format]

PARALLEL PERSPECTIVES (1–2):
  Perspective 1: [Same topic, different domain type]
    — This guide treats [TOPIC] as [Type X]. A parallel guide 
      as [Type Y] would emphasize [different aspects].
    — What the reader gains from the alternate lens: [specific insight]
  Perspective 2: [Same format, if applicable]
```

---

**→ ARCHITECTURE OUTPUT:**

Produce:
1. The Vyāpti List (5–10 invariable relations, fully formatted with causal classification)
2. The Hetvābhāsa List (5–8 fallacies, fully formatted)
3. The Concept Dependency Map (DAG with circular dependency resolutions and ≈ confusion-pairs noted)
4. The Threshold Concept List (1–3, fully formatted)
5. The Spaced Return Plan (one entry per foundational concept, with signal text)
6. The Resolution Ledger (initialized, minimum 3 entries)
7. The Chapter Sequence with structure assignments (from Step 2G decision table)
8. The Confusion-Pair and Landscape Point registry (from Step 2H)
9. The Decay Marker Registry (from Step 2I)
10. The Derivation Registry (from Step 2J)
11. The Cross-Domain Isomorphism Map (from Step 2K)
12. The Composability Anchors (from Step 2L)

---

═══════════════════════════════════════════
⛔ STAGE 2 GATE — HARD STOP (CRITICAL GATE)
═══════════════════════════════════════════

SELF-AUDIT — Count every element:
□ Vyāptis: [count] — required: 5–10. List names.
□ Each vyāpti has causal classification? [yes/no]
□ Hetvābhāsas: [count] — required: 5–8. List names.
□ Each has all 5 fields? [yes/no]
□ Dependency map: produced? Circular deps resolved? [yes/no]
□ Threshold concepts: [count] — required: 1–3
□ Spaced returns: [count] — must equal foundational chapter 
  count [N]. Each has signal text? [yes/no]
□ Resolution ledger: [count] entries — required: min 3. 
  At least 1 OPEN? [yes/no]
□ Chapter sequence with structures: produced? 
  Structures used: [list] — min 3 different? [yes/no]
  Domain-required structures present? [yes/no]
□ Confusion-pair registry: [count] pairs assigned? [yes/no]
□ Landscape point registry: [count] points assigned? [yes/no]
□ Decay markers: [count] — required: min 3
□ Derivation registry: [count] entries — required: min 3 
  (1 per Part). Each has proof sketch (premises + via + risk + grounding)? [yes/no]
□ Cross-domain isomorphism map: [count] entries — required: 
  min 3 (if reader specified adjacent knowledge). 
  Each has breakdown + what breakdown teaches? [yes/no]
□ Composability anchors: produced? Entry prerequisites, exit 
  competencies, sequel directions, parallel perspectives? [yes/no]

Fix ANY gaps found. Then STOP and present ALL 12 architecture 
outputs using the format from Rule 1. Include the element 
count verification in your gate message.

Tell the user: "The architecture above controls everything 
that follows. Changes here are cheap; changes after 
generation are expensive. Please review carefully."

DO NOT begin writing guide prose. DO NOT draft the opening. 
DO NOT preview any chapters.

---

# ═══════════════════════════════════════════
# STAGE 3: RESEARCH GATE
# ═══════════════════════════════════════════

## PHASE 2.5: SOURCE RESEARCH AND REFERENCE BANK CONSTRUCTION
### (Verifying and Grounding the Architecture — Not Replacing It)

**The problem this stage solves:** Without pre-research, the generating system produces references from training knowledge at generation time. This causes three failure modes: (1) hallucinated citations — sources that don't exist or are misattributed, (2) stale citations — sources that have been superseded, retracted, or updated, (3) generic citations — "see any textbook on X" rather than the specific source that best supports the chapter's argument. Pre-research eliminates all three by collecting real, verified sources before prose generation begins.

**Critical framing — VERIFICATION, NOT DISCOVERY:** The Stage 2 architecture was built from the LLM's integrated, compressed knowledge of the domain — a synthesis of thousands of sources into coherent structural reasoning. This is the right tool for architectural decisions. Stage 3 search serves to **verify and ground** that architecture, not to replace it. Specifically:
- Search to **verify** each vyāpti, not to discover new ones
- Search to **find documented instances** of each hetvābhāsa, not to discover new fallacies
- Search to **source** each chapter's core concept, not to redefine what the chapter covers
- **Flag conflicts** between search findings and architecture for user decision — do not auto-revise based on search results alone

Search biases (recency, SEO ranking, fragmentation, authority confusion) can distort architectural reasoning if given too much weight. The LLM's integrated reasoning leads; search follows as verification and grounding.

**Input:** The complete Stage 2 Architecture — specifically:
- The chapter sequence with core concepts
- The vyāpti list (each needs sourcing to verify the structural regularity)
- The hetvābhāsa list (each needs sourcing to document the fallacy)
- The threshold concept list (each needs sourcing for the transformation it describes)
- The decay marker registry (each needs sourcing to establish current status)
- The resolution ledger (open questions need sourcing for frontier status)

**Also from Stage 1:**
- The tacit knowledge density estimate (density level, anticipated tacit skills list)
- These become the search targets for the Tacit Knowledge Source Search (Step 3G)

### Step 3A: Chapter-by-Chapter Source Search

For EACH chapter in the sequence from Stage 2, search for:

1. **The core concept's foundational source** — the landmark paper, book chapter, or primary text where the concept was first established or best articulated. This is the source the reader would cite if writing about this concept.

2. **The best contemporary treatment** — the most current, accessible, and rigorous explanation. This may be a textbook, review article, or practitioner guide. Prioritize sources published within the last 5–10 years unless the foundational source is itself the best treatment.

3. **A worked example or case source** — a source that demonstrates the concept in application. For Craft (Type 4) domains: practitioner accounts, case studies, post-mortems. For Empirical (Types 2–3): experimental papers or datasets. For Formal (Type 1): proof collections or problem sets. For Interpretive (Type 5): the primary text itself.

4. **A dissenting or complicating source** (where applicable) — a source that challenges, limits, or nuances the chapter's core claim. This feeds the guide's epistemic honesty and may connect to hetvābhāsas or decay markers.

**Search strategy (verification-first):**
- Use specific, targeted queries: "[concept name] foundational paper", "[concept] systematic review", "[concept] practitioner guide"
- For each search, evaluate: Is this a primary source or a secondary summary? Is the author authoritative in this domain? Is this current enough for the claim it supports?
- If a search returns no strong results for a concept, FLAG it — this is a sourcing gap. The chapter may be relying on training knowledge that cannot be externally verified.
- If search results contradict the Stage 2 architecture, do NOT auto-revise. Flag the conflict in Step 3F for user review.

### Step 3B: Vyāpti Verification Search

For EACH vyāpti from the Stage 2 list, search to **verify** that the structural regularity holds:

1. **Empirical or theoretical support** — evidence confirming the structural regularity. For causal vyāptis: intervention studies, mechanism papers. For structural vyāptis: review articles, meta-analyses. For empirical regularities: replication studies, scope condition analyses.

2. **Known exceptions or boundary conditions** — sources that document where the vyāpti breaks down. These strengthen the scope conditions written in Stage 2.

If a vyāpti cannot be verified against external evidence, flag it and note:
- "UNSOURCED VYĀPTI: [name] — based on training knowledge, not verified against current literature. Consider downgrading causal status or adding explicit caveat."

### Step 3C: Hetvābhāsa Documentation Search

For EACH hetvābhāsa from the Stage 2 list, search for:

1. **A documented instance** — a real case where this reasoning error led to a bad outcome. Named examples are stronger than hypotheticals.

2. **Literature on the fallacy** — if the fallacy has a name in the domain's literature (not just the Ānvīkṣikī name), find the source that describes it.

### Step 3D: Frontier and Decay Source Search

For EACH decay marker in the registry, search for:
- The **current status** of the condition the claim depends on
- The **most recent authoritative source** confirming or updating the claim

For EACH open entry in the resolution ledger, search for:
- **Current state of the debate** — the most recent papers or analyses addressing the open question

For threshold concepts, search for:
- **Pedagogical research** on how the threshold crossing is best facilitated (if available for this domain)

### Step 3E: Assemble the Reference Bank

Organize all collected sources into a Reference Bank structured by chapter:

```
REFERENCE BANK

═══════════════════════════════════════════
CHAPTER [N]: [CONCEPT NAME]
───────────────────────────────────────────
FOUNDATIONAL: 
  [Author(s), Title, Year, URL if available]
  — [One-line annotation: what this establishes]

CONTEMPORARY TREATMENT:
  [Author(s), Title, Year, URL if available]
  — [Annotation: why this is the best current treatment]

WORKED EXAMPLE / CASE:
  [Author(s), Title, Year, URL if available]
  — [Annotation: what this demonstrates]

DISSENTING / COMPLICATING (if found):
  [Author(s), Title, Year, URL if available]
  — [Annotation: what this challenges or nuances]

ADDITIONAL (if search surfaced strong relevant sources):
  [Author(s), Title, Year, URL if available]
  — [Annotation]

SOURCING GAPS: [List any concepts in this chapter that 
  could not be grounded in verified sources. Note: "Based 
  on training knowledge — reader should independently verify."]

═══════════════════════════════════════════
[Repeat for each chapter]

═══════════════════════════════════════════
CROSS-CUTTING SOURCES
───────────────────────────────────────────
VYĀPTI SOURCES:
  Vyāpti 1 [name]: [Source] — [verification status]
  Vyāpti 2 [name]: [Source] — [verification status]
  [repeat for all]
  UNSOURCED: [list any vyāptis without external verification]

HETVĀBHĀSA SOURCES:
  Hetvābhāsa 1 [name]: [Documented instance source]
  [repeat for all]

DECAY MARKER CURRENT STATUS:
  Claim 1: [Current status per search] — [Source, date]
  [repeat for all]

FRONTIER SOURCES:
  Open question 1: [Most current source on debate status]
  [repeat for all]

TACIT KNOWLEDGE SOURCES (from Step 3G):
  Tacit skill 1 [name]: [count] sources across [vehicles found]
  Tacit skill 2 [name]: [count] sources across [vehicles found]
  [repeat for all]
  GAPS: [skills with missing required vehicles]

═══════════════════════════════════════════
SOURCING QUALITY SUMMARY
───────────────────────────────────────────
Chapters with strong sourcing (3+ verified sources): [list]
Chapters with weak sourcing (1–2 sources): [list]
Chapters with sourcing gaps (0 verified sources): [list]
Vyāptis fully sourced: [N] of [total]
Hetvābhāsas with documented instances: [N] of [total]
Decay markers with current verification: [N] of [total]
```

### Step 3F: Architecture Revision Flags

Based on the research, flag any Stage 2 architecture elements that should be reconsidered:

```
ARCHITECTURE REVISION FLAGS (from Research):

STRENGTHEN: [Elements where research found stronger 
  evidence than expected — consider upgrading causal status 
  or expanding scope]

WEAKEN: [Elements where research found less support than 
  expected — consider downgrading, adding caveats, or 
  restructuring the chapter]

MISSING: [Important sources or concepts discovered during 
  research that are NOT in the current architecture — 
  consider adding]

OUTDATED: [Decay markers where current status has changed 
  since training data — update the architecture accordingly]

RECOMMEND: [Specific architecture changes, if any. 
  If none needed, state "Architecture confirmed by research 
  — no revisions recommended."]
```

### Step 3G: Tacit Knowledge Source Search

**Input:** The anticipated tacit skills list from Stage 1's Tacit Knowledge Density Estimate, plus the tacit knowledge density level (Low/Medium/High) which determines which source types are required.

For EACH anticipated tacit skill, search for four categories of sources. **Which categories are required depends on the density level from Stage 1:**
- **Low density:** Case studies only (categories 1)
- **Medium density:** Case studies + Experiential simulations (categories 1–2)
- **High density:** All four categories (1–4)

**Category 1 — Case Studies:**
Search for real situations where expert judgment on this tacit skill was the deciding factor. Prioritize:
- Messy, ambiguous cases where the "right" answer wasn't obvious
- Cases where the expert's reasoning process is documented (not just the outcome)
- Post-mortems and failure analyses where tacit knowledge gaps caused problems
- Search queries: "[tacit skill] case study", "[tacit skill] expert decision making", "[domain] judgment call examples", "[domain] post-mortem"

**Category 2 — Experiential Simulations:**
Search for existing exercises, decision-forcing cases, scenario walkthroughs, or simulation frameworks that put learners in the position of making the judgment calls this tacit skill requires. These are NOT quizzes testing explicit knowledge — they are exercises in ambiguity where the reasoning process matters more than the answer.
- Search queries: "[tacit skill] simulation exercise", "[domain] decision-forcing case", "[domain] scenario-based learning", "[tacit skill] training exercise"

**Category 3 — High-Contrast Debates:**
Search for instances where two credible experts reached different conclusions on a question involving this tacit skill — not because one was wrong on the facts, but because they weighted evidence differently, recognized different patterns, or had different risk tolerances. The contrast itself teaches the tacit dimension.
- Search queries: "[tacit skill] expert disagreement", "[domain] debate [specific judgment area]", "[domain] opposing expert views"

**Category 4 — Practitioner Podcasts and Interviews:**
Search for long-form conversations where experts in this domain think out loud about the kind of judgment this tacit skill involves. Podcasts and interviews are uniquely valuable because experts in conversation reveal reasoning processes they never articulate in writing — the hesitations, qualifications, real-time pattern recognition, and intuitive weighting that constitute tacit knowledge made partially audible.
- Search queries: "[domain] expert interview podcast", "[domain] practitioner conversation", "[specific expert name] interview [tacit skill area]"
- For each result, note the specific segment or topic within the conversation that surfaces the tacit reasoning

**Assemble the Tacit Knowledge Source Bank:**

```
TACIT KNOWLEDGE SOURCE BANK

═══════════════════════════════════════════
TACIT SKILL 1: [Name from Stage 1 anticipated list]
Density level: [Low/Medium/High] → Required: [list vehicles]
───────────────────────────────────────────
CASE STUDIES (required for all density levels):
  1. [Source — Title, Author/Org, Year, URL if available]
     — [Annotation: what happened, why tacit judgment was 
       decisive, what the reader will learn]
  2. [Source]
     — [Annotation]

EXPERIENTIAL SIMULATIONS (required for Medium+):
  1. [Source — Title, Author/Org, Year, URL if available]
     — [Annotation: what the exercise involves, what tacit 
       skill it develops]
  [Or: "No existing simulation found — will design original 
   decision-forcing scenario in the guide"]

HIGH-CONTRAST DEBATES (required for High):
  1. [Source — Debate/Article/Talk, Participants, Year, URL]
     — [Annotation: what the experts disagree on, why both 
       sides are defensible, what tacit dimension drives 
       the divergence]

PRACTITIONER PODCASTS/INTERVIEWS (required for High):
  1. [Source — Show/Episode, Guest, Year, URL if available]
     — [Annotation: what to listen for, approximate timestamp 
       or topic where tacit reasoning surfaces]

SOURCING GAPS: [Any vehicles that could not be sourced. 
  Note whether an original exercise/case can be designed 
  from training knowledge.]

═══════════════════════════════════════════
[Repeat for each anticipated tacit skill]

═══════════════════════════════════════════
TACIT KNOWLEDGE SOURCING SUMMARY
───────────────────────────────────────────
Tacit skills with full sourcing (all required vehicles): [list]
Tacit skills with partial sourcing: [list + what's missing]
Tacit skills with no external sourcing: [list — these will 
  rely on LLM-generated cases and exercises]
Total sources collected: [count by category]
```

═══════════════════════════════════════════
⛔ STAGE 3 GATE — HARD STOP (RESEARCH GATE)
═══════════════════════════════════════════

SELF-AUDIT:
□ Chapter source search: [N] of [total] chapters have 
  at least 2 verified sources? List any gaps.
□ Vyāpti verification: [N] of [total] vyāptis sourced?
  List any unsourced.
□ Hetvābhāsa documentation: [N] of [total] have documented 
  instances? List any undocumented.
□ Decay marker current status: [N] of [total] verified 
  against current information? List any unverified.
□ Frontier sources: [N] of [total] open questions have 
  current sourcing? List any gaps.
□ Tacit knowledge source search (Step 3G):
  - Tacit skills searched: [N] of [total from Stage 1]
  - Case studies found: [N] of [N required]
  - Experiential simulations found: [N] of [N required by density]
  - High-contrast debates found: [N] of [N required by density]
  - Podcast/interview refs found: [N] of [N required by density]
  - Skills with sourcing gaps: [list]
□ Sourcing Quality Summary produced? [yes/no]
□ Tacit Knowledge Source Bank produced? [yes/no]
□ Architecture Revision Flags produced? [yes/no]

STOP and present:
- The complete Reference Bank
- The Tacit Knowledge Source Bank
- The Sourcing Quality Summary
- Architecture Revision Flags (if any)

Tell the user: "The Reference Bank above will feed every 
chapter's REFERENCES section. Chapters flagged with sourcing 
gaps will rely on training knowledge — consider whether those 
chapters need restructuring or additional research.

If Architecture Revision Flags suggest changes, please 
specify revisions before I proceed. Reply 'continue' to 
proceed to Stage 4 (Guide Generation), or specify corrections."

DO NOT begin writing guide prose. DO NOT draft the opening.

---

# ═══════════════════════════════════════════
# STAGE 4: GUIDE GENERATION (Parts I–III)
# ═══════════════════════════════════════════

## PHASE 3: GUIDE GENERATION
### Structural Requirements

**Before writing any prose, reproduce the Stage 2 Architecture Output as a reference block AND the Stage 3 Reference Bank chapter-source mapping.** This is not optional — it is the mechanism that prevents architectural drift during long-form generation and ensures every chapter's references are drawn from verified sources, not generated from training memory.

The guide has five parts. Each part has specific requirements. Word allocations are proportional and vary by domain type.

**WORD ALLOCATION BY DOMAIN TYPE:**

| Domain Type | Foundations | Synthesis | Advanced | Frontier | Framework |
|---|---|---|---|---|---|
| Type 1 (Formal) | 40% | 25% | 15% | 10% | 10% |
| Type 2 (Mechanistic) | 30% | 30% | 20% | 10% | 10% |
| Type 3 (Probabilistic) | 25% | 25% | 20% | 20% | 10% |
| Type 4 (Craft) | 25% | 20% | 25% | 15% | 15% |
| Type 5 (Interpretive) | 20% | 25% | 20% | 20% | 15% |

Total guide: 10,000–20,000 words depending on domain scope. The guide is complete when the framework chapter enables novel reasoning, not when a word count is met. Every sentence must earn its place.

**CONCEPT DENSITY CHECK:** Every chapter must have exactly one core insight — statable in a single sentence that doesn't use the word "overview" or "introduction." Chapters with zero core insights get merged into adjacent chapters as application material. Chapters with multiple core insights get split.

**CHAPTER REFERENCES REQUIREMENT:** Every chapter must end with a REFERENCES section listing the source material that informed the chapter's content. **Draw references from the Stage 3 Reference Bank** — do not generate references from training memory during prose writing. This serves three purposes: (1) it gives the reader a path to verify claims and go deeper than the guide can, (2) it models the epistemic virtue of showing your sources, and (3) it makes the guide's own pramāṇa visible — the reader can evaluate the quality of the foundations the chapter rests on.

Reference entries should be specific (not "see any textbook on X") and annotated (a one-line note on what the source contributes and why it's worth reading). Prioritize primary sources, foundational texts, and landmark papers over secondary summaries. For Craft (Type 4) domains, practitioner accounts and case studies count as valid references. For Interpretive (Type 5) domains, the primary texts under analysis are references. Include 3–7 references per chapter — enough to ground the chapter, not so many that the list becomes a bibliography dump. For chapters flagged with sourcing gaps in Stage 3, explicitly note which claims rely on unverified training knowledge.

---

### THE OPENING: Before Chapter 1

```
[TOPIC]: A Framework for Thinking
From First Principles to Expert Judgment

The Central Question: [The deepest question this domain 
  tries to answer]

What You Will Be Able to Do: [3–4 concrete capabilities — 
  not "understand X" but "reason about X in situations Y", 
  "evaluate claims about X using Z", "diagnose when approach 
  X is failing and why"]

How We Will Build It: [One paragraph on the pedagogical 
  method — not a table of contents but an explanation of the 
  inquiry approach the guide uses]

A Note on Domain Type: [One paragraph on what kind of 
  knowledge this is, what counts as valid evidence here, 
  and what the honest limits of the guide are]

Analogy Anchor: [From calibration — "This guide draws 
  analogies from [reader's domains]. If you have a background 
  in [X], you'll recognize parallels."]
```

---

### PART I: FOUNDATIONS (Chapters 1–N, where N depends on the domain)

**Purpose:** Establish the conceptual bedrock. Nothing in Part I should require anything not established in Part I or stated as an axiom/pramāṇa.

**CHAPTER STRUCTURE — Use the structure assigned in Step 2G. The five structures are defined below.**

---

**STRUCTURE A: PAÑCĀVAYAVA (default for foundational chapters)**

```
CHAPTER [N]: [CONCEPT NAME]

PREREQUISITES: [Exactly which previous chapters/concepts 
  are required]

SEAM BRIDGE: [Required — state the relationship between 
  this chapter and the previous one. Use exactly one:]
  BUILDS ON: "[Previous] gave you [X]. This chapter adds 
    [Y], which was impossible without [X]."
  PARALLEL TO: "[Previous] and [this] are both tools for 
    [shared purpose]. They don't depend on each other."
  REFRAMES: "Now that you understand [this], go back and 
    reconsider [previous]."
  SPECIALIZES: "[Previous] was the general framework. 
    [This] is what it looks like in [specific context]."
  TENSIONS WITH: "[Previous] suggests [X]. [This] suggests 
    [Y]. The tension is real, not a mistake."

────────────────────────────────────────────────
THE PROBLEM (Pakṣa — the proposition)

Present the reader with a scenario they cannot yet resolve 
using only what they know so far. Let them encounter the gap:

"Here is a situation: [concrete, specific scenario].
Try to reason through it with what you have so far."

Then name what breaks:
"If you found yourself unable to [X] or uncertain about [Y], 
you've encountered exactly the gap this concept fills."

Do not merely explain the problem — pose it.
────────────────────────────────────────────────
THE REASON (Hetu — why this concept solves it)

The fundamental insight that resolves the problem.
This is not the definition. It is the realization that makes 
the definition necessary.
────────────────────────────────────────────────
THE EXAMPLE WITH UNIVERSAL RULE (Udāharaṇa)

A worked example that instantiates the concept.
After the example, state the universal principle it illustrates:
"This example works because [vyāpti]: wherever [A], 
necessarily [B]."
────────────────────────────────────────────────
THE APPLICATION (Upanaya)

Apply the concept to the reader's domain/goal (from calibration).
Apply it to a second, different case to show the concept is 
not the example.
────────────────────────────────────────────────
THE CONCLUSION (Nigamana)

What the reader can now do that they couldn't before.
Which vyāpti this concept anchors or illuminates.
What this concept enables next.
────────────────────────────────────────────────

CAUSAL REASONING CHECK — Three Moves:

INTERVENTION: If you changed [the variable this concept 
  identifies], what downstream effect would you predict, 
  through what mechanism? What confounders might make you 
  think the intervention worked when it didn't (or vice versa)?

MECHANISM: WHY does this principle produce the outcomes it 
  does? What is the causal pathway (A → B → C)? What would 
  disrupt the A→B link or the B→C link independently?

SCOPE: Under what specific conditions would following this 
  principle lead you to the WRONG conclusion or action? How 
  would you recognize you're in those conditions before you've 
  committed to the wrong course?

HETVĀBHĀSA ALERT (if assigned to this chapter in Step 2B):
[If a characteristic fallacy naturally arises at this point, 
introduce and name it now]

TRANSFER TEST:
Present a novel scenario the guide has NOT covered — one that 
requires the reader to apply the chapter's concept in an 
unfamiliar context. For tests after Chapter 3+, require 
discriminating between multiple concepts from different chapters.

SCENARIO: [A specific, realistic situation]
APPLY: Using what you've learned, what would you diagnose, 
  predict, or recommend?
WHAT THE EXPERT SEES: [The reasoning an expert would use — 
  revealed after the reader has attempted the scenario]
WHAT NOVICES TYPICALLY GET WRONG: [The characteristic error, 
  connecting to the hetvābhāsa if applicable]

GOING DEEPER:
For readers wanting more depth: [1–3 specific resources — 
  books, papers, tools, or primary sources]
For readers who found this challenging: revisit [specific 
  prerequisite concept] before continuing.

DERIVATION NOTE (if this chapter contains a claim from the 
Derivation Registry, Step 2J — insert at point of claim):

  🔗 DERIVATION: [Claim]
  This claim follows from [principle/premise A] combined with 
  [principle/premise B], via [named mechanism or vyāpti]. 
  The main risk of error here is [named hetvābhāsa] — we avoid 
  it because [reason]. 
  Source: [Sourced / Partially sourced / Unsourced — if unsourced, 
  the reader should verify via [specific method]].

CROSS-DOMAIN BRIDGE (if an isomorphism from Step 2K is 
assigned to this chapter):

  🌐 ISOMORPHISM: [This domain's concept] ↔ [Reader's domain concept]
  The structural match: [What's the same abstract structure]
  Where it breaks: [Where the analogy fails — and why]
  What the difference teaches: [What's unique to this domain 
    that your prior knowledge cannot predict]

METACOGNITIVE CHECKPOINT:

  🎯 CALIBRATION PROBE: Before reading the expert answer to the 
  transfer test above, rate your confidence (1–5) that your 
  answer is correct. After checking: were you overconfident, 
  underconfident, or calibrated? Track this over chapters — 
  your calibration curve is itself information about your 
  learning.

  📝 SELF-EXPLANATION: In your own words (not the guide's), 
  explain WHY the core principle of this chapter holds. What 
  would break it? If you cannot articulate this without 
  re-reading, your understanding is receptive, not generative.

────────────────────────────────────────────────
REFERENCES

Sources that inform this chapter:

1. [Author(s), Title, Year] — [One-line annotation: what this 
   source contributes to the chapter's argument and why it's 
   worth reading]
2. [Author(s), Title, Year] — [Annotation]
3. [Author(s), Title, Year] — [Annotation]
[3–7 references. Prioritize primary/foundational sources. 
 Every major claim in the chapter should be traceable to 
 at least one reference here.]
```

---

**STRUCTURE B: CONVERGENCE (for intermediate synthesis chapters)**

```
CHAPTER [N]: [CONCEPT NAME]

PREREQUISITES: [Which previous chapters converge here]
SEAM BRIDGE: [Relationship to previous chapter]

CONVERGENCE POINT: [Which previously established concepts 
  meet here, and what new capability emerges from their 
  intersection]

WHAT SURPRISE THIS CREATES: [What the reader would not have 
  predicted from the individual foundations]

[Body — organized by the content's needs, not a fixed template]

CAUSAL REASONING CHECK — Three Moves:
[As in Structure A]

TRANSFER TEST:
[As in Structure A — but must require discriminating between 
multiple concepts from different chapters]

DERIVATION NOTE (if applicable — as in Structure A)
CROSS-DOMAIN BRIDGE (if applicable — as in Structure A)

────────────────────────────────────────────────
REFERENCES
[As in Structure A — 3–7 annotated sources informing 
 this chapter]
```

---

**STRUCTURE C: DIAGNOSIS (for failure mode and troubleshooting chapters)**

```
CHAPTER [N]: [CONCEPT NAME]

SEAM BRIDGE: [Relationship to previous chapter]

SYMPTOM: [What the failure looks like from the outside]
DIFFERENTIAL DIAGNOSIS: [What it could be — multiple candidates]
RULING OUT: [How to distinguish between candidates]
CORRECT DIAGNOSIS: [The actual cause, with causal explanation]
TREATMENT: [What to do, connected to the vyāpti being violated]

For each failure, connect to the failure ontology from Phase 0:
Failure by whose standard? On what timescale? Relative to what 
benchmark?

CAUSAL REASONING CHECK — Three Moves:
[As in Structure A]

DERIVATION NOTE (if applicable — as in Structure A)
CROSS-DOMAIN BRIDGE (if applicable — as in Structure A)

────────────────────────────────────────────────
REFERENCES
[As in Structure A — 3–7 annotated sources. For diagnosis 
 chapters, include sources documenting the failure modes 
 and their resolution.]
```

---

**STRUCTURE D: DEBATE (Vāda — for contested areas)**

```
CHAPTER [N]: [CONTESTED QUESTION]

SEAM BRIDGE: [Relationship to previous chapter]

POSITION A: [Best evidence and reasoning for A]
POSITION B: [Best evidence and reasoning for B]
CRUX OF DISAGREEMENT: [The precise point where A and B diverge]
WHAT WOULD RESOLVE IT: [Evidence or argument that would settle it]

WHERE JALPA EXISTS: [Are any participants arguing for position 
  rather than truth? What are their incentives?]

DERIVATION NOTE (if applicable — as in Structure A)
CROSS-DOMAIN BRIDGE (if applicable — as in Structure A)

────────────────────────────────────────────────
REFERENCES
[As in Structure A — 3–7 annotated sources. For debate 
 chapters, include the strongest source for EACH position, 
 so the reader can evaluate the arguments firsthand.]
```

---

**STRUCTURE E: NARRATIVE (for case studies and tacit knowledge)**

```
CHAPTER [N]: [CONCEPT NAME]

SEAM BRIDGE: [Relationship to previous chapter]

THE CASE: [A real or realistic case, told chronologically — 
  what happened and why decisions were made]
WHAT WENT RIGHT/WRONG AND WHY: [Analysis with causal reasoning]
THE PRINCIPLE EXTRACTED: [What generalizes from this case]
THE TACIT RESIDUE: [What can't be fully extracted — what 
  requires practice to build]

DERIVATION NOTE (if applicable — as in Structure A)
CROSS-DOMAIN BRIDGE (if applicable — as in Structure A)

────────────────────────────────────────────────
REFERENCES
[As in Structure A — 3–7 annotated sources. For narrative 
 chapters, include the case source itself plus analytical 
 sources that generalize from it.]
```

---

**Landscape Acknowledgment — Required at every landscape point identified in Step 2H:**

When multiple concepts exist at the same level of the dependency map, before diving into the first one:

```
AT THIS LEVEL: THE LANDSCAPE

We have arrived at a branching point. Several concepts exist 
at this level of complexity. They are peers — neither requires 
the others as prerequisite.

| Concept | Core insight | When you need it | Chapter |
|---------|-------------|-----------------|---------|
| [A]     | [One line]  | [Specific use]  | [N]     |
| [B]     | [One line]  | [Specific use]  | [N+k]   |

Why we explore [A] first:
[Reason 1 — pedagogical]
[Reason 2 — practical]

We will return to [B] in Chapter [N+k]. When we do, you will 
recognize it as [relationship to A].
```

---

**Threshold Concept Treatment — Required for concepts identified as thresholds in Step 2D:**

```
PRE-THRESHOLD WARNING (before the chapter):
"What you're about to encounter will reorganize how you think 
about [previously introduced concepts]. This is expected and 
desirable. Specifically, you currently understand [X] as 
[current form]. After this chapter, you'll understand it as 
[transformed form]. The shift may feel uncomfortable — that 
discomfort is the threshold working."

[Chapter content — allocate 1.5x normal space]

POST-THRESHOLD REFLECTION (after the chapter):
"Notice that [earlier concept] now looks different. 
Specifically: [what changed]. If you go back and re-read 
Chapter [N] now, you'll see [what's visible in retrospect]. 
This reorganization is permanent — and it's a sign that your 
understanding has genuinely deepened."
```

---

**Discrimination Case — Required for every confusion-pair identified in Step 2H:**

```
DISCRIMINATION CASE: [Concept A] vs. [Concept B]

These two concepts are frequently confused because 
[why they look similar].

SCENARIO: [A situation where both seem applicable]
Why [A] is wrong here: [Specific reasoning]
Why [B] is right here: [Specific reasoning]
The distinguishing signal: [What to look for that tells you 
  which one applies in practice]
```

---

**Spaced Return Signal — Required at every point identified in Step 2E. Use the signal text written in Step 2E.**

```
SPACED RETURN:
We first encountered [concept] in Chapter [N], where it meant 
[simple form]. Now that we're working with [current concept], 
notice that [concept] reappears here in a more general form: 
[expanded form]. Your understanding of [concept] has just 
deepened — and it should.
```

---

**Resolution Closure — Required whenever an earlier question from the Resolution Ledger is resolved:**

```
RESOLUTION:
In Chapter [N], we asked: [question, stated explicitly].
We now have enough machinery to answer it: [answer].
If you revisit Chapter [N] with this understanding, you'll 
notice [what becomes visible in retrospect that wasn't before].
```

---

**Decay Marker — Required for every claim registered in Step 2I:**

```
⏱ CONDITION-DEPENDENT: [Claim] holds as of [date]. 
  The underlying principle is [X — durable]. 
  The specific manifestation depends on [Y — which changes]. 
  Check [Z — specific thing to verify] to confirm this 
  still applies.
```

---

### PART I–III INLINE QUALITY ASSERTIONS

**NEW IN v3.0** — Instead of a post-hoc quality gate, embed assertions during generation. After completing each Part, verify:

**After Part I:**
```
PART I ASSERTION CHECKLIST:
□ Every chapter uses its assigned structure from Step 2G
□ Every chapter has exactly one core insight
□ Every chapter has a seam bridge to its predecessor
□ Every chapter has a causal reasoning check (3 moves)
□ Every foundational chapter has a transfer test
□ All hetvābhāsas assigned to Part I chapters are introduced
□ All landscape points in Part I have acknowledgments
□ All confusion-pairs in Part I have discrimination cases
□ No concept in Part I relies on anything not yet introduced
□ Tacit knowledge blocks: [count] present vs. [minimum required]
  - Each block has case study? [yes/no per block]
  - Each block has experiential simulation (if Medium+ density)? [yes/no]
  - High-contrast debates present (if High density)? [yes/no]
  - Podcast/interview refs present (if High density)? [yes/no]
  - Sources drawn from Tacit Knowledge Source Bank? [yes/no]
□ Decay markers from registry: [count placed] vs. [count due in Part I]
□ Chapter references: every chapter has 3–7 annotated sources? [count chapters with references] / [total Part I chapters]
□ Derivation proof sketches from registry: [count placed] vs. [count due in Part I]
□ Cross-domain isomorphism blocks: [count placed] vs. [count due in Part I]
□ Metacognitive checkpoints: [count] / [total Part I chapters]

MISSING ELEMENTS (if any): [List and address before proceeding]
```

═══════════════════════════════════════════
⛔ STAGE 4 GATE — HARD STOP
═══════════════════════════════════════════

SELF-AUDIT:
1. Run the Part I Assertion Checklist above. Every box must 
   be checked. Fix gaps before stopping.
2. Produce cumulative ELEMENT TRACKING (Rule 3).
3. List REMAINING ELEMENTS for Stages 5–6.

STOP and present using Rule 1 format. Include:
- Chapters produced with core insight for each
- Assertion checklist result
- Element tracking counts
- Remaining work list

DO NOT begin Part II. DO NOT write the recalibration check.

---

### PART II: INTERMEDIATE SYNTHESIS

**Purpose:** Concepts that require multiple foundations working together. The key intellectual move here is not just introducing new concepts but showing how previously separate ideas *converge*.

**RECALIBRATION CHECK (required before beginning Part II):**
```
The reader has now absorbed [N foundational concepts from Part I].
Analogy pool update: In addition to [original analogy domains], 
  the following Part I concepts are now available as analogy sources 
  for more complex material: [list]
Depth adjustment: [any changes based on how Part I content 
  developed relative to calibration expectations]
Calibration carry-forward: The reader's Part I metacognitive 
  checkpoints revealed [pattern — e.g., systematic overconfidence 
  on X, underconfidence on Y, well-calibrated on Z]. Part II 
  material should [adjust accordingly — e.g., add extra 
  verification prompts for X-type claims, build confidence on 
  Y-type reasoning].
```

Chapters in this part should primarily use Structure B (Convergence) or Structure E (Narrative), as assigned in Step 2G.

**Tacit Knowledge Note:** At points where expert judgment is not fully articulable, deploy a **Tacit Knowledge Transmission Block**. This replaces the simple marker with a multi-vehicle approach that actively transmits tacit knowledge rather than merely identifying its existence. **Draw case studies, simulations, debates, and podcast references from the Stage 3 Tacit Knowledge Source Bank.**

Which vehicles to include depends on the density level from Stage 1:
- **Low density:** Case study + Receptive→Generative bridge
- **Medium density:** Case study + Experiential simulation + Receptive→Generative bridge
- **High density:** All vehicles

```
TACIT KNOWLEDGE BLOCK: [Name of the tacit skill]

────────────────────────────────────────────────
THE GAP

[What experts can do here that cannot be fully articulated 
as rules. Be specific — not "experts just know" but "experts 
can [specific capability] in situations where [specific 
ambiguity], and this skill involves [pattern recognition / 
risk weighting / aesthetic judgment / timing intuition / etc.] 
that resists full propositional capture.]

────────────────────────────────────────────────
CASE STUDY (required for all density levels)

[A real case — sourced from the Tacit Knowledge Source Bank — 
where this tacit skill was the deciding factor.]

THE SITUATION: [What happened — presented chronologically, 
  with the ambiguity and incomplete information intact. Do 
  not sanitize into a clean textbook case.]
THE DECISION POINT: [Where expert judgment was required]
WHAT THE EXPERT DID: [The choice made and the reasoning 
  process — to whatever extent it's documented]
WHY THIS CAN'T BE REDUCED TO A RULE: [What about this 
  situation made rules insufficient — was it the ambiguity? 
  The interaction of multiple factors? The need to weigh 
  incommensurable values? The time pressure?]
WHAT A NOVICE WOULD LIKELY HAVE DONE: [The characteristic 
  novice response and why it seems reasonable but fails]

Source: [Full citation from Tacit Knowledge Source Bank]

────────────────────────────────────────────────
EXPERIENTIAL SIMULATION (required for Medium+ density)

[A decision-forcing scenario the reader works through. NOT 
a transfer test (which tests explicit knowledge) — this is 
a judgment exercise where there is no single right answer. 
The point is to practice the reasoning process.]

SITUATION: [Ambiguous, realistic scenario with incomplete 
  information, time pressure, or competing valid approaches. 
  Sourced from or inspired by Tacit Knowledge Source Bank.]
  
WHAT YOU MUST DECIDE: [The judgment call — framed so the 
  reader must commit to an approach before seeing how 
  experts would handle it]

CONSTRAINTS: [What makes this hard — missing information, 
  time pressure, competing stakeholder needs, irreversibility]

EXPERT PANEL — How experienced practitioners would approach 
this (revealing legitimate variation in expert judgment):

  EXPERT A: [Approach + reasoning — emphasizing what pattern 
    they recognize and what they weight heavily]
  EXPERT B: [Different approach + reasoning — emphasizing a 
    different pattern or different weighting]
  EXPERT C (if applicable): [A third perspective that 
    highlights a dimension A and B both underweight]

WHY ALL APPROACHES ARE DEFENSIBLE: [What makes this a 
  judgment call, not a knowledge gap]

WHAT THIS REVEALS: [The tacit dimension the reader just 
  exercised — name it explicitly so they can recognize it 
  developing through practice]

────────────────────────────────────────────────
HIGH-CONTRAST DEBATE (required for High density)

[Two credible positions on a judgment call in this domain. 
NOT a Structure D debate about contested facts — this is a 
debate about judgment under ambiguity where both sides are 
defensible because the disagreement is about tacit weighting, 
not about evidence.]

POSITION A: [Expert view + reasoning]
  This expert weights: [What they prioritize and why]

POSITION B: [Expert view + reasoning]
  This expert weights: [What they prioritize and why]

WHY BOTH ARE DEFENSIBLE: [This is a judgment call because 
  the facts underdetermine the answer — the difference is 
  in what you weigh, what patterns you recognize as 
  relevant, and what risks you're willing to accept]

WHAT SEPARATES THEM: [The tacit dimension — pattern 
  recognition breadth? Risk tolerance? Time horizon? 
  Aesthetic versus functional priority? Name it.]

Source: [Citation from Tacit Knowledge Source Bank]

────────────────────────────────────────────────
LISTEN FURTHER (required for High density)

[1–2 specific podcast episodes or long-form interviews where 
an expert thinks through this kind of judgment out loud.]

EPISODE 1: [Title, Show, Guest, Year, URL if available]
  WHAT TO LISTEN FOR: [The specific tacit reasoning that 
    surfaces — e.g., "At ~23:00, [expert] describes how 
    they decide [X], and you can hear the pattern 
    recognition happening in real time"]
  WHY THIS MATTERS: [What the reader will absorb from 
    hearing the expert think out loud that no written 
    source can transmit]

EPISODE 2 (if available): [Same format]

────────────────────────────────────────────────
RECEPTIVE → GENERATIVE BRIDGE (required for all density levels)

What this guide has built: RECEPTIVE knowledge — you can 
  recognize, evaluate, and follow reasoning about [this 
  tacit skill]. You can see when an expert is exercising 
  this judgment and understand why they made the call 
  they made.

What practice builds: GENERATIVE knowledge — you can 
  exercise this judgment yourself under real conditions, 
  with real stakes and real ambiguity.

The gap between these: [Specific description of what 
  changes when you move from recognizing to generating]

SPECIFIC PRACTICE PATH: [NOT "get more experience" — 
  concrete, actionable steps:]
  1. [Specific exercise or activity — with frequency]
  2. [Specific type of exposure or apprenticeship pattern]
  3. [Specific deliberate practice protocol]
  4. [How to self-assess progress — what markers indicate 
     you're developing this tacit skill]
```

---

### PART III: ADVANCED INTEGRATION

**Purpose:** Edge cases, failure modes, sophisticated applications, and the interaction of the domain with adjacent domains.

**RECALIBRATION CHECK (required before beginning Part III):**
```
The reader has now absorbed [foundational + synthesis concepts].
The reader's relationship to the material has shifted from 
  [initial characterization] to [current characterization].
Analogy pool update: [any new analogy sources from Part II]
Part III emphasis: Based on the reader's goal of [goal from 
  calibration], emphasize [specific aspects of advanced material].
Calibration carry-forward: The reader's calibration pattern from 
  Part I checkpoints was [pattern]. Part II transfer tests 
  [confirmed / shifted / complicated] this pattern. Part III 
  should [specific adjustment — e.g., the framework anti-patterns 
  should especially target the reader's demonstrated blind spots].
```

**Required sections:**

**Failure Mode Catalogue (use Structure C — Diagnosis):**
```
THE FAILURE MODES OF [TOPIC]

Experts are distinguished not by knowing more things that work
but by knowing more precisely when and why things fail.

[For each of 3–6 domain-appropriate failure modes, use the 
Diagnosis structure: Symptom → Differential → Ruling Out → 
Correct Diagnosis → Treatment]

For each failure mode, connect to the failure ontology from 
Phase 0: failure by whose standard? On what timescale? 
Relative to what benchmark?
```

**Boundary Conditions:**
```
WHERE THE FRAMEWORK BREAKS DOWN

Every framework has scope conditions. This one fails when:
[Specific conditions under which the framework gives 
misleading answers]

What to do when you're outside the framework's scope:
[Honest guidance — including "consult someone who specializes 
in X" when appropriate]
```

**Framework Anti-Patterns (NEW IN v3.2):**
```
FRAMEWORK ANTI-PATTERNS

Anti-patterns are behavioral signatures that indicate the 
framework is actively misleading you. They are the 
metacognitive equivalent of code smells — they don't prove 
something is wrong, but they strongly suggest it.

ANTI-PATTERN 1: [Name]
  IF YOU FIND YOURSELF: [Specific behavior the reader might 
    exhibit — e.g., "forcing every problem into a single 
    vyāpti's pattern", "dismissing evidence because it 
    doesn't fit the framework"]
  THE FRAMEWORK IS LIKELY: [What's going wrong — which 
    inductive bias is distorting your view]
  CORRECTIVE: [Specific action — not "be careful" but 
    "step back and ask [specific question]" or "temporarily 
    adopt [alternative framework] and see if the problem 
    looks different"]

[3–5 anti-patterns, domain-specific]
```

**Framework Stress-Tests (NEW IN v3.2):**
```
FRAMEWORK STRESS-TESTS

These scenarios are designed to make the framework fail. 
Work through them and experience the limits firsthand — 
knowing a bridge has a weight limit is different from 
feeling it flex underfoot.

STRESS-TEST 1: [Name]
  SCENARIO: [A realistic situation specifically constructed 
    to be outside the framework's scope conditions]
  TRY TO APPLY THE FRAMEWORK: [What happens when you do — 
    where it gives misleading or incomplete answers]
  WHAT THIS REVEALS: [Which assumption of the framework is 
    violated, and what alternative approach is needed]
  THE EXPERT'S MOVE: [How an expert recognizes this class 
    of situation and adapts — connecting back to the expert 
    virtues (especially pattern recognition with scope 
    awareness and first-principles recovery)]

[2–3 stress-tests]
```

**Inductive Bias Disclosure:**
```
THE INDUCTIVE BIASES OF THIS GUIDE'S FRAMEWORKS

Every framework in this guide simplifies reality in specific 
ways. Here are the simplifications — and when they mislead:

For each major framework introduced in the guide:
FRAMEWORK: [Name]
WHAT IT ASSUMES: [The inductive bias — what patterns it 
  expects to find]
WHEN THIS HELPS: [Situations where the simplification is 
  useful and approximately correct]
WHEN THIS MISLEADS: [Situations where the bias causes you 
  to see patterns that aren't there or miss patterns that are]
CORRECTIVE: [What to do when you suspect the framework's 
  bias is distorting your view]
```

**Error Museum (include for Types 1, 2, and 5; optional for Types 3 and 4):**
```
THE ERROR MUSEUM

The history of [TOPIC] includes ideas that were wrong — 
but not obviously wrong. They were held by intelligent people 
reasoning carefully from incomplete information.

ERROR 1: [Name]
What was believed: [The wrong idea, presented as a serious 
  intellectual position]
Why it was attractive: [What evidence and reasoning 
  supported it]
What refuted it: [The evidence or argument that 
  overturned it]
What we should learn: [About the limits of our own current 
  knowledge — if smart people were wrong before, what might 
  we be wrong about now?]

[2–3 errors total]
```

**After Part II–III, run the inline assertion checklist:**
```
PART II–III ASSERTION CHECKLIST:
□ All chapters use their assigned structures from Step 2G
□ Structure diversity: [list structures used] — minimum 3 met?
□ All spaced returns due in Parts II–III are present with signal text
□ All resolution ledger entries due in Parts II–III are resolved
□ All confusion-pairs due in Parts II–III have discrimination cases
□ All landscape points in Parts II–III have acknowledgments
□ All hetvābhāsas assigned to Parts II–III are introduced
□ Tacit knowledge blocks: [count] present vs. [minimum required]
  - Each block has case study? [yes/no per block]
  - Each block has experiential simulation (if Medium+ density)? [yes/no]
  - High-contrast debates present (if High density)? [yes/no]
  - Podcast/interview refs present (if High density)? [yes/no]
  - Sources drawn from Tacit Knowledge Source Bank? [yes/no]
□ Decay markers from registry: [count placed] vs. [count due]
□ Chapter references: every chapter has 3–7 annotated sources? [count chapters with references] / [total Parts II–III chapters]
□ Derivation proof sketches from registry: [count placed] vs. [count due in Parts II–III]
□ Cross-domain isomorphism blocks: [count placed] vs. [count due]
□ Metacognitive checkpoints: Part I only (verified in Stage 4). 
  Parts II–III use recalibration checks at Part transitions instead.
□ Framework anti-patterns: [count] — minimum 3
□ Framework stress-tests: [count] — minimum 2
□ Failure mode catalogue present with minimum 3 modes
□ Inductive bias disclosure present
□ At least 1 Structure D (Debate) chapter for Types 3, 4, 5

MISSING ELEMENTS (if any): [List and address before proceeding]
```

═══════════════════════════════════════════
⛔ STAGE 5 GATE — HARD STOP
═══════════════════════════════════════════

SELF-AUDIT:
1. Run the Part II–III Assertion Checklist above. Fix gaps.
2. Produce cumulative ELEMENT TRACKING (Rule 3).
3. List REMAINING ELEMENTS for Stage 6, specifically:
   - Resolution ledger open entries for Part IV
   - All 8 required Part V subsections:
     I. Inquiry Protocol
     II. Vyāpti Quick-Reference (ALL [N] vyāptis)
     III. Hetvābhāsa Quick-Reference (ALL [N] hetvābhāsas)
     IV. Compression Exercise (ALL [N] vyāptis — not a subset)
     V. Diagnostic Questions (min 3, target 5, with 3 depth levels)
     VI. Where to Go (ALL goal types from calibration)
     VII. Composability (sequel hooks + parallel references)
     VIII. Honest Limits
   - Collaborative Learning Appendix: [N] entries for [N] chapters

STOP and present using Rule 1 format.

DO NOT begin Part IV.

---

# ═══════════════════════════════════════════
# STAGE 6: FRONTIER + FRAMEWORK
# ═══════════════════════════════════════════

### PART IV: FRONTIER AND OPEN QUESTIONS

**Purpose:** The honest state of current knowledge. This section models expert epistemic humility.

```
THE EDGE OF CURRENT KNOWLEDGE

✓ ESTABLISHED: [Claims we hold with high confidence, and why]
~ WORKING HYPOTHESIS: [What the field believes but is not 
  settled — and what evidence supports it]
? GENUINELY OPEN: [Questions that remain unresolved, with 
  the crux of disagreement stated]
⚡ ACTIVELY CONTESTED: [Areas where smart people disagree — 
  model Vāda here: present both sides as genuinely 
  seeking truth]

WHERE JALPA EXISTS IN THIS FIELD:
[Honest acknowledgment of areas where researchers argue for 
positions rather than seeking truth — and how to read such 
debates. What incentives exist? What would you need to 
discount when reading arguments from parties with 
those incentives?]

WHAT WOULD RESOLVE THE OPEN QUESTIONS:
[For each open question: what evidence, argument, or 
discovery would settle it]
```

**Resolution Ledger Check:** At this point, review the resolution ledger from Phase 2F. Any remaining open entries that are genuinely unresolved must be placed here as open questions. **No entry may remain unaddressed. List each resolved and open entry explicitly.**

```
RESOLUTION LEDGER — FINAL STATUS:
Entry 1: [Question] → RESOLVED in Chapter [Y] ✓
Entry 2: [Question] → RESOLVED in Chapter [Z] ✓
Entry 3: [Question] → OPEN — placed in Frontier above ✓
[All entries accounted for]
```

---

### PART V: THE FRAMEWORK — HOW TO THINK ABOUT [TOPIC]

**This is the most important part of the guide. It is the distillation of everything into a usable cognitive architecture.**

```
CHAPTER [FINAL]: THE EXPERT'S FRAMEWORK

This chapter does not introduce new concepts.
It shows you how to use everything you've built.

─────────────────────────────────────────────────
I. THE INQUIRY PROTOCOL

When you encounter a new problem or situation in [TOPIC], 
proceed as follows:

STEP 1 — EVIDENCE AUDIT:
What is the epistemic status of the claims involved?
Ask: Is this established (which evidence supports it?), 
working hypothesis, or speculative?

STEP 2 — PATTERN RECOGNITION:
Which of the known situations does this resemble?
Which structural regularities are likely operative?
What would you predict if those regularities hold here?

STEP 3 — SCOPE CHECK:
Are you within the scope conditions of the patterns 
you've identified?
What would indicate you're outside scope?

STEP 4 — REASONING ERROR SCAN:
Which characteristic fallacies are you at risk of 
committing here?
Run a quick check against the catalogue.

STEP 5 — CAUSAL REASONING:
If you intervene on what you think is the cause, what 
specific downstream effect do you predict?
Through what mechanism?
What confounders might mislead you?
What would you observe if you're wrong?

STEP 6 — CALIBRATED CONCLUSION:
What do you believe, with what confidence, on what basis?
What would change your view?

─────────────────────────────────────────────────
II. THE STRUCTURAL REGULARITIES QUICK-REFERENCE

[ALL 5–10 vyāptis from Phase 2, restated here as a usable 
reference, with their scope conditions and causal status.
Cross-reference: verify every vyāpti from the Stage 2 
architecture is present.]

─────────────────────────────────────────────────
III. THE REASONING ERRORS QUICK-REFERENCE

[ALL 5–8 characteristic fallacies from Phase 2, with their 
signatures — brief, scannable.
Cross-reference: verify every hetvābhāsa from the Stage 2 
architecture is present.]

─────────────────────────────────────────────────
IV. COMPRESSION EXERCISE

For EACH structural regularity (not a subset), the compressed 
form experts hold in working memory:

COMPRESSED: [A phrase or mental image — how an expert 
  thinks this in real-time]
DECOMPRESSION: [What that compressed form unpacks into 
  when applied to a specific case]
PRACTICE: Take [concept from Chapter N] and compress it 
  into a single sentence that would let you reconstruct 
  the full reasoning if needed. Then decompress it and 
  check: did the full reasoning survive the compression?

─────────────────────────────────────────────────
V. DIAGNOSTIC QUESTIONS FOR EVALUATING REASONING

When evaluating how someone (including yourself) reasons 
about [TOPIC], these questions reveal depth of understanding:

QUESTION 1: [A question where the answer reveals depth]
  A surface answer sounds like: [X]
  A deeper answer sounds like: [Y]
  The deepest answer includes: [Z — and acknowledges 
    uncertainty about specific aspects]

[3–5 diagnostic questions — minimum 3, target 5]

─────────────────────────────────────────────────
VI. WHERE TO GO FROM HERE

The guide has built a framework. Now the reader needs to 
stress-test it.

FOR EACH GOAL TYPE (from calibration — address ALL of these,
not a subset):
- Readers seeking to read primary literature: 
  [Specific recommended starting points]
- Readers applying to practice: 
  [Specific recommended next steps]
- Readers preparing to teach: 
  [What to pay attention to in their own teaching]
- Readers seeking deeper understanding: 
  [The open problems most worth pursuing]

─────────────────────────────────────────────────
VII. COMPOSABILITY — THIS GUIDE IN CONTEXT

(Drawn from Step 2L Composability Anchors)

ENTRY PREREQUISITES:
This guide assumed you could:
- [Prerequisite 1 — from Step 2L]
- [Prerequisite 2]

EXIT COMPETENCIES:
Having completed this guide, you can now:
- [Competency 1]
- [Competency 2]
- [Competency 3]

SEQUEL: This guide ends at [boundary]. Follow-up directions:

  DIRECTION 1: [Advanced subtopic]
    Entry point: [Which competencies above are prerequisite]
    What this covers: [Scope of the follow-up]

  DIRECTION 2: [Different subtopic]
    Entry point: [Prerequisites]
    What this covers: [Scope]

PARALLEL PERSPECTIVE: This guide treated [TOPIC] as [Type X]. 
A complementary guide built as [Type Y] would emphasize 
[different aspects] — specifically, it would reveal 
[what this guide's lens necessarily conceals].

─────────────────────────────────────────────────
VIII. WHAT THIS GUIDE CANNOT DO

Honest statement of limits:
- Tacit knowledge that requires practice: [Named specifically]
- Depth that requires specialization: [Named specifically]
- Experience that cannot be substituted: [Named specifically]
- The guide's own inductive biases: [Brief restatement — 
  what this framework predisposes you to see and miss]

The goal was to build a framework, not to substitute for 
experience. A framework tells you what questions to ask. 
Experience tells you how to hear the answers.
```

---

### COLLABORATIVE LEARNING APPENDIX

**NEW IN v3.25** — This appendix collects all discussion and teaching exercises for the guide. Each entry is tied to a specific chapter and is designed for use with peers, study groups, or teaching contexts. The guide is fully functional for solo readers without this appendix.

```
─────────────────────────────────────────────────
COLLABORATIVE LEARNING APPENDIX

For each chapter, provide ONE of the following:

CHAPTER [N]: [Chapter Title]
  Type: Discussion / Teaching
  
  🗣️ DISCUSSION: [A question for peer debate — structured 
    so both sides are defensible, exercising Vāda mode. 
    Not "what do you think?" but a genuine crux where 
    informed people disagree.]
    
    Side A would argue: [Position A — strongest version]
    Side B would argue: [Position B — strongest version]
    The crux: [What factual or conceptual question, if 
    resolved, would settle the debate]
  
  OR
  
  🎓 TEACHING: "Explain [this chapter's core concept] to 
    someone who hasn't read this guide."
    
    Key test: Can you explain [specific mechanism] without 
    falling back on the guide's exact phrasing? Where you 
    stumble is where your understanding is receptive, not 
    generative.
    Predicted stumble point: [The aspect most readers find 
    hardest to articulate independently — connects to tacit 
    knowledge if applicable]

[Repeat for every chapter in the guide]

─────────────────────────────────────────────────
USING THIS APPENDIX

For study groups: Work through the guide individually first. 
  Then use these prompts as meeting agendas — one or two 
  chapters per session. Discussion prompts work best when 
  group members have genuinely different answers.

For peer instruction (Mazur method): Each member answers the 
  discussion question independently, then compares. If answers 
  diverge, discuss before revealing the guide's analysis.

For self-teaching: The teaching prompts work solo — try 
  explaining aloud or in writing. The stumble points are 
  diagnostic: they reveal exactly where your understanding 
  needs deepening.
```

═══════════════════════════════════════════
⛔ STAGE 6 GATE — HARD STOP
═══════════════════════════════════════════

SELF-AUDIT:
1. Part IV: All frontier topics have epistemic status markers?
2. Resolution ledger: ALL entries accounted for (resolved or 
   open)? Display the FINAL STATUS table.
3. Part V subsection check:
   □ Inquiry Protocol: present?
   □ Vyāpti Quick-Reference: ALL [N] present? Count them.
   □ Hetvābhāsa Quick-Reference: ALL [N] present? Count them.
   □ Compression Exercise: ALL [N] vyāptis covered? Count.
   □ Diagnostic Questions: [count] — minimum 3?
     Each has surface/deeper/deepest levels? [yes/no]
   □ Where to Go: ALL goal types from calibration addressed?
     [List goal types and confirm each is covered]
   □ Composability: sequel hooks + parallel references present?
     Entry prerequisites and exit competencies stated? [yes/no]
   □ Honest Limits: present?
4. Collaborative Learning Appendix check:
   □ Entry for every chapter? [count] / [total chapters]
   □ Each is a genuine crux (discussion with both sides + crux) 
     or teaching prompt with predicted stumble point? [yes/no]
5. Produce FINAL ELEMENT TRACKING — all counts should equal 
   totals. List any gaps.

STOP and present using Rule 1 format.

Tell the user: "All stages complete. Reply 'continue' for 
Stage 7 (Final Quality Verification), or specify corrections."

---

# ═══════════════════════════════════════════
# STAGE 7: QUALITY VERIFICATION
# ═══════════════════════════════════════════

## PHASE 4: QUALITY VERIFICATION
### Final Verification — Structural Completeness

Most quality checks have already been performed via inline assertions after each Part. This final verification catches anything that spans the full guide.

### CROSS-GUIDE STRUCTURAL CHECKS

Each item must be answered "yes" or the corresponding section must be revised.

**EPISTEMOLOGICAL INTEGRITY**
□ Is every claim labeled by its epistemic status (established / working hypothesis / contested / open)?
□ Does the guide model Vāda (inquiry for truth) when presenting contested areas?
□ Are the pramāṇas appropriate to the domain type (not "proof" in a probabilistic domain; not "studies suggest" in a formal domain)?
□ Is the failure ontology from Phase 0 used consistently — every "works" or "fails" claim traceable to defined benchmarks and timescales?
□ Does the guide itself demonstrate intellectual humility — including acknowledging what the guide cannot do?

**STRUCTURAL COMPLETENESS**
□ Vyāpti coverage: All [N] vyāptis from Stage 2 appear in the Quick-Reference? [List any missing]
□ Hetvābhāsa coverage: All [N] hetvābhāsas from Stage 2 appear in the Quick-Reference? [List any missing]
□ Spaced return coverage: All [N] spaced returns executed? [List any missing]
□ Resolution ledger: All entries resolved or marked open in Part IV? [List any remaining]
□ Confusion-pairs: All [N] discrimination cases present? [List any missing]
□ Landscape points: All [N] landscape acknowledgments present? [List any missing]
□ Decay markers: All [N] registered claims marked? [List any missing]
□ Tacit knowledge blocks: [Count] present vs. [minimum required]?
  - Every block has case study sourced from Tacit Knowledge Source Bank? [yes/no]
  - Experiential simulations present where required by density level? [yes/no]
  - High-contrast debates present where required by density level? [yes/no]
  - Podcast/interview references present where required by density level? [yes/no]
  - Every block has Receptive→Generative bridge with specific practice path? [yes/no]
□ Structure diversity: [List structures used] — minimum 3 different?
□ Chapter references: Every chapter has 3–7 annotated sources? [List any chapters missing references]
□ Derivation proof sketches: All [N] from registry placed as reader-facing summaries in guide text? Each summary names premises, mechanism/vyāpti, hetvābhāsa risk, and source grounding? [List any incomplete]
□ Cross-domain isomorphism blocks: All [N] from map placed? Each has structural match + breakdown + what breakdown teaches? [List any missing]
□ Metacognitive checkpoints: Present in every Part I chapter? [Count] / [total Part I chapters]. Each has calibration probe + self-explanation prompt? [yes/no]
□ Collaborative Learning Appendix: Entry for every chapter? [Count] / [total chapters]. Discussion prompts have both sides + crux? Teaching prompts have predicted stumble point? [yes/no]
□ Framework anti-patterns: [Count] — minimum 3? Each has behavior + cause + corrective? [yes/no]
□ Framework stress-tests: [Count] — minimum 2? Each has scenario + framework failure + expert's move? [yes/no]
□ Composability section in Part V: sequel hooks + parallel references present? [yes/no]

**CALIBRATION INTEGRITY**
□ Does the opening include the analogy anchor from calibration?
□ Are skip markers present for readers above beginner level?
□ Does depth modulation vary by section based on reader goals?
□ Are analogies drawn from the reader's actual background, not generic?
□ Does Part V address all goal types from calibration?
□ Were recalibration checks performed at Part II and Part III transitions?
□ If operating context (Q4) was specified, are examples and failure modes adapted to that context?

**WRITING INTEGRITY**
□ Does every sentence add information not present in adjacent sentences?
□ Is engagement achieved through stakes, surprise, productive confusion, and visible reasoning — not through rhetorical decoration?
□ Does the Pakṣa (Problem) section of each foundational chapter pose a problem for the reader to encounter, not just explain a gap?

### ASPIRATIONAL CHECKS (Design Goals)

These cannot be fully verified in the text but represent what the guide is designed to achieve:

□ Does the guide produce a reader who can handle *novel* situations, not just familiar ones?
□ Do the transfer tests require genuine application to scenarios not covered in the guide?
□ Is tacit knowledge identified and addressed honestly, not papered over?
□ Would a reader with the described background find the analogies illuminating?
□ Does the guide's own writing model the epistemic standards it teaches?
□ Can a reader verify the guide's own non-obvious claims using the derivation summaries and the Ānvīkṣikī tools the guide taught them? (Meta-circular verification — full derivations available via Appendix F Expansion Prompt)

---

## APPENDIX A: HONEST LIMITS OF THIS META-PROMPT

This meta-prompt cannot substitute for:

**Domain knowledge in the AI system generating the guide.** The structure is only as good as the content it organizes. If the AI's knowledge of [TOPIC] is shallow, the structural requirements will reveal this, not conceal it.

**The reader's experience.** The framework the guide builds is a map. Maps tell you how to navigate; they cannot substitute for the journey. The guide should explicitly tell readers this.

**Fully tacit knowledge.** Some expertise genuinely cannot be made fully propositional. Surgery, jazz improvisation, and clinical diagnosis all have tacit components that reading cannot transmit. This meta-prompt includes tacit knowledge markers and the receptive/generative distinction; it does not claim to eliminate the tacit.

**Resolution of genuinely open questions.** Where the frontier of a field is genuinely uncertain, a guide built by this meta-prompt will honestly present that uncertainty. It will not manufacture false confidence for the sake of narrative closure.

**Its own inductive biases.** This meta-prompt assumes knowledge is foundational, propositional, graph-structured, and sequentially teachable. Some domains resist these assumptions. The meta-prompt includes inductive bias disclosure to make this visible, but the biases remain structural features of the framework.

These limits are features, not bugs. A guide that acknowledges what it cannot do is more trustworthy than one that doesn't.

---

## APPENDIX B: v3.0 CHANGELOG

Changes from v2.0, with rationale:

| Change | Rationale |
|---|---|
| **Staged execution model** (7 stages with verified handoffs) | Single-pass generation causes architectural drift; compliance degrades after Part I. Staged execution keeps architecture in active context. |
| **Architecture restatement requirement** (Stage 2 output reproduced at Stage 4 start) | Phase 2 outputs fade from working memory during long generation. Explicit restatement prevents this. |
| **Recalibration at Part transitions** | Reader's relationship to material changes; analogies appropriate for Ch. 1 may not serve Ch. 8. Continuous recalibration prevents stale calibration. |
| **Structure decision table** (Step 2G) | v2.0 gave AI freedom to choose chapter structures at generation time, producing structure homogeneity. Pre-assigned structures with a decision table ensure diversity. |
| **Minimum structure diversity requirement** | Prevents all-Structure-A guides that lack synthesis and diagnostic content. |
| **Inline quality assertions** (after each Part) | v2.0's post-hoc quality gates are unenforceable in single-pass generation. Inline assertions catch gaps as they occur. |
| **Minimum viable guide specification** (3 tiers) | Acknowledges that full compliance may not always be achievable; defines non-negotiable elements. |
| **Explicit spaced return count** (1 per foundational concept) | v2.0 was vague; v3.0 mandates N returns for N foundational chapters. |
| **Confusion-pair and landscape point registry** (Step 2H) | These were implicitly required but not tracked; v3.0 makes them explicit and countable. |
| **Decay marker registry** (Step 2I) | Condition-dependent claims were often missed; pre-identification ensures coverage. |
| **Tacit knowledge density estimate** | Craft and Interpretive domains need more tacit markers; the estimate sets a minimum. |
| **Signal text for spaced returns** | Pre-writing the exact return sentence prevents omission during generation. |
| **Resolution ledger final status display** | Forces explicit accounting of all ledger entries at guide's end. |
| **Compression exercise coverage** | v2.0 allowed subset coverage; v3.0 requires all vyāptis. |
| **Goal-type coverage in Part V** | v2.0 allowed subset coverage of "Where to Go" by goal type; v3.0 requires all. |

---

## APPENDIX C: v3.1 CHANGELOG

Changes from v3.0, with rationale:

| Change | Rationale |
|---|---|
| **Enforced Stage Gate Protocol** (wrapper with hard stops) | v3.0 recommended staged execution but didn't enforce it. v3.1 adds ⛔ hard stops with self-audit checklists at every stage boundary, preventing the system from proceeding with incomplete outputs. |
| **Stage 3: Research Gate** (new stage between Architecture and Generation) | v3.0 generated references from training knowledge at write time, producing hallucinated, stale, or generic citations. The Research Gate uses web search to collect verified sources before prose generation begins, producing a Reference Bank that feeds all chapter references. |
| **Reference Bank** (structured source collection per chapter) | Pre-researched sources organized by chapter with annotations, sourcing gap flags, and vyāpti/hetvābhāsa verification. Eliminates citation hallucination and provides architecture revision signals from research findings. |
| **Chapter REFERENCES section** (required in all 5 structure templates) | Every chapter now ends with annotated references drawn from the Reference Bank, making the guide's pramāṇa visible and verifiable. Includes domain-type-specific guidance (debate sources for Structure D, case sources for Structure E, etc.). |
| **Architecture Revision Flags** (from Research Gate) | Research findings may strengthen, weaken, or challenge Stage 2 architecture decisions. Explicit flags give the user a chance to revise architecture before generation — when changes are still cheap. |
| **"Going Deeper" block** (in Structure A) | Adds per-chapter resource pointers for readers wanting more depth or needing to revisit prerequisites. |
| **Element tracking expansion** | Added chapter references and Reference Bank coverage to Rule 3 cumulative tracking and all assertion checklists. |
| **User control keywords** | Added "continue with corrections", "restart stage [N]", and "status" as explicit control mechanisms for staged execution. |
| **Step 0A: Scope Calibration Search** (light pre-search in Stage 1) | The domain classification is the most consequential decision in the pipeline. A light pre-search (3–5 queries) catches blind spots in the LLM's internal model without distorting architectural reasoning. Produces a Landscape Calibration Note that informs but does not override classification. |
| **Verification-first framing** (Stage 3 Research Gate) | Search biases (recency, SEO, fragmentation, authority confusion) can distort architecture if given too much weight. Explicit framing positions search as verification of LLM-generated architecture, not replacement. Conflicts flagged for user decision, not auto-revised. |
| **Tacit Knowledge Transmission Block** (replaces simple marker) | v3.0's tacit knowledge markers identified gaps but didn't try to close them. The new block uses five vehicles — case studies, experiential simulations, high-contrast debates, practitioner podcasts, and a Receptive→Generative bridge with specific practice paths — to actively transmit tacit knowledge rather than merely acknowledging it. |
| **Step 3G: Tacit Knowledge Source Search** (new Research Gate step) | Searches for real case studies, existing simulations, expert debates, and practitioner podcasts for each anticipated tacit skill. Produces a Tacit Knowledge Source Bank that feeds the Tacit Knowledge Transmission Blocks during generation. |
| **Tacit Knowledge Density Estimate expansion** | Extended from Craft/Interpretive domains only to ALL domain types. Even Formal domains have tacit knowledge. Density levels now specify which vehicles are required (Low: case study; Medium: + simulation; High: all four). Adds anticipated tacit skills list as search targets. |
| **Tacit vehicle tracking** | Added per-vehicle tracking (case studies, simulations, debates, podcasts) to Rule 3 cumulative tracking, Part I/II–III assertion checklists, and Final Quality Verification. |

---

## APPENDIX D: EMPIRICAL VALIDATION FRAMEWORK

**NEW IN v3.2** — Each major design decision in this meta-prompt is anchored to learning science research. This appendix makes those connections explicit, so future versions can evolve based on evidence rather than intuition.

| Design Decision | Research Basis | Key Finding |
|---|---|---|
| **Problem-first presentation** (Pakṣa before Hetu) | Productive failure (Kapur, 2008); Desirable difficulties (Bjork, 1994) | Encountering the problem before the solution produces deeper understanding and better transfer, even when initial performance appears worse. |
| **Spaced returns** (concept revisitation across chapters) | Spacing effect (Cepeda et al., 2006; Ebbinghaus, 1885) | Distributed practice produces substantially better long-term retention than massed practice. Spacing returns across Parts maps to the optimal lag effect. |
| **Transfer tests in novel contexts** | Transfer-appropriate processing (Morris, Bransford & Franks, 1977) | Retrieval practice in varied contexts produces better transfer than studying the same material. Novel scenarios force genuine application rather than pattern matching. |
| **Metacognitive calibration probes** | Dunning-Kruger effect (Kruger & Dunning, 1999); Expert calibration (Keren, 1991; Lichtenstein et al., 1982) | Novices systematically overestimate their understanding. Explicit calibration practice — predicting performance before checking — improves accuracy of self-assessment. |
| **Self-explanation prompts** | Self-explanation effect (Chi, Bassok, Lewis, Reimann & Glaser, 1989; Chi, 2000) | Students who generate explanations for why principles hold learn approximately twice as effectively as those who re-read. The effect is robust across domains. |
| **Discrimination cases** (confusion-pair exercises) | Interleaving and discrimination learning (Rohrer, Dedrick & Stershic, 2015; Kornell & Bjork, 2008) | Interleaved practice that requires discriminating between similar concepts produces better learning than blocked practice, because it forces attention to distinguishing features. |
| **Threshold concepts** (special treatment) | Threshold concepts framework (Meyer & Land, 2003, 2005) | Transformative concepts that irreversibly reorganize understanding require different pedagogical treatment: more preparation, explicit acknowledgment of the shift, and tolerance for productive discomfort during the transition. |
| **Tacit knowledge multi-vehicle approach** | Dreyfus skill acquisition model (Dreyfus & Dreyfus, 1980); Situated cognition (Lave & Wenger, 1991) | Expertise includes non-propositional components that develop through practice in context. Multiple vehicles (cases, simulations, debates, practitioner voices) provide richer approximations of situated experience than text alone. |
| **Collaborative learning hooks** | Peer instruction (Mazur, 1997); Social constructivism (Vygotsky, 1978) | Peer discussion after individual attempt — on conceptual questions where students disagree — produces learning gains exceeding lecture. Articulating and defending positions forces deeper processing. |
| **Derivation transparency** | Epistemic transparency in AI (Doshi-Velez & Kim, 2017); Argumentation theory (Toulmin, 1958) | Structured argumentation with visible premises, warrants, and backing enables evaluation by non-experts. Applied to AI-generated content: showing reasoning chains with typed premises gives readers evaluative power. |
| **Framework anti-patterns** | Metacognitive monitoring (Flavell, 1979; Nelson & Narens, 1990) | Expert metacognition includes error detection — recognizing when one's own framework is producing distorted outputs. Explicit anti-patterns train this monitoring skill. |

These research connections are not exhaustive validation — they are the primary evidence base. The meta-prompt's specific implementations (e.g., the three-layer derivation system with proof sketches, reader-facing summaries, and on-demand full expansions; the vyāpti-based isomorphism mapping) extend beyond what any single study validates. Their design is informed by, but not limited to, the research cited.

---

## APPENDIX E: v3.2 CHANGELOG

Changes from v3.1, with rationale:

| Change | Rationale |
|---|---|
| **Metacognitive Scaffolding** (calibration probes + self-explanation prompts in every chapter) | v3.1 builds first-order domain knowledge but not the second-order skill of monitoring one's own understanding. Calibration probes train the first expert virtue (calibrated uncertainty) as a skill, not just a concept. Self-explanation prompts double retention and transfer (Chi et al., 1989). |
| **Derivation Transparency** (Ānvīkṣikī-native claim verification: pramāṇa → vyāpti chain → kārya-kāraṇa → graph position → hetvābhāsa check → source grounding) | LLMs cannot reliably self-report epistemic confidence. Replaces naive confidence labels with structured derivation chains using the guide's own epistemic tools, making claims tractable, structured, and verifiable. Meta-circular: the reader uses the guide's taught framework to verify the guide itself. |
| **Step 2J: Derivation Registry** (pre-identifies non-obvious claims) | Without pre-identification, derivation notes are omitted during long-form generation. The registry ensures coverage by listing claims that require explicit derivation before prose writing begins. Minimum 1 per Part. |
| **Cross-Domain Transfer Layer** (Step 2K: Isomorphism Map + CROSS-DOMAIN BRIDGE blocks) | v3.1 uses analogies for comprehension. Isomorphisms go further — they map where structural regularities (vyāptis) have twins in the reader's background domain, and crucially, where the correspondence breaks. The breakdown teaches what's unique to this domain. |
| **Q4: Operating Context** (optional Phase 1 calibration question) | Reader background (Q1–Q3) captures *who* the reader is but not *where they operate*. For Type 4 Craft and Type 3 Probabilistic domains, institutional, regulatory, and cultural context materially changes which knowledge applies. Lightweight and optional by design. |
| **Composability Anchors** (Step 2L + Part V Section VII) | Guides don't exist in isolation. Sequel hooks name what the reader has mastered and where to go next. Parallel guide references model inductive bias awareness by showing the same topic through a different domain-type lens. |
| **Framework Anti-Patterns** (proactive failure detection in Part III) | v3.1's "Where the Framework Breaks Down" is reactive. Anti-patterns are specific behavioral signatures that indicate a framework is actively misleading the reader. Framework stress-tests let the reader *experience* the limit rather than being told about it. |
| **Collaborative/Social Learning Hooks** (discussion + teaching prompts per chapter) | Understanding is partly social. Discussion prompts exercise Vāda mode. Teaching prompts test generative (not just receptive) understanding. Lightweight by design — guide remains usable solo. |
| **Appendix D: Empirical Validation Framework** | Anchors each major design decision to learning science research. Makes the meta-prompt's own evidence base visible and evaluable, modeling the epistemic transparency it teaches. |
| **Element tracking expansion** | Added 6 new trackable elements to Rule 3, both assertion checklists, and Final Quality Verification: derivation notes, cross-domain isomorphism blocks, metacognitive checkpoints, collaborative hooks, framework anti-patterns, and composability anchors. |
| **Part V expanded to 8 subsections** (from 7) | Added Section VII: Composability — THIS GUIDE IN CONTEXT, with entry prerequisites, exit competencies, sequel hooks, and parallel perspective references. Previous Section VII (Honest Limits) becomes Section VIII. |

---

## APPENDIX F: DERIVATION EXPANSION PROMPT

**NEW IN v3.25** — Use this prompt to expand any proof sketch from the Derivation Registry into a full 6-component Ānvīkṣikī derivation. Paste it into a new conversation along with: (1) the generated guide document, (2) the Stage 2 architecture output, and (3) the claim number you want expanded.

```
--- BEGIN EXPANSION PROMPT ---

You have been given:
- A learning guide generated by the Ānvīkṣikī meta-prompt
- The Stage 2 architecture that produced the guide
- A claim number from the Derivation Registry

Your task: Expand derivation entry [CLAIM_NUMBER] into the 
full 6-component Ānvīkṣikī derivation format.

For the specified claim, produce:

FULL DERIVATION: [Claim statement from registry]

1. PREMISES (with pramāṇa typing):
   Premise 1: [Statement]
     — Pramāṇa: [pratyakṣa / anumāna / śabda / upamāna]
     — Justification: [Why this pramāṇa type is correct]
     — Source: [Reference Bank entry / training knowledge / 
       specific chapter where established]

   Premise 2: [Statement]
     — Pramāṇa: [type]
     — Justification: [Why this type]
     — Source: [source]

   [Additional premises as needed]

2. VYĀPTI CHAIN (the inference pathway):
   Step 1: [V₁ name] — [What this vyāpti establishes]
   Step 2: [V₂ name] — [How this follows from Step 1]
   ...
   Conclusion: [How the chain terminates in the claim]

   Each step must map to a named vyāpti from the architecture. 
   If a step requires a vyāpti not in the architecture, flag 
   this as a gap.

3. CAUSAL STATUS:
   Classification: [Causal / Structural / Empirical regularity]
   Justification: [Why this classification — what would change 
   if the relationship were a different type?]

4. GRAPH POSITION:
   Parent concepts: [From the dependency DAG]
   Child concepts: [What depends on this claim]
   Implication: [If this claim were false, what else in the 
   guide would need revision?]

5. HETVĀBHĀSA CHECK:
   Primary risk: [Named fallacy from the architecture]
   How it could produce this claim invalidly: [Mechanism]
   Why the derivation escapes this: [Specific reason]
   Secondary risks checked: [Other fallacies considered 
   and ruled out, with reasons]

6. SOURCE GROUNDING:
   Status: [Sourced / Partially sourced / Unsourced]
   For each premise:
     — [Premise 1]: [Source or "unsourced — relies on 
       training knowledge"]
     — [Premise 2]: [Source]
   Verification path for unsourced elements: [What the 
   reader could check to verify independently]

META-CHECK: Does this derivation use the guide's own 
epistemic tools (vyāptis, hetvābhāsas, pramāṇas) to 
verify the guide's own claims? If yes, note the 
meta-circular verification. If not, explain why this 
claim requires external verification tools.

--- END EXPANSION PROMPT ---
```

---

## APPENDIX G: v3.25 CHANGELOG

Changes from v3.2, with rationale:

| Change | Rationale |
|---|---|
| **Minimum Viable Guide Spec updated with v3.2 elements** | v3.2 left its 6 new element types untiered. Under constraint, the system had no guidance on which to sacrifice. All v3.2 elements now assigned to Tier 1 (derivation proof sketches), Tier 2 (anti-patterns, stress-tests, metacognitive checkpoints), or Tier 3 (isomorphisms, composability, collaborative appendix). |
| **Metacognitive checkpoints scoped to Part I only** | Research basis (Kruger & Dunning, Chi et al.) measured calibration interventions in small doses. Per-chapter checkpoints across a 15-chapter guide produce diminishing returns. Part I — where miscalibration is most dangerous — retains full checkpoints. Parts II–IV use existing recalibration checks (now with calibration carry-forward) and transfer tests instead. |
| **Derivation proof sketches replace full 6-component format** | The full derivation format consumed excessive tokens in both architecture (Stage 2) and guide prose (Stages 4–6) relative to its function. Proof sketches preserve the essential reasoning chain (premises, mechanism, risk, grounding) in ~40% of the tokens. Full derivations are recoverable on demand via the Expansion Prompt (Appendix F). |
| **Reader-facing derivation summary** | The 6-component format interrupted narrative flow with structural formalism. The natural-language summary preserves every epistemic function the reader needs (evaluating premises, checking inference validity, learning error awareness, assessing source reliability) without typed notation. |
| **Appendix F: Derivation Expansion Prompt** | Full derivations remain available but are generated on demand rather than inline. The user pastes the guide, architecture, and claim number into a new conversation to produce the complete 6-component derivation. This recovers the verification depth of v3.2 without the token cost. |
| **Collaborative Learning Appendix replaces per-chapter hooks** | Per-chapter collaborative hooks assumed a social context that may not exist and added tracking overhead to every chapter. The appendix collects all discussion and teaching prompts in one place, making them useful for study groups while eliminating per-chapter dead weight for solo readers. Discussion prompts now include both-sides + crux structure; teaching prompts include predicted stumble points. |
| **Element tracking reduced from 20 to 16 items** | Self-audit reliability degrades with list length. Scoping metacognitive checkpoints to Part I, moving collaborative hooks to a single appendix, and simplifying derivation format reduces the per-stage tracking burden while preserving all epistemic functions. |
| **Tier annotations in Rule 3** | Each tracked element now shows its MVG tier, enabling the system to make informed prioritization decisions during generation without consulting the full MVG Spec. |
| **Calibration carry-forward in recalibration checks** | Parts II and III recalibration checks now include the reader's calibration pattern from Part I metacognitive checkpoints, ensuring the metacognitive development arc persists even without per-chapter checkpoints in later Parts. |

---

*Ānvīkṣikī does not promise to give you the answer. It promises to teach you how to look.*

---
```
END OF META-PROMPT v3.25
```
