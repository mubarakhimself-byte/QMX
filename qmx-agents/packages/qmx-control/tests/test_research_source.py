"""The article job's `outputs` land through the host into the real control Library."""

from __future__ import annotations

import hashlib
import runpy
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any

import httpx
import pytest
from qmx_apps.manifest import Definition
from qmx_engine.ledger import redact
from qmx_library.store import Store as Library

from qmx_control.service import ControlService

APP = Path(__file__).resolve().parents[4] / "examples/apps/mql5-articles"
FIXTURE = Path(__file__).resolve().parents[2] / "qmx-apps/tests/fixtures/mql5-623.html"
URL = "https://www.mql5.com/en/articles/623"
TITLE = "Interview with Sergey Pankratyev (ATC 2012)"

sys.path.insert(0, str(APP))


@pytest.fixture
def control(tmp_path: Path) -> Generator[ControlService]:
    service = ControlService(tmp_path / "home", secret_getter=lambda _service, _name: None)
    with Library.open(tmp_path / "library", redactor=redact) as library:
        service.attach_library(library)
        try:
            yield service
        finally:
            service.close()


def land(control: ControlService, answer: dict[str, Any]) -> list[dict[str, Any]]:
    """What the host does with a job answer that carries `outputs`: land each one."""
    outputs = [(item["output"], item["data"]) for item in answer["outputs"]]
    return control.app_runtime().artifacts.save_all(Definition.load(APP), outputs)


def articles(control: ControlService) -> list[dict[str, Any]]:
    return [item for item in control.library_search() if item["kind"] == "app-output"]


def test_a_saved_article_lands_in_the_real_control_library_once(
    control: ControlService, monkeypatch: pytest.MonkeyPatch
) -> None:
    from collector import Store, parse_article, run_daily

    store = Store(control.home / "apps/mql5-articles")
    (store.root / "data/config.json").write_text('{"crawl": false}', encoding="utf-8")
    metadata, markdown = parse_article(FIXTURE.read_text(encoding="utf-8"), URL)
    store.save(623, FIXTURE.read_bytes(), markdown, metadata)
    monkeypatch.setenv("QMX_VOLUME", str(store.root))

    first = run_daily()
    land(control, first)
    land(control, first)
    again = run_daily()

    [saved] = articles(control)
    assert saved["title"] == "mql5-articles mql5-article"
    assert saved["content"] == {
        "title": TITLE,
        "source_url": URL,
        "sha256": hashlib.sha256(markdown.encode()).hexdigest(),
        "published": "2012-12-27T05:53Z",
        "markdown": markdown,
    }
    assert markdown.startswith(f"# {TITLE}\n")
    assert (again["landed"], again["outputs"]) == (1, [])
    assert store.status()["pending_publication"] == 0


def test_the_daily_entrypoint_respects_robots_and_still_lands_the_saved_article(
    control: ControlService, monkeypatch: pytest.MonkeyPatch
) -> None:
    from collector import Store

    store = Store(control.home / "apps/mql5-articles")
    store.save(623, b"<article>saved</article>", "# Saved\n", {"title": "Saved"})
    calls: list[str] = []

    def mql5(_transport: httpx.HTTPTransport, request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, text="User-agent: *\nDisallow: /\n")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", mql5)
    monkeypatch.setenv("QMX_VOLUME", str(store.root))
    answer = runpy.run_path(str(APP / "jobs/daily.py"))["run"]()
    land(control, answer)

    assert calls == ["https://www.mql5.com/robots.txt"]
    assert {key: value for key, value in answer.items() if key != "outputs"} == {
        "discovered": 0,
        "fetched": 0,
        "deferred": 0,
        "seeded": 0,
        "landed": 0,
    }
    assert [item["content"]["title"] for item in articles(control)] == ["Saved"]
    assert [item["content"]["source_url"] for item in articles(control)] == [URL]
