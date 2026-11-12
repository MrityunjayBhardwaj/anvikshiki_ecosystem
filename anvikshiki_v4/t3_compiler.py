"""
T3 Compiler: Build graph-structured retrieval corpus from guide text.

Key insight: the entities, relationships, and community structure are
ALREADY defined in the Stage 2 architecture. We skip the expensive
LLM extraction step that standard GraphRAG requires.

Input:  Guide text (chapter_id → markdown) + KnowledgeStore
Output: NetworkX DiGraph (knowledge graph) + list of TextChunk
"""

from __future__ import annotations

import logging
import re
from typing import Optional

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field

from .schema import EpistemicStatus, Hetvabhasa, KnowledgeStore, Vyapti

log = logging.getLogger(__name__)


# ─── Text Chunk ──────────────────────────────────────────────


class TextChunk(BaseModel):
    """A retrievable unit of guide text and what its own words point at.

    Chapter-level facts (prerequisites, difficulty) are not copied here: they
    live on the chapter node of the knowledge graph and on the base's chapter
    fingerprint, both reachable through `chapter_id` (#134).
    """

    # A field dropped from the model must fail its callers, not be silently
    # ignored as pydantic does by default (#134).
    model_config = ConfigDict(extra="forbid")

    # An identifier for diagnostics and tests; nothing ranks on it (#134).
    chunk_id: str
    chapter_id: str
    text: str
    vyapti_anchors: list[str] = Field(default_factory=list)
    # Computed, accurate (#293) and not yet read: its consumer is fallacy
    # routing after T2 runs, which does not exist yet (#296).
    hetvabhasa_anchors: list[str] = Field(default_factory=list)
    # None means the base gave no concept names to search for, so nothing was
    # looked for; [] means the names were searched and none occur here (#126).
    concept_anchors: Optional[list[str]] = None
    # The chapter's weakest authored status. Not read yet: the thesis's
    # inheritance from T2 results is not built (#296).
    epistemic_status: str = "established"


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

    concepts, unnamed = _concept_vocabulary(ks)
    if unnamed:
        log.warning(
            "%d of %d concepts have only an id, not a name (e.g. %s), so no "
            "passage can be linked to them (#126)",
            len(unnamed), len(unnamed) + len(concepts), unnamed[0],
        )

    for chapter_id, text in guide_text.items():
        fp = ks.chapter_fingerprints.get(chapter_id)
        sections = _split_sections(text)

        for i, section_text in enumerate(sections):
            if not section_text.strip():
                continue

            # Detect references to vyāptis, hetvābhāsas, and concepts
            vyapti_refs = _detect_vyapti_refs(section_text, ks.vyaptis)
            het_refs = _detect_hetvabhasa_refs(section_text, ks.hetvabhasas)
            concept_refs = _detect_concept_refs(section_text, concepts)

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
                epistemic_status=ep_status,
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


def _id_pattern(item_id: str, spelled: str) -> re.Pattern:
    """Every way the guides write an id: `V05`, `V5` and `VYĀPTI 5`.

    The base pads ids (`V05`, `H03`) and the guides do not (`V5`, `H3`), so a
    plain substring test missed nearly every mention (#293). The digit boundary
    keeps `V1` from matching inside `V10`.
    """
    m = re.fullmatch(r"([A-Za-z]+)0*(\d+)", item_id)
    if not m:
        return re.compile(rf"(?<![A-Za-z0-9]){re.escape(item_id)}(?![A-Za-z0-9])")
    prefix, number = m.groups()
    return re.compile(
        rf"(?<![A-Za-z0-9])(?:{re.escape(prefix)}|(?i:{spelled})\s+)0*{number}(?![0-9])"
    )


def _title_pattern(name: str, words: int = 2) -> Optional[re.Pattern]:
    """The opening words of an item's title, as one phrase.

    `The Market Signal Decay Law` matches on "market signal", not on "market"
    alone: a single title word anchored 89% of chunks (#135). Two words, not the
    whole title, because the guides shorten titles ("Market Signal Decay",
    "Organizational Entropy").
    """
    terms = name.split()
    if terms and terms[0].lower() == "the":
        terms = terms[1:]
    if not terms:
        return None
    phrase = r"\s+".join(re.escape(t) for t in terms[:words])
    # A plural still names the item ("Moat Mirages"); a longer word does not.
    return re.compile(rf"(?<![\w-]){phrase}(?:s|es)?(?![\w-])", re.IGNORECASE)


def _detect_refs(text: str, items: dict, spelled: str) -> list[str]:
    refs = []
    for item_id, item in items.items():
        title = _title_pattern(item.name)
        if _id_pattern(item_id, spelled).search(text) or (
            title is not None and title.search(text)
        ):
            refs.append(item_id)
    return refs


def _detect_vyapti_refs(
    text: str, vyaptis: dict[str, Vyapti]
) -> list[str]:
    """Detect which vyāptis a text chunk references: by id, or by its title."""
    return _detect_refs(text, vyaptis, "VY[AĀ]PTI")


def _detect_hetvabhasa_refs(
    text: str, hetvabhasas: dict[str, Hetvabhasa]
) -> list[str]:
    """Detect which hetvābhāsas a text chunk references: by id, or by its title."""
    return _detect_refs(text, hetvabhasas, "HETV[AĀ]BH[AĀ]SA")


def _concept_vocabulary(
    ks: KnowledgeStore,
) -> tuple[dict[str, re.Pattern], list[str]]:
    """The concepts a passage can be linked to, and the ones it cannot.

    Concepts are the dependency graph's keys and values, less the rule ids the
    graph also carries. A concept keyed by a readable phrase (`unit_economics`)
    is searched as that phrase. One keyed by an opaque id (`C01`) has no name to
    search prose for: every shipped base is keyed that way, and the guides never
    write the ids (#126). Those are returned as unnamed rather than searched for
    a token that cannot occur.
    """
    ids = set(ks.dependency_graph)
    for dependents in ks.dependency_graph.values():
        ids.update(dependents)
    ids -= set(ks.vyaptis)

    named: dict[str, re.Pattern] = {}
    unnamed: list[str] = []
    for cid in sorted(ids):
        if re.fullmatch(r"[A-Za-z]+\d+", cid):
            unnamed.append(cid)
            continue
        pattern = _title_pattern(cid.replace("_", " "), words=len(cid.split("_")))
        if pattern is None:
            unnamed.append(cid)
        else:
            named[cid] = pattern
    return named, unnamed


def _detect_concept_refs(
    text: str, concepts: dict[str, re.Pattern]
) -> Optional[list[str]]:
    """Detect which concepts a text chunk references.

    None when there is no concept name to look for, so "could not look" never
    reads as "this passage names no concept".
    """
    if not concepts:
        return None
    return [cid for cid, pattern in concepts.items() if pattern.search(text)]
