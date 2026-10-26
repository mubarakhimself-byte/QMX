"""Hindsight traces only where `[telemetry] send_to` names a target (design 62 E1)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from qmx_home import Layout

import qmx_memory.hindsight
from qmx_memory.hindsight import HindsightConfig, HindsightIndex

NAMES = (
    "HINDSIGHT_API_OTEL_TRACES_ENABLED",
    "HINDSIGHT_API_OTEL_EXPORTER_OTLP_ENDPOINT",
    "HINDSIGHT_API_OTEL_SERVICE_NAME",
)
ISOLATED = (
    *NAMES,
    "HF_HOME",
    "SENTENCE_TRANSFORMERS_HOME",
    "HINDSIGHT_API_EMBEDDINGS_PROVIDER",
    "HINDSIGHT_API_RERANKER_PROVIDER",
    "HINDSIGHT_API_ENABLE_OBSERVATIONS",
    "HINDSIGHT_API_DAEMON_LOG",
)


class Stopped(Exception):
    pass


def tracing_at_start(config: HindsightConfig, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """The tracing names Hindsight's server would read, captured where it is built. The stand-in
    package keeps the real one, which takes minutes to import, out of a unit test."""
    for name in ISOLATED:
        monkeypatch.delenv(name, raising=False)
    seen: dict[str, str] = {}

    def server(**_: object) -> None:
        seen.update({name: os.environ[name] for name in NAMES if name in os.environ})
        raise Stopped

    monkeypatch.setitem(
        sys.modules, "hindsight", SimpleNamespace(HindsightServer=server, HindsightClient=None)
    )

    def database(_: HindsightConfig) -> str:
        return "postgresql://db"

    monkeypatch.setattr(qmx_memory.hindsight, "start_database", database)
    with pytest.raises(Stopped):
        HindsightIndex(config).start()
    return seen


def test_hindsight_traces_only_to_the_target_it_is_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    off = tracing_at_start(HindsightConfig(Layout(tmp_path / "off")), monkeypatch)
    on = tracing_at_start(
        HindsightConfig(Layout(tmp_path / "on"), telemetry="http://127.0.0.1:5080/api/default"),
        monkeypatch,
    )

    assert off == {}
    assert on == {
        "HINDSIGHT_API_OTEL_TRACES_ENABLED": "1",
        "HINDSIGHT_API_OTEL_EXPORTER_OTLP_ENDPOINT": "http://127.0.0.1:5080/api/default",
        "HINDSIGHT_API_OTEL_SERVICE_NAME": "qmx-memory",
    }
