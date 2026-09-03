# tests/test_copywriting_expert.py
"""
Integration tests for the Copywriting knowledge base (#20).

The point of this KB is generality: business_expert.yaml says in its own
header that it carries "notable features for engine testing" — a rebutting
conflict, scope exclusions placed to produce undercutting attacks. It was
shaped, in part, for the engine that reads it. copywriting_expert.yaml was
transcribed from stage-2/stage-3 material hand-authored on 27 Feb 2026 for a
human reader, with no engine in mind. So what the engine does here is
evidence about the engine.

Every assertion below was first run as a probe against business_expert.yaml,
whose values are already known from test_business_expert.py. A probe that
cannot reproduce the known numbers is measuring itself, and the first version
of this one could not: it expected 12 chapter fingerprints where the business
KB has 10, and it called precompile_kb with no facts and read the resulting
zero arguments as a result rather than as an artefact of the call. Both were
caught by the control, not by the subject.
"""

from pathlib import Path

import pytest
import yaml

from anvikshiki_v4.t2_compiler_v4 import compile_t2, load_knowledge_store
from anvikshiki_v4.schema import CausalStatus, DomainType
from anvikshiki_v4.schema import EpistemicStatus as KBEpistemic
from anvikshiki_v4.schema_v4 import PramanaType

KB_PATH = Path(__file__).resolve().parents[1] / "data" / "copywriting_expert.yaml"


# ── Fixtures ──

@pytest.fixture
def copy_ks():
    return load_knowledge_store(str(KB_PATH))


@pytest.fixture
def full_facts():
    """One fact per antecedent that is not itself produced by another rule.

    Supplying all of them is deliberate: the question is whether every
    authored rule can fire at all, not whether a realistic query fires a
    realistic subset.
    """
    return [
        {"predicate": p, "confidence": 0.85} for p in [
            "attention_captured", "specific_claim", "problem_first_sequence",
            "awareness_level_matched", "distinctive_voice", "voice_consistency",
            "specific_verifiable_proof", "friction_reduced",
            "expert_editing_applied", "ai_drafting_used",
        ]
    ]


@pytest.fixture
def chain_facts():
    """Only what the two chains need, so a depth-2 argument proves the chain
    rather than being reachable by a shorter route."""
    return [
        {"predicate": "attention_captured", "confidence": 0.9},
        {"predicate": "problem_first_sequence", "confidence": 0.9},
        {"predicate": "awareness_level_matched", "confidence": 0.9},
        {"predicate": "expert_editing_applied", "confidence": 0.9},
    ]


# ── The KB loads and has the authored shape ──

class TestKnowledgeStoreLoading:

    def test_domain_type(self, copy_ks):
        assert copy_ks.domain_type == DomainType.CRAFT

    def test_pramana_count(self, copy_ks):
        assert len(copy_ks.pramanas) == 4

    def test_vyapti_count(self, copy_ks):
        """Nine, matching STEP 2A's own heading. The 11/9/10 pattern across
        business, copywriting and non-fiction is the datum #20 was filed to
        confirm, so this number is load-bearing and not a sanity check."""
        assert len(copy_ks.vyaptis) == 9

    def test_hetvabhasa_count(self, copy_ks):
        assert len(copy_ks.hetvabhasas) == 7

    def test_threshold_concepts(self, copy_ks):
        assert len(copy_ks.threshold_concepts) == 3

    def test_chapter_fingerprints(self, copy_ks):
        assert len(copy_ks.chapter_fingerprints) == 20

    def test_reference_bank(self, copy_ks):
        assert len(copy_ks.reference_bank) == 25

    def test_the_two_structural_vyaptis(self, copy_ks):
        """V04 and V09 are the two the author classified STRUCTURAL. The rest
        collapse onto `empirical`, because the schema has no separate value
        for the author's CAUSAL and EMPIRICAL REGULARITY."""
        structural = sorted(v.id for v in copy_ks.vyaptis.values()
                            if v.causal_status == CausalStatus.STRUCTURAL)
        assert structural == ["V04", "V09"]

    def test_the_three_vyaptis_the_author_marked_down(self, copy_ks):
        """V05, V08 and V09 are the three STEP 3B calls PARTIALLY SOURCED. The
        causal_status mapping is lossy, so the author's reservation survives
        only here — if this drifts, the KB has silently promoted a claim its
        source material declines to make."""
        assert copy_ks.vyaptis["V05"].epistemic_status == KBEpistemic.WORKING_HYPOTHESIS
        assert copy_ks.vyaptis["V08"].epistemic_status == KBEpistemic.WORKING_HYPOTHESIS
        assert copy_ks.vyaptis["V09"].epistemic_status == KBEpistemic.ACTIVELY_CONTESTED

    def test_the_decay_marker_survived_transcription(self, copy_ks):
        """DECAY MARKER 1 in STEP 2I is the only one attached to a vyapti."""
        v9 = copy_ks.vyaptis["V09"]
        assert v9.decay_risk.value == "high"
        assert v9.decay_condition
        assert "annually" in v9.decay_condition


# ── The engine compiles it ──

class TestCompilation:

    def test_premise_arguments_created(self, copy_ks, full_facts):
        af = compile_t2(copy_ks, full_facts)
        premises = [a for a in af.arguments.values()
                    if a.top_rule is None and not a.conclusion.startswith("_")]
        assert len(premises) == 10

    def test_premise_tags_are_pratyaksa(self, copy_ks, full_facts):
        af = compile_t2(copy_ks, full_facts)
        for a in af.arguments.values():
            if a.top_rule is None and not a.conclusion.startswith("_"):
                assert a.tag.pramana_type == PramanaType.PRATYAKSA

    def test_every_authored_rule_can_fire(self, copy_ks, full_facts):
        """All nine, on a KB the engine has never seen and that was written
        without knowledge of it. This is the generality claim in #20, stated
        as a law rather than as a sentence in a PR body."""
        af = compile_t2(copy_ks, full_facts)
        fired = sorted({a.top_rule for a in af.arguments.values() if a.top_rule})
        assert fired == ["V01", "V02", "V03", "V04", "V05", "V06", "V07", "V08", "V09"]
        assert len(fired) == len(copy_ks.vyaptis)

    def test_fixpoint_convergence(self, copy_ks, full_facts):
        af = compile_t2(copy_ks, full_facts)
        assert len(af.arguments) < 100


# ── Chains ──

class TestChainDerivation:
    """The two chains are the author's own words, not a graph decoration.

    V01 -> V03: "Attention is the non-negotiable prerequisite; everything else
              is conditional on it."
    V04 -> V08: "editing can't fix strategic errors — polishing copy aimed at
              the wrong awareness level is wasted effort."
    """

    def test_attention_chain_v1_to_v3(self, copy_ks, chain_facts):
        af = compile_t2(copy_ks, chain_facts)
        derived = [a for a in af.arguments.values()
                   if a.top_rule == "V03" and a.conclusion == "reader_receptive"]
        assert derived, "V03 did not fire"
        assert any(a.tag.derivation_depth >= 2 for a in derived)

    def test_strategy_chain_v4_to_v8(self, copy_ks, chain_facts):
        af = compile_t2(copy_ks, chain_facts)
        derived = [a for a in af.arguments.values()
                   if a.top_rule == "V08" and a.conclusion == "copy_effective"]
        assert derived, "V08 did not fire"
        assert any(a.tag.derivation_depth >= 2 for a in derived)

    def test_v3_does_not_fire_without_attention(self, copy_ks):
        """Remove the chain's root and the chain must not complete. Without
        this, a V03 that fired for some unrelated reason would still pass the
        chain test above."""
        af = compile_t2(copy_ks, [
            {"predicate": "problem_first_sequence", "confidence": 0.9},
        ])
        assert not [a for a in af.arguments.values() if a.top_rule == "V03"]

    def test_v8_does_not_fire_without_strategic_fit(self, copy_ks):
        af = compile_t2(copy_ks, [
            {"predicate": "expert_editing_applied", "confidence": 0.9},
        ])
        assert not [a for a in af.arguments.values() if a.top_rule == "V08"]

    def test_two_independent_routes_to_credibility(self, copy_ks, full_facts):
        """V02 (specificity) and V06 (proof) both conclude perceived_credibility
        from different antecedents — the shape business_expert.yaml has at
        long_term_value, arrived at here without being planned for."""
        af = compile_t2(copy_ks, full_facts)
        routes = sorted({a.top_rule for a in af.arguments.values()
                         if a.conclusion == "perceived_credibility" and a.top_rule})
        assert routes == ["V02", "V06"]


# ── Attacks: what is here, and what is not ──

class TestAttacks:

    def test_scope_exclusions_undercut(self, copy_ks):
        """Every vyapti carries scope exclusions, because the author wrote a
        "Scope conditions" paragraph for each one saying where it relaxes and
        where it breaks. Those become undercutting attacks unchanged."""
        af = compile_t2(copy_ks, [
            {"predicate": "attention_captured", "confidence": 0.9},
            {"predicate": "captive_audience", "confidence": 0.9},
            {"predicate": "specific_claim", "confidence": 0.9},
            {"predicate": "quick_processing_context", "confidence": 0.9},
        ])
        undercuts = [a for a in af.attacks if a.attack_type == "undercutting"]
        assert len(undercuts) == 2
        targeted = sorted(af.arguments[a.target].top_rule for a in undercuts)
        assert targeted == ["V01", "V02"]
        assert all(a.hetvabhasa == "savyabhicara" for a in undercuts)

    def test_there_are_no_rebutting_attacks_and_here_is_the_denominator(
            self, copy_ks, full_facts):
        """The absence is the finding, so it is asserted with what was examined.

        business_expert.yaml has V11 concluding not_value_creation against
        V01's value_creation, and says so in its header — it was authored
        that way. Nothing among these nine concludes the negation of another,
        because the author never wrote a conflicting pair. Inventing a tenth
        vyapti to supply one would have destroyed the measurement and
        corrupted the 11/9/10 count.

        A bare `== 0` here would read as "the engine found no conflicts",
        which is a claim about the domain. With the denominator beside it, it
        reads as what it is: nine rules were examined, none of them negates
        another, so there is nothing for a rebuttal to be made of.
        """
        af = compile_t2(copy_ks, full_facts)
        rebuttals = [a for a in af.attacks if a.attack_type == "rebutting"]

        consequents = {v.consequent for v in copy_ks.vyaptis.values()}
        assert len(copy_ks.vyaptis) == 9, "denominator moved; re-read this test"
        contradictory = {c for c in consequents
                         if f"not_{c}" in consequents or c.removeprefix("not_") != c}
        assert contradictory == set(), (
            f"a negated consequent now exists ({contradictory}); this KB can "
            f"produce rebuttals and this test is no longer describing it"
        )
        assert rebuttals == [], (
            f"{len(rebuttals)} rebutting attacks appeared among "
            f"{len(copy_ks.vyaptis)} vyaptis whose consequents are pairwise "
            f"non-contradictory — the compiler is producing an attack the KB "
            f"has no basis for"
        )


# ── The reference bank is NOT retrofitted, asserted so it cannot pass for one ──

class TestReferenceBankIsNotYetVerified:
    """#16's copywriting retrofit has not been done. business_expert.yaml's
    identifier laws hardcode their own KB_PATH, so they are silently
    inapplicable here — a bank with no identifiers at all would sail past the
    entire suite without a word. These laws exist so that it cannot, and so
    the retrofit has something it must come back and change.
    """

    @pytest.fixture
    def bank(self):
        return yaml.safe_load(KB_PATH.read_text())["reference_bank"]

    def test_the_bank_is_not_empty(self, bank):
        assert len(bank) == 25

    def test_every_entry_names_a_title(self, bank):
        missing = [k for k, v in bank.items() if not v.get("title")]
        assert missing == []

    def test_no_entry_carries_an_identifier_yet_out_of_all_of_them(self, bank):
        """The zero with its denominator. When #16's retrofit lands this test
        must fail, and that failure is the point: it is the only thing in the
        suite that will notice the retrofit was never done."""
        fields = ("doi", "isbn_13", "work_id", "url", "resolution")
        carried = sorted(k for k, v in bank.items()
                         if any(f in v for f in fields))
        assert carried == [], (
            f"{len(carried)} of {len(bank)} bank entries now carry an "
            f"identifier. If #16's copywriting retrofit has been done, "
            f"replace this test with the identifier laws in "
            f"test_reference_bank_identifiers.py rather than deleting it."
        )
        assert len(bank) == 25

    def test_every_source_cited_by_a_rule_exists_in_the_bank(self, copy_ks):
        """The one bank property that does hold today. A rule citing a source
        the bank does not define is a dangling identifier, and it is cheap to
        forbid whether or not the identifiers themselves resolve."""
        bank = copy_ks.reference_bank
        cited = {s for v in copy_ks.vyaptis.values() for s in v.sources}
        assert cited, "no rule cites any source"
        dangling = sorted(cited - set(bank))
        assert dangling == []


# ── The citation tier is unchanged by this, same as #104 ──

def test_every_rule_tiers_curated(copy_ks):
    """All nine are hand-authored, so augmentation_metadata is None and the
    citation tier returns before provenance is read. Adding a KB changes no
    rule's tier — asserted rather than claimed, because a PR body cannot fail.
    """
    for v in copy_ks.vyaptis.values():
        assert v.augmentation_metadata is None
        assert v.provenance == []
        assert v.provenance_attached is False
