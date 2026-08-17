# anvikshiki_v4/lattice.py
"""The epistemic status lattice L, and the two operations that compose it.

L is totally ordered, weakest first:

    CONTESTED < OPEN < PROVISIONAL < HYPOTHESIS < ESTABLISHED

Two operations, and the discipline is the same one the provenance metadata
already follows:

    meet (∧) = min — chaining. Reasoning through a step cannot produce a
        conclusion stronger than the weakest link it passed through.
    join (∨) = max — accrual. A conclusion is as strong as the best argument
        that survives for it.

A rule enters L through `status_of_rule`, which meets what the rule was
authored as with the ceiling its origin allows. The meet is what carries the
containment guarantee downstream: if every argument for a conclusion passes
through a generated rule, the join over those arguments cannot exceed that
rule's ceiling, and if one independent curated derivation exists the join
correctly rises above it.

Both are idempotent, which is the whole point: restating the same evidence
composes to itself, along a chain and across accrual alike, for every element
of L and any number of restatements. That is a one-line consequence of
`min(s, s) = s` rather than something a parameter has to be tuned to achieve.

The laws this is built to satisfy are stated in
`anvikshiki_v4/tests/test_algebra_laws.py`.
"""

from .schema import AugmentationOrigin
from .schema import EpistemicStatus as KBEpistemicStatus
from .schema_v4 import EpistemicStatus

# Weakest first. Index in this tuple is the element's rank in L.
STATUS_ORDER: tuple[EpistemicStatus, ...] = (
    EpistemicStatus.CONTESTED,
    EpistemicStatus.OPEN,
    EpistemicStatus.PROVISIONAL,
    EpistemicStatus.HYPOTHESIS,
    EpistemicStatus.ESTABLISHED,
)

_RANK = {status: index for index, status in enumerate(STATUS_ORDER)}

# The knowledge base's statuses into L.
_FROM_KB = {
    KBEpistemicStatus.ESTABLISHED: EpistemicStatus.ESTABLISHED,
    KBEpistemicStatus.WORKING_HYPOTHESIS: EpistemicStatus.HYPOTHESIS,
    KBEpistemicStatus.PROVISIONAL: EpistemicStatus.PROVISIONAL,
    KBEpistemicStatus.GENUINELY_OPEN: EpistemicStatus.OPEN,
    KBEpistemicStatus.ACTIVELY_CONTESTED: EpistemicStatus.CONTESTED,
}

# The highest status a rule may reach, given how it was produced.
#
# A ceiling, not an assignment: a curated rule the knowledge base records as
# GENUINELY_OPEN stays OPEN. The ceiling only ever lowers, which is what
# makes the bound survive accrual — a maximum over a set bounded by
# PROVISIONAL is still bounded by PROVISIONAL.
#
# Every origin is mapped explicitly and an unmapped one raises. A default
# here would silently admit the next origin someone adds at whatever the
# default happened to be, and the whole point of the ceiling is that a
# model proposing rules cannot promote its own proposals.
_ORIGIN_CEILING = {
    # Hand-authored in the base KB, with sources. No cap; the authored
    # status decides.
    AugmentationOrigin.CURATED: EpistemicStatus.ESTABLISHED,
    # Extracted from guide prose by T2b. A human wrote the prose but not the
    # rule, and extraction is the one stage in this engine whose accuracy is
    # still unmeasured.
    AugmentationOrigin.GUIDE_EXTRACTED: EpistemicStatus.HYPOTHESIS,
    # Promoted out of the shadow KB by a reviewer. A human approved it, so it
    # outranks anything merely proposed — but approving a rule is not the
    # same act as authoring one into the base KB with sources.
    AugmentationOrigin.HITL_PROMOTED: EpistemicStatus.HYPOTHESIS,
    # Retrieved evidence, unverified against the source document.
    AugmentationOrigin.WEB_SOURCED: EpistemicStatus.PROVISIONAL,
    # The model's own parametric knowledge, with nothing behind it.
    AugmentationOrigin.LLM_PARAMETRIC: EpistemicStatus.PROVISIONAL,
}


def rank(status: EpistemicStatus) -> int:
    """Position in L, weakest = 0."""
    return _RANK[status]


def meet(statuses) -> EpistemicStatus:
    """Weakest link — the status of a chain of reasoning.

    Raises on an empty argument rather than returning the lattice top. A meet
    over nothing is conventionally the top element, and that convention would
    hand ESTABLISHED to a derivation that composed no evidence at all — an
    absence scoring as the strongest possible result. Callers that can
    legitimately have nothing to compose should say so themselves.
    """
    statuses = list(statuses)
    if not statuses:
        raise ValueError(
            "meet over no statuses: a chain that composed nothing has no "
            "weakest link, and defaulting to the lattice top would score an "
            "absence of evidence as ESTABLISHED"
        )
    return min(statuses, key=rank)


def join(statuses) -> EpistemicStatus:
    """Best supporting argument — the status of accrued support.

    Raises on empty for the same reason `meet` does, in the other direction:
    a join over nothing is the lattice bottom, and CONTESTED is a positive
    claim that a conclusion was argued and defeated. "Nothing concluded this"
    is a different state and belongs to the caller.
    """
    statuses = list(statuses)
    if not statuses:
        raise ValueError(
            "join over no statuses: nothing was accrued, which is not the "
            "same finding as a conclusion having been argued and defeated"
        )
    return max(statuses, key=rank)


def from_kb(status: KBEpistemicStatus) -> EpistemicStatus:
    """A knowledge-base status, as an element of L."""
    try:
        return _FROM_KB[status]
    except KeyError:
        raise ValueError(
            f"knowledge-base status {status!r} has no place in the lattice; "
            f"known statuses are {sorted(s.value for s in _FROM_KB)}"
        ) from None


def ceiling_for_origin(origin) -> EpistemicStatus:
    """The highest status a rule of this origin may reach.

    `None` means curated: `Vyapti.augmentation_metadata` is optional and
    absent on every rule in a hand-authored base KB, so absence is the
    curated case rather than an unknown one.
    """
    if origin is None:
        return _ORIGIN_CEILING[AugmentationOrigin.CURATED]
    try:
        return _ORIGIN_CEILING[origin]
    except KeyError:
        raise ValueError(
            f"augmentation origin {origin!r} has no ceiling in the lattice. "
            f"Add one explicitly rather than letting it default: an origin "
            f"with no ceiling is an unvalidated rule with no bound. Known "
            f"origins are {sorted(o.value for o in _ORIGIN_CEILING)}"
        ) from None


def status_of_rule(vyapti) -> EpistemicStatus:
    """A rule's effective status: what it was authored as, capped by origin.

    ⋀( from_kb(vyapti.epistemic_status), ceiling_for_origin(origin) )

    This is the bound that makes the guarantee hold on the *output* rather
    than on an input. The numeric confidence cap it replaces constrained one
    factor of a product that was then thresholded, so a conclusion derived
    entirely through generated rules could still come out ESTABLISHED if the
    arithmetic landed above the cutoff — and two capped derivations combining
    by noisy-or reached 0.94. A cap on an input to a non-monotone pipeline is
    not a guarantee on its output; a meet in a lattice is.
    """
    origin = None
    if vyapti.augmentation_metadata is not None:
        origin = vyapti.augmentation_metadata.origin
    return meet([from_kb(vyapti.epistemic_status), ceiling_for_origin(origin)])
