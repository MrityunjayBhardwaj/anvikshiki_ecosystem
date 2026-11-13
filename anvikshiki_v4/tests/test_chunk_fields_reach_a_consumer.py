"""Every field on a TextChunk is written by the compiler and read by something (#129, #134).

A field nobody reads produces no symptom: it is computed correctly, stored
correctly and never consulted, which looks identical to a field that works.
#129 noticed two such anchor fields. Writing the check over every field found
seven, and #134 decided them one by one:

    embedding        dropped — never assigned by any code path, never read
    source_ids       dropped — never assigned, so [] on every chunk
    sourced          dropped — derived from the chapter's decay markers, which
                     no shipped base has, so False on all 130 business chunks;
                     and decay markers say a claim ages, not that it is sourced
    prerequisites,   dropped — copies of chapter-level facts. The chapter node
    difficulty_tier  of the knowledge graph already carries both, keyed by the
                     chunk's `chapter_id`, and so does the chapter fingerprint
    chunk_id         kept — an identifier for diagnostics and tests
    hetvabhasa_anchors,
    concept_anchors  kept — see KNOWN_UNREAD below

Two of the dropped or kept-unread fields were never on #129's list:
`source_ids` and `epistemic_status`. The old scan matched attribute reads by
NAME, and both names are also fields of other models (`Tag.source_ids`,
`Vyapti.epistemic_status`), so reads of those counted as reads of the chunk's.
The scan now treats a shared name as "could not tell" rather than "read", and
every such field carries a verdict that was checked by hand (HAND_CHECKED).

WHAT THIS CHECK STILL CANNOT SEE. Shared names are found from attributes that
other classes in the package declare or assign. An object from outside the
package with a same-named attribute (a dspy prediction's `.text`, say) is not
found, so a passing field can still be dead. It is a lower bound.
"""

import ast
from collections import Counter
from pathlib import Path

import pytest

from anvikshiki_v4.t3_compiler import TextChunk

PACKAGE = Path(__file__).resolve().parents[1]
DEFINING_MODULE = PACKAGE / "t3_compiler.py"

# Fields nothing in the engine reads, each with the reason it is kept anyway.
# Asserted EXACTLY: a new unread field fails, and so does wiring one of these up
# without removing it here.
KNOWN_UNREAD = {
    "chunk_id": "an identifier; read by run_pipeline_e2e.py, scripts/ and tests, "
                "which is what an identifier is for",
    "hetvabhasa_anchors": "accurate since #293, but its consumer is fallacy "
                          "routing after T2 runs, which is not built (#296)",
    "concept_anchors": "None on every shipped base, which names no concepts; "
                       "the matcher works for a base that does (#126)",
    "epistemic_status": "the chapter's weakest authored status; the thesis's "
                        "inheritance from T2 results that would read it is not "
                        "built (#296)",
}

# Chunk fields whose name another class in the package also uses, so a
# name-matched read proves nothing. Each verdict was checked by reading every
# match. Asserted exactly against the scan, so a new collision needs a verdict.
HAND_CHECKED = {
    "chapter_id": ("read", "t3a_retriever.py compares c.chapter_id to the "
                           "boosted chapters in both ranking paths"),
    "epistemic_status": ("unread", "every .epistemic_status read in the package "
                                   "is on a Vyapti or a proposed vyapti"),
    "text": ("read", "t3a_retriever.py indexes chunk.text and engine_v4.py "
                     "passes c.text to synthesis"),
}


def _engine_modules() -> list[Path]:
    """The engine package only — not tests, not scripts.

    A field read solely by a test is not connected to anything a query runs
    through, and `scripts/` hand-builds chunks rather than consuming them, so
    counting either would let a dead field look live.
    """
    return sorted(
        p for p in PACKAGE.glob("*.py")
        if p.name != "__init__.py" and p != DEFINING_MODULE
    )


def _trees():
    for path in _engine_modules():
        yield path, ast.parse(path.read_text())


def _reads_of(field: str) -> list[str]:
    """Modules that read `<something>.<field>` as an attribute, matched on the
    AST so a name in a comment or docstring does not count (#130)."""
    found = set()
    for path, tree in _trees():
        for node in ast.walk(tree):
            if (isinstance(node, ast.Attribute) and node.attr == field
                    and not isinstance(node.ctx, ast.Store)):
                found.add(path.name)
                break
    return sorted(found)


def _names_other_classes_use() -> set[str]:
    """Attribute names that some other class declares in its body or assigns
    on `self`. A read of one of these is not evidence about chunks."""
    names = set()
    for path in sorted(PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text())
        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef) or cls.name == "TextChunk":
                continue
            for node in ast.walk(cls):
                if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    names.add(node.target.id)
                elif isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            names.add(t.id)
                        elif (isinstance(t, ast.Attribute)
                              and isinstance(t.value, ast.Name)
                              and t.value.id == "self"):
                            names.add(t.attr)
    return names


def _ambiguous() -> set[str]:
    return set(TextChunk.model_fields) & _names_other_classes_use()


def _unread() -> set[str]:
    unread = set()
    for f in TextChunk.model_fields:
        if f in HAND_CHECKED:
            if HAND_CHECKED[f][0] == "unread":
                unread.add(f)
        elif not _reads_of(f):
            unread.add(f)
    return unread


# ── the scan can fail ─────────────────────────────────────────

def test_the_scan_looks_at_more_than_one_module():
    """A glob that matched nothing would report every field unread, which reads
    as a catastrophic finding rather than a broken scan."""
    mods = _engine_modules()
    assert len(mods) > 10, [p.name for p in mods]
    assert DEFINING_MODULE not in mods


def test_the_scan_can_see_a_read_that_exists():
    """A matcher that never matches reports everything unread and looks like a
    discovery (#126's shape), so the positive case is pinned first."""
    assert "t3a_retriever.py" in _reads_of("vyapti_anchors")


def test_the_collision_that_hid_a_field_is_detected():
    """`Vyapti.epistemic_status` is what made the chunk field look read. If the
    shared-name scan stopped seeing it, the old blind spot is back."""
    assert "epistemic_status" in _ambiguous()
    assert _reads_of("epistemic_status"), "the name-matched read is the trap"


# ── the laws ──────────────────────────────────────────────────

def test_every_shared_name_has_a_hand_checked_verdict():
    """A name another class also uses cannot be settled by the scan. A new one
    must get a verdict here; a stale one must be removed."""
    assert _ambiguous() == set(HAND_CHECKED), (
        f"chunk fields sharing a name with another class: {sorted(_ambiguous())}; "
        f"verdicts recorded for: {sorted(HAND_CHECKED)}"
    )


def test_a_field_the_scan_cannot_find_read_is_not_verdicted_read():
    """A hand verdict of 'read' must not cover for a field nothing reads even by
    name — that would be the verdict hiding a dead field."""
    for f, (verdict, _) in HAND_CHECKED.items():
        if verdict == "read":
            assert _reads_of(f), f"{f} is marked read but nothing reads it by name"


def test_every_chunk_field_is_read_or_is_a_known_absence():
    unread = _unread()
    assert unread == set(KNOWN_UNREAD), (
        f"unread chunk fields are {sorted(unread)}, expected exactly "
        f"{sorted(KNOWN_UNREAD)} — a new name is a field nothing consults; a "
        f"missing one has found a consumer and should leave KNOWN_UNREAD"
    )


def _compiler_writes() -> set[str]:
    """Keyword arguments of every `TextChunk(...)` call in the compiler."""
    written = set()
    calls = 0
    for node in ast.walk(ast.parse(DEFINING_MODULE.read_text())):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "TextChunk"):
            calls += 1
            written |= {k.arg for k in node.keywords}
    assert calls, "the compiler no longer constructs a TextChunk by name"
    return written


def test_the_compiler_writes_every_field():
    """`embedding` and `source_ids` were declared and never assigned anywhere,
    so the model promised values no code kept. Any field the compiler does not
    pass is the same defect."""
    missing = set(TextChunk.model_fields) - _compiler_writes()
    assert not missing, f"declared on TextChunk but never written: {sorted(missing)}"


def test_a_dropped_field_is_refused_not_ignored():
    """Pydantic ignores unknown keywords by default, so a caller still passing
    `sourced=` would lose it without a sound."""
    with pytest.raises(ValueError):
        TextChunk(chunk_id="x", chapter_id="ch01", text="t", sourced=True)


# ── on the real corpus ────────────────────────────────────────

def test_every_field_varies_on_the_real_corpus():
    """`sourced` was written on every chunk and False on all of them. A field
    constant across a real corpus tells a reader nothing. `concept_anchors` is
    the known exception, None on every shipped base and pinned in #126's test."""
    from anvikshiki_v4.engine_factory import load_guide_dir
    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store
    from anvikshiki_v4.t3_compiler import compile_t3

    ks = load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")
    _, chunks = compile_t3(load_guide_dir("guides/business_expert"), ks)
    assert len(chunks) > 100, f"only {len(chunks)} chunks — corpus did not load"

    constant = []
    for f in TextChunk.model_fields:
        values = Counter(repr(getattr(c, f)) for c in chunks)
        if len(values) < 2:
            constant.append((f, next(iter(values))))
    assert constant == [("concept_anchors", "None")], constant


def test_the_vyapti_anchor_is_read_on_the_primary_path():
    """It was read only inside `_fallback_retrieve` — the keyword path taken
    when embeddings are unavailable — so on a healthy run every anchor field
    was inert. `_apply_boost` runs on the embedding path."""
    tree = ast.parse((PACKAGE / "t3a_retriever.py").read_text())
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_apply_boost"
    )
    reads = [
        n.attr for n in ast.walk(fn)
        if isinstance(n, ast.Attribute) and not isinstance(n.ctx, ast.Store)
    ]
    assert "vyapti_anchors" in reads, (
        "_apply_boost no longer reads vyapti_anchors, so the anchor signal is "
        "back to being consulted only when embeddings are unavailable"
    )
