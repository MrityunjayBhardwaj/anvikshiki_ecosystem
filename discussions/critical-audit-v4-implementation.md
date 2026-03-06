# Critical Audit: v4 Implementation — Handwavy, Hardcoded, and Unsupported

**Date:** 2026-03-06
**Scope:** Full read of all anvikshiki_v4 modules post audit-fix implementation
**Method:** Line-by-line review of schema_v4.py, t2_compiler_v4.py, argumentation.py, config.py, grounding.py, uncertainty.py, contestation.py, engine_v4.py, datalog_engine.py, coverage.py, kb_augmentation.py

---

## SEVERITY 1: Structurally Broken / Dead Code

### 1. config.py is entirely dead code

Created to address audit I-02, I-04, I-05, I-06 — but **zero modules import or consume it**. Every other module uses its own local constants:

| Config field | Actually used by | Uses config.py? |
|---|---|---|
| `decay_half_life_days` | `t2_compiler_v4.py:37` (`DECAY_HALF_LIFE_DAYS = 365`) | No |
| `belief_map` | `t2_compiler_v4.py:30-35` (`BELIEF_MAP = {...}`) | No |
| `max_argument_combos_per_rule` | `t2_compiler_v4.py:18` (`MAX_ARGUMENT_COMBOS_PER_RULE = 5`) | No |
| `max_compilation_iterations` | `t2_compiler_v4.py:147,205` (`MAX_ITERATIONS = 100`) | No |
| `preferred_timeout_seconds` | `argumentation.py:241` (hardcoded `30.0`) | No |
| `stable_timeout_seconds` | `argumentation.py:349` (hardcoded `60.0`) | No |
| `es_established_belief` etc. | `schema_v4.py:193-202` (hardcoded `0.8`, `0.1`, etc.) | No |

The config was the WS0 deliverable ("centralize thresholds") but WS5 ("wire config") was dropped. Result: a facade with no plumbing.

### 2. `_check_contested()` is dead logic (argumentation.py:209-235)

```python
def _check_contested(self, out_args):
    for arg in out_args:
        # ... analyzes defeaters ...
        if all_defeaters_attacked:
            return EpistemicStatus.CONTESTED  # ← branch A
    return EpistemicStatus.CONTESTED          # ← branch B (identical)
```

Both branches return `CONTESTED`. The "heuristic preferred semantics approximation" analyzes whether defeaters are themselves attacked, then **ignores the result entirely**. Every OUT argument gets CONTESTED regardless of the analysis.

### 3. Two parallel inference engines that ignore each other

- `DatalogEngine` (datalog_engine.py) — semi-naive Datalog evaluator with Heyting lattice values
- `t2_compiler_v4.py`'s forward-chaining loop (lines 146-213) — naive fixpoint over ASPIC+ arguments

These use **different representations** (Fact/Rule vs Argument/Attack), **different evaluation strategies** (semi-naive vs naive), and **different epistemic models** (5-value Heyting lattice vs continuous SL opinions). The DatalogEngine is only used as an optional validator in grounding Layer 5 and kb_augmentation's compile test. The actual reasoning path never touches it.

---

## SEVERITY 2: Claims That Don't Hold

### 4. "Semiring" is not a semiring

The docstring and thesis claim ProvenanceTag forms a semiring under tensor/oplus. A semiring requires:
- tensor associativity — **tested, holds** (Jøsang trust discounting)
- oplus commutativity — **tested, holds** (cumulative fusion)
- oplus identity (zero) — **tested, holds**
- tensor identity (one) — **tested, LEFT only** (trust discounting is non-commutative)
- **Distributivity: tensor distributes over oplus** — **never tested, almost certainly fails**

Jøsang trust discounting does NOT distribute over cumulative fusion. This is a known result. So `(b,d,u)` under these operations forms a **left-unital, associative, commutative pair of operations** — not a semiring. The claim is mathematically false.

### 5. "Five-layer grounding defense" is four layers at best

Layer 2 ("grammar-constrained decoding") exists only as a comment in grounding.py:241:

```python
# Layer 2 (grammar constraint) applied at serving level — transparent.
```

There's no code, no configuration, no integration with any grammar-constrained decoding library (XGrammar, Instructor, CRANE — all mentioned in BUILD_GUIDE.md). The comment asserts something exists that doesn't.

### 6. Source overlap interpolation in oplus is ad-hoc (schema_v4.py:149-158)

```python
new_b = (1 - overlap_ratio) * fused_b + overlap_ratio * avg_b
```

Linear interpolation between cumulative fusion and simple averaging based on source Jaccard overlap. No reference in Jøsang 2016 or any other SL literature supports this formula. Problems:
- Can break the `b+d+u=1` invariant (fused and averaged values have different sums)
- The `min(1.0, ...)` / `max(0.0, ...)` clamps at lines 161-163 prove the formula goes out of bounds
- There's no test verifying the invariant holds with overlap

### 7. ASPIC+ argument construction is interleaved incorrectly (t2_compiler_v4.py:204-213)

The compile loop interleaves `_derive_rule_arguments()` and `_derive_attacks()` in the same iteration:

```python
for _ in range(MAX_ITERATIONS):
    _derive_rule_arguments(af, knowledge_store)
    _derive_attacks(af, knowledge_store)    # ← attacks on PARTIAL argument set
```

ASPIC+ theory (Prakken 2010) requires building the complete argument set first, then deriving all attacks. Interleaving means attacks in iteration N are computed against arguments from iteration N, missing attacks that should target arguments created later. The fixpoint eventually catches up, but intermediate states are theoretically unsound.

---

## SEVERITY 3: Unsupported Design Choices (~35 magic numbers)

### 8. Metadata propagation rules are asserted, not derived

| Operation | trust_score | decay_factor | derivation_depth | pramana_type |
|---|---|---|---|---|
| tensor | `min(a,b)` | `min(a,b)` | `a+b` | `min(a,b)` |
| oplus | `max(a,b)` | `max(a,b)` | `min(a,b)` | `max(a,b)` |

These are described as "monotone product lattice" but:
- Why `min` for trust under tensor? If source A (trust=0.9) cites source B (trust=0.8), the chain gets trust=0.8 — but what if A's high trust *endorses* B's reliability?
- Why `max` for trust under oplus? If two arguments from sources with trust 0.3 and 0.9 support the same conclusion, why does the combined trust equal 0.9 rather than some aggregate?
- `derivation_depth = min(a,b)` under oplus is counterintuitive — if one argument has depth 5 and another depth 1, the combined is 1. The shallow argument dominates.
- No reference supports these specific choices. They're plausible defaults, not theoretical results.

### 9. `_build_rule_tag()` trust computation (t2_compiler_v4.py:112)

```python
trust = vyapti.confidence.formulation * vyapti.confidence.existence
```

Multiplying two confidence scores to get a trust score has no theoretical basis. Why multiply rather than `min()`, geometric mean, or harmonic mean? This collapses two independent dimensions into one in an arbitrary way.

### 10. MINIMAL grounding sets confidence=1.0 unconditionally (grounding.py:224)

A single LLM call without any verification gets perfect confidence. This defeats the purpose of confidence tracking and means any downstream code checking `grounding.confidence < threshold` will never fire in MINIMAL mode.

### 11. `_check_scope()` uses substring matching (grounding.py:332)

```python
if any(excl.lower() in p.lower() for p in predicates):
```

This is a substring check, not predicate matching. `"market"` would match `"stock_market_cap"`, `"market_analysis"`, `"supermarket_chain"`. Meanwhile, the t2_compiler uses `_predicate_name()` for proper scope matching. Two different scope-checking strategies in the same system.

### 12. `_synthesis_reward` is trivially gameable (engine_v4.py:45-83)

- Checks for "certainly" as overconfidence detection (what about "definitely", "always", "without doubt"?)
- Checks for hedging words in a list — an LLM that learns to prepend "evidence suggests" to every response scores 0.2 for free
- `len(pred.response) > 50` as a substantiveness check — trivially satisfied

### 13. Full list of magic numbers

| Value | Location | Justification |
|---|---|---|
| 0.05 tolerance | schema_v4.py:68 | None |
| 0.8/0.1/0.5/0.3/0.4/0.6 thresholds | schema_v4.py:193-200 | "DSPy-optimizable" (but not) |
| 5 max combos | t2_compiler_v4.py:18 | None |
| 365 half-life | t2_compiler_v4.py:37 | None |
| 0.3 decay threshold | t2_compiler_v4.py:38 | None |
| 0.95/0.6/0.2/0.4 belief map values | t2_compiler_v4.py:31-34 | None |
| 100 max iterations | t2_compiler_v4.py:147,205 | None |
| 0.693 ln(2) | t2_compiler_v4.py:117 | Correct math, but `math.log(2)` exists |
| 30.0 preferred timeout | argumentation.py:241 | None |
| 60.0 stable timeout | argumentation.py:349 | None |
| 0.4 clarification threshold | grounding.py:266 | None |
| 0.9 round-trip threshold | grounding.py:280 | None |
| 3 max refinement rounds | grounding.py:296 | None |
| 0.7 ensemble temperature | grounding.py:248 | None |
| 180 days decay warning | grounding.py:348 | None |
| 0.6/0.2/0.4 coverage thresholds | coverage.py:22-24 | None |
| 0.4 applicability threshold | kb_augmentation.py:43 | None |
| 8 max new vyaptis | kb_augmentation.py:44 | None |
| 0.75 max confidence cap | kb_augmentation.py:45 | None |
| 0.85 formulation multiplier | kb_augmentation.py:355 | None |
| 0.1 uncertainty floor | contestation.py:181 | None |
| N=3, threshold=0.5 | engine_v4.py:113-118 | None |
| 0.20/0.15/... reward weights | engine_v4.py:52-83 | "aligned" (claimed, not verified) |
| 50 char minimum | engine_v4.py:55 | None |
| 5 max chunks | engine_v4.py:253 | None |

---

## SEVERITY 4: Code Quality Issues

### 14. `_domain_contrary_index` rebuilt on every call (t2_compiler_v4.py:103)

```python
if ks is not None and (na, nb) in _build_domain_contrary_index(ks):
```

`_build_domain_contrary_index(ks)` is called for every pair comparison. For N conclusions, that's O(N²) calls to rebuild a set. The module-level `_domain_contrary_index` variable is defined but never used.

### 15. `forward()` and `forward_with_coverage()` share ~70% identical code (engine_v4.py)

Steps 3-8 are copy-pasted between both methods (lines 120-267 vs 269-494). Any bug fix in one requires remembering to update the other.

### 16. `compute_preferred()` and `compute_stable()` are brute-force exponential (argumentation.py:239-408)

`_enumerate_stable` does a full 2^n enumeration with timeout. `_enumerate_preferred` does backtracking without good pruning. For frameworks with >20 arguments, these will timeout and silently fall back to grounded semantics. The timeout-based fallback isn't flagged to the caller.

---

## Summary Table

| # | Issue | Type | Severity |
|---|---|---|---|
| 1 | config.py created but never wired | Dead code | Critical |
| 2 | `_check_contested()` always returns same value | Dead logic | Critical |
| 3 | Two parallel inference engines, neither uses the other | Architectural | Critical |
| 4 | "Semiring" claim — distributivity doesn't hold | False claim | High |
| 5 | Layer 2 grammar-constrained decoding doesn't exist | False claim | High |
| 6 | oplus overlap interpolation — ad-hoc, breaks invariant | Unsupported | High |
| 7 | Interleaved argument/attack construction | Theoretically unsound | Medium |
| 8 | Metadata lattice ops asserted without derivation | Unsupported | Medium |
| 9 | trust = formulation × existence — arbitrary | Unsupported | Medium |
| 10 | MINIMAL mode confidence=1.0 | Semantic error | Medium |
| 11 | Scope checking uses substring vs predicate match | Inconsistency | Medium |
| 12 | Reward function trivially gameable | Handwavy | Medium |
| 13 | 35+ magic numbers | Hardcoded | Medium |
| 14 | Domain contrary index rebuilt O(N²) times | Performance | Low |
| 15 | forward() / forward_with_coverage() code duplication | DRY violation | Low |
| 16 | Preferred/stable semantics brute-force with silent fallback | Scalability | Low |

---

## Honest Assessment

The implementation is a **functional prototype** that passes its tests because the tests were written alongside the code. The ASPIC+ grounded semantics core (argumentation.py:53-109) is the strongest piece — polynomial, correct algorithm, well-referenced. The Jøsang trust discounting tensor is mathematically sound. Everything else ranges from "reasonable heuristic with no citation" to "dead code that claims to solve problems it doesn't."

The thesis claims mathematical unification (semiring, lattice, presheaf topos). The implementation delivers pragmatic composition with honest-sounding docstrings. The gap between claim and reality is the central problem.
