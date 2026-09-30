"""A quote's conclusion must not carry the question's premise (#161).

Run 2's q04 asked "Why did the Tacoma Narrows Bridge collapse in 1940?"; argue
wrote "…collapsed in 1940 because…" over a quote that never says 1940, and the
support judge — seeing 400 characters either side, the nearest "1940" 904
away — rightly would not vouch for it. The judge stays strict: accepting
details the question supplies would vouch for a false premise. Argue is told
not to repeat them, and a counter shows whether it listens.
"""

import json

from occam.answer import Artifact, Params, run
from occam.argue import Argument, adds_question_number, argue_prompt
from occam.model import ScriptedModel
from occam.spans import SpanRef
from occam.tests.test_answer import AS_OF, QUERIES, SUPPORT_ALL, VIABLE, attacks, argue_reply, wiki
from occam.types import Pramana

Q04 = "Why did the Tacoma Narrows Bridge collapse in 1940?"
QUOTE = ("the bridge collapsed because moderate winds produced aeroelastic flutter "
         "that was self-exciting and unbounded")


def quote_arg(conclusion, quote=QUOTE):
    span = SpanRef(snapshot_id="S0", text_sha256="0" * 64, start=0, end=len(quote),
                   quote=quote, checked=True, verdict="ok")
    return Argument(id="A0000", conclusion=conclusion, kind="quote", span=span,
                    pramana=Pramana.SABDA, sample_ids=(0,))


def test_run_2s_dropped_claim_is_counted():
    a = quote_arg("The Tacoma Narrows Bridge collapsed in 1940 because moderate winds "
                  "produced a self-exciting and unbounded aeroelastic flutter.")
    assert adds_question_number(Q04, a)


def test_a_conclusion_that_only_answers_why_is_not_counted():
    assert not adds_question_number(Q04, quote_arg(
        "The bridge collapsed because moderate winds produced self-exciting flutter."))


def test_a_number_the_quote_itself_states_is_not_counted():
    q = "On 7 November 1940 the bridge collapsed because of flutter"
    assert not adds_question_number(Q04, quote_arg("The bridge collapsed in 1940 because "
                                                   "of flutter.", quote=q))


def test_a_number_not_in_the_question_is_not_this_counter():
    """Numbers the question never mentioned are the support judge's business."""
    assert not adds_question_number(Q04, quote_arg("It collapsed at 35 mph winds."))


def test_inferences_are_not_counted():
    a = quote_arg("It collapsed in 1940.").model_copy(update={"kind": "inference",
                                                              "span": None})
    assert not adds_question_number(Q04, a)


def test_the_argue_prompt_says_so():
    p = argue_prompt(Q04, [])
    assert "Do not repeat details from the question" in p


def _run(conclusion, question="Is growth alone enough to make a business viable?",
         judge=SUPPORT_ALL, **params):
    return run(question,
               ScriptedModel([QUERIES] + [argue_reply([{**VIABLE, "conclusion": conclusion}],
                                                      "q1")] * 3
                             + [judge] + [attacks()] * 3),
               params=Params(k_argue=3, k_attack=3, judge_same=False, **params),
               as_of=AS_OF, http_get=wiki)


def test_the_counter_is_shown_at_zero_with_its_denominator():
    ans, _ = _run(VIABLE["conclusion"])
    c = ans.counters["question_number_added"]
    # three samples quoting the same span in the same words are one argument
    assert (c.n, c.of) == (0, 1) and "before the support judge" in c.population


def test_an_artifact_argued_under_the_first_prompt_shows_no_new_counter():
    _, art = _run(VIABLE["conclusion"])
    old = json.loads(art.model_dump_json())
    del old["params"]["argue_prompt"]                    # as every artifact before #161
    from occam.answer import replay
    a = Artifact.model_validate(old)
    assert a.params.argue_prompt == 1
    assert "question_number_added" not in replay(a).counters


def test_a_run_whose_quote_conclusion_repeats_the_questions_year_counts_it():
    ans, _ = _run("Viability requires LTV to exceed CAC in 2024.",
                  question="Is growth alone enough to make a business viable in 2024?")
    c = ans.counters["question_number_added"]
    assert (c.n, c.of) == (1, 1)


def test_it_counts_the_argument_the_support_judge_then_drops():
    """Run 2's case exactly: the claim carrying the question's year is the one
    support drops, so counting after support would never see it."""
    reject = json.dumps({"judgments": [{"id": "A0000", "verdict": "does_not_support"}]})
    ans, _ = _run("Viability requires LTV to exceed CAC in 2024.",
                  question="Is growth alone enough to make a business viable in 2024?",
                  judge=reject)
    assert ans.counters["support_dropped"].n == 1
    c = ans.counters["question_number_added"]
    assert (c.n, c.of) == (1, 1)
