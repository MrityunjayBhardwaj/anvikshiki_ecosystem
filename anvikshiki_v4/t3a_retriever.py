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
        if self._corpus:
            try:
                import dspy
                self._retriever = dspy.retrievers.Embeddings(
                    model=model,
                    docs=self._corpus,
                    k=k,
                )
            except Exception:
                # Graceful fallback: retrieval will return empty
                pass

    def retrieve(
        self,
        query: str,
        k: Optional[int] = None,
        boost_sections: Optional[list[str]] = None,
    ) -> list[TextChunk]:
        """
        Retrieve top-k chunks by embedding similarity.

        Args:
            query: Natural language query
            k: Number of results (default: self._k)
            boost_sections: Chapter IDs to prioritize (from T2b cross-link).
                           Chunks from these sections appear first if they
                           score in the top 2*k results.
        """
        num_results = k or self._k

        if not self._retriever:
            return self._fallback_retrieve(query, num_results, boost_sections)

        try:
            # Retrieve more than needed to allow boosting
            fetch_k = num_results * 2 if boost_sections else num_results
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

            if boost_sections:
                retrieved_chunks = self._apply_boost(
                    retrieved_chunks, boost_sections, num_results
                )

            return retrieved_chunks[:num_results]

        except Exception:
            return self._fallback_retrieve(query, num_results, boost_sections)

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
        """
        # Collect all chapter IDs from activated predicates
        boost_chapters: set[str] = set()
        for chapter_ids in activated_predicate_sections.values():
            boost_chapters.update(chapter_ids)

        return self.retrieve(
            query=query,
            k=k,
            boost_sections=sorted(boost_chapters) if boost_chapters else None,
        )

    def _apply_boost(
        self,
        chunks: list[TextChunk],
        boost_sections: list[str],
        k: int,
    ) -> list[TextChunk]:
        """
        Reorder chunks to prioritize those from boosted sections.

        Boosted chunks that appear in the top 2*k results get moved
        to the front, maintaining relative order within each group.
        """
        boost_set = set(boost_sections)
        boosted = [c for c in chunks if c.chapter_id in boost_set]
        non_boosted = [c for c in chunks if c.chapter_id not in boost_set]
        return (boosted + non_boosted)[:k]

    def _fallback_retrieve(
        self,
        query: str,
        k: int,
        boost_sections: Optional[list[str]] = None,
    ) -> list[TextChunk]:
        """
        Keyword-based fallback when embeddings are unavailable.

        Simple term overlap scoring — no LLM calls needed.
        """
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

            # Boost for vyapti anchors
            if chunk.vyapti_anchors:
                score *= 1.2

            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:k]]
