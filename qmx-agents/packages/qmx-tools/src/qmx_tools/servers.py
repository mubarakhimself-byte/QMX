"""Four stdio doors over the same domain functions used by agents.

Whether a function writes comes from its catalog row (`qmx_control.catalog.DOMAIN_ROWS`, by
target). `library_save` and `propose_order` have no row, because the library toolset and the
broker serve agents the same stores; they stay stdio doors here and are marked as writes.
"""

from typing import Final

from fastmcp import FastMCP
from qmx_control.catalog import DOMAIN_ROWS

from qmx_tools.functions import domain_functions
from qmx_tools.service import DomainContext

WRITES: Final = frozenset(
    {row.target for row in DOMAIN_ROWS if row.approval != "read"}
    | {"library_save", "propose_order"}
)


def create_server(name: str, ctx: DomainContext | None = None) -> FastMCP:
    server = FastMCP(f"qmx-{name}")
    for tool_name, function in domain_functions(ctx or DomainContext.from_environment())[
        name
    ].items():
        server.tool(
            name=tool_name,
            annotations={
                "readOnlyHint": tool_name not in WRITES,
                "destructiveHint": False,
                "openWorldHint": False,
            },
        )(function)
    return server


def data() -> None:
    create_server("data").run()


def backtest() -> None:
    create_server("backtest").run()


def research() -> None:
    create_server("research").run()


def node() -> None:
    create_server("node").run()
