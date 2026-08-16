# conftest.py
"""Pytest session setup — pins the suite's environment explicitly.

Why this file exists
────────────────────
``litellm/__init__.py:82`` calls ``dotenv.load_dotenv()`` as an import side
effect, and ``dotenv.main.find_dotenv`` (main.py:356) picks its search root by
heuristic:

    usecwd | REPL | debugger | frozen  →  os.getcwd()
    otherwise                          →  the importing file's directory, upward

So which ``.env`` the suite sees — if any — depends on how the interpreter was
launched and where the virtualenv happens to sit:

  * plain ``pytest``       walks up from ``.venv/.../litellm/`` and finds this
                           repo's ``.env`` only because the venv lives inside
                           the repo. Move the venv and the suite goes quiet.
  * under coverage or pdb  ``sys.gettrace() is not None``, so the cwd branch is
                           taken (main.py:354) and a run launched from another
                           directory sees no ``.env`` at all.

``test_engine_v4_l3.py`` reads the key at module import to decide
``LLM_AVAILABLE``, and ``skipif`` consumes it — so the same suite on the same
code reports four failures or four skips depending on the launcher. The skip
path reads as green.

This file removes the guess. The ``.env`` beside it is loaded at collection
time, anchored to ``__file__``, before any test module is imported. Nothing
about the working directory, the venv's location, or the launcher changes what
the suite sees.

Variables already set in the environment win — ``load_dotenv`` does not
override — so ``GOOGLE_API_KEY=... pytest`` still does what it looks like.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent
DOTENV_PATH = REPO_ROOT / ".env"

DOTENV_LOADED = load_dotenv(DOTENV_PATH, override=False)


def pytest_report_header(config):
    """Report the environment the suite is actually running against.

    A degraded run has to be distinguishable from a healthy one. Without this,
    "no LLM configured" and "LLM configured and working" differ only in a skip
    count that nobody reads.
    """
    gemini = bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"))
    local = os.environ.get("LOCAL_LLM_URL")
    return [
        f"env file: {DOTENV_PATH} ({'loaded' if DOTENV_LOADED else 'absent'})",
        f"llm backends: gemini={'configured' if gemini else 'absent'}, "
        f"local={local or 'absent'}",
    ]
