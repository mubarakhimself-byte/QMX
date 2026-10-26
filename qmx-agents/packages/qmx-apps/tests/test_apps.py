from __future__ import annotations

import json
import shutil
import sqlite3
import sys
import time
from collections.abc import Generator
from contextlib import closing
from pathlib import Path
from typing import cast

import psutil
import pytest

from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import Definition
from qmx_apps.supervisor import Supervisor, refuse_tool
from qmx_apps.volume import Volume

EXAMPLES = Path(__file__).resolve().parents[4] / "examples/apps"
DEEP_HOME = 144
"""The home's length in characters, whatever the temp root. Below it, `environments/<hash>/Lib/
site-packages` adds 96 and the native `_cffi_backend.cp314-win_amd64.pyd` 34 more, so the `.pyd`
lands at 274, past 260. `site-packages` stays at 240, under the 258 that Windows allows a process's
working directory, which uv's bytecode compile starts in (it fails with os error 267 past it)."""


@pytest.fixture
def supervisor(tmp_path: Path) -> Generator[Supervisor]:
    owner = Supervisor(
        tmp_path / "home", secret_getter=lambda service, username: "declared-fixture"
    )
    try:
        yield owner
    finally:
        owner.close()


@pytest.fixture
def fixture_app(tmp_path: Path) -> Path:
    source = EXAMPLES / "exchange-status"
    target = tmp_path / "fixture"
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    shutil.copyfile(Path(__file__).with_name("fixture_server.py"), target / "server.py")
    return target


def install(owner: Supervisor, path: Path) -> None:
    owner.install(path, trust="first_party")


def document(value: object) -> Document:
    assert isinstance(value, dict)
    return cast(Document, value)


def dead(pid: int) -> None:
    deadline = time.monotonic() + 5
    while psutil.pid_exists(pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not psutil.pid_exists(pid), f"Owned app process {pid} survived shutdown"


def test_manifest_hash_and_optional_volume_files(fixture_app: Path, tmp_path: Path) -> None:
    image = Definition.load(fixture_app)
    assert image.hash == Definition.load(fixture_app).hash
    volume = Volume(tmp_path, image.manifest.id)
    volume.create(agents=False)
    assert (volume.root / "app.db").is_file()
    assert not (volume.root / "memory.db").exists()
    assert all((volume.root / name).is_dir() for name in ("data", "blobs", "logs"))
    with closing(sqlite3.connect(volume.root / "app.db")) as db:
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    volume.create(agents=True)
    assert (volume.root / "memory.db").is_file()
    with pytest.raises(AppError, match="volume"):
        volume.check_write(tmp_path / "outside")


def test_start_applies_definition_migrations(supervisor: Supervisor, fixture_app: Path) -> None:
    directory = fixture_app / "migrations"
    directory.mkdir()
    (directory / "1-state.sql").write_text("CREATE TABLE migrated (value TEXT);")
    install(supervisor, fixture_app)
    supervisor.start("exchange-status")
    supervisor.stop("exchange-status")
    with closing(sqlite3.connect(supervisor.home / "apps/exchange-status/app.db")) as db:
        assert db.execute("SELECT COUNT(*) FROM migrated").fetchone() == (0,)


@pytest.mark.parametrize(
    "old,new",
    [
        ('id = "exchange-status"', 'id = "../escape"'),
        ('id = "exchange-status"', 'id = "con"'),
        ('version = "1.0.0"', 'version = "oops"'),
        ('risk = "shows"', 'risk = "orders"'),
        ('mcp = "server.py"', 'mcp = "../server.py"'),
        ('kind = "screens"', 'kind = "headless"'),
        ('kind = "screens"', 'kind = "screens"\nstartup_timeout_seconds = 0'),
        ('kind = "screens"', 'kind = "screens"\nstartup_timeout_seconds = nan'),
    ],
)
def test_manifest_rejects_invalid_definitions(fixture_app: Path, old: str, new: str) -> None:
    manifest = fixture_app / "app.toml"
    manifest.write_text(manifest.read_text().replace(old, new), encoding="utf-8")
    with pytest.raises(AppError) as caught:
        Definition.load(fixture_app)
    assert caught.value.code == "invalid_definition"


def test_manifest_rejects_remote_schema_refs(fixture_app: Path) -> None:
    with (fixture_app / "app.toml").open("a", encoding="utf-8") as file:
        file.write('\n[feeds.bad]\n"$ref" = "https://example.com/schema"\n')
    with pytest.raises(AppError, match="self-contained"):
        Definition.load(fixture_app)


def test_manifest_rejects_bad_schema(fixture_app: Path) -> None:
    path = fixture_app / "app.toml"
    path.write_text(path.read_text().replace('type = "object"', 'type = "nonsense"', 1))
    with pytest.raises(AppError) as caught:
        Definition.load(fixture_app)
    assert caught.value.code == "invalid_definition"


def test_install_start_registry_stop_and_restart(supervisor: Supervisor, fixture_app: Path) -> None:
    install(supervisor, fixture_app)
    started = supervisor.start("exchange-status")
    pid = cast(int, started["pid"])
    assert psutil.pid_exists(pid)
    assert started["status"] == "running"
    assert cast(float, started["heartbeat_age_seconds"]) < 3
    limits = document(started["limits"])
    assert limits["memory_mb"] == 1024
    if sys.platform == "win32":
        assert limits["cpu_percent"] == 50
        assert limits["kill_on_close"] is True
    else:
        assert limits["fallback"] == "RLIMIT_AS and psutil"
    registry = supervisor.registry()
    assert registry[0]["transport"] == "stdio"
    assert "ping" in [document(tool)["name"] for tool in cast(list[object], registry[0]["tools"])]
    assert supervisor.call("exchange-status", "ping", {})["result"] == {"pong": True}
    text_result = supervisor.call("exchange-status", "text_status", {})
    assert text_result["result"] is None
    assert (
        document(cast(list[object], text_result["content"])[0])["text"]
        == "Recorded text-only response"
    )
    assert document(text_result["meta"])["fixture"] is True
    assert (
        document(document(text_result["meta"])["io.modelcontextprotocol/serverInfo"])["name"]
        == "Supervisor boundary fixture"
    )
    if sys.platform == "win32":
        before_cpu = cast(
            float,
            document(supervisor.status("exchange-status")["metrics"])["cpu_seconds"],
        )
        supervisor.call("exchange-status", "child_cpu", {})
        after_cpu = cast(
            float,
            document(supervisor.status("exchange-status")["metrics"])["cpu_seconds"],
        )
        assert after_cpu >= before_cpu + 0.30, "Exited child CPU must remain in the job budget"
    stopped = supervisor.stop("exchange-status")
    assert stopped["status"] == "stopped"
    dead(pid)
    assert supervisor.registry() == []
    restarted = supervisor.restart("exchange-status")
    assert restarted["instance_id"] != started["instance_id"]
    supervisor.stop("exchange-status")
    dead(cast(int, restarted["pid"]))


@pytest.mark.skipif(sys.platform != "win32", reason="Windows native DLL path handling")
def test_deep_windows_home_loads_native_dependencies(tmp_path: Path, fixture_app: Path) -> None:
    padding = DEEP_HOME - len(str(tmp_path / "home")) - 1
    deep = tmp_path / ("nested" * 50)[:padding] if padding > 0 else tmp_path
    owner = Supervisor(deep / "home")
    try:
        install(owner, fixture_app)
        definition_hash = cast(str, owner.get("exchange-status")["definition_hash"])
        native = next(
            (owner.environments / definition_hash).glob(
                "Lib/site-packages/_cffi_backend*.pyd"
            )
        )
        assert len(str(native)) > 260, "Exercise the Windows native DLL path boundary"
        started = owner.start("exchange-status")
        assert owner.call("exchange-status", "ping", {})["result"] == {"pong": True}
        owner.stop("exchange-status")
        dead(cast(int, started["pid"]))
    finally:
        owner.close()


def test_startup_has_its_own_deadline(supervisor: Supervisor, fixture_app: Path) -> None:
    script = fixture_app / "server.py"
    script.write_text(
        script.read_text().replace(
            '    mcp.run(transport="stdio", show_banner=False)',
            "    import time\n    time.sleep(32)\n"
            '    mcp.run(transport="stdio", show_banner=False)',
        )
    )
    install(supervisor, fixture_app)
    started = supervisor.start("exchange-status")
    assert started["status"] == "running"
    assert supervisor.call("exchange-status", "ping", {})["result"] == {"pong": True}
    supervisor.stop("exchange-status")
    dead(cast(int, started["pid"]))


def test_running_requests_keep_their_deadlines(supervisor: Supervisor, fixture_app: Path) -> None:
    install(supervisor, fixture_app)
    supervisor.start("exchange-status")
    with pytest.raises(AppError, match="timed out"):
        supervisor.call("exchange-status", "slow_tool", {})
    with pytest.raises(AppError) as resource_error:
        supervisor.resource("exchange-status", "fixture://slow")
    assert resource_error.value.code == "resource_timeout"
    assert supervisor.call("exchange-status", "ping", {})["result"] == {"pong": True}


def test_definition_is_immutable_and_volume_has_one_owner(
    supervisor: Supervisor, fixture_app: Path
) -> None:
    install(supervisor, fixture_app)
    before = supervisor.get("exchange-status")["definition_hash"]
    script = fixture_app / "server.py"
    script.write_text(script.read_text() + "\n# changed source\n")
    with pytest.raises(AppError) as caught:
        install(supervisor, fixture_app)
    assert caught.value.code == "immutable_version"
    assert supervisor.get("exchange-status")["definition_hash"] == before
    supervisor.start("exchange-status")
    contender = Supervisor(supervisor.home)
    try:
        with pytest.raises(AppError) as busy:
            contender.start("exchange-status")
        assert busy.value.code == "volume_busy"
        with pytest.raises(AppError) as busy_install:
            install(contender, fixture_app)
        assert busy_install.value.code == "volume_busy"
        assert supervisor.call("exchange-status", "ping", {})["result"] == {"pong": True}
    finally:
        contender.close()


def test_new_version_and_trust_boundary(supervisor: Supervisor, fixture_app: Path) -> None:
    with pytest.raises(AppError) as caught:
        supervisor.install(fixture_app)
    assert caught.value.code == "tier_required"
    install(supervisor, fixture_app)
    path = fixture_app / "app.toml"
    path.write_text(path.read_text().replace('version = "1.0.0"', 'version = "1.1.0"'))
    supervisor.install(
        fixture_app,
        trust="reviewed",
        expected_id="exchange-status",
        expected_hash=str(supervisor.get("exchange-status")["definition_hash"]),
    )
    assert [item["version"] for item in supervisor.versions("exchange-status")] == [
        "1.0.0",
        "1.1.0",
    ]


def test_only_declared_secrets_and_redacted_logs(
    supervisor: Supervisor, fixture_app: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QMX_UNDECLARED_SECRET", "must-not-leak")
    monkeypatch.setenv("PYTHONPATH", "must-not-inherit")
    with (fixture_app / "app.toml").open("a") as file:
        file.write('\n[capabilities.secrets]\nDECLARED_SECRET = "qmx/fixture"\n')
    install(supervisor, fixture_app)
    supervisor.start("exchange-status")
    data = document(supervisor.call("exchange-status", "environment", {})["result"])
    assert data["declared_matches"] is True
    assert data["undeclared_present"] is False
    assert data["pythonpath_present"] is False
    assert data["cwd"] == str(supervisor.home / "apps/exchange-status")
    assert data["home"] == data["cwd"]
    supervisor.call("exchange-status", "print_secret", {})
    supervisor.stop("exchange-status")
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (supervisor.home / "apps/exchange-status/logs").iterdir()
    )
    assert "declared-fixture" not in text
    assert "must-not-leak" not in text
    assert "[redacted]" in text
    assert supervisor.logs("exchange-status")


@pytest.mark.parametrize("tool", ["write", "write_database"])
def test_actual_subprocess_refuses_outside_writes(
    supervisor: Supervisor, fixture_app: Path, tmp_path: Path, tool: str
) -> None:
    install(supervisor, fixture_app)
    supervisor.start("exchange-status")
    outside = tmp_path / "outside.db"
    with pytest.raises(AppError, match="inside its volume"):
        supervisor.call("exchange-status", tool, {"path": str(outside)})
    assert not outside.exists()
    inside = supervisor.home / "apps/exchange-status/data/inside.db"
    assert supervisor.call("exchange-status", tool, {"path": str(inside)})["result"] == {
        "written": True
    }


def test_no_usage_budget_stops_an_app(supervisor: Supervisor, fixture_app: Path) -> None:
    path = fixture_app / "app.toml"
    path.write_text(path.read_text().replace("runs = 100", "runs = 1"))
    install(supervisor, fixture_app)
    supervisor.start("exchange-status")
    for _ in range(3):
        assert supervisor.call("exchange-status", "ping", {})["result"] == {"pong": True}
    status = supervisor.status("exchange-status")
    assert status["status"] == "running"
    assert document(status["metrics"])["runs"] == 3
    supervisor.stop("exchange-status")


def test_heartbeat_breaker_stops_actual_process(supervisor: Supervisor, fixture_app: Path) -> None:
    with (fixture_app / "app.toml").open("a") as file:
        file.write("\n[breaker]\nheartbeat_timeout = 1\n")
    install(supervisor, fixture_app)
    pid = cast(int, supervisor.start("exchange-status")["pid"])
    supervisor.call("exchange-status", "freeze_heartbeat", {})
    dead(pid)
    assert (
        document(supervisor.status("exchange-status")["breaker"])["reason"] == "heartbeat_timeout"
    )


def with_job(fixture_app: Path, body: str) -> None:
    path = fixture_app / "app.toml"
    text = path.read_text().replace('mcp = "server.py"', 'mcp = "server.py"\njobs = ["job.py"]')
    path.write_text(text + "\n[schedule]\ninterval_seconds = 0.5\n")
    (fixture_app / "job.py").write_text(body)


def test_the_supervisor_schedules_nothing_and_runs_a_job_when_asked(
    supervisor: Supervisor, fixture_app: Path
) -> None:
    with_job(
        fixture_app,
        "from pathlib import Path\n"
        "def run():\n"
        "    path = Path('data/job.txt')\n"
        "    path.write_text(str(int(path.read_text()) + 1) if path.exists() else '1')\n",
    )
    install(supervisor, fixture_app)
    supervisor.start("exchange-status")
    marker = supervisor.home / "apps/exchange-status/data/job.txt"
    time.sleep(2)
    assert not marker.exists(), "the old half-second schedule must not run the job"
    assert supervisor.run_job("exchange-status", "job.py")["job"] == "job.py"
    assert supervisor.run_job("exchange-status", "job.py")["job"] == "job.py"
    assert marker.read_text() == "2"
    with pytest.raises(AppError) as caught:
        supervisor.run_job("exchange-status", "other.py")
    assert caught.value.code == "job_not_found"
    supervisor.stop("exchange-status")
    with pytest.raises(AppError) as stopped:
        supervisor.run_job("exchange-status", "job.py")
    assert (stopped.value.code, str(stopped.value)) == ("not_running", "The app is stopped.")


def test_failing_jobs_still_trip_the_crash_breaker(
    supervisor: Supervisor, fixture_app: Path
) -> None:
    with_job(fixture_app, "def run():\n    raise RuntimeError('boom')\n")
    install(supervisor, fixture_app)
    pid = cast(int, supervisor.start("exchange-status")["pid"])
    for _ in range(3):
        with pytest.raises(AppError) as caught:
            supervisor.run_job("exchange-status", "job.py")
        assert caught.value.code in {"job_failed", "not_running"}
    dead(pid)
    status = supervisor.status("exchange-status")
    assert (status["status"], document(status["breaker"])["reason"]) == ("tripped", "error_limit")


@pytest.mark.serial
def test_producer_to_consumer_artifact_and_screen_state(supervisor: Supervisor) -> None:
    install(supervisor, EXAMPLES / "exchange-status")
    install(supervisor, EXAMPLES / "weekend-watcher")
    supervisor.start("exchange-status")
    try:
        supervisor.start("weekend-watcher")
    except AppError as error:
        pytest.fail(f"Watcher startup failed: {error}; logs={supervisor.logs('weekend-watcher')}")
    assert supervisor.status("exchange-status")["status"] == "running", supervisor.logs(
        "exchange-status"
    )
    supervisor.call(
        "exchange-status",
        "record",
        {"exchange": "recorded-venue", "status": "degraded", "observed_at": "2026-10-07T00:00:00Z"},
    )
    snapshot = document(supervisor.call("exchange-status", "snapshot", {})["artifact_ref"])
    result = supervisor.call("weekend-watcher", "summarize", {"snapshot": snapshot})
    summary = document(result["artifact_ref"])
    content = json.loads(
        (supervisor.home / f"apps/weekend-watcher/blobs/{summary['sha256']}.json").read_text()
    )
    assert "recorded-venue: degraded" in content["summary"]
    assert content["source_sha256"] == snapshot["sha256"]
    assert content["mode"] == "recorded_fixture"
    assert (supervisor.home / "apps/weekend-watcher/memory.db").exists()
    assert not (supervisor.home / "apps/exchange-status/memory.db").exists()
    resources = supervisor.resource("exchange-status", "ui://exchange-status/view.html")
    assert "recorded-venue" in cast(str, resources[0]["text"])
    assert resources[0]["mimeType"] == "text/html;profile=mcp-app"
    supervisor.restart("exchange-status")
    assert "recorded-venue" in cast(
        str, supervisor.resource("exchange-status", "ui://exchange-status/view.html")[0]["text"]
    )
    with pytest.raises(AppError) as caught:
        supervisor.call(
            "weekend-watcher", "summarize", {"snapshot": {**snapshot, "sha256": "0" * 64}}
        )
    assert caught.value.code == "unknown_artifact"
    with pytest.raises(AppError) as caught:
        supervisor.artifacts.save(
            Definition.load(EXAMPLES / "exchange-status"), "snapshot", {"observations": "bad"}
        )
    assert caught.value.code == "invalid_output"


def test_a_tool_is_refused_for_a_parent_surface_or_record_not_money_words() -> None:
    refuse_tool("place_order", {"name": "place_order", "money_path": True})
    refuse_tool("score", {"_meta": {"parent_library": "qmf-risk", "parent_surface": "value_type"}})
    with pytest.raises(AppError) as surface:
        refuse_tool(
            "write_risk", {"_meta": {"parent_library": "qmf-risk", "parent_surface": "write"}}
        )
    with pytest.raises(AppError) as record:
        refuse_tool("bind", {"annotations": {"tool": {"record_family": "binding"}}})
    assert (surface.value.code, str(surface.value), surface.value.status) == (
        "tool_refused",
        "Parent surface refused: write_risk",
        403,
    )
    assert str(record.value) == "Parent record mutation refused: bind"
