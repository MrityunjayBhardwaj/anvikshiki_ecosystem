# tests/test_schema_v4.py
import pytest
import math
from anvikshiki_v4.schema_v4 import (
    ProvenanceTag, PramanaType, EpistemicStatus, Argument, Attack, Label
)


# ── Semiring Law Tests ──

def test_tensor_associativity():
    a = ProvenanceTag(belief=0.8, disbelief=0.1, uncertainty=0.1,
                      trust_score=0.9, decay_factor=0.95, derivation_depth=1)
    b = ProvenanceTag(belief=0.7, disbelief=0.2, uncertainty=0.1,
                      trust_score=0.85, decay_factor=0.9, derivation_depth=1)
    c = ProvenanceTag(belief=0.9, disbelief=0.05, uncertainty=0.05,
                      trust_score=0.95, decay_factor=0.92, derivation_depth=1)
    ab_c = ProvenanceTag.tensor(ProvenanceTag.tensor(a, b), c)
    a_bc = ProvenanceTag.tensor(a, ProvenanceTag.tensor(b, c))
    assert abs(ab_c.belief - a_bc.belief) < 1e-10
    assert abs(ab_c.trust_score - a_bc.trust_score) < 1e-10
    assert ab_c.derivation_depth == a_bc.derivation_depth == 3


def test_oplus_commutativity():
    a = ProvenanceTag(belief=0.6, disbelief=0.1, uncertainty=0.3,
                      trust_score=0.8, decay_factor=0.9, derivation_depth=2)
    b = ProvenanceTag(belief=0.5, disbelief=0.15, uncertainty=0.35,
                      trust_score=0.85, decay_factor=0.95, derivation_depth=1)
    ab = ProvenanceTag.oplus(a, b)
    ba = ProvenanceTag.oplus(b, a)
    assert abs(ab.belief - ba.belief) < 1e-10
    assert abs(ab.disbelief - ba.disbelief) < 1e-10
    assert abs(ab.uncertainty - ba.uncertainty) < 1e-10


def test_tensor_identity():
    a = ProvenanceTag(belief=0.7, disbelief=0.2, uncertainty=0.1,
                      trust_score=0.8, decay_factor=0.9, derivation_depth=2)
    result = ProvenanceTag.tensor(a, ProvenanceTag.one())
    assert abs(result.belief - a.belief) < 1e-10
    assert abs(result.trust_score - a.trust_score) < 1e-10
    assert result.derivation_depth == a.derivation_depth


def test_oplus_identity():
    a = ProvenanceTag(belief=0.7, disbelief=0.2, uncertainty=0.1,
                      trust_score=0.8, decay_factor=0.9, derivation_depth=2)
    result = ProvenanceTag.oplus(a, ProvenanceTag.zero())
    assert abs(result.belief - a.belief) < 1e-10


def test_tensor_annihilation():
    a = ProvenanceTag(belief=0.9, disbelief=0.05, uncertainty=0.05,
                      trust_score=0.9, decay_factor=0.95, derivation_depth=1)
    result = ProvenanceTag.tensor(a, ProvenanceTag.zero())
    assert result.belief == 0.0
    assert result.strength == 0.0


# ── Tag Arithmetic Tests ──

def test_tensor_attenuates():
    a = ProvenanceTag(belief=0.9, disbelief=0.05, uncertainty=0.05,
                      trust_score=0.8, decay_factor=0.9, derivation_depth=1)
    b = ProvenanceTag(belief=0.9, disbelief=0.05, uncertainty=0.05,
                      trust_score=0.85, decay_factor=0.95, derivation_depth=1)
    result = ProvenanceTag.tensor(a, b)
    assert result.belief == pytest.approx(0.81, rel=0.01)  # ~0.81 after normalization
    assert result.belief < min(a.belief, b.belief)  # Attenuation property
    assert result.trust_score == 0.8   # min
    assert result.derivation_depth == 2


def test_oplus_accumulates():
    """Three HYPOTHESIS-level tags: combined belief > any individual."""
    tag = ProvenanceTag(belief=0.6, disbelief=0.1, uncertainty=0.3,
                        trust_score=0.8, decay_factor=0.9, derivation_depth=1)
    combined = ProvenanceTag.oplus(tag, tag)
    combined = ProvenanceTag.oplus(combined, tag)
    assert combined.belief > 0.6  # Non-idempotent accumulation


# ── Epistemic Status Tests ──

def test_epistemic_status_established():
    tag = ProvenanceTag(belief=0.9, disbelief=0.05, uncertainty=0.05)
    assert tag.epistemic_status() == EpistemicStatus.ESTABLISHED


def test_epistemic_status_hypothesis():
    tag = ProvenanceTag(belief=0.6, disbelief=0.15, uncertainty=0.25)
    assert tag.epistemic_status() == EpistemicStatus.HYPOTHESIS


def test_epistemic_status_contested():
    tag = ProvenanceTag(belief=0.4, disbelief=0.5, uncertainty=0.1)
    assert tag.epistemic_status() == EpistemicStatus.CONTESTED


def test_epistemic_status_open():
    tag = ProvenanceTag(belief=0.15, disbelief=0.15, uncertainty=0.7)
    assert tag.epistemic_status() == EpistemicStatus.OPEN


# ── Validation Tests ──

def test_tag_validation_rejects_invalid():
    with pytest.raises(ValueError, match="b \\+ d \\+ u must"):
        ProvenanceTag(belief=0.5, disbelief=0.5, uncertainty=0.5)


# ── Serialization Tests ──

def test_tag_roundtrip():
    tag = ProvenanceTag(
        belief=0.7, disbelief=0.2, uncertainty=0.1,
        source_ids=frozenset(["src1", "src2"]),
        pramana_type=PramanaType.ANUMANA,
        trust_score=0.85, decay_factor=0.9, derivation_depth=2,
    )
    d = tag.to_dict()
    restored = ProvenanceTag.from_dict(d)
    assert abs(restored.belief - tag.belief) < 1e-10
    assert restored.pramana_type == tag.pramana_type
    assert restored.source_ids == tag.source_ids
