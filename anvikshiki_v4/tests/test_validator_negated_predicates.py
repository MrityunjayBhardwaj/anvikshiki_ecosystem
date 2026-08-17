# anvikshiki_v4/tests/test_validator_negated_predicates.py
"""The Datalog validator's policy on negation, and the message it feeds back.

`validate_predicates` had no tests. It is the third module in this package to
keep its own idea of what `not_` means, and the second to strip the prefix
before looking the predicate up — after coverage routing, which was fixed for
the same reason. `known_preds` is built from rule *heads* as well as bodies, so
a negated name can legitimately be in it, and stripping first rejected exactly
those.

Two things are asserted here that are easy to mistake for each other:

1. *The affirmative fallback is policy, not leniency.* A query asserting
   `not_X` against a vocabulary that knows `X` is about a concept the knowledge
   base holds. This is the same call coverage routing makes, deliberately, and
   the two modules are asserted to agree.

2. *Order and double-negation elimination are the fix.* As-written first, so a
   literal negated predicate is found; `not_not_X → X` before either lookup, so
   a single strip cannot land on the *opposite* predicate and accept a name
   whose actual meaning is absent from the vocabulary.

The error message is not cosmetic. Layer 5 of the grounding defense puts it
into a prompt and asks a model to fix the predicates, up to three times — so a
message that rejects a predicate while listing it as valid on the same line is
a self-contradicting instruction, repeated.
"""

import pytest

from anvikshiki_v4.datalog_engine import DatalogEngine, EpistemicValue, Rule


def _engine(*rules: tuple[str, list[str], list[str]]) -> DatalogEngine:
    """An engine holding the given (head, positive, negative) rules."""
    engine = DatalogEngine(boolean_mode=True)
    for i, (head, positive, negative) in enumerate(rules, start=1):
        engine.add_rule(Rule(
            vyapti_id=f"V{i:02d}", name=f"V{i:02d}", head=head,
            body_positive=positive, body_negative=negative,
            confidence=EpistemicValue.ESTABLISHED,
        ))
    return engine


@pytest.fixture
def one_sided():
    """A base that concludes a negation without asserting its affirmative.

    Modelled on V11 of the shipped knowledge base — "The Growth Trap", whose
    consequent is `not_value_creation` — but with `value_creation` absent,
    which is what makes the defect reachable. The shipped base happens to name
    both forms, so the bug hid there; a knowledge base concluding a negation
    without separately asserting its affirmative is an ordinary thing.
    """
    return _engine(("not_value_creation", ["organizational_growth"], []))


@pytest.fixture
def two_sided():
    """A base holding both an affirmative predicate and its literal negation."""
    return _engine(
        ("value_creation", ["positive_unit_economics"], []),
        ("not_value_creation", ["organizational_growth"], []),
    )


# ── The filed defect ─────────────────────────────────────────

def test_a_negated_predicate_in_the_vocabulary_is_accepted(one_sided):
    """The observed case.

    Before: rejected, because the prefix was stripped to `value_creation`,
    which this base does not name.
    """
    assert one_sided.validate_predicates(["not_value_creation(acme)"]) == []


def test_the_error_never_names_a_predicate_absent_from_its_own_input(
    one_sided,
):
    """The sharpest half of the defect, and the reason it is worth a test.

    Before: `Unknown predicate: 'value_creation' — valid: ['not_value_creation',
    'organizational_growth']`. The name complained about appears nowhere in the
    input, and the name that does appear is listed as valid on the same line.
    """
    errors = one_sided.validate_predicates(["not_value_creation(acme)"])
    assert errors == [], errors

    # And when a predicate really is unknown, the message names what was asked
    # about rather than a string derived from it.
    unknown = one_sided.validate_predicates(["value_creation(acme)"])
    assert len(unknown) == 1
    assert "'value_creation'" in unknown[0]


def test_the_message_never_rejects_a_name_it_lists_as_valid(two_sided):
    """The self-contradiction, asserted directly over every reachable name.

    A message can be wrong in ways a single example misses, so this asks the
    question of the whole vocabulary plus its negations.
    """
    known = set()
    for rule in two_sided.rules:
        known.add(rule.head)
        known.update(rule.body_positive)
        known.update(rule.body_negative)

    queries = [f"{p}(acme)" for p in sorted(known)]
    queries += [f"not_{p}(acme)" for p in sorted(known)]
    queries.append("nothing_like_a_real_predicate(acme)")

    contradictions = []
    for query in queries:
        for error in two_sided.validate_predicates([query]):
            rejected = error.split("'")[1]
            if rejected in known:
                contradictions.append((query, error))

    assert not contradictions, contradictions
    assert len(queries) == 2 * len(known) + 1  # the scan really ran


# ── Double negation ──────────────────────────────────────────

def test_a_doubly_negated_name_is_rejected_when_its_meaning_is_absent(
    one_sided,
):
    """The second defect, found by running the validator rather than reading it.

    `not_not_value_creation` means `value_creation`, which this base does not
    name — so it must be rejected. Before, a single strip left
    `not_value_creation`, which *is* in the vocabulary, so the validator
    accepted a predicate on the strength of finding its opposite. Layer 5 of
    the grounding defense waved it straight through.
    """
    errors = one_sided.validate_predicates(["not_not_value_creation(acme)"])
    assert len(errors) == 1
    assert "'value_creation'" in errors[0]


def test_a_doubly_negated_name_is_accepted_when_its_meaning_is_present(
    two_sided,
):
    """The same normalisation in the other direction.

    This is the case the fix changes against the shipped knowledge base: every
    `not_not_X` for an X the base names was rejected, and each rejection cost
    up to three LLM refinement rounds chasing an error that was not one.
    """
    assert two_sided.validate_predicates(
        ["not_not_value_creation(acme)"]
    ) == []


def test_the_message_names_the_literal_too_when_normalisation_moved_it(
    one_sided,
):
    """Double negation is the one case where looked-up ≠ typed, so say both.

    Naming only the canonical form would reintroduce the original complaint —
    an error naming a string the caller never wrote — for a caller who wrote a
    doubly-negated name.
    """
    error = one_sided.validate_predicates(
        ["not_not_value_creation(acme)"]
    )[0]
    assert "'value_creation'" in error
    assert "not_not_value_creation" in error


def test_negation_depth_alternates(two_sided):
    """Odd depths are the negation, even depths the affirmative.

    Both are in this vocabulary, so every depth is accepted — the assertion
    that bites is on the one-sided base, where they alternate accept/reject.
    """
    for depth in range(5):
        name = "not_" * depth + "value_creation"
        assert two_sided.validate_predicates([f"{name}(acme)"]) == [], name

    one_sided = _engine(("not_value_creation", ["organizational_growth"], []))
    verdicts = {
        depth: not one_sided.validate_predicates(
            ["not_" * depth + "value_creation(acme)"]
        )
        for depth in range(5)
    }
    assert verdicts == {0: False, 1: True, 2: False, 3: True, 4: False}


# ── The fallback is policy, and is bounded ───────────────────

def test_the_negation_of_a_known_predicate_is_accepted(two_sided):
    """Decision (1) from the module docstring, asserted so a change argues.

    `positive_unit_economics` is in the vocabulary and its negation is not, so
    this is the fallback path rather than an as-written hit.
    """
    assert two_sided.validate_predicates(
        ["not_positive_unit_economics(acme)"]
    ) == []


def test_an_unknown_predicate_is_still_rejected(two_sided):
    """The fix reorders lookups; it does not make the validator permissive."""
    errors = two_sided.validate_predicates(["shareholder_delight(acme)"])
    assert len(errors) == 1
    assert "Unknown predicate: 'shareholder_delight'" in errors[0]


def test_the_negation_of_an_unknown_predicate_is_still_rejected(two_sided):
    """Both forms miss, so both lookups fail and the error names what was asked."""
    errors = two_sided.validate_predicates(["not_shareholder_delight(acme)"])
    assert len(errors) == 1
    assert "'not_shareholder_delight'" in errors[0]


def test_malformed_input_is_unchanged(two_sided):
    """The arity check is upstream of the vocabulary lookup and stays there."""
    errors = two_sided.validate_predicates(["garbled"])
    assert len(errors) == 1
    assert errors[0].startswith("Malformed:")


def test_facts_contribute_to_the_vocabulary_including_negated_ones():
    """`known_preds` is seeded from facts as well as rules.

    A negated predicate can arrive that way too, so the as-written lookup has
    to see facts and not only rule heads.
    """
    from anvikshiki_v4.datalog_engine import Fact

    engine = _engine(("value_creation", ["positive_unit_economics"], []))
    engine.add_fact(Fact(predicate="not_regulated_industry", entity="acme"))
    assert engine.validate_predicates(
        ["not_regulated_industry(acme)"]
    ) == []


# ── One package, one idea of what not_ means ─────────────────

def test_the_validator_and_coverage_routing_agree_on_the_same_vocabulary():
    """The consolidation, as a cross-module assertion.

    The package held two opposite beliefs about `X` and `not_X` once already —
    the compiler treating them as contradictory while the evaluator scored them
    a match. Both modules now read `predicate_contrariness`, so a query the
    validator accepts is one coverage routes, and a divergence fails here
    instead of surfacing as a routing bug months later.
    """
    from anvikshiki_v4.coverage import SemanticCoverageAnalyzer
    from anvikshiki_v4.schema import (
        CausalStatus, Confidence, DomainType, EpistemicStatus, KnowledgeStore,
        Vyapti,
    )

    def vyapti(vid, antecedents, consequent):
        return Vyapti(
            id=vid, name=vid, statement=f"{antecedents} implies {consequent}",
            causal_status=CausalStatus.EMPIRICAL,
            confidence=Confidence(
                existence=0.9, formulation=0.9, evidence="theoretical"
            ),
            epistemic_status=EpistemicStatus.ESTABLISHED,
            antecedents=antecedents, consequent=consequent,
        )

    specs = [
        ("V01", ["positive_unit_economics"], "value_creation"),
        ("V11", ["organizational_growth"], "not_value_creation"),
    ]
    ks = KnowledgeStore(
        domain_type=DomainType.CRAFT,
        vyaptis={s[0]: vyapti(*s) for s in specs},
    )
    analyzer = SemanticCoverageAnalyzer(ks)
    engine = _engine(*[(c, a, []) for _vid, a, c in specs])

    names = ["value_creation", "not_value_creation", "positive_unit_economics",
             "not_positive_unit_economics", "not_not_value_creation",
             "not_not_not_value_creation", "unrelated_entirely"]
    disagreements = []
    for name in names:
        validator_ok = not engine.validate_predicates([f"{name}(acme)"])
        # Coverage's token layer is fuzzy by design, so compare against its
        # two exact-vocabulary layers rather than against overlap.
        routed = analyzer.analyze([name])
        coverage_ok = routed.match_details.get(name, "").endswith(
            ("exact", "synonym")
        )
        if validator_ok != coverage_ok:
            disagreements.append((name, validator_ok, coverage_ok))

    assert not disagreements, disagreements
    assert len(names) == 7  # the loop really ran


def test_no_module_outside_predicate_contrariness_strips_not_itself():
    """Three modules had their own copy of this rule; two of them were wrong.

    Asserted by parsing the package rather than by convention, because the
    failure mode is someone adding a fourth copy — and a fourth copy is
    invisible to every behavioural test above until it is reached by an input
    nobody thought of.
    """
    import pathlib

    root = pathlib.Path(__file__).resolve().parent.parent
    modules = [
        path for path in sorted(root.glob("*.py"))
        if path.name != "predicate_contrariness.py"
    ]
    assert len(modules) > 20, f"only found {len(modules)} modules to scan"

    offenders = {}
    for path in modules:
        lines = [
            f"{path.name}:{n}: {line.strip()}"
            for n, line in enumerate(
                path.read_text().splitlines(), start=1
            )
            if 'startswith("not_")' in line or '[4:]' in line
        ]
        if lines:
            offenders[path.name] = lines

    assert not offenders, (
        "these modules strip the negation prefix themselves instead of "
        f"calling predicate_contrariness: {offenders}"
    )


# ── The real knowledge base exercises this ───────────────────

def test_the_shipped_knowledge_base_reaches_the_negated_path():
    """Guard against the fixtures drifting away from the shipped data.

    The one-sided fixture above is not what ships: `business_expert.yaml`
    names both `value_creation` and `not_value_creation`, which is exactly why
    the filed defect was unreachable through it. What *is* reachable there is
    the double-negation half, and that is asserted here on real data.
    """
    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

    ks = load_knowledge_store("anvikshiki_v4/data/business_expert.yaml")
    engine = _engine(*[
        (v.consequent, list(v.antecedents), list(v.scope_exclusions))
        for v in ks.vyaptis.values()
    ])

    literal_negations = sorted({
        pred
        for v in ks.vyaptis.values()
        for pred in list(v.antecedents) + [v.consequent]
        if pred.startswith("not_")
    })
    assert literal_negations, (
        "the shipped knowledge base no longer holds a literal negated "
        "predicate, so the fixtures above no longer model real data"
    )

    for pred in literal_negations:
        assert engine.validate_predicates([f"{pred}(acme)"]) == [], pred

    # Every name the base knows, doubly negated, is that same name — and was
    # rejected before the fix.
    known = sorted(
        {r.head for r in engine.rules}
        | {p for r in engine.rules for p in r.body_positive}
        | {p for r in engine.rules for p in r.body_negative}
    )
    assert len(known) > 10, f"only {len(known)} predicates in the shipped base"
    for pred in known:
        assert engine.validate_predicates([f"not_not_{pred}(acme)"]) == [], pred
