# Auditing the extraction harness, and what it can and cannot measure

**Date:** 2026-08-17
**Subject:** `anvikshiki_ecosystem` at `ccd4b08` (working tree dirty under `backend/` and `webapp/`; untouched by this work).
**Method:** every claim below was produced by running code in the repo's own `.venv`. Where a number appears, the command that produced it is reproducible from the repo root.

**Verdict: NOT TRUSTWORTHY.** Per the task's own gate, no extraction score is reported. Part B was not run. The reasons are in Part A; the strongest single one is that the matcher scores a predicate and its exact logical negation as a perfect match, so an extractor that inverted every gold predicate would be graded **precision 1.000, recall 1.000**.

---

## 0. State check, before anything else

The task said to expect 263 passed / 4 failed and to say so if the number differed. Run exactly as specified:

```
.venv/bin/python -m pytest anvikshiki_v4/tests -q
→ 4 failed, 263 passed in 82.53s
```

All four failures are `TestLivePipeline`, caused by the retired `gemini-2.0-flash`. That matches the stated expectation. Not bumped, as instructed.

One thing worth flagging, because it bit me before I read the task carefully. An earlier invocation from the same shell reported **263 passed, 4 skipped in 7.4s** — the live tests silently vanished rather than failing. The cause is not flakiness:

```python
# .venv/lib/python3.14/site-packages/litellm/__init__.py:82
dotenv.load_dotenv()
```

`litellm` loads `.env` as an import side effect, walking up from the current working directory. `test_engine_v4_l3.py:712` then reads `os.environ["GOOGLE_API_KEY"]` at module import to decide `LLM_AVAILABLE`, and `@pytest.mark.skipif` consumes it. Observed directly:

```
cwd=repo root   after `import dspy`:  GOOGLE_API_KEY present: True
cwd=/tmp        after `import dspy`:  GOOGLE_API_KEY present: False
```

So **whether these four tests fail or silently skip depends on the directory pytest was launched from.** That is not a finding about extraction, but it is a finding about the suite as an instrument: a run from the wrong directory reports green and looks like a pass. It also means API credentials *are* available in-process from the repo root, which is why Part B was runnable in principle and why the decision not to run it is a deliberate one rather than a blocked one.

---

## Part A — audit of the instrument

### A1. Where does the gold set come from?

**Finding: there is no gold set in use. The only gold artefact in the repo is loaded by nothing.**

`anvikshiki_v4/tests/fixtures/expected_predicates.yaml` contains 14 hand-shaped predicates for Chapter 2, with descriptions, claim types and section numbers. Its header says:

> `# Used by test_predicate_extraction.py for precision/recall evaluation.`

That sentence is false. Searching all 51 non-vendored Python files:

```
references to "expected_predicates"  = 0   (py files examined = 51)
```

Nothing opens it. `test_predicate_extraction.py` never reads the fixtures directory at all. Every precision/recall test in the suite uses inline toy literals — `predicate_precision(["a","b"], {"a","b"})`. Likewise `ExtractionEvaluator` is instantiated in exactly two places, both inside that test file, and `optimize_pipeline` / `build_dspy_metric` are never invoked anywhere in the repo. **The harness has never been pointed at real extractor output.**

So the honest answer to "is the gold produced by the component being graded?" is: today, no — because nothing is graded. But the question deserves a second, forward-looking answer, because the loop is latent in the design rather than absent from it.

**The HITL reviewer cannot produce a gold set, and wiring it in as one would create exactly the loop the task warns about.** `HITLReviewer.__init__` builds its worklist from `stage_d.new_vyaptis + stage_d.refinement_vyaptis` — the extractor's own proposals. The interface offers accept / reject / modify / quit. There is no operation that adds an item the extractor *failed to propose*. Its output, via `apply_decisions()` and `export_approved_yaml()`, is an approved `KnowledgeStore` — a KB, not a gold set — and no code path carries it back to `ExtractionEvaluator`.

The consequence is structural: any gold derived from HITL output is a subset of extractor output. Recall measured against it is pinned at or near 1.0 by construction, and would report "the extractor missed nothing" no matter how much it missed. Precision would become a measure of reviewer agreement, which is worth something, but not the thing the metric is named after. **The reviewer is a filter on false positives. It is structurally incapable of measuring false negatives, which is what recall is for.**

On the provenance of the fixture itself, I could not establish authorship — it arrives whole in the initial squashed commit. Two triangulations argue it was hand-authored rather than machine-derived, and I report them as circumstantial rather than conclusive:

- `gold ∩ business_expert.yaml vocabulary = 0 of 14`. It was not back-derived from the KB.
- **0 of 14** gold names appear literally in the prose they are gold for. These are conceptual labels a human assigned (`imagined_economies_of_scale` for a passage about false scale assumptions), not strings lifted from text.

A third observation cuts the other way, and matters for anyone who later tries to use this fixture as a benchmark. `guide_ch2_excerpt.md` is **not** an excerpt of `guides/business_expert/guide_ch2.md`. It is 3,776 characters against the real chapter's 16,211 (23%), and none of its substantial paragraphs appear in the real chapter. It is separately written prose, authored alongside its own answer key. Measuring against it would answer "can the extractor find concepts a human deliberately planted in a 73-line toy", not "how does extraction perform on this corpus". That is a milder problem than self-grading, but it is not a benchmark either.

### A2. What does the soft matching admit?

**Finding: the matcher is Jaccard overlap on underscore-split tokens with a 0.5 threshold, it is blind to negation and to argument order, and the semantic matcher the docs promise does not exist.**

The threshold is the default `threshold: float = 0.5` on `_best_match_score` (`extraction_eval.py:61`), used unchanged by `predicate_precision`, `predicate_recall`, `ExtractionEvaluator` and `build_dspy_metric`.

First, the documentation gap. The module docstring says "Uses BERTScore for soft predicate matching" and `_token_overlap`'s own docstring calls itself a "BERTScore fallback when sentence-transformers is unavailable". `docs/predicate_extraction_design.md:263` repeats the claim. Searching the package:

```
bertscore / sentence_transformers implementation hits = 0
(the only 2 hits are the two docstrings that promise it)
```

There is no fallback, because there is nothing to fall back *from*. The crude path is the only path, and it is described everywhere as the degraded one.

The task asked for two constructed cases. Here are seven, run through the real function:

```
0.500  MATCH   ltv_exceeds_cac          ~ ltv_above_cac                SHOULD match (synonym)
1.000  MATCH   short_payback_period     ~ payback_period_short         SHOULD match (reorder)
0.500  MATCH   positive_unit_economics  ~ negative_unit_economics      should NOT match (antonym)
0.667  MATCH   value_creation           ~ not_value_creation           should NOT match (negation)
0.500  MATCH   high_retention_rate      ~ high_churn_rate              should NOT match (inverse)
0.600  MATCH   economies_of_scale_real  ~ imagined_economies_of_scale  should NOT match (opposites)
1.000  MATCH   ltv_exceeds_cac          ~ cac_exceeds_ltv              should NOT match (reversed)
```

The should-match cases pass, but note that the synonym case lands at exactly 0.500 against a `>= 0.5` threshold — the intended behaviour is sitting on the boundary, and a one-token change in either name drops it to zero. The headroom is nil.

The should-not-match cases all pass too, and they are not exotic. `economies_of_scale_real` and `imagined_economies_of_scale` are **both entries in the repo's own gold fixture**, deliberately authored as a contrast pair, and the matcher cannot tell them apart. `ltv_exceeds_cac` vs `cac_exceeds_ltv` scores a perfect 1.000, because bag-of-tokens discards the relation the predicate exists to express.

Pushing this to its conclusion — an extractor that emits the exact logical inverse of every gold predicate:

```
gold      = [economies_of_scale_real, ltv_exceeds_cac, positive_unit_economics, value_creation]
extracted = [imagined_economies_of_scale, cac_exceeds_ltv, negative_unit_economics, not_value_creation]

precision = 1.000
recall    = 1.000
```

**A maximally wrong extractor scores perfectly.** This is not a threshold that wants tuning; a matcher this loose inflates precision and recall together, which is the specific failure mode that looks like a good result and cannot be caught by staring at the aggregate.

There is a sharp internal contradiction here that makes the defect hard to write off as a known approximation. `t2_compiler_v4._are_contrary()` treats `X` and `not_X` as **contradictory** — that is the trigger for the rebutting attacks the whole argumentation layer is built on. `extraction_eval._token_overlap()` scores the same pair **0.667, a match**. Two modules in one package hold opposite beliefs about the same string pair, and the engine's core semantics side against the evaluator.

### A3. Are the composite weights justified?

**Finding: asserted, never derived.**

The weights (precision 0.20, recall 0.20, naming 0.15, completeness 0.15, dag_valid 0.10, coverage 0.10, zero_section 0.10) appear in exactly two places: the `ExtractionEvaluator` docstring and a restating table at `docs/predicate_extraction_design.md:253`. Grepping all 43 markdown files under `theory/`, `docs/` and `discussions/` turns up no derivation, no ablation, no sensitivity analysis, no argument for why correctness should be 40% of the score and formatting 15%.

Report the components separately. The composite is uninterpretable — and worse than merely uninterpretable, because 50% of its mass sits on components that measure whether output is *well-formed* rather than whether it is *right*. `naming` + `completeness` + `dag_valid` + `zero_section` total 0.50, and an extractor can max all four while extracting nonsense, as long as the nonsense is snake_case, acyclic, fully-populated and present in every section.

### A4. What happens on empty input?

**Finding: most metrics degrade safely to 0.0. One does not, and it is the one that reads as a pass.**

```
predicate_precision([], gold)        = 0.0
predicate_recall([], gold)           = 0.0
predicate_precision(['x'], set())    = 0.0
predicate_recall(['x'], set())       = 0.0
naming_quality([])                   = 0.0
vyapti_completeness(StageDOutput())  = 0.0
zero_section_rate(StageAOutput())    = 0.0
dag_validity(ValidationResult())     = 1.0   ← default, never-run validation
```

`dag_validity` is `1.0 if not validation.cycle_errors else 0.0`. An empty error list means "no cycles found", and a validation that never ran also has an empty error list. The two are indistinguishable. Note that `ValidationResult()` defaults to `is_valid=False` — so **the object asserts it is not valid, and `dag_validity` scores it 1.0 anyway.** The function does not consult the field that would tell it.

This is not hypothetical. `extraction_hitl.main()` — the CLI entry point — constructs `validation = ValidationResult(is_valid=True)` as a hardcoded literal at line 357, never running validation at all. Anything downstream reading DAG validity off that object gets a free 1.0.

The composite on a wholly empty run is **0.1000**, and every point of it comes from `dag_valid`. That is not high enough to read as a pass on its own, so the degenerate case is not catastrophic in isolation. It matters because it is a floor of unearned credit that rises with the weight of the well-formedness half of the metric.

### A5. Does anything test the evaluator?

**Finding: yes, and this is the harness's strongest point — but the tests cannot catch the defects above, and one of them encodes the circularity in miniature.**

`test_predicate_extraction.py` carries roughly 20 test methods across `TestTokenOverlap`, `TestBestMatchScore`, `TestPredicatePrecisionRecall`, `TestNamingQuality`, `TestVyaptiCompleteness`, `TestDAGValidity`, `TestZeroSectionRate` and `TestCompositeEvaluator`. That is more than most evaluation code gets, and the empty-input cases are genuinely covered (`predicate_precision([], {"a"}) == 0.0`, `naming_quality([]) == 0.0`).

But every input is a toy literal chosen to confirm the arithmetic — `"a"`, `"b"`, `"foo_bar"`, `"baz_qux"`. `TestTokenOverlap::test_no_overlap` asserts `_token_overlap("foo_bar","baz_qux") == 0.0`, which tests that disjoint token sets score zero. No test asks whether *semantically opposite* names score zero, which is the question that matters, and the answer to which is no. The tests verify the implementation computes Jaccard correctly. They never ask whether Jaccard is the right thing to compute.

And `TestCompositeEvaluator::test_perfect_extraction` does this:

```python
gold = {c.name for c in sample_stage_a.candidates}   # gold ← the prediction
...
assert metrics["precision"] == 1.0
assert metrics["recall"] == 1.0
```

Gold is defined as the extracted set, then perfect scores are asserted. It cannot fail for any implementation that isn't outright broken. It is a tautology with a test name that reads like a capability claim — the self-grading loop, present in the test suite in miniature, even though the production path that would create it does not yet exist.

### Verdict

**NOT TRUSTWORTHY.** Ranked by how badly each would distort a reported number:

1. **The matcher is blind to negation and argument order.** Inverted output scores 1.000/1.000. This alone voids any precision or recall figure the harness produces.
2. **No gold set is wired in, and the one that exists is unreferenced by all 51 Python files** — while its own header claims otherwise. There is no measurement to trust or distrust; there is no measurement.
3. **The only mechanism that could produce gold (HITL) is structurally incapable of it**, because the reviewer never sees what the extractor missed. Wiring it in naively manufactures the self-confirming loop.
4. **The composite is uninterpretable** — weights asserted, never derived, with half the mass on well-formedness rather than correctness.
5. **`dag_validity` returns 1.0 for a validation that never ran** and contradicts that object's own `is_valid=False`.
6. **The documented semantic matcher does not exist**, and the crude path is described throughout as the fallback from something that was never built.

Per the task's gate, Part B is not run and no score is reported.

---

## Pre-registration for Part B — recorded, not executed

Written now and left in place deliberately, so that a future run cannot be registered after the fact. **Nothing below was executed. There is no number in this document, and any number later attributed to it is fabricated.**

Had Part A permitted a run, this is what I had committed to:

**Corpus and denominator.** `guides/business_expert/guide_ch2.md` — the real chapter, 16,211 characters — against the 14 hand-authored gold predicates in `expected_predicates.yaml`. Denominator for recall: **14**. Denominator for precision: however many candidates Stage A returns, printed before scoring. The 73-line `guide_ch2_excerpt.md` would have been run as a **separate** measurement and reported separately, never merged, because as established in A1 it is prose authored alongside its own answer key and would flatter the result.

**Expectation.** Recall between 0.4 and 0.7. The gold names are conceptual rather than lexical — 0 of 14 appear literally in the prose — so the extractor has to invent matching labels, and the token matcher then has to accept them. Precision I could not have predicted with a straight face, because it depends on how many candidates Stage A emits, and nothing in the repo records a typical count.

**What would have meant unreliable.** The task's kill criteria, adopted unchanged: recall < 0.5, or precision < 0.5, or either control failing.

**Controls.** Positive: `positive_unit_economics` and `value_creation` are V01's own antecedent and consequent, they are in the KB the pipeline is seeded with, and Chapter 2 is *about* them — if those come back missed, the run is void. Negative: a passage of prose containing no extractable domain claim (the chapter's opening narrative paragraph, or a stretch of `stage3_reference_bank.md` bibliography), where any output at all is a false positive.

**A note on the negative control, in hindsight.** The A2 inversion experiment functioned as a negative control on the *instrument* rather than the extractor — feed the harness input that is definitively wrong and see whether it says so. It said 1.000/1.000. That control failed, which is what closes Part A. It is worth recording that the instrument-level control was cheap, took one function call, and was more informative than the extractor-level run would have been.

---

## Part B — not run

Gated by Part A. A precision/recall pair from this harness would be quoted later without its caveats, and the number would be indefensible, because the matcher underneath it cannot distinguish a correct extraction from its exact opposite.

What would unblock it, in order:

1. **Replace or gate the matcher.** Minimum viable fix: refuse a match when the two names disagree on a polarity token (`not_`, `negative`/`positive`, `imagined`/`real`, `exceeds`/`below`) or when they share a token multiset but differ in order. Better: an embedding matcher, which is what the docs already claim exists. Either way the fix must be tested against the seven pairs in A2, not against `foo_bar`/`baz_qux`.
2. **Wire the gold fixture to something**, and correct or delete its false header comment.
3. **Report components, not the composite**, until the weights are derived or abandoned.
4. **Give the HITL reviewer an "add missed predicate" operation**, without which no gold it produces can support a recall figure.

Items 1 and 2 are small. Item 4 is the one that decides whether this harness can ever measure recall.

---

## Part C — portability to a different extraction task

The second system extracts *claims made in a working session* rather than *predicates from domain prose*. Splitting the harness by what survives that change:

**General — portable as shapes, not as code.** The precision/recall machinery is standard set-comparison over string identifiers; nothing in `predicate_precision` or `predicate_recall` knows what a predicate is. The three-way structure of the composite (correctness / well-formedness / coverage) is a reasonable frame for any extraction task. The accept-reject-modify review loop is domain-neutral. But "portable as shapes" is the honest phrasing: these are twenty-line functions whose value is in the interface decisions, and copying them saves an afternoon. **The reason to borrow this is not the code.**

**Specific — does not transfer.** `naming_quality` encodes snake_case and a hardcoded generic-name blocklist, both artefacts of predicates being Datalog symbols. `vyapti_completeness` counts seven named fields of a `ProposedVyapti` — antecedents, consequent, scope conditions, confidence — a schema with no analogue in session claims. `dag_validity` and `zero_section_rate` presuppose an acyclic rule graph and a document partitioned into sections; a session transcript has neither a DAG nor sections, though turns might substitute for the latter. That is 0.50 of the composite weight gone, which is another way of seeing that the composite is not a real quantity.

**The matcher does not transfer either, and would fail worse.** Jaccard on underscore-split tokens works at all only because predicates are `snake_case_identifiers` with meaningful token boundaries. Session claims are natural-language sentences. Token overlap between two sentences is dominated by function words, and the negation blindness demonstrated in A2 gets *more* dangerous, not less — "the user approved the migration" and "the user did not approve the migration" share almost every token. Any adopting system needs a real semantic matcher from day one, and inherits none of that from here.

**Is the HITL reviewer the load-bearing piece?** This is the right question and the answer is a qualified yes — qualified in a way that changes what should be borrowed.

The genuinely valuable idea is the one implied by the architecture: a human produces the gold through a batch review interface, which is the only thing in the whole design that breaks the self-grading circle. That idea transfers completely and is worth more than every metric in `extraction_eval.py` combined.

But **the implementation as written does not embody the idea, and copying it would propagate the defect.** `HITLReviewer` reviews only what the extractor proposed. It is a precision instrument — it finds false positives and removes them — and it is blind to false negatives by construction. A system that adopts it will be able to say "of what we extracted, this fraction was right" and will never be able to say "of what was there, this fraction was found". For session-claim extraction, missed claims are almost certainly the more costly error: an invented claim is visible and gets challenged, a claim that was made and never captured is silently absent.

So the recommendation is: **borrow the batch-review pattern, but design the review UI around the source material rather than around the extractor's output.** Show the reviewer the session turn (or the prose section) with the extracted claims beside it, and make "there is a claim here that was missed" a first-class action. That is a different interface from the one in this file — it is anchored on the corpus, not on the candidate list — and it is the version that can produce a gold set worth measuring recall against. Everything else here is cheaper to rewrite than to port.

---

## What I did not check, and what would change the conclusion

**Not checked.** I never ran `PredicateExtractionPipeline` end to end — no Stage A through E execution, no LLM extraction calls, so I have no evidence about extraction quality in either direction. Nothing in this document says extraction is bad; it says the instrument cannot tell you. I did not read the 1,123 lines of `predicate_extraction.py` beyond its stage boundaries and the two helpers the evaluator imports. I did not examine `traces/` as candidate fixtures. I did not assess Stage C's deduplication, which uses a separate 0.85 cosine threshold and may have its own matching semantics. I did not review `extraction_schema.py` beyond `ValidationResult` and `ExtractionConfig`. Per the non-goals I left the retired model, the two known algebra bugs, and `backend/`+`webapp/` alone.

**What would change the conclusion.** The verdict rests on the matcher, and it would move if any of these turned out true:

- *A real semantic matcher exists somewhere I did not look.* I searched for `bertscore` and `sentence_transformers` across all non-vendored Python and found only the two docstrings promising them. If a matcher lives outside the package or in an unmerged branch, finding A2 weakens to a packaging problem.
- *The 0.5 threshold is not what production would use.* I took it from the default arguments, and no caller overrides it. A deliberately higher threshold would narrow but not close the gap — `ltv_exceeds_cac` vs `cac_exceeds_ltv` scores **1.000**, so no threshold whatsoever excludes it. Order-blindness is not a tuning problem.
- *The gold fixture is used by tooling outside this repo.* I established it is referenced by zero of 51 Python files here. An external consumer would change A1's "no measurement exists" to "the measurement lives elsewhere and was not audited", which is a materially different report.
- *Someone intends the composite as a rough optimizer signal, not a quality claim.* That is a defensible use for `build_dspy_metric` — a MIPROv2 reward does not need to be interpretable. It would soften A3 considerably. It would not soften A2, because an optimizer steered by a negation-blind reward learns to satisfy the reward.

The one finding that survives all four is A2. A matcher that scores a predicate and its negation as identical cannot ground a precision or recall claim, and that is the whole reason this document reports no number.
