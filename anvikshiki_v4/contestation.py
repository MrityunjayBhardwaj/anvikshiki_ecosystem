# anvikshiki_v4/contestation.py
"""
Three Nyāya debate protocols as contestation modes.

Vāda   (honest inquiry)    → grounded semantics → polynomial
Jalpa  (adversarial debate) → preferred semantics → NP-hard (offline)
Vitaṇḍā (pure critique)     → stable semantics   → coNP-hard (offline)
"""

from dataclasses import dataclass, field
from typing import Optional
from .argumentation import MAX_UNDECIDED, ArgumentationFramework
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
    # Both None: too many undecided arguments to compute, said in preferred_note.
    preferred_extensions: Optional[list[dict[str, Label]]]
    defensible_positions: Optional[list[str]]  # IN some preferred, not IN grounded
    counter_arguments: dict[str, list[str]]  # conclusion → attack summaries
    preferred_note: str = ""


@dataclass
class VitandaResult:
    """Result of pure critique / audit (stable semantics)."""
    # None: too many undecided arguments to compute, said in stable_note.
    stable_extensions: Optional[list[dict[str, Label]]]
    vulnerability_inventory: dict[str, list[Attack]]  # conclusion → attacks
    undefended: list[str]  # Arguments with no counter-attack to their attackers
    stable_note: str = ""


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

    def jalpa(self, af: ArgumentationFramework) -> JalpaResult:
        """Adversarial disputation — preferred semantics (NP-hard, offline)."""
        grounded = af.compute_grounded()
        grounded_in = {
            aid for aid, lbl in grounded.items() if lbl == Label.IN
        }

        preferred = af.compute_preferred()

        # Find defensible positions: IN in some preferred but not in grounded.
        # Grounded UNDECIDED, always: what grounded labels OUT is in no
        # preferred extension.
        defensible = set()
        for ext in preferred or ():
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
            defensible_positions=None if preferred is None else sorted(defensible),
            counter_arguments=counter_args,
            preferred_note="" if preferred is not None else (
                f"preferred not computed: more than {MAX_UNDECIDED} "
                f"undecided arguments"
            ),
        )

    def vitanda(self, af: ArgumentationFramework) -> VitandaResult:
        """Pure critique — stable semantics (coNP-hard, offline)."""
        stable = af.compute_stable()

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
            stable_note="" if stable is not None else (
                f"stable not computed: more than {MAX_UNDECIDED} "
                f"undecided arguments"
            ),
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
        evidence: {conclusion, status, pramana_type, sources}
        """
        conclusion = evidence.get("conclusion", f"_contest_{target_arg_id}")
        pramana = PramanaType[evidence.get("pramana_type", "ANUMANA")]
        # A contestation states how strong its claim is, on the lattice.
        # HYPOTHESIS by default — which is where the previous default of
        # belief=0.7 landed under the old cutoffs, so this changes the
        # vocabulary rather than the behaviour.
        status = EpistemicStatus(evidence.get("status", "hypothesis"))

        tag = ProvenanceTag(
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
            status=status,
        )

        # For viruddha/satpratipaksa: add reverse attack too
        if contestation_type in ("viruddha", "satpratipaksa"):
            af.add_attack(Attack(
                attacker=target_arg_id, target=new_id,
                attack_type="rebutting", hetvabhasa=contestation_type,
            ))

        return new_id
