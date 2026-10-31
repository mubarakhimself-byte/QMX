"""Hindsight keeps every file in the QMX folder's parts (design 62 A3), never in his profile."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import BinaryIO

import pytest
from qmx_home import Layout

import qmx_memory.hindsight
from qmx_memory.hindsight import HindsightConfig, HindsightIndex

PLACED = ("HF_HOME", "SENTENCE_TRANSFORMERS_HOME", "HINDSIGHT_API_DAEMON_LOG")


def test_the_index_runs_on_the_folders_database_and_stops_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in PLACED:
        monkeypatch.delenv(name, raising=False)
    layout = Layout(tmp_path / "QMX")
    seen: dict[str, object] = {}
    databases: list[str] = []

    class Server:
        url = "http://127.0.0.1:1"

        def __init__(self, **kwargs: object) -> None:
            seen.update(db_url=kwargs["db_url"], **{name: os.environ[name] for name in PLACED})

        def start(self, *, timeout: float) -> None:
            seen["started"] = timeout

        def stop(self) -> None:
            databases.append("server stopped")

    class Client:
        def __init__(self, **_: object) -> None: ...
        def create_bank(self, **_: object) -> None: ...
        def close(self) -> None: ...

    monkeypatch.setitem(
        sys.modules, "hindsight", SimpleNamespace(HindsightServer=Server, HindsightClient=Client)
    )

    def start(config: HindsightConfig) -> str:
        databases.append(f"started in {config.database}")
        return "postgresql://hindsight@127.0.0.1:5433/hindsight"

    def stop(_: HindsightConfig) -> None:
        databases.append("stopped")

    monkeypatch.setattr(qmx_memory.hindsight, "start_database", start)
    monkeypatch.setattr(qmx_memory.hindsight, "stop_database", stop)

    index = HindsightIndex(HindsightConfig(layout))
    index.start()
    index.close()

    models = str(layout.cache / "models" / "huggingface")
    assert seen == {
        "db_url": "postgresql://hindsight@127.0.0.1:5433/hindsight",
        "HF_HOME": models,
        "SENTENCE_TRANSFORMERS_HOME": models,
        "HINDSIGHT_API_DAEMON_LOG": str(layout.logs / "hindsight" / "daemon.log"),
        "started": 600.0,
    }
    assert databases == [
        f"started in {layout.root / 'data' / 'memory' / 'hindsight' / 'pg'}",
        "server stopped",
        "stopped",
    ]


def test_pg0_starts_on_the_folders_database_under_its_own_name_and_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout = Layout(tmp_path / "QMX")
    config = HindsightConfig(layout)
    package = tmp_path / "site" / "pg0"
    monkeypatch.setitem(sys.modules, "pg0", SimpleNamespace(__file__=str(package / "__init__.py")))
    calls: list[tuple[list[str], str]] = []

    def call(argv: list[str], *, stdout: BinaryIO, env: dict[str, str], **_: object) -> int:
        calls.append((argv[1:], env["HOME"]))
        if argv[1] == "info":
            stdout.write(b'{"uri": "postgresql://hindsight@127.0.0.1:5433/hindsight"}')
        return 0

    monkeypatch.setattr(qmx_memory.hindsight.subprocess, "call", call)

    uri = qmx_memory.hindsight.start_database(config)

    database = str(layout.root / "data" / "memory" / "hindsight" / "pg")
    home = str(layout.root / "cache" / "pg0")
    name = config.instance
    assert uri == "postgresql://hindsight@127.0.0.1:5433/hindsight"
    assert name.startswith("qmx-") and len(name) == len("qmx-") + 12
    assert calls == [
        (
            ["start", "--name", name, "--username", "hindsight", "--password", "hindsight",
             "--database", "hindsight", "--data-dir", database],
            home,
        ),
        (["info", "--name", name, "-o", "json"], home),
    ]  # fmt: skip
