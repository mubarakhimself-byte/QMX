"""`settings.toml [telemetry] send_to`: where this machine's monitoring goes (design 62 E1).

One setting decides it for every sender on the machine: each chat's CLI, the engine's exporter
and Hindsight's tracing. `off` is the default and sends nothing. `this-pc` sends to OpenObserve on
this machine's loopback. Any other value names a place, whose collector is reached by that name
over the tailnet. No sender holds an address of its own.

OpenObserve on this PC takes nothing without its sign-in, so every sender sends `headers(home)`:
the ingest credential the deep-logs dialog put in the key store, as an `Authorization` header.
It goes to this PC's loopback only. A place's collector listens on the tailnet with no sign-in,
and a key never leaves this PC.
"""

from __future__ import annotations

import logging
import re
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Final, cast

LOG = logging.getLogger(__name__)

SECTION: Final = "telemetry"
OFF: Final = "off"
THIS_PC: Final = "this-pc"
THIS_PC_ENDPOINT: Final = "http://127.0.0.1:5080/api/default"
"""OpenObserve's OTLP/HTTP root on loopback, its default port and organisation. No collector runs
on This PC: a loopback network never sleeps, so nothing needs a disk queue in front of it."""
COLLECTOR_PORT: Final = 4318
"""OTLP/HTTP's registered port, where a place's collector listens."""
PLACE: Final = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")
"""A place name as a tailnet machine name: lowercase letters, digits and hyphens."""
INGEST_KEY: Final = "qmx/openobserve-ingest"
"""The key-store name of this PC's OpenObserve ingest credential: the whole header value."""


def send_to(raw: object) -> str:
    """The `send_to` value, or ValueError naming what was written. Missing means `off`."""
    if raw is None:
        return OFF
    if isinstance(raw, str) and (raw in {OFF, THIS_PC} or PLACE.fullmatch(raw)):
        return raw
    raise ValueError(f"[telemetry] send_to is {raw!r}: use off, this-pc or a place name")


def endpoint(target: str) -> str:
    """The OTLP/HTTP root for a parsed `send_to`, or "" when nothing is sent."""
    if target == OFF:
        return ""
    if target == THIS_PC:
        return THIS_PC_ENDPOINT
    return f"http://{target}:{COLLECTOR_PORT}"


def target(home: Path) -> str:
    """The parsed `send_to` `<home>/settings.toml` names. A file that does not parse, or a value
    that is not one of the three, sends nothing."""
    try:
        document = tomllib.loads((home / "settings.toml").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return OFF
    except (OSError, ValueError) as error:
        LOG.warning("telemetry: settings.toml was not read, so nothing is sent: %s", error)
        return OFF
    section: object = document.get(SECTION)
    raw = cast("dict[str, object]", section).get("send_to") if isinstance(section, dict) else None
    try:
        return send_to(raw)
    except ValueError as error:
        LOG.warning("telemetry: %s; nothing is sent", error)
        return OFF


def configured(home: Path) -> str:
    """The OTLP/HTTP root `<home>/settings.toml` names, or "" when it names none."""
    return endpoint(target(home))


def headers(home: Path, read: Callable[[str], str | None]) -> dict[str, str]:
    """The headers every sender adds: the ingest credential `read` finds under `INGEST_KEY`, for
    `this-pc` only. A key store that fails sends no header, so the sender's own failure counter
    says what went wrong rather than every send raising."""
    if target(home) != THIS_PC:
        return {}
    try:
        found = read(INGEST_KEY)
    except Exception as error:  # any key store failure: send without the header
        LOG.warning("telemetry: the key store did not answer (%s)", type(error).__name__)
        return {}
    return {"Authorization": found} if found else {}
