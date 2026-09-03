# tests/test_judging_is_blind.py
"""The judge is asked about the pair and shown nothing about the matcher.

Step one of #10 is the human's work by protocol — a model judging the
instrument that grades its own output is the self-confirming loop the audit
exists to prevent — so the only thing code can do is make that half cheap and
keep it honest. Honest here means two specific things, and the sheet as it
stands defeats both:

  * **the fields.** `matcher_says_match` and `score` sit three lines above the
    field the judge types into. The question is whether two predicates mean the
    same thing; the matcher's answer to it is the quantity being measured.

  * **the order.** The sheet is written matched-rows-first: on the shipped
    sheet the first 5 rows are the matcher's claimed matches and the remaining
    33 are its near misses. Blinding the fields while leaving that order
    intact is blinding in name — position alone tells the judge the verdict.

The second is the one that would have been missed. It is asserted below
against the sheet's real construction so the shuffle cannot be removed as an
unnecessary complication.
"""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from anvikshiki_v4.instrument_validation import (
    MATCH,
    NO_MATCH,
    UNJUDGED,
    MatcherDecision,
    MatcherParams,
    SheetProvenance,
    read_decision_sheet,
    write_decision_sheet,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import judge_decision_sheet as judge  # noqa: E402

REAL_SHEET = Path("traces/instrument_validation/decision_sheet_ch02.yaml")


def _provenance(**overrides) -> SheetProvenance:
    return SheetProvenance(**{
        "matcher": MatcherParams(),
        "extraction_model": "test-model",
        "extraction_sha256": "0" * 64,
        "chapter_id": "ch02",
        "gold_count": 2,
        "candidate_count": 4,
        "matched_rows": 2,
        "near_miss_rows": 4,
        "git_commit": "abc1234",
        "python_hash_seed": "unset",
        **overrides,
    })


def _rows() -> list[MatcherDecision]:
    """Matched rows first, near misses after — the sheet's real shape."""
    matched = [
        MatcherDecision(
            gold=f"gold_{i}", candidate=f"cand_{i}",
            gold_description=f"description of gold {i}",
            candidate_description=f"description of candidate {i}",
            matcher_says_match=True, score=1.0, kind="matched",
        )
        for i in range(2)
    ]
    near = [
        MatcherDecision(
            gold=f"gold_{i}", candidate=f"other_{i}",
            gold_description=f"description of gold {i}",
            candidate_description=f"description of other {i}",
            matcher_says_match=False, score=0.31, kind="near_miss",
            veto_reason="polarity",
        )
        for i in range(4)
    ]
    return matched + near


@pytest.fixture
def sheet_path(tmp_path):
    return write_decision_sheet(_rows(), tmp_path / "sheet.yaml", _provenance())


# ── the fields ───────────────────────────────────────────────

class TestNothingAboutTheMatcherIsShown:

    @pytest.mark.parametrize("row", _rows(), ids=lambda d: d.kind + "_" + d.candidate)
    def test_the_rendered_pair_carries_no_verdict(self, row):
        shown = judge._render(row, 1, 6)
        for leak in ("matcher", "score", "0.31", "near_miss", "matched",
                     "veto", "polarity", "True", "False"):
            assert leak not in shown, f"{leak!r} reached the judge"

    def test_the_pair_and_its_descriptions_are_shown(self):
        """Blind is not blank. The judgment is made from the descriptions, so
        an interface that withheld those would produce judgments about two
        predicate names, which is `match_on=name` with extra steps."""
        row = _rows()[0]
        shown = judge._render(row, 1, 6)
        assert row.gold in shown and row.candidate in shown
        assert row.gold_description in shown
        assert row.candidate_description in shown

    def test_a_missing_description_says_so_rather_than_showing_nothing(self):
        row = _rows()[0].model_copy(update={"candidate_description": ""})
        assert "(no description)" in judge._render(row, 1, 6)


# ── the order ────────────────────────────────────────────────

class TestTheOrderIsNotTheSheetsOrder:

    def test_file_order_leaks_the_verdict(self):
        """Asserted against the sheet's real construction, because it is the
        whole reason the shuffle exists. Remove the shuffle and a judge working
        top to bottom reads the verdict off the position."""
        rows = _rows()
        boundary = sum(1 for r in rows if r.matcher_says_match)
        assert all(r.matcher_says_match for r in rows[:boundary])
        assert not any(r.matcher_says_match for r in rows[boundary:])

    def test_the_presentation_order_is_shuffled(self):
        rows = _rows()
        assert judge._order(rows, seed=0) != list(range(len(rows)))

    def test_the_same_seed_gives_the_same_order(self):
        """Recorded and reproducible: an ordering nobody can reconstruct makes
        the run unrepeatable for no benefit."""
        rows = _rows()
        assert judge._order(rows, seed=7) == judge._order(rows, seed=7)

    def test_different_seeds_give_different_orders(self):
        rows = _rows()
        assert judge._order(rows, seed=1) != judge._order(rows, seed=2)

    def test_every_row_is_presented_exactly_once(self):
        rows = _rows()
        assert sorted(judge._order(rows, seed=3)) == list(range(len(rows)))


# ── judging end to end ───────────────────────────────────────

def _run(sheet_path, answers, monkeypatch, seed=0, extra=()):
    supplied = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _prompt: next(supplied))
    monkeypatch.setattr(
        sys, "argv",
        ["judge", "--sheet", str(sheet_path), "--seed", str(seed), *extra],
    )
    return judge.main()


class TestJudgingEndToEnd:

    def test_answers_are_written_as_facts_about_the_pair(
        self, sheet_path, monkeypatch
    ):
        assert _run(sheet_path, ["y"] * 6, monkeypatch) == 0
        rows = read_decision_sheet(sheet_path).decisions
        assert {d.human for d in rows} == {MATCH}
        assert all(d.human_says_match is True for d in rows), (
            "including the four near misses, where the matcher said no — "
            "which is the point of the vocabulary"
        )

    def test_no_is_recorded_as_no_match(self, sheet_path, monkeypatch):
        _run(sheet_path, ["n"] * 6, monkeypatch)
        rows = read_decision_sheet(sheet_path).decisions
        assert {d.human for d in rows} == {NO_MATCH}

    def test_unsure_leaves_the_row_unjudged(self, sheet_path, monkeypatch):
        _run(sheet_path, [""] * 6, monkeypatch)
        rows = read_decision_sheet(sheet_path).decisions
        assert {d.human for d in rows} == {UNJUDGED}
        assert not any(d.judged for d in rows)

    def test_quitting_keeps_what_was_judged(self, sheet_path, monkeypatch):
        _run(sheet_path, ["y", "n", "q"], monkeypatch)
        rows = read_decision_sheet(sheet_path).decisions
        assert sum(1 for d in rows if d.judged) == 2

    def test_an_interrupt_saves_rather_than_discards(
        self, sheet_path, monkeypatch
    ):
        """Twenty minutes of judging must not be lost to a stray ctrl-C."""
        supplied = iter(["y", "y"])

        def _input(_prompt):
            try:
                return next(supplied)
            except StopIteration:
                raise KeyboardInterrupt

        monkeypatch.setattr("builtins.input", _input)
        monkeypatch.setattr(
            sys, "argv", ["judge", "--sheet", str(sheet_path), "--seed", "0"]
        )
        assert judge.main() == 0
        assert sum(
            1 for d in read_decision_sheet(sheet_path).decisions if d.judged
        ) == 2

    def test_a_second_run_offers_only_the_unjudged_rows(
        self, sheet_path, monkeypatch
    ):
        _run(sheet_path, ["y", "y", "q"], monkeypatch)
        _run(sheet_path, ["n"] * 4, monkeypatch)
        rows = read_decision_sheet(sheet_path).decisions
        assert sum(1 for d in rows if d.human == MATCH) == 2
        assert sum(1 for d in rows if d.human == NO_MATCH) == 4

    def test_back_revisits_the_previous_pair(self, sheet_path, monkeypatch):
        _run(sheet_path, ["y", "b", "n", "q"], monkeypatch)
        rows = read_decision_sheet(sheet_path).decisions
        judged = [d.human for d in rows if d.judged]
        assert judged == [NO_MATCH], (
            "the first answer is overwritten, not appended beside it"
        )

    def test_an_unrecognised_key_does_not_advance(self, sheet_path, monkeypatch):
        """A fat-fingered key must not silently become an answer, and must not
        skip the pair it was typed at."""
        _run(sheet_path, ["maybe", "y", "q"], monkeypatch)
        rows = read_decision_sheet(sheet_path).decisions
        assert sum(1 for d in rows if d.judged) == 1

    def test_the_provenance_survives_judging(self, sheet_path, monkeypatch):
        before = read_decision_sheet(sheet_path).provenance
        _run(sheet_path, ["y"] * 6, monkeypatch)
        assert read_decision_sheet(sheet_path).provenance == before

    def test_the_pairs_themselves_are_untouched(self, sheet_path, monkeypatch):
        """Judgments are keyed to (gold, candidate). A run that reordered or
        rewrote the rows would leave the judgments describing other pairs."""
        before = [
            (d.gold, d.candidate, d.matcher_says_match, d.score, d.kind)
            for d in read_decision_sheet(sheet_path).decisions
        ]
        _run(sheet_path, ["y", "n", "", "y", "n", ""], monkeypatch)
        after = [
            (d.gold, d.candidate, d.matcher_says_match, d.score, d.kind)
            for d in read_decision_sheet(sheet_path).decisions
        ]
        assert after == before

    def test_a_backup_is_written_before_the_sheet_is_replaced(
        self, sheet_path, monkeypatch
    ):
        """`traces/` is gitignored, so the sheet has no git backup and a
        rebuild is not a recovery — the rows depend on parameters the rebuild
        would have to be handed exactly."""
        _run(sheet_path, ["y"] * 6, monkeypatch)
        backups = list(Path(sheet_path).parent.glob("*.bak.yaml"))
        assert len(backups) == 1
        assert not any(
            d.judged for d in read_decision_sheet(backups[0]).decisions
        ), "the backup is the state before this run, not after it"

    def test_no_partial_file_is_left_behind(self, sheet_path, monkeypatch):
        _run(sheet_path, ["y"] * 6, monkeypatch)
        assert not list(Path(sheet_path).parent.glob("*.partial.yaml"))


class TestItRefusesWhatItCannotTrace:

    def test_a_sheet_without_provenance_is_refused(
        self, tmp_path, monkeypatch, capsys
    ):
        """The same refusal `report_agreement.py` makes. A sheet that cannot
        say how it was built cannot be regenerated, so judgments entered
        against it are not checkable against anything."""
        path = tmp_path / "old.yaml"
        path.write_text(yaml.safe_dump({
            "instructions": "…",
            "decisions": [d.model_dump() for d in _rows()],
        }))
        monkeypatch.setattr(sys, "argv", ["judge", "--sheet", str(path)])
        assert judge.main() == 1
        assert "provenance" in capsys.readouterr().err

    def test_a_missing_sheet_is_refused(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            sys, "argv", ["judge", "--sheet", str(tmp_path / "nope.yaml")]
        )
        assert judge.main() == 1


@pytest.mark.skipif(
    not REAL_SHEET.exists(),
    reason=(
        "traces/ is gitignored, so the real sheet is absent in a fresh clone "
        "or worktree — see #114. The laws above stand on the fixture; this "
        "one only checks the shipped sheet still has the shape they assume."
    ),
)
def test_the_shipped_sheet_has_the_shape_these_laws_assume():
    sheet = read_decision_sheet(REAL_SHEET)
    assert sheet.provenance is not None
    kinds = [d.kind for d in sheet.decisions]
    assert kinds == sorted(kinds, key=lambda k: k != "matched"), (
        "the shipped sheet no longer groups matched rows first, so the order "
        "argument for the shuffle needs restating rather than assuming"
    )


def test_the_script_runs_as_a_script(tmp_path):
    """Imported and executed are different things, and this is executed."""
    path = write_decision_sheet(_rows(), tmp_path / "s.yaml", _provenance())
    result = subprocess.run(
        [sys.executable, "scripts/judge_decision_sheet.py",
         "--sheet", str(path), "--all"],
        input="q\n", capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "shuffled" in result.stdout


# ── the two halves of the instrument mean the same thing by --sheet ──

class TestTheReportReadsTheSheetItWasGiven:
    """`report_agreement.py` read one hardcoded path and never parsed argv, so
    `--sheet <other>` reported the default file's figures under the caller's
    filename. A silently-ignored flag does not fail — it answers plausibly
    about the wrong artifact, which is the harder thing to notice. It cost a
    false conclusion once: a judged copy reporting `0 / 38` read as the
    judgment vocabulary failing to reach the report, rather than as the report
    looking somewhere else.
    """

    def _report(self, sheet):
        return subprocess.run(
            [sys.executable, "scripts/report_agreement.py", "--sheet", str(sheet)],
            capture_output=True, text=True,
        )

    def test_the_named_sheet_is_the_one_reported_on(self, sheet_path, monkeypatch):
        _run(sheet_path, ["y"] * 6, monkeypatch)
        out = self._report(sheet_path).stdout
        assert "judged / unjudged                 6 / 0" in out, out

    def test_a_missing_named_sheet_is_refused_rather_than_defaulted(self, tmp_path):
        """The failure that must not fall back. Refusing is the only answer
        that cannot be mistaken for a report about the file you asked for."""
        result = self._report(tmp_path / "absent.yaml")
        assert result.returncode != 0
        assert "absent.yaml" in (result.stderr + result.stdout)

    def test_an_unknown_flag_is_an_error_not_a_no_op(self, sheet_path):
        result = subprocess.run(
            [sys.executable, "scripts/report_agreement.py",
             "--sheeet", str(sheet_path)],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert "unrecognized arguments" in result.stderr
