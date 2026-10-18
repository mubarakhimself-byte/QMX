"""S2 at the host. The plan login check reads the subscription method in the ship home and
refuses a throwaway home with no login. No model turn; `claude auth status` only.
"""

from __future__ import annotations

import os
import shutil
import sys

from common import FAKE_HOME, LAUNCHER, SCRATCH, SHIP, Log, boot, require_login
from qma.harness.home import ClaudeSettings, QmxHome, code_settings, plan_auth_method
from qma.harness.launch import LaunchRefused


def main() -> int:
    log = Log("hp5-s02")
    boot()
    os.environ |= {"HOME": str(FAKE_HOME), "USERPROFILE": str(FAKE_HOME)}
    require_login(log)
    empty = QmxHome(SCRATCH / "s02-empty")
    shutil.rmtree(empty.root, ignore_errors=True)
    for home in (QmxHome(SHIP / "home"), empty):
        workspace = home.workspaces_dir
        settings = code_settings(
            ClaudeSettings(),
            launcher=LAUNCHER,
            workspace=workspace,
            memory_dir=home.memory_dir(workspace),
        )
        auth = plan_auth_method(home, settings)
        log(f"{home.plan_dir}: {auth}")
        try:
            auth.require()
            refusal = None
        except LaunchRefused as error:
            refusal = str(error)
        if home is empty:
            log.check("the empty home is refused", refusal is not None, refusal)
        else:
            log.check("the ship home reads the subscription method", refusal is None, auth.method)
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
