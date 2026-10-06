"""A quoted answer to a question asking for a cause must give the reason
(#194): its words carry the link, and a fresh judge call says it answers
this question. Otherwise it stays at hypothesis, and says why."""

import json
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from occam.answer import Params, canonical, replay, run
from occam.model import ScriptedModel
from occam.reason import asks_for_a_cause, reason_prompt, states_a_link
from occam.tests.test_answer import SUPPORT_ALL, argue_reply, attacks
from occam.types import Status
from occam.tests.test_answer import made_before_rules

AS_OF = datetime(2026, 10, 4, 12, tzinfo=timezone.utc)
WHY = "Why is the sky blue?"
LINKED = "Blue light is scattered more than other colors because it travels as shorter, smaller waves."
UNLINKED = "Blue light is scattered more than other colors. It travels as shorter, smaller waves."
WEB_URL = "https://sky.test/blue"


def pages(sentence):
    text = f"The sky is studied by many. {sentence} Sunsets are red."

    def get(url):
        if url == WEB_URL:
            return 200, "text/plain", f"Ask an astronomer. {sentence} More below.".encode()
        q = parse_qs(urlparse(url).query)
        if q.get("list") == ["search"]:
            return 200, "application/json", json.dumps(
                {"query": {"search": [{"title": "Diffuse sky radiation"}]}}).encode()
        return 200, "application/json", json.dumps(
            {"query": {"pages": {"1": {"title": "x", "extract": text}}}}).encode()
    return get


def web_search(question, n):
    return [WEB_URL], "{raw}"


def quotes(conclusion, quote=None):
    quote = quote or conclusion
    return [{"id": "q1", "kind": "quote", "source": 1, "quote": quote, "conclusion": conclusion},
            {"id": "q2", "kind": "quote", "source": 2, "quote": quote, "conclusion": conclusion}]


def ask(question, steps, judge, sentence=LINKED, params=None):
    model = ScriptedModel([json.dumps({"queries": ["sky"]}), argue_reply(steps, "q1"), SUPPORT_ALL]
                          + list(judge) + [attacks()])
    p = params or Params(k_argue=1, k_attack=1, web_sources=1)
    ans, art = run(question, model, as_of=AS_OF, http_get=pages(sentence), params=p,
                   web_search=web_search)
    return ans, art, model


GIVES = json.dumps({"verdict": "gives_reason"})
DOES_NOT = json.dumps({"verdict": "does_not"})


# ── the two text predicates ────────────────────────────────

def test_a_question_asks_for_a_cause_by_why_or_a_caus_word():
    for q in (WHY, "What causes the seasons on Earth?", "What caused the extinction?",
              "What is the main cause of the Aurora Borealis?"):
        assert asks_for_a_cause(q), q
    for q in ("Who proposed continental drift, and when?", "What was the Rosetta Stone used "
              "to decipher?", "When was the causeway built?"):
        assert not asks_for_a_cause(q), q


def test_a_link_is_matched_on_whole_words():
    assert states_a_link(LINKED)
    assert states_a_link("The collapse was caused by aeroelastic flutter.")
    assert states_a_link("Seasons result from the tilt; the tilt is responsible for them.")
    assert not states_a_link(UNLINKED)                       # side by side, no link
    assert not states_a_link("The causeway has stood since 1940.")   # not a word, not a cause
    # The live reply that showed "since" was needed, and its neighbours:
    assert states_a_link("Since blue light wavelengths scatter more, the diffuse sky seen "
                         "in daytime is blue.")
    assert not states_a_link("It has been studied since 1871.")
    assert not states_a_link("Sincerely, the sky.")


# ── end to end ─────────────────────────────────────────────

def test_a_quote_stating_the_reason_on_two_hosts_is_established():
    ans, art, _ = ask(WHY, quotes(LINKED), [GIVES])
    assert ans.status == Status.ESTABLISHED, ans.status_bound_by
    assert art.reason_replies == (("A0000", GIVES),)
    assert canonical(replay(art)) == canonical(ans)


def test_cause_and_effect_with_no_link_stay_a_hypothesis_and_the_judge_is_not_asked():
    """The case #194 says must stay red."""
    ans, art, _ = ask(WHY, quotes(UNLINKED), [], sentence=UNLINKED)
    assert ans.status == Status.HYPOTHESIS
    assert ans.status_bound_by == (f"quote {ans.answer_id} answers a question asking for a "
                                   f"cause, but its words state no causal link",)
    assert art.reason_replies == ()


def test_a_linked_quote_the_judge_says_does_not_answer_stays_a_hypothesis():
    ans, _, _ = ask(WHY, quotes(LINKED), [DOES_NOT])
    assert ans.status == Status.HYPOTHESIS
    assert ans.status_bound_by == (f"quote {ans.answer_id}: the judge said it does not give "
                                   f"the reason asked for",)


def test_doubt_never_lifts():
    for reply, said in (("not json", "no readable reply from the reason judge"),
                        (json.dumps({"verdict": "cannot_tell"}),
                         "the judge could not tell if it gives the reason asked for")):
        ans, _, _ = ask(WHY, quotes(LINKED), [reply])
        assert ans.status == Status.HYPOTHESIS
        assert ans.status_bound_by == (f"quote {ans.answer_id}: {said}",)


def test_a_question_not_asking_for_a_cause_is_not_judged():
    q = "What colour is the sky?"
    ans, art, model = ask(q, quotes(LINKED), [])
    assert art.reason_replies == () and ans.status == Status.ESTABLISHED
    assert not any("Does the STATEMENT give the reason" in p for p in model.prompts)


def test_the_judge_sees_the_question_and_that_one_statement():
    p = reason_prompt(WHY, LINKED)
    assert f"QUESTION: {WHY}" in p and f"STATEMENT (copied from a source): {LINKED}" in p


def test_the_bound_ties_with_one_already_there():
    """On Wikipedia alone the single source binds too: both are named."""
    model = ScriptedModel([json.dumps({"queries": ["sky"]}),
                           argue_reply(quotes(LINKED)[:1], "q1"), SUPPORT_ALL, DOES_NOT, attacks()])
    ans, _ = run(WHY, model, as_of=AS_OF, http_get=pages(LINKED),
                 params=Params(k_argue=1, k_attack=1))
    assert set(ans.status_bound_by) == {
        "rests on a single source (en.wikipedia.org)",
        f"quote {ans.answer_id}: the judge said it does not give the reason asked for"}


def test_an_artifact_made_before_the_check_replays_without_it():
    ans, art, _ = ask(WHY, quotes(LINKED), [DOES_NOT])
    stored = made_before_rules(json.loads(art.model_dump_json()))
    del stored["params"]["why_check"]
    old = replay(type(art).model_validate(stored))
    assert old.status == Status.ESTABLISHED and ans.status == Status.HYPOTHESIS


# ── #213: a "since" links only where it opens a clause ─────

Q07 = ("Death by asteroid rather than by a series of volcanic eruptions or some other global "
       "calamity has been the leading hypothesis since the 1980s, when scientists found "
       "asteroid dust in the geologic layer that marks the extinction of the dinosaurs.")


def test_a_since_about_time_is_no_link_under_rule_3():
    assert not states_a_link(Q07)                            # run 5, q07: time, not cause
    assert not states_a_link("Since 1940, the bridge has been rebuilt twice.")
    assert not states_a_link("The sky has looked blue ever since the dawn of time.")
    # where it opens the text or a clause, it can link
    assert states_a_link("Since blue light wavelengths scatter more, the diffuse sky seen "
                         "in daytime is blue.")              # run 5, q08
    assert states_a_link("The sky is blue, since blue light is scattered most.")
    assert states_a_link("The sky is blue (since blue light is scattered most).")


def test_rule_2_keeps_its_own_answer_so_old_runs_replay():
    assert states_a_link(Q07, rule=2)


Q07_QUESTION = "What caused the extinction of the dinosaurs?"


def test_under_rule_3_a_time_since_stays_a_hypothesis_and_the_judge_is_not_asked():
    ans, art, model = ask(Q07_QUESTION, quotes(Q07), [], sentence=Q07)
    assert ans.status == Status.HYPOTHESIS
    assert ans.status_bound_by == (f"quote {ans.answer_id} answers a question asking for a "
                                   f"cause, but its words state no causal link",)
    assert art.reason_replies == ()
    assert canonical(replay(art)) == canonical(ans)


def test_a_run_made_under_rule_2_replays_under_rule_2():
    ans, art, _ = ask(Q07_QUESTION, quotes(Q07), [GIVES], sentence=Q07,
                      params=Params(k_argue=1, k_attack=1, web_sources=1, why_check=2))
    assert art.params.why_check == 2 and art.reason_replies == (("A0000", GIVES),)
    assert ans.status == Status.ESTABLISHED
    assert canonical(replay(art)) == canonical(ans)
