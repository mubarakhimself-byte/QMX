"""The article outbox uses the real control service's MCP schema."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

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
