"""P-CTREFRESH (PRB-CT, engine AD-67): a refresh on the home rotates the pair and kills the old one.

Run on the app's home (the server) after his one demo sign-in, as the `qmx` user. It refreshes
the grant at cTrader's token endpoint, stores the new pair in the home's key store before it lets
go of the old one, reopens a session with the new access token, then asks for the account list
with the old access token and expects a refusal. It records the milliseconds for one refresh and
reopen (DATA-PLAN perf, no fail rule).

Whether a second grant for the same cTrader ID under the same app revokes the first needs a
second sign-in; with `--second-grant NAME` naming that pair's key store entry, the probe checks
the first pair after the second exists, and otherwise records `not run`.

**Pass:** the new pair reads the account list, the old access token is refused, and the stored
pair is the new one.
**Fail:** the refresh is refused, the new pair cannot read, or the old pair still reads. The
fallback parks DR5B and keeps today's short sessions.

    uv run --no-sync --project qmx-agents python scripts/probes/data/p_ctrefresh.py --dry-run \
        --protocol /srv/qmx/proto/openapi.pb --tag 101
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from collections.abc import Sequence

from common import Report
from p_ctscope import (
    DEMO,
    Grant,
    ProbeTransport,
    VenueRefused,
    account_list,
    app_auth,
    common_arguments,
    compiled,
    dry_run,
    load_grant,
)
from qmf.venue.proto import CompiledProto
from qmx_broker.oauth import TOKEN_URL, OAuthRefused, Tokens, refresh_tokens
from qmx_host.venue_session import TOKEN_NAME, HomeKeyStore


async def reads(proto: CompiledProto, grant: Grant, access: str) -> bool:
    transport = await ProbeTransport.connect(proto, DEMO)
    try:
        await app_auth(transport, grant.app)
        try:
            listed = await account_list(transport, access)
        except VenueRefused:
            return False
        return "ctidTraderAccount" in listed or "permissionScope" in listed
    finally:
        await transport.close()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    common_arguments(parser)
    parser.add_argument("--token-url", default=TOKEN_URL)
    parser.add_argument("--second-grant", default="", help="key store name of a second pair")
    arguments = parser.parse_args(argv)
    report = Report("P-CTREFRESH")
    if arguments.dry_run:
        return dry_run(report, arguments)
    keys = HomeKeyStore(arguments.home)
    grant = load_grant(arguments.home, arguments.machine)
    proto = compiled(arguments.protocol, arguments.tag)
    started = time.perf_counter()
    try:
        fresh = refresh_tokens(grant.app, grant.tokens.refresh_token, token_url=arguments.token_url)
    except OAuthRefused as refused:
        report.fail(f"the refresh was refused with {refused.code}")
        return report.render()
    keys.replace(TOKEN_NAME, fresh.document())
    new_reads = asyncio.run(reads(proto, grant, fresh.access_token))
    report.numbers["refresh and reopen ms"] = round((time.perf_counter() - started) * 1000)
    old_reads = asyncio.run(reads(proto, grant, grant.tokens.access_token))
    stored = keys.read(TOKEN_NAME)
    report.numbers["new pair reads"] = new_reads
    report.numbers["old pair reads"] = old_reads
    if not new_reads:
        report.fail("the refreshed pair cannot read the account list")
    if old_reads:
        report.fail("the old access token still reads after the refresh")
    if stored is None or Tokens.from_document(stored) != fresh:
        report.fail("the key store does not hold the refreshed pair")
    if arguments.second_grant:
        second = keys.read(arguments.second_grant)
        if second is None:
            report.fail(f"{arguments.second_grant} is not in the key store")
        else:
            first_reads = asyncio.run(reads(proto, grant, fresh.access_token))
            report.numbers["first grant reads after the second"] = first_reads
    else:
        report.numbers["second grant"] = "not run, needs a second sign-in"
    return report.render()


if __name__ == "__main__":
    sys.exit(main())
