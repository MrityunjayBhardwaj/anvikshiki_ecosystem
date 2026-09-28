"""Conformal prediction over epistemic status (#144).

Stages 4–6 are deterministic given their input, but their input came from a
model. Reporting a single status hides that. This stage turns the status into
a *set* of statuses with a coverage guarantee:

    P(true status ∈ set) ≥ 1 − α

marginal over the population the calibration labels were drawn from, and
only under exchangeability with it. Nothing more is promised.

The classifier is interpretable on purpose
──────────────────────────────────────────
p̂(y | x) is a table: for each status the pipeline derived (x), how often
people who read the answer and its quotes judged it to be each status (y),
Laplace-smoothed. Every prediction can therefore cite what drove it — "the
pipeline said hypothesis; of 41 such labelled answers, people judged …".

Split conformal, done by the book
─────────────────────────────────
Labels are split, deterministically, into a half that fits the table and a
half that calibrates it. Scores are s = 1 − p̂(true | x). With n calibration
scores the threshold is the ⌈(n+1)(1−α)⌉-th smallest; when that rank exceeds
n, no finite threshold gives the guarantee, and every status is in the set —
said so, never replaced by a smaller uncalibrated set.

Without a calibration there is no set at all, and the answer says the
guarantee is unavailable. A set built from an uncalibrated quantile is a
number whose meaning nobody can state.

What shuffling the labels does — measured, not predicted
────────────────────────────────────────────────────────
#144 expected coverage to collapse under shuffled calibration labels; I first
expected it to hold. Over 30 seeds it does neither: shuffled calibration pairs
are independent while real test pairs are not, so exchangeability breaks and
coverage *scatters* (0.79 to 1.00; below nominal on 8 of 30 seeds), while the
sets balloon to ~4.6 of 5 statuses on every seed. With real labels: 0.88 to
0.95, sets of ~2. A law asserts the measured shape.
"""

from __future__ import annotations

import math
import random
from typing import Optional, Sequence

from pydantic import BaseModel, ConfigDict

from .types import STATUS_ORDER, Status

__all__ = ["Example", "Calibration", "fit", "evaluate", "ABSTAINED"]

# The input category for an answer the pipeline abstained on.
ABSTAINED = "abstained"
_INPUTS = tuple(s.value for s in STATUS_ORDER) + (ABSTAINED,)
_LABELS = tuple(s.value for s in STATUS_ORDER)


class Example(BaseModel):
    """One labelled answer: what the pipeline derived, what a person judged."""

    model_config = ConfigDict(frozen=True)

    derived: str        # a status value, or "abstained"
    label: str          # a status value — a person's judgment
    ref: str = ""       # which artifact, for audit

    def model_post_init(self, _ctx) -> None:
        if self.derived not in _INPUTS:
            raise ValueError(f"derived {self.derived!r} is not one of {_INPUTS}")
        if self.label not in _LABELS:
            raise ValueError(f"label {self.label!r} is not one of {_LABELS}")


class Calibration(BaseModel):
    """A fitted table and its conformal threshold. Persisted as JSON."""

    model_config = ConfigDict(frozen=True)

    alpha: float
    table: dict[str, dict[str, float]]     # derived -> label -> p̂
    table_counts: Optional[dict[str, int]] # examples behind each row; None for a fixed table
    n_fit: int
    n_cal: int
    qhat: Optional[float]                  # None: too few calibration scores for α
    population: str                        # what the labels were drawn from

    def prob(self, derived: str) -> dict[str, float]:
        return self.table[derived]

    def predict(self, derived: str) -> tuple[tuple[Status, ...], str]:
        """The status set for an answer, and the sentence that explains it."""
        p = self.prob(derived)
        behind = None if self.table_counts is None else self.table_counts.get(derived, 0)
        if self.qhat is None:
            return tuple(STATUS_ORDER), (
                f"every status: {self.n_cal} calibration examples are too few to "
                f"guarantee {1 - self.alpha:.0%} coverage")
        # Include y when its score is within the threshold — computed exactly
        # as the calibration scores were. Comparing p̂ ≥ 1 − q̂ instead is not
        # the same test in floating point: 1 − (1 − 0.01) ≠ 0.01, and the
        # difference dropped the true status from every set.
        chosen = tuple(s for s in STATUS_ORDER if 1 - p[s.value] <= self.qhat)
        if behind == 0:
            return tuple(STATUS_ORDER), (
                f"every status: no labelled example had derived status '{derived}', "
                f"so the table has nothing to say about it")
        if not chosen:
            # An empty set would read as a confident "none of these". It only
            # means this row is unlike anything calibrated; say that instead.
            return tuple(STATUS_ORDER), (
                f"every status: no status is within the calibrated threshold for "
                f"derived status '{derived}' — unlike the calibration population")
        return chosen, (
            f"P(true status in set) >= {1 - self.alpha:.0%}, marginal over "
            f"{self.population} (n_cal={self.n_cal}); driven by derived status "
            f"'{derived}', " + (f"{behind} labelled examples behind that row"
                                if behind is not None else "a fixed table, not fitted to labels"))


def _table(examples: Sequence[Example]) -> tuple[dict[str, dict[str, float]], dict[str, int]]:
    counts = {x: {y: 0 for y in _LABELS} for x in _INPUTS}
    for e in examples:
        counts[e.derived][e.label] += 1
    table, totals = {}, {}
    for x in _INPUTS:
        total = sum(counts[x].values())
        totals[x] = total
        table[x] = {y: (counts[x][y] + 1) / (total + len(_LABELS)) for y in _LABELS}
    return table, totals


def fit(examples: Sequence[Example], *, alpha: float = 0.1, population: str,
        seed: int = 0, table: Optional[dict[str, dict[str, float]]] = None) -> Calibration:
    """Split, fit the table on one half, calibrate on the other.

    `table` substitutes a fixed classifier — used by the law that a bad
    classifier produces large sets rather than confident wrong ones.
    """
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0, 1)")
    idx = list(range(len(examples)))
    random.Random(seed).shuffle(idx)
    half = len(idx) // 2
    fit_part = [examples[i] for i in idx[:half]]
    cal_part = [examples[i] for i in idx[half:]]
    if table is None:
        table, totals = _table(fit_part)
    else:
        totals = None        # unknown — never zero, which would read as "no data"
    scores = sorted(1 - table[e.derived][e.label] for e in cal_part)
    n = len(scores)
    k = math.ceil((n + 1) * (1 - alpha))
    qhat = scores[k - 1] if 1 <= k <= n else None
    return Calibration(alpha=alpha, table=table, table_counts=totals, n_fit=len(fit_part),
                       n_cal=n, qhat=qhat, population=population)


class Evaluation(BaseModel):
    model_config = ConfigDict(frozen=True)

    covered: int
    n: int
    mean_set_size: float
    wrong_singletons: int

    @property
    def coverage(self) -> Optional[float]:
        return self.covered / self.n if self.n else None


def evaluate(cal: Calibration, held_out: Sequence[Example]) -> Evaluation:
    """Empirical coverage on held-out labels, beside the nominal 1 − α."""
    covered = size = wrong_single = 0
    for e in held_out:
        s, _ = cal.predict(e.derived)
        values = {x.value for x in s}
        covered += e.label in values
        size += len(values)
        wrong_single += len(values) == 1 and e.label not in values
    n = len(held_out)
    return Evaluation(covered=covered, n=n, mean_set_size=size / n if n else 0.0,
                      wrong_singletons=wrong_single)
