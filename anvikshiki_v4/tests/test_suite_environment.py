# tests/test_suite_environment.py
"""The suite's own environment must not depend on how it was launched.

These guard the property that makes every other gate meaningful: the same code
at the same commit has to produce the same result whatever directory pytest was
started from. It did not — `litellm` loads a `.env` as an import side effect and
`dotenv` picks its search root by heuristic, so the LLM-availability flag, and
with it four skip-or-fail outcomes, moved with the working directory and with
whether a debugger or coverage was attached.
"""

import os
from pathlib import Path

import pytest

import conftest


def test_dotenv_is_anchored_to_the_repo_not_the_working_directory():
    """The env file is found by location, not by search from cwd."""
    assert conftest.DOTENV_PATH.is_absolute()
    assert conftest.DOTENV_PATH.parent == Path(conftest.__file__).resolve().parent
    # The anchor is the repo root — the directory holding the project config.
    assert (conftest.DOTENV_PATH.parent / "pyproject.toml").exists()


def test_dotenv_anchor_survives_a_working_directory_change(tmp_path, monkeypatch):
    """Re-resolving from another cwd yields the same file."""
    before = conftest.DOTENV_PATH
    monkeypatch.chdir(tmp_path)
    after = Path(conftest.__file__).resolve().parent / ".env"
    assert after == before


def test_llm_availability_is_decided_by_the_environment_not_the_launcher():
    """The flag the skip condition reads must agree with the pinned environment.

    This is the assertion that would have caught the original defect: the four
    live tests skipped because the key was absent, while the key was present in
    the `.env` the suite is supposed to be running against.
    """
    from anvikshiki_v4.tests import test_engine_v4_l3 as l3

    configured = bool(
        os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("LOCAL_LLM_URL")
    )
    assert l3.LLM_AVAILABLE == configured


@pytest.mark.skipif(not conftest.DOTENV_PATH.exists(), reason="no .env in this checkout")
def test_env_file_contents_reached_the_process():
    """A `.env` that exists but was never read is the failure mode being guarded.

    `load_dotenv` returns True only when it actually parsed the file, so this
    distinguishes "loaded" from "silently found nothing" — the same distinction
    the suite lost when a run from the wrong directory reported green.
    """
    assert conftest.DOTENV_LOADED is True
