"""Advisories — engine-side findings that are not defeats.

An advisory says something about a rule that participated in an answer
without saying that the answer is wrong. A stale rule still fires. A rule
whose declared scope was never established still fires. Neither is an attack,
so neither belongs in `violations`, and until this module existed neither
belonged anywhere: the scope and decay checks ran on every query and their
output was discarded one frame later.

Two producers, one shape:

  * `GroundingPipeline._check_scope` / `._check_decay` — what the grounding
    boundary noticed about the predicates it produced.
  * `unestablished_scope_advisories` — what the argumentation framework
    noticed about the rules that actually fired.

The second cannot live with the first. `_check_scope` sees a list of
predicates and no framework, so it can say "the query asserts an exclusion"
but not "a rule fired anyway" — the question needs the compiled framework,
which exists only in the engine. Splitting them by what each can observe is
why this is a module and not a method.

The `message` is the load-bearing field, not a rendering of the others. It is
what a reader acts on and what the trace has always printed; `kind`,
`vyapti_id` and `subject` exist so a caller can filter and group without
parsing it back.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .predicate_contrariness import predicate_entity, predicate_name
from .schema import KnowledgeStore
from .schema_v4 import Label


class AdvisoryKind(str, Enum):
    """What the engine noticed.

    Not a severity. All three are advisory by decision: they report a
    condition on a rule that fired, and none of them suppresses the firing.
    """

    SCOPE_EXCLUSION = "scope_exclusion"
    DECAY = "decay"
    UNESTABLISHED_SCOPE = "unestablished_scope"


class Advisory(BaseModel):
    """One finding about one rule."""

    kind: AdvisoryKind
    vyapti_id: str
    message: str
    subject: Optional[str] = Field(
        default=None,
        description=(
            "The predicate the advisory is about, bound to the entity it was "
            "observed of where there is one. `None` is a binding in its own "
            "right — a bare predicate — and not a missing value."
        ),
    )


def scope_exclusion_advisory(vyapti_id: str, subject: str) -> Advisory:
    """The query asserts something a rule declares itself excluded by."""
    return Advisory(
        kind=AdvisoryKind.SCOPE_EXCLUSION,
        vyapti_id=vyapti_id,
        subject=subject,
        message=f"SCOPE: {vyapti_id} excludes '{subject}', which the query asserts",
    )


def decay_advisory(vyapti_id: str, message: str) -> Advisory:
    """A rule whose last verification is old enough to matter, or absent."""
    return Advisory(
        kind=AdvisoryKind.DECAY,
        vyapti_id=vyapti_id,
        subject=None,
        message=message,
    )


def unestablished_scope_advisories(
    knowledge_store: KnowledgeStore,
    af,
    labels: dict,
) -> list[Advisory]:
    """Rules that fired with a declared scope condition never established.

    `scope_conditions` is authored on every rule in both shipped bases,
    extracted, evaluated, printed into the grounder's prompt — and read by
    nothing that decides anything. A rule fires whether or not its declared
    scope holds. This does not change that: the rule still fires, and the
    conclusion is still returned. It says so.

    **Established means present in the framework**, as an asserted premise or
    as something a rule derived. Both are arguments, so both are read off
    `af.arguments` — one source rather than two, which matters because a
    scope condition *could* in principle be derivable even though none in
    either shipped base is (0 of 5 in business, 0 of 4 in copywriting: no
    condition is any rule's consequent, and none is any rule's antecedent).
    Every one of them has to arrive as a grounded fact from the query, which
    is what makes the advisory worth having rather than a formality.

    **Only rules labelled IN.** A defeated rule argument has already been
    answered by the framework, and reporting its scope as well would put a
    second finding on a conclusion the engine is not making. Same test
    `derivation_state` applies for the same reason.

    **A bare condition establishes for any entity; a bound one only for its
    own.** The shipped bases write rules in bare names while facts arrive
    bound, so a query asserting `heterogeneous_quality_market` with no entity
    is read as a statement about the world the rule reasons in. The strict
    reading would advise on every rule in every query written that way, and an
    advisory nobody can act on is noise in the channel this cluster exists to
    open. It is a deliberate leniency, and it is safe *here* precisely because
    nothing is gated on the result — if firing is ever gated on scope, this
    is the line to revisit first.
    """
    established: set[tuple[str, Optional[str]]] = {
        (predicate_name(a.conclusion), predicate_entity(a.conclusion))
        for a in af.arguments.values()
        if not a.conclusion.startswith("_")
    }
    established_bare = {name for name, entity in established if entity is None}

    seen: set[tuple[str, str, Optional[str]]] = set()
    advisories: list[Advisory] = []

    for aid, arg in af.arguments.items():
        if arg.top_rule is None or labels.get(aid) != Label.IN:
            continue
        vyapti = knowledge_store.vyaptis.get(arg.top_rule)
        if vyapti is None:
            continue

        entity = predicate_entity(arg.conclusion)
        for condition in vyapti.scope_conditions:
            if condition in established_bare or (condition, entity) in established:
                continue
            key = (arg.top_rule, condition, entity)
            if key in seen:
                continue
            seen.add(key)

            subject = condition if entity is None else f"{condition}({entity})"
            advisories.append(Advisory(
                kind=AdvisoryKind.UNESTABLISHED_SCOPE,
                vyapti_id=arg.top_rule,
                subject=subject,
                message=(
                    f"SCOPE UNESTABLISHED: {arg.top_rule} declares scope "
                    f"'{subject}', which the query never establishes. The rule "
                    f"fired anyway and concluded '{arg.conclusion}'."
                ),
            ))

    return sorted(advisories, key=lambda a: (a.vyapti_id, a.subject or ""))


def as_wire(advisories: list[Advisory]) -> list[dict]:
    """The form that goes out on a `dspy.Prediction`, beside `violations`.

    Dicts rather than models, because `violations` next to it is a list of
    dicts and one output field should not need two unpacking rules.
    """
    return [a.model_dump(mode="json") for a in advisories]
