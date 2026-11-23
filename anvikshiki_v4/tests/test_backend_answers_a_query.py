"""The backend answers a query, and says what happened along the way (#314).

On `webapp` the backend could not answer at all: nothing configured a
language model, and the stream called `engine.t2b_compiler` and
`engine.argumentation`, which the engine does not have. These tests drive the
real FastAPI app with a stubbed engine, so they check what goes over the wire
without a model call.

Things each test pins down:
- importing the app needs no provider key; a missing key fails the query, by name
- the stream's coverage stage says "not run" when grounding stopped first
- every field the engine returns reaches the client, the verdict included
- the mode the client picks reaches grounding; an unknown one is refused
- the KB counts are named for what they count
- a debug log of the provider setup never contains any part of a key
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import dspy
import pytest

from anvikshiki_v4 import GroundingMode
from anvikshiki_v4.lm_config import PROVIDERS, PROVIDER_ENV

REPO = Path(__file__).resolve().parents[2]
KB = "anvikshiki_v4/data/business_expert.yaml"

VERDICT = {"asks": "value_creation(acme)", "answer": "no",
           "by": "not_value_creation(acme)", "status": "hypothesis",
           "given": [["organizational_growth(acme)"]],
           "reason": "contrary_accepted"}

COVERAGE = {"coverage_ratio": 1.0, "decision": "FULL",
            "matched_predicates": ["organizational_growth"],
            "unmatched_predicates": [], "match_details": {},
            "relevant_vyaptis": ["V04"], "inert_predicates": []}


def _answered(**over):
    """What the engine returns on the full path, trimmed to one argument."""
    fields = dict(
        verdict=VERDICT, response="Verdict: No.", sources=["src_a"],
        derivation={"rule_backed": True, "derived_count": 1},
        uncertainty={}, provenance={}, violations=[],
        advisories=[{"kind": "decay", "rule": "V04"}],
        grounding_confidence=1.0, extension_size=1, coverage=COVERAGE,
        augmentation=None, contestation=None,
        arguments={"A0": {"id": "A0", "conclusion": "c(acme)",
                          "tag": {"source_ids": frozenset({"s2", "s1"})}}},
        attacks=[], labels={"A0": "in"},
    )
    fields.update(over)
    return dspy.Prediction(**fields)


def _clarifying():
    """What the engine returns when grounding asks for clarification."""
    return _answered(verdict=None, response="Clarification needed.",
                     sources=[], grounding_confidence=0.33, extension_size=0,
                     coverage=None, arguments={}, labels={}, advisories=[])


class _Engine:
    def __init__(self, prediction):
        self.prediction = prediction
        self.calls = []

    def forward_with_coverage(self, query, interpreted_intent="", mode=None):
        self.calls.append((query, mode))
        return self.prediction


@pytest.fixture
def api(monkeypatch):
    from fastapi.testclient import TestClient
    import backend.engine_state as es
    import backend.main as main

    monkeypatch.setattr(es, "ensure_lm", lambda: None)  # no model in-process

    def serve(prediction):
        engine = _Engine(prediction)
        monkeypatch.setattr(es.state, "engine", engine)
        monkeypatch.setattr(es.state, "loaded", True)
        return TestClient(main.app), engine

    return serve


def _events(body: str) -> dict:
    events = {}
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events[lines["event"]] = json.loads(lines["data"])
    return events


def _stream(client, mode="partial"):
    r = client.get("/api/query/stream", params={"query": "q", "mode": mode})
    return r, (_events(r.text) if r.status_code == 200 else None)


# ── coverage that never ran ──────────────────────────────────────────────────

def test_coverage_that_never_ran_is_reported_as_not_run(api):
    client, _ = api(_clarifying())
    _, events = _stream(client)
    assert events["stage:coverage"]["decision"] == "NOT_RUN"
    assert events["stage:coverage"]["coverage_ratio"] is None
    assert events["complete"]["coverage"] is None


def test_coverage_that_ran_is_reported_as_it_came(api):
    """The control: a real coverage result goes through unchanged."""
    client, _ = api(_answered())
    _, events = _stream(client)
    assert events["stage:coverage"]["decision"] == "FULL"
    assert events["stage:coverage"]["coverage_ratio"] == 1.0
    assert events["stage:coverage"]["matched"] == ["organizational_growth"]


# ── every engine field reaches the client ────────────────────────────────────

@pytest.mark.parametrize("path", ["stream", "sync"])
def test_the_verdict_derivation_and_advisories_reach_the_client(api, path):
    client, _ = api(_answered())
    if path == "stream":
        result = _stream(client)[1]["complete"]
    else:
        r = client.post("/api/query", json={"query": "q", "mode": "full"})
        assert r.status_code == 200, r.text
        result = r.json()
    assert result["verdict"] == VERDICT
    assert result["derivation"] == {"rule_backed": True, "derived_count": 1}
    assert result["advisories"] == [{"kind": "decay", "rule": "V04"}]
    assert result["arguments"]["A0"]["tag"]["source_ids"] == ["s1", "s2"]


def test_a_field_the_engine_did_not_set_is_still_sent_as_null(api):
    """The webapp schema requires these keys; an engine path that leaves one
    out must not make the whole answer fail to parse."""
    prediction = _answered()
    del prediction._store["augmentation"]
    client, _ = api(prediction)
    result = _stream(client)[1]["complete"]
    assert "augmentation" in result and result["augmentation"] is None


def test_labels_is_the_field_not_the_inherited_method(api):
    client, _ = api(_answered())
    assert _stream(client)[1]["complete"]["labels"] == {"A0": "in"}


# ── the mode reaches grounding ───────────────────────────────────────────────

@pytest.mark.parametrize("mode", ["minimal", "partial", "full"])
def test_the_chosen_mode_reaches_the_engine(api, mode):
    client, engine = api(_answered())
    r, _ = _stream(client, mode)
    assert r.status_code == 200
    r = client.post("/api/query", json={"query": "q", "mode": mode})
    assert r.status_code == 200
    assert engine.calls == [("q", GroundingMode(mode))] * 2


@pytest.mark.parametrize("path", ["stream", "sync"])
def test_an_unknown_mode_is_refused_not_run_as_full(api, path):
    client, engine = api(_answered())
    if path == "stream":
        r, _ = _stream(client, "turbo")
    else:
        r = client.post("/api/query", json={"query": "q", "mode": "turbo"})
    assert r.status_code == 400
    assert "turbo" in r.json()["detail"] and "minimal" in r.json()["detail"]
    assert engine.calls == []


def test_the_engine_passes_the_mode_to_grounding():
    """One level down: `forward_with_coverage` hands the mode to grounding,
    and with no mode calls grounding exactly as it did before."""
    from anvikshiki_v4.engine_v4 import AnvikshikiEngineV4
    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

    seen = []

    class _Grounding:
        def __call__(self, query, **kwargs):
            seen.append(kwargs)
            raise StopIteration  # grounding is all this test needs

    engine = AnvikshikiEngineV4(knowledge_store=load_knowledge_store(KB),
                                grounding_pipeline=_Grounding())
    for mode in (None, GroundingMode.MINIMAL):
        with pytest.raises(StopIteration):
            engine.forward_with_coverage("q", mode=mode)
    assert seen == [{}, {"mode": GroundingMode.MINIMAL}]


# ── KB counts ────────────────────────────────────────────────────────────────

def test_kb_counts_are_named_for_what_they_count():
    from fastapi.testclient import TestClient
    import backend.main as main
    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

    ks = load_knowledge_store(KB)
    client = TestClient(main.app)
    loaded = client.post("/kb/load", json={"kb_yaml_path": KB}).json()
    inspected = client.get("/kb/inspect").json()
    for info in (loaded, inspected):
        assert "argument_count" not in info
        assert info["vyapti_count"] == len(ks.vyaptis)
        assert info["hetvabhasa_count"] == len(ks.hetvabhasas)
    assert len(ks.hetvabhasas) != 0  # a zero would pass for the wrong reason


# ── provider setup, in a clean process ───────────────────────────────────────

def _clean_env(**extra):
    env = {k: v for k, v in os.environ.items()
           if k not in {p.env_key for p in PROVIDERS} | {PROVIDER_ENV}}
    env.update(extra)
    return env


def _run(code, env, cwd):
    return subprocess.run([sys.executable, "-c", code], env=env, cwd=cwd,
                          capture_output=True, text=True, timeout=120)


def test_no_key_loads_a_kb_and_fails_the_query_by_name(tmp_path):
    """Run where the repo's .env cannot be found, with every key unset.

    Before, importing the app configured the model, so this process could
    not even import it. Now the import and the KB load work, and the query
    is refused with the variable that is missing.
    """
    code = f"""
import sys; sys.path.insert(0, {str(REPO)!r})
import backend.engine_state as es
es._root = __import__("pathlib").Path({str(tmp_path)!r})  # no .env here
from fastapi.testclient import TestClient
import backend.main as main, dspy
print("lm_after_import", dspy.settings.lm is None)
c = TestClient(main.app)
print("load", c.post("/kb/load", json={{"kb_yaml_path": {KB!r}}}).status_code)
r = c.post("/api/query", json={{"query": "q", "mode": "full"}})
print("query", r.status_code, r.json()["detail"])
"""
    out = _run(code, _clean_env(), tmp_path)
    assert out.returncode == 0, out.stderr[-2000:]
    lines = dict(line.split(" ", 1) for line in out.stdout.splitlines())
    assert lines["lm_after_import"] == "True"
    assert lines["load"] == "200"
    status, detail = lines["query"].split(" ", 1)
    assert status == "400"
    assert any(p.env_key in detail for p in PROVIDERS), detail


def test_the_debug_log_never_shows_any_part_of_a_key(tmp_path):
    fake = "sk-or-FAKE1234567890abcdef"
    provider = next(p for p in PROVIDERS if p.name == "openrouter")
    code = f"""
import sys; sys.path.insert(0, {str(REPO)!r})
import backend.engine_state as es
es._root = __import__("pathlib").Path({str(tmp_path)!r})
es.ensure_lm()
"""
    out = _run(code, _clean_env(DEBUG_MODE="1", **{
        provider.env_key: fake, PROVIDER_ENV: "openrouter"}), tmp_path)
    assert out.returncode == 0, out.stderr[-2000:]
    log = out.stdout + out.stderr
    assert f"{provider.env_key}" in log and "SET" in log  # the log did print
    assert "Provider : openrouter" in log
    for i in range(len(fake) - 3):
        assert fake[i:i + 4] not in log, f"key fragment {fake[i:i + 4]!r} logged"


# ── a failed model call ──────────────────────────────────────────────────────

class _ProviderDown(Exception):
    pass


class _FailingEngine:
    """Fails the way litellm does: a message that is a whole traceback."""

    BLOB = ("litellm.InternalServerError: internal error, please try again later\n"
            + "Traceback (most recent call last):\n" + "  frame\n" * 2000)

    def forward_with_coverage(self, query, interpreted_intent="", mode=None):
        raise _ProviderDown(self.BLOB)


@pytest.mark.parametrize("path", ["stream", "sync"])
def test_a_failed_model_call_tells_the_client_one_line(api, monkeypatch, path):
    import backend.engine_state as es
    client, _ = api(_answered())
    monkeypatch.setattr(es.state, "engine", _FailingEngine())
    if path == "stream":
        r = client.get("/api/query/stream", params={"query": "q", "mode": "full"})
        message = _events(r.text)["error"]["message"]
    else:
        r = client.post("/api/query", json={"query": "q", "mode": "full"})
        assert r.status_code == 500
        message = r.json()["detail"]
    assert message == ("_ProviderDown: litellm.InternalServerError: "
                       "internal error, please try again later")
    assert len(_FailingEngine.BLOB) > 10_000  # the long form really was long
