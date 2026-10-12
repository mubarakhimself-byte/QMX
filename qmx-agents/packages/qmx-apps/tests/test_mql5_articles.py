from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
from itertools import pairwise
from pathlib import Path
from typing import Any

import httpx
import pytest
from collector import BASE, Store, article_url, collect, parse_article
from fastmcp import Client, FastMCP

from qmx_apps.manifest import Definition

FIXTURE = Path(__file__).with_name("fixtures") / "mql5-623.html"
APP = Path(__file__).resolve().parents[4] / "examples/apps/mql5-articles"


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def refused(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Tests must use MockTransport or in-process MCP.")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", refused)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", refused)


def test_saved_archive_html_and_valid_daily_schedule() -> None:
    html = FIXTURE.read_text(encoding="utf-8").replace(
        "</article>",
        '<div class="article-tools-panel">REMOVE_TOOLS</div>'
        '<script>REMOVE_SCRIPT</script><a href="/en/articles/7">Reference</a></article>',
    )
    metadata, markdown = parse_article(html, article_url(623))
    assert metadata["title"] == "Interview with Sergey Pankratyev (ATC 2012)"
    assert metadata["published"].startswith("2012")
    assert "# Interview" in markdown
    assert "REMOVE_TOOLS" not in markdown and "REMOVE_SCRIPT" not in markdown
    assert f"[Reference]({BASE}/en/articles/7)" in markdown
    definition = Definition.load(APP)
    assert definition.manifest.kind == "headless"
    assert definition.manifest.entrypoints.jobs == ["jobs/daily.py"]
    assert definition.manifest.schedule is not None
    assert definition.manifest.schedule.interval_seconds == 86400
    with pytest.raises(ValueError, match="article root"):
        parse_article("<html>login page</html>", article_url(623))


def archive(store: Store) -> None:
    root = store.root / "data/seed"
    (root / "md").mkdir(parents=True)
    (root / "raw").mkdir()
    markdown = "# Previously saved\n\nArchived research.\n"
    (root / "md/1.md").write_bytes(markdown.replace("\n", "\r\n").encode())
    (root / "raw/1.html.gz").write_bytes(gzip.compress(FIXTURE.read_bytes()))
    (root / "catalog.jsonl").write_text(
        json.dumps(
            {
                "id": 1,
                "url": article_url(1),
                "title": "Previous",
                "fetch_status": "ok",
                "sha256": hashlib.sha256(markdown.encode()).hexdigest(),
            }
        )
        + "\n"
        + json.dumps({"id": 999991, "url": article_url(999991), "fetch_status": "failed"})
        + "\n",
        encoding="utf-8",
    )


def test_seed_dedupe_conditional_requests_and_rate_limits(tmp_path: Path) -> None:
    store = Store(tmp_path)
    assert store.status()["known"] == 3057
    archive(store)
    assert store.seed() == 1 and store.seed() == 0
    now = [1000.0]
    calls: list[tuple[str, float]] = []
    listing = (
        '<a href="/en/articles/623">bundled</a><a href="/en/articles/1">imported</a>'
        '<a href="/en/articles/999991?tracking=1">retry failed</a>'
        '<a href="https://other.test/en/articles/999992">external</a>'
    )

    def sleep(seconds: float) -> None:
        now[0] += seconds

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        calls.append((path, now[0]))
        assert request.headers["User-Agent"].startswith("QMXMQL5Research/")
        if path == "/robots.txt":
            if "If-None-Match" in request.headers:
                assert request.headers["If-None-Match"] == '"robots"'
                return httpx.Response(304)
            return httpx.Response(
                200,
                text="User-agent: *\nCrawl-delay: 5\nRequest-rate: 1/10\n",
                headers={"ETag": '"robots"'},
            )
        if path == "/en/articles":
            if "If-None-Match" in request.headers:
                assert request.headers["If-Modified-Since"] == "Thu, 08 Oct 2026 00:00:00 GMT"
                return httpx.Response(304)
            return httpx.Response(
                200,
                text=listing,
                headers={"ETag": '"listing"', "Last-Modified": "Thu, 08 Oct 2026 00:00:00 GMT"},
            )
        assert path == "/en/articles/999991"
        return httpx.Response(200, content=FIXTURE.read_bytes())

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        first = collect(store, http, pages=1, clock=lambda: now[0], sleep=sleep)
        second = collect(store, http, pages=1, clock=lambda: now[0], sleep=sleep)
    assert first["fetched"] == 1 and second["fetched"] == 0
    assert [path for path, _ in calls].count("/en/articles/999991") == 1
    assert all(later[1] - earlier[1] >= 10 for earlier, later in pairwise(calls))
    with store.db() as db:
        row = db.execute("SELECT * FROM articles WHERE id=999991").fetchone()
        assert row is not None and row["status"] == "ready"
        assert (store.root / row["raw"]).read_bytes() == FIXTURE.read_bytes()
        assert "# Interview" in (store.root / row["markdown"]).read_text(encoding="utf-8")
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


@pytest.mark.parametrize("status", [200, 500, 429])
def test_robots_fail_closed_and_retry_after_survives_restart(tmp_path: Path, status: int) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        assert request.url.path == "/robots.txt"
        return httpx.Response(
            status, text="User-agent: *\nDisallow: /en/articles\n", headers={"Retry-After": "120"}
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        store = Store(tmp_path)

        def run() -> dict[str, int]:
            return collect(store, http, clock=lambda: 1000, sleep=lambda seconds: None)

        if status == 500:
            with pytest.raises(httpx.HTTPStatusError):
                run()
        else:
            result = run()
            assert result["fetched"] == 0
        if status == 429:
            assert Store(tmp_path).state("blocked_until") == 1120
            assert run()["deferred"] == 1
            assert calls == ["/robots.txt"]


def test_seed_checksum_failure_is_not_silently_marked_ready(tmp_path: Path) -> None:
    store = Store(tmp_path)
    archive(store)
    (tmp_path / "data/seed/md/1.md").write_text("damaged", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        store.seed()
    assert store.status()["available"] == 0


def test_real_mcp_library_outbox_recovers_a_lost_acknowledgement(tmp_path: Path) -> None:
    store = Store(tmp_path)
    metadata, markdown = parse_article(FIXTURE.read_text(encoding="utf-8"), article_url(1))
    metadata["title"] = "x" * 300
    store.save(1, FIXTURE.read_bytes(), markdown, metadata)
    library = FastMCP("recorded-library")
    items: list[dict[str, Any]] = []
    lost = [True]

    @library.tool
    def library_search(query: str, limit: int = 1000) -> list[dict[str, Any]]:
        """Search the recorded Library."""
        return [item for item in items if query in json.dumps(item)][:limit]

    @library.tool
    def library_save(item: dict[str, Any]) -> dict[str, Any]:
        """Persist a recorded artifact, then simulate a lost response."""
        item = {
            "id": f"artifact-{len(items) + 1}",
            **item,
        }
        items.append(item)
        if lost[0]:
            lost[0] = False
            raise RuntimeError("lost response")
        return item

    assert callable(library_search) and callable(library_save)

    async def run() -> None:
        async with Client(library) as client:
            with pytest.raises(Exception, match="lost response"):
                await store.publish(client)
            assert store.status()["pending_publication"] == 1
            assert await store.publish(client) == 1
            assert await store.publish(client) == 0

    asyncio.run(run())
    assert len(items) == 1 and len(items[0]["title"]) == 200
    assert items[0]["content"]["source_url"] == article_url(1)
    assert items[0]["content"]["markdown"] == markdown
    assert store.status()["pending_publication"] == 0
