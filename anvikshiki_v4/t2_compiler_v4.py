# anvikshiki_v4/t2_compiler_v4.py
"""
T2 Compiler v4: Compile verified architecture into
an argumentation framework over provenance semirings.
"""

import math
from itertools import product as iter_product
from datetime import datetime
from .paths import resolve_repo_path
from .schema import KnowledgeStore, CausalStatus
from .schema_v4 import (
    Argument, Attack, ProvenanceTag, PramanaType, EpistemicStatus
)
from .lattice import from_kb, meet, rank
from .argumentation import ArgumentationFramework
from .engine_params import CompilerParams, DEFAULT_PARAMS
from .predicate_contrariness import (
    are_contrary,
    get_contrary,
    normalize_negation,
    predicate_name,
)

# ── Tag Construction ──

PRAMANA_MAP = {
    CausalStatus.DEFINITIONAL: PramanaType.PRATYAKSA,
    CausalStatus.STRUCTURAL: PramanaType.PRATYAKSA,
    CausalStatus.EMPIRICAL: PramanaType.ANUMANA,
    CausalStatus.REGULATORY: PramanaType.SABDA,
}

# Module-level defaults from centralized params (engine_params.py).
# Functions accept an optional CompilerParams to override.
_DEFAULT_COMPILER = DEFAULT_PARAMS.compiler


# Contrariness lives in predicate_contrariness.py, which the evaluator and
# coverage routing read too. It was defined here alone while the evaluator
# scored `value_creation` against `not_value_creation` as a match — one package
# holding two opposite beliefs about the same pair of strings, with the
# engine's own semantics on the losing side. These names are kept so call sites
# read the same; the behaviour is unchanged.

_predicate_name = predicate_name
_normalize_negation = normalize_negation
_get_contrary = get_contrary


def _are_contrary(a: str, b: str, ks: KnowledgeStore | None = None) -> bool:
    """Check if two conclusions are contradictory.

    Two-layer check (fixes audit III-02):
    1. Syntactic: not_ prefix negation (with double-negation elimination)
    2. Domain: KnowledgeStore.contrariness_pairs lookup
    """
    return are_contrary(a, b, ks)


def _build_rule_tag(
    vyapti,
    knowledge_store: KnowledgeStore,
    params: CompilerParams = _DEFAULT_COMPILER,
) -> ProvenanceTag:
    """Build a provenance tag for a vyāpti from its KB metadata.

    The vyāpti's epistemic status is not consumed here. It enters the
    reasoning as an element of the lattice, at the point where the argument
    using this rule is built.
    """
    trust = vyapti.confidence.formulation * vyapti.confidence.existence

    decay = 1.0
    if vyapti.last_verified:
        age_days = (datetime.now() - vyapti.last_verified).days
        decay = math.exp(-params.LN2 * age_days / params.decay_half_life_days)

    return ProvenanceTag(
        source_ids=frozenset(vyapti.sources),
        pramana_type=PRAMANA_MAP.get(
            vyapti.causal_status, PramanaType.ANUMANA),
        trust_score=trust,
        decay_factor=decay,
        derivation_depth=0,
    )


# ── Main Compiler ──

def _deep_copy_af(af: ArgumentationFramework) -> ArgumentationFramework:
    """Deep copy an AF so the original is not mutated."""
    import copy
    return copy.deepcopy(af)


def precompile_kb(
    knowledge_store: KnowledgeStore,
    params: CompilerParams = _DEFAULT_COMPILER,
) -> ArgumentationFramework:
    """Phase 1: Build AF from KB rules only (no query facts).

    Call once per KB, cache the result.  Query-specific facts are
    added incrementally via compile_t2(..., precompiled_af=...).
    (Fixes audit III-08)
    """
    af = ArgumentationFramework()

    for _ in range(params.max_fixpoint_iterations):
        prev_count = len(af.arguments)
        _derive_rule_arguments(af, knowledge_store, params)
        _derive_attacks(af, knowledge_store, params)
        if len(af.arguments) == prev_count:
            break

    return af


def compile_t2(
    knowledge_store: KnowledgeStore,
    query_facts: list[dict],
    precompiled_af: ArgumentationFramework | None = None,
    params: CompilerParams = _DEFAULT_COMPILER,
) -> ArgumentationFramework:
    """
    Build the argumentation framework from KB + query facts.

    If precompiled_af is provided, starts from a deep copy of that
    cached AF and only adds query-specific premises + incremental
    derivation.  Otherwise builds from scratch (backward-compatible).

    Steps:
    1. Create premise arguments from grounded query facts
    2. Create rule-based arguments from vyāptis (forward chain)
    3. Derive attacks (rebutting, undercutting, undermining)
    4. Repeat steps 2-3 until fixpoint (no new arguments)
    """
    if precompiled_af is not None:
        af = _deep_copy_af(precompiled_af)
    else:
        af = ArgumentationFramework()

    # ── Step 1: Premise arguments from grounded query facts ──
    for fact in query_facts:
        arg_id = af.next_arg_id()
        tag = ProvenanceTag(
            source_ids=frozenset(fact.get("sources", [])),
            pramana_type=PramanaType.PRATYAKSA,
            trust_score=1.0,
            decay_factor=1.0,
            derivation_depth=0,
        )
        af.add_argument(Argument(
            id=arg_id,
            conclusion=fact["predicate"],
            top_rule=None,
            premises=frozenset([fact["predicate"]]),
            is_strict=True,
            tag=tag,
            # A grounded query fact is direct evidence, and it enters L at
            # the top. The grounder's confidence is deliberately NOT turned
            # into a status here: cutting a float into categories is the
            # defect being removed, and confidence belongs to the conformal
            # feature vector (#23), where it gets a coverage guarantee
            # instead of a threshold.
            status=EpistemicStatus.ESTABLISHED,
        ))

    # ── Steps 2-4: Forward chain with fixpoint ──
    for _ in range(params.max_fixpoint_iterations):
        prev_count = len(af.arguments)
        _derive_rule_arguments(af, knowledge_store, params)
        _derive_attacks(af, knowledge_store, params)
        if len(af.arguments) == prev_count:
            break

    return af


def _derive_rule_arguments(
    af: ArgumentationFramework,
    ks: KnowledgeStore,
    params: CompilerParams = _DEFAULT_COMPILER,
):
    """Create rule-based arguments for all applicable vyāptis.

    Builds ALL sub-argument combinations (not just the strongest),
    capped at params.max_argument_combos_per_rule per rule to avoid
    combinatorial explosion.  (Fixes audit III-03)

    Tracks (rule_id, sub_argument_ids) to prevent cyclic re-derivation.
    """
    available = {a.conclusion for a in af.arguments.values()}
    existing_derivations = {
        (a.top_rule, a.sub_arguments)
        for a in af.arguments.values() if a.top_rule
    }

    for vid, v in ks.vyaptis.items():
        if not all(ant in available for ant in v.antecedents):
            continue

        # Collect ALL candidate sub-arguments per antecedent
        candidates_per_ant = []
        for ant in v.antecedents:
            candidates = [
                a for a in af.arguments.values()
                if a.conclusion == ant
            ]
            if not candidates:
                break
            candidates_per_ant.append(candidates)

        if len(candidates_per_ant) != len(v.antecedents):
            continue

        # All combinations, sorted by total belief (best first), capped
        combos = list(iter_product(*candidates_per_ant))
        combos.sort(
            key=lambda c: sum(rank(a.status) for a in c), reverse=True
        )
        combos = combos[:params.max_argument_combos_per_rule]

        rule_tag = _build_rule_tag(v, ks, params)
        is_strict = v.causal_status.value in ("definitional", "structural")

        for combo in combos:
            sub_arg_ids = tuple(a.id for a in combo)
            derivation_key = (vid, sub_arg_ids)
            if derivation_key in existing_derivations:
                continue
            existing_derivations.add(derivation_key)

            combined_tag = rule_tag
            for sub_arg in combo:
                combined_tag = ProvenanceTag.tensor(combined_tag, sub_arg.tag)

            # σ(a) = ⋀( status(top_rule), { σ(s) : s ∈ sub_args } )
            # Weakest link: an inference cannot conclude more strongly than
            # the weakest thing it reasoned through.
            combined_status = meet(
                [from_kb(v.epistemic_status)]
                + [sub_arg.status for sub_arg in combo]
            )

            arg_id = af.next_arg_id()
            af.add_argument(Argument(
                id=arg_id,
                conclusion=v.consequent,
                top_rule=vid,
                sub_arguments=sub_arg_ids,
                premises=frozenset().union(*(
                    af.arguments[sa].premises for sa in sub_arg_ids
                )),
                is_strict=is_strict,
                tag=combined_tag,
                status=combined_status,
            ))


def _derive_attacks(
    af: ArgumentationFramework,
    ks: KnowledgeStore,
    params: CompilerParams = _DEFAULT_COMPILER,
):
    """Derive all three attack types from AF structure."""
    existing_attacks = {
        (atk.attacker, atk.target) for atk in af.attacks
    }

    # 3a. Rebutting attacks (viruddha): contradictory conclusions
    # Uses _are_contrary() with domain pairs for proper detection (fixes III-02)
    conclusions: dict[str, list[str]] = {}
    for a in af.arguments.values():
        conclusions.setdefault(a.conclusion, []).append(a.id)

    checked_pairs = set()
    for conc_a, ids_a in conclusions.items():
        for conc_b, ids_b in conclusions.items():
            if conc_a >= conc_b:
                continue  # Avoid duplicate pair checks
            pair = (conc_a, conc_b)
            if pair in checked_pairs:
                continue
            checked_pairs.add(pair)
            if not _are_contrary(conc_a, conc_b, ks):
                continue
            # Contradictory — create mutual rebutting attacks
            for id_a in ids_a:
                for id_b in ids_b:
                    if (id_b, id_a) not in existing_attacks:
                        af.add_attack(Attack(
                            attacker=id_b, target=id_a,
                            attack_type="rebutting", hetvabhasa="viruddha"))
                        existing_attacks.add((id_b, id_a))
                    if (id_a, id_b) not in existing_attacks:
                        af.add_attack(Attack(
                            attacker=id_a, target=id_b,
                            attack_type="rebutting", hetvabhasa="viruddha"))
                        existing_attacks.add((id_a, id_b))

    # 3b. Undercutting attacks (savyabhicāra): scope violations
    # Uses _predicate_name() for matching (fixes III-09)
    # Attacks ALL arguments using the violated rule (fixes III-11)
    for vid, v in ks.vyaptis.items():
        for excl in v.scope_exclusions:
            # Match by predicate name, not exact string (III-09)
            if not any(_predicate_name(arg.conclusion) == _predicate_name(excl)
                       for arg in af.arguments.values()):
                continue
            # Find all arguments using this rule
            rule_args = [
                a for a in af.arguments.values() if a.top_rule == vid
            ]
            if not rule_args:
                continue
            # Renamed from _undercut_ to inapplicable_ (III-11)
            target_conclusion = f"inapplicable_{vid}"
            if any(arg.conclusion == target_conclusion
                   for arg in af.arguments.values()):
                continue
            scope_arg_id = af.next_arg_id()
            af.add_argument(Argument(
                id=scope_arg_id,
                conclusion=target_conclusion,
                top_rule=None,
                premises=frozenset([excl]),
                is_strict=True,
                tag=ProvenanceTag(
                    pramana_type=PramanaType.PRATYAKSA,
                    trust_score=1.0, decay_factor=1.0,
                ),
                # The scope exclusion is present in the framework as an
                # observed fact about this query, not as a claim under
                # dispute — it enters at the top of L, as the premises do.
                status=EpistemicStatus.ESTABLISHED,
            ))
            # Attack ALL arguments using this rule
            for rule_arg in rule_args:
                if (scope_arg_id, rule_arg.id) not in existing_attacks:
                    af.add_attack(Attack(
                        attacker=scope_arg_id, target=rule_arg.id,
                        attack_type="undercutting", hetvabhasa="savyabhicara"))
                    existing_attacks.add((scope_arg_id, rule_arg.id))

    # 3c. Undermining attacks (asiddha): decay-expired premises
    for a in list(af.arguments.values()):
        if a.tag.decay_factor >= params.decay_undermine_threshold:
            continue
        stale_conclusion = f"_stale_{a.id}"
        if any(arg.conclusion == stale_conclusion
               for arg in af.arguments.values()):
            continue
        decay_arg_id = af.next_arg_id()
        af.add_argument(Argument(
            id=decay_arg_id,
            conclusion=stale_conclusion,
            top_rule=None,
            premises=frozenset(["_temporal_decay"]),
            is_strict=True,
            tag=ProvenanceTag(
                pramana_type=PramanaType.PRATYAKSA,
                trust_score=1.0, decay_factor=1.0,
            ),
            # That the supporting premise has decayed past its threshold is
            # a computed fact about the framework, not a defeasible claim.
            # Decay stays structural — it triggers an attack in the graph,
            # which is what survives the subtraction; the magnitude does not.
            status=EpistemicStatus.ESTABLISHED,
        ))
        af.add_attack(Attack(
            attacker=decay_arg_id, target=a.id,
            attack_type="undermining", hetvabhasa="asiddha"))


def load_knowledge_store(path: str) -> KnowledgeStore:
    """Load KnowledgeStore from YAML file.

    Callers throughout the tree pass repo-relative literals such as
    "anvikshiki_v4/data/business_expert.yaml", so the path is resolved against
    a fixed anchor rather than the working directory. See `paths.py` for why.
    """
    import yaml
    with open(resolve_repo_path(path, description="knowledge base")) as f:
        data = yaml.safe_load(f)
    return KnowledgeStore(**data)
