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
    Provenance metadata carried alongside an argument's status.

    Four fields forming a bounded product lattice
    L = L_p × L_t × L_d × L_depth:
      - pramana_type: UPAMANA(1) < SABDA(2) < ANUMANA(3) < PRATYAKSA(4)
      - trust_score:  [0,1] with standard ≤
      - decay_factor: [0,1] with standard ≤
      - derivation_depth: ℕ with standard ≤

    Composition axioms (consistent across all four fields):
      tensor (sequential) = meet (∧) = min  — weakest-link principle:
          chaining through inference cannot strengthen metadata.
      oplus (parallel)    = join (∨) = max  — best-source principle:
          accruing independent arguments takes the strongest metadata.

    Exception: derivation_depth uses + for tensor (chains add depth)
    and min for oplus (parallel paths report the shallowest).

    The Subjective Logic opinion — belief, disbelief, uncertainty, their
    sum-to-one invariant, the trust-discounting and cumulative-fusion
    arithmetic, and `strength` — used to sit here too. It is gone. An
    argument's grade is its status in the epistemic lattice, computed from
    the argumentation labelling (`lattice.py`, `ArgumentationFramework.
    get_epistemic_status`), because chaining a belief product through fixed
    cutoffs made a conclusion decay under nothing but repetition.

    What remains is metadata, and metadata composes by min and max — which
    is idempotent, so the same law holds here for free.
    """
    source_ids: FrozenSet[str] = frozenset()
    pramana_type: PramanaType = PramanaType.ANUMANA
    trust_score: float = 1.0         # Source authority [0,1]
    decay_factor: float = 1.0        # Temporal freshness [0,1]
    derivation_depth: int = 0

    def __repr__(self) -> str:
        return (
            f"Tag(src={len(self.source_ids)}, "
            f"pramana={self.pramana_type.name}, "
            f"trust={self.trust_score:.2f}, "
            f"decay={self.decay_factor:.2f}, "
            f"depth={self.derivation_depth})"
        )

    # ── Lattice Operations ──

    @staticmethod
    def tensor(a: 'ProvenanceTag', b: 'ProvenanceTag') -> 'ProvenanceTag':
        """⊗: Sequential composition (chaining through inference).

        Meet (∧) = min for pramana, trust, decay — weakest-link: chaining
        cannot strengthen provenance.  derivation_depth uses + (chains
        accumulate depth).  Associative, idempotent on the lattice fields,
        with identity one().
        """
        return ProvenanceTag(
            source_ids=a.source_ids | b.source_ids,
            pramana_type=PramanaType(min(a.pramana_type, b.pramana_type)),
            trust_score=min(a.trust_score, b.trust_score),
            decay_factor=min(a.decay_factor, b.decay_factor),
            derivation_depth=a.derivation_depth + b.derivation_depth,
        )

    @staticmethod
    def oplus(a: 'ProvenanceTag', b: 'ProvenanceTag') -> 'ProvenanceTag':
        """⊕: Parallel composition (accrual of independent arguments).

        Join (∨) = max for pramana, trust, decay — best-source: accrual
        takes the strongest provenance.  derivation_depth uses min (parallel
        paths report the shallowest).  Associative, commutative, idempotent,
        with identity zero().

        The source-overlap discount that used to live here is gone with the
        arithmetic it corrected. It existed to stop cumulative fusion from
        double-counting one argument restated, and it silently failed to
        fire when neither tag carried a source id. max needs no discount:
        `max(s, s) = s` whatever the provenance says.
        """
        return ProvenanceTag(
            source_ids=a.source_ids | b.source_ids,
            pramana_type=PramanaType(max(a.pramana_type, b.pramana_type)),
            trust_score=max(a.trust_score, b.trust_score),
            decay_factor=max(a.decay_factor, b.decay_factor),
            derivation_depth=min(a.derivation_depth, b.derivation_depth),
        )

    @staticmethod
    def zero() -> 'ProvenanceTag':
        """Identity for ⊕ — the bottom of the metadata lattice.

        Bottom, not top. This tag stands for "nothing accrued", and max
        against it must leave the other operand untouched; built at the top
        it would have raised any argument it met to maximal trust and
        perfect freshness, which is an absence of evidence scoring as the
        best possible source.
        """
        return ProvenanceTag(
            pramana_type=PramanaType.UPAMANA,
            trust_score=0.0,
            decay_factor=0.0,
        )

    @staticmethod
    def one() -> 'ProvenanceTag':
        """Identity for ⊗ — the top of the metadata lattice.

        Top, so that min against it leaves the other operand untouched.
        Not a safe default value for an argument that has no provenance:
        it is an identity, and the two roles are different.
        """
        return ProvenanceTag(
            pramana_type=PramanaType.PRATYAKSA,
            trust_score=1.0,
            decay_factor=1.0,
        )

    # ── Serialization ──

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
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
    # Both of the following are mandatory. They are declared with None
    # defaults only because the fields above already carry defaults;
    # __post_init__ is what enforces them.
    #
    # `tag` no longer defaults to one(). one() is the identity for ⊗ and so
    # sits at the TOP of the metadata lattice — as a default it would have
    # handed every argument built without provenance the strongest pramāṇa,
    # full trust and perfect freshness.
    tag: Optional[ProvenanceTag] = None
    # Status in L: the meet of this argument's top rule and its
    # sub-arguments.
    status: Optional['EpistemicStatus'] = None

    def __post_init__(self):
        if self.status is None:
            raise ValueError(
                f"argument {self.id!r} was built without a status from the "
                f"lattice. There is no sensible default: the top would score "
                f"an unevaluated argument as ESTABLISHED and the bottom would "
                f"report it as defeated. Compute the meet of its top rule and "
                f"its sub-arguments, or state its premise status explicitly."
            )
        if self.tag is None:
            raise ValueError(
                f"argument {self.id!r} was built without a provenance tag. "
                f"There is no safe default: the lattice identity sits at the "
                f"top, so defaulting would report an argument of unknown "
                f"provenance as direct evidence from a fully trusted source."
            )


@dataclass
class Attack:
    """An attack between arguments."""
    attacker: str       # Argument ID
    target: str         # Argument ID
    attack_type: str    # "undermining" | "undercutting" | "rebutting"
    hetvabhasa: str     # Nyāya fallacy type: asiddha | savyabhicara | viruddha
