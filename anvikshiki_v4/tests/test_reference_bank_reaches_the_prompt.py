"""The model building a rule is shown the whole reference bank (#105).

Stage D listed `sorted(reference_bank)[:30]` under a field named
`reference_bank`, so the 31st source of any base disappeared from the prompt
with nothing saying the list was partial, and the ones lost were whichever
sorted last. The shipped banks hold 29, 25 and 30 entries, so nonfiction sat
exactly at the cap.

These run the real Stage D sub-rule path with the model stubbed, and read the
argument it actually receives.
"""

import pytest

from anvikshiki_v4.extraction_schema import (
    ExtractionConfig,
    PredicateNode,
    PredicateRelation,
    StageAOutput,
    StageBOutput,
    StageCOutput,
)
from anvikshiki_v4.predicate_extraction import StageDConstructor
from anvikshiki_v4.schema import DomainType, KnowledgeStore


class _Recorder:
    """Records the kwargs of each call. The branch swallows an exception from
    the model with `continue`, so `calls` proves the prompt was really built."""

    def __init__(self):
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return type("Result", (), {"sources": []})()


def _prompted_bank(bank: dict) -> str:
    ks = KnowledgeStore(domain_type=DomainType.CRAFT, reference_bank=bank)
    stage_d = StageDConstructor(ks, ExtractionConfig())
    rec = _Recorder()
    stage_d.constructor = rec
    stage_d(
        stage_a=StageAOutput(candidates=[], chapter_id="ch02"),
        stage_b=StageBOutput(nodes={
            "churn_rising": PredicateNode(
                predicate="churn_rising",
                description="a decomposed predicate",
                parent="unit_economics_negative",
                relation_to_parent=PredicateRelation.COMPOSES,
                depth=1,
            )
        }),
        stage_c=StageCOutput(vocabulary=["churn_rising"]),
        guide_text={"ch02": "chapter text"},
    )
    assert len(rec.calls) == 1, "the sub-rule branch never called the model"
    return rec.calls[0]["reference_bank"]


def _bank(n: int) -> dict:
    return {f"src_{i:03d}": {"title": f"work {i}"} for i in range(n)}


@pytest.mark.parametrize("n", [29, 30, 31, 47])
def test_every_source_id_reaches_the_prompt(n):
    """31 and 47 are the cases the old cap cut; the one sorting last is the
    one it dropped first."""
    shown = _prompted_bank(_bank(n)).split(", ")
    assert shown == sorted(_bank(n)), f"{len(shown)} of {n} ids shown"
    assert f"src_{n - 1:03d}" in shown


def test_an_empty_bank_says_none_rather_than_nothing():
    assert _prompted_bank({}) == "None"


@pytest.mark.parametrize(
    "kb", ["business_expert", "copywriting_expert", "nonfiction_expert"]
)
def test_every_shipped_bank_reaches_the_prompt_whole(kb):
    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

    bank = load_knowledge_store(f"anvikshiki_v4/data/{kb}.yaml").reference_bank
    assert len(bank) >= 20, f"{kb} bank has only {len(bank)} entries"
    assert _prompted_bank(bank).split(", ") == sorted(bank)
