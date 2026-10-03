"""The kie.ai client, offline: its own error shape, its credit count, and the
URLs read out of a web-search reply that has no structured citations."""

import io
import json

import pytest

import occam.model as m
from occam.model import KieModel, OpenRouterModel, make_model, urls_in


def stub(monkeypatch, *bodies):
    sent = []

    class R(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def urlopen(req, timeout=0):
        sent.append((req.full_url, json.loads(req.data)))
        return R(json.dumps(bodies[len(sent) - 1]).encode())
    monkeypatch.setattr(m.urllib.request, "urlopen", urlopen)
    return sent


def reply(content, credits=0.5):
    return {"choices": [{"message": {"content": content}, "finish_reason": "stop"}],
            "model": "gpt-5.2", "credits_consumed": credits}


def test_urls_are_read_out_of_prose_and_markdown_once_each():
    text = ("- [NASA](https://spaceplace.nasa.gov/blue-sky/en/) — kids.\n"
            "See https://www.noaa.gov/jetstream/why-is-sky-blue. Also "
            "<https://a.test/x?y=1>, and again https://spaceplace.nasa.gov/blue-sky/en/\n"
            "(http://b.test/p);")
    assert urls_in(text) == ["https://spaceplace.nasa.gov/blue-sky/en/",
                             "https://www.noaa.gov/jetstream/why-is-sky-blue",
                             "https://a.test/x?y=1", "http://b.test/p"]
    assert urls_in("no links here") == []


def test_a_reply_is_returned_and_its_credits_counted(monkeypatch):
    sent = stub(monkeypatch, reply("ok", 1.31), reply("again", 0.2))
    k = KieModel("gpt-5-2", api_key="x")
    assert k.complete("p", temperature=0.7) == "ok" and k.complete("q", temperature=0.0) == "again"
    assert sent[0][0] == "https://api.kie.ai/gpt-5-2/v1/chat/completions"
    assert sent[0][1]["temperature"] == 0.7 and sent[0][1]["stream"] is False
    assert k.credits == pytest.approx(1.51) and k.served == ["gpt-5.2 via kie.ai"] * 2


def test_kies_own_error_code_on_http_200_is_an_error_not_an_empty_answer(monkeypatch):
    stub(monkeypatch, {"code": 422, "msg": "The model is not supported", "data": None})
    with pytest.raises(RuntimeError, match="The model is not supported"):
        KieModel("nope", api_key="x").complete("p", temperature=0.0)


def test_a_busy_server_is_asked_again_and_only_the_answer_is_kept(monkeypatch):
    busy = {"code": 500, "msg": "Server exception, please try again later", "data": None}
    sent = stub(monkeypatch, busy, busy, reply("ok", 1.0))
    pauses = []
    k = KieModel(api_key="x", sleep=pauses.append)
    assert k.complete("p", temperature=0.0) == "ok"
    assert len(sent) == 3 and pauses == [10.0, 20.0] and k.credits == 1.0


def test_a_busy_server_that_stays_busy_fails_loudly(monkeypatch):
    busy = {"code": 500, "msg": "Server exception, please try again later", "data": None}
    stub(monkeypatch, busy, busy, busy, busy)
    with pytest.raises(RuntimeError, match="Server exception"):
        KieModel(api_key="x", sleep=lambda s: None).complete("p", temperature=0.0)


def test_a_client_error_is_not_asked_again(monkeypatch):
    sent = stub(monkeypatch, {"code": 422, "msg": "The model is not supported", "data": None})
    with pytest.raises(RuntimeError):
        KieModel(api_key="x", sleep=lambda s: None).complete("p", temperature=0.0)
    assert len(sent) == 1


def test_an_empty_reply_is_asked_again_then_fails_loudly(monkeypatch):
    stub(monkeypatch, reply(""), reply("  "), reply(""))
    with pytest.raises(RuntimeError, match="empty reply 3 times"):
        KieModel(api_key="x").complete("p", temperature=0.0)


def test_web_search_asks_with_the_tool_and_keeps_only_the_urls(monkeypatch):
    sent = stub(monkeypatch, reply("Try [x](https://x.test/a) and https://y.test/b."))
    urls, raw = KieModel(api_key="x").web_search("Why?", 3)
    assert urls == ["https://x.test/a", "https://y.test/b"]
    assert sent[0][1]["tools"] == [{"type": "function", "function": {"name": "web_search"}}]
    assert "wikipedia.org" in sent[0][1]["messages"][0]["content"]
    assert json.loads(raw)["credits_consumed"] == 0.5          # the whole response, for audit


def test_a_model_spec_picks_its_provider(monkeypatch):
    monkeypatch.setenv("KIE_API_KEY", "x")
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    assert make_model("kie/gpt-5-2").name == "kie/gpt-5-2"
    assert make_model("z-ai/glm-5.2").name == "openrouter/z-ai/glm-5.2"
    assert make_model("openrouter/z-ai/glm-5.2").name == "openrouter/z-ai/glm-5.2"
    assert isinstance(make_model("kie/gpt-5-2"), KieModel)
    assert isinstance(make_model("z-ai/glm-5.2"), OpenRouterModel)


def test_no_key_refuses_to_run(monkeypatch):
    monkeypatch.delenv("KIE_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="KIE_API_KEY is not set"):
        KieModel()
