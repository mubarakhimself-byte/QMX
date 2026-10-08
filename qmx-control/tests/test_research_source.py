"""The article outbox uses the real control service's MCP schema."""

from __future__ import annotations

import asyncio
import json
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from fastmcp import Client

from qmx_control.server import create_mcp
from qmx_control.service import ControlService

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "examples/apps/mql5-articles"))


def test_article_publishes_to_real_control_library(tmp_path: Path) -> None:
    from collector import Store, article_url, parse_article

    source = Path(__file__).resolve().parents[2] / "qmx-apps/tests/fixtures/mql5-623.html"
    store = Store(tmp_path / "app")
    metadata, markdown = parse_article(source.read_text(encoding="utf-8"), article_url(623))
    store.save(623, source.read_bytes(), markdown, metadata)
    service = ControlService(tmp_path / "control")

    async def run() -> None:
        async with Client(create_mcp(service)) as client:
            assert await store.publish(client) == 1
            assert await store.publish(client) == 0

    asyncio.run(run())
    saved = service.library_search(article_url(623))
    assert len(saved) == 1
    assert saved[0]["kind"] == "article"
    content = saved[0]["content"]
    assert isinstance(content, dict)
    assert content["markdown"] == markdown
    assert content["source_url"] == article_url(623)
    assert content["title"] == metadata["title"]
    assert store.status()["pending_publication"] == 0


def test_daily_entrypoint_publishes_offline_and_respects_robots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import collector

    app = Path(__file__).resolve().parents[2] / "examples/apps/mql5-articles"
    store = collector.Store(tmp_path / "app")
    store.save(623, b"<article>saved</article>", "# Saved", {"title": "Saved"})
    service = ControlService(tmp_path / "control")
    calls: list[str] = []

    def library(url: str, *, auth: str) -> Client[Any]:
        assert url == "http://127.0.0.1:8766/mcp/" and auth == "fixture-token"
        return Client(create_mcp(service))

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        assert request.url.path == "/robots.txt"
        return httpx.Response(200, text="User-agent: *\nDisallow: /\n")

    def http(*, timeout: float) -> httpx.Client:
        assert timeout == 20
        return httpx.Client(transport=httpx.MockTransport(respond))

    monkeypatch.setenv("QMX_VOLUME", str(store.root))
    monkeypatch.setenv("QMX_CONTROL_TOKEN", "fixture-token")
    monkeypatch.setattr(collector, "Client", library)
    monkeypatch.setattr(collector, "httpx", SimpleNamespace(Client=http))
    namespace = runpy.run_path(str(app / "jobs/daily.py"))
    namespace["run"]()
    result = json.loads(capsys.readouterr().out)
    assert result == {"discovered": 0, "fetched": 0, "deferred": 0, "seeded": 0, "published": 1}
    assert calls == ["https://www.mql5.com/robots.txt"]
    assert len(service.library_search(collector.article_url(623))) == 1
