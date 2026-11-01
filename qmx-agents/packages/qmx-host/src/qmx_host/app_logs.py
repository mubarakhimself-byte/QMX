"""The host's log shipper (Part C slice C-04, Level 0 AD-42): every app's JSONL log lines and the
engine's open incidents, sent through the one telemetry switch to this machine's OpenObserve.

Apps keep writing their logs in their volume (`apps/<id>/logs/*.jsonl`, the supervisor's own
`supervisor.jsonl` among them); the host reads them and hands each line, as one OTLP log, to the
process's one exporter (`qmx_engine.telemetry`). The files are the queue: the shipper hands no
more lines than the exporter has room for, keeps a byte cursor per file in `logs/app-logs.json`,
and leaves the rest on disk for the next pass. Nothing waits on OpenObserve: the exporter posts
on its own thread with its own timeout, and a post that fails drops its batch and counts it in
`logs/telemetry.json`. With `[telemetry] send_to = "off"` nothing is read and nothing is sent.

Every line is redacted before it leaves: the engine's one redaction (AD-37) over every string,
and the value of any field whose name says it holds a secret.
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, cast

from pydantic import JsonValue
from qma.harness.home import DoctorLine
from qma.telemetry import OFF, target
from qmx_control.service import open_incidents
from qmx_engine import telemetry
from qmx_engine.ledger import redact

STATE: Final = "logs/app-logs.json"
"""The shipper's cursors and counters under the home."""
EVERY_S: Final = 1.0
"""`[telemetry] ship_every_s`: how often the host looks for new lines."""
KIND: Final = "app_log"
INCIDENT: Final = "incident"
SECRET_WORDS: Final = frozenset(
    {
        "apikey",
        "auth",
        "authorization",
        "bearer",
        "cookie",
        "credential",
        "credentials",
        "key",
        "passphrase",
        "passwd",
        "password",
        "pwd",
        "secret",
        "token",
    }
)
"""A field whose name holds one of these words has its value sent as `[redacted]`, whatever its
shape, since a password or a short key has no shape the text pass knows."""
WORDS: Final = re.compile(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])")
APP_ID: Final = re.compile(r"[a-z0-9][a-z0-9-]*")

type Exporter = Callable[[], telemetry.Telemetry | None]


def secret_named(name: str) -> bool:
    """`api_key`, `X-Auth-Token`, `clientSecret` and `password` are; `monkey` and `tokens_in`
    are not."""
    return any(word.lower() in SECRET_WORDS for word in WORDS.findall(name))


def scrubbed(value: JsonValue) -> JsonValue:
    """`value` with every secret-named field's value masked, at any depth."""
    if isinstance(value, dict):
        return {
            key: redact.MASK if secret_named(key) and item is not None else scrubbed(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [scrubbed(item) for item in value]
    return value


def record_of(line: str, app_id: str, file: str) -> str:
    """One log line as the JSON text the exporter takes: its own fields, the app and the file it
    came from, secret-named values masked and every string redacted. A line that is not a JSON
    object is sent as its message."""
    try:
        parsed: object = json.loads(line)
    except ValueError:
        parsed = None
    fields = cast("dict[str, JsonValue]", parsed) if isinstance(parsed, dict) else {"message": line}
    at = fields.get("at")
    if at is not None and not _instant(at):
        fields = {**{k: v for k, v in fields.items() if k != "at"}, "app_at": at}
    clean, _ = redact.redact_json(scrubbed({**fields, "app_id": app_id, "log_file": file}))
    return json.dumps(clean, sort_keys=True)


def _instant(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def incident_record(row: Mapping[str, object]) -> str:
    """One open incident as an OTLP log: its title as the message, at the time last seen."""
    fields = {**row, "message": row.get("title"), "level": "error", "at": row.get("last_seen")}
    clean, _ = redact.redact_json(scrubbed(cast("JsonValue", fields)))
    return json.dumps(clean, sort_keys=True)


class AppLogs:
    """One home's shipper. Not thread-safe: one caller, the host's shipping task."""

    def __init__(
        self,
        home: Path,
        settings: Callable[[], Mapping[str, object]] = dict,
        *,
        exporter: Exporter | None = None,
        switch: Callable[[], str] | None = None,
    ) -> None:
        self.home = home
        self.settings = settings
        self.exporter: Exporter = exporter or (lambda: telemetry.opened(home))
        self.switch = switch or (lambda: target(home))
        self.cursors: dict[str, int] = {}
        self.shipped = 0
        self.incidents: dict[str, tuple[object, object]] = {}
        self._load()

    @property
    def state(self) -> Path:
        return self.home / STATE

    def every_s(self) -> float:
        found = self.settings().get("ship_every_s", EVERY_S)
        return float(found) if isinstance(found, int | float) and found > 0 else EVERY_S

    def tick(self) -> int:
        """Hand every new line the exporter has room for, then the incidents that changed, and
        record where each file got to. Returns how many records were handed."""
        if self.switch() == OFF:
            return 0
        found = self.exporter()
        if found is None:
            return 0
        room = telemetry.CAPACITY - _held(found)
        handed = 0
        files = self._files()
        self.cursors = {name: at for name, at in self.cursors.items() if name in files}
        for name, path in files.items():
            if handed >= room:
                break
            try:
                handed += self._ship(found, name, path, room - handed)
            except OSError as error:
                print(f"app logs: {name} was not read this pass: {error}", file=sys.stderr)
        if handed < room:
            handed += self._ship_incidents(found, room - handed)
        self.shipped += handed
        self._save()
        return handed

    async def run(self) -> None:
        """Ship until cancelled. A pass that fails is skipped; the next one starts where the
        cursors say."""
        while True:
            try:
                await asyncio.to_thread(self.tick)
            except (OSError, ValueError) as error:
                print(f"app logs: a shipping pass was skipped: {error}", file=sys.stderr)
            await asyncio.sleep(self.every_s())

    def doctor_line(self) -> DoctorLine:
        """The doctor's deep-logs row: off as off, or what was shipped and what was lost."""
        if self.switch() == OFF:
            return DoctorLine(
                "deep logs", True, "Telemetry off: [telemetry] send_to is off, so nothing is sent"
            )
        found = telemetry.process()
        stats = found.stats() if found is not None else {}
        dropped = stats.get("dropped", 0)
        lost = dropped if isinstance(dropped, int) else 0
        return DoctorLine(
            "deep logs",
            lost == 0,
            f"Telemetry on to {stats.get('endpoint') or self.switch()}: {self.shipped} app log "
            f"lines and incidents shipped since the host started from {len(self.cursors)} files; "
            f"{lost} records dropped",
        )

    def _files(self) -> dict[str, Path]:
        """Every app volume's JSONL logs, by their path under the home."""
        apps = self.home / "apps"
        if not apps.is_dir():
            return {}
        return {
            path.relative_to(self.home).as_posix(): path
            for path in sorted(apps.glob("*/logs/*.jsonl"))
            if APP_ID.fullmatch(path.parent.parent.name) and path.is_file()
        }

    def _ship(self, found: telemetry.Telemetry, name: str, path: Path, room: int) -> int:
        offset = self.cursors.get(name, 0)
        if path.stat().st_size < offset:
            offset = 0
        handed = 0
        app_id = path.parent.parent.name
        with path.open("rb") as file:
            file.seek(offset)
            while handed < room:
                raw = file.readline()
                if not raw.endswith(b"\n"):
                    break
                offset += len(raw)
                line = raw.decode("utf-8", errors="replace").strip()
                if line:
                    found.hand(KIND, record_of(line, app_id, path.name))
                    handed += 1
        self.cursors[name] = offset
        return handed

    def _ship_incidents(self, found: telemetry.Telemetry, room: int) -> int:
        handed = 0
        for row in open_incidents(self.home):
            if handed >= room:
                break
            key, seen = str(row["id"]), (row.get("count"), row.get("last_seen"))
            if self.incidents.get(key) == seen:
                continue
            found.hand(INCIDENT, incident_record(row))
            self.incidents[key] = seen
            handed += 1
        return handed

    def _load(self) -> None:
        try:
            document: object = json.loads(self.state.read_text(encoding="utf-8"))
        except OSError, ValueError:
            return
        cursors = cast("dict[str, object]", document).get("cursors")
        if isinstance(cursors, dict):
            self.cursors = {
                str(name): offset
                for name, offset in cast("dict[str, object]", cursors).items()
                if isinstance(offset, int) and offset >= 0
            }

    def _save(self) -> None:
        document = {
            "cursors": self.cursors,
            "shipped": self.shipped,
            "at": datetime.now(UTC).isoformat(),
        }
        try:
            self.state.parent.mkdir(parents=True, exist_ok=True)
            scratch = self.state.with_suffix(".tmp")
            scratch.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
            scratch.replace(self.state)
        except OSError as error:
            print(f"app logs: the cursors were not saved: {error}", file=sys.stderr)


def _held(found: telemetry.Telemetry) -> int:
    held = found.stats().get("held", 0)
    return held if isinstance(held, int) else 0
