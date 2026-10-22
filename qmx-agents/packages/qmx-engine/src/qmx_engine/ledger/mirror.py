"""A run's journal, mirrored to the Hub, so another machine can adopt the run (AD-7, ruling 117).

An engine instance pushes a run's ledger events to the Hub at each `node_finished`, with the
run's own definition bundle beside them: values and artifacts travel, the zone does not. The Hub
keeps one journal per run and one adoption record per run. `adopt` is the Hub's compare-and-swap:
the claim `adopt:<run_id>` is granted to exactly one home, and no adoption is granted while the
run's own home still beats.

Two sides. `HubJournals` is the engine's side and speaks to the Hub's `/v1/op` route the way
`heartbeat.HubLink` speaks to `/v1/heartbeat`; every refusal is a `MirrorRefused` with a closed
code. The Hub's side is `qmx_hub.server`. `attach`/`attached` names the one Hub this process
pushes to, as `qmx_engine.ports.router` names the one router: a process with no Hub mirrors
nothing and adopts nothing, which is the local case.

Seeding is the one place this module transforms rather than copies. A node that committed files
into its old home's `work/` zone leaves nothing here, so its ending events are left out of the
seed: the slot stays open, `Run.recover` folds that attempt to `unknown`, and the node runs again.
The memo is derived from those endings (`core.fold`), so leaving them out is what voids it.
"""

from __future__ import annotations

import base64
import json
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Protocol, cast

from pydantic import JsonValue

from qmx_engine.ledger.events import Event, EventKind
from qmx_engine.ports.library import Bundle

ADOPT_TTL_S: Final = 900
"""How long an adoption claim holds without a renewal: ten host heartbeats with slack (AD-24)."""
FRESH_S: Final = 90.0
"""Three host heartbeats (AD-65's `autonomy.stale_after`): a home that beat inside this window
still owns its runs, and an adoption of one of them is refused."""
CALL_TIMEOUT_S: Final = 10.0
"""The one event a node that committed files keeps: the record that its files left the overlay."""


class MirrorRefused(Exception):
    """The Hub refused the mirror or the adoption. `code` is the closed word."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class Journal:
    """One run's journal as the Hub holds it: where it ran, its bundle, and its events."""

    run_id: str
    home: str
    at: str
    bundle: Bundle
    events: tuple[Event, ...]

    def as_json(self) -> dict[str, JsonValue]:
        return {
            "run_id": self.run_id,
            "home": self.home,
            "at": self.at,
            "bundle": bundle_json(self.bundle),
            "events": [event_json(event) for event in self.events],
        }

    @classmethod
    def of(cls, payload: Mapping[str, JsonValue]) -> Journal:
        run_id = str(payload["run_id"])
        found = cast("Mapping[str, JsonValue]", payload.get("bundle") or {})
        events = cast("list[Mapping[str, JsonValue]]", payload.get("events") or [])
        return cls(
            run_id,
            str(payload.get("home") or ""),
            str(payload.get("at") or ""),
            bundle_of(found),
            tuple(event_of(event, run_id) for event in events),
        )


def event_json(event: Event) -> dict[str, JsonValue]:
    return {
        "seq": event.seq,
        "at": event.at,
        "kind": event.kind,
        "data": cast(JsonValue, event.data),
    }


def event_of(payload: Mapping[str, JsonValue], run_id: str) -> Event:
    data = payload.get("data")
    return Event(
        int(str(payload.get("seq") or 0)),
        run_id,
        str(payload.get("at") or ""),
        cast(EventKind, str(payload.get("kind"))),
        cast("dict[str, JsonValue]", data if isinstance(data, dict) else {}),
    )


def bundle_json(bundle: Bundle) -> dict[str, JsonValue]:
    """The bundle as JSON: bytes go base64, so a binary ref travels unchanged."""
    return {
        "definition": cast(JsonValue, bundle.definition),
        "files": {
            ref: base64.b64encode(data).decode("ascii") for ref, data in bundle.files.items()
        },
    }


def bundle_of(payload: Mapping[str, JsonValue]) -> Bundle:
    definition = payload.get("definition")
    files = cast("Mapping[str, str]", payload.get("files") or {})
    return Bundle(
        cast("dict[str, JsonValue]", definition if isinstance(definition, dict) else {}),
        {ref: base64.b64decode(data) for ref, data in files.items()},
    )


def journal_of(events: Iterable[Event], *, bundle: Bundle, home: str, at: str) -> Journal:
    found = tuple(events)
    run_id = found[-1].run_id if found else ""
    return Journal(run_id, home, at, bundle, found)


def committed(events: Iterable[Event]) -> frozenset[str]:
    """The node ids that committed files into their home's `work/` zone."""
    return frozenset(
        str(event.data.get("node_id"))
        for event in events
        if event.kind == "zone_committed" and event.data.get("node_id")
    )


def seedable(journal: Journal, folder: Path) -> list[Event]:
    """The events a new home writes as its own ledger, in order.

    `run_created` names this home's folder, since the run lives here now. A node that committed
    files into the old home's `work/` zone keeps one line, that its files left the overlay, and
    nothing else: its slot is absent from the seeded fold, so the memo the ending would have given
    it never exists and the node starts again. Every other slot arrives as it stood.
    """
    gone = committed(journal.events)
    seeded: list[Event] = []
    for event in journal.events:
        if event.kind != "zone_committed" and str(event.data.get("node_id")) in gone:
            continue
        data = event.data
        if event.kind == "run_created":
            data = {**data, "folder": str(folder), "adopted_from": journal.home}
        seeded.append(Event(event.seq, event.run_id, event.at, event.kind, data))
    return seeded


class Journals(Protocol):
    """What a runner pushes to and adopts from: one Hub, named by its home."""

    home: str

    def push(self, journal: Journal) -> float:
        """Send the run's journal; returns the call's milliseconds."""

    def adoption(self, run_id: str) -> str | None:
        """The home that adopted the run, if one did."""

    def adopt(self, run_id: str) -> Journal:
        """Take the claim and the journal, or raise `MirrorRefused`."""


def post_json(url: str, body: Mapping[str, JsonValue], headers: Mapping[str, str]) -> JsonValue:
    """One JSON POST through the standard library: the engine names no HTTP client of its own."""
    request = urllib.request.Request(  # noqa: S310 (the home's own setting)
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=CALL_TIMEOUT_S) as answer:  # noqa: S310
        return cast(JsonValue, json.loads(answer.read()))


def wall() -> str:
    """One RFC 3339 stamp in UTC, the shape a heartbeat row carries."""
    return datetime.now(UTC).isoformat()


class HubJournals:
    """The Hub's journal route, from this home: one call per push, one per adoption.

    `times` keeps each push's milliseconds, so the perf box is read from the same call the run
    makes rather than from a probe beside it. A failed push is counted and never raised into the
    run: a run does not stop because its mirror did.
    """

    def __init__(
        self,
        url: str,
        key: str,
        *,
        home: str,
        ttl: int = ADOPT_TTL_S,
        post: Callable[[str, Mapping[str, JsonValue], Mapping[str, str]], JsonValue] = post_json,
        now: Callable[[], str] = wall,
    ) -> None:
        self.url = url.rstrip("/")
        self.key = key
        self.home = home
        self.ttl = ttl
        self.times: list[float] = []
        self.failures = 0
        self._post = post
        self._now = now

    def op(self, verb: str, args: Mapping[str, JsonValue]) -> JsonValue:
        """One Hub operation. A refusal is a `MirrorRefused`; an unreachable Hub, one too."""
        try:
            answer = self._post(
                f"{self.url}/v1/op/{verb}",
                {"who": "hub", "args": dict(args)},
                {"Authorization": f"Bearer {self.key}"},
            )
        except urllib.error.HTTPError as refused:
            raise MirrorRefused(*_refusal(refused)) from refused
        except OSError as unreachable:
            raise MirrorRefused("hub_unreachable", str(unreachable)) from unreachable
        body = cast("Mapping[str, JsonValue]", answer)
        if not body.get("ok"):
            raise MirrorRefused(str(body.get("code") or "refused"), str(body.get("message") or ""))
        return body.get("value")

    def push(self, journal: Journal) -> float:
        started = time.perf_counter()
        try:
            self.op("journal_put", {"journal": journal.as_json(), "at": self._now()})
        except MirrorRefused:
            self.failures += 1
            raise
        milliseconds = (time.perf_counter() - started) * 1000.0
        self.times.append(milliseconds)
        return milliseconds

    def adoption(self, run_id: str) -> str | None:
        found = self.op("adoption_of", {"run_id": run_id})
        if not isinstance(found, Mapping):
            return None
        to = cast("Mapping[str, JsonValue]", found).get("to")
        return None if to is None else str(to)

    def adopt(self, run_id: str) -> Journal:
        found = self.op("journal_adopt", {"run_id": run_id, "home": self.home, "ttl": self.ttl})
        if not isinstance(found, Mapping):
            raise MirrorRefused("no_journal", f"the Hub holds no journal for {run_id}")
        return Journal.of(cast("Mapping[str, JsonValue]", found))


def _refusal(refused: urllib.error.HTTPError) -> tuple[str, str]:
    """The Hub's own code and message out of a 400, without quoting a body it did not send."""
    try:
        body = json.loads(refused.read())
    except OSError, ValueError:
        return "hub_unreachable", "the Hub answered without a body"
    if not isinstance(body, dict):
        return "hub_unreachable", "the Hub answered without a body"
    found = cast("dict[str, JsonValue]", body)
    return str(found.get("code") or "refused"), str(found.get("message") or "")


_journals: Journals | None = None
_lock = threading.Lock()


def attach(journals: Journals | None) -> None:
    """Name the one Hub this process mirrors to (AD-7): one process, one Hub, like one router."""
    global _journals  # noqa: PLW0603 (the process-wide seam router.adopt uses)
    with _lock:
        _journals = journals


def attached() -> Journals | None:
    """The Hub this process mirrors to, or None when it has none."""
    return _journals
