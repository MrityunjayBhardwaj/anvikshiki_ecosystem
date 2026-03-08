# Ānvīkṣikī Meta² — Design Documentation
## Architecture Decisions and Their Relationship to v3.2

---

## 1. What the Meta² Prompt Is

The Meta² prompt is a conversational interface layer that sits UPSTREAM of the Ānvīkṣikī v3.2 meta-prompt. Its sole output is a precisely constructed user prompt — the "TOPIC + ABOUT ME + Begin with Stage 1" block that v3.2 consumes as its initial input.

It does not generate guides. It does not modify v3.2. It generates the INPUT that v3.2 needs to produce the best possible guide for a specific person.

**The analogy:** If v3.2 is a factory that builds custom learning guides, the Meta² prompt is the intake interview that produces the manufacturing specification. The factory can work without the intake interview — but the specification will be less precise, and the output less personalized.

---

## 2. The Core Problem Meta² Solves

v3.2 is extraordinarily sensitive to input quality. The entire 7-stage pipeline — domain classification, knowledge architecture, research gate, guide generation, quality verification — flows from what the user provides in their first message. But most users don't know what v3.2 needs.

**The information asymmetry:** v3.2 needs 15 categories of information to produce an optimally calibrated guide. The average user provides 2–3 of these (topic + vague background) and expects the system to infer the rest. When v3.2 infers what it should have been told, it makes reasonable but generic assumptions — and the guide reflects those generic assumptions across all 7 stages.

**The specificity gap:** The difference between a good v3.2 prompt and a great one is not length — it's specificity. "I have some business experience" produces a fundamentally different guide than "I've run a 5-person engineering team for 3 years but never managed a P&L, negotiated a contract, or read a balance sheet." The second prompt gives v3.2 precise skip markers, targeted analogy sources, specific known unknowns, and calibrated depth modulation. The first gives it nothing.

**The self-knowledge gap:** Some of what v3.2 needs, users genuinely don't know about themselves. Category 6 (suspected unknowns) and Category 10 (tacit knowledge intuition) require guided reflection. A user who's never thought about what expertise looks like in their target domain can't articulate what the tacit knowledge vehicles should address — but they CAN answer "have you ever watched an expert and thought 'I see what they're doing but not how they decided'?"

**The context gap (NEW IN v3.2):** v3.2 recognizes that the same domain knowledge applies differently depending on where the reader operates. A business guide for EU-regulated fintech differs structurally from one for US startup land. The operating context (Category 13) shapes which examples, failure modes, and practical recommendations the guide produces — but users rarely volunteer this unless asked.

Meta² closes all four gaps through structured conversation.

---

## 3. The 15 Extraction Categories: What Each Does and Why

### Category 1: Topic and Scope → v3.2 Stage 2 (Architecture)

**What it feeds:** The chapter sequence, vyāpti list, and hetvābhāsa list in Stage 2 are directly derived from the topic scope. A precisely scoped topic produces a focused architecture with clear boundaries. A vague topic produces an architecture that tries to cover everything and covers nothing deeply.

**Design decision:** Meta² probes for BOUNDARIES, not just content. "What's excluded" is as important as "what's included" because v3.2's chapter sequence must terminate somewhere. Without explicit boundaries, Stage 2 tends to generate 15–20 chapters that each try to do too little. With boundaries, it generates 8–12 chapters that each do one thing well.

**Design decision:** Meta² checks for scope creep in conversation. Users naturally expand scope as they talk ("oh, and I also need to know about..."). Meta² notes these additions but contains them — either folding them into the existing scope or flagging them as a separate v3.2 run.

---

### Category 2: Domain Type Intuition → v3.2 Stage 1 (Phase 0 Domain Classification)

**What it feeds:** The Phase 0 domain classification is the single most consequential decision in the pipeline. It controls: which pramāṇa framework applies, what vyāptis look like, which chapter structures are required, what the failure ontology examines, how tacit knowledge is treated, and what the expert endpoint looks like.

**Design decision:** Meta² asks about the EPISTEMOLOGICAL CHARACTER of the domain through proxy questions, not by asking "is this a Type 3 or Type 4 domain?" Users don't think in Ānvīkṣikī typology. But they CAN answer "when experts disagree, is one of them wrong or do they just weight things differently?" — which distinguishes Type 1/2 (one is wrong) from Type 4/5 (legitimate variation in judgment).

**Design decision:** Meta² specifically probes for TYPE STRADDLING. Many real-world learning needs span domain types (business is Type 3 economics + Type 4 craft + Type 5 interpretive strategy). The user's intuition about which TYPE DOMINATES helps Stage 1 choose a primary classification with secondary types noted.

---

### Category 3: Prior Exposure → v3.2 Stage 1 (Phase 1 Calibration — Q1)

**What it feeds:** The starting chapter, skip markers, and abbreviation/expansion plan.

**Design decision:** Meta² distinguishes between DOING and KNOWING. Phase 1's Q1 has five levels (None through Active Researcher), but these are crude. A user with "undergraduate formal study" who has never APPLIED the knowledge is calibrated differently from one who has been working in the field for 3 years without formal study. Meta² extracts both the formal exposure level and the practical experience level, giving v3.2 a richer calibration signal.

**Design decision:** Meta² probes for the BOUNDARY of competence. "Where do you go from confident to uncertain?" is more useful than "what do you know?" because v3.2 needs to know where Part I should START, not just that the user has some background.

---

### Category 4: Adjacent Knowledge → v3.2 Stage 1 (Phase 1 Calibration — Q2) + Stage 2 (Step 2K Cross-Domain Isomorphism Map) + All Chapter Analogies

**What it feeds:** The analogy pool that controls EVERY analogy in EVERY chapter of the guide. NEW IN v3.2: also feeds the Cross-Domain Isomorphism Map (Step 2K), which systematically identifies where structural regularities (vyāptis) in the guide's domain have structural twins in the reader's background domain — and where the correspondence breaks.

**Design decision:** This is extracted with the most specificity of any category because it has the highest leverage. A single specific analogy domain ("10 years of neural network architecture design") produces better analogies across 12 chapters than three generic domains ("science, programming, art"). Meta² asks for the user's STRONGEST expertise first, then secondary domains.

**Design decision:** Meta² explicitly asks "what do you naturally compare new things to?" This surfaces the user's actual analogical reasoning patterns, not just their resume. A physicist who naturally thinks in terms of optimization landscapes will get better analogies from that frame than from "physics" generically.

**Design decision (NEW IN v3.2):** Meta² now probes for STRUCTURAL TRANSFER INTUITIONS: "Are there patterns from your field that you suspect might work the same way in [topic]?" This goes beyond analogy (which serves comprehension) to isomorphism (which serves transfer). When a user says "I think pricing might work like gradient descent — iterating toward a local optimum," they're giving v3.2 a pre-formed isomorphism entry for Step 2K: the structural match, a specific breakdown point (pricing has fewer iterations, noisier feedback), and a lesson about what's unique to the target domain.

---

### Category 5: Known Unknowns → v3.2 Stage 1 (Calibration — What to Expand) + Stage 2 (Hetvābhāsa Placement)

**What it feeds:** Two things. First, the "what to expand" field in Phase 1 calibration, which controls depth allocation. Second, the hetvābhāsa placement in Stage 2 — if the user knows they don't understand financial statements, the hetvābhāsas about financial reasoning should be placed in the chapters that teach financial statements, because that's where the user is at maximum risk of the reasoning error.

**Design decision:** Meta² asks for CONCRETE gaps, not general ones. "I don't know finance" gives v3.2 nothing. "I cannot read a balance sheet, I don't know what EBITDA means, and I can't evaluate whether a business is profitable from its financial statements" gives v3.2 three specific chapter targets and three specific hetvābhāsa placement candidates.

**Design decision:** Meta² probes for STUCK POINTS — places where the user has tried to learn and failed. These are signals of threshold concepts (Step 2D). If the user says "I've tried to learn accounting three times and it never clicks," that's evidence that accrual accounting may be a threshold concept requiring the expanded 1.5x treatment.

---

### Category 6: Suspected Unknowns → v3.2 Stage 2 (Resolution Ledger + Hetvābhāsa Design)

**What it feeds:** The resolution ledger (questions raised early, resolved later) and the tacit hetvābhāsa design. When a user suspects they're making a mistake but can't identify it, that's EXACTLY the kind of reasoning error a hetvābhāsa should name and make visible.

**Design decision:** This is the hardest category to extract, which is why Meta² approaches it INDIRECTLY. Direct questions ("what don't you know that you don't know?") are paradoxical. Instead, Meta² asks about feelings, intuitions, and anxieties: "what nags at you?" and "if an expert watched you work, what mistake would they notice first?" These questions access pre-verbal intuitions that the user CAN articulate with prompting.

**Design decision:** Meta² treats partial, uncertain answers as highly valuable. A user who says "I think my pricing is probably wrong but I'm not sure" gives v3.2 a resolution ledger entry ("Is the user's pricing strategy sound?") and a hetvābhāsa candidate ("The Intuition Pricing Trap — when domain experts set prices based on what feels right rather than market analysis"). These are the highest-value inputs for the guide because they address what the user actually needs most.

---

### Category 7: Learning Goals → v3.2 Stage 1 (Phase 1 — Q3) + Stage 6 (Part V — Where to Go)

**What it feeds:** Depth emphasis in Phase 1 and, critically, the Part V "Where to Go" section which MUST address every goal type listed in calibration.

**Design decision:** Meta² pushes for AT LEAST 3 goals because the v3.2 Part V specification requires coverage of ALL goal types. If the user provides only one goal, Part V produces a thin, single-path conclusion. With 3–5 goals, Part V becomes a rich, multi-path navigation tool that serves the reader across different contexts and timeframes.

**Design decision:** Meta² maps extracted goals to v3.2's five recognized goal types (intuitive understanding, read primary literature, apply to problem, teach others, understand expert mindset). This ensures the generated prompt uses language v3.2's Phase 1 recognizes, preventing miscategorization.

**Design decision:** Meta² distinguishes EXPLICIT goals ("I want to understand finance") from IMPLICIT goals. A user building a company implicitly needs to teach/explain business concepts to their team — even if they don't list "teach this subject" as a goal. Meta² surfaces these implicit goals.

---

### Category 8: Specific Context → v3.2 Calibration + Analogy Selection + Application Layer

**What it feeds:** The "what to expand" field (areas directly relevant to the user's goal), application-layer content in chapters (transfer tests, worked examples), and domain-specific dynamics that the guide should call out.

**Design decision:** Meta² asks "why NOW?" because urgency and context shape what the guide should prioritize. A user learning business management because they just got funded has different priorities than one learning it "eventually." The former needs cash flow and hiring immediately; the latter can follow a more theoretical sequence.

**Design decision:** Meta² extracts CONSTRAINTS because v3.2's Craft (Type 4) treatment depends on understanding the user's constraint structure. A solo founder with no team, limited capital, and high technical capability faces different constraints than a well-funded team lead. These constraints become the "goal structure" and "constraint structure" inputs for Type 4 domain classification.

---

### Category 9: Failure/Risk Intuition → v3.2 Stage 1 (Phase 0 Failure Ontology) + Part III (Anti-Patterns + Stress-Tests)

**What it feeds:** The Failure Ontology Output, which defines failure across four dimensions (what counts as failure, relative to what, on what timescale, vs. insufficient information). Every subsequent claim in the guide about "works" or "fails" must be traceable to this ontology. NEW IN v3.2: also feeds framework anti-patterns (behavioral signatures that indicate the framework is misleading the user) and framework stress-tests (scenarios designed to make the framework fail).

**Design decision:** Meta² asks about failure concretely and personally rather than abstractly. "What does failure look like in business management?" produces a generic answer. "What would happen if you priced your services 50% too low for six months?" produces a specific, visceral answer that feeds a concrete failure ontology.

**Design decision:** Meta² probes IRREVERSIBILITY specifically because v3.2's failure ontology distinguishes reversible from irreversible failures. This distinction changes how aggressively the guide treats risk — irreversible failure domains get more hetvābhāsa coverage and more cautious framing.

---

### Category 10: Tacit Knowledge Intuition → v3.2 Stage 1 (Tacit Knowledge Density Estimate)

**What it feeds:** The density level (Low/Medium/High), which controls:
- Minimum tacit knowledge block count
- Which vehicles are required per block (case study only → all four)
- Whether a "Limits of Propositional Instruction" section is needed in Part III
- The anticipated tacit skills list that drives Stage 3's Step 3G search

**Design decision:** Meta² asks about OBSERVATIONS OF EXPERTISE rather than about tacit knowledge directly. Users don't think in terms of "tacit knowledge density." But they CAN answer "have you ever watched someone do this and thought 'how did they know to do THAT?'" This surfaces the user's own sense of how much of the domain resists explicit instruction.

**Design decision:** Meta² asks about LEARNING PREFERENCES among the four vehicles. "Would you rather have a case study, a simulation, a debate between experts, or a podcast of an expert thinking out loud?" The user's preference doesn't change the density level (that's structural), but it helps v3.2 know which vehicles to invest in most heavily.

---

### Category 11: Depth vs. Breadth → v3.2 Word Allocation + Depth Modulation

**What it feeds:** The word allocation by domain type table in Stage 4 and the depth modulation calibration artifact.

**Design decision:** Meta² frames this as a TRADEOFF, not a preference. "Would you rather be 80% competent fast or 95% competent thoroughly?" makes the cost explicit. This produces more honest answers than "do you want depth or breadth?" which most users answer "both."

**Design decision:** Meta² extracts effort willingness because it constrains the realistic depth of the guide. A user willing to spend 20 hours with a 50-page guide is calibrated differently from one wanting a 2-hour primer.

---

### Category 12: Learning Style → v3.2 Calibration Artifacts + Tone Modulation

**What it feeds:** The calibration artifacts (analogy anchor, skip markers, depth modulation) and the implicit tone decisions the guide makes.

**Design decision:** This is the LOWEST PRIORITY category among the original 12. Meta² extracts it when the conversation naturally surfaces it but does not force it. v3.2's structural machinery handles most of what "learning style" addresses — the architecture ensures proper sequencing, the threshold concept treatment handles difficult material, and the tacit knowledge blocks handle experiential learning. What remains is mostly tone, which v3.2 handles adequately from the other categories.

**Design decision:** Meta² asks about PAST LEARNING SUCCESSES, not preferences. "How did you learn [your area of expertise]?" is more diagnostic than "how do you like to learn?" People's actual learning patterns are more predictive than their self-reported preferences.

---

### Category 13: Operating Context → v3.2 Stage 1 (Phase 1 Calibration — Q4)

**NEW IN v3.2.** v3.2 added Q4 to Phase 1 Calibration: an optional question about the reader's operating context — jurisdiction, regulatory environment, institutional type, or cultural context.

**What it feeds:** When specified, the operating context constrains examples, failure modes, and practical recommendations throughout the guide. A business guide for a reader in EU-regulated healthcare produces different case studies, compliance considerations, and failure modes than one for a US startup founder. This constraint propagates through Stages 4–6, shaping the application layer of every chapter.

**Design decision:** Meta² treats this as a CONDITIONALLY IMPORTANT category. For Type 4 (Craft) and Type 3 (Probabilistic) domains, operating context is often the difference between a useful guide and a misleading one — legal advice that's correct in one jurisdiction is wrong in another. For Type 1 (Formal) domains, operating context is usually irrelevant (mathematics doesn't change by jurisdiction). Meta² probes lightly and notes when the category doesn't apply rather than forcing extraction.

**Design decision:** Meta² listens for IMPLICIT context cues throughout the conversation. Users often mention their jurisdiction, institutional type, or regulatory environment in passing (e.g., "I'm building a fintech in India") without flagging it as important. Meta² catches these cues and confirms them during the gap check, because users typically don't realize their context constrains which domain knowledge applies.

**Design decision:** Meta² pairs Category 13 extraction with Category 8 (Specific Context) in conversation flow. The distinction is: Category 8 captures SITUATION (what triggered the learning need, what they're doing, what's at stake), while Category 13 captures ENVIRONMENT (the regulatory, institutional, and cultural container they operate within). Both are about context, but they feed different v3.2 subsystems.

---

### Category 14: Composability and Learning Trajectory → v3.2 Stage 2 (Step 2L Composability Anchors) + Stage 6 (Part V Section VII)

**NEW IN v3.2.** v3.2 added composability as an architectural concern: every guide explicitly defines its position in a broader knowledge graph — what it presumes the reader knows, what it certifies, and where it points next.

**What it feeds:** Step 2L Composability Anchors, which define entry prerequisites, exit competencies, sequel directions (1–2 follow-up learning paths with entry points), and parallel perspective references (the same topic treated as a different domain type). These render in Part V Section VII: "Composability — This Guide in Context."

**Design decision:** Meta² extracts SEQUEL DIRECTION — what the reader wants to learn AFTER this guide. This prevents the common failure where Part V's sequel hooks are generic ("learn more about [topic]") rather than specific ("having mastered business fundamentals, the reader can pursue either financial modeling as a Type 1 formal discipline or strategic leadership as a Type 4 craft discipline"). When Meta² knows the reader's trajectory, v3.2 can tailor exit competencies to match the entry prerequisites of the next guide.

**Design decision:** Meta² probes for PARALLEL LENS AWARENESS. A reader who sees machine learning through a Formal (Type 1) lens might benefit from knowing that a Craft (Type 4) guide would emphasize different things. Meta² asks: "Do you think about [topic] primarily through the lens of [their background]? Would a different lens be useful?" This feeds the parallel perspective references in Part V, which model the seventh expert virtue: inductive bias awareness.

**Design decision:** Meta² pairs Category 14 extraction with Category 7 (Learning Goals) in conversation flow. Sequel direction is a natural extension of "what do you want to be able to do?" and parallel perspective is a natural extension of "understand the expert's mindset." Bundling them avoids adding extra turns.

---

### Category 15: Social Learning Context → v3.2 Stages 4–6 (Collaborative Hooks)

**NEW IN v3.2.** v3.2 places a collaborative learning hook in every chapter — either a structured discussion prompt (exercising Vāda mode) or a teaching prompt (testing generative understanding).

**What it feeds:** The collaborative hooks are generated regardless of this input (they're structural requirements), but the hooks are MORE USEFUL when calibrated to the reader's social learning reality. A solo learner benefits from teaching prompts (which test generative understanding through self-explanation). A reader with a peer group benefits from discussion prompts (which exercise the ability to defend positions). A reader who must discuss this in professional settings benefits from prompts calibrated to professional discourse norms.

**Design decision:** This is the LOWEST PRIORITY of all 15 categories. Meta² extracts it when the conversation naturally surfaces it — typically alongside Category 12 (Learning Style). One question is usually sufficient. The guide remains fully usable for solo learners regardless; this category ensures the collaborative hooks are well-targeted rather than generic.

**Design decision:** Meta² does NOT probe deeply here because v3.2's collaborative hooks are lightweight by design. Over-investing in social learning context extraction would produce a prompt that over-specifies how the reader should interact with the guide — which contradicts v3.2's design principle that the guide remains usable solo.

---

## 4. Conversation Design Decisions

### 4.1: Why Conversational, Not Form-Based

A form (even a sophisticated one) cannot probe follow-ups, notice tensions, or surface Category 6 (suspected unknowns). The conversational format allows:

- **Follow-up depth:** When a user says "I have some programming experience," a form accepts it. A conversation asks "what kind? Web? Systems? ML? How many years? What's the most complex thing you've built?"
- **Tension surfacing:** When a user says they want breadth but their context demands depth in finance, a conversation can name that tension and help resolve it.
- **Indirect extraction:** Category 6 and 10 require approaching the question from an unexpected angle. Conversations allow this; forms don't.
- **Context-aware bundling:** Categories 13, 14, and 15 (new in v3.2) are often extractable alongside related core categories rather than requiring dedicated questions. A conversation naturally bundles operating context with situation, composability with goals, and social learning with learning style.

### 4.2: Why 5–9 Turns

Too few turns (1–3) can't cover 15 categories with adequate depth. Too many turns (11+) produces user fatigue and diminishing returns. The 5–9 range allows:

- 1–2 questions per turn × 7 turns = 14 questions, covering all categories
- Room for follow-ups on the most important categories
- A confirmation turn before output
- Natural conversation pacing that doesn't feel like an interrogation
- Categories 13–15 are bundled with related categories (8, 7, 12 respectively), keeping the turn count manageable despite 3 additional categories

### 4.3: Why 1–2 Questions Per Turn

Cognitive load management. Users who face 5 questions in a single message:
- Answer the first two thoroughly and skim the rest
- Feel interrogated rather than engaged
- Lose the conversational thread that surfaces Category 6 insights

Two questions is the maximum that maintains conversational flow while making progress through the categories.

### 4.4: Why Reflection Before Output

The Phase D reflection serves three purposes:
1. **Error correction:** The user catches misunderstandings before they're baked into the prompt
2. **Gap surfacing:** Hearing their situation reflected back often triggers "oh, and I forgot to mention..."
3. **Commitment:** Users who hear their own goals stated clearly and confirm them are more likely to follow through on the guide

---

## 5. Output Format Design Decisions

### 5.1: Why This Specific Prompt Structure

The output format maps directly to v3.2's input parsing:

| Prompt Section | v3.2 Component It Feeds |
|---|---|
| TOPIC + Scope | Stage 1 Phase 0 classification + Stage 2 chapter sequence |
| Background | Phase 1 calibration level + analogy pool |
| Adjacent knowledge (bulleted) | Phase 1 Q2 → analogy pool (listed explicitly so v3.2 doesn't miss any) |
| Structural transfer patterns (bulleted) | Stage 2 Step 2K → Cross-Domain Isomorphism Map (reader's structural intuitions pre-seed the mapping) |
| What I do NOT know (bulleted) | Phase 1 "what to expand" + Stage 2 hetvābhāsa placement |
| What I suspect (bulleted) | Stage 2 resolution ledger + hetvābhāsa design |
| Learning goals (bulleted with "ALL") | Phase 1 Q3 + Part V "Where to Go" (the "ALL" keyword triggers v3.2's full goal coverage) |
| Analogy domains (bulleted) | Phase 1 analogy pool (restated for emphasis — v3.2 uses these for EVERY analogy) |
| Operating context | Phase 1 Q4 → context-adapted examples, failure modes, recommendations |
| Tacit knowledge note | Stage 1 tacit density estimate + Stage 3 Step 3G search targets |
| Depth preference | Word allocation + depth modulation |
| Learning trajectory | Stage 2 Step 2L → Composability Anchors + Part V Section VII |
| Social learning | Stages 4–6 → collaborative hook calibration (discussion vs. teaching prompts) |
| "Begin with Stage 1." | Triggers v3.2's Rule 6 first message behavior |

### 5.2: Why Bulleted Lists for Specific Sections

v3.2 parses the user prompt and uses it across multiple stages. Prose paragraphs are harder for the LLM to decompose than bulleted lists. The sections that feed MULTIPLE downstream stages (adjacent knowledge feeds analogies + calibration + isomorphism map; learning goals feed calibration + Part V) are bulleted to ensure each item is individually accessible during architecture and generation.

### 5.3: Why "ALL of these — address each in Part V"

This is a v3.2-specific trigger. Part V's "Where to Go" section specification reads: "FOR EACH GOAL TYPE (from calibration — address ALL of these, not a subset)." By including the word "ALL" in the learning goals section header, the prompt pre-loads the instruction that v3.2 needs to hear when it reaches Part V generation — preventing the common failure where Part V addresses only 1–2 of 4 stated goals.

### 5.4: Why "Begin with Stage 1."

This triggers v3.2's Rule 6 (First Message Behavior), which ensures the system responds ONLY with Stage 1 and does not attempt to generate architecture or prose in the first turn. Without this trigger, some LLM implementations may attempt to run multiple stages in a single response, which v3.2's staged execution model is specifically designed to prevent.

### 5.5: Why the Three New Sections (Operating Context, Learning Trajectory, Social Learning)

**Operating context** is placed after the analogy domains because v3.2's Phase 1 processes Q4 (operating context) after Q2 (adjacent knowledge). Placing it in the same sequence as v3.2's internal processing reduces the chance of the LLM skipping it during Phase 1 parsing.

**Learning trajectory** is placed after depth preference because composability is an architectural concern (Step 2L) that builds on the reader's full calibration profile. By the time v3.2 reads this field, it has all the context it needs to design precise sequel hooks and parallel perspective references.

**Social learning** is placed last because it's the lowest-priority input. v3.2's collaborative hooks are structural requirements regardless — this field only improves their targeting.

---

## 6. Quality Audit Design Decisions

### 6.1: The "Different Guide" Test

The final quality check asks: "Would this prompt produce a DIFFERENT guide for THIS person than for any other person studying the same topic?" This is the meta-test for calibration quality. If two people with different backgrounds, goals, and contexts would receive the same prompt, the extraction failed. The guide would be generic — precisely what v3.2's calibration system is designed to prevent.

### 6.2: Why ≥ 3 Learning Goals

Empirically, users who provide 1 learning goal get a guide with a monotone emphasis. Users who provide 3+ get a guide with differentiated depth across Parts I–V. The threshold of 3 ensures enough variation to produce a structurally diverse guide while remaining achievable for most users.

### 6.3: Why Category 6 Is Flagged as High-Value

Suspected unknowns are the highest-leverage input because they feed both the resolution ledger AND the hetvābhāsa design. A user who says "I think my pricing is probably wrong but I don't know how" gives v3.2:
- A resolution ledger entry (raised in the pricing chapter, resolved in the strategy chapter)
- A hetvābhāsa candidate (the pricing intuition fallacy)
- A tacit knowledge signal (pricing judgment is partly tacit)
- A calibration signal (this user needs depth in pricing, not breadth)

No other single input feeds four v3.2 subsystems simultaneously.

### 6.4: Why Structural Transfer Patterns Are Audited (NEW IN v3.2)

v3.2's Cross-Domain Isomorphism Map (Step 2K) can work without reader-supplied transfer intuitions — it will generate isomorphisms from the analogy pool alone. But reader-supplied patterns are higher-value because they reveal which structural parallels the reader has ALREADY noticed (and can build on) vs. which are genuinely novel. The audit checks for their presence because they're easy to miss during extraction but significantly improve Step 2K output.

### 6.5: Why Operating Context Is Checked (NEW IN v3.2)

The audit verifies that operating context is either explicitly specified OR explicitly marked as not applicable. The "explicitly not applicable" case matters because it prevents v3.2 from inferring a context that doesn't exist. A prompt that says nothing about operating context might lead v3.2's Phase 1 to guess — and a wrong guess here produces mismatched examples and failure modes throughout the guide.

---

## 7. Edge Case Handling

### 7.1: Vague Users

Some users resist specificity. Meta² handles this gracefully by generating the best possible prompt with [NEEDS SPECIFICS] markers rather than refusing to produce output. The rationale: a 70%-calibrated v3.2 prompt still produces a better guide than no prompt at all. The markers tell the user exactly where to improve.

### 7.2: Multi-Topic Users

v3.2 is designed for a single domain per run. Multi-topic users get a recommendation to prioritize and run sequentially. The rationale: v3.2's architecture (vyāpti list, dependency map, chapter sequence) assumes a coherent domain. Forcing two domains into one run produces an architecture that serves neither well.

### 7.3: Topics That Don't Need v3.2

v3.2 is heavy machinery for building deep expertise frameworks. If the user's actual need is a tutorial, a reference, or a simple explanation, Meta² says so. This prevents waste — both of the user's time and of the computational resources required for a 7-stage execution pipeline.

### 7.4: Users With Draft Prompts

Meta² can audit existing prompts against the quality checklist. This handles the case where the user has already written a prompt (perhaps from the v3.2 documentation) but suspects it could be improved. Meta² identifies gaps and asks targeted questions to fill them.

### 7.5: Users Mentioning Regulations or Jurisdictions (NEW IN v3.2)

When a user mentions specific regulations, jurisdictions, or institutional contexts in passing, Meta² flags this as Category 13 material and confirms it explicitly. Users often don't realize that their operating context is architecturally important — they mention "I'm in EU healthcare" as background color, not as a structural constraint. Meta² catches these signals and ensures they're captured precisely in the operating context field.

---

## 8. What Meta² Deliberately Does NOT Do

**It does not explain v3.2.** The user doesn't need to know about vyāptis, hetvābhāsas, or staged execution. They need to know about their own learning goals and context. Meta² extracts what v3.2 needs without requiring the user to understand v3.2's internal machinery.

**It does not make domain judgments.** Meta² does not classify the domain, identify vyāptis, or plan the architecture. Those are v3.2's job. Meta² extracts the RAW SIGNAL that v3.2 transforms into structural decisions.

**It does not limit scope to v3.2's categories.** The 15 extraction categories are designed to be BROADER than what v3.2 strictly requires. Extra context (Category 8: specific situation, Category 9: failure intuition) gives v3.2 richer material to work with even though not every piece of information maps to a single v3.2 field. Richer input produces richer output.

**It does not guarantee quality.** Meta² improves the PROBABILITY of a great guide by improving input quality. It cannot compensate for weak LLM domain knowledge, insufficient context windows, or v3.2 execution failures. The guide quality is still bounded by the generating system's capabilities.

**It does not over-extract lightweight categories.** Categories 13 (Operating Context), 14 (Composability), and 15 (Social Learning) were added in Meta² v1.1 to support v3.2 features, but they are designed to be extracted alongside related core categories. Meta² does not add conversational bloat for marginal extraction gains.

---

## 9. Relationship Map: Meta² Output → v3.2 Pipeline

```
META² EXTRACTION          v3.2 STAGE           GUIDE OUTPUT
─────────────────         ──────────           ────────────

Category 1 ──────────┐
(Topic + Scope)       ├──→ Stage 1 ──────────→ Domain Classification
Category 2 ──────────┤    (Domain Audit)       Failure Ontology
(Domain Type)         │                         Pramāṇa
Category 9 ──────────┘                         
(Failure Intuition)

Category 3 ──────────┐
(Prior Exposure)      ├──→ Stage 1 ──────────→ Starting Chapter
Category 4 ──────────┤    (Calibration)        Analogy Pool
(Adjacent Knowledge)  │    Q1–Q4                Skip Markers
Category 11 ─────────┤                         Depth Modulation
(Depth/Breadth)       │                         Operating Context
Category 12 ─────────┤                         adaptation
(Learning Style)      │
Category 13 ─────────┘
(Operating Context)

Category 10 ─────────────→ Stage 1 ──────────→ Tacit Density Level
(Tacit Intuition)          (Tacit Estimate)     Required Vehicles
                                                Anticipated Skills

Category 1 ──────────┐
(Scope sub-domains)   ├──→ Stage 2 ──────────→ Vyāpti List
Category 5 ──────────┤    (Architecture)       Hetvābhāsa List
(Known Unknowns)      │                         Chapter Sequence
Category 6 ──────────┘                         Resolution Ledger

Category 4 ──────────────→ Stage 2 ──────────→ Cross-Domain
(Structural transfer       (Step 2K)            Isomorphism Map
 patterns)

Category 14 ─────────────→ Stage 2 ──────────→ Entry Prerequisites
(Learning Trajectory)      (Step 2L)            Exit Competencies
                                                Sequel Directions
                                                Parallel Perspectives

[No direct extraction]───→ Stage 2 ──────────→ Derivation Registry
                           (Step 2J)            (internally generated
                                                 from architecture)

Category 10 ─────────────→ Stage 3 ──────────→ Tacit Knowledge
(Tacit skills list)        (Research Gate)      Source Bank

Category 4 ──────────────→ Stages 4–6 ────────→ All Analogies
(Analogy Domains)          (Generation)         in Every Chapter

Category 4 ──────────────→ Stages 4–6 ────────→ Cross-Domain Bridge
(Structural patterns)      (Generation)         blocks in chapters

Category 5 ──────────────→ Stages 4–6 ────────→ Hetvābhāsa
(Known Unknowns)           (Generation)         Placement

Category 13 ─────────────→ Stages 4–6 ────────→ Context-adapted
(Operating Context)        (Generation)         examples, failure
                                                modes, recommendations

Category 15 ─────────────→ Stages 4–6 ────────→ Collaborative hooks
(Social Learning)          (Generation)         calibration (discussion
                                                vs. teaching prompts)

[No direct extraction]───→ Stages 4–6 ────────→ Metacognitive
                           (Generation)         checkpoints (structural,
                                                not input-dependent)

[No direct extraction]───→ Stages 4–6 ────────→ Derivation notes
                           (Generation)         (from registry)

Category 9 ──────────────→ Stage 5 ──────────→ Framework Anti-Patterns
(Failure Intuition)        (Part III)           Framework Stress-Tests

Category 7 ──────────────→ Stage 6 ──────────→ Part V:
(All Learning Goals)       (Frontier +          Where to Go
                            Framework)

Category 14 ─────────────→ Stage 6 ──────────→ Part V Section VII:
(Learning Trajectory)      (Part V)             Composability —
                                                This Guide in Context

Category 8 ──────────────→ Stages 4–6 ────────→ Transfer Tests
(Specific Context)         (Generation)         Worked Examples
                                                Application Layer
```

---

## 10. Version History

| Version | Date | Changes |
|---|---|---|
| Meta² v1.0 | Initial release | 12 extraction categories, 5-phase conversation flow, output format mapped to v3.1 input specification, quality audit checklist, edge case handling |
| Meta² v1.1 | 2026-02-23 | Updated for v3.2 alignment: added 3 new extraction categories (13: Operating Context → Q4, 14: Composability → Step 2L, 15: Social Learning → collaborative hooks). Expanded Category 4 (Adjacent Knowledge) to probe for structural transfer patterns feeding Step 2K Cross-Domain Isomorphism Map. Expanded Category 9 to note its feed into framework anti-patterns and stress-tests. Added 3 new output format fields (operating context, learning trajectory, social learning). Updated quality audit with 3 new checks. Updated relationship map to include all v3.2 pipeline elements including derivation registry (Step 2J) and metacognitive checkpoints as internally generated. Updated conversation flow from 4–8 to 5–9 turns with bundling strategy for lightweight categories. All v3.1 references updated to v3.2. |

---

*The Meta² prompt does not teach. It listens — carefully enough that the teaching can be precisely aimed.*
