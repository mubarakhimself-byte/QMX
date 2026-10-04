"""DevOps wrappers for pure QMN config authoring and boot preflight.

The 71-row config artifact and the strict boot deployment document are
different inputs. This process only selects contained paths and starts the
existing pure config or host-preflight module as a child; it imports neither
the composition root nor a venue/provider adapter.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

__all__ = ["DEFAULT_CONFIG_NAME", "DEFAULT_DEPLOYMENT_NAME", "main"]

DEFAULT_CONFIG_NAME: Final[str] = "node-config.json"
DEFAULT_DEPLOYMENT_NAME: Final[str] = "qmn-deployment.json"
_CONFIG_MODULE: Final[str] = "qmn.config.cli"
_HOST_CHECK_MODULE: Final[str] = "qmn.host.configured_runtime"


def _safe_relative(root: Path, value: str | None, default_name: str, *, must_exist: bool) -> Path:
    supplied = Path(value) if value else Path(default_name)
    if supplied.is_absolute() or any(part in {"", ".", ".."} for part in supplied.parts):
        raise ValueError("path must be a normalized path relative to QMX_ROOT")
    current = root
    for part in supplied.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("path must not traverse symlinks")
    if must_exist:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root)
        if not resolved.is_file():
            raise ValueError("path must name a regular file")
        return resolved
    current.resolve(strict=False).relative_to(root)
    return current


def _run(module: str, argv: list[str]) -> int:
    safe_environment = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "TZ": "UTC",
        "PYTHONNOUSERSITE": "1",
    }
    if os.name == "nt":
        # Windows DLL/side-by-side resolution requires the OS system directory.
        # Preserve this single OS input; credential and Python-path variables
        # remain excluded from the deployment child's allow-list.
        system_root = os.environ.get("SYSTEMROOT")
        if not system_root:
            print("refused: Windows deployment child requires SYSTEMROOT", file=sys.stderr)
            return 2
        safe_environment["SYSTEMROOT"] = system_root
    completed = subprocess.run(
        [sys.executable, "-m", module, *argv],
        check=False,
        capture_output=True,
        text=True,
        env=safe_environment,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return completed.returncode


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("init", "validate", "explain", "validate-deployment"))
    parser.add_argument("--root", help="operator-selected QMX_ROOT (defaults to QMX_ROOT or cwd)")
    parser.add_argument("--path", help="normalized path relative to QMX_ROOT")
    args = parser.parse_args(argv)
    try:
        root = Path(args.root or os.environ.get("QMX_ROOT", ".")).resolve(strict=True)
        if args.action == "validate-deployment":
            target = _safe_relative(root, args.path, DEFAULT_DEPLOYMENT_NAME, must_exist=True)
            child_module = _HOST_CHECK_MODULE
            child_args = ["--deployment", str(target), "--qmx-root", str(root)]
        else:
            target = _safe_relative(
                root,
                args.path,
                DEFAULT_CONFIG_NAME,
                must_exist=args.action != "init",
            )
            child_module = _CONFIG_MODULE
            child_args = [args.action, "--root", str(root), "--path", str(target.relative_to(root))]
    except (OSError, ValueError) as exc:
        print(
            f"refused: selected config path is unavailable or unsafe ({type(exc).__name__})",
            file=sys.stderr,
        )
        return 2
    return _run(child_module, child_args)


if __name__ == "__main__":
    raise SystemExit(main())
