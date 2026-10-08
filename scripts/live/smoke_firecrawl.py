"""Operator-only Firecrawl discovery; --url also consumes scrape credits."""

from __future__ import annotations

import argparse
import asyncio

from fastmcp import Client
from qmx_agents.router import FIRECRAWL_SERVER, credential


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Optionally scrape one URL using paid provider credits")
    args = parser.parse_args()
    async with Client(FIRECRAWL_SERVER["url"], auth=credential("firecrawl")) as client:
        names = [tool.name for tool in await client.list_tools()]
        print("Available tools:", ", ".join(names))
        if "firecrawl_scrape" not in names:
            raise RuntimeError("The authenticated provider did not expose firecrawl_scrape.")
        if args.url:
            print((await client.call_tool("firecrawl_scrape", {"url": args.url})).data)


if __name__ == "__main__":
    asyncio.run(main())
