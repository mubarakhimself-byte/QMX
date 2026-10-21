"""The keys, entered once and carried as ciphertext (H11, H13, H33; AD-12 two hosts).

Keys stay where they are today: Windows Credential Manager, under `qmx/*`. This module never
moves them. What it moves is a sealed copy:

- Every replicable entry is encrypted under the vault's public key and published as ciphertext.
  The private key never leaves the machine the key was typed on, so the ciphertext on the server
  is useful to exactly one reader: the vault that sealed it. A node keeps the ciphertext as its
  inventory and asks the vault for a value over the tailnet, holding the answer in `KeyCache`.
- Broker credentials are never replicable. `install` refuses to seal one, so the rule is held by
  the code rather than by the caller's memory.
- Deletion publishes a tombstone. A node that reads a tombstone refuses the name from then on,
  which is what makes "a deletion is refused within one sync" true even if a stale value is still
  in a cache somewhere.

The public-key half is X25519, HKDF-SHA256 and AES-256-GCM: an ephemeral key per entry, the
vault's public key as the recipient, the entry's name as associated data so a ciphertext cannot
be relabelled into another key's slot.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Final, Protocol

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

SALT: Final = b"qmx-vault-v1"
"""The KDF's salt. Fixed, because the ephemeral key is already unique per entry."""
NONCE: Final = 12
"""AES-GCM's nonce length, the one size every implementation agrees on."""
BROKER_MARKS: Final[tuple[str, ...]] = ("broker",)
"""A keyring name holding a broker credential. Never replicated, in any spelling."""


class NotReplicable(PermissionError):
    """This entry may not leave the machine it was entered on."""


class MissingKey(PermissionError):
    """The vault holds no live value for this name."""


class WrongKey(PermissionError):
    """The ciphertext was sealed for another vault, or the name was relabelled."""


def is_replicable(name: str) -> bool:
    """False for a broker credential, named either as `qmx/broker/...`, `qmx/brokers`, or with
    `broker` as any segment. True for everything else, which is a default about names only: a
    caller still passes `replicable=False` for a key it wants kept local."""
    segments = [segment for segment in name.strip().lower().split("/") if segment]
    return not any(
        segment in BROKER_MARKS or segment.startswith("broker-") or segment.startswith("broker_")
        for segment in segments
    )


class VaultKey:
    """The vault's key pair. `seal` needs only the public half, which every machine may hold;
    `open` needs the private half, which stays with the vault."""

    def __init__(self, private: X25519PrivateKey | None = None) -> None:
        self._private = private

    @classmethod
    def generate(cls) -> VaultKey:
        return cls(X25519PrivateKey.generate())

    @classmethod
    def from_private_bytes(cls, raw: bytes) -> VaultKey:
        return cls(X25519PrivateKey.from_private_bytes(raw))

    def private_bytes(self) -> bytes:
        """The 32 bytes to keep in Credential Manager. Nothing else in this module writes it."""
        if self._private is None:
            raise WrongKey("this is a public-only vault key")
        from cryptography.hazmat.primitives import serialization

        return self._private.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def public_bytes(self) -> bytes:
        if self._private is not None:
            from cryptography.hazmat.primitives import serialization

            return self._private.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        raise WrongKey("this vault key has no public half")

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
        except Exception as error:  # noqa: BLE001  (the AEAD's own exception hierarchy varies)
            raise WrongKey(f"{name} was not sealed for this vault") from error

    def _recipient(self) -> X25519PublicKey:
        private = self._private
        if private is not None:
            return private.public_key()
        raise WrongKey("this vault key has no public half")


def _derive(shared: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=SALT, info=b"qmx-vault-entry").derive(
        shared
    )


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

    values: dict[str, str] = field(default_factory=dict)

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
    """One published entry. `fingerprint` is a rotation witness (a truncated SHA-256 of the
    value), never the value, and `deleted` is the tombstone that makes a deletion spread."""

    name: str
    replicable: bool
    sealed: bytes
    fingerprint: str
    updated_at: float
    deleted: bool = False

    def document(self) -> dict[str, object]:
        return {
            "name": self.name,
            "replicable": self.replicable,
            "sealed": base64.b64encode(self.sealed).decode("ascii"),
            "fingerprint": self.fingerprint,
            "updated_at": float(self.updated_at),
            "deleted": self.deleted,
        }

    @classmethod
    def from_document(cls, document: object) -> VaultEntry | None:
        """Parse one entry off the tailnet. A row that does not fit is dropped, not raised."""
        if not isinstance(document, dict):
            return None
        name = document.get("name")
        if not isinstance(name, str) or not name:
            return None
        try:
            sealed = base64.b64decode(str(document.get("sealed", "")), validate=True)
        except (ValueError, TypeError):
            return None
        updated_at = document.get("updated_at")
        if not isinstance(updated_at, (int, float)):
            return None
        return cls(
            name=name,
            replicable=bool(document.get("replicable", False)),
            sealed=sealed,
            fingerprint=str(document.get("fingerprint", "")),
            updated_at=float(updated_at),
            deleted=bool(document.get("deleted", False)),
        )


class Vault:
    """The machine the keys were entered on. It reads a value only to seal it or to answer a
    pass-bearing request; nothing here logs, formats or returns a value to a caller that is not
    the relay."""

    def __init__(
        self,
        key: VaultKey,
        source: Source,
        *,
        clock: Callable[[], float] = time.time,
        replicable: Callable[[str], bool] = is_replicable,
    ) -> None:
        self.key = key
        self.source = source
        self.clock = clock
        self.replicable = replicable
        self._entries: dict[str, VaultEntry] = {}
        self._fingerprints: dict[str, str] = {}
        self._deleted: set[str] = set()

    @property
    def public_key(self) -> bytes:
        return self.key.public_bytes()

    def public_key_text(self) -> str:
        return base64.b64encode(self.public_key).decode("ascii")

    def install(self, name: str, value: str, *, replicable: bool | None = None) -> VaultEntry:
        """Enter or rotate one value. `replicable` defaults to the name's own answer, and a
        broker credential's is False whatever the caller says."""
        allowed = is_replicable(name) and (self.replicable(name) if replicable is None else replicable)
        self.source.write(name, value)
        fingerprint = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
        entry = VaultEntry(
            name=name,
            replicable=allowed,
            sealed=self.key.seal(name, value.encode("utf-8")) if allowed else b"",
            fingerprint=fingerprint,
            updated_at=float(self.clock()),
        )
        self._entries[name] = entry
        self._fingerprints[name] = fingerprint
        self._deleted.discard(name)
        return entry

    def delete(self, name: str) -> VaultEntry:
        """Remove the value here and publish a tombstone, so a node stops serving the name even
        when its copy of the old ciphertext is still on disk."""
        self.source.delete(name)
        self._deleted.add(name)
        entry = VaultEntry(
            name=name,
            replicable=self._entries.get(name, VaultEntry(name, False, b"", "", 0.0)).replicable,
            sealed=b"",
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
        """Every replicable entry and every tombstone, newest first by name. This is the whole
        sync payload; a non-replicable entry is never in it, whether or not it was installed."""
        published = [entry for entry in self._entries.values() if entry.replicable or entry.deleted]
        return tuple(sorted(published, key=lambda entry: entry.name))

    def rotate(self, name: str) -> str:
        """Import a value from the source into the published set, for a key that was entered
        before this vault existed. Returns the fingerprint; no value crosses the return."""
        entry = self.install(name, self.read(name))
        return entry.fingerprint

    def sync_document(self) -> dict[str, object]:
        """The one message a node reads: the entries, and the public key it may check them
        against. `key` is here so a node can refuse a payload sealed for another vault."""
        return {
            "key": self.public_key_text(),
            "entries": [entry.document() for entry in self.entries()],
        }


class VaultStore:
    """The node's copy: ciphertext and tombstones, never plaintext. Newest `updated_at` wins, so
    a rotation and a deletion each take effect on the sync that carries them and a replayed old
    message cannot undo one."""

    def __init__(self, public_key: bytes = b"", *, clock: Callable[[], float] = time.time) -> None:
        self.public_key = public_key
        self.clock = clock
        self._entries: dict[str, VaultEntry] = {}
        self.received = 0

    def sync(self, document: object) -> int:
        """Take one published payload. Returns how many entries were newer; a refusal is a stale
        message, which the next sync fixes."""
        if not isinstance(document, dict):
            return 0
        key = document.get("key")
        if isinstance(key, str) and key:
            try:
                self.public_key = base64.b64decode(key)
            except (ValueError, TypeError):
                return 0
        taken = 0
        for row in document.get("entries", []):  # type: ignore[union-attr]
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

    def sealed(self, name: str) -> bytes:
        entry = self._entries.get(name)
        if entry is None or entry.deleted or not entry.sealed:
            raise MissingKey(f"{name} is not in the vault")
        return entry.sealed

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(name for name, entry in self._entries.items() if not entry.deleted))

    def tombstones(self) -> tuple[str, ...]:
        return tuple(sorted(name for name, entry in self._entries.items() if entry.deleted))


@dataclass(frozen=True)
class CachedKey:
    """One plaintext value in a node's memory, with the deadline it was granted for."""

    name: str
    value: str
    expires_at: float


class KeyCache:
    """The node's memory of values it was granted. It answers without the vault and without the
    Hub, which is what keeps in-flight runs calling while both are stopped: a cache miss is a
    wait, a hit is a key. The value is never written to disk and never formatted into a log."""

    def __init__(self, *, clock: Callable[[], float] = time.time) -> None:
        self.clock = clock
        self._held: dict[str, CachedKey] = {}

    def put(self, name: str, value: str, ttl_s: float) -> None:
        self._held[name] = CachedKey(name, value, float(self.clock()) + float(ttl_s))

    def get(self, name: str) -> str | None:
        held = self._held.get(name)
        if held is None:
            return None
        if float(self.clock()) >= held.expires_at:
            del self._held[name]
            return None
        return held.value

    def drop(self, name: str) -> None:
        self._held.pop(name, None)

    def names(self) -> tuple[str, ...]:
        """The names held, never their values. For the usage page and for a lane's log."""
        return tuple(sorted(name for name in self._held if self.get(name) is not None))

    def clear(self) -> None:
        self._held.clear()

    def __len__(self) -> int:
        return len([name for name in self._held if self.get(name) is not None])


def install_from_document(
    vault: Vault, document: object, *, value_of: Callable[[str], str | None] | None = None
) -> int:
    """Publish every entry a running vault already holds, for a vault built after the keys were
    entered. Only names whose value the source can still answer for are installed."""
    if not isinstance(document, dict):
        return 0
    installed = 0
    for row in document.get("names", []):  # type: ignore[union-attr]
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
