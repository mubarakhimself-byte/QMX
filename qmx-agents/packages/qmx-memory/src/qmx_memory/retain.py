"""The retain worker: a session's own words become one digest row on its agent ref (AD-18).

A chat's blocks are read from the harness's session record at turn end, on idle, at a compaction
and at close, cut to P-MEM's 8,000-character digest and written as one `lesson` row whose
`derived-from` edge names the session item and the run (or chat) it came from. The row is then
retained, so the next chat recalls it.

The worker is idempotent by (chat, block count): a turn that ended twice, or a close after a turn
end, writes nothing new. A digest longer than one turn's blocks is a `lesson` row; a compaction
writes one too, so the summary a chat loses to its own compaction is still in memory.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from qmx_memory.engine import RecallEngine
from qmx_memory.rows import digest_text

TRIGGERS: tuple[str, ...] = ("turn-end", "idle", "compaction", "close")
"""What makes a digest (§28.6). Every one of them lands on the same row shape."""

LIMIT = 8_000
"""Characters of a session one digest carries: P-MEM's digest size, so the two measure alike."""

MAX_BLOCKS = 400
"""Blocks one digest reads. A longer chat keeps its newest blocks: the digest is a summary, not an
archive, and the transcript blob is the archive."""


def _skipped(what: str, error: Exception) -> None:
    print(f"memory {what} skipped: {type(error).__name__}: {error}", file=sys.stderr)


@dataclass
class RetainWorker:
    """Writes one digest row per trigger, in the home's scope, and retains it."""

    engine: RecallEngine
    blocks: Callable[[str], Sequence[Mapping[str, object]]]
    """The harness's recorded blocks for one chat, oldest first."""
    session_item: Callable[[str], str | None] = field(default=lambda chat: None)
    """The chat's `session` item object id, so the digest's `derived-from` edge names a real
    object. The recorder answers it; a chat with no item yet gets no edge."""
    home: str = "hub"
    clock: Callable[[], datetime] = field(default=lambda: datetime.now(UTC))
    _seen: dict[str, int] = field(default_factory=dict[str, int])
    _rows: dict[str, str] = field(default_factory=dict[str, str])

    def digest(self, chat: str, trigger: str) -> str | None:
        """Write and retain the chat's digest. The row id when one was written, None when there
        was nothing new to keep."""
        if trigger not in TRIGGERS:
            raise ValueError(f"{trigger!r} is not one of {', '.join(TRIGGERS)}")
        found = list(self.blocks(chat))[-MAX_BLOCKS:]
        text = digest_text(found, LIMIT)
        if not text.strip():
            return None
        seen = self._seen.get(chat, 0)
        if seen == len(found) and chat in self._rows:
            return None
        row = {
            "tag": "lesson",
            "when_to_use": f"what chat {chat} found, at its {trigger}",
            "content": text,
            "refs": [f"session:{chat}"],
            "keywords": [chat, trigger],
            "source_run_ids": [chat],
            "learned_at": self.clock().isoformat(),
        }
        item = self.session_item(chat)
        try:
            written = self.engine.write(
                "home", self.home, row, derived_from=([item] if item else [])
            )
        except Exception as error:  # a memory write never fails a chat
            _skipped(f"digest at {trigger}", error)
            return None
        self._seen[chat] = len(found)
        self._rows[chat] = written.object_id
        return written.object_id

    def turn_ended(self, chat: str) -> str | None:
        return self.digest(chat, "turn-end")

    def compacted(self, chat: str) -> str | None:
        return self.digest(chat, "compaction")

    def idle(self, chat: str) -> str | None:
        return self.digest(chat, "idle")

    def closed(self, chat: str) -> str | None:
        digest = self.digest(chat, "close")
        self._seen.pop(chat, None)
        self._rows.pop(chat, None)
        return digest
