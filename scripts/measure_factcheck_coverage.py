#!/usr/bin/env python
"""How much Google Fact Check Tools has to say about Occam's questions (#190).

Searches `claims:search` for every question in the built-in ten and in each
held-out set, plus the adversarial claim and a positive control that must
hit, and prints the number of claims returned per query. Each question is
searched twice: as asked, and with its question words dropped, because the
service matches words and a miss on the full sentence might be the wording.

    python scripts/measure_factcheck_coverage.py --out traces/factcheck/coverage.json
    python scripts/measure_factcheck_coverage.py --from traces/factcheck/coverage.json

A hit is not coverage. The service returns any fact-check sharing a word with
the query, so a count says only that something came back; whether a review
states the answer has to be read (the reading for 2026-10-12 is on #190).

Two rules this script keeps
───────────────────────────
**A failed search is never a zero.** It is printed as ERR with its reason, so
"could not look" never reads as "nothing found". A count at the page cap is
printed as "≥N".

**The API key is read from GOOGLE_FACTCHECK_API_KEY and written nowhere.**
occam.factcheck reports a failure by status alone.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from occam.controls import ADVERSARIAL_PAGE, FACTUAL_QUESTIONS
from occam.factcheck import FactCheckError, claims

QUESTION_SETS = ("occam/questions/held-out-1.txt", "occam/questions/held-out-2.txt")
POSITIVE_CONTROL = "vaccines cause autism"
PAGES = 3
STOP = frozenset(
    "a an the of in on at to and or is are was were did do does what why who when where "
    "how which according leading main first successful cause causes caused".split())


def read_set(path: str) -> list[str]:
    return [line.strip() for line in Path(path).read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def keywords(question: str) -> str:
    words = "".join(ch if ch.isalnum() else " " for ch in question).split()
    return " ".join(w for w in words if w.lower() not in STOP)


def queries() -> list[tuple[str, str]]:
    out = [("builtin", q) for q in FACTUAL_QUESTIONS]
    for path in QUESTION_SETS:
        out += [(Path(path).stem, q) for q in read_set(path)]
    out.append(("adversarial", ADVERSARIAL_PAGE.split(". ")[0]))
    out.append(("control", POSITIVE_CONTROL))
    return out


def search(query: str, key: str) -> dict:
    for attempt in range(4):
        try:
            found, _, more = claims(query, key=key, pages=PAGES)
            return {"n": len(found), "capped": more, "claims": found}
        except FactCheckError as e:
            if attempt == 3:
                return {"n": None, "error": str(e), "claims": []}
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def show(rows: list[dict]) -> int:
    for r in rows:
        n = "ERR" if r["n"] is None else (f"≥{r['n']}" if r.get("capped") else str(r["n"]))
        top = r["claims"][0].get("text", "")[:70] if r["claims"] else r.get("error", "")
        print(f"{r['set']:<11} {r['form']:<8} {n:>4}  {r['query'][:55]:<55} | {top}")
    asked = [r for r in rows if r["form"] == "as asked" and r["set"] not in ("adversarial", "control")]
    errors = sum(r["n"] is None for r in rows)
    either = {r["question"] for r in rows if r["set"] not in ("adversarial", "control") and r["n"]}
    control = [r for r in rows if r["set"] == "control"]
    print(f"\nquestions with at least one claim returned, either form: {len(either)} / {len(asked)}")
    print(f"searches that failed: {errors} / {len(rows)}")
    ok = bool(control) and all(r["n"] for r in control)
    print(f"positive control {POSITIVE_CONTROL!r}: {'hit' if ok else 'MISSED — the counts mean nothing'}")
    return 0 if ok and not errors else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", help="where to write every reply (live run)")
    ap.add_argument("--from", dest="src", help="re-print a stored run; no calls")
    args = ap.parse_args(argv)
    if args.src:
        return show(json.loads(Path(args.src).read_text())["rows"])
    key = os.environ.get("GOOGLE_FACTCHECK_API_KEY", "").strip()
    if not key or not args.out:
        print("needs GOOGLE_FACTCHECK_API_KEY and --out", file=sys.stderr)
        return 2
    out = Path(args.out)
    if out.exists():
        print(f"refusing to write over {out}", file=sys.stderr)
        return 2
    rows = []
    for set_name, q in queries():
        forms = [("as asked", q)] + ([("keywords", keywords(q))] if keywords(q) != q else [])
        for form, query in forms:
            rows.append({"set": set_name, "question": q, "form": form, "query": query,
                         **search(query, key)})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"at": datetime.now(timezone.utc).isoformat(), "rows": rows}, indent=1))
    code = show(rows)
    print(f"written {out}")
    return code


if __name__ == "__main__":
    sys.exit(main())
