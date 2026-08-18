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

import argparse
import collections
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
from anvikshiki_v4.lattice import (
    CitationTier,
    should_drop_for_citation,
    status_of_rule,
    tier_for_citation,
)
from anvikshiki_v4.predicate_extraction import StageDConstructor, StageEValidator
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

KB = REPO_ROOT / "anvikshiki_v4" / "data" / "business_expert.yaml"
STAGE_A_CACHE = REPO_ROOT / "traces" / "instrument_validation" / "stage_a_ch02.json"
# The run that was actually asked to quote. The cache above predates span
# capture, so every candidate in it carries an empty quote and no rule built
# from it can reach ATTRIBUTED — which is a fact about when it was produced,
# not about the chapter.
STAGE_A_QUOTED = (
    REPO_ROOT / "traces" / "verbatim_rate" / "stage_a_ch02_verbatim.json"
)
OUT_DIR = REPO_ROOT / "traces" / "extraction_ch02"


def _load_stage_a(path: Path) -> StageAOutput:
    """Accept either a bare StageAOutput or one wrapped with run metadata."""
    blob = json.loads(path.read_text())
    return StageAOutput(**blob.get("stage_a", blob))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--stage-a",
        type=Path,
        default=STAGE_A_QUOTED if STAGE_A_QUOTED.exists() else STAGE_A_CACHE,
        help="Stage A output to trace (defaults to the quoted run when present)",
    )
    args = ap.parse_args()

    if not args.stage_a.exists():
        raise SystemExit(f"no cached Stage A run at {args.stage_a}")

    print(f"tracing {args.stage_a.relative_to(REPO_ROOT)}\n")
    stage_a = _load_stage_a(args.stage_a)
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

    # ── the citation tier, over the rules that reached the store ──
    print()
    print("─" * 66)
    print(f"citation tier over the {len(stored)} stored rule(s)")
    print("─" * 66)
    if not stored:
        print("no stored rules — nothing to tier, and no tier figure below "
              "would be a measurement")
    else:
        tiers = collections.Counter(
            tier_for_citation(v).value for v in stored
        )
        for tier in CitationTier:
            n = tiers.get(tier.value, 0)
            print(f"  {tier.value:12s} {n:3d} / {len(stored)}"
                  f"  ({100.0 * n / len(stored):5.1f}%)")

        statuses = collections.Counter(status_of_rule(v).value for v in stored)
        print()
        print(f"  effective status: {dict(statuses)}")

        dropped = [v for v in stored if should_drop_for_citation(v)]
        print(f"  would be dropped: {len(dropped)} / {len(stored)}")
        for v in dropped:
            print(f"    - {v.id} {v.name}")

    # The curated half, reported beside it. A tier run that silently ignored
    # the shipped knowledge base would look identical to one that found it
    # clean.
    curated = [v for v in ks.vyaptis.values() if not v.augmentation_metadata]
    print()
    print(f"curated rules in the base KB: {len(curated)}")
    if curated:
        c_tiers = collections.Counter(
            tier_for_citation(v).value for v in curated
        )
        c_drop = [v for v in curated if should_drop_for_citation(v)]
        print(f"  tiers           : {dict(c_tiers)}")
        print(f"  would be dropped: {len(c_drop)} / {len(curated)}")
        print("  (a hand-authored rule cites literature rather than a located")
        print("   span, so the citation axis does not bound it — see the tier")
        print("   named `curated` rather than reusing `attributed`)")

    print()
    print(f"stage D trace      : {(OUT_DIR / 'stage_d_ch02.json').relative_to(REPO_ROOT)}")
    print(f"stage E trace      : {(OUT_DIR / 'stage_e_ch02.json').relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
