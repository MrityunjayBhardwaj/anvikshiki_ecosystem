# tests/test_layer_five_has_a_solver.py
"""Layer 5 can run, and the vocabulary it validates against is the one the
prompt handed out.

Two defects that only make sense together.

  #93  The grounding pipeline documents five layers of defense. The fifth —
       solver-feedback refinement — is guarded on `self.engine is not None`,
       and the one production construction site called
       `GroundingPipeline(active_ks)` with no solver. `use_solver` is True in
       FULL mode, which is the default; the second half is what was False,
       always. `refinement_rounds` was returned on every result and was
       structurally 0.

  #115 Which is why nobody noticed that the two sides of the boundary
       disagreed about what a valid predicate name is.
       `OntologySnippetBuilder` tells the model its vocabulary includes scope
       conditions — added deliberately, with an instruction to assert one when
       the query states it holds. `validate_predicates` builds its vocabulary
       from rule heads, `body_positive` and `body_negative`. Exclusions are
       `body_negative` and survive; scope conditions are in neither.

Measured before either was touched, over `business_expert.yaml`, no LLM:

    antecedent       superior_information          -> ACCEPTED
    consequent       pricing_power                 -> ACCEPTED
    scope EXCLUSION  subsidized_entity             -> ACCEPTED
    scope CONDITION  heterogeneous_quality_market  -> REJECTED

So wiring the solver in on its own would have spent up to three refinement
rounds per query deleting exactly the predicate the scope advisory needs, with
the feedback prompt telling the model to use ONLY predicates from the ontology
— for a predicate that is in the ontology it was shown.
"""

from types import SimpleNamespace

import pytest

from anvikshiki_v4.datalog_engine import DatalogEngine, EpistemicValue, Rule
from anvikshiki_v4.engine_factory import initialize_engine
from anvikshiki_v4.grounding import (
    GroundingPipeline,
    build_grounding_solver,
    ontology_vocabulary,
)
from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

KB_PATH = "anvikshiki_v4/data/business_expert.yaml"


@pytest.fixture
def ks():
    return load_knowledge_store(KB_PATH)


# ── #115: one vocabulary, read by both sides ─────────────────

class TestTheVocabularyIsShared:

    def test_scope_conditions_are_permitted(self, ks):
        vocabulary = ontology_vocabulary(ks)
        declared = {
            c for v in ks.vyaptis.values() for c in v.scope_conditions
        }
        assert declared, "fixture base declares no scope conditions"
        assert declared <= vocabulary.permitted

    def test_a_scope_name_that_is_also_an_antecedent_is_not_listed_twice(
        self, ks
    ):
        """One word cannot be told two different things about itself. A scope
        predicate that some rule also consumes is already assertable as a
        consumable name, and the prompt says something different about the
        scope-only section — assert one ONLY if the query states it."""
        vocabulary = ontology_vocabulary(ks)
        assert not (vocabulary.consumable & vocabulary.scope_only)

    def test_the_solver_accepts_every_name_the_prompt_permits(self, ks):
        """The boundary-pair law, and the reason this is a shared function
        rather than two computations that happen to agree today.

        Every name a grounded predicate may legitimately carry, asked of the
        validator that would reject it. One list, both sides.
        """
        solver = build_grounding_solver(ks)
        rejected = [
            name for name in sorted(ontology_vocabulary(ks).permitted)
            if solver.validate_predicates([f"{name}(acme)"])
        ]
        assert rejected == []

    def test_a_solver_without_the_vocabulary_rejects_them(self, ks):
        """The counterfactual, so the fix is demonstrated rather than
        asserted. This is the solver `kb_augmentation` builds — correct for
        what it does, which is compile-testing a rule set, and wrong as a
        validator for a prompt that permits more than the rules mention."""
        bare = DatalogEngine(boolean_mode=True)
        for v in ks.vyaptis.values():
            bare.add_rule(Rule(
                vyapti_id=v.id, name=v.name, head=v.consequent,
                body_positive=list(v.antecedents),
                body_negative=list(v.scope_exclusions),
                confidence=EpistemicValue.ESTABLISHED,
            ))
        conditions = sorted(ontology_vocabulary(ks).scope_only & {
            c for v in ks.vyaptis.values() for c in v.scope_conditions
        })
        assert conditions
        assert all(
            bare.validate_predicates([f"{c}(acme)"]) for c in conditions
        )

    def test_an_invented_name_is_still_rejected(self, ks):
        """Widening the vocabulary is not the same as abandoning it. If the
        validator accepted everything, wiring it in would be theatre."""
        solver = build_grounding_solver(ks)
        assert solver.validate_predicates(["utterly_invented_predicate(acme)"])

    def test_the_extra_vocabulary_derives_nothing(self, ks):
        """It says what may be *said*, not what can be *concluded*. A scope
        name is in no rule body, so evaluation cannot use it — asserting one
        must not quietly become a premise the solver reasons from."""
        from anvikshiki_v4.datalog_engine import Fact

        solver = build_grounding_solver(ks)
        condition = sorted(ontology_vocabulary(ks).scope_only)[0]
        solver.add_fact(Fact(predicate=condition, entity="acme"))
        solver.evaluate()
        assert [
            key for key in solver.facts if key != (condition, "acme")
        ] == []


# ── #93: the query path builds one ───────────────────────────

class TestTheQueryPathHasASolver:

    def test_the_factory_wires_one_in(self):
        """The defect exactly as filed, at the site it was filed against.
        `guide_dir=None` skips guide augmentation, so this costs no LLM call
        and does not depend on any guide being on disk."""
        engine, _ = initialize_engine(kb_yaml_path=KB_PATH, guide_dir=None)
        assert engine.grounding.engine is not None

    def test_the_wired_solver_carries_the_rules(self):
        engine, _ = initialize_engine(kb_yaml_path=KB_PATH, guide_dir=None)
        ks = load_knowledge_store(KB_PATH)
        assert len(engine.grounding.engine.rules) == len(ks.vyaptis)

    def test_the_wired_solver_agrees_with_this_engine_s_prompt(self):
        """Built from the *active* store, not the base one. T2b augmentation
        can add rules, and a validator built from the pre-augmentation base
        would reject names the augmented prompt permits — the same
        disagreement one layer along."""
        engine, artifacts = initialize_engine(
            kb_yaml_path=KB_PATH, guide_dir=None
        )
        permitted = ontology_vocabulary(artifacts.active_ks).permitted
        assert not [
            name for name in sorted(permitted)
            if engine.grounding.engine.validate_predicates([f"{name}(acme)"])
        ]


ENSEMBLE_N = 5


class _RefiningGrounder:
    """Five agreeing members emit an invalid predicate; the refinement call
    that follows emits a valid one.

    The whole ensemble agrees deliberately. Disagreement would put confidence
    below 0.9 and route through Layer 4's round-trip, which is two more LLM
    calls and a different feature — the law here is about Layer 5.
    """

    def __init__(self):
        self.calls = 0

    def __call__(self, **kwargs):
        self.calls += 1
        predicates = (["not_a_real_predicate(acme)"]
                      if self.calls <= ENSEMBLE_N
                      else ["superior_information(acme)"])
        return SimpleNamespace(predicates=predicates, relevant_vyaptis=[])


def _pipeline(ks, solver):
    pipeline = GroundingPipeline.__new__(GroundingPipeline)
    pipeline.ks = ks
    pipeline.grounder = _RefiningGrounder()
    pipeline.engine = solver
    return pipeline


class TestLayerFiveActuallyRefines:

    def test_a_rejected_predicate_is_fed_back_and_replaced(self, ks):
        pipeline = _pipeline(ks, build_grounding_solver(ks))
        result = pipeline._forward_ensemble(
            "q", "snippet", n=ENSEMBLE_N, use_solver=True
        )
        assert result.refinement_rounds == 1
        assert result.predicates == ["superior_information(acme)"]

    def test_without_a_solver_the_bad_predicate_survives(self, ks):
        """What every query did until now: the model's first answer is the
        final answer, in the mode chosen precisely because it is not."""
        pipeline = _pipeline(ks, None)
        result = pipeline._forward_ensemble(
            "q", "snippet", n=ENSEMBLE_N, use_solver=True
        )
        assert result.refinement_rounds == 0
        assert result.predicates == ["not_a_real_predicate(acme)"]

    def test_a_scope_condition_is_not_refined_away(self, ks):
        """The regression #115 would have caused, asserted directly.

        A query that establishes a rule's declared scope is the one case the
        scope advisory is waiting for, and Layer 5 must leave it alone.
        """
        condition = sorted({
            c for v in ks.vyaptis.values() for c in v.scope_conditions
        })[0]
        grounded = ["superior_information(acme)", f"{condition}(acme)"]

        pipeline = GroundingPipeline.__new__(GroundingPipeline)
        pipeline.ks = ks
        pipeline.engine = build_grounding_solver(ks)
        pipeline.grounder = lambda **kw: SimpleNamespace(
            predicates=list(grounded), relevant_vyaptis=[]
        )
        result = pipeline._forward_ensemble(
            "q", "snippet", n=ENSEMBLE_N, use_solver=True
        )
        assert result.refinement_rounds == 0
        assert sorted(result.predicates) == sorted(grounded)
