"""S27, broker credential scope. FOR THE OPERATOR ONLY: it reads a broker credential from the
keyring to log in, so no agent and no check lane runs it.

For each `--account`, it sends one market order request for the symbol's minimum volume on that
cTrader demo account and records whether the broker refuses it for scope. It refuses, before
any credential is read, an account id that settings.toml [brokers] does not list under a
connection marked `environment = "demo"`, and it only ever connects to the demo host.

Each broker credential in the keyring inventory gets one stored result under
`<home>/state/scope-proofs/`: refused for scope, refused for another reason, accepted (it can
trade; close the demo position), or not tested because no demo account given uses it. An
untested entry never overwrites an earlier result.

    s27_broker_scope.py --account <ctidTraderAccountId> [--account ...]
        [--home D:/QMX-worktrees/qma-ship/home] [--symbol EURUSD] [--scope-code ACCESS_DENIED]

`--scope-code` names a cTrader error code that means "this token may not trade"; the default
is ACCESS_DENIED. Any other refusal is stored as not proven, with its code, so the operator
can decide. The log holds names, ids and error codes, never a credential or a broker message.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common import SHIP_HOME, Log
from google.protobuf.json_format import MessageToDict, ParseDict
from qma.harness.harness import broker_inventory
from qma.harness.home import QmxHome
from qma.harness.money import UNLISTED, proof_path, save_scope_proof
from qma.harness.routes import control_service
from qmf.core import is_refusal
from qmf.venue.connection import encode_framed_payload
from qmf.venue.proto import CompiledProto, compile_descriptor_set
from qmx_broker.adapters import CTraderAdapter
from qmx_broker.credentials import credentials
from qmx_broker.ctrader_transport import CTraderTransport
from qmx_broker.models import Account, Broker, BrokerSettings, Connection

ANSWERS = frozenset(
    {"ProtoErrorRes", "ProtoOAErrorRes", "ProtoOAOrderErrorEvent", "ProtoOAExecutionEvent"}
)
ORDER_WAIT_S = 15.0


class Refused(Exception):
    """The run stops before any credential is read."""


@dataclass(frozen=True)
class Target:
    broker: Broker
    connection: Connection
    account: Account

    @property
    def credential(self) -> str:
        return (self.account.credential_ref or self.connection.credential_ref).casefold()


def demo_targets(settings: BrokerSettings, ids: list[str]) -> list[Target]:
    targets: list[Target] = []
    for wanted in ids:
        found = [
            Target(broker, connection, account)
            for broker in settings.brokers
            for connection in broker.connections
            for account in connection.accounts
            if account.id == wanted
        ]
        if not found:
            raise Refused(f"account {wanted} is not listed in settings.toml [brokers]")
        for target in found:
            if target.connection.environment != "demo":
                raise Refused(f"account {wanted} is not marked demo in [brokers]; refused")
            if target.broker.adapter != "ctrader":
                raise Refused(f"account {wanted} is not a cTrader account; S27 tests cTrader")
        targets += found
    return targets


def message(proto: CompiledProto, name: str) -> Any:
    found = proto.message_class(name)
    if is_refusal(found):
        raise ValueError(f"the pinned protocol has no {name}")
    return found.value()


async def answer(transport: CTraderTransport) -> tuple[str, str | None]:
    """The next answer frame's name and, for an error, its code only."""
    proto = transport.proto
    while True:
        size = int.from_bytes(await transport.reader.readexactly(4), "big")
        envelope = message(proto, "ProtoMessage")
        envelope.ParseFromString(await transport.reader.readexactly(size))
        for name in proto.message_names():
            if name not in ANSWERS:
                continue
            body = message(proto, name)
            if getattr(body, "payloadType", None) == int(envelope.payloadType):
                body.ParseFromString(envelope.payload)
                code = MessageToDict(body, preserving_proto_field_name=True).get("errorCode")
                return name, None if code is None else str(code)


async def send_order(transport: CTraderTransport, values: dict[str, Any]) -> tuple[str, str | None]:
    order = ParseDict(values, message(transport.proto, "ProtoOANewOrderReq"))
    envelope = message(transport.proto, "ProtoMessage")
    envelope.payloadType = order.payloadType
    envelope.payload = order.SerializeToString()
    envelope.clientMsgId = "s27-scope"
    frame = encode_framed_payload(envelope.SerializeToString())
    if is_refusal(frame):
        raise ValueError("could not frame the order request")
    transport.writer.write(frame.value)
    await transport.writer.drain()
    async with asyncio.timeout(ORDER_WAIT_S):
        return await answer(transport)


async def attempt(target: Target, symbol: str) -> tuple[str, str | None]:
    connection = target.connection
    if not connection.protocol_path or connection.protocol_tag is None:
        raise ValueError("set protocol_path and protocol_tag for this connection")
    compiled = compile_descriptor_set(
        Path(connection.protocol_path).read_bytes(),
        package_name="openapi-proto-messages",
        release_tag=connection.protocol_tag,
    )
    if is_refusal(compiled):
        raise ValueError("invalid cTrader protocol definitions")
    secret = credentials(target.credential)
    transport = await CTraderTransport.connect(compiled.value, "demo")
    try:
        adapter = CTraderAdapter(target.account, transport.request, transport.spot)
        await adapter.authenticate(connection, secret)
        info = await adapter.symbol_info(symbol)
        if "minVolume" not in info:
            raise ValueError(f"{symbol} reports no minimum volume")
        return await send_order(
            transport,
            {
                "ctidTraderAccountId": int(target.account.id),
                "symbolId": int(info["symbolId"]),
                "orderType": "MARKET",
                "tradeSide": "BUY",
                "volume": int(info["minVolume"]),
            },
        )
    finally:
        await transport.close()


def record(home: QmxHome, target: Target, symbol: str, scope_codes: set[str], log: Log) -> None:
    facts = {"account_id": target.account.id, "broker": target.broker.id, "symbol": symbol}
    try:
        name, code = asyncio.run(attempt(target, symbol))
    except Exception as error:
        outcome = f"not tested: the attempt failed ({type(error).__name__})"
        save_scope_proof(
            home.state_dir, target.credential, refused_for_scope=False, outcome=outcome, **facts
        )
        log(f"{target.credential} on demo account {target.account.id}: {outcome}")
        return
    if name == "ProtoOAExecutionEvent":
        refused, outcome = (
            False,
            "the broker accepted the order: it can trade; close the demo position",
        )
    elif code in scope_codes:
        refused, outcome = True, f"refused for scope ({code})"
    else:
        refused, outcome = False, f"refused, not for scope ({name} {code})"
    save_scope_proof(
        home.state_dir,
        target.credential,
        refused_for_scope=refused,
        outcome=outcome,
        error_code=code,
        **facts,
    )
    log(f"{target.credential} on demo account {target.account.id}: {outcome}")


def main() -> int:
    parser = argparse.ArgumentParser(prog="s27_broker_scope.py")
    parser.add_argument("--account", action="append", required=True)
    parser.add_argument("--home", type=Path, default=SHIP_HOME)
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--scope-code", action="append", default=[])
    args = parser.parse_args()
    log = Log("hp14-s27")
    home = QmxHome(args.home)
    control = control_service(home)
    try:
        settings = BrokerSettings.model_validate(control.settings_get("brokers"))
        targets = demo_targets(settings, args.account)
    except Refused as refusal:
        log.check("every account id is a listed demo account", False, str(refusal))
        return log.verdict()
    log.check("every account id is a listed demo account", True, args.account)
    scope_codes = set(args.scope_code) or {"ACCESS_DENIED"}
    inventory, non_broker = broker_inventory(control)
    entries = sorted(inventory - non_broker - {UNLISTED})
    log(f"broker credentials in the inventory: {entries}")
    for target in targets:
        record(home, target, args.symbol, scope_codes, log)
    tested = {target.credential for target in targets}
    for entry in entries:
        if entry not in tested and not proof_path(home.state_dir, entry).exists():
            save_scope_proof(
                home.state_dir,
                entry,
                refused_for_scope=False,
                outcome="not tested: no demo account given uses this entry",
            )
            log(f"{entry}: not tested: no demo account given uses this entry")
    stored = [entry for entry in entries if proof_path(home.state_dir, entry).exists()]
    log.check("each broker credential has a stored result", stored == entries, stored)
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
