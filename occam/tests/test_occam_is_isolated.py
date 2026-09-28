"""The package's isolation is a law, not a docstring claim (#137).

Occam exists to be the subset that survives being stripped to the bone: no
predicates, no vocabulary, no knowledge base, no regular expressions in any
decision path. That is easy to state and easy to lose one convenient import at
a time, and nothing would fail when it went.

The allowlist below is small on purpose. Three modules from the engine are
admissible because they were *measured* clean rather than assumed so — the
ASPIC+ solver imports no knowledge store, no vocabulary and no regular
expressions:

    $ grep -c 'KnowledgeStore\\|knowledge_store\\|reference_bank\\|synonym\\|re\\.\\|vocab' \\
        anvikshiki_v4/argumentation.py
    0

Everything else in the engine is forbidden here. A law that fails when a
forbidden module appears is the only thing that keeps the boundary real, and
the failure message has to say *why* the module is refused, or the next person
to need it will simply add it to the list.
"""

import ast
import tomllib
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parent

# Engine modules Occam may use. Each is here because it carries no knowledge
# base, no vocabulary and no matching — checked, not assumed.
ALLOWED_ENGINE_MODULES = {
    "anvikshiki_v4.argumentation",  # the solver: grounded + preferred semantics
    "anvikshiki_v4.schema_v4",      # Argument, Attack, ProvenanceTag, statuses
    "anvikshiki_v4.lattice",        # the status ordering and its joins
}

# Why each of these would break the point of the package, if imported.
FORBIDDEN_REASONS = {
    "t2_compiler_v4": "loads a KnowledgeStore — Occam has no knowledge base",
    "t2b_compiler": "runs predicate extraction over a guide corpus",
    "t3_compiler": "chunks guide prose and detects references by name matching",
    "t3a_retriever": "retrieval over a compiled corpus",
    "coverage": "routes on a fixed predicate vocabulary",
    "predicate_contrariness": "a hand-maintained antonym list",
    "predicate_extraction": "the five-stage extractor Occam replaces",
    "extraction_eval": "Jaccard token overlap — the matcher Occam removes",
    "instrument_validation": "measures that matcher",
    "engine_factory": "wires the whole knowledge-base pipeline",
    "engine_v4": "the knowledge-base engine",
    "grounding": "grounds a query against a predicate vocabulary",
    "kb_augmentation": "augments a knowledge base",
    "advisories": "reads declared scope from a knowledge base",
}


def _modules() -> list[Path]:
    return sorted(p for p in PACKAGE.glob("*.py") if p.name != "__init__.py")


def _imported_names(path: Path) -> set[str]:
    """Every module name this file imports, absolute form where resolvable."""
    tree = ast.parse(path.read_text())
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                found.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative — inside occam, fine
                continue
            if node.module:
                found.add(node.module)
                for a in node.names:
                    found.add(f"{node.module}.{a.name}")
    return found


def test_there_are_modules_to_check():
    """Denominator. An empty glob passes every law below."""
    mods = _modules()
    assert mods, "no modules found — the scan is broken, not the package clean"
    assert any(p.name == "snapshot.py" for p in mods), [p.name for p in mods]


def test_no_forbidden_engine_module_is_imported():
    """The law. Names the reason, so adding an import is a decision rather
    than a convenience."""
    offences: list[str] = []
    for path in _modules():
        for name in _imported_names(path):
            if not name.startswith("anvikshiki_v4"):
                continue
            leaf = name.split(".")[1] if "." in name else ""
            if leaf in FORBIDDEN_REASONS:
                offences.append(
                    f"{path.name} imports {name} — {FORBIDDEN_REASONS[leaf]}"
                )
    assert not offences, "\n".join(offences)


def test_any_engine_import_is_on_the_allowlist():
    """Catches the module nobody thought to forbid. The forbidden list is a
    list and a list will miss things; this one is closed rather than open."""
    stray: list[str] = []
    for path in _modules():
        for name in _imported_names(path):
            if not name.startswith("anvikshiki_v4"):
                continue
            if not any(name.startswith(a) for a in ALLOWED_ENGINE_MODULES):
                stray.append(f"{path.name} imports {name}")
    assert not stray, (
        "engine imports not on the allowlist:\n" + "\n".join(stray) +
        "\nAdd it to ALLOWED_ENGINE_MODULES only after checking the module "
        "carries no knowledge store, vocabulary or matching."
    )


def test_the_allowlist_ships_unused_and_the_denominator_says_so():
    """Ready, not working. The snapshot store imports nothing from the engine,
    so the allowlist is unexercised on the day it ships — and an unexercised
    allowlist is untested machinery wearing the same green as the rest. State
    the zero beside what it was measured over, or the number means nothing.
    """
    used = set()
    for path in _modules():
        for name in _imported_names(path):
            if name.startswith("anvikshiki_v4"):
                used.add(name)
    assert used == set(), f"expected no engine imports yet, found {sorted(used)}"
    assert len(_modules()) >= 1, "zero measured over no modules at all"


def test_no_regular_expressions_in_the_package():
    """Occam's decisions are substring containment and graph computation. A
    regex here is the reading-by-word-matching that the package exists to
    remove, and it arrives looking helpful."""
    users = [p.name for p in _modules() if "re" in _imported_names(p)]
    assert not users, (
        f"{users} import `re`. Occam decides by exact containment and by "
        f"solving a graph; pattern matching on prose is what it replaces."
    )


def test_occam_tests_are_actually_collected():
    """A test directory pytest never visits is worse than no tests: the suite
    stays green and the laws are decorative. `testpaths` was
    ["anvikshiki_v4/tests"] when this package was created, so these files
    existed and ran nowhere."""
    cfg = tomllib.loads((REPO / "pyproject.toml").read_text())
    paths = cfg["tool"]["pytest"]["ini_options"]["testpaths"]
    assert "occam/tests" in paths, (
        f"testpaths is {paths} — occam/tests is not collected, so every law "
        f"in this package is invisible to a bare `pytest` run"
    )
