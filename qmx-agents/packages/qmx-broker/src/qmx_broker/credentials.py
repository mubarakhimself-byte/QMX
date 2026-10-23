"""Resolve a credential bundle only when a connection is opened, and file it by its scope.

A credential is `read` only when its probe proves it cannot trade; it is then stored under
`qmx/read/<connection>` and replicates like a declared tool key. A data-provider key is filed
under `qmx/data/<connection>`. A key whose probe finds a live account it can trade is stored
nowhere: the row reads `needs_you` and the key belongs on a trading server (AD-28, AD-67,
ruling 135).
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Protocol, cast

import keyring
from keyring.errors import PasswordDeleteError

READ_PREFIX = "qmx/read/"
DATA_PREFIX = "qmx/data/"
FILED_PREFIXES = (READ_PREFIX, DATA_PREFIX)


class SecretStore(Protocol):
    def get_password(self, service: str, username: str) -> str | None: ...
    def set_password(self, service: str, username: str, password: str) -> None: ...
    def delete_password(self, service: str, username: str) -> None: ...


@dataclass(frozen=True, slots=True)
class Filing:
    """What a save did with one connection's secret, and the word its row reads."""

    connection: str
    reference: str
    stored: bool
    word: Literal["ok", "needs_you"]
    reason: str = ""


def _store(store: SecretStore | None) -> SecretStore:
    return cast(SecretStore, keyring) if store is None else store


def credentials(reference: str) -> dict[str, str]:
    if not reference.startswith("qmx/"):
        raise ValueError("Use a qmx/* Credential Manager reference")
    secret = keyring.get_password(reference, reference.removeprefix("qmx/"))
    if secret is None:
        raise ValueError(
            f"Missing Credential Manager entry {reference}; configure it before connecting"
        )
    try:
        value: object = json.loads(secret)
        if (
            not isinstance(value, dict)
            or not value
            or any(
                not isinstance(key, str) or not isinstance(item, str) or not item
                for key, item in cast("dict[object, object]", value).items()
            )
        ):
            raise ValueError
    except (ValueError, TypeError) as error:
        raise ValueError(
            "Credential Manager entry must be a JSON object of nonempty strings"
        ) from error
    return cast("dict[str, str]", value)


def filed_reference(connection_id: str, kind: str = "broker") -> str:
    """The replicable name a static read or data key is filed under."""
    prefix = DATA_PREFIX if kind == "data" else READ_PREFIX
    return f"{prefix}{connection_id}"


def file_credential(
    connection_id: str,
    values: Mapping[str, str],
    *,
    kind: str = "broker",
    can_trade_live: bool = False,
    store: SecretStore | None = None,
) -> Filing:
    """File one key by what its probe found; a key that can trade live money is kept nowhere."""
    if can_trade_live:
        return Filing(
            connection_id,
            "",
            False,
            "needs_you",
            "This key can trade a live account; it belongs on a trading server.",
        )
    reference = filed_reference(connection_id, kind)
    _store(store).set_password(reference, reference.removeprefix("qmx/"), json.dumps(dict(values)))
    return Filing(connection_id, reference, True, "ok")


def refile(
    old_reference: str,
    connection_id: str,
    *,
    kind: str = "broker",
    store: SecretStore | None = None,
) -> Filing:
    """Move a key typed under an unreplicable name to `qmx/read/*` or `qmx/data/*`."""
    secrets = _store(store)
    raw = secrets.get_password(old_reference, old_reference.removeprefix("qmx/"))
    if raw is None:
        return Filing(connection_id, old_reference, False, "needs_you", "No stored entry to re-file.")
    reference = filed_reference(connection_id, kind)
    secrets.set_password(reference, reference.removeprefix("qmx/"), raw)
    try:
        secrets.delete_password(old_reference, old_reference.removeprefix("qmx/"))
    except PasswordDeleteError:
        pass
    return Filing(connection_id, reference, True, "ok")
