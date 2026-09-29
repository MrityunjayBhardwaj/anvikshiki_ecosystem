"""Command line: ask a question, or replay a stored run.

    python -m occam ask "question" [--url URL ...] [--k 3] [--sources 3] [--out FILE]
    python -m occam replay FILE [--calibration CAL]
    python -m occam controls [--out DIR]     # the three validation controls, live
    python -m occam measure [--out DIR]      # the pre-registered factual set, live
    python -m occam probe-judge              # the support judge on its 12-pair probe, live
    python -m occam calibrate LABELS.jsonl --population "..." [--alpha 0.1] [--out CAL]

LABELS.jsonl has one {"artifact": FILE, "label": STATUS} per line — a person's
judgment of how much the answer in FILE is worth, after reading it and its
quotes.

`ask` needs OPENROUTER_API_KEY. `replay` needs nothing but the file: it
recomputes the answer with no model and says whether it matches the stored one.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .answer import Answer, Artifact, Params, canonical, replay, run, stored_run
from .conformal import ABSTAINED, Calibration, Example, fit


def _show(a: Answer) -> None:
    print(f"\nQ: {a.question}")
    if a.abstained:
        print(f"ABSTAINED — {a.abstain_reason}")
    else:
        print(f"A: {a.conclusion}")
        print(f"   status: {a.status.value}   bound by: {'; '.join(a.status_bound_by)}")
        if a.status_set is not None:
            print(f"   status set: {{{', '.join(s.value for s in a.status_set)}}}")
        print(f"   {a.status_set_note}")
    for p in a.positions:
        print(f"   position [{p['status']}] ({p['samples']} samples): {p['conclusion']}")
    print("counters:")
    for name, c in a.counters.items():
        frac = f" = {c.frac:.2f}" if c.frac is not None and name.endswith("frac") else ""
        print(f"   {name:18} {c.n:g} of {c.of} {c.population}{frac}")
    for d in a.degraded:
        print(f"   degraded: {d}")


def _refuse_overwrite(paths: list[Path]) -> bool:
    """True (and says so) if any artifact would be written over. Checked before
    a model is built: a registered run's artifacts are gitignored, so one
    overwritten is gone, and every figure citing it with it (#168)."""
    held = [p for p in paths if p.exists()]
    for p in held:
        print(f"refusing to overwrite {p}", file=sys.stderr)
    if held:
        print("choose a new --out; artifacts from earlier runs are never replaced",
              file=sys.stderr)
    return bool(held)


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
    ask.add_argument("--calibration")
    rp = sub.add_parser("replay")
    rp.add_argument("file")
    rp.add_argument("--calibration")
    ct = sub.add_parser("controls")
    ct.add_argument("--out")
    sub.add_parser("probe-judge")
    ms = sub.add_parser("measure")
    ms.add_argument("--out")
    cp = sub.add_parser("calibrate")
    cp.add_argument("labels")
    cp.add_argument("--population", required=True)
    cp.add_argument("--alpha", type=float, default=0.1)
    cp.add_argument("--out", default="traces/occam/calibration.json")
    args = ap.parse_args(argv)
    cal = None
    if getattr(args, "calibration", None):
        cal = Calibration.model_validate_json(Path(args.calibration).read_text())

    if args.cmd == "controls":
        from .controls import CONTROLS, run_control, verdict
        from .model import OpenRouterModel
        now = datetime.now(timezone.utc)
        outdir = Path(args.out or f"traces/occam/controls-{now:%Y%m%dT%H%M%SZ}")
        if _refuse_overwrite([outdir / f"control-{c.name}.json" for c in CONTROLS]):
            return 2
        model = OpenRouterModel()
        outdir.mkdir(parents=True, exist_ok=True)
        results = []
        for c in CONTROLS:
            r = run_control(c, model, as_of=now)
            results.append(r)
            (outdir / f"control-{c.name}.json").write_text(stored_run(r.answer, r.artifact))
            vf = r.answer.counters["verified_frac"]
            print(f"{c.name:12} {'PASS' if r.passed else 'FAIL'}  {r.observed}  "
                  f"(verified {vf.n:g} of {vf.of} quotes)")
            if not r.passed:
                print(f"{'':12} → {c.failure_means}")
        gates = verdict(results)
        print("\nkill criteria: " + ("none triggered" if not gates else "; ".join(gates)))
        print(f"artifacts: {outdir}/")
        return 1 if any(g.startswith(("VOID", "STOP")) for g in gates) else 0

    if args.cmd == "probe-judge":
        from .controls import probe_judge
        from .model import OpenRouterModel
        rows = probe_judge(OpenRouterModel(), as_of=datetime.now(timezone.utc))
        for aid, what, exp, got, claim in rows:
            print(f"{'ok ' if got == exp else 'MISS'} {aid} {what:22} expected {exp:17} got {got:17} {claim}")
        agree = sum(r[2] == r[3] for r in rows)
        neg = [r for r in rows if r[2] == "does_not_support"]
        pos = [r for r in rows if r[2] == "supports"]
        false_sup = sum(r[3] == "supports" for r in neg)
        false_rej = sum(r[3] == "does_not_support" for r in pos)
        unsure = sum(r[3] == "cannot_tell" for r in rows)
        print(f"\nagreement {agree} of {len(rows)}; false 'supports' {false_sup} of {len(neg)} "
              f"non-supporting pairs; false rejections {false_rej} of {len(pos)} supporting "
              f"pairs; cannot_tell {unsure} of {len(rows)}")
        return 0

    if args.cmd == "measure":
        from .controls import FACTUAL_QUESTIONS
        from .model import OpenRouterModel
        outdir = Path(args.out or
                      f"traces/occam/measure-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
        if _refuse_overwrite([outdir / f"q{i:02d}.json"
                              for i in range(1, len(FACTUAL_QUESTIONS) + 1)]):
            return 2
        model = OpenRouterModel()
        outdir.mkdir(parents=True, exist_ok=True)
        pooled = {"ok": 0, "markup": 0, "punctuation": 0, "absent": 0, "unresolvable": 0}
        claimed = abstained = 0
        statuses: dict[str, int] = {}
        for i, q in enumerate(FACTUAL_QUESTIONS, 1):
            answer, artifact = run(q, model)
            (outdir / f"q{i:02d}.json").write_text(stored_run(answer, artifact))
            c = answer.counters
            for v in ("absent", "punctuation", "unresolvable"):
                pooled[v] += int(c[f"{v}_frac"].n)
            pooled["ok"] += int(c["verified_frac"].n)
            claimed += c["verified_frac"].of
            abstained += answer.abstained
            key = "abstained" if answer.abstained else answer.status.value
            statuses[key] = statuses.get(key, 0) + 1
            print(f"q{i:02d} [{key:11}] verified {c['verified_frac'].n:g} of {c['verified_frac'].of}"
                  f", absent {c['absent_frac'].n:g}  {answer.conclusion or answer.abstain_reason}"[:200])
        print(f"\npooled over {claimed} quotes claimed: verified {pooled['ok']}, absent "
              f"{pooled['absent']}, punctuation {pooled['punctuation']}, unresolvable "
              f"{pooled['unresolvable']}")
        print(f"abstained {abstained} of {len(FACTUAL_QUESTIONS)}; statuses {statuses}")
        print(f"artifacts: {outdir}/")
        return 0

    if args.cmd == "calibrate":
        examples = []
        for line in Path(args.labels).read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            stored = json.loads(Path(row["artifact"]).read_text())
            a = replay(Artifact.model_validate(stored["artifact"]))
            examples.append(Example(derived=a.status.value if a.status and not a.abstained
                                    else ABSTAINED, label=row["label"], ref=row["artifact"]))
        cal = fit(examples, alpha=args.alpha, population=args.population)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(cal.model_dump_json(indent=1))
        print(f"{len(examples)} labelled answers: fit {cal.n_fit}, calibrate {cal.n_cal}; "
              f"qhat={cal.qhat}; written {args.out}")
        print("Report coverage only on answers NOT in this file (evaluate on held-out labels).")
        return 0

    if args.cmd == "ask":
        from .model import OpenRouterModel
        out = Path(args.out or f"traces/occam/{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json")
        if _refuse_overwrite([out]):
            return 2
        answer, artifact = run(args.question, OpenRouterModel(args.model), urls=args.url,
                               n_sources=args.sources,
                               params=Params(k_argue=args.k, k_attack=args.k),
                               calibration=cal)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(stored_run(answer, artifact))
        _show(answer)
        print(f"\nartifact: {out}")
        return 0

    stored = json.loads(Path(args.file).read_text())
    answer = replay(Artifact.model_validate(stored["artifact"]), cal)
    if cal is not None:
        _show(answer)
        print("\n(calibrated replay: not compared with the stored answer)")
        return 0
    same = canonical(answer) == json.dumps(stored["answer"], sort_keys=True, ensure_ascii=False)
    _show(answer)
    print(f"\nreplay {'MATCHES' if same else 'DIFFERS FROM'} the stored answer")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
