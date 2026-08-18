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

from enum import Enum
from typing import TYPE_CHECKING

from .schema import AugmentationOrigin
from .schema import EpistemicStatus as KBEpistemicStatus
from .schema_v4 import EpistemicStatus
from .span_verification import is_discriminating

if TYPE_CHECKING:
    from .schema import Provenance, Vyapti

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


class CitationTier(str, Enum):
    """How well a rule's citation has been checked.

    Not a quality judgement about the claim — a statement about what we have
    verified regarding where it came from. A true claim badly cited and a
    false claim well cited both exist, and this axis only sees the citation.
    """

    ATTRIBUTED = "attributed"
    EXISTS = "exists"
    UNRESOLVED = "unresolved"
    FABRICATED = "fabricated"
    # Hand-authored: this rule makes no located-span claim, so the axis does
    # not apply to it. A separate value rather than reusing ATTRIBUTED,
    # because the tier is shown to a reader — calling a curated rule
    # "attributed" would assert a verification that never happened, in order
    # to obtain a ceiling that is correct for an entirely different reason.
    CURATED = "curated"


# The highest status a rule may reach, given how well its citation checks out.
#
# Same discipline as `_ORIGIN_CEILING`: every tier mapped explicitly, an
# unmapped one raises. These are ceilings, so a rule already weaker stays
# weaker — the tier never promotes anything.
_CITATION_CEILING = {
    # The locator points somewhere we can reach and the claim's span was
    # found in it. This is the only tier that has checked the words.
    CitationTier.ATTRIBUTED: EpistemicStatus.ESTABLISHED,
    # A source we can reach, with nothing checked inside it. The document is
    # real; whether it says this is unknown.
    CitationTier.EXISTS: EpistemicStatus.HYPOTHESIS,
    # A citation that is a bare string, or a locator nothing can currently
    # resolve. Both mean the same thing operationally — we cannot get to the
    # source — and neither is evidence against the rule.
    CitationTier.UNRESOLVED: EpistemicStatus.PROVISIONAL,
    # We looked at the source and the words were not there. The bottom of L
    # rather than a drop: CONTESTED is the positive claim that something was
    # argued and defeated, which is exactly what a checked-and-missing span
    # establishes. Dropping is a separate decision a caller makes; see
    # `should_drop_for_citation`.
    CitationTier.FABRICATED: EpistemicStatus.CONTESTED,
    # No cap. The rule cites literature rather than a span, so this axis has
    # nothing to say about it and must not lower it — the origin ceiling is
    # what governs a curated rule.
    CitationTier.CURATED: EpistemicStatus.ESTABLISHED,
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


def ceiling_for_origin(
    origin: AugmentationOrigin | None,
) -> EpistemicStatus:
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


def _record_is_reachable(record: "Provenance") -> bool | None:
    """Whether this record's source can be reached. Three states.

    True  — there is a locator and something can resolve it.
    False — there is a locator and it demonstrably does not resolve.
    None  — **we have no resolver**, so the question was never asked.

    The third state is the whole reason this is not a bool. Identifier
    resolution is not built yet, so today the honest answer for every record
    carrying a locator is None: not "the source is unreachable", but "nobody
    looked". Collapsing None into False would read our own missing machinery
    as evidence against every source in the knowledge base — and because the
    unreachable tier is the one that justifies dropping a rule, that
    collapse would delete the entire KB on the strength of a component we
    have not written yet.

    So None maps to UNRESOLVED, never FABRICATED, and this function returns
    None until a resolver exists to return anything else.
    """
    # Unconditional today, and written as one line so it does not read as a
    # resolver that happens to be failing. Two branches both returning None
    # would look like logic and be none: the honest statement is that this
    # question cannot be asked yet, for any record. When identifier
    # resolution lands it answers here, and only here.
    return None


def tier_for_citation(vyapti: "Vyapti") -> CitationTier:
    """How well this rule's citation has been checked.

    Read off the provenance records, taking the **best** record: a rule with
    one verified span and one bare string is better cited than a rule with
    only the bare string, and the ceiling should reflect its strongest
    support rather than its weakest. That is the opposite discipline to
    `meet` further up, and deliberately so — chaining through a weak step
    genuinely weakens a conclusion, while citing an extra weak source
    alongside a strong one does not weaken the strong one.

    **A hand-authored rule is exempt, and this is the load-bearing case.**
    `Vyapti.provenance` is empty on curated rules *by design* — the schema
    says so where the field is defined: they cite literature rather than a
    located span, and `augmentation_metadata` is what tells the two apart.
    Tiering that absence UNRESOLVED would read a deliberate design decision
    as an unverified citation and cap the entire shipped knowledge base at
    PROVISIONAL — on the strength of an identifier resolver that does not
    exist yet. Two tests already existed to catch precisely that demotion.

    So the citation axis only bounds rules that were *supposed* to carry a
    record: extracted ones, whose citations are machine-produced and
    therefore both checkable and fakeable. Absent metadata means curated,
    exactly as `ceiling_for_origin` reads it.

    An extracted rule with no records is still UNRESOLVED, not FABRICATED.
    Never checked is not the same as checked and found wanting.
    """
    if vyapti.augmentation_metadata is None:
        return CitationTier.CURATED

    if not vyapti.provenance:
        return CitationTier.UNRESOLVED

    tiers = [_tier_for_record(record) for record in vyapti.provenance]
    # Best record wins, by ceiling strength.
    return max(tiers, key=lambda t: rank(_CITATION_CEILING[t]))


def _tier_for_record(record: "Provenance") -> CitationTier:
    """One provenance record's tier."""
    checked = record.quote_found_in_source

    # Checked, and the words were genuinely not there. The only fabrication
    # evidence this system actually has — and note it comes from the span
    # check at capture time, not from identifier resolution. #19 defines
    # FABRICATED as "identifier does not resolve", which is unreachable while
    # no resolver exists; wiring it that way would have made every rule
    # fabricated.
    #
    # Read from the verdict, never from the bool alone. A quote that matches
    # once markdown emphasis is stripped is not verbatim, so the bool is
    # False — the same False an invented sentence produces. Deciding deletion
    # on that collapse deleted the central claim of the first real chapter
    # traced, for a pair of asterisks the model did not reproduce.
    if checked is False:
        if record.quote_verdict == "absent":
            return CitationTier.FABRICATED
        if record.quote_verdict == "markup":
            # The words are identical; only markdown emphasis differs. That
            # is source *formatting*, on the same footing as the line
            # wrapping already normalised away — the model quoted prose out
            # of a marked-up document and did not reproduce the asterisks.
            # Treated as found, so it can reach ATTRIBUTED below.
            checked = True
        else:
            # Everything else that failed the strict check: a punctuation
            # substitution is a changed character in the content rather than
            # formatting around it, and no run has yet produced one to reason
            # from. An old record carries no verdict at all. Neither is
            # evidence against the source, and neither is evidence for it.
            return CitationTier.UNRESOLVED

    reachable = _record_is_reachable(record)
    if reachable is False:
        return CitationTier.UNRESOLVED

    # Checked and found — but a span too short to discriminate proves nothing
    # about whether the source says this, so it does not earn the tier that
    # means "we read the words there".
    if checked is True and is_discriminating(record.quote):
        return CitationTier.ATTRIBUTED

    # A locator we could reach but nothing checked inside it. Only claimable
    # once resolution exists; until then `reachable` is None and this falls
    # through to UNRESOLVED, which is the honest answer.
    if reachable is True:
        return CitationTier.EXISTS

    return CitationTier.UNRESOLVED


def ceiling_for_citation(vyapti: "Vyapti") -> EpistemicStatus:
    """The highest status this rule may reach, given its citation tier."""
    tier = tier_for_citation(vyapti)
    try:
        return _CITATION_CEILING[tier]
    except KeyError:
        raise ValueError(
            f"citation tier {tier!r} has no ceiling in the lattice. Add one "
            f"explicitly rather than letting it default: a tier with no "
            f"ceiling is an unchecked citation with no bound. Known tiers "
            f"are {sorted(t.value for t in _CITATION_CEILING)}"
        ) from None


def should_drop_for_citation(vyapti: "Vyapti") -> bool:
    """Whether this rule's citation is bad enough to remove it entirely.

    Kept apart from the ceiling on purpose. A ceiling is total — it returns a
    status for every rule — and a function that could instead delete its
    argument is not. Making the drop a separate, explicit decision also means
    a caller has to opt into deletion rather than receiving it as a side
    effect of asking what a rule's status is.

    True only for FABRICATED: a span that was checked against its source and
    was not there. Never for a rule nobody has checked.
    """
    return tier_for_citation(vyapti) is CitationTier.FABRICATED


def status_of_rule(vyapti: "Vyapti") -> EpistemicStatus:
    """A rule's effective status: authored, capped by origin and by citation.

    ⋀( from_kb(status), ceiling_for_origin(origin), ceiling_for_citation() )

    This is the bound that makes the guarantee hold on the *output* rather
    than on an input. The numeric confidence cap it replaces constrained one
    factor of a product that was then thresholded, so a conclusion derived
    entirely through generated rules could still come out ESTABLISHED if the
    arithmetic landed above the cutoff — and two capped derivations combining
    by noisy-or reached 0.94. A cap on an input to a non-monotone pipeline is
    not a guarantee on its output; a meet in a lattice is.

    The citation ceiling joins on the same terms — a third bound inside one
    meet rather than a second pass, because the guarantee wanted is "the
    weakest of everything we know about this rule", and adding a bound must
    not depend on a caller remembering to apply it.

    Note what this does to a hand-authored knowledge base: its rules cite
    bare strings, so they tier UNRESOLVED and cap at PROVISIONAL however they
    were authored. That is the intended reading — status becomes computed
    from what has been verified rather than asserted, and rises on its own as
    sources are checked.
    """
    origin = None
    if vyapti.augmentation_metadata is not None:
        origin = vyapti.augmentation_metadata.origin
    return meet([
        from_kb(vyapti.epistemic_status),
        ceiling_for_origin(origin),
        ceiling_for_citation(vyapti),
    ])
