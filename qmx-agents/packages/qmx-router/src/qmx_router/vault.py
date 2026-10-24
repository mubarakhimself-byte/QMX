"""The keys, entered once and carried as ciphertext each machine can open for itself (H11, H13,
H33; AD-28 two hosts, ruling 135).

Keys stay where they are today: Windows Credential Manager, under `qmx/*`. This module never
moves them. What it moves is a sealed copy:

- One replication is an allow-list of static keys, never a default: a model-provider row,
  `qmx/read/*` or `qmx/data/*`. A trade key, an OAuth token, a broker credential, the backup
  payload key and the pairing key are not vault entries at all, so they are never sealed and a
  deletion spreads no tombstone for them.
- Every receiving machine has its own key pair. `install` seals the value once per machine, and
  each machine opens its own share with the private key in its own key file. No machine asks
  another for a value: the PC can be off and the server still serves a model call.
- Deletion of a vault entry publishes a tombstone, so a stale ciphertext is refused from the sync
  that carries it. Deletion of anything else is local and silent.

The seal format is unchanged: X25519, HKDF-SHA256 and AES-256-GCM, an ephemeral key per entry with
the vault's public key as the recipient and the entry's name as associated data, so a ciphertext
cannot be relabelled into another key's slot.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Protocol, cast

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

SALT: Final = b"qmx-vault-v1"
"""The KDF's salt. Fixed, because the ephemeral key is already unique per entry."""
NONCE: Final = 12
"""AES-GCM's nonce length, the one size every implementation agrees on."""
PRIVATE_BYTES: Final = 32
"""An X25519 private key's length, which is also the whole key file."""
PROVIDERS: Final[tuple[str, ...]] = (
    "deepseek",
    "glm",
    "kimi",
    "meta",
    "minimax",
    "ollama",
    "opencode-go",
    "openrouter",
    "qwen",
)
"""The model-provider rows of `[providers]`, one `qmx/<name>` keyring entry each. A row he adds is
passed by the caller; this is the bundled set."""
STATIC_PREFIXES: Final[tuple[str, ...]] = ("qmx/read/", "qmx/data/")
"""A connection's static read or data key. The connection is the segment after the prefix."""
TOKEN_MARKS: Final[tuple[str, ...]] = ("token", "oauth", "chatgpt")
"""A name holding a token is never a static key, whatever prefix it tries to hide behind."""
KEY_FOLDER: Final = ".qmx"
"""The folder each machine keeps its own private key in, inside its home."""
KEY_FILE: Final = "vault.key"
"""The file name the plan names: `<home>/.qmx/vault.key`, mode 0600, owner only."""


class NotReplicable(PermissionError):
    """This entry may not leave the machine it was entered on."""


class MissingKey(PermissionError):
    """The vault holds no live value for this name."""


class WrongKey(PermissionError):
    """The ciphertext was sealed for another vault, or the name was relabelled."""


class VaultUnavailable(RuntimeError):
    """This machine has no key file, so it cannot open anything. The code names the machine, as
    a job reports it: `vault:unavailable:contabo`."""

    def __init__(self, machine: str) -> None:
        super().__init__(f"vault:unavailable:{machine}")
        self.machine = machine


def is_replicable(name: str, *, providers: Iterable[str] = PROVIDERS) -> bool:
    """Whether `name` is a vault entry: an allow-list of a model-provider row, `qmx/read/*` or
    `qmx/data/*`, and nothing else. A token name is refused even under a static prefix, and a
    trade key, a broker credential or the backup payload key is refused because it is on no list.
    """
    folded = name.strip().lower()
    if not folded.startswith("qmx/"):
        return False
    tail = folded.removeprefix("qmx/")
    if any(mark in tail for mark in TOKEN_MARKS):
        return False
    if tail in providers:
        return True
    return any(
        folded.startswith(prefix) and len(folded) > len(prefix) for prefix in STATIC_PREFIXES
    )


class VaultKey:
    """One machine's key pair. `seal` needs only the public half, which every machine holds;
    `open` needs the private half, which stays with the machine that owns it."""

    def __init__(self, private: X25519PrivateKey) -> None:
        self._private: X25519PrivateKey | None = private
        self._public: X25519PublicKey | None = None

    @classmethod
    def generate(cls) -> VaultKey:
        return cls(X25519PrivateKey.generate())

    @classmethod
    def from_private_bytes(cls, raw: bytes) -> VaultKey:
        return cls(X25519PrivateKey.from_private_bytes(raw))

    @classmethod
    def from_public_bytes(cls, raw: bytes) -> VaultKey:
        """Another machine's public half. It can seal for that machine and cannot open."""
        key = cls.__new__(cls)
        key._private = None
        key._public = X25519PublicKey.from_public_bytes(raw)
        return key

    def private_bytes(self) -> bytes:
        """The 32 bytes to keep in this machine's key file. Nothing else writes them."""
        if self._private is None:
            raise WrongKey("this is a public-only vault key")
        return self._private.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def public_bytes(self) -> bytes:
        if self._private is not None:
            return self._private.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        if self._public is None:
            raise WrongKey("this vault key has no public half")
        return self._public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

    def seal(self, name: str, value: bytes) -> bytes:
        """Ciphertext for `name`: ephemeral public key, nonce, then the sealed bytes."""
        recipient = self._recipient()
        ephemeral = X25519PrivateKey.generate()
        shared = ephemeral.exchange(recipient)
        derived = _derive(shared)
        nonce = os.urandom(NONCE)
        sealed = AESGCM(derived).encrypt(nonce, value, name.encode("utf-8"))
        ephemeral_public = ephemeral.public_key().public_bytes_raw()
        return ephemeral_public + nonce + sealed

    def open(self, name: str, sealed: bytes) -> bytes:
        if self._private is None:
            raise WrongKey("this vault key cannot open a seal")
        if len(sealed) <= 32 + NONCE:
            raise WrongKey("the ciphertext is shorter than its header")
        ephemeral_public, nonce, body = sealed[:32], sealed[32 : 32 + NONCE], sealed[32 + NONCE :]
        try:
            shared = self._private.exchange(X25519PublicKey.from_public_bytes(ephemeral_public))
        except ValueError as error:
            raise WrongKey(f"the ciphertext carries no usable key: {error}") from error
        try:
            return AESGCM(_derive(shared)).decrypt(nonce, body, name.encode("utf-8"))
        except Exception as error:
            raise WrongKey(f"{name} was not sealed for this vault") from error

    def _recipient(self) -> X25519PublicKey:
        if self._private is not None:
            return self._private.public_key()
        if self._public is not None:
            return self._public
        raise WrongKey("this vault key has no public half")


def _derive(shared: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=SALT, info=b"qmx-vault-entry").derive(
        shared
    )


def key_file(home: Path) -> Path:
    """`<home>/.qmx/vault.key`: the one file a machine's private key lives in."""
    return home / KEY_FOLDER / KEY_FILE


def write_machine_key(home: Path, key: VaultKey) -> Path:
    """Write this machine's private key where only its user reads it: 0600 in a 0700 folder. The
    server's file is written by its setup as `qmx`, which is the only reader it needs."""
    folder = home / KEY_FOLDER
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = folder / KEY_FILE
    path.write_bytes(key.private_bytes())
    path.chmod(0o600)
    return path


def read_machine_key(home: Path, machine: str) -> VaultKey:
    """This machine's key from its key file, or `vault:unavailable:<machine>`: a job that cannot
    open a key says which machine is missing one rather than waiting on another host."""
    try:
        raw = key_file(home).read_bytes()
    except OSError as error:
        raise VaultUnavailable(machine) from error
    if len(raw) != PRIVATE_BYTES:
        raise VaultUnavailable(machine)
    return VaultKey.from_private_bytes(raw)


class Source(Protocol):
    """Where a vault reads values. The real one is Credential Manager by name; a lane passes a
    `MemorySource`, so no test or lane ever has to touch a real key."""

    def names(self) -> Iterable[str]: ...

    def read(self, name: str) -> str | None: ...

    def write(self, name: str, value: str) -> None: ...

    def delete(self, name: str) -> None: ...


@dataclass
class MemorySource:
    """A stand-in for Credential Manager, for lanes and tests only."""

    values: dict[str, str] = field(default_factory=lambda: {})

    def names(self) -> Iterable[str]:
        return tuple(self.values)

    def read(self, name: str) -> str | None:
        return self.values.get(name)

    def write(self, name: str, value: str) -> None:
        self.values[name] = value

    def delete(self, name: str) -> None:
        self.values.pop(name, None)


@dataclass(frozen=True)
class VaultEntry:
    """One published entry. `sealed` carries one ciphertext per receiving machine, `fingerprint` is
    a rotation witness (a truncated SHA-256 of the value), never the value, and `deleted` is the
    tombstone that makes a deletion of a vault entry spread."""

    name: str
    replicable: bool
    sealed: Mapping[str, bytes]
    fingerprint: str
    updated_at: float
    deleted: bool = False

    def document(self) -> dict[str, object]:
        return {
            "name": self.name,
            "replicable": self.replicable,
            "sealed": {
                machine: base64.b64encode(part).decode("ascii")
                for machine, part in self.sealed.items()
            },
            "fingerprint": self.fingerprint,
            "updated_at": float(self.updated_at),
            "deleted": self.deleted,
        }

    @classmethod
    def from_document(cls, document: object) -> VaultEntry | None:
        """Parse one entry off the tailnet. A row that does not fit is dropped, not raised."""
        if not isinstance(document, dict):
            return None
        data = cast("dict[str, Any]", document)
        name = data.get("name")
        if not isinstance(name, str) or not name:
            return None
        raw = data.get("sealed")
        sealed: dict[str, bytes] = {}
        if isinstance(raw, dict):
            for machine, text in cast("dict[object, object]", raw).items():
                try:
                    sealed[str(machine)] = base64.b64decode(str(text), validate=True)
                except TypeError, ValueError:
                    continue
        updated_at = data.get("updated_at")
        if not isinstance(updated_at, int | float):
            return None
        return cls(
            name=name,
            replicable=bool(data.get("replicable", False)),
            sealed=sealed,
            fingerprint=str(data.get("fingerprint", "")),
            updated_at=float(updated_at),
            deleted=bool(data.get("deleted", False)),
        )


class Vault:
    """The machine the keys were entered on. It reads a value only to seal it. It seals a copy for
    itself and for every receiving machine it holds a public key for, so no machine ever asks it
    for a value."""

    def __init__(
        self,
        key: VaultKey,
        source: Source,
        *,
        machine: str = "pc",
        peers: Mapping[str, VaultKey] | None = None,
        clock: Callable[[], float] = time.time,
        replicable: Callable[[str], bool] = is_replicable,
    ) -> None:
        self.key = key
        self.source = source
        self.machines: dict[str, VaultKey] = {machine: key, **(peers or {})}
        self.clock = clock
        self.replicable = replicable
        self._entries: dict[str, VaultEntry] = {}
        self._deleted: set[str] = set()

    @property
    def public_key(self) -> bytes:
        return self.key.public_bytes()

    def public_key_text(self) -> str:
        return base64.b64encode(self.public_key).decode("ascii")

    def install(self, name: str, value: str, *, replicable: bool | None = None) -> VaultEntry:
        """Enter or rotate one value. `replicable` defaults to the name's own answer, and a name on
        no allow-list stays local whatever the caller says: no caller can seal a trade key."""
        allowed = is_replicable(name) and (
            self.replicable(name) if replicable is None else replicable
        )
        self.source.write(name, value)
        fingerprint = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
        entry = VaultEntry(
            name=name,
            replicable=allowed,
            sealed=(
                {
                    machine: key.seal(name, value.encode("utf-8"))
                    for machine, key in self.machines.items()
                }
                if allowed
                else {}
            ),
            fingerprint=fingerprint,
            updated_at=float(self.clock()),
        )
        self._entries[name] = entry
        self._deleted.discard(name)
        return entry

    def delete(self, name: str) -> VaultEntry:
        """Remove the value here. A vault entry publishes a tombstone, so a receiving machine stops
        serving the name from the sync that carries it. Anything else, a token or a trade key,
        leaves locally and publishes nothing: it was never in the vault."""
        self.source.delete(name)
        held = self._entries.get(name)
        published = held.replicable if held is not None else is_replicable(name)
        if not published:
            return VaultEntry(
                name=name,
                replicable=False,
                sealed={},
                fingerprint="",
                updated_at=float(self.clock()),
                deleted=True,
            )
        self._deleted.add(name)
        entry = VaultEntry(
            name=name,
            replicable=True,
            sealed={},
            fingerprint="",
            updated_at=float(self.clock()),
            deleted=True,
        )
        self._entries[name] = entry
        return entry

    def read(self, name: str) -> str:
        """The value, for the relay's own use. Raises `MissingKey` for a name this vault holds
        nothing live for, which is what a revoked or deleted key looks like to the relay."""
        if name in self._deleted:
            raise MissingKey(f"{name} was deleted")
        value = self.source.read(name)
        if value is None:
            raise MissingKey(f"{name} is not in the vault")
        return value

    def entries(self) -> tuple[VaultEntry, ...]:
        """Every vault entry, a rotation and a tombstone alike, oldest name first. This is the
        whole sync payload; an entry off the allow-list is never in it, installed or not."""
        published = [entry for entry in self._entries.values() if entry.replicable]
        return tuple(sorted(published, key=lambda entry: entry.name))

    def rotate(self, name: str) -> str:
        """Import a value from the source into the published set, for a key that was entered
        before this vault existed. Returns the fingerprint; no value crosses the return."""
        entry = self.install(name, self.read(name))
        return entry.fingerprint

    def sync_document(self) -> dict[str, object]:
        """The one message a receiving machine reads: the entries and the public key of every
        machine they are sealed for, so a machine can check its own share exists."""
        return {
            "key": self.public_key_text(),
            "keys": {
                machine: as_text(key.public_bytes()) for machine, key in self.machines.items()
            },
            "entries": [entry.document() for entry in self.entries()],
        }


class VaultStore:
    """One receiving machine's copy: ciphertext and tombstones, never plaintext. Newest
    `updated_at` wins, so a rotation and a deletion each take effect on the sync that carries them
    and a replayed old message cannot undo one. It opens only its own share, with its own key."""

    def __init__(
        self, machine: str = "", public_key: bytes = b"", *, clock: Callable[[], float] = time.time
    ) -> None:
        self.machine = machine
        self.public_key = public_key
        self.clock = clock
        self._entries: dict[str, VaultEntry] = {}
        self.received = 0

    def sync(self, document: object) -> int:
        """Take one published payload. Returns how many entries were newer; a refusal is a stale
        message, which the next sync fixes."""
        if not isinstance(document, dict):
            return 0
        data = cast("dict[str, Any]", document)
        key = data.get("key")
        if isinstance(key, str) and key:
            try:
                self.public_key = base64.b64decode(key)
            except ValueError, TypeError:
                return 0
        taken = 0
        rows = data.get("entries")
        for row in cast("list[object]", rows) if isinstance(rows, list) else []:
            entry = VaultEntry.from_document(row)
            if entry is None:
                continue
            held = self._entries.get(entry.name)
            if held is not None and entry.updated_at <= held.updated_at:
                continue
            self._entries[entry.name] = entry
            taken += 1
        self.received += taken
        return taken

    def has(self, name: str) -> bool:
        """True only for a live entry: a tombstone answers False from the sync that carries it."""
        entry = self._entries.get(name)
        return entry is not None and not entry.deleted

    def entry(self, name: str) -> VaultEntry | None:
        return self._entries.get(name)

    def open(self, name: str, key: VaultKey) -> str:
        """The value, opened with this machine's own key. A share sealed for another machine, or a
        name that is not here, is refused rather than guessed at."""
        entry = self._entries.get(name)
        if entry is None or entry.deleted or not entry.sealed:
            raise MissingKey(f"{name} is not in the vault")
        share = entry.sealed.get(self.machine)
        if share is None:
            raise MissingKey(f"{name} is not sealed for {self.machine or 'this machine'}")
        return key.open(name, share).decode("utf-8")

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(name for name, entry in self._entries.items() if not entry.deleted))

    def tombstones(self) -> tuple[str, ...]:
        return tuple(sorted(name for name, entry in self._entries.items() if entry.deleted))


def install_from_document(
    vault: Vault, document: object, *, value_of: Callable[[str], str | None] | None = None
) -> int:
    """Publish every entry a running vault already holds, for a vault built after the keys were
    entered. Only names whose value the source can still answer for are installed."""
    if not isinstance(document, dict):
        return 0
    rows = cast("dict[str, Any]", document).get("names")
    installed = 0
    for row in cast("list[object]", rows) if isinstance(rows, list) else []:
        name = str(row)
        value = value_of(name) if value_of is not None else vault.source.read(name)
        if value is None:
            continue
        vault.install(name, value, replicable=is_replicable(name))
        installed += 1
    return installed


def as_text(value: bytes) -> str:
    """A public key or fingerprint, in the one spelling a file or a log uses."""
    return base64.b64encode(value).decode("ascii")


def document_of(*entries: VaultEntry) -> dict[str, object]:
    """A test's view of a sync payload: the entries alone, no key. The server sends
    `Vault.sync_document`; tests may build one of these and still exercise `VaultStore.sync`."""
    return {"entries": [entry.document() for entry in entries]}


def json_document(document: object) -> str:
    """The sync payload as text, for the tailnet route and for a lane's file."""
    return json.dumps(document, sort_keys=True)
