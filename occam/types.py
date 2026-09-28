"""Occam's own copies of the engine's ordered types.

Copied, not imported: importing anything from `anvikshiki_v4` executes its
package `__init__`, which loads the whole knowledge-base engine (#150). Laws
hold these to the engine's definitions, so the copies cannot drift.
"""

from __future__ import annotations

from enum import Enum, IntEnum

__all__ = ["Pramana", "Status", "STATUS_ORDER", "rank"]


class Pramana(IntEnum):
    """The pramāṇa hierarchy — higher value, stronger channel. Same values as
    the engine's `PramanaType`, so preference compares identically."""

    UPAMANA = 1     # analogy
    SABDA = 2       # testimony — every fetched document
    ANUMANA = 3     # inference
    PRATYAKSA = 4   # direct evidence


class Status(Enum):
    """The five epistemic statuses. Derived in `status.py`, never assigned."""

    CONTESTED = "contested"
    OPEN = "open"
    PROVISIONAL = "provisional"
    HYPOTHESIS = "hypothesis"
    ESTABLISHED = "established"


# Weakest first; the index is the rank. Same order as the engine's lattice.
STATUS_ORDER: tuple[Status, ...] = (
    Status.CONTESTED, Status.OPEN, Status.PROVISIONAL,
    Status.HYPOTHESIS, Status.ESTABLISHED,
)


def rank(status: Status) -> int:
    return STATUS_ORDER.index(status)
