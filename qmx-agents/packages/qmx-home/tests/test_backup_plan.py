"""`[backup]` read into one plan, and the second drive QMX proposes (design 62 C2, L1)."""

from __future__ import annotations

from datetime import time
from pathlib import Path

import pytest

from qmx_home import resolve
from qmx_home.backup.plan import Keep, Plan, PlanRefused, Target, parse, proposal

GB = 1_000_000_000


def test_a_full_section_parses_and_the_volume_keys_are_left_alone(tmp_path: Path) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    usb = tmp_path / "usb" / "QMX-backup"
    section = {
        "remote": "b2",
        "bucket": "apps",
        "repository": "git@example:backup.git",
        "quick_undo": {"hours": 24, "days": 3},
        "targets": [
            {
                "id": "usb",
                "kind": "folder",
                "path": str(usb),
                "every": "week",
                "at": "22:30",
                "keep": {"daily": 7, "monthly": 6},
                "on": False,
            },
            {"id": "c-drive", "path": str(tmp_path / "elsewhere")},
        ],
        "leave_out": ["exports/**"],
        "drill": {"every": "week", "sample": 50},
        "keys": {"public": "abc"},
    }

    plan = parse(section, layout)

    assert plan.quick_undo == Keep(hours=24, days=3)
    assert plan.targets == (
        Target("usb", "folder", usb, "week", time(22, 30), Keep(days=7, weeks=8, months=6), False),
        Target("c-drive", "folder", tmp_path / "elsewhere"),
    )
    assert (plan.leave_out, plan.drill.sample, dict(plan.keys)) == (
        ("exports/**",),
        50,
        {"public": "abc"},
    )
    assert parse({"remote": "b2", "bucket": "apps"}, layout) == Plan()


@pytest.mark.parametrize(
    ("row", "line"),
    [
        (
            {"id": "t", "kind": "tape"},
            "backup place 't': the kind 'tape' is not one QMX knows; use folder",
        ),
        ({"id": "t", "at": "3am"}, "backup place 't': at must be a time such as 03:00, not '3am'"),
        (
            {"id": "t", "every": "month"},
            "backup place 't': every must be hour, day or week, not 'month'",
        ),
        (
            {"id": "t", "colour": "red"},
            "backup place 1 has colour, which a backup place does not have",
        ),
    ],
)
def test_a_bad_row_is_refused_by_name(tmp_path: Path, row: dict[str, object], line: str) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    with pytest.raises(PlanRefused) as refused:
        parse({"targets": [{"path": str(tmp_path / "usb"), **row}]}, layout)
    assert str(refused.value) == line


def test_a_duplicate_id_and_a_target_inside_the_folder_are_refused(tmp_path: Path) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    twice = [{"id": "usb", "path": str(tmp_path / "a")}, {"id": "usb", "path": str(tmp_path / "b")}]
    inside = [{"id": "inside", "path": str(layout.root / "backups" / "mine")}]

    with pytest.raises(PlanRefused) as duplicate:
        parse({"targets": twice}, layout)
    with pytest.raises(PlanRefused) as nested:
        parse({"targets": inside}, layout)

    assert str(duplicate.value) == "backup place 2: the id 'usb' is used twice"
    assert str(nested.value) == (
        f"backup place 'inside': {layout.root / 'backups' / 'mine'} is inside the QMX folder "
        f"{layout.root}, so a copy there is lost with the folder; name a folder on another drive"
    )


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
        "accept it in Settings, Data and backups, or name a USB disk instead"
    )
    assert proposal(layout, [own], lambda d: roomy[d]) is None
