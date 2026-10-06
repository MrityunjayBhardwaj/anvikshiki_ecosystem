"""A second source corroborates an answer by covering it (#212): its sentence
states every claim the answer states, judged one way, in both orders shown.
Sameness was the stricter relation, and in run 5 it kept every pair across
two hosts apart."""

import json
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from occam.answer import Params, canonical, replay, run
from occam.covers import CoverPair, cover_veto, covered_by, covers_prompt
from occam.model import ScriptedModel
from occam.tests.test_answer import SUPPORT_ALL, argue_reply, attacks
from occam.types import Status
from occam.tests.test_answer import made_before_rules

AS_OF = datetime(2026, 10, 4, 12, tzinfo=timezone.utc)
QUESTION = "Where do Earth's seasons come from?"
# run 5, q02: spaceplace.nasa.gov's answer and weather.gov's sentence
ANSWER = "Earth's tilted axis causes the seasons."
SOURCE = ("The earth's spin axis is tilted with respect to its orbital plane. "
          "This is what causes the seasons.")
WEB_URL = "https://weather.test/seasons"
COVERS = json.dumps({"verdict": "covers", "missing": ""})
DOES_NOT = json.dumps({"verdict": "does_not", "missing": "the spin axis"})


def pages(wiki_sentence, web_sentence):
    def get(url):
        if url == WEB_URL:
            return 200, "text/plain", f"About the year. {web_sentence} More below.".encode()
        q = parse_qs(urlparse(url).query)
        if q.get("list") == ["search"]:
            return 200, "application/json", json.dumps(
                {"query": {"search": [{"title": "Season"}]}}).encode()
        return 200, "application/json", json.dumps({"query": {"pages": {"1": {
            "title": "Season", "extract": f"Seasons vary. {wiki_sentence} Sunsets differ."}}}}).encode()
    return get


def web_search(question, n):
    return [WEB_URL], "{raw}"


def steps(answer=ANSWER, source=SOURCE):
    return [{"id": "q1", "kind": "quote", "source": 1, "quote": answer, "conclusion": answer},
            {"id": "q2", "kind": "quote", "source": 2, "quote": source, "conclusion": source}]


def ask(judge, answer=ANSWER, source=SOURCE, **params):
    model = ScriptedModel([json.dumps({"queries": ["Season"]}), argue_reply(steps(answer, source), "q1"),
                           SUPPORT_ALL] + list(judge) + [attacks()])
    p = Params(k_argue=1, k_attack=1, web_sources=1, judge_same=False, **params)
    ans, art = run(QUESTION, model, as_of=AS_OF, http_get=pages(answer, source), params=p,
                   web_search=web_search)
    return ans, art, model


# ── the veto ───────────────────────────────────────────────

def test_a_source_that_only_adds_a_number_is_not_vetoed():
    assert cover_veto(ANSWER, "The axis is tilted by about 23.4 degrees; this causes the seasons.") == ""


def test_a_number_the_source_lacks_or_contradicts_is_vetoed():
    assert cover_veto("Wegener proposed it in 1912.", "Wegener proposed it.") == \
        "the answer states a number the source does not: 1912"
    assert cover_veto("Wegener proposed it in 1912.", "In 1915, Wegener proposed it.") == \
        "the answer states a number the source does not: 1912"
    assert cover_veto("Water boils at 50 degrees Celsius at sea level.",
                      "Water boils at 100 degrees Celsius at sea level.") != ""


def test_a_negation_on_one_side_is_vetoed():
    assert cover_veto("The bridge collapsed due to flutter.",
                      "The bridge did not collapse due to flutter.") == "negation differs: not"


# ── reading the replies ────────────────────────────────────

PAIR = CoverPair(answer="a", source="s", text_answer="A.", text_source="S.")


def test_covers_only_when_both_orders_say_so():
    assert covered_by([PAIR], [("a", "s", 0, COVERS), ("a", "s", 1, COVERS)]) == {"a": frozenset({"s"})}
    for second in (DOES_NOT, json.dumps({"verdict": "cannot_tell"}), "not json"):
        assert covered_by([PAIR], [("a", "s", 0, COVERS), ("a", "s", 1, second)]) == {}
    assert covered_by([PAIR], [("a", "s", 0, COVERS)]) == {}          # one order missing


def test_a_vetoed_pair_never_covers_whatever_is_stored():
    vetoed = PAIR.model_copy(update={"veto": "negation differs: not"})
    assert covered_by([vetoed], [("a", "s", 0, COVERS), ("a", "s", 1, COVERS)]) == {}


def test_replies_are_read_by_the_pair_they_name_not_by_position():
    other = CoverPair(answer="a", source="t", text_answer="A.", text_source="T.")
    replies = [("a", "t", 1, DOES_NOT), ("a", "s", 1, COVERS), ("a", "t", 0, DOES_NOT),
               ("a", "s", 0, COVERS)]
    assert covered_by([PAIR, other], replies) == {"a": frozenset({"s"})}


def test_the_prompt_shows_both_labelled_and_flips_only_the_order():
    p0, p1 = covers_prompt(PAIR), covers_prompt(PAIR, flip=True)
    assert p0.index("ANSWER: A.") < p0.index("SOURCE: S.")
    assert p1.index("SOURCE: S.") < p1.index("ANSWER: A.")


# ── the whole pipeline ─────────────────────────────────────

def test_a_source_on_a_second_host_that_covers_the_answer_establishes_it():
    ans, art, model = ask([COVERS, COVERS])
    assert ans.status == Status.ESTABLISHED, ans.status_bound_by
    assert [(a, s, o) for a, s, o, _ in art.cover_replies] == [
        (ANSWER.casefold(), SOURCE.casefold(), 0), (ANSWER.casefold(), SOURCE.casefold(), 1)]
    assert canonical(replay(art)) == canonical(ans)


def test_one_order_saying_does_not_keeps_the_single_source():
    ans, _, _ = ask([COVERS, DOES_NOT])
    assert ans.status == Status.HYPOTHESIS
    assert ans.status_bound_by == ("rests on a single source (en.wikipedia.org)",)


def test_without_the_check_the_same_run_rests_on_one_source():
    """The control: the run 5 shape, under the claim lens alone."""
    ans, art, _ = ask([], covers_check=1)
    assert art.cover_replies == () and ans.status == Status.HYPOTHESIS


def test_the_adversarial_pair_is_vetoed_before_any_judge():
    false, true = ("Water boils at 50 degrees Celsius at sea level.",
                   "Water boils at 100 degrees Celsius at sea level.")
    ans, art, model = ask([], answer=false, source=true)
    assert art.cover_replies == () and ans.status == Status.HYPOTHESIS
    assert not any("state everything the ANSWER" in p for p in model.prompts)


def test_covering_is_one_way():
    """The source said less than the answer: a judge saying `covers` for
    (answer, source) is the only reply read, and the source is not lifted by
    the answer it failed to cover."""
    ans, art, _ = ask([DOES_NOT, DOES_NOT],
                      answer="The tilted axis and the changing distance from the Sun cause the seasons.",
                      source="The tilted axis causes the seasons.")
    assert ans.status == Status.HYPOTHESIS
    assert {(a, s) for a, s, _, _ in art.cover_replies} == {
        ("the tilted axis and the changing distance from the sun cause the seasons.",
         "the tilted axis causes the seasons.")}


def test_an_artifact_made_before_the_check_replays_without_it():
    ans, art, _ = ask([COVERS, COVERS])
    stored = made_before_rules(json.loads(art.model_dump_json()))
    del stored["params"]["covers_check"]
    old = replay(type(art).model_validate(stored))
    assert old.status == Status.HYPOTHESIS and ans.status == Status.ESTABLISHED


# ── which pairs are asked about ────────────────────────────

def ask_steps(steps_, judge=()):
    model = ScriptedModel([json.dumps({"queries": ["Season"]}), argue_reply(steps_, "q1"),
                           SUPPORT_ALL] + list(judge) + [attacks()])
    p = Params(k_argue=1, k_attack=1, web_sources=1, judge_same=False)
    return run(QUESTION, model, as_of=AS_OF, http_get=pages(ANSWER + " " + SOURCE, SOURCE),
               params=p, web_search=web_search)[1], model


def test_a_source_on_the_answers_own_host_is_not_asked_about():
    same_host = [{"id": "q1", "kind": "quote", "source": 1, "quote": ANSWER, "conclusion": ANSWER},
                 {"id": "q2", "kind": "quote", "source": 1, "quote": SOURCE, "conclusion": SOURCE}]
    art, _ = ask_steps(same_host)
    assert art.cover_replies == ()


def test_an_answer_in_the_models_own_words_is_not_asked_about():
    restated = [{"id": "q1", "kind": "quote", "source": 1, "quote": ANSWER,
                 "conclusion": "The tilt of the axis gives us seasons."},
                {"id": "q2", "kind": "quote", "source": 2, "quote": SOURCE, "conclusion": SOURCE}]
    art, _ = ask_steps(restated)
    assert art.cover_replies == ()


def test_one_text_on_two_hosts_keeps_both_hosts():
    from types import SimpleNamespace as S
    from occam.covers import hosts_of_snapshots
    snaps = [S(id="x", urls=("https://a.test/1",)), S(id="x", urls=("https://b.test/1",))]
    assert hosts_of_snapshots(snaps) == {"x": frozenset({"a.test", "b.test"})}
