"""The memory port (SOLUTION-DESIGN 8.1a, AD-18) and the object the engine receives for it.

The port is what a node or an agent has: an empty-or-full snapshot, a recall, the already-built
and dead-end checks, one `note` write, `consolidate` and `feedback` at the run's edges, and a
model-free search over run summaries. `forget`, `rebuild` and `reflect` are the host's, on the same
object, because a chat's `memory_forget` reaches the store the host owns.

`MemoryStub` is the port as the engine composes it: the host installs the real engine (AD-59's
provider, `qmx_memory.RecallEngine`) before the door opens, and the stub answers every verb until
it does. Nothing here imports the memory package: it depends on this one, so the seam is a
registration the host makes and this module reads.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from pydantic import JsonValue

from qmx_engine.ports.library import JsonObject, LibraryPort, LibraryRefused

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
    def snapshot(
        self, scopes: tuple[str, ...], budget_tokens: int, questions: tuple[str, ...] = ()
    ) -> Snapshot: ...

    def recall(
        self,
        query: str,
        scopes: tuple[str, ...],
        budget: int,
        tags: tuple[str, ...] = (),
        *,
        now: datetime | None = None,
        regime: tuple[str, ...] = (),
    ) -> list[Hit]: ...

    def check_built(self, intent_key: str) -> list[str]: ...

    def check_dead_end(self, query: str) -> list[Hit]: ...

    def note(self, run_id: str, row: JsonObject) -> str:
        """The only write a node or agent has; it lands in `run` scope."""
        ...

    def consolidate(self, run_id: str, into_scope: str) -> Consolidated: ...

    def feedback(self, row_ids: tuple[str, ...], outcome: str) -> None: ...

    def search_runs(self, query: str, workflow: str | None = None) -> list[Hit]: ...

    def forget(self, row_ids: tuple[str, ...]) -> int:
        """Archive the rows and take them out of the index, for good (AD-18)."""
        ...

    def rebuild(self, scope: str = "all") -> str:
        """Re-index from the Library. A forgotten row is archived, so it stays out."""
        ...

    def reflect(self, question: str, tags: tuple[str, ...] = ()) -> tuple[str, list[str]]:
        """A provider that can answer a question itself, with the rows it cited."""
        ...


INSTALLED: list[MemoryPort] = []
"""The engine the host installed. A host serves one home, so one provider answers here; the list
holds at most one entry and `install(None)` clears it."""


def install(provider: MemoryPort | None) -> None:
    """Called by the host at composition, before the engine's door opens. `None` uninstalls."""
    INSTALLED.clear()
    if provider is not None:
        INSTALLED.append(provider)


def installed() -> MemoryPort | None:
    """The provider the host installed, if any."""
    return INSTALLED[0] if INSTALLED else None


class MemoryStub:
    """The port the engine is handed: the installed provider's answers, or the empty ones that
    stood in for memory before this packet. A verb with no provider answers empty and names the
    missing provider once in the log, never a refusal: memory is not a step's gate. A `note` with
    neither a provider nor a Library refuses, because it would otherwise be dropped."""

    def __init__(self, library: LibraryPort | None) -> None:
        self.library = library
        self.provider = installed()
        self.named: set[str] = set()

    def missing(self, verb: str) -> None:
        if verb not in self.named:
            self.named.add(verb)
            LOG.warning("memory %s answered empty: no memory provider is installed", verb)

    def snapshot(
        self, scopes: tuple[str, ...], budget_tokens: int, questions: tuple[str, ...] = ()
    ) -> Snapshot:
        found = self.provider
        if found is None:
            self.missing("snapshot")
            return Snapshot()
        return found.snapshot(scopes, budget_tokens, questions)

    def recall(
        self,
        query: str,
        scopes: tuple[str, ...],
        budget: int,
        tags: tuple[str, ...] = (),
        *,
        now: datetime | None = None,
        regime: tuple[str, ...] = (),
    ) -> list[Hit]:
        found = self.provider
        if found is None:
            self.missing("recall")
            return []
        return found.recall(query, scopes, budget, tags, now=now, regime=regime)

    def check_built(self, intent_key: str) -> list[str]:
        found = self.provider
        if found is None:
            self.missing("check_built")
            return []
        return found.check_built(intent_key)

    def check_dead_end(self, query: str) -> list[Hit]:
        found = self.provider
        if found is None:
            self.missing("check_dead_end")
            return []
        return found.check_dead_end(query)

    def note(self, run_id: str, row: JsonObject) -> str:
        provider = self.provider
        if provider is not None:
            return provider.note(run_id, row)
        if self.library is None:
            raise LibraryRefused("no_library", "no memory provider and no Library to note into")
        return self.library.put_memory_row(run_id, row, principal=f"run:{run_id}").object_id

    def consolidate(self, run_id: str, into_scope: str) -> Consolidated:
        provider = self.provider
        if provider is not None:
            return provider.consolidate(run_id, into_scope)
        self.missing("consolidate")
        return Consolidated()

    def feedback(self, row_ids: tuple[str, ...], outcome: str) -> None:
        provider = self.provider
        if provider is None:
            self.missing("feedback")
            return
        provider.feedback(row_ids, outcome)

    def search_runs(self, query: str, workflow: str | None = None) -> list[Hit]:
        provider = self.provider
        if provider is None:
            self.missing("search_runs")
            return []
        return provider.search_runs(query, workflow)

    def forget(self, row_ids: tuple[str, ...]) -> int:
        provider = self.provider
        if provider is None:
            self.missing("forget")
            return 0
        return provider.forget(row_ids)

    def rebuild(self, scope: str = "all") -> str:
        provider = self.provider
        if provider is None:
            self.missing("rebuild")
            return ""
        return provider.rebuild(scope)

    def reflect(self, question: str, tags: tuple[str, ...] = ()) -> tuple[str, list[str]]:
        provider = self.provider
        if provider is None:
            self.missing("reflect")
            return "", []
        return provider.reflect(question, tags)


def rows_of(row: JsonObject) -> Iterable[str]:
    """The refs a row names, for a caller that reports where a note came from."""
    found = row.get("refs")
    return [str(one) for one in found] if isinstance(found, list) else []
