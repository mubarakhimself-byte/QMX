"""Build the same typed functions for LangChain and FastMCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.tools import BaseTool, tool
from qmb.results.interpret import compare_runs
from qmf.core import Instant
from qmn.doors.api import read_status

from qmx_tools.service import (
    Artifact,
    BacktestSpec,
    DomainContext,
    OrderProposal,
    Page,
    ResponseFormat,
    SeriesRequest,
    json_value,
    unwrap,
)


def domain_functions(ctx: DomainContext) -> dict[str, dict[str, Callable[..., dict[str, Any]]]]:
    def list_instruments(
        limit: int = 50, cursor: int = 0, response_format: ResponseFormat = "concise"
    ) -> dict[str, Any]:
        """List recorded instrument/timeframe pairs. Continue with next_cursor."""
        rows = sorted({(item.symbol, item.timeframe) for item in ctx.datasets})
        return ctx.page(
            [{"symbol": symbol, "timeframe": frame} for symbol, frame in rows],
            Page(limit=limit, cursor=cursor, response_format=response_format),
            "instruments",
        )

    def read_bars(
        symbol: str,
        timeframe: str,
        start: int | None = None,
        end: int | None = None,
        limit: int = 50,
        cursor: int = 0,
        response_format: ResponseFormat = "concise",
    ) -> dict[str, Any]:
        """Read recorded bars in an inclusive nanosecond window; QMF seal rules apply."""
        return ctx.read(
            "bars",
            SeriesRequest(
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                limit=limit,
                cursor=cursor,
                response_format=response_format,
            ),
        )

    def read_features(
        symbol: str,
        timeframe: str,
        start: int | None = None,
        end: int | None = None,
        limit: int = 50,
        cursor: int = 0,
        response_format: ResponseFormat = "concise",
    ) -> dict[str, Any]:
        """Read recorded features without recalculating or fetching live data."""
        return ctx.read(
            "features",
            SeriesRequest(
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                limit=limit,
                cursor=cursor,
                response_format=response_format,
            ),
        )

    def calendar(
        symbol: str,
        timeframe: str,
        start: int | None = None,
        end: int | None = None,
        limit: int = 50,
        cursor: int = 0,
        response_format: ResponseFormat = "concise",
    ) -> dict[str, Any]:
        """Read the recorded calendar for an instrument; missing coverage is an error."""
        return ctx.read(
            "calendar",
            SeriesRequest(
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                limit=limit,
                cursor=cursor,
                response_format=response_format,
            ),
        )

    def run_backtest(
        spec: BacktestSpec, response_format: ResponseFormat = "concise"
    ) -> dict[str, Any]:
        """Run a host-registered strategy on recorded slices and return a durable result ref."""
        return ctx.run_backtest(BacktestSpec.model_validate(spec), response_format)

    def backtest_status(run_id: str, response_format: ResponseFormat = "concise") -> dict[str, Any]:
        """Read a persisted run's status. This synchronous door returns completed runs."""
        artifact = ctx.artifact(run_id)
        if artifact.kind != "backtest":
            raise ValueError("Use the run_id returned by run_backtest; this ref is not a backtest")
        return ctx.output(
            {"run_id": run_id, "name": artifact.name, "status": "completed"},
            "status",
            response_format,
        )

    def backtest_results(
        run_id: str, response_format: ResponseFormat = "concise", limit: int = 50, cursor: int = 0
    ) -> dict[str, Any]:
        """Read a backtest summary or paginate slices; large pages become artifacts."""
        backtest_status(run_id)
        content = ctx.artifact(run_id).content
        if response_format == "concise":
            return ctx.output(
                {key: content[key] for key in ("data_points_processed", "filled", "stream_order")},
                "results",
                response_format,
            )
        return ctx.page(
            content["slices"],
            Page(limit=limit, cursor=cursor, response_format=response_format),
            "results",
        )

    def compare_runs_tool(
        left: str,
        right: str,
        limit: int = 50,
        cursor: int = 0,
        response_format: ResponseFormat = "concise",
    ) -> dict[str, Any]:
        """Compare stored CT-32 artifacts field by field using QMB, without interpreting HTML."""
        first = ctx.artifact(left).content
        second = ctx.artifact(right).content
        comparison = unwrap(
            compare_runs(
                first.get("performance_result", first), second.get("performance_result", second)
            )
        )
        return ctx.page(
            json_value(comparison.differing),
            Page(limit=limit, cursor=cursor, response_format=response_format),
            "comparison",
        )

    def qml_run(
        bot_ref: str,
        instants: list[int],
        limit: int = 50,
        cursor: int = 0,
        response_format: ResponseFormat = "concise",
    ) -> dict[str, Any]:
        """Evaluate a host-registered QML bot on recorded instants; return intents, never orders."""
        request = Page(limit=limit, cursor=cursor, response_format=response_format)
        bot = ctx.bots.get(bot_ref)
        if bot is None:
            raise ValueError(
                "Unknown bot_ref; ask the host to register a QML HostedBot with recorded surfaces"
            )
        selected = instants[cursor : cursor + limit]
        rows = [
            {
                "instant": value,
                "intents": json_value(unwrap(bot.on_instant(unwrap(Instant.try_create(value))))),
            }
            for value in selected
        ]
        return {
            **ctx.page(rows, request.model_copy(update={"cursor": 0}), "qml"),
            "next_cursor": cursor + limit if cursor + limit < len(instants) else None,
            "total": len(instants),
        }

    def library_search(
        query: str = "",
        limit: int = 50,
        cursor: int = 0,
        response_format: ResponseFormat = "concise",
    ) -> dict[str, Any]:
        """Find saved artifacts by name/kind and paginate their references."""
        rows: list[dict[str, Any]] = []
        for path in sorted((ctx.root / "artifacts").glob("*.json")):
            ref = f"artifacts/{path.name}"
            artifact = ctx.artifact(ref)
            if query.casefold() in f"{artifact.name} {artifact.kind}".casefold():
                rows.append({"ref": ref, "name": artifact.name, "kind": artifact.kind})
        return ctx.page(
            rows, Page(limit=limit, cursor=cursor, response_format=response_format), "library"
        )

    def library_save(
        artifact: Artifact, response_format: ResponseFormat = "concise"
    ) -> dict[str, Any]:
        """Save named content as an immutable artifact and return its reference."""
        return ctx.output(ctx.save(Artifact.model_validate(artifact)), "saved", response_format)

    def node_state(response_format: ResponseFormat = "concise") -> dict[str, Any]:
        """Read QMN lifecycle and provenance. No trading or node-control powers are exposed."""
        if ctx.node is None:
            raise ValueError("No node configured; inject the host's QMN DoorRuntime")
        return ctx.output(unwrap(read_status(ctx.node)), "node", response_format)

    def propose_order(
        proposal: OrderProposal, response_format: ResponseFormat = "concise"
    ) -> dict[str, Any]:
        """Stage an order proposal for review; saving cannot submit or authorize an order."""
        proposal = OrderProposal.model_validate(proposal)
        saved = ctx.save(
            Artifact(
                name=f"{proposal.side} {proposal.symbol}",
                kind="order-proposal",
                content=proposal.model_dump(mode="json"),
            )
        )
        return ctx.output(
            {"proposal": saved, "status": "awaiting_operator_signature", "executed": False},
            "proposal",
            response_format,
        )

    return {
        "data": {
            "list_instruments": list_instruments,
            "read_bars": read_bars,
            "read_features": read_features,
            "calendar": calendar,
        },
        "backtest": {
            "run_backtest": run_backtest,
            "backtest_status": backtest_status,
            "backtest_results": backtest_results,
            "compare_runs": compare_runs_tool,
        },
        "research": {
            "qml_run": qml_run,
            "library_search": library_search,
            "library_save": library_save,
        },
        "node": {"node_state": node_state, "propose_order": propose_order},
    }


def default_tool_registry(ctx: DomainContext | None = None) -> dict[str, BaseTool]:
    """Resolve only the thirteen domain capabilities; hosts may inject their engine context."""
    ctx = ctx or DomainContext.from_environment()
    return {
        f"qmx-{server}.{name}": tool(f"qmx_{server}_{name}")(function)
        for server, functions in domain_functions(ctx).items()
        for name, function in functions.items()
    }
