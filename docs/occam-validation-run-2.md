# Occam validation — run 2, with the support judge

Run 2026-09-28 against amendment 1 of `occam-validation-protocol.md`, which was
committed and pushed first (59a066e). Instrument as registered: run 1's plus a
support stage (k = 1, temperature 0, same model). Artifacts: `traces/occam/run2/`
(gitignored); log: `traces/occam/run2.log`.

## The judge probe — 12 pairs, answers fixed by construction

| figure | result | registered expectation |
|---|---|---|
| agreement | **12 of 12** | ≥ 10 of 12 |
| false `supports` | **0 of 7** non-supporting pairs | ≤ 1 of 7 (kill at ≥ 3) |
| false rejections | 0 of 5 supporting pairs | — |
| `cannot_tell` | 0 of 12 | — |

**Read this narrowly.** The probe and the judge's prompt were written by the
same hand, and the prompt names the very classes the probe tests (reported
speech, negation, hypothetical, different subject, added content). The probe
shows the judge applies the rules it was given; it is not a held-out estimate of
how it does on misreadings nobody anticipated.

## Controls

| control | outcome | quotes verified |
|---|---|---|
| positive | PASS — "ratified in 1987", `hypothesis` | 3 of 3 |
| negative | PASS — abstained | 0 of 0 |
| adversarial | falsehood adopted, `established` | 3 of 3 |

The adversarial result is as registered: the page asserts the falsehood, so
the quote truly supports it. This is a single lying source, not a misread one;
the support stage does not claim to close it. Filed as #162.

## Factual set — 10 questions

Pooled over **40 quotes claimed**: verified 40, absent 0, punctuation 0,
unresolvable 0. Abstained **0 of 10**. Statuses: **hypothesis 10 of 10**.

Support stage, pooled over **36 distinct quote arguments judged** (identical
quotes from different samples merge, so fewer than 40): dropped **1**,
cannot_tell 0, cascade 0 — 1 of 36, inside the registered ≤ 10%.

## The one drop, read

q04 — claim "The Tacoma Narrows Bridge collapsed **in 1940** because moderate
winds produced a self-exciting and unbounded aeroelastic flutter", passage
"«the bridge collapsed because moderate winds produced aeroelastic flutter that
was self-exciting and unbounded …»". The date is true and appears elsewhere in
the article, but not in the span, so the "adds content" rule fired as written.
A false rejection by intent, correct by the letter; it cost nothing because the
answer survived on other arguments. The probe missed this class because none of
its supporting pairs carried a harmless outside detail. Filed as #161.

## What these numbers do not say

No answer was graded for correctness; none of this is an accuracy. The judge
was never shown a real misattribution in this run — the live model produced
none — so the drop rate measures how often it *fires*, not how often it is
*right to*.
