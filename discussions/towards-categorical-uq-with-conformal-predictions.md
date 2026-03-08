# Towards Categorical UQ with Conformal Predictions

**Date:** 2026-03-07
**Context:** Replacing threshold-based `epistemic_status()` (5 magic floats) with calibrated categorical uncertainty quantification over {ESTABLISHED, HYPOTHESIS, PROVISIONAL, OPEN, CONTESTED}.

---

## 1. The Problem

The current engine derives epistemic status in two steps:

1. **Grounded semantics** produces labels: IN / OUT / UNDECIDED (structural, polynomial, principled)
2. **`epistemic_status()`** thresholds continuous SL values into 5 categories using 5 magic floats:

```python
if belief > 0.8 and uncertainty <= 0.1:  return ESTABLISHED
elif belief > 0.5 and uncertainty < 0.3: return HYPOTHESIS
elif disbelief > 0.4 and belief > 0.3:   return CONTESTED
elif uncertainty > 0.6:                   return OPEN
else:                                     return PROVISIONAL
```

**What's wrong:**
- The thresholds are arbitrary (why 0.8 and not 0.75?)
- The output is a single point (ESTABLISHED), not a distribution (72% ESTABLISHED, 21% HYPOTHESIS, ...)
- Information is destroyed — the downstream LLM gets "ESTABLISHED" when the engine actually has (b=0.81, d=0.02, u=0.17)
- Edge cases: a claim with b=0.79 is HYPOTHESIS; b=0.81 is ESTABLISHED. The 0.02 difference creates a categorical jump.
- Violates P4 (graded native) and P6 (structural provenance)

**What we want:** A calibrated categorical distribution over epistemic statuses with formal coverage guarantees.

---

## 2. Why Conformal Prediction

### 2.1 What conformal prediction gives us

Conformal prediction (Vovk, Gammerman & Shafer 2005) produces **prediction sets** with guaranteed coverage:

> For any user-specified error rate α ∈ (0,1), the prediction set C(x) satisfies:
> P(Y ∈ C(x)) ≥ 1 - α

This is **distribution-free** — it works for any underlying data distribution, any model class. The only requirement is exchangeability of calibration data.

For our 5-class problem, this means:
- At α=0.1: "This conclusion is {ESTABLISHED, HYPOTHESIS} with ≥90% coverage"
- At α=0.05: "This conclusion is {ESTABLISHED} with ≥95% coverage" (tighter set when evidence is strong)
- When uncertain: "This conclusion is {ESTABLISHED, HYPOTHESIS, PROVISIONAL} with ≥95% coverage" (wider set)

The **set size** is itself a calibrated uncertainty measure: |C(x)| = 1 means high confidence, |C(x)| = 5 means the engine genuinely doesn't know.

### 2.2 Why not alternatives

| Alternative | Problem for our context |
|---|---|
| **Multinomial SL** (Jøsang 2016 Ch. 5) | Requires redesigning ProvenanceTag from binary to 5-class. Composition (tensor, oplus) becomes much more complex. Correct but expensive to implement. |
| **Platt scaling / temperature scaling** | Requires a neural network producing logits. Our classifier is structural (label + pramāṇa + SL values), not neural. |
| **Bayesian posterior** | Requires specifying a prior over epistemic statuses — reintroduces the calibration problem (§3.1 of thesis: "where do the numbers come from?") |
| **Evidential deep learning** (Sensoy et al. 2018) | Requires neural network training end-to-end. Overkill for a 5-class, ~10-feature problem. |

Conformal prediction works with **any** base classifier — even a simple decision tree or random forest over our structural features. No neural network needed. No distributional assumptions. Formal guarantees.

### 2.3 Specific variant: RAPS

We use **Regularized Adaptive Prediction Sets (RAPS)** (Angelopoulos et al. 2021), which extends APS (Romano, Sesia & Candès 2020):

1. Train any base classifier f: features → softmax over 5 statuses
2. On calibration set, compute nonconformity scores: s(x, y) = Σ_{j: π_j(x) ≤ π_y(x)} f_πj(x) + u · f_πy(x) + λ(o(x,y) - k_reg)⁺
   - π is the sorting permutation (most probable first)
   - λ and k_reg are regularization parameters penalizing large sets
3. Compute quantile q̂ = ⌈(1-α)(n+1)⌉/n-th quantile of calibration scores
4. At inference: C(x) = {y : s(x, y) ≤ q̂}

**Why RAPS over plain APS:** RAPS produces smaller, more informative prediction sets by penalizing inclusion of unlikely classes. For our 5-class problem, this is important — we want {ESTABLISHED} when the evidence is clear, not {ESTABLISHED, HYPOTHESIS, PROVISIONAL, OPEN, CONTESTED}.

---

## 3. Feature Space

The classifier operates on features extracted from the argumentation framework at the conclusion level. Each conclusion c has:

### 3.1 Structural features (from ASPIC+ / grounded semantics)

| Feature | Type | Source | Description |
|---|---|---|---|
| `label` | Categorical(3) | `af.labels[arg_id]` | IN / OUT / UNDECIDED — the grounded extension label |
| `num_in_args` | int | argument count | Number of IN-labeled arguments for this conclusion |
| `num_out_args` | int | argument count | Number of OUT-labeled arguments for this conclusion |
| `num_undecided_args` | int | argument count | Number of UNDECIDED arguments |
| `num_attacks_received` | int | attack index | Total attacks on arguments for this conclusion |
| `num_attacks_survived` | int | attack index | Attacks where the target is still IN |
| `has_strict_support` | bool | argument.is_strict | Any supporting argument uses a strict top rule |
| `max_sub_argument_depth` | int | argument tree | Deepest sub-argument chain |

### 3.2 Pramāṇa features (from Nyāya ontology)

| Feature | Type | Source | Description |
|---|---|---|---|
| `best_pramana` | Ordinal(4) | `combined.pramana_type` | Highest pramāṇa type among IN arguments (1-4) |
| `pramana_diversity` | int | unique pramāṇa types | Number of distinct pramāṇa types among supporting arguments |
| `has_pratyaksa` | bool | pramāṇa check | Any supporting argument backed by direct evidence |

### 3.3 SL features (from Subjective Logic annotation)

| Feature | Type | Source | Description |
|---|---|---|---|
| `belief` | float [0,1] | `combined.belief` | Combined belief after ⊕ fusion of accepted arguments |
| `disbelief` | float [0,1] | `combined.disbelief` | Combined disbelief |
| `uncertainty` | float [0,1] | `combined.uncertainty` | Combined uncertainty |
| `trust_score` | float [0,1] | `combined.trust_score` | Combined trust |
| `decay_factor` | float [0,1] | `combined.decay_factor` | Combined decay |
| `strength` | float [0,1] | `combined.strength` | belief × trust × decay |

### 3.4 Provenance features

| Feature | Type | Source | Description |
|---|---|---|---|
| `num_sources` | int | `combined.source_ids` | Number of distinct sources supporting this conclusion |
| `derivation_depth` | int | `combined.derivation_depth` | Chain length |

**Total: ~18 features.** This is a small, well-structured feature space — ideal for tree-based classifiers, no need for neural networks.

---

## 4. Training Data

### 4.1 The data we need

Each training example is a tuple:

```
(features_18d, ground_truth_status ∈ {ESTABLISHED, HYPOTHESIS, PROVISIONAL, OPEN, CONTESTED})
```

We need two sets:
- **Training set** (for the base classifier): ≥500 examples
- **Calibration set** (for conformal prediction): ≥200 examples (separate, never seen during training)

### 4.2 Three sources of training data

#### Source A: Synthetic generation from the argumentation framework (immediate, free)

The engine can generate training data by:

1. Take any KnowledgeStore (e.g., `business_expert.yaml`)
2. Vary query predicates systematically (all subsets of known predicates)
3. Vary BELIEF_MAP values (sweep belief from 0.0 to 1.0)
4. Vary decay_factor (sweep from 0.0 to 1.0)
5. For each configuration: compile AF, compute grounded extension, extract features
6. Label using **expert heuristic** (the current threshold function, treated as noisy ground truth)

**Volume:** For a KB with 10 predicates and 10 rules, sweeping 5 belief levels × 5 decay levels × 2^10 predicate subsets = ~50K examples. Far more than needed.

**Quality concern:** The labels come from the threshold function we're trying to replace. This bootstraps us — the conformal prediction layer will correct for threshold miscalibration through the calibration step, but the base categories are still defined by the original heuristic. This is acceptable as a starting point because:
- The categories themselves (ESTABLISHED, HYPOTHESIS, etc.) are from Nyāya theory — they're the right categories
- Only the *boundaries* between categories are noisy
- Conformal prediction is robust to noise in the base classifier

#### Source B: Expert annotation (high quality, expensive)

Create ~200 scenario cards, each describing:
- A conclusion with its argument tree
- The SL values, pramāṇa types, and attack structure
- Ask 3+ domain experts: "What epistemic status would you assign?"

Inter-annotator agreement (Krippendorff's α) determines annotation quality. For 5 ordinal categories, α > 0.67 is acceptable.

**This is the calibration set.** The conformal guarantee only holds if the calibration data is from the true distribution. Synthetic data bootstraps the classifier; expert data calibrates it.

#### Source C: Engine usage logs (future, continuous)

Once deployed, the engine produces conclusions with features. Users can contest or accept them (via ContestationManager). Each contestation event is an implicit label:
- User accepts → agrees with assigned status
- User contests via viruddha → evidence against current status
- User doesn't contest → weak accept signal

This enables **online calibration** — the conformal quantile q̂ is updated as new calibration data arrives.

### 4.3 Data generation protocol

**Phase 1 (immediate, 0 cost):**
1. Run synthetic generation (Source A) → ~10K examples
2. Split 80/20 → 8K training, 2K held-out
3. Train base classifier on 8K
4. Use 2K as calibration set for conformal prediction
5. **Honest caveat:** marginal coverage guaranteed, conditional coverage approximate

**Phase 2 (1-2 weeks of expert time):**
1. Create 200 expert-annotated scenario cards (Source B)
2. Replace synthetic calibration set with expert calibration set
3. Retrain base classifier on synthetic + small expert training portion
4. Conformal calibration on expert-only set → stronger coverage guarantees

**Phase 3 (ongoing):**
1. Collect user contestation logs (Source C)
2. Periodically recalibrate: update q̂ with new calibration data
3. Monitor coverage rate: if empirical coverage drops below 1-α, recalibrate

---

## 5. The Base Classifier

### 5.1 Model choice: Gradient Boosted Trees (XGBoost / LightGBM)

For 18 features and 5 classes, gradient boosted trees are optimal:
- Handle mixed feature types (categorical, ordinal, continuous)
- No feature scaling needed
- Native feature importance for interpretability
- Fast training (~seconds) and inference (~microseconds)
- Work well with small datasets (500-10K)
- scikit-learn, XGBoost, or LightGBM — all standard Python libraries

**Why not neural networks:** 18 features, 5 classes, ~10K training examples. Neural networks would overfit. Trees are the right tool.

**Why not rule-based (current approach):** The current 5-threshold system IS a hand-specified decision tree with 5 splits. A learned tree finds optimal splits from data instead of hand-specifying them. Same structure, better boundaries.

### 5.2 Training procedure

```python
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score

# X: (N, 18) feature matrix
# y: (N,) labels in {0, 1, 2, 3, 4} for the 5 statuses

clf = GradientBoostingClassifier(
    n_estimators=100,
    max_depth=4,        # Shallow trees — interpretable
    min_samples_leaf=10, # Regularize for small datasets
    n_classes=5,
)
clf.fit(X_train, y_train)

# Cross-validation accuracy (expect ~85-95% given features are highly predictive)
scores = cross_val_score(clf, X_train, y_train, cv=5)
```

### 5.3 Ordinal structure

The epistemic statuses have ordinal structure: ESTABLISHED > HYPOTHESIS > PROVISIONAL > OPEN > CONTESTED (roughly — OPEN and CONTESTED are not naturally ordered, but the first three are).

For the base classifier, we can exploit this via:
- **Ordinal encoding** of the target (0-4)
- **Ordinal loss function** that penalizes ESTABLISHED↔CONTESTED errors more than ESTABLISHED↔HYPOTHESIS errors
- Or simply: standard multi-class classification, and let conformal prediction handle the uncertainty

The ordinal structure matters more for the prediction set interpretation: a set {ESTABLISHED, HYPOTHESIS} is more informative than {ESTABLISHED, CONTESTED} because the former spans adjacent categories.

---

## 6. Conformal Calibration

### 6.1 The calibration procedure

Given: trained classifier f, calibration set {(x_i, y_i)}_{i=1}^{n_cal}

```python
import numpy as np

# Step 1: Get softmax probabilities on calibration set
probs_cal = clf.predict_proba(X_cal)  # (n_cal, 5)

# Step 2: Compute nonconformity scores (APS)
scores = []
for i in range(n_cal):
    # Sort classes by decreasing probability
    sorted_idx = np.argsort(-probs_cal[i])
    cumsum = 0.0
    for rank, j in enumerate(sorted_idx):
        cumsum += probs_cal[i, j]
        if j == y_cal[i]:
            # Add uniform random for tie-breaking (randomized APS)
            u = np.random.uniform()
            score = cumsum - (1 - u) * probs_cal[i, j]
            scores.append(score)
            break

# Step 3: Compute quantile
alpha = 0.10  # 90% coverage
q_hat = np.quantile(scores, (1 - alpha) * (1 + 1/n_cal))
```

### 6.2 Prediction sets at inference

```python
def predict_with_uq(clf, x, q_hat):
    """Return prediction set + distribution."""
    probs = clf.predict_proba(x.reshape(1, -1))[0]
    sorted_idx = np.argsort(-probs)

    # Build prediction set
    prediction_set = []
    cumsum = 0.0
    for j in sorted_idx:
        cumsum += probs[j]
        prediction_set.append(STATUSES[j])
        if cumsum >= q_hat:
            break

    # Distribution: normalized probabilities
    distribution = {
        STATUSES[i]: float(probs[i])
        for i in range(5)
    }

    return {
        "primary_status": STATUSES[sorted_idx[0]],  # argmax
        "prediction_set": prediction_set,             # calibrated set
        "distribution": distribution,                  # full distribution
        "set_size": len(prediction_set),              # uncertainty indicator
        "coverage_guarantee": 1 - alpha,              # formal guarantee
    }
```

### 6.3 Coverage guarantees — what we get and what we don't

**What conformal prediction guarantees (Vovk et al. 2005):**

> **Marginal coverage:** Over the distribution of test examples,
> P(Y_test ∈ C(X_test)) ≥ 1 - α

This holds for ANY base classifier, ANY data distribution, with finite-sample correction.

**What it does NOT guarantee:**

> **Conditional coverage:** For a specific argument structure x,
> P(Y ∈ C(x) | X = x) ≥ 1 - α  ← NOT guaranteed

This is a known limitation (thesis §7.5.3, constraint I7). The marginal guarantee says "on average across all queries, 90% are covered." It does NOT say "for this specific query, we're 90% sure."

**Mitigation — Mondrian conformal prediction:**

Partition the feature space into groups and calibrate separately within each group:
- Group 1: label = IN
- Group 2: label = OUT
- Group 3: label = UNDECIDED

Within each group, the marginal guarantee holds. This gives approximate conditional coverage per group. With 3 groups and n_cal = 200, each group gets ~67 calibration examples — still sufficient for reliable quantiles.

**Stronger mitigation — coverage groups by (label, pramāṇa_type):**

12 groups (3 labels × 4 pramāṇa types). But this requires n_cal ≈ 50 per group → n_cal ≈ 600 total. Achievable with synthetic data, tight with expert annotations.

### 6.4 Sample complexity

How much calibration data do we need?

The conformal guarantee holds for any n ≥ 1, but the prediction sets become tighter with more data:

| n_cal | Expected set size at α=0.1 | Coverage reliability |
|---|---|---|
| 50 | Large (conservative) | Guaranteed but loose |
| 100 | Moderate | Good for 5 classes |
| 200 | Close to optimal | Recommended minimum |
| 500 | Near-optimal | Ideal |
| 1000+ | Minimal overhead | Diminishing returns |

For 5 classes, n_cal = 200 is the practical minimum. With synthetic generation (Source A), we can easily produce 2000+ calibration examples.

---

## 7. Integration with the Anvikshiki Architecture

### 7.1 Where it plugs in

```
                CURRENT                          WITH CONFORMAL UQ
                ───────                          ─────────────────

af.compute_grounded()                    af.compute_grounded()
        │                                        │
        ▼                                        ▼
af.get_epistemic_status(conc)            af.get_epistemic_status(conc)
        │                                        │
        ▼                                        ▼
combined.epistemic_status()              extract_features(conc, af, combined)
  [5 threshold floats]                           │
        │                                        ▼
        ▼                                conformal_predict(features)
EpistemicStatus.ESTABLISHED                      │
  [single point]                                 ▼
                                         {
                                           primary: ESTABLISHED,
                                           set: {ESTABLISHED, HYPOTHESIS},
                                           distribution: {EST: 0.72, HYP: 0.21, ...},
                                           coverage: 0.90,
                                           set_size: 2
                                         }
```

### 7.2 Code changes

**`argumentation.py` — `get_epistemic_status()`:**

Replace `status = combined.epistemic_status()` (line 193) with:

```python
if accepted:
    combined = accepted[0].tag
    for a in accepted[1:]:
        combined = ProvenanceTag.oplus(combined, a.tag)

    # Extract features for conformal classifier
    features = _extract_features(conclusion, self, combined, accepted)
    uq_result = self._conformal_classifier.predict(features)

    return (uq_result["primary_status"], uq_result, combined, accepted)
```

**`schema_v4.py` — `epistemic_status()`:**

Deprecate (keep for backward compat, mark as legacy). The conformal classifier replaces it.

**`engine_v4.py` — output schema:**

The engine output gains richer epistemic information:

```python
results[conc] = {
    "status": uq_result["primary_status"],        # backward compat
    "status_distribution": uq_result["distribution"],  # NEW
    "prediction_set": uq_result["prediction_set"],     # NEW
    "coverage_guarantee": uq_result["coverage"],       # NEW
    "set_size": uq_result["set_size"],                 # NEW
    "tag": combined,
    "arguments": accepted,
}
```

**`uncertainty.py` — `compute_uncertainty_v4()`:**

Replace threshold-based explanations with conformal-derived explanations:

```python
"epistemic": {
    "status": uq_result["primary_status"].value,
    "prediction_set": [s.value for s in uq_result["prediction_set"]],
    "distribution": uq_result["distribution"],
    "explanation": (
        f"'{conclusion}': {uq_result['primary_status'].value} "
        f"(confidence set: {uq_result['prediction_set']}, "
        f"coverage ≥ {uq_result['coverage']:.0%})"
    ),
},
```

### 7.3 New files

```
anvikshiki_v4/
├── epistemic_classifier.py    # Feature extraction + conformal prediction
├── data/
│   ├── calibration_data.json  # Calibration set (generated or expert)
│   └── classifier_model.pkl   # Trained gradient boosted classifier
```

### 7.4 What the downstream LLM sees

**Before (current):**
```
- value_creation: established (belief=0.81, sources=['R01', 'R03'])
```

**After (conformal UQ):**
```
- value_creation: established (90% confidence set: {established, hypothesis},
  distribution: established=72%, hypothesis=21%, provisional=5%, open=1%, contested=1%,
  sources=['R01', 'R03'])
```

The LLM can now calibrate its hedging language based on the distribution width:
- set_size=1 → "This is well-established"
- set_size=2 → "This is likely established, though may be hypothesis-level"
- set_size=3+ → "The epistemic status is uncertain — evidence is mixed"

---

## 8. Training Cost Analysis

### 8.1 Computational cost

| Step | Cost | Time |
|---|---|---|
| **Synthetic data generation** | N × compile_t2 + compute_grounded | ~10K examples in ~30 seconds (polynomial AF operations) |
| **Feature extraction** | O(|arguments|) per conclusion | Negligible — already computed during get_epistemic_status |
| **Classifier training** | GBT on 8K × 18 features | < 5 seconds on any modern CPU |
| **Conformal calibration** | Quantile computation on 2K scores | < 1 second |
| **Total setup** | One-time | < 1 minute |

### 8.2 Inference cost (per query)

| Step | Additional cost vs. current |
|---|---|
| Feature extraction | ~0 (values already computed) |
| Classifier predict_proba | ~10 microseconds (tree traversal) |
| Conformal set construction | ~1 microsecond (sort 5 values) |
| **Total per conclusion** | **~11 microseconds** |

For comparison, the grounded extension computation is O(|args| × |attacks|), typically ~1-10 milliseconds. The conformal prediction adds < 0.1% overhead.

### 8.3 LLM call cost

**Zero additional LLM calls.** The conformal classifier is a local gradient boosted tree — no LLM involvement. The existing grounding call (1 LLM call) and synthesis call (1 LLM call) are unchanged.

### 8.4 Expert annotation cost (Phase 2)

200 scenario cards × ~5 minutes per card × 3 annotators = ~50 person-hours. This is a one-time cost for high-quality calibration data.

---

## 9. Calibration Quality Assessment

### 9.1 How to measure calibration

**Empirical coverage rate:** On a held-out test set:

```python
covered = sum(1 for x, y in test_set if y in C(x))
coverage_rate = covered / len(test_set)
# Should be ≥ 1 - alpha
```

**Average set size:** Smaller is better (tighter uncertainty):

```python
avg_set_size = sum(len(C(x)) for x, _ in test_set) / len(test_set)
# Ideal: close to 1.0 for easy cases, close to 5.0 for genuinely uncertain cases
```

**Stratified coverage:** Coverage per (label, pramāṇa_type) group. If any group has coverage < 1 - α, the conditional coverage is violated for that group → use Mondrian conformal prediction.

### 9.2 Expected calibration quality

Given the feature space:
- `label` alone perfectly determines OPEN (UNDECIDED) and CONTESTED (all OUT)
- Within IN: `pramana_type` + `belief` + `uncertainty` strongly predict the 3-way split

Expected base classifier accuracy: **~90-95%** (the features are highly predictive by design — they were chosen because they're the structural signals for epistemic status).

Expected average set size at α=0.1: **~1.2-1.5** (most predictions will be single-class, with a few edge cases producing 2-class sets).

### 9.3 When calibration will be poor

1. **Novel KB structures** not represented in calibration data — the classifier hasn't seen this feature combination before. Mitigation: retrain periodically as new KBs are deployed.

2. **Extremely imbalanced classes** — if PROVISIONAL is rare in training data, the classifier may have poor recall for it. Mitigation: class weighting in the GBT, or synthetic oversampling.

3. **Distribution shift** — if deployed KBs have different pramāṇa distributions than the training KB. Mitigation: use domain-general features (ratios, normalized values) rather than absolute values.

---

## 10. Relationship to Other Architecture Fixes

### 10.1 Interaction with Fix 1 (Kill jalpa/vitanda)

**Compatible.** The conformal classifier uses grounded labels as a primary feature. Removing jalpa/vitanda from the engine hot path doesn't affect the classifier — it only uses grounded extension results.

CONTESTED status derivation currently requires "OUT in grounded, IN in preferred" — but preferred semantics is NP-hard and we're removing it from the hot path. With the conformal classifier, CONTESTED is learned from features (all-OUT label, high disbelief, etc.) rather than requiring preferred semantics computation.

### 10.2 Interaction with Fix 3 (Centralize parameters)

**Replaces most of them.** The conformal classifier eliminates:
- 5 epistemic_status() thresholds (replaced by learned boundaries)
- BELIEF_MAP influence on status (absorbed into learned features)

Remaining parameters (DECAY_HALF_LIFE, reward weights) are unaffected — they're in different parts of the pipeline.

### 10.3 Interaction with Fix 4 (Axiomatize metadata)

**Orthogonal.** The conformal classifier consumes metadata features (trust_score, decay_factor) but doesn't change how they compose. The axiomatization of tensor=meet / oplus=join is about composition; the classifier is about status derivation from composed values.

### 10.4 Future path to Multinomial SL (Option A from earlier discussion)

The conformal prediction framework is **a stepping stone** to multinomial SL. If we later redesign ProvenanceTag to carry a 5-class SL opinion natively, the conformal calibration layer can calibrate those opinions:
- Multinomial SL produces a distribution over 5 statuses → use as base classifier softmax
- Conformal calibration ensures the distribution is well-calibrated
- Same RAPS procedure, different base model

---

## 11. Implementation Roadmap

### Phase 1: Synthetic bootstrap (1 day)

1. Write `epistemic_classifier.py` with:
   - `extract_features(conclusion, af, combined_tag, args)` → 18-dim vector
   - `EpistemicClassifier` class wrapping sklearn GBT + conformal prediction
2. Generate synthetic training data from `business_expert.yaml`:
   - Sweep predicate subsets × BELIEF_MAP variations
   - Label with current `epistemic_status()` thresholds
3. Train GBT, calibrate with RAPS
4. Replace `combined.epistemic_status()` call in `argumentation.py`
5. All existing tests should still pass (primary_status = argmax should match thresholds for clean cases)

### Phase 2: Expert calibration (1-2 weeks)

1. Create 200 scenario cards from diverse KBs
2. Expert annotation (3 annotators, compute inter-annotator agreement)
3. Replace synthetic calibration set with expert set
4. Evaluate: coverage rate, average set size, stratified coverage

### Phase 3: Online calibration (ongoing)

1. Instrument ContestationManager to log (features, user_action) pairs
2. Periodically update calibration quantile q̂ from user feedback
3. Monitor coverage drift → trigger recalibration when coverage drops

---

## 12. Key References

### Conformal Prediction

- **Vovk, V., Gammerman, A. & Shafer, G.** *Algorithmic Learning in a Random World.* Springer, 2005. — The foundational text. Distribution-free coverage guarantees.

- **Romano, Y., Sesia, M. & Candès, E.** "Classification with Valid and Adaptive Coverage." *NeurIPS 2020*. — Adaptive Prediction Sets (APS). Our starting point.

- **Angelopoulos, A.N., Bates, S., Malik, J. & Jordan, M.I.** "Uncertainty Sets for Image Classifiers using Conformal Prediction." *ICLR 2021*. — RAPS. The specific variant we use.

- **Angelopoulos, A.N. & Bates, S.** "A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification." *Foundations and Trends in Machine Learning*, 2023. — Accessible tutorial covering all major variants.

### Already in Thesis References

- **Jøsang, A.** *Subjective Logic.* Springer, 2016. — Ch. 5 covers multinomial opinions (the future Option A path).

- **Baroni, P. & Giacomin, M.** "On Principle-Based Evaluation of Extension-Based Argumentation Semantics." *AIJ* 171, 675-700, 2007. — No semantics satisfies all principles (I1 in our impossibility constraints).

- **Dvořák, W. & Dunne, P.E.** "Computational Problems in Formal Argumentation and Their Complexity." *Handbook of Formal Argumentation*, 2018. — Grounded=P, preferred=NP-complete (I5).

### Implementation

- **MAPIE** (Model Agnostic Prediction Interval Estimator): Python library for conformal prediction. `pip install mapie`. Supports multi-class conformal with APS/RAPS.

- **scikit-learn** `GradientBoostingClassifier`: The base classifier. No additional dependencies.

---

## 13. Summary

| Dimension | Current (thresholds) | Proposed (conformal UQ) |
|---|---|---|
| **Output** | Single status | Distribution + prediction set + primary status |
| **Calibration** | None — thresholds are arbitrary | Formal: P(Y ∈ C(x)) ≥ 1-α |
| **Magic numbers** | 5 floats (0.8, 0.1, 0.5, 0.3, 0.6) | 0 (learned from data) |
| **Training cost** | 0 | < 1 minute (synthetic), ~50 person-hours (expert) |
| **Inference cost** | ~0 | ~11 microseconds per conclusion |
| **LLM calls** | 0 additional | 0 additional |
| **Information loss** | High (continuous → single category) | Low (full distribution preserved) |
| **Edge case handling** | Arbitrary jumps at boundaries | Smooth — edge cases produce wider prediction sets |
| **P4 (graded native)** | Violates | Satisfies (distribution IS the graded output) |
| **P6 (structural provenance)** | Violates (numerical thresholds) | Partially satisfies (learned from structural features) |

**The key insight:** We're not replacing the threshold function with something fundamentally different. We're replacing a hand-specified 5-split decision tree with a learned 100-tree ensemble, then wrapping it in conformal prediction for calibrated uncertainty. Same structure, better boundaries, formal guarantees.
