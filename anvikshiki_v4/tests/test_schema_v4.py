# tests/test_schema_v4.py
"""Tests for the provenance tag and the argument it annotates.

Everything here used to be about the Subjective Logic opinion — that
chaining attenuated belief, that accrual accumulated it, that a tag's belief
and uncertainty could be read through cutoffs to produce a status, and that
b + d + u summed to one. None of that exists now: an argument's grade is its
status in the epistemic lattice, computed from the argumentation labelling.

What is left on the tag is provenance metadata, which composes by min along
a chain and max across accrual. The laws over that composition are stated in
`test_algebra_laws.py`; these are the specific behaviours worth pinning.
"""

import pytest

from anvikshiki_v4.schema_v4 import (
    Argument, EpistemicStatus, PramanaType, ProvenanceTag
)


# ── Composition ──

def test_tensor_is_associative():
    a = ProvenanceTag(trust_score=0.9, decay_factor=0.95, derivation_depth=1)
    b = ProvenanceTag(trust_score=0.85, decay_factor=0.9, derivation_depth=1)
    c = ProvenanceTag(trust_score=0.95, decay_factor=0.92, derivation_depth=1)
    ab_c = ProvenanceTag.tensor(ProvenanceTag.tensor(a, b), c)
    a_bc = ProvenanceTag.tensor(a, ProvenanceTag.tensor(b, c))
    assert ab_c == a_bc
    assert ab_c.derivation_depth == a_bc.derivation_depth == 3


def test_oplus_is_commutative():
    a = ProvenanceTag(trust_score=0.8, decay_factor=0.9, derivation_depth=2)
    b = ProvenanceTag(trust_score=0.85, decay_factor=0.95, derivation_depth=1)
    assert ProvenanceTag.oplus(a, b) == ProvenanceTag.oplus(b, a)


def test_chaining_takes_the_weakest_link():
    a = ProvenanceTag(pramana_type=PramanaType.PRATYAKSA,
                      trust_score=0.8, decay_factor=0.9, derivation_depth=1)
    b = ProvenanceTag(pramana_type=PramanaType.SABDA,
                      trust_score=0.85, decay_factor=0.95, derivation_depth=1)
    result = ProvenanceTag.tensor(a, b)
    assert result.pramana_type == PramanaType.SABDA   # min
    assert result.trust_score == 0.8                  # min
    assert result.decay_factor == 0.9                 # min
    assert result.derivation_depth == 2               # sum


def test_accrual_takes_the_best_source():
    a = ProvenanceTag(pramana_type=PramanaType.SABDA,
                      trust_score=0.8, decay_factor=0.9, derivation_depth=2)
    b = ProvenanceTag(pramana_type=PramanaType.PRATYAKSA,
                      trust_score=0.85, decay_factor=0.95, derivation_depth=1)
    result = ProvenanceTag.oplus(a, b)
    assert result.pramana_type == PramanaType.PRATYAKSA  # max
    assert result.trust_score == 0.85                    # max
    assert result.decay_factor == 0.95                   # max
    assert result.derivation_depth == 1                  # min


def test_accrual_is_idempotent():
    """Restating one argument must not strengthen its provenance.

    This needed a source-overlap discount when accrual was cumulative
    fusion, and the discount did not fire when a tag carried no source ids.
    max is idempotent whatever the provenance says.
    """
    for sources in (frozenset(["s1"]), frozenset(["s1", "s2"]), frozenset()):
        tag = ProvenanceTag(trust_score=0.7, decay_factor=0.8,
                            source_ids=sources)
        assert ProvenanceTag.oplus(tag, tag) == tag


# ── Identities ──

def test_one_is_the_identity_for_chaining():
    """one() sits at the TOP of the metadata lattice, so min leaves a alone."""
    a = ProvenanceTag(pramana_type=PramanaType.SABDA,
                      trust_score=0.8, decay_factor=0.9, derivation_depth=2)
    assert ProvenanceTag.tensor(ProvenanceTag.one(), a) == a
    assert ProvenanceTag.tensor(a, ProvenanceTag.one()) == a


def test_zero_is_the_identity_for_accrual_on_the_lattice_fields():
    """zero() sits at the BOTTOM, so max leaves a alone.

    Built at the top — which is where it used to sit, carrying trust 1.0 and
    decay 1.0 — accruing "no evidence" raised an argument to maximal trust
    and perfect freshness.

    Depth is the documented exception and is *not* covered here, because it
    does not hold: accrual takes the shallowest path by `min`, whose
    identity would have to be an unbounded depth, and no tag can carry one.
    So accruing zero() still flattens depth. That is left for #14, which is
    where depth accounting is settled — asserting it here would mean either
    a false claim or a special case in the operator.
    """
    a = ProvenanceTag(pramana_type=PramanaType.SABDA,
                      trust_score=0.8, decay_factor=0.9, derivation_depth=2)
    for result in (ProvenanceTag.oplus(a, ProvenanceTag.zero()),
                   ProvenanceTag.oplus(ProvenanceTag.zero(), a)):
        assert result.pramana_type == a.pramana_type
        assert result.trust_score == a.trust_score
        assert result.decay_factor == a.decay_factor


def test_accrual_against_zero_still_flattens_depth():
    """The known gap above, asserted so it cannot regress unnoticed.

    When #14 gives depth an identity this should start failing, and that is
    the intent — the test names the wart rather than leaving it implicit.
    """
    a = ProvenanceTag(derivation_depth=2)
    assert ProvenanceTag.oplus(a, ProvenanceTag.zero()).derivation_depth == 0


# ── Arguments must state their status and provenance ──

def test_argument_without_a_status_is_refused():
    with pytest.raises(ValueError, match="without a status"):
        Argument(id="A0", conclusion="p", top_rule=None,
                 tag=ProvenanceTag())


def test_argument_without_a_tag_is_refused():
    with pytest.raises(ValueError, match="without a provenance tag"):
        Argument(id="A0", conclusion="p", top_rule=None,
                 status=EpistemicStatus.HYPOTHESIS)


# ── Serialization ──

def test_tag_roundtrip():
    tag = ProvenanceTag(
        source_ids=frozenset(["src1", "src2"]),
        pramana_type=PramanaType.ANUMANA,
        trust_score=0.85, decay_factor=0.9, derivation_depth=2,
    )
    assert ProvenanceTag.from_dict(tag.to_dict()) == tag


def test_serialized_tag_carries_no_opinion():
    """The wire format is the API contract's other half.

    A belief left in `to_dict` would keep the frontend's schema expecting
    one, and a field that is always absent parses as a break rather than as
    a removal.
    """
    d = ProvenanceTag(trust_score=0.5).to_dict()
    assert set(d) == {
        "source_ids", "pramana_type", "trust_score",
        "decay_factor", "derivation_depth",
    }
