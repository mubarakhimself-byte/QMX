"""Resolve a credential bundle only when a connection is opened, and file it by its scope.

A credential is `read` only when its probe proves it cannot trade; it is then stored under
`qmx/read/<connection>` and replicates like a declared tool key. A data-provider key is filed
under `qmx/data/<connection>`. A key whose probe finds a live account it can trade is stored
nowhere: the row reads `needs_you` and the key belongs on a trading server (AD-28, AD-67,
ruling 135). An OAuth pair is never a vault entry: its home writes it into its own key store,
which on This PC is Credential Manager.
"""

import json
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import dataclass
from typing import Literal, Protocol, cast

import keyring
from keyring.errors import PasswordDeleteError

READ_PREFIX = "qmx/read/"
DATA_PREFIX = "qmx/data/"
FILED_PREFIXES = (READ_PREFIX, DATA_PREFIX)
CTRADER_CLIENT_ID = "qmx/ctrader-client-id"
CTRADER_CLIENT_SECRET = "qmx/ctrader-client-secret"  # noqa: S105 - an entry name, not a secret
CTRADER_APP = "qmx/read/ctrader-app"
"""The read app's id and secret as one static entry, which the vault seals for the server."""
THIS_PC = "pc"
"""This PC's place name, and a connection's home when he names no other (engine AD-67, AD-72)."""
CTRADER_TOKENS = "qmx/token/ctrader-app"
"""The grant's pair, only in its home's own key store. The vault refuses any name with `token`."""


class SecretStore(Protocol):
    def get_password(self, service: str, username: str) -> str | None: ...
    def set_password(self, service: str, username: str, password: str) -> None: ...
    def delete_password(self, service: str, username: str) -> None: ...


class KeyStore(Protocol):
    """A home's own store for secrets that never replicate, read and written by name."""

    def read(self, name: str) -> str | None: ...
    def replace(self, name: str, value: str) -> None: ...
    def delete(self, name: str) -> None: ...


class CredentialManager:
    """This PC's key store: Windows Credential Manager through keyring, each entry under its
    `qmx/*` name with the name minus `qmx/` as its user name. No value is printed or logged."""

    def __init__(self, store: SecretStore | None = None) -> None:
        self._store = store

    def read(self, name: str) -> str | None:
        return _store(self._store).get_password(name, name.removeprefix("qmx/"))

    def replace(self, name: str, value: str) -> None:
        _store(self._store).set_password(name, name.removeprefix("qmx/"), value)

    def delete(self, name: str) -> None:
        with suppress(PasswordDeleteError):
            _store(self._store).delete_password(name, name.removeprefix("qmx/"))


class Held(Protocol):
    @property
    def password(self) -> str: ...


class TargetStore(SecretStore, Protocol):
    def get_credential(self, service: str, username: str | None) -> Held | None: ...


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
        return Filing(
            connection_id, old_reference, False, "needs_you", "No stored entry to re-file."
        )
    reference = filed_reference(connection_id, kind)
    secrets.set_password(reference, reference.removeprefix("qmx/"), raw)
    with suppress(PasswordDeleteError):
        secrets.delete_password(old_reference, old_reference.removeprefix("qmx/"))
    return Filing(connection_id, reference, True, "ok")


@dataclass(frozen=True, slots=True)
class Joined:
    """What the cTrader app copy did. `changed` means the vault copy must be carried again."""

    word: Literal["ok", "needs_you"]
    changed: bool
    reason: str = ""


def join_ctrader_app(store: TargetStore | None = None) -> Joined:
    """Copy his two typed entries into `qmx/read/ctrader-app` as `{clientId, clientSecret}`.

    Each entry is read by its target name, whatever user name it was saved under, and both are
    left where he typed them. A run whose copy already matches writes nothing, so it is safe to
    run before every sign-in. No value is printed or returned.
    """
    secrets = cast(TargetStore, keyring) if store is None else store
    found: dict[str, str] = {}
    for name in (CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET):
        held = secrets.get_credential(name, None)
        value = "" if held is None else (held.password or "").strip()
        if not value:
            return Joined("needs_you", False, f"{name} is not in Credential Manager")
        found[name] = value
    joined = json.dumps(
        {"clientId": found[CTRADER_CLIENT_ID], "clientSecret": found[CTRADER_CLIENT_SECRET]},
        sort_keys=True,
    )
    user = CTRADER_APP.removeprefix("qmx/")
    if secrets.get_password(CTRADER_APP, user) == joined:
        return Joined("ok", False)
    secrets.set_password(CTRADER_APP, user, joined)
    return Joined("ok", True)


if __name__ == "__main__":
    import sys

    done = join_ctrader_app()
    if done.word != "ok":
        print(f"{CTRADER_APP}: {done.reason}")
        sys.exit(1)
    print(f"{CTRADER_APP}: {'written' if done.changed else 'already current'}")
