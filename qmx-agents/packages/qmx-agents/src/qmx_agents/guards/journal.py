"""One serialized, append-only evidence writer per run volume."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from threading import RLock
from typing import Any

from pydantic import BaseModel


def encoded(value: object) -> bytes:
    def serialize(value: object) -> object:
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        raise TypeError(f"Unsupported journal value: {type(value).__name__}")

    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False, default=serialize
    ).encode()


def fingerprint(value: object) -> str:
    return sha256(encoded(value)).hexdigest()


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


class RunJournal:
    def __init__(self, path: Path, run_id: str, *, clock: Callable[[], str] = timestamp) -> None:
        if not run_id.strip():
            raise ValueError("Journal requires a run id")
        self.path = path
        self.run_id = run_id
        self.clock = clock
        self._mutex = RLock()
        self._closed = False
        self._failed = False
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_path = path.with_suffix(path.suffix + ".lock")
        self._owner = self._lock_path.open("x", encoding="utf-8")
        self._sequence = 0
        try:
            if path.exists():
                data = path.read_bytes()
                if data and not data.endswith(b"\n"):
                    raise ValueError("Journal has an incomplete record")
                for line in data.decode("utf-8").splitlines():
                    record: dict[str, Any] = json.loads(line)
                    digest = record.pop("fingerprint")
                    if (
                        digest != fingerprint(record)
                        or record["seq"] != self._sequence + 1
                        or record["run_id"] != run_id
                    ):
                        raise ValueError("Journal identity or sequence is corrupt")
                    self._sequence += 1
        except BaseException:
            self.close()
            raise

    def append(self, event: str, payload: Mapping[str, object]) -> dict[str, Any]:
        with self._mutex:
            if self._closed or self._failed:
                raise OSError("Journal writer is closed or failed")
            record: dict[str, Any] = {
                "seq": self._sequence + 1,
                "run_id": self.run_id,
                "time": self.clock(),
                "event": event,
                "payload": dict(payload),
            }
            record["fingerprint"] = fingerprint(record)
            data = encoded(record) + b"\n"
            try:
                with self.path.open("ab") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
            except OSError:
                # A partial write must never be followed by a fresh sequence.
                self._failed = True
                raise
            self._sequence += 1
            return record

    def store_result(self, data: bytes) -> str:
        with self._mutex:
            if self._closed or self._failed:
                raise OSError("Journal writer is closed or failed")
            folder = self.path.parent / (self.path.name + ".results")
            folder.mkdir(exist_ok=True)
            path = folder / sha256(data).hexdigest()
            if path.exists():
                if path.read_bytes() != data:
                    raise OSError("Result fingerprint mismatch")
            else:
                with path.open("xb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
            return str(path)

    def quarantine(self, data: bytes, reason: str) -> str:
        reference = self.store_result(data)
        self.append("quarantine", {"result_ref": reference, "reason": reason})
        return reference

    def close(self) -> None:
        with self._mutex:
            if not self._closed:
                self._owner.close()
                self._lock_path.unlink()
                self._closed = True

    def __enter__(self) -> RunJournal:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
