# anvikshiki_v4/t2_compiler_v4.py
"""
T2 Compiler v4: Compile verified architecture into
an argumentation framework over provenance semirings.
"""

import math
from itertools import product as iter_product
from datetime import datetime
from .schema import KnowledgeStore, CausalStatus
from .schema import EpistemicStatus as KBEpistemicStatus
from .schema_v4 import (
    Argument, Attack, ProvenanceTag, PramanaType
)
from .argumentation import ArgumentationFramework

# Maximum sub-argument combinations per rule to avoid combinatorial explosion
MAX_ARGUMENT_COMBOS_PER_RULE = 5


# ── Tag Construction ──

PRAMANA_MAP = {
    CausalStatus.DEFINITIONAL: PramanaType.PRATYAKSA,
    CausalStatus.STRUCTURAL: PramanaType.PRATYAKSA,
    CausalStatus.EMPIRICAL: PramanaType.ANUMANA,
    CausalStatus.REGULATORY: PramanaType.SABDA,
}

BELIEF_MAP = {
    KBEpistemicStatus.ESTABLISHED: (0.95, 0.0, 0.05),
    KBEpistemicStatus.WORKING_HYPOTHESIS: (0.6, 0.1, 0.3),
    KBEpistemicStatus.GENUINELY_OPEN: (0.2, 0.2, 0.6),
    KBEpistemicStatus.ACTIVELY_CONTESTED: (0.4, 0.4, 0.2),
}

DECAY_HALF_LIFE_DAYS = 365      # DSPy-optimizable
DECAY_UNDERMINE_THRESHOLD = 0.3  # DSPy-optimizable


def _predicate_name(pred: str) -> str:
    """Extract predicate name from 'pred(entity)' format.

    'binding_constraint_identified(acme_corp)' → 'binding_constraint_identified'
    'positive_unit_economics' → 'positive_unit_economics'
    (Fixes audit III-01)
    """
    paren = pred.find("(")
    return pred[:paren] if paren >= 0 else pred


def _normalize_negation(conclusion: str) -> str:
    """Normalize by eliminating double negations: not_not_X → X."""
    while conclusion.startswith("not_not_"):
        conclusion = conclusion[8:]
    return conclusion


def _get_contrary(conclusion: str) -> str:
    """Compute the contrary of a conclusion, handling double negation.

    not_not_X → contrary of X → not_X
    not_X → X
    X → not_X
    """
    norm = _normalize_negation(conclusion)
    if norm.startswith("not_"):
        return norm[4:]          # not_X → X
    else:
        return f"not_{norm}"     # X → not_X


# Module-level cache for domain contrariness index (built once per compile)
_domain_contrary_index: set[tuple[str, str]] = set()


def _build_domain_contrary_index(ks: KnowledgeStore) -> set[tuple[str, str]]:
    """Build a fast lookup set from KnowledgeStore.contrariness_pairs."""
    index = set()
    for pair in ks.contrariness_pairs:
        if len(pair) == 2:
            index.add((pair[0], pair[1]))
            index.add((pair[1], pair[0]))
    return index


def _are_contrary(a: str, b: str, ks: KnowledgeStore | None = None) -> bool:
    """Check if two conclusions are contradictory.

    Two-layer check (fixes audit III-02):
    1. Syntactic: not_ prefix negation (with double-negation elimination)
    2. Domain: KnowledgeStore.contrariness_pairs lookup
    """
    # Strip entity arguments for comparison
    na = _normalize_negation(_predicate_name(a))
    nb = _normalize_negation(_predicate_name(b))

    # Layer 1: syntactic negation
    if _get_contrary(na) == nb:
        return True

    # Layer 2: domain-specific pairs
    if ks is not None and (na, nb) in _build_domain_contrary_index(ks):
        return True

    return False


def _build_rule_tag(vyapti, knowledge_store: KnowledgeStore) -> ProvenanceTag:
    """Build a provenance tag for a vyāpti from its KB metadata."""
    b, d, u = BELIEF_MAP.get(vyapti.epistemic_status, (0.5, 0.1, 0.4))
    trust = vyapti.confidence.formulation * vyapti.confidence.existence

    decay = 1.0
    if vyapti.last_verified:
        age_days = (datetime.now() - vyapti.last_verified).days
        decay = math.exp(-0.693 * age_days / DECAY_HALF_LIFE_DAYS)

    return ProvenanceTag(
        belief=b, disbelief=d, uncertainty=u,
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


def precompile_kb(knowledge_store: KnowledgeStore) -> ArgumentationFramework:
    """Phase 1: Build AF from KB rules only (no query facts).

    Call once per KB, cache the result.  Query-specific facts are
    added incrementally via compile_t2(..., precompiled_af=...).
    (Fixes audit III-08)
    """
    af = ArgumentationFramework()

    MAX_ITERATIONS = 100
    for _ in range(MAX_ITERATIONS):
        prev_count = len(af.arguments)
        _derive_rule_arguments(af, knowledge_store)
        _derive_attacks(af, knowledge_store)
        if len(af.arguments) == prev_count:
            break

    return af


def compile_t2(
    knowledge_store: KnowledgeStore,
    query_facts: list[dict],
    precompiled_af: ArgumentationFramework | None = None,
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
        confidence = fact.get("confidence", 0.9)
        tag = ProvenanceTag(
            belief=confidence,
            disbelief=0.0,
            uncertainty=round(1.0 - confidence, 4),
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
        ))

    # ── Steps 2-4: Forward chain with fixpoint ──
    MAX_ITERATIONS = 100
    for _ in range(MAX_ITERATIONS):
        prev_count = len(af.arguments)
        _derive_rule_arguments(af, knowledge_store)
        _derive_attacks(af, knowledge_store)
        if len(af.arguments) == prev_count:
            break

    return af


def _derive_rule_arguments(
    af: ArgumentationFramework,
    ks: KnowledgeStore,
):
    """Create rule-based arguments for all applicable vyāptis.

    Builds ALL sub-argument combinations (not just the strongest),
    capped at MAX_ARGUMENT_COMBOS_PER_RULE per rule to avoid
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
            key=lambda c: sum(a.tag.belief for a in c), reverse=True
        )
        combos = combos[:MAX_ARGUMENT_COMBOS_PER_RULE]

        rule_tag = _build_rule_tag(v, ks)
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
            ))


def _derive_attacks(
    af: ArgumentationFramework,
    ks: KnowledgeStore,
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
                    belief=1.0, disbelief=0.0, uncertainty=0.0,
                    pramana_type=PramanaType.PRATYAKSA,
                    trust_score=1.0, decay_factor=1.0,
                ),
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
        if a.tag.decay_factor >= DECAY_UNDERMINE_THRESHOLD:
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
                belief=1.0 - a.tag.decay_factor,
                disbelief=0.0,
                uncertainty=a.tag.decay_factor,
                pramana_type=PramanaType.PRATYAKSA,
                trust_score=1.0, decay_factor=1.0,
            ),
        ))
        af.add_attack(Attack(
            attacker=decay_arg_id, target=a.id,
            attack_type="undermining", hetvabhasa="asiddha"))


def load_knowledge_store(path: str) -> KnowledgeStore:
    """Load KnowledgeStore from YAML file."""
    import yaml
    with open(path) as f:
        data = yaml.safe_load(f)
    return KnowledgeStore(**data)
