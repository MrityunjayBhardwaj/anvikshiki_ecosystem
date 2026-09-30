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

## Amendment 2 — 2026-09-28: corroboration before `established` (#162)

Added after run 2 and **before** any live run under the change. Nothing above is changed.

**Instrument change, mechanical, no model:** an argument that would be
`established` keeps it only if the grounded-IN quote arguments sharing its
conclusion, each with an established ceiling of its own, cite snapshots from
at least 2 hosts **and** at least 2 distinct texts. Otherwise it is `hypothesis`, bound by "rests on a single
source (<host>)". Hosts are host names with `www.` removed, not registrable
domains. They proxy independence weakly in both directions: two pages on one
site count once, and two sites copying each other count twice.

*Revised before any live run (#165):* the text condition was added after
review found that identical bytes fetched from a mirror merge into one
snapshot carrying both URLs, so hosts alone let one document corroborate
itself. Identical text is one source, as `snapshot.py` already counts it.

**Consequence registered in advance:** gather searches Wikipedia only, so every
factual answer is one host and **`established` 0 of 10 is guaranteed by
construction** in any run with the current gather. It is not a finding and
must not be reported as one. Only a second, non-Wikipedia source can make
`established` reachable again.

**Replay of run 2, no model calls** (`python -m occam replay`, key unset,
`traces/occam/run2/q01..q10.json`): **10 of 10 replays match the stored
answer; 0 statuses move.** All ten were already `hypothesis` under #158, and
the single-host cap sits above a bound that is already lower. The run 2
adversarial control saved no artifact, so it cannot be replayed exactly; its
live form (the conclusion verbatim in a verified, supported quote) is a law
(`test_the_lying_page_in_the_form_run_2_saw_is_capped_by_its_single_host`),
and under the change it is `hypothesis`, bound by
"rests on a single source (controls.occam.invalid)".

**Expected in any run 3:** the adversarial control still **adopts** the
falsehood, since corroboration cannot change what is concluded, only how
strongly. It is expected at `hypothesis`, bound by its single host. If it is
`established`, the change has failed and that is the headline.

## Amendment 3 — 2026-09-30: the same-answer judge, probed and applied to run 2 (#172)

Added after the judge was merged (#173, 21eff61) and **before** any live call of
it. Nothing above is changed.

**Instrument under test:** the same-answer judge as merged — a mechanical veto
(numbers, negation), then one fresh call per pair in each order, temperature 0,
the run's own model (`z-ai/glm-5.2` via OpenRouter); a pair merges only if both
orders say `same`. Question lens = consistent answers to this question; claim
lens = each statement says everything the other says.

### The probe — `python -m occam probe-same`

Pairs whose right answer is fixed before any model sees them
(`occam/sameprobe.py`). Composition measured offline at registration:

**Flips** — run 2's 29 distinct answer conclusions (10 questions), each changed
by code in one way; every flip is `different` by construction.

| kind | lens | pairs | vetoed | reach the judge |
|---|---|---|---|---|
| number swapped (+1) | claim | 15 | 15 | 0 |
| number swapped | question — only on "when" questions | 11 | 11 | 0 |
| "not" inserted, main clause only | claim / question | 13 / 13 | 13 / 13 | 0 |
| cause and effect reversed | claim / question — only on why/cause questions | 11 / 11 | 0 | 22 |
| antonym swapped (fixed list) | claim only | 31 | 0 | 31 |
| **total** | | **105** | **52** | **53** (106 calls) |

A flip is labelled under the question lens only when it changes what the
question asks (a date on a "when" question, the cause on a "why" question, the
main assertion when negated). Antonyms can land on a detail the question does not
ask ("high-latitude aurora"), so they are claim-lens only. **Consequence: under
the question lens, only the 11 cause/effect reversals test the judge itself;**
every other question-lens flip is decided by the veto.

**PAWS-Wiki** — human-labelled paraphrase pairs built from word swaps (Zhang,
Baldridge & He, NAACL 2019). Licence: *"may be freely used for any purpose,
although acknowledgement of Google LLC ("Google") as the data source would be
appreciated"* — data © Google LLC. Google's own bucket returned 403 on
2026-09-30, so the copy is the authors' Hugging Face release,
`google-research-datasets/paws` @ `161ece9501cf0a11f3e48bd356eaa82de46d6a09`,
`labeled_final/test-00000-of-00001.parquet` (sha256
`ae342ff12bb84b84b95f468abf5db6cb7c7bd578271299fe9c99be75b8132f4d`, 8000 rows:
3536 paraphrase, 4464 not), converted once to JSONL with keys sorted (sha256
`0e2e68dc4a3e1a6120969c1c042636934cae24549ca5e388bed4df7fcc08405e`; the loader
refuses other bytes). Draw: `random.Random(172)`, 100 paraphrases then 100
non-paraphrases, each pool sorted by id. Claim lens only (PAWS has no
questions); the question shown is empty. Vetoed by numbers: 1 paraphrase, 2
non-paraphrases; 197 pairs reach the judge (394 calls).

**Held out?** PAWS: yes — labels are human and not ours. Flips: their labels are
fixed by construction, but the generator was written by the same hand as the
judge's prompt, so they are **not held out**; say so beside the figure.

**Figures, each with its denominator:** wrong merges on flips (of 105; of the 53
the judge saw); wrong merges on PAWS non-paraphrases (of 100); missed merges on
PAWS paraphrases (of 100); `cannot_tell`, order disagreements, malformed and
unanswered pairs, each over the pairs they could occur in. A call that fails
after retries is stored as an empty reply and counted as **unanswered**, never
as the judge keeping a pair apart.

**Kill criteria** (the limits the user set on 2026-09-30):
- **any** flip merged → **STOP**.
- more than **5 of 100** PAWS non-paraphrases merged → **STOP**.
- any expected-`different` pair unanswered → **INCOMPLETE**: the limits cannot
  clear until it is answered.

*Added after the first probe run and before its unanswered calls were re-asked
(#175):* an empty reply counts as unanswered, like a failed call, read from the
stored bytes. The first run left 6 expected-`different` pairs unanswered (4 ×
HTTP 402 "in-flight budget", 2 empty replies) and 1 paraphrase. They are re-asked
with `python -m occam probe-same --fill <run> --out <new>`: the same prompts, model
and temperature, 2 calls at a time; every reply already returned is kept byte for
byte, and the re-asked calls are listed in the new file's `filled`. The limits
are read on the filled file.

STOP means the judge merges answers that say different things: the default is
turned back off in a follow-up, and run 2's re-judged figures below are reported
but not claimed as merges of rewordings. Missed merges on PAWS paraphrases are
reported, not gated: PAWS "paraphrase" is a looser human judgement than the
claim lens's "each says everything the other says", so some misses are that
strictness working as designed.

### Run 2, re-judged — `python -m occam rejudge traces/occam/run2 --out traces/occam/run2-judged`

Only the judge is new: every other stage is read from the stored artifact, not
re-asked, and the rejudge refuses a model other than the one the run recorded.
The rejudged artifacts must replay to their own stored answers.

Measured offline with `candidate_pairs` over the ten run 2 artifacts: 28
question-lens pairs; 1 vetoed (q04, "without" on one side only — a **known false
veto**); 27 judged = **54 calls**. **0 claim-lens pairs**: no run 2 quote states its
conclusion word for word, so corroboration has nothing to act on and **0 statuses
can move — by construction, not a finding.**

**My labels, not held out:** all 28 pairs `same` under the question lens — each
question's answers are consistent (q03's "1912" is less precise than "6 January
1912", and q10's third answer omits "regulate cellular metabolism", both allowed
by the question lens). So run 2 **cannot show a wrong merge** (denominator 0);
it measures missed merges only, of 28, the veto included.

**Predictions** (carried from #172, registered before any call): q06 3 → 1;
q03 3 → 1; q01 merges (the year is the question's); agreement rises in at most
about 5 of 10; 0 statuses move. The earlier "q10 stays ≥ 2" is superseded by the
consistency decision on #172. The "at most 5" prior disagrees with my own labels
(all same): it records that I expected the judge to be stricter than I am.

### Results — 2026-09-30, read against the predictions above

**Probe** (`traces/occam/probe-same-a3.json`, 500 calls at 8 at a time; 7 calls
unanswered — 4 × HTTP 402, 3 empty — re-asked into
`traces/occam/probe-same-a3-filled.json`, the other 493 replies byte-identical):

| figure | result | held out? |
|---|---|---|
| flips merged (wrong merges) | **0 of 105** (52 vetoed; 0 of the 53 the judge saw) | no — same hand as the prompt |
| PAWS non-paraphrases merged (wrong merges) | **1 of 100** (id 5691) — limit 5 | yes |
| PAWS paraphrases kept apart (missed merges) | **48 of 100** (1 vetoed, 47 judged apart) | yes |
| orders disagreed | 3 of 11 question-lens cause reversals; 11 of 99 and 2 of 98 judged PAWS pairs | — |
| malformed | 1 PAWS reply (broken JSON) | — |

**Kill criteria: none triggered.** The judge stays on by default.

The 3 order disagreements on reversed cause and effect are the closest call in
the probe: under the question lens the judge said `same` in **one** order for 3
of 11 reversals, and only the both-orders rule kept them apart. 48 missed merges
on PAWS paraphrases is the claim lens's strictness at work (e.g. it splits
"novelist" from "author"), reported, not gated.

**Run 2, re-judged** (`traces/occam/run2-judged/`, 54 calls; rejudged artifacts
replay 10 of 10): 27 of 27 judged pairs merged, 0 order disagreements; missed 1
of 28 — the known false veto on q04. Wrong merges: none possible, denominator 0.

| prediction | result |
|---|---|
| q06 3 → 1 | ✓ |
| q03 3 → 1 | ✓ |
| q01 merges | ✓ |
| agreement rises in at most about 5 of 10 | **✗ — rose in 9 of 10** (q04 held by its veto) |
| 0 statuses move | ✓ (by construction) |

The failed prior is the finding: the judge is as lenient as my own labels, not
stricter. Taken with the 3 one-order `same` verdicts on reversed causes, the
question lens leans toward merging, and both orders are what keep it honest.

## Amendment 4 — 2026-09-30: run 3, argue told not to repeat the question (#161)

Added before any live call under the change. Nothing above is changed.

**Instrument change:** the argue instruction gains one rule: *a quote step's
conclusion says only what its quote says; do not repeat details from the question
(a date, a place, a name) unless the quote states them; if the answer needs one,
quote the passage that states it as its own step.* Recorded as `argue_prompt: 2`
in each artifact's params; artifacts without the field were argued under 1 and
replay unchanged (run 2 and its re-judge: 20 of 20 match). The support judge is
**unchanged and stays strict**: it must not vouch for a detail the question
supplied, because the question's premise may be false.

**Why:** run 2's one support drop (q04, A0003) was a true quote whose conclusion
repeated the question's "in 1940". The nearest "1940" on the page was 904
characters from the span, outside the judge's 400-character window, so the drop
was correct given what the judge saw. The fault was argue's.

**New counter, a count and never a decision:** `question_number_added` = quote
arguments whose conclusion carries a whole number from the question that their
quote does not state, over all quote arguments **as argued, before support drops
any**. Numbers are read by splitting on whitespace ("1940s" and "1,000" are not
read). **It can only fire on questions that contain a number: 2 of the 10 (q01
"1986", q04 "1940").** Baseline, run 2 under prompt 1, measured offline with the
shipped function: **1 of 36** — exactly the argument support dropped.

**Run 3** = `python -m occam controls --out traces/occam/run3-controls` and
`python -m occam measure --out traces/occam/run3`, same model, same pre-registered
questions, the same-answer judge **on** (the default since #173).

*Attribution:* run 3 changes two things against run 2 — the argue prompt and the
judge. The counter and support drops are attributable to the prompt (the judge
runs after them and cannot move them). Positions and agreement are not: they move
with both, and the judge's own effect on run 2 is already measured (Amendment 3).

**Predictions:**
- `question_number_added`: **0** across the run (baseline 1 of 36).
- support drops of a quote whose conclusion adds a question number: **0**.
- `support_dropped` ≤ 10% of quote arguments judged (as Amendment 1).
- abstention ≤ 3 of 10 (as Amendment 1; run 2 abstained on 0).
- `established` **0 of 10 — by construction** (Wikipedia only, Amendment 2); not a finding.
- controls: positive answers "1987"; negative abstains; adversarial **adopts** the
  falsehood at `hypothesis`, bound by its single host (Amendment 2).

**Kill criteria** (unchanged): positive control missed → VOID; negative control
answers → STOP; adversarial at `established` → the corroboration change has failed,
and that is the headline. New for this run: a live call that fails (including an
empty reply that stays empty, #175) is reported with the question it cost, never
dropped silently; a question lost that way is reported, not re-asked into the
same folder.
