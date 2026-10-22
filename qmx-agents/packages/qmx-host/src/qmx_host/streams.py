"""One held stream per reachable owned node, so its items reach this home's inbox (AD-65).

A node that answers is held, not polled: one GET to its engine stream, and every change of its
open items lands in the cache the merged inbox reads. Nothing is copied into this home's ledger;
the row keeps its `home_engine` and this home only shows it.

A node that stops answering is not torn down. The stream retries every `RETRY_S`, and until it
answers again its rows read "server unreachable since ..." with the last values seen, which is
what `Forwarder.rows` builds from the same cache.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Final, cast

import httpx
from pydantic import JsonValue
from qmx_engine.service.forward import PASS_HEADER, Forwarder, wall

RETRY_S: Final = 5.0
"""A dropped stream reconnects in five seconds: a stream round, not a poll interval."""
READ_TIMEOUT_S: Final = 30.0


@dataclass
class Streams:
    """This home's held streams: one per owned node, and nothing else of its own."""

    forwarders: Sequence[Forwarder]
    client: httpx.AsyncClient

    @classmethod
    def of(cls, forwarders: Sequence[Forwarder]) -> Streams:
        return cls(forwarders, httpx.AsyncClient(timeout=READ_TIMEOUT_S))

    def took(self, forwarder: Forwarder, items: Sequence[Mapping[str, JsonValue]]) -> None:
        """One frame's items are the node's open set; the merged read serves them from here."""
        forwarder.down.answered("inbox.list", [dict(item) for item in items], wall(), streamed=True)

    async def hold(self, forwarder: Forwarder) -> None:
        """Hold one node's stream until cancelled. A failure marks its rows and retries."""
        while True:
            try:
                url = f"{forwarder.instance.url}/api/engine/forward/stream"
                headers = {PASS_HEADER: forwarder.pass_for()}
                async with self.client.stream("GET", url, headers=headers) as answer:
                    if answer.status_code != 200:
                        forwarder.down.failed(wall())
                        await asyncio.sleep(RETRY_S)
                        continue
                    async for kind, data in _frames(answer):
                        if kind == "inbox" and isinstance(data, list):
                            rows = [row for row in data if isinstance(row, dict)]
                            self.took(forwarder, cast("list[Mapping[str, JsonValue]]", rows))
            except httpx.HTTPError, OSError:
                forwarder.down.failed(wall())
            await asyncio.sleep(RETRY_S)

    async def hold_all(self) -> None:
        """Hold every node's stream until cancelled: the host's one task for all of them."""
        await asyncio.gather(*(self.hold(found) for found in self.forwarders))

    async def close(self) -> None:
        await self.client.aclose()


async def _frames(answer: httpx.Response) -> AsyncIterator[tuple[str, JsonValue]]:
    """The SSE frames as `(kind, payload)`: `data:` lines, one JSON object each."""
    buffer: list[str] = []

    def parsed() -> tuple[str, JsonValue] | None:
        body = "\n".join(buffer)
        buffer.clear()
        if not body.strip():
            return None
        frame = json.loads(body)
        return str(frame.get("kind")), frame.get("items")

    async for line in answer.aiter_lines():
        if line.startswith("data:"):
            buffer.append(line.removeprefix("data:").strip())
            continue
        if not line.strip():
            found = parsed()
            if found is not None:
                yield found


__all__ = ["Streams"]
