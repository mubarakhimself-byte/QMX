"""P-CTSCOPE (PRB-CT, engine AD-67): the read app's demo grant cannot trade.

Run on the app's home (the server) after his one demo sign-in, as the `qmx` user. The app's id
and secret come from the home's own vault copy (`qmx/read/ctrader-app`), the pair from the home's
key store (`qmx/token/ctrader-app`). Nothing is printed but names, codes and verdicts.

The cTrader half reads the grant's `permissionScope` from `ProtoOAGetAccountListByAccessTokenRes`
and the accounts it lists. It sends no order: the broker transport admits only sign-in and read
requests, and this probe adds none. The MT5 half reads an investor login's `trade_allowed` when
`--mt5-ref` names one; the exchange half reads a Binance key's API restrictions when
`--exchange-ref` names one. A half that does not run is recorded `not run` and labelled `trade`,
because only a probe can prove `read`.

**Pass:** the scope is `SCOPE_VIEW`, every listed account is demo, and each half that ran found a
credential that cannot trade.
**Fail:** the scope is `SCOPE_TRADE` or unreported, a live account is listed, or a half that ran
found trading allowed.

    uv run --no-sync --project qmx-agents python scripts/probes/data/p_ctscope.py --dry-run \
        --home /srv/qmx/home --protocol /srv/qmx/proto/openapi.pb --tag 101
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, override

import keyring
from common import Report
from google.protobuf.json_format import MessageToDict
from qmf.core import is_refusal
from qmf.venue.connection import encode_framed_payload
from qmf.venue.proto import CompiledProto, compile_descriptor_set
from qmx_broker.credentials import credentials
from qmx_broker.ctrader_transport import CTraderTransport
from qmx_broker.oauth import AppCredential, Tokens
from qmx_host.venue_session import TOKEN_NAME, HomeKeyStore, vault_app

DEMO: Final = "demo"
HEARTBEAT_S: Final = 10.0


@dataclass(frozen=True, slots=True)
class Grant:
    """The home's app credential and pair, held in memory for one probe run."""

    app: AppCredential
    tokens: Tokens


def common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--home", type=Path, required=True, help="the app's home folder")
    parser.add_argument("--machine", default="contabo", help="the home's placement name")
    parser.add_argument("--protocol", type=Path, required=True, help="pinned FileDescriptorSet")
    parser.add_argument("--tag", type=int, required=True, help="the proto release tag")
    parser.add_argument(
        "--dry-run", action="store_true", help="parse the inputs and exit with no network call"
    )


def dry_run(report: Report, arguments: argparse.Namespace) -> int:
    """What a dry run checks: the inputs exist. It reads no secret and opens no socket."""
    for name in ("home", "protocol"):
        path: Path = getattr(arguments, name)
        report.numbers[name] = "present" if path.exists() else "missing"
    report.numbers["dry run"] = "no network call"
    print(f"{report.probe} DRY RUN {json.dumps(report.numbers, sort_keys=True)}")
    return 0


def load_grant(home: Path, machine: str) -> Grant:
    held = HomeKeyStore(home).read(TOKEN_NAME)
    if held is None:
        raise SystemExit(f"{TOKEN_NAME} is not in {home}/vault; sign in first")
    return Grant(vault_app(home, machine), Tokens.from_document(held))


def compiled(protocol: Path, tag: int) -> CompiledProto:
    found = compile_descriptor_set(
        protocol.read_bytes(), package_name="openapi-proto-messages", release_tag=tag
    )
    if is_refusal(found):
        raise SystemExit("the protocol definitions do not compile")
    return found.value


class VenueRefused(Exception):
    """cTrader answered a request with an error. Only its code is kept: a remote description
    may echo a credential."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class ProbeTransport(CTraderTransport):
    """The broker's read transport, except that a refusal raises with its error code."""

    @override
    async def _receive(self) -> tuple[str, str, dict[str, Any]]:
        size = int.from_bytes(await self.reader.readexactly(4), "big")
        envelope = self._message("ProtoMessage")
        envelope.ParseFromString(await self.reader.readexactly(size))
        for name in self.proto.message_names():
            message = self._message(name)
            if name != "ProtoMessage" and message.payloadType == envelope.payloadType:
                message.ParseFromString(envelope.payload)
                body = MessageToDict(message, preserving_proto_field_name=True)
                if name in {"ProtoErrorRes", "ProtoOAErrorRes"}:
                    raise VenueRefused(str(body.get("errorCode", "unknown")))
                return name, str(envelope.clientMsgId), body
        raise ValueError("unknown payload type in the pinned definitions")

    async def heartbeat(self) -> None:
        """`ProtoHeartbeatEvent`, so an idle connection is not dropped for silence."""
        message = self._message("ProtoHeartbeatEvent")
        envelope = self._message("ProtoMessage")
        envelope.payloadType = message.payloadType
        envelope.payload = message.SerializeToString()
        frame = encode_framed_payload(envelope.SerializeToString())
        if is_refusal(frame):
            raise ValueError("could not frame the heartbeat")
        self.writer.write(frame.value)
        await self.writer.drain()

    async def events(self, seconds: float) -> list[str]:
        """The message names that arrive unasked within `seconds`, heartbeating every 10."""
        seen: list[str] = []
        deadline = asyncio.get_running_loop().time() + seconds
        while (left := deadline - asyncio.get_running_loop().time()) > 0:
            await self.heartbeat()
            try:
                async with asyncio.timeout(min(left, HEARTBEAT_S)):
                    while True:
                        name, _, _ = await self._receive()
                        if name != "ProtoHeartbeatEvent":
                            seen.append(name)
            except TimeoutError:
                continue
            except VenueRefused as refused:
                seen.append(f"error {refused.code}")
                return seen
            except (asyncio.IncompleteReadError, ConnectionError):
                seen.append("disconnected")
                return seen
        return seen


async def app_auth(transport: ProbeTransport, app: AppCredential) -> None:
    await transport.request(
        "ProtoOAApplicationAuthReq", {"clientId": app.client_id, "clientSecret": app.client_secret}
    )


async def account_list(transport: ProbeTransport, access: str) -> dict[str, Any]:
    return await transport.request("ProtoOAGetAccountListByAccessTokenReq", {"accessToken": access})


async def ctrader_half(report: Report, grant: Grant, proto: CompiledProto) -> None:
    transport = await ProbeTransport.connect(proto, DEMO)
    try:
        await app_auth(transport, grant.app)
        listed = await account_list(transport, grant.tokens.access_token)
    finally:
        await transport.close()
    scope = str(listed.get("permissionScope", "unreported"))
    accounts = listed.get("ctidTraderAccount", [])
    live = [str(item.get("ctidTraderAccountId")) for item in accounts if item.get("isLive")]
    report.numbers["permissionScope"] = scope
    report.numbers["accounts listed"] = len(accounts)
    report.numbers["live accounts listed"] = live
    if scope != "SCOPE_VIEW":
        report.fail(f"the demo grant's scope is {scope}, not SCOPE_VIEW")
    if live:
        report.fail(f"the demo grant lists live accounts {live}")


def mt5_half(report: Report, reference: str) -> None:
    if not reference:
        report.numbers["mt5"] = "not run, no investor login (labelled trade)"
        return
    import MetaTrader5 as mt5  # noqa: PLC0415  # pyright: ignore[reportMissingImports]

    raw = keyring.get_password(reference, reference.removeprefix("qmx/"))
    if raw is None:
        report.fail(f"{reference} is not in Credential Manager")
        return
    login = json.loads(raw)
    if not mt5.initialize(
        login=int(login["login"]), password=login["password"], server=login["server"]
    ):
        report.fail("the MT5 terminal did not sign in with the investor login")
        return
    try:
        allowed = bool(mt5.account_info().trade_allowed)
    finally:
        mt5.shutdown()
    report.numbers["mt5 trade_allowed"] = allowed
    if allowed:
        report.fail("the MT5 investor login reports trade_allowed")


def exchange_half(report: Report, reference: str) -> None:
    if not reference:
        report.numbers["exchange"] = "not run, no read-only key (labelled trade)"
        return
    import ccxt  # noqa: PLC0415  # pyright: ignore[reportMissingTypeStubs]

    key = credentials(reference)
    exchange: Any = ccxt.binance({"apiKey": key["apiKey"], "secret": key["secret"]})
    restrictions = exchange.sapiGetAccountApiRestrictions()
    trading = [
        flag
        for flag in ("enableSpotAndMarginTrading", "enableFutures", "enableWithdrawals")
        if str(restrictions.get(flag)).lower() == "true"
    ]
    report.numbers["exchange trading flags"] = trading
    if trading:
        report.fail(f"the exchange key allows {trading}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    common_arguments(parser)
    parser.add_argument("--mt5-ref", default="", help="qmx/* entry with an MT5 investor login")
    parser.add_argument("--exchange-ref", default="", help="qmx/read/* Binance read-only key")
    arguments = parser.parse_args(argv)
    report = Report("P-CTSCOPE")
    if arguments.dry_run:
        return dry_run(report, arguments)
    grant = load_grant(arguments.home, arguments.machine)
    asyncio.run(ctrader_half(report, grant, compiled(arguments.protocol, arguments.tag)))
    mt5_half(report, arguments.mt5_ref)
    exchange_half(report, arguments.exchange_ref)
    return report.render()


if __name__ == "__main__":
    sys.exit(main())
