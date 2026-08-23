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

import re

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


# Words that negate a natural-language description. Names carry negation
# structurally, as a `not_` prefix; prose carries it lexically.
NEGATION_WORDS: frozenset[str] = frozenset({
    "not", "no", "never", "without", "lacks", "lacking", "absent",
    "absence", "fails", "failing", "cannot", "neither", "nor", "false",
})


def _tokens(text: str) -> list[str]:
    """Split a predicate name or a description into comparable word tokens."""
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def normalize_negation(name: str) -> str:
    """Eliminate double negations: not_not_X → X."""
    while name.startswith("not_not_"):
        name = name[8:]
    return name


def affirmative(name: str) -> str:
    """The unnegated form of a predicate name. not_X → X, X → X.

    Distinct from `get_contrary`, which flips the polarity in both directions.
    This one only ever removes negation, which is what a caller wants when it
    is about to *fall back* from the name as written to the concept underneath:
    for an already-affirmative name the two forms coincide, so the caller can
    compare them to see whether a second lookup is even worth doing.

    Double negation is eliminated first. A single-shot prefix strip on
    `not_not_X` leaves `not_X`, which in the knowledge base shipped here is a
    real and *opposite* predicate — the exact route by which a doubly-negated
    query matched the rule concluding the negation of what it asked about.
    """
    norm = normalize_negation(name)
    return norm[len(NEGATION_PREFIX):] if norm.startswith(
        NEGATION_PREFIX
    ) else norm


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


def predicate_entity(pred: str) -> str | None:
    """The entity a predicate is about: 'holds(acme)' → 'acme'.

    `None` for a bare predicate, which is a binding in its own right and not
    a missing value — every knowledge base in the tree writes rules as bare
    names, and matching two bare predicates against each other is the case
    that has always worked.

    Anything that opens a paren without closing one at the end is malformed
    and read as a bare name, so it can still match other bare names rather
    than becoming an entity nothing else can share.
    """
    paren = pred.find("(")
    if paren < 0 or not pred.endswith(")"):
        return None
    return pred[paren + 1:-1]


# Articles and corporate suffixes that distinguish two spellings of one
# subject without distinguishing two subjects. `the_firm` and `firm` are the
# same firm; `acme_corp` and `acme` are the same company. Deliberately short:
# every entry is a claim that two strings mean the same thing, and a wrong
# entry merges two real entities.
_ENTITY_ARTICLES = ("the_", "a_", "an_")
_ENTITY_SUFFIXES = (
    "_corp", "_corporation", "_inc", "_incorporated", "_ltd", "_limited",
    "_llc", "_plc", "_co", "_company", "_group", "_holdings",
)


def normalize_entity(entity: str | None) -> str | None:
    """A canonical form for comparing two spellings of one subject.

    NOT a repair. Nothing in the engine rewrites a binding to this value —
    `predicate_entity` still returns exactly what was written, because two
    spellings may genuinely be two companies and silently merging them is the
    failure the entity work exists to prevent.

    This exists so a caller can ask "could these be the same subject?" without
    deciding that they are. Two sites ask it for opposite reasons: the
    grounding ensemble, where N samplings of ONE query cannot be about two
    subjects, so agreement is safe to infer; and the engine boundary, where
    they might be, so divergence is reported rather than resolved.

    `None` — a bare predicate — normalises to `None`, because absence of a
    binding is a binding and not a spelling of one.
    """
    if entity is None:
        return None
    norm = entity.strip().strip("()\"' ").casefold()
    norm = re.sub(r"[\s\-.]+", "_", norm)
    norm = re.sub(r"_+", "_", norm).strip("_")
    for article in _ENTITY_ARTICLES:
        if norm.startswith(article) and len(norm) > len(article):
            norm = norm[len(article):]
            break
    for suffix in _ENTITY_SUFFIXES:
        if norm.endswith(suffix) and len(norm) > len(suffix):
            norm = norm[: -len(suffix)]
            break
    return norm.strip("_") or None


def entity_divergence(predicates: list[str]) -> dict[str, set[str]]:
    """Spellings that normalise alike, grouped by canonical form.

    Only groups with more than one raw spelling are returned, so an empty
    result means "no two of these could be the same subject written twice" —
    not "nothing was checked". Callers should print the number of predicates
    examined beside an empty result.
    """
    by_norm: dict[str, set[str]] = {}
    for pred in predicates:
        entity = predicate_entity(pred)
        if entity is None:
            continue
        by_norm.setdefault(normalize_entity(entity), set()).add(entity)
    return {k: v for k, v in by_norm.items() if len(v) > 1}


def with_entity(name: str, entity: str | None) -> str:
    """Rebuild a predicate from a name and a binding — the inverse of the pair
    above, so a rule can conclude about the entity it reasoned over.

    `with_entity(predicate_name(p), predicate_entity(p)) == p` for every
    well-formed `p`; a malformed one normalises to its bare name.
    """
    return name if entity is None else f"{name}({entity})"


def negation_differs(a: str, b: str) -> bool:
    """True when exactly one of the two names is negated."""
    na, nb = normalize_negation(a), normalize_negation(b)
    return na.startswith(NEGATION_PREFIX) != nb.startswith(NEGATION_PREFIX)


def polarity_opposed(
    a: str, b: str,
    extra_token_pairs: tuple[frozenset[str], ...] = (),
) -> frozenset[str] | None:
    """The opposing token pair the two names disagree on, if any.

    The opposing tokens must be ones that actually *distinguish* the two
    texts, so shared tokens are removed first. Otherwise a text carrying both
    sides of a pair — "retention rate is high (low churn)" holds high/low and
    retention/churn — reports itself as its own opposite, and descriptions
    that name a quantity alongside its complement never match anything,
    including themselves.

    So `high_retention` against `high_churn` is opposed on retention/churn,
    while `high_retention` against `retention_rate` is not opposed at all.
    """
    tokens_a, tokens_b = set(_tokens(a)), set(_tokens(b))
    only_a, only_b = tokens_a - tokens_b, tokens_b - tokens_a
    for pair in (*POLARITY_PAIRS, *DOMAIN_ANTONYMS, *extra_token_pairs):
        left, right = tuple(pair)
        if (left in only_a and right in only_b) or (
            right in only_a and left in only_b
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


def text_veto(a: str, b: str) -> str | None:
    """Why two natural-language descriptions must not be matched.

    The description counterpart of `match_veto`. Names carry negation
    structurally as a `not_` prefix; prose carries it lexically, so
    "value is created" and "value is not created" share every token that
    matters and differ only by the word that reverses them — the same defect
    the name matcher had, in a form where it is easier to hit.

    Argument order is not checked here. In a name, token position encodes the
    relation; in a sentence it does not, and reading order off prose would
    reject paraphrases for no reason.
    """
    tokens_a, tokens_b = set(_tokens(a)), set(_tokens(b))
    if not tokens_a or not tokens_b:
        return None

    neg_a = bool(tokens_a & NEGATION_WORDS)
    neg_b = bool(tokens_b & NEGATION_WORDS)
    if neg_a != neg_b:
        return "negation: one description negates and the other does not"

    opposed = polarity_opposed(a, b)
    if opposed is not None:
        return f"polarity: disagree on {'/'.join(sorted(opposed))}"

    return None


def are_contrary(
    a: str, b: str,
    knowledge_store=None,
) -> bool:
    """Whether two conclusions contradict each other.

    Three layers. The binding is checked first because it decides whether the
    other two are even the right question:
      0. the two conclusions are about the same entity
      1. syntactic not_ negation, with double negation eliminated
      2. the domain's own KnowledgeStore.contrariness_pairs

    Why the binding comes first
    ──────────────────────────
    `value_creation(acme)` and `not_value_creation(globex)` are perfectly
    compatible claims — acme creates value, globex does not, and both can hold
    at once. Treating them as contradictory is what made the compiler build a
    rebutting attack between them, and rebuttal reaches the labelling: a
    defeasible conclusion about one company was labelled OUT on the strength of
    an unrelated fact about another.

    Rebutting is defined as *concluding the contrary of the other's
    conclusion*, and the framework's conclusions are ground atoms — a vyāpti is
    `smoke(X) -> fire(X)`, and arguments are built by instantiating it, so
    `fire(acme)` and `fire(globex)` are two different atoms. The entity sits
    inside the atom being negated, not beside it. The contrary of
    `value_creation(acme)` is `not_value_creation(acme)` and nothing else.

    Consistency is the point. The rationality postulates require the accepted
    conclusions to be *consistent* and no two accepted arguments to attack each
    other. `{value_creation(acme), not_value_creation(globex)}` is satisfiable,
    so the first postulate asks nothing of it — but a spurious attack makes the
    second one force a conclusion out. Comparing names alone satisfies a
    postulate by manufacturing the inconsistency the postulate exists to rule
    out.

    A bare name is a binding, not a wildcard
    ────────────────────────────────────────
    `predicate_entity` returns `None` for a bare name, and that is a binding in
    its own right: two bare conclusions still rebut, which is what every
    fixture in the tree relies on. A bare conclusion is *not* read as "about
    every entity". After instantiation the framework holds no free variables —
    that is what grounding means — so a bare conclusion is a nullary ground
    atom, and reading it as universally quantified would put a quantifier back
    into the attack relation one layer after it was eliminated. If a bare
    predicate ever did mean "for all entities", the place to instantiate it is
    the grounder, which already contracts to emit `predicate_name(entity)`.

    The consequence is a known limit rather than an oversight: a bound
    conclusion does not rebut a bare one, so a real contradiction written
    across the two forms is missed. It is pinned by a test rather than left
    implicit.

    Restoring, not inventing
    ────────────────────────
    This is the behaviour the compiler shipped with. `_are_contrary` compared
    whole conclusion strings until the entity strip was added, and prefixing
    `not_` to the whole string kept acme and globex apart for free. The strip
    was needed for layer 2, which looks up bare names in the domain's pairs —
    so the binding check is added rather than the strip removed.
    """
    if predicate_entity(a) != predicate_entity(b):
        return False

    na = normalize_negation(predicate_name(a))
    nb = normalize_negation(predicate_name(b))

    if get_contrary(na) == nb:
        return True

    if knowledge_store is not None:
        for pair in knowledge_store.contrariness_pairs:
            if len(pair) == 2 and {na, nb} == {pair[0], pair[1]}:
                return True

    return False


