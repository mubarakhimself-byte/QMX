"""One data route: a venue's public frames for the instruments it lists, in the internal format."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from qmf.venue.routes.frames import READERS, SNAPSHOT_READERS, Chains, UnreadFrame
from qmf.venue.routes.model import Event, Listing


class Route:
    """Normalises one venue's frames. It holds each listed book's chain, so a delta reads
    `ready` only while it follows the last snapshot; one route serves one connection."""

    def __init__(self, venue: str, listings: Iterable[Listing]) -> None:
        if venue not in READERS:
            raise ValueError(f"no data route reads {venue}; routes read {', '.join(READERS)}")
        self.venue = venue
        self.listings = {listing.native: listing for listing in listings}
        self._chains: Chains = {}

    def normalise(self, frame: Mapping[str, Any], receive_time: int) -> list[Event]:
        """The events in one parsed frame, received at `receive_time` (Unix nanoseconds).
        Acknowledgements give none; a frame this route cannot read raises `UnreadFrame`."""
        try:
            return READERS[self.venue](frame, receive_time, self.listings, self._chains)
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise UnreadFrame(
                f"{self.venue} frame not read: {type(error).__name__}: {error}"
            ) from error

    def snapshot(self, native: str, answer: Mapping[str, Any], receive_time: int) -> list[Event]:
        """A REST book answer for `native`, which the venue's diff stream then chains from."""
        reader = SNAPSHOT_READERS.get(self.venue)
        if reader is None:
            raise UnreadFrame(f"{self.venue} sends its book snapshots in the stream itself")
        try:
            return reader(answer, receive_time, self.listings[native], self._chains)
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise UnreadFrame(
                f"{self.venue} snapshot not read: {type(error).__name__}: {error}"
            ) from error
