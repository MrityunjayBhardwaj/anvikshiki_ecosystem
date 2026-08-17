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

**Part 3** asks the same questions of the real compiler rather than of tags
composed by hand. This is the part that answers the standing objection: a
law broken on a dataclass in isolation may simply never be reached by the
running pipeline, and if it is not, the removal loses its motivation. It is
reached — on the shipped sample knowledge base, three of four arguments come
out a lattice level below the meet of their own links.

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
from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store


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
_SOURCE_SETS = (
    frozenset({"s1"}),
    frozenset({"s1", "s2"}),
    # The pipeline's default. `compile_t2` builds a query fact's tag with
    # `frozenset(fact.get("sources", []))`, so a fact that arrives without a
    # sources key carries no source ids at all — and the accrual discount
    # keys on source overlap. A domain of only well-sourced tags would never
    # exercise the branch where that discount does not fire.
    frozenset(),
)

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
    reason="the accrual discount does not fire on unsourced tags; see #44",
)
def test_accruing_evidence_against_itself_changes_nothing():
    """Accrual idempotence, stated over every field rather than over status.

    The status-level law above cannot catch this one. Double-counting only
    ever raises belief, and a rising belief never *lowers* status — so the
    defect passes a monotonicity check and is visible only as a change where
    there should be none.

    Idempotence holds today by way of a source-overlap discount: accruing a
    tag against itself is a full overlap, so the fusion is interpolated all
    the way to a plain average of two identical tags. When both tags carry
    no source ids the ratio is 0, the discount never fires, and cumulative
    fusion double-counts one piece of evidence — which is the thing the
    discount was added to prevent.

    Under the target design this is `max(s, s) = s` and needs no discount,
    no source bookkeeping and no special case.
    """
    domain = tag_domain()
    violations = []

    for tag in domain:
        accrued = accrue(tag, tag)
        if accrued.belief != pytest.approx(tag.belief, abs=1e-9):
            violations.append(
                f"belief {tag.belief:.4f} → {accrued.belief:.4f} for {tag!r}"
            )

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


# ═════════════════════════════════════════════════════════════
# Part 3 — The same laws, through the real compiler.
#
# Everything above composes tags directly. That is how the
# restatement defect was first observed, and it is also the
# standing objection to it: a law broken on a dataclass in
# isolation may never be reached by the running pipeline, and if
# it is not, the subtraction loses its empirical motivation.
#
# These two close that gap. They build the argumentation
# framework from the shipped sample knowledge base and ask the
# same questions of what comes out.
# ═════════════════════════════════════════════════════════════

_SAMPLE_KB = "anvikshiki_v4/data/sample_architecture.yaml"

# The knowledge base's four statuses, into the lattice L.
_KB_STATUS = {
    "established": EpistemicStatus.ESTABLISHED,
    "hypothesis": EpistemicStatus.HYPOTHESIS,
    "open": EpistemicStatus.OPEN,
    "contested": EpistemicStatus.CONTESTED,
}


@pytest.fixture
def compiled_af():
    """The sample KB compiled from one query fact.

    V01 (established): concentrated_ownership → long_horizon_possible
    V02 (hypothesis):  long_horizon_possible  → capability_building_possible

    So the framework carries a premise, two one-step derivations and one
    two-step derivation — enough to ask what chaining does to a status and
    to a depth without inventing a fixture the pipeline would never build.
    """
    ks = load_knowledge_store(_SAMPLE_KB)
    facts = [{
        "predicate": "concentrated_ownership",
        "confidence": 0.9,
        "sources": ["q1"],
    }]
    return ks, compile_t2(ks, facts)


def _meet_of_links(ks, af, arg) -> EpistemicStatus:
    """The status the target design assigns: meet over the derivation.

    Premise arguments are taken at whatever status the system assigns them
    today, deliberately. Where a premise's status should come from is #12's
    question, and this law does not need an answer to it — it asks only
    whether *chaining* preserves what it was handed.
    """
    if arg.top_rule is None:
        return status_of(arg.tag)

    links = [_KB_STATUS[ks.vyaptis[arg.top_rule].epistemic_status.value]]
    links += [
        _meet_of_links(ks, af, af.arguments[sub])
        for sub in arg.sub_arguments
    ]
    return min(links, key=rank)


@pytest.mark.xfail(
    strict=True,
    reason="status is thresholded from a belief product, not met over L (#12)",
)
def test_status_through_the_pipeline_is_the_meet_of_its_links(compiled_af):
    """Weakest link, asked of the compiler rather than of a dataclass.

    An argument's status should be the weakest status in its derivation —
    no better, and no worse. Today it is read off a belief product through
    fixed cutoffs, so it lands *below* the meet: one step through an
    established rule from an established premise reports HYPOTHESIS where
    the lattice says ESTABLISHED, and the two-step derivation reports
    PROVISIONAL where the lattice says HYPOTHESIS.

    This is the law whose failure the design document asks for by name. If
    it held today, the restatement defect would be unreachable through the
    real pipeline and the subtraction would lose its empirical motivation.
    """
    ks, af = compiled_af
    assert len(af.arguments) >= 4, "the fixture stopped exercising a chain"

    violations = []
    for arg in sorted(af.arguments.values(), key=lambda a: a.id):
        expected = _meet_of_links(ks, af, arg)
        actual = status_of(arg.tag)
        if actual is not expected:
            violations.append(
                f"{arg.id} ({arg.top_rule or 'premise'} → {arg.conclusion}): "
                f"lattice says {expected.name}, pipeline says {actual.name}"
            )

    assert not violations, report(violations, len(af.arguments))


@pytest.mark.xfail(
    strict=True,
    reason="derivation_depth never increments (#14)",
)
def test_derivation_depth_through_the_pipeline_counts_inference_steps(
    compiled_af,
):
    """A two-step derivation must not report the same depth as a premise.

    The compiler builds every tag at depth 0 and composes them with an
    operator that adds, so the field stays at 0 for every argument in the
    framework — and nothing in the output distinguishes a fact that was
    asserted from one derived through two rules.
    """
    _, af = compiled_af

    derived = [a for a in af.arguments.values() if a.top_rule is not None]
    assert derived, "the fixture stopped exercising a derivation"

    violations = [
        f"{a.id} ({a.top_rule} → {a.conclusion}) reports depth "
        f"{depth_of(a.tag)}, the same as a premise"
        for a in sorted(derived, key=lambda a: a.id)
        if depth_of(a.tag) == 0
    ]

    assert not violations, report(violations, len(derived))
