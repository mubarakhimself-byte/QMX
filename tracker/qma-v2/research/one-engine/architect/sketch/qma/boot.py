"""What a QMA process may inherit from its parent. Standard library only.

Runs as the first statement of every QMA entry point (`qma.serve`, `qma.console`). The SDK
builds each CLI's environment from `os.environ` at `connect()`, with the chat's `env` merged
over it (02a trap 6; `subprocess_cli.connect`, read 2026-10-14). So whatever survives here
reaches every CLI, every Bash call and every mini-app this process starts.

An allow-list, not a deny-list. Routing, billing, proxy, CA and process-wrapper variables
(`ANTHROPIC_*`, `CLAUDE_CODE_USE_*`, `HTTPS_PROXY`, `NODE_EXTRA_CA_CERTS`,
`CLAUDE_CODE_PROCESS_WRAPPER` and every name the CLI adds later) are gone because they are
not on the list. Everything a CLI needs from QMA is set by `launch.launch_env`.

`launch.assert_scrubbed` re-checks the same list at every launch, so a name added back at
run time refuses the launch.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Final

KEEP_NAMES: Final[frozenset[str]] = frozenset(
    {
        # every OS
        "PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "TERM", "USER", "LOGNAME", "SHELL", "TMPDIR",
        # Windows
        "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "USERPROFILE", "USERNAME", "USERDOMAIN",
        "COMPUTERNAME", "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA",
        "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "COMMONPROGRAMFILES", "TEMP", "TMP",
        "OS", "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS",
        "CLAUDE_CODE_GIT_BASH_PATH",  # how the CLI finds a non-default Git Bash; not a routing key
        # Linux: user systemd (launcher scopes) and the Secret Service (keyring)
        "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS",
    }
)
"""Matched case-insensitively (Windows env names are case-insensitive). A unit test fails
if any name here contains PROXY, ANTHROPIC, OPENAI, AWS, NODE_, SSL_ or CLAUDE (except
`CLAUDE_CODE_GIT_BASH_PATH`). Agent Bash sees only these names plus what `launch_env` sets,
which departs from vanilla Claude Code (a toolchain variable he relies on must be added
here; DESIGN open questions)."""


def scrub_process_env(environ: MutableMapping[str, str]) -> tuple[str, ...]:
    """Delete every variable whose name is not in `KEEP_NAMES`.

    Returns the removed names, sorted, never their values. `doctor` shows them so the
    operator can see what his shell was carrying. Idempotent: a second call removes
    nothing and returns ().
    """
    raise NotImplementedError
