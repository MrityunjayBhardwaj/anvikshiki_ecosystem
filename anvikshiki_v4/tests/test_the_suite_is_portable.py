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
import os
from fnmatch import fnmatch
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[1]

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


def _under_a_scratch_dir(node, parents) -> bool:
    """`tmp_path / "traces/x"` names a directory the test made itself.

    Walk up the chain of `/` the string sits in; if its leftmost operand is
    pytest's scratch directory (`tmp_path`, `tmp_path_factory...`), the path
    lives there and nothing ignored in the repo is read.
    """
    while isinstance(parents.get(node), ast.BinOp) and isinstance(
        parents[node].op, ast.Div
    ):
        node = parents[node]
    left = node
    while isinstance(left, ast.BinOp):
        left = left.left
    while isinstance(left, (ast.Call, ast.Attribute)):
        left = left.func if isinstance(left, ast.Call) else left.value
    return isinstance(left, ast.Name) and left.id.startswith("tmp")


def names_the_ignored_dir(code: str) -> bool:
    """Whether code (prose already stripped) names the repo's `traces/`."""
    tree = ast.parse(code)
    parents = {c: n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}
    return any(
        isinstance(n, ast.Constant)
        and isinstance(n.value, str)
        and "traces/" in n.value
        and not _under_a_scratch_dir(n, parents)
        for n in ast.walk(tree)
    )


def _is_virtualenv(path: Path) -> bool:
    return (path / "pyvenv.cfg").is_file()


def collectible(config, root: Path = REPO_ROOT) -> list[Path]:
    """Every Python file a pytest run under `root` may import (#132).

    Not one directory's `test_*.py`. Read from pytest's own settings, so the
    set moves when the configuration does:

      * anything matching `python_files`, anywhere pytest would walk — an
        untargeted run from outside the repo ignores `testpaths` (#61);
      * every `conftest.py`, which runs at collection time, so an unguarded
        read there takes the whole session down before any test runs;
      * every module under a `testpaths` directory, since helpers,
        `__init__.py` and fixtures there are imported by the tests.

    Directories matching `norecursedirs`, and virtualenvs, are not walked,
    as pytest does not walk them.
    """
    patterns = list(config.getini("python_files")) + ["conftest.py"]
    skip = list(config.getini("norecursedirs"))
    testpaths = [root / t for t in config.getini("testpaths")]
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        dirnames[:] = sorted(
            n for n in dirnames
            if not any(fnmatch(n, s) for s in skip)
            and not _is_virtualenv(here / n)
        )
        for name in filenames:
            if not name.endswith(".py"):
                continue
            path = here / name
            if any(fnmatch(name, p) for p in patterns) or any(
                t == path.parent or t in path.parents for t in testpaths
            ):
                found.append(path)
    return sorted(found)


def _modules_reading_ignored_artefacts(config):
    """Modules that name the ignored directory in code, and how many were read.

    Citing a trace in prose is the opposite of the problem — it is where a
    measured number says it came from — so the match has to be against code.
    A module that merely mentions `traces/` in a docstring reads nothing and
    is portable already.
    """
    scanned = [p for p in collectible(config) if p != Path(__file__).resolve()]
    hits = []
    for path in scanned:
        code = _code_only(path.read_text(), filename=str(path))
        if names_the_ignored_dir(code):
            hits.append((str(path.relative_to(REPO_ROOT)), code))
    return hits, len(scanned)


def test_the_ignored_directory_is_still_ignored():
    """If `traces/` ever becomes tracked, this whole module is unnecessary and
    should be deleted rather than left asserting something that cannot fail."""
    gitignore = (TESTS_DIR.parents[1] / ".gitignore").read_text()
    assert "traces/" in gitignore


def test_every_module_reading_traces_guards_on_absence(pytestconfig):
    """The law. A module may depend on an ignored artefact; it may not depend
    on it silently."""
    hits, scanned = _modules_reading_ignored_artefacts(pytestconfig)
    unguarded = [name for name, code in hits if not any(g in code for g in GUARDS)]
    assert unguarded == [], (
        f"{unguarded} (of {len(hits)} naming it, in {scanned} collectible "
        f"files) read from the gitignored traces/ directory without a "
        f"skip guard, so the suite is green only on a machine that has "
        f"already run the pipeline. Add "
        f"`pytest.mark.skipif(not PATH.exists(), reason=...)` — see "
        f"test_provenance_locator.py for the shape. #114."
    )


def test_the_guard_is_watching_something(pytestconfig):
    """A law over an empty set passes and means nothing.

    If no module reads `traces/` any more, the check above is vacuous and
    this file should go — the same reasoning as asserting a zero with its
    denominator.
    """
    reading, scanned = _modules_reading_ignored_artefacts(pytestconfig)
    assert reading, (
        "no test module reads traces/ any more, so the portability law above "
        f"is quantified over an empty set ({scanned} files scanned). Delete "
        "this module rather than leaving a check that cannot fail."
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


def test_a_path_under_the_scratch_dir_is_not_a_read():
    """`occam/tests/test_cli_writes.py` builds its own `traces/` under
    `tmp_path`. Widening the scan to occam/ (#132) flagged it; it reads
    nothing a fresh clone lacks."""
    scratch = (
        "def test_x(tmp_path):\n"
        "    (tmp_path / 'traces/occam/run1').mkdir(parents=True)\n"
        "    assert (tmp_path / 'traces' / 'x' / 'traces/q.json').exists()\n"
    )
    assert not names_the_ignored_dir(scratch)


def test_a_path_under_the_repo_is_still_a_read():
    """The control: the same string hung off anything but the scratch dir is
    a read of the repo's ignored directory."""
    for line in (
        "T = Path('traces/occam/run14/q01.json')",
        "T = REPO_ROOT / 'traces/occam/run14'",
        "T = Path(__file__).parent / 'traces/x.json'",
        "open('traces/x.json')",
    ):
        assert names_the_ignored_dir(line), line


def test_the_scan_reaches_what_pytest_collects(pytestconfig, tmp_path):
    """The set is what pytest would import, not one directory's test files.

    Run on a fixture tree laid out with this repo's settings, so each kind of
    file has a case that must be scanned and one that must not.
    """
    tree = {
        "conftest.py": True,              # runs at collection time
        "scripts/test_live.py": True,     # collected by an untargeted run
        "scripts/helper.py": False,       # matches no pattern
        "pkg/check_test.py": True,        # the other default pattern
        "anvikshiki_v4/tests/__init__.py": True,       # under testpaths
        "anvikshiki_v4/tests/fixtures/load.py": True,  # under testpaths
        "node_modules/x/test_dep.py": False,           # norecursedirs
        ".hidden/test_secret.py": False,               # norecursedirs ('.*')
        "env/test_venv.py": False,                     # a virtualenv
        "env/pyvenv.cfg": None,
    }
    for rel in tree:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("")
    got = {str(p.relative_to(tmp_path)) for p in collectible(pytestconfig, tmp_path)}
    assert got == {rel for rel, scanned in tree.items() if scanned}


def test_the_real_scan_covers_conftest_and_both_test_trees(pytestconfig):
    files = collectible(pytestconfig)
    rels = {str(p.relative_to(REPO_ROOT)) for p in files}
    assert "conftest.py" in rels
    for root in pytestconfig.getini("testpaths"):
        assert any(r.startswith(root + "/") for r in rels), root
    assert len(files) > len(list(TESTS_DIR.glob("test_*.py")))


def test_an_untargeted_run_collects_only_the_suite(pytestconfig):
    """Outside `testpaths`, nothing may match `python_files` (#61).

    `testpaths` applies only when pytest is given no paths. Run from outside
    the repo, or as `pytest .`, it walks everything — and
    `scripts/test_glm5.py` was collected that way: three live DeepInfra calls,
    1781 tests instead of 1778, and without the key an import-time
    `sys.exit(1)` in its sibling took the whole session down.
    """
    testpaths = [REPO_ROOT / t for t in pytestconfig.getini("testpaths")]
    patterns = pytestconfig.getini("python_files")
    stray = [
        str(p.relative_to(REPO_ROOT)) for p in collectible(pytestconfig)
        if any(p.name == pat or fnmatch(p.name, pat) for pat in patterns)
        and not any(t in p.parents for t in testpaths)
    ]
    assert stray == [], (
        f"{stray} match {patterns} outside {pytestconfig.getini('testpaths')}, "
        f"so `pytest <repo>` from anywhere else collects them. Rename them "
        f"(scripts/glm5_smoke.py is the precedent) or move them under a "
        f"testpaths directory."
    )
