from __future__ import annotations

import gzip
import hashlib
import json
import sqlite3
from contextlib import closing
from itertools import pairwise
from pathlib import Path
from typing import Any, cast

import httpx
import pytest
from collector import BASE, Store, article_url, collect, parse_article, run_daily

from qmx_apps.artifacts import Artifacts, Landing
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
    assert definition.manifest.suggested_trigger is not None
    assert definition.manifest.suggested_trigger.seconds == 86400
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


def volume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, settings: object) -> Store:
    """The app's volume where the host keeps it, `<home>/apps/mql5-articles`, as the job sees it."""
    root = tmp_path / "home/apps/mql5-articles"
    store = Store(root)
    (root / "data/config.json").write_text(json.dumps(settings), encoding="utf-8")
    monkeypatch.setenv("QMX_VOLUME", str(root))
    return store


def saved(store: Store, *ids: int) -> None:
    for article_id in ids:
        markdown = f"# Article {article_id}\n"
        store.save(article_id, b"<html></html>", markdown, {"title": f"Article {article_id}"})


def answered(outputs: list[dict[str, Any]]) -> list[str]:
    return [str(item["data"]["source_url"]).rsplit("/", 1)[1] for item in outputs]


def test_the_daily_job_answers_unlanded_articles_until_the_host_stored_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = volume(tmp_path, monkeypatch, {"crawl": False, "publish": {"per_run": 2}})
    saved(store, 9, 2, 5)
    host = Artifacts(tmp_path / "home")
    definition = Definition.load(APP)

    first = run_daily()
    again = run_daily()
    for item in first["outputs"][:1]:
        host.save(definition, item["output"], item["data"])
    after = run_daily()

    assert answered(first["outputs"]) == ["2", "5"]
    assert first["outputs"][0] == {
        "output": "mql5-article",
        "data": {
            "title": "Article 2",
            "source_url": article_url(2),
            "sha256": hashlib.sha256(b"# Article 2\n").hexdigest(),
            "published": "",
            "markdown": "# Article 2\n",
        },
    }
    assert (first["landed"], answered(again["outputs"])) == (0, ["2", "5"])
    assert (after["landed"], answered(after["outputs"])) == (1, ["5", "9"])
    assert store.status()["pending_publication"] == 2


def test_an_article_whose_library_landing_failed_is_answered_again_and_lands_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = volume(tmp_path, monkeypatch, {"crawl": False})
    saved(store, 7)
    definition = Definition.load(APP)
    landings: list[str] = []
    down = [True]

    def library(landing: Landing) -> str:
        if down[0]:
            raise RuntimeError("the Library is down")
        landings.append(str(cast(dict[str, Any], landing.data)["source_url"]))
        return f"library-{len(landings)}"

    host = Artifacts(tmp_path / "home", library)
    first = run_daily()
    with pytest.raises(RuntimeError, match="the Library is down"):
        host.save_all(definition, [(item["output"], item["data"]) for item in first["outputs"]])
    down[0] = False
    again = run_daily()
    host.save_all(definition, [(item["output"], item["data"]) for item in again["outputs"]])
    after = run_daily()

    assert (again["landed"], answered(again["outputs"])) == (0, ["7"])
    assert landings == [article_url(7)]
    assert (after["landed"], after["outputs"]) == (1, [])
    assert store.status()["pending_publication"] == 0


@pytest.mark.parametrize(
    "config", [[1, 2], {"publish": 5}, {"publish": {"per_run": True}}, {"crawl": "no"}]
)
def test_a_config_that_is_not_the_documented_shape_is_refused_in_words(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, config: Any
) -> None:
    volume(tmp_path, monkeypatch, config)

    with pytest.raises(ValueError, match=r"publish\.per_run to 1 or more"):
        run_daily()


def test_one_run_answers_at_most_per_run_articles_and_an_unreachable_site_still_lands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = volume(tmp_path, monkeypatch, {})
    saved(store, *range(1, 202))

    def offline(*args: Any, **kwargs: Any) -> None:
        raise httpx.ConnectError("the network is off")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", offline)
    ran = run_daily()

    assert (ran["crawl_error"], ran["fetched"]) == ("ConnectError", 0)
    assert answered(ran["outputs"]) == [str(article_id) for article_id in range(1, 201)]


def test_an_article_the_old_library_door_saved_stays_landed(tmp_path: Path) -> None:
    root = tmp_path / "volume"
    root.mkdir()
    with closing(sqlite3.connect(root / "app.db")) as db, db:
        db.execute(
            "CREATE TABLE articles (id INTEGER PRIMARY KEY, url TEXT UNIQUE NOT NULL, "
            "metadata TEXT NOT NULL, status TEXT NOT NULL, raw TEXT, markdown TEXT, "
            "library_id TEXT)"
        )
        db.execute(
            "INSERT INTO articles VALUES(1, ?, '{}', 'ready', 'blobs/a.html', 'blobs/a.md', 'x')",
            (article_url(1),),
        )

    store = Store(root)

    assert store.status()["pending_publication"] == 0
    assert store.outbox(200) == []
