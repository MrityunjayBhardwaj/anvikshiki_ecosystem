# Build Prompt: Ānvīkṣikī Engine v4

Paste this into a fresh Claude Code session from `/Users/mrityunjaybhardwaj/Documents/Anvikshiki/`.

---

## Prompt

Build the Ānvīkṣikī Engine **v4** — a neurosymbolic argumentation engine using ASPIC+ over provenance semirings. This replaces the existing v3 engine (Heyting lattice + sheaf) with a unified architecture where epistemic status *emerges* from argumentation semantics rather than being hand-assigned.

### What Already Exists

There is a **working v3 implementation** at `anvikshiki/` (2,605 LOC, 15 modules, 9 test files). The v4 system reuses some of these modules unchanged and replaces others.

**Reuse unchanged:**
- `anvikshiki/schema.py` — KnowledgeStore, Vyapti, Hetvabhasa Pydantic models (input format)
- `anvikshiki/grounding.py` — five-layer NL→predicate defense
- `anvikshiki/t3_compiler.py` — GraphRAG corpus builder
- `anvikshiki/datalog_engine.py` — semi-naive evaluator (Phase 2 substrate only)
- `anvikshiki/data/sample_architecture.yaml` — sample KB

**Replace / remove (absorbed into argumentation):**
- `anvikshiki/sheaf.py` → eliminated (rationality postulates replace consistency checking)
- `anvikshiki/conformal.py` → eliminated (ProvenanceTag.source_ids replaces source verification)
- `anvikshiki/uncertainty.py` → rewrite (derive from ProvenanceTag fields, not hand-tuned dict)
- `anvikshiki/t2_compiler.py` → rewrite as `t2_compiler_v4.py` (vyāptis → ArgumentationFramework)
- `anvikshiki/engine.py` → rewrite as `engine_v4.py` (8-step argumentation pipeline)
- `anvikshiki/optimize.py` → update (argumentation-aware calibration metric)

**Create new:**
- `schema_v4.py` — ProvenanceTag (semiring), PramanaType, Argument, Attack, Label
- `argumentation.py` — ArgumentationFramework, compute_grounded/preferred/stable, _defeats
- `contestation.py` — vāda/jalpa/vitaṇḍā debate protocols
- `t2_compiler_v4.py` — KB + facts → AF with arguments, attacks, provenance tags

### Architecture Documents

Read these two files as the complete spec:

1. **`anvikshiki_engine/thesis2_v1.md`** — The architectural thesis. Key sections:
   - Section 7 (line ~692): The unified architecture, Nyāya-to-ASPIC+ mapping
   - Section 9.5 (line ~1011): Core data structures (ProvenanceTag, Argument, Attack)
   - Section 9.6 (line ~1164): Argumentation engine (AF, compute_grounded, _defeats)
   - Section 9.7 (line ~1339): T2 compiler (compile_t2, _build_rule_tag)
   - Section 9.8 (line ~1572): Complete engine pipeline (AnvikshikiEngineV4)

2. **`anvikshiki_engine/BUILD_GUIDE_V2.md`** — The implementation manual. Contains:
   - Complete Python code for every module (with gap-fills for thesis sketches)
   - All test specifications with runnable pytest code
   - Phase-by-phase build order with validation gates
   - Sample YAML with conflicts and scope exclusions

### Environment

- macOS (Darwin 24.4.0)
- Python 3.12 in `.venv/` (activate with `source .venv/bin/activate`)
- Already installed: `dspy>=3.1.0`, `networkx`, `pydantic>=2.6`, `pyyaml`, `numpy`, `scipy`, `pytest`
- No git repo initialized yet

### Build Instructions

Create the v4 package as `anvikshiki_v4/` alongside the existing `anvikshiki/` (do NOT modify v3 code). Follow the BUILD_GUIDE_V2.md exactly.

**Phase 1: Foundation (do this first)**

1. Create `anvikshiki_v4/` package directory with `__init__.py`
2. Copy unchanged modules from `anvikshiki/`: `schema.py`, `grounding.py`, `t3_compiler.py`, `datalog_engine.py`
3. Copy `anvikshiki/data/` directory
4. Implement `schema_v4.py` from BUILD_GUIDE_V2.md Section 4.2 — ProvenanceTag with ⊗/⊕ operations, __post_init__ validation, to_dict/from_dict, all enums
5. Implement `argumentation.py` from BUILD_GUIDE_V2.md Section 7.3 — ArgumentationFramework with compute_grounded(), _defeats(), get_epistemic_status(), compute_preferred(), compute_stable(), add_counter_argument(), get_argument_tree()
6. Write tests for schema_v4 and argumentation, run them: `pytest anvikshiki_v4/tests/ -v`

**Phase 2: Compilation + UQ**

7. Implement `t2_compiler_v4.py` from BUILD_GUIDE_V2.md Section 8.4 — compile_t2() with fixpoint loop, _build_rule_tag(), all three attack derivation types
8. Implement `uncertainty.py` from BUILD_GUIDE_V2.md Section 11.2 — compute_uncertainty_v4()
9. Update `data/sample_architecture.yaml` with the expanded version from BUILD_GUIDE_V2.md Section 8.5 (includes conflicts and scope exclusions)
10. Write tests, run: `pytest anvikshiki_v4/tests/ -v`

**Phase 3: Contestation + Engine**

11. Implement `contestation.py` from BUILD_GUIDE_V2.md Section 12.3 — ContestationManager with vāda/jalpa/vitaṇḍā + apply_contestation()
12. Implement `engine_v4.py` from BUILD_GUIDE_V2.md Section 13.2 — AnvikshikiEngineV4 (8-step pipeline) + Phase 1 variant
13. Implement `optimize.py` from BUILD_GUIDE_V2.md Section 14.1 — calibration_metric_v4()
14. Write `__init__.py` exports
15. Write all remaining tests, run full suite: `pytest anvikshiki_v4/tests/ -v`

**Phase 4: Verify**

16. Run the Quick Start example from BUILD_GUIDE_V2.md Section 13.3 (adapt for available LLM)
17. Verify: semiring laws pass, grounded extension is conflict-free, scope exclusions generate undercutting attacks, rebutting attacks create mutual attacks, epistemic status emerges from extension membership

### Key Constraints

- Use frozen dataclasses for ProvenanceTag and Argument (not Pydantic) — needed for hashability
- Use mutable dataclass for ArgumentationFramework and Attack
- ProvenanceTag.__post_init__ must validate b + d + u ≈ 1.0 (tolerance 0.05)
- _defeats() must check pramāṇa hierarchy first (bādhita), then tag.strength
- compile_t2() must include the forward-chaining fixpoint loop (thesis omitted it)
- All code must work with DSPy 3.1.x (use dspy.Refine not deprecated dspy.Assert)
- Do NOT modify anything in `anvikshiki/` — v3 stays intact

### Success Criteria

All of these must pass:
```bash
source .venv/bin/activate
pytest anvikshiki_v4/tests/test_schema_v4.py -v     # Semiring laws
pytest anvikshiki_v4/tests/test_argumentation.py -v  # Grounded extension
pytest anvikshiki_v4/tests/test_t2_compiler_v4.py -v # AF compilation
pytest anvikshiki_v4/tests/test_uncertainty.py -v     # UQ from tags
pytest anvikshiki_v4/tests/test_contestation.py -v   # Debate protocols
pytest anvikshiki_v4/tests/ -v                        # Full suite
```
