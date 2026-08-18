# anvikshiki_v4/tests/test_status_breakdown.py
"""The explanation behind a rule's status, which the provenance panel renders.

A ceiling enforced internally and invisible externally is a guarantee nobody
benefits from. `status_of_rule` returns a meet and discards its arguments, so
a reader asking "why is this only PROVISIONAL?" cannot answer it from the
result — and that question is the entire point of showing provenance.

The property that needs guarding here is that the explanation and the enforced
number cannot drift. They come from one computation, and the test below breaks
if anyone reintroduces a second.
"""

from __future__ import annotations

from anvikshiki_v4.lattice import (
    BOUND_AUTHORED,
    BOUND_CITATION,
    BOUND_ORIGIN,
    CitationTier,
    status_breakdown,
    status_of_rule,
)
from anvikshiki_v4.schema_v4 import EpistemicStatus
from anvikshiki_v4.tests.test_citation_tier import _record, _rule


def test_the_breakdown_and_the_enforced_status_are_one_computation():
    """Two independent meets over the same three bounds would eventually
    disagree, and the panel would then explain a status the engine did not
    apply. `status_of_rule` delegates; this fails if it stops."""
    for rule in (
        _rule(extracted=False),
        _rule(provenance=[_record(quote="x" * 40, quote_found_in_source=True)]),
        _rule(provenance=[]),
        _rule(status="open"),
    ):
        assert status_of_rule(rule) is status_breakdown(rule).effective


def test_binding_names_every_bound_at_the_minimum_not_just_one():
    """Ties are the normal case, not an edge one.

    An extracted rule authored as established has origin and citation both
    holding it at the same rank. Naming one would imply that lifting it would
    raise the status, which is false while the other sits at the same level —
    the first real query run against this reported all three tied.
    """
    tied = _rule(provenance=[])   # extracted, no records

    breakdown = status_breakdown(tied)
    assert breakdown.effective is EpistemicStatus.PROVISIONAL
    # citation (unresolved → provisional) is the floor; origin is hypothesis.
    assert breakdown.binding == (BOUND_CITATION,)

    curated = _rule(extracted=False)
    curated_breakdown = status_breakdown(curated)
    assert curated_breakdown.effective is EpistemicStatus.ESTABLISHED
    # Authored established, origin uncapped, citation uncapped — all three.
    assert curated_breakdown.binding == (
        BOUND_AUTHORED, BOUND_ORIGIN, BOUND_CITATION
    )
    assert len(curated_breakdown.binding) > 1, (
        "a tie must report every tied bound; reporting one would claim "
        "lifting it alone would raise the status"
    )


def test_binding_is_never_empty():
    """Something is always at the minimum — it is a meet over three values.

    An empty tuple would render as "unbounded", which is the reading that
    flatters us and is never true of a rule.
    """
    for rule in (
        _rule(extracted=False),
        _rule(provenance=[]),
        _rule(status="contested"),
        _rule(provenance=[_record(
            quote="y" * 40, quote_found_in_source=False, quote_verdict="absent"
        )]),
    ):
        assert status_breakdown(rule).binding, (
            "no bound reported at the minimum of a three-way meet"
        )


def test_the_breakdown_reports_the_tier_it_used():
    """The panel shows the tier name beside the bound, and a tier computed
    twice can disagree with the one the ceiling came from."""
    verified = _rule(provenance=[_record(
        quote="a span long enough to discriminate between chapters",
        quote_found_in_source=True,
    )])

    breakdown = status_breakdown(verified)
    assert breakdown.citation_tier is CitationTier.ATTRIBUTED
    assert breakdown.citation_ceiling is EpistemicStatus.ESTABLISHED

    curated = status_breakdown(_rule(extracted=False))
    assert curated.citation_tier is CitationTier.CURATED
    assert curated.origin is None, (
        "absent metadata is the curated case; the compiler is what turns "
        "that into the word 'curated' for display"
    )
