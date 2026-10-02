"""Stage 5a — which conclusions say the same thing, and for what purpose? (#172)

Positions and corroboration used to group conclusions by exact wording, so
three samples giving one explanation in three phrasings counted as three
positions (run 2: agreement 1 of 3 in 10 of 10 questions). Merging them needs
a notion of "the same", and sameness is never absolute: it is sameness *for a
purpose*. So every pair is judged under a lens.

    question   the two give consistent answers to THIS question. Details the
               question does not ask about do not count: run 2's q01 asks
               "Why did Challenger break apart in 1986?", so an answer that
               repeats "in 1986" agrees with one that does not. One answer
               may also be less precise or less complete than the other —
               "1912" agrees with "6 January 1912" for q03's "…and when?" —
               as long as nothing conflicts; someone who needs the exact date
               can ask for it (decided on #172). "1912" vs "1913" conflicts.
    claim      the two state the entire sentence. Used for corroboration,
               because `established` vouches for every word shown, and a lie
               can hide in a detail a question-lens judge would wave through.

Who decides
───────────
The mechanism picks the pairs, vetoes before any model sees them, groups, and
counts. The model answers one narrow question per pair — same, different or
cannot tell — in a fresh call that sees that pair and nothing else (#174),
asked in both orders. It never sets a status.

    veto          a negation word on one side only; or numbers that differ
                  (claim lens) or conflict — neither side's numbers contained
                  in the other's (question lens, where numbers the question
                  itself contains are context, not answer). Opposites without a
                  number or a "not" ("rose"/"fell") get past the veto; the
                  judge must catch those, and the probe must contain them.
    both orders   a pair merges only if the judge says `same` with the
                  statements in each order: that cancels a bias toward
                  whichever comes first.
    no chaining   a group merges only if every pair inside it is `same`.
                  A~B and B~C with A≁C merges nothing.

Anything short of that — a veto, `different`, `cannot_tell`, a malformed or
missing reply — keeps the pair apart. Doubt never merges.

Replay
──────
The replies are stored in the artifact, as every other model reply is, and
replay parses them without a model. Candidate pairs are recomputed from the
arguments by the same function on both paths, so the stored replies are read
against exactly the pairs they were asked about.
"""

from __future__ import annotations

import itertools
import re
from typing import Literal, Optional, Sequence

from pydantic import BaseModel, ConfigDict

from .argue import ArgueResult, norm_conclusion
from .model import Model, extract_json
from .spans import states

__all__ = ["Lens", "EQUIV_VERDICTS", "Pair", "Verdict", "EquivResult", "veto",
           "candidate_pairs", "equiv_prompt", "judge_same", "equiv_from_replies"]

Lens = Literal["question", "claim"]
EQUIV_VERDICTS = ("same", "different", "cannot_tell")

# Words that negate the whole statement. Set 1 also held "without", which
# negates a noun phrase, not the statement: "grew without bound" says it grew,
# and set 1 vetoed it exactly as it vetoed "did not grow" (#192). Which set a
# run used is `Params.veto_words`: the stored judge replies are read in order
# over the pairs no veto ruled out, so a run must replay under its own set.
NEGATIONS_BY_SET = {
    1: frozenset({"not", "no", "never", "none", "neither", "nor", "without", "cannot"}),
    2: frozenset({"not", "no", "never", "none", "neither", "nor", "cannot"}),
}
NEGATIONS = NEGATIONS_BY_SET[2]
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
_WORD = re.compile(r"[a-z]+(?:['’][a-z]+)?")


def _numbers(s: str) -> set[str]:
    return {n.replace(",", "") for n in _NUMBER.findall(s)}


def _negations(s: str, words: frozenset[str]) -> set[str]:
    out = set()
    for w in _WORD.findall(s.casefold()):
        if w in words:
            out.add(w)
        elif w.endswith(("n't", "n’t")):
            out.add("n't")
    return out


def veto(a: str, b: str, lens: Lens, question: str,
         negations: frozenset[str] = NEGATIONS) -> str:
    """Why the pair cannot be the same, decided without a model; "" if nothing
    rules it out."""
    na, nb = _numbers(a), _numbers(b)
    if lens == "question":
        asked = _numbers(question)
        na, nb = na - asked, nb - asked
        if not (na <= nb or nb <= na):         # less precise is fine; conflicting is not
            return f"numbers conflict: {', '.join(sorted(na ^ nb))}"
    elif na != nb:
        return f"numbers differ: {', '.join(sorted(na ^ nb))}"
    ga, gb = _negations(a, negations), _negations(b, negations)
    if ga != gb:
        return f"negation differs: {', '.join(sorted(ga ^ gb))}"
    return ""


class Pair(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    lens: Lens
    a: str                 # normalised conclusion — the key positions and hosts use
    b: str
    text_a: str            # a wording the model actually wrote, shown to the judge
    text_b: str
    veto: str = ""


def candidate_pairs(argued: ArgueResult, question: str, *,
                    veto_words: int = 2) -> tuple[Pair, ...]:
    """Every pair that could merge, in a fixed order. Deterministic: live and
    replay compute the same tuple from the same arguments.

    Question lens: distinct surviving answer conclusions. Claim lens: distinct
    conclusions of quotes that state them word for word — the only arguments
    that can reach an established ceiling, and so the only ones corroboration
    reads. `veto_words` names the negation set (see NEGATIONS_BY_SET)."""
    by = argued.by_id()
    wording: dict[str, str] = {}
    for a in sorted(argued.arguments, key=lambda x: x.id):
        wording.setdefault(norm_conclusion(a.conclusion), a.conclusion)
    answers = sorted({norm_conclusion(by[x].conclusion) for x in argued.answers if x})
    verbatim = sorted({norm_conclusion(a.conclusion) for a in argued.arguments
                       if a.kind == "quote" and states(a.span.quote, a.conclusion)})
    pairs: list[Pair] = []
    for lens, keys in (("question", answers), ("claim", verbatim)):
        for x, y in itertools.combinations(keys, 2):
            pairs.append(Pair(id=f"P{len(pairs):04d}", lens=lens, a=x, b=y,
                              text_a=wording[x], text_b=wording[y],
                              veto=veto(wording[x], wording[y], lens, question,
                                        NEGATIONS_BY_SET[veto_words])))
    return tuple(pairs)


_LENS_RULE = {
    "question": (
        "LENS question — do the two give consistent answers to the QUESTION?\n"
        "- same: they answer the question the same way. One may be less precise or "
        "leave part of the answer out, as long as nothing in either contradicts the "
        "other. Details the question does not ask about do not matter.\n"
        "- different: they conflict on something the question asks about — a "
        "different number, date, name, cause, direction, or a negation.\n"
        "- cannot_tell: you cannot decide."),
    "claim": (
        "LENS claim — does each statement say everything the other says?\n"
        "- same: each says everything the other says, no more and no less, only in "
        "different words.\n"
        "- different: one says something the other does not, or they conflict — "
        "including a different number, date, direction or a negation, and including "
        "one being more specific than the other.\n"
        "- cannot_tell: you cannot decide."),
}


def equiv_prompt(question: str, pair: Pair, *, flip: bool = False) -> str:
    """One pair, nothing else: each comparison is made fresh (#174), so no
    judgement is made in the light of another."""
    x, y = (pair.text_b, pair.text_a) if flip else (pair.text_a, pair.text_b)
    return "\n".join([
        "Compare statement X with statement Y under the LENS given below.\n"
        "Judge only what the statements say, not whether they are true.\n"
        'Return JSON only: {"verdict": "same", '
        '"differs_on": "<the detail that differs, or empty>", '
        '"asked_by_question": false}\n',
        f"QUESTION: {question}\n",
        _LENS_RULE[pair.lens],
        f"X: {x}",
        f"Y: {y}\n",
    ])


def judge_same(model: Model, question: str, pairs: Sequence[Pair], *,
               temperature: float = 0.0) -> list[str]:
    """Two fresh calls per pair no veto ruled out — X/Y, then Y/X — in pair
    order. No call at all when there is nothing to judge."""
    replies: list[str] = []
    for p in pairs:
        if not p.veto:
            for flip in (False, True):
                replies.append(model.complete(equiv_prompt(question, p, flip=flip),
                                              temperature=temperature))
    return replies


class Verdict(BaseModel):
    model_config = ConfigDict(frozen=True)

    pair: Pair
    forward: Optional[str]            # None: not returned
    backward: Optional[str]
    differs_on: str = ""
    asked_by_question: Optional[bool] = None

    @property
    def same(self) -> bool:
        return not self.pair.veto and self.forward == "same" and self.backward == "same"

    @property
    def why_apart(self) -> str:
        if self.pair.veto:
            return self.pair.veto
        if self.forward is None or self.backward is None:
            return "not judged in both orders"
        if self.forward != self.backward:
            return f"the two orders disagreed ({self.forward} / {self.backward})"
        return self.differs_on or self.forward


class EquivResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    verdicts: tuple[Verdict, ...]
    malformed: tuple[tuple[int, str], ...]

    def groups(self, lens: Lens, keys: Sequence[str]) -> dict[str, str]:
        """Each key's group representative. A key joins the first group, in
        sorted order, with every member of which it was judged `same`;
        otherwise it starts its own. No chaining."""
        same = {frozenset((v.pair.a, v.pair.b)) for v in self.verdicts
                if v.pair.lens == lens and v.same}
        reps: dict[str, list[str]] = {}
        out: dict[str, str] = {}
        for k in sorted(set(keys)):
            for rep, members in reps.items():
                if all(frozenset((k, m)) in same for m in members):
                    members.append(k)
                    out[k] = rep
                    break
            else:
                reps[k] = [k]
                out[k] = k
        return out


def _read(reply: str) -> Optional[dict]:
    obj = extract_json(reply)
    if isinstance(obj, dict) and obj.get("verdict") in EQUIV_VERDICTS:
        return obj
    return None


def equiv_from_replies(replies: Sequence[str], pairs: Sequence[Pair]) -> EquivResult:
    """Deterministic. Replies are in pair order over the pairs no veto ruled
    out, each pair's X/Y reply then its Y/X reply."""
    malformed: list[tuple[int, str]] = []
    verdicts = []
    i = 0
    for p in pairs:
        f = b = None
        if not p.veto:
            got = []
            for j in (i, i + 1):
                r = _read(replies[j]) if j < len(replies) else None
                if r is None and j < len(replies):
                    malformed.append((j, f"reply for {p.id} is not a JSON object with a verdict"))
                got.append(r)
            f, b = got
            i += 2
        asked = f.get("asked_by_question") if f else None
        verdicts.append(Verdict(
            pair=p, forward=f["verdict"] if f else None, backward=b["verdict"] if b else None,
            differs_on=str((f or {}).get("differs_on") or (b or {}).get("differs_on") or ""),
            asked_by_question=asked if isinstance(asked, bool) else None))
    return EquivResult(verdicts=tuple(verdicts), malformed=tuple(malformed))
