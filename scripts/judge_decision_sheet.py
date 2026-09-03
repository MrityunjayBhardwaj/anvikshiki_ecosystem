#!/usr/bin/env python3
"""Judge the decision sheet one pair at a time, without seeing the matcher.

Step one of #10, and the step no model may take: a model judging the
instrument that grades its own output reproduces the self-confirming loop the
whole audit exists to prevent. This script exists to make the human's half
cheap, not to do it.

    .venv/bin/python scripts/judge_decision_sheet.py

Three properties, and each is here because the alternative quietly corrupts
the measurement.

**Blind.** `matcher_says_match`, `score`, `veto_reason` and `kind` are never
shown. The sheet asks whether two predicates mean the same thing; showing the
answer the matcher gave turns that into a question about the matcher, which is
the quantity under test. Reading the YAML directly cannot be blind — the
verdict sits three lines above the field you type into.

**Shuffled.** The sheet is written matched-rows-first, so file order is itself
a perfect leak of `matcher_says_match`: the first five rows are the matcher's
five claimed matches and the remaining thirty-three are its near misses. A
judge working top to bottom learns the verdict from position alone, and
blinding the fields without shuffling the order would be blinding in name. The
seed is recorded and printed, so the ordering is reproducible.

**Resumable, and identified by pair.** Judgments are keyed to
`(gold, candidate)` rather than to row index, because that is the identity the
sheet's own provenance is built around — a sheet regenerated under different
parameters no longer corresponds to judgments stored by position.

The sheet lives under `traces/`, which is gitignored and has no git backup, so
every write goes through a timestamped copy first and lands atomically.
"""

from __future__ import annotations

import argparse
import os
import random
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anvikshiki_v4.instrument_validation import (  # noqa: E402
    MATCH,
    NO_MATCH,
    UNJUDGED,
    MatcherDecision,
    read_decision_sheet,
    write_decision_sheet,
)

DEFAULT_SHEET = "traces/instrument_validation/decision_sheet_ch02.yaml"

BOLD, DIM, RESET = "\033[1m", "\033[2m", "\033[0m"


def _plain(text: str) -> str:
    return text if sys.stdout.isatty() else ""


def _wrap(text: str, width: int = 76, indent: str = "    ") -> str:
    import textwrap

    if not text:
        return f"{indent}(no description)"
    return textwrap.fill(
        text, width=width, initial_indent=indent, subsequent_indent=indent
    )


def _render(decision: MatcherDecision, position: int, total: int) -> str:
    """One pair, and nothing the matcher thought about it."""
    b, d, r = _plain(BOLD), _plain(DIM), _plain(RESET)
    return (
        f"\n{d}── {position} of {total} ──────────────────────────────{r}\n"
        f"\n  {b}A{r}  {decision.gold}\n"
        f"{_wrap(decision.gold_description)}\n"
        f"\n  {b}B{r}  {decision.candidate}\n"
        f"{_wrap(decision.candidate_description)}\n"
        f"\n  Do A and B mean the same thing?\n"
    )


PROMPT = "  [y] yes   [n] no   [enter] unsure   [b] back   [q] save and quit  > "

ANSWERS = {"y": MATCH, "yes": MATCH, "n": NO_MATCH, "no": NO_MATCH, "": UNJUDGED}


def _order(decisions: list[MatcherDecision], seed: int) -> list[int]:
    """Presentation order: a recorded shuffle, not the file's own order.

    File order groups the matcher's claimed matches ahead of its near misses,
    so walking the sheet top to bottom tells the judge the verdict before they
    have read the pair.
    """
    indices = list(range(len(decisions)))
    random.Random(seed).shuffle(indices)
    return indices


def _save(sheet, decisions: list[MatcherDecision], path: Path) -> None:
    """Back up, write to a sibling, rename. The sheet is gitignored.

    Rebuilding it is not a recovery: the rows depend on parameters the rebuild
    would have to be given exactly, and judgments are keyed to the pairs on the
    sheet that was judged.
    """
    if path.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        shutil.copy2(path, path.with_suffix(f".{stamp}.bak.yaml"))
    temp = path.with_suffix(".partial.yaml")
    write_decision_sheet(decisions, temp, sheet.provenance)
    os.replace(temp, path)


def _counts(decisions: list[MatcherDecision]) -> tuple[int, int, int]:
    match = sum(1 for d in decisions if d.human == MATCH)
    no_match = sum(1 for d in decisions if d.human == NO_MATCH)
    return match, no_match, len(decisions) - match - no_match


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", default=DEFAULT_SHEET)
    parser.add_argument(
        "--seed", type=int, default=0,
        help="presentation-order seed; recorded so the order is reproducible",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="revisit rows already judged (default: only unjudged ones)",
    )
    args = parser.parse_args()

    path = Path(args.sheet)
    if not path.exists():
        print(f"No sheet at {path}", file=sys.stderr)
        return 1

    sheet = read_decision_sheet(path)
    if sheet.provenance is None:
        # The same refusal `report_agreement.py` makes, for the same reason:
        # a sheet that cannot say how it was built cannot be regenerated, and
        # judgments entered against it are not checkable against anything.
        print(
            f"{path} records no provenance, so nothing can say how it was "
            "built. Rebuild it with scripts/run_instrument_validation.py "
            "before judging.",
            file=sys.stderr,
        )
        return 1

    decisions = sheet.decisions
    queue = [
        i for i in _order(decisions, args.seed)
        if args.all or not decisions[i].judged
    ]

    print(f"sheet : {path}  ({len(decisions)} rows)")
    print(f"order : shuffled, seed {args.seed}")
    print(
        "\nYou are shown the two predicates and their descriptions, and "
        "nothing\nthe matcher thought about them — its verdict is what these "
        "judgments\nare measuring. Unsure is a real answer: unjudged rows are "
        "reported as\nunjudged and never counted either way."
    )

    if not queue:
        match, no_match, unjudged = _counts(decisions)
        print(f"\nNothing left to judge. {match} match, {no_match} no_match, "
              f"{unjudged} unjudged.")
        print("Run scripts/report_agreement.py for kappa.")
        return 0

    position = 0
    while 0 <= position < len(queue):
        decision = decisions[queue[position]]
        print(_render(decision, position + 1, len(queue)))
        if decision.judged:
            print(f"  {_plain(DIM)}currently: {decision.human}{_plain(RESET)}")

        try:
            answer = input(PROMPT).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\ninterrupted — saving what has been judged so far")
            break

        if answer == "q":
            break
        if answer == "b":
            position = max(0, position - 1)
            continue
        if answer not in ANSWERS:
            print(f"  {answer!r} is not one of y / n / enter / b / q")
            continue

        decisions[queue[position]] = decision.model_copy(
            update={"human": ANSWERS[answer]}
        )
        position += 1

    _save(sheet, decisions, path)
    match, no_match, unjudged = _counts(decisions)
    print(f"\nsaved to {path}")
    print(f"  match {match}   no_match {no_match}   unjudged {unjudged}")
    if unjudged:
        print(f"  {unjudged} left — rerun this script to continue where you "
              "stopped.")
    else:
        print("  All rows judged. Run scripts/report_agreement.py for kappa.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
