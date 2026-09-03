# anvikshiki_v4/engine_v4.py
"""
The Ānvīkṣikī Engine v4 — Argumentation over Provenance Semirings.

Supports two entry points:
  forward()               — original path (no coverage routing)
  forward_with_coverage() — coverage-based routing (FULL/PARTIAL/DECLINE)
"""

from typing import Optional

import dspy
from .advisories import Advisory, as_wire, unestablished_scope_advisories
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
    framework_support: str = dspy.InputField(
        desc=(
            "Whether the argumentation framework derived anything at all. "
            "When it says NONE, no rule fired and no conclusion is supported "
            "by the knowledge base — any answer is general knowledge, not "
            "derived reasoning, and must not be presented as the latter."))

    response: str = dspy.OutputField(
        desc="Calibrated response with epistemic qualification. "
             "Use hedging language for HYPOTHESIS/PROVISIONAL claims. "
             "Explicitly flag CONTESTED and OPEN items.")
    sources_cited: list[str] = dspy.OutputField(
        desc="Source IDs actually used in the response")


NO_DERIVATION_NOTICE = (
    "Note: my knowledge base did not derive this. No rule fired, so nothing "
    "below is supported by the framework's own reasoning or its cited "
    "sources — treat it as general knowledge rather than as a grounded "
    "conclusion."
)


def derivation_state(af, labels) -> dict:
    """What the argumentation framework actually derived, as a state.

    Both answering paths need this and both used to lack it. `accepted_str`
    fell back to the string "No accepted conclusions." and the synthesizer was
    asked the question anyway — which it answered fluently and without a
    hedge, producing confident prose at exactly the moment the engine had
    nothing. The only outward signal was an empty `sources` list, which reads
    as "no citations needed" rather than "no reasoning happened", and nothing
    was reading it.

    A premise is not a derivation, and that distinction is the whole content
    of this function. `extension_size` counts every argument labelled IN, and
    premises are arguments, so a query that derived nothing reported an
    extension of 3 — the facts handed in, counted back out. `extension_size`
    is left as it is because it is on the wire and typed downstream;
    `derived_count` here is the number that answers the question people were
    asking it.
    """
    if af.arguments and not labels:
        raise ValueError(
            "derivation_state called on an unlabelled framework: "
            f"{len(af.arguments)} arguments and no labels. Call "
            "af.compute_grounded() first. Without this guard the answer "
            "would be 'nothing was derived' — the framework's own silence "
            "read as a fact about the query, which is the defect this "
            "function exists to stop."
        )

    derived = sorted({
        a.conclusion for aid, a in af.arguments.items()
        if a.top_rule is not None
        and labels.get(aid) == Label.IN
        and not a.conclusion.startswith("_")
    })
    return {
        "rule_backed": bool(derived),
        "derived_conclusions": derived,
        "derived_count": len(derived),
        "premise_count": sum(
            1 for a in af.arguments.values()
            if a.top_rule is None and not a.conclusion.startswith("_")
        ),
    }


def collect_advisories(knowledge_store, af, labels, grounding) -> list[Advisory]:
    """Every advisory this answer carries, from both sides of the boundary.

    Two producers with two different views, joined here because this is the
    only place that holds both. The grounding pipeline saw the predicates and
    can say the query asserts an exclusion, or that a rule it routed to has
    decayed; the framework saw what actually fired and can say a rule
    concluded something with its declared scope never established.

    Both were computed before this function existed and neither was read. The
    grounding half was attached to a result whose only production consumers
    sit inside the `clarification_needed` branch it never reaches; the
    framework half had not been written, because there was nowhere to put it.
    """
    return list(grounding.advisories) + unestablished_scope_advisories(
        knowledge_store, af, labels
    )


NO_FRAMEWORK = {
    "rule_backed": False,
    "derived_conclusions": [],
    "derived_count": 0,
    "premise_count": 0,
}


def framework_support_line(derivation: dict) -> str:
    """The synthesizer's view of the same state."""
    if not derivation["rule_backed"]:
        return "NONE — no rule fired and no conclusion is supported"
    return (
        f"{derivation['derived_count']} derived conclusion(s): "
        f"{', '.join(derivation['derived_conclusions'])}"
    )


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


# ── Argumentation view for consumers ──

def af_view(af=None, status_by_conclusion: dict | None = None) -> dict:
    """Serialisable view of the argumentation framework: arguments, attacks, labels.

    The graph is the explanation — a consumer that receives a response without
    it has the engine's answer and none of its reasoning. Every return path
    therefore carries this view, empty rather than absent when no framework was
    built, because "no arguments" and "the field never arrived" are different
    facts and only one of them is true on a decline.

    Shapes match the API contract exactly: `is_strict` is reported as
    `rule_type`, `top_rule` as `vyapti_id`, and each attack is given a stable
    id, since attacks are a list with no identity of their own.

    `status_by_conclusion` supplies `epistemic_status`, which is the
    *conclusion's* — every argument concluding X reports X's, and None when
    the conclusion has none. Each argument additionally reports `status`, its
    own place in the lattice, which differs whenever the join over a
    conclusion's surviving arguments picked a different one.
    """
    if af is None:
        return {"arguments": {}, "attacks": [], "labels": {}}

    status_by_conclusion = status_by_conclusion or {}
    labels = af.labels

    arguments = {
        aid: {
            "id": aid,
            "conclusion": a.conclusion,
            "rule_type": "strict" if a.is_strict else "defeasible",
            "label": labels.get(aid, Label.UNDECIDED).value,
            "epistemic_status": (
                status_by_conclusion[a.conclusion].value
                if a.conclusion in status_by_conclusion else None
            ),
            # This argument's own place in the lattice — the meet of its top
            # rule and its sub-arguments. Distinct from `epistemic_status`
            # above, which is the conclusion's, and equal to it only for the
            # argument that won the join. Two arguments for one conclusion
            # can differ here, and that difference is the explanation for
            # why the conclusion landed where it did.
            "status": a.status.value,
            # Why the status is where it is, rather than only what it is. A
            # ceiling enforced internally and invisible externally is a
            # guarantee nobody benefits from.
            #
            # A list, because bounds tie routinely — an extracted rule
            # authored as a working hypothesis has `authored` and `origin`
            # both at HYPOTHESIS — and naming one of two tied constraints
            # misstates what would change if it were lifted. Empty is never
            # sent: `null` means the argument did not record it, which is a
            # different claim from "nothing constrains this".
            "status_bound_by": (
                list(a.status_bound_by)
                if a.status_bound_by is not None else None
            ),
            # None on an argument with no top rule, and rendered as such:
            # an asserted premise has no origin tier and makes no citation
            # claim, so showing it one would invent provenance.
            "origin": a.origin,
            "citation_tier": a.citation_tier,
            "tag": a.tag.to_dict(),
            "premises": sorted(a.premises),
            "vyapti_id": a.top_rule,
        }
        for aid, a in af.arguments.items()
    }

    attacks = [
        {
            "id": f"ATK{i:04d}",
            "attacker": atk.attacker,
            "target": atk.target,
            "attack_type": atk.attack_type,
            "hetvabhasa": atk.hetvabhasa,
        }
        for i, atk in enumerate(af.attacks)
    ]

    return {
        "arguments": arguments,
        "attacks": attacks,
        "labels": {aid: lbl.value for aid, lbl in labels.items()},
    }


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
                violations=[], advisories=as_wire(grounding.advisories),
                grounding_confidence=grounding.confidence,
                extension_size=0, derivation=dict(NO_FRAMEWORK), **af_view(),
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
        advisories = collect_advisories(self.ks, af, labels, grounding)
        derivation = derivation_state(af, labels)
        framework_derived_nothing = not derivation["rule_backed"]

        accepted_str = "\n".join(
            f"- {conc}: {info['status'].value} "
            f"(pramana={info['tag'].pramana_type.name}, "
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
            f"- {conc}: {uq['epistemic']['status']}"
            f"{', contested' if uq['aleatoric']['contested'] else ''}"
            for conc, uq in uncertainty.items()
        )

        response = self.synthesizer(
            query=query,
            accepted_arguments=accepted_str,
            defeated_arguments=defeated_str,
            uncertainty_report=uq_str,
            retrieved_prose="\n\n".join(retrieved_chunks[:5]),
            framework_support=framework_support_line(derivation),
        )

        # Prepended rather than requested. The instruction above tells the
        # model to declare the fallback and the model may comply, but a
        # guarantee that depends on the model complying is not a guarantee —
        # and this is the one sentence the reader most needs to be able to
        # rely on.
        response_text = response.response
        if framework_derived_nothing:
            response_text = f"{NO_DERIVATION_NOTICE}\n\n{response_text}"

        return dspy.Prediction(
            response=response_text,
            sources=response.sources_cited,
            derivation=derivation,
            uncertainty=uncertainty,
            provenance=provenance,
            violations=violations,
            advisories=as_wire(advisories),
            grounding_confidence=grounding.confidence,
            extension_size=sum(
                1 for lbl in labels.values() if lbl == Label.IN
            ),
            contestation=contestation_analysis,
            **af_view(af, {c: i["status"] for c, i in results.items()}),
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
                violations=[], advisories=as_wire(grounding.advisories),
                grounding_confidence=grounding.confidence,
                extension_size=0, derivation=dict(NO_FRAMEWORK),
                coverage=None, augmentation=None,
                contestation=None, **af_view(),
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
                    violations=[], advisories=as_wire(grounding.advisories),
                    grounding_confidence=grounding.confidence,
                    extension_size=0, derivation=dict(NO_FRAMEWORK),
                    coverage=coverage.model_dump(),
                    augmentation=augmentation,
                    contestation=None, **af_view(),
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
        #
        # Whether the framework derived anything is a state, not a sentence in
        # a prompt. It used to be neither: `accepted_str` fell back to the
        # string "No accepted conclusions." and the synthesizer was asked the
        # question anyway, which it answered fluently and without a hedge —
        # confident prose at exactly the moment the engine had nothing, with
        # an empty `sources` list as the only signal and no caller reading it.
        #
        # A premise is not a derivation. `extension_size` counts every
        # argument labelled IN and premises are arguments, so it reported 3
        # for a query that derived nothing — the facts handed in, counted back
        # out. It is left alone here because it is on the wire and typed
        # downstream; `derivation` below is the field to read instead.
        advisories = collect_advisories(active_ks, af, labels, grounding)
        derivation = derivation_state(af, labels)
        framework_derived_nothing = not derivation["rule_backed"]

        accepted_str = "\n".join(
            f"- {conc}: {info['status'].value} "
            f"(pramana={info['tag'].pramana_type.name}, "
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
            f"- {conc}: {uq['epistemic']['status']}"
            f"{', contested' if uq['aleatoric']['contested'] else ''}"
            for conc, uq in uncertainty.items()
        )

        response = self.synthesizer(
            query=query,
            accepted_arguments=accepted_str,
            defeated_arguments=defeated_str,
            uncertainty_report=uq_str,
            retrieved_prose="\n\n".join(retrieved_chunks[:5]),
            framework_support=framework_support_line(derivation),
        )

        # Prepended rather than requested. The instruction in the signature
        # tells the model to declare the fallback and the model may comply,
        # but a guarantee that depends on the model complying is not a
        # guarantee — and this is the one sentence the reader most needs to be
        # able to rely on.
        response_text = response.response
        if framework_derived_nothing:
            response_text = f"{NO_DERIVATION_NOTICE}\n\n{response_text}"

        return dspy.Prediction(
            response=response_text,
            sources=response.sources_cited,
            derivation=derivation,
            uncertainty=uncertainty,
            provenance=provenance,
            violations=violations,
            advisories=as_wire(advisories),
            grounding_confidence=grounding.confidence,
            extension_size=sum(
                1 for lbl in labels.values() if lbl == Label.IN
            ),
            contestation=contestation_analysis,
            coverage=coverage.model_dump(),
            augmentation=augmentation,
            **af_view(af, {c: i["status"] for c, i in results.items()}),
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
            # Phase 1 has no argumentation framework by construction, so the
            # honest value is NONE for every query it answers — this variant
            # exists to be the ungrounded baseline the others are measured
            # against, and saying so is the whole point of it.
            framework_support="NONE — Phase 1 runs without an argumentation framework",
        )
        # Normalize output to match Phase 2+ schema for downstream compatibility
        return dspy.Prediction(
            response=response.response,
            sources=getattr(response, "sources_cited", []) or [],
            uncertainty={},
            provenance={},
            violations=[],
            advisories=as_wire(grounding.advisories),
            grounding_confidence=grounding.confidence,
            extension_size=0,
            derivation=dict(NO_FRAMEWORK),
            contestation=None,
            coverage=None,
            augmentation=None,
            **af_view(),
        )
