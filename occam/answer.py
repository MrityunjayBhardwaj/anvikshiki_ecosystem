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
from typing import Any, Optional, Sequence

from pydantic import BaseModel, ConfigDict

from .argue import ArgueResult, argue, argue_from_replies, norm_conclusion
from .attack import AttackResult, attack, attack_from_replies
from .conformal import ABSTAINED, Calibration
from .gather import HttpGet, gather, urllib_get
from .model import Model
from .snapshot import Snapshot, SnapshotStore, host
from .solve import chain_pramana
from .spans import ADMITTED
from .support import SupportResult, apply_support, support, support_from_replies
from .status import MAX_AGE_DAYS, StatusResult, derive
from .types import Status, rank

__all__ = ["Count", "Answer", "Artifact", "Params", "run", "replay", "assemble", "canonical"]

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

    @classmethod
    def of(cls, s: Snapshot) -> "StoredSnapshot":
        return cls(id=s.id, urls=s.urls, fetched_at=s.fetched_at, media_type=s.media_type,
                   body_b64=base64.b64encode(s.body).decode(), text=s.text,
                   text_sha256=s.text_sha256, extractor=s.extractor,
                   empty_reason=s.empty_reason)

    def load(self) -> Snapshot:
        # Snapshot re-hashes body and text on construction, so a tampered
        # artifact fails here, loudly, rather than replaying something else.
        return Snapshot(id=self.id, urls=self.urls, fetched_at=self.fetched_at,
                        media_type=self.media_type, body=base64.b64decode(self.body_b64),
                        text=self.text, text_sha256=self.text_sha256,
                        extractor=self.extractor, empty_reason=self.empty_reason)


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
    attack_replies: tuple[str, ...]


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

def run(question: str, model: Model, *, urls: Optional[Sequence[str]] = None,
        n_sources: int = 3, params: Optional[Params] = None,
        as_of: Optional[datetime] = None, http_get: HttpGet = urllib_get,
        calibration: Optional[Calibration] = None) -> tuple[Answer, Artifact]:
    """The whole pipeline. The clock is read once, here, and persisted."""
    params = (params or Params()).model_copy(update={"model": model.name})
    as_of = as_of or datetime.now(timezone.utc)
    snaps, notes, gather_replies = gather(question, at=as_of, urls=urls, n=n_sources,
                                          http_get=http_get, model=model)
    readable = [s for s in snaps if s.text.strip()]
    argue_replies: list[str] = []
    support_replies: list[str] = []
    attack_replies: list[str] = []
    if readable:
        argue_replies, argued = argue(model, question, readable, k=params.k_argue,
                                      temperature=params.t_argue, max_chars=params.max_chars)
        support_replies, judged = support(model, argued, readable, k=params.k_support,
                                          temperature=params.t_support)
        if support_replies:
            argued, _ = apply_support(argued, judged)
        attack_replies, _ = attack(model, question, argued, k=params.k_attack,
                                   temperature=params.t_attack)
    artifact = Artifact(question=question, as_of=as_of, params=params,
                        snapshots=tuple(StoredSnapshot.of(s) for s in snaps),
                        gather_notes=tuple(notes), gather_replies=tuple(gather_replies),
                        argue_replies=tuple(argue_replies),
                        support_replies=tuple(support_replies),
                        attack_replies=tuple(attack_replies))
    return replay(artifact, calibration), artifact


def replay(artifact: Artifact, calibration: Optional[Calibration] = None) -> Answer:
    """Stages 4–7 from the artifact alone. Deterministic; no model.

    With a calibration, the answer also carries a conformal status set."""
    if artifact.version != ARTIFACT_VERSION:
        raise ValueError(f"artifact version {artifact.version}, expected {ARTIFACT_VERSION}")
    snaps = [s.load() for s in artifact.snapshots]
    store = SnapshotStore()
    for s in snaps:
        store.put(s)
    readable = [s for s in snaps if s.text.strip()]
    argued = argue_from_replies(artifact.argue_replies, readable)
    judged: Optional[SupportResult] = None
    if artifact.support_replies:
        argued, judged = apply_support(argued,
                                       support_from_replies(artifact.support_replies, argued))
    attacked = attack_from_replies(artifact.attack_replies, argued.arguments)
    derived = derive(argued.arguments, attacked.attacks, store, as_of=artifact.as_of,
                     max_age_days=artifact.params.max_age_days)
    return assemble(artifact, snaps, readable, argued, attacked, derived, calibration, judged)


def canonical(answer: Answer) -> str:
    """Byte-stable serialisation: the replay comparison is on this."""
    return json.dumps(answer.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)


# ── assembly ────────────────────────────────────────────────

def _tree(aid: str, argued: ArgueResult, attacked: AttackResult, derived: StatusResult,
          urls: dict[str, str], seen: frozenset = frozenset()) -> dict[str, Any]:
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
        node["span"] = {"snapshot_id": a.span.snapshot_id, "url": urls.get(a.span.snapshot_id, ""),
                        "text_sha256": a.span.text_sha256, "start": a.span.start,
                        "end": a.span.end, "quote": a.span.quote, "verdict": a.span.verdict}
    node["sub_arguments"] = [
        _tree(s, argued, attacked, derived, urls, seen | {aid})
        for s in a.sub_arguments if s not in seen
    ]
    return node


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
             judged: Optional[SupportResult] = None) -> Answer:
    by_id = argued.by_id()
    statuses = derived.statuses
    urls = {s.id: s.urls[0] for s in snaps}
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

    # Positions: distinct answer conclusions, each with its best surviving argument.
    groups: dict[str, list[str]] = {}
    for aid in argued.answers:
        if aid is not None:
            groups.setdefault(norm_conclusion(by_id[aid].conclusion), [])
            if aid not in groups[norm_conclusion(by_id[aid].conclusion)]:
                groups[norm_conclusion(by_id[aid].conclusion)].append(aid)
    support = Counter(norm_conclusion(by_id[a].conclusion) for a in argued.answers if a)

    def best(ids: list[str]) -> tuple[Optional[str], Optional[Status]]:
        live = [i for i in ids if statuses[i].status is not None]
        if not live:
            return None, None
        top = max(live, key=lambda i: (rank(statuses[i].status), -int(i[1:])))
        return top, statuses[top].status

    positions = []
    for key, ids in groups.items():
        top, st = best(ids)
        positions.append({"conclusion": by_id[ids[0]].conclusion, "argument_ids": ids,
                          "best_argument": top, "status": st.value if st else None,
                          "samples": support[key]})
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
            reason = "argue: the model found no answer in the sources"
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
    agree = support[norm_conclusion(by_id[answer_id].conclusion)] if answer_id else 0
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
        derivation=_tree(answer_id, argued, attacked, derived, urls) if answer_id else None,
        positions=tuple(positions),
        snapshots=tuple({"id": s.id, "urls": list(s.urls), "fetched_at": s.fetched_at.isoformat(),
                         "text_sha256": s.text_sha256, "extractor": s.extractor}
                        for s in cited),
        counters=counters, degraded=tuple(degraded),
    )
