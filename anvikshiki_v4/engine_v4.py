# anvikshiki_v4/engine_v4.py
"""
The Ānvīkṣikī Engine v4 — Argumentation over Provenance Semirings.

Supports two entry points:
  forward()               — original path (no coverage routing)
  forward_with_coverage() — coverage-based routing (FULL/PARTIAL/DECLINE)
"""

from typing import Optional

import dspy
from .schema import KnowledgeStore
from .schema_v4 import EpistemicStatus, Label
from .t2_compiler_v4 import compile_t2
from .uncertainty import compute_uncertainty_v4
from .contestation import ContestationManager
from .coverage import CoverageResult, SemanticCoverageAnalyzer
from .kb_augmentation import AugmentationPipeline, AugmentationResult
from .t3a_retriever import T3aRetriever
from .engine_params import SynthesisParams, DEFAULT_PARAMS


# ── DSPy Signatures ──

class SynthesizeResponse(dspy.Signature):
    """Produce a calibrated response from argumentation results."""
    query: str = dspy.InputField()
    accepted_arguments: str = dspy.InputField(
        desc="Formatted list of accepted conclusions with epistemic status")
    defeated_arguments: str = dspy.InputField(
        desc="Formatted list of defeated conclusions with hetvābhāsa types")
    uncertainty_report: str = dspy.InputField(
        desc="Structured uncertainty decomposition")
    retrieved_prose: str = dspy.InputField(
        desc="Relevant text from the knowledge base")

    response: str = dspy.OutputField(
        desc="Calibrated response with epistemic qualification. "
             "Use hedging language for HYPOTHESIS/PROVISIONAL claims. "
             "Explicitly flag CONTESTED and OPEN items.")
    sources_cited: list[str] = dspy.OutputField(
        desc="Source IDs actually used in the response")


_DEFAULT_SYNTHESIS = DEFAULT_PARAMS.synthesis


def _synthesis_reward(
    args: dict,
    pred: dspy.Prediction,
    params: SynthesisParams = _DEFAULT_SYNTHESIS,
) -> float:
    """Reward function for dspy.Refine.

    Weights from engine_params.SynthesisParams (sum to 1.0):
      substantive response, sources, epistemic hedging,
      hetvābhāsa warnings, no overconfidence, extension quality.
    """
    score = 0.0

    # 1. Non-empty, substantive response
    if pred.response and len(pred.response) > params.min_response_length:
        score += params.reward_substantive

    # 2. Sources cited
    if pred.sources_cited and len(pred.sources_cited) > 0:
        score += params.reward_sources

    # 3. Epistemic qualification language
    hedges = ["established", "hypothesis", "provisional", "contested",
              "uncertain", "open question", "evidence suggests",
              "limited evidence"]
    if any(h in pred.response.lower() for h in hedges):
        score += params.reward_hedging

    # 4. Hetvābhāsa warnings when violations present
    if "defeated" in args.get("defeated_arguments", "").lower():
        if any(w in pred.response.lower()
               for w in ["caveat", "however", "limitation", "exception"]):
            score += params.reward_hetvabhasa_warning

    # 5. No overconfidence
    if "certainly" not in pred.response.lower():
        score += params.reward_no_overconfidence

    # 6. Extension quality signal from input
    if "No accepted conclusions" not in args.get("accepted_arguments", ""):
        score += params.reward_extension_quality

    return min(1.0, score)


# ── Engine ──

class AnvikshikiEngineV4(dspy.Module):
    """Complete v4 engine: argumentation over provenance semirings."""

    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        grounding_pipeline,  # GroundingPipeline from grounding.py
        coverage_analyzer: Optional[SemanticCoverageAnalyzer] = None,
        augmentation_pipeline: Optional[AugmentationPipeline] = None,
        t3a_retriever: Optional[T3aRetriever] = None,
        t2b_source_sections: Optional[dict[str, list[str]]] = None,
    ):
        super().__init__()
        self.ks = knowledge_store
        self.grounding = grounding_pipeline
        self.contestation_mgr = ContestationManager()

        # Coverage-based routing components (optional)
        self.coverage_analyzer = coverage_analyzer
        self.augmentation_pipeline = augmentation_pipeline
        self.t3a_retriever = t3a_retriever
        self.t2b_source_sections = t2b_source_sections or {}

        self.synthesizer = dspy.Refine(
            module=dspy.ChainOfThought(SynthesizeResponse),
            N=_DEFAULT_SYNTHESIS.refine_n,
            reward_fn=_synthesis_reward,
            threshold=_DEFAULT_SYNTHESIS.refine_threshold,
        )

    def forward(self, query: str, retrieved_chunks: list[str]):
        # STEP 1: Ground query
        grounding = self.grounding(query)
        if grounding.clarification_needed:
            return dspy.Prediction(
                response=f"Clarification needed: {grounding.warnings}",
                sources=[], uncertainty={}, provenance={},
                violations=[], grounding_confidence=grounding.confidence,
                extension_size=0,
            )

        # STEP 2: Build argumentation framework
        # Include source provenance from grounding when available
        grounding_sources = getattr(grounding, 'sources', []) or []
        query_facts = [
            {"predicate": p, "confidence": grounding.confidence,
             "sources": grounding_sources}
            for p in grounding.predicates
        ]
        af = compile_t2(self.ks, query_facts)

        # STEP 3: Compute grounded extension + vāda analysis
        # Always uses grounded semantics (polynomial, guaranteed termination).
        # Preferred/stable semantics (jalpa/vitanda) are NP/coNP-hard and
        # available via ContestationManager for offline analysis only.
        vada_result = self.contestation_mgr.vada(af)
        labels = af.labels  # vada already computed grounded
        contestation_analysis = {
            "mode": "vada",
            "open_questions": vada_result.open_questions,
            "suggested_evidence": vada_result.suggested_evidence,
        }

        # STEP 4: Derive epistemic status per conclusion
        conclusions = set(
            a.conclusion for a in af.arguments.values()
            if not a.conclusion.startswith("_")
        )
        results = {}
        for conc in conclusions:
            status, tag, args = af.get_epistemic_status(conc)
            if status is not None:
                results[conc] = {
                    "status": status, "tag": tag, "arguments": args,
                }

        # STEP 5: Extract provenance
        provenance = {}
        for conc, info in results.items():
            provenance[conc] = {
                "sources": sorted(info["tag"].source_ids),
                "pramana": info["tag"].pramana_type.name,
                "derivation_depth": info["tag"].derivation_depth,
                "trust": info["tag"].trust_score,
                "decay": info["tag"].decay_factor,
            }

        # STEP 6: Uncertainty decomposition
        uncertainty = {}
        for conc, info in results.items():
            uncertainty[conc] = compute_uncertainty_v4(
                info["tag"], grounding.confidence,
                conc, info["status"],
            )

        # STEP 7: Collect defeated arguments (hetvābhāsas)
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

        # STEP 8: Synthesize response
        accepted_str = "\n".join(
            f"- {conc}: {info['status'].value} "
            f"(belief={info['tag'].belief:.2f}, "
            f"sources={sorted(info['tag'].source_ids)})"
            for conc, info in results.items()
            if info["status"] in (
                EpistemicStatus.ESTABLISHED, EpistemicStatus.HYPOTHESIS,
                EpistemicStatus.PROVISIONAL,
            )
        ) or "No accepted conclusions."

        defeated_str = "\n".join(
            f"- {v['target_conclusion']}: defeated by {v['hetvabhasa']} "
            f"({v['type']})"
            for v in violations
        ) or "No defeated conclusions."

        uq_str = "\n".join(
            f"- {conc}: confidence={uq['total_confidence']:.2f}, "
            f"epistemic={uq['epistemic']['status']}"
            for conc, uq in uncertainty.items()
        )

        response = self.synthesizer(
            query=query,
            accepted_arguments=accepted_str,
            defeated_arguments=defeated_str,
            uncertainty_report=uq_str,
            retrieved_prose="\n\n".join(retrieved_chunks[:5]),
        )

        return dspy.Prediction(
            response=response.response,
            sources=response.sources_cited,
            uncertainty=uncertainty,
            provenance=provenance,
            violations=violations,
            grounding_confidence=grounding.confidence,
            extension_size=sum(
                1 for lbl in labels.values() if lbl == Label.IN
            ),
            contestation=contestation_analysis,
        )

    def forward_with_coverage(
        self,
        query: str,
        interpreted_intent: str = "",
    ) -> dspy.Prediction:
        """
        Coverage-based routing entry point.

        Flow:
          1. Ground query → predicates
          2. Coverage check (base + fine-grained KB)
          3. Route:
             FULL/PARTIAL → compile_t2(KB, facts) + T3a retrieval → synthesis
             DECLINE + in-domain → T3b augmentation → merge → compile_t2 + T3a → synthesis
             DECLINE + out-of-domain → decline response
          4. T3a retrieval runs in parallel with T2 inference
        """
        # STEP 1: Ground query
        grounding = self.grounding(query)
        if grounding.clarification_needed:
            return dspy.Prediction(
                response=f"Clarification needed: {grounding.warnings}",
                sources=[], uncertainty={}, provenance={},
                violations=[], grounding_confidence=grounding.confidence,
                extension_size=0, coverage=None, augmentation=None,
            )

        # STEP 2: Coverage analysis
        coverage = None
        if self.coverage_analyzer:
            coverage = self.coverage_analyzer.analyze(grounding.predicates)
        else:
            # No coverage analyzer → treat as FULL coverage (legacy path)
            coverage = CoverageResult(
                coverage_ratio=1.0,
                matched_predicates=grounding.predicates,
                decision="FULL",
            )

        # STEP 3: Route based on coverage
        active_ks = self.ks
        augmentation = None

        if coverage.decision == "DECLINE" and self.augmentation_pipeline:
            # T3b: generate augmentation predicates
            aug_result = self.augmentation_pipeline(
                query=query,
                interpreted_intent=interpreted_intent or query,
                coverage_result=coverage,
            )
            augmentation = {
                "augmented": aug_result.augmented,
                "reason": aug_result.reason,
                "framework_score": aug_result.framework_score,
                "new_vyapti_count": len(aug_result.new_vyaptis),
                "warnings": aug_result.validation_warnings,
            }

            if aug_result.augmented and aug_result.merged_kb:
                active_ks = aug_result.merged_kb
            elif not aug_result.augmented:
                # Out-of-domain: decline
                return dspy.Prediction(
                    response=(
                        f"This query falls outside my domain's reasoning framework. "
                        f"{aug_result.reason}"
                    ),
                    sources=[], uncertainty={}, provenance={},
                    violations=[], grounding_confidence=grounding.confidence,
                    extension_size=0, coverage=coverage.model_dump(),
                    augmentation=augmentation,
                )

        # STEP 4: Build argumentation framework with active KB
        grounding_sources = getattr(grounding, 'sources', []) or []
        query_facts = [
            {"predicate": p, "confidence": grounding.confidence,
             "sources": grounding_sources}
            for p in grounding.predicates
        ]
        af = compile_t2(active_ks, query_facts)

        # STEP 5: T3a retrieval (parallel with T2 — no dependency)
        retrieved_chunks: list[str] = []
        if self.t3a_retriever:
            # Cross-link: boost sections whose predicates were activated
            activated_sections: dict[str, list[str]] = {}
            for vid in coverage.relevant_vyaptis:
                if vid in self.t2b_source_sections:
                    activated_sections[vid] = self.t2b_source_sections[vid]

            if activated_sections:
                t3a_chunks = self.t3a_retriever.retrieve_for_predicates(
                    activated_sections, query, k=5
                )
            else:
                t3a_chunks = self.t3a_retriever.retrieve(query, k=5)

            retrieved_chunks = [c.text for c in t3a_chunks]

        # STEP 6: Compute grounded extension + vāda analysis
        vada_result = self.contestation_mgr.vada(af)
        labels = af.labels
        contestation_analysis = {
            "mode": "vada",
            "open_questions": vada_result.open_questions,
            "suggested_evidence": vada_result.suggested_evidence,
        }

        # STEP 7: Derive epistemic status, provenance, uncertainty
        conclusions = set(
            a.conclusion for a in af.arguments.values()
            if not a.conclusion.startswith("_")
        )
        results = {}
        for conc in conclusions:
            status, tag, args = af.get_epistemic_status(conc)
            if status is not None:
                results[conc] = {
                    "status": status, "tag": tag, "arguments": args,
                }

        provenance = {}
        for conc, info in results.items():
            provenance[conc] = {
                "sources": sorted(info["tag"].source_ids),
                "pramana": info["tag"].pramana_type.name,
                "derivation_depth": info["tag"].derivation_depth,
                "trust": info["tag"].trust_score,
                "decay": info["tag"].decay_factor,
            }

        uncertainty = {}
        for conc, info in results.items():
            uncertainty[conc] = compute_uncertainty_v4(
                info["tag"], grounding.confidence,
                conc, info["status"],
            )

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

        # STEP 8: Synthesize
        accepted_str = "\n".join(
            f"- {conc}: {info['status'].value} "
            f"(belief={info['tag'].belief:.2f}, "
            f"sources={sorted(info['tag'].source_ids)})"
            for conc, info in results.items()
            if info["status"] in (
                EpistemicStatus.ESTABLISHED, EpistemicStatus.HYPOTHESIS,
                EpistemicStatus.PROVISIONAL,
            )
        ) or "No accepted conclusions."

        defeated_str = "\n".join(
            f"- {v['target_conclusion']}: defeated by {v['hetvabhasa']} "
            f"({v['type']})"
            for v in violations
        ) or "No defeated conclusions."

        uq_str = "\n".join(
            f"- {conc}: confidence={uq['total_confidence']:.2f}, "
            f"epistemic={uq['epistemic']['status']}"
            for conc, uq in uncertainty.items()
        )

        response = self.synthesizer(
            query=query,
            accepted_arguments=accepted_str,
            defeated_arguments=defeated_str,
            uncertainty_report=uq_str,
            retrieved_prose="\n\n".join(retrieved_chunks[:5]),
        )

        return dspy.Prediction(
            response=response.response,
            sources=response.sources_cited,
            uncertainty=uncertainty,
            provenance=provenance,
            violations=violations,
            grounding_confidence=grounding.confidence,
            extension_size=sum(
                1 for lbl in labels.values() if lbl == Label.IN
            ),
            contestation=contestation_analysis,
            coverage=coverage.model_dump(),
            augmentation=augmentation,
        )


# ── Phase 1 Variant: LLM Only ──

class AnvikshikiEngineV4Phase1(dspy.Module):
    """Phase 1: LLM-only reasoning without argumentation framework."""

    def __init__(self, knowledge_store, grounding_pipeline):
        super().__init__()
        self.ks = knowledge_store
        self.grounding = grounding_pipeline
        self.reasoner = dspy.ChainOfThought(SynthesizeResponse)

    def forward(self, query: str, retrieved_chunks: list[str]):
        grounding = self.grounding(query)
        response = self.reasoner(
            query=query,
            accepted_arguments=f"Predicates: {grounding.predicates}",
            defeated_arguments="Phase 1: no argumentation framework",
            uncertainty_report=f"Grounding confidence: {grounding.confidence}",
            retrieved_prose="\n\n".join(retrieved_chunks[:5]),
        )
        # Normalize output to match Phase 2+ schema for downstream compatibility
        return dspy.Prediction(
            response=response.response,
            sources=getattr(response, "sources_cited", []) or [],
            uncertainty={},
            provenance={},
            violations=[],
            grounding_confidence=grounding.confidence,
            extension_size=0,
            contestation=None,
        )
