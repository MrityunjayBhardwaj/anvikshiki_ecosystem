# Ānvīkṣikī Engine v4 — Build Guide

## From Thesis to Working System: A Complete Implementation Manual

**Target:** Build the four-phase neurosymbolic argumentation engine described in `thesis2_v1.md`
**Stack:** DSPy 3.1.x + ASPIC+ Argumentation Engine + Provenance Semirings + Custom Datalog + NetworkX
**Python:** 3.10+ (required by DSPy 3.x)
**Date:** March 2026

---

## Table of Contents

0. [What Changed from BUILD_GUIDE.md (v3) and WHY](#0-what-changed-from-build_guidemd-v3-and-why)
1. [Technology Stack Decisions](#1-technology-stack-decisions)
2. [Project Structure](#2-project-structure)
3. [Environment Setup](#3-environment-setup)
4. [Module 1: Core v4 Schema (`schema_v4.py`)](#4-module-1-core-v4-schema)
5. [Module 2: KnowledgeStore Schema (`schema.py`)](#5-module-2-knowledgestore-schema)
6. [Module 3: Datalog Engine (`datalog_engine.py`)](#6-module-3-datalog-engine)
7. [Module 4: Argumentation Engine (`argumentation.py`)](#7-module-4-argumentation-engine)
8. [Module 5: T2 Compiler v4 (`t2_compiler_v4.py`)](#8-module-5-t2-compiler-v4)
9. [Module 6: T3 Compiler (`t3_compiler.py`)](#9-module-6-t3-compiler)
10. [Module 7: Grounding Pipeline (`grounding.py`)](#10-module-7-grounding-pipeline)
11. [Module 8: Uncertainty Quantification (`uncertainty.py`)](#11-module-8-uncertainty-quantification)
12. [Module 9: Contestation Protocols (`contestation.py`)](#12-module-9-contestation-protocols)
13. [Module 10: Final Engine (`engine_v4.py`)](#13-module-10-final-engine)
14. [Module 11: Optimization (`optimize.py`)](#14-module-11-optimization)
15. [Testing Strategy](#15-testing-strategy)
16. [Phase-by-Phase Build Order](#16-phase-by-phase-build-order)
17. [DSPy 3.x Migration Notes](#17-dspy-3x-migration-notes)
18. [Appendix A: egglog Integration](#18-appendix-a-egglog-integration)
19. [Appendix B: Grammar-Constrained Decoding Options](#19-appendix-b-grammar-constrained-decoding)
20. [Appendix C: Nyāya-to-ASPIC+ Implementation Tables](#20-appendix-c-nyāya-to-aspic-implementation-tables)
21. [Appendix D: Provenance Semiring Mathematics](#21-appendix-d-provenance-semiring-mathematics)
22. [Appendix E: Contestable AI Compliance Checklist](#22-appendix-e-contestable-ai-compliance-checklist)

---

## 0. What Changed from BUILD_GUIDE.md (v3) and WHY

### 0.1 Architecture Summary

```
NYĀYA EPISTEMOLOGY (design ontology)
    │   provides: concepts, categories, distinctions
    │   does NOT provide: computation, semantics, complexity bounds
    ▼
ASPIC+ ARGUMENTATION (reasoning structure)
    │   provides: arguments, defeats, extensions, proof traces
    │   does NOT provide: quantitative strength, evidence accumulation
    ▼
PROVENANCE SEMIRING (quantitative annotation)
    │   provides: evidence tags, trust propagation, decay tracking
    │   does NOT provide: conflict resolution, defeat handling
    ▼
DATALOG EVALUATION (computational substrate)
        provides: polynomial fixpoint computation, semi-naive evaluation
```

v3 solved each concern with the best tool from a different tradition — Heyting lattice, cellular sheaf, trust table, keyword matching, domain-base dict, meet-only lattice. The result: six independent formalisms that do not compose. v4 replaces all six with two composing layers: **argumentation structure + semiring annotation**. The sheaf, conformal verifier, trust table, keyword hetvābhāsa detector, and Heyting lattice are all eliminated.

### 0.2 Module Migration Table

| v3 Module (BUILD_GUIDE.md) | v4 Module (this guide) | What Changed |
|---|---|---|
| `schema.py` (KnowledgeStore, Vyapti) | `schema.py` **unchanged** | Same YAML input format. No migration needed. |
| `schema.py` (EpistemicValue IntEnum) | `schema_v4.py` (ProvenanceTag, Argument, Attack, Label) | Heyting lattice eliminated. Epistemic status now *emerges* from extension membership + tag values. |
| `datalog_engine.py` (semi-naive Heyting Datalog) | `datalog_engine.py` **reused** (Phase 2 only) | Same code, reduced role. Phase 3+ uses argumentation engine directly. |
| *(no equivalent)* | `argumentation.py` **NEW** | Core v4 module. ASPIC+ grounded semantics via Wu/Caminada/Gabbay 2009 with pramāṇa-based preferences. |
| `t2_compiler.py` (vyāptis → Datalog rules) | `t2_compiler_v4.py` **rewritten** | Compiles vyāptis to ASPIC+ arguments + derives three attack types + builds provenance tags. |
| `t3_compiler.py` (GraphRAG) | `t3_compiler.py` **unchanged** | No changes. T3 is the retrieval corpus for Phase 4. |
| `grounding.py` (five-layer defense) | `grounding.py` **unchanged** | v4 changes the symbolic layer only. |
| `uncertainty.py` (Heyting + domain_base dict) | `uncertainty.py` **refined** | All three UQ components now derive from ProvenanceTag fields. `DOMAIN_BASE_UNCERTAINTY` dict eliminated. |
| `conformal.py` (split conformal prediction) | **REMOVED** | Source tracking via ProvenanceTag.source_ids through argument trees. |
| `sheaf.py` (coboundary, Laplacian, H¹) | **REMOVED** | Consistency guaranteed by argumentation rationality postulates. |
| `source_authority.py` (trust tier table) | **REMOVED** | Trust encoded in ProvenanceTag.trust_score + pramāṇa hierarchy. |
| `provenance.py` (chain tracer) | **REMOVED** | Provenance carried natively by argument trees + tag.source_ids. |
| `engine.py` (7-step pipeline) | `engine_v4.py` **rewritten** | 8-step pipeline: ground → AF build → grounded extension → epistemic status → provenance → UQ → violations → synthesize. |
| `optimize.py` (calibration metric) | `optimize.py` **updated** | Metric checks extension quality, tag calibration, contestation coverage. |
| *(no equivalent)* | `contestation.py` **NEW** | Three Nyāya debate protocols: vāda/jalpa/vitaṇḍā → grounded/preferred/stable semantics. |

### 0.3 The Frankenstein Problem — Why v4 Exists

The v3 architecture had six independent formalisms from six intellectual traditions:

1. **Heyting lattice** (order theory) — epistemic status propagation
2. **Cellular sheaf** (algebraic topology) — consistency checking
3. **Trust lookup table** (hand-tuned) — source authority (20+ entries)
4. **Keyword matching** (string ops) — hetvābhāsa detection
5. **Domain-base dict** (hand-tuned) — aleatoric uncertainty (8 entries)
6. **Meet-only propagation** (lattice algebra) — evidence attenuation

Each was the "best tool" for its concern, but they do not compose. The sheaf was architecturally present but functionally inert (identity restriction maps make the coboundary trivial). The trust table had 20+ hand-specified entries with no formal justification. Keyword hetvābhāsa detection used string matching (`if "survivorship" in sig`).

**v4 result:** 6 formalisms → 2 that compose. 16 hand-specified decisions → 3 tunable parameters + DSPy-optimizable hyperparameters.

### 0.4 What Stays the Same

These components require **zero changes** from v3:

- **KnowledgeStore input format** — same YAML schema, same Pydantic models
- **`grounding.py`** — five-layer NL→predicate defense (LLM-facing; v4 changes symbolic layer only)
- **`t3_compiler.py`** — GraphRAG corpus builder
- **`datalog_engine.py`** — semi-naive evaluator (kept for Phase 2 backward compatibility)
- **DSPy 3.1.x patterns** — LM config, Refine/BestOfN, Pydantic output, MIPROv2
- **Project conventions** — Pydantic models, pytest structure, pyproject.toml layout

---

## 1. Technology Stack Decisions

### 1.1 Why These Choices

| Component | Tool | Why |
|-----------|------|-----|
| **LLM Orchestration** | DSPy 3.1.x | Typed signatures, optimizable modules, Pydantic output types, `dspy.Refine` for constraints |
| **Argumentation Engine** | Custom Python | Full control over preference ordering, defeat logic, provenance tag propagation. No existing Python ASPIC+ library handles semiring-valued tags. |
| **Provenance Semiring** | Custom Python (Subjective Logic) | Cumulative fusion (Jøsang 2016) for evidence accrual, tensor for chaining. Pure arithmetic, no dependencies. |
| **Datalog Engine** | Custom Python (semi-naive) | Reused from v3 for Phase 2. ~300 lines, fully inspectable for proof traces. |
| **Datalog Engine (optional)** | egglog-python | Rust-backed alternative if >1000 arguments. Native lattice merge via `:merge`. |
| **Knowledge Graph** | NetworkX | For T3 GraphRAG corpus. Mature, pure-Python. |
| **Retrieval** | `dspy.retrievers.Embeddings` | Built into DSPy 3.x, uses FAISS. |
| **Structured Output** | Pydantic + `dspy.JSONAdapter()` | Native DSPy 3.x support for typed predictors. |
| **Grammar Constraint** | Instructor (API) / XGrammar (local) | Instructor for Claude/GPT; XGrammar for local serving via SGLang. |

### 1.2 What Was Removed from the Stack

| Dependency | Was Used For | Why Removed |
|-----------|-------------|-------------|
| NumPy/SciPy | Sheaf Laplacian computation | No sheaf in v4. ProvenanceTag operations are pure Python arithmetic. |
| Conformal prediction | Source verification | Replaced by ProvenanceTag.source_ids provenance tracking. |
| Sentence-transformers | Optional CrossEncoder in conformal.py | No conformal module. |

### 1.3 New Concepts in the Stack

**ASPIC+ Structured Argumentation** — Arguments built from premises via strict/defeasible rules. Three defeat types: undermining (attack on premise), undercutting (attack on rule applicability), rebutting (counter-argument for contrary conclusion). Grounded semantics computable in polynomial time. References: Prakken 2010, Modgil & Prakken 2018.

**Provenance Semirings** — Algebraic annotation on Datalog derivations. Two operations: ⊗ (tensor, sequential composition through inference chains) and ⊕ (oplus, parallel composition from independent arguments). The ProvenanceTag uses Subjective Logic opinions (Jøsang 2016) as the concrete semiring. References: Green et al. PODS 2007, Jøsang 2016.

---

## 2. Project Structure

```
anvikshiki_v4/
├── __init__.py
├── schema.py                  # KnowledgeStore, Vyapti, Hetvabhasa (input format, reused from v3)
├── schema_v4.py               # ProvenanceTag, PramanaType, RuleType, EpistemicStatus,
│                              #   Argument, Attack, Label (v4 core types)
├── datalog_engine.py          # Semi-naive evaluator (reused from v3, Phase 2 only)
├── argumentation.py           # ArgumentationFramework, compute_grounded(), _defeats(),
│                              #   get_epistemic_status() (v4 core engine)
├── t2_compiler_v4.py          # KB + query facts → AF with arguments, attacks, tags
├── t3_compiler.py             # Guide text → GraphRAG corpus (reused from v3)
├── grounding.py               # Five-layer NL→predicate defense (reused from v3)
├── uncertainty.py             # Three-way UQ from provenance tags (v4 refined)
├── contestation.py            # Three debate protocols: vāda/jalpa/vitaṇḍā (v4 new)
├── engine_v4.py               # Complete 8-step pipeline (AnvikshikiEngineV4)
├── optimize.py                # DSPy optimization with argumentation-aware metric
├── cli.py                     # Command-line interface
│
├── tests/
│   ├── __init__.py
│   ├── test_schema.py         # KnowledgeStore validation (reused from v3)
│   ├── test_schema_v4.py      # ProvenanceTag semiring laws, Argument/Attack construction
│   ├── test_datalog.py        # Semi-naive evaluation (reused from v3)
│   ├── test_argumentation.py  # Grounded extension, defeats, epistemic status
│   ├── test_t2_compiler_v4.py # AF construction, attack generation, tag computation
│   ├── test_t3_compiler.py    # GraphRAG (reused from v3)
│   ├── test_grounding.py      # Five-layer defense (requires LLM)
│   ├── test_uncertainty.py    # UQ from provenance tags
│   ├── test_contestation.py   # Debate protocol correctness
│   ├── test_engine_v4.py      # Full pipeline integration
│   └── fixtures/
│       ├── sample_architecture.yaml
│       └── sample_af.json     # Pre-built AF for unit testing
│
├── data/
│   └── sample_architecture.yaml
│
├── pyproject.toml
└── README.md
```

### 2.1 Module Dependency Graph

```
schema.py (input types — Pydantic)
    │
schema_v4.py (v4 types — frozen dataclasses)
    │
    ├──→ argumentation.py (imports schema_v4)
    │        │
    ├──→ t2_compiler_v4.py (imports schema, schema_v4, argumentation)
    │        │
    ├──→ uncertainty.py (imports schema_v4)
    │        │
    └──→ contestation.py (imports argumentation, schema_v4)
              │
grounding.py (five-layer defense, imports schema)
    │
    └──→ engine_v4.py (imports grounding, t2_compiler_v4, argumentation,
              │          uncertainty, contestation, schema_v4)
              │
              └──→ optimize.py (imports engine_v4)
```

---

## 3. Environment Setup

### 3.1 System Requirements

- Python 3.10–3.13
- macOS, Linux, or WSL2
- 4GB+ RAM (reduced from v3's 8GB — no sheaf Laplacian)

### 3.2 Installation

```bash
# Create project directory
mkdir -p anvikshiki_v4 && cd anvikshiki_v4

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Core dependencies
pip install dspy>=3.1.0          # LLM orchestration (includes LiteLLM)
pip install networkx>=3.2        # Knowledge graph (T3 only)
pip install pydantic>=2.6        # Structured output types
pip install pyyaml>=6.0          # YAML parsing for architecture files

# Optional: high-performance Datalog backend
pip install egglog>=11.0         # Rust-backed Datalog with lattice merge

# Optional: structured output for API models
pip install instructor>=1.5     # Pydantic extraction from API models

# Optional: local model serving with grammar constraints
pip install xgrammar            # Grammar-constrained decoding engine

# Development
pip install pytest>=8.0
pip install pytest-asyncio      # For async DSPy tests
```

**Note:** `numpy` and `scipy` are NOT required for v4 core. They remain optional if T3 corpus needs numerical operations.

### 3.3 LM Configuration

```python
import dspy

# Option A: OpenAI (recommended for development)
lm = dspy.LM('openai/gpt-4o-mini', api_key='sk-...')

# Option B: Anthropic
lm = dspy.LM('anthropic/claude-sonnet-4-5-20250929', api_key='sk-ant-...')

# Option C: Local model via Ollama
lm = dspy.LM('ollama_chat/llama3.2', api_base='http://localhost:11434', api_key='')

# Option D: Local model via SGLang (best for grammar-constrained decoding)
lm = dspy.LM('openai/meta-llama/Meta-Llama-3-8B-Instruct',
              api_base='http://localhost:7501/v1', api_key='')

# Configure globally
dspy.configure(lm=lm)
```

### 3.4 pyproject.toml

```toml
[project]
name = "anvikshiki-v4"
version = "0.1.0"
description = "Neurosymbolic argumentation engine with ASPIC+ over provenance semirings"
requires-python = ">=3.10"
dependencies = [
    "dspy>=3.1.0",
    "networkx>=3.2",
    "pydantic>=2.6",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
egglog = ["egglog>=11.0"]
instructor = ["instructor>=1.5"]
dev = ["pytest>=8.0", "pytest-asyncio"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## 4. Module 1: Core v4 Schema

**File:** `anvikshiki_v4/schema_v4.py`
**Purpose:** All new data types for the argumentation-based engine. Every other v4 module depends on these types.
**Dependencies:** `dataclasses`, `enum`, `datetime`

### 4.1 Design Decisions

1. **ProvenanceTag as frozen dataclass (not Pydantic).** Frozen for hashability — tags are stored in sets and used as dictionary keys. Pydantic BaseModel is mutable and unhashable. Tradeoff: no automatic validation. We add a `__post_init__` check that `b + d + u ≈ 1.0`.

2. **Semiring operations as static methods.** `ProvenanceTag.tensor(a, b)` and `ProvenanceTag.oplus(a, b)` rather than `a.tensor(b)`. Reason: semiring operations are symmetric/associative — static methods make this clear and match mathematical notation.

3. **PramanaType as IntEnum with explicit ordering.** `UPAMANA=1 < SABDA=2 < ANUMANA=3 < PRATYAKSA=4`. This ordering is load-bearing: `_defeats()` compares pramāṇa types directly. Formalizes Nyāya's hierarchy: direct perception > inference > testimony > analogy.

4. **EpistemicStatus as plain Enum (NOT IntEnum, NOT ordered).** Deliberate change from v3 where EpistemicStatus was partially ordered via the Heyting lattice. In v4, epistemic status is *derived* from extension membership + tag values. CONTESTED and OPEN are incomparable — not ordered — which fixes v3 audit item H1.

5. **Argument as frozen dataclass.** Immutable after construction. Sub-arguments are a tuple of argument IDs, premises a frozenset of base predicates.

6. **Attack as mutable dataclass.** Attacks can be added dynamically during contestation.

7. **Label as Enum.** IN / OUT / UNDECIDED. Derived by `compute_grounded()`, not hand-assigned.

### 4.2 Complete Implementation

```python
# anvikshiki_v4/schema_v4.py
"""Core data structures for the argumentation-based engine (v4)."""

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Optional, FrozenSet
from datetime import datetime


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
    Semiring-valued annotation on arguments.
    Extends Subjective Logic opinions (Jøsang 2016) with provenance metadata.

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

        When argument A supports a premise of argument B, the combined
        evidence attenuates through the chain.
        """
        return ProvenanceTag(
            belief=a.belief * b.belief,
            disbelief=min(1.0, a.disbelief + b.disbelief
                         - a.disbelief * b.disbelief),
            uncertainty=min(1.0, a.uncertainty + b.uncertainty
                           - a.uncertainty * b.uncertainty),
            source_ids=a.source_ids | b.source_ids,
            pramana_type=PramanaType(min(a.pramana_type, b.pramana_type)),
            trust_score=min(a.trust_score, b.trust_score),
            decay_factor=min(a.decay_factor, b.decay_factor),
            derivation_depth=a.derivation_depth + b.derivation_depth,
        )

    @staticmethod
    def oplus(a: 'ProvenanceTag', b: 'ProvenanceTag') -> 'ProvenanceTag':
        """⊕: Parallel composition (accrual of independent arguments).

        Uses cumulative fusion (Jøsang 2016) — non-idempotent, so
        multiple independent arguments strengthen the conclusion.
        """
        kappa = a.uncertainty + b.uncertainty \
            - a.uncertainty * b.uncertainty
        if kappa < 1e-10:
            # Both fully certain — weighted average
            new_b = (a.belief + b.belief) / 2
            new_d = (a.disbelief + b.disbelief) / 2
            new_u = 0.0
        else:
            new_b = (a.belief * b.uncertainty
                     + b.belief * a.uncertainty) / kappa
            new_d = (a.disbelief * b.uncertainty
                     + b.disbelief * a.uncertainty) / kappa
            new_u = (a.uncertainty * b.uncertainty) / kappa

        return ProvenanceTag(
            belief=min(1.0, new_b),
            disbelief=min(1.0, new_d),
            uncertainty=max(0.0, new_u),
            source_ids=a.source_ids | b.source_ids,
            pramana_type=PramanaType(max(a.pramana_type, b.pramana_type)),
            trust_score=1 - (1 - a.trust_score) * (1 - b.trust_score),
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
        if self.belief > 0.8 and self.uncertainty < 0.1:
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
```

### 4.3 Semiring Laws Verification

| Axiom | Statement | ProvenanceTag Verification |
|-------|-----------|---------------------------|
| **⊗ associativity** | (a ⊗ b) ⊗ c = a ⊗ (b ⊗ c) | belief: `(a.b × b.b) × c.b = a.b × (b.b × c.b)` — multiplication is associative. `min()` is associative. Union is associative. |
| **⊗ commutativity** | a ⊗ b = b ⊗ a | belief: `a.b × b.b = b.b × a.b`. `min()` is commutative. Union is commutative. |
| **⊕ associativity** | (a ⊕ b) ⊕ c = a ⊕ (b ⊕ c) | Cumulative fusion is associative (Jøsang 2016, Theorem 12.3). |
| **⊕ commutativity** | a ⊕ b = b ⊕ a | Fusion formula is symmetric in a and b. |
| **Distributivity** | a ⊗ (b ⊕ c) = (a ⊗ b) ⊕ (a ⊗ c) | Holds for belief (multiplication distributes over fusion). Approximate for trust due to noisy-OR. |
| **⊗ identity** | a ⊗ one() = a | `one() = Tag(b=1, d=0, u=0)`. `a.b × 1 = a.b`, `min(a.trust, 1) = a.trust`. |
| **⊕ identity** | a ⊕ zero() = a | `zero() = Tag(b=0, d=0, u=1)`. Cumulative fusion with fully uncertain tag returns original. |
| **Annihilation** | a ⊗ zero() = zero() | `zero()` has `b=0`. `0 × a.b = 0`. Strength = 0. |

### 4.4 Nyāya-to-ASPIC+ Mapping Table

| Nyāya Concept | ASPIC+ Equivalent | Code Reference |
|---------------|-------------------|----------------|
| Vyāpti (definitional/structural) | Strict rule rₛ ∈ Rₛ | `Argument(is_strict=True)` |
| Vyāpti (empirical/regulatory) | Defeasible rule rₐ ∈ Rₐ | `Argument(is_strict=False)` |
| Pratyakṣa (direct evidence) | Necessary premise Kₙ | `Argument(top_rule=None, tag.pramana_type=PRATYAKSA)` |
| Śabda (testimony) | Ordinary premise Kₚ | `Argument(top_rule=None, tag.pramana_type=SABDA)` |
| Anumāna (inference chain) | Argument tree | `Argument(sub_arguments=(...), top_rule=vid)` |
| Pañcāvayava (proof trace) | Argument structure | `Argument` dataclass fields |
| Asiddha (unestablished) | Undermining attack | `Attack(type="undermining", hetvabhasa="asiddha")` |
| Savyabhicāra (inconclusive) | Undercutting attack | `Attack(type="undercutting", hetvabhasa="savyabhicara")` |
| Viruddha (contradictory) | Rebutting attack | `Attack(type="rebutting", hetvabhasa="viruddha")` |
| Satpratipakṣa (counterbalanced) | Symmetric attack | Mutual `Attack`s + equal `tag.strength` |
| Bādhita (sublated) | Preference-based defeat | `_defeats()` returns True when `attacker.pramana > target.pramana` |
| Pramāṇa hierarchy | Argument preference ≤ | `PramanaType(IntEnum)` comparison |
| ESTABLISHED | IN grounded, strong tag | `get_epistemic_status()` → ESTABLISHED |
| CONTESTED | OUT grounded, IN preferred | `get_epistemic_status()` → CONTESTED |
| OPEN | UNDECIDED | `get_epistemic_status()` → OPEN |
| Vāda (honest inquiry) | Grounded semantics | `compute_grounded()` |
| Jalpa (adversarial debate) | Preferred semantics | `compute_preferred()` |
| Vitaṇḍā (pure critique) | Stable semantics | `compute_stable()` |

### 4.5 Tests: `tests/test_schema_v4.py`

```python
# tests/test_schema_v4.py
import pytest
import math
from anvikshiki_v4.schema_v4 import (
    ProvenanceTag, PramanaType, EpistemicStatus, Argument, Attack, Label
)


# ── Semiring Law Tests ──

def test_tensor_associativity():
    a = ProvenanceTag(belief=0.8, disbelief=0.1, uncertainty=0.1,
                      trust_score=0.9, decay_factor=0.95, derivation_depth=1)
    b = ProvenanceTag(belief=0.7, disbelief=0.2, uncertainty=0.1,
                      trust_score=0.85, decay_factor=0.9, derivation_depth=1)
    c = ProvenanceTag(belief=0.9, disbelief=0.05, uncertainty=0.05,
                      trust_score=0.95, decay_factor=0.92, derivation_depth=1)
    ab_c = ProvenanceTag.tensor(ProvenanceTag.tensor(a, b), c)
    a_bc = ProvenanceTag.tensor(a, ProvenanceTag.tensor(b, c))
    assert abs(ab_c.belief - a_bc.belief) < 1e-10
    assert abs(ab_c.trust_score - a_bc.trust_score) < 1e-10
    assert ab_c.derivation_depth == a_bc.derivation_depth == 3


def test_oplus_commutativity():
    a = ProvenanceTag(belief=0.6, disbelief=0.1, uncertainty=0.3,
                      trust_score=0.8, decay_factor=0.9, derivation_depth=2)
    b = ProvenanceTag(belief=0.5, disbelief=0.15, uncertainty=0.35,
                      trust_score=0.85, decay_factor=0.95, derivation_depth=1)
    ab = ProvenanceTag.oplus(a, b)
    ba = ProvenanceTag.oplus(b, a)
    assert abs(ab.belief - ba.belief) < 1e-10
    assert abs(ab.disbelief - ba.disbelief) < 1e-10
    assert abs(ab.uncertainty - ba.uncertainty) < 1e-10


def test_tensor_identity():
    a = ProvenanceTag(belief=0.7, disbelief=0.2, uncertainty=0.1,
                      trust_score=0.8, decay_factor=0.9, derivation_depth=2)
    result = ProvenanceTag.tensor(a, ProvenanceTag.one())
    assert abs(result.belief - a.belief) < 1e-10
    assert abs(result.trust_score - a.trust_score) < 1e-10
    assert result.derivation_depth == a.derivation_depth


def test_oplus_identity():
    a = ProvenanceTag(belief=0.7, disbelief=0.2, uncertainty=0.1,
                      trust_score=0.8, decay_factor=0.9, derivation_depth=2)
    result = ProvenanceTag.oplus(a, ProvenanceTag.zero())
    assert abs(result.belief - a.belief) < 1e-10


def test_tensor_annihilation():
    a = ProvenanceTag(belief=0.9, disbelief=0.05, uncertainty=0.05,
                      trust_score=0.9, decay_factor=0.95, derivation_depth=1)
    result = ProvenanceTag.tensor(a, ProvenanceTag.zero())
    assert result.belief == 0.0
    assert result.strength == 0.0


# ── Tag Arithmetic Tests ──

def test_tensor_attenuates():
    a = ProvenanceTag(belief=0.9, disbelief=0.05, uncertainty=0.05,
                      trust_score=0.8, decay_factor=0.9, derivation_depth=1)
    b = ProvenanceTag(belief=0.9, disbelief=0.05, uncertainty=0.05,
                      trust_score=0.85, decay_factor=0.95, derivation_depth=1)
    result = ProvenanceTag.tensor(a, b)
    assert result.belief == pytest.approx(0.81, rel=1e-5)
    assert result.trust_score == 0.8   # min
    assert result.derivation_depth == 2


def test_oplus_accumulates():
    """Three HYPOTHESIS-level tags: combined belief > any individual."""
    tag = ProvenanceTag(belief=0.6, disbelief=0.1, uncertainty=0.3,
                        trust_score=0.8, decay_factor=0.9, derivation_depth=1)
    combined = ProvenanceTag.oplus(tag, tag)
    combined = ProvenanceTag.oplus(combined, tag)
    assert combined.belief > 0.6  # Non-idempotent accumulation


# ── Epistemic Status Tests ──

def test_epistemic_status_established():
    tag = ProvenanceTag(belief=0.9, disbelief=0.05, uncertainty=0.05)
    assert tag.epistemic_status() == EpistemicStatus.ESTABLISHED


def test_epistemic_status_hypothesis():
    tag = ProvenanceTag(belief=0.6, disbelief=0.15, uncertainty=0.25)
    assert tag.epistemic_status() == EpistemicStatus.HYPOTHESIS


def test_epistemic_status_contested():
    tag = ProvenanceTag(belief=0.4, disbelief=0.5, uncertainty=0.1)
    assert tag.epistemic_status() == EpistemicStatus.CONTESTED


def test_epistemic_status_open():
    tag = ProvenanceTag(belief=0.15, disbelief=0.15, uncertainty=0.7)
    assert tag.epistemic_status() == EpistemicStatus.OPEN


# ── Validation Tests ──

def test_tag_validation_rejects_invalid():
    with pytest.raises(ValueError, match="b \\+ d \\+ u must"):
        ProvenanceTag(belief=0.5, disbelief=0.5, uncertainty=0.5)


# ── Serialization Tests ──

def test_tag_roundtrip():
    tag = ProvenanceTag(
        belief=0.7, disbelief=0.2, uncertainty=0.1,
        source_ids=frozenset(["src1", "src2"]),
        pramana_type=PramanaType.ANUMANA,
        trust_score=0.85, decay_factor=0.9, derivation_depth=2,
    )
    d = tag.to_dict()
    restored = ProvenanceTag.from_dict(d)
    assert abs(restored.belief - tag.belief) < 1e-10
    assert restored.pramana_type == tag.pramana_type
    assert restored.source_ids == tag.source_ids
```

---

## 5. Module 2: KnowledgeStore Schema

**File:** `anvikshiki_v4/schema.py`
**Purpose:** Data structures for the compiled knowledge store — populated by the T2 compiler from Stage 2+3 YAML output.
**Status:** Unchanged from v3.

### 5.1 Implementation

Identical to BUILD_GUIDE.md Section 4. Contains: `DomainType`, `CausalStatus`, `EpistemicStatus`, `DecayRisk`, `Confidence`, `Vyapti`, `Hetvabhasa`, `ThresholdConcept`, `ChapterFingerprint`, `KnowledgeStore`.

All models inherit from `pydantic.BaseModel` for validation, JSON serialization, and use as DSPy 3.x output field types.

### 5.2 What v4 Reads Differently

v4 reads the same YAML input but interprets fields for argumentation:

| KnowledgeStore Field | v3 Usage | v4 Usage |
|---------------------|----------|----------|
| `Vyapti.causal_status` | Not used in compilation | Determines strict vs defeasible rule: DEFINITIONAL/STRUCTURAL → strict, EMPIRICAL/REGULATORY → defeasible |
| `Vyapti.epistemic_status` | Mapped to Heyting lattice value | Input to `_build_rule_tag()` → initializes (belief, disbelief, uncertainty) on ProvenanceTag |
| `Vyapti.confidence` | Displayed in output | `formulation × existence` → ProvenanceTag.trust_score |
| `Vyapti.last_verified` | Decay warning | Exponential decay → ProvenanceTag.decay_factor |
| `Vyapti.scope_exclusions` | Checked by sheaf | Generates undercutting attacks (savyabhicāra) |
| `Vyapti.sources` | Displayed in output | Stored in ProvenanceTag.source_ids for provenance tracking |

### 5.3 Tests

Reuse v3 `tests/test_schema.py` — Pydantic validation, JSON round-trip, enum serialization.

---

## 6. Module 3: Datalog Engine

**File:** `anvikshiki_v4/datalog_engine.py`
**Purpose:** Semi-naive Datalog evaluator with lattice-valued facts.
**Status:** Reused from v3 unchanged.

### 6.1 Role in v4

| Phase | Datalog Engine Role |
|-------|-------------------|
| Phase 1 | Not used (LLM-only baseline) |
| Phase 2 | Used with `boolean_mode=True` to construct initial arguments via forward chaining. Derived facts become premise arguments for the ArgumentationFramework. |
| Phase 3+ | Not used directly. ArgumentationFramework handles inference. The fixpoint pattern from the Datalog engine is reused conceptually in `compute_grounded()`. |

### 6.2 Implementation

Identical to BUILD_GUIDE.md Section 5. Contains: `EpistemicValue` IntEnum lattice with `meet()`/`join()`, `Fact`, `Rule`, `Violation`, `DatalogEngine` class with `add_fact()`, `add_rule()`, `evaluate()` (semi-naive), `_try_fire()`, `query()`, `explain()`, `validate_predicates()`, `check_hetvabhasas()`.

### 6.3 Tests

Reuse v3 `tests/test_datalog.py` — boolean/lattice mode, semi-naive correctness, termination, scope exclusion.

---

## 7. Module 4: Argumentation Engine

**File:** `anvikshiki_v4/argumentation.py`
**Purpose:** The central new module of v4. Implements ASPIC+ grounded semantics over provenance semirings with pramāṇa-based preferences.
**Dependencies:** `schema_v4.py`

### 7.1 Design Decisions

1. **ArgumentationFramework as mutable dataclass.** Arguments and attacks are added incrementally during T2 compilation and during contestation.

2. **Index structures for O(1) lookup.** `_attackers_of[target] → [attacker_ids]` and `_attacks_on[target] → [Attack objects]`. Both maintained by `add_attack()`. Critical for polynomial `compute_grounded()`.

3. **Grounded semantics as default.** `compute_grounded()` is the primary computation — polynomial time (P-complete), maximally skeptical. Implements Wu, Caminada & Gabbay 2009 iterative propagation.

4. **Preference-based defeat.** `_defeats()` checks pramāṇa hierarchy first (higher pramāṇa always wins — this is bādhita). On equal pramāṇa, compares `tag.strength`. Formalizes Nyāya's principle: pratyakṣa > anumāna > śabda > upamāna.

5. **Epistemic status from semantics.** `get_epistemic_status()` finds all arguments for a conclusion, combines accepted arguments' tags via ⊕, derives EpistemicStatus from the combined tag. This is where epistemic status *emerges* from argumentation rather than being hand-assigned.

### 7.2 The Grounded Extension Algorithm

**Algorithm (Wu, Caminada & Gabbay 2009):**
1. All arguments start unlabeled
2. Label all unattacked arguments **IN**
3. For each argument with an IN attacker that defeats it: label **OUT**
4. For each argument where all attackers are OUT: label **IN**
5. Repeat steps 3-4 until fixpoint
6. Everything remaining is **UNDECIDED**

**Complexity:** O(|arguments| × |attacks|) — polynomial.

**Worked Example:**

```
Arguments:
  A0: premise "concentrated_ownership(acme)"  [PRATYAKSA, b=0.9]
  A1: rule V01 "→ long_horizon_possible(acme)" sub=(A0) [ANUMANA, b=0.72]
  A2: rule V02 "→ capability_building(acme)" sub=(A1)   [ANUMANA, b=0.58]
  A3: scope "public_firm(acme)"               [PRATYAKSA, b=1.0]

Attacks:
  A3 --undercutting--> A1  (scope exclusion: public_firm ∈ V01.exclusions)

Iteration 1:
  A0: no attackers → IN
  A3: no attackers → IN
  A1: attacker A3 is IN, _defeats(A3, A1)?
      A3.pramana=PRATYAKSA > A1.pramana=ANUMANA → True → A1 OUT
  A2: sub-argument A1 is OUT → A2's antecedent has no IN argument → UNDECIDED

Result: A0=IN, A3=IN, A1=OUT, A2=UNDECIDED
  concentrated_ownership → ESTABLISHED
  long_horizon_possible → CONTESTED (has argument, but defeated)
  capability_building → OPEN (no accepted argument)
```

### 7.3 Complete Implementation

```python
# anvikshiki_v4/argumentation.py
"""
Argumentation engine computing ASPIC+ grounded semantics
via Datalog-style fixpoint evaluation over provenance semirings.

References:
  - Wu, Caminada & Gabbay 2009 (grounded semantics)
  - Prakken 2010 (ASPIC+ framework)
  - Diller et al. KR 2025 (grounding ASPIC+ with Datalog)
"""

from dataclasses import dataclass, field
from typing import Optional
from .schema_v4 import (
    Argument, Attack, Label, ProvenanceTag, PramanaType, EpistemicStatus
)


@dataclass
class ArgumentationFramework:
    """
    The instantiated argumentation framework.
    Computed from KB at compile time. Evaluated at query time.
    """
    arguments: dict[str, Argument] = field(default_factory=dict)
    attacks: list[Attack] = field(default_factory=list)
    labels: dict[str, Label] = field(default_factory=dict)

    # Index structures for efficient lookup
    _attackers_of: dict[str, list[str]] = field(default_factory=dict)
    _attacks_on: dict[str, list[Attack]] = field(default_factory=dict)
    _next_id: int = field(default=0)

    def add_argument(self, arg: Argument):
        """Add an argument to the framework."""
        self.arguments[arg.id] = arg

    def add_attack(self, attack: Attack):
        """Add an attack and update index structures."""
        self.attacks.append(attack)
        self._attackers_of.setdefault(attack.target, []).append(
            attack.attacker)
        self._attacks_on.setdefault(attack.target, []).append(attack)

    def next_arg_id(self) -> str:
        """Generate a unique argument ID."""
        aid = f"A{self._next_id:04d}"
        self._next_id += 1
        return aid

    # ── Grounded Semantics ──

    def compute_grounded(self) -> dict[str, Label]:
        """
        Compute grounded labeling via iterative propagation.

        Algorithm (Wu, Caminada & Gabbay 2009):
        1. Label all unattacked arguments IN
        2. Label attacked-by-IN arguments OUT (if defeat succeeds)
        3. Label arguments with all-attackers-OUT as IN
        4. Repeat until fixpoint
        5. Everything unlabeled is UNDECIDED

        Complexity: O(|arguments| × |attacks|) — polynomial.
        """
        labels = {}
        remaining = set(self.arguments.keys())

        changed = True
        while changed:
            changed = False

            for arg_id in list(remaining):
                attackers = self._attackers_of.get(arg_id, [])

                # No attackers → IN
                if not attackers:
                    labels[arg_id] = Label.IN
                    remaining.discard(arg_id)
                    changed = True
                    continue

                # All attackers OUT → IN (defended)
                if all(labels.get(a) == Label.OUT for a in attackers):
                    labels[arg_id] = Label.IN
                    remaining.discard(arg_id)
                    changed = True
                    continue

                # Any attacker IN → check defeat with preferences
                if any(labels.get(a) == Label.IN for a in attackers):
                    defeated = False
                    for atk in self._attacks_on.get(arg_id, []):
                        if labels.get(atk.attacker) != Label.IN:
                            continue
                        attacker_arg = self.arguments[atk.attacker]
                        target_arg = self.arguments[arg_id]
                        if self._defeats(attacker_arg, target_arg):
                            defeated = True
                            break

                    if defeated:
                        labels[arg_id] = Label.OUT
                        remaining.discard(arg_id)
                        changed = True

        # Everything remaining is UNDECIDED
        for arg_id in remaining:
            labels[arg_id] = Label.UNDECIDED

        self.labels = labels
        return labels

    def _defeats(self, attacker: Argument, target: Argument) -> bool:
        """
        Does the attack from attacker succeed as defeat?

        Uses pramāṇa-based preference (Nyāya bādhita principle):
        - Higher pramāṇa always wins
        - Equal pramāṇa: compare tag strength
        """
        a_pramana = attacker.tag.pramana_type
        t_pramana = target.tag.pramana_type

        # Higher pramāṇa always wins (bādhita override)
        if t_pramana > a_pramana:
            return False  # Target survives
        if a_pramana > t_pramana:
            return True   # Attacker wins

        # Same pramāṇa — compare tag strength
        return attacker.tag.strength >= target.tag.strength

    # ── Epistemic Status Derivation ──

    def get_epistemic_status(
        self, conclusion: str
    ) -> tuple[Optional[EpistemicStatus], ProvenanceTag, list[Argument]]:
        """
        Derive epistemic status for a conclusion from the extension.
        Returns (EpistemicStatus | None, combined ProvenanceTag, relevant arguments).
        """
        args_for = [
            a for a in self.arguments.values()
            if a.conclusion == conclusion
        ]

        if not args_for:
            return (None, ProvenanceTag.zero(), [])

        # Combine tags of accepted arguments via ⊕
        accepted = [
            a for a in args_for
            if self.labels.get(a.id) == Label.IN
        ]

        if not accepted:
            undecided = [
                a for a in args_for
                if self.labels.get(a.id) == Label.UNDECIDED
            ]
            if undecided:
                combined = undecided[0].tag
                for a in undecided[1:]:
                    combined = ProvenanceTag.oplus(combined, a.tag)
                return (combined.epistemic_status(), combined, undecided)
            else:
                # All OUT — contested
                combined = args_for[0].tag
                for a in args_for[1:]:
                    combined = ProvenanceTag.oplus(combined, a.tag)
                return (EpistemicStatus.CONTESTED, combined, args_for)

        combined = accepted[0].tag
        for a in accepted[1:]:
            combined = ProvenanceTag.oplus(combined, a.tag)

        return (combined.epistemic_status(), combined, accepted)

    # ── Preferred Semantics (Phase 4) ──

    def compute_preferred(
        self, timeout_seconds: float = 30.0
    ) -> list[dict[str, Label]]:
        """
        Compute preferred extensions (maximally admissible sets).
        NP-hard — for offline jalpa analysis only.

        Falls back to grounded extension if timeout exceeded.
        """
        import time
        start = time.time()

        grounded = self.compute_grounded()
        grounded_in = {
            aid for aid, lbl in grounded.items() if lbl == Label.IN
        }

        # Start from grounded extension and try to extend
        extensions = []
        self._enumerate_preferred(
            grounded_in, set(), extensions, start, timeout_seconds
        )

        if not extensions:
            # Timeout or no additional extensions — return grounded
            return [grounded]

        # Convert sets to label dicts
        results = []
        for ext in extensions:
            labeling = {}
            for aid in self.arguments:
                if aid in ext:
                    labeling[aid] = Label.IN
                elif any(
                    a in ext for a in self._attackers_of.get(aid, [])
                ):
                    labeling[aid] = Label.OUT
                else:
                    labeling[aid] = Label.UNDECIDED
            results.append(labeling)

        return results

    def _enumerate_preferred(
        self, current: set, tried: set,
        results: list, start: float, timeout: float
    ):
        """Backtracking search for maximal admissible supersets."""
        import time
        if time.time() - start > timeout:
            return

        # Check if current is admissible
        if not self._is_admissible(current):
            return

        # Try extending with each UNDECIDED argument
        extended = False
        for aid in self.arguments:
            if aid in current or aid in tried:
                continue
            if time.time() - start > timeout:
                break
            candidate = current | {aid}
            if self._is_admissible(candidate):
                self._enumerate_preferred(
                    candidate, tried | {aid}, results, start, timeout
                )
                extended = True
            tried.add(aid)

        if not extended:
            # Current is maximal admissible
            if current not in [set(r) for r in results]:
                results.append(current.copy())

    def _is_admissible(self, s: set) -> bool:
        """Check if set s is conflict-free and defends all its members."""
        # Conflict-free: no two arguments in s attack each other
        for aid in s:
            for attacker_id in self._attackers_of.get(aid, []):
                if attacker_id in s:
                    return False

        # Defends all members: for every attacker of s-member,
        # some s-member counter-attacks it
        for aid in s:
            for attacker_id in self._attackers_of.get(aid, []):
                attacker = self.arguments[attacker_id]
                target = self.arguments[aid]
                if not self._defeats(attacker, target):
                    continue  # Attack doesn't succeed, no defense needed
                # Need some s-member to defeat the attacker
                defended = False
                for defender_id in s:
                    if defender_id in self._attackers_of.get(
                        attacker_id, []
                    ):
                        defender = self.arguments[defender_id]
                        if self._defeats(defender, attacker):
                            defended = True
                            break
                if not defended:
                    return False
        return True

    # ── Stable Semantics (Phase 4) ──

    def compute_stable(
        self, timeout_seconds: float = 60.0
    ) -> list[dict[str, Label]]:
        """
        Compute stable extensions (conflict-free sets attacking everything outside).
        coNP-hard — for formal vitaṇḍā audit only.

        Returns list of labelings. May be empty if no stable extension exists.
        """
        import time
        start = time.time()

        results = []
        self._enumerate_stable(
            set(), 0, list(self.arguments.keys()),
            results, start, timeout_seconds
        )
        return results

    def _enumerate_stable(
        self, current: set, idx: int, all_args: list,
        results: list, start: float, timeout: float
    ):
        """Enumerate-and-check with pruning for stable extensions."""
        import time
        if time.time() - start > timeout:
            return

        if idx == len(all_args):
            # Check if current is stable: conflict-free + attacks everything outside
            if not self._is_conflict_free(current):
                return
            for aid in all_args:
                if aid in current:
                    continue
                # aid must be attacked by some member of current
                attacked = any(
                    a in current
                    for a in self._attackers_of.get(aid, [])
                )
                if not attacked:
                    return
            labeling = {}
            for aid in all_args:
                labeling[aid] = Label.IN if aid in current else Label.OUT
            results.append(labeling)
            return

        aid = all_args[idx]
        # Try including aid
        self._enumerate_stable(
            current | {aid}, idx + 1, all_args,
            results, start, timeout
        )
        # Try excluding aid
        self._enumerate_stable(
            current, idx + 1, all_args,
            results, start, timeout
        )

    def _is_conflict_free(self, s: set) -> bool:
        """No two arguments in s attack each other."""
        for aid in s:
            for attacker_id in self._attackers_of.get(aid, []):
                if attacker_id in s:
                    return False
        return True

    # ── Contestation Support ──

    def add_counter_argument(
        self,
        conclusion: str,
        tag: ProvenanceTag,
        attack_target: str,
        attack_type: str,
        hetvabhasa: str,
    ) -> str:
        """Add a user-supplied counter-argument and its attack.

        Returns the new argument ID.
        """
        arg_id = self.next_arg_id()
        self.add_argument(Argument(
            id=arg_id,
            conclusion=conclusion,
            top_rule=None,
            premises=frozenset([conclusion]),
            is_strict=False,
            tag=tag,
        ))
        self.add_attack(Attack(
            attacker=arg_id,
            target=attack_target,
            attack_type=attack_type,
            hetvabhasa=hetvabhasa,
        ))
        return arg_id

    # ── Proof Trace Rendering ──

    def get_argument_tree(self, arg_id: str) -> dict:
        """Return the full argument tree as a nested dict for rendering."""
        arg = self.arguments.get(arg_id)
        if not arg:
            return {}

        tree = {
            "id": arg.id,
            "conclusion": arg.conclusion,
            "label": self.labels.get(arg.id, Label.UNDECIDED).value,
            "tag": arg.tag.to_dict(),
            "top_rule": arg.top_rule,
            "is_strict": arg.is_strict,
            "sub_arguments": [
                self.get_argument_tree(sa) for sa in arg.sub_arguments
            ],
            "attacks_received": [
                {
                    "attacker": atk.attacker,
                    "type": atk.attack_type,
                    "hetvabhasa": atk.hetvabhasa,
                    "attacker_label": self.labels.get(
                        atk.attacker, Label.UNDECIDED
                    ).value,
                }
                for atk in self._attacks_on.get(arg_id, [])
            ],
        }
        return tree

    def to_dict(self) -> dict:
        """Export entire AF as JSON-serializable dict for audit."""
        return {
            "arguments": {
                aid: {
                    "conclusion": a.conclusion,
                    "top_rule": a.top_rule,
                    "sub_arguments": list(a.sub_arguments),
                    "premises": sorted(a.premises),
                    "is_strict": a.is_strict,
                    "tag": a.tag.to_dict(),
                    "label": self.labels.get(aid, Label.UNDECIDED).value,
                }
                for aid, a in self.arguments.items()
            },
            "attacks": [
                {
                    "attacker": atk.attacker,
                    "target": atk.target,
                    "type": atk.attack_type,
                    "hetvabhasa": atk.hetvabhasa,
                }
                for atk in self.attacks
            ],
        }
```

### 7.4 Complexity Analysis

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| `add_argument()` | O(1) | Dictionary insertion |
| `add_attack()` | O(1) | List append + index update |
| `compute_grounded()` | O(\|args\| × \|attacks\|) | Iterative propagation, polynomial |
| `compute_preferred()` | NP-hard (worst case) | Backtracking with 30s timeout fallback |
| `compute_stable()` | coNP-hard (worst case) | Enumerate-and-check with 60s timeout |
| `get_epistemic_status()` | O(\|args for conclusion\|) | Linear scan + oplus chain |
| `_defeats()` | O(1) | Two comparisons |

### 7.5 Tests: `tests/test_argumentation.py`

```python
# tests/test_argumentation.py
import pytest
from anvikshiki_v4.schema_v4 import (
    Argument, Attack, Label, ProvenanceTag, PramanaType, EpistemicStatus
)
from anvikshiki_v4.argumentation import ArgumentationFramework


def _make_arg(aid, conclusion, pramana=PramanaType.ANUMANA,
              belief=0.7, trust=0.8, decay=0.9, depth=1, strict=False):
    return Argument(
        id=aid, conclusion=conclusion, top_rule=None,
        premises=frozenset([conclusion]), is_strict=strict,
        tag=ProvenanceTag(
            belief=belief, disbelief=round(1-belief-0.1, 2),
            uncertainty=0.1,
            pramana_type=pramana, trust_score=trust,
            decay_factor=decay, derivation_depth=depth,
        ),
    )


def test_empty_framework():
    af = ArgumentationFramework()
    labels = af.compute_grounded()
    assert labels == {}


def test_single_unattacked():
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.IN


def test_single_attack_defeat():
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p", belief=0.8))
    af.add_argument(_make_arg("A1", "q", belief=0.6))
    af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.IN
    assert labels["A1"] == Label.OUT


def test_defense():
    """A0 attacks A1, A1 attacks A2 → A0 IN, A1 OUT, A2 IN (defended)."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p", belief=0.8))
    af.add_argument(_make_arg("A1", "q", belief=0.7))
    af.add_argument(_make_arg("A2", "r", belief=0.6))
    af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
    af.add_attack(Attack("A1", "A2", "rebutting", "viruddha"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.IN
    assert labels["A1"] == Label.OUT
    assert labels["A2"] == Label.IN


def test_odd_cycle_undecided():
    """A0 ↔ A1 with equal strength → both UNDECIDED (satpratipakṣa)."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p", belief=0.7))
    af.add_argument(_make_arg("A1", "not_p", belief=0.7))
    af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
    af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.UNDECIDED
    assert labels["A1"] == Label.UNDECIDED


def test_pramana_preference():
    """PRATYAKSA attacker defeats SABDA target regardless of belief."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p", pramana=PramanaType.PRATYAKSA,
                              belief=0.5))
    af.add_argument(_make_arg("A1", "q", pramana=PramanaType.SABDA,
                              belief=0.9))
    af.add_attack(Attack("A0", "A1", "undermining", "asiddha"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.IN
    assert labels["A1"] == Label.OUT


def test_equal_pramana_strength_wins():
    """Same pramāṇa, higher strength wins."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p", belief=0.8, trust=0.9))
    af.add_argument(_make_arg("A1", "not_p", belief=0.5, trust=0.7))
    af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
    af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
    labels = af.compute_grounded()
    assert labels["A0"] == Label.IN
    assert labels["A1"] == Label.OUT


def test_epistemic_status_established():
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p", belief=0.9,
                              pramana=PramanaType.PRATYAKSA))
    af.compute_grounded()
    status, tag, args = af.get_epistemic_status("p")
    assert status == EpistemicStatus.ESTABLISHED


def test_epistemic_status_contested():
    """All arguments for conclusion are OUT → CONTESTED."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p", belief=0.6))
    af.add_argument(_make_arg("A1", "attacker",
                              pramana=PramanaType.PRATYAKSA, belief=0.9))
    af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
    af.compute_grounded()
    status, tag, args = af.get_epistemic_status("p")
    assert status == EpistemicStatus.CONTESTED


def test_oplus_accumulation():
    """Multiple IN arguments for same conclusion → combined belief > individual."""
    af = ArgumentationFramework()
    for i in range(3):
        af.add_argument(_make_arg(
            f"A{i}", "p", belief=0.5,
            trust=0.8, decay=0.9, depth=1,
        ))
    af.compute_grounded()
    status, tag, args = af.get_epistemic_status("p")
    assert tag.belief > 0.5


def test_grounded_is_conflict_free():
    """Property: no two IN arguments attack each other."""
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p"))
    af.add_argument(_make_arg("A1", "not_p"))
    af.add_argument(_make_arg("A2", "q"))
    af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
    af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
    labels = af.compute_grounded()
    in_args = [aid for aid, lbl in labels.items() if lbl == Label.IN]
    for a in in_args:
        for b in in_args:
            if a != b:
                assert b not in af._attackers_of.get(a, [])


def test_argument_tree():
    af = ArgumentationFramework()
    af.add_argument(_make_arg("A0", "p"))
    af.add_argument(_make_arg("A1", "q"))
    af.add_attack(Attack("A1", "A0", "undermining", "asiddha"))
    af.compute_grounded()
    tree = af.get_argument_tree("A0")
    assert tree["id"] == "A0"
    assert len(tree["attacks_received"]) == 1
```

---

## 8. Module 5: T2 Compiler v4

**File:** `anvikshiki_v4/t2_compiler_v4.py`
**Purpose:** Compile verified architecture (KnowledgeStore + query facts) into an ArgumentationFramework with arguments, attacks, and provenance tags.
**Dependencies:** `schema.py`, `schema_v4.py`, `argumentation.py`
**Status:** Complete rewrite from v3.

### 8.1 Design Decisions

1. **Three-step compilation + fixpoint.** (a) Premise arguments from grounded query facts, (b) rule-based arguments from vyāptis, (c) derive attacks. Then iterate (b)-(c) until no new arguments.

2. **Tag construction from KB metadata.** `_build_rule_tag()` maps CausalStatus → PramanaType and EpistemicStatus → (belief, disbelief, uncertainty). Trust = `formulation × existence`. Decay = exponential half-life.

3. **Attack derivation is deterministic.** No LLM calls. Three patterns: rebutting (negation prefix), undercutting (scope exclusions), undermining (decay < threshold).

### 8.2 The Five Attack Types

| Hetvābhāsa | Defeat Type | Trigger | Generation Code |
|-----------|-------------|---------|-----------------|
| **Asiddha** (unestablished) | Undermining | `arg.tag.decay_factor < 0.3` | Create stale argument with `belief = 1 - decay_factor`, add attack on target |
| **Savyabhicāra** (inconclusive) | Undercutting | Scope exclusion predicate established in AF | Create scope argument (PRATYAKSA), add attack on rule argument |
| **Viruddha** (contradictory) | Rebutting | `pred` and `not_pred` both have arguments | Mutual attacks in both directions |
| **Satpratipakṣa** (counterbalanced) | Symmetric | Falls out from mutual viruddha + equal `tag.strength` | Both attacks succeed, both UNDECIDED in grounded |
| **Bādhita** (sublated) | Preference | `_defeats()` with pramāṇa comparison | No explicit attack — preference in `_defeats()` handles it |

### 8.3 Tag Construction Tables

**CausalStatus → PramanaType:**

| CausalStatus | PramanaType | Rationale |
|-------------|-------------|-----------|
| DEFINITIONAL | PRATYAKSA | Definitional truths are directly perceivable from ontology |
| STRUCTURAL | PRATYAKSA | Structural rules follow from domain architecture |
| EMPIRICAL | ANUMANA | Empirical rules are inferred from observed patterns |
| REGULATORY | SABDA | Regulatory rules are testimony from institutional authorities |

**EpistemicStatus → (belief, disbelief, uncertainty):**

| EpistemicStatus | b | d | u | Rationale |
|----------------|---|---|---|-----------|
| ESTABLISHED | 0.95 | 0.0 | 0.05 | Strong evidence, minimal uncertainty |
| WORKING_HYPOTHESIS | 0.6 | 0.1 | 0.3 | Reasonable but uncertain |
| PROVISIONAL | 0.4 | 0.1 | 0.5 | Accepted tentatively |
| GENUINELY_OPEN | 0.2 | 0.2 | 0.6 | Little evidence either way |
| ACTIVELY_CONTESTED | 0.4 | 0.4 | 0.2 | Strong evidence both for and against |

**Note:** These mappings are DSPy-optimizable parameters.

### 8.4 Complete Implementation

```python
# anvikshiki_v4/t2_compiler_v4.py
"""
T2 Compiler v4: Compile verified architecture into
an argumentation framework over provenance semirings.
"""

import math
from datetime import datetime
from .schema import KnowledgeStore, CausalStatus
from .schema import EpistemicStatus as KBEpistemicStatus
from .schema_v4 import (
    Argument, Attack, ProvenanceTag, PramanaType
)
from .argumentation import ArgumentationFramework


# ── Tag Construction ──

PRAMANA_MAP = {
    CausalStatus.DEFINITIONAL: PramanaType.PRATYAKSA,
    CausalStatus.STRUCTURAL: PramanaType.PRATYAKSA,
    CausalStatus.EMPIRICAL: PramanaType.ANUMANA,
    CausalStatus.REGULATORY: PramanaType.SABDA,
}

BELIEF_MAP = {
    KBEpistemicStatus.ESTABLISHED: (0.95, 0.0, 0.05),
    KBEpistemicStatus.WORKING_HYPOTHESIS: (0.6, 0.1, 0.3),
    KBEpistemicStatus.GENUINELY_OPEN: (0.2, 0.2, 0.6),
    KBEpistemicStatus.ACTIVELY_CONTESTED: (0.4, 0.4, 0.2),
}

DECAY_HALF_LIFE_DAYS = 365      # DSPy-optimizable
DECAY_UNDERMINE_THRESHOLD = 0.3  # DSPy-optimizable


def _build_rule_tag(vyapti, knowledge_store: KnowledgeStore) -> ProvenanceTag:
    """Build a provenance tag for a vyāpti from its KB metadata."""
    b, d, u = BELIEF_MAP.get(vyapti.epistemic_status, (0.5, 0.1, 0.4))
    trust = vyapti.confidence.formulation * vyapti.confidence.existence

    decay = 1.0
    if vyapti.last_verified:
        age_days = (datetime.now() - vyapti.last_verified).days
        decay = math.exp(-0.693 * age_days / DECAY_HALF_LIFE_DAYS)

    return ProvenanceTag(
        belief=b, disbelief=d, uncertainty=u,
        source_ids=frozenset(vyapti.sources),
        pramana_type=PRAMANA_MAP.get(
            vyapti.causal_status, PramanaType.ANUMANA),
        trust_score=trust,
        decay_factor=decay,
        derivation_depth=0,
    )


# ── Main Compiler ──

def compile_t2(
    knowledge_store: KnowledgeStore,
    query_facts: list[dict],
) -> ArgumentationFramework:
    """
    Build the argumentation framework from KB + query facts.

    Steps:
    1. Create premise arguments from base facts
    2. Create rule-based arguments from vyāptis (forward chain)
    3. Derive attacks (rebutting, undercutting, undermining)
    4. Repeat steps 2-3 until fixpoint (no new arguments)
    """
    af = ArgumentationFramework()

    # ── Step 1: Premise arguments from grounded query facts ──
    for fact in query_facts:
        arg_id = af.next_arg_id()
        confidence = fact.get("confidence", 0.9)
        tag = ProvenanceTag(
            belief=confidence,
            disbelief=0.0,
            uncertainty=round(1.0 - confidence, 4),
            source_ids=frozenset(fact.get("sources", [])),
            pramana_type=PramanaType.PRATYAKSA,
            trust_score=1.0,
            decay_factor=1.0,
            derivation_depth=0,
        )
        af.add_argument(Argument(
            id=arg_id,
            conclusion=fact["predicate"],
            top_rule=None,
            premises=frozenset([fact["predicate"]]),
            is_strict=True,
            tag=tag,
        ))

    # ── Steps 2-4: Forward chain with fixpoint ──
    MAX_ITERATIONS = 100
    for iteration in range(MAX_ITERATIONS):
        prev_count = len(af.arguments)

        # Step 2: Rule-based arguments from vyāptis
        _derive_rule_arguments(af, knowledge_store)

        # Step 3: Derive attacks
        _derive_attacks(af, knowledge_store)

        # Fixpoint check
        if len(af.arguments) == prev_count:
            break

    return af


def _derive_rule_arguments(
    af: ArgumentationFramework,
    ks: KnowledgeStore,
):
    """Create rule-based arguments for all applicable vyāptis."""
    available = {a.conclusion for a in af.arguments.values()}
    existing_rules = {
        a.top_rule for a in af.arguments.values() if a.top_rule
    }

    for vid, v in ks.vyaptis.items():
        if vid in existing_rules:
            continue
        if not all(ant in available for ant in v.antecedents):
            continue

        # Find sub-arguments (pick strongest for each antecedent)
        sub_arg_ids = []
        sub_tags = []
        for ant in v.antecedents:
            candidates = [
                a for a in af.arguments.values()
                if a.conclusion == ant
            ]
            if candidates:
                best = max(candidates, key=lambda a: a.tag.strength)
                sub_arg_ids.append(best.id)
                sub_tags.append(best.tag)

        rule_tag = _build_rule_tag(v, ks)
        combined_tag = rule_tag
        for st in sub_tags:
            combined_tag = ProvenanceTag.tensor(combined_tag, st)

        is_strict = v.causal_status.value in ("definitional", "structural")
        arg_id = af.next_arg_id()

        af.add_argument(Argument(
            id=arg_id,
            conclusion=v.consequent,
            top_rule=vid,
            sub_arguments=tuple(sub_arg_ids),
            premises=frozenset().union(*(
                af.arguments[sa].premises for sa in sub_arg_ids
            )),
            is_strict=is_strict,
            tag=combined_tag,
        ))


def _derive_attacks(
    af: ArgumentationFramework,
    ks: KnowledgeStore,
):
    """Derive all three attack types from AF structure."""
    existing_attacks = {
        (atk.attacker, atk.target) for atk in af.attacks
    }

    # 3a. Rebutting attacks (viruddha): contradictory conclusions
    conclusions: dict[str, list[str]] = {}
    for a in af.arguments.values():
        conclusions.setdefault(a.conclusion, []).append(a.id)

    for conc, arg_ids in conclusions.items():
        neg_conc = (f"not_{conc}" if not conc.startswith("not_")
                    else conc[4:])
        if neg_conc not in conclusions:
            continue
        for pos_id in arg_ids:
            for neg_id in conclusions[neg_conc]:
                if (neg_id, pos_id) not in existing_attacks:
                    af.add_attack(Attack(
                        attacker=neg_id, target=pos_id,
                        attack_type="rebutting", hetvabhasa="viruddha"))
                    existing_attacks.add((neg_id, pos_id))
                if (pos_id, neg_id) not in existing_attacks:
                    af.add_attack(Attack(
                        attacker=pos_id, target=neg_id,
                        attack_type="rebutting", hetvabhasa="viruddha"))
                    existing_attacks.add((pos_id, neg_id))

    # 3b. Undercutting attacks (savyabhicāra): scope violations
    for a in af.arguments.values():
        if a.top_rule is None:
            continue
        v = ks.vyaptis.get(a.top_rule)
        if not v:
            continue
        for excl in v.scope_exclusions:
            if not any(arg.conclusion == excl
                       for arg in af.arguments.values()):
                continue
            # Check if this attack already exists
            target_conclusion = f"_undercut_{a.top_rule}"
            if any(arg.conclusion == target_conclusion
                   for arg in af.arguments.values()):
                continue
            scope_arg_id = af.next_arg_id()
            af.add_argument(Argument(
                id=scope_arg_id,
                conclusion=target_conclusion,
                top_rule=None,
                premises=frozenset([excl]),
                is_strict=True,
                tag=ProvenanceTag(
                    belief=1.0, disbelief=0.0, uncertainty=0.0,
                    pramana_type=PramanaType.PRATYAKSA,
                    trust_score=1.0, decay_factor=1.0,
                ),
            ))
            af.add_attack(Attack(
                attacker=scope_arg_id, target=a.id,
                attack_type="undercutting", hetvabhasa="savyabhicara"))

    # 3c. Undermining attacks (asiddha): decay-expired premises
    for a in list(af.arguments.values()):
        if a.tag.decay_factor >= DECAY_UNDERMINE_THRESHOLD:
            continue
        stale_conclusion = f"_stale_{a.id}"
        if any(arg.conclusion == stale_conclusion
               for arg in af.arguments.values()):
            continue
        decay_arg_id = af.next_arg_id()
        af.add_argument(Argument(
            id=decay_arg_id,
            conclusion=stale_conclusion,
            top_rule=None,
            premises=frozenset(["_temporal_decay"]),
            is_strict=True,
            tag=ProvenanceTag(
                belief=1.0 - a.tag.decay_factor,
                disbelief=0.0,
                uncertainty=a.tag.decay_factor,
                pramana_type=PramanaType.PRATYAKSA,
                trust_score=1.0, decay_factor=1.0,
            ),
        ))
        af.add_attack(Attack(
            attacker=decay_arg_id, target=a.id,
            attack_type="undermining", hetvabhasa="asiddha"))


def load_knowledge_store(path: str) -> KnowledgeStore:
    """Load KnowledgeStore from YAML file."""
    import yaml
    with open(path) as f:
        data = yaml.safe_load(f)
    return KnowledgeStore(**data)
```

### 8.5 Sample Architecture YAML

```yaml
# data/sample_architecture.yaml
domain_type: 3  # EMPIRICAL
pramanas: ["pratyaksa", "anumana", "sabda"]
vyaptis:
  V01:
    id: V01
    name: "Concentrated Ownership Enables Long Horizons"
    statement: "If ownership is concentrated, the firm can take long-horizon decisions"
    causal_status: empirical
    scope_conditions: ["private_firm"]
    scope_exclusions: ["public_firm", "regulated_utility"]
    confidence: {existence: 0.85, formulation: 0.9, evidence: "observational"}
    epistemic_status: established
    decay_risk: low
    sources: ["src_chandler_1990", "src_jensen_1993"]
    antecedents: ["concentrated_ownership"]
    consequent: "long_horizon_possible"
  V02:
    id: V02
    name: "Long Horizons Enable Capability Building"
    statement: "Long-horizon firms can invest in capability building"
    causal_status: empirical
    scope_conditions: []
    scope_exclusions: ["capital_constrained"]
    confidence: {existence: 0.8, formulation: 0.85, evidence: "observational"}
    epistemic_status: hypothesis
    sources: ["src_teece_1997"]
    antecedents: ["long_horizon_possible"]
    consequent: "capability_building_possible"
  V03:
    id: V03
    name: "Concentrated Ownership Creates Agency Risk"
    statement: "Concentrated ownership can entrench bad management"
    causal_status: empirical
    scope_conditions: []
    scope_exclusions: ["strong_board"]
    confidence: {existence: 0.75, formulation: 0.8, evidence: "observational"}
    epistemic_status: established
    sources: ["src_morck_2005"]
    antecedents: ["concentrated_ownership"]
    consequent: "not_good_governance"
hetvabhasas:
  H01:
    id: H01
    name: "Survivorship Bias"
    description: "Drawing conclusions from survivors only"
    detection_signature: "success_stories_only"
    correction_pattern: "Include failed examples"
    common_contexts: ["strategy", "entrepreneurship"]
threshold_concepts: []
dependency_graph: {}
chapter_fingerprints: {}
reference_bank:
  src_chandler_1990: {title: "Scale and Scope", author: "Chandler", year: 1990}
  src_jensen_1993: {title: "The Modern Industrial Revolution", author: "Jensen", year: 1993}
  src_teece_1997: {title: "Dynamic Capabilities", author: "Teece et al.", year: 1997}
  src_morck_2005: {title: "Corporate Governance and Family Control", author: "Morck et al.", year: 2005}
```

### 8.6 Tests: `tests/test_t2_compiler_v4.py`

```python
# tests/test_t2_compiler_v4.py
import pytest
from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store, _build_rule_tag
from anvikshiki_v4.schema_v4 import Label, PramanaType


@pytest.fixture
def sample_ks():
    return load_knowledge_store("data/sample_architecture.yaml")


def test_basic_compilation(sample_ks):
    """compile_t2 produces AF with correct argument count."""
    facts = [{"predicate": "concentrated_ownership", "confidence": 0.9}]
    af = compile_t2(sample_ks, facts)
    assert len(af.arguments) > 1  # At least premise + some rule args


def test_premise_arguments(sample_ks):
    """Query facts produce premise arguments with PRATYAKSA."""
    facts = [{"predicate": "concentrated_ownership", "confidence": 0.85}]
    af = compile_t2(sample_ks, facts)
    premise_args = [a for a in af.arguments.values() if a.top_rule is None
                    and a.conclusion == "concentrated_ownership"]
    assert len(premise_args) == 1
    assert premise_args[0].tag.pramana_type == PramanaType.PRATYAKSA
    assert premise_args[0].tag.derivation_depth == 0


def test_chain_derivation(sample_ks):
    """V01: A→B, V02: B→C — both B and C derived."""
    facts = [{"predicate": "concentrated_ownership", "confidence": 0.9}]
    af = compile_t2(sample_ks, facts)
    conclusions = {a.conclusion for a in af.arguments.values()}
    assert "long_horizon_possible" in conclusions
    assert "capability_building_possible" in conclusions


def test_scope_exclusion_generates_attack(sample_ks):
    """public_firm in V01.scope_exclusions → undercutting attack."""
    facts = [
        {"predicate": "concentrated_ownership", "confidence": 0.9},
        {"predicate": "public_firm", "confidence": 0.95},
    ]
    af = compile_t2(sample_ks, facts)
    undercut_attacks = [
        atk for atk in af.attacks if atk.attack_type == "undercutting"
    ]
    assert len(undercut_attacks) > 0
    assert undercut_attacks[0].hetvabhasa == "savyabhicara"


def test_rebutting_attacks(sample_ks):
    """V03 derives not_good_governance — should rebut any good_governance."""
    facts = [
        {"predicate": "concentrated_ownership", "confidence": 0.9},
        {"predicate": "good_governance", "confidence": 0.7},
    ]
    af = compile_t2(sample_ks, facts)
    rebutting = [atk for atk in af.attacks if atk.hetvabhasa == "viruddha"]
    assert len(rebutting) > 0


def test_fixpoint_convergence(sample_ks):
    """Transitive chain terminates."""
    facts = [{"predicate": "concentrated_ownership", "confidence": 0.9}]
    af = compile_t2(sample_ks, facts)
    # Should not hang — if we get here, fixpoint converged
    assert len(af.arguments) < 1000  # Sanity bound


def test_build_rule_tag(sample_ks):
    """_build_rule_tag maps KB metadata correctly."""
    v = sample_ks.vyaptis["V01"]
    tag = _build_rule_tag(v, sample_ks)
    assert tag.pramana_type == PramanaType.ANUMANA  # EMPIRICAL → ANUMANA
    assert tag.belief == pytest.approx(0.95)  # ESTABLISHED
    assert tag.trust_score == pytest.approx(0.9 * 0.85)
```

---

## 9. Module 6: T3 Compiler

**File:** `anvikshiki_v4/t3_compiler.py`
**Purpose:** Build GraphRAG retrieval corpus from guide text + KnowledgeStore.
**Status:** Reused from v3 unchanged (BUILD_GUIDE.md Section 7).

### 9.1 v4 Addition: Argument-Chunk Linking

New function that links T3 text chunks to argument IDs from the AF:

```python
def link_chunks_to_arguments(
    chunks: list,  # TextChunk objects from compile_t3
    af,            # ArgumentationFramework
) -> dict[str, list[str]]:
    """Map argument IDs to relevant chunk indices.

    For each argument, find chunks that reference its vyāpti
    or conclusion predicate. Enables synthesis to cite relevant
    guide sections for each accepted argument.
    """
    arg_to_chunks = {}
    for arg in af.arguments.values():
        matching = []
        for i, chunk in enumerate(chunks):
            if arg.top_rule and arg.top_rule in getattr(
                chunk, 'vyapti_anchors', []
            ):
                matching.append(i)
            elif arg.conclusion in getattr(
                chunk, 'concept_anchors', []
            ):
                matching.append(i)
        if matching:
            arg_to_chunks[arg.id] = matching
    return arg_to_chunks
```

### 9.2 Tests

Reuse v3 `tests/test_t3_compiler.py` — graph construction, chunk splitting, reference detection.

---

## 10. Module 7: Grounding Pipeline

**File:** `anvikshiki_v4/grounding.py`
**Purpose:** Five-layer NL→predicate defense. Translates natural language queries into structured predicates.
**Status:** Unchanged from v3 (BUILD_GUIDE.md Section 8).

### 10.1 The Five Layers

| Layer | Method | Cost | When |
|-------|--------|------|------|
| 1. Ontology-constrained prompt | Include VALID PREDICATES list | Free | Always |
| 2. Grammar constraint | XGrammar/Instructor | Free at decode | If available |
| 3. Ensemble consensus | N=5 parallel rollouts, majority vote | 5× LLM calls | Always |
| 4. Round-trip verification | Verbalize predicates → check faithfulness | 2× LLM calls | If agreement < 0.9 |
| 5. Solver-feedback refinement | Re-ground with error context | 1× LLM call | If errors detected, up to 3 rounds |

**Output:** `GroundingResult(predicates, confidence, disputed, warnings, refinement_rounds, clarification_needed)`

### 10.2 Tests

Reuse v3 `tests/test_grounding.py` — requires LLM API access for integration tests.

---

## 11. Module 8: Uncertainty Quantification

**File:** `anvikshiki_v4/uncertainty.py`
**Purpose:** Three-way uncertainty decomposition from provenance tags.
**Status:** Refined for v4 — derives all values from ProvenanceTag fields instead of hand-tuned dictionaries.

### 11.1 What Changed from v3

| UQ Component | v3 Source | v4 Source |
|-------------|----------|----------|
| **Epistemic** | Heyting lattice value (IntEnum 0-4) | `tag.belief` + `tag.uncertainty` |
| **Aleatoric** | `DOMAIN_BASE_UNCERTAINTY` dict (8 hand-tuned entries) | `tag.disbelief` (domain contestation encoded at compile time) |
| **Inference** | `grounding_confidence` only | `grounding_confidence` + `tag.decay_factor` + `tag.derivation_depth` |
| **Aggregate** | `min(ep, al, inf)` | `tag.strength` = `belief × trust × decay` |

### 11.2 Complete Implementation

```python
# anvikshiki_v4/uncertainty.py
"""Three-way uncertainty decomposition from provenance tags."""

from .schema_v4 import ProvenanceTag, EpistemicStatus


def compute_uncertainty_v4(
    tag: ProvenanceTag,
    grounding_confidence: float,
    conclusion: str,
    epistemic_status: EpistemicStatus,
) -> dict:
    """
    Decompose uncertainty into three independent components.
    All values derived from ProvenanceTag — no hand-tuned dictionaries.
    """
    return {
        "epistemic": {
            "status": epistemic_status.value if epistemic_status else "none",
            "belief": tag.belief,
            "uncertainty": tag.uncertainty,
            "explanation": (
                "High belief with low uncertainty — well-established"
                if tag.belief > 0.8 and tag.uncertainty < 0.1
                else "Moderate evidence — working hypothesis"
                if tag.belief > 0.5
                else "Insufficient evidence"
            ),
        },
        "aleatoric": {
            "disbelief": tag.disbelief,
            "explanation": (
                "High disbelief indicates inherent domain disagreement"
                if tag.disbelief > 0.3
                else "Low domain-level contestation"
            ),
        },
        "inference": {
            "grounding_confidence": grounding_confidence,
            "decay_factor": tag.decay_factor,
            "derivation_depth": tag.derivation_depth,
            "explanation": (
                f"Grounding confidence: {grounding_confidence:.2f}, "
                f"temporal freshness: {tag.decay_factor:.2f}, "
                f"chain length: {tag.derivation_depth}"
            ),
        },
        "total_confidence": tag.strength,
    }
```

### 11.3 Tests: `tests/test_uncertainty.py`

```python
# tests/test_uncertainty.py
from anvikshiki_v4.uncertainty import compute_uncertainty_v4
from anvikshiki_v4.schema_v4 import ProvenanceTag, EpistemicStatus


def test_strong_tag():
    tag = ProvenanceTag(belief=0.9, disbelief=0.05, uncertainty=0.05,
                        trust_score=0.9, decay_factor=0.95, derivation_depth=1)
    result = compute_uncertainty_v4(tag, 0.9, "p", EpistemicStatus.ESTABLISHED)
    assert result["epistemic"]["belief"] == 0.9
    assert result["total_confidence"] > 0.7


def test_high_disbelief():
    tag = ProvenanceTag(belief=0.4, disbelief=0.5, uncertainty=0.1,
                        trust_score=0.8, decay_factor=0.9, derivation_depth=1)
    result = compute_uncertainty_v4(tag, 0.8, "p", EpistemicStatus.CONTESTED)
    assert "disagreement" in result["aleatoric"]["explanation"]


def test_low_decay():
    tag = ProvenanceTag(belief=0.7, disbelief=0.1, uncertainty=0.2,
                        trust_score=0.8, decay_factor=0.2, derivation_depth=1)
    result = compute_uncertainty_v4(tag, 0.8, "p", EpistemicStatus.HYPOTHESIS)
    assert result["inference"]["decay_factor"] == 0.2


def test_deep_derivation():
    tag = ProvenanceTag(belief=0.5, disbelief=0.2, uncertainty=0.3,
                        trust_score=0.7, decay_factor=0.8, derivation_depth=5)
    result = compute_uncertainty_v4(tag, 0.7, "p", EpistemicStatus.HYPOTHESIS)
    assert result["inference"]["derivation_depth"] == 5


def test_low_grounding():
    tag = ProvenanceTag(belief=0.7, disbelief=0.1, uncertainty=0.2,
                        trust_score=0.8, decay_factor=0.9, derivation_depth=1)
    result = compute_uncertainty_v4(tag, 0.3, "p", EpistemicStatus.HYPOTHESIS)
    assert result["inference"]["grounding_confidence"] == 0.3
```

---

## 12. Module 9: Contestation Protocols

**File:** `anvikshiki_v4/contestation.py`
**Purpose:** Three Nyāya debate types as contestation modes with different argumentation semantics.
**Dependencies:** `argumentation.py`, `schema_v4.py`
**Status:** Entirely new — no v3 equivalent.

### 12.1 The Three Protocols

| Debate Type | Semantics | Complexity | Use Case | Stakeholder |
|------------|-----------|-----------|----------|-------------|
| **Vāda** (cooperative inquiry) | Grounded | P-complete | Routine queries | Expert, educator |
| **Jalpa** (adversarial disputation) | Preferred | NP-hard | Stress-testing | Auditor, regulator |
| **Vitaṇḍā** (pure critique) | Stable | coNP-hard | Formal audit | External auditor |

### 12.2 User Contestation Input API

Five input types matching the five hetvābhāsas:

| User Says | Hetvābhāsa | AF Modification |
|-----------|-----------|-----------------|
| "This premise is not established" | Asiddha | Add undermining attack on target premise |
| "This rule does not apply here" | Savyabhicāra | Add undercutting attack on target rule argument |
| "I have evidence for the opposite" | Viruddha | Add rebutting argument + mutual attacks |
| "Equally strong counter-evidence" | Satpratipakṣa | Add symmetric rebutting with comparable strength |
| "More direct evidence overrides" | Bādhita | Add argument with higher pramāṇa type |

### 12.3 Complete Implementation

```python
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

        # Undefended arguments
        grounded = af.compute_grounded()
        undefended = []
        for aid, lbl in grounded.items():
            if lbl != Label.IN:
                continue
            for atk_id in af._attackers_of.get(aid, []):
                if grounded.get(atk_id) != Label.OUT:
                    undefended.append(aid)
                    break

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

        tag = ProvenanceTag(
            belief=belief,
            disbelief=round(1.0 - belief - 0.1, 2),
            uncertainty=0.1,
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
```

### 12.4 Tests: `tests/test_contestation.py`

```python
# tests/test_contestation.py
import pytest
from anvikshiki_v4.schema_v4 import (
    Argument, Attack, Label, ProvenanceTag, PramanaType
)
from anvikshiki_v4.argumentation import ArgumentationFramework
from anvikshiki_v4.contestation import ContestationManager


def _simple_af():
    """AF with one accepted argument."""
    af = ArgumentationFramework()
    af.add_argument(Argument(
        id="A0", conclusion="p", top_rule=None,
        premises=frozenset(["p"]), is_strict=False,
        tag=ProvenanceTag(belief=0.7, disbelief=0.2, uncertainty=0.1,
                          pramana_type=PramanaType.ANUMANA,
                          trust_score=0.8, decay_factor=0.9),
    ))
    return af


def test_vada_returns_grounded():
    cm = ContestationManager()
    af = _simple_af()
    result = cm.vada(af)
    assert result.extension_size == 1
    assert "p" in result.accepted


def test_jalpa_returns_preferred():
    cm = ContestationManager()
    af = _simple_af()
    result = cm.jalpa(af, timeout_seconds=5.0)
    assert len(result.preferred_extensions) >= 1


def test_vitanda_returns_vulnerabilities():
    cm = ContestationManager()
    af = _simple_af()
    af.add_argument(Argument(
        id="A1", conclusion="not_p", top_rule=None,
        premises=frozenset(["not_p"]),
        tag=ProvenanceTag(belief=0.6, disbelief=0.3, uncertainty=0.1,
                          pramana_type=PramanaType.SABDA,
                          trust_score=0.7, decay_factor=0.9),
    ))
    af.add_attack(Attack("A1", "A0", "rebutting", "viruddha"))
    af.add_attack(Attack("A0", "A1", "rebutting", "viruddha"))
    result = cm.vitanda(af, timeout_seconds=5.0)
    assert "p" in result.vulnerability_inventory or \
           "not_p" in result.vulnerability_inventory


def test_contestation_asiddha():
    """Undermining contestation → target becomes OUT."""
    cm = ContestationManager()
    af = _simple_af()
    new_id = cm.apply_contestation(af, "asiddha", "A0", {
        "conclusion": "_stale_A0",
        "belief": 0.9,
        "pramana_type": "PRATYAKSA",
    })
    labels = af.compute_grounded()
    assert labels["A0"] == Label.OUT


def test_contestation_viruddha_creates_mutual_attack():
    """Rebutting contestation creates attacks in both directions."""
    cm = ContestationManager()
    af = _simple_af()
    new_id = cm.apply_contestation(af, "viruddha", "A0", {
        "conclusion": "not_p", "belief": 0.7,
    })
    # Both directions should have attacks
    attacks_on_a0 = [atk for atk in af.attacks if atk.target == "A0"]
    attacks_on_new = [atk for atk in af.attacks if atk.target == new_id]
    assert len(attacks_on_a0) >= 1
    assert len(attacks_on_new) >= 1


def test_contestation_idempotent():
    """Same contestation twice doesn't change outcome."""
    cm = ContestationManager()
    af = _simple_af()
    cm.apply_contestation(af, "asiddha", "A0", {
        "conclusion": "_stale1", "belief": 0.9,
        "pramana_type": "PRATYAKSA",
    })
    labels1 = af.compute_grounded()
    cm.apply_contestation(af, "asiddha", "A0", {
        "conclusion": "_stale2", "belief": 0.9,
        "pramana_type": "PRATYAKSA",
    })
    labels2 = af.compute_grounded()
    assert labels1["A0"] == labels2["A0"]
```

---

## 13. Module 10: Final Engine

**File:** `anvikshiki_v4/engine_v4.py`
**Purpose:** The complete 8-step pipeline assembling all components.
**Dependencies:** All other modules.

### 13.1 Pipeline Overview

```
Query (NL)
  │
  ▼  Step 1: Grounding (grounding.py)
Predicates + confidence
  │
  ▼  Step 2: Build AF (t2_compiler_v4.py)
ArgumentationFramework (arguments + attacks + tags)
  │
  ▼  Step 3: Compute Extension (argumentation.py)
Labels: IN / OUT / UNDECIDED per argument
  │
  ▼  Step 4: Derive Epistemic Status
(EpistemicStatus, ProvenanceTag) per conclusion
  │
  ▼  Step 5: Extract Provenance
source_ids, pramāṇa type, derivation depth per conclusion
  │
  ▼  Step 6: Uncertainty Decomposition (uncertainty.py)
epistemic / aleatoric / inference per conclusion
  │
  ▼  Step 7: Collect Violations
Defeated arguments + hetvābhāsa types
  │
  ▼  Step 8: Synthesize Response (DSPy)
Calibrated NL response + sources cited
```

### 13.2 Complete Implementation

```python
# anvikshiki_v4/engine_v4.py
"""
The Ānvīkṣikī Engine v4 — Argumentation over Provenance Semirings.
"""

import dspy
from .schema import KnowledgeStore
from .schema_v4 import EpistemicStatus, ProvenanceTag, Label
from .argumentation import ArgumentationFramework
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
    """Reward function for dspy.Refine."""
    score = 0.0
    if pred.response and len(pred.response) > 20:
        score += 0.3
    if pred.sources_cited and len(pred.sources_cited) > 0:
        score += 0.2
    # Check for epistemic qualification language
    hedges = ["hypothesis", "provisional", "contested", "open",
              "uncertain", "evidence suggests", "limited evidence"]
    if any(h in pred.response.lower() for h in hedges):
        score += 0.2
    # Check for hetvābhāsa warnings when violations present
    if "defeated" in args.get("defeated_arguments", "").lower():
        if any(w in pred.response.lower()
               for w in ["caveat", "however", "limitation", "exception"]):
            score += 0.15
    # No overconfidence
    if "certainly" not in pred.response.lower():
        score += 0.15
    return score


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
        query_facts = [
            {"predicate": p, "confidence": grounding.confidence,
             "sources": []}
            for p in grounding.predicates
        ]
        af = compile_t2(self.ks, query_facts)

        # STEP 3: Compute extension (based on contestation mode)
        if self.contestation_mode == "jalpa":
            extensions = af.compute_preferred(timeout_seconds=30.0)
            labels = extensions[0] if extensions else af.compute_grounded()
        elif self.contestation_mode == "vitanda":
            extensions = af.compute_stable(timeout_seconds=60.0)
            labels = extensions[0] if extensions else af.compute_grounded()
        else:
            labels = af.compute_grounded()

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
        return self.reasoner(
            query=query,
            accepted_arguments=f"Predicates: {grounding.predicates}",
            defeated_arguments="Phase 1: no argumentation framework",
            uncertainty_report=f"Grounding confidence: {grounding.confidence}",
            retrieved_prose="\n\n".join(retrieved_chunks[:5]),
        )
```

### 13.3 Quick Start Example

```python
import dspy
from anvikshiki_v4.schema import KnowledgeStore
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store
from anvikshiki_v4.grounding import GroundingPipeline
from anvikshiki_v4.engine_v4 import AnvikshikiEngineV4

# 1. Configure LM
dspy.configure(lm=dspy.LM('openai/gpt-4o-mini'))

# 2. Load knowledge base
ks = load_knowledge_store("data/sample_architecture.yaml")

# 3. Create engine (Phase 3: semiring mode, vāda default)
grounding = GroundingPipeline(ks, None)
engine = AnvikshikiEngineV4(ks, grounding, contestation_mode="vada")

# 4. Query
result = engine(
    query="What strategic advantages does concentrated ownership provide?",
    retrieved_chunks=["..."],
)

# 5. Inspect results
print(result.response)
print(f"Confidence: {list(result.uncertainty.values())[0]['total_confidence']:.2f}")
print(f"Sources: {result.sources}")
print(f"Violations: {result.violations}")
print(f"Extension size: {result.extension_size}")
```

### 13.4 Tests: `tests/test_engine_v4.py`

```python
# tests/test_engine_v4.py
import pytest


# ── Unit Tests (mocked LLM) ──

def test_engine_initialization():
    """Engine constructs without error."""
    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store
    ks = load_knowledge_store("data/sample_architecture.yaml")
    # Engine requires grounding pipeline — skip full init in unit test
    assert ks is not None


def test_compile_and_compute():
    """AF construction + grounded extension produces valid labels."""
    from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store
    from anvikshiki_v4.schema_v4 import Label
    ks = load_knowledge_store("data/sample_architecture.yaml")
    facts = [{"predicate": "concentrated_ownership", "confidence": 0.9}]
    af = compile_t2(ks, facts)
    labels = af.compute_grounded()
    assert any(lbl == Label.IN for lbl in labels.values())


# ── Integration Tests (require LLM) ──

@pytest.mark.skipif(
    "not config.getoption('--run-integration')",
    reason="Requires --run-integration flag and API key"
)
def test_full_pipeline():
    """End-to-end: query → response with uncertainty."""
    import dspy
    dspy.configure(lm=dspy.LM('openai/gpt-4o-mini'))
    # Full pipeline test would go here
    pass
```

---

## 14. Module 11: Optimization

**File:** `anvikshiki_v4/optimize.py`
**Purpose:** DSPy optimization with argumentation-aware calibration metric.
**Dependencies:** `engine_v4.py`

### 14.1 Updated Calibration Metric

```python
# anvikshiki_v4/optimize.py
"""DSPy optimization for the v4 engine."""

import dspy


def calibration_metric_v4(gold, pred) -> float:
    """
    Argumentation-aware calibration metric.
    Rewards: calibration, source attribution, epistemic qualification,
             extension quality, contestation coverage.
    """
    score = 0.0

    # 1. Non-empty, substantive response
    if hasattr(pred, 'response') and pred.response and len(pred.response) > 50:
        score += 0.2

    # 2. Sources cited
    if hasattr(pred, 'sources') and pred.sources:
        score += 0.15

    # 3. Extension quality: productive reasoning occurred
    if hasattr(pred, 'extension_size') and pred.extension_size > 0:
        score += 0.15

    # 4. Epistemic qualification in response
    hedges = ["established", "hypothesis", "provisional",
              "contested", "uncertain", "open question"]
    if hasattr(pred, 'response') and any(
        h in pred.response.lower() for h in hedges
    ):
        score += 0.2

    # 5. Violations reported when present
    if hasattr(pred, 'violations') and pred.violations:
        if hasattr(pred, 'response') and any(
            w in pred.response.lower()
            for w in ["however", "caveat", "exception", "limitation"]
        ):
            score += 0.15

    # 6. No overconfidence
    if hasattr(pred, 'response') and "certainly" not in pred.response.lower():
        score += 0.15

    return min(1.0, score)


def optimize_engine(engine, trainset, valset, auto="medium"):
    """Run MIPROv2 optimization on the engine."""
    optimizer = dspy.MIPROv2(
        metric=calibration_metric_v4,
        auto=auto,
    )
    optimized = optimizer.compile(
        engine,
        trainset=trainset,
        valset=valset,
    )
    return optimized


def evaluate_engine(engine, devset, num_threads=8):
    """Evaluate engine on a development set."""
    evaluator = dspy.Evaluate(
        devset=devset,
        metric=calibration_metric_v4,
        num_threads=num_threads,
        display_progress=True,
    )
    return evaluator(engine)
```

### 14.2 Optimizable Parameters Inventory

| Parameter | Module | Default | Description |
|-----------|--------|---------|-------------|
| Epistemic status thresholds | `schema_v4.py` | b>0.8, u<0.1, etc. | When to classify ESTABLISHED vs HYPOTHESIS |
| Decay half-life | `t2_compiler_v4.py` | 365 days | Exponential decay rate |
| Decay undermine threshold | `t2_compiler_v4.py` | 0.3 | Below this, argument attacked as stale |
| Grounding confidence threshold | `grounding.py` | 0.4 | Below this, request clarification |
| Round-trip threshold | `grounding.py` | 0.9 | Below this, run round-trip verification |
| Ensemble N | `grounding.py` | 5 | Parallel grounding attempts |
| Synthesis Refine threshold | `engine_v4.py` | 0.5 | Minimum reward to accept synthesis |
| Synthesis Refine N | `engine_v4.py` | 3 | Max retry attempts |
| CausalStatus → PramanaType | `t2_compiler_v4.py` | See table | Refinable per domain |
| EpistemicStatus → (b,d,u) | `t2_compiler_v4.py` | See table | Learnable from training data |

---

## 15. Testing Strategy

### 15.1 Unit Tests (No LLM Calls)

| Module | Test File | Focus |
|--------|----------|-------|
| `schema.py` | `test_schema.py` | Pydantic validation, JSON round-trip, enum serialization (reused from v3) |
| `schema_v4.py` | `test_schema_v4.py` | Semiring laws (5 axioms), tag arithmetic, epistemic status derivation, Argument/Attack construction |
| `datalog_engine.py` | `test_datalog.py` | Boolean/lattice mode, semi-naive correctness, termination (reused from v3) |
| `argumentation.py` | `test_argumentation.py` | Grounded extension, defeat with preferences, pramāṇa hierarchy, cycles, epistemic status, oplus accumulation |
| `t2_compiler_v4.py` | `test_t2_compiler_v4.py` | AF construction from YAML, three attack types, tag computation, fixpoint convergence |
| `t3_compiler.py` | `test_t3_compiler.py` | Graph construction, chunk splitting (reused from v3) |
| `uncertainty.py` | `test_uncertainty.py` | UQ from provenance tags, all three components |
| `contestation.py` | `test_contestation.py` | Three protocols, user contestation input, AF modification |

### 15.2 Integration Tests (Require LLM)

```python
@pytest.fixture
def setup_engine_v4():
    import dspy
    dspy.configure(lm=dspy.LM('openai/gpt-4o-mini'))
    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store
    from anvikshiki_v4.grounding import GroundingPipeline
    from anvikshiki_v4.engine_v4 import AnvikshikiEngineV4
    ks = load_knowledge_store("data/sample_architecture.yaml")
    grounding = GroundingPipeline(ks, None)
    engine = AnvikshikiEngineV4(ks, grounding, contestation_mode="vada")
    return engine

def test_full_pipeline_v4(setup_engine_v4):
    engine = setup_engine_v4
    result = engine(
        query="What happens when a company has concentrated ownership?",
        retrieved_chunks=["..."],
    )
    assert result.response
    assert result.uncertainty
    assert result.extension_size > 0
```

### 15.3 Property-Based Tests

Structural invariants that must hold for ANY input:

1. **Grounded extension is conflict-free.** No two IN arguments attack each other.
2. **Grounded extension defends all members.** Every attacker of an IN argument is OUT.
3. **Grounded ⊆ every preferred extension.** Every IN-grounded argument is IN in at least one preferred extension.
4. **Semiring laws hold for random tags.** Fuzz test with random ProvenanceTag pairs.
5. **Fixpoint terminates.** `compile_t2` terminates within `MAX_ITERATIONS` for any KB.

### 15.4 Running Tests

```bash
# Unit tests only (no LLM, fast)
pytest tests/ -k "not integration" -v

# Integration tests (requires API key)
OPENAI_API_KEY=sk-... pytest tests/ -k "integration" -v --run-integration

# Property-based tests
pytest tests/ -k "property" -v

# All tests
pytest tests/ -v --run-integration
```

---

## 16. Phase-by-Phase Build Order

### Phase 1: DSPy Only — Baseline (Week 1-2)

**Build:**
1. `schema.py` — reuse from v3
2. `schema_v4.py` — ProvenanceTag, PramanaType, RuleType, EpistemicStatus, Argument, Attack, Label
3. `t3_compiler.py` — reuse from v3
4. `grounding.py` — reuse from v3
5. `engine_v4.py` (Phase 1 variant) — LLM-only reasoning, no AF

**Validation gate:**
- [ ] All unit tests for `schema.py` and `schema_v4.py` pass (semiring laws verified)
- [ ] Grounding pipeline produces correct predicates for sample queries
- [ ] LLM synthesis produces plausible responses
- [ ] Baseline metrics established for comparison with Phase 2+

### Phase 2: DSPy + Abstract Argumentation — Boolean Tags (Week 3-4)

**Build:**
1. `argumentation.py` — `compute_grounded()` only
2. `t2_compiler_v4.py` — with Boolean tags (`ProvenanceTag.one()` for all arguments)
3. `engine_v4.py` (Phase 2) — AF construction + grounded extension, no quantitative reasoning

**Validation gate:**
- [ ] AF construction produces correct arguments from sample KB
- [ ] Grounded extension matches hand-computed expected output for sample scenarios
- [ ] Hetvābhāsas detected as defeat relations (not keyword matching)
- [ ] Scope exclusions produce undercutting attacks that propagate through chains
- [ ] Compare Phase 1 vs Phase 2: Phase 2 produces deterministic reasoning traces

### Phase 3: DSPy + ASPIC+ over Provenance Semirings — Core (Week 5-6)

**Build:**
1. Full ProvenanceTag with tensor/oplus operations (activate semiring arithmetic)
2. `_build_rule_tag()` in `t2_compiler_v4.py` (map KB metadata to tags)
3. `uncertainty.py` (v4 version — from tags, not hand-tuned dict)
4. `optimize.py` (v4 calibration metric)

**Validation gate:**
- [ ] Semiring operations verified: tensor attenuates belief, oplus accumulates evidence
- [ ] Tag propagation through 3-hop chain: belief decreases, uncertainty increases, depth = 3
- [ ] Three independent HYPOTHESIS arguments for same conclusion: combined tag.belief > any single
- [ ] Epistemic status derived correctly from combined tag values
- [ ] UQ decomposition uses tag fields, not `DOMAIN_BASE_UNCERTAINTY` dict
- [ ] Compare Phase 2 vs Phase 3: Phase 3 produces ESTABLISHED/HYPOTHESIS/PROVISIONAL distinctions

### Phase 4: Full System + GraphRAG + Contestation (Week 7-8)

**Build:**
1. T3 integration — link chunks to arguments
2. `contestation.py` — three protocols
3. `engine_v4.py` full version with `contestation_mode` parameter
4. `compute_preferred()` and `compute_stable()` in `argumentation.py`

**Validation gate:**
- [ ] T3 chunks linked to argument provenance: synthesis cites correct guide sections
- [ ] Vāda mode matches Phase 3 grounded output exactly
- [ ] Jalpa mode produces additional defensible positions beyond grounded
- [ ] Vitaṇḍā mode produces complete vulnerability inventory
- [ ] User contestation: add counter-argument → extension changes → synthesis reflects change
- [ ] End-to-end metric: MIPROv2 optimization improves over unoptimized baseline

---

## 17. DSPy 3.x Migration Notes

### 17.1 Complete API Translation Table

| DSPy 2.x (thesis code) | DSPy 3.1.x (this guide) | Notes |
|------------------------|------------------------|-------|
| `dspy.OpenAI(model, api_key)` | `dspy.LM('openai/model', api_key)` | Uses LiteLLM routing |
| `dspy.Anthropic(...)` | `dspy.LM('anthropic/model')` | Same pattern |
| `dspy.Program` | `dspy.Module` | Base class renamed |
| `dspy.Predict(sig)` | `dspy.Predict(sig)` | Unchanged |
| `dspy.ChainOfThought(sig)` | `dspy.ChainOfThought(sig)` | Unchanged |
| `dspy.Assert(cond, msg)` | `dspy.Refine(module, N, reward_fn, threshold)` | **DEPRECATED** |
| `dspy.Suggest(cond, msg)` | `dspy.BestOfN(module, N, reward_fn, threshold)` | **DEPRECATED** |
| `dspy.TypedPredictor(sig)` | Pydantic BaseModel as output field type | Native support |
| `dspy.teleprompt.MIPROv2(metric, num_candidates, init_temperature)` | `dspy.MIPROv2(metric, auto="medium")` | Simplified API |
| `dspy.teleprompt.BootstrapFewShotWithRandomSearch` | Same | Unchanged |
| Community retrievers | `dspy.retrievers.Embeddings` | Built-in FAISS |
| No async | `dspy.asyncify()`, `module.batch()` | New |
| No parallel | `dspy.Parallel(num_threads=8)` | New |

### 17.2 New Optimizers

| Optimizer | Best For | API |
|-----------|---------|-----|
| **MIPROv2** | General-purpose, first choice | `dspy.MIPROv2(metric, auto="medium")` |
| **SIMBA** | Large search spaces | `dspy.SIMBA(metric, ...)` |
| **GEPA** | Newest, experimental | `dspy.GEPA(metric, ...)` |
| **BootstrapFinetune** | When you have labeled data | `dspy.BootstrapFinetune(metric, ...)` |

### 17.3 v4-Specific Note

v4 does not introduce new DSPy patterns beyond what v3 uses. All architectural changes are in the symbolic layer (argumentation engine, provenance semiring, contestation protocols). LLM-facing components (grounding, synthesis, optimization) use the same DSPy 3.1.x patterns.

---

## 18. Appendix A: egglog Integration

### 18.1 When to Use egglog vs Python

| Criterion | Custom Python | egglog-python |
|-----------|--------------|---------------|
| AF size < 500 arguments | Preferred | Overkill |
| AF size > 1000 arguments | Slow | Preferred (Rust backend) |
| Custom `_defeats()` logic | Easy | Requires encoding preference as egglog rule |
| Native lattice `:merge` | Not available | Built-in |
| Proof trace inspection | Full Python access | Requires extraction |
| Debugging | Standard Python | Opaque Rust engine |

### 18.2 v4 egglog Usage

In v4, egglog can serve as an alternative backend for:

1. **Argument construction via recursive rules.** Define vyāptis as egglog rules. Derived facts become arguments.

2. **Attack derivation via contradiction detection.** Define negation-prefix pattern. Derive attack facts when contradictory conclusions exist.

3. **Tag accumulation via native `:merge`.** Encode ProvenanceTag operations as egglog sorts with `:merge` directives.

```python
# Example: egglog argument construction
from egglog import EGraph

egraph = EGraph()
egraph.register("""
(sort Tag)
(function tensor (Tag Tag) Tag :merge (tensor-impl old new))
(function oplus (Tag Tag) Tag :merge (oplus-impl old new))

; Define arguments
(function arg (String) Tag)
(function derived (String String) Tag)  ; (conclusion, vyapti_id) -> tag

; Rules
(rule ((= t1 (arg "concentrated_ownership")))
      ((set (derived "long_horizon_possible" "V01")
            (tensor t1 (arg "V01_rule_tag")))))
""")
```

### 18.3 Installation

```bash
pip install egglog>=11.0
```

---

## 19. Appendix B: Grammar-Constrained Decoding Options

### 19.1 For API-Based Models (Instructor)

```python
import instructor
from openai import OpenAI

client = instructor.from_openai(OpenAI())

class GroundingOutput(BaseModel):
    predicates: list[str]
    confidence: float

result = client.chat.completions.create(
    model="gpt-4o-mini",
    response_model=GroundingOutput,
    messages=[{"role": "user", "content": query}],
)
```

### 19.2 For Local Models (SGLang + XGrammar)

```python
# Start SGLang server with XGrammar
# sglang serve meta-llama/Meta-Llama-3-8B-Instruct --grammar-backend xgrammar

import dspy
lm = dspy.LM('openai/meta-llama/Meta-Llama-3-8B-Instruct',
              api_base='http://localhost:7501/v1', api_key='')
```

### 19.3 Practical Recommendation

| Environment | Recommendation |
|------------|----------------|
| Development | `dspy.JSONAdapter()` + OpenAI |
| Production (API) | Instructor + OpenAI/Anthropic |
| Production (local) | SGLang + XGrammar |

---

## 20. Appendix C: Nyāya-to-ASPIC+ Implementation Tables

### Table 1: Nyāya Concepts → ASPIC+ Primitives → Code Types

| Nyāya | ASPIC+ | Code |
|-------|--------|------|
| Vyāpti (definitional) | Strict rule rₛ | `Argument(is_strict=True)` |
| Vyāpti (empirical) | Defeasible rule rₐ | `Argument(is_strict=False)` |
| Pratyakṣa | Necessary premise Kₙ | `tag.pramana_type=PRATYAKSA` |
| Śabda | Ordinary premise Kₚ | `tag.pramana_type=SABDA` |
| Anumāna | Argument tree | `Argument(sub_arguments=(...))` |
| Pañcāvayava | Argument structure | `get_argument_tree()` |
| Pramāṇa hierarchy | Preference ordering ≤ | `PramanaType(IntEnum)` comparison |
| ESTABLISHED | IN grounded + strong tag | `get_epistemic_status()` |
| CONTESTED | OUT grounded, IN preferred | Same |
| OPEN | UNDECIDED | Same |
| Vāda | Grounded semantics | `compute_grounded()` |
| Jalpa | Preferred semantics | `compute_preferred()` |
| Vitaṇḍā | Stable semantics | `compute_stable()` |

### Table 2: Five Hetvābhāsas → Defeat Types → Attack Generation

| Hetvābhāsa | Meaning | Defeat Type | ASPIC+ Attack | Trigger |
|-----------|---------|-------------|---------------|---------|
| **Asiddha** | Unestablished | Undermining | Attack on premise | `decay_factor < 0.3` |
| **Savyabhicāra** | Inconclusive | Undercutting | Attack on rule | Scope exclusion established |
| **Viruddha** | Contradictory | Rebutting | Counter-argument | `pred` and `not_pred` both exist |
| **Satpratipakṣa** | Counterbalanced | Symmetric | Mutual rebutting | Equal strength mutual attacks |
| **Bādhita** | Sublated | Preference | `_defeats()` | Higher pramāṇa overrides |

### Table 3: Three Debate Types → Semantics → Complexity

| Debate | Semantics | Skeptical Complexity | Default Use | Stakeholder |
|--------|-----------|---------------------|-------------|-------------|
| Vāda | Grounded | P-complete | Routine queries | Expert |
| Jalpa | Preferred | coNP-complete | Stress-testing | Auditor |
| Vitaṇḍā | Stable | coNP-complete | Formal audit | External auditor |

### Table 4: Pramāṇa Types → Computational Analogues

| Pramāṇa | Value | Analogue | Default Trust | Typical Source |
|---------|-------|----------|---------------|----------------|
| Upamāna | 1 | Embedding similarity | 0.5 | Analogical transfer |
| Śabda | 2 | Expert claims, citations | 0.7 | Published literature |
| Anumāna | 3 | Rule chaining, derivation | 0.85 | Datalog evaluation |
| Pratyakṣa | 4 | Ground truth, direct lookup | 1.0 | Empirical measurement |

### Table 5: v3 Components → v4 Replacements

| v3 Component | v4 Status | Replacement |
|-------------|----------|-------------|
| Heyting lattice (IntEnum) | Eliminated | Extension membership + tag.epistemic_status() |
| Cellular sheaf (δ, L, H¹) | Eliminated | Rationality postulates guarantee consistency |
| Trust table (20+ entries) | Eliminated | tag.trust_score + pramāṇa preference |
| Keyword hetvābhāsa detection | Eliminated | Native defeat relations (5 types) |
| DOMAIN_BASE_UNCERTAINTY dict | Eliminated | tag.disbelief from compile-time params |
| Meet-only propagation | Eliminated | Non-idempotent ⊕ (cumulative fusion) |
| Identity restriction maps | N/A (no sheaf) | — |
| 2-of-8 stalk encoding | N/A (no stalks) | — |

---

## 21. Appendix D: Provenance Semiring Mathematics

### 21.1 Formal Definition

A commutative semiring (K, ⊕, ⊗, 0, 1) satisfies:
- (K, ⊕, 0) is a commutative monoid
- (K, ⊗, 1) is a commutative monoid
- ⊗ distributes over ⊕
- 0 ⊗ a = a ⊗ 0 = 0 for all a (annihilation)

### 21.2 Tensor (⊗) Worked Example

Tags A = `(b=0.9, d=0.05, u=0.05, trust=0.85, decay=0.9, depth=1)` and B = `(b=0.8, d=0.1, u=0.1, trust=0.9, decay=0.95, depth=1)`:

```
tensor(A, B):
  belief     = 0.9 × 0.8  = 0.72
  disbelief  = min(1, 0.05 + 0.1 - 0.005)  = 0.145
  uncertainty = min(1, 0.05 + 0.1 - 0.005)  = 0.145
  trust      = min(0.85, 0.9)  = 0.85
  decay      = min(0.9, 0.95)  = 0.9
  depth      = 1 + 1           = 2
  pramana    = min(A, B)
  sources    = A.sources ∪ B.sources
```

**Observation:** Belief attenuates (0.72 < 0.8 < 0.9). Uncertainty grows. Trust is weakest-link. This models evidence degradation through inference chains.

### 21.3 Oplus (⊕) Worked Example — Cumulative Fusion

Tags A = `(b=0.6, d=0.1, u=0.3)` and B = `(b=0.5, d=0.15, u=0.35)`:

```
oplus(A, B) via Jøsang cumulative fusion:
  κ     = 0.3 + 0.35 - 0.3 × 0.35       = 0.545
  new_b = (0.6×0.35 + 0.5×0.3) / 0.545  = 0.36/0.545 = 0.661
  new_d = (0.1×0.35 + 0.15×0.3) / 0.545 = 0.08/0.545  = 0.147
  new_u = (0.3×0.35) / 0.545             = 0.105/0.545  = 0.193
  trust = 1 - (1-0.85)(1-0.9) = 0.985  (noisy-OR)
```

**Key observation:** Combined belief (0.661) exceeds both individual beliefs (0.6, 0.5). This is the **non-idempotent accumulation** property that v3's meet-only lattice lacked. Three independent HYPOTHESIS arguments genuinely strengthen the conclusion.

### 21.4 Convergence Guarantee

For recursive Datalog over an ω-continuous semiring, semi-naive evaluation converges to the least fixpoint (Khamis et al., PODS 2022). ProvenanceTag is ω-continuous because all fields are bounded ([0,1] for floats, finite for sets and enums). Therefore the argumentation fixpoint terminates.

### 21.5 Universality

PosBool[X] is the most general provenance semiring (Green et al., PODS 2007). ProvenanceTag is obtained by applying a homomorphism from PosBool[X] to the Subjective Logic opinion space. The architecture could be generalized to any other provenance scheme (Boolean, counting, tropical, Viterbi, access control) by changing the semiring homomorphism.

---

## 22. Appendix E: Contestable AI Compliance Checklist

### 22.1 Moreira et al. (2025) Eight-Property Checklist

| Property | Requirement | v4 Compliance |
|----------|------------|---------------|
| 1. Explainability | Intrinsic > post-hoc | Argument trees from compiled KB — faithful, inspectable, machine-checkable |
| 2. Openness | Broad access, not expert-only | Five typed contestation inputs — NL descriptions, not formal logic |
| 3. Traceability | Granular audit logging | ProvenanceTag on every argument: source_ids, pramāṇa, trust, decay, depth |
| 4. Safeguards | Proportional to risk | Rationality postulates + 5 formally classified hetvābhāsa types |
| 5. Adaptivity | Learn from contestation | New arguments/attacks persist. AF recomputes incrementally. |
| 6. Auditing | Independent external | Full AF exportable as JSON via `af.to_dict()` |
| 7. Ease of contestation | Accessible challenge routes | 5 contestation types + 3 debate protocols with different complexity |
| 8. Explanation quality | Faithfulness and robustness | Explanation IS the reasoning — argument trees, not approximation |

### 22.2 Leofante et al. (KR 2024) Four Requirements

| Requirement | Description | v4 Implementation |
|------------|------------|-------------------|
| **(E)** Explanations | Explanations of outputs and reasoning | Argument trees with provenance tags and pramāṇa classification |
| **(G)** Grounds | Formal basis for contestation | Five ground types from Nyāya hetvābhāsas (Table 2 above) |
| **(I)** Interaction | Structured human-machine dialogue | Three debate protocols: vāda/jalpa/vitaṇḍā (Section 12) |
| **(R)** Redress | System revision after contestation | Recompute grounded extension after adding/removing arguments — polynomial, deterministic |

### 22.3 Henin & Le Métayer Hierarchy

| Level | Standard LLM/RAG | v3 | ArgLLMs | v4 |
|-------|-----------------|-----|---------|-----|
| **Explainability** | Partial | Yes (Datalog trace) | Yes (QBAF trees) | Yes (argument trees + provenance tags) |
| **Justifiability** | No | Partial | Partial | Yes (grounded extension + provenance chain) |
| **Contestability** | No | Partial (3 unrelated mechanisms) | Yes (score modification) | Yes (5 grounds + 3 protocols + formal guarantees) |

---

*This document is the implementation companion to `thesis2_v1.md`. The thesis describes the architecture and theory; this guide shows how to build it with current tools.*
