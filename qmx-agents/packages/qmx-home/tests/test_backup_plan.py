"""`[backup]` read into one plan, with its storages from `[engine]`, and the second drive QMX
proposes (design 06 sections 4 and 5, design 62 L1)."""

from __future__ import annotations

from datetime import time
from pathlib import Path

import pytest

from qmx_home import resolve
from qmx_home.backup.plan import (
    PC_POLICY,
    UPKEEP,
    Keep,
    Plan,
    PlanRefused,
    Policy,
    Storage,
    defaults,
    orphans_dropped,
    parse,
    proposal,
)

GB = 1_000_000_000


def engine(**rows: dict[str, object]) -> dict[str, object]:
    return {"host_name": "pc", "disk": {"floor_gb": 3}, "placement": rows}


def test_a_full_section_parses_its_storages_from_engine_and_old_keys_are_left_alone(
    tmp_path: Path,
) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    usb = tmp_path / "usb"
    section = {
        "on": False,
        "remote": "b2",
        "repository": "git@example:backup.git",
        "targets": [{"id": "old"}],
        "leave_out": ["exports/**"],
        "place": {
            "pc": {"every": "2h", "keep": {"hours": 4, "days": 0}, "save": ["recipe"]},
            "01J-USB": {"every": "1w", "at": "22:30", "keep": {"months": 6}, "on": False},
            "01J-GONE": {"every": "1d"},
        },
        "upkeep": {"drill_every": "1w", "drill_sample": 50},
    }
    rows = engine(
        usb={"id": "01J-USB", "via": "folder", "can": ["keep"], "path": str(usb)},
        server={"provider": "ssh", "kind": "owned", "host": "s"},
        drive={"id": "01J-DRV", "via": "rclone", "can": ["keep"], "remote": "qmx-01J-DRV"},
    )

    plan = parse(section, layout, rows)

    assert (plan.on, plan.leave_out, plan.floor_gb) == (False, ("exports/**",), 3.0)
    assert plan.pc == Policy(save=("recipe",), every="2h", keep=Keep(hours=4))
    assert plan.storages == (
        Storage(
            "01J-USB",
            "usb",
            "folder",
            usb,
            Policy(False, every="1w", at=time(22, 30), keep=Keep(days=14, weeks=8, months=6)),
        ),
        Storage("01J-DRV", "drive", "rclone", None),
    )
    assert [s.id for s in plan.sending] == ["01J-USB"]
    assert (plan.upkeep.drill_every, plan.upkeep.drill_sample) == ("1w", 50)
    assert parse({"remote": "b2", "bucket": "apps"}, layout) == Plan()


@pytest.mark.parametrize(
    ("place", "line"),
    [
        ({"at": "3am"}, "[backup.place.01J-USB]: at must be a time such as 03:00, not '3am'"),
        (
            {"every": "30min"},
            "[backup.place.01J-USB]: every is a span of an hour or more, such as 1h, 1d or 1w",
        ),
        (
            {"save": ["recipe", "secret"]},
            "[backup.place.01J-USB]: save lists classes from recipe, content, result, prices",
        ),
        (
            {"colour": "red"},
            "[backup.place.01J-USB] has colour; use at, every, floor, keep, on, save",
        ),
    ],
)
def test_a_bad_policy_is_refused_by_name(
    tmp_path: Path, place: dict[str, object], line: str
) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    rows = engine(usb={"id": "01J-USB", "via": "folder", "can": ["keep"], "path": str(tmp_path)})
    with pytest.raises(PlanRefused) as refused:
        parse({"place": {"01J-USB": place}}, layout, rows)
    assert str(refused.value) == line


def test_an_unknown_key_and_a_storage_inside_the_folder_are_refused(tmp_path: Path) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    inside = engine(
        mine={"via": "folder", "can": ["keep"], "path": str(layout.root / "backups" / "mine")},
    )

    with pytest.raises(PlanRefused) as unknown:
        parse({"tape": "E:"}, layout)
    with pytest.raises(PlanRefused) as nested:
        parse({}, layout, inside)

    assert str(unknown.value) == (
        "[backup] has tape, which QMX does not know; use leave_out, on, place, rclone_path, upkeep"
    )
    assert str(nested.value) == (
        f"the storage 'mine': {layout.root / 'backups' / 'mine'} is inside the QMX folder "
        f"{layout.root}, so a copy there is lost with the folder; pick a folder on another drive"
    )


def test_the_read_names_every_default_and_a_storage_with_no_policy_reads_them_all() -> None:
    rows = engine(usb={"id": "01J-USB", "via": "folder", "can": ["keep"]})

    shown = defaults({"repository": "kept"}, rows)

    assert shown == {
        "repository": "kept",
        "on": True,
        "leave_out": [],
        "rclone_path": "",
        "upkeep": {
            "on": True,
            "every": "1mo",
            "repack_past": 0.05,
            "repack_per_run": "all",
            "safety": "24h",
            "check_slice": 12,
            "drill": True,
            "drill_every": "1mo",
            "drill_sample": 200,
            "before_update_wait": "10m",
        },
        "place": {
            "pc": {
                "on": True,
                "save": ["recipe", "content", "result", "prices"],
                "every": "1h",
                "at": "03:00",
                "keep": {"hours": 48, "days": 7},
            },
            "01J-USB": {
                "on": True,
                "save": ["recipe", "content", "result", "prices"],
                "every": "1d",
                "keep": {"days": 14, "weeks": 8, "months": 12},
                "at": "03:00",
                "floor": "auto",
            },
        },
    }
    assert dict(UPKEEP) == shown["upkeep"]
    assert PC_POLICY.keep == Keep(hours=48, days=7)


def test_a_policy_whose_row_is_gone_is_dropped_and_this_pcs_stays() -> None:
    rows = engine(usb={"id": "01J-USB", "via": "folder", "can": ["keep"]})
    section = {
        "repository": "kept",
        "place": {"pc": {"every": "2h"}, "01J-USB": {}, "01J-GONE": {"every": "1d"}},
    }

    assert orphans_dropped(section, rows) == {
        "repository": "kept",
        "place": {"pc": {"every": "2h"}, "01J-USB": {}},
    }
    assert orphans_dropped({"place": {"01J-GONE": {}}}, {}) == {}


@pytest.mark.skipif(not Path("C:/").drive, reason="drive letters are a Windows matter")
def test_the_second_drive_is_proposed_only_when_the_first_copy_leaves_it_room(
    tmp_path: Path,
) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    own = Path(tmp_path.anchor)
    other = Path("Q:/") if own != Path("Q:/") else Path("R:/")
    his = {own: (1000 * GB, 400 * GB), other: (237 * GB, 22 * GB)}
    roomy = {own: (1000 * GB, 400 * GB), other: (237 * GB, 150 * GB)}

    assert proposal(layout, [own, other], lambda d: his[d]) is None
    offered = proposal(layout, [own, other], lambda d: roomy[d])
    assert offered is not None
    assert offered.path == other / "QMX-backup"
    assert offered.line == (
        f"QMX proposes {other / 'QMX-backup'} on another drive for a daily copy of your work; "
        "accept it in Settings, Sync to my storage, or connect a USB disk instead"
    )
    assert proposal(layout, [own], lambda d: roomy[d]) is None


@pytest.mark.skipif(not Path("C:/").drive, reason="a junction is a Windows link")
def test_a_storage_reached_through_a_junction_into_the_folder_is_refused(tmp_path: Path) -> None:
    import _winapi

    layout = resolve(tmp_path / "QMX", create=True)
    door = tmp_path / "looks-elsewhere"
    _winapi.CreateJunction(str(layout.backups), str(door))  # pyright: ignore[reportAttributeAccessIssue]
    rows = engine(door={"via": "folder", "can": ["keep"], "path": str(door)})

    with pytest.raises(PlanRefused) as refused:
        parse({}, layout, rows)

    assert str(refused.value).startswith(f"the storage 'door': {door} is inside")


def test_the_rclone_path_is_an_optional_string_read_as_written(tmp_path: Path) -> None:
    layout = resolve(tmp_path / "QMX", create=True)

    assert parse({}, layout).rclone_path == ""
    assert parse({"rclone_path": "D:/Tools/rclone/rclone.exe"}, layout).rclone_path == (
        "D:/Tools/rclone/rclone.exe"
    )
    with pytest.raises(PlanRefused) as refused:
        parse({"rclone_path": 3}, layout)
    assert str(refused.value) == "[backup] rclone_path must be the path of rclone, or empty"
