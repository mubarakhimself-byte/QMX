"""The OS memory cap over every agent CLI tree, and the chat-to-process bookkeeping.

`max_live_chats` and idle reaping (harness.py) bound how many CLIs run. This bounds what they
use together, Bash children and MCP helpers included, so a runaway agent cannot starve his
desktop. The cap is `settings.toml [budgets] agent_memory_mb`, UI-editable. qmx-control
itself is never inside the cap.

This module owns the parent object. `qma.launcher` puts each chat's CLI into it, in a
per-chat child, before the CLI starts. There is no pid hunt and no connect lock (A14, B11).
- Windows: one named parent Job Object with the memory limit and kill-on-close, held by
  qmx-control. Each launcher nests a per-chat job inside it. Precedent: `qmx_apps/windows_job.py`.
- Linux: the user slice `qma-agents.slice` with `MemoryMax`, set through user systemd. Each
  launcher runs its CLI in a per-chat scope under it. Where user systemd is missing or
  refuses, `report().os_cap` is False and the live-chat cap is the only bound.
- macOS: no OS cap. The live-chat cap and reaping only.

Exceeding the cap kills or starves the agent trees, never qmx-control. Because each chat has
its own child job or scope, the report names the chat whose tree died; its reader sees the
CLI exit, the turn is marked unknown, and a `needs_you` block says why.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qma.harness.home import QmxHome, SessionId


@dataclass(frozen=True)
class CapReport:
    os_cap: bool
    """False on macOS, and on Linux without a usable user systemd."""
    limit_mb: int | None
    used_mb: int | None
    chats: tuple[SessionId, ...]
    last_killed: SessionId | None
    """The chat whose tree the OS killed most recently, if any."""


class AgentProcessCap:
    @classmethod
    def for_platform(cls, home: QmxHome, limit_mb: int | None) -> AgentProcessCap:
        """Create or adopt the parent job (Windows) or slice (Linux); a no-op on macOS.
        `None` means no memory limit; the Windows job still exists for kill-on-close.
        Idempotent: an existing slice is adopted, not recreated."""
        raise NotImplementedError

    @property
    def handle_name(self) -> str:
        """What `launch_env` passes as `QMA_CAP`: the job name, the slice name, or ""."""
        raise NotImplementedError

    def alive(self, session_id: SessionId) -> bool:
        """True when this chat's pid file names a CLI that is still running (pid and process
        start time both match, so a reused pid reads as dead)."""
        raise NotImplementedError

    def stop_chat(self, session_id: SessionId) -> None:
        """Kill this chat's whole tree: its per-chat job, its scope, or its process group.
        Idempotent."""
        raise NotImplementedError

    def kill_orphans(self) -> tuple[SessionId, ...]:
        """At `Harness.open`: `stop_chat` every chat whose pid file names a live process,
        then delete stale pid files. On Linux also stops leftover `qma-chat-*` scopes.
        Returns the chats it killed, for their `needs_you` blocks. Idempotent."""
        raise NotImplementedError

    def report(self) -> CapReport:
        raise NotImplementedError

    def set_limit(self, limit_mb: int | None) -> None:
        """Applies a UI edit to the live parent job or slice. Running chats stay members."""
        raise NotImplementedError

    def close(self) -> None:
        """Windows: closing the parent job handle kills every member (kill-on-close). Linux:
        stops every `qma-chat-*` scope. Idempotent."""
        raise NotImplementedError
