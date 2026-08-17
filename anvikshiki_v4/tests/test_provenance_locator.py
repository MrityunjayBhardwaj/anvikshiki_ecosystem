# anvikshiki_v4/tests/test_provenance_locator.py
"""`Provenance` as a checkable citation rather than a description.

The model now carries two locator families — a guide-corpus position and a
fetched-document URL with a content hash — plus the span itself under the name
`quote`. What is asserted here is mostly about *absence being distinguishable*,
because that is where this model can go wrong quietly:

- a record locating nothing must not be constructible, which it became the
  moment `chapter_id` stopped being required
- a missing `retrieved_at` must stay missing rather than defaulting to now,
  since decay reads it and "nobody recorded this" is not "fresh"
- a malformed hash must fail on the way in, not sit in the field that later
  decides whether a quote can be re-checked

And one thing asserted about what this change does *not* do: nothing populates
`quote` yet, so these fields are a surface for a verification gate rather than
evidence of anything. The real extraction trace on disk is read here to keep
that honest.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from anvikshiki_v4.extraction_schema import Provenance, StageAOutput

REAL_TRACE = "traces/instrument_validation/stage_a_ch02.json"
DIGEST = "a" * 64


# ── The rename, and the old name still parsing ───────────────

def test_the_span_is_readable_under_its_new_name():
    assert Provenance(chapter_id="ch02", quote="Growth hides waste.").quote == (
        "Growth hides waste."
    )


def test_the_old_field_name_still_parses():
    """Backward compatibility is the point of the alias, not a nicety.

    Traces on disk were written with `sentence`. If they stop loading, the only
    record of what extraction has ever produced becomes unreadable.
    """
    assert Provenance(chapter_id="ch02", sentence="legacy").quote == "legacy"


def test_the_new_name_is_what_gets_written():
    """The alias is for reading. Serialisation should not keep the old name
    alive, or the rename never finishes and both spellings circulate."""
    dumped = Provenance(chapter_id="ch02", quote="x").model_dump()
    assert "quote" in dumped
    assert "sentence" not in dumped


def test_a_dumped_record_reparses():
    """Round-trip, so output is valid input — the property that makes the
    alias safe to rely on rather than a one-way door."""
    original = Provenance(
        chapter_id="ch02", section_header="Coordination", paragraph_index=3,
        doc_url="https://example.com/a", content_sha256=DIGEST,
        retrieved_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
        quote="Growth hides waste.", confidence=0.7,
    )
    assert Provenance.model_validate(original.model_dump()) == original


# ── A record must locate something ───────────────────────────

def test_a_provenance_with_no_locator_is_refused():
    """`chapter_id` was required, which enforced this by accident. Defaulting
    it for the document path opens the hole, so it is closed explicitly."""
    with pytest.raises(ValidationError, match="needs a locator"):
        Provenance(quote="a claim from nowhere")


def test_a_guide_locator_alone_is_enough():
    assert Provenance(chapter_id="ch02").chapter_id == "ch02"


def test_a_document_locator_alone_is_enough():
    """The case the old model could not express at all: a claim read from a
    fetched document, with no chapter to name."""
    prov = Provenance(doc_url="https://example.com/paper", quote="x")
    assert prov.doc_url == "https://example.com/paper"
    assert prov.chapter_id == ""


def test_both_locators_together_are_allowed():
    """Not an error. A guide chapter can also have a canonical URL, and
    refusing that would force a caller to drop one of two true facts."""
    prov = Provenance(chapter_id="ch02", doc_url="https://example.com/ch02")
    assert prov.chapter_id and prov.doc_url


def test_a_relative_url_is_refused():
    """A relative URL resolves against whatever happens to be fetching it,
    which means it locates a different document from a different caller."""
    with pytest.raises(ValidationError, match="absolute"):
        Provenance(doc_url="/papers/a.html")


# ── The hash ─────────────────────────────────────────────────

def test_an_absent_hash_is_allowed():
    """Empty means nobody hashed anything. That is a real state and must be
    representable — the alternative is callers inventing a value."""
    assert Provenance(chapter_id="ch02").content_sha256 == ""


def test_a_well_formed_hash_is_accepted_and_normalised():
    """Case-normalised so two records of the same bytes compare equal."""
    assert Provenance(
        chapter_id="ch02", content_sha256=DIGEST.upper()
    ).content_sha256 == DIGEST


@pytest.mark.parametrize("bad", [
    "TODO",
    "unknown",
    "a" * 63,
    "a" * 65,
    "g" * 64,
    "sha256:" + "a" * 64,
])
def test_a_malformed_hash_is_refused(bad):
    """Every one of these is a plausible placeholder, and each would sit in the
    field that decides whether a quote can be re-verified."""
    with pytest.raises(ValidationError, match="64 hex characters"):
        Provenance(chapter_id="ch02", content_sha256=bad)


# ── The timestamp must not fabricate freshness ───────────────

def test_retrieved_at_defaults_to_absent_not_to_now():
    """The failure this prevents, stated as a test.

    A timestamp defaulted to construction time would make every record look
    freshly fetched, including ones nobody fetched. Decay reads this field, so
    the default would raise confidence rather than lower it — absence failing
    toward strength, which is this codebase's recurring shape.
    """
    assert Provenance(chapter_id="ch02").retrieved_at is None


def test_two_records_built_apart_do_not_disagree_about_when():
    """Guards the same thing from the other side: if a default were ever
    introduced as `default_factory=datetime.now`, this would start failing."""
    first = Provenance(chapter_id="ch02")
    second = Provenance(chapter_id="ch02")
    assert first.retrieved_at == second.retrieved_at is None


def test_an_explicit_timestamp_survives():
    when = datetime(2026, 8, 17, 12, 30, tzinfo=timezone.utc)
    assert Provenance(
        chapter_id="ch02", doc_url="https://example.com/a", retrieved_at=when
    ).retrieved_at == when


# ── The real trace, and what it says about the span ──────────

def test_the_real_extraction_trace_still_parses():
    """Read the run on disk, not a fixture.

    This is the only record of what extraction has actually produced, it was
    written under the old field name, and a rename that breaks it would be a
    silent loss — the file would simply stop being loadable by the code that
    wrote it.
    """
    import json

    raw = json.load(open(REAL_TRACE))
    out = StageAOutput.model_validate(raw)
    assert len(out.candidates) == 24, (
        "the trace changed shape; the count is asserted so this test cannot "
        "pass by validating an empty candidate list"
    )
    assert all(c.provenance.chapter_id == "ch02" for c in out.candidates)


def test_the_real_trace_carries_no_spans_at_all():
    """The honest current state, asserted so the next change has to face it.

    Adding locator fields does not add evidence. Extraction is never asked for
    a quote, so all 24 candidates in the only real run have an empty span —
    which means a verification gate over these fields would have nothing to
    check and would drop everything it saw.

    When extraction starts quoting, this test is the one that should fail, and
    the docstring on `Provenance` should stop saying nothing populates `quote`.
    """
    import json

    out = StageAOutput.model_validate(json.load(open(REAL_TRACE)))
    with_spans = [c for c in out.candidates if c.provenance.quote.strip()]
    assert len(out.candidates) == 24
    assert with_spans == [], (
        f"{len(with_spans)} candidate(s) now carry a span — extraction has "
        f"started quoting, so update Provenance's docstring and the "
        f"verification gate's assumptions"
    )
