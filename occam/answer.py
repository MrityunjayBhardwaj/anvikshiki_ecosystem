"""Stage 7 — the Answer, its countable features, and replay (#143).

The artifact is what makes the pipeline checkable by someone else. It holds
the question, the clock the run used, every snapshot's bytes and text, and
the model's raw replies — nothing derived. `replay` rebuilds the answer from
it with no model in the loop. If replay disagrees with the original, that is
a bug in this system, and replay is how it is found.

Every feature is a count with its denominator. A bare zero cannot be told
apart from a loop that never ran, so none is ever printed alone.
"""

from __future__ import annotations

import base64
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterator, Optional, Sequence

from pydantic import BaseModel, ConfigDict, model_validator

from .argue import (ArgueResult, adds_question_number, argue, argue_from_replies, norm_conclusion,
                    question_numbers, unquoted_question_numbers)
from .attack import AttackResult, attack, attack_from_replies
from .conformal import ABSTAINED, Calibration
from .equiv import EquivResult, candidate_pairs, equiv_from_replies, judge_same
from .gather import HttpGet, gather, urllib_get
from .model import Model
from .snapshot import Snapshot, SnapshotStore, host
from .solve import chain_pramana
from .spans import ADMITTED
from .support import SupportResult, apply_support, support, support_from_replies
from .status import MAX_AGE_DAYS, StatusResult, derive
from .types import STATUS_ORDER, Status

# Weakest first, as types.STATUS_ORDER, but for choosing what to show (see
# Params.shown_order). Never for ceilings or attack strength.
SHOWN_ORDER: dict[int, tuple[Status, ...]] = {
    1: STATUS_ORDER,
    2: (Status.OPEN, Status.CONTESTED, Status.PROVISIONAL, Status.HYPOTHESIS,
        Status.ESTABLISHED),
}

__all__ = ["Count", "Answer", "Artifact", "Params", "run", "replay", "rejudge", "assemble",
           "canonical", "stored_run", "contradicted_quotes", "derivation_nodes",
           "support_verdicts", "question_details"]

ARTIFACT_VERSION = 1


class Count(BaseModel):
    """n of a population. `frac` is None over an empty population."""

    model_config = ConfigDict(frozen=True)

    n: float
    of: int
    population: str

    @property
    def frac(self) -> Optional[float]:
        return self.n / self.of if self.of else None


class Params(BaseModel):
    model_config = ConfigDict(frozen=True)

    k_argue: int = 3
    k_attack: int = 3
    t_argue: float = 0.7
    t_attack: float = 0.2
    k_support: int = 1
    t_support: float = 0.0
    # The same-answer judge (#172): on by default, a setting so it can be
    # turned off (`--no-judge-same`). An artifact made before it has no such
    # field and is read as False — see Artifact — so it replays exactly as it
    # did: exact-wording groups, no new fields.
    judge_same: bool = True
    t_same: float = 0.0
    # Which argue instruction wrote the replies. 2 (#161): a quote's conclusion
    # does not repeat the question's details. An artifact without the field
    # was argued under 1, and shows no counter that 2 introduced.
    argue_prompt: int = 2
    # Which counters the answer shows, so adding one does not change what an
    # older artifact replays to. 2 (#179): `question_number_unquoted`. 3
    # (#181): both premise counters say what they could read in the question.
    # An artifact without the field shows the counters it was made with.
    counter_set: int = 3
    # Which wording the abstain reasons use, for the same reason. 2 (#188):
    # when the model returns no answer, say only that — not that the sources
    # have none. An artifact without the field keeps the wording it was made with.
    reason_wording: int = 2
    # Which negation words the same-answer veto reads (occam.equiv
    # NEGATIONS_BY_SET). 2 (#192): "without" is not a negation. An artifact
    # without the field was judged under 1, and its stored replies line up
    # with set 1's pairs only.
    veto_words: int = 2
    # Which order picks the answer shown and orders the positions. 2 (#191):
    # contested above open — a contested answer has a coherent case for it,
    # an open one has none. Only the choice of what to show: the status
    # lattice (types.STATUS_ORDER), which sets ceilings and attack strength,
    # is untouched. An artifact without the field shows what it showed.
    shown_order: int = 2
    max_chars: int = 40_000
    max_age_days: int = MAX_AGE_DAYS
    model: str = ""


class StoredSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    urls: tuple[str, ...]
    fetched_at: datetime
    media_type: str
    body_b64: str
    text: str
    text_sha256: str
    extractor: str
    empty_reason: Optional[str]
    revision_url: Optional[str] = None      # absent in artifacts before #169

    @classmethod
    def of(cls, s: Snapshot) -> "StoredSnapshot":
        return cls(id=s.id, urls=s.urls, fetched_at=s.fetched_at, media_type=s.media_type,
                   body_b64=base64.b64encode(s.body).decode(), text=s.text,
                   text_sha256=s.text_sha256, extractor=s.extractor,
                   empty_reason=s.empty_reason, revision_url=s.revision_url)

    def load(self) -> Snapshot:
        # Snapshot re-hashes body and text on construction, so a tampered
        # artifact fails here, loudly, rather than replaying something else.
        return Snapshot(id=self.id, urls=self.urls, fetched_at=self.fetched_at,
                        media_type=self.media_type, body=base64.b64decode(self.body_b64),
                        text=self.text, text_sha256=self.text_sha256,
                        extractor=self.extractor, empty_reason=self.empty_reason,
                        revision_url=self.revision_url)


class Artifact(BaseModel):
    """Everything a replay needs, and nothing derived."""

    model_config = ConfigDict(frozen=True)

    version: int = ARTIFACT_VERSION
    question: str
    as_of: datetime
    params: Params
    snapshots: tuple[StoredSnapshot, ...]
    gather_notes: tuple[str, ...] = ()
    gather_replies: tuple[str, ...] = ()      # the model's search queries, for audit
    argue_replies: tuple[str, ...]
    support_replies: tuple[str, ...] = ()     # empty: support was never judged
    same_replies: tuple[str, ...] = ()        # the same-answer judge: X/Y, then Y/X
    attack_replies: tuple[str, ...]
    # When the same-answer judge was asked (#177), for audit: `as_of` for a
    # live run, the rejudge's own clock for one judged later. None: not
    # recorded — the judge did not run, or the artifact predates the field
    # (run2-judged was judged two days after it was argued, and cannot say
    # so). Nothing is derived from it; replay ignores it.
    same_judged_at: Optional[datetime] = None
    # Who served the model calls (#186): the distinct "model via provider"
    # pairs, as the provider reported them. `served_by` covers the run;
    # `same_served_by` a judge added later by rejudge. None: not recorded (made
    # before the field, or by a model that does not report it); () would mean
    # no call was made. Audit only, like same_judged_at.
    served_by: Optional[tuple[str, ...]] = None
    same_served_by: Optional[tuple[str, ...]] = None

    @model_validator(mode="before")
    @classmethod
    def _predates_the_judge(cls, data: Any) -> Any:
        # Params.judge_same defaults to True for new runs. A stored artifact
        # without the field was made before the judge existed; reading it as
        # True would replay it through a stage it never ran (#172).
        if isinstance(data, dict) and isinstance(data.get("params"), dict) \
                and "judge_same" not in data["params"]:
            data = {**data, "params": {**data["params"], "judge_same": False}}
        if isinstance(data, dict) and isinstance(data.get("params"), dict) \
                and "argue_prompt" not in data["params"]:
            data = {**data, "params": {**data["params"], "argue_prompt": 1}}
        if isinstance(data, dict) and isinstance(data.get("params"), dict) \
                and "counter_set" not in data["params"]:
            data = {**data, "params": {**data["params"], "counter_set": 1}}
        if isinstance(data, dict) and isinstance(data.get("params"), dict) \
                and "reason_wording" not in data["params"]:
            data = {**data, "params": {**data["params"], "reason_wording": 1}}
        if isinstance(data, dict) and isinstance(data.get("params"), dict) \
                and "veto_words" not in data["params"]:
            data = {**data, "params": {**data["params"], "veto_words": 1}}
        if isinstance(data, dict) and isinstance(data.get("params"), dict) \
                and "shown_order" not in data["params"]:
            data = {**data, "params": {**data["params"], "shown_order": 1}}
        return data


class Answer(BaseModel):
    model_config = ConfigDict(frozen=True)

    question: str
    conclusion: Optional[str]
    answer_id: Optional[str]
    status: Optional[Status]
    status_bound_by: tuple[str, ...]
    status_set: Optional[tuple[Status, ...]] = None
    status_set_note: str = "no calibration set: the coverage guarantee is unavailable"
    abstained: bool
    abstain_reason: str
    derivation: Optional[dict[str, Any]]
    positions: tuple[dict[str, Any], ...]
    snapshots: tuple[dict[str, Any], ...]
    counters: dict[str, Count]
    degraded: tuple[str, ...]


# ── running and replaying ───────────────────────────────────

def _served_since(model: Model, start: int) -> Optional[tuple[str, ...]]:
    served = getattr(model, "served", None)
    return None if served is None else tuple(sorted(set(served[start:])))


def run(question: str, model: Model, *, urls: Optional[Sequence[str]] = None,
        n_sources: int = 3, params: Optional[Params] = None,
        as_of: Optional[datetime] = None, http_get: HttpGet = urllib_get,
        calibration: Optional[Calibration] = None) -> tuple[Answer, Artifact]:
    """The whole pipeline. The clock is read once, here, and persisted."""
    params = (params or Params()).model_copy(update={"model": model.name})
    as_of = as_of or datetime.now(timezone.utc)
    start = len(getattr(model, "served", ()))
    snaps, notes, gather_replies = gather(question, at=as_of, urls=urls, n=n_sources,
                                          http_get=http_get, model=model)
    readable = [s for s in snaps if s.text.strip()]
    argue_replies: list[str] = []
    support_replies: list[str] = []
    attack_replies: list[str] = []
    same_replies: list[str] = []
    if readable:
        argue_replies, argued = argue(model, question, readable, k=params.k_argue,
                                      temperature=params.t_argue, max_chars=params.max_chars)
        support_replies, judged = support(model, argued, readable, k=params.k_support,
                                          temperature=params.t_support)
        if support_replies:
            argued, _ = apply_support(argued, judged)
        attack_replies, _ = attack(model, question, argued, k=params.k_attack,
                                   temperature=params.t_attack)
        if params.judge_same:
            pairs = candidate_pairs(argued, question, veto_words=params.veto_words)
            same_replies = judge_same(model, question, pairs,
                                      temperature=params.t_same)
    artifact = Artifact(question=question, as_of=as_of, params=params,
                        snapshots=tuple(StoredSnapshot.of(s) for s in snaps),
                        gather_notes=tuple(notes), gather_replies=tuple(gather_replies),
                        argue_replies=tuple(argue_replies),
                        support_replies=tuple(support_replies),
                        attack_replies=tuple(attack_replies),
                        same_replies=tuple(same_replies),
                        same_judged_at=as_of if params.judge_same else None,
                        served_by=_served_since(model, start))
    return replay(artifact, calibration), artifact


def replay(artifact: Artifact, calibration: Optional[Calibration] = None) -> Answer:
    """Stages 4–7 from the artifact alone. Deterministic; no model.

    With a calibration, the answer also carries a conformal status set."""
    if artifact.version != ARTIFACT_VERSION:
        raise ValueError(f"artifact version {artifact.version}, expected {ARTIFACT_VERSION}")
    snaps, readable, raw, argued, judged = _argued(artifact)
    store = SnapshotStore()
    for s in snaps:
        store.put(s)
    attacked = attack_from_replies(artifact.attack_replies, argued.arguments)
    same: Optional[EquivResult] = None
    claim_group = None
    if artifact.params.judge_same:
        same = equiv_from_replies(artifact.same_replies,
                                  candidate_pairs(argued, artifact.question,
                                                  veto_words=artifact.params.veto_words))
        claim_group = same.groups("claim", [v.pair.a for v in same.verdicts] +
                                  [v.pair.b for v in same.verdicts])
    derived = derive(argued.arguments, attacked.attacks, store, as_of=artifact.as_of,
                     max_age_days=artifact.params.max_age_days, claim_group=claim_group)
    return assemble(artifact, snaps, readable, argued, attacked, derived, calibration, judged,
                    same, raw)


def _argued(artifact: Artifact) -> tuple[list[Snapshot], list[Snapshot], ArgueResult,
                                         ArgueResult, Optional[SupportResult]]:
    """The arguments as the rest of the pipeline sees them, from the artifact
    alone — and as argued, before support dropped any. One function for replay
    and rejudge, so the pairs a re-judge asks about are the pairs a replay will
    read its replies against."""
    snaps = [s.load() for s in artifact.snapshots]
    readable = [s for s in snaps if s.text.strip()]
    raw = argued = argue_from_replies(artifact.argue_replies, readable)
    judged: Optional[SupportResult] = None
    if artifact.support_replies:
        argued, judged = apply_support(argued,
                                       support_from_replies(artifact.support_replies, argued))
    return snaps, readable, raw, argued, judged


def rejudge(artifact: Artifact, model: Model, *, at: datetime) -> tuple[Answer, Artifact]:
    """Add the same-answer judge to a run stored without it (#172).

    Every other stage is read from the artifact, not re-asked, so the only new
    model output is the judge's. Refused when the artifact already carries a
    judge — its replies would be replaced — and when the model is not the one
    the run recorded, since `params.model` names who wrote every reply in it.

    `at` is when the judge is asked, recorded as `same_judged_at` (#177). It
    is required, never read here: the caller owns the clock, as `run` does."""
    if artifact.params.judge_same:
        raise ValueError("this run already went through the same-answer judge")
    if model.name != artifact.params.model:
        raise ValueError(f"run was made by {artifact.params.model!r}; rejudging with "
                         f"{model.name!r} would misattribute the judge's replies")
    _, readable, _, argued, _ = _argued(artifact)
    start = len(getattr(model, "served", ()))
    replies: list[str] = []
    if readable:
        replies = judge_same(model, artifact.question,
                             candidate_pairs(argued, artifact.question,
                                             veto_words=artifact.params.veto_words),
                             temperature=artifact.params.t_same)
    judged = artifact.model_copy(update={
        "params": artifact.params.model_copy(update={"judge_same": True}),
        "same_replies": tuple(replies), "same_judged_at": at,
        "same_served_by": _served_since(model, start)})
    return replay(judged), judged


def canonical(answer: Answer) -> str:
    """Byte-stable serialisation: the replay comparison is on this."""
    return json.dumps(answer.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)


def stored_run(answer: Answer, artifact: Artifact) -> str:
    """The file every live command writes and `replay` reads: the artifact
    (everything the model said and every byte fetched) beside the answer it
    produced, so a replay has something to match against."""
    return json.dumps({"artifact": artifact.model_dump(mode="json"),
                       "answer": json.loads(canonical(answer))}, indent=1)


def contradicted_quotes(answer: Answer) -> tuple[list[dict[str, Any]], int]:
    """The quotes beneath the shown answer that an attack defeated, and how
    many quotes lie beneath it at all (#193). A status can be honest while
    the answer's own sources disagree with each other — run 3's q04 rests on
    "under high wind conditions", which three "moderate winds" arguments
    defeat — and the reader should not have to open the tree to learn it.

    Read from the stored derivation, so every answer already has it and
    replay is unchanged. An abstained answer has no quotes beneath it."""
    hit: dict[str, dict[str, Any]] = {}
    quotes: set[str] = set()
    for _, node, again in derivation_nodes(answer):
        if node["kind"] == "quote" and not again:
            quotes.add(node["id"])
            won = [x for x in node["attacks_received"] if x["succeeded"]]
            if won:
                span = node.get("span") or {}
                hit[node["id"]] = {"id": node["id"], "quote": span.get("quote", ""),
                                   "url": span.get("url", ""),
                                   "by": [{"attacker": x["attacker"], "why": x["rationale"]}
                                          for x in won]}
    return [hit[k] for k in sorted(hit)], len(quotes)


def derivation_nodes(answer: Answer) -> Iterator[tuple[int, dict[str, Any], bool]]:
    """Every node of the shown answer's derivation, depth first, with its
    depth and whether its id was already met. `_tree` cuts cycles but not
    sharing, so an argument two steps rest on appears under both: it is
    yielded again, marked, with its subtree only the first time. Nothing for
    an abstained answer."""
    seen: set[str] = set()

    def walk(node: dict[str, Any], depth: int) -> Iterator[tuple[int, dict[str, Any], bool]]:
        again = node["id"] in seen
        seen.add(node["id"])
        yield depth, node, again
        if not again:              # its subtree was walked where it was first met
            for sub in node["sub_arguments"]:
                yield from walk(sub, depth + 1)

    if answer.derivation is not None:
        yield from walk(answer.derivation, 0)


def support_verdicts(artifact: Artifact) -> dict[str, Optional[str]]:
    """Each surviving quote argument's support verdict, read from the stored
    run: the check on the link between a quote and the conclusion drawn from
    it. None means the judge was never asked (artifacts before #146 or
    without support replies). Read when the answer is shown, not stored in
    it, so every stored answer replays as it was."""
    _, _, _, argued, _ = _argued(artifact)
    return {a.id: a.support for a in argued.arguments if a.kind == "quote"}


def question_details(answer: Answer, artifact: Artifact) -> tuple[tuple[str, ...],
                                                                   list[tuple[str, bool, bool]]]:
    """The details the question supplied that the premise counters can read
    (whole numbers only, #181), and for each: whether the shown answer
    carries it, and whether a quote beneath the answer states it. A detail
    carried with no quote beneath is the question's, not an observation.
    Uses the counters' own predicate (`unquoted_question_numbers`)."""
    nums = question_numbers(answer.question)
    if answer.answer_id is None:
        return nums, []
    _, _, _, argued, _ = _argued(artifact)
    unquoted = unquoted_question_numbers(answer.question, answer.answer_id, argued.by_id())
    carried = set(question_numbers(answer.conclusion or ""))
    return nums, [(n, n in carried, n in carried and n not in unquoted) for n in nums]


# ── assembly ────────────────────────────────────────────────

def _tree(aid: str, argued: ArgueResult, attacked: AttackResult, derived: StatusResult,
          sources: dict[str, Snapshot], seen: frozenset = frozenset()) -> dict[str, Any]:
    a = argued.by_id()[aid]
    st = derived.statuses[aid]
    defeats = set(derived.solved.defeats)
    node: dict[str, Any] = {
        "id": aid, "conclusion": a.conclusion, "kind": a.kind,
        "pramana": a.pramana.name, "label": st.label.value,
        "status": st.status.value if st.status else None,
        "status_bound_by": list(st.status_bound_by), "sample_ids": list(a.sample_ids),
        "attacks_received": [
            {"attacker": x.attacker, "type": x.type, "fallacy": x.fallacy,
             "rationale": x.rationale, "succeeded": (x.attacker, aid) in defeats}
            for x in attacked.attacks if x.target == aid
        ],
    }
    if a.span is not None:
        src = sources.get(a.span.snapshot_id)
        node["span"] = {"snapshot_id": a.span.snapshot_id, "url": src.urls[0] if src else "",
                        "text_sha256": a.span.text_sha256, "start": a.span.start,
                        "end": a.span.end, "quote": a.span.quote, "verdict": a.span.verdict}
        if src is not None and src.revision_url is not None:    # see _cited_snapshot
            node["span"]["revision_url"] = src.revision_url
    node["sub_arguments"] = [
        _tree(s, argued, attacked, derived, sources, seen | {aid})
        for s in a.sub_arguments if s not in seen
    ]
    return node


def _cited_snapshot(s: Snapshot) -> dict[str, Any]:
    out = {"id": s.id, "urls": list(s.urls), "fetched_at": s.fetched_at.isoformat(),
           "text_sha256": s.text_sha256, "extractor": s.extractor}
    # Only when recorded: a key added unconditionally would make every
    # artifact stored before #169 replay as DIFFERS. Its absence is shown to
    # the reader by the CLI, not hidden.
    if s.revision_url is not None:
        out["revision_url"] = s.revision_url
    return out


def _depth(aid: str, argued: ArgueResult, seen: frozenset = frozenset()) -> int:
    subs = [s for s in argued.by_id()[aid].sub_arguments if s not in seen]
    return 1 + max((_depth(s, argued, seen | {aid}) for s in subs), default=0)


def _cited(aid: str, argued: ArgueResult, seen: frozenset = frozenset()) -> set[str]:
    a = argued.by_id()[aid]
    out = {a.span.snapshot_id} if a.span else set()
    for s in a.sub_arguments:
        if s not in seen:
            out |= _cited(s, argued, seen | {aid})
    return out


def assemble(artifact: Artifact, snaps: Sequence[Snapshot], readable: Sequence[Snapshot],
             argued: ArgueResult, attacked: AttackResult, derived: StatusResult,
             calibration: Optional[Calibration] = None,
             judged: Optional[SupportResult] = None,
             same: Optional[EquivResult] = None,
             raw: Optional[ArgueResult] = None) -> Answer:
    by_id = argued.by_id()
    statuses = derived.statuses
    sources = {s.id: s for s in snaps}
    rank = SHOWN_ORDER[artifact.params.shown_order].index
    k = argued.k
    degraded: list[str] = list(artifact.gather_notes)
    for s in snaps:
        if not s.text.strip():
            degraded.append(f"unreadable source {s.urls[0]}: {s.empty_reason}")
        elif len(s.text) > artifact.params.max_chars:
            degraded.append(f"source {s.urls[0]} shown to the model truncated to "
                            f"{artifact.params.max_chars} of {len(s.text)} characters")
    for sid, why in argued.malformed:
        degraded.append(f"argue sample {sid} malformed: {why}")
    for sid, why in attacked.malformed:
        degraded.append(f"attack sample {sid} rejected: {why}")
    if derived.solved.preferred is None:
        degraded.append(derived.solved.preferred_note)
    if same is not None:
        for i, why in same.malformed:
            degraded.append(f"same-answer judge reply {i} malformed: {why}")
        unjudged = [v.pair.id for v in same.verdicts
                    if not v.pair.veto and (v.forward is None or v.backward is None)]
        if unjudged:
            degraded.append(f"same-answer judge: {len(unjudged)} pair(s) not judged in both "
                            f"orders, kept apart: {', '.join(unjudged)}")

    # Positions: distinct answers, each with its best surviving argument. With
    # the same-answer judge, "distinct" is under the question lens (#172);
    # without it, exact normalised wording, as before.
    answer_keys = [norm_conclusion(by_id[a].conclusion) for a in argued.answers if a]
    group_of = same.groups("question", answer_keys) if same else {k: k for k in answer_keys}
    groups: dict[str, list[str]] = {}
    for aid in argued.answers:
        if aid is not None:
            g = groups.setdefault(group_of[norm_conclusion(by_id[aid].conclusion)], [])
            if aid not in g:
                g.append(aid)
    support = Counter(group_of[k] for k in answer_keys)

    def best(ids: list[str]) -> tuple[Optional[str], Optional[Status]]:
        live = [i for i in ids if statuses[i].status is not None]
        if not live:
            return None, None
        # With the judge, a merged position shows its most detailed wording
        # among the best-grounded: the others are consistent with it (#172).
        top = max(live, key=lambda i: (rank(statuses[i].status),
                                       len(by_id[i].conclusion) if same else 0, -int(i[1:])))
        return top, statuses[top].status

    positions = []
    for key, ids in groups.items():
        top, st = best(ids)
        shown = by_id[top].conclusion if same is not None and top else by_id[ids[0]].conclusion
        pos: dict[str, Any] = {"conclusion": shown, "argument_ids": ids,
                               "best_argument": top, "status": st.value if st else None,
                               "samples": support[key]}
        if same is not None:
            # Only with the judge: keys added unconditionally would make every
            # older artifact replay as DIFFERS. The CLI says when it did not run.
            members = {k for k, g in group_of.items() if g == key}
            pos["wordings"] = sorted({by_id[i].conclusion for i in ids})
            pos["kept_apart"] = [
                {"from": v.pair.text_b if v.pair.a in members else v.pair.text_a,
                 "why": v.why_apart, "asked_by_question": v.asked_by_question}
                for v in same.verdicts
                if v.pair.lens == "question" and not v.same
                and (v.pair.a in members) != (v.pair.b in members)]
        positions.append(pos)
    positions.sort(key=lambda p: (-(rank(Status(p["status"])) if p["status"] else -1),
                                  -p["samples"], p["argument_ids"][0]))

    chosen = positions[0] if positions and positions[0]["status"] else None
    if chosen is None:
        abstained = True
        if not readable:
            reason = "gather: no readable source"
        elif argued.malformed and len(argued.malformed) == k:
            reason = "argue: every sample was malformed"
        elif positions:
            reason = "solve: every proposed answer was defeated"
        elif any("does not support its claim" in n for n in argued.answer_notes):
            reason = ("support: every proposed answer rested on a quote that, read in "
                      "context, does not support its claim")
        elif any(n.startswith("answer step") for n in argued.answer_notes):
            reason = ("check: every proposed answer was dropped — its quote or a premise "
                      "failed span verification")
        elif all(n == "model abstained" for n in argued.answer_notes if n):
            # The model returning nothing is all that was observed: the sources
            # may be silent, or the question's premise false (run 4's
            # false-premise control, #188). Nothing here tells which.
            reason = ("argue: the model found no answer in the sources"
                      if artifact.params.reason_wording < 2 else
                      "argue: the model returned no answer from the sources — this does "
                      "not say whether they are silent or the question's premise is false")
        else:
            reason = "argue: no sample produced an answer"
    else:
        abstained, reason = False, ""

    answer_id = chosen["best_argument"] if chosen else None
    ans_status = statuses[answer_id] if answer_id else None
    cited_ids = _cited(answer_id, argued) if answer_id else set()
    cited = [s for s in snaps if s.id in cited_ids]

    # ── features: every one a count over a named population ──
    vc = argued.verdict_counts()
    claimed = argued.spans_claimed
    steps_claimed = sum(1 for _ in argued.dropped) + sum(1 for _ in argued.cascade) + \
        sum(len(by_id[a].sample_ids) for a in by_id)
    agree = support[group_of[norm_conclusion(by_id[answer_id].conclusion)]] if answer_id else 0
    ages = [(artifact.as_of - s.fetched_at).days for s in cited]
    counters = {
        "k": Count(n=k, of=artifact.params.k_argue, population="argue samples requested"),
        "agree_frac": Count(n=agree, of=k, population="samples whose answer is the chosen conclusion"),
        "n_positions": Count(n=len(positions), of=sum(1 for a in argued.answers if a),
                             population="samples that produced a surviving answer"),
        "verified_frac": Count(n=sum(vc[v] for v in ADMITTED), of=claimed, population="quotes claimed"),
        "absent_frac": Count(n=vc["absent"], of=claimed, population="quotes claimed"),
        "punctuation_frac": Count(n=vc["punctuation"], of=claimed, population="quotes claimed"),
        "unresolvable_frac": Count(n=vc["unresolvable"], of=claimed, population="quotes claimed"),
        "direct_drops": Count(n=len(argued.dropped), of=steps_claimed, population="steps claimed"),
        "cascade_drops": Count(n=len(argued.cascade), of=steps_claimed, population="steps claimed"),
        "n_snapshots": Count(n=len({s.text_sha256 for s in cited}), of=len(snaps),
                             population="snapshots gathered (cited, by distinct text)"),
        "n_hosts": Count(n=len({host(u) for s in cited for u in s.urls}), of=len(cited),
                         population="cited snapshots (host names; not registrable domains)"),
        "oldest_days": Count(n=max(ages, default=0), of=len(cited), population="cited snapshots"),
        "chain_depth": Count(n=_depth(answer_id, argued) if answer_id else 0, of=len(by_id),
                             population="arguments"),
        "pramana_floor": Count(n=int(chain_pramana(by_id)[answer_id]) if answer_id else 0,
                               of=4, population="pramana scale (1 upamana .. 4 pratyaksa)"),
        "attack_density": Count(n=len(attacked.attacks), of=len(by_id), population="arguments"),
        "minority_attacks": Count(n=len(attacked.minority),
                                  of=len(attacked.minority) + len(attacked.attacks),
                                  population="distinct edges proposed"),
        "retrieval_hits": Count(n=len(readable), of=len(snaps), population="snapshots gathered"),
        "support_judged": Count(n=len(judged.verdicts) if judged else 0,
                                of=len(judged.verdicts) if judged else
                                sum(1 for a in by_id.values() if a.kind == "quote"),
                                population="verified quote arguments"),
        "support_dropped": Count(n=len(judged.dropped) if judged else 0,
                                 of=len(judged.verdicts) if judged else 0,
                                 population="quote arguments judged"),
        "support_cannot_tell": Count(n=sum(v == "cannot_tell" for v in judged.verdicts.values())
                                     if judged else 0,
                                     of=len(judged.verdicts) if judged else 0,
                                     population="quote arguments judged"),
        "support_cascade": Count(n=len(judged.cascade) if judged else 0,
                                 of=len(judged.verdicts) if judged else 0,
                                 population="quote arguments judged (arguments lost with them)"),
    }
    # What the premise counters can see (#181): only whole numbers, so on a
    # question without one their zero is "could not look". Said every time,
    # zero included.
    nums = question_numbers(artifact.question)
    reach = "" if artifact.params.counter_set < 3 else (
        f"; the question has {len(nums)} whole number(s) to check ({', '.join(nums)})" if nums
        else "; the question has no whole number, so this cannot fire")
    if artifact.params.argue_prompt >= 2 and raw is not None:
        # Counted over the arguments as argued, before support dropped any:
        # the dropped ones are the case this measures (#161). Shown at zero too.
        quotes = [a for a in raw.arguments if a.kind == "quote"]
        counters["question_number_added"] = Count(
            n=sum(adds_question_number(artifact.question, a) for a in quotes), of=len(quotes),
            population="quote arguments whose conclusion carries a number from the question "
                       "that the quote does not state (before the support judge)" + reach)
    if artifact.params.counter_set >= 2 and raw is not None:
        # The same question for the model's own steps (#179), which the
        # support judge never sees: a number the question supplied, carried
        # with no quote beneath it. Before support, as above.
        raw_by = raw.by_id()
        steps = [a for a in raw.arguments if a.kind != "quote"]
        counters["question_number_unquoted"] = Count(
            n=sum(bool(unquoted_question_numbers(artifact.question, a.id, raw_by))
                  for a in steps), of=len(steps),
            population="inference and analogy steps whose conclusion carries a number from "
                       "the question that no quote beneath them states, directly or through "
                       "other steps (before the support judge)" + reach)
    if same is not None:
        # Only with the judge, like the position fields (see there). Merged
        # samples may be less precise than the answer shown, so the count says
        # "consistent with", not "the same as".
        counters["agree_frac"] = Count(
            n=counters["agree_frac"].n, of=counters["agree_frac"].of,
            population="samples whose answer is consistent with the chosen conclusion "
                       "(same-answer judge, question lens)")
        for lens in ("question", "claim"):
            vs = [v for v in same.verdicts if v.pair.lens == lens]
            judged_both = [v for v in vs if v.forward is not None and v.backward is not None]
            counters[f"same_{lens}_vetoed"] = Count(
                n=sum(bool(v.pair.veto) for v in vs), of=len(vs),
                population=f"{lens}-lens pairs")
            counters[f"same_{lens}_merged"] = Count(
                n=sum(v.same for v in vs), of=len(vs), population=f"{lens}-lens pairs")
            counters[f"same_{lens}_order_disagree"] = Count(
                n=sum(v.forward != v.backward for v in judged_both), of=len(judged_both),
                population=f"{lens}-lens pairs judged in both orders")

    status_set: Optional[tuple[Status, ...]] = None
    set_note = "no calibration set: the coverage guarantee is unavailable"
    if calibration is not None:
        derived_status = ans_status.status.value if ans_status and not abstained else ABSTAINED
        status_set, set_note = calibration.predict(derived_status)

    return Answer(
        question=artifact.question,
        status_set=status_set, status_set_note=set_note,
        conclusion=by_id[answer_id].conclusion if answer_id else None,
        answer_id=answer_id,
        status=ans_status.status if ans_status else None,
        status_bound_by=ans_status.status_bound_by if ans_status else (),
        abstained=abstained, abstain_reason=reason,
        derivation=_tree(answer_id, argued, attacked, derived, sources) if answer_id else None,
        positions=tuple(positions),
        snapshots=tuple(_cited_snapshot(s) for s in cited),
        counters=counters, degraded=tuple(degraded),
    )
