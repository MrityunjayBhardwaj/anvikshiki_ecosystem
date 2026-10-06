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

## Amendment 7 — 2026-10-04: run 6, a source that covers the answer corroborates it (#212)

Added before any live call under the change. Nothing above is changed.

**Why a run.** In run 5, prediction 4 failed: **0 of 10** answers were
`established`, against 1–4 predicted. Read pair by pair, the cause was
corroboration's test, not the sources. A second host counted only if the
claim-lens judge called its sentence *the same* as the answer's, and every
pair across two hosts was kept apart because one sentence said more.
`established` vouches for the answer's words only, so what it needs is
one-way: does the source state everything the answer states?

**The probe that licensed building it** (2026-10-04, `traces/occam/probe-covers/`,
1.78 credits). The criteria were written before any call. On 7 controls
written by hand, all 6 that must stay apart did (a different cause, a source
that says less, a conflicting number, a negation, water at 50 °C, related but
not covering), and the one that must cover did. Of run 5's 15 pairs across two
hosts, 5 covered, lifting q02 (weather.gov, Wikipedia) and q04 (Wikipedia).
Those pairs were chosen after reading them, so the probe licensed the build
and measured no rate. Its prompt differs from the built one only in layout
(one blank line).

**Instrument change** (commit 93eb83c, `covers_check 2`, occam/covers.py):
- For each answer that is a quote in its own words, every other such
  conclusion from a host the answer isn't on is asked about, in a fresh call,
  with both orders shown. It covers only if both orders say `covers`.
- Vetoed before any call: a number in the answer that the source lacks or
  contradicts, or a negation on one side only. A source that only adds a
  number reaches the judge.
- The status stage adds the covering sources' hosts and texts to the answer's
  own. Covering never chains. Replies are keyed by (answer, source, order).
- **Replay of run 5 under it**, with the probe's replies: q02 and q04 move
  from `hypothesis` to `established`, and nothing else moves. 58 of 70 stored
  runs replay byte for byte, as before.
- Also in force since run 5: `why_check 3` (#213).
- Everything else as in run 5: `kie/gemini-3.1-pro`, k = 3, temperatures
  0.7 / 0.2, judge on, `veto_words 2`, 3 Wikipedia pages and `--web 3`.

**Run 6** = `python -m occam measure --model kie/gemini-3.1-pro --out
traces/occam/run6` and `python -m occam controls --model kie/gemini-3.1-pro
--out traces/occam/run6-controls`.

**Baselines** (run 5, measured 2026-10-04): ≥2 readable web pages in 8 of 10;
restated quotes 0 of 64; quote answers 7 of 10; `established` 0 of 10; 10
`hypothesis`.

**Predictions:**
1. Sources: ≥2 readable web pages in **at least 7 of 10** questions. The
   search is not deterministic: run 5 got 8 with 10 of 30 pages refused.
2. Restated quote arguments stay at **at most 10%** of quote arguments.
3. Quote answers: **at least 5 of 10**.
4. `established`: **1 to 4 of 10.** This is the prediction run 5 failed. The
   replay of run 5 gives 2, and new pages and samples will move it.
5. Every `established` answer is read by hand: the covering sentence, its
   host and page, and whether the two pages copy each other. Copies are
   reported as such and not counted as independent.
6. The reason check: no cause question reaches `established` with a quote
   answer whose link or judge failed (by construction; the listing checks the
   wiring live).
7. Controls as in Amendment 5. Each control has one host, so the covers check
   asks no question there, and the controls only show that nothing else
   moved. The adversarial pair (50 °C against 100 °C) is tested offline: it is
   vetoed before any judge.
8. Every artifact replays to its stored answer with no key.

**Kill criteria:** those of Amendment 6, plus: an `established` answer that is
**false on reading**, or whose covering sentence does **not** in fact state
it, means **STOP: covers has failed**, and it is reported before anything
else. Spend is read from kie.ai's balance before and after each command.

**Status spread.** As in Amendment 6: run 6 reports the counts with their
denominator and whether the calibration gate *would* be met.

### Results — 2026-10-04, read against the predictions above

Run 6 is `traces/occam/run6/` and `traces/occam/run6-controls/`, from commit
45285e8 on `kie/gemini-3.1-pro`, in one pass each. All 10 artifacts and all 4
controls replay byte for byte to their stored answers with no key. Across every
stored run, 69 of 81 replay; the 12 that don't are the same pre-artifact runs
as before (challenger ×2, run1 ×10). The scorer is run 5's, plus a listing of
every cover pair with its veto or its two verdicts.

| prediction | result |
|---|---|
| 1. ≥2 readable web pages in ≥7 of 10 | ✗ **5 of 10.** 17 of 30 pages fetched had text. The 13 without: 7 were HTTP 403 (britannica ×4, physics.stackexchange, britishmuseum, nih.gov) and 6 were HTTP 404 (thestructuralengineer, rainbowsymphony, earthsky, nps.gov, smithsonianmag, optics4kids). A 404 is a link the search reply gave that does not resolve. This is the fetch, not the covers check, and the check can only work with pages it gets. |
| 2. restated quote arguments ≤10% | ✓ **0 of 47.** |
| 3. quote answers ≥5 of 10 | ✓ **7 of 10** (q01, q02, q04, q06, q07, q08, q09). q03, q05 and q10 are inferences. |
| 4. `established` 1–4 of 10 | ✓ **2 of 10**: q02 and q04, the two the replay of run 5 predicted. |
| 5. every `established` answer read by hand | ✓ both, below. No copies found. |
| 6. the reason check, listed | ✓ wired. Cause questions are q01, q02, q04, q05, q07 and q08. q05 is an inference. q01, q02, q04 and q08 pass the link check and get `gives_reason`. q07's only link is the temporal "since the 1980s", which link rule 3 (#213) now refuses, so q07 is capped at `hypothesis` and names why. Both `established` answers had a link and `gives_reason`. |
| 7. controls | ✓ all 4 PASS, the same lines as run 5 on this model. Each has one host, so the covers check asked nothing there (0 cover replies in each). |
| 8. every artifact replays | ✓ 10 of 10, plus 4 of 4 controls. |

**Kill criteria:** none triggered. Both `established` answers are true on
reading, and each covering sentence states its answer.

- **q02**, "Earth's tilted axis causes the seasons." (spaceplace.nasa.gov).
  Covered, `covers` in both orders, by weather.gov's "The earth's spin axis is
  tilted with respect to its orbital plane. This is what causes the seasons."
  and by two Wikipedia sentences: "The seasons result from the Earth's axis of
  rotation being tilted with respect to its orbital plane by an angle of
  approximately 23.4 degrees." and "This variation in the weather (because of
  the direction of the Earth's axial tilt) results in the seasons." The first
  of these adds a number, which a source may. Copies: the longest run of text
  either web page shares with a Wikipedia page is 41 characters ("tilted with
  respect to its orbital plane"), a stock phrase, not a copied passage.
- **q04**, "The Tacoma Narrows Bridge collapsed primarily due to the aeroelastic
  flutter." (simscale.com). Covered by Wikipedia's Aeroelasticity page: "The
  original Tacoma Narrows Bridge was destroyed as a result of aeroelastic
  flutter." Both quotes were checked verbatim on their pages. The source says
  "destroyed", not "collapsed". Read as stating the collapse in substance;
  this is the one place a reader might hold the line stricter. Copies: the
  longest shared run with Wikipedia is 41 characters.

**The 18 cover pairs.** 3 were vetoed before any call: q03's two on "1912",
and q04's "did not allow wind to pass through" on the negation. 15 were judged,
30 replies, every one readable. 4 covered, all in q02 and q04. The rest, read
by hand:
- q01, q08 and q09: each source states less than the answer (the Rogers
  Commission and the burning gas; that the sky is blue; that the versions
  differ little). `does_not` in both orders is right.
- q04: Wikipedia's lede "collapsed possibly because of aeroelastic flutter" is
  hedged, and `does_not` is right. But **"the bridge collapsed because moderate
  winds produced aeroelastic flutter"** got `does_not` in both orders, while
  "destroyed as a result of aeroelastic flutter" got `covers`. The rejected
  sentence is the more literal match. The judge erred toward keeping apart,
  which costs a host and never vouches wrongly, but it is noise.
- **Order mattered once in 15**: q02's "The seasons are a result of that tilt
  and are caused by the differential intensity of sunlight" got `does_not`
  shown first and `covers` shown second. Asking both orders kept it out.

**Status spread:** 8 `hypothesis` and 2 `established` out of 10, so 2
statuses; the calibration gate would not be met.

**Spend:** read from kie.ai's balance. **86.71 credits** for all of run 6,
9586.12 before and 9499.41 after. The measure calls report 85.61. The
remaining 1.10 is the controls and any gap; the controls command does not
report its own credits, so the two are not separated.

## Amendment 8 — 2026-10-05: run 7, ask for more web pages and keep what loads (#216)

Added before any live call under the change. Nothing above is changed.

**Why a run.** In run 6, prediction 1 failed: only **5 of 10** questions had
two readable web pages, against at least 7 predicted. 13 of 30 pages had no
text: 7 refused us (HTTP 403) and 6 were 404, 5 of which are still 404 to a
browser. kie.ai's search reply carries no citations, so every URL is one the
model wrote, and some were never there. The covers check can only read the
pages it gets.

**The probe that licensed building it** (2026-10-05,
`traces/occam/probe-search/`, 4.70 credits; criteria written before each
part). Part 1: neither the plain nor the streamed reply carries citations,
and kie.ai's docs list none, so reading them is not an option. Part 2: on
run 6's 10 questions, asking for 9 links and fetching all, **8 of 10** got
readable pages on 2 or more hosts (bar 8). 20 of 88 links were 404 and 16
were 403. q03 and q09 fell short; their good hosts refuse our fetcher. One
search per question, so this licensed the build and measured no rate.

**Instrument change** (commit e728b57, `web_fill 2`, occam/gather.py):
- Ask the search for 3 × `web_sources` pages; fetch in order until
  `web_sources` readable pages on different hosts are held. A second page on
  a host already held is not fetched.
- Every failed fetch stays in the artifact. One note per question counts
  every URL named: readable on distinct hosts, each failure reason,
  same-host skips, not fetched.
- Gathering only. Replay reads the stored snapshots, so every stored run
  replays as before (72 of 84 byte for byte, the same 12 pre-artifact runs
  failing).
- **Observed live** on q09, with the real search and fetch (0.38 credits):
  5 links failed (2 × 403, 3 × 404), then 3 readable pages on 3 hosts
  (arce.org, smithsonianmag.com, worldhistory.org). Run 6 had 1.
- Everything else as in run 6: `kie/gemini-3.1-pro`, k = 3, temperatures
  0.7 / 0.2, judge on, `veto_words 2`, `why_check 3`, `covers_check 2`, 3
  Wikipedia pages and `--web 3`.

**Run 7** = `python -m occam measure --model kie/gemini-3.1-pro --out
traces/occam/run7` and `python -m occam controls --model kie/gemini-3.1-pro
--out traces/occam/run7-controls`.

**Baselines** (run 6, measured 2026-10-04): ≥2 readable web pages in 5 of 10;
restated quotes 0 of 47; quote answers 7 of 10; `established` 2 of 10 (q02,
q04); 8 `hypothesis`.

**Predictions:**
1. Sources: readable web pages on **≥2 distinct hosts in at least 8 of 10**
   questions. Counted by host, because a second page on one host is not a
   second source.
2. Every question with a web search carries the fill note, and its counts
   add up: readable + failures + same-host skips + not fetched = named.
3. Restated quote arguments stay at **at most 10%**.
4. Quote answers: **at least 5 of 10**.
5. `established`: **2 to 5 of 10.** More hosts give the covers check more
   pairs. Fewer than 2 with prediction 1 met would point at the judge or the
   answers, not the fetch, and is read pair by pair.
6. Every `established` answer is read by hand: the covering sentence, its
   host and page, and whether the two pages copy each other.
7. The reason check: no cause question reaches `established` with a quote
   answer whose link or judge failed (listed live).
8. Controls as in Amendment 7. They are given their URLs, so nothing is
   searched and the fill rule does not act.
9. Every artifact replays to its stored answer with no key.

**Kill criteria:** those of Amendment 7. An `established` answer that is
false on reading, or whose covering sentence does not state it, means
**STOP**, reported before anything else. Spend is read from kie.ai's balance
before and after each command.

**Status spread.** As in Amendment 6.

### Results — 2026-10-05, read against the predictions above

Run 7 is `traces/occam/run7/` and `traces/occam/run7-controls/`, from commit
555e645 on `kie/gemini-3.1-pro`, in one pass each. All 10 artifacts and all 4
controls replay byte for byte to their stored answers with no key. Across every
stored run, 86 of 98 replay; the 12 that don't are the same pre-artifact runs
as before (challenger ×2, run1 ×10). The scorer is run 6's, plus a count of
distinct readable hosts and a check that each fill note adds up.

| prediction | result |
|---|---|
| 1. ≥2 distinct readable web hosts in ≥8 of 10 | ✓ **10 of 10** (run 6: 5). 7 questions held 3 hosts, 3 held 2 (q04, q06, q09). Of the 90 links named: 27 readable pages kept; 32 fetched without text (15 HTTP 404, 14 HTTP 403, 1 HTTP 202, 1 unknown host, 1 page with no visible text); 3 skipped on a host already held; 28 not fetched. |
| 2. the fill note adds up | ✓ **10 of 10**: readable + failures + same-host skips + not fetched = 9 named, in every question. |
| 3. restated quote arguments ≤10% | ✓ **0 of 62.** |
| 4. quote answers ≥5 of 10 | ✓ **7 of 10.** q05 is an inference; q01 and q09 abstained. |
| 5. `established` 2–5 of 10 | ✗ **1 of 10** (q02). Prediction 1 was met, so this is read pair by pair, below. It is not the fetch. |
| 6. every `established` answer read by hand | ✓ q02, below. No copies found. |
| 7. the reason check, listed | ✓ wired. q02's quote passes the link check and gets `gives_reason`. q04 and q08 do too and are bound elsewhere. q07's quote states no causal link and is capped at `hypothesis`, naming why. q01 abstained before the check. |
| 8. controls | ✓ all 4 PASS, the same lines as run 6. Nothing was searched. |
| 9. every artifact replays | ✓ 10 of 10, plus 4 of 4 controls. |

**Kill criteria:** none triggered. The one `established` answer is true on
reading, and each covering sentence states it.

- **q02**, "Earth's tilted axis causes the seasons." (spaceplace.nasa.gov), as
  in run 6. Covered, `covers` in both orders, by weather.gov's "The earth's
  spin axis is tilted with respect to its orbital plane. This is what causes
  the seasons." and by three Wikipedia sentences. Copies: the longest run of
  text any web page shares with another page is 41 characters ("tilted with
  respect to its orbital plane"), a stock phrase.

**Why only one.** Each of the other nine, read:
- **q01 (Challenger) abstained: the support check refused a finding.** It
  judged 6 quotes `does_not_support`, and each is a sentence that reports a
  finding: "The Rogers Commission concluded that…", "The commission found
  that…", "The investigation determined that…". In each the model's claim
  dropped the attribution. The support prompt counts a source that "only
  reports that someone else holds the view" as not supporting, which was
  written for "critics say"; here it caught the official investigation. Both
  inference answers rested in part on those quotes and fell with them,
  although the 9 quotes that were kept state the same cause. In run 6 the
  model kept "The Rogers Commission concluded that" in its claim, and the
  same sentence passed.
- **q09 (Rosetta Stone) abstained: the claims were fragments.** The model
  wrote "the Egyptian scripts." and "hieroglyphic writing" as its
  conclusions. A fragment asserts nothing, and the support check, which is
  not shown the question, refused all 7. This is right as the check is
  written; the answers were unusable.
- **q08 (blue sky): the covers judge held them apart.** 8 pairs, 16 replies,
  one `covers`. "Since blue light wavelengths scatter more, the diffuse sky
  seen in daytime is blue" against "…because molecules in the air scatter
  blue light from the Sun more than they scatter red light" got `does_not`
  both ways. The answer names molecules and red light, which the source does
  not; a reader could go either way. One order split, and asking both kept
  it out.
- **Held back correctly:** q03 and q06, where the answer carries a number the
  web pages lack ("6 January 1912", "6 km"), so every pair was vetoed. q04,
  whose web pages say "high winds", not flutter. q07, whose quote states no
  causal link. q10, whose answer makes two claims where the sources state
  one. q05 is an inference.

So the fill rule did what it was built for, and what stopped more answers
was the support check's attribution rule (q01), the model's fragment
answers (q09) and a strict judge (q08). None vouched wrongly.

**The 30 cover pairs.** 7 were vetoed before any call (q03 ×3 and q06 ×4, on
numbers). 23 were judged, 46 replies, every one readable. 5 covered, all in
q02. Order mattered once in 23 (q08).

**Status spread:** 7 `hypothesis`, 1 `established` and 2 abstained, out of
10. The calibration gate would not be met.

**Spend:** read from kie.ai's balance. **129.35 credits** for the measure
command (9494.33 before, 9364.98 after) and **1.10** for the controls (to
9363.88). The measure calls report 107.5, of which the 10 searches are 3.94.
In run 6 the two agreed to within the controls. The 21.85 gap is not
explained: failed calls, which are retried and never recorded, may be billed,
or another user of the key spent in the window. The balance figure is the one
to quote.

## Amendment 9 — 2026-10-06: run 8, argue prompt 4 (#219, #218)

Added before any live call under the change. Nothing above is changed.

**Why a run.** Run 7 had readable pages on 2 or more hosts for all 10
questions but established 1. Read pair by pair, two of the losses were the
claims the model wrote, not the fetch or the checks:
- q09 abstained because its claims were fragments ("the Egyptian
  scripts."), which assert nothing (#219).
- q01 abstained because its claims cut "The Rogers Commission concluded
  that" off a reported finding, and the support check refuses a view the
  source only reports (#218).

**Instrument change** (#221, merged as c77f8f3, `argue_prompt 4`,
occam/argue.py). The instruction now says:
- a quote's conclusion reads as a sentence on its own, with its own subject
  and verb, to someone who has not seen the question; if no shorter part of
  the quote does that, the conclusion is the whole quote;
- when a passage reports what a person, body or study found, the
  conclusion keeps who found it, copied from the start of that wording.

The support check is unchanged; the user chose this over counting official
findings as the source's own claim. Replay never re-prompts, so every stored
run replays as before (86 of 98, the same 12 pre-artifact runs failing).

**Observed live**, one question each, so no rate is measured:
- q09 (`traces/occam/probe-219/`, 11.27 credits, before the attribution
  sentence): 0 fragments, 5 of 5 quotes supported, answer `hypothesis` —
  but every sample answered with an inference, not a quote.
- q01 (`traces/occam/probe-218/`, 12.73 credits): 5 of 5 attributed quotes
  supported, the answer a quote — but `hypothesis`, "rests on a single
  source": an answer that names the commission was not covered by another
  host's differently attributed sentence.

Everything else as in run 7: `kie/gemini-3.1-pro`, k = 3, temperatures 0.7 /
0.2, judge on, `veto_words 2`, `why_check 3`, `covers_check 2`, `web_fill 2`,
3 Wikipedia pages and `--web 3`.

**Run 8** = `python -m occam measure --model kie/gemini-3.1-pro --out
traces/occam/run8` and `python -m occam controls --model kie/gemini-3.1-pro
--out traces/occam/run8-controls`.

**Baselines**, from the stored artifacts of runs 6 and 7 (measured
2026-10-06). A fragment is a quote conclusion of 4 words or fewer. An
attribution cut is a quote containing "<verb> that" for concluded, found,
determined, reported, said, stated, showed, argued, believed or suggested,
whose conclusion contains none.

| | run 6 | run 7 |
|---|---|---|
| quote arguments | 55 | 78 |
| fragments | 4 | 6 |
| attribution cuts (refused) | 2 (2) | 6 (6) |
| refused by the support check | 8 | 16 |
| arguments lost to a refused premise | 1 | 5 |
| answers: quote / inference / abstained | 7 / 3 / 0 | 7 / 1 / 2 |
| `established` | 2 | 1 |

**Predictions:**
1. Fragments: **at most 1** in the whole run.
2. Attribution cuts: **at most 2**, and no attributed quote that keeps its
   attribution is refused for being a reported view (each refusal of a quote
   with "<verb> that" is read).
3. Refused by the support check: **at most 10%** of quote arguments.
4. Abstentions: **at most 1 of 10.**
5. Answers that are inferences: **at most 3 of 10.** More would mean the
   whole-quote rule pushes the model to compose answers, which caps them at
   `hypothesis`.
6. Quote answers: **at least 5 of 10.**
7. `established`: **1 to 4 of 10.** Attributed answers may find no covering
   sentence on another host (q01's probe); every answer whose conclusion
   carries an attribution is listed with what bound it.
8. Arguments lost to a refused premise: reported, with no prediction; it
   decides whether #218's second question needs building.
9. Sources and checks as in run 7: ≥2 distinct readable web hosts in ≥8 of
   10, every fill note adds up, restated quotes ≤10%, the reason check
   listed live.
10. Every `established` answer read by hand: the covering sentence, its host
    and page, and whether the two pages copy each other.
11. Controls as in Amendment 8, and every artifact replays with no key.

**Kill criteria:** those of Amendment 7. An `established` answer that is
false on reading, or whose covering sentence does not state it, means
**STOP**, reported before anything else. Spend is read from kie.ai's balance
before, between and after the two commands.

**Status spread.** As in Amendment 6.

### Results — 2026-10-06, read against the predictions above

Run 8 is `traces/occam/run8/` and `traces/occam/run8-controls/`, from commit
3811cd1 on `kie/gemini-3.1-pro`, in one pass each. All 10 artifacts and all 4
controls replay byte for byte to their stored answers with no key. Across every
stored run, 102 of 114 replay; the 12 that don't are the same pre-artifact runs
as before (challenger ×2, run1 ×10). Counts use the predicates stated in the
baselines.

| prediction | result |
|---|---|
| 1. fragments ≤1 | ✓ **0 of 49** quote arguments (run 7: 6 of 78). |
| 2. attribution cuts ≤2; no kept attribution refused | ✓ **0** cuts. 2 quotes kept their attribution, and neither was refused. |
| 3. refused by the support check ≤10% | ✓ **0 of 49** (run 7: 16 of 78). |
| 4. abstentions ≤1 of 10 | ✓ **0** (run 7: 2). |
| 5. inference answers ≤3 of 10 | ✓ **2** (q05, q09). |
| 6. quote answers ≥5 of 10 | ✓ **8 of 10.** |
| 7. `established` 1–4 of 10 | ✓ **3 of 10**: q02, q04, q10. One answer carries an attribution: q01, "The Rogers Commission concluded that…", bound by "rests on a single source (en.wikipedia.org)". It had no cover pair at all: all 3 of its quotes are from Wikipedia, so the covers check had nothing to read. |
| 8. arguments lost to a refused premise | reported: **0** (run 7: 5). |
| 9. sources and checks | ✓ ≥2 distinct readable hosts in **10 of 10**; every fill note adds up, 10 of 10; restated quotes **0 of 49**. The reason check is wired: q02 and q04, the established cause questions, pass the link check and get `gives_reason`; q07's quote states no causal link and is capped, naming why. |
| 10. every `established` answer read by hand | ✓ all 3, below. No stop. One is borderline and its second source partly draws on Wikipedia. |
| 11. controls and replay | ✓ all 4 PASS with the same verdicts. Under prompt 4 the positive and adversarial answers are now whole sentences ("…ratified in 1987 by fourteen member states.", "…at sea level under standard atmospheric pressure."), still `hypothesis`. Replay as above. |

**Kill criteria:** none triggered. Each `established` answer is true on
reading, and each covering sentence states it, in two cases in substance
rather than word for word.

- **q02**, "Earth's tilted axis causes the seasons." (spaceplace.nasa.gov),
  as in runs 6 and 7. Covered both ways by weather.gov ("the seasons are
  caused by the Earth being tilted on its axis by an average of 23.5
  degrees"), science.nasa.gov and two Wikipedia sentences. Longest shared
  run between any two pages: 35 characters, a stock phrase.
- **q04**, "The Tacoma Narrows Bridge collapsed primarily due to the
  aeroelastic flutter." (simscale.com), as in run 6. Covered by Wikipedia's
  "The original Tacoma Narrows Bridge was destroyed as a result of
  aeroelastic flutter." Destroyed, not collapsed: as in run 6, read as
  stating it in substance. Longest shared run: 33 characters, the bridge's
  name.
- **q10**, "The primary function of mitochondria in a cell is to produce ATP,
  the main energy currency of the cell." (studymind.co.uk). Covered both
  ways by Wikipedia's "The most prominent roles of mitochondria are to
  produce the energy currency of the cell, ATP (i.e., phosphorylation of
  ADP), through respiration and to regulate cellular metabolism." True on
  reading. Two cautions:
  - **"Primary function" against "most prominent roles".** The source names
    two roles, and the answer ranks one first. Read as stated in substance;
    a stricter reader could refuse it, as with q04's "destroyed".
  - **The second source partly draws on the first.** studymind's next
    sentence, "In addition to energy production, mitochondria also play a
    role in other cellular processes, such as cell signaling, cellular
    differentiation, and cell death", follows Wikipedia's "In addition to
    supplying cellular energy, mitochondria are involved in other tasks,
    such as signaling, cellular differentiation, and cell death" (52
    characters shared). The answer sentence itself is not copied. But the
    two hosts are less independent than two hosts are taken to be, and
    nothing in the mechanism sees a paraphrase. It was found here only by
    reading.

**The 25 cover pairs.** 7 were vetoed before any call. 18 were judged, 36
replies, every one readable. 6 covered, in q02, q04 and q10. Order mattered
once (q05, an inference answer).

**What moved.** Against run 7, the support check refused nothing (16 before),
and no question abstained. The losses run 7 traced to the model's claims are
gone. The answers still held back are bound by a single source (q01, q03,
q06, q08), an inference (q05, q09) or the reason check (q07). #218's second
question, whether one refused premise should sink an inference, cost nothing
here (0 lost) and does not need building on this evidence.

**Status spread:** 7 `hypothesis` and 3 `established` out of 10. The
calibration gate would not be met.

**Spend:** read from kie.ai's balance. **93.99 credits** for the measure
command (9339.88 before, 9245.89 between) and **1.55** for the controls (to
9244.34). The measure calls report 93.99, exactly the balance. Run 7's
21.85-credit gap did not recur, and stays unexplained.

## Amendment 10 — 2026-10-06: run 9, ten held-out questions (#226)

Added before any live call on these questions. Nothing above is changed.

**Why a run.** Runs 5 to 8 all used the same ten questions
(`controls.FACTUAL_QUESTIONS`), and every recent fix (#212, #216, #218, #219)
came from reading their failures. Run 8's 3 of 10 `established` cannot be
told apart from fitting to those ten. This run asks whether the pipeline as
it stands does as well on questions it has never seen.

**The held-out set** is `occam/questions/held-out-1.txt`, committed with this
amendment. I drafted it and the user approved it before any call. It
mirrors the built-in set's shape: six cause questions (Titanic, ocean tides,
Hindenburg, rainbows, autumn leaves, the 1918 pandemic) and four fact
questions (penicillin, the first modern Olympics, red blood cells, the Great
Wall). No rule has been written or tuned on it. Its answers are not labelled,
so it is not a calibration set.

**Instrument:** unchanged from run 8 apart from the question list: `rules 4`,
argue prompt 4, `web_fill 2`, `kie/gemini-3.1-pro`, k = 3, temperatures 0.7 /
0.2, judge on, 3 Wikipedia pages and `--web 3`. `measure --questions` is the
only code change (#226, commit dc845e8), and it touches nothing a question
passes through.

**Run 9** = `python -m occam measure --model kie/gemini-3.1-pro --questions
occam/questions/held-out-1.txt --out traces/occam/run9` and `python -m occam
controls --model kie/gemini-3.1-pro --out traces/occam/run9-controls`.

**Baseline:** run 8 on the built-in ten (Amendment 9's results). Ten
questions are few: one question is 10 points. So each prediction states a
band, not a point, and a miss by one question is reported as such.

**Predictions:**
1. Fragments (quote conclusions of 4 words or fewer): **at most 2** in the
   run (run 8: 0).
2. Attribution cuts: **at most 2** (run 8: 0).
3. Refused by the support check: **at most 15%** of quote arguments (run 8:
   0%).
4. Abstentions: **at most 2 of 10** (run 8: 0).
5. ≥2 distinct readable web hosts in **at least 8 of 10**; every fill note
   adds up.
6. Quote answers: **at least 5 of 10** (run 8: 8).
7. `established`: **1 to 5 of 10** (run 8: 3). **0** would say run 8's
   result was fitted to its ten questions, and is reported as the finding.
8. Every `established` answer is read by hand: the covering sentence, its
   host and page, and whether the pages copy or paraphrase each other (#225).
9. The reason check is listed for the six cause questions.
10. Controls as in Amendment 9, and every artifact replays with no key.

**Kill criteria:** those of Amendment 7. An `established` answer that is
false on reading, or whose covering sentence does not state it, means
**STOP**, reported before anything else. Spend is read from kie.ai's balance
before, between and after the two commands.
