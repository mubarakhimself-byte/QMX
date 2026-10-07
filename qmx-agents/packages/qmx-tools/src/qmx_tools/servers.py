"""Four stdio doors over the same domain functions used by agents."""

from fastmcp import FastMCP

from qmx_tools.registry import domain_functions
from qmx_tools.service import DomainContext


def create_server(name: str, ctx: DomainContext | None = None) -> FastMCP:
    server = FastMCP(f"qmx-{name}")
    for tool_name, function in domain_functions(ctx or DomainContext.from_environment())[
        name
    ].items():
        server.tool(
            name=tool_name,
            annotations={
                "readOnlyHint": tool_name not in {"run_backtest", "library_save", "propose_order"},
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
