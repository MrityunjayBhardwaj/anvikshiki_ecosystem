# tests/test_uncertainty.py
from anvikshiki_v4.uncertainty import compute_uncertainty_v4
from anvikshiki_v4.schema_v4 import ProvenanceTag, EpistemicStatus


def test_strong_tag():
    tag = ProvenanceTag(belief=0.9, disbelief=0.05, uncertainty=0.05,
                        trust_score=0.9, decay_factor=0.95, derivation_depth=1)
    result = compute_uncertainty_v4(tag, 0.9, "p", EpistemicStatus.ESTABLISHED)
    assert result["epistemic"]["belief"] == 0.9
    assert result["total_confidence"] > 0.7


def test_high_disbelief():
    tag = ProvenanceTag(belief=0.4, disbelief=0.5, uncertainty=0.1,
                        trust_score=0.8, decay_factor=0.9, derivation_depth=1)
    result = compute_uncertainty_v4(tag, 0.8, "p", EpistemicStatus.CONTESTED)
    assert "disagreement" in result["aleatoric"]["explanation"]


def test_low_decay():
    tag = ProvenanceTag(belief=0.7, disbelief=0.1, uncertainty=0.2,
                        trust_score=0.8, decay_factor=0.2, derivation_depth=1)
    result = compute_uncertainty_v4(tag, 0.8, "p", EpistemicStatus.HYPOTHESIS)
    assert result["inference"]["decay_factor"] == 0.2


def test_deep_derivation():
    tag = ProvenanceTag(belief=0.5, disbelief=0.2, uncertainty=0.3,
                        trust_score=0.7, decay_factor=0.8, derivation_depth=5)
    result = compute_uncertainty_v4(tag, 0.7, "p", EpistemicStatus.HYPOTHESIS)
    assert result["inference"]["derivation_depth"] == 5


def test_low_grounding():
    tag = ProvenanceTag(belief=0.7, disbelief=0.1, uncertainty=0.2,
                        trust_score=0.8, decay_factor=0.9, derivation_depth=1)
    result = compute_uncertainty_v4(tag, 0.3, "p", EpistemicStatus.HYPOTHESIS)
    assert result["inference"]["grounding_confidence"] == 0.3
