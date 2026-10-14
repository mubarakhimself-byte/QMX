"""One OS memory cap over every agent CLI process tree.

`max_live_chats` and idle reaping (harness.py) bound how many CLIs run. This bounds what
they use together, Bash children and MCP helpers included, so a runaway agent cannot
starve his desktop. The cap is `settings.toml [budgets] agent_memory_mb`, UI-editable.
qmx-control itself is never inside the cap.

Per OS:
- Windows: one Job Object with a job memory limit and JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE.
  Processes a member starts later inherit the job. Kill-on-close also ends every CLI when
  qmx-control dies, so no CLI outlives its host. Precedent: `qmx_apps/windows_job.py`.
- Linux: a delegated cgroup v2 subtree under the user's systemd slice
  (`qma-agents.slice`) with `MemoryMax`. Adoption writes the pid to its `cgroup.procs`.
  Children inherit the cgroup.
- macOS: no OS cap. The live-chat cap and reaping only.

Exceeding the cap kills or starves the agent tree, never qmx-control. The chat's reader
sees the CLI exit, the turn is marked unknown, and a `needs_you` block says why.

The SDK does not hand back the CLI's pid (Inferred). `adopt_tree` finds the new child of
qmx-control after `connect()` and adopts it plus every descendant it already started,
before the first prompt goes out, so nothing the agent runs escapes. Check S30 proves it.
If that proves unreliable, the fallback is `cli_path` pointed at a small launcher that
joins the job or cgroup before it starts the real CLI.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapReport:
    os_cap: bool
    """False on macOS, and wherever the cgroup subtree is not delegated."""
    limit_mb: int | None
    used_mb: int | None
    members: int


class AgentProcessCap:
    @classmethod
    def for_platform(cls, limit_mb: int | None) -> AgentProcessCap:
        """Windows job, Linux cgroup, or the no-op on macOS. `None` means no OS limit but
        the Windows job still exists for kill-on-close. Idempotent: on Linux an existing
        `qma-agents.slice` is adopted, not recreated."""
        raise NotImplementedError

    def adopt_tree(self, root_pid: int) -> None:
        """Put `root_pid` and its current descendants under the cap. Adopting a pid twice
        is a no-op."""
        raise NotImplementedError

    def new_child_pid(self, before: frozenset[int]) -> int:
        """The qmx-control child that appeared since `before` (a snapshot taken just before
        `connect()`) and runs the bundled CLI. Raises if there is not exactly one.
        `Harness` connects one chat at a time (one asyncio lock around connect), so the
        diff names one child."""
        raise NotImplementedError

    def report(self) -> CapReport:
        raise NotImplementedError

    def set_limit(self, limit_mb: int | None) -> None:
        """Applies a UI edit to the live job or cgroup. Running members stay members."""
        raise NotImplementedError

    def close(self) -> None:
        """Windows: closing the job handle kills every member (kill-on-close). Linux: leaves
        the slice; members exit when their stdin closes. Idempotent."""
        raise NotImplementedError
