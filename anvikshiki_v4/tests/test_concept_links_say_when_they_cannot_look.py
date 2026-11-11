"""Concept links say when there was nothing to look for (#126).

Every shipped base keys its dependency graph by opaque id (`C01`), and the
guides never write those ids, so the old matcher searched prose for a token
that cannot occur and returned [] for every passage — which reads as "this
passage names no concept". Now a base with no concept names yields None
("not searched") and a warning; a base keyed by phrases is searched for them.
"""

import logging

import pytest

from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store
from anvikshiki_v4.t3_compiler import compile_t3

PROSE = {
    "ch02": (
        "Unit economics decide whether growth helps. As V1 says, value "
        "creation needs positive margins. Pricing power is a separate matter."
    )
}


@pytest.fixture(scope="module")
def business():
    return load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")


def _with_graph(ks, graph):
    """The real base with only its dependency graph replaced, so no other
    required field is pinned by hand here (#47)."""
    return ks.model_copy(update={"dependency_graph": graph})


def _anchors(ks):
    _, chunks = compile_t3(PROSE, ks)
    assert len(chunks) == 1
    return chunks[0].concept_anchors


def test_opaque_ids_are_not_searched_and_say_so(business, caplog):
    ks = _with_graph(business, {"C01": ["C02"]})
    with caplog.at_level(logging.WARNING, logger="anvikshiki_v4.t3_compiler"):
        assert _anchors(ks) is None
    assert "2 of 2 concepts have only an id" in caplog.text


def test_named_concepts_are_searched_as_phrases(business, caplog):
    ks = _with_graph(business, {"unit_economics": ["pricing_power"]})
    with caplog.at_level(logging.WARNING, logger="anvikshiki_v4.t3_compiler"):
        assert sorted(_anchors(ks)) == ["pricing_power", "unit_economics"]
    assert "only an id" not in caplog.text


def test_a_named_concept_absent_from_the_passage_is_an_empty_list(business):
    """[] now means searched and not found, distinct from None."""
    ks = _with_graph(business, {"capital_allocation": ["moat_depth"]})
    assert _anchors(ks) == []


def test_one_word_of_a_concept_name_is_not_the_concept(business):
    ks = _with_graph(business, {"unit_cost_curve": []})
    assert _anchors(ks) == []


def test_concepts_that_appear_only_as_dependents_are_searched(business):
    """The old matcher walked keys only; `pricing_power` here is a value."""
    ks = _with_graph(business, {"moat_depth": ["pricing_power"]})
    assert _anchors(ks) == ["pricing_power"]


def test_rule_ids_in_the_graph_are_not_concepts(business, caplog):
    """The graph carries rule chains too (V01 → V08). With the prose citing V1,
    a rule id must not come back as a concept link, nor count as unnamed."""
    ks = _with_graph(business, {"V01": ["V08"], "unit_economics": []})
    with caplog.at_level(logging.WARNING, logger="anvikshiki_v4.t3_compiler"):
        assert _anchors(ks) == ["unit_economics"]
    assert "only an id" not in caplog.text


@pytest.mark.parametrize(
    "kb", ["business_expert", "copywriting_expert", "nonfiction_expert"]
)
def test_no_shipped_base_names_its_concepts_and_the_compiler_says_so(kb, caplog):
    """The real state today, pinned so it is seen: if a base gains concept
    names this fails, and the test should then assert real links instead."""
    ks = load_knowledge_store(f"anvikshiki_v4/data/{kb}.yaml")
    assert ks.dependency_graph, "base lost its dependency graph"
    with caplog.at_level(logging.WARNING, logger="anvikshiki_v4.t3_compiler"):
        assert _anchors(ks) is None
    assert "concepts have only an id" in caplog.text
