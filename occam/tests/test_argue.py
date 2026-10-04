"""Stage 2: the model quotes, the mechanism locates, and samples merge exactly (#139).

Every law here runs on scripted replies, so what is tested is the handling of
a model's output — the part that must be deterministic — and not the model.
"""

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from occam.argue import (
    PRAMANA_OF_KIND,
    Argument,
    argue,
    argue_from_replies,
    argue_prompt,
)
from occam.model import ScriptedModel, extract_json
from occam.snapshot import capture
from occam.spans import locate, verify
from occam.snapshot import SnapshotStore
from occam.types import Pramana

T0 = datetime(2026, 9, 28, tzinfo=timezone.utc)

TEXT = (
    "Unit economics decide survival.\n"
    "A business creates value if and only if **LTV exceeds CAC** over the\n"
    "customer's lifetime. Growth without that is borrowed time."
)
SNAP = capture(url="https://example.com/ch", body=b"<p>ch</p>", text=TEXT,
               fetched_at=T0, extractor="test/1")
OTHER = capture(url="https://example.org/b", body=b"<p>b</p>",
                text="Cash runway is measured in months.", fetched_at=T0)


def reply(steps, answer="s2"):
    return "Here you go:\n```json\n" + json.dumps({"answer": answer, "steps": steps}) + "\n```"


Q1 = {"id": "s1", "kind": "quote", "source": 1,
      "quote": "Growth without that is borrowed time.",
      "conclusion": "Growth without LTV > CAC is borrowed time."}
I2 = {"id": "s2", "kind": "inference", "from": ["s1"],
      "conclusion": "Growth alone does not make the business viable."}


def run(*replies):
    return argue_from_replies(list(replies), [SNAP, OTHER])


# ── the model quotes; the mechanism places ─────────────────

def test_a_real_quote_becomes_a_located_admitted_span():
    r = run(reply([Q1, I2]))
    a = r.by_id()
    quote = next(x for x in r.arguments if x.kind == "quote")
    assert quote.span.verdict == "ok"
    assert TEXT[quote.span.start:quote.span.end] == Q1["quote"]
    assert r.answers == (next(x.id for x in r.arguments if x.kind == "inference"),)
    assert a[r.answers[0]].sub_arguments == (quote.id,)


def test_located_spans_verify_identically_on_replay():
    """locate() and verify() are two readings of one rule; a span located
    once must verify to the same verdict, or replay disagrees with capture."""
    store = SnapshotStore()
    store.put(SNAP)
    quotes = ["Unit economics decide survival.",
              "if and only if LTV exceeds CAC over the customer's lifetime",
              "LTV exceeds CAC",
              "over the customer's lifetime.",
              "the customer’s lifetime"]
    for q in quotes:
        loc = locate(SNAP, q)
        assert loc.span is not None, q
        again = verify(loc.span.model_copy(update={"checked": None, "verdict": None}), store)
        assert again.verdict == loc.verdict, (q, loc.verdict, again.verdict, again.reason)


def test_markup_quote_is_placed_on_the_words_inside_the_asterisks():
    loc = locate(SNAP, "LTV exceeds CAC over the customer's lifetime")
    assert loc.verdict == "markup"
    assert TEXT[loc.span.start:loc.span.end].startswith("LTV exceeds CAC**")


def test_a_fabricated_quote_is_absent_dropped_and_counted():
    fake = {**Q1, "quote": "Growth is always worth any price."}
    r = run(reply([fake, I2]))
    assert r.verdict_counts()["absent"] == 1 and r.spans_claimed == 1
    assert (0, "s1", "absent") in r.dropped
    assert (0, "s2", "s1") in r.cascade          # the inference fell with it
    assert r.arguments == () and r.answers == (None,)
    assert "dropped" in r.answer_notes[0]


def test_a_quote_from_a_source_that_does_not_exist_is_unresolvable():
    r = run(reply([{**Q1, "source": 7}, I2]))
    assert r.verdict_counts()["unresolvable"] == 1
    assert r.verdict_counts()["absent"] == 0


def test_the_right_words_from_the_wrong_source_are_absent():
    r = run(reply([{**Q1, "source": 2}, I2]))
    assert r.verdict_counts()["absent"] == 1


# ── inference steps ─────────────────────────────────────────

def test_an_inference_with_premises_is_admitted_as_anumana():
    r = run(reply([Q1, I2]))
    inf = next(x for x in r.arguments if x.kind == "inference")
    assert inf.span is None and inf.pramana == Pramana.ANUMANA


@pytest.mark.parametrize("premises", [{}, {"from": []}, {"from": None}])
def test_an_inference_with_no_premises_is_dropped_as_unsupported(premises):
    """An unsupported ANUMANA step would outrank every verified SABDA quote
    under the engine's preference order. It is an assertion; it goes —
    whether `from` is missing, empty or null."""
    bare = {"id": "s2", "kind": "inference", "conclusion": "Growth is fine.", **premises}
    r = run(reply([Q1, bare]))
    assert (0, "s2", "unsupported: no premises") in r.dropped
    assert all(x.kind == "quote" for x in r.arguments)


def test_a_premise_cycle_is_dropped_not_recursed():
    a = {"id": "s2", "kind": "inference", "from": ["s3"], "conclusion": "a"}
    b = {"id": "s3", "kind": "inference", "from": ["s2"], "conclusion": "b"}
    r = run(reply([Q1, a, b]))
    assert {x.kind for x in r.arguments} == {"quote"}
    assert any("cycle" in why for _, _, why in r.cascade)


def test_an_unknown_premise_is_dropped():
    bad = {**I2, "from": ["s9"]}
    r = run(reply([Q1, bad]))
    assert (0, "s2", "premise names an unknown step") in r.dropped


# ── pramāṇa is derived, never read ─────────────────────────

def test_the_model_cannot_set_pramana():
    """The field is ignored on input and fixed by kind on output."""
    r = run(reply([{**Q1, "pramana": "PRATYAKSA"}, {**I2, "pramana": "PRATYAKSA"}]))
    for x in r.arguments:
        assert x.pramana == PRAMANA_OF_KIND[x.kind]
    assert Pramana.PRATYAKSA not in {x.pramana for x in r.arguments}


def test_an_argument_whose_pramana_disagrees_with_its_kind_is_refused():
    r = run(reply([Q1, I2]))
    quote = next(x for x in r.arguments if x.kind == "quote")
    with pytest.raises(ValidationError, match="derived from the kind"):
        Argument(**{**quote.model_dump(), "pramana": Pramana.PRATYAKSA})


# ── merging samples ─────────────────────────────────────────

def test_identical_samples_merge_into_one_argument_with_both_sample_ids():
    r = run(reply([Q1, I2]), reply([Q1, I2]))
    assert len(r.arguments) == 2
    assert all(x.sample_ids == (0, 1) for x in r.arguments)
    assert r.answers[0] == r.answers[1]


def test_merge_casefolds_and_collapses_whitespace_only():
    loud = {**I2, "conclusion": "GROWTH alone  does not make the business viable."}
    r = run(reply([Q1, I2]), reply([Q1, loud]))
    assert len([x for x in r.arguments if x.kind == "inference"]) == 1


def test_paraphrases_stay_two_arguments():
    """The known cost of exact merging, asserted so it stays visible."""
    para = {**I2, "conclusion": "Growing is not enough to be viable."}
    r = run(reply([Q1, I2]), reply([Q1, para]))
    assert len([x for x in r.arguments if x.kind == "inference"]) == 2


def test_one_conclusion_from_two_quotes_is_two_arguments():
    """Different support, different argument. Merging would discard one."""
    q_other = {**Q1, "quote": "Unit economics decide survival."}
    r = run(reply([Q1, I2]), reply([q_other, I2]))
    assert len([x for x in r.arguments if x.kind == "quote"]) == 2


# ── malformed and abstaining replies ───────────────────────

def test_a_reply_that_is_not_json_is_malformed_and_counted():
    r = run("I cannot help with that.")
    assert r.malformed and r.answers == (None,) and r.arguments == ()


def test_a_model_abstention_is_recorded_as_such():
    r = run(reply([], answer=None))
    assert r.answers == (None,) and r.answer_notes == ("model abstained",)


def test_argue_records_k_replies_and_the_prompt_numbers_sources():
    m = ScriptedModel([reply([Q1, I2])] * 3)
    replies, r = argue(m, "Is growth enough?", [SNAP, OTHER], k=3)
    assert len(replies) == 3 and r.k == 3 and len(m.prompts) == 3
    assert "SOURCE 1 (https://example.com/ch)" in m.prompts[0]
    assert "SOURCE 2" in m.prompts[0]
    assert argue_from_replies(replies, [SNAP, OTHER]) == r   # replay


def test_extract_json_takes_the_object_out_of_prose():
    assert extract_json('ok ```json\n{"a": 1}\n``` done') == {"a": 1}
    assert extract_json("no json here") is None
    assert extract_json("{broken") is None


def test_the_prompt_forbids_outside_knowledge_and_allows_abstention():
    p = argue_prompt("q?", [SNAP])
    assert '"answer": null' in p and "outside knowledge" in p


def test_prompt_3_asks_for_the_sources_own_words_and_each_source_separately():
    """#210: the three asks that let an answer pass `states()` and be
    corroborated. Each is a sentence a reword could drop without notice."""
    p = argue_prompt("Why is the sky blue?", [SNAP])
    assert "copied word for word from its own quote" in p
    assert "the answer is that quote step itself" in p
    assert "quote each of them as a step of its own" in p


def test_new_runs_record_prompt_3():
    from occam.answer import Params
    assert Params().argue_prompt == 3
