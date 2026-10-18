"""The settings port (SOLUTION-DESIGN 8.3): the engine's defaults with the operator's `[engine]` and
`[roles]` sections over them, read through `ControlService.settings_get`. It never writes.

`[engine]` holds any `settings.DEFAULTS` key, as a dotted key or as nested tables
(`[engine.retry] backoff = [...]` is `retry.backoff`); a key the engine does not know is ignored.
`[roles]` maps a role name to its candidate list, so the operator may add a role. Until the
account pool (L2), the plan account's background share is the harness's `[budgets]
background_cap`, read here and never written.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Protocol, cast

from pydantic import JsonValue
from qmx_control.service import ControlService

from qmx_engine.roles import PLAN
from qmx_engine.settings import DEFAULTS, Setting


class SettingsPort(Protocol):
    def values(self) -> Mapping[str, Setting]: ...


class StaticSettings:
    def __init__(self, values: Mapping[str, Setting] = DEFAULTS) -> None:
        self._values = values

    def values(self) -> Mapping[str, Setting]:
        return self._values


class ControlSettings:
    def __init__(self, control: ControlService) -> None:
        self.control = control

    def values(self) -> Mapping[str, Setting]:
        merged: dict[str, Setting] = dict(DEFAULTS)
        engine = self.control.settings_get("engine")
        for key, value in flatten(engine, ""):
            if key in DEFAULTS and (found := setting(value)) is not None:
                merged[key] = found
        cap = setting(self.control.settings_get("budgets").get("background_cap"))
        if isinstance(cap, int | float):
            merged[f"pool.accounts.{PLAN}.background_share"] = cap
        roles = self.control.settings_get("roles")
        for role, value in roles.items():
            if (found := setting(value)) is not None:
                merged[f"roles.{role}"] = found
        return merged


def flatten(table: Mapping[str, JsonValue], prefix: str) -> Iterator[tuple[str, JsonValue]]:
    for key, value in table.items():
        if isinstance(value, dict):
            yield from flatten(value, f"{prefix}{key}.")
        else:
            yield f"{prefix}{key}", value


def setting(value: JsonValue) -> Setting:
    if isinstance(value, list):
        if all(isinstance(v, str) for v in value):
            return tuple(cast(list[str], value))
        if all(isinstance(v, int) and not isinstance(v, bool) for v in value):
            return tuple(cast(list[int], value))
        return None
    if isinstance(value, bool):
        return None
    return value if isinstance(value, int | float | str) else None
