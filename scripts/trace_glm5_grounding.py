#!/usr/bin/env python3
"""
Focused GLM-5 Grounding Trace — captures input prompts, reasoning_content, and outputs.

Runs the grounding step directly with GLM-5 via DeepInfra,
then dumps the full trace: input prompt → reasoning_content → parsed output.
"""

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dspy

from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store
from anvikshiki_v4.grounding import GroundQuery, OntologySnippetBuilder

# ── Config ──

API_KEY = os.environ.get("DEEPINFRA_API_KEY")
if not API_KEY:
    print("ERROR: DEEPINFRA_API_KEY not set")
    sys.exit(1)

MODEL_ID = "openai/zai-org/GLM-5"
MODEL_LABEL = "GLM-5 (DeepInfra)"
BASE_URL = "https://api.deepinfra.com/v1/openai"

QUERY = "Does Acme Corp have good unit economics and efficient resource allocation?"

# ── Helpers ──

def hr(char="═", width=80):
    return char * width

def extract_all_history(lm):
    """Extract full details from every LLM call in DSPy history."""
    results = []
    for entry in lm.history:
        resp = entry.get("response")
        content = ""
        reasoning_content = ""
        if resp and hasattr(resp, "choices"):
            for choice in resp.choices:
                msg = choice.message
                content = msg.content or ""
                extra = getattr(msg, "model_extra", {}) or {}
                reasoning_content = extra.get("reasoning_content", "")
        results.append({
            "messages": entry.get("messages", []),
            "content": content,
            "reasoning_content": reasoning_content,
            "outputs": entry.get("outputs", []),
        })
    return results


def main():
    output_lines = []

    def pr(text=""):
        print(text)
        output_lines.append(text)

    t0 = time.time()

    # ── Setup ──
    pr(hr())
    pr(f"  GLM-5 GROUNDING PIPELINE TRACE")
    pr(f"  Model: {MODEL_LABEL}")
    pr(f"  Query: {QUERY}")
    pr(hr())

    lm = dspy.LM(
        MODEL_ID,
        api_key=API_KEY,
        api_base=BASE_URL,
        max_tokens=4096,
    )
    dspy.configure(lm=lm, adapter=dspy.JSONAdapter())
    pr(f"\nDSPy configured: {MODEL_ID}")

    # ── Load KB ──
    kb_path = os.path.join(
        os.path.dirname(__file__), "..",
        "anvikshiki_v4", "data", "business_expert.yaml"
    )
    ks = load_knowledge_store(kb_path)
    pr(f"KnowledgeStore: {len(ks.vyaptis)} vyaptis, domain={ks.domain_type.value}\n")

    # ── Build ontology snippet (Layer 1) ──
    snippet_builder = OntologySnippetBuilder()
    snippet = snippet_builder.build(ks)

    pr(hr("─"))
    pr("  LAYER 1: Ontology Snippet (constrains LLM vocabulary)")
    pr(hr("─"))
    pr(snippet)

    # ── Call GroundQuery directly via dspy.ChainOfThought ──
    pr(hr("─"))
    pr("  CALLING: dspy.ChainOfThought(GroundQuery)")
    pr(hr("─"))

    grounder = dspy.ChainOfThought(GroundQuery)

    t1 = time.time()
    try:
        result = grounder(
            query=QUERY,
            ontology_snippet=snippet,
            domain_type=ks.domain_type.value,
            config={"temperature": 0},
        )
        t2 = time.time()
        pr(f"\n  Completed in {t2-t1:.1f}s")
        pr(f"  Parsed result:")
        pr(f"    reasoning:       {getattr(result, 'reasoning', 'N/A')}")
        pr(f"    predicates:      {getattr(result, 'predicates', 'N/A')}")
        pr(f"    relevant_vyaptis: {getattr(result, 'relevant_vyaptis', 'N/A')}")
    except Exception as e:
        t2 = time.time()
        pr(f"\n  FAILED after {t2-t1:.1f}s: {type(e).__name__}: {e}")

    # ── Dump full LLM history ──
    traces = extract_all_history(lm)

    for i, trace in enumerate(traces):
        pr(f"\n{'='*80}")
        pr(f"  LLM CALL #{i+1} of {len(traces)}")
        pr(f"{'='*80}")

        # Input messages
        pr(f"\n{'─'*80}")
        pr(f"  INPUT PROMPT (messages sent to GLM-5)")
        pr(f"{'─'*80}")
        for msg in trace["messages"]:
            role = msg.get("role", "?")
            content = msg.get("content", "")
            if len(content) > 3000:
                content = content[:3000] + f"\n\n... [{len(content)} chars total, truncated for display]"
            pr(f"\n  [{role.upper()}]:")
            for line in content.split("\n"):
                pr(f"    {line}")

        # Reasoning content
        pr(f"\n{'─'*80}")
        pr(f"  REASONING_CONTENT (GLM-5 internal chain-of-thought)")
        pr(f"{'─'*80}")
        rc = trace["reasoning_content"]
        if rc:
            pr()
            for line in rc.split("\n"):
                pr(f"  {line}")
        else:
            pr("  (none)")

        # Raw content
        pr(f"\n{'─'*80}")
        pr(f"  CONTENT (raw LLM response that DSPy parses)")
        pr(f"{'─'*80}")
        ct = trace["content"]
        if ct:
            pr()
            for line in ct.split("\n"):
                pr(f"  {line}")
        else:
            pr("  (empty)")

        # DSPy parsed output
        pr(f"\n{'─'*80}")
        pr(f"  DSPy PARSED OUTPUTS")
        pr(f"{'─'*80}")
        outputs = trace["outputs"]
        if outputs:
            for out in outputs:
                if isinstance(out, dict):
                    pr(f"  {json.dumps(out, indent=2)}")
                else:
                    pr(f"  {out}")
        else:
            pr("  (none)")

    total = time.time() - t0
    pr(f"\n{'='*80}")
    pr(f"  DONE — {len(traces)} LLM calls, {total:.1f}s total")
    pr(f"{'='*80}")

    # ── Save ──
    out_path = os.path.join(os.path.dirname(__file__), "..", "traces", "glm5_grounding_trace.txt")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write("\n".join(output_lines))
    pr(f"\nTrace saved to: {out_path}")


if __name__ == "__main__":
    main()
