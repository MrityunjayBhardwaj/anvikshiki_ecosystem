# The Ānvīkṣikī Engine

### How a question becomes an answer you are allowed to argue with

---

*Every trace in this document was produced by running the code in this repository against `anvikshiki_v4/data/business_expert.yaml`. Nothing is illustrative. Where the output is wrong or awkward, it is shown wrong and awkward, and §8 says why.*

*Related: `docs/pipeline_eli5.md` covers the same ground stage-by-stage in more depth. This document is the narrative version — one question, followed from the door to the answer.*

---

## 1. The problem, stated concretely

Ask a language model whether a company with strong unit economics is creating value, and you will get a fluent, confident, plausible paragraph. Ask it again with the word "but" in front and you may get the opposite paragraph, equally fluent and equally confident.

Neither answer tells you three things you need:

- **What was assumed.** Which claims did it treat as given, and which did it derive?
- **What could overturn it.** If one fact changed, would the answer change? Which fact?
- **How to disagree.** If you think it is wrong, what specifically do you point at?

You cannot point at anything. The answer is a single undifferentiated block of text produced by a process you cannot inspect, and your only available response is to trust it or not. Disagreement has no address.

This engine exists to give disagreement an address.

## 2. The idea, which is old

*Ānvīkṣikī* (आन्वीक्षिकी) is the Sanskrit term for the discipline of critical inquiry — the tradition that produced the Nyāya school's theory of what makes a reason *good*. That tradition's central move is worth stating plainly, because the whole architecture is an implementation of it:

> Knowledge is not what you can assert. Knowledge is **what survives challenge**.

Nyāya is unusually engineering-minded about this. It doesn't just say "arguments can be bad" — it enumerates the *specific ways* a reason fails, and gives each one a name. Those names became the attack types in this system:

- **asiddha** — the premise itself is not established
- **savyabhicāra** — the reason is inconstant; it doesn't hold in this case
- **viruddha** — the reason proves the opposite of what's claimed

And it distinguishes *how you came to know* something — the **pramāṇas**: direct perception (*pratyakṣa*), inference (*anumāna*), testimony (*śabda*), analogy (*upamāna*) — in a strict order of strength. When two arguments conflict, the one resting on the stronger channel wins.

None of this is decoration. In the code, `PramanaType` is an ordered enum whose comparison operator decides which argument defeats which. `hetvabhasa` is a string field on every attack. The Sanskrit is the variable naming; the mechanism is 1990s formal argumentation theory (ASPIC+, Dung semantics), and the two turn out to fit together almost exactly.

## 3. What the engine knows

Domain knowledge lives in a YAML file as **vyāptis** — invariable relations. Here is one, as it actually appears:

```yaml
V01:
  name: "The Value Equation"
  statement: "A business survives if and only if it creates more economic value
              than it consumes, as measured by unit economics of its core transaction"
  causal_status: empirical
  antecedents: [positive_unit_economics]
  consequent: value_creation
  scope_conditions: [commercial_enterprise]
  scope_exclusions: [subsidized_entity, network_effect_building_phase]
  epistemic_status: established
  confidence: {existence: 0.95, formulation: 0.9, evidence: observational}
  sources: [src_hbs_unit_economics, src_ries_2011]
```

Read it as a rule — *if positive unit economics, then value creation* — but notice the two fields that make it more than a rule.

**`scope_exclusions`** is where the honesty lives. The rule does not apply to a subsidised entity, or to a company deliberately burning money to build network effects. Most knowledge representations record what a rule says. This one records **where it stops**, and — as we'll see — that boundary is enforced by attacking the rule rather than by a comment nobody reads.

**`epistemic_status`** records how settled the claim is in its field: `established`, `hypothesis`, `open`, `contested`. This is the field the whole engine is ultimately computing over.

The business-strategy knowledge base is eleven such rules:

```
V01 The Value Equation            positive_unit_economics → value_creation
V02 The Constraint Cascade        binding_constraint_identified → resource_allocation_effective
V03 Information Asymmetry Premium superior_information → pricing_power
V04 Organizational Entropy        organizational_growth → coordination_overhead
V05 Market Signal Decay           coordination_overhead → distorted_market_signal
V06 Optionality-Commitment        strategic_commitment → capability_gain
V07 Incentive-Behavior Isomorphism incentive_alignment → organizational_effectiveness
V08 Capital Allocation Identity   value_creation, resource_allocation_effective → long_term_value
V09 Disruption Asymmetry          incumbent_rational_allocation, low_margin_market_entrant → disruption_vulnerability
V10 Judgment Calibration          calibration_accuracy → decision_quality
V11 The Growth Trap               organizational_growth, coordination_overhead → not_value_creation
```

Eleven rules and eight named fallacies is the entire domain model. That smallness is deliberate and it turns out to be a constant: the copywriting guide's architecture document lists nine vyāptis, the non-fiction writing volume lists ten. A domain's reasoning *shape* appears to be about ten invariants. Everything else is detail that hangs off them.

Look at **V11** and then look at **V01** again. V01 concludes `value_creation`. V11 concludes `not_value_creation`. They are in the same knowledge base, deliberately. The engine is not supposed to hold a consistent opinion about growth. It is supposed to hold *both rules* and let the facts decide which survives. Keep V11 in mind; it is the star of §5.

## 4. The journey of a question

Someone asks: **"Our unit economics are solidly positive. Are we creating value?"**

### 4.1 The gate

Before any reasoning happens, the engine asks a question about itself: *do I know anything about this?*

This is a purely mechanical check, no model involved. Every predicate the query mentions is matched against the knowledge base's vocabulary — first exactly, then through a synonym table, then by token overlap. The result is a coverage ratio and a routing decision:

```
in-domain      ratio=1.00  FULL     matched: positive_unit_economics, binding_constraint_identified
                                    how: exact, exact          → V01, V02

partial        ratio=0.33  PARTIAL  matched: positive_unit_economics
                                    unmatched: brand_equity, employee_morale

out-of-domain  ratio=0.00  DECLINE  unmatched: marketing_channel, email_open_rate, seo_ranking
```

The third row is the important one. Asked about SEO rankings, the business-strategy engine does not improvise. It has no rule mentioning anything like `seo_ranking`, the coverage ratio is zero, and it declines. Not "I'm not certain" — a structural refusal, computed before a single reasoning step.

This is the first behaviour that separates the engine from a chatbot, and it costs nothing: no LLM call, fully deterministic, same answer every time.

Our question scores FULL. We proceed.

### 4.2 Translation

Natural language now has to become predicates, and this is the one place where a language model's judgment is load-bearing.

The defence is to constrain the vocabulary. The model is not asked "what does this question mean?" — it is shown the complete list of legal predicate names and asked which of *those* apply. It's asked five times independently, and only predicates that appear in every run are treated as consensus; the disagreement rate becomes a confidence number. If agreement is poor, the predicates get translated back into English and compared to the original question, and if the round trip has drifted, the disputed items are dropped.

Out comes:

```
positive_unit_economics(acme)     confidence 0.9
```

Everything downstream of this line is deterministic. Everything upstream of it is a model's judgment. That boundary is worth remembering — it is where the system's real uncertainty lives, and §8 returns to it.

### 4.3 Building the argument

Now the symbolic machinery starts, and it is fast:

```
args=2  attacks=0   [0.09 ms]

A0000  positive_unit_economics   rule=None  strict=True   label=in  b=0.900
       pramāṇa=PRATYAKSA   sources=[user_input]

A0001  value_creation            rule=V01   strict=False  label=in  b=0.855
       pramāṇa=ANUMANA     sources=[src_hbs_unit_economics, src_ries_2011, user_input]
```

Two arguments. The first is the user's own statement — a **premise argument**, marked `strict` because the user asserted it, tagged `PRATYAKSA` because direct testimony about your own company is the strongest evidence channel available here.

The second is derived. It applies V01, so its rule is `V01` and it inherits `ANUMANA` — inference — because that's what a derived conclusion is. Notice what happened to the source list: it now carries **both** of V01's citations *and* the user's input. The provenance accumulated automatically along the derivation. Nobody wrote code to do that per-rule; it falls out of how tags compose.

And notice `is_strict=False`. V01 is `empirical`, not definitional, so the argument built on it is **defeasible** — it can be argued with. Had V01 been `structural` or `definitional`, the argument would be strict and could not be rebutted at all. The epistemology of the rule determines the vulnerability of the conclusion.

Ninety microseconds, and there are no attacks, because nothing in this small world contradicts anything.

### 4.4 The verdict

The engine now computes the **grounded extension** — the set of arguments that survive.

The rule is recursive and short: an argument is IN if every argument that defeats it is OUT. An argument is OUT if any argument that defeats it is IN. Iterate to a fixpoint; whatever is left over is UNDECIDED. It is guaranteed to terminate, runs in polynomial time, and produces exactly one answer.

Here, nothing attacks anything, so both arguments are IN.

### 4.5 The status

The final step converts survival into an epistemic label:

```
value_creation   → HYPOTHESIS   (belief 0.855, trust 0.85, depth 0)
long_term_value  → None         (nothing derives it)
```

**And here is the engine's most instructive current flaw, visible in its own output.**

V01's `epistemic_status` in the knowledge base is `established`. The user was 90% confident. One inference step later, the answer is *HYPOTHESIS*. What degraded it? Only the arithmetic: belief 0.9 × 0.95 = 0.855, and the residual uncertainty of 0.145 crosses a hardcoded threshold that demands ≤ 0.1 for ESTABLISHED.

Nothing was contradicted. No attack landed. The conclusion was weakened purely by having been *derived* rather than asserted. Push it further and it gets worse — chain the same evidence against itself and the status decays from `established` to `hypothesis` to `provisional`, though nothing was learned or challenged along the way.

This is the known defect that governs the engine's next redesign: continuous belief values flowing through multiplication and then being cut into categories by fixed thresholds. There is no threshold that repairs it, because a strictly decreasing quantity crosses any fixed cutoff eventually. The fix is to stop computing status arithmetically and derive it from the argument structure instead — where "restating a claim doesn't weaken it" holds automatically, because taking a minimum of a value with itself returns the value.

The story is told with the flaw in it because the flaw is legible in the output, which is itself the point of building the system this way.

### 4.6 The words

Only now does a language model get to write prose — and it is handed the conclusions, their statuses, the defeated arguments with their fallacy names, and the retrieved source passages, with instructions to hedge according to status and to flag anything contested.

The model is not reasoning. It is **reporting a computation it did not perform and cannot alter**. That is the entire division of labour: the model handles language, the engine handles inference, and the engine's output is a graph that exists whether or not anyone renders it into English.

## 5. When the rules disagree

Now the interesting case. Suppose the company also tells us it is growing fast and drowning in coordination overhead. V01 still fires — unit economics are positive, so value is created. But **V11, the Growth Trap**, also fires: growth plus coordination overhead produces `not_value_creation`.

The knowledge base now contains a contradiction, on purpose.

```
args=9  attacks=4

rebutting  viruddha  value_creation      [in]  --> not_value_creation  [out]
rebutting  viruddha  not_value_creation  [out] --> value_creation      [in]
rebutting  viruddha  value_creation      [in]  --> not_value_creation  [out]
rebutting  viruddha  not_value_creation  [out] --> value_creation      [in]

value_creation      → HYPOTHESIS
not_value_creation  → CONTESTED
```

The engine noticed, unprompted, that `value_creation` and `not_value_creation` cannot both hold, and generated **mutual** attacks — each argument attacking the other, tagged `viruddha`, the Nyāya name for a reason that establishes the contrary of what it was offered for.

Mutual attack means the contest has to be settled. Both arguments rest on inference (`ANUMANA`), so pramāṇa doesn't separate them, and the tiebreak falls to strength — where V01, marked `established` in the knowledge base, outweighs V11, marked `hypothesis`. V01's argument goes IN; V11's goes OUT.

**The epistemic standing of the rules decided the dispute.** Not a similarity score, not a vote, not the model's preference. If a domain expert later downgrades V01 to `hypothesis` or upgrades V11 to `established`, the outcome flips, and it flips because a human changed a documented field — not because a model changed its mind.

And `not_value_creation` lands on **CONTESTED**, which is not the same as false. It means: arguments for this existed and were defeated. That distinction is preserved and reportable.

Now change the facts. Ask about a company that is growing with coordination overhead but says *nothing* about unit economics:

```
accepted = [organizational_growth, coordination_overhead,
            distorted_market_signal, not_value_creation]
extension_size = 4
```

`not_value_creation` is now **accepted**. V01 never fired — there was no claim of positive unit economics for it to fire on — so nothing contested V11 and it stands unopposed. The chain also ran forward on its own: growth produced coordination overhead (V04), which produced distorted market signals (V05).

Same knowledge base, opposite conclusion, and the difference is entirely in the facts supplied. **The engine has no opinion about growth. It has rules, and the rules have scope.**

## 6. When a rule doesn't apply

The third attack type is the quietest and the most useful.

Ask about resource allocation for a company that has identified its binding constraint. V02 fires: `binding_constraint_identified → resource_allocation_effective`. Fine.

Now add one fact — the company's work is *highly parallel*:

```
undercutting  savyabhicara:  inapplicable_V02  -->  A0002  [out]

resource_allocation_effective  →  CONTESTED
```

V02 lists `highly_parallel_system` in its `scope_exclusions`. The moment that predicate appears, the engine constructs an argument whose sole conclusion is *"V02 does not apply here"* and points it at every argument built on V02. The conclusion goes OUT.

This is **savyabhicāra** — the inconstant reason. And note it is not an attack on the *conclusion*; it is an attack on the *inference*. The engine is not claiming resource allocation is ineffective. It is claiming that the theory-of-constraints rule has nothing to say about a system with no serial bottleneck, which is exactly right and exactly what a careful domain expert would say.

Undercutting attacks always succeed. There is no preference comparison, because a rule that doesn't apply doesn't get to argue about strength.

The scope exclusion in the YAML is not documentation. It is an executable boundary.

## 7. What would change your mind

Here is the capability that is hardest to get any other way.

A user asks whether resource allocation is effective, having said only that unit economics are positive:

```
status = None      nothing derives it
```

An honest "I can't conclude that." But the engine can say more, because it can read its own rules:

```
rule V02 (The Constraint Cascade) concludes resource_allocation_effective
  requires : [binding_constraint_identified]
  missing  : [binding_constraint_identified]
  excluded if: [highly_parallel_system]
```

*"I need one more thing: have you identified your binding constraint? And if your system is highly parallel, don't bother — this rule won't apply."*

Supply it:

```
resource_allocation_effective → HYPOTHESIS  via V02        [0.1 ms]
```

Supply the exclusion as well:

```
resource_allocation_effective → CONTESTED, argument OUT    [0.1 ms]
  undercut: inapplicable_V02 → A0004  (savyabhicara)
```

Any language model will answer "what would change your mind?" with something plausible. **What it cannot do is guarantee that supplying the named fact actually changes the output** — there is no mechanism binding its explanation to its computation.

Here the explanation *is* the computation. You add the premise, the extension is recomputed, and the label flips in a tenth of a millisecond. If it doesn't flip, the explanation was wrong and you find out immediately, for free.

That is what an answer with an address looks like. You can disagree with `V02`, or with the scope exclusion, or with the fact — and each of those is a different, specific, checkable disagreement.

## 8. Where the knowledge comes from, and how far to trust it

Eleven rules per domain is small enough to author by hand, and the business-strategy base was. But hand-authoring doesn't scale across domains, so there are three other routes in, each recorded on the rule itself:

- **`CURATED`** — hand-authored
- **`GUIDE_EXTRACTED`** — extracted offline from a written guide by a five-stage pipeline that pulls candidate predicates from prose, decomposes them, canonicalises synonyms, assembles rules, and validates the result for cycles and Datalog-compilability
- **`LLM_PARAMETRIC`** — generated at query time when coverage declines but the domain's framework still seems applicable, using existing rules as structural templates
- **`WEB_SOURCED`** — designed, not yet built: retrieve documents, extract with verbatim citations, validate, merge

The design intent is that origin should bound status: a conclusion resting entirely on machine-generated rules must not be reportable as `established`, however the arithmetic lands. Today that bound is a confidence cap on an input rather than a ceiling on the output, which is weaker than it sounds and is on the list to fix.

**Three things should temper how much any current output is trusted.**

*The extraction step is unmeasured.* Everything downstream consumes whatever the extraction pipeline produces, and its accuracy has never been measured — because the harness built to measure it scores a predicate and its exact negation as a perfect match, and would grade an extractor that inverted every answer at 100%. That instrument is being replaced before any extraction number is reported. Nothing here claims extraction is bad; the claim is that the system cannot presently tell you.

*The status arithmetic is wrong in the way §4.5 showed*, and is being removed rather than tuned.

*The citations are well-formed and unverified.* Every one of the knowledge base's 22 source identifiers resolves to an entry in a reference bank, and those entries are real, specific, and annotated — *"Ries, E. (2011). The Lean Startup. Crown Business."* But the bank contains zero DOIs, zero ISBNs, and zero URLs, so nothing in the pipeline can confirm the work exists, and nobody has confirmed the book says what the annotation claims. The chain is intact in *shape* and unverified in *fact*, and the honest status of every rule in the knowledge base is therefore "cited, unchecked."

## 9. What it is for

The engine does not make a language model smarter. It changes what kind of object an answer is.

An LLM answer is a paragraph. This engine's answer is a graph with a paragraph attached: a set of arguments, the attacks between them, which survived and why, what each one rests on, and what would have to change for the outcome to differ. The paragraph is a rendering of the graph, and the graph exists whether or not you read the paragraph.

Four things follow from that, and they don't follow from a better model:

**Disagreement gets an address.** Not "the AI is wrong" but "V02's scope exclusion shouldn't include parallel systems" — a claim a domain expert can adjudicate without knowing anything about machine learning.

**The reasoning is re-derivable.** Given the same knowledge base and the same grounded predicates, the graph, labels, and conclusions are identical every time, with no model in the loop. Someone who disputes a conclusion can recompute it themselves in milliseconds.

**Refusal is structural.** Three different ways of not knowing — no coverage, undecided, contested — with different causes and different remedies, instead of one undifferentiated hedge.

**The knowledge is a maintainable artifact.** Rules can be versioned, reviewed, deprecated, and argued about, by people who are experts in the domain rather than in the system.

None of that requires the model to be more capable. It requires the reasoning to be somewhere you can point at — which is the thing this engine, however unfinished, actually is.

---

*The Nyāya tradition held that a claim earns its standing by surviving structured challenge, and that the honest response to insufficient reason is to say so. Both of those are now enum values.*
