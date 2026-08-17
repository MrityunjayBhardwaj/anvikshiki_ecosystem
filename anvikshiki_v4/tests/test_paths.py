# tests/test_paths.py
"""Repo-relative data paths must resolve to the same thing from any directory.

Two loaders had this defect and failed differently: the knowledge base raised
file-not-found, which was loud, and the guide directory returned an empty
mapping, which was silent and therefore worse — an engine with no guides still
answered, retrieving nothing and reporting nothing. These cover the shared
resolution and both loaders' behaviour at the edges.
"""

from pathlib import Path

import pytest

from anvikshiki_v4.engine_factory import load_guide_dir
from anvikshiki_v4.paths import REPO_ROOT, resolve_repo_path
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

KB = "anvikshiki_v4/data/sample_architecture.yaml"
GUIDES = "guides/business_expert"


# ── resolution ──

def test_repo_relative_path_resolves_from_another_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert resolve_repo_path(KB) == REPO_ROOT / KB


def test_a_path_that_already_resolves_is_used_as_given(tmp_path, monkeypatch):
    """The repo root is a fallback, never an override."""
    local = tmp_path / "anvikshiki_v4" / "data"
    local.mkdir(parents=True)
    (local / "sample_architecture.yaml").write_text(
        "domain_type: FORMAL\npramanas: [local_override]\nvyaptis: {}\n"
    )
    monkeypatch.chdir(tmp_path)
    assert resolve_repo_path(KB) == Path(KB)
    assert load_knowledge_store(KB).pramanas == ["local_override"]


def test_absolute_paths_are_untouched():
    absolute = REPO_ROOT / KB
    assert resolve_repo_path(str(absolute)) == absolute


def test_missing_path_raises_naming_what_the_caller_asked_for(tmp_path, monkeypatch):
    """A typo must stay a typo rather than being laundered into a success."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError) as excinfo:
        resolve_repo_path("anvikshiki_v4/data/no_such_kb.yaml", description="knowledge base")
    assert "anvikshiki_v4/data/no_such_kb.yaml" in str(excinfo.value)
    assert "knowledge base" in str(excinfo.value)


# ── the two loaders ──

def test_knowledge_store_loads_from_another_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert len(load_knowledge_store(KB).vyaptis) > 0


def test_guides_load_from_another_directory(tmp_path, monkeypatch):
    """Observed before the fix: 7 chapters from the repo root, 0 from anywhere else."""
    monkeypatch.chdir(tmp_path)
    from_elsewhere = load_guide_dir(GUIDES)
    monkeypatch.undo()
    assert from_elsewhere == load_guide_dir(GUIDES)
    assert from_elsewhere, "no guide chapters loaded at all"


def test_missing_guide_directory_raises_instead_of_returning_empty(tmp_path, monkeypatch):
    """The silent-empty case is the one that made a broken engine look healthy."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        load_guide_dir("guides/no_such_guide_dir")


def test_empty_guide_directory_is_distinguishable_from_a_missing_one(tmp_path):
    """An existing directory with no guides returns empty — and only that case does."""
    empty = tmp_path / "guides" / "empty_domain"
    empty.mkdir(parents=True)
    assert load_guide_dir(str(empty)) == {}


def test_guide_path_that_is_a_file_is_reported_as_such(tmp_path):
    not_a_dir = tmp_path / "guides.md"
    not_a_dir.write_text("# not a directory")
    with pytest.raises(NotADirectoryError):
        load_guide_dir(str(not_a_dir))
