# Labelling Occam's answers — a guide for the labeller

Written 2026-11-04 for the pilot (#266, Amendment 14). **Draft: the user approves it
before the first label.** If it changes after labelling starts, every label made under
the old text is redone, because a calibration describes one way of labelling as well as
one pipeline.

## What you are asked

For each item on the sheet, read the question, the answer and every quote under it.
Then record three things:

1. **`label`**: the status the answer *deserves*, one of the five below.
2. **`wrong`**: `true` if you know or can see that the answer is false, otherwise `false`.
3. **`minutes`**: roughly how long the item took you, as a whole number.

Add a **`note`** whenever you used something not on the sheet: your own knowledge, a page
you looked up, or a dispute the sheet doesn't show. Say what it was.

You are judging the answer, not the pipeline. The pipeline's own status is hidden from
you. Don't open the full replay, the strata file or the run's counters until every
label is in. The calibration measures how often the pipeline's status matches yours,
so a label that echoes its status measures nothing.

## The sheet

    python -m occam replay traces/occam/pilot1 --blind --template traces/occam/pilot1-labels.jsonl \
        > traces/occam/pilot1-sheet.txt

The sheet lists the items in a shuffled order. Each item shows:

- the question and the answer;
- the answer's chain, down to the quoted words;
- **every other quote the model drew from the sources**, grouped by page.

The other quotes are the rest of the evidence. They're where a second source, a
rival view or a correction shows up. Every quote on the sheet was found on its page:
`verbatim: ok`, or `verbatim: markup` when it differs only by formatting such as bold or
italics. A quote the model claimed but the page doesn't contain is removed before the
sheet is made, so it never reaches you. Nothing else about the quotes was decided for you.

Fill in `traces/occam/pilot1-labels.jsonl`, one row per item, in the same order as the
sheet. `calibrate` refuses the file until every `label` is one of the five words below,
spelt exactly.

## The five statuses

Work down the list and stop at the first that fits.

| label | when |
|---|---|
| `contested` | Credible sources, on the sheet or ones you know, take **opposite positions** on what the answer says, and neither clearly wins. This includes an answer that picks one side of a live dispute as if it were settled. |
| `open` | **Nobody knows.** The question is unsettled and no position is well supported. Or the answer asserts something the evidence on the sheet cannot decide either way. |
| `provisional` | The answer may be right, but its support is **thin**: early or limited evidence, a quote too short or vague to carry it, a source whose standing you doubt, or an answer that claims more than its quotes show. |
| `hypothesis` | The answer is **probably right, but the sheet does not settle it**. Either only one independent page says it, or it is the model's own wording or reasoning beyond what any quote states, and you accept the step but no quote makes it. |
| `established` | The answer is right, and **at least two independent pages on the sheet state it in their own words**. Nothing on the sheet, or that you know of, credibly disputes it. |

**Independent** means one page is not reprinting another. A fact-check that quotes the
FDA sentence word for word is the FDA again, not a second source. When you can't tell,
treat the pages as one and say so in the note.

**Stated in their own words** means a quote says what the answer says. It is not enough
that it says something from which the answer follows. If the answer only follows, the
best it can be is `hypothesis`.

## Hard cases

- **A wrong answer.** Set `wrong: true`, then label how it is carried. A wrong answer
  with credible sources behind it is `contested`; one with none is `open`. Never label
  a wrong answer `established` or `hypothesis`. The `wrong` field is what the pilot's
  kill criterion reads.
- **An abstention** (`ABSTAINED — the pipeline gave no answer`). Label the status that a
  good answer to the question would deserve *from the quotes on the sheet*. If the quotes
  settle it from two independent pages, that's `established`, even though no answer was
  given. Leave `wrong` as `false`.
- **An answer that is partly right.** Label the part the question asks about. Note the rest.
- **A right answer from weak pages.** If the answer is true but the quotes are poor, label
  the quotes: `provisional` or `hypothesis`. The label says how well the sheet carries the
  answer. Your knowledge is there to catch errors and disputes, not to fill gaps in the
  evidence.

## The re-label

At least seven days after the last label, make a second sheet in a new order:

    python -m occam replay traces/occam/pilot1 --blind --seed 1 \
        --template traces/occam/pilot1-relabels.jsonl > traces/occam/pilot1-resheet.txt

Label **only its first 10 items**, without looking at your first labels. How often the two
agree is the pilot's measure of whether a label can be repeated.
