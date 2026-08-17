# anvikshiki_v4/span_verification.py
"""Does this quote actually appear in this source text?

One definition of "verbatim", in one place, because there is about to be more
than one caller: extraction checks a quote against the section it was read
from, and the validation gate checks it again against the document the
provenance points at. Two implementations of this question would drift on
exactly the details below, and a citation check that means something slightly
different in two places is worse than one that is merely strict.

What is normalised, and what is not
───────────────────────────────────
**Whitespace is normalised.** Markdown wraps lines, extraction hands the model
a section with hard line breaks in the middle of sentences, and a model
quoting that text will not reproduce the wrapping. Treating a newline as
different from a space would fail almost every true quote, so runs of
whitespace collapse to one space and the ends are stripped.

**Case is not normalised.** Verbatim means verbatim. Folding case buys very
little — models rarely change case mid-sentence — and every loosening of a
match rule in this package has cost more than it bought. The extraction harness
audit's finding was that a matcher loose enough to be forgiving was loose
enough to score an exact logical inverse as a perfect match.

**Punctuation is not normalised either — but its absence is diagnosed.**
A model that renders `'` as `’` or `--` as `—` produces a quote that is not
verbatim by this rule, and refusing it is correct. The danger is what happens
to the *number*: if a run reports "40% of quotes not found in source", a reader
takes that as fabrication, when it may be a model that types typographic
apostrophes. That is our own strictness producing a signal that reads as a fact
about the model.

So the verdict stays strict and `diagnose` says which kind of miss it was.
A rate made of punctuation substitutions and a rate made of invented sentences
are different findings, and nothing downstream can tell them apart from a bare
boolean.
"""

from __future__ import annotations

import re

_WHITESPACE = re.compile(r"\s+")
_HYPHEN_RUN = re.compile(r"-{2,}")

# Typographic characters a model may substitute for their ASCII originals.
# Used only to explain a miss, never to accept one.
_PUNCTUATION_FOLD = {
    "‘": "'", "’": "'",           # single curly quotes
    "“": '"', "”": '"',           # double curly quotes
    "–": "-", "—": "-",           # en dash, em dash
    "−": "-",                          # minus sign
    "…": "...",                        # ellipsis
    " ": " ",                          # non-breaking space
    "′": "'", "″": '"',           # prime, double prime
}

# A quote shorter than this cannot discriminate: "growth" appears in most
# chapters of a business guide, so finding it proves nothing about whether the
# model read the claim there. The gate that drops predicates lives elsewhere;
# this constant is here so both callers agree on the threshold.
MIN_DISCRIMINATING_LENGTH = 24


def normalise_whitespace(text: str) -> str:
    """Collapse whitespace runs to single spaces and strip the ends."""
    return _WHITESPACE.sub(" ", text).strip()


def fold_punctuation(text: str) -> str:
    """Replace typographic punctuation with its ASCII original.

    Diagnostic only. Nothing decides a match on the folded form, so this errs
    toward folding too much rather than too little: the cost of a false
    `punctuation` verdict is that one miss is described too gently, while the
    cost of a false `absent` is a fabrication rate inflated by typography.

    Hyphen runs collapse for that reason. A source written with `--` and a
    model that renders it `—` fold to `--` and `-`, which do not match, and the
    substitution would be reported as an invented sentence.
    """
    for fancy, plain in _PUNCTUATION_FOLD.items():
        text = text.replace(fancy, plain)
    return _HYPHEN_RUN.sub("-", text)


def quote_appears_in(quote: str, source: str) -> bool:
    """Whether `quote` occurs verbatim in `source`, whitespace aside.

    An empty quote is not found. It is not an error either — the caller has to
    distinguish "the model gave no quote" from "the model gave one that is not
    there", and collapsing them here would take that choice away.
    """
    if not quote.strip():
        return False
    return normalise_whitespace(quote) in normalise_whitespace(source)


def diagnose(quote: str, source: str) -> str:
    """Why the quote was not found, or "" when it was.

    The categories exist so a not-found rate can be read. In order of how much
    they should worry someone:

      `absent`                     — the words are not in the source at all.
                                     This is the one that means fabrication.
      `punctuation`                — matches once typographic characters are
                                     folded to ASCII. A rendering artefact, not
                                     an invention.
      `too short to discriminate`  — found, but so short that finding it says
                                     nothing. Reported rather than silently
                                     accepted.
      `empty`                      — the model returned no quote for this
                                     predicate.
    """
    if not quote.strip():
        return "empty"

    if quote_appears_in(quote, source):
        if len(normalise_whitespace(quote)) < MIN_DISCRIMINATING_LENGTH:
            return "too short to discriminate"
        return ""

    if normalise_whitespace(fold_punctuation(quote)) in normalise_whitespace(
        fold_punctuation(source)
    ):
        return "punctuation"

    return "absent"
