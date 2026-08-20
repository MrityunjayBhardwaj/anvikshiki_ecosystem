# tests/test_scope_exclusions_respect_entity.py
"""A scope exclusion excludes the entity it was observed of, not the rule.

`Vyapti` writes a rule as

    consequent(Entity) :- antecedent1(Entity), …, not scope_exclusion1(Entity)

— one Entity variable throughout. The compiler dropped it from the exclusion
half: the moment *any* argument matched an exclusion predicate it built a
single `inapplicable_<vid>` argument and aimed it at every argument using that
rule. One firm in a perfectly commoditized market suppressed V03 for every
firm in the query.

    superior_information(acme), superior_information(globex),
    perfectly_commoditized_market(acme)

    pricing_power(acme)     V03   OUT     ← correct, acme is excluded
    pricing_power(globex)   V03   OUT     ← wrong, globex is not

It fails toward caution rather than confidence — the effect is denying
conclusions that should stand, not asserting ones that should not — which is
why it ranked below the rebuttal case. The output is still wrong.

Why it was invisible: the block returns early when no argument uses the rule,
and until rules began firing none ever did, so the whole path was unreachable
dead code and had never been evaluated on any input. It was found by asking
what that fix had switched on rather than by reading its diff, and pinned with
a law asserting the wrong behaviour so that closing it would break a test.

Three things had to move together, and the third is the one that is easy to
miss: the trigger, the target, and the dedup guard. The guard skipped
construction when an `inapplicable_<vid>` argument already existed, so binding
only the trigger and the target would have let the first entity's undercutter
suppress every later one — a second entity's exclusion silently doing nothing.
"""

import pytest

from anvikshiki_v4 import t2_compiler_v4
from anvikshiki_v4.predicate_contrariness import predicate_entity
from anvikshiki_v4.schema_v4 import Label
from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store

KB = "anvikshiki_v4/data/business_expert.yaml"
SHIPPED_KBS = [
    "anvikshiki_v4/data/business_expert.yaml",
    "anvikshiki_v4/data/sample_architecture.yaml",
]


def facts(*predicates):
    return [{"predicate": p, "sources": []} for p in predicates]


def undercuts(af):
    """Every undercutting attack as (undercutter conclusion, target)."""
    return [
        (af.arguments[atk.attacker].conclusion,
         af.arguments[atk.target].conclusion)
        for atk in af.attacks
        if atk.attack_type == "undercutting"
    ]


def label_of(af, labels, conclusion):
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

def test_an_exclusion_denies_only_the_entity_it_was_observed_of(ks):
    """The regression proper, asserted at the label rather than the attack.

    globex is not in a commoditized market. Its conclusion must stand.
    """
    af = compile_t2(ks, facts(
        "superior_information(acme)",
        "superior_information(globex)",
        "perfectly_commoditized_market(acme)",
    ))
    labels = af.compute_grounded()

    assert label_of(af, labels, "pricing_power(acme)") is Label.OUT
    assert label_of(af, labels, "pricing_power(globex)") is Label.IN, (
        "globex's conclusion was denied by an exclusion observed of acme"
    )
    assert undercuts(af) == [
        ("inapplicable_V03(acme)", "pricing_power(acme)")
    ]


def test_the_undercutter_carries_the_binding_it_was_built_for(ks):
    """`inapplicable_V03(acme)`, not `inapplicable_V03`.

    Without the binding two entities excluded from one rule collide on a
    single argument, and the framework can no longer say which entity the
    exclusion was about — including to a reader of the provenance panel.
    """
    af = compile_t2(ks, facts(
        "superior_information(acme)",
        "perfectly_commoditized_market(acme)",
    ))
    scope_args = [
        a for a in af.arguments.values()
        if a.conclusion.startswith("inapplicable_")
    ]
    assert [a.conclusion for a in scope_args] == ["inapplicable_V03(acme)"]
    assert scope_args[0].premises == frozenset(
        ["perfectly_commoditized_market(acme)"]
    ), (
        "the premise must record the fact as observed. With one undercutter "
        "per entity a bare name reads identically on all of them, and this "
        "premise is what vāda offers back as evidence to check."
    )


def test_two_excluded_entities_each_get_their_own_undercutter(ks):
    """The dedup guard is the part that is easy to get wrong.

    It skipped construction when an `inapplicable_<vid>` argument already
    existed. Binding the trigger and the target but leaving that guard
    unbound would let acme's undercutter suppress globex's, so globex would
    be excluded and keep its conclusion anyway — the defect inverted rather
    than fixed, and invisible in the single-entity case above.
    """
    af = compile_t2(ks, facts(
        "superior_information(acme)",
        "superior_information(globex)",
        "perfectly_commoditized_market(acme)",
        "perfectly_commoditized_market(globex)",
    ))
    labels = af.compute_grounded()

    assert set(undercuts(af)) == {
        ("inapplicable_V03(acme)", "pricing_power(acme)"),
        ("inapplicable_V03(globex)", "pricing_power(globex)"),
    }
    assert label_of(af, labels, "pricing_power(acme)") is Label.OUT
    assert label_of(af, labels, "pricing_power(globex)") is Label.OUT


def test_bare_exclusions_behave_exactly_as_before(ks):
    """`None` is a binding, and every KB fixture in the tree is written bare.

    A base with no entities anywhere must produce the same single unbound
    undercutter it always did.
    """
    af = compile_t2(ks, facts(
        "superior_information",
        "perfectly_commoditized_market",
    ))
    assert undercuts(af) == [("inapplicable_V03", "pricing_power")]


def test_an_exclusion_about_one_entity_does_not_reach_a_bare_conclusion(ks):
    """The mirror of the rebuttal limit, recorded for the same reason.

    A bare conclusion is a nullary ground atom, not "every entity", so an
    exclusion observed of acme does not undercut an unbound derivation. The
    grounder contracts to emit `predicate_name(entity)` so production does not
    mix the two, but the behaviour should be stated rather than discovered.
    """
    af = compile_t2(ks, facts(
        "superior_information",
        "perfectly_commoditized_market(acme)",
    ))
    assert undercuts(af) == []


# ── The generative law, with its denominator and its mutation asserted ──────

@pytest.mark.parametrize("kb_path", SHIPPED_KBS)
def test_no_undercut_in_a_shipped_kb_ever_crosses_a_binding(kb_path):
    """Every rule in every shipped base, excluded for one entity of two.

    The domain grounds each rule's antecedents for both entities and each
    rule's exclusions for `acme` alone, so every exclusion in the base has a
    globex conclusion standing beside it that it must not touch.

    The framework is required to contain undercuts before it is asked whether
    any cross a binding — "none of them do X" is true of an empty set, and a
    version of this law that grounded too little would pass by describing one.
    """
    ks = load_knowledge_store(kb_path)
    antecedents = sorted({
        a for v in ks.vyaptis.values() for a in v.antecedents
    })
    exclusions = sorted({
        e for v in ks.vyaptis.values() for e in v.scope_exclusions
    })
    assert antecedents and exclusions, (
        f"{kb_path} declares no antecedents or no exclusions, so this law "
        f"cannot be exercised against it"
    )

    grounded = (
        [f"{a}({e})" for a in antecedents for e in ("acme", "globex")]
        + [f"{x}(acme)" for x in exclusions]
    )
    af = compile_t2(ks, facts(*grounded))
    found = undercuts(af)

    assert found, (
        f"{kb_path} produced no undercutting attacks at all, so this law is "
        f"vacuous for it — the generated domain no longer reaches the "
        f"exclusion path"
    )

    crossing = [
        (x, y) for x, y in found
        if predicate_entity(x) != predicate_entity(y)
    ]
    assert not crossing, (
        f"{kb_path}: {len(crossing)} of {len(found)} undercuts cross a "
        f"binding, e.g. {crossing[:3]}"
    )


@pytest.mark.parametrize("kb_path", SHIPPED_KBS)
def test_the_law_above_would_catch_the_defect_it_was_written_for(
    kb_path, monkeypatch
):
    """The law is only worth having if it fails on the old behaviour.

    The mutation restores the old reach — every argument built from the rule,
    regardless of binding — and nothing else. An earlier attempt patched
    `predicate_entity` itself, which was too broad: it unbinds the rule
    derivation as well, so the whole framework goes bare, there is only one
    entity left and #83 cannot be exhibited at all. The mutation has to be as
    narrow as the defect. That the first one silently produced *no* crossing
    undercuts, rather than an error, is exactly why the substitution is
    asserted to have taken effect before the law is required to fail.
    """
    monkeypatch.setattr(
        t2_compiler_v4, "_rule_arguments_reached_by_exclusion",
        lambda af, vid, entity: [
            a for a in af.arguments.values() if a.top_rule == vid
        ],
    )

    ks = load_knowledge_store(kb_path)
    probe = compile_t2(ks, facts(
        *[f"{a}({e})" for v in ks.vyaptis.values() for a in v.antecedents
          for e in ("acme", "globex")],
        *[f"{x}(acme)" for v in ks.vyaptis.values()
          for x in v.scope_exclusions],
    ))
    blind = [
        (x, y) for x, y in undercuts(probe)
        if predicate_entity(x) != predicate_entity(y)
    ]
    assert blind, (
        "the mutation did not take effect — the exclusion block is not "
        "reading the name this test patched, so the failure below would "
        "prove nothing"
    )

    with pytest.raises(AssertionError, match="cross a binding"):
        test_no_undercut_in_a_shipped_kb_ever_crosses_a_binding(kb_path)


@pytest.mark.parametrize("kb_path", SHIPPED_KBS)
def test_every_globex_conclusion_survives_an_acme_only_exclusion(kb_path):
    """The consequence the attack-level law does not state.

    An undercut that crosses a binding is only worth catching because it
    denies a conclusion. This asserts the denial directly: with every
    exclusion observed of acme alone, no globex conclusion may be denied *by
    an undercutter*.

    Scoped to undercutting deliberately. A first version asserted that no
    globex conclusion could be OUT at all, and it failed on
    `not_value_creation(globex)` — which the generated domain denies through a
    perfectly good same-entity rebuttal, because it asserts
    `value_creation(globex)` as a fact and V11 derives its negation. A law
    over a generated domain has to name the mechanism it is about, or it
    reports the domain's other mechanisms as failures.
    """
    ks = load_knowledge_store(kb_path)
    antecedents = sorted({
        a for v in ks.vyaptis.values() for a in v.antecedents
    })
    exclusions = sorted({
        e for v in ks.vyaptis.values() for e in v.scope_exclusions
    })
    grounded = (
        [f"{a}({e})" for a in antecedents for e in ("acme", "globex")]
        + [f"{x}(acme)" for x in exclusions]
    )
    af = compile_t2(ks, facts(*grounded))
    labels = af.compute_grounded()

    globex_args = [
        a for a in af.arguments.values()
        if predicate_entity(a.conclusion) == "globex" and a.top_rule
    ]
    assert globex_args, f"{kb_path} derived nothing for globex"

    undercut_targets = {
        atk.target for atk in af.attacks
        if atk.attack_type == "undercutting"
    }
    denied = [
        a.conclusion for a in globex_args
        if labels[a.id] is not Label.IN and a.id in undercut_targets
    ]
    assert not denied, (
        f"{kb_path}: globex conclusions denied by an acme-only exclusion: "
        f"{denied}"
    )
