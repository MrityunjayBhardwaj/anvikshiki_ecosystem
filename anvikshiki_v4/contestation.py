# anvikshiki_v4/contestation.py
"""
Three Nyāya debate protocols as contestation modes.

Vāda   (honest inquiry)    → grounded semantics → polynomial
Jalpa  (adversarial debate) → preferred semantics → NP-hard (offline)
Vitaṇḍā (pure critique)     → stable semantics   → coNP-hard (offline)
"""

from dataclasses import dataclass, field
from .argumentation import ArgumentationFramework
from .schema_v4 import (
    ProvenanceTag, PramanaType, Label, Argument, Attack, EpistemicStatus
)


@dataclass
class VadaResult:
    """Result of cooperative inquiry (grounded semantics)."""
    accepted: dict  # conclusion → (status, tag, arguments)
    open_questions: list[str]  # UNDECIDED conclusions
    suggested_evidence: list[str]  # Predicates that could resolve UNDECIDED
    extension_size: int


@dataclass
class JalpaResult:
    """Result of adversarial stress-testing (preferred semantics)."""
    preferred_extensions: list[dict[str, Label]]
    defensible_positions: list[str]  # IN preferred but OUT grounded
    counter_arguments: dict[str, list[str]]  # conclusion → attack summaries


@dataclass
class VitandaResult:
    """Result of pure critique / audit (stable semantics)."""
    stable_extensions: list[dict[str, Label]]
    vulnerability_inventory: dict[str, list[Attack]]  # conclusion → attacks
    undefended: list[str]  # Arguments with no counter-attack to their attackers


class ContestationManager:
    """Manages the three debate protocols and user contestation input."""

    def vada(self, af: ArgumentationFramework) -> VadaResult:
        """Cooperative inquiry — grounded semantics (polynomial)."""
        labels = af.compute_grounded()

        accepted = {}
        open_questions = []
        conclusions = set(
            a.conclusion for a in af.arguments.values()
            if not a.conclusion.startswith("_")
        )

        for conc in conclusions:
            status, tag, args = af.get_epistemic_status(conc)
            if status is None:
                continue
            accepted[conc] = {
                "status": status, "tag": tag, "arguments": args,
            }
            if status == EpistemicStatus.OPEN:
                open_questions.append(conc)

        # Suggest evidence for UNDECIDED arguments
        suggested = []
        for arg in af.arguments.values():
            if labels.get(arg.id) == Label.UNDECIDED:
                for prem in arg.premises:
                    if prem not in suggested:
                        suggested.append(prem)

        return VadaResult(
            accepted=accepted,
            open_questions=open_questions,
            suggested_evidence=suggested,
            extension_size=sum(
                1 for lbl in labels.values() if lbl == Label.IN
            ),
        )

    def jalpa(
        self, af: ArgumentationFramework, timeout_seconds: float = 30.0
    ) -> JalpaResult:
        """Adversarial disputation — preferred semantics (NP-hard, offline)."""
        grounded = af.compute_grounded()
        grounded_in = {
            aid for aid, lbl in grounded.items() if lbl == Label.IN
        }

        preferred = af.compute_preferred(timeout_seconds=timeout_seconds)

        # Find defensible positions: IN in some preferred but OUT in grounded
        defensible = set()
        for ext in preferred:
            for aid, lbl in ext.items():
                if lbl == Label.IN and aid not in grounded_in:
                    arg = af.arguments[aid]
                    if not arg.conclusion.startswith("_"):
                        defensible.add(arg.conclusion)

        # Find counter-arguments for each accepted conclusion
        counter_args = {}
        for conc in set(
            a.conclusion for a in af.arguments.values()
            if not a.conclusion.startswith("_")
        ):
            attacks_on_conc = []
            for a in af.arguments.values():
                if a.conclusion != conc:
                    continue
                for atk in af._attacks_on.get(a.id, []):
                    attacker = af.arguments[atk.attacker]
                    attacks_on_conc.append(
                        f"{atk.hetvabhasa}: {attacker.conclusion} "
                        f"({atk.attack_type})"
                    )
            if attacks_on_conc:
                counter_args[conc] = attacks_on_conc

        return JalpaResult(
            preferred_extensions=preferred,
            defensible_positions=sorted(defensible),
            counter_arguments=counter_args,
        )

    def vitanda(
        self, af: ArgumentationFramework, timeout_seconds: float = 60.0
    ) -> VitandaResult:
        """Pure critique — stable semantics (coNP-hard, offline)."""
        stable = af.compute_stable(timeout_seconds=timeout_seconds)

        # Vulnerability inventory: all attacks per conclusion
        vuln = {}
        for a in af.arguments.values():
            if a.conclusion.startswith("_"):
                continue
            attacks = af._attacks_on.get(a.id, [])
            if attacks:
                vuln.setdefault(a.conclusion, []).extend(attacks)

        # Undefended arguments — compute grounded locally without
        # overwriting af.labels (which may reflect stable computation)
        saved_labels = af.labels.copy()
        grounded = af.compute_grounded()
        undefended = []
        for aid, lbl in grounded.items():
            if lbl != Label.IN:
                continue
            for atk_id in af._attackers_of.get(aid, []):
                if grounded.get(atk_id) != Label.OUT:
                    undefended.append(aid)
                    break
        af.labels = saved_labels  # Restore — vitanda shouldn't mutate AF state

        return VitandaResult(
            stable_extensions=stable,
            vulnerability_inventory=vuln,
            undefended=undefended,
        )

    def apply_contestation(
        self,
        af: ArgumentationFramework,
        contestation_type: str,
        target_arg_id: str,
        evidence: dict,
    ) -> str:
        """Apply a user contestation to the AF. Returns new argument ID.

        contestation_type: "asiddha" | "savyabhicara" | "viruddha"
                          | "satpratipaksa" | "badhita"
        evidence: {conclusion, belief, pramana_type, sources}
        """
        conclusion = evidence.get("conclusion", f"_contest_{target_arg_id}")
        belief = evidence.get("belief", 0.7)
        pramana = PramanaType[evidence.get("pramana_type", "ANUMANA")]

        # Clamp disbelief to prevent negative values (e.g. belief=0.95)
        disbelief = max(0.0, round(1.0 - belief - 0.1, 4))
        uncertainty = round(1.0 - belief - disbelief, 4)

        tag = ProvenanceTag(
            belief=belief,
            disbelief=disbelief,
            uncertainty=uncertainty,
            source_ids=frozenset(evidence.get("sources", [])),
            pramana_type=pramana,
            trust_score=evidence.get("trust", 0.8),
            decay_factor=1.0,
            derivation_depth=0,
        )

        attack_type_map = {
            "asiddha": "undermining",
            "savyabhicara": "undercutting",
            "viruddha": "rebutting",
            "satpratipaksa": "rebutting",
            "badhita": "rebutting",
        }

        new_id = af.add_counter_argument(
            conclusion=conclusion,
            tag=tag,
            attack_target=target_arg_id,
            attack_type=attack_type_map.get(contestation_type, "rebutting"),
            hetvabhasa=contestation_type,
        )

        # For viruddha/satpratipaksa: add reverse attack too
        if contestation_type in ("viruddha", "satpratipaksa"):
            af.add_attack(Attack(
                attacker=target_arg_id, target=new_id,
                attack_type="rebutting", hetvabhasa=contestation_type,
            ))

        return new_id
