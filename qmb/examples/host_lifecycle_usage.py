"""L27 reference usage: qmb host start|status|stop|configure|rotate-control|recover-control."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from tempfile import TemporaryDirectory

from qmb.doors.cli import COMMAND_GROUPS, HOST_COMMANDS, HOST_CONFIGURE_COMMANDS, command_tree
from qmb.doors.cli.host import (
    INSPECT_CWD_RELATIVE_ROOT,
    INSPECT_SHA_COMMAND_GROUPS,
    PAIRING_SESSION_TTL_REGISTRY_KEY,
    QMB_HOST_CONFIGURE_EXISTED_AT_INSPECT_SHA,
    QMB_HOST_EXISTED_AT_INSPECT_SHA,
    claim_host_configure_existed_at_inspect_sha,
    claim_qmb_host_existed_at_inspect_sha,
    claim_recover_control_existed_at_inspect_sha,
    claim_rotate_control_existed_at_inspect_sha,
    claim_types_absent_at_inspect_sha,
    invoke_host_configure_pairing_ttl,
    invoke_host_recover_control,
    invoke_host_rotate_control,
    invoke_host_start,
    invoke_host_status,
    invoke_host_stop,
    product_daemon_root,
)
from qmf.core.refusal import is_ok, is_refusal


def main() -> None:
    assert "host" not in INSPECT_SHA_COMMAND_GROUPS
    assert COMMAND_GROUPS[-1] == "host"
    assert (
        command_tree()["host"]
        == HOST_COMMANDS
        == (
            "start",
            "status",
            "stop",
            "configure",
            "rotate-control",
            "recover-control",
        )
    )
    assert HOST_CONFIGURE_COMMANDS == ("pairing-ttl",)
    assert QMB_HOST_EXISTED_AT_INSPECT_SHA is False
    assert QMB_HOST_CONFIGURE_EXISTED_AT_INSPECT_SHA is False
    assert is_refusal(claim_qmb_host_existed_at_inspect_sha(True))
    assert is_refusal(claim_host_configure_existed_at_inspect_sha(True))
    assert is_refusal(claim_rotate_control_existed_at_inspect_sha(True))
    assert is_refusal(claim_recover_control_existed_at_inspect_sha(True))
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

        def sleeper(_seconds: float) -> None:
            return None

        started = invoke_host_start(root=root, spawn=spawn, wait_attempts=1, sleeper=sleeper)
        assert is_ok(started), started
        assert started.value["state"] == "started"
        again = invoke_host_start(root=root, spawn=spawn, wait_attempts=1)
        assert is_ok(again), again
        assert again.value["state"] == "already-running"
        assert again.value["spawned"] is False

        def transport(
            verb: str,
            token: str,
            *,
            root: Path,
            extra: Mapping[str, object] | None = None,
        ) -> dict[str, object]:
            expected = "example-token"
            assert token == expected
            if verb == "status":
                return {
                    "ok": True,
                    "status": {
                        "lock": "held",
                        "pid": os.getpid(),
                        "bind": "127.0.0.1:8765",
                        "operator_established": True,
                        "ttl": "unset",
                        "pending_record_ids": [],
                        "bound_record_ids": [],
                    },
                }
            if verb == "configure":
                assert extra is not None
                assert extra["target"] == "pairing-ttl"
                assert extra["duration"] == "PT15M"
                return {
                    "ok": True,
                    "configured": {
                        "registry_key": PAIRING_SESSION_TTL_REGISTRY_KEY,
                        "ttl": "set",
                        "writer": "host.configure.pairing-ttl",
                    },
                }
            if verb == "rotate-control":
                return {
                    "ok": True,
                    "rotated": {
                        "rotated": True,
                        "local_operator": "unchanged",
                        "writer": "host.rotate-control",
                    },
                }
            (root / ".daemon_writer").unlink()
            return {"ok": True, "stopped": True}

        status = invoke_host_status(root=root, transport=transport)
        assert is_ok(status), status
        configured = invoke_host_configure_pairing_ttl("PT15M", root=root, transport=transport)
        assert is_ok(configured), configured
        assert configured.value["registry_key"] == PAIRING_SESSION_TTL_REGISTRY_KEY
        rotated = invoke_host_rotate_control(root=root, transport=transport)
        assert is_ok(rotated), rotated
        assert rotated.value["rotated"] is True
        assert rotated.value["local_operator"] == "unchanged"
        stopped = invoke_host_stop(root=root, transport=transport, wait_attempts=1)
        assert is_ok(stopped), stopped
        assert stopped.value["state"] == "stopped"
        (root / "host_control").unlink()

        def recover_spawn(argv: tuple[str, ...], *, env: Mapping[str, str], root: Path) -> int:
            assert "--recover-control" in argv
            assert env["QMA_DAEMON_RECOVER_CONTROL"] == "1"
            (root / "host_control").write_text("recovered-token\n", encoding="utf-8")
            return os.getpid()

        recovered = invoke_host_recover_control(
            root=root,
            spawn=recover_spawn,
            wait_attempts=1,
            sleeper=sleeper,
            owns_root=True,
        )
        assert is_ok(recovered), recovered
        assert recovered.value["recovered"] is True
        assert recovered.value["bound_8765"] is False
        readable = invoke_host_recover_control(root=root, spawn=recover_spawn, owns_root=True)
        assert is_refusal(readable)
    print("qmb host start|status|stop|configure|rotate-control|recover-control ok")


if __name__ == "__main__":
    main()
