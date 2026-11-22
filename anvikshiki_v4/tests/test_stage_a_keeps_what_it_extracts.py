"""Stage A keeps every candidate it builds; no gate pretends otherwise (#63).

Every candidate was built with `confidence=0.5` and then kept only if
`confidence >= min_confidence`, default 0.3. Both sides were constants, so the
gate never dropped one, and it read as per-candidate quality control in a
pipeline whose problem is that nobody can say how good its output is. The 48
provenance records in saved traces all carry 0.5.

The field, the gate and the setting are gone. What survives is tested here:
Stage A keeps what the model returned, and drops only a name that fails the
snake-case check, or that has no usable characters at all (#302).
"""

import ast
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from anvikshiki_v4.extraction_schema import ExtractionConfig, Provenance
from anvikshiki_v4.predicate_extraction import StageAExtractor
from anvikshiki_v4.schema import DomainType, KnowledgeStore

REPO = Path(__file__).resolve().parents[2]
SAVED = REPO / "traces/instrument_validation/stage_a_ch02.json"

SECTION = (
    "### Unit economics\n"
    "Growth hides waste when the cost to acquire a customer rises faster than "
    "the value that customer returns, and the firm keeps spending to grow. "
    "This section runs past twenty words so the extractor makes a call."
)


class _Model:
    """Answers each section with the same four predicates.

    One verified quote, one paraphrase, one with no quote, and one whose name
    starts with a digit, which fails the snake-case check — every quote
    outcome Stage A records, plus the one drop it makes.
    """

    def __init__(self):
        self.calls = 0
        self.history = []

    def __call__(self, **kwargs):
        self.calls += 1
        return SimpleNamespace(
            predicates=["cac_rising", "growth_hides_waste", "firm_spends", "1st_mover"],
            descriptions=["d"] * 4,
            claim_types=["causal"] * 4,
            related_vyaptis=["none"] * 4,
            quotes=[
                "the cost to acquire a customer rises faster than the value",
                "growth conceals inefficiency in every firm everywhere",
                "",
                "",
            ],
        )


def _run(sections: int):
    stage = StageAExtractor(
        KnowledgeStore(domain_type=DomainType.CRAFT), ExtractionConfig()
    )
    model = _Model()
    stage.extractor = model
    out = stage(chapter_text="\n\n".join([SECTION] * sections), chapter_id="ch02")
    return out, model


def test_every_named_candidate_the_model_returns_is_kept():
    out, model = _run(sections=3)
    assert model.calls == 3, "the stub was not the model Stage A called"
    names = [c.name for c in out.candidates]
    assert len(names) == 3 * 3, names
    assert names.count("cac_rising") == 3
    # Kept whatever its quote's verdict: a paraphrase is recorded, not dropped.
    assert names.count("growth_hides_waste") == 3
    assert out.unverified_quote_candidates == 3
    assert names.count("firm_spends") == 3
    assert out.quoteless_candidates == 3


def test_the_one_drop_is_a_name_that_fails_the_snake_case_check():
    """The control: Stage A can drop, and does, for that reason only."""
    out, _ = _run(sections=1)
    names = [c.name for c in out.candidates]
    assert names == ["cac_rising", "growth_hides_waste", "firm_spends"]


def test_the_dropped_setting_is_refused_not_ignored():
    with pytest.raises(ValidationError, match="min_confidence"):
        ExtractionConfig(min_confidence=0.3)


def test_a_saved_record_carrying_confidence_still_loads():
    """Old traces hold the key; they must still be readable."""
    legacy = {"chapter_id": "ch02", "paragraph_index": 4,
              "quote": "Growth hides waste.", "confidence": 0.5}
    record = Provenance.model_validate(legacy)
    assert record.quote == "Growth hides waste."
    assert "confidence" not in record.model_dump()


@pytest.mark.skipif(not SAVED.exists(), reason="traces/ is gitignored")
def test_the_real_saved_stage_a_still_loads():
    from anvikshiki_v4.extraction_schema import StageAOutput

    blob = json.loads(SAVED.read_text())
    out = StageAOutput.model_validate(blob.get("stage_a", blob))
    assert out.candidates


def _python_files():
    listed = subprocess.run(
        ["git", "ls-files", "*.py"], cwd=REPO, capture_output=True, text=True,
        check=True,
    ).stdout.split()
    return [REPO / p for p in listed]


def test_no_code_passes_confidence_to_a_provenance():
    """`Provenance` ignores unknown keys so old records load, which means a
    caller passing `confidence=` would be silently ignored. Refuse it here."""
    calls, offenders = 0, []
    for path in _python_files():
        if not path.exists():
            continue
        for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if name != "Provenance":
                continue
            calls += 1
            if any(k.arg == "confidence" for k in node.keywords):
                offenders.append(f"{path.relative_to(REPO)}:{node.lineno}")
    assert calls >= 10, f"only {calls} Provenance(...) calls found; the scan is blind"
    assert offenders == [], f"{offenders} pass a confidence Provenance no longer has"
