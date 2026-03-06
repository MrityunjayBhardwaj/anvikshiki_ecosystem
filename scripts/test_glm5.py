#!/usr/bin/env python3
"""
Test GLM-5 via DeepInfra with 3 prompt sizes:
  1. Simple (short) — "What is 2+2?"
  2. GroundQuery (medium) — exact DSPy GroundQuery prompt
  3. T2b-style (long) — ~1500 token chapter section for predicate extraction

Checks where GLM-5 puts its output: content vs reasoning_content.
"""

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


def call_glm5(label, system_msg, user_msg, temperature=0, max_tokens=1024):
    """Call GLM-5 and report where the output lands."""
    from openai import OpenAI
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"  system: {len(system_msg)} chars | user: {len(user_msg)} chars")
    print(f"{'='*70}")

    t0 = time.time()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    elapsed = time.time() - t0

    choice = response.choices[0]
    msg = choice.message
    extra = getattr(msg, "model_extra", {}) or {}
    content = msg.content or ""
    reasoning = extra.get("reasoning_content", "")

    print(f"\n  Time: {elapsed:.1f}s")
    print(f"  finish_reason: {choice.finish_reason}")
    print(f"\n  content ({len(content)} chars):")
    if content:
        print(f"    {repr(content[:500])}{'...' if len(content) > 500 else ''}")
    else:
        print(f"    (empty)")
    print(f"\n  reasoning_content ({len(reasoning)} chars):")
    if reasoning:
        print(f"    {repr(reasoning[:500])}{'...' if len(reasoning) > 500 else ''}")
    else:
        print(f"    (empty)")

    where = "content" if content else ("reasoning_content" if reasoning else "nowhere")
    print(f"\n  >> Answer landed in: {where}")

    return content, reasoning


# ── TEST 1: Simple (short) ──

def test_simple():
    return call_glm5(
        "TEST 1: Simple prompt (short)",
        "You are a helpful assistant. Reply concisely.",
        "What is 2 + 2? Reply in one word.",
        max_tokens=256,
    )


# ── TEST 2: GroundQuery (medium ~2K chars) ──

def test_groundquery():
    system = """Your input fields are:
1. `query` (str): User's natural language question
2. `ontology_snippet` (str): Valid predicates and rules
3. `domain_type` (str): Domain classification
Your output fields are:
1. `reasoning` (str): Step-by-step reasoning
2. `predicates` (list[str]): Structured predicates
3. `relevant_vyaptis` (list[str]): Relevant vyapti IDs

Outputs will be a JSON object:
{
  "reasoning": "...",
  "predicates": ["pred(entity)", ...],
  "relevant_vyaptis": ["V01", ...]
}"""

    user = """[[ ## query ## ]]
Does Acme Corp have good unit economics and efficient resource allocation?

[[ ## ontology_snippet ## ]]
RULE V01: IF positive_unit_economics THEN value_creation
RULE V02: IF binding_constraint_identified THEN resource_allocation_effective
RULE V08: IF value_creation, resource_allocation_effective THEN long_term_value

VALID PREDICATES: positive_unit_economics, binding_constraint_identified,
value_creation, resource_allocation_effective, long_term_value

[[ ## domain_type ## ]]
CRAFT

Respond with JSON."""

    return call_glm5("TEST 2: GroundQuery prompt (medium ~2K chars)", system, user)


# ── TEST 3: T2b-style (long ~4K chars) ──

def test_t2b():
    system = """You are a predicate extraction engine. Given a section of instructional text,
extract causal and conditional predicates. Return a JSON object:
{
  "predicates": [
    {"name": "predicate_name", "type": "causal|conditional|metric", "evidence": "quote from text"}
  ],
  "reasoning": "step-by-step explanation"
}
Use only snake_case predicate names. Extract ALL causal relationships."""

    section = """Unit economics is the fundamental building block of business analysis.
The core transaction reveals the DNA of a business model. If a company generates more
revenue per unit than it costs to produce that unit, it has positive unit economics.
This is the foundation of sustainable value creation. Companies with negative unit
economics must eventually either improve their margins or cease to exist.

The key metrics are: customer acquisition cost (CAC), lifetime value (LTV),
contribution margin, and payback period. When LTV/CAC > 3, the business model
is generally considered healthy. Below 1, destruction of value occurs with each
additional customer acquired.

Binding constraints determine where resources should flow. In any system with serial
dependencies, the throughput is limited by the slowest component. Identifying this
binding constraint is the first step to effective resource allocation. Pouring resources
into non-binding areas yields diminishing returns — like widening a highway except at
the bottleneck.

Information asymmetry creates pricing power. When a seller knows more about quality
than the buyer, the seller can capture premium pricing. This is particularly true in
heterogeneous quality markets where standardized comparison is difficult. In perfectly
commoditized markets, this advantage disappears.

Organizational growth inevitably increases coordination overhead. As teams scale, the
number of communication pathways grows quadratically. Each additional person adds not
just their productivity but also their coordination burden. Without active structural
intervention — reorganizing teams, delegating authority, building systems — this
overhead will eventually consume all productivity gains.

The relationship between incentive alignment and organizational effectiveness is
nearly isomorphic. When individual incentives align with organizational goals,
effectiveness follows almost mechanically. Misaligned incentives produce predictably
dysfunctional behavior, regardless of stated values or cultural aspirations.

Strategic commitment creates capability but destroys optionality. Every investment
in one direction forecloses alternatives. The optionality-commitment tradeoff is
fundamental: companies must commit deeply enough to build real capabilities while
maintaining enough flexibility to adapt when circumstances change.

Calibration accuracy — the ability to assign correct probabilities to uncertain
outcomes — directly determines decision quality. Overconfident decision-makers
systematically underinvest in hedging and information gathering. Under-confident
ones over-invest in analysis, missing time-sensitive opportunities.

The disruption asymmetry occurs when incumbents rationally allocate resources away
from low-margin segments, creating entry points for disruptors. The incumbent's
behavior is locally optimal but globally vulnerable. This is particularly dangerous
along sustaining innovation trajectories where the incumbent is improving faster
than the market demands."""

    return call_glm5(
        "TEST 3: T2b-style prompt (long ~4K chars)",
        system,
        section,
        max_tokens=2048,
    )


if __name__ == "__main__":
    results = {}

    results["simple"] = test_simple()
    results["groundquery"] = test_groundquery()
    results["t2b"] = test_t2b()

    # ── Summary ──
    print(f"\n{'='*70}")
    print("  SUMMARY: Where does GLM-5 put the answer?")
    print(f"{'='*70}")
    for name, (content, reasoning) in results.items():
        where = "content" if content else ("reasoning_content" if reasoning else "nowhere")
        c_len = len(content)
        r_len = len(reasoning)
        print(f"  {name:15s}  →  {where:20s}  (content={c_len}, reasoning={r_len})")
