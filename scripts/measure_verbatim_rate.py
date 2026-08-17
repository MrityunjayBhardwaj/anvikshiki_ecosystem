#!/usr/bin/env python
"""Measure how often extraction quotes its source verbatim, and how long the
quotes are.

`MIN_DISCRIMINATING_LENGTH = 24` is a guess. Nothing has measured the lengths a
model actually returns, and #18 is about to drop candidates on that number. This
script produces the distribution the threshold should be chosen from, plus the
four-way split of what happened to each quote.

    python scripts/measure_verbatim_rate.py             # live run, 7 calls
    python scripts/measure_verbatim_rate.py --from-cache  # re-analyse, 0 calls

Everything after the run is recomputed from the persisted quotes and the
sections re-derived from the chapter, so choosing a different threshold costs
nothing. The one live run is the only thing that spends.

Two rules this script exists to obey
────────────────────────────────────
**It never writes to `traces/instrument_validation/`.** That directory holds the
Stage A output pinned by SHA-256 inside the decision sheet currently awaiting
judgment. Overwriting it would leave a judged sheet describing candidates that
no longer exist. The output path is asserted to be elsewhere and the pinned
file's hash is checked before and after the run.

**Every count is printed as `n / N`.** A bare zero cannot be told apart from a
measurement that never ran, and this repo has produced that exact confusion in
its own measuring tools twice. The denominator travels with the number.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env")

from anvikshiki_v4.extraction_schema import ExtractionConfig, StageAOutput
from anvikshiki_v4.span_verification import (
    MIN_DISCRIMINATING_LENGTH,
    diagnose,
    normalise_whitespace,
    quote_appears_in,
)

KB = REPO_ROOT / "anvikshiki_v4" / "data" / "business_expert.yaml"
CHAPTER = REPO_ROOT / "guides" / "business_expert" / "guide_ch2.md"
CHAPTER_ID = "ch02"

OUT_DIR = REPO_ROOT / "traces" / "verbatim_rate"
STAGE_A_OUT = OUT_DIR / "stage_a_ch02_verbatim.json"
REPORT_OUT = OUT_DIR / "verbatim_rate_ch02.md"

# Pinned by hash inside traces/instrument_validation/decision_sheet_ch02.yaml.
# Read-only from here, and checked rather than trusted.
PROTECTED = REPO_ROOT / "traces" / "instrument_validation" / "stage_a_ch02.json"

MODEL_ID = "openai/zai-org/GLM-5"
BASE_URL = "https://api.deepinfra.com/v1/openai"

# The thresholds worth asking about. 24 is the incumbent guess and is in the
# list so it can be read off the same curve as its alternatives rather than
# compared against them from memory.
SWEEP = [0, 8, 12, 16, 20, 24, 30, 40, 60, 80, 120]


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pct(n: int, d: int) -> str:
    """`n / d` with a percentage, or an explicit refusal when d is zero.

    A rate over an empty denominator is not 0% — it is unmeasured, and the two
    have been confused in this repo's own tooling. Say so instead.
    """
    if d == 0:
        return f"{n} / 0 (no denominator — nothing was measured)"
    return f"{n} / {d} ({100.0 * n / d:.1f}%)"


# ── the run ──────────────────────────────────────────────────────────


def run_stage_a() -> tuple[StageAOutput, str, int]:
    """One live Stage A pass. Returns the output, the model id, and max_tokens."""
    import dspy

    from anvikshiki_v4.predicate_extraction import StageAExtractor, _split_into_sections
    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

    # Checked before the loop, not inside it. Without a key every section
    # raises, `failed_sections` reaches 7 of 7, and the run still writes a
    # complete report — a page of quote statistics over zero candidates. The
    # denominators keep that page honest, but a run that cannot possibly
    # measure anything should not start.
    key = os.environ.get("DEEPINFRA_API_KEY")
    if not key:
        raise SystemExit(
            "DEEPINFRA_API_KEY is not set — refusing to run. Every section "
            "would fail authentication and the report would describe an "
            "extraction that never happened."
        )

    lm = dspy.LM(MODEL_ID, api_key=key, api_base=BASE_URL, max_tokens=16000)
    dspy.configure(lm=lm)

    ks = load_knowledge_store(KB)
    config = ExtractionConfig()
    extractor = StageAExtractor(ks, config)

    max_tokens = 512 if config.model_tier == "small" else 2000
    chapter_text = CHAPTER.read_text()
    sections = _split_into_sections(chapter_text, max_tokens=max_tokens)
    billable = sum(1 for s in sections if len(s.strip().split()) >= 20)

    print(f"chapter    {CHAPTER.relative_to(REPO_ROOT)}  {len(chapter_text)} chars")
    print(f"sections   {len(sections)}, of which {billable} get a call "
          f"({len(sections) - billable} skipped by the 20-word guard)")
    print(f"model      {MODEL_ID}\n")
    print(f"running {billable} live calls…", flush=True)

    out = extractor.forward(chapter_text=chapter_text, chapter_id=CHAPTER_ID)
    return out, MODEL_ID, max_tokens


# ── the analysis, which costs nothing ────────────────────────────────


def sections_for(max_tokens: int) -> list[str]:
    """Re-derive the exact sections the run was given.

    `_split_into_sections` is a pure function of the chapter text and the token
    budget, so the section a candidate was checked against can be recovered
    from its `paragraph_index` without storing it. That is what makes the whole
    analysis re-runnable for zero calls.
    """
    from anvikshiki_v4.predicate_extraction import _split_into_sections

    return _split_into_sections(CHAPTER.read_text(), max_tokens=max_tokens)


def analyse(out: StageAOutput, sections: list[str]) -> dict:
    rows = []
    for c in out.candidates:
        quote = c.provenance.quote or ""
        idx = c.provenance.paragraph_index
        section = sections[idx] if 0 <= idx < len(sections) else ""
        rows.append(
            {
                "name": c.name,
                "section": idx,
                "quote": quote,
                "length": len(normalise_whitespace(quote)),
                # Recomputed here rather than read off the stored flag. The
                # stored one was decided at capture time under the incumbent
                # threshold, and the point of this script is to vary that.
                "found": quote_appears_in(quote, section),
                "verdict": diagnose(quote, section) or "verbatim",
            }
        )
    return {"rows": rows}


def report(out: StageAOutput, rows: list[dict], sections: list[str],
           model: str, max_tokens: int) -> str:
    L: list[str] = []
    w = L.append

    n = len(rows)
    billable = sum(1 for s in sections if len(s.strip().split()) >= 20)

    w("# Verbatim quote rate — business_expert ch02\n")
    w(f"Measured {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n")
    w(f"- model: `{model}`")
    w(f"- chapter: `{CHAPTER.relative_to(REPO_ROOT)}`, "
      f"{len(CHAPTER.read_text())} chars")
    w(f"- sections: {len(sections)}, called: {billable}, "
      f"section budget: {max_tokens} tokens")
    w(f"- candidates: **{n}**")
    w(f"- incumbent threshold: `MIN_DISCRIMINATING_LENGTH = "
      f"{MIN_DISCRIMINATING_LENGTH}`\n")

    if not out.quotes_checked:
        w("> **`quotes_checked` is False — every count below is meaningless.**")
        w("> This output predates span capture and nothing was checked.\n")

    if billable and out.failed_sections == billable:
        w(f"> **Every section failed ({pct(out.failed_sections, billable)}).**")
        w("> Nothing was extracted, so nothing below is a measurement of the "
          "extractor. The failures are listed under the next heading and they "
          "are the only finding this run supports.\n")

    w("## Did the run itself hold together\n")
    w(f"- sections with no predicate: {pct(out.zero_predicate_sections, billable)}")
    w(f"- sections that errored: {pct(out.failed_sections, billable)}")
    w(f"- sections truncated: {pct(out.truncated_sections, billable)}"
      f"  (checked: {out.truncation_checked})")
    for f in out.failures:
        w(f"  - failure: {f}")
    for t in out.truncations:
        w(f"  - truncation: {t}")
    w("")

    w("## Where the quotes went\n")
    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    order = [
        "verbatim",
        "too short to discriminate",
        "punctuation",
        "markup",
        "punctuation and markup",
        "absent",
        "empty",
    ]
    w("| verdict | count | meaning |")
    w("|---|---|---|")
    meaning = {
        "verbatim": "found in the section and long enough to mean something",
        "too short to discriminate": "found, but too short for finding it to prove anything",
        "punctuation": "matches once curly quotes and dashes are folded — a rendering artefact, not an invention",
        "markup": "matches once markdown emphasis is stripped — the model quoted the prose and dropped the `**`",
        "punctuation and markup": "both of the above at once",
        "absent": "**the words are not in the section at all — this is the fabrication number**",
        "empty": "the model returned no quote for this predicate",
    }
    for v in order:
        w(f"| `{v}` | {pct(counts.get(v, 0), n)} | {meaning[v]} |")
    for v in sorted(set(counts) - set(order)):
        w(f"| `{v}` | {pct(counts[v], n)} | — |")
    w("")

    w("### The two ways a quote can be missing\n")
    empty_seen = counts.get("empty", 0)
    if not out.quotes_checked:
        # These two counters did not exist when a pre-capture run was written,
        # so they load as 0 — which would read as "no candidate lacked a
        # quote" directly beneath a table saying every one of them did. The
        # counter's default is not a measurement.
        w(f"- model returned an empty quote: **not measured** "
          f"(this run predates the counter; {empty_seen} of {n} quotes are "
          f"empty, but nothing recorded why)")
        w("- our zip ran off a short `quotes` list: **not measured**, same reason")
    else:
        w(f"- model returned an empty quote: "
          f"{pct(out.quoteless_candidates, n)}")
        w(f"- our zip ran off a short `quotes` list: "
          f"{pct(out.unquoted_by_short_list, n)}")
        # The two reasons partition the empty quotes, so they must sum to the
        # verdict table's `empty` row. Checked on the page rather than left for
        # a reader to notice, because a breakdown that silently disagrees with
        # the total it breaks down is worse than no breakdown.
        split = out.quoteless_candidates + out.unquoted_by_short_list
        if split != empty_seen:
            w("")
            w(f"> **These do not add up.** {out.quoteless_candidates} + "
              f"{out.unquoted_by_short_list} = {split}, but the verdict table "
              f"counts {empty_seen} empty quotes out of {n}. One of the two "
              "is wrong and the split cannot be read until that is resolved.")
    w("")
    w("The second is ours, not the model's. It is reported apart from the first "
      "because a padded index and a declined citation both arrive as `\"\"`, and "
      "a rate that mixes them describes our plumbing while reading as a fact "
      "about the extractor.")
    w("")
    w("Neither figure detects an omitted **middle** element, which shifts every "
      "quote after it onto the wrong predicate while leaving the list lengths "
      "equal. A shifted quote still passes the verbatim check, because it is a "
      "real span attached to the wrong claim.")
    w("")

    w("## Quote length distribution\n")
    lengths = sorted(r["length"] for r in rows if r["length"] > 0)
    if not lengths:
        w(f"**No candidate carried a non-empty quote ({pct(0, n)}).** "
          "There is no distribution to report and no threshold can be chosen "
          "from this run.\n")
    else:
        w(f"Over the {pct(len(lengths), n)} candidates with a non-empty quote, "
          "in characters after whitespace normalisation:\n")
        qs = statistics.quantiles(lengths, n=4) if len(lengths) >= 4 else []
        w("| statistic | chars |")
        w("|---|---|")
        w(f"| min | {lengths[0]} |")
        if qs:
            w(f"| 25th pct | {qs[0]:.0f} |")
        w(f"| median | {statistics.median(lengths):.0f} |")
        if qs:
            w(f"| 75th pct | {qs[2]:.0f} |")
        w(f"| max | {lengths[-1]} |")
        w(f"| mean | {statistics.fmean(lengths):.1f} |")
        w("")

    w("## Threshold sweep — what #18 would drop\n")
    w("For each candidate threshold T: how many quotes fall below it, and how "
      "many of *those* were genuinely present in the source. The second column "
      "is the cost of the threshold — real citations discarded for being "
      "short.\n")
    w("| T | below T | of those, verbatim in source | at or above T **and** verbatim |")
    w("|---|---|---|---|")
    for t in SWEEP:
        below = [r for r in rows if r["length"] < t]
        below_found = [r for r in below if r["found"]]
        usable = [r for r in rows if r["length"] >= t and r["found"]]
        mark = " ←incumbent" if t == MIN_DISCRIMINATING_LENGTH else ""
        w(f"| {t}{mark} | {pct(len(below), n)} | {pct(len(below_found), len(below))} "
          f"| {pct(len(usable), n)} |")
    w("")

    w("## Negative control — the bibliography\n")
    w("The pre-registration names a stretch of bibliography as the negative "
      "control: any predicate extracted from it is a false positive. Reported "
      "apart from the rate rather than folded into it.\n")

    # Kept apart on purpose. `### REFERENCES` is a numbered citation list and
    # is the control. `### Going Deeper` sits next to it and looks like more
    # of the same, but it is prose carrying real claims — counting the two
    # together would score genuine extractions as control failures and make
    # the control read as failed when it passed.
    control = [
        i for i, s in enumerate(sections)
        if s.lstrip().startswith("### REFERENCES")
    ]
    adjacent = [
        i for i, s in enumerate(sections)
        if s.lstrip().startswith("### Going Deeper")
    ]

    w(f"**Control — `### REFERENCES`, section(s) "
      f"{control if control else 'none identified'}.** A numbered citation "
      "list. Nothing here is a claim.\n")
    if control:
        hits = [r for r in rows if r["section"] in control]
        verdict = "**PASSED**" if not hits else "**FAILED**"
        w(f"Predicates extracted from it: {pct(len(hits), n)} — {verdict}")
        for r in hits:
            w(f"  - section {r['section']}: `{r['name']}` — {r['verdict']}")
    else:
        w("Section not found — the control did not run, which is not the "
          "same as passing.")
    w("")

    w(f"**Not a control — `### Going Deeper`, section(s) "
      f"{adjacent if adjacent else 'none'}.** Adjacent to the references and "
      "similar in shape, but prose making substantive claims. Listed so it is "
      "not silently scored either way.\n")
    for r in [r for r in rows if r["section"] in adjacent]:
        w(f"  - section {r['section']}: `{r['name']}` — {r['verdict']}")
    w("")

    w("## Every candidate\n")
    w("| # | section | predicate | len | verdict | quote |")
    w("|---|---|---|---|---|---|")
    for k, r in enumerate(rows):
        q = r["quote"].replace("|", "\\|").replace("\n", " ")
        if len(q) > 90:
            q = q[:90] + "…"
        w(f"| {k} | {r['section']} | `{r['name']}` | {r['length']} "
          f"| {r['verdict']} | {q} |")
    w("")
    return "\n".join(L)


# ── entry ────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--from-cache",
        action="store_true",
        help="re-analyse the last run without spending any calls",
    )
    args = ap.parse_args()

    # The output must not land in the directory whose contents a pending
    # decision sheet pins by hash. Not an `assert`: `python -O` strips those,
    # and a guard that disappears under an optimisation flag is not a guard.
    if PROTECTED.parent in (STAGE_A_OUT.parent, REPORT_OUT.parent):
        raise SystemExit(
            f"refusing to write into {PROTECTED.parent}, which holds artifacts "
            "pinned by the decision sheet awaiting judgment"
        )
    protected_before = sha256_of(PROTECTED) if PROTECTED.exists() else None

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.from_cache:
        if not STAGE_A_OUT.exists():
            print(f"no cached run at {STAGE_A_OUT} — run without --from-cache first")
            return 1
        blob = json.loads(STAGE_A_OUT.read_text())
        out = StageAOutput.model_validate(blob["stage_a"])
        model = blob.get("model", "unknown")
        max_tokens = blob.get("section_max_tokens", 2000)

        # Every verdict below is recomputed against sections re-derived from
        # the chapter *on disk now*. If it has moved since the run, the quotes
        # are being checked against text they were never taken from and the
        # whole report is quietly about a different document. Recording the
        # hash and not checking it is the appearance of a guarantee.
        recorded = blob.get("chapter_sha256", "")
        actual = sha256_of(CHAPTER)
        if not recorded:
            print("WARNING: this run recorded no chapter hash, so it cannot be "
                  "confirmed that the chapter is the one it was measured "
                  "against.\n")
        elif recorded != actual:
            raise SystemExit(
                f"refusing to re-analyse: {CHAPTER.relative_to(REPO_ROOT)} has "
                f"changed since the run.\n"
                f"  recorded {recorded[:16]}…\n"
                f"  on disk  {actual[:16]}…\n"
                "Every verdict would be recomputed against text the quotes "
                "were not taken from. Re-run without --from-cache."
            )
        print(f"re-analysing {STAGE_A_OUT.relative_to(REPO_ROOT)} — no calls made")
        print(f"chapter hash matches the run: {actual[:16]}…\n")
    else:
        out, model, max_tokens = run_stage_a()
        STAGE_A_OUT.write_text(
            json.dumps(
                {
                    "model": model,
                    "section_max_tokens": max_tokens,
                    "chapter": str(CHAPTER.relative_to(REPO_ROOT)),
                    "chapter_sha256": sha256_of(CHAPTER),
                    "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "stage_a": out.model_dump(mode="json"),
                },
                indent=2,
            )
        )
        print(f"\nwrote {STAGE_A_OUT.relative_to(REPO_ROOT)}")

    sections = sections_for(max_tokens)
    rows = analyse(out, sections)["rows"]
    text = report(out, rows, sections, model, max_tokens)
    REPORT_OUT.write_text(text)
    print(text)
    print(f"\nwrote {REPORT_OUT.relative_to(REPO_ROOT)}")

    # Checked, not assumed. The whole reason this script has its own output
    # directory is that this file must survive the run untouched.
    if protected_before is not None:
        after = sha256_of(PROTECTED)
        status = "UNCHANGED" if after == protected_before else "*** MODIFIED ***"
        print(f"\npinned {PROTECTED.relative_to(REPO_ROOT)}: {status} "
              f"({after[:16]}…)")
        if after != protected_before:
            return 1
    else:
        print(f"\npinned {PROTECTED.relative_to(REPO_ROOT)}: absent before the run")

    # A run where every section failed produced a report of zeros. The
    # denominators say so on the page, but the exit status has to say so too —
    # anything scripting this must not read "wrote the report" as "measured
    # the rate".
    billable = sum(1 for s in sections if len(s.strip().split()) >= 20)
    if billable and out.failed_sections == billable:
        print(f"\nFAILED: every called section errored "
              f"({out.failed_sections} / {billable}). Nothing was measured.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
