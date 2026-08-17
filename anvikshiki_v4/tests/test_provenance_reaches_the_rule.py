# tests/test_provenance_reaches_the_rule.py
"""Provenance is computed per candidate; these check it survives to the rule.

It did not. Both Stage D construction sites built a `ProposedVyapti` without
passing `provenance=`, so every rule extraction had ever produced carried an
empty list — and `Vyapti`, which is what actually reaches the knowledge base,
had no field to put one in at all. A citation tier over those lists would have
reported the same value after every source gained a resolvable identifier,
because the identifiers would be attached to sources the rule never receives.

The shape has a precedent here: something computed correctly per item and
discarded at the point the items are rolled up, so the roll-up reports an
absence the underlying data does not have.
"""

import ast
import json

from anvikshiki_v4.extraction_schema import (
    CandidatePredicate,
    ClaimType,
    ExtractionConfig,
    PredicateNode,
    PredicateRelation,
    Provenance,
    ProposedVyapti,
    StageAOutput,
    StageBOutput,
    StageCOutput,
    StageDOutput,
)
from anvikshiki_v4.predicate_extraction import StageDConstructor, StageEValidator
from anvikshiki_v4.schema import DomainType, KnowledgeStore, Vyapti


def _candidate(name: str, quote: str = "A span from the chapter.",
               paragraph: int = 0, **kwargs) -> CandidatePredicate:
    return CandidatePredicate(
        name=name,
        description=f"description of {name}",
        claim_type=kwargs.pop("claim_type", ClaimType.CAUSAL),
        provenance=Provenance(
            chapter_id="ch02",
            section_header="Unit economics",
            paragraph_index=paragraph,
            quote=quote,
            quote_found_in_source=True,
        ),
        **kwargs,
    )


def _stage_d() -> StageDConstructor:
    return StageDConstructor(
        KnowledgeStore(domain_type=DomainType.CRAFT), ExtractionConfig()
    )


# ── the standalone path ──

def test_a_standalone_rule_carries_the_candidate_that_built_it():
    """No model is called: with no Stage B nodes only the standalone branch runs.

    This rule's statement is taken from the candidate's quote a few lines
    above the construction, so a rule that keeps the quote and drops the
    record of where it came from is quoting a source it cannot name.
    """
    candidate = _candidate("cash_burn_accelerating")
    out = _stage_d()(
        stage_a=StageAOutput(candidates=[candidate], chapter_id="ch02"),
        stage_b=StageBOutput(nodes={}),
        stage_c=StageCOutput(vocabulary=["cash_burn_accelerating"]),
        guide_text={},
    )

    assert len(out.new_vyaptis) == 1, "the standalone path did not fire"
    rule = out.new_vyaptis[0]
    assert rule.provenance_attached is True
    assert [p.quote for p in rule.provenance] == ["A span from the chapter."]
    assert rule.provenance[0].chapter_id == "ch02"
    assert rule.provenance[0].paragraph_index == 0


# ── the sub-rule path ──

class _StubConstructor:
    """Stands in for the LLM call so the sub-rule branch can be reached.

    The branch is unreachable without it — it calls the constructor before
    building anything, and an exception there is swallowed by a `continue`,
    which would make this test pass by producing no rules at all.
    """

    def __init__(self):
        self.calls = 0

    def __call__(self, **kwargs):
        self.calls += 1
        return type("Result", (), {
            "name": "a sub-rule",
            "statement": "the model's sentence",
            "causal_status": "empirical",
            "scope_conditions": [],
            "scope_exclusions": [],
            "confidence_existence": 0.7,
            "confidence_formulation": 0.6,
            "epistemic_status": "hypothesis",
            "sources": [],
        })()


def _run_sub_rule_path(candidates, node_name="churn_rising",
                       parent="unit_economics_negative"):
    stage_d = _stage_d()
    stub = _StubConstructor()
    stage_d.constructor = stub
    out = stage_d(
        stage_a=StageAOutput(candidates=candidates, chapter_id="ch02"),
        stage_b=StageBOutput(nodes={
            node_name: PredicateNode(
                predicate=node_name,
                description="a decomposed predicate",
                parent=parent,
                relation_to_parent=PredicateRelation.COMPOSES,
                depth=1,
            )
        }),
        stage_c=StageCOutput(vocabulary=[node_name]),
        guide_text={"ch02": "chapter text"},
    )
    assert stub.calls == 1, "the sub-rule branch never ran"
    rules = out.new_vyaptis + out.refinement_vyaptis
    assert len(rules) == 1, f"expected one sub-rule, got {len(rules)}"
    return rules[0]


def test_a_sub_rule_collects_the_candidates_at_both_ends():
    """Antecedent and consequent are both predicates and both may have a record."""
    rule = _run_sub_rule_path([
        _candidate("churn_rising", quote="Churn began to climb.", paragraph=3),
        _candidate("unit_economics_negative", quote="Each sale lost money.", paragraph=7),
    ])
    assert rule.provenance_attached is True
    assert sorted(p.quote for p in rule.provenance) == [
        "Churn began to climb.", "Each sale lost money.",
    ]


def test_a_sub_rule_whose_consequent_no_candidate_introduced_still_gets_one():
    """The consequent is often an existing knowledge-base predicate.

    Finding one record rather than two is the normal case, not a failure, and
    the rule must still be built — refusing would discard a real rule to
    enforce a record-keeping rule.
    """
    rule = _run_sub_rule_path([
        _candidate("churn_rising", quote="Churn began to climb."),
    ])
    assert [p.quote for p in rule.provenance] == ["Churn began to climb."]
    assert rule.provenance_attached is True


def test_the_same_span_reached_from_both_ends_is_recorded_once():
    """A duplicate is a claim of corroboration nobody made.

    The citation tier counts these records, so listing one span twice would
    make a single piece of evidence look like two — the same error as the
    overlap discount that walked belief upward when one source was restated.
    """
    same_quote = "One sentence, reached twice."
    rule = _run_sub_rule_path([
        _candidate("churn_rising", quote=same_quote, paragraph=2),
        _candidate("churn_rising", quote=same_quote, paragraph=2),
    ])
    assert len(rule.provenance) == 1, (
        f"the same span was recorded {len(rule.provenance)} times"
    )


def test_two_candidates_for_one_predicate_are_both_kept_when_they_differ():
    """Deduping must not collapse genuinely separate places the claim was found."""
    rule = _run_sub_rule_path([
        _candidate("churn_rising", quote="Churn began to climb.", paragraph=2),
        _candidate("churn_rising", quote="Retention fell for two quarters.", paragraph=9),
    ])
    assert len(rule.provenance) == 2


# ── an empty list is not the same as never having looked ──

def test_a_rule_nobody_attached_provenance_to_says_so():
    """The distinction the whole fix rests on.

    Before this, `provenance == []` meant both 'no contributing candidate had
    a record' and 'the construction site never passed one', and every rule
    ever built was the second. A tier computed over those lists measures our
    own plumbing and reports it as the state of the corpus.
    """
    never_looked = ProposedVyapti(id="V99", name="hand-built")
    assert never_looked.provenance == []
    assert never_looked.provenance_attached is False

    assert Vyapti(
        id="V99", name="n", statement="s",
        causal_status="empirical",
        confidence={"existence": 0.5, "formulation": 0.5, "evidence": "observational"},
        epistemic_status="hypothesis",
    ).provenance_attached is False


def test_looked_and_found_nothing_is_distinguishable_from_never_looked():
    """A candidate whose name is not in the vocabulary contributes nothing.

    The rule is still built and still went through the attaching step, so it
    reports an empty list with the flag set — which is a different fact from
    the default object above.
    """
    rule = _run_sub_rule_path(
        [_candidate("some_unrelated_predicate")],
        node_name="churn_rising", parent="unit_economics_negative",
    )
    assert rule.provenance == []
    assert rule.provenance_attached is True, (
        "the attaching step ran and found nothing; that is not 'never looked'"
    )


# ── the second half: the proposal is not the rule ──

def _validate(proposed: ProposedVyapti):
    validator = StageEValidator(KnowledgeStore(domain_type=DomainType.CRAFT))
    result = validator.validate_and_merge(StageDOutput(new_vyaptis=[proposed]))
    ks = result[0] if isinstance(result, tuple) else result
    return ks.vyaptis.get(proposed.id)


def test_provenance_survives_the_proposal_becoming_a_knowledge_base_rule():
    """`Vyapti` is what a citation tier reads, not `ProposedVyapti`.

    Threading provenance onto the proposal alone would have changed nothing
    observable — the record would have died one conversion later instead of
    one earlier, and the tier would still have been computed over [].
    """
    record = Provenance(
        chapter_id="ch02", quote="A span from the chapter.",
        quote_found_in_source=True,
    )
    stored = _validate(ProposedVyapti(
        id="V90",
        name="a rule",
        statement="A span from the chapter.",
        antecedents=["churn_rising"],
        consequent="unit_economics_negative",
        provenance=[record],
        provenance_attached=True,
    ))

    assert stored is not None, "Stage E did not store the rule at all"
    assert stored.provenance_attached is True
    assert [p.quote for p in stored.provenance] == ["A span from the chapter."]
    assert stored.provenance[0].quote_found_in_source is True, (
        "the flag a citation tier needs to reach ATTRIBUTED did not survive"
    )


def test_the_whole_path_from_candidate_to_stored_rule_keeps_the_span():
    """End to end, with no model call: candidate → Stage D → Stage E → KB."""
    candidate = _candidate("cash_burn_accelerating", quote="Burn rate doubled.")
    stage_d_out = _stage_d()(
        stage_a=StageAOutput(candidates=[candidate], chapter_id="ch02"),
        stage_b=StageBOutput(nodes={}),
        stage_c=StageCOutput(vocabulary=["cash_burn_accelerating"]),
        guide_text={},
    )
    stored = _validate(stage_d_out.new_vyaptis[0])

    assert stored is not None
    assert [p.quote for p in stored.provenance] == ["Burn rate doubled."]
    assert stored.provenance[0].chapter_id == "ch02"


def test_provenance_survives_being_written_to_a_knowledge_base_and_read_back():
    """The knowledge base is the durable artifact; a tier reads it later.

    Serialisation is pydantic's, so this holds by construction — which is
    exactly why it is worth pinning. A field that fails to round-trip would
    make every rule look unsourced again on the next load, and that reads as
    a fact about the rules.
    """
    ks = KnowledgeStore(domain_type=DomainType.CRAFT)
    ks.vyaptis["V90"] = Vyapti(
        id="V90", name="a rule", statement="s",
        causal_status="empirical",
        confidence={"existence": 0.5, "formulation": 0.5, "evidence": "observational"},
        epistemic_status="hypothesis",
        provenance=[Provenance(
            chapter_id="ch02", quote="Burn rate doubled.",
            quote_found_in_source=True,
        )],
        provenance_attached=True,
    )

    reloaded = KnowledgeStore(**json.loads(ks.model_dump_json()))
    rule = reloaded.vyaptis["V90"]
    assert rule.provenance_attached is True
    assert [p.quote for p in rule.provenance] == ["Burn rate doubled."]
    assert rule.provenance[0].quote_found_in_source is True


# ── the guarantee, asserted rather than intended ──

def _construction_sites(class_name: str, only_file: str | None = None):
    """Every `X(...)` call in the package, with its keywords."""
    from pathlib import Path

    import anvikshiki_v4

    package = Path(anvikshiki_v4.__file__).parent
    found = []
    paths = sorted(package.glob("*.py"))
    if only_file:
        paths = [p for p in paths if p.name == only_file]
    for path in paths:
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            # Both `X(...)` and `module.X(...)`, so switching to the
            # qualified form does not make this check vacuous.
            name = (
                func.id if isinstance(func, ast.Name)
                else func.attr if isinstance(func, ast.Attribute)
                else None
            )
            if name != class_name:
                continue
            found.append((
                f"{path.name}:{node.lineno}",
                {kw.arg for kw in node.keywords},
                node.keywords,
            ))
    return found


def test_no_path_turns_a_proposal_into_a_rule_without_carrying_provenance():
    """A source-level check, because a third conversion is what would break this.

    Two paths convert a `ProposedVyapti` into a `Vyapti` today — the automatic
    Stage E merge and the human-approval path. Both were dropping provenance.
    If a third appears, the record dies again and nothing at runtime would say
    so: the rule would simply look unsourced, which is indistinguishable from
    a rule that genuinely has no source.

    `kb_augmentation` is correctly excluded by the rule rather than by a name:
    it builds from the model's parametric knowledge, reads from no proposal,
    and has no source document to point at.
    """
    converting, missing = [], []
    for site, kwargs, keywords in _construction_sites("Vyapti"):
        reads_a_proposal = any(
            isinstance(kw.value, ast.Attribute)
            and isinstance(kw.value.value, ast.Name)
            and kw.value.value.id == "proposed"
            for kw in keywords
        )
        if not reads_a_proposal:
            continue
        converting.append(site)
        if not {"provenance", "provenance_attached"} <= kwargs:
            missing.append(site)

    # The denominator. A scan that matched nothing would pass in silence.
    assert len(converting) >= 2, (
        f"the scan found only {len(converting)} proposal-to-rule "
        f"conversion(s) ({converting}) — it has stopped matching how they "
        f"are written"
    )
    assert not missing, (
        f"{len(missing)} conversion(s) drop the candidate's provenance:\n"
        + "\n".join(f"  - {site}" for site in missing)
    )


def test_every_stage_d_construction_records_whether_it_looked():
    """`provenance_attached` is what separates an absence from an omission.

    A new Stage D branch that forgets it would produce rules reading as
    'nobody ever tried', which is the state this whole fix exists to end. The
    count is asserted so the scan cannot pass by matching nothing.
    """
    sites = _construction_sites("ProposedVyapti", only_file="predicate_extraction.py")
    assert len(sites) == 2, (
        f"expected the two Stage D construction sites, found {len(sites)}: "
        f"{[s for s, _, _ in sites]}"
    )
    silent = [site for site, kwargs, _ in sites if "provenance_attached" not in kwargs]
    assert not silent, (
        f"{len(silent)} Stage D construction(s) do not record whether they "
        f"looked for provenance:\n" + "\n".join(f"  - {site}" for site in silent)
    )
