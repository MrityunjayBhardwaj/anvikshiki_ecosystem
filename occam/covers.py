"""Stage 5b — does a second source state everything the answer states? (#212)

Corroboration lifts an answer to `established` only when the same claim
stands on two hosts. Before this, "the same claim" meant the claim-lens judge
called two sentences *the same*: each says everything the other says, no
more and no less. Run 5 showed what that costs. Different sites word a claim
with different detail, so every pair across two hosts was kept apart for one
reason: one sentence says more. weather.gov's "The earth's spin axis is tilted
with respect to its orbital plane. This is what causes the seasons." was kept
apart from the answer "Earth's tilted axis causes the seasons." because it
names the spin axis.

But `established` vouches for every word of the *answer*, and nothing more.
So what corroboration needs is one-way: does the source sentence state every
claim the answer states? A source that says more still covers an answer that
says less. Sameness is the stricter relation, and for vouching it is the
wrong one.

Who decides
───────────
The mechanism picks the pairs, vetoes before any model sees them, and counts.
The model answers one narrow question per pair — covers, does_not or
cannot_tell — in a fresh call that sees the two statements and nothing else,
asked with the two shown in each order. The roles stay fixed by label: the
order only cancels a bias toward whichever comes first.

    pairs     (answer, source): the answer is the conclusion of a quote some
              sample gave as its answer, stated in its quote's own words; the
              source is any other conclusion so stated, from a quote on a host
              the answer's quotes are not on. A source on the answer's own
              hosts adds no host, so it is not asked about.
    veto      a number in the answer the source does not state — which also
              catches a conflicting one (1912 against 1915) — or a negation
              word on one side only. A source that only adds a number ("about
              23.4 degrees") is not vetoed: saying more is the point.
    covers    only if both orders say `covers`. Anything short of that — a
              veto, `does_not`, `cannot_tell`, a malformed or missing reply —
              does not cover. Doubt never lifts.

Covering is not sameness, and it does not chain: a source covers the answer,
not the answer's other sources. The status stage counts, for each answer, the
hosts and texts of its own quotes and of the quotes whose conclusions cover it
(occam.status).

Replay
──────
Replies are stored with the two conclusions they were about and the order
they were shown in, never by position. A replay, or a what-if that drops a
quote, reads each reply against the pair it judged; a pair with no stored
reply was not judged, and does not cover.
"""

from __future__ import annotations

import itertools
from typing import Mapping, Optional, Sequence

from pydantic import BaseModel, ConfigDict

from .argue import ArgueResult, norm_conclusion
from .equiv import NEGATIONS, _negations, _numbers
from .model import Model, extract_json
from .snapshot import host
from .spans import states

__all__ = ["COVER_VERDICTS", "CoverPair", "cover_veto", "cover_pairs", "covers_prompt",
           "judge_covers", "covered_by", "hosts_of_snapshots"]

COVER_VERDICTS = ("covers", "does_not", "cannot_tell")


class CoverPair(BaseModel):
    model_config = ConfigDict(frozen=True)

    answer: str            # normalised conclusion — the key corroboration counts under
    source: str
    text_answer: str       # a wording the model actually wrote, shown to the judge
    text_source: str
    veto: str = ""


def cover_veto(answer: str, source: str) -> str:
    """Why the source cannot cover the answer, decided without a model; ""
    if nothing rules it out."""
    missing = _numbers(answer) - _numbers(source)
    if missing:
        return f"the answer states a number the source does not: {', '.join(sorted(missing))}"
    ga, gs = _negations(answer, NEGATIONS), _negations(source, NEGATIONS)
    if ga != gs:
        return f"negation differs: {', '.join(sorted(ga ^ gs))}"
    return ""


def cover_pairs(argued: ArgueResult,
                hosts_of_snapshot: Mapping[str, frozenset[str]]) -> tuple[CoverPair, ...]:
    """Every (answer, source) pair a judge is asked about, in a fixed order.
    Deterministic: live and replay compute the same tuple from the same
    arguments and snapshots."""
    by = argued.by_id()
    wording: dict[str, str] = {}
    hosts: dict[str, set[str]] = {}
    for a in sorted(argued.arguments, key=lambda x: x.id):
        if a.kind == "quote" and states(a.span.quote, a.conclusion):
            k = norm_conclusion(a.conclusion)
            wording.setdefault(k, a.conclusion)
            hosts.setdefault(k, set()).update(hosts_of_snapshot.get(a.span.snapshot_id, ()))
    answers = sorted({norm_conclusion(by[x].conclusion) for x in argued.answers
                      if x and by[x].kind == "quote"} & set(wording))
    out = []
    for a, s in itertools.product(answers, sorted(wording)):
        if s != a and hosts[s] - hosts[a]:
            out.append(CoverPair(answer=a, source=s, text_answer=wording[a],
                                 text_source=wording[s],
                                 veto=cover_veto(wording[a], wording[s])))
    return tuple(out)


def covers_prompt(pair: CoverPair, *, flip: bool = False) -> str:
    """The two statements and nothing else: each is judged fresh (#174)."""
    shown = [("ANSWER", pair.text_answer), ("SOURCE", pair.text_source)]
    if flip:
        shown.reverse()
    return "\n".join([
        "Does the SOURCE statement state everything the ANSWER statement states?\n"
        "- covers: every claim in the ANSWER is also stated in the SOURCE. The SOURCE "
        "may say more.\n"
        "- does_not: the ANSWER claims something the SOURCE does not state, or the two "
        "conflict.\n"
        "- cannot_tell: you cannot decide.\n"
        "Judge only what the two say, not whether it is true.\n"
        'Return JSON only: {"verdict": "covers", '
        '"missing": "<what the SOURCE does not state, or empty>"}\n',
        f"{shown[0][0]}: {shown[0][1]}",
        f"{shown[1][0]}: {shown[1][1]}\n",
    ])


def judge_covers(model: Model, pairs: Sequence[CoverPair], *,
                 temperature: float = 0.0) -> list[tuple[str, str, int, str]]:
    """Two fresh calls per pair no veto ruled out, stored as (answer, source,
    order shown, reply). No call when there is nothing to judge."""
    out = []
    for p in pairs:
        if not p.veto:
            for flip in (0, 1):
                out.append((p.answer, p.source, flip,
                            model.complete(covers_prompt(p, flip=bool(flip)),
                                           temperature=temperature)))
    return out


def _verdict(reply: Optional[str]) -> Optional[str]:
    obj = extract_json(reply) if reply is not None else None
    v = obj.get("verdict") if isinstance(obj, dict) else None
    return v if v in COVER_VERDICTS else None


def covered_by(pairs: Sequence[CoverPair],
               replies: Sequence[tuple[str, str, int, str]]) -> dict[str, frozenset[str]]:
    """For each answer, the source conclusions that cover it: not vetoed, and
    `covers` in both orders. Deterministic."""
    stored = {(a, s, o): r for a, s, o, r in replies}
    out: dict[str, set[str]] = {}
    for p in pairs:
        if p.veto:
            continue
        if all(_verdict(stored.get((p.answer, p.source, o))) == "covers" for o in (0, 1)):
            out.setdefault(p.answer, set()).add(p.source)
    return {a: frozenset(s) for a, s in out.items()}


def hosts_of_snapshots(snapshots) -> dict[str, frozenset[str]]:
    """Each snapshot's hosts, by id: what cover_pairs reads. One text fetched
    from two hosts is one snapshot id; its hosts are merged, never overwritten."""
    out: dict[str, set[str]] = {}
    for s in snapshots:
        out.setdefault(s.id, set()).update(host(u) for u in s.urls)
    return {k: frozenset(v) for k, v in out.items()}
