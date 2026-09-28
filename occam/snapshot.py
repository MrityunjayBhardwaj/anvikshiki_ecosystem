"""Content-addressed storage for fetched documents (#137).

Everything the Occam pipeline concludes is addressed back to bytes stored here.
The reason is the property the engine exists for: after the model has spoken,
the pipeline is deterministic — same arguments and attacks give the same graph,
the same labels and the same conclusions, with no model in the loop. Reason
against a live URL instead and a re-run reads a document that has since
changed, so a third party disputing one step has nothing to dispute against.
The disagreement loses its address.

Two hashes, and the distinction is the whole point of this module
─────────────────────────────────────────────────────────────────
`id` is the hash of `body` — the bytes that were served. `text_sha256` is the
hash of `text` — the characters that spans index into.

They are different facts and one hash cannot carry both. Change the text
extractor and every stored offset moves, while `body` is byte-identical: a
span anchored to the body alone would silently begin pointing at different
words, and nothing would report it. `extractor` is recorded beside the text
hash for the same reason — knowing *that* the extraction changed is only
useful alongside what it changed to.

What is deduplicated, and on which hash
───────────────────────────────────────
Storage is keyed by `id`, because that is what a span names. Source counting
is keyed by `text_sha256`, because two documents whose extracted text is
identical are one source — counting them as two inflates the independence
signal that `n_domains` and `n_snapshots` are supposed to carry.

Both are needed. Keying storage on the text hash would lose which bytes were
served; counting sources by id would let one document behind two URLs look
like corroboration.

Absence is recorded, never swallowed
────────────────────────────────────
A paywall, a robots exclusion, a PDF with no text layer and a network failure
all produce a snapshot whose `text` is empty — and each for a different reason
that a reader needs. "Could not look" must never print as "nothing found":
they call for opposite actions, and by the time the pipeline reports a status
the difference is unrecoverable. So `empty_reason` is mandatory whenever
`text` is empty, enforced at construction rather than by convention.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Iterator, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = ["Snapshot", "SnapshotStore", "body_address", "text_address"]


def body_address(body: bytes) -> str:
    """The content address of served bytes. This is a snapshot's identity."""
    return "sha256:" + hashlib.sha256(body).hexdigest()


def text_address(text: str) -> str:
    """The content address of extracted text. This is what spans point into."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Snapshot(BaseModel):
    """One fetched document, frozen at the moment it was read."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Content address of `body`: 'sha256:<hex>'.")
    urls: tuple[str, ...] = Field(
        description=(
            "Every address this exact body was served from. A tuple rather "
            "than a single URL because the same document is routinely "
            "reachable at several, and discarding the others would make two "
            "sightings of one document look like two sources."
        ),
    )
    fetched_at: datetime = Field(
        description=(
            "When the bytes were read. Mandatory: decay reads this, and a "
            "missing value must never be taken for 'just now'."
        ),
    )
    media_type: str = ""
    body: bytes = Field(repr=False)
    text: str = Field(
        default="",
        repr=False,
        description="Extracted plain text. Character offsets index into this.",
    )
    text_sha256: str = Field(
        description=(
            "Hash of `text`. Pins which extraction the offsets belong to, "
            "which `id` cannot: the same bytes extracted by a different "
            "version produce different offsets for the same words."
        ),
    )
    extractor: str = Field(
        default="",
        description=(
            "What produced `text`. Recorded because a changed extraction is "
            "only actionable if you can see what it changed to."
        ),
    )
    empty_reason: Optional[str] = Field(
        default=None,
        description=(
            "Why `text` is empty — paywalled, robots-excluded, no text layer, "
            "fetch failed. Required when `text` is empty, because a document "
            "we could not read and a document that said nothing call for "
            "opposite actions."
        ),
    )

    @model_validator(mode="after")
    def _check(self) -> "Snapshot":
        if self.id != body_address(self.body):
            raise ValueError(
                f"id {self.id!r} is not the content address of the body "
                f"({body_address(self.body)!r}). The id IS the hash; a "
                f"snapshot whose id was assigned rather than computed cannot "
                f"be verified by anyone holding it."
            )
        if self.text_sha256 != text_address(self.text):
            raise ValueError(
                "text_sha256 does not hash `text`. Spans resolve by comparing "
                "this field, so a wrong value makes every span against this "
                "snapshot unresolvable — which reads as fabrication."
            )
        if not self.urls:
            raise ValueError("a snapshot with no URL cannot be re-fetched or disputed")
        if not self.text.strip() and not self.empty_reason:
            raise ValueError(
                "empty text with no reason. A paywall, a robots exclusion, a "
                "PDF with no text layer and a network failure are different "
                "findings; collapsing them into a silent empty string is the "
                "defect this field exists to prevent."
            )
        if self.text.strip() and self.empty_reason:
            raise ValueError(
                f"text is present but empty_reason is set ({self.empty_reason!r}); "
                f"one of the two is wrong and a reader cannot tell which"
            )
        return self


def capture(
    *,
    url: str,
    body: bytes,
    text: str,
    fetched_at: datetime,
    media_type: str = "",
    extractor: str = "",
    empty_reason: Optional[str] = None,
) -> Snapshot:
    """Build a snapshot, computing both addresses rather than accepting them.

    The only supported way to make one. Taking hashes from a caller would let a
    snapshot claim an address it does not have, and the address is the single
    thing every downstream guarantee rests on.
    """
    return Snapshot(
        id=body_address(body),
        urls=(url,),
        fetched_at=fetched_at,
        media_type=media_type,
        body=body,
        text=text,
        text_sha256=text_address(text),
        extractor=extractor,
        empty_reason=empty_reason,
    )


class SnapshotStore:
    """Snapshots by content address, with source counting by text hash."""

    def __init__(self) -> None:
        self._by_id: dict[str, Snapshot] = {}
        self._ids_by_text: dict[str, list[str]] = {}

    def put(self, snapshot: Snapshot) -> Snapshot:
        """Store it, or merge its URL into the snapshot already held.

        Returns the canonical record. Re-fetching the same bytes from a second
        address adds the address and keeps the original `fetched_at`: the
        earlier read is when this content was witnessed, and overwriting it
        would quietly make a stale document look fresh to the decay factor.
        """
        held = self._by_id.get(snapshot.id)
        if held is None:
            self._by_id[snapshot.id] = snapshot
            self._ids_by_text.setdefault(snapshot.text_sha256, []).append(snapshot.id)
            return snapshot

        merged_urls = held.urls + tuple(u for u in snapshot.urls if u not in held.urls)
        if merged_urls == held.urls:
            return held
        canonical = held.model_copy(update={"urls": merged_urls})
        self._by_id[snapshot.id] = canonical
        return canonical

    def get(self, snapshot_id: str) -> Optional[Snapshot]:
        return self._by_id.get(snapshot_id)

    def ids_for_text(self, text_sha256: str) -> tuple[str, ...]:
        """Every stored body whose extracted text hashes to this.

        More than one is normal and not a fault: two servers can deliver
        different bytes — different ads, different whitespace — that extract to
        identical text. For span resolution they are interchangeable; for
        counting sources they are one.
        """
        return tuple(self._ids_by_text.get(text_sha256, ()))

    def distinct_sources(self) -> int:
        """Sources, counted by extracted text rather than by stored body.

        The number `n_snapshots` should report. Counting `len(self)` instead
        would let one document held at two addresses read as corroboration.
        """
        return len(self._ids_by_text)

    def readable(self) -> tuple[Snapshot, ...]:
        """Snapshots that yielded text. The denominator for `retrieval_hits`."""
        return tuple(s for s in self._by_id.values() if s.text.strip())

    def unreadable(self) -> tuple[Snapshot, ...]:
        """Snapshots that yielded nothing, each with its reason.

        Reported separately and never silently dropped: a run that fetched ten
        documents and could read none is a very different finding from a run
        that found nothing to fetch, and both end with no text in hand.
        """
        return tuple(s for s in self._by_id.values() if not s.text.strip())

    def __len__(self) -> int:
        return len(self._by_id)

    def __iter__(self) -> Iterator[Snapshot]:
        return iter(self._by_id.values())

    def __contains__(self, snapshot_id: object) -> bool:
        return snapshot_id in self._by_id
