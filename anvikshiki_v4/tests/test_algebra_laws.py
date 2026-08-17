# anvikshiki_v4/tests/test_algebra_laws.py
"""Law tests for the epistemic lattice and the provenance metadata.

These were written before the removal work, deliberately, and four of the
laws in them failed. Three now pass, and they pass without a single
assertion being rewritten — Part 1 was stated over *epistemic status* rather
than over belief triples, and routed through four seam functions, so the
subtraction changed only what `chain`, `accrue` and `status_of` do.

What is left failing is depth accounting (#14), which the subtraction did
not touch and was never going to: depth is metadata, and it survives the
removal exactly as it was.

Generation is a deterministic grid rather than `hypothesis`. This suite is a
gate, and a gate that samples randomly reports a different result on
different runs; every counterexample below is reproducible by construction,
and no new dependency lands in a venv whose size is already a constraint.
"""

import itertools

import pytest

from anvikshiki_v4.lattice import STATUS_ORDER, join, meet, rank
from anvikshiki_v4.schema_v4 import (
    EpistemicStatus,
    PramanaType,
    ProvenanceTag,
)
from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store


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
# They used to route to the Subjective Logic opinion arithmetic; they now
# route to the meet and join over L. The laws did not change.

def chain(a: EpistemicStatus, b: EpistemicStatus) -> EpistemicStatus:
    """Sequential composition — reasoning through one step to the next."""
    return meet([a, b])


def accrue(a: EpistemicStatus, b: EpistemicStatus) -> EpistemicStatus:
    """Parallel composition — two independent arguments for one conclusion."""
    return join([a, b])


def status_of(status: EpistemicStatus) -> EpistemicStatus:
    return status


def depth_of(tag: ProvenanceTag) -> int:
    return tag.derivation_depth


_RESTATEMENTS = range(2, 6)   # how many times evidence is restated


def status_domain() -> list[EpistemicStatus]:
    """Every element of L. The lattice is small and fully enumerable."""
    return list(STATUS_ORDER)


def test_the_status_domain_is_the_whole_lattice():
    """The denominator for every law in Part 1.

    A law quantified over an empty domain passes vacuously and reports the
    same green tick as one that checked something.
    """
    domain = status_domain()
    assert len(domain) == len(EpistemicStatus)
    assert set(domain) == set(EpistemicStatus)
    # Total order, strictly increasing, no two elements sharing a rank.
    assert [rank(s) for s in domain] == sorted(rank(s) for s in domain)
    assert len({rank(s) for s in domain}) == len(domain)


# ═════════════════════════════════════════════════════════════
# Part 1 — Laws over epistemic status.
# ═════════════════════════════════════════════════════════════

def test_restating_evidence_never_lowers_status_along_a_chain():
    """Restatement monotonicity.

    Restating the same evidence adds nothing, contradicts nothing and
    learns nothing, so it must not degrade a conclusion. Chaining composes
    by meet, and meet is idempotent — under the target design this holds by
    construction for every element and every number of restatements.

    It did not hold before. Chaining multiplied beliefs, so status fell
    through fixed cutoffs after finitely many restatements, and no choice of
    threshold repaired it: for any cutoff in (0,1) and any belief < 1 there
    is an n with belief**n below the cutoff. 552 of 720 generated tags
    violated this. The lattice makes it `min(s, s) = s`.
    """
    domain = status_domain()
    violations = []

    for status in domain:
        base = status_of(status)
        accumulated = status
        worst = base
        worst_n = 0
        for n in _RESTATEMENTS:
            accumulated = chain(accumulated, status)
            reached = status_of(accumulated)
            if rank(reached) < rank(worst):
                worst, worst_n = reached, n
        if worst_n:
            violations.append((
                rank(base) - rank(worst),
                f"{base.name} → {worst.name} after {worst_n} restatements",
            ))

    violations.sort(key=lambda v: -v[0])
    assert not violations, report([v[1] for v in violations], len(domain))


def test_restating_evidence_never_lowers_status_across_accrual():
    """The same law on the accrual side.

    This one held before too, but only because of a source-overlap discount
    bolted on to restore it — a special case that silently failed to fire
    when neither tag carried a source id. Here it is `max(s, s) = s`, with
    nothing to discount and nothing to fail to fire.
    """
    domain = status_domain()
    violations = []

    for status in domain:
        base = status_of(status)
        accumulated = status
        for n in _RESTATEMENTS:
            accumulated = accrue(accumulated, status)
            reached = status_of(accumulated)
            if rank(reached) < rank(base):
                violations.append(
                    f"{base.name} → {reached.name} after {n} accruals"
                )
                break

    assert not violations, report(violations, len(domain))


def test_accruing_evidence_against_itself_changes_nothing():
    """Accrual idempotence, stated as equality rather than as no-decrease.

    The monotonicity law above cannot catch double-counting: it only ever
    raises a conclusion, and a rise passes a no-decrease check cleanly. The
    defect is visible only as a change where there should be none.
    """
    domain = status_domain()
    violations = [
        f"{s.name} → {accrue(s, s).name}"
        for s in domain if accrue(s, s) is not s
    ]
    assert not violations, report(violations, len(domain))


def test_chaining_is_bounded_by_its_weakest_link():
    """The meet is a bound, not an average or a product.

    A chain can be no stronger than the weakest thing it passed through, and
    no weaker either — the second half is what the belief product got wrong.
    """
    domain = status_domain()
    violations = []
    for a, b, c in itertools.product(domain, domain, domain):
        result = chain(chain(a, b), c)
        expected = min([a, b, c], key=rank)
        if result is not expected:
            violations.append(
                f"{a.name} ⋀ {b.name} ⋀ {c.name} = {result.name}, "
                f"expected {expected.name}"
            )
    assert not violations, report(violations, len(domain) ** 3)


def test_chaining_and_accrual_are_associative_and_commutative():
    domain = status_domain()
    for a, b, c in itertools.product(domain, domain, domain):
        assert chain(chain(a, b), c) is chain(a, chain(b, c))
        assert accrue(accrue(a, b), c) is accrue(a, accrue(b, c))
        assert chain(a, b) is chain(b, a)
        assert accrue(a, b) is accrue(b, a)


def test_composing_nothing_is_refused():
    """An empty meet is the top and an empty join is the bottom.

    Both conventions would turn an absence into a finding: ESTABLISHED for a
    derivation that composed no evidence, CONTESTED for a conclusion nothing
    ever argued. The lattice refuses instead of picking one.
    """
    with pytest.raises(ValueError, match="meet over no statuses"):
        meet([])
    with pytest.raises(ValueError, match="join over no statuses"):
        join([])


# ═════════════════════════════════════════════════════════════
# Part 2 — Laws over the provenance metadata that remains.
# ═════════════════════════════════════════════════════════════

_TRUSTS = (0.0, 0.3, 0.7, 1.0)
_DECAYS = (0.0, 0.5, 1.0)
_PRAMANAS = tuple(PramanaType)
_SOURCE_SETS = (
    frozenset({"s1"}),
    frozenset({"s1", "s2"}),
    # The pipeline's default: `compile_t2` builds a query fact's tag with
    # `frozenset(fact.get("sources", []))`, so a fact arriving without a
    # sources key carries no source ids at all. A domain of only
    # well-sourced tags never reaches that branch — which is exactly how a
    # defect in the old accrual discount stayed invisible.
    frozenset(),
)


def tag_domain() -> list[ProvenanceTag]:
    """Every tag the metadata laws are quantified over."""
    return [
        ProvenanceTag(
            source_ids=sources,
            pramana_type=pramana,
            trust_score=trust,
            decay_factor=decay,
            derivation_depth=0,
        )
        for trust, decay, pramana, sources in itertools.product(
            _TRUSTS, _DECAYS, _PRAMANAS, _SOURCE_SETS
        )
    ]


def test_the_tag_domain_is_nonempty():
    domain = tag_domain()
    assert len(domain) == (
        len(_TRUSTS) * len(_DECAYS) * len(_PRAMANAS) * len(_SOURCE_SETS)
    )
    assert len(domain) >= 100


def test_metadata_chaining_is_idempotent():
    domain = tag_domain()
    violations = [
        f"{tag!r} → {ProvenanceTag.tensor(tag, tag)!r}"
        for tag in domain
        # depth is the documented exception: tensor sums it
        if ProvenanceTag.tensor(tag, tag).to_dict() | {"derivation_depth": 0}
        != tag.to_dict() | {"derivation_depth": 0}
    ]
    assert not violations, report(violations, len(domain))


def test_metadata_accrual_is_idempotent():
    """Including for tags carrying no source ids.

    The discount this used to depend on keyed on source overlap and did not
    fire when both operands were unsourced, so accrual double-counted
    exactly where provenance was unknown.
    """
    domain = tag_domain()
    violations = [
        f"{tag!r} → {ProvenanceTag.oplus(tag, tag)!r}"
        for tag in domain if ProvenanceTag.oplus(tag, tag) != tag
    ]
    assert not violations, report(violations, len(domain))


def test_metadata_composition_is_associative():
    sample = tag_domain()[::5]
    assert len(sample) >= 8
    for a, b, c in itertools.product(sample, sample, sample):
        assert (ProvenanceTag.tensor(ProvenanceTag.tensor(a, b), c)
                == ProvenanceTag.tensor(a, ProvenanceTag.tensor(b, c)))
        assert (ProvenanceTag.oplus(ProvenanceTag.oplus(a, b), c)
                == ProvenanceTag.oplus(a, ProvenanceTag.oplus(b, c)))


def test_metadata_accrual_is_commutative():
    sample = tag_domain()[::3]
    assert len(sample) >= 12
    for a, b in itertools.product(sample, sample):
        assert ProvenanceTag.oplus(a, b) == ProvenanceTag.oplus(b, a)


def test_one_is_the_identity_for_chaining():
    """Both sides now. Trust discounting was asymmetric and `one()` was a
    left identity only; min is not, so the law is the full one."""
    domain = tag_domain()
    one = ProvenanceTag.one()
    violations = [
        f"{tag!r}" for tag in domain
        if ProvenanceTag.tensor(one, tag) != tag
        or ProvenanceTag.tensor(tag, one) != tag
    ]
    assert not violations, report(violations, len(domain))


def test_zero_is_the_identity_for_accrual_on_the_lattice_fields():
    """`zero()` sits at the bottom of the lattice, so max leaves a tag alone.

    Built at the top — carrying trust 1.0 and decay 1.0, as it used to —
    accruing "no evidence" raised an argument to maximal trust and perfect
    freshness. Depth is excluded here and covered by the next test.
    """
    domain = tag_domain()
    zero = ProvenanceTag.zero()
    violations = []
    for tag in domain:
        result = ProvenanceTag.oplus(tag, zero)
        if (result.trust_score != tag.trust_score
                or result.decay_factor != tag.decay_factor
                or result.pramana_type != tag.pramana_type):
            violations.append(f"{tag!r} → {result!r}")
    assert not violations, report(violations, len(domain))


@pytest.mark.xfail(
    strict=True,
    reason="derivation_depth never increments (#14)",
)
def test_chaining_increases_derivation_depth():
    """Depth accounting, untouched by the subtraction.

    Every production call site builds tags at depth 0 and `tensor` adds, so
    0 + 0 = 0 holds forever and nothing in the output distinguishes an
    asserted fact from one derived through two rules. Depth is metadata: it
    survived the removal exactly as it was, and #14 is where it is fixed.
    """
    domain = tag_domain()
    violations = []

    for tag in domain:
        accumulated = tag
        previous = depth_of(accumulated)
        for n in _RESTATEMENTS:
            accumulated = ProvenanceTag.tensor(accumulated, tag)
            if depth_of(accumulated) <= previous:
                violations.append(
                    f"chain of {n} left derivation_depth at "
                    f"{depth_of(accumulated)} for {tag!r}"
                )
                break
            previous = depth_of(accumulated)

    assert not violations, report(violations, len(domain))


# ═════════════════════════════════════════════════════════════
# Part 3 — The same laws, through the real compiler.
#
# Everything above composes values directly. That is how the
# restatement defect was first observed, and it was also the
# standing objection to it: a law broken on a dataclass in
# isolation may never be reached by the running pipeline, and if
# it is not, the removal loses its empirical motivation.
#
# Before the subtraction, three of four arguments here came out a
# lattice level below the meet of their own links.
# ═════════════════════════════════════════════════════════════

_SAMPLE_KB = "anvikshiki_v4/data/sample_architecture.yaml"

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
    """The status the design assigns: meet over the derivation.

    Recomputed here from the knowledge base rather than read back off the
    argument, so this checks the compiler's answer against an independent
    walk of the same formula.
    """
    if arg.top_rule is None:
        return arg.status

    links = [_KB_STATUS[ks.vyaptis[arg.top_rule].epistemic_status.value]]
    links += [
        _meet_of_links(ks, af, af.arguments[sub])
        for sub in arg.sub_arguments
    ]
    return meet(links)


def test_status_through_the_pipeline_is_the_meet_of_its_links(compiled_af):
    """Weakest link, asked of the compiler rather than of a dataclass.

    An argument's status is the weakest status in its derivation — no
    better, and no worse. It used to be read off a belief product through
    fixed cutoffs and landed *below* the meet: one step through an
    established rule from an established premise reported HYPOTHESIS where
    the lattice says ESTABLISHED, and the two-step derivation reported
    PROVISIONAL where the lattice says HYPOTHESIS.
    """
    ks, af = compiled_af
    assert len(af.arguments) >= 4, "the fixture stopped exercising a chain"

    violations = []
    for arg in sorted(af.arguments.values(), key=lambda a: a.id):
        expected = _meet_of_links(ks, af, arg)
        if arg.status is not expected:
            violations.append(
                f"{arg.id} ({arg.top_rule or 'premise'} → {arg.conclusion}): "
                f"lattice says {expected.name}, pipeline says {arg.status.name}"
            )

    assert not violations, report(violations, len(af.arguments))


def test_an_established_chain_stays_established(compiled_af):
    """The concrete case the issue was filed about.

    V01 is marked established in the knowledge base and the premise is
    asserted, so one inference step must not come back HYPOTHESIS.
    """
    _, af = compiled_af
    af.compute_grounded()

    status, _, _ = af.get_epistemic_status("long_horizon_possible")
    assert status == EpistemicStatus.ESTABLISHED

    # And the second step, through a rule the KB records as a hypothesis,
    # lands exactly there — the weakest link, not a level below it.
    status, _, _ = af.get_epistemic_status("capability_building_possible")
    assert status == EpistemicStatus.HYPOTHESIS


def test_a_conclusion_nothing_argues_has_no_status(compiled_af):
    """Distinct from CONTESTED, which is a positive claim about defeat."""
    _, af = compiled_af
    af.compute_grounded()
    status, _, args = af.get_epistemic_status("never_mentioned_anywhere")
    assert status is None
    assert args == []


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
