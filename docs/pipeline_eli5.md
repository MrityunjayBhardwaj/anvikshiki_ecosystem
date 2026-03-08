# ELI5: How the Anvikshiki Engine Actually Works

> A plain-English walkthrough of every pipeline stage using the business strategy example.
> For each stage: **What** it does, **Why** it exists, and **How** it works.
>
> Based on a real test run: Llama-3.2-3B, `business_expert.yaml`, lightweight grounding path.

---

## The Setup

**The question:** "Does a company with positive unit economics always create value?"

**The knowledge base:** 11 business strategy rules extracted from academic sources (Harvard Business School, Goldratt, Christensen, Dunbar, etc.), plus 8 reasoning fallacy detectors.

**The model:** Llama-3.2-3B-Instruct-4bit running locally on MLX.

**The key insight before we begin:** The LLM is used for **translation** and **writing**. All actual reasoning is done by the symbolic engine. The LLM never decides what's true — it only converts English to predicates and predicates back to English.

---

## Stage 0: Accept the Request

### What
The user sends a question through the web app. The system authenticates them, loads their LLM settings, and decides which execution path to use.

### Why
Different users have different LLMs configured. A user running GPT-4 via API can handle the full 5-call ensemble grounding. A user running Llama-3.2-3B locally cannot — the model is too small to produce consistent structured output across 5 runs. The routing logic picks the right path automatically.

Three paths exist:

| Path | When | LLM Calls | Speed |
|------|------|-----------|-------|
| **A: Symbolic** | User supplies predicates directly | 1 (synthesis only) | ~1.8s |
| **B: Lightweight** | Small local model (3B-7B) | 2 (1 grounding + 1 synthesis) | ~3.8s |
| **C: Full N=5** | Large API model (GPT-4, Gemini) | 6-9 | ~30-120s |

### How
```
HTTP POST /api/queries/
├── JWT token decoded → user identified
├── User's LLM config loaded from DB:
│     provider: "openai/mlx-community/Llama-3.2-3B-Instruct-4bit"
│     api_base: "http://localhost:8080/v1"
│     is_small_model: true
├── dspy.LM() instantiated with these params
├── Route decision: is_small_model=true, no query_facts
│     → Path B: execute_lightweight_grounding()
└── QueryRecord created in DB with status="processing"
```

**Source:** `routers/queries.py:22-31`, `services/engine_service.py:23-34`

---

## Stage 1: Load the Knowledge Base

### What
Read the YAML file that contains the domain expertise. Parse it into a structured `KnowledgeStore` object with typed fields, validation, and relationships.

### Why
Think of the knowledge base as a textbook the engine reasons over. Without it, the engine is an empty shell — it has the *ability* to reason but nothing to reason *about*.

The KB provides five critical things:
1. **Vocabulary** — what facts can exist in this domain (e.g., `positive_unit_economics`, `value_creation`)
2. **Rules** — how facts chain together (e.g., IF `positive_unit_economics` THEN `value_creation`)
3. **Confidence scores** — how sure we are about each rule (existence: 0.95, formulation: 0.9)
4. **Scope conditions** — when each rule applies and when it *doesn't* (e.g., V01 excludes subsidized entities)
5. **Sources** — the academic papers backing each rule (e.g., Harvard Business School, Ries 2011)

This is what makes the engine domain-aware rather than a generic chatbot. A chatbot might hallucinate business advice. This engine can only derive conclusions traceable to specific rules with cited sources.

### How
```
yaml.safe_load(file) → KnowledgeStore(**data)

Output:
  domain_type: CRAFT
  11 vyaptis (rules):
    V01: IF positive_unit_economics → THEN value_creation
         (empirical, established, conf=0.95x0.9, sources: HBS, Ries)
    V04: IF organizational_growth → THEN coordination_overhead
         (empirical, established, conf=0.85x0.75, sources: Dunbar, Conway)
    V11: IF organizational_growth + coordination_overhead → THEN not_value_creation
         (empirical, hypothesis, conf=0.7x0.65)
         ^^^ This CONTRADICTS V01 — creates a formal conflict
    ...8 more rules

  8 hetvabhasas (fallacy detectors):
    H01: "The Revenue Vanity Trap" — inferring health from revenue alone
    H02: "The Framework Reification Error" — treating frameworks as reality
    ...6 more

  22 academic source references
```

The result is cached by `kb_id` so repeated queries skip parsing.

**Source:** `t2_compiler_v4.py:310-315`, `schema.py:134+`

---

## Stage 2: Build the Ontology Snippet

### What
Construct a "cheat sheet" of valid predicate names from the knowledge base. This text string tells the LLM *exactly* which vocabulary to use — and forbids it from inventing new terms.

### Why
LLMs are creative. Too creative. Ask one to "translate this question into structured predicates" and it might output:
- `has_good_business(acme)` — not in our vocabulary
- `is_sustainable(acme)` — not in our vocabulary
- `makes_money(acme)` — not in our vocabulary

None of these match any rule in the KB, so the engine couldn't derive anything. The ontology snippet constrains the LLM to *only* output predicates that actually exist:
- `positive_unit_economics(acme)` — matches V01's antecedent
- `value_creation(acme)` — matches V01's consequent

Think of it like giving someone a multiple-choice test instead of an essay — you constrain the answer space to valid options.

This is **Layer 1** of the five-layer grounding defense. It costs zero LLM calls — it's pure string construction.

### How
```
OntologySnippetBuilder iterates all 11 vyaptis and produces:

VALID PREDICATES — use ONLY these:

RULE V01: The Value Equation
  IF: positive_unit_economics
  THEN: value_creation
  SCOPE: commercial_enterprise
  EXCLUDES: subsidized_entity, network_effect_building_phase

RULE V04: The Organizational Entropy Principle
  IF: organizational_growth
  THEN: coordination_overhead
  EXCLUDES: active_structural_intervention

RULE V11: The Growth Trap
  IF: organizational_growth, coordination_overhead
  THEN: not_value_creation
  EXCLUDES: active_structural_intervention, small_team_direct_contact

...(8 more rules)

ALL VALID PREDICATE NAMES:
  - binding_constraint_identified(Entity)
  - calibration_accuracy(Entity)
  - coordination_overhead(Entity)
  - positive_unit_economics(Entity)
  - value_creation(Entity)
  - not_value_creation(Entity)
  ...(14 more)

OUTPUT FORMAT:
Return predicates as: predicate_name(entity)
Use ONLY predicate names from the list above.
```

**Source:** `grounding.py:98-143`

---

## Stage 3: LLM Grounding — Translate English to Predicates

### What
Send the user's question + the ontology snippet to the LLM. The LLM reads the question, looks at the valid predicates, and picks the ones that match.

**Input:** "Does a company with positive unit economics always create value?"

**Output:** `["positive_unit_economics(acme)", "value_creation(acme)"]`

The LLM recognized that "positive unit economics" and "create value" map to specific predicates in our vocabulary.

### Why
The symbolic engine speaks in predicates like `positive_unit_economics(acme)`. It cannot process English directly. This stage is the bridge between human language and machine reasoning.

**Why "lightweight" (1 call instead of 5)?** The full pipeline makes 5 parallel LLM calls at temperature=0.7, then takes the majority vote (ensemble consensus). This works great with large models like GPT-4 that produce consistent structured output. But small models (3B params) are too erratic — they produce different predicates each run, leading to empty consensus sets (0.0 confidence). A single call with chain-of-thought reasoning works better for small models.

### How
```
DSPy Signature: GroundQuery
  Inputs:
    query:            "Does a company with positive unit economics always create value?"
    ontology_snippet: [the ~60 line vocabulary list from Stage 2]
    domain_type:      "CRAFT"

  Outputs:
    reasoning:         Step-by-step analysis (chain-of-thought)
    predicates:        ["positive_unit_economics(acme)", "value_creation(acme)"]
    relevant_vyaptis:  ["V01"]
```

DSPy's `ChainOfThought` wrapper constructs a prompt from this signature, sends it to the LLM via HTTP, and parses the structured response.

The extracted predicates are packaged as "query facts" with metadata:
```
[
  {"predicate": "positive_unit_economics(acme)", "confidence": 0.7, "sources": ["lightweight_grounding"]},
  {"predicate": "value_creation(acme)",          "confidence": 0.7, "sources": ["lightweight_grounding"]}
]
```

Confidence is fixed at 0.7 for lightweight grounding (no ensemble consensus to boost it).

**Source:** `grounding.py:46-66`, `engine_service.py:240-291`

---

## Stage 4: T2 Compilation — Build the Argumentation Framework

### What
Take the knowledge base rules + query facts and construct a formal "argumentation framework" — a graph where nodes are arguments and edges are attacks between them.

Think of it as building a courtroom:
- Each **argument** is a lawyer making a case for some conclusion
- Each **attack** is one lawyer objecting to another's argument
- The **judge** (grounded semantics, Stage 5) decides who wins

### Why
This is the core of the neurosymbolic approach. Instead of asking an LLM "is this true?", we build a formal debate and let logic resolve it.

LLMs can't reliably handle conflicting evidence. If you tell GPT-4 "Acme has good unit economics" AND "Acme is growing too fast and coordination costs are eating into value", it might randomly pick one or hedge without formal justification.

The argumentation framework resolves conflicts formally:
1. Each piece of evidence becomes a structured argument with a **provenance tag** (belief score, source, evidence type)
2. Contradictions become explicit **attacks** (A attacks B)
3. The ASPIC+ **defeat relation** determines which attacks succeed based on evidence strength, not LLM whims
4. **Grounded semantics** finds the unique minimal defensible position

The result is *traceable, auditable reasoning*. You can ask "why was value_creation accepted?" and get a proof tree, not "the LLM said so."

### How — Three Sub-steps

**Step 4a: Create premise arguments from query facts**

Each query fact becomes a "premise argument" — the bedrock that all reasoning builds on.
```
A0000: "positive_unit_economics(acme)"
  Type: premise (no rule — this is a base fact)
  Tag:  belief=0.70, disbelief=0.00, uncertainty=0.30
  Pramana: PRATYAKSA (direct evidence — strongest type, value=4)
  Strength: 0.70 × 1.0 × 1.0 = 0.70

A0001: "value_creation(acme)"
  Type: premise (base fact)
  Tag:  belief=0.70, disbelief=0.00, uncertainty=0.30
  Pramana: PRATYAKSA
  Strength: 0.70
```

**Step 4b: Forward-chain through rules (vyaptis)**

The compiler checks every rule: "are ALL antecedents available in the current argument set?"

```
V01: IF positive_unit_economics → THEN value_creation
  positive_unit_economics available? YES (A0000)
  → Fire rule → Create new argument:

A0002: "value_creation(acme)"
  Via rule: V01 ("The Value Equation")
  Sub-arguments: (A0000)
  Tag: tensor(V01_rule_tag, A0000_tag)
    V01 rule tag:  belief=0.95, pramana=ANUMANA, trust=0.855
    Combined via semiring tensor (⊗):
      belief = 0.95 × 0.70 = 0.665  (attenuated through chain)
      pramana = min(ANUMANA, PRATYAKSA) = ANUMANA  (weakest link)
      sources = {src_hbs_unit_economics, src_ries_2011, lightweight_grounding}

V08: IF value_creation + resource_allocation → THEN long_term_value
  resource_allocation available? NO
  → SKIP (not all antecedents present)

V04, V05, V11: need organizational_growth → not in facts → SKIP
```

The **tensor** operation (⊗) is key: when you chain evidence through a rule, the result *attenuates*. Belief gets multiplied (never increases), the pramana type takes the minimum (weakest link), and the derivation depth increases. A conclusion derived through 3 rules from a 0.7-confidence fact will be much weaker than the original fact.

**Step 4c: Derive attacks**

Three attack types, each mapped to a Nyaya fallacy category:

| Attack Type | Sanskrit | When It Fires |
|-------------|----------|---------------|
| Rebutting | viruddha | Two arguments reach contradictory conclusions (X vs not_X) |
| Undercutting | savyabhicara | A fact matches a rule's scope_exclusion |
| Undermining | asiddha | A premise's evidence has decayed below threshold |

In this test run:
- No `not_value_creation` argument exists → no rebutting attacks
- No scope exclusions triggered → no undercutting attacks
- All decay factors = 1.0 → no undermining attacks

```
Result: 3 arguments, 0 attacks

(With organizational_growth in the facts, V04 and V11 would fire,
 creating not_value_creation — which REBUTS value_creation.
 Then the engine would have to resolve the conflict.)
```

The process repeats (fixpoint iteration) until no new arguments can be derived.

**Source:** `t2_compiler_v4.py:92-145`, `t2_compiler_v4.py:148-206`, `t2_compiler_v4.py:209-307`

> **For readers who want to see the formal machinery:**
>
> When the engine "fires a rule," it's constructing an ASPIC+ argument. Here's the formal representation of the unit economics example:
>
> ```
> A0001: positive_unit_economics     [premise, pramana=PRATYAKSA, b=0.85]
> A0002: growing_market              [premise, pramana=PRATYAKSA, b=0.80]
> A0003: value_creation              [via V01: pos_unit_eco ⇒ value_creation]
>         tag = A0001.tag ⊗ V01.tag
>             = (b=0.85, u=0.15) ⊗ (b=0.95, u=0.05)
>             = (b=0.808, u=0.193)    [belief attenuates through chain]
>
> A0004: long_term_value             [via V08: value_creation ∧ growing_market ⇒ long_term_value]
>         tag = A0003.tag ⊗ A0002.tag ⊗ V08.tag
>             = (b=0.808) × (b=0.80) × (b=0.60) ≈ b=0.388  [each step weakens chain]
>         pramana = min(PRATYAKSA, PRATYAKSA, ANUMANA) = ANUMANA  [weakest link]
> ```
>
> When `subsidized_entity` is present, the engine creates:
>
> ```
> A0005: _undercut_V01              [scope violation]
>         tag = (b=1.0, pramana=PRATYAKSA)
>
> Attack(attacker=A0005, target=A0003, type="undercutting", hetvabhasa="savyabhicara")
> → A0003 labeled OUT → A0004 loses its support → also OUT
> ```
>
> This is not LLM reasoning. It is a deterministic symbolic computation over
> a mathematically-defined argumentation graph. The outcome is provable
> given the inputs — the same query will always produce the same labels.
>
> *Full formal treatment: [thesis_v3.md §6.1](../theory/thesis_v3.md)*

---

## Stage 5: Grounded Semantics — The Judge Decides

### What
Compute the "grounded extension" — the unique, minimal set of arguments that can be rationally accepted given all the attacks. Each argument gets labeled:

| Label | Meaning |
|-------|---------|
| **IN** | Accepted — all its attackers are defeated |
| **OUT** | Defeated — at least one attacker is accepted and wins the fight |
| **UNDECIDED** | Not enough information to accept or defeat |

### Why
This is where conflicts get resolved formally. Suppose `value_creation(acme)` and `not_value_creation(acme)` both exist (as they would with `organizational_growth` in the facts). Which one wins?

The grounded semantics algorithm doesn't guess. It uses the **ASPIC+ defeat relation**:

1. **Pramana ordering first:** PRATYAKSA(4) > ANUMANA(3) > SABDA(2) > UPAMANA(1). A higher evidence type *always* wins, regardless of belief score. Direct observation beats inference. Inference beats testimony.

2. **If same pramana level, compare strength:** `strength = belief × trust × decay`. The stronger argument wins.

3. **Special cases:**
   - Strict arguments (definitional/structural rules) can *never* be rebutted
   - Undercutting attacks *always* succeed (they attack the rule itself, not the conclusion)

This is the **Nyaya badhita principle**: a higher epistemic channel trumps a lower one, period.

### How
```
Algorithm (Wu, Caminada & Gabbay 2009):
  1. Find unattacked arguments → label IN
  2. Find arguments attacked by IN → check if defeat succeeds → if yes, label OUT
  3. Find arguments with ALL attackers OUT → label IN (defended)
  4. Repeat until no changes (fixpoint)
  5. Everything remaining → UNDECIDED

In this test:
  Iteration 1:
    A0000: no attackers → IN
    A0001: no attackers → IN
    A0002: no attackers → IN
  Fixpoint reached. Done.

Result: {A0000: IN, A0001: IN, A0002: IN}
Complexity: O(|arguments| × |attacks|) — polynomial, always terminates.
```

The algorithm is the same one used for cooperative inquiry (**Vada** mode). The engine also supports:
- **Jalpa** (preferred semantics) — finds ALL defensible positions, even aggressive ones. NP-hard, for offline stress-testing.
- **Vitanda** (stable semantics) — finds every possible vulnerability. coNP-hard, for formal audits.

**Source:** `argumentation.py:53-109` (compute_grounded), `contestation.py:45-81` (vada)

---

## Stage 6: Epistemic Status — How Confident Are We?

### What
For each conclusion, classify how confident we are based on the provenance tag values. Five levels:

| Status | Condition | Plain English |
|--------|-----------|---------------|
| **ESTABLISHED** | belief > 0.8, uncertainty <= 0.1 | "We're very confident." |
| **HYPOTHESIS** | belief > 0.5, uncertainty < 0.3 | "Evidence suggests this, but not certain." |
| **PROVISIONAL** | belief > 0.5 (doesn't meet above) | "Some evidence supports this." |
| **OPEN** | uncertainty > 0.6 | "Not enough evidence either way." |
| **CONTESTED** | disbelief > 0.4, belief > 0.3 | "Significant evidence both for AND against." |

### Why
A chatbot says: "Yes, Acme has a sustainable business model."

This engine says: "The evidence *suggests* value creation (PROVISIONAL, belief=0.70) but the grounding confidence is moderate (0.70). The conclusion should be treated as a working hypothesis, not an established fact."

The epistemic status drives the final response language:
- ESTABLISHED → stated as fact
- HYPOTHESIS → "evidence suggests..."
- PROVISIONAL → "some evidence indicates..."
- CONTESTED → "however, there is counter-evidence..."
- OPEN → "this remains an open question..."

This is **calibrated communication** — matching your language to your actual evidence.

### Why not just use a single confidence number? Because `belief=0.7` means very different things depending on context. A conclusion with `belief=0.7, disbelief=0.0, uncertainty=0.3` (PROVISIONAL — we lack evidence) is fundamentally different from `belief=0.7, disbelief=0.3, uncertainty=0.0` (borderline CONTESTED — there's active counter-evidence). The epistemic status captures this distinction.

### How
```
For each conclusion, combine tags of accepted arguments via ⊕ (oplus):

positive_unit_economics(acme):
  Argument A0000: b=0.70, d=0.00, u=0.30
  Check: b=0.70 > 0.5 ✓, u=0.30 >= 0.3 ✗ (misses HYPOTHESIS by 0.01)
  → PROVISIONAL

value_creation(acme):
  Arguments A0001 (b=0.70) and A0002 (b=0.665) — both accepted
  Combined via oplus (⊕): accrual of independent evidence
  Check: b > 0.5 ✓, u >= 0.3 ✗
  → PROVISIONAL
```

The **oplus** operation (⊕) is for parallel composition — when multiple independent arguments support the same conclusion, their evidence *accumulates*. Two moderate arguments are stronger than one.

**Source:** `schema_v4.py:154-169`, `argumentation.py:154-196`

---

## Stage 7: Provenance — Where Did This Come From?

### What
Extract the full audit trail for each conclusion: which sources contributed, what type of evidence, how long the inference chain is, how fresh the data is.

### Why
This is what makes the engine **auditable**. When the engine says "Acme shows value creation (PROVISIONAL)", a user can ask "where does that come from?" and get:

```
Sources:      src_hbs_unit_economics (Harvard Business School),
              src_ries_2011 (The Lean Startup),
              lightweight_grounding
Rule:         V01 "The Value Equation" (empirical, confidence 0.855)
Evidence:     PRATYAKSA (direct observation)
Chain depth:  0 (base fact) or 1 (one inference step)
Trust:        1.0 (full source authority)
Freshness:    1.0 (no temporal decay)
```

Compare this to a chatbot that says "Acme has a sustainable business model" with zero traceability. This engine gives you a paper trail you can verify.

### How
```
For each conclusion, extract from its ProvenanceTag:

positive_unit_economics(acme):
  sources:          ["lightweight_grounding"]
  pramana:          PRATYAKSA (direct evidence — strongest)
  derivation_depth: 0 (base fact)
  trust:            1.0
  decay:            1.0

value_creation(acme):
  sources:          ["lightweight_grounding"]   ← from premise argument
  (or via V01):     ["lightweight_grounding", "src_hbs_unit_economics", "src_ries_2011"]
  pramana:          PRATYAKSA (premise) or ANUMANA (inferred via V01)
  derivation_depth: 0 (premise) or 1 (derived)
  trust:            1.0 (premise) or 0.855 (V01's confidence)
  decay:            1.0
```

**Source:** `engine_service.py:175-184`

---

## Stage 8: Uncertainty Decomposition — Three Kinds of "Not Sure"

### What
Break uncertainty into three independent components. Each tells you something different about *why* we're uncertain:

| Component | Source | Meaning | What To Do |
|-----------|--------|---------|------------|
| **Epistemic** | belief + uncertainty from tag | "We lack evidence" | Collect more data |
| **Aleatoric** | disbelief from tag | "The domain itself disagrees" | Build for variance |
| **Inference** | grounding confidence + decay + depth | "Our reasoning chain might be flawed" | Verify assumptions |

### Why
Not all uncertainty is the same. "I'm not sure" could mean three very different things:

- **Epistemic:** "We just haven't gathered enough data yet." → Solution: go collect more evidence. This uncertainty is *reducible*.
- **Aleatoric:** "Experts genuinely disagree about this." → Solution: there isn't one — this is inherent domain variability. Irreducible.
- **Inference:** "The LLM might have grounded the query wrong, or the rule chain is too long." → Solution: verify the grounding, check the rules, or use a better model.

A single "70% confident" number hides all of this. The three-way decomposition tells users *what to do next*.

### How
```
compute_uncertainty_v4(tag, grounding_confidence=0.7, conclusion, status)

For positive_unit_economics(acme):

  Epistemic:
    belief: 0.70, uncertainty: 0.30
    → "moderate evidence — working hypothesis"

  Aleatoric:
    disbelief: 0.0
    → "low domain-level contestation"
    (No one is arguing against this — there's just not enough evidence)

  Inference:
    grounding_confidence: 0.70 (lightweight grounding, no ensemble)
    decay_factor: 1.0 (fresh)
    derivation_depth: 0 (base fact)
    → "grounding=0.70, freshness=1.00, chain_depth=0"

  Total confidence: strength = belief × trust × decay = 0.70 × 1.0 × 1.0 = 0.70
```

**Source:** `uncertainty.py:7-57`

---

## Stage 9: Fallacy Detection — What Went Wrong?

### What
Scan the argumentation framework for **defeated arguments** — conclusions that were attacked by a winning argument. Each defeat is classified by its Nyaya fallacy type (hetvabhasa):

| Fallacy | Sanskrit | Meaning | Example |
|---------|----------|---------|---------|
| Unestablished | asiddha | The premise is not proven | Stale evidence (decay below threshold) |
| Deviating | savyabhicara | The rule has scope violations | V01 applied to a subsidized entity |
| Contradictory | viruddha | Two conclusions contradict | value_creation vs not_value_creation |

### Why
A chatbot might silently ignore contradictory evidence. This engine explicitly flags every reasoning flaw with a specific classification and corrective action.

Example (if organizational_growth were in the facts):
> "WARNING: value_creation(acme) is CONTESTED because V11 ('The Growth Trap') derives not_value_creation(acme). This is a **viruddha** (contradictory) hetvabhasa. The conflict is resolved in favor of value_creation based on pramana ordering, but the counter-evidence should not be ignored."

This is the engine being honest about the limits of its reasoning.

### How
```
For each attack in the framework:
  If the attacker is labeled IN (accepted):
    If the target's conclusion is user-facing (not internal like _undercut_*):
      → Record as a violation with its hetvabhasa type

In this test: 0 attacks exist → 0 violations

With organizational_growth in the facts, you'd see:
  VIOLATION: viruddha (rebutting)
    Attacker: A0005 "not_value_creation(acme)" (via V11)
    Target:   A0002 "value_creation(acme)" (via V01)
    → The engine resolved this based on strength comparison,
      but flags it so the user knows a conflict exists.
```

**Source:** `engine_service.py:199-211`

---

## Stage 10: LLM Synthesis — Write the Final Answer

### What
Feed all the structured results from Stages 4-9 into the LLM and ask it to compose a natural language response. The response must be:
- **Calibrated** — hedge HYPOTHESIS/PROVISIONAL claims, flag CONTESTED ones
- **Sourced** — cite the academic papers backing each claim
- **Honest** — mention what's open or contested
- **Concise** — useful, not a wall of caveats

### Why
Humans don't want to read raw argumentation frameworks. They want a clear, well-written answer. But the answer must be **faithful** to the formal reasoning — no adding claims the AF doesn't support, no ignoring defeats, no overconfident language for PROVISIONAL conclusions.

This is the **only** stage where the LLM generates free text (in the lightweight path). Everything before this was deterministic symbolic computation — no hallucination possible. The LLM here is a *writer*, not a *reasoner*. It composes prose from structured data. It *cannot* hallucinate claims because it's constrained by the AF output fed as input.

### How

**The inputs to the LLM:**
```
accepted_arguments:
  "- value_creation(acme): provisional (belief=0.70, sources=['lightweight_grounding'])
   - positive_unit_economics(acme): provisional (belief=0.70, sources=['lightweight_grounding'])"

defeated_arguments:
  "No defeated conclusions."

uncertainty_report:
  "- value_creation(acme): confidence=0.70, epistemic=provisional
   - positive_unit_economics(acme): confidence=0.70, epistemic=provisional"

retrieved_prose:
  "A company with positive unit economics demonstrates value creation...
   However, organizational growth can lead to coordination overhead..."
```

**Quality control — `dspy.Refine(N=3)`:**

The LLM generates up to 3 candidate responses. Each is scored by a reward function:

| Criterion | Weight | Check |
|-----------|--------|-------|
| Substantive (> 50 chars) | 0.20 | Not a one-liner |
| Sources cited | 0.15 | At least 1 source |
| Epistemic hedging | 0.20 | Contains "hypothesis", "provisional", etc. |
| Hetvabhasa warnings | 0.15 | Mentions caveats when violations exist |
| No overconfidence | 0.15 | Doesn't say "certainly" |
| Extension quality | 0.15 | Has accepted conclusions |

The candidate scoring >= 0.5 (threshold) is returned. If none meets the bar, the best one is used anyway.

**The DSPy signature:**
```
class SynthesizeResponse(dspy.Signature):
    query:               str   → the user's question
    accepted_arguments:  str   → formatted accepted conclusions
    defeated_arguments:  str   → formatted defeated conclusions
    uncertainty_report:  str   → structured uncertainty data
    retrieved_prose:     str   → relevant text chunks

    response:            str   → calibrated natural language answer
    sources_cited:       list  → source IDs used in the response
```

**Source:** `engine_v4.py:16-34`, `engine_v4.py:36-74`, `engine_service.py:213-244`

---

## Stage 11: Assemble Response and Save

### What
Combine all outputs from Stages 3-10 into a single JSON response, update the database record from "processing" to "completed", and return to the client.

### Why
The API contract requires all reasoning artifacts in a single response — the natural language answer, the sources, the uncertainty decomposition, the provenance, the violations, the contestation analysis, the grounding confidence, and the extension size. The database record enables query history and the frontend's polling mechanism (for async jalpa/vitanda queries that may take 30+ seconds).

### How
```json
{
  "id": "1ac4dd7b-...",
  "status": "completed",

  "response": "Please note that this response is based on provisional
               beliefs and should be taken as a hypothetical scenario.",
  "sources": ["lightweight_grounding"],

  "uncertainty": {
    "value_creation(acme)": {
      "epistemic":  {"status": "provisional", "belief": 0.7, "uncertainty": 0.3},
      "aleatoric":  {"disbelief": 0.0},
      "inference":  {"grounding_confidence": 0.7, "decay_factor": 1.0, "derivation_depth": 0},
      "total_confidence": 0.7
    }
  },
  "provenance": {
    "value_creation(acme)": {
      "sources": ["lightweight_grounding"],
      "pramana": "PRATYAKSA",
      "derivation_depth": 0, "trust": 1.0, "decay": 1.0
    }
  },
  "violations": [],
  "grounding_confidence": 0.7,
  "extension_size": 2,
  "contestation": {"mode": "vada", "open_questions": [], "suggested_evidence": []},
  "duration_ms": 3803
}
```

**Source:** `routers/queries.py:73-86`

---

## Summary

```
  QUERY: "Does a company with positive unit economics always create value?"
     │
     │  Stage 0:  Accept request, pick execution path          (0 LLM calls)
     │  Stage 1:  Load knowledge base from YAML                (0 LLM calls)
     │  Stage 2:  Build constrained vocabulary for LLM         (0 LLM calls)
     │  Stage 3:  LLM translates English → predicates          (1 LLM call)
     │  Stage 4:  Build arguments, fire rules, derive attacks  (0 LLM calls)
     │  Stage 5:  Judge decides: IN / OUT / UNDECIDED           (0 LLM calls)
     │  Stage 6:  Classify confidence level per conclusion     (0 LLM calls)
     │  Stage 7:  Extract source audit trail                   (0 LLM calls)
     │  Stage 8:  Decompose uncertainty into 3 types           (0 LLM calls)
     │  Stage 9:  Detect reasoning fallacies                   (0 LLM calls)
     │  Stage 10: LLM writes calibrated response               (1 LLM call)
     │  Stage 11: Save results, return JSON                    (0 LLM calls)
     │
     ▼
  TOTAL: 2 LLM calls. 10 of 12 stages are pure symbolic computation.
  Duration: ~3.8 seconds end-to-end.
```

**The key insight:** the LLM is used for **translation** (English → predicates) and **composition** (data → prose). It is never used for **reasoning**. All reasoning is done by the symbolic engine — deterministic, auditable, and grounded in formal argumentation theory (ASPIC+, grounded semantics, provenance semirings, Nyaya epistemology).

---

## Appendix: Rigorous Mapping of Each Stage to the Thesis

> How each pipeline step and its implementation maps to the claims, formalisms, and design decisions stated in `thesis_v4_r1.md` — *The Ānvīkṣikī Engine (v4): From Nyāya Epistemology to Neurosymbolic Argumentation*.

---

### Stage 0 → §1 "Why Bother?" + §1.3 Constraints

**Thesis claim (§1.1, lines 87–93):** LLMs cannot "chain domain-specific rules, check whether the reasoning violates known fallacy patterns, verify that the claims are grounded in cited evidence, or decompose its uncertainty." RAG "cannot derive consequences, check prerequisites, detect scope violations, or prove that a conclusion follows from premises."

**Implementation:** Stage 0 routes the query to one of three execution paths. The routing itself embodies §1.3's constraints:

| Constraint (§1.3) | How Stage 0 satisfies it |
|---|---|
| **Model-agnostic** | `dspy.LM()` instantiated from user's config — any provider, any model. "No dependency on specific LLM capabilities." |
| **Polynomial termination** | All paths lead to Datalog fixpoint (Stage 5), which is P-complete. No path permits unbounded LLM iteration. |
| **Practically deployable** | Three paths trade cost vs. quality: symbolic (1 call, ~1.8s), lightweight (2 calls, ~3.8s), full N=5 (6-9 calls, ~30-120s). |

**Thesis claim (§8.2, line 855):** "LLM role: Only grounding (NL→predicates) and synthesis (results→NL) — everything else is symbolic."

**Implementation:** The path selection enforces this boundary. Even the most expensive path (C: full N=5) uses the LLM only for grounding and synthesis. Stages 4-9 are purely symbolic regardless of path.

**Source:** `routers/queries.py:22-31` (routing), §1.2 objectives, §1.3 constraints, §8.2 comparison table.

---

### Stage 1 → §2.3 Vyāpti/Hetvābhāsa/Pañcāvayava + §2.4 Compilation Targets + §9.5 Data Structures

**Thesis claim (§2.3, lines 162–168):** "Vyāpti (invariable concomitance): The production rule… Each vyāpti has a causal status (structural, regulatory, empirical, definitional), scope conditions, confidence ratings, evidence quality markers, and decay characteristics. Vyāptis are the executable rules of the engine."

**Implementation:** The YAML knowledge base (`business_expert.yaml`) is parsed into a `KnowledgeStore` containing exactly these fields. Each vyāpti carries:
- `causal_status` → maps to `PramanaType` via `_build_rule_tag()` (§9.7, line 1530): `DEFINITIONAL → PRATYAKSA`, `EMPIRICAL → ANUMANA`, `REGULATORY → SABDA`
- `scope_conditions` / `scope_exclusions` → feed Stage 4c undercutting attacks (§7.2: savyabhicāra → undercutting)
- `confidence.existence × confidence.formulation` → becomes `trust_score` in the provenance tag (§9.7, line 1549)
- `decay_risk` + `last_verified` → becomes `decay_factor` via exponential decay with half-life=365 days (§9.7, lines 1552-1557)

**Thesis claim (§2.3, lines 170–180):** Hetvābhāsa = "The constraint. A systematic catalog of ways inference can fail." Five types from Gautama's *Nyāya Sūtra*.

**Implementation:** The 8 hetvābhāsas in `business_expert.yaml` (H01–H08) are loaded but, crucially, they are NOT used for keyword matching. Per §7.4 (line 795): "Keyword hetvābhāsa detection ELIMINATED — hetvābhāsas ARE the defeat relation." The KB's hetvābhāsa entries serve as documentation; the actual detection happens structurally in Stage 4c.

**Thesis claim (§2.4, lines 196–200):** "T2 (Logic Engine): Executable inference over formalized domain rules — *this is what this thesis redesigns*."

**Implementation:** `load_knowledge_store()` in `t2_compiler_v4.py:310-315` is the T2 compiler entry point. It parses the verified architecture (YAML) into the data structures specified in §9.5 (lines 1011–1162).

**Source:** `t2_compiler_v4.py:310-315`, `schema_v4.py:1-227`, §2.3, §2.4, §9.5, §9.7.

---

### Stage 2 → §5.4 (Grounding Limitation) + Grounding Defense Layer 1

**Thesis claim (§5.4, lines 517–531):** "Li et al. (2024) benchmarked LLMs on argumentation computation — they perform poorly on extension computation, confirming the need for symbolic argumentation engines." And: "None uses argumentation as the *core inference engine* for a compiled knowledge base."

**Implementation:** The ontology snippet is the architectural response to this finding. Since LLMs cannot reliably construct argumentation frameworks, we confine them to a constrained translation task: given a fixed vocabulary of valid predicates, pick the ones matching the query. The snippet is §6.3 Layer 1 from thesis_v2.md (ontology-constrained prompting, Strategy 4 from §6.2), which thesis2_v1 inherits unchanged: "Grounding (NL → predicates) — unchanged from v3" (§9.8, line 1580).

**Thesis claim (§8.2, line 855):** "LLM role: Only grounding (NL→predicates) and synthesis (results→NL)."

**Implementation:** The ontology snippet constrains the grounding call so that the LLM's output space is limited to predicates that exist in the KB. This is how the architecture enforces the boundary: the LLM translates, it does not reason. It cannot invent predicates because the snippet provides a closed vocabulary.

**Source:** `grounding.py:98-143` (OntologySnippetBuilder), §5.4, §8.2.

---

### Stage 3 → §8.2 "The Fundamental Issue" + §1.4 Usage

**Thesis claim (§8.2, lines 862–864):** "The full architecture confines the LLM to what it's actually good at: natural language understanding (grounding: NL → predicates) and natural language generation (synthesis: results → calibrated response). Everything between — argument construction, attack computation, extension evaluation, provenance tracking — is deterministic and symbolic."

**Implementation:** Stage 3 is the first LLM call. It implements exactly the grounding half of this claim. The `GroundQuery` DSPy signature (§6.4 code in thesis_v2.md, `grounding.py:46-65`) takes `query + ontology_snippet + domain_type` and outputs `predicates + relevant_vyaptis`.

**Thesis claim (§3.1, line 221):** "Asking an LLM 'what's the probability that concentrated ownership enables long-horizon investment?' produces a confident-sounding number with no epistemic grounding."

**Implementation:** Stage 3 does NOT ask the LLM for probabilities. It asks for predicate selection — a classification task, not a calibration task. The confidence is fixed at 0.7 for lightweight grounding (or computed from ensemble consensus for full N=5). The system never relies on the LLM's self-assessed confidence. This directly addresses §3.1's critique of Bayesian approaches.

**Source:** `grounding.py:46-66`, `engine_service.py:240-291`, §8.2, §3.1.

---

### Stage 4 → §6.2 ASPIC+ + §7.2 Nyāya-to-ASPIC+ Mapping + §7.3 Provenance Tag + §9.7 T2 Compiler

This is the thesis's core contribution. Stage 4 implements the unified architecture of §7.

**Step 4a: Premise arguments** → §7.2 mapping table, row "Pratyakṣa"

**Thesis (§7.2, line 729):** "Pratyakṣa (direct evidence) → Necessary premise Kₙ: Ground fact from data/observation."

**Implementation:** Each query fact becomes an `Argument` with `pramana_type=PRATYAKSA`, `top_rule=None`, `is_strict=True`. This IS the Nyāya-to-ASPIC+ mapping: direct evidence is a necessary premise that cannot be attacked (strict). Code: `compile_t2()` Step 1 (§9.7, lines 1365–1388).

**Step 4b: Rule-based arguments** → §6.2 ASPIC+ definition + §7.3 Provenance Tag

**Thesis (§6.2, lines 637–640):** "If A₁, ..., Aₙ are arguments for φ₁, ..., φₙ and there is a rule φ₁, ..., φₙ → ψ (strict) or φ₁, ..., φₙ ⇒ ψ (defeasible), then the tree with root ψ and children A₁, ..., Aₙ is an argument for ψ."

**Implementation:** `compile_t2()` Step 2 (§9.7, lines 1390–1437) checks each vyāpti: are all antecedents available? If yes, build a rule-based argument with `sub_arguments` pointing to the antecedent arguments. This is the ASPIC+ argument construction rule verbatim.

**Thesis (§7.3, lines 770–777):** "⊗ (sequential composition): belief_AB = belief_A × belief_B, trust_AB = min(trust_A, trust_B), pramana_AB = lower_pramana(A, B)."

**Implementation:** `ProvenanceTag.tensor()` in `schema_v4.py:42-56` implements exactly this. When V01 fires with antecedent A0000 (belief=0.70), the argument tag is `tensor(V01_rule_tag, A0000_tag)` → belief = 0.95 × 0.70 = 0.665, pramana = min(ANUMANA, PRATYAKSA) = ANUMANA. The ELI5 trace shows this computation.

**Step 4c: Derive attacks** → §7.2 mapping table, rows "Asiddha/Savyabhicāra/Viruddha"

Three attack types, each a direct implementation of the Nyāya-to-ASPIC+ mapping:

| Thesis §7.2 | Attack Code (§9.7) | Implementation |
|---|---|---|
| "Viruddha (contradictory) → Rebutting attack: Counter-argument for contrary conclusion" (line 735) | Step 3a (lines 1441–1461) | Find X and not_X in conclusions → mutual rebutting attacks |
| "Savyabhicāra (inconclusive) → Undercutting attack: Attack on defeasible rule applicability" (line 734) | Step 3b (lines 1463–1493) | If `scope_exclusion` predicate is established → create undercutting argument `_undercut_{rule_id}` |
| "Asiddha (unestablished) → Undermining attack: Attack on ordinary premise" (line 733) | Step 3c (lines 1495–1516) | If `decay_factor < 0.3` → create undermining argument `_stale_{arg_id}` |

**Thesis claim (§7.4, line 795):** "Keyword hetvābhāsa detection ELIMINATED."

**Implementation verified:** No string matching on hetvābhāsa detection signatures anywhere in the v4 engine. The three attack derivation rules in `t2_compiler_v4.py:209-307` are purely structural — they check predicate contradictions, scope exclusion sets, and decay thresholds. This is the thesis's central architectural improvement over v3.

**Thesis claim (§6.4, lines 674–688):** "Diller et al. (KR 2025) show how to compute ASPIC+ argumentation using Datalog... Argument construction: Represent rules as Datalog facts. Arguments are derived facts."

**Implementation:** The forward-chaining fixpoint loop in `t2_compiler_v4.py` (Step 4, §9.7 line 1518: "Re-run Step 2 with newly derived conclusions until fixpoint") is Datalog-style semi-naive evaluation applied to ASPIC+ argument construction — exactly the Diller et al. approach.

**Source:** `t2_compiler_v4.py:92-307`, `schema_v4.py:42-100`, §6.2, §7.2, §7.3, §9.5, §9.7.

---

### Stage 5 → §5.2 Dung Semantics + §6.4 Datalog Computation + §8.6 Debate Protocols

**Thesis claim (§5.2, lines 468–478):** "Dung (1995) introduced abstract argumentation frameworks. Grounded semantics: P-complete. Preferred: NP-complete. Stable: coNP-complete."

**Implementation:** `compute_grounded()` in `argumentation.py:53-109` implements grounded semantics — the polynomial (P-complete) option. This satisfies §1.3's "polynomial termination" constraint.

**Thesis (§6.4, lines 685–687):** "Wu, Caminada & Gabbay (2009) showed that grounded semantics can be computed by iterative propagation — starting from unattacked arguments (IN), labeling their targets (OUT), and propagating until fixpoint."

**Implementation:** The algorithm in `argumentation.py:53-109` follows this exact procedure. The code comment references "Wu, Caminada & Gabbay 2009." The fixpoint loop iterates until `changed = False` — the Datalog termination condition.

**Thesis (§6.2, lines 651–655):** "ASPIC+ satisfies: Closure, Direct consistency, Indirect consistency, Rationality postulates — no two accepted arguments attack each other."

**Implementation:** The grounded extension computed by Stage 5 satisfies these by construction. This is why §7.4 (line 793) can eliminate the cellular sheaf: "Argumentation extensions are globally consistent by construction (Caminada & Amgoud 2007). No separate consistency layer needed."

**Thesis (§7.2, lines 743–745):** "Vāda → Grounded semantics. Jalpa → Preferred semantics. Vitaṇḍā → Stable semantics."

**Implementation:** The engine supports all three:
- `compute_grounded()` → vāda (default, polynomial, used for routine queries)
- `compute_preferred()` → jalpa (NP-hard, for stress-testing — `argumentation.py:200-242`)
- `compute_stable()` → vitaṇḍā (coNP-hard, for formal audit — `argumentation.py:310-327`)

**Thesis (§8.6, line 942):** "The cost hierarchy matches the use case hierarchy: routine queries are cheap, deep analysis is expensive, and exhaustive audit is most expensive."

**Implementation:** The `contestation_mode` parameter in the query request selects the semantics. This is the thesis's three-protocol contestation system (§8.6) made operational.

**The defeat relation** → §7.2, row "Bādhita"

**Thesis (§7.2, lines 737–738):** "Bādhita (sublated by higher pramāṇa) → Preference-based defeat: Higher-ranked pramāṇa overrides lower."

**Implementation:** `_defeats()` in `argumentation.py:111-150` checks pramāṇa ordering first (`PRATYAKSA > ANUMANA > SABDA > UPAMANA`), then falls back to tag strength comparison. This implements the Nyāya *badhita* principle: "a higher epistemic channel trumps a lower one, period." A PRATYAKSA argument always defeats an ANUMANA argument, regardless of belief scores.

**Source:** `argumentation.py:53-150`, `contestation.py:45-81`, §5.2, §6.2, §6.4, §7.2, §8.6.

---

### Stage 6 → §3.6 "The Verdict" + §7.2 Epistemic Status Mapping + §7.4 "What Becomes Unnecessary"

**Thesis claim (§3.6, line 337):** "The 'epistemic status' *emerges* from the argumentation semantics rather than being hand-assigned to a lattice element."

This is the thesis's central insight. In v3 (§4.2, lines 358–369), epistemic status was a hand-assigned Heyting lattice value — an `IntEnum` with arbitrary ordering. In v4, epistemic status is derived from two things: (1) extension membership (IN/OUT/UNDECIDED) and (2) provenance tag values (belief/disbelief/uncertainty thresholds).

**Thesis (§7.2, lines 739–742):**

| Extension membership | Tag condition | → Status |
|---|---|---|
| IN grounded, strong tag | belief > 0.8, uncertainty < 0.1 | ESTABLISHED |
| IN grounded, moderate tag | belief > 0.5, uncertainty < 0.3 | HYPOTHESIS |
| IN grounded, from Kₚ | otherwise | PROVISIONAL |
| UNDECIDED | — | OPEN |
| OUT in grounded, IN in preferred | disbelief > 0.4, belief > 0.3 | CONTESTED |

**Implementation:** `ProvenanceTag.epistemic_status()` in `schema_v4.py:154-169` implements exactly these thresholds. `ArgumentationFramework.get_epistemic_status()` in `argumentation.py:154-196` combines accepted argument tags via ⊕ (oplus) before calling this method.

**Thesis (§7.4, line 792):** "Heyting lattice ELIMINATED — Epistemic status emerges from extension membership."

**Implementation verified:** No `EpistemicValue(IntEnum)` anywhere in the v4 codebase. The `EpistemicStatus(Enum)` in `schema_v4.py` is a classification output, not a propagation input. The v3 total ordering problem (§4.3 H1: "CONTESTED and OPEN are not naturally comparable") is resolved — they are now derived from orthogonal dimensions (disbelief vs. uncertainty), not from a linear ordering.

**Thesis (§7.4, line 797):** "Evidence accumulates through the non-idempotent ⊕ (cumulative fusion). Three independent HYPOTHESIS arguments for the same conclusion yield a stronger-than-HYPOTHESIS tag."

**Implementation:** `ProvenanceTag.oplus()` in `schema_v4.py:72-100` implements Jøsang's cumulative fusion (§7.3, lines 779–784). This fixes v3's H2 problem (§4.3): "Conjunction within a chain uses min() (meet). Evidence can only *degrade* through inference — it can never accumulate."

**Source:** `schema_v4.py:154-169`, `argumentation.py:154-196`, §3.6, §7.2, §7.4, §4.3 (H1, H2).

---

### Stage 7 → §6.1 Provenance Semirings + §7.3 The Provenance Tag + §5.3 Provenance-Aware Datalog

**Thesis claim (§6.1, lines 596–622):** "Green, Karvounarakis & Tannen (PODS 2007) proved the foundational result: the provenance semiring PosBool[X] is the most general annotation structure for positive Datalog. Every other annotation scheme — Boolean, fuzzy, probabilistic, access control, trust — is a homomorphic image of the free provenance semiring."

**Implementation:** The `ProvenanceTag` IS the engine's semiring annotation. Each argument carries a tag. Each tag carries `source_ids` (the provenance trace), `pramana_type` (evidence classification), `trust_score` (source authority), `decay_factor` (temporal freshness), and `derivation_depth` (chain length). Stage 7 extracts these fields per conclusion.

**Thesis (§7.3, lines 751–786):** The ProvenanceTag definition with 8 fields and two operations (⊗, ⊕).

**Implementation:** `ProvenanceTag` in `schema_v4.py:20-100` matches the thesis definition field-for-field:

| Thesis §7.3 field | Implementation field | Extracted in Stage 7 |
|---|---|---|
| `source_ids: FrozenSet[str]` | `tag.source_ids` | `provenance[conc]["sources"]` |
| `pramana_type: PramanaType` | `tag.pramana_type` | `provenance[conc]["pramana"]` |
| `trust_score: float` | `tag.trust_score` | `provenance[conc]["trust"]` |
| `decay_factor: float` | `tag.decay_factor` | `provenance[conc]["decay"]` |
| `derivation_depth: int` | `tag.derivation_depth` | `provenance[conc]["derivation_depth"]` |

**Thesis (§7.4, line 794):** "Trust lookup table (20+ entries) ELIMINATED — Source trust is encoded in the provenance tag's trust_score field."

**Implementation verified:** No trust lookup table in v4. Trust is computed as `confidence.existence × confidence.formulation` in `_build_rule_tag()` (§9.7, line 1549) — 2 parameters from the KB, not 20+ hand-specified entries. This resolves v3's H3 problem (§4.3).

**Source:** `schema_v4.py:20-100`, `engine_service.py:175-184`, §6.1, §7.3, §7.4 (H3).

---

### Stage 8 → §1.2 Objective 4 + §3.1/§3.3 Epistemological Debate + §7.4 Elimination of Hand-Tuned UQ

**Thesis claim (§1.2, line 102):** Objective 4 — "Decompose uncertainty — separate 'we don't know' from 'nobody can know' from 'the LLM might be wrong'."

**Implementation:** Stage 8 decomposes uncertainty into three components, each mapped to thesis concepts:

| Component | Thesis source | Derivation |
|---|---|---|
| **Epistemic** ("we don't know") | §3.1, line 221: "P(X)=0.5 could mean 'we have no evidence at all' (OPEN)" | From `tag.belief` and `tag.uncertainty` — high uncertainty = low evidence |
| **Aleatoric** ("nobody can know") | §3.1, line 221: "P(X)=0.5 could mean 'we have strong evidence for and against' (CONTESTED)" | From `tag.disbelief` — high disbelief = inherent domain disagreement |
| **Inference** ("the LLM might be wrong") | §3.3, line 262: "Reliabilism: process reliability is a single number, not a structure" — rejected as too thin, but adopted for the grounding module | From `grounding_confidence`, `decay_factor`, `derivation_depth` — pipeline reliability metrics |

**Thesis (§3.1, lines 221–227):** "Probability collapses distinctions that matter… These are categorically different epistemic situations requiring different responses. Bayesians handle this with second-order uncertainty, but this reintroduces the categorical distinctions Nyāya provides natively — with extra mathematical machinery."

**Implementation:** The three-way decomposition IS the Nyāya alternative to Bayesian probability. `belief=0.7, disbelief=0.0, uncertainty=0.3` (PROVISIONAL) and `belief=0.7, disbelief=0.3, uncertainty=0.0` (borderline CONTESTED) have the same scalar "probability" but fundamentally different decompositions. Stage 8 surfaces this distinction.

**Thesis (§7.4, line 796):** "Hand-specified domain_base uncertainty ELIMINATED — Aleatoric uncertainty is modeled by the uncertainty component of provenance tags on base facts."

**Implementation verified:** No `domain_base` dictionary in v4. The uncertainty decomposition in `uncertainty.py:7-57` derives all values from the provenance tag and grounding confidence — structural, not hand-tuned. This resolves v3's H4 problem (§4.3).

**Source:** `uncertainty.py:7-57`, §1.2 (objective 4), §3.1, §3.3, §7.4 (H4).

---

### Stage 9 → §2.3 Five Hetvābhāsa Types + §7.2 Mapping + §4.2 The Frankenstein Problem

**Thesis claim (§2.3, lines 170–180):** Five hetvābhāsa types from Gautama's *Nyāya Sūtra*: savyabhicāra (inconclusive), viruddha (contradictory), satpratipakṣa (counterbalanced), asiddha (unestablished), bādhita (sublated).

**Thesis claim (§7.4, line 795):** "Keyword hetvābhāsa detection ELIMINATED — Hetvābhāsas ARE the defeat relation. Savyabhicāra = undercutting attack exists. Viruddha = rebutting attack exists. Asiddha = premise not established. Satpratipakṣa = symmetric attack. Bādhita = preference override. No separate detection module."

**This is the thesis's strongest architectural claim.** In v3 (§4.2, line 365), fallacy detection used "keyword-based pattern matching + sheaf H¹" — two independent ad-hoc mechanisms. In v4, hetvābhāsas are NOT detected by a separate module. They ARE the attack/defeat relations computed in Stage 4c and evaluated in Stage 5.

**Implementation:** Stage 9 iterates the attacks in the AF. For each attack where the attacker is labeled IN (accepted), it records a violation with the `hetvabhasa` field from the `Attack` dataclass (§9.5, line 1155). The hetvābhāsa type was assigned structurally during Stage 4c:
- Rebutting attacks → `hetvabhasa="viruddha"` (§9.7, line 1455)
- Undercutting attacks → `hetvabhasa="savyabhicara"` (§9.7, line 1492)
- Undermining attacks → `hetvabhasa="asiddha"` (§9.7, line 1515)

No keyword matching. No sheaf δ. No separate detection pipeline. The fallacy IS the defeat.

**Thesis (§2.3, line 180):** "This five-way classification is *richer* than Pollock's two-way (rebutting/undercutting) and richer than ASPIC+'s three-way (undermining/undercutting/rebutting). The bādhita category — defeat from a different epistemic channel — has no exact Western analogue."

**Implementation:** The `_defeats()` function in `argumentation.py:111-150` implements bādhita as the pramāṇa-preference check. This is the fourth defeat type — cross-modal override — that standard ASPIC+ lacks. Satpratipakṣa (symmetric attack) is handled by the mutual rebutting attacks in Stage 4c (lines 1450–1461): both directions of the contradiction get attack edges, and if neither prevails via preference, both remain UNDECIDED.

**Source:** `engine_service.py:199-211`, `t2_compiler_v4.py:209-307`, §2.3, §7.2, §7.4, §4.2.

---

### Stage 10 → §8.2 "Fundamental Issue" + §9.8 SynthesizeResponse + §1.3 "Epistemically Honest"

**Thesis claim (§8.2, lines 862–864):** "The full architecture confines the LLM to what it's actually good at: natural language understanding (grounding) and natural language generation (synthesis)."

**Implementation:** Stage 10 is the synthesis half. The `SynthesizeResponse` DSPy signature (§9.8, lines 1595–1611) takes structured inputs from Stages 4-9 and outputs calibrated prose. The LLM is a *writer*, not a *reasoner*.

**Thesis (§1.3, line 114):** "Epistemically honest: The system never claims more certainty than the evidence warrants."

**Implementation:** The `_synthesis_reward()` function in `engine_v4.py:36-74` enforces this:
- 0.20 weight for epistemic hedging ("hypothesis", "provisional", "suggests") — the LLM must use qualified language
- 0.15 weight for no overconfidence — penalizes "certainly", "definitely", "without doubt"
- 0.15 weight for hetvābhāsa warnings — must mention caveats when violations exist

`dspy.Refine(N=3, reward_fn=_synthesis_reward, threshold=0.5)` generates up to 3 candidates and selects the one that best calibrates its language to the evidence. This is the architectural enforcement of §1.3's epistemic honesty constraint.

**Thesis (§8.3, line 879):** "Explanation quality: Faithful to compiled KB structure — the explanation IS the reasoning, not an approximation. Faithfulness guaranteed because the symbolic engine IS the reasoner."

**Implementation:** The synthesis input includes `accepted_arguments` (formatted from the AF's grounded extension) and `defeated_arguments` (formatted from the AF's attacks). The LLM can only compose prose from this data — it cannot hallucinate claims because the structured input is the complete and exclusive evidence set.

**Source:** `engine_v4.py:16-74`, `engine_service.py:213-244`, §8.2, §1.3, §8.3.

---

### Stage 11 → §8.3-8.5 Contestable AI + §1.3 Inspectable

**Thesis claim (§8.3, line 873):** "Traceability: Provenance semiring tags — every conclusion traces through argument tree to specific sources, with pramāṇa type and trust score at each step."

**Implementation:** The final JSON response includes all artifacts: `response`, `sources`, `uncertainty` (three-way decomposition per conclusion), `provenance` (source_ids, pramana, trust, decay, depth per conclusion), `violations` (hetvābhāsa type + attack details), `grounding_confidence`, `extension_size`, `contestation` (mode + open questions + suggested evidence). This is the complete audit trail §8.3 requires.

**Thesis (§8.5, lines 908–922):** The Henin & Le Métayer hierarchy: explainability < justifiability < contestability.

**Implementation mapping:**

| Level | How Stage 11 satisfies it |
|---|---|
| **Explainability** | `argument_tree` (via `/api/reasoning/{id}/argument-tree`) exposes the full argument structure — "understand what the system did" |
| **Justifiability** | `provenance` + `uncertainty` fields trace every conclusion to sources with quantified evidence — "the system can demonstrate its decision was correct given its inputs and rules" |
| **Contestability** | `contestation` field + `/api/contestation/{id}/contest` endpoint enables adding counter-arguments that recompute the extension — "challenges have formal consequences on the system's behavior" |

**Thesis (§8.4, lines 881–906):** Four Leofante et al. (KR 2024) requirements:

| Requirement | Implementation |
|---|---|
| **(E) Explanations** | `argument_tree` endpoint returns nested proof traces with provenance tags |
| **(G) Grounds** | Five formal ground types: asiddha, savyabhicāra, viruddha, satpratipakṣa, bādhita — each with a specific API action |
| **(I) Interaction** | Three debate protocols via `contestation_mode`: vāda (cooperative), jalpa (adversarial), vitaṇḍā (pure critique) |
| **(R) Redress** | `apply_contestation()` in `contestation.py:163-218` adds new arguments/attacks and recomputes — polynomial, deterministic, structurally meaningful |

**Source:** `routers/queries.py:73-86`, `contestation.py:163-218`, §8.3, §8.4, §8.5.

---

### Cross-Cutting: What the Thesis Eliminates and How the Implementation Confirms It

The thesis's §7.4 claims 6 formalisms are eliminated. Stage-by-stage verification:

| v3 Component (§4.2) | Thesis §7.4 claim | Implementation evidence |
|---|---|---|
| **Heyting lattice** | "Eliminated — epistemic status emerges from extension membership" | No `EpistemicValue(IntEnum)` in v4. Stage 6 derives status from `ProvenanceTag.epistemic_status()`. |
| **Cellular sheaf** (δ, Laplacian, H¹) | "Eliminated — argumentation extensions are globally consistent by construction" | No sheaf code in v4. No `np.eye(stalk_dim)`. Stage 5's grounded extension satisfies Caminada & Amgoud rationality postulates. |
| **Trust lookup table** (20+ entries) | "Eliminated — source trust encoded in provenance tag's trust_score" | Trust = `confidence.existence × confidence.formulation` (2 KB fields, not 20+ table entries). |
| **Keyword hetvābhāsa detection** | "Eliminated — hetvābhāsas ARE the defeat relation" | No `if "survivorship" in sig` anywhere. Stage 4c derives attacks structurally. |
| **Hand-specified domain_base uncertainty** | "Eliminated — aleatoric uncertainty from provenance tags" | No `domain_base = {"CRAFT": 0.5}` dictionary. Stage 8 derives from tag values. |
| **Meet-only propagation** | "Eliminated — evidence accumulates through non-idempotent ⊕" | `ProvenanceTag.oplus()` implements cumulative fusion, not `min()`. |

**Thesis (§7.4, line 802):** "Net effect: 6 independent formalisms → 2 that compose (argumentation structure + semiring annotation). 16 hand-specified decisions → 3 tunable parameters + DSPy-optimizable hyperparameters."

**Implementation:** The entire v4 engine uses exactly two formalisms: ASPIC+ argumentation (Stages 4-5) and provenance semiring tags (Stages 6-8). Everything else — consistency, trust, fallacy detection, uncertainty — emerges from these two. The 12-stage pipeline is the operational realization of this claim.
