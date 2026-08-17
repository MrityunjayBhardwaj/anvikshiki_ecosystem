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

Both are idempotent, which is the whole point: restating the same evidence
composes to itself, along a chain and across accrual alike, for every element
of L and any number of restatements. That is a one-line consequence of
`min(s, s) = s` rather than something a parameter has to be tuned to achieve.

The laws this is built to satisfy are stated in
`anvikshiki_v4/tests/test_algebra_laws.py`.
"""

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

# The knowledge base's four statuses into L. PROVISIONAL has no counterpart
# there yet — it is what #13 adds, to bound rules by their origin.
_FROM_KB = {
    KBEpistemicStatus.ESTABLISHED: EpistemicStatus.ESTABLISHED,
    KBEpistemicStatus.WORKING_HYPOTHESIS: EpistemicStatus.HYPOTHESIS,
    KBEpistemicStatus.GENUINELY_OPEN: EpistemicStatus.OPEN,
    KBEpistemicStatus.ACTIVELY_CONTESTED: EpistemicStatus.CONTESTED,
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
