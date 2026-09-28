# Occam validation protocol — pre-registered

Registered 2026-09-28, **before** the first measured run, and committed in the
same pull request as the controls it governs (#145). A threshold chosen after
seeing the result is not a threshold, so nothing below may be edited after
run 1 except to add a dated amendment at the end that says what changed and why.

## What is measured

**Instrument:** `python -m occam` at the commit carrying this file. Model
`openrouter/z-ai/glm-5.2`; `k_argue = k_attack = 3`; temperatures 0.7 / 0.2;
40,000 characters per source; `max_age_days = 365`; Wikipedia search, 3
sources per question.

**Corpus for run 1:**

1. The three controls in `occam/controls.py`, each with its planted page as
   the only source.
2. Ten factual questions answerable from English Wikipedia (listed below),
   one run each.

```
Why did the Challenger space shuttle break apart in 1986?
What causes the seasons on Earth?
Who proposed the theory of continental drift, and when?
Why did the Tacoma Narrows Bridge collapse in 1940?
What is the main cause of the Aurora Borealis?
When and where was the first successful powered airplane flight?
What caused the extinction of the dinosaurs according to the leading hypothesis?
Why is the sky blue?
What was the Rosetta Stone used to decipher?
What is the function of mitochondria in a cell?
```

## Denominators, stated in advance

| figure | numerator | denominator |
|---|---|---|
| verified-quote fraction | quotes with verdict `ok` or `markup` | quotes the model claimed, all questions pooled |
| fabrication rate | quotes with verdict `absent` | quotes the model claimed, pooled |
| punctuation / unresolvable | those verdicts | quotes claimed, pooled — reported apart from fabrication |
| abstention rate | questions abstained | 10 factual questions |
| status distribution | answers at each status | answered questions |

Every figure is printed as *n of N*. Per-question rows are listed, not only totals.

## Expected ranges (priors, with their source)

- verified-quote fraction ≥ 0.9 — prior: ch02 run 24/24 found (22 clean,
  1 markup, 1 short), Challenger run 4/4.
- fabrication rate ≤ 0.1.
- abstention rate on the factual set ≤ 0.3.
- status mostly `hypothesis`: answers are usually the model's inference over
  quotes, which caps at `hypothesis` by design.

## Kill criteria

- **Positive control missed → the run is VOID.** No figure from it is quotable.
- **Negative control answers → STOP.** The refusal is broken; every other number is void.
- **Verified-quote fraction < 0.5 → that is the headline finding**, not a footnote.
- Empirical conformal coverage below 1 − α outside sampling error → the
  calibration set is unrepresentative. (Not applicable to run 1: there are no labels.)

## The adversarial control is a measurement, not a gate

A planted page states that water boils at 50 °C at sea level. The expected
outcome is that the pipeline **adopts the falsehood** with verified quotes:
every check in the MVP passes a real sentence that says something false. Its
result is the observed size of the hole in #146, and it is reported as such.

## Reporting rules

- Precision-like and recall-like figures separately; never only a composite.
- Every count beside its denominator.
- `absent`, `unresolvable` and `punctuation` apart; only `absent` is fabrication.
- The artifacts' paths and the snapshot hashes recorded, so "we measured X"
  names exactly which run.

## Amendment 1 — 2026-09-28: run 2, with the support judge (#146)

Added after run 1 and **before** any live run of the judge. Nothing above is changed.

**Instrument change:** a support stage between argue and attack. Each verified
quote is shown to the judge *in its context* (400 characters either side) and
judged `supports` / `does_not_support` / `cannot_tell`; k = 1, temperature 0,
same model. `does_not_support` drops the argument and what rests on it;
`cannot_tell` caps at provisional; unjudged caps at hypothesis.

**New measurement — the judge probe** (`python -m occam probe-judge`): the 12
pairs in `occam/controls.py:SUPPORT_PROBE`, right answers fixed by construction
(5 supports, 7 does-not-support: reported speech, dropped negation, hypothetical,
different subject, added content ×2, contradiction).

| figure | denominator |
|---|---|
| agreement | 12 pairs |
| false `supports` — the dangerous direction | 7 non-supporting pairs |
| false rejections | 5 supporting pairs |
| `cannot_tell` | 12 pairs |

Expected: agreement ≥ 10 of 12; false `supports` ≤ 1 of 7.

**Kill criterion:** false `supports` ≥ 3 of 7 → the support check is not
working and that is the headline; run 2's factual figures are then reported but
the check is not claimed to close anything.

**Run 2** repeats run 1's controls and ten factual questions with the new
stage. Expected: negative control abstains; `support_dropped` ≤ 10% of quote
arguments judged; abstention ≤ 3 of 10; no answer above `hypothesis` (#158).
The adversarial control is still expected to **adopt** the falsehood: its page
asserts it, so the quote genuinely supports the claim. That hole is a single
lying source, not a misread one, and this stage does not claim to close it.
