"""Wrap the domain functions as LangChain tools."""

from __future__ import annotations

from langchain_core.tools import BaseTool, tool

from qmx_tools.functions import domain_functions
from qmx_tools.service import DomainContext


def default_tool_registry(ctx: DomainContext | None = None) -> dict[str, BaseTool]:
    """Resolve only the thirteen domain capabilities; hosts may inject their engine context."""
    ctx = ctx or DomainContext.from_environment()
    return {
        f"qmx-{server}.{name}": tool(f"qmx_{server}_{name}")(function)
        for server, functions in domain_functions(ctx).items()
        for name, function in functions.items()
    }
