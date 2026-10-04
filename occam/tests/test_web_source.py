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


def test_an_artifact_made_before_web_sources_reads_as_wikipedia_only():
    _, art = ask_web([WIKI_QUOTE], [WEB_URL])
    stored = json.loads(art.model_dump_json())
    del stored["params"]["web_sources"]
    assert type(art).model_validate(stored).params.web_sources == 0
