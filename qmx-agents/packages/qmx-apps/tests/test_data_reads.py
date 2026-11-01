"""AD-33 change 4: an app that declares `data_reads = ["market"]` gets a read-only market root.

Both fixture apps are real subprocesses under the supervisor, so the refused writes are refused by
the bootstrap's audit hook inside the app's own process.
"""

from __future__ import annotations

import shutil
import sys
from collections.abc import Generator
from pathlib import Path
from typing import cast

import pytest

from qmx_apps.errors import AppError
from qmx_apps.supervisor import Supervisor

EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"
READER = "market-reader"
OTHER = "exchange-status"
PARTITION = Path("series/dukascopy/eurusd/bars/m1/2024-01/part-0.parquet")
"""A partition-shaped file; its bytes are a fixture, not a parquet file."""

SERVER = """
import os
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("data_reads fixture")


@mcp.tool()
def seen() -> dict:
    return {"names": sorted(os.environ), "market": os.environ.get("QMX_MARKET_ROOT")}


@mcp.tool()
def read_partition(relative: str) -> dict:
    return {"text": (Path(os.environ["QMX_MARKET_ROOT"]) / relative).read_text()}


@mcp.tool()
def write(path: str) -> dict:
    Path(path).write_text("probe", encoding="utf-8")
    return {"written": True}


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
"""

TODAY = {
    "APPDATA",
    "FASTMCP_SHOW_BANNER",
    "HOME",
    "LOCALAPPDATA",
    "PATH",
    "PYTHONDONTWRITEBYTECODE",
    "QMX_DATA_DIR",
    "QMX_STAGE",
    "QMX_VOLUME",
    "TEMP",
    "TMP",
    "USERPROFILE",
}
"""The environment every app got before this change, less the Windows system names."""
WINDOWS = {"COMSPEC", "SYSTEMROOT", "WINDIR"} if sys.platform == "win32" else set()


def source(root: Path, app_id: str, data_reads: str) -> Path:
    target = root / f"source-{app_id}"
    shutil.copytree(EXAMPLE, target, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    (target / "server.py").write_text(SERVER, encoding="utf-8")
    manifest = target / "app.toml"
    manifest.write_text(
        manifest.read_text()
        .replace(f'id = "{OTHER}"', f'id = "{app_id}"')
        .replace("data_reads = []", f"data_reads = {data_reads}")
    )
    return target


@pytest.fixture(scope="module")
def owner(tmp_path_factory: pytest.TempPathFactory) -> Generator[tuple[Supervisor, Path]]:
    root = tmp_path_factory.mktemp("data-reads")
    supervisor = Supervisor(root / "home")
    market = root / "home" / "market"
    (market / PARTITION).parent.mkdir(parents=True)
    (market / PARTITION).write_text("EURUSD 2024-01 bars", encoding="utf-8")
    try:
        supervisor.install(source(root, READER, '["market"]'), trust="first_party")
        supervisor.install(source(root, OTHER, "[]"), trust="first_party")
        supervisor.start(READER)
        supervisor.start(OTHER)
        yield supervisor, market
    finally:
        supervisor.close()


def call(supervisor: Supervisor, app_id: str, tool: str, **arguments: str) -> dict[str, object]:
    answer = supervisor.call(app_id, tool, dict(arguments))
    return cast(dict[str, object], answer["result"])


def test_a_declaring_app_sees_the_root_and_reads_a_partition(
    owner: tuple[Supervisor, Path],
) -> None:
    supervisor, market = owner
    seen = call(supervisor, READER, "seen")
    assert seen["market"] == str(market.resolve())
    assert set(cast(list[str], seen["names"])) == TODAY | WINDOWS | {"QMX_MARKET_ROOT"}
    read = call(supervisor, READER, "read_partition", relative=PARTITION.as_posix())
    assert read == {"text": "EURUSD 2024-01 bars"}


def test_an_app_without_the_declaration_gets_todays_environment(
    owner: tuple[Supervisor, Path],
) -> None:
    supervisor, _ = owner
    seen = call(supervisor, OTHER, "seen")
    assert seen["market"] is None
    assert set(cast(list[str], seen["names"])) == TODAY | WINDOWS


@pytest.mark.parametrize(
    "target",
    [
        PARTITION.with_name("planted.parquet"),
        PARTITION,
        Path("../escaped.txt"),
    ],
    ids=["new-file", "overwrite-partition", "dot-dot-escape"],
)
def test_a_write_under_the_root_is_refused_in_the_app_process(
    owner: tuple[Supervisor, Path], target: Path
) -> None:
    supervisor, market = owner
    with pytest.raises(AppError, match="inside its volume"):
        supervisor.call(READER, "write", {"path": str(market / target)})
    assert not (market / PARTITION.with_name("planted.parquet")).exists()
    assert not (market.parent / "escaped.txt").exists()
    assert (market / PARTITION).read_text(encoding="utf-8") == "EURUSD 2024-01 bars"
