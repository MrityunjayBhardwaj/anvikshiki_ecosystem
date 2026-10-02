"""Who served a run's model calls (#186).

OpenRouter reports a model slug and the provider that ran each call, and no
version (observed 2026-10-01: `model` "z-ai/glm-5.2", `provider`
"DigitalOcean", `system_fingerprint` null). Under one model name, the
provider is what can vary — so that is what an artifact records.
"""

import io
import json
from datetime import timedelta

from occam.answer import Artifact, Params, canonical, rejudge, replay, run
from occam.model import ScriptedModel
from occam.tests.test_answer import AS_OF, QUERIES, SUPPORT_ALL, VIABLE, attacks, argue_reply, wiki
from occam.tests.test_equiv import WORDINGS, all_same

LATER = AS_OF + timedelta(days=2)
QUESTION = "Is growth alone enough to make a business viable?"


def openrouter_body(content, **top):
    return {"choices": [{"message": {"content": content}, "finish_reason": "stop"}], **top}


def fake_urlopen(bodies):
    def urlopen(req, timeout):
        class R(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False
        return R(json.dumps(bodies.pop(0)).encode())
    return urlopen


def test_the_model_records_the_slug_and_provider_openrouter_reports(monkeypatch):
    from occam.model import OpenRouterModel
    monkeypatch.setattr("occam.model.urllib.request.urlopen", fake_urlopen([
        openrouter_body("a", model="z-ai/glm-5.2", provider="DigitalOcean"),
        openrouter_body("b", model="z-ai/glm-5.2"),
    ]))
    m = OpenRouterModel(api_key="k")
    m.complete("p", temperature=0)
    m.complete("p", temperature=0)
    assert m.served == ["z-ai/glm-5.2 via DigitalOcean",
                        "z-ai/glm-5.2 via an unreported provider"]


class Served(ScriptedModel):
    """A scripted model that reports a provider per call, in turn."""

    def __init__(self, replies, providers, name="scripted"):
        super().__init__(replies, name=name)
        self.providers, self.served = list(providers), []

    def complete(self, prompt, *, temperature):
        self.served.append(f"m via {self.providers[len(self.served) % len(self.providers)]}")
        return super().complete(prompt, temperature=temperature)


def replies(judge=True):
    argue = [argue_reply([{**VIABLE, "conclusion": w}], "q1") for w in WORDINGS]
    return [QUERIES] + argue + [SUPPORT_ALL] + [attacks()] * 3 + (all_same(3) if judge else [])


def test_a_run_records_every_provider_that_served_it_once_each():
    m = Served(replies(), ["A", "B"])
    ans, art = run(QUESTION, m, params=Params(k_argue=3, k_attack=3), as_of=AS_OF, http_get=wiki)
    assert len(m.served) > 2 and art.served_by == ("m via A", "m via B")
    back = Artifact.model_validate_json(art.model_dump_json())
    assert back.served_by == ("m via A", "m via B")
    assert canonical(replay(back)) == canonical(ans)            # audit only


def test_a_model_that_reports_nothing_is_not_recorded_rather_than_recorded_empty():
    _, art = run(QUESTION, ScriptedModel(replies()), params=Params(k_argue=3, k_attack=3),
                 as_of=AS_OF, http_get=wiki)
    assert art.served_by is None


def test_a_rejudge_records_only_the_judges_calls():
    _, off = run(QUESTION, ScriptedModel(replies(judge=False)),
                 params=Params(k_argue=3, k_attack=3, judge_same=False), as_of=AS_OF, http_get=wiki)
    m = Served(all_same(3), ["C"])
    m.served = ["m via earlier"]                     # calls made before this rejudge
    _, judged = rejudge(off, m, at=LATER)
    assert judged.same_served_by == ("m via C",)
    assert judged.served_by is None                  # the run's own calls were never recorded


def test_the_replay_output_says_who_served_every_time():
    from occam.__main__ import _served
    m = Served(replies(), ["A"])
    _, live = run(QUESTION, m, params=Params(k_argue=3, k_attack=3), as_of=AS_OF, http_get=wiki)
    _, off = run(QUESTION, ScriptedModel(replies(judge=False)),
                 params=Params(k_argue=3, k_attack=3, judge_same=False), as_of=AS_OF, http_get=wiki)
    _, later = rejudge(off, Served(all_same(3), ["C"]), at=LATER)
    assert _served(live) == "served by: m via A"
    assert _served(off).startswith("served by: not recorded")
    assert _served(later).endswith("; the later judge: m via C")
    assert _served(live.model_copy(update={"served_by": ()})) == \
        "served by: no model call was made"
