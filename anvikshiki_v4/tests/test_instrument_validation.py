# tests/test_instrument_validation.py
"""The harness grades extraction; this is what grades the harness.

Until something does, a precision figure means "the matcher said so" rather
than "this is right" — and the matcher previously said an extractor emitting
the exact inverse of every gold predicate scored 1.000/1.000.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from anvikshiki_v4.instrument_validation import (
    AGREE,
    DISAGREE,
    MATCH,
    NO_MATCH,
    UNJUDGED,
    MatcherDecision,
    MatcherParams,
    SheetProvenance,
    agreement,
    build_decision_sheet,
    read_decision_sheet,
    write_decision_sheet,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

GOLD = {"ltv_exceeds_cac", "high_retention_rate", "value_creation"}
GOLD_DESCRIPTIONS = {
    "ltv_exceeds_cac": "Lifetime value exceeds customer acquisition cost",
    "high_retention_rate": "Customer retention rate is high (low churn)",
    "value_creation": "The business creates value",
}
CANDIDATES = [
    ("ltv_above_cac", "Lifetime value is above acquisition cost"),
    ("cac_exceeds_ltv", "Acquisition cost exceeds lifetime value"),
    ("customers_stay_subscribed", "Customer retention rate is high (low churn)"),
]


# ── what lands on the sheet ──

def test_the_sheet_carries_the_matches_as_precision_claims():
    sheet = build_decision_sheet(GOLD, GOLD_DESCRIPTIONS, CANDIDATES)
    matched = [d for d in sheet if d.kind == "matched"]
    assert matched, "no matched pairs reached the sheet"
    assert all(d.matcher_says_match for d in matched)
    assert any(
        d.gold == "ltv_exceeds_cac" and d.candidate == "ltv_above_cac"
        for d in matched
    )


def test_the_sheet_carries_near_misses_as_recall_claims():
    """The half a review built around extractor output cannot produce.

    Without these, the sheet finds only false positives — the same blindness
    the HITL reviewer has, and recall is made of the other kind.
    """
    sheet = build_decision_sheet(GOLD, GOLD_DESCRIPTIONS, CANDIDATES)
    near = [d for d in sheet if d.kind == "near_miss"]
    assert near
    assert all(not d.matcher_says_match for d in near)
    # value_creation matched nothing, so its nearest candidates must be offered
    assert any(d.gold == "value_creation" for d in near)


def test_a_refused_pair_carries_the_reason_it_was_refused():
    """The judge should see why, not just that."""
    sheet = build_decision_sheet(GOLD, GOLD_DESCRIPTIONS, CANDIDATES)
    reversed_pair = [
        d for d in sheet
        if d.gold == "ltv_exceeds_cac" and d.candidate == "cac_exceeds_ltv"
    ]
    if reversed_pair:
        assert "argument order" in reversed_pair[0].veto_reason


def _provenance(**overrides) -> SheetProvenance:
    fields = dict(
        matcher=MatcherParams(),
        extraction_model="test/model",
        extraction_sha256="0" * 64,
        chapter_id="ch02",
        gold_count=len(GOLD),
        candidate_count=len(CANDIDATES),
        matched_rows=1,
        near_miss_rows=2,
        git_commit="abc123",
        python_hash_seed="unset",
    )
    fields.update(overrides)
    return SheetProvenance(**fields)


def test_the_sheet_round_trips_through_yaml(tmp_path):
    sheet = build_decision_sheet(GOLD, GOLD_DESCRIPTIONS, CANDIDATES)
    provenance = _provenance()
    path = write_decision_sheet(sheet, tmp_path / "sheet.yaml", provenance)
    loaded = read_decision_sheet(path)
    assert loaded.decisions == sheet
    assert loaded.provenance == provenance


# ── #64: the same run twice must produce the same sheet ──

_PROBE = """
import sys
from anvikshiki_v4.instrument_validation import build_decision_sheet, MatcherParams

gold = {"value_creation", "high_retention_rate"}
gold_descriptions = {"value_creation": "The business creates value",
                     "high_retention_rate": "Customer retention is high"}
# Deliberately share no tokens with the gold names, so every pair scores 0.0
# and the ranking is decided entirely by how ties are broken.
candidates = [(n, "") for n in
              ("zebra", "quark", "mango", "alpha", "tiger", "delta", "kappa")]

sheet = build_decision_sheet(gold, gold_descriptions, candidates,
                             MatcherParams(match_on="name"))
for d in sheet:
    print(d.kind, d.gold, d.candidate, d.score, sep="\\t")
"""


def _build_under_seed(seed: str) -> str:
    env = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONPATH": str(REPO_ROOT)}
    done = subprocess.run(
        [sys.executable, "-c", _PROBE],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True,
    )
    assert done.returncode == 0, f"probe failed under seed {seed}:\n{done.stderr}"
    return done.stdout


def test_the_sheet_is_the_same_whatever_the_process_hash_seed_is():
    """The rows a human is asked to judge must not change between runs.

    Candidate names live in a set and `sorted` is stable, so ranking on
    similarity alone left tied candidates in set iteration order — which for
    strings is randomised per process by PYTHONHASHSEED. Ties are the common
    case, not an edge case: under match_on='name' most pairs score exactly 0.0.

    Judgments are stored per (gold, candidate) row, so a sheet that rebuilds
    differently cannot be regenerated to match the judgments already entered
    against it, and a kill criterion computed over it is not checkable.

    The seeds are set on child processes rather than read from this one, so
    this test still fails on the bug when the suite itself is run under a
    fixed PYTHONHASHSEED — which would otherwise hide exactly what it checks.
    """
    outputs = {seed: _build_under_seed(seed) for seed in ("0", "1", "17", "4242")}

    rows = outputs["0"].strip().splitlines()
    assert len(rows) == 6, f"expected 2 gold x 3 near misses, got {len(rows)}"

    distinct = set(outputs.values())
    assert len(distinct) == 1, (
        f"the sheet differs across {len(distinct)} of {len(outputs)} hash seeds; "
        "which rows a human is asked to judge depends on the process"
    )


def test_tied_near_misses_are_ranked_by_name():
    """The tie-break has to be something, and it has to be stated.

    Ranking on (-score, name) is a total order because candidate names are
    unique. Anything less is a partial order, and a partial order handed to a
    stable sort leaves the rest to whatever collection the items came from.
    """
    tied = [(n, "") for n in ("zebra", "mango", "alpha", "delta")]
    sheet = build_decision_sheet(
        {"value_creation"}, {"value_creation": "The business creates value"},
        tied, MatcherParams(match_on="name"),
    )
    near = [d for d in sheet if d.kind == "near_miss"]
    assert [d.score for d in near] == [0.0, 0.0, 0.0], "expected an all-tied ranking"
    assert [d.candidate for d in near] == ["alpha", "delta", "mango"]


# ── agreement ──

def _decision(matcher_match: bool, human: str) -> MatcherDecision:
    return MatcherDecision(
        gold="g", candidate="c", matcher_says_match=matcher_match, human=human
    )


def test_an_unjudged_sheet_reports_no_agreement_rather_than_perfect():
    """The defect this whole phase is about, in its own machinery.

    A sheet nobody filled in must not come back as agreement, for the same
    reason a validation that never ran must not score 1.0.
    """
    report = agreement(build_decision_sheet(GOLD, GOLD_DESCRIPTIONS, CANDIDATES))
    assert report.judged == 0
    assert report.observed_agreement is None
    assert report.cohens_kappa is None
    assert report.kappa_undefined_reason == "nothing was judged"
    assert report.semantic_encoder_is_indicated is None


def test_unjudged_rows_are_excluded_not_counted_as_agreement():
    report = agreement([
        _decision(True, AGREE),
        _decision(True, ""),
        _decision(False, ""),
    ])
    assert report.judged == 1
    assert report.unjudged == 2


def test_the_two_disagreement_classes_are_reported_separately():
    """They are not symmetric and only one of them argues for an encoder."""
    report = agreement([
        _decision(True, AGREE),       # both say match
        _decision(False, AGREE),      # both reject
        _decision(True, DISAGREE),    # matcher yes, human no — precision failure
        _decision(False, DISAGREE),   # matcher no, human yes — semantics needed
    ])
    assert report.both_match == 1
    assert report.both_reject == 1
    assert report.matcher_only == 1
    assert report.human_only == 1
    assert report.observed_agreement == 0.5


def test_a_semantic_encoder_is_indicated_only_by_human_yes_matcher_no():
    """A precision failure is not evidence for an encoder; the veto handles it."""
    precision_failures_only = agreement([
        _decision(True, DISAGREE), _decision(True, AGREE), _decision(False, AGREE)
    ])
    assert precision_failures_only.human_only == 0
    assert precision_failures_only.semantic_encoder_is_indicated is False

    missed_a_true_match = agreement([
        _decision(False, DISAGREE), _decision(True, AGREE), _decision(False, AGREE)
    ])
    assert missed_a_true_match.human_only == 1
    assert missed_a_true_match.semantic_encoder_is_indicated is True


def test_kappa_is_undefined_rather_than_one_when_chance_agreement_is_total():
    """Perfect agreement on a single answer is not a kappa of 1.0.

    If both raters say match to everything, chance agreement is already 1.0
    and kappa divides by zero. Reporting 1.0 there would be the strongest
    possible claim drawn from the weakest possible evidence.
    """
    report = agreement([_decision(True, AGREE), _decision(True, AGREE)])
    assert report.observed_agreement == 1.0
    assert report.cohens_kappa is None
    assert "chance agreement is 1.0" in report.kappa_undefined_reason


def test_kappa_is_computed_when_the_raters_vary():
    report = agreement([
        _decision(True, AGREE), _decision(True, AGREE),
        _decision(False, AGREE), _decision(False, AGREE),
        _decision(True, DISAGREE), _decision(False, DISAGREE),
    ])
    assert report.cohens_kappa is not None
    assert -1.0 <= report.cohens_kappa <= 1.0
    assert report.observed_agreement == pytest.approx(4 / 6)


# ── replaying one set of judgments across match modes ──

def _near_miss_the_human_calls_a_match(human):
    """One pair, judged as a match, spelled whichever way the caller asks."""
    return MatcherDecision(
        gold="high_retention_rate",
        candidate="customers_stay_subscribed",
        gold_description=GOLD_DESCRIPTIONS["high_retention_rate"],
        candidate_description=GOLD_DESCRIPTIONS["high_retention_rate"],
        matcher_says_match=False,
        human=human,
        kind="near_miss",
    )


@pytest.mark.parametrize("spelling", [MATCH, DISAGREE])
def test_a_mode_replay_preserves_what_the_human_meant(spelling):
    """The human judges the pair, not the matcher, so one sheet scores all modes.

    A judgment is a fact about whether two predicates mean the same thing, and
    the replay must carry that fact across a verdict that moves underneath it —
    otherwise switching modes silently rewrites what the human said.

    Parametrised over both spellings because that is the whole argument for the
    fact vocabulary. `disagree` on a near miss and `match` mean the same thing
    here, and only one of them keeps meaning it after the verdict flips: the
    relative spelling needs a compensating flip on the way through, and a
    compensating flip is only ever as reliable as whoever maintains it. The
    replay writes the fact, so there is nothing left to flip.
    """
    from anvikshiki_v4.instrument_validation import replay_mode

    judged = _near_miss_the_human_calls_a_match(spelling)
    assert judged.human_says_match is True

    replayed = replay_mode([judged], GOLD_DESCRIPTIONS, match_on="description")[0]
    assert replayed.matcher_says_match is True     # descriptions catch it
    assert replayed.human_says_match is True       # and the human still says match
    assert replayed.human == MATCH                 # written as the fact it is


def test_a_mode_replay_leaves_unjudged_rows_unjudged():
    from anvikshiki_v4.instrument_validation import replay_mode

    row = MatcherDecision(gold="value_creation", candidate="x", matcher_says_match=False)
    assert replay_mode([row], GOLD_DESCRIPTIONS, match_on="either")[0].human == ""


# ── #65: the sheet has to say how it was built ──

def test_a_sheet_cannot_be_written_without_recording_how_it_was_built():
    """Optional provenance is provenance that gets skipped.

    The registered protocol requires the model, the candidate count and the
    match mode alongside every figure. They were printed to stdout and nowhere
    else, so they survived exactly as long as a terminal scrollback.
    """
    with pytest.raises(TypeError):
        write_decision_sheet([], "unused.yaml")


def test_a_sheet_written_without_a_provenance_block_reads_as_unknown(tmp_path):
    """Not as a plausible default, which is the defect one layer up.

    Sheets on disk predate this block. Defaulting `match_on` to its registered
    value while loading them would state that they were built under 'name' —
    and the sheet this was written for was in fact built under 'either'. A
    fabricated record of a build is worse than no record, because nothing
    downstream can tell the two apart.
    """
    import yaml

    path = tmp_path / "old_sheet.yaml"
    path.write_text(yaml.safe_dump({
        "instructions": "…",
        "decisions": [MatcherDecision(
            gold="g", candidate="c", matcher_says_match=True,
        ).model_dump()],
    }))

    loaded = read_decision_sheet(path)
    assert len(loaded.decisions) == 1, "the rows must still load"
    assert loaded.provenance is None


def test_the_recorded_match_mode_is_the_one_the_matcher_actually_ran_on(tmp_path):
    """One object goes to the matcher and to the sheet, so they cannot drift.

    The parameters that were not passed explicitly are the dangerous ones: a
    caller restating them for the provenance block writes a literal that goes
    stale the moment the default moves.
    """
    params = MatcherParams(match_on="description", near_misses_per_gold=1)
    sheet = build_decision_sheet(GOLD, GOLD_DESCRIPTIONS, CANDIDATES, params)
    path = write_decision_sheet(
        sheet, tmp_path / "sheet.yaml", _provenance(matcher=params),
    )

    recorded = read_decision_sheet(path).provenance
    assert recorded.matcher == params
    assert recorded.matcher.near_misses_per_gold == 1
    per_gold = {}
    for d in read_decision_sheet(path).decisions:
        if d.kind == "near_miss":
            per_gold[d.gold] = per_gold.get(d.gold, 0) + 1
    assert per_gold, "no near misses to check the recorded setting against"
    assert set(per_gold.values()) == {1}, (
        f"sheet records near_misses_per_gold=1 but carries {per_gold}"
    )


def test_a_half_written_provenance_block_fails_loudly(tmp_path):
    """A block missing its identity fields must not quietly describe a run."""
    import yaml

    from pydantic import ValidationError

    path = tmp_path / "partial.yaml"
    path.write_text(yaml.safe_dump({
        "provenance": {"matcher": {"match_on": "either"}},
        "decisions": [],
    }))
    with pytest.raises(ValidationError):
        read_decision_sheet(path)


# ── the judgment vocabulary states a fact ────────────────────
#
# Thirty-three of the shipped sheet's thirty-eight rows are near misses, where
# `matcher_says_match` is False. Under `agree`/`disagree` a judge answering the
# question the sheet's own instructions pose — "do these two mean the same
# thing?" — had to invert their answer on every one of them, and getting it
# wrong is undetectable downstream: an inverted sheet produces a different
# kappa and nothing can tell it from an honest one.

@pytest.mark.parametrize("matcher_says_match", [True, False])
def test_match_says_match_whatever_the_matcher_said(matcher_says_match):
    d = _decision(matcher_says_match, MATCH)
    assert d.judged
    assert d.human_says_match is True


@pytest.mark.parametrize("matcher_says_match", [True, False])
def test_no_match_says_no_match_whatever_the_matcher_said(matcher_says_match):
    d = _decision(matcher_says_match, NO_MATCH)
    assert d.judged
    assert d.human_says_match is False


def test_the_relative_spelling_still_reads_correctly():
    """A sheet already written in agree/disagree means what it meant. Nothing
    is judged today, so nothing depends on this — but silently changing what a
    filled sheet says would be the same defect at one remove."""
    assert _decision(True, AGREE).human_says_match is True
    assert _decision(False, AGREE).human_says_match is False
    assert _decision(True, DISAGREE).human_says_match is False
    assert _decision(False, DISAGREE).human_says_match is True


def test_agree_and_match_mean_opposite_things_on_a_near_miss():
    """The trap, asserted so it cannot be forgotten or reintroduced.

    This is not a quirk to work around — it is why the vocabulary changed. On
    the 33 near-miss rows the two spellings of a judge's honest 'yes, these
    mean the same thing' point in opposite directions.
    """
    assert _decision(False, MATCH).human_says_match is True
    assert _decision(False, AGREE).human_says_match is False


def test_an_unrecognised_word_is_unjudged_rather_than_a_guess(tmp_path):
    """A typo must not be silently resolved to one of the two answers. Unjudged
    is reported as unjudged; a guess would enter the count as data."""
    d = _decision(True, "yes")
    assert not d.judged
    assert d.human_says_match is None


def test_the_instructions_ask_for_the_fact_not_for_agreement(tmp_path):
    """The sheet carries its own instructions, so they are part of the
    instrument. Asking for agreement with `matcher_says_match` is asking the
    judge to encode the thing being measured."""
    import yaml as _yaml

    path = write_decision_sheet(
        [_decision(False, UNJUDGED)], tmp_path / "sheet.yaml", _provenance()
    )
    instructions = _yaml.safe_load(path.read_text())["instructions"]
    assert "'match'" in instructions and "'no_match'" in instructions
    assert "agree" not in instructions, (
        "the word is the trap: a judge scanning for it will find the old "
        "vocabulary in a sheet that no longer uses it"
    )
    assert "matcher_says_match" in instructions, (
        "the fields to ignore have to be named, or the judge reads them"
    )


def test_a_judged_sheet_round_trips(tmp_path):
    path = write_decision_sheet(
        [_decision(False, MATCH), _decision(True, NO_MATCH)],
        tmp_path / "sheet.yaml", _provenance(),
    )
    back = read_decision_sheet(path).decisions
    assert [d.human for d in back] == [MATCH, NO_MATCH]
    assert [d.human_says_match for d in back] == [True, False]
