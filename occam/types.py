"""Occam's own copies of the engine's ordered types.

Copied, not imported: importing anything from `anvikshiki_v4` executes its
package `__init__`, which loads the whole knowledge-base engine (#150). A law
holds these to the engine's definitions, so the copy cannot drift.
"""

from __future__ import annotations

from enum import IntEnum

__all__ = ["Pramana"]


class Pramana(IntEnum):
    """The pramāṇa hierarchy — higher value, stronger channel. Same values as
    the engine's `PramanaType`, so preference compares identically."""

    UPAMANA = 1     # analogy
    SABDA = 2       # testimony — every fetched document
    ANUMANA = 3     # inference
    PRATYAKSA = 4   # direct evidence
