"""The typed domain functions behind the MCP doors and the agent tools."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Final, cast

from qmb.results.interpret import compare_runs
from qmf.core import Instant
from qml.door import explain, new
from qmn.doors.api import read_status
from qmx_control.catalog import BLOCKS_LATER
from qmx_control.library import OPERATOR
from qmx_library.kinds import KindRefused
from qmx_library.port import Draft
from qmx_library.principal import MAIN, drafts_ref

from qmx_tools.gather import DUMMY, TEMPLATES, gather
from qmx_tools.gather import template as template_document
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
from qmx_tools.unit_check import checked

if TYPE_CHECKING:
    from qmx_library.port import JsonObject, ObjectId, ObjectView

UNIT_KIND: Final = "unit"


def domain_functions(ctx: DomainContext) -> dict[str, dict[str, Callable[..., dict[str, Any]]]]:
    def list_instruments(
        limit: int = 50, cursor: int = 0, response_format: ResponseFormat = "concise"
    ) -> dict[str, Any]:
        """List the series this host holds. Continue with next_cursor."""
        if ctx.market is None:
            raise ValueError(
                "No market-data door on this host; the data tools need the host's door (Lib AD-28)"
            )
        rows = [
            {"symbol": row.subject, "timeframe": row.kind, "series": row.series}
            for row in unwrap(ctx.market.instruments())
        ]
        return ctx.page(
            rows, Page(limit=limit, cursor=cursor, response_format=response_format), "instruments"
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
        content: Any = artifact.content
        if not isinstance(content, dict) or not {
            "data_points_processed",
            "filled",
            "stream_order",
            "slices",
        }.issubset(cast("dict[str, Any]", content)):
            raise ValueError("Invalid backtest content; use the run_id returned by run_backtest")
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
        if not isinstance(first, dict) or not isinstance(second, dict):
            raise ValueError("Select backtest or CT-32 object artifacts with library_search")
        first = cast("dict[str, Any]", first)
        second = cast("dict[str, Any]", second)
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
        request = Page(limit=limit, cursor=cursor, response_format=response_format)
        found = ctx.library.search(query, offset=request.cursor, limit=request.limit + 1)
        rows = [
            {"ref": item["ref"], "name": item["title"], "kind": item["kind"]}
            for item in found[:limit]
        ]
        return {
            **ctx.output(rows, "library", response_format),
            "next_cursor": cursor + limit if len(found) > limit else None,
            "total": ctx.library.count(query),
        }

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
        "unit": unit_functions(ctx),
        "blocks": {
            "blocks_find": blocks_find,
            "blocks_get": blocks_get,
            "blocks_check": blocks_check,
            "blocks_match": blocks_match,
        },
    }


def _templates() -> list[str]:
    return sorted(p.name.removesuffix(".json") for p in TEMPLATES.iterdir() if p.is_file())


def unit_functions(ctx: DomainContext) -> dict[str, Callable[..., dict[str, Any]]]:
    """The `unit` rows (Part A AD-117). They write `unit` drafts on an item's draft ref and
    nothing else: no `bot` or `strategy`, nothing on `main`, no test, no order."""

    def put(item: str, document: dict[str, Any], title: str, head: ObjectId | None) -> str:
        draft = Draft(UNIT_KIND, item, title, fields=cast("JsonObject", document))
        return ctx.library.store.put(
            OPERATOR, draft, on=drafts_ref(item), expected_head=head
        ).object_id

    def draft(item: str) -> ObjectView:
        store = ctx.library.store
        head = store.head(item, drafts_ref(item)) or store.head(item, MAIN)
        view = None if head is None else store.get(OPERATOR, head[0])
        if view is None or view.kind != UNIT_KIND:
            raise ValueError(
                f"{item!r} names no unit in the Library; start one with unit_new and pass the "
                "item it returns"
            )
        return view

    def unit_new(
        template: str = DUMMY, overrides: dict[str, Any] | None = None, title: str | None = None
    ) -> dict[str, Any]:
        """Start a unit from a template and save it as a new unit draft."""
        if template not in _templates():
            raise ValueError(f"no template {template!r}; the templates are {_templates()}")
        made = new(template_document(template), overrides)
        if isinstance(made, tuple):
            raise ValueError("; ".join(f"{p.where[0]}: {p.message}" for p in made))
        item = str(uuid.uuid7())
        name = title or str(made.get("title") or made.get("unit_id") or template)
        try:
            object_id = put(item, made, name, None)
        except KindRefused as refused:
            raise ValueError(
                "the document does not save as a unit: "
                + "; ".join(f"{p.where[0]}: {p.message}" for p in refused.problems)
            ) from refused
        return {"item": item, "object_id": object_id, "document": made}

    def unit_check(
        document: dict[str, Any],
        item: str | None = None,
        previous_problem_set: str | None = None,
    ) -> dict[str, Any]:
        """Check a unit at layers A to F, every problem at once; save it as `item`'s draft first."""
        saved: dict[str, Any] | None = None
        if item is not None:
            before = draft(item)
            head = ctx.library.store.head(item, drafts_ref(item))
            try:
                saved = {
                    "object_id": put(
                        item, document, before.title, None if head is None else head[0]
                    ),
                    "refused": [],
                }
            except KindRefused as refused:
                saved = {"object_id": None, "refused": [p.as_json() for p in refused.problems]}
        return {**checked(ctx.library.store, document, previous_problem_set), "saved": saved}

    def unit_explain(
        document: dict[str, Any] | None = None, item: str | None = None
    ) -> dict[str, Any]:
        """Explain a unit in plain lines, from a document or a unit in the Library."""
        if (document is None) == (item is None):
            raise ValueError("pass a document or the item of a unit in the Library, not both")
        given: object = document if document is not None else draft(str(item)).fields
        found = gather(ctx.library.store, given)
        return {"lines": list(explain(given, found.context)), "notes": list(found.warnings)}

    return {"unit_new": unit_new, "unit_check": unit_check, "unit_explain": unit_explain}


def _not_built(row: str) -> ValueError:
    return ValueError(f"{row}: {BLOCKS_LATER}")


def blocks_find(words: str, limit: int = 50) -> dict[str, Any]:
    """Find dictionary blocks by words. Arrives with the dictionary's new form (A11)."""
    raise _not_built("blocks_find")


def blocks_get(entry_id: str, version: str | None = None) -> dict[str, Any]:
    """Read one dictionary entry in full. Arrives with the dictionary's new form (A11)."""
    raise _not_built("blocks_get")


def blocks_check(entry: dict[str, Any], source: str) -> dict[str, Any]:
    """Check a block draft and its source. Arrives with the dictionary's new form (A11)."""
    raise _not_built("blocks_check")


def blocks_match(text: str) -> dict[str, Any]:
    """Match each sentence to an entry. Arrives with the dictionary's new form (A11)."""
    raise _not_built("blocks_match")
