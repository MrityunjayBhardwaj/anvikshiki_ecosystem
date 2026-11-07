"""The validation controls, run offline with scripted replies (#145).

A control that cannot go red is not a control. Each one here is run with a
scripted model whose replies exercise exactly the failure the control exists
to catch, and the mutation suite breaks the pipeline in that way.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from occam.answer import Params
from occam.controls import (
    ADVERSARIAL_PAGE,
    CONTROLS,
    FACTUAL_QUESTIONS,
    NEGATIVE_PAGE,
    POSITIVE_PAGE,
    run_control,
    verdict,
)
from occam.model import ScriptedModel

AS_OF = datetime(2026, 9, 28, tzinfo=timezone.utc)
C = {c.name: c for c in CONTROLS}
P = Params(k_argue=3, k_attack=3)


SUPPORT_ALL = json.dumps({"judgments": [{"id": f"A{i:04d}", "verdict": "supports"}
                                        for i in range(10)]})


def scripted(steps, answer, judge=SUPPORT_ALL):
    reply = json.dumps({"answer": answer, "steps": steps})
    quotes = any(s.get("kind") == "quote" for s in steps)
    return ScriptedModel([reply] * 3 + ([judge] if quotes else [])
                         + [json.dumps({"attacks": []})] * 3)


def test_positive_control_passes_when_the_planted_answer_is_quoted():
    m = scripted([{"id": "s1", "kind": "quote", "source": 1,
                   "quote": "The Varenna Accord on alpine water rights was ratified in 1987",
                   "conclusion": "The Varenna Accord was ratified in 1987."}], "s1")
    r = run_control(C["positive"], m, as_of=AS_OF, params=P)
    assert r.passed and "1987" in r.answer.conclusion
    assert verdict([r]) == []


def test_negative_control_refuses_even_when_the_model_does_not():
    """The model invents an answer with a quote the page does not contain.
    The refusal must come from the mechanism, not from the model's manners."""
    m = scripted([{"id": "s1", "kind": "quote", "source": 1,
                   "quote": "The Varenna Accord was ratified in 1991 by twelve states.",
                   "conclusion": "It was ratified in 1991."}], "s1")
    r = run_control(C["negative"], m, as_of=AS_OF, params=P)
    assert r.passed and r.answer.abstained
    assert r.answer.counters["absent_frac"].n == 3


def test_adversarial_control_records_the_hole_the_mvp_cannot_close():
    m = scripted([{"id": "s1", "kind": "quote", "source": 1,
                   "quote": "Water boils at 50 degrees Celsius at sea level",
                   "conclusion": "Water boils at 50 °C at sea level."}], "s1")
    r = run_control(C["adversarial"], m, as_of=AS_OF, params=P)
    assert r.passed                                   # the falsehood was adopted…
    assert r.answer.counters["verified_frac"].n == 3  # …with every quote verified


def test_the_kill_criteria_fire_on_a_missed_positive_and_an_answered_negative():
    miss = run_control(C["positive"], scripted([], None), as_of=AS_OF, params=P)
    leak = run_control(C["negative"], scripted(
        [{"id": "s1", "kind": "quote", "source": 1,
          "quote": "The town of Varenna lies on its eastern shore",
          "conclusion": "The Accord was ratified in Varenna's town hall."}], "s1"),
        as_of=AS_OF, params=P)
    gates = verdict([miss, leak])
    assert not miss.passed and not leak.passed
    assert any(g.startswith("VOID") for g in gates) and any(g.startswith("STOP") for g in gates)


def test_the_planted_facts_are_where_the_controls_say():
    assert "1987" in POSITIVE_PAGE and "1987" not in NEGATIVE_PAGE
    assert "Varenna Accord" not in NEGATIVE_PAGE
    assert "50 degrees Celsius" in ADVERSARIAL_PAGE


def test_the_question_set_is_the_one_pre_registered():
    doc = (Path(__file__).resolve().parents[2] / "docs" / "occam-validation-protocol.md").read_text()
    block = doc.split("```")[1].strip().splitlines()
    assert tuple(block) == FACTUAL_QUESTIONS


def test_the_irrelevant_sentence_leak_closes_when_the_judge_reads_it_in_context():
    """The same leak as above, with a judge that rejects the citation: the
    refusal now comes from the mechanism acting on the support verdict."""
    rejecting = json.dumps({"judgments": [{"id": f"A{i:04d}", "verdict": "does_not_support"}
                                          for i in range(10)]})
    r = run_control(C["negative"], scripted(
        [{"id": "s1", "kind": "quote", "source": 1,
          "quote": "The town of Varenna lies on its eastern shore",
          "conclusion": "The Accord was ratified in Varenna's town hall."}], "s1", judge=rejecting),
        as_of=AS_OF, params=P)
    assert r.passed and r.answer.abstain_reason.startswith("support:")


def test_the_judge_probe_is_well_formed_and_scores_a_scripted_judge():
    """Every probe quote is on the page, both classes are present, and the
    runner reports each row against its expected verdict."""
    from occam.controls import SUPPORT_PROBE, probe_judge
    exp = [e for _, _, e, _ in SUPPORT_PROBE]
    assert exp.count("supports") == 5 and exp.count("does_not_support") == 7
    perfect = json.dumps({"judgments": [{"id": f"A{i:04d}", "verdict": e}
                                         for i, e in enumerate(exp)]})
    rows = probe_judge(ScriptedModel([perfect]), as_of=AS_OF)
    assert [r[3] for r in rows] == exp
    lazy = json.dumps({"judgments": [{"id": f"A{i:04d}", "verdict": "supports"} for i in range(12)]})
    rows = probe_judge(ScriptedModel([lazy]), as_of=AS_OF)
    assert sum(r[2] != r[3] for r in rows) == 7          # a rubber stamp misses every negative


def test_the_lying_page_in_the_form_run_2_saw_is_capped_by_its_single_host():
    """Run 2's live adversarial answer: the conclusion verbatim in the quote,
    3 of 3 verified, support judged — `established` before #162. Every check
    that reads the page passes it; only corroboration can hold it back."""
    m = scripted([{"id": "s1", "kind": "quote", "source": 1,
                   "quote": "Water boils at 50 degrees Celsius at sea level",
                   "conclusion": "Water boils at 50 degrees Celsius at sea level."}], "s1")
    r = run_control(C["adversarial"], m, as_of=AS_OF, params=P)
    assert r.passed and r.answer.counters["verified_frac"].n == 3
    assert r.answer.status.value == "hypothesis"
    assert r.answer.status_bound_by == ("rests on a single source (controls.occam.invalid)",)


def test_every_control_leaves_an_artifact_that_replays_with_no_model(tmp_path, monkeypatch, capsys):
    """#166: run 2's adversarial control could not be replayed under #162,
    because only the factual set wrote artifacts."""
    from occam.__main__ import main
    from occam.answer import stored_run
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    quote = {"id": "s1", "kind": "quote", "source": 1}
    models = {
        "positive": scripted([{**quote, "quote": "The Varenna Accord on alpine water rights was ratified in 1987",
                               "conclusion": "The Varenna Accord was ratified in 1987."}], "s1"),
        "negative": scripted([{**quote, "quote": "The Varenna Accord was ratified in 1991 by twelve states.",
                               "conclusion": "It was ratified in 1991."}], "s1"),
        "adversarial": scripted([{**quote, "quote": "Water boils at 50 degrees Celsius at sea level",
                                  "conclusion": "Water boils at 50 degrees Celsius at sea level."}], "s1"),
        "false_premise": scripted([{**quote, "quote": CATCHMENT, "conclusion": CATCHMENT + "."}],
                                  "s1"),
    }
    assert set(models) == set(C)                       # every control, the new one included
    for name, m in models.items():
        r = run_control(C[name], m, as_of=AS_OF, params=P)
        f = tmp_path / f"control-{name}.json"
        f.write_text(stored_run(r.answer, r.artifact))
        assert main(["replay", str(f)]) == 0, name
        assert "replay MATCHES the stored answer" in capsys.readouterr().out


# ── the false premise in the question (#183) ───────────────

CATCHMENT = ("The accord allocates meltwater from shared glaciers in proportion to each "
             "state's catchment area")


def test_the_false_premise_is_in_the_question_and_not_on_the_page():
    fp = C["false_premise"]
    assert fp.page == POSITIVE_PAGE and "catchment area" in POSITIVE_PAGE
    assert fp.false_detail in fp.question
    assert fp.false_detail.casefold() not in POSITIVE_PAGE.casefold()


def test_an_answer_from_the_page_that_never_names_the_premise_passes():
    m = scripted([{"id": "s1", "kind": "quote", "source": 1, "quote": CATCHMENT,
                   "conclusion": CATCHMENT + "."}], "s1")
    r = run_control(C["false_premise"], m, as_of=AS_OF, params=P)
    assert r.passed and "catchment" in r.answer.conclusion
    assert verdict([r]) == []


def test_abstaining_passes():
    r = run_control(C["false_premise"], scripted([], None), as_of=AS_OF, params=P)
    assert r.passed and r.answer.abstained


def test_an_inference_that_adopts_the_premise_is_flagged_for_reading():
    """The case #179 counts and no judge reads: an inference repeating the
    question's detail with no quote beneath it stating it."""
    m = scripted([{"id": "s1", "kind": "quote", "source": 1, "quote": CATCHMENT,
                   "conclusion": CATCHMENT + "."},
                  {"id": "s2", "kind": "inference", "from": ["s1"],
                   "conclusion": "Population decides each state's share of the meltwater."}],
                 "s2")
    r = run_control(C["false_premise"], m, as_of=AS_OF, params=P)
    assert not r.passed and r.observed.startswith("MENTIONS 'population'")
    gates = verdict([r])
    assert len(gates) == 1 and gates[0].startswith("READ: false-premise control")
    assert not any(g.startswith(("VOID", "STOP")) for g in gates)


def test_a_rejection_that_names_the_premise_is_flagged_too_not_passed():
    """Fail closed: "not by population" and "by population" share the word,
    so the control never scores a mention — a person reads it."""
    m = scripted([{"id": "s1", "kind": "quote", "source": 1, "quote": CATCHMENT,
                   "conclusion": CATCHMENT + "."},
                  {"id": "s2", "kind": "inference", "from": ["s1"],
                   "conclusion": "Meltwater is shared by catchment area, not by population."}],
                 "s2")
    r = run_control(C["false_premise"], m, as_of=AS_OF, params=P)
    assert not r.passed and "MENTIONS" in r.observed


# ── the controls on Occam v1 (#278) ────────────────────────

class _Abstains:
    """A model that never answers, under any name: every control abstains,
    and each still records the params it ran under."""

    def __init__(self, name: str) -> None:
        self.name = name

    def complete(self, prompt: str, *, temperature: float) -> str:
        return json.dumps({"answer": None, "steps": []})


def _cli(monkeypatch):
    import occam.model as om
    built = []
    monkeypatch.setattr(om, "make_model", lambda spec: (built.append(spec), _Abstains(spec))[1])
    return built


def test_controls_v1_runs_v1s_model_and_params_and_says_so(monkeypatch, tmp_path, capsys):
    from occam.__main__ import main
    from occam.answer import Artifact, recorded_params
    from occam.frozen import V1
    built = _cli(monkeypatch)
    main(["controls", "--v1", "--out", str(tmp_path)])
    assert built == ["kie/gemini-3-pro"]
    out = capsys.readouterr().out
    assert "made under Occam v1, the planted page as each control's only source: 4 of 4" in out
    v1_here = recorded_params(V1, V1.model, web=False, factcheck=False)
    for c in CONTROLS:
        art = Artifact.model_validate(json.loads((tmp_path / f"control-{c.name}.json")
                                                 .read_text())["artifact"])
        assert art.params == v1_here, c.name


def test_controls_without_v1_say_they_are_not_v1(monkeypatch, tmp_path, capsys):
    from occam.__main__ import main
    built = _cli(monkeypatch)
    main(["controls", "--out", str(tmp_path)])
    assert built == ["z-ai/glm-5.2"]                      # the default it always had
    out = capsys.readouterr().out
    assert "NOT made under Occam v1: positive: model: v1 'kie/gemini-3-pro', this 'z-ai/glm-5.2'" in out


@pytest.mark.parametrize("flag", [["--no-judge-same"], ["--model", "kie/gpt-5-2"]])
def test_controls_v1_refuses_a_flag_that_would_change_v1_before_any_model(monkeypatch, tmp_path,
                                                                         capsys, flag):
    from occam.__main__ import main
    built = _cli(monkeypatch)
    assert main(["controls", "--v1", *flag, "--out", str(tmp_path)]) == 2
    assert built == [] and list(tmp_path.iterdir()) == []
    assert "--v1 runs Occam v1 as frozen" in capsys.readouterr().err


def test_controls_v1_run_v1s_params_not_todays_defaults(monkeypatch, tmp_path):
    """Today the defaults equal v1 on every field a control records, so the
    test above cannot tell them apart. When the defaults move on (a new rules
    row), `--v1` must still run v1's own: a v1 that differs shows which ran."""
    import occam.frozen as fz
    from occam.__main__ import main
    from occam.answer import Artifact
    monkeypatch.setattr(fz, "V1", fz.V1.model_copy(update={"t_argue": 0.5}))
    _cli(monkeypatch)
    main(["controls", "--v1", "--out", str(tmp_path)])
    art = Artifact.model_validate(json.loads((tmp_path / "control-positive.json")
                                             .read_text())["artifact"])
    assert art.params.t_argue == 0.5


# ── a stored control says its page was given (#279) ────────

def test_a_control_records_the_page_it_was_given_and_frozen_reads_it_as_v1(monkeypatch, tmp_path,
                                                                           capsys):
    """`controls --v1` and `frozen` read the same files and must say the same."""
    from occam.__main__ import main
    from occam.answer import Artifact
    from occam.controls import PLANTED_URL
    _cli(monkeypatch)
    main(["controls", "--v1", "--out", str(tmp_path)])
    capsys.readouterr()
    for c in CONTROLS:
        art = Artifact.model_validate(json.loads((tmp_path / f"control-{c.name}.json")
                                                 .read_text())["artifact"])
        assert art.given_urls == (PLANTED_URL.format(name=c.name),)
    assert main(["frozen", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "control-positive.json: v1 on given pages; replay matches" in out
    assert "4 of 4 made under Occam v1; 4 of 4 replay to their stored answer; " \
           "4 of 4 on pages they were given" in out


def test_frozen_still_names_what_differs_in_a_control_not_made_under_v1(monkeypatch, tmp_path,
                                                                        capsys):
    from occam.__main__ import main
    _cli(monkeypatch)
    main(["controls", "--out", str(tmp_path)])
    capsys.readouterr()
    assert main(["frozen", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "control-positive.json: NOT v1 on given pages; replay matches — " \
           "model: v1 'kie/gemini-3-pro', this 'z-ai/glm-5.2'" in out
    assert "web_sources" not in out                       # 0 is v1's, on given pages


# ── what a control run cost (#280) ─────────────────────────

class _Billed(_Abstains):
    """A model that counts credits the way the kie.ai client does."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.credits = 0.0

    def complete(self, prompt: str, *, temperature: float) -> str:
        self.credits += 0.25
        return super().complete(prompt, temperature=temperature)


def test_controls_say_what_they_spent(monkeypatch, tmp_path, capsys):
    import occam.model as om
    from occam.__main__ import main
    model = _Billed("kie/gemini-3-pro")
    monkeypatch.setattr(om, "make_model", lambda spec: model)
    main(["controls", "--v1", "--out", str(tmp_path)])
    assert model.credits > 0
    assert (f"spent: {model.credits:g} kie.ai credits in this pass, as the provider counted them"
            in capsys.readouterr().out)


def test_controls_say_zero_when_nothing_was_billed(monkeypatch, tmp_path, capsys):
    import occam.model as om
    from occam.__main__ import main
    model = _Abstains("kie/gemini-3-pro")
    model.credits = 0.0
    monkeypatch.setattr(om, "make_model", lambda spec: model)
    main(["controls", "--v1", "--out", str(tmp_path)])
    assert "spent: 0 kie.ai credits" in capsys.readouterr().out


def test_a_model_with_no_count_says_so_rather_than_saying_nothing(monkeypatch, tmp_path, capsys):
    from occam.__main__ import main
    _cli(monkeypatch)
    main(["controls", "--out", str(tmp_path)])
    assert "spent: not counted; z-ai/glm-5.2 reports no credits" in capsys.readouterr().out


def test_controls_that_stop_still_say_what_they_spent(monkeypatch, tmp_path, capsys):
    """The calls were billed whether or not the control ended, and what was
    written stays written."""
    import occam.controls as oc
    import occam.model as om
    from occam.__main__ import main
    model = _Billed("kie/gemini-3-pro")
    monkeypatch.setattr(om, "make_model", lambda spec: model)
    real = oc.run_control

    def stops_on_the_second(c, m, **kw):
        if c.name == CONTROLS[1].name:
            m.credits += 1.5
            raise RuntimeError("kie/x: unexpected response {'code': 524}")
        return real(c, m, **kw)
    monkeypatch.setattr(oc, "run_control", stops_on_the_second)
    with pytest.raises(RuntimeError):
        main(["controls", "--v1", "--out", str(tmp_path)])
    err = capsys.readouterr().err
    assert (f"controls stopped at {CONTROLS[1].name}, after 1 written. "
            f"spent: {model.credits:g} kie.ai credits so far") in err
    assert [p.name for p in tmp_path.iterdir()] == [f"control-{CONTROLS[0].name}.json"]
