#!/usr/bin/env python3
"""
End-to-End Pipeline Trace with Gemini 2.5 Pro — FULL Input/Output Capture

Exercises the COMPLETE updated pipeline using a real LLM backend
(Google Gemini 2.5 Pro) with FULL prompt inputs, processing details,
and complete outputs at every stage.

Format matches docs/pipeline_flowchart_llama3.2md.md with INPUT/OUTPUT boxes.

Usage:
    GOOGLE_API_KEY=your_key python scripts/e2e_trace_gemini.py
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dspy

from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store, compile_t2
from anvikshiki_v4.t2b_compiler import compile_t2b
from anvikshiki_v4.t3_compiler import compile_t3
from anvikshiki_v4.coverage import SemanticCoverageAnalyzer
from anvikshiki_v4.t3a_retriever import T3aRetriever
from anvikshiki_v4.engine_factory import load_guide_dir
from anvikshiki_v4.schema_v4 import Label
from anvikshiki_v4.contestation import ContestationManager
from anvikshiki_v4.uncertainty import compute_uncertainty_v4
from anvikshiki_v4.grounding import (
    OntologySnippetBuilder, GroundingResult, GroundQuery,
)
from anvikshiki_v4.kb_augmentation import AugmentationPipeline
from anvikshiki_v4.engine_v4 import SynthesizeResponse


# ── Formatting Helpers ──

class TraceOutput:
    """Captures all output for both console and file."""
    def __init__(self):
        self.lines: list[str] = []

    def print(self, text: str = ""):
        print(text)
        self.lines.append(text)

    def banner(self, title: str):
        self.print(f"\n{'='*72}")
        self.print(f"  {title}")
        self.print(f"{'='*72}\n")

    def section(self, title: str):
        self.print(f"\n{'─'*60}")
        self.print(f"  {title}")
        self.print(f"{'─'*60}\n")

    def input_box(self, title: str, content: str):
        self.print(f"┌─ INPUT: {title} {'─'*(55 - len(title))}┐")
        for line in content.split('\n'):
            self.print(f"│ {line:<68} │")
        self.print(f"└{'─'*70}┘")

    def output_box(self, title: str, content: str):
        self.print(f"┌─ OUTPUT: {title} {'─'*(54 - len(title))}┐")
        for line in content.split('\n'):
            self.print(f"│ {line:<68} │")
        self.print(f"└{'─'*70}┘")

    def processing(self, content: str):
        self.print(f"\n                    ▼ Processing ▼\n")
        for line in content.split('\n'):
            self.print(f"  {line}")
        self.print()

    def save(self, path: str):
        with open(path, 'w') as f:
            f.write('\n'.join(self.lines))


# ── Guide directory (for real T2b + T3 compilation) ──

GUIDE_DIR = os.path.join(
    os.path.dirname(__file__), "..",
    "guides", "business_expert"
)


def main():
    t0 = time.time()
    out = TraceOutput()

    # ═══════════════════════════════════════════════════════════
    #  SETUP
    # ═══════════════════════════════════════════════════════════

    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable")
        sys.exit(1)

    out.banner("SETUP: Configure DSPy with Gemini 2.5 Pro")
    lm = dspy.LM("gemini/gemini-2.5-pro", api_key=api_key, max_tokens=4096)
    dspy.configure(lm=lm, adapter=dspy.JSONAdapter())

    out.input_box("DSPy Configuration", (
        f"LM model:  gemini/gemini-2.5-pro\n"
        f"Adapter:   JSONAdapter (structured output)\n"
        f"max_tokens: 4096\n"
        f"API key:   {api_key[:10]}...{api_key[-4:]}"
    ))

    # ═══════════════════════════════════════════════════════════
    #  PHASE 0: Load KB + Guide Text → Real T2b + T3 Compilation
    # ═══════════════════════════════════════════════════════════

    out.banner("PHASE 0: Load KnowledgeStore + Guide Text → compile_t2b + compile_t3")

    kb_path = os.path.join(
        os.path.dirname(__file__), "..",
        "anvikshiki_v4", "data", "business_expert.yaml"
    )
    ks = load_knowledge_store(kb_path)

    out.input_box("Base KnowledgeStore", (
        f"Source: anvikshiki_v4/data/business_expert.yaml\n"
        f"Domain: {ks.domain_type.value}\n"
        f"Vyaptis: {len(ks.vyaptis)} (V01-V11)\n"
        f"Hetvabhasas: {len(ks.hetvabhasas)}\n"
        f"\nBase vyapti rules:"
    ))
    for vid, v in sorted(ks.vyaptis.items()):
        out.print(f"  {vid}: {', '.join(v.antecedents)} → {v.consequent}")
        out.print(f"        [{v.causal_status.value}, {v.epistemic_status.value}, "
                  f"conf={v.confidence.existence:.2f}×{v.confidence.formulation:.2f}]")

    # ── Load guide text from actual markdown files ──
    out.section("Loading Guide Text from guides/business_expert/")

    guide_text = load_guide_dir(GUIDE_DIR)
    out.input_box("Guide Text Loaded", (
        f"Guide directory: {GUIDE_DIR}\n"
        f"Chapters loaded: {len(guide_text)}\n"
        + "\n".join(
            f"  {cid}: {len(text)} chars ({text[:80].strip()}...)"
            for cid, text in sorted(guide_text.items())
        )
    ))

    if not guide_text:
        out.print("WARNING: No guide text found. Falling back to YAML-only mode.")
        out.print(f"  Looked in: {GUIDE_DIR}")
        out.print("  Expected files: guide_ch2.md, guide_ch3_ch4.md, etc.")

    # ── T2b: Compile fine-grained KB from guide prose ──
    out.section("T2b Compilation: compile_t2b(base_ks, guide_text)")
    t2b_start = time.time()

    if guide_text:
        t2b_result = compile_t2b(ks, guide_text)
        augmented_ks = t2b_result.augmented_ks
        synonym_table = t2b_result.synonym_table
        t2b_source_sections = t2b_result.source_sections
        fine_grained_ids = t2b_result.fine_grained_vyapti_ids
    else:
        # Fallback: no guide text → use base KB as-is
        augmented_ks = ks.model_copy(deep=True)
        synonym_table = {}
        t2b_source_sections = {}
        fine_grained_ids = []

    t2b_elapsed = time.time() - t2b_start

    aug_preds = set()
    for v in augmented_ks.vyaptis.values():
        aug_preds.update(v.antecedents)
        if v.consequent:
            aug_preds.add(v.consequent)

    base_count = len(ks.vyaptis)
    fine_count = len(fine_grained_ids)

    out.output_box("T2b Result", (
        f"Time: {t2b_elapsed:.1f}s\n"
        f"Total vyaptis: {len(augmented_ks.vyaptis)} ({base_count} base + {fine_count} fine-grained)\n"
        f"Total predicates: {len(aug_preds)}\n"
        f"Fine-grained IDs: {fine_grained_ids}\n"
        f"Synonym table: {len(synonym_table)} entries\n"
        f"Source sections: {len(t2b_source_sections)} mappings"
    ))

    if fine_grained_ids:
        out.section("New Vyaptis from T2b (extracted from guide prose)")
        for vid in fine_grained_ids:
            v = augmented_ks.vyaptis[vid]
            origin = ""
            if v.augmentation_metadata:
                origin = f" [{v.augmentation_metadata.origin.value}"
                if v.augmentation_metadata.source_chapter_ids:
                    origin += f", {', '.join(v.augmentation_metadata.source_chapter_ids)}"
                origin += "]"
            out.print(f"  {vid}: {', '.join(v.antecedents)}")
            out.print(f"        → {v.consequent}{origin}")

    if synonym_table:
        out.section("Synonym Table (from Stage C canonicalization)")
        for alias, canonical in sorted(synonym_table.items()):
            out.print(f"  {alias} → {canonical}")

    if t2b_source_sections:
        out.section("Source Sections (T2b → T3a cross-link)")
        for vid, chapters in sorted(t2b_source_sections.items()):
            out.print(f"  {vid} → {chapters}")

    # ── T3: Compile text chunks from guide prose ──
    out.section("T3 Compilation: compile_t3(guide_text, augmented_ks)")
    t3_start = time.time()

    chunks = []
    if guide_text:
        _, chunks = compile_t3(guide_text, augmented_ks)

    t3_elapsed = time.time() - t3_start

    out.output_box("T3 Result", (
        f"Time: {t3_elapsed:.1f}s\n"
        f"Text chunks: {len(chunks)}\n"
        f"Chapters covered: {len(set(c.chapter_id for c in chunks)) if chunks else 0}"
    ))

    if chunks:
        out.section("Sample Chunks (first 3)")
        for c in chunks[:3]:
            out.print(f"  {c.chunk_id} ({c.chapter_id}): "
                      f"{c.text[:100].strip()}...")
            if c.vyapti_anchors:
                out.print(f"    vyapti_anchors: {c.vyapti_anchors}")

    # ═══════════════════════════════════════════════════════════
    #  BUILD COMPONENTS
    # ═══════════════════════════════════════════════════════════

    out.banner("BUILD: Coverage Analyzer + T3a Retriever + T3b Pipeline")

    coverage_analyzer = SemanticCoverageAnalyzer(augmented_ks, synonym_table)
    t3a_retriever = T3aRetriever(chunks=chunks) if chunks else T3aRetriever(chunks=[])
    augmentation_pipeline = AugmentationPipeline(augmented_ks)
    snippet_builder = OntologySnippetBuilder()
    ontology_snippet = snippet_builder.build(augmented_ks)
    cm = ContestationManager()

    out.output_box("Component Initialization", (
        f"Coverage analyzer: {len(coverage_analyzer._vocab)} predicates in vocabulary\n"
        f"T3a Retriever: {len(chunks)} chunks (from real guide text), "
        f"fallback={t3a_retriever._retriever is None}\n"
        f"T3b AugmentationPipeline: ready\n"
        f"Ontology snippet: {len(ontology_snippet)} chars, "
        f"{ontology_snippet.count('RULE ')} rules"
    ))

    out.section("Full Ontology Snippet (Layer 1 Defense)")
    out.print(ontology_snippet)

    # ═══════════════════════════════════════════════════════════
    #  SCENARIO 1: FULL Coverage — LLM Grounding + Inference
    # ═══════════════════════════════════════════════════════════

    out.banner("SCENARIO 1: FULL Coverage — In-Domain Query")

    query_1 = "Does a company with strong LTV-CAC ratio and positive contribution margin have viable unit economics?"

    # ── Stage 0: LLM Grounding ──
    out.section("Stage 0: LLM Grounding (Gemini 2.5 Pro)")

    out.input_box("GroundQuery DSPy Signature", (
        f"Signature: GroundQuery(dspy.Signature)\n"
        f"  Docstring: 'Translate a natural language query into\n"
        f"    structured predicates. Use ONLY predicates from the\n"
        f"    provided ontology snippet. Think step by step about\n"
        f"    which entities and relationships the query mentions.'\n"
        f"\n"
        f"  InputFields:\n"
        f"    query:           str  (User's NL question)\n"
        f"    ontology_snippet: str  (Valid predicates and rules)\n"
        f"    domain_type:     str  (Domain classification)\n"
        f"\n"
        f"  OutputFields:\n"
        f"    reasoning:        str  (Step-by-step predicate matching)\n"
        f"    predicates:       list[str]  (Structured predicates)\n"
        f"    relevant_vyaptis: list[str]  (IDs of relevant vyaptis)"
    ))

    out.input_box("Grounding Call Inputs (Scenario 1)", (
        f"query:\n"
        f"  \"{query_1}\"\n"
        f"\n"
        f"ontology_snippet: (see full snippet above, {len(ontology_snippet)} chars)\n"
        f"  First 5 rules:\n"
        + "\n".join(f"  {line}" for line in ontology_snippet.split('\n')[:20])
        + f"\n  ...\n"
        f"\n"
        f"domain_type: \"{augmented_ks.domain_type.value}\""
    ))

    grounder = dspy.ChainOfThought(GroundQuery)

    t_ground = time.time()
    try:
        g1 = grounder(
            query=query_1,
            ontology_snippet=ontology_snippet,
            domain_type=augmented_ks.domain_type.value,
        )
        grounding_1 = GroundingResult(
            predicates=g1.predicates if g1.predicates else [],
            confidence=0.75,
            warnings=["single-call grounding"],
        )
    except Exception as e:
        out.print(f"  Grounding failed: {e}")
        g1 = None
        grounding_1 = GroundingResult(
            predicates=["positive_unit_economics", "ltv_exceeds_cac", "positive_contribution_margin"],
            confidence=0.70,
            warnings=["manual fallback"],
        )
    t_ground_done = time.time()

    out.output_box("Grounding Result (Scenario 1)", (
        f"Time: {t_ground_done - t_ground:.1f}s\n"
        f"\n"
        f"reasoning:\n"
        f"  {getattr(g1, 'reasoning', 'N/A') if g1 else 'N/A'}\n"
        f"\n"
        f"predicates:\n"
        f"  {json.dumps(grounding_1.predicates, indent=2)}\n"
        f"\n"
        f"relevant_vyaptis:\n"
        f"  {json.dumps(getattr(g1, 'relevant_vyaptis', []) if g1 else [], indent=2)}\n"
        f"\n"
        f"confidence: {grounding_1.confidence}\n"
        f"warnings: {grounding_1.warnings}"
    ))

    # ── Stage 1: Coverage Analysis ──
    out.section("Stage 1: Semantic Coverage Analysis")

    out.input_box("Coverage Analysis Input", (
        f"grounded_predicates: {grounding_1.predicates}\n"
        f"\n"
        f"Analyzer vocabulary ({len(coverage_analyzer._vocab)} predicates):\n"
        f"  {sorted(list(coverage_analyzer._vocab))}\n"
        f"\n"
        f"Synonym table:\n"
        + "\n".join(f"  {k} → {v}" for k, v in synonym_table.items())
        + f"\n\nThresholds: FULL >= 0.6, PARTIAL >= 0.2, DECLINE < 0.2"
    ))

    coverage_1 = coverage_analyzer.analyze(grounding_1.predicates)

    out.processing(
        f"For each predicate:\n"
        + "\n".join(
            f"  '{p}' → match_type={coverage_1.match_details.get(p, 'UNMATCHED')}"
            for p in grounding_1.predicates
        )
        + f"\n\nCoverage ratio = |matched| / total = "
        f"{len(coverage_1.matched_predicates)} / {len(grounding_1.predicates)} "
        f"= {coverage_1.coverage_ratio:.2f}"
    )

    out.output_box("Coverage Result", (
        f"coverage_ratio: {coverage_1.coverage_ratio:.2f}\n"
        f"decision: {coverage_1.decision}\n"
        f"matched_predicates: {coverage_1.matched_predicates}\n"
        f"unmatched_predicates: {coverage_1.unmatched_predicates}\n"
        f"match_details: {json.dumps(coverage_1.match_details, indent=2)}\n"
        f"relevant_vyaptis: {coverage_1.relevant_vyaptis}"
    ))

    # ── Stage 2: Routing ──
    out.section("Stage 2: Coverage-Based Routing")
    out.print(f"  Decision: {coverage_1.decision}")
    if coverage_1.decision in ("FULL", "PARTIAL"):
        out.print(f"  Route: → T2 Compilation with augmented KB (no T3b needed)")
    elif coverage_1.decision == "DECLINE":
        out.print(f"  Route: → T3b Augmentation Pipeline")

    # ── Stage 3: T2 Compilation ──
    out.section("Stage 3: T2 Compilation (Facts + Rules → AF)")

    bare_preds_1 = [p.split("(")[0] for p in grounding_1.predicates]

    query_facts_1 = [
        {"predicate": p, "confidence": grounding_1.confidence, "sources": []}
        for p in bare_preds_1
    ]

    out.input_box("T2 Compilation Input", (
        f"KnowledgeStore: {len(augmented_ks.vyaptis)} vyaptis\n"
        f"\n"
        f"Entity stripping: (entity tags removed for bare predicate matching)\n"
        + "\n".join(f"  {orig} → {bare}" for orig, bare in zip(grounding_1.predicates, bare_preds_1))
        + f"\n\nquery_facts:\n"
        + json.dumps(query_facts_1, indent=2)
    ))

    t_t2 = time.time()
    af_1 = compile_t2(augmented_ks, query_facts_1)
    t_t2_done = time.time()

    # Reconstruct forward chain from AF structure
    out.processing(
        f"Step 3a: Create Premise Arguments\n"
        + "\n".join(
            f"  {aid}: {arg.conclusion} [premise]  tag: b={arg.tag.belief:.3f}, "
            f"d={arg.tag.disbelief:.3f}, u={arg.tag.uncertainty:.3f}, "
            f"pramana={arg.tag.pramana_type.name}"
            for aid, arg in sorted(af_1.arguments.items())
            if arg.top_rule is None and not arg.conclusion.startswith("_")
        )
        + f"\n\nStep 3b: Forward Chain (derive rule arguments)\n"
        + "\n".join(
            f"  {arg.top_rule}: {', '.join(augmented_ks.vyaptis[arg.top_rule].antecedents)} "
            f"→ {augmented_ks.vyaptis[arg.top_rule].consequent}\n"
            f"    All antecedents available ✓\n"
            f"    → Create {aid}: {arg.conclusion} via {arg.top_rule}\n"
            f"      sub_arguments: {arg.sub_arguments}\n"
            f"      tag: b={arg.tag.belief:.4f}, d={arg.tag.disbelief:.4f}, "
            f"u={arg.tag.uncertainty:.4f}\n"
            f"      derivation_depth: {arg.tag.derivation_depth}\n"
            f"      pramana: {arg.tag.pramana_type.name}\n"
            f"      trust: {arg.tag.trust_score:.4f}, decay: {arg.tag.decay_factor:.4f}"
            for aid, arg in sorted(af_1.arguments.items())
            if arg.top_rule is not None and not arg.conclusion.startswith("_")
        )
        + f"\n\nStep 3c: Derive Attacks\n"
        + (
            "\n".join(
                f"  {atk.attack_type.upper()}: {atk.attacker} → {atk.target} "
                f"(hetvabhasa: {atk.hetvabhasa})"
                for atk in af_1.attacks
            ) if af_1.attacks else "  No attacks derived."
        )
        + f"\n\nFixpoint: no new arguments → STOP"
        + f"\nTime: {t_t2_done - t_t2:.4f}s"
    )

    out.output_box("ArgumentationFramework", (
        f"arguments: {len(af_1.arguments)}\n"
        f"attacks: {len(af_1.attacks)}\n"
        + "\n".join(
            f"\n  {aid}: {arg.conclusion}\n"
            f"    top_rule: {arg.top_rule or '[premise]'}\n"
            f"    sub_arguments: {arg.sub_arguments}\n"
            f"    premises: {set(arg.premises)}\n"
            f"    tag: Tag(b={arg.tag.belief:.4f}, d={arg.tag.disbelief:.4f}, "
            f"u={arg.tag.uncertainty:.4f})\n"
            f"    pramana: {arg.tag.pramana_type.name}\n"
            f"    depth: {arg.tag.derivation_depth}, trust: {arg.tag.trust_score:.4f}, "
            f"decay: {arg.tag.decay_factor:.4f}\n"
            f"    sources: {set(arg.tag.source_ids)}"
            for aid, arg in sorted(af_1.arguments.items())
            if not arg.conclusion.startswith("_")
        )
    ))

    # ── Stage 4: T3a Retrieval (parallel) ──
    out.section("Stage 4: T3a Retrieval (cross-linked, parallel with T2)")

    activated = {}
    for vid in coverage_1.relevant_vyaptis:
        if vid in t2b_source_sections:
            activated[vid] = t2b_source_sections[vid]

    out.input_box("T3a Retrieval Input", (
        f"query: \"{query_1}\"\n"
        f"activated_sections (from T2b cross-link):\n"
        + (json.dumps(activated, indent=2) if activated else "  (none)")
        + f"\n\nk: 3"
    ))

    if activated:
        chunks_1 = t3a_retriever.retrieve_for_predicates(activated, query_1, k=3)
    else:
        chunks_1 = t3a_retriever.retrieve(query_1, k=3)

    out.output_box("Retrieved Chunks", (
        f"Count: {len(chunks_1)}\n"
        + "\n".join(
            f"\n  [{c.chunk_id}] chapter: {c.chapter_id}\n"
            f"  epistemic: {c.epistemic_status}\n"
            f"  vyapti_anchors: {c.vyapti_anchors}\n"
            f"  text: \"{c.text}\""
            for c in chunks_1
        )
    ))

    # ── Stage 5: Contestation ──
    out.section("Stage 5: Contestation (vāda)")

    out.input_box("Contestation Input", (
        f"ArgumentationFramework: {len(af_1.arguments)} args, {len(af_1.attacks)} attacks\n"
        f"Mode: vada (cooperative debate)"
    ))

    vada_1 = cm.vada(af_1)
    labels_1 = af_1.labels

    out.processing(
        "Grounded Semantics:\n"
        "  Iteration 1:\n"
        + "\n".join(
            f"    {aid}: {arg.conclusion} → no attackers → IN"
            for aid, arg in sorted(af_1.arguments.items())
            if not arg.conclusion.startswith("_")
        )
        + "\n  Fixpoint reached."
    )

    out.output_box("Contestation Result", (
        f"labels:\n"
        + "\n".join(
            f"  {aid}: {arg.conclusion} → {labels_1.get(aid, 'UNKNOWN').value}"
            for aid, arg in sorted(af_1.arguments.items())
            if not arg.conclusion.startswith("_")
        )
        + f"\n\nextension_size: {sum(1 for l in labels_1.values() if l == Label.IN)}"
        + f"\nopen_questions: {vada_1.open_questions}"
        + f"\nsuggested_evidence: {vada_1.suggested_evidence}"
    ))

    # ── Stage 6: Epistemic Status ──
    out.section("Stage 6: Epistemic Status Derivation")

    from anvikshiki_v4.schema_v4 import EpistemicStatus as ES

    conclusions_1 = set(a.conclusion for a in af_1.arguments.values() if not a.conclusion.startswith("_"))
    results_1 = {}
    for conc in sorted(conclusions_1):
        status, tag, args = af_1.get_epistemic_status(conc)
        if status:
            results_1[conc] = {"status": status, "tag": tag}

    out.output_box("Epistemic Status", (
        "\n".join(
            f"  {conc}:\n"
            f"    status: {info['status'].value}\n"
            f"    belief: {info['tag'].belief:.4f}\n"
            f"    disbelief: {info['tag'].disbelief:.4f}\n"
            f"    uncertainty: {info['tag'].uncertainty:.4f}\n"
            f"    pramana: {info['tag'].pramana_type.name}\n"
            f"    derivation_depth: {info['tag'].derivation_depth}"
            for conc, info in sorted(results_1.items())
        )
    ))

    # ── Stage 7-9: Provenance, Uncertainty, Violations ──
    out.section("Stages 7-9: Provenance / Uncertainty / Violations")

    uncertainty_1 = {}
    for conc, info in results_1.items():
        uq = compute_uncertainty_v4(info["tag"], grounding_1.confidence, conc, info["status"])
        uncertainty_1[conc] = uq

    out.output_box("Provenance (Stage 7)", (
        "\n".join(
            f"  {conc}:\n"
            f"    sources: {sorted(info['tag'].source_ids)}\n"
            f"    pramana: {info['tag'].pramana_type.name}\n"
            f"    derivation_depth: {info['tag'].derivation_depth}\n"
            f"    trust: {info['tag'].trust_score:.4f}\n"
            f"    decay: {info['tag'].decay_factor:.4f}"
            for conc, info in sorted(results_1.items())
        )
    ))

    out.output_box("Uncertainty Decomposition (Stage 8)", (
        "\n".join(
            f"  {conc}:\n"
            f"    epistemic: {json.dumps(uq.get('epistemic', {}))}\n"
            f"    aleatoric: {json.dumps(uq.get('aleatoric', {}))}\n"
            f"    inference: {json.dumps(uq.get('inference', {}))}\n"
            f"    total_confidence: {uq['total_confidence']:.4f}"
            for conc, uq in sorted(uncertainty_1.items())
        )
    ))

    violations_1 = []
    for atk in af_1.attacks:
        if labels_1.get(atk.attacker) == Label.IN:
            t_arg = af_1.arguments.get(atk.target)
            if t_arg and not t_arg.conclusion.startswith("_"):
                violations_1.append(atk)

    out.output_box("Violations / Hetvābhāsa (Stage 9)", (
        f"violations: {len(violations_1)}\n"
        + ("\n".join(
            f"  {atk.attack_type}: {atk.attacker} → {atk.target} ({atk.hetvabhasa})"
            for atk in violations_1
        ) if violations_1 else "  (none — no conflicts in this query)")
    ))

    # ── Stage 10: LLM Synthesis ──
    out.section("Stage 10: LLM Synthesis (Gemini 2.5 Pro)")

    accepted_str = "\n".join(
        f"- {conc}: {info['status'].value} (belief={info['tag'].belief:.2f})"
        for conc, info in results_1.items()
        if info["status"] in (ES.ESTABLISHED, ES.HYPOTHESIS, ES.PROVISIONAL)
    ) or "No accepted conclusions."

    defeated_str = "No defeated conclusions."
    uq_str = "\n".join(
        f"- {conc}: confidence={uq['total_confidence']:.2f}, epistemic={uq['epistemic']['status']}"
        for conc, uq in uncertainty_1.items()
    )
    retrieved_prose = "\n\n".join(c.text for c in chunks_1[:3])

    out.input_box("SynthesizeResponse DSPy Signature", (
        f"Signature: SynthesizeResponse(dspy.Signature)\n"
        f"  Docstring: 'Produce a calibrated response from\n"
        f"    argumentation results.'\n"
        f"\n"
        f"  InputFields:\n"
        f"    query:               str\n"
        f"    accepted_arguments:  str (formatted conclusions)\n"
        f"    defeated_arguments:  str (hetvabhasa types)\n"
        f"    uncertainty_report:  str (3-way decomposition)\n"
        f"    retrieved_prose:     str (T3a chunks)\n"
        f"\n"
        f"  OutputFields:\n"
        f"    response:      str  (calibrated with hedging)\n"
        f"    sources_cited: list[str]  (source IDs used)"
    ))

    out.input_box("Synthesis Call Inputs (Scenario 1)", (
        f"query:\n"
        f"  \"{query_1}\"\n"
        f"\n"
        f"accepted_arguments:\n"
        f"  {accepted_str}\n"
        f"\n"
        f"defeated_arguments:\n"
        f"  {defeated_str}\n"
        f"\n"
        f"uncertainty_report:\n"
        f"  {uq_str}\n"
        f"\n"
        f"retrieved_prose:\n"
        f"  {retrieved_prose}"
    ))

    synthesizer = dspy.ChainOfThought(SynthesizeResponse)

    t_synth = time.time()
    try:
        synth_1 = synthesizer(
            query=query_1,
            accepted_arguments=accepted_str,
            defeated_arguments=defeated_str,
            uncertainty_report=uq_str,
            retrieved_prose=retrieved_prose,
        )
        t_synth_done = time.time()

        out.output_box("Synthesis Result (Scenario 1)", (
            f"Time: {t_synth_done - t_synth:.1f}s\n"
            f"\n"
            f"reasoning:\n"
            f"  {getattr(synth_1, 'reasoning', 'N/A')}\n"
            f"\n"
            f"response:\n"
            f"  {synth_1.response}\n"
            f"\n"
            f"sources_cited:\n"
            f"  {synth_1.sources_cited}"
        ))
    except Exception as e:
        t_synth_done = time.time()
        out.print(f"  Synthesis failed ({t_synth_done - t_synth:.1f}s): {e}")

    # ═══════════════════════════════════════════════════════════
    #  SCENARIO 2: DECLINE — T3b Augmentation with real LLM
    # ═══════════════════════════════════════════════════════════

    out.banner("SCENARIO 2: DECLINE — T3b Augmentation (LLM Calls)")

    query_2 = "How does Tesla's vertical integration strategy affect its competitive position in the EV market?"

    # ── Stage 0: LLM Grounding ──
    out.section("Stage 0: LLM Grounding (Gemini 2.5 Pro)")

    out.input_box("Grounding Call Inputs (Scenario 2)", (
        f"query:\n"
        f"  \"{query_2}\"\n"
        f"\n"
        f"ontology_snippet: (same as Scenario 1, {len(ontology_snippet)} chars)\n"
        f"domain_type: \"{augmented_ks.domain_type.value}\""
    ))

    t_g2 = time.time()
    g2 = None
    try:
        g2 = grounder(
            query=query_2,
            ontology_snippet=ontology_snippet,
            domain_type=augmented_ks.domain_type.value,
        )
        grounding_2 = GroundingResult(
            predicates=g2.predicates if g2.predicates else [],
            confidence=0.65,
        )
    except Exception as e:
        out.print(f"  Grounding failed: {e}")
        grounding_2 = GroundingResult(
            predicates=["vertical_integration", "ev_market_position", "manufacturing_efficiency"],
            confidence=0.60,
        )
    t_g2_done = time.time()

    out.output_box("Grounding Result (Scenario 2)", (
        f"Time: {t_g2_done - t_g2:.1f}s\n"
        f"\n"
        f"reasoning:\n"
        f"  {getattr(g2, 'reasoning', 'N/A') if g2 else 'N/A'}\n"
        f"\n"
        f"predicates:\n"
        f"  {json.dumps(grounding_2.predicates, indent=2)}\n"
        f"\n"
        f"relevant_vyaptis:\n"
        f"  {json.dumps(getattr(g2, 'relevant_vyaptis', []) if g2 else [], indent=2)}\n"
        f"\n"
        f"confidence: {grounding_2.confidence}"
    ))

    # ── Stage 1: Coverage Analysis ──
    out.section("Stage 1: Semantic Coverage Analysis")

    coverage_2 = coverage_analyzer.analyze(grounding_2.predicates)

    out.processing(
        f"For each predicate:\n"
        + "\n".join(
            f"  '{p}' → match_type={coverage_2.match_details.get(p, 'UNMATCHED')}"
            for p in grounding_2.predicates
        )
        + f"\n\nCoverage ratio = {len(coverage_2.matched_predicates)} / "
        f"{len(grounding_2.predicates)} = {coverage_2.coverage_ratio:.2f}"
    )

    out.output_box("Coverage Result (Scenario 2)", (
        f"coverage_ratio: {coverage_2.coverage_ratio:.2f}\n"
        f"decision: {coverage_2.decision}\n"
        f"matched_predicates: {coverage_2.matched_predicates}\n"
        f"unmatched_predicates: {coverage_2.unmatched_predicates}\n"
        f"match_details: {json.dumps(coverage_2.match_details, indent=2)}\n"
        f"relevant_vyaptis: {coverage_2.relevant_vyaptis}"
    ))

    # ── Stage 2: Routing ──
    out.section("Stage 2: Coverage-Based Routing")
    out.print(f"  Decision: {coverage_2.decision}")

    active_ks_2 = augmented_ks
    aug_result_2 = None

    if coverage_2.decision == "DECLINE":
        out.print(f"  Route: → T3b Augmentation Pipeline (2 LLM calls)")

        # ── T3b Augmentation ──
        out.section("Stage 2b: T3b Augmentation Pipeline")

        # Build and show inputs
        framework_summary = augmentation_pipeline._build_framework_summary()

        out.input_box("ScoreFrameworkApplicability Inputs", (
            f"Signature: ScoreFrameworkApplicability(dspy.Signature)\n"
            f"  Docstring: 'Score how applicable the domain's reasoning\n"
            f"    framework is to a query. Consider whether the domain's\n"
            f"    vyaptis and conceptual axes can meaningfully analyze\n"
            f"    this query. Score 0.0-1.0 where >= 0.4 means\n"
            f"    the framework can contribute.'\n"
            f"\n"
            f"query:\n"
            f"  \"{query_2}\"\n"
            f"\n"
            f"interpreted_intent:\n"
            f"  \"{query_2}\"\n"
            f"\n"
            f"framework_summary:\n"
            f"  {framework_summary}\n"
            f"\n"
            f"domain_type: \"{augmented_ks.domain_type.value}\""
        ))

        t_aug = time.time()
        try:
            aug_result_2 = augmentation_pipeline(
                query=query_2,
                interpreted_intent=query_2,
                coverage_result=coverage_2,
            )
            t_aug_done = time.time()

            out.output_box("T3b Augmentation Result", (
                f"Time: {t_aug_done - t_aug:.1f}s\n"
                f"\n"
                f"augmented: {aug_result_2.augmented}\n"
                f"framework_score: {aug_result_2.framework_score:.2f}\n"
                f"reason: {aug_result_2.reason}\n"
                f"new_vyaptis: {len(aug_result_2.new_vyaptis)}\n"
                f"validation_warnings: {aug_result_2.validation_warnings}\n"
            ))

            if aug_result_2.augmented and aug_result_2.new_vyaptis:
                out.print("  Generated vyaptis:")
                for nv in aug_result_2.new_vyaptis:
                    out.print(f"\n    {nv.id}: {nv.name}")
                    out.print(f"      statement: {nv.statement}")
                    out.print(f"      antecedents: {nv.antecedents}")
                    out.print(f"      consequent: {nv.consequent}")
                    out.print(f"      causal_status: {nv.causal_status.value}")
                    out.print(f"      epistemic_status: {nv.epistemic_status.value}")
                    out.print(f"      confidence: existence={nv.confidence.existence:.2f}, "
                              f"formulation={nv.confidence.formulation:.2f}")
                    out.print(f"      scope_conditions: {nv.scope_conditions}")
                    if nv.augmentation_metadata:
                        out.print(f"      origin: {nv.augmentation_metadata.origin.value}")
                        out.print(f"      template vyaptis: {nv.augmentation_metadata.framework_vyaptis_used}")

            if aug_result_2.augmented and aug_result_2.merged_kb:
                active_ks_2 = aug_result_2.merged_kb
                out.print(f"\n  Merged KB: {len(active_ks_2.vyaptis)} vyaptis")
            elif not aug_result_2.augmented:
                out.print(f"\n  Below threshold or out-of-domain → using base KB")
        except Exception as e:
            t_aug_done = time.time()
            out.print(f"  Augmentation failed ({t_aug_done - t_aug:.1f}s): {e}")
            import traceback
            traceback.print_exc()
    else:
        out.print(f"  Route: → T2 Compilation with augmented KB (coverage sufficient)")

    # ── Stage 3: T2 Compilation ──
    out.section("Stage 3: T2 Compilation (Scenario 2)")

    bare_preds_2 = [p.split("(")[0] for p in grounding_2.predicates]
    query_facts_2 = [
        {"predicate": p, "confidence": grounding_2.confidence, "sources": []}
        for p in bare_preds_2
    ]

    out.input_box("T2 Compilation Input (Scenario 2)", (
        f"KnowledgeStore: {len(active_ks_2.vyaptis)} vyaptis\n"
        f"Entity stripping:\n"
        + "\n".join(f"  {orig} → {bare}" for orig, bare in zip(grounding_2.predicates, bare_preds_2))
        + f"\n\nquery_facts:\n"
        + json.dumps(query_facts_2, indent=2)
    ))

    af_2 = compile_t2(active_ks_2, query_facts_2)

    out.output_box("ArgumentationFramework (Scenario 2)", (
        f"arguments: {len(af_2.arguments)}, attacks: {len(af_2.attacks)}\n"
        + "\n".join(
            f"\n  {aid}: {arg.conclusion}\n"
            f"    top_rule: {arg.top_rule or '[premise]'}\n"
            f"    tag: Tag(b={arg.tag.belief:.4f})\n"
            f"    depth: {arg.tag.derivation_depth}, pramana: {arg.tag.pramana_type.name}"
            + (f"\n    origin: {active_ks_2.vyaptis[arg.top_rule].augmentation_metadata.origin.value}"
               if arg.top_rule and active_ks_2.vyaptis.get(arg.top_rule)
               and active_ks_2.vyaptis[arg.top_rule].augmentation_metadata else "")
            for aid, arg in sorted(af_2.arguments.items())
            if not arg.conclusion.startswith("_")
        )
    ))

    # ── Contestation + Epistemic + Synthesis ──
    out.section("Stage 5: Contestation (Scenario 2)")
    vada_2 = cm.vada(af_2)
    labels_2 = af_2.labels

    out.output_box("Contestation Result (Scenario 2)", (
        "\n".join(
            f"  {aid}: {arg.conclusion} → {labels_2.get(aid, 'UNKNOWN').value}"
            for aid, arg in sorted(af_2.arguments.items())
            if not arg.conclusion.startswith("_")
        )
    ))

    out.section("Stage 6: Epistemic Status (Scenario 2)")
    conclusions_2 = set(a.conclusion for a in af_2.arguments.values() if not a.conclusion.startswith("_"))
    results_2 = {}
    for conc in sorted(conclusions_2):
        status, tag, args = af_2.get_epistemic_status(conc)
        if status:
            results_2[conc] = {"status": status, "tag": tag}

    out.output_box("Epistemic Status (Scenario 2)", (
        "\n".join(
            f"  {conc}: {info['status'].value} (b={info['tag'].belief:.4f}, "
            f"u={info['tag'].uncertainty:.4f})"
            for conc, info in sorted(results_2.items())
        ) or "  (no epistemic results)"
    ))

    out.section("Stages 7-9: Provenance / Uncertainty (Scenario 2)")
    uncertainty_2 = {}
    for conc, info in results_2.items():
        uq = compute_uncertainty_v4(info["tag"], grounding_2.confidence, conc, info["status"])
        uncertainty_2[conc] = uq

    out.output_box("Uncertainty (Scenario 2)", (
        "\n".join(
            f"  {conc}: total_conf={uq['total_confidence']:.4f}, "
            f"epistemic={uq['epistemic']['status']}"
            for conc, uq in sorted(uncertainty_2.items())
        ) or "  (no uncertainty data)"
    ))

    # Synthesis
    out.section("Stage 10: LLM Synthesis (Scenario 2)")

    accepted_str_2 = "\n".join(
        f"- {conc}: {info['status'].value} (belief={info['tag'].belief:.2f})"
        for conc, info in results_2.items()
        if info["status"] in (ES.ESTABLISHED, ES.HYPOTHESIS, ES.PROVISIONAL)
    ) or "No accepted conclusions."

    uq_str_2 = "\n".join(
        f"- {conc}: confidence={uq['total_confidence']:.2f}"
        for conc, uq in uncertainty_2.items()
    ) or "No uncertainty data."

    chunks_2 = t3a_retriever.retrieve(query_2, k=3)
    prose_2 = "\n\n".join(c.text for c in chunks_2[:3])

    out.input_box("Synthesis Call Inputs (Scenario 2)", (
        f"query:\n"
        f"  \"{query_2}\"\n"
        f"\n"
        f"accepted_arguments:\n"
        f"  {accepted_str_2}\n"
        f"\n"
        f"defeated_arguments:\n"
        f"  No defeated conclusions.\n"
        f"\n"
        f"uncertainty_report:\n"
        f"  {uq_str_2}\n"
        f"\n"
        f"retrieved_prose:\n"
        f"  {prose_2}"
    ))

    t_s2 = time.time()
    try:
        synth_2 = synthesizer(
            query=query_2,
            accepted_arguments=accepted_str_2,
            defeated_arguments="No defeated conclusions.",
            uncertainty_report=uq_str_2,
            retrieved_prose=prose_2,
        )
        t_s2_done = time.time()

        out.output_box("Synthesis Result (Scenario 2)", (
            f"Time: {t_s2_done - t_s2:.1f}s\n"
            f"\n"
            f"reasoning:\n"
            f"  {getattr(synth_2, 'reasoning', 'N/A')}\n"
            f"\n"
            f"response:\n"
            f"  {synth_2.response}\n"
            f"\n"
            f"sources_cited:\n"
            f"  {synth_2.sources_cited}"
        ))
    except Exception as e:
        t_s2_done = time.time()
        out.print(f"  Synthesis failed ({t_s2_done - t_s2:.1f}s): {e}")

    # ═══════════════════════════════════════════════════════════
    #  SCENARIO 3: Out-of-Domain — T3b Decline
    # ═══════════════════════════════════════════════════════════

    out.banner("SCENARIO 3: Out-of-Domain — T3b Decline")

    query_3 = "What is the best recipe for chocolate soufflé?"

    out.section("Stage 0: LLM Grounding (Gemini 2.5 Pro)")

    out.input_box("Grounding Call Inputs (Scenario 3)", (
        f"query:\n"
        f"  \"{query_3}\"\n"
        f"\n"
        f"ontology_snippet: (same as Scenarios 1-2, {len(ontology_snippet)} chars)\n"
        f"domain_type: \"{augmented_ks.domain_type.value}\""
    ))

    t_g3 = time.time()
    g3 = None
    try:
        g3 = grounder(
            query=query_3,
            ontology_snippet=ontology_snippet,
            domain_type=augmented_ks.domain_type.value,
        )
        grounding_3 = GroundingResult(
            predicates=g3.predicates if g3.predicates else [],
            confidence=0.3,
        )
    except Exception as e:
        out.print(f"  Grounding failed: {e}")
        grounding_3 = GroundingResult(
            predicates=["chocolate_preparation", "baking_technique"],
            confidence=0.2,
        )
    t_g3_done = time.time()

    out.output_box("Grounding Result (Scenario 3)", (
        f"Time: {t_g3_done - t_g3:.1f}s\n"
        f"\n"
        f"reasoning:\n"
        f"  {getattr(g3, 'reasoning', 'N/A') if g3 else 'N/A'}\n"
        f"\n"
        f"predicates:\n"
        f"  {json.dumps(grounding_3.predicates, indent=2)}\n"
        f"\n"
        f"relevant_vyaptis:\n"
        f"  {json.dumps(getattr(g3, 'relevant_vyaptis', []) if g3 else [], indent=2)}\n"
        f"\n"
        f"confidence: {grounding_3.confidence}"
    ))

    out.section("Stage 1: Coverage Analysis")
    coverage_3 = coverage_analyzer.analyze(grounding_3.predicates)

    out.processing(
        f"For each predicate:\n"
        + "\n".join(
            f"  '{p}' → match_type={coverage_3.match_details.get(p, 'UNMATCHED')}"
            for p in grounding_3.predicates
        )
        + f"\n\nCoverage ratio = {len(coverage_3.matched_predicates)} / "
        f"{max(len(grounding_3.predicates), 1)} = {coverage_3.coverage_ratio:.2f}"
    )

    out.output_box("Coverage Result (Scenario 3)", (
        f"coverage_ratio: {coverage_3.coverage_ratio:.2f}\n"
        f"decision: {coverage_3.decision}\n"
        f"matched: {coverage_3.matched_predicates}\n"
        f"unmatched: {coverage_3.unmatched_predicates}"
    ))

    if coverage_3.decision == "DECLINE":
        out.section("Stage 2: T3b Augmentation → Domain Check")

        framework_summary = augmentation_pipeline._build_framework_summary()
        out.input_box("ScoreFrameworkApplicability Inputs (Scenario 3)", (
            f"query: \"{query_3}\"\n"
            f"interpreted_intent: \"{query_3}\"\n"
            f"\n"
            f"framework_summary:\n"
            f"  {framework_summary}\n"
            f"\n"
            f"domain_type: \"{augmented_ks.domain_type.value}\"\n"
            f"\n"
            f"APPLICABILITY_THRESHOLD: {0.4}"
        ))

        t_a3 = time.time()
        try:
            aug_3 = augmentation_pipeline(
                query=query_3,
                interpreted_intent=query_3,
                coverage_result=coverage_3,
            )
            t_a3_done = time.time()

            out.output_box("T3b Domain Check Result (Scenario 3)", (
                f"Time: {t_a3_done - t_a3:.1f}s\n"
                f"\n"
                f"augmented: {aug_3.augmented}\n"
                f"framework_score: {aug_3.framework_score:.2f}\n"
                f"reason: {aug_3.reason}\n"
                f"new_vyaptis: {len(aug_3.new_vyaptis)}\n"
                f"\n"
                f"Decision: framework_score ({aug_3.framework_score:.2f}) "
                f"{'<' if aug_3.framework_score < 0.4 else '>='} "
                f"threshold ({0.4})\n"
                f"→ {'DECLINE (out-of-domain)' if not aug_3.augmented else 'AUGMENT'}"
            ))

            if not aug_3.augmented:
                out.print(f"\n  DECLINE RESPONSE:")
                out.print(f"  'This query falls outside my domain's reasoning framework.'")
                out.print(f"  '{aug_3.reason}'")
        except Exception as e:
            t_a3_done = time.time()
            out.print(f"  Augmentation failed ({t_a3_done - t_a3:.1f}s): {e}")

    # ═══════════════════════════════════════════════════════════
    #  SUMMARY
    # ═══════════════════════════════════════════════════════════

    out.banner("PIPELINE SUMMARY")
    total = time.time() - t0

    out.print(f"  Total wall time: {total:.1f}s")
    out.print(f"  LM: gemini-2.5-pro")
    out.print(f"  KB: {len(augmented_ks.vyaptis)} vyaptis ({base_count} base + {fine_count} fine-grained)")
    out.print(f"  Predicate vocabulary: {len(aug_preds)} predicates")

    out.print(f"\n  Scenario 1 (FULL coverage):")
    out.print(f"    Query: \"{query_1}\"")
    out.print(f"    Coverage: {coverage_1.coverage_ratio:.2f} → {coverage_1.decision}")
    out.print(f"    Arguments: {len(af_1.arguments)}, Attacks: {len(af_1.attacks)}")
    out.print(f"    LLM calls: grounding (1) + synthesis (1) = 2")

    out.print(f"\n  Scenario 2 (in-domain, coverage {coverage_2.decision}):")
    out.print(f"    Query: \"{query_2}\"")
    out.print(f"    Coverage: {coverage_2.coverage_ratio:.2f} → {coverage_2.decision}")
    if aug_result_2:
        out.print(f"    T3b: score={aug_result_2.framework_score:.2f}, "
                  f"augmented={aug_result_2.augmented}, "
                  f"new_vyaptis={len(aug_result_2.new_vyaptis)}")
    out.print(f"    Arguments: {len(af_2.arguments)}, Attacks: {len(af_2.attacks)}")
    out.print(f"    LLM calls: grounding (1) + T3b (0-2) + synthesis (1)")

    out.print(f"\n  Scenario 3 (out-of-domain):")
    out.print(f"    Query: \"{query_3}\"")
    out.print(f"    Coverage: {coverage_3.coverage_ratio:.2f} → {coverage_3.decision}")
    out.print(f"    LLM calls: grounding (1) + T3b domain check (1) = 2")

    # Stage reference table
    out.print(f"\n  Stage Reference:")
    out.print(f"  {'Stage':<8} {'Name':<30} {'LLM?':<6} {'Processing'}")
    out.print(f"  {'─'*8} {'─'*30} {'─'*6} {'─'*30}")
    out.print(f"  {'0':<8} {'LLM Grounding':<30} {'Yes':<6} ChainOfThought(GroundQuery)")
    out.print(f"  {'1':<8} {'Coverage Analysis':<30} {'No':<6}  3-layer match (exact/syn/token)")
    out.print(f"  {'2':<8} {'Coverage Routing':<30} {'No':<6}  FULL/PARTIAL/DECLINE threshold")
    out.print(f"  {'2b':<8} {'T3b Augmentation':<30} {'Yes':<6} ScoreApplicability + Generate")
    out.print(f"  {'3':<8} {'T2 Compilation':<30} {'No':<6}  Forward chain + attacks")
    out.print(f"  {'4':<8} {'T3a Retrieval':<30} {'No':<6}  Embedding/fallback retrieval")
    out.print(f"  {'5':<8} {'Contestation':<30} {'No':<6}  Grounded semantics")
    out.print(f"  {'6':<8} {'Epistemic Status':<30} {'No':<6}  Tag threshold classification")
    out.print(f"  {'7':<8} {'Provenance':<30} {'No':<6}  Tag field extraction")
    out.print(f"  {'8':<8} {'Uncertainty':<30} {'No':<6}  3-way decomposition")
    out.print(f"  {'9':<8} {'Violations':<30} {'No':<6}  Attack graph scan")
    out.print(f"  {'10':<8} {'LLM Synthesis':<30} {'Yes':<6} ChainOfThought(SynthesizeResponse)")

    # Save output
    trace_path = os.path.join(
        os.path.dirname(__file__), "..",
        "docs", f"run_trace_gemini_full_{time.strftime('%Y-%m-%d')}.md"
    )
    out.save(trace_path)
    out.print(f"\n  Full trace saved to: {trace_path}")


if __name__ == "__main__":
    main()
