"""Stage 5 — ASPIC+ grounded and preferred semantics, with no knowledge base (#141).

Occam owns this solver rather than importing the engine's. The engine's is
knowledge-base-free at the file level, but importing it executes the engine
package's `__init__`, which loads the whole knowledge-base pipeline (#150).
A law holds the grounded labelling here identical to the engine's
`compute_grounded` over randomised frameworks, so the copy cannot drift.

The defeat relation (unchanged from the engine)
───────────────────────────────────────────────
    undercutting  always defeats — it attacks the inference, not the conclusion
    rebutting     never defeats a strict target; otherwise preference decides
    undermining   preference decides

    preference: higher pramāṇa wins outright; equal pramāṇa → the attacker
                defeats iff it is not strictly weaker in strength

An argument's pramāṇa for preference is the minimum along its chain: an
inference over a quoted premise is no stronger than the testimony it rests
on. Without that, an ANUMANA step (3) would outrank every SABDA quote (2) it
was built from.

Attacks on sub-arguments (ASPIC+ proper)
────────────────────────────────────────
An attack on B′ is an attack on every argument that contains B′, and whether
it succeeds is decided against B′. The engine's frameworks are flat, so it
never needed this; Occam's derivations are trees, and without it a rebutted
premise would leave the inference built on it standing.

Two semantics, because the difference is a finding
──────────────────────────────────────────────────
Grounded is the sceptical reading: unique, a fixpoint. Preferred extensions
are the maximal admissible sets; an argument IN some preferred extension is
*credulously* accepted — some coherent position defends it.

A theorem the status stage depends on, and a law checks: an argument OUT in
grounded is IN no preferred extension. (Its grounded-IN defeater is in every
preferred extension, and conflict-freeness excludes it.) So the informative
split is inside UNDECIDED: credulously accepted there means a real case each
way; accepted in no extension means no coherent position holds it.
"""

from __future__ import annotations

from enum import Enum
from itertools import combinations
from typing import Mapping, Optional, Sequence

from pydantic import BaseModel, ConfigDict

from .argue import Argument
from .attack import Attack, check_edges
from .types import Pramana

__all__ = ["Label", "SolveResult", "solve", "solve_graph", "chain_pramana",
           "supers_of", "MAX_UNDECIDED"]

# Preferred semantics is exponential in the number of grounded-UNDECIDED
# arguments. Past this many, preferred is not computed and the result says
# so — a skipped computation must not read as an empty one.
MAX_UNDECIDED = 16


class Label(str, Enum):
    IN = "in"
    OUT = "out"
    UNDECIDED = "undecided"


class SolveResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    grounded: dict[str, Label]
    defeats: tuple[tuple[str, str], ...]              # (defeater, defeated), lifted
    preferred: Optional[tuple[frozenset[str], ...]]   # None: not computed
    preferred_note: str = ""

    @property
    def credulous(self) -> Optional[frozenset[str]]:
        """Arguments IN at least one preferred extension, or None if not computed."""
        if self.preferred is None:
            return None
        return frozenset().union(*self.preferred) if self.preferred else frozenset()


def chain_pramana(arguments: Mapping[str, Argument]) -> dict[str, Pramana]:
    """Each argument's pramāṇa for preference: the minimum along its chain."""
    memo: dict[str, Pramana] = {}

    def go(aid: str, seen: frozenset) -> Pramana:
        if aid in memo:
            return memo[aid]
        a = arguments[aid]
        p = a.pramana
        for s in a.sub_arguments:
            if s not in seen:                       # guard: never recurse a cycle
                p = min(p, go(s, seen | {aid}))
        memo[aid] = Pramana(p)
        return memo[aid]

    return {aid: go(aid, frozenset()) for aid in arguments}


def supers_of(subs: Mapping[str, Sequence[str]]) -> dict[str, frozenset[str]]:
    """For each argument, every argument containing it (itself included)."""
    parents: dict[str, set[str]] = {aid: set() for aid in subs}
    for aid, ss in subs.items():
        for s in ss:
            parents[s].add(aid)
    out: dict[str, frozenset[str]] = {}
    for aid in subs:
        seen, stack = {aid}, [aid]
        while stack:
            for p in parents[stack.pop()]:
                if p not in seen:
                    seen.add(p)
                    stack.append(p)
        out[aid] = frozenset(seen)
    return out


def _defeats(att: str, tgt: str, attack: Attack, pramana: Mapping[str, Pramana],
             strength: Mapping[str, int], strict: frozenset[str]) -> bool:
    if attack.type == "undercutting":
        return True
    if attack.type == "rebutting" and tgt in strict:
        return False
    a_p, t_p = pramana[att], pramana[tgt]
    if t_p > a_p:
        return False
    if a_p > t_p:
        return True
    return strength.get(att, 0) >= strength.get(tgt, 0)


def solve(arguments: Sequence[Argument], attacks: Sequence[Attack], *,
          strength: Optional[Mapping[str, int]] = None,
          strict: frozenset[str] = frozenset()) -> SolveResult:
    """Label every argument under grounded semantics, and enumerate preferred.

    `strength` breaks pramāṇa ties (higher is stronger); omitted, every
    argument is equally strong and a tie defeats. `strict` names arguments
    with a strict top rule — Occam never produces one, because a model that
    could declare its own steps strict could make them unrebuttable.
    """
    args = {a.id: a for a in arguments}
    return solve_graph({a.id: a.sub_arguments for a in arguments}, attacks,
                       pramana=chain_pramana(args), strength=strength, strict=strict)


def solve_graph(subs: Mapping[str, Sequence[str]], attacks: Sequence[Attack], *,
                pramana: Mapping[str, Pramana],
                strength: Optional[Mapping[str, int]] = None,
                strict: frozenset[str] = frozenset()) -> SolveResult:
    """The solver over bare structure: sub-argument edges, attacks, and each
    argument's pramāṇa. `solve` derives the pramāṇa and calls this; the
    agreement law calls it directly with arbitrary pramāṇas."""
    args = dict(subs)
    check_edges(attacks, args)
    supers = supers_of(subs)
    strength = strength or {}

    defeat_pairs: set[tuple[str, str]] = set()
    for atk in attacks:
        if _defeats(atk.attacker, atk.target, atk, pramana, strength, strict):
            for b in supers[atk.target]:
                defeat_pairs.add((atk.attacker, b))
    defeaters: dict[str, set[str]] = {aid: set() for aid in args}
    for x, b in defeat_pairs:
        defeaters[b].add(x)

    grounded = _grounded(args, defeaters)
    undecided = sorted(a for a, l in grounded.items() if l == Label.UNDECIDED)
    if len(undecided) > MAX_UNDECIDED:
        return SolveResult(
            grounded=grounded, defeats=tuple(sorted(defeat_pairs)), preferred=None,
            preferred_note=(f"preferred not computed: {len(undecided)} undecided "
                            f"arguments exceeds the limit of {MAX_UNDECIDED}"),
        )
    base = frozenset(a for a, l in grounded.items() if l == Label.IN)
    return SolveResult(grounded=grounded, defeats=tuple(sorted(defeat_pairs)),
                       preferred=_preferred(base, undecided, defeaters))


def _grounded(args: Mapping[str, object],
              defeaters: Mapping[str, set[str]]) -> dict[str, Label]:
    """The least fixpoint: IN when every defeater is OUT; OUT when some is IN."""
    labels: dict[str, Label] = {}
    changed = True
    while changed:
        changed = False
        for aid in args:
            if aid in labels:
                continue
            ds = defeaters[aid]
            if all(labels.get(d) == Label.OUT for d in ds):
                labels[aid] = Label.IN
                changed = True
            elif any(labels.get(d) == Label.IN for d in ds):
                labels[aid] = Label.OUT
                changed = True
    return {aid: labels.get(aid, Label.UNDECIDED) for aid in args}


def _admissible(s: frozenset[str], defeaters: Mapping[str, set[str]]) -> bool:
    for a in s:
        if defeaters[a] & s:
            return False                                   # not conflict-free
        for d in defeaters[a]:
            if not (defeaters[d] & s):
                return False                               # undefended
    return True


def _preferred(base: frozenset[str], undecided: list[str],
               defeaters: Mapping[str, set[str]]) -> tuple[frozenset[str], ...]:
    """Maximal admissible supersets of the grounded extension.

    Every preferred extension contains the grounded extension and excludes
    everything grounded labels OUT, so only the UNDECIDED arguments are
    searched — largest subsets first, so the first admissible set found at a
    size is maximal unless a larger one already contains it.
    """
    found: list[frozenset[str]] = []
    for size in range(len(undecided), -1, -1):
        for combo in combinations(undecided, size):
            cand = base | frozenset(combo)
            if any(cand <= f for f in found):
                continue
            if _admissible(cand, defeaters):
                found.append(cand)
    return tuple(sorted(found, key=lambda f: sorted(f)))
