# On-the-fly KB construction: the WEB_SOURCED tier

**Date:** 2026-08-17
**Subject:** `anvikshiki_ecosystem` at `ccd4b08`
**Status:** design note. Nothing here is implemented.
**Depends on:** `optimal-state-end-to-end.md` (Theorem 4, the status lattice), `extraction-harness-audit.md` (why extraction quality gates this)

---

## 1. What this is

A path where the KB is **derived at query time from retrieved documents** rather than authored in advance: retrieve → extract predicates with verbatim citations → validate → reason. The goal is to get the engine's distinctive capabilities without first hand-authoring a large predicate base for every domain.

**The short answer: it works, it needs a ~11-rule skeleton rather than a strong base, and it costs you the top of the status lattice.** The two capabilities that nothing else in this space can do — verifiable counterfactuals and localizable disagreement — survive intact.

This is also less new than it looks. The origin enum already anticipates it:

```
CURATED         "Hand-authored in base KB"          ← wired
GUIDE_EXTRACTED "T2b: extracted from guide prose"   ← wired (t2b_compiler.py)
LLM_PARAMETRIC  "T3b v1: LLM parametric knowledge"  ← wired (kb_augmentation.py)
WEB_SOURCED     "T3b v2: web search evidence"       ← declared, referenced NOWHERE
HITL_PROMOTED   "T3b v3: promoted from shadow KB"   ← declared, referenced NOWHERE
```

This note specifies `WEB_SOURCED`, plus the promotion path that makes `HITL_PROMOTED` meaningful.

---

## 2. The constraint that shapes the whole design

From `optimal-state-end-to-end.md` Theorem 4: if every argument supporting a conclusion passes through an auto-generated rule, `status(c) ≤ PROVISIONAL`, by boundedness of meet.

Applied here: **a purely on-the-fly system can never output ESTABLISHED.** Not because the crawl might be bad — because an LLM deciding the epistemic status of the rules the engine uses to qualify epistemic status is circular *structurally* (thesis_v3 §12.3), and the lattice bound is what makes that circularity non-exploitable.

This is the guarantee working, not a limitation to engineer around. Design accordingly: **the ceiling is a feature, and it should be visible in the output.**

### What survives the ceiling

| Capability | Under pure crawl |
|---|---|
| Verifiable counterfactuals ("what would change my mind", checkable in 0.1ms) | **Intact** — graph structure is indifferent to rule origin |
| Localizable disagreement (point at the attack edge, re-run it) | **Intact, conditional on snapshotting** — see §7 |
| Decay as defeat | **Improved** — crawled sources carry real dates; `src_ries_2011` does not |
| Span-level provenance | **Improved** — see §4 |
| Bound on LLM-generated knowledge | **Vacuous if everything is crawled** — discriminates nothing when uniform |
| ESTABLISHED status | **Lost** |
| Honest DECLINE | **Lost unless deliberately preserved** — see §6 |

Two of those losses are recoverable by design (keep a curated tier; keep the applicability gate). The ESTABLISHED ceiling is not, and should not be.

---

## 3. The four-tier KB

One function maps origin to a lattice ceiling. The meet in the status derivation propagates it automatically — no special-casing anywhere downstream.

| Origin | Ceiling | Produced by | Admission gate |
|---|---|---|---|
| `CURATED` | ESTABLISHED | Human authoring | Human judgment |
| `GUIDE_EXTRACTED` | HYPOTHESIS | T2b, offline over a fixed corpus | Measured against gold (G3) |
| `WEB_SOURCED` | PROVISIONAL | T3b v2, query-time retrieval | Four structural gates (§5) |
| `LLM_PARAMETRIC` | PROVISIONAL | T3b v1, model's own knowledge | Existing gates, **no span possible** |
| `HITL_PROMOTED` | tier of the reviewer's decision | Human review of a lower tier | Human judgment |

```python
ORIGIN_CEILING = {
    AugmentationOrigin.CURATED:         Status.ESTABLISHED,
    AugmentationOrigin.GUIDE_EXTRACTED: Status.HYPOTHESIS,
    AugmentationOrigin.WEB_SOURCED:     Status.PROVISIONAL,
    AugmentationOrigin.LLM_PARAMETRIC:  Status.PROVISIONAL,
}

def effective_status(v: Vyapti) -> Status:
    origin = v.augmentation_metadata.origin if v.augmentation_metadata else CURATED
    return meet(v.epistemic_status, ORIGIN_CEILING[origin])
```

That replaces `MAX_CONFIDENCE = 0.75`, which caps an *input* to a non-monotone pipeline and therefore guarantees nothing about the output.

**Distinguish `WEB_SOURCED` from `LLM_PARAMETRIC` even though they share a ceiling.** They fail differently: parametric knowledge fails by confabulation with no trace; web-sourced fails by misreading a real document. The first is unfalsifiable, the second is checkable against the span. Same ceiling, very different debuggability — and the provenance display should say which.

### Why the skeleton can't be empty

`kb_augmentation` generates *"using existing vyaptis as structural templates"* — `_build_framework_summary()` and `_build_applicable_vyaptis_text()` feed the curated rules in as the axes to project onto. With zero curated rules there are no axes, and nothing constrains the generator.

The skeleton is small:

```
curated vyaptis : 11
predicates      : 20
hetvabhasas     : 8
```

**Eleven rules per domain, not thousands.** That is the actual prerequisite — a day's authoring, not a project. The skeleton defines the domain's reasoning *shape*; the crawl fills in specifics.

---

## 4. Citations: what exists, what's missing

The citation infrastructure is mostly built. `Provenance` already carries a span:

```python
class Provenance(BaseModel):
    chapter_id: str
    section_header: str = ""
    paragraph_index: int = 0
    sentence: str = Field(default="", description="The exact sentence containing the claim")
    confidence: float = 0.5
```

`sentence` is the span field. Two things are missing.

**First, the locator is corpus-shaped.** `chapter_id` assumes a guide. Web documents need a URL, a retrieval timestamp, and a content hash.

**Second — and this is the real gap — nothing verifies the span.** `provenance.sentence` appears exactly once in the codebase, at `predicate_extraction.py:840`, where it is *used* as a fallback for the vyāpti statement. Stage E's gates are cycles, orphans, and Datalog compilation. **No gate checks that the quoted sentence actually appears in the source document.**

So today a predicate can carry a fabricated quotation and pass every validation. That is the single highest-value check to add, and it is a string search.

### The provenance upgrade nobody has noticed

Current sources:

```
sources cited : 22
format        : ['src_blank_2005', 'src_buffett_letters', 'src_christensen_1997', ...]
```

Opaque strings. No URL, no span, no date. There is no way — for a human or a machine — to check whether `src_ries_2011` supports the rule it is attached to.

A `WEB_SOURCED` predicate with a verified span gives: **predicate → exact quoted text → document URL → retrieval timestamp → content hash.** Mechanically checkable.

**On this axis the crawled tier is strictly better than the hand-authored one.** The trade is not rigor versus convenience; it is *status ceiling* versus *verifiable sourcing*, and those are independent axes. A curated rule has high status and unverifiable sources. A crawled rule has low status and verifiable sources. Both facts should be visible.

---

## 5. The span-grounding gate

The measurement problem: on-the-fly builds a fresh mini-KB per query, so you can never pre-label gold for it. The extraction discipline established in `extraction-harness-audit.md` does not transfer directly.

The substitute: **a per-query check that is falsifiable without a gold set.**

```
G-SPAN — for every WEB_SOURCED predicate:
  1. provenance.quote is non-empty
  2. provenance.quote appears VERBATIM in the retrieved document body
     (after whitespace normalisation only — no fuzzy matching, no paraphrase tolerance)
  3. provenance.doc_url is present and resolvable to a snapshot
  4. the quote is long enough to be discriminating (≥ 40 chars, tunable)

  Predicates failing any check are DROPPED, not downgraded.
  Report drop_rate. A run with drop_rate > 0.3 is flagged degraded.
```

**What this catches:** fabricated citations — the dominant failure mode, and the one §12.3 names explicitly ("LLMs hallucinate citations").

**What this does not catch:** a correctly-quoted span misread into the wrong predicate. Extraction *semantics* still need the one-time benchmark (G3), measured offline against gold and assumed to transfer. State that assumption; it is not free.

**Why no fuzzy matching.** The temptation is to allow near-matches for quotes that got lightly reworded. Resist it — that reintroduces exactly the loose-matcher failure documented in the harness audit, where a threshold admits things it shouldn't and inflates the pass rate. Verbatim or dropped.

The gate joins Stage E's existing three, giving four structural checks before crawled material is allowed to reason:

```
1. Cycle detection        (exists)
2. Orphan predicates      (exists)
3. Datalog compilation    (exists)
4. Span grounding         (new)
```

---

## 6. Integration into `forward_with_coverage`

Current STEP 3 routes DECLINE to `AugmentationPipeline`, which generates from parametric knowledge. The change inserts a retrieval-backed tier ahead of it and, critically, **preserves the honest refusal**.

```
STEP 1  Ground query                                    unchanged
STEP 2  Coverage analysis                               unchanged
STEP 3  Route:
          FULL / PARTIAL         → existing path, active_ks = self.ks
          DECLINE                → score framework applicability (exists, ≥ 0.4)
              below threshold    → DECLINE RESPONSE          ← preserved, unchanged
              above threshold    → CRAWL TIER (new):
                    3a. retrieve k documents for the query
                    3b. snapshot each: (url, retrieved_at, sha256, body)   ← §7
                    3c. run extraction Stages A–E over the snapshots
                    3d. gates: cycles, orphans, datalog, G-SPAN
                    3e. tag survivors WEB_SOURCED + ORIGIN_CEILING
                    3f. merge into a KB copy → active_ks
                    3g. persist to the KB cache keyed by topic  ← §8
                    on zero survivors → fall back to LLM_PARAMETRIC,
                                        or DECLINE if that also yields nothing
STEP 4  Compile AF with active_ks                       unchanged
STEP 5  T3a retrieval                                   reuse the crawl snapshots
STEP 6  Grounded extension + vāda                       unchanged
STEP 7  Status / provenance / uncertainty               status now origin-capped
STEP 8  Synthesize                                      must surface the tier
```

Two deliberate properties of this routing:

**DECLINE survives.** Crawling fires only when `applicability_score ≥ APPLICABILITY_THRESHOLD` (0.4, already implemented). Genuinely out-of-domain queries still refuse. Without this, a crawl-on-miss architecture deletes the engine's most distinctive behaviour — it would always find *something* and always answer.

**STEP 5 reuses STEP 3b.** The crawl already fetched documents; T3a should retrieve prose from those snapshots rather than issuing a second, unrelated retrieval. Otherwise the synthesis quotes different sources than the reasoning used.

### What synthesis must say

A `WEB_SOURCED` answer is not an ordinary answer, and the output must not hide that:

> *"Working from sources retrieved just now, not from the curated knowledge base. Highest available status for this answer is PROVISIONAL. Supporting spans: [quote] — [url], retrieved 2026-08-17."*

If the tier is invisible in the output, the ceiling guarantee is real internally and useless externally.

---

## 7. Snapshotting — the requirement that preserves determinism

This is easy to miss and it is load-bearing.

One of the capabilities worth building for is **localizable disagreement**: post-grounding the pipeline is deterministic, so a third party can dispute a specific attack edge and re-run the computation themselves. Live retrieval breaks that — the web changes, and a re-run silently reasons over different documents.

**So the crawl must snapshot.** Store `(url, retrieved_at, sha256, body)` for every document, keyed by content hash, and make the reasoning run against the snapshot rather than the live fetch. Then:

- the same query + same snapshot set → same graph, same labels, same statuses, bit-for-bit
- a disputed conclusion can be re-derived by anyone holding the snapshot
- source drift becomes *detectable* (re-crawl, compare hashes) rather than invisible

Without snapshotting you keep the counterfactual capability and lose the reproducibility one. With it you keep both. The cost is disk.

---

## 8. Cost, latency, caching

Extraction is five LLM stages with ensembles — minutes per corpus, not seconds. Naively per-query this is unusable.

It is not per-query. It is **once per topic**, then cached: `3g` persists survivors into the KB, so the second query on a topic finds them via the normal coverage path (FULL/PARTIAL) and never crawls. The KB grows monotonically. This is the "adaptive knowledge landscape" the augmentation module's docstring already describes; the cache is what makes it real.

Practical consequences:

- **First query on a new topic is slow** (crawl + extract). Surface this in the trace — the SSE pipeline already has stage events; add `stage:crawl` and `stage:extraction`.
- **Cache invalidation is decay.** Snapshots carry `retrieved_at`; the existing decay machinery already turns age into an undermining attack. Crawled knowledge ages out *structurally*, which is more principled than a TTL.
- **The KB must be bounded.** Monotonic growth with no eviction ends badly. Evict by: never used in N queries, or superseded by a `HITL_PROMOTED` equivalent.

---

## 9. What carries over, and what this does not solve

**Carries over unchanged:** F1–F5 (termination, polynomial grounded semantics, conflict-freeness, rationality postulates, unique fixpoint) — none depends on where rules came from. Theorem 2 (restatement monotonicity by idempotence) holds for any lattice-valued status. Theorem 4 is what produces the ceiling.

**Does not solve:**

- **Extraction semantic accuracy.** G-SPAN catches fabrication, not misreading. Still gated on the one-time benchmark, and that benchmark still needs the matcher fixed — a matcher that scores `value_creation` against `not_value_creation` as a match cannot validate a crawl pipeline any more than it can validate a guide one.
- **Retrieval quality.** Garbage documents produce well-cited garbage predicates. G-SPAN will happily verify a quote from a bad source. Source authority (thesis_v3 §13, *śabda*) is the missing piece and is not specified here.
- **Cross-document contradiction.** Two sources disagreeing produce two rules whose conclusions rebut each other. The argumentation layer handles this correctly — it is what rebutting attacks are *for*, and the result is CONTESTED, which is the right answer. Worth noting as a feature, but untested at crawl scale.
- **Conformal calibration.** Still `[OPEN]`, still gated on labelled data.

---

## 10. Build order

1. **`ORIGIN_CEILING` + `PROVISIONAL` in the KB lattice.** Small, and it retires `MAX_CONFIDENCE`. Gives Theorem 4 teeth for the tiers that already exist, before any crawl work.
2. **Extend `Provenance`** with `doc_url`, `retrieved_at`, `content_sha256`, rename `sentence` → `quote`. Backward-compatible; `chapter_id` stays for the guide path.
3. **G-SPAN in Stage E.** A string search. Runs against the guide corpus immediately and will tell you the current fabrication rate on `GUIDE_EXTRACTED` predicates — a useful number nobody has.
4. **Snapshot store.** Content-addressed, before any live retrieval exists, so determinism is never lost even briefly.
5. **Crawl tier in STEP 3**, behind the existing applicability gate.
6. **Surface the tier in synthesis and in the UI provenance panel.**
7. **`HITL_PROMOTED` path** — review UI anchored on the *source span*, with a "this predicate was missed" action (see the harness audit; a reviewer who only sees extractor output cannot measure recall).

Steps 1–3 are worth doing regardless of whether the crawl is ever built: they improve the guide path, and step 3 produces a measurement that currently does not exist.

---

## 11. Open questions

- **Source authority.** thesis_v3 §13 specifies *śabda* as trust-based epistemic defaults. A crawl tier needs it — currently every URL is equally trustworthy, which is obviously wrong. `[OPEN]`
- **How many documents.** k is unspecified. Too few misses coverage; too many blows latency and dilutes precision. Empirical. `[OPEN]`
- **Whether guide-extracted and crawled predicates are exchangeable.** Bears on whether one conformal calibration covers both tiers, or each needs its own. `[OPEN]`
- **Whether the skeleton generalises.** Eleven rules works for business strategy. Whether ~11 is a domain constant or an artefact of this KB is untested across a second domain. `[OPEN]`
