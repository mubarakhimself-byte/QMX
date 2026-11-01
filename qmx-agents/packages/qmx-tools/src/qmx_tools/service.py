"""Adapt trusted engine inputs; agents never choose filesystem roots or execution code."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields, is_dataclass
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Final, Literal, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from qmf.core import Result, is_refusal
from qml.protocol import HostedBot
from qmn.doors.api import DoorRuntime
from qmx_control.library import Library
from qmx_control.models import ControlError, LibraryInput
from qmx_control.service import ControlService
from qmx_judge.landing import BacktestResult, LandingPort, land

ResponseFormat = Literal["concise", "detailed"]


class SeriesRow(Protocol):
    """One series as the market-data door names it."""

    @property
    def series(self) -> str: ...

    @property
    def subject(self) -> str: ...

    @property
    def kind(self) -> str: ...


class ReadRow(Protocol):
    """One answer from the market-data door."""

    @property
    def series(self) -> str: ...

    @property
    def fingerprints(self) -> tuple[str, ...]: ...

    @property
    def rows(self) -> tuple[dict[str, object], ...]: ...


class MarketPort(Protocol):
    """The host's market-data door, as the tools see it (Lib AD-28).

    The door is a module of the host, not of this package, so the tools depend on this shape
    and the host passes its own object in. Every read goes through it: the door is where the
    seal and the split are applied.
    """

    def instruments(self) -> Result[Any]: ...

    def card(self, series: str) -> Result[Any]: ...

    def read(
        self,
        series: str = "",
        *,
        fingerprints: Sequence[str] = (),
        start_ns: int | None = None,
        end_ns: int | None = None,
        purpose: Any = "exploration",
        data_scope: Sequence[str] | None = None,
        into: Path | None = None,
        holdout: Any = None,
        run: str | None = None,
    ) -> Result[Any]: ...


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
    holdout: dict[str, int | str] | Literal["off"] | None = None
    """The study's holdout, `{"boundary": "YYYY-MM", "months": n}` or "off"; None takes the
    run's fixed one, else the Settings default, which is off (ruling 137)."""
    run: str | None = None
    """The run this read belongs to; its first read fixes its holdout."""

    @model_validator(mode="after")
    def ordered_window(self) -> SeriesRequest:
        if self.start is not None and self.end is not None and self.start > self.end:
            raise ValueError("start must be at or before end; use nanoseconds for both")
        return self


FAMILIES: Final[dict[str, str]] = {
    "bars": "bar",
    "features": "feature",
    "calendar": "calendar",
}
"""The agent's word for a series family, and the door kind it names."""


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


@dataclass(frozen=True, slots=True)
class BacktestRun:
    """One finished backtest: the result to land and the three edges to land it with."""

    result: BacktestResult
    consumed: str
    """The dataset card version the backtest read (Library AD-25)."""
    uses: str
    """The bot version it ran (Library AD-29)."""
    tests: str | None = None
    """The hypothesis it was built to test, when one is named (AD-23)."""


class BacktestDoor(Protocol):
    """The engine's `qmb_backtest` operation on the QMB placement (engine AD-31).

    Backtests run on one dedicated QMB machine that agents call, so this tool holds a door and
    not a runner: the door owns the queue, the memo key and the data read, and answers with one
    result to land.
    """

    def run(self, *, spec: Mapping[str, Any]) -> Result[BacktestRun]: ...


@dataclass
class DomainContext:
    root: Path
    market: MarketPort | None = None
    backtests: dict[str, dict[str, Any]] = field(default_factory=dict[str, dict[str, Any]])
    backtest_door: BacktestDoor | None = None
    landing: LandingPort | None = None
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
        """Read one series through the host's market-data door, and cite the card it came from.

        The door is the only reader: it applies the read's holdout and the split, so a sealed
        month is refused with its reason here, never served as an empty page.
        """
        door = self.market
        if door is None:
            raise ValueError(
                "The market-data door did not open on this host: its store cannot be read or "
                "its [data] settings cannot be used; the host log's market-data line says which"
            )
        series = self._series_for(door, kind, request.symbol, request.timeframe)
        answer = unwrap(
            door.read(
                series,
                start_ns=request.start,
                end_ns=request.end,
                purpose="exploration",
                holdout=request.holdout,
                run=request.run,
            )
        )
        return {
            **self.page([dict(row) for row in answer.rows], request, kind),
            "card": answer.series,
            "fingerprints": list(answer.fingerprints),
        }

    def _series_for(self, door: MarketPort, kind: str, symbol: str, timeframe: str) -> str:
        """The door's series for the agent's (kind, symbol, timeframe), or why there is none."""
        family = FAMILIES.get(kind)
        if family is None:
            raise ValueError(f"Unknown data kind {kind!r}; ask for bars, features or calendar")
        expected = "calendar" if family == "calendar" else f"{family}-{timeframe}"
        known = unwrap(door.instruments())
        for row in known:
            if row.subject == symbol and row.kind == expected:
                return row.series
        held = sorted(row.series for row in known if row.subject == symbol)
        absent = (
            f"No {kind} series for {symbol} {timeframe} on this host; "
            f"it holds {held or 'none'} for that instrument; pick one with list_instruments"
        )
        raise ValueError(absent)

    def run_backtest(self, spec: BacktestSpec, response_format: ResponseFormat) -> dict[str, Any]:
        """Ask the QMB placement for one backtest, then land its one result shape.

        The tool no longer runs QMB in this process and no longer writes the old Library's
        `backtest` items: backtests go through the `qmb_backtest` door (engine AD-31) and land as
        one `backtest-result` through the Library's landing step (Library AD-29).
        """
        arguments = self.backtests.get(spec.config_ref)
        if arguments is None:
            raise ValueError(
                "Unknown config_ref; ask the host to register a recorded QMB run configuration"
            )
        door = self.backtest_door
        landing = self.landing
        if door is None or landing is None:
            raise ValueError(
                "This host binds no qmb_backtest door: backtests run on the QMB placement and "
                "land through the Library (engine AD-31, Library AD-29)"
            )
        run = unwrap(door.run(spec=arguments))
        landed = land(
            run.result,
            landing,
            consumed=run.consumed,
            uses=run.uses,
            tests=run.tests,
        )
        return self.output(
            {
                "run_id": landed.object_id,
                "status": "completed",
                "edges": [list(edge) for edge in landed.edges],
                "memo_key": run.result.memo_key,
            },
            "backtest",
            response_format,
        )
