"""Stage 6 — status derived from both extensions, bound by the weakest link (#142, #148).

Status is computed here and nowhere else. It reads two things: what each
argument's provenance allows (its *ceiling*), and how the two semantics
labelled it. No caller supplies a status; `Argument` refuses the field.

Ceilings — what the provenance allows
─────────────────────────────────────
    quote leaf, verified, discriminating, fresh,
      and its conclusion literally in the quote   ESTABLISHED
    quote whose conclusion restates it            HYPOTHESIS   the words are the model's (#158)
    quote whose support was never judged          HYPOTHESIS   not checked is not checked-and-fine
    quote whose support the judge could not tell  PROVISIONAL  (#146; does_not_support is dropped)
    quote from a snapshot older than max_age      HYPOTHESIS   stale
    quote whose snapshot cannot be found          HYPOTHESIS   freshness unknown — never "fresh"
    inference step                                HYPOTHESIS   the step is the model's
    quote too short to discriminate (#148)        PROVISIONAL
    analogy step                                  PROVISIONAL

An argument's ceiling is the minimum over its own and its sub-arguments' —
the weakest link. A well-sourced conclusion resting on one weak step is not
established.

Labels — what the semantics decided
───────────────────────────────────
    grounded IN                                   the ceiling
    grounded UNDECIDED, IN some preferred         CONTESTED — a real case each way
    grounded UNDECIDED, IN no preferred           OPEN — no coherent position holds it
    grounded UNDECIDED, preferred not computed    OPEN, and the bound says why
    grounded OUT                                  no status: rejected

#142 defined `contested` as "OUT in grounded, IN in preferred". That cannot
happen: an argument OUT in grounded has a grounded-IN defeater, which is in
every preferred extension (see solve.py; a law checks it). So `contested`
here is the reachable version of the same idea — undecided sceptically,
defended credulously — and `open` is undecided with no defence at all.

Corroboration — what one source cannot give (#162)
──────────────────────────────────────────────────
A ceiling reads one argument's provenance, and no reading of one document can
catch that document lying: the adversarial control's page really does say
water boils at 50 °C, and every check above passes it. So `established`
also needs a second host. An argument that would be established keeps it
only if the grounded-IN quote arguments sharing its conclusion (normalised as
argue merges them), each with an established ceiling of its own, cite
snapshots from at least MIN_HOSTS hosts and MIN_HOSTS distinct texts.
Otherwise it is a hypothesis, bound by "rests on a single source (<hosts>)".
Texts too, because identical text is one source (see snapshot.py): the same
bytes fetched from a mirror merge into one snapshot carrying both URLs, and
counting its hosts alone would let one document vouch for itself (#165).

It is applied after solving, to the status and not the ceiling, for two
reasons. It is a fact about the set of surviving arguments, and survival is
what solving decides — counting a defeated page as corroboration would let a
rejected source vouch for an accepted one. And the ceiling is the argument's
strength in the attack graph: one well-quoted page is exactly as strong
against a rival as it was, it simply is not enough on its own to be the top.

Hosts are a proxy for independence, and a weak one in both directions: two
pages on one site count once, and two sites copying each other count twice.
Every Wikipedia-only answer is one host, so it tops out at hypothesis.

`status_bound_by` is the deliverable
────────────────────────────────────
It names every constraint sitting at the minimum, which is the same thing as
answering "what would change this answer?". A tuple, because bounds tie and
naming one of two tied constraints misstates what lifting it would do. An
established argument is bound by the top of the lattice, named as such —
never by an empty tuple, which would read as "nothing constrains this".
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

from pydantic import BaseModel, ConfigDict

from .argue import Argument, norm_conclusion
from .attack import Attack
from .snapshot import Snapshot, SnapshotStore, host
from .solve import Label, SolveResult, solve
from .spans import is_discriminating, states
from .types import STATUS_ORDER, Status, rank

__all__ = ["ArgStatus", "StatusResult", "derive", "ceilings", "MAX_AGE_DAYS", "MIN_HOSTS"]

MAX_AGE_DAYS = 365
MIN_HOSTS = 2

TOP = "top of the lattice"


class ArgStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    label: Label
    credulous: Optional[bool]          # None: preferred was not computed
    ceiling: Status
    status: Optional[Status]           # None: rejected (grounded OUT)
    status_bound_by: tuple[str, ...]

    @property
    def rejected(self) -> bool:
        return self.status is None


class StatusResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    as_of: datetime
    max_age_days: int
    solved: SolveResult
    statuses: dict[str, ArgStatus]


def _snapshot(a: Argument, store: SnapshotStore) -> Optional[Snapshot]:
    snap = store.get(a.span.snapshot_id)
    if snap is None:
        for other in store.ids_for_text(a.span.text_sha256):
            return store.get(other)
    return snap


def _own_ceiling(a: Argument, store: SnapshotStore, as_of: datetime,
                 max_age_days: int) -> tuple[Status, tuple[str, ...]]:
    if a.kind == "analogy":
        return Status.PROVISIONAL, (f"analogy step {a.id}",)
    if a.kind == "inference":
        return Status.HYPOTHESIS, (f"inference step {a.id}",)
    bounds: list[tuple[Status, str]] = []
    if a.support is None:
        bounds.append((Status.HYPOTHESIS, f"quote {a.id}: support not judged"))
    elif a.support == "cannot_tell":
        bounds.append((Status.PROVISIONAL, f"quote {a.id}: support could not be judged"))
    if not states(a.span.quote, a.conclusion):
        # The quote verified; the conclusion is the model's restatement of it.
        # A restatement is an inference over the quote, so it caps where every
        # other model inference does (#158).
        bounds.append((Status.HYPOTHESIS, f"quote {a.id} restated in the model's words"))
    if not is_discriminating(a.span.quote):
        bounds.append((Status.PROVISIONAL, f"quote {a.id} too short to discriminate"))
    snap = _snapshot(a, store)
    if snap is None:
        bounds.append((Status.HYPOTHESIS, f"quote {a.id}: snapshot not held, freshness unknown"))
    else:
        age = (as_of - snap.fetched_at).days
        if age > max_age_days:
            bounds.append((Status.HYPOTHESIS,
                           f"quote {a.id} stale: {age} days old (limit {max_age_days})"))
    if not bounds:
        return Status.ESTABLISHED, (TOP,)
    low = min(bounds, key=lambda b: rank(b[0]))[0]
    return low, tuple(why for s, why in bounds if s == low)


def ceilings(arguments: Sequence[Argument], store: SnapshotStore, as_of: datetime,
             max_age_days: int = MAX_AGE_DAYS) -> dict[str, tuple[Status, tuple[str, ...]]]:
    """Each argument's ceiling and what binds it, weakest link over the chain."""
    args = {a.id: a for a in arguments}
    own = {aid: _own_ceiling(a, store, as_of, max_age_days) for aid, a in args.items()}
    memo: dict[str, tuple[Status, tuple[str, ...]]] = {}

    def go(aid: str, seen: frozenset) -> tuple[Status, tuple[str, ...]]:
        if aid in memo:
            return memo[aid]
        parts = [own[aid]] + [go(s, seen | {aid}) for s in args[aid].sub_arguments
                              if s not in seen]
        low = min(rank(p[0]) for p in parts)
        bound: list[str] = []
        for s, why in parts:
            if rank(s) == low:
                bound.extend(w for w in why if w not in bound)
        if len(bound) > 1 and TOP in bound:
            bound.remove(TOP)
        memo[aid] = (STATUS_ORDER[low], tuple(bound))
        return memo[aid]

    return {aid: go(aid, frozenset()) for aid in args}


def derive(arguments: Sequence[Argument], attacks: Sequence[Attack],
           store: SnapshotStore, *, as_of: datetime,
           max_age_days: int = MAX_AGE_DAYS) -> StatusResult:
    """Solve, then read every argument's status off the two extensions.

    `as_of` is required and never defaulted to now: freshness must come out
    the same on replay, and a clock read here would make it depend on when
    the replay ran.
    """
    ceil = ceilings(arguments, store, as_of, max_age_days)
    solved = solve(arguments, attacks, strength={a: rank(c[0]) for a, c in ceil.items()})
    credulous = solved.credulous
    by_label: dict[str, tuple[Optional[Status], tuple[str, ...]]] = {}
    for aid, label in solved.grounded.items():
        c_status, c_bound = ceil[aid]
        if label == Label.IN:
            by_label[aid] = (c_status, c_bound)
        elif label == Label.OUT:
            by_label[aid] = (None, (f"{aid} defeated in the grounded extension",))
        elif credulous is None:
            by_label[aid] = (Status.OPEN, (f"{aid} undecided; {solved.preferred_note}",))
        elif aid in credulous:
            by_label[aid] = (Status.CONTESTED,
                             (f"{aid} undecided sceptically but defended in a preferred extension",))
        else:
            by_label[aid] = (Status.OPEN, (f"{aid} undecided and defended in no preferred extension",))

    # Corroboration (#162): see the module docstring.
    hosts_of: dict[str, set[str]] = {}
    texts_of: dict[str, set[str]] = {}
    for a in arguments:
        if (a.kind == "quote" and solved.grounded[a.id] == Label.IN
                and ceil[a.id][0] == Status.ESTABLISHED):
            snap = _snapshot(a, store)
            key = norm_conclusion(a.conclusion)
            hosts_of.setdefault(key, set()).update(host(u) for u in snap.urls)
            texts_of.setdefault(key, set()).add(snap.text_sha256)
    for a in arguments:
        st, _ = by_label[a.id]
        if st == Status.ESTABLISHED:
            key = norm_conclusion(a.conclusion)
            hosts = hosts_of[key]
            if len(hosts) < MIN_HOSTS or len(texts_of[key]) < MIN_HOSTS:
                by_label[a.id] = (Status.HYPOTHESIS,
                                  (f"rests on a single source ({', '.join(sorted(hosts))})",))
    # ≥2 hosts and ≥2 distinct texts together mean two different documents on
    # two different hosts: a mirror adds a host but no text (#165), a second
    # page on one site adds a text but no host.

    # No second weakest-link pass over labels. Lifting attacks to the
    # arguments containing their targets already orders the labels: a parent
    # is IN only if every sub-argument is, OUT whenever one is, and
    # credulously accepted only if every sub-argument is. A law checks all
    # three on random trees; a second pass here would only mask a fault in
    # the first.
    statuses = {}
    for aid, label in solved.grounded.items():
        st, bound = by_label[aid]
        statuses[aid] = ArgStatus(
            id=aid, label=label,
            credulous=None if credulous is None else aid in credulous,
            ceiling=ceil[aid][0], status=st, status_bound_by=bound,
        )
    return StatusResult(as_of=as_of, max_age_days=max_age_days, solved=solved,
                        statuses=statuses)
