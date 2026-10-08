"""Adapt trusted engine inputs; agents never choose filesystem roots or execution code."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field, fields, is_dataclass
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from qmb.results.ct32 import as_ct32_artifact
from qmb.runloop import run
from qmf.core import Result, World, is_refusal
from qmf.data.store.append_store import AppendStore
from qml.protocol import HostedBot
from qmn.doors.api import DoorRuntime
from qmx_control.library import Library
from qmx_control.models import ControlError, LibraryInput, MemoKey
from qmx_control.service import ControlService

ResponseFormat = Literal["concise", "detailed"]


class Request(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response_format: ResponseFormat = "concise"


class Page(Request):
    limit: int = Field(default=50, ge=1, le=500)
    cursor: int = Field(default=0, ge=0)


class SeriesRequest(Page):
    symbol: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    start: int | None = None
    end: int | None = None

    @model_validator(mode="after")
    def ordered_window(self) -> SeriesRequest:
        if self.start is not None and self.end is not None and self.start > self.end:
            raise ValueError("start must be at or before end; use nanoseconds for both")
        return self


class Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["bars", "features", "calendar"]
    symbol: str
    timeframe: str
    fingerprint: str


class BacktestSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    config_ref: str = Field(min_length=1)


class Artifact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    content: Any


class OrderProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    side: Literal["buy", "sell"]
    quantity: Decimal = Field(gt=0, allow_inf_nan=False)
    reason: str = Field(min_length=1)

    @field_validator("quantity", mode="before")
    @classmethod
    def exact_quantity(cls, value: Any) -> Any:
        if isinstance(value, float):
            raise ValueError("Send quantity as a decimal string, never a binary float")
        return value


def json_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: json_value(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return {
            str(key): json_value(item) for key, item in cast("Mapping[Any, Any]", value).items()
        }
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in cast("list[Any]", value)]
    return value


def unwrap(result: Result[Any]) -> Any:
    if is_refusal(result):
        raise ValueError(
            f"Engine refused the request: {json_value(result)}. "
            "Correct the cited input or ask the host to configure its recorded evidence."
        )
    return result.value


@dataclass
class DomainContext:
    root: Path
    store: AppendStore | None = None
    datasets: list[Dataset] = field(default_factory=list[Dataset])
    backtests: dict[str, dict[str, Any]] = field(default_factory=dict[str, dict[str, Any]])
    backtest_identities: dict[str, MemoKey] = field(default_factory=dict[str, MemoKey])
    bots: dict[str, HostedBot] = field(default_factory=dict[str, HostedBot])
    node: DoorRuntime | None = None
    inline_bytes: int = 16_000
    library: Library = field(init=False)
    control: ControlService = field(init=False)

    def __post_init__(self) -> None:
        self.control = ControlService(self.root)
        self.library = self.control.library

    def save(self, artifact: Artifact) -> dict[str, Any]:
        saved = self.control.library_save(
            LibraryInput(
                title=artifact.name, kind=artifact.kind, content=json_value(artifact.model_dump())
            )
        )
        return {"ref": saved["ref"], "name": artifact.name, "kind": artifact.kind}

    def artifact(self, ref: str) -> Artifact:
        try:
            saved = self.library.by_ref(ref)
        except ControlError as error:
            raise ValueError(str(error)) from error
        content = saved["content"]
        if (
            isinstance(content, dict)
            and content.get("name") == saved["title"]
            and content.get("kind") == saved["kind"]
            and "content" in content
        ):
            return Artifact.model_validate(content)
        return Artifact(name=str(saved["title"]), kind=str(saved["kind"]), content=content)

    def output(self, value: Any, name: str, response_format: ResponseFormat) -> dict[str, Any]:
        body = json_value(value)
        encoded = json.dumps(body, sort_keys=True, ensure_ascii=False)
        if len(encoded.encode()) > self.inline_bytes:
            return {"artifact": self.save(Artifact(name=name, kind="tool-result", content=body))}
        return {"name": name, "result": body, "response_format": response_format}

    def page(self, rows: list[Any], request: Page, name: str) -> dict[str, Any]:
        end = request.cursor + request.limit
        selected = rows[request.cursor : end]
        return {
            **self.output(selected, name, request.response_format),
            "next_cursor": end if end < len(rows) else None,
            "total": len(rows),
        }

    def read(self, kind: str, request: SeriesRequest) -> dict[str, Any]:
        if self.store is None:
            raise ValueError("No data store configured; inject a host-owned QMF AppendStore")
        matches = [
            item
            for item in self.datasets
            if item.kind == kind
            and item.symbol == request.symbol
            and item.timeframe == request.timeframe
        ]
        if not matches:
            raise ValueError(
                "No matching recorded dataset; select symbol/timeframe from list_instruments"
            )
        rows: list[dict[str, Any]] = []
        for item in matches:
            rows.extend(
                unwrap(
                    self.store.read_raw(
                        item.fingerprint, for_world=self.store.world, at=request.end
                    )
                )
            )
        rows = [
            row
            for row in rows
            if (request.start is None or row["t"] >= request.start)
            and (request.end is None or row["t"] <= request.end)
        ]
        rows.sort(key=lambda row: row["t"])
        return self.page(rows, request, kind)

    def run_backtest(self, spec: BacktestSpec, response_format: ResponseFormat) -> dict[str, Any]:
        arguments = self.backtests.get(spec.config_ref)
        if arguments is None:
            raise ValueError(
                "Unknown config_ref; ask the host to register a recorded QMB run configuration"
            )

        def produce() -> LibraryInput:
            outcome = unwrap(run(**arguments))
            content = json_value(outcome)
            if outcome.performance_result is not None:
                content["performance_result"] = unwrap(as_ct32_artifact(outcome.performance_result))
            return LibraryInput(
                title=spec.config_ref,
                kind="backtest",
                content={
                    "name": spec.config_ref,
                    "kind": "backtest",
                    "content": content,
                },
            )

        identity = self.backtest_identities.get(spec.config_ref)
        saved = (
            self.control.memoized_backtest(identity, produce)
            if identity
            else self.control.library_save(produce())
        )
        content = cast("dict[str, Any]", saved["content"])["content"]
        return self.output(
            {
                "run_id": saved["ref"],
                "status": "completed",
                "data_points_processed": content["data_points_processed"],
                "memo_key": saved.get("memo_key"),
            },
            "backtest",
            response_format,
        )

    @classmethod
    def from_environment(cls) -> DomainContext:
        import os  # noqa: PLC0415
        from importlib import import_module  # noqa: PLC0415

        from qmf.data import EvidenceStore  # noqa: PLC0415

        factory_ref = os.environ.get("QMX_TOOLS_FACTORY")
        if factory_ref:
            module, separator, name = factory_ref.partition(":")
            if not separator:
                raise ValueError("QMX_TOOLS_FACTORY must be a host-owned module:function")
            context = getattr(import_module(module), name)()
            if not isinstance(context, cls):
                raise ValueError("QMX_TOOLS_FACTORY must return a DomainContext")
            return context
        root = Path(os.environ.get("QMX_TOOLS_ROOT", str(Path.home() / ".qmx"))).resolve()
        ctx = cls(root=root)
        manifest = root / "datasets.json"
        if manifest.exists():
            ctx.datasets = [
                Dataset.model_validate(item)
                for item in json.loads(manifest.read_text(encoding="utf-8"))
            ]
            ctx.store = unwrap(EvidenceStore(root / "market").for_world(World.REPLAY)).append_store
        return ctx
