"""Execute nightly workflow shell steps against a controlled external CLI.

The results option declaration follows pinned mutmut 3.3.0's official source:
https://github.com/boxed/mutmut/blob/3.3.0/mutmut/__main__.py#L987-L1000
This exercises CLI compatibility and failure propagation, not mutation execution.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
MODULES = {
    "mutation": ("qmf.core.exact", "qmf.core.chrono"),
    "mutation-qmn": (
        "qmn.order.door",
        "qmn.order.path",
        "qmn.ledger.binding_ledger",
        "qmn.reconcile.residuals",
        "qmn.capital.kill_line",
        "qmn.ledger.virtual",
    ),
}

CLI = """import os, sys
import click
arguments = sys.argv[sys.argv.index("mutmut") + 1:]
if arguments[0] == "run":
    print("1/100 progress; later work may fail")
    raise SystemExit(int(os.environ["RUN_EXIT"]))
@click.command()
@click.option("--all", default=False)
def results(all):
    for row in os.environ["RESULT_ROWS"].splitlines():
        if all or not row.endswith(": killed"):
            click.echo(row)
results(arguments[1:])
"""


@pytest.mark.parametrize("job", ["mutation", "mutation-qmn"])
@pytest.mark.parametrize("scenario", ["complete", "crashed", "incomplete", "survivor"])
def test_nightly_shell_cli_and_verdict(tmp_path: Path, job: str, scenario: str) -> None:
    bash = shutil.which("bash")
    if os.name == "nt":
        git = shutil.which("git")
        git_bash = Path(git).parent.parent / "bin" / "bash.exe" if git else None
        bash = str(git_bash) if git_bash and git_bash.is_file() else None
    if bash is None:
        pytest.skip("nightly Linux shell is unavailable on this host")
    document = yaml.safe_load(
        (ROOT / ".github/workflows/battery.yml").read_text(encoding="utf-8")
    )
    steps = cast("list[dict[str, str]]", document["jobs"][job]["steps"])
    commands = [
        step["run"]
        for step in steps
        if "run" in step
        and any(
            marker in step["run"]
            for marker in ("mutmut run >", "mutmut results ", "mutation_gate.py")
        )
    ]
    cli = tmp_path / "external_uv.py"
    cli.write_text(CLI, encoding="utf-8")
    executable = shlex.quote(Path(sys.executable).as_posix())
    script = (
        f'uv() {{ {executable} {shlex.quote(cli.as_posix())} "$@"; }}\n'
        f'python() {{ {executable} "$@"; }}\n' + "\n".join(commands)
    )
    statuses = ["killed"] * len(MODULES[job])
    if scenario == "incomplete":
        statuses[-1] = "not checked"
    elif scenario == "survivor":
        statuses[-1] = "survived"
    rows = "\n".join(
        f"{module}.x_value__mutmut_1: {status}"
        for module, status in zip(MODULES[job], statuses, strict=True)
    )
    result = subprocess.run(
        [bash, "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", script],
        cwd=tmp_path,
        env=dict(
            os.environ,
            GITHUB_WORKSPACE=ROOT.as_posix(),
            RESULT_ROWS=rows,
            RUN_EXIT="2" if scenario == "crashed" else "0",
        ),
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=30,
    )
    expected = (
        2
        if scenario in {"crashed", "incomplete"}
        else (1 if scenario == "survivor" and job == "mutation" else 0)
    )
    assert result.returncode == expected, result.stdout + result.stderr
