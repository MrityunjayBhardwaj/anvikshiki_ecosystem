# anvikshiki_v4/schema_v4.py
"""Core data structures for the argumentation-based engine (v4)."""

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Optional, FrozenSet


# ─── ENUMS ──────────────────────────────────────────────────

class PramanaType(IntEnum):
    """Pramāṇa hierarchy — higher value = stronger epistemic channel."""
    UPAMANA = 1      # Analogy (weakest)
    SABDA = 2        # Testimony
    ANUMANA = 3      # Inference
    PRATYAKSA = 4    # Direct evidence (strongest)


class RuleType(Enum):
    STRICT = "strict"           # Definitional, structural — cannot be attacked
    DEFEASIBLE = "defeasible"   # Empirical, regulatory — can be undercut


class EpistemicStatus(Enum):
    """Derived from argumentation semantics — NOT hand-assigned."""
    ESTABLISHED = "established"     # IN grounded, strong tag
    HYPOTHESIS = "hypothesis"       # IN grounded, moderate tag
    PROVISIONAL = "provisional"     # IN grounded, from ordinary premises only
    OPEN = "open"                   # UNDECIDED in grounded extension
    CONTESTED = "contested"         # OUT in grounded, IN in preferred


class Label(Enum):
    IN = "in"           # Accepted — all attackers are OUT
    OUT = "out"         # Defeated — at least one attacker is IN and defeats
    UNDECIDED = "undecided"  # Neither accepted nor defeated


# ─── PROVENANCE TAG (SEMIRING) ───────────────────────────────

@dataclass(frozen=True)
class ProvenanceTag:
    """
    Annotation on arguments combining two structures:

    1. Subjective Logic opinion (b, d, u) — forms a semiring under
       tensor (Josang deduction) and oplus (cumulative fusion).
    2. Provenance metadata (pramana_type, trust_score, decay_factor,
       derivation_depth) — propagates via a monotone product lattice.

    These compose pragmatically, not algebraically.  Semiring axioms
    (associativity, distributivity) hold for (b,d,u) only.  Metadata
    uses consistent lattice ops: tensor=min, oplus=max for all fields.

    Invariant: belief + disbelief + uncertainty ≈ 1.0 (within tolerance 0.05)
    """
    belief: float = 1.0              # Evidence FOR [0,1]
    disbelief: float = 0.0           # Evidence AGAINST [0,1]
    uncertainty: float = 0.0         # Ignorance [0,1]
    source_ids: FrozenSet[str] = frozenset()
    pramana_type: PramanaType = PramanaType.ANUMANA
    trust_score: float = 1.0         # Source authority [0,1]
    decay_factor: float = 1.0        # Temporal freshness [0,1]
    derivation_depth: int = 0

    def __post_init__(self):
        total = self.belief + self.disbelief + self.uncertainty
        if abs(total - 1.0) > 0.05:
            raise ValueError(
                f"b + d + u must ≈ 1.0, got {total:.4f} "
                f"(b={self.belief}, d={self.disbelief}, u={self.uncertainty})"
            )

    def __repr__(self) -> str:
        return (
            f"Tag(b={self.belief:.2f}, d={self.disbelief:.2f}, "
            f"u={self.uncertainty:.2f}, src={len(self.source_ids)}, "
            f"pramana={self.pramana_type.name}, "
            f"trust={self.trust_score:.2f}, "
            f"decay={self.decay_factor:.2f}, "
            f"depth={self.derivation_depth})"
        )

    # ── Semiring Operations ──

    @staticmethod
    def tensor(a: 'ProvenanceTag', b: 'ProvenanceTag') -> 'ProvenanceTag':
        """⊗: Sequential composition (chaining through inference).

        Uses Josang's trust discounting operator (Josang 2016, §10.3).
        Preserves b+d+u=1 exactly (no normalization needed).
        Provably associative.  Left identity = one().
        Disbelief ATTENUATES: d_result = a.b * b.d ≤ b.d.
        (Fixes audit III-05, III-06, II-01)

        Only (b,d,u) use this formula.  Metadata fields propagate via
        a monotone product lattice (NOT part of semiring axioms).
        """
        # Josang trust discounting (§10.3): preserves b+d+u=1 exactly,
        # provably associative, disbelief attenuates (d = a.b * b.d ≤ b.d)
        new_b = a.belief * b.belief
        new_d = a.belief * b.disbelief
        new_u = a.disbelief + a.uncertainty + a.belief * b.uncertainty
        return ProvenanceTag(
            belief=new_b,
            disbelief=new_d,
            uncertainty=new_u,
            source_ids=a.source_ids | b.source_ids,
            # Metadata: monotone lattice, NOT part of semiring axioms
            pramana_type=PramanaType(min(a.pramana_type, b.pramana_type)),
            trust_score=min(a.trust_score, b.trust_score),
            decay_factor=min(a.decay_factor, b.decay_factor),
            derivation_depth=a.derivation_depth + b.derivation_depth,
        )

    @staticmethod
    def oplus(a: 'ProvenanceTag', b: 'ProvenanceTag') -> 'ProvenanceTag':
        """⊕: Parallel composition (accrual of independent arguments).

        Uses cumulative fusion (Josang 2016) — non-idempotent, so
        multiple independent arguments strengthen the conclusion.

        Source overlap: if sources overlap, interpolate between cumulative
        fusion (independent) and simple averaging (dependent) proportional
        to the overlap ratio.  (Fixes audit III-07)
        """
        # Source overlap discount (III-07)
        if a.source_ids and b.source_ids:
            overlap = len(a.source_ids & b.source_ids)
            total_sources = len(a.source_ids | b.source_ids)
            overlap_ratio = overlap / total_sources if total_sources > 0 else 0.0
        else:
            overlap_ratio = 0.0

        kappa = a.uncertainty + b.uncertainty \
            - a.uncertainty * b.uncertainty
        if kappa < 1e-10:
            # Both fully certain — weighted average
            fused_b = (a.belief + b.belief) / 2
            fused_d = (a.disbelief + b.disbelief) / 2
            fused_u = 0.0
        else:
            fused_b = (a.belief * b.uncertainty
                       + b.belief * a.uncertainty) / kappa
            fused_d = (a.disbelief * b.uncertainty
                       + b.disbelief * a.uncertainty) / kappa
            fused_u = (a.uncertainty * b.uncertainty) / kappa

        # Interpolate: independent fusion <-> simple average by overlap
        if overlap_ratio > 0:
            avg_b = (a.belief + b.belief) / 2
            avg_d = (a.disbelief + b.disbelief) / 2
            avg_u = (a.uncertainty + b.uncertainty) / 2
            new_b = (1 - overlap_ratio) * fused_b + overlap_ratio * avg_b
            new_d = (1 - overlap_ratio) * fused_d + overlap_ratio * avg_d
            new_u = (1 - overlap_ratio) * fused_u + overlap_ratio * avg_u
        else:
            new_b, new_d, new_u = fused_b, fused_d, fused_u

        return ProvenanceTag(
            belief=min(1.0, new_b),
            disbelief=min(1.0, new_d),
            uncertainty=max(0.0, new_u),
            source_ids=a.source_ids | b.source_ids,
            # Metadata: monotone lattice
            pramana_type=PramanaType(max(a.pramana_type, b.pramana_type)),
            trust_score=max(a.trust_score, b.trust_score),
            decay_factor=max(a.decay_factor, b.decay_factor),
            derivation_depth=min(a.derivation_depth, b.derivation_depth),
        )

    @staticmethod
    def zero() -> 'ProvenanceTag':
        """Additive identity — no evidence."""
        return ProvenanceTag(belief=0, disbelief=0, uncertainty=1.0)

    @staticmethod
    def one() -> 'ProvenanceTag':
        """Multiplicative identity — certain, no degradation."""
        return ProvenanceTag(belief=1.0, disbelief=0, uncertainty=0)

    @property
    def strength(self) -> float:
        """Scalar strength for defeat comparison: belief × trust × decay."""
        return self.belief * self.trust_score * self.decay_factor

    def epistemic_status(self) -> 'EpistemicStatus':
        """Derive epistemic status from tag values.

        NOTE: These thresholds are DSPy-optimizable parameters.
        Defaults are reasonable starting points, not final values.
        """
        if self.belief > 0.8 and self.uncertainty <= 0.1:
            return EpistemicStatus.ESTABLISHED
        elif self.belief > 0.5 and self.uncertainty < 0.3:
            return EpistemicStatus.HYPOTHESIS
        elif self.disbelief > 0.4 and self.belief > 0.3:
            return EpistemicStatus.CONTESTED
        elif self.uncertainty > 0.6:
            return EpistemicStatus.OPEN
        else:
            return EpistemicStatus.PROVISIONAL

    # ── Serialization ──

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "belief": self.belief,
            "disbelief": self.disbelief,
            "uncertainty": self.uncertainty,
            "source_ids": sorted(self.source_ids),
            "pramana_type": self.pramana_type.name,
            "trust_score": self.trust_score,
            "decay_factor": self.decay_factor,
            "derivation_depth": self.derivation_depth,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'ProvenanceTag':
        """Reconstruct from dict."""
        return cls(
            belief=d["belief"],
            disbelief=d["disbelief"],
            uncertainty=d["uncertainty"],
            source_ids=frozenset(d.get("source_ids", [])),
            pramana_type=PramanaType[d.get("pramana_type", "ANUMANA")],
            trust_score=d.get("trust_score", 1.0),
            decay_factor=d.get("decay_factor", 1.0),
            derivation_depth=d.get("derivation_depth", 0),
        )


# ─── ARGUMENTS ───────────────────────────────────────────────

@dataclass(frozen=True)
class Argument:
    """A structured argument in the ASPIC+ framework.

    Premise arguments: top_rule=None, conclusion=predicate, sub_arguments=()
    Rule arguments: top_rule=vyapti_id, sub_arguments=(sub_arg_ids...)
    """
    id: str
    conclusion: str                    # Predicate concluded
    top_rule: Optional[str]            # Vyāpti ID (None for premise arguments)
    sub_arguments: tuple = ()          # Sub-argument IDs
    premises: FrozenSet[str] = frozenset()  # Base fact predicates
    is_strict: bool = False            # Strict vs defeasible top rule
    tag: ProvenanceTag = field(
        default_factory=ProvenanceTag.one)


@dataclass
class Attack:
    """An attack between arguments."""
    attacker: str       # Argument ID
    target: str         # Argument ID
    attack_type: str    # "undermining" | "undercutting" | "rebutting"
    hetvabhasa: str     # Nyāya fallacy type: asiddha | savyabhicara | viruddha
