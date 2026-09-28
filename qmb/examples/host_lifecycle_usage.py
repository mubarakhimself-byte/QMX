"""L27 reference usage: qmb host start|status|stop (Story 67.1)."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from tempfile import TemporaryDirectory

from qmb.doors.cli import COMMAND_GROUPS, HOST_COMMANDS, command_tree
from qmb.doors.cli.host import (
    INSPECT_CWD_RELATIVE_ROOT,
    INSPECT_SHA_COMMAND_GROUPS,
    QMB_HOST_EXISTED_AT_INSPECT_SHA,
    claim_qmb_host_existed_at_inspect_sha,
    claim_types_absent_at_inspect_sha,
    invoke_host_start,
    invoke_host_status,
    invoke_host_stop,
    product_daemon_root,
)
from qmf.core.refusal import is_ok, is_refusal


def main() -> None:
    assert "host" not in INSPECT_SHA_COMMAND_GROUPS
    assert COMMAND_GROUPS[-1] == "host"
    assert command_tree()["host"] == HOST_COMMANDS == ("start", "status", "stop")
    assert QMB_HOST_EXISTED_AT_INSPECT_SHA is False
    assert is_refusal(claim_qmb_host_existed_at_inspect_sha(True))
    assert is_refusal(claim_types_absent_at_inspect_sha(True))
    product = product_daemon_root()
    assert product.name != INSPECT_CWD_RELATIVE_ROOT
    print("product QMA_DAEMON_ROOT is not qma-daemon-data")

    with TemporaryDirectory() as raw:
        root = Path(raw)

        def spawn(argv: tuple[str, ...], *, env: Mapping[str, str], root: Path) -> int:
            assert argv[-2:] == ("-m", "qma.daemon")
            assert env["QMA_DAEMON_ROOT"] == str(root)
            (root / ".daemon_writer").write_text(
                json.dumps(
                    {
                        "boot_epoch_id": "boot",
                        "machine": "example",
                        "pid": os.getpid(),
                        "role": "qma-daemon",
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            (root / "host_control").write_text("example-token\n", encoding="utf-8")
            (root / "host_control.bind").write_text(
                json.dumps({"host": "127.0.0.1", "port": 19236}),
                encoding="utf-8",
            )
            return os.getpid()

        started = invoke_host_start(
            root=root, spawn=spawn, wait_attempts=1, sleeper=lambda _s: None
        )
        assert is_ok(started), started
        assert started.value["state"] == "started"
        again = invoke_host_start(root=root, spawn=spawn, wait_attempts=1)
        assert is_ok(again), again
        assert again.value["state"] == "already-running"
        assert again.value["spawned"] is False

        def transport(verb: str, token: str, *, root: Path) -> dict[str, object]:
            expected = "example-token"
            assert token == expected
            if verb == "status":
                return {
                    "ok": True,
                    "status": {
                        "lock": "held",
                        "pid": os.getpid(),
                        "bind": "127.0.0.1:8765",
                        "operator_established": False,
                        "ttl": "unset",
                        "pending_record_ids": [],
                        "bound_record_ids": [],
                    },
                }
            (root / ".daemon_writer").unlink()
            return {"ok": True, "stopped": True}

        status = invoke_host_status(root=root, transport=transport)
        assert is_ok(status), status
        stopped = invoke_host_stop(root=root, transport=transport, wait_attempts=1)
        assert is_ok(stopped), stopped
        assert stopped.value["state"] == "stopped"
    print("qmb host start|status|stop ok")


if __name__ == "__main__":
    main()
