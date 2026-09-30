"""Stage 2 — arguments whose leaves point into snapshots (#139).

The model is asked for a small derivation: quote steps that copy words out of
a numbered source, and inference or analogy steps that reason from earlier
steps. It is never asked for offsets and never asked for a status or a
pramāṇa. Offsets are computed by `spans.locate`, the pramāṇa is derived from
the step's kind, and the status is computed three stages later.

Why the model quotes rather than points
───────────────────────────────────────
If the model emitted offsets and the quote were read back as
`text[start:end]`, the quote would be present by construction and the
fabrication check could never fire. The model types words; the mechanism
decides whether, and where, they occur.

What is dropped, and why each drop is counted
─────────────────────────────────────────────
A quote step whose words are not admitted by `locate` is dropped, under its
verdict. An inference or analogy step with no premises is dropped as
unsupported: it is an assertion, not an inference, and under the engine's
preference ordering an unsupported ANUMANA step would outrank every verified
quote (SABDA) it attacked. A step resting on a dropped step is dropped too —
counted as a *cascade*, apart from direct drops, because lumping them hides
which happened.

Merging samples — exact, never fuzzy
────────────────────────────────────
Two samples producing the same argument become one argument with both sample
ids. "The same" means the same conclusion after casefolding and whitespace
collapse *and the same support*: the same located span for a quote, the same
merged premises for an inference. Two different derivations of one
conclusion are two arguments — accrual later takes the better — and merging
them would throw one away. Paraphrased conclusions stay separate on purpose;
a fuzzy merge here would bring back the similarity matcher Occam removes.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Literal, Mapping, Optional, Sequence

from pydantic import BaseModel, ConfigDict, model_validator

from .model import Model, extract_json
from .snapshot import Snapshot
from .spans import ADMITTED, VERDICTS, Located, SpanRef, locate
from .types import Pramana

__all__ = [
    "Argument", "ArgueResult", "KINDS", "PRAMANA_OF_KIND",
    "argue", "argue_from_replies", "argue_prompt", "norm_conclusion", "adds_question_number",
    "unquoted_question_numbers",
]

Kind = Literal["quote", "inference", "analogy"]
KINDS: tuple[str, ...] = ("quote", "inference", "analogy")

# Derived, never read from the model. A fetched document is testimony; an
# inference step is inference; an analogy is analogy. Nothing in the MVP can
# certify direct evidence, so PRATYAKSA is unreachable here by design.
PRAMANA_OF_KIND: dict[str, Pramana] = {
    "quote": Pramana.SABDA,
    "inference": Pramana.ANUMANA,
    "analogy": Pramana.UPAMANA,
}

MAX_SOURCE_CHARS = 40_000


def norm_conclusion(s: str) -> str:
    """Casefold and collapse whitespace. The whole of the merge rule."""
    return " ".join(s.casefold().split())


class Argument(BaseModel):
    """One argument after merging: a located quote, or a step over premises.

    Unknown fields are refused rather than ignored. There is no `status`
    here and there must never be one a caller can pass: status is computed
    in `status.py` and nowhere else, and a silently ignored `status=` would
    let a caller believe it had set one.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    conclusion: str
    kind: Kind
    span: Optional[SpanRef] = None
    sub_arguments: tuple[str, ...] = ()
    pramana: Pramana
    sample_ids: tuple[int, ...]
    # Whether the quote, read in its context, supports the conclusion (#146).
    # None: nobody judged it — which is not the same as judged and fine, and
    # the status stage caps it accordingly. Meaningful only on a quote.
    support: Optional[Literal["supports", "cannot_tell"]] = None

    @model_validator(mode="after")
    def _check(self) -> "Argument":
        if self.pramana != PRAMANA_OF_KIND[self.kind]:
            raise ValueError(
                f"{self.id}: pramana {self.pramana.name} for a {self.kind} step. "
                f"The pramāṇa is derived from the kind; a model that could set "
                f"it could promote its own claims."
            )
        if self.kind == "quote":
            if self.span is None or self.span.verdict not in ADMITTED:
                raise ValueError(f"{self.id}: a quote argument needs an admitted span")
            if self.sub_arguments:
                raise ValueError(f"{self.id}: a quote argument has no premises")
        else:
            if self.span is not None:
                raise ValueError(f"{self.id}: a {self.kind} step quotes nothing")
            if not self.sub_arguments:
                raise ValueError(
                    f"{self.id}: a {self.kind} step with no premises is an "
                    f"assertion, not an argument"
                )
        if self.support is not None and self.kind != "quote":
            raise ValueError(f"{self.id}: only a quote has support to judge")
        if not self.sample_ids:
            raise ValueError(f"{self.id}: an argument no sample produced")
        return self


class ArgueResult(BaseModel):
    """Everything stage 2 produced, including what it refused and why."""

    model_config = ConfigDict(frozen=True)

    k: int
    arguments: tuple[Argument, ...]
    answers: tuple[Optional[str], ...]          # per sample: merged id, or None
    answer_notes: tuple[str, ...]               # per sample: why None, or ""
    located: tuple[tuple[int, Located], ...]    # every quote claim, by sample
    malformed: tuple[tuple[int, str], ...]      # (sample, reason)
    dropped: tuple[tuple[int, str, str], ...]   # (sample, step id, reason)
    cascade: tuple[tuple[int, str, str], ...]   # (sample, step id, premise that fell)

    def verdict_counts(self) -> dict[str, int]:
        """Verdicts over every quote claimed, all five written even at zero."""
        c = Counter(loc.verdict for _, loc in self.located)
        return {v: c.get(v, 0) for v in VERDICTS}

    @property
    def spans_claimed(self) -> int:
        return len(self.located)

    def by_id(self) -> dict[str, Argument]:
        return {a.id: a for a in self.arguments}


def argue_prompt(question: str, snapshots: Sequence[Snapshot],
                 max_chars: int = MAX_SOURCE_CHARS) -> str:
    """The instruction. Sources are numbered from 1 in the order given."""
    parts = [
        "Answer the question using ONLY the numbered sources below. "
        "Build a short derivation and return it as JSON, nothing else:\n\n"
        '{"answer": "<id of the step whose conclusion answers the question, '
        'or null if the sources do not answer it>",\n'
        ' "steps": [\n'
        '  {"id": "s1", "kind": "quote", "source": 1, '
        '"quote": "<words copied exactly from source 1>", '
        '"conclusion": "<what that passage establishes>"},\n'
        '  {"id": "s2", "kind": "inference", "from": ["s1"], '
        '"conclusion": "<what follows from the listed steps>"}\n'
        " ]}\n\n"
        "Rules:\n"
        "- A quote must be copied character for character from ONE source: "
        "one contiguous passage, no ellipses, no paraphrase, no added words.\n"
        "- Every inference must list the earlier steps it follows from. "
        "Use kind \"analogy\" only for a step that reasons by comparison.\n"
        "- Conclusions are one short sentence each.\n"
        "- A quote step's conclusion says only what its quote says. Do not repeat "
        "details from the question (a date, a place, a name) unless the quote itself "
        "states them; if the answer needs such a detail, quote the passage that "
        "states it as a step of its own.\n"
        "- If the sources do not answer the question, return "
        '{"answer": null, "steps": []}. Do not use outside knowledge.\n',
        f"QUESTION: {question}\n",
    ]
    for i, s in enumerate(snapshots, 1):
        text = s.text if len(s.text) <= max_chars else s.text[:max_chars]
        parts.append(f"--- SOURCE {i} ({s.urls[0]}) ---\n{text}\n")
    return "\n".join(parts)


def argue(model: Model, question: str, snapshots: Sequence[Snapshot], *,
          k: int = 3, temperature: float = 0.7,
          max_chars: int = MAX_SOURCE_CHARS) -> tuple[list[str], ArgueResult]:
    """Ask the model k times; return the raw replies and what they yield.

    The replies are returned so they can be persisted before anything else
    happens: `argue_from_replies` over them is the replay.
    """
    prompt = argue_prompt(question, snapshots, max_chars)
    replies = [model.complete(prompt, temperature=temperature) for _ in range(k)]
    return replies, argue_from_replies(replies, snapshots)


def argue_from_replies(replies: Sequence[str],
                       snapshots: Sequence[Snapshot]) -> ArgueResult:
    """Deterministic: the same replies and snapshots give the same result."""
    registry: dict[tuple, str] = {}
    built: dict[str, dict[str, Any]] = {}
    answers: list[Optional[str]] = []
    notes: list[str] = []
    located: list[tuple[int, Located]] = []
    malformed: list[tuple[int, str]] = []
    dropped: list[tuple[int, str, str]] = []
    cascade: list[tuple[int, str, str]] = []

    for sid, reply in enumerate(replies):
        obj = extract_json(reply)
        if not isinstance(obj, dict) or not isinstance(obj.get("steps"), list):
            malformed.append((sid, "reply is not a JSON object with a steps list"))
            answers.append(None)
            notes.append("malformed reply")
            continue

        steps: dict[str, dict] = {}
        order: list[str] = []
        for raw in obj["steps"]:
            if not isinstance(raw, dict) or not isinstance(raw.get("id"), str):
                malformed.append((sid, f"step without a string id: {str(raw)[:80]}"))
                continue
            if raw["id"] in steps:
                dropped.append((sid, raw["id"], "duplicate step id"))
                continue
            steps[raw["id"]] = raw
            order.append(raw["id"])

        # Direct checks, one step at a time.
        ok: dict[str, dict] = {}
        for step_id in order:
            raw = steps[step_id]
            kind = raw.get("kind")
            conclusion = raw.get("conclusion")
            if kind not in KINDS:
                dropped.append((sid, step_id, f"unknown kind {kind!r}"))
                continue
            if not isinstance(conclusion, str) or not conclusion.strip():
                dropped.append((sid, step_id, "no conclusion"))
                continue
            if kind == "quote":
                src = raw.get("source")
                quote = raw.get("quote") if isinstance(raw.get("quote"), str) else ""
                if not isinstance(src, int) or not 1 <= src <= len(snapshots):
                    loc = Located(snapshot_id="", quote=quote, verdict="unresolvable",
                                  reason=f"source {src!r} is not one of 1..{len(snapshots)}")
                else:
                    loc = locate(snapshots[src - 1], quote)
                located.append((sid, loc))
                if loc.verdict not in ADMITTED:
                    dropped.append((sid, step_id, loc.verdict))
                    continue
                ok[step_id] = {"kind": kind, "conclusion": conclusion,
                               "span": loc.span, "from": ()}
            else:
                prem = raw.get("from")
                if not isinstance(prem, list) or not prem:
                    dropped.append((sid, step_id, "unsupported: no premises"))
                    continue
                if not all(isinstance(p, str) and p in steps for p in prem):
                    dropped.append((sid, step_id, "premise names an unknown step"))
                    continue
                ok[step_id] = {"kind": kind, "conclusion": conclusion,
                               "span": None, "from": tuple(dict.fromkeys(prem))}

        # Cascade and cycles: resolve in dependency order.
        merged: dict[str, str] = {}      # sample step id -> global argument id
        state: dict[str, str] = {}       # "visiting" | "done" | "dead"

        def resolve(step_id: str) -> Optional[str]:
            if state.get(step_id) == "done":
                return merged[step_id]
            if state.get(step_id) == "dead":
                return None
            if state.get(step_id) == "visiting":
                return None                       # cycle; caller records it
            if step_id not in ok:
                return None
            state[step_id] = "visiting"
            node = ok[step_id]
            subs: list[str] = []
            for p in node["from"]:
                cyclic = state.get(p) == "visiting"
                g = resolve(p)
                if g is None:
                    state[step_id] = "dead"
                    cascade.append((sid, step_id, f"cycle through {p}" if cyclic else p))
                    return None
                subs.append(g)
            if node["kind"] == "quote":
                sp = node["span"]
                key = ("quote", norm_conclusion(node["conclusion"]),
                       sp.snapshot_id, sp.start, sp.end)
            else:
                key = (node["kind"], norm_conclusion(node["conclusion"]),
                       tuple(sorted(subs)))
            gid = registry.get(key)
            if gid is None:
                gid = f"A{len(registry):04d}"
                registry[key] = gid
                built[gid] = {"conclusion": node["conclusion"], "kind": node["kind"],
                              "span": node["span"], "subs": tuple(subs),
                              "samples": [sid]}
            elif sid not in built[gid]["samples"]:
                built[gid]["samples"].append(sid)
            merged[step_id] = gid
            state[step_id] = "done"
            return gid

        for step_id in order:
            if step_id in ok:
                resolve(step_id)

        ans = obj.get("answer")
        if ans is None:
            answers.append(None)
            notes.append("model abstained")
        elif not isinstance(ans, str) or ans not in steps:
            answers.append(None)
            notes.append(f"answer names an unknown step {ans!r}")
        elif ans not in merged:
            answers.append(None)
            notes.append(f"answer step {ans} was dropped")
        else:
            answers.append(merged[ans])
            notes.append("")

    arguments = tuple(
        Argument(id=gid, conclusion=b["conclusion"], kind=b["kind"], span=b["span"],
                 sub_arguments=b["subs"], pramana=PRAMANA_OF_KIND[b["kind"]],
                 sample_ids=tuple(b["samples"]))
        for gid, b in built.items()
    )
    return ArgueResult(
        k=len(replies), arguments=arguments, answers=tuple(answers),
        answer_notes=tuple(notes), located=tuple(located),
        malformed=tuple(malformed), dropped=tuple(dropped), cascade=tuple(cascade),
    )


_EDGE = ".,;:!?\"'()[]"


def _digit_tokens(text: str) -> set[str]:
    """Whole-number tokens, read by splitting on whitespace — no pattern
    matching; "1940s" and "1,000" are not read as numbers. Used to count,
    never to decide."""
    return {t.strip(_EDGE) for t in text.split() if t.strip(_EDGE).isdigit()}


def unquoted_question_numbers(question: str, aid: str,
                              by_id: Mapping[str, "Argument"]) -> set[str]:
    """The numbers from the question that `aid`'s conclusion carries and no
    quote it rests on states, directly or through other steps (#161, #179).

    A count's predicate, never a decision. Nothing needs to cap on it: a
    conclusion carrying a number its quote lacks is not literally in the
    quote, and every inference is the model's step, so status.py's ceilings
    already hold such an argument below `established` (a law checks it)."""
    wanted = _digit_tokens(by_id[aid].conclusion) & _digit_tokens(question)
    stated: set[str] = set()
    todo, seen = [aid], set()
    while wanted and todo:
        a = by_id[todo.pop()]
        if a.id in seen:
            continue
        seen.add(a.id)
        # Argument guarantees a quote carries a span and nothing else does.
        if a.span is not None:
            stated |= _digit_tokens(a.span.quote)
        todo.extend(a.sub_arguments)
    return wanted - stated


def adds_question_number(question: str, a: "Argument") -> bool:
    """A quote argument whose conclusion carries a number from the question
    that its quote does not state (#161): the support judge cannot vouch for
    it, and it must not — the question's premise may be false."""
    return a.kind == "quote" and bool(unquoted_question_numbers(question, a.id, {a.id: a}))
