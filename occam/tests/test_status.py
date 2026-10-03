"""Stage 6: status from both extensions, weakest link binding (#142, #148)."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from occam.argue import Argument
from occam.attack import FALLACY_OF_TYPE, Attack
from occam.snapshot import SnapshotStore, capture
from occam.solve import Label
from occam.spans import MIN_DISCRIMINATING_LENGTH, is_discriminating, locate
from occam.status import MIN_HOSTS, TOP, derive
from occam.types import STATUS_ORDER, Pramana, Status

NOW = datetime(2026, 9, 28, tzinfo=timezone.utc)
TEXT = ("Customer lifetime value must exceed acquisition cost for viability. "
        "Rapid growth amplifies whatever unit economics already exist. "
        "LTV : CAC ≥ 3:1 is the usual benchmark. "
        "Some argue scale alone eventually fixes margins for every business.")


def world(fetched=NOW):
    store = SnapshotStore()
    snap = store.put(capture(url="https://e.com/a", body=b"a", text=TEXT, fetched_at=fetched))
    return store, snap


TEXT2 = TEXT + " A second page says the same, in its own document."


def second(store, url="https://f.org/b", body=b"b", fetched=NOW, text=TEXT2):
    """Another document saying the same things — a second host by default."""
    return store.put(capture(url=url, body=body, text=text, fetched_at=fetched))


def q(aid, snap, words):
    loc = locate(snap, words)
    assert loc.span is not None
    # The conclusion is the quoted words themselves, so provenance alone
    # decides the ceiling; restatement has its own laws below (#158).
    return Argument(id=aid, conclusion=words, kind="quote", span=loc.span,
                    pramana=Pramana.SABDA, sample_ids=(0,), support="supports")


def step(aid, *subs, kind="inference"):
    return Argument(id=aid, conclusion=aid, kind=kind, sub_arguments=subs,
                    pramana={"inference": Pramana.ANUMANA, "analogy": Pramana.UPAMANA}[kind],
                    sample_ids=(0,))


def atk(a, t, ty="rebutting"):
    return Attack(attacker=a, target=t, type=ty, fallacy=FALLACY_OF_TYPE[ty])


LONG1 = "Customer lifetime value must exceed acquisition cost for viability."
LONG2 = "Rapid growth amplifies whatever unit economics already exist."
LONG3 = "Some argue scale alone eventually fixes margins for every business."
SHORT = "LTV : CAC ≥ 3:1"


# ── ceilings ────────────────────────────────────────────────

def test_a_fresh_discriminating_quote_is_established_bound_by_the_top():
    store, s = world()
    r = derive([q("Q", s, LONG1), q("R", second(store), LONG1)], [], store, as_of=NOW)
    st = r.statuses["Q"]
    assert st.status == Status.ESTABLISHED and st.status_bound_by == (TOP,)


def test_an_inference_over_established_quotes_is_a_hypothesis():
    store, s = world()
    r = derive([q("Q", s, LONG1), step("I", "Q")], [], store, as_of=NOW)
    assert r.statuses["I"].status == Status.HYPOTHESIS
    assert r.statuses["I"].status_bound_by == ("inference step I",)


def test_a_short_quote_caps_at_provisional_and_is_not_dropped():
    """#148, from real data: the ch02 run's 'LTV : CAC ≥ 3:1' was found
    verbatim and is 15 characters. Found is honest; it discriminates nothing."""
    store, s = world()
    assert not is_discriminating(SHORT) and len(SHORT) < MIN_DISCRIMINATING_LENGTH
    r = derive([q("S", s, SHORT)], [], store, as_of=NOW)
    assert r.statuses["S"].status == Status.PROVISIONAL
    assert "too short" in r.statuses["S"].status_bound_by[0]


def test_the_floor_matches_the_engine():
    from anvikshiki_v4 import span_verification as sv
    assert MIN_DISCRIMINATING_LENGTH == sv.MIN_DISCRIMINATING_LENGTH
    for quote in [SHORT, LONG1, "economics.", "x" * 23, "x" * 24, "  a  " * 6]:
        assert is_discriminating(quote) == sv.is_discriminating(quote), quote


def test_a_stale_snapshot_caps_at_hypothesis():
    store, s = world(fetched=NOW - timedelta(days=400))
    r = derive([q("Q", s, LONG1)], [], store, as_of=NOW)
    assert r.statuses["Q"].status == Status.HYPOTHESIS
    assert "stale" in r.statuses["Q"].status_bound_by[0]


def test_a_missing_snapshot_is_never_read_as_fresh():
    _, s = world()
    r = derive([q("Q", s, LONG1)], [], SnapshotStore(), as_of=NOW)
    assert r.statuses["Q"].status == Status.HYPOTHESIS
    assert "freshness unknown" in r.statuses["Q"].status_bound_by[0]


# ── the weakest link ───────────────────────────────────────

def test_one_weak_leaf_lowers_the_root():
    store, s = world()
    strong = derive([q("A", s, LONG1), q("B", s, LONG2), step("I", "A", "B")], [], store, as_of=NOW)
    weak = derive([q("A", s, LONG1), q("B", s, SHORT), step("I", "A", "B")], [], store, as_of=NOW)
    assert strong.statuses["I"].status == Status.HYPOTHESIS
    assert weak.statuses["I"].status == Status.PROVISIONAL
    assert "quote B too short to discriminate" in weak.statuses["I"].status_bound_by


def test_an_analogy_anywhere_in_the_chain_caps_the_chain():
    store, s = world()
    r = derive([q("A", s, LONG1), step("N", "A", kind="analogy"), step("I", "N")],
               [], store, as_of=NOW)
    assert r.statuses["I"].status == Status.PROVISIONAL


def test_a_tie_names_every_constraint_at_the_minimum():
    store, s = world()
    r = derive([q("S", s, SHORT), q("A", s, LONG1), step("N", "A", kind="analogy"),
                step("I", "S", "N")], [], store, as_of=NOW)
    bound = r.statuses["I"].status_bound_by
    assert r.statuses["I"].status == Status.PROVISIONAL
    assert isinstance(bound, tuple) and len(bound) >= 2
    assert "quote S too short to discriminate" in bound and "analogy step N" in bound


# ── labels ─────────────────────────────────────────────────

def test_mutual_defeat_is_contested_not_open():
    store, s = world()
    r = derive([q("A", s, LONG1), q("B", s, LONG3)], [atk("A", "B"), atk("B", "A")],
               store, as_of=NOW)
    for aid in "AB":
        assert r.statuses[aid].label == Label.UNDECIDED
        assert r.statuses[aid].status == Status.CONTESTED


def test_an_odd_cycle_is_open_not_contested():
    store, s = world()
    r = derive([q("A", s, LONG1), q("B", s, LONG2), q("C", s, LONG3)],
               [atk("A", "B"), atk("B", "C"), atk("C", "A")], store, as_of=NOW)
    assert {r.statuses[a].status for a in "ABC"} == {Status.OPEN}


def test_open_and_contested_are_distinguishable_in_output():
    assert Status.OPEN != Status.CONTESTED
    assert Status.OPEN.value != Status.CONTESTED.value


def test_a_defeated_argument_is_rejected_and_so_is_what_rests_on_it():
    store, s = world()
    # Equal pramāṇa, so strength decides: B (established) defeats A
    # (provisional, short quote), and A's attack on B fails.
    r = derive([q("A", s, SHORT), step("I", "A"), q("B", s, LONG3),
                q("B2", second(store), LONG3)],
               [atk("B", "A"), atk("A", "B")], store, as_of=NOW)
    assert r.statuses["A"].rejected and r.statuses["I"].rejected
    assert r.statuses["B"].status == Status.ESTABLISHED


def test_strength_breaks_pramana_ties_through_the_ceiling():
    """Equal pramāṇa: the stronger ceiling defeats the weaker, not vice versa."""
    store, s = world(fetched=NOW)
    r = derive([q("A", s, LONG1), q("B", s, SHORT)], [atk("A", "B"), atk("B", "A")],
               store, as_of=NOW)
    assert r.statuses["A"].label == Label.IN and r.statuses["B"].label == Label.OUT


# ── status cannot be supplied ──────────────────────────────

def test_a_caller_cannot_set_a_status_on_an_argument():
    _, s = world()
    base = q("Q", s, LONG1).model_dump()
    with pytest.raises(ValidationError):
        Argument(**base, status="established")


def test_derive_requires_an_explicit_as_of():
    store, s = world()
    with pytest.raises(TypeError):
        derive([q("Q", s, LONG1)], [], store)          # no clock default


def test_status_order_matches_the_engine():
    from anvikshiki_v4.lattice import STATUS_ORDER as E
    assert [s.value for s in STATUS_ORDER] == [s.value for s in E]


def test_labels_already_respect_the_weakest_link_so_status_needs_no_second_pass():
    """Why status.py has one weakest-link pass, not two: lifting makes the
    semantics order parent and sub-argument by itself. Over random trees —
    parent IN ⇒ subs IN; a sub OUT ⇒ parent OUT; parent credulous ⇒ subs
    credulous."""
    import random
    from occam.solve import solve_graph
    from occam.types import Pramana as P
    rng = random.Random(142)
    checked = 0
    for _ in range(400):
        n = rng.randint(3, 9)
        ids = [f"A{i}" for i in range(n)]
        subs = {i: () for i in ids}
        for j, i in enumerate(ids[1:], 1):
            if rng.random() < 0.5:
                subs[i] = tuple(rng.sample(ids[:j], rng.randint(1, min(2, j))))
        attacks = [atk(*rng.sample(ids, 2), rng.choice(list(FALLACY_OF_TYPE)))
                   for _ in range(rng.randint(1, 2 * n))]
        r = solve_graph(subs, attacks, pramana={i: P(rng.randint(1, 4)) for i in ids},
                        strength={i: rng.randint(0, 4) for i in ids})
        g, cred = r.grounded, r.credulous
        for parent, ss in subs.items():
            for sub in ss:
                checked += 1
                if g[parent] == Label.IN:
                    assert g[sub] == Label.IN
                if g[sub] == Label.OUT:
                    assert g[parent] == Label.OUT
                if parent in cred:
                    assert sub in cred
    assert checked > 500



def test_a_quote_whose_conclusion_restates_it_caps_at_hypothesis():
    """#158, from run 1: all seven `established` answers were paraphrases
    riding on a verified quote."""
    store, s = world()
    loc = locate(s, LONG1)
    para = Argument(id="P", conclusion="Viability needs LTV above CAC.", kind="quote",
                    span=loc.span, pramana=Pramana.SABDA, sample_ids=(0,), support="supports")
    r = derive([para], [], store, as_of=NOW)
    assert r.statuses["P"].status == Status.HYPOTHESIS
    # One host ties with the restatement, so both are named (#202).
    assert r.statuses["P"].status_bound_by == ("quote P restated in the model's words",
                                               "rests on a single source (e.com)")


def test_a_conclusion_inside_the_quote_is_established_full_stop_and_emphasis_aside():
    from occam.spans import states
    assert states("the words **LTV exceeds CAC** here", "LTV exceeds CAC.")
    assert states(LONG1, "Customer lifetime value must exceed acquisition cost")
    assert not states(LONG1, "customer lifetime value must exceed acquisition cost")  # case kept
    assert not states(LONG1, "Lifetime value must beat acquisition cost")
    assert not states(LONG1, ".")



def test_a_quote_never_judged_for_support_cannot_be_established():
    """Not checked is not checked-and-fine (#146)."""
    store, s = world()
    a = q("Q", s, LONG1).model_copy(update={"support": None})
    r = derive([a], [], store, as_of=NOW)
    assert r.statuses["Q"].status == Status.HYPOTHESIS
    assert r.statuses["Q"].status_bound_by == ("quote Q: support not judged",
                                               "rests on a single source (e.com)")


def test_a_quote_whose_support_could_not_be_told_caps_at_provisional():
    store, s = world()
    a = q("Q", s, LONG1).model_copy(update={"support": "cannot_tell"})
    r = derive([a], [], store, as_of=NOW)
    assert r.statuses["Q"].status == Status.PROVISIONAL


# ── corroboration (#162) ───────────────────────────────────

def test_one_source_caps_at_hypothesis_and_names_the_host():
    """The adversarial control: one page, every check passed, still a lie."""
    store, s = world()
    r = derive([q("Q", s, LONG1)], [], store, as_of=NOW)
    st = r.statuses["Q"]
    assert st.status == Status.HYPOTHESIS
    assert st.status_bound_by == ("rests on a single source (e.com)",)
    assert st.ceiling == Status.ESTABLISHED      # provenance unchanged; strength unchanged


def test_two_hosts_saying_the_same_thing_are_both_established():
    store, s = world()
    r = derive([q("Q", s, LONG1), q("R", second(store), LONG1)], [], store, as_of=NOW)
    assert MIN_HOSTS == 2
    assert {r.statuses[i].status for i in "QR"} == {Status.ESTABLISHED}


def test_two_pages_on_one_host_do_not_corroborate():
    """Hosts, not snapshots: a site cannot vouch for itself."""
    store, s = world()
    other = second(store, url="https://e.com/other")
    assert other.id != s.id
    r = derive([q("Q", s, LONG1), q("R", other, LONG1)], [], store, as_of=NOW)
    assert r.statuses["Q"].status == Status.HYPOTHESIS
    assert r.statuses["Q"].status_bound_by == ("rests on a single source (e.com)",)


def test_www_is_the_same_host():
    store, s = world()
    r = derive([q("Q", s, LONG1), q("R", second(store, url="https://www.e.com/x"), LONG1)],
               [], store, as_of=NOW)
    assert r.statuses["Q"].status == Status.HYPOTHESIS


def test_a_different_conclusion_is_not_corroboration():
    store, s = world()
    # Q has two documents but one host; R, on another host, says something else.
    # Its host must not be lent to Q.
    same_site = second(store, url="https://e.com/other", body=b"c")
    r = derive([q("Q", s, LONG1), q("Q2", same_site, LONG1), q("R", second(store), LONG2)],
               [], store, as_of=NOW)
    assert r.statuses["Q"].status == Status.HYPOTHESIS
    assert r.statuses["R"].status == Status.HYPOTHESIS


def test_a_defeated_source_does_not_vouch_for_a_surviving_one():
    store, s = world()
    f = second(store)
    # R (f.org) is attacked by an unattacked quote and cannot answer back.
    r = derive([q("Q", s, LONG1), q("R", f, LONG1), q("K", s, LONG3)],
               [atk("K", "R")], store, as_of=NOW)
    assert r.statuses["R"].rejected
    assert r.statuses["Q"].status == Status.HYPOTHESIS


def test_a_weaker_argument_on_another_host_does_not_lift_one_to_the_top():
    store, s = world()
    unjudged = q("R", second(store), LONG1).model_copy(update={"support": None})
    r = derive([q("Q", s, LONG1), unjudged], [], store, as_of=NOW)
    assert r.statuses["R"].status == Status.HYPOTHESIS
    assert r.statuses["Q"].status == Status.HYPOTHESIS
    assert r.statuses["Q"].status_bound_by == ("rests on a single source (e.com)",)


def test_an_undecided_source_does_not_corroborate():
    store, s = world()
    f = second(store)
    # R and K defeat each other: R is undecided in grounded, so not IN.
    r = derive([q("Q", s, LONG1), q("R", f, LONG1), q("K", f, LONG3)],
               [atk("K", "R"), atk("R", "K")], store, as_of=NOW)
    assert r.statuses["R"].status == Status.CONTESTED
    assert r.statuses["Q"].status == Status.HYPOTHESIS


def test_one_document_fetched_from_a_mirror_does_not_corroborate_itself():
    """#165: identical bytes from two hosts merge into one snapshot with both
    URLs. Two hosts, one document, one argument — still one source."""
    store, s = world()
    m = second(store, url="https://mirror.net/a", body=b"a", text=TEXT)
    assert m.id == s.id and len(m.urls) == 2
    r = derive([q("Q", m, LONG1)], [], store, as_of=NOW)
    assert r.statuses["Q"].status == Status.HYPOTHESIS
    assert r.statuses["Q"].status_bound_by == ("rests on a single source (e.com, mirror.net)",)


def test_the_same_text_in_different_bytes_on_another_host_does_not_corroborate():
    store, s = world()
    r = derive([q("Q", s, LONG1), q("R", second(store, text=TEXT), LONG1)], [], store,
               as_of=NOW)
    assert r.statuses["Q"].status == Status.HYPOTHESIS


# ── the question's premise (#179) ──────────────────────────

def test_a_conclusion_carrying_an_unquoted_question_number_is_never_established():
    """Why #179 counts and does not cap. A number from the question that no
    quote beneath a conclusion states is the model's addition, and the
    ceilings already hold it below `established`: a quote's conclusion that
    adds it is not literally in the quote, and every inference is the model's
    step. Over random trees, on two hosts so corroboration cannot be what
    holds it down — and `established` must occur, or the law saw nothing."""
    import random
    from occam.argue import unquoted_question_numbers
    question = "Why did the seals fail in 1986?"
    dated = "The seals failed in the cold of January 1986 at launch."
    plain = "Cold had stiffened the rubber seals before the launch."
    text = f"{dated} {plain}"
    store = SnapshotStore()
    snaps = [store.put(capture(url="https://e.com/a", body=b"a", text=text, fetched_at=NOW)),
             store.put(capture(url="https://f.org/b", body=b"b", text=text + " Again.",
                               fetched_at=NOW))]
    rng = random.Random(179)
    flagged = established = 0
    for _ in range(300):
        args: list[Argument] = []
        for i in range(rng.randint(3, 8)):
            aid = f"A{i}"
            if not args or rng.random() < 0.4:
                words = rng.choice([dated, plain])
                concl = rng.choice([words, words.rstrip(".") + " in 1986."])
                args.append(q(aid, rng.choice(snaps), words).model_copy(
                    update={"id": aid, "conclusion": concl}))
            else:
                subs = tuple(a.id for a in rng.sample(args, rng.randint(1, min(2, len(args)))))
                s = step(aid, *subs, kind=rng.choice(["inference", "inference", "analogy"]))
                args.append(s.model_copy(update={"conclusion": rng.choice(
                    ["The seals failed.", "The seals failed in 1986."])}))
        r = derive(args, [], store, as_of=NOW)
        by = {a.id: a for a in args}
        for a in args:
            st = r.statuses[a.id].status
            established += st == Status.ESTABLISHED
            if unquoted_question_numbers(question, a.id, by):
                flagged += 1
                assert st != Status.ESTABLISHED, (a, r.statuses[a.id])
    assert flagged > 200 and established > 50, (flagged, established)


# ── a single source tied with a ceiling (#202) ─────────────

def restated(aid, snap, words=LONG1, conclusion="Viability needs LTV above CAC."):
    loc = locate(snap, words)
    return Argument(id=aid, conclusion=conclusion, kind="quote", span=loc.span,
                    pramana=Pramana.SABDA, sample_ids=(0,), support="supports")


def test_a_restated_quote_on_one_host_names_the_single_source_too():
    """Lifting the restatement alone would leave it at hypothesis, so the
    bound list must say so. Under bound_ties 1 it names what it always did."""
    store, s = world()
    new = derive([restated("P", s)], [], store, as_of=NOW).statuses["P"]
    old = derive([restated("P", s)], [], store, as_of=NOW, bound_ties=1).statuses["P"]
    assert new.status == old.status == Status.HYPOTHESIS
    assert new.status_bound_by == ("quote P restated in the model's words",
                                   "rests on a single source (e.com)")
    assert old.status_bound_by == ("quote P restated in the model's words",)


def test_a_restated_quote_backed_by_a_second_host_names_only_the_restatement():
    """Another host whose quote states the same conclusion verbatim is
    corroboration, so the only tie is the restatement."""
    store, s = world()
    s2 = second(store)
    conclusion = "Viability needs LTV above CAC."
    backer = Argument(id="B", conclusion=conclusion, kind="quote",
                      span=locate(s2, LONG1).span, pramana=Pramana.SABDA,
                      sample_ids=(0,), support="supports")
    # B verifies but restates too, so nothing corroborates: the control case.
    r = derive([restated("P", s), backer], [], store, as_of=NOW)
    assert "rests on a single source" in " ".join(r.statuses["P"].status_bound_by)
    # Now B's conclusion is its own quote, so its ceiling is established and
    # it counts for P's group once P's conclusion is the same words.
    b2 = q("B", s2, LONG1)
    p2 = restated("P", s, conclusion=LONG1).model_copy(
        update={"span": locate(s, LONG1).span})
    r2 = derive([p2.model_copy(update={"support": None}), b2], [], store, as_of=NOW)
    assert r2.statuses["P"].status_bound_by == ("quote P: support not judged",)


def test_only_a_quote_at_hypothesis_gains_the_bound():
    """An inference is capped by its own step and can never be established,
    and a provisional quote is below the single-source cap: for neither is it
    a tie."""
    store, s = world()
    p = restated("P", s)
    inf = Argument(id="I", conclusion="So the business is viable.", kind="inference",
                   sub_arguments=("P",), pramana=Pramana.ANUMANA, sample_ids=(0,))
    prov = q("V", s, LONG1).model_copy(update={"support": "cannot_tell"})
    r = derive([p, inf, prov], [], store, as_of=NOW)
    assert not any("single source" in b for b in r.statuses["I"].status_bound_by)
    assert r.statuses["V"].status == Status.PROVISIONAL
    assert not any("single source" in b for b in r.statuses["V"].status_bound_by)


def test_a_quote_whose_snapshot_is_not_held_is_not_called_single_source():
    """No snapshot, no hosts to count: its ceiling already says freshness is
    unknown, and "single source" would be a guess."""
    store, s = world()
    p = restated("P", s)
    r = derive([p], [], SnapshotStore(), as_of=NOW)
    assert r.statuses["P"].status == Status.HYPOTHESIS
    assert not any("single source" in b for b in r.statuses["P"].status_bound_by)
