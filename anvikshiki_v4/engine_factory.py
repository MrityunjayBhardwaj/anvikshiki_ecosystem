"""
Engine Factory: Initialize a fully-wired AnvikshikiEngineV4 from YAML + guide text.

Runs the complete compile-time pipeline:
  1. Load KnowledgeStore from YAML
  2. Load guide text from markdown files
  3. compile_t2b() → augmented KB + synonym table + source sections
  4. compile_t3() → knowledge graph + text chunks
  5. T3aRetriever(chunks) → FAISS index
  6. SemanticCoverageAnalyzer(augmented_ks, synonym_table)
  7. AugmentationPipeline(augmented_ks) for T3b
  8. GroundingPipeline(augmented_ks) for grounding
  9. AnvikshikiEngineV4 with all components wired

Usage:
    engine, artifacts = initialize_engine(
        kb_yaml_path="anvikshiki_v4/data/business_expert.yaml",
        guide_dir="guides/business_expert",
    )
    result = engine.forward_with_coverage("How do unit economics work?")
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

from .schema import KnowledgeStore
from .t2_compiler_v4 import load_knowledge_store
from .t2b_compiler import T2bResult, compile_t2b
from .t3_compiler import TextChunk, compile_t3
from .t3a_retriever import T3aRetriever
from .coverage import SemanticCoverageAnalyzer
from .kb_augmentation import AugmentationPipeline
from .grounding import GroundingPipeline
from .engine_v4 import AnvikshikiEngineV4


class CompileArtifacts:
    """All compile-time artifacts, exposed for inspection and tracing."""

    def __init__(
        self,
        base_ks: KnowledgeStore,
        t2b_result: Optional[T2bResult],
        active_ks: KnowledgeStore,
        guide_text: dict[str, str],
        chunks: list[TextChunk],
        synonym_table: dict[str, str],
        source_sections: dict[str, list[str]],
    ):
        self.base_ks = base_ks
        self.t2b_result = t2b_result
        self.active_ks = active_ks
        self.guide_text = guide_text
        self.chunks = chunks
        self.synonym_table = synonym_table
        self.source_sections = source_sections


def load_guide_dir(guide_dir: str) -> dict[str, str]:
    """
    Load guide markdown files from a directory.

    Maps chapter IDs to markdown text. Chapter IDs are inferred from
    filenames: guide_ch2.md → "ch02", guide_ch3_ch4.md → "ch03".

    Files that don't match guide_ch*.md or guide_opening*.md patterns
    are skipped (stage files, pure prompt files, etc.).
    """
    guide_text: dict[str, str] = {}
    guide_path = Path(guide_dir)

    if not guide_path.is_dir():
        return guide_text

    for md_file in sorted(guide_path.glob("*.md")):
        name = md_file.stem

        # Match guide_chN, guide_chN_chM, guide_opening_ch1
        chapter_id = _extract_chapter_id(name)
        if not chapter_id:
            continue

        text = md_file.read_text(encoding="utf-8")
        if text.strip():
            guide_text[chapter_id] = text

    return guide_text


def _extract_chapter_id(filename: str) -> Optional[str]:
    """Extract chapter ID from guide filename.

    guide_ch2 → ch02
    guide_ch3_ch4 → ch03
    guide_ch11_ch12 → ch11
    guide_opening_ch1 → ch01
    guide_ch9_ch10 → ch09
    """
    if not filename.startswith("guide_"):
        return None

    # Find first chapter number
    match = re.search(r"ch(\d+)", filename)
    if not match:
        return None

    num = int(match.group(1))
    return f"ch{num:02d}"


def initialize_engine(
    kb_yaml_path: str,
    guide_dir: Optional[str] = None,
    guide_text: Optional[dict[str, str]] = None,
    contestation_mode: str = "vada",
    embedding_model: str = "openai/text-embedding-3-small",
    retriever_k: int = 5,
) -> tuple[AnvikshikiEngineV4, CompileArtifacts]:
    """
    Initialize a fully-wired engine from YAML KB + guide text.

    Args:
        kb_yaml_path: Path to the base KnowledgeStore YAML
        guide_dir: Directory containing guide_ch*.md files. If provided,
                   guide text is loaded from here.
        guide_text: Pre-loaded guide text dict (chapter_id → markdown).
                    Takes precedence over guide_dir.
        contestation_mode: "vada", "jalpa", or "vitanda"
        embedding_model: Model for T3a retriever embeddings
        retriever_k: Default number of chunks to retrieve

    Returns:
        engine: Fully initialized AnvikshikiEngineV4
        artifacts: CompileArtifacts for inspection/tracing
    """
    # Step 1: Load base KB
    base_ks = load_knowledge_store(kb_yaml_path)

    # Step 2: Load guide text
    if guide_text is None and guide_dir is not None:
        guide_text = load_guide_dir(guide_dir)
    guide_text = guide_text or {}

    # Step 3: Compile T2b (if guide text available)
    t2b_result = None
    active_ks = base_ks
    synonym_table: dict[str, str] = {}
    source_sections: dict[str, list[str]] = {}

    if guide_text:
        t2b_result = compile_t2b(base_ks, guide_text)
        active_ks = t2b_result.augmented_ks
        synonym_table = t2b_result.synonym_table
        source_sections = t2b_result.source_sections

    # Step 4: Compile T3 → chunks
    chunks: list[TextChunk] = []
    if guide_text:
        _, chunks = compile_t3(guide_text, active_ks)

    # Step 5: Build T3a retriever
    t3a_retriever = None
    if chunks:
        t3a_retriever = T3aRetriever(
            chunks=chunks, model=embedding_model, k=retriever_k
        )

    # Step 6: Build coverage analyzer
    coverage_analyzer = SemanticCoverageAnalyzer(active_ks, synonym_table)

    # Step 7: Build augmentation pipeline (T3b)
    augmentation_pipeline = AugmentationPipeline(active_ks)

    # Step 8: Build grounding pipeline
    grounding_pipeline = GroundingPipeline(active_ks)

    # Step 9: Assemble engine
    engine = AnvikshikiEngineV4(
        knowledge_store=active_ks,
        grounding_pipeline=grounding_pipeline,
        contestation_mode=contestation_mode,
        coverage_analyzer=coverage_analyzer,
        augmentation_pipeline=augmentation_pipeline,
        t3a_retriever=t3a_retriever,
        t2b_source_sections=source_sections,
    )

    artifacts = CompileArtifacts(
        base_ks=base_ks,
        t2b_result=t2b_result,
        active_ks=active_ks,
        guide_text=guide_text,
        chunks=chunks,
        synonym_table=synonym_table,
        source_sections=source_sections,
    )

    return engine, artifacts
