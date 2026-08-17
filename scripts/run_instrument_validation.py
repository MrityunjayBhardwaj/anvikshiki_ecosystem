#!/usr/bin/env python
"""Run Stage A over one chapter and build the matcher decision sheet for #10.

Step one of the pre-registered protocol in
`discussions/instrument-validation-preregistration.md`: produce candidates,
pair them against the gold set, and write out the matcher's verdicts for a
human to confirm or overturn.

Only Stage A runs. Candidates are what the matcher is judged on, and B–E cost
more calls without changing a single decision on the sheet.

    python scripts/run_instrument_validation.py            # run and write sheet
    python scripts/run_instrument_validation.py --from-cache   # rebuild sheet only

The raw Stage A output is cached so the sheet can be rebuilt — with a
different match mode, say — without paying for extraction twice.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env")

import dspy

from anvikshiki_v4.extraction_gold import load_gold
from anvikshiki_v4.extraction_schema import ExtractionConfig, StageAOutput
from anvikshiki_v4.instrument_validation import (
    build_decision_sheet,
    write_decision_sheet,
)
from anvikshiki_v4.predicate_extraction import StageAExtractor
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

KB = REPO_ROOT / "anvikshiki_v4" / "data" / "business_expert.yaml"
CHAPTER = REPO_ROOT / "guides" / "business_expert" / "guide_ch2.md"
OUT_DIR = REPO_ROOT / "traces" / "instrument_validation"
STAGE_A_CACHE = OUT_DIR / "stage_a_ch02.json"
SHEET = OUT_DIR / "decision_sheet_ch02.yaml"

MODEL_ID = "openai/zai-org/GLM-5"
BASE_URL = "https://api.deepinfra.com/v1/openai"


def configure_lm() -> str:
    key = os.environ.get("DEEPINFRA_API_KEY")
    if not key:
        raise SystemExit("DEEPINFRA_API_KEY is not set — nothing to run with")
    dspy.configure(lm=dspy.LM(MODEL_ID, api_key=key, api_base=BASE_URL, max_tokens=16000))
    return MODEL_ID


def run_stage_a() -> tuple[StageAOutput, str]:
    model = configure_lm()
    ks = load_knowledge_store(str(KB))
    text = CHAPTER.read_text()

    print(f"model    : {model}")
    print(f"chapter  : {CHAPTER.relative_to(REPO_ROOT)}  ({len(text):,} chars)")
    print("running Stage A ...")

    stage_a = StageAExtractor(ks, ExtractionConfig())
    out = stage_a(chapter_text=text, chapter_id="ch02")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STAGE_A_CACHE.write_text(out.model_dump_json(indent=2))
    return out, model


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-cache", action="store_true",
                        help="rebuild the sheet from a previous run, no LLM calls")
    parser.add_argument("--match-on", default="name",
                        choices=["name", "description", "either"])
    args = parser.parse_args()

    if args.from_cache:
        if not STAGE_A_CACHE.exists():
            raise SystemExit(f"no cached run at {STAGE_A_CACHE}")
        out = StageAOutput(**json.loads(STAGE_A_CACHE.read_text()))
        model = "(cached)"
    else:
        out, model = run_stage_a()

    gold = load_gold()

    print()
    print("─" * 62)
    print(f"sections            : {out.section_count}")
    print(f"candidates returned : {len(out.candidates)}   ← precision denominator")
    print(f"gold predicates     : {len(gold)}   ← recall denominator")
    print(f"zero-predicate secs : {out.zero_predicate_sections}")
    print(f"failed sections     : {out.failed_sections}"
          f"{'  ← extraction errors, NOT thin prose' if out.failed_sections else ''}")
    for f in out.failures:
        print(f"    {f}")
    print("─" * 62)

    if not out.candidates:
        print("\nNo candidates. Nothing to judge, and no number to report.")
        return 1

    sheet = build_decision_sheet(
        gold_names=gold.names,
        gold_descriptions=gold.descriptions,
        candidates=[(c.name, c.description) for c in out.candidates],
        match_on=args.match_on,
    )
    write_decision_sheet(sheet, SHEET)

    matched = sum(1 for d in sheet if d.kind == "matched")
    near = sum(1 for d in sheet if d.kind == "near_miss")
    print(f"\ndecision sheet      : {SHEET.relative_to(REPO_ROOT)}")
    print(f"  {matched:>3} matched pairs   (precision claims)")
    print(f"  {near:>3} near misses     (recall claims)")
    print(f"  {matched + near:>3} rows to judge")
    print(f"\nmatch_on            : {args.match_on}")
    print(f"model               : {model}")
    print("\nNo precision or recall figure is printed here, deliberately. The")
    print("matcher has not been validated yet — that is what the sheet is for.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
