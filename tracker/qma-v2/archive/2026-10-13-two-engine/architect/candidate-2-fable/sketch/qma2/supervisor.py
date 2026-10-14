"""Process trees, kill-tree and the isolation backends. Platform-neutral seam.

Every child the harness starts (the Claude CLI the SDK spawns, every Bash command on the
OpenAI engine, hook commands) belongs to one `ProcessTree` per thread:
- Windows: a Job Object with KILL_ON_JOB_CLOSE and breakaway disallowed.
- POSIX: a process group (`start_new_session=True`), killed with `killpg`.

`Launcher` backends (the only place "who runs the agent" is decided):
- SameUserLauncher (default): scrubbed env, same OS user. Money barrier = sealed secrets +
  managed rules (speed bumps for Bash). Reported as isolation "same_user".
- LowRightsLauncher (opt-in per OS): Windows CreateProcessWithLogonW as a dedicated local user;
  POSIX `sudo -u qmx-agent` (set up by a wizard). The operator's keyring and files become
  unreachable; reported as "low_rights_user". Not needed for sign-off.

Claude SDK note: the SDK spawns the CLI itself; the adapter passes a `cli_path` wrapper
produced by `Launcher.wrap_command` so the child still lands in the thread's tree and env.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from qma2.types import ThreadId


@dataclass(frozen=True)
class Spawned:
    pid: int
    tree_id: str


class ProcessTree(Protocol):
    def adopt(self, pid: int) -> None: ...
    def kill(self, *, grace_s: float = 2.0) -> None: ...
    def alive(self) -> bool: ...


class Launcher(Protocol):
    def spawn_env(self, allow: Sequence[str], inject: Mapping[str, str]) -> dict[str, str]: ...
    def wrap_command(self, argv: Sequence[str], tree: ProcessTree) -> Sequence[str]: ...
    def isolation(self) -> str: ...


class Supervisor:
    def __init__(self, launcher: Launcher) -> None:
        raise NotImplementedError

    def tree(self, thread_id: ThreadId) -> ProcessTree:
        """One tree per thread; created on first use; idempotent."""
        raise NotImplementedError

    async def run(
        self,
        thread_id: ThreadId,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout_s: float,
        output_cap: int = 64 * 1024,
        stdin: str | None = None,
    ) -> tuple[int, str, str]:
        """Bash/PowerShell on the OpenAI engine and hook commands. Output beyond the cap is
        saved to the thread's trace dir and returned head-and-tail with a path."""
        raise NotImplementedError

    def kill_all(self) -> None: ...


class SameUserLauncher:
    def __init__(self, platform: str) -> None: ...


class LowRightsLauncher:
    def __init__(self, platform: str, user: str) -> None: ...
