"""Conformal status sets: coverage, what shuffling does, and no set without labels (#144).

Synthetic labels stand in for people. The world: the pipeline's derived
status is right 70% of the time and otherwise off by one rank — a simple,
stated generator, so the laws test the conformal machinery and not a claim
about the pipeline.
"""

import json
import math
import random
from datetime import datetime, timezone

import pytest

from occam.conformal import ABSTAINED, Example, evaluate, fit
from occam.types import STATUS_ORDER

ALPHA = 0.1
V = [s.value for s in STATUS_ORDER]


def world(n, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        i = rng.randrange(5)
        if rng.random() < 0.7:
            j = i
        else:
            j = min(4, max(0, i + rng.choice((-1, 1))))
        out.append(Example(derived=V[i], label=V[j]))
    return out


def tolerance(n_test, n_cal=300):
    """Three standard errors at 1 − α, counting BOTH sources of variation:
    the held-out sample and the calibration split. An earlier version counted
    only the first; over 30 seeds one real-label run fell outside it, and the
    law had passed on a lucky seed."""
    v = ALPHA * (1 - ALPHA)
    return 3 * math.sqrt(v / n_test + v / n_cal)


def test_empirical_coverage_meets_the_nominal_level_on_held_out_data():
    cal = fit(world(600, 1), alpha=ALPHA, population="synthetic")
    ev = evaluate(cal, world(3000, 2))
    assert ev.coverage >= 1 - ALPHA - tolerance(3000), ev
    assert ev.mean_set_size < 5, "informative: not every status every time"


def test_shuffled_labels_make_coverage_erratic_and_sets_uninformative():
    """What the guarantee's dependence on real labels looks like, measured
    over 30 seeds. Shuffled calibration pairs are independent while real
    test pairs are not, so exchangeability breaks: coverage neither holds
    nor collapses — it scatters (below nominal on some seeds, near-total
    over-coverage on others) — and the sets balloon on every seed. Real
    labels stay near nominal with small sets."""
    real_cov, sh_cov, below = [], [], 0
    for seed in range(30):
        data, test = world(600, 100 + seed), world(3000, 500 + seed)
        labels = [e.label for e in data]
        random.Random(seed).shuffle(labels)
        shuffled = [Example(derived=e.derived, label=l) for e, l in zip(data, labels)]
        real = evaluate(fit(data, alpha=ALPHA, population="s", seed=seed), test)
        noise = evaluate(fit(shuffled, alpha=ALPHA, population="s", seed=seed), test)
        assert noise.mean_set_size > real.mean_set_size + 2.0, seed
        real_cov.append(real.coverage)
        sh_cov.append(noise.coverage)
        below += noise.coverage < 1 - ALPHA - tolerance(3000)
    assert all(c >= 1 - ALPHA - tolerance(3000) for c in real_cov)
    assert below >= 3, "shuffling never broke coverage — the label dependence is untested"
    assert max(sh_cov) - min(sh_cov) > 2 * (max(real_cov) - min(real_cov))


def test_a_terrible_classifier_gives_large_sets_not_confident_wrong_ones():
    """A fixed table that puts 0.96 on the wrong neighbour of every status."""
    bad = {}
    for x in V + [ABSTAINED]:
        wrong = V[(V.index(x) + 2) % 5] if x in V else V[0]
        bad[x] = {y: (0.96 if y == wrong else 0.01) for y in V}
    cal = fit(world(600, 1), alpha=ALPHA, population="synthetic", table=bad)
    good = evaluate(fit(world(600, 1), alpha=ALPHA, population="synthetic"), world(3000, 2))
    ev = evaluate(cal, world(3000, 2))
    assert ev.coverage >= 1 - ALPHA - tolerance(3000)
    assert ev.mean_set_size > good.mean_set_size
    assert ev.wrong_singletons == 0


def test_too_few_calibration_examples_gives_every_status_and_says_why():
    cal = fit(world(8, 1), alpha=ALPHA, population="synthetic")
    assert cal.qhat is None
    s, why = cal.predict("hypothesis")
    assert len(s) == 5 and "too few" in why


def test_the_threshold_is_the_finite_sample_rank_not_the_plain_quantile():
    cal = fit(world(200, 3), alpha=ALPHA, population="synthetic")
    n = cal.n_cal
    k = math.ceil((n + 1) * (1 - ALPHA))
    assert k <= n and cal.qhat is not None
    # recompute independently from the same split
    idx = list(range(200))
    random.Random(0).shuffle(idx)
    data = world(200, 3)
    cal_part = [data[i] for i in idx[100:]]
    scores = sorted(1 - cal.table[e.derived][e.label] for e in cal_part)
    assert cal.qhat == scores[k - 1]


def test_every_prediction_names_its_driver_and_population():
    cal = fit(world(600, 1), alpha=ALPHA, population="synthetic factual lookups")
    _, why = cal.predict("contested")
    assert "'contested'" in why and "synthetic factual lookups" in why and "labelled examples" in why


def test_labels_and_inputs_outside_the_status_space_are_refused():
    with pytest.raises(ValueError):
        Example(derived="hypothesis", label="maybe")
    with pytest.raises(ValueError):
        Example(derived="unknown", label="open")


def test_the_answer_carries_a_set_only_when_calibrated(tmp_path):
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    from test_answer import AGREE, NO_ATTACKS, ask
    from occam.answer import replay
    ans, art = ask(AGREE, NO_ATTACKS)
    assert ans.status_set is None and "unavailable" in ans.status_set_note
    cal = fit(world(600, 1), alpha=ALPHA, population="synthetic")
    calibrated = replay(art, cal)
    assert calibrated.status_set and calibrated.status in calibrated.status_set
    assert "marginal over synthetic" in calibrated.status_set_note
    # the calibration round-trips through JSON unchanged
    from occam.conformal import Calibration
    assert Calibration.model_validate_json(cal.model_dump_json()) == cal


def test_an_unseen_derived_status_gets_every_status_never_an_empty_set():
    """A sharp classifier puts q̂ below the uniform row's score, so without the
    guard an input with no labelled examples would get an EMPTY set — a
    confident 'nothing' about the one case with no data behind it."""
    sharp = [Example(derived=v, label=v) for v in V for _ in range(60)]
    cal = fit(sharp, alpha=ALPHA, population="synthetic")
    assert cal.qhat is not None and cal.qhat < 0.8          # the dangerous regime
    s, why = cal.predict(ABSTAINED)
    assert len(s) == 5 and "no labelled example" in why


def test_smoothing_leaves_no_status_impossible():
    """Stated design: a status never seen in a row keeps a small probability.
    A zero would make it unreachable in any set, however large q̂."""
    cal = fit([Example(derived="hypothesis", label="hypothesis")] * 40,
              alpha=ALPHA, population="synthetic")
    row = cal.prob("hypothesis")
    assert all(p > 0 for p in row.values())
    assert row["established"] == 1 / (cal.table_counts["hypothesis"] + 5)


def test_a_seen_but_diffuse_row_below_the_threshold_gets_every_status():
    """Four sharp rows set a small q̂; a rare fifth row whose labels are spread
    evenly has every score above it. Without the guard its set is empty."""
    data = [Example(derived=v, label=v) for v in V[1:] for _ in range(100)]
    data += [Example(derived=V[0], label=v) for v in V for _ in range(3)]
    cal = fit(data, alpha=ALPHA, population="synthetic")
    assert cal.table_counts[V[0]] > 0 and cal.qhat is not None
    assert all(1 - p > cal.qhat for p in cal.prob(V[0]).values())   # empty without the guard
    s, why = cal.predict(V[0])
    assert len(s) == 5 and "unlike the calibration population" in why
