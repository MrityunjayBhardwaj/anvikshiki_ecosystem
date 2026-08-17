# anvikshiki_v4/tests/test_algebra_laws.py
"""Law tests for the epistemic lattice and the provenance metadata.

These were written before the removal work, deliberately, and four of the
laws in them failed. Three passed after it without a single assertion being
rewritten — Part 1 was stated over *epistemic status* rather than over belief
triples, and routed through four seam functions, so the subtraction changed
only what `chain`, `accrue` and `status_of` do.

The fourth was depth accounting (#14), and it did not survive contact. As
stated it was a law about a *tag*, and it contradicted two laws that already
held: `one()` is an element of the generated domain, so a demand that
`tensor(t, t)` increase depth cannot coexist with `tensor(one, one) == one`.
No operator satisfies all three. Depth turned out to belong to the argument
rather than to the metadata travelling with it, so the law moved to Part 3,
where a step is something that actually happened. Its generator was the other
half — every tag was built at depth 0, and a single-valued axis cannot tell a
broken operator from an operand that is a premise.

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
# Depth used to be fixed at 0 for every generated tag, and a domain of one
# value cannot distinguish an operator that fails to count a step from an
# operand that is a premise. 0 is a premise, 1 a one-step derivation, 3 a
# deeper one — enough for max, min and + to disagree with each other.
_DEPTHS = (0, 1, 3)


def tag_domain() -> list[ProvenanceTag]:
    """Every tag the metadata laws are quantified over."""
    return [
        ProvenanceTag(
            source_ids=sources,
            pramana_type=pramana,
            trust_score=trust,
            decay_factor=decay,
            derivation_depth=depth,
        )
        for trust, decay, pramana, sources, depth in itertools.product(
            _TRUSTS, _DECAYS, _PRAMANAS, _SOURCE_SETS, _DEPTHS
        )
    ]


def test_the_tag_domain_is_nonempty():
    domain = tag_domain()
    assert len(domain) == (
        len(_TRUSTS) * len(_DECAYS) * len(_PRAMANAS) * len(_SOURCE_SETS)
        * len(_DEPTHS)
    )
    assert len(domain) >= 100


def test_the_tag_domain_varies_every_axis():
    """Including depth, which it did not.

    An axis pinned to one value makes every law quantified over it weaker
    than it reads, and silently: the count in the failure message still
    reports the full denominator.
    """
    domain = tag_domain()
    assert {t.derivation_depth for t in domain} == set(_DEPTHS)
    assert {t.trust_score for t in domain} == set(_TRUSTS)
    assert {t.decay_factor for t in domain} == set(_DECAYS)
    assert {t.pramana_type for t in domain} == set(_PRAMANAS)
    assert {t.source_ids for t in domain} == set(_SOURCE_SETS)


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


def test_metadata_composition_is_idempotent_for_depth_too():
    """Depth stopped being the exception, and this is where that is checked.

    A law demanding that `tensor(t, t)` *increase* depth used to sit here,
    xfailed against #14. It could never have flipped. `one()` is an element
    of the generated domain — trust 1.0, decay 1.0, PRATYAKSA, unsourced,
    depth 0 — and the identity law two tests above pins
    `tensor(one, one) == one`, so no operator satisfies both. Three laws,
    jointly unsatisfiable, and the marker read as though a fix were pending.

    The reason it was stated over a tag at all is that depth happened to be
    stored on one. It is a property of the derivation, not of the metadata
    travelling with it, so the law belongs in Part 3 — over what the compiler
    builds, where a step is something that actually happened.

    The generator is the other half of the story. It emitted
    `derivation_depth=0` and nothing else, so the domain could not tell a
    broken operator from an operand that is a premise. Same blind spot as the
    unsourced-tag one, one level up: the defect was in what the domain failed
    to produce. Depth is a generated axis now.
    """
    domain = tag_domain()
    violations = [
        f"{tag!r} → tensor {ProvenanceTag.tensor(tag, tag)!r} "
        f"/ oplus {ProvenanceTag.oplus(tag, tag)!r}"
        for tag in domain
        if ProvenanceTag.tensor(tag, tag) != tag
        or ProvenanceTag.oplus(tag, tag) != tag
    ]
    assert not violations, report(violations, len(domain))


def test_chaining_carries_the_deeper_of_two_depths():
    """Weakest link, for a field where larger is worse.

    Composition does not invent a step. `max` is what makes the metadata
    laws hold for depth without an exception, and `1 + max` — the part that
    does count a step — happens where an argument is built.
    """
    domain = tag_domain()
    violations = []
    for a, b in itertools.product(domain[::7], domain[::5]):
        chained = ProvenanceTag.tensor(a, b)
        expected = max(depth_of(a), depth_of(b))
        if depth_of(chained) != expected:
            violations.append(
                f"{depth_of(a)} ⊗ {depth_of(b)} = {depth_of(chained)}, "
                f"expected {expected}"
            )
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
    "provisional": EpistemicStatus.PROVISIONAL,
    "open": EpistemicStatus.OPEN,
    "contested": EpistemicStatus.CONTESTED,
}

# The origin ceiling, restated rather than imported, so `_meet_of_links`
# stays an independent walk of the formula instead of asking the code under
# test what it thinks. Every knowledge base in the tree is curated and this
# map is a no-op against them — but a helper that ignored the ceiling would
# report a false failure the moment a fixture gained a generated rule, and
# blame the compiler for it.
_ORIGIN_CEILING = {
    None: EpistemicStatus.ESTABLISHED,
    "curated": EpistemicStatus.ESTABLISHED,
    "guide_extracted": EpistemicStatus.HYPOTHESIS,
    "hitl_promoted": EpistemicStatus.HYPOTHESIS,
    "web_sourced": EpistemicStatus.PROVISIONAL,
    "llm_parametric": EpistemicStatus.PROVISIONAL,
}


def test_both_mirrored_maps_cover_what_the_code_defines():
    """A restated formula that has fallen behind reports a false failure.

    These two maps duplicate `lattice._FROM_KB` and `lattice._ORIGIN_CEILING`
    on purpose — an independent walk is only independent if it does not
    import the thing it checks. The cost is that they can go stale, so the
    staleness is what is asserted, not the values.
    """
    from anvikshiki_v4.schema import AugmentationOrigin
    from anvikshiki_v4.schema import EpistemicStatus as KBEpistemicStatus

    assert {s.value for s in KBEpistemicStatus} == set(_KB_STATUS)
    assert {o.value for o in AugmentationOrigin} | {None} == set(
        _ORIGIN_CEILING
    )


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

    rule = ks.vyaptis[arg.top_rule]
    origin = (
        rule.augmentation_metadata.origin.value
        if rule.augmentation_metadata is not None
        else None
    )
    # The rule enters as its authored status met with its origin's ceiling.
    links = [
        _KB_STATUS[rule.epistemic_status.value],
        _ORIGIN_CEILING[origin],
    ]
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


def test_derivation_depth_through_the_pipeline_counts_inference_steps(
    compiled_af,
):
    """A two-step derivation must not report the same depth as a premise.

    The compiler used to build every tag at depth 0 and compose them with an
    operator that adds, so the field stayed at 0 for every argument in the
    framework — and nothing in the output distinguished a fact that was
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


def _expected_depth(af, arg) -> int:
    """1 + the deepest sub-argument, premises at 0.

    Walked from the argument graph rather than read off the tag, so this
    checks the compiler's answer against an independent recursion — the same
    discipline `_meet_of_links` follows for status.
    """
    if arg.top_rule is None:
        return 0
    return 1 + max(
        (_expected_depth(af, af.arguments[sub]) for sub in arg.sub_arguments),
        default=0,
    )


def test_depth_through_the_pipeline_is_the_height_of_the_derivation(
    compiled_af,
):
    """depth(a) = 1 + max{ depth(s) : s ∈ sub_args(a) }, for every argument.

    Height, not a sum: a rule resting on two sub-arguments at depths 2 and 3
    is 4 deep, not 9. The old axiom said + — and because every tag started at
    0, no fixture ever made the two disagree.
    """
    _, af = compiled_af
    violations = []
    for arg in sorted(af.arguments.values(), key=lambda a: a.id):
        expected = _expected_depth(af, arg)
        if depth_of(arg.tag) != expected:
            violations.append(
                f"{arg.id} ({arg.top_rule or 'premise'} → {arg.conclusion}): "
                f"height says {expected}, pipeline says {depth_of(arg.tag)}"
            )
    assert not violations, report(violations, len(af.arguments))


def test_a_premise_is_depth_zero_and_a_chain_is_deeper(compiled_af):
    """The distinction the field exists to make, asked concretely.

    One step from an asserted premise is 1; the second step through V02 is 2.
    Anything that reports the same number for all three has lost the only
    thing in the output that separates an assertion from an inference.
    """
    _, af = compiled_af

    def depth_for(conclusion: str) -> int:
        args = [a for a in af.arguments.values()
                if a.conclusion == conclusion]
        assert args, f"nothing concludes {conclusion}"
        return min(depth_of(a.tag) for a in args)

    assert depth_for("concentrated_ownership") == 0     # asserted
    assert depth_for("long_horizon_possible") == 1      # V01
    assert depth_for("capability_building_possible") == 2   # V01 then V02
