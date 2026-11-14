"""The project profile: `<factory_home>/projects/<project>/project.toml` (FACTORY-DESIGN 11.1), read by the kit.

`load(index, settings)` returns the file's tables over the built-in defaults, so a program whose project has
no profile yet still runs: `project.shared_generated` is `uv.lock` and `**/uv.lock`, `pool.workers` is the
`seats` setting, and `[generators]` holds the two the one ratchet needs (FACTORY-DESIGN 5).

`[generators]` maps a shared-generated pattern to what rebuilds it at merge time (`ship merge`, after a moved
target is merged in, under the project's merge lock): one argv, or a list of argv run in order, from the repo
root through the timed wrapper. Each run that changes files matching its pattern is one commit (`ratchet: prune
<n> rows` under `ci/baselines/`, else `contract: regenerate <pattern>`). A generator whose `.py` script is not
in the repo is skipped. The defaults, which a profile's own `[generators]` table adds to or replaces key by key:

```toml
[generators]
"ci/baselines/*" = ["python", "tools/ci/qci.py", "ratchet", "--prune"]  # drop the rows fixed code left behind
"contracts/*.json" = [["uv", "sync", "--frozen", "--project", "qmx-agents"],
                      ["uv", "run", "--frozen", "python", "tools/contract_dump.py"]]  # the contract dump
```

`python` here is the interpreter running the kit.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

from ship.settings import Settings


def home(settings: Settings) -> Path:
    from ship.launch import factory_home

    return factory_home(settings)


def path_of(project: str, settings: Settings) -> Path:
    return home(settings) / "projects" / project / "project.toml"


def default_generators() -> dict[str, list]:
    """The baselines prune and the contract dump, run at merge (the module's docstring)."""
    return {"ci/baselines/*": [sys.executable, "tools/ci/qci.py", "ratchet", "--prune"],
            "contracts/*.json": [["uv", "sync", "--frozen", "--project", "qmx-agents"],
                                 ["uv", "run", "--frozen", "python", "tools/contract_dump.py"]]}


def generator_commands(value) -> list[list[str]]:
    """A `[generators]` value as a list of argv: one argv, or a list of them. `python` is the kit's own."""
    runs = value if value and isinstance(value[0], (list, tuple)) else [value]
    return [[sys.executable if (i == 0 and a == "python") else str(a) for i, a in enumerate(argv)]
            for argv in runs if argv]


def defaults(project: str, settings: Settings) -> dict:
    return {"project": {"name": project, "shared_generated": ["uv.lock", "**/uv.lock"],
                        "target_branch": settings.ci_gate_base},
            "pool": {"workers": settings.seats},
            "generators": default_generators()}


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


def project_values(profile: dict) -> dict[str, str]:
    """`PROJECT.<key>` for every key of the profile's [project] table: the prompt values a worker gets."""
    return {f"PROJECT.{k}": str(v) for k, v in (profile.get("project") or {}).items()}


def rules_file(profile: dict, settings: Settings) -> str:
    """The project's PROJECT-RULES.md: the profile's `rules`, else the factory home's copy."""
    project = profile.get("project") or {}
    return str(project.get("rules") or home(settings) / "projects" / str(project.get("name") or "qmx") / "PROJECT-RULES.md")


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
