# tests/test_rebuttal_respects_entity.py
"""Two conclusions can only contradict each other if they are about the same
thing.

`value_creation(acme)` and `not_value_creation(globex)` are compatible claims —
acme creates value, globex does not, and both hold at once. The compiler built
a mutual rebutting attack between them anyway, because `are_contrary` stripped
the entity before comparing and never looked at it again. Rebuttal reaches the
labelling, so this was not a cosmetic mislabel: a valid conclusion about one
company was labelled OUT on the strength of an unrelated fact about another.

The observation that opened it, against the shipped knowledge base:

    facts: positive_unit_economics(acme), organizational_growth(globex)

    value_creation(acme)         V01   IN
    not_value_creation(globex)   V11   OUT     ← denied, and nothing said why

Between plain premises the attack was built but inert, because `_defeats`
refuses to rebut an argument with a strict top rule and premises are strict.
It reaches the labelling only on rule-derived arguments, which are defeasible —
so this became consequential exactly when rules started firing.

Why the binding decides it, and why `None` is a binding
──────────────────────────────────────────────────────
Rebutting is defined as concluding *the contrary of the other's conclusion*,
and the framework's conclusions are ground atoms: a vyāpti is
`smoke(X) -> fire(X)`, and arguments are built by instantiating it. `fire(acme)`
and `fire(globex)` are two atoms, and the entity sits inside the one being
negated. The rationality postulates ask that accepted conclusions be
*consistent*; `{value_creation(acme), not_value_creation(globex)}` already is,
so comparing names alone satisfied a postulate by manufacturing the
inconsistency the postulate exists to rule out.

A bare conclusion is a nullary ground atom, not `∀X. p(X)`. Two bare
conclusions therefore still rebut — every fixture in the tree depends on it —
and a bound conclusion does not rebut a bare one. That last one is a real
limit and is pinned below rather than left implicit.

This restores the compiler's original behaviour. `_are_contrary` compared whole
conclusion strings until an entity strip was added, and prefixing `not_` to the
whole string kept acme and globex apart for free. The strip is still needed for
the domain-pairs lookup, so the binding check is added rather than the strip
removed.
"""

import pytest

from anvikshiki_v4 import t2_compiler_v4
from anvikshiki_v4.predicate_contrariness import (
    are_contrary,
    get_contrary,
    match_veto,
    normalize_negation,
    predicate_entity,
    predicate_name,
)
from anvikshiki_v4.schema_v4 import Label
from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store

KB = "anvikshiki_v4/data/business_expert.yaml"
SHIPPED_KBS = [
    "anvikshiki_v4/data/business_expert.yaml",
    "anvikshiki_v4/data/sample_architecture.yaml",
]


def facts(*predicates):
    return [{"predicate": p, "sources": []} for p in predicates]


def rebuttals(af):
    """Every rebutting attack as a (attacker conclusion, target conclusion)."""
    return [
        (af.arguments[atk.attacker].conclusion,
         af.arguments[atk.target].conclusion)
        for atk in af.attacks
        if atk.attack_type == "rebutting"
    ]


def conclusion_label(af, labels, conclusion):
    for aid, arg in af.arguments.items():
        if arg.conclusion == conclusion:
            return labels[aid]
    raise AssertionError(
        f"no argument concluded {conclusion!r} — the fixture no longer "
        f"exercises what this test is about. Present: "
        f"{sorted(a.conclusion for a in af.arguments.values())}"
    )


@pytest.fixture(scope="module")
def ks():
    return load_knowledge_store(KB)


# ── The law that was missing ────────────────────────────────────────────────

def test_conclusions_about_different_entities_do_not_rebut(ks):
    """The regression proper, at the level where it did damage.

    V01 concludes value_creation(acme); V04+V11 conclude
    not_value_creation(globex). Two companies, no contradiction.
    """
    af = compile_t2(ks, facts(
        "positive_unit_economics(acme)",
        "organizational_growth(globex)",
    ))
    labels = af.compute_grounded()

    # The fixture must actually reach both conclusions, or the assertion below
    # passes by describing a framework that never contained the pair.
    assert conclusion_label(af, labels, "value_creation(acme)") is Label.IN
    assert conclusion_label(
        af, labels, "not_value_creation(globex)"
    ) is Label.IN, (
        "a conclusion about globex was denied on the strength of a fact "
        "about acme"
    )
    assert rebuttals(af) == [], (
        f"cross-entity rebuttal: {rebuttals(af)}"
    )


def test_conclusions_about_the_same_entity_still_rebut(ks):
    """The other half. A genuine contradiction must still defeat.

    Same facts as above with one entity throughout, so V01 and V11 now make
    opposing claims about acme. Removing the spurious attacks must not remove
    the real one.
    """
    af = compile_t2(ks, facts(
        "positive_unit_economics(acme)",
        "organizational_growth(acme)",
    ))
    labels = af.compute_grounded()

    assert set(rebuttals(af)) == {
        ("value_creation(acme)", "not_value_creation(acme)"),
        ("not_value_creation(acme)", "value_creation(acme)"),
    }
    assert Label.OUT in {
        conclusion_label(af, labels, "value_creation(acme)"),
        conclusion_label(af, labels, "not_value_creation(acme)"),
    }, "a real contradiction no longer reaches the labelling"


def test_bare_conclusions_still_rebut(ks):
    """`None` is a binding, and bare-vs-bare is what every fixture writes.

    If this fails, the change has read a bare name as "no entity" rather than
    as an entity in its own right, and every existing rebuttal test in the
    tree is about to go quiet.
    """
    af = compile_t2(ks, facts(
        "positive_unit_economics",
        "organizational_growth",
    ))
    assert set(rebuttals(af)) == {
        ("value_creation", "not_value_creation"),
        ("not_value_creation", "value_creation"),
    }


# ── The limit, stated rather than discovered later ──────────────────────────

def test_a_bound_conclusion_does_not_rebut_a_bare_one():
    """The known cost of treating `None` as a binding.

    A contradiction written across the two forms is missed. This is reachable
    only if the grounder emits a bare predicate, which its prompt forbids
    ("Return predicates as: predicate_name(entity)"), and no captured trace
    contains one. The alternative — reading a bare name as a wildcard matching
    every entity — would put a quantifier back into the attack relation one
    layer after grounding eliminated it, and is the original defect in a
    narrower form: one bare conclusion would still knock out every entity's.

    If this ever needs to change, instantiate at the grounder. Not here.
    """
    assert not are_contrary("value_creation(acme)", "not_value_creation")
    assert not are_contrary("not_value_creation", "value_creation(acme)")


def test_the_domain_pairs_layer_respects_the_binding_too():
    """Layer 2 is the reason the entity strip exists; it must not reopen the
    hole the strip caused.

    `contrariness_pairs` declares opposed *names* — the lookup needs them
    bare — so a version that checked the binding only on the syntactic `not_`
    layer would leave every domain-declared pair entity-blind.
    """
    class _KS:
        contrariness_pairs = [["value_creation", "value_destruction"]]

    ks = _KS()
    assert are_contrary("value_creation(acme)", "value_destruction(acme)", ks)
    assert not are_contrary(
        "value_creation(acme)", "value_destruction(globex)", ks
    )


# ── The other two attack types, examined rather than assumed ────────────────

def test_undermining_targets_an_argument_by_identity_not_by_predicate(ks):
    """Undermining cannot be entity-blind, and this records why.

    A decayed argument gets a `_stale_<id>` attacker aimed at that argument's
    id. No predicate is compared, so there is no binding to lose. Asserted
    here so that a future rewrite comparing conclusions instead trips a test.
    """
    af = compile_t2(ks, facts(
        "positive_unit_economics(acme)",
        "organizational_growth(globex)",
    ))
    for atk in af.attacks:
        if atk.attack_type != "undermining":
            continue
        attacker = af.arguments[atk.attacker]
        assert attacker.conclusion == f"_stale_{atk.target}", (
            "an undermining attack no longer names its target's id — it is "
            "matching on something else, and that something else may be a "
            "predicate compared without its binding"
        )


# ── The generative law, with its denominator and its mutation asserted ──────

def two_entity_framework(kb_path):
    """Every rule in a base, bound to two entities at once.

    The domain has to include the *contrary of each consequent*, not only the
    antecedents. A rebuttal needs both sides of a pair present, and grounding
    antecedents alone reaches only the side the rules derive — which made the
    first version of this law vacuous on `sample_architecture.yaml`: that base
    concludes `not_good_governance` and nothing ever concluded
    `good_governance`, so the framework held no rebuttals at all and "none of
    them cross a binding" was true of an empty set.
    """
    ks = load_knowledge_store(kb_path)
    names = sorted(
        {a for v in ks.vyaptis.values() for a in v.antecedents}
        | {get_contrary(v.consequent) for v in ks.vyaptis.values()}
    )
    assert names, f"{kb_path} declares no predicates to ground"
    grounded = [f"{n}({e})" for n in names for e in ("acme", "globex")]
    return compile_t2(ks, facts(*grounded))


@pytest.mark.parametrize("kb_path", SHIPPED_KBS)
def test_no_rebuttal_in_a_shipped_kb_ever_crosses_a_binding(kb_path):
    """Over every rule in every shipped base, bound to two entities at once.

    The single-case tests above pin one pair. This one asks the question of
    the whole base, and asserts its own denominator first: a law of the form
    "none of them do X" passes trivially over an empty set, so the framework
    is required to contain rebuttals before it is asked whether any cross.
    """
    af = two_entity_framework(kb_path)
    found = rebuttals(af)

    assert found, (
        f"{kb_path} produced no rebutting attacks at all, so this law is "
        f"vacuous for it — the generated domain no longer reaches both sides "
        f"of any contrary pair"
    )

    crossing = [
        (x, y) for x, y in found
        if predicate_entity(x) != predicate_entity(y)
    ]
    assert not crossing, (
        f"{kb_path}: {len(crossing)} of {len(found)} rebuttals cross a "
        f"binding, e.g. {crossing[:3]}"
    )


@pytest.mark.parametrize("kb_path", SHIPPED_KBS)
def test_the_law_above_would_catch_the_defect_it_was_written_for(
    kb_path, monkeypatch
):
    """The law is only worth having if it fails on the old behaviour.

    A law over a generated domain can pass because the generator never
    produced the shape it is about. So the entity-blind comparison is put
    back, the substitution is *asserted to have taken effect*, and only then
    is the law required to fail — a mutation check that silently failed to
    mutate would otherwise report the same thing as one that worked.

    Run against both bases, because the vacuity it guards against was
    base-specific: the first version of the law was live on
    `business_expert.yaml` and empty on `sample_architecture.yaml`, and a
    mutation check on one base would not have said so.
    """
    def entity_blind(a, b, knowledge_store=None):
        na = normalize_negation(predicate_name(a))
        nb = normalize_negation(predicate_name(b))
        return na == f"not_{nb}" or nb == f"not_{na}"

    monkeypatch.setattr(t2_compiler_v4, "are_contrary", entity_blind)

    assert t2_compiler_v4._are_contrary(
        "value_creation(acme)", "not_value_creation(globex)"
    ), (
        "the mutation did not take effect — `_are_contrary` is not reading "
        "the name this test patched, so the failure below would prove nothing"
    )

    with pytest.raises(AssertionError, match="cross a binding"):
        test_no_rebuttal_in_a_shipped_kb_ever_crosses_a_binding(kb_path)


# ── The other caller, unaffected ────────────────────────────────────────────

def test_the_extraction_matcher_is_untouched():
    """`match_veto` is the evaluator's caller and passes names it has already
    stripped, so both sides bind to `None` and the new check is a no-op there.

    Recorded because the fix lives in the shared function: if a future change
    made `match_veto` pass whole predicates, the veto that refuses to match a
    predicate against its own negation would quietly stop firing for anything
    entity-bearing.
    """
    assert match_veto("value_creation", "not_value_creation") is not None
    assert match_veto("value_creation(acme)", "not_value_creation(globex)") \
        is not None
