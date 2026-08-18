# tests/test_rules_fire_on_grounded_predicates.py
"""Rules must fire on the predicates the grounder actually produces.

They did not. The grounder emits `pricing_power(company)`; a knowledge base
declares `pricing_power`; and `_derive_rule_arguments` compared the two as
strings. Every rule in every base was skipped, so no vyāpti had ever fired on
the real query path and every argument the engine returned was a
self-supporting asserted fact.

Nothing caught it because every existing test fed `compile_t2` bare predicate
names — a format no production caller produces. The fixtures and the real
grounder had drifted apart and nothing compared them, so the compiler was
thoroughly tested on input it never receives. The first law below is the one
that would have failed.

`Vyapti`'s own docstring specifies the semantics being restored here:

    consequent(Entity) :- antecedent1(Entity), antecedent2(Entity), ...

One Entity variable, shared by the whole rule. `datalog_engine` already
reasons this way; this is the ASPIC+ compiler agreeing with it.
"""

import pytest

from anvikshiki_v4.predicate_contrariness import (
    predicate_entity,
    predicate_name,
    with_entity,
)
from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store

KB = "anvikshiki_v4/data/business_expert.yaml"


def facts(*predicates):
    return [{"predicate": p, "sources": []} for p in predicates]


def rule_args(af):
    return [a for a in af.arguments.values() if a.top_rule]


@pytest.fixture(scope="module")
def ks():
    return load_knowledge_store(KB)


# ── The law that was missing ────────────────────────────────────────────────

def test_a_rule_fires_on_a_predicate_carrying_an_entity(ks):
    """The regression proper: the grounder's format must reach the rules.

    If this fails, the engine is answering every query without consulting its
    knowledge base, and nothing else in the suite will say so.
    """
    af = compile_t2(ks, facts("superior_information(firm)"))
    derived = rule_args(af)

    assert derived, (
        "V03 did not fire on `superior_information(firm)`. The knowledge base "
        "is not being consulted on the real query path."
    )
    assert [a.top_rule for a in derived] == ["V03"]


def test_every_rule_in_the_shipped_kb_fires_on_grounded_predicates(ks):
    """Not one rule, all of them — and the denominator is asserted.

    A version of this that silently matched zero rules would pass while
    proving nothing, so the count of rules actually exercised is checked too.
    """
    testable = [(vid, v) for vid, v in ks.vyaptis.items() if v.antecedents]
    assert len(testable) == 11, (
        f"expected 11 rules with antecedents in the shipped KB, found "
        f"{len(testable)} — update this law rather than weakening it"
    )

    fired = [
        vid for vid, v in testable
        if any(
            a.top_rule == vid
            for a in compile_t2(
                ks, facts(*(f"{ant}(acme)" for ant in v.antecedents))
            ).arguments.values()
        )
    ]
    assert len(fired) == len(testable), (
        f"only {len(fired)} / {len(testable)} rules fired: "
        f"missing {sorted(set(v for v, _ in testable) - set(fired))}"
    )


def test_the_conclusion_is_about_the_entity_it_reasoned_over(ks):
    """Firing is not enough — the rule must say which firm it decided about.

    Stripping the entity to make the match succeed would let every rule fire
    and quietly lose the subject, which is a smaller copy of the same defect.
    """
    af = compile_t2(ks, facts("superior_information(firm)"))
    derived = rule_args(af)

    assert [a.conclusion for a in derived] == ["pricing_power(firm)"]


def test_the_entity_survives_a_multi_step_derivation(ks):
    """V01 and V02 feed V08. The binding has to hold across all three."""
    af = compile_t2(ks, facts(
        "positive_unit_economics(acme)",
        "binding_constraint_identified(acme)",
    ))
    by_rule = {a.top_rule: a for a in rule_args(af)}

    assert set(by_rule) == {"V01", "V02", "V08"}
    assert by_rule["V08"].conclusion == "long_term_value(acme)"
    assert by_rule["V08"].tag.derivation_depth == 2


# ── Strictness: one Entity variable, not several ────────────────────────────

def test_antecedents_bound_to_different_entities_do_not_fire(ks):
    """V08 needs both antecedents about the SAME entity.

    Two true facts about two different companies do not license a conclusion
    about either. Failing to fire is the conservative direction: the
    alternative is a confident claim attached to the wrong subject.
    """
    af = compile_t2(ks, facts(
        "value_creation(acme)",
        "resource_allocation_effective(globex)",
    ))
    assert [a.top_rule for a in rule_args(af)] == []


def test_the_same_rule_fires_once_per_entity(ks):
    """Two companies, two conclusions, each about its own subject."""
    af = compile_t2(ks, facts(
        "superior_information(acme)",
        "superior_information(globex)",
    ))
    derived = rule_args(af)

    assert all(a.top_rule == "V03" for a in derived)
    assert sorted(a.conclusion for a in derived) == [
        "pricing_power(acme)", "pricing_power(globex)"
    ]


def test_a_bare_predicate_is_a_binding_and_still_matches(ks):
    """Bare names are how every KB fixture is written; they must keep working.

    `None` is a binding in its own right, not a missing value.
    """
    af = compile_t2(ks, facts("superior_information"))
    derived = rule_args(af)

    assert [a.conclusion for a in derived] == ["pricing_power"]


def test_a_bare_fact_does_not_satisfy_an_entity_bound_rule(ks):
    """The two forms are different bindings and must not cross-match."""
    af = compile_t2(ks, facts(
        "value_creation(acme)",
        "resource_allocation_effective",
    ))
    assert [a.top_rule for a in rule_args(af)] == []


# ── Things that must not have changed ───────────────────────────────────────

def test_an_antecedentless_rule_still_fires_exactly_once(ks):
    """It is about nothing in particular, so it carries no binding."""
    kb = load_knowledge_store(KB)
    vid, v = next(iter(kb.vyaptis.items()))
    v.antecedents = []

    af = compile_t2(kb, facts())
    fired = [a for a in af.arguments.values() if a.top_rule == vid]

    assert len(fired) == 1
    assert fired[0].conclusion == v.consequent
    assert fired[0].tag.derivation_depth == 1


def test_compilation_is_reproducible(ks):
    """Argument ids are handed out in iteration order, and entities arrive in
    a set — so an unsorted loop would renumber the framework between runs on
    identical input. The decision sheet was irreproducible for exactly this.
    """
    given = facts(
        "superior_information(zeta)",
        "superior_information(alpha)",
        "positive_unit_economics(mid)",
    )
    runs = [
        sorted(
            (a.id, a.top_rule, a.conclusion)
            for a in compile_t2(ks, given).arguments.values()
        )
        for _ in range(3)
    ]
    assert runs[0] == runs[1] == runs[2]


# ── The parsing pair ────────────────────────────────────────────────────────

@pytest.mark.parametrize("pred,name,entity", [
    ("holds(acme)", "holds", "acme"),
    ("holds", "holds", None),
    ("not_value_creation(acme)", "not_value_creation", "acme"),
    ("not_value_creation", "not_value_creation", None),
])
def test_a_predicate_splits_into_a_name_and_a_binding(pred, name, entity):
    assert predicate_name(pred) == name
    assert predicate_entity(pred) == entity
    assert with_entity(name, entity) == pred


@pytest.mark.parametrize("kb", [
    "anvikshiki_v4/data/business_expert.yaml",
    "anvikshiki_v4/data/sample_architecture.yaml",
])
def test_knowledge_bases_declare_bare_predicate_names(kb):
    """The binding is supplied by the query, never written into the rule.

    `with_entity` assumes the consequent it is given is a bare name. Handed a
    consequent that already carries one it would produce `pricing_power(x)(f)`
    — a predicate nothing can ever match, so the rule would fire and conclude
    something unreachable rather than fail visibly.

    No shipped base does this today. Asserted so that a base which starts
    doing so breaks a law here rather than silently producing dead
    conclusions, and with the rule set checked non-empty so the scan cannot
    pass by reading nothing.
    """
    store = load_knowledge_store(kb)
    assert store.vyaptis, f"{kb} declares no rules — this law read nothing"

    offenders = [
        (vid, p)
        for vid, v in store.vyaptis.items()
        for p in [v.consequent, *v.antecedents, *v.scope_exclusions]
        if "(" in p
    ]
    assert not offenders, (
        f"{kb} writes a binding into the rule itself: {offenders}. "
        "Entities come from the query; see #81."
    )


def test_scope_exclusions_are_still_entity_blind(ks):
    """Pins a blind spot this change *activates*, so it fails when closed.

    The exclusion block returns early when no argument uses the rule, so
    before rules fired it was unreachable and had never been evaluated. Now
    that they fire, it triggers on any entity and undercuts every entity:
    `perfectly_commoditized_market(acme)` denies globex's conclusion too.

    Filed as #83. Asserted rather than left implicit because a fix that makes
    dead code live owes an account of what it turned on — and this documents
    the wrong behaviour so that correcting it breaks a law rather than
    silently changing output.
    """
    af = compile_t2(ks, facts(
        "superior_information(acme)",
        "superior_information(globex)",
        "perfectly_commoditized_market(acme)",
    ))
    undercut = {
        af.arguments[atk.target].conclusion
        for atk in af.attacks
        if af.arguments[atk.attacker].conclusion.startswith("inapplicable_")
    }

    assert undercut == {"pricing_power(acme)", "pricing_power(globex)"}, (
        "expected the known entity-blind behaviour of #83; if globex is no "
        "longer undercut, #83 is fixed and this law should be replaced by one "
        "asserting only acme is"
    )


def test_a_malformed_predicate_reads_as_a_bare_name():
    """`holds(` has no closing paren. Reading a broken string as an entity
    would invent a binding nothing else can share, which silently stops the
    predicate matching anything at all.
    """
    assert predicate_entity("holds(") is None
    assert predicate_name("holds(") == "holds"
