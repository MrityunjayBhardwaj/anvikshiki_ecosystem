# anvikshiki_v4/engine_v4.py
"""
The Ānvīkṣikī Engine v4 — Argumentation over Provenance Semirings.
"""

import dspy
from .schema import KnowledgeStore
from .schema_v4 import EpistemicStatus, Label
from .t2_compiler_v4 import compile_t2
from .uncertainty import compute_uncertainty_v4
from .contestation import ContestationManager


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


def _synthesis_reward(args: dict, pred: dspy.Prediction) -> float:
    """Reward function for dspy.Refine.

    Weights aligned with calibration_metric_v4 in optimize.py:
      substantive response: 0.20, sources: 0.15, epistemic hedging: 0.20,
      hetvābhāsa warnings: 0.15, no overconfidence: 0.15, extension: 0.15
    """
    score = 0.0

    # 1. Non-empty, substantive response (matches metric criterion 1)
    if pred.response and len(pred.response) > 50:
        score += 0.2

    # 2. Sources cited (matches metric criterion 2)
    if pred.sources_cited and len(pred.sources_cited) > 0:
        score += 0.15

    # 3. Epistemic qualification language (matches metric criterion 4)
    hedges = ["established", "hypothesis", "provisional", "contested",
              "uncertain", "open question", "evidence suggests",
              "limited evidence"]
    if any(h in pred.response.lower() for h in hedges):
        score += 0.2

    # 4. Hetvābhāsa warnings when violations present (matches metric criterion 5)
    if "defeated" in args.get("defeated_arguments", "").lower():
        if any(w in pred.response.lower()
               for w in ["caveat", "however", "limitation", "exception"]):
            score += 0.15

    # 5. No overconfidence (matches metric criterion 6)
    if "certainly" not in pred.response.lower():
        score += 0.15

    # 6. Extension quality signal from input (matches metric criterion 3)
    if "No accepted conclusions" not in args.get("accepted_arguments", ""):
        score += 0.15

    return min(1.0, score)


# ── Engine ──

class AnvikshikiEngineV4(dspy.Module):
    """Complete v4 engine: argumentation over provenance semirings."""

    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        grounding_pipeline,  # GroundingPipeline from grounding.py
        contestation_mode: str = "vada",
    ):
        super().__init__()
        self.ks = knowledge_store
        self.grounding = grounding_pipeline
        self.contestation_mode = contestation_mode
        self.contestation_mgr = ContestationManager()

        self.synthesizer = dspy.Refine(
            module=dspy.ChainOfThought(SynthesizeResponse),
            N=3,
            reward_fn=_synthesis_reward,
            threshold=0.5,
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

        # STEP 3: Compute extension + contestation analysis
        contestation_analysis = None
        if self.contestation_mode == "jalpa":
            jalpa_result = self.contestation_mgr.jalpa(af, timeout_seconds=30.0)
            labels = (jalpa_result.preferred_extensions[0]
                      if jalpa_result.preferred_extensions
                      else af.compute_grounded())
            contestation_analysis = {
                "mode": "jalpa",
                "num_preferred": len(jalpa_result.preferred_extensions),
                "defensible_positions": jalpa_result.defensible_positions,
                "counter_arguments": jalpa_result.counter_arguments,
            }
        elif self.contestation_mode == "vitanda":
            vitanda_result = self.contestation_mgr.vitanda(
                af, timeout_seconds=60.0)
            labels = (vitanda_result.stable_extensions[0]
                      if vitanda_result.stable_extensions
                      else af.compute_grounded())
            contestation_analysis = {
                "mode": "vitanda",
                "num_stable": len(vitanda_result.stable_extensions),
                "vulnerabilities": {
                    c: len(atks) for c, atks
                    in vitanda_result.vulnerability_inventory.items()
                },
                "undefended": vitanda_result.undefended,
            }
        else:
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
