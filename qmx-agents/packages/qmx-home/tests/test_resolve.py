from __future__ import annotations

from pathlib import Path

import pytest

from qmx_home import LABEL, Label, Layout, NoQmxFolder, pointer_file, resolve


@pytest.fixture
def profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch user profile: every per-user folder the resolver reads points inside it."""
    user = tmp_path / "profile"
    for name, folder in {
        "USERPROFILE": user,
        "HOME": user,
        "APPDATA": user / "AppData" / "Roaming",
        "LOCALAPPDATA": user / "AppData" / "Local",
        "XDG_CONFIG_HOME": user / ".config",
    }.items():
        folder.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv(name, str(folder))
    monkeypatch.delenv("QMX_HOME", raising=False)
    return user


def folder(path: Path, *, labelled: bool = False) -> Path:
    path.mkdir(parents=True)
    if labelled:
        (path / LABEL).write_text(Label.mint().dump(), encoding="utf-8")
    return path.resolve()


def point_at(root: Path) -> None:
    pointer = pointer_file()
    assert pointer is not None
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(f"home = '{root}'\nrecent = ['{root}']\n", encoding="utf-8")


def tree(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def test_the_flag_wins_over_qmx_home_and_the_pointer(
    profile: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    flagged, named, pointed = (folder(tmp_path / name) for name in ("flag", "env", "pointer"))
    monkeypatch.setenv("QMX_HOME", str(named))
    point_at(pointed)

    assert resolve(flagged, drives=[]) == Layout(flagged)


def test_qmx_home_wins_over_the_pointer(
    profile: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    named, pointed = folder(tmp_path / "env"), folder(tmp_path / "pointer")
    monkeypatch.setenv("QMX_HOME", str(named))
    point_at(pointed)

    assert resolve(drives=[]).home == named


def test_the_pointer_names_the_folder_without_a_label(profile: Path, tmp_path: Path) -> None:
    pointed = folder(tmp_path / "flat-home")
    point_at(pointed)

    assert resolve(drives=[]).home == pointed


def test_a_lost_pointer_falls_through_to_the_drive_scan(profile: Path, tmp_path: Path) -> None:
    point_at(tmp_path / "moved-away")
    drive = tmp_path / "drive-e"
    found = folder(drive / "QMX", labelled=True)

    assert resolve(drives=[tmp_path / "drive-d", drive]).root == found


def test_the_scan_passes_over_a_qmx_folder_without_a_real_label(
    profile: Path, tmp_path: Path
) -> None:
    folder(tmp_path / "drive-d" / "QMX")
    junk = folder(tmp_path / "drive-e" / "QMX")
    (junk / LABEL).write_text('format = "something-else"\n', encoding="utf-8")
    found = folder(tmp_path / "drive-f" / "QMX", labelled=True)

    drives = [tmp_path / name for name in ("drive-d", "drive-e", "drive-f")]
    assert resolve(drives=drives).root == found


def test_a_labelled_default_folder_is_found_before_the_drives(
    profile: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    system = tmp_path / "drive-c"
    monkeypatch.setenv("SYSTEMDRIVE", str(system))
    default = folder(profile / "QMX", labelled=True)
    folder(system / "QMX", labelled=True)

    assert resolve(drives=[system]).root == default


def test_nothing_found_refuses_in_one_line_and_creates_nothing(
    profile: Path, tmp_path: Path
) -> None:
    before = tree(tmp_path)

    with pytest.raises(NoQmxFolder) as refused:
        resolve(drives=[tmp_path / "drive-d"])

    assert str(refused.value) == "no QMX folder found: start QMX once, or pass --home"
    assert tree(tmp_path) == before


def test_a_flag_naming_a_missing_folder_refuses_without_create(
    profile: Path, tmp_path: Path
) -> None:
    missing = tmp_path / "typo"

    with pytest.raises(NoQmxFolder) as refused:
        resolve(missing, drives=[])

    assert str(refused.value) == f"no QMX folder at {missing.resolve()}"
    assert not missing.exists()


def test_create_makes_the_flags_folder_with_a_format_1_label(profile: Path, tmp_path: Path) -> None:
    made = resolve(tmp_path / "lane" / "home", create=True, drives=[])

    label = Label.parse(made.label.read_text(encoding="utf-8"))
    assert (made.root, tree(made.root)) == ((tmp_path / "lane" / "home").resolve(), [LABEL])
    assert (label.format_version, label.created_by) == (1, "0.1.0")
    assert resolve(made.root, create=True, drives=[]) == made
    assert Label.parse(made.label.read_text(encoding="utf-8")) == label


def test_create_leaves_an_existing_home_without_a_label(profile: Path, tmp_path: Path) -> None:
    home = folder(tmp_path / "flat-home")
    (home / "settings.toml").write_text("", encoding="utf-8")

    assert resolve(home, create=True, drives=[]).home == home
    assert tree(home) == ["settings.toml"]


def test_create_needs_the_flag(profile: Path) -> None:
    with pytest.raises(NoQmxFolder) as refused:
        resolve(create=True, drives=[])

    assert str(refused.value) == "--create needs --home <path>"


def test_qmx_home_naming_a_missing_folder_refuses(
    profile: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QMX_HOME", str(tmp_path / "gone"))

    with pytest.raises(NoQmxFolder) as refused:
        resolve(drives=[])

    assert (
        str(refused.value)
        == f"QMX_HOME names {(tmp_path / 'gone').resolve()}, which is not a folder"
    )


def test_a_label_reads_back_what_it_wrote() -> None:
    label = Label("0193aaaa-0000-7000-8000-000000000000", 1, "0.1.0", "0.2.0")

    assert Label.parse(label.dump()) == label
    with pytest.raises(ValueError, match="not a qmx-home label"):
        Label.parse('format = "qmx-home"\nformat_version = "one"\n')
