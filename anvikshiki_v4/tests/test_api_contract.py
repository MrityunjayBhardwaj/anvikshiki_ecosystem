# tests/test_api_contract.py
"""Contract tests between what the engine returns and what the API promises.

Three mismatches shipped at once across this one interface — three missing
fields, an attack type spelled differently on each side, and an uncertainty
entry whose shape disagreed with its declared type. Three is not bad luck; it
is the absence of a test. The frontend parses with a strict schema and the
caller swallowed the exception, so every one of them failed silently.

The frontend's `webapp/lib/types.ts` is read as the single source of truth
rather than restated here, because a contract restated in two places is two
contracts. Parsing TypeScript with regular expressions is crude, so every
extraction asserts it found something plausible — an extractor that silently
returns nothing would make these tests pass by measuring nothing, which is the
same defect they exist to catch.
"""

import re
from pathlib import Path

import dspy
import pytest

from anvikshiki_v4.engine_v4 import AnvikshikiEngineV4
from anvikshiki_v4.grounding import GroundingResult
from anvikshiki_v4.schema_v4 import EpistemicStatus, Label, PramanaType
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

TYPES_TS = Path(__file__).resolve().parents[2] / "webapp" / "lib" / "types.ts"
COMPILER_PY = Path(__file__).resolve().parents[1] / "t2_compiler_v4.py"


# ── Reading the contract ──

def _types_source() -> str:
    if not TYPES_TS.exists():
        pytest.fail(
            f"the API contract lives at {TYPES_TS} and is missing, so engine "
            f"output cannot be checked against it"
        )
    return TYPES_TS.read_text()


def _schema_fields(schema_name: str, minimum: int = 3) -> set[str]:
    """Top-level keys of a `z.object({...})` declaration.

    `minimum` is the caller's floor on a plausible parse — the point is that no
    caller accepts an empty or near-empty extraction as a passing contract.
    """
    src = _types_source()
    match = re.search(
        rf"export const {schema_name} = z\.object\(\{{(.*?)^\}}\);",
        src, re.DOTALL | re.MULTILINE,
    )
    assert match, f"{schema_name} not found in {TYPES_TS.name}"
    body = match.group(1)
    # Keys at the start of a line, ignoring nested object contents.
    fields = set(re.findall(r"^\s{2}(\w+):", body, re.MULTILINE))
    assert len(fields) >= minimum, (
        f"only {len(fields)} fields parsed out of {schema_name} — the "
        f"extraction is broken, not the contract"
    )
    return fields


def _schema_field_types(schema_name: str) -> dict[str, str]:
    """Map each top-level key of a `z.object({...})` to its declaration text.

    Enough to tell `z.number()` from `z.object({...})` without reimplementing
    zod in Python — which is the point, since the declaration is the contract
    and restating it here would create a second one.
    """
    src = _types_source()
    match = re.search(
        rf"export const {schema_name} = z\.object\(\{{(.*?)^\}}\);",
        src, re.DOTALL | re.MULTILINE,
    )
    assert match, f"{schema_name} not found in {TYPES_TS.name}"
    body = match.group(1)
    keys = re.findall(r"^\s{2}(\w+):", body, re.MULTILINE)
    parts = re.split(r"^\s{2}\w+:", body, flags=re.MULTILINE)[1:]
    assert len(keys) == len(parts), f"{schema_name}: key/declaration split disagreed"
    decls = {k: v.strip() for k, v in zip(keys, parts)}
    assert decls, f"{schema_name} parsed as empty"
    return decls


def _ts_enum(name: str) -> set[str]:
    """Values of a `z.enum([...])` declaration."""
    src = _types_source()
    match = re.search(rf"export const {name} = z\.enum\(\[(.*?)\]\);", src, re.DOTALL)
    assert match, f"enum {name} not found in {TYPES_TS.name}"
    values = set(re.findall(r'"([^"]+)"', match.group(1)))
    assert values, f"enum {name} parsed as empty"
    return values


# ── Engine output, produced offline ──

class _MockGrounding:
    def __init__(self, predicates):
        self._predicates = predicates

    def __call__(self, query):
        return GroundingResult(
            predicates=self._predicates, confidence=0.85,
            disputed=[], warnings=[], clarification_needed=False,
        )


def _engine(predicates):
    ks = load_knowledge_store("anvikshiki_v4/data/sample_architecture.yaml")
    engine = AnvikshikiEngineV4(
        knowledge_store=ks, grounding_pipeline=_MockGrounding(predicates)
    )
    engine.synthesizer = lambda **kw: dspy.Prediction(
        response="Contract-test synthesis.", sources_cited=["R01"],
    )
    return engine


@pytest.fixture(scope="module")
def result():
    """A full result, from a query that produces attacks as well as arguments."""
    engine = _engine(["concentrated_ownership", "good_governance"])
    return engine.forward_with_coverage("does ownership shape governance?")


# ── The contract ──

def test_returned_fields_cover_the_api_schema(result):
    """returned_fields ⊇ schema_fields. Anything missing serialises to null."""
    promised = _schema_fields("EngineResultSchema", minimum=13)
    returned = set(result.keys())
    missing = promised - returned
    assert not missing, (
        f"the API promises {sorted(missing)} and the engine never returns them; "
        f"they serialise to null and fail the frontend's parse"
    )


def test_every_return_path_carries_the_argumentation_view():
    """A decline is still a result, and the frontend requires the same fields.

    A path that returns early is exactly where fields get forgotten, so the
    empty-framework paths are asserted rather than assumed.
    """
    promised = _schema_fields("EngineResultSchema", minimum=13)

    class _NeedsClarification:
        def __call__(self, query):
            return GroundingResult(
                predicates=[], confidence=0.1, disputed=[],
                warnings=["ambiguous"], clarification_needed=True,
            )

    engine = _engine(["concentrated_ownership"])
    engine.grounding = _NeedsClarification()
    pred = engine.forward_with_coverage("something ambiguous")

    missing = promised - set(pred.keys())
    assert not missing, f"clarification path omits {sorted(missing)}"
    assert pred.get("arguments") == {}
    assert pred.get("attacks") == []
    assert pred.get("labels") == {}


def test_labels_survives_attribute_access_on_the_prediction(result):
    """dspy.Prediction inherits Example.labels(), which shadows the field.

    `getattr(pred, "labels")` returns the bound method, not the data — silently,
    with no error anywhere. Any consumer reading fields by attribute gets a
    method object where the label map should be, so the accessor is part of
    the contract, not an implementation detail.
    """
    assert callable(getattr(result, "labels")), (
        "dspy no longer shadows this field — the workaround below can go"
    )
    assert isinstance(result.get("labels"), dict)
    assert result.get("labels"), "labels came back empty for a query with arguments"


def test_attack_types_agree_across_the_boundary():
    """Every attack type the compiler can emit must exist in the API enum."""
    promised = _ts_enum("AttackType")
    emitted = set(re.findall(r'attack_type="(\w+)"', COMPILER_PY.read_text()))
    assert emitted, f"no attack_type literals found in {COMPILER_PY.name}"
    unknown = emitted - promised
    assert not unknown, (
        f"the compiler emits {sorted(unknown)}, which the API enum does not "
        f"accept ({sorted(promised)})"
    )


@pytest.mark.parametrize(
    "ts_name,py_enum",
    [
        ("EpistemicStatus", EpistemicStatus),
        ("Label", Label),
        ("PramanaType", PramanaType),
    ],
)
def test_enums_agree_across_the_boundary(ts_name, py_enum):
    """Enum values must match, in both directions."""
    promised = _ts_enum(ts_name)
    if ts_name == "PramanaType":
        emitted = {m.name for m in py_enum}     # serialised by .name
    else:
        emitted = {m.value for m in py_enum}    # serialised by .value
    assert emitted == promised, (
        f"{ts_name}: engine has {sorted(emitted)}, API has {sorted(promised)}"
    )


def test_uncertainty_entry_matches_its_declared_shape(result):
    """Each uncertainty field must have the kind of value the API declares.

    The declaration is read rather than restated, so this kept holding when
    the continuous belief layer went: `total_confidence` left the schema and
    this test needed only its floor updated, not its logic.
    """
    declared = _schema_field_types("UncertaintyEntrySchema")
    assert {"epistemic", "aleatoric", "inference"} <= set(declared)
    assert "total_confidence" not in declared, (
        "the composite is back in the contract — it multiplied three "
        "quantities under weights nobody derived"
    )

    entries = result.get("uncertainty")
    assert entries, "no uncertainty entries produced for a query with conclusions"

    for conc, entry in entries.items():
        for field, decl in declared.items():
            if field not in entry or entry[field] is None:
                continue                       # optional / nullable
            value = entry[field]
            if decl.startswith("z.number()"):
                assert isinstance(value, (int, float)) and not isinstance(value, bool), (
                    f"{conc}.{field} is {type(value).__name__}, declared a number"
                )
            elif decl.startswith("z.object("):
                assert isinstance(value, dict), (
                    f"{conc}.{field} is {type(value).__name__}, declared an object"
                )
