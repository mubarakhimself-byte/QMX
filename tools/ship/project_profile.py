"""The project profile: `<factory_home>/projects/<project>/project.toml` (FACTORY-DESIGN 11.1), read by the kit.

`load(index, settings)` returns the file's tables over the built-in defaults, so a program whose project has
no profile yet still runs: `project.shared_generated` is `uv.lock` and `**/uv.lock`, `pool.workers` is the
`seats` setting, and there are no `generators`. `[generators]` maps a shared-generated pattern to the argv
that rebuilds it at merge time, run from the repo root.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from ship.settings import Settings


def home(settings: Settings) -> Path:
    from ship.launch import factory_home

    return factory_home(settings)


def path_of(project: str, settings: Settings) -> Path:
    return home(settings) / "projects" / project / "project.toml"


def defaults(project: str, settings: Settings) -> dict:
    return {"project": {"name": project, "shared_generated": ["uv.lock", "**/uv.lock"],
                        "target_branch": settings.ci_gate_base},
            "pool": {"workers": settings.seats},
            "generators": {}}


def load(index, settings: Settings) -> dict:
    """The profile of `index.project` (an Index, or None for "qmx")."""
    project = (getattr(index, "project", None) or "qmx") if index is not None else "qmx"
    out = defaults(project, settings)
    path = path_of(project, settings)
    if not path.exists():
        return out
    raw = tomllib.loads(path.read_text("utf-8"))
    for key, value in raw.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = {**out[key], **value}
        else:
            out[key] = value
    return out


def of_program(program_dir: Path, settings: Settings) -> dict:
    """The profile of the program in `program_dir` (its PROGRAM.yaml `project`, else qmx)."""
    from ship import program as prog
    from ship.layout import Program

    program = Program(program_dir)
    index = None
    if program.project_file.exists():
        try:
            index = prog.load(program)
        except prog.ProgramError:
            index = None
    return load(index, settings)


def target_branch(program_dir: Path, settings: Settings) -> str:
    """The branch a program merges into: the profile's `target_branch`, else the `ci_gate_base` setting.
    The one place the kit reads it (D-L22)."""
    return str(of_program(program_dir, settings)["project"].get("target_branch") or settings.ci_gate_base)
