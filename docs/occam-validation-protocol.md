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

### Results — 2026-09-30, read against the predictions above

Run 3 (`traces/occam/run3/`, `traces/occam/run3-controls/`; all 13 artifacts
replay to their stored answers with no key):

| prediction | result |
|---|---|
| `question_number_added` 0 (baseline 1 of 36) | ✓ **0 of 42** quote arguments (q01 0 of 5, q04 0 of 7 — the only two questions it can fire on) |
| no support drop of a quote carrying a question number | ✓ 0 |
| `support_dropped` ≤ 10% | ✓ **0 of 42** |
| abstention ≤ 3 of 10 | ✓ 0 of 10 |
| `established` 0 of 10 (by construction) | ✓ 9 `hypothesis`, 1 `open` |
| positive answers "1987" | ✓ `hypothesis` |
| negative abstains | ✓ |
| adversarial adopts at `hypothesis`, single host | ✓ bound by "rests on a single source (controls.occam.invalid)" |

**Kill criteria: none triggered.**

**One real instance, read:** q04's answer still says "in 1940" — but now as an
*inference* over three quotes, one of which states the date ("collapsed into
Puget Sound the morning of November 7, 1940"). That is the instruction working as
written: the detail got its own quote.

**q04 is `open`, and that is not #161.** Two Wikipedia pages disagree: one says
the bridge fell "under high wind conditions", the other that "moderate winds
produced aeroelastic flutter". Both quotes are verbatim; the attack stage paired
them as mutual undermining, and the answer, which says "high winds", is rebutted
by the "moderate" quotes. `open` is the pipeline reporting a disagreement between
its sources, as it should.

## Note — 2026-09-30: the question's premise in the model's own steps (#179)

Not an amendment: argue, support and status are unchanged, and every stored run
replays to the answer it stored (run 2, its re-judge and run 3: 33 of 33).

Amendment 4's counter reads quote steps only. An *inference* can carry the
question's premise too, and no judge reads inference steps. A new counter,
again a count and never a decision: `question_number_unquoted` = inference and
analogy steps whose conclusion carries a whole number from the question that
**no quote beneath them states, directly or through other steps**, over those
steps as argued, before support drops any. It is shown only on artifacts made
from now on (`counter_set: 2`), so that older ones still replay. Baselines,
measured offline with the shipped function by forcing it on:

| run | argue prompt | `question_number_unquoted` |
|---|---|---|
| run 2 | 1 | **4 of 14** (q01 ×2 "1986", q04 ×2 "1940") |
| run 3 | 2 | **1 of 21** (q01 "1986") |

**Why not a cap on status:** there is nothing for a cap to catch. A quote
step's conclusion carrying a number its quote lacks is not literally in the
quote, so it is capped as a restatement. Every inference is capped as the
model's step. Neither can be `established`, whatever the sources. A law over
random trees on two hosts checks it: `established` occurs, and no flagged
argument reaches it. Raising the inference, analogy or restatement ceiling
fails that law. Run 3's flagged step (q01 A0001) is not even the answer
shown. If a later change ever lifts an inference above `hypothesis`, that law
is what has to be answered.

*Added later (#181):* both premise counters read only whole numbers. From
`counter_set: 3` on, each counter says what it could read, every time: "the
question has 1 whole number(s) to check (1986)", or "the question has no whole
number, so this cannot fire". Eight of the ten questions have none, so on
those a zero means "could not look", not "did not happen". A false premise
that isn't a number is untested; that control is #183.

## Amendment 5 — 2026-10-01: a fourth control, the false premise in the question (#183)

Added before any live call under the change. Nothing above is changed.

**Instrument change:** a fourth control, `false_premise`. The question carries
the falsehood and the page carries the truth: *"Why does the Varenna Accord
allocate meltwater by population?"*, asked over the positive control's own page,
which says the accord allocates "in proportion to each state's catchment area".
The subject is invented, as in every control, so a right answer can only come
from the page. Only the detail is false, and it isn't a number, so neither
premise counter can see it (#181).

The issue proposed a real subject read from Wikipedia ("…Tacoma Narrows Bridge
collapse in an earthquake?"). It was not used: the model knows that story from
memory, so a correct answer would not show that the pipeline read the page.

**How it is scored:**
- **PASS:** the pipeline abstains, or its answer never mentions "population"
  (any case).
- **FLAG:** the answer mentions it. "Not by population" and "by population"
  share the word, so the control never scores a mention. A person reads the
  answer and records **adopts** or **rejects** below. A flag is never a pass,
  and it never voids or stops the run (`verdict` prints a `READ:` line; the
  command's exit code is unchanged).

**Run 4 (controls only)** = `python -m occam controls --out traces/occam/run4-controls`:
same model, same-answer judge on, `argue_prompt 2`, `counter_set 3`. The factual
questions are not re-run: nothing that touches them has changed since run 3.

**Predictions:**
- `false_premise`: **PASS**. It answers from the page ("catchment area") without
  "population", or it abstains. If it answers, the status is at most
  `hypothesis` (one host, Amendment 2).
- On `false_premise`, both premise counters print "the question has no whole
  number, so this cannot fire" (#181). This is the first live artifact under
  `counter_set 3`.
- positive answers "1987"; negative abstains; adversarial **adopts** the
  falsehood at `hypothesis`, bound by its single host (as in Amendment 4).
- every artifact replays to its stored answer with no key.

**Kill criteria:** unchanged (positive missed → VOID; negative answers → STOP;
adversarial at `established` → the corroboration change has failed). New:
`false_premise` **adopting** the premise, at any status, is the headline of the
run. It means the pipeline carries a false detail from the question into an
answer it vouches for, and a counter that reads numbers can't catch that. A live
call that fails is reported with the control it cost, never dropped silently.

### Results — 2026-10-01, read against the predictions above

Run 4 (`traces/occam/run4-controls/`; all 4 artifacts replay to their stored
answers with no key; `argue_prompt 2`, `counter_set 3`, judge on):

| prediction | result |
|---|---|
| `false_premise` PASS | ✓ **abstained**, 3 of 3 argue samples `{"answer": null, "steps": []}` |
| its premise counters print "cannot fire" | ✓ both, at **0 of 0**: no argument was made for them to read |
| positive answers "1987" | ✓ `hypothesis` (bound: the quote restated in the model's words) |
| negative abstains | ✓ |
| adversarial adopts at `hypothesis`, single host | ✓ bound by "rests on a single source (controls.occam.invalid)" |
| every artifact replays | ✓ 4 of 4 |

**Kill criteria: none triggered. No FLAG to read.**

**What the pass does and doesn't show.** The model declined to answer, so the
refusal came from the model and not from the mechanism. Nothing reached the
support judge (0 replies), the attack stage (0) or the same-answer judge (0).
This run shows that this model, under argue prompt 2, does not carry this false
detail into an answer. It does **not** show that the pipeline would stop one if
the model did. That path (an inference stating the false detail, which no judge
reads and which no number counter can see) is tested only offline, with
scripted replies (`test_an_inference_that_adopts_the_premise_is_flagged_for_reading`);
there the control flags it. One question, one model, one run: this is not a rate.

The abstention reason reads "the model found no answer in the sources", but the
page does answer the corrected question ("catchment area"). A reader can't tell
"the premise is false" from "the sources are silent".

## Amendment 6 — 2026-10-04: run 5, a second source, prompt 3 and the reason check (#208)

Added before any live call under the change. Nothing above is changed.

**Why a run.** In runs 2–4 every answer rests on one host (Wikipedia), so
`established` was unreachable by construction (Amendment 2), and 33 of 34
replayable answers are `hypothesis`. Calibration needs a spread of statuses.
Three changes go in together, because measured offline none moves a status
alone: lifting the "restated in the model's words" limit changed 0 of 31
statuses (#201), since the single-source limit ties with it.

**Instrument changes** (the commit carrying this amendment):
- **Web pages as a second source (#209).** OpenRouter's web-search plugin,
  run on the same model with Wikipedia and its mirrors excluded, discovers up
  to 3 URLs per question (`web_sources 3`). Only the URLs are kept. Each page
  is fetched by Occam, snapshotted and quoted like any other, and every check
  applies to it. The plugin's own text is stored for audit and never read.
- **Argue prompt 3 (#210).** A quote's conclusion is copied from its quote. A
  passage stating the answer, reason included, is the answer. A point two
  sources state is quoted from each.
- **The reason check (#194, `why_check 2`).** On a question asking for a
  cause, a quote answer stays at `hypothesis` unless its words carry a causal
  link *and* a fresh judge call says it gives the reason asked for.
- Everything else as in Amendment 4: `openrouter/z-ai/glm-5.2`, k = 3,
  temperatures 0.7 / 0.2, same-answer judge on, `veto_words 2`, 3 Wikipedia
  pages per question.

**Run 5** = `python -m occam measure --out traces/occam/run5` (the ten
questions, `--web 3` by default) and `python -m occam controls --out
traces/occam/run5-controls`. The controls take their pages by hand, so no web
search runs for them: they test that nothing else moved.

**Baselines** (run 3, measured 2026-10-04 by replay): quote arguments whose
conclusion is not their quote's own words, **42 of 42**; answers that are
quotes, **3 of 10** (7 inferences); hosts per question, **1** in 10 of 10;
statuses, 9 `hypothesis`, 1 `open`. Across runs 2–4, quote answers to the 18
answered cause questions: 7, all stating a link, **0 of 7** in the source's
own words.

**Predictions:**
1. Sources: at least 2 readable web pages in **at least 8 of 10** questions
   (one probe on 2026-10-03: 4 of 5 fetched; Britannica returned 403). Hosts
   per question rise from 1 to at least 2 in those questions.
2. Restated quote arguments fall from 42 of 42 to **at most half** of the quote
   arguments made.
3. Quote answers rise from 3 of 10 to **at least 5 of 10**.
4. `established`: **1 to 4 of 10.** It needs two verbatim quotes on two hosts
   that the claim-lens judge calls the same, which the strict lens rarely
   does (1 claim pair in 37 runs before prompt 3). Most answers stay
   `hypothesis`.
5. The reason check: on the 6 cause questions, every quote answer is listed
   with its link and the judge's verdict. No cause question reaches
   `established` with a quote answer whose link check failed (this holds by
   construction; listing it checks the wiring live).
6. Controls as in Amendment 5: positive answers "1987"; negative abstains;
   adversarial adopts at `hypothesis`, bound by its single host;
   `false_premise` PASS.
7. Every artifact replays to its stored answer with no key.

**Read by hand, reported with every `established` answer:** the hosts and
quotes that corroborate it, and whether the two are independent. Copies (two
agencies publishing one text, as NASA's and NOAA's pages on the sky do) and
Wikipedia mirrors are counted apart. They are a known weakness of counting
hosts (`status.py`), measured here, not assumed away.

**Kill criteria:** unchanged (positive missed → VOID; negative answers → STOP;
adversarial at `established` → STOP: corroboration has failed). New: if the web
search fails or finds nothing beyond Wikipedia on **5 or more of 10**
questions, predictions 1–4 are **NOT MEASURED** and are reported as such, not
as a negative. A failed live call is reported with the question it cost. The
spend is read from OpenRouter's usage counter before and after and reported.

**Status spread.** The calibration gate asks for at least 3 statuses at 10% or
more. Ten questions cannot show that reliably; run 5 reports the counts with
their denominator and says whether the gate *would* be met, nothing more.

### Note — 2026-10-04: the model changes before run 5

Written before run 5, after one live `ask` on the new instrument. Nothing
above is changed.

- **Model:** `kie/gpt-5-2` (GPT-5.2 through kie.ai), not `openrouter/z-ai/glm-5.2`,
  whose account ran out of credit. Every model stage changes model at once.
  **So run 5 against run 3 can't separate the model from the prompt or the
  source.** The baselines above stay as they are, and run 5 reports this beside
  each comparison.
- **Web search:** kie.ai returns no structured citations. The URLs are read out
  of the model's reply, and may come from its search or its memory. The pages
  are fetched and checked either way. Prediction 1 counts pages fetched with
  text, so a URL that doesn't exist counts against it.
- **The reason check:** "since" now counts as a causal link unless a number
  follows it. The one live reply used "Since blue light wavelengths scatter
  more, the diffuse sky … is blue", a true reason the earlier word list
  rejected.
- **Spend:** read from kie.ai's credit balance before and after each command,
  and from the credits each call reports. The one live `ask`: **6.66 credits**.
- **Read in run 5:** the live `ask` kept two answers apart for "negation
  differs: not" over "The sky looks blue, *not violet*". That `not` negates a
  noun phrase, not the statement, like "without" in #192. Every negation veto in
  run 5 is listed and read by hand.

Command: `python -m occam measure --model kie/gpt-5-2 --out traces/occam/run5`
and `python -m occam controls --model kie/gpt-5-2 --out traces/occam/run5-controls`.

### Note — 2026-10-04 (later): run 5 moves to `kie/gemini-3.1-pro`

Written before the run that is reported. Two attempts on `kie/gpt-5-2` ended
early and are **not** run 5:
- **Attempt 1** stopped at q01's first argue call: kie.ai returned `{"code": 500,
  "msg": "Server exception…"}`, with nothing written. Since then, a 5xx or 429
  is asked again 3 times with pauses.
- **Attempt 2** answered q01 and q02 (kept in `traces/occam/run5-attempt2/`,
  never reported as run 5), then hit 500 on every try at q03. Measured
  directly, gpt-5-2 on kie.ai accepts about **22k input tokens** (80k characters
  worked; at 90k it returned an ordinary reply, "The message you submitted was
  too long…"; at 170k and above it returned 500). A six-source argue prompt
  runs to about 240k characters. That reply is now an error, never a sample.

**Model for run 5:** `kie/gemini-3.1-pro`. It took a 240k-character prompt
(68k tokens, 6.83 credits), and its search tool (`googleSearch`) returns URLs
when asked to list them. Everything else is as in Amendment 6 and the note
above. Run 5 against run 3 still can't separate the model from the other
changes. The four controls above ran on `kie/gpt-5-2`, so they are re-run on
this model too, into `traces/occam/run5-controls-gemini/`.

### Note — 2026-10-04 (later still): run 5 resumed after a timeout

The run on `kie/gemini-3.1-pro` wrote q01 and q02, then a read at q03 timed out
after 300 seconds and stopped it. It is **resumed**, not restarted: `measure
--resume` keeps q01 and q02 as written, and runs q03–q10 on the same model, now
retrying a timed-out read and waiting up to 600 seconds. Each artifact
records its own `as_of`. The four controls on this model finished in the
first pass (`traces/occam/run5-controls-gemini/`, all PASS).

### Results — 2026-10-04, read against the predictions above

Run 5 is `traces/occam/run5/` on `kie/gemini-3.1-pro`, with `argue_prompt 3`,
`web_sources 3`, `why_check 2`, the judge on and `veto_words 2`. The model
changed as well as the other three things, so no row below separates the model
from the change. q01–q02 come from the first pass (commit 152916c) and q03–q10
from the resumed pass (commit 16c69b6). The two commits differ only in
`--resume` and the timeout retry. All 10 artifacts replay byte for byte to
their stored answers with no key. The scorer is the one used for every row.

| prediction | result |
|---|---|
| 1. ≥2 readable web pages in ≥8 of 10 | ✓ **8 of 10**, exactly at the line. 20 of 30 pages fetched had text; the 10 without were HTTP 403 (britannica, noaa, loc, amnh, britishmuseum, smarthistory) or 404 (sciencedaily, structuralengineer, nasa.gov, livescience). q06 and q09 have 1 readable web page each. |
| 2. restated quote arguments ≤ half | ✓ **0 of 64** (run 3: 42 of 42). |
| 3. quote answers ≥5 of 10 | ✓ **7 of 10** (run 3: 3). 4 of the 7 quote a web page (spaceplace.nasa.gov, britannica.com, simscale.com, news.utexas.edu) and 3 quote Wikipedia. q01, q05 and q10 are inferences. |
| 4. `established` 1–4 of 10 | ✗ **0 of 10.** All 7 quote answers are bound by "rests on a single source". See below. |
| 5. the reason check, listed | ✓ wired. Cause questions are q01, q02, q04, q05, q07 and q08. q01 and q05 are inferences, so the reason judge doesn't read them. The 4 quote answers (q02, q04, q07, q08) all pass the link check and get `gives_reason` from the judge. Read by hand, q07's link is **the temporal "since"** ("the leading hypothesis *since the 1980s*"): the rule lets a "since" through when a word follows it, and "the" is a word. The judge's `gives_reason` is right on reading (the sentence names the asteroid), but the link check passed for the wrong reason (#213). No status moved, because the single source binds q07 anyway. |
| 6. controls | ✓ all 4 PASS on this model (`run5-controls-gemini/`, and on gpt-5-2 in `run5-controls/`); adversarial at `hypothesis`, bound by its single host; all 4 replay. |
| 7. every artifact replays | ✓ 10 of 10, plus 4 of 4 controls. |

**Kill criteria:** none triggered. Web search found pages beyond Wikipedia in
10 of 10 questions. **Status spread:** 10 `hypothesis` out of 10, so 1 status,
and the calibration gate would not be met.

**Why nothing was established.** In none of the 7 quote answers did a second
host quote the same words. So corroboration needed the claim-lens judge to
merge the answer with another host's sentence. Every cross-host claim pair
holding an answer was kept apart, and every reason, read by hand, is the same
one: **one sentence says more than the other.**
- **q02:** weather.gov says "The earth's spin axis is tilted with respect to
  its orbital plane. This is what causes the seasons." The answer (from
  spaceplace) says "Earth's tilted axis causes the seasons." The judge's
  reason: "Y specifies … the spin axis … which X does not mention."
- **q08:** spaceplace says "Blue light is scattered more than the other colors
  because it travels as shorter, smaller waves." The answer is "Since blue
  light wavelengths scatter more, the diffuse sky seen in daytime is blue."
  The judge called them different.
- **q02, q04, q07, q09:** the Wikipedia sentence carries a number the answer
  lacks ("23.4°", "1940", "1820s"), and the claim-lens veto stops it before
  any judge sees it.

The claim lens asks whether two sentences are **the same**, and the judge
answers that faithfully. But vouching for an answer needs a one-way relation:
**the second host's sentence states everything the answer states.** A sentence
that says more still vouches for one that says less. The claim lens was made
strict on purpose (#172: `established` vouches for every word shown). That
strictness is about the answer's words, and a superset covers all of them.
Whether an entailment lens would lift q02 can't be computed by replay, because
it needs new judge calls. It is **not measured** (#212).

**All 24 vetoes, read by hand:** every one is "numbers differ" under the claim
lens, where one side has a number and the other has none. Each is correct
under the rule as written. There were no negation vetoes, so the "not violet"
case from the live `ask` didn't come up.

**Spend:** read from kie.ai's balance. **115.53 credits** for all of run 5 on
gemini, 9703.43 before and 9587.90 after. That is 27.03 for the first pass
(the four controls, q01, q02, and the q03 calls lost to the timeout) and 88.50
for the resumed pass. The calls themselves report 86.69 for the resumed pass,
1.81 below the drop in the balance. Where the 1.81 went is not known: the
web-search calls report their credits through the same client, so they are
not the obvious gap.
