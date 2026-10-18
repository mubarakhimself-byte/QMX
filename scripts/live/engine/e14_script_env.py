"""EP7 lane 2 (E14): a script node prints its whole environment while the engine's own process
holds a fake provider key, `CLAUDE_CONFIG_DIR`, a `qmx/` ref and a HOME pointing at the plan login.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e14_script_env.py`
Writes `evidence/ep7/<ENGINE_LOG_PREFIX>ep7-e14.log`. Every planted value is a fake canary; no real
key, login or keyring value is read. No model and no ship home.
"""

from __future__ import annotations

import json
from typing import Final

from common import Log, throwaway_home
from x07_nodes import cli, edge, events, node, of, run_id_of, write_folder

CANARY: Final = "fake-ep7-canary-not-a-key"
PRINT_ENV: Final = """
    import json, os
    print(json.dumps(dict(os.environ)))
"""


def main() -> int:
    log = Log("ep7", "ep7-e14")
    home = throwaway_home("ep7", "e14")
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
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(main())
