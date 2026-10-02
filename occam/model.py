"""The model boundary: the only place Occam talks to a language model.

Everything a model says enters the pipeline as a raw string, recorded verbatim
before anything parses it. That ordering is what makes a run replayable: the
deterministic stages re-run from the recorded strings, so a disputed step can
be recomputed without asking the model again — and without the model getting
a second chance to say something different.

Two implementations. `OpenRouterModel` calls a real model over HTTP with the
standard library alone. `ScriptedModel` returns canned replies in order, which
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
