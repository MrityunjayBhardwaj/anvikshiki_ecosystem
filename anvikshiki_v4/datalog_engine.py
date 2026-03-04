"""
Semi-naive Datalog engine for the Ānvīkṣikī knowledge base.

Supports two modes:
  Phase 2 — boolean_mode=True:  facts are derived or not (classical Datalog)
  Phase 3+ — boolean_mode=False: facts carry Heyting-valued epistemic qualification

Properties:
  TERMINATES:  guaranteed (finite predicate/entity space, monotone lattice)
  COMPLEXITY:  O(|rules| × |Δfacts|) per iteration (semi-naive)
  TOTAL:       O(|rules| × |facts|) — polynomial
  CORRECT:     computes minimal model (least fixpoint)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable, Optional


# ─── Heyting Lattice ─────────────────────────────────────────


class EpistemicValue(IntEnum):
    """
    Five-element Heyting algebra of truth values.

    Ordering: BOTTOM < CONTESTED < OPEN < HYPOTHESIS < ESTABLISHED

    Operations:
      meet(a, b) = min(a, b)  — weakest link in a chain
      join(a, b) = max(a, b)  — best evidence across derivation paths
    """

    BOTTOM = 0       # No evidence / false
    CONTESTED = 1    # ⚡ Actively contested
    OPEN = 2         # ? Genuinely open
    HYPOTHESIS = 3   # ~ Working hypothesis
    ESTABLISHED = 4  # ✓ Established

    @staticmethod
    def meet(a: EpistemicValue, b: EpistemicValue) -> EpistemicValue:
        """AND: minimum (weakest link in the inference chain)."""
        return EpistemicValue(min(a.value, b.value))

    @staticmethod
    def join(a: EpistemicValue, b: EpistemicValue) -> EpistemicValue:
        """OR: maximum (best available evidence)."""
        return EpistemicValue(max(a.value, b.value))


# ─── Facts and Rules ─────────────────────────────────────────


@dataclass(frozen=True)
class Fact:
    """A ground fact in the knowledge base."""

    predicate: str
    entity: str
    value: EpistemicValue = EpistemicValue.ESTABLISHED

    def __str__(self) -> str:
        return f"{self.predicate}({self.entity}) = {self.value.name}"


@dataclass
class Rule:
    """
    A Datalog rule (compiled from a vyāpti).

    Semantics:
      head(Entity) :- body_pos_1(Entity), body_pos_2(Entity), ...,
                      not body_neg_1(Entity), ...

    In lattice mode, the consequent value is:
      meet(confidence, meet(antecedent_values...))
    """

    vyapti_id: str
    name: str
    head: str                    # Consequent predicate name
    body_positive: list[str]     # Required antecedent predicates
    body_negative: list[str]     # Scope exclusions (negated predicates)
    confidence: EpistemicValue   # Rule's own epistemic status

    def __str__(self) -> str:
        pos = ", ".join(f"{p}(E)" for p in self.body_positive)
        neg = ", ".join(f"not {p}(E)" for p in self.body_negative)
        body = ", ".join(filter(None, [pos, neg]))
        return f"% {self.vyapti_id}: {self.name}\n{self.head}(E) :- {body}."


@dataclass
class Violation:
    """A hetvābhāsa (integrity constraint) violation."""

    hetvabhasa_id: str
    name: str
    description: str
    triggered_by: list[str]
    correction: str


# ─── The Engine ──────────────────────────────────────────────


class DatalogEngine:
    """
    Semi-naive Datalog evaluator with lattice-valued facts.

    Semi-naive optimization: each iteration only fires rules where at least
    one body predicate was NEWLY DERIVED in the previous iteration (Δfacts).
    This avoids re-deriving known facts every iteration.
    """

    def __init__(self, boolean_mode: bool = True):
        self.boolean_mode = boolean_mode
        self.facts: dict[tuple[str, str], EpistemicValue] = {}
        self.rules: list[Rule] = []
        self.hetvabhasa_checks: list[dict] = []
        self.trace: list[str] = []
        self._delta: dict[tuple[str, str], EpistemicValue] = {}

    # ─── Loading ─────────────────────────────────────────

    def add_fact(self, fact: Fact) -> None:
        """Add or update a fact. Join (max) with existing value."""
        key = (fact.predicate, fact.entity)
        if key not in self.facts:
            # New fact — store it and add to delta (even if BOTTOM)
            self.facts[key] = fact.value
            if fact.value > EpistemicValue.BOTTOM:
                self._delta[key] = fact.value
        else:
            old = self.facts[key]
            new = EpistemicValue.join(old, fact.value)
            if new > old:
                self.facts[key] = new
                self._delta[key] = new

    def add_rule(self, rule: Rule) -> None:
        """Add a rule (compiled vyāpti) to the rule base."""
        self.rules.append(rule)

    def add_hetvabhasa_check(
        self,
        hid: str,
        name: str,
        check_fn: Callable[[dict], list[str]],
        correction: str,
    ) -> None:
        """
        Add a hetvābhāsa integrity constraint.

        check_fn: (facts_dict) → list of triggering fact descriptions.
                  Returns non-empty list if violation detected.
        """
        self.hetvabhasa_checks.append({
            "id": hid,
            "name": name,
            "check_fn": check_fn,
            "correction": correction,
        })

    # ─── Semi-Naive Evaluation ───────────────────────────

    def evaluate(self) -> int:
        """
        Semi-naive fixpoint evaluation.

        Returns the number of iterations to reach fixpoint.

        Algorithm:
          1. Start with Δ = initial facts
          2. For each rule, check if any body predicate has a fact in Δ
          3. If rule fires and produces a NEW (or upgraded) fact, add to next Δ
          4. Repeat until Δ is empty (fixpoint reached)
        """
        iteration = 0

        while self._delta:
            new_delta: dict[tuple[str, str], EpistemicValue] = {}

            for rule in self.rules:
                # Find entities that have ANY body predicate in delta
                delta_entities: set[str] = set()
                for pred in rule.body_positive:
                    for (p, e) in self._delta:
                        if p == pred:
                            delta_entities.add(e)

                # For each candidate entity, try to fire the rule
                for entity in delta_entities:
                    result = self._try_fire(rule, entity)
                    if result is not None:
                        key = (rule.head, entity)
                        old = self.facts.get(key, EpistemicValue.BOTTOM)
                        if result > old:
                            self.facts[key] = result
                            new_delta[key] = result
                            self.trace.append(
                                f"Iter {iteration}: {rule.vyapti_id} → "
                                f"{rule.head}({entity}) = {result.name}"
                            )

            self._delta = new_delta
            iteration += 1

            # Safety bound — should never trigger for valid Datalog
            max_possible = len(self.rules) * (len(self.facts) + 1) + 1
            if iteration > max_possible:
                raise RuntimeError(
                    f"Fixpoint not reached after {iteration} iterations — "
                    f"possible bug in rule definitions"
                )

        return iteration

    def _try_fire(
        self, rule: Rule, entity: str
    ) -> Optional[EpistemicValue]:
        """
        Try to fire a rule for a specific entity.

        Returns the consequent's epistemic value if rule fires,
        None if antecedents are not satisfied.
        """
        # All positive body predicates must be present
        antecedent_values: list[EpistemicValue] = []
        for pred in rule.body_positive:
            key = (pred, entity)
            if key not in self.facts:
                return None  # Missing antecedent
            antecedent_values.append(self.facts[key])

        # No negative body predicate may be present (scope exclusions)
        for pred in rule.body_negative:
            key = (pred, entity)
            if key in self.facts and self.facts[key] > EpistemicValue.BOTTOM:
                return None  # Scope exclusion fires

        # Compute consequent value
        if self.boolean_mode:
            return EpistemicValue.ESTABLISHED
        else:
            # Meet of rule confidence and all antecedent values
            result = rule.confidence
            for av in antecedent_values:
                result = EpistemicValue.meet(result, av)
            return result

    # ─── Querying ────────────────────────────────────────

    def query(
        self,
        predicate: str,
        entity: Optional[str] = None,
        min_value: EpistemicValue = EpistemicValue.BOTTOM,
    ) -> list[tuple[str, EpistemicValue]]:
        """
        Query derived facts.

        Returns list of (entity, epistemic_value) pairs,
        sorted by value descending.
        """
        results = []
        for (p, e), v in self.facts.items():
            if p == predicate and v > min_value:
                if entity is None or e == entity:
                    results.append((e, v))
        return sorted(results, key=lambda x: x[1], reverse=True)

    def explain(self, predicate: str, entity: str) -> list[str]:
        """Return the derivation trace for a specific fact."""
        target = f"{predicate}({entity})"
        return [step for step in self.trace if target in step]

    def validate_predicates(self, predicates: list[str]) -> list[str]:
        """
        Validate predicate strings against the known vocabulary.
        Used by Layer 5 of the grounding defense.

        Returns list of error messages (empty = all valid).
        """
        errors: list[str] = []
        known_preds: set[str] = set()
        for rule in self.rules:
            known_preds.add(rule.head)
            known_preds.update(rule.body_positive)
            known_preds.update(rule.body_negative)

        # Also include predicates from existing facts
        for (p, _e) in self.facts:
            known_preds.add(p)

        for pred_str in predicates:
            if "(" not in pred_str or ")" not in pred_str:
                errors.append(
                    f"Malformed: '{pred_str}' — expected format: predicate(entity)"
                )
                continue

            name = pred_str.split("(")[0].strip()
            if name.startswith("not_"):
                name = name[4:]

            if name not in known_preds:
                hint = sorted(known_preds)[:10]
                errors.append(
                    f"Unknown predicate: '{name}' — valid: {hint}"
                )

        return errors

    # ─── Integrity Constraints ───────────────────────────

    def check_hetvabhasas(self) -> list[Violation]:
        """
        Run all hetvābhāsa checks against current derived facts.
        Returns list of violations.
        """
        violations: list[Violation] = []
        for check in self.hetvabhasa_checks:
            triggers = check["check_fn"](self.facts)
            if triggers:
                violations.append(
                    Violation(
                        hetvabhasa_id=check["id"],
                        name=check["name"],
                        description=f"{check['name']} detected in current derivation",
                        triggered_by=triggers,
                        correction=check["correction"],
                    )
                )
        return violations

    # ─── Serialization ───────────────────────────────────

    def to_datalog_text(self) -> str:
        """Export the full knowledge base as Datalog text."""
        lines = [
            "% Ānvīkṣikī Knowledge Base",
            f"% Mode: {'Boolean' if self.boolean_mode else 'Lattice'}",
            f"% Rules: {len(self.rules)}, Facts: {len(self.facts)}",
            "",
            "% ─── Rules (Vyāptis) ───",
        ]

        for rule in self.rules:
            lines.append(str(rule))
            lines.append("")

        lines.append("% ─── Facts ───")
        for (pred, entity), value in sorted(self.facts.items()):
            if self.boolean_mode:
                lines.append(f"{pred}({entity}).")
            else:
                lines.append(f"{pred}({entity}).  % {value.name}")

        return "\n".join(lines)

    def reset(self) -> None:
        """Clear all facts and traces, keeping rules and constraints."""
        self.facts.clear()
        self.trace.clear()
        self._delta.clear()
