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
from typing import Optional
from .schema_v4 import (
    Argument, Attack, Label, ProvenanceTag, EpistemicStatus
)


@dataclass
class ArgumentationFramework:
    """
    The instantiated argumentation framework.
    Computed from KB at compile time. Evaluated at query time.
    """
    arguments: dict[str, Argument] = field(default_factory=dict)
    attacks: list[Attack] = field(default_factory=list)
    labels: dict[str, Label] = field(default_factory=dict)

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

        Algorithm (Wu, Caminada & Gabbay 2009):
        1. Label all unattacked arguments IN
        2. Label attacked-by-IN arguments OUT (if defeat succeeds)
        3. Label arguments with all-attackers-OUT as IN
        4. Repeat until fixpoint
        5. Everything unlabeled is UNDECIDED

        Complexity: O(|arguments| × |attacks|) — polynomial.
        """
        labels = {}
        remaining = set(self.arguments.keys())

        changed = True
        while changed:
            changed = False

            for arg_id in list(remaining):
                # Filter to only defeating attackers (ASPIC+ preference)
                defeating_attackers = []
                for atk in self._attacks_on.get(arg_id, []):
                    attacker_arg = self.arguments[atk.attacker]
                    target_arg = self.arguments[arg_id]
                    if self._defeats(attacker_arg, target_arg, atk):
                        defeating_attackers.append(atk.attacker)

                # No defeating attackers → IN (effectively unattacked)
                if not defeating_attackers:
                    labels[arg_id] = Label.IN
                    remaining.discard(arg_id)
                    changed = True
                    continue

                # All defeating attackers OUT → IN (defended)
                if all(labels.get(a) == Label.OUT
                       for a in defeating_attackers):
                    labels[arg_id] = Label.IN
                    remaining.discard(arg_id)
                    changed = True
                    continue

                # Any defeating attacker IN → OUT
                if any(labels.get(a) == Label.IN
                       for a in defeating_attackers):
                    labels[arg_id] = Label.OUT
                    remaining.discard(arg_id)
                    changed = True

        # Everything remaining is UNDECIDED
        for arg_id in remaining:
            labels[arg_id] = Label.UNDECIDED

        self.labels = labels
        return labels

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
        # (ASPIC+: defeat iff attacker is not strictly less preferred)
        return attacker.tag.strength >= target.tag.strength

    # ── Epistemic Status Derivation ──

    def get_epistemic_status(
        self, conclusion: str
    ) -> tuple[Optional[EpistemicStatus], ProvenanceTag, list[Argument]]:
        """
        Derive epistemic status for a conclusion from the extension.
        Returns (EpistemicStatus | None, combined ProvenanceTag, relevant arguments).
        """
        args_for = [
            a for a in self.arguments.values()
            if a.conclusion == conclusion
        ]

        if not args_for:
            return (None, ProvenanceTag.zero(), [])

        # Combine tags of accepted arguments via ⊕
        accepted = [
            a for a in args_for
            if self.labels.get(a.id) == Label.IN
        ]

        if not accepted:
            undecided = [
                a for a in args_for
                if self.labels.get(a.id) == Label.UNDECIDED
            ]
            if undecided:
                combined = undecided[0].tag
                for a in undecided[1:]:
                    combined = ProvenanceTag.oplus(combined, a.tag)
                return (combined.epistemic_status(), combined, undecided)
            else:
                # All OUT — contested
                combined = args_for[0].tag
                for a in args_for[1:]:
                    combined = ProvenanceTag.oplus(combined, a.tag)
                return (EpistemicStatus.CONTESTED, combined, args_for)

        combined = accepted[0].tag
        for a in accepted[1:]:
            combined = ProvenanceTag.oplus(combined, a.tag)

        return (combined.epistemic_status(), combined, accepted)

    # ── Preferred Semantics (Phase 4) ──

    def compute_preferred(
        self, timeout_seconds: float = 30.0
    ) -> list[dict[str, Label]]:
        """
        Compute preferred extensions (maximally admissible sets).
        NP-hard — for offline jalpa analysis only.

        Falls back to grounded extension if timeout exceeded.
        """
        import time
        start = time.time()

        grounded = self.compute_grounded()
        grounded_in = {
            aid for aid, lbl in grounded.items() if lbl == Label.IN
        }

        # Start from grounded extension and try to extend
        extensions = []
        self._enumerate_preferred(
            grounded_in, set(), extensions, start, timeout_seconds
        )

        if not extensions:
            # Timeout or no additional extensions — return grounded
            return [grounded]

        # Convert sets to label dicts
        results = []
        for ext in extensions:
            labeling = {}
            for aid in self.arguments:
                if aid in ext:
                    labeling[aid] = Label.IN
                elif any(
                    a in ext for a in self._attackers_of.get(aid, [])
                ):
                    labeling[aid] = Label.OUT
                else:
                    labeling[aid] = Label.UNDECIDED
            results.append(labeling)

        return results

    def _enumerate_preferred(
        self, current: set, tried: set,
        results: list, start: float, timeout: float
    ):
        """Backtracking search for maximal admissible supersets."""
        import time
        if time.time() - start > timeout:
            return

        # Check if current is admissible
        if not self._is_admissible(current):
            return

        # Try extending with each UNDECIDED argument
        extended = False
        for aid in self.arguments:
            if aid in current or aid in tried:
                continue
            if time.time() - start > timeout:
                break
            candidate = current | {aid}
            if self._is_admissible(candidate):
                self._enumerate_preferred(
                    candidate, tried | {aid}, results, start, timeout
                )
                extended = True
            tried.add(aid)

        if not extended:
            # Current is maximal admissible
            if current not in [set(r) for r in results]:
                results.append(current.copy())

    def _is_admissible(self, s: set) -> bool:
        """Check if set s is conflict-free and defends all its members."""
        # Conflict-free: no two arguments in s attack each other
        for aid in s:
            for attacker_id in self._attackers_of.get(aid, []):
                if attacker_id in s:
                    return False

        # Defends all members: for every defeating attacker of s-member,
        # some s-member counter-defeats it
        for aid in s:
            for atk in self._attacks_on.get(aid, []):
                attacker = self.arguments[atk.attacker]
                target = self.arguments[aid]
                if not self._defeats(attacker, target, atk):
                    continue  # Attack doesn't succeed as defeat
                # Need some s-member to defeat the attacker
                defended = False
                for defender_id in s:
                    for def_atk in self._attacks_on.get(atk.attacker, []):
                        if def_atk.attacker == defender_id:
                            defender = self.arguments[defender_id]
                            if self._defeats(defender, attacker, def_atk):
                                defended = True
                                break
                    if defended:
                        break
                if not defended:
                    return False
        return True

    # ── Stable Semantics (Phase 4) ──

    def compute_stable(
        self, timeout_seconds: float = 60.0
    ) -> list[dict[str, Label]]:
        """
        Compute stable extensions (conflict-free sets attacking everything outside).
        coNP-hard — for formal vitaṇḍā audit only.

        Returns list of labelings. May be empty if no stable extension exists.
        """
        import time
        start = time.time()

        results = []
        self._enumerate_stable(
            set(), 0, list(self.arguments.keys()),
            results, start, timeout_seconds
        )
        return results

    def _enumerate_stable(
        self, current: set, idx: int, all_args: list,
        results: list, start: float, timeout: float
    ):
        """Enumerate-and-check with pruning for stable extensions."""
        import time
        if time.time() - start > timeout:
            return

        if idx == len(all_args):
            # Check if current is stable: conflict-free + attacks everything outside
            if not self._is_conflict_free(current):
                return
            for aid in all_args:
                if aid in current:
                    continue
                # aid must be attacked by some member of current
                attacked = any(
                    a in current
                    for a in self._attackers_of.get(aid, [])
                )
                if not attacked:
                    return
            labeling = {}
            for aid in all_args:
                labeling[aid] = Label.IN if aid in current else Label.OUT
            results.append(labeling)
            return

        aid = all_args[idx]
        # Try including aid
        self._enumerate_stable(
            current | {aid}, idx + 1, all_args,
            results, start, timeout
        )
        # Try excluding aid
        self._enumerate_stable(
            current, idx + 1, all_args,
            results, start, timeout
        )

    def _is_conflict_free(self, s: set) -> bool:
        """No two arguments in s attack each other."""
        for aid in s:
            for attacker_id in self._attackers_of.get(aid, []):
                if attacker_id in s:
                    return False
        return True

    # ── Contestation Support ──

    def add_counter_argument(
        self,
        conclusion: str,
        tag: ProvenanceTag,
        attack_target: str,
        attack_type: str,
        hetvabhasa: str,
    ) -> str:
        """Add a user-supplied counter-argument and its attack.

        Returns the new argument ID.
        """
        arg_id = self.next_arg_id()
        self.add_argument(Argument(
            id=arg_id,
            conclusion=conclusion,
            top_rule=None,
            premises=frozenset([conclusion]),
            is_strict=False,
            tag=tag,
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
