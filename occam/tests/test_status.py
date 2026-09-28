"""Stage 6: status from both extensions, weakest link binding (#142, #148)."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from occam.argue import Argument
from occam.attack import FALLACY_OF_TYPE, Attack
from occam.snapshot import SnapshotStore, capture
from occam.solve import Label
from occam.spans import MIN_DISCRIMINATING_LENGTH, is_discriminating, locate
from occam.status import TOP, derive
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
    r = derive([q("Q", s, LONG1)], [], store, as_of=NOW)
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
    r = derive([q("A", s, SHORT), step("I", "A"), q("B", s, LONG3)],
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
    assert r.statuses["P"].status_bound_by == ("quote P restated in the model's words",)


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
    assert r.statuses["Q"].status_bound_by == ("quote Q: support not judged",)


def test_a_quote_whose_support_could_not_be_told_caps_at_provisional():
    store, s = world()
    a = q("Q", s, LONG1).model_copy(update={"support": "cannot_tell"})
    r = derive([a], [], store, as_of=NOW)
    assert r.statuses["Q"].status == Status.PROVISIONAL
