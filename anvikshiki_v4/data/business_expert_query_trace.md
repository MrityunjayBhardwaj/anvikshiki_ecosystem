# Anvikshiki Engine Query Trace

**Query:** "I have an ai startup like chatgpt, what should be my business model?"
**Architecture:** `business_expert.yaml`
**Date:** 2026-03-03

---

## Engine Thinking (Internal Reasoning)

### Pre-Step: Planning the Protocol Execution

Now I have the full architecture. Let me execute the 6-step protocol.

**STEP 1 — Load Architecture**

Domain: CRAFT
Pramanas: 4 (pratyaksa, anumana, sabda, upamana)
Vyaptis: 11 (V01-V11)
Hetvabhasas: 8 (H01-H08)

**STEP 2 — Ground the Query**

Query: "I have an ai startup like chatgpt, what should be my business model?"

Entities:
- The user's AI startup (unnamed)
- ChatGPT (as a reference/comparison)

Predicates:
- ai_startup(user_company) — the user has an AI startup
- similar_to(user_company, chatgpt) — the startup is similar to ChatGPT
- commercial_enterprise(user_company) — implied, it's a startup
- startup_stage(user_company) — implied early stage
- technology_company(user_company) — implied from AI startup
- seeking_business_model(user_company) — explicitly stated question

Now I'm identifying what can be reasonably inferred from the query. The user hasn't established
positive unit economics yet — that's actually what they're trying to figure out by asking about
business models.

The ChatGPT comparison tells me they're likely building a generative AI product, which typically
involves API or subscription models with significant compute costs targeting either consumers or
enterprises. They're probably in early stages without organizational growth yet, though they might
be exploring network effects or information asymmetries that AI models can create.

Let me refocus on what's actually stated versus what I'm inferring. The core facts are that they
have an AI startup and want guidance on business model strategy — everything else is speculation
based on the ChatGPT reference point.

### Thinking: Framework Selection

Now I'm thinking through which frameworks actually apply here. The value equation is directly
relevant since they need to figure out unit economics that work. The constraint cascade matters
too because identifying what's actually limiting them will shape the model. And information
asymmetry is worth considering since AI does create that advantage, though I need to see where
they're going with that line of thinking.

The optionality-commitment framework is important because choosing a business model is a real
strategic commitment that closes off other paths. Capital allocation could matter but that's
downstream from figuring out what actually creates value. And disruption asymmetry is worth
keeping in mind since they're operating in a space where incumbents are vulnerable, though
that's more about market positioning than the core business model question.

### Thinking: Grounding Precision

Now I'm stepping back to think about what I actually know about this situation. It's a
"what should I do" question, so I'm looking for what business model logically follows from
the startup's characteristics. Let me identify the key facts: it's a commercial enterprise,
a technology company, and they're building a generative AI product similar to ChatGPT.

From that, I can reasonably infer high compute costs — that's inherent to LLM inference — and
that they're early-stage. Now I'm checking which of my decision frameworks actually apply here.
The compute cost constraint seems like the binding one I should focus on, and I can infer some
data advantage from being in AI. But I'm noticing that several conditions I'd normally check —
positive unit economics, organizational growth, coordination overhead — aren't established yet.
The strategic commitment piece is relevant though, since choosing a business model is itself a
strategic decision.

I need to be more careful about what's actually grounded versus what I'm inferring. The scope
exclusions are particularly important here — ChatGPT-style startups hit several warning flags:
they're often building network effects, operating in increasingly commoditized markets, and
competing against very attentive incumbents like Google and Meta. Let me work through the scope
conditions more systematically to see where the framework actually applies.

### Thinking: Scope Analysis

There are attentive incumbents in AI like Google, Microsoft, and Meta — that's a scope warning.
There are also significant scale barriers with compute, data, and talent requirements, which
triggers another warning. Now checking decay risk: V09 and V04 both have moderate decay risk,
which doesn't meet the threshold for warnings since only high or critical decay risk matters,
so I'm clear on that front.

### Thinking: Inference Chain Construction

Moving into Step 5, I'm tracing out the inference chains.

First, I can establish that superior information processing from AI models leads to pricing
power through V03. Second, compute cost being the binding constraint allows me to apply V02
and conclude resource allocation is effective. Third, the strategic commitment to a particular
business model connects through V06 to build capability.

But **Chain 4 breaks down** — positive unit economics is what they're actually trying to
determine, so V01's antecedent isn't satisfied yet, though this is the critical constraint the
business model must satisfy. There's also a scope exclusion around network effect building
phases that might apply.

**Chain 5 on disruption doesn't work** either since the scope exclusions for attentive
incumbents are triggered.

So I'm left with V03, V02, V06, and V01 (scope-qualified) as the main applicable chains.

### Thinking: Hetvabhasa Self-Check

Now I need to check for hetvabhasa fallacies, starting with the revenue vanity trap. I'm
noticing the query doesn't explicitly mention revenue, so I should avoid letting revenue
growth dominate the analysis.

The scalability presumption is another risk — just because something is "like ChatGPT" doesn't
mean it'll scale identically. And the moat mirage is real here too; I need to be careful not to
treat AI technology itself as a durable competitive advantage.

Actually, let me be more precise about which fallacies could undermine my own reasoning. The
framework reification fallacy doesn't apply since I'm aware the vyapti framework has limits.
But the **scalability presumption** could easily fire if I assume "like ChatGPT" implies similar
scaling dynamics, and the **moat mirage** definitely fires if I suggest AI technology alone
creates competitive advantage. I need to construct my answer with these pitfalls in mind.

### Thinking: Synthesis Planning

Now I'm looking at the key business model constraints:
- Unit economics must be positive, though there's a real tension here — AI startups often run
  negative unit economics intentionally during the building phase
- Information asymmetry from AI creates pricing power that the business model should exploit
- The binding constraint for ChatGPT-like companies is compute cost, so the entire model —
  architecture, inference efficiency, and pricing — needs to be designed around this
- Choosing a business model locks in commitments that destroy other options, so I should think
  about where flexibility matters most

The competitive landscape isn't a classic disruption scenario either — incumbents are actively
watching and responding. Growth without deliberate structural changes will erode value over
time, which is a real risk to flag. I need to avoid the common fallacies around scalability and
moats that plague AI business model thinking.

So the core question really comes down to unit economics — whether each inference transaction
creates more value than it costs. There are several paths: API pricing keeps margins transparent
but thin until scale kicks in, subscriptions trade predictability for the need to price above
average compute costs, enterprise licensing offers better margins with longer sales cycles, and
freemium models can build network effects even while running negative unit economics initially.

The real constraint is compute cost itself, so the business model has to be architected around
that — optimizing inference efficiency through distillation and caching, pricing to cover
marginal costs plus margin, and deferring optimization of marketing or features until that's
locked in.

The model itself becomes the competitive moat through proprietary fine-tuning data and domain
expertise, with user feedback creating a flywheel that continuously improves it. I should avoid
locking into one approach too early — starting with an API gives flexibility before committing
to applications, and keeping pricing adjustable lets me pivot as I learn.

There are some constraints to watch: I can intentionally run negative unit economics during
network effect building, but I shouldn't assume I'll disrupt incumbents who are already watching
and competing.

---

## STEP 1 — Load Architecture (T2)

```
ARCHITECTURE LOADED
  Domain:      CRAFT
  Pramanas:    4 — [pratyaksa, anumana, sabda, upamana]
  Vyaptis:     11 — V01 (Value Equation), V02 (Constraint Cascade), V03 (Information Asymmetry Premium),
                     V04 (Organizational Entropy), V05 (Market Signal Decay), V06 (Optionality-Commitment),
                     V07 (Incentive-Behavior Isomorphism), V08 (Capital Allocation Identity),
                     V09 (Disruption Asymmetry), V10 (Judgment Calibration), V11 (Growth Trap)
  Hetvabhasas: 8 — H01 (Revenue Vanity Trap), H02 (Framework Reification), H03 (Survivorship Inference),
                    H04 (Correlation-Strategy Confusion), H05 (Scalability Presumption), H06 (Sunk Cost Anchor),
                    H07 (Moat Mirage), H08 (Metric Goodhart)
```

---

## STEP 2 — Ground the Query

**Query**: "I have an ai startup like chatgpt, what should be my business model?"

```
GROUNDING
  Entities:
    - user_company (unnamed AI startup)
    - ChatGPT (reference product — OpenAI's conversational AI)

  Predicates:
    - commercial_enterprise(user_company)           — it's a startup seeking revenue
    - generative_ai_product(user_company)            — "like ChatGPT" implies LLM-based product
    - high_compute_cost(user_company)                — LLM inference is compute-intensive (implied)
    - early_stage_company(user_company)              — "startup" implies pre-scale
    - superior_information(user_company)              — AI models create information processing advantage
    - binding_constraint_identified(user_company)     — compute cost is the binding constraint for LLM startups
    - strategic_commitment(user_company)              — choosing a business model is a strategic commitment
    - network_effect_building_phase(user_company)     — ChatGPT-like products often in flywheel-building stage
    - organizational_growth(user_company)             — NOT YET (startup stage, but will be relevant at scale)

  Relevant vyaptis:
    V01 — Value Equation:              RELEVANT — core question; must design unit economics for each AI transaction
    V02 — Constraint Cascade:          RELEVANT — compute cost is the binding constraint; model allocates around it
    V03 — Information Asymmetry:       RELEVANT — AI model creates information advantage → pricing power
    V04 — Organizational Entropy:      RELEVANT (forward-looking) — scaling warning for business model design
    V05 — Market Signal Decay:         MARGINAL — relevant only when org grows beyond direct customer contact
    V06 — Optionality-Commitment:      RELEVANT — choosing a business model is the key strategic commitment
    V07 — Incentive-Behavior:          MARGINAL — not directly about business model design
    V08 — Capital Allocation:          RELEVANT (chain dependent) — requires V01+V02 outputs as antecedents
    V09 — Disruption Asymmetry:        RELEVANT — AI startups are potential disruptors, but with caveats
    V10 — Judgment Calibration:        META-RELEVANT — quality of the business model decision itself
    V11 — Growth Trap:                 RELEVANT (warning) — premature scaling without value creation

  Query type: derivation
```

---

## STEP 3 — Scope Check (Deterministic)

**V01 — The Value Equation**
- Scope condition `commercial_enterprise` → SATISFIED
- Scope exclusion `subsidized_entity` → not triggered
- Scope exclusion `network_effect_building_phase` → **TRIGGERED** — ChatGPT-like products are typically in network-effect building phase (more users → more feedback data → better model)

```
⚠ SCOPE WARNING: V01 (The Value Equation)
  Exclusion triggered: "network_effect_building_phase"
  Implication: Unit economics may be intentionally negative during flywheel building.
  V01 still applies as a TARGET constraint (the business model must eventually achieve
  positive unit economics), but cannot be used to evaluate CURRENT viability.
```

**V02 — The Constraint Cascade**
- Scope condition `serial_dependency_system` → SATISFIED (AI inference is serial: query→compute→response)
- Scope exclusion `highly_parallel_system` → not triggered

**V03 — The Information Asymmetry Premium**
- Scope condition `heterogeneous_quality_market` → SATISFIED (AI model quality varies greatly)
- Scope exclusion `perfectly_commoditized_market` → BORDERLINE — LLM APIs are commoditizing but not perfectly so
- Scope exclusion `regulated_disclosure_market` → not triggered

**V04 — Organizational Entropy**
- Scope conditions: none required
- Scope exclusion `active_structural_intervention` → not triggered (no evidence of deliberate org design)

**V06 — Optionality-Commitment**
- Scope conditions: none required
- Scope exclusion `abundant_resources_relative_to_opportunity` → not triggered (startup implies constrained resources)

**V08 — Capital Allocation Identity**
- Scope condition `significant_free_cash_flow` → NOT SATISFIED — startups typically don't have significant FCF
- Scope exclusion `regulated_industry` → not triggered
- Note: V08 applies weakly; the startup likely burns cash rather than allocates surplus

**V09 — Disruption Asymmetry**
- Scope condition `sustaining_innovation_trajectory` → AMBIGUOUS — AI could be sustaining or disruptive depending on market
- Scope exclusion `attentive_incumbent` → **TRIGGERED** — Google, Microsoft, Meta, Amazon are all actively competing in AI
- Scope exclusion `scale_barrier_to_entry` → **TRIGGERED** — massive compute/data/talent requirements

```
⚠ SCOPE WARNING: V09 (Disruption Asymmetry)
  Exclusion triggered: "attentive_incumbent" — Google (Gemini), Microsoft (Copilot),
  Meta (Llama), Amazon (Bedrock) are all heavily investing in AI.
  Exclusion triggered: "scale_barrier_to_entry" — LLM training requires $10M-$1B+
  compute, proprietary data, and specialized ML talent.
  Implication: Classical disruption theory does NOT straightforwardly apply. The
  incumbents are not ignoring this market. Do not plan around incumbent inattention.
```

**V11 — Growth Trap**
- Scope exclusion `active_structural_intervention` → not triggered
- Scope exclusion `small_team_direct_contact` → LIKELY TRIGGERED for a startup (small team)

```
⚠ SCOPE WARNING: V11 (The Growth Trap)
  Exclusion triggered: "small_team_direct_contact" — as a startup, the team is likely
  small enough that coordination overhead hasn't materialized.
  Implication: V11 doesn't apply NOW but becomes relevant at scaling thresholds (~50+ people).
```

---

## STEP 4 — Decay Check (Deterministic)

Today: **2026-03-03**

Scanning relevant vyaptis for `high` or `critical` decay_risk:
- V01: low → skip
- V02: low → skip
- V03: low → skip
- V04: moderate → skip (threshold is high/critical only)
- V06: low → skip
- V08: low → skip
- V09: moderate → skip
- V11: low → skip

```
✓ Decay check: all rules current
  (Note: V04 and V09 have "moderate" decay risk but do not meet the high/critical threshold.
   V04's condition "AI/remote tools may shift traditional thresholds" is contextually
   relevant to an AI startup but does not trigger a formal decay warning.)
```

---

## STEP 5 — Reason Over Domain

### Inference Chain

```
Step 1: Apply V02 — The Constraint Cascade
  Antecedents required:  [binding_constraint_identified]
  Antecedents satisfied: YES — compute cost is the binding constraint for LLM inference
  Scope:                 PASSED — serial dependency system, no exclusions triggered
  Epistemic status:      established
  Confidence:            formulation=0.85, evidence=observational
  Derived:               resource_allocation_effective = "Allocate resources around the compute
                         constraint first; don't optimize sales/marketing/features until inference
                         cost economics work"
  Epistemic propagation: established (min of established, established) = ESTABLISHED
```

```
Step 2: Apply V03 — The Information Asymmetry Premium
  Antecedents required:  [superior_information]
  Antecedents satisfied: YES — AI model creates superior information processing capability
  Scope:                 PASSED (borderline on commoditization, but not perfectly commoditized)
  Epistemic status:      established
  Confidence:            formulation=0.90, evidence=theoretical
  Derived:               pricing_power = "Information asymmetry from proprietary model quality,
                         fine-tuning data, and domain specialization creates pricing power"
  Epistemic propagation: ESTABLISHED
```

```
Step 3: Apply V06 — The Optionality-Commitment Tradeoff
  Antecedents required:  [strategic_commitment]
  Antecedents satisfied: YES — choosing a business model is a strategic commitment
  Scope:                 PASSED
  Epistemic status:      established
  Confidence:            formulation=0.85, evidence=theoretical
  Derived:               capability_gain = "Each business model choice (API vs. subscription vs.
                         enterprise) creates specific capabilities while foreclosing others"
  Epistemic propagation: ESTABLISHED
```

```
Step 4: Apply V01 — The Value Equation [⚠ SCOPE-QUALIFIED]
  Antecedents required:  [positive_unit_economics]
  Antecedents satisfied: CONDITIONAL — not yet achieved, but this is the design target
  Scope:                 ⚠ QUALIFIED — "network_effect_building_phase" exclusion applies
  Epistemic status:      established (rule itself)
  Confidence:            formulation=0.90, evidence=observational
  Derived:               value_creation = "The business model must be DESIGNED so that each
                         core transaction (API call, subscription month, enterprise contract)
                         creates more value than it consumes. During network-effect building,
                         negative unit economics are tolerable IF the flywheel thesis is sound."
  Epistemic propagation: HYPOTHESIS (scope warning downgrades from established)
```

```
Step 5: Apply V04 — Organizational Entropy (forward-looking)
  Antecedents required:  [organizational_growth]
  Antecedents satisfied: NOT YET — startup is pre-growth, but this informs model DESIGN
  Scope:                 PASSED
  Epistemic status:      established
  Derived:               coordination_overhead = "Business model must account for scaling
                         thresholds at ~8, 50, 150 people; design org structure before hiring"
  Epistemic propagation: N/A (advisory, antecedent not satisfied for formal derivation)
  Note:                  Applied as FORWARD WARNING, not current derivation
```

```
Step 6: Chain — Apply V08 — Capital Allocation Identity
  Antecedents required:  [value_creation (from Step 4), resource_allocation_effective (from Step 1)]
  Antecedents satisfied: PARTIAL — value_creation is scope-qualified; resource_allocation is derived
  Scope:                 ⚠ significant_free_cash_flow condition NOT MET (startup burns cash)
  Epistemic status:      established (rule)
  Derived:               long_term_value = "Long-term value depends on allocating capital to
                         the highest-return use; for an AI startup this means choosing between
                         model training, inference infrastructure, go-to-market, and talent"
  Epistemic propagation: HYPOTHESIS (weakest link: Step 4's scope-qualified value_creation)
```

### Hetvabhasa Check

Scanning reasoning against all 8 detection signatures:

- **H01 (Revenue Vanity Trap)**: `revenue_growth_cited_without_unit_economics` — NOT detected. Reasoning explicitly centers unit economics.
- **H02 (Framework Reification)**: `single_framework_treated_as_complete_model` — NOT detected. Multiple vyaptis applied with scope caveats.
- **H03 (Survivorship Inference)**: `success_stories_only` — **BORDERLINE** — referencing ChatGPT as the model risks survivorship bias.

```
🚫 HETVABHASA DETECTED: H03 — The Survivorship Inference
  Signal:     "success_stories_only" — using ChatGPT as the reference template risks
              studying only the winner while ignoring Jasper, Character.AI, Inflection,
              and other AI startups that followed similar models with different outcomes.
  Correction: Include failed examples with the same characteristics; check base rates.
  Action:     Revise — note that "like ChatGPT" business model has a LOW base rate of
              success. Most AI startups with similar models have not achieved profitability.
              The reasoning must account for survivor bias in the reference point.
```

- **H05 (Scalability Presumption)**: `linear_extrapolation_across_scale_thresholds` — **DETECTED**

```
🚫 HETVABHASA DETECTED: H05 — The Scalability Presumption
  Signal:     "linear_extrapolation_across_scale_thresholds" — assuming a ChatGPT-like
              product at small scale will achieve ChatGPT-like margins at large scale
              ignores phase transitions (compute costs don't scale linearly, enterprise
              sales require different org structures than self-serve).
  Correction: Model the phase transitions; identify what changes qualitatively at each
              threshold. Separate business model for <1K, 1K-100K, 100K-1M, 1M+ users.
  Action:     Incorporated — the response must distinguish business model by scale stage.
```

- **H07 (Moat Mirage)**: `no_competitors_equated_with_competitive_advantage` — **DETECTED**

```
🚫 HETVABHASA DETECTED: H07 — The Moat Mirage
  Signal:     Being "like ChatGPT" (having an AI model) is not a competitive advantage.
              LLM capabilities are commoditizing rapidly. A technology lead alone is not a moat.
  Correction: Identify structural barriers (network effects, switching costs, proprietary
              data, distribution). A model you trained is not a moat; OpenAI/Google/Meta
              will match capabilities.
  Action:     Incorporated — the response must explicitly address where durable advantage
              comes from (NOT the AI model itself).
```

- **H04, H06, H08**: NOT detected in reasoning.

---

## STEP 6 — Synthesize Calibrated Response

---

### RESPONSE

Your business model must solve one fundamental problem before anything else: **make each core
transaction create more value than it consumes** (V01). For a ChatGPT-like AI startup, the
"core transaction" is an inference call — a user query that costs you compute. Everything else
follows from whether you can price above that marginal cost while delivering enough value that
customers pay.

**Three business model architectures, ranked by unit economics clarity:**

**1. API / Usage-Based Pricing** (strongest unit economics signal)
- Charge per token/request. Revenue scales directly with compute cost.
- Requires: knowing your cost-per-inference precisely (V02 — compute is your binding constraint;
  optimize there before anything else).
- Best when: you have a differentiated model or fine-tuning that commands a premium (V03 —
  information asymmetry creates pricing power).
- Risk: LLM APIs are commoditizing. Your model alone is NOT a moat (H07 correction). Pricing
  power comes from **proprietary training data, domain specialization, or workflow integration**
  — not model architecture.

**2. Subscription / SaaS** (moderate clarity)
- Flat monthly fee for access (ChatGPT Plus model).
- Requires: predicting average compute per subscriber and pricing above it.
- Best when: you can create **switching costs** (user history, customization, workflow
  integration) that prevent churn when competitors match your capabilities.
- Risk: heavy users subsidize light users; margin compression if usage patterns shift upward.

**3. Enterprise Licensing** (highest margin, longest cycle)
- Custom deployments, dedicated instances, SLAs.
- Requires: sales team, compliance capabilities, data privacy guarantees.
- Best when: your information asymmetry is domain-specific (legal AI, medical AI, financial AI)
  and the buyer has high willingness-to-pay.

**Critical warnings from the reasoning:**

- **You are NOT in a disruption play** (V09 scope-excluded). Google, Microsoft, Meta, and Amazon
  are attentive incumbents with more compute, data, and distribution than you. Do not plan your
  business model around incumbent inattention.

- **Survivorship bias alert** (H03). ChatGPT is a singular outcome. Most AI startups with
  similar models — Jasper, Character.AI, Inflection AI, Cohere's consumer attempts — have
  struggled with monetization or been acqui-hired. The base rate for "ChatGPT-like business
  model succeeds" is LOW.

- **Scalability is not linear** (H05). Your business model at 1K users, 100K users, and 10M
  users will be structurally different. Design for the current stage, not for the ChatGPT-scale
  stage. Phase transitions in compute costs, org structure (V04), and market signal quality (V05)
  will force business model evolution.

- **Your AI model is not your moat** (H07). The moat must come from: (a) proprietary data
  flywheels (user interactions improve the model), (b) distribution/workflow embedding (hard to
  rip out), (c) switching costs (user history, custom fine-tuning), or (d) regulatory/compliance
  barriers in a vertical.

- **The network-effect building phase** (V01 scope exclusion) means you may rationally run
  negative unit economics NOW — but only if you have a falsifiable thesis for why more users
  create a durable advantage. "More users = more data = better model" is the thesis, but it must
  be tested, not assumed.

**Recommended approach** (V06 — preserve optionality):
Start with **API pricing** (clearest unit economics, most flexibility). Layer **subscription**
on top for power users. Explore **enterprise** as you find domain-specific information
asymmetry. This sequence preserves optionality while each stage validates the unit economics
thesis before committing further.

---

### Confidence & Metadata

**CONFIDENCE**: `moderate`
_V01 (Value Equation) is scope-qualified by network_effect_building_phase; V09 (Disruption) is
double scope-excluded; three hetvabhasas fired requiring reasoning corrections. Chain passes
through hypothesis status._

**RULES USED**: `[V02 → V03 → V06 → V01(⚠) → V08(⚠)] + V04(advisory) + V09(excluded)`

**SCOPE WARNINGS**:
- `V01`: "network_effect_building_phase" — unit economics may be intentionally negative
- `V09`: "attentive_incumbent" + "scale_barrier_to_entry" — disruption theory does not apply
- `V11`: "small_team_direct_contact" — growth trap not yet relevant (startup size)
- `V08`: scope condition "significant_free_cash_flow" not met (startup burns cash)

**DECAY WARNINGS**: `none`

**SOURCES CITED**: `src_hbs_unit_economics, src_ries_2011, src_goldratt_1984, src_shapiro_varian_1998, src_porter_1985, src_thorndike_2012, src_christensen_1997, src_king_baatartogtokh_2015, src_blank_2005`

**UNCERTAINTY FLAGS**:
```
scope_violations:      3 (V01, V09, V11)
decay_exposures:       0
hypothesis_chain:      true (V01 scope → V08 chain)
contested_chain:       false
open_question_chain:   false
hetvabhasa_fired:      true (H03, H05, H07)
```

---

## Pipeline Summary

```
Query
  ↓
STEP 1: Load Architecture → 11 vyaptis, 8 hetvabhasas from business_expert.yaml
  ↓
STEP 2: Ground Query → 9 predicates, 8 relevant vyaptis, query type = derivation
  ↓
STEP 3: Scope Check → 3 scope warnings (V01, V09, V11)
  ↓
STEP 4: Decay Check → 0 decay warnings (all current)
  ↓
STEP 5: Reason → 6-step inference chain, 3 hetvabhasas fired (H03, H05, H07)
  ↓
STEP 6: Synthesize → moderate confidence, hypothesis chain, 3 scope violations
  ↓
Calibrated Response
```
