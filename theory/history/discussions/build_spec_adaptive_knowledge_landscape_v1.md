# Adaptive Knowledge Landscape — Build Specification

## From MVV to Full System: Implementation Manual for Each Version

**Companion to:** `adaptive-knowledge-landscape.md` (brainstorm discussion)
**Target codebase:** `anvikshiki_ecosystem/anvikshiki_v4/`
**Stack:** DSPy 3.1.x + Pydantic + Custom Datalog + YAML + SQLite (v3+)
**Date:** March 2026

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Shared Schema Extensions](#2-shared-schema-extensions)
3. [v1: Ephemeral Augmentation (MVV)](#3-v1-ephemeral-augmentation-mvv)
4. [v2: Web Search + Evidence Sourcing](#4-v2-web-search--evidence-sourcing)
5. [v3: Shadow KB Persistence + HITL Review](#5-v3-shadow-kb-persistence--hitl-review)
6. [v4: Source Reliability Scoring + Vitaṇḍā Stress Test](#6-v4-source-reliability-scoring--vitaṇḍā-stress-test)
7. [v5: Formalized Framework Templates + Multi-Domain](#7-v5-formalized-framework-templates--multi-domain)
8. [Testing Strategy (All Versions)](#8-testing-strategy-all-versions)
9. [Migration Path Between Versions](#9-migration-path-between-versions)

---

## 1. Architecture Overview

### System Flow (All Versions)

```
User Query
    │
    ▼
QueryRefinementPipeline.refine(query)
    │
    ├── coverage >= 0.6 ──────────── PROCEED → engine_v4.forward() as normal
    │
    ├── coverage >= 0.2 ──────────── PARTIAL ─┐
    │                                         │
    └── coverage < 0.2 ───────────── DECLINE ─┤
                                              │
                                              ▼
                                    AugmentationPipeline
                                    ┌─────────────────────┐
                                    │ 1. domain_check()    │  ← Is this in-domain?
                                    │    score < 0.4? SKIP │
                                    │                      │
                                    │ 2. generate()        │  ← v1: LLM only
                                    │                      │    v2+: LLM + web
                                    │                      │
                                    │ 3. validate()        │  ← Reuses Stage E
                                    │                      │
                                    │ 4. merge_kb()        │  ← Temporary merge
                                    │                      │
                                    │ 5. persist()         │  ← v3+: shadow KB
                                    └─────────┬───────────┘
                                              │
                                              ▼
                                    engine_v4.forward(merged_kb)
```

### Version Scope Summary

| Version | New Files | Modified Files | LLM Calls Added | Key Capability |
|---------|-----------|----------------|-----------------|----------------|
| **v1** | `kb_augmentation.py` | `query_refinement.py`, `engine_v4.py` | +2 per query | Framework-guided predicate generation |
| **v2** | `evidence_search.py` | `kb_augmentation.py` | +1–3 per query | Web-sourced evidence for generated predicates |
| **v3** | `shadow_kb.py`, `review_queue.py` | `kb_augmentation.py`, `schema.py` | +0 | Persistent shadow KB, HITL promotion workflow |
| **v4** | `source_reliability.py` | `kb_augmentation.py`, `evidence_search.py`, `shadow_kb.py` | +1 per query | Cross-source reliability scoring, Vitaṇḍā stress test |
| **v5** | `framework_templates.py`, `domain_registry.py` | `kb_augmentation.py`, data YAML files | +1 per domain | Formal framework YAML, multi-domain generalization |

### Shared Design Principles

1. **Augmented predicates are Vyapti objects.** The rest of the engine never knows they were generated. No special-casing downstream.
2. **Confidence from evidence quality, not KB layer.** A well-sourced augmented predicate outranks a poorly-sourced curated one.
3. **Selective augmentation.** Only augment when frameworks can illuminate the query. Never always-augment (SIGIR 2024: irrelevant retrieval actively hurts).
4. **Reuse existing validation.** Stage E cycle detection + Datalog compilation test applies to all generated predicates.

---

## 2. Shared Schema Extensions

These Pydantic models are introduced in v1 and extended in later versions. Define them in `kb_augmentation.py` initially; refactor to `schema.py` in v3 when they stabilize.

### `AugmentationOrigin` (Enum)

```python
class AugmentationOrigin(str, Enum):
    """Where an augmented predicate came from."""
    LLM_PARAMETRIC = "llm_parametric"      # v1: LLM's internal knowledge
    WEB_SOURCED = "web_sourced"            # v2: web search evidence
    HITL_PROMOTED = "hitl_promoted"        # v3: human-approved from shadow KB
    CROSS_VALIDATED = "cross_validated"    # v4: multi-source agreement
    FRAMEWORK_DERIVED = "framework_derived" # v5: formal framework instantiation
```

### `AugmentationMetadata` (Pydantic BaseModel)

```python
class AugmentationMetadata(BaseModel):
    """Attached to every augmented Vyapti. Tracks origin and lifecycle."""
    origin: AugmentationOrigin
    generated_at: datetime
    generating_query: str                      # the query that triggered generation
    framework_vyaptis_used: list[str]          # which base KB vyaptis guided generation
    framework_applicability_score: float       # 0.0–1.0
    evidence_urls: list[str] = []              # v2+: supporting URLs
    evidence_snippets: list[str] = []          # v2+: relevant quotes
    source_reliability_score: Optional[float] = None  # v4+
    review_status: str = "unreviewed"          # v3+: "unreviewed"|"approved"|"rejected"|"needs_source"
    reviewer_notes: str = ""                   # v3+
    generation_model: str = ""                 # which LLM generated this
    generation_run_id: str = ""                # batch tracking
```

### `AugmentationResult` (Pydantic BaseModel)

```python
class AugmentationResult(BaseModel):
    """Return type of AugmentationPipeline.forward()."""
    augmented: bool                            # did augmentation happen?
    reason: str                                # why or why not
    framework_score: float                     # domain check score
    new_vyaptis: list[Vyapti]                  # generated vyaptis (empty if augmented=False)
    new_predicates: list[str]                  # predicate names introduced
    merged_kb: Optional[KnowledgeStore] = None # merged KB (None if augmented=False)
    metadata: list[AugmentationMetadata] = []  # one per new vyapti
    validation_warnings: list[str] = []        # from Stage E validation
```

---

## 3. v1: Ephemeral Augmentation (MVV)

### What v1 Proves

The core hypothesis: **framework-guided predicate generation produces argumentable knowledge.** If the engine can take an under-represented query, generate structured predicates using existing vyaptis as templates, and run argumentation over the result — the concept works.

### New File: `kb_augmentation.py` (~250 lines)

#### DSPy Signatures

```python
class ScoreFrameworkApplicability(dspy.Signature):
    """Judge whether the engine's reasoning frameworks can illuminate
    a query topic. Score 0.0 = clearly outside domain, 1.0 = directly applicable.

    Consider:
    1. Do the vyaptis' causal patterns apply to this topic?
    2. Can the hetvabhasas (fallacy detectors) catch real errors in this topic?
    3. Would the chapter reasoning templates produce non-trivial insight?
    4. Is this topic structurally similar to topics the frameworks already cover?"""

    query: str = dspy.InputField(desc="The user's original query")
    interpreted_intent: str = dspy.InputField(desc="From ClarifyIntent step")
    framework_summary: str = dspy.InputField(
        desc="Vyapti names, statements, and chapter key concepts"
    )
    domain_type: str = dspy.InputField(desc="e.g., CRAFT")

    reasoning: str = dspy.OutputField(desc="Why these frameworks do or don't apply")
    applicability_score: float = dspy.OutputField(
        desc="0.0–1.0. >= 0.4 means augmentation is worthwhile"
    )
    applicable_vyaptis: list[str] = dspy.OutputField(
        desc="Vyapti IDs whose causal patterns are relevant (e.g., ['V02','V06'])"
    )
    applicable_chapters: list[str] = dspy.OutputField(
        desc="Chapter IDs whose reasoning templates apply (e.g., ['ch03','ch07'])"
    )
```

```python
class GenerateAugmentationPredicates(dspy.Signature):
    """Generate new vyaptis (causal rules) for a topic that the knowledge base
    doesn't specifically cover, but that the existing frameworks can illuminate.

    RULES:
    - Each vyapti must have antecedents and a consequent in snake_case
    - Reuse existing predicate names where they apply (e.g., value_creation, binding_constraint_identified)
    - New predicate names must be specific to the query topic
    - confidence_existence <= 0.75 (these are generated, not curated)
    - epistemic_status = "hypothesis" for all generated vyaptis
    - causal_status should reflect the actual causal nature of the claim
    - scope_conditions must include the query's specific domain (e.g., "supply_chain_context")
    - Chain into existing vyaptis where possible (use their consequents as your antecedents)"""

    query: str = dspy.InputField()
    interpreted_intent: str = dspy.InputField()
    applicable_vyaptis: str = dspy.InputField(
        desc="Full text of applicable vyaptis including their antecedents, consequents, scope conditions"
    )
    chapter_context: str = dspy.InputField(
        desc="Relevant chapter key terms, anchoring concepts, reasoning patterns"
    )
    existing_predicates: str = dspy.InputField(
        desc="All predicate names in the current KB vocabulary"
    )

    reasoning: str = dspy.OutputField(
        desc="How you're applying the existing frameworks to this specific topic"
    )
    vyapti_names: list[str] = dspy.OutputField(desc="snake_case names for each new vyapti")
    vyapti_statements: list[str] = dspy.OutputField(
        desc="Natural language statement for each (parallel to names)"
    )
    antecedents_list: list[str] = dspy.OutputField(
        desc="Comma-separated antecedent predicates for each vyapti (parallel to names)"
    )
    consequents: list[str] = dspy.OutputField(
        desc="Consequent predicate for each vyapti (parallel to names)"
    )
    causal_statuses: list[str] = dspy.OutputField(
        desc="'structural'|'regulatory'|'empirical'|'definitional' for each (parallel to names)"
    )
    scope_conditions_list: list[str] = dspy.OutputField(
        desc="Comma-separated scope conditions for each vyapti (parallel to names)"
    )
    confidence_existences: list[float] = dspy.OutputField(
        desc="0.0–0.75 existence confidence for each (parallel to names)"
    )
    base_vyaptis_used: list[str] = dspy.OutputField(
        desc="Which existing vyapti IDs informed each new one (parallel to names)"
    )
```

#### `AugmentationPipeline` (dspy.Module)

```python
class AugmentationPipeline(dspy.Module):
    """v1: Ephemeral, LLM-parametric-only augmentation."""

    APPLICABILITY_THRESHOLD: float = 0.4
    MAX_NEW_VYAPTIS: int = 8

    def __init__(
        self,
        knowledge_store: KnowledgeStore,
    ):
        super().__init__()
        self.ks = knowledge_store
        self.snippet_builder = OntologySnippetBuilder()
        self.domain_scorer = dspy.ChainOfThought(ScoreFrameworkApplicability)
        self.generator = dspy.ChainOfThought(GenerateAugmentationPredicates)

    def forward(
        self,
        query: str,
        refinement_result: RefinementResult,
    ) -> AugmentationResult:
        """
        Called when coverage < PROCEED threshold but query might be in-domain.

        Steps:
            1. domain_check — score framework applicability (1 LLM call)
            2. generate    — produce new vyaptis (1 LLM call)
            3. validate    — cycle detection + Datalog compile (0 LLM calls)
            4. merge_kb    — create temporary merged KnowledgeStore

        Returns AugmentationResult with merged_kb ready for engine_v4.
        """
        # Step 1: Domain check
        framework_summary = self._build_framework_summary()
        domain_result = self.domain_scorer(
            query=query,
            interpreted_intent=refinement_result.interpreted_intent,
            framework_summary=framework_summary,
            domain_type=self.ks.domain_type.value,
        )
        score = float(domain_result.applicability_score)

        if score < self.APPLICABILITY_THRESHOLD:
            return AugmentationResult(
                augmented=False,
                reason=f"Framework applicability too low ({score:.2f} < {self.APPLICABILITY_THRESHOLD})",
                framework_score=score,
                new_vyaptis=[],
                new_predicates=[],
            )

        # Step 2: Generate predicates
        applicable_vyaptis_text = self._build_applicable_vyaptis_text(
            domain_result.applicable_vyaptis
        )
        chapter_context = self._build_chapter_context(
            domain_result.applicable_chapters
        )
        existing_predicates = self._get_all_predicates()

        gen_result = self.generator(
            query=query,
            interpreted_intent=refinement_result.interpreted_intent,
            applicable_vyaptis=applicable_vyaptis_text,
            chapter_context=chapter_context,
            existing_predicates=existing_predicates,
        )

        # Step 3: Parse + validate
        new_vyaptis = self._parse_generated_vyaptis(
            gen_result,
            domain_result.applicable_vyaptis,
        )
        new_vyaptis, warnings = self._validate(new_vyaptis)

        if not new_vyaptis:
            return AugmentationResult(
                augmented=False,
                reason="All generated vyaptis failed validation",
                framework_score=score,
                new_vyaptis=[],
                new_predicates=[],
                validation_warnings=warnings,
            )

        # Step 4: Merge KB
        merged_kb = self._merge_kb(new_vyaptis)

        # Build metadata
        metadata = [
            AugmentationMetadata(
                origin=AugmentationOrigin.LLM_PARAMETRIC,
                generated_at=datetime.utcnow(),
                generating_query=query,
                framework_vyaptis_used=domain_result.applicable_vyaptis,
                framework_applicability_score=score,
                generation_model=str(dspy.settings.lm),
            )
            for _ in new_vyaptis
        ]

        new_predicates = set()
        for v in new_vyaptis:
            new_predicates.update(v.antecedents)
            new_predicates.add(v.consequent)

        return AugmentationResult(
            augmented=True,
            reason=f"Generated {len(new_vyaptis)} vyaptis (framework score: {score:.2f})",
            framework_score=score,
            new_vyaptis=new_vyaptis,
            new_predicates=list(new_predicates),
            merged_kb=merged_kb,
            metadata=metadata,
            validation_warnings=warnings,
        )

    # --- Helper methods ---

    def _build_framework_summary(self) -> str:
        """Compact summary of all vyaptis + chapter fingerprints for domain scoring."""
        lines = []
        for vid, v in self.ks.vyaptis.items():
            lines.append(
                f"{vid}: {v.name} — {v.statement} "
                f"[{', '.join(v.antecedents)}] → {v.consequent}"
            )
        lines.append("\nChapters:")
        for cid, ch in self.ks.chapter_fingerprints.items():
            lines.append(
                f"{cid}: {ch.title} — key: {', '.join(ch.key_terms[:6])}"
            )
        return "\n".join(lines)

    def _build_applicable_vyaptis_text(self, vyapti_ids: list[str]) -> str:
        """Full text of applicable vyaptis for the generator prompt."""
        lines = []
        for vid in vyapti_ids:
            v = self.ks.vyaptis.get(vid)
            if not v:
                continue
            lines.append(f"--- {vid}: {v.name} ---")
            lines.append(f"Statement: {v.statement}")
            lines.append(f"Antecedents: {v.antecedents}")
            lines.append(f"Consequent: {v.consequent}")
            lines.append(f"Causal status: {v.causal_status.value}")
            lines.append(f"Scope conditions: {v.scope_conditions}")
            lines.append(f"Scope exclusions: {v.scope_exclusions}")
            lines.append(f"Epistemic status: {v.epistemic_status.value}")
            lines.append("")
        return "\n".join(lines)

    def _build_chapter_context(self, chapter_ids: list[str]) -> str:
        """Key terms + anchoring concepts from applicable chapters."""
        lines = []
        for cid in chapter_ids:
            ch = self.ks.chapter_fingerprints.get(cid)
            if not ch:
                continue
            lines.append(f"--- {cid}: {ch.title} ---")
            lines.append(f"Key terms: {', '.join(ch.key_terms[:10])}")
            lines.append(f"Anchoring concepts: {', '.join(ch.anchoring_concepts[:5])}")
            lines.append(f"Vyaptis introduced: {', '.join(ch.vyaptis_introduced)}")
            lines.append("")
        return "\n".join(lines)

    def _get_all_predicates(self) -> str:
        """All predicate names in the KB for reuse."""
        preds = set()
        for v in self.ks.vyaptis.values():
            preds.update(v.antecedents)
            preds.add(v.consequent)
        return ", ".join(sorted(preds))

    def _parse_generated_vyaptis(
        self,
        gen_result,
        applicable_vyaptis: list[str],
    ) -> list[Vyapti]:
        """Convert parallel lists from GenerateAugmentationPredicates into Vyapti objects."""
        from anvikshiki_v4.predicate_extraction import _enforce_snake_case

        vyaptis = []
        n = min(
            len(gen_result.vyapti_names),
            len(gen_result.vyapti_statements),
            len(gen_result.consequents),
            self.MAX_NEW_VYAPTIS,
        )
        existing_ids = set(self.ks.vyaptis.keys())

        for i in range(n):
            # Generate unique ID: VAUG_001, VAUG_002, ...
            aug_id = f"VAUG_{i+1:03d}"
            while aug_id in existing_ids:
                aug_id = f"VAUG_{i+100:03d}"

            name = _enforce_snake_case(gen_result.vyapti_names[i])
            if not name or name == "unknown_predicate":
                continue

            # Parse antecedents from comma-separated string
            raw_ants = gen_result.antecedents_list[i] if i < len(gen_result.antecedents_list) else ""
            antecedents = [
                _enforce_snake_case(a.strip())
                for a in raw_ants.split(",")
                if a.strip()
            ]
            antecedents = [a for a in antecedents if a and a != "unknown_predicate"]

            consequent = _enforce_snake_case(gen_result.consequents[i])
            if not consequent or consequent == "unknown_predicate":
                continue

            # Parse causal status
            raw_status = gen_result.causal_statuses[i] if i < len(gen_result.causal_statuses) else "empirical"
            try:
                causal_status = CausalStatus(raw_status.strip().lower())
            except ValueError:
                causal_status = CausalStatus.EMPIRICAL

            # Parse scope conditions
            raw_scope = gen_result.scope_conditions_list[i] if i < len(gen_result.scope_conditions_list) else ""
            scope_conditions = [s.strip() for s in raw_scope.split(",") if s.strip()]

            # Confidence — cap at 0.75 for generated content
            conf_exist = gen_result.confidence_existences[i] if i < len(gen_result.confidence_existences) else 0.5
            conf_exist = min(float(conf_exist), 0.75)

            vyaptis.append(Vyapti(
                id=aug_id,
                name=name,
                statement=gen_result.vyapti_statements[i] if i < len(gen_result.vyapti_statements) else name,
                causal_status=causal_status,
                scope_conditions=scope_conditions,
                scope_exclusions=[],
                confidence=Confidence(
                    existence=conf_exist,
                    formulation=min(conf_exist, 0.6),  # formulation <= existence for generated
                    evidence="theoretical",             # LLM parametric = theoretical
                ),
                epistemic_status=EpistemicStatus.WORKING_HYPOTHESIS,
                decay_risk=DecayRisk.MODERATE,
                sources=[],       # v1: no sources (LLM parametric)
                antecedents=antecedents,
                consequent=consequent,
            ))

        return vyaptis

    def _validate(self, vyaptis: list[Vyapti]) -> tuple[list[Vyapti], list[str]]:
        """Reuse Stage E validation logic: cycle detection + Datalog compilation."""
        from anvikshiki_v4.predicate_extraction import _detect_cycles
        from anvikshiki_v4.datalog_engine import DatalogEngine

        warnings = []

        # Build adjacency from existing + new vyaptis
        all_vyaptis = dict(self.ks.vyaptis)
        for v in vyaptis:
            all_vyaptis[v.id] = v

        adj: dict[str, set[str]] = {}
        for v in all_vyaptis.values():
            if v.consequent not in adj:
                adj[v.consequent] = set()
            for a in v.antecedents:
                adj[v.consequent].add(a)

        cycles = _detect_cycles(adj)
        if cycles:
            # Remove vyaptis involved in cycles
            cycle_preds = set()
            for cycle in cycles:
                cycle_preds.update(cycle)
            kept = []
            for v in vyaptis:
                if v.consequent in cycle_preds or any(a in cycle_preds for a in v.antecedents):
                    warnings.append(f"Removed {v.id} ({v.name}): cycle detected involving {v.consequent}")
                else:
                    kept.append(v)
            vyaptis = kept

        # Test Datalog compilation
        try:
            engine = DatalogEngine(boolean_mode=True)
            for v in all_vyaptis.values():
                engine.add_rule(
                    head=v.consequent,
                    body=v.antecedents,
                    tag=v.id,
                )
            engine.compile()
        except Exception as e:
            warnings.append(f"Datalog compilation warning: {e}")
            # Don't reject — just warn. The existing engine handles gracefully.

        return vyaptis, warnings

    def _merge_kb(self, new_vyaptis: list[Vyapti]) -> KnowledgeStore:
        """Create a new KnowledgeStore with augmented vyaptis merged in."""
        merged_vyaptis = dict(self.ks.vyaptis)
        for v in new_vyaptis:
            merged_vyaptis[v.id] = v

        # Rebuild dependency graph
        merged_deps = dict(self.ks.dependency_graph)
        for v in new_vyaptis:
            # Find which existing vyaptis this chains to
            for existing_id, existing_v in self.ks.vyaptis.items():
                if v.consequent in existing_v.antecedents:
                    if v.id not in merged_deps:
                        merged_deps[v.id] = []
                    merged_deps[v.id].append(existing_id)

        return KnowledgeStore(
            domain_type=self.ks.domain_type,
            pramanas=self.ks.pramanas,
            vyaptis=merged_vyaptis,
            hetvabhasas=self.ks.hetvabhasas,
            threshold_concepts=self.ks.threshold_concepts,
            dependency_graph=merged_deps,
            chapter_fingerprints=self.ks.chapter_fingerprints,
            reference_bank=self.ks.reference_bank,
        )
```

#### Modifications to Existing Files

**`query_refinement.py`** — Add `in_domain` flag to `RefinementResult`:

```python
# Add to RefinementResult:
class RefinementResult(BaseModel):
    # ... existing fields ...
    in_domain_hint: bool = True  # default True for backward compat
    # Set to False only when ClarifyIntent clearly identifies
    # the query as entirely outside the guide's domain
```

No change to `ClarifyIntent` signature — the `interpreted_intent` and `unmapped_concepts` fields already give enough signal. The `AugmentationPipeline` does its own domain check via `ScoreFrameworkApplicability`.

**`engine_v4.py`** — Add orchestration method:

```python
# Add to AnvikshikiEngineV4:
def forward_with_augmentation(
    self,
    query: str,
    retrieved_chunks: list[str],
    refinement_result: RefinementResult,
    augmentation_pipeline: Optional[AugmentationPipeline] = None,
) -> dspy.Prediction:
    """Orchestrates augmentation + engine. Falls back to base KB if augmentation fails."""
    if (
        augmentation_pipeline
        and refinement_result.coverage.coverage_ratio < self.ks_proceed_threshold
        and refinement_result.in_domain_hint
    ):
        aug_result = augmentation_pipeline.forward(query, refinement_result)
        if aug_result.augmented and aug_result.merged_kb:
            # Temporarily swap KB
            original_ks = self.knowledge_store
            self.knowledge_store = aug_result.merged_kb
            try:
                prediction = self.forward(query, retrieved_chunks)
                # Attach augmentation metadata to prediction
                prediction.augmentation = aug_result
                return prediction
            finally:
                self.knowledge_store = original_ks

    # Normal path — no augmentation
    return self.forward(query, retrieved_chunks)
```

#### v1 Example Trace

```
Query: "How should I think about supply chain resilience?"

1. QueryRefinement:
   - ClarifyIntent maps: supply_chain → no match, resilience → no match
   - Coverage: 0.08 (DECLINE)
   - interpreted_intent: "frameworks for building supply chain resilience"

2. AugmentationPipeline.domain_check():
   - ScoreFrameworkApplicability:
     reasoning: "V02 (Constraint Cascade) applies — supply chain resilience
       is about identifying binding constraints in a supply network.
       V06 (Optionality-Commitment) applies — resilience = maintaining
       optionality vs over-committing to single suppliers."
     applicability_score: 0.78
     applicable_vyaptis: ["V02", "V06", "V08"]
     applicable_chapters: ["ch03", "ch07", "ch10"]

3. AugmentationPipeline.generate():
   - GenerateAugmentationPredicates produces:
     VAUG_001: single_source_dependency → supply_chain_fragility
       (via V02 constraint pattern, scope: supply_chain_context)
     VAUG_002: supplier_diversification → supply_chain_resilience
       (via V06 optionality pattern, scope: supply_chain_context)
     VAUG_003: supply_chain_resilience, resource_allocation_effective → long_term_value
       (chains to V08 consequent, scope: supply_chain_context)
     VAUG_004: supply_chain_fragility → not_long_term_value
       (rebuttal via V11 pattern, scope: supply_chain_context)
   - All epistemic_status=HYPOTHESIS, confidence.existence <= 0.75

4. Validate: no cycles, Datalog compiles ✓

5. Merge KB: 11 original + 4 augmented = 15 vyaptis

6. engine_v4.forward() runs argumentation over merged KB:
   - VAUG_001 and VAUG_004 create an attack path (fragility → not_long_term_value)
   - VAUG_002 and VAUG_003 create a defense path (diversification → resilience → long_term_value)
   - Grounded extension includes both paths with uncertainty
   - SynthesizeResponse generates answer with provenance
```

#### v1 Test Specification

```python
# test_kb_augmentation.py

class TestScoreFrameworkApplicability:
    """Unit tests for domain check — does NOT require LLM."""

    def test_in_domain_high_score(self, sample_ks):
        """Supply chain query with applicable vyaptis should score >= 0.4."""
        # Mock the DSPy call, verify prompt construction + threshold logic

    def test_out_of_domain_low_score(self, sample_ks):
        """Astrophysics query should score < 0.4 and return augmented=False."""

    def test_empty_applicable_vyaptis_returns_false(self, sample_ks):
        """If scorer returns no applicable vyaptis, augment=False."""


class TestParseGeneratedVyaptis:
    """Unit tests for _parse_generated_vyaptis — deterministic."""

    def test_parallel_list_parsing(self, sample_ks):
        """Correct parsing of parallel name/statement/antecedent/consequent lists."""

    def test_confidence_capped_at_075(self, sample_ks):
        """Generated vyaptis never exceed confidence 0.75."""

    def test_invalid_names_skipped(self, sample_ks):
        """Non-snake-case names get normalized; empty names get dropped."""

    def test_max_vyaptis_cap(self, sample_ks):
        """More than MAX_NEW_VYAPTIS generated → only first N kept."""

    def test_epistemic_status_always_hypothesis(self, sample_ks):
        """All generated vyaptis have EpistemicStatus.WORKING_HYPOTHESIS."""


class TestValidation:
    """Unit tests for _validate — deterministic, reuses Stage E logic."""

    def test_no_cycles_all_pass(self, sample_ks):
        """Clean vyaptis pass validation with no warnings."""

    def test_cycle_detected_removes_offender(self, sample_ks):
        """Vyapti creating a cycle gets removed, others kept."""

    def test_datalog_compilation_test(self, sample_ks):
        """Merged KB compiles through DatalogEngine without error."""


class TestMergeKB:
    """Unit tests for _merge_kb — deterministic."""

    def test_merged_kb_has_all_vyaptis(self, sample_ks):
        """Original + augmented vyaptis all present."""

    def test_dependency_graph_updated(self, sample_ks):
        """New vyaptis chaining into existing ones appear in dependency_graph."""

    def test_original_kb_unchanged(self, sample_ks):
        """Merging doesn't mutate the original KnowledgeStore."""


class TestAugmentationPipelineIntegration:
    """Integration tests — require LLM (mark with @pytest.mark.llm)."""

    @pytest.mark.llm
    def test_supply_chain_generates_vyaptis(self, business_expert_ks):
        """Full pipeline for supply chain query produces valid vyaptis."""

    @pytest.mark.llm
    def test_astrophysics_declines(self, business_expert_ks):
        """Entirely out-of-domain query returns augmented=False."""

    @pytest.mark.llm
    def test_merged_kb_runs_through_engine(self, business_expert_ks):
        """End-to-end: augmented KB produces an engine response with provenance."""
```

---

## 4. v2: Web Search + Evidence Sourcing

### What v2 Adds

After v1 generates predicates from LLM parametric knowledge, v2 adds a **second pass** that searches the web for evidence supporting or refuting each generated predicate. This grounds generated knowledge in citable sources.

### New File: `evidence_search.py` (~200 lines)

#### Dependencies

```
# requirements.txt additions
tavily-python>=0.5.0       # Primary: structured search with chunked content
duckduckgo-search>=6.0.0   # Fallback: free, no API key
```

#### DSPy Signatures

```python
class FormulateEvidenceQuery(dspy.Signature):
    """Convert a generated vyapti into a web search query that would
    find evidence supporting or refuting it."""

    vyapti_statement: str = dspy.InputField(desc="The vyapti's natural language statement")
    vyapti_antecedents: str = dspy.InputField(desc="Comma-separated antecedent predicate names")
    vyapti_consequent: str = dspy.InputField(desc="Consequent predicate name")
    domain_context: str = dspy.InputField(desc="The original user query providing domain context")

    framework_query: str = dspy.OutputField(
        desc="Search query using domain terminology (e.g., 'single source dependency supply chain risk')"
    )
    broad_query: str = dspy.OutputField(
        desc="Broader search query for general evidence (e.g., 'supply chain resilience strategies research')"
    )
```

```python
class EvaluateEvidence(dspy.Signature):
    """Given a generated vyapti and web evidence, determine how well
    the evidence supports the vyapti. Adjust confidence accordingly.

    RULES:
    - SUPPORTS: evidence directly confirms the causal claim → boost confidence by 0.05–0.15
    - PARTIAL: evidence relates but doesn't directly confirm → boost by 0.0–0.05
    - NEUTRAL: evidence is not relevant → no change
    - REFUTES: evidence contradicts the claim → reduce confidence by 0.1–0.3
    - If evidence reveals scope conditions, add them"""

    vyapti_statement: str = dspy.InputField()
    evidence_snippets: list[str] = dspy.InputField(
        desc="Relevant text snippets from web sources"
    )
    evidence_urls: list[str] = dspy.InputField()

    verdict: str = dspy.OutputField(desc="SUPPORTS|PARTIAL|NEUTRAL|REFUTES")
    confidence_adjustment: float = dspy.OutputField(desc="-0.3 to +0.15")
    supporting_quotes: list[str] = dspy.OutputField(desc="Exact quotes from evidence")
    new_scope_conditions: list[str] = dspy.OutputField(
        desc="Scope conditions revealed by evidence (empty if none)"
    )
    reasoning: str = dspy.OutputField()
```

#### `EvidenceGatherer` Class

```python
class EvidenceGatherer:
    """Searches web for evidence supporting/refuting generated vyaptis.
    Uses Tavily (primary) with DuckDuckGo fallback."""

    def __init__(self, tavily_api_key: Optional[str] = None):
        self.tavily = None
        if tavily_api_key or os.environ.get("TAVILY_API_KEY"):
            from tavily import TavilyClient
            self.tavily = TavilyClient(
                api_key=tavily_api_key or os.environ["TAVILY_API_KEY"]
            )
        self.query_formulator = dspy.ChainOfThought(FormulateEvidenceQuery)
        self.evidence_evaluator = dspy.ChainOfThought(EvaluateEvidence)

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """Returns list of {title, url, content, score}."""
        if self.tavily:
            response = self.tavily.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_raw_content=False,
                topic="general",
            )
            return response.get("results", [])
        else:
            # DuckDuckGo fallback
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            return [
                {"title": r["title"], "url": r["href"], "content": r["body"], "score": 0.5}
                for r in results
            ]

    def gather_evidence_for_vyapti(
        self,
        vyapti: Vyapti,
        original_query: str,
    ) -> EvidenceResult:
        """Full pipeline: formulate queries → search → evaluate.
        Returns EvidenceResult with adjusted confidence + sources."""

        # 1. Formulate search queries (1 LLM call)
        queries = self.query_formulator(
            vyapti_statement=vyapti.statement,
            vyapti_antecedents=", ".join(vyapti.antecedents),
            vyapti_consequent=vyapti.consequent,
            domain_context=original_query,
        )

        # 2. Search (0 LLM calls — API calls)
        framework_results = self.search(queries.framework_query, max_results=3)
        broad_results = self.search(queries.broad_query, max_results=3)
        all_results = framework_results + broad_results

        if not all_results:
            return EvidenceResult(
                vyapti_id=vyapti.id,
                verdict="NEUTRAL",
                confidence_adjustment=0.0,
                sources=[],
                evidence_snippets=[],
            )

        # 3. Evaluate evidence (1 LLM call)
        snippets = [r["content"] for r in all_results if r.get("content")]
        urls = [r["url"] for r in all_results if r.get("url")]

        evaluation = self.evidence_evaluator(
            vyapti_statement=vyapti.statement,
            evidence_snippets=snippets[:6],  # cap context length
            evidence_urls=urls[:6],
        )

        return EvidenceResult(
            vyapti_id=vyapti.id,
            verdict=evaluation.verdict,
            confidence_adjustment=float(evaluation.confidence_adjustment),
            sources=urls,
            evidence_snippets=evaluation.supporting_quotes,
            new_scope_conditions=evaluation.new_scope_conditions,
            reasoning=evaluation.reasoning,
        )
```

#### `EvidenceResult` Model

```python
class EvidenceResult(BaseModel):
    vyapti_id: str
    verdict: str                          # SUPPORTS|PARTIAL|NEUTRAL|REFUTES
    confidence_adjustment: float          # -0.3 to +0.15
    sources: list[str]                    # URLs
    evidence_snippets: list[str]          # supporting quotes
    new_scope_conditions: list[str] = []  # scope conditions revealed
    reasoning: str = ""
```

#### Modifications to `kb_augmentation.py`

```python
class AugmentationPipeline(dspy.Module):
    """v2: Adds evidence sourcing after generation."""

    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        evidence_gatherer: Optional[EvidenceGatherer] = None,  # NEW in v2
    ):
        # ... existing v1 init ...
        self.evidence_gatherer = evidence_gatherer

    def forward(self, query, refinement_result) -> AugmentationResult:
        # ... v1 steps 1-3 (domain_check, generate, validate) ...

        # NEW Step 3.5: Evidence sourcing (v2)
        if self.evidence_gatherer and new_vyaptis:
            new_vyaptis = self._gather_evidence(new_vyaptis, query)

        # ... v1 step 4 (merge_kb) ...

    def _gather_evidence(
        self,
        vyaptis: list[Vyapti],
        query: str,
    ) -> list[Vyapti]:
        """Gather web evidence for each vyapti and adjust confidence."""
        updated = []
        for v in vyaptis:
            evidence = self.evidence_gatherer.gather_evidence_for_vyapti(v, query)

            # Adjust confidence based on evidence
            new_existence = max(0.1, min(0.9,
                v.confidence.existence + evidence.confidence_adjustment
            ))

            # Update evidence type based on verdict
            new_evidence_type = v.confidence.evidence
            if evidence.verdict == "SUPPORTS" and evidence.sources:
                new_evidence_type = "observational"  # upgraded from "theoretical"

            # Refuted vyaptis get dropped (confidence would be very low)
            if evidence.verdict == "REFUTES" and new_existence < 0.2:
                continue

            updated_v = v.model_copy(update={
                "confidence": Confidence(
                    existence=new_existence,
                    formulation=min(new_existence, v.confidence.formulation + evidence.confidence_adjustment * 0.5),
                    evidence=new_evidence_type,
                ),
                "sources": evidence.sources[:3],  # top 3 URLs
                "scope_conditions": list(set(v.scope_conditions + evidence.new_scope_conditions)),
            })
            updated.append(updated_v)

        return updated
```

#### v2 Cost Analysis

| Step | LLM Calls | API Calls |
|------|-----------|-----------|
| Domain check | 1 | 0 |
| Generate predicates | 1 | 0 |
| Formulate queries (per vyapti) | 1 × N | 0 |
| Web search (per vyapti) | 0 | 2 × N |
| Evaluate evidence (per vyapti) | 1 × N | 0 |

For N=4 generated vyaptis: **2 + 8 = 10 LLM calls, 8 API calls**.

Optimization: batch `FormulateEvidenceQuery` for all vyaptis in one call (reduce to 3 LLM calls + N evaluation calls = 7 total).

#### v2 Tests

```python
class TestEvidenceGatherer:
    def test_tavily_search_returns_structured(self, mock_tavily):
        """Tavily client returns {title, url, content, score} dicts."""

    def test_ddg_fallback_when_no_tavily(self):
        """Without TAVILY_API_KEY, falls back to DuckDuckGo."""

    def test_empty_results_returns_neutral(self):
        """No search results → verdict=NEUTRAL, adjustment=0.0."""


class TestEvaluateEvidence:
    def test_supporting_evidence_boosts_confidence(self, mock_lm):
        """SUPPORTS verdict increases confidence by 0.05–0.15."""

    def test_refuting_evidence_drops_vyapti(self, mock_lm):
        """REFUTES with low resulting confidence removes the vyapti."""

    def test_new_scope_conditions_added(self, mock_lm):
        """Evidence revealing scope conditions adds them to vyapti."""


class TestV2Integration:
    @pytest.mark.llm
    @pytest.mark.web
    def test_end_to_end_with_evidence(self, business_expert_ks):
        """Full v2 pipeline: generate → search → evaluate → merge."""
```

---

## 5. v3: Shadow KB Persistence + HITL Review

### What v3 Adds

Generated predicates are no longer ephemeral. They persist in a **shadow KB** (SQLite database) alongside the curated YAML KB. A HITL review queue allows humans to approve, reject, or modify augmented predicates. Approved predicates can be promoted to the curated KB.

### New File: `shadow_kb.py` (~250 lines)

#### SQLite Schema

```sql
-- Created by ShadowKB.__init__()
CREATE TABLE IF NOT EXISTS augmented_vyaptis (
    id                  TEXT PRIMARY KEY,      -- VAUG_001, etc.
    name                TEXT NOT NULL,
    statement           TEXT NOT NULL,
    causal_status       TEXT NOT NULL,
    antecedents         TEXT NOT NULL,          -- JSON array
    consequent          TEXT NOT NULL,
    scope_conditions    TEXT NOT NULL,          -- JSON array
    scope_exclusions    TEXT NOT NULL,          -- JSON array
    confidence_existence    REAL NOT NULL,
    confidence_formulation  REAL NOT NULL,
    confidence_evidence     TEXT NOT NULL,
    epistemic_status    TEXT NOT NULL,
    decay_risk          TEXT NOT NULL,
    sources             TEXT NOT NULL,          -- JSON array

    -- Augmentation metadata
    origin              TEXT NOT NULL,          -- AugmentationOrigin value
    generating_query    TEXT NOT NULL,
    framework_vyaptis_used TEXT NOT NULL,       -- JSON array
    framework_applicability_score REAL NOT NULL,
    evidence_urls       TEXT NOT NULL,          -- JSON array
    evidence_snippets   TEXT NOT NULL,          -- JSON array
    generation_model    TEXT NOT NULL,
    generation_run_id   TEXT NOT NULL,
    generated_at        TEXT NOT NULL,

    -- Review lifecycle
    review_status       TEXT NOT NULL DEFAULT 'pending',  -- pending|approved|rejected|needs_source
    reviewer            TEXT,
    reviewer_notes      TEXT DEFAULT '',
    reviewed_at         TEXT,
    promoted_to_curated TEXT,                  -- vyapti ID in curated KB after promotion

    -- Usage stats
    times_used          INTEGER DEFAULT 0,
    times_accepted_in_extension INTEGER DEFAULT 0,
    times_defeated      INTEGER DEFAULT 0,
    last_used_at        TEXT
);

CREATE INDEX IF NOT EXISTS idx_augmented_status ON augmented_vyaptis(review_status);
CREATE INDEX IF NOT EXISTS idx_augmented_query ON augmented_vyaptis(generating_query);
CREATE INDEX IF NOT EXISTS idx_augmented_consequent ON augmented_vyaptis(consequent);
```

#### `ShadowKB` Class

```python
class ShadowKB:
    """Persistent storage for augmented vyaptis with review lifecycle."""

    def __init__(self, db_path: str = "data/shadow_kb.sqlite"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def store(self, vyapti: Vyapti, metadata: AugmentationMetadata) -> str:
        """Store an augmented vyapti. Returns the vyapti ID."""
        self.conn.execute("""
            INSERT OR REPLACE INTO augmented_vyaptis
            (id, name, statement, causal_status, antecedents, consequent,
             scope_conditions, scope_exclusions,
             confidence_existence, confidence_formulation, confidence_evidence,
             epistemic_status, decay_risk, sources,
             origin, generating_query, framework_vyaptis_used,
             framework_applicability_score, evidence_urls, evidence_snippets,
             generation_model, generation_run_id, generated_at,
             review_status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            vyapti.id, vyapti.name, vyapti.statement,
            vyapti.causal_status.value,
            json.dumps(vyapti.antecedents), vyapti.consequent,
            json.dumps(vyapti.scope_conditions), json.dumps(vyapti.scope_exclusions),
            vyapti.confidence.existence, vyapti.confidence.formulation,
            vyapti.confidence.evidence,
            vyapti.epistemic_status.value, vyapti.decay_risk.value,
            json.dumps(vyapti.sources),
            metadata.origin.value, metadata.generating_query,
            json.dumps(metadata.framework_vyaptis_used),
            metadata.framework_applicability_score,
            json.dumps(metadata.evidence_urls), json.dumps(metadata.evidence_snippets),
            metadata.generation_model, metadata.generation_run_id,
            metadata.generated_at.isoformat(),
            "pending",
        ))
        self.conn.commit()
        return vyapti.id

    def find_relevant(
        self,
        predicates: list[str],
        min_confidence: float = 0.3,
        include_rejected: bool = False,
    ) -> list[Vyapti]:
        """Find shadow vyaptis whose antecedents/consequents overlap with given predicates.
        Used to check if we've already augmented for similar queries."""
        placeholders = ",".join("?" * len(predicates))
        status_filter = "" if include_rejected else "AND review_status != 'rejected'"

        rows = self.conn.execute(f"""
            SELECT * FROM augmented_vyaptis
            WHERE confidence_existence >= ?
            {status_filter}
            AND (
                consequent IN ({placeholders})
                OR EXISTS (
                    SELECT 1 FROM json_each(antecedents)
                    WHERE json_each.value IN ({placeholders})
                )
            )
        """, [min_confidence] + predicates + predicates).fetchall()

        return [self._row_to_vyapti(row) for row in rows]

    def get_pending_review(self, limit: int = 20) -> list[dict]:
        """Get vyaptis awaiting human review, ordered by priority."""
        rows = self.conn.execute("""
            SELECT *, times_used, times_defeated FROM augmented_vyaptis
            WHERE review_status = 'pending'
            ORDER BY times_used DESC, confidence_existence ASC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(row) for row in rows]

    def record_review(
        self,
        vyapti_id: str,
        decision: str,
        reviewer: str,
        notes: str = "",
    ):
        """Record a HITL review decision."""
        self.conn.execute("""
            UPDATE augmented_vyaptis
            SET review_status = ?, reviewer = ?, reviewer_notes = ?,
                reviewed_at = ?
            WHERE id = ?
        """, (decision, reviewer, notes, datetime.utcnow().isoformat(), vyapti_id))
        self.conn.commit()

    def record_usage(self, vyapti_id: str, accepted_in_extension: bool):
        """Track how a vyapti performed in argumentation."""
        self.conn.execute("""
            UPDATE augmented_vyaptis
            SET times_used = times_used + 1,
                times_accepted_in_extension = times_accepted_in_extension + ?,
                last_used_at = ?
            WHERE id = ?
        """, (1 if accepted_in_extension else 0, datetime.utcnow().isoformat(), vyapti_id))
        self.conn.commit()

    def record_defeat(self, vyapti_id: str):
        """Track when a vyapti is defeated in argumentation."""
        self.conn.execute("""
            UPDATE augmented_vyaptis
            SET times_defeated = times_defeated + 1
            WHERE id = ?
        """, (vyapti_id,))
        self.conn.commit()

    def promote_to_curated(
        self,
        vyapti_id: str,
        curated_id: str,
    ):
        """Mark a shadow vyapti as promoted to the curated KB."""
        self.conn.execute("""
            UPDATE augmented_vyaptis
            SET promoted_to_curated = ?, review_status = 'promoted'
            WHERE id = ?
        """, (curated_id, vyapti_id))
        self.conn.commit()

    def get_stats(self) -> dict:
        """Shadow KB statistics for monitoring."""
        row = self.conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN review_status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN review_status = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN review_status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                SUM(CASE WHEN review_status = 'promoted' THEN 1 ELSE 0 END) as promoted,
                AVG(confidence_existence) as avg_confidence,
                AVG(CAST(times_defeated AS REAL) / MAX(times_used, 1)) as avg_defeat_rate
            FROM augmented_vyaptis
        """).fetchone()
        return dict(row)

    def _row_to_vyapti(self, row) -> Vyapti:
        """Convert a SQLite row back to a Vyapti object."""
        return Vyapti(
            id=row["id"],
            name=row["name"],
            statement=row["statement"],
            causal_status=CausalStatus(row["causal_status"]),
            antecedents=json.loads(row["antecedents"]),
            consequent=row["consequent"],
            scope_conditions=json.loads(row["scope_conditions"]),
            scope_exclusions=json.loads(row["scope_exclusions"]),
            confidence=Confidence(
                existence=row["confidence_existence"],
                formulation=row["confidence_formulation"],
                evidence=row["confidence_evidence"],
            ),
            epistemic_status=EpistemicStatus(row["epistemic_status"]),
            decay_risk=DecayRisk(row["decay_risk"]),
            sources=json.loads(row["sources"]),
        )

    def _create_tables(self):
        """Initialize SQLite tables."""
        self.conn.executescript(SCHEMA_SQL)  # the SQL from above
```

#### Modifications to `kb_augmentation.py` for v3

```python
class AugmentationPipeline(dspy.Module):
    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        evidence_gatherer: Optional[EvidenceGatherer] = None,
        shadow_kb: Optional[ShadowKB] = None,  # NEW in v3
    ):
        # ... existing init ...
        self.shadow_kb = shadow_kb

    def forward(self, query, refinement_result) -> AugmentationResult:
        # ... existing steps ...

        # NEW in v3: Check shadow KB first
        if self.shadow_kb:
            existing = self._check_shadow_kb(refinement_result)
            if existing:
                # Reuse previously generated vyaptis instead of re-generating
                merged_kb = self._merge_kb(existing)
                return AugmentationResult(
                    augmented=True,
                    reason=f"Reused {len(existing)} shadow KB vyaptis",
                    framework_score=1.0,  # already validated
                    new_vyaptis=existing,
                    new_predicates=[...],
                    merged_kb=merged_kb,
                )

        # ... v1/v2 generation steps ...

        # NEW in v3: Persist to shadow KB
        if self.shadow_kb and new_vyaptis:
            for v, m in zip(new_vyaptis, metadata):
                self.shadow_kb.store(v, m)

        # ... merge_kb, return ...

    def _check_shadow_kb(self, refinement_result: RefinementResult) -> list[Vyapti]:
        """Check if shadow KB already has relevant vyaptis for this query."""
        # Use the unmatched concepts from coverage analysis
        search_preds = list(refinement_result.coverage.closest_predicates.values())
        search_preds += refinement_result.coverage.matched_predicates

        relevant = self.shadow_kb.find_relevant(
            predicates=search_preds,
            min_confidence=0.3,
        )
        # Only reuse approved or pending (not rejected)
        return [v for v in relevant]
```

#### New File: `review_queue.py` (~100 lines)

```python
class ReviewQueue:
    """CLI/API interface for HITL review of shadow KB vyaptis."""

    def __init__(self, shadow_kb: ShadowKB):
        self.shadow_kb = shadow_kb

    def get_next_batch(self, reviewer: str, batch_size: int = 5) -> list[dict]:
        """Get next batch of vyaptis for review.
        Priority: high-usage + low-confidence first."""
        return self.shadow_kb.get_pending_review(limit=batch_size)

    def submit_review(
        self,
        vyapti_id: str,
        decision: str,    # "approve"|"reject"|"needs_source"
        reviewer: str,
        notes: str = "",
    ) -> dict:
        """Submit a review decision."""
        self.shadow_kb.record_review(vyapti_id, decision, reviewer, notes)
        return {"vyapti_id": vyapti_id, "decision": decision, "reviewer": reviewer}

    def promote(
        self,
        vyapti_id: str,
        curated_kb_path: str,
    ) -> str:
        """Promote an approved vyapti to the curated YAML KB.
        Returns the new curated vyapti ID (e.g., V12)."""
        row = self.shadow_kb.conn.execute(
            "SELECT * FROM augmented_vyaptis WHERE id = ? AND review_status = 'approved'",
            (vyapti_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"Vyapti {vyapti_id} not found or not approved")

        # Load curated KB, find next ID
        ks = load_knowledge_store(curated_kb_path)
        existing_ids = sorted(ks.vyaptis.keys())
        # Parse "V11" → 11, next = "V12"
        max_num = max(int(vid[1:]) for vid in existing_ids if vid.startswith("V"))
        new_id = f"V{max_num + 1:02d}"

        # Convert to curated vyapti and append to YAML
        vyapti = self.shadow_kb._row_to_vyapti(row)
        vyapti_dict = {
            "id": new_id,
            "name": vyapti.name,
            "statement": vyapti.statement,
            "causal_status": vyapti.causal_status.value,
            "antecedents": vyapti.antecedents,
            "consequent": vyapti.consequent,
            "scope_conditions": vyapti.scope_conditions,
            "scope_exclusions": vyapti.scope_exclusions,
            "confidence": {
                "existence": vyapti.confidence.existence,
                "formulation": vyapti.confidence.formulation,
                "evidence": vyapti.confidence.evidence,
            },
            "epistemic_status": "established",  # promoted = established
            "decay_risk": vyapti.decay_risk.value,
            "sources": vyapti.sources,
        }

        # Append to YAML
        with open(curated_kb_path, "r") as f:
            data = yaml.safe_load(f)
        data["vyaptis"][new_id] = vyapti_dict
        with open(curated_kb_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        self.shadow_kb.promote_to_curated(vyapti_id, new_id)
        return new_id

    def export_stats(self) -> dict:
        """Export review statistics."""
        stats = self.shadow_kb.get_stats()
        stats["promotion_rate"] = (
            stats["promoted"] / max(stats["approved"], 1) if stats["approved"] else 0
        )
        stats["rejection_rate"] = (
            stats["rejected"] / max(stats["total"], 1) if stats["total"] else 0
        )
        return stats
```

#### v3 Tests

```python
class TestShadowKB:
    def test_store_and_retrieve(self, tmp_path):
        """Store a vyapti and retrieve it by predicate overlap."""

    def test_rejected_excluded_by_default(self, tmp_path):
        """find_relevant excludes rejected vyaptis unless include_rejected=True."""

    def test_usage_tracking(self, tmp_path):
        """record_usage increments times_used and times_accepted_in_extension."""

    def test_defeat_tracking(self, tmp_path):
        """record_defeat increments times_defeated."""

    def test_stats(self, tmp_path):
        """get_stats returns correct counts and averages."""


class TestReviewQueue:
    def test_get_next_batch_priority(self, shadow_kb_with_data):
        """High-usage, low-confidence vyaptis come first."""

    def test_submit_review_updates_status(self, shadow_kb_with_data):
        """Review decision persists in SQLite."""

    def test_promote_appends_to_yaml(self, shadow_kb_with_data, tmp_yaml):
        """Promotion adds vyapti to YAML with next sequential ID."""

    def test_promote_rejects_unapproved(self, shadow_kb_with_data):
        """Cannot promote a vyapti that hasn't been approved."""


class TestShadowKBReuse:
    def test_reuse_existing_shadow_vyaptis(self, sample_ks, tmp_path):
        """Similar query reuses previously generated vyaptis from shadow KB."""

    def test_no_duplicate_generation(self, sample_ks, tmp_path):
        """Same query twice doesn't create duplicate vyaptis."""
```

---

## 6. v4: Source Reliability Scoring + Vitaṇḍā Stress Test

### What v4 Adds

Two capabilities:

1. **Source reliability scoring** — Cross-source agreement tracking. Sources that consistently agree with other sources get higher reliability. Vyaptis backed by reliable sources get confidence boosts.
2. **Vitaṇḍā stress test** — Before accepting augmented predicates, run a dedicated adversarial argumentation pass that attacks every new predicate. Only predicates surviving the stress test enter the merged KB.

### New File: `source_reliability.py` (~150 lines)

```python
class SourceRecord(BaseModel):
    """Tracks reliability of an information source over time."""
    source_id: str                        # URL domain or source identifier
    domain: str                           # e.g., "hbr.org", "arxiv.org"
    reliability_score: float = 1.0        # Laplace-smoothed agreement rate
    agreements: int = 0
    disagreements: int = 0
    total_claims: int = 0
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)


class ReliabilityTracker:
    """RA-RAG-inspired source reliability scoring via cross-source agreement.
    Stores reliability data in the shadow KB SQLite database."""

    PRIOR_AGREEMENTS: int = 1   # Laplace smoothing pseudocounts
    PRIOR_TOTAL: int = 2

    def __init__(self, db_path: str = "data/shadow_kb.sqlite"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS source_reliability (
                source_id       TEXT PRIMARY KEY,
                domain          TEXT NOT NULL,
                reliability_score REAL NOT NULL DEFAULT 1.0,
                agreements      INTEGER NOT NULL DEFAULT 0,
                disagreements   INTEGER NOT NULL DEFAULT 0,
                total_claims    INTEGER NOT NULL DEFAULT 0,
                first_seen      TEXT NOT NULL,
                last_seen       TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def get_reliability(self, source_id: str) -> float:
        """Get reliability score for a source. Returns 0.5 for unknown sources."""
        row = self.conn.execute(
            "SELECT reliability_score FROM source_reliability WHERE source_id = ?",
            (source_id,)
        ).fetchone()
        return row["reliability_score"] if row else 0.5

    def update_from_cross_agreement(
        self,
        claim: str,
        source_verdicts: list[tuple[str, str]],  # [(source_id, verdict)]
    ):
        """Update reliability based on cross-source agreement for a claim.

        For each source: if its verdict matches the majority, it "agrees."
        Reliability = (agreements + PRIOR) / (total + 2*PRIOR) (Laplace smoothed)."""
        if len(source_verdicts) < 2:
            return

        # Majority vote
        from collections import Counter
        verdicts = [v for _, v in source_verdicts]
        majority = Counter(verdicts).most_common(1)[0][0]

        now = datetime.utcnow().isoformat()
        for source_id, verdict in source_verdicts:
            agreed = verdict == majority
            self.conn.execute("""
                INSERT INTO source_reliability
                    (source_id, domain, reliability_score, agreements, disagreements,
                     total_claims, first_seen, last_seen)
                VALUES (?, ?, 0.5, ?, ?, 1, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    agreements = agreements + ?,
                    disagreements = disagreements + ?,
                    total_claims = total_claims + 1,
                    last_seen = ?,
                    reliability_score = CAST(
                        (agreements + ? + ?) AS REAL
                    ) / (total_claims + 1 + ?)
            """, (
                source_id,
                self._extract_domain(source_id),
                1 if agreed else 0,
                0 if agreed else 1,
                now, now,
                1 if agreed else 0,
                0 if agreed else 1,
                now,
                self.PRIOR_AGREEMENTS,
                1 if agreed else 0,
                self.PRIOR_TOTAL,
            ))
        self.conn.commit()

    def weighted_confidence(
        self,
        base_confidence: float,
        source_urls: list[str],
    ) -> float:
        """Adjust a vyapti's confidence based on source reliability.
        Uses geometric mean of source reliabilities as a multiplier."""
        if not source_urls:
            return base_confidence

        reliabilities = [self.get_reliability(url) for url in source_urls]
        if not reliabilities:
            return base_confidence

        # Geometric mean
        import math
        geo_mean = math.exp(sum(math.log(max(r, 0.01)) for r in reliabilities) / len(reliabilities))

        # Scale: geo_mean=1.0 → no change, geo_mean=0.5 → reduce by 15%, geo_mean=0.2 → reduce by 40%
        adjustment = (geo_mean - 0.5) * 0.3  # maps [0,1] → [-0.15, +0.15]
        return max(0.1, min(0.95, base_confidence + adjustment))

    @staticmethod
    def _extract_domain(url: str) -> str:
        from urllib.parse import urlparse
        try:
            return urlparse(url).netloc
        except Exception:
            return url
```

#### Vitaṇḍā Stress Test

Add to `kb_augmentation.py`:

```python
class VitandaChallenge(dspy.Signature):
    """You are a Vitaṇḍā (devil's advocate). Your ONLY job is to attack
    the generated vyapti. Find the strongest possible objection.

    Attack vectors:
    1. The causal claim is reversed (B actually causes A, not A→B)
    2. There's a confounding variable not captured
    3. The scope conditions are too narrow or too broad
    4. The claim contradicts known principles in the domain
    5. The evidence is from an unreliable or biased source
    6. The claim is tautological (consequent is just a restatement of antecedent)"""

    vyapti_statement: str = dspy.InputField()
    vyapti_antecedents: str = dspy.InputField()
    vyapti_consequent: str = dspy.InputField()
    vyapti_sources: str = dspy.InputField()
    existing_kb_summary: str = dspy.InputField(desc="Existing vyaptis for contradiction check")

    attack_found: bool = dspy.OutputField(desc="True if a serious flaw was found")
    attack_type: str = dspy.OutputField(
        desc="reversal|confound|scope_error|contradiction|source_bias|tautology|none"
    )
    attack_reasoning: str = dspy.OutputField()
    severity: float = dspy.OutputField(desc="0.0–1.0. >= 0.7 means reject the vyapti")
    suggested_fix: str = dspy.OutputField(
        desc="How to fix the vyapti if possible (e.g., add scope condition)"
    )


class StressTest:
    """Vitaṇḍā stress test for augmented vyaptis.
    Runs adversarial challenges. Only passing vyaptis survive."""

    SEVERITY_THRESHOLD: float = 0.7

    def __init__(self, knowledge_store: KnowledgeStore):
        self.ks = knowledge_store
        self.challenger = dspy.ChainOfThought(VitandaChallenge)

    def test_vyaptis(self, vyaptis: list[Vyapti]) -> tuple[list[Vyapti], list[dict]]:
        """Run stress test on each vyapti. Returns (survivors, attack_reports)."""
        kb_summary = "\n".join(
            f"{vid}: {v.statement}" for vid, v in self.ks.vyaptis.items()
        )

        survivors = []
        reports = []

        for v in vyaptis:
            result = self.challenger(
                vyapti_statement=v.statement,
                vyapti_antecedents=", ".join(v.antecedents),
                vyapti_consequent=v.consequent,
                vyapti_sources=", ".join(v.sources) if v.sources else "none (LLM generated)",
                existing_kb_summary=kb_summary,
            )

            report = {
                "vyapti_id": v.id,
                "attack_found": result.attack_found,
                "attack_type": result.attack_type,
                "severity": float(result.severity),
                "reasoning": result.attack_reasoning,
                "suggested_fix": result.suggested_fix,
            }
            reports.append(report)

            if not result.attack_found or float(result.severity) < self.SEVERITY_THRESHOLD:
                # Apply suggested fixes if minor attack found
                if result.attack_found and result.suggested_fix:
                    if result.attack_type == "scope_error" and result.suggested_fix:
                        v = v.model_copy(update={
                            "scope_conditions": v.scope_conditions + [result.suggested_fix]
                        })
                survivors.append(v)

        return survivors, reports
```

#### Modifications to `kb_augmentation.py` for v4

```python
class AugmentationPipeline(dspy.Module):
    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        evidence_gatherer: Optional[EvidenceGatherer] = None,
        shadow_kb: Optional[ShadowKB] = None,
        reliability_tracker: Optional[ReliabilityTracker] = None,  # NEW v4
        enable_stress_test: bool = False,                          # NEW v4
    ):
        # ... existing init ...
        self.reliability_tracker = reliability_tracker
        self.stress_test = StressTest(knowledge_store) if enable_stress_test else None

    def forward(self, query, refinement_result) -> AugmentationResult:
        # ... v1-v3 steps ...

        # NEW v4: Adjust confidence based on source reliability
        if self.reliability_tracker and new_vyaptis:
            for i, v in enumerate(new_vyaptis):
                adjusted = self.reliability_tracker.weighted_confidence(
                    v.confidence.existence, v.sources
                )
                new_vyaptis[i] = v.model_copy(update={
                    "confidence": Confidence(
                        existence=adjusted,
                        formulation=min(adjusted, v.confidence.formulation),
                        evidence=v.confidence.evidence,
                    )
                })

        # NEW v4: Vitaṇḍā stress test
        if self.stress_test and new_vyaptis:
            new_vyaptis, attack_reports = self.stress_test.test_vyaptis(new_vyaptis)
            # Store attack reports in metadata for later review
            for report in attack_reports:
                if report["attack_found"]:
                    warnings.append(
                        f"Vitaṇḍā attack on {report['vyapti_id']}: "
                        f"{report['attack_type']} (severity {report['severity']:.2f})"
                    )

        # ... merge_kb, persist, return ...
```

#### v4 Cost Analysis

Additional per-query costs on top of v2:
- Vitaṇḍā challenge: +1 LLM call per generated vyapti (N calls)
- Reliability scoring: 0 LLM calls (deterministic lookup)

For N=4: **v2 total + 4 = ~14 LLM calls total**.

#### v4 Tests

```python
class TestReliabilityTracker:
    def test_laplace_smoothing(self, tmp_path):
        """New source starts at 0.5 (no data), converges with evidence."""

    def test_cross_agreement_updates(self, tmp_path):
        """Majority-agreeing sources increase score; dissenters decrease."""

    def test_weighted_confidence(self, tmp_path):
        """High-reliability sources boost confidence; low sources reduce it."""


class TestStressTest:
    @pytest.mark.llm
    def test_tautology_detected(self, sample_ks):
        """Tautological vyapti (A→A) gets flagged with high severity."""

    @pytest.mark.llm
    def test_scope_fix_applied(self, sample_ks):
        """Scope error attack results in scope condition being added."""

    @pytest.mark.llm
    def test_valid_vyapti_survives(self, sample_ks):
        """Well-formed vyapti with evidence passes stress test."""
```

---

## 7. v5: Formalized Framework Templates + Multi-Domain

### What v5 Adds

The framework knowledge that was implicit in LLM prompts (v1–v4) becomes **explicit, machine-readable YAML templates**. This enables:
1. Multi-domain support — different guides produce different framework templates
2. Formal framework instantiation — template variables get filled systematically, not via free-form LLM generation
3. Framework composition — combine frameworks from different domains

### New File: `framework_templates.py` (~200 lines)

#### Framework Template YAML Format

```yaml
# data/frameworks/constraint_cascade.yaml
framework_id: FW_CONSTRAINT
name: "Constraint Cascade"
source_vyaptis: ["V02"]
domain_type: CRAFT

# Structural pattern — the abstract causal structure
pattern:
  description: >
    In any system with flow, there exists a bottleneck node.
    The bottleneck determines total throughput.
    Relieving the bottleneck improves system efficiency.
  abstract_predicates:
    - name: "system_with_flow"
      role: "context"
      description: "A system where something flows from input to output"
    - name: "bottleneck_identified"
      role: "antecedent"
      description: "The primary constraint limiting throughput is identified"
    - name: "resource_reallocation"
      role: "action"
      description: "Resources are redirected to relieve the bottleneck"
    - name: "throughput_improvement"
      role: "consequent"
      description: "System throughput increases"

  # Template vyapti — gets instantiated for specific domains
  template_vyaptis:
    - name: "${domain}_bottleneck_identified"
      statement: "When the binding constraint in ${domain} is identified, ${reallocation_action} becomes effective"
      antecedents: ["${domain}_bottleneck_identified"]
      consequent: "${domain}_resource_effective"
      causal_status: "structural"

    - name: "${domain}_constraint_relief"
      statement: "Relieving the primary constraint in ${domain} improves ${outcome_metric}"
      antecedents: ["${domain}_resource_effective"]
      consequent: "${domain}_${outcome_improved}"
      causal_status: "empirical"

# Diagnostic questions — domain-specific instantiation prompts
diagnostic_questions:
  - "What flows through the system? (e.g., materials, information, decisions)"
  - "Where does flow get constrained? (e.g., single supplier, approval bottleneck)"
  - "What happens when you relieve that constraint?"
  - "Are there secondary constraints that become binding after the first is relieved?"

# Applicability test — when does this framework apply?
applicability:
  requires: ["system_with_flow", "identifiable_constraint"]
  excludes: ["no_flow_system", "fully_distributed"]
  typical_domains: ["supply_chain", "manufacturing", "software_delivery", "hiring"]
```

#### `FrameworkTemplate` Model

```python
class AbstractPredicate(BaseModel):
    name: str
    role: str               # "context"|"antecedent"|"action"|"consequent"
    description: str

class TemplateVyapti(BaseModel):
    name: str               # contains ${domain} etc. placeholders
    statement: str
    antecedents: list[str]
    consequent: str
    causal_status: str

class FrameworkTemplate(BaseModel):
    framework_id: str
    name: str
    source_vyaptis: list[str]
    domain_type: str
    pattern_description: str
    abstract_predicates: list[AbstractPredicate]
    template_vyaptis: list[TemplateVyapti]
    diagnostic_questions: list[str]
    applicability_requires: list[str]
    applicability_excludes: list[str]
    typical_domains: list[str]
```

#### `FrameworkInstantiator` (dspy.Module)

```python
class InstantiateFramework(dspy.Signature):
    """Given a framework template and a target domain, produce concrete
    predicate names by filling template variables.

    RULES:
    - Replace ${domain} with the specific domain (e.g., "supply_chain")
    - Replace ${reallocation_action} with a domain-specific action
    - Replace ${outcome_metric} with a domain-specific outcome
    - All generated names must be snake_case
    - Reuse existing KB predicates where they fit"""

    template_yaml: str = dspy.InputField(desc="The framework template content")
    target_domain: str = dspy.InputField(desc="Specific domain to instantiate for")
    query_context: str = dspy.InputField(desc="The user's query providing context")
    existing_predicates: str = dspy.InputField(desc="Current KB predicate vocabulary")

    instantiated_names: list[str] = dspy.OutputField(
        desc="Concrete predicate names replacing template variables"
    )
    variable_bindings: list[str] = dspy.OutputField(
        desc="'${var} = value' for each template variable"
    )
    reasoning: str = dspy.OutputField()


class FrameworkInstantiator(dspy.Module):
    """Instantiates framework templates for specific domains."""

    def __init__(self, templates_dir: str = "data/frameworks/"):
        super().__init__()
        self.templates = self._load_templates(templates_dir)
        self.instantiator = dspy.ChainOfThought(InstantiateFramework)

    def instantiate(
        self,
        framework_id: str,
        target_domain: str,
        query: str,
        existing_predicates: list[str],
    ) -> list[Vyapti]:
        """Instantiate a framework template for a specific domain.
        Returns concrete Vyapti objects."""
        template = self.templates.get(framework_id)
        if not template:
            return []

        result = self.instantiator(
            template_yaml=yaml.dump(template.model_dump()),
            target_domain=target_domain,
            query_context=query,
            existing_predicates=", ".join(existing_predicates),
        )

        # Parse variable bindings
        bindings = {}
        for b in result.variable_bindings:
            if "=" in b:
                var, val = b.split("=", 1)
                bindings[var.strip()] = val.strip()

        # Instantiate template vyaptis with bindings
        vyaptis = []
        for i, tv in enumerate(template.template_vyaptis):
            name = self._apply_bindings(tv.name, bindings)
            statement = self._apply_bindings(tv.statement, bindings)
            antecedents = [self._apply_bindings(a, bindings) for a in tv.antecedents]
            consequent = self._apply_bindings(tv.consequent, bindings)

            from anvikshiki_v4.predicate_extraction import _enforce_snake_case
            vyaptis.append(Vyapti(
                id=f"VFWK_{framework_id}_{i+1:03d}",
                name=_enforce_snake_case(name),
                statement=statement,
                causal_status=CausalStatus(tv.causal_status),
                antecedents=[_enforce_snake_case(a) for a in antecedents],
                consequent=_enforce_snake_case(consequent),
                scope_conditions=[f"{target_domain}_context"],
                scope_exclusions=[],
                confidence=Confidence(
                    existence=0.7,       # framework-derived = higher base confidence
                    formulation=0.6,
                    evidence="theoretical",
                ),
                epistemic_status=EpistemicStatus.WORKING_HYPOTHESIS,
                decay_risk=DecayRisk.LOW,
                sources=[],
            ))

        return vyaptis

    @staticmethod
    def _apply_bindings(template_str: str, bindings: dict) -> str:
        result = template_str
        for var, val in bindings.items():
            result = result.replace(var, val)
        return result

    def _load_templates(self, templates_dir: str) -> dict[str, FrameworkTemplate]:
        templates = {}
        import glob as glob_mod
        for path in glob_mod.glob(os.path.join(templates_dir, "*.yaml")):
            with open(path) as f:
                data = yaml.safe_load(f)
            template = FrameworkTemplate(
                framework_id=data["framework_id"],
                name=data["name"],
                source_vyaptis=data["source_vyaptis"],
                domain_type=data["domain_type"],
                pattern_description=data["pattern"]["description"],
                abstract_predicates=[
                    AbstractPredicate(**p) for p in data["pattern"]["abstract_predicates"]
                ],
                template_vyaptis=[
                    TemplateVyapti(**t) for t in data["pattern"]["template_vyaptis"]
                ],
                diagnostic_questions=data["diagnostic_questions"],
                applicability_requires=data["applicability"]["requires"],
                applicability_excludes=data["applicability"]["excludes"],
                typical_domains=data["applicability"]["typical_domains"],
            )
            templates[template.framework_id] = template
        return templates
```

#### New File: `domain_registry.py` (~80 lines)

```python
class DomainConfig(BaseModel):
    """Configuration for a domain supported by the engine."""
    domain_id: str
    domain_name: str
    domain_type: DomainType
    kb_path: str                       # path to curated YAML
    shadow_kb_path: str                # path to shadow SQLite
    frameworks_dir: str                # path to framework templates
    guide_chapters_dir: Optional[str]  # path to guide chapters (for context)


class DomainRegistry:
    """Manages multiple domain configurations for multi-domain support."""

    def __init__(self, config_path: str = "data/domains.yaml"):
        self.domains: dict[str, DomainConfig] = {}
        if os.path.exists(config_path):
            self._load(config_path)

    def _load(self, path: str):
        with open(path) as f:
            data = yaml.safe_load(f)
        for d in data.get("domains", []):
            config = DomainConfig(**d)
            self.domains[config.domain_id] = config

    def get_domain(self, domain_id: str) -> Optional[DomainConfig]:
        return self.domains.get(domain_id)

    def detect_domain(self, query: str, all_kb_stores: dict[str, KnowledgeStore]) -> str:
        """Given a query, determine which domain's frameworks best apply.
        Uses the ScoreFrameworkApplicability from each domain's KB
        and returns the domain_id with the highest score."""
        # This is a simple max-score approach.
        # For production, could use an LLM classifier.
        best_domain = None
        best_score = 0.0
        for domain_id, ks in all_kb_stores.items():
            pipeline = AugmentationPipeline(ks)
            summary = pipeline._build_framework_summary()
            # Score this domain's frameworks against the query
            scorer = dspy.ChainOfThought(ScoreFrameworkApplicability)
            result = scorer(
                query=query,
                interpreted_intent=query,
                framework_summary=summary,
                domain_type=ks.domain_type.value,
            )
            score = float(result.applicability_score)
            if score > best_score:
                best_score = score
                best_domain = domain_id
        return best_domain
```

#### Multi-Domain `domains.yaml`

```yaml
# data/domains.yaml
domains:
  - domain_id: business_strategy
    domain_name: "Business Strategy"
    domain_type: CRAFT
    kb_path: "data/business_expert.yaml"
    shadow_kb_path: "data/shadow_kb_business.sqlite"
    frameworks_dir: "data/frameworks/business/"
    guide_chapters_dir: "../guides/business_expert/"

  - domain_id: software_architecture
    domain_name: "Software Architecture"
    domain_type: DESIGN
    kb_path: "data/software_architect.yaml"
    shadow_kb_path: "data/shadow_kb_software.sqlite"
    frameworks_dir: "data/frameworks/software/"
    guide_chapters_dir: "../guides/software_architect/"
```

#### v5 Tests

```python
class TestFrameworkTemplate:
    def test_load_template_yaml(self, tmp_path):
        """Framework template loads from YAML with all fields."""

    def test_variable_binding(self):
        """_apply_bindings replaces ${domain} etc. correctly."""


class TestFrameworkInstantiator:
    @pytest.mark.llm
    def test_instantiate_constraint_for_supply_chain(self, frameworks_dir):
        """Constraint cascade template instantiated for supply_chain produces valid vyaptis."""

    def test_unknown_framework_returns_empty(self, frameworks_dir):
        """Non-existent framework_id returns empty list."""


class TestDomainRegistry:
    def test_load_domains_yaml(self, tmp_path):
        """domains.yaml loads and parses correctly."""

    @pytest.mark.llm
    def test_detect_domain(self, multi_domain_kbs):
        """Business query routes to business domain; software query to software."""
```

---

## 8. Testing Strategy (All Versions)

### Test Pyramid

```
                    ┌───────────────┐
                    │  Integration  │  ← @pytest.mark.llm, @pytest.mark.web
                    │   (5-10)      │     Full pipeline with real LLM/API calls
                    ├───────────────┤
                    │   Module      │  ← Mock LLM responses, test logic
                    │   (15-25)     │     _parse, _validate, _merge, shadow_kb
                    ├───────────────┤
                    │    Unit       │  ← Pure functions, deterministic
                    │   (30-50)     │     snake_case, cycle detect, model validation
                    └───────────────┘
```

### Test Markers

```python
# conftest.py additions
def pytest_configure(config):
    config.addinivalue_line("markers", "llm: requires LLM API calls")
    config.addinivalue_line("markers", "web: requires web API calls (Tavily/DDG)")
    config.addinivalue_line("markers", "slow: takes >10s")
```

### Fixtures

```python
@pytest.fixture
def sample_ks() -> KnowledgeStore:
    """Minimal KB with 3 vyaptis for unit tests."""
    return KnowledgeStore(
        domain_type=DomainType.CRAFT,
        vyaptis={
            "V01": Vyapti(id="V01", name="unit_economics_value",
                statement="Positive unit economics indicates value creation",
                causal_status=CausalStatus.EMPIRICAL,
                antecedents=["positive_unit_economics"],
                consequent="value_creation",
                confidence=Confidence(existence=0.92, formulation=0.87, evidence="observational"),
                epistemic_status=EpistemicStatus.ESTABLISHED),
            "V02": Vyapti(id="V02", name="constraint_cascade",
                statement="Identifying the binding constraint makes resource allocation effective",
                causal_status=CausalStatus.STRUCTURAL,
                antecedents=["binding_constraint_identified"],
                consequent="resource_allocation_effective",
                confidence=Confidence(existence=0.88, formulation=0.82, evidence="theoretical"),
                epistemic_status=EpistemicStatus.ESTABLISHED),
            "V08": Vyapti(id="V08", name="value_compounding",
                statement="Value creation with effective resource allocation compounds into long term value",
                causal_status=CausalStatus.EMPIRICAL,
                antecedents=["value_creation", "resource_allocation_effective"],
                consequent="long_term_value",
                confidence=Confidence(existence=0.85, formulation=0.80, evidence="observational"),
                epistemic_status=EpistemicStatus.ESTABLISHED),
        },
        chapter_fingerprints={
            "ch03": ChapterFingerprint(
                chapter_id="ch03", title="Constraint Analysis",
                key_terms=["binding_constraint", "bottleneck", "throughput"],
                anchoring_concepts=["theory_of_constraints"],
                vyaptis_introduced=["V02"]),
        },
    )

@pytest.fixture
def shadow_kb_with_data(tmp_path) -> ShadowKB:
    """Shadow KB pre-populated with 5 test vyaptis in various states."""
    db_path = str(tmp_path / "test_shadow.sqlite")
    skb = ShadowKB(db_path=db_path)
    # ... populate with test data ...
    return skb
```

### Golden Test Cases

Maintain a `tests/golden/` directory with expected outputs for known queries:

```
tests/golden/
├── supply_chain_resilience.json    # expected augmentation for this query
├── pricing_strategy.json           # expected augmentation
└── astrophysics_decline.json       # expected decline (out of domain)
```

---

## 9. Migration Path Between Versions

### v1 → v2

1. `pip install tavily-python duckduckgo-search`
2. Add `evidence_search.py`
3. Add `evidence_gatherer` parameter to `AugmentationPipeline.__init__`
4. Set `TAVILY_API_KEY` environment variable (or use DDG fallback)
5. No schema changes. No database changes. Backward compatible.

### v2 → v3

1. Add `shadow_kb.py`, `review_queue.py`
2. Add `shadow_kb` parameter to `AugmentationPipeline.__init__`
3. First run creates `data/shadow_kb.sqlite` automatically
4. Move `AugmentationMetadata` and `AugmentationOrigin` to `schema.py`
5. Existing v2 deployments work unchanged (shadow_kb=None by default)

### v3 → v4

1. Add `source_reliability.py`
2. Add `source_reliability` table to `shadow_kb.sqlite` (auto-created by `ReliabilityTracker`)
3. Add `VitandaChallenge` signature and `StressTest` class to `kb_augmentation.py`
4. Add `reliability_tracker` and `enable_stress_test` params to pipeline
5. Backward compatible: both params default to None/False

### v4 → v5

1. Add `framework_templates.py`, `domain_registry.py`
2. Create `data/frameworks/` directory with template YAMLs
3. Create `data/domains.yaml`
4. Modify `AugmentationPipeline` to accept `FrameworkInstantiator` and use template-based generation alongside (not replacing) free-form generation
5. Backward compatible: without framework templates, falls back to v4 behavior

### Rollback Strategy

Each version is additive. To roll back:
- **Disable v5**: remove `framework_templates.py` import, set `framework_instantiator=None`
- **Disable v4**: set `enable_stress_test=False`, `reliability_tracker=None`
- **Disable v3**: set `shadow_kb=None` (SQLite file remains but is unused)
- **Disable v2**: set `evidence_gatherer=None`
- **Disable v1**: don't call `forward_with_augmentation`, use `forward` directly

The shadow KB SQLite file is never destructive — it's additive-only. The curated YAML KB is only modified by explicit HITL promotion (v3+), which requires human approval.

---

## Appendix A: File Manifest

```
anvikshiki_v4/
├── kb_augmentation.py          # v1: core augmentation pipeline
├── evidence_search.py          # v2: web search + evidence evaluation
├── shadow_kb.py                # v3: SQLite persistence
├── review_queue.py             # v3: HITL review interface
├── source_reliability.py       # v4: cross-source reliability tracking
├── framework_templates.py      # v5: formal framework YAML instantiation
├── domain_registry.py          # v5: multi-domain configuration
├── data/
│   ├── shadow_kb.sqlite        # v3+: generated automatically
│   ├── frameworks/             # v5: framework template YAMLs
│   │   ├── constraint_cascade.yaml
│   │   ├── optionality_commitment.yaml
│   │   └── ...
│   └── domains.yaml            # v5: multi-domain registry
└── tests/
    ├── test_kb_augmentation.py # v1+
    ├── test_evidence_search.py # v2+
    ├── test_shadow_kb.py       # v3+
    ├── test_review_queue.py    # v3+
    ├── test_source_reliability.py # v4+
    ├── test_stress_test.py     # v4+
    ├── test_framework_templates.py # v5+
    ├── test_domain_registry.py # v5+
    └── golden/                 # golden test cases
        ├── supply_chain_resilience.json
        └── astrophysics_decline.json
```

## Appendix B: LLM Call Budget Summary

| Version | Calls per Query (N=4 vyaptis) | What They Do |
|---------|-------------------------------|--------------|
| **v1** | 2 | domain check + generate |
| **v2** | ~10 | v1 + formulate queries(4) + evaluate evidence(4) |
| **v3** | 0–10 | 0 if shadow KB hit; else same as v2 |
| **v4** | ~14 | v2 + stress test(4) |
| **v5** | ~15 | v4 + framework instantiation(1) |

Shadow KB reuse (v3+) is the primary cost optimization — repeated queries in the same domain area cost 0 additional LLM calls after the first.
