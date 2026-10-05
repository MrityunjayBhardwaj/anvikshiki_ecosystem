"""A second source found on the web (#209): the search only discovers URLs;
every page is fetched, snapshotted and quoted by us like any other, so each
existing check applies to it — and corroboration across hosts becomes
reachable, which Wikipedia alone never allows."""

import json

from occam.answer import Params, replay, canonical, run
from occam.gather import gather
from occam.model import ScriptedModel
from occam.tests.test_answer import (AS_OF, QUERIES, SUPPORT_ALL, VIABLE, argue_reply, attacks,
                                     wiki)
from occam.types import Status

SENTENCE = VIABLE["quote"]
WEB_URL = "https://econ.test/unit-economics"
WEB_HTML = (f"<html><head><title>x</title><script>var s=1;</script></head><body>"
            f"<p>Analysts say this often.</p><p>{SENTENCE}</p><p>Other matters follow.</p>"
            f"</body></html>").encode()


def web_and_wiki(url):
    if url == WEB_URL:
        return 200, "text/html; charset=utf-8", WEB_HTML
    if url.startswith("https://down.test/"):
        return 403, "text/html", b"forbidden"
    return wiki(url)


def search(found, reply="{raw search reply}"):
    calls = []

    def web_search(question, n):
        calls.append((question, n))
        return list(found), reply
    web_search.calls = calls
    return web_search


# ── gather ─────────────────────────────────────────────────

def test_web_pages_follow_wikipedias_and_the_raw_reply_is_kept_for_audit():
    ws = search([WEB_URL, "https://down.test/a"])
    snaps, notes, raw = gather("Is growth enough?", at=AS_OF, n=2, http_get=web_and_wiki,
                               model=ScriptedModel([QUERIES]), web_search=ws, n_web=2)
    assert [s.urls[0] for s in snaps[2:]] == [WEB_URL, "https://down.test/a"]
    assert all("wikipedia.org" in s.urls[0] for s in snaps[:2])
    assert SENTENCE in snaps[2].text and "var s" not in snaps[2].text   # read by our parser
    assert snaps[3].text == "" and snaps[3].empty_reason == "HTTP 403"  # could not look, said so
    assert raw == [QUERIES, "{raw search reply}"]
    assert ws.calls == [("Is growth enough?", 2)]


def test_no_more_than_n_web_pages_are_fetched():
    snaps, _, _ = gather("q", at=AS_OF, n=2, http_get=web_and_wiki,
                         web_search=search([WEB_URL, "https://down.test/a"]), n_web=1)
    assert [s.urls[0] for s in snaps[2:]] == [WEB_URL]


def test_a_wikipedia_or_mirror_page_from_the_web_search_is_skipped_and_said():
    found = ["https://de.wikipedia.org/wiki/St%C3%BCckkosten", "https://www.wikiwand.com/en/x",
             "https://notwikiwand.com/a", WEB_URL]
    snaps, notes, _ = gather("q", at=AS_OF, n=2, http_get=web_and_wiki,
                             web_search=search(found), n_web=4)
    # a host that merely ends in a mirror's name is not that mirror
    assert [s.urls[0] for s in snaps[2:]] == ["https://notwikiwand.com/a", WEB_URL]
    assert "web search: skipped 2 Wikipedia or mirror page(s)" in notes


def test_a_search_that_finds_nothing_or_fails_is_a_note_never_silence():
    _, notes, raw = gather("q", at=AS_OF, n=2, http_get=web_and_wiki,
                           web_search=search([]), n_web=2)
    assert "web search returned no pages beyond Wikipedia for 'q'" in notes

    def broken(question, n):
        raise RuntimeError("HTTP 402")
    snaps, notes, raw = gather("q", at=AS_OF, n=2, http_get=web_and_wiki,
                               web_search=broken, n_web=2)
    assert "web search failed: RuntimeError: HTTP 402" in notes and len(snaps) == 2


# ── fill rule 2: ask for more, keep what loads (#216) ──────

def counted_get():
    """Text on any live.test host, 404 on dead.test or a /gone page, 403 on
    down.test; and the URLs fetched, in order."""
    fetched = []

    def get(url):
        fetched.append(url)
        if "dead.test" in url or url.endswith("/gone"):
            return 404, "text/html", b"not found"
        if "live" in url:
            return 200, "text/html", f"<p>{SENTENCE} ({url})</p>".encode()
        return web_and_wiki(url)
    get.fetched = fetched
    return get


def web_only(found, n_web, fill=2):
    get = counted_get()
    ws = search(found)
    snaps, notes, _ = gather("q", at=AS_OF, urls=None, n=0, http_get=get, web_search=ws,
                             n_web=n_web, web_fill=fill)
    return snaps, notes, ws, [u for u in get.fetched if "wikipedia" not in u]


def test_rule_2_asks_for_three_times_as_many_and_fills_past_dead_links():
    found = ["https://dead.test/a", "https://a.live.test/1", "https://down.test/b",
             "https://b.live.test/1", "https://c.live.test/1", "https://d.live.test/1"]
    snaps, notes, ws, fetched = web_only(found, n_web=2)
    assert ws.calls == [("q", 6)]
    assert fetched == found[:4]                                   # stops once 2 are held
    assert [s.urls[0] for s in snaps] == found[:4]                # failures stay on the record
    assert [bool(s.text) for s in snaps] == [False, True, False, True]
    assert ("web search: named 6; readable on distinct hosts 2 of 2 wanted, 1 HTTP 403, "
            "1 HTTP 404; skipped 0 on a host already held; not fetched 2") in notes


def test_rule_2_does_not_fetch_a_second_page_on_a_host_already_held():
    found = ["https://a.live.test/1", "https://a.live.test/2", "https://b.live.test/1"]
    snaps, notes, _, fetched = web_only(found, n_web=2)
    assert fetched == ["https://a.live.test/1", "https://b.live.test/1"]
    assert "skipped 1 on a host already held" in notes[-1]


def test_rule_2_still_fetches_a_host_whose_first_page_was_dead():
    found = ["https://a.live.test/gone", "https://a.live.test/1", "https://b.live.test/1"]
    snaps, notes, _, fetched = web_only(found, n_web=2)
    assert fetched == found                       # a dead page holds no host
    assert [bool(s.text) for s in snaps] == [False, True, True]


def test_rule_2_with_too_few_readable_says_so():
    snaps, notes, _, _ = web_only(["https://dead.test/a", "https://down.test/b"], n_web=3)
    assert len(snaps) == 2 and not any(s.text for s in snaps)
    assert notes[-1] == ("web search: named 2; readable on distinct hosts 0 of 3 wanted, "
                         "1 HTTP 403, 1 HTTP 404; skipped 0 on a host already held; "
                         "not fetched 0")


def test_rule_1_is_unchanged_whatever_loads():
    found = ["https://dead.test/a", "https://a.live.test/1", "https://b.live.test/1"]
    snaps, notes, ws, fetched = web_only(found, n_web=2, fill=1)
    assert ws.calls == [("q", 2)] and fetched == found[:2]
    assert not any(n.startswith("web search: named") for n in notes)


def test_given_urls_nothing_is_searched():
    ws = search([WEB_URL])
    snaps, _, _ = gather("q", at=AS_OF, urls=["https://down.test/b"], http_get=web_and_wiki,
                         web_search=ws, n_web=3)
    assert ws.calls == [] and len(snaps) == 1


# ── the whole pipeline ─────────────────────────────────────

QUESTION = "Is growth alone enough to make a business viable?"
WIKI_QUOTE = {"id": "q1", "kind": "quote", "source": 1, "quote": SENTENCE, "conclusion": SENTENCE}
WEB_QUOTE = {"id": "q2", "kind": "quote", "source": 3, "quote": SENTENCE, "conclusion": SENTENCE}


def ask_web(steps, found):
    model = ScriptedModel([QUERIES] + [argue_reply(steps, "q1")] * 3 + [SUPPORT_ALL]
                          + [attacks()] * 3)
    return run(QUESTION, model, as_of=AS_OF, http_get=web_and_wiki,
               params=Params(web_sources=3), web_search=search(found))


def test_the_same_words_on_a_second_host_establish_the_answer():
    ans, art = ask_web([WIKI_QUOTE, WEB_QUOTE], [WEB_URL])
    assert art.params.web_sources == 3
    assert ans.status == Status.ESTABLISHED, ans.status_bound_by
    assert canonical(replay(art)) == canonical(ans)            # replay never searches


def test_the_same_words_on_wikipedia_alone_stay_a_hypothesis():
    """The control: drop the web quote and the single source binds."""
    ans, _ = ask_web([WIKI_QUOTE], [WEB_URL])
    assert ans.status == Status.HYPOTHESIS
    assert ans.status_bound_by == ("rests on a single source (en.wikipedia.org)",)


def test_without_a_search_the_params_say_no_web_pages_were_asked_for():
    model = ScriptedModel([QUERIES] + [argue_reply([WIKI_QUOTE], "q1")] * 3 + [SUPPORT_ALL]
                          + [attacks()] * 3)
    _, art = run(QUESTION, model, as_of=AS_OF, http_get=web_and_wiki, params=Params(web_sources=3))
    assert art.params.web_sources == 0
    assert all("wikipedia.org" in s.urls[0] for s in art.snapshots)


def test_a_run_fills_under_rule_2_and_says_so():
    found = ["https://dead.test/a", WEB_URL]
    model = ScriptedModel([QUERIES] + [argue_reply([WIKI_QUOTE, WEB_QUOTE], "q1")] * 3
                          + [SUPPORT_ALL] + [attacks()] * 3)
    ws = search(found)
    ans, art = run(QUESTION, model, as_of=AS_OF, http_get=counted_get(),
                   params=Params(web_sources=1), web_search=ws)
    assert art.params.web_fill == 2 and ws.calls == [(QUESTION, 3)]
    assert [s.urls[0] for s in art.snapshots[-2:]] == found
    assert any(d.startswith("web search: named 2; readable on distinct hosts 1 of 1")
               for d in ans.degraded)
    assert canonical(replay(art)) == canonical(ans)


def test_an_artifact_made_before_web_fill_reads_as_rule_1():
    _, art = ask_web([WIKI_QUOTE], [WEB_URL])
    stored = json.loads(art.model_dump_json())
    del stored["params"]["web_fill"]
    assert type(art).model_validate(stored).params.web_fill == 1


def test_an_artifact_made_before_web_sources_reads_as_wikipedia_only():
    _, art = ask_web([WIKI_QUOTE], [WEB_URL])
    stored = json.loads(art.model_dump_json())
    del stored["params"]["web_sources"]
    assert type(art).model_validate(stored).params.web_sources == 0
