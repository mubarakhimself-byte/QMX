"""Secret storage per OS, and the only functions that build a child process env.

Backends (Codex `auto` design): OS keyring by default (Windows Credential Manager,
macOS Keychain, Linux Secret Service), `ephemeral` for tests/CI, and an age-encrypted
file whose key sits in the keyring for headless Linux. Labels keep the existing
`qmx/<name>` convention.

Reach is a type, not a convention (model.HostSecretRef vs OperatorSecretRef):
`host_env` accepts only HostSecretRef, so broker credentials, the control token and the
operator key cannot be injected into an engine host by any code that type-checks.

Two envs, both allow-lists (never os.environ minus a deny-list):
- host_env: what an engine host process gets. Platform basics + the one provider key
  its route needs (OpenAI) or CLAUDE_CONFIG_DIR + isolation flags (Claude). Because the
  host is the launcher of the Claude CLI, the SDK's env merge can only merge this clean
  env (fixes HOW Gotcha 6 without a custom transport).
- tool_env: what Bash/PowerShell commands, hook scripts and MCP stdio servers get.
  Platform basics only. Never a provider key, never QMX_* or ANTHROPIC_*/OPENAI_*.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from qma2.model import HostSecretRef, OperatorSecretRef, Route


class Backend(StrEnum):
    KEYRING = "keyring"
    EPHEMERAL = "ephemeral"
    AGE_FILE = "age_file"


class SecretStore(Protocol):
    def get(self, ref: HostSecretRef | OperatorSecretRef) -> str | None: ...
    def set(self, ref: HostSecretRef | OperatorSecretRef, value: str) -> None: ...
    def delete(self, ref: HostSecretRef | OperatorSecretRef) -> None: ...
    def list(self, prefix: str) -> list[str]: ...


def open_store(backend: Backend, home: Path) -> SecretStore:
    raise NotImplementedError


PLATFORM_BASICS: frozenset[str] = frozenset(
    {
        "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP",
        "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA",
        "HOME", "USER", "LANG", "LC_ALL", "TERM", "TMPDIR", "SHELL",
    }
)


def host_env(route: Route, store: SecretStore, base: Mapping[str, str], claude_home: Path, trace_dir: Path) -> dict[str, str]:
    """Allow-listed env for one engine host.

    # TODO pseudocode
    # env = {k: v for k, v in base.items() if k in PLATFORM_BASICS}
    # match route:
    #   ClaudeRoute: env |= {CLAUDE_CONFIG_DIR: claude_home,
    #                        ENABLE_CLAUDEAI_MCP_SERVERS: "false",
    #                        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1",
    #                        OTEL exporter -> local file under trace_dir}
    #                (no key: the operator's /login lives in claude_home)
    #   OpenAIRoute: env["QMX_PROVIDER_KEY"] = store.get(route.account.key_ref | access_ref)
    #                env["OPENAI_AGENTS_DISABLE_TRACING"] = "0"  # host installs local processor
    # assert not any(k.startswith(("ANTHROPIC_", "CLAUDE_CODE_USE_")) for k in env)
    """
    raise NotImplementedError


def tool_env(base: Mapping[str, str]) -> dict[str, str]:
    """Allow-listed env for every command an agent or hook runs."""
    raise NotImplementedError


def redact(text: str) -> str:
    """Codex sanitizer port: mask anything that looks like a key or bearer token, and any
    value currently held in the store (exact-match), before logs, traces, items, blocks."""
    raise NotImplementedError
