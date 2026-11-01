"""The typed domain functions behind the MCP doors and the agent tools."""

from __future__ import annotations

import difflib
import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Literal, cast

import qml
from qmf.core import Instant
from qml.catalogue.entry import ENTRY_SCHEMA, Computed, compute_status, corpus_problems
from qml.catalogue.index import find as find_rows
from qml.catalogue.index import match as match_text
from qml.catalogue.index import row as index_row
from qml.catalogue.loader import block_fingerprint
from qml.catalogue.roles import NEAREST_SUGGESTIONS
from qml.door import explain, new
from qmn.doors.api import read_status
from qmx_control.library import OPERATOR
from qmx_judge.landing import REPORT_SLOT, RESULT_KIND
from qmx_judge.tries import try_item
from qmx_library.kinds import KindRefused
from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import MAIN, drafts_ref

from qmx_tools.gather import DUMMY, STDLIB, TEMPLATES, entry_face, gather
from qmx_tools.gather import template as template_document
from qmx_tools.service import (
    Artifact,
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
    from qmx_library.store import Store

UNIT_KIND: Final = "unit"
REPO: Final = Path(qml.__file__).resolve().parents[3]


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
        response_format: ResponseFormat = "concise",
    ) -> dict[str, Any]:
        """Backtest a unit on QMB over `window` (`{"start": "2025-03-01", "end": "2025-04-01"}`)
        and land its result in the Library. Answers the run id, and the result id when it
        finished within the wait; otherwise read it later with backtest_status."""
        asked = {
            "unit": unit,
            "window": window,
            "markets": markets,
            "study": study,
            "compiled_fp": compiled_fp,
            "seed": seed,
            "motion": motion,
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
        """Compare two landed results: differing measures, and trades in one only or differing."""
        (first, mine), (second, theirs) = _result(left), _result(right)
        ours = {str(t["trade_id"]): t for t in mine}
        other = {str(t["trade_id"]): t for t in theirs}
        rows = [
            {"trade_id": key, "left": ours.get(key), "right": other.get(key)}
            for key in sorted(ours.keys() | other.keys())
            if ours.get(key) != other.get(key)
        ]
        a = cast("dict[str, Any]", first.get("measures") or {})
        b = cast("dict[str, Any]", second.get("measures") or {})
        measures = {
            key: [a.get(key), b.get(key)]
            for key in sorted(a.keys() | b.keys())
            if a.get(key) != b.get(key)
        }
        page = ctx.page(
            rows, Page(limit=limit, cursor=cursor, response_format=response_format), "comparison"
        )
        return {**page, "same_trades": not rows, "measures": measures}

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
            "backtest_run": backtest_run,
            "backtest_status": backtest_status,
            "backtest_results": backtest_results,
            "backtest_compare": backtest_compare,
        },
        "research": {
            "qml_run": qml_run,
            "library_search": library_search,
            "library_save": library_save,
        },
        "node": {"node_state": node_state, "propose_order": propose_order},
        "unit": unit_functions(ctx),
        "blocks": block_functions(ctx),
    }


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
        others = [h.entry for h in catalogue() if h.entry.get("entry_id") != mine]
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
