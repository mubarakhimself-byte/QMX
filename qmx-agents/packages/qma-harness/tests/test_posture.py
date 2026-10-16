from __future__ import annotations

import asyncio
import importlib
import builtins
import io
import json
import os
import pathlib
import subprocess
import sys
import threading
from collections.abc import Iterator
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import keyring
import pytest
from fastapi.testclient import TestClient
from qmx_control.server import create_app

import qma.harness.harness
import qma.harness.money
from qma.harness.harness import Harness
from qma.harness.home import DoctorLine, QmxHome
from qma.harness.money import (
    UNLISTED,
    ExposureFinding,
    ExposureReport,
    ExposureTarget,
    MoneyPosture,
    exposure_targets,
    keyring_inventory,
    load_scope_proofs,
    measure,
    money_posture,
    run_exposure_probe,
    save_scope_proof,
    store_names,
    unproven,
)
from qma.harness.routes import control_service, router

CANARY = "canary-7f3a-not-a-real-login"
NON_BROKER = frozenset({"qmx/chatgpt", "qmx/control-token", "qmx/openrouter"})
BEARER = "test-bearer"
HEADERS = {"Authorization": f"Bearer {BEARER}"}


@pytest.mark.parametrize(
    ("inventory", "proofs", "posture", "missing"),
    [
        ((), {}, MoneyPosture.STRUCTURAL, ()),
        (("qmx/chatgpt", "qmx/openrouter"), {}, MoneyPosture.STRUCTURAL, ()),
        (("qmx/x-test",), {}, MoneyPosture.SPEED_BUMP, ("qmx/x-test",)),
        (("qmx/ctrader-trading",), {"qmx/ctrader-trading": True}, MoneyPosture.STRUCTURAL, ()),
        (
            ("qmx/ctrader-trading",),
            {"qmx/ctrader-trading": False},
            MoneyPosture.SPEED_BUMP,
            ("qmx/ctrader-trading",),
        ),
        (
            ("qmx/a", "qmx/b", "qmx/chatgpt"),
            {"qmx/a": True},
            MoneyPosture.SPEED_BUMP,
            ("qmx/b",),
        ),
        ((UNLISTED,), {}, MoneyPosture.SPEED_BUMP, (UNLISTED,)),
        (("qmx/Ctrader",), {"qmx/ctrader": True}, MoneyPosture.STRUCTURAL, ()),
    ],
)
def test_money_posture_table(
    inventory: tuple[str, ...],
    proofs: dict[str, bool],
    posture: MoneyPosture,
    missing: tuple[str, ...],
) -> None:
    assert money_posture(frozenset(inventory), NON_BROKER, proofs) is posture
    assert unproven(frozenset(inventory), NON_BROKER, proofs) == missing


def test_an_unlisted_store_keeps_an_unprovable_entry_in_the_inventory() -> None:
    assert keyring_inventory(["QMX/Kimi"], None) == frozenset({"qmx/kimi", UNLISTED})
    assert keyring_inventory(["qmx/kimi"], frozenset({"qmx/x"})) == frozenset(
        {"qmx/kimi", "qmx/x"}
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Credential Manager is Windows only")
def test_the_windows_listing_asks_only_for_qmx_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    import ctypes  # noqa: PLC0415

    filters: list[object] = []

    class Advapi:
        def CredEnumerateW(self, wanted: object, *_: object) -> int:  # noqa: N802
            filters.append(wanted)
            ctypes.set_last_error(qma.harness.money.ERROR_NOT_FOUND)
            return 0

    monkeypatch.setattr(ctypes, "WinDLL", lambda *_, **__: Advapi())
    assert qma.harness.money._windows_store_names() == []  # pyright: ignore[reportPrivateUsage]
    assert filters == ["qmx/*"]


def test_store_names_keeps_qmx_names_only_and_drops_the_user_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    listing = ["openrouter@qmx/openrouter", "git:https://github.com", "QMX/Kimi", "qmx/x-test"]
    monkeypatch.setattr(qma.harness.money, "_windows_store_names", lambda: listing)
    assert store_names("win32") == frozenset({"qmx/openrouter", "qmx/kimi", "qmx/x-test"})
    assert store_names("darwin") is None

    def broken() -> list[str]:
        raise OSError(5, "denied")

    monkeypatch.setattr(qma.harness.money, "_windows_store_names", broken)
    assert store_names("win32") is None


def test_only_a_parsed_true_proof_counts(tmp_path: Path) -> None:
    folder = tmp_path / "scope-proofs"
    folder.mkdir()
    rows = {
        "a.json": {"credential": "qmx/A", "refused_for_scope": True},
        "b.json": {"credential": "qmx/b", "refused_for_scope": False},
        "c.json": {"credential": "qmx/c", "refused_for_scope": "yes"},
    }
    for name, row in rows.items():
        (folder / name).write_text(json.dumps(row), encoding="utf-8")
    (folder / "d.json").write_text("{not json", encoding="utf-8")
    saved = save_scope_proof(tmp_path, "qmx/Ctrader-Demo", refused_for_scope=True, outcome="x")
    assert saved == folder / "ctrader-demo.json"
    assert load_scope_proofs(tmp_path) == {"qmx/a": True, "qmx/b": False, "qmx/ctrader-demo": True}


def test_exposure_targets_cover_entries_home_files_secrets_his_home_and_the_port(
    tmp_path: Path,
) -> None:
    home, personal = tmp_path / "qmx", tmp_path / "me" / ".claude"
    login = home / "claude" / ".credentials.json"
    targets = exposure_targets(home, ["qmx/b", UNLISTED, "qmx/a"], 8876, [login], personal)
    assert targets == (
        ExposureTarget("keyring_entry", "qmx/a"),
        ExposureTarget("keyring_entry", "qmx/b"),
        ExposureTarget("read_path", str(home / "settings.toml")),
        ExposureTarget("read_path", str(home / "control.db")),
        ExposureTarget("read_path", str(home / "portfolio.db")),
        ExposureTarget("read_path", str(login)),
        ExposureTarget("read_path", str(personal)),
        ExposureTarget("write_path", str(home)),
        ExposureTarget("write_path", str(personal)),
        ExposureTarget("loopback", "127.0.0.1:8876"),
    )
    assert exposure_targets(home, [], None, [], personal)[-1].kind == "write_path"


class Refuses(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(401)
        self.end_headers()

    def log_message(self, *_: object) -> None:
        return


@pytest.fixture
def refusing_port() -> Iterator[int]:
    server = HTTPServer(("127.0.0.1", 0), Refuses)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server.server_address[1]
    server.shutdown()
    server.server_close()


def _planted(tmp_path: Path) -> tuple[Path, Path, Path]:
    home = tmp_path / "qmx"
    login = home / "claude" / ".credentials.json"
    login.parent.mkdir(parents=True)
    login.write_text(json.dumps({"token": CANARY}), encoding="utf-8")
    (home / "settings.toml").write_text(f'note = "{CANARY}"', encoding="utf-8")
    personal = tmp_path / "me" / ".claude"
    personal.mkdir(parents=True)
    return home, login, personal


def test_measure_never_opens_a_path_and_never_reads_the_keyring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, refusing_port: int
) -> None:
    home, login, personal = _planted(tmp_path)
    targets = exposure_targets(
        home, ["qmx/kimi", "qmx/gone"], refusing_port, [login, home / "rclone.conf"], personal
    )
    opened: list[object] = []

    def refuse(*args: object, **_: object) -> Any:
        opened.append(args[0] if args else None)
        raise AssertionError("the probe opened a file")

    def no_read(*_: object) -> str:
        raise AssertionError("the probe read a keyring value")

    for owner, name in (
        (builtins, "open"),
        (io, "open"),
        (os, "open"),
        (pathlib.Path, "open"),
        (pathlib.Path, "read_text"),
        (pathlib.Path, "read_bytes"),
    ):
        monkeypatch.setattr(owner, name, refuse)
    monkeypatch.setattr(keyring, "get_password", no_read)
    monkeypatch.setattr(keyring, "get_credential", no_read)

    findings = measure(targets, listed=frozenset({"qmx/kimi"}), platform="win32")

    bash = "agent Bash can read it; the gate blocks only the file tools"
    writes = "agent Bash can write into it; the gate blocks only the file tools"
    assert opened == []
    assert [(f.target.value, f.reachable, f.detail) for f in findings] == [
        ("qmx/gone", False, "not in the credential store"),
        ("qmx/kimi", True, qma.harness.money.KEYRING_READABLE),
        (str(home / "settings.toml"), True, bash),
        (str(home / "control.db"), False, "absent"),
        (str(home / "portfolio.db"), False, "absent"),
        (str(login), True, bash),
        (str(home / "rclone.conf"), False, "absent"),
        (str(personal), True, bash),
        (str(home), True, writes),
        (str(personal), True, writes),
        (f"127.0.0.1:{refusing_port}", False, "refused without a bearer (401)"),
    ]
    assert CANARY not in repr(findings)


def test_keyring_reachability_is_not_measured_where_only_a_read_would_tell() -> None:
    target = ExposureTarget("keyring_entry", "qmx/kimi")
    for platform, listed in (("linux", frozenset({"qmx/kimi"})), ("darwin", None)):
        (finding,) = measure([target], listed=listed, platform=platform)
        assert finding.reachable is None
        assert finding.detail == qma.harness.money.NOT_MEASURED_KEYRING


def test_the_probe_child_fails_any_open_of_a_target(tmp_path: Path) -> None:
    secret = tmp_path / "settings.toml"
    secret.write_text(CANARY, encoding="utf-8")
    code = (
        "import sys\n"
        "from qma.harness.money import ExposureTarget, guard_opens\n"
        "guard_opens([ExposureTarget('read_path', sys.argv[1])])\n"
        "open(sys.argv[1]).read()\n"
    )
    done = subprocess.run(
        [sys.executable, "-I", "-c", code, str(secret)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 1
    assert "PermissionError: the exposure probe never opens" in done.stderr
    assert CANARY not in done.stderr


def test_the_probe_child_never_calls_get_password(tmp_path: Path) -> None:
    home, login, personal = _planted(tmp_path)
    targets = exposure_targets(home, ["qmx/x-absent"], None, [login], personal)
    code = (
        "import keyring\n"
        "def boom(*_):\n"
        "    raise SystemExit('get_password called')\n"
        "keyring.get_password = boom\n"
        "keyring.get_credential = boom\n"
    ) + qma.harness.money.PROBE_BOOT
    rows = json.dumps([{"kind": t.kind, "value": t.value} for t in targets])
    done = subprocess.run(
        [sys.executable, "-I", "-c", code, qma.harness.money.__file__],
        input=rows,
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    found = json.loads(done.stdout)
    assert found[0] == ["keyring_entry", "qmx/x-absent", False, "not in the credential store"]
    assert [row[1] for row in found] == [t.value for t in targets]
    assert CANARY not in done.stdout


def test_the_probe_subprocess_reports_without_the_canary(tmp_path: Path) -> None:
    home, login, personal = _planted(tmp_path)
    targets = exposure_targets(home, ["qmx/x-absent"], None, [login], personal)
    report = asyncio.run(run_exposure_probe(dict(os.environ), targets, cli_version="2.1.299"))
    assert [(f.target, f.reachable) for f in report.findings] == [
        (targets[0], False),
        (targets[1], True),
        (targets[2], False),
        (targets[3], False),
        (targets[4], True),
        (targets[5], True),
        (targets[6], True),
        (targets[7], True),
    ]
    assert report.cli_version == "2.1.299"
    assert CANARY not in json.dumps(report.document())
    assert report.readable() == (str(home / "settings.toml"), str(login), str(personal))


def test_a_probe_that_cannot_run_reports_every_target_unmeasured(tmp_path: Path) -> None:
    targets = (ExposureTarget("read_path", str(tmp_path)),)
    report = asyncio.run(run_exposure_probe({}, targets, cli_version="x"))
    (finding,) = report.findings
    assert finding.reachable is None
    assert finding.detail.startswith("not measured: the probe did not finish")


def test_get_doctor_never_probes_and_the_post_probes_once(tmp_path: Path) -> None:
    home = QmxHome(tmp_path / "qmx")
    control = control_service(home)
    calls: list[bool] = []

    async def lines(probe: bool) -> list[DoctorLine]:
        calls.append(probe)
        return [DoctorLine("money posture", False, "speed_bump")]

    extra = router(home, control, scrubbed=(), keep=(), harness_lines=lines)
    with TestClient(create_app(control, BEARER, extra_routers=[extra])) as rest:
        for _ in range(10):
            assert rest.get("/api/doctor", headers=HEADERS).status_code == 200
        posted = rest.post("/api/doctor/probe", headers=HEADERS).json()
        assert rest.post("/api/doctor/probe").status_code == 401
    assert calls == [False] * 10 + [True]
    assert posted["lines"][-1] == {"name": "money posture", "ok": False, "detail": "speed_bump"}


def test_the_harness_names_unproven_entries_and_stores_one_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(name, str(tmp_path / "throwaway"))
    home = QmxHome(tmp_path / "qmx")
    control = control_service(home)
    control.settings_put(
        "providers",
        {
            "kimi": {
                "base_url": "https://api.moonshot.ai/anthropic",
                "credential_ref": "qmx/kimi",
                "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "kimi-k2.5"),
            }
        },
    )
    listed = frozenset({"qmx/kimi", "qmx/chatgpt", "qmx/ctrader-trading", "qmx/x-test"})
    monkeypatch.setattr(qma.harness.harness, "store_names", lambda: listed)
    proofs = home.state_dir / "scope-proofs"
    proofs.mkdir(parents=True)
    proof = {"credential": "qmx/ctrader-trading", "refused_for_scope": True}
    (proofs / "ctrader.json").write_text(json.dumps(proof), encoding="utf-8")
    probes: list[tuple[ExposureTarget, ...]] = []

    async def fake_probe(
        env: dict[str, str], targets: tuple[ExposureTarget, ...], *, cli_version: str
    ) -> ExposureReport:
        probes.append(targets)
        assert env["CLAUDE_CONFIG_DIR"] == str(home.plan_dir)
        found = tuple(
            ExposureFinding(t, t.kind == "keyring_entry", "fake") for t in targets[:4]
        )
        return ExposureReport(datetime(2026, 10, 15, tzinfo=UTC), cli_version, found)

    monkeypatch.setattr(qma.harness.harness, "run_exposure_probe", fake_probe)

    async def body() -> None:
        harness = await Harness.open(home, control=control)
        try:
            plain = {line.name: line for line in await harness.doctor()}
            assert probes == []
            assert plain["exposure probe"].detail == "not run yet; POST /api/doctor/probe runs it"
            probed = {line.name: line for line in await harness.doctor(probe=True)}
            assert len(probes) == 1
            assert probed["exposure probe"].detail.endswith(
                "agent Bash can read: qmx/chatgpt, qmx/control-token, qmx/ctrader-trading, "
                "qmx/firecrawl"
            )
            assert probed["relay"].detail.startswith("0 live grants; refused: bearer 0")
            assert "agent process cap" in probed
            money = (await harness.usage()).document()["money"]
            await harness.doctor()
            assert len(probes) == 1
        finally:
            await harness.close()
        assert money["posture"] == "SPEED_BUMP"
        assert money["unproven"] == ["qmx/firecrawl", "qmx/x-test"]
        assert money["readable_from_agent_bash"] == [
            "qmx/chatgpt",
            "qmx/control-token",
            "qmx/ctrader-trading",
            "qmx/firecrawl",
        ]
        assert money["note"].startswith(
            "SPEED_BUMP: no stored proof that these credentials cannot trade: qmx/firecrawl, "
            "qmx/x-test."
        )

    asyncio.run(body())


LIVE = Path(__file__).resolve().parents[4] / "scripts" / "live" / "qma"


def test_s27_refuses_any_account_not_marked_demo_before_reading_a_credential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "path", [str(LIVE), *sys.path])
    sys.modules.pop("s27_broker_scope", None)
    s27 = importlib.import_module("s27_broker_scope")
    from qmx_broker.models import BrokerSettings  # noqa: PLC0415

    def connection(name: str, environment: str, account: str) -> dict[str, Any]:
        return {
            "id": name,
            "credential_ref": f"qmx/{name}",
            "environment": environment,
            "accounts": [{"id": account, "currency": "USD"}],
        }

    settings = BrokerSettings.model_validate(
        {
            "brokers": [
                {
                    "id": "ic",
                    "name": "IC",
                    "adapter": "ctrader",
                    "connections": [
                        connection("demo", "demo", "111"),
                        connection("live", "live", "222"),
                    ],
                }
            ]
        }
    )
    (target,) = s27.demo_targets(settings, ["111"])
    assert (target.account.id, target.credential) == ("111", "qmx/demo")
    with pytest.raises(s27.Refused, match="account 222 is not marked demo"):
        s27.demo_targets(settings, ["111", "222"])
    with pytest.raises(s27.Refused, match="account 333 is not listed"):
        s27.demo_targets(settings, ["333"])
    sys.modules.pop("s27_broker_scope", None)
