"""The validation controls, run offline with scripted replies (#145).

A control that cannot go red is not a control. Each one here is run with a
scripted model whose replies exercise exactly the failure the control exists
to catch, and the mutation suite breaks the pipeline in that way.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

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
