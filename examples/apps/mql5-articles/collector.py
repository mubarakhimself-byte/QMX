"""One instance owns the article catalog, HTTP cache and Library outbox.

The daily job answers its articles as job `outputs`, and the host lands each as one
`mql5-article` artifact. The app holds no host credential and calls no host door.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import sqlite3
import threading
import time
from collections.abc import Callable, Generator
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup, Tag
from markdownify import markdownify

BASE = "https://www.mql5.com"
AGENT = "QMXMQL5Research/1.0 (+https://github.com/MubarakHimself/QMX)"
RUN_LOCK = threading.Lock()
ARTICLE = "mql5-article"
"""The provides name each article lands under."""
PER_RUN = 200
"""`publish.per_run`'s starting default: how many articles one daily job answers."""


def article_url(article_id: int) -> str:
    if article_id <= 0:
        raise ValueError("Article ids must be positive.")
    return f"{BASE}/en/articles/{article_id}"


def attribute(tag: Tag | None, name: str) -> str:
    value = tag.get(name) if tag else None
    return value if isinstance(value, str) else ""


def parse_article(html: str, url: str) -> tuple[dict[str, Any], str]:
    """Adapt the archived library's selectors and markdown conversion."""
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one("article.articles-content") or soup.select_one("article")
    if article is None:
        raise ValueError("No article root in the saved page.")
    for node in article.select(
        ".article-tools-panel, .article__author-with-articles, .article__last-comments, "
        ".other-author-articles, .similar-author-articles, #popupRegisterLogin, "
        "script, style, noscript"
    ):
        node.decompose()

    def meta(name: str, key: str = "property") -> str:
        return attribute(soup.find("meta", attrs={key: name}), "content")

    heading = article.select_one("h1")
    title = heading.get_text(" ", strip=True) if heading else meta("og:title")
    if not title:
        raise ValueError("No article title in the saved page.")
    author = soup.select_one(".article-footer__author-name a")
    author_url = urljoin(url, attribute(author, "href")) if author else meta("article:author")
    published = article.select_one(".article-header__info time")
    info = article.select_one(".article-header__info")
    sections = [node.get_text(" ", strip=True) for node in info.select("a")] if info else []
    for node in article.select("a[href], img[src]"):
        name = "src" if node.name == "img" else "href"
        target = urljoin(url, attribute(node, name))
        if urlsplit(target).scheme in {"http", "https"}:
            node[name] = target
        else:
            del node[name]
    markdown = re.sub(
        r"\n{3,}", "\n\n", markdownify(str(article), heading_style="ATX", bullets="-")
    ).strip()
    if not markdown:
        raise ValueError("Empty article markdown.")
    return {
        "title": title,
        "source_url": url,
        "source": "mql5",
        "author": author.get_text(" ", strip=True) if author else author_url.rsplit("/", 1)[-1],
        "author_url": author_url,
        "published": attribute(published, "datetime") or meta("article:published_time"),
        "description": meta("og:description") or meta("description", "name"),
        "platform": sections[0] if sections else meta("article:section"),
        "section": sections[1] if len(sections) > 1 else "",
        "tags": [attribute(tag, "content") for tag in soup.select('meta[property="article:tag"]')],
    }, markdown


class Store:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        (self.root / "blobs").mkdir(parents=True, exist_ok=True)
        (self.root / "data").mkdir(exist_ok=True)
        with self.db() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY, url TEXT UNIQUE NOT NULL,
                    metadata TEXT NOT NULL, status TEXT NOT NULL,
                    raw TEXT, markdown TEXT, landed TEXT, sent TEXT);
                CREATE TABLE IF NOT EXISTS http (
                    url TEXT PRIMARY KEY, etag TEXT, modified TEXT, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value REAL NOT NULL);
            """)
            columns = {row[1] for row in db.execute("PRAGMA table_info(articles)")}
            if "library_id" in columns:
                # A row the old Library door saved stays landed.
                db.execute("ALTER TABLE articles RENAME COLUMN library_id TO landed")
            if "sent" not in columns:
                db.execute("ALTER TABLE articles ADD COLUMN sent TEXT")
            seed = json.loads(Path(__file__).with_name("seed-ids.json").read_text(encoding="utf-8"))
            db.executemany(
                "INSERT OR IGNORE INTO articles(id,url,metadata,status) VALUES(?,?,?,'seeded')",
                (
                    (item, article_url(item), json.dumps({"source_url": article_url(item)}))
                    for item in seed["ids"]
                ),
            )

    @contextmanager
    def db(self) -> Generator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.root / "app.db", timeout=5)) as db, db:
            db.row_factory = sqlite3.Row
            yield db

    def blob(self, content: bytes, suffix: str) -> str:
        name = f"blobs/{hashlib.sha256(content).hexdigest()}.{suffix}"
        path = self.root / name
        if not path.exists():
            temporary = path.with_suffix(".tmp")
            temporary.write_bytes(content)
            temporary.replace(path)
        elif path.read_bytes() != content:
            raise ValueError("An existing content-addressed blob is corrupt.")
        return name

    def state(self, key: str) -> float:
        with self.db() as db:
            row = db.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
            return float(row[0]) if row else 0

    def set_state(self, key: str, value: float) -> None:
        with self.db() as db:
            db.execute("INSERT OR REPLACE INTO state VALUES(?,?)", (key, value))

    def save(self, article_id: int, raw: bytes, markdown: str, metadata: dict[str, Any]) -> None:
        raw_path = self.blob(raw, "html")
        md_path = self.blob(markdown.encode("utf-8"), "md")
        metadata = {
            **metadata,
            "source_url": article_url(article_id),
            "source": "mql5",
            "sha256": Path(md_path).stem,
            "raw_sha256": Path(raw_path).stem,
            "fetched_at": metadata.get("fetched_at") or datetime.now(UTC).isoformat(),
        }
        with self.db() as db:
            db.execute(
                "INSERT INTO articles(id,url,metadata,status,raw,markdown) "
                "VALUES(?,?,?,'ready',?,?) "
                "ON CONFLICT(id) DO UPDATE SET metadata=excluded.metadata,status='ready',"
                "raw=excluded.raw,markdown=excluded.markdown",
                (article_id, article_url(article_id), json.dumps(metadata), raw_path, md_path),
            )

    def seed(self, limit: int = 500) -> int:
        """Import successful archived files offline; failed rows stay eligible for fetching."""
        archive = self.root / "data/seed"
        catalog = archive / "catalog.jsonl"
        if not catalog.exists():
            return 0
        count = 0
        with catalog.open(encoding="utf-8") as file, self.db() as db:
            for line in file:
                row = json.loads(line)
                if row.get("fetch_status") != "ok":
                    continue
                article_id = int(row["id"])
                current = db.execute(
                    "SELECT raw FROM articles WHERE id=?", (article_id,)
                ).fetchone()
                if current and current[0]:
                    continue
                if row["url"] != article_url(article_id):
                    raise ValueError("Seed article URL does not match its id.")
                paths = [archive / f"md/{article_id}.md", archive / f"raw/{article_id}.html.gz"]
                if any(not path.resolve().is_relative_to(archive.resolve()) for path in paths):
                    raise ValueError("Seed files must stay inside data/seed.")
                markdown = paths[0].read_text(encoding="utf-8")
                # The old Windows exporter hashed text before newline conversion.
                if hashlib.sha256(markdown.encode("utf-8")).hexdigest() != row["sha256"]:
                    raise ValueError(f"Seed markdown checksum mismatch for article {article_id}.")
                self.save(article_id, gzip.decompress(paths[1].read_bytes()), markdown, row)
                count += 1
                if count >= limit:
                    break
        return count

    def status(self) -> dict[str, int]:
        with self.db() as db:
            return {
                "known": int(db.execute("SELECT count(*) FROM articles").fetchone()[0]),
                "available": int(
                    db.execute("SELECT count(*) FROM articles WHERE raw IS NOT NULL").fetchone()[0]
                ),
                "pending_publication": int(
                    db.execute(
                        "SELECT count(*) FROM articles WHERE raw IS NOT NULL AND landed IS NULL"
                    ).fetchone()[0]
                ),
            }

    def confirm(self) -> int:
        """Mark landed each sent article whose artifact the host stored in this volume, under
        the sha256 of its canonical JSON; one the host never stored is sent again."""
        with self.db() as db:
            sent = db.execute(
                "SELECT id, sent FROM articles WHERE sent IS NOT NULL AND landed IS NULL"
            ).fetchall()
            stored = [
                (row["sent"], row["id"])
                for row in sent
                if (self.root / "blobs" / f"{row['sent']}.json").is_file()
            ]
            db.executemany("UPDATE articles SET landed=? WHERE id=?", stored)
        return len(stored)

    def outbox(self, limit: int) -> list[dict[str, Any]]:
        """The next `limit` unlanded articles, oldest first, each as one `mql5-article` output,
        each remembered as sent under the hash the host stores it by."""
        with self.db() as db:
            rows = db.execute(
                "SELECT id, url, metadata, markdown FROM articles "
                "WHERE raw IS NOT NULL AND landed IS NULL ORDER BY id LIMIT ?",
                (limit,),
            ).fetchall()
            outputs: list[dict[str, Any]] = []
            for row in rows:
                metadata = json.loads(row["metadata"])
                article = {
                    "title": str(metadata.get("title") or f"MQL5 article {row['id']}"),
                    "source_url": row["url"],
                    "sha256": metadata["sha256"],
                    "published": str(metadata.get("published") or ""),
                    "markdown": (self.root / row["markdown"]).read_text(encoding="utf-8"),
                }
                canonical = json.dumps(
                    article, sort_keys=True, separators=(",", ":"), ensure_ascii=False
                ).encode()
                db.execute(
                    "UPDATE articles SET sent=? WHERE id=?",
                    (hashlib.sha256(canonical).hexdigest(), row["id"]),
                )
                outputs.append({"output": ARTICLE, "data": article})
        return outputs


class Deferred(Exception):
    """The upstream's Retry-After window has not elapsed."""


def request_page(
    store: Store,
    client: httpx.Client,
    url: str,
    *,
    delay: float,
    clock: Callable[[], float],
    sleep: Callable[[float], None],
    robots: bool = False,
) -> bytes:
    if store.state("blocked_until") > clock():
        raise Deferred
    sleep(max(0, store.state("last_request") + delay - clock()))
    with store.db() as db:
        cached = db.execute("SELECT * FROM http WHERE url=?", (url,)).fetchone()
    headers = {"User-Agent": AGENT}
    if cached:
        if cached["etag"]:
            headers["If-None-Match"] = cached["etag"]
        if cached["modified"]:
            headers["If-Modified-Since"] = cached["modified"]
    store.set_state("last_request", clock())
    response = client.get(url, headers=headers, follow_redirects=False)
    if response.status_code in {429, 503}:
        retry = response.headers.get("Retry-After", "60")
        try:
            until = clock() + int(retry)
        except ValueError:
            try:
                until = parsedate_to_datetime(retry).timestamp()
            except ValueError, TypeError:
                until = clock() + 60
        store.set_state("blocked_until", max(clock() + 60, until))
        raise Deferred
    if response.status_code == 304:
        if not cached:
            raise ValueError("304 without a cached response.")
        return (store.root / cached["body"]).read_bytes()
    if robots and response.status_code in {404, 410}:
        body = b"User-agent: *\nDisallow:\n"
    elif robots and response.status_code in {401, 403}:
        body = b"User-agent: *\nDisallow: /\n"
    else:
        response.raise_for_status()
        body = response.content
    path = store.blob(body, "html")
    with store.db() as db:
        db.execute(
            "INSERT OR REPLACE INTO http VALUES(?,?,?,?)",
            (
                url,
                response.headers.get("ETag", ""),
                response.headers.get("Last-Modified", ""),
                path,
            ),
        )
    return body


def collect(
    store: Store,
    client: httpx.Client,
    *,
    limit: int = 25,
    pages: int = 5,
    clock: Callable[[], float] = time.time,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, int]:
    result = {"discovered": 0, "fetched": 0, "deferred": 0}
    try:
        raw = request_page(
            store,
            client,
            BASE + "/robots.txt",
            delay=max(2, store.state("request_interval")),
            clock=clock,
            sleep=sleep,
            robots=True,
        )
        policy = RobotFileParser()
        policy.parse(raw.decode("utf-8").splitlines())
        rate = policy.request_rate(AGENT)
        delay = max(
            2, float(policy.crawl_delay(AGENT) or 0), rate.seconds / rate.requests if rate else 0
        )
        store.set_state("request_interval", delay)
        for page in range(1, pages + 1):
            url = BASE + "/en/articles" + (f"/page{page}" if page > 1 else "")
            if not policy.can_fetch(AGENT, url):
                break
            html = request_page(store, client, url, delay=delay, clock=clock, sleep=sleep).decode(
                "utf-8"
            )
            discovered = 0
            for anchor in BeautifulSoup(html, "html.parser").select("a[href]"):
                target = urlsplit(urljoin(url, attribute(anchor, "href")))
                match = re.fullmatch(r"/en/articles/([1-9][0-9]*)/?", target.path)
                if target.scheme != "https" or target.netloc != "www.mql5.com" or not match:
                    continue
                article_id = int(match[1])
                with store.db() as db:
                    cursor = db.execute(
                        "INSERT OR IGNORE INTO articles(id,url,metadata,status) "
                        "VALUES(?,?,?,'pending')",
                        (article_id, article_url(article_id), "{}"),
                    )
                    discovered += cursor.rowcount
            result["discovered"] += discovered
            if not discovered:
                break
        with store.db() as db:
            pending = db.execute(
                "SELECT id,url FROM articles WHERE status='pending' ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        for item in pending:
            if not policy.can_fetch(AGENT, item["url"]):
                continue
            raw = request_page(store, client, item["url"], delay=delay, clock=clock, sleep=sleep)
            metadata, markdown = parse_article(raw.decode("utf-8"), item["url"])
            store.save(item["id"], raw, markdown, metadata)
            result["fetched"] += 1
    except Deferred:
        result["deferred"] = 1
    return result


def settings(root: Path) -> tuple[bool, int]:
    """Whether the job crawls www.mql5.com, and `publish.per_run`, from the instance's
    `data/config.json` over the defaults."""
    own = root / "data" / "config.json"
    found = (
        cast(dict[str, Any], json.loads(own.read_text(encoding="utf-8"))) if own.is_file() else {}
    )
    crawl = found.get("crawl", True)
    per_run = cast(dict[str, Any], found.get("publish", {})).get("per_run", PER_RUN)
    if not isinstance(crawl, bool) or not isinstance(per_run, int) or per_run < 1:
        raise ValueError(
            "data/config.json sets crawl to true or false and publish.per_run to 1 or more."
        )
    return crawl, per_run


def run_daily() -> dict[str, Any]:
    """Seed, crawl, then answer the next unlanded articles as `outputs`; the host lands each one
    as its own Library artifact. A site that cannot be reached still lets the archive land."""
    if not RUN_LOCK.acquire(blocking=False):
        raise RuntimeError("Article work is already running.")
    try:
        store = Store(Path(os.environ["QMX_VOLUME"]))
        crawl, per_run = settings(store.root)
        landed = store.confirm()
        seeded = store.seed()
        result: dict[str, Any] = {"discovered": 0, "fetched": 0, "deferred": 0}
        if crawl:
            try:
                with httpx.Client(timeout=20) as http:
                    result = {**collect(store, http)}
            except httpx.HTTPError as error:
                result["crawl_error"] = type(error).__name__
        outputs = store.outbox(per_run)
        return {**result, "seeded": seeded, "landed": landed, "outputs": outputs}
    finally:
        RUN_LOCK.release()
