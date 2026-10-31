"""The one rclone runner (design 06 section 3): where it finds rclone, the pinned fetch and its
hash, the minimum, secrets kept out of every command line, the failures it sorts, and a conf
whose password is gone set aside once."""

from __future__ import annotations

import hashlib
import http.server
import io
import json
import os
import shutil
import sys
import threading
import zipfile
from collections.abc import Generator
from pathlib import Path

import pytest

from qmx_home import Layout, resolve
from qmx_home.rclone import (
    CONFIG_KEY,
    UNREADABLE,
    Pinned,
    Rclone,
    RcloneRefused,
    _system,  # pyright: ignore[reportPrivateUsage]
)

REAL = shutil.which("rclone")
needs_rclone = pytest.mark.skipif(REAL is None, reason="rclone is not on PATH")
PLANTED = "planted-Answer-7731"


class Store:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def read(self, name: str) -> str | None:
        return self.values.get(name)

    def replace(self, name: str, value: str) -> None:
        self.values[name] = value


def fake(folder: Path, version: str, *, code: int = 0, log: str = "") -> Path:
    """A stand-in rclone: it reports `version`, and every other call writes `log` to stderr and
    exits `code`."""
    script = folder / "fake_rclone.py"
    script.write_text(
        "import sys\n"
        f"if 'version' in sys.argv: print('rclone v{version}'); sys.exit(0)\n"
        f"sys.stderr.write({log!r} + '\\n')\n"
        f"sys.exit({code})\n",
        encoding="utf-8",
    )
    command = folder / "rclone.cmd"
    command.write_text(f'@"{sys.executable}" -I "{script}" %*\n', encoding="utf-8")
    return command


def folder(tmp_path: Path) -> Layout:
    return resolve(tmp_path / "QMX", create=True)


def nowhere(_name: str) -> str | None:
    return None


@needs_rclone
def test_rclone_is_found_at_the_setting_on_path_and_in_the_cache(tmp_path: Path) -> None:
    layout = folder(tmp_path)
    assert REAL is not None
    named = Rclone(layout, keys=Store(), path=REAL, which=nowhere).binary()
    on_path = Rclone(layout, keys=Store()).binary()
    cached = layout.cache / "tools" / "rclone" / Path(REAL).name
    cached.parent.mkdir(parents=True)
    os.link(REAL, cached)
    from_cache = Rclone(layout, keys=Store(), which=nowhere).binary()
    assert (named, on_path, from_cache) == (Path(REAL), Path(REAL), cached)


@pytest.fixture
def release(tmp_path: Path) -> Generator[tuple[str, bytes]]:
    """A loopback server offering a release zip that holds the real rclone."""
    assert REAL is not None
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as archive:
        archive.write(REAL, f"rclone-v1.75.2-{_system()}/{Path(REAL).name}")
    body = buffer.getvalue()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", body
    finally:
        server.shutdown()


@needs_rclone
def test_the_pinned_release_is_fetched_checked_and_refused_on_a_wrong_hash(
    tmp_path: Path, release: tuple[str, bytes]
) -> None:
    base, body = release
    good = Pinned((1, 75, 2), {_system(): hashlib.sha256(body).hexdigest()}, base)
    bad = Pinned((1, 75, 2), {_system(): "0" * 64}, base)
    refused = folder(tmp_path / "bad")
    with pytest.raises(RcloneRefused) as wrong:
        Rclone(refused, keys=Store(), which=nowhere, pinned=bad).binary()
    fetched = Rclone(folder(tmp_path / "good"), keys=Store(), which=nowhere, pinned=good)
    assert "did not match its published sha256 " + "0" * 64 in str(wrong.value)
    assert not (refused.cache / "tools").exists()
    assert fetched.binary().parent.parts[-2:] == ("tools", "rclone")
    assert fetched.version() == (1, 75, 2)


def test_an_rclone_older_than_the_minimum_is_refused_naming_it(tmp_path: Path) -> None:
    old = fake(tmp_path, "1.60.0")
    with pytest.raises(RcloneRefused) as refused:
        Rclone(folder(tmp_path), keys=Store(), which=lambda _n: str(old)).binary()
    assert "is version 1.60.0, older than 1.75.2, which QMX needs" in str(refused.value)


@pytest.mark.parametrize(
    ("code", "log", "failure"),
    [
        (5, '{"level":"error","msg":"dial tcp 127.0.0.1:9: connectex: refused"}', "offline"),
        (7, '{"level":"error","msg":"oauth2: \\"invalid_grant\\" token expired"}', "signin"),
        (1, '{"level":"error","msg":"googleapi: storageQuotaExceeded"}', "full"),
        (3, '{"level":"error","msg":"error listing: directory not found"}', "missing"),
        (1, '{"level":"error","msg":"something rclone never said before"}', "other"),
    ],
)
def test_a_failure_is_sorted_from_its_exit_code_and_json_log(
    tmp_path: Path, code: int, log: str, failure: str
) -> None:
    binary = fake(tmp_path, "1.75.2", code=code, log=log)
    runner = Rclone(folder(tmp_path), keys=Store(), path=str(binary))
    runner.conf.parent.mkdir(parents=True, exist_ok=True)
    runner.conf.write_text("RCLONE_ENCRYPT_V0:\nnot-really\n", encoding="utf-8")
    runner.keys.replace(CONFIG_KEY, "known")
    ran = runner.run(["lsf", "lane:"])
    assert (ran.code, ran.failure) == (code, failure)
    assert "{" not in ran.line


@needs_rclone
def test_no_secret_reaches_a_command_line_and_the_record_holds_names_only(tmp_path: Path) -> None:
    runner = Rclone(folder(tmp_path), keys=Store())
    obscured = runner.obscure(PLANTED)
    runner.run(
        ["config", "create", "lane", "local", "description=lane storage", "--non-interactive"],
        secrets={"RCLONE_CONFIG_LANE_PASSWORD": PLANTED},
        answer=PLANTED,
        password=True,
    )
    recorded = json.dumps([[*call.args, *call.env] for call in runner.record])
    assert obscured not in ("", PLANTED)
    assert PLANTED not in recorded
    assert "description=..." in recorded
    assert "--non-interactive" in recorded
    assert "RCLONE_RESULT" in recorded
    assert "RCLONE_CONFIG_LANE_PASSWORD" in recorded
    assert PLANTED not in runner.conf.read_text(encoding="utf-8")
    assert "RCLONE_ENCRYPT_V0:" in runner.conf.read_text(encoding="utf-8")


@needs_rclone
def test_a_conf_whose_password_is_gone_is_set_aside_once(tmp_path: Path) -> None:
    layout = folder(tmp_path)
    first = Rclone(layout, keys=Store())
    first.run(["config", "create", "lane", "local", "--non-interactive"])
    emptied = Rclone(layout, keys=Store())
    aside = emptied.check_conf()
    again = emptied.check_conf()
    remotes = emptied.run(["listremotes"])
    assert aside is not None
    assert aside.name.startswith(UNREADABLE)
    assert again == aside
    assert [p.name for p in layout.data.glob(UNREADABLE + "*")] == [aside.name]
    assert (remotes.code, remotes.out) == (0, "")


@needs_rclone
def test_a_conf_with_a_changed_password_is_set_aside_with_one_call(tmp_path: Path) -> None:
    layout = folder(tmp_path)
    keys = Store()
    Rclone(layout, keys=keys).run(["config", "create", "lane", "local", "--non-interactive"])
    keys.replace(CONFIG_KEY, "another password")
    runner = Rclone(layout, keys=keys)
    ran = runner.run(["listremotes"])
    calls = [call.args for call in runner.record if "listremotes" in call.args]
    assert ran.failure == "missing"
    assert ran.line.startswith("the storages' settings on this PC could not be opened")
    assert len(calls) == 1
    assert len(list(layout.data.glob(UNREADABLE + "*"))) == 1
    assert runner.run(["listremotes"]).code == 0
