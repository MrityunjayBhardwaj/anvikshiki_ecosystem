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
