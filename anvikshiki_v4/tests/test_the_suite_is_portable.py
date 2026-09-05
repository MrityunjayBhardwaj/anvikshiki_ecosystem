# tests/test_the_suite_is_portable.py
"""A green suite here must mean a green suite in a fresh clone.

`traces/` is gitignored, so everything under it exists only on a machine that
has already run the pipeline. Three test modules read from it. Two guarded on
existence and one opened the file directly, which made the suite green here
and red anywhere else — and a suite count is quoted as evidence, so the
difference is not cosmetic.

Measured rather than argued, on a worktree of the same commit (`61d17c6`),
which is a fresh clone for this purpose because a worktree carries no ignored
files:

    with traces/     853 passed,   4 skipped,  0 failed
    without traces/  848 passed,   7 skipped,  2 FAILED   ← FileNotFoundError

Same 857 collected either way. The two failures were
`test_provenance_locator.py`'s pair, which called `open(REAL_TRACE)` with no
guard while both sibling modules already used `pytest.mark.skipif`.

This module is the recurrence guard. The pattern has now been got wrong once
out of three attempts, and the failure is invisible to the person who
introduces it — their machine has the file.
"""

import ast
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent

# A module that reads an ignored artefact has to say what it does when the
# artefact is missing. Either form counts: the decorator or the inline call.
GUARDS = ("skipif", "pytest.skip")


class _DocstringStripper(ast.NodeTransformer):
    """Remove docstrings, so what a module says cannot pass for what it does."""

    def _strip(self, node):
        self.generic_visit(node)
        body = node.body
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            body.pop(0)
            if not body:
                body.append(ast.Pass())
        return node

    visit_Module = _strip
    visit_ClassDef = _strip
    visit_FunctionDef = _strip
    visit_AsyncFunctionDef = _strip


def _code_only(text: str, filename: str = "<source>") -> str:
    """The module with its prose removed.

    `ast.unparse` drops comments on its own, so stripping docstring nodes is
    the whole of the difference between naming the directory and reading it.

    The filename is carried only so that an unparseable module says which one
    it was — this walks every test file in the tree, and a SyntaxError with no
    name attached is a long hunt for a short problem.
    """
    return ast.unparse(_DocstringStripper().visit(ast.parse(text, filename=filename)))


def _modules_reading_ignored_artefacts():
    """Modules that name the ignored directory in code.

    Citing a trace in prose is the opposite of the problem — it is where a
    measured number says it came from — so the match has to be against code.
    A module that merely mentions `traces/` in a docstring reads nothing and
    is portable already.
    """
    hits = []
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        # This module names the directory in code in its own failure message.
        if path.name == Path(__file__).name:
            continue
        code = _code_only(path.read_text(), filename=str(path))
        if "traces/" in code:
            hits.append((path.name, code))
    return hits


def test_the_ignored_directory_is_still_ignored():
    """If `traces/` ever becomes tracked, this whole module is unnecessary and
    should be deleted rather than left asserting something that cannot fail."""
    gitignore = (TESTS_DIR.parents[1] / ".gitignore").read_text()
    assert "traces/" in gitignore


def test_every_module_reading_traces_guards_on_absence():
    """The law. A module may depend on an ignored artefact; it may not depend
    on it silently."""
    unguarded = [
        name for name, code in _modules_reading_ignored_artefacts()
        if not any(g in code for g in GUARDS)
    ]
    assert unguarded == [], (
        f"{unguarded} read from the gitignored traces/ directory without a "
        f"skip guard, so the suite is green only on a machine that has "
        f"already run the pipeline. Add "
        f"`pytest.mark.skipif(not PATH.exists(), reason=...)` — see "
        f"test_provenance_locator.py for the shape. #114."
    )


def test_the_guard_is_watching_something():
    """A law over an empty set passes and means nothing.

    If no module reads `traces/` any more, the check above is vacuous and
    this file should go — the same reasoning as asserting a zero with its
    denominator.
    """
    reading = _modules_reading_ignored_artefacts()
    assert reading, (
        "no test module reads traces/ any more, so the portability law above "
        "is quantified over an empty set. Delete this module rather than "
        "leaving a check that cannot fail."
    )


def test_prose_naming_the_directory_is_not_a_read():
    """A docstring citing the trace a number came from is provenance, not a
    dependency.

    That citation is the behaviour we want more of — it is how a measured
    claim says where it came from — and the first module to write one was
    flagged as unportable for it. See #130.
    """
    prose_only = (
        '"""Replaying the gate over traces/extraction_ch02/stage_d_ch02.json'
        ' drops exactly one."""\n'
        "def test_something():\n"
        "    assert True\n"
    )
    assert "traces/" in prose_only, "the fixture must name the directory"
    assert "traces/" not in _code_only(prose_only)


def test_a_comment_naming_the_directory_is_not_a_read():
    """Comments go the same way as docstrings, and `ast.unparse` drops them."""
    commented = "# reads traces/extraction_ch02/stage_d_ch02.json one day\n" \
                "def test_something():\n" \
                "    assert True\n"
    assert "traces/" in commented
    assert "traces/" not in _code_only(commented)


def test_a_real_read_survives_the_strip():
    """The other direction, and the one that matters more.

    Stripping prose must not be able to hide an actual dependency — a guard
    that quietly stops flagging is worse than the bug it was written for,
    because a loud failure becomes a silent absence.
    """
    reader = (
        '"""A module with no prose mention at all."""\n'
        "from pathlib import Path\n"
        'TRACE = Path("traces/extraction_ch02/stage_d_ch02.json")\n'
        "def test_something():\n"
        "    assert TRACE.exists()\n"
    )
    assert "traces/" in _code_only(reader)
