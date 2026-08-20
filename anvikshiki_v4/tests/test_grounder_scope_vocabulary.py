# tests/test_grounder_scope_vocabulary.py
"""The prompt may not show the model a predicate and then forbid the word.

`OntologySnippetBuilder` prints each rule's scope conditions and exclusions:

    RULE V03: ...
      IF: superior_information
      THEN: pricing_power
      SCOPE: heterogeneous_quality_market
      EXCLUDES: perfectly_commoditized_market, regulated_disclosure_market

built its valid-name list from antecedents and consequents only, and closed
with "Use ONLY predicate names from the list above." So the model was shown
`perfectly_commoditized_market`, told it is what excludes the rule, and told in
the same prompt that it may not use the word. A model that follows the
instruction correctly can never produce one.

Measured on the shipped base before the fix:

    distinct scope_exclusions declared      14    in the valid list:  0 / 14
    distinct scope_conditions declared       5    in the valid list:  0 / 5
    antecedents + consequents               20    in the valid list: 20 / 20

Nineteen names, not the fourteen the exclusion issue names — the SCOPE: lines
are unusable for exactly the same reason the EXCLUDES: lines are.

Why a labelled section rather than the flat list
────────────────────────────────────────────────
Appending them to ALL VALID PREDICATE NAMES is one line and says the wrong
thing: that these are ordinary findings to report. They are not. A scope
predicate says when a rule does or does not apply, so one asserted without
warrant *suppresses* a rule that should have fired — the failure direction is
silence, which is the hardest kind to notice. The per-rule EXCLUDES: lines
already carry that meaning and a flat list discards it, so the section keeps
the names assertable while keeping what they are for.

Consequence downstream: an exclusion the model can finally emit is what makes
the undercutting attack reachable in the compiler, and what switches on the
advisory scope check — which is why that check's entity and polarity handling
had to be corrected first.
"""

import pytest

from anvikshiki_v4.grounding import OntologySnippetBuilder
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

KB_PATH = "anvikshiki_v4/data/business_expert.yaml"

MAIN_HEADER = "ALL VALID PREDICATE NAMES:"
SCOPE_HEADER = "SCOPE PREDICATES"
FORMAT_HEADER = "OUTPUT FORMAT:"


@pytest.fixture(scope="module")
def ks():
    return load_knowledge_store(KB_PATH)


@pytest.fixture(scope="module")
def snippet(ks):
    return OntologySnippetBuilder().build(ks)


def _bulleted(block: str) -> set[str]:
    return {
        line.strip().lstrip("- ").split("(")[0]
        for line in block.splitlines()
        if line.strip().startswith("- ")
    }


def _main_list(snippet: str) -> set[str]:
    tail = snippet.split(MAIN_HEADER, 1)[1]
    for stop in (SCOPE_HEADER, FORMAT_HEADER):
        tail = tail.split(stop, 1)[0]
    return _bulleted(tail)


def _scope_list(snippet: str) -> set[str]:
    if SCOPE_HEADER not in snippet:
        return set()
    return _bulleted(snippet.split(SCOPE_HEADER, 1)[1].split(FORMAT_HEADER, 1)[0])


def _declared(ks, field: str) -> set[str]:
    return {n for v in ks.vyaptis.values() for n in getattr(v, field)}


def test_the_base_declares_scope_vocabulary_to_test_with(ks):
    """The denominator, asserted per field.

    A base with no exclusions, or no conditions, would let every law below
    pass by matching nothing — and these are two independent fields, so one
    being populated says nothing about the other.
    """
    assert len(_declared(ks, "scope_exclusions")) > 0
    assert len(_declared(ks, "scope_conditions")) > 0


def test_no_predicate_is_shown_and_then_forbidden(ks, snippet):
    """The headline law, stated as the mechanism rather than as a count.

    Every predicate name the prompt names to the model — as an antecedent, a
    consequent, a scope condition or an exclusion — must appear in one of the
    lists the prompt permits. Any future field printed into this prompt but
    left out of the vocabulary fails here without anyone remembering to add a
    test for it.
    """
    shown = set()
    for v in ks.vyaptis.values():
        shown.update(v.antecedents)
        if v.consequent:
            shown.add(v.consequent)
        shown.update(v.scope_conditions)
        shown.update(v.scope_exclusions)

    permitted = _main_list(snippet) | _scope_list(snippet)
    assert shown, "no predicates shown at all — the law would be vacuous"
    assert shown - permitted == set(), (
        "the prompt names these predicates and does not permit them: "
        f"{sorted(shown - permitted)}"
    )


def test_every_exclusion_is_permitted(ks, snippet):
    exclusions = _declared(ks, "scope_exclusions")
    permitted = _main_list(snippet) | _scope_list(snippet)
    assert exclusions <= permitted


def test_every_scope_condition_is_permitted(ks, snippet):
    """The half the exclusion issue does not name. SCOPE: lines were
    unusable for exactly the same reason EXCLUDES: lines were."""
    conditions = _declared(ks, "scope_conditions")
    permitted = _main_list(snippet) | _scope_list(snippet)
    assert conditions <= permitted


def test_scope_predicates_are_labelled_not_folded_into_the_flat_list(
    ks, snippet
):
    """The decision, pinned. A regression to the one-line fix — appending
    them to the main list — tells the model these are findings to volunteer,
    and fails here."""
    scope_only = (
        _declared(ks, "scope_exclusions") | _declared(ks, "scope_conditions")
    ) - _main_list(snippet)
    assert scope_only, "precondition: some scope names are not antecedents"
    assert scope_only <= _scope_list(snippet)
    assert SCOPE_HEADER in snippet


def test_the_section_says_what_the_names_are_for(snippet):
    """A labelled section whose label carries no instruction is a flat list
    with a heading."""
    assert SCOPE_HEADER in snippet, "no labelled section to carry an instruction"
    section = snippet.split(SCOPE_HEADER, 1)[1].split(FORMAT_HEADER, 1)[0]
    assert "ONLY if the query itself states" in section
    assert "suppress" in section


def test_the_closing_instruction_admits_both_lists(snippet):
    """"Use ONLY predicate names from the list above" is the sentence that
    made the prompt self-contradicting. Adding a second list without amending
    it would leave the contradiction in place in a subtler form."""
    assert "from the lists above" in snippet
    assert "from the list above" not in snippet


def test_a_name_is_not_listed_in_both_places(ks, snippet):
    """A predicate that is both an antecedent and an exclusion is already
    assertable; listing it twice would say two different things about one
    word."""
    assert _main_list(snippet) & _scope_list(snippet) == set()


def test_a_base_without_scope_vocabulary_gets_no_empty_section(ks):
    """The section is conditional, so a base declaring none does not get a
    header introducing nothing."""
    bare = ks.model_copy(deep=True)
    for v in bare.vyaptis.values():
        v.scope_conditions = []
        v.scope_exclusions = []
    snippet = OntologySnippetBuilder().build(bare)
    assert SCOPE_HEADER not in snippet
    assert _main_list(snippet), "the main list must survive the copy"


def test_relevant_vyaptis_narrows_the_scope_section_too(ks):
    """The snippet can be built for a subset of rules. The scope section must
    narrow with it, or a filtered prompt permits vocabulary from rules it does
    not show."""
    vid = next(
        v_id for v_id, v in sorted(ks.vyaptis.items()) if v.scope_exclusions
    )
    snippet = OntologySnippetBuilder().build(ks, relevant_vyaptis=[vid])
    permitted = _main_list(snippet) | _scope_list(snippet)
    other = {
        e
        for v_id, v in ks.vyaptis.items()
        if v_id != vid
        for e in v.scope_exclusions
    }
    only_elsewhere = other - {
        e for e in ks.vyaptis[vid].scope_exclusions
    } - set(ks.vyaptis[vid].antecedents)
    assert only_elsewhere, "precondition: other rules exclude other things"
    assert only_elsewhere & permitted == set()
