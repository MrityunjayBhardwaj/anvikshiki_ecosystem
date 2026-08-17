# tests/test_uncertainty.py
"""The three uncertainty components, reported separately.

`total_confidence` is gone — it multiplied belief, trust and decay under
weights nobody derived, and two of those three no longer exist. The
epistemic component is a lattice element rather than a belief read through a
cutoff; the aleatoric one is structural, taken from whether the
argumentation defeated every argument for the conclusion.
"""

from anvikshiki_v4.uncertainty import compute_uncertainty_v4
from anvikshiki_v4.schema_v4 import EpistemicStatus, ProvenanceTag


def _tag(**kw):
    base = dict(trust_score=0.9, decay_factor=0.95, derivation_depth=1)
    base.update(kw)
    return ProvenanceTag(**base)


def test_status_is_reported_without_a_threshold():
    result = compute_uncertainty_v4(
        _tag(), 0.9, "p", EpistemicStatus.ESTABLISHED)
    assert result["epistemic"]["status"] == "established"
    assert "p" in result["epistemic"]["explanation"]


def test_every_status_has_an_explanation():
    """A status with no explanation would render as a bare word in the UI."""
    for status in EpistemicStatus:
        result = compute_uncertainty_v4(_tag(), 0.9, "p", status)
        assert result["epistemic"]["status"] == status.value
        assert result["epistemic"]["explanation"].strip()


def test_contested_is_read_from_the_status_not_a_disbelief_mass():
    result = compute_uncertainty_v4(
        _tag(), 0.8, "p", EpistemicStatus.CONTESTED)
    assert result["aleatoric"]["contested"] is True
    assert result["aleatoric"]["undecided"] is False
    assert "disagrees" in result["aleatoric"]["explanation"]


def test_open_is_distinct_from_contested():
    """Unresolved and defeated are different findings and must not merge."""
    result = compute_uncertainty_v4(_tag(), 0.8, "p", EpistemicStatus.OPEN)
    assert result["aleatoric"]["contested"] is False
    assert result["aleatoric"]["undecided"] is True


def test_uncontested_says_so():
    result = compute_uncertainty_v4(
        _tag(), 0.8, "p", EpistemicStatus.ESTABLISHED)
    assert result["aleatoric"]["contested"] is False
    assert result["aleatoric"]["undecided"] is False


def test_low_decay():
    result = compute_uncertainty_v4(
        _tag(decay_factor=0.2), 0.8, "p", EpistemicStatus.HYPOTHESIS)
    assert result["inference"]["decay_factor"] == 0.2


def test_deep_derivation():
    result = compute_uncertainty_v4(
        _tag(derivation_depth=5), 0.7, "p", EpistemicStatus.HYPOTHESIS)
    assert result["inference"]["derivation_depth"] == 5


def test_low_grounding():
    result = compute_uncertainty_v4(
        _tag(), 0.3, "p", EpistemicStatus.HYPOTHESIS)
    assert result["inference"]["grounding_confidence"] == 0.3


def test_no_composite_is_reported():
    """The components are not multiplied back into one number."""
    result = compute_uncertainty_v4(
        _tag(), 0.9, "p", EpistemicStatus.ESTABLISHED)
    assert "total_confidence" not in result
