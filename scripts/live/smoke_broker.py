"""Operator-only demo broker reads; no order submission or model calls."""

import argparse
import asyncio
import json
from pathlib import Path

from qmx_broker.service import BrokerService


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home() / ".qmx")
    parser.add_argument("--broker", required=True)
    parser.add_argument("--connection", required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--symbol", required=True)
    args = parser.parse_args()
    service = BrokerService(args.home)
    _, connection, _ = service.configured_settings().resolve(
        args.broker, args.connection, args.account
    )
    if connection.environment != "demo":
        raise ValueError("This smoke script only connects to demo accounts")
    for operation in ("account_state", "positions", "symbol_info", "quotes"):
        values = {"symbol": args.symbol} if operation in {"symbol_info", "quotes"} else {}
        result = await service.read(operation, args.broker, args.connection, args.account, **values)
        print(json.dumps({"operation": operation, "result": result}))


if __name__ == "__main__":
    asyncio.run(main())
