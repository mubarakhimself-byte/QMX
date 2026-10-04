"""Exercise mutation staging through its public CLI, without running mutants."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import tomllib

SCRIPT = Path(__file__).resolve().parents[1] / "stage_mutation_config.py"


def _component(tmp_path: Path) -> tuple[Path, Path]:
    component = tmp_path / "component"
    (component / "src" / "sample").mkdir(parents=True)
    (component / "tests").mkdir()
    (component / "examples").mkdir()
    (component / "src" / "sample" / "money.py").write_text("amount = 1\n")
    (component / "src" / "sample" / "sibling.py").write_text("label = 'kept'\n")
    manifest = component / "pyproject.toml"
    manifest.write_text('[project]\nname = "sample"\nversion = "0.1.0"\n', encoding="utf-8")
    declaration = tmp_path / "mutation.toml"
    declaration.write_text(
        '[tool.mutmut]\nsource_paths = ["src"]\n'
        'only_mutate = ["src/sample/money.py"]\n'
        'also_copy = ["examples"]\n'
        'pytest_add_cli_args_test_selection = ["tests"]\n'
        'pytest_add_cli_args = ["--deselect=tests/test_speed.py::test_speed"]\n'
        '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n',
        encoding="utf-8",
    )
    return manifest, declaration


def _stage(manifest: Path, declaration: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT), str(manifest), str(declaration)],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )


def test_staging_preserves_siblings_and_selects_only_declared_mutation_files(
    tmp_path: Path,
) -> None:
    manifest, declaration = _component(tmp_path)
    original = manifest.read_bytes()

    result = _stage(manifest, declaration)

    assert result.returncode == 0, result.stderr
    assert manifest.read_bytes().startswith(original)
    staged = tomllib.loads(manifest.read_text(encoding="utf-8"))
    assert staged["project"]["name"] == "sample"
    assert staged["tool"]["mutmut"] == {
        "paths_to_mutate": ["src"],
        "do_not_mutate": ["src/sample/sibling.py"],
        "also_copy": ["examples"],
    }
    assert staged["tool"]["pytest"]["ini_options"] == {
        "testpaths": ["tests"],
        "addopts": ["--deselect=tests/test_speed.py::test_speed"],
    }
    assert (manifest.parent / "src" / "sample" / "sibling.py").read_text() == "label = 'kept'\n"


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ('source_paths = ["src"]', 'source_paths = ["src"]\nunknown_option = true'),
        ('only_mutate = ["src/sample/money.py"]', 'only_mutate = ["src/sample/missing.py"]'),
        ('only_mutate = ["src/sample/money.py"]', 'only_mutate = ["../outside.py"]'),
        ('also_copy = ["examples"]', 'also_copy = ["../outside.py"]'),
        ('source_paths = ["src"]', 'source_paths = "src"'),
        ('only_mutate = ["src/sample/money.py"]', "only_mutate = []"),
        ('testpaths = ["tests"]', 'testpaths = ["tests"]\naddopts = "--ignore=tests"'),
        (
            'pytest_add_cli_args_test_selection = ["tests"]',
            'pytest_add_cli_args_test_selection = ["examples"]',
        ),
    ],
)
def test_invalid_scope_never_changes_the_component_manifest(
    tmp_path: Path, before: str, after: str
) -> None:
    manifest, declaration = _component(tmp_path)
    declaration.write_text(declaration.read_text(encoding="utf-8").replace(before, after))
    (tmp_path / "outside.py").write_text("amount = 99\n")
    original = manifest.read_bytes()

    result = _stage(manifest, declaration)

    assert result.returncode != 0
    assert "mutation staging: FAIL:" in result.stderr
    assert manifest.read_bytes() == original


@pytest.mark.parametrize("table", ["[tool.mutmut]\n", "[tool.pytest.ini_options]\n"])
def test_existing_tool_sections_are_refused_without_appending(tmp_path: Path, table: str) -> None:
    manifest, declaration = _component(tmp_path)
    with manifest.open("a", encoding="utf-8") as output:
        output.write(table)
    original = manifest.read_bytes()

    result = _stage(manifest, declaration)

    assert result.returncode != 0
    assert manifest.read_bytes() == original


def test_manifest_symlink_cannot_redirect_an_append(tmp_path: Path) -> None:
    manifest, declaration = _component(tmp_path)
    outside = tmp_path / "outside.toml"
    outside.write_bytes(manifest.read_bytes())
    manifest.unlink()
    try:
        manifest.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation unavailable on this host")
    original = outside.read_bytes()

    result = _stage(manifest, declaration)

    assert result.returncode != 0
    assert outside.read_bytes() == original


def test_translated_pytest_deselection_is_executed_by_pytest(tmp_path: Path) -> None:
    manifest, declaration = _component(tmp_path)
    (manifest.parent / "tests" / "test_speed.py").write_text(
        "def test_speed():\n    assert False\ndef test_correctness():\n    assert True\n"
    )
    assert _stage(manifest, declaration).returncode == 0

    result = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-c", str(manifest), "-q", "-p", "no:cacheprovider"],
        cwd=manifest.parent,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed, 1 deselected" in result.stdout
