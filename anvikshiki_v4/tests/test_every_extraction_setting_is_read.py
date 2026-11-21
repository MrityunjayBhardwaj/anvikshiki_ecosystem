"""Every extraction setting has a reader; the dropped ones are refused (#304).

`ExtractionConfig` held three settings that read as control and that nothing
read: `ensemble_n` (no stage votes), `decomposition_max_depth` (Stage B goes
one level, fixed) and `similarity_threshold` (Stage C has no embeddings; it
groups names on a fixed 0.5 word overlap). `run_pipeline_e2e.py` turned the
first one down "for speed", and got no speed from it. `min_confidence` went
the same way in #63.

So the test is the general one, not three special cases: a setting with no
reader fails here, by name, the day it is added.
"""

import re
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from anvikshiki_v4.extraction_schema import ExtractionConfig, StageAOutput
from anvikshiki_v4.predicate_extraction import StageBDecomposer
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

REPO = Path(__file__).resolve().parents[2]
SCHEMA = "anvikshiki_v4/extraction_schema.py"


def _production_sources() -> dict[str, str]:
    """Tracked Python outside the tests and outside the schema that defines
    the settings: where a setting has to be read for it to do anything."""
    listed = subprocess.run(
        ["git", "ls-files", "*.py"], cwd=REPO, capture_output=True, text=True,
        check=True,
    ).stdout.split()
    return {
        p: (REPO / p).read_text()
        for p in listed
        if p != SCHEMA and "/tests/" not in f"/{p}" and (REPO / p).exists()
    }


def readers(name: str, sources: dict[str, str]) -> list[str]:
    """Files that read `name` as an attribute. Passing it as a keyword is
    setting it, not reading it, which is exactly what the e2e script did."""
    pattern = re.compile(rf"\.{re.escape(name)}\b")
    return sorted(p for p, text in sources.items() if pattern.search(text))


@pytest.fixture(scope="module")
def sources():
    found = _production_sources()
    assert len(found) > 50, f"only {len(found)} files scanned; the scan is blind"
    return found


def test_every_setting_has_a_reader(sources):
    unread = {
        name: readers(name, sources)
        for name in ExtractionConfig.model_fields
        if not readers(name, sources)
    }
    assert not unread, f"settings nothing reads: {sorted(unread)}"
    assert len(ExtractionConfig.model_fields) >= 2  # the loop really ran


def test_the_scan_finds_a_reader_and_misses_a_non_reader(sources):
    """Both answers are reachable. `model_tier` is read in Stage A and in the
    verbatim-rate script; `ensemble_n` was only ever set, never read — the
    e2e script passed it as a keyword, which the scan must not count."""
    assert "anvikshiki_v4/predicate_extraction.py" in readers("model_tier", sources)
    assert readers("ensemble_n", sources) == []
    assert readers("ensemble_n", {"x.py": "Cfg(ensemble_n=1)"}) == []
    assert readers("ensemble_n", {"x.py": "n = cfg.ensemble_n"}) == ["x.py"]


@pytest.mark.parametrize("dropped", [
    "min_confidence", "ensemble_n", "decomposition_max_depth",
    "similarity_threshold",
])
def test_a_dropped_setting_is_refused_not_ignored(dropped):
    with pytest.raises(ValidationError, match=dropped):
        ExtractionConfig(**{dropped: 1})


def test_stage_b_decomposes_exactly_one_level():
    """What `decomposition_max_depth` claimed to govern, observed directly.

    The stub answers every call with children, so a recursive decomposer
    would call again on them. One call per seed rule that has a chapter, and
    every node at depth 0 or 1, is what Stage B actually does.
    """
    ks = load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")
    calls = []

    def decomposer(**kwargs):
        calls.append(kwargs["vyapti_summary"].split(",")[0])
        n = len(calls)
        return SimpleNamespace(
            sub_predicates=[f"part_a_{n}", f"part_b_{n}"],
            sub_descriptions=["a", "b"],
            parent_predicate="",
            relation_type="composes",
        )

    stage = StageBDecomposer(ks, ExtractionConfig())
    stage.decomposer = decomposer
    text = {cid: "Guide text for this chapter." for cid in ks.chapter_fingerprints}
    out = stage(stage_a=StageAOutput(), guide_text=text)

    seeded = [
        vid for vid in ks.vyaptis
        if stage._find_chapter_for_vyapti(vid) in text
    ]
    assert len(seeded) >= 5, f"only {len(seeded)} rules reach Stage B"
    assert len(calls) == len(seeded)
    assert out.decomposition_count == len(seeded)
    assert {node.depth for node in out.nodes.values()} == {0, 1}
