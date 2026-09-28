"""Stage 3a: support judged in context, three outcomes, drops that cascade (#146)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from test_answer import (  # noqa: E402
    AGREE, GROWTH, INFER, NO_ATTACKS, SUPPORT_ALL, VIABLE, _positions, argue_reply,
    ask, attacks,
)

from occam.answer import Artifact, canonical, replay  # noqa: E402
from occam.argue import argue_from_replies  # noqa: E402
from occam.snapshot import capture  # noqa: E402
from occam.support import apply_support, support_from_replies, support_prompt  # noqa: E402
from occam.types import Status  # noqa: E402

from datetime import datetime, timezone  # noqa: E402

T0 = datetime(2026, 9, 28, tzinfo=timezone.utc)
PAGE = ("Blitzscaling prioritises speed over efficiency. Proponents claim that rapid "
        "growth alone can make a company viable before its unit economics work. "
        "Most studies find the opposite.")
SNAP = capture(url="https://e.test/b", body=b"b", text=PAGE, fetched_at=T0)
REPORTED = {"id": "q", "kind": "quote", "source": 1,
            "quote": "rapid growth alone can make a company viable",
            "conclusion": "Growth alone makes a company viable."}
STEP = {"id": "i", "kind": "inference", "from": ["q"],
        "conclusion": "Unit economics do not matter early on."}


def judge(**verdicts):
    return json.dumps({"judgments": [{"id": k, "verdict": v} for k, v in verdicts.items()]})


def argued():
    return argue_from_replies([json.dumps({"answer": "i", "steps": [REPORTED, STEP]})], [SNAP])


# ── the judge sees the context, not just the quote ─────────

def test_the_prompt_marks_the_span_inside_its_surrounding_words():
    a = argued()
    p = support_prompt([x for x in a.arguments if x.kind == "quote"], [SNAP])
    assert "Proponents claim that «rapid growth alone can make a company viable»" in p
    assert "CLAIM: Growth alone makes a company viable." in p


# ── three outcomes ─────────────────────────────────────────

def test_does_not_support_drops_the_quote_and_what_rests_on_it():
    a = argued()
    new, res = apply_support(a, support_from_replies([judge(A0000="does_not_support")], a))
    assert new.arguments == () and res.dropped == ("A0000",)
    assert res.cascade == (("A0001", "A0000"),)
    assert new.answers == (None,) and "does not support" in new.answer_notes[0]


def test_supports_keeps_it_and_records_the_verdict():
    a = argued()
    new, _ = apply_support(a, support_from_replies([judge(A0000="supports")], a))
    assert next(x for x in new.arguments if x.kind == "quote").support == "supports"


def test_an_omitted_judgment_is_cannot_tell_never_supports():
    a = argued()
    res = support_from_replies([judge()], a)
    assert res.verdicts == {"A0000": "cannot_tell"} and res.unanswered == {"A0000": 1}


def test_a_malformed_reply_leaves_every_quote_cannot_tell():
    a = argued()
    res = support_from_replies(["no json"], a)
    assert res.verdicts == {"A0000": "cannot_tell"} and res.malformed


def test_a_verdict_needs_a_strict_majority():
    a = argued()
    two_one = [judge(A0000="supports")] * 2 + [judge(A0000="does_not_support")]
    split = [judge(A0000="supports"), judge(A0000="does_not_support"), judge(A0000="cannot_tell")]
    assert support_from_replies(two_one, a).verdicts["A0000"] == "supports"
    assert support_from_replies(split, a).verdicts["A0000"] == "cannot_tell"


# ── end to end ─────────────────────────────────────────────

def test_the_reported_claim_hole_closes_when_the_judge_rejects_it():
    """The #146 case: the verbatim reported claim used to win `established`
    against a two-of-three inference. Rejected in context, it is dropped and
    the inference stands."""
    verbatim = {**GROWTH, "conclusion": GROWTH["quote"]}
    replies = [argue_reply([VIABLE, INFER], "i1")] * 2 + [argue_reply([verbatim], "q2")]
    base, _ = ask(replies, [attacks()] * 3)
    ids = _positions(base)
    i1, q2 = ids[INFER["conclusion"]], ids[GROWTH["quote"]]
    fight = [attacks((q2, i1, "rebutting"), (i1, q2, "rebutting"))] * 3
    rejecting = json.dumps({"judgments": [
        {"id": q2, "verdict": "does_not_support"}] + [
        {"id": f"A{i:04d}", "verdict": "supports"} for i in range(40) if f"A{i:04d}" != q2]})
    ans, _ = ask(replies, fight, judge=rejecting)
    assert ans.conclusion == INFER["conclusion"] and ans.status == Status.HYPOTHESIS
    assert ans.counters["support_dropped"].n == 1


def test_every_answer_unsupported_abstains_naming_the_support_stage():
    ans, _ = ask(AGREE, NO_ATTACKS, judge=json.dumps({"judgments": [
        {"id": f"A{i:04d}", "verdict": "does_not_support"} for i in range(10)]}))
    assert ans.abstained and ans.abstain_reason.startswith("support:")


def test_replay_applies_the_stored_judgments_and_is_sensitive_to_them():
    ans, art = ask(AGREE, NO_ATTACKS)
    assert canonical(replay(Artifact.model_validate(json.loads(art.model_dump_json())))) == canonical(ans)
    flipped = art.model_copy(update={"support_replies": (json.dumps({"judgments": [
        {"id": "A0000", "verdict": "does_not_support"}]}),)})
    assert replay(flipped).abstained


def test_an_artifact_with_no_judgments_replays_as_unjudged_not_as_supported():
    ans, art = ask(AGREE, NO_ATTACKS)
    old = art.model_copy(update={"support_replies": ()})
    leaf = replay(old).derivation["sub_arguments"][0]
    assert any("support not judged" in b for b in leaf["status_bound_by"])


def test_the_attack_stage_never_sees_an_argument_the_judge_dropped():
    """Otherwise the model proposes attacks on arguments that replay has
    removed, those edges dangle, and whole attack samples are rejected."""
    from occam.answer import Params, run
    from occam.model import ScriptedModel
    from test_answer import AS_OF, QUERIES, wiki
    two = [argue_reply([VIABLE, INFER, {**GROWTH, "id": "g"}], "i1")] * 3
    judge_drops_growth = json.dumps({"judgments": [
        {"id": "A0000", "verdict": "supports"}, {"id": "A0002", "verdict": "does_not_support"}]})
    m = ScriptedModel([QUERIES] + two + [judge_drops_growth] + [attacks()] * 3)
    run("q?", m, params=Params(k_argue=3, k_attack=3), as_of=AS_OF, http_get=wiki)
    attack_prompt = m.prompts[-1]
    assert "A0000 [quote]" in attack_prompt and "A0002" not in attack_prompt
