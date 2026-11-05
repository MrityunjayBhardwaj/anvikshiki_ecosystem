"""Independent model calls go out together, and replies keep their order
(#271); a network that stops answering is waited out, not given up on (#272)."""

import io
import json
import threading
import time

import pytest

import occam.__main__ as cli
import occam.model as m
from occam.covers import CoverPair, judge_covers
from occam.equiv import Pair, judge_same
from occam.model import KieModel, ScriptedModel, complete_all


class Echo:
    """Replies with its prompt, after a delay that makes later prompts finish
    first, and records how many calls were in flight at once."""

    name = "echo"

    def __init__(self, concurrency):
        self.concurrency = concurrency
        self.live = self.most = 0
        self.lock = threading.Lock()

    def complete(self, prompt, *, temperature):
        with self.lock:
            self.live += 1
            self.most = max(self.most, self.live)
        time.sleep(0.05 / (1 + len(prompt) % 7))
        with self.lock:
            self.live -= 1
        if prompt == "fail-a" or prompt == "fail-b":
            raise RuntimeError(prompt)
        return f"re:{prompt}"


PROMPTS = [f"p{i}" + "x" * i for i in range(12)]


def test_replies_come_back_in_prompt_order_with_calls_in_flight_together():
    model = Echo(concurrency=4)
    assert complete_all(model, PROMPTS, temperature=0.0) == [f"re:{p}" for p in PROMPTS]
    assert model.most == 4


def test_a_model_without_concurrency_is_asked_one_at_a_time_in_order():
    s = ScriptedModel(["a", "b", "c"])
    assert complete_all(s, ["1", "2", "3"], temperature=0.0) == ["a", "b", "c"]
    assert s.prompts == ["1", "2", "3"]
    one = Echo(concurrency=1)
    complete_all(one, PROMPTS, temperature=0.0)
    assert one.most == 1


def test_the_first_failure_in_prompt_order_is_raised():
    with pytest.raises(RuntimeError, match="fail-a"):
        complete_all(Echo(concurrency=4), ["ok", "fail-a", "ok2", "fail-b"], temperature=0.0)


def test_the_judges_store_each_reply_against_its_own_pair_and_order():
    """Replay reads same-answer replies by position and cover replies by key
    (#201), so a reply filed against the wrong pair would be read as that
    pair's verdict."""
    pairs = [Pair(id=f"p{i}", lens="claim", a=f"a{i}", b=f"b{i}", text_a=f"a{i}",
                  text_b=f"b{i}", veto="number" if i == 2 else "") for i in range(5)]
    replies = judge_same(Echo(concurrency=8), "Q?", pairs)
    asked = [(p, f) for p in pairs if not p.veto for f in (False, True)]
    assert len(replies) == len(asked) == 8
    for (p, flip), r in zip(asked, replies):
        first, second = (p.text_b, p.text_a) if flip else (p.text_a, p.text_b)
        assert r.index(f"X: {first}") < r.index(f"Y: {second}")
    covers = [CoverPair(answer=f"ans{i}", source=f"src{i}", text_answer=f"ans{i}",
                        text_source=f"src{i}") for i in range(4)]
    for answer, source, order, reply in judge_covers(Echo(concurrency=8), covers):
        assert answer in reply and source in reply
        assert (reply.index(answer) < reply.index(source)) == (order == 0)


# ── the kie.ai client under threads and a missing network ──

class R(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def reply(content="ok", credits=1.0):
    return R(json.dumps({"choices": [{"message": {"content": content}, "finish_reason": "stop"}],
                         "credits_consumed": credits}).encode())


def test_credits_are_counted_exactly_when_calls_run_together(monkeypatch):
    """Threads are made to switch every microsecond, so an unguarded
    read-add-write of the counter would lose counts."""
    import sys
    live = {"now": 0, "most": 0}
    lock = threading.Lock()

    def urlopen(req, timeout=0):
        with lock:
            live["now"] += 1
            live["most"] = max(live["most"], live["now"])
        time.sleep(0.0005)
        with lock:
            live["now"] -= 1
        return reply(credits=0.25)
    monkeypatch.setattr(m.urllib.request, "urlopen", urlopen)
    old = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    try:
        k = KieModel(api_key="x", concurrency=16)
        complete_all(k, [f"p{i}" for i in range(2000)], temperature=0.0)
    finally:
        sys.setswitchinterval(old)
    assert live["most"] > 1                                     # the calls did overlap
    assert k.credits == pytest.approx(500.0)
    assert len(k.durations) == len(k.served) == 2000


def test_a_network_that_comes_back_is_waited_for_and_each_wait_is_said(monkeypatch, capsys):
    tries = []

    def urlopen(req, timeout=0):
        tries.append(1)
        if len(tries) <= 5:
            raise m.urllib.error.URLError("nodename nor servname provided, or not known")
        return reply()
    monkeypatch.setattr(m.urllib.request, "urlopen", urlopen)
    pauses = []
    k = KieModel(api_key="x", sleep=pauses.append)
    assert k.complete("p", temperature=0.0) == "ok"
    assert pauses == [15.0, 30.0, 60.0, 120.0, 120.0]          # doubling, then capped
    assert [w for w, _ in k.waits] == pauses
    err = capsys.readouterr().err
    assert err.count("waiting") == 5 and "nodename nor servname" in err
    assert "225 s waited so far" in err                         # said before the fifth wait


def test_a_network_that_stays_away_fails_loudly_once_patience_runs_out(monkeypatch):
    def urlopen(req, timeout=0):
        raise ConnectionResetError("reset by peer")
    monkeypatch.setattr(m.urllib.request, "urlopen", urlopen)
    pauses = []
    with pytest.raises(RuntimeError, match=r"no reply after waiting 225 s"):
        KieModel(api_key="x", sleep=pauses.append, unreachable_patience=300).complete(
            "p", temperature=0.0)
    assert sum(pauses) == 225


def test_a_busy_server_is_not_waited_for_like_a_missing_network(monkeypatch):
    def urlopen(req, timeout=0):
        raise m.urllib.error.HTTPError(req.full_url, 503, "busy", {}, io.BytesIO(b"busy"))
    monkeypatch.setattr(m.urllib.request, "urlopen", urlopen)
    pauses = []
    with pytest.raises(RuntimeError, match="HTTP 503"):
        KieModel(api_key="x", sleep=pauses.append).complete("p", temperature=0.0)
    assert pauses == [10.0, 20.0, 30.0]


# ── the command line ───────────────────────────────────────

def test_concurrency_is_set_on_a_live_model_and_never_on_a_scripted_one():
    k = KieModel(api_key="x")
    assert k.concurrency == 1                                   # the class default
    assert cli._concurrent(k, 8).concurrency == 8
    s = ScriptedModel([])
    assert not hasattr(cli._concurrent(s, 8), "concurrency")
    with pytest.raises(SystemExit):
        cli._concurrent(k, 0)


def test_the_call_summary_is_said_with_none_and_with_some():
    assert cli._calls(ScriptedModel([])) == "model calls: none timed"
    k = KieModel(api_key="x")
    k.durations = [float(s) for s in range(1, 21)]
    k.waits = [(15.0, "x"), (30.0, "y")]
    assert cli._calls(k) == ("model calls: 20 returned; seconds per call median 11.0, "
                             "95th percentile 20.0, max 20.0; network waits: 2 (45 s)")


def test_measure_passes_concurrency_to_the_model(tmp_path, monkeypatch):
    made = {}

    def make(spec):
        made["m"] = KieModel(api_key="x")
        return made["m"]
    monkeypatch.setattr(m, "make_model", make)
    monkeypatch.setattr(cli, "run", lambda *a, **k: (_ for _ in ()).throw(SystemExit(7)))
    monkeypatch.setattr(cli, "_factcheck_search", lambda n: (None, True))
    with pytest.raises(SystemExit):
        cli.main(["measure", "--v1", "--concurrency", "5", "--out", str(tmp_path / "r")])
    assert made["m"].concurrency == 5
