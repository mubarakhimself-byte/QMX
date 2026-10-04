"""Actual cross-process lock and abrupt process restart on the local fixture."""

import json
import os
import subprocess
import sys
from pathlib import Path

from qmf.core import is_ok
from test_spot_paper_slice import open_account, tick


def test_other_process_refuses_owned_account_and_exit_releases_lock(tmp_path: Path) -> None:
    opened = open_account(tmp_path)
    assert is_ok(opened)
    account = opened.value
    assert is_ok(tick(account))
    assert is_ok(account.submit("buy", "buy", "0.100", "100.00", now_ns=1000))
    environment = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
    code = (
        "import json,sys; from pathlib import Path; "
        "from qmf.core import is_ok,is_refusal; "
        "from test_spot_paper_slice import open_account; "
        "r=open_account(Path(sys.argv[1]), node='other-process'); "
        "print(json.dumps({'refused':is_refusal(r)})); "
        "r.value.close() if is_ok(r) else None"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", code, str(tmp_path)],
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        assert json.loads(result.stdout)["refused"] is True
    finally:
        account.close()
    # The new process commits a partial fill, then os._exit skips close/finally.
    crash_code = (
        "import os,sys; from pathlib import Path; from qmf.core import is_ok; "
        "from test_spot_paper_slice import open_account,tick; "
        "r=open_account(Path(sys.argv[1]), node='other-process'); "
        "assert is_ok(r); assert is_ok(tick(r.value,2,1001,True,quantity='0.050')); "
        "os._exit(0)"
    )
    subprocess.run(
        [sys.executable, "-c", crash_code, str(tmp_path)],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    resumed = open_account(tmp_path)
    assert is_ok(resumed)
    try:
        state = resumed.value.query()
        assert state["orders"][0]["filled"] == "0.050"
        assert state["feed_status"] == "UNSYNCED"
        assert is_ok(resumed.value.cancel("buy"))
        assert resumed.value.query()["balances"]["USDT"]["reserved"] == "0"
    finally:
        resumed.value.close()
