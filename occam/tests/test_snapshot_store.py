"""A snapshot is addressed by its bytes, and its text by its own hash (#137).

Everything the pipeline concludes resolves back to a snapshot, so the laws here
are about identity and about absence — the two things that, if wrong, are
unrecoverable later. A span pointing at a snapshot whose address was asserted
rather than computed cannot be checked by anyone holding it, and a document we
could not read, stored as a document that said nothing, produces a confident
answer from silence.

Nothing here touches the network. `capture` takes the bytes it is given, so a
fetch is injected as data and these laws are portable — unlike the trace
fixtures in #114, there is nothing outside the repo for them to depend on.
"""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from occam.snapshot import (
    Snapshot,
    SnapshotStore,
    body_address,
    capture,
    text_address,
)

T0 = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)


def _cap(url="https://example.com/a", body=b"<p>Growth helps</p>",
         text="Growth helps", at=T0, **kw):
    return capture(url=url, body=body, text=text, fetched_at=at,
                   extractor="test-extractor/1", **kw)


# ── identity ────────────────────────────────────────────────

def test_the_id_is_the_hash_of_the_body():
    s = _cap()
    assert s.id == body_address(s.body)
    assert s.id.startswith("sha256:")


def test_an_asserted_id_is_refused():
    """The address must be computed, not claimed. A snapshot whose id was
    assigned cannot be verified by a third party, which is the only reason the
    id exists."""
    with pytest.raises(ValidationError, match="content address"):
        Snapshot(
            id="sha256:" + "0" * 64,
            urls=("https://example.com/a",),
            fetched_at=T0,
            body=b"real bytes",
            text="real text",
            text_sha256=text_address("real text"),
        )


def test_the_text_hash_is_separate_from_the_id():
    """The load-bearing distinction. Same bytes, two extractions: the id is
    unchanged and the text hash is not, which is exactly the case a single
    hash cannot express."""
    body = b"<p><em>Growth</em> helps</p>"
    loose = _cap(body=body, text="Growth helps")
    tight = _cap(body=body, text="*Growth* helps")

    assert loose.id == tight.id, "same bytes must have the same address"
    assert loose.text_sha256 != tight.text_sha256, (
        "two extractions of one body must be distinguishable, or every offset "
        "stored against the first silently points at the second"
    )


def test_a_text_hash_that_does_not_hash_the_text_is_refused():
    with pytest.raises(ValidationError, match="text_sha256"):
        Snapshot(
            id=body_address(b"b"), urls=("https://e.com",), fetched_at=T0,
            body=b"b", text="hello", text_sha256=text_address("something else"),
        )


def test_a_snapshot_records_what_extracted_it():
    """Knowing the extraction changed is only actionable beside what it
    changed to."""
    assert _cap().extractor == "test-extractor/1"


def test_a_snapshot_with_no_url_is_refused():
    with pytest.raises(ValidationError, match="no URL"):
        Snapshot(
            id=body_address(b"b"), urls=(), fetched_at=T0,
            body=b"b", text="t", text_sha256=text_address("t"),
        )


def test_a_snapshot_is_frozen():
    """Mutating stored bytes would break the address silently."""
    s = _cap()
    with pytest.raises(ValidationError):
        s.text = "something else"


# ── absence is recorded, never swallowed ────────────────────

def test_empty_text_without_a_reason_is_refused():
    """The law this module exists for. 'Could not look' and 'nothing found'
    call for opposite actions, and after the fact they are indistinguishable."""
    with pytest.raises(ValidationError, match="empty text with no reason"):
        _cap(text="")


def test_empty_text_with_a_reason_is_accepted_and_kept():
    s = _cap(text="", empty_reason="paywalled: HTTP 402")
    assert s.text == ""
    assert "402" in s.empty_reason


def test_the_four_unreadable_reasons_stay_distinct():
    """Each of these is a different finding for the reader, and a bare empty
    string erases the difference between all four."""
    store = SnapshotStore()
    reasons = [
        "paywalled: HTTP 402",
        "robots.txt disallows /docs/",
        "PDF has no text layer",
        "fetch failed: ConnectionError",
    ]
    for i, why in enumerate(reasons):
        store.put(_cap(url=f"https://e.com/{i}", body=f"b{i}".encode(),
                       text="", empty_reason=why))

    held = {s.empty_reason for s in store.unreadable()}
    assert held == set(reasons), "a reason was lost or collapsed"
    assert len(store.readable()) == 0
    assert len(store.unreadable()) == 4, "measured over 4 stored snapshots"


def test_text_present_and_a_reason_set_is_refused():
    """Both filled means one is wrong, and a reader cannot tell which."""
    with pytest.raises(ValidationError, match="empty_reason is set"):
        _cap(text="real text", empty_reason="paywalled")


# ── storage and source counting ─────────────────────────────

def test_put_then_get_returns_byte_identical_bytes():
    store = SnapshotStore()
    s = store.put(_cap())
    back = store.get(s.id)
    assert back is not None
    assert back.body == s.body
    assert back.text == s.text


def test_the_same_bytes_from_a_second_url_merge_rather_than_duplicate():
    store = SnapshotStore()
    store.put(_cap(url="https://a.example/x"))
    merged = store.put(_cap(url="https://b.example/y"))

    assert len(store) == 1, "same bytes must be one snapshot"
    assert merged.urls == ("https://a.example/x", "https://b.example/y"), (
        "the second address must be kept — discarding it makes two sightings "
        "of one document look like two sources"
    )


def test_merging_keeps_the_first_fetch_time():
    """The earlier read is when this content was witnessed. Overwriting it
    would make a stale document look fresh to the decay factor."""
    store = SnapshotStore()
    store.put(_cap(url="https://a.example/x", at=T0))
    later = store.put(_cap(url="https://b.example/y", at=T0 + timedelta(days=200)))
    assert later.fetched_at == T0


def test_sources_are_counted_by_text_not_by_body():
    """Two servers, different bytes, identical extracted text. Two snapshots,
    ONE source — counting bodies would report corroboration that does not
    exist."""
    store = SnapshotStore()
    store.put(_cap(url="https://a.example/x", body=b"<p>Growth helps</p><!--ad A-->",
                   text="Growth helps"))
    store.put(_cap(url="https://b.example/y", body=b"<p>Growth helps</p><!--ad B-->",
                   text="Growth helps"))

    assert len(store) == 2, "different bytes are different snapshots"
    assert store.distinct_sources() == 1, (
        "identical extracted text is one source; len(store) is the wrong "
        "denominator for independence"
    )
    assert len(store.ids_for_text(text_address("Growth helps"))) == 2


def test_distinct_sources_counts_up_with_genuinely_different_text():
    store = SnapshotStore()
    for i in range(3):
        store.put(_cap(url=f"https://e.com/{i}", body=f"b{i}".encode(),
                       text=f"claim number {i}"))
    assert len(store) == 3
    assert store.distinct_sources() == 3, "measured over 3 stored snapshots"


def test_readable_and_unreadable_partition_the_store():
    """Every count with its denominator: the two must sum to the total, or one
    of them is quietly dropping records."""
    store = SnapshotStore()
    store.put(_cap(url="https://e.com/1", body=b"1", text="has text"))
    store.put(_cap(url="https://e.com/2", body=b"2", text="",
                   empty_reason="fetch failed: timeout"))
    assert len(store.readable()) + len(store.unreadable()) == len(store) == 2


def test_membership_is_by_address():
    store = SnapshotStore()
    s = store.put(_cap())
    assert s.id in store
    assert "sha256:" + "f" * 64 not in store
