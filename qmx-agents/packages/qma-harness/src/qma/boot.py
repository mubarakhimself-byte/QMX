"""What a QMA process may inherit from its parent. Standard library only.

Runs as the first statement of every QMA entry point. The SDK builds each CLI's environment
from `os.environ` at `connect()`, so whatever survives here reaches every CLI, every Bash call
and every mini-app this process starts. An allow-list, not a deny-list: routing, billing,
proxy, CA and process-wrapper variables are gone because they are not on the list.
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Iterable, MutableMapping
from pathlib import Path
from typing import Final, cast

BANNED_FRAGMENTS: Final[tuple[str, ...]] = (
    "PROXY",
    "ANTHROPIC",
    "OPENAI",
    "AWS",
    "NODE_",
    "SSL_",
    "CLAUDE",
)
"""No kept name may contain one of these, except `GIT_BASH_NAME`."""

GIT_BASH_NAME: Final = "CLAUDE_CODE_GIT_BASH_PATH"
"""How the CLI finds a non-default Git Bash. Not a routing key."""

KEEP_NAMES: Final[frozenset[str]] = frozenset(
    {
        "PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "TERM", "USER", "LOGNAME", "SHELL",
        "TMPDIR", "SSH_AUTH_SOCK",
        "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "PATHEXT", "USERPROFILE", "USERNAME",
        "USERDOMAIN", "COMPUTERNAME", "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA",
        "PROGRAMDATA", "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "COMMONPROGRAMFILES",
        "TEMP", "TMP", "OS", "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS",
        GIT_BASH_NAME,
        "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS", "DISPLAY", "WAYLAND_DISPLAY",
    }
)  # fmt: skip
"""Matched case-insensitively, because Windows environment names are."""

_ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_()]*")


class KeepListRefused(ValueError):
    """A keep-list name that is not an environment name or carries a banned fragment."""


def banned_fragment(name: str) -> str | None:
    upper = name.upper()
    if upper == GIT_BASH_NAME:
        return None
    return next((fragment for fragment in BANNED_FRAGMENTS if fragment in upper), None)


def parse_keep_names(raw: Iterable[str]) -> frozenset[str]:
    """Validate `settings.toml [environment] keep`. Raises `KeepListRefused` naming the first
    bad name. Toolchain names such as `JAVA_HOME` go here, never into `KEEP_NAMES`."""
    names: set[str] = set()
    for name in raw:
        if not _ENV_NAME.fullmatch(name):
            raise KeepListRefused(f"{name!r} is not an environment variable name")
        fragment = banned_fragment(name)
        if fragment is not None:
            raise KeepListRefused(f"{name!r} carries the banned fragment {fragment!r}")
        names.add(name.upper())
    return frozenset(names)


def read_keep_names(settings_toml: Path) -> frozenset[str]:
    """`[environment] keep` from `settings_toml`. Never raises: a missing or unreadable file,
    a missing section and each bad name give nothing."""
    try:
        document = tomllib.loads(settings_toml.read_text(encoding="utf-8"))
    except OSError, UnicodeDecodeError, tomllib.TOMLDecodeError:
        return frozenset()
    section = document.get("environment")
    keep = cast("dict[str, object]", section).get("keep") if isinstance(section, dict) else None
    if not isinstance(keep, list):
        return frozenset()
    names: set[str] = set()
    for name in cast("list[object]", keep):
        if not isinstance(name, str):
            continue
        try:
            names |= parse_keep_names([name])
        except KeepListRefused:
            continue
    return frozenset(names)


def scrub_process_env(
    environ: MutableMapping[str, str], extra_keep: frozenset[str] = frozenset()
) -> tuple[str, ...]:
    """Delete every variable whose name is not in `KEEP_NAMES | extra_keep`. Returns the removed
    names, sorted, never their values. A second call removes nothing and returns ()."""
    keep = {name.upper() for name in KEEP_NAMES | extra_keep}
    removed = sorted(name for name in environ if name.upper() not in keep)
    for name in removed:
        del environ[name]
    return tuple(removed)
