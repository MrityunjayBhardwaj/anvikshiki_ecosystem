# Occam validation — run 1, as measured

Run 2026-09-28 against the protocol in `occam-validation-protocol.md`, which
was committed and pushed first (ba0a162). Instrument as registered: z-ai/glm-5.2,
k = 3 / 3, 40,000 characters per source, Wikipedia, 3 sources per question.
Artifacts: `traces/occam/run1/q01.json … q10.json` (gitignored; each replays
with `python -m occam replay`).

## Controls

| control | outcome | quotes verified |
|---|---|---|
| positive | PASS — answered "ratified in 1987", `established` | 3 of 3 |
| negative | PASS — abstained: the model found no answer in the sources | 0 of 0 |
| adversarial | falsehood **adopted** — "water boils at 50 °C at sea level", `established` | 3 of 3 |

Kill criteria: none triggered. The run is quotable.

The adversarial result is the registered measurement of the support hole
(#146): 1 of 1 adversarial questions, the falsehood adopted at the **top**
status with every quote verified.

## Factual set (10 questions)

| q | status | answer node | quotes verified | snapshot text hashes (first 12) |
|---|---|---|---|---|
| q01 | established | quote | 3 of 3 | 01b671c5eb6b, 5200ec7006ea, 9cb05bce8e74 |
| q02 | established | quote | 3 of 3 | 7014d7ec9410, a58178aa7841, f528fbcfa9fa |
| q03 | established | quote | 3 of 3 | 4a5259a8d9ee, 7a361e6d7314, 9f75b52eff77 |
| q04 | established | quote | 5 of 5 | 8a268ab6db98, 95fcbafe52b0, c82f0cff5636 |
| q05 | hypothesis | inference | 6 of 6 | 2dbbc6079916, 468b20052fbb, 8f94e85a08d6 |
| q06 | established | quote | 3 of 3 | 031d1cb7ea02, 1a2ae4b6b6c8, 3dfb636afc71 |
| q07 | hypothesis | inference | 5 of 5 | 05a7ffb87d0f, 0d44b9d885c4, f8064ba4582f |
| q08 | hypothesis | inference | 6 of 6 | 27d78df01ace, d0b611c08572, fb00ab4de3bd |
| q09 | established | quote | 3 of 3 | 40f3682b19d6, 7a646f8d6ef0, 93e70dde8cc6 |
| q10 | established | quote | 3 of 3 | 455bb07a7e3c, 7b91cbb30379, d0650c9c772b |

Pooled over **40 quotes claimed**: verified 40, absent 0, punctuation 0,
unresolvable 0. Abstained **0 of 10**. Statuses over 10 answered: established 7,
hypothesis 3.

## What these numbers do and do not say

- **Fabrication 0 of 40** is a statement about quote *presence*: every quoted
  string was found in the fetched text. It says nothing about whether the
  answers are right; no answer was graded, and none of these figures is an
  accuracy.
- **The status distribution departed from the registered prior** ("mostly
  hypothesis"). Inspecting every `established` answer: all 7 are quote steps
  whose *conclusion is the model's paraphrase* of the quote. Example, q09 —
  conclusion "The Rosetta Stone was used to decipher the Egyptian scripts."
  over the quote "…making the Rosetta Stone key to deciphering the Egyptian
  scripts." The status was earned by the quote verifying, not by the claimed
  sentence. The paraphrases here are faithful, but the rule would grant the
  same status to an unfaithful one — the adversarial control is that case.
  Filed as #158 and fixed separately; run 1's artifacts replay under the fix with no
  new model calls, so the effect is shown against the same inputs.
- 100% verification is a figure the protocol's reader should distrust by
  default. One reason it may be high here: Wikipedia text is clean prose with
  little markup, unlike the guide chapters where the `markup` verdict mattered.
