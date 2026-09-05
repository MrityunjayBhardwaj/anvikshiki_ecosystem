# tests/test_span_gate_drops_unverified.py
"""A predicate whose quotation cannot be verified is dropped, not downgraded.

#18: "A predicate can carry a fabricated quotation and pass every validation
we have." That was exactly true, and the reason is worth stating precisely,
because the check was not missing — it was connected to the wrong thing.

`diagnose` already ran on every candidate at extraction and recorded a
verdict. What the verdict controlled was this:

    statement=(candidate.provenance.quote
               if (quote_found_in_source and is_discriminating(quote))
               else candidate.description)

A failing quote meant the rule's statement came from the model's own
description instead. The predicate was admitted either way. So a fabricated
citation and an honest paraphrase were indistinguishable at every later
stage, and `quote_appears_in` — the actual verbatim test this module has
shipped for weeks — appeared nowhere in the live path at all, only in the
measurement script and in tests.

The gate runs FIRST in validation, before cycle detection, so a predicate we
are not admitting cannot also generate a finding about the graph it was never
going to join.
"""

import pytest

from anvikshiki_v4.extraction_schema import (
    Provenance,
    ProposedVyapti,
    StageDOutput,
)
from anvikshiki_v4.predicate_extraction import (
    SPAN_DROP_DEGRADED_AT,
    StageEValidator,
)
from anvikshiki_v4.schema import DomainType, KnowledgeStore

GOOD_QUOTE = "Unit economics turn positive only after retention stabilises."
SHORT_QUOTE = "Burn rate doubled."          # 18 chars, under the threshold


def _prov(**kw):
    base = dict(chapter_id="ch02", quote=GOOD_QUOTE, quote_found_in_source=True)
    base.update(kw)
    return Provenance(**base)


def _proposed(vid="V90", provenance=None, **kw):
    base = dict(
        id=vid, name="a rule", statement="s",
        antecedents=["churn_rising"], consequent=f"consequent_{vid}",
    )
    base.update(kw)
    if provenance is not None:
        base["provenance"] = provenance
        base["provenance_attached"] = True
    return ProposedVyapti(**base)


def _run(*proposals):
    v = StageEValidator(KnowledgeStore(domain_type=DomainType.CRAFT))
    ks, errors = v.validate_and_merge(StageDOutput(new_vyaptis=list(proposals)))
    return ks, errors


# ── The gate ──

class TestUnverifiedSpansAreDropped:

    def test_a_verified_span_survives(self):
        ks, errors = _run(_proposed(provenance=[_prov()]))
        assert "V90" in ks.vyaptis
        assert errors.span_dropped == []

    def test_a_quote_not_found_in_the_source_is_dropped(self):
        """The case #18 exists for. Before this the rule was admitted with the
        model's description standing in for the quote."""
        ks, errors = _run(
            _proposed(provenance=[_prov(quote_found_in_source=False)])
        )
        assert "V90" not in ks.vyaptis
        assert errors.span_dropped == ["V90"]

    def test_a_quote_too_short_to_discriminate_is_dropped(self):
        """`"economics."` really does occur in the chapter, so "found" is the
        honest verdict — and it is still useless as a citation. Found and
        usable are different questions."""
        ks, errors = _run(_proposed(provenance=[_prov(quote=SHORT_QUOTE)]))
        assert "V90" not in ks.vyaptis
        assert errors.span_dropped == ["V90"]

    def test_an_empty_quote_is_dropped(self):
        ks, errors = _run(_proposed(provenance=[_prov(quote="   ")]))
        assert "V90" not in ks.vyaptis

    def test_one_good_provenance_entry_is_enough(self):
        """A rule that cites widely should not be punished for one bad
        citation among several."""
        ks, errors = _run(_proposed(provenance=[
            _prov(quote=SHORT_QUOTE),
            _prov(quote_found_in_source=False),
            _prov(),
        ]))
        assert "V90" in ks.vyaptis
        assert errors.span_dropped == []


class TestWhatCountsAsALocator:
    """The regression this class exists to prevent is one I shipped into a
    test run and only the suite caught.

    The first version of check 3 asked for `doc_url` or `content_sha256` —
    the locators a WEB-SOURCED document carries. Neither is set anywhere in
    production; both are fields waiting on the content-addressed snapshot
    store (#27). The corpus we extract from is the guide, and it locates a
    span by chapter and paragraph.

    So the gate would have dropped EVERY predicate the pipeline has ever
    produced, and reported it as a 100% drop rate — which reads as "the
    extractor fabricates everything" rather than "the check named the wrong
    fields". A check quantified over the wrong set, presenting as a fact
    about the input.
    """

    def test_chapter_id_alone_is_a_locator(self):
        """What the guide corpus actually carries today."""
        ks, _ = _run(_proposed(provenance=[_prov(chapter_id="ch02")]))
        assert "V90" in ks.vyaptis

    def test_the_web_locator_counts_too(self):
        """#27's snapshot store will populate `doc_url`. The gate must not
        have to be edited again when it does."""
        ks, _ = _run(_proposed(provenance=[
            _prov(chapter_id="", doc_url="https://example.org/paper.pdf")
        ]))
        assert "V90" in ks.vyaptis

    def test_the_schema_itself_refuses_a_provenance_with_no_locator(self):
        """So the gate's third check is a BACKSTOP that cannot currently
        fire, and this test is why that is deliberate rather than an
        unreachable branch nobody noticed.

        `Provenance` will not construct without a locator, which means a
        locator-less span cannot reach validation to be dropped. Keeping the
        check costs nothing and survives the schema relaxing; deleting it
        would make the gate silently weaker the day that happened. If this
        test fails, the schema stopped enforcing it and the gate's check just
        became load-bearing.
        """
        with pytest.raises(ValueError, match="locator"):
            Provenance(quote=GOOD_QUOTE, quote_found_in_source=True)


class TestUnsourcedIsADifferentFailure:

    def test_a_proposal_with_no_provenance_is_counted_not_dropped(self):
        """An unsourced proposal is not a fabricated one, and dropping it is
        a policy change #18 does not ask for. It is reported so that the
        decision gets taken deliberately rather than by my default."""
        ks, errors = _run(_proposed())
        assert "V90" in ks.vyaptis
        assert errors.span_unsourced == ["V90"]
        assert errors.span_dropped == []

    def test_unsourced_proposals_are_not_in_the_denominator(self):
        """A drop rate computed over proposals the gate cannot judge would
        move when the unsourced count moved, which is the wrong reference
        set — the rate is about quotes that were checked."""
        _, errors = _run(_proposed("V90"), _proposed("V91", provenance=[_prov()]))
        assert errors.span_checked == 1
        assert errors.span_drop_rate == 0.0


class TestTheRateIsReportedWithItsDenominator:

    def test_drop_rate_carries_its_denominator(self):
        _, errors = _run(
            _proposed("V90", provenance=[_prov(quote_found_in_source=False)]),
            _proposed("V91", provenance=[_prov()]),
            _proposed("V92", provenance=[_prov()]),
            _proposed("V93", provenance=[_prov()]),
        )
        assert errors.span_checked == 4
        assert errors.span_dropped == ["V90"]
        assert errors.span_drop_rate == 0.25

    def test_a_clean_run_is_not_degraded(self):
        _, errors = _run(_proposed(provenance=[_prov()]))
        assert errors.span_degraded is False

    def test_a_run_above_the_threshold_is_flagged_degraded(self):
        """Half the proposals unverifiable is the extractor quoting badly,
        not the source being bad, and the run should say so."""
        _, errors = _run(
            _proposed("V90", provenance=[_prov(quote_found_in_source=False)]),
            _proposed("V91", provenance=[_prov()]),
        )
        assert errors.span_drop_rate == 0.5 > SPAN_DROP_DEGRADED_AT
        assert errors.span_degraded is True

    def test_the_threshold_is_a_named_constant(self):
        """It is permitted, not validated. The only measurement behind it is
        the verbatim rate — 22 of 24, 0 fabricated — and a 24-quote sample
        cannot calibrate a threshold. Named so moving it is one edit rather
        than an archaeology exercise."""
        assert 0.0 < SPAN_DROP_DEGRADED_AT < 1.0


class TestFabricationIsSeparableFromFormatting:
    """`span_verification` is explicit that a markup difference "is not
    verbatim and is not accepted — but it is also not an invented sentence,
    and calling it `absent` puts a formatting artefact into the fabrication
    number." A single drop rate does exactly that, so the reason is recorded
    alongside the id.

    This is not hypothetical. Replaying the gate over the real ch02 Stage D
    output (`traces/extraction_ch02/stage_d_ch02.json`, 15 proposals, no
    model calls) drops exactly one — and its verdict is `markup`, not
    `absent`. Reported as one number the run looks 6.7% unreliable; reported
    honestly the fabrication rate is 0 of 15, which agrees with the
    independently measured verbatim rate of 22/24 with 0 fabricated.
    """

    def test_the_drop_reason_is_recorded(self):
        _, errors = _run(_proposed(provenance=[
            _prov(quote_found_in_source=False, quote_verdict="markup")
        ]))
        assert errors.span_drop_reasons == {"markup": ["V90"]}

    def test_absent_is_the_verdict_that_means_fabrication(self):
        _, errors = _run(
            _proposed("V90", provenance=[
                _prov(quote_found_in_source=False, quote_verdict="absent")]),
            _proposed("V91", provenance=[
                _prov(quote_found_in_source=False, quote_verdict="markup")]),
        )
        assert errors.span_drop_reasons["absent"] == ["V90"]
        assert errors.span_drop_reasons["markup"] == ["V91"]
        # The number worth quoting is the first, not their sum.
        assert len(errors.span_dropped) == 2

    def test_a_drop_with_no_verdict_is_still_given_a_reason(self):
        """Silence is not a category. An unlabelled drop would be invisible
        in any breakdown and would quietly deflate every named reason."""
        _, errors = _run(_proposed(provenance=[
            _prov(quote=SHORT_QUOTE, quote_verdict="")
        ]))
        assert errors.span_drop_reasons == {"unverified": ["V90"]}


class TestTheGateRunsBeforeTheGraphChecks:

    def test_a_dropped_predicate_raises_no_orphan_warning(self):
        """Ordering, asserted rather than assumed. A finding about a
        predicate we are not admitting is noise, and it would send someone
        looking at a graph the predicate was never going to join."""
        _, errors = _run(_proposed(
            provenance=[_prov(quote_found_in_source=False)],
            antecedents=["a_predicate_nothing_concludes"],
        ))
        assert errors.span_dropped == ["V90"]
        assert "a_predicate_nothing_concludes" not in errors.orphan_predicates


class TestValidationStillReportsItRan:

    def test_ran_is_true_even_when_everything_was_dropped(self):
        """`ran` exists because an empty error list meant two things. A run
        that dropped every proposal still validated, and must not read as a
        run that never happened."""
        ks, errors = _run(_proposed(provenance=[_prov(quote_found_in_source=False)]))
        assert errors.ran is True
        assert ks.vyaptis == {}
