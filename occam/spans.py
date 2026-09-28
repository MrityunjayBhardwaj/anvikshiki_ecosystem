"""Resolve a span against a snapshot and verify it verbatim (#138).

This is the one mechanism in the pipeline that cannot be delegated to a model.
Without it there is no difference between a sourced claim and an invented one,
and every later guarantee — the solver, the status, the conformal set — would
be computed over sentences nobody checked.

The check itself is one line: the quote, whitespace collapsed, is a substring
of the snapshot's text, whitespace collapsed. Everything else in this module
exists so that the *answer* to that line can be read correctly.

Five verdicts, not one flag
───────────────────────────
A bare boolean says False for an invented sentence and False for a real
sentence the model quoted without its markdown asterisks. Deciding a drop on
that collapse once deleted the central claim of the first real chapter traced,
over a pair of asterisks. So the miss is diagnosed:

    ok             found verbatim                           admit
    markup         identical once emphasis is stripped      admit — formatting, not content
    punctuation    a character inside the content differs   drop, counted apart
    absent         looked, and the words are not there      drop — THE fabrication count
    unresolvable   could not look, or looked in the wrong place   drop, counted apart

Only `absent` is fabrication. A fabrication rate that also counts typography,
missing snapshots or changed extractors reports our own strictness as a fact
about the model.

`checked` is tri-state
──────────────────────
`None` means nobody looked. `False` means someone looked and the words were not
there. `True` means they were. Coercing it to a bool reports every unchecked
span either as a fabrication or as verified, and nothing downstream can tell
afterwards which way it went.

Drop, never downgrade
─────────────────────
A span that fails is removed from what the solver sees, and the removal is
counted. It is never kept at a lower status: a sentence that is not in the
document supports nothing, and "weakly supported by a quote that does not
exist" is not a weaker claim, it is a false one.

What this does NOT establish
────────────────────────────
That the sentence supports the claim it is attached to. A real sentence,
correctly located, passes every check here whatever it is cited for (#146).

No regular expressions
──────────────────────
The engine's `span_verification` answers the same question with `re`, and the
package law forbids importing either. The definitions are kept in step by a
law that runs both over the same cases, because two meanings of "verbatim"
that drift apart are worse than one that is merely strict.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .snapshot import Snapshot, SnapshotStore

__all__ = [
    "SpanRef", "Verdict", "VERDICTS", "ADMITTED", "Tally", "Located",
    "classify", "verify", "locate", "admit", "tally",
    "is_discriminating", "MIN_DISCRIMINATING_LENGTH", "states",
]

Verdict = Literal["ok", "markup", "punctuation", "absent", "unresolvable"]

# A quote shorter than this, whitespace collapsed, cannot discriminate:
# "economics." occurs in most chapters of a business guide, so finding it says
# nothing about whether the model read the claim there. Found and
# discriminating are different questions and are answered separately — the
# verdict stays honest about found-ness, and the status stage caps a leaf
# resting on a short quote (#148). Same number as the engine's, held by a law.
MIN_DISCRIMINATING_LENGTH = 24
VERDICTS: tuple[str, ...] = ("ok", "markup", "punctuation", "absent", "unresolvable")
ADMITTED = frozenset({"ok", "markup"})

# Markdown emphasis a model drops when it quotes prose out of a formatted
# document. Underscores are deliberately absent: `_x_` is valid markdown, but
# stripping `_` mangles snake_case identifiers, and does so in the direction
# that hides a real miss. Kept identical to the engine's choice.
_MARKUP = frozenset("*`")

# Typographic characters a model may substitute for their ASCII originals.
# Used only to explain a miss, never to accept one.
_PUNCTUATION_FOLD = {
    "\u2018": "'", "\u2019": "'",      # single curly quotes
    "\u201c": '"', "\u201d": '"',      # double curly quotes
    "\u2013": "-", "\u2014": "-",      # en dash, em dash
    "\u2212": "-",                     # minus sign
    "\u2026": "...",                   # ellipsis
    "\u00a0": " ",                     # non-breaking space
    "\u2032": "'", "\u2033": '"',      # prime, double prime
}


def _project(text: str, *, markup: bool = False, punctuation: bool = False) -> str:
    """Collapse whitespace; optionally strip emphasis and fold typography.

    Whitespace always collapses: extraction wraps lines and a model quoting
    the text does not reproduce the wrapping. Case never folds — verbatim
    means verbatim, and every loosening of a match rule in this repo has cost
    more than it bought.
    """
    return _project_map(text, markup=markup, punctuation=punctuation)[0]


def _project_map(text: str, *, markup: bool = False,
                 punctuation: bool = False) -> tuple[str, list[int]]:
    """`_project`, plus where each output character came from in `text`.

    The map is what lets offsets be *computed* rather than asked for: find
    the projected quote in the projected text, then read the original
    positions of its first and last characters.
    """
    out: list[str] = []
    origin: list[int] = []
    for i, ch in enumerate(text):
        if markup and ch in _MARKUP:
            continue
        for c in (_PUNCTUATION_FOLD.get(ch, ch) if punctuation else ch):
            if c.isspace():
                if not out or out[-1] == " ":
                    continue
                c = " "
            elif punctuation and c == "-" and out and out[-1] == "-":
                continue
            out.append(c)
            origin.append(i)
    if out and out[-1] == " ":
        out.pop()
        origin.pop()
    return "".join(out), origin


def is_discriminating(quote: str) -> bool:
    """Whether the quote is long enough that finding it means something."""
    return len(_project(quote)) >= MIN_DISCRIMINATING_LENGTH


def states(quote: str, conclusion: str) -> bool:
    """Whether the conclusion is literally among the quoted words.

    Same projection as verification — whitespace collapsed, emphasis ignored,
    case kept — and a final full stop on the conclusion ignored, since a
    sentence ending is form, not content. Anything else is a restatement:
    the model's words, however faithful, and so the model's inference (#158).
    """
    claim = _project(conclusion, markup=True)
    if claim.endswith("."):
        claim = claim[:-1].rstrip()
    return bool(claim) and claim in _project(quote, markup=True)


def classify(quote: str, text: str) -> Verdict:
    """Which of ok / markup / punctuation / absent the quote earns in `text`.

    Ordered from exact to loosest, and `absent` is what is left when nothing
    explains the miss. Every category above `absent` is subtracted from the
    fabrication number, so each must be a difference in *form* — never in
    words. A punctuation-and-markup miss is `punctuation`: a character inside
    the content differs, so it is dropped.
    """
    if not _project(quote):
        return "absent"
    if _project(quote) in _project(text):
        return "ok"
    if _project(quote, markup=True) in _project(text, markup=True):
        return "markup"
    if _project(quote, punctuation=True) in _project(text, punctuation=True):
        return "punctuation"
    if (_project(quote, markup=True, punctuation=True)
            in _project(text, markup=True, punctuation=True)):
        return "punctuation"
    return "absent"


class SpanRef(BaseModel):
    """A claim's pointer into a snapshot, and — once verified — what was found."""

    model_config = ConfigDict(frozen=True)

    snapshot_id: str = Field(description="Content address of the snapshot's body.")
    text_sha256: str = Field(
        description=(
            "Which extraction the offsets belong to. The same body extracted "
            "by another version moves every offset while `snapshot_id` stays "
            "identical, so the id alone cannot pin them."
        ),
    )
    start: int
    end: int
    quote: str = Field(
        description=(
            "The words claimed to sit at [start, end). Verified against the "
            "text, never trusted: it is the thing under test."
        ),
    )
    checked: Optional[bool] = Field(
        default=None,
        description=(
            "None: nobody looked. False: looked, the words are not there. "
            "True: looked, the words are there. Never a bool alone."
        ),
    )
    verdict: Optional[Verdict] = None
    reason: str = Field(
        default="",
        description="Why an `unresolvable` span could not be resolved.",
    )

    @model_validator(mode="after")
    def _check(self) -> "SpanRef":
        if self.start < 0 or self.end <= self.start:
            raise ValueError(
                f"[{self.start}, {self.end}) is not a span. An inference step "
                f"that quotes nothing has no SpanRef at all; an empty one "
                f"would verify as found wherever it pointed."
            )
        if not self.quote.strip():
            raise ValueError("a span with no quote has nothing to verify")
        # The verdict and `checked` must tell the same story, or a reader of
        # one draws the opposite conclusion from a reader of the other.
        allowed = {
            None: {None},
            "ok": {True},
            "markup": {True},
            "punctuation": {False},
            "absent": {False},
            "unresolvable": {None, True},
        }[self.verdict]
        if self.checked not in allowed:
            raise ValueError(
                f"verdict {self.verdict!r} with checked={self.checked!r}; "
                f"expected one of {sorted(allowed, key=repr)}"
            )
        if (self.verdict == "unresolvable") != bool(self.reason):
            raise ValueError("`reason` is required for, and only for, `unresolvable`")
        return self

    @property
    def admitted(self) -> bool:
        return self.verdict in ADMITTED


def _resolve(span: SpanRef, store: SnapshotStore) -> tuple[Optional[Snapshot], str]:
    """The snapshot this span indexes into, or why there is none."""
    snap = store.get(span.snapshot_id)
    if snap is None:
        # Bodies whose extracted text is identical are interchangeable for
        # span resolution — the offsets index into text, and the text is the
        # same by hash. The span still names the body it was made against.
        for other in store.ids_for_text(span.text_sha256):
            snap = store.get(other)
            break
    if snap is None:
        return None, f"snapshot {span.snapshot_id} is not held"
    if snap.text_sha256 != span.text_sha256:
        return None, (
            f"the extraction changed under the offsets: span indexes text "
            f"{span.text_sha256[:12]}…, snapshot now holds "
            f"{snap.text_sha256[:12]}… ({snap.extractor or 'unknown extractor'})"
        )
    if not snap.text.strip():
        return None, f"snapshot yielded no text: {snap.empty_reason}"
    return snap, ""


def verify(span: SpanRef, store: SnapshotStore) -> SpanRef:
    """Resolve the span and return it with `checked`, `verdict` and `reason` set.

    Found-ness is decided on the whole text first, so a fabricated quote is
    `absent` wherever its offsets point. Only a quote that IS there is then
    held to its offsets: words that exist, addressed somewhere they are not,
    are `unresolvable` — the location is part of the claim, and silently
    re-pointing it would hide whatever produced the wrong address.

    Offset agreement ignores emphasis markers, so a span whose offsets take
    in the surrounding asterisks still addresses the words inside them.
    """
    snap, why = _resolve(span, store)
    if snap is None:
        return span.model_copy(update={"checked": None, "verdict": "unresolvable",
                                       "reason": why})

    verdict = classify(span.quote, snap.text)
    if verdict not in ADMITTED:
        return span.model_copy(update={"checked": False, "verdict": verdict, "reason": ""})

    sliced = snap.text[span.start:span.end]
    if _project(sliced, markup=True) != _project(span.quote, markup=True):
        return span.model_copy(update={
            "checked": True, "verdict": "unresolvable",
            "reason": (
                f"the quote is in the text but not at [{span.start}, {span.end}), "
                f"which holds {sliced[:60]!r}"
            ),
        })
    return span.model_copy(update={"checked": True, "verdict": verdict, "reason": ""})


class Located(BaseModel):
    """The outcome of placing a claimed quote in a snapshot.

    `span` is present whenever the words could be placed — including a
    `punctuation` miss, whose location is known even though it is dropped —
    and absent for `absent` and `unresolvable`, which have nowhere to point.
    The verdict is carried here as well as on the span so that a miss with no
    location is still counted.
    """

    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    quote: str
    verdict: Verdict
    span: Optional[SpanRef] = None
    reason: str = ""


def locate(snapshot: Optional[Snapshot], quote: str, *,
           snapshot_id: str = "") -> Located:
    """Turn a claimed quote into offsets, mechanically, and verify it.

    The model supplies words; this supplies where they are. Asking a model
    for character offsets instead would make the quote `text[start:end]` by
    construction — always present, so `absent` could never fire and the
    fabrication count would be connected to nothing (see #139).

    The first occurrence is taken. Which occurrence does not change the
    verdict, and the rule is deterministic, so a replay lands on the same one.
    """
    sid = snapshot.id if snapshot is not None else snapshot_id
    if snapshot is None:
        return Located(snapshot_id=sid, quote=quote, verdict="unresolvable",
                       reason=f"snapshot {sid or '(none named)'} is not held")
    if not snapshot.text.strip():
        return Located(snapshot_id=sid, quote=quote, verdict="unresolvable",
                       reason=f"snapshot yielded no text: {snapshot.empty_reason}")
    if not _project(quote):
        return Located(snapshot_id=sid, quote=quote, verdict="absent",
                       reason="empty quote")

    verdict = classify(quote, snapshot.text)
    if verdict == "absent":
        return Located(snapshot_id=sid, quote=quote, verdict="absent")

    space = {"ok": {}, "markup": {"markup": True}}.get(verdict)
    candidates = [space] if space is not None else [
        {"punctuation": True}, {"markup": True, "punctuation": True}]
    for kw in candidates:
        ptext, origin = _project_map(snapshot.text, **kw)
        pquote = _project(quote, **kw)
        pos = ptext.find(pquote)
        if pos >= 0:
            start, end = origin[pos], origin[pos + len(pquote) - 1] + 1
            break
    else:  # classify found it, so one of the spaces must — say so if not
        raise AssertionError(f"classify said {verdict} but no projection places {quote!r}")

    span = SpanRef(snapshot_id=sid, text_sha256=snapshot.text_sha256,
                   start=start, end=end, quote=quote,
                   checked=verdict in ADMITTED, verdict=verdict)
    return Located(snapshot_id=sid, quote=quote, verdict=verdict, span=span)


def admit(spans: Iterable[SpanRef]) -> tuple[tuple[SpanRef, ...], tuple[SpanRef, ...]]:
    """Split verified spans into (admitted, dropped).

    Refuses an unverified span rather than guessing which side it belongs on:
    dropping it would count it nowhere, and admitting it would let an
    unchecked sentence reach the solver.
    """
    kept: list[SpanRef] = []
    dropped: list[SpanRef] = []
    for s in spans:
        if s.verdict is None:
            raise ValueError(
                f"span at {s.snapshot_id}[{s.start}:{s.end}] was never verified; "
                f"call verify() first"
            )
        (kept if s.admitted else dropped).append(s)
    return tuple(kept), tuple(dropped)


class Tally(BaseModel):
    """Verdict counts over a stated population. Every rate names its denominator."""

    model_config = ConfigDict(frozen=True)

    total: int
    counts: dict[str, int]

    def frac(self, verdict: str) -> Optional[float]:
        """`None` over zero spans. A rate of 0.0 from a run that verified
        nothing would read as "no fabrication" — the empty loop printing as
        the clean result."""
        if verdict not in VERDICTS:
            raise KeyError(verdict)
        return self.counts[verdict] / self.total if self.total else None

    @property
    def absent_frac(self) -> Optional[float]:
        """The fabrication rate — `absent` over every span verified."""
        return self.frac("absent")

    def __str__(self) -> str:
        parts = " · ".join(f"{v} {self.counts[v]}" for v in VERDICTS)
        return f"{parts} (of {self.total} spans verified)"


def tally(spans: Iterable[SpanRef]) -> Tally:
    """Count verdicts, every one of the five present even at zero.

    A verdict missing from the counts cannot be told apart from one nobody
    computed, so zeros are written out. Unverified spans are refused for the
    same reason `admit` refuses them.
    """
    spans = tuple(spans)
    if any(s.verdict is None for s in spans):
        raise ValueError("tally over unverified spans; call verify() first")
    c = Counter(s.verdict for s in spans)
    return Tally(total=len(spans), counts={v: c.get(v, 0) for v in VERDICTS})
