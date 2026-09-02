# tests/test_reference_bank_identifiers.py
"""Every reference-bank entry states how well its source was located (#16).

The bank was well-formed before this and entirely unverifiable: 29 entries of
title/author/year, zero DOIs, zero ISBNs, zero URLs. The chain resolved in
*shape* — all 25 citations pointed at a real bank entry — while nothing in the
pipeline could confirm any of those works exists.

Three statuses, never two, and the third is the load-bearing one:

    resolved   a locator was fetched and matched on title, author and year
    ambiguous  several candidates are defensible; none was chosen
    not_found  we looked and did not find it

`not_found` is deliberately not `fabricated`. Two failed searches are not proof
of absence, and the citation tier reserves its deleting verdict for a span that
was checked and found missing. Reading "we could not find it" as "the source is
invented" is the same collapse that would have deleted the knowledge base on the
strength of an identifier resolver nobody had written.

None of this changes a rule's status today. All 11 rules tier CURATED, which
returns before provenance is read, so the retrofit buys reader-checkable
citations and a precondition for the resolver — not an observable status change.
Saying so here keeps the next reader from expecting one.
"""

from pathlib import Path

import yaml

# Anchored to this file, not to the working directory. The bare relative path
# reads fine and fails from anywhere but the repo root — 12 of the 13 laws
# below fail that way — which is #61's shape, and there is no reason to add to
# it in a new file when `test_citation_tier.py` already does this correctly.
KB_PATH = Path(__file__).resolve().parents[1] / "data" / "business_expert.yaml"
VALID_STATUSES = {"resolved", "ambiguous", "not_found"}


def _bank():
    return yaml.safe_load(KB_PATH.read_text())["reference_bank"]


def test_the_bank_is_not_empty():
    """Denominator for every law below. An empty bank passes all of them."""
    assert len(_bank()) >= 29


def test_every_entry_records_a_resolution_status():
    bank = _bank()
    missing = [k for k, v in bank.items() if "resolution" not in v]
    assert not missing, f"{len(missing)} of {len(bank)} entries carry no status: {missing}"


def test_every_status_is_one_of_the_three():
    bad = {k: v["resolution"].get("status") for k, v in _bank().items()
           if v["resolution"].get("status") not in VALID_STATUSES}
    assert not bad, bad


def test_every_entry_records_when_it_was_checked():
    """A locator resolves at a moment in time. Without the date, a stale
    identifier is indistinguishable from a fresh one."""
    bad = [k for k, v in _bank().items() if not v["resolution"].get("checked")]
    assert not bad, bad


def test_every_resolved_entry_carries_an_identifier():
    """The whole point. `resolved` with nothing to resolve is the empty
    verification that reads as a passing one."""
    bad = []
    for k, v in _bank().items():
        if v["resolution"]["status"] != "resolved":
            continue
        if not (v.get("work_id") or v.get("doi") or v.get("url")):
            bad.append(k)
    assert not bad, f"resolved but no identifier: {bad}"


def test_a_resolved_entry_without_an_isbn_says_why():
    """Absent because no edition matched the recorded year, never absent
    because nobody looked. Ten of eighteen books have one; the other eight
    must state the reason rather than leave a hole."""
    bad = [k for k, v in _bank().items()
           if v.get("work_id") and not v.get("isbn_13")
           and not v["resolution"].get("isbn_note")]
    assert not bad, f"no ISBN and no reason given: {bad}"


def test_no_entry_is_marked_fabricated():
    """`not_found` must never be written up as fabrication. The tier that
    authorises dropping a rule fires on a span checked and found missing, not
    on a search that came back empty."""
    statuses = {v["resolution"]["status"] for v in _bank().values()}
    assert "fabricated" not in statuses


def test_ambiguous_entries_list_their_candidates_and_choose_none():
    """Recording the ambiguity is the point; resolving it by picking would
    assert something nobody verified."""
    for k, v in _bank().items():
        if v["resolution"]["status"] != "ambiguous":
            continue
        cands = v["resolution"].get("candidates")
        assert cands and len(cands) > 1, f"{k}: ambiguous with {cands}"
        assert not (v.get("work_id") or v.get("doi") or v.get("url")), \
            f"{k}: ambiguous but an identifier was chosen anyway"


def test_not_found_entries_say_what_was_searched():
    """An unlocatable citation is a finding, and a finding with no method
    behind it cannot be re-checked or overturned."""
    for k, v in _bank().items():
        if v["resolution"]["status"] != "not_found":
            continue
        assert v["resolution"].get("via"), f"{k}: no search method recorded"
        assert v["resolution"].get("note"), f"{k}: no note recorded"


def test_every_cited_source_still_resolves_into_the_bank():
    """The property that already held, asserted so this edit cannot break it."""
    doc = yaml.safe_load(KB_PATH.read_text())
    bank, n = doc["reference_bank"], 0
    for vid, v in doc["vyaptis"].items():
        for s in (v.get("sources") or []):
            n += 1
            assert s in bank, f"{vid} cites {s}, which is not in the bank"
    assert n >= 25, f"only {n} citations examined"


def test_identifiers_are_well_formed():
    """A typo'd ISBN and a right one look equally plausible in YAML."""
    for k, v in _bank().items():
        if isbn := v.get("isbn_13"):
            assert isbn.isdigit() and len(isbn) == 13, f"{k}: {isbn}"
        if doi := v.get("doi"):
            assert doi.startswith("10."), f"{k}: {doi}"
        if url := v.get("url"):
            assert url.startswith("https://"), f"{k}: {url}"
        if work := v.get("work_id"):
            assert work.startswith("openlibrary:OL"), f"{k}: {work}"


def test_the_bank_carries_real_identifiers_now():
    """The before/after, asserted. The filed premise was 0 DOIs, 0 ISBNs and
    0 URLs across the whole bank; a regression to that state must fail."""
    bank = _bank()
    ids = sum(1 for v in bank.values()
              if v.get("work_id") or v.get("doi") or v.get("url"))
    assert ids >= 25, f"only {ids} of {len(bank)} entries carry an identifier"


def test_the_citation_tier_is_unchanged_by_this():
    """Reachability, asserted rather than asserted-in-prose. Adding
    identifiers must not silently move a rule's ceiling: every rule is
    hand-authored, tiers CURATED, and is exempt from the citation axis."""
    from anvikshiki_v4.lattice import CitationTier, tier_for_citation
    from anvikshiki_v4.t2_compiler_v4 import load_knowledge_store

    ks = load_knowledge_store(str(KB_PATH))
    tiers = {vid: tier_for_citation(v) for vid, v in ks.vyaptis.items()}
    assert len(tiers) == 11, f"expected 11 rules, examined {len(tiers)}"
    assert set(tiers.values()) == {CitationTier.CURATED}, tiers
