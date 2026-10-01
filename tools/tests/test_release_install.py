"""Installer preflight controls; positive installation uses mocked venv/pip."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tarfile
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest

_INSTALL_PATH = Path(__file__).resolve().parents[2] / "release" / "install.py"
_SPEC = importlib.util.spec_from_file_location("qmx_release_installer", _INSTALL_PATH)
assert _SPEC is not None and _SPEC.loader is not None
installer = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(installer)

_DISTRIBUTIONS = (
    "qmf_core",
    "qmf_data",
    "qmf_registry",
    "qmf_indicators",
    "qmf_structure",
    "qmf_risk",
    "qmf_venue",
    "qmf_calendar_forex",
    "qml",
    "qmb",
    "qmn",
    "qma_core",
    "qma_wire",
    "qma_daemon",
)


def _wheel(name: str) -> bytes:
    output = BytesIO()
    stem = f"{name}-1.0.0.dist-info"
    with ZipFile(output, "w") as wheel:
        metadata = f"Metadata-Version: 2.1\nName: {name}\nVersion: 1.0.0\n\n"
        wheel.writestr(f"{stem}/METADATA", metadata)
        wheel_text = "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n\n"
        wheel.writestr(f"{stem}/WHEEL", wheel_text)
        wheel.writestr(f"{stem}/RECORD", "")
    return output.getvalue()


def _archive(entries: dict[str, bytes]) -> bytes:
    output = BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        for name, content in entries.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, BytesIO(content))
    return output.getvalue()


def _bundle(path: Path, *, unsafe_ui: bool = False) -> Path:
    path.mkdir()
    artifacts: dict[str, str] = {}
    for distribution in _DISTRIBUTIONS:
        filename = f"{distribution}-1.0.0-py3-none-any.whl"
        (path / filename).write_bytes(_wheel(distribution))
        artifacts[filename] = hashlib.sha256((path / filename).read_bytes()).hexdigest()
    lock = "example==1.0.0 \\\n" + "    --hash=sha256:" + "a" * 64 + "\n"
    (path / "requirements.lock").write_text(lock)
    (path / "launcher.py").write_text("pass\n")
    (path / "install.py").write_text("pass\n")
    packs = {"qma/packs/default.json": "b" * 64}
    (path / "pack-resources.json").write_text(json.dumps(packs))
    ui = _archive(
        {"../escape.txt": b"bad", "index.html": b"<html></html>"}
        if unsafe_ui
        else {"index.html": b"<html></html>", "assets/app.js": b"ok"}
    )
    (path / "ui.tar.gz").write_bytes(ui)
    (path / "README.md").write_text("Candidate install instructions\n")
    (path / "source-manifest.json").write_text(json.dumps({"backend": "a" * 40}))
    node = _archive(
        {
            "install.py": b"pass\n",
            "safe_io.py": b"pass\n",
            "systemd/templates/qmn.service.in": b"[Service]\n",
            "justfile-recipes/node.just": b"# fixture\n",
        }
    )
    (path / "qmn-deploy.tar.gz").write_bytes(node)
    required = (
        "requirements.lock",
        "launcher.py",
        "install.py",
        "pack-resources.json",
        "ui.tar.gz",
        "qmn-deploy.tar.gz",
        "README.md",
        "source-manifest.json",
    )
    for name in required:
        artifacts[name] = hashlib.sha256((path / name).read_bytes()).hexdigest()
    record = {"candidate": "a" * 40, "artifacts": artifacts, "checks": {}}
    (path / "acceptance.json").write_text(json.dumps(record))
    return path


def _mock_environment(
    monkeypatch: pytest.MonkeyPatch, *, wheel_hashes: dict[str, str] | None = None
) -> tuple[list[list[str]], list[Path]]:
    monkeypatch.setattr(installer.sys, "version_info", (3, 14))
    calls: list[list[str]] = []
    environments: list[Path] = []

    class FakeBuilder:
        def __init__(self, *, with_pip: bool) -> None:
            assert with_pip is True

        def create(self, destination: Path) -> None:
            environments.append(destination)
            (destination / "bin").mkdir(parents=True)
            (destination / "bin" / "python").touch()

    def fake_run(command: list[str], *, check: bool) -> None:
        assert check is True
        calls.append(command)
        if wheel_hashes is not None and "--no-deps" in command:
            for name in command[command.index("--no-deps") + 1 :]:
                path = Path(name)
                wheel_hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()

    monkeypatch.setattr(installer.venv, "EnvBuilder", FakeBuilder)
    monkeypatch.setattr(installer.subprocess, "run", fake_run)
    return calls, environments


def test_preflight_rejects_missing_required_wheel_before_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _bundle(tmp_path / "bundle")
    manifest = json.loads((bundle / "acceptance.json").read_text())
    removed = next(name for name in manifest["artifacts"] if name.startswith("qmb-"))
    del manifest["artifacts"][removed]
    (bundle / "acceptance.json").write_text(json.dumps(manifest))
    calls, environments = _mock_environment(monkeypatch)
    destination = tmp_path / "install"

    with pytest.raises(RuntimeError, match="Required product wheel"):
        installer.install(bundle, destination)

    assert not destination.exists()
    assert not calls
    assert not environments


def test_preflight_rejects_malformed_inventory_and_tampering_before_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _bundle(tmp_path / "bundle")
    manifest = json.loads((bundle / "acceptance.json").read_text())
    manifest["artifacts"]["qmb-1.0.0-py3-none-any.whl"] = "bad"
    (bundle / "acceptance.json").write_text(json.dumps(manifest))
    calls, environments = _mock_environment(monkeypatch)
    with pytest.raises(RuntimeError, match="checksum is malformed"):
        installer.install(bundle, tmp_path / "malformed")
    assert not calls and not environments

    bundle = _bundle(tmp_path / "tampered")
    wheel = bundle / "qmb-1.0.0-py3-none-any.whl"
    wheel.write_bytes(wheel.read_bytes() + b"tamper")
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        installer.install(bundle, tmp_path / "tampered-install")
    assert not calls and not environments


def test_preflight_requires_every_consumed_artifact_to_be_in_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _bundle(tmp_path / "bundle")
    manifest = json.loads((bundle / "acceptance.json").read_text())
    del manifest["artifacts"]["launcher.py"]
    (bundle / "acceptance.json").write_text(json.dumps(manifest))
    calls, environments = _mock_environment(monkeypatch)

    with pytest.raises(RuntimeError, match="Required product artifact is missing"):
        installer.install(bundle, tmp_path / "install")

    assert not calls and not environments


def test_preflight_rejects_wheel_metadata_mismatch_before_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _bundle(tmp_path / "bundle")
    wheel_path = bundle / "qmb-1.0.0-py3-none-any.whl"
    wheel_path.write_bytes(_wheel("different-name"))
    manifest = json.loads((bundle / "acceptance.json").read_text())
    manifest["artifacts"][wheel_path.name] = hashlib.sha256(wheel_path.read_bytes()).hexdigest()
    (bundle / "acceptance.json").write_text(json.dumps(manifest))
    calls, environments = _mock_environment(monkeypatch)

    with pytest.raises(RuntimeError, match="filename and METADATA disagree"):
        installer.install(bundle, tmp_path / "install")

    assert not calls and not environments


def test_lock_preflight_accepts_uv_multihash_continuation_format(tmp_path: Path) -> None:
    lock = tmp_path / "requirements.lock"
    first_hash = "a" * 64
    second_hash = "b" * 64
    third_hash = "c" * 64
    lock.write_text(
        f"alpha==1.2.3 \\\n    --hash=sha256:{first_hash} \\\n    --hash=sha256:{second_hash}\n"
        "    # via generated-export\n"
        f"beta==4.5.6 \\\n    --hash=sha256:{third_hash}\n"
    )
    installer._validate_lock(lock)


def test_preflight_rejects_unhashed_lock_before_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _bundle(tmp_path / "bundle")
    lock_path = bundle / "requirements.lock"
    lock_path.write_text("example==1.0.0\n")
    manifest = json.loads((bundle / "acceptance.json").read_text())
    manifest["artifacts"][lock_path.name] = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    (bundle / "acceptance.json").write_text(json.dumps(manifest))
    calls, environments = _mock_environment(monkeypatch)

    with pytest.raises(RuntimeError, match="at least one SHA256"):
        installer.install(bundle, tmp_path / "install")

    assert not calls and not environments


def test_preflight_rejects_unsafe_archive_before_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _bundle(tmp_path / "bundle", unsafe_ui=True)
    calls, environments = _mock_environment(monkeypatch)
    destination = tmp_path / "install"

    with pytest.raises(RuntimeError, match="unsafe path"):
        installer.install(bundle, destination)

    assert not destination.exists()
    assert not calls and not environments
    assert not (tmp_path / "escape.txt").exists()


def test_positive_install_flow_is_mocked_and_uses_only_bound_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _bundle(tmp_path / "bundle")
    extra = bundle / "unlisted-9.9.9-py3-none-any.whl"
    extra.write_bytes(_wheel("unlisted"))
    wheel_hashes: dict[str, str] = {}
    calls, environments = _mock_environment(monkeypatch, wheel_hashes=wheel_hashes)

    with pytest.raises(RuntimeError, match="Unlisted product wheel"):
        installer.install(bundle, tmp_path / "refused")
    assert not environments

    extra.unlink()
    destination = tmp_path / "install"
    installer.install(bundle, destination)

    assert len(environments) == 1
    assert len(calls) == 3
    assert "--require-hashes" in calls[0]
    pip_wheels = set(calls[1][5:])
    expected_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in bundle.glob("*.whl")
    }
    assert {Path(name).name for name in pip_wheels} == set(expected_hashes)
    assert wheel_hashes == expected_hashes
    assert all(Path(name).parent != bundle for name in pip_wheels)
    assert (destination / "ui" / "index.html").read_bytes() == b"<html></html>"
    assert (destination / "launcher.py").is_file()
    assert (destination / "installed-artifacts.json").is_file()


@pytest.mark.parametrize("unsafe_name", ["../escape.py", "/escape.py", "C:/escape.py"])
def test_node_archive_unsafe_paths_refuse_before_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, unsafe_name: str
) -> None:
    bundle = _bundle(tmp_path / "bundle")
    node = bundle / "qmn-deploy.tar.gz"
    node.write_bytes(_archive({unsafe_name: b"bad"}))
    record = json.loads((bundle / "acceptance.json").read_text())
    record["artifacts"][node.name] = hashlib.sha256(node.read_bytes()).hexdigest()
    (bundle / "acceptance.json").write_text(json.dumps(record))
    _, environments = _mock_environment(monkeypatch)
    with pytest.raises(RuntimeError, match="unsafe path"):
        installer.install(bundle, tmp_path / "installed")
    assert environments == []
    assert not (tmp_path / "installed").exists()


def test_node_assets_and_template_interpreter_alias_are_installed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _bundle(tmp_path / "bundle")
    _mock_environment(monkeypatch)
    destination = tmp_path / "installed"
    installer.install(bundle, destination)
    assert (destination / "qmn/deploy/systemd/templates/qmn.service.in").is_file()
    assert (destination / "README.md").is_file()
    assert json.loads((destination / "source-manifest.json").read_text())["backend"] == "a" * 40
    if installer.os.name != "nt":
        assert (destination / ".venv").is_symlink()
        assert (destination / ".venv").resolve() == (destination / "venv").resolve()


def test_node_archive_missing_mandatory_template_refuses_before_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _bundle(tmp_path / "bundle")
    node = bundle / "qmn-deploy.tar.gz"
    node.write_bytes(_archive({"install.py": b"pass\n", "safe_io.py": b"pass\n"}))
    record = json.loads((bundle / "acceptance.json").read_text())
    record["artifacts"][node.name] = hashlib.sha256(node.read_bytes()).hexdigest()
    (bundle / "acceptance.json").write_text(json.dumps(record))
    _, environments = _mock_environment(monkeypatch)
    with pytest.raises(RuntimeError, match="no required file"):
        installer.install(bundle, tmp_path / "installed")
    assert environments == []
    assert not (tmp_path / "installed").exists()


def test_bundle_replacement_after_preflight_cannot_change_installed_assets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _bundle(tmp_path / "bundle")
    _mock_environment(monkeypatch)
    original_create = installer.venv.EnvBuilder.create

    def replace_bundle_during_create(builder: object, destination: Path) -> None:
        (bundle / "qmn-deploy.tar.gz").write_bytes(_archive({"replacement.py": b"bad"}))
        (bundle / "launcher.py").write_text("replacement launcher\n")
        (bundle / "README.md").write_text("replacement readme\n")
        original_create(builder, destination)

    monkeypatch.setattr(installer.venv.EnvBuilder, "create", replace_bundle_during_create)
    destination = tmp_path / "installed"
    installer.install(bundle, destination)
    assert (destination / "qmn/deploy/install.py").is_file()
    assert not (destination / "qmn/deploy/replacement.py").exists()
    assert (destination / "launcher.py").read_text() == "pass\n"
    assert (destination / "README.md").read_text() == "Candidate install instructions\n"


def test_bundle_replacement_before_snapshot_refuses_before_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _bundle(tmp_path / "bundle")
    _, environments = _mock_environment(monkeypatch)
    original_manifest = installer._manifest

    def replace_after_manifest(path: Path):
        record = original_manifest(path)
        if path == bundle:
            (bundle / "launcher.py").write_text("replacement launcher\n")
        return record

    monkeypatch.setattr(installer, "_manifest", replace_after_manifest)
    with pytest.raises(RuntimeError, match="changed after preflight"):
        installer.install(bundle, tmp_path / "installed")
    assert environments == []
    assert not (tmp_path / "installed").exists()
