# anvikshiki_v4/tests/test_truncation_is_not_an_empty_section.py
"""A cut-off answer is a fact about our token budget, not about the prose.

Observed on two runs of the same chapter differing only in budget:

    max_tokens=4096    26 candidates,  2 zero-predicate sections
    max_tokens=16000   24 candidates,  0 zero-predicate sections

Truncation does not raise. The response arrives, it is simply incomplete, so
it parses to no predicates and lands in the same counter as a section that
genuinely holds none — and `zero_section_rate` carries 0.10 of the composite,
so a setting was lowering a quality score.

Nothing here calls a model. The signal is `finish_reason == "length"` on the
completion, which reaches the pipeline through the LM's call history
(`dspy/clients/base_lm.py:_process_lm_response` stores the raw response under
`"response"`), so a stub history is the whole fixture and the tests stay
deterministic and free.
"""

from types import SimpleNamespace

import pytest

from anvikshiki_v4.extraction_eval import ExtractionEvaluator, zero_section_rate
from anvikshiki_v4.extraction_schema import (
    ClaimType,
    CandidatePredicate,
    Provenance,
    StageAOutput,
    StageDOutput,
    ValidationResult,
)
from anvikshiki_v4.predicate_extraction import was_truncated


# ── A stub of what the LM history actually holds ─────────────

def _history(*finish_reasons: str | None) -> list[dict]:
    """One history entry whose response carries these finish reasons.

    Shaped after the real entry: a dict with a `"response"` holding a
    litellm ModelResponse, whose `choices[i].finish_reason` is the signal.
    """
    return [{
        "response": SimpleNamespace(choices=[
            SimpleNamespace(finish_reason=reason) for reason in finish_reasons
        ])
    }]


class _Module:
    def __init__(self, history):
        self.history = history


# ── The detection ────────────────────────────────────────────

def test_a_cut_off_answer_is_detected():
    assert was_truncated(_Module(_history("length"))) is True


def test_a_complete_answer_is_detected():
    assert was_truncated(_Module(_history("stop"))) is False


def test_truncation_in_any_choice_counts():
    assert was_truncated(_Module(_history("stop", "length"))) is True


@pytest.mark.parametrize("history, why", [
    ([], "history switched off, or no call made yet"),
    (None, "module carries no history attribute"),
    ([{"response": None}], "entry holds no response"),
    ([{"response": SimpleNamespace(choices=[])}], "response holds no choices"),
    (_history(None), "the provider did not report a finish reason"),
])
def test_undetectable_truncation_reports_neither_yes_nor_no(history, why):
    """None, never False.

    This is the whole point of the three-valued return. The history is
    conditional — `_process_lm_response` returns early under
    `settings.disable_history`, and `update_history` skips both lists when
    `max_history_size == 0` — so reading its absence as "nothing was
    truncated" would reinstate the defect wherever the history is off, which
    is the case a caller cannot see.
    """
    assert was_truncated(_Module(history)) is None, why


def test_a_module_with_no_history_falls_back_to_the_lm(monkeypatch):
    """Per-module history is preferred, but the LM's is the fallback.

    `update_history` appends to `settings.caller_modules`, so a module's own
    list exists only when it was the caller. The LM's always gets the entry.
    """
    import anvikshiki_v4.predicate_extraction as pe

    monkeypatch.setattr(pe, "_lm_history", lambda: _history("length"))
    assert was_truncated(_Module(None)) is True
    assert was_truncated(_Module([])) is True


# ── The metric ───────────────────────────────────────────────

def test_a_truncated_section_does_not_count_as_an_empty_one():
    """The reported case, as a number.

    Ten sections, two of them cut off by the budget and nothing genuinely
    empty. Before, those two were `zero_predicate_sections` and the rate came
    out 0.8 — a fifth of the score lost to a setting.
    """
    truncated = StageAOutput(
        section_count=10, zero_predicate_sections=0, truncated_sections=2
    )
    assert zero_section_rate(truncated) == 1.0

    # And for contrast: two sections that really did hold nothing, out of the
    # eight that were answered.
    genuinely_empty = StageAOutput(
        section_count=10, zero_predicate_sections=2, truncated_sections=2
    )
    assert zero_section_rate(genuinely_empty) == pytest.approx(0.75)


def test_a_failed_section_leaves_the_denominator_too():
    """Same argument, for the split that already existed.

    An exception and a truncation are different events with the same
    consequence for this metric: no answer came back, so the section says
    nothing about how much the prose contained.
    """
    assert zero_section_rate(
        StageAOutput(section_count=4, zero_predicate_sections=0,
                     failed_sections=2)
    ) == 1.0
    assert zero_section_rate(
        StageAOutput(section_count=4, zero_predicate_sections=1,
                     failed_sections=2)
    ) == pytest.approx(0.5)


def test_a_run_where_nothing_was_answered_is_unmeasured_not_perfect():
    """Every section failed or truncated, so the rate has no denominator.

    Returning 1.0 here would be the original defect inverted — an absence of
    evidence scoring full marks.
    """
    nothing_answered = StageAOutput(
        section_count=3, failed_sections=2, truncated_sections=1
    )
    assert zero_section_rate(nothing_answered) == 0.0

    metrics = ExtractionEvaluator(gold_predicates={"x"}).evaluate(
        nothing_answered, StageDOutput(), ValidationResult(ran=True)
    )
    assert "zero_section" in metrics["unmeasured"], (
        "a rate with no denominator scored 0.0 and was not named as absent, "
        "so the composite reports a missing input as poor quality"
    )


def test_an_unverifiable_run_names_the_component_as_unmeasured():
    """`truncation_checked=False` is a third state, and it has to surface.

    A run that could not read finish_reason cannot tell an empty section from
    one it cut off. That figure is uninterpretable, not low, and the
    `unmeasured` list is where that distinction is kept.
    """
    stage_a = StageAOutput(
        candidates=[CandidatePredicate(
            name="x", description="d", claim_type=ClaimType.CAUSAL,
            provenance=Provenance(chapter_id="ch02", confidence=0.7),
        )],
        section_count=4,
        zero_predicate_sections=1,
        truncation_checked=False,
    )
    metrics = ExtractionEvaluator(gold_predicates={"x"}).evaluate(
        stage_a, StageDOutput(), ValidationResult(ran=True, is_valid=True)
    )
    assert "zero_section" in metrics["unmeasured"]


def test_a_checked_run_with_real_input_is_not_flagged():
    """Otherwise the flag is noise and stops being read."""
    stage_a = StageAOutput(
        candidates=[CandidatePredicate(
            name="x", description="d", claim_type=ClaimType.CAUSAL,
            provenance=Provenance(chapter_id="ch02", confidence=0.7),
        )],
        section_count=4,
        zero_predicate_sections=1,
    )
    metrics = ExtractionEvaluator(gold_predicates={"x"}).evaluate(
        stage_a, StageDOutput(), ValidationResult(ran=True, is_valid=True)
    )
    assert "zero_section" not in metrics["unmeasured"]
    assert stage_a.truncation_checked is True


def test_truncation_defaults_leave_existing_behaviour_alone():
    """A StageAOutput built without the new fields scores as it always did."""
    assert zero_section_rate(
        StageAOutput(section_count=10, zero_predicate_sections=5)
    ) == pytest.approx(0.5)


# ── Through the extractor's own loop ─────────────────────────
#
# Everything above tests the helper and the metric in isolation. The routing
# between the three counters lives in `StageAExtractor.forward`, and a helper
# that returns the right answer to a loop that files it in the wrong counter
# still ships the defect. The stub stands in for the DSPy predictor and
# leaves behind the history entry a real call would.

_SECTION = (
    "### Heading\n"
    + "This section runs well past twenty words so the extractor does not "
      "skip it as too short to be worth a call. " * 3
)


def _chapter(sections: int) -> str:
    return "\n\n".join(_SECTION for _ in range(sections))


class _StubPredictor:
    """Replays a script of outcomes, one per section."""

    def __init__(self, script, keep_history=True):
        self.script = list(script)
        self.keep_history = keep_history
        self.history = [] if keep_history else None
        self.calls = 0

    def __call__(self, **kwargs):
        mode = self.script[self.calls % len(self.script)]
        self.calls += 1
        if mode == "raises":
            raise RuntimeError("provider returned 503")
        if self.keep_history:
            reason = "length" if mode.startswith("truncated") else "stop"
            self.history.append({"response": SimpleNamespace(
                choices=[SimpleNamespace(finish_reason=reason)])})
        predicates = [] if mode.endswith("empty") else ["some_predicate"]
        return SimpleNamespace(
            predicates=predicates,
            descriptions=["a description"] * len(predicates),
            claim_types=["causal"] * len(predicates),
            related_vyaptis=["none"] * len(predicates),
        )


def _run(script, sections=4, keep_history=True) -> StageAOutput:
    from anvikshiki_v4.extraction_schema import ExtractionConfig
    from anvikshiki_v4.predicate_extraction import StageAExtractor
    from anvikshiki_v4.schema import DomainType, KnowledgeStore

    stage = StageAExtractor(
        KnowledgeStore(domain_type=DomainType.CRAFT), ExtractionConfig()
    )
    stage.extractor = _StubPredictor(script, keep_history=keep_history)
    return stage(chapter_text=_chapter(sections), chapter_id="ch02")


def test_the_loop_files_a_cut_off_section_as_truncated_not_empty():
    out = _run(["truncated_empty"])
    assert out.truncated_sections == 4
    assert out.zero_predicate_sections == 0
    assert out.truncation_checked is True
    assert len(out.truncations) == 4


def test_the_loop_separates_all_four_outcomes():
    """One section of each, so no two counters can be confused for each other.

    A test where every section behaves the same way passes for three of the
    four possible mis-filings.
    """
    out = _run(["ok", "truncated_empty", "ok_empty", "raises"])
    assert (out.zero_predicate_sections, out.truncated_sections,
            out.failed_sections) == (1, 1, 1)
    assert len(out.candidates) == 1


def test_a_section_cut_off_after_parsing_something_still_counts_as_truncated():
    """Its predicates are kept — a partial reading is better than none — but
    the section is not evidence about how much the prose contained."""
    out = _run(["truncated"])
    assert out.truncated_sections == 4
    assert out.zero_predicate_sections == 0
    assert len(out.candidates) == 4


def test_the_loop_records_that_it_could_not_check(monkeypatch):
    """History off: three empty sections and no way to know why.

    `truncation_checked` must fall to False so the figure is reported as
    uninterpretable. Reading "no truncation found" out of "could not look" is
    the defect this issue is about, one level up.
    """
    import anvikshiki_v4.predicate_extraction as pe

    monkeypatch.setattr(pe, "_lm_history", lambda: None)
    out = _run(["ok_empty"], sections=3, keep_history=False)
    assert out.zero_predicate_sections == 3
    assert out.truncation_checked is False


def test_a_multi_chapter_run_carries_every_count_up():
    """The aggregator dropped `failed_sections` and `failures` entirely, so a
    multi-chapter run reported no failures however many there were."""
    from anvikshiki_v4.extraction_schema import ExtractionConfig
    from anvikshiki_v4.predicate_extraction import PredicateExtractionPipeline
    from anvikshiki_v4.schema import DomainType, KnowledgeStore

    pipeline = PredicateExtractionPipeline(
        KnowledgeStore(domain_type=DomainType.CRAFT), ExtractionConfig()
    )
    pipeline.stage_a.extractor = _StubPredictor(
        ["truncated_empty", "raises", "ok_empty", "ok"]
    )
    stage_a = pipeline.stage_a
    combined = StageAOutput(candidates=[], chapter_id="all")
    for chapter_id in ("ch02", "ch03"):
        result = stage_a(chapter_text=_chapter(4), chapter_id=chapter_id)
        combined.candidates.extend(result.candidates)
        combined.section_count += result.section_count
        combined.zero_predicate_sections += result.zero_predicate_sections
        combined.failed_sections += result.failed_sections
        combined.failures.extend(result.failures)
        combined.truncated_sections += result.truncated_sections
        combined.truncations.extend(result.truncations)
        combined.truncation_checked = (
            combined.truncation_checked and result.truncation_checked
        )

    assert combined.section_count == 8
    assert combined.failed_sections == 2, "failures were dropped again"
    assert combined.truncated_sections == 2
    assert combined.zero_predicate_sections == 2
    assert len(combined.failures) == 2
    assert len(combined.truncations) == 2
