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

from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent

# A module that reads an ignored artefact has to say what it does when the
# artefact is missing. Either form counts: the decorator or the inline call.
GUARDS = ("skipif", "pytest.skip")


def _modules_reading_ignored_artefacts():
    hits = []
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        text = path.read_text()
        # Only count a module that actually names the ignored directory in
        # code. This module's own prose mentions it constantly, which is why
        # it excludes itself above.
        if "traces/" in text:
            hits.append((path.name, text))
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
        name for name, text in _modules_reading_ignored_artefacts()
        if not any(g in text for g in GUARDS)
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
