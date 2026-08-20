# anvikshiki_v4/t2_compiler_v4.py
"""
T2 Compiler v4: Compile verified architecture into
an argumentation framework over provenance semirings.
"""

import math
from dataclasses import replace
from itertools import product as iter_product
from datetime import datetime
from .paths import resolve_repo_path
from .schema import KnowledgeStore, CausalStatus
from .schema_v4 import (
    Argument, Attack, ProvenanceTag, PramanaType, EpistemicStatus
)
from .lattice import (
    BOUND_ASSERTED,
    meet,
    rank,
    status_breakdown,
    status_of_rule,
)
from .argumentation import ArgumentationFramework
from .engine_params import CompilerParams, DEFAULT_PARAMS
from .predicate_contrariness import (
    are_contrary,
    get_contrary,
    normalize_negation,
    predicate_entity,
    predicate_name,
    with_entity,
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
            # An asserted fact. No rule bounds it, so naming one would
            # attribute the constraint to a rule that does not exist.
            status_bound_by=(BOUND_ASSERTED,),
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


def _argument_bindings(af: ArgumentationFramework) -> dict:
    """Arguments indexed by (predicate name, entity binding).

    The grounder produces `pricing_power(company)` while a knowledge base
    declares `pricing_power`, so comparing conclusions as strings finds
    nothing. Splitting both sides into a name and a binding is what lets the
    two meet.
    """
    index: dict = {}
    for a in af.arguments.values():
        key = (predicate_name(a.conclusion), predicate_entity(a.conclusion))
        index.setdefault(key, []).append(a)
    return index


def _rule_bindings(ks: KnowledgeStore, index: dict):
    """Every (rule, entity) pair worth attempting, deterministically ordered.

    A vyāpti is `consequent(E) :- antecedent1(E), antecedent2(E), …` — one
    Entity variable shared by the whole rule, as `Vyapti`'s own docstring
    specifies. So a rule is attempted once per entity, and every antecedent
    must hold *for that same entity*. `datalog_engine` already reasons this
    way; this is the ASPIC+ compiler agreeing with it.
    """
    for vid, v in ks.vyaptis.items():
        if not v.antecedents:
            # A rule with no antecedents fires once and is about nothing in
            # particular, so there is no binding to carry to its consequent.
            yield vid, v, None
            continue

        # Every antecedent shares E, so any entity this rule could fire for
        # has to appear under the first one. The rest are checked by the
        # caller, which is what makes the binding strict.
        entities = {e for (name, e) in index if name == v.antecedents[0]}

        # Sorted because argument ids are handed out in iteration order and a
        # set's order is hash-randomised between runs. An unsorted loop here
        # would make the framework's ids differ run to run for the same input
        # — the defect that made the decision sheet irreproducible.
        for entity in sorted(entities, key=lambda e: (e is not None, e or "")):
            yield vid, v, entity


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
    index = _argument_bindings(af)
    existing_derivations = {
        (a.top_rule, a.sub_arguments)
        for a in af.arguments.values() if a.top_rule
    }

    for vid, v, entity in _rule_bindings(ks, index):
        # Collect ALL candidate sub-arguments per antecedent, every one of
        # them bound to the same entity as the rest of the rule.
        candidates_per_ant = []
        for ant in v.antecedents:
            candidates = index.get((ant, entity), [])
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

            # depth(a) = 1 + max{ depth(s) : s ∈ sub_args(a) }
            #
            # Set here rather than accumulated by the composition above,
            # because depth is the height of the derivation tree and a tree
            # height is not a binary operation on two tags. Applying this
            # rule is the one step; how many antecedents it took does not
            # make the derivation deeper. Well-founded: every sub-argument
            # already exists when this runs, and the derivation graph is
            # acyclic by construction (`existing_derivations` refuses to
            # re-derive a rule from the same sub-arguments).
            combined_tag = replace(
                combined_tag,
                # `default=0` is for a rule with no antecedents, which
                # `iter_product()` yields as one empty combination. Firing it
                # is still one inference step, so it lands at 1 — and without
                # the default, max over an empty combo raises and a rule the
                # compiler supports today stops compiling.
                derivation_depth=1 + max(
                    (sub_arg.tag.derivation_depth for sub_arg in combo),
                    default=0,
                ),
            )

            # σ(a) = ⋀( status(top_rule), { σ(s) : s ∈ sub_args } )
            # Weakest link: an inference cannot conclude more strongly than
            # the weakest thing it reasoned through.
            #
            # The rule's own status is already capped by its origin, so a
            # derivation through a generated rule cannot exceed that rule's
            # ceiling however strong its premises are.
            breakdown = status_breakdown(v)
            sub_statuses = [sub_arg.status for sub_arg in combo]
            combined_status = meet([breakdown.effective] + sub_statuses)

            # What is actually holding this argument down. The rule's own
            # bounds only explain it while the rule is the weakest link; once
            # a sub-argument is weaker, naming a rule bound would point a
            # reader at something whose removal would change nothing.
            if any(rank(st) < rank(breakdown.effective) for st in sub_statuses):
                bound_by = tuple(
                    f"sub:{sub_arg.id}" for sub_arg in combo
                    if rank(sub_arg.status) == rank(combined_status)
                )
            else:
                bound_by = breakdown.binding

            arg_id = af.next_arg_id()
            af.add_argument(Argument(
                id=arg_id,
                # The consequent is about whatever the antecedents were about.
                # Concluding the bare `pricing_power` from
                # `superior_information(firm)` would make the rule fire and
                # silently drop which firm it decided about.
                conclusion=with_entity(v.consequent, entity),
                top_rule=vid,
                sub_arguments=sub_arg_ids,
                premises=frozenset().union(*(
                    af.arguments[sa].premises for sa in sub_arg_ids
                )),
                is_strict=is_strict,
                tag=combined_tag,
                status=combined_status,
                status_bound_by=bound_by,
                # Absent metadata *is* the curated case — the same reading
                # `ceiling_for_origin` gives it. Sent as the word rather than
                # as null so the panel can tell a curated rule from an
                # argument that has no rule at all; both would otherwise
                # arrive as None and render alike.
                origin=(
                    breakdown.origin.value if breakdown.origin else "curated"
                ),
                citation_tier=breakdown.citation_tier.value,
            ))


def _rule_arguments_reached_by_exclusion(
    af: ArgumentationFramework, vid: str, entity: str | None
) -> list:
    """The arguments a scope exclusion reaches: this rule, this binding.

    How far an exclusion reaches is the whole of what #83 got wrong, so it is
    named rather than inlined. The block used to return every argument built
    from the rule, which meant one firm in a perfectly commoditized market
    suppressed V03 for every firm in the query. An exclusion is observed of an
    entity, and `Vyapti` shares one Entity variable across the rule and its
    exclusions, so it reaches that entity's derivations and no others.
    """
    return [
        a for a in af.arguments.values()
        if a.top_rule == vid and predicate_entity(a.conclusion) == entity
    ]


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
    # Attacks the arguments using the violated rule *for that entity* (III-11).
    #
    # An exclusion is scoped to the entity it was observed of. `Vyapti` writes
    # a rule as `consequent(Entity) :- ..., not scope_exclusion1(Entity)`, one
    # Entity variable throughout, so `perfectly_commoditized_market(acme)`
    # excludes V03 for acme and says nothing about globex. Triggering on any
    # entity and undercutting every entity denied conclusions that should
    # stand — one firm in a commoditized market suppressed the rule for all of
    # them. The block was unreachable dead code until rules began firing,
    # which is why it had never been evaluated.
    for vid, v in ks.vyaptis.items():
        for excl in v.scope_exclusions:
            excl_name = predicate_name(excl)
            # Match by predicate name, not exact string (III-09), and collect
            # the bindings the exclusion was actually observed for. A bare
            # exclusion fact binds to None, which is a binding like any other,
            # so a base written entirely in bare names behaves as before.
            excluded_entities = {
                predicate_entity(arg.conclusion)
                for arg in af.arguments.values()
                if predicate_name(arg.conclusion) == excl_name
            }
            for entity in sorted(
                excluded_entities, key=lambda e: (e is not None, e or "")
            ):
                rule_args = _rule_arguments_reached_by_exclusion(
                    af, vid, entity
                )
                if not rule_args:
                    continue
                # Renamed from _undercut_ to inapplicable_ (III-11), and bound,
                # so two entities excluded from one rule do not collide on a
                # single argument — the dedup guard below is per-entity for the
                # same reason.
                target_conclusion = with_entity(
                    f"inapplicable_{vid}", entity
                )
                if any(arg.conclusion == target_conclusion
                       for arg in af.arguments.values()):
                    continue
                scope_arg_id = af.next_arg_id()
                af.add_argument(Argument(
                    id=scope_arg_id,
                    conclusion=target_conclusion,
                    top_rule=None,
                    status_bound_by=(BOUND_ASSERTED,),
                    # The fact that excluded the rule, as observed rather than
                    # as the base declares it. With one undercutter per entity
                    # the bare name would read identically on all of them, and
                    # this premise is what vāda offers back as evidence to
                    # check.
                    premises=frozenset([with_entity(excl_name, entity)]),
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
                # Attack every argument this rule derived for this entity
                for rule_arg in rule_args:
                    if (scope_arg_id, rule_arg.id) not in existing_attacks:
                        af.add_attack(Attack(
                            attacker=scope_arg_id, target=rule_arg.id,
                            attack_type="undercutting",
                            hetvabhasa="savyabhicara"))
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
            status_bound_by=(BOUND_ASSERTED,),
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
