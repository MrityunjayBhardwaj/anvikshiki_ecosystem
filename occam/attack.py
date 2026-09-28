"""Stage 3 — typed attack edges proposed by the model, kept by majority (#140).

In the knowledge-base engine, attacks come from a contrariness table: a
hand-maintained antonym list over a predicate vocabulary. Occam has neither,
so the model proposes attacks — typed, with a stated reason — and the
mechanism decides which survive.

Why a model judgment belongs here
─────────────────────────────────
An attack edge is auditable. "A3 undercuts A7: the inference does not hold"
is something a person can check in seconds; a similarity score of 0.67 is
not. The three types are structurally distinct enough to classify.

What the mechanism enforces
───────────────────────────
- **Type fits target.** An undercut attacks an inference rule, so it may only
  target an inference or analogy step — never a quote, which has no rule.
  This matters because an undercut always defeats, whatever the preference:
  aimed at a quote, it would delete verified evidence by assertion. An
  undermining attack targets a premise, so only a quote. A rebut may target
  anything. A mismatched edge is dropped and counted.
- **Majority.** An edge (attacker, target, type) is kept only when strictly
  more than half the samples propose it. Missing an edge changes a verdict;
  inventing one changes it further. The threshold is a number on the result,
  not an implication of the code.
- **Dangling ids are a hard error.** A dangling edge silently changes an
  extension. `check_edges` raises with the unknown id; a sample that names
  one is rejected whole, recorded with that message.
- **Rationale is stored and never read.** It is for the auditor. If the
  solver ever read it, the solver would stop being deterministic in the
  words of a model.
"""

from __future__ import annotations

from typing import Iterable, Literal, Sequence

from pydantic import BaseModel, ConfigDict, model_validator

from .argue import Argument, ArgueResult
from .model import Model, extract_json

__all__ = [
    "Attack", "AttackResult", "ATTACK_TYPES", "FALLACY_OF_TYPE",
    "attack", "attack_from_replies", "attack_prompt", "check_edges",
    "majority_threshold",
]

AttackType = Literal["rebutting", "undercutting", "undermining"]
ATTACK_TYPES: tuple[str, ...] = ("rebutting", "undercutting", "undermining")

# The Nyāya reading of each attack, derived from the type rather than asked
# for: a rebut exhibits a contradiction (viruddha), an undercut shows the
# reason does not settle the conclusion (savyabhicāra), an undermine shows a
# premise is unestablished (asiddha).
FALLACY_OF_TYPE = {
    "rebutting": "viruddha",
    "undercutting": "savyabhicara",
    "undermining": "asiddha",
}

# Which kinds of argument each type may target.
_TARGETS = {
    "rebutting": {"quote", "inference", "analogy"},
    "undercutting": {"inference", "analogy"},
    "undermining": {"quote"},
}


def majority_threshold(k: int) -> int:
    """Strictly more than half of k samples."""
    return k // 2 + 1


class Attack(BaseModel):
    model_config = ConfigDict(frozen=True)

    attacker: str
    target: str
    type: AttackType
    fallacy: str
    rationale: str = ""
    sample_ids: tuple[int, ...] = ()

    @model_validator(mode="after")
    def _check(self) -> "Attack":
        if self.fallacy != FALLACY_OF_TYPE[self.type]:
            raise ValueError(f"fallacy {self.fallacy!r} does not follow from {self.type}")
        if self.attacker == self.target:
            raise ValueError(f"{self.attacker} attacks itself")
        return self

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.attacker, self.target, self.type)


def check_edges(attacks: Iterable[Attack], argument_ids: Iterable[str]) -> None:
    """Raise if any edge names an argument that does not exist."""
    known = set(argument_ids)
    for a in attacks:
        for end in (a.attacker, a.target):
            if end not in known:
                raise ValueError(
                    f"attack {a.attacker} -> {a.target} ({a.type}) names unknown "
                    f"argument {end!r}. A dangling edge silently changes the "
                    f"extension, so it is refused rather than skipped."
                )


class AttackResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    k: int
    threshold: int
    attacks: tuple[Attack, ...]                  # kept: proposed by >= threshold samples
    minority: tuple[Attack, ...]                 # proposed, but by too few
    self_attacks: int
    type_mismatch: tuple[tuple[int, str], ...]   # (sample, description)
    malformed: tuple[tuple[int, str], ...]       # (sample, reason) — whole sample rejected


def attack_prompt(question: str, arguments: Sequence[Argument]) -> str:
    lines = [
        "Below are arguments about a question. Identify which arguments ATTACK "
        "which others. Return JSON only:\n\n"
        '{"attacks": [{"attacker": "A0001", "target": "A0003", '
        '"type": "rebutting", "rationale": "<one sentence>"}]}\n\n'
        "Types:\n"
        "- rebutting: the attacker's conclusion contradicts the target's conclusion.\n"
        "- undercutting: the attacker shows the target's inference does not hold "
        "(its premises do not support its conclusion). Only targets inference or "
        "analogy steps.\n"
        "- undermining: the attacker shows a quoted premise is false or does not "
        "apply. Only targets quote steps.\n\n"
        "Only list real conflicts. Arguments that agree, or that are about "
        "different things, do not attack each other. Return {\"attacks\": []} if "
        "there are none. Use only the ids below.\n",
        f"QUESTION: {question}\n",
    ]
    for a in arguments:
        if a.kind == "quote":
            lines.append(f"{a.id} [quote]: {a.conclusion}\n    quoted: \"{a.span.quote}\"")
        else:
            lines.append(f"{a.id} [{a.kind} from {', '.join(a.sub_arguments)}]: {a.conclusion}")
    return "\n".join(lines)


def attack(model: Model, question: str, argued: ArgueResult, *, k: int = 3,
           temperature: float = 0.2) -> tuple[list[str], AttackResult]:
    """Ask k times at low temperature; return raw replies and the kept edges."""
    if not argued.arguments:
        return [], attack_from_replies([], argued.arguments)
    prompt = attack_prompt(question, argued.arguments)
    replies = [model.complete(prompt, temperature=temperature) for _ in range(k)]
    return replies, attack_from_replies(replies, argued.arguments)


def attack_from_replies(replies: Sequence[str],
                        arguments: Sequence[Argument]) -> AttackResult:
    """Deterministic: the same replies and arguments give the same edges."""
    kinds = {a.id: a.kind for a in arguments}
    k = len(replies)
    threshold = majority_threshold(k)
    proposals: dict[tuple, dict] = {}
    self_attacks = 0
    mismatch: list[tuple[int, str]] = []
    malformed: list[tuple[int, str]] = []

    for sid, reply in enumerate(replies):
        obj = extract_json(reply)
        if not isinstance(obj, dict) or not isinstance(obj.get("attacks"), list):
            malformed.append((sid, "reply is not a JSON object with an attacks list"))
            continue
        edges: list[Attack] = []
        bad = ""
        for raw in obj["attacks"]:
            if not isinstance(raw, dict):
                bad = f"attack entry is not an object: {str(raw)[:60]}"
                break
            att, tgt, typ = raw.get("attacker"), raw.get("target"), raw.get("type")
            if typ not in ATTACK_TYPES or not isinstance(att, str) or not isinstance(tgt, str):
                bad = f"attack entry has no valid attacker/target/type: {str(raw)[:80]}"
                break
            if att == tgt:
                self_attacks += 1
                continue
            rationale = raw.get("rationale") if isinstance(raw.get("rationale"), str) else ""
            edges.append(Attack(attacker=att, target=tgt, type=typ,
                                fallacy=FALLACY_OF_TYPE[typ], rationale=rationale))
        if not bad:
            try:
                check_edges(edges, kinds)
            except ValueError as e:
                bad = str(e)
        if bad:
            malformed.append((sid, bad))
            continue
        seen: set[tuple] = set()
        for e in edges:
            if kinds[e.target] not in _TARGETS[e.type]:
                mismatch.append((sid, f"{e.attacker} {e.type} {e.target} "
                                      f"(a {kinds[e.target]})"))
                continue
            if e.key in seen:
                continue
            seen.add(e.key)
            slot = proposals.setdefault(e.key, {"edge": e, "samples": []})
            slot["samples"].append(sid)

    kept: list[Attack] = []
    minority: list[Attack] = []
    for key in sorted(proposals):
        slot = proposals[key]
        edge = slot["edge"].model_copy(update={"sample_ids": tuple(slot["samples"])})
        (kept if len(slot["samples"]) >= threshold else minority).append(edge)
    return AttackResult(k=k, threshold=threshold, attacks=tuple(kept),
                        minority=tuple(minority), self_attacks=self_attacks,
                        type_mismatch=tuple(mismatch), malformed=tuple(malformed))
