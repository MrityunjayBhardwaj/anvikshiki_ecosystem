"""A name with nothing usable in it is dropped and counted, never renamed (#302).

`_enforce_snake_case` answered `"unknown_predicate"` for '', '!!!' or 'ä'.
The placeholder is valid snake case, so each caller's "is this usable?" check
passed it, and it showed up in three places:

- Stage A kept it as a candidate, and every junk name from every section merged
  into one predicate that looked like the guide supported it many times over.
- Stage B's "model gave no parent, use the rule's first antecedent" fallback
  never ran: the empty parent became `unknown_predicate`, and children hung off
  a parent node nobody named.
- KB augmentation built rules with `unknown_predicate` as a condition, and its
  `if not consequent` check could not fire.

Each test below goes through the real stage with a stubbed model.
"""

from types import SimpleNamespace

import pytest

from anvikshiki_v4.extraction_schema import (
    ExtractionConfig,
    StageAOutput,
)
from anvikshiki_v4.kb_augmentation import AugmentationPipeline
from anvikshiki_v4.predicate_extraction import (
    StageAExtractor,
    StageBDecomposer,
    _enforce_snake_case,
    _normalize_predicate_name,
)
from anvikshiki_v4.schema import DomainType, KnowledgeStore
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

UNUSABLE = ["", "   ", "!!!", "ä", "1st_mover"]

SECTION = (
    "### Unit economics\n"
    "Growth hides waste when the cost to acquire a customer rises faster than "
    "the value that customer returns, and the firm keeps spending to grow. "
    "This section runs past twenty words so the extractor makes a call."
)


@pytest.mark.parametrize("name", UNUSABLE)
def test_nothing_usable_normalises_to_empty(name):
    assert _normalize_predicate_name(name) == ""
    assert "unknown" not in _enforce_snake_case(name)


def test_a_usable_name_still_normalises():
    """The control: the change only touches names with nothing in them."""
    assert _normalize_predicate_name("Good Name!") == "good_name"
    assert _enforce_snake_case("LtvExceedsCac") == "ltv_exceeds_cac"


def _stage_a(names, sections=2):
    stage = StageAExtractor(
        KnowledgeStore(domain_type=DomainType.CRAFT), ExtractionConfig()
    )
    calls = []

    def model(**kwargs):
        calls.append(1)
        n = len(names)
        return SimpleNamespace(
            predicates=list(names), descriptions=["d"] * n,
            claim_types=["causal"] * n, related_vyaptis=["none"] * n,
            quotes=[""] * n,
        )

    stage.extractor = model
    out = stage(chapter_text="\n\n".join([SECTION] * sections), chapter_id="ch02")
    assert len(calls) == sections, "the stub was not the model Stage A called"
    return out


def test_stage_a_drops_junk_names_and_counts_each_one():
    out = _stage_a(["cac_rising", *UNUSABLE])
    assert [c.name for c in out.candidates] == ["cac_rising", "cac_rising"]
    assert out.unusable_name_count == 2 * len(UNUSABLE)
    assert len(out.unusable_names) == out.unusable_name_count
    assert out.unusable_names[0].startswith("section 0: ")
    assert "'!!!'" in " ".join(out.unusable_names)


def test_stage_a_counts_zero_when_every_name_is_usable():
    """Zero is a measurement here, not silence: it is 0, not None."""
    out = _stage_a(["cac_rising", "firm_spends"])
    assert out.unusable_name_count == 0
    assert out.unusable_names == []


def test_a_record_written_before_the_count_reads_as_not_measured():
    assert StageAOutput.model_validate({}).unusable_name_count is None


def test_stage_b_falls_back_to_the_rule_when_the_model_names_no_parent():
    ks = load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")

    def decomposer(**kwargs):
        return SimpleNamespace(
            sub_predicates=["part_a"], sub_descriptions=["a"],
            parent_predicate="", relation_type="composes",
        )

    stage = StageBDecomposer(ks, ExtractionConfig())
    stage.decomposer = decomposer
    out = stage(
        stage_a=StageAOutput(),
        guide_text={cid: "Guide text." for cid in ks.chapter_fingerprints},
    )
    assert out.decomposition_count >= 5
    assert "unknown_predicate" not in out.nodes
    rule_names = {
        n for v in ks.vyaptis.values() for n in [*v.antecedents, v.consequent]
    }
    parents = {node.parent for node in out.nodes.values() if node.depth == 1}
    assert parents and parents <= rule_names, parents - rule_names


def _augment(antecedents, consequent):
    ks = load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")
    pipe = AugmentationPipeline(ks)
    generation = SimpleNamespace(
        vyapti_names=["Generated rule"],
        vyapti_statements=["Something leads to something."],
        antecedents_list=[antecedents],
        consequents=[consequent],
        causal_statuses=["empirical"],
        scope_conditions_list=[""],
        confidence_existences=[0.6],
        base_vyaptis_used=[""],
    )
    return pipe._parse_and_validate(generation, "q", [])


def test_augmentation_builds_a_rule_from_usable_names():
    """The control: the stub does reach a built rule."""
    rules, _ = _augment("market_growth, low_margin", "value_destruction")
    assert [r.antecedents for r in rules] == [["market_growth", "low_margin"]]


def test_augmentation_refuses_a_rule_with_an_unusable_condition():
    rules, warnings = _augment("market_growth, !!!", "value_destruction")
    assert rules == []
    assert any("unusable antecedent" in w and "'!!!'" in w for w in warnings)


def test_augmentation_refuses_a_rule_with_an_unusable_conclusion():
    rules, warnings = _augment("market_growth", "???")
    assert rules == []
    assert any("no consequent" in w for w in warnings)


def test_the_extraction_reward_does_not_count_an_empty_name_as_snake_case():
    """`_enforce_snake_case("") == ""` now holds, so the reward's "every name
    is already snake case" check must not read an empty name as passing.
    Before #302 it failed because "" became the placeholder."""
    from anvikshiki_v4.predicate_extraction import _extraction_reward

    def score(names):
        return _extraction_reward(
            {"existing_predicates": ""},
            SimpleNamespace(predicates=names, descriptions=["d"] * len(names)),
        )

    assert score(["cac_rising", ""]) == pytest.approx(score(["cac_rising", "Bad Name"]))
    assert score(["cac_rising", "firm_spends"]) - score(["cac_rising", ""]) == pytest.approx(0.2)
