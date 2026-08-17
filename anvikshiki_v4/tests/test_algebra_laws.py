# anvikshiki_v4/tests/test_algebra_laws.py
"""Law tests for the provenance algebra.

Written *before* the removal work (#12, #14), deliberately. Several of the
laws below are violated by the algebra as it stands today, and each one is
marked `xfail(strict=True)` with the issue that is expected to fix it. That
recorded failure is the evidence the removal is the right move rather than a
preference — and `strict` means the marker itself fails the suite the moment
the law starts holding, so nobody has to remember to come back and delete it.

**Part 1** states its laws over *epistemic status*, not over belief triples,
so the laws survive the subtraction: #12 replaces what `chain`, `accrue` and
`status_of` do without touching the text of a single assertion. That seam is
the point of writing them now.

**Part 2** states properties of the opinion arithmetic itself. #12 deletes
that arithmetic, and these tests go with it — they are here because a law
suite that only described the target design could not tell you what the
current one actually does.

Generation is a deterministic grid rather than `hypothesis`. This suite is a
gate, and a gate that samples randomly reports a different result on
different runs; every counterexample below is reproducible by construction,
and no new dependency lands in a venv whose size is already a constraint.
"""

import itertools

import pytest

from anvikshiki_v4.schema_v4 import (
    EpistemicStatus,
    PramanaType,
    ProvenanceTag,
)


# ── The lattice order ────────────────────────────────────────
#
# L from the design target, minus BOTTOM, which the v4 enum does not carry:
#
#     CONTESTED < OPEN < PROVISIONAL < HYPOTHESIS < ESTABLISHED
#
# Defined here rather than in schema_v4 because this PR adds no production
# code. #12 should move it next to the lattice it derives status from, and
# these tests should then import it from there rather than redeclare it.

STATUS_RANK = {
    EpistemicStatus.CONTESTED: 1,
    EpistemicStatus.OPEN: 2,
    EpistemicStatus.PROVISIONAL: 3,
    EpistemicStatus.HYPOTHESIS: 4,
    EpistemicStatus.ESTABLISHED: 5,
}


def rank(status: EpistemicStatus) -> int:
    return STATUS_RANK[status]


def report(violations: list[str], examined: int) -> str:
    """Render a violation set with its denominator and its worst case.

    A law that reports only the first counterexample it trips over reports
    whichever one the domain happened to order first — which is how a defect
    that costs two lattice levels on ordinary evidence gets read as a
    degenerate corner case. Count, denominator and worst case, always.
    """
    return (
        f"{len(violations)} of {examined} examined violate this law.\n"
        + "\n".join(f"  - {v}" for v in violations[:5])
        + (f"\n  … and {len(violations) - 5} more" if len(violations) > 5 else "")
    )


# ── The seam ─────────────────────────────────────────────────
#
# Part 1's laws are written against these four functions and nothing else.
# Today they route to the opinion arithmetic. After #12 they route to the
# meet/join over L, and the laws are unchanged.

def chain(a: ProvenanceTag, b: ProvenanceTag) -> ProvenanceTag:
    """Sequential composition — reasoning through one step to the next."""
    return ProvenanceTag.tensor(a, b)


def accrue(a: ProvenanceTag, b: ProvenanceTag) -> ProvenanceTag:
    """Parallel composition — two independent arguments for one conclusion."""
    return ProvenanceTag.oplus(a, b)


def status_of(tag: ProvenanceTag) -> EpistemicStatus:
    return tag.epistemic_status()


def depth_of(tag: ProvenanceTag) -> int:
    return tag.derivation_depth


# ── The domain ───────────────────────────────────────────────

_BELIEFS = (0.0, 0.2, 0.4, 0.5, 0.6, 0.75, 0.85, 0.9, 0.95, 1.0)
_DISBELIEF_SHARES = (0.0, 0.5, 1.0)   # share of the remainder given to disbelief
_TRUSTS = (0.3, 1.0)
_DECAYS = (0.5, 1.0)
_PRAMANAS = (PramanaType.UPAMANA, PramanaType.PRATYAKSA)
_SOURCE_SETS = (frozenset({"s1"}), frozenset({"s1", "s2"}))

_RESTATEMENTS = range(2, 6)   # how many times evidence is restated


def tag_domain() -> list[ProvenanceTag]:
    """Every tag the laws are quantified over.

    Constructed the way the pipeline constructs them — in particular at
    `derivation_depth=0`, which is the only depth any production call site
    ever passes (`t2_compiler_v4.py:90,160`, `contestation.py:192`). A depth
    law tested against hand-set nonzero depths would pass for a reason the
    running system never supplies.
    """
    tags = []
    for belief, share, trust, decay, pramana, sources in itertools.product(
        _BELIEFS, _DISBELIEF_SHARES, _TRUSTS, _DECAYS, _PRAMANAS, _SOURCE_SETS
    ):
        remainder = 1.0 - belief
        disbelief = remainder * share
        uncertainty = remainder - disbelief
        tags.append(ProvenanceTag(
            belief=belief,
            disbelief=disbelief,
            uncertainty=uncertainty,
            source_ids=sources,
            pramana_type=pramana,
            trust_score=trust,
            decay_factor=decay,
            derivation_depth=0,
        ))
    return tags


def test_the_domain_is_nonempty_and_well_formed():
    """The denominator for every law below.

    A law quantified over an empty domain passes vacuously and reports the
    same green tick as one that checked something.
    """
    domain = tag_domain()
    assert len(domain) == (
        len(_BELIEFS) * len(_DISBELIEF_SHARES) * len(_TRUSTS)
        * len(_DECAYS) * len(_PRAMANAS) * len(_SOURCE_SETS)
    )
    assert len(domain) >= 100
    for tag in domain:
        total = tag.belief + tag.disbelief + tag.uncertainty
        assert abs(total - 1.0) < 1e-9


# ═════════════════════════════════════════════════════════════
# Part 1 — Laws over epistemic status. These survive #12.
# ═════════════════════════════════════════════════════════════

@pytest.mark.xfail(
    strict=True,
    reason="violated by the continuous algebra; expected to hold after #12",
)
def test_restating_evidence_never_lowers_status_along_a_chain():
    """Restatement monotonicity.

    Restating the same evidence adds nothing, contradicts nothing and
    learns nothing, so it must not degrade a conclusion. Chaining composes
    by meet, and meet is idempotent — under the target design this holds by
    construction for every element and every number of restatements.

    Today chaining multiplies beliefs, so status falls through fixed
    cutoffs after finitely many restatements. No choice of threshold
    repairs it: for any cutoff in (0,1) and any belief < 1 there is an n
    with belief**n below the cutoff.
    """
    domain = tag_domain()
    violations = []

    for tag in domain:
        base = status_of(tag)
        accumulated = tag
        worst = base
        worst_n = 0
        for n in _RESTATEMENTS:
            accumulated = chain(accumulated, tag)
            reached = status_of(accumulated)
            if rank(reached) < rank(worst):
                worst, worst_n = reached, n
        if worst_n:
            violations.append((
                rank(base) - rank(worst),
                f"{base.name} → {worst.name} after {worst_n} restatements "
                f"of {tag!r}",
            ))

    violations.sort(key=lambda v: -v[0])
    assert not violations, report([v[1] for v in violations], len(domain))


def test_restating_evidence_never_lowers_status_across_accrual():
    """The same law on the accrual side, where it already holds.

    Kept as a regression: accrual reaches idempotence today through a
    source-overlap discount — a special case bolted on to restore a law
    that the target design gets from `max(s, s) = s` for free. If that
    discount is ever touched, this is what notices.
    """
    domain = tag_domain()
    violations = []

    for tag in domain:
        base = status_of(tag)
        accumulated = tag
        for n in _RESTATEMENTS:
            accumulated = accrue(accumulated, tag)
            reached = status_of(accumulated)
            if rank(reached) < rank(base):
                violations.append(
                    f"{base.name} → {reached.name} after {n} accruals "
                    f"of {tag!r}"
                )
                break

    assert not violations, report(violations, len(domain))


@pytest.mark.xfail(
    strict=True,
    reason="derivation_depth never increments (#14)",
)
def test_chaining_increases_derivation_depth():
    """Depth accounting.

    The docstring states the axiom "chains add depth". Every production
    call site constructs tags at depth 0 and `tensor` adds, so 0 + 0 = 0
    holds forever and the field that would have exposed the restatement bug
    is the one that never moves.

    Stated as strict increase rather than a specific count, because the
    convention — whether a chain of n premises reports depth n or n-1 —
    belongs to #14 and is not what is broken here.
    """
    domain = tag_domain()
    violations = []

    for tag in domain:
        accumulated = tag
        previous = depth_of(accumulated)
        for n in _RESTATEMENTS:
            accumulated = chain(accumulated, tag)
            if depth_of(accumulated) <= previous:
                violations.append(
                    f"chain of {n} left derivation_depth at "
                    f"{depth_of(accumulated)} for {tag!r}"
                )
                break
            previous = depth_of(accumulated)

    assert not violations, report(violations, len(domain))


# ═════════════════════════════════════════════════════════════
# Part 2 — Properties of the opinion arithmetic. #12 deletes these.
# ═════════════════════════════════════════════════════════════

def test_one_is_a_left_identity_for_the_opinion():
    """The control, and it holds — on one side."""
    for tag in tag_domain():
        result = chain(ProvenanceTag.one(), tag)
        assert result.belief == pytest.approx(tag.belief, abs=1e-12)
        assert result.disbelief == pytest.approx(tag.disbelief, abs=1e-12)
        assert result.uncertainty == pytest.approx(tag.uncertainty, abs=1e-12)


def test_one_is_a_left_identity_only():
    """`one()` is documented as "the" identity without naming a side.

    Trust discounting is asymmetric by construction — `a ⊗ b` reads as a's
    opinion about b's opinion — so a right identity was never on offer.
    This records the asymmetry rather than filing it as a defect: chaining
    a tag *through* a certain rule zeroes whatever disbelief it had
    accumulated, because `new_d = a.belief × b.disbelief`.

    The docstring's unqualified "Identity = one()" is what wants amending
    (#26), not the arithmetic — which #12 removes anyway.
    """
    disbelieving = [t for t in tag_domain() if t.disbelief > 0.0]
    assert disbelieving, "domain carries no tag with disbelief to lose"

    erased = [
        t for t in disbelieving
        if chain(t, ProvenanceTag.one()).disbelief != pytest.approx(
            t.disbelief, abs=1e-12
        )
    ]
    assert len(erased) == len(disbelieving), (
        "right-chaining through one() no longer erases disbelief — the "
        "asymmetry this test records has changed"
    )


@pytest.mark.xfail(
    strict=True,
    reason="zero() carries top-of-lattice metadata; see #42",
)
def test_zero_is_an_additive_identity_for_every_field():
    """Accruing no evidence must change nothing.

    It changes three things. `zero()` means "no evidence", but it is
    constructed with `trust_score=1.0`, `decay_factor=1.0` and
    `pramana_type=ANUMANA` — the *top* of the join lattice on two of those
    fields and the middle of it on the third. So accruing a no-evidence tag
    raises an argument's trust and freshness to maximal, and `strength`
    (belief × trust × decay) is what drives defeat.

    The join identity is bottom, not top: trust 0.0, decay 0.0, pramana
    UPAMANA. Depth is a third case — `oplus` takes min, so accrual against
    depth 0 flattens any depth the argument had.
    """
    zero = ProvenanceTag.zero()
    domain = tag_domain()
    violations = []

    for tag in domain:
        result = accrue(tag, zero)
        moved = []
        if result.trust_score != pytest.approx(tag.trust_score):
            moved.append(f"trust {tag.trust_score} → {result.trust_score}")
        if result.decay_factor != pytest.approx(tag.decay_factor):
            moved.append(f"decay {tag.decay_factor} → {result.decay_factor}")
        if result.pramana_type != tag.pramana_type:
            moved.append(
                f"pramana {tag.pramana_type.name} → {result.pramana_type.name}"
            )
        if result.derivation_depth != tag.derivation_depth:
            moved.append(
                f"depth {tag.derivation_depth} → {result.derivation_depth}"
            )
        if moved:
            violations.append(f"{', '.join(moved)} for {tag!r}")

    assert not violations, report(violations, len(domain))


def test_zero_is_an_additive_identity_for_the_opinion():
    """The opinion half of the identity, which does hold."""
    zero = ProvenanceTag.zero()
    for tag in tag_domain():
        result = accrue(tag, zero)
        assert result.belief == pytest.approx(tag.belief, abs=1e-9)
        assert result.disbelief == pytest.approx(tag.disbelief, abs=1e-9)
        assert result.uncertainty == pytest.approx(tag.uncertainty, abs=1e-9)


def test_chaining_is_associative():
    """Exact in the reals; asserted within float tolerance.

    Jøsang discounting preserves b + d + u = 1 by construction rather than
    by renormalisation, which is precisely why associativity is available
    to assert at all — the renormalised tensor it replaced broke it.
    """
    sample = tag_domain()[::7]
    assert len(sample) >= 20

    for a, b, c in itertools.product(sample[:12], sample[:12], sample[:12]):
        left = chain(chain(a, b), c)
        right = chain(a, chain(b, c))
        assert left.belief == pytest.approx(right.belief, abs=1e-12)
        assert left.disbelief == pytest.approx(right.disbelief, abs=1e-12)
        assert left.uncertainty == pytest.approx(right.uncertainty, abs=1e-12)
        assert left.pramana_type == right.pramana_type
        assert left.trust_score == pytest.approx(right.trust_score, abs=1e-12)
        assert left.decay_factor == pytest.approx(right.decay_factor, abs=1e-12)
        assert left.derivation_depth == right.derivation_depth


def test_accrual_is_commutative():
    """Order of two independent arguments must not matter."""
    sample = tag_domain()[::5]
    assert len(sample) >= 20

    for a, b in itertools.product(sample[:20], sample[:20]):
        left = accrue(a, b)
        right = accrue(b, a)
        assert left.belief == pytest.approx(right.belief, abs=1e-12)
        assert left.disbelief == pytest.approx(right.disbelief, abs=1e-12)
        assert left.uncertainty == pytest.approx(right.uncertainty, abs=1e-12)
