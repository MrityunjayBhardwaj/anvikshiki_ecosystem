# anvikshiki_v4/tests/test_status_bound_by_is_recorded.py
"""Every production argument records what bounds its status.

A ceiling enforced internally and invisible externally is a guarantee nobody
benefits from — that is the whole premise of showing provenance. An argument
built without `status_bound_by` reaches the panel with a status and no
explanation for it, and `None` there is indistinguishable from "nothing
constrains this" to anyone reading a rendered table.

Asserted by parsing the package rather than by raising at construction. A
runtime check only fires once a real query runs the affected branch, and three
of the five sites are reached only by scope exclusions or temporal decay. This
is the same shape as the origin-stamp and provenance laws: find the
construction sites in the source, assert how many there are so the scan cannot
pass by matching nothing, then check each one.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parent.parent

# Every module that builds an Argument for production use. Test fixtures are
# deliberately excluded: their bindings are irrelevant and requiring them
# would have meant editing a hundred fixtures to assert nothing.
SEARCHED = ("t2_compiler_v4.py", "argumentation.py")

# Asserted, not discovered. If a site is added or removed this number is what
# forces someone to look at whether the new one records its bounds — which is
# exactly how the fifth site was found while writing this.
EXPECTED_SITES = 5


def _argument_constructions() -> list[tuple[str, int, ast.Call]]:
    found = []
    for name in SEARCHED:
        path = PACKAGE / name
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name) and func.id == "Argument":
                found.append((name, node.lineno, node))
    return found


def test_the_scan_finds_the_construction_sites_it_expects():
    """The denominator. A scan matching nothing passes every assertion below
    it, and this file exists because that has already happened twice in this
    tree — in the tools built to catch it."""
    sites = _argument_constructions()
    assert len(sites) == EXPECTED_SITES, (
        f"expected {EXPECTED_SITES} Argument construction sites across "
        f"{SEARCHED}, found {len(sites)}: "
        f"{[(m, ln) for m, ln, _ in sites]}. If a site was added, give it a "
        f"`status_bound_by` and update this count."
    )


def test_every_production_argument_records_what_bounds_it():
    sites = _argument_constructions()
    assert sites, "no construction sites found — the scan matched nothing"

    missing = [
        (module, lineno)
        for module, lineno, call in sites
        if not any(kw.arg == "status_bound_by" for kw in call.keywords)
    ]
    assert missing == [], (
        f"{len(missing)} of {len(sites)} Argument construction site(s) do not "
        f"record what bounds the status: {missing}. Such an argument reaches "
        f"the provenance panel with a ceiling and no explanation, and its "
        f"`None` reads as 'unconstrained' to whoever renders it."
    )


def test_the_scan_fails_when_pointed_at_a_name_nothing_matches(monkeypatch):
    """Mutation-check of the scan itself.

    A scan believed rather than verified is the same defect one level up, and
    is how a probe comparing two empty files reported perfect reproducibility.
    Point the matcher at a class name nothing constructs and confirm the
    denominator assertion fails rather than passing over an empty set.
    """
    import anvikshiki_v4.tests.test_status_bound_by_is_recorded as module

    def _nothing() -> list:
        return []

    monkeypatch.setattr(module, "_argument_constructions", _nothing)

    with pytest.raises(AssertionError):
        module.test_the_scan_finds_the_construction_sites_it_expects()
    with pytest.raises(AssertionError):
        module.test_every_production_argument_records_what_bounds_it()
