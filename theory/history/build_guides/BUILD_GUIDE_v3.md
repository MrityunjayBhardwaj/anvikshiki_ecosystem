# Ānvīkṣikī Engine v3 — Build Guide

## From Thesis to Working System: A Complete Implementation Manual

**Target:** Build the four-phase neurosymbolic reasoning engine described in `thesis_v3(1).md`
**Stack:** DSPy 3.1.x + Custom Lattice Datalog + egglog + NetworkX + NumPy
**Python:** 3.10+ (required by DSPy 3.x)
**Date:** March 2026

---

## What Changed from BUILD_GUIDE (v2)

| Area | v2 Build Guide | v3 Build Guide |
|------|---------------|----------------|
| **Conformal prediction** | Module 7 (`conformal.py`) | **Removed** — replaced by `provenance.py` |
| **Epistemic lattice** | 4 values + BOTTOM | **6 values**: + PROVISIONAL + BOTTOM |
| **Grounding** | Five-layer always-on (5-7 LLM calls) | **Two-layer default + three-layer escalation** (1-2 calls) |
| **Source authority** | Not present | **New module**: `source_authority.py` (śabda model) |
| **KB bootstrapping** | Full expert authoring | **Automated bootstrap** + expert reviews ~15-20% |
| **Performance** | All computation at query time | **Compile-time / query-time split** |
| **Uncertainty divisor** | `ep_score = value / 4.0` | `ep_score = value / 5.0` (6-value lattice) |
| **Thesis reference** | `thesis_v2.md` | `thesis_v3(1).md` |

---

## Table of Contents

1. [Technology Stack Decisions](#1-technology-stack-decisions)
2. [Project Structure](#2-project-structure)
3. [Environment Setup](#3-environment-setup)
4. [Module 1: Core Schema (`schema.py`)](#4-module-1-core-schema)
5. [Module 2: Datalog Engine (`datalog_engine.py`)](#5-module-2-datalog-engine)
6. [Module 3: T2 Compiler (`t2_compiler.py`)](#6-module-3-t2-compiler)
7. [Module 4: T3 Compiler (`t3_compiler.py`)](#7-module-4-t3-compiler)
8. [Module 5: Grounding Pipeline (`grounding.py`)](#8-module-5-grounding-pipeline)
9. [Module 6: Uncertainty Quantification (`uncertainty.py`)](#9-module-6-uncertainty-quantification)
10. [Module 7: Provenance Chain Tracer (`provenance.py`)](#10-module-7-provenance-chain-tracer)
11. [Module 8: Cellular Sheaf (`sheaf.py`)](#11-module-8-cellular-sheaf)
12. [Module 9: Source Authority (`source_authority.py`)](#12-module-9-source-authority)
13. [Module 10: Final Engine (`engine.py`)](#13-module-10-final-engine)
14. [Module 11: Optimization (`optimize.py`)](#14-module-11-optimization)
15. [Module 12: KB Bootstrapping (`bootstrap.py`)](#15-module-12-kb-bootstrapping)
16. [Testing Strategy](#16-testing-strategy)
17. [Phase-by-Phase Build Order](#17-phase-by-phase-build-order)
18. [DSPy 3.x Migration Notes](#18-dspy-3x-migration-notes)
19. [Appendix A: egglog Integration](#19-appendix-a-egglog-integration)
20. [Appendix B: Grammar-Constrained Decoding](#20-appendix-b-grammar-constrained-decoding)

---

## 1. Technology Stack Decisions

### Why These Choices

| Component | Tool | Why |
|-----------|------|-----|
| **LLM Orchestration** | DSPy 3.1.x | Typed signatures, optimizable modules, Pydantic output types, `dspy.Refine` for constraints |
| **Datalog Engine** | Custom Python (primary) | Full control over lattice extensions, Heyting meet/join, proof traces, PROVISIONAL status |
| **Datalog Engine** | egglog-python (optional backend) | Rust-backed, native lattice merge via `:merge`, pip-installable |
| **Knowledge Graph** | NetworkX | Mature, pure-Python, sufficient for hundreds-to-thousands of nodes |
| **Retrieval** | `dspy.retrievers.Embeddings` | Built into DSPy 3.x, uses FAISS for large corpora |
| **Structured Output** | Pydantic + `dspy.JSONAdapter` | Native DSPy 3.x support for typed predictors |
| **Sheaf Computation** | NumPy/SciPy | Dense linear algebra for Laplacian, eigenvectors |
| **Provenance** | Custom Python | Deterministic proof-tree walk, zero LLM calls — replaces conformal prediction |
| **Grammar Constraint** | Instructor (API models) / XGrammar (local models) | Instructor for Claude/GPT; XGrammar for local serving |

### What Changed from v2 Build Guide

| v2 Build Guide (DSPy 2.x patterns) | v3 Build Guide (DSPy 3.1.x) |
|--------------------------------------|-------------------------------|
| `dspy.Suggest(condition, msg)` | `dspy.Refine(module, N, reward_fn, threshold)` |
| `dspy.Assert(condition, msg)` | `dspy.Refine(module, N, reward_fn, threshold)` |
| `dspy.OpenAI(...)` | `dspy.LM('openai/gpt-4o-mini')` |
| `conformal.py` (source verification) | `provenance.py` (deterministic chain tracing) |
| Five-layer grounding always-on | Two-layer default + three-layer escalation |
| `EpistemicValue` (5 values) | `EpistemicValue` (6 values — added PROVISIONAL) |

---

## 2. Project Structure

```
anvikshiki/
├── __init__.py
├── schema.py              # Core data structures (KnowledgeStore, Vyapti, etc.)
├── datalog_engine.py      # Semi-naive Datalog evaluator with lattice values
├── t2_compiler.py         # Architecture YAML → Datalog rules
├── t3_compiler.py         # Guide text → GraphRAG corpus
├── grounding.py           # Two-layer default + three-layer escalation grounding
├── uncertainty.py         # Three-way UQ decomposition
├── provenance.py          # Deterministic provenance chain tracing (replaces conformal.py)
├── sheaf.py               # Cellular sheaf consistency checking
├── source_authority.py    # Śabda-based source authority model (NEW in v3)
├── bootstrap.py           # Automated KB bootstrapping pipeline (NEW in v3)
├── engine.py              # Final assembled engine (all phases)
├── optimize.py            # DSPy optimization pipeline
├── cli.py                 # Command-line interface
│
├── tests/
│   ├── __init__.py
│   ├── test_schema.py
│   ├── test_datalog.py
│   ├── test_grounding.py
│   ├── test_t2_compiler.py
│   ├── test_t3_compiler.py
│   ├── test_uncertainty.py
│   ├── test_provenance.py     # NEW (replaces test_conformal.py)
│   ├── test_sheaf.py
│   ├── test_source_authority.py  # NEW
│   ├── test_bootstrap.py     # NEW
│   ├── test_engine.py
│   └── fixtures/
│       └── sample_architecture.yaml
│
├── data/
│   └── sample_architecture.yaml   # Example Stage 2+3 output
│
├── pyproject.toml
└── README.md
```

---

## 3. Environment Setup

### 3.1 System Requirements

- Python 3.10–3.13
- macOS, Linux, or WSL2
- 8GB+ RAM (sheaf Laplacian computation on large graphs)

### 3.2 Installation

```bash
# Create project directory
mkdir -p anvikshiki && cd anvikshiki

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Core dependencies
pip install dspy>=3.1.0          # LLM orchestration (includes LiteLLM)
pip install networkx>=3.2        # Knowledge graph
pip install numpy>=1.26          # Numerical computation
pip install scipy>=1.12          # Sparse linear algebra (sheaf Laplacian)
pip install pydantic>=2.6        # Structured output types
pip install pyyaml>=6.0          # YAML parsing for architecture files

# Optional: high-performance Datalog backend
pip install egglog>=11.0         # Rust-backed Datalog with lattice merge

# Optional: structured output for API models
pip install instructor>=1.5      # Pydantic extraction from API models

# Optional: local model serving with grammar constraints
pip install xgrammar             # Grammar-constrained decoding engine

# Development
pip install pytest>=8.0
pip install pytest-asyncio       # For async DSPy tests
```

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
name = "anvikshiki"
version = "0.3.0"
description = "Neurosymbolic reasoning engine with lattice Datalog, sheaf consistency, and provenance tracing"
requires-python = ">=3.10"
dependencies = [
    "dspy>=3.1.0",
    "networkx>=3.2",
    "numpy>=1.26",
    "scipy>=1.12",
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

## 4. Module 1: Core Schema

**File:** `anvikshiki/schema.py`
**Purpose:** Data structures for the compiled knowledge store
**Dependencies:** `pydantic`, `enum`, `datetime`

### 4.1 Design Decisions (v3 changes)

- **PROVISIONAL epistemic status added** — auto-generated rules not yet expert-validated
- **Source authority fields added** to `Vyapti` — trust tier, domain-of-competence match
- All models use `pydantic.BaseModel` for validation and DSPy 3.x output types

### 4.2 Implementation Spec

```python
# anvikshiki/schema.py

from pydantic import BaseModel, Field
from enum import Enum, IntEnum
from typing import Optional
from datetime import datetime


class DomainType(Enum):
    """Eight domain types from the Ānvīkṣikī taxonomy."""
    FORMAL = 1
    MECHANISTIC = 2
    EMPIRICAL = 3
    CRAFT = 4
    INTERPRETIVE = 5
    DESIGN = 6
    NORMATIVE = 7
    META_ANALYTICAL = 8


class CausalStatus(str, Enum):
    STRUCTURAL = "structural"
    REGULATORY = "regulatory"
    EMPIRICAL = "empirical"
    DEFINITIONAL = "definitional"


class EpistemicStatus(str, Enum):
    """Five epistemic values (plus BOTTOM in the Datalog engine).
    v3: Added PROVISIONAL for auto-generated, unvalidated rules."""
    ESTABLISHED = "established"
    WORKING_HYPOTHESIS = "hypothesis"
    PROVISIONAL = "provisional"          # NEW in v3
    GENUINELY_OPEN = "open"
    ACTIVELY_CONTESTED = "contested"


class DecayRisk(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class Confidence(BaseModel):
    existence: float = Field(ge=0, le=1)
    formulation: float = Field(ge=0, le=1)
    evidence: str  # "experimental", "observational", "theoretical", "expert_consensus"


class Vyapti(BaseModel):
    """A domain rule — the core computational primitive."""
    id: str
    name: str
    statement: str
    causal_status: CausalStatus
    scope_conditions: list[str] = []
    scope_exclusions: list[str] = []
    confidence: Confidence
    epistemic_status: EpistemicStatus
    decay_risk: DecayRisk = DecayRisk.LOW
    decay_condition: Optional[str] = None
    last_verified: Optional[datetime] = None
    sources: list[str] = []

    # Datalog-compilable fields
    antecedents: list[str] = []
    consequent: str = ""

    # v3: Source authority metadata
    source_trust_tier: Optional[str] = None      # "canonical", "cited", "credible", "unknown"
    source_venue_tier: Optional[str] = None       # "peer_reviewed", "edited", "self_published"
    source_domain_match: bool = True              # Author speaks within competence?


class Hetvabhasa(BaseModel):
    """A reasoning fallacy — an integrity constraint."""
    id: str
    name: str
    description: str
    detection_signature: str
    correction_pattern: str
    common_contexts: list[str] = []


class ThresholdConcept(BaseModel):
    name: str
    reorganizes: list[str] = []
    prerequisites: list[str] = []
    troublesome_aspects: list[str] = []


class ChapterFingerprint(BaseModel):
    chapter_id: str
    title: str
    key_terms: list[str] = []
    anchoring_concepts: list[str] = []
    vyaptis_introduced: list[str] = []
    hetvabhasas_active: list[str] = []
    prerequisites: list[str] = []
    forward_dependencies: list[str] = []
    epistemic_statuses: dict[str, EpistemicStatus] = {}
    decay_markers: list[dict] = []
    difficulty_tier: str = "intermediate"


class KnowledgeStore(BaseModel):
    """The complete compiled knowledge base for a domain."""
    domain_type: DomainType
    pramanas: list[str] = []
    vyaptis: dict[str, Vyapti] = {}
    hetvabhasas: dict[str, Hetvabhasa] = {}
    threshold_concepts: list[ThresholdConcept] = []
    dependency_graph: dict[str, list[str]] = {}
    chapter_fingerprints: dict[str, ChapterFingerprint] = {}
    reference_bank: dict[str, dict] = {}
```

### 4.3 Test: `tests/test_schema.py`

Test that:
- A `KnowledgeStore` can be constructed from a sample dictionary
- Round-trip JSON serialization preserves all fields
- Invalid confidence values (>1, <0) raise `ValidationError`
- `EpistemicStatus.PROVISIONAL` is correctly serializable
- Source authority fields default correctly when absent

---

## 5. Module 2: Datalog Engine

**File:** `anvikshiki/datalog_engine.py`
**Purpose:** Semi-naive bottom-up Datalog evaluator with lattice-valued facts
**Dependencies:** None (pure Python + standard library)

### 5.1 Design Decisions

- Same as v2 Build Guide, except:
- **PROVISIONAL added to the Heyting lattice** between HYPOTHESIS and OPEN
- Lattice now has **6 values** (BOTTOM through ESTABLISHED)
- Any inference chain touching a PROVISIONAL rule produces at most PROVISIONAL

### 5.2 The Heyting Lattice (v3)

```
ESTABLISHED (5)     ← strongest
    |
HYPOTHESIS (4)
    |
PROVISIONAL (3)     ← NEW in v3: auto-generated, unvalidated
    |
OPEN (2)
    |
CONTESTED (1)
    |
BOTTOM (0)          ← no evidence / false
```

**Operations:**
- `meet(a, b) = min(a, b)` — used for chaining (weakest link)
- `join(a, b) = max(a, b)` — used for multiple derivation paths (best evidence)

### 5.3 Implementation Spec

```python
# anvikshiki/datalog_engine.py

from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional, Callable


class EpistemicValue(IntEnum):
    """Heyting algebra of truth values. v3: Added PROVISIONAL."""
    BOTTOM = 0
    CONTESTED = 1
    OPEN = 2
    PROVISIONAL = 3    # NEW in v3
    HYPOTHESIS = 4
    ESTABLISHED = 5

    @staticmethod
    def meet(a: 'EpistemicValue', b: 'EpistemicValue') -> 'EpistemicValue':
        return EpistemicValue(min(a.value, b.value))

    @staticmethod
    def join(a: 'EpistemicValue', b: 'EpistemicValue') -> 'EpistemicValue':
        return EpistemicValue(max(a.value, b.value))


@dataclass(frozen=True)
class Fact:
    predicate: str
    entity: str
    value: EpistemicValue = EpistemicValue.ESTABLISHED


@dataclass
class Rule:
    vyapti_id: str
    name: str
    head: str                    # Consequent predicate
    body_positive: list[str]     # Required antecedent predicates
    body_negative: list[str]     # Scope exclusions (negated)
    confidence: EpistemicValue   # Rule's own epistemic status


@dataclass
class Violation:
    hetvabhasa_id: str
    name: str
    description: str
    triggered_by: list[str]
    correction: str


class DatalogEngine:
    """
    Semi-naive Datalog evaluator with lattice-valued facts.

    TERMINATES: guaranteed (finite predicate/entity space, monotone lattice)
    COMPLEXITY: O(|rules| × |Δfacts|) per iteration
    CORRECT: computes minimal model (least fixpoint) of the rules
    """

    def __init__(self, boolean_mode: bool = True):
        self.boolean_mode = boolean_mode
        self.facts: dict[tuple[str, str], EpistemicValue] = {}
        self.rules: list[Rule] = []
        self.hetvabhasa_checks: list[dict] = []
        self.trace: list[str] = []
        self._delta: dict[tuple[str, str], EpistemicValue] = {}

    # --- Loading ---

    def add_fact(self, fact: Fact):
        """Add or update a fact. Join (max) if already exists."""
        key = (fact.predicate, fact.entity)
        old = self.facts.get(key, EpistemicValue.BOTTOM)
        new = EpistemicValue.join(old, fact.value)
        if new > old:
            self.facts[key] = new
            self._delta[key] = new

    def add_rule(self, rule: Rule):
        self.rules.append(rule)

    def add_hetvabhasa_check(self, hid, name, check_fn, correction):
        self.hetvabhasa_checks.append({
            'id': hid, 'name': name,
            'check_fn': check_fn, 'correction': correction,
        })

    # --- Semi-Naive Evaluation ---

    def evaluate(self) -> int:
        """Semi-naive fixpoint. Returns iteration count."""
        iteration = 0
        while self._delta:
            new_delta = {}
            for rule in self.rules:
                delta_entities = set()
                for pred in rule.body_positive:
                    for (p, e), v in self._delta.items():
                        if p == pred:
                            delta_entities.add(e)

                for entity in delta_entities:
                    result = self._try_fire(rule, entity)
                    if result is not None:
                        key = (rule.head, entity)
                        old = self.facts.get(key, EpistemicValue.BOTTOM)
                        if result > old:
                            self.facts[key] = result
                            new_delta[key] = result
                            self.trace.append(
                                f"Iter {iteration}: {rule.vyapti_id} → "
                                f"{rule.head}({entity}) = {result.name}"
                            )

            self._delta = new_delta
            iteration += 1
            max_iter = len(self.rules) * (len(self.facts) + 1) + 1
            if iteration > max_iter:
                raise RuntimeError("Fixpoint not reached — possible bug")

        return iteration

    def _try_fire(self, rule: Rule, entity: str) -> Optional[EpistemicValue]:
        antecedent_values = []
        for pred in rule.body_positive:
            key = (pred, entity)
            if key not in self.facts:
                return None
            antecedent_values.append(self.facts[key])

        for pred in rule.body_negative:
            key = (pred, entity)
            if key in self.facts and self.facts[key] > EpistemicValue.BOTTOM:
                return None

        if self.boolean_mode:
            return EpistemicValue.ESTABLISHED
        else:
            result = rule.confidence
            for av in antecedent_values:
                result = EpistemicValue.meet(result, av)
            return result

    # --- Querying ---

    def query(self, predicate, entity=None, min_value=EpistemicValue.BOTTOM):
        results = []
        for (p, e), v in self.facts.items():
            if p == predicate and v > min_value:
                if entity is None or e == entity:
                    results.append((e, v))
        return sorted(results, key=lambda x: x[1], reverse=True)

    def explain(self, predicate, entity):
        target = f"{predicate}({entity})"
        return [s for s in self.trace if target in s]

    def validate_predicates(self, predicates: list[str]) -> list[str]:
        """Validate predicate strings against known vocabulary (Layer 5)."""
        errors = []
        known = set()
        for rule in self.rules:
            known.add(rule.head)
            known.update(rule.body_positive)
            known.update(rule.body_negative)
        for pred_str in predicates:
            if '(' not in pred_str or ')' not in pred_str:
                errors.append(f"Malformed: '{pred_str}'")
                continue
            name = pred_str.split('(')[0].strip()
            if name.startswith('not_'):
                name = name[4:]
            if name not in known:
                errors.append(f"Unknown predicate: '{name}'")
        return errors

    # --- Integrity Constraints ---

    def check_hetvabhasas(self) -> list[Violation]:
        violations = []
        for check in self.hetvabhasa_checks:
            triggers = check['check_fn'](self.facts)
            if triggers:
                violations.append(Violation(
                    hetvabhasa_id=check['id'],
                    name=check['name'],
                    description=f"{check['name']} detected",
                    triggered_by=triggers,
                    correction=check['correction'],
                ))
        return violations

    # --- Serialization ---

    def to_datalog_text(self) -> str:
        lines = [
            f"% Ānvīkṣikī Knowledge Base (v3)",
            f"% Mode: {'Boolean' if self.boolean_mode else 'Lattice'}",
            f"% Rules: {len(self.rules)}, Facts: {len(self.facts)}",
            "",
        ]
        for rule in self.rules:
            pos = ", ".join(f"{p}(E)" for p in rule.body_positive)
            neg = ", ".join(f"not {p}(E)" for p in rule.body_negative)
            body = ", ".join(filter(None, [pos, neg]))
            lines.append(f"% {rule.vyapti_id}: {rule.name}")
            lines.append(f"{rule.head}(E) :- {body}.")
            lines.append("")
        for (pred, entity), value in sorted(self.facts.items()):
            lines.append(f"{pred}({entity}).  % {value.name}")
        return "\n".join(lines)
```

### 5.4 Tests: `tests/test_datalog.py`

**Critical test cases:**

1. **Boolean forward chaining**: Add facts A(x), B(x), rule `A(E), B(E) → C(E)`. Verify C(x) derived.
2. **Lattice propagation**: Rule confidence=HYPOTHESIS, antecedent=ESTABLISHED → consequent=HYPOTHESIS (meet).
3. **PROVISIONAL propagation** (NEW): Rule confidence=ESTABLISHED, antecedent=PROVISIONAL → consequent=PROVISIONAL.
4. **Multiple derivation paths**: Two rules derive same fact with HYPOTHESIS and ESTABLISHED → ESTABLISHED (join).
5. **Scope exclusion**: Rule with `body_negative=["public_firm"]`, add `public_firm(x)` → rule NOT fire.
6. **Semi-naive correctness**: Adding new fact re-evaluates only delta.
7. **Termination guarantee**: Cyclic rule dependency terminates (monotone lattice).
8. **Hetvabhasa detection**: Survivorship-bias check fires on selective evidence.

---

## 6. Module 3: T2 Compiler

**File:** `anvikshiki/t2_compiler.py`
**Purpose:** Compile verified architecture (Stage 2+3 YAML) into Datalog rules
**Dependencies:** `schema.py`, `datalog_engine.py`, `pyyaml`

### 6.1 v3 Changes

- `EPISTEMIC_MAP` now includes `PROVISIONAL` mapping
- Source authority metadata propagated from `Vyapti` to `Rule.confidence`

### 6.2 Implementation Spec

```python
# anvikshiki/t2_compiler.py

import yaml
from .schema import KnowledgeStore, EpistemicStatus, Vyapti, Hetvabhasa
from .datalog_engine import DatalogEngine, Rule, Fact, EpistemicValue

# v3: Map includes PROVISIONAL
EPISTEMIC_MAP = {
    EpistemicStatus.ESTABLISHED: EpistemicValue.ESTABLISHED,
    EpistemicStatus.WORKING_HYPOTHESIS: EpistemicValue.HYPOTHESIS,
    EpistemicStatus.PROVISIONAL: EpistemicValue.PROVISIONAL,       # NEW
    EpistemicStatus.GENUINELY_OPEN: EpistemicValue.OPEN,
    EpistemicStatus.ACTIVELY_CONTESTED: EpistemicValue.CONTESTED,
}


def load_knowledge_store(architecture_path: str) -> KnowledgeStore:
    """Parse Stage 2+3 YAML output into a KnowledgeStore."""
    with open(architecture_path) as f:
        arch = yaml.safe_load(f)
    return KnowledgeStore(**arch)


def compile_t2(
    knowledge_store: KnowledgeStore,
    boolean_mode: bool = True,
) -> DatalogEngine:
    engine = DatalogEngine(boolean_mode=boolean_mode)

    for vid, v in knowledge_store.vyaptis.items():
        rule = Rule(
            vyapti_id=vid,
            name=v.name,
            head=v.consequent,
            body_positive=v.antecedents,
            body_negative=v.scope_exclusions,
            confidence=EPISTEMIC_MAP.get(
                v.epistemic_status, EpistemicValue.HYPOTHESIS
            ),
        )
        engine.add_rule(rule)

    for hid, h in knowledge_store.hetvabhasas.items():
        check_fn = _build_hetvabhasa_check(h, knowledge_store)
        engine.add_hetvabhasa_check(
            hid=hid, name=h.name,
            check_fn=check_fn, correction=h.correction_pattern,
        )

    return engine


def ground_facts_from_predicates(
    engine: DatalogEngine,
    predicates: list[str],
    default_value: EpistemicValue = EpistemicValue.ESTABLISHED,
) -> list[Fact]:
    facts = []
    for pred_str in predicates:
        negated = pred_str.startswith("not_")
        clean = pred_str[4:] if negated else pred_str
        if '(' in clean and ')' in clean:
            name = clean.split('(')[0].strip()
            entity = clean.split('(')[1].rstrip(')').strip()
            value = EpistemicValue.BOTTOM if negated else default_value
            fact = Fact(name, entity, value)
            engine.add_fact(fact)
            facts.append(fact)
    return facts


def _build_hetvabhasa_check(hetvabhasa: Hetvabhasa, ks: KnowledgeStore):
    sig = hetvabhasa.detection_signature.lower()

    def check(facts):
        triggers = []
        if "survivorship" in sig:
            for (pred, entity), val in facts.items():
                if "success" in pred or "winner" in pred:
                    has_base = any(
                        "base_rate" in p or "failure" in p
                        for (p, e), v in facts.items() if e == entity
                    )
                    if not has_base:
                        triggers.append(f"{pred}({entity}) — no base rate")
        if "scale" in sig or "extrapolat" in sig:
            for (pred, entity), val in facts.items():
                if "large_scale" in pred or "enterprise" in pred:
                    has_evidence = any(
                        "scale_validated" in p
                        for (p, e), v in facts.items() if e == entity
                    )
                    if not has_evidence:
                        triggers.append(f"{pred}({entity}) — not validated at scale")
        return triggers

    return check
```

### 6.3 Sample Architecture YAML

Same as v2 Build Guide — see `data/sample_architecture.yaml`. The v3 addition is optional source authority fields on each vyāpti:

```yaml
# v3 additions to each vyāpti entry:
  V01:
    # ... all v2 fields ...
    source_trust_tier: canonical
    source_venue_tier: peer_reviewed
    source_domain_match: true
```

---

## 7. Module 4: T3 Compiler

**File:** `anvikshiki/t3_compiler.py`
**Purpose:** Build graph-structured retrieval corpus from guide text
**Dependencies:** `networkx`, `schema.py`

### 7.1 Implementation

Unchanged from v2 Build Guide. See v2 Build Guide §7 for the full `compile_t3()`, `TextChunk`, and retrieval integration with `dspy.retrievers.Embeddings`.

---

## 8. Module 5: Grounding Pipeline

**File:** `anvikshiki/grounding.py`
**Purpose:** Two-layer default + three-layer escalation NL→predicate defense
**Dependencies:** `dspy`, `schema.py`, `datalog_engine.py`

### 8.1 v3 Architecture Change: Two-Layer Default

The v2 Build Guide used a five-layer always-on pipeline (5-7 LLM calls). The v3 thesis restructures this to a **two-layer default** with optional escalation:

```
DEFAULT PATH (all queries — 1-2 LLM calls):

  Layer 1: Ontology-Constrained Prompt (always on, 1 LLM call)
      ↓
  Layer 5: Solver-Feedback Refinement (0-1 LLM calls, max 3 rounds)
      ↓
  Verified Predicates + grounding_confidence


ESCALATION PATH (when default fails):

  + Layer 2: Grammar-Constrained Decoding (if open-source model)
  + Layer 3: Ensemble Consensus (N=3-5, 2-4 additional calls)
  + Layer 4: Round-Trip Verification (1 additional call)

Escalation triggers:
  - Solver rejects after 3 rounds
  - Zero valid predicates produced
  - User requests high-confidence mode
```

### 8.2 Implementation Spec

```python
# anvikshiki/grounding.py

import dspy
from pydantic import BaseModel
from .schema import KnowledgeStore
from .datalog_engine import DatalogEngine


class GroundingResult(BaseModel):
    predicates: list[str] = []
    confidence: float = 0.0
    disputed: list[str] = []
    warnings: list[str] = []
    refinement_rounds: int = 0
    clarification_needed: bool = False


class GroundQuery(dspy.Signature):
    """Translate a natural language query into structured predicates.
    Use ONLY predicates from the ontology snippet."""

    query: str = dspy.InputField(desc="User's natural language question")
    ontology_snippet: str = dspy.InputField(
        desc="Valid predicates — use ONLY these")
    domain_type: str = dspy.InputField(desc="Domain classification")

    reasoning: str = dspy.OutputField(
        desc="Step by step: which predicates match the query?")
    predicates: list[str] = dspy.OutputField(
        desc="Structured predicates, e.g. ['concentrated_ownership(acme)']")
    relevant_vyaptis: list[str] = dspy.OutputField(
        desc="Vyāpti IDs relevant to this query")


class VerbalizePredicates(dspy.Signature):
    """Translate predicates back to natural language for round-trip check."""
    predicates: list[str] = dspy.InputField()
    ontology_snippet: str = dspy.InputField()
    verbalization: str = dspy.OutputField()


class CheckFaithfulness(dspy.Signature):
    """Check if round-trip translation preserves the original meaning."""
    original_query: str = dspy.InputField()
    verbalized_predicates: str = dspy.InputField()
    faithful: bool = dspy.OutputField()
    discrepancies: list[str] = dspy.OutputField()


class OntologySnippetBuilder:
    """Layer 1: Build constrained vocabulary from knowledge store."""

    def build(self, knowledge_store: KnowledgeStore,
              relevant_vyaptis=None) -> str:
        snippet = "VALID PREDICATES — use ONLY these:\n\n"
        vyapti_ids = relevant_vyaptis or list(knowledge_store.vyaptis.keys())
        all_predicates = set()

        for vid in vyapti_ids:
            v = knowledge_store.vyaptis.get(vid)
            if not v:
                continue
            all_predicates.update(v.antecedents)
            all_predicates.add(v.consequent)
            snippet += f"RULE {vid}: {v.name}\n"
            snippet += f"  IF: {', '.join(v.antecedents)}\n"
            snippet += f"  THEN: {v.consequent}\n"
            snippet += f"  SCOPE: {', '.join(v.scope_conditions)}\n"
            if v.scope_exclusions:
                snippet += f"  EXCLUDES: {', '.join(v.scope_exclusions)}\n"
            snippet += "\n"

        snippet += "\nALL VALID PREDICATE NAMES:\n"
        for p in sorted(all_predicates):
            snippet += f"  - {p}(Entity)\n"
        snippet += (
            "\nOUTPUT FORMAT:\n"
            "Return predicates as: predicate_name(entity)\n"
            "Use ONLY predicate names from the list above.\n"
            "Include negation as: not_predicate_name(entity)\n"
        )
        return snippet


class GroundingCache:
    """
    Compile-time grounding cache for 0-LLM-call cache hits (thesis §10.2).
    Populated during KB construction with common NL patterns → predicate mappings.
    """

    def __init__(self):
        self._cache: dict[str, list[str]] = {}  # normalized_query → predicates

    def add(self, query_pattern: str, predicates: list[str]):
        self._cache[self._normalize(query_pattern)] = predicates

    def lookup(self, query: str) -> list[str] | None:
        normalized = self._normalize(query)
        # Exact match first
        if normalized in self._cache:
            return self._cache[normalized]
        # Substring match for common patterns
        for pattern, preds in self._cache.items():
            if pattern in normalized or normalized in pattern:
                return preds
        return None

    def populate_from_kb(self, knowledge_store: KnowledgeStore):
        """Auto-populate cache from vyāpti names and statements."""
        for vid, v in knowledge_store.vyaptis.items():
            # Cache the vyāpti's natural language statement → its predicates
            if v.statement and v.antecedents:
                self.add(v.statement, v.antecedents + [v.consequent])

    @staticmethod
    def _normalize(text: str) -> str:
        return ' '.join(text.lower().split())


class GroundingPipeline(dspy.Module):
    """
    v3: Two-layer default + three-layer escalation.

    DEFAULT (all queries, 0-2 LLM calls):
      Layer 0: Cache lookup (0 LLM calls) — thesis §10.2
      Layer 1: Ontology-constrained prompt (1 LLM call)
      Layer 5: Solver-feedback refinement (0-1 LLM calls)

    ESCALATION (on failure):
      Layer 2: Grammar-constrained decoding
      Layer 3: Ensemble consensus (N=5)
      Layer 4: Round-trip verification
    """

    def __init__(self, knowledge_store: KnowledgeStore,
                 datalog_engine: DatalogEngine):
        super().__init__()
        self.ks = knowledge_store
        self.engine = datalog_engine
        self.snippet_builder = OntologySnippetBuilder()
        self.grounder = dspy.ChainOfThought(GroundQuery)
        self.verbalizer = dspy.ChainOfThought(VerbalizePredicates)
        self.checker = dspy.ChainOfThought(CheckFaithfulness)
        # v3: Grounding cache for 0-LLM-call hits
        self.cache = GroundingCache()
        self.cache.populate_from_kb(knowledge_store)

    def forward(self, query: str) -> GroundingResult:
        # ── LAYER 0: Cache lookup (0 LLM calls) ──
        cached = self.cache.lookup(query)
        if cached:
            errors = self.engine.validate_predicates(cached)
            if not errors:
                return GroundingResult(
                    predicates=cached, confidence=1.0,
                    disputed=[], warnings=['grounding: cache hit'],
                    refinement_rounds=0, clarification_needed=False,
                )

        snippet = self.snippet_builder.build(self.ks)

        # ── DEFAULT LAYER 1: Single ontology-constrained grounding ──
        grounding = self.grounder(
            query=query,
            ontology_snippet=snippet,
            domain_type=self.ks.domain_type.name,
        )
        candidate_preds = grounding.predicates
        candidate_vyaptis = grounding.relevant_vyaptis
        confidence = 1.0  # Single-call default confidence

        # ── DEFAULT LAYER 5: Solver-feedback refinement ──
        refinement_rounds = 0
        for _ in range(3):
            errors = self.engine.validate_predicates(candidate_preds)
            if not errors:
                break
            error_ctx = f"Errors: {errors}. Fix using ONLY ontology predicates."
            refined = self.grounder(
                query=query + "\n\n" + error_ctx,
                ontology_snippet=snippet,
                domain_type=self.ks.domain_type.name,
            )
            candidate_preds = refined.predicates
            refinement_rounds += 1

        # ── ESCALATION CHECK ──
        # If solver still rejects or zero predicates, trigger escalation
        final_errors = self.engine.validate_predicates(candidate_preds)
        if final_errors or not candidate_preds:
            return self._escalation_path(
                query, snippet, candidate_preds, refinement_rounds)

        # Deterministic scope/decay checks
        warnings = []
        warnings.extend(self._check_scope(candidate_preds))
        warnings.extend(self._check_decay(candidate_vyaptis))

        return GroundingResult(
            predicates=candidate_preds,
            confidence=confidence,
            disputed=[],
            warnings=warnings,
            refinement_rounds=refinement_rounds,
            clarification_needed=False,
        )

    def _escalation_path(self, query, snippet, fallback_preds, prior_rounds):
        """Layers 2-4: Ensemble + round-trip (expensive, triggered on failure)."""
        # Layer 3: Ensemble grounding (N=5)
        groundings = []
        for i in range(5):
            g = self.grounder(
                query=query,
                ontology_snippet=snippet,
                domain_type=self.ks.domain_type.name,
                config={"rollout_id": i, "temperature": 0.7},
            )
            groundings.append(g)

        all_pred_sets = [set(g.predicates) for g in groundings]
        consensus_preds = set.intersection(*all_pred_sets)
        disputed_preds = set.union(*all_pred_sets) - consensus_preds
        total = len(consensus_preds) + len(disputed_preds)
        confidence = len(consensus_preds) / max(total, 1)

        if confidence < 0.4:
            return GroundingResult(
                predicates=list(consensus_preds),
                confidence=confidence,
                disputed=list(disputed_preds),
                warnings=["Grounding confidence too low — requesting clarification"],
                refinement_rounds=prior_rounds,
                clarification_needed=True,
            )

        candidate_preds = list(consensus_preds | disputed_preds)

        # Layer 4: Round-trip verification (if agreement < 0.9)
        if confidence < 0.9:
            verb = self.verbalizer(predicates=candidate_preds, ontology_snippet=snippet)
            faith = self.checker(
                original_query=query, verbalized_predicates=verb.verbalization)
            if not faith.faithful:
                candidate_preds = list(consensus_preds)
                confidence = 1.0 if consensus_preds else 0.0

        warnings = self._check_scope(candidate_preds)
        return GroundingResult(
            predicates=candidate_preds,
            confidence=confidence,
            disputed=list(disputed_preds),
            warnings=warnings,
            refinement_rounds=prior_rounds,
            clarification_needed=False,
        )

    def _check_scope(self, predicates):
        warnings = []
        for vid, v in self.ks.vyaptis.items():
            for excl in v.scope_exclusions:
                if any(excl.lower() in p.lower() for p in predicates):
                    warnings.append(f"SCOPE: {vid} excludes '{excl}' but query matches")
        return warnings

    def _check_decay(self, vyapti_ids):
        from datetime import datetime
        warnings = []
        for vid in (vyapti_ids or []):
            v = self.ks.vyaptis.get(vid)
            if v and v.decay_risk.value in ("high", "critical"):
                if v.last_verified:
                    age = (datetime.now() - v.last_verified).days
                    if age > 180:
                        warnings.append(f"DECAY: {vid} last verified {age}d ago")
                else:
                    warnings.append(f"DECAY: {vid} NEVER verified")
        return warnings
```

---

## 9. Module 6: Uncertainty Quantification

**File:** `anvikshiki/uncertainty.py`
**Purpose:** Three-way decomposition: epistemic + aleatoric + inference
**Dependencies:** `datalog_engine.py`, `schema.py`

### 9.1 v3 Change

- **Epistemic score divisor**: `value / 5.0` (was `value / 4.0` in v2) because the lattice now has 6 values (0-5)

### 9.2 Implementation Spec

```python
# anvikshiki/uncertainty.py

from .datalog_engine import DatalogEngine, EpistemicValue
from .schema import KnowledgeStore, DomainType, DecayRisk

DOMAIN_BASE_UNCERTAINTY = {
    DomainType.FORMAL: 0.0,
    DomainType.MECHANISTIC: 0.1,
    DomainType.EMPIRICAL: 0.3,
    DomainType.CRAFT: 0.5,
    DomainType.INTERPRETIVE: 0.6,
    DomainType.DESIGN: 0.4,
    DomainType.NORMATIVE: 0.5,
    DomainType.META_ANALYTICAL: 0.3,
}


def compute_uncertainty(
    engine: DatalogEngine,
    knowledge_store: KnowledgeStore,
    grounding_confidence: float,
    target_predicate: str,
    target_entity: str,
) -> dict:
    # --- Epistemic (from Heyting values) ---
    results = engine.query(target_predicate, target_entity)
    if not results:
        epistemic = {
            'status': 'NOT_DERIVED', 'value': 0,
            'explanation': f"No derivation for {target_predicate}({target_entity})",
        }
    else:
        entity, value = results[0]
        trace = engine.explain(target_predicate, target_entity)
        weakest = _find_weakest_link(trace)
        epistemic = {
            'status': value.name,
            'value': value.value,
            'weakest_link': weakest.name if weakest else "N/A",
            'derivation_depth': len(trace),
            'explanation': f"Derived with {value.name}" + (
                f" (limited by {weakest.name})" if weakest and weakest < value else ""
            ),
        }

    # --- Aleatoric (from domain type) ---
    domain_base = DOMAIN_BASE_UNCERTAINTY.get(knowledge_store.domain_type, 0.5)
    decay_count, total_rules = _count_decay_exposure(engine, knowledge_store)
    aleatoric = {
        'domain_base_uncertainty': domain_base,
        'decay_exposure': decay_count / max(total_rules, 1),
        'explanation': (
            f"Domain {knowledge_store.domain_type.name}: base={domain_base:.1f}. "
            f"{decay_count}/{total_rules} rules have high decay risk."
        ),
    }

    # --- Inference (from grounding) ---
    inference = {
        'grounding_confidence': grounding_confidence,
        'explanation': (
            f"Grounding agreement: {grounding_confidence:.2f}. " +
            ("Reliable." if grounding_confidence > 0.8
             else "Moderate." if grounding_confidence > 0.5
             else "Low — query may be ambiguous.")
        ),
    }

    # --- Aggregate (conservative: minimum) ---
    # v3: divide by 5.0 (6-value lattice: 0-5)
    if epistemic.get('value', 0) == 0:
        total = 0.0
    else:
        ep_score = epistemic['value'] / 5.0
        al_score = 1.0 - aleatoric['domain_base_uncertainty']
        in_score = inference['grounding_confidence']
        total = min(ep_score, al_score, in_score)

    return {
        'epistemic': epistemic,
        'aleatoric': aleatoric,
        'inference': inference,
        'total_confidence': total,
    }


def _find_weakest_link(trace):
    weakest = None
    for step in trace:
        for v in EpistemicValue:
            if v.name in step:
                if weakest is None or v < weakest:
                    weakest = v
    return weakest


def _count_decay_exposure(engine, ks):
    decay_count, total_rules = 0, 0
    for step in engine.trace:
        for vid, v in ks.vyaptis.items():
            if vid in step:
                total_rules += 1
                if v.decay_risk in (DecayRisk.HIGH, DecayRisk.CRITICAL):
                    decay_count += 1
    return decay_count, total_rules
```

---

## 10. Module 7: Provenance Chain Tracer

**File:** `anvikshiki/provenance.py`
**Purpose:** Deterministic provenance chain tracing through Datalog proof trees
**Dependencies:** `datalog_engine.py`, `schema.py`

> **v3 revision:** This module **replaces** `conformal.py` from the v2 Build Guide. Conformal prediction was removed because: (1) the scoring function was trivial word overlap; (2) the calibration set doesn't exist in practice; (3) CP cannot measure epistemic uncertainty in this architecture; (4) deterministic provenance is cheaper and more informative.

### 10.1 Implementation Spec

```python
# anvikshiki/provenance.py

from dataclasses import dataclass


@dataclass
class ProvenanceStep:
    """One step in a provenance chain."""
    vyapti_id: str
    vyapti_name: str
    antecedents: list[str]
    consequent: str
    epistemic_value: str
    sources: list[str]
    source_authority: dict  # Trust tier + venue (from source_authority.py)


@dataclass
class ProvenanceChain:
    """Complete provenance for a derived fact."""
    target_fact: str
    chain: list[ProvenanceStep]
    weakest_link: str
    all_sources: list[str]
    has_provisional: bool      # Any PROVISIONAL step in chain?


class ProvenanceTracer:
    """
    Builds provenance chains from Datalog derivation traces.
    Zero LLM calls — purely deterministic proof-tree walk.
    """

    def __init__(self, engine, knowledge_store):
        self.engine = engine
        self.ks = knowledge_store

    def trace(self, predicate: str, entity: str) -> ProvenanceChain:
        steps = []
        all_sources = []
        weakest = None
        has_provisional = False

        trace_entries = self.engine.explain(predicate, entity)

        for entry in trace_entries:
            for vid, v in self.ks.vyaptis.items():
                if vid in entry:
                    step = ProvenanceStep(
                        vyapti_id=vid,
                        vyapti_name=v.name,
                        antecedents=v.antecedents,
                        consequent=v.consequent,
                        epistemic_value=v.epistemic_status.value,
                        sources=v.sources,
                        source_authority={
                            'trust_tier': v.source_trust_tier,
                            'venue_tier': v.source_venue_tier,
                            'domain_match': v.source_domain_match,
                        },
                    )
                    steps.append(step)
                    all_sources.extend(v.sources)

                    if v.epistemic_status.value == "provisional":
                        has_provisional = True

                    if weakest is None or self._rank(
                        v.epistemic_status.value
                    ) < self._rank(weakest):
                        weakest = v.epistemic_status.value

        return ProvenanceChain(
            target_fact=f"{predicate}({entity})",
            chain=steps,
            weakest_link=weakest or "N/A",
            all_sources=list(set(all_sources)),
            has_provisional=has_provisional,
        )

    def _rank(self, status: str) -> int:
        return {"contested": 1, "open": 2, "provisional": 3,
                "hypothesis": 4, "established": 5}.get(status, 0)
```

### 10.2 Tests: `tests/test_provenance.py`

1. Derive a fact through a chain of 3 rules → verify provenance chain has 3 steps
2. Chain includes a PROVISIONAL rule → verify `has_provisional=True`
3. Chain includes HYPOTHESIS weakest → verify `weakest_link="hypothesis"`
4. All sources from chain rules appear in `all_sources`

---

## 11. Module 8: Cellular Sheaf

**File:** `anvikshiki/sheaf.py`
**Purpose:** Local-to-global consistency; hetvābhāsa detection as H¹ obstructions
**Dependencies:** `numpy`, `networkx`

### 11.1 v3 Change: Compile-Time / Query-Time Split

- `sheaf_laplacian()` and `global_consistency_score()` are **compile-time diagnostics** — run when KB changes, never at query time
- `detect_hetvabhasas()` (local coboundary) is the **only query-time operation** — O(k·d²) where k = query-relevant edges

### 11.2 Implementation

Unchanged from v2 Build Guide §11 (`KnowledgeSheaf` class with `coboundary()`, `detect_hetvabhasas()`, `sheaf_laplacian()`, `global_consistency_score()`). The implementation is identical — the change is operational: which methods run when.

---

## 12. Module 9: Source Authority

**File:** `anvikshiki/source_authority.py`
**Purpose:** Śabda-based source authority model for default epistemic status assignment
**Dependencies:** `enum`, `pydantic`

> **NEW in v3.** Formalizes classical Nyāya testimony conditions (āptavacana + abhiyoga) as trust-based epistemic defaults. The sheaf consistency check overrides these defaults when authorities contradict each other.

### 12.1 Implementation Spec

```python
# anvikshiki/source_authority.py

from enum import Enum
from pydantic import BaseModel
from typing import Optional


class TrustTier(str, Enum):
    CANONICAL = "canonical"       # Recognized authority in field
    CITED = "cited"               # Well-cited, peer-reviewed work
    CREDIBLE = "credible"         # Domain expert, limited verification
    UNKNOWN = "unknown"           # No track record signal


class VenueTier(str, Enum):
    PEER_REVIEWED = "peer_reviewed"
    EDITED = "edited"
    SELF_PUBLISHED = "self_published"


class SourceAuthority(BaseModel):
    author: str
    domains_of_competence: list[str] = []
    trust_tier: TrustTier = TrustTier.UNKNOWN
    basis: list[str] = []
    citation_count: Optional[int] = None
    institutional_affiliation: Optional[str] = None
    peer_reviewed_in_domain: bool = False
    known_biases: list[str] = []


class SourceDocument(BaseModel):
    title: str
    authors: list[SourceAuthority] = []
    publication_venue: str = ""
    venue_tier: VenueTier = VenueTier.SELF_PUBLISHED
    year: int = 2025
    domain_tags: list[str] = []


# Trust-based epistemic assignment table (thesis §13.3)
# Returns: EpistemicStatus string value
def assign_default_status(
    author_trust: TrustTier,
    venue: VenueTier,
    claim_type: str,  # "mechanism", "definitional", "empirical"
    domain_match: bool = True,
) -> str:
    """
    Deterministic function: (trust, venue, claim_type, domain_match) → epistemic status.
    If author speaks outside domains_of_competence, trust is downgraded one level.
    """
    effective_trust = author_trust
    if not domain_match:
        downgrade = {
            TrustTier.CANONICAL: TrustTier.CITED,
            TrustTier.CITED: TrustTier.CREDIBLE,
            TrustTier.CREDIBLE: TrustTier.UNKNOWN,
            TrustTier.UNKNOWN: TrustTier.UNKNOWN,
        }
        effective_trust = downgrade[author_trust]

    # Lookup table from thesis §13.3
    if effective_trust == TrustTier.CANONICAL:
        if venue == VenueTier.PEER_REVIEWED:
            return "established"
        elif venue == VenueTier.EDITED:
            return "established" if claim_type in ("mechanism", "definitional") else "hypothesis"
        else:
            return "hypothesis"
    elif effective_trust == TrustTier.CITED:
        if venue == VenueTier.PEER_REVIEWED:
            return "established"
        else:
            return "hypothesis"
    elif effective_trust == TrustTier.CREDIBLE:
        return "hypothesis"
    else:  # UNKNOWN
        if venue == VenueTier.PEER_REVIEWED:
            return "hypothesis"
        else:
            return "provisional"
```

### 12.2 Sheaf Override of Trust Defaults (thesis §13.4)

When two canonical authorities contradict each other, the sheaf check detects H¹ ≠ 0. The trust-based defaults are then **automatically overridden** to CONTESTED:

```python
def resolve_authority_conflicts(
    vyaptis: dict[str, 'Vyapti'],
    sheaf_violations: list[dict],
) -> dict[str, str]:
    """
    Override trust-based epistemic defaults when sheaf detects contradictions.

    Thesis §13.4: "Trust is the default. Sheaf consistency is the override.
    Authority alone cannot suppress genuine scholarly disagreement."

    Returns: dict of vyapti_id → new epistemic status ("contested")
    """
    overrides = {}
    for violation in sheaf_violations:
        edge = violation.get('edge', ())
        if len(edge) != 2:
            continue
        # Find vyāptis whose predicates are involved in the conflict
        for vid, v in vyaptis.items():
            if v.consequent in edge or any(a in edge for a in v.antecedents):
                if v.epistemic_status.value in ("established", "hypothesis"):
                    overrides[vid] = "contested"
    return overrides
```

### 12.3 Tests: `tests/test_source_authority.py`

1. Canonical + peer-reviewed + mechanism → `"established"`
2. Unknown + self-published → `"provisional"`
3. Canonical speaking outside domain (domain_match=False) → downgraded to CITED tier
4. All 10 table entries from thesis §13.3 verified
5. **Sheaf override**: Two CANONICAL authorities contradict → both overridden to CONTESTED
6. **No false override**: Non-conflicting CANONICAL authorities remain ESTABLISHED

---

## 13. Module 10: Final Engine

**File:** `anvikshiki/engine.py`
**Purpose:** Assemble all components into the complete pipeline
**Dependencies:** All previous modules + `dspy`

### 13.1 v3 Pipeline (8 steps)

```
1. Cache / two-layer grounding (NL → verified predicates)  [0-2 LLM calls]
2. Ground facts into materialized Datalog                   [deterministic, incremental]
3. Forward chain (semi-naive on Δ only)                     [deterministic, polynomial]
4. Hetvābhāsa integrity check                              [deterministic]
5. Sheaf consistency check (local coboundary)               [deterministic, O(k·d²)]
6. Provenance chain tracing                                 [deterministic, zero-cost]
7. Three-way uncertainty decomposition                      [deterministic]
8. DSPy synthesis (calibrated NL response)                  [1 LLM call]
```

**Removed from v2:** Step 6 was "Conformal source verification" — now replaced by provenance tracing.
**Added in v3:** Grounding cache (step 1), incremental Datalog (step 2-3), provenance tracing (step 6), sheaf override of trust defaults.

### 13.2 Implementation Spec

```python
# anvikshiki/engine.py

import dspy
import numpy as np
from .schema import KnowledgeStore
from .grounding import GroundingPipeline, GroundingResult
from .datalog_engine import DatalogEngine, EpistemicValue
from .t2_compiler import compile_t2, ground_facts_from_predicates
from .sheaf import KnowledgeSheaf
from .provenance import ProvenanceTracer       # v3: replaces ConformalSourceVerifier
from .uncertainty import compute_uncertainty


class SynthesizeResponse(dspy.Signature):
    """Produce a calibrated response with epistemic qualification."""

    query: str = dspy.InputField()
    derivation_trace: str = dspy.InputField(desc="Datalog derivation steps")
    retrieved_prose: str = dspy.InputField(desc="Relevant guide text")
    uncertainty_report: str = dspy.InputField(desc="Uncertainty decomposition")
    hetvabhasa_violations: str = dspy.InputField(desc="Detected reasoning fallacies")

    response: str = dspy.OutputField(
        desc="Natural language response with epistemic qualification")
    sources_cited: list[str] = dspy.OutputField(
        desc="Reference Bank entries supporting claims")


def _synthesis_reward(args, pred) -> float:
    if not pred.response or len(pred.response) < 20:
        return 0.0
    score = 0.5
    if pred.sources_cited and len(pred.sources_cited) > 0:
        score += 0.3
    if any(w in pred.response.lower()
           for w in ["established", "hypothesis", "provisional", "contested", "uncertain"]):
        score += 0.2
    return score


class AnvikshikiEngine(dspy.Module):
    """
    The complete Ānvīkṣikī Engine (v3).

    Pipeline:
    0. Grounding cache lookup (0 LLM calls — thesis §10.2)
    1. Two-layer grounding with escalation (NL → verified predicates)
    2. Incremental Datalog forward chaining on Δ (thesis §10.2)
    3. Hetvābhāsa integrity check (deterministic)
    4. Sheaf consistency check (local coboundary)
    5. Sheaf override of trust defaults (thesis §13.4)
    6. Provenance chain tracing (replaces conformal source verification)
    7. Three-way uncertainty decomposition
    8. DSPy synthesis (calibrated NL response)
    """

    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        sheaf: KnowledgeSheaf,
        boolean_mode: bool = False,  # Phase 3+ by default
    ):
        super().__init__()
        self.ks = knowledge_store
        self.sheaf = sheaf
        self.boolean_mode = boolean_mode

        # v3: Pre-materialize Datalog engine at init (thesis §10.2)
        # Base facts are evaluated once; queries add Δ incrementally
        self.base_engine = compile_t2(knowledge_store, boolean_mode=boolean_mode)
        self.base_engine.evaluate()  # Materialize base facts to fixpoint

        self.grounding = GroundingPipeline(knowledge_store, self.base_engine)

        self._synthesizer = dspy.ChainOfThought(SynthesizeResponse)
        self.synthesizer = dspy.Refine(
            module=self._synthesizer,
            N=3,
            reward_fn=_synthesis_reward,
            threshold=0.5,
        )

    def forward(self, query: str, retrieved_chunks: list[str]):
        # STEP 1: Two-layer grounding (+ escalation if needed)
        grounding = self.grounding(query)

        if grounding.clarification_needed:
            return dspy.Prediction(
                response=(
                    f"I need clarification. Disputed elements: "
                    f"{', '.join(grounding.disputed)}. Could you specify?"
                ),
                confidence=grounding.confidence,
                uncertainty={'type': 'grounding_ambiguity'},
            )

        # STEP 2: Clone materialized engine + add query facts (thesis §10.2)
        # Instead of fresh compile_t2(), clone pre-materialized base engine
        # and run semi-naive only on the delta from grounded query facts
        import copy
        self.engine = copy.deepcopy(self.base_engine)
        grounded_facts = ground_facts_from_predicates(
            self.engine, grounding.predicates)

        # STEP 3: Semi-naive on Δ only (incremental, not full re-evaluation)
        iterations = self.engine.evaluate()

        # STEP 4: Hetvābhāsa check (deterministic)
        violations = self.engine.check_hetvabhasas()

        # STEP 5: Sheaf consistency check (local coboundary only)
        section = self._build_sheaf_section()
        sheaf_violations = self.sheaf.detect_hetvabhasas(section)

        all_violations = violations + [
            type('Violation', (), {
                'hetvabhasa_id': f"SHEAF_{i}",
                'name': v['interpretation'],
                'description': v['interpretation'],
                'triggered_by': [str(v['edge'])],
                'correction': "Local reasoning fails to glue globally",
            })()
            for i, v in enumerate(sheaf_violations)
        ]

        # STEP 6: Provenance chain tracing (v3: replaces conformal)
        tracer = ProvenanceTracer(self.engine, self.ks)
        provenance_chains = {}
        grounded_keys = {(f.predicate, f.entity) for f in grounded_facts}
        for (pred, entity), value in self.engine.facts.items():
            if value > EpistemicValue.BOTTOM and (pred, entity) not in grounded_keys:
                chain = tracer.trace(pred, entity)
                provenance_chains[f"{pred}({entity})"] = chain

        # STEP 7: Uncertainty decomposition
        primary_pred = self._find_primary_derived(grounded_facts)
        if primary_pred:
            uncertainty = compute_uncertainty(
                self.engine, self.ks, grounding.confidence,
                primary_pred[0], primary_pred[1],
            )
        else:
            uncertainty = {
                'epistemic': {'status': 'NO_DERIVATION'},
                'aleatoric': {'domain_base_uncertainty': 0.5},
                'inference': {'grounding_confidence': grounding.confidence},
                'total_confidence': 0.0,
            }

        # STEP 8: Synthesize response
        context = '\n'.join(retrieved_chunks)
        if grounding.warnings:
            context += f"\n\nWARNINGS: {'; '.join(grounding.warnings)}"
        if all_violations:
            context += f"\n\nFALLACY ALERTS: {'; '.join(v.name for v in all_violations)}"

        response = self.synthesizer(
            query=query,
            derivation_trace='\n'.join(self.engine.trace),
            retrieved_prose=context,
            uncertainty_report=str(uncertainty),
            hetvabhasa_violations=str([
                {'id': v.hetvabhasa_id, 'name': v.name, 'correction': v.correction}
                for v in all_violations
            ]),
        )

        return dspy.Prediction(
            response=response.response,
            sources=response.sources_cited,
            uncertainty=uncertainty,
            proof_trace=self.engine.trace,
            provenance=provenance_chains,          # v3: new output
            violations=[
                {'id': v.hetvabhasa_id, 'name': v.name, 'correction': v.correction}
                for v in all_violations
            ],
            grounding_confidence=grounding.confidence,
            derivation_iterations=iterations,
        )

    def _build_sheaf_section(self):
        section = {}
        for (pred, entity), value in self.engine.facts.items():
            if pred not in section:
                section[pred] = np.zeros(self.sheaf.stalk_dim)
            section[pred][0] = value.value / 5.0  # v3: 6-value lattice
            section[pred][1] = 1.0
        return section

    def _find_primary_derived(self, grounded_facts):
        grounded_keys = {(f.predicate, f.entity) for f in grounded_facts}
        for (pred, entity), value in self.engine.facts.items():
            if value > EpistemicValue.BOTTOM and (pred, entity) not in grounded_keys:
                return (pred, entity)
        return None
```

---

## 14. Module 11: Optimization

**File:** `anvikshiki/optimize.py`
**Purpose:** DSPy 3.x optimization pipeline
**Dependencies:** `dspy`

### 14.1 Implementation

Unchanged from v2 Build Guide §13 (`calibration_metric`, `optimize_engine`, `evaluate_engine`). The reward function now checks for `"provisional"` in addition to v2's epistemic terms.

---

## 15. Module 12: KB Bootstrapping

**File:** `anvikshiki/bootstrap.py`
**Purpose:** Automated KB construction from domain texts with PROVISIONAL status
**Dependencies:** `dspy`, `schema.py`, `source_authority.py`

> **NEW in v3.** Reduces expert dependency by using LLMs for initial KB construction, assigning PROVISIONAL status to all auto-generated rules, and targeting expert validation to sheaf-flagged inconsistencies and ESTABLISHED claims only (~15-20% of rules).

### 15.1 Implementation Spec

```python
# anvikshiki/bootstrap.py

import dspy
from pydantic import BaseModel
from .schema import KnowledgeStore, Vyapti, EpistemicStatus, CausalStatus, Confidence
from .source_authority import assign_default_status, TrustTier, VenueTier


class ExtractedVyapti(BaseModel):
    name: str
    statement: str
    antecedents: list[str]
    consequent: str
    causal_status: str
    scope_conditions: list[str] = []
    scope_exclusions: list[str] = []


class ExtractVyaptisFromText(dspy.Signature):
    """Extract domain rules (vyāptis) from a text passage.
    Each vyāpti is an if-then rule about the domain."""

    passage: str = dspy.InputField(desc="Domain text to extract rules from")
    domain_type: str = dspy.InputField(desc="Domain classification")
    existing_predicates: list[str] = dspy.InputField(
        desc="Already-known predicates, reuse these when possible")

    vyaptis: list[ExtractedVyapti] = dspy.OutputField(
        desc="Extracted if-then rules with antecedents and consequents")


class BootstrapPipeline(dspy.Module):
    """
    Auto-construct KB from domain texts.

    All auto-generated rules receive PROVISIONAL status.
    Expert review is targeted to:
      1. Rules flagged by sheaf consistency check
      2. Rules claimed as ESTABLISHED by source authority
      3. Rules in critical inference chains
    """

    def __init__(self):
        super().__init__()
        self.extractor = dspy.ChainOfThought(ExtractVyaptisFromText)

    def bootstrap_from_texts(
        self,
        texts: list[str],
        domain_type: str,
        source_trust: TrustTier = TrustTier.UNKNOWN,
        source_venue: VenueTier = VenueTier.SELF_PUBLISHED,
    ) -> dict[str, Vyapti]:
        """Extract vyāptis from texts, assign PROVISIONAL status."""
        all_vyaptis = {}
        existing_predicates = []
        counter = 1

        for text in texts:
            result = self.extractor(
                passage=text,
                domain_type=domain_type,
                existing_predicates=existing_predicates,
            )

            for ev in result.vyaptis:
                vid = f"V_AUTO_{counter:03d}"
                counter += 1

                # Determine default epistemic status from source authority
                default_status = assign_default_status(
                    source_trust, source_venue,
                    claim_type=ev.causal_status,
                    domain_match=True,
                )

                # Override to PROVISIONAL unless source is very strong
                if default_status != "established":
                    final_status = EpistemicStatus.PROVISIONAL
                else:
                    final_status = EpistemicStatus.WORKING_HYPOTHESIS

                vyapti = Vyapti(
                    id=vid,
                    name=ev.name,
                    statement=ev.statement,
                    causal_status=CausalStatus(ev.causal_status)
                        if ev.causal_status in [e.value for e in CausalStatus]
                        else CausalStatus.EMPIRICAL,
                    scope_conditions=ev.scope_conditions,
                    scope_exclusions=ev.scope_exclusions,
                    confidence=Confidence(
                        existence=0.5, formulation=0.3, evidence="auto_extracted"),
                    epistemic_status=final_status,
                    antecedents=ev.antecedents,
                    consequent=ev.consequent,
                    source_trust_tier=source_trust.value,
                    source_venue_tier=source_venue.value,
                )

                all_vyaptis[vid] = vyapti
                existing_predicates.extend(ev.antecedents)
                existing_predicates.append(ev.consequent)
                existing_predicates = list(set(existing_predicates))

        return all_vyaptis

    def identify_review_targets(
        self, vyaptis: dict[str, Vyapti], sheaf_violations: list[dict]
    ) -> list[str]:
        """Identify which auto-generated vyāptis need expert review."""
        targets = set()

        # 1. Any vyāpti involved in a sheaf violation
        for violation in sheaf_violations:
            edge = violation.get('edge', ())
            for vid, v in vyaptis.items():
                if v.consequent in edge or any(a in edge for a in v.antecedents):
                    targets.add(vid)

        # 2. Any vyāpti claiming ESTABLISHED or higher
        for vid, v in vyaptis.items():
            if v.epistemic_status == EpistemicStatus.ESTABLISHED:
                targets.add(vid)

        return sorted(targets)
```

### 15.2 Tests: `tests/test_bootstrap.py`

1. Extract vyāptis from sample text → all have PROVISIONAL or WORKING_HYPOTHESIS status
2. `identify_review_targets` flags sheaf-violation rules
3. No auto-generated rule receives ESTABLISHED without canonical sources

---

## 16. Testing Strategy

### 16.1 Unit Tests (No LLM Calls)

| Module | Test Focus |
|--------|-----------|
| `schema.py` | Pydantic validation, PROVISIONAL status, source authority fields |
| `datalog_engine.py` | Boolean/lattice mode, PROVISIONAL propagation, semi-naive, termination |
| `t2_compiler.py` | YAML loading, PROVISIONAL mapping, rule compilation |
| `t3_compiler.py` | Graph construction, chunk splitting, reference detection |
| `uncertainty.py` | UQ with 6-value lattice (divides by 5.0), weakest-link |
| `provenance.py` | Chain tracing, PROVISIONAL detection, source aggregation |
| `sheaf.py` | Coboundary correctness, Laplacian symmetry, violation detection |
| `source_authority.py` | Trust-tier lookup table, domain-match downgrade |
| `bootstrap.py` | PROVISIONAL assignment, review target identification |

### 16.2 Integration Tests (Require LLM)

```python
# tests/test_engine.py

import dspy
import pytest
from anvikshiki.schema import KnowledgeStore
from anvikshiki.t2_compiler import load_knowledge_store, compile_t2
from anvikshiki.engine import AnvikshikiEngine
from anvikshiki.sheaf import KnowledgeSheaf
from anvikshiki.t3_compiler import compile_t3

@pytest.fixture
def setup_engine():
    dspy.configure(lm=dspy.LM('openai/gpt-4o-mini'))
    ks = load_knowledge_store("data/sample_architecture.yaml")
    graph, chunks = compile_t3({}, ks)
    sheaf = KnowledgeSheaf(graph)
    # v3: No conformal verifier needed
    engine = AnvikshikiEngine(ks, sheaf, boolean_mode=False)
    return engine, chunks

def test_full_pipeline(setup_engine):
    engine, chunks = setup_engine
    result = engine(
        query="What happens when a company has concentrated ownership?",
        retrieved_chunks=[c.text for c in chunks[:3]] if chunks else [""],
    )
    assert result.response
    assert result.uncertainty
    assert 'epistemic' in result.uncertainty
    # v3: provenance chains available
    assert hasattr(result, 'provenance')
```

### 16.3 Running Tests

```bash
# Unit tests (no LLM, fast)
pytest tests/ -k "not integration" -v

# Integration tests (requires API key)
OPENAI_API_KEY=sk-... pytest tests/ -k "integration" -v

# All tests
pytest tests/ -v
```

---

## 17. Phase-by-Phase Build Order

### Phase 1: DSPy Only (Week 1-2)

1. `schema.py` — data structures (with v3 PROVISIONAL status + source authority fields)
2. `t2_compiler.py` — YAML → KnowledgeStore (parser only)
3. `t3_compiler.py` — guide text → graph + chunks
4. `grounding.py` — two-layer default grounding
5. `engine.py` — Phase 1 variant (LLM-only reasoning)

**Validation:** Run grounding pipeline against sample queries. Verify two-layer default handles most queries in 1-2 calls.

### Phase 2: DSPy + Boolean Datalog (Week 3-4)

1. `datalog_engine.py` — with `boolean_mode=True`
2. Update `t2_compiler.py` — compile vyāptis as Datalog rules
3. Update `engine.py` — Datalog replaces LLM reasoning

**Validation:** Compare Phase 1 (LLM reasoning) vs Phase 2 (Datalog). Verify derivation traces, hetvābhāsa checks, scope exclusions.

### Phase 3: DSPy + Lattice Datalog + UQ (Week 5)

One-line change: `boolean_mode=False`

Add:
1. `uncertainty.py` — three-way decomposition (with `/ 5.0` divisor)
2. `provenance.py` — deterministic chain tracing

**Validation:** Verify PROVISIONAL propagation, provenance chains, UQ decomposition.

### Phase 4: DSPy + Lattice Datalog + Sheaf + UQ (Week 6-7)

Add:
1. `sheaf.py` — coboundary, Laplacian, violation detection
2. `source_authority.py` — śabda-based epistemic defaults
3. `bootstrap.py` — automated KB construction
4. Update `engine.py` — sheaf check + provenance after Datalog

**Validation:** Known inconsistency → sheaf detects H¹ ≠ 0. Bootstrap pipeline produces PROVISIONAL rules. Source authority assigns correct defaults.

---

## 18. DSPy 3.x Migration Notes

### Complete API Translation Table

| Concept | DSPy 2.x (thesis code) | DSPy 3.1.x (this guide) |
|---------|-------------------------|--------------------------|
| **LM setup** | `dspy.OpenAI('gpt-4')` | `dspy.LM('openai/gpt-4o-mini')` |
| **Configure** | `dspy.settings.configure(lm=lm)` | `dspy.configure(lm=lm)` |
| **Scoped LM** | N/A | `with dspy.context(lm=other_lm): ...` |
| **Base class** | `dspy.Program` or `dspy.Module` | `dspy.Module` only |
| **Hard constraint** | `dspy.Assert(cond, msg)` | `dspy.Refine(module, N, reward_fn, threshold)` |
| **Soft constraint** | `dspy.Suggest(cond, msg)` | `dspy.BestOfN(module, N, reward_fn, threshold)` |
| **Typed output** | `dspy.TypedPredictor` | Native: `field: MyModel = dspy.OutputField()` |
| **Optimizer** | `MIPROv2(metric, num_candidates=10)` | `dspy.MIPROv2(metric, auto="medium")` |
| **Retriever** | Community RMs | `dspy.retrievers.Embeddings(embedder, corpus, k=5)` |
| **Async** | N/A | `dspy.asyncify(module)` |
| **Parallel** | Manual threading | `dspy.Parallel(num_threads=N)` or `module.batch()` |
| **Cache bypass** | N/A | `config={"rollout_id": i, "temperature": 1.0}` |

### Reward Functions for dspy.Refine

```python
def my_reward(args, pred):
    """0.0 = unacceptable, 1.0 = perfect."""
    score = 0.0
    if pred.response and len(pred.response) > 10:
        score += 0.5
    if hasattr(pred, 'sources_cited') and pred.sources_cited:
        score += 0.3
    return score

refined = dspy.Refine(module=my_cot, N=3, reward_fn=my_reward, threshold=0.7)
```

---

## 19. Appendix A: egglog Integration

If performance becomes a bottleneck, swap in egglog (Rust-backed Datalog with native lattice merge):

```bash
pip install egglog
```

```python
# anvikshiki/egglog_backend.py

from egglog import EGraph

def create_heyting_engine():
    eg = EGraph()
    eg.run_program("""
        ; v3 Heyting lattice: 0=BOTTOM, 1=CONTESTED, 2=OPEN,
        ;   3=PROVISIONAL, 4=HYPOTHESIS, 5=ESTABLISHED
        (function derived (String String) i64 :merge (min old new))
        (function rule_confidence (String) i64)

        (set (rule_confidence "V01") 5)  ; ESTABLISHED
        (set (derived "concentrated_ownership" "acme") 5)

        (rule ((= ant_val (derived "concentrated_ownership" ?entity))
               (= conf (rule_confidence "V01")))
              ((set (derived "long_horizon_possible" ?entity)
                    (min ant_val conf))))
        (run 10)
    """)
    return eg
```

**When to use egglog:** >1000 rules/facts, or need equality saturation.
**When to keep pure Python:** Need full proof traces, custom hetvābhāsa checks, <500 rules.

---

## 20. Appendix B: Grammar-Constrained Decoding

### For API Models

```python
# Option A: DSPy's built-in JSONAdapter
dspy.configure(lm=dspy.LM('openai/gpt-4o-mini'), adapter=dspy.JSONAdapter())

# Option B: Instructor for Pydantic validation + retries
import instructor
client = instructor.from_provider("openai/gpt-4o-mini")
```

### For Local Models

```bash
# SGLang with XGrammar (token-level grammar enforcement)
python -m sglang.launch_server --model meta-llama/Llama-3.1-8B-Instruct --port 7501
```

```python
lm = dspy.LM('openai/meta-llama/Llama-3.1-8B-Instruct',
              api_base='http://localhost:7501/v1', api_key='')
dspy.configure(lm=lm, adapter=dspy.JSONAdapter())
```

### Practical Recommendation

- **Development:** `dspy.JSONAdapter()` + OpenAI API
- **Production (API):** Instructor + OpenAI/Anthropic
- **Production (local):** SGLang + XGrammar

---

## Quick Start

```python
import dspy
from anvikshiki.t2_compiler import load_knowledge_store, compile_t2
from anvikshiki.t3_compiler import compile_t3
from anvikshiki.sheaf import KnowledgeSheaf
from anvikshiki.engine import AnvikshikiEngine

# 1. Configure
dspy.configure(lm=dspy.LM('openai/gpt-4o-mini'))

# 2. Load knowledge base
ks = load_knowledge_store("data/sample_architecture.yaml")

# 3. Build T3 corpus
graph, chunks = compile_t3({}, ks)

# 4. Initialize sheaf (v3: no conformal verifier)
sheaf = KnowledgeSheaf(graph)

# 5. Create engine (Phase 3: lattice mode)
engine = AnvikshikiEngine(ks, sheaf, boolean_mode=False)

# 6. Query
result = engine(
    query="What strategic advantages does concentrated ownership provide?",
    retrieved_chunks=[c.text for c in chunks[:5]] if chunks else [""],
)

print(result.response)
print(f"Confidence: {result.uncertainty['total_confidence']:.2f}")
print(f"Proof trace: {result.proof_trace}")
print(f"Provenance: {result.provenance}")  # v3: new output
print(f"Violations: {result.violations}")
```

---

*This document is the implementation companion to `thesis_v3(1).md`. The thesis describes the architecture and theory; this guide shows how to build it with current tools.*

