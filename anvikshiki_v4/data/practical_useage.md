Practical Usage
There are three levels of usage depending on whether you have LLM access.

Level 1: Pure Symbolic (no LLM needed)
This uses the argumentation engine directly — compile a KB, add query facts, compute the extension:


from anvikshiki_v4.schema import KnowledgeStore
from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store
from anvikshiki_v4.uncertainty import compute_uncertainty_v4

# Load your knowledge base
ks = load_knowledge_store("anvikshiki_v4/data/sample_architecture.yaml")

# Define query facts — what the user is asking about
query_facts = [
    {"predicate": "concentrated_ownership", "confidence": 0.9,
     "sources": ["user_input"]},
]

# Compile KB + facts → argumentation framework
af = compile_t2(ks, query_facts)

# Compute grounded extension
labels = af.compute_grounded()

# See what was accepted/defeated
for aid, arg in af.arguments.items():
    if arg.conclusion.startswith("_"):
        continue  # skip internal predicates
    print(f"{arg.conclusion}: {labels[aid].value}  "
          f"(b={arg.tag.belief:.2f}, pramana={arg.tag.pramana_type.name})")

# Get epistemic status per conclusion
for conc in {"long_horizon_possible", "capability_building_possible",
             "not_good_governance"}:
    status, tag, args = af.get_epistemic_status(conc)
    if status:
        print(f"\n{conc}: {status.value}")
        print(f"  belief={tag.belief:.2f}, uncertainty={tag.uncertainty:.2f}")
        print(f"  sources={sorted(tag.source_ids)}")

# Uncertainty decomposition
for conc in {"long_horizon_possible"}:
    status, tag, _ = af.get_epistemic_status(conc)
    uq = compute_uncertainty_v4(tag, 0.9, conc, status)
    print(f"\n{conc} uncertainty:")
    print(f"  epistemic: {uq['epistemic']['explanation']}")
    print(f"  aleatoric: {uq['aleatoric']['explanation']}")
    print(f"  inference: {uq['inference']['explanation']}")
With the sample YAML, this would show:

concentrated_ownership → IN (premise fact, strict, PRATYAKSA)
long_horizon_possible → IN (derived via V01, empirical ANUMANA)
capability_building_possible → IN (derived via V02, chained)
not_good_governance → IN (derived via V03 — contradicts V01's optimism)
V01 and V03 both fire from concentrated_ownership, producing arguments for long_horizon_possible (positive) and not_good_governance (negative). If public_firm were in the query facts, V01 would get undercut (scope exclusion), and long_horizon_possible would be OUT.

Level 2: With Contestation (still no LLM)

from anvikshiki_v4.contestation import ContestationManager

cm = ContestationManager()

# Vāda — cooperative inquiry (what do we know?)
vada = cm.vada(af)
print(f"Accepted: {list(vada.accepted.keys())}")
print(f"Open questions: {vada.open_questions}")
print(f"Suggested evidence: {vada.suggested_evidence}")

# Jalpa — adversarial stress test (what could be challenged?)
jalpa = cm.jalpa(af, timeout_seconds=10.0)
print(f"Defensible positions: {jalpa.defensible_positions}")
print(f"Counter-arguments: {jalpa.counter_arguments}")

# Vitaṇḍā — vulnerability audit (where are the weaknesses?)
vitanda = cm.vitanda(af, timeout_seconds=10.0)
print(f"Vulnerabilities: {vitanda.vulnerability_inventory.keys()}")
print(f"Undefended: {vitanda.undefended}")

# User contestation — inject a counter-argument
new_id = cm.apply_contestation(af, "viruddha", "A0002", {
    "conclusion": "not_long_horizon_possible",
    "belief": 0.85,
    "pramana_type": "PRATYAKSA",
    "sources": ["field_observation_2024"],
})
# Recompute after contestation
labels = af.compute_grounded()
Level 3: Full Engine (requires LLM via DSPy)

import dspy
from anvikshiki_v4.schema import KnowledgeStore
from anvikshiki_v4.grounding import GroundingPipeline
from anvikshiki_v4.engine_v4 import AnvikshikiEngineV4

# ── Option A: Cloud LLM ──
dspy.configure(lm=dspy.LM("openai/gpt-4o"))           # OpenAI
# dspy.configure(lm=dspy.LM("anthropic/claude-sonnet-4-6"))  # Anthropic
# dspy.configure(lm=dspy.LM("gemini/gemini-2.0-flash",       # Gemini
#     api_key="YOUR_GOOGLE_API_KEY"))

# ── Option B: Local MLX model (free, no API key needed) ──
# First, start the server in a separate terminal:
#   cd ~/Documents/local_llm && source .venv/bin/activate
#   HF_HOME="$PWD/hf_cache" mlx_lm.server --model mlx-community/Llama-3.2-3B-Instruct-4bit
#
# Then configure DSPy to point at it:
# dspy.configure(lm=dspy.LM(
#     model="openai/mlx-community/Llama-3.2-3B-Instruct-4bit",
#     api_base="http://localhost:8080/v1",
#     api_key="local",
# ))

# Load KB
ks = load_knowledge_store("anvikshiki_v4/data/sample_architecture.yaml")

# Build the pipeline
grounding = GroundingPipeline(knowledge_store=ks)
engine = AnvikshikiEngineV4(
    knowledge_store=ks,
    grounding_pipeline=grounding,
    contestation_mode="vada",  # or "jalpa", "vitanda"
)

# Run a query
result = engine(
    query="What happens when ownership is concentrated in a private firm?",
    retrieved_chunks=[
        "Chandler (1990) showed concentrated ownership enables...",
        "Morck et al. (2005) found entrenchment risks...",
    ],
)

# Results
print(result.response)           # Calibrated natural language response
print(result.sources)            # ["src_chandler_1990", ...]
print(result.extension_size)     # Number of IN arguments
print(result.grounding_confidence)  # 0.0-1.0
print(result.violations)         # Defeated arguments (hetvābhāsas)
print(result.contestation)       # {"mode": "vada", "open_questions": [...]}

# Drill into uncertainty per conclusion
for conc, uq in result.uncertainty.items():
    print(f"{conc}: confidence={uq['total_confidence']:.2f}, "
          f"status={uq['epistemic']['status']}")

# Drill into provenance
for conc, prov in result.provenance.items():
    print(f"{conc}: pramana={prov['pramana']}, "
          f"sources={prov['sources']}, depth={prov['derivation_depth']}")
Building Your Own Knowledge Base
The YAML format is straightforward — each vyāpti is a domain rule:


domain_type: EMPIRICAL          # One of 8 domain types
vyaptis:
  V01:
    id: V01
    name: "Human-readable rule name"
    statement: "If X then Y"
    causal_status: empirical     # empirical|structural|definitional|regulatory
    scope_conditions: ["applies_when_this"]
    scope_exclusions: ["not_when_this"]  # triggers undercutting attacks
    confidence:
      existence: 0.85            # How sure the rule exists
      formulation: 0.9           # How precise the statement is
      evidence: "observational"
    epistemic_status: established  # established|hypothesis|open|contested
    sources: ["src_author_year"]
    antecedents: ["predicate_a"]   # IF these predicates hold...
    consequent: "predicate_b"      # THEN this predicate holds
Key things that drive the argumentation:

Contradictory consequents ("X" vs "not_X") generate rebutting attacks automatically
scope_exclusions generate undercutting attacks when the excluded predicate exists
Stale rules (decay_factor < 0.3 from old last_verified) generate undermining attacks
causal_status determines is_strict (definitional/structural = strict, can't be rebutted) and pramāṇa type
epistemic_status sets initial belief/disbelief/uncertainty values for the tag