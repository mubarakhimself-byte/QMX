"""LangGraph checkpoints and scoped records on the existing daemon journal.

The graph owns its cursor. QMX owns the journal and request lifecycle. No extra
database, server, tracing service or independent step scheduler is involved.
"""

from __future__ import annotations

import base64
import json
import threading
from collections.abc import Sequence
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import ChannelVersions, Checkpoint, CheckpointMetadata
from langgraph.checkpoint.memory import InMemorySaver
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qmf.core import is_refusal

from .providers import ProviderError


class JournalCheckpointer(InMemorySaver):
    """Official saver semantics, reconstructed from trusted journal records.

    Checkpoint data uses LangGraph's serializer with pickle fallback disabled.
    Only the daemon can write these records. Payloads are encoded strings because
    the canonical QMX journal deliberately excludes JSON nulls and floats.
    """

    def __init__(self, journal: AuthoritativeJournal) -> None:
        super().__init__()  # pyright: ignore[reportUnknownMemberType] - upstream factory annotation
        self.journal = journal
        self._journal_lock = threading.RLock()
        events = journal.read_events()
        if is_refusal(events):
            raise ProviderError("storage_failure", "Cannot restore graph checkpoints")
        for event in events.value:
            if event.event != "agent_graph.checkpoint":
                continue
            args = self.serde.loads_typed(
                (str(event.payload["encoding"]), base64.b64decode(str(event.payload["data"])))
            )
            if event.payload["method"] == "put":
                super().put(*args)
            elif event.payload["method"] == "writes":
                super().put_writes(*args)

    def _append(self, method: str, args: tuple[Any, ...]) -> None:
        config = args[0]
        durable_config = {
            "configurable": {
                key: value
                for key, value in config["configurable"].items()
                if key in {"thread_id", "checkpoint_ns", "checkpoint_id", "checkpoint_map"}
            }
        }
        args = (durable_config, *args[1:])
        encoding, data = self.serde.dumps_typed(args)
        saved = self.journal.append_event(
            event="agent_graph.checkpoint",
            payload={
                "method": method,
                "encoding": encoding,
                "data": base64.b64encode(data).decode("ascii"),
            },
        )
        if is_refusal(saved):
            raise ProviderError("storage_failure", "Graph checkpoint was not persisted")

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        with self._journal_lock:
            # Durability precedes exposure to the graph's next step.
            self._append("put", (config, checkpoint, metadata, new_versions))
            return super().put(config, checkpoint, metadata, new_versions)

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        with self._journal_lock:
            self._append("writes", (config, writes, task_id, task_path))
            super().put_writes(config, writes, task_id, task_path)


class JournalRecords:
    """Scoped workflow definitions, memory and effect receipts; no permissions."""

    def __init__(self, journal: AuthoritativeJournal) -> None:
        self.journal = journal

    def get(self, kind: str, key: str) -> dict[str, Any] | None:
        events = self.journal.read_events()
        if is_refusal(events):
            raise ProviderError("storage_failure", "Cannot read graph records")
        for event in reversed(events.value):
            if (
                event.event == "agent_graph.record"
                and event.payload.get("key") == key
                and event.payload.get("kind") == kind
            ):
                return json.loads(str(event.payload["body"]))
        return None

    def put(self, kind: str, key: str, body: dict[str, Any]) -> None:
        encoded = json.dumps(body, ensure_ascii=False, allow_nan=False, sort_keys=True)
        saved = self.journal.append_event(
            event="agent_graph.record", payload={"kind": kind, "key": key, "body": encoded}
        )
        if is_refusal(saved):
            raise ProviderError("storage_failure", "Graph record was not persisted")
