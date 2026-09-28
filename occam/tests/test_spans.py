"""A span is verified against a snapshot, with five verdicts and a tri-state flag (#138).

Both directions, always. A guard that drops everything is worse than the bug it
replaces, because it looks like rigour: the fabrication rate reads zero and no
claim survives to be wrong. So every law that proves a bad span is dropped sits
beside one that proves a good span survives.

Nothing here touches the network; snapshots are built from bytes in the test.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from occam.snapshot import SnapshotStore, capture
from occam.spans import (
    ADMITTED,
    VERDICTS,
    SpanRef,
    admit,
    classify,
    tally,
    verify,
)

T0 = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)

TEXT = (
    "Unit economics decide survival.\n"
    "A business creates value if and only if **LTV exceeds CAC** over the\n"
    "customer's lifetime. Growth without that is borrowed time."
)


def _store(text=TEXT, body=b"<html>chapter</html>", **kw):
    store = SnapshotStore()
    snap = store.put(capture(url="https://example.com/ch", body=body, text=text,
                             fetched_at=T0, extractor="test/1", **kw))
    return store, snap


def _span(snap, quote, start=None, end=None, **kw):
    if start is None:
        start = snap.text.index(quote) if quote in snap.text else 0
    if end is None:
        end = start + len(quote)
    return SpanRef(snapshot_id=snap.id, text_sha256=snap.text_sha256,
                   start=start, end=end, quote=quote, **kw)


# ── the direction that matters more: real spans survive ─────

def test_a_real_span_survives():
    store, snap = _store()
    v = verify(_span(snap, "Unit economics decide survival."), store)
    assert (v.verdict, v.checked, v.admitted) == ("ok", True, True)


def test_a_real_span_across_a_line_break_survives():
    """Extraction wraps lines; a model quoting the sentence does not."""
    store, snap = _store()
    raw = "over the\ncustomer's lifetime"
    start = snap.text.index(raw)
    v = verify(_span(snap, "over the customer's lifetime", start=start,
                     end=start + len(raw)), store)
    assert v.verdict == "ok" and v.admitted


def test_dropped_asterisks_are_markup_and_admitted_not_fabrication():
    """The case that once deleted a chapter's central claim. The words are
    identical; only emphasis differs."""
    store, snap = _store()
    quote = "if and only if LTV exceeds CAC over the customer's lifetime"
    start = snap.text.index("if and only if")
    end = snap.text.index("lifetime") + len("lifetime")
    v = verify(_span(snap, quote, start=start, end=end), store)
    assert (v.verdict, v.checked, v.admitted) == ("markup", True, True)
    t = tally([v])
    assert t.counts["absent"] == 0 and t.absent_frac == 0.0


def test_offsets_taking_in_the_asterisks_still_address_the_words():
    store, snap = _store()
    start = snap.text.index("**LTV")
    end = snap.text.index("CAC**") + len("CAC**")
    v = verify(_span(snap, "LTV exceeds CAC", start=start, end=end), store)
    assert v.verdict == "ok" and v.admitted


# ── and the other direction: bad spans are dropped ──────────

def test_a_planted_absent_span_is_dropped_and_absent_frac_rises():
    store, snap = _store()
    real = verify(_span(snap, "Unit economics decide survival."), store)
    before = tally([real])
    fake = verify(_span(snap, "Growth is always worth any price.", start=0, end=10), store)
    assert (fake.verdict, fake.checked, fake.admitted) == ("absent", False, False)
    after = tally([real, fake])
    assert before.absent_frac == 0.0
    assert after.counts["absent"] == 1 and after.absent_frac == 0.5
    kept, dropped = admit([real, fake])
    assert kept == (real,) and dropped == (fake,)


def test_a_changed_character_is_punctuation_and_dropped_apart_from_absent():
    store, snap = _store()
    quote = "the customer’s lifetime"   # typographic apostrophe
    start = snap.text.index("customer's") - len("the ")
    v = verify(_span(snap, quote, start=start, end=start + len(quote)), store)
    assert (v.verdict, v.checked, v.admitted) == ("punctuation", False, False)
    t = tally([v])
    assert t.counts == {**{k: 0 for k in VERDICTS}, "punctuation": 1}
    assert t.absent_frac == 0.0


def test_case_is_not_folded():
    """Verbatim means verbatim. A casefolded match is a changed word."""
    assert classify("unit economics decide survival.", TEXT) == "absent"


# ── could not look, counted apart from fabrication ──────────

def test_a_text_hash_mismatch_is_unresolvable_and_not_absent():
    store, snap = _store()
    stale = SpanRef(snapshot_id=snap.id, text_sha256="0" * 64, start=0, end=4,
                    quote="Unit")
    v = verify(stale, store)
    assert (v.verdict, v.checked) == ("unresolvable", None)
    assert "extraction changed" in v.reason
    t = tally([v])
    assert t.counts["unresolvable"] == 1 and t.counts["absent"] == 0


def test_the_same_body_under_a_new_extractor_is_unresolvable():
    """The M0 two-hash design, exercised end to end: same bytes, new
    extraction, offsets that no longer mean what they meant."""
    body = b"<p>same bytes</p>"
    _, old = _store(text="Growth helps margins.", body=body)
    store, _ = _store(text="  Growth helps margins. [ad]", body=body)
    v = verify(_span(old, "Growth helps"), store)
    assert v.verdict == "unresolvable" and v.checked is None


def test_a_missing_snapshot_is_unresolvable_with_checked_none():
    _, snap = _store()
    v = verify(_span(snap, "Unit economics"), SnapshotStore())
    assert (v.verdict, v.checked) == ("unresolvable", None)
    assert "not held" in v.reason


def test_an_unreadable_snapshot_is_unresolvable_not_absent():
    """A paywall is 'could not look', never 'nothing there'."""
    store = SnapshotStore()
    snap = store.put(capture(url="https://x/pay", body=b"<p>subscribe</p>", text="",
                             fetched_at=T0, empty_reason="paywalled"))
    span = SpanRef(snapshot_id=snap.id, text_sha256=snap.text_sha256,
                   start=0, end=5, quote="Units")
    v = verify(span, store)
    assert (v.verdict, v.checked) == ("unresolvable", None)
    assert "paywalled" in v.reason


def test_a_body_with_identical_text_resolves_the_span():
    """Bodies whose text hashes the same are interchangeable for resolution
    (the M0 store's promise); the span keeps naming the body it was made on."""
    _, a = _store(body=b"<p>ad one</p>")
    store, _ = _store(body=b"<p>ad two</p>")
    v = verify(_span(a, "Unit economics decide survival."), store)
    assert v.verdict == "ok" and v.snapshot_id == a.id


def test_real_words_at_the_wrong_offsets_are_unresolvable_not_ok():
    """The location is part of the claim. Re-pointing it silently would hide
    whatever produced the wrong address."""
    store, snap = _store()
    v = verify(_span(snap, "Unit economics", start=40, end=54), store)
    assert (v.verdict, v.checked, v.admitted) == ("unresolvable", True, False)
    assert "not at [40, 54)" in v.reason


def test_a_fabricated_quote_is_absent_wherever_its_offsets_point():
    """Found-ness is decided before offsets, so fabrication is never hidden
    inside the unresolvable count."""
    store, snap = _store()
    v = verify(_span(snap, "Profit is irrelevant.", start=10_000, end=10_021), store)
    assert v.verdict == "absent"


# ── the tri-state and the contract between the fields ──────

@pytest.mark.parametrize("verdict,checked", [
    ("ok", False), ("ok", None), ("markup", None),
    ("absent", True), ("absent", None), ("punctuation", None),
    (None, True), (None, False),
])
def test_verdict_and_checked_cannot_disagree(verdict, checked):
    kw = {"reason": "x"} if verdict == "unresolvable" else {}
    with pytest.raises(ValidationError):
        SpanRef(snapshot_id="sha256:a", text_sha256="b", start=0, end=1,
                quote="q", verdict=verdict, checked=checked, **kw)


def test_unverified_is_none_not_false():
    """The mutation this law exists for: coerce `checked` to a bool and an
    unverified span reads as a looked-and-failed one."""
    s = SpanRef(snapshot_id="sha256:a", text_sha256="b", start=0, end=1, quote="q")
    assert s.checked is None and s.verdict is None


def test_unverified_spans_are_refused_not_silently_sorted():
    s = SpanRef(snapshot_id="sha256:a", text_sha256="b", start=0, end=1, quote="q")
    with pytest.raises(ValueError, match="never verified"):
        admit([s])
    with pytest.raises(ValueError, match="unverified"):
        tally([s])


@pytest.mark.parametrize("start,end,quote", [(5, 5, "x"), (6, 5, "x"),
                                             (-1, 3, "x"), (0, 3, "   ")])
def test_an_empty_or_inverted_span_is_refused(start, end, quote):
    with pytest.raises(ValidationError):
        SpanRef(snapshot_id="sha256:a", text_sha256="b", start=start, end=end,
                quote=quote)


def test_only_ok_and_markup_are_admitted():
    assert ADMITTED == {"ok", "markup"}
    assert set(VERDICTS) == {"ok", "markup", "punctuation", "absent", "unresolvable"}


def test_the_tally_writes_every_zero_and_names_its_denominator():
    t = tally([])
    assert t.counts == {v: 0 for v in VERDICTS} and t.total == 0
    assert "of 0 spans verified" in str(t)


# ── one meaning of "verbatim", held in step with the engine's ──

# (quote, source). Covers every verdict, and the combined miss that the engine
# names separately and Occam folds into `punctuation`.
_AGREEMENT_CASES = [
    ("LTV exceeds CAC", "if **LTV exceeds CAC** then"),
    ("if LTV exceeds CAC then", "if **LTV exceeds CAC** then"),
    ("the customer’s lifetime", "the customer's lifetime"),
    ("a — b", "a -- b"),
    ("the “best” LTV", 'the **"best"** LTV'),
    ("wrapped\n  across   lines", "wrapped across lines"),
    ("Invented sentence here.", "Nothing like that at all."),
    ("CASE matters", "case matters"),
    ("`code` span", "code span"),
    ("wait…", "wait..."),
]

_ENGINE_TO_OCCAM = {
    "": "ok",
    "too short to discriminate": "ok",
    "markup": "markup",
    "punctuation": "punctuation",
    "punctuation and markup": "punctuation",
    "absent": "absent",
}


@pytest.mark.parametrize("quote,source", _AGREEMENT_CASES)
def test_occam_and_the_engine_agree_on_what_verbatim_means(quote, source):
    """Two implementations of this question drift on exactly the details that
    matter, and Occam may not import the engine's (it uses `re`). So the law
    runs both. The test may import what the package may not."""
    from anvikshiki_v4.span_verification import diagnose
    assert classify(quote, source) == _ENGINE_TO_OCCAM[diagnose(quote, source)]


def test_the_agreement_cases_reach_every_verdict_classify_can_return():
    """Denominator for the law above: agreement over cases that all say `ok`
    would prove nothing."""
    seen = {classify(q, s) for q, s in _AGREEMENT_CASES}
    assert seen == {"ok", "markup", "punctuation", "absent"}
