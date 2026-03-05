"""
T2b Compiler: Compile-time fine-grained KB extraction from guide prose.

Wraps the existing PredicateExtractionPipeline (Stages A-E) to produce:
  1. Augmented KnowledgeStore with fine-grained vyaptis tagged by origin
  2. Synonym table for semantic coverage matching
  3. Source section mappings for T3a cross-linking

Usage:
    from anvikshiki_v4.t2b_compiler import compile_t2b
    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

    ks = load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")
    result = compile_t2b(ks, guide_text={"ch02": ch2_md, "ch03": ch3_md})
    # result.augmented_ks has base + fine-grained vyaptis
    # result.synonym_table maps aliases to canonical predicate names
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .extraction_schema import ExtractionConfig, ValidationResult
from .predicate_extraction import PredicateExtractionPipeline
from .schema import (
    AugmentationMetadata,
    AugmentationOrigin,
    KnowledgeStore,
)


class T2bResult(BaseModel):
    """Output of the T2b compile-time extraction."""

    augmented_ks: KnowledgeStore
    synonym_table: dict[str, str] = Field(
        default_factory=dict,
        description="Predicate alias -> canonical name",
    )
    validation: ValidationResult = Field(default_factory=ValidationResult)
    fine_grained_vyapti_ids: list[str] = Field(
        default_factory=list,
        description="IDs of newly extracted vyaptis (not in base KB)",
    )
    source_sections: dict[str, list[str]] = Field(
        default_factory=dict,
        description="vyapti_id -> [chapter_ids] for T3a cross-linking",
    )


def compile_t2b(
    knowledge_store: KnowledgeStore,
    guide_text: dict[str, str],
    config: Optional[ExtractionConfig] = None,
) -> T2bResult:
    """
    Run compile-time fine-grained KB extraction.

    1. Run PredicateExtractionPipeline (Stages A-E)
    2. Tag new vyaptis with GUIDE_EXTRACTED origin metadata
    3. Build synonym table from Stage C canonicalization
    4. Track source chapter mappings for T3a cross-linking
    5. Store metadata on the augmented KnowledgeStore
    """
    base_ids = set(knowledge_store.vyaptis.keys())

    # Run the existing extraction pipeline
    pipeline = PredicateExtractionPipeline(
        knowledge_store, config or ExtractionConfig()
    )
    augmented_ks, validation, stage_d = pipeline(guide_text)

    # Identify new vyapti IDs
    new_ids = [vid for vid in augmented_ks.vyaptis if vid not in base_ids]

    # Tag each new vyapti with origin metadata
    now = datetime.now()
    source_sections: dict[str, list[str]] = {}

    for vid in new_ids:
        vyapti = augmented_ks.vyaptis[vid]

        # Find source chapter(s) from Stage D provenance
        parent_vyapti_id = None
        chapter_ids: list[str] = []

        # Check new_vyaptis and refinement_vyaptis for provenance
        for proposed in stage_d.new_vyaptis + stage_d.refinement_vyaptis:
            if proposed.id == vid:
                parent_vyapti_id = proposed.parent_vyapti
                # Find chapter from parent vyapti's chapter fingerprint
                if proposed.parent_vyapti:
                    for cid, fp in augmented_ks.chapter_fingerprints.items():
                        if proposed.parent_vyapti in fp.vyaptis_introduced:
                            chapter_ids.append(cid)
                # Also check provenance records
                for prov in proposed.provenance:
                    if prov.chapter_id and prov.chapter_id not in chapter_ids:
                        chapter_ids.append(prov.chapter_id)
                break

        vyapti.augmentation_metadata = AugmentationMetadata(
            origin=AugmentationOrigin.GUIDE_EXTRACTED,
            generated_at=now,
            source_chapter_ids=chapter_ids,
            parent_vyapti_id=parent_vyapti_id,
        )

        if chapter_ids:
            source_sections[vid] = chapter_ids

    # Build synonym table from Stage C
    # Run Stage C independently to get synonym_clusters
    synonym_table = _build_synonym_table(pipeline, guide_text)

    # Store metadata on the KnowledgeStore
    augmented_ks.fine_grained_vyapti_ids = new_ids
    augmented_ks.synonym_table = synonym_table

    return T2bResult(
        augmented_ks=augmented_ks,
        synonym_table=synonym_table,
        validation=validation,
        fine_grained_vyapti_ids=new_ids,
        source_sections=source_sections,
    )


def _build_synonym_table(
    pipeline: PredicateExtractionPipeline,
    guide_text: dict[str, str],
) -> dict[str, str]:
    """
    Build synonym table from Stage C canonicalization clusters.

    Also adds token-overlap mappings for predicates that share >60%
    tokens with base KB predicates.
    """
    synonym_table: dict[str, str] = {}

    # Run Stages A-C to get synonym clusters
    from .extraction_schema import StageAOutput

    all_stage_a = StageAOutput(candidates=[], chapter_id="all")
    for chapter_id, text in guide_text.items():
        try:
            chapter_result = pipeline.stage_a(
                chapter_text=text, chapter_id=chapter_id
            )
            all_stage_a.candidates.extend(chapter_result.candidates)
        except Exception:
            continue

    if not all_stage_a.candidates:
        return synonym_table

    try:
        stage_b = pipeline.stage_b(stage_a=all_stage_a, guide_text=guide_text)
        stage_c = pipeline.stage_c(stage_a=all_stage_a, stage_b=stage_b)
    except Exception:
        return synonym_table

    # Extract mappings from synonym clusters
    for cluster in stage_c.synonym_clusters:
        for alt in cluster.alternatives:
            if alt != cluster.canonical:
                synonym_table[alt] = cluster.canonical

    # Add token-overlap mappings between new and base KB predicates
    base_preds: set[str] = set()
    for v in pipeline.ks.vyaptis.values():
        base_preds.update(v.antecedents)
        if v.consequent:
            base_preds.add(v.consequent)

    new_preds = set(stage_c.vocabulary) - base_preds
    for new_pred in new_preds:
        new_tokens = set(new_pred.split("_"))
        new_tokens.discard("")
        if not new_tokens:
            continue

        best_score = 0.0
        best_base = ""
        for base_pred in base_preds:
            base_tokens = set(base_pred.split("_"))
            base_tokens.discard("")
            if not base_tokens:
                continue
            overlap = len(new_tokens & base_tokens)
            total = min(len(new_tokens), len(base_tokens))
            score = overlap / total if total > 0 else 0.0
            if score > best_score:
                best_score = score
                best_base = base_pred

        # Only add strong token overlaps (>60%) as synonyms
        if best_score > 0.6 and best_base and new_pred not in synonym_table:
            synonym_table[new_pred] = best_base

    return synonym_table
