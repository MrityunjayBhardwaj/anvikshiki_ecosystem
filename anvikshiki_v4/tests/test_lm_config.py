# tests/test_lm_config.py
"""A provider that cannot be selected is not support for that provider.

Selection used to be a first-key-wins chain in `backend/engine_state.py`:

    if deepinfra_key:   ...
    elif google_key:    ...
    elif openai_key:    ...

which has a failure mode worth naming, because it is the reason this module
exists. A key that is *set but unusable* takes its branch and every fallback
below it becomes unreachable. On the machine this was written for,
`DEEPINFRA_API_KEY` was present and out of balance, so appending a fourth
`elif` would have added a provider that could never be chosen — support in the
diff and nothing at runtime.

The laws below are therefore mostly about reachability and about refusing to
substitute, not about which model each provider names:

  - the new provider must be selectable while an older key is present
  - an explicit request must be honoured or raise, never silently degrade
  - "no key at all" must be distinguishable from "the API rejected us"

The substitution law is the sharp one. Asking for one provider and being handed
another changes the model underneath a measurement without saying so, which is
worse than refusing to start — the run still produces numbers, and they are
attributed to the wrong model.
"""

import os

import pytest

import dspy

from anvikshiki_v4.lm_config import (
    DEFAULT_MAX_TOKENS,
    MAX_TOKENS_ENV,
    MODEL_ENV,
    PROVIDER_ENV,
    PROVIDER_ORDER,
    PROVIDERS,
    NoProviderAvailable,
    available_providers,
    build_lm,
    select_provider,
)
from anvikshiki_v4.reasoning_lm import ReasoningLM

ALL_KEY_ENVS = [p.env_key for p in PROVIDERS] + [
    "GEMINI_API_KEY", PROVIDER_ENV, MODEL_ENV, MAX_TOKENS_ENV,
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Every law starts from no provider configured.

    Without this the suite's result depends on the developer's `.env`, which
    is the same class of problem the module is about: an outcome decided by
    ambient environment rather than by anything stated.
    """
    for name in ALL_KEY_ENVS:
        monkeypatch.delenv(name, raising=False)


def _set(monkeypatch, **keys):
    for name, value in keys.items():
        monkeypatch.setenv(name, value)


def test_openrouter_is_a_known_provider():
    assert "openrouter" in PROVIDER_ORDER


def test_openrouter_is_selectable_while_an_older_key_is_present(monkeypatch):
    """The headline law.

    This is exactly what appending `elif openrouter_key:` to the old chain
    would fail: DeepInfra is configured, so the fourth branch is dead. The
    provider must be reachable without unsetting anything.
    """
    _set(monkeypatch, DEEPINFRA_API_KEY="di", OPENROUTER_API_KEY="or")
    assert select_provider().name == "openrouter"


def test_the_old_chain_would_have_failed_this(monkeypatch):
    """The mutation check, asserting the mutation applies.

    Replays first-key-wins in the pre-module order over the same environment.
    If it does not pick a different provider than the module does, the law
    above proves nothing and this fails rather than passing quietly.
    """
    _set(monkeypatch, DEEPINFRA_API_KEY="di", OPENROUTER_API_KEY="or")

    old_order = ("deepinfra", "google", "openai", "openrouter")
    by_name = {p.name: p for p in PROVIDERS}
    old_choice = next(
        name for name in old_order if os.environ.get(by_name[name].env_key)
    )
    assert old_choice == "deepinfra", (
        "the mutation did not apply — the old chain must pick a different "
        "provider here, or the reachability law is vacuous"
    )
    assert select_provider().name != old_choice


def test_an_explicit_request_is_honoured(monkeypatch):
    _set(monkeypatch, GOOGLE_API_KEY="g", OPENROUTER_API_KEY="or",
         ANVI_LM_PROVIDER="google")
    assert select_provider().name == "google"


def test_an_explicit_request_without_its_key_raises(monkeypatch):
    """Never substitute. A silent swap changes the model under a measurement."""
    _set(monkeypatch, DEEPINFRA_API_KEY="di", ANVI_LM_PROVIDER="openrouter")
    with pytest.raises(NoProviderAvailable) as exc:
        select_provider()
    assert "OPENROUTER_API_KEY" in str(exc.value)


def test_the_refusal_names_what_is_actually_available(monkeypatch):
    """An error that does not say what to do next sends the reader to the
    source. The providers that *are* configured are the actionable part."""
    _set(monkeypatch, DEEPINFRA_API_KEY="di", ANVI_LM_PROVIDER="openrouter")
    with pytest.raises(NoProviderAvailable) as exc:
        select_provider()
    assert "deepinfra" in str(exc.value)


def test_an_unknown_provider_name_raises_and_lists_the_known_ones(monkeypatch):
    _set(monkeypatch, OPENROUTER_API_KEY="or", ANVI_LM_PROVIDER="anthropic")
    with pytest.raises(NoProviderAvailable) as exc:
        select_provider()
    for name in PROVIDER_ORDER:
        assert name in str(exc.value)


def test_no_key_at_all_raises_and_names_every_env_var():
    """Distinguishable from an API rejection: this is a setup problem, and the
    message has to be enough to fix it without reading the source."""
    with pytest.raises(NoProviderAvailable) as exc:
        select_provider()
    for provider in PROVIDERS:
        assert provider.env_key in str(exc.value)


def test_available_providers_is_empty_when_nothing_is_configured():
    assert available_providers() == []


def test_available_providers_follows_the_fallback_order(monkeypatch):
    _set(monkeypatch, OPENAI_API_KEY="o", OPENROUTER_API_KEY="or",
         DEEPINFRA_API_KEY="di")
    got = available_providers()
    assert got == [n for n in PROVIDER_ORDER if n in got]


def test_google_accepts_the_name_its_own_docs_use(monkeypatch):
    """`GEMINI_API_KEY` is what the provider's documentation says to set;
    honouring only `GOOGLE_API_KEY` reads as 'no key configured' to someone who
    followed those docs."""
    _set(monkeypatch, GEMINI_API_KEY="g")
    assert select_provider().name == "google"


def test_openrouter_builds_a_reasoning_lm(monkeypatch):
    """GLM splits its output between `content` and `reasoning_content`; a plain
    `dspy.LM` reads those responses as empty."""
    _set(monkeypatch, OPENROUTER_API_KEY="or")
    lm, provider, model = build_lm()
    assert isinstance(lm, ReasoningLM)
    assert provider.name == "openrouter"
    assert model.startswith("openrouter/")


def test_a_non_reasoning_provider_builds_a_plain_lm(monkeypatch):
    _set(monkeypatch, GOOGLE_API_KEY="g")
    lm, provider, _ = build_lm()
    assert isinstance(lm, dspy.LM) and not isinstance(lm, ReasoningLM)
    assert provider.name == "google"


def test_the_model_id_is_overridable(monkeypatch):
    _set(monkeypatch, OPENROUTER_API_KEY="or",
         ANVI_LM_MODEL="openrouter/z-ai/glm-4.6")
    _, _, model = build_lm()
    assert model == "openrouter/z-ai/glm-4.6"


def test_build_lm_reports_which_provider_served_it(monkeypatch):
    """A run that cannot say which provider answered it cannot be compared
    against another run."""
    _set(monkeypatch, OPENROUTER_API_KEY="or")
    _, provider, model = build_lm()
    assert provider.name and model


def test_the_default_budget_is_not_the_one_measured_truncating(monkeypatch):
    """4096 was measured cutting real extraction responses off, and a
    truncated answer is recorded as an empty result — a fact about the budget
    read as a fact about the input."""
    _set(monkeypatch, OPENROUTER_API_KEY="or")
    lm, _, _ = build_lm()
    assert lm.kwargs["max_tokens"] == DEFAULT_MAX_TOKENS
    assert DEFAULT_MAX_TOKENS > 4096


def test_the_budget_is_overridable_by_env(monkeypatch):
    _set(monkeypatch, OPENROUTER_API_KEY="or", ANVI_LM_MAX_TOKENS="2048")
    lm, _, _ = build_lm()
    assert lm.kwargs["max_tokens"] == 2048


def test_a_non_numeric_budget_raises_rather_than_silently_defaulting(
    monkeypatch
):
    """Falling back to the default would run at a budget the caller did not
    ask for and did not get told about."""
    _set(monkeypatch, OPENROUTER_API_KEY="or", ANVI_LM_MAX_TOKENS="lots")
    with pytest.raises(NoProviderAvailable):
        build_lm()


def test_an_explicit_argument_beats_the_environment(monkeypatch):
    _set(monkeypatch, OPENROUTER_API_KEY="or", GOOGLE_API_KEY="g",
         ANVI_LM_PROVIDER="openrouter")
    assert select_provider("google").name == "google"


def test_every_provider_declares_a_model_and_a_key(monkeypatch):
    """The denominator, and a guard on future entries: a provider added
    without a default model or env key would be silently unselectable."""
    assert len(PROVIDERS) >= 4
    for provider in PROVIDERS:
        assert provider.env_key and provider.default_model
        assert provider.default_model.strip() == provider.default_model


def test_litellm_routes_the_openrouter_prefix():
    """The default model id is only correct if litellm resolves the prefix to
    the provider. If this stops being true the id needs an api_base, and the
    failure would otherwise appear as a confusing 404 at query time."""
    import litellm
    model, provider = litellm.get_llm_provider(
        model="openrouter/z-ai/glm-5.2"
    )[:2]
    assert provider == "openrouter"
    assert model == "z-ai/glm-5.2"
