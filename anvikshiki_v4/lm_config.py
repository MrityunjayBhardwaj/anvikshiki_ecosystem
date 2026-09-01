"""Provider resolution for the engine's language model.

Which provider serves a query used to be decided by a first-key-wins chain —
`if deepinfra_key ... elif google_key ... elif openai_key`. That has two
problems, and the second is the one that bites.

*The choice is not stated anywhere.* "Which provider answered this?" is only
answerable by reading the environment and replaying the chain in your head.

*A key that is set but unusable captures every run.* A dead provider is
indistinguishable from a chosen one: `DEEPINFRA_API_KEY` present but out of
balance takes the first branch and the fallbacks below it are unreachable. Any
provider appended to the end of such a chain is dead code on that machine — it
cannot be selected however correct it is.

So selection is explicit here:

    ANVI_LM_PROVIDER   openrouter | deepinfra | google | openai
                       When set, that provider is used. If its key is missing
                       this raises, rather than quietly using a different
                       provider — a run that silently changed model is worse
                       than one that refused to start.

                       When unset, providers are tried in PROVIDER_ORDER and
                       the first with a key present wins. That is still
                       first-key-wins, but it is now overridable, which is the
                       property the old chain lacked.

    ANVI_LM_MODEL      Override the per-provider default model id, so no caller
                       is pinned to a default that ages.

    ANVI_LM_MAX_TOKENS Override the output budget. The default is deliberately
                       not 4096: that budget was measured truncating real
                       extraction responses, and a truncated answer is recorded
                       as a fact about the input rather than about the budget.

Reasoning models route JSON to `reasoning_content` rather than `content`, so
those providers get `ReasoningLM`; the rest get a plain `dspy.LM`. Which one a
provider needs is a property of its default model, so it is declared alongside
it rather than inferred at the call site.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import dspy

from .reasoning_lm import ReasoningLM

# Not 4096. That budget was measured truncating real responses, and the
# truncation is recorded as an empty result rather than as an error.
DEFAULT_MAX_TOKENS = 16000

PROVIDER_ENV = "ANVI_LM_PROVIDER"
MODEL_ENV = "ANVI_LM_MODEL"
MAX_TOKENS_ENV = "ANVI_LM_MAX_TOKENS"


@dataclass(frozen=True)
class Provider:
    """One way of reaching a model.

    `reasoning` records whether the default model splits its output across
    `content` and `reasoning_content`. It travels with the provider because it
    is a fact about the model, not a choice the caller should have to make.
    """

    name: str
    env_key: str
    default_model: str
    reasoning: bool
    api_base: Optional[str] = None


# OpenRouter first: it is the provider that reaches the most models from one
# account, and putting it last would make it unreachable on any machine that
# already has one of the others configured — including a machine where that
# other key no longer works.
PROVIDERS: tuple[Provider, ...] = (
    Provider(
        name="openrouter",
        env_key="OPENROUTER_API_KEY",
        # litellm resolves the `openrouter/` prefix to the provider and strips
        # it, so no api_base is needed. GLM keeps the lineage every captured
        # trace in this repo used, so a before/after against those traces is
        # not confounded by a change of model family.
        default_model="openrouter/z-ai/glm-5.2",
        reasoning=True,
    ),
    Provider(
        name="deepinfra",
        env_key="DEEPINFRA_API_KEY",
        default_model="openai/zai-org/GLM-5",
        reasoning=True,
        api_base="https://api.deepinfra.com/v1/openai",
    ),
    Provider(
        name="google",
        env_key="GOOGLE_API_KEY",
        default_model="gemini/gemini-2.5-pro",
        reasoning=False,
    ),
    Provider(
        name="openai",
        env_key="OPENAI_API_KEY",
        default_model="openai/gpt-4o-mini",
        reasoning=False,
    ),
)

PROVIDER_ORDER: tuple[str, ...] = tuple(p.name for p in PROVIDERS)

_BY_NAME = {p.name: p for p in PROVIDERS}


class NoProviderAvailable(RuntimeError):
    """No provider could be resolved.

    Its own class so a caller can tell "nothing is configured" apart from "the
    provider is configured and the API rejected us" — the second is an outage,
    the first is a setup problem, and they need different responses.
    """


def _api_key(provider: Provider) -> Optional[str]:
    key = os.environ.get(provider.env_key)
    # Google is reachable under either name; GEMINI_API_KEY is what the
    # provider's own docs use, and honouring only one of them reads as "no key
    # configured" to someone who followed those docs.
    if not key and provider.name == "google":
        key = os.environ.get("GEMINI_API_KEY")
    return key or None


def available_providers() -> list[str]:
    """Providers whose key is present, in fallback order.

    Presence of a key is not proof the provider works — it says nothing about
    balance, quota or model access. This answers "what could be tried", never
    "what will succeed".
    """
    return [p.name for p in PROVIDERS if _api_key(p)]


def select_provider(requested: Optional[str] = None) -> Provider:
    """The provider to use, and why.

    An explicit request is honoured or raises. It never silently degrades to a
    different provider: asking for openrouter and being given google would
    change the model under a measurement without saying so.
    """
    requested = requested or os.environ.get(PROVIDER_ENV) or None

    if requested:
        requested = requested.strip().lower()
        if requested not in _BY_NAME:
            raise NoProviderAvailable(
                f"{PROVIDER_ENV}={requested!r} is not a known provider. "
                f"Known: {', '.join(PROVIDER_ORDER)}"
            )
        provider = _BY_NAME[requested]
        if not _api_key(provider):
            raise NoProviderAvailable(
                f"{PROVIDER_ENV}={requested!r} but {provider.env_key} is not "
                f"set. Refusing to fall back to another provider, because a "
                f"silent change of model would invalidate any measurement "
                f"taken from this run. Providers with a key present: "
                f"{', '.join(available_providers()) or 'none'}"
            )
        return provider

    for provider in PROVIDERS:
        if _api_key(provider):
            return provider

    raise NoProviderAvailable(
        "No LM API key found. Set one of: "
        + ", ".join(f"{p.env_key} ({p.name})" for p in PROVIDERS)
        + f" — or name one explicitly with {PROVIDER_ENV}."
    )


def resolve_model(provider: Provider, model: Optional[str] = None) -> str:
    return model or os.environ.get(MODEL_ENV) or provider.default_model


def resolve_max_tokens(max_tokens: Optional[int] = None) -> int:
    if max_tokens is not None:
        return max_tokens
    raw = os.environ.get(MAX_TOKENS_ENV)
    if raw:
        try:
            return int(raw)
        except ValueError as exc:
            raise NoProviderAvailable(
                f"{MAX_TOKENS_ENV}={raw!r} is not an integer"
            ) from exc
    return DEFAULT_MAX_TOKENS


def build_lm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    **kwargs,
) -> tuple[dspy.LM, Provider, str]:
    """Build the LM without configuring DSPy.

    Returns the LM, the provider it came from and the model id, so a caller can
    log or record which provider actually served a run. Separated from
    `configure_lm` so that fact is available to callers that manage DSPy
    settings themselves.
    """
    chosen = select_provider(provider)
    model_id = resolve_model(chosen, model)

    lm_kwargs = dict(
        api_key=_api_key(chosen),
        max_tokens=resolve_max_tokens(max_tokens),
        **kwargs,
    )
    if chosen.api_base:
        lm_kwargs["api_base"] = chosen.api_base

    cls = ReasoningLM if chosen.reasoning else dspy.LM
    return cls(model_id, **lm_kwargs), chosen, model_id


def configure_lm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    **kwargs,
) -> tuple[Provider, str]:
    """Build the LM and install it in DSPy. Returns (provider, model_id)."""
    lm, chosen, model_id = build_lm(provider, model, max_tokens, **kwargs)
    dspy.configure(lm=lm, adapter=dspy.JSONAdapter())
    return chosen, model_id
