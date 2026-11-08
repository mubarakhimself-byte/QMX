"""Validate and hash the immutable app image, independently of an instance.

An app declares three things beyond its entrypoints: its `[operations]` (the only way another app
or a chat reaches it), the contracts it keeps (`[provides]` out, `[feeds]` in, `[profiles]` for a
profile document), and how it wants to be run (`[suggested_trigger]`, `[isolation]`). There is no
event list: an app's landing is a Library artifact and the event is the Library ref log (AD-64).
`emits` and `accepts` are retired and refused by name.
"""

from __future__ import annotations

import hashlib
import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from math import ceil
from pathlib import Path
from types import MappingProxyType
from typing import Final, Literal, cast

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from qmx_apps.errors import AppError, Document

type Trust = Literal["first_party", "operator", "reviewed", "agent"]
IGNORED = frozenset({".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"})
RESERVED = frozenset(
    {
        "con",
        "prn",
        "aux",
        "nul",
        *[f"com{i}" for i in range(1, 10)],
        *[f"lpt{i}" for i in range(1, 10)],
    }
)
SYSTEM_ENV = frozenset(
    {
        "PATH",
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "HOME",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "TEMP",
        "TMP",
        "PYTHONPATH",
        "PYTHONDONTWRITEBYTECODE",
        "QMX_VOLUME",
        "QMX_STAGE",
    }
)
OPERATION_NAME: Final = re.compile(r"\A[a-z][a-z0-9_]*\Z")
"""An operation is a snake_case word. It is the second half of the tool's wire name, so it stays
inside `[a-zA-Z0-9_-]` and its own name can never carry a dash or a dot."""
NODE_APP: Final = "trading-node"
TRADING_GRANT_SECRETS: Final = frozenset({"qmx/trading-node-keys"})
TRADING_GRANT_PREFIXES: Final = ("qmx/trading-node-keys-", "qmx/node-")
"""The venue trading-grant secrets only the trading node may name (Level 0 AD-33's secret map,
Part C AD-306): its keys document, the per-venue split of it, and its own grant entries
`qmx/node-<tag>-<venue>`. Compared case-folded, because Credential Manager and NTFS ignore case."""
HOST_SECRETS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "qmx/control-token": "control bearer, which acts as the operator",
        "qmx/chatgpt": "ChatGPT sign-in",
        "qmx/rclone-config": "backup configuration password",
        "qmx/pairing-key": "pairing key, which signs every run pass",
        "qmx/run-pass-key": "run pass key",
        "qmx/openobserve-root": "deep-logs root password",
        "qmx/openobserve-ingest": "deep-logs sign-in",
        "qmx/openobserve-agent": "deep-logs sign-in",
        "qmx/ctrader-client-id": "cTrader app Client ID, which can sign in to his broker",
        "qmx/ctrader-client-secret": "cTrader app Client secret, which can sign in to his broker",
        "qmx/ctrader-mcp": "cTrader MCP token, which acts on his cTrader account",
    }
)
HOST_SECRET_PREFIXES: Final[Mapping[str, str]] = MappingProxyType(
    {"qmx/chatgpt-": "ChatGPT sign-in"}
)
"""The entries the host holds for itself, which no app may declare on any role: the bearer
(`qmx_control.server`), the chat sign-ins `qmx/chatgpt` and `qmx/chatgpt-<n>`
(`qmx_router.gpt.siwc`), the backup password (`qmx_home.rclone`), the vault files a home signs
passes with, the deep-logs sign-in (`qmx_host.connect_logs`), the cTrader app keys he types
(`qmx_broker.credentials`) and the cTrader MCP token agents' chats use (`qma.harness.tools`,
C-36). The server's vault reader (`qmx_host.host.HOST_VAULT`) reads this
table, so a new host name is refused in both places. Compared case-folded, because Credential
Manager and NTFS ignore case."""
RETIRED: Final = frozenset({"emits", "accepts"})
"""`app.<id>.<event>` and webhook routes are gone: the app's landing is the event (AD-64)."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Entrypoints(StrictModel):
    mcp: str
    jobs: list[str] = Field(default_factory=list)
    agents: list[str] = Field(default_factory=list)
    workflows: list[str] = Field(default_factory=list)
    ui: str | None = None


class Capabilities(StrictModel):
    network: list[str] = Field(default_factory=list)
    secrets: dict[str, str] = Field(default_factory=dict)
    data_reads: list[str] = Field(default_factory=list)


LEGACY_BUDGET: Final = frozenset({"runs", "cpu_seconds"})
"""Usage budgets retired by engine AD-57 and ruling 106. They are dropped on load, and nothing
stops an app on usage."""


class Isolation(StrictModel):
    """Machine isolation he may set per app (a Job object or a container limit). Unset, the app
    runs unlimited; neither value is a breaker that stops an app on usage, and neither is set by
    default. `[isolation]` is the table's name; `[budget]` still loads for an app that has not
    migrated yet, its two usage keys dropped."""

    memory_mb: int | None = Field(default=None, gt=0, le=16384)
    cpu_percent: int | None = Field(default=None, ge=1, le=100)

    @model_validator(mode="before")
    @classmethod
    def _drop_usage(cls, data: object) -> object:
        if isinstance(data, dict):
            table = cast(dict[str, object], data)
            return {key: value for key, value in table.items() if key not in LEGACY_BUDGET}
        return data


Budget = Isolation
"""The old name of the isolation table, kept for the modules that read `manifest.budget`."""


class Breaker(StrictModel):
    """When the supervisor trips an app, and what it does next. `restart = "backoff"` starts a
    tripped app again by itself (AD-33 change 3): it waits `backoff_seconds` after the first trip
    and doubles the wait on each further trip up to `backoff_max_seconds`. `never` leaves it down
    until someone starts it, as every app that sets nothing is."""

    max_errors: int = Field(default=3, gt=0)
    heartbeat_timeout: float = Field(default=10, ge=1)
    restart: Literal["never", "backoff"] = "never"
    backoff_seconds: float = Field(default=5, gt=0)
    backoff_max_seconds: float = Field(default=300, gt=0)

    @model_validator(mode="after")
    def _ordered_backoff(self) -> Breaker:
        if self.backoff_max_seconds < self.backoff_seconds:
            raise ValueError("backoff_max_seconds is at least backoff_seconds.")
        return self

    def backoff(self, trips: int) -> float:
        """The wait before the restart that follows trip number `trips`, counted from 1."""
        doublings = min(trips - 1, 64)  # restarts never stop, and 2**n past 1023 overflows a float
        return min(self.backoff_seconds * 2**doublings, self.backoff_max_seconds)


class SuggestedTrigger(StrictModel):
    """The trigger his enable creates on the app's `app_op` workflow (engine AD-57), in the
    engine's trigger shape. `job` names the job entrypoint it runs, the first one when unset."""

    kind: Literal["interval", "cron"] = "interval"
    seconds: int | None = Field(default=None, gt=0)
    expr: str | None = None
    zone: str = "UTC"
    job: str | None = None

    @model_validator(mode="after")
    def _one_schedule(self) -> SuggestedTrigger:
        if (self.kind == "interval") != (self.seconds is not None) or (
            (self.kind == "cron") != (self.expr is not None)
        ):
            raise ValueError("An interval trigger takes seconds; a cron trigger takes expr.")
        return self


class Operation(StrictModel):
    """One thing another app or a chat may ask this app to do (AD-61, AD-64). The catalog builds
    the row from this table and nothing else, so a tool the app's server serves but does not
    declare here is never reachable."""

    description: str = ""
    input_schema: Document = Field(default_factory=dict)
    output_schema: Document = Field(default_factory=dict)
    approval: Literal["read", "domain_write", "manage"] = "read"
    reversibility: (
        Literal["none", "reversible", "compensable", "irreversible", "irreversible_external"] | None
    ) = None
    state: Literal["none", "instance"] = "none"
    returns: Literal["value", "artifact", "run"] = "value"


class Contract(StrictModel):
    """A schema an app declares at a seam, and how long an output under it stays fresh. Written
    as `[provides.<name>] schema = { ... }` with an optional `stale_after` in seconds; the bare
    form `[provides.<name>] type = "object" ...` is the same contract without a `stale_after`.

    `lander` names a core lander the host registered (AD-33 change 2): every job of the app is
    opened by it before it queues, and an output under this contract reaches the Library only
    through its close."""

    schema_: Document = Field(alias="schema")
    stale_after: float | None = Field(default=None, gt=0)
    lander: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def _bare_schema(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        table = dict(cast(dict[str, object], data))
        if "schema" not in table or set(table) - {"schema", "stale_after", "lander"}:
            return {"schema": table}
        return table


class AppDefinition(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$", max_length=80)
    name: str = Field(min_length=1, max_length=200)
    version: str = Field(
        pattern=r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[\w.-]+)?(?:\+[\w.-]+)?$"
    )
    risk: Literal["shows", "runs", "money"]
    kind: Literal["screens", "headless", "both"]
    startup_timeout_seconds: float = Field(default=90, gt=0)
    entrypoints: Entrypoints
    capabilities: Capabilities = Field(default_factory=Capabilities)
    suggested_trigger: SuggestedTrigger | None = None
    isolation: Isolation = Field(default_factory=Isolation)
    breaker: Breaker = Field(default_factory=Breaker)
    operations: dict[str, Operation] = Field(default_factory=dict)
    provides: dict[str, Contract] = Field(default_factory=dict)
    feeds: dict[str, Contract] = Field(default_factory=dict)
    profiles: Contract | None = None

    @property
    def budget(self) -> Isolation:
        return self.isolation

    @property
    def lander(self) -> str | None:
        """The one lander the app's provides name, if any."""
        return next((it.lander for it in self.provides.values() if it.lander is not None), None)

    @model_validator(mode="after")
    def _one_lander(self) -> AppDefinition:
        named = {it.lander for it in self.provides.values() if it.lander is not None}
        if len(named) > 1:
            raise ValueError(f"An app lands through one lander; its provides name {sorted(named)}.")
        return self

    @model_validator(mode="before")
    @classmethod
    def _tables(cls, data: object) -> object:
        """`[budget]` is the isolation table's old spelling, `[schedule] interval_seconds` reads
        as an interval `[suggested_trigger]`, and a retired key is named."""
        if not isinstance(data, dict):
            return data
        table = dict(cast(dict[str, object], data))
        for retired in sorted(RETIRED & set(table)):
            raise ValueError(
                f"{retired} is retired: an app lands a Library artifact under a provides name, "
                "and the Library ref log is the event"
            )
        if "budget" in table and "isolation" not in table:
            table["isolation"] = table.pop("budget")
        schedule = table.pop("schedule", None)
        if isinstance(schedule, dict) and "suggested_trigger" not in table:
            seconds = cast(dict[str, object], schedule).get("interval_seconds")
            if isinstance(seconds, int | float) and not isinstance(seconds, bool):
                table["suggested_trigger"] = {"kind": "interval", "seconds": max(1, ceil(seconds))}
        return table


def _local_schema(value: JsonValue) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"$ref", "$dynamicRef"} and (
                not isinstance(item, str) or not item.startswith("#")
            ):
                raise ValueError(
                    "Artifact schemas must be self-contained (local fragment refs only)."
                )
            _local_schema(item)
    elif isinstance(value, list):
        for item in value:
            _local_schema(item)


def schemas(manifest: AppDefinition) -> list[tuple[str, Document]]:
    """Every JSON Schema the definition declares, by the name it is declared under."""
    found = [(f"provides.{name}", it.schema_) for name, it in manifest.provides.items()]
    found += [(f"feeds.{name}", it.schema_) for name, it in manifest.feeds.items()]
    for name, operation in manifest.operations.items():
        found += [
            (f"operations.{name}.input_schema", operation.input_schema),
            (f"operations.{name}.output_schema", operation.output_schema),
        ]
    if manifest.profiles is not None:
        found.append(("profiles", manifest.profiles.schema_))
    return [(name, schema) for name, schema in found if schema]


def image_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts):
            continue
        if path.is_symlink() or path.is_junction():
            raise ValueError("Definitions cannot contain symlinks or junctions.")
        if path.is_file():
            paths.append(path)
    return paths


def image_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in image_files(root):
        name = path.relative_to(root).as_posix().encode()
        content = path.read_bytes()
        digest.update(len(name).to_bytes(8, "big"))
        digest.update(name)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def host_secret(service: str) -> str | None:
    """What `service` is when it names one of the host's own entries, in any letter case."""
    name = service.casefold()
    if found := HOST_SECRETS.get(name):
        return found
    return next(
        (what for prefix, what in HOST_SECRET_PREFIXES.items() if name.startswith(prefix)), None
    )


def _checked(manifest: AppDefinition, name: str, schema: Document) -> None:
    try:
        _local_schema(schema)
        Draft202012Validator.check_schema(schema)
    except (ValueError, SchemaError) as error:
        raise ValueError(f"{name} is not a self-contained JSON Schema: {error}") from error


@dataclass(frozen=True)
class Definition:
    root: Path
    manifest: AppDefinition
    hash: str

    @classmethod
    def load(cls, path: Path) -> Definition:
        root = path.resolve()
        try:
            with (root / "app.toml").open("rb") as file:
                manifest = AppDefinition.model_validate(tomllib.load(file))
            if manifest.id in RESERVED:
                raise ValueError("App id is a reserved Windows filename.")
            entries = manifest.entrypoints
            for name in [entries.mcp, *entries.jobs, *entries.agents, *entries.workflows]:
                entry = (root / name).resolve()
                if not entry.is_relative_to(root) or not entry.is_file():
                    raise ValueError("Entrypoints must be files inside the definition.")
            if not entries.mcp.endswith(".py") or any(
                not item.endswith(".py") for item in entries.jobs
            ):
                raise ValueError("MCP and job entrypoints are Python script paths.")
            suggested = manifest.suggested_trigger
            if suggested and suggested.job not in {None, *entries.jobs}:
                raise ValueError("A suggested trigger runs one of the app's job entrypoints.")
            if suggested and not entries.jobs:
                raise ValueError("A suggested trigger requires job entrypoints.")
            if entries.ui:
                ui = (root / entries.ui).resolve()
                if not ui.is_relative_to(root) or not ui.is_dir():
                    raise ValueError("UI must be a directory inside the definition.")
            if (manifest.kind == "headless") == bool(entries.ui):
                raise ValueError("Headless apps omit UI; screens/both apps declare it.")
            for name, service in manifest.capabilities.secrets.items():
                if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name) or name in SYSTEM_ENV:
                    raise ValueError(
                        "Secret environment names must not override runtime variables."
                    )
                if not re.fullmatch(r"qmx/[a-zA-Z0-9_-]+", service):
                    raise ValueError("Secrets must reference qmx/* Credential Manager services.")
                if owned := host_secret(service):
                    raise ValueError(f"{service} is the host's own {owned}; no app may declare it.")
            grants = [
                service
                for service in manifest.capabilities.secrets.values()
                if service.casefold() in TRADING_GRANT_SECRETS
                or service.casefold().startswith(TRADING_GRANT_PREFIXES)
            ]
            if grants and manifest.id != NODE_APP:
                raise ValueError(
                    f"Only the {NODE_APP} app may name the venue trading-grant secrets; "
                    f"{manifest.id} names {', '.join(sorted(grants))}."
                )
            for name, operation in manifest.operations.items():
                if not OPERATION_NAME.fullmatch(name):
                    raise ValueError(
                        f"operations.{name} is not a snake_case word of letters, digits and "
                        "underscores"
                    )
                if operation.state == "instance" and operation.approval == "read":
                    raise ValueError(
                        f"operations.{name} keeps instance state, so it cannot be a read"
                    )
            for name, schema in schemas(manifest):
                _checked(manifest, name, schema)
            for name in ("pyproject.toml", "uv.lock"):
                if not (root / name).is_file():
                    raise ValueError(f"The definition requires {name}.")
            return cls(root, manifest, image_hash(root))
        except (OSError, ValueError, SchemaError) as error:
            raise AppError("invalid_definition", str(error)) from error
