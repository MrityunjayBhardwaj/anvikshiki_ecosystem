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


# ── resuming a run that stopped part-way ───────────────────

def _resumable(monkeypatch, tmp_path, kept_model, kept_question=None):
    """q01 already written by `kept_model` for `kept_question` (the built-in
    list's first, by default); the live model is scripted-xyz and every new
    question gets q01's stored answer back."""
    import json

    import occam.__main__ as cli
    from occam.answer import stored_run
    from occam.controls import FACTUAL_QUESTIONS
    from occam.model import ScriptedModel
    from occam.tests.test_answer import AGREE, NO_ATTACKS, ask
    ans, art = ask(AGREE, NO_ATTACKS)
    art = art.model_copy(update={
        "question": kept_question or FACTUAL_QUESTIONS[0],
        "params": art.params.model_copy(update={"model": kept_model})})
    (tmp_path / "q01.json").write_text(stored_run(ans, art))
    before = (tmp_path / "q01.json").read_text()
    ran = []
    monkeypatch.setattr(om, "make_model", lambda spec: ScriptedModel([], name="scripted-xyz"))
    monkeypatch.setattr(cli, "run", lambda q, model, **kw: (ran.append(q), (ans, art))[1])
    return ran, before, json


def test_resume_keeps_what_was_written_and_runs_only_the_rest(monkeypatch, tmp_path, capsys):
    ran, before, _ = _resumable(monkeypatch, tmp_path, "scripted-xyz")
    assert main(["measure", "--resume", "--web", "0", "--out", str(tmp_path)]) == 0
    assert len(ran) == 9                                    # q02..q10 only
    assert (tmp_path / "q01.json").read_text() == before    # never written over
    assert "q01 kept from an earlier pass" in capsys.readouterr().out


def test_resume_refuses_a_question_another_model_made(monkeypatch, tmp_path):
    ran, before, _ = _resumable(monkeypatch, tmp_path, "openrouter/z-ai/glm-5.2")
    assert main(["measure", "--resume", "--out", str(tmp_path)]) == 2
    assert ran == [] and (tmp_path / "q01.json").read_text() == before


# ── a question list from a file (#226) ─────────────────────

HELD_OUT = "# a held-out set\n\nWhat causes ocean tides?\n  \nWho discovered penicillin?\n"


def test_measure_runs_the_questions_in_a_file(monkeypatch, tmp_path, capsys):
    ran, _, _ = _resumable(monkeypatch, tmp_path, "scripted-xyz",
                           kept_question="What causes ocean tides?")
    qs = tmp_path / "held-out.txt"
    qs.write_text(HELD_OUT)
    out = tmp_path / "run"
    out.mkdir()
    (tmp_path / "q01.json").rename(out / "q01.json")
    assert main(["measure", "--resume", "--web", "0", "--questions", str(qs),
                 "--out", str(out)]) == 0
    assert ran == ["Who discovered penicillin?"]           # comments and blanks skipped
    assert "abstained 0 of 2" in capsys.readouterr().out


def test_resume_refuses_a_question_from_another_list(monkeypatch, tmp_path):
    ran, before, _ = _resumable(monkeypatch, tmp_path, "scripted-xyz")
    qs = tmp_path / "held-out.txt"
    qs.write_text(HELD_OUT)
    assert main(["measure", "--resume", "--questions", str(qs), "--out", str(tmp_path)]) == 2
    assert ran == [] and (tmp_path / "q01.json").read_text() == before


def test_an_empty_question_file_is_refused_before_any_model(tmp_path, no_model):
    qs = tmp_path / "empty.txt"
    qs.write_text("# nothing\n\n")
    assert main(["measure", "--questions", str(qs), "--out", str(tmp_path / "new")]) == 2
