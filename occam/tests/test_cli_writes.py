"""Live commands never write over an earlier run's artifacts (#168).

`traces/` is gitignored, so an overwritten artifact is unrecoverable, and the
validation docs cite those files by path and hash. The refusal must come before
a model is built: after that, the run has already cost model calls.
"""

import pytest

import occam.model as om
from occam.__main__ import main


class Built(Exception):
    pass


@pytest.fixture
def no_model(monkeypatch):
    def refuse(*a, **k):
        raise Built
    monkeypatch.setattr(om, "OpenRouterModel", refuse)


@pytest.mark.parametrize("cmd,held", [
    (["measure"], "q01.json"),
    (["controls"], "control-adversarial.json"),
])
def test_a_directory_holding_artifacts_is_refused_before_any_model(tmp_path, no_model, cmd, held):
    (tmp_path / held).write_text("registered")
    assert main(cmd + ["--out", str(tmp_path)]) == 2
    assert (tmp_path / held).read_text() == "registered"


def test_ask_refuses_an_existing_file(tmp_path, no_model):
    f = tmp_path / "a.json"
    f.write_text("registered")
    assert main(["ask", "q?", "--out", str(f)]) == 2
    assert f.read_text() == "registered"


@pytest.mark.parametrize("cmd", [["measure"], ["controls"]])
def test_a_fresh_directory_goes_on_to_build_the_model(tmp_path, no_model, cmd):
    with pytest.raises(Built):
        main(cmd + ["--out", str(tmp_path / "new")])


def test_measure_no_longer_defaults_into_run1(no_model, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "traces/occam/run1").mkdir(parents=True)
    (tmp_path / "traces/occam/run1/q01.json").write_text("registered")
    with pytest.raises(Built):        # a fresh default dir: nothing refused
        main(["measure"])
    assert (tmp_path / "traces/occam/run1/q01.json").read_text() == "registered"
