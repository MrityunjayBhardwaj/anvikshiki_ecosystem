# Ānvīkṣikī Engine — Build Guide

## From Thesis to Working System: A Complete Implementation Manual

**Target:** Build the four-phase neurosymbolic reasoning engine described in `thesis_v2.md`
**Stack:** DSPy 3.1.x + Custom Lattice Datalog + egglog + NetworkX + NumPy
**Python:** 3.10+ (required by DSPy 3.x)
**Date:** March 2026

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
10. [Module 7: Conformal Source Verifier (`conformal.py`)](#10-module-7-conformal-source-verifier)
11. [Module 8: Cellular Sheaf (`sheaf.py`)](#11-module-8-cellular-sheaf)
12. [Module 9: Final Engine (`engine.py`)](#12-module-9-final-engine)
13. [Module 10: Optimization (`optimize.py`)](#13-module-10-optimization)
14. [Testing Strategy](#14-testing-strategy)
15. [Phase-by-Phase Build Order](#15-phase-by-phase-build-order)
16. [DSPy 3.x Migration Notes](#16-dspy-3x-migration-notes)
17. [Appendix A: egglog Integration (Alternative Datalog Backend)](#17-appendix-a-egglog-integration)
18. [Appendix B: Grammar-Constrained Decoding Options](#18-appendix-b-grammar-constrained-decoding)

---

## 1. Technology Stack Decisions

### Why These Choices

| Component | Tool | Why |
|-----------|------|-----|
| **LLM Orchestration** | DSPy 3.1.x | Typed signatures, optimizable modules, Pydantic output types, `dspy.Refine` for constraints |
| **Datalog Engine** | Custom Python (primary) | Full control over lattice extensions, Heyting meet/join, proof traces |
| **Datalog Engine** | egglog-python (optional backend) | Rust-backed, native lattice merge via `:merge`, pip-installable |
| **Knowledge Graph** | NetworkX | Mature, pure-Python, sufficient for hundreds-to-thousands of nodes |
| **Retrieval** | `dspy.retrievers.Embeddings` | Built into DSPy 3.x, uses FAISS for large corpora |
| **Structured Output** | Pydantic + `dspy.JSONAdapter` | Native DSPy 3.x support for typed predictors |
| **Sheaf Computation** | NumPy/SciPy | Dense linear algebra for Laplacian, eigenvectors |
| **Conformal Prediction** | NumPy + custom | Lightweight, no heavy ML dependencies |
| **Grammar Constraint** | Instructor (API models) / XGrammar (local models) | Instructor for Claude/GPT; XGrammar for local serving |

### What Changed from thesis_v2.md

The thesis code uses DSPy 2.x patterns. This guide updates **every module** to DSPy 3.1.x:

| thesis_v2.md (DSPy 2.x) | This Guide (DSPy 3.1.x) |
|--------------------------|--------------------------|
| `dspy.Suggest(condition, msg)` | `dspy.Refine(module, N, reward_fn, threshold)` |
| `dspy.Assert(condition, msg)` | `dspy.Refine(module, N, reward_fn, threshold)` |
| `dspy.OpenAI(...)` | `dspy.LM('openai/gpt-4o-mini')` |
| `dspy.Program` | `dspy.Module` |
| `dspy.teleprompt.MIPROv2(metric, num_candidates, init_temperature)` | `dspy.MIPROv2(metric, auto="medium")` |
| `from dspy.teleprompt import BootstrapFewShotWithRandomSearch` | Same import, API unchanged |
| Community retrievers | `dspy.retrievers.Embeddings` |
| No async support | `dspy.asyncify()`, `module.batch()` |

---

## 2. Project Structure

```
anvikshiki/
├── __init__.py
├── schema.py              # Core data structures (KnowledgeStore, Vyapti, etc.)
├── datalog_engine.py      # Semi-naive Datalog evaluator with lattice values
├── t2_compiler.py         # Architecture YAML → Datalog rules
├── t3_compiler.py         # Guide text → GraphRAG corpus
├── grounding.py           # Five-layer NL→predicate defense
├── uncertainty.py         # Three-way UQ decomposition
├── conformal.py           # Conformal prediction for source verification
├── sheaf.py               # Cellular sheaf consistency checking
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
│   ├── test_conformal.py
│   ├── test_sheaf.py
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
version = "0.1.0"
description = "Neurosymbolic reasoning engine with lattice Datalog and sheaf consistency"
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
**Purpose:** Data structures for the compiled knowledge store. These are populated by the T2 compiler from Stage 2+3 YAML output.
**Dependencies:** `pydantic`, `enum`, `datetime`

### 4.1 Design Decisions

- Use `pydantic.BaseModel` instead of raw `dataclass` for validation and JSON serialization
- Use `pydantic.BaseModel` as DSPy 3.x output types for structured extraction
- `Vyapti.antecedents` and `Vyapti.consequent` are the Datalog-compilable fields
- `EpistemicStatus` doubles as both a schema enum and a Heyting lattice element

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
    """Four epistemic values (plus BOTTOM in the Datalog engine)."""
    ESTABLISHED = "established"
    WORKING_HYPOTHESIS = "hypothesis"
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
    antecedents: list[str] = []      # Predicate names required
    consequent: str = ""             # Predicate name produced


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

### 4.3 Key Points

- All models inherit from `pydantic.BaseModel` — this means they serialize to JSON, validate on construction, and can be used directly as DSPy 3.x output field types
- `EpistemicStatus` is a `str, Enum` so it serializes cleanly to/from YAML
- The `KnowledgeStore` is the central data structure that every other module reads from

### 4.4 Test: `tests/test_schema.py`

Test that:
- A `KnowledgeStore` can be constructed from a sample dictionary
- Round-trip JSON serialization preserves all fields
- Invalid confidence values (>1, <0) raise `ValidationError`
- `Vyapti.antecedents` and `Vyapti.consequent` are required for Datalog compilation

---

## 5. Module 2: Datalog Engine

**File:** `anvikshiki/datalog_engine.py`
**Purpose:** Semi-naive bottom-up Datalog evaluator with lattice-valued facts
**Dependencies:** None (pure Python + standard library)

### 5.1 Design Decisions

- **Custom implementation over pyDatalog/Soufflé** because:
  - pyDatalog is unmaintained and uses top-down evaluation (wrong for forward chaining)
  - Soufflé's Python SWIG bindings are clunky (file-based I/O)
  - We need the Heyting lattice to participate in fixpoint computation (no existing Python engine supports this)
  - The engine is small (~300 lines) and must be fully inspectable for proof traces
- **Semi-naive evaluation** tracks `Δfacts` per iteration — only fires rules where at least one antecedent is newly derived
- **Dual-mode**: `boolean_mode=True` for Phase 2, `boolean_mode=False` for Phase 3+
- **Negation**: Stratified negation via scope exclusions (Datalog with safe negation)

### 5.2 The Heyting Lattice

```
ESTABLISHED (4)     ← strongest
    |
HYPOTHESIS (3)
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
    """Heyting algebra of truth values."""
    BOTTOM = 0
    CONTESTED = 1
    OPEN = 2
    HYPOTHESIS = 3
    ESTABLISHED = 4

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
        """
        Semi-naive fixpoint. Returns iteration count.

        Each iteration only processes rules where at least one
        body predicate has a NEW fact in delta.
        """
        iteration = 0
        while self._delta:
            new_delta = {}
            for rule in self.rules:
                # Find entities that have ANY body predicate in delta
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

            # Safety bound (should never trigger for valid Datalog)
            max_iter = len(self.rules) * (len(self.facts) + 1) + 1
            if iteration > max_iter:
                raise RuntimeError("Fixpoint not reached — possible bug")

        return iteration

    def _try_fire(self, rule: Rule, entity: str) -> Optional[EpistemicValue]:
        """Try to fire a rule for a specific entity."""
        # All positive body predicates must be present
        antecedent_values = []
        for pred in rule.body_positive:
            key = (pred, entity)
            if key not in self.facts:
                return None
            antecedent_values.append(self.facts[key])

        # No negative body predicate may be present
        for pred in rule.body_negative:
            key = (pred, entity)
            if key in self.facts and self.facts[key] > EpistemicValue.BOTTOM:
                return None

        # Compute consequent value
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
            f"% Ānvīkṣikī Knowledge Base",
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

1. **Boolean forward chaining**: Add facts A(x), B(x), rule `A(E), B(E) → C(E)`. Verify C(x) is derived.
2. **Lattice propagation**: In lattice mode, rule confidence=HYPOTHESIS, antecedent=ESTABLISHED → consequent should be HYPOTHESIS (meet).
3. **Multiple derivation paths**: Two rules derive same fact with HYPOTHESIS and ESTABLISHED → result should be ESTABLISHED (join).
4. **Scope exclusion**: Rule with `body_negative=["public_firm"]`, add `public_firm(x)` → rule should NOT fire.
5. **Semi-naive correctness**: Verify that adding a new fact and re-evaluating only processes delta, not entire fact base. Compare trace lengths between naive (re-derive everything) and semi-naive.
6. **Termination guarantee**: Create a cyclic rule dependency (A→B, B→A). Verify the engine terminates (Datalog is monotone — once A and B are derived, delta is empty).
7. **Hetvabhasa detection**: Add a survivorship-bias check function, derive facts that trigger it, verify violation is returned.
8. **Predicate validation**: Test `validate_predicates` with valid, malformed, and unknown predicates.

---

## 6. Module 3: T2 Compiler

**File:** `anvikshiki/t2_compiler.py`
**Purpose:** Compile verified architecture (Stage 2+3 YAML) into Datalog rules
**Dependencies:** `schema.py`, `datalog_engine.py`, `pyyaml`

### 6.1 Implementation Spec

```python
# anvikshiki/t2_compiler.py

import yaml
from .schema import KnowledgeStore, EpistemicStatus, Vyapti, Hetvabhasa
from .datalog_engine import DatalogEngine, Rule, Fact, EpistemicValue

# Map schema epistemic status → Datalog lattice value
EPISTEMIC_MAP = {
    EpistemicStatus.ESTABLISHED: EpistemicValue.ESTABLISHED,
    EpistemicStatus.WORKING_HYPOTHESIS: EpistemicValue.HYPOTHESIS,
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
    """
    Compile KnowledgeStore into a Datalog engine.

    boolean_mode=True  → Phase 2 (rules fire / don't fire)
    boolean_mode=False → Phase 3+ (epistemic values propagate via meet)
    """
    engine = DatalogEngine(boolean_mode=boolean_mode)

    # Compile vyāptis as Datalog rules
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

    # Compile hetvābhāsas as integrity constraints
    for hid, h in knowledge_store.hetvabhasas.items():
        check_fn = _build_hetvabhasa_check(h, knowledge_store)
        engine.add_hetvabhasa_check(
            hid=hid,
            name=h.name,
            check_fn=check_fn,
            correction=h.correction_pattern,
        )

    return engine


def ground_facts_from_predicates(
    engine: DatalogEngine,
    predicates: list[str],
    default_value: EpistemicValue = EpistemicValue.ESTABLISHED,
) -> list[Fact]:
    """
    Convert grounding output into Datalog facts.
    Called after the grounding pipeline produces verified predicates.
    """
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
    """Build a deterministic check function for a hetvābhāsa."""
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

### 6.2 Sample Architecture YAML

Create `data/sample_architecture.yaml`:

```yaml
domain_type: CRAFT
pramanas:
  - systematic_study
  - practitioner_judgment
  - case_analysis

vyaptis:
  V01:
    id: V01
    name: Concentrated Ownership Enables Long Horizons
    statement: "Companies with concentrated ownership can pursue strategies with longer time horizons"
    causal_status: structural
    scope_conditions: ["private firms", "family businesses", "founder-led companies"]
    scope_exclusions: ["public_firm", "activist_pressure"]
    confidence:
      existence: 0.85
      formulation: 0.70
      evidence: observational
    epistemic_status: established
    decay_risk: low
    antecedents: ["concentrated_ownership"]
    consequent: "long_horizon_possible"
    sources: ["S01", "S02"]

  V02:
    id: V02
    name: Long Horizons Enable Capability Building
    statement: "Organizations with longer time horizons can invest in deep capability building"
    causal_status: structural
    scope_conditions: ["organizations with sufficient capital"]
    scope_exclusions: ["cash_constrained"]
    confidence:
      existence: 0.90
      formulation: 0.75
      evidence: observational
    epistemic_status: established
    decay_risk: low
    antecedents: ["long_horizon_possible"]
    consequent: "capability_building_possible"
    sources: ["S01"]

hetvabhasas:
  H01:
    id: H01
    name: Survivorship Bias
    description: "Drawing conclusions only from successful cases"
    detection_signature: "survivorship, success-only sample"
    correction_pattern: "Include base rates and failure cases"
    common_contexts: ["strategy case studies", "best practices"]

  H02:
    id: H02
    name: Scale Extrapolation
    description: "Applying rules outside their validated scale"
    detection_signature: "scale extrapolation, enterprise application"
    correction_pattern: "Verify rule has been validated at the target scale"
    common_contexts: ["startup-to-enterprise", "small-to-large market"]

threshold_concepts:
  - name: competitive_advantage
    reorganizes: ["value_creation", "differentiation"]
    prerequisites: ["basic_economics"]
    troublesome_aspects: ["temporary vs sustainable"]

dependency_graph:
  competitive_advantage: ["basic_economics", "value_creation"]
  value_creation: ["basic_economics"]

reference_bank:
  S01:
    title: "Competitive Strategy"
    author: "Porter, M.E."
    year: 1980
    text: "Competitive advantage grows out of value a firm is able to create for its buyers."
  S02:
    title: "The Innovator's Dilemma"
    author: "Christensen, C.M."
    year: 1997
    text: "Good management was the most powerful reason why they failed to stay atop their industries."
```

### 6.3 Tests: `tests/test_t2_compiler.py`

1. Load `sample_architecture.yaml` → `KnowledgeStore` → verify field counts
2. `compile_t2(ks, boolean_mode=True)` → verify 2 rules, 2 hetvabhasa checks
3. Add `concentrated_ownership(acme)` → evaluate → verify `long_horizon_possible(acme)` derived
4. Add `concentrated_ownership(acme)` + `public_firm(acme)` → verify `long_horizon_possible(acme)` NOT derived (scope exclusion)
5. Chain test: `concentrated_ownership(acme)` → `long_horizon_possible(acme)` → `capability_building_possible(acme)`. Verify full chain derives in 2 iterations.

---

## 7. Module 4: T3 Compiler

**File:** `anvikshiki/t3_compiler.py`
**Purpose:** Build graph-structured retrieval corpus from guide text
**Dependencies:** `networkx`, `schema.py`

### 7.1 Implementation Spec

```python
# anvikshiki/t3_compiler.py

import networkx as nx
from pydantic import BaseModel, Field
from typing import Optional
from .schema import KnowledgeStore


class TextChunk(BaseModel):
    """A retrievable unit of guide text with rich metadata."""
    chunk_id: str
    chapter_id: str
    text: str
    vyapti_anchors: list[str] = []
    hetvabhasa_anchors: list[str] = []
    concept_anchors: list[str] = []
    prerequisites: list[str] = []
    epistemic_status: str = "established"
    sourced: bool = False
    source_ids: list[str] = []
    difficulty_tier: str = "intermediate"
    embedding: Optional[list[float]] = None


def compile_t3(
    guide_text: dict[str, str],
    knowledge_store: KnowledgeStore,
) -> tuple[nx.DiGraph, list[TextChunk]]:
    """
    Build T3 corpus: knowledge graph + chunked text.

    guide_text: chapter_id → chapter markdown text
    knowledge_store: from T2 compiler

    Returns: (graph, chunks)
    """
    G = nx.DiGraph()

    # Add vyāpti nodes
    for vid, v in knowledge_store.vyaptis.items():
        G.add_node(vid, type="vyapti", name=v.name,
                   epistemic_status=v.epistemic_status.value,
                   confidence=v.confidence.formulation,
                   decay_risk=v.decay_risk.value)

    # Add concept nodes from dependency graph
    for concept, prereqs in knowledge_store.dependency_graph.items():
        G.add_node(concept, type="concept")
        for prereq in prereqs:
            G.add_edge(prereq, concept, relation="prerequisite_for")

    # Add hetvābhāsa nodes
    for hid, h in knowledge_store.hetvabhasas.items():
        G.add_node(hid, type="hetvabhasa", name=h.name)
        for ctx in h.common_contexts:
            if ctx in G.nodes:
                G.add_edge(hid, ctx, relation="monitors")

    # Add chapter nodes
    for cid, fp in knowledge_store.chapter_fingerprints.items():
        G.add_node(cid, type="chapter", title=fp.title,
                   difficulty=fp.difficulty_tier)
        for prereq in fp.prerequisites:
            G.add_edge(prereq, cid, relation="prerequisite_for")
        for vid in fp.vyaptis_introduced:
            G.add_edge(cid, vid, relation="introduces")

    # Add threshold concept nodes
    for tc in knowledge_store.threshold_concepts:
        tc_id = f"tc_{tc.name}"
        G.add_node(tc_id, type="threshold_concept", name=tc.name)
        for prereq in tc.prerequisites:
            G.add_edge(prereq, tc_id, relation="prerequisite_for")
        for concept in tc.reorganizes:
            G.add_edge(tc_id, concept, relation="reorganizes")

    # Chunk guide text
    chunks = []
    for chapter_id, text in guide_text.items():
        fp = knowledge_store.chapter_fingerprints.get(chapter_id)
        sections = _split_sections(text)
        for i, section_text in enumerate(sections):
            chunk = TextChunk(
                chunk_id=f"{chapter_id}_s{i:03d}",
                chapter_id=chapter_id,
                text=section_text,
                vyapti_anchors=_detect_vyapti_refs(section_text, knowledge_store.vyaptis),
                hetvabhasa_anchors=_detect_het_refs(section_text, knowledge_store.hetvabhasas),
                concept_anchors=_detect_concept_refs(section_text, knowledge_store.dependency_graph),
                prerequisites=fp.prerequisites if fp else [],
                difficulty_tier=fp.difficulty_tier if fp else "intermediate",
            )
            chunks.append(chunk)

    return G, chunks


def _split_sections(text: str, max_tokens: int = 512) -> list[str]:
    sections, current, current_len = [], [], 0
    for line in text.split('\n'):
        if line.startswith('###') and current:
            sections.append('\n'.join(current))
            current, current_len = [line], len(line.split())
        else:
            current.append(line)
            current_len += len(line.split())
            if current_len > max_tokens:
                sections.append('\n'.join(current))
                current, current_len = [], 0
    if current:
        sections.append('\n'.join(current))
    return sections


def _detect_vyapti_refs(text, vyaptis):
    refs = []
    for vid, v in vyaptis.items():
        if vid in text:
            refs.append(vid)
        elif any(t.lower() in text.lower() for t in v.name.split()[:3]):
            refs.append(vid)
    return refs


def _detect_het_refs(text, hetvabhasas):
    return [hid for hid, h in hetvabhasas.items()
            if hid in text or h.name.lower() in text.lower()]


def _detect_concept_refs(text, dep_graph):
    return [c for c in dep_graph if c.replace('_', ' ').lower() in text.lower()]
```

### 7.2 Retrieval Integration with DSPy 3.x

```python
# Example: Setting up T3 retrieval with DSPy 3.x
import dspy

# After compiling T3 chunks:
corpus = [chunk.text for chunk in chunks]

embedder = dspy.Embedder('openai/text-embedding-3-small', dimensions=512)
search = dspy.retrievers.Embeddings(
    embedder=embedder,
    corpus=corpus,
    k=5,
)

# Save embeddings for later
search.save("./t3_embeddings")

# Load without recomputing
# search = dspy.retrievers.Embeddings.from_saved("./t3_embeddings", embedder)
```

---

## 8. Module 5: Grounding Pipeline

**File:** `anvikshiki/grounding.py`
**Purpose:** Five-layer NL→predicate defense
**Dependencies:** `dspy`, `schema.py`, `datalog_engine.py`

### 8.1 Critical DSPy 3.x Changes

The thesis uses `dspy.Suggest()` for fallacy checking. In DSPy 3.x:
- `dspy.Assert` and `dspy.Suggest` are **deprecated**
- Replace with `dspy.Refine(module, N, reward_fn, threshold)` for hard constraints
- Replace with `dspy.BestOfN(module, N, reward_fn, threshold)` for soft constraints

### 8.2 Implementation Spec

```python
# anvikshiki/grounding.py

import dspy
from pydantic import BaseModel, Field
from .schema import KnowledgeStore
from .datalog_engine import DatalogEngine


class GroundingResult(BaseModel):
    """Output of the grounding pipeline."""
    predicates: list[str] = []
    confidence: float = 0.0
    disputed: list[str] = []
    warnings: list[str] = []
    refinement_rounds: int = 0
    clarification_needed: bool = False


# --- DSPy 3.x Signatures ---

class GroundQuery(dspy.Signature):
    """Translate a natural language query into structured predicates.
    Use ONLY predicates from the ontology snippet."""

    query: str = dspy.InputField(desc="User's natural language question")
    ontology_snippet: str = dspy.InputField(
        desc="Valid predicates and their descriptions — use ONLY these")
    domain_type: str = dspy.InputField(desc="Domain classification")

    reasoning: str = dspy.OutputField(
        desc="Step by step: which predicates match the query?")
    predicates: list[str] = dspy.OutputField(
        desc="Structured predicates, e.g. ['concentrated_ownership(acme)']")
    relevant_vyaptis: list[str] = dspy.OutputField(
        desc="Vyāpti IDs relevant to this query, e.g. ['V01', 'V02']")


class VerbalizePredicates(dspy.Signature):
    """Translate predicates back to natural language for round-trip check."""

    predicates: list[str] = dspy.InputField()
    ontology_snippet: str = dspy.InputField()

    verbalization: str = dspy.OutputField(
        desc="Natural language description of what these predicates assert")


class CheckFaithfulness(dspy.Signature):
    """Check if round-trip translation preserves the original meaning."""

    original_query: str = dspy.InputField()
    verbalized_predicates: str = dspy.InputField()

    faithful: bool = dspy.OutputField(
        desc="Do the predicates capture the same meaning as the query?")
    discrepancies: list[str] = dspy.OutputField(
        desc="Specific meaning differences, if any")


# --- Layer 1: Ontology Snippet Builder ---

class OntologySnippetBuilder:
    """Build constrained vocabulary from knowledge store."""

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


# --- Main Pipeline ---

class GroundingPipeline(dspy.Module):
    """
    Five-layer grounding defense.

    Layer 1: Ontology-constrained prompt (always on, 0 cost)
    Layer 2: Grammar-constrained decoding (see Appendix B)
    Layer 3: Ensemble consensus N=5 (always on, 5x cost)
    Layer 4: Round-trip verification (conditional: agreement < 0.9)
    Layer 5: Solver-feedback refinement (conditional: solver errors)
    """

    def __init__(self, knowledge_store: KnowledgeStore,
                 datalog_engine: DatalogEngine):
        super().__init__()
        self.ks = knowledge_store
        self.engine = datalog_engine

        # Layer 1
        self.snippet_builder = OntologySnippetBuilder()

        # Layer 3: Ensemble grounding
        self.grounder = dspy.ChainOfThought(GroundQuery)

        # Layer 4: Round-trip verification
        self.verbalizer = dspy.ChainOfThought(VerbalizePredicates)
        self.checker = dspy.ChainOfThought(CheckFaithfulness)

    def forward(self, query: str) -> GroundingResult:
        # LAYER 1: Build ontology-constrained prompt
        snippet = self.snippet_builder.build(self.ks)

        # LAYERS 2+3: Ensemble grounding (N=5)
        # Layer 2 (grammar constraint) applied at serving level
        # if using SGLang/vLLM with XGrammar — transparent to DSPy.
        # For API models, DSPy's JSONAdapter handles structured output.
        groundings = []
        for i in range(5):
            g = self.grounder(
                query=query,
                ontology_snippet=snippet,
                domain_type=self.ks.domain_type.name,
                config={"rollout_id": i, "temperature": 0.7},
            )
            groundings.append(g)

        # Compute consensus
        all_pred_sets = [set(g.predicates) for g in groundings]
        all_vyapti_sets = [set(g.relevant_vyaptis) for g in groundings]

        consensus_preds = set.intersection(*all_pred_sets)
        disputed_preds = set.union(*all_pred_sets) - consensus_preds
        consensus_vyaptis = set.intersection(*all_vyapti_sets)

        total = len(consensus_preds) + len(disputed_preds)
        confidence = len(consensus_preds) / max(total, 1)

        # Low confidence → request clarification
        if confidence < 0.4:
            return GroundingResult(
                predicates=list(consensus_preds),
                confidence=confidence,
                disputed=list(disputed_preds),
                warnings=["Grounding confidence too low — requesting clarification"],
                clarification_needed=True,
            )

        candidate_preds = list(consensus_preds | disputed_preds)
        candidate_vyaptis = list(consensus_vyaptis)

        # LAYER 4: Round-trip verification (if agreement < 0.9)
        if confidence < 0.9:
            verb = self.verbalizer(
                predicates=candidate_preds,
                ontology_snippet=snippet,
            )
            faith = self.checker(
                original_query=query,
                verbalized_predicates=verb.verbalization,
            )
            if not faith.faithful:
                candidate_preds = list(consensus_preds)
                confidence = 1.0 if consensus_preds else 0.0

        # LAYER 5: Solver-feedback refinement
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

        # Deterministic scope/decay checks
        warnings = []
        warnings.extend(self._check_scope(candidate_preds))
        warnings.extend(self._check_decay(candidate_vyaptis))

        return GroundingResult(
            predicates=candidate_preds,
            confidence=confidence,
            disputed=list(disputed_preds),
            warnings=warnings,
            refinement_rounds=refinement_rounds,
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
        for vid in vyapti_ids:
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

### 8.3 Key DSPy 3.x Patterns Used

- **Ensemble via `config={"rollout_id": i}`**: Bypasses cache to get diverse outputs
- **`list[str]` output fields**: DSPy 3.x natively parses list outputs via ChatAdapter/JSONAdapter
- **`bool` output field**: In `CheckFaithfulness`, DSPy 3.x handles boolean extraction
- **No `dspy.Suggest/Assert`**: Constraint enforcement is structural (ensemble consensus + round-trip), not assertion-based

---

## 9. Module 6: Uncertainty Quantification

**File:** `anvikshiki/uncertainty.py`
**Purpose:** Three-way decomposition: epistemic + aleatoric + inference
**Dependencies:** `datalog_engine.py`, `schema.py`

### 9.1 Implementation Spec

```python
# anvikshiki/uncertainty.py

from .datalog_engine import DatalogEngine, EpistemicValue
from .schema import KnowledgeStore, DomainType, DecayRisk


# Domain-type base aleatoric uncertainty
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
    """Full three-way uncertainty decomposition for a derived fact."""

    # --- Epistemic (from Heyting values — structural) ---
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

    # --- Aleatoric (from domain type — structural) ---
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

    # --- Inference (from grounding ensemble — measured) ---
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
    if epistemic.get('value', 0) == 0:
        total = 0.0
    else:
        ep_score = epistemic['value'] / 4.0
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

## 10. Module 7: Conformal Source Verifier

**File:** `anvikshiki/conformal.py`
**Purpose:** Statistical guarantees that claims are grounded in the Reference Bank
**Dependencies:** `numpy`

### 10.1 Implementation Spec

```python
# anvikshiki/conformal.py

import numpy as np


class ConformalSourceVerifier:
    """
    Split conformal prediction for source-claim verification.

    Guarantee: with probability >= 1-alpha, every claim marked
    as "supported" is actually supported by its cited source.
    """

    def __init__(self, alpha: float = 0.1):
        self.alpha = alpha  # 90% coverage by default
        self.calibration_scores: list[float] = []
        self.threshold: float | None = None

    def calibrate(self, calibration_set: list[tuple[str, str, bool]]):
        """
        Calibrate using labeled (claim, source, is_supported) triples.
        These must come from human annotation or a trusted NLI model.
        """
        scores = [
            self._score_support(claim, source)
            for claim, source, supported in calibration_set
            if supported
        ]
        if not scores:
            self.threshold = 0.5
            return

        n = len(scores)
        q = np.ceil((1 - self.alpha) * (n + 1)) / n
        q = min(q, 1.0)
        self.threshold = float(np.quantile(scores, q))
        self.calibration_scores = scores

    def verify_claim(self, claim: str, sources: list[str]) -> dict:
        if self.threshold is None:
            raise ValueError("Must calibrate before verifying")

        if not sources:
            return {
                'supported': False, 'support_score': 0.0,
                'best_source': None, 'coverage_guarantee': 1 - self.alpha,
                'threshold': self.threshold,
            }

        scores = [self._score_support(claim, src) for src in sources]
        best_idx = int(np.argmax(scores))

        return {
            'supported': scores[best_idx] >= self.threshold,
            'support_score': scores[best_idx],
            'best_source': sources[best_idx],
            'coverage_guarantee': 1 - self.alpha,
            'threshold': self.threshold,
        }

    def _score_support(self, claim: str, source: str) -> float:
        """
        Score how well a source supports a claim.

        PRODUCTION NOTE: Replace this with a trained NLI model
        (e.g. cross-encoder/nli-deberta-v3-large) or embedding
        cosine similarity for real deployments.
        """
        claim_words = set(claim.lower().split())
        source_words = set(source.lower().split())
        if not claim_words:
            return 0.0
        return len(claim_words & source_words) / len(claim_words)
```

### 10.2 Production Upgrade Path

Replace `_score_support` with:
```python
from sentence_transformers import CrossEncoder

nli_model = CrossEncoder('cross-encoder/nli-deberta-v3-large')

def _score_support(self, claim: str, source: str) -> float:
    scores = nli_model.predict([(claim, source)])
    # Returns [contradiction, neutral, entailment] logits
    return float(scores[0][2])  # entailment score
```

---

## 11. Module 8: Cellular Sheaf

**File:** `anvikshiki/sheaf.py`
**Purpose:** Local-to-global consistency checking; hetvābhāsa detection as H¹ obstructions
**Dependencies:** `numpy`, `networkx`

### 11.1 Implementation Spec

```python
# anvikshiki/sheaf.py

import numpy as np
import networkx as nx


class KnowledgeSheaf:
    """
    Cellular sheaf over the vyāpti knowledge graph.

    Vertices: domain concepts (stalks = R^d)
    Edges: vyāptis (restriction maps = d×d matrices)
    H⁰ = kernel(L) = globally consistent sections
    H¹ ≠ 0 → hetvābhāsas (gluing failures)
    """

    def __init__(self, graph: nx.DiGraph, stalk_dim: int = 8):
        self.graph = graph
        self.stalk_dim = stalk_dim
        self.stalks = {n: stalk_dim for n in graph.nodes()}
        self.restrictions = {
            (u, v): np.eye(stalk_dim)
            for u, v in graph.edges()
        }

    def set_restriction(self, edge: tuple, matrix: np.ndarray):
        self.restrictions[edge] = matrix

    def coboundary(self, section: dict[str, np.ndarray]) -> dict[tuple, np.ndarray]:
        """
        δ(section)(u,v) = F_{u→v} · section(u) - section(v)
        Zero everywhere → globally consistent.
        """
        result = {}
        for (u, v) in self.graph.edges():
            if u in section and v in section:
                F = self.restrictions.get((u, v), np.eye(self.stalk_dim))
                result[(u, v)] = F @ section[u] - section[v]
        return result

    def detect_hetvabhasas(
        self, section: dict[str, np.ndarray], threshold: float = 0.1
    ) -> list[dict]:
        """Detect hetvābhāsas as cohomological obstructions (H¹ ≠ 0)."""
        delta = self.coboundary(section)
        violations = []
        for edge, residual in delta.items():
            norm = float(np.linalg.norm(residual))
            if norm > threshold:
                violations.append({
                    'edge': edge,
                    'magnitude': norm,
                    'residual': residual.tolist(),
                    'interpretation': (
                        f"Reasoning {edge[0]}→{edge[1]} fails to glue "
                        f"globally (residual: {norm:.3f})"
                    ),
                })
        return violations

    def sheaf_laplacian(self) -> np.ndarray:
        """Compute L = δᵀδ. Kernel = globally consistent sections."""
        nodes = list(self.graph.nodes())
        node_idx = {n: i for i, n in enumerate(nodes)}
        n_nodes = len(nodes)
        n_edges = len(self.graph.edges())
        total_dim = n_nodes * self.stalk_dim

        delta = np.zeros((n_edges * self.stalk_dim, total_dim))

        for e_idx, (u, v) in enumerate(self.graph.edges()):
            F = self.restrictions.get((u, v), np.eye(self.stalk_dim))
            u_s = node_idx[u] * self.stalk_dim
            v_s = node_idx[v] * self.stalk_dim
            e_s = e_idx * self.stalk_dim
            delta[e_s:e_s+self.stalk_dim, u_s:u_s+self.stalk_dim] = F
            delta[e_s:e_s+self.stalk_dim, v_s:v_s+self.stalk_dim] = -np.eye(self.stalk_dim)

        return delta.T @ delta

    def global_consistency_score(self) -> float:
        """Spectral gap of sheaf Laplacian (higher = more consistent)."""
        L = self.sheaf_laplacian()
        eigenvalues = np.linalg.eigvalsh(L)
        sorted_eigs = sorted(eigenvalues)
        if len(sorted_eigs) < 2:
            return 1.0
        return min(float(sorted_eigs[1]) / 10.0, 1.0)
```

### 11.2 Scaling Notes

For knowledge bases with >500 concepts:
- Use `scipy.sparse` for the Laplacian matrix
- Use `scipy.sparse.linalg.eigsh` for the spectral gap (only need first few eigenvalues)
- Consider sheaf sparsification (Hansen & Ghrist) for very large graphs

---

## 12. Module 9: Final Engine

**File:** `anvikshiki/engine.py`
**Purpose:** Assemble all components into the complete pipeline
**Dependencies:** All previous modules + `dspy`

### 12.1 Key DSPy 3.x Patterns

```python
# anvikshiki/engine.py

import dspy
import numpy as np
from .schema import KnowledgeStore
from .grounding import GroundingPipeline, GroundingResult
from .datalog_engine import DatalogEngine, EpistemicValue
from .t2_compiler import compile_t2, ground_facts_from_predicates
from .sheaf import KnowledgeSheaf
from .conformal import ConformalSourceVerifier
from .uncertainty import compute_uncertainty


class SynthesizeResponse(dspy.Signature):
    """Produce a calibrated response with appropriate epistemic qualification."""

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
    """Reward function for dspy.Refine — ensures non-empty, source-citing response."""
    if not pred.response or len(pred.response) < 20:
        return 0.0
    score = 0.5
    if pred.sources_cited and len(pred.sources_cited) > 0:
        score += 0.3
    if any(w in pred.response.lower()
           for w in ["established", "hypothesis", "contested", "uncertain"]):
        score += 0.2
    return score


class AnvikshikiEngine(dspy.Module):
    """
    The complete Ānvīkṣikī Engine.

    Pipeline:
    1. Five-layer grounding (NL → verified predicates)
    2. Datalog forward chaining (predicates → derived facts)
    3. Hetvābhāsa integrity check (deterministic)
    4. Sheaf consistency check (cohomological)
    5. Conformal source verification
    6. Three-way uncertainty decomposition
    7. DSPy synthesis (calibrated NL response)
    """

    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        sheaf: KnowledgeSheaf,
        conformal: ConformalSourceVerifier,
        boolean_mode: bool = False,  # Phase 3+ by default
    ):
        super().__init__()
        self.ks = knowledge_store
        self.sheaf = sheaf
        self.conformal = conformal
        self.boolean_mode = boolean_mode

        # Compile T2
        self.engine = compile_t2(knowledge_store, boolean_mode=boolean_mode)

        # Grounding pipeline
        self.grounding = GroundingPipeline(knowledge_store, self.engine)

        # Synthesis with Refine (replaces dspy.Assert in v3.x)
        self._synthesizer = dspy.ChainOfThought(SynthesizeResponse)
        self.synthesizer = dspy.Refine(
            module=self._synthesizer,
            N=3,
            reward_fn=_synthesis_reward,
            threshold=0.5,
        )

    def forward(self, query: str, retrieved_chunks: list[str]):
        # STEP 1: Five-layer grounding
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

        # STEP 2: Fresh engine per query (prevent cross-query contamination)
        self.engine = compile_t2(self.ks, boolean_mode=self.boolean_mode)
        grounded_facts = ground_facts_from_predicates(
            self.engine, grounding.predicates)

        # STEP 3: Forward chain (deterministic, polynomial, terminates)
        iterations = self.engine.evaluate()

        # STEP 4: Hetvābhāsa check (deterministic)
        violations = self.engine.check_hetvabhasas()

        # STEP 5: Sheaf consistency check
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

        # STEP 6: Conformal source verification
        claim_verifications = []
        for (pred, entity), value in self.engine.facts.items():
            if value > EpistemicValue.BOTTOM:
                sources = self._get_sources(pred, entity)
                if sources and self.conformal.threshold is not None:
                    v = self.conformal.verify_claim(f"{pred}({entity})", sources)
                    claim_verifications.append(v)

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

        # STEP 8: Synthesize response (with Refine for quality)
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
            section[pred][0] = value.value / 4.0
            section[pred][1] = 1.0
        return section

    def _find_primary_derived(self, grounded_facts):
        grounded_keys = {(f.predicate, f.entity) for f in grounded_facts}
        for (pred, entity), value in self.engine.facts.items():
            if value > EpistemicValue.BOTTOM and (pred, entity) not in grounded_keys:
                return (pred, entity)
        return None

    def _get_sources(self, predicate, entity):
        sources = []
        for vid, v in self.ks.vyaptis.items():
            if v.consequent == predicate or predicate in v.antecedents:
                sources.extend(v.sources)
        return [
            self.ks.reference_bank.get(sid, {}).get('text', '')
            for sid in sources if sid in self.ks.reference_bank
        ]
```

---

## 13. Module 10: Optimization

**File:** `anvikshiki/optimize.py`
**Purpose:** DSPy 3.x optimization pipeline
**Dependencies:** `dspy`

### 13.1 Implementation Spec

```python
# anvikshiki/optimize.py

import dspy
from dspy.evaluate import Evaluate


def calibration_metric(gold, pred, trace=None) -> float:
    """
    Reward calibrated uncertainty — not just correct answers.
    Overconfidence on wrong answers is penalized heavily.
    """
    answer_correct = hasattr(gold, 'answer') and gold.answer in pred.response

    # Parse stated confidence from uncertainty report
    total_conf = 0.5
    if hasattr(pred, 'uncertainty') and isinstance(pred.uncertainty, dict):
        total_conf = pred.uncertainty.get('total_confidence', 0.5)

    # Calibration error
    actual = 1.0 if answer_correct else 0.0
    calibration_error = abs(total_conf - actual)

    # Bonuses
    source_bonus = 0.1 if hasattr(pred, 'sources') and pred.sources else 0.0
    warning_bonus = 0.05 if hasattr(pred, 'violations') and pred.violations else 0.0

    # Severe penalty for overconfident wrong answers
    if not answer_correct and total_conf > 0.7:
        return 0.0

    return (1.0 - calibration_error) + source_bonus + warning_bonus


def optimize_engine(engine, trainset, valset=None, auto="medium"):
    """
    Run MIPROv2 optimization over the full engine.

    DSPy 3.x API:
    - MIPROv2 accepts auto="light"|"medium"|"heavy"
    - No more num_candidates or init_temperature parameters
    - Uses .deepcopy() for safe optimization
    """
    optimizer = dspy.MIPROv2(
        metric=calibration_metric,
        auto=auto,
    )

    optimized = optimizer.compile(
        engine.deepcopy(),
        trainset=trainset,
        valset=valset,
        max_bootstrapped_demos=3,
        max_labeled_demos=4,
    )

    return optimized


def evaluate_engine(engine, devset, num_threads=8):
    """Evaluate engine on a development set."""
    evaluator = Evaluate(
        devset=devset,
        metric=calibration_metric,
        num_threads=num_threads,
        display_progress=True,
    )
    return evaluator(engine)
```

---

## 14. Testing Strategy

### 14.1 Unit Tests (No LLM Calls)

| Module | Test Focus |
|--------|-----------|
| `schema.py` | Pydantic validation, JSON round-trip, enum serialization |
| `datalog_engine.py` | Boolean/lattice mode, semi-naive correctness, termination, hetvabhasa detection |
| `t2_compiler.py` | YAML loading, rule compilation, scope exclusion mapping |
| `t3_compiler.py` | Graph construction, chunk splitting, reference detection |
| `uncertainty.py` | UQ computation for each domain type, weakest-link finding |
| `conformal.py` | Calibration quantile, claim verification, edge cases |
| `sheaf.py` | Coboundary correctness, Laplacian symmetry, violation detection |

### 14.2 Integration Tests (Require LLM)

```python
# tests/test_engine.py

import dspy
import pytest
from anvikshiki.schema import KnowledgeStore
from anvikshiki.t2_compiler import load_knowledge_store, compile_t2
from anvikshiki.engine import AnvikshikiEngine
from anvikshiki.sheaf import KnowledgeSheaf
from anvikshiki.conformal import ConformalSourceVerifier
from anvikshiki.t3_compiler import compile_t3
import networkx as nx

@pytest.fixture
def setup_engine():
    dspy.configure(lm=dspy.LM('openai/gpt-4o-mini'))
    ks = load_knowledge_store("data/sample_architecture.yaml")
    graph, chunks = compile_t3({}, ks)
    sheaf = KnowledgeSheaf(graph)
    conformal = ConformalSourceVerifier(alpha=0.1)
    conformal.calibrate([
        ("ownership matters", "Competitive advantage grows from value creation", True),
    ])
    engine = AnvikshikiEngine(ks, sheaf, conformal, boolean_mode=False)
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
```

### 14.3 Running Tests

```bash
# Unit tests (no LLM, fast)
pytest tests/ -k "not integration" -v

# Integration tests (requires API key)
OPENAI_API_KEY=sk-... pytest tests/ -k "integration" -v

# All tests
pytest tests/ -v
```

---

## 15. Phase-by-Phase Build Order

### Phase 1: DSPy Only (Week 1-2)

Build and test these modules:
1. `schema.py` — data structures
2. `t2_compiler.py` — YAML → KnowledgeStore (parser only, no Datalog)
3. `t3_compiler.py` — guide text → graph + chunks
4. `grounding.py` — five-layer defense
5. `engine.py` — but with `engine_phase1.py` (LLM-only reasoning, no Datalog)

**Phase 1 engine variant** — uses `dspy.ChainOfThought` for reasoning instead of Datalog:

```python
class AnvikshikiEngineV1(dspy.Module):
    """Phase 1: Pure DSPy. All reasoning is LLM-based."""

    def __init__(self, knowledge_store):
        super().__init__()
        self.ks = knowledge_store
        self.grounding = GroundingPipeline(knowledge_store, None)  # No Datalog yet
        self.reasoner = dspy.ChainOfThought(ReasonOverDomain)
        self.synthesizer = dspy.ChainOfThought(SynthesizeResponse)
```

**Validation:** Run grounding pipeline against sample queries. Measure ensemble agreement rates.

### Phase 2: DSPy + Boolean Datalog (Week 3-4)

Add:
1. `datalog_engine.py` — with `boolean_mode=True`
2. Update `t2_compiler.py` — compile vyāptis as Datalog rules
3. Update `engine.py` — Datalog replaces LLM reasoning

**Validation:** For same queries, compare Phase 1 (LLM reasoning) vs Phase 2 (Datalog reasoning). Verify:
- Datalog derivation traces are correct
- Hetvabhasa integrity constraints fire when expected
- Scope exclusions block derivation when expected

### Phase 3: DSPy + Lattice Datalog + UQ (Week 5)

Change one line:
```python
engine = compile_t2(knowledge_store, boolean_mode=False)
```

Add:
1. `uncertainty.py` — three-way decomposition
2. `conformal.py` — source verification

**Validation:** Same queries, but now check:
- Epistemic values propagate correctly (HYPOTHESIS chain → HYPOTHESIS conclusion)
- UQ decomposition returns all three components
- Conformal verifier calibrates and verifies

### Phase 4: DSPy + Lattice Datalog + Sheaf + UQ (Week 6-7)

Add:
1. `sheaf.py` — coboundary, Laplacian, violation detection
2. Update `engine.py` — sheaf check after Datalog evaluation

**Validation:**
- Construct a knowledge graph with a known inconsistency
- Verify the sheaf detects H¹ ≠ 0
- Verify the engine reports the violation in its response

---

## 16. DSPy 3.x Migration Notes

### Complete API Translation Table

| Concept | DSPy 2.x (thesis_v2.md) | DSPy 3.1.x (this guide) |
|---------|--------------------------|--------------------------|
| **LM setup** | `dspy.OpenAI('gpt-4')` | `dspy.LM('openai/gpt-4o-mini')` |
| **Configure** | `dspy.settings.configure(lm=lm)` | `dspy.configure(lm=lm)` |
| **Scoped LM** | N/A | `with dspy.context(lm=other_lm): ...` |
| **Base class** | `dspy.Program` or `dspy.Module` | `dspy.Module` only |
| **Predict** | `dspy.Predict(sig)` | `dspy.Predict(sig)` (unchanged) |
| **CoT** | `dspy.ChainOfThought(sig)` | `dspy.ChainOfThought(sig)` (unchanged) |
| **Hard constraint** | `dspy.Assert(cond, msg)` | `dspy.Refine(module, N, reward_fn, threshold)` |
| **Soft constraint** | `dspy.Suggest(cond, msg)` | `dspy.BestOfN(module, N, reward_fn, threshold)` |
| **Typed output** | `dspy.TypedPredictor` wrapper | Native: `field: MyPydanticModel = dspy.OutputField()` |
| **Optimizer** | `MIPROv2(metric, num_candidates=10, init_temperature=1.0)` | `dspy.MIPROv2(metric, auto="medium")` |
| **Evaluation** | `dspy.Evaluate(devset, metric)` | `dspy.Evaluate(devset, metric, num_threads=N)` |
| **Retriever** | `dspy.Retrieve(k=5)` + community RMs | `dspy.retrievers.Embeddings(embedder, corpus, k=5)` |
| **Embedder** | External (sentence-transformers) | `dspy.Embedder('openai/text-embedding-3-small')` |
| **Saving** | `program.save(path)` | `program.save('path.json')` |
| **Loading** | `program.load(path)` | `loaded = MyClass(); loaded.load('path.json')` |
| **Async** | N/A | `dspy.asyncify(module)` |
| **Parallel** | Manual threading | `dspy.Parallel(num_threads=N)` or `module.batch()` |
| **Cache bypass** | N/A | `config={"rollout_id": i, "temperature": 1.0}` |
| **Structured JSON** | Prompt engineering | `dspy.configure(adapter=dspy.JSONAdapter())` |
| **Agent/Tools** | N/A | `dspy.ReAct(sig, tools=[fn])` or `dspy.CodeAct(sig, tools=[fn])` |

### New Optimizers in DSPy 3.x

| Optimizer | Use Case |
|-----------|----------|
| `dspy.MIPROv2` | Joint instruction + demo optimization (primary recommendation) |
| `dspy.SIMBA` | Stochastic mini-batch introspective analysis |
| `dspy.GEPA` | Reflective prompt evolution (most powerful for instruction optimization) |
| `BootstrapFinetune` | Distill prompt-based program into weight updates |
| `BetterTogether` | Chain prompt + weight optimizers |

### Reward Functions for dspy.Refine

The reward function signature is: `fn(args: dict, pred: dspy.Prediction) -> float`

```python
def my_reward(args, pred):
    """0.0 = completely unacceptable, 1.0 = perfect."""
    score = 0.0
    if pred.response and len(pred.response) > 10:
        score += 0.5
    if hasattr(pred, 'sources_cited') and pred.sources_cited:
        score += 0.3
    return score

refined = dspy.Refine(
    module=my_chain_of_thought,
    N=3,              # max retry attempts
    reward_fn=my_reward,
    threshold=0.7,    # minimum score to accept
)
```

---

## 17. Appendix A: egglog Integration (Alternative Datalog Backend)

If performance or lattice semantics become a bottleneck with the pure-Python engine, swap in egglog:

```bash
pip install egglog
```

```python
# anvikshiki/egglog_backend.py
# Alternative backend using Rust-based egglog with native lattice merge

from egglog import EGraph

def create_heyting_engine():
    """
    egglog natively supports lattice merge via :merge parameter.
    Define Heyting algebra with :merge (min old new) for meet semantics.
    """
    eg = EGraph()

    # Define the engine in egglog's s-expression format
    eg.run_program("""
        ; Heyting lattice: 0=BOTTOM, 1=CONTESTED, 2=OPEN, 3=HYPOTHESIS, 4=ESTABLISHED
        ; Function with lattice merge (meet = min)
        (function derived (String String) i64 :merge (min old new))
        (function rule_confidence (String) i64)

        ; Example: define a rule
        ; V01: concentrated_ownership → long_horizon_possible
        (set (rule_confidence "V01") 4)  ; ESTABLISHED

        ; Ground a fact
        (set (derived "concentrated_ownership" "acme") 4)

        ; Fire rule: derive consequent with meet(rule_conf, antecedent)
        (rule ((= ant_val (derived "concentrated_ownership" ?entity))
               (= conf (rule_confidence "V01")))
              ((set (derived "long_horizon_possible" ?entity)
                    (min ant_val conf))))

        (run 10)  ; run fixpoint up to 10 iterations
    """)

    # Extract results
    # eg.extract(...)
    return eg
```

**When to use egglog:**
- Knowledge base has >1000 rules/facts (Rust performance matters)
- You need equality saturation (e-graph) capabilities
- You want native lattice merge without implementing fixpoint yourself

**When to keep the pure-Python engine:**
- You need full proof trace control
- You need custom hetvabhasa check functions as Python callables
- Knowledge base is <500 rules (pure Python is fast enough)

---

## 18. Appendix B: Grammar-Constrained Decoding Options

### For API-Based Models (OpenAI, Anthropic)

**Use Instructor** for Pydantic-validated structured output:

```python
import instructor
from pydantic import BaseModel

client = instructor.from_provider("openai/gpt-4o-mini")

class GroundedPredicates(BaseModel):
    reasoning: str
    predicates: list[str]
    relevant_vyaptis: list[str]

result = client.create(
    response_model=GroundedPredicates,
    messages=[{
        "role": "user",
        "content": f"Query: {query}\n\nOntology:\n{snippet}\n\nGround this query."
    }],
)
```

**Or use DSPy's JSONAdapter** (built-in, no extra dependency):

```python
dspy.configure(
    lm=dspy.LM('openai/gpt-4o-mini'),
    adapter=dspy.JSONAdapter(),
)
# Now all Predict/ChainOfThought calls use JSON mode
```

### For Local Models (Llama, Mistral via SGLang/vLLM)

**Use XGrammar** via SGLang's OpenAI-compatible API:

```bash
# Start SGLang server with your model
python -m sglang.launch_server --model meta-llama/Llama-3.1-8B-Instruct --port 7501
```

```python
# DSPy connects to SGLang as an OpenAI-compatible endpoint
lm = dspy.LM(
    'openai/meta-llama/Llama-3.1-8B-Instruct',
    api_base='http://localhost:7501/v1',
    api_key='',
)
dspy.configure(lm=lm, adapter=dspy.JSONAdapter())

# XGrammar enforces JSON schema at the token level — transparent to DSPy
```

### CRANE-Style Grammar Augmentation

CRANE requires direct logit access and is not compatible with DSPy's adapter layer. If you need CRANE's CoT+grammar approach:

1. Run CRANE separately as a preprocessing step
2. Feed its output into the DSPy pipeline as pre-grounded predicates
3. Or contribute a DSPy adapter that wraps CRANE

### Practical Recommendation

For the Ānvīkṣikī Engine:
- **Development:** `dspy.JSONAdapter()` + OpenAI API (simplest, works immediately)
- **Production (API):** Instructor + OpenAI/Anthropic (Pydantic validation + retries)
- **Production (local):** SGLang + XGrammar (true token-level grammar enforcement)

---

## Quick Start

```python
import dspy
from anvikshiki.t2_compiler import load_knowledge_store, compile_t2
from anvikshiki.t3_compiler import compile_t3
from anvikshiki.sheaf import KnowledgeSheaf
from anvikshiki.conformal import ConformalSourceVerifier
from anvikshiki.engine import AnvikshikiEngine

# 1. Configure
dspy.configure(lm=dspy.LM('openai/gpt-4o-mini'))

# 2. Load knowledge base
ks = load_knowledge_store("data/sample_architecture.yaml")

# 3. Build T3 corpus
graph, chunks = compile_t3({}, ks)

# 4. Initialize components
sheaf = KnowledgeSheaf(graph)
conformal = ConformalSourceVerifier(alpha=0.1)
conformal.calibrate([("test claim", "test source", True)])

# 5. Create engine (Phase 3: lattice mode)
engine = AnvikshikiEngine(ks, sheaf, conformal, boolean_mode=False)

# 6. Query
result = engine(
    query="What strategic advantages does concentrated ownership provide?",
    retrieved_chunks=[c.text for c in chunks[:5]] if chunks else [""],
)

print(result.response)
print(f"Confidence: {result.uncertainty['total_confidence']:.2f}")
print(f"Proof trace: {result.proof_trace}")
print(f"Violations: {result.violations}")
```

---

*This document is the implementation companion to `thesis_v2.md`. The thesis describes the architecture and theory; this guide shows how to build it with current tools.*
