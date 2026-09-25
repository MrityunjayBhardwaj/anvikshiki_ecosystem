"""An activated vyāpti outranks a chapter-mate that merely shares its chapter (#129).

`EngineV4.query` builds `{vyapti_id: [chapter_ids]}` from `coverage.relevant_vyaptis`
at STEP 5 — it knows exactly which rules the query activated. `retrieve_for_predicates`
then unioned the values and dropped the keys, so the boost was applied per CHAPTER.

A chapter holds many chunks. Boosting the chapter promotes all of them equally,
including the ones that mention none of the activated rules — while every chunk
already records, in `vyapti_anchors`, which rules its own text names. The
narrower signal was available on both sides of the call and used on neither.

Everything here runs without embeddings or network: `_apply_boost` is a pure
reordering, and `_fallback_retrieve` is keyword overlap. Both are the real
functions the engine calls, not reimplementations of them — but note that
without an index only the fallback is reachable end-to-end, so the real-corpus
law at the bottom exercises that path and `_apply_boost` is covered by the
fixtures above. Each law says which of the two it is pinning.
"""

from anvikshiki_v4.t3_compiler import TextChunk
from anvikshiki_v4.t3a_retriever import T3aRetriever


def _chunk(cid: str, chapter: str, text: str, anchors: list[str] | None = None):
    return TextChunk(
        chunk_id=cid,
        chapter_id=chapter,
        text=text,
        vyapti_anchors=anchors or [],
    )


# Same chapter throughout, so chapter boosting cannot be what separates them.
ANCHORED = _chunk("a", "ch02", "unit economics decide whether growth helps", ["V01"])
CHAPTER_MATE = _chunk("b", "ch02", "the office moved to a larger floor")
ELSEWHERE = _chunk("c", "ch07", "pricing power follows from switching costs")


def _retriever(chunks):
    """A retriever with no index. `T3aRetriever` degrades to keyword overlap
    rather than raising, which is what makes these paths reachable offline."""
    return T3aRetriever(chunks=chunks, model="not/a-real-embedding-model")


def test_the_fixture_does_not_smuggle_in_a_chapter_boost():
    """Denominator for the ranking laws: if the two chunks under comparison sat
    in different chapters, section boosting alone would explain the order and
    the anchor would be proving nothing."""
    assert ANCHORED.chapter_id == CHAPTER_MATE.chapter_id
    assert ANCHORED.vyapti_anchors and not CHAPTER_MATE.vyapti_anchors


def test_an_anchored_chunk_outranks_its_chapter_mate():
    r = _retriever([CHAPTER_MATE, ANCHORED])
    # Deliberately passed in the losing order: the input has the chapter-mate
    # first, so a no-op implementation returns it first and fails.
    ranked = r._apply_boost(
        [CHAPTER_MATE, ANCHORED], boost_sections=["ch02"], k=2, boost_vyaptis=["V01"]
    )
    assert [c.chunk_id for c in ranked] == ["a", "b"]


def test_a_chapter_boost_still_beats_an_unrelated_chapter():
    """The pre-existing behaviour, asserted so the new tier does not silently
    replace the one that was already working."""
    r = _retriever([ELSEWHERE, CHAPTER_MATE])
    ranked = r._apply_boost(
        [ELSEWHERE, CHAPTER_MATE], boost_sections=["ch02"], k=2, boost_vyaptis=None
    )
    assert [c.chunk_id for c in ranked] == ["b", "c"]


def test_an_anchor_for_a_rule_that_did_not_fire_earns_nothing():
    """The boost is for rules the query ACTIVATED, not for carrying any anchor
    at all. Without this the new tier would be the old flat 1.2 in a new place."""
    r = _retriever([CHAPTER_MATE, ANCHORED])
    ranked = r._apply_boost(
        [CHAPTER_MATE, ANCHORED], boost_sections=["ch02"], k=2, boost_vyaptis=["V99"]
    )
    # V99 did not fire, so nothing separates them and input order is preserved.
    assert [c.chunk_id for c in ranked] == ["b", "a"]


def test_retrieve_for_predicates_keeps_the_vyapti_ids():
    """The regression that matters. The ids were discarded one line after
    arriving, so this pins the plumbing rather than only the ranking."""
    seen = {}
    r = _retriever([ANCHORED, CHAPTER_MATE])

    def spy(query, k=None, boost_sections=None, boost_vyaptis=None):
        seen["sections"], seen["vyaptis"] = boost_sections, boost_vyaptis
        return []

    r.retrieve = spy
    r.retrieve_for_predicates({"V01": ["ch02"], "V04": ["ch07"]}, "why?", k=3)

    assert seen["vyaptis"] == ["V01", "V04"], seen
    assert seen["sections"] == ["ch02", "ch07"], seen


def test_the_fallback_path_separates_activated_from_merely_anchored():
    """The keyword path scored `if chunk.vyapti_anchors: score *= 1.2` — any
    anchor, related or not. Two chunks with equal term overlap and equal
    chapters now separate on whether their rule actually fired."""
    other = _chunk("d", "ch02", "unit economics decide whether growth helps", ["V77"])
    r = _retriever([other, ANCHORED])
    ranked = r._fallback_retrieve(
        "unit economics growth", k=2, boost_sections=None, boost_vyaptis=["V01"]
    )
    assert ranked[0].chunk_id == "a", [c.chunk_id for c in ranked]


def test_an_unactivated_query_still_prefers_a_chunk_that_states_a_rule():
    """The weaker 1.2 is kept. With nothing to match against, "states a rule"
    remains a reasonable proxy for "is informative", and removing it would be a
    behaviour change nobody asked for."""
    bare = _chunk("e", "ch02", "unit economics decide whether growth helps")
    r = _retriever([bare, ANCHORED])
    ranked = r._fallback_retrieve(
        "unit economics growth", k=2, boost_sections=None, boost_vyaptis=None
    )
    assert ranked[0].chunk_id == "a", [c.chunk_id for c in ranked]


def test_plain_retrieve_is_unchanged_when_nothing_is_activated():
    """`boost_vyaptis` defaults to None, so every existing caller — including
    `engine_v4.py`'s no-activation branch — behaves exactly as before."""
    r = _retriever([ANCHORED, CHAPTER_MATE, ELSEWHERE])
    ranked = r._apply_boost(
        [ELSEWHERE, CHAPTER_MATE, ANCHORED], boost_sections=None, k=3, boost_vyaptis=None
    )
    assert [c.chunk_id for c in ranked] == ["c", "b", "a"]


# ── on the real base, not on fixtures ─────────────────────────

def _real_corpus():
    """The shipped business base and its guide prose. Both are tracked and not
    ignored, so this needs no skip guard (#114)."""
    from anvikshiki_v4.engine_factory import load_guide_dir
    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store
    from anvikshiki_v4.t3_compiler import compile_t3

    ks = load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")
    _, chunks = compile_t3(load_guide_dir("guides/business_expert"), ks)
    return ks, chunks


def test_the_tier_actually_reorders_the_real_corpus():
    """The fixtures above are ones I designed, and a ranking law can pass on a
    fixture built to make it pass. This runs the same code over the shipped
    base and asserts the reordering happens on prose nobody wrote for the test.

    It is quantified over EVERY rule, not one. Measured against a single rule
    first, the answer was "no change" — that rule was V05, which anchors 52% of
    all chunks, so the two tiers held nearly the same set and the sample of one
    was the worst case in the base. Over all eleven the tier reorders nine.
    A denominator would have said so immediately.

    WHICH PATH THIS EXERCISES, because it is not the one the name suggests.
    With a bogus embedding model there is no index, and `retrieve` hands off to
    `_fallback_retrieve` before `_apply_boost` is ever reached — so this measures
    the keyword path's scoring change, not the embedding path's reordering.
    Confirmed by mutation: flattening the fallback back to the old `score *= 1.2`
    fails this law, while disabling the `_apply_boost` tier does not.

    `_apply_boost` therefore has fixture coverage only. Exercising it on the real
    corpus needs a live embedding index, which means network and an API key, and
    that is not something the suite should require — but the gap is real and is
    the reason this docstring says so rather than letting the module name imply
    otherwise.
    """
    ks, chunks = _real_corpus()
    r = T3aRetriever(chunks=chunks, model="not/a-real-embedding-model")
    query = "how do unit economics decide whether growth helps?"

    examined = changed = 0
    for vid in ks.vyaptis:
        chapters = sorted({c.chapter_id for c in chunks if vid in c.vyapti_anchors})
        if not chapters:
            continue
        examined += 1
        before = r.retrieve(query, k=5, boost_sections=chapters, boost_vyaptis=None)
        after = r.retrieve_for_predicates({vid: chapters}, query, k=5)
        if [c.chunk_id for c in before] != [c.chunk_id for c in after]:
            changed += 1

    assert examined >= 10, f"only {examined} rules had any anchored chapter"
    assert changed >= examined // 2, (
        f"the anchor tier reordered {changed} of {examined} rules on the real "
        f"base; it was 9 of 11 when #129 landed. A collapse toward zero means "
        f"anchors have become uniform enough to stop separating anything — see "
        f"#135, where they already cover 89% of chunks."
    )


def test_the_anchor_signal_has_not_become_universal():
    """#135's number, pinned. An anchor carried by every chunk is not evidence,
    and the ranking above cannot do better than the signal it ranks on. Stated
    with its denominator so the zero-information case fails loudly rather than
    looking like excellent coverage."""
    _, chunks = _real_corpus()
    anchored = sum(1 for c in chunks if c.vyapti_anchors)
    assert len(chunks) > 100, f"only {len(chunks)} chunks — corpus did not load"
    assert anchored < len(chunks), (
        f"every one of {len(chunks)} chunks carries a vyapti anchor, so the "
        f"anchor tier can no longer separate anything (#135)"
    )
