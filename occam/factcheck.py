"""Fact-check articles as sources: Google Fact Check Tools `claims:search` (#190, #230).

The service only discovers. Each review it names is an article on a
fact-checker's own site, and that article is fetched, snapshotted and quoted
by `gather` exactly like a page a web search named, so every check downstream
applies to it unchanged.

What the service says about a claim — its `textualRating`, one publisher's
free-text verdict such as "Mostly false" — is never read by anything that
decides an answer. It stays in the search reply, which is kept for audit, and
a reader may compare it with Occam's answer afterwards. Adopting it would make
the publisher's judgement Occam's without a quote to show for it.

The API key is sent in the request and must reach nothing that is stored: a
failure is reported by status alone, never by the URL that carried the key.
"""

from __future__ import annotations

import json
import urllib.parse
from typing import Any

from .gather import HttpGet, WebSearch, urllib_get

__all__ = ["CLAIMS_SEARCH", "FactCheckError", "claims", "review_urls", "factcheck_search"]

CLAIMS_SEARCH = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
PAGE_SIZE = 10


class FactCheckError(RuntimeError):
    """The search could not be read. Its message never carries the key."""


def claims(query: str, *, key: str, pages: int = 1, http_get: HttpGet = urllib_get,
           enough: int = 0) -> tuple[list[dict[str, Any]], list[str], bool]:
    """Claims the service returns for `query`, in its order, over up to
    `pages` pages, stopping early once `enough` review URLs are held (0: read
    every page allowed). Returns (claims, raw response bodies, more pages left)."""
    found: list[dict[str, Any]] = []
    raw: list[str] = []
    token = ""
    for _ in range(pages):
        params = {"query": query, "languageCode": "en", "pageSize": str(PAGE_SIZE), "key": key}
        if token:
            params["pageToken"] = token
        try:
            status, _, body = http_get(CLAIMS_SEARCH + "?" + urllib.parse.urlencode(params))
        except Exception as e:  # noqa: BLE001 — reported without the URL, which holds the key
            raise FactCheckError(f"fact-check search could not be reached ({type(e).__name__})") from None
        text = body.decode("utf-8", errors="replace")
        if status != 200:
            raise FactCheckError(f"fact-check search answered HTTP {status}")
        try:
            data = json.loads(text)
        except ValueError:
            raise FactCheckError("fact-check search answered with something other than JSON") from None
        raw.append(text)
        found += [c for c in data.get("claims", []) if isinstance(c, dict)]
        token = data.get("nextPageToken", "") or ""
        if not token or (enough and len(review_urls(found)) >= enough):
            break
    return found, raw, bool(token)


def review_urls(found: list[dict[str, Any]]) -> list[str]:
    """Every review article's URL, in the order the service gave them, once each."""
    urls: list[str] = []
    for c in found:
        for r in c.get("claimReview", []) or []:
            u = r.get("url") if isinstance(r, dict) else None
            if isinstance(u, str) and u.startswith(("http://", "https://")) and u not in urls:
                urls.append(u)
    return urls


def factcheck_search(key: str, *, http_get: HttpGet = urllib_get) -> WebSearch:
    """A search for `gather`: (question, n) -> (review URLs, raw replies as JSON).

    Reads pages until it holds n URLs or the service has no more, at most
    three pages. The question is sent as written: the service matches words,
    and rewording it would be a choice made before any source was read."""
    def search(question: str, n: int) -> tuple[list[str], str]:
        found, raw, _ = claims(question, key=key, pages=3, http_get=http_get, enough=n)
        return review_urls(found), json.dumps(raw)
    return search
