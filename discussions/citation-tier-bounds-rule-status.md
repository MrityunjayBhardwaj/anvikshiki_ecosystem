# The citation tier — what it bounds, and what it must never do

Implements #19. Merged state at the time of writing: `webapp` at `030a0c9`, with
the verbatim rate from #76 already in.

The tier answers one question — *how well has this rule's citation been checked?* —
and maps the answer onto a ceiling in the same lattice the origin ceiling already
uses. A rule's effective status becomes the weakest of what it was authored as,
what its origin allows, and what its citation supports.

## The tiers

| tier | means | ceiling |
|---|---|---|
| `attributed` | the claim's span was found in the source | ESTABLISHED |
| `exists` | the source is reachable, nothing checked inside it | HYPOTHESIS |
| `unresolved` | a bare string, or a locator nothing can resolve | PROVISIONAL |
| `fabricated` | we looked at the source and the words were not there | CONTESTED |
| `curated` | hand-authored; makes no located-span claim | no cap |

## On the real chapter

24 candidates from ch02 → 15 rules through Stage D and E, no model call in the
tiering:

```
attributed   15 / 15   (100.0%)
exists        0 / 15
unresolved    0 / 15
fabricated    0 / 15
would drop    0 / 15

curated rules in the base KB: 11, all tier `curated`, 0 dropped
```

**ATTRIBUTED is reachable on real data for the first time.** Before #62 and #74 no
rule carried a quote or a provenance record, so the tier could only ever have
reported UNRESOLVED — a measurement of our own plumbing.

**Read 15/15 narrowly.** Three of the five tiers are at zero here, so the real trace
exercises `attributed` and `curated` and nothing else; `exists`, `unresolved` and
`fabricated` are covered by tests alone. In particular `exists` is *unreachable in
production today* — it requires a resolver that says yes, and no resolver exists.
The tests reach it by patching reachability, which is the honest way to cover a
branch that production cannot enter.

And the one candidate that failed its span check, `ltv_cac_ratio_above_three`
(`LTV : CAC ≥ 3:1`, 15 chars, too short to discriminate), **never became a rule** —
it is absent from the Stage D output entirely. The tier did not admit it; the tier
never saw it. 24 candidates becoming 15 rules is a separate filter this document
makes no claim about.

## Three deliberate divergences from the issue

**#19 says `FABRICATED → drop the rule` when "the identifier does not resolve".
Implemented as: only when a span was checked against its source and diagnosed
`absent`.**

Identifier resolution is #16 and is unbuilt. Had "we have no resolver" been wired
to "the identifier does not resolve", every rule in the knowledge base would tier
FABRICATED and be deleted — our own missing component read as evidence against
every source we have, with deletion rather than a depressed score as the
consequence. Reachability is therefore three-state and `None` maps to UNRESOLVED.
A locator can also fail to resolve because a registry is down or a document was
withdrawn; only fabrication is evidence against the claim.

**Hand-authored rules are exempt.** `Vyapti.provenance` is empty on curated rules
*by design* — the schema says so where the field is defined: they cite literature
rather than a located span. Tiering that absence UNRESOLVED capped the entire
shipped KB at PROVISIONAL and broke 13 tests, two of which existed precisely to
catch that demotion (`test_a_curated_knowledge_base_is_unaffected`, whose docstring
reads "if the ceiling touched them it would silently demote the whole engine").
A by-design absence is not a deficiency.

**`CURATED` is its own tier rather than reusing `ATTRIBUTED`.** Both give an
uncapped ceiling, so nothing downstream would notice — except the provenance panel
(#25), which shows the tier to a person and would be asserting that a span was
found in a source nobody checked. The ceiling may be right for a reason the label
must not misstate.

## The defect the trace caught, which review had not

The first working version tiered V16 — `ltv_cac_ratio_exceeds_one`, *"A business is
viable at the unit level if and only if LTV > CAC"* — as FABRICATED, and would have
deleted it. It is the central claim of the chapter and its quote is word-perfect.
It fails the strict check only because the model did not reproduce the `**` around
`LTV > CAC`.

The cause was named during planning and then not fixed: `quote_found_in_source` is
a `bool`, so a dropped asterisk and an invented sentence both arrive as `False`,
and the tier read `False` as grounds to delete. The verdict existed at capture
time — `diagnose` returns it — and was collapsed to a boolean before reaching the
record.

Fixed by carrying `quote_verdict` on `Provenance`. FABRICATED now requires the
verdict to say `absent`. A `markup` miss reaches ATTRIBUTED, on the reasoning that
markdown emphasis is source *formatting* — the same footing as the line wrapping
already normalised away — rather than a change to the words. A punctuation
substitution is a changed character in the content and stays UNRESOLVED; no run has
produced one yet, so there is nothing to decide from.

An old record with `False` and no recorded verdict reads as UNRESOLVED. Without a
reason, fabrication and formatting are the same value, and the tier that authorises
deletion must not fire on that ambiguity.

**The general shape, again:** ask what type the data must arrive at, and whether it
can hold the distinction the consumer needs. A boolean cannot carry a four-way
verdict, and the information was being computed and discarded one stage upstream.

## Known limits

- `exists` is unreachable in production until #16 lands.
- The drop is implemented (`should_drop_for_citation`) but **not yet wired into any
  caller**. Nothing deletes rules today; on this data it would delete nothing.
- The tier is computed but not yet surfaced — #25 is what shows it to a reader.
- One chapter, one model. `fabricated` has never been observed on real data.

## Self-review finding: `exists` is doubly inert (#79)

Comparing the two ceiling tables against each other, rather than reading either
alone:

```
tier         ceiling       lowers the result for
attributed   established   NOTHING   (correct — it is the top)
exists       hypothesis    curated only
unresolved   provisional   curated, guide_extracted, hitl_promoted
fabricated   contested     all five origins
curated      established   NOTHING   (correct)
```

`exists` binds only for `curated`-origin rules, and those are exempt from this
axis by construction — they return the `curated` tier before `exists` is ever
evaluated. So it is not only unreachable until #16; it would change no outcome
even once reachable. Every other origin is already capped at HYPOTHESIS or below.

Nothing is wrong in today's output, because `exists` is never produced. The cost
lands later: #25 would render it to a reader as a meaningful tier. Filed as #79
with the three ways out — move its ceiling to PROVISIONAL so it binds, declare it
display-only, or remove it until #16 makes it real.
