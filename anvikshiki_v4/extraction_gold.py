# anvikshiki_v4/extraction_gold.py
"""Loading the hand-authored gold set the evaluation harness measures against.

`tests/fixtures/expected_predicates.yaml` held fourteen gold predicates and a
header claiming `test_predicate_extraction.py` used them for precision and
recall. Nothing loaded it — zero references across all fifty-one non-vendored
Python files. Every precision and recall test in the suite used inline toy
literals like `["a", "b"]`, `ExtractionEvaluator` was instantiated only inside
that test file, and `optimize_pipeline` was never called anywhere. The harness
had never been pointed at real extractor output.

So there was no measurement to trust or distrust. There was no measurement.
This module is what a gold set is loaded through.

On the provenance of the fixture, which decides what may be claimed from it
────────────────────────────────────────────────────────────────────────────
Two observations argue it was hand-authored rather than back-derived from the
knowledge base, which is what a gold set has to be:

  * none of its fourteen names appear in `business_expert.yaml`'s vocabulary
  * none of the fourteen appear literally in the prose they are gold for —
    `imagined_economies_of_scale` labels a passage about false scale
    assumptions, which is a human's conceptual label, not a lifted string

One observation cuts the other way and constrains what the fixture can be used
for. Its own header says the predicates should be extracted from
`guide_ch2_excerpt.md`, and that file is **not** an excerpt of
`guides/business_expert/guide_ch2.md` — 3,776 characters against the real
chapter's 16,211, with none of its substantial paragraphs appearing there. It
is separately written prose authored alongside its own answer key.

Measuring against the excerpt answers "can the extractor find concepts a human
deliberately planted in a short toy", not "how does extraction perform on this
corpus". `GoldSet.authored_for` carries that distinction so a run cannot report
one as the other, and so the two are never averaged together.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

FIXTURES_DIR = Path(__file__).resolve().parent / "tests" / "fixtures"
CHAPTER_2_GOLD = FIXTURES_DIR / "expected_predicates.yaml"


class GoldPredicate(BaseModel):
    """One hand-authored gold predicate."""

    name: str
    description: str = ""
    claim_type: str = ""
    section: str = ""


class GoldVyapti(BaseModel):
    """A relationship Stage D is expected to construct."""

    antecedents: list[str] = Field(default_factory=list)
    consequent: str = ""
    relation: str = ""


class GoldSet(BaseModel):
    """A gold standard for one chapter, and what it may be measured against."""

    chapter_id: str = ""
    authored_for: str = Field(
        default="",
        description=(
            "The text a human read while authoring this gold. Measuring "
            "against any other text is a different experiment and must be "
            "reported as one."
        ),
    )
    predicates: list[GoldPredicate] = Field(default_factory=list)
    existing_related: list[str] = Field(default_factory=list)
    expected_vyaptis: list[GoldVyapti] = Field(default_factory=list)

    @property
    def names(self) -> set[str]:
        return {p.name for p in self.predicates}

    @property
    def descriptions(self) -> dict[str, str]:
        """name → description, for matching on prose rather than on labels."""
        return {p.name: p.description for p in self.predicates if p.description}

    def __len__(self) -> int:
        return len(self.predicates)


def load_gold(path: str | Path = CHAPTER_2_GOLD) -> GoldSet:
    """Load a gold set from YAML.

    Raises rather than returning an empty set when the file is missing. A gold
    set that silently comes back empty gives recall a denominator of zero,
    which reads as a passing score for a measurement that never happened.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"gold set not found: {path}")

    data = yaml.safe_load(path.read_text()) or {}

    gold = GoldSet(
        chapter_id=data.get("chapter_id", ""),
        authored_for=data.get("authored_for", ""),
        predicates=[
            GoldPredicate(**p) for p in data.get("expected_predicates", [])
        ],
        existing_related=data.get("existing_related", []),
        expected_vyaptis=[
            GoldVyapti(**v) for v in data.get("expected_vyaptis", [])
        ],
    )

    if not gold.predicates:
        raise ValueError(
            f"gold set at {path} parsed to zero predicates — an empty gold set "
            f"makes every recall figure meaningless rather than merely wrong"
        )

    return gold
