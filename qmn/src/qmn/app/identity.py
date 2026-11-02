"""Who this node is: its machine id plus an install id minted at first start (Part C AD-305).

The install id is 128 random bits, written as 26 lowercase base-32 characters; the node tag is
its first 8, the tag every order of this node will carry. Beside it the volume keeps the machine
fingerprint it was minted on: a SHA-256 of Windows' ``MachineGuid`` or Linux's ``/etc/machine-id``,
so the raw id never leaves the machine in an answer.

Every start compares the fingerprint. A different one means the volume was moved or copied, and
the node refuses all trading until he says on its card that it is the same node
(``confirm_same_node``), which binds the identity to this machine. A machine whose id cannot be
read counts as a different machine, so a copy can never pass by hiding its id.
"""

from __future__ import annotations

import base64
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from qmn.app.store import IdentityRow, Json, Store

__all__ = [
    "INSTALL_ID_BYTES",
    "LINUX_MACHINE_ID",
    "TAG_LENGTH",
    "Standing",
    "establish",
    "fingerprint_of",
    "install_id_of",
    "machine_fingerprint",
]

TAG_LENGTH: Final = 8
INSTALL_ID_BYTES: Final = 16
LINUX_MACHINE_ID: Final = (Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id"))
_WINDOWS_KEY: Final = r"SOFTWARE\Microsoft\Cryptography"


def install_id_of(random: bytes) -> str:
    """``INSTALL_ID_BYTES`` random bytes as 26 lowercase base-32 characters."""
    return base64.b32encode(random).decode("ascii").rstrip("=").lower()


def fingerprint_of(machine_id: str) -> str:
    return hashlib.sha256(machine_id.strip().lower().encode("utf-8")).hexdigest()


def machine_fingerprint() -> str | None:
    """This machine's fingerprint, or ``None`` when its id cannot be read."""
    if sys.platform == "win32":
        import winreg  # noqa: PLC0415 - Windows only

        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, _WINDOWS_KEY, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY
            ) as key:
                value, _ = winreg.QueryValueEx(key, "MachineGuid")
        except OSError:
            return None
        return fingerprint_of(str(value)) if value else None
    for path in LINUX_MACHINE_ID:
        try:
            text = path.read_text(encoding="ascii").strip()
        except OSError:
            continue
        if text:
            return fingerprint_of(text)
    return None


@dataclass(frozen=True, slots=True)
class Standing:
    """The minted identity against the machine the node runs on now."""

    row: IdentityRow
    here: str | None

    @property
    def install_id(self) -> str:
        return self.row.install_id

    @property
    def tag(self) -> str:
        return self.row.install_id[:TAG_LENGTH]

    @property
    def mismatch(self) -> bool:
        return self.here is None or self.row.fingerprint != self.here

    def document(self) -> dict[str, Json]:
        return {
            "install_id": self.install_id,
            "tag": self.tag,
            "machine_fingerprint": self.row.fingerprint,
            "minted_at_ns": self.row.minted_at_ns,
            "mismatch": self.mismatch,
        }


def establish(store: Store, *, install_id: str, here: str | None, now_ns: int) -> Standing:
    """Keep ``install_id`` as the identity on first start, or read the one kept; compare it
    with ``here``."""
    kept = store.identity()
    if kept is None:
        kept = store.mint_identity(IdentityRow(install_id, here, now_ns))
    return Standing(kept, here)
