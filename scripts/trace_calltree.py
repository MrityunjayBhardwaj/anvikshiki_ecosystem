#!/usr/bin/env python3
"""
Full function call trace for dspy.ChainOfThought(GroundQuery).
Captures every function call/return with file, line, function name.
"""

import os
import sys
import time
import threading
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dspy
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store
from anvikshiki_v4.grounding import GroundQuery, OntologySnippetBuilder

# ── Config ──
API_KEY = os.environ["DEEPINFRA_API_KEY"]
MODEL_ID = "openai/zai-org/GLM-5"
BASE_URL = "https://api.deepinfra.com/v1/openai"

# ── Setup ──
lm = dspy.LM(MODEL_ID, api_key=API_KEY, api_base=BASE_URL, max_tokens=4096)
dspy.configure(lm=lm, adapter=dspy.JSONAdapter())

ks = load_knowledge_store(os.path.join(os.path.dirname(__file__), "..", "anvikshiki_v4", "data", "business_expert.yaml"))
snippet = OntologySnippetBuilder().build(ks)
grounder = dspy.ChainOfThought(GroundQuery)

# ── Trace setup ──
trace_lines = []
depth = 0
tracing = False
SKIP_DIRS = {"importlib", "abc", "typing", "_collections", "enum", "re", "sre", "json/", "urllib3", "certifi", "charset", "idna"}

def trace_func(frame, event, arg):
    global depth, tracing
    if not tracing:
        return

    filename = frame.f_code.co_filename
    # Skip noisy stdlib internals
    if any(s in filename for s in SKIP_DIRS):
        return

    funcname = frame.f_code.co_name
    lineno = frame.f_lineno

    # Shorten path for readability
    short = filename
    for prefix in ["/Users/mrityunjaybhardwaj/Documents/Anvikshiki/.venv/lib/python3.14/site-packages/",
                   "/Users/mrityunjaybhardwaj/Documents/Anvikshiki/anvikshiki_ecosystem/"]:
        if filename.startswith(prefix):
            short = filename[len(prefix):]
            break

    if event == "call":
        line = f"{'  ' * depth}→ {short}:{lineno}  {funcname}()"
        trace_lines.append(line)
        print(line)
        sys.stdout.flush()
        depth += 1
        return trace_func
    elif event == "return":
        depth = max(0, depth - 1)
        line = f"{'  ' * depth}← {short}:{lineno}  {funcname}  returned"
        trace_lines.append(line)
        print(line)
        sys.stdout.flush()
    elif event == "exception":
        line = f"{'  ' * depth}!! {short}:{lineno}  {funcname}  EXCEPTION: {arg[1]}"
        trace_lines.append(line)
        print(line)
        sys.stdout.flush()

# ── Watchdog: kill if stuck for 60s ──
def watchdog():
    time.sleep(60)
    print("\n\n=== WATCHDOG: 60s timeout — dumping last 50 trace lines ===")
    for line in trace_lines[-50:]:
        print(line)
    print(f"\nTotal trace lines: {len(trace_lines)}")
    print("=== STUCK — last call never returned ===")
    sys.stdout.flush()
    os._exit(1)

t = threading.Thread(target=watchdog, daemon=True)
t.start()

# ── Run with tracing ──
print(f"Tracing dspy.ChainOfThought(GroundQuery) call...\n")
sys.stdout.flush()

tracing = True
sys.settrace(trace_func)
threading.settrace(trace_func)

t0 = time.time()
try:
    result = grounder(
        query="Does Acme Corp have good unit economics and efficient resource allocation?",
        ontology_snippet=snippet,
        domain_type=ks.domain_type.value,
        config={"temperature": 0},
    )
    sys.settrace(None)
    tracing = False
    dt = time.time() - t0
    print(f"\n\nCompleted in {dt:.1f}s")
    print(f"reasoning: {getattr(result, 'reasoning', None)}")
    print(f"predicates: {getattr(result, 'predicates', None)}")
except Exception as e:
    sys.settrace(None)
    tracing = False
    dt = time.time() - t0
    print(f"\n\nFAILED after {dt:.1f}s: {e}")

# Save trace
out_path = os.path.join(os.path.dirname(__file__), "..", "traces", "calltree_trace.txt")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    f.write("\n".join(trace_lines))
print(f"\nTrace ({len(trace_lines)} lines) saved to: {out_path}")
