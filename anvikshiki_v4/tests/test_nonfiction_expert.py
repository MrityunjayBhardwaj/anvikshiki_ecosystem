# tests/test_nonfiction_expert.py
"""The third knowledge base, and the first one authored before the engine
that now reads it had the machinery it is being read with.

#21 asked for a third domain so that "the architecture is not single-sample"
stops resting on two points. That is the smaller half of what this base is
for. The larger half:

  business_expert.yaml says in its own header that it carries "notable
  features for engine testing". copywriting_expert.yaml was not shaped for
  the engine, but it was transcribed BEFORE the scope advisories (#89/#92),
  the wired Layer 5 solver, and coverage's inertness demotion (#116) were
  merged. This base is the first the engine meets that none of that work
  could have been tuned against.

So the laws below are deliberately about what the ENGINE does with an
unshaped base, not only about whether the transcription copied ten rules
correctly. Every rule firing is the measure #20 established; the scope,
decay and coverage laws are the ones that could not have been written
before this month.

Two things this base has that neither sibling does, both asserted here so a
later edit cannot quietly drop them:

  * domain_type INTERPRETIVE. Both existing bases are CRAFT, so until now
    every compile has exercised one value. The volume's own Stage 1 audit
    names Type 5 primary; `domain_type` reaches the grounding, extraction
    and augmentation prompts as live context, so this is a real path.

  * REAL decay conditions. The source ships a Decay Marker Registry — seven
    claims with an explicit verification condition each — and six rules carry
    that text verbatim. Both sibling bases have `decay_condition` on almost
    nothing.

And one thing it does NOT have, asserted so its absence stays deliberate:
`last_verified` is unset on every rule, because the source reference bank
says "DRAFT — pending verification pass" (#106). The decay AGE branch still
has nothing anywhere in the shipped set to fire on.
"""

from pathlib import Path

import pytest
import yaml

from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store
from anvikshiki_v4.schema import CausalStatus, DecayRisk, DomainType
from anvikshiki_v4.schema import EpistemicStatus as KBEpistemic
from anvikshiki_v4.advisories import (
    decayed_rule_advisories,
    unestablished_scope_advisories,
)
from anvikshiki_v4.tests.test_advisories_are_carried import _af

KB_PATH = Path(__file__).resolve().parents[1] / "data" / "nonfiction_expert.yaml"


@pytest.fixture
def nf_ks():
    return load_knowledge_store(str(KB_PATH))


@pytest.fixture
def bank():
    return yaml.safe_load(KB_PATH.read_text())["reference_bank"]


def _facts_for(v):
    """Every antecedent and every declared scope condition, as ground terms.

    Supplying the scope conditions too is the point of the fixture: a rule
    fires without them, so a test that omitted them would be quietly
    measuring the advisory path instead of the firing path.
    """
    return [f"{a}(x)" for a in v.antecedents] + \
           [f"{s}(x)" for s in (v.scope_conditions or [])]


# ── The base loads with the shape the author wrote ──

class TestKnowledgeStoreLoading:

    def test_domain_type_is_the_first_non_craft_base(self, nf_ks):
        """The volume's Stage 1 audit says "Primary domain type: TYPE 5 —
        INTERPRETIVE/HUMANISTIC + TYPE 4 — PRACTICAL/CRAFT (hybrid)". Type 5
        is named primary, so INTERPRETIVE is the honest value and not a
        preference. Both sibling bases are CRAFT."""
        assert nf_ks.domain_type == DomainType.INTERPRETIVE

    def test_pramana_count(self, nf_ks):
        assert len(nf_ks.pramanas) == 4

    def test_vyapti_count(self, nf_ks):
        """Ten, matching Step 2A's own heading (V0-1..V0-10). This completes
        the 11 / 9 / 10 pattern across business, copywriting and non-fiction
        that #20 was filed to confirm, so the number is load-bearing."""
        assert len(nf_ks.vyaptis) == 10

    def test_hetvabhasa_count(self, nf_ks):
        """Nine, matching Step 2B (V0F-1..V0F-9)."""
        assert len(nf_ks.hetvabhasas) == 9

    def test_threshold_concepts(self, nf_ks):
        assert len(nf_ks.threshold_concepts) == 3

    def test_chapter_fingerprints(self, nf_ks):
        """Twenty-one: the opening plus Ch 1–20, exactly Step 2G's table."""
        assert len(nf_ks.chapter_fingerprints) == 21

    def test_reference_bank(self, nf_ks):
        assert len(nf_ks.reference_bank) == 30

    def test_the_six_structural_vyaptis(self, nf_ks):
        """The six the author marked STRUCTURAL. The other four collapse onto
        `empirical`, because the schema has no separate value for the
        author's CAUSAL and EMPIRICAL REGULARITY — the same lossy mapping
        copywriting documents."""
        structural = sorted(v.id for v in nf_ks.vyaptis.values()
                            if v.causal_status == CausalStatus.STRUCTURAL)
        assert structural == ["V01", "V02", "V03", "V04", "V07", "V08"]

    def test_epistemic_status_follows_the_authors_rendering_rule(self, nf_ks):
        """Not a sanity check — this is the transcription's most consequential
        judgment call. Each rule carries a "GUIDE RENDERING RULE" saying how
        the claim may be stated, and the status is read off it:

            "State as structural regularity" -> established
            "State as argued position"       -> provisional
            "Calibrated hedge"               -> provisional
            "Working hypothesis"             -> hypothesis

        Marking all ten established would have been the easy transcription and
        would have thrown away the volume's most careful work. V04 and V06 are
        the two the author called working hypotheses about his own framework.
        """
        by = {}
        for v in nf_ks.vyaptis.values():
            by.setdefault(v.epistemic_status, []).append(v.id)
        assert sorted(by[KBEpistemic.ESTABLISHED]) == ["V05", "V07", "V08", "V10"]
        assert sorted(by[KBEpistemic.PROVISIONAL]) == ["V01", "V02", "V03", "V09"]
        assert sorted(by[KBEpistemic.WORKING_HYPOTHESIS]) == ["V04", "V06"]

    def test_no_rule_concludes_the_negation_of_another(self, nf_ks):
        """business_expert.yaml has V11 concluding not_value_creation against
        V01's value_creation. Neither unshaped base has a rebutting pair,
        because neither author wrote one. Two in a row is a datum about how
        humans author these, and manufacturing one here would have destroyed
        it — so this asserts the absence rather than leaving it to chance."""
        consequents = {v.consequent for v in nf_ks.vyaptis.values()}
        negations = {c for c in consequents
                     if c.startswith("not_") and c[4:] in consequents}
        assert negations == set()


# ── What the engine does with it ──

class TestEveryAuthoredRuleFires:

    def test_all_ten_rules_fire(self, nf_ks):
        """#20's measure, applied to a base written after none of this work.
        A rule that cannot fire is a rule the compiler dropped, and it would
        otherwise look exactly like a rule no query happened to reach."""
        silent = []
        for vid, v in sorted(nf_ks.vyaptis.items()):
            af, _ = _af(nf_ks, *_facts_for(v))
            if vid not in {a.top_rule for a in af.arguments.values()}:
                silent.append(vid)
        assert silent == [], f"authored but unfirable: {silent}"

    def test_the_authors_one_chain_derives_at_depth_two(self, nf_ks):
        """V01 ends at a ceiling question and V03 opens "Wherever the Western
        ascending arc generates a ceiling question…". They share the predicate
        because the author wrote them sharing it, and it is the only chain in
        the volume. No second chain was manufactured, so if this breaks the
        base has no multi-step derivation left at all."""
        af, labels = _af(nf_ks, "method_pursued_to_limit(x)",
                         "empirical_discipline(x)", "mapped_convergence(x)")
        by_rule = {a.top_rule: a for a in af.arguments.values() if a.top_rule}
        assert set(by_rule) == {"V01", "V03"}
        assert by_rule["V01"].conclusion == "ceiling_question_generated(x)"
        assert by_rule["V03"].conclusion == "descending_framework_available(x)"


class TestScopeAndDecayOnAnUnshapedBase:

    def test_every_scope_condition_is_inert(self, nf_ks):
        """Ten scope conditions, none of them derivable — no condition is any
        rule's consequent. This is the property `advisories.py` documents for
        the shipped set, and this base raises its denominator from 4 and 5 to
        10. If a future edit makes one derivable, the advisory stops being a
        statement about the query and the docstring there goes stale."""
        consequents = {v.consequent for v in nf_ks.vyaptis.values()}
        scope = {s for v in nf_ks.vyaptis.values()
                 for s in (v.scope_conditions or [])}
        assert len(scope) == 10
        assert scope & consequents == set()

    def test_a_rule_fired_without_its_scope_says_so(self, nf_ks):
        """The #89/#92 channel, against a base that could not have been used
        to tune it. V01 declares `empirical_discipline` and fires without it."""
        af, labels = _af(nf_ks, "method_pursued_to_limit(x)")
        advisories = unestablished_scope_advisories(nf_ks, af, labels)
        assert "V01" in {a.vyapti_id for a in advisories}

    def test_the_six_rules_carrying_the_authors_decay_conditions(self, nf_ks):
        """Transcribed verbatim from the Decay Marker Registry (Step 2I).
        DM-4 names V06 outright; DM-5 is V03's content. This is the first
        shipped base where the never-verified advisory carries the author's
        own verification condition rather than an empty parenthesis."""
        carried = sorted(v.id for v in nf_ks.vyaptis.values()
                         if v.decay_condition)
        assert carried == ["V01", "V02", "V03", "V06", "V09", "V10"]

    def test_the_three_high_risk_rules(self, nf_ks):
        high = sorted(v.id for v in nf_ks.vyaptis.values()
                      if v.decay_risk == DecayRisk.HIGH)
        assert high == ["V01", "V03", "V06"]

    def test_a_decayed_rule_reaches_an_advisory(self, nf_ks):
        """V06 is high risk, never verified, and DM-4 asks for evidence from
        independently constructed inquiry frameworks. Firing it must say so."""
        v06 = nf_ks.vyaptis["V06"]
        af, labels = _af(nf_ks, *_facts_for(v06))
        advisories = decayed_rule_advisories(nf_ks, af, labels)
        assert [a.vyapti_id for a in advisories] == ["V06"]
        assert "independently constructed" in advisories[0].message

    def test_last_verified_is_unset_on_every_rule(self, nf_ks):
        """Deliberate, and the reason is upstream: the source reference bank
        says "Status: DRAFT — pending verification pass" (#106). Setting a
        date would be inventing one.

        The consequence is worth failing on if it ever silently changes: the
        decay AGE branch has no rule in ANY shipped base to fire on, so every
        decay advisory the engine can currently produce is the never-verified
        one. When #106's verification pass lands, this test should fail.
        """
        dated = sorted(v.id for v in nf_ks.vyaptis.values() if v.last_verified)
        assert dated == [], (
            f"{dated} now carry last_verified. If #106's verification pass "
            f"has been done, replace this with a law about the age branch "
            f"rather than deleting it — the age branch has never run."
        )


# ── The reference bank is NOT retrofitted, asserted so it cannot pass for one ──

class TestReferenceBankIsNotYetVerified:
    """Same shape as the copywriting laws, and for the same reason:
    business_expert.yaml's identifier laws hardcode their own KB_PATH, so a
    bank with no identifiers at all would sail past the whole suite in
    silence. #16's retrofit needs something it must come back and change.

    The upstream fact that makes this correct rather than lazy:
    stage3_reference_bank.md carries ZERO DOIs and ZERO ISBNs across all 118
    of its entries. There is nothing to transcribe, and inventing an
    identifier is the exact defect the citation tier exists to catch.
    """

    def test_the_bank_is_not_empty(self, bank):
        assert len(bank) == 30

    def test_every_entry_names_a_title(self, bank):
        missing = [k for k, v in bank.items() if not v.get("title")]
        assert missing == []

    def test_no_entry_carries_an_identifier_yet_out_of_all_of_them(self, bank):
        """The zero with its denominator. When #16's retrofit reaches this
        base the test must fail, and that failure is the point."""
        fields = ("doi", "isbn_13", "work_id", "url", "resolution")
        carried = sorted(k for k, v in bank.items()
                         if any(f in v for f in fields))
        assert carried == [], (
            f"{len(carried)} of {len(bank)} bank entries now carry an "
            f"identifier. If #16's non-fiction retrofit has been done, "
            f"replace this test with the identifier laws in "
            f"test_reference_bank_identifiers.py rather than deleting it."
        )
        assert len(bank) == 30

    def test_classical_texts_carry_no_invented_year(self, bank):
        """Four entries name a work with no meaningful single year — the
        Nyāya Sūtras, the Nyāyabhāṣya, the Sāṃkhyakārikā, the Arthaśāstra,
        and Jayarāśi's Tattvopaplavasiṃha. Omitting `year` is the correct
        absence; supplying one would be fabrication dressed as completeness.
        """
        undated = sorted(k for k, v in bank.items() if "year" not in v)
        assert undated == [
            "src_bisht_anvikshiki",
            "src_gautama_nyayasutras",
            "src_isvarakrsna_samkhyakarika",
            "src_jayarasi_tattvopaplavasimha",
            "src_kautilya_arthasastra",
            "src_vatsyayana_nyayabhasya",
        ]

    def test_every_source_cited_by_a_rule_exists_in_the_bank(self, nf_ks):
        """A rule citing a source the bank does not define is a dangling
        identifier, and it is cheap to forbid whether or not the identifiers
        themselves resolve."""
        cited = {s for v in nf_ks.vyaptis.values() for s in v.sources}
        dangling = sorted(cited - set(nf_ks.reference_bank))
        assert dangling == []

    def test_the_bank_carries_no_entry_no_rule_cites(self, nf_ks):
        """The other direction. A bank entry nothing cites is a reference
        that was transcribed and then connected to nothing — the defect class
        this project keeps meeting, in miniature."""
        cited = {s for v in nf_ks.vyaptis.values() for s in v.sources}
        orphaned = sorted(set(nf_ks.reference_bank) - cited)
        assert orphaned == []
