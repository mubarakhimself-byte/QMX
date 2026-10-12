"""Validate and hash the immutable app image, independently of an instance."""

from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from pydantic import BaseModel, ConfigDict, Field, JsonValue

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


class Budget(StrictModel):
    runs: int = Field(default=1000, gt=0)
    cpu_seconds: float = Field(default=300, gt=0)
    memory_mb: int = Field(default=1024, gt=0, le=16384)
    cpu_percent: int = Field(default=50, ge=1, le=100)


class Breaker(StrictModel):
    max_errors: int = Field(default=3, gt=0)
    heartbeat_timeout: float = Field(default=10, ge=1)


class Schedule(StrictModel):
    interval_seconds: float = Field(gt=0)


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
    schedule: Schedule | None = None
    budget: Budget = Field(default_factory=Budget)
    breaker: Breaker = Field(default_factory=Breaker)
    provides: dict[str, Document] = Field(default_factory=dict)
    feeds: dict[str, Document] = Field(default_factory=dict)


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
            if manifest.schedule and not entries.jobs:
                raise ValueError("An interval schedule requires job entrypoints.")
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
