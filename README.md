# Anvikshiki Ecosystem

**A neurosymbolic reasoning engine that combines ASPIC+ argumentation, lattice Datalog, and five-layer LLM grounding to answer domain questions with calibrated uncertainty and provenance tracking.**

The name comes from *Ānvīkṣikī* (Sanskrit: आन्वीक्षिकी) — the ancient Indian science of critical inquiry and logical analysis.

---

## What This Is

Most LLM-based Q&A systems hallucinate confidently. Anvikshiki takes a different approach:

1. **Domain knowledge is encoded as formal rules** (vyāptis) in Datalog — not just embeddings
2. **Arguments are constructed and attacked** using ASPIC+ argumentation semantics
3. **The LLM is constrained** by a five-layer grounding defense that forces it to use KB vocabulary
4. **Uncertainty is decomposed** into epistemic, aleatoric, and inference components
5. **The system says "I don't know"** when the KB doesn't cover a query

This produces answers with provenance chains, epistemic status labels, and calibrated confidence — not just text.

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│  Query Refinement (1 LLM call)      │  ← Clarify intent, check KB coverage
│  PROCEED / PARTIAL / DECLINE        │    Honest "I don't know" when needed
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Five-Layer Grounding               │  ← Ontology-constrained prompt
│  (LLM → KB predicates + confidence) │    Grammar-constrained decoding
└──────────────┬──────────────────────┘    Ensemble N=5, round-trip verify
               │
┌──────────────▼──────────────────────┐
│  T2 Compiler (0 LLM calls)         │  ← Compile KB + facts → ASPIC+ framework
│  Datalog forward chaining           │    Generate arguments + attacks
│  Semi-naive evaluation              │    Rebutting, undercutting, undermining
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Argumentation Semantics            │  ← Compute grounded extension
│  Labelling: IN / OUT / UNDEC        │    Epistemic status per conclusion
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Contestation Protocols             │  ← Vāda (cooperative inquiry)
│  Uncertainty Decomposition          │    Jalpa (adversarial stress test)
│  Provenance Tracking                │    Vitaṇḍā (vulnerability audit)
└──────────────┬──────────────────────┘
               │
               ▼
        Calibrated Response
        + Sources + Uncertainty
        + Provenance + Violations
```

## Quick Start

```bash
# Clone and install
git clone https://github.com/YOUR_USERNAME/anvikshiki_ecosystem.git
cd anvikshiki_ecosystem
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run all tests (no LLM needed — 249 pass)
pytest
```

### Level 1: Pure Symbolic (no LLM needed)

```python
from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store
from anvikshiki_v4.uncertainty import compute_uncertainty_v4

# Load the business strategy knowledge base
ks = load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")

# Query: "Does a company with positive unit economics create value?"
query_facts = [
    {"predicate": "positive_unit_economics", "confidence": 0.9, "sources": ["user_input"]},
]

# Compile → argumentation framework
af = compile_t2(ks, query_facts)

# Compute grounded extension (which arguments survive?)
labels = af.compute_grounded()

# See accepted conclusions with epistemic status
for conc in ["value_creation", "long_term_value"]:
    status, tag, args = af.get_epistemic_status(conc)
    if status:
        print(f"{conc}: {status.value}")
        print(f"  belief={tag.belief:.2f}, uncertainty={tag.uncertainty:.2f}")
        print(f"  sources={sorted(tag.source_ids)}")
```

### Level 2: With Contestation (still no LLM)

```python
from anvikshiki_v4.contestation import ContestationManager

cm = ContestationManager()

# Cooperative inquiry — what do we know?
vada = cm.vada(af)
print(f"Accepted: {list(vada.accepted.keys())}")
print(f"Open questions: {vada.open_questions}")

# Adversarial stress test — what could be challenged?
jalpa = cm.jalpa(af, timeout_seconds=10.0)
print(f"Defensible: {jalpa.defensible_positions}")

# Vulnerability audit — where are the weaknesses?
vitanda = cm.vitanda(af, timeout_seconds=10.0)
print(f"Vulnerabilities: {list(vitanda.vulnerability_inventory.keys())}")
```

### Level 3: Full Engine (requires LLM via DSPy)

```python
import dspy
from anvikshiki_v4.grounding import GroundingPipeline
from anvikshiki_v4.engine_v4 import AnvikshikiEngineV4
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

dspy.configure(lm=dspy.LM("openai/gpt-4o"))  # or anthropic/claude-sonnet-4-6, gemini/gemini-2.0-flash

ks = load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")
grounding = GroundingPipeline(knowledge_store=ks)
engine = AnvikshikiEngineV4(
    knowledge_store=ks,
    grounding_pipeline=grounding,
)

result = engine(
    query="Does a company with strong LTV-CAC ratio and positive contribution margin have viable unit economics?",
    retrieved_chunks=["Ries (2011) showed that..."],
)

print(result.response)              # Calibrated natural language answer
print(result.grounding_confidence)  # 0.0–1.0
print(result.uncertainty)           # {predicate: {epistemic, aleatoric, inference}}
print(result.provenance)            # {predicate: {pramana, sources, depth}}
print(result.violations)            # Defeated arguments (fallacies caught)
```

### Query Refinement (Pre-pipeline Coverage Check)

```python
from anvikshiki_v4.query_refinement import QueryRefinementPipeline
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

ks = load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")
pipeline = QueryRefinementPipeline(ks)

# This checks if the KB can answer the query BEFORE running the engine
result = pipeline.refine("What's the best marketing channel for B2B SaaS?")

print(result.can_proceed)      # False — KB doesn't cover marketing channels
print(result.decline_message)  # "I don't have relevant info about marketing_channel..."
print(result.coverage.coverage_ratio)       # 0.0
print(result.coverage.closest_predicates)   # {"marketing_channel": "distorted_market_signal"}
```

## Repository Structure

```
anvikshiki_ecosystem/
├── anvikshiki_v4/                # Core engine package
│   ├── schema.py                 # KnowledgeStore, Vyapti, ChapterFingerprint
│   ├── schema_v4.py              # ProvenanceTag semiring (belief ⊗ uncertainty)
│   ├── datalog_engine.py         # Forward-chaining Datalog with semi-naive eval
│   ├── t2_compiler_v4.py         # KB → ASPIC+ argumentation framework
│   ├── argumentation.py          # ArgumentationFramework, grounded semantics
│   ├── uncertainty.py            # Epistemic/aleatoric/inference decomposition
│   ├── grounding.py              # Five-layer LLM grounding defense
│   ├── engine_v4.py              # Full pipeline orchestrator (Stages 0–11)
│   ├── contestation.py           # Vāda / Jalpa / Vitaṇḍā protocols
│   ├── query_refinement.py       # Pre-pipeline coverage check & intent clarification
│   ├── predicate_extraction.py   # Automated predicate extraction from prose
│   ├── extraction_schema.py      # Extraction pipeline data models
│   ├── extraction_eval.py        # Precision/recall evaluation for extraction
│   ├── extraction_hitl.py        # Human-in-the-loop review for extracted predicates
│   ├── t3_compiler.py            # T3 GraphRAG compiler
│   ├── optimize.py               # DSPy optimizer configurations
│   ├── data/
│   │   ├── business_expert.yaml  # Business strategy KB (11 vyāptis, 8 hetvābhāsas)
│   │   ├── sample_architecture.yaml
│   │   ├── business_expert_trace.md
│   │   └── practical_useage.md   # Usage examples (Levels 1–3)
│   └── tests/                    # 249 tests, 0 LLM calls needed
│       ├── test_engine_v4.py
│       ├── test_t2_compiler_v4.py
│       ├── test_argumentation.py
│       ├── test_contestation.py
│       ├── test_uncertainty.py
│       ├── test_schema_v4.py
│       ├── test_business_expert.py
│       ├── test_predicate_extraction.py
│       ├── test_query_refinement.py
│       └── fixtures/
│           ├── guide_ch2_excerpt.md
│           └── expected_predicates.yaml
│
├── guides/
│   └── business_expert/          # Complete 12-chapter business strategy guide
│       ├── guide_opening_ch1.md  # Ch 1: Financial Statements as Language
│       ├── guide_ch2.md          # Ch 2: Unit Economics
│       ├── guide_ch3_ch4.md      # Ch 3-4: Constraints & Capital Allocation
│       ├── guide_ch5_ch6.md      # Ch 5-6: Competitive Position & Business Models
│       ├── guide_ch7_ch8.md      # Ch 7-8: Organizational Design & Incentives
│       ├── guide_ch9_ch10.md     # Ch 9-10: Markets & Executive Judgment
│       ├── guide_ch11_ch12.md    # Ch 11-12: Frontier & Expert Framework
│       ├── stage1.md             # Stage 1: Domain & Reader Calibration
│       ├── stage2_part1_vyaptis.md       # Vyāpti extraction
│       ├── stage2_part2_hetvabhasas.md   # Hetvābhāsa identification
│       ├── stage2_part3_architecture.md  # Knowledge architecture
│       ├── stage2_part4_registries.md    # Metadata registries
│       └── stage3_reference_bank.md      # Source verification
│
├── docs/
│   ├── eli5_trace.md                     # ELI5 engine walkthrough
│   ├── eli5_trace_e2e.md                 # End-to-end trace with augmented KB
│   ├── pipeline_flowchart_llama3.2.md    # Full pipeline flowchart
│   ├── predicate_extraction_design.md    # Extraction module design doc
│   └── predicate_extraction_theory.md    # Pragmatics-based extraction theory
│
├── theory/
│   ├── thesis2_v1.md             # Current thesis: ASPIC+ over provenance semirings
│   ├── BUILD_GUIDE.md            # Implementation manual (DSPy 3.1.x)
│   ├── ecosystem_evolution.md    # Full project evolution log (meta-prompt → engine)
│   └── history/                  # All historical versions
│       ├── thesis/               # thesis_v1 → v2 → v2_patch → v3
│       ├── build_guides/         # BUILD_GUIDE_v2 → v3 → v4
│       ├── meta_prompts/         # meta_prompt_v3.2 → v3.25 → v3.26 + meta^2
│       └── discussions/          # Architecture decision discussions
│
├── pyproject.toml
├── .gitignore
└── README.md
```

## Key Concepts

### Knowledge Base (YAML)

Domain knowledge is encoded as **vyāptis** (invariant relationships) in YAML:

```yaml
vyaptis:
  V01:
    name: "The Value Equation"
    statement: "If unit economics are positive, the business creates value"
    antecedents: [positive_unit_economics]
    consequent: value_creation
    causal_status: empirical
    scope_exclusions: [negative_unit_economics]   # Generates undercutting attacks
    epistemic_status: established
    confidence:
      existence: 0.95
      formulation: 0.9
```

### Argumentation

The engine doesn't just derive conclusions — it builds an **argumentation framework** where:
- **Rebutting attacks**: V01 ("positive economics → value") vs V11 ("growth + overhead → NOT value")
- **Undercutting attacks**: Scope exclusions disable rules when conditions aren't met
- **Undermining attacks**: Stale or low-confidence rules can be challenged
- **Grounded semantics**: Only conclusions that survive all attacks are accepted (IN)

### Uncertainty Decomposition

Every conclusion gets three uncertainty components:
- **Epistemic**: What don't we know? (based on evidence quality, source count)
- **Aleatoric**: What's inherently variable? (based on domain type, causal status)
- **Inference**: How much uncertainty from the reasoning chain? (depth, rule confidence)

### Provenance

Every accepted conclusion has a full provenance chain: which pramāṇa (source of knowledge) was used, which sources support it, and how deep the derivation goes.

### Contestation Protocols

Three modes inspired by Nyāya debate tradition:
- **Vāda** (cooperative): What do we know? What's open?
- **Jalpa** (adversarial): What positions are defensible under challenge?
- **Vitaṇḍā** (destructive): Where are the vulnerabilities?

## Tests

```bash
# Run all 249 tests (no LLM API key needed)
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest anvikshiki_v4/tests/test_business_expert.py -v

# Skip integration tests that need LLM
pytest -m "not integration"
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `dspy>=3.1.0` | LLM orchestration & grounding signatures |
| `networkx>=3.2` | Argumentation graph structure |
| `numpy>=1.26` | Provenance tag semiring operations |
| `scipy>=1.12` | Uncertainty quantification |
| `pydantic>=2.6` | Schema validation |
| `pyyaml>=6.0` | Knowledge base serialization |

## License

MIT
