"""The first start after a restore (B5): server sync and fires stay paused until he carries on, the
pause is a merge a Hub cannot undo, the blobs the restore named are purged again, and no host
starts while a restore is being finished."""

from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from qmx_control.service import ControlService
from qmx_engine.control_door import EngineDoor
from qmx_engine.ledger import redact
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.settings import ControlSettings
from qmx_engine.service.context import OPERATOR
from qmx_engine.triggers import rows
from qmx_engine.triggers.cron import Cron
from qmx_home import Layout, resolve
from qmx_home.backup import restore as restoring
from qmx_home.backup.repository import FolderRepository
from qmx_home.files import hold
from qmx_hub.replicate import StorePeer
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.port import Draft
from qmx_library.principal import Principal
from qmx_library.store import Store
from test_backups_service import finished
from test_host import CHAIN

import qmx_host.host
from qmx_host.backups import Backups
from qmx_host.host import Replicator, RestoreFinishing, hear, single_instance

ME = Principal("operator")
ENGINE: Any = "engine"


class Wall:
    """The engine's clock: the wall's time, `behind` it."""

    def __init__(self, behind: timedelta) -> None:
        self.behind = behind

    def now(self) -> datetime:
        return datetime.now(UTC) - self.behind


def control_of(layout: Layout) -> ControlService:
    return ControlService(layout.home, secret_getter=lambda _service, _name: None)


def backups_of(layout: Layout) -> Backups:
    return Backups(layout, control_of(layout), clock=lambda: datetime.now().astimezone(), floor=0)


def quick_copy(layout: Layout) -> str:
    """A quick-undo copy of the folder as it is now; its date."""
    backups = backups_of(layout)
    assert finished(backups, backups.start(None, asked=True).job).state == "finished"
    return FolderRepository(layout.backups / "quick").copies()[-1]


def restored(layout: Layout, stamp: str) -> None:
    """The quick-undo copy `stamp` staged and finished in the folder, as the next start does."""
    restoring.stage(layout, FolderRepository(layout.backups / "quick"), stamp, keep_free=0)
    assert restoring.finish(layout, running=lambda _data: None) is not None


def test_the_engine_reads_the_nested_pause_that_a_settings_update_writes(tmp_path: Path) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    control = control_of(layout)
    settings = ControlSettings(control)
    before = settings.values()["autonomy.paused"]

    control.settings_update("engine", lambda s: {**s, "autonomy": {"paused": True}})

    assert (before, settings.values()["autonomy.paused"]) == (0, 1)


class Server(StorePeer):
    """The Library server, a real store, counting each time a sync asks it for its refs."""

    def __init__(self, store: Store) -> None:
        super().__init__(store)
        self.asked = 0

    def refs(self) -> list[Any]:
        self.asked += 1
        return super().refs()


def test_nothing_from_a_server_or_a_trigger_reaches_a_restored_folder_before_he_carries_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    (layout.home / "settings.toml").write_text(
        '[engine]\nhost_name = "pc-1"\n\n[library]\nprimary = "server"\n', encoding="utf-8"
    )
    control = control_of(layout)
    then = Wall(timedelta(hours=4))

    async def before_the_copy() -> str:
        with Store.open(layout.home / "library", redactor=redact) as store:
            async with EngineDoor.open(
                control, library=EngineLibraryAdapter(store), clock=then
            ) as door:
                svc = door.svc
                item = svc.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR).item
                await svc.tests.run(item, caller=OPERATOR)
                version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
                svc.versions.enable(version, caller=OPERATOR)
                hourly = rows.create(
                    svc.ctx.engine.ledger,
                    workflow_item=svc.versions.get(version).item,
                    pinned_object=version,
                    spec=Cron("0 * * * *", "UTC"),
                    caller=OPERATOR,
                    now=then.now(),
                )
                return hourly.id

    trigger = asyncio.run(before_the_copy())
    stamp = quick_copy(layout)

    def fired() -> list[str]:
        """Each fire that ran, by its status; the occurrences a catch-up covers read skipped."""
        with Reader.open(layout.home) as reader:
            found = rows.fires(reader.connection, trigger)
        return [fire.status for fire in found if fire.status != "skipped"]

    with Store.open(tmp_path / "server", redactor=redact, name="server") as server_store:
        newer = server_store.put(
            ME, Draft("note", "n9", title="saved on the server"), on="main", expected_head=None
        )
        server = Server(server_store)

        def library_client(_home: Path) -> Server:
            return server

        monkeypatch.setattr(qmx_host.host, "library_client", library_client)
        restored(layout, stamp)
        backups = backups_of(layout)

        async def the_start() -> tuple[list[object], list[object]]:
            with Store.open(layout.home / "library", redactor=redact) as store:
                backups.hold_after_restore(store)
                async with EngineDoor.open(control, library=EngineLibraryAdapter(store)) as door:

                    def sync() -> None:
                        replicator = Replicator.for_home(layout.home, store, control)
                        assert replicator is not None
                        replicator.tick()

                    backups.when_carried_on(sync)
                    for _ in range(3):
                        await door.scheduler.tick()
                        await door.scheduler.settle()
                    engine = control.settings_get(ENGINE)
                    before: list[object] = [fired(), server.asked, store.head("n9", "main"), engine]
                    line = backups.carry_on_restore()
                    for _ in range(3):
                        await door.scheduler.tick()
                        await door.scheduler.settle()
                    engine = control.settings_get(ENGINE)
                    after: list[object] = [
                        fired(),
                        server.asked > 0,
                        store.head("n9", "main"),
                        line,
                        engine,
                    ]
            return before, after

        before, after = asyncio.run(the_start())

    assert before == [[], 0, None, {"host_name": "pc-1", "autonomy": {"paused": True}}]
    assert after == [
        ["ok"],
        True,
        (newer.object_id, 1),
        f"server sync and fires run again in {layout.root}; each clocked trigger fires once for "
        "the time it missed, and the runs the copy held carry on",
        {"host_name": "pc-1"},
    ]


class Hub:
    """A Hub whose pause switch reads `autonomy_paused`."""

    def __init__(self) -> None:
        self.autonomy_paused = False
        self.pushed: list[object] = []

    def push(self, row: object) -> Hub:
        self.pushed.append(row)
        return self


@pytest.mark.parametrize(("earlier", "given_back"), [(None, {}), (1, {"autonomy": {"paused": 1}})])
def test_the_pause_is_a_merge_a_hub_does_not_clear_and_carry_on_gives_back_its_earlier_value(
    tmp_path: Path, earlier: int | None, given_back: dict[str, object]
) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    engine: dict[str, Any] = {"host_name": "pc-1", "disk": {"floor_gb": 3}}
    if earlier is not None:
        engine["autonomy"] = {"paused": earlier}
    control_of(layout).settings_put(ENGINE, engine)
    restored(layout, quick_copy(layout))
    hub = Hub()

    sections: list[object] = []
    backups = backups_of(layout)
    for _ in range(2):
        backups = backups_of(layout)
        with Store.open(layout.home / "library", redactor=redact) as store:
            assert backups.hold_after_restore(store) is not None
        for flag in (False, True):
            hub.autonomy_paused = flag
            hear(cast("Any", hub), cast("Any", "row"), backups.control, heed=backups.after is None)
        sections.append(backups.control.settings_get(ENGINE))
    backups.carry_on_restore()
    given = backups.control.settings_get(ENGINE)
    with Store.open(layout.home / "library", redactor=redact) as store:
        again = backups_of(layout).hold_after_restore(store)

    paused = {**engine, "autonomy": {"paused": True}}
    assert sections == [paused, paused]
    assert hub.pushed == ["row"] * 4
    assert given == {"host_name": "pc-1", "disk": {"floor_gb": 3}, **given_back}
    assert again is None


@pytest.mark.parametrize("role", ["writer", "replica"])
def test_each_blob_the_restore_names_is_purged_again_on_a_writer_with_its_ref(
    tmp_path: Path, role: str, capsys: pytest.CaptureFixture[str]
) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    with Store.open(layout.home / "library", redactor=redact) as store:
        put = store.put(
            ME,
            Draft("source", "paper", title="A paper", blobs={"content": b"\x00a key was in here"}),
            on="main",
            expected_head=None,
        )
        blob = store.get(ME, put.object_id).blobs["content"].blob_id
    stamp = quick_copy(layout)
    with Store.open(layout.home / "library", redactor=redact) as store:
        store.purge(ME, blob, "a key was in it")
    restored(layout, stamp)
    item, ref = (f"{kind}{blob.removeprefix('sha256:')}" for kind in ("purge:", "refs/purges/"))

    found: list[object] = []
    for _ in range(2):
        with Store.open(layout.home / "library", redactor=redact, role=cast("Any", role)) as store:
            backups_of(layout).hold_after_restore(store)
            found.append((store.purged(blob), store.has_blob(blob), store.head(item, ref)))

    head = ("purged", 1) if role == "writer" else None
    assert found == [(True, False, head), (True, False, head)]
    assert "library:" not in capsys.readouterr().err


def test_no_host_starts_while_a_restore_is_finishing_and_a_host_lets_the_restore_lock_go(
    tmp_path: Path,
) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    lock = layout.backups / "restore.lock"

    with hold(lock, "a finish runs"), pytest.raises(RestoreFinishing) as refused:  # noqa: SIM117
        with single_instance(layout.home):
            pass
    with single_instance(layout.home), hold(lock, "taken while the host runs"):
        pass

    assert str(refused.value) == (
        f"QMX did not start: a restore is finishing in {layout.root}; start QMX again when it has"
    )


def interrupted(layout: Layout, run_id: str) -> None:
    """A run whose attempt was in flight when the copy was made."""
    at = datetime.now(UTC).isoformat()
    slot: dict[str, Any] = {"node_id": "start", "iteration": 0, "partition": None, "attempt": 1}
    with Ledger.open(layout.home) as ledger:
        ledger.append(run_id, "run_created", {}, at=at)
        ledger.append(run_id, "run_input", {"inputs": {}}, at=at)
        ledger.append(run_id, "node_scheduled", {**slot, "memo_key": "m"}, at=at)
        ledger.append(run_id, "node_started", slot, at=at)


def test_the_view_names_the_runs_that_resume_on_carry_on_and_the_folders_set_aside(
    tmp_path: Path,
) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    interrupted(layout, "run-held")
    restored(layout, quick_copy(layout))
    restored(layout, quick_copy(layout))
    backups = backups_of(layout)
    with Store.open(layout.home / "library", redactor=redact) as store:
        backups.hold_after_restore(store)

    view = backups.view()
    row = backups.doctor_line()

    after = cast("dict[str, Any]", view["after_restore"])
    aside = cast("dict[str, Any]", view["set_aside"])
    folders = [r["folder"] for r in aside["folders"]]
    assert after["interrupted"] == ["run-held"]
    assert after["line"].endswith("; 1 run the copy held resumes then: run-held")
    assert after["line"] in row.detail
    assert not row.ok
    assert len(folders) == 2
    assert all(re.fullmatch(r"backups/before-restore-\d{8}T\d{12}Z", f) for f in folders)
    assert aside["bytes"] == sum(r["bytes"] for r in aside["folders"]) > 0
    assert aside["free_bytes"] > 0
    assert aside["line"].startswith("2 folders set aside by earlier restores hold ")
