"""E14 (EP7 lane 2, SEC2A lane 3): a script node prints its whole environment while the engine's
own process holds a fake provider key, `CLAUDE_CONFIG_DIR`, a `qmx/` ref, a HOME pointing at the
plan login and a TMP inside the QMX home. The script must see the run context (AD-24) and none of
those.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e14_script_env.py`
Writes `evidence/sec2a/<ENGINE_LOG_PREFIX>sec2a-e14.log`. Every planted value is a fake canary; no
real key, login or keyring value is read. No model and no ship home.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from common import Log, throwaway_home
from x07_nodes import cli, edge, events, node, of, run_id_of, write_folder

CANARY: Final = "fake-ep7-canary-not-a-key"
CONTEXT: Final = (
    "QMX_RUN_ID",
    "QMX_NODE_ID",
    "QMX_ATTEMPT",
    "QMX_MODE",
    "QMX_FAKE",
    "QMX_NOW",
    "QMX_WORK",
    "QMX_WORK_SHARED",
    "QMX_CODE",
)
PRINT_ENV: Final = """
    import json, os
    print(json.dumps(dict(os.environ)))
"""


def main() -> int:
    log = Log("sec2a", "sec2a-e14")
    home = throwaway_home("sec2a", "e14")
    plan = str(home.resolve() / "claude")
    root = write_folder(
        home / "wf-env",
        [node("start", "trigger"), node("env", "script", script="scripts/env.py")],
        {"start": {"main": [edge("env")]}},
        {"env": PRINT_ENV},
    )
    planted = {
        "ANTHROPIC_API_KEY": CANARY,
        "CLAUDE_CONFIG_DIR": plan,
        "OPENAI_API_KEY": CANARY,
        "QMX_PROVIDER_REF": "qmx/openrouter",
        "HOME": plan,
        "TMPDIR": plan.replace("\\", "/"),
        "TEMP": plan.replace("\\", "\\\\") + "\\\\tmp",
        "TMP": str(home.resolve() / "tmp"),
    }
    log(f"planted in the engine's environment: {sorted(planted)}")
    code, lines = cli(log, "run", str(root), "--home", str(home), **planted)
    seen: dict[str, str] = of(events(home, run_id_of(lines)), "node_finished", "env")[0]["outputs"][
        "main"
    ]
    log(f"names the script saw: {json.dumps(sorted(seen))}")
    names = " ".join(seen).upper()
    values = "\n".join(seen.values())
    log.check("the run finished", code == 0, lines[-1:])
    log.check("no ANTHROPIC name", "ANTHROPIC" not in names, "ANTHROPIC" in names)
    log.check("no CLAUDE name", "CLAUDE" not in names, "CLAUDE" in names)
    log.check("no OPENAI name", "OPENAI" not in names, "OPENAI" in names)
    log.check("no planted canary value", CANARY not in values, CANARY in values)
    log.check("no qmx/ value", "qmx/" not in values, "qmx/" in values)
    log.check("no plan path in any value", plan.lower() not in values.lower(), plan)
    inside = [
        name for name, value in seen.items() if under(value, home.resolve()) and name != "PATH"
    ]
    log.check("no value is the home or inside it", inside == [], inside)
    missing = [name for name in CONTEXT if not seen.get(name)]
    log.check("the run context is all there", missing == [], missing)
    run_id = run_id_of(lines)
    log(f"run context: { {name: seen.get(name) for name in CONTEXT} }")
    log.check("QMX_RUN_ID names the run", seen.get("QMX_RUN_ID") == run_id, seen.get("QMX_RUN_ID"))
    log.check("QMX_MODE is test", seen.get("QMX_MODE") == "test", seen.get("QMX_MODE"))
    log.check(
        "the attempt's cwd is its overlay beside the home, not in it",
        Path(seen.get("QMX_WORK", "")).parents[2] == Path(f"{home.resolve()}.zones")
        and not under(seen.get("QMX_WORK", ""), home.resolve()),
        seen.get("QMX_WORK"),
    )
    return log.verdict()


def under(value: str, home: Path) -> bool:
    """True when one path in the value is the home or sits inside it, compared by component."""
    for entry in value.split(";"):
        if entry.strip():
            path = Path(entry.strip())
            if path == home or home in path.parents:
                return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
