#!/usr/bin/env python
"""Report matcher-vs-human agreement once the decision sheet has been judged.

Step one of #10. Run after filling in `human:` on the sheet:

    python scripts/report_agreement.py

Reports observed agreement, Cohen's kappa, and the two disagreement classes
separately — they are not symmetric, and only one of them argues for adopting
a semantic encoder.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from anvikshiki_v4.extraction_gold import load_gold
from anvikshiki_v4.instrument_validation import (
    agreement,
    read_decision_sheet,
    replay_mode,
)

SHEET = REPO_ROOT / "traces" / "instrument_validation" / "decision_sheet_ch02.yaml"
KAPPA_KILL = 0.6   # registered in discussions/instrument-validation-preregistration.md


def _line(label: str, value) -> None:
    print(f"  {label:<34}{value}")


def main() -> int:
    if not SHEET.exists():
        raise SystemExit(f"no sheet at {SHEET} — run run_instrument_validation.py first")

    decisions = read_decision_sheet(SHEET)
    gold = load_gold()

    print(f"sheet: {SHEET.relative_to(REPO_ROOT)}  ({len(decisions)} rows)\n")

    reports = {}
    for mode in ("name", "description", "either"):
        replayed = replay_mode(decisions, gold.descriptions, match_on=mode)
        reports[mode] = agreement(replayed)

    for mode, r in reports.items():
        print(f"── match_on = {mode} " + "─" * (44 - len(mode)))
        _line("judged / unjudged", f"{r.judged} / {r.unjudged}")
        if not r.judged:
            print("  nothing judged — no agreement to report\n")
            continue
        _line("observed agreement", f"{r.observed_agreement:.3f}")
        _line(
            "Cohen's kappa",
            f"{r.cohens_kappa:.3f}" if r.cohens_kappa is not None
            else f"undefined — {r.kappa_undefined_reason}",
        )
        _line("both say match", r.both_match)
        _line("both reject", r.both_reject)
        _line("matcher yes / human no", f"{r.matcher_only}   ← precision failure")
        _line("matcher no / human yes", f"{r.human_only}   ← the only encoder evidence")
        print()

    judged_any = any(r.judged for r in reports.values())
    if not judged_any:
        print("Nothing has been judged. No extraction number may be reported.")
        return 1

    print("─" * 62)
    best = max(
        (m for m, r in reports.items() if r.cohens_kappa is not None),
        key=lambda m: reports[m].cohens_kappa,
        default=None,
    )
    if best is None:
        print("No mode produced a defined kappa. Read the observed agreement and")
        print("the disagreement counts directly; the aggregate cannot be summarised.")
        return 1

    k = reports[best].cohens_kappa
    print(f"best-agreeing mode : {best}  (kappa {k:.3f})")

    if k < KAPPA_KILL:
        print(f"\nKAPPA BELOW THE REGISTERED KILL CRITERION ({KAPPA_KILL}).")
        print("The matcher and the human do not agree well enough for the")
        print("matcher's verdicts to stand in for judgment. No extraction number")
        print("is reported from this instrument. That is the finding.")
        return 1

    encoder = reports[best].semantic_encoder_is_indicated
    print(f"\nsemantic encoder indicated : {encoder}")
    if not encoder:
        print("  No human-yes/matcher-no disagreements, so nothing here argues")
        print("  for the ~2GB dependency. Registered in advance: it is not adopted.")

    print("\nInstrument validated. Step two of #10 may proceed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
