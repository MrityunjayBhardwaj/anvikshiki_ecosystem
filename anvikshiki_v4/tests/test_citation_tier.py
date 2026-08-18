# anvikshiki_v4/tests/test_citation_tier.py
"""The citation axis: how well a rule's source has been checked, as a ceiling.

Three properties matter more than the mapping itself, and each has cost
something in this tree before.

**Missing machinery must never read as evidence against a source.** Identifier
resolution does not exist yet. The tier that justifies deleting a rule is the
one meaning "we went to the source and the words were not there", and if
"we have no resolver" collapses into that, every rule in the knowledge base is
fabricated and gets dropped. The scan for this is mutation-checked below: the
resolver is pointed at nothing and no rule may tier FABRICATED.

**A by-design absence is not a deficiency.** Hand-authored rules carry no
provenance records on purpose — the schema says so where the field is
defined — because they cite literature rather than a located span. Reading
that as an unchecked citation caps the entire shipped knowledge base at
PROVISIONAL, which two tests in `test_origin_ceiling.py` already existed to
prevent.

**A tier is shown to a reader, so it may not lie to obtain a ceiling.** The
curated case needs an uncapped ceiling, and the quickest way to get one is to
call those rules ATTRIBUTED. That would assert in the provenance panel that a
span was found in a source nobody checked. `CURATED` exists so the ceiling can
be right without the label being false.
"""

from __future__ import annotations

import pytest

from anvikshiki_v4.lattice import (
    CitationTier,
    ceiling_for_citation,
    rank,
    should_drop_for_citation,
    status_of_rule,
    tier_for_citation,
)
from anvikshiki_v4.schema import (
    AugmentationMetadata,
    AugmentationOrigin,
    CausalStatus,
    Confidence,
    EpistemicStatus as KBEpistemicStatus,
    Provenance,
    Vyapti,
)
from anvikshiki_v4.schema_v4 import EpistemicStatus

_LONG = "a span long enough to discriminate between two chapters"


def _rule(*, provenance=None, extracted=True, status="established") -> Vyapti:
    """A rule with a citation, built the same way `test_origin_ceiling` builds
    one — every required field passed explicitly.

    Confidence is 1.0 for the reason that file gives: a ceiling must bind
    regardless of how confident the generator claimed to be, and a modest
    fixture would leave that untested.
    """
    metadata = None
    if extracted:
        metadata = AugmentationMetadata(origin=AugmentationOrigin.GUIDE_EXTRACTED)
    return Vyapti(
        id="V01",
        name="a_rule",
        statement="p implies q",
        causal_status=CausalStatus.EMPIRICAL,
        confidence=Confidence(
            existence=1.0, formulation=1.0, evidence="theoretical"
        ),
        epistemic_status=KBEpistemicStatus(status),
        antecedents=["p"],
        consequent="q",
        provenance=list(provenance or []),
        augmentation_metadata=metadata,
    )


def _record(**kwargs) -> Provenance:
    kwargs.setdefault("chapter_id", "ch02")
    return Provenance(**kwargs)


# ── the safety property ──────────────────────────────────────

def test_no_resolver_never_produces_a_fabricated_tier():
    """The property that keeps a missing component from deleting the KB.

    Resolution is unbuilt, so every locator's reachability is None. None must
    reach UNRESOLVED, never FABRICATED — the tier that authorises a drop.
    """
    unchecked = _rule(provenance=[_record(quote=_LONG)])

    assert tier_for_citation(unchecked) is CitationTier.UNRESOLVED
    assert should_drop_for_citation(unchecked) is False


def test_an_unreachable_locator_still_does_not_authorise_a_drop(monkeypatch):
    """Mutation-check of the property above, rather than a restatement of it.

    The previous test passes because reachability is None everywhere today —
    which it would also do if the mapping from False were wrong, since
    nothing currently returns False. So force a resolver that answers "no" to
    everything and confirm the drop still does not fire.

    #19 maps "identifier does not resolve" straight to FABRICATED and thence
    to a drop. That is deliberately not implemented: a locator can fail to
    resolve because it was invented, because a registry is down, or because
    the document was withdrawn, and only the first is evidence against the
    claim. A span checked against its source and found missing is evidence;
    an unreachable URL is an absence of evidence.
    """
    import anvikshiki_v4.lattice as lattice

    monkeypatch.setattr(lattice, "_record_is_reachable", lambda record: False)

    rule = _rule(provenance=[_record(quote=_LONG)])

    assert lattice.tier_for_citation(rule) is CitationTier.UNRESOLVED
    assert lattice.should_drop_for_citation(rule) is False


def test_the_mutation_check_can_actually_fail(monkeypatch):
    """Proves the harness above is wired to the thing it claims to test.

    A monkeypatch that silently missed its target would leave the previous
    test passing for the wrong reason — the scan believed rather than
    verified, which is how two defects reached the measuring tools already.
    Patch reachability to the value that *should* change the answer and
    confirm the answer changes.
    """
    import anvikshiki_v4.lattice as lattice

    rule = _rule(provenance=[_record(quote=_LONG)])
    assert lattice.tier_for_citation(rule) is CitationTier.UNRESOLVED

    monkeypatch.setattr(lattice, "_record_is_reachable", lambda record: True)

    assert lattice.tier_for_citation(rule) is CitationTier.EXISTS


def test_the_whole_shipped_knowledge_base_survives_the_tier():
    """The blast-radius check, over the real KB rather than a fixture.

    Asserts its own denominator: a scan that silently matched no rules would
    otherwise pass by examining nothing, which is the same defect one level up.
    """
    from pathlib import Path

    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

    root = Path(__file__).resolve().parent.parent
    ks = load_knowledge_store(root / "data" / "business_expert.yaml")
    rules = list(ks.vyaptis.values())

    assert len(rules) >= 10, (
        f"expected the business KB to hold rules; found {len(rules)}. A zero "
        "here would let every assertion below pass by iterating nothing."
    )
    dropped = [v for v in rules if should_drop_for_citation(v)]
    assert dropped == [], (
        f"{len(dropped)} of {len(rules)} curated rules would be deleted by "
        "the citation axis"
    )
    assert all(
        tier_for_citation(v) is CitationTier.CURATED for v in rules
    ), "a hand-authored rule tiered as though it had made a span claim"


def test_a_curated_rule_is_not_labelled_attributed():
    """The ceiling is right for a different reason than ATTRIBUTED's.

    Both give ESTABLISHED, so nothing downstream would notice — except the
    provenance panel, which shows the tier to a person and would be claiming
    a verification that never happened.
    """
    curated = _rule(extracted=False)

    assert tier_for_citation(curated) is CitationTier.CURATED
    assert tier_for_citation(curated) is not CitationTier.ATTRIBUTED
    assert ceiling_for_citation(curated) is EpistemicStatus.ESTABLISHED
    assert status_of_rule(curated) is EpistemicStatus.ESTABLISHED


# ── the mapping ──────────────────────────────────────────────

@pytest.mark.parametrize("provenance, extracted, expected", [
    ([], False, CitationTier.CURATED),
    ([], True, CitationTier.UNRESOLVED),
    ([{"quote": _LONG, "quote_found_in_source": True}], True,
     CitationTier.ATTRIBUTED),
    ([{"quote": _LONG, "quote_found_in_source": False,
       "quote_verdict": "absent"}], True, CitationTier.FABRICATED),
    ([{"quote": _LONG, "quote_found_in_source": None}], True,
     CitationTier.UNRESOLVED),
    ([{"quote": "too short", "quote_found_in_source": True}], True,
     CitationTier.UNRESOLVED),
    # Formatting only: the words are identical, the asterisks are not.
    ([{"quote": _LONG, "quote_found_in_source": False,
       "quote_verdict": "markup"}], True, CitationTier.ATTRIBUTED),
    # Failed the strict check with no reason recorded — an old record. Not
    # evidence against the source, so not grounds to delete.
    ([{"quote": _LONG, "quote_found_in_source": False}], True,
     CitationTier.UNRESOLVED),
])
def test_each_tier_is_reachable(provenance, extracted, expected):
    """Every tier reached by an input. A tier the code can produce but
    nothing reaches is a claim about behaviour that nothing verifies."""
    rule = _rule(
        provenance=[_record(**p) for p in provenance], extracted=extracted
    )
    assert tier_for_citation(rule) is expected


def test_a_span_too_short_to_discriminate_does_not_reach_attributed():
    """Found and usable are different questions, and ATTRIBUTED claims the
    second. `economics.` is genuinely in the chapter and proves nothing."""
    rule = _rule(provenance=[
        _record(quote="economics.", quote_found_in_source=True)
    ])

    assert tier_for_citation(rule) is not CitationTier.ATTRIBUTED
    assert tier_for_citation(rule) is CitationTier.UNRESOLVED


def test_never_checked_and_checked_and_missing_are_different_tiers():
    """The distinction the whole three-state flag exists for. Collapsing them
    would report every unchecked citation as a fabrication."""
    never = _rule(provenance=[_record(quote=_LONG, quote_found_in_source=None)])
    missing = _rule(provenance=[_record(
        quote=_LONG, quote_found_in_source=False, quote_verdict="absent"
    )])

    assert tier_for_citation(never) is CitationTier.UNRESOLVED
    assert tier_for_citation(missing) is CitationTier.FABRICATED
    assert should_drop_for_citation(never) is False
    assert should_drop_for_citation(missing) is True


def test_dropped_markdown_does_not_read_as_a_fabricated_citation():
    """The defect the real trace caught, kept as a regression.

    `quote_found_in_source` is False for a markup miss, because the quote is
    genuinely not verbatim. It is the same False an invented sentence
    produces, and the first version of this tier read it as grounds to delete
    — which removed the central claim of ch02, correctly quoted, over a pair
    of asterisks the model did not reproduce.
    """
    markup = _rule(provenance=[_record(
        quote=_LONG, quote_found_in_source=False, quote_verdict="markup"
    )])

    assert tier_for_citation(markup) is CitationTier.ATTRIBUTED
    assert should_drop_for_citation(markup) is False


def test_a_failed_check_with_no_recorded_reason_is_not_a_fabrication():
    """A record written before the verdict field existed carries no reason.

    Without one, a dropped asterisk and an invented sentence are the same
    value, and the tier that authorises deletion must not fire on that
    ambiguity. Unknown resolves to UNRESOLVED, never FABRICATED.
    """
    old = _rule(provenance=[_record(
        quote=_LONG, quote_found_in_source=False, quote_verdict=""
    )])

    assert tier_for_citation(old) is CitationTier.UNRESOLVED
    assert should_drop_for_citation(old) is False


def test_the_best_record_decides_not_the_worst():
    """Opposite discipline to `meet`, deliberately. Chaining through a weak
    step weakens a conclusion; citing an extra weak source alongside a
    verified one does not weaken the verified one."""
    rule = _rule(provenance=[
        _record(quote="", quote_found_in_source=None),
        _record(quote=_LONG, quote_found_in_source=True),
    ])

    assert tier_for_citation(rule) is CitationTier.ATTRIBUTED


# ── the ceiling ──────────────────────────────────────────────

def test_the_ceiling_only_ever_lowers():
    """A ceiling, not an assignment. A rule authored weak stays weak however
    well it is cited."""
    well_cited_but_open = _rule(
        provenance=[_record(quote=_LONG, quote_found_in_source=True)],
        status="open",
    )

    assert tier_for_citation(well_cited_but_open) is CitationTier.ATTRIBUTED
    assert status_of_rule(well_cited_but_open) is EpistemicStatus.OPEN


def test_a_fabricated_citation_sinks_the_rule_to_the_bottom():
    fabricated = _rule(provenance=[_record(
        quote=_LONG, quote_found_in_source=False, quote_verdict="absent"
    )])

    assert ceiling_for_citation(fabricated) is EpistemicStatus.CONTESTED
    assert status_of_rule(fabricated) is EpistemicStatus.CONTESTED


def test_every_tier_has_an_explicit_ceiling():
    """No default. An unmapped tier must raise rather than inherit whatever
    the fallback happened to be — the same discipline the origin ceiling
    keeps, and for the same reason."""
    from anvikshiki_v4.lattice import _CITATION_CEILING

    missing = [t for t in CitationTier if t not in _CITATION_CEILING]
    assert missing == [], f"tiers with no ceiling: {missing}"
    assert len(_CITATION_CEILING) == len(CitationTier)


def test_the_citation_bound_composes_with_the_origin_bound():
    """Both apply at once and the weaker wins, which is what makes adding a
    bound safe: no caller has to remember to apply it."""
    extracted_and_verified = _rule(
        provenance=[_record(quote=_LONG, quote_found_in_source=True)]
    )

    # Citation says ESTABLISHED, origin says HYPOTHESIS for guide extraction.
    assert ceiling_for_citation(extracted_and_verified) is (
        EpistemicStatus.ESTABLISHED
    )
    assert status_of_rule(extracted_and_verified) is EpistemicStatus.HYPOTHESIS
    assert rank(status_of_rule(extracted_and_verified)) < rank(
        EpistemicStatus.ESTABLISHED
    )
