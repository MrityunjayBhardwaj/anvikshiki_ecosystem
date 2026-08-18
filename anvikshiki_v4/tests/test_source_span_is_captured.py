# anvikshiki_v4/tests/test_source_span_is_captured.py
"""Extraction is asked for the span, and told when it did not give one.

Before this, `Provenance.sentence` was described as "the exact sentence
containing the claim" and nothing ever wrote to it: the signature had no output
field for it and the construction site did not set it. The only recorded run has
24 candidates with an empty span in all 24. So a verification gate over that
field would have dropped every predicate and reported it as a fabrication rate.

Three outcomes are separated here, and keeping them apart is most of the point:

    no quote given          the model declined to cite
    quote not in section    the model cited something that is not there
    quote in section        a citation that can be checked

Only the second is evidence of fabrication. A single counter covering the first
two would blame the model for a prompt it was never given, which is the same
mistake as counting a truncated answer as an empty section — twice fixed in this
same file already.

The verdict is deliberately strict, and the *reason* is recorded alongside it.
A model that types `’` for `'` produces a span that is not verbatim and must be
refused; but a run reporting "40% not found" reads as fabrication when it may be
typography, so `punctuation` and `absent` are different findings.

Nothing here calls a model.
"""

import json
from types import SimpleNamespace

import pytest

from anvikshiki_v4.extraction_schema import ExtractionConfig, StageAOutput
from anvikshiki_v4.schema import DomainType, KnowledgeStore
from anvikshiki_v4.span_verification import (
    MIN_DISCRIMINATING_LENGTH,
    diagnose,
    fold_punctuation,
    is_discriminating,
    normalise_whitespace,
    quote_appears_in,
    strip_markup,
)

SOURCE = (
    "### Growth and unit economics\n"
    "A startup's growth rate -- however fast -- cannot fix negative unit\n"
    "economics. Growth multiplies whatever unit economics you already have.\n"
    "**The fundamental inequality:** viability holds if and only if "
    "**LTV > CAC** at the unit level.\n"
)


# ── What counts as verbatim ──────────────────────────────────

def test_a_quote_broken_across_lines_still_matches():
    """The section handed to the model has hard line breaks mid-sentence.

    Treating a newline as different from a space would fail almost every
    true quote, which is why whitespace is the one thing normalised.
    """
    assert quote_appears_in(
        "cannot fix negative unit economics.", SOURCE
    )
    assert quote_appears_in(
        "growth rate -- however fast -- cannot fix negative unit economics.",
        SOURCE,
    )


def test_case_is_not_normalised():
    """Verbatim means verbatim. Every loosening of a match rule in this
    package has cost more than it bought."""
    assert not quote_appears_in(
        "a startup's growth rate", SOURCE
    )


def test_an_invented_sentence_is_not_found():
    assert not quote_appears_in(
        "Growth can always outrun bad unit economics.", SOURCE
    )


def test_one_changed_word_is_not_found():
    """The check has to be sharp enough to catch a near-miss, or it is
    measuring nothing."""
    assert not quote_appears_in(
        "A startup's growth rate -- however slow -- cannot fix negative "
        "unit economics.",
        SOURCE,
    )


def test_an_empty_quote_is_not_found_rather_than_an_error():
    """The caller has to distinguish 'gave no quote' from 'gave a bad one',
    so this returns False and lets `diagnose` say which."""
    assert quote_appears_in("", SOURCE) is False
    assert quote_appears_in("   \n ", SOURCE) is False


# ── Why a quote was not found ────────────────────────────────

@pytest.mark.parametrize("quote, expected", [
    ("Growth multiplies whatever unit economics you already have.", ""),
    ("", "empty"),
    ("   ", "empty"),
    ("Growth can always outrun bad unit economics.", "absent"),
    ("A startup’s growth rate", "punctuation"),
    ("A startup's growth rate — however fast — cannot fix negative unit "
     "economics.", "punctuation"),
    ("A startup’s growth rate — however fast — cannot fix negative unit "
     "economics.", "punctuation"),
    ("economics.", "too short to discriminate"),
    ("viability holds if and only if LTV > CAC at the unit level.", "markup"),
    ("The fundamental inequality: viability holds if and only if LTV > CAC",
     "markup"),
    ("A startup’s growth rate — however fast — cannot fix negative unit "
     "economics. Growth multiplies whatever unit economics you already have. "
     "The fundamental inequality: viability holds if and only if LTV > CAC",
     "punctuation and markup"),
])
def test_every_diagnosis_is_reachable(quote, expected):
    """All seven verdicts, each reached by an input.

    A category the code can produce but no input reaches is a claim about
    behaviour that nothing verifies — and `punctuation` in particular was
    unreachable on first writing, because folding an em dash to one hyphen
    could not match a source written with two.
    """
    assert diagnose(quote, SOURCE) == expected


def test_dropped_markdown_emphasis_is_not_counted_as_fabrication():
    """The case that made this category necessary, from the real chapter.

    ch02 reads `if and only if **LTV > CAC**` and GLM-5 quoted the prose
    without the asterisks. Every word matches; only the markup differs. With
    no `markup` verdict that quote scored `absent` — the category described in
    the report as "the words are not in the section at all", i.e. the
    fabrication number. One formatting artefact was 4.2% of a rate nobody
    would have read as formatting.
    """
    quote = "viability holds if and only if LTV > CAC at the unit level."

    assert quote not in SOURCE            # still not verbatim, and still refused
    assert quote_appears_in(quote, SOURCE) is False
    assert diagnose(quote, SOURCE) == "markup"
    assert diagnose(quote, SOURCE) != "absent"


def test_stripping_markup_does_not_excuse_a_changed_word():
    """The same guard `punctuation` has. Generous about markers, never about
    words — otherwise every added category is a hole in the fabrication
    number rather than a correction to it."""
    assert diagnose(
        "viability holds if and only if LTV < CAC at the unit level.", SOURCE
    ) == "absent"


def test_underscores_survive_stripping_because_predicates_contain_them():
    """`_italic_` is real markdown, but this domain's predicates are
    snake_case and a quote is likelier to contain `not_value_creation` than
    an underscore-italicised phrase. Stripping them would mangle the
    identifier and do it in the direction that hides a miss."""
    assert strip_markup("**not_value_creation**") == "not_value_creation"
    assert strip_markup("`ltv_cac_ratio`") == "ltv_cac_ratio"
    assert strip_markup("_emphasised_") == "_emphasised_"


def test_the_punctuation_verdict_does_not_swallow_a_real_difference():
    """Folding is generous on purpose, but not so generous that a changed
    word gets excused as typography."""
    assert diagnose(
        "A startup’s growth rate — however slow — cannot fix negative unit "
        "economics.",
        SOURCE,
    ) == "absent"


def test_a_short_quote_is_reported_even_though_it_was_found():
    """'growth' appears in most chapters of a business guide. Finding it
    proves nothing, so it is neither refused outright nor waved through."""
    assert len("economics.") < MIN_DISCRIMINATING_LENGTH
    assert quote_appears_in("economics.", SOURCE)
    assert diagnose("economics.", SOURCE) == "too short to discriminate"


def test_the_helpers_do_what_their_names_say():
    assert normalise_whitespace("  a\n\n b  ") == "a b"
    assert fold_punctuation("a’b—c") == "a'b-c"
    assert fold_punctuation("a--b") == "a-b"


# ── Through the extractor's own loop ─────────────────────────
#
# The helpers above can be right while the loop files their answers under the
# wrong counter, which is exactly the defect this file was created for twice
# before. The stub stands in for the DSPy predictor.

_HEADING = "### Growth and unit economics"
_BODY = (
    "A startup's growth rate cannot fix negative unit economics, and this "
    "section runs past twenty words so the extractor does not skip it. "
)
_SECTION = f"{_HEADING}\n{_BODY * 3}"


class _StubPredictor:
    """Returns one predicate per call with the quote it is told to."""

    def __init__(self, quote):
        self.quote = quote
        self.history = []

    def __call__(self, **kwargs):
        self.history.append({"response": SimpleNamespace(
            choices=[SimpleNamespace(finish_reason="stop")])})
        return SimpleNamespace(
            predicates=["some_predicate"],
            descriptions=["a paraphrase the model wrote"],
            quotes=[self.quote],
            claim_types=["causal"],
            related_vyaptis=["none"],
        )


def _run(quote) -> StageAOutput:
    from anvikshiki_v4.predicate_extraction import StageAExtractor

    stage = StageAExtractor(
        KnowledgeStore(domain_type=DomainType.CRAFT), ExtractionConfig()
    )
    stage.extractor = _StubPredictor(quote)
    return stage(chapter_text=_SECTION, chapter_id="ch02")


def test_a_verbatim_quote_is_captured_and_marked_found():
    out = _run("A startup's growth rate cannot fix negative unit economics")
    prov = out.candidates[0].provenance
    assert prov.quote == (
        "A startup's growth rate cannot fix negative unit economics"
    )
    assert prov.quote_found_in_source is True
    assert (out.quoteless_candidates, out.unverified_quote_candidates) == (0, 0)
    assert out.quote_failures == []


def test_a_fabricated_quote_is_kept_but_marked_unverified():
    """Kept, not dropped. Dropping here would remove the very thing the rate
    is meant to measure; the gate that drops belongs downstream."""
    out = _run("Growth solves everything if you scale fast enough.")
    prov = out.candidates[0].provenance
    assert len(out.candidates) == 1
    assert prov.quote_found_in_source is False
    assert out.unverified_quote_candidates == 1
    assert out.quoteless_candidates == 0
    assert "absent" in out.quote_failures[0]


def test_no_quote_at_all_is_counted_apart_from_a_wrong_one():
    """'Declined to cite' and 'cited something absent' are different facts
    about the model, and only the second is evidence of fabrication."""
    out = _run("")
    prov = out.candidates[0].provenance
    assert prov.quote == ""
    assert prov.quote_found_in_source is None
    assert out.quoteless_candidates == 1
    assert out.unverified_quote_candidates == 0
    assert out.quote_failures == []


def test_a_run_that_checked_is_distinguishable_from_one_that_could_not():
    """The counters are meaningless without this, and the old traces prove it.

    Reparsing `stage_a_ch02.json` — written before spans were captured —
    yields `quoteless_candidates == 0`, which reads as "no candidate lacked a
    quote" when every one of its 24 did. The flag is what separates a measured
    zero from an unmeasured one.
    """
    assert _run("").quotes_checked is True

    stale = StageAOutput(chapter_id="ch02", section_count=1)
    assert stale.quotes_checked is False
    assert stale.quoteless_candidates == 0  # meaningless, and now labelled so


def test_the_three_outcomes_are_never_the_same_counter():
    """One run of each, compared, so no two can be confused for each other."""
    verbatim = _run("A startup's growth rate cannot fix negative unit economics")
    absent = _run("Growth solves everything if you scale fast enough.")
    missing = _run("")

    assert [o.quoteless_candidates for o in (verbatim, absent, missing)] == [
        0, 0, 1
    ]
    assert [
        o.unverified_quote_candidates for o in (verbatim, absent, missing)
    ] == [0, 1, 0]
    assert [
        o.candidates[0].provenance.quote_found_in_source
        for o in (verbatim, absent, missing)
    ] == [True, False, None]


class _StubMultiPredictor:
    """Returns several predicates with whatever parallel lists it is given.

    The single-predicate stub above cannot reach the zip at all: with one
    predicate, a short list and a complete one are the same list.
    """

    def __init__(self, predicates, quotes):
        self.predicates = predicates
        self.quotes = quotes
        self.history = []

    def __call__(self, **kwargs):
        self.history.append({"response": SimpleNamespace(
            choices=[SimpleNamespace(finish_reason="stop")])})
        return SimpleNamespace(
            predicates=list(self.predicates),
            descriptions=[f"paraphrase of {p}" for p in self.predicates],
            quotes=list(self.quotes),
            claim_types=["causal"] * len(self.predicates),
            related_vyaptis=["none"] * len(self.predicates),
        )


def _run_many(predicates, quotes) -> StageAOutput:
    from anvikshiki_v4.predicate_extraction import StageAExtractor

    stage = StageAExtractor(
        KnowledgeStore(domain_type=DomainType.CRAFT), ExtractionConfig()
    )
    stage.extractor = _StubMultiPredictor(predicates, quotes)
    return stage(chapter_text=_SECTION, chapter_id="ch02")


_REAL = "A startup's growth rate cannot fix negative unit economics"


def test_a_short_quotes_list_is_not_counted_as_the_model_declining_to_cite():
    """Our zip running out and the model answering "no quote" both arrive as
    `""`. Only the second is a fact about the model, and the verbatim rate is
    unreadable while they share a counter."""
    out = _run_many(["pred_a", "pred_b", "pred_c"], [_REAL])

    assert len(out.candidates) == 3
    assert out.unquoted_by_short_list == 2
    assert out.quoteless_candidates == 0
    assert all("short quotes list" in f for f in out.quote_failures)
    assert "1 quote(s) for 3 predicate(s)" in out.quote_failures[0]


def test_an_offered_empty_quote_is_still_the_models_own_silence():
    """The other side of the same split: a list long enough, holding "". That
    is the model declining, and it must not be attributed to our zip."""
    out = _run_many(["pred_a", "pred_b"], [_REAL, ""])

    assert out.quoteless_candidates == 1
    assert out.unquoted_by_short_list == 0
    assert out.quote_failures == []


def test_the_two_reasons_partition_the_empty_quotes():
    """They must sum to the number of empty quotes, or the split is not a
    split. The measurement script asserts this on the page too — a breakdown
    that disagrees with the total it breaks down is worse than none."""
    out = _run_many(["a", "b", "c", "d"], [_REAL, ""])

    empty = sum(1 for c in out.candidates if not c.provenance.quote)
    assert empty == 3
    assert out.quoteless_candidates == 1
    assert out.unquoted_by_short_list == 2
    assert out.quoteless_candidates + out.unquoted_by_short_list == empty


def test_a_run_predating_the_short_list_counter_reads_as_unmeasured():
    """Same trap as `quoteless_candidates`, one field later: a new counter
    defaulting to 0 claims a measurement on every record written before it
    existed. `quotes_checked` is what makes the zero readable."""
    stale = StageAOutput(chapter_id="ch02", section_count=1)
    assert stale.unquoted_by_short_list == 0
    assert stale.quotes_checked is False


def test_a_shifted_middle_element_is_still_undetected():
    """The limit of this fix, asserted rather than described.

    Dropping a quote from the *middle* leaves the lists a valid length apart
    at the end only — every quote after the gap silently moves onto the wrong
    predicate. The one that lands on the last predicate is a real span from
    this section, so it passes the verbatim check while citing a claim it does
    not support. Nothing here catches that, and this test fails the day
    something does.
    """
    second = "this section runs past twenty words so the extractor does not skip it"
    assert second in _SECTION  # both are real spans; that is the problem

    out = _run_many(["pred_a", "pred_b"], [second])

    # `pred_a` is now credited with `pred_b`'s quote, verbatim and verified.
    assert out.candidates[0].name == "pred_a"
    assert out.candidates[0].provenance.quote == second
    assert out.candidates[0].provenance.quote_found_in_source is True

    # And the only thing flagged is the padding at the end, which is the
    # symptom furthest from the actual mistake.
    assert out.unquoted_by_short_list == 1
    assert out.unverified_quote_candidates == 0


def test_a_punctuation_miss_is_recorded_as_such_not_as_absent():
    """So a not-found rate can be read. A run whose misses are all typography
    and one whose misses are all invention need opposite responses."""
    out = _run("A startup’s growth rate cannot fix negative unit economics")
    assert out.unverified_quote_candidates == 1
    assert "punctuation" in out.quote_failures[0]
    assert "absent" not in out.quote_failures[0]


def test_the_section_heading_is_captured():
    out = _run("A startup's growth rate cannot fix negative unit economics")
    assert out.candidates[0].provenance.section_header == (
        "Growth and unit economics"
    )


def test_a_section_with_no_heading_gets_an_empty_one():
    """`_split_into_sections` also splits on the token budget, so a section
    can begin mid-prose. Inheriting the previous heading would attach a claim
    to a part of the chapter it did not come from."""
    from anvikshiki_v4.predicate_extraction import StageAExtractor

    stage = StageAExtractor(
        KnowledgeStore(domain_type=DomainType.CRAFT), ExtractionConfig()
    )
    stage.extractor = _StubPredictor("")
    out = stage(chapter_text=_BODY * 3, chapter_id="ch02")
    assert out.candidates[0].provenance.section_header == ""


# ── The statement no longer takes an unverified span ─────────

def _statement_from_stage_d(quote, found) -> str:
    """Drive the real Stage D standalone path and return the rule's statement.

    No model is called. With `stage_b.nodes` empty the first loop — the only
    one that calls the constructor — does nothing, and the standalone branch
    runs purely locally. Worth doing this way rather than re-implementing the
    expression in the test: a test that restates the code it is checking passes
    whether or not the code still says that.
    """
    from anvikshiki_v4.extraction_schema import (
        CandidatePredicate, ClaimType, Provenance, StageBOutput, StageCOutput,
    )
    from anvikshiki_v4.predicate_extraction import StageDConstructor

    candidate = CandidatePredicate(
        name="some_new_predicate",
        description="a paraphrase the model wrote",
        claim_type=ClaimType.CAUSAL,
        provenance=Provenance(
            chapter_id="ch02", quote=quote, quote_found_in_source=found,
        ),
    )
    stage_d = StageDConstructor(
        KnowledgeStore(domain_type=DomainType.CRAFT), ExtractionConfig()
    )
    out = stage_d(
        stage_a=StageAOutput(candidates=[candidate], chapter_id="ch02"),
        stage_b=StageBOutput(nodes={}),
        stage_c=StageCOutput(vocabulary=["some_new_predicate"]),
        guide_text={},
    )
    assert len(out.new_vyaptis) == 1, "the standalone path did not fire"
    return out.new_vyaptis[0].statement


def test_only_a_verified_quote_becomes_the_rule_statement():
    """`quote or description` was harmless while quotes were never captured.

    Now that they are, it would promote a sentence the model produced and the
    section does not contain into the rule's statement, where it reads as the
    source's own words. The fallback still happens; the provenance records
    that it did.
    """
    assert _statement_from_stage_d(
        "A real span from the chapter.", True
    ) == "A real span from the chapter."


def test_an_unverified_quote_does_not_become_the_statement():
    assert _statement_from_stage_d(
        "A span that is not in the chapter.", False
    ) == "a paraphrase the model wrote"


def test_a_found_but_too_short_quote_does_not_become_the_statement():
    """Found and usable are different questions, and one flag answered both.

    `"economics."` genuinely occurs in the chapter, so `quote_found_in_source`
    is True for it — the honest verdict — and on that flag alone a
    ten-character fragment became the rule's statement. Caught by probing the
    change rather than by reading it.
    """
    from anvikshiki_v4.span_verification import is_discriminating

    assert not is_discriminating("economics.")
    assert _statement_from_stage_d(
        "economics.", True
    ) == "a paraphrase the model wrote"


def test_a_long_enough_verified_quote_still_wins():
    """The guard must not swallow the case it exists to allow."""
    span = "Growth multiplies whatever unit economics you already have."
    assert is_discriminating(span)
    assert _statement_from_stage_d(span, True) == span


def test_an_unchecked_quote_does_not_become_the_statement_either():
    """None is 'nobody looked'. Treating it as good enough to quote would be
    the same failure in a quieter form."""
    assert _statement_from_stage_d("", None) == "a paraphrase the model wrote"
    assert _statement_from_stage_d(
        "An unchecked span.", None
    ) == "a paraphrase the model wrote"


# ── The real chapter, and the number this change exists for ──

def test_todays_statements_are_not_in_the_source_they_cite():
    """The measurement, on real data, with no model call.

    Every statement extraction currently produces is `description`, because
    `quote` is empty on all 24 candidates in the only recorded run. Checked
    against the chapter they were extracted from, **none of them appears**.

    This is not a fabrication rate — the model was never asked to quote — but
    it is what the citation chain contains today, and it is the number this
    change exists to move. When extraction starts quoting, this test should be
    replaced by one measuring the real rate.
    """
    from pathlib import Path

    chapter = Path("guides/business_expert/guide_ch2.md")
    trace = Path("traces/instrument_validation/stage_a_ch02.json")
    if not (chapter.exists() and trace.exists()):
        pytest.skip("run from the repo root; chapter or trace not present")

    source = chapter.read_text()
    candidates = json.load(trace.open())["candidates"]
    assert len(candidates) == 24, "the trace changed shape"

    found = [
        c for c in candidates if quote_appears_in(c["description"], source)
    ]
    assert found == [], (
        f"{len(found)} description(s) now appear verbatim in the chapter"
    )

    # The control matters more than the assertion above: a checker that finds
    # nothing anywhere would pass it while measuring nothing at all.
    real_lines = [
        ln.strip() for ln in source.split("\n") if len(ln.strip()) > 60
    ][:5]
    assert len(real_lines) == 5
    assert all(quote_appears_in(ln, source) for ln in real_lines)
