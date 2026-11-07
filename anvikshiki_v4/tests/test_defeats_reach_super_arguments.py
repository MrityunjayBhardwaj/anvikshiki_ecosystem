"""A defeat on an argument reaches every argument built on it (#287), and a
scope undercutter stands or falls with the fact that excluded the rule (#255).

ASPIC+ treats an attack on a sub-argument as an attack on whatever contains
it, decided against the sub-argument. The engine checked an attack only
against its target, so a conclusion could stand on a premise that had already
fallen: `value_creation` stayed established on a premise the question also
denied.
"""

import pytest

from anvikshiki_v4.argumentation import ArgumentationFramework
from anvikshiki_v4.engine_v4 import attack_violations
from anvikshiki_v4.schema import EpistemicStatus as KB
from anvikshiki_v4.schema_v4 import (
    Argument, Attack, EpistemicStatus, Label, PramanaType, ProvenanceTag,
)
from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store
from anvikshiki_v4.tests.test_question_is_not_evidence import _rule, _store


def _compile(kb, *facts):
    ks = kb if not isinstance(kb, str) else load_knowledge_store(
        f"anvikshiki_v4/data/{kb}_expert.yaml")
    af = compile_t2(ks, [{"predicate": p, "confidence": 0.9} for p in facts])
    af.compute_grounded()
    return af


def _labels(af, conclusion):
    return {af.labels[a.id] for a in af.arguments.values() if a.conclusion == conclusion}


def _status(af, conclusion):
    return af.get_epistemic_status(conclusion)[0]


# ── a contested or defeated premise reaches what is built on it ─

def test_a_conclusion_on_a_contested_premise_is_open_not_established():
    """The question supposes a premise and its negation. Neither is accepted,
    so nothing that needs the premise is accepted either."""
    af = _compile("business", "positive_unit_economics(acme)",
                  "not_positive_unit_economics(acme)")
    assert _labels(af, "positive_unit_economics(acme)") == {Label.UNDECIDED}
    assert _labels(af, "value_creation(acme)") == {Label.UNDECIDED}
    assert _status(af, "value_creation(acme)") is EpistemicStatus.OPEN


def test_a_rule_switched_off_switches_off_what_is_chained_from_it():
    """`captive_audience` excludes V01 for acme, so `persuasion_possible`
    falls; V03 needs it, so `reader_receptive` falls with it."""
    on = ("attention_captured(acme)", "problem_first_sequence(acme)")
    af = _compile("copywriting", *on)
    assert _labels(af, "reader_receptive(acme)") == {Label.IN}
    af = _compile("copywriting", *on, "captive_audience(acme)")
    assert _labels(af, "persuasion_possible(acme)") == {Label.OUT}
    assert _labels(af, "reader_receptive(acme)") == {Label.OUT}


def _hand(sub_strict, attacker_pramana):
    """P, a defeasible premise; S, a strict rule built on it; X rebuts P."""
    tag = lambda p: ProvenanceTag(pramana_type=p)
    af = ArgumentationFramework()
    af.add_argument(Argument(id="P", conclusion="p", top_rule=None, is_strict=sub_strict,
                             tag=tag(PramanaType.ANUMANA), status=EpistemicStatus.HYPOTHESIS))
    af.add_argument(Argument(id="S", conclusion="s", top_rule="R", sub_arguments=("P",),
                             is_strict=True, tag=tag(PramanaType.PRATYAKSA),
                             status=EpistemicStatus.ESTABLISHED))
    af.add_argument(Argument(id="X", conclusion="not_p", top_rule=None,
                             tag=tag(attacker_pramana), status=EpistemicStatus.HYPOTHESIS))
    af.add_attack(Attack(attacker="X", target="P", attack_type="rebutting",
                         hetvabhasa="viruddha"))
    return af


@pytest.mark.parametrize("sub_strict, attacker, s_label", [
    (False, PramanaType.ANUMANA, Label.OUT),   # succeeds on P, so reaches S
    (False, PramanaType.UPAMANA, Label.IN),    # fails on P: weaker attacker
    (True, PramanaType.ANUMANA, Label.IN),     # fails on P: a strict premise
])
def test_success_is_decided_against_the_argument_attacked(sub_strict, attacker, s_label):
    """S is strict and PRATYAKSA, so decided against S every rebuttal would
    fail. Decided against P, the one attacked, it succeeds exactly when it
    succeeds on P."""
    labels = _hand(sub_strict, attacker).compute_grounded()
    assert labels["S"] is s_label
    assert labels["P"] is s_label


def test_the_answer_names_the_attack_that_took_a_chained_conclusion_down():
    af = _compile("copywriting", "attention_captured(acme)", "problem_first_sequence(acme)",
                  "captive_audience(acme)")
    named = {v["target_conclusion"] for v in attack_violations(af, af.labels)}
    assert {"persuasion_possible(acme)", "reader_receptive(acme)"} <= named


# ── the scope undercutter (#255) ───────────────────────────────

def test_an_exclusion_the_question_also_denies_leaves_the_rule_open():
    af = _compile("business", "superior_information(acme)",
                  "perfectly_commoditized_market(acme)",
                  "not_perfectly_commoditized_market(acme)")
    assert _labels(af, "inapplicable_V03(acme)") == {Label.UNDECIDED}
    assert _status(af, "pricing_power(acme)") is EpistemicStatus.OPEN


def test_an_exclusion_nobody_denies_still_switches_the_rule_off():
    af = _compile("business", "superior_information(acme)",
                  "perfectly_commoditized_market(acme)")
    assert _labels(af, "pricing_power(acme)") == {Label.OUT}


def test_an_undercutter_is_strict_only_when_what_it_rests_on_is():
    af = _compile("business", "superior_information(acme)",
                  "perfectly_commoditized_market(acme)")
    (u,) = [a for a in af.arguments.values() if a.conclusion == "inapplicable_V03(acme)"]
    (ex,) = [a for a in af.arguments.values()
             if a.conclusion == "perfectly_commoditized_market(acme)"]
    assert (u.sub_arguments, u.is_strict, u.status, u.tag) == \
        ((ex.id,), ex.is_strict, ex.status, ex.tag)
    assert u.is_strict is False


def test_a_rule_argument_derived_after_the_undercutter_is_undercut_too():
    """V01 reads `b`, which V02 derives one round later. The first V01
    argument, from the supposed `b`, meets the undercutter in round one; the
    second, from the derived `b`, arrives in round two. The undercutter used
    to be skipped once built, and the second argument stood."""
    store = _store(
        _rule("V01", ["b"], "c", KB.ESTABLISHED, scope_exclusions=["ex"]),
        _rule("V02", ["a"], "b", KB.ESTABLISHED),
    )
    af = _compile(store, "b", "a", "ex")
    v01 = [a for a in af.arguments.values() if a.top_rule == "V01"]
    assert len(v01) == 2
    assert {af.labels[a.id] for a in v01} == {Label.OUT}
