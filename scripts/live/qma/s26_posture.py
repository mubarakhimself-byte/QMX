"""S26, the money posture fails closed. Runs the posture the usage page shows against a
throwaway QMX home and this PC's real keyring inventory, by name only. No value is read.

    s26_posture.py unknown      add keyring entry qmx/x-test with a fake value; SPEED_BUMP
    s26_posture.py unreachable  add qmx/x-test with a proof, prove every other entry, and name
                                qmx/x-test-unreachable in [brokers] with no keyring entry; the
                                probe reports it not reachable, and the posture is SPEED_BUMP
    s26_posture.py proven       a scope-proof fixture for every entry in the live inventory;
                                STRUCTURAL

The cases that add qmx/x-test remove it in a `finally`, then compare the entry names listed
before and after. PASS when the posture is the expected one and the names match.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import sys
from pathlib import Path

import keyring
from common import SCRATCH, Log, use_fake_home
from qma.harness.harness import broker_inventory, posture_view
from qma.harness.home import DOCTOR_CHAT, QmxHome
from qma.harness.launch import PlanLaunch, launch_env
from qma.harness.money import (
    exposure_targets,
    run_exposure_probe,
    save_exposure,
    save_scope_proof,
    store_names,
)
from qma.harness.routes import control_service
from qma.harness.tools import secret_files

TEST_ENTRY = "qmx/x-test"
UNREACHABLE = "qmx/x-test-unreachable"
FAKE_VALUE = "fake-hp14-not-a-secret"
EXPECTED = {"unknown": "SPEED_BUMP", "unreachable": "SPEED_BUMP", "proven": "STRUCTURAL"}


def fresh_home(case: str) -> QmxHome:
    root = SCRATCH / "hp14" / f"s26-{case}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return QmxHome(root)


def prove(home: QmxHome, names: frozenset[str], non_broker: frozenset[str], log: Log) -> None:
    for name in sorted(names - non_broker):
        save_scope_proof(home.state_dir, name, refused_for_scope=True, source="s26 fixture")
        log(f"fixture proof: {name}")


async def probe(home: QmxHome, inventory: frozenset[str], log: Log) -> None:
    targets = exposure_targets(
        home.root, inventory, None, secret_files(home), Path.home() / ".claude"
    )
    env = {
        **os.environ,
        **launch_env(PlanLaunch(), home=home, session_id=DOCTOR_CHAT, cap=""),
    }
    report = await run_exposure_probe(env, targets, cli_version="s26")
    save_exposure(home.state_dir, report)
    for finding in report.findings:
        if finding.target.kind == "keyring_entry":
            log(f"probe {finding.target.value}: reachable {finding.reachable} ({finding.detail})")


def run_case(case: str, log: Log) -> None:
    home = fresh_home(case)
    control = control_service(home)
    if case == "unreachable":
        broker = {
            "id": "s26",
            "name": "S26 fixture",
            "adapter": "ctrader",
            "connections": [{"id": "c", "credential_ref": UNREACHABLE, "environment": "demo"}],
        }
        control.settings_put("brokers", {"brokers": [broker]})
    inventory, non_broker = broker_inventory(control)
    log(f"inventory: {sorted(inventory)}")
    log(f"known not to be broker credentials: {sorted(non_broker)}")
    if case == "unreachable":
        prove(home, inventory - {UNREACHABLE}, non_broker, log)
        asyncio.run(probe(home, inventory, log))
    elif case == "proven":
        prove(home, inventory, non_broker, log)
    view = posture_view(home, control)
    log(f"posture: {view.posture.name}; unproven: {list(view.unproven)}")
    log(f"note: {view.note()}")
    log.check(
        f"posture is {EXPECTED[case]}", view.posture.name == EXPECTED[case], view.posture.name
    )
    expected_unproven = {
        "unknown": TEST_ENTRY in view.unproven,
        "unreachable": list(view.unproven) == [UNREACHABLE],
        "proven": view.unproven == (),
    }[case]
    log.check("the unproven list names what it should", expected_unproven, list(view.unproven))
    if case == "unreachable":
        exposure = view.exposure
        finding = (
            None
            if exposure is None
            else next(f for f in exposure.findings if f.target.value == UNREACHABLE)
        )
        log.check(
            f"the probe could not reach {UNREACHABLE}",
            finding is not None and finding.reachable is False,
            None if finding is None else finding.detail,
        )


def main() -> int:
    parser = argparse.ArgumentParser(prog="s26_posture.py")
    parser.add_argument("case", choices=sorted(EXPECTED))
    args = parser.parse_args()
    log = Log(f"hp14-s26-{args.case}")
    use_fake_home()
    adds = args.case in ("unknown", "unreachable")
    before = store_names()
    log(f"keyring names before: {None if before is None else sorted(before)}")
    if before is None:
        log("BLOCKED: this PC's keyring cannot be listed")
        return 3
    try:
        if adds:
            keyring.set_password(TEST_ENTRY, TEST_ENTRY.removeprefix("qmx/"), FAKE_VALUE)
            log(f"added {TEST_ENTRY} with a fake value")
        run_case(args.case, log)
    finally:
        if adds:
            keyring.delete_password(TEST_ENTRY, TEST_ENTRY.removeprefix("qmx/"))
            log(f"removed {TEST_ENTRY}")
        after = store_names()
        log(f"keyring names after: {None if after is None else sorted(after)}")
        log.check("keyring names after equal those before", after == before, after == before)
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
