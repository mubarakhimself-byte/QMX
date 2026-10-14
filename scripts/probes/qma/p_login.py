"""S2, DESIGN open question 6. The operator signs the ship home in to his Max plan.

Run in an interactive terminal with the probe venv's Python. The CLI opens with
`forceLoginMethod: claudeai`. Type `/login`, check that no Console choice is offered,
finish the sign-in in the browser, then type `/exit`. The script then prints only the
login fields of `claude auth status`.
"""

from __future__ import annotations

import json
import subprocess

from common import CONFIG_DIR, FORCE_LOGIN, SCRATCH, Log, auth_method, bundled_cli, cli_env


def main() -> int:
    log = Log("hp0-login")
    cli = bundled_cli()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    argv = [str(cli), "--settings", json.dumps(FORCE_LOGIN)]
    log(f"starting {argv} with CLAUDE_CONFIG_DIR={CONFIG_DIR}")
    log("Type /login, note whether a Console option appears, sign in, then type /exit.")
    subprocess.run(argv, env=cli_env(), cwd=SCRATCH, check=False)
    status = auth_method(cli)
    log(f"auth status fields: {status}")
    stored = (CONFIG_DIR / ".credentials.json").exists()
    log(f"credentials file in the ship home (existence only, the gate every probe uses): {stored}")
    verdict = "PASS" if status.get("loggedIn") else "FAIL"
    log.row("S2 auth method", status.get("authMethod"), verdict)
    log.row("S2 api provider", status.get("apiProvider"), verdict)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
