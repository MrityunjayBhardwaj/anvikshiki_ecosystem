#!/usr/bin/env python3
"""
Ānvīkṣikī Engine — End-to-End Pipeline Reproduction
=====================================================

Runs both pipelines described in docs/pipeline_flowchart_llama3.2md.md:

  PART 1: OFFLINE KB ENRICHMENT (Stages A-E on Ch2 + T3 compilation)
  PART 2: ONLINE QUERY PIPELINE (Stages 0-11 for a sample query)

Usage:
    cd anvikshiki_ecosystem
    .venv/bin/python run_pipeline_e2e.py

Requires:
    - Local MLX server at http://localhost:8080/v1
      (start with: mlx_lm.server --model mlx-community/Llama-3.2-3B-Instruct-4bit --port 8080)
"""

import json
import os
import sys
import time

# Ensure the package is importable
sys.path.insert(0, os.path.dirname(__file__))

import dspy

# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════

LOCAL_LLM_URL = os.environ.get("LOCAL_LLM_URL", "http://localhost:8080/v1")
LOCAL_LLM_MODEL = os.environ.get(
    "LOCAL_LLM_MODEL", "mlx-community/Llama-3.2-3B-Instruct-4bit"
)
BUSINESS_YAML = "anvikshiki_v4/data/business_expert.yaml"
GUIDE_CH2 = "guides/business_expert/guide_ch2.md"

SAMPLE_QUERY = (
    "Does a company with strong LTV-CAC ratio and positive "
    "contribution margin have viable unit economics?"
)

SAMPLE_CHUNKS = [
    "### 2.1 The LTV-CAC Relationship\n"
    "The most fundamental equation in startup economics: LTV must exceed CAC. "
    "Lifetime Value (LTV) measures total revenue from a customer over their lifetime. "
    "Customer Acquisition Cost (CAC) measures what you spend to acquire each customer. "
    "When LTV > CAC, each customer creates value. When LTV < CAC, each customer destroys it.",
    "### 2.2 Contribution Margin\n"
    "Contribution margin = revenue - variable costs per unit. This is the true measure "
    "of unit-level profitability, not gross margin. Many startups confuse gross margin with "
    "contribution margin, leading to false confidence in unit economics.",
]


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

def banner(title: str) -> None:
    width = 72
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width + "\n")


def section(title: str) -> None:
    print(f"\n--- {title} ---\n")


def pp(obj, indent=2):
    """Pretty-print dicts/lists."""
    if isinstance(obj, dict):
        print(json.dumps(obj, indent=indent, default=str))
    else:
        print(obj)


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    t0 = time.time()

    # ── Configure DSPy ──
    banner("SETUP: Configure DSPy with Local MLX LLM")
    lm = dspy.LM(
        f"openai/{LOCAL_LLM_MODEL}",
        api_base=LOCAL_LLM_URL,
        api_key="local",
        max_tokens=4096,
    )
    dspy.configure(lm=lm, adapter=dspy.JSONAdapter())
    print(f"  LM: {LOCAL_LLM_MODEL}")
    print(f"  API: {LOCAL_LLM_URL}")

    # ── Load seed KB ──
    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

    ks = load_knowledge_store(BUSINESS_YAML)
    print(f"  KB loaded: {len(ks.vyaptis)} vyaptis, "
          f"{len(ks.chapter_fingerprints)} chapters")
    vocab = set()
    for v in ks.vyaptis.values():
        vocab.update(v.antecedents)
        vocab.add(v.consequent)
    print(f"  Predicate vocabulary: {len(vocab)} predicates")

    # ══════════════════════════════════════════════════════════
    #  PART 1: OFFLINE KB ENRICHMENT PIPELINE
    # ══════════════════════════════════════════════════════════

    banner("PART 1: OFFLINE KB ENRICHMENT PIPELINE")

    # ── Load guide text (ch02 only for demo) ──
    section("Loading Guide Text (Ch2)")
    with open(GUIDE_CH2) as f:
        ch2_text = f.read()
    print(f"  Loaded {GUIDE_CH2}: {len(ch2_text)} chars, "
          f"~{len(ch2_text.split())} words")

    guide_text = {"ch02": ch2_text}

    # ── Stage A-E: Predicate Extraction ──
    section("STAGE A-E: Predicate Extraction Pipeline")
    print("  Running extraction pipeline on ch02...")
    print("  (Stage A: extract candidates, B: decompose, "
          "C: canonicalize, D: construct vyaptis, E: validate)")

    from anvikshiki_v4.predicate_extraction import PredicateExtractionPipeline
    from anvikshiki_v4.extraction_schema import ExtractionConfig

    config = ExtractionConfig(
        ensemble_n=1,                    # reduced for speed with local LLM
        decomposition_max_depth=1,
        max_new_vyaptis_per_chapter=8,   # cap for demo
        min_confidence=0.3,
    )

    extraction_pipeline = PredicateExtractionPipeline(ks, config=config)

    t_extract = time.time()
    try:
        augmented_ks, validation, stage_d = extraction_pipeline(
            guide_text=guide_text
        )
        t_extract_done = time.time()

        section("STAGE A-E RESULTS")
        print(f"  Time: {t_extract_done - t_extract:.1f}s")
        print(f"  Valid: {validation.is_valid}")
        print(f"  New vyaptis proposed: {len(stage_d.new_vyaptis)}")
        print(f"  Refinement vyaptis: {len(stage_d.refinement_vyaptis)}")
        print(f"  Cycle errors: {validation.cycle_errors}")
        print(f"  Orphan predicates: {validation.orphan_predicates[:5]}")
        print(f"  Datalog errors: {validation.datalog_errors}")
        print(f"  Coverage ratio: {validation.coverage_ratio:.2f}")

        aug_vocab = set()
        for v in augmented_ks.vyaptis.values():
            aug_vocab.update(v.antecedents)
            aug_vocab.add(v.consequent)
        print(f"\n  Seed KB: {len(ks.vyaptis)} vyaptis, {len(vocab)} predicates")
        print(f"  Augmented KB: {len(augmented_ks.vyaptis)} vyaptis, "
              f"{len(aug_vocab)} predicates")
        print(f"  New predicates: {sorted(aug_vocab - vocab)[:10]}...")

        if stage_d.new_vyaptis:
            section("NEW VYAPTIS (from Stage D)")
            for pv in stage_d.new_vyaptis[:5]:
                print(f"  {pv.id}: {pv.name}")
                print(f"    Statement: {pv.statement[:80]}...")
                print(f"    {pv.antecedents} → {pv.consequent}")
                print(f"    Causal: {pv.causal_status}, "
                      f"Epistemic: {pv.epistemic_status}, "
                      f"Conf: {pv.confidence_existence:.2f}")
                print()

        # Use augmented KB for the rest of the pipeline
        active_ks = augmented_ks
    except Exception as e:
        print(f"\n  ⚠ Extraction pipeline error: {e}")
        print("  Falling back to seed KB for online pipeline.")
        active_ks = ks
        augmented_ks = ks
        validation = None
        stage_d = None

    # ── T3 Compilation ──
    section("T3 COMPILATION: Build GraphRAG Corpus")

    from anvikshiki_v4.t3_compiler import compile_t3

    t_t3 = time.time()
    graph, chunks = compile_t3(guide_text, active_ks)
    t_t3_done = time.time()

    print(f"  Time: {t_t3_done - t_t3:.2f}s")
    print(f"  Knowledge graph: {graph.number_of_nodes()} nodes, "
          f"{graph.number_of_edges()} edges")
    print(f"  Text chunks: {len(chunks)}")

    if chunks:
        section("SAMPLE CHUNKS (first 2)")
        for ch in chunks[:2]:
            print(f"  {ch.chunk_id}:")
            print(f"    Vyapti anchors: {ch.vyapti_anchors}")
            print(f"    Concept anchors: {ch.concept_anchors[:5]}")
            print(f"    Epistemic status: {ch.epistemic_status}")
            print(f"    Text: {ch.text[:100]}...")
            print()

    section("KNOWLEDGE GRAPH NODE TYPES")
    node_types = {}
    for _, data in graph.nodes(data=True):
        t = data.get("type", "unknown")
        node_types[t] = node_types.get(t, 0) + 1
    for t, count in sorted(node_types.items()):
        print(f"  {t}: {count}")

    # ══════════════════════════════════════════════════════════
    #  PART 2: ONLINE QUERY PIPELINE
    # ══════════════════════════════════════════════════════════

    banner("PART 2: ONLINE QUERY PIPELINE")
    print(f'  Query: "{SAMPLE_QUERY}"')

    # ── Stage 0: Request Ingestion ──
    section("STAGE 0: Request Ingestion")
    print(f"  Query: {SAMPLE_QUERY}")
    print(f"  Contestation mode: vada")
    print(f"  Retrieved chunks: {len(SAMPLE_CHUNKS)} provided")

    # ── Stage 1: KB Loading (already loaded) ──
    section("STAGE 1: KB Loading")
    # Use seed KB for online pipeline — keeps prompts small for 3B local LLM
    # The augmented KB was proven in the offline pipeline above
    active_ks = ks
    print(f"  Using seed KB (smaller prompts for local 3B LLM)")
    print(f"  (Augmented KB proven above: {len(augmented_ks.vyaptis) if augmented_ks != ks else '?'} vyaptis)")
    print(f"  Vyaptis: {len(active_ks.vyaptis)}")
    active_vocab = set()
    for v in active_ks.vyaptis.values():
        active_vocab.update(v.antecedents)
        active_vocab.add(v.consequent)
    print(f"  Predicates: {len(active_vocab)}")

    # ── Stage 0.5: Query Refinement ──
    section("STAGE 0.5: Query Refinement & Coverage Check")
    from anvikshiki_v4.query_refinement import QueryRefinementPipeline

    refinement = QueryRefinementPipeline(active_ks)

    t_refine = time.time()
    try:
        ref_result = refinement.refine(SAMPLE_QUERY)
    except Exception as e:
        print(f"  Query refinement LLM call failed: {type(e).__name__}: {str(e)[:120]}")
        print("  Using manual refinement result (positive_unit_economics maps directly).")
        from anvikshiki_v4.query_refinement import RefinementResult, CoverageReport
        # Manual coverage: this query maps to positive_unit_economics
        coverage = refinement.analyzer.analyze(
            mapped_predicates=["positive_unit_economics", "value_creation"],
            unmapped_concepts=["ltv_cac_ratio", "contribution_margin"],
        )
        ref_result = RefinementResult(
            original_query=SAMPLE_QUERY,
            interpreted_intent="Whether strong LTV-CAC and positive contribution margin indicate viable unit economics",
            suggested_queries=["What happens when positive_unit_economics is established?"],
            coverage=coverage,
            can_proceed=True,
        )
    t_refine_done = time.time()

    print(f"  Time: {t_refine_done - t_refine:.1f}s")
    print(f"  Interpreted intent: {ref_result.interpreted_intent}")
    print(f"  Mapped predicates: {ref_result.coverage.matched_predicates}")
    print(f"  Matched vyaptis: {ref_result.coverage.matched_vyaptis}")
    print(f"  Unmatched concepts: {ref_result.coverage.unmatched_concepts}")
    print(f"  Coverage ratio: {ref_result.coverage.coverage_ratio:.2f}")
    print(f"  Can proceed: {ref_result.can_proceed}")
    print(f"  Relevant chapters: {ref_result.coverage.relevant_chapters}")
    if ref_result.suggested_queries:
        print(f"  Suggested queries:")
        for sq in ref_result.suggested_queries:
            print(f"    - {sq}")
    if ref_result.decline_message:
        print(f"  Message: {ref_result.decline_message[:200]}")

    route = ("PROCEED" if ref_result.coverage.coverage_ratio >= 0.6
             else "PARTIAL" if ref_result.coverage.coverage_ratio >= 0.2
             else "DECLINE")
    print(f"\n  ROUTE: {route}")

    # ── Stage 2: Ontology Snippet (Layer 1) ──
    section("STAGE 2: Ontology Snippet Construction (Layer 1)")
    from anvikshiki_v4.grounding import OntologySnippetBuilder

    snippet_builder = OntologySnippetBuilder()
    snippet = snippet_builder.build(active_ks)
    print(f"  Snippet length: {len(snippet)} chars")
    print(f"  Rules listed: {snippet.count('RULE ')}")
    print(f"  Predicates listed: {snippet.count('(Entity)')}")
    # Show first few lines
    for line in snippet.split("\n")[:8]:
        print(f"    {line}")
    print("    ...")

    # ── Stage 3: LLM Grounding ──
    section("STAGE 3: LLM Grounding (NL → Predicates)")
    from anvikshiki_v4.grounding import GroundingPipeline, GroundingResult, GroundQuery

    # For local small LLM: use single-call grounding (not N=5 ensemble)
    # The full ensemble is for production with larger models
    print("  Using single-call grounding (lightweight mode for local 3B LLM)")
    grounder = dspy.ChainOfThought(GroundQuery)

    t_ground = time.time()
    try:
        g = grounder(
            query=SAMPLE_QUERY,
            ontology_snippet=snippet,
            domain_type=active_ks.domain_type.value,
        )
        grounding = GroundingResult(
            predicates=g.predicates if g.predicates else [],
            confidence=0.7,  # single call = moderate confidence
            disputed=[],
            warnings=["lightweight mode: single LLM call, no ensemble"],
            refinement_rounds=0,
            clarification_needed=False,
        )
    except Exception as e:
        print(f"  Grounding LLM call failed: {e}")
        print("  Falling back to manual grounding.")
        grounding = GroundingResult(
            predicates=["positive_unit_economics"],
            confidence=0.7,
            disputed=[],
            warnings=["manual fallback: LLM grounding failed"],
            refinement_rounds=0,
            clarification_needed=False,
        )
    t_ground_done = time.time()

    print(f"  Time: {t_ground_done - t_ground:.1f}s")
    print(f"  Predicates: {grounding.predicates}")
    print(f"  Confidence: {grounding.confidence:.2f}")
    print(f"  Disputed: {grounding.disputed}")
    print(f"  Warnings: {grounding.warnings}")
    print(f"  Refinement rounds: {grounding.refinement_rounds}")
    print(f"  Clarification needed: {grounding.clarification_needed}")

    # Validate grounded predicates exist in KB vocabulary
    valid_preds = []
    for p in grounding.predicates:
        # Extract predicate name (before parenthesis)
        pred_name = p.split("(")[0] if "(" in p else p
        if pred_name in active_vocab or f"not_{pred_name}" in active_vocab:
            valid_preds.append(p)
        else:
            print(f"  Dropping invalid predicate: {p} (not in KB vocabulary)")

    if not valid_preds:
        print("  No valid predicates from grounding. Using manual fallback.")
        valid_preds = ["positive_unit_economics(acme)"]

    grounding.predicates = valid_preds
    print(f"  Valid predicates after filtering: {grounding.predicates}")

    manual_predicates = None
    grounding_confidence = grounding.confidence

    # ── Stage 4: T2 Compilation ──
    section("STAGE 4: T2 Compilation (Facts + Rules → AF)")
    from anvikshiki_v4.t2_compiler_v4 import compile_t2

    if manual_predicates:
        query_facts = [
            {"predicate": p, "confidence": 0.7, "sources": ["manual_fallback"]}
            for p in manual_predicates
        ]
    else:
        query_facts = [
            {"predicate": p, "confidence": grounding_confidence,
             "sources": ["llm_grounding"]}
            for p in grounding.predicates
        ]

    print(f"  Query facts: {query_facts}")

    t_compile = time.time()
    af = compile_t2(active_ks, query_facts)
    t_compile_done = time.time()

    print(f"  Time: {t_compile_done - t_compile:.4f}s")
    print(f"  Arguments: {len(af.arguments)}")
    print(f"  Attacks: {len(af.attacks)}")

    section("ARGUMENTS BUILT")
    from anvikshiki_v4.schema_v4 import Label
    for aid, arg in af.arguments.items():
        if arg.conclusion.startswith("_"):
            continue
        top_rule = arg.top_rule if arg.top_rule else "premise"
        subs = [s for s in arg.sub_arguments] if arg.sub_arguments else []
        print(f"  {aid}: {arg.conclusion}")
        print(f"    top_rule: {top_rule}, sub_args: {subs}")
        print(f"    tag: b={arg.tag.belief:.3f}, d={arg.tag.disbelief:.3f}, "
              f"u={arg.tag.uncertainty:.3f}")
        print(f"    pramana: {arg.tag.pramana_type.name}, "
              f"depth={arg.tag.derivation_depth}, "
              f"trust={arg.tag.trust_score:.3f}")
        print(f"    sources: {sorted(arg.tag.source_ids)}")
        print()

    if af.attacks:
        section("ATTACKS")
        for atk in af.attacks:
            print(f"  {atk.attacker} → {atk.target}: "
                  f"{atk.attack_type} ({atk.hetvabhasa})")

    # ── Stage 5: Contestation ──
    section("STAGE 5: Contestation (Vāda)")
    from anvikshiki_v4.contestation import ContestationManager

    cm = ContestationManager()
    t_contest = time.time()
    vada_result = cm.vada(af)
    t_contest_done = time.time()
    labels = af.labels

    print(f"  Time: {t_contest_done - t_contest:.4f}s")
    print(f"  Open questions: {vada_result.open_questions}")
    print(f"  Suggested evidence: {vada_result.suggested_evidence}")

    section("EXTENSION LABELS")
    for aid, arg in af.arguments.items():
        if arg.conclusion.startswith("_"):
            continue
        label = labels.get(aid, Label.UNDECIDED)
        print(f"  {aid} ({arg.conclusion}): {label.value}")

    in_count = sum(1 for l in labels.values() if l == Label.IN)
    print(f"\n  Extension size: {in_count}")

    # ── Stage 6: Epistemic Status ──
    section("STAGE 6: Epistemic Status Derivation")
    conclusions = set(
        a.conclusion for a in af.arguments.values()
        if not a.conclusion.startswith("_")
    )

    results = {}
    for conc in sorted(conclusions):
        status, tag, args = af.get_epistemic_status(conc)
        if status is not None:
            results[conc] = {"status": status, "tag": tag, "arguments": args}
            print(f"  {conc}:")
            print(f"    Status: {status.value}")
            print(f"    Belief: {tag.belief:.3f}, Uncertainty: {tag.uncertainty:.3f}")
            print()

    # ── Stage 7: Provenance ──
    section("STAGE 7: Provenance Extraction")
    provenance = {}
    for conc, info in results.items():
        provenance[conc] = {
            "sources": sorted(info["tag"].source_ids),
            "pramana": info["tag"].pramana_type.name,
            "derivation_depth": info["tag"].derivation_depth,
            "trust": round(info["tag"].trust_score, 3),
            "decay": round(info["tag"].decay_factor, 3),
        }
        print(f"  {conc}:")
        pp(provenance[conc])
        print()

    # ── Stage 8: Uncertainty Decomposition ──
    section("STAGE 8: Uncertainty Decomposition")
    from anvikshiki_v4.uncertainty import compute_uncertainty_v4

    uncertainty = {}
    for conc, info in results.items():
        uq = compute_uncertainty_v4(
            info["tag"], grounding_confidence, conc, info["status"]
        )
        uncertainty[conc] = uq
        print(f"  {conc}:")
        print(f"    Total confidence: {uq['total_confidence']:.3f}")
        print(f"    Epistemic: status={uq['epistemic']['status']}, "
              f"belief={uq['epistemic'].get('belief', 'N/A')}")
        print(f"    Aleatoric: {uq['aleatoric']}")
        print(f"    Inference: {uq['inference']}")
        print()

    # ── Stage 9: Violation Detection ──
    section("STAGE 9: Violation Detection (Hetvābhāsa)")
    violations = []
    for atk in af.attacks:
        if labels.get(atk.attacker) == Label.IN:
            target_arg = af.arguments.get(atk.target)
            if target_arg and not target_arg.conclusion.startswith("_"):
                violations.append({
                    "hetvabhasa": atk.hetvabhasa,
                    "type": atk.attack_type,
                    "attacker": atk.attacker,
                    "target": atk.target,
                    "target_conclusion": target_arg.conclusion,
                })

    if violations:
        for v in violations:
            print(f"  {v['target_conclusion']}: defeated by {v['hetvabhasa']} "
                  f"({v['type']})")
    else:
        print("  No violations detected.")

    # ── Stage 10: LLM Synthesis ──
    section("STAGE 10: LLM Synthesis")
    from anvikshiki_v4.schema_v4 import EpistemicStatus as ES

    accepted_str = "\n".join(
        f"- {conc}: {info['status'].value} "
        f"(belief={info['tag'].belief:.2f}, "
        f"sources={sorted(info['tag'].source_ids)})"
        for conc, info in results.items()
        if info["status"] in (ES.ESTABLISHED, ES.HYPOTHESIS, ES.PROVISIONAL)
    ) or "No accepted conclusions."

    defeated_str = "\n".join(
        f"- {v['target_conclusion']}: defeated by {v['hetvabhasa']} ({v['type']})"
        for v in violations
    ) or "No defeated conclusions."

    uq_str = "\n".join(
        f"- {conc}: confidence={uq['total_confidence']:.2f}, "
        f"epistemic={uq['epistemic']['status']}"
        for conc, uq in uncertainty.items()
    )

    print("  Inputs to synthesizer:")
    print(f"    Accepted:\n{accepted_str}")
    print(f"    Defeated:\n{defeated_str}")
    print(f"    Uncertainty:\n{uq_str}")

    t_synth = time.time()

    # Use a single ChainOfThought call for robustness with local LLM
    # (dspy.Refine can struggle with small models)
    from anvikshiki_v4.engine_v4 import SynthesizeResponse
    synthesizer = dspy.ChainOfThought(SynthesizeResponse)

    max_retries = 3
    response = None
    for attempt in range(max_retries):
        try:
            response = synthesizer(
                query=SAMPLE_QUERY,
                accepted_arguments=accepted_str,
                defeated_arguments=defeated_str,
                uncertainty_report=uq_str,
                retrieved_prose="\n\n".join(SAMPLE_CHUNKS[:3]),
            )
            t_synth_done = time.time()

            section("STAGE 10 OUTPUT")
            print(f"  Time: {t_synth_done - t_synth:.1f}s")
            print(f"\n  Response:\n    {response.response}")
            print(f"\n  Sources cited: {response.sources_cited}")
            break
        except Exception as e:
            print(f"  Synthesis attempt {attempt+1}/{max_retries} failed: "
                  f"{type(e).__name__}: {str(e)[:100]}")
            if attempt == max_retries - 1:
                t_synth_done = time.time()
                print(f"  All synthesis attempts failed. Time: {t_synth_done - t_synth:.1f}s")
                response = None

    # ── Stage 11: Response Assembly ──
    section("STAGE 11: Final Response Assembly")
    final_response = {
        "query_text": SAMPLE_QUERY,
        "contestation_mode": "vada",
        "status": "completed",
        "response": response.response if response else "Synthesis failed",
        "sources": response.sources_cited if response else [],
        "uncertainty": {
            conc: {"total_confidence": round(uq["total_confidence"], 3)}
            for conc, uq in uncertainty.items()
        },
        "provenance": provenance,
        "violations": violations,
        "grounding_confidence": round(grounding_confidence, 3),
        "extension_size": in_count,
        "contestation": {
            "mode": "vada",
            "open_questions": vada_result.open_questions,
            "suggested_evidence": vada_result.suggested_evidence,
        },
    }

    print("  FINAL JSON RESPONSE:")
    print(json.dumps(final_response, indent=2, default=str))

    # ══════════════════════════════════════════════════════════
    #  SUMMARY
    # ══════════════════════════════════════════════════════════

    banner("PIPELINE SUMMARY")
    total_time = time.time() - t0
    print(f"  Total wall time: {total_time:.1f}s")
    print(f"\n  OFFLINE PIPELINE:")
    print(f"    Seed KB: {len(ks.vyaptis)} vyaptis, {len(vocab)} predicates")
    if validation:
        print(f"    Augmented KB: {len(augmented_ks.vyaptis)} vyaptis, "
              f"{len(aug_vocab)} predicates")
        print(f"    New vyaptis: {len(stage_d.new_vyaptis) if stage_d else 0}")
        print(f"    Validation: {'PASS' if validation.is_valid else 'FAIL'}")
    print(f"    T3 graph: {graph.number_of_nodes()} nodes, "
          f"{graph.number_of_edges()} edges")
    print(f"    T3 chunks: {len(chunks)}")

    print(f"\n  ONLINE PIPELINE:")
    print(f"    Query refinement: coverage={ref_result.coverage.coverage_ratio:.2f} "
          f"→ {route}")
    print(f"    Grounding: {len(grounding.predicates)} predicates, "
          f"conf={grounding_confidence:.2f}")
    print(f"    Argumentation: {len(af.arguments)} args, {len(af.attacks)} attacks")
    print(f"    Extension: {in_count} IN")
    print(f"    Violations: {len(violations)}")
    print(f"    Synthesis: {'OK' if response else 'FAILED'}")


if __name__ == "__main__":
    main()
