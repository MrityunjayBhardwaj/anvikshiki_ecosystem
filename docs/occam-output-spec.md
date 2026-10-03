# Occam output spec — what an answer shows its reader

These ten rules were first written on 2026-10-02 for the Answer Lab, a showcase that put
real Occam runs beside a hand-built "ideal" card for each. They are the target for stage 3
(#201). Each rule below says where it is met today, and where it isn't yet.

"Shown" means `python -m occam ask` and `python -m occam replay FILE`; both print through
`_show` in `occam/__main__.py`. Everything listed is computed from the stored run when it
is shown, so no stored answer changes and every artifact replays as it did — except where
a rule needed the answer itself to change, which is gated by a field of `Params`.

## The rules

1. **Every sentence traces to a node; anything untraced is labelled.**
   Met: the answer's conclusion is its derivation's root, and every line beneath it is a
   node. Occam writes no summary sentence of its own.

2. **Every chain ends at bytes (quote, character range, revision, hash), or says why it can't.**
   Met: the derivation prints each quote with its URL, character range, full text hash,
   snapshot id and revision (or "not recorded").

3. **Details the question supplied are suppositions, never observations.**
   Met for whole numbers: a `question detail` line says, for each number in the question,
   whether the answer carries it and whether a quote beneath the answer states it. It
   uses the premise counters' own predicate (#181). Words and names aren't read, and the
   line says when the question has no number to check.

4. **Every link shows its own check: verbatim, judged, attack outcome, or not checked.**
   Met: each quote shows its verbatim verdict and its support verdict (read from the
   stored run; "not judged" when the judge was never asked, and "not shown" when no
   stored run was given). Each node lists every attack on it and whether it succeeded,
   and says "none" when there were none.

5. **Status comes with a plain-words reason, and incoherence is named.**
   Met: a `meaning` line says what the status claims, keyed on the status itself; `bound
   by` names every limit holding it there, ties included (#202). Quotes beneath the answer
   that another argument defeated are named (#193), and the derivation shows which links
   stand unattacked and which are in dispute.

6. **What would change it is computed by replay, never written by hand.**
   Partly met: `bound by` names what holds the status down. Editing one stored reply and
   replaying is item 4 of #201.

7. **Uncertainty is a calibrated set plus measured drivers.**
   Waiting on M7 (#144). Until there are labels the answer says "the coverage guarantee is
   unavailable" and shows no set. The drivers will be the counters M7's classifier uses.

8. **Abstentions say which kind: false premise, silent sources, or defeated.**
   Met as far as the evidence goes: each abstain reason names the stage that failed, and
   "the model returned no answer" says it can't tell silent sources from a false premise
   (#188).

9. **Every count has its denominator; gaps are printed, never silent.**
   Met: every counter prints "n of N" with its population, and every check above prints
   its zero or its "could not look".

10. **Everything replays from the stored artifact with no model.**
    Met: `replay` needs only the file, and everything above is computed from it.

## The labeller's view

`python -m occam replay FILE --blind` prints the question, the answer and its chain down
to the quoted bytes, with nothing the pipeline decided about it: no status, bounds, meaning,
attacks, judge verdicts, positions or counters. M7's labels must come from reading the
answer and its quotes, not from seeing the status they are meant to check.

The verbatim verdict stays, because it is a string comparison and not a judgement. The
shown answer is itself the pipeline's choice; that can't be hidden from someone asked to
label it.
