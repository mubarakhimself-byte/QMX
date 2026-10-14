"""The CLI launcher: puts one chat's CLI under the OS limits before the CLI exists.

Standard library only. Installed as the console script `qma-cli-launcher` (a real `.exe`
shim on Windows, so the SDK's batch-file refusal does not apply). `launch.build_options`
passes it as `cli_path` (02a section 14: "`cli_path` overrides" the CLI lookup). The SDK
then runs `qma-cli-launcher <cli args>`, and the launcher runs the bundled CLI with the same
args, the same stdio and the same exit code.

The version probe is the exception (fix check 2.5). Before the main spawn, SDK 0.2.163 runs
`[cli_path, "-v"]` with this process's environment only, not `options.env`
(`subprocess_cli._check_claude_version`), and swallows any failure. So that start carries no
`QMA_*` input, and the `verbatim_prompts` version warning depends on its output. How the
launcher answers it is settled by HP0's version-probe box, with these fallbacks in order: a
no-input mode (on `-v`, or with no `QMA_*` names, find the bundled CLI, skip the job and the
pid file, pass the output through); else `qma.serve` sets
`CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK=1` after the scrub (the SDK reads it from `os.environ`
in `connect`) and `doctor` checks the version floor itself.

Why a launcher and not adoption after `connect()`: the SDK does not hand back the CLI's
pid, and enumerating qmx-control's children races with every other child it starts
(doctor, the exposure probe, mini-apps). A process created before its parent joined a job
also stays outside it, and MCP helpers and hooks start during `connect()`. Joining first
removes the race (interrogate A14, B11).

Inputs come from `launch_env` and are removed from the environment before the CLI starts:
    QMA_REAL_CLI     the bundled CLI path
    QMA_CHAT_ID      the chat's session id
    QMA_PROC_DIR     where the pid file goes
    QMA_CAP          the platform cap handle name: the Windows parent job name, or the
                     Linux slice name; empty on macOS

Per OS, set before the CLI starts:
- Windows. Join the named parent job (global memory limit and kill-on-close, held by
  qmx-control), then close that handle so only qmx-control keeps it alive. Create a per-chat
  job with kill-on-close, nested in the parent, held only by this launcher. Start the CLI;
  it and everything it starts inherit both jobs. If the launcher dies, the chat's tree dies.
  If qmx-control dies, every tree dies. Unverified (fix check 2.6): a pip or uv console
  script `.exe` is a trampoline that starts `python.exe`, possibly inside its own job, and a
  process already in a job may be unable to join the parent job. HP0's trampoline-job box
  measures it with two chats and picks the fallback.
- Linux. Set `PR_SET_PDEATHSIG=SIGKILL`, then exec `systemd-run --user --scope
  --slice=<QMA_CAP> --unit=qma-chat-<id>-<n> <cli> <args>`. The slice carries `MemoryMax`.
  The scope is per chat, so a memory kill names one chat and `procs.stop_chat` can stop one
  chat's whole tree. Where user systemd is missing or refuses, exec the CLI directly in a
  new process group with the death signal set: no memory cap, live-chat cap only.
- macOS. Start the CLI as a child in a new process group, watch the parent with kqueue
  (`NOTE_EXIT`), and kill the group when the parent exits or this process is terminated.
  No memory cap, live-chat cap only.

Pid file: `<QMA_PROC_DIR>/<QMA_CHAT_ID>.json` holds the launcher pid, the CLI pid and the
CLI's process start time, written atomically before the CLI reads its first byte of input,
removed on clean exit. Only this chat's launcher writes it. `procs.alive` and
`procs.kill_orphans` read it; the start time guards against pid reuse.

Second job: `qma-cli-launcher --qma-block-config-change` is the ConfigChange command hook
(`home.code_settings`). It reads the hook input, writes the reason to stderr and exits 2,
which blocks the change (Claude Code hooks reference, ConfigChange decision control). The
SDK never passes that flag to the CLI, so the two jobs cannot collide.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

BLOCK_CONFIG_CHANGE: Final = "--qma-block-config-change"
INPUT_NAMES: Final[tuple[str, ...]] = ("QMA_REAL_CLI", "QMA_CHAT_ID", "QMA_PROC_DIR", "QMA_CAP")


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch: `BLOCK_CONFIG_CHANGE` -> exit 2; otherwise join the cap for this OS,
    write the pid file, run the real CLI with `argv` unchanged and return its exit code."""
    raise NotImplementedError
