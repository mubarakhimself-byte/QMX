"""S28, the Effect registry. Three tool surfaces refuse the `qmx` server build: a tool with no
effect, a tool named `place_order`, and a second PROPOSE_MONEY tool besides the broker's
`propose_order`. The real tool list from a throwaway QMX home builds, as the control.

With `--regression`, the regression lane instead: `place_order` goes through the base
branch's `check_descriptor` (read with `git show`) and through the head `build_server`, and
both must refuse it. It writes `hp8-regression.log`.

    s28_effects.py [--regression [--base origin/qma/hp7]]
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from common import Log, throwaway_home

REPO = Path(__file__).resolve().parents[3]
DESCRIPTORS = "qmx-agents/packages/qma-core/src/qma/core/barriers/descriptors.py"


async def nothing(arguments: dict[str, Any]) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": str(arguments)}]}


def refused(log: Log, label: str, build: Any) -> None:
    try:
        build()
    except Exception as error:
        log.check(label, True, f"{type(error).__name__}: {error}")
        return
    log.check(label, False, "built")


def effects(log: Log) -> None:
    from qma.harness.tools import Effect, Grants, ToolDef, build_server  # noqa: PLC0415
    from qmx_broker.service import BrokerService  # noqa: PLC0415

    root = throwaway_home("hp8-s28")
    broker = BrokerService(root)

    def read(name: str) -> ToolDef:
        return ToolDef(name, name, {"type": "object"}, Effect.READ, nothing)

    def no_effect() -> object:
        bad: Any = None
        return build_server(
            [ToolDef("read_x", "x", {}, bad, nothing)], grants=Grants(), domain_write="allow"
        )

    real = ToolDef(
        "propose_order", "p", {}, Effect.PROPOSE_MONEY, nothing, target=broker.propose_order
    )
    second = ToolDef("stage_trade", "s", {}, Effect.PROPOSE_MONEY, nothing, target=nothing)
    refused(log, "a tool with no effect", no_effect)
    refused(
        log,
        "a tool named place_order",
        lambda: build_server(
            [read("read_bars"), read("place_order")], grants=Grants(), domain_write="allow"
        ),
    )
    refused(
        log,
        "a second PROPOSE_MONEY tool",
        lambda: build_server([real, second], grants=Grants(), domain_write="allow"),
    )
    asyncio.run(real_list(log, root))


async def real_list(log: Log, root: Path) -> None:
    from qma.harness import QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415
    from qma.harness.tools import Grants, build_server, tool_defs  # noqa: PLC0415
    from qmx_broker.service import BrokerService  # noqa: PLC0415
    from qmx_tools.service import DomainContext  # noqa: PLC0415

    home = QmxHome(root)
    control = control_service(home)
    domain = DomainContext(root=root)
    domain.control, domain.library = control, control.library
    defs = await tool_defs(control=control, broker=BrokerService(root), domain=domain)
    build_server(defs, grants=Grants(), domain_write="ask")
    log.check("control: the real QMX tool list builds", True, f"{len(defs)} tools")


def base_check(base: str) -> Any:
    git = shutil.which("git") or "git"
    source = subprocess.run(
        [git, "-C", str(REPO), "show", f"{base}:{DESCRIPTORS}"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    copy = Path(tempfile.mkdtemp()) / "base_descriptors.py"
    copy.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("base_descriptors", copy)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {base}:{DESCRIPTORS}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.check_descriptor


def regression(log: Log, base: str) -> None:
    from qma.harness.tools import Effect, Grants, ToolDef, build_server  # noqa: PLC0415

    log(f"base: {base}")
    check = base_check(base)
    refused(log, f"{base} check_descriptor refuses place_order", lambda: check("place_order", {}))
    tool = ToolDef("place_order", "p", {"type": "object"}, Effect.READ, nothing)
    refused(
        log,
        "head build_server refuses place_order",
        lambda: build_server([tool], grants=Grants(), domain_write="allow"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regression", action="store_true")
    parser.add_argument("--base", default="origin/qma/hp7")
    args = parser.parse_args()
    log = Log("hp8-regression" if args.regression else "hp8-s28")
    if args.regression:
        regression(log, args.base)
    else:
        effects(log)
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
