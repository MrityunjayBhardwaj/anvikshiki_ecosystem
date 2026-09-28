"""Occam Ānvīkṣikī — an isolated minimal pipeline for answers you can check.

A black-box model proposes arguments with verifiable spans; a deterministic
solver decides; conformal prediction quantifies what is left. No predicates,
no ontology, no knowledge base, no regular expressions.

Deliberately isolated. This package must not import the knowledge-base layer,
the predicate matcher, or coverage routing — a test asserts the import graph,
because isolation stated in a docstring is a claim and isolation asserted by a
law is a property.
"""

from .snapshot import Snapshot, SnapshotStore, body_address, capture, text_address

__all__ = [
    "Snapshot", "SnapshotStore", "capture", "body_address", "text_address",
]
