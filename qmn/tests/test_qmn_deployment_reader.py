"""No-follow deployment reads preserve containment under hostile paths/races."""

from __future__ import annotations

import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from qmf.core import is_refusal
from qmn.host import configured_runtime as runtime

# These tests deliberately exercise the private filesystem security seam.
# pyright: reportPrivateUsage=false


def test_reader_reads_nested_file_with_exact_size_bound(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    payload = b"x" * (1 << 20)
    (nested / "deployment.json").write_bytes(payload)
    assert runtime._read_deployment_no_follow(tmp_path, Path("nested/deployment.json")) == payload
    (nested / "deployment.json").write_bytes(payload + b"x")
    with pytest.raises(OSError):
        runtime._read_deployment_no_follow(tmp_path, Path("nested/deployment.json"))


@pytest.mark.parametrize("relative", ["..", "../outside.json", "/absolute.json", ""])
def test_reader_rejects_traversal_and_non_file_paths(tmp_path: Path, relative: str) -> None:
    with pytest.raises((OSError, ValueError)):
        runtime._read_deployment_no_follow(tmp_path, Path(relative))


def test_reader_rejects_directory_leaf(tmp_path: Path) -> None:
    (tmp_path / "directory").mkdir()
    with pytest.raises(OSError):
        runtime._read_deployment_no_follow(tmp_path, Path("directory"))


def _directory_link(link: Path, target: Path) -> None:
    if os.name == "nt":
        # Junctions exercise real reparse points without symlink privilege.
        env = dict(os.environ, QMN_TEST_LINK=str(link), QMN_TEST_TARGET=str(target))
        powershell = shutil.which("powershell")
        assert powershell is not None
        completed = subprocess.run(
            [
                powershell,
                "-NoProfile",
                "-Command",
                "New-Item -ItemType Junction -Path $env:QMN_TEST_LINK "
                "-Target $env:QMN_TEST_TARGET -ErrorAction Stop | Out-Null",
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert link.is_junction()
    else:
        link.symlink_to(target, target_is_directory=True)


@pytest.mark.parametrize("root_alias", [False, True])
def test_reader_and_preflight_reject_reparse_directory(tmp_path: Path, root_alias: bool) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "deployment.json").write_bytes(b"{}")
    root = tmp_path / "root"
    root.mkdir()
    link = root / "linked"
    _directory_link(link, outside)
    reader_root = link if root_alias else root
    relative = Path("deployment.json") if root_alias else Path("linked/deployment.json")
    try:
        with pytest.raises((OSError, ValueError)):
            runtime._read_deployment_no_follow(reader_root, relative)
        if not root_alias:
            refused = runtime.assess_configured_runtime(
                reader_root / relative, qmx_root=reader_root
            )
            assert is_refusal(refused)
            assert "readable beneath QMX_ROOT" in str(refused.context.get("reason"))
    finally:
        if os.name == "nt":
            link.rmdir()
        else:
            link.unlink()


def test_preflight_pins_operator_root_before_concurrent_pointer_switch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qmf.core import is_ok
    from test_qmn_configured_composition import valid_deployment

    physical = tmp_path / "commit-tree"
    physical.mkdir()
    deployment = valid_deployment(physical)
    outside = tmp_path / "other-tree"
    outside.mkdir()
    (outside / deployment.name).write_bytes(b"hostile bytes")
    pointer = tmp_path / "current"
    _directory_link(pointer, physical)
    original_read = runtime._read_deployment_no_follow

    def switch_then_read(root: Path, relative: Path) -> bytes:
        assert root == physical.resolve()
        if os.name == "nt":
            pointer.rmdir()
        else:
            pointer.unlink()
        _directory_link(pointer, outside)
        return original_read(root, relative)

    monkeypatch.setattr(runtime, "_read_deployment_no_follow", switch_then_read)
    try:
        assessed = runtime.assess_configured_runtime(pointer / deployment.name, qmx_root=pointer)
        assert is_ok(assessed), assessed
        assert assessed.value.stand_down
        assert not assessed.value.activation_authorized and not assessed.value.provider_ready
    finally:
        if os.name == "nt":
            pointer.rmdir()
        else:
            pointer.unlink()


@pytest.mark.skipif(os.name != "nt", reason="Windows namespace aliases")
@pytest.mark.parametrize("name", ["deployment.json:stream", "NUL", "con.txt", "file.", "file "])
def test_reader_rejects_windows_namespace_aliases(tmp_path: Path, name: str) -> None:
    with pytest.raises((OSError, ValueError)):
        runtime._read_deployment_no_follow(tmp_path, Path(name))


@pytest.mark.skipif(os.name != "nt", reason="Native Windows handle sharing")
def test_reader_blocks_concurrent_parent_leaf_replacement_and_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qmn.host import _windows_deployment as native

    parent = tmp_path / "nested"
    parent.mkdir()
    leaf = parent / "deployment.json"
    leaf.write_bytes(b"checked bytes")
    replacement = tmp_path / "replacement.json"
    replacement.write_bytes(b"hostile bytes")
    original_read = native._NativeReader.read
    attempted: list[OSError] = []
    # Establish that the user can perform every attack before acquiring handles.
    parent.rename(tmp_path / "moved")
    (tmp_path / "moved").rename(parent)
    replacement.replace(leaf)
    leaf.write_bytes(b"checked bytes")
    replacement.write_bytes(b"hostile bytes")

    def replace_paths() -> None:
        for action in (
            lambda: parent.rename(tmp_path / "moved"),
            lambda: replacement.replace(leaf),
            lambda: leaf.write_bytes(b"hostile bytes"),
        ):
            try:
                action()
            except OSError as exc:
                attempted.append(exc)
            else:
                pytest.fail("held native deployment handle allowed replacement or write")

    def read_with_attacker(self: native._NativeReader, handle: int, limit: int) -> bytes:
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(replace_paths).result(timeout=5)
        return original_read(self, handle, limit)

    monkeypatch.setattr(native._NativeReader, "read", read_with_attacker)
    assert (
        runtime._read_deployment_no_follow(tmp_path, Path("nested/deployment.json"))
        == b"checked bytes"
    )
    assert len(attempted) == 3
    assert all(isinstance(exc, PermissionError) for exc in attempted)
    # All handles close on success; the very same replacement then succeeds.
    replacement.replace(leaf)
    assert leaf.read_bytes() == b"hostile bytes"
    leaf.write_bytes(b"released")
    parent.rename(tmp_path / "moved")


@pytest.mark.skipif(os.name != "nt", reason="Native Windows handle errors")
def test_reader_read_errors_fail_closed_and_release_handles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qmn.host import _windows_deployment as native

    leaf = tmp_path / "deployment.json"
    leaf.write_bytes(b"checked bytes")
    original_read = native._NativeReader.read

    def failed_read(self: native._NativeReader, handle: int, limit: int) -> bytes:
        del self, handle, limit
        raise OSError("native read unavailable")

    monkeypatch.setattr(native._NativeReader, "read", failed_read)
    with pytest.raises(OSError, match="native read unavailable"):
        runtime._read_deployment_no_follow(tmp_path, Path(leaf.name))
    leaf.rename(tmp_path / "released.json")
    monkeypatch.setattr(native._NativeReader, "read", original_read)
    assert runtime._read_deployment_no_follow(tmp_path, Path("released.json")) == b"checked bytes"


@pytest.mark.skipif(os.name != "nt", reason="Native Windows query/read errors")
@pytest.mark.parametrize("failed_api", ["get_info_ex", "read_file"])
def test_reader_refuses_failed_native_apis_and_closes_directory_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failed_api: str
) -> None:
    import ctypes

    from qmn.host import _windows_deployment as native

    parent = tmp_path / "nested"
    parent.mkdir()
    (parent / "deployment.json").write_bytes(b"checked bytes")
    original_init = native._NativeReader.__init__

    def unavailable(*_args: object) -> int:
        ctypes.set_last_error(50)  # ERROR_NOT_SUPPORTED, never interpreted as success.
        return 0

    def inject(self: native._NativeReader) -> None:
        original_init(self)
        monkeypatch.setattr(self, failed_api, unavailable)

    monkeypatch.setattr(native._NativeReader, "__init__", inject)
    with pytest.raises(OSError) as raised:
        runtime._read_deployment_no_follow(tmp_path, Path("nested/deployment.json"))
    assert raised.value.winerror == 50
    parent.rename(tmp_path / "released")
