# The verbatim quote rate — first measurement

Run on 2026-08-18 over `guides/business_expert/guide_ch2.md`, model
`openai/zai-org/GLM-5`, 7 live Stage A calls. Reproduce with
`python scripts/measure_verbatim_rate.py`, or re-read it at another threshold
for free with `--from-cache`. Full report:
`traces/verbatim_rate/verbatim_rate_ch02.md` (gitignored — this file is the
tracked record).

This is the distribution #18 was told not to pick a threshold without.

## What the model did with 24 quotes

| verdict | count | |
|---|---|---|
| `verbatim` | 22 / 24 (91.7%) | found in the section, long enough to mean something |
| `too short to discriminate` | 1 / 24 (4.2%) | `LTV : CAC ≥ 3:1`, 15 chars |
| `markup` | 1 / 24 (4.2%) | matches once `**` is stripped |
| `punctuation` | 0 / 24 (0.0%) | |
| **`absent`** | **0 / 24 (0.0%)** | **the fabrication number** |
| `empty` | 0 / 24 (0.0%) | the model never declined to quote |

Asked to quote, GLM-5 quoted. Nothing was invented, nothing was skipped, and
the `quotes` list never came back short — so on this run the parallel-list zip
held and none of the missing-quote machinery fired.

Every count above carries its denominator on purpose. A run of this script
without an API key produces the same table full of zeros, and the denominators
are the only thing that distinguishes it (see "what the first run measured"
below).

## The fabrication number was 4.2% until it was read

The first pass scored one quote `absent` — the verdict the report describes as
*"the words are not in the section at all"*. It was this:

```
chapter:  ... if and only if **LTV > CAC**. More specifically ...
quote:    A business is viable at the unit level if and only if LTV > CAC
```

Every word matches. The model quoted prose out of a formatted source and
dropped the asterisks, which is what models do. `diagnose` had a `punctuation`
category for curly quotes and em dashes and nothing for markdown, so a
formatting artefact landed in the fabrication bucket and would have been
reported as a 4.2% fabrication rate.

`span_verification.py`'s own docstring predicts this exactly — *"our own
strictness producing a signal that reads as a fact about the model"* — and the
module was still one category short of its own warning. Fixed by adding
`markup` and `punctuation and markup`, both diagnostic only: the verdict stays
strict, nothing new is accepted as verbatim, and the candidate is still
refused. Only the explanation changed, and the explanation is the number
anybody will quote.

**True fabrication rate on this chapter: 0 / 24.**

## Quote lengths, and what they say about `MIN_DISCRIMINATING_LENGTH = 24`

| min | 25th | median | 75th | max | mean |
|---|---|---|---|---|---|
| 15 | 60 | 86 | 135 | 305 | 100.6 |

The sweep, where "cost" is real citations discarded for being short:

| T | below T | of those, verbatim in source | at or above T **and** verbatim |
|---|---|---|---|
| 12 | 0 / 24 | — | 23 / 24 (95.8%) |
| 16 | 1 / 24 | 1 / 1 (100%) | 22 / 24 (91.7%) |
| 20 | 1 / 24 | 1 / 1 (100%) | 22 / 24 (91.7%) |
| **24** | 1 / 24 | 1 / 1 (100%) | 22 / 24 (91.7%) |
| 30 | 1 / 24 | 1 / 1 (100%) | 22 / 24 (91.7%) |
| 40 | 2 / 24 | 2 / 2 (100%) | 21 / 24 (87.5%) |
| 60 | 5 / 24 | 5 / 5 (100%) | 18 / 24 (75.0%) |
| 80 | 10 / 24 | 9 / 10 (90%) | 14 / 24 (58.3%) |
| 120 | 17 / 24 | 16 / 17 (94%) | 7 / 24 (29.2%) |

Three things follow, and only the first is good news for the incumbent.

**24 is defensible.** It fires exactly once, on `LTV : CAC ≥ 3:1` — a bare
ratio that appears throughout a business guide and proves nothing about
whether the model read the claim where it says it did. That is the case the
threshold exists for, and it catches it.

**24 is not, however, *chosen*.** Every threshold from 16 to 30 drops exactly
the same single quote. This data cannot tell them apart, so keeping 24 is a
decision the distribution permits rather than one it recommends. Anyone
reporting "we validated the threshold" would be overstating it.

**Above 60 the threshold starts costing more than it saves.** Every quote
below 60 characters was verbatim in the source — the "of those, verbatim"
column is 100% all the way up. So in that whole range the threshold's only
effect is discarding real citations for being short. The first non-verbatim
quote does not appear below the cut until T=80. Raising the threshold buys
nothing here and loses citations linearly.

One caveat that bounds all three: this is **24 quotes from one chapter by one
model**. `min` is 15 and the next value up is in the 20s, so the single point
below 24 is what the entire 16–30 conclusion rests on. A second chapter could
move it.

## The negative control passed

`### REFERENCES` — the numbered citation list — produced **0 / 24** predicates.
That is the pre-registration's negative control and it is clean.

`### Going Deeper` produced 2, both verbatim
(`geometric_decay_assumption`, `ltv_survival_equivalence`). It sits next to the
references and looks like more bibliography, but it is prose making real claims
about LTV mathematics. Counting the two sections together — which the first
version of the script did — would have scored two correct extractions as
control failures and reported the control as failed when it passed. They are
now reported separately, and `### Going Deeper` is explicitly labelled as not a
control rather than quietly excluded.

## What the first run measured, which was nothing

The first live attempt failed authentication on all seven sections. It still
wrote a complete report: a quote-length distribution, a threshold sweep, a
fabrication rate. Every figure was `0`.

What kept it readable was printing the denominator beside every count — the
page said `0 / 0 (no denominator — nothing was measured)` rather than `0.0%`,
and `sections that errored: 7 / 7 (100.0%)`. Without that it would have been a
clean-looking measurement of a run that never happened, which is this
codebase's oldest recurring defect committed by the tool built to measure it.

Two guards were added rather than relying on the reader: the script now refuses
to start without `DEEPINFRA_API_KEY`, and exits non-zero when every called
section failed, so nothing scripting it can read "wrote the report" as
"measured the rate".

## Known limits

- **One chapter, one model, 24 quotes.** Nothing here generalises to the corpus
  yet, and the 16–30 flat region rests on a single data point.
- **A shifted middle element is still undetected.** `unquoted_by_short_list`
  catches a `quotes` list that runs out at the end. An omitted *middle* element
  moves every later quote onto the wrong predicate while leaving the lengths
  equal, and a shifted quote still passes the verbatim check because it is a
  real span from the section — attached to a claim it does not support. That is
  the wider parallel-list defect and it is unfixed. There is a test asserting
  this blind spot exists, which fails the day something closes it.
- **Two notions of "verbatim" appear on the same page.** The verdict table
  scores the markup quote as `markup` and reports `absent: 0 / 24`. The
  threshold sweep's "of those, verbatim in source" column uses the strict
  check, which counts that same quote as not found — so at T=80 the sweep
  reads `9 / 10` where the table implies `10 / 10`. One artifact, two answers,
  and the sweep is the more conservative of them. Filed separately.
- **`traces/` is gitignored**, so the Stage A output behind these numbers has no
  git backup. The run is cheap to repeat (7 calls) but will not reproduce
  byte-for-byte.

The pinned artifacts for #10 were verified unchanged across this work:
`stage_a_ch02.json` at `8767fac9…` and `decision_sheet_ch02.yaml` at
`fc5a59b6…`, checked before and after, 2 of 2 files compared.
