"""Process entry for the composed qma-daemon (Story 36.1; FR-W09).

Not an operator command line: mutating acts arrive over the CT-40 wire.
QMB remains the platform's single CLI (DEC-0336).
``--recover-control`` is the QMB-invoked one-shot recover writer (Story 67.4).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys

from qma.daemon.bootstrap_config import BootstrapConfigError, load_plugin_load_configs
from qma.daemon.host_control import resolve_daemon_root
from qma.daemon.process import (
    DAEMON_RECOVER_ENV,
    DAEMON_RECOVER_FLAG,
    DEFAULT_BIND_PORT,
    DaemonProcess,
    run_recover_entry,
)
from qmf.core import is_refusal


def _recover_requested(argv: list[str]) -> bool:
    if DAEMON_RECOVER_FLAG in argv:
        return True
    return os.environ.get(DAEMON_RECOVER_ENV) == "1"


def _recover_main() -> int:
    root = resolve_daemon_root(os.environ)
    try:
        plugin_load_configs = load_plugin_load_configs(root)
    except BootstrapConfigError as exc:
        _refuse(str(exc))
        return 2
    recovered = run_recover_entry(
        root,
        machine=os.environ.get("QMA_DAEMON_MACHINE", "workstation"),
        boot_epoch_id=os.environ.get("QMA_DAEMON_BOOT_EPOCH", "boot"),
        plugin_load_configs=plugin_load_configs,
        log_handler=logging.StreamHandler(),
    )
    if is_refusal(recovered):
        _refuse(
            f"recover-control refused: {recovered.category.value}: "
            f"{recovered.context.get('reason', recovered.context)}"
        )
        return 2
    return 0


def main() -> int:
    if _recover_requested(sys.argv[1:]):
        return _recover_main()
    root = resolve_daemon_root(os.environ)
    machine = os.environ.get("QMA_DAEMON_MACHINE", "workstation")
    boot = os.environ.get("QMA_DAEMON_BOOT_EPOCH", "boot")
    port_raw = os.environ.get("QMA_DAEMON_BIND_PORT", str(DEFAULT_BIND_PORT))
    try:
        bind_port = int(port_raw)
    except ValueError:
        _refuse(f"QMA_DAEMON_BIND_PORT must be an integer, got {port_raw!r}")
        return 2
    try:
        plugin_load_configs = load_plugin_load_configs(root)
    except BootstrapConfigError as exc:
        _refuse(str(exc))
        return 2
    composed = DaemonProcess.compose(
        root,
        machine=machine,
        boot_epoch_id=boot,
        bind_port=bind_port,
        plugin_load_configs=plugin_load_configs,
        log_handler=logging.StreamHandler(),
    )
    if is_refusal(composed):
        _refuse(
            f"daemon composition refused: {composed.category.value}: "
            f"{composed.context.get('reason', composed.context)}"
        )
        return 2
    process = composed.value
    try:
        served = asyncio.run(process.serve())
        if is_refusal(served):
            _refuse(
                f"daemon serve refused: {served.category.value}: "
                f"{served.context.get('reason', served.context)}"
            )
            return 2
        return 0
    except KeyboardInterrupt:
        return 0
    finally:
        process.close()


def _refuse(message: str) -> None:
    """Print one actionable structured refusal to the operator's stderr."""
    print(
        json.dumps({"level": "ERROR", "event": "daemon.startup_refused", "reason": message}),
        file=sys.stderr,
    )


if __name__ == "__main__":
    raise SystemExit(main())
