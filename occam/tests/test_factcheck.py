"""Fact-check articles as sources (#230): the service only discovers; each
article is fetched, snapshotted and quoted by us like any page, its rating is
never read by anything that decides, and the API key reaches nothing stored."""

import json
import urllib.parse

import pytest

from occam.__main__ import main
from occam.answer import Params, canonical, replay, run
from occam.factcheck import CLAIMS_SEARCH, FactCheckError, claims, factcheck_search, review_urls
from occam.gather import gather
from occam.model import ScriptedModel
from occam.tests.test_answer import AS_OF, QUERIES, SUPPORT_ALL, argue_reply, attacks
from occam.tests.test_web_source import (QUESTION, SENTENCE, WEB_HTML, WEB_URL, WIKI_QUOTE,
                                         search, web_and_wiki)
from occam.types import Status

KEY = "SECRET-KEY-do-not-store"
FC_URL = "https://checker.test/review/1"
FC_URL_2 = "https://checker.test/review/2"          # same host as FC_URL
FC_OTHER = "https://other-checker.test/r"
RATING = "Pants on Fire"
FC_HTML = (f"<html><body><h1>Fact check</h1><p>{SENTENCE}</p></body></html>").encode()


def claim(*urls, rating=RATING):
    return {"text": "a claim", "claimReview": [
        {"publisher": {"site": "x"}, "url": u, "textualRating": rating} for u in urls]}


def api(pages, status=200):
    """A scripted claims:search: page i of `pages`, chained by tokens."""
    seen = []

    def get(url):
        if url.startswith(CLAIMS_SEARCH):
            q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
            seen.append(q)
            if status != 200:
                return status, "application/json", b'{"error": "blocked"}'
            i = int(q.get("pageToken", "0"))
            body = {"claims": pages[i]}
            if i + 1 < len(pages):
                body["nextPageToken"] = str(i + 1)
            return 200, "application/json", json.dumps(body).encode()
        if url in (FC_URL, FC_URL_2, FC_OTHER):
            return 200, "text/html", FC_HTML
        return web_and_wiki(url)
    get.seen = seen
    return get


# ── the search ─────────────────────────────────────────────

def test_review_urls_keep_the_services_order_once_each():
    found = [claim(FC_URL, FC_OTHER), claim(FC_URL), {"claimReview": [{"url": "javascript:x"}]}]
    assert review_urls(found) == [FC_URL, FC_OTHER]


def test_the_search_reads_more_pages_only_until_it_holds_enough():
    get = api([[claim(FC_URL)], [claim(FC_OTHER)], [claim(FC_URL_2)]])
    urls, raw = factcheck_search(KEY, http_get=get)("Do vaccines cause autism?", 2)
    assert urls == [FC_URL, FC_OTHER] and len(get.seen) == 2
    assert get.seen[0]["query"] == "Do vaccines cause autism?"     # sent as written
    assert len(json.loads(raw)) == 2


def test_the_search_stops_at_three_pages():
    get = api([[claim(f"https://h{i}.test/a")] for i in range(5)])
    urls, _ = factcheck_search(KEY, http_get=get)("q", 9)
    assert len(urls) == 3 and len(get.seen) == 3


def test_a_refusal_is_an_error_that_never_carries_the_key():
    with pytest.raises(FactCheckError) as e:
        claims("q", key=KEY, http_get=api([], status=403))
    assert "HTTP 403" in str(e.value) and KEY not in str(e.value)

    def down(url):
        raise OSError(f"could not reach {url}")                    # a message holding the URL
    with pytest.raises(FactCheckError) as e:
        claims("q", key=KEY, http_get=down)
    assert KEY not in str(e.value) and e.value.__cause__ is None


# ── gather ─────────────────────────────────────────────────

def test_articles_are_fetched_after_the_web_pages_on_hosts_not_already_held():
    get = api([[claim(FC_URL, FC_URL_2, FC_OTHER)]])
    snaps, notes, raw = gather("q", at=AS_OF, n=2, http_get=get,
                               web_search=search([WEB_URL]), n_web=1,
                               factcheck_search=factcheck_search(KEY, http_get=get),
                               n_factcheck=2, web_fill=2)
    assert [s.urls[0] for s in snaps[2:]] == [WEB_URL, FC_URL, FC_OTHER]   # FC_URL_2's host held
    assert any(n.startswith("fact-check search: named 3; readable on distinct hosts 2 of 2 wanted; "
                            "skipped 1 on a host already held") for n in notes)


def test_a_host_the_web_search_holds_is_not_fetched_again():
    get = api([[claim(WEB_URL, FC_OTHER)]])
    snaps, _, _ = gather("q", at=AS_OF, n=2, http_get=get, web_search=search([WEB_URL]),
                         n_web=1, factcheck_search=factcheck_search(KEY, http_get=get),
                         n_factcheck=2, web_fill=2)
    assert [s.urls[0] for s in snaps[2:]] == [WEB_URL, FC_OTHER]


def test_a_blocked_search_is_a_note_without_the_key():
    get = api([], status=403)
    snaps, notes, _ = gather("q", at=AS_OF, n=2, http_get=get,
                             factcheck_search=factcheck_search(KEY, http_get=get), n_factcheck=2)
    assert "fact-check search failed: FactCheckError: fact-check search answered HTTP 403" in notes
    assert len(snaps) == 2 and not any(KEY in n for n in notes)


def test_without_n_factcheck_nothing_is_searched():
    get = api([[claim(FC_URL)]])
    gather("q", at=AS_OF, n=2, http_get=get,
           factcheck_search=factcheck_search(KEY, http_get=get), n_factcheck=0)
    assert get.seen == []


# ── the whole pipeline ─────────────────────────────────────

FC_QUOTE = {"id": "q2", "kind": "quote", "source": 3, "quote": SENTENCE, "conclusion": SENTENCE}


def ask_fc(steps, get=None):
    get = get or api([[claim(FC_URL)]])
    model = ScriptedModel([QUERIES] + [argue_reply(steps, "q1")] * 3 + [SUPPORT_ALL]
                          + [attacks()] * 3)
    ans, art = run(QUESTION, model, as_of=AS_OF, http_get=get,
                   params=Params(factcheck_sources=1),
                   factcheck_search=factcheck_search(KEY, http_get=get))
    return ans, art, model


def test_a_fact_check_article_is_a_second_host_and_can_establish_the_answer():
    ans, art, _ = ask_fc([WIKI_QUOTE, FC_QUOTE])
    assert art.params.factcheck_sources == 1 and art.snapshots[-1].urls == (FC_URL,)
    assert ans.status == Status.ESTABLISHED, ans.status_bound_by
    assert canonical(replay(art)) == canonical(ans)              # replay never searches


def test_the_rating_is_kept_for_audit_and_never_shown_to_the_model():
    _, art, model = ask_fc([WIKI_QUOTE, FC_QUOTE])
    assert any(RATING in r for r in art.gather_replies)
    assert not any(RATING in p for p in model.prompts)
    assert not any(RATING in s.text for s in art.snapshots)


def test_the_key_reaches_nothing_stored():
    ans, art, _ = ask_fc([WIKI_QUOTE, FC_QUOTE])
    assert KEY not in art.model_dump_json() and KEY not in ans.model_dump_json()


def test_without_a_search_the_params_say_none_were_asked_for():
    model = ScriptedModel([QUERIES] + [argue_reply([WIKI_QUOTE], "q1")] * 3 + [SUPPORT_ALL]
                          + [attacks()] * 3)
    _, art = run(QUESTION, model, as_of=AS_OF, http_get=web_and_wiki,
                 params=Params(factcheck_sources=2))
    assert art.params.factcheck_sources == 0


def test_an_artifact_made_before_factcheck_sources_reads_as_none():
    _, art, _ = ask_fc([WIKI_QUOTE])
    stored = json.loads(art.model_dump_json())
    del stored["params"]["factcheck_sources"]
    assert type(art).model_validate(stored).params.factcheck_sources == 0


# ── the command line ───────────────────────────────────────

class Built(Exception):
    pass


@pytest.mark.parametrize("cmd", [["measure"], ["ask", "q?"]])
def test_factcheck_without_a_key_is_refused_before_any_model(tmp_path, monkeypatch, cmd):
    import occam.model as om
    monkeypatch.delenv("GOOGLE_FACTCHECK_API_KEY", raising=False)
    monkeypatch.setattr(om, "make_model", lambda spec: (_ for _ in ()).throw(Built()))
    out = tmp_path / ("run" if cmd[0] == "measure" else "a.json")
    assert main(cmd + ["--factcheck", "2", "--out", str(out)]) == 2


def test_factcheck_with_a_key_goes_on_to_build_the_model(tmp_path, monkeypatch):
    import occam.model as om
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", KEY)
    monkeypatch.setattr(om, "make_model", lambda spec: (_ for _ in ()).throw(Built()))
    with pytest.raises(Built):
        main(["measure", "--factcheck", "2", "--out", str(tmp_path / "run")])
