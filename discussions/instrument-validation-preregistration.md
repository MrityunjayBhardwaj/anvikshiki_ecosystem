# Pre-registration: instrument validation and the first extraction measurement

**Date:** 2026-08-17
**Issue:** #10
**Status:** written before any run. **Nothing below has been executed. There is no number in this document, and any number later attributed to it is fabricated.**

This exists so that a run cannot be registered after its result is known. The previous audit pre-registered its Part B the same way and then did not run it, because Part A disqualified the instrument. That instrument has since been repaired (#6, #7, #8, #9); this registers what happens next.

---

## 0. Why the instrument is validated before anything is measured

The harness grades extraction. Nothing grades the harness. Until something does, a precision figure means "the matcher said so", not "this is right" — and the same matcher previously scored an extractor emitting the exact inverse of every gold predicate at precision 1.000, recall 1.000.

This is the step CaRB took when replacing OIE2016. The two benchmarks produced **contradictory system rankings** on the same systems, and human assessment settled which to believe. A loose matcher does not add noise to a measurement; it inverts the conclusion.

**The order is forced:** validate the matcher against human judgment → then, and only then, report extraction numbers.

---

## 1. Step one — validate the matcher

### Who judges

A human, reading the two descriptions and deciding whether they mean the same thing. **Not the extractor, not the matcher, and not an LLM.** A model judging its own instrument reproduces the self-confirming loop the audit exists to prevent — and the point of this step is precisely to obtain a signal from outside the system.

### What is judged

Not all ~420 pairs. The sheet (`instrument_validation.build_decision_sheet`) carries only the verdicts whose being wrong would change a reported number:

| Rows | What each row is |
|---|---|
| every pair the matcher **matched** | a precision claim |
| for each gold matched to nothing, its **nearest candidates** | a recall claim — a possible missed match |

Roughly 50 rows, about 30 minutes.

The second half is the half a review interface built on extractor output **cannot** produce. The HITL reviewer shows only what the extractor proposed, so it finds false positives and is structurally blind to false negatives — which is what recall is made of.

### What is reported

Observed agreement, Cohen's κ, and the two disagreement classes **separately**, because they are not symmetric:

- **matcher yes / human no** → a precision failure. The veto is the instrument for it, and it is cheap.
- **matcher no / human yes** → the *only* evidence that token overlap is insufficient, and therefore the only evidence that a semantic encoder would earn its cost.

**Registered in advance:** if the second class is empty, a semantic encoder is not adopted, whatever the aggregate κ looks like. NegMPNet was already rejected on dependency cost — torch is ~2GB on a 362MB venv, for ~420 short-string comparisons — and that decision stands unless this class of disagreement provides evidence against it.

Unjudged rows are counted and excluded, never treated as agreement.

### Which match mode

All three (`name`, `description`, `either`) are scored against the same human judgments. `match_on` currently defaults to `name`; **the default changes only if the human judgments say a different mode agrees better.** This is registered now so the choice is not made by whichever produces the more flattering extraction number afterwards.

#### Amendment, 2026-08-17: the mode that builds the sample, registered before judging

The clause above governs which mode's **verdicts** are adopted. It does not cover a second thing the mode also decides: **which pairs land on the sheet at all.** `replay_mode` re-scores every mode against the same judgments, so the verdicts are compared on identical ground — but the sample is whatever the *building* mode surfaced, and no mode can be credited or blamed for pairs it was never shown. That gap was unstated here and is closed now.

**The sheet is built under `either`. The verdict question stays open to the judgments, exactly as registered above.**

The reason is that `name` cannot construct the recall half. Near misses are meant to be the *nearest* candidates to a gold predicate nothing matched — that half exists because a review built on extractor output can only find false positives, and recall is made of the other kind. Measured on the 24 candidates from ch02:

| | `name` | `either` |
|---|---|---|
| near-miss rows | 33 | 33 |
| rows scoring exactly 0.0 | 21 | 0 |
| golds whose three "nearest" candidates all score 0.0 | **6 of 11** | 0 of 11 |

For those six gold predicates the three offered candidates are identical — `accelerated_failure`, `cash_burn_accelerating`, `cohort_based_ltv_model` — because every candidate ties at zero name overlap and the tie is broken alphabetically. Eighteen of the thirty-three recall rows therefore ask a human about pairs selected by spelling. Under `either`, descriptions break those ties and every row is a real nearest neighbour.

Two things this amendment deliberately does **not** do. It does not claim `either` agrees better with human judgment — that is unknown until the sheet is judged, and it remains the registered criterion. And it is not a choice made after seeing which mode flatters a number: no figure has been reported from any mode, and κ has not been computed, because nothing has been judged. What was observed is a property of the *sample construction*, visible without a single human verdict.

The degeneracy is filed as a bug in its own right; if it is fixed, `name` becomes able to build a usable sample and this amendment stops applying to future sheets.

### Kill criterion for the instrument

κ below **0.6** means matcher and human do not agree well enough for the matcher's verdicts to stand in for judgment, and **no extraction number is reported from it**. That would be a repeat of the previous verdict, and it would be reported as the finding rather than worked around.

---

## 2. Step two — measure extraction

Runs only if step one passes.

### Corpus and denominators

- **Corpus:** `guides/business_expert/guide_ch2.md` — the real chapter, 16,422 characters.
- **Recall denominator:** 14, the gold predicates in `expected_predicates.yaml`.
- **Precision denominator:** however many candidates Stage A returns, printed before scoring. Nothing in the repo records a typical count.

**Reported separately, never merged:** `guide_ch2_excerpt.md` is *not* an excerpt of that chapter — 3,812 characters against 16,422, sharing none of its substantial paragraphs, and it was written alongside its own answer key. A run against it measures whether the extractor finds concepts a human deliberately planted in a short toy. That is worth knowing and is not the same experiment. `GoldSet.authored_for` records which text the gold was authored against.

Note the consequence, registered now: the gold was authored against the excerpt, so measuring the **real chapter** against it is the harder direction and a low recall there is partly a statement about the gold's provenance, not only about the extractor.

### Expectation

Recall between **0.4 and 0.7**. The gold names are conceptual rather than lexical — none of the fourteen appear literally in the prose — so the extractor must invent matching labels and the matcher must accept them.

Precision is **not predicted**. It depends on how many candidates Stage A emits, and nothing records a typical count. Stating a range now would be invention.

### Kill criteria

- recall < 0.5 → extraction is unreliable, and that becomes the **headline finding**, not a footnote
- precision < 0.5 → the extractor invents content
- either control failing → the run is void

### Controls

- **Positive:** `positive_unit_economics` and `value_creation` are V01's own antecedent and consequent, they are in the KB the pipeline is seeded with, and Chapter 2 is about them. If those come back missed, the run is void.
- **Negative:** a passage with no extractable domain claim — the chapter's opening narrative paragraph, or a stretch of `stage3_reference_bank.md` bibliography. Any output at all is a false positive.

### What is reported

Precision and recall **separately**, never only a composite. They fail for opposite reasons and need opposite fixes. Per-item failures listed. Components reported individually — the composite's weights are asserted and never derived, and half its mass sits on well-formedness rather than correctness.

Alongside every figure: which model produced the extraction, the candidate count, and the `match_on` mode.

---

## 3. What has to be decided before running

Both cost money or belong to the maintainer, and neither is settled here:

1. **The model.** `gemini-2.0-flash` is retired (404). A DeepInfra key is present. Whichever is used is reported beside the number, because an extraction figure without its model is not reproducible.
2. **The judging.** Step one is human work and cannot be delegated to the system being validated.

---

## 4. What would falsify the conclusion of this exercise

- **The gold is wrong.** It is fourteen hand-authored predicates from one person against one chapter. A second annotator disagreeing materially would make the denominator itself the finding.
- **The chapter is unrepresentative.** One chapter of one guide. Nothing here licenses a claim about the corpus, and Phase 4's second and third knowledge bases are what would.
- **Stage A emits far more candidates than expected.** Precision is a ratio with an unrecorded denominator; a very large candidate count makes a low precision figure a statement about verbosity rather than accuracy, and that distinction must survive into the report.
