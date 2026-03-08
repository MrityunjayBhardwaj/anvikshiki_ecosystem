# anvikshiki_v4/uncertainty.py
"""Three-way uncertainty decomposition from provenance tags."""

from .schema_v4 import ProvenanceTag, EpistemicStatus


def compute_uncertainty_v4(
    tag: ProvenanceTag,
    grounding_confidence: float,
    conclusion: str,
    epistemic_status: EpistemicStatus,
) -> dict:
    """
    Decompose uncertainty into three independent components.
    All values derived from ProvenanceTag — no hand-tuned dictionaries.
    Epistemic status is passed in (computed by argumentation layer).
    """
    return {
        "conclusion": conclusion,
        "epistemic": {
            "status": epistemic_status.value if epistemic_status else "none",
            "belief": tag.belief,
            "uncertainty": tag.uncertainty,
            "explanation": (
                f"'{conclusion}': high belief with low uncertainty "
                "— well-established"
                if tag.belief > 0.8 and tag.uncertainty <= 0.1
                else f"'{conclusion}': moderate evidence "
                "— working hypothesis"
                if tag.belief > 0.5
                else f"'{conclusion}': insufficient evidence"
            ),
        },
        "aleatoric": {
            "disbelief": tag.disbelief,
            "explanation": (
                f"'{conclusion}': high disbelief indicates inherent "
                "domain disagreement"
                if tag.disbelief > 0.3
                else f"'{conclusion}': low domain-level contestation"
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
        "total_confidence": tag.strength,
    }
