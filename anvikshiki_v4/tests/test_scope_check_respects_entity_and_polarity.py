# tests/test_scope_check_respects_entity_and_polarity.py
"""A query that denies a rule's exclusion is not a query that triggers it.

`GroundingPipeline._check_scope` decided whether a candidate predicate matched
a rule's `scope_exclusions` with a lowercase substring test:

    if any(excl.lower() in p.lower() for p in predicates):

`"subsidized_entity" in "not_subsidized_entity(acme)"` is True, so a query
stating that the exclusion does **not** hold produced exactly the warning a
query stating that it does would. The warning inverted the query's meaning.
Observed against the shipped base, where V01 excludes `subsidized_entity`:

    subsidized_entity(acme)         1 warning
    not_subsidized_entity(acme)     1 warning     <- denial, warned identically
    subsidized_entity(globex)       1 warning     <- whose exclusion? unsaid

The second half is the entity-blindness already corrected in the compiler for
this same field: the warning named the rule and the exclusion but never the
entity the exclusion was observed of, so two excluded firms collapsed into one
indistinguishable line.

Why the compiler was already right
──────────────────────────────────
`t2_compiler_v4` matches with `predicate_name(conclusion) == predicate_name(
excl)`, which separates `not_subsidized_entity` from `subsidized_entity` for
free, and binds the resulting undercut to the entity. Two components in one
package held two ideas of what it means for an exclusion to apply. They now
share the helpers rather than each carrying its own test, and the agreement is
pinned below rather than left to inspection.

A bare exclusion fact binds to `None`, which is a binding in its own right, so
a knowledge base written entirely in bare names behaves exactly as before.

This check could not fire at all before the grounder was given the exclusion
vocabulary — the model was never permitted to emit one of these names. That is
why the defect survived: it was correct-looking dead code, and fixing the
vocabulary is precisely what switches it on.
"""

import pytest

from anvikshiki_v4.grounding import GroundingPipeline
from anvikshiki_v4.predicate_contrariness import predicate_name
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

KB_PATH = "anvikshiki_v4/data/business_expert.yaml"


@pytest.fixture(scope="module")
def ks():
    return load_knowledge_store(KB_PATH)


@pytest.fixture(scope="module")
def checker(ks):
    """A pipeline with only the field `_check_scope` reads.

    `GroundingPipeline.__init__` constructs DSPy modules and would need an LM
    configured; the deterministic checks depend on nothing but the store.
    """
    gp = GroundingPipeline.__new__(GroundingPipeline)
    gp.ks = ks
    return gp


@pytest.fixture(scope="module")
def an_exclusion(ks):
    """A (vyapti id, exclusion name) pair actually present in the shipped base.

    Read from the data rather than hardcoded, so the test follows the base if
    its rules are re-authored instead of silently testing a name that no longer
    exists.
    """
    for vid, v in sorted(ks.vyaptis.items()):
        for excl in v.scope_exclusions:
            return vid, predicate_name(excl)
    pytest.fail("the shipped base declares no scope exclusions to test with")


def test_the_shipped_base_declares_exclusions_to_check(ks):
    """The denominator. Every law below is vacuous on a base with none."""
    declared = {e for v in ks.vyaptis.values() for e in v.scope_exclusions}
    assert len(declared) > 0, (
        "no scope exclusions in the shipped base — every scope law below "
        "would pass by matching nothing"
    )


def test_asserting_the_exclusion_warns(checker, an_exclusion):
    vid, excl = an_exclusion
    warnings = checker._check_scope([f"{excl}(acme)"])
    assert len(warnings) == 1
    assert vid in warnings[0].message


def test_denying_the_exclusion_does_not_warn(checker, an_exclusion):
    """The headline. `not_X` is a different predicate, not a match on X."""
    _, excl = an_exclusion
    assert checker._check_scope([f"not_{excl}(acme)"]) == []


def test_the_warning_names_the_entity_it_was_observed_of(checker, an_exclusion):
    _, excl = an_exclusion
    (warning,) = checker._check_scope([f"{excl}(globex)"])
    assert "globex" in warning.message, (
        "an exclusion is scoped to the entity it was observed of; a warning "
        "that does not name the entity cannot be acted on"
    )


def test_each_excluded_entity_warns_once(checker, an_exclusion):
    """Two excluded firms are two findings, not one.

    The pre-fix `any(...)` collapsed the whole candidate list into a single
    boolean, so a second excluded entity was invisible.
    """
    _, excl = an_exclusion
    warnings = checker._check_scope([f"{excl}(acme)", f"{excl}(globex)"])
    assert len(warnings) == 2
    assert any("acme" in w.message for w in warnings)
    assert any("globex" in w.message for w in warnings)


def test_a_bare_exclusion_fact_still_warns(checker, an_exclusion):
    """`None` is a binding, not a missing value — bases written in bare names
    behaved this way before the entity work and must keep behaving so."""
    _, excl = an_exclusion
    assert len(checker._check_scope([excl])) == 1


def test_an_unrelated_predicate_does_not_warn(checker, ks):
    antecedents = sorted(
        {a for v in ks.vyaptis.values() for a in v.antecedents}
    )
    exclusions = {
        predicate_name(e) for v in ks.vyaptis.values()
        for e in v.scope_exclusions
    }
    plain = [a for a in antecedents if predicate_name(a) not in exclusions]
    assert plain, "no antecedent is free of the exclusion vocabulary"
    assert checker._check_scope([f"{plain[0]}(acme)"]) == []


def test_a_longer_name_containing_the_exclusion_does_not_warn(
    checker, an_exclusion
):
    """Substring matching also fired on names that merely embed the exclusion,
    which is a different predicate with a different meaning."""
    _, excl = an_exclusion
    assert checker._check_scope([f"formerly_{excl}(acme)"]) == []


def test_the_scope_check_and_the_compiler_agree_on_what_matches(
    checker, ks, an_exclusion
):
    """One idea of a match, not two.

    The compiler decides an exclusion applies with
    `predicate_name(conclusion) == predicate_name(excl)`. The advisory check
    must select the same candidates, or the engine warns about a rule it does
    not undercut and undercuts a rule it does not warn about.
    """
    _, excl = an_exclusion
    candidates = [
        f"{excl}(acme)",
        f"not_{excl}(acme)",
        f"{excl}(globex)",
        f"formerly_{excl}(acme)",
        excl,
    ]
    compiler_matches = {c for c in candidates if predicate_name(c) == excl}
    check_matches = {
        c for c in candidates if checker._check_scope([c])
    }
    assert check_matches == compiler_matches


def test_substring_matching_is_what_this_replaces(checker, an_exclusion):
    """The mutation check, and it asserts the mutation applied.

    Restoring the old predicate — a lowercase substring test — must make the
    polarity law above fail. A mutation that changes nothing would let this
    file pass for the wrong reason.
    """
    _, excl = an_exclusion
    denial = f"not_{excl}(acme)"

    assert checker._check_scope([denial]) == [], "precondition: fixed behaviour"

    old_predicate = excl.lower() in denial.lower()
    assert old_predicate is True, (
        "the mutation did not apply — the old substring test must match the "
        "denial, or this law is checking nothing"
    )
