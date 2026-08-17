# anvikshiki_v4/uncertainty.py
"""Three-way uncertainty decomposition from an argument's status and tag.

The three components answer different questions and fail for different
reasons, so they are reported separately and never merged:

    epistemic  — how strongly the argumentation supports the conclusion.
                 The status computed from the labelling over the lattice.
    aleatoric  — whether the domain itself disagrees. Structural: a
                 conclusion is contested when its supporting arguments were
                 defeated, which is a fact about the attack graph.
    inference  — how the conclusion was reached: how confident the grounder
                 was, how fresh the evidence is, how deep the derivation ran.

There is deliberately no composite score. The previous `total_confidence`
was `belief × trust × decay`, a product of three quantities measuring
different things, and the weights that made it one number were asserted
rather than derived. A caller that wants to trade these off should see the
components and do it explicitly.

The calibrated replacement for the epistemic component is a conformal
prediction set with a coverage guarantee (#23), which needs labelled
calibration data that does not exist yet. Until it does, the honest output
is a lattice element, not a number.
"""

from .schema_v4 import EpistemicStatus, ProvenanceTag

_EPISTEMIC_EXPLANATION = {
    EpistemicStatus.ESTABLISHED:
        "every argument reaching it survives, and none passed through a "
        "weaker link than an established one",
    # These name the weakest link without claiming where its status came
    # from. A rule reaches a status either because it was authored that way
    # or because its origin caps it there — `lattice.status_of_rule` takes
    # the meet — and an explanation asserting the knowledge base recorded it
    # would be wrong for every generated rule.
    EpistemicStatus.HYPOTHESIS:
        "supported, but the derivation passes through a rule no stronger "
        "than a working hypothesis",
    EpistemicStatus.PROVISIONAL:
        "supported only through rules that are provisional — proposed, and "
        "not validated",
    EpistemicStatus.OPEN:
        "the argumentation neither accepts nor defeats it — attackers and "
        "defenders are mutually undecided",
    EpistemicStatus.CONTESTED:
        "every argument for it is defeated by an argument that survives",
}


def compute_uncertainty_v4(
    tag: ProvenanceTag,
    grounding_confidence: float,
    conclusion: str,
    epistemic_status: EpistemicStatus,
) -> dict:
    """Decompose uncertainty into three independently reported components."""
    status_name = (
        epistemic_status.value if epistemic_status else "none"
    )
    contested = epistemic_status == EpistemicStatus.CONTESTED
    undecided = epistemic_status == EpistemicStatus.OPEN

    return {
        "conclusion": conclusion,
        "epistemic": {
            "status": status_name,
            "explanation": (
                f"'{conclusion}': {_EPISTEMIC_EXPLANATION[epistemic_status]}"
                if epistemic_status
                else f"'{conclusion}': no argument concludes this"
            ),
        },
        "aleatoric": {
            "contested": contested,
            "undecided": undecided,
            "explanation": (
                f"'{conclusion}': the domain disagrees — surviving arguments "
                "defeat every argument for this conclusion"
                if contested
                else f"'{conclusion}': attack and defence are unresolved "
                "against each other"
                if undecided
                else f"'{conclusion}': no surviving argument contradicts it"
            ),
        },
        "inference": {
            "grounding_confidence": grounding_confidence,
            "decay_factor": tag.decay_factor,
            "derivation_depth": tag.derivation_depth,
            "explanation": (
                f"'{conclusion}': grounding={grounding_confidence:.2f}, "
                f"freshness={tag.decay_factor:.2f}, "
                f"chain_depth={tag.derivation_depth}"
            ),
        },
    }
