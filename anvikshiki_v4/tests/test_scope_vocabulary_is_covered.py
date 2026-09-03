# tests/test_scope_vocabulary_is_covered.py
"""A predicate the base itself declares is a word the base knows.

`SemanticCoverageAnalyzer` built its vocabulary from antecedents and
consequents only. Scope conditions and exclusions — the other two roles a
predicate has in a vyāpti, and the ones the grounder is explicitly shown and
told to assert when the query states them — were not in it, so coverage read
the base's own answer to its own question as a word it did not recognise.

The cost is not a lower ratio. Measured on the shipped base, no LLM:

    ['superior_information(acme)', 'heterogeneous_quality_market(acme)']
        before   ratio 0.50   PARTIAL    the condition unmatched
        after    ratio 1.00   FULL       the condition matched, and inert

    ['commercial_enterprise(startup)']          ← produced by a live run
        before   ratio 0.00   DECLINE
        after    ratio 1.00   PARTIAL

DECLINE diverts to augmentation, which asks whether a rule can be *invented*
for the predicate. So a query answering the base's own scope question sent the
engine off to invent a rule for a predicate that base had already declared.

What makes admitting them safe is #113's separation of vocabulary from
machinery, and that is asserted here rather than assumed: every scope
predicate in both shipped bases is inert by construction, so a query made only
of them is demoted to PARTIAL and never claims FULL.
"""

import pytest

from anvikshiki_v4.coverage import SemanticCoverageAnalyzer
from anvikshiki_v4.schema import (
    CausalStatus,
    Confidence,
    DomainType,
    EpistemicStatus,
    KnowledgeStore,
    Vyapti,
)
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

BASES = {
    "business": "anvikshiki_v4/data/business_expert.yaml",
    "copywriting": "anvikshiki_v4/data/copywriting_expert.yaml",
}
BOTH_BASES = pytest.mark.parametrize("base", sorted(BASES))


def _vyapti(vid, antecedents, consequent, **kw):
    return Vyapti(
        id=vid, name=vid, statement=f"{antecedents} implies {consequent}",
        causal_status=CausalStatus.EMPIRICAL,
        confidence=Confidence(existence=0.9, formulation=0.9,
                              evidence="theoretical"),
        epistemic_status=EpistemicStatus.ESTABLISHED,
        antecedents=antecedents, consequent=consequent, **kw
    )


@pytest.fixture
def ks(base):
    return load_knowledge_store(BASES[base])


def _conditions(ks):
    return sorted({c for v in ks.vyaptis.values() for c in v.scope_conditions})


def _exclusions(ks):
    return sorted({e for v in ks.vyaptis.values() for e in v.scope_exclusions})


class TestTheBasesOwnWordsAreRecognised:

    @BOTH_BASES
    def test_every_declared_scope_condition_is_matched(self, ks):
        conditions = _conditions(ks)
        assert conditions, "this base declares no scope conditions"
        result = SemanticCoverageAnalyzer(ks).analyze(
            [f"{c}(acme)" for c in conditions]
        )
        assert result.unmatched_predicates == []
        assert result.coverage_ratio == 1.0

    @BOTH_BASES
    def test_every_declared_scope_exclusion_is_matched(self, ks):
        exclusions = _exclusions(ks)
        assert exclusions, "this base declares no scope exclusions"
        result = SemanticCoverageAnalyzer(ks).analyze(
            [f"{e}(acme)" for e in exclusions]
        )
        assert result.unmatched_predicates == []

    @BOTH_BASES
    def test_a_scope_condition_routes_to_the_rule_that_declared_it(self, ks):
        """Matching without routing would leave the query recognised, inert,
        and pointed at no prose either — the same omission one level along.
        `relevant_vyaptis` is what retrieval reaches for chapters with."""
        condition = _conditions(ks)[0]
        declaring = sorted(
            vid for vid, v in ks.vyaptis.items()
            if condition in v.scope_conditions
        )
        result = SemanticCoverageAnalyzer(ks).analyze([f"{condition}(acme)"])
        assert set(declaring) <= set(result.relevant_vyaptis)

    @BOTH_BASES
    def test_a_rule_is_listed_once_however_many_roles_a_predicate_has(self, ks):
        """The index appends per role now, so a predicate that is both an
        antecedent and a scope condition of one rule must not name it twice."""
        for condition in _conditions(ks):
            vyaptis = SemanticCoverageAnalyzer(ks).analyze(
                [f"{condition}(acme)"]
            ).relevant_vyaptis
            assert len(vyaptis) == len(set(vyaptis))


class TestVocabularyIsNotMachinery:
    """#113's distinction is what makes admitting these predicates safe."""

    @BOTH_BASES
    def test_every_scope_predicate_in_a_shipped_base_is_inert(self, ks):
        """The property the whole treatment rests on, asserted rather than
        assumed. No scope predicate is any rule's antecedent, none is any
        rule's consequent, and none has a contrary that is concluded — so
        nothing can fire on one and nothing can be rebutted by one."""
        analyzer = SemanticCoverageAnalyzer(ks)
        not_inert = [
            p for p in _conditions(ks) + _exclusions(ks)
            if not analyzer._is_inert(p)
        ]
        assert not_inert == []

    @BOTH_BASES
    def test_a_query_made_only_of_scope_predicates_does_not_claim_full(self, ks):
        """FULL is a claim the base can reason about this query. It cannot
        reason with a scope predicate — it can only be told one."""
        result = SemanticCoverageAnalyzer(ks).analyze(
            [f"{c}(acme)" for c in _conditions(ks)]
        )
        assert result.coverage_ratio == 1.0
        assert result.decision == "PARTIAL"
        assert len(result.inert_predicates) == len(result.matched_predicates)

    @BOTH_BASES
    def test_a_scope_condition_beside_a_real_antecedent_routes_full(self, ks):
        """The mixed case, which is the common one: a query that says what it
        is about *and* that the rule's scope holds. Before, the second half
        pulled the ratio down for supplying exactly what the rule asked for."""
        antecedent = sorted({
            a for v in ks.vyaptis.values() for a in v.antecedents
        })[0]
        result = SemanticCoverageAnalyzer(ks).analyze(
            [f"{antecedent}(acme)", f"{_conditions(ks)[0]}(acme)"]
        )
        assert result.coverage_ratio == 1.0
        assert result.decision == "FULL"
        assert len(result.inert_predicates) == 1

    def test_the_live_case_no_longer_declines(self):
        """`commercial_enterprise(startup)` came out of a real grounding run
        and was filed under `unmatched_predicates`, scoring 0.00 and routing
        DECLINE — which diverts to augmentation, asking whether a rule can be
        invented for a predicate this base declares on V02."""
        ks = load_knowledge_store(BASES["business"])
        assert "commercial_enterprise" in _conditions(ks), (
            "fixture no longer demonstrates the case it exists for"
        )
        result = SemanticCoverageAnalyzer(ks).analyze(
            ["commercial_enterprise(startup)"]
        )
        assert result.decision == "PARTIAL"
        assert result.unmatched_predicates == []

    def test_a_scope_name_a_rule_can_consume_is_not_inert(self):
        """The guard on the reasoning above. Nothing in either shipped base is
        both a scope predicate and an antecedent, so the inertness of scope
        predicates is a fact about these bases and not a theorem. A base that
        used one in both roles must still report it as usable."""
        ks = KnowledgeStore(
            domain_type=DomainType.CRAFT,
            vyaptis={v.id: v for v in (
                _vyapti("V01", ["regulated_market"], "compliance_cost",
                        scope_conditions=["regulated_market"]),
            )},
        )
        result = SemanticCoverageAnalyzer(ks).analyze(["regulated_market(acme)"])
        assert result.inert_predicates == []
        assert result.decision == "FULL"

    def test_a_word_in_no_role_at_all_is_still_unmatched(self):
        """Widening the vocabulary is not abandoning it."""
        ks = load_knowledge_store(BASES["business"])
        result = SemanticCoverageAnalyzer(ks).analyze(
            ["utterly_unrelated_concept(acme)"]
        )
        assert result.unmatched_predicates == ["utterly_unrelated_concept(acme)"]
        assert result.decision == "DECLINE"
