# anvikshiki_v4/tests/test_origin_ceiling.py
"""Augmentation containment: a generated rule cannot launder itself upward.

The guarantee, stated over the lattice rather than over a number:

    if every argument for a conclusion passes through at least one rule
    whose origin caps it at PROVISIONAL, then the conclusion is at most
    PROVISIONAL — and if some argument reaches it without passing through
    such a rule, the bound correctly lifts.

The second half is the reason this is a ceiling and not a blanket
demotion. A bound that also demoted independently-derived conclusions would
be blunt where this one is tight.

Every knowledge base in `anvikshiki_v4/data/` is hand-authored, so
`augmentation_metadata` is None on every rule in the tree and the ceiling is
a no-op against all of them. A suite that only compiled those fixtures would
report this law green without once reaching the branch it is about — which is
how the previous accrual defect stayed invisible. The fixtures here are built
with origins set explicitly.
"""

import pytest

from anvikshiki_v4.argumentation import ArgumentationFramework
from anvikshiki_v4.lattice import (
    ceiling_for_origin,
    rank,
    status_of_rule,
)
from anvikshiki_v4.schema import (
    AugmentationMetadata,
    AugmentationOrigin,
    CausalStatus,
    Confidence,
    DomainType,
    EpistemicStatus as KBEpistemicStatus,
    KnowledgeStore,
    Vyapti,
)
from anvikshiki_v4.schema_v4 import EpistemicStatus
from anvikshiki_v4.t2_compiler_v4 import compile_t2


def _vyapti(
    vid: str,
    antecedents: list[str],
    consequent: str,
    origin: AugmentationOrigin | None = None,
    status: KBEpistemicStatus = KBEpistemicStatus.ESTABLISHED,
) -> Vyapti:
    """A rule with an explicit origin.

    Confidence is 1.0 deliberately: the point of the ceiling is that it binds
    regardless of how confident the generator claimed to be, and a fixture
    with a modest confidence would leave that untested.
    """
    metadata = None
    if origin is not None:
        metadata = AugmentationMetadata(origin=origin)
    return Vyapti(
        id=vid,
        name=vid,
        statement=f"{' and '.join(antecedents)} implies {consequent}",
        causal_status=CausalStatus.EMPIRICAL,
        confidence=Confidence(
            existence=1.0, formulation=1.0, evidence="theoretical"
        ),
        epistemic_status=status,
        antecedents=antecedents,
        consequent=consequent,
        augmentation_metadata=metadata,
    )


def _store(*vyaptis: Vyapti) -> KnowledgeStore:
    return KnowledgeStore(
        domain_type=DomainType.CRAFT,
        vyaptis={v.id: v for v in vyaptis},
    )


def _status_of(ks: KnowledgeStore, predicate: str) -> EpistemicStatus:
    """Compile from one asserted premise and read a conclusion's status."""
    af = compile_t2(ks, [{"predicate": "p", "confidence": 1.0,
                          "sources": ["q1"]}])
    af.compute_grounded()
    status, _, _ = af.get_epistemic_status(predicate)
    return status


# ── The ceiling itself ───────────────────────────────────────

def test_every_origin_has_an_explicit_ceiling():
    """No origin may fall through to a default.

    An unmapped origin is an unvalidated rule with no bound, and a default
    would admit the next origin someone adds at whatever the default was.
    """
    for origin in AugmentationOrigin:
        assert ceiling_for_origin(origin) in EpistemicStatus


def test_an_unknown_origin_is_refused_rather_than_defaulted():
    with pytest.raises(ValueError, match="no ceiling in the lattice"):
        ceiling_for_origin("origin_nobody_mapped")


def test_absent_metadata_is_the_curated_case():
    """`augmentation_metadata` is None on every rule in a hand-authored KB.

    Absence has to mean curated rather than unknown, or the ceiling would
    demote every base knowledge base in the tree.
    """
    assert ceiling_for_origin(None) is EpistemicStatus.ESTABLISHED
    curated = _vyapti("V01", ["p"], "q")
    assert curated.augmentation_metadata is None
    assert status_of_rule(curated) is EpistemicStatus.ESTABLISHED


def test_generated_origins_are_capped_below_established():
    """The three origins nothing human authored cannot reach the top of L."""
    for origin in (
        AugmentationOrigin.GUIDE_EXTRACTED,
        AugmentationOrigin.WEB_SOURCED,
        AugmentationOrigin.LLM_PARAMETRIC,
    ):
        rule = _vyapti("V01", ["p"], "q", origin=origin)
        assert rank(status_of_rule(rule)) < rank(EpistemicStatus.ESTABLISHED)


def test_the_ceiling_lowers_but_never_lifts():
    """A ceiling, not an assignment.

    A curated rule the knowledge base records as GENUINELY_OPEN stays OPEN.
    If the ceiling assigned rather than capped, authoring a rule as open
    would silently promote it.
    """
    violations = []
    for origin in list(AugmentationOrigin) + [None]:
        for kb_status in KBEpistemicStatus:
            rule = _vyapti("V01", ["p"], "q", origin=origin, status=kb_status)
            effective = status_of_rule(rule)
            ceiling = ceiling_for_origin(origin)
            authored = rank(
                status_of_rule(_vyapti("V01", ["p"], "q", status=kb_status))
            )
            if rank(effective) > min(rank(ceiling), authored):
                violations.append(
                    f"{origin} + {kb_status.value} → {effective.name}, "
                    f"above the meet of its ceiling and its authored status"
                )
    assert not violations, "\n".join(violations)


def test_provisional_is_reachable_from_the_knowledge_base():
    """The status it was added for.

    PROVISIONAL was in the derived enum and unreachable: premises enter at
    the top of L and rules mapped from four KB statuses, none of them
    PROVISIONAL. Its branches in synthesis and uncertainty were dead code.
    """
    rule = _vyapti(
        "V01", ["p"], "q", origin=AugmentationOrigin.LLM_PARAMETRIC
    )
    assert status_of_rule(rule) is EpistemicStatus.PROVISIONAL


# ── The containment guarantee, through the compiler ──────────

def test_a_conclusion_reached_only_through_generated_rules_is_contained():
    """Theorem 4. The single-path case: p → q through an LLM-proposed rule.

    The rule is authored ESTABLISHED with confidence 1.0 and the premise is
    asserted, so nothing but the ceiling stands between this conclusion and
    the top of the lattice.
    """
    ks = _store(_vyapti(
        "V01", ["p"], "q", origin=AugmentationOrigin.LLM_PARAMETRIC
    ))
    assert _status_of(ks, "q") is EpistemicStatus.PROVISIONAL


def test_the_bound_survives_accrual_over_many_generated_paths():
    """Repeating an unvalidated claim through several paths does not lift it.

    This is the half a probabilistic cap loses. Two derivations capped at
    0.75 combine by noisy-or to 0.94, so repetition launders the claim; a
    maximum over a set bounded by PROVISIONAL is still bounded by
    PROVISIONAL, for any number of paths.
    """
    ks = _store(
        _vyapti("V01", ["p"], "q",
                origin=AugmentationOrigin.LLM_PARAMETRIC),
        _vyapti("V02", ["p"], "q",
                origin=AugmentationOrigin.WEB_SOURCED),
        _vyapti("V03", ["p"], "q",
                origin=AugmentationOrigin.LLM_PARAMETRIC),
    )
    af = compile_t2(ks, [{"predicate": "p", "confidence": 1.0,
                          "sources": ["q1"]}])
    af.compute_grounded()
    status, _, args = af.get_epistemic_status("q")
    assert len(args) >= 3, "the fixture stopped exercising accrual"
    assert status is EpistemicStatus.PROVISIONAL


def test_the_bound_holds_along_a_chain_through_a_generated_rule():
    """One generated link caps everything downstream of it.

    p → q by a curated rule, q → r by a generated one. The weakest link is
    the generated rule, so r is contained even though its own rule and its
    premise are both established.
    """
    ks = _store(
        _vyapti("V01", ["p"], "q"),
        _vyapti("V02", ["q"], "r",
                origin=AugmentationOrigin.LLM_PARAMETRIC),
    )
    assert _status_of(ks, "q") is EpistemicStatus.ESTABLISHED
    assert _status_of(ks, "r") is EpistemicStatus.PROVISIONAL


def test_an_independent_curated_derivation_lifts_the_bound():
    """The corollary, and the reason this is tight rather than blunt.

    If *some* surviving argument reaches the conclusion without passing
    through a generated rule, the join exceeds the ceiling — correctly,
    because an independent curated derivation exists.
    """
    ks = _store(
        _vyapti("V01", ["p"], "q",
                origin=AugmentationOrigin.LLM_PARAMETRIC),
        _vyapti("V02", ["p"], "q"),
    )
    assert _status_of(ks, "q") is EpistemicStatus.ESTABLISHED


def test_the_containment_law_over_every_generated_origin():
    """Quantified, with its denominator, rather than one worked example."""
    capped = [
        origin for origin in AugmentationOrigin
        if rank(ceiling_for_origin(origin)) < rank(EpistemicStatus.ESTABLISHED)
    ]
    assert capped, "no origin is capped — the law would pass vacuously"

    violations = []
    for origin in capped:
        ks = _store(_vyapti("V01", ["p"], "q", origin=origin))
        reached = _status_of(ks, "q")
        ceiling = ceiling_for_origin(origin)
        if rank(reached) > rank(ceiling):
            violations.append(
                f"{origin.value}: conclusion reached {reached.name}, "
                f"above its ceiling {ceiling.name}"
            )
    assert not violations, (
        f"{len(violations)} of {len(capped)} capped origins violate "
        f"containment:\n" + "\n".join(f"  - {v}" for v in violations)
    )


def test_a_curated_knowledge_base_is_unaffected():
    """The ceiling must be a no-op on hand-authored rules.

    Every KB in the tree is curated, so if the ceiling touched them it would
    silently demote the whole engine.
    """
    ks = _store(_vyapti("V01", ["p"], "q"), _vyapti("V02", ["q"], "r"))
    assert _status_of(ks, "q") is EpistemicStatus.ESTABLISHED
    assert _status_of(ks, "r") is EpistemicStatus.ESTABLISHED


def test_the_generated_rule_is_still_reasoned_with():
    """Contained, not excluded.

    A capped rule still fires, still derives its conclusion and still enters
    the framework. The ceiling bounds how strongly the conclusion may be
    reported, and dropping the rule instead would lose a derivation the
    engine is supposed to expose.
    """
    ks = _store(_vyapti(
        "V01", ["p"], "q", origin=AugmentationOrigin.LLM_PARAMETRIC
    ))
    af = compile_t2(ks, [{"predicate": "p", "confidence": 1.0,
                          "sources": ["q1"]}])
    assert isinstance(af, ArgumentationFramework)
    derived = [a for a in af.arguments.values() if a.top_rule == "V01"]
    assert derived, "the capped rule stopped producing an argument at all"
    assert derived[0].conclusion == "q"
