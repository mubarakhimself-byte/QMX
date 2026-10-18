"""What a QMA process may inherit from its parent. Standard library only.

Runs as the first statement of every QMA entry point (`qma.serve`, `qma.console`). The SDK
builds each CLI's environment from `os.environ` at `connect()`, with the chat's `env` merged
over it (02a trap 6; `subprocess_cli.connect`, read 2026-10-14). So whatever survives here
reaches every CLI, every Bash call and every mini-app this process starts.

An allow-list, not a deny-list. Routing, billing, proxy, CA and process-wrapper variables
(`ANTHROPIC_*`, `CLAUDE_CODE_USE_*`, `HTTPS_PROXY`, `NODE_EXTRA_CA_CERTS`,
`CLAUDE_CODE_PROCESS_WRAPPER` and every name the CLI adds later) are gone because they are
not on the list. Everything a CLI needs from QMA is set by `launch.launch_env`.

`launch.assert_scrubbed` re-checks at every launch that no name carrying a
`BANNED_FRAGMENTS` fragment came back at run time.

The operator extends the list in the UI (`settings.toml [environment] keep`, fix check 2.9).
`qma.serve` reads that list with `tomllib` before the scrub, so a change takes effect at the
next qmx-control start, and `doctor` says so.
"""

from __future__ import annotations

from collections.abc import Iterable, MutableMapping
from pathlib import Path
from typing import Final

BANNED_FRAGMENTS: Final[tuple[str, ...]] = ("PROXY", "ANTHROPIC", "OPENAI", "AWS", "NODE_", "SSL_", "CLAUDE")
"""No kept name may contain one of these, except `CLAUDE_CODE_GIT_BASH_PATH`. One list for
the unit test over `KEEP_NAMES`, `parse_keep_names` and `launch.assert_scrubbed`."""

KEEP_NAMES: Final[frozenset[str]] = frozenset(
    {
        # every OS
        "PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "TERM", "USER", "LOGNAME", "SHELL", "TMPDIR",
        "SSH_AUTH_SOCK",  # git over SSH through the agent (Linux, macOS, Windows OpenSSH)
        # Windows
        "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "PATHEXT", "USERPROFILE", "USERNAME", "USERDOMAIN",
        "COMPUTERNAME", "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA",
        "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "COMMONPROGRAMFILES", "TEMP", "TMP",
        "OS", "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS",
        "CLAUDE_CODE_GIT_BASH_PATH",  # how the CLI finds a non-default Git Bash; not a routing key
        # Linux: user systemd (launcher scopes), the Secret Service (keyring), the display
        "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS", "DISPLAY", "WAYLAND_DISPLAY",
    }
)
"""Matched case-insensitively (Windows env names are case-insensitive). A unit test fails
if any name here contains a `BANNED_FRAGMENTS` fragment (except `CLAUDE_CODE_GIT_BASH_PATH`).
Agent Bash sees only these names, the operator's UI keep list and what `launch_env` sets,
which departs from vanilla Claude Code (DESIGN, departures)."""


class KeepListRefused(ValueError):
    """A UI keep-list name that carries a banned fragment. `ControlService` refuses the write
    with the name; at boot the name is dropped and `doctor` names it."""


def parse_keep_names(raw: Iterable[str]) -> frozenset[str]:
    """Validate `settings.toml [environment] keep`: env-name syntax, no `BANNED_FRAGMENTS`
    fragment. Raises `KeepListRefused` naming the first bad name. Toolchain names such as
    `JAVA_HOME`, `GOPATH` or a conda prefix go here, never into `KEEP_NAMES`."""
    raise NotImplementedError


def read_keep_names(settings_toml: Path) -> frozenset[str]:
    """`tomllib` read of `[environment] keep`, then `parse_keep_names`. A missing file or
    section gives the empty set. Never raises at boot: bad names are dropped and reported."""
    raise NotImplementedError


def scrub_process_env(environ: MutableMapping[str, str], extra_keep: frozenset[str] = frozenset()) -> tuple[str, ...]:
    """Delete every variable whose name is not in `KEEP_NAMES | extra_keep`.

    Returns the removed names, sorted, never their values. `doctor` shows them so the
    operator can see what his shell was carrying. Idempotent: a second call removes
    nothing and returns ().
    """
    raise NotImplementedError
