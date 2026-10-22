"""Runtime closure selection, reproducibility and offline preflight contracts."""

from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import subprocess
import tarfile
from collections.abc import Mapping
from io import BytesIO
from pathlib import Path
from typing import cast
from zipfile import ZipFile

import pytest

_RUNTIME_PATH = Path(__file__).resolve().parents[2] / "release" / "runtime_wheels.py"
_RUNTIME_SPEC = importlib.util.spec_from_file_location("qmx_test_runtime_wheels", _RUNTIME_PATH)
assert _RUNTIME_SPEC is not None and _RUNTIME_SPEC.loader is not None
runtime_wheels = importlib.util.module_from_spec(_RUNTIME_SPEC)
_RUNTIME_SPEC.loader.exec_module(runtime_wheels)

_PRODUCT_DISTRIBUTIONS = (
    "qmf_core", "qmf_data", "qmf_registry", "qmf_indicators", "qmf_structure",
    "qmf_risk", "qmf_venue", "qmf_calendar_forex", "qml", "qmb", "qmn",
)


def _fixture_product_wheel(name: str) -> bytes:
    output = BytesIO()
    stem = f"{name}-1.0.0.dist-info"
    with ZipFile(output, "w") as wheel:
        wheel.writestr(
            f"{stem}/METADATA",
            f"Metadata-Version: 2.1\nName: {name}\nVersion: 1.0.0\n\n",
        )
        wheel.writestr(
            f"{stem}/WHEEL",
            "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n\n",
        )
        wheel.writestr(f"{stem}/RECORD", "")
    return output.getvalue()


def _fixture_archive(entries: Mapping[str, bytes]) -> bytes:
    output = BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        for name, content in entries.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, BytesIO(content))
    return output.getvalue()

_ROOT = Path(__file__).resolve().parents[2]
_BUILD_PATH = _ROOT / "tools" / "build_release.py"
_BUILD_SPEC = importlib.util.spec_from_file_location("qmx_build_release", _BUILD_PATH)
assert _BUILD_SPEC is not None and _BUILD_SPEC.loader is not None
builder = importlib.util.module_from_spec(_BUILD_SPEC)
_BUILD_SPEC.loader.exec_module(builder)

_INSTALL_PATH = _ROOT / "release" / "install.py"
_INSTALL_SPEC = importlib.util.spec_from_file_location("qmx_runtime_installer", _INSTALL_PATH)
assert _INSTALL_SPEC is not None and _INSTALL_SPEC.loader is not None
installer = importlib.util.module_from_spec(_INSTALL_SPEC)
_INSTALL_SPEC.loader.exec_module(installer)


def _wheel(
    name: str,
    version: str,
    tag: str = "py3-none-any",
    *,
    declared_tags: tuple[str, ...] | None = None,
) -> bytes:
    output = BytesIO()
    dist_info = f"{name.replace('-', '_')}-{version}.dist-info"
    fields = tag.split("-")
    expanded_tags = tuple(
        "-".join(parts) for parts in itertools.product(*(field.split(".") for field in fields))
    )
    wheel_tags = declared_tags if declared_tags is not None else expanded_tags
    tag_headers = "".join(f"Tag: {value}\n" for value in wheel_tags)
    with ZipFile(output, "w") as wheel:
        wheel.writestr(
            f"{dist_info}/METADATA",
            f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n\n",
        )
        wheel.writestr(
            f"{dist_info}/WHEEL",
            f"Wheel-Version: 1.0\nRoot-Is-Purelib: true\n{tag_headers}\n",
        )
        wheel.writestr(f"{dist_info}/RECORD", "")
    return output.getvalue()


def _lock(name: str, version: str, data: bytes, marker: str | None = None) -> str:
    suffix = f" ; {marker}" if marker else ""
    return (
        f"{name}=={version}{suffix} \\\n"
        f"    --hash=sha256:{hashlib.sha256(data).hexdigest()}\n"
    )


def _runtime_bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    _wheelhouse = tmp_path / "wheelhouse"
    _wheelhouse.mkdir()
    demo = _wheel("demo-runtime", "1.2.3")
    (_wheelhouse / "demo_runtime-1.2.3-py3-none-any.whl").write_bytes(demo)
    lock = _lock("demo-runtime", "1.2.3", demo)
    (bundle / "requirements.lock").write_text(lock)
    builder._runtime_closure(bundle, _wheelhouse, lock, "")
    helper_path = _ROOT / "release" / "runtime_wheels.py"
    (bundle / "runtime_wheels.py").write_bytes(helper_path.read_bytes())
    return bundle


def test_marker_evaluation_selects_exact_linux_active_packages() -> None:
    lock = (
        "alpha==1.0.0 ; sys_platform == 'linux' \\\n"
        f"    --hash=sha256:{'a' * 64}\n"
        "windows-only==2.0.0 ; sys_platform == 'win32' \\\n"
        f"    --hash=sha256:{'b' * 64}\n"
    )
    parsed = runtime_wheels.parse_locked_requirements(
        (lock,), environment=runtime_wheels.marker_environment(target=True)
    )
    assert set(parsed) == {"alpha"}
    assert parsed["alpha"]["version"] == "1.0.0"


def test_builder_selects_hash_locked_target_wheel_and_is_reproducible(
    tmp_path: Path,
) -> None:
    bundle_a = tmp_path / "a"
    bundle_b = tmp_path / "b"
    bundle_a.mkdir()
    bundle_b.mkdir()
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    py2_alias = _wheel("demo-runtime", "1.2.3", "py2-none-any")
    py3_wheel = _wheel("demo-runtime", "1.2.3", "py3-none-any")
    (wheelhouse / "demo_runtime-1.2.3-py2-none-any.whl").write_bytes(py2_alias)
    (wheelhouse / "demo_runtime-1.2.3-py3-none-any.whl").write_bytes(py3_wheel)
    lock = _lock("demo-runtime", "1.2.3", py3_wheel)

    builder._runtime_closure(bundle_a, wheelhouse, lock, "")
    builder._runtime_closure(bundle_b, wheelhouse, lock, "")

    assert (bundle_a / "runtime-wheels.tar.gz").read_bytes() == (
        bundle_b / "runtime-wheels.tar.gz"
    ).read_bytes()
    inventory = json.loads((bundle_a / "runtime-wheelhouse.json").read_text())
    assert [wheel["filename"] for wheel in inventory["wheels"]] == [
        "demo_runtime-1.2.3-py3-none-any.whl"
    ]
    assert inventory["target"]["platform"] == "linux"


def test_builder_rejects_missing_or_foreign_locked_wheel(tmp_path: Path) -> None:
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    data = _wheel("demo-runtime", "1.2.3")
    (wheelhouse / "demo_runtime-1.2.3-py3-none-any.whl").write_bytes(data)
    destination = tmp_path / "out"
    destination.mkdir()
    wrong_lock = _lock("demo-runtime", "1.2.3", b"different")

    with pytest.raises(RuntimeError, match="Expected one hash-locked"):
        builder._runtime_closure(destination, wheelhouse, wrong_lock, "")


def test_builder_rejects_linux_tag_without_declared_glibc_floor(tmp_path: Path) -> None:
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    data = _wheel("demo-runtime", "1.2.3", "cp314-cp314-linux_x86_64")
    (wheelhouse / "demo_runtime-1.2.3-cp314-cp314-linux_x86_64.whl").write_bytes(data)
    destination = tmp_path / "out"
    destination.mkdir()

    with pytest.raises(RuntimeError, match="Expected one hash-locked"):
        builder._runtime_closure(destination, wheelhouse, _lock("demo-runtime", "1.2.3", data), "")


def test_compressed_wheel_tags_match_packaging_parser_and_minimum_glibc(
    tmp_path: Path,
) -> None:
    from packaging.utils import parse_wheel_filename

    compressed = "cp314-cp314-manylinux_2_34_x86_64.manylinux_2_17_x86_64"
    content = _wheel("demo-runtime", "1.2.3", compressed)
    filename = "demo_runtime-1.2.3-" + compressed + ".whl"
    fixture = tmp_path / filename
    fixture.write_bytes(content)
    metadata = runtime_wheels.wheel_metadata(fixture)
    _, _, _, parsed_tags = parse_wheel_filename(filename)

    tags = cast(list[str], metadata["tags"])
    floors = [runtime_wheels.tag_glibc_floor(tag) for tag in tags]
    assert set(tags) == {str(tag) for tag in parsed_tags}
    assert min(floor for floor in floors if floor is not None) == (2, 17)


def test_compressed_wheel_requires_every_filename_tag_in_wheel_metadata(
    tmp_path: Path,
) -> None:
    compressed = "cp314-cp314-manylinux_2_34_x86_64.manylinux_2_17_x86_64"
    content = _wheel(
        "demo-runtime",
        "1.2.3",
        compressed,
        declared_tags=("cp314-cp314-manylinux_2_34_x86_64",),
    )
    fixture = tmp_path / f"demo_runtime-1.2.3-{compressed}.whl"
    fixture.write_bytes(content)

    with pytest.raises(ValueError, match="filename and WHEEL tags disagree"):
        runtime_wheels.wheel_metadata(fixture)


@pytest.mark.parametrize("duplicate_kind", ["filename", "distribution"])
def test_runtime_inventory_rejects_duplicate_filename_and_distribution(
    tmp_path: Path, duplicate_kind: str
) -> None:
    bundle = _runtime_bundle(tmp_path)
    lock_text = (bundle / "requirements.lock").read_text()
    inventory = json.loads((bundle / "runtime-wheelhouse.json").read_text())
    duplicate = dict(inventory["wheels"][0])
    if duplicate_kind == "distribution":
        duplicate["filename"] = "renamed-but-duplicate-distribution.whl"
    inventory["wheels"].append(duplicate)

    with pytest.raises(ValueError, match="duplicate runtime wheel"):
        runtime_wheels.validate_inventory_requirements(
            inventory=inventory, lock_text=lock_text, glibc=(2, 39)
        )


def test_installer_offline_preflight_and_pip_are_isolated_and_hash_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _runtime_bundle(tmp_path)
    # Add the normal product bundle fixture around the verified runtime files.
    for distribution in _PRODUCT_DISTRIBUTIONS:
        filename = f"{distribution}-1.0.0-py3-none-any.whl"
        (bundle / filename).write_bytes(_fixture_product_wheel(distribution))
    (bundle / "launcher.py").write_text("pass\n")
    (bundle / "install.py").write_text("pass\n")
    (bundle / "README.md").write_text("test\n")
    (bundle / "source-manifest.json").write_text(json.dumps({"backend": "a" * 40}))
    (bundle / "ui.tar.gz").write_bytes(_fixture_archive({"index.html": b"ok"}))
    (bundle / "qmn-deploy.tar.gz").write_bytes(
        _fixture_archive(
            {
                "install.py": b"pass\n",
                "safe_io.py": b"pass\n",
                "systemd/templates/qmn.service.in": b"[Service]\n",
                "justfile-recipes/node.just": b"# test\n",
            }
        )
    )
    artifacts = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in bundle.iterdir()
        if path.is_file()
    }
    (bundle / "acceptance.json").write_text(
        json.dumps({"candidate": "a" * 40, "artifacts": artifacts, "checks": {}})
    )
    manifest = json.loads((bundle / "acceptance.json").read_text())
    assert manifest["artifacts"]["runtime-wheels.tar.gz"]

    helper = installer._runtime_helper()
    def supported_target(
        *, target: Mapping[str, object], running: bool
    ) -> tuple[int, int]:
        assert target["platform"] == "linux"
        assert running
        return 2, 39

    monkeypatch.setattr(helper, "validate_runtime_target", supported_target)
    monkeypatch.setattr(installer, "_runtime_helper", lambda: helper)
    monkeypatch.setattr(installer.sys, "version_info", (3, 14))
    calls: list[list[str]] = []

    class FakeBuilder:
        def __init__(self, *, with_pip: bool) -> None:
            assert with_pip

        def create(self, destination: Path) -> None:
            (destination / "bin").mkdir(parents=True)
            (destination / "bin" / "python").touch()

    monkeypatch.setattr(installer.venv, "EnvBuilder", FakeBuilder)
    def fake_run(command: list[str], *, check: bool) -> subprocess.CompletedProcess[object]:
        assert check
        calls.append(command)
        return subprocess.CompletedProcess(args=command, returncode=0)

    monkeypatch.setattr(installer.subprocess, "run", fake_run)

    installer.install(bundle, tmp_path / "installed")

    assert calls[0][3:5] == ["--isolated", "install"]
    assert "--require-hashes" in calls[0]
    assert "--no-index" in calls[0]
    assert "--find-links" in calls[0]
    assert calls[1][3:5] == ["--isolated", "install"]
    assert calls[2][3:5] == ["--isolated", "check"]


def test_runtime_inventory_rejects_lock_hash_or_archive_mismatch_before_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _runtime_bundle(tmp_path)
    inventory_path = bundle / "runtime-wheelhouse.json"
    inventory = json.loads(inventory_path.read_text())
    inventory["wheels"][0]["sha256"] = "0" * 64
    inventory_path.write_text(json.dumps(inventory))
    helper = installer._runtime_helper()
    def supported_target(
        *, target: Mapping[str, object], running: bool
    ) -> tuple[int, int]:
        assert target["platform"] == "linux"
        assert running
        return 2, 39

    monkeypatch.setattr(helper, "validate_runtime_target", supported_target)
    monkeypatch.setattr(installer, "_runtime_helper", lambda: helper)

    with pytest.raises(RuntimeError, match="SHA256 is not allowed"):
        installer._validate_runtime_closure(bundle, {
            "runtime-wheels.tar.gz": "0" * 64,
            "runtime-wheelhouse.json": "0" * 64,
        })
