# Improving the Meta-Prompt for Concrete Sourcing

## The Actual Problem: What "LLM Understanding" Means as a Source

When an LLM writes "research shows X" or states a vyāpti confidently, it's doing one of four things — and the meta-prompt currently doesn't distinguish between them:

```
Type A — DIRECTLY WITNESSED: Claim appears verbatim or
         near-verbatim in a specific training document.
         (Reliable, but source is unknown and unverifiable)

Type B — SYNTHESIZED: Claim is the LLM's compression of
         multiple training documents that pointed in this
         direction. No single source states it this way.
         (Plausible but potentially no single source exists)

Type C — INTERPOLATED: Claim is what the LLM inferred as
         likely true given adjacent knowledge. Never
         explicitly stated anywhere.
         (Could be correct or could be confabulation)

Type D — HALLUCINATED: Claim sounds right stylistically
         but has no basis in training data.
         (Indistinguishable from Type A at generation time)
```

The v3.26 "Sourced / Partially sourced / Unsourced" trichotomy treats all four as a single gradient. It doesn't — because it can't. The LLM doesn't know which type it's producing.

**The current Stage 3 flaw:** Stage 3 searches for sources *after* Stage 2 architecture is built. If a source can't be found, the claim stays in the guide with a disclaimer. This is confirmation-bias baked into the process — you build from training knowledge and then search for validation.

---

## The Fundamental Fix: Source-First Reconciliation

### Add Step 2Q: Architecture Reconciliation (runs after Stage 3)

Currently the pipeline is:
```
Stage 2 (architecture from training) → Stage 3 (verify) → Stage 4 (generate)
```

It needs to be:
```
Stage 2 (architecture proposed) → Stage 3 (verify) →
Stage 2Q (RECONCILE) → Stage 4 (generate sourced content)
```

Stage 2Q forces the architecture to be rebuilt around what's actually sourceable:

```
STEP 2Q: ARCHITECTURE RECONCILIATION

For each element in Stage 2, apply the sourcing outcome
from Stage 3:

VYĀPTI RECONCILIATION:
  For each vyāpti V:

  IF sourced (primary source found, read, confirmed):
    → Status: VERIFIED. Render with full confidence per
      epistemic status. Cite inline.

  IF partially sourced (supporting evidence found but
    no direct statement of the vyāpti):
    → Status: SYNTHESIZED. Mandatory caveat language.
      Document what the sources say vs. what the vyāpti
      claims. Render as "evidence converges on..."
      not "research shows..."

  IF unsourced (no external evidence found):
    → DECISION REQUIRED:
      (a) DEMOTE to "Working Hypothesis" — rendered in
          guide with explicit box: "This is a reasoned
          inference, not a documented regularity."
      (b) REMOVE — if the vyāpti is not critical to the
          architecture, remove rather than present
          unsourced content
      (c) REPLACE — substitute with an adjacent vyāpti
          that IS sourceable and covers similar ground
      → Cannot proceed to Stage 4 with unsourced vyāptis
        at foundational status. No exceptions.

CLAIM RECONCILIATION (chapter-level):
  For each chapter's core claims:

  IF foundational source found AND read:
    → Assign [RefCode] (e.g., Ch3-F1)
    → Record: what the source actually says (direct quote
      or close paraphrase)
    → Record: inference gap (what guide's claim adds
      beyond source — must be minimal for Tier 1 claims)

  IF no foundational source found:
    → Claim must be restructured as explicitly derived
      from named vyāptis (Ānvīkṣikī inference, not
      factual assertion)
    → Or: downgraded to "practitioner observation" with
      named practitioners
    → Or: removed

ARCHITECTURE DELTA REPORT:
  Produce a diff of Stage 2 vs. Stage 2Q architecture:
  - Vyāptis promoted (stronger sourcing than expected)
  - Vyāptis demoted (weaker sourcing than expected)
  - Vyāptis removed (unsourceable)
  - Claims restructured (moved from factual to derived)
  - New elements added (discovered during Stage 3)

  → Present to user for approval before Stage 4.
```

---

## Replace the Sourcing Trichotomy With a Provenance Classification

The current "Sourced / Partially sourced / Unsourced" doesn't tell you *what kind* of sourcing exists. Replace with:

```
PROVENANCE CLASSIFICATION (required for every vyāpti and
every non-trivial claim):

CLASS 1 — DIRECTLY CITED
  Definition: A specific source makes this claim
    explicitly. The guide is reporting what the source
    says.
  Required: Author + Title + Year + DOI/URL + page/
    section + verbatim or close paraphrase of the
    relevant passage
  Render as: "[Claim] (Smith, 2019, p.47)"
  Verification: Source must be READ, not just found.

CLASS 2 — SYNTHESIZED FROM SOURCES
  Definition: No single source makes the claim, but
    multiple identified sources together imply it.
  Required: At least 2 specific sources + explicit
    statement of what each source contributes +
    the inferential step the guide takes
  Render as: "Drawing from [A] and [B], the pattern
    suggests..." — never "research shows"
  Verification: Each source must be READ.

CLASS 3 — FIELD CONSENSUS
  Definition: So well-established that standard
    textbooks treat it as settled.
  Required: Name of the specific textbooks/handbooks
    where this appears as established knowledge
  Render as: Standard assertion, with textbook in
    bibliography
  Verification: Must appear in at least 2 standard
    texts for the domain.

CLASS 4 — ATTRIBUTED EXPERT OPINION
  Definition: Specific named expert(s) hold this view,
    documented in a retrievable source.
  Required: Named expert + source where they state it
    (paper, book, documented interview, talk)
  Render as: "[Expert] argues that..." — never as
    established fact
  Verification: Source must be accessible.

CLASS 5 — REASONED FROM VYĀPTIS
  Definition: Claim is derived through Ānvīkṣikī
    inference chain from sourced vyāptis. Novel
    application of established principles.
  Required: Full derivation proof sketch showing
    which sourced vyāptis carry each inference step
  Render as: "Following from [V1] and [V3], we can
    derive..." — with derivation visible
  Only acceptable for: novel applications of
    established frameworks, not for the frameworks
    themselves

CLASS 6 — WORKING HYPOTHESIS (flagged)
  Definition: Reasoned inference that cannot be
    grounded in sourced vyāptis or external evidence.
  Required: Explicit declaration + reasoning shown
  Render as: Mandatory callout box:
    ⚠️ WORKING HYPOTHESIS
    This claim is the author's reasoned inference,
    not a documented finding. Treat as hypothesis
    to be tested, not established knowledge.
  Restricted to: Non-foundational claims only.
    Foundational claims cannot be Working Hypotheses.

PROHIBITED:
  ✗ "Research shows X" without Class 1 or 2 citation
  ✗ "Studies have found X" without specific studies
  ✗ "Experts agree X" without named experts + sources
  ✗ "It is well-known that X" without Class 3 textbooks
  ✗ Any factual claim at Tier 1 or Tier 2 without
    Class 1, 2, or 3 provenance
```

---

## Add Source Reading Verification (The Hallucination Trap)

Stage 3 currently asks the agent to *find* sources. Finding is insufficient — an LLM can find a plausible-sounding paper that doesn't say what the claim says, or hallucinate a URL that doesn't exist.

```
STEP 3H: SOURCE READING VERIFICATION

For every source identified in Steps 3A–3G:

EXISTENCE CHECK:
  □ URL resolves to an accessible page?
  □ DOI resolves to an actual paper?
  □ Book exists in at least one library catalog?
  → If URL/DOI fails: search for alternative access
    (Semantic Scholar, OpenAlex, author's page,
    institutional repository)
  → If book: verify via WorldCat or Google Books
    preview at minimum

CONTENT CHECK (required — not optional):
  □ Retrieve the specific passage that supports the
    claim (section, page, paragraph)
  □ Record: exact quote or close paraphrase of
    what the source says
  □ Record: what the guide's claim says
  □ Record: the inference gap (difference between
    what source says and what guide claims)
  □ Is the inference gap justified by the domain's
    vyāptis? If not — the source does not support
    the claim. Find a better source or downgrade.

AUTHORITY CHECK:
  □ Is this source authoritative in the domain?
    — Peer-reviewed journal? (which tier?)
    — Established textbook? (which edition/publisher?)
    — Practitioner report? (which organization?)
    — Primary document? (is it the original?)
  □ Has this source been cited/used by others in
    the domain? (evidence of reception)
  □ Any known criticisms, retractions, or updates?

RECENCY CHECK (domain-specific thresholds):
  Type 1 (Formal): foundational sources can be older;
    recent sources needed for applications
  Type 2 (Mechanistic): 10 years for stable mechanisms;
    3 years for fast-moving areas
  Type 3 (Probabilistic): 5 years for effect sizes;
    new meta-analyses supersede older ones
  Type 4 (Craft): practitioner context changes —
    verify regulatory/market claims are current
  Type 5 (Interpretive): primary sources timeless;
    interpretive frameworks may require recent
    engagement with the literature

OUTPUT FORMAT:
  SOURCE VERIFICATION: [RefCode]
  Title: [...]
  Exists: ✅/❌
  Accessible via: [URL / DOI / Library]
  Relevant passage: "[direct quote or paraphrase]"
  Guide claim: "[what the guide will say]"
  Inference gap: [None / Minimal / Significant]
  Gap justified by: [vyāpti name, or "unjustified —
    downgrading claim"]
  Authority: [tier]
  Recency: [acceptable / borderline / stale]
  Verdict: ACCEPTED / ACCEPTED-WITH-CAVEAT / REJECTED
```

---

## Inline Citation Protocol for Guide Chapters (Stages 4–6)

Every chapter needs a citation obligation built in:

```
INLINE CITATION REQUIREMENT (all Stages 4–6):

Before generating any chapter:
  Load the chapter's Reference Bank entries (from
  Stage 3, verified by Step 3H)
  Load the chapter's Derivation Registry entries
  (for Class 5 claims)

During generation, apply these rules:

RULE C-1: EVERY FACTUAL CLAIM NEEDS A TAG
  Every claim that could be contested must have
  an inline citation tag: (→ RefCode) in the prose

  Acceptable: "Firms that misalign incentives
  systematically underperform (→ Ch4-F1, Ch4-F2)"

  Not acceptable: "Research has consistently shown
  that misaligned incentives lead to underperformance"

RULE C-2: VYĀPTI INVOCATIONS ARE NOT CITATIONS
  When a vyāpti is applied to explain a situation,
  that is Class 5 (reasoned) — it must be presented
  as inference, not as a factual claim.

  Acceptable: "Following V1 (incentive-outcome
  alignment), we can infer that..."

  Not acceptable: "Incentive misalignment causes
  failure" [stated as bare fact without provenance]

RULE C-3: PROHIBITED PHRASES
  These phrases are banned in guide prose because
  they obscure provenance:
  ✗ "Research shows..." → Replace with specific (→ RefCode)
  ✗ "Studies have found..." → Name the studies
  ✗ "It is widely accepted..." → Class 3 requires textbooks
  ✗ "Experts agree..." → Class 4 requires named experts
  ✗ "Evidence suggests..." → What evidence? (→ RefCode)
  ✗ "In practice..." → Whose practice? Case or Class 4?

RULE C-4: WORKING HYPOTHESES ARE MANDATORY BOXES
  Any claim with Class 6 provenance must appear in
  a visually distinct callout box — it cannot be
  embedded in normal prose where it blends with
  sourced claims.

SELF-AUDIT (per chapter, before completing):
  □ Every factual claim has a (→ RefCode) tag?
  □ No prohibited phrases present?
  □ Working Hypotheses are in callout boxes?
  □ All RefCodes map to verified sources in
    Step 3H output?
  □ Inference gaps for Class 2/5 claims are stated?
```

---

## Conflict Documentation Protocol

When Stage 3 finds that two sources disagree on a claim:

```
CONFLICT DOCUMENTATION (Step 3F, expanded):

SOURCE CONFLICT [N]:
  Claim in architecture: [statement from Stage 2]

  Source A says: "[direct quote]" (→ RefCode-A)
    — In favor of: [position]
    — Date: [year]
    — Evidence type: [RCT / meta-analysis / case /
                      observational / theoretical]

  Source B says: "[direct quote]" (→ RefCode-B)
    — In favor of: [opposing/modifying position]
    — Date: [year]
    — Evidence type: [...]

  Conflict type:
    □ Empirical — same question, different findings
    □ Scope — both true but in different conditions
    □ Temporal — A was true then, B reflects update
    □ Definitional — different meaning of key term

  Resolution:
    EMPIRICAL → Add to Resolution Ledger as contested.
      Present both in guide as a Vāda debate. Do NOT
      pick a winner without stronger evidence.
    SCOPE → Convert to contextual analysis. "In
      condition X: A holds. In condition Y: B holds."
    TEMPORAL → Use more recent source. Note the update
      explicitly in the guide with a decay marker.
    DEFINITIONAL → Resolve definition first, then
      recheck if conflict survives.

  Guide treatment: [how this conflict will appear
    in the relevant chapter — must be explicit,
    not hidden]
```

---

## Strengthen Stage 2 Vyāpti Format

Add a mandatory Provenance Pre-Assignment to every vyāpti at Stage 2:

```
VYĀPTI [N]: [Name]
Statement: [...]
Causal status: [...]
Epistemic status: [...]

PROVENANCE PRE-ASSIGNMENT:
  Anticipated class: [1 / 2 / 3 / 4 / 5]
  Justification: [why this class is expected —
    what kind of evidence the domain typically has]
  Search targets for Stage 3:
    Primary: "[specific search query for foundational source]"
    Verification: "[query for independent replication]"
    Exception: "[query for known boundary conditions]"

  Minimum sourcing threshold:
    [Class 1 or 2 required for causal vyāptis]
    [Class 1, 2, or 3 acceptable for structural vyāptis]
    [Class 3 or 4 minimum for empirical regularities]

  If threshold not met in Stage 3:
    → Automatic demotion to Working Hypothesis status
    → Chapter anchor must be redesigned to not rest
      on this vyāpti as foundational
```

---

## What This Changes About the Stage Architecture

```
v3.26 flow:
Stage 2 → Stage 3 → [Stage 4 generation]

Improved flow:
Stage 2 → Stage 3 → Step 3H (reading verification)
        → Step 2Q (reconciliation)
        → User approval of reconciled architecture
        → Stage 4 (generation against sourced architecture)
```

The new **Stage 2Q gate** is the most important addition — it is the point where the guide's epistemic foundation is either confirmed as solid or restructured until it is. Nothing enters Stage 4 that hasn't cleared this gate.

---

## Integration With the Logic Engine

In the logic programming architecture, provenance becomes metadata on rules — not documentation:

```prolog
% Vyāpti with full provenance attached
vyapti(V1,
    statement("Incentive misalignment causes systematic underperformance"),
    provenance(class1,
        source("Jensen & Meckling 1976",
               "Theory of the Firm",
               doi("10.1016/0304-405X(76)90026-X"),
               passage("...agency costs arise when..."),
               verified(true))),
    causal_status(causal),
    confidence(high),
    decay_risk(low)).

% Inference engine checks provenance before using rule
can_apply_vyapti(V, Context) :-
    vyapti(V, _, provenance(Class, Source), _, _, _),
    source_verified(Source),
    Class \= class6,  % Working hypotheses cannot be
                      % applied as inference rules
    decay_not_triggered(V, Context).

% Unsourced vyāpti — flagged, not silently used
can_apply_vyapti(V, _) :-
    vyapti(V, _, provenance(class6, _), _, _, _),
    log_warning("Working hypothesis applied: ~w", [V]),
    fail.  % Cannot chain from working hypothesis
```

This means when an agent uses the logic engine to reason, it **cannot silently use unsourced vyāptis as inference rules**. The provenance constraint is enforced computationally, not by instruction.

---

## Summary of Changes to Add to the Meta-Prompt

| Where | What |
|-------|------|
| Stage 2, Step 2A | Provenance Pre-Assignment block on every vyāpti |
| Stage 2, Step 2J | Derivation registry must specify provenance class per claim |
| Stage 3 | Add Step 3H: Source Reading Verification (existence + content + authority + recency) |
| New Stage 2Q | Architecture Reconciliation — rebuild architecture around what's actually sourceable |
| Stage 2Q Gate | Hard gate: no foundational vyāpti proceeds unsourced |
| Stages 4–6 | Inline Citation Protocol (Rules C-1 through C-4, prohibited phrase list) |
| Stage 3F (expanded) | Source Conflict Documentation Protocol |
| All stages | Replace "Sourced / Partially sourced / Unsourced" with 6-class Provenance Classification |
| Part One rationale | Add section: "The Provenance Problem in AI-Generated Guides" explaining why Class 6 exists and how to read it |

The net effect: every claim in the generated guide has a visible, traceable, verifiable origin — or is explicitly marked as a working hypothesis in a callout box. The reader never encounters an unmarked claim resting on training interpolation.
