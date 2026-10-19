"""Validate and hash the immutable app image, independently of an instance."""

from __future__ import annotations

import hashlib
import math
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
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
"""Usage budgets retired by engine AD-57 and ruling 106. The example apps still carry them until
they migrate (APP2a), so a manifest naming them loads and they are dropped."""


class Budget(StrictModel):
    """Machine isolation he may set per app (a Job object or container limit). Unset, the app
    runs unlimited; neither value is a breaker that stops an app on usage."""

    memory_mb: int | None = Field(default=None, gt=0, le=16384)
    cpu_percent: int | None = Field(default=None, ge=1, le=100)

    @model_validator(mode="before")
    @classmethod
    def _drop_usage(cls, data: object) -> object:
        if isinstance(data, dict):
            table = cast(dict[str, object], data)
            return {key: value for key, value in table.items() if key not in LEGACY_BUDGET}
        return data


class Breaker(StrictModel):
    max_errors: int = Field(default=3, gt=0)
    heartbeat_timeout: float = Field(default=10, ge=1)


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
    budget: Budget = Field(default_factory=Budget)
    breaker: Breaker = Field(default_factory=Breaker)
    provides: dict[str, Document] = Field(default_factory=dict)
    feeds: dict[str, Document] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _legacy_schedule(cls, data: object) -> object:
        """`[schedule] interval_seconds` is read as an interval `suggested_trigger` until the
        example apps migrate (APP2a)."""
        if not isinstance(data, dict):
            return data
        table = dict(cast(dict[str, object], data))
        if "schedule" not in table:
            return table
        schedule = table.pop("schedule")
        if isinstance(schedule, dict) and "suggested_trigger" not in table:
            seconds = cast(dict[str, object], schedule).get("interval_seconds")
            if isinstance(seconds, int | float) and not isinstance(seconds, bool):
                seconds = max(1, math.ceil(seconds))
            table["suggested_trigger"] = {"kind": "interval", "seconds": seconds}
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
            for schema in [*manifest.provides.values(), *manifest.feeds.values()]:
                _local_schema(schema)
                Draft202012Validator.check_schema(schema)
            for name in ("pyproject.toml", "uv.lock"):
                if not (root / name).is_file():
                    raise ValueError(f"The definition requires {name}.")
            return cls(root, manifest, image_hash(root))
        except (OSError, ValueError, SchemaError) as error:
            raise AppError("invalid_definition", str(error)) from error
