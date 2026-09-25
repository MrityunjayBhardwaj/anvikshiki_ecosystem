"""Every field computed onto a TextChunk is read by something (#129).

`_chunk_guide_text` computes three anchor fields in one loop, from one kind of
matcher, and stores them side by side. Only one of them was ever read:

    vyapti_anchors        t3a_retriever.py — a scoring boost
    hetvabhasa_anchors    nothing; the name occurred nowhere else in the package
    concept_anchors       nothing (a `print` in run_pipeline_e2e.py)

None of that failed anything, because a field nobody reads produces no symptom.
The value is computed correctly, stored correctly, and never consulted — which
looks identical to a field that is working. This module makes the absence
fail instead of staying quiet, and does it over *every* field rather than the
three that happened to be noticed: the same check that would have caught these
catches the next one for free.

The known-unread set is asserted EXACTLY, not as an upper bound. A new unread
field fails the law (it is not in the set), and wiring one of the known two up
also fails it (it is in the set and should not be) — so the list cannot rot in
either direction, and removing a field from it is a deliberate edit rather than
a silent drift.

Why the two are still unread after #129, which is the honest answer and not an
oversight:

  hetvabhasa_anchors  has no producer at retrieval time. Retrieval is STEP 5 of
                      `EngineV4.query`; hetvābhāsa violations are computed at
                      STEP 7 (engine_v4.py, "Collect defeated arguments"), two
                      steps later, from the evaluated argumentation framework.
                      There is no `relevant_hetvabhasas` anywhere in the package
                      to boost on. Wiring it needs the pipeline reordered, which
                      is a larger change than connecting a field.

  concept_anchors     has no activation signal either — there is no
                      `relevant_concepts` — and the matcher that fills it cannot
                      currently match anything (#126: it searches chapter prose
                      for the literal `c01`). Fixing that matcher first would
                      have produced a correct signal on a channel with no
                      consumer, which is why #129 comes first.

Five further fields are unread for reasons of their own and are tracked in
#134 — `prerequisites`, `sourced` and `difficulty_tier` are populated on every
chunk and consulted by nothing; `chunk_id` is read only by diagnostics; and
`embedding` is never read AND never assigned by any code path in the repository.
#129 noticed the two anchor fields; writing this check generally is what found
the other five, which is the whole argument for checking the property rather
than the instances.

WHAT THIS CHECK CANNOT SEE, stated so it is not trusted further than it goes:
attribute reads are matched by NAME, with no type information. `v.epistemic_status`
on a `Vyapti` counts as a read of the chunk field of the same name. So the check
UNDER-reports — every field it flags is genuinely unread, but a field it passes
may still be dead if another class shares the attribute name. It is a lower
bound on the problem, not a measurement of it.

Both anchor fields are left in place rather than deleted. They are computed by a working
matcher and are plausibly wanted by the source-anchored review surface (#29);
"I don't see why this is needed" is not the same as "this is not needed". What
changes here is that their absence is recorded and enforced instead of implied.
"""

import ast
from pathlib import Path

from anvikshiki_v4.t3_compiler import TextChunk

PACKAGE = Path(__file__).resolve().parents[1]
DEFINING_MODULE = PACKAGE / "t3_compiler.py"

# Fields on a chunk that nothing in the engine package reads. Seven of twelve
# (#134) — #129 noticed the two anchor fields, and writing the general check is
# what found the other five. The set is asserted EXACTLY below, so this list
# cannot quietly grow or quietly shrink.
KNOWN_UNREAD = {
    # #129 — no producer at retrieval time; see this module's docstring.
    "hetvabhasa_anchors",
    "concept_anchors",
    # #134 — populated by the compiler at t3_compiler.py:171-174 and never
    # consulted. Real pedagogical signal from the chapter fingerprints, paid
    # for on every chapter of every base, and looked at by nothing.
    "prerequisites",
    "sourced",
    "difficulty_tier",
    # #134 — read only by run_pipeline_e2e.py and two scripts/ tracers. That
    # may be right for an identifier, but nothing says so.
    "chunk_id",
    # #134 — the sharpest one: never READ and never ASSIGNED, by any code path
    # in the repository including tests and scripts. It has been None on every
    # chunk ever constructed.
    "embedding",
}


def _engine_modules() -> list[Path]:
    """The engine package only — not tests, not scripts.

    A field read solely by a test is not connected to anything a query runs
    through, and `scripts/` hand-builds chunks rather than consuming them, so
    counting either would let a dead field look live. That is the mistake this
    module exists to catch, and it would be an easy one to make here.
    """
    return sorted(
        p for p in PACKAGE.glob("*.py")
        if p.name != "__init__.py" and p != DEFINING_MODULE
    )


def _reads_of(field: str) -> list[str]:
    """Modules that read `chunk.<field>` as an attribute.

    Matched on the AST rather than on text, so a field named only in a comment
    or docstring does not count as a read — that conflation is exactly what
    made #130 flag a module which performs no file access at all.
    """
    found = []
    for path in _engine_modules():
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:  # pragma: no cover - would fail the suite elsewhere
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == field:
                # An assignment target is a write, not a read.
                if not isinstance(node.ctx, ast.Store):
                    found.append(path.name)
                    break
    return sorted(set(found))


def test_there_are_fields_to_check():
    """Denominator. An empty field list passes every law below."""
    assert len(TextChunk.model_fields) >= 8, sorted(TextChunk.model_fields)


def test_the_scan_looks_at_more_than_one_module():
    """A glob that matched nothing would report every field as unread, which
    reads as a catastrophic finding rather than as a broken scan."""
    mods = _engine_modules()
    assert len(mods) > 10, [p.name for p in mods]
    assert DEFINING_MODULE not in mods


def test_the_scan_can_see_a_read_that_exists():
    """The direction that matters more. A matcher that never matches reports
    every field unread and looks like a discovery — #126's shape exactly — so
    the positive case is pinned before the negative one is trusted."""
    assert "t3a_retriever.py" in _reads_of("vyapti_anchors")
    assert "t3a_retriever.py" in _reads_of("chapter_id")


def test_every_chunk_field_is_read_or_is_a_known_absence():
    """The law. A field computed onto a chunk and consulted by nothing is
    machinery connected to nothing, and it produces no symptom on its own."""
    unread = sorted(
        f for f in TextChunk.model_fields if not _reads_of(f)
    )
    assert set(unread) == KNOWN_UNREAD, (
        f"unread chunk fields are {unread}, expected exactly "
        f"{sorted(KNOWN_UNREAD)} — a new name here is a field nothing "
        f"consults; a name that disappeared has found a consumer and should "
        f"be removed from KNOWN_UNREAD, with the docstring's reason deleted."
    )


# Of the unread fields, the one that is not even written. Kept separate from
# the rest because "computed and ignored" and "declared and never produced" are
# different defects and collapsing them loses the sharper one.
NEVER_WRITTEN = {"embedding"}


def test_the_computed_absences_are_still_computed():
    """Unread is not the same as unwritten. If the compiler stopped populating
    these, the right finding is 'the field is gone', not 'the field is quiet',
    and the two must not be confusable."""
    src = DEFINING_MODULE.read_text()
    for field in sorted(KNOWN_UNREAD - NEVER_WRITTEN):
        assert f"{field}=" in src, f"{field} is no longer assigned in the compiler"


def test_the_never_written_field_is_still_never_written():
    """`embedding` is declared on the model and assigned by NOTHING — not the
    compiler, not the retriever, not a script, not a test. It has been None on
    every chunk ever constructed, so the model promises a cached vector that no
    code path keeps (#134).

    Asserted as a standing zero rather than left implicit: if something starts
    populating it, this fails and the field graduates out of both lists — which
    is the point at which somebody has to decide whether anything reads it.
    """
    writers = []
    for path in sorted(PACKAGE.parent.rglob("*.py")):
        if ".venv" in path.parts or "site-packages" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text())
        except (SyntaxError, UnicodeDecodeError):  # pragma: no cover
            continue
        for node in ast.walk(tree):
            # `embedding=...` as a keyword argument or an attribute assignment.
            if isinstance(node, ast.keyword) and node.arg in NEVER_WRITTEN:
                writers.append(path.name)
            elif (isinstance(node, ast.Attribute)
                  and node.attr in NEVER_WRITTEN
                  and isinstance(node.ctx, ast.Store)):
                writers.append(path.name)
    assert not writers, (
        f"{sorted(NEVER_WRITTEN)} is now assigned in {sorted(set(writers))}; "
        f"it had no producer at all when #134 was filed"
    )


def test_the_never_written_field_is_among_the_unread():
    """The two lists must stay consistent. A field that is never written and
    yet counted as read would mean the scan is wrong, not that the field is
    fine."""
    assert NEVER_WRITTEN <= KNOWN_UNREAD


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
