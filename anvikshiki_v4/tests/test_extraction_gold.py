# tests/test_extraction_gold.py
"""The gold set is loaded, and the harness is pointed at it.

The fixture held fourteen hand-authored predicates and a header claiming the
test suite used them for precision and recall. Nothing loaded it — zero
references across every Python file in the repo — while every precision and
recall test used inline toy literals like `["a", "b"]`. There was no
measurement to trust or distrust; there was no measurement.
"""

from pathlib import Path

import pytest

from anvikshiki_v4.extraction_eval import (
    ExtractionEvaluator,
    _description_overlap,
    predicate_precision,
    predicate_recall,
)
from anvikshiki_v4.extraction_gold import CHAPTER_2_GOLD, GoldSet, load_gold

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def gold() -> GoldSet:
    return load_gold()


# ── the fixture is real, and loaded ──

def test_the_gold_set_loads(gold):
    assert len(gold) == 14
    assert gold.chapter_id == "ch02"
    assert "ltv_exceeds_cac" in gold.names


def test_every_gold_predicate_carries_a_description(gold):
    """Descriptions are the half that was being discarded, so they must be there."""
    missing = [p.name for p in gold.predicates if not p.description.strip()]
    assert not missing, f"gold entries with no description: {missing}"
    assert len(gold.descriptions) == 14


def test_the_gold_set_records_what_it_was_authored_against(gold):
    """Which text a human read while writing this decides what may be claimed.

    The excerpt it was authored for is not an excerpt of the real chapter, so a
    run against each measures a different thing and the two cannot be merged.
    """
    assert gold.authored_for.endswith("guide_ch2_excerpt.md")
    assert (REPO_ROOT / gold.authored_for).exists()


def test_the_header_no_longer_claims_a_reader_that_does_not_exist():
    """The old header named a test file that never opened this fixture."""
    header = CHAPTER_2_GOLD.read_text()[:1200]
    assert "Used by test_predicate_extraction.py" not in header
    assert "extraction_gold.py" in header


def test_a_missing_gold_file_raises_rather_than_scoring_zero(tmp_path):
    """An empty gold set gives recall a denominator of zero.

    `predicate_recall` returns 0.0 for empty gold, which is indistinguishable
    from an extractor that found nothing. Failing at load time is the only
    place this can be caught.
    """
    with pytest.raises(FileNotFoundError):
        load_gold(tmp_path / "absent.yaml")


def test_a_gold_file_with_no_predicates_raises(tmp_path):
    empty = tmp_path / "empty.yaml"
    empty.write_text("chapter_id: ch02\nexpected_predicates: []\n")
    with pytest.raises(ValueError, match="zero predicates"):
        load_gold(empty)


# ── the harness is pointed at it ──

def test_the_evaluator_can_be_built_from_the_gold_set(gold):
    evaluator = ExtractionEvaluator.from_gold_set(gold)
    assert evaluator.gold_predicates == gold.names
    assert evaluator.gold_descriptions == gold.descriptions
    assert evaluator.gold_vyapti_count == 4


def test_a_perfect_extraction_against_the_real_gold_scores_one(gold):
    """Sanity: gold matched against itself is 1.0 under every mode."""
    names = sorted(gold.names)
    for mode in ("name", "description", "either"):
        assert predicate_precision(
            names, gold.names, match_on=mode,
            extracted_descriptions=gold.descriptions,
            gold_descriptions=gold.descriptions,
        ) == 1.0


def test_an_inverted_extraction_against_the_real_gold_scores_zero(gold):
    """The audit's experiment, run against the actual fourteen.

    The gold contains its own contrast pairs — economies_of_scale_real beside
    imagined_economies_of_scale, negative_unit_economics beside the
    positive_unit_economics in existing_related — so inverting it produces
    predicates the old matcher scored 1.000 against.
    """
    inverted = [f"not_{name}" for name in sorted(gold.names)]
    assert predicate_precision(inverted, gold.names) == 0.0
    assert predicate_recall(inverted, gold.names) == 0.0


# ── matching on descriptions rather than labels ──

def test_descriptions_can_match_where_invented_labels_do_not(gold):
    """The case that motivates description matching.

    None of the fourteen gold names appear literally in the prose they are gold
    for, so an extractor has to invent a label and the name matcher has to
    accept the guess. A different label over the same sentence is exactly what
    names miss and descriptions catch.
    """
    gold_name = "high_retention_rate"
    gold_description = gold.descriptions[gold_name]
    extracted = "customers_stay_subscribed"

    by_name = predicate_precision(
        [extracted], {gold_name}, match_on="name",
        extracted_descriptions={extracted: gold_description},
        gold_descriptions=gold.descriptions,
    )
    by_description = predicate_precision(
        [extracted], {gold_name}, match_on="description",
        extracted_descriptions={extracted: gold_description},
        gold_descriptions=gold.descriptions,
    )

    assert by_name == 0.0, "the invented label should not match by name"
    assert by_description == 1.0, "the same description should match by description"


def test_description_matching_still_refuses_a_negated_description():
    """The looser comparison must not reopen the hole the veto closed."""
    gold_name, extracted = "value_creation", "value_not_created"
    assert predicate_precision(
        [extracted], {gold_name}, match_on="description",
        extracted_descriptions={extracted: "The business does not create value"},
        gold_descriptions={gold_name: "The business creates value"},
    ) == 0.0


def test_description_overlap_ignores_function_words():
    """Otherwise any two sentences look similar and everything matches."""
    assert _description_overlap(
        "the value is created by the business",
        "a profit is destroyed in the market",
    ) == 0.0


def test_match_on_defaults_to_name_until_validation_says_otherwise(gold):
    """Recorded as a decision, not an oversight.

    Whether descriptions match better on this corpus is an empirical question,
    and switching the default on an untested belief that a looser comparison is
    a better one is how the original defect got in.
    """
    assert ExtractionEvaluator.from_gold_set(gold).match_on == "name"


def test_an_unknown_match_mode_is_rejected(gold):
    with pytest.raises(ValueError, match="match_on"):
        predicate_precision(["x"], gold.names, match_on="semantic")
