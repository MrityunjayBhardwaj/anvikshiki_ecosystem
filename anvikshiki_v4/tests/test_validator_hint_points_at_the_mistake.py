"""The validator's hint names the valid predicates nearest the mistake (#59).

Grounding feeds rejected predicates back to a model and asks it to fix them
"using ONLY predicates from the ontology". The hint it was handed was
`sorted(known)[:10]` after the word `valid:` — the ten names nearest the start
of the alphabet, 10 of 34, with nothing saying so. Now it is the names that
share the most words with what was written, never one that says the opposite,
and always with the size of the vocabulary beside it.
"""

import pytest

from anvikshiki_v4.datalog_engine import HINT_SIZE, nearest_known
from anvikshiki_v4.grounding import build_grounding_solver, ontology_vocabulary
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

KBS = ["business_expert", "copywriting_expert", "nonfiction_expert"]


@pytest.fixture(scope="module", params=KBS)
def base(request):
    ks = load_knowledge_store(f"anvikshiki_v4/data/{request.param}.yaml")
    return ks, build_grounding_solver(ks)


def _hint(engine, pred):
    errors = engine.validate_predicates([f"{pred}(acme)"])
    assert len(errors) == 1, errors
    return errors[0]


def _multiword(ks):
    return sorted(
        n for n in ontology_vocabulary(ks).permitted
        if not n.startswith("not_") and len(n.split("_")) >= 2
    )


# ── on the shipped bases ──────────────────────────────────────

def test_the_hint_states_the_whole_vocabulary_size(base):
    ks, engine = base
    total = len(ontology_vocabulary(ks).permitted)
    assert total > HINT_SIZE, "too small a vocabulary to test a short list"
    probe = _multiword(ks)[-1] + "_signal"
    assert f"of {total}, by shared words" in _hint(engine, probe)


def test_a_reordered_valid_name_is_offered_itself_first(base):
    """Quantified over every multi-word name, so the names sorting last are
    tested as hard as the first — the old hint could only ever offer the
    first ten."""
    ks, engine = base
    names = _multiword(ks)
    assert len(names) >= 20, f"only {len(names)} multi-word names"
    for name in names:
        reordered = "_".join(reversed(name.split("_")))
        if reordered in ontology_vocabulary(ks).permitted:
            continue
        assert nearest_known(reordered, engine.extra_vocabulary)[0] == name


def test_every_name_offered_is_one_the_validator_accepts(base):
    """A hint that offered a rejected name would send the repair loop round
    again on the hint's own mistake."""
    ks, engine = base
    offered = 0
    for name in _multiword(ks):
        for probe in (name + "_signal", "not_" + name + "_signal"):
            for suggestion in nearest_known(probe, engine.extra_vocabulary):
                offered += 1
                assert engine.validate_predicates([f"{suggestion}(acme)"]) == [], (
                    probe, suggestion)
    assert offered > 50, f"only {offered} suggestions examined"


# ── behaviour pinned on the business base ─────────────────────

@pytest.fixture(scope="module")
def business():
    ks = load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")
    return build_grounding_solver(ks)


def test_the_opposite_claim_is_never_offered():
    """`negative_unit_economics` shares two of three words with what was
    written, and is the opposite of it. No shipped vocabulary holds an
    opposed pair today, so this is a fixture: on the real bases the veto had
    nothing to refuse and a test there could not fail."""
    known = {"positive_unit_economics", "negative_unit_economics", "churn_rising"}
    near = nearest_known("unit_economics_positive", known)
    assert near == ["positive_unit_economics"]
    # The control: without the polarity word, both sides are fair to offer.
    assert sorted(nearest_known("unit_economics", known)) == [
        "negative_unit_economics", "positive_unit_economics"]


def test_a_domain_antonym_is_never_offered():
    """retention/churn is one of the domain antonym pairs, not a polarity word."""
    near = nearest_known("high_retention_rate", {"high_churn_rate", "retention_rate"})
    assert near == ["retention_rate"]


def test_the_positive_case_still_works_on_the_real_base(business):
    near = nearest_known("unit_economics_positive", business.extra_vocabulary)
    assert near[0] == "positive_unit_economics"


def test_a_negated_mistake_is_offered_negated_names(business):
    near = nearest_known("not_unit_economics_positive", business.extra_vocabulary)
    assert near and near[0] == "not_positive_unit_economics"
    assert all(n.startswith("not_") for n in near)


def test_no_shared_word_says_so_with_the_count(business):
    hint = _hint(business, "shareholder_delight")
    assert "no valid name shares a word with it" in hint
    assert f"({len(business.extra_vocabulary)} valid names exist)" in hint


def test_the_list_is_short_and_says_it_is(business):
    """`market` is in five names and `value` in three: eight candidates, so the
    hint must stop at HINT_SIZE and say how many it shows."""
    hint = _hint(business, "market_value")
    assert f"({HINT_SIZE} of {len(business.extra_vocabulary)}," in hint


def test_the_old_alphabetical_list_is_gone(business):
    """The first name alphabetically shares nothing with this mistake."""
    first = sorted(business.extra_vocabulary)[0]
    assert first not in _hint(business, "unit_economics_positive")
