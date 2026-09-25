"""
T3a Retriever: Embedding-based prose retrieval over guide text chunks.

Uses TextChunks from t3_compiler and provides:
  1. Basic embedding retrieval via dspy.retrievers.Embeddings
  2. Section boosting for T2b cross-linking (activated predicates → source sections)

Zero LLM calls at query time — embedding similarity only.
"""

from __future__ import annotations

from typing import Optional

from .t3_compiler import TextChunk


class T3aRetriever:
    """
    Embedding-based retriever over guide text chunks.

    Wraps dspy.retrievers.Embeddings (FAISS-backed) with section
    boosting for T2b cross-linking.
    """

    def __init__(
        self,
        chunks: list[TextChunk],
        model: str = "openai/text-embedding-3-small",
        k: int = 5,
    ):
        self._chunks = chunks
        self._k = k
        self._model = model

        # Build corpus and index mapping
        self._corpus: list[str] = []
        self._index_to_chunk: dict[int, TextChunk] = {}

        for i, chunk in enumerate(chunks):
            if chunk.text.strip():
                self._corpus.append(chunk.text)
                self._index_to_chunk[len(self._corpus) - 1] = chunk

        # Build FAISS index via DSPy
        self._retriever = None
        # Degraded runs have to be distinguishable from healthy ones. When the
        # embedding index cannot be built, retrieval silently drops to keyword
        # overlap and every result looks the same as a working index's — so
        # the reason is recorded here and reported by `degraded_reason`.
        self._degraded_reason: Optional[str] = None
        if self._corpus:
            try:
                import dspy
                self._retriever = dspy.retrievers.Embeddings(
                    model=model,
                    docs=self._corpus,
                    k=k,
                )
            except Exception as exc:
                self._degraded_reason = (
                    f"embedding index unavailable ({type(exc).__name__}: "
                    f"{str(exc)[:120]}) — retrieval is keyword overlap"
                )
        elif not chunks:
            self._degraded_reason = "no chunks supplied — retrieval returns nothing"

    @property
    def degraded_reason(self) -> Optional[str]:
        """Why retrieval is not running on embeddings, or None if it is.

        A retriever that has fallen back to keyword overlap answers every query
        and reports nothing, so a degraded run reads exactly like a healthy
        one. Callers that record a trace should record this.
        """
        return self._degraded_reason

    @property
    def is_degraded(self) -> bool:
        return self._degraded_reason is not None

    def retrieve(
        self,
        query: str,
        k: Optional[int] = None,
        boost_sections: Optional[list[str]] = None,
        boost_vyaptis: Optional[list[str]] = None,
    ) -> list[TextChunk]:
        """
        Retrieve top-k chunks by embedding similarity.

        Args:
            query: Natural language query
            k: Number of results (default: self._k)
            boost_sections: Chapter IDs to prioritize (from T2b cross-link).
                           Chunks from these sections appear first if they
                           score in the top 2*k results.
            boost_vyaptis: Vyāpti IDs the query actually activated. A chapter
                           holds many chunks and boosting the chapter promotes
                           all of them equally, including the ones that mention
                           none of the activated rules; a chunk whose
                           `vyapti_anchors` name an activated rule is the
                           narrower and better signal, so it outranks a
                           chapter-mate that merely shares its chapter.
        """
        num_results = k or self._k

        if not self._retriever:
            return self._fallback_retrieve(
                query, num_results, boost_sections, boost_vyaptis
            )

        try:
            # Retrieve more than needed to allow boosting
            fetch_k = (
                num_results * 2
                if (boost_sections or boost_vyaptis)
                else num_results
            )
            results = self._retriever(query, k=fetch_k)

            # Map results back to TextChunks
            retrieved_chunks: list[TextChunk] = []
            for result in results:
                text = result if isinstance(result, str) else getattr(result, "text", str(result))
                # Find matching chunk by text content
                for idx, corpus_text in enumerate(self._corpus):
                    if corpus_text == text and idx in self._index_to_chunk:
                        chunk = self._index_to_chunk[idx]
                        if chunk not in retrieved_chunks:
                            retrieved_chunks.append(chunk)
                            break

            if boost_sections or boost_vyaptis:
                retrieved_chunks = self._apply_boost(
                    retrieved_chunks, boost_sections, num_results, boost_vyaptis
                )

            return retrieved_chunks[:num_results]

        except Exception as exc:
            # Record the first query-time failure too — the index built, so
            # __init__ saw nothing wrong, and without this the degradation is
            # invisible for the rest of the process's life.
            if self._degraded_reason is None:
                self._degraded_reason = (
                    f"embedding query failed ({type(exc).__name__}: "
                    f"{str(exc)[:120]}) — retrieval is keyword overlap"
                )
            return self._fallback_retrieve(
                query, num_results, boost_sections, boost_vyaptis
            )

    def retrieve_for_predicates(
        self,
        activated_predicate_sections: dict[str, list[str]],
        query: str,
        k: Optional[int] = None,
    ) -> list[TextChunk]:
        """
        Cross-linked retrieval: boost sections whose predicates were activated.

        Args:
            activated_predicate_sections: vyapti_id → [chapter_ids] from T2b
            query: The user's query
            k: Number of results

        Both halves of the mapping are used. The values give the chapters to
        prioritise; the keys name the rules that actually fired, which every
        chunk already records in `vyapti_anchors`. Unioning the values and
        dropping the keys — which is what this did — throws away the more
        specific of the two signals one line after receiving it.
        """
        # Collect all chapter IDs from activated predicates
        boost_chapters: set[str] = set()
        for chapter_ids in activated_predicate_sections.values():
            boost_chapters.update(chapter_ids)

        activated = sorted(activated_predicate_sections)

        return self.retrieve(
            query=query,
            k=k,
            boost_sections=sorted(boost_chapters) if boost_chapters else None,
            boost_vyaptis=activated or None,
        )

    def _apply_boost(
        self,
        chunks: list[TextChunk],
        boost_sections: Optional[list[str]],
        k: int,
        boost_vyaptis: Optional[list[str]] = None,
    ) -> list[TextChunk]:
        """
        Reorder chunks to prioritize those from boosted sections.

        Three tiers, relative order preserved within each:

          1. the chunk names an activated vyāpti in `vyapti_anchors`
          2. the chunk merely sits in an activated chapter
          3. everything else

        Tier 1 is strictly narrower than tier 2 — a chapter contains many
        chunks and only some of them state the rule that fired — so a chunk
        that names the rule should not be ranked level with a chapter-mate
        that happens to be about something else.
        """
        boost_set = set(boost_sections or ())
        vyapti_set = set(boost_vyaptis or ())

        anchored: list[TextChunk] = []
        sectioned: list[TextChunk] = []
        rest: list[TextChunk] = []
        for c in chunks:
            if vyapti_set and vyapti_set.intersection(c.vyapti_anchors):
                anchored.append(c)
            elif c.chapter_id in boost_set:
                sectioned.append(c)
            else:
                rest.append(c)

        return (anchored + sectioned + rest)[:k]

    def _fallback_retrieve(
        self,
        query: str,
        k: int,
        boost_sections: Optional[list[str]] = None,
        boost_vyaptis: Optional[list[str]] = None,
    ) -> list[TextChunk]:
        """
        Keyword-based fallback when embeddings are unavailable.

        Simple term overlap scoring — no LLM calls needed.
        """
        activated = set(boost_vyaptis or ())
        query_tokens = set(query.lower().split())
        if not query_tokens:
            return []

        scored: list[tuple[float, TextChunk]] = []
        for chunk in self._chunks:
            chunk_tokens = set(chunk.text.lower().split())
            if not chunk_tokens:
                continue
            overlap = len(query_tokens & chunk_tokens)
            score = overlap / len(query_tokens)

            # Boost score for matching sections
            if boost_sections and chunk.chapter_id in boost_sections:
                score *= 1.5

            # Boost for vyapti anchors. A chunk naming a rule the query
            # actually activated is worth more than one naming some unrelated
            # rule, and the flat 1.2 could not tell those apart — it rewarded
            # any chunk carrying any anchor. The weaker boost is kept for the
            # unactivated case: with nothing to match against, "states a rule"
            # is still a reasonable proxy for "is informative".
            if activated and activated.intersection(chunk.vyapti_anchors):
                score *= 1.5
            elif chunk.vyapti_anchors:
                score *= 1.2

            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:k]]
