#!/usr/bin/env python3
"""
Reproduce GLM-5 content vs reasoning_content discrepancy.

Single call with response_format=json_object — reliably puts JSON
in reasoning_content and leaves content empty.
"""

import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_KEY = os.environ.get("DEEPINFRA_API_KEY")
if not API_KEY:
    print("ERROR: DEEPINFRA_API_KEY not set in .env")
    sys.exit(1)

BASE_URL = "https://api.deepinfra.com/v1/openai"
MODEL = "zai-org/GLM-5"

# ── Exact DSPy-generated ExtractPredicates prompt (captured from e2e trace) ──

SYSTEM_PROMPT = """Your input fields are:
1. `section_text` (str): A section of guide text (markdown)
2. `chapter_id` (str): Chapter identifier, e.g. 'ch02'
3. `existing_predicates` (str): Already-known predicates from the knowledge store
4. `domain_context` (str): Domain type and brief description
Your output fields are:
1. `reasoning` (str): Step-by-step: what causal/conditional claims does this text make?
2. `predicates` (list[str]): Extracted predicate names in snake_case. Empty list if none.
3. `descriptions` (list[str]): One-sentence description for each predicate, same order.
4. `claim_types` (list[str]): Claim type for each: causal, conditional, metric, definitional, scope, negation
5. `related_vyaptis` (list[str]): Related existing vyapti ID for each (or 'none')
All interactions will be structured in the following way, with the appropriate values filled in.

Inputs will have the following structure:

[[ ## section_text ## ]]
{section_text}

[[ ## chapter_id ## ]]
{chapter_id}

[[ ## existing_predicates ## ]]
{existing_predicates}

[[ ## domain_context ## ]]
{domain_context}

Outputs will be a JSON object with the following fields.

{
  "reasoning": "{reasoning}",
  "predicates": "{predicates}        # note: the value you produce must adhere to the JSON schema: {\\"type\\": \\"array\\", \\"items\\": {\\"type\\": \\"string\\"}}",
  "descriptions": "{descriptions}        # note: the value you produce must adhere to the JSON schema: {\\"type\\": \\"array\\", \\"items\\": {\\"type\\": \\"string\\"}}",
  "claim_types": "{claim_types}        # note: the value you produce must adhere to the JSON schema: {\\"type\\": \\"array\\", \\"items\\": {\\"type\\": \\"string\\"}}",
  "related_vyaptis": "{related_vyaptis}        # note: the value you produce must adhere to the JSON schema: {\\"type\\": \\"array\\", \\"items\\": {\\"type\\": \\"string\\"}}}"
}
In adhering to this structure, your objective is:
        Extract domain predicates from instructional text.

        A predicate is a testable property of a domain entity.
        Look for: causal claims ("X causes Y"), conditional statements ("if X then Y"),
        metric relationships ("X is measured by Y"), and scope conditions.
        Use ONLY snake_case names. Return empty list if no predicates found.
        Extract NEW predicates not already in the existing set."""

USER_PROMPT = """[[ ## section_text ## ]]
### ─── Where the Map Ends ───

Everything through Chapter 10 represents established knowledge — frameworks and principles that, while debatable at the margins, are grounded in decades of research, practitioner experience, and empirical validation. This chapter is different. This chapter is about the questions that the experts themselves disagree on, where the evidence is genuinely ambiguous, and where your judgment as a practitioner must operate without settled ground.

The Frontier chapter exists for two reasons. First, intellectual honesty: the guide would be incomplete — and dangerously overconfident — if it presented business reasoning as a domain of settled knowledge with no open questions. Second, practical utility: as an AI startup founder, you are operating directly at the frontier. The contested questions below are not abstract — they are the strategic terrain you navigate daily.

**[DECAY WARNING]:** More than any other chapter, this one is time-sensitive. The contested questions described here are contested as of the guide's writing (2024–2026 knowledge base). Some may have been resolved by the time you read this. For each question, we provide monitoring criteria — specific evidence that would shift the balance toward one side.

---

[[ ## chapter_id ## ]]
ch11

[[ ## existing_predicates ## ]]
EXISTING PREDICATES (extract NEW sub-predicates, not these):
  V01: positive_unit_economics -> value_creation
  V02: binding_constraint_identified -> resource_allocation_effective
  V03: superior_information -> pricing_power
  V04: organizational_growth -> coordination_overhead
  V05: coordination_overhead -> distorted_market_signal
  V06: strategic_commitment -> capability_gain
  V07: incentive_alignment -> organizational_effectiveness
  V08: value_creation, resource_allocation_effective -> long_term_value
  V09: incumbent_rational_allocation, low_margin_market_entrant -> disruption_vulnerability
  V10: calibration_accuracy -> decision_quality
  V11: organizational_growth, coordination_overhead -> not_value_creation

All known: ['binding_constraint_identified', 'calibration_accuracy', 'capability_gain', 'coordination_overhead', 'decision_quality', 'disruption_vulnerability', 'distorted_market_signal', 'incentive_alignment', 'incumbent_rational_allocation', 'long_term_value', 'low_margin_market_entrant', 'not_value_creation', 'organizational_effectiveness', 'organizational_growth', 'positive_unit_economics', 'pricing_power', 'resource_allocation_effective', 'strategic_commitment', 'superior_information', 'value_creation']

[[ ## domain_context ## ]]
Domain: CRAFT.

Respond with a JSON object in the following order of fields: `reasoning`, then `predicates` (must be formatted as a valid Python list[str]), then `descriptions` (must be formatted as a valid Python list[str]), then `claim_types` (must be formatted as a valid Python list[str]), then `related_vyaptis` (must be formatted as a valid Python list[str])."""


if __name__ == "__main__":
    from openai import OpenAI
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    print("=" * 80)
    print("  GLM-5 DISCREPANCY REPRODUCER — single call")
    print(f"  Model: {MODEL}")
    print(f"  response_format: json_object  (this is what triggers the bug)")
    print("=" * 80)

    # ── Print full input ──
    print(f"\n{'─'*80}")
    print("  INPUT")
    print(f"{'─'*80}")
    print(f"  model:           {MODEL}")
    print(f"  temperature:     0.7")
    print(f"  response_format: {{'type': 'json_object'}}")
    print(f"  max_tokens:      4096")
    print(f"\n  ── SYSTEM MESSAGE ({len(SYSTEM_PROMPT)} chars) ──")
    print(SYSTEM_PROMPT)
    print(f"\n  ── USER MESSAGE ({len(USER_PROMPT)} chars) ──")
    print(USER_PROMPT)
    print(f"{'─'*80}")
    sys.stdout.flush()

    # ── Call API ──
    t0 = time.time()
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        max_tokens=4096,
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    dt = time.time() - t0

    msg = resp.choices[0].message
    content = msg.content or ""
    extra = getattr(msg, "model_extra", {}) or {}
    reasoning = extra.get("reasoning_content", "")
    answer_in = "content" if content else ("reasoning_content" if reasoning else "empty")

    # ── Print full output ──
    print(f"\n{'─'*80}")
    print(f"  OUTPUT — answer landed in: {answer_in} — {dt:.1f}s")
    print(f"{'─'*80}")
    print(f"  finish_reason: {resp.choices[0].finish_reason}")
    print(f"  usage:         {resp.usage}")

    print(f"\n  ── content ({len(content)} chars) ──")
    if content:
        print(content)
    else:
        print("  (empty)")

    print(f"\n  ── reasoning_content ({len(reasoning)} chars) ──")
    if reasoning:
        print(reasoning)
    else:
        print("  (empty)")

    # ── Verify the reasoning_content is valid JSON ──
    source = reasoning if not content else content
    if source:
        print(f"\n{'─'*80}")
        print(f"  JSON PARSE CHECK on {answer_in}")
        print(f"{'─'*80}")
        try:
            parsed = json.loads(source)
            print(f"  Valid JSON: YES")
            print(f"  Keys: {list(parsed.keys())}")
            if "predicates" in parsed:
                print(f"  predicates: {parsed['predicates']}")
        except json.JSONDecodeError as e:
            print(f"  Valid JSON: NO — {e}")

    print(f"\n{'='*80}")
    print(f"  VERDICT: answer_in={answer_in}, content={len(content)} chars, reasoning_content={len(reasoning)} chars")
    if not content and reasoning:
        print(f"  BUG CONFIRMED: response_format=json_object causes GLM-5 to put")
        print(f"  the JSON answer in reasoning_content, leaving content empty.")
        print(f"  DSPy reads only content → gets empty string → retries forever.")
    print(f"{'='*80}")
