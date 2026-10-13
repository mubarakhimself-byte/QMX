"""SecretStore: two tiers, three backends, one env allow-list.

Tiers (the money answer, design.md tension 1):
- REACHABLE: OS keyring (`qmx/<provider>/<name>`), as today. Holds model-provider keys and the
  ChatGPT OAuth tokens. A same-user Bash can read these; the harm is cost or privacy, not money.
- SEALED: an age-style file `<home>/qma2/sealed.json` encrypted with a key derived from the
  operator passphrase. Decrypted only in the control process after `OperatorAuth.login`, held
  in memory, never written back in clear. Trading-scope broker credentials go here or nowhere.
  A same-user Bash can read the file and cannot decrypt it. That is the real guarantee.

Backends: `keyring` (default), `ephemeral` (tests/CI; dict), `file_sealed` (SEALED tier).
Linux without Secret Service: REACHABLE falls back to the sealed file too (then the operator
must be logged in for provider keys; stated cost).

Claude: nothing is stored. The subscription lives in `claude-home/`; QMX never reads it
(H1 fact 4). `scrub_env` removes every ANTHROPIC_* / CLAUDE_CODE_USE_* / OPENAI_* variable
from the child env so an inherited API key can never route a turn (Gotcha 6).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Protocol

from qma2.types import OperatorProof


class Tier(StrEnum):
    REACHABLE = "reachable"
    SEALED = "sealed"


class SecretBackend(Protocol):
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...
    def delete(self, key: str) -> None: ...
    def list(self, prefix: str) -> Sequence[str]: ...


class SecretStore:
    def __init__(self, reachable: SecretBackend, sealed: SecretBackend) -> None:
        raise NotImplementedError

    def get(self, ref: str) -> str | None:
        """`ref` is "qmx/<provider>/<name>"; tier is resolved from a fixed prefix table:
        qmx/broker/* → SEALED (raises `SealedLocked` until the operator logs in), else REACHABLE."""
        raise NotImplementedError

    def put(self, ref: str, value: str, proof: OperatorProof) -> None:
        """Only the operator writes secrets. Values never appear in logs (redact()) or settings
        (ControlService._no_secrets keeps settings clean; qma2 Settings has no secret fields)."""
        raise NotImplementedError

    def unseal(self, passphrase: str) -> None:
        """Derive the key, decrypt into memory. Called by OperatorAuth.login."""
        raise NotImplementedError

    def redact(self, text: str) -> str:
        """Replace every known secret value with ***; used by tool result previews and traces."""
        raise NotImplementedError


ENV_ALLOW_BASE: tuple[str, ...] = (
    "PATH", "HOME", "USERPROFILE", "TEMP", "TMP", "SYSTEMROOT", "LANG", "TZ", "TERM",
    "APPDATA", "LOCALAPPDATA", "COMSPEC", "PATHEXT",
)
ENV_DENY_PREFIXES: tuple[str, ...] = ("ANTHROPIC_", "CLAUDE_CODE_USE_", "OPENAI_", "QMX_")


def scrub_env(parent: Mapping[str, str], extra_allow: Sequence[str] = ()) -> dict[str, str]:
    """Pure: allow-list the parent env. The result is what every engine child starts from,
    before per-provider injection (`Launcher.spawn_env`)."""
    raise NotImplementedError
