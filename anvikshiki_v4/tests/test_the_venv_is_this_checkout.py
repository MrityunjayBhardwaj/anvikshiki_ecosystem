"""A checkout's own `.venv` runs this checkout's code (#48).

This venv was once copied from an older clone and kept pointing at it. Scripts
run from outside the repo then imported the older clone's engine and raised
nothing, so their numbers described different code. `.venv/bin/pytest` and
`activate` used the older clone's interpreter too.

These tests start the venv's own interpreter outside the repo, because pytest
puts the repo first on `sys.path` and an import from here always looks right.
They read `.venv` rather than the running interpreter, so they see it however
the suite was launched. A worktree or a clone with no `.venv` has nothing to
check and skips.
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VENV = REPO_ROOT / ".venv"
PYTHON = VENV / "bin" / "python"

pytestmark = pytest.mark.skipif(not PYTHON.exists(), reason="this checkout has no .venv")


def _found_from_outside(name, cwd):
    """Where the venv's interpreter finds `name`, started outside the repo with
    no PYTHONPATH. None if it cannot find it, which fails loudly when used."""
    code = ("import importlib.util as u; s = u.find_spec(%r); "
            "print(s.origin if s else '')" % name)
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    out = subprocess.run([str(PYTHON), "-c", code], cwd=cwd, env=env, check=True,
                         capture_output=True, text=True).stdout.strip()
    return Path(out).resolve() if out else None


@pytest.mark.parametrize("package", ["anvikshiki_v4", "occam"])
def test_a_script_outside_the_repo_imports_this_checkout(package, tmp_path):
    found = _found_from_outside(package, tmp_path)
    assert found == REPO_ROOT / package / "__init__.py", (
        f"{PYTHON} finds {package} at {found}; run: {PYTHON} -m pip install -e .")


def _shebang(path):
    with path.open("rb") as f:
        return f.readline().decode("utf-8", "replace").strip()


def test_every_script_in_the_venv_runs_the_venvs_own_interpreter():
    scripts = [p for p in (VENV / "bin").iterdir() if p.is_file() and not p.is_symlink()]
    assert any(_shebang(p).startswith("#!") for p in scripts)   # the scan saw some scripts
    elsewhere = [f"{p.name}: {_shebang(p)}" for p in scripts
                 if _shebang(p).startswith("#!/") and "/bin/python" in _shebang(p)
                 and not _shebang(p)[2:].startswith(f"{VENV}/")]
    assert elsewhere == [], f"these run another venv's interpreter: {elsewhere}"


def test_activating_the_venv_activates_this_venv():
    text = (VENV / "bin" / "activate").read_text()
    named = re.findall(r"^\s*(?:export )?VIRTUAL_ENV=['\"]?(/[^'\"\s]+)", text, re.M)
    assert [n for n in named if n != str(VENV)] == [], f"activate names {named}"
