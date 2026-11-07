"""Occam v1 is frozen (#264): its settings are named, its prompt text is
pinned by hash, the CLI runs it as frozen, and a calibration refuses answers
from any other pipeline."""

import json

import pytest

import occam.__main__ as cli
import occam.frozen as frozen
import occam.model as om
from occam.answer import Params, stored_run
from occam.frozen import V1, V1_PROMPTS, fingerprint, made_under_v1, rendered_prompts
from occam.model import ScriptedModel
from occam.tests.test_answer import AGREE, NO_ATTACKS, ask

# The params all 20 of run 14's artifacts recorded (traces/occam/run14).
RUN_14 = {"argue_prompt": 5, "factcheck_sources": 3, "judge_same": True, "k_argue": 3,
          "k_attack": 3, "k_support": 1, "max_age_days": 365, "max_chars": 40000,
          "model": "kie/gemini-3-pro", "rules": 8, "t_argue": 0.7, "t_attack": 0.2,
          "t_same": 0.0, "t_support": 0.0, "web_fill": 2, "web_sources": 3}


# ── what v1 is ─────────────────────────────────────────────

def test_v1_is_the_pipeline_run_14_recorded():
    assert made_under_v1(Params.model_validate(RUN_14)) == []


def test_every_prompt_the_model_is_sent_is_v1s():
    """A red here means a prompt's text changed. That is Occam v2, not an edit
    to v1: a label on a v1 answer does not describe what v2 asks the model.
    Name the new version in occam.frozen rather than re-recording v1's hashes."""
    now = fingerprint()
    changed = sorted(k for k in V1_PROMPTS if now.get(k) != V1_PROMPTS[k])
    assert not changed, f"prompts changed since Occam v1: {changed}"
    assert set(now) == set(V1_PROMPTS)


def test_one_changed_word_in_one_prompt_is_caught_and_named(monkeypatch):
    monkeypatch.setattr(frozen, "QUERY_PROMPT", frozen.QUERY_PROMPT.replace("short", "brief"))
    now = fingerprint()
    assert [k for k in V1_PROMPTS if now[k] != V1_PROMPTS[k]] == ["query"]


def test_the_model_call_around_the_text_is_pinned_too():
    sent = rendered_prompts()
    assert '"temperature": 0.0' in sent["kie/complete"]
    assert '"googleSearch"' in sent["kie/web_search"]       # gemini's search tool name


@pytest.mark.parametrize("change,named", [
    ({"rules": 7}, ["rules", "covers_check"]),
    ({"model": "kie/gemini-3.1-pro"}, ["model"]),
    ({"factcheck_sources": 0}, ["factcheck_sources"]),
    ({"argue_prompt": 4}, ["argue_prompt"]),
])
def test_each_difference_from_v1_is_named(change, named):
    off = made_under_v1(Params.model_validate({**RUN_14, **change}))
    assert [line.split(":")[0] for line in off] == named


# ── the CLI runs v1 as frozen ──────────────────────────────

@pytest.fixture
def captured(monkeypatch):
    """make_model and run recorded, nothing called."""
    seen = {}
    ans, art = ask(AGREE, NO_ATTACKS)

    def run(q, model, **kw):
        seen.setdefault("params", []).append(kw["params"])
        seen["kw"] = kw
        return ans, art.model_copy(update={"params": kw["params"]})
    monkeypatch.setattr(om, "make_model", lambda spec: (seen.update(spec=spec),
                                                       ScriptedModel([], name=spec))[1])
    monkeypatch.setattr(cli, "run", run)
    monkeypatch.setattr(cli, "_factcheck_search", lambda n: (seen.update(fc=n), (None, True))[1])
    return seen


def test_measure_v1_runs_v1s_model_and_params(tmp_path, captured):
    assert cli.main(["measure", "--v1", "--out", str(tmp_path / "r")]) == 0
    assert captured["spec"] == "kie/gemini-3-pro" and captured["fc"] == 3
    assert all(p == V1 for p in captured["params"]) and captured["params"]


def test_ask_v1_runs_v1s_model_params_and_sources(tmp_path, captured, capsys):
    assert cli.main(["ask", "--v1", "q?", "--out", str(tmp_path / "a.json")]) == 0
    assert captured["spec"] == "kie/gemini-3-pro" and captured["params"] == [V1]
    assert captured["kw"]["n_sources"] == 3 and captured["kw"]["urls"] is None
    assert "made under Occam v1" in capsys.readouterr().out


def test_without_v1_the_defaults_are_what_they_were(tmp_path, captured, capsys):
    assert cli.main(["ask", "q?", "--out", str(tmp_path / "a.json")]) == 0
    assert captured["spec"] == "z-ai/glm-5.2" and captured["fc"] == 0
    p = captured["params"][0]
    assert (p.web_sources, p.factcheck_sources, p.k_argue, p.k_attack) == (3, 0, 3, 3)
    assert "NOT made under Occam v1" in capsys.readouterr().out


@pytest.mark.parametrize("cmd", [
    ["measure", "--v1", "--web", "3"],          # even v1's own value: a flag is a choice
    ["measure", "--v1", "--model", "kie/gemini-3-pro"],
    ["measure", "--v1", "--no-judge-same"],
    ["ask", "--v1", "q?", "--k", "5"],
    ["ask", "--v1", "q?", "--url", "https://example.org"],
    ["ask", "--v1", "q?", "--sources", "2"],
    ["ask", "--v1", "q?", "--factcheck", "0"],
])
def test_v1_refuses_a_flag_that_would_change_it_before_any_model(tmp_path, captured, cmd, capsys):
    out = ["--out", str(tmp_path / ("r" if cmd[0] == "measure" else "a.json"))]
    assert cli.main(cmd + out) == 2
    assert "spec" not in captured and not list(tmp_path.iterdir())
    assert "--v1 runs Occam v1 as frozen" in capsys.readouterr().err


# ── which stored runs are v1 ───────────────────────────────

def _stored(path, params_update=None, answer_update=None):
    ans, art = ask(AGREE, NO_ATTACKS)
    art = art.model_copy(update={"params": art.params.model_copy(update={
        "model": V1.model, "web_sources": 3, "factcheck_sources": 3, **(params_update or {})})})
    if answer_update:
        ans = ans.model_copy(update=answer_update)
    path.write_text(stored_run(ans, art))


def test_frozen_passes_a_directory_of_v1_runs_that_replay(tmp_path, capsys):
    _stored(tmp_path / "q01.json")
    _stored(tmp_path / "q02.json")
    assert cli.main(["frozen", str(tmp_path)]) == 0
    assert "2 of 2 made under Occam v1; 2 of 2 replay" in capsys.readouterr().out


@pytest.mark.parametrize("kw,said", [
    ({"params_update": {"model": "z-ai/glm-5.2"}}, "q02.json: NOT v1; replay matches — model"),
    ({"answer_update": {"conclusion": "edited after the run"}}, "q02.json: v1; replay DIFFERS"),
])
def test_frozen_fails_on_one_run_from_elsewhere_or_one_that_no_longer_replays(tmp_path, capsys,
                                                                             kw, said):
    _stored(tmp_path / "q01.json")
    _stored(tmp_path / "q02.json", **kw)
    assert cli.main(["frozen", str(tmp_path)]) == 1
    assert said in capsys.readouterr().out


def _given(path, given_urls=("https://a.test/1",), web=0, factcheck=0):
    """A v1 run's file, as a run handed `given_urls` would record it."""
    ans, art = ask(AGREE, NO_ATTACKS)
    art = art.model_copy(update={"given_urls": given_urls, "params": art.params.model_copy(update={
        "model": V1.model, "web_sources": web, "factcheck_sources": factcheck})})
    path.write_text(stored_run(ans, art))


def test_no_searches_are_not_v1_unless_the_artifact_says_its_pages_were_given(tmp_path, capsys):
    """#279: 0 and 0 with no pages given is a run whose searches were off. It
    reads as an older control does, because nothing says otherwise."""
    _given(tmp_path / "q01.json", given_urls=())
    assert cli.main(["frozen", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "q01.json: NOT v1; replay matches — web_sources: v1 3, this 0" in out
    assert "0 of 1 on pages they were given" in out


def test_a_run_given_its_pages_that_still_records_searches_is_not_v1(tmp_path, capsys):
    """Given pages move v1 to 0 and 0; they do not excuse any other count."""
    _given(tmp_path / "q01.json", web=3, factcheck=3)
    assert cli.main(["frozen", str(tmp_path)]) == 1
    assert "NOT v1 on given pages; replay matches — web_sources: v1 0, this 3" \
        in capsys.readouterr().out


def test_an_artifact_from_before_the_field_reads_as_not_given(tmp_path, capsys):
    _given(tmp_path / "q01.json", given_urls=())
    stored = json.loads((tmp_path / "q01.json").read_text())
    del stored["artifact"]["given_urls"]
    (tmp_path / "q01.json").write_text(json.dumps(stored))
    assert cli.main(["frozen", str(tmp_path)]) == 1
    assert "0 of 1 on pages they were given" in capsys.readouterr().out


def test_given_pages_do_not_change_the_answer_a_run_replays_to(tmp_path, capsys):
    _given(tmp_path / "q01.json")
    assert cli.main(["frozen", str(tmp_path)]) == 0
    assert "q01.json: v1 on given pages; replay matches" in capsys.readouterr().out


def test_ask_given_a_url_says_it_ran_v1_on_the_page_it_was_given(monkeypatch, tmp_path, capsys):
    """`ask --url` with v1's own settings is the other door to a given page.
    `--v1` refuses `--url`, so this door is reached with the settings spelled."""
    from occam.answer import run as real_run
    from occam.tests.test_controls import _Abstains
    monkeypatch.setattr(om, "make_model", lambda spec: _Abstains(spec))
    monkeypatch.setattr(cli, "run", lambda q, m, **kw: real_run(
        q, m, http_get=lambda url: (200, "text/plain; charset=utf-8", b"a page"), **kw))
    out = tmp_path / "a.json"
    assert cli.main(["ask", "q?", "--url", "https://a.test/1", "--model", V1.model,
                     "--factcheck", "0", "--out", str(out)]) == 0
    assert "made under Occam v1, on the pages it was given" in capsys.readouterr().out
    assert json.loads(out.read_text())["artifact"]["given_urls"] == ["https://a.test/1"]


def test_v1_line_says_nothing_of_given_pages_on_a_run_that_gathered_its_own():
    _, art = ask(AGREE, NO_ATTACKS)
    assert cli._v1_line(art.model_copy(update={"params": V1})) == "made under Occam v1"


def test_frozen_fails_on_an_empty_directory(tmp_path):
    assert cli.main(["frozen", str(tmp_path)]) == 1


# ── a calibration describes one pipeline ───────────────────

def _labels(tmp_path, n_v1, n_other):
    rows = []
    for i in range(n_v1 + n_other):
        f = tmp_path / f"q{i:02d}.json"
        _stored(f, params_update=None if i < n_v1 else {"model": "z-ai/glm-5.2"})
        rows.append(json.dumps({"artifact": str(f), "label": "hypothesis"}))
    (tmp_path / "labels.jsonl").write_text("\n".join(rows))
    return ["calibrate", str(tmp_path / "labels.jsonl"), "--population", "test",
            "--out", str(tmp_path / "cal.json")]


def test_calibrate_refuses_an_answer_not_made_under_v1(tmp_path, capsys):
    assert cli.main(_labels(tmp_path, 3, 1)) == 2
    assert "not made under Occam v1 (model" in capsys.readouterr().err
    assert not (tmp_path / "cal.json").exists()


def test_calibrate_accepts_v1_answers_and_counts_zero_from_elsewhere(tmp_path, capsys):
    assert cli.main(_labels(tmp_path, 4, 0)) == 0
    assert "labelled answers not made under Occam v1: 0 of 4" in capsys.readouterr().out


def test_calibrate_refuses_a_v1_run_on_given_pages(tmp_path, capsys):
    """#279: `frozen` calls it v1 on given pages, and that is v1's reading of a
    page someone chose, not v1's gathering. Labels describe v1 as it gathers."""
    f = tmp_path / "control.json"
    _given(f)
    (tmp_path / "labels.jsonl").write_text(json.dumps({"artifact": str(f), "label": "hypothesis"}))
    assert cli.main(["calibrate", str(tmp_path / "labels.jsonl"), "--population", "test",
                     "--out", str(tmp_path / "cal.json")]) == 2
    assert "not made under Occam v1 (web_sources: v1 3, this 0" in capsys.readouterr().err
    assert not (tmp_path / "cal.json").exists()


def test_any_pipeline_lets_them_through_and_says_how_many(tmp_path, capsys):
    assert cli.main(_labels(tmp_path, 3, 1) + ["--any-pipeline"]) == 0
    assert "labelled answers not made under Occam v1: 1 of 4" in capsys.readouterr().out
