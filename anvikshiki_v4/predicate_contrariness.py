# anvikshiki_v4/predicate_contrariness.py
"""When two predicate names must NOT be treated as the same predicate.

The package held two opposite beliefs about the same string pair. The compiler
treats `X` and `not_X` as contradictory — that is the trigger for the rebutting
attacks the whole argumentation layer is built on — while the evaluator scored
`value_creation` against `not_value_creation` at 0.667 and called it a match.
Two modules, one package, and the engine's core semantics siding against its
own instrument.

The consequence was not subtle: an extractor emitting the exact logical inverse
of every gold predicate scored precision 1.000, recall 1.000. A matcher that
loose does not add noise to a measurement, it inverts the conclusion.

So contrariness lives here, once, and the compiler, the evaluator and coverage
routing all read it.

Why a veto rather than a better similarity score
────────────────────────────────────────────────
Similarity is statistical; this is not. `ltv_exceeds_cac` and `cac_exceeds_ltv`
score a perfect 1.000 under any bag-of-tokens measure, because bag-of-tokens
discards the relation the predicate exists to express — no threshold anywhere
in (0, 1] excludes it. A veto sits above the score and refuses the match
outright, which makes the guarantee absolute instead of a matter of tuning.

What this is not
────────────────
`DOMAIN_ANTONYMS` is not a theory of antonymy and does not pretend to be
complete. It is a list, and a list will miss pairs. That incompleteness is a
known limit to be measured by instrument validation against human judgment,
not a gap to be talked around: a veto that misses a pair leaves the old
behaviour for that pair, which is a false match, and the number of those is an
empirical question nobody has answered yet.
"""

from __future__ import annotations

NEGATION_PREFIX = "not_"

# Morphological and generic polarity oppositions. A pair here means: if one
# name carries one token and the other name carries its opposite, the two names
# assert opposing things and cannot be the same predicate.
POLARITY_PAIRS: tuple[frozenset[str], ...] = tuple(
    frozenset(pair) for pair in [
        ("positive", "negative"),
        ("real", "imagined"),
        ("high", "low"),
        ("strong", "weak"),
        ("growing", "declining"),
        ("rising", "falling"),
        ("increasing", "decreasing"),
        ("above", "below"),
        ("over", "under"),
        ("more", "less"),
        ("with", "without"),
        ("sustainable", "unsustainable"),
        ("profitable", "unprofitable"),
    ]
)

# Domain vocabulary whose opposition is lexical rather than morphological —
# nothing in the shape of "retention" says it is the opposite of "churn".
# Seeded from pairs observed to defeat the old matcher. Extend per domain, and
# prefer KnowledgeStore.contrariness_pairs where the domain declares its own.
DOMAIN_ANTONYMS: tuple[frozenset[str], ...] = tuple(
    frozenset(pair) for pair in [
        ("retention", "churn"),
        ("creation", "destruction"),
        ("growth", "decline"),
        ("gain", "loss"),
        ("surplus", "deficit"),
    ]
)

# Tokens that make a predicate relational, so that operand order carries the
# meaning. `ltv_exceeds_cac` and `cac_exceeds_ltv` are opposite claims built
# from identical tokens.
RELATIONAL_TOKENS: frozenset[str] = frozenset({
    "exceeds", "above", "below", "outpaces", "beats", "precedes",
    "drives", "causes", "requires", "implies", "dominates",
})


def _tokens(name: str) -> list[str]:
    return [t for t in name.lower().replace("-", "_").split("_") if t]


def normalize_negation(name: str) -> str:
    """Eliminate double negations: not_not_X → X."""
    while name.startswith("not_not_"):
        name = name[8:]
    return name


def get_contrary(name: str) -> str:
    """The contrary of a predicate name. not_X → X, X → not_X."""
    norm = normalize_negation(name)
    if norm.startswith(NEGATION_PREFIX):
        return norm[len(NEGATION_PREFIX):]
    return f"{NEGATION_PREFIX}{norm}"


def predicate_name(pred: str) -> str:
    """Strip the entity argument: 'holds(acme)' → 'holds'."""
    paren = pred.find("(")
    return pred[:paren] if paren >= 0 else pred


def negation_differs(a: str, b: str) -> bool:
    """True when exactly one of the two names is negated."""
    na, nb = normalize_negation(a), normalize_negation(b)
    return na.startswith(NEGATION_PREFIX) != nb.startswith(NEGATION_PREFIX)


def polarity_opposed(
    a: str, b: str,
    extra_token_pairs: tuple[frozenset[str], ...] = (),
) -> frozenset[str] | None:
    """The opposing token pair the two names disagree on, if any.

    Only fires when one name carries one side and the other carries the other
    side, so `high_retention` against `high_churn` is opposed while
    `high_retention` against `retention_rate` is not.
    """
    tokens_a, tokens_b = set(_tokens(a)), set(_tokens(b))
    for pair in (*POLARITY_PAIRS, *DOMAIN_ANTONYMS, *extra_token_pairs):
        left, right = tuple(pair)
        if (left in tokens_a and right in tokens_b) or (
            right in tokens_a and left in tokens_b
        ):
            return pair
    return None


def relational_order_differs(a: str, b: str) -> bool:
    """True when two relational predicates share operands but reverse them.

    Requires the same relational token on both sides and the same operand
    multiset — otherwise the two names are simply different predicates and
    ordinary similarity should decide, not this veto.
    """
    ta, tb = _tokens(a), _tokens(b)
    rel_a = [t for t in ta if t in RELATIONAL_TOKENS]
    rel_b = [t for t in tb if t in RELATIONAL_TOKENS]
    if not rel_a or rel_a != rel_b:
        return False

    rel = rel_a[0]
    left_a, right_a = ta[:ta.index(rel)], ta[ta.index(rel) + 1:]
    left_b, right_b = tb[:tb.index(rel)], tb[tb.index(rel) + 1:]
    if sorted(left_a + right_a) != sorted(left_b + right_b):
        return False
    return left_a == right_b and right_a == left_b and left_a != left_b


def match_veto(
    a: str, b: str,
    extra_token_pairs: tuple[frozenset[str], ...] = (),
    knowledge_store=None,
) -> str | None:
    """Why these two names must not be matched, or None if nothing forbids it.

    The reason is returned rather than a bare bool so a rejected match can be
    reported as "refused because these disagree on positive/negative" instead
    of vanishing into a score.

    `extra_token_pairs` are opposing *tokens*; `knowledge_store` supplies the
    domain's opposing *whole predicate names*. They are different things and
    are checked separately — a KB pair like
    ["value_creation", "value_destruction"] names two predicates, and looking
    for it among underscore-split tokens would never find it.
    """
    na, nb = predicate_name(a), predicate_name(b)
    if normalize_negation(na) == normalize_negation(nb):
        return None

    if negation_differs(na, nb):
        return "negation: exactly one of the two is negated"

    if knowledge_store is not None and are_contrary(na, nb, knowledge_store):
        return "contrariness: the domain declares these two opposed"

    opposed = polarity_opposed(na, nb, extra_token_pairs)
    if opposed is not None:
        return f"polarity: disagree on {'/'.join(sorted(opposed))}"

    if relational_order_differs(na, nb):
        return "argument order: same relation, operands reversed"

    return None


def are_contrary(
    a: str, b: str,
    knowledge_store=None,
) -> bool:
    """Whether two conclusions contradict each other.

    Two layers, unchanged from the compiler's original behaviour:
      1. syntactic not_ negation, with double negation eliminated
      2. the domain's own KnowledgeStore.contrariness_pairs
    """
    na = normalize_negation(predicate_name(a))
    nb = normalize_negation(predicate_name(b))

    if get_contrary(na) == nb:
        return True

    if knowledge_store is not None:
        for pair in knowledge_store.contrariness_pairs:
            if len(pair) == 2 and {na, nb} == {pair[0], pair[1]}:
                return True

    return False


