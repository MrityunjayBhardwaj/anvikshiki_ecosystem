#!/usr/bin/env python
"""Run Stage D and E over the cached Stage A output and record what survives.

There was no Stage D or E output anywhere in `traces/` — only the Stage A
cache and the decision sheet — so the claim that provenance is dropped when a
candidate becomes a rule was read off the construction sites rather than
confirmed against a run. This produces the missing artifact.

    python scripts/trace_stage_d_provenance.py

**No model is called.** Stage B and Stage C are bypassed: with no Stage B
nodes, Stage D's first loop — the only one that calls the constructor — does
nothing, and the standalone branch runs purely locally over the candidates
already on disk. The vocabulary is therefore the candidate names as extracted
rather than a canonicalised set.

What that costs, stated so the trace is not read as more than it is: the
sub-rule path is not exercised here, so its provenance collection is covered
by tests and not by this artifact. What it buys is that the numbers below come
from the 24 real candidates of ch02 rather than from fixtures.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from anvikshiki_v4.extraction_schema import (
    ExtractionConfig,
    StageAOutput,
    StageBOutput,
    StageCOutput,
)
from anvikshiki_v4.predicate_extraction import StageDConstructor, StageEValidator
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

KB = REPO_ROOT / "anvikshiki_v4" / "data" / "business_expert.yaml"
STAGE_A_CACHE = REPO_ROOT / "traces" / "instrument_validation" / "stage_a_ch02.json"
OUT_DIR = REPO_ROOT / "traces" / "extraction_ch02"


def main() -> int:
    if not STAGE_A_CACHE.exists():
        raise SystemExit(f"no cached Stage A run at {STAGE_A_CACHE}")

    stage_a = StageAOutput(**json.loads(STAGE_A_CACHE.read_text()))
    ks = load_knowledge_store(str(KB))

    stage_d = StageDConstructor(ks, ExtractionConfig())
    stage_d_out = stage_d(
        stage_a=stage_a,
        stage_b=StageBOutput(nodes={}),
        stage_c=StageCOutput(vocabulary=[c.name for c in stage_a.candidates]),
        guide_text={},
    )

    rules = stage_d_out.new_vyaptis + stage_d_out.refinement_vyaptis

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "stage_d_ch02.json").write_text(stage_d_out.model_dump_json(indent=2))

    validator = StageEValidator(ks)
    merged = validator.validate_and_merge(stage_d_out)
    augmented = merged[0] if isinstance(merged, tuple) else merged
    stored = [v for v in augmented.vyaptis.values() if v.augmentation_metadata]
    (OUT_DIR / "stage_e_ch02.json").write_text(json.dumps(
        {v.id: json.loads(v.model_dump_json()) for v in stored}, indent=2
    ))

    print("─" * 66)
    print(f"candidates in      : {len(stage_a.candidates)}")
    print(f"rules out of D     : {len(rules)}")
    print(f"stored by E        : {len(stored)}")
    print("─" * 66)

    # The three states kept apart, because only one of them is a fact about
    # the corpus. "No provenance" used to be the only possible answer and it
    # was produced by our own plumbing.
    never = [r for r in rules if not r.provenance_attached]
    looked_empty = [r for r in rules if r.provenance_attached and not r.provenance]
    carried = [r for r in rules if r.provenance]
    print(f"never attached     : {len(never)}   <- was 100% before this fix")
    print(f"attached, none found: {len(looked_empty)}")
    print(f"carrying a record  : {len(carried)}")

    with_locator = [r for r in carried if any(p.chapter_id or p.doc_url for p in r.provenance)]
    with_quote = [r for r in carried if any(p.quote for p in r.provenance)]
    checked = [r for r in carried
               if any(p.quote_found_in_source is not None for p in r.provenance)]
    print()
    print(f"  with a locator   : {len(with_locator)}")
    print(f"  with a quote     : {len(with_quote)}")
    print(f"  quote checked    : {len(checked)}")
    print()
    print("A rule reaches #19's ATTRIBUTED tier only with a quote that was")
    print("found in the source. Where the quote count is 0 the reason is now")
    print("visible in the artifact rather than absent from it.")

    print()
    print(f"stage D trace      : {(OUT_DIR / 'stage_d_ch02.json').relative_to(REPO_ROOT)}")
    print(f"stage E trace      : {(OUT_DIR / 'stage_e_ch02.json').relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
