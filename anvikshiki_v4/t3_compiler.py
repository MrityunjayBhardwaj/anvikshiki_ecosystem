"""
T3 Compiler: Build graph-structured retrieval corpus from guide text.

Key insight: the entities, relationships, and community structure are
ALREADY defined in the Stage 2 architecture. We skip the expensive
LLM extraction step that standard GraphRAG requires.

Input:  Guide text (chapter_id → markdown) + KnowledgeStore
Output: NetworkX DiGraph (knowledge graph) + list of TextChunk
"""

from __future__ import annotations

from typing import Optional

import networkx as nx
from pydantic import BaseModel, Field

from .schema import EpistemicStatus, Hetvabhasa, KnowledgeStore, Vyapti


# ─── Text Chunk ──────────────────────────────────────────────


class TextChunk(BaseModel):
    """A retrievable unit of guide text with rich metadata."""

    chunk_id: str
    chapter_id: str
    text: str
    vyapti_anchors: list[str] = Field(default_factory=list)
    hetvabhasa_anchors: list[str] = Field(default_factory=list)
    concept_anchors: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    epistemic_status: str = "established"
    sourced: bool = False
    source_ids: list[str] = Field(default_factory=list)
    difficulty_tier: str = "intermediate"
    embedding: Optional[list[float]] = None


# ─── T3 Compiler ─────────────────────────────────────────────


def compile_t3(
    guide_text: dict[str, str],
    knowledge_store: KnowledgeStore,
) -> tuple[nx.DiGraph, list[TextChunk]]:
    """
    Build the T3 corpus: knowledge graph + chunked text.

    Args:
        guide_text: chapter_id → chapter markdown text
        knowledge_store: from T2 compiler

    Returns:
        graph: NetworkX DiGraph with entities and relationships
        chunks: list of TextChunk objects ready for indexing
    """
    G = _build_knowledge_graph(knowledge_store)
    chunks = _chunk_guide_text(guide_text, knowledge_store)
    return G, chunks


# ─── Knowledge Graph Construction ────────────────────────────


def _build_knowledge_graph(ks: KnowledgeStore) -> nx.DiGraph:
    """Build the knowledge graph from the architecture."""
    G = nx.DiGraph()

    # Vyāpti nodes
    for vid, v in ks.vyaptis.items():
        G.add_node(
            vid,
            type="vyapti",
            name=v.name,
            epistemic_status=v.epistemic_status.value,
            confidence=v.confidence.formulation,
            decay_risk=v.decay_risk.value,
        )

    # Concept nodes from dependency graph
    for concept, prereqs in ks.dependency_graph.items():
        if concept not in G.nodes:
            G.add_node(concept, type="concept")
        for prereq in prereqs:
            if prereq not in G.nodes:
                G.add_node(prereq, type="concept")
            G.add_edge(prereq, concept, relation="prerequisite_for")

    # Hetvābhāsa nodes
    for hid, h in ks.hetvabhasas.items():
        G.add_node(hid, type="hetvabhasa", name=h.name)
        for ctx in h.common_contexts:
            if ctx in G.nodes:
                G.add_edge(hid, ctx, relation="monitors")

    # Chapter nodes
    for cid, fp in ks.chapter_fingerprints.items():
        G.add_node(
            cid,
            type="chapter",
            title=fp.title,
            difficulty=fp.difficulty_tier,
        )
        for prereq in fp.prerequisites:
            G.add_edge(prereq, cid, relation="prerequisite_for")
        for vid in fp.vyaptis_introduced:
            G.add_edge(cid, vid, relation="introduces")
        for fwd in fp.forward_dependencies:
            G.add_edge(cid, fwd, relation="forward_reference")

    # Threshold concept nodes
    for tc in ks.threshold_concepts:
        tc_id = f"tc_{tc.name}"
        G.add_node(tc_id, type="threshold_concept", name=tc.name)
        for prereq in tc.prerequisites:
            if prereq not in G.nodes:
                G.add_node(prereq, type="concept")
            G.add_edge(prereq, tc_id, relation="prerequisite_for")
        for concept in tc.reorganizes:
            if concept not in G.nodes:
                G.add_node(concept, type="concept")
            G.add_edge(tc_id, concept, relation="reorganizes")

    return G


# ─── Text Chunking ───────────────────────────────────────────


def _chunk_guide_text(
    guide_text: dict[str, str],
    ks: KnowledgeStore,
) -> list[TextChunk]:
    """Chunk guide text with metadata from chapter fingerprints."""
    chunks: list[TextChunk] = []

    for chapter_id, text in guide_text.items():
        fp = ks.chapter_fingerprints.get(chapter_id)
        sections = _split_sections(text)

        for i, section_text in enumerate(sections):
            if not section_text.strip():
                continue

            # Detect references to vyāptis, hetvābhāsas, and concepts
            vyapti_refs = _detect_vyapti_refs(section_text, ks.vyaptis)
            het_refs = _detect_hetvabhasa_refs(section_text, ks.hetvabhasas)
            concept_refs = _detect_concept_refs(section_text, ks.dependency_graph)

            # Determine epistemic status from chapter fingerprint
            ep_status = "established"
            if fp and fp.epistemic_statuses:
                # Take the weakest status in this chapter
                status_order = ["contested", "open", "hypothesis", "established"]
                for status_val in fp.epistemic_statuses.values():
                    idx = status_order.index(status_val.value) if status_val.value in status_order else 3
                    current_idx = status_order.index(ep_status) if ep_status in status_order else 3
                    if idx < current_idx:
                        ep_status = status_val.value

            chunk = TextChunk(
                chunk_id=f"{chapter_id}_s{i:03d}",
                chapter_id=chapter_id,
                text=section_text,
                vyapti_anchors=vyapti_refs,
                hetvabhasa_anchors=het_refs,
                concept_anchors=concept_refs,
                prerequisites=fp.prerequisites if fp else [],
                epistemic_status=ep_status,
                sourced=bool(fp and fp.decay_markers),
                difficulty_tier=fp.difficulty_tier if fp else "intermediate",
            )
            chunks.append(chunk)

    return chunks


def _split_sections(text: str, max_tokens: int = 512) -> list[str]:
    """Split chapter text into sections, respecting semantic boundaries."""
    sections: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in text.split("\n"):
        # Section headers (###) are natural split points
        if line.startswith("###") and current:
            sections.append("\n".join(current))
            current = [line]
            current_len = len(line.split())
        else:
            line_words = line.split()
            # If a single line exceeds max_tokens, split it
            if len(line_words) > max_tokens:
                # Flush current buffer first
                if current:
                    sections.append("\n".join(current))
                    current = []
                    current_len = 0
                # Split the long line into token-sized chunks
                for i in range(0, len(line_words), max_tokens):
                    chunk = " ".join(line_words[i : i + max_tokens])
                    sections.append(chunk)
            else:
                current.append(line)
                current_len += len(line_words)
                if current_len > max_tokens:
                    sections.append("\n".join(current))
                    current = []
                    current_len = 0

    if current:
        sections.append("\n".join(current))

    return sections


# ─── Reference Detection ─────────────────────────────────────


def _detect_vyapti_refs(
    text: str, vyaptis: dict[str, Vyapti]
) -> list[str]:
    """Detect which vyāptis a text chunk references."""
    refs: list[str] = []
    text_lower = text.lower()
    for vid, v in vyaptis.items():
        # Check for explicit ID references (V01, V02, etc.)
        if vid in text:
            refs.append(vid)
        # Check for key terms from the vyāpti name
        elif any(term.lower() in text_lower for term in v.name.split()[:3] if len(term) > 3):
            refs.append(vid)
    return refs


def _detect_hetvabhasa_refs(
    text: str, hetvabhasas: dict[str, Hetvabhasa]
) -> list[str]:
    """Detect which hetvābhāsas a text chunk references."""
    text_lower = text.lower()
    return [
        hid
        for hid, h in hetvabhasas.items()
        if hid in text or h.name.lower() in text_lower
    ]


def _detect_concept_refs(
    text: str, dep_graph: dict[str, list[str]]
) -> list[str]:
    """Detect which concepts a text chunk references."""
    text_lower = text.lower()
    return [
        concept
        for concept in dep_graph
        if concept.replace("_", " ").lower() in text_lower
    ]
