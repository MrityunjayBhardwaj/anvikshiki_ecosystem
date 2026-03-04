"""
Stage F: Human-in-the-Loop Review for the Predicate Extraction Pipeline.

Renders proposed vyaptis as YAML diffs, collects accept/reject/modify decisions,
and applies them to produce the final approved KnowledgeStore.

Usage (CLI):
    python -m anvikshiki_v4.extraction_hitl \
        --kb anvikshiki_v4/data/business_expert.yaml \
        --proposed extraction_output.yaml \
        --output approved_kb.yaml

Usage (programmatic):
    from anvikshiki_v4.extraction_hitl import HITLReviewer

    reviewer = HITLReviewer(original_ks, augmented_ks, stage_d, validation)
    approved_ks = reviewer.review_interactive()
"""

from __future__ import annotations

import sys
from typing import Optional

import yaml

from .extraction_schema import (
    ProposedVyapti,
    ReviewDecision,
    ReviewItem,
    StageDOutput,
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


# ─── YAML Rendering ──────────────────────────────────────────


def _vyapti_to_yaml_dict(v: ProposedVyapti) -> dict:
    """Convert a ProposedVyapti to a YAML-serializable dict."""
    return {
        "id": v.id,
        "name": v.name,
        "statement": v.statement,
        "causal_status": v.causal_status,
        "antecedents": v.antecedents,
        "consequent": v.consequent,
        "scope_conditions": v.scope_conditions,
        "scope_exclusions": v.scope_exclusions,
        "confidence": {
            "existence": v.confidence_existence,
            "formulation": v.confidence_formulation,
            "evidence": v.evidence_type,
        },
        "epistemic_status": v.epistemic_status,
        "decay_risk": v.decay_risk,
        "sources": v.sources,
        "parent_vyapti": v.parent_vyapti,
    }


def render_vyapti_diff(v: ProposedVyapti, index: int, total: int) -> str:
    """Render a single proposed vyapti as a readable diff block."""
    lines = [
        f"{'=' * 60}",
        f"  Proposed Vyapti {index}/{total}: {v.id}",
        f"{'=' * 60}",
        "",
    ]

    d = _vyapti_to_yaml_dict(v)
    yaml_str = yaml.dump(d, default_flow_style=False, sort_keys=False)
    for line in yaml_str.strip().split("\n"):
        lines.append(f"  + {line}")

    lines.append("")

    if v.parent_vyapti:
        lines.append(f"  Parent: {v.parent_vyapti}")

    lines.append(
        f"  Confidence: existence={v.confidence_existence:.2f}, "
        f"formulation={v.confidence_formulation:.2f}"
    )
    lines.append(f"  Epistemic: {v.epistemic_status}")
    lines.append("")

    return "\n".join(lines)


def render_validation_summary(validation: ValidationResult) -> str:
    """Render validation results as a summary block."""
    lines = [
        "Validation Summary:",
        f"  Valid: {validation.is_valid}",
        f"  Coverage ratio: {validation.coverage_ratio:.1%}",
    ]
    if validation.cycle_errors:
        lines.append(f"  Cycle errors: {len(validation.cycle_errors)}")
        for err in validation.cycle_errors[:3]:
            lines.append(f"    - {err}")
    if validation.orphan_predicates:
        lines.append(
            f"  Orphan predicates: {len(validation.orphan_predicates)}"
        )
        for p in validation.orphan_predicates[:5]:
            lines.append(f"    - {p}")
    if validation.datalog_errors:
        lines.append(f"  Datalog errors: {len(validation.datalog_errors)}")
        for err in validation.datalog_errors[:3]:
            lines.append(f"    - {err}")
    return "\n".join(lines)


# ─── Review Logic ─────────────────────────────────────────────


class HITLReviewer:
    """Human-in-the-loop reviewer for proposed vyaptis."""

    def __init__(
        self,
        original_ks: KnowledgeStore,
        augmented_ks: KnowledgeStore,
        stage_d: StageDOutput,
        validation: ValidationResult,
    ):
        self.original_ks = original_ks
        self.augmented_ks = augmented_ks
        self.stage_d = stage_d
        self.validation = validation
        self.review_items: list[ReviewItem] = []

        all_proposed = stage_d.new_vyaptis + stage_d.refinement_vyaptis
        for v in all_proposed:
            self.review_items.append(
                ReviewItem(vyapti=v, validation=validation)
            )

    def review_interactive(self, output: Optional[object] = None) -> KnowledgeStore:
        """Run interactive review, printing to stdout.

        Returns the final approved KnowledgeStore.
        """
        out = output or sys.stdout
        total = len(self.review_items)

        _write(out, f"\nPredicate Extraction Review: {total} proposed vyaptis\n")
        _write(out, render_validation_summary(self.validation))
        _write(out, "\n")

        for i, item in enumerate(self.review_items, 1):
            _write(out, render_vyapti_diff(item.vyapti, i, total))
            _write(out, "  [a]ccept  [r]eject  [m]odify  [q]uit\n")
            _write(out, "  Decision: ")

            try:
                choice = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                _write(out, "\nReview aborted.\n")
                break

            if choice.startswith("a"):
                item.decision = ReviewDecision.ACCEPT
                _write(out, "  -> Accepted\n\n")
            elif choice.startswith("r"):
                item.decision = ReviewDecision.REJECT
                _write(out, "  -> Rejected\n\n")
            elif choice.startswith("m"):
                item.decision = ReviewDecision.MODIFY
                _write(out, "  Notes (press Enter when done): ")
                try:
                    notes = input().strip()
                    item.reviewer_notes = notes
                except (EOFError, KeyboardInterrupt):
                    pass
                _write(out, "  -> Marked for modification\n\n")
            elif choice.startswith("q"):
                _write(out, "\nReview ended early.\n")
                break
            else:
                _write(out, "  -> Skipped (no valid input)\n\n")

        return self.apply_decisions()

    def review_batch(
        self, decisions: dict[str, ReviewDecision]
    ) -> KnowledgeStore:
        """Apply batch decisions programmatically.

        Args:
            decisions: vyapti_id -> ReviewDecision mapping
        """
        for item in self.review_items:
            if item.vyapti.id in decisions:
                item.decision = decisions[item.vyapti.id]
        return self.apply_decisions()

    def apply_decisions(self) -> KnowledgeStore:
        """Build final KnowledgeStore from review decisions."""
        approved = self.original_ks.model_copy(deep=True)

        for item in self.review_items:
            if item.decision == ReviewDecision.ACCEPT:
                vyapti = self._proposed_to_vyapti(item.vyapti)
                if vyapti:
                    approved.vyaptis[item.vyapti.id] = vyapti
            elif item.decision == ReviewDecision.MODIFY:
                vyapti = self._proposed_to_vyapti(item.vyapti)
                if vyapti:
                    approved.vyaptis[item.vyapti.id] = vyapti

        return approved

    @staticmethod
    def _proposed_to_vyapti(proposed: ProposedVyapti) -> Optional[Vyapti]:
        """Convert ProposedVyapti to schema.Vyapti."""
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

        try:
            return Vyapti(
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
        except Exception:
            return None

    def summary(self) -> dict[str, int]:
        """Return counts by decision type."""
        counts = {"accepted": 0, "rejected": 0, "modified": 0, "pending": 0}
        for item in self.review_items:
            if item.decision == ReviewDecision.ACCEPT:
                counts["accepted"] += 1
            elif item.decision == ReviewDecision.REJECT:
                counts["rejected"] += 1
            elif item.decision == ReviewDecision.MODIFY:
                counts["modified"] += 1
            else:
                counts["pending"] += 1
        return counts


def _write(out: object, text: str) -> None:
    """Write text to output stream."""
    if hasattr(out, "write"):
        out.write(text)


# ─── Export Utilities ─────────────────────────────────────────


def export_proposed_yaml(
    stage_d: StageDOutput,
    output_path: str,
) -> None:
    """Export proposed vyaptis to a YAML file for offline review."""
    all_proposed = stage_d.new_vyaptis + stage_d.refinement_vyaptis
    data = {
        "proposed_vyaptis": [_vyapti_to_yaml_dict(v) for v in all_proposed],
        "new_count": len(stage_d.new_vyaptis),
        "refinement_count": len(stage_d.refinement_vyaptis),
    }
    with open(output_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def export_approved_yaml(
    knowledge_store: KnowledgeStore,
    output_path: str,
) -> None:
    """Export the approved KnowledgeStore to YAML."""
    data = knowledge_store.model_dump(mode="json")
    with open(output_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# ─── CLI Entry Point ─────────────────────────────────────────


def main() -> None:
    """CLI entry point for interactive HITL review."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Human-in-the-loop review for predicate extraction"
    )
    parser.add_argument(
        "--kb",
        required=True,
        help="Path to original knowledge store YAML",
    )
    parser.add_argument(
        "--proposed",
        required=True,
        help="Path to proposed vyaptis YAML (from export_proposed_yaml)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write approved KB YAML",
    )
    args = parser.parse_args()

    from .t2_compiler_v4 import load_knowledge_store

    original_ks = load_knowledge_store(args.kb)

    with open(args.proposed) as f:
        proposed_data = yaml.safe_load(f)

    proposed_vyaptis = []
    for vd in proposed_data.get("proposed_vyaptis", []):
        proposed_vyaptis.append(ProposedVyapti(**vd))

    stage_d = StageDOutput(
        new_vyaptis=proposed_vyaptis[: proposed_data.get("new_count", 0)],
        refinement_vyaptis=proposed_vyaptis[
            proposed_data.get("new_count", 0) :
        ],
    )

    validation = ValidationResult(is_valid=True)

    reviewer = HITLReviewer(original_ks, original_ks, stage_d, validation)
    approved = reviewer.review_interactive()

    export_approved_yaml(approved, args.output)
    summary = reviewer.summary()
    print(f"\nDone: {summary}")


if __name__ == "__main__":
    main()
