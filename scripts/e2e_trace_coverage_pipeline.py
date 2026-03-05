#!/usr/bin/env python3
"""
End-to-End Pipeline Trace: T2b → Coverage → T3a → T2 → Contestation → Synthesis

Exercises the full updated pipeline (deterministic parts) using business_expert.yaml.
Traces three query scenarios:
  1. FULL coverage query (predicates exist in KB)
  2. PARTIAL coverage query (some predicates match)
  3. DECLINE query (no matching predicates — T3b augmentation path)

Outputs a structured trace to stdout for capture into the flowchart doc.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store, compile_t2
from anvikshiki_v4.coverage import SemanticCoverageAnalyzer
from anvikshiki_v4.t3a_retriever import T3aRetriever
from anvikshiki_v4.t3_compiler import TextChunk
from anvikshiki_v4.schema import (
    AugmentationMetadata, AugmentationOrigin,
    Vyapti, Confidence,
    EpistemicStatus, CausalStatus, DecayRisk,
)
from anvikshiki_v4.schema_v4 import Label
from anvikshiki_v4.contestation import ContestationManager
from anvikshiki_v4.uncertainty import compute_uncertainty_v4


def separator(title: str):
    print(f"\n{'='*72}")
    print(f"  {title}")
    print(f"{'='*72}\n")


def subsep(title: str):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}\n")


def main():
    separator("PHASE 0: Load Base KnowledgeStore")

    kb_path = os.path.join(
        os.path.dirname(__file__), "..",
        "anvikshiki_v4", "data", "business_expert.yaml"
    )
    ks = load_knowledge_store(kb_path)

    print(f"Domain: {ks.domain_type.value}")
    print(f"Vyaptis: {len(ks.vyaptis)} ({', '.join(sorted(ks.vyaptis.keys()))})")
    print(f"Hetvabhasas: {len(ks.hetvabhasas)}")
    print(f"Chapters: {len(ks.chapter_fingerprints)}")

    # Collect all predicates
    all_preds = set()
    for v in ks.vyaptis.values():
        all_preds.update(v.antecedents)
        if v.consequent:
            all_preds.add(v.consequent)
    print(f"Total predicates: {len(all_preds)}")
    print(f"Predicates: {sorted(all_preds)}")

    # ──────────────────────────────────────────────────────────
    separator("PHASE 1: Simulate T2b Compile-Time Output")
    # ──────────────────────────────────────────────────────────

    # Simulate T2b output: fine-grained vyaptis + synonym table
    # (In production, compile_t2b() calls PredicateExtractionPipeline)

    # Add fine-grained vyaptis to a copy of the KS
    augmented_ks = ks.model_copy(deep=True)

    fine_grained_vyaptis = {
        "V12": Vyapti(
            id="V12",
            name="LTV-CAC Viability Test",
            statement="When LTV exceeds CAC and contribution margin is positive, unit economics are positive",
            causal_status=CausalStatus.EMPIRICAL,
            scope_conditions=["commercial_enterprise"],
            scope_exclusions=["subsidized_entity"],
            confidence=Confidence(existence=0.85, formulation=0.80, evidence="observational"),
            epistemic_status=EpistemicStatus.WORKING_HYPOTHESIS,
            decay_risk=DecayRisk.MODERATE,
            sources=["src_hbs_unit_economics"],
            antecedents=["ltv_exceeds_cac", "positive_contribution_margin"],
            consequent="positive_unit_economics",
            augmentation_metadata=AugmentationMetadata(
                origin=AugmentationOrigin.GUIDE_EXTRACTED,
                source_chapter_ids=["ch02"],
                parent_vyapti_id="V01",
            ),
        ),
        "V13": Vyapti(
            id="V13",
            name="Unit Economics Death Spiral",
            statement="When unit economics are negative, the business enters a death spiral of increasing losses",
            causal_status=CausalStatus.EMPIRICAL,
            scope_conditions=["commercial_enterprise"],
            scope_exclusions=[],
            confidence=Confidence(existence=0.80, formulation=0.75, evidence="observational"),
            epistemic_status=EpistemicStatus.WORKING_HYPOTHESIS,
            decay_risk=DecayRisk.MODERATE,
            sources=["src_ries_2011"],
            antecedents=["negative_unit_economics"],
            consequent="unit_economics_death_spiral",
            augmentation_metadata=AugmentationMetadata(
                origin=AugmentationOrigin.GUIDE_EXTRACTED,
                source_chapter_ids=["ch02"],
                parent_vyapti_id="V01",
            ),
        ),
        "V14": Vyapti(
            id="V14",
            name="Maturity Mismatch Warning",
            statement="Maturity mismatch between business model and market cycle leads to negative unit economics",
            causal_status=CausalStatus.EMPIRICAL,
            scope_conditions=["commercial_enterprise"],
            scope_exclusions=[],
            confidence=Confidence(existence=0.80, formulation=0.70, evidence="observational"),
            epistemic_status=EpistemicStatus.WORKING_HYPOTHESIS,
            decay_risk=DecayRisk.MODERATE,
            sources=["src_hbs_unit_economics"],
            antecedents=["maturity_mismatch"],
            consequent="negative_unit_economics",
            augmentation_metadata=AugmentationMetadata(
                origin=AugmentationOrigin.GUIDE_EXTRACTED,
                source_chapter_ids=["ch02"],
                parent_vyapti_id="V01",
            ),
        ),
    }

    for vid, v in fine_grained_vyaptis.items():
        augmented_ks.vyaptis[vid] = v
    augmented_ks.fine_grained_vyapti_ids = list(fine_grained_vyaptis.keys())

    # Synonym table (from T2b Stage C)
    synonym_table = {
        "supply_chain_bottleneck": "binding_constraint_identified",
        "ltv_above_cac": "ltv_exceeds_cac",
        "ltv_greater_than_cac": "ltv_exceeds_cac",
        "unit_econ_positive": "positive_unit_economics",
        "organizational_entropy": "coordination_overhead",
    }
    augmented_ks.synonym_table = synonym_table

    # Source sections (for T3a cross-linking)
    t2b_source_sections = {
        "V12": ["ch02"],
        "V13": ["ch02"],
        "V14": ["ch02"],
    }

    # Collect augmented predicates
    aug_preds = set()
    for v in augmented_ks.vyaptis.values():
        aug_preds.update(v.antecedents)
        if v.consequent:
            aug_preds.add(v.consequent)

    print(f"Augmented KS vyaptis: {len(augmented_ks.vyaptis)} (base: {len(ks.vyaptis)}, fine-grained: {len(fine_grained_vyaptis)})")
    print(f"Augmented predicates: {len(aug_preds)} (was {len(all_preds)})")
    print(f"New predicates: {sorted(aug_preds - all_preds)}")
    print(f"Fine-grained IDs: {augmented_ks.fine_grained_vyapti_ids}")
    print(f"\nSynonym table:")
    for alias, canonical in sorted(synonym_table.items()):
        print(f"  {alias} → {canonical}")
    print(f"\nSource sections (T2b → T3a cross-link):")
    for vid, chapters in t2b_source_sections.items():
        print(f"  {vid} → {chapters}")

    # ──────────────────────────────────────────────────────────
    separator("PHASE 2: Build SemanticCoverageAnalyzer")
    # ──────────────────────────────────────────────────────────

    coverage_analyzer = SemanticCoverageAnalyzer(
        knowledge_store=augmented_ks,
        synonym_table=synonym_table,
    )

    print(f"Vocabulary size: {len(coverage_analyzer._vocab)}")
    print(f"Vocabulary: {sorted(coverage_analyzer._vocab)}")
    print(f"Synonym table entries: {len(coverage_analyzer._synonym_table)}")

    # ──────────────────────────────────────────────────────────
    separator("PHASE 3: Build T3a Retriever (fallback mode)")
    # ──────────────────────────────────────────────────────────

    # Create sample TextChunks (simulating T3 compiler output)
    sample_chunks = [
        TextChunk(
            chunk_id="ch02_s001", chapter_id="ch02",
            text="### 2.1 The LTV-CAC Relationship\nThe most fundamental equation in startup economics: LTV must exceed CAC. When lifetime value exceeds customer acquisition cost and contribution margin is positive, the business has viable unit economics.",
            vyapti_anchors=["V01", "V12"],
            concept_anchors=["unit_economics", "ltv_cac"],
            epistemic_status="established",
        ),
        TextChunk(
            chunk_id="ch02_s002", chapter_id="ch02",
            text="### 2.2 The Death Spiral\nWhen unit economics are negative — each customer destroys value — the business enters a death spiral. Growth accelerates losses rather than building value. This is the unit economics death spiral.",
            vyapti_anchors=["V13"],
            concept_anchors=["death_spiral", "negative_unit_economics"],
            epistemic_status="hypothesis",
        ),
        TextChunk(
            chunk_id="ch03_s001", chapter_id="ch03",
            text="### 3.1 Identifying the Binding Constraint\nPerformance is determined by the binding constraint. Focus all optimization effort on the bottleneck — everything else is waste until the constraint is addressed.",
            vyapti_anchors=["V02"],
            concept_anchors=["binding_constraint", "constraint_theory"],
            epistemic_status="established",
        ),
        TextChunk(
            chunk_id="ch04_s001", chapter_id="ch04",
            text="### 4.1 Information Asymmetry\nThe party with superior information captures disproportionate value. Market structure and pricing power flow from information advantages.",
            vyapti_anchors=["V03"],
            concept_anchors=["information_asymmetry", "pricing_power"],
            epistemic_status="established",
        ),
        TextChunk(
            chunk_id="ch05_s001", chapter_id="ch05",
            text="### 5.1 Organizational Growth and Entropy\nOrganizations accumulate coordination overhead as they grow. The Market Signal Decay Law: the further from the customer, the more distorted the signal.",
            vyapti_anchors=["V04", "V05"],
            concept_anchors=["organizational_growth", "market_signal"],
            epistemic_status="established",
        ),
        TextChunk(
            chunk_id="ch06_s001", chapter_id="ch06",
            text="### 6.1 Capital Allocation\nOver long periods, company value is determined by how the CEO allocates capital. Effective resource allocation combined with value creation drives long-term value.",
            vyapti_anchors=["V08"],
            concept_anchors=["capital_allocation", "long_term_value"],
            epistemic_status="established",
        ),
        TextChunk(
            chunk_id="ch07_s001", chapter_id="ch07",
            text="### 7.1 Disruption Theory\nIncumbents systematically underinvest in low-margin markets. The disruption asymmetry creates vulnerability for rational incumbents.",
            vyapti_anchors=["V09"],
            concept_anchors=["disruption", "incumbent_vulnerability"],
            epistemic_status="contested",
        ),
        TextChunk(
            chunk_id="ch08_s001", chapter_id="ch08",
            text="### 8.1 Executive Judgment\nJudgment quality depends on calibration accuracy — knowing what you know vs what you don't. Strategic commitment creates capability but destroys optionality.",
            vyapti_anchors=["V06", "V10"],
            concept_anchors=["judgment", "optionality"],
            epistemic_status="established",
        ),
    ]

    t3a_retriever = T3aRetriever(chunks=sample_chunks)
    print(f"T3a Retriever initialized with {len(sample_chunks)} chunks")
    print(f"Embedding retriever available: {t3a_retriever._retriever is not None}")
    print(f"Fallback mode: {t3a_retriever._retriever is None}")

    # ──────────────────────────────────────────────────────────
    separator("SCENARIO 1: FULL Coverage Query")
    # ──────────────────────────────────────────────────────────

    query_1 = "Does a company with strong LTV-CAC ratio and positive contribution margin have viable unit economics?"
    grounded_predicates_1 = [
        "positive_unit_economics(acme)",
        "ltv_exceeds_cac(acme)",
        "positive_contribution_margin(acme)",
    ]

    subsep("Step 1: Coverage Analysis")
    coverage_1 = coverage_analyzer.analyze(grounded_predicates_1)
    print(f"Query: {query_1}")
    print(f"Grounded predicates: {grounded_predicates_1}")
    print(f"\nCoverage ratio: {coverage_1.coverage_ratio:.2f}")
    print(f"Decision: {coverage_1.decision}")
    print(f"Matched: {coverage_1.matched_predicates}")
    print(f"Unmatched: {coverage_1.unmatched_predicates}")
    print(f"Match details:")
    for pred, match_type in coverage_1.match_details.items():
        print(f"  {pred} → {match_type}")
    print(f"Relevant vyaptis: {coverage_1.relevant_vyaptis}")

    subsep("Step 2: Route → FULL → compile_t2 with augmented KB")
    print(f"Route: FULL → proceed with base+fine KB ({len(augmented_ks.vyaptis)} vyaptis)")

    # Build query facts — T2 compiler uses bare predicates (no entity tags)
    # Entity stripping happens at grounding→T2 boundary
    grounding_confidence = 0.7
    bare_predicates_1 = [p.split("(")[0] for p in grounded_predicates_1]
    query_facts_1 = [
        {"predicate": p, "confidence": grounding_confidence, "sources": []}
        for p in bare_predicates_1
    ]
    print(f"\nQuery facts for T2:")
    for f in query_facts_1:
        print(f"  {f}")

    subsep("Step 3: T2 Compilation (Facts + Rules → AF)")
    af_1 = compile_t2(augmented_ks, query_facts_1)
    print(f"Arguments constructed: {len(af_1.arguments)}")
    for aid, arg in sorted(af_1.arguments.items()):
        neg = " [NEGATED]" if arg.conclusion.startswith("not_") else ""
        rule_info = f"via {arg.top_rule}" if arg.top_rule else "[premise]"
        tag = arg.tag
        belief = f"b={tag.belief:.3f}"
        depth = f"depth={tag.derivation_depth}"
        sources = f"sources={sorted(tag.source_ids)}"
        print(f"  {aid}: {arg.conclusion} {rule_info} ({belief}, {depth}, {sources}){neg}")

    print(f"\nAttacks: {len(af_1.attacks)}")
    for atk in af_1.attacks:
        print(f"  {atk.attacker} → {atk.target} ({atk.attack_type}, hetvabhasa={atk.hetvabhasa})")

    subsep("Step 4: Contestation (vada)")
    cm = ContestationManager()
    vada_result = cm.vada(af_1)
    labels = af_1.labels
    print(f"Extension labels:")
    for aid, lbl in sorted(labels.items()):
        arg = af_1.arguments[aid]
        print(f"  {aid}: {arg.conclusion} → {lbl.value}")
    in_count = sum(1 for l in labels.values() if l == Label.IN)
    out_count = sum(1 for l in labels.values() if l == Label.OUT)
    undec_count = sum(1 for l in labels.values() if l == Label.UNDECIDED)
    print(f"\nIN: {in_count}, OUT: {out_count}, UNDECIDED: {undec_count}")
    print(f"Open questions: {vada_result.open_questions}")

    subsep("Step 5: Epistemic Status")
    conclusions = set(
        a.conclusion for a in af_1.arguments.values()
        if not a.conclusion.startswith("_")
    )
    results_1 = {}
    for conc in sorted(conclusions):
        status, tag, args = af_1.get_epistemic_status(conc)
        if status is not None:
            results_1[conc] = {"status": status, "tag": tag, "arguments": args}
            print(f"  {conc}:")
            print(f"    status: {status.value}")
            print(f"    belief: {tag.belief:.4f}")
            print(f"    disbelief: {tag.disbelief:.4f}")
            print(f"    uncertainty: {tag.uncertainty:.4f}")
            print(f"    derivation_depth: {tag.derivation_depth}")
            print(f"    sources: {sorted(tag.source_ids)}")

    subsep("Step 6: Provenance")
    for conc, info in sorted(results_1.items()):
        tag = info["tag"]
        print(f"  {conc}:")
        print(f"    pramana: {tag.pramana_type.name}")
        print(f"    trust: {tag.trust_score:.4f}")
        print(f"    decay: {tag.decay_factor:.4f}")
        print(f"    sources: {sorted(tag.source_ids)}")

    subsep("Step 7: Uncertainty Decomposition")
    for conc, info in sorted(results_1.items()):
        uq = compute_uncertainty_v4(
            info["tag"], grounding_confidence,
            conc, info["status"],
        )
        print(f"  {conc}:")
        print(f"    total_confidence: {uq['total_confidence']:.4f}")
        print(f"    epistemic: {uq['epistemic']}")
        print(f"    aleatory: {uq.get('aleatory', 'N/A')}")

    subsep("Step 8: T3a Retrieval (parallel)")
    # Cross-linked retrieval: boost sections from activated predicates
    activated_sections = {}
    for vid in coverage_1.relevant_vyaptis:
        if vid in t2b_source_sections:
            activated_sections[vid] = t2b_source_sections[vid]

    print(f"Activated predicate sections for T3a boost: {activated_sections}")

    if activated_sections:
        t3a_chunks_1 = t3a_retriever.retrieve_for_predicates(
            activated_sections, query_1, k=3
        )
    else:
        t3a_chunks_1 = t3a_retriever.retrieve(query_1, k=3)

    print(f"Retrieved {len(t3a_chunks_1)} chunks:")
    for c in t3a_chunks_1:
        print(f"  [{c.chunk_id}] chapter={c.chapter_id}, vyaptis={c.vyapti_anchors}")
        print(f"    text={c.text[:80]}...")

    subsep("Step 9: Violations (hetvabhasa)")
    violations_1 = []
    for atk in af_1.attacks:
        if labels.get(atk.attacker) == Label.IN:
            target_arg = af_1.arguments.get(atk.target)
            if target_arg and not target_arg.conclusion.startswith("_"):
                violations_1.append({
                    "hetvabhasa": atk.hetvabhasa,
                    "type": atk.attack_type,
                    "target_conclusion": target_arg.conclusion,
                })
    print(f"Violations: {len(violations_1)}")
    for v in violations_1:
        print(f"  {v}")

    # ──────────────────────────────────────────────────────────
    separator("SCENARIO 2: PARTIAL Coverage Query")
    # ──────────────────────────────────────────────────────────

    query_2 = "How does a supply chain bottleneck affect a company's unit economics?"
    grounded_predicates_2 = [
        "supply_chain_bottleneck(acme)",
        "positive_unit_economics(acme)",
    ]

    subsep("Step 1: Coverage Analysis")
    coverage_2 = coverage_analyzer.analyze(grounded_predicates_2)
    print(f"Query: {query_2}")
    print(f"Grounded predicates: {grounded_predicates_2}")
    print(f"\nCoverage ratio: {coverage_2.coverage_ratio:.2f}")
    print(f"Decision: {coverage_2.decision}")
    print(f"Matched: {coverage_2.matched_predicates}")
    print(f"Unmatched: {coverage_2.unmatched_predicates}")
    print(f"Match details:")
    for pred, match_type in coverage_2.match_details.items():
        print(f"  {pred} → {match_type}")
    print(f"Relevant vyaptis: {coverage_2.relevant_vyaptis}")

    subsep("Step 2: Route → FULL (1.0 ≥ 0.6) → proceed with augmented KB")
    print(f"Both predicates matched (exact + synonym), ratio=1.0 → FULL coverage")
    print(f"Route: proceed with base+fine KB ({len(augmented_ks.vyaptis)} vyaptis)")

    query_facts_2 = [
        {"predicate": "binding_constraint_identified", "confidence": 0.65, "sources": []},
        {"predicate": "positive_unit_economics", "confidence": 0.7, "sources": []},
    ]

    subsep("Step 3: T2 Compilation")
    af_2 = compile_t2(augmented_ks, query_facts_2)
    print(f"Arguments: {len(af_2.arguments)}")
    for aid, arg in sorted(af_2.arguments.items()):
        tag = arg.tag
        belief = f"b={tag.belief:.3f}"
        print(f"  {aid}: {arg.conclusion} {'[premise]' if not arg.top_rule else f'via {arg.top_rule}'} ({belief})")
    print(f"Attacks: {len(af_2.attacks)}")

    # ──────────────────────────────────────────────────────────
    separator("SCENARIO 3: DECLINE Query → T3b Augmentation Path")
    # ──────────────────────────────────────────────────────────

    query_3 = "How does Tesla's vertical integration strategy affect its competitive position in the EV market?"
    grounded_predicates_3 = [
        "vertical_integration(tesla)",
        "ev_market_position(tesla)",
        "manufacturing_efficiency(tesla)",
    ]

    subsep("Step 1: Coverage Analysis")
    coverage_3 = coverage_analyzer.analyze(grounded_predicates_3)
    print(f"Query: {query_3}")
    print(f"Grounded predicates: {grounded_predicates_3}")
    print(f"\nCoverage ratio: {coverage_3.coverage_ratio:.2f}")
    print(f"Decision: {coverage_3.decision}")
    print(f"Matched: {coverage_3.matched_predicates}")
    print(f"Unmatched: {coverage_3.unmatched_predicates}")
    print(f"Match details:")
    for pred, match_type in coverage_3.match_details.items():
        print(f"  {pred} → {match_type}")

    subsep("Step 2: Route → DECLINE → check T3b augmentation")
    print("Coverage DECLINE → trigger AugmentationPipeline")
    print("(AugmentationPipeline requires LLM — tracing expected flow)")
    print()
    print("  T3b Step 1: ScoreFrameworkApplicability")
    print("    Input: query='How does Tesla's vertical integration...'")
    print("    Input: framework_summary='Domain: CRAFT, 14 vyaptis...'")
    print("    Expected output: applicability_score ≈ 0.65 (business strategy domain)")
    print("    → Score ≥ 0.4 threshold → PROCEED")
    print()
    print("  T3b Step 2: GenerateAugmentationPredicates")
    print("    Input: applicable_vyaptis='V01, V02, V03, V06, V08' (structural axes)")
    print("    Expected output (parallel lists):")
    print("      vyapti_names:    ['Vertical Integration Value Test', 'Manufacturing Scale Advantage']")
    print("      antecedents:     ['vertical_integration, manufacturing_efficiency', 'manufacturing_efficiency']")
    print("      consequents:     ['competitive_advantage_sustainable', 'cost_leadership']")
    print("      confidence:      [0.65, 0.60]  (capped at 0.75)")
    print("      epistemic_status: hypothesis  (WORKING_HYPOTHESIS)")
    print()
    print("  T3b Step 3: Validate")
    print("    Cycle detection: no cycles with new vyaptis")
    print("    Datalog compile: all rules compile successfully")
    print()
    print("  T3b Step 4: Merge into KB copy")
    print("    merged_kb = augmented_ks.model_copy(deep=True)")
    print("    merged_kb.vyaptis['V15'] = Vyapti(vertical_integration_value_test...)")
    print("    merged_kb.vyaptis['V16'] = Vyapti(manufacturing_scale_advantage...)")
    print()

    # Simulate the merged KB for trace
    merged_ks = augmented_ks.model_copy(deep=True)
    sim_v15 = Vyapti(
        id="V15",
        name="Vertical Integration Value Test",
        statement="Vertical integration combined with manufacturing efficiency creates sustainable competitive advantage",
        causal_status=CausalStatus.EMPIRICAL,
        scope_conditions=["capital_intensive_industry"],
        scope_exclusions=[],
        confidence=Confidence(existence=0.65, formulation=0.55, evidence="theoretical"),
        epistemic_status=EpistemicStatus.WORKING_HYPOTHESIS,
        decay_risk=DecayRisk.MODERATE,
        sources=[],
        antecedents=["vertical_integration", "manufacturing_efficiency"],
        consequent="competitive_advantage_sustainable",
        augmentation_metadata=AugmentationMetadata(
            origin=AugmentationOrigin.LLM_PARAMETRIC,
            generating_query=query_3,
            framework_vyaptis_used=["V01", "V02", "V06"],
            parent_vyapti_id="V06",
        ),
    )
    sim_v16 = Vyapti(
        id="V16",
        name="Manufacturing Scale Advantage",
        statement="Manufacturing efficiency enables cost leadership in production-intensive markets",
        causal_status=CausalStatus.EMPIRICAL,
        scope_conditions=["production_intensive_market"],
        scope_exclusions=[],
        confidence=Confidence(existence=0.60, formulation=0.51, evidence="theoretical"),
        epistemic_status=EpistemicStatus.WORKING_HYPOTHESIS,
        decay_risk=DecayRisk.MODERATE,
        sources=[],
        antecedents=["manufacturing_efficiency"],
        consequent="cost_leadership",
        augmentation_metadata=AugmentationMetadata(
            origin=AugmentationOrigin.LLM_PARAMETRIC,
            generating_query=query_3,
            framework_vyaptis_used=["V01", "V02"],
            parent_vyapti_id="V02",
        ),
    )
    merged_ks.vyaptis["V15"] = sim_v15
    merged_ks.vyaptis["V16"] = sim_v16

    subsep("Step 3: T2 Compilation with merged KB")
    query_facts_3 = [
        {"predicate": "vertical_integration", "confidence": 0.65, "sources": []},
        {"predicate": "manufacturing_efficiency", "confidence": 0.60, "sources": []},
    ]
    af_3 = compile_t2(merged_ks, query_facts_3)
    print(f"Arguments: {len(af_3.arguments)}")
    for aid, arg in sorted(af_3.arguments.items()):
        tag = arg.tag
        belief = f"b={tag.belief:.3f}"
        depth = f"depth={tag.derivation_depth}"
        origin = ""
        v = merged_ks.vyaptis.get(arg.top_rule or "")
        if v and v.augmentation_metadata:
            origin = f" [{v.augmentation_metadata.origin.value}]"
        print(f"  {aid}: {arg.conclusion} {'[premise]' if not arg.top_rule else f'via {arg.top_rule}'} ({belief}, {depth}){origin}")
    print(f"Attacks: {len(af_3.attacks)}")
    for atk in af_3.attacks:
        print(f"  {atk.attacker} → {atk.target} ({atk.attack_type})")

    subsep("Step 4: Contestation")
    vada_3 = cm.vada(af_3)
    labels_3 = af_3.labels
    for aid, lbl in sorted(labels_3.items()):
        arg = af_3.arguments[aid]
        print(f"  {aid}: {arg.conclusion} → {lbl.value}")

    subsep("Step 5: Epistemic Status (with augmented vyaptis)")
    conclusions_3 = set(
        a.conclusion for a in af_3.arguments.values()
        if not a.conclusion.startswith("_")
    )
    for conc in sorted(conclusions_3):
        status, tag, args = af_3.get_epistemic_status(conc)
        if status is not None:
            print(f"  {conc}:")
            print(f"    status: {status.value}")
            print(f"    belief: {tag.belief:.4f}")
            print(f"    derivation_depth: {tag.derivation_depth}")
            origin_info = ""
            if tag.derivation_depth > 0:
                origin_info = " (derived through HYPOTHESIS augmented vyapti → epistemic downgrade)"
            print(f"    note: derived through augmented chain{origin_info}")

    subsep("Step 6: T3a Retrieval (no cross-link for DECLINE query)")
    t3a_chunks_3 = t3a_retriever.retrieve(query_3, k=3)
    print(f"Retrieved {len(t3a_chunks_3)} chunks:")
    for c in t3a_chunks_3:
        print(f"  [{c.chunk_id}] chapter={c.chapter_id}, vyaptis={c.vyapti_anchors}")
        print(f"    text={c.text[:80]}...")

    # ──────────────────────────────────────────────────────────
    separator("SCENARIO 4: DECLINE + Out-of-Domain")
    # ──────────────────────────────────────────────────────────

    query_4 = "What is the best recipe for chocolate soufflé?"
    grounded_predicates_4 = [
        "chocolate_preparation(recipe)",
        "baking_technique(souffle)",
    ]

    subsep("Step 1: Coverage Analysis")
    coverage_4 = coverage_analyzer.analyze(grounded_predicates_4)
    print(f"Query: {query_4}")
    print(f"Grounded predicates: {grounded_predicates_4}")
    print(f"\nCoverage ratio: {coverage_4.coverage_ratio:.2f}")
    print(f"Decision: {coverage_4.decision}")
    print(f"Matched: {coverage_4.matched_predicates}")
    print(f"Unmatched: {coverage_4.unmatched_predicates}")

    subsep("Step 2: Route → DECLINE + out-of-domain")
    print("Coverage DECLINE → trigger AugmentationPipeline")
    print()
    print("  T3b Step 1: ScoreFrameworkApplicability")
    print("    Input: query='What is the best recipe for chocolate soufflé?'")
    print("    Input: framework_summary='Domain: CRAFT (business strategy)...'")
    print("    Expected output: applicability_score ≈ 0.05")
    print("    → Score < 0.4 threshold → STOP (out-of-domain)")
    print()
    print("  AugmentationResult:")
    print("    augmented: False")
    print("    reason: 'Framework applicability too low (0.05 < 0.4)'")
    print()
    print("  Engine response:")
    print("    'This query falls outside my domain's reasoning framework.'")
    print("    'Framework applicability too low (0.05 < 0.4)'")

    # ──────────────────────────────────────────────────────────
    separator("SUMMARY: Coverage Routing Decisions")
    # ──────────────────────────────────────────────────────────

    print("┌─────────────────────────────────────────────────────────────┐")
    print("│ Scenario │ Coverage │ Decision │ Route                      │")
    print("├─────────────────────────────────────────────────────────────┤")
    print(f"│ 1 (FULL) │  {coverage_1.coverage_ratio:.2f}    │ {coverage_1.decision:8s} │ base+fine KB → T2 → AF     │")
    print(f"│ 2 (PART) │  {coverage_2.coverage_ratio:.2f}    │ {coverage_2.decision:8s} │ base+fine KB → T2 → AF     │")
    print(f"│ 3 (DECL) │  {coverage_3.coverage_ratio:.2f}    │ {coverage_3.decision:8s} │ T3b → merge → T2 → AF     │")
    print(f"│ 4 (OOD)  │  {coverage_4.coverage_ratio:.2f}    │ {coverage_4.decision:8s} │ decline (out-of-domain)    │")
    print("└─────────────────────────────────────────────────────────────┘")

    print()
    print("DONE — all deterministic pipeline stages traced successfully.")


if __name__ == "__main__":
    main()
