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


def folder(path: Path, *, labelled: bool = True) -> Path:
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

    assert resolve(drives=[]).root == named


def test_the_pointer_names_the_folder_and_its_home_is_data(profile: Path, tmp_path: Path) -> None:
    pointed = folder(tmp_path / "QMX")
    point_at(pointed)

    assert resolve(drives=[]).home == pointed / "data"


def test_a_lost_pointer_falls_through_to_the_drive_scan(profile: Path, tmp_path: Path) -> None:
    point_at(tmp_path / "moved-away")
    drive = tmp_path / "drive-e"
    found = folder(drive / "QMX", labelled=True)

    assert resolve(drives=[tmp_path / "drive-d", drive]).root == found


def test_the_scan_passes_over_a_qmx_folder_without_a_real_label(
    profile: Path, tmp_path: Path
) -> None:
    folder(tmp_path / "drive-d" / "QMX", labelled=False)
    junk = folder(tmp_path / "drive-e" / "QMX", labelled=False)
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


def test_create_makes_exactly_the_label_and_the_five_parts(profile: Path, tmp_path: Path) -> None:
    made = resolve(tmp_path / "lane" / "QMX", create=True, drives=[])

    label = Label.parse(made.label.read_text(encoding="utf-8"))
    assert made.root == (tmp_path / "lane" / "QMX").resolve()
    assert tree(made.root) == ["backups", "cache", "data", "keys", "logs", LABEL]
    assert made.home == made.root / "data"
    assert (label.format_version, label.created_by) == (2, "0.1.0")
    assert resolve(made.root, create=True, drives=[]) == made
    assert Label.parse(made.label.read_text(encoding="utf-8")) == label


def test_a_flat_home_is_refused_with_the_first_start_and_left_alone(
    profile: Path, tmp_path: Path
) -> None:
    home = folder(tmp_path / "flat-home", labelled=False)
    (home / "control.db").write_text("", encoding="utf-8")

    with pytest.raises(NoQmxFolder) as refused:
        resolve(home, create=True, drives=[])

    assert str(refused.value) == (
        f"{home} holds QMX data in the old flat layout. QMX does not open it and never changes "
        "it. On This PC, bring it into a new QMX folder with the first start: python -m qmx_host "
        f"bring-in --home <new QMX folder> --old {home}. A server's folder is moved into the "
        "tree by qmx-recover repair"
    )
    assert tree(home) == ["control.db"]


def test_a_folder_that_is_not_a_qmx_home_is_refused_without_the_layout_command(
    profile: Path, tmp_path: Path
) -> None:
    documents = folder(tmp_path / "Documents", labelled=False)
    (documents / "cv.docx").write_text("cv", encoding="utf-8")
    (documents / "taxes").mkdir()
    (documents / "taxes" / "2025.pdf").write_text("pdf", encoding="utf-8")

    with pytest.raises(NoQmxFolder) as refused:
        resolve(documents, create=True, drives=[])

    assert str(refused.value) == (
        f"{documents} is not a QMX folder: it has no qmx-home.toml and none of a QMX home's own "
        "files; pass the folder QMX made, or --create with an empty one"
    )
    assert tree(documents) == ["cv.docx", "taxes", "taxes/2025.pdf"]


def test_an_empty_folder_needs_create(profile: Path, tmp_path: Path) -> None:
    empty = folder(tmp_path / "empty", labelled=False)

    with pytest.raises(NoQmxFolder) as refused:
        resolve(empty, drives=[])

    assert str(refused.value) == (
        f"no QMX folder at {empty}: it has no qmx-home.toml (pass --create to make one)"
    )
    assert tree(empty) == []


def test_a_pointer_with_a_bom_and_a_double_quoted_windows_path_is_read(
    profile: Path, tmp_path: Path
) -> None:
    pointed = folder(tmp_path / "new" / "QMX")
    pointer = pointer_file()
    assert pointer is not None
    pointer.parent.mkdir(parents=True)
    pointer.write_text(f'home = "{pointed}"\n', encoding="utf-8-sig")

    assert resolve(drives=[]).root == pointed


def test_a_utf16_pointer_is_refused_by_name(profile: Path, tmp_path: Path) -> None:
    pointed = folder(tmp_path / "QMX")
    pointer = pointer_file()
    assert pointer is not None
    pointer.parent.mkdir(parents=True)
    pointer.write_text(f"home = '{pointed}'\n", encoding="utf-16")

    with pytest.raises(NoQmxFolder) as refused:
        resolve(drives=[])

    assert str(refused.value).startswith(f"the pointer {pointer} cannot be read (")
    assert str(refused.value).endswith("): write it again as UTF-8, or pass --home")


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


def kind_of(flag: Path | None = None, *, create: bool = False) -> tuple[str, Path | None]:
    with pytest.raises(NoQmxFolder) as refused:
        resolve(flag, create=create, drives=[])
    return refused.value.kind, refused.value.folder


def test_each_refusal_says_whether_nothing_was_found_old_data_was_or_a_folder_was_refused(
    profile: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    flat = folder(tmp_path / "flat", labelled=False)
    (flat / "control.db").write_text("", encoding="utf-8")
    empty = folder(tmp_path / "empty", labelled=False)
    newer = folder(tmp_path / "newer", labelled=False)
    newer_label = Label("0193aaaa-0000-7000-8000-000000000000", 3, "9.0.0", "9.0.0", min_reader=3)
    (newer / LABEL).write_text(newer_label.dump(), encoding="utf-8")
    nested = folder(tmp_path / "home") / "data"
    nested.mkdir()
    documents = folder(tmp_path / "Documents", labelled=False)
    (documents / "cv.docx").write_text("cv", encoding="utf-8")

    found = {
        "nothing": kind_of(),
        "typo": kind_of(tmp_path / "typo"),
        "empty": kind_of(empty),
        "flat": kind_of(flat),
        "newer": kind_of(newer),
        "nested": kind_of(nested),
        "documents": kind_of(documents),
        "create without a flag": kind_of(create=True),
    }
    monkeypatch.setenv("QMX_HOME", str(tmp_path / "gone"))
    found["QMX_HOME"] = kind_of()

    assert found == {
        "nothing": ("missing", None),
        "typo": ("missing", (tmp_path / "typo").resolve()),
        "empty": ("missing", empty),
        "flat": ("old", flat),
        "newer": ("refused", newer),
        "nested": ("refused", nested.resolve()),
        "documents": ("refused", documents),
        "create without a flag": ("refused", None),
        "QMX_HOME": ("refused", (tmp_path / "gone").resolve()),
    }


def test_a_pointer_to_a_folder_that_is_gone_is_refused_when_the_scan_finds_none(
    profile: Path, tmp_path: Path
) -> None:
    gone = folder(tmp_path / "usb" / "QMX")
    point_at(gone)
    (tmp_path / "usb").rename(tmp_path / "unplugged")

    with pytest.raises(NoQmxFolder) as refused:
        resolve(drives=[])

    assert (refused.value.kind, refused.value.folder) == ("refused", gone)
    assert str(refused.value) == (
        f"the QMX folder {gone} is not there. If it is on a drive that is unplugged, plug the "
        "drive in and start QMX again; if you moved the folder, open it where it is now"
    )


def test_an_unreadable_pointer_is_refused_not_missing(profile: Path) -> None:
    pointer = pointer_file()
    assert pointer is not None
    pointer.parent.mkdir(parents=True)
    pointer.write_text("recent = []\n", encoding="utf-8")

    assert kind_of() == ("refused", None)
    assert NoQmxFolder("a line raised elsewhere").kind == "refused"


def test_a_label_reads_back_what_it_wrote() -> None:
    label = Label("0193aaaa-0000-7000-8000-000000000000", 2, "0.1.0", "0.2.0")

    assert Label.parse(label.dump()) == label
    with pytest.raises(ValueError, match="not a qmx-home label"):
        Label.parse('format = "qmx-home"\nformat_version = "one"\n')
