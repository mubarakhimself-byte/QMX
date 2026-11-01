"""Adapt trusted engine inputs; agents never choose filesystem roots or execution code."""

from __future__ import annotations

import json
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Final, Literal, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from qmf.core import Result, is_refusal
from qml.protocol import HostedBot
from qmn.doors.api import DoorRuntime
from qmx_control.library import OPERATOR, Library
from qmx_control.models import ControlError, LibraryInput
from qmx_control.service import ControlService
from qmx_judge.tries import TRY_KIND, try_item
from qmx_library.principal import MAIN

ResponseFormat = Literal["concise", "detailed"]
type Document = dict[str, Any]

QMB_APP: Final = "qmb"
QMB_BACKTEST: Final = "jobs/backtest.py"
"""The tester and its `backtest` job every door starts: the default tester (`qmb.md` section 5)."""


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
    market: MarketPort | None = None
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

    def backtest(self, request: Document, response_format: ResponseFormat) -> dict[str, Any]:
        """Start one QMB `backtest` job as this chat and wait up to `[qmb] agent_wait_s` for it.

        The job crosses the supervisor's one run path, where the core's lander opens the run,
        counts its try and lands its result (Part B AD-202). A run still going when the wait
        ends answers its run id, read from the `opened` try this chat's run landed."""
        principal = self.control._caller()  # pyright: ignore[reportPrivateUsage]
        wait = float(cast("int | float", self.control.settings_get("qmb")["agent_wait_s"]))
        asked_at = datetime.now(UTC).isoformat()
        outcome: dict[str, Any] = {}

        def start() -> None:
            try:
                outcome["ran"] = self.control.app_job(
                    QMB_APP, QMB_BACKTEST, inputs=request, principal=principal
                )
            except ControlError as error:
                outcome["refused"] = error

        worker = threading.Thread(target=start, name="qmx-backtest", daemon=True)
        worker.start()
        worker.join(wait)
        if "refused" in outcome:
            raise ValueError(str(outcome["refused"]))
        if "ran" in outcome:
            run_id = str(outcome["ran"]["run_id"])
            result_id = self.library.store.head(run_id, MAIN)
            fields = {} if result_id is None else self._fields(result_id[0])
            found = {
                "run_id": run_id,
                "status": fields.get("status"),
                "result_id": result_id[0] if result_id else None,
            }
            if fields.get("reason"):
                found["reason"] = fields["reason"]
            return self.output(found, "backtest", response_format)
        opened = self._opened(principal, str(request["unit"]), asked_at)
        return self.output(
            {"run_id": opened, "status": "running", "result_id": None, "waited_s": wait},
            "backtest",
            response_format,
        )

    def _fields(self, object_id: str) -> dict[str, Any]:
        return dict(self.library.store.get(OPERATOR, object_id).fields)

    def _opened(self, principal: str, unit: str, since: str) -> str | None:
        """The newest run this principal opened on `unit` since `since` that has not closed."""
        store = self.library.store
        newest: tuple[str, str] | None = None
        for object_id in store.with_field(TRY_KIND, "principal", principal):
            fields = self._fields(object_id)
            run_id, at = str(fields.get("run_id")), str(fields.get("at", ""))
            if fields.get("state") != "opened" or fields.get("unit") != unit or at < since:
                continue
            if store.head(try_item(run_id, "landed"), MAIN) is None and (
                newest is None or at > newest[1]
            ):
                newest = (run_id, at)
        return None if newest is None else newest[0]
