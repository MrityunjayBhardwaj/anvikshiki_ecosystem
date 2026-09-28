"""Command line: ask a question, or replay a stored run.

    python -m occam ask "question" [--url URL ...] [--k 3] [--sources 3] [--out FILE]
    python -m occam replay FILE

`ask` needs OPENROUTER_API_KEY. `replay` needs nothing but the file: it
recomputes the answer with no model and says whether it matches the stored one.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .answer import Answer, Artifact, Params, canonical, replay, run


def _show(a: Answer) -> None:
    print(f"\nQ: {a.question}")
    if a.abstained:
        print(f"ABSTAINED — {a.abstain_reason}")
    else:
        print(f"A: {a.conclusion}")
        print(f"   status: {a.status.value}   bound by: {'; '.join(a.status_bound_by)}")
        print(f"   {a.status_set_note}")
    for p in a.positions:
        print(f"   position [{p['status']}] ({p['samples']} samples): {p['conclusion']}")
    print("counters:")
    for name, c in a.counters.items():
        frac = f" = {c.frac:.2f}" if c.frac is not None and name.endswith("frac") else ""
        print(f"   {name:18} {c.n:g} of {c.of} {c.population}{frac}")
    for d in a.degraded:
        print(f"   degraded: {d}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="occam")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ask = sub.add_parser("ask")
    ask.add_argument("question")
    ask.add_argument("--url", action="append")
    ask.add_argument("--k", type=int, default=3)
    ask.add_argument("--sources", type=int, default=3)
    ask.add_argument("--model", default="z-ai/glm-5.2")
    ask.add_argument("--out")
    rp = sub.add_parser("replay")
    rp.add_argument("file")
    args = ap.parse_args(argv)

    if args.cmd == "ask":
        from .model import OpenRouterModel
        answer, artifact = run(args.question, OpenRouterModel(args.model), urls=args.url,
                               n_sources=args.sources,
                               params=Params(k_argue=args.k, k_attack=args.k))
        out = Path(args.out or f"traces/occam/{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"artifact": artifact.model_dump(mode="json"),
                                   "answer": json.loads(canonical(answer))}, indent=1))
        _show(answer)
        print(f"\nartifact: {out}")
        return 0

    stored = json.loads(Path(args.file).read_text())
    answer = replay(Artifact.model_validate(stored["artifact"]))
    same = canonical(answer) == json.dumps(stored["answer"], sort_keys=True, ensure_ascii=False)
    _show(answer)
    print(f"\nreplay {'MATCHES' if same else 'DIFFERS FROM'} the stored answer")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
