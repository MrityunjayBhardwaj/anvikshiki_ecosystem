# anvikshiki_v4/argumentation.py
"""
Argumentation engine computing ASPIC+ grounded semantics
via Datalog-style fixpoint evaluation over provenance semirings.

References:
  - Wu, Caminada & Gabbay 2009 (grounded semantics)
  - Prakken 2010 (ASPIC+ framework)
  - Diller et al. KR 2025 (grounding ASPIC+ with Datalog)
"""

from dataclasses import dataclass, field
from itertools import combinations
from typing import Mapping, Optional
from .schema_v4 import (
    Argument, Attack, Label, ProvenanceTag, EpistemicStatus
)
from .lattice import BOUND_ASSERTED, join, rank

# Preferred semantics is exponential in the grounded-UNDECIDED arguments. Past
# this many it is not computed, and the result says so. Occam's solver holds
# the same limit, and a law holds the two solvers' answers equal.
MAX_UNDECIDED = 16


def _admissible(s: frozenset[str], defeaters: Mapping[str, set[str]]) -> bool:
    """Conflict-free over defeats, and every defeater of a member is defeated
    by some member."""
    for aid in s:
        if defeaters[aid] & s:
            return False
        if any(not defeaters[d] & s for d in defeaters[aid]):
            return False
    return True


@dataclass
class ArgumentationFramework:
    """
    The instantiated argumentation framework.
    Computed from KB at compile time. Evaluated at query time.
    """
    arguments: dict[str, Argument] = field(default_factory=dict)
    attacks: list[Attack] = field(default_factory=list)
    labels: dict[str, Label] = field(default_factory=dict)
    # Ids of the premise arguments the question supplied. They are the
    # conditions a query reasons under, not evidence for what follows from
    # them; `t2_compiler_v4.QUESTION_STATUS` says why and how they are graded.
    supposed: set[str] = field(default_factory=set)

    # Index structures for efficient lookup
    _attackers_of: dict[str, list[str]] = field(default_factory=dict)
    _attacks_on: dict[str, list[Attack]] = field(default_factory=dict)
    _next_id: int = field(default=0)

    def add_argument(self, arg: Argument):
        """Add an argument to the framework."""
        self.arguments[arg.id] = arg

    def add_attack(self, attack: Attack):
        """Add an attack and update index structures."""
        self.attacks.append(attack)
        self._attackers_of.setdefault(attack.target, []).append(
            attack.attacker)
        self._attacks_on.setdefault(attack.target, []).append(attack)

    def next_arg_id(self) -> str:
        """Generate a unique argument ID."""
        aid = f"A{self._next_id:04d}"
        self._next_id += 1
        return aid

    # ── Grounded Semantics ──

    def compute_grounded(self) -> dict[str, Label]:
        """
        Compute grounded labeling via iterative propagation.

        Algorithm (Wu, Caminada & Gabbay 2009), over `defeat_map`:
        1. IN when every defeater is OUT (none at all included)
        2. OUT when some defeater is IN
        3. Repeat until fixpoint
        4. Everything unlabeled is UNDECIDED

        Complexity: O(|arguments| × |attacks|) — polynomial.
        """
        defeaters = self.defeat_map()
        labels: dict[str, Label] = {}
        changed = True
        while changed:
            changed = False
            for arg_id in self.arguments:
                if arg_id in labels:
                    continue
                ds = defeaters[arg_id]
                if all(labels.get(d) == Label.OUT for d in ds):
                    labels[arg_id] = Label.IN
                    changed = True
                elif any(labels.get(d) == Label.IN for d in ds):
                    labels[arg_id] = Label.OUT
                    changed = True
        labels = {aid: labels.get(aid, Label.UNDECIDED) for aid in self.arguments}
        self.labels = labels
        return labels

    def supers(self) -> dict[str, set[str]]:
        """Every argument that contains each one, itself included, through
        any depth of sub-arguments."""
        out = {aid: {aid} for aid in self.arguments}
        changed = True
        while changed:
            changed = False
            for a in self.arguments.values():
                for s in a.sub_arguments:
                    if s not in out:
                        continue           # a dangling id contains nothing
                    new = out[a.id] - out[s]
                    if new:
                        out[s] |= new
                        changed = True
        return out

    def reaching_attacks(self) -> list[tuple[Attack, str]]:
        """Each attack with every argument it reaches: its target and every
        argument built on the target (#287). In ASPIC+ an attack on a
        sub-argument is an attack on whatever contains it, so a conclusion
        cannot stand on a premise that has fallen."""
        supers = self.supers()
        return [(atk, b) for atk in self.attacks for b in sorted(supers[atk.target])]

    def defeat_map(self) -> dict[str, set[str]]:
        """Each argument's defeaters: the attackers whose attack reaches it
        and succeeds. Success is decided against the argument attacked, not
        the one built on it — a strict rule on top does not shield a
        defeasible premise underneath."""
        out: dict[str, set[str]] = {aid: set() for aid in self.arguments}
        for atk, reached in self.reaching_attacks():
            if self._defeats(self.arguments[atk.attacker],
                             self.arguments[atk.target], atk):
                out[reached].add(atk.attacker)
        return out

    def _defeats(
        self, attacker: Argument, target: Argument, attack: Attack
    ) -> bool:
        """
        Does the attack from attacker succeed as defeat?

        ASPIC+ defeat relation (Prakken 2010, Definition 3.12):
        - Undercutting: always succeeds (attacks the inference rule itself,
          not the conclusion — no preference comparison needed)
        - Rebutting: fails if target's top rule is strict (strict arguments
          cannot be rebutted); otherwise uses preference comparison
        - Undermining: uses preference comparison

        Preference uses pramāṇa-based ordering (Nyāya bādhita principle):
        - Higher pramāṇa always wins
        - Equal pramāṇa: attack succeeds if attacker is at least as strong
          (i.e., attacker is not strictly less preferred — standard ASPIC+)
        """
        # Undercutting attacks always succeed — they target the inference
        # rule itself, bypassing preference (Prakken 2010, Definition 3.7)
        if attack.attack_type == "undercutting":
            return True

        # Rebutting: cannot rebut an argument with a strict top rule
        if attack.attack_type == "rebutting" and target.is_strict:
            return False

        # Preference comparison for rebutting and undermining
        a_pramana = attacker.tag.pramana_type
        t_pramana = target.tag.pramana_type

        # Higher pramāṇa always wins (bādhita override)
        if t_pramana > a_pramana:
            return False  # Target survives — strictly more preferred
        if a_pramana > t_pramana:
            return True   # Attacker wins — strictly more preferred

        # Same pramāṇa — attack succeeds if attacker is at least as strong
        # (ASPIC+: defeat iff attacker is not strictly less preferred).
        # Strength is the argument's place in L, not a product of floats:
        # the comparison this needs is an ordering, and L is already one.
        return rank(attacker.status) >= rank(target.status)

    # ── Epistemic Status Derivation ──

    def supposed_under(self, arg_id: str) -> list[frozenset[str]]:
        """What the question supposed that one argument rests on, as
        alternatives: the argument holds given any one of the returned sets.

        A supposed premise rests on itself. An argument needs every
        sub-argument, so its alternatives are the unions across one choice
        from each. That holds with or without a rule: a defeat on any
        sub-argument reaches it (#287), so it cannot hold given only one.
        Anything else — a computed fact, a typed contestation — rests on no
        supposition. Redundant sets are left in; `given` drops them, once.
        """
        arg = self.arguments[arg_id]
        if arg_id in self.supposed:
            return [frozenset([arg.conclusion])]
        if not arg.sub_arguments:
            return [frozenset()]
        alts = [frozenset()]
        for part in (self.supposed_under(s) for s in arg.sub_arguments):
            alts = [a | b for a in alts for b in part]
        return sorted(set(alts), key=lambda s: (len(s), sorted(s)))

    def given(self, conclusion: str) -> list[frozenset[str]]:
        """What a conclusion's status holds only given (#195).

        A supposition is the condition a derivation holds under, not a link
        in it, so it does not lower what follows — and a status that rests on
        nothing but what the question supposed would read as a finding unless
        it says so. The status is the join over the IN arguments, so it holds
        unconditionally if one argument at that status rests on no
        supposition, and then this is empty. Otherwise one set per distinct
        set those arguments rest on, fewest first: the status holds given any
        one of them. A set containing another is dropped, since holding
        given {A} makes {A, B} redundant. Empty, too, when no argument is IN:
        a contested or open conclusion asserts nothing to be conditional.
        """
        status, _, _ = self.get_epistemic_status(conclusion)
        best = [
            a for a in self.arguments.values()
            if a.conclusion == conclusion
            and self.labels.get(a.id) == Label.IN and a.status == status
        ]
        sets = {alt for a in best for alt in self.supposed_under(a.id)}
        if not sets or frozenset() in sets:
            return []
        return sorted((s for s in sets if not any(t < s for t in sets)),
                      key=lambda s: (len(s), sorted(s)))

    def get_epistemic_status(
        self, conclusion: str
    ) -> tuple[Optional[EpistemicStatus], ProvenanceTag, list[Argument]]:
        """
        Derive epistemic status for a conclusion from the extension.

        The labelling decides the outcome and the lattice decides the
        grade — no thresholds anywhere:

            none                 → None (nothing concludes this)
            every argument OUT   → CONTESTED
            some UNDECIDED, none IN → OPEN
            otherwise            → ⋁ { σ(a) : label(a) = IN }

        The join is what makes accrual idempotent: restating support for a
        conclusion takes the maximum over the same value, which is that
        value. Nothing has to be discounted for it to hold.

        Returns (EpistemicStatus | None, combined ProvenanceTag, relevant arguments).
        """
        args_for = [
            a for a in self.arguments.values()
            if a.conclusion == conclusion
        ]

        if not args_for:
            return (None, ProvenanceTag.zero(), [])

        accepted = [
            a for a in args_for
            if self.labels.get(a.id) == Label.IN
        ]
        undecided = [
            a for a in args_for
            if self.labels.get(a.id) == Label.UNDECIDED
        ]

        if accepted:
            combined = accepted[0].tag
            for a in accepted[1:]:
                combined = ProvenanceTag.oplus(combined, a.tag)
            # Accrual over the surviving arguments: the best one carries it.
            status = join([a.status for a in accepted])
            return (status, combined, accepted)

        if undecided:
            combined = undecided[0].tag
            for a in undecided[1:]:
                combined = ProvenanceTag.oplus(combined, a.tag)
            return (EpistemicStatus.OPEN, combined, undecided)

        # All OUT — check if potentially reinstatable (approximate preferred)
        combined = args_for[0].tag
        for a in args_for[1:]:
            combined = ProvenanceTag.oplus(combined, a.tag)
        # All arguments OUT — conservatively mark CONTESTED.
        # Full preferred semantics (NP-hard) would be needed to distinguish
        # "defensibly reinstatable" from "definitively defeated".
        return (EpistemicStatus.CONTESTED, combined, args_for)

    # ── Preferred Semantics (Phase 4) ──

    def compute_preferred(self) -> Optional[list[dict[str, Label]]]:
        """
        Preferred extensions: the maximal admissible sets, over defeats.
        Exponential in the undecided arguments, so for offline jalpa only.

        Conflict and defence are both read from defeats, as the grounded
        labelling is, because that is the framework ASPIC+ builds: an attack
        that does not succeed is not a conflict. Read from attacks instead,
        the grounded extension itself can fail to be conflict-free (#153).

        Each extension is a labelling of every argument: IN if a member, OUT
        if a member defeats it, otherwise UNDECIDED.

        Returns None past MAX_UNDECIDED undecided arguments: not computed,
        which must not read as "these are all of them".
        """
        grounded = self.compute_grounded()
        undecided = sorted(
            aid for aid, lbl in grounded.items() if lbl == Label.UNDECIDED
        )
        if len(undecided) > MAX_UNDECIDED:
            return None
        base = frozenset(
            aid for aid, lbl in grounded.items() if lbl == Label.IN
        )
        defeaters = self.defeat_map()

        # Every preferred extension contains the grounded extension and
        # excludes what it labels OUT, so only the undecided are searched.
        # Largest first: a set found at a size is maximal unless it sits
        # inside one already found.
        found: list[frozenset[str]] = []
        for size in range(len(undecided), -1, -1):
            for combo in combinations(undecided, size):
                candidate = base | frozenset(combo)
                if any(candidate <= f for f in found):
                    continue
                if _admissible(candidate, defeaters):
                    found.append(candidate)

        return [
            {
                aid: Label.IN if aid in ext
                else Label.OUT if defeaters[aid] & ext
                else Label.UNDECIDED
                for aid in self.arguments
            }
            for ext in sorted(found, key=sorted)
        ]

    # ── Stable Semantics (Phase 4) ──

    def compute_stable(self) -> Optional[list[dict[str, Label]]]:
        """
        Stable extensions: conflict-free sets that defeat every argument
        outside them, over `defeat_map` as grounded and preferred are (#284).
        For offline vitaṇḍā audit only.

        Every stable extension is preferred, and a preferred extension is
        stable exactly when it leaves nothing UNDECIDED, so this reads them
        off `compute_preferred` and shares its search and its limit. An empty
        list means there is none (an odd cycle has none); None means past
        MAX_UNDECIDED it was not computed.
        """
        preferred = self.compute_preferred()
        if preferred is None:
            return None
        return [e for e in preferred if Label.UNDECIDED not in e.values()]

    # ── Contestation Support ──

    def add_counter_argument(
        self,
        conclusion: str,
        tag: ProvenanceTag,
        attack_target: str,
        attack_type: str,
        hetvabhasa: str,
        status: EpistemicStatus = EpistemicStatus.HYPOTHESIS,
    ) -> str:
        """Add a user-supplied counter-argument and its attack.

        `status` defaults to HYPOTHESIS rather than to the top of L: a
        contestation is a claim offered against the framework, and letting
        an assertion enter as ESTABLISHED would let it outrank curated
        knowledge by virtue of having been typed.

        Returns the new argument ID.
        """
        arg_id = self.next_arg_id()
        self.add_argument(Argument(
            id=arg_id,
            conclusion=conclusion,
            top_rule=None,
            # A user-supplied contestation. Its status is the explicit
            # default above, not a bound derived from any rule.
            status_bound_by=(BOUND_ASSERTED,),
            premises=frozenset([conclusion]),
            is_strict=False,
            tag=tag,
            status=status,
        ))
        self.add_attack(Attack(
            attacker=arg_id,
            target=attack_target,
            attack_type=attack_type,
            hetvabhasa=hetvabhasa,
        ))
        return arg_id

    # ── Proof Trace Rendering ──

    def get_argument_tree(self, arg_id: str, _visited: set = None) -> dict:
        """Return the full argument tree as a nested dict for rendering.

        Uses a visited set to detect and short-circuit cycles in
        sub-argument structures (guards against stack overflow).
        """
        if _visited is None:
            _visited = set()

        arg = self.arguments.get(arg_id)
        if not arg:
            return {}

        if arg_id in _visited:
            return {"id": arg_id, "cycle_detected": True}
        _visited.add(arg_id)

        tree = {
            "id": arg.id,
            "conclusion": arg.conclusion,
            "label": self.labels.get(arg.id, Label.UNDECIDED).value,
            "tag": arg.tag.to_dict(),
            "top_rule": arg.top_rule,
            "is_strict": arg.is_strict,
            "sub_arguments": [
                self.get_argument_tree(sa, _visited)
                for sa in arg.sub_arguments
            ],
            "attacks_received": [
                {
                    "attacker": atk.attacker,
                    "type": atk.attack_type,
                    "hetvabhasa": atk.hetvabhasa,
                    "attacker_label": self.labels.get(
                        atk.attacker, Label.UNDECIDED
                    ).value,
                }
                for atk in self._attacks_on.get(arg_id, [])
            ],
        }
        return tree

    def to_dict(self) -> dict:
        """Export entire AF as JSON-serializable dict for audit."""
        return {
            "arguments": {
                aid: {
                    "conclusion": a.conclusion,
                    "top_rule": a.top_rule,
                    "sub_arguments": list(a.sub_arguments),
                    "premises": sorted(a.premises),
                    "is_strict": a.is_strict,
                    "tag": a.tag.to_dict(),
                    "label": self.labels.get(aid, Label.UNDECIDED).value,
                }
                for aid, a in self.arguments.items()
            },
            "attacks": [
                {
                    "attacker": atk.attacker,
                    "target": atk.target,
                    "type": atk.attack_type,
                    "hetvabhasa": atk.hetvabhasa,
                }
                for atk in self.attacks
            ],
        }
