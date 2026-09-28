"""Stage 3a — does each quote, read in place, support what it is cited for? (#146)

The span check proves a sentence is present. It does not prove the sentence
says what the argument claims. A real sentence, correctly located, can be
cited for something it does not say, and every mechanical check passes it:

    source   "Proponents claim that rapid growth alone can make a company viable."
    quote    "rapid growth alone can make a company viable"
    claim    "Growth alone makes a company viable."

The quote supports the claim only if you cannot see "Proponents claim". So
the judge is shown the span *in its context* — which the mechanism can do
because it holds the offsets — and asked whether the source itself asserts
the conclusion.

Three outcomes, as `checked` has three
──────────────────────────────────────
    supports           kept
    does_not_support   dropped — and everything resting on it, counted apart
    cannot_tell        kept, capped at provisional by the status stage

A pair the judge did not return is `cannot_tell`, never `supports`: an
omission must not read as approval. An argument that was never judged at all
(an older artifact, or a run without this stage) carries `support=None`, and
the status stage caps that too.

What this does not fix
──────────────────────
A source that asserts something false. If the page says water boils at
50 °C, the quote supports the claim perfectly. That is a single lying source,
not a misread one, and it needs corroboration, not this.
"""

from __future__ import annotations

from collections import Counter
from typing import Optional, Sequence

from pydantic import BaseModel, ConfigDict

from .argue import Argument, ArgueResult
from .model import Model, extract_json
from .snapshot import Snapshot

__all__ = ["SUPPORT_VERDICTS", "SupportResult", "support", "support_from_replies",
           "support_prompt", "apply_support", "CONTEXT_CHARS"]

SUPPORT_VERDICTS = ("supports", "does_not_support", "cannot_tell")
CONTEXT_CHARS = 400


def _context(arg: Argument, texts: dict[str, str]) -> str:
    text = texts.get(arg.span.snapshot_id, "")
    s, e = arg.span.start, arg.span.end
    if not text or e > len(text):
        return f"«{arg.span.quote}»"
    lo, hi = max(0, s - CONTEXT_CHARS), min(len(text), e + CONTEXT_CHARS)
    return (("…" if lo else "") + text[lo:s] + "«" + text[s:e] + "»" + text[e:hi]
            + ("…" if hi < len(text) else ""))


def support_prompt(quotes: Sequence[Argument], snapshots: Sequence[Snapshot]) -> str:
    texts = {s.id: s.text for s in snapshots}
    parts = [
        "For each item, a passage is marked «like this» inside the text around it, "
        "and a CLAIM is attributed to that passage. Decide whether the source "
        "itself asserts the claim through the marked passage.\n\n"
        "- supports: the source, in its own voice, states what the claim says.\n"
        "- does_not_support: the passage says something else; or the source only "
        "reports that someone else holds the view (\"critics say\", \"proponents "
        "claim\"); or the passage is hypothetical, negated, or about a different "
        "subject; or the claim adds content the passage does not contain.\n"
        "- cannot_tell: the passage is too ambiguous to decide.\n\n"
        "Judge only what the text says, not whether the claim is true in the world.\n"
        'Return JSON only: {"judgments": [{"id": "A0000", "verdict": "supports"}]}\n',
    ]
    for a in quotes:
        parts.append(f"--- {a.id}\nTEXT: {_context(a, texts)}\nCLAIM: {a.conclusion}\n")
    return "\n".join(parts)


class SupportResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    k: int
    verdicts: dict[str, str]                     # quote id -> majority verdict
    votes: dict[str, dict[str, int]]             # quote id -> verdict -> samples
    unanswered: dict[str, int]                   # quote id -> samples that omitted it
    malformed: tuple[tuple[int, str], ...]
    dropped: tuple[str, ...]                     # quote ids judged does_not_support
    cascade: tuple[tuple[str, str], ...]         # (argument, the dropped one it rested on)


def support(model: Model, argued: ArgueResult, snapshots: Sequence[Snapshot], *,
            k: int = 1, temperature: float = 0.0) -> tuple[list[str], SupportResult]:
    """Ask k times; return raw replies and the aggregated verdicts."""
    quotes = [a for a in argued.arguments if a.kind == "quote"]
    if not quotes:
        return [], support_from_replies([], argued)
    prompt = support_prompt(quotes, snapshots)
    replies = [model.complete(prompt, temperature=temperature) for _ in range(k)]
    return replies, support_from_replies(replies, argued)


def support_from_replies(replies: Sequence[str], argued: ArgueResult) -> SupportResult:
    """Deterministic. A verdict needs a strict majority of the k samples;
    anything short of one — including silence — is `cannot_tell`."""
    quote_ids = [a.id for a in argued.arguments if a.kind == "quote"]
    k = len(replies)
    votes = {q: Counter() for q in quote_ids}
    unanswered = {q: 0 for q in quote_ids}
    malformed: list[tuple[int, str]] = []
    for sid, reply in enumerate(replies):
        obj = extract_json(reply)
        items = obj.get("judgments") if isinstance(obj, dict) else None
        if not isinstance(items, list):
            malformed.append((sid, "reply is not a JSON object with a judgments list"))
            for q in quote_ids:
                unanswered[q] += 1
            continue
        seen: dict[str, str] = {}
        for it in items:
            if (isinstance(it, dict) and it.get("id") in votes
                    and it.get("verdict") in SUPPORT_VERDICTS and it["id"] not in seen):
                seen[it["id"]] = it["verdict"]
        for q in quote_ids:
            if q in seen:
                votes[q][seen[q]] += 1
            else:
                unanswered[q] += 1
    need = k // 2 + 1
    verdicts = {}
    for q in quote_ids:
        top = [v for v in ("supports", "does_not_support") if votes[q][v] >= need]
        verdicts[q] = top[0] if k and top else "cannot_tell"
    return SupportResult(k=k, verdicts=verdicts,
                         votes={q: dict(votes[q]) for q in quote_ids},
                         unanswered=unanswered, malformed=tuple(malformed),
                         dropped=(), cascade=())


def apply_support(argued: ArgueResult, judged: SupportResult) -> tuple[ArgueResult, SupportResult]:
    """Drop what does not support its claim, and everything built on it.

    Kept quotes carry their verdict; answers that pointed at a dropped
    argument become None with the reason, so abstention can name this stage.
    """
    dropped = {q for q, v in judged.verdicts.items() if v == "does_not_support"}
    gone = set(dropped)
    cascade: list[tuple[str, str]] = []
    changed = True
    while changed:
        changed = False
        for a in argued.arguments:
            if a.id in gone:
                continue
            hit = next((s for s in a.sub_arguments if s in gone), None)
            if hit is not None:
                gone.add(a.id)
                cascade.append((a.id, hit))
                changed = True
    kept = tuple(
        a.model_copy(update={"support": judged.verdicts.get(a.id)}) if a.kind == "quote" else a
        for a in argued.arguments if a.id not in gone
    )
    answers, notes = [], []
    for ans, note in zip(argued.answers, argued.answer_notes):
        if ans is not None and ans in gone:
            answers.append(None)
            notes.append(f"answer {ans} rested on a quote that does not support its claim")
        else:
            answers.append(ans)
            notes.append(note)
    new = argued.model_copy(update={"arguments": kept, "answers": tuple(answers),
                                    "answer_notes": tuple(notes)})
    return new, judged.model_copy(update={"dropped": tuple(sorted(dropped)),
                                          "cascade": tuple(cascade)})
