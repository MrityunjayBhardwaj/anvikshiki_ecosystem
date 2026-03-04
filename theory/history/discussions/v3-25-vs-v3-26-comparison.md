# v3.25 vs v3.26 — Comparison

## v3.25 → v3.26: What Changed and Why

### High-Level: Core Structural Change

**v3.25: 7 stages** | **v3.26: 8 stages** (adds a Safety Net Revision as Stage 8)

The fundamental philosophy shift in v3.26 is moving from **post-hoc quality repair** to **prevention-first in-process quality control**. v3.25 relied on Stage 7 to catch and fix problems after generation. v3.26 adds 21 prevention mechanisms (C1–C21) built into the generation process itself, so Stage 8's manifest should theoretically be empty.

---

### Additions in v3.26 by Stage

#### Stage 2: Knowledge Architecture (5 major additions)

| What | v3.25 | v3.26 |
|------|-------|-------|
| **Vyāpti format** | Causal classification only | + Epistemic status block: confidence level, evidence quality, guide rendering rule (C8) |
| **Step 2C (Dependency Map)** | Standard DAG | + MECE assertions at every branching point — exhaustiveness is *mandatory* (C2) |
| **Step 2G (Chapter Structures)** | Structure assignment only | + Action Titles (must pass 3 tests: Disagreement, Domain Specificity, Compression) + Emotional Beat arc (5 beats with sequencing constraints) + Debate planning with crux statements (C1, C3, C4) |
| **Step 2N: Forward Reference Matrix** | Not present | Pre-plans all cross-chapter connections with type (Foreshadow / Incomplete Picture / Concept Extension / Synthesis / Tension) and planned rendering text (C5) |
| **Step 2O: Exit Narrative** | Not present | 150–200 word prose paragraph simulating completed reader in a realistic scenario; also serves as architectural verification (C6) |
| **Step 2P: Session Plan** | Not present | Assigns chapters to generation sessions with constraints on session size and part-transition placement (C7) |
| **Architecture output count** | 12 items | 15 items |

#### PRE-STAGE 3: Voice Calibration Document (entirely new)

v3.26 inserts a new stage between Stage 2 and Stage 3. Before any guide prose is generated, produce a **500–800 word voice sample** (not part of the guide) as one of three formats: middle-chapter excerpt, author's note, or expert conversation. This gives Chapter 1 a voice reference point that previously only later chapters benefited from (C9).

#### Stage 3: Research Gate (identical between versions)

Stage 3 content is unchanged.

#### Stages 4–6: Guide Generation (4 new in-process controls)

| Control | Purpose |
|---------|---------|
| **Session Start Protocol (C10)** | 6-step mandatory checklist before each generation session: load fingerprints, load voice sample, load forward hook ledger, re-read last chapter's final paragraphs, do a 50–100 word voice warm-up |
| **Chapter Fingerprints (C11)** | 13-section structured summary generated immediately after every chapter (~200–300 words). Tracks: core insight, concepts defined (first-mention registry with exact definitions), vyāptis treated, tone markers, forward hooks planted. Highest context preservation priority |
| **Forward Hook Ledger (C12)** | Running ledger of all planted forward references with status (OPEN / RESOLVED). Checked before each chapter to resolve pending promises and plant new ones |
| **Simulation Quality Checklist (C13)** | 5-point check before finalizing any transfer test or simulation: genuine ambiguity, non-obvious expert insight, novice-expert divergence point, real-world messiness, reader context fit |
| **Tacit Knowledge Quality Test (C14)** | Derivability test: if someone with only explicit knowledge could write it, it's "expert analysis" not tacit knowledge. Must also demonstrate felt experience |

#### Stage 6 Addition: Scenario Forks (C17)

For every `?` or `⚡` question in Part IV that affects the framework: produce 2–3 resolution scenarios each with framework impact, practical implications, observable monitoring signals, and current evidence lean. Forces epistemic honesty about uncertainty.

#### Stage 6 Addition: Framework Intent Statements (C19)

At the start of each Part (II–V), include a ~100-word reader-facing statement: what you can now do, what cognitive move this enables, what specific vyāptis are now operational, and explicitly what this does NOT yet give you.

#### New Stage 8: Safety Net Revision (Phase 5)

Checks six failure types in a specific order:
1. **Calibration** (voice drift across chapters) — compare fingerprint tone markers
2. **Cross-chapter connections** — scan Forward Hook Ledger for OPEN hooks
3. **Redundancy** — check first-mention registries for duplicate definitions
4. **Appendix quality** — check completeness
5. **Threshold resistance** — verify threshold chapters have ≥30% resistance
6. **Debate crux** — verify debates have genuine cruxes

Each failure item diagnoses WHY the prevention mechanism failed (process problem → reinforce; architecture problem → note for v3.27; irreducible → accept).

---

### What Problems These Changes Solve

| Problem in v3.25 | v3.26 Solution |
|-----------------|----------------|
| Voice inconsistency across long guides | Voice Calibration Document + Session Start Protocol (C9, C10) |
| Repeated/inconsistent terminology across chapters | Chapter Fingerprint first-mention registry + Terminology Lock rule (C11) |
| Forward references that get forgotten | Forward Reference Matrix planned upfront + Hook Ledger tracked (C5, C12) |
| Vague chapter titles that don't state insights | Action Titles with 3-test validation (C1) |
| Emotional pacing problems (too many hard chapters in sequence) | Emotional Beat arc with sequencing constraints (C3) |
| False debates that dissolve on examination | Crux statement requirement + scope/definitional reclassification (C4) |
| Overconfident vyāpti claims | Epistemic status block with rendering rules (C8) |
| Underspecified guide coverage (missing domain areas) | MECE assertion requirement (C2) |
| Abstract competency promises | Exit Narrative with concrete scenario (C6) |
| Inefficient multi-session workflow | Session Plan with constraints (C7) |
| Fake tacit knowledge (just analysis relabeled) | Tacit Knowledge Quality Test (C14) |
| Weak simulations that don't create productive confusion | Simulation Quality Checklist (C13) |
| Unresolved open questions without decision framework | Scenario Forks (C17) |
| Unclear what each Part builds | Framework Intent Statements (C19) |

---

### Summary Characterization

**v3.25** is a well-structured staged generation system with strong architectural control (vyāptis, hetvābhāsas, spaced returns, etc.) that relies primarily on Stage 7 quality verification to catch problems after generation.

**v3.26** keeps everything in v3.25 and adds a systematic **prevention stack** — 21 controls (C1–C21) built into the generation process itself. The goal is that a guide generated in v3.26 arrives at Stage 7/8 needing minimal revision, because voice consistency, cross-chapter coherence, terminology stability, and forward reference integrity are maintained continuously during generation rather than fixed afterward.
