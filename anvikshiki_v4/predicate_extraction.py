"""
Automated Predicate Extraction Pipeline — Stages A through E + Orchestrator.

Extracts fine-grained predicates from guide text, decomposes existing vyaptis
into sub-predicates, canonicalizes, constructs new vyaptis, and validates
the augmented KnowledgeStore.

Usage:
    from anvikshiki_v4.predicate_extraction import PredicateExtractionPipeline
    from anvikshiki_v4.extraction_schema import ExtractionConfig
    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

    ks = load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")
    pipeline = PredicateExtractionPipeline(ks)
    augmented_ks, validation, stage_d = pipeline(guide_text={"ch02": ch2_md, ...})
"""

from __future__ import annotations

import re
from typing import Optional

import dspy

from .extraction_schema import (
    CandidatePredicate,
    ClaimType,
    ExtractionConfig,
    PredicateNode,
    PredicateRelation,
    Provenance,
    ProposedVyapti,
    StageAOutput,
    StageBOutput,
    StageCOutput,
    StageDOutput,
    SynonymCluster,
    ValidationResult,
)
from .schema import (
    CausalStatus,
    Confidence,
    DecayRisk,
    EpistemicStatus,
    KnowledgeStore,
    Vyapti,
)


# ─── Utilities ─────────────────────────────────────────────────


SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
MAX_PREDICATE_LEN = 60


def _enforce_snake_case(name: str) -> str:
    """Convert any string to valid snake_case predicate name."""
    # CamelCase → snake_case
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    # Replace non-alphanumeric with underscore
    s = re.sub(r"[^a-z0-9]+", "_", s.lower())
    # Strip leading/trailing underscores, collapse doubles
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:MAX_PREDICATE_LEN] if s else "unknown_predicate"


def _normalize_predicate_name(name: str) -> str:
    """Normalize and validate a predicate name."""
    norm = _enforce_snake_case(name)
    if not norm or not SNAKE_CASE_RE.match(norm):
        return ""
    return norm


def _split_into_sections(text: str, max_tokens: int = 512) -> list[str]:
    """Split markdown text into sections respecting ### boundaries."""
    sections = []
    current = []
    current_len = 0

    for line in text.split("\n"):
        words = len(line.split())
        if line.startswith("###") and current:
            sections.append("\n".join(current))
            current = [line]
            current_len = words
        elif current_len + words > max_tokens and current:
            sections.append("\n".join(current))
            current = [line]
            current_len = words
        else:
            current.append(line)
            current_len += words

    if current:
        sections.append("\n".join(current))

    return sections


def _detect_cycles(adj: dict[str, set[str]]) -> list[list[str]]:
    """Detect cycles in a predicate DAG using DFS."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {}
    for node in adj:
        color[node] = WHITE
    for targets in adj.values():
        for t in targets:
            if t not in color:
                color[t] = WHITE

    cycles: list[list[str]] = []
    path: list[str] = []

    def dfs(node: str) -> None:
        color[node] = GRAY
        path.append(node)
        for neighbor in adj.get(node, set()):
            if color.get(neighbor, WHITE) == GRAY:
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
            elif color.get(neighbor, WHITE) == WHITE:
                dfs(neighbor)
        path.pop()
        color[node] = BLACK

    for node in list(color.keys()):
        if color[node] == WHITE:
            dfs(node)

    return cycles


# ─── DSPy Signatures ──────────────────────────────────────────


class ExtractPredicates(dspy.Signature):
    """Extract domain predicates from instructional text.

    A predicate is a testable property of a domain entity.
    Look for: causal claims ("X causes Y"), conditional statements ("if X then Y"),
    metric relationships ("X is measured by Y"), and scope conditions.
    Use ONLY snake_case names. Return empty list if no predicates found.
    Extract NEW predicates not already in the existing set."""

    section_text: str = dspy.InputField(
        desc="A section of guide text (markdown)"
    )
    chapter_id: str = dspy.InputField(desc="Chapter identifier, e.g. 'ch02'")
    existing_predicates: str = dspy.InputField(
        desc="Already-known predicates from the knowledge store"
    )
    domain_context: str = dspy.InputField(
        desc="Domain type and brief description"
    )

    reasoning: str = dspy.OutputField(
        desc="Step-by-step: what causal/conditional claims does this text make?"
    )
    predicates: list[str] = dspy.OutputField(
        desc="Extracted predicate names in snake_case. Empty list if none."
    )
    descriptions: list[str] = dspy.OutputField(
        desc="One-sentence description for each predicate, same order."
    )
    claim_types: list[str] = dspy.OutputField(
        desc="Claim type for each: causal, conditional, metric, definitional, scope, negation"
    )
    related_vyaptis: list[str] = dspy.OutputField(
        desc="Related existing vyapti ID for each (or 'none')"
    )


class DecomposeVyapti(dspy.Signature):
    """Given a high-level vyapti and relevant guide text, identify sub-predicates
    that compose the vyapti's antecedents or consequent.

    Think step by step: what specific conditions, metrics, or sub-concepts
    does the guide text mention that are part of this higher-level predicate?"""

    vyapti_summary: str = dspy.InputField(
        desc="The vyapti: ID, name, antecedents, consequent, statement"
    )
    guide_excerpt: str = dspy.InputField(
        desc="Relevant guide text for this vyapti's chapter"
    )
    stage_a_candidates: str = dspy.InputField(
        desc="Candidate predicates already extracted from Stage A"
    )

    reasoning: str = dspy.OutputField(
        desc="Analysis: what sub-concepts does the guide text reveal?"
    )
    sub_predicates: list[str] = dspy.OutputField(
        desc="Sub-predicate names in snake_case. Empty if no decomposition."
    )
    sub_descriptions: list[str] = dspy.OutputField(
        desc="One-sentence description for each sub-predicate."
    )
    parent_predicate: str = dspy.OutputField(
        desc="Which existing predicate these decompose"
    )
    relation_type: str = dspy.OutputField(
        desc="'composes' (AND), 'alternative' (OR), or 'none'"
    )


class ResolveSynonyms(dspy.Signature):
    """Given candidate predicate names with descriptions, identify which are
    synonyms and choose the best canonical name.

    Prefer names that are: specific (not generic), consistent with existing
    naming conventions, under 40 characters, snake_case."""

    candidate_list: str = dspy.InputField(
        desc="Numbered list of predicate names with descriptions"
    )
    existing_naming_examples: str = dspy.InputField(
        desc="Examples of existing predicate names for style reference"
    )

    canonical_names: list[str] = dspy.OutputField(
        desc="Final deduplicated predicate names"
    )
    synonym_mappings: list[str] = dspy.OutputField(
        desc="Mappings like 'old_name -> canonical_name' for merged predicates"
    )


class ConstructVyapti(dspy.Signature):
    """Construct a complete vyapti (causal rule) from a predicate relationship.

    Be conservative: set epistemic_status to 'hypothesis' unless the guide text
    explicitly presents strong evidence. Keep confidence values moderate."""

    predicate_relationship: str = dspy.InputField(
        desc="Antecedent(s), consequent, evidence text"
    )
    guide_evidence: str = dspy.InputField(
        desc="Relevant guide text passages"
    )
    existing_vyaptis_context: str = dspy.InputField(
        desc="Related existing vyaptis for style reference"
    )
    reference_bank: str = dspy.InputField(
        desc="Available source IDs from the reference bank"
    )

    name: str = dspy.OutputField(desc="Short descriptive name for the vyapti")
    statement: str = dspy.OutputField(
        desc="Precise English statement of the invariable relation"
    )
    causal_status: str = dspy.OutputField(
        desc="One of: structural, regulatory, empirical, definitional"
    )
    scope_conditions: list[str] = dspy.OutputField(
        desc="Contexts where this holds"
    )
    scope_exclusions: list[str] = dspy.OutputField(
        desc="Contexts where this breaks"
    )
    confidence_existence: float = dspy.OutputField(
        desc="0.0-1.0: confidence the rule exists"
    )
    confidence_formulation: float = dspy.OutputField(
        desc="0.0-1.0: confidence the formulation is precise"
    )
    epistemic_status: str = dspy.OutputField(
        desc="One of: established, hypothesis, open, contested"
    )
    sources: list[str] = dspy.OutputField(
        desc="Source IDs from the reference bank"
    )
    reasoning: str = dspy.OutputField(
        desc="Why this relationship exists and what evidence supports it"
    )


# ─── Reward Functions ──────────────────────────────────────────


def _extraction_reward(args: dict, pred: dspy.Prediction) -> float:
    """Reward for Stage A extraction quality."""
    score = 0.0
    predicates = getattr(pred, "predicates", None) or []

    # 1. Non-empty extraction (but not too many)
    if predicates:
        score += 0.2
        if len(predicates) <= 20:
            score += 0.1

    # 2. All names are valid snake_case
    if predicates and all(
        _enforce_snake_case(p) == p for p in predicates
    ):
        score += 0.2

    # 3. Descriptions present and match count
    descriptions = getattr(pred, "descriptions", None) or []
    if descriptions and len(descriptions) == len(predicates):
        score += 0.15

    # 4. Novel vs existing
    existing_text = args.get("existing_predicates", "")
    if predicates:
        novel = sum(1 for p in predicates if p not in existing_text)
        if novel / max(len(predicates), 1) > 0.3:
            score += 0.15

    # 5. Reasoning present and substantive
    reasoning = getattr(pred, "reasoning", "") or ""
    if len(reasoning) > 50:
        score += 0.2

    return min(1.0, score)


def _vyapti_construction_reward(args: dict, pred: dspy.Prediction) -> float:
    """Reward for Stage D vyapti construction quality."""
    score = 0.0

    name = getattr(pred, "name", "") or ""
    statement = getattr(pred, "statement", "") or ""
    causal_status = getattr(pred, "causal_status", "") or ""
    epistemic_status = getattr(pred, "epistemic_status", "") or ""
    conf_e = getattr(pred, "confidence_existence", 0.0)
    conf_f = getattr(pred, "confidence_formulation", 0.0)
    sources = getattr(pred, "sources", None) or []

    # 1. Has name and statement
    if name and len(statement) > 30:
        score += 0.25

    # 2. Conservative confidence
    if 0.0 < conf_e <= 0.85 and 0.0 < conf_f <= 0.85:
        score += 0.15

    # 3. Has scope conditions or exclusions
    scope_cond = getattr(pred, "scope_conditions", None) or []
    scope_excl = getattr(pred, "scope_exclusions", None) or []
    if scope_cond or scope_excl:
        score += 0.15

    # 4. Has sources
    if sources:
        score += 0.15

    # 5. Valid causal status
    if causal_status in ("structural", "regulatory", "empirical", "definitional"):
        score += 0.15

    # 6. Conservative epistemic status
    if epistemic_status in ("hypothesis", "open", "contested"):
        score += 0.15

    return min(1.0, score)


# ─── Stage A: Extract Candidate Predicates ─────────────────────


class StageAExtractor(dspy.Module):
    """Stage A: Extract candidate predicates from guide text sections."""

    def __init__(self, knowledge_store: KnowledgeStore, config: ExtractionConfig):
        super().__init__()
        self.ks = knowledge_store
        self.config = config

        if config.model_tier == "small":
            self.extractor = dspy.ChainOfThought(ExtractPredicates)
        else:
            self.extractor = dspy.ChainOfThought(ExtractPredicates)

    def forward(self, chapter_text: str, chapter_id: str) -> StageAOutput:
        existing = self._build_predicate_list()
        domain_ctx = f"Domain: {self.ks.domain_type.value}."

        max_tokens = 512 if self.config.model_tier == "small" else 2000
        sections = _split_into_sections(chapter_text, max_tokens=max_tokens)

        all_candidates: list[CandidatePredicate] = []
        zero_sections = 0

        for i, section in enumerate(sections):
            if len(section.strip().split()) < 20:
                continue

            try:
                result = self.extractor(
                    section_text=section,
                    chapter_id=chapter_id,
                    existing_predicates=existing,
                    domain_context=domain_ctx,
                )
            except Exception:
                zero_sections += 1
                continue

            predicates = getattr(result, "predicates", None) or []
            descriptions = getattr(result, "descriptions", None) or []
            claim_types = getattr(result, "claim_types", None) or []
            related = getattr(result, "related_vyaptis", None) or []

            if not predicates:
                zero_sections += 1
                continue

            for j, pred_name in enumerate(predicates):
                norm = _normalize_predicate_name(pred_name)
                if not norm:
                    continue

                desc = descriptions[j] if j < len(descriptions) else ""
                ct_str = claim_types[j] if j < len(claim_types) else "causal"
                rel = related[j] if j < len(related) else "none"

                try:
                    ct = ClaimType(ct_str)
                except ValueError:
                    ct = ClaimType.CAUSAL

                candidate = CandidatePredicate(
                    name=norm,
                    description=desc,
                    claim_type=ct,
                    provenance=Provenance(
                        chapter_id=chapter_id,
                        paragraph_index=i,
                        confidence=0.5,
                    ),
                    related_existing_vyapti=rel if rel != "none" else None,
                )

                if candidate.provenance.confidence >= self.config.min_confidence:
                    all_candidates.append(candidate)

        return StageAOutput(
            candidates=all_candidates,
            chapter_id=chapter_id,
            section_count=len(sections),
            zero_predicate_sections=zero_sections,
        )

    def _build_predicate_list(self) -> str:
        """Build seed ontology snippet showing existing predicates."""
        lines = [
            "EXISTING PREDICATES (extract NEW sub-predicates, not these):"
        ]
        all_preds: set[str] = set()
        for vid, v in self.ks.vyaptis.items():
            all_preds.update(v.antecedents)
            if v.consequent:
                all_preds.add(v.consequent)
            lines.append(
                f"  {vid}: {', '.join(v.antecedents)} -> {v.consequent}"
            )
        lines.append(f"\nAll known: {sorted(all_preds)}")
        return "\n".join(lines)


# ─── Stage B: Hierarchical Decomposition ───────────────────────


class StageBDecomposer(dspy.Module):
    """Stage B: Decompose existing predicates into hierarchical sub-predicates."""

    def __init__(self, knowledge_store: KnowledgeStore, config: ExtractionConfig):
        super().__init__()
        self.ks = knowledge_store
        self.config = config
        self.decomposer = dspy.ChainOfThought(DecomposeVyapti)

    def forward(
        self,
        stage_a: StageAOutput,
        guide_text: dict[str, str],
    ) -> StageBOutput:
        nodes: dict[str, PredicateNode] = {}
        decomposition_count = 0

        for vid, v in self.ks.vyaptis.items():
            chapter_id = self._find_chapter_for_vyapti(vid)
            if not chapter_id or chapter_id not in guide_text:
                continue

            excerpt = guide_text[chapter_id][:4000]

            relevant_candidates = [
                c
                for c in stage_a.candidates
                if c.related_existing_vyapti == vid
                or c.provenance.chapter_id == chapter_id
            ]
            candidates_str = "\n".join(
                f"  - {c.name}: {c.description}" for c in relevant_candidates
            ) or "None"

            vyapti_str = (
                f"ID: {vid}, Name: {v.name}\n"
                f"Antecedents: {v.antecedents}\n"
                f"Consequent: {v.consequent}\n"
                f"Statement: {v.statement}"
            )

            try:
                result = self.decomposer(
                    vyapti_summary=vyapti_str,
                    guide_excerpt=excerpt,
                    stage_a_candidates=candidates_str,
                )
            except Exception:
                continue

            sub_preds = getattr(result, "sub_predicates", None) or []
            sub_descs = getattr(result, "sub_descriptions", None) or []
            parent_pred = getattr(result, "parent_predicate", "") or ""
            rel_type = getattr(result, "relation_type", "composes") or "composes"

            if not sub_preds:
                continue

            decomposition_count += 1

            try:
                relation = PredicateRelation(rel_type)
            except ValueError:
                relation = PredicateRelation.COMPOSES

            parent = _normalize_predicate_name(parent_pred)
            if not parent:
                # Default to the first antecedent
                parent = v.antecedents[0] if v.antecedents else v.consequent

            child_names = []
            for k, sp_name in enumerate(sub_preds):
                norm = _normalize_predicate_name(sp_name)
                if not norm or norm == parent:
                    continue
                desc = sub_descs[k] if k < len(sub_descs) else ""
                nodes[norm] = PredicateNode(
                    predicate=norm,
                    description=desc,
                    parent=parent,
                    relation_to_parent=relation,
                    depth=1,
                    source_vyapti=vid,
                )
                child_names.append(norm)

            # Add/update parent node
            if parent not in nodes:
                nodes[parent] = PredicateNode(
                    predicate=parent,
                    description=f"From {vid}: {v.name}",
                    depth=0,
                    source_vyapti=vid,
                    children=child_names,
                )
            else:
                nodes[parent].children.extend(child_names)

        return StageBOutput(nodes=nodes, decomposition_count=decomposition_count)

    def _find_chapter_for_vyapti(self, vyapti_id: str) -> Optional[str]:
        """Look up which chapter introduces this vyapti."""
        for cid, fp in self.ks.chapter_fingerprints.items():
            if vyapti_id in fp.vyaptis_introduced:
                return cid
        return None


# ─── Stage C: Canonicalize and Deduplicate ─────────────────────


class StageCCanonicalizer(dspy.Module):
    """Stage C: Canonicalize and deduplicate predicates."""

    def __init__(self, knowledge_store: KnowledgeStore, config: ExtractionConfig):
        super().__init__()
        self.ks = knowledge_store
        self.config = config
        self.resolver = dspy.ChainOfThought(ResolveSynonyms)

    def forward(
        self,
        stage_a: StageAOutput,
        stage_b: StageBOutput,
    ) -> StageCOutput:
        # Collect all candidates
        all_candidates: dict[str, str] = {}
        for c in stage_a.candidates:
            all_candidates[c.name] = c.description
        for name, node in stage_b.nodes.items():
            if name not in all_candidates:
                all_candidates[name] = node.description

        # Deterministic pre-filtering
        cleaned: dict[str, str] = {}
        for name, desc in all_candidates.items():
            norm = _normalize_predicate_name(name)
            if norm and norm not in cleaned:
                cleaned[norm] = desc

        if len(cleaned) <= 1:
            return StageCOutput(
                vocabulary=list(cleaned.keys()),
                synonym_clusters=[],
                removed_count=len(all_candidates) - len(cleaned),
            )

        # Group potential synonyms by shared tokens
        clusters = self._cluster_by_tokens(cleaned)
        synonym_clusters: list[SynonymCluster] = []

        ambiguous = [c for c in clusters if len(c) > 1]
        if ambiguous:
            # Use LLM to resolve ambiguous clusters
            candidate_list = "\n".join(
                f"{i + 1}. {name}: {cleaned[name]}"
                for i, name in enumerate(cleaned.keys())
            )
            existing_examples = ", ".join(
                sorted(
                    set(
                        pred
                        for v in self.ks.vyaptis.values()
                        for pred in v.antecedents + [v.consequent]
                    )
                )[:20]
            )

            try:
                result = self.resolver(
                    candidate_list=candidate_list,
                    existing_naming_examples=existing_examples,
                )
                canonical_names = getattr(result, "canonical_names", None) or []
                mappings = getattr(result, "synonym_mappings", None) or []

                # Parse mappings into SynonymCluster objects
                rename_map: dict[str, str] = {}
                for mapping in mappings:
                    if " -> " in mapping:
                        old, new = mapping.split(" -> ", 1)
                        old = _normalize_predicate_name(old.strip())
                        new = _normalize_predicate_name(new.strip())
                        if old and new and old != new:
                            rename_map[old] = new

                # Build clusters
                canonical_to_alts: dict[str, list[str]] = {}
                for old, new in rename_map.items():
                    canonical_to_alts.setdefault(new, []).append(old)
                for canonical, alts in canonical_to_alts.items():
                    synonym_clusters.append(
                        SynonymCluster(
                            canonical=canonical,
                            alternatives=alts,
                            merge_reason="LLM synonym resolution",
                        )
                    )

                # Build final vocabulary
                removed = set(rename_map.keys())
                unique = [n for n in cleaned if n not in removed]
                # Add any canonical names not in cleaned
                for c in canonical_names:
                    norm = _normalize_predicate_name(c)
                    if norm and norm not in unique:
                        unique.append(norm)

            except Exception:
                unique = list(cleaned.keys())
        else:
            unique = list(cleaned.keys())

        return StageCOutput(
            vocabulary=unique,
            synonym_clusters=synonym_clusters,
            removed_count=len(all_candidates) - len(unique),
        )

    @staticmethod
    def _cluster_by_tokens(
        predicates: dict[str, str],
    ) -> list[list[str]]:
        """Cluster predicates sharing >50% tokens (cheap heuristic)."""
        names = list(predicates.keys())
        token_sets = {n: set(n.split("_")) for n in names}
        visited: set[str] = set()
        clusters: list[list[str]] = []

        for n in names:
            if n in visited:
                continue
            cluster = [n]
            visited.add(n)
            for m in names:
                if m in visited:
                    continue
                overlap = len(token_sets[n] & token_sets[m])
                total = min(len(token_sets[n]), len(token_sets[m]))
                if total > 0 and overlap / total > 0.5:
                    cluster.append(m)
                    visited.add(m)
            clusters.append(cluster)

        return clusters


# ─── Stage D: Construct New Vyaptis ────────────────────────────


class StageDConstructor(dspy.Module):
    """Stage D: Construct new vyaptis from extracted predicates."""

    def __init__(self, knowledge_store: KnowledgeStore, config: ExtractionConfig):
        super().__init__()
        self.ks = knowledge_store
        self.config = config
        self.constructor = dspy.ChainOfThought(ConstructVyapti)

    def forward(
        self,
        stage_a: StageAOutput,
        stage_b: StageBOutput,
        stage_c: StageCOutput,
        guide_text: dict[str, str],
    ) -> StageDOutput:
        new_vyaptis: list[ProposedVyapti] = []
        refinement_vyaptis: list[ProposedVyapti] = []
        vocab_set = set(stage_c.vocabulary)

        # Determine next vyapti ID number
        existing_ids = sorted(self.ks.vyaptis.keys())
        next_num = (
            max((int(vid[1:]) for vid in existing_ids), default=0) + 1
        )

        # Build relationships from Stage B decompositions
        for name, node in stage_b.nodes.items():
            if node.depth == 0:
                continue  # Skip existing chapter-level predicates
            if name not in vocab_set:
                continue  # Removed in canonicalization
            if not node.parent:
                continue

            vid = f"V{next_num:02d}"
            next_num += 1

            # Get evidence text
            chapter_id = self._get_chapter_for_predicate(node)
            evidence = guide_text.get(chapter_id, "")[:2000] if chapter_id else ""

            # Get related existing vyapti context
            parent_vyapti = self.ks.vyaptis.get(node.source_vyapti or "")
            context = ""
            if parent_vyapti:
                context = (
                    f"Parent: {node.source_vyapti}: {parent_vyapti.name}\n"
                    f"Antecedents: {parent_vyapti.antecedents}\n"
                    f"Consequent: {parent_vyapti.consequent}"
                )

            sources_str = ", ".join(sorted(self.ks.reference_bank.keys())[:30])

            try:
                result = self.constructor(
                    predicate_relationship=(
                        f"Antecedent: {name}\n"
                        f"Consequent: {node.parent}\n"
                        f"Relation: {node.relation_to_parent or 'composes'}\n"
                        f"Description: {node.description}"
                    ),
                    guide_evidence=evidence,
                    existing_vyaptis_context=context or "None",
                    reference_bank=sources_str or "None",
                )
            except Exception:
                continue

            vyapti = ProposedVyapti(
                id=vid,
                name=getattr(result, "name", "") or f"Sub-rule of {node.parent}",
                statement=getattr(result, "statement", "") or "",
                causal_status=getattr(result, "causal_status", "empirical") or "empirical",
                antecedents=[name],
                consequent=node.parent,
                scope_conditions=getattr(result, "scope_conditions", None) or [],
                scope_exclusions=getattr(result, "scope_exclusions", None) or [],
                confidence_existence=min(
                    getattr(result, "confidence_existence", 0.7) or 0.7, 0.85
                ),
                confidence_formulation=min(
                    getattr(result, "confidence_formulation", 0.6) or 0.6, 0.85
                ),
                epistemic_status=getattr(result, "epistemic_status", "hypothesis") or "hypothesis",
                sources=getattr(result, "sources", None) or [],
                parent_vyapti=node.source_vyapti,
            )

            if node.source_vyapti:
                refinement_vyaptis.append(vyapti)
            else:
                new_vyaptis.append(vyapti)

        # Also handle Stage A causal/conditional claims not captured by Stage B
        handled_names = set(stage_b.nodes.keys())
        for candidate in stage_a.candidates:
            if candidate.name not in vocab_set:
                continue
            if candidate.claim_type not in (ClaimType.CAUSAL, ClaimType.CONDITIONAL):
                continue
            if candidate.name in handled_names:
                continue

            # Skip if this predicate already exists in the KB
            existing_preds = set()
            for v in self.ks.vyaptis.values():
                existing_preds.update(v.antecedents)
                existing_preds.add(v.consequent)
            if candidate.name in existing_preds:
                continue

            handled_names.add(candidate.name)

            vid = f"V{next_num:02d}"
            next_num += 1

            # This is a standalone new predicate — create a minimal vyapti
            new_vyaptis.append(
                ProposedVyapti(
                    id=vid,
                    name=candidate.description[:80] if candidate.description else candidate.name,
                    statement=candidate.provenance.sentence or candidate.description,
                    causal_status="empirical",
                    antecedents=[candidate.name],
                    consequent=candidate.name + "_effect",
                    confidence_existence=0.6,
                    confidence_formulation=0.5,
                    epistemic_status="hypothesis",
                    sources=[],
                    parent_vyapti=candidate.related_existing_vyapti,
                )
            )

            # Cap per chapter
            chapter_counts: dict[str, int] = {}
            for v in new_vyaptis + refinement_vyaptis:
                ch = v.parent_vyapti or "unknown"
                chapter_counts[ch] = chapter_counts.get(ch, 0) + 1

        return StageDOutput(
            new_vyaptis=new_vyaptis[: self.config.max_new_vyaptis_per_chapter * 10],
            refinement_vyaptis=refinement_vyaptis,
        )

    def _get_chapter_for_predicate(self, node: PredicateNode) -> Optional[str]:
        """Find chapter for a predicate via its source vyapti."""
        if not node.source_vyapti:
            return None
        for cid, fp in self.ks.chapter_fingerprints.items():
            if node.source_vyapti in fp.vyaptis_introduced:
                return cid
        return None


# ─── Stage E: Validate and Merge (Deterministic) ──────────────


class StageEValidator:
    """Stage E: Validate and merge new vyaptis with existing KB."""

    def __init__(self, knowledge_store: KnowledgeStore):
        self.ks = knowledge_store

    def validate_and_merge(
        self,
        stage_d: StageDOutput,
    ) -> tuple[KnowledgeStore, ValidationResult]:
        errors = ValidationResult()
        augmented = self.ks.model_copy(deep=True)

        all_proposed = stage_d.new_vyaptis + stage_d.refinement_vyaptis

        # Step 1: Check for DAG cycles
        adj: dict[str, set[str]] = {}
        for v in augmented.vyaptis.values():
            for ant in v.antecedents:
                adj.setdefault(ant, set()).add(v.consequent)

        for proposed in all_proposed:
            for ant in proposed.antecedents:
                adj.setdefault(ant, set()).add(proposed.consequent)

        cycles = _detect_cycles(adj)
        if cycles:
            errors.cycle_errors = [
                f"Cycle: {' -> '.join(c)}" for c in cycles
            ]
            cycle_preds: set[str] = set()
            for c in cycles:
                cycle_preds.update(c)
            all_proposed = [
                v for v in all_proposed if v.consequent not in cycle_preds
            ]

        # Step 2: Check for orphan predicates (warnings, not errors)
        all_consequents = set(v.consequent for v in augmented.vyaptis.values())
        all_consequents.update(v.consequent for v in all_proposed)
        for proposed in all_proposed:
            for ant in proposed.antecedents:
                if ant not in all_consequents:
                    errors.orphan_predicates.append(ant)

        # Step 3: Validate against Pydantic schema and add to KS
        for proposed in all_proposed:
            try:
                # Map causal_status string to enum
                try:
                    cs = CausalStatus(proposed.causal_status)
                except ValueError:
                    cs = CausalStatus.EMPIRICAL

                try:
                    es = EpistemicStatus(proposed.epistemic_status)
                except ValueError:
                    es = EpistemicStatus.WORKING_HYPOTHESIS

                try:
                    dr = DecayRisk(proposed.decay_risk)
                except ValueError:
                    dr = DecayRisk.MODERATE

                vyapti = Vyapti(
                    id=proposed.id,
                    name=proposed.name,
                    statement=proposed.statement,
                    causal_status=cs,
                    scope_conditions=proposed.scope_conditions,
                    scope_exclusions=proposed.scope_exclusions,
                    confidence=Confidence(
                        existence=proposed.confidence_existence,
                        formulation=proposed.confidence_formulation,
                        evidence=proposed.evidence_type,
                    ),
                    epistemic_status=es,
                    decay_risk=dr,
                    sources=proposed.sources,
                    antecedents=proposed.antecedents,
                    consequent=proposed.consequent,
                )
                augmented.vyaptis[proposed.id] = vyapti
            except Exception as e:
                errors.datalog_errors.append(
                    f"Vyapti {proposed.id} validation failed: {e}"
                )

        # Step 4: Test-compile through DatalogEngine
        try:
            from .datalog_engine import DatalogEngine, EpistemicValue, Fact, Rule

            engine = DatalogEngine(boolean_mode=True)
            for vid, v in augmented.vyaptis.items():
                engine.add_rule(
                    Rule(
                        vyapti_id=vid,
                        name=v.name,
                        head=v.consequent,
                        body_positive=v.antecedents,
                        body_negative=v.scope_exclusions,
                        confidence=EpistemicValue.ESTABLISHED,
                    )
                )

            # Add synthetic facts for all antecedents
            all_antecedents: set[str] = set()
            for v in augmented.vyaptis.values():
                all_antecedents.update(v.antecedents)

            for ant in all_antecedents:
                engine.add_fact(
                    Fact(
                        predicate=ant,
                        entity="test",
                        value=EpistemicValue.ESTABLISHED,
                    )
                )

            engine.evaluate()
        except Exception as e:
            errors.datalog_errors.append(f"Datalog evaluation failed: {e}")

        # Step 5: Compute coverage ratio
        old_preds = set(
            pred
            for v in self.ks.vyaptis.values()
            for pred in v.antecedents + [v.consequent]
        )
        new_preds = set(
            pred
            for v in augmented.vyaptis.values()
            for pred in v.antecedents + [v.consequent]
        )
        total = len(new_preds)
        added = len(new_preds - old_preds)
        errors.coverage_ratio = added / max(total, 1)

        errors.is_valid = not errors.cycle_errors and not errors.datalog_errors

        return augmented, errors


# ─── Pipeline Orchestrator ─────────────────────────────────────


class PredicateExtractionPipeline(dspy.Module):
    """Complete predicate extraction pipeline: Stages A through E.

    Stage F (HITL) is invoked separately after this pipeline completes.
    """

    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        config: Optional[ExtractionConfig] = None,
    ):
        super().__init__()
        self.config = config or ExtractionConfig()
        self.ks = knowledge_store

        self.stage_a = StageAExtractor(knowledge_store, self.config)
        self.stage_b = StageBDecomposer(knowledge_store, self.config)
        self.stage_c = StageCCanonicalizer(knowledge_store, self.config)
        self.stage_d = StageDConstructor(knowledge_store, self.config)
        self.stage_e = StageEValidator(knowledge_store)

    def forward(
        self,
        guide_text: dict[str, str],
    ) -> tuple[KnowledgeStore, ValidationResult, StageDOutput]:
        """Run the full extraction pipeline.

        Args:
            guide_text: chapter_id -> chapter markdown text

        Returns:
            (augmented_ks, validation_result, stage_d_output)
        """
        # Stage A: Extract from each chapter
        all_stage_a = StageAOutput(candidates=[], chapter_id="all")
        for chapter_id, text in guide_text.items():
            chapter_result = self.stage_a(
                chapter_text=text, chapter_id=chapter_id
            )
            all_stage_a.candidates.extend(chapter_result.candidates)
            all_stage_a.section_count += chapter_result.section_count
            all_stage_a.zero_predicate_sections += (
                chapter_result.zero_predicate_sections
            )

        # Stage B: Hierarchical decomposition
        stage_b = self.stage_b(stage_a=all_stage_a, guide_text=guide_text)

        # Stage C: Canonicalize
        stage_c = self.stage_c(stage_a=all_stage_a, stage_b=stage_b)

        # Stage D: Construct vyaptis
        stage_d = self.stage_d(
            stage_a=all_stage_a,
            stage_b=stage_b,
            stage_c=stage_c,
            guide_text=guide_text,
        )

        # Stage E: Validate and merge
        augmented_ks, validation = self.stage_e.validate_and_merge(stage_d)

        return augmented_ks, validation, stage_d


# ─── Iterative Refinement ─────────────────────────────────────


def run_iterative_extraction(
    knowledge_store: KnowledgeStore,
    guide_text: dict[str, str],
    config: Optional[ExtractionConfig] = None,
    max_passes: int = 3,
    improvement_threshold: float = 0.02,
) -> tuple[KnowledgeStore, ValidationResult]:
    """Run the pipeline multiple times, feeding results back as new seed.

    Pass 1: Initial extraction from seed KB.
    Pass 2+: Use augmented KB as new seed — catches predicates that depend
             on predicates discovered in previous pass.
    """
    cfg = config or ExtractionConfig()
    best_ks = knowledge_store
    best_coverage = 0.0
    best_validation = ValidationResult()

    for pass_num in range(max_passes):
        pipeline = PredicateExtractionPipeline(best_ks, cfg)
        augmented, validation, _ = pipeline(guide_text)

        if validation.is_valid and validation.coverage_ratio > best_coverage:
            improvement = validation.coverage_ratio - best_coverage
            best_ks = augmented
            best_coverage = validation.coverage_ratio
            best_validation = validation

            if improvement < improvement_threshold:
                break
        else:
            break

    return best_ks, best_validation
