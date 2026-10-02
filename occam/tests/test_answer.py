"""Stage 7 and the whole pipeline: answer, features, persist and replay (#143).

Offline: Wikipedia is a dictionary of canned responses and the model is
scripted, so these laws exercise every deterministic stage end to end.
"""

import json
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest

from occam.answer import Artifact, Params, canonical, replay, run
from occam.gather import fetch, gather, html_to_text
from occam.model import ScriptedModel
from occam.types import Status

AS_OF = datetime(2026, 9, 28, 12, tzinfo=timezone.utc)

PAGES = {
    "Unit economics": (
        "Unit economics describes revenue and costs per unit. "
        "A business is viable at the unit level only when customer lifetime value exceeds acquisition cost."
    ),
    "Blitzscaling": (
        "Blitzscaling prioritises speed over efficiency. "
        "Proponents claim that rapid growth alone can make a company viable before its unit economics work."
    ),
}


def wiki(url):
    q = parse_qs(urlparse(url).query)
    if q.get("list") == ["search"]:
        order = sorted(PAGES, key=lambda t: t != q["srsearch"][0])   # exact title first
        hits = [{"title": t} for t in order][: int(q["srlimit"][0])]
        return 200, "application/json", json.dumps({"query": {"search": hits}}).encode()
    title = q["titles"][0]
    return 200, "application/json", json.dumps(
        {"query": {"pages": {"1": {"title": title, "extract": PAGES.get(title, "")}}}}).encode()


VIABLE = {"id": "q1", "kind": "quote", "source": 1,
          "quote": "A business is viable at the unit level only when customer lifetime value exceeds acquisition cost.",
          "conclusion": "Viability requires LTV to exceed CAC."}
GROWTH = {"id": "q2", "kind": "quote", "source": 2,
          "quote": "rapid growth alone can make a company viable before its unit economics work",
          "conclusion": "Growth alone can make a company viable."}
INFER = {"id": "i1", "kind": "inference", "from": ["q1"],
         "conclusion": "Growth alone does not make a business viable."}


def argue_reply(steps, answer):
    return json.dumps({"answer": answer, "steps": steps})


def attacks(*edges):
    return json.dumps({"attacks": [{"attacker": a, "target": t, "type": ty, "rationale": "r"}
                                   for a, t, ty in edges]})


QUERIES = json.dumps({"queries": ["Unit economics", "Blitzscaling"]})
# The judge approves every quote; ids it does not know are ignored.
SUPPORT_ALL = json.dumps({"judgments": [{"id": f"A{i:04d}", "verdict": "supports"}
                                        for i in range(40)]})


def ask(argue_replies, attack_replies, params=None, http_get=wiki, judge=SUPPORT_ALL):
    has_quotes = any('"kind": "quote"' in r for r in argue_replies)
    model = ScriptedModel([QUERIES] + list(argue_replies) + ([judge] if has_quotes else [])
                          + list(attack_replies))
    p = params or Params(k_argue=len(argue_replies), k_attack=len(attack_replies))
    return run("Is growth alone enough to make a business viable?", model,
               params=p, as_of=AS_OF, http_get=http_get)


AGREE = [argue_reply([VIABLE, INFER], "i1")] * 3
NO_ATTACKS = [attacks()] * 3


# ── end to end ─────────────────────────────────────────────

def test_a_sourced_answer_comes_back_with_a_status_and_a_tree_to_the_bytes():
    ans, art = ask(AGREE, NO_ATTACKS)
    assert not ans.abstained
    assert ans.conclusion == "Growth alone does not make a business viable."
    assert ans.status == Status.HYPOTHESIS              # an inference over a quote
    leaf_id = ans.derivation["sub_arguments"][0]["id"]
    # Tied at hypothesis: the inference, and the leaf's paraphrase of its quote.
    assert set(ans.status_bound_by) == {f"inference step {ans.answer_id}",
                                        f"quote {leaf_id} restated in the model's words"}
    leaf = ans.derivation["sub_arguments"][0]
    assert leaf["kind"] == "quote" and leaf["span"]["verdict"] == "ok"
    text = next(s for s in art.snapshots if s.id == leaf["span"]["snapshot_id"]).text
    assert text[leaf["span"]["start"]:leaf["span"]["end"]] == VIABLE["quote"]
    assert leaf["span"]["url"] == "https://en.wikipedia.org/wiki/Unit_economics"


def test_no_status_set_is_emitted_without_calibration_and_it_says_so():
    ans, _ = ask(AGREE, NO_ATTACKS)
    assert ans.status_set is None and "unavailable" in ans.status_set_note


def test_every_feature_carries_its_denominator_and_population():
    ans, _ = ask(AGREE, NO_ATTACKS)
    expected = {"k", "agree_frac", "n_positions", "verified_frac", "absent_frac",
                "punctuation_frac", "unresolvable_frac", "direct_drops", "cascade_drops",
                "n_snapshots", "n_hosts", "oldest_days", "chain_depth", "pramana_floor",
                "attack_density", "minority_attacks", "retrieval_hits",
                "support_judged", "support_dropped", "support_cannot_tell", "support_cascade",
                # the same-answer judge, on by default (#172)
                "same_question_vetoed", "same_question_merged", "same_question_order_disagree",
                "same_claim_vetoed", "same_claim_merged", "same_claim_order_disagree",
                # argue prompt 2 (#161)
                "question_number_added",
                # counter set 2 (#179)
                "question_number_unquoted"}
    assert set(ans.counters) == expected
    for name, c in ans.counters.items():
        assert c.population, name
        assert isinstance(c.of, int), name
    c = ans.counters
    assert (c["verified_frac"].n, c["verified_frac"].of) == (3, 3)
    assert (c["agree_frac"].n, c["agree_frac"].of) == (3, 3)
    assert (c["retrieval_hits"].n, c["retrieval_hits"].of) == (2, 2)
    assert c["chain_depth"].n == 2 and c["pramana_floor"].n == 2   # SABDA


GROW_INFER = {"id": "i2", "kind": "inference", "from": ["q2"],
              "conclusion": "Growth alone can make a business viable."}


def _positions(ans):
    return {p["conclusion"]: p["best_argument"] for p in ans.positions}


def test_two_inferences_in_mutual_defeat_are_both_contested():
    replies = [argue_reply([VIABLE, INFER], "i1")] * 2 + [argue_reply([GROWTH, GROW_INFER], "i2")]
    base, _ = ask(replies, [attacks()] * 3)
    ids = _positions(base)
    i1, i2 = ids[INFER["conclusion"]], ids[GROW_INFER["conclusion"]]
    fight = [attacks((i2, i1, "rebutting"), (i1, i2, "rebutting"))] * 3
    ans, _ = ask(replies, fight)
    assert {p["status"] for p in ans.positions} == {"contested"}
    assert ans.status == Status.CONTESTED and ans.counters["n_positions"].n == 2


def test_known_hole_a_reported_claim_quoted_bare_defeats_a_majority_inference():
    """Recorded, not endorsed (#146). Source 2 says 'Proponents claim that
    rapid growth alone can make a company viable…'. Quoted without
    'Proponents claim', and concluded in exactly those words, it is a
    verified quote that states its conclusion (ceiling established) and beats
    the inference (ceiling hypothesis) at equal pramāṇa — though one sample
    of three proposed it. #158 closed the paraphrased form of this; the
    verbatim form needs the support check."""
    verbatim = {**GROWTH, "conclusion": GROWTH["quote"]}
    replies = [argue_reply([VIABLE, INFER], "i1")] * 2 + [argue_reply([verbatim], "q2")]
    base, _ = ask(replies, [attacks()] * 3)
    ids = _positions(base)
    i1, q2 = ids[INFER["conclusion"]], ids[GROWTH["quote"]]
    ans, _ = ask(replies, [attacks((q2, i1, "rebutting"), (i1, q2, "rebutting"))] * 3)
    # It still wins. #162 keeps it from `established` only because every
    # fixture page shares one host; the support judge is what closes it.
    assert ans.conclusion == GROWTH["quote"] and ans.status == Status.HYPOTHESIS
    assert any(b.startswith("rests on a single source") for b in ans.status_bound_by)
    assert ans.counters["agree_frac"].n == 1 and ans.counters["agree_frac"].of == 3


# ── replay ─────────────────────────────────────────────────

def test_persist_reload_replay_is_byte_identical():
    ans, art = ask(AGREE, NO_ATTACKS)
    reloaded = Artifact.model_validate(json.loads(art.model_dump_json()))
    assert canonical(replay(reloaded)) == canonical(ans)


def test_replay_is_sensitive_to_the_stored_attack_edges():
    replies = [argue_reply([VIABLE, INFER], "i1")] * 2 + [argue_reply([GROWTH, GROW_INFER], "i2")]
    ans, art = ask(replies, [attacks()] * 3)
    ids = _positions(ans)
    i1, i2 = ids[INFER["conclusion"]], ids[GROW_INFER["conclusion"]]
    fight = attacks((i2, i1, "rebutting"), (i1, i2, "rebutting"))
    one = art.model_copy(update={"attack_replies": (fight,) + art.attack_replies[1:]})
    two = art.model_copy(update={"attack_replies": (fight, fight) + art.attack_replies[2:]})
    # One reply of three is below the majority: kept out of the graph by
    # design, but not out of the record — the minority counter moves.
    r1 = replay(one)
    assert (r1.status, r1.conclusion, r1.derivation) == (ans.status, ans.conclusion, ans.derivation)
    assert (ans.counters["minority_attacks"].n, r1.counters["minority_attacks"].n) == (0, 2)
    # Two of three carry it: the replay must move.
    assert replay(two).status == Status.CONTESTED != ans.status


def test_a_tampered_artifact_fails_to_load_rather_than_replaying_something_else():
    _, art = ask(AGREE, NO_ATTACKS)
    s0 = art.snapshots[0]
    bad = art.model_copy(update={"snapshots": (s0.model_copy(update={"text": s0.text + " x"}),)
                                 + art.snapshots[1:]})
    with pytest.raises(ValueError, match="text_sha256"):
        replay(bad)


def test_replay_uses_the_stored_clock_not_now():
    _, art = ask(AGREE, NO_ATTACKS)
    later = art.model_copy(update={"as_of": AS_OF + timedelta(days=400)})
    assert replay(later).status == Status.HYPOTHESIS
    assert any("stale" in b for b in replay(later).derivation["sub_arguments"][0]["status_bound_by"])


# ── abstention names the stage ─────────────────────────────

def test_every_span_dropped_abstains_naming_the_check_stage():
    fake = {**VIABLE, "quote": "Growth guarantees viability in every market."}
    ans, _ = ask([argue_reply([fake, INFER], "i1")] * 3, [])
    assert ans.abstained and ans.abstain_reason.startswith("check:")
    assert ans.counters["absent_frac"].n == 3 and ans.counters["absent_frac"].of == 3
    assert ans.counters["cascade_drops"].n == 3


def test_a_model_that_finds_nothing_abstains_as_such():
    """It says what was observed, and no more (#188): run 4's false-premise
    control got no answer from a page that answers the corrected question."""
    ans, _ = ask([argue_reply([], None)] * 3, [])
    assert ans.abstained and ans.abstain_reason == (
        "argue: the model returned no answer from the sources — this does not say "
        "whether they are silent or the question's premise is false")


def test_an_artifact_made_before_the_new_wording_keeps_the_old_one():
    import json
    from occam.answer import Artifact, canonical, replay
    ans, art = ask([argue_reply([], None)] * 3, [])
    old = json.loads(art.model_dump_json())
    del old["params"]["reason_wording"]                  # as every artifact before #188
    a = Artifact.model_validate(old)
    assert a.params.reason_wording == 1
    assert replay(a).abstain_reason == "argue: the model found no answer in the sources"
    assert canonical(replay(art)) == canonical(ans)


def test_no_readable_source_abstains_at_gather_and_calls_no_model():
    def down(url):
        raise OSError("network unreachable")
    model = ScriptedModel([QUERIES])
    ans, art = run("q?", model, as_of=AS_OF, http_get=down)
    assert ans.abstained and ans.abstain_reason.startswith("gather:")
    assert len(model.prompts) == 1 and art.argue_replies == ()      # queries only
    assert any("search returned no pages" in d for d in ans.degraded)


def test_every_answer_defeated_abstains_naming_the_solve_stage():
    """A quote from the other source undercuts the only answer; an undercut
    always defeats, so no position survives."""
    replies = [argue_reply([VIABLE, INFER, {**GROWTH, "id": "g"}], "i1")] * 3
    ans, art = ask(replies, [attacks()] * 3)
    assert not ans.abstained
    assert ans.answer_id == "A0001"
    cut = art.model_copy(update={"attack_replies": (attacks(("A0002", "A0001", "undercutting")),) * 3})
    dead = replay(cut)
    assert dead.abstained and dead.abstain_reason.startswith("solve:")
    assert dead.positions[0]["status"] is None


# ── gathering ──────────────────────────────────────────────

def test_a_failed_fetch_is_a_snapshot_with_a_reason_not_an_exception():
    def boom(url):
        raise TimeoutError("slow")
    s = fetch("https://x.test/a", at=AS_OF, http_get=boom)
    assert s.text == "" and "TimeoutError" in s.empty_reason
    s404 = fetch("https://x.test/b", at=AS_OF, http_get=lambda u: (404, "text/html", b"nope"))
    assert s404.empty_reason == "HTTP 404" and s404.id != s.id


def test_html_is_reduced_to_visible_text_without_scripts():
    html = "<html><head><title>t</title><script>var x=1</script></head><body><p>Hello <b>world</b></p><style>p{}</style><div>Second&amp;line</div></body></html>"
    assert html_to_text(html) == "Hello world\nSecond&line"


def test_gather_by_url_fetches_exactly_those():
    seen = []
    def get(url):
        seen.append(url)
        return 200, "text/plain; charset=utf-8", b"plain words here"
    snaps, notes, raw = gather("q", at=AS_OF, urls=["https://a.test/1", "https://b.test/2"], http_get=get)
    assert seen == ["https://a.test/1", "https://b.test/2"]
    assert [s.text for s in snaps] == ["plain words here"] * 2 and notes == []


def test_a_position_survives_through_its_undefeated_argument():
    """One conclusion, two derivations; the first is undercut. Accrual takes
    the surviving one — the position must not be reported defeated."""
    second = {"id": "j", "kind": "inference", "from": ["q2"], "conclusion": INFER["conclusion"]}
    replies = [argue_reply([VIABLE, INFER], "i1"), argue_reply([GROWTH, second], "j"),
               argue_reply([VIABLE, INFER], "i1")]
    # merge order: A0000 q1, A0001 i1, A0002 q2, A0003 j
    ans, _ = ask(replies, [attacks(("A0002", "A0001", "undercutting"))] * 3)
    assert len(ans.positions) == 1
    pos = ans.positions[0]
    assert pos["argument_ids"] == ["A0001", "A0003"] and pos["best_argument"] == "A0003"
    assert not ans.abstained and ans.answer_id == "A0003" and ans.status == Status.HYPOTHESIS


def test_the_model_proposes_the_search_queries_and_they_are_recorded():
    searched = []
    def get(url):
        q = parse_qs(urlparse(url).query)
        if q.get("list") == ["search"]:
            searched.append(q["srsearch"][0])
        return wiki(url)
    model = ScriptedModel([json.dumps({"queries": ["Blitzscaling"]})])
    snaps, notes, raw = gather("Is growth enough?", at=AS_OF, n=1, http_get=get, model=model)
    assert searched == ["Blitzscaling"] and raw and notes == []
    assert [s.urls[0] for s in snaps] == ["https://en.wikipedia.org/wiki/Blitzscaling"]
    ans, art = ask(AGREE, NO_ATTACKS)
    assert art.gather_replies == (QUERIES,)


def test_no_usable_queries_falls_back_to_the_question_and_says_so():
    searched = []
    def get(url):
        q = parse_qs(urlparse(url).query)
        if q.get("list") == ["search"]:
            searched.append(q["srsearch"][0])
        return wiki(url)
    snaps, notes, _ = gather("Is growth enough?", at=AS_OF, n=2, http_get=get,
                             model=ScriptedModel(["no json"]))
    assert searched == ["Is growth enough?"]
    assert any("proposed no search queries" in n for n in notes)


def test_titles_are_deduplicated_across_queries_up_to_n():
    model = ScriptedModel([json.dumps({"queries": ["a", "b", "c"]})])
    snaps, _, _ = gather("q", at=AS_OF, n=2, http_get=wiki, model=model)
    assert len(snaps) == 2 and len({s.urls[0] for s in snaps}) == 2



def test_the_paraphrased_reported_claim_no_longer_wins():
    """#158 narrowed the hole: paraphrased, the reported claim caps at
    hypothesis like the inference it fights, and the standoff is contested."""
    replies = [argue_reply([VIABLE, INFER], "i1")] * 2 + [argue_reply([GROWTH], "q2")]
    base, _ = ask(replies, [attacks()] * 3)
    ids = _positions(base)
    i1, q2 = ids[INFER["conclusion"]], ids[GROWTH["conclusion"]]
    ans, _ = ask(replies, [attacks((q2, i1, "rebutting"), (i1, q2, "rebutting"))] * 3)
    assert ans.status == Status.CONTESTED


# ── the source's own version id (#169) ─────────────────────

def wiki_with_revisions(url):
    q = parse_qs(urlparse(url).query)
    if q.get("list") == ["search"]:
        return wiki(url)
    assert "revisions" in q["prop"][0].split("|")        # asked in the same request
    title = q["titles"][0]
    return 200, "application/json", json.dumps({"query": {"pages": {"1": {
        "title": title, "extract": PAGES.get(title, ""),
        "revisions": [{"revid": 1000 + len(title), "parentid": 1, "timestamp": "2026-09-20T18:27:40Z"}],
    }}}}).encode()


def test_a_wikipedia_quote_carries_the_revision_it_was_read_from():
    ans, art = ask(AGREE, NO_ATTACKS, http_get=wiki_with_revisions)
    rev = "https://en.wikipedia.org/w/index.php?oldid=" + str(1000 + len("Unit economics"))
    assert [s["revision_url"] for s in ans.snapshots] == [rev]
    leaf = ans.derivation["sub_arguments"][0]
    assert leaf["span"]["revision_url"] == rev
    assert {s.revision_url for s in art.snapshots} >= {rev}          # stored, so replay keeps it
    again = replay(Artifact.model_validate_json(art.model_dump_json()))
    assert canonical(again) == canonical(ans)


def test_no_revision_is_absent_not_invented():
    ans, art = ask(AGREE, NO_ATTACKS)                                 # the API sent none
    assert all(s.revision_url is None for s in art.snapshots)
    assert all("revision_url" not in s for s in ans.snapshots)
    assert "revision_url" not in ans.derivation["sub_arguments"][0]["span"]


def test_the_cli_says_when_a_source_cannot_be_rechecked(capsys):
    from occam.__main__ import _show
    ans, _ = ask(AGREE, NO_ATTACKS)
    _show(ans)
    assert "not recorded — cannot be re-checked" in capsys.readouterr().out
    ans, _ = ask(AGREE, NO_ATTACKS, http_get=wiki_with_revisions)
    _show(ans)
    assert "revision: https://en.wikipedia.org/w/index.php?oldid=" in capsys.readouterr().out


def test_a_revision_url_the_bytes_do_not_vouch_for_is_refused():
    """#171: the revision is derived from the hashed body, so editing it in an
    artifact must fail to load, as editing the body or text does."""
    import pytest
    from pydantic import ValidationError
    _, art = ask(AGREE, NO_ATTACKS, http_get=wiki_with_revisions)
    d = json.loads(art.model_dump_json())
    d["snapshots"][0]["revision_url"] = "https://en.wikipedia.org/w/index.php?oldid=1"
    with pytest.raises(ValidationError, match="revision_url"):
        replay(Artifact.model_validate(d))
    d["snapshots"][0]["revision_url"] = None                  # dropping it is tampering too
    with pytest.raises(ValidationError, match="revision_url"):
        replay(Artifact.model_validate(d))


def test_a_stored_wikipedia_snapshot_still_yields_its_revision():
    """The extractor name is persisted in every artifact, so the rule that
    derives the revision must keep recognising the stored spelling, not just
    whatever the constant says today."""
    import base64
    from occam.answer import StoredSnapshot
    body = json.dumps({"query": {"pages": {"1": {"title": "T", "extract": "Some text.",
                                                 "revisions": [{"revid": 42}]}}}}).encode()
    import hashlib
    stored = StoredSnapshot(
        id="sha256:" + hashlib.sha256(body).hexdigest(), urls=("https://en.wikipedia.org/wiki/T",),
        fetched_at=AS_OF, media_type="application/json", body_b64=base64.b64encode(body).decode(),
        text="Some text.", text_sha256=hashlib.sha256(b"Some text.").hexdigest(),
        extractor="wikipedia-extracts/1", empty_reason=None,
        revision_url="https://en.wikipedia.org/w/index.php?oldid=42")
    assert stored.load().revision_url == "https://en.wikipedia.org/w/index.php?oldid=42"


# ── #193: an answer says when the quotes beneath it were defeated ─

def _two_sides():
    return [argue_reply([VIABLE, INFER], "i1")] * 2 + [argue_reply([GROWTH, GROW_INFER], "i2")]


def test_an_answer_names_a_quote_beneath_it_that_another_quote_defeated(capsys):
    """Run 3's q04 shape: two quotes contradict each other, each defeats the
    other, and the shown answer rests on one of them. Its status is honest
    (contested); what the reader could not see is why."""
    from occam.__main__ import _show
    from occam.answer import contradicted_quotes
    ans, _ = ask(_two_sides(), [attacks(("A0002", "A0000", "undermining"),
                                        ("A0000", "A0002", "undermining"))] * 3)
    assert ans.answer_id == "A0001"                          # i1, resting on quote A0000
    hit, n = contradicted_quotes(ans)
    assert n == 1 and [h["id"] for h in hit] == ["A0000"]
    assert hit[0]["quote"] == VIABLE["quote"] and [x["attacker"] for x in hit[0]["by"]] == ["A0002"]
    _show(ans)
    out = capsys.readouterr().out
    assert "quotes beneath this answer that another argument defeated: 1 of 1" in out
    assert f'A0000 "{VIABLE["quote"]}"' in out and "defeated by A0002: r" in out


def test_nothing_defeated_is_said_as_zero_not_left_unsaid(capsys):
    from occam.__main__ import _show
    from occam.answer import contradicted_quotes
    ans, _ = ask(_two_sides(), [attacks()] * 3)
    assert contradicted_quotes(ans) == ([], 1)
    _show(ans)
    assert "quotes beneath this answer that another argument defeated: 0 of 1" in \
        capsys.readouterr().out


def test_an_attack_that_failed_is_not_a_defeat():
    """A verbatim quote has the highest ceiling, so an inference attacking it
    fails. It was disputed, not defeated, and is not named."""
    from occam.answer import contradicted_quotes
    verbatim = {**VIABLE, "conclusion": VIABLE["quote"]}
    replies = [argue_reply([verbatim, INFER], "i1")] * 2 + \
        [argue_reply([GROWTH, GROW_INFER], "i2")]
    ans, _ = ask(replies, [attacks(("A0003", "A0000", "undermining"))] * 3)
    q = ans.derivation["sub_arguments"][0]
    assert q["id"] == "A0000" and [x["succeeded"] for x in q["attacks_received"]] == [False]
    assert contradicted_quotes(ans) == ([], 1)
