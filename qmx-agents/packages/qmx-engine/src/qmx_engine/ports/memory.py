"""The memory port (SOLUTION-DESIGN 8.1a, AD-18) and the stub that stands in until the memory
packet: an empty snapshot, nothing recalled, built or dead-ended, `note` storing a `run`-scope row
in the Library, and `consolidate` a no-op that logs."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol

from pydantic import JsonValue

from qmx_engine.ports.library import JsonObject, LibraryPort

LOG = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Snapshot:
    text: str = ""
    version: str = "empty"
    row_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Hit:
    row_id: str
    text: str
    tag: str
    score: float
    refs: tuple[str, ...] = ()
    provenance: JsonObject = field(default_factory=dict[str, JsonValue])


@dataclass(frozen=True, slots=True)
class Consolidated:
    added: int = 0
    merged: int = 0
    corrected: int = 0
    pruned: int = 0


class MemoryPort(Protocol):
    def snapshot(self, scopes: tuple[str, ...], budget_tokens: int) -> Snapshot: ...

    def recall(
        self, query: str, scopes: tuple[str, ...], budget: int, tags: tuple[str, ...] = ()
    ) -> list[Hit]: ...

    def check_built(self, intent_key: str) -> list[str]: ...

    def check_dead_end(self, query: str) -> list[Hit]: ...

    def note(self, run_id: str, row: JsonObject) -> str:
        """The only write a node or agent has; it lands in `run` scope."""
        ...

    def consolidate(self, run_id: str, into_scope: str) -> Consolidated: ...

    def feedback(self, row_ids: tuple[str, ...], outcome: str) -> None: ...

    def search_runs(self, query: str, workflow: str | None = None) -> list[Hit]: ...


class MemoryStub:
    def __init__(self, library: LibraryPort) -> None:
        self.library = library

    def snapshot(self, scopes: tuple[str, ...], budget_tokens: int) -> Snapshot:
        return Snapshot()

    def recall(
        self, query: str, scopes: tuple[str, ...], budget: int, tags: tuple[str, ...] = ()
    ) -> list[Hit]:
        return []

    def check_built(self, intent_key: str) -> list[str]:
        return []

    def check_dead_end(self, query: str) -> list[Hit]:
        return []

    def note(self, run_id: str, row: JsonObject) -> str:
        return self.library.put_memory_row(run_id, row, principal=f"run:{run_id}").object_id

    def consolidate(self, run_id: str, into_scope: str) -> Consolidated:
        LOG.info("memory consolidation of %s into %s skipped: memory is a stub", run_id, into_scope)
        return Consolidated()

    def feedback(self, row_ids: tuple[str, ...], outcome: str) -> None:
        return None

    def search_runs(self, query: str, workflow: str | None = None) -> list[Hit]:
        return []
