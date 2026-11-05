"""No check in the package is an `assert` (#276).

`python -O` removes every assert statement, so a guard written as one passes
silently in exactly the run where it was not looked at. Occam's guards keep a
frozen version honest and probes valid; each is a `raise`. Tests may assert:
pytest rewrites them and nobody runs the suite under -O.
"""

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]


def asserts_in(source: str, name: str) -> list[str]:
    """Each assert statement in `source`, as "name:line"."""
    return [f"{name}:{n.lineno}" for n in ast.walk(ast.parse(source))
            if isinstance(n, ast.Assert)]


def test_no_module_in_the_package_guards_with_an_assert():
    modules = [p for p in PACKAGE.rglob("*.py") if "tests" not in p.relative_to(PACKAGE).parts]
    assert len(modules) > 10                         # the scan saw the package, not nothing
    found = [a for p in modules for a in asserts_in(p.read_text(), p.name)]
    assert found == [], f"python -O drops these; raise instead: {found}"


def test_the_scan_finds_an_assert_where_there_is_one():
    assert asserts_in("x = 1\nif x:\n    assert x == 1, 'one'\n", "m.py") == ["m.py:3"]
    assert asserts_in("x = 1\nif x != 1:\n    raise RuntimeError\n", "m.py") == []
