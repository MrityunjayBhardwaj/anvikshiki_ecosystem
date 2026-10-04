"""Stage 3b — does a quoted answer give the reason the question asks for? (#194)

A question that asks for a cause — "Why did the bridge collapse?" — is
answered by a reason, and a reason has three parts: the cause, the effect,
and the link between them. An inference step that joins the dots is the
model's, and caps at hypothesis like every inference. But a source can state
the reason itself, in one passage, and then the answer is a quote, not an
inference, and may rise as far as any quote (prompt 3, #210).

That opening needs a guard. A quote is checked for being present, for
supporting what it is cited for, and — with a second host — for being said
twice. None of those asks whether it answers *this* question, and a true
sentence that does not ("The bridge opened in July 1940") would pass them
all. So, on a question that asks for a cause, a quote that is an answer
keeps its status above hypothesis only if both hold:

    link    its conclusion carries a causal link ("because", "caused by",
            "due to", …). Cause and effect side by side, with no link, is
            the reader's inference, not the source's statement.
    judge   a fresh call, shown the question and that one statement and
            nothing else, says it gives the reason the question asks for.

Otherwise the status stage caps it at hypothesis and names why. Doubt never
lifts: a malformed reply, `cannot_tell`, or no reply at all keeps the cap.

The judge sees the question, which the support judge must not (a question's
premise is context for grouping, never for vouching). That is safe here
because this judge can only *withhold* a status, never grant one: a false
premise in the question can make it say `does_not`, which only keeps the cap.

Replies are stored with the id of the quote they were about, not by
position, so a replay — or a what-if that drops a quote — reads each reply
against the statement it judged.
"""

from __future__ import annotations

from typing import Mapping, Optional, Sequence

from .argue import Argument, ArgueResult
from .model import Model, extract_json

__all__ = ["REASON_VERDICTS", "CAUSAL_LINKS", "asks_for_a_cause", "states_a_link",
           "reason_candidates", "reason_prompt", "judge_reasons", "reason_bounds"]

REASON_VERDICTS = ("gives_reason", "does_not", "cannot_tell")

# Word sequences that link a cause to an effect. "so" is left out: it is as
# often about degree as about cause. "since" is about time as often as cause;
# which uses of it count is the link rule (`Params.why_check`, see
# states_a_link). What passes is still judged before it can lift.
CAUSAL_LINKS: tuple[tuple[str, ...], ...] = tuple(tuple(p.split()) for p in (
    "because", "due to", "owing to", "caused by", "cause", "causes", "caused", "causing",
    "result of", "results from", "resulted from", "resulting from", "as a result",
    "leads to", "led to", "lead to", "responsible for", "produced by", "driven by",
    "triggered by", "therefore", "thus", "hence",
))


def _words(text: str) -> list[str]:
    out, cur = [], []
    for ch in text.casefold():
        if ch.isalpha():
            cur.append(ch)
        elif cur:
            out.append("".join(cur))
            cur = []
    if cur:
        out.append("".join(cur))
    return out


# Whole words: a prefix test on "caus" would take "causeway" for a cause.
CAUSE_WORDS = frozenset({"why", "cause", "causes", "caused", "causing", "causal", "causation"})


def asks_for_a_cause(question: str) -> bool:
    """A question with "why", or a form of "cause", as a whole word."""
    return any(w in CAUSE_WORDS for w in _words(question))


# Where a causal "since" can stand: opening the text or a clause.
_CLAUSE_OPENERS = ".,;:!?(\u2014\u2013\"'\u201c\u2018"


def _since_links(text: str, rule: int) -> bool:
    """Rule 2 (#194): any "since" a letter follows. "since 1940" fails, but
    "since the 1980s" (run 5, q07), which is time, passes.
    Rule 3 (#213): only a "since" that opens the text or a clause, before a
    letter. "Since blue light scatters more, the sky is blue" passes; "the
    leading hypothesis since the 1980s" and "Since 1940, …" do not. A clause
    "since" can still be time ("…, since the 1980s") — the judge reads it."""
    low = text.casefold()
    i = low.find("since")
    while i >= 0:
        after = low[i + 5:]
        if after[:1] in (" ", ",") and after.lstrip(" ,")[:1].isalpha():
            before = low[:i].rstrip()
            if rule < 3 or not before or before[-1] in _CLAUSE_OPENERS:
                return True
        i = low.find("since", i + 5)
    return False


def states_a_link(text: str, rule: int = 3) -> bool:
    """Whether the text carries a causal link, matched on whole words, under
    link rule `rule` (`Params.why_check`)."""
    ws = _words(text)
    if any(tuple(ws[i:i + len(p)]) == p for p in CAUSAL_LINKS for i in range(len(ws))):
        return True
    return _since_links(text, rule)


def reason_candidates(argued: ArgueResult, question: str, rule: int = 3) -> list[Argument]:
    """The quotes a reason judge is asked about: on a question that asks for a
    cause, every quote some sample gave as its answer whose words carry a link.
    In id order, one function for the live run and the replay."""
    if not asks_for_a_cause(question):
        return []
    by = argued.by_id()
    ids = sorted({x for x in argued.answers if x and by[x].kind == "quote"})
    return [by[x] for x in ids if states_a_link(by[x].conclusion, rule)]


def reason_prompt(question: str, statement: str) -> str:
    """One statement, nothing else: each is judged fresh (#174)."""
    return "\n".join([
        "Does the STATEMENT give the reason the QUESTION asks for?\n"
        "- gives_reason: the statement itself says what causes the thing the question "
        "asks about.\n"
        "- does_not: it states a fact about the subject, or a cause of something else, "
        "but not the reason asked for.\n"
        "- cannot_tell: you cannot decide.\n"
        "Judge only what the statement says, not whether it is true.\n"
        'Return JSON only: {"verdict": "gives_reason"}\n',
        f"QUESTION: {question}",
        f"STATEMENT (copied from a source): {statement}\n",
    ])


def judge_reasons(model: Model, argued: ArgueResult, question: str, *,
                  temperature: float = 0.0, rule: int = 3) -> list[tuple[str, str]]:
    """One fresh call per candidate, stored as (quote id, reply)."""
    return [(a.id, model.complete(reason_prompt(question, a.conclusion), temperature=temperature))
            for a in reason_candidates(argued, question, rule)]


def _verdict(reply: Optional[str]) -> Optional[str]:
    obj = extract_json(reply) if reply is not None else None
    v = obj.get("verdict") if isinstance(obj, dict) else None
    return v if v in REASON_VERDICTS else None


def reason_bounds(argued: ArgueResult, question: str,
                  replies: Sequence[tuple[str, str]], rule: int = 3) -> dict[str, str]:
    """For each quote answer on a question asking for a cause that has not
    shown it gives the reason: the bound the status stage names. Deterministic."""
    if not asks_for_a_cause(question):
        return {}
    stored: Mapping[str, str] = dict(replies)
    by = argued.by_id()
    out: dict[str, str] = {}
    for aid in sorted({x for x in argued.answers if x and by[x].kind == "quote"}):
        if not states_a_link(by[aid].conclusion, rule):
            out[aid] = (f"quote {aid} answers a question asking for a cause, but its words "
                        f"state no causal link")
            continue
        v = _verdict(stored.get(aid))
        if v == "gives_reason":
            continue
        said = {"does_not": "the judge said it does not give the reason asked for",
                "cannot_tell": "the judge could not tell if it gives the reason asked for",
                None: ("no readable reply from the reason judge" if aid in stored
                       else "the reason judge was not asked")}[v]
        out[aid] = f"quote {aid}: {said}"
    return out
