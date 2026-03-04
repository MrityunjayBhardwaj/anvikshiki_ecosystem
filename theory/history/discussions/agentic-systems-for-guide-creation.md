# Agentic Systems for End-to-End Guide Creation

## The Core Insight: What v3.26 Was Actually Solving

v3.26's entire prevention stack (C1–C21) exists because a **single LLM fights context decay** across a 20,000–40,000 word generation run. Voice drifts. Forward hooks get forgotten. Terminology shifts. Fingerprints consume context.

An agent team solves the *underlying problem* directly:
- **Persistent external state** replaces the reliance on context
- **Specialization** gives each agent a narrower, better-executed task
- **Parallelization** collapses multi-day sequential work into concurrent runs
- **Agent-to-agent review** replaces self-auditing (which LLMs are notoriously bad at)

The meta-prompt's stage gate protocol maps almost perfectly onto an agent handoff protocol. The architecture is already there — it just needs to be externalized.

---

## The Agent Team

```
┌─────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR                        │
│  Manages stage gates, element tracking, user interface  │
└─────────┬───────────┬──────────┬──────────┬────────────┘
          │           │          │          │
    ┌─────▼────┐ ┌────▼────┐ ┌──▼──────┐ ┌▼──────────┐
    │ ANALYST  │ │ARCHITECT│ │RESEARCH │ │CONTINUITY │
    │ Stage 1  │ │ Stage 2 │ │ SWARM   │ │  AGENT    │
    └──────────┘ └─────────┘ │ Stage 3 │ └───────────┘
                             └─────────┘
    ┌──────────────────────────────────────────────────┐
    │              CHAPTER AUTHORS (pool)              │
    │           Stages 4–6, one per session            │
    └──────────────────────────────────────────────────┘
    ┌──────────┐ ┌──────────┐ ┌──────────────────────┐
    │  VOICE   │ │VERIFIER  │ │   DEVIL'S ADVOCATE   │
    │SPECIALIST│ │Stage 7–8 │ │  (cross-cutting)     │
    └──────────┘ └──────────┘ └──────────────────────┘
```

---

### 1. Orchestrator Agent

**The stage gate enforcer.** Prevents any agent from starting before the previous gate is satisfied. This is the single biggest gain over single-LLM execution — the stage gate is physically impossible to skip, not just instructed not to skip.

**Responsibilities:**
- Maintains the **Element Tracking Dashboard** (Rule 3 counts) as a live database updated after each chapter
- Routes user "continue" / "revise: X" commands to the correct agent
- Decides session groupings using the Session Plan (Step 2P)
- Holds the master architectural documents as structured JSON (not prose in context)
- Presents stage gate summaries to user in Rule 1 format

**What it doesn't do:** Generate any guide content. Pure coordination.

**Tools:** Database read/write, message routing, structured comparison (expected vs. produced counts), user-facing output formatting

---

### 2. Domain Analyst (Stage 1)

Focused entirely on Step 0A + Phase 0 + Phase 1. This agent's output is a **structured data object**, not prose — the Orchestrator stores it as the canonical Stage 1 record.

**Responsibilities:**
- Runs 3–5 targeted web searches (Step 0A calibration)
- Classifies domain type with justification
- Produces failure ontology (all 4 dimensions)
- Produces reader calibration (Q1–Q4)
- Produces tacit knowledge density estimate with anticipated skills list

**Key enhancement over single-LLM:** The analyst's search results are stored permanently. Later agents (especially the Research Swarm) can query "what tacit skills did Stage 1 identify?" without needing Stage 1 in context.

---

### 3. Architect (Stage 2)

The most complex single-agent task. Produces all 15 architectural outputs. Should be a **full-capability model** (Opus-class) given the critical nature of Stage 2.

**Key enhancements over single-LLM:**

The Architect's outputs are stored as **structured data**, not a prose document:

```
Architecture Store (external DB):
├── vyaptis[]            — each a structured record with all fields
├── hetvabhasas[]        — same
├── dependency_map       — actual DAG with MECE annotations
├── threshold_concepts[]
├── spaced_return_plan[] — chapter N → chapter M → signal text
├── resolution_ledger[]  — with status field (OPEN/RESOLVED/Part IV)
├── chapter_sequence[]   — each chapter: id, structure, action_title,
│                          emotional_beat, debate_plan, vyapti_anchors
├── forward_ref_matrix[] — typed cross-chapter connections
├── exit_narrative       — prose + verification checklist results
├── session_plan[]       — session → chapters[] assignments
└── ...
```

This means **any agent at any stage** can query "what is the signal text for the spaced return of concept X?" without loading the entire Stage 2 output into context.

**Devil's Advocate Challenge at Stage 2 Gate:** Before the Orchestrator accepts Stage 2, the Devil's Advocate runs a targeted challenge:
- Are all MECE checks genuinely exhaustive? (challenges each one)
- Can all action titles survive the Disagreement test? (attempts to write a weaker version)
- Are emotional beats sequenced to comply with constraints?
- Do crux statements resolve to Empirical or Values-based? (flags scope/definitional ones)

---

### 4. Voice Specialist (Pre-Stage 3)

Dedicated to generating the Voice Calibration Document. Small but critical.

**Enhancement:** The voice sample is stored as a **vector embedding + raw text** in the persistent store. The Session Start Protocol for every Chapter Author session begins with this agent injecting the voice sample into the Chapter Author's context — not relying on the author to retrieve it.

Additionally, this agent **evaluates voice consistency** during Stage 7–8 by comparing each chapter's tone markers (from fingerprints) against the voice baseline.

---

### 5. Research Swarm (Stage 3)

The biggest **parallelization opportunity** in the entire pipeline.

**v3.26 single-LLM problem:** Stage 3 must search for sources for every chapter, every vyāpti, every hetvābhāsa, every tacit skill — sequentially. For a 12-chapter guide with 8 vyāptis and 6 hetvābhāsas, that's 30+ search threads done one at a time.

**Agent swarm approach:**

```
Research Coordinator
├── Chapter Source Agents (one per chapter, run in parallel)
│   └── Each: foundational + contemporary + worked example + dissenting
├── Vyāpti Verifiers (one per vyāpti, run in parallel)
│   └── Each: empirical support + known exceptions
├── Hetvābhāsa Documenters (one per fallacy, run in parallel)
│   └── Each: documented instance + literature
├── Decay Status Agents (one per decay marker)
│   └── Each: current status + most recent source
└── Tacit Knowledge Sourcers (one per anticipated skill)
    └── Each: case studies + simulations + debates + podcasts (by density)
```

All run **simultaneously**. Research Coordinator assembles the Reference Bank from results.

**Wall-clock time:** A 12-chapter guide's Stage 3 goes from ~45 minutes sequential to ~5 minutes parallel.

---

### 6. Chapter Author Pool (Stages 4–6)

The Chapter Authors are **not all running at once**. They run in **session order** as defined by the Session Plan. But within a session, two Chapter Authors can run in parallel if the emotional beats allow it and Chapter N+1 doesn't reference Chapter N's specific prose.

**The critical mechanism: Session Start Protocol is automated**

In single-LLM execution, the Session Start Protocol (C10) relies on the LLM to remember to load 6 things before generating. In agent execution:

```
Session Initializer (sub-agent of Orchestrator):
1. Query Architecture Store → inject relevant Forward Reference Matrix rows
2. Query Fingerprint DB → inject all prior fingerprints
3. Retrieve Voice Sample → inject
4. Retrieve last chapter's final 3 paragraphs from output store
5. Execute voice warm-up (50-100 word throwaway, discard)
6. Inject resolved hook targets (Open hooks due in this chapter)

→ Only then does Chapter Author receive its generation prompt
```

This makes the protocol **structurally enforced**, not instructed.

---

### 7. Continuity Agent

The most novel agent in the team. Does not generate guide content. Maintains all state needed for cross-chapter coherence.

**Manages three persistent stores:**

**Fingerprint Database (C11)**
After every chapter, extracts the 13-section fingerprint and stores it as a structured record. Enforces:
- **Terminology Lock:** If a Chapter Author uses a term that doesn't match the first-mention registry, flags it before the chapter is accepted
- **Spaced Return Verification:** Before Chapter M generates an SR, queries the fingerprint for the original chapter N's exact formulation
- **Appendix Accumulation (C21):** Extracts appendix contributions and adds to the Appendix Draft

**Forward Hook Ledger (C12)**
- Before each chapter: queries ledger for OPEN hooks targeted at this chapter → injects into Chapter Author's context as "required resolutions"
- After each chapter: updates ledger with newly planted seeds + marks resolved hooks
- At Stage 7: produces complete ledger status for verification

**Element Tracking Dashboard (Rule 3)**
Updates the cumulative count of every structural element after each chapter:

```
After Chapter 5 complete:
  Vyāptis referenced: 4/8
  Hetvābhāsas introduced: 3/6
  Spaced returns executed: 2/5
  [... all 20+ tracked elements]
  → "Remaining work" report generated for Orchestrator
```

---

### 8. Verifier (Stages 7–8)

**Stage 7:** Assembles the complete guide from the output store. Runs all inline quality assertions as a batch, identifies OPEN hooks, checks appendix completeness.

**Stage 8 (Safety Net):** Runs the 6 revision types in prescribed order:

```
TYPE 1 (Calibration): Voice Specialist compares fingerprint tone markers
TYPE 2 (Cross-chapter): Continuity Agent runs final hook ledger scan
TYPE 3 (Redundancy): Continuity Agent checks first-mention registries
TYPE 4 (Appendix): Continuity Agent validates appendix completeness
TYPE 5 (Threshold): Verifier checks threshold chapter structure
TYPE 6 (Debate crux): Verifier checks all debate chapters
```

---

### 9. Devil's Advocate Agent (Cross-Cutting)

Runs **at three specific points**, not continuously:

**At Stage 2 Gate:** Challenges architectural decisions (vyāpti formulations, action titles, emotional arc, debate cruxes)

**At Stage 3 Gate:** Challenges the Reference Bank — looks for sourcing gaps that were marked "training knowledge" but could actually be sourced

**At Stage 7 Gate:** Attempts to find logical inconsistencies between fingerprints

The Devil's Advocate's outputs go to the **user**, not the Orchestrator — these are judgment calls, not mechanical fixes.

---

## How Agents Enhance Beyond the Meta-Prompt Design

### Enhancement 1: Architecture as Queryable Data, Not Text

In single-LLM execution, "reproduce the Stage 2 architecture" (Rule 2) means pasting 3,000 words of text into context. In an agent system:

```
"What is the signal text for the spaced return of Vyāpti 3 in Chapter 7?"
→ Architecture Store returns: "Now that you've seen [X]..."
```

This eliminates both the context cost and the retrieval error of searching through prose.

### Enhancement 2: Parallel Research at Scale

~35 independent research threads done simultaneously instead of sequentially. This isn't just a speed improvement — it enables **genuinely exhaustive research** that a single-LLM context budget would force you to abbreviate.

### Enhancement 3: Cross-Agent Review Replaces Self-Auditing

Routing the Stage 2 Gate self-audit to the Devil's Advocate (a different agent with fresh context, no attachment to the architecture it's critiquing) produces significantly more reliable gap detection.

### Enhancement 4: Voice Consistency as a Quantitative Signal

The Voice Specialist can run **embedding similarity comparisons** between the voice sample and each chapter's fingerprint tone markers — converting a subjective "does this feel consistent?" into a detectable signal.

### Enhancement 5: Exhaustive Element Tracking Without Context Pressure

A dedicated Continuity Agent with no other job updates exact counts after each chapter with no degradation possible.

### Enhancement 6: Session Isolation Prevents Contamination

Each Chapter Author runs in a **fresh context** populated only with what's needed: the relevant Architecture Store entries, prior chapter fingerprints, voice sample, and Forward Reference Matrix rows. It doesn't carry the accumulated prose of all prior chapters — only the structured *memory* of them.

---

## Resource Allocation: What Runs Where and When

```
STAGE 1   │ Domain Analyst (1 agent)          │ Sequential
STAGE 2   │ Architect (1, Opus-class)          │ Sequential
          │ Devil's Advocate gate review       │ After Architect completes
PRE-S3    │ Voice Specialist (1)               │ Sequential
STAGE 3   │ Research Swarm (up to 35 parallel) │ Parallel
          │ Research Coordinator (assembles)   │ After swarm completes
S4-S6     │ Session Initializer                │ Before each session
          │ Chapter Authors (1-3 per session)  │ Parallel within session
          │ Continuity Agent                   │ After each chapter
STAGE 7   │ Verifier                           │ Sequential
          │ Devil's Advocate gate review       │ After Verifier
STAGE 8   │ Voice Specialist + Continuity      │ Parallel (different types)
          │ Verifier (final)                   │ After revision
```

**Cost-sensitive allocation:** Not every agent needs Opus-class. The Architect and Chapter Authors do. The Research Swarm, Continuity Agent, and Verifier can use Sonnet-class. The Devil's Advocate should be Opus-class.

---

## The Single Most Important Design Decision

**All persistent state lives outside any agent's context.** The Architecture Store, Fingerprint Database, Forward Hook Ledger, Element Tracking Dashboard, Reference Bank, Voice Sample, and Output Store are **external databases** that agents query and update. No agent is responsible for "remembering" anything across a session boundary.

This is what the prevention stack (C1–C21) was trying to compensate for — the LLM's inability to reliably "remember" across 40,000 words. An agent team eliminates the need for compensation by solving the underlying problem: durable, queryable, agent-agnostic state.

The meta-prompt's instruction to "reproduce the Stage 2 architecture as a header before Stage 4" becomes unnecessary. Any agent that needs a piece of the architecture queries it from the store. The information is always current, always exact, always free of context-budget tradeoffs.

---

## What This Looks Like in Practice

A user provides a topic and reader profile. From that point:

1. **Domain Analyst** classifies, calibrates, estimates tacit density → ~10 minutes
2. **Architect** produces all 15 outputs, stored as structured data → ~30 minutes; Devil's Advocate challenges → user reviews and approves
3. **Voice Specialist** produces voice sample → ~5 minutes; user approves tone
4. **Research Swarm** (35 parallel threads) → ~10 minutes wall-clock; Research Coordinator assembles Reference Bank
5. **Chapter sessions** (3–4 sessions of 2–3 chapters each): each session runs Session Initializer → Chapter Author → Continuity Agent → user approval loop
6. **Verifier** assembles and checks the complete guide
7. **Stage 8** runs targeted revisions only for flagged items (ideally: none)

Total: a guide that would take a single LLM 6–8 hours of careful staged execution becomes a **2–3 hour process** with minimal human decision points — just the stage gate approvals the meta-prompt already requires.
