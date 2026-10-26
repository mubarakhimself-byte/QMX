"""`settings.toml [telemetry] send_to`: where this machine's monitoring goes (design 62 E1).

One setting decides it for every sender on the machine: each chat's CLI, the engine's exporter
and Hindsight's tracing. `off` is the default and sends nothing. `this-pc` sends to OpenObserve on
this machine's loopback. Any other value names a place, whose collector is reached by that name
over the tailnet. No sender holds an address of its own.
"""

from __future__ import annotations

import logging
import re
import tomllib
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


def configured(home: Path) -> str:
    """The OTLP/HTTP root `<home>/settings.toml` names, or "" when it names none. A file that
    does not parse, or a value that is not one of the three, sends nothing."""
    try:
        document = tomllib.loads((home / "settings.toml").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return ""
    except (OSError, ValueError) as error:
        LOG.warning("telemetry: settings.toml was not read, so nothing is sent: %s", error)
        return ""
    section: object = document.get(SECTION)
    raw = cast("dict[str, object]", section).get("send_to") if isinstance(section, dict) else None
    try:
        return endpoint(send_to(raw))
    except ValueError as error:
        LOG.warning("telemetry: %s; nothing is sent", error)
        return ""
