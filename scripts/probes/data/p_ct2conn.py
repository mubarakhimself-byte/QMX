"""P-CT2CONN (PRB-CT, engine AD-67): what a second demo connection under the same app does.

Two runs, one per machine, under the read app. `--role hold` runs on the PC: it opens a demo
connection, authorises the app with the PC's `qmx/read/ctrader-app` and listens, recording every
unasked message and whether the socket drops; it names the PC's home with `--home`. `--role
second` runs on the server's home, the default, while the first is held: it opens another demo
connection under the same app and authorises it with the server's vault copy. Neither run reads
or needs the grant's tokens, so the PC still holds none.

**Pass:** the result is recorded either way. The row says whether the second was refused with
error 67 or the first was dropped, and whether the drop came with an event.
**Fail:** neither run finished. When the first dies with no event, DR5B's health walk gains a
liveness read every check.

    uv run --no-sync --project qmx-agents python scripts/probes/data/p_ct2conn.py --dry-run \
        --role hold --home D:/QMX-worktrees/qma-ship/home --machine pc \
        --protocol D:/proto/openapi.pb --tag 101
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence

import keyring
from common import Report
from p_ctscope import DEMO, ProbeTransport, VenueRefused, common_arguments, compiled, dry_run
from qmf.venue.proto import CompiledProto
from qmx_broker.credentials import CTRADER_APP
from qmx_broker.oauth import AppCredential
from qmx_host.venue_session import vault_app


def app_for(role: str, arguments: argparse.Namespace) -> AppCredential:
    """The PC reads its own Credential Manager entry; the server opens its vault copy."""
    if role == "second":
        return vault_app(arguments.home, arguments.machine)
    raw = keyring.get_password(CTRADER_APP, CTRADER_APP.removeprefix("qmx/"))
    if raw is None:
        raise SystemExit(f"{CTRADER_APP} is not in Credential Manager; run the app copy first")
    return AppCredential.parse(raw)


async def connect(report: Report, proto: CompiledProto, app: AppCredential, listen: float) -> None:
    transport = await ProbeTransport.connect(proto, DEMO)
    try:
        try:
            await transport.request(
                "ProtoOAApplicationAuthReq",
                {"clientId": app.client_id, "clientSecret": app.client_secret},
            )
            report.numbers["application auth"] = "accepted"
        except VenueRefused as refused:
            report.numbers["application auth"] = f"refused with {refused.code}"
        seen = await transport.events(listen)
        report.numbers["unasked messages"] = seen
        report.numbers["dropped"] = "disconnected" in seen
    finally:
        await transport.close()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    common_arguments(parser)
    parser.add_argument("--role", choices=("hold", "second"), required=True)
    parser.add_argument("--listen", type=float, default=120.0, help="seconds to listen (a bound)")
    arguments = parser.parse_args(argv)
    report = Report(f"P-CT2CONN ({arguments.role})")
    if arguments.dry_run:
        return dry_run(report, arguments)
    app = app_for(arguments.role, arguments)
    asyncio.run(connect(report, compiled(arguments.protocol, arguments.tag), app, arguments.listen))
    return report.render()


if __name__ == "__main__":
    sys.exit(main())
