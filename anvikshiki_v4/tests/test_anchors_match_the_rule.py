"""A chunk is anchored to a rule only when it names that rule (#135, #293).

Two faults in one matcher. The title fallback anchored a chunk if ANY single
word of a rule's title appeared in it, so "market" anchored the Market Signal
Decay Law and 116 of 130 business chunks carried an anchor. And the id check
looked for the base's padded ids (`V05`, `H03`) while the guides write `V5`,
`H3` and `VYĀPTI 5`, so the precise signal almost never fired.
"""

from types import SimpleNamespace

import pytest

from anvikshiki_v4.t3_compiler import _detect_hetvabhasa_refs, _detect_vyapti_refs


def _v(vid, name):
    """The matcher reads only `.name`; a full Vyapti would pin unrelated
    required fields here (#47)."""
    return SimpleNamespace(id=vid, name=name)


RULES = {
    "V01": _v("V01", "The Value Equation"),
    "V05": _v("V05", "The Market Signal Decay Law"),
    "V10": _v("V10", "The Judgment Calibration Principle"),
}


@pytest.mark.parametrize("text", [
    "as V5 predicts, the signal decays",
    "as V05 predicts",
    "**[VYĀPTI 5 — a definition box]**",
    "see Vyāpti 5 above",
    "(V5)",
])
def test_every_way_the_guides_write_an_id_anchors(text):
    assert _detect_vyapti_refs(text, RULES) == ["V05"]


@pytest.mark.parametrize("text", ["V50 is not a rule here", "AV5 is a part number", "V15"])
def test_a_longer_number_or_a_word_is_not_the_id(text):
    assert _detect_vyapti_refs(text, RULES) == []


def test_v1_does_not_match_inside_v10():
    assert _detect_vyapti_refs("only V10 is cited", RULES) == ["V10"]


def test_one_word_of_the_title_is_not_a_reference():
    """The #135 case: every one of these shares a word with a title."""
    text = "the market grew, the equation held, and judgment was needed"
    assert _detect_vyapti_refs(text, RULES) == []


def test_a_phrase_from_the_title_is_a_reference():
    """The guides shorten titles, so the opening phrase is what they repeat."""
    assert _detect_vyapti_refs("how market signal decay shapes strategy", RULES) == ["V05"]
    assert _detect_vyapti_refs("the Value Equation, restated", RULES) == ["V01"]


def test_a_plural_names_the_rule():
    """The guide writes "Moat Mirages (H7)"; the plural is still the item."""
    assert _detect_vyapti_refs("several market signals arrived late", RULES) == ["V05"]


@pytest.mark.parametrize("text", [
    "supermarket signals were loud", # letters run in at the start
    "marketing signals were loud",   # letters run on after the first word
    "market signaling was loud",     # letters run on at the end
    "value equational thinking",
])
def test_a_word_that_merely_shares_letters_is_not_the_phrase(text):
    assert _detect_vyapti_refs(text, RULES) == []


def test_fallacies_are_matched_the_same_way():
    fallacies = {
        "H03": SimpleNamespace(id="H03", name="The Survivorship Inference")
    }
    assert _detect_hetvabhasa_refs("this is H3 at work", fallacies) == ["H03"]
    assert _detect_hetvabhasa_refs("**[HETVĀBHĀSA 3]**", fallacies) == ["H03"]
    assert _detect_hetvabhasa_refs("survivorship inference again", fallacies) == ["H03"]
    assert _detect_hetvabhasa_refs("H13 and the survivors", fallacies) == []


# ── on the shipped base ───────────────────────────────────────

@pytest.fixture(scope="module")
def corpus():
    from anvikshiki_v4.engine_factory import load_guide_dir
    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store
    from anvikshiki_v4.t3_compiler import compile_t3

    ks = load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")
    _, chunks = compile_t3(load_guide_dir("guides/business_expert"), ks)
    assert len(chunks) > 100, f"only {len(chunks)} chunks — corpus did not load"
    return ks, chunks


def test_no_rule_is_anchored_to_most_of_the_corpus(corpus):
    """Was 67 of 130 for V05 and 116 of 130 overall. Measured after the fix:
    23 of 130 at most for one rule, 53 of 130 overall. The bound is loose on
    purpose; it fails if a single-word match comes back, not on small drift."""
    ks, chunks = corpus
    n = len(chunks)
    per_rule = {vid: sum(vid in c.vyapti_anchors for c in chunks) for vid in ks.vyaptis}
    anchored = sum(bool(c.vyapti_anchors) for c in chunks)
    assert max(per_rule.values()) <= n // 4, per_rule
    assert anchored <= n // 2, f"{anchored} of {n} chunks anchored"


def test_every_chunk_that_names_a_rule_by_number_is_anchored_to_it(corpus):
    """Read straight from the prose with an independent pattern: if a chunk
    writes `V5` or `VYĀPTI 5`, it must carry V05. Before #293 this held for
    V10 alone."""
    import re

    ks, chunks = corpus
    checked = 0
    for c in chunks:
        for m in re.finditer(r"(?:\bV|VYĀPTI )(\d{1,2})(?!\d)", c.text):
            vid = f"V{int(m.group(1)):02d}"
            if vid in ks.vyaptis:
                checked += 1
                assert vid in c.vyapti_anchors, (c.chunk_id, m.group(0))
    assert checked >= 30, f"only {checked} id mentions found — pattern or corpus changed"


def test_every_chunk_that_names_a_fallacy_by_number_is_anchored_to_it(corpus):
    import re

    ks, chunks = corpus
    checked = 0
    for c in chunks:
        for m in re.finditer(r"(?:\bH|HETVĀBHĀSA )(\d{1,2})(?!\d)", c.text):
            hid = f"H{int(m.group(1)):02d}"
            if hid in ks.hetvabhasas:
                checked += 1
                assert hid in c.hetvabhasa_anchors, (c.chunk_id, m.group(0))
    assert checked >= 30, f"only {checked} id mentions found — pattern or corpus changed"
