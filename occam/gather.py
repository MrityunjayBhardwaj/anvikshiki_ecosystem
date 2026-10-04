"""Stage 1 — gather: search, fetch, snapshot (#143).

Everything downstream is addressed to what this stage stores, so it records
failure as carefully as success. A page that could not be fetched becomes a
snapshot with no text and a stated reason — never a missing entry, because
"could not look" and "looked and found nothing" call for opposite actions.

Search is Wikipedia's public API: no key, a real index, and plain-text
extracts, so no HTML has to be interpreted for the common case. Arbitrary
URLs are fetched and their HTML reduced to text with the standard library's
parser — no regular expressions, which the package forbids.

The network is injected (`http_get`), so the laws run offline and a control
can script exactly the page it is testing.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from typing import TYPE_CHECKING, Callable, Optional, Sequence

from .snapshot import WIKIPEDIA_EXTRACTOR, Snapshot, capture, host

if TYPE_CHECKING:
    from .model import Model

__all__ = ["HttpGet", "WebSearch", "EXCLUDED_HOSTS", "gather", "fetch", "wikipedia_search", "search_queries",
           "html_to_text", "urllib_get"]

# (url) -> (status, content_type, body). Raises on network failure.
HttpGet = Callable[[str], tuple[int, str, bytes]]
# (question, n) -> (urls found, raw reply kept for audit). OpenRouterModel.web_search.
WebSearch = Callable[[str, int], tuple[list[str], str]]
# Wikipedia is gathered on its own, and a mirror of it would count as a second
# host while repeating the first (#209). The search is asked to leave these
# out, and gather drops any that come back anyway: the request is a saving,
# this filter is the guarantee.
EXCLUDED_HOSTS = ("wikipedia.org", "wikiwand.com", "wikizero.com", "dbpedia.org")


def _excluded(url: str) -> bool:
    h = host(url)
    return any(h == d or h.endswith("." + d) for d in EXCLUDED_HOSTS)

USER_AGENT = "occam-anvikshiki/0.1 (research prototype; https://github.com/MrityunjayBhardwaj/anvikshiki_ecosystem)"
WIKI_API = "https://en.wikipedia.org/w/api.php"


def urllib_get(url: str, timeout: float = 30.0) -> tuple[int, str, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", "") if e.headers else "", e.read() or b""


class _Text(HTMLParser):
    _SKIP = {"script", "style", "noscript", "svg", "head", "template"}
    _BLOCK = {"p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5",
              "h6", "tr", "table", "section", "article", "blockquote", "pre"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip += 1
        elif tag in self._BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip:
            self._skip -= 1
        elif tag in self._BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    """Visible text, one block per line. Deterministic for a given input."""
    p = _Text()
    p.feed(html)
    lines = (" ".join(line.split()) for line in "".join(p.parts).split("\n"))
    return "\n".join(line for line in lines if line)


def _failed(url: str, reason: str, at: datetime) -> Snapshot:
    # The body records the failure itself, so two different failures are two
    # snapshots with two reasons rather than one empty body merged under one.
    return capture(url=url, body=f"FETCH FAILED {url}: {reason}".encode(), text="",
                   fetched_at=at, media_type="x-occam/fetch-error",
                   extractor="none", empty_reason=reason)


def fetch(url: str, *, at: datetime, http_get: HttpGet = urllib_get) -> Snapshot:
    """One URL, snapshotted. Never raises for a network or HTTP failure."""
    try:
        status, ctype, body = http_get(url)
    except Exception as e:  # noqa: BLE001 — every failure becomes a recorded reason
        return _failed(url, f"fetch error: {type(e).__name__}: {e}", at)
    if status != 200:
        return _failed(url, f"HTTP {status}", at)
    ctype = ctype.split(";")[0].strip().lower()
    if ctype in ("text/html", "application/xhtml+xml"):
        text = html_to_text(body.decode("utf-8", errors="replace"))
        extractor = "occam.html_to_text/1"
    elif ctype.startswith("text/"):
        text = body.decode("utf-8", errors="replace")
        extractor = "utf-8/1"
    else:
        return capture(url=url, body=body, text="", fetched_at=at, media_type=ctype,
                       extractor="none", empty_reason=f"no text extractor for {ctype or 'unknown type'}")
    if not text.strip():
        return capture(url=url, body=body, text="", fetched_at=at, media_type=ctype,
                       extractor=extractor, empty_reason="page yielded no visible text")
    return capture(url=url, body=body, text=text, fetched_at=at, media_type=ctype,
                   extractor=extractor)


def _wiki_page(title: str, *, at: datetime, http_get: HttpGet) -> Snapshot:
    page_url = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))
    api = WIKI_API + "?" + urllib.parse.urlencode({
        "action": "query", "prop": "extracts|revisions", "explaintext": "1", "redirects": "1",
        "rvprop": "ids|timestamp", "titles": title, "format": "json",
    })
    try:
        status, _, body = http_get(api)
    except Exception as e:  # noqa: BLE001
        return _failed(page_url, f"fetch error: {type(e).__name__}: {e}", at)
    if status != 200:
        return _failed(page_url, f"HTTP {status}", at)
    try:
        pages = json.loads(body)["query"]["pages"]
        text = next(iter(pages.values())).get("extract", "") or ""
    except (ValueError, KeyError, StopIteration, AttributeError):
        return capture(url=page_url, body=body, text="", fetched_at=at,
                       media_type="application/json", extractor=WIKIPEDIA_EXTRACTOR,
                       empty_reason="Wikipedia response had no extract")
    if not text.strip():
        return capture(url=page_url, body=body, text="", fetched_at=at,
                       media_type="application/json", extractor=WIKIPEDIA_EXTRACTOR,
                       empty_reason="Wikipedia extract was empty")
    return capture(url=page_url, body=body, text=text, fetched_at=at,
                   media_type="application/json", extractor=WIKIPEDIA_EXTRACTOR)



def wikipedia_search(query: str, n: int, *, http_get: HttpGet = urllib_get) -> list[str]:
    """Titles of the top n Wikipedia pages for a query. Empty on failure."""
    api = WIKI_API + "?" + urllib.parse.urlencode({
        "action": "query", "list": "search", "srsearch": query,
        "srlimit": str(n), "format": "json",
    })
    try:
        status, _, body = http_get(api)
        if status != 200:
            return []
        return [hit["title"] for hit in json.loads(body)["query"]["search"]][:n]
    except Exception:  # noqa: BLE001
        return []


QUERY_PROMPT = (
    "Write up to 3 short encyclopedia search queries that would find pages "
    "answering the question below — the names of the events, people, things "
    "or concepts involved, not the question itself. Return JSON only: "
    '{{"queries": ["...", "..."]}}\n\nQUESTION: {question}'
)


def search_queries(model: "Model", question: str) -> tuple[list[str], str]:
    """The model reads the question and proposes queries. Returns (queries, raw reply).

    Falls back to the question itself — recorded as such by the caller — when
    the reply carries no usable queries.
    """
    from .model import extract_json
    reply = model.complete(QUERY_PROMPT.format(question=question), temperature=0.0)
    obj = extract_json(reply)
    qs = obj.get("queries") if isinstance(obj, dict) else None
    qs = [q.strip() for q in qs if isinstance(q, str) and q.strip()][:3] if isinstance(qs, list) else []
    return qs, reply


def _web_pages(question: str, n: int, web_search: WebSearch, *, at: datetime,
               http_get: HttpGet, notes: list[str], raw: list[str]) -> list[Snapshot]:
    """Up to n pages a web search found, fetched and snapshotted by us (#209).

    The search only discovers: what is kept is the URLs, and each page is
    read through `fetch` exactly as a URL given by hand would be. A Wikipedia
    or mirror URL is skipped (EXCLUDED_HOSTS)."""
    try:
        found, reply = web_search(question, n)
    except Exception as e:  # noqa: BLE001 — could not look is a note, never silence
        notes.append(f"web search failed: {type(e).__name__}: {e}")
        return []
    raw.append(reply)
    kept = [u for u in found if not _excluded(u)]
    if len(kept) < len(found):
        notes.append(f"web search: skipped {len(found) - len(kept)} Wikipedia or mirror page(s)")
    if not kept:
        notes.append(f"web search returned no pages beyond Wikipedia for {question!r}")
    return [fetch(u, at=at, http_get=http_get) for u in kept[:n]]


def gather(question: str, *, at: datetime, urls: Optional[Sequence[str]] = None,
           n: int = 3, http_get: HttpGet = urllib_get, model: Optional["Model"] = None,
           web_search: Optional[WebSearch] = None, n_web: int = 0,
           ) -> tuple[list[Snapshot], list[str], list[str]]:
    """Snapshots for a question, notes on anything that degraded, and the
    model's raw replies — its search queries, then the web search — for audit.

    With `urls`, those are fetched and nothing is searched. Otherwise the
    model, if given, proposes search queries and each query's top pages are
    taken, deduplicated by title, up to `n`; without a model the question
    itself is the query. Then, with `web_search` and `n_web`, up to `n_web`
    web pages follow Wikipedia's. A search that returns nothing is a note,
    not silence.
    """
    notes: list[str] = []
    if urls:
        return [fetch(u, at=at, http_get=http_get) for u in urls], notes, []
    raw: list[str] = []
    queries = [question]
    if model is not None:
        proposed, reply = search_queries(model, question)
        raw.append(reply)
        if proposed:
            queries = proposed
        else:
            notes.append("the model proposed no search queries; searched the question itself")
    # Round-robin over each query's ranked hits: the best page of every query
    # before the second-best of any, and overlap between queries never leaves
    # fewer than n pages while unseen ones remain.
    ranked: list[list[str]] = []
    for q in queries:
        found = wikipedia_search(q, n, http_get=http_get)
        if not found:
            notes.append(f"search returned no pages for {q!r}")
        ranked.append(found)
    titles: list[str] = []
    for depth in range(n):
        for found in ranked:
            if depth < len(found) and found[depth] not in titles and len(titles) < n:
                titles.append(found[depth])
    snaps = [_wiki_page(t, at=at, http_get=http_get) for t in titles]
    if web_search is not None and n_web > 0:
        snaps += _web_pages(question, n_web, web_search, at=at, http_get=http_get,
                            notes=notes, raw=raw)
    return snaps, notes, raw
