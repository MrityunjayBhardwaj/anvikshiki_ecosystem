"""A quote's conclusion must not carry the question's premise (#161).

Run 2's q04 asked "Why did the Tacoma Narrows Bridge collapse in 1940?"; argue
wrote "…collapsed in 1940 because…" over a quote that never says 1940, and the
support judge — seeing 400 characters either side, the nearest "1940" 904
away — rightly would not vouch for it. The judge stays strict: accepting
details the question supplies would vouch for a false premise. Argue is told
not to repeat them, and a counter shows whether it listens.

The model's own steps are never judged for support, so an inference can carry
the premise too (#179). It is counted, not capped: the ceilings already keep
it below `established` (test_status.py has the law), so a cap would be a
second copy of a check that can never fire.
"""

import json

from occam.answer import Artifact, Params, run
from occam.argue import Argument, adds_question_number, argue_prompt, unquoted_question_numbers
from occam.model import ScriptedModel
from occam.spans import SpanRef
from occam.tests.test_answer import AS_OF, INFER, QUERIES, SUPPORT_ALL, VIABLE, attacks, argue_reply, wiki
from occam.types import Pramana
from occam.tests.test_answer import made_before_rules

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


# ── the model's own steps (#179) ───────────────────────────

def infer(aid, conclusion, *subs, kind="inference"):
    return Argument(id=aid, conclusion=conclusion, kind=kind, sub_arguments=subs,
                    pramana={"inference": Pramana.ANUMANA, "analogy": Pramana.UPAMANA}[kind],
                    sample_ids=(0,))


def test_an_inference_carrying_the_questions_year_over_a_quote_without_it_is_counted():
    """Run 3's q01 A0001: "…broke apart in 1986 due to O-ring seal failure…"
    over quotes none of which says 1986."""
    by = {"A0000": quote_arg("Moderate winds produced flutter."),
          "A0001": infer("A0001", "It collapsed in 1940 because of flutter.", "A0000")}
    assert unquoted_question_numbers(Q04, "A0001", by) == {"1940"}


def test_a_quote_two_steps_down_that_states_it_clears_it():
    """Run 3's q04: "in 1940" rests on a quote saying "November 7, 1940"."""
    dated = quote_arg("It fell in 1940.", quote="collapsed the morning of November 7, 1940")
    by = {"A0000": dated.model_copy(update={"id": "A0000"}),
          "A0001": infer("A0001", "Flutter destroyed it.", "A0000"),
          "A0002": infer("A0002", "It collapsed in 1940 because of flutter.", "A0001")}
    assert unquoted_question_numbers(Q04, "A0002", by) == set()


def test_a_quote_on_another_branch_does_not_clear_it():
    """Only what the step rests on: a dated quote elsewhere in the run is
    not beneath this conclusion."""
    by = {"A0000": quote_arg("Moderate winds produced flutter."),
          "A0009": quote_arg("It fell in 1940.", quote="November 7, 1940").model_copy(
              update={"id": "A0009"}),
          "A0001": infer("A0001", "It collapsed in 1940.", "A0000")}
    assert unquoted_question_numbers(Q04, "A0001", by) == {"1940"}


def test_an_analogy_is_the_models_step_too():
    by = {"A0000": quote_arg("Moderate winds produced flutter."),
          "A0001": infer("A0001", "Like a flag, it failed in 1940.", "A0000", kind="analogy")}
    assert unquoted_question_numbers(Q04, "A0001", by) == {"1940"}


def test_the_quote_counter_is_the_same_predicate():
    """One predicate, two populations: a quote rests on its own words only."""
    a = quote_arg("The bridge collapsed in 1940.")
    assert adds_question_number(Q04, a) and \
        unquoted_question_numbers(Q04, a.id, {a.id: a}) == {"1940"}


def _run_infer(conclusion, question, kind="inference"):
    step = {**INFER, "kind": kind, "conclusion": conclusion}
    return run(question,
               ScriptedModel([QUERIES] + [argue_reply([VIABLE, step], "i1")] * 3
                             + [SUPPORT_ALL] + [attacks()] * 3),
               params=Params(k_argue=3, k_attack=3, judge_same=False),
               as_of=AS_OF, http_get=wiki)


def test_the_step_counter_is_shown_at_zero_with_its_denominator():
    ans, _ = _run_infer(INFER["conclusion"], "Is growth alone enough to make a business viable?")
    c = ans.counters["question_number_unquoted"]
    assert (c.n, c.of) == (0, 1) and "no quote beneath them" in c.population


def test_a_run_whose_answer_step_repeats_the_questions_year_counts_it():
    ans, _ = _run_infer("Growth alone did not make a business viable in 2024.",
                        "Is growth alone enough to make a business viable in 2024?")
    c = ans.counters["question_number_unquoted"]
    assert (c.n, c.of) == (1, 1)
    assert "2024" in ans.conclusion and ans.status.value == "hypothesis"


def test_a_run_whose_analogy_repeats_the_questions_year_counts_it():
    ans, _ = _run_infer("Like a leaky bucket, growth did not make it viable in 2024.",
                        "Is growth alone enough to make a business viable in 2024?",
                        kind="analogy")
    c = ans.counters["question_number_unquoted"]
    assert (c.n, c.of) == (1, 1)


def test_an_artifact_made_before_the_step_counter_does_not_show_it():
    """Run 2 and run 3 must replay to what they stored."""
    from occam.answer import canonical, replay
    ans, art = _run_infer(INFER["conclusion"], "Is growth alone enough to make a business viable?")
    old = made_before_rules(json.loads(art.model_dump_json()))
    del old["params"]["counter_set"]
    a = Artifact.model_validate(old)
    assert a.params.counter_set == 1
    got = replay(a)
    assert "question_number_unquoted" not in got.counters
    assert "question_number_added" in got.counters          # prompt 2's counter kept
    assert canonical(replay(art)) == canonical(ans)


# ── what the counters can see (#181) ──────────────────────

def test_on_a_question_without_a_number_both_counters_say_they_cannot_fire():
    """8 of run 3's 10 questions: a zero there is "could not look"."""
    ans, _ = _run_infer(INFER["conclusion"], "Is growth alone enough to make a business viable?")
    for name in ("question_number_added", "question_number_unquoted"):
        c = ans.counters[name]
        assert c.population.endswith("; the question has no whole number, so this cannot fire"), name


def test_on_a_question_with_a_number_both_counters_name_what_they_check():
    ans, _ = _run_infer(INFER["conclusion"],
                        "Is growth alone enough to make a business viable in 2024?")
    for name in ("question_number_added", "question_number_unquoted"):
        assert ans.counters[name].population.endswith(
            "; the question has 1 whole number(s) to check (2024)"), name


def test_an_artifact_made_under_counter_set_2_replays_as_it_was_made():
    """#180's artifacts: the counter, without the clause added after them."""
    from occam.answer import canonical, replay
    _, art = _run_infer(INFER["conclusion"], "Is growth alone enough to make a business viable?")
    assert art.params.counter_set == 3
    two = Artifact.model_validate({**json.loads(art.model_dump_json()),
                                   "params": {**json.loads(art.params.model_dump_json()),
                                              "counter_set": 2}})
    got = replay(two).counters
    assert "question_number_unquoted" in got
    assert all("the question has" not in got[n].population
               for n in ("question_number_added", "question_number_unquoted"))
