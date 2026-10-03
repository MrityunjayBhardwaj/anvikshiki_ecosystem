"""The model boundary: the only place Occam talks to a language model.

Everything a model says enters the pipeline as a raw string, recorded verbatim
before anything parses it. That ordering is what makes a run replayable: the
deterministic stages re-run from the recorded strings, so a disputed step can
be recomputed without asking the model again — and without the model getting
a second chance to say something different.

Three implementations. `OpenRouterModel` and `KieModel` call a real model
over HTTP with the standard library alone. `ScriptedModel` returns canned replies in order, which
is how the laws and the validation controls run without a network: a control
fixture scripts exactly the output whose handling it is testing.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Optional, Protocol

__all__ = ["Model", "OpenRouterModel", "ScriptedModel", "extract_json"]


class Model(Protocol):
    """Anything that turns a prompt into a reply."""

    name: str

    def complete(self, prompt: str, *, temperature: float) -> str: ...


class OpenRouterModel:
    """A chat model behind OpenRouter's OpenAI-compatible endpoint."""

    URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, model: str = "z-ai/glm-5.2", *,
                 api_key: Optional[str] = None, timeout: float = 240.0,
                 max_tokens: int = 8000, empty_retries: int = 2) -> None:
        self.name = f"openrouter/{model}"
        self._model = model
        self._key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not self._key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Occam refuses to run a model "
                "stage without a model rather than produce an empty answer "
                "that reads like 'no evidence found'."
            )
        self._timeout = timeout
        self._max_tokens = max_tokens
        self._empty_retries = empty_retries
        # Who served each call, as OpenRouter reports it (#186): the model
        # slug and the provider that ran it. OpenRouter gives no version, so
        # the provider is the part that can vary under one model name.
        self.served: list[str] = []

    def complete(self, prompt: str, *, temperature: float) -> str:
        """The model's reply, never an empty one.

        An empty reply is the model saying nothing, not the model saying
        something unreadable. Returned as "", every stage would parse it as
        malformed and act on that — a pair kept apart, a sample dropped — so
        "could not ask" would print as a decision (#175). It is asked again,
        and if it stays empty the call fails, loudly, like any other failed
        call."""
        finish = None
        for _ in range(1 + self._empty_retries):
            reply, finish = self._once(prompt, temperature)
            if reply.strip():
                return reply
        raise RuntimeError(f"{self.name}: empty reply {1 + self._empty_retries} times "
                           f"(finish_reason {finish!r})")

    def web_search(self, question: str, n: int) -> tuple[list[str], str]:
        """URLs a web search cited for the question, and the raw response for audit.

        Discovery only (#209): the model's reply text is never used — the URLs
        are fetched and quoted like any other page, and every check applies to
        what they say, not to what the model said about them."""
        from .gather import EXCLUDED_HOSTS
        payload = json.dumps({
            "model": self._model,
            "messages": [{"role": "user", "content":
                          f"Find web pages that answer this question.\n\nQUESTION: {question}"}],
            "temperature": 0.0,
            "max_tokens": 300,
            "plugins": [{"id": "web", "max_results": n,
                         "exclude_domains": list(EXCLUDED_HOSTS)}],
        }).encode()
        req = urllib.request.Request(self.URL, data=payload, headers={
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as r:
                raw = r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"{self.name}: web search HTTP {e.code}: {e.read()[:300]!r}") from e
        body = json.loads(raw)
        self.served.append(f"{body.get('model') or self._model} via "
                           f"{body.get('provider') or 'an unreported provider'}")
        urls: list[str] = []
        try:
            notes = body["choices"][0]["message"].get("annotations") or []
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(f"{self.name}: unexpected web search response {raw[:300]}") from e
        for a in notes:
            url = (a.get("url_citation") or {}).get("url") if isinstance(a, dict) else None
            if isinstance(url, str) and url not in urls:
                urls.append(url)
        return urls, raw

    def _once(self, prompt: str, temperature: float) -> tuple[str, Any]:
        payload = json.dumps({
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": self._max_tokens,
        }).encode()
        req = urllib.request.Request(self.URL, data=payload, headers={
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as r:
                body = json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"{self.name}: HTTP {e.code}: {e.read()[:300]!r}") from e
        self.served.append(f"{body.get('model') or self._model} via "
                           f"{body.get('provider') or 'an unreported provider'}")
        try:
            choice = body["choices"][0]
            return choice["message"]["content"] or "", choice.get("finish_reason")
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(f"{self.name}: unexpected response {str(body)[:300]}") from e


def urls_in(text: str) -> list[str]:
    """Every http(s) URL written in a text, in order, once each — bare or as a
    markdown link. Read character by character, no pattern matching: a URL
    runs to whitespace or a closing bracket or quote, and loses a trailing
    full stop, comma, colon or semicolon (sentence punctuation, not path)."""
    out: list[str] = []
    i = 0
    while True:
        starts = [j for j in (text.find("https://", i), text.find("http://", i)) if j >= 0]
        if not starts:
            return out
        j = k = min(starts)
        while k < len(text) and not text[k].isspace() and text[k] not in ")]>\"'<":
            k += 1
        url = text[j:k].rstrip(".,;:")
        if url not in out:
            out.append(url)
        i = k


class KieModel:
    """A chat model behind kie.ai's OpenAI-format endpoint, `/{slug}/v1/chat/completions`.

    kie.ai reports neither the provider nor a version, only a model name, so
    `served` records that name. Its web search returns no structured
    citations: `web_search` reads the URLs the model writes in its reply. Those
    may come from the search or from the model's memory — the response does
    not say — which is why every one is fetched and checked by us, and a URL
    that does not exist fails at the fetch and is recorded as such (#209)."""

    BASE = "https://api.kie.ai"

    def __init__(self, model: str = "gpt-5-2", *, api_key: Optional[str] = None,
                 timeout: float = 300.0, empty_retries: int = 2) -> None:
        self.name = f"kie/{model}"
        self._model = model
        self._key = api_key or os.environ.get("KIE_API_KEY", "")
        if not self._key:
            raise RuntimeError(
                "KIE_API_KEY is not set. Occam refuses to run a model stage without "
                "a model rather than produce an empty answer that reads like "
                "'no evidence found'."
            )
        self._timeout = timeout
        self._empty_retries = empty_retries
        self.served: list[str] = []
        # kie.ai bills each call in credits and says how many; summed here so a
        # run can report what it spent from the provider's own count.
        self.credits = 0.0

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        req = urllib.request.Request(
            f"{self.BASE}/{self._model}/v1/chat/completions",
            data=json.dumps({**body, "stream": False}).encode(),
            headers={"Authorization": f"Bearer {self._key}",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as r:
                out = json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"{self.name}: HTTP {e.code}: {e.read()[:300]!r}") from e
        if not isinstance(out, dict) or "choices" not in out:
            # kie.ai reports some failures as HTTP 200 with its own code.
            raise RuntimeError(f"{self.name}: unexpected response {str(out)[:300]}")
        self.served.append(f"{out.get('model') or self._model} via kie.ai")
        self.credits += float(out.get("credits_consumed") or 0)
        return out

    def complete(self, prompt: str, *, temperature: float) -> str:
        """The model's reply, never an empty one (see OpenRouterModel.complete)."""
        finish = None
        for _ in range(1 + self._empty_retries):
            out = self._post({"messages": [{"role": "user", "content": prompt}],
                              "temperature": temperature})
            choice = out["choices"][0]
            reply, finish = (choice.get("message") or {}).get("content") or "", \
                choice.get("finish_reason")
            if reply.strip():
                return reply
        raise RuntimeError(f"{self.name}: empty reply {1 + self._empty_retries} times "
                           f"(finish_reason {finish!r})")

    def web_search(self, question: str, n: int) -> tuple[list[str], str]:
        """URLs the model wrote after searching the web, and the raw response.
        Discovery only: nothing it says about the pages is used."""
        from .gather import EXCLUDED_HOSTS
        out = self._post({
            "messages": [{"role": "user", "content":
                          f"Search the web for up to {n} pages that answer the question "
                          f"below. Do not use {', '.join(EXCLUDED_HOSTS)}. List each page's "
                          f"full URL on its own line.\n\nQUESTION: {question}"}],
            "temperature": 0.0,
            "tools": [{"type": "function", "function": {"name": "web_search"}}],
        })
        content = (out["choices"][0].get("message") or {}).get("content") or ""
        return urls_in(content), json.dumps(out)


def make_model(spec: str) -> "Model":
    """`kie/<slug>` for kie.ai; anything else is an OpenRouter model slug,
    with or without an `openrouter/` prefix (as `Params.model` records it)."""
    if spec.startswith("kie/"):
        return KieModel(spec[len("kie/"):])
    return OpenRouterModel(spec[len("openrouter/"):] if spec.startswith("openrouter/") else spec)


class ScriptedModel:
    """Returns the given replies in order; raises when they run out.

    Running out is an error, not an empty string: a stage that asked for more
    samples than were scripted is a broken fixture, and an empty reply would
    be handled as a malformed sample and quietly counted.
    """

    def __init__(self, replies: list[str], name: str = "scripted") -> None:
        self.name = name
        self._replies = list(replies)
        self.prompts: list[str] = []

    def complete(self, prompt: str, *, temperature: float) -> str:
        self.prompts.append(prompt)
        if not self._replies:
            raise RuntimeError("ScriptedModel ran out of replies")
        return self._replies.pop(0)


def extract_json(reply: str) -> Optional[Any]:
    """The JSON object in a reply, or None when there is not exactly one.

    Models wrap JSON in prose and code fences. This takes the span from the
    first `{` to the last `}` and parses it — no pattern matching — and
    returns None rather than guessing when that does not parse.
    """
    start, end = reply.find("{"), reply.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(reply[start:end + 1])
    except json.JSONDecodeError:
        return None
