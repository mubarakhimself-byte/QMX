"""The typed domain functions behind the MCP doors and the agent tools."""

from __future__ import annotations

import difflib
import importlib.metadata
import json
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Literal, cast

import qml
from qmf.core import Instant, fingerprint, is_refusal
from qmf.data.journal_writer import key_token
from qmf.data.series import STATE_NAME, SeriesKey, SeriesStore
from qml.catalogue.entry import ENTRY_SCHEMA, Computed, compute_status, corpus_problems
from qml.catalogue.index import find as find_rows
from qml.catalogue.index import match as match_text
from qml.catalogue.index import row as index_row
from qml.catalogue.loader import block_fingerprint
from qml.catalogue.roles import NEAREST_SUGGESTIONS
from qml.door import explain, new
from qmx_control.library import OPERATOR
from qmx_judge.judge import (
    STUDY_KIND,
    JudgedResult,
    JudgeRefused,
    judge,
    land_judgement,
    parse_spec,
    quick_spec,
)
from qmx_judge.landing import REPORT_SLOT, RESULT_KIND, Stored
from qmx_judge.tries import TRY_KIND, try_item
from qmx_library.kinds import KindRefused
from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import MAIN, drafts_ref, state_ref

from qmx_tools import journals
from qmx_tools.gather import DUMMY, STDLIB, TEMPLATES, entry_face, gather
from qmx_tools.gather import template as template_document
from qmx_tools.service import (
    Artifact,
    DomainContext,
    MarketPort,
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
    from qmx_library.store import Store

UNIT_KIND: Final = "unit"
NO_NODE: Final = "no trading node is set up yet"
REPO: Final = Path(qml.__file__).resolve().parents[3]
COMPARED_REQUEST: Final = ("unit", "compiled_fp", "markets", "window", "seed", "motion", "study")
"""The result fields that make two runs one request, whatever tester ran them."""


type Opening = tuple[str, int, int, str]
"""A trade's pairing key: market, opening instant, its order among the trades the result opened
on that market at that instant, and the trade id of a row landed before B6."""


def _opened_at(result_id: str, n: int, trade: dict[str, Any]) -> int:
    value = trade.get("opened_at", 0)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and value.isascii() and value.isdigit():
        return int(value)
    raise ValueError(
        f"{result_id}: trade {n} opens at {value!r}, not a whole number of nanoseconds"
    )


def _by_opening(result_id: str, trades: list[dict[str, Any]]) -> dict[Opening, dict[str, Any]]:
    """A result's trades by market and opening instant, since a unit holds one position per
    market, then by their order, so two trades opened together never merge. A row with no
    opening instant, landed before B6, pairs by its trade id."""
    rows: dict[Opening, dict[str, Any]] = {}
    seen: dict[tuple[str, int, str], int] = {}
    for n, trade in enumerate(trades):
        market, at = str(trade.get("market_id")), _opened_at(result_id, n, trade)
        legacy = "" if "opened_at" in trade else str(trade.get("trade_id"))
        order = seen.get((market, at, legacy), 0)
        seen[market, at, legacy] = order + 1
        rows[market, at, order, legacy] = trade
    return rows


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

    def backtest_run(
        unit: str,
        window: dict[str, str],
        markets: list[str] | None = None,
        study: str | None = None,
        compiled_fp: str | None = None,
        seed: int | None = None,
        motion: Literal["on", "off"] = "on",
        allow_gaps: bool | None = None,
        response_format: ResponseFormat = "concise",
    ) -> dict[str, Any]:
        """Backtest a unit on QMB over `window` (`{"start": "2025-03-01", "end": "2025-04-01"}`)
        and land its result in the Library. Answers the run id, and the result id when it
        finished within the wait; otherwise read it later with backtest_status. A hole in the
        bars longer than `[qmb] gap_bars_refuse` fails the run unless `allow_gaps` is true;
        left out, the study's `allow_gaps` decides."""
        asked = {
            "unit": unit,
            "window": window,
            "markets": markets,
            "study": study,
            "compiled_fp": compiled_fp,
            "seed": seed,
            "motion": motion,
            "allow_gaps": allow_gaps,
        }
        request = {name: value for name, value in asked.items() if value is not None}
        return ctx.backtest(request, response_format)

    def backtest_status(run_id: str, response_format: ResponseFormat = "concise") -> dict[str, Any]:
        """Read a run's state from its try rows: running, landed or failed, and its result id."""
        store = ctx.library.store
        opened = store.head(try_item(run_id, "opened"), MAIN)
        if opened is None:
            raise ValueError(f"no run {run_id}; pass the run_id backtest_run answered")
        first = store.get(OPERATOR, opened[0]).fields
        closed = store.head(try_item(run_id, "landed"), MAIN)
        last = None if closed is None else store.get(OPERATOR, closed[0]).fields
        links = cast("list[str]", (last or {}).get("links") or [])
        return ctx.output(
            {
                "run_id": run_id,
                "state": "running" if last is None else last["state"],
                "kind": first.get("kind"),
                "tester": first.get("tester"),
                "principal": first.get("principal"),
                "place": first.get("place"),
                "result_id": links[1] if len(links) > 1 else None,
            },
            "status",
            response_format,
        )

    def _result(result_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        store = ctx.library.store
        try:
            view = store.get(OPERATOR, result_id)
        except LibraryRefused as error:
            raise ValueError(f"{result_id}: {error}") from error
        if view.kind != RESULT_KIND:
            raise ValueError(f"{result_id} is a {view.kind}; pass the result_id of a backtest")
        report = view.blobs.get(REPORT_SLOT)
        body = cast(
            "dict[str, Any]", {} if report is None else json.loads(store.read_blob(report.blob_id))
        )
        return dict(view.fields), cast("list[dict[str, Any]]", body.get("trades", []))

    def backtest_results(
        result_id: str,
        response_format: ResponseFormat = "concise",
        limit: int = 50,
        cursor: int = 0,
    ) -> dict[str, Any]:
        """Read a landed result: status, measures in money and R, labels, and a page of trades."""
        fields, trades = _result(result_id)
        summary = {
            name: fields.get(name)
            for name in ("run_id", "status", "reason", "measures", "labels", "principal", "tester")
        }
        page = ctx.page(
            trades, Page(limit=limit, cursor=cursor, response_format=response_format), "trades"
        )
        return {**page, "summary": summary}

    def backtest_compare(
        left: str,
        right: str,
        limit: int = 50,
        cursor: int = 0,
        response_format: ResponseFormat = "concise",
    ) -> dict[str, Any]:
        """Compare two landed results trade by trade (the parity diff): each trade only one made,
        each trade both made whose prices, size, money or R differ, and the measures that
        differ. Trades pair by market, opening time and their order among trades opened on
        that market at that time, so two testers' names never matter."""
        (first, mine), (second, theirs) = _result(left), _result(right)
        ours, other = _by_opening(left, mine), _by_opening(right, theirs)
        rows: list[dict[str, Any]] = []
        for key in sorted(ours.keys() | other.keys(), key=lambda k: (k[1], k[0], k[2], k[3])):
            a, b = ours.get(key), other.get(key)
            trade = {"market_id": key[0], "opened_at": key[1], "order": key[2]}
            if a is None or b is None:
                rows.append({**trade, "only": "right" if a is None else "left", "row": a or b})
                continue
            differs = {
                name: [a.get(name), b.get(name)]
                for name in sorted((a.keys() | b.keys()) - {"trade_id"})
                if a.get(name) != b.get(name)
            }
            if differs:
                rows.append({**trade, "differs": differs})
        a_measures = cast("dict[str, Any]", first.get("measures") or {})
        b_measures = cast("dict[str, Any]", second.get("measures") or {})
        measures = {
            key: [a_measures.get(key), b_measures.get(key)]
            for key in sorted(a_measures.keys() | b_measures.keys())
            if a_measures.get(key) != b_measures.get(key)
        }
        request = {
            name: [first.get(name), second.get(name)]
            for name in COMPARED_REQUEST
            if first.get(name) != second.get(name)
        }
        page = ctx.page(
            rows, Page(limit=limit, cursor=cursor, response_format=response_format), "comparison"
        )
        return {
            **page,
            "testers": [first.get("tester"), second.get("tester")],
            "statuses": [first.get("status"), second.get("status")],
            "same_request": not request,
            "request_differs": request,
            "same_trades": not rows,
            "measures": measures,
        }

    def backtest_judge_run(
        results: list[str], study: str | None = None, response_format: ResponseFormat = "concise"
    ) -> dict[str, Any]:
        """Judge landed results with the core's referee and land the verdict. Answers the
        verdict in plain words, with the raw and effective tries behind it."""
        store = ctx.library.store
        judged = [_judged(store, result_id) for result_id in results]
        pin, spec_fields = _study(store, study, judged)
        tries = _tries(store, judged)
        family = [
            found
            for result_id in sorted(_landed_results(tries) - set(results))
            if (found := _judged(store, result_id)).status == "finished"
        ]
        principal = ctx.control._caller()  # pyright: ignore[reportPrivateUsage]
        try:
            spec = parse_spec(spec_fields)
            verdict = judge(
                spec,
                study=pin,
                results=judged,
                tries=tries,
                family=family,
                principal=principal,
                versions={"checker": f"qml {importlib.metadata.version('qml')}"},
            )
            landed = land_judgement(
                _JudgeLibrary(store), verdict, results=judged, spec=spec, writer=str(OPERATOR)
            )
        except JudgeRefused as refused:
            raise ValueError("; ".join(refused.problems)) from refused
        return ctx.output(
            {
                "verdict_id": landed.verdict,
                "overall": verdict.overall,
                "says": verdict.says(),
                "raw_tries": verdict.raw_tries,
                "effective_tries": verdict.effective_tries,
                "study": pin,
                "cards": dict(landed.cards),
                "per_market": [
                    {"market": m.market, "outcome": m.outcome, "trades": m.trades}
                    for m in verdict.per_market
                ],
            },
            "verdict",
            response_format,
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

    def journal_query(
        stream: Literal["unit", "market", "node"],
        window: dict[str, str | int],
        filters: dict[str, str] | None = None,
        view: Literal["rows", "trades_with_context", "digest"] = "rows",
        include_backfilled: bool = False,
        limit: int = 50,
        cursor: int = 0,
        response_format: ResponseFormat = "concise",
    ) -> dict[str, Any]:
        """Read one journal stream (unit, market or node) over a required time window:
        {"start": "2025-01-02T07:00:00Z", "end": "2025-01-02T09:00:00Z"}, UTC. Filter by any
        envelope field (unit_id, market_id, kind, world, account, machine, ...). View `rows`,
        `trades_with_context` (each signal and trade with its market's minute, spread included),
        or `digest` (counts per unit, market and day). Past the data it says where the data
        stops; backfilled rows are left out unless include_backfilled. Reading history is
        read with readings_query, which keeps the study's holdout."""
        answer = journals.journal_query(
            ctx.root,
            stream=stream,
            window=window,
            filters=filters,
            view=view,
            include_backfilled=include_backfilled,
            detailed=response_format == "detailed",
        )
        rows = cast("list[Any]", answer.pop("rows"))
        paged = ctx.page(
            rows, Page(limit=limit, cursor=cursor, response_format=response_format), "journal"
        )
        return {**answer, **paged}

    def notes_write(
        title: str,
        text: str,
        note_kind: Literal["analysis", "proposal", "lesson", "forecast_ref", "disagreement"],
        receipts: list[str] | None = None,
        about: list[dict[str, str]] | None = None,
        window: dict[str, str] | None = None,
        sources_marked: list[str] | None = None,
        expires: str | None = None,
        author: str = "agent",
        response_format: ResponseFormat = "concise",
    ) -> dict[str, Any]:
        """Write an agent's analysis as a Library `note`, the only thing an agent writes from
        journals. Cite every number by the tool call it came from in `receipts`; `about` links
        what it is about ({"rel": "about", "ref": a Library id or a journal record id}); mark
        outside sources in `sources_marked`. A note is never a journal row and moves nothing."""
        draft = journals.note_draft(
            title=title,
            text=text,
            note_kind=note_kind,
            about=about or (),
            receipts=receipts or (),
            window=window,
            sources_marked=sources_marked or (),
            expires=expires,
            author=author,
        )
        try:
            landed = ctx.library.store.put(OPERATOR, draft, on=MAIN, expected_head=None)
        except (LibraryRefused, KindRefused) as error:
            raise ValueError(f"the note did not land: {error}") from error
        return ctx.output({"note": landed.object_id, "item": landed.item}, "note", response_format)

    def node_read(
        operation: str, arguments: dict[str, Any], response_format: ResponseFormat
    ) -> dict[str, Any]:
        """One of the trading node's reads through the host's node link (Part C AD-303)."""
        found = None if ctx.node is None else ctx.node.node_read(operation, arguments)
        if found is None:
            found = {"set_up": False, "message": NO_NODE}
        return ctx.output(found, "node", response_format)

    def node_state(response_format: ResponseFormat = "concise") -> dict[str, Any]:
        """Read the trading node's state. No trading or node-control powers are exposed."""
        return node_read("status", {}, response_format)

    def node_units(
        deployment_id: str | None = None, response_format: ResponseFormat = "concise"
    ) -> dict[str, Any]:
        """Read the trading node's units, or one deployment's."""
        given = {} if deployment_id is None else {"deployment_id": deployment_id}
        return node_read("units", given, response_format)

    def node_positions(
        account: str | None = None, response_format: ResponseFormat = "concise"
    ) -> dict[str, Any]:
        """Read the trading node's open positions, or one account's."""
        return node_read(
            "positions", {} if account is None else {"account": account}, response_format
        )

    def node_journal_tail(
        after_sequence: int = 0,
        streams: list[str] | None = None,
        response_format: ResponseFormat = "concise",
    ) -> dict[str, Any]:
        """Read the trading node's journal rows after a sequence."""
        given: dict[str, Any] = {"after_sequence": after_sequence}
        if streams is not None:
            given["streams"] = streams
        return node_read("journal_tail", given, response_format)

    def node_passport(response_format: ResponseFormat = "concise") -> dict[str, Any]:
        """Read the trading node's passport."""
        return node_read("passport", {}, response_format)

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
            "backtest_run": backtest_run,
            "backtest_status": backtest_status,
            "backtest_results": backtest_results,
            "backtest_compare": backtest_compare,
            "backtest_judge_run": backtest_judge_run,
        },
        "research": {
            "qml_run": qml_run,
            "library_search": library_search,
            "library_save": library_save,
            "journal_query": journal_query,
            "notes_write": notes_write,
        },
        "node": {
            "node_state": node_state,
            "node_units": node_units,
            "node_positions": node_positions,
            "node_journal_tail": node_journal_tail,
            "node_passport": node_passport,
            "propose_order": propose_order,
        },
        "unit": unit_functions(ctx),
        "blocks": block_functions(ctx),
        "instrument": {"instrument_get": instrument_functions(ctx)},
        "readings": {"readings_query": readings_functions(ctx)},
    }


class _JudgeLibrary:
    """The judge's Library port over this home's store: records onto `main` as the operator,
    each item found before it is written, each edge kept once by the store."""

    def __init__(self, store: Store) -> None:
        self.store = store

    def find(self, item: str) -> str | None:
        head = self.store.head(item, MAIN)
        return None if head is None else head[0]

    def put(
        self,
        kind: str,
        fields: Mapping[str, object],
        blobs: Mapping[str, bytes],
        *,
        item: str | None,
        title: str,
        summary: str,
        principal: str,
    ) -> Stored:
        draft = Draft(kind, item, title, summary, fields=cast("JsonObject", dict(fields)))
        return Stored(self.store.put(OPERATOR, draft, on=MAIN, expected_head=None).object_id)

    def link(self, from_id: str, relation: str, to_id: str, *, principal: str) -> str:
        return self.store.relate(OPERATOR, from_id, relation, to_id)


def _judged(store: Store, result_id: str) -> JudgedResult:
    """A landed result and its report's trades, as the judge reads them."""
    try:
        view = store.get(OPERATOR, result_id)
    except LibraryRefused as error:
        raise ValueError(f"{result_id}: {error}") from error
    if view.kind != RESULT_KIND:
        raise ValueError(f"{result_id} is a {view.kind}; pass the result_id of a backtest")
    report = view.blobs.get(REPORT_SLOT)
    body = cast(
        "dict[str, Any]", {} if report is None else json.loads(store.read_blob(report.blob_id))
    )
    trades = cast("list[dict[str, Any]]", body.get("trades", []))
    needed = {"market_id", "closed_at", "r"}
    unnamed = [str(t.get("trade_id")) for t in trades if not needed <= set(t)]
    if unnamed:
        raise ValueError(f"{result_id}: trade {unnamed[0]} names no market_id, closed_at and r")
    return JudgedResult.read(result_id, view.fields, trades)


def _study(store: Store, study: str | None, judged: list[JudgedResult]) -> tuple[str, JsonObject]:
    """The study the verdict is judged under: the one named, else the results' own, else a quick
    spec over every admitted market, landed once per unit."""
    own = (store.get(OPERATOR, r.result_id).fields.get("study") for r in judged)
    named = study or next((pin for pin in own if isinstance(pin, str)), None)
    if named is not None:
        view = store.get(OPERATOR, named)
        if view.kind != STUDY_KIND:
            raise ValueError(f"{named} is a {view.kind}; pass the id of a study-spec")
        return named, view.fields
    unit = judged[0].unit if judged else ""
    claim = store.get(OPERATOR, unit).fields.get("claim_card") if store.catalog.row(unit) else None
    idea = cast("dict[str, Any]", claim).get("idea") if isinstance(claim, dict) else None
    fields = cast("JsonObject", quick_spec(idea if isinstance(idea, str) else None))
    key = fingerprint({"unit": unit, "spec": fields})
    item = f"study-quick-{unit if is_refusal(key) else key.value.digest[:24]}"
    head = store.head(item, MAIN)
    if head is not None:
        return head[0], fields
    draft = Draft(STUDY_KIND, item, f"quick study of {unit}", fields=fields)
    return store.put(OPERATOR, draft, on=MAIN, expected_head=None).object_id, fields


def _tries(store: Store, judged: list[JudgedResult]) -> list[dict[str, Any]]:
    """Every `try` of the results' families, and each result's own run tries."""
    found: dict[str, dict[str, Any]] = {}
    for result in judged:
        for state in ("opened", "landed"):
            head = store.head(try_item(result.run_id, state), MAIN)
            if head is not None:
                found[head[0]] = dict(store.get(OPERATOR, head[0]).fields)
    families = {str(row["family"]) for row in found.values() if row.get("family")}
    for family in sorted(families):
        for object_id in store.with_field(TRY_KIND, "family", family):
            found[object_id] = dict(store.get(OPERATOR, object_id).fields)
    return list(found.values())


def _landed_results(tries: list[dict[str, Any]]) -> set[str]:
    """The result each landed run links to, after the try it closes. A behaviour check's try
    links its `test-report`, which is no result to judge."""
    linked = (
        cast("list[str]", row.get("links") or [])
        for row in tries
        if row.get("state") == "landed" and row.get("kind") in ("run", "whatif_rerun")
    )
    return {links[1] for links in linked if len(links) > 1}


def _templates() -> list[str]:
    return sorted(p.name.removesuffix(".json") for p in TEMPLATES.iterdir() if p.is_file())


def unit_functions(ctx: DomainContext) -> dict[str, Callable[..., dict[str, Any]]]:
    """The `unit` rows (Part A AD-117). They write `unit` drafts on an item's draft ref and
    nothing else: no `bot` or `strategy`, nothing on `main`, no test, no order."""

    def put(
        item: str,
        document: dict[str, Any],
        title: str,
        head: ObjectId | None,
        parents: list[ObjectId] | None = None,
    ) -> str:
        fields = cast("JsonObject", document)
        draft = Draft(UNIT_KIND, item, title, fields=fields, parents=parents)
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
            # With no draft ref yet, `before` is main's head: the draft descends from it, so his
            # publish fast-forwards instead of conflicting on every changed field.
            parents = [before.object_id] if head is None else None
            try:
                saved = {
                    "object_id": put(
                        item, document, before.title, None if head is None else head[0], parents
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
            raise ValueError("pass exactly one of a document and the item of a unit in the Library")
        given: object = document if document is not None else draft(str(item)).fields
        found = gather(ctx.library.store, given)
        return {"lines": list(explain(given, found.context)), "notes": list(found.warnings)}

    return {"unit_new": unit_new, "unit_check": unit_check, "unit_explain": unit_explain}


@dataclass(frozen=True, slots=True)
class _Held:
    """One entry the doors see: its face, its code, its computed status and where it lives."""

    entry: dict[str, object]
    source: bytes | None
    status: str | None
    held_in: str

    @property
    def pin(self) -> str:
        return f"{self.entry.get('entry_id')}@{self.entry.get('version')}"


def _golden(entry: dict[str, object]) -> object:
    """The golden cases an entry of QML's own names, read from a checkout; None elsewhere."""
    declared = entry.get("golden")
    cases = cast("dict[str, object]", declared).get("cases") if isinstance(declared, dict) else None
    path = REPO / cases if isinstance(cases, str) else None
    return json.loads(path.read_text("utf-8")) if path is not None and path.is_file() else None


@cache
def _qml_entries() -> tuple[_Held, ...]:
    """QML's own blocks, each with the status its evidence earns, computed once per process."""
    held: list[_Held] = []
    for folder in sorted(STDLIB.iterdir(), key=lambda f: f.name):
        for version in sorted(folder.iterdir(), key=lambda f: f.name):
            face, code = version / "entry.json", version / "block.py"
            if not (face.is_file() and code.is_file()):
                continue
            entry = cast("dict[str, object]", json.loads(face.read_text("utf-8")))
            source = code.read_bytes()
            status = compute_status(entry, source, _golden(entry)).status
            held.append(_Held(entry, source, None if status is None else status.value, "qml"))
    return tuple(held)


def _entry_items(store: Store) -> list[str]:
    """Every Library item that ever held an entry marked `qmx.entry/1`."""
    return sorted(
        {
            store.get(store.engine, object_id).item
            for object_id in store.with_field("component", "entry.schema", ENTRY_SCHEMA)
        }
    )


def _library_entries(store: Store) -> list[_Held]:
    """The Library's entries on `main`, each with the status its last status run wrote."""
    held: list[_Held] = []
    for item in _entry_items(store):
        head = store.head(item, MAIN)
        if head is None:
            continue
        view = store.get(store.engine, head[0])
        code = view.blobs.get("code")
        mark = view.annotations.get("status")
        value = cast("dict[str, object]", mark).get("value") if isinstance(mark, dict) else None
        held.append(
            _Held(
                entry_face(view.fields),
                None if code is None else store.read_blob(code.blob_id),
                value if isinstance(value, str) else None,
                item,
            )
        )
    return held


def write_entry_statuses(store: Store) -> list[tuple[str, str, Computed]]:
    """Compute the status of each Library entry at its `main` and draft heads from its code
    and its `golden` blob, and write it on that object as its `status` annotation. Returns
    `(item, ref, computed)` per object, `main` first. Rerunning writes the same values."""
    written: list[tuple[str, str, Computed]] = []
    for item in _entry_items(store):
        seen: set[str] = set()
        for ref in (MAIN, drafts_ref(item)):
            head = store.head(item, ref)
            if head is None or head[0] in seen:
                continue
            seen.add(head[0])
            view = store.get(store.engine, head[0])
            if view.kind != "component":
                continue
            code, golden = view.blobs.get("code"), view.blobs.get("golden")
            computed = compute_status(
                entry_face(view.fields),
                None if code is None else store.read_blob(code.blob_id),
                None if golden is None else json.loads(store.read_blob(golden.blob_id)),
            )
            store.annotate(store.engine, head[0], {"status": json_value(computed.annotation())})
            written.append((item, ref, computed))
    return written


def block_functions(ctx: DomainContext) -> dict[str, Callable[..., dict[str, Any]]]:
    """The `blocks` rows (Part A AD-113, AD-117): the dictionary's doors. They read and check,
    and write nothing; an entry is saved as a `component` item, where the Library's put check
    runs the same entry checker."""

    def catalogue() -> list[_Held]:
        """QML's own entries, then the Library's whose pin QML does not hold, the order in which
        `gather` resolves a pin."""
        own = _qml_entries()
        pins = {h.pin for h in own}
        return [*own, *(h for h in _library_entries(ctx.library.store) if h.pin not in pins)]

    def blocks_find(
        words: str,
        role: str | None = None,
        data_level: int | None = None,
        market_class: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Find dictionary blocks by words before writing one: one line per entry, best match
        first. Narrow by the slot role it plays, the data level the market offers or the
        market class it must carry to."""
        rows = [index_row(h.entry, h.status) for h in catalogue()]
        found = find_rows(
            rows, words, role=role, data_level=data_level, market_class=market_class, limit=limit
        )
        return {"rows": [r.as_json() for r in found], "count": len(found)}

    def blocks_get(entry_id: str, version: int | None = None) -> dict[str, Any]:
        """Read one dictionary entry in full, with its code and status; the newest version
        unless one is named."""
        everything = catalogue()
        held = [h for h in everything if h.entry.get("entry_id") == entry_id]
        if version is not None:
            held = [h for h in held if h.entry.get("version") == version]
        if not held:
            ids = sorted({str(h.entry.get("entry_id")) for h in everything})
            near = difflib.get_close_matches(entry_id, ids, n=NEAREST_SUGGESTIONS, cutoff=0.0)
            raise ValueError(f"no entry {entry_id!r}; the nearest are {', '.join(near)}")
        newest = max(held, key=lambda h: cast("int", h.entry.get("version")))
        return {
            "entry": newest.entry,
            "status": newest.status,
            "code": None if newest.source is None else newest.source.decode("utf-8"),
            "held_in": newest.held_in,
        }

    def blocks_check(entry: dict[str, Any], source: str | None = None) -> dict[str, Any]:
        """Check an entry draft and its block source: every problem at once, the status it
        would earn, what its next status lacks, and the fingerprint its source has."""
        code = None if source is None else source.encode("utf-8")
        computed = compute_status(entry, code)
        mine = entry.get("entry_id")
        others = [h.entry for h in catalogue()]
        clashes = [p for p in corpus_problems([*others, entry]) if p.where.startswith(f"{mine}@")]
        problems = [*computed.problems, *clashes]
        return {
            "verdict": "fail" if problems else "pass",
            "status": None if computed.status is None or clashes else computed.status.value,
            "counts": {"errors": len(problems)},
            "errors": [p.as_json() for p in problems],
            "missing": list(computed.missing),
            "fingerprint": None if code is None else block_fingerprint(code).value,
        }

    def blocks_match(text: str) -> dict[str, Any]:
        """Match each sentence of a source to the entry it states; a sentence no entry covers
        comes back as an append request, never as a guess."""
        rows = [index_row(h.entry, h.status) for h in catalogue()]
        return match_text(text, rows).as_json()

    return {
        "blocks_find": blocks_find,
        "blocks_get": blocks_get,
        "blocks_check": blocks_check,
        "blocks_match": blocks_match,
    }


INSTRUMENT_KIND: Final = "instrument"
INSTRUMENT_STATUSES: Final = ("specified", "live", "suspect", "delisted")
"""Every status an `instrument` record holds; the kind requires one, so the four list them all."""
READINGS_SOURCE: Final = "journal-readings"
READING_KIND: Final = "reading"
READING_SOURCES: Final = ("node", "mis")
CONCISE_READING: Final = (
    "market_id",
    "tier",
    "source",
    "word",
    "value",
    "percentile",
    "health",
    "computed_at",
    "stale_after_s",
    "fallback_step",
    "estimate",
    "corrects",
)
"""The section 7 fields a concise row keeps."""


def _iso_ns(ns: int) -> str:
    seconds, rest = divmod(ns, 1_000_000_000)
    moment = datetime.fromtimestamp(seconds, tz=UTC).strftime("%Y-%m-%dT%H:%M:%S")
    return f"{moment}.{rest // 1_000_000:03d}Z"


@dataclass(frozen=True, slots=True)
class _InForce:
    """One instrument item's version in force: its version number, when it reached `main`,
    and the object that holds the record."""

    item: str
    version: int
    since: str
    view: ObjectView


def instrument_functions(ctx: DomainContext) -> Callable[..., dict[str, Any]]:
    """The `instrument` row (Part C CONTRACTS.md section 12): one record as it stood at an
    instant, read from his Library's `instrument` items on `main`. A record's version is how
    many times `main` has moved for its item, as the unit checker counts it."""

    def in_force(item: str, moment: int, version: int | None) -> _InForce | None:
        store = ctx.library.store
        moves = list(enumerate(store.history_of(OPERATOR, item, MAIN), 1))
        if version is None:
            moves = [(n, m) for n, m in moves if journals.parse_instant(m.at, "at") <= moment]
        else:
            moves = [(n, m) for n, m in moves if n == version]
        if not moves:
            return None
        n, move = moves[-1]
        return _InForce(item, n, move.at, store.get(OPERATOR, move.new_head))

    def nearest(asked: Mapping[str, str]) -> list[str]:
        store = ctx.library.store
        fields = [
            store.get(OPERATOR, object_id).fields
            for status in INSTRUMENT_STATUSES
            for object_id in store.with_field(INSTRUMENT_KIND, "status", status)
        ]
        if "market_id" in asked:
            names = {str(f.get("market_id")) for f in fields}
            wanted = asked["market_id"]
        else:
            names = {f"{f.get('venue')}:{f.get('symbol')}" for f in fields}
            wanted = f"{asked['venue']}:{asked['symbol']}"
        return difflib.get_close_matches(wanted, sorted(names), n=NEAREST_SUGGESTIONS, cutoff=0.0)

    def instrument_get(
        venue: str | None = None,
        symbol: str | None = None,
        market_id: str | None = None,
        at: str | int | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        """Read one instrument record as it stood at `at` (an ISO 8601 time or epoch
        nanoseconds, now by default), or its `version`. Name it by `venue` and `symbol`, or by
        `market_id` when one venue holds that market. An archived record is withdrawn."""
        if (venue is None) != (symbol is None) or (symbol is None) == (market_id is None):
            raise ValueError("name the instrument by venue and symbol, or by market_id alone")
        if version is not None and version < 1:
            raise ValueError("version counts from 1, the record's first version on main")
        try:
            moment = time.time_ns() if at is None else journals.parse_instant(at, "at")
        except ValueError:
            raise ValueError(
                f"at is an ISO 8601 time such as 2025-01-02T08:00:00Z or epoch nanoseconds; "
                f"got {at!r}"
            ) from None
        asked = (
            {"market_id": cast("str", market_id)}
            if symbol is None
            else {"venue": cast("str", venue), "symbol": symbol}
        )
        store = ctx.library.store
        key = "symbol" if symbol is not None else "market_id"
        items = sorted(
            {
                store.get(OPERATOR, object_id).item
                for object_id in store.with_field(INSTRUMENT_KIND, key, asked[key])
            }
        )
        found: list[_InForce] = []
        starts: list[str] = []
        for item in items:
            state = store.head(item, state_ref(item))
            if state is not None and state[0] == "archived":
                continue
            held = in_force(item, moment, version)
            if held is None:
                starts.extend(m.at for m in store.history_of(OPERATOR, item, MAIN)[:1])
            elif all(held.view.fields.get(name) == value for name, value in asked.items()):
                found.append(held)
        if len(found) == 1:
            held = found[0]
            return {
                "ok": True,
                "record": held.view.fields,
                "id": held.item,
                "version": held.version,
                "fingerprint": held.view.object_id,
                "status": held.view.fields.get("status"),
                "in_force_since": held.since,
                "at": _iso_ns(moment),
            }
        if found:
            return {
                "ok": False,
                "code": "ambiguous",
                "message": f"{len(found)} instrument records hold {asked['market_id']}; name one "
                "by venue and symbol",
                "choices": [
                    {
                        "id": h.item,
                        "venue": h.view.fields.get("venue"),
                        "symbol": h.view.fields.get("symbol"),
                    }
                    for h in found
                ],
            }
        answer: dict[str, Any] = {"ok": False, "code": "not_found", "nearest": nearest(asked)}
        if starts:
            answer["message"] = (
                f"no version of it was in force at {_iso_ns(moment)}; its first version reached "
                f"main at {min(starts)}"
            )
        return answer

    return instrument_get


@dataclass(frozen=True, slots=True, order=True)
class _Reading:
    """One reading record as a `journal-readings` partition holds it, ordered as pages run."""

    t: int
    partition: str
    seq: int
    record: Mapping[str, Any] = field(compare=False)

    @property
    def body(self) -> Mapping[str, Any]:
        return cast("Mapping[str, Any]", self.record.get("body", {}))

    @property
    def cursor(self) -> str:
        return f"{self.t}:{self.seq}:{self.partition}"

    def concise(self) -> dict[str, Any]:
        """What the reading said and how fresh it was; `detailed` carries the whole record."""
        body = self.body
        ref = cast("Mapping[str, Any]", body.get("reading", {}))
        found: dict[str, Any] = {
            "at": _iso_ns(self.t * journals.NS_PER_MS),
            "reading": f"{ref.get('id')}@{ref.get('version')}",
        }
        found.update({name: body[name] for name in CONCISE_READING if name in body})
        if isinstance(found.get("computed_at"), int):
            found["computed_at"] = _iso_ns(found["computed_at"])
        return found

    def detailed(self) -> dict[str, Any]:
        return {"partition": self.partition, "t": self.t, "seq": self.seq, "record": self.record}


@dataclass(frozen=True, slots=True)
class _Ask:
    """What a `readings_query` names, matched against each record's body."""

    reading: str
    version: str | None
    markets: frozenset[str] | None
    tier: str | None
    source: str | None

    def holds(self, body: Mapping[str, Any]) -> bool:
        ref = cast("Mapping[str, Any]", body.get("reading", {}))
        return (
            ref.get("id") == self.reading
            and self.version in (None, ref.get("version"))
            and (self.markets is None or body.get("market_id") in self.markets)
            and self.tier in (None, body.get("tier"))
            and self.source in (None, body.get("source"))
        )


def _reading_folders(root: Path, subjects: frozenset[str] | None) -> list[Path]:
    """The `journal-readings` series folders, narrowed to the subjects asked for."""
    base = root / READINGS_SOURCE
    if not base.is_dir():
        return []
    found: list[Path] = []
    for subject in sorted(base.iterdir()):
        kind = subject / READING_KIND
        if (subjects is None or subject.name in subjects) and kind.is_dir():
            found.extend(sorted(path for path in kind.iterdir() if path.is_dir()))
    return found


def _months(folder: Path) -> list[SeriesKey]:
    keys: list[SeriesKey] = []
    for month in sorted(folder.iterdir()):
        year, _, number = month.name.partition("-")
        if not (year.isdigit() and number.isdigit() and (month / STATE_NAME).is_file()):
            continue
        variant = "" if folder.name == "-" else folder.name
        made = SeriesKey.try_create(
            READINGS_SOURCE,
            folder.parent.parent.name,
            READING_KIND,
            int(year),
            int(number),
            variant,
        )
        if not is_refusal(made):
            keys.append(made.value)
    return keys


def _held_out_from(door: MarketPort, series: str) -> int | None:
    """Where the door's holdout starts for `series`, from its own card, or None when off."""
    card: object = unwrap(door.card(series))
    boundary = (
        cast("Mapping[str, object]", card).get("seal_boundary")
        if isinstance(card, Mapping)
        else None
    )
    if boundary == "":
        return None
    if isinstance(boundary, str) and boundary.isdigit():
        return int(boundary)
    raise ValueError(
        f"the market-data door names a holdout this row cannot place ({boundary!r}), so reading "
        "history stays unread rather than risk the held-out window"
    )


def _cursor(cursor: str | None) -> tuple[int, str, int] | None:
    if cursor is None:
        return None
    t, _, rest = cursor.partition(":")
    seq, _, partition = rest.partition(":")
    if not (t.isdigit() and seq.isdigit() and partition):
        raise ValueError("cursor is a next_cursor a readings_query answer gave; pass it unchanged")
    return int(t), partition, int(seq)


def readings_functions(ctx: DomainContext) -> Callable[..., dict[str, Any]]:
    """The `readings` row (Part C CONTRACTS.md section 12, AD-313): reading history from the
    `journal-readings` partitions the host's records job harvests, the open month included.
    It is the only door agents read readings through. The market-data door's holdout is his
    choice per study (ruling 137): a month the door would seal is never read here, and a
    window that reaches one is refused by name, as the door refuses a sealed read."""

    def readings_query(
        reading: str,
        window: dict[str, str | int],
        version: str | None = None,
        markets: list[str] | None = None,
        tier: Literal["tick", "bar", "session", "day", "calendar"] | None = None,
        source: Literal["node", "mis"] | None = None,
        limit: int = 50,
        cursor: str | None = None,
        response_format: ResponseFormat = "concise",
    ) -> dict[str, Any]:
        """Read what one reading said over a required time window, UTC:
        {"start": "2025-01-06T00:00:00Z", "end": "2025-01-13T00:00:00Z"}. Narrow by its
        `version`, `markets` (market ids), `tier` and `source`. Each row has its value or word,
        health, computed_at and stale_after_s. Pass `next_cursor` back as `cursor` for the next
        page; `data_ends_at` is the last recorded instant."""
        if "start" not in window or "end" not in window:
            raise ValueError(
                "readings_query needs a time window: pass window = {start, end}, for example "
                '{"start": "2025-01-06T00:00:00Z", "end": "2025-01-13T00:00:00Z"}'
            )
        start = journals.parse_instant(window["start"], "start")
        end = journals.parse_instant(window["end"], "end")
        if end <= start:
            raise ValueError("the window's end comes after its start")
        if limit < 1:
            raise ValueError("limit is 1 or more")
        door = ctx.market
        if door is None:
            raise ValueError(
                "No market-data door on this host; reading history is read only where the door "
                "can say which months a study holds out (Lib AD-28)"
            )
        after = _cursor(cursor)
        ask = _Ask(reading, version, None if markets is None else frozenset(markets), tier, source)
        root = ctx.root / journals.MARKET_FOLDER / "series"
        sources = READING_SOURCES if source is None else (source,)
        subjects = (
            None
            if markets is None
            else frozenset(key_token(f"{s}.{m}") for s in sources for m in markets)
        )
        held_from: int | None = None
        readable: list[list[SeriesKey]] = []
        sealed: list[str] = []
        for folder in _reading_folders(root, subjects):
            keys = _months(folder)
            if not keys:
                continue
            boundary = _held_out_from(door, keys[0].series)
            if boundary is not None:
                held_from = boundary if held_from is None else min(held_from, boundary)
            opened = [key for key in keys if boundary is None or key.end_ns <= boundary]
            sealed.extend(
                key.text
                for key in keys
                if key not in opened and key.start_ns < end and start < key.end_ns
            )
            readable.append(opened)
        if sealed:
            raise ValueError(
                f"the study's holdout seals reading history from {_iso_ns(cast('int', held_from))};"
                f" this window reaches {', '.join(sealed)}, so it is refused, never answered "
                "empty; ask for a window that ends before the holdout"
            )
        store = SeriesStore(root)
        rows: list[_Reading] = []
        last: int | None = None
        unreadable: list[str] = []
        for keys in readable:
            for index, key in enumerate(keys):
                if not (key.start_ns < end and start < key.end_ns) and index < len(keys) - 1:
                    continue
                read = store.read(key)
                if is_refusal(read):
                    unreadable.append(key.text)
                    continue
                for cells in read.value.rows:
                    row = _Reading(
                        int(cast("int", cells["t"])),
                        key.text,
                        int(cast("int", cells["seq"])),
                        json.loads(str(cells["record"])),
                    )
                    if not ask.holds(row.body):
                        continue
                    last = row.t if last is None else max(last, row.t)
                    inside = start <= row.t * journals.NS_PER_MS < end
                    if inside and (after is None or (row.t, row.partition, row.seq) > after):
                        rows.append(row)
        rows.sort()
        page = rows[:limit]
        shown = [row.detailed() if response_format == "detailed" else row.concise() for row in page]
        answer: dict[str, Any] = {
            **ctx.output(shown, "readings", response_format),
            "next_cursor": page[-1].cursor if len(rows) > limit else None,
            "data_ends_at": None if last is None else _iso_ns(last * journals.NS_PER_MS),
            "window": {"start": _iso_ns(start), "end": _iso_ns(end)},
        }
        if last is None:
            answer["note"] = "no reading history matches; nothing is recorded yet"
        elif last * journals.NS_PER_MS < end:
            answer["note"] = (
                f"the data stops at {answer['data_ends_at']}; nothing after it is recorded yet"
            )
        if held_from is not None:
            answer["holdout_from"] = _iso_ns(held_from)
        if unreadable:
            answer["unreadable"] = unreadable
        return answer

    return readings_query
