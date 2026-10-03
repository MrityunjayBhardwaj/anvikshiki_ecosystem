"""Command line: ask a question, or replay a stored run.

    python -m occam ask "question" [--url URL ...] [--k 3] [--sources 3] [--out FILE] [--no-judge-same]
    python -m occam replay FILE [--calibration CAL] [--blind]
    python -m occam controls [--out DIR] [--no-judge-same]  # the three validation controls, live
    python -m occam measure [--out DIR] [--no-judge-same]   # the pre-registered factual set, live
    python -m occam probe-judge              # the support judge on its 12-pair probe, live
    python -m occam probe-same [--out FILE]  # the same-answer judge on its probe, live (#172)
    python -m occam probe-same --fill FILE --out NEW   # re-ask only its unanswered calls, live
    python -m occam score-same FILE          # re-score a stored probe-same run, no model
    python -m occam rejudge DIR --out DIR    # add the same-answer judge to stored runs, live
    python -m occam calibrate LABELS.jsonl --population "..." [--alpha 0.1] [--out CAL]

LABELS.jsonl has one {"artifact": FILE, "label": STATUS} per line — a person's
judgment of how much the answer in FILE is worth, after reading it and its
quotes.

The same-answer judge (#172) is on by default; `--no-judge-same` turns it off,
and the choice is recorded in the artifact's params.

`ask` needs OPENROUTER_API_KEY. `replay` needs nothing but the file: it
recomputes the answer with no model and says whether it matches the stored one.
`--blind` shows the answer as a labeller should read it: the question, the
answer and its chain down to the quoted bytes, with nothing the pipeline
decided about it — no status, bounds, attack outcomes, judge verdicts or
counters — so a label cannot echo the status it is meant to check.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .answer import (Answer, Artifact, Params, canonical, contradicted_quotes,
                     derivation_nodes, question_details, replay, run, stored_run,
                     support_verdicts)
from .conformal import ABSTAINED, Calibration, Example, fit
from .types import Status


def _judged_when(art: Artifact) -> str:
    """When the same-answer judge was asked, said every time (#177)."""
    if not art.params.judge_same:
        return "same-answer judge: not run"
    if art.same_judged_at is None:
        return "same-answer judge: when it was asked is not recorded (made before #177)"
    if art.same_judged_at == art.as_of:
        return f"same-answer judge: asked in the run ({art.as_of.isoformat()})"
    return (f"same-answer judge: asked {art.same_judged_at.isoformat()}, after the run "
            f"({art.as_of.isoformat()}) — its replies are from a later call than the rest")


def _served(art: Artifact) -> str:
    """Who served the model calls, said every time (#186)."""
    def says(pairs):
        return ", ".join(pairs) if pairs else "no model call was made"
    line = ("served by: not recorded (made before #186, or by a model that does not report it)"
            if art.served_by is None else f"served by: {says(art.served_by)}")
    if art.same_judged_at is not None and art.same_judged_at != art.as_of:
        line += ("; the later judge: not recorded" if art.same_served_by is None
                 else f"; the later judge: {says(art.same_served_by)}")
    return line


# What each status means, in a reader's words. Keyed on the status, never on
# the wording of its bounds: the bounds say which limit, this says what the
# status itself claims (status.py has the rules).
MEANING = {
    Status.ESTABLISHED: "a checked quote states it word for word, and at least two "
                        "independent sources say it",
    Status.HYPOTHESIS: "the sources support it, but something beneath it is not settled: "
                       "the model's own wording or reasoning, a single source, or a link "
                       "nobody checked. 'bound by' names which",
    Status.PROVISIONAL: "only weakly supported: an analogy, a quote too short to prove "
                        "anything, or a link the judge could not decide",
    Status.CONTESTED: "the arguments conflict, and one consistent reading of them accepts "
                      "this answer while another does not",
    Status.OPEN: "the arguments conflict, and no consistent reading of them accepts this answer",
}

NO_RUN = "not shown (no stored run given)"


def _chain(a: Answer, support: Optional[dict], blind: bool) -> None:
    """The answer's derivation down to the bytes, each link with its own
    check: verbatim, support, attack outcome — or that it was not checked."""
    print("   derivation, from the answer down to the quoted bytes:")
    for depth, n, again in derivation_nodes(a):
        pad = "      " + "   " * depth
        if again:
            print(f"{pad}{n['id']} (shown above)")
            continue
        tag = "" if blind else f" [{n['status'] or 'rejected'}]"
        print(f"{pad}{n['id']} {n['kind']}{tag}: {n['conclusion']}")
        if n["kind"] == "quote":
            sp = n["span"]
            checks = f"verbatim: {sp['verdict']}"
            if not blind:
                said = NO_RUN if support is None else (support.get(n["id"]) or "not judged")
                checks += f" · support: {said}"
            print(f"{pad}   \"{sp['quote']}\"")
            print(f"{pad}   {checks} · {sp['url']} characters {sp['start']}–{sp['end']}")
            print(f"{pad}   text sha256 {sp['text_sha256']} · snapshot {sp['snapshot_id']}")
            print(f"{pad}   revision: {sp.get('revision_url') or 'not recorded'}")
        if not blind:
            if not n["attacks_received"]:
                print(f"{pad}   attacked by: none")
            for x in n["attacks_received"]:
                print(f"{pad}   attacked by {x['attacker']} ({x['type']}): "
                      f"{'succeeded' if x['succeeded'] else 'failed'} — {x['rationale']}")


def _question_details(a: Answer, art: Optional[Artifact]) -> None:
    """Details the question supplied are suppositions, never observations:
    say for each whether a quote beneath the answer states it (#181's
    predicate). Said every time, including when it cannot look."""
    if art is None:
        print(f"   question details: {NO_RUN}")
        return
    nums, rows = question_details(a, art)
    if not nums:
        print("   question details: the question has no whole number, so this check cannot "
              "fire (it reads whole numbers only)")
    for num, carried, stated in rows:
        print(f"   question detail {num}: " + (
            "carried by the answer, and stated by a quote beneath it" if stated else
            "carried by the answer, but no quote beneath it states it: the question "
            "supplied it, nothing observed it" if carried else
            "not carried by the answer"))


def _show(a: Answer, art: Optional[Artifact] = None, blind: bool = False) -> None:
    print(f"\nQ: {a.question}")
    if blind:
        print(f"ABSTAINED — {a.abstain_reason}" if a.abstained else f"A: {a.conclusion}")
        if not a.abstained:
            _chain(a, None, blind=True)
        for s in a.snapshots:
            print(f"source {s['urls'][0]}\n   revision: "
                  f"{s.get('revision_url') or 'not recorded'}")
        return
    if a.abstained:
        print(f"ABSTAINED — {a.abstain_reason}")
    else:
        print(f"A: {a.conclusion}")
        print(f"   status: {a.status.value}   bound by: {'; '.join(a.status_bound_by)}")
        print(f"   meaning: {MEANING[a.status]}")
        if a.status_set is not None:
            print(f"   status set: {{{', '.join(s.value for s in a.status_set)}}}")
        print(f"   {a.status_set_note}")
        # Said every time, zero included, so silence cannot read as "not
        # checked" (#193).
        hit, n_quotes = contradicted_quotes(a)
        print(f"   quotes beneath this answer that another argument defeated: "
              f"{len(hit)} of {n_quotes}")
        for q in hit:
            print(f"      {q['id']} \"{q['quote']}\"")
            for x in q["by"]:
                print(f"         defeated by {x['attacker']}: {x['why']}")
        _question_details(a, art)
        _chain(a, None if art is None else support_verdicts(art), blind=False)
    if a.positions and "wordings" not in a.positions[0]:
        print("   positions grouped by exact wording (same-answer judge not run)")
    for p in a.positions:
        print(f"   position [{p['status']}] ({p['samples']} samples): {p['conclusion']}")
        for w in p.get("wordings", []):
            if w != p["conclusion"]:
                print(f"      also worded: {w}")
        for k in p.get("kept_apart", []):
            print(f"      kept apart from: {k['from'][:90]} — {k['why']}")
    print("counters:")
    for name, c in a.counters.items():
        frac = f" = {c.frac:.2f}" if c.frac is not None and name.endswith("frac") else ""
        print(f"   {name:18} {c.n:g} of {c.of} {c.population}{frac}")
    for d in a.degraded:
        print(f"   degraded: {d}")
    for s in a.snapshots:
        print(f"source {s['urls'][0]}\n   revision: "
              f"{s.get('revision_url') or 'not recorded — cannot be re-checked once the page changes'}")


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


def _report_probe(probe, kill_criteria) -> int:
    from .sameprobe import score
    res, rows = score(probe)
    print(f"model {probe.model}, temperature {probe.temperature}, as of {probe.as_of}; "
          f"{len(probe.pairs)} pairs, {len(probe.replies)} calls, "
          f"{len(probe.failures)} calls failed")
    print(f"{'source':6} {'lens':8} {'expect':9} {'kind':26} {'pairs':>5} {'veto':>5} "
          f"{'lost':>5} {'judged':>6} {'MERGED':>6} {'apart':>5} {'c_tell':>6} "
          f"{'orders≠':>7} {'malf':>5}")
    for r in rows:
        print(f"{r['source']:6} {r['lens']:8} {r['expected']:9} {r['kind']:26} "
              f"{r['pairs']:5} {r['vetoed']:5} {r['unanswered']:5} {r['judged']:6} "
              f"{r['merged']:6} {r['apart']:5} {r['cannot_tell']:6} "
              f"{r['orders_disagree']:7} {r['malformed']:5}")
    for want, what in (("different", "WRONG MERGES (the dangerous direction)"),
                       ("same", "missed merges")):
        for src in ("flip", "paws"):
            rs = [r for r in rows if r["source"] == src and r["expected"] == want]
            if not rs:
                continue
            n = sum(r["pairs"] for r in rs)
            bad = (sum(r["merged"] for r in rs) if want == "different"
                   else sum(r["vetoed"] + r["apart"] for r in rs))
            print(f"{what}, {src}: {bad} of {n} expected-{want} pairs "
                  f"({sum(r['unanswered'] for r in rs)} unanswered)")
    for r in rows:
        if r["expected"] == "different" and r["merged_ids"]:
            by = {pp.pair.id: pp for pp in probe.pairs}
            for pid in r["merged_ids"]:
                pp = by[pid]
                print(f"  merged {pid} [{pp.origin}] {pp.pair.text_a!r}\n"
                      f"         vs {pp.pair.text_b!r}")
    gates = kill_criteria(rows)
    print("\nkill criteria: " + ("none triggered" if not gates else "; ".join(gates)))
    return 1 if gates else 0


def _rejudge(src: Path, dst: Path) -> int:
    """Add the same-answer judge to each stored run in `src`, write the result
    to `dst`, and show what moved. Every other stage is read, not re-asked."""
    from .answer import rejudge
    from .model import OpenRouterModel
    files = sorted(src.glob("q*.json"))
    if _refuse_overwrite([dst / f.name for f in files]):
        return 2
    model = OpenRouterModel()
    dst.mkdir(parents=True, exist_ok=True)
    moved = rose = merged = judged = vetoed = disagree = 0
    for f in files:
        stored = json.loads(f.read_text())
        before = stored["answer"]
        answer, artifact = rejudge(Artifact.model_validate(stored["artifact"]), model,
                                   at=datetime.now(timezone.utc))
        (dst / f.name).write_text(stored_run(answer, artifact))
        c = answer.counters
        v, m, d = (c.get("same_question_vetoed"), c.get("same_question_merged"),
                   c.get("same_question_order_disagree"))
        vetoed += int(v.n) if v else 0
        judged += (v.of - int(v.n)) if v else 0
        merged += int(m.n) if m else 0
        disagree += int(d.n) if d else 0
        b_ag, a_ag = before["counters"]["agree_frac"], c["agree_frac"]
        b_st = "abstained" if before["abstained"] else before["status"]
        a_st = "abstained" if answer.abstained else answer.status.value
        moved += b_st != a_st
        rose += a_ag.n > b_ag["n"]
        print(f"{f.stem}: positions {len(before['positions'])} → {len(answer.positions)}; "
              f"agreement {b_ag['n']:g} → {a_ag.n:g} of {a_ag.of}; status {b_st} → {a_st}")
        for p in answer.positions:
            print(f"   [{p['samples']}] {p['conclusion']}")
            for k in p.get("kept_apart", []):
                print(f"       kept apart from: {k['from'][:80]} — {k['why']}")
    print(f"\nquestion-lens pairs: {judged} judged, {vetoed} vetoed; merged {merged} of "
          f"{judged} judged; orders disagreed on {disagree} of {judged}")
    print(f"agreement rose in {rose} of {len(files)}; statuses moved in {moved} of {len(files)}")
    print(f"artifacts: {dst}/")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="occam")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ask = sub.add_parser("ask")
    ask.add_argument("--no-judge-same", action="store_true",
                    help="turn off the same-answer judge (on by default)")
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
    rp.add_argument("--blind", action="store_true",
                    help="show it as a labeller reads it: no status or anything decided")
    ct = sub.add_parser("controls")
    ct.add_argument("--no-judge-same", action="store_true",
                    help="turn off the same-answer judge (on by default)")
    ct.add_argument("--out")
    sub.add_parser("probe-judge")
    ps = sub.add_parser("probe-same")
    ps.add_argument("--out")
    ps.add_argument("--runs", default="traces/occam/run2",
                    help="stored runs whose answer conclusions are flipped")
    ps.add_argument("--workers", type=int, default=8)
    ps.add_argument("--fill", help="a stored probe-same run: re-ask only the calls that "
                                   "never returned a reply, and write the result to --out")
    ss = sub.add_parser("score-same")
    ss.add_argument("file")
    rj = sub.add_parser("rejudge")
    rj.add_argument("dir")
    rj.add_argument("--out", required=True)
    ms = sub.add_parser("measure")
    ms.add_argument("--no-judge-same", action="store_true",
                    help="turn off the same-answer judge (on by default)")
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
            r = run_control(c, model, as_of=now, params=Params(judge_same=not args.no_judge_same))
            results.append(r)
            (outdir / f"control-{c.name}.json").write_text(stored_run(r.answer, r.artifact))
            vf = r.answer.counters["verified_frac"]
            # A false-premise answer that mentions the detail is read, not scored (#183).
            label = "PASS" if r.passed else "FLAG" if c.expect == "reject_premise" else "FAIL"
            print(f"{c.name:13} {label}  {r.observed}  "
                  f"(verified {vf.n:g} of {vf.of} quotes)")
            if not r.passed:
                print(f"{'':13} → {c.failure_means}")
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

    if args.cmd in ("probe-same", "score-same"):
        from .sameprobe import (ProbeRun, flip_pairs, kill_criteria, paws_pairs,
                                run_conclusions, run_probe)
        if args.cmd == "probe-same" and args.fill:
            from .model import OpenRouterModel
            from .sameprobe import fill
            if not args.out:
                print("--fill needs --out: a stored run is never rewritten", file=sys.stderr)
                return 2
            out = Path(args.out)
            if _refuse_overwrite([out]):
                return 2
            before = ProbeRun.model_validate_json(Path(args.fill).read_text())
            model = OpenRouterModel(before.model.removeprefix("openrouter/"))
            probe = fill(model, before, at=datetime.now(timezone.utc).isoformat(),
                         workers=min(args.workers, 2))
            out.write_text(probe.model_dump_json(indent=1))
            print(f"filled {len(probe.filled)} calls from {args.fill}; "
                  f"{len(probe.failures)} still failed; artifact: {out}")
        elif args.cmd == "probe-same":
            now = datetime.now(timezone.utc)
            out = Path(args.out or f"traces/occam/probe-same-{now:%Y%m%dT%H%M%SZ}.json")
            if _refuse_overwrite([out]):
                return 2
            from .model import OpenRouterModel
            pairs = flip_pairs(run_conclusions(Path(args.runs))) + paws_pairs()
            probe = run_probe(OpenRouterModel(), pairs, as_of=now.isoformat(),
                              workers=args.workers)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(probe.model_dump_json(indent=1))
            print(f"artifact: {out}")
        else:
            probe = ProbeRun.model_validate_json(Path(args.file).read_text())
        return _report_probe(probe, kill_criteria)

    if args.cmd == "rejudge":
        return _rejudge(Path(args.dir), Path(args.out))

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
            answer, artifact = run(q, model, params=Params(judge_same=not args.no_judge_same))
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
                               params=Params(k_argue=args.k, k_attack=args.k,
                                             judge_same=not args.no_judge_same),
                               calibration=cal)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(stored_run(answer, artifact))
        _show(answer, artifact)
        print(f"\nartifact: {out}")
        return 0

    stored = json.loads(Path(args.file).read_text())
    artifact = Artifact.model_validate(stored["artifact"])
    answer = replay(artifact, cal)
    if args.blind:
        _show(answer, artifact, blind=True)
        return 0
    if cal is not None:
        _show(answer, artifact)
        print(_judged_when(artifact))
        print(_served(artifact))
        print("\n(calibrated replay: not compared with the stored answer)")
        return 0
    same = canonical(answer) == json.dumps(stored["answer"], sort_keys=True, ensure_ascii=False)
    _show(answer, artifact)
    print(_judged_when(artifact))
    print(_served(artifact))
    print(f"\nreplay {'MATCHES' if same else 'DIFFERS FROM'} the stored answer")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
