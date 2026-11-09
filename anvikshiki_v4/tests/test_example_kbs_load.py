"""The UI's example KB buttons load, wherever the backend was started (#108).

Both buttons pointed into `anvikshiki_v4/knowledge_bases/`, which does not
exist, and `/kb/load` checked the path against the process's cwd while the
loader read it against the repo. So both headline buttons answered "KB file
not found". `KBLoader.tsx` is read rather than restated, so a button that
moves is checked where it now points.
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
LOADER_TSX = REPO / "webapp" / "components" / "kb" / "KBLoader.tsx"


def _example_paths():
    block = re.search(r"const EXAMPLE_KBS = \[(.*?)\];", LOADER_TSX.read_text(), re.S)
    assert block, "EXAMPLE_KBS not found in KBLoader.tsx"
    paths = re.findall(r'path:\s*"([^"]+)"', block.group(1))
    assert len(paths) >= 2, paths               # the extractor found the buttons
    return paths


@pytest.fixture
def client(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    import backend.main as api
    monkeypatch.chdir(tmp_path)                 # started anywhere but the repo root
    return TestClient(api.app)


@pytest.mark.parametrize("path", _example_paths())
def test_every_example_button_loads_its_kb(client, path):
    r = client.post("/kb/load", json={"kb_yaml_path": path})
    assert r.status_code == 200, r.json()
    assert r.json()["loaded"] is True


def test_a_missing_kb_still_says_so(client):
    r = client.post("/kb/load", json={"kb_yaml_path": "anvikshiki_v4/data/no_such_kb.yaml"})
    assert r.status_code == 404
    assert "no_such_kb.yaml" in r.json()["detail"]
