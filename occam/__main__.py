"""Command line: ask a question, or replay a stored run.

    python -m occam ask "question" [--url URL ...] [--k 3] [--sources 3] [--out FILE] [--no-judge-same]
    python -m occam replay FILE [--calibration CAL] [--blind]
    python -m occam replay DIR --blind [--template LABELS.jsonl] [--seed 0]  # a labeller's sheet
    python -m occam replay FILE --drop-attack A:T ... --reject-quote ID ...   # what if
    python -m occam controls [--out DIR] [--no-judge-same] [--v1]  # the validation controls, live
    python -m occam measure [--out DIR] [--no-judge-same]   # the pre-registered factual set, live
    python -m occam probe-judge              # the support judge on its 12-pair probe, live
    python -m occam probe-same [--out FILE]  # the same-answer judge on its probe, live (#172)
    python -m occam probe-same --fill FILE --out NEW   # re-ask only its unanswered calls, live
    python -m occam score-same FILE          # re-score a stored probe-same run, no model
    python -m occam rejudge DIR --out DIR    # add the same-answer judge to stored runs, live
    python -m occam calibrate LABELS.jsonl --population "..." [--alpha 0.1] [--out CAL]
    python -m occam frozen DIR               # which stored runs were made under Occam v1

LABELS.jsonl has one {"artifact": FILE, "label": STATUS} per line — a person's
judgment of how much the answer in FILE is worth, after reading it and its
quotes (docs/occam-labelling-guide.md). `replay DIR --blind --template`
writes a blank one in the sheet's order; `calibrate` refuses any row whose
label is not one of the five statuses, and prints derived against label for
every labelled answer.

The same-answer judge (#172) is on by default; `--no-judge-same` turns it off,
and the choice is recorded in the artifact's params.

Occam v1 (#264, occam.frozen) is the pipeline that made run 14. `ask --v1` and
`measure --v1` run it, and refuse any flag that would change it. `calibrate`
refuses a labelled answer that was not made under v1, since a calibration
describes one pipeline; `--any-pipeline` lets it through, and says so.

`ask` and `measure` send independent model calls together, up to
`--concurrency` (default 8) at once, and store the replies in the order they
were asked (#271). That changes how calls are made, not what is asked, so a
run made with any concurrency is still Occam v1. A call that gets no reply
at all waits for the network for up to 30 minutes, and says so (#272).

`ask` needs OPENROUTER_API_KEY. `replay` needs nothing but the file: it
recomputes the answer with no model and says whether it matches the stored one.
`--blind` shows the answer as a labeller should read it: the question, the
answer and its chain down to the quoted bytes, then every other quote the
model drew from the sources (#267), with nothing the pipeline decided about
it — no status, bounds, attack outcomes, judge verdicts, counters or reason
for an abstention — so a label cannot echo the status it is meant to check.
With `--drop-attack ATTACKER:TARGET` or `--reject-quote ID` (each repeatable)
it edits those stored replies first and prints the answer before and after:
what would change it, computed by replay. Nothing is written, and an edit the
stored replies cannot answer for is refused rather than guessed (#206).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .answer import (Answer, Artifact, Params, WhatIfRefused, canonical, contradicted_quotes,
                     counted_sources, derivation_nodes, gathered_quotes, question_details,
                     recorded_params, replay, replay_counted,
                     run, stored_run,
                     support_verdicts, unread_judge_pairs, what_if)
from .conformal import ABSTAINED, Calibration, Example, fit
from .status import MIN_HOSTS
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


def _counted(art: Artifact, a: Answer, counted: Optional[dict] = None) -> None:
    """The sources corroboration counted toward the answer (#248), every time,
    one and none included: "two independent sources" is a claim a reader can
    only check by seeing which two, and whether one relays the other (#225).
    `counted` is what the caller's replay already found (#250); without it,
    one more replay finds it."""
    quotes, n_texts = (counted_sources(art, a.answer_id) if counted is None
                       else counted.get(a.answer_id, ((), 0)))
    hosts = sorted({h for h, _, _ in quotes})
    print(f"   sources counted toward corroboration: {len(hosts)} host(s), "
          f"{n_texts} distinct text(s) (needs {MIN_HOSTS} of each; the n_hosts "
          f"counter below counts the cited page only)")
    for h in hosts:
        # One row per distinct quote: two arguments quoting the same sentence
        # are one thing the host said, not two (#250).
        ids: dict[str, list[str]] = {}
        for _, aid, q in (x for x in quotes if x[0] == h):
            ids.setdefault(" ".join(q.split()), []).append(aid)
        for q, aids in ids.items():
            print(f"      {h} {', '.join(aids)}: \"{q[:150]}{'…' if len(q) > 150 else ''}\"")


def _gathered(a: Answer, art: Artifact) -> None:
    """Every other quote the model drew from the sources, for the labeller
    (#267), counted every time, none included. Listed by page, in id order,
    with nothing the pipeline decided about them."""
    shown = {n["id"] for _, n, _ in derivation_nodes(a)}
    rest = [q for q in gathered_quotes(art) if q[0] not in shown]
    print(f"   other quotes the model drew from the sources: {len(rest)}"
          + (" (none)" if not rest else ""))
    by_url: dict[str, list] = {}
    for q in rest:
        by_url.setdefault(q[3], []).append(q)
    for url, qs in by_url.items():
        print(f"      {url}")
        for aid, quote, verdict, _, s, e in qs:
            print(f"         {aid} \"{quote}\"")
            print(f"            verbatim: {verdict} · characters {s}–{e}")


def _show(a: Answer, art: Optional[Artifact] = None, blind: bool = False,
          counted: Optional[dict] = None) -> None:
    print(f"\nQ: {a.question}")
    if blind:
        # The reason is the pipeline's judgement (which check failed), so the
        # labeller is told only that no answer was given (#267).
        print("ABSTAINED — the pipeline gave no answer" if a.abstained
              else f"A: {a.conclusion}")
        if not a.abstained:
            _chain(a, None, blind=True)
        if art is not None:
            _gathered(a, art)
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
        if art is not None:
            _counted(art, a, counted)
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


def _what_if(artifact: Artifact, answer: Answer, drops: list[str], rejects: list[str],
             cal) -> int:
    edges = []
    for d in drops:
        attacker, sep, target = d.partition(":")
        if not sep or not attacker or not target:
            print(f"--drop-attack takes ATTACKER:TARGET, got {d!r}", file=sys.stderr)
            return 2
        edges.append((attacker, target))
    try:
        edited = what_if(artifact, drop_attacks=edges, reject_quotes=rejects)
    except WhatIfRefused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    after = replay(edited, cal)
    change = "; ".join([f"no attack {a} → {t}" for a, t in edges] +
                       [f"support judge rejects {q}" for q in rejects])
    print(f"what if: {change}  (computed by replay; nothing written)")
    print(f"same-answer judge pairs this edit removed, whose stored replies are not read: "
          f"{unread_judge_pairs(artifact, edited)}")
    for name, a in (("as run", answer), ("what if", after)):
        print(f"\n{name}:")
        if a.abstained:
            print(f"   ABSTAINED — {a.abstain_reason}")
        else:
            print(f"   A: {a.conclusion}")
            print(f"   status: {a.status.value}   bound by: {'; '.join(a.status_bound_by)}")
    print("\n" + ("the answer changes" if (answer.conclusion, answer.status) !=
                   (after.conclusion, after.status) else
                   "the answer and its status are the same; what binds it changes"
                   if answer.status_bound_by != after.status_bound_by else
                   "the answer, its status and what binds it are the same"))
    return 0


def _factcheck_search(n: int) -> tuple[object, bool]:
    """The fact-check search for `--factcheck n`, or None for 0. The second
    value is False when n asks for one and no key is set: refused before any
    model is built, since a run without it would record "none found" for
    what was never searched."""
    if n <= 0:
        return None, True
    key = os.environ.get("GOOGLE_FACTCHECK_API_KEY", "").strip()
    if not key:
        print("--factcheck needs GOOGLE_FACTCHECK_API_KEY in the environment", file=sys.stderr)
        return None, False
    from .factcheck import factcheck_search
    return factcheck_search(key), True


def _sheet(directory: Path, args) -> int:
    """The labeller's sheet (#266): every run in a directory, blind, in a
    seeded shuffled order so neighbouring items do not share a question set's
    order. With --template, a labels file in the same order with one blank
    row per item; `calibrate` refuses it until every label is filled in."""
    if not args.blind:
        print("a directory is replayed only as a labeller's sheet: add --blind",
              file=sys.stderr)
        return 2
    if args.calibration or args.drop_attack or args.reject_quote:
        print("a labeller's sheet shows nothing decided: no --calibration, "
              "--drop-attack or --reject-quote", file=sys.stderr)
        return 2
    paths = sorted(directory.glob("q*.json"))
    if not paths:
        print(f"no runs (q*.json) in {directory}", file=sys.stderr)
        return 1
    if args.template and _refuse_overwrite([Path(args.template)]):
        return 2
    import random
    order = list(paths)
    random.Random(args.seed).shuffle(order)
    rows = []
    for i, p in enumerate(order, 1):
        art = Artifact.model_validate(json.loads(p.read_text())["artifact"])
        answer = replay(art)
        print(f"\n══ item {i} of {len(order)} · {p} " + "═" * 20)
        _show(answer, art, blind=True)
        # `wrong` is apart from the label: a status says how well an answer is
        # carried, and an answer can be carried well and still be false (#266).
        rows.append(json.dumps({"item": i, "artifact": str(p), "label": "",
                                "wrong": None, "minutes": None, "note": ""}))
    if args.template:
        Path(args.template).write_text("\n".join(rows) + "\n")
        print(f"\nlabels template: {args.template} ({len(rows)} blank rows)", file=sys.stderr)
    return 0


def _label_table(examples) -> None:
    """Every labelled answer, derived status against label, every cell
    printed, zeros included (#266): the table a pilot is read from, over all
    the labels and not the fitted half."""
    from .conformal import _INPUTS, _LABELS
    n = len(examples)
    agree = sum(e.derived == e.label for e in examples)
    print(f"derived (rows) against label (columns), all {n} labelled answers:")
    print("   " + " " * 12 + "".join(f"{y:>12}" for y in _LABELS) + f"{'total':>8}")
    for x in _INPUTS:
        cells = [sum(e.derived == x and e.label == y for e in examples) for y in _LABELS]
        print(f"   {x:<12}" + "".join(f"{c:>12}" for c in cells) + f"{sum(cells):>8}")
    print(f"   label same as derived: {agree} of {n}")


def _wrong(rows: list[dict], examples) -> None:
    """Answers the labeller marked false, by derived status, every time,
    zero included (#266). An established answer marked wrong is the pilot's
    kill criterion. A row that never said is counted as not said, never as
    right: silence must not read as safety."""
    marked = [(e.derived, r.get("wrong")) for r, e in zip(rows, examples)]
    wrong = [d for d, w in marked if w is True]
    unsaid = sum(w is None for _, w in marked)
    by = ", ".join(f"{x} {wrong.count(x)}" for x in
                   ("established", "hypothesis", "provisional", "open", "contested", ABSTAINED))
    print(f"labelled wrong: {len(wrong)} of {len(rows)} ({by}); "
          f"wrong not said on {unsaid} of {len(rows)}")


def _relabel_agreement(rows: list[dict], relabels: Path) -> None:
    """How often a second labelling of the same answers agrees with the first,
    keyed by artifact. Blank rows are the unlabelled rest of the re-label
    sheet; a filled row naming an answer the first file lacks is counted
    apart, never dropped silently."""
    first = {r["artifact"]: r["label"] for r in rows}
    valid = {s.value for s in Status}
    again = [json.loads(line) for line in relabels.read_text().splitlines() if line.strip()]
    filled = [r for r in again if r.get("label")]
    bad = [r for r in filled if r["label"] not in valid]
    unknown = [r for r in filled if r["label"] in valid and r["artifact"] not in first]
    pairs = [(first[r["artifact"]], r["label"]) for r in filled
             if r["label"] in valid and r["artifact"] in first]
    same = sum(a == b for a, b in pairs)
    print(f"re-labelled: same label {same} of {len(pairs)} answers labelled twice "
          f"({len(again) - len(filled)} rows left blank, {len(bad)} not a status, "
          f"{len(unknown)} not in the first labelling)")
    for a, b in ((a, b) for a, b in pairs if a != b):
        print(f"   first {a}, then {b}")


CONCURRENCY = 8


def _concurrent(model, n: int):
    """Let `model` have up to n calls in flight (#271). Only a live model that
    declares the attribute is changed, so a scripted test model keeps its
    order. Changes how calls are made, never what is asked: a run made with
    any n is the same pipeline, Occam v1 included."""
    if n < 1:
        raise SystemExit("--concurrency must be at least 1")
    if hasattr(model, "concurrency"):
        model.concurrency = n
    return model


def _calls(model) -> str:
    """How long the model's calls took and how often the network was waited
    for (#272), from what the client recorded. Said every time, zero included."""
    d = sorted(getattr(model, "durations", []))
    waits = getattr(model, "waits", [])
    if not d:
        return "model calls: none timed"
    med = d[len(d) // 2]
    p95 = d[min(len(d) - 1, int(len(d) * 0.95))]
    return (f"model calls: {len(d)} returned; seconds per call median {med:.1f}, "
            f"95th percentile {p95:.1f}, max {d[-1]:.1f}; network waits: {len(waits)}"
            + (f" ({sum(w for w, _ in waits):g} s)" if waits else ""))


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


# Flags that change the pipeline, each with its default outside v1 and its
# value under it (occam.frozen.V1, V1_RUN). A flag left unset is None, so
# `--v1` can tell a default from a choice.
_PIPELINE_FLAGS = {"model": ("z-ai/glm-5.2", "kie/gemini-3-pro"), "web": (3, 3),
                   "factcheck": (0, 3), "k": (3, 3), "sources": (3, 3)}


def _settle(args: argparse.Namespace) -> Optional[str]:
    """Fill each pipeline flag left unset — from v1 under `--v1`, else from its
    default — and return why `--v1` refuses, if a flag given would change v1."""
    from .frozen import V1, V1_RUN
    # A raise, not an assert: `python -O` drops asserts, and this is what keeps
    # `--v1` running the model and source counts v1 names (#276).
    if (V1.model, V1.web_sources, V1.factcheck_sources, V1.k_argue, V1_RUN["n_sources"]) \
            != tuple(v for _, v in _PIPELINE_FLAGS.values()) or V1.k_attack != V1.k_argue:
        raise RuntimeError("the CLI's --v1 flag values differ from occam.frozen.V1")
    given = [f"--{f}" for f in _PIPELINE_FLAGS if getattr(args, f, None) is not None]
    given += ["--no-judge-same"] * bool(args.no_judge_same) + ["--url"] * bool(getattr(args, "url", None))
    for f, (default, v1) in _PIPELINE_FLAGS.items():
        if hasattr(args, f) and getattr(args, f) is None:
            setattr(args, f, v1 if args.v1 else default)
    if args.v1 and given:
        return (f"--v1 runs Occam v1 as frozen; {', '.join(given)} would change it "
                f"(occam.frozen.V1)")
    return None


def _params(args: argparse.Namespace) -> Params:
    """The run's params: v1's own under `--v1`, else built from the flags."""
    from .frozen import V1
    if args.v1:
        return V1
    k = getattr(args, "k", 3)                 # measure has no --k: it always ran 3
    return Params(k_argue=k, k_attack=k, judge_same=not args.no_judge_same,
                  web_sources=args.web, factcheck_sources=args.factcheck)


def _differ(kept: Params, mine: Params, names: tuple[str, str] = ("kept", "this")) -> list[str]:
    """Each setting a kept artifact recorded that this pass would record
    differently, as "field: kept X, this Y" (or under the `names` given)."""
    return [f"{f}: {names[0]} {getattr(kept, f)!r}, {names[1]} {getattr(mine, f)!r}"
            for f in Params.model_fields if getattr(kept, f) != getattr(mine, f)]


def _v1_line(art: Artifact) -> str:
    """Whether a run was made under Occam v1, said every time."""
    from .frozen import made_under_v1
    off = made_under_v1(art.params)
    return "made under Occam v1" if not off else \
        f"NOT made under Occam v1: {'; '.join(off)}"


def _frozen(directory: Path) -> int:
    """Each stored run in DIR: made under v1 or not, and whether it replays to
    its stored answer. Exit 0 only when every one is v1 and replays."""
    from .frozen import made_under_v1
    files = sorted(directory.glob("*.json"))
    v1 = replays = 0
    for f in files:
        stored = json.loads(f.read_text())
        if "artifact" not in stored:
            print(f"{f.name}: not a stored run")
            continue
        art = Artifact.model_validate(stored["artifact"])
        off = made_under_v1(art.params)
        same = canonical(replay(art)) == json.dumps(stored["answer"], sort_keys=True,
                                                    ensure_ascii=False)
        v1 += not off
        replays += same
        print(f"{f.name}: {'v1' if not off else 'NOT v1'}; replay "
              f"{'matches' if same else 'DIFFERS'}" + (f" — {'; '.join(off)}" if off else ""))
    print(f"\n{v1} of {len(files)} made under Occam v1; {replays} of {len(files)} replay to "
          f"their stored answer")
    return 0 if files and v1 == replays == len(files) else 1


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
    ask.add_argument("--v1", action="store_true",
                     help="run Occam v1 as frozen (#264); refuses flags that would change it")
    ask.add_argument("--k", type=int)
    ask.add_argument("--sources", type=int)
    ask.add_argument("--web", type=int,
                     help="web pages found by search beside Wikipedia's; 0 for Wikipedia only")
    ask.add_argument("--factcheck", type=int,
                     help="fact-check articles found by Google Fact Check Tools after the web "
                          "pages (#230); needs GOOGLE_FACTCHECK_API_KEY. 0 for none")
    ask.add_argument("--model", help="kie/<slug> for kie.ai (e.g. kie/gpt-5-2); otherwise an OpenRouter slug")
    ask.add_argument("--out")
    ask.add_argument("--calibration")
    ask.add_argument("--concurrency", type=int, default=CONCURRENCY,
                     help="model calls in flight at once (#271); changes how calls are made, not what is asked")
    rp = sub.add_parser("replay")
    rp.add_argument("file")
    rp.add_argument("--calibration")
    rp.add_argument("--blind", action="store_true",
                    help="show it as a labeller reads it: no status or anything decided. "
                         "Given a directory, one sheet of every run in it (#266)")
    rp.add_argument("--template", metavar="LABELS.jsonl",
                    help="with a directory and --blind: also write a labels file with one "
                         "blank row per item, in the sheet's order")
    rp.add_argument("--seed", type=int, default=0,
                    help="with a directory and --blind: the order the items are shuffled into")
    rp.add_argument("--drop-attack", action="append", default=[], metavar="ATTACKER:TARGET",
                    help="what if this attack had not been proposed (repeatable)")
    rp.add_argument("--reject-quote", action="append", default=[], metavar="ID",
                    help="what if the support judge had rejected this quote (repeatable)")
    ct = sub.add_parser("controls")
    ct.add_argument("--no-judge-same", action="store_true",
                    help="turn off the same-answer judge (on by default)")
    ct.add_argument("--out")
    ct.add_argument("--model", help="kie/<slug> for kie.ai (e.g. kie/gpt-5-2); otherwise an OpenRouter slug")
    ct.add_argument("--v1", action="store_true",
                    help="run the controls on Occam v1 as frozen (#278); refuses flags that "
                         "would change it")
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
    ms.add_argument("--model", help="kie/<slug> for kie.ai (e.g. kie/gpt-5-2); otherwise an OpenRouter slug")
    ms.add_argument("--v1", action="store_true",
                    help="run Occam v1 as frozen (#264); refuses flags that would change it")
    ms.add_argument("--resume", action="store_true",
                    help="keep the questions already written to --out and run only the rest; "
                         "refused if a kept one was made with other settings (model, "
                         "sources, samples, rules), each named")
    ms.add_argument("--web", type=int,
                    help="web pages found by search beside Wikipedia's; 0 for Wikipedia only")
    ms.add_argument("--factcheck", type=int,
                    help="fact-check articles found by Google Fact Check Tools after the web "
                         "pages (#230); needs GOOGLE_FACTCHECK_API_KEY. 0 for none")
    ms.add_argument("--concurrency", type=int, default=CONCURRENCY,
                    help="model calls in flight at once (#271); changes how calls are made, not what is asked")
    ms.add_argument("--questions", metavar="FILE",
                    help="one question per line (blank and #-lines skipped) instead of the "
                         "built-in ten, e.g. a held-out set (#226)")
    cp = sub.add_parser("calibrate")
    cp.add_argument("labels")
    cp.add_argument("--population", required=True)
    cp.add_argument("--alpha", type=float, default=0.1)
    cp.add_argument("--out", default="traces/occam/calibration.json")
    cp.add_argument("--relabels", metavar="FILE",
                    help="a second labelling of some of the same answers (#266): prints how "
                         "often the two agree; rows with a blank label are not counted")
    cp.add_argument("--any-pipeline", action="store_true",
                    help="accept labelled answers not made under Occam v1 (said in the output)")
    fz = sub.add_parser("frozen")
    fz.add_argument("dir")
    args = ap.parse_args(argv)
    if args.cmd in ("ask", "measure"):
        refused = _settle(args)
        if refused:
            print(refused, file=sys.stderr)
            return 2
    cal = None
    if getattr(args, "calibration", None):
        cal = Calibration.model_validate_json(Path(args.calibration).read_text())

    if args.cmd == "controls":
        from .controls import CONTROLS, run_control, verdict
        from .frozen import V1
        from .model import make_model
        refused = _settle(args)
        if refused:
            print(refused, file=sys.stderr)
            return 2
        now = datetime.now(timezone.utc)
        outdir = Path(args.out or f"traces/occam/controls-{now:%Y%m%dT%H%M%SZ}")
        if _refuse_overwrite([outdir / f"control-{c.name}.json" for c in CONTROLS]):
            return 2
        model = make_model(args.model)
        params = V1 if args.v1 else Params(judge_same=not args.no_judge_same)
        # A control's only source is its planted page, so it records 0 web and
        # 0 fact-check sources whatever it was given; v1 for a control is v1's
        # params as a run given only that page records them (#278).
        v1_here = recorded_params(V1, V1.model, web=False, factcheck=False)
        outdir.mkdir(parents=True, exist_ok=True)
        results = []
        for c in CONTROLS:
            r = run_control(c, model, as_of=now, params=params)
            results.append(r)
            (outdir / f"control-{c.name}.json").write_text(stored_run(r.answer, r.artifact))
            vf = r.answer.counters["verified_frac"]
            # A false-premise answer that mentions the detail is read, not scored (#183).
            label = "PASS" if r.passed else "FLAG" if c.expect == "reject_premise" else "FAIL"
            print(f"{c.name:13} {label}  {r.observed}  "
                  f"(verified {vf.n:g} of {vf.of} quotes)")
            if not r.passed:
                print(f"{'':13} → {c.failure_means}")
        off = {r.name: _differ(r.artifact.params, v1_here, ("this", "v1")) for r in results}
        print("\n" + ("made under Occam v1, the planted page as each control's only source: "
                      f"{len(results)} of {len(results)}" if not any(off.values()) else
                      "NOT made under Occam v1: " + "; ".join(
                          f"{n}: {', '.join(d)}" for n, d in off.items() if d)))
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

    if args.cmd == "frozen":
        return _frozen(Path(args.dir))

    if args.cmd == "measure":
        from .controls import FACTUAL_QUESTIONS
        from .frozen import made_under_v1
        from .model import make_model
        # Read before any model is built, so a bad file costs nothing.
        questions = FACTUAL_QUESTIONS if not args.questions else tuple(
            line.strip() for line in Path(args.questions).read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#"))
        if not questions:
            print(f"no questions in {args.questions}", file=sys.stderr)
            return 2
        outdir = Path(args.out or
                      f"traces/occam/measure-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
        paths = [outdir / f"q{i:02d}.json" for i in range(1, len(questions) + 1)]
        if not args.resume and _refuse_overwrite(paths):
            return 2
        fc_search, ok = _factcheck_search(args.factcheck)
        if not ok:
            return 2
        model = _concurrent(make_model(args.model), args.concurrency)
        web_search = getattr(model, "web_search", None) if args.web else None
        # A resumed run keeps what it wrote and never writes over it. Every kept
        # question must have been made with the settings this pass records —
        # model, sources, samples, rules — not only the same model (#275): one
        # run, one instrument. (Wikipedia pages per question, which no artifact
        # records, is not a measure flag: every pass gathers run's default.)
        kept = {p: json.loads(p.read_text()) for p in paths if args.resume and p.exists()}
        mine = recorded_params(_params(args), model.name, web=web_search is not None,
                               factcheck=fc_search is not None)
        other = [f"{p} ({'; '.join(off)})" for p, d in kept.items()
                 if (off := _differ(Artifact.model_validate(d["artifact"]).params, mine))]
        if other:
            print(f"refusing to resume: made with other settings than this pass records: "
                  f"{', '.join(other)}", file=sys.stderr)
            return 2
        # Nor from another question list: one run, one set.
        moved = [f"{p.name} ({d['artifact']['question']!r})" for p, d in kept.items()
                 if d["artifact"]["question"] != questions[paths.index(p)]]
        if moved:
            print(f"refusing to resume: kept for a different question than this list has "
                  f"there: {', '.join(moved)}", file=sys.stderr)
            return 2
        outdir.mkdir(parents=True, exist_ok=True)
        pooled = {"ok": 0, "markup": 0, "punctuation": 0, "absent": 0, "unresolvable": 0}
        claimed = abstained = 0
        statuses: dict[str, int] = {}
        written = 0
        for i, q in enumerate(questions, 1):
            path = outdir / f"q{i:02d}.json"
            try:
                if path not in kept:
                    answer, artifact = run(q, model,
                                           params=_params(args),
                                           web_search=web_search,
                                           factcheck_search=fc_search)
                    path.write_text(stored_run(answer, artifact))
                    written += 1
            except BaseException:
                # A pass that stops still spent what it spent (#233): the calls
                # for the question in progress were billed, and a resume asks
                # them again. Said on every exit, so it never reads as nothing.
                if hasattr(model, "credits"):
                    print(f"pass stopped at q{i:02d}: spent {model.credits:g} kie.ai credits, as "
                          f"the provider counted them, over {written} question(s) written and "
                          f"q{i:02d}'s calls, which were discarded", file=sys.stderr, flush=True)
                print(_calls(model), file=sys.stderr, flush=True)
                raise
            if path in kept:
                answer = Answer.model_validate(kept[path]["answer"])
                print(f"q{i:02d} kept from an earlier pass ({kept[path]['artifact']['as_of']})")
            c = answer.counters
            for v in ("absent", "punctuation", "unresolvable"):
                pooled[v] += int(c[f"{v}_frac"].n)
            pooled["ok"] += int(c["verified_frac"].n)
            claimed += c["verified_frac"].of
            abstained += answer.abstained
            key = "abstained" if answer.abstained else answer.status.value
            statuses[key] = statuses.get(key, 0) + 1
            print(f"q{i:02d} [{key:11}] verified {c['verified_frac'].n:g} of {c['verified_frac'].of}"
                  f", absent {c['absent_frac'].n:g}  {answer.conclusion or answer.abstain_reason}"[:200],
                  flush=True)
        print(f"\npooled over {claimed} quotes claimed: verified {pooled['ok']}, absent "
              f"{pooled['absent']}, punctuation {pooled['punctuation']}, unresolvable "
              f"{pooled['unresolvable']}")
        print(f"abstained {abstained} of {len(questions)}; statuses {statuses}")
        made = [p for p in paths if p.exists()]
        v1 = sum(not made_under_v1(Artifact.model_validate(json.loads(p.read_text())["artifact"])
                                   .params) for p in made)
        print(f"made under Occam v1: {v1} of {len(made)}")
        if hasattr(model, "credits"):
            print(f"spent: {model.credits:g} kie.ai credits in this pass, as the provider "
                  f"counted them ({len(kept)} question(s) kept from earlier passes not included)")
        print(_calls(model))
        print(f"artifacts: {outdir}/")
        return 0

    if args.cmd == "calibrate":
        from .frozen import made_under_v1
        examples = []
        mixed = 0
        rows = [json.loads(line) for line in Path(args.labels).read_text().splitlines()
                if line.strip()]
        valid = {s.value for s in Status}
        bad = [r for r in rows if r.get("label") not in valid]
        if bad or not rows:
            print(f"refusing {args.labels}: {len(bad)} of {len(rows)} rows have no valid "
                  f"label (one of {', '.join(sorted(valid))})", file=sys.stderr)
            for r in bad[:10]:
                print(f"   item {r.get('item', '?')} {r.get('artifact')}: "
                      f"label {r.get('label')!r}", file=sys.stderr)
            return 2
        for row in rows:
            stored = json.loads(Path(row["artifact"]).read_text())
            art = Artifact.model_validate(stored["artifact"])
            off = made_under_v1(art.params)
            if off:
                if not args.any_pipeline:
                    print(f"refusing {row['artifact']}: not made under Occam v1 ({'; '.join(off)}); "
                          f"a calibration describes one pipeline (--any-pipeline to accept it)",
                          file=sys.stderr)
                    return 2
                mixed += 1
            a = replay(art)
            examples.append(Example(derived=a.status.value if a.status and not a.abstained
                                    else ABSTAINED, label=row["label"], ref=row["artifact"]))
        cal = fit(examples, alpha=args.alpha, population=args.population)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(cal.model_dump_json(indent=1))
        print(f"{len(examples)} labelled answers: fit {cal.n_fit}, calibrate {cal.n_cal}; "
              f"qhat={cal.qhat}; written {args.out}")
        print(f"labelled answers not made under Occam v1: {mixed} of {len(examples)}")
        _label_table(examples)
        _wrong(rows, examples)
        if args.relabels:
            _relabel_agreement(rows, Path(args.relabels))
        print("Report coverage only on answers NOT in this file (evaluate on held-out labels).")
        return 0

    if args.cmd == "ask":
        from .model import make_model
        out = Path(args.out or f"traces/occam/{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json")
        if _refuse_overwrite([out]):
            return 2
        fc_search, ok = _factcheck_search(args.factcheck)
        if not ok:
            return 2
        model = _concurrent(make_model(args.model), args.concurrency)
        answer, artifact = run(args.question, model, urls=args.url,
                               n_sources=args.sources,
                               params=_params(args),
                               calibration=cal,
                               web_search=getattr(model, "web_search", None) if args.web else None,
                               factcheck_search=fc_search)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(stored_run(answer, artifact))
        _show(answer, artifact)
        print(_v1_line(artifact))
        print(_calls(model))
        print(f"\nartifact: {out}")
        return 0

    if Path(args.file).is_dir():
        return _sheet(Path(args.file), args)
    if args.template:
        print("--template needs a directory of runs", file=sys.stderr)
        return 2
    stored = json.loads(Path(args.file).read_text())
    artifact = Artifact.model_validate(stored["artifact"])
    answer, counted = replay_counted(artifact, cal)
    if args.blind:
        _show(answer, artifact, blind=True)
        return 0
    if args.drop_attack or args.reject_quote:
        return _what_if(artifact, answer, args.drop_attack, args.reject_quote, cal)
    if cal is not None:
        _show(answer, artifact, counted=counted)
        print(_judged_when(artifact))
        print(_served(artifact))
        print("\n(calibrated replay: not compared with the stored answer)")
        return 0
    same = canonical(answer) == json.dumps(stored["answer"], sort_keys=True, ensure_ascii=False)
    _show(answer, artifact, counted=counted)
    print(_judged_when(artifact))
    print(_served(artifact))
    print(f"\nreplay {'MATCHES' if same else 'DIFFERS FROM'} the stored answer")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
