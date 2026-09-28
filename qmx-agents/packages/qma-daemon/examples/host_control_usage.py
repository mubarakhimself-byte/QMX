"""L27 reference usage: product QMA_DAEMON_ROOT and host-control (Story 67.1)."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from qma.daemon.host_control import (
    HOST_CONTROL_EXISTED_AT_INSPECT_SHA,
    HOST_CONTROL_IS_CT40,
    INSPECT_CWD_RELATIVE_ROOT,
    LOCAL_OPERATOR_EXISTED_AT_INSPECT_SHA,
    LOCAL_OPERATOR_NEW_SQLITE_CLASS,
    claim_host_configure_existed_at_inspect_sha,
    claim_host_control_existed_at_inspect_sha,
    claim_local_operator_existed_at_inspect_sha,
    claim_types_absent_at_inspect_sha,
    host_control_call,
    load_local_operator,
    principal_count,
    product_daemon_root,
)
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import (
    BROWSER_SPAWNS_PYTHON,
    DAEMON_SPAWN_MODULE,
    HOST_CONTROL_ON_CT40_PORT,
    START_ORCHESTRATES_MISSIONS,
    DaemonProcess,
    supervised_spawn_argv,
)
from qma.wire import GrantRecord, WireEnvelope
from qmf.core import is_ok, is_refusal


def main() -> None:
    assert HOST_CONTROL_EXISTED_AT_INSPECT_SHA is False
    assert LOCAL_OPERATOR_EXISTED_AT_INSPECT_SHA is False
    assert LOCAL_OPERATOR_NEW_SQLITE_CLASS is False
    assert HOST_CONTROL_IS_CT40 is False
    assert HOST_CONTROL_ON_CT40_PORT is False
    assert START_ORCHESTRATES_MISSIONS is False
    assert BROWSER_SPAWNS_PYTHON is False
    assert INSPECT_CWD_RELATIVE_ROOT not in product_daemon_root().parts
    assert supervised_spawn_argv("python")[-2:] == ("-m", DAEMON_SPAWN_MODULE)
    assert is_refusal(claim_host_control_existed_at_inspect_sha(True))
    assert is_refusal(claim_local_operator_existed_at_inspect_sha(True))
    assert is_refusal(claim_host_configure_existed_at_inspect_sha(True))
    assert is_refusal(claim_types_absent_at_inspect_sha(True))
    assert WireEnvelope.__name__ == "WireEnvelope"
    assert GrantRecord.__name__ == "GrantRecord"

    async def _run(root: Path) -> None:
        seed = root / "seed-corpus"
        seed.mkdir()
        composed = DaemonProcess.compose(
            root,
            machine="example-host",
            boot_epoch_id="boot-example-67-1",
            bind_port=0,
            plugin_load_configs=research_corpus_plugin_load_config(seed),
        )
        assert is_ok(composed), composed
        process = composed.value
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            assert process.host_control is not None
            assert process.host_control.bound is not None
            assert process.host_control.bound.port != 8765
            live = load_local_operator(process.sqlite)
            assert live is not None
            assert principal_count(process.sqlite) == 1
            status = await asyncio.to_thread(host_control_call, root, "status")
            assert is_ok(status), status
            assert status.value["ok"] is True
            snapshot = status.value["status"]
            assert isinstance(snapshot, dict)
            assert snapshot["operator_established"] is True
            assert snapshot["ttl"] == "unset"
            stopped = await asyncio.to_thread(host_control_call, root, "stop")
            assert is_ok(stopped), stopped
            for _ in range(50):
                if process.is_closed:
                    break
                await asyncio.sleep(0.01)
        finally:
            if not process.is_closed:
                await process.aclose()

    with tempfile.TemporaryDirectory() as raw:
        asyncio.run(_run(Path(raw)))


if __name__ == "__main__":
    main()
