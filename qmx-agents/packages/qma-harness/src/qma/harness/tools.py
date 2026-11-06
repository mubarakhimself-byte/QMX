"""QMX's own tools for a chat, built from the operation catalog (engine AD-61).

"The copilot is the same API as the UI" (01 section 11.1), so every tool is a catalog row
(`qmx_control.catalog`) bound to the control-plane, broker, domain or host function that already
serves it. In-process means the CLI never receives the qmx-control bearer token (HOW seam 2).

A row with `agent=False` never joins. Which tools ask and the grant check derive from the row's
`approval`. Each toolset is one in-process server, `qmx_<toolset>`, and a chat's surface is the
set of those servers switched on (probe P-PK found no mid-chat re-list for one server; P-TG
passed toggling). A tool's full name is `mcp__qmx_<toolset>__<op>`, the same length as the
`mcp__qmx__<toolset>_<op>` the catalog checks.
"""

from __future__ import annotations

import asyncio
import contextlib
import glob
import hashlib
import json
import logging
import re
import sys
from collections.abc import Awaitable, Callable, Iterable, Mapping
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, Literal, NewType, cast

import keyring
from claude_agent_sdk import SdkMcpTool, create_sdk_mcp_server
from pydantic import JsonValue
from qmx_broker.models import ReadStamp
from qmx_broker.service import BrokerService
from qmx_control.catalog import (
    CORE_TOOLSETS,
    DOMAIN_ROWS,
    TOOLSET_WIRE,
    CatalogError,
    OperationSpec,
    app_rows,
    name_problem,
    rows,
    spill,
)
from qmx_control.service import plain_https
from qmx_home.classes import secret_globs, secret_paths

from qma.harness.delegate import DelegateRefused
from qma.harness.demo_only import (
    EXPIRED,
    VENUES,
    AccountWorlds,
    NotOffered,
    ServerCall,
    demo_account,
)
from qma.harness.guard import QMX_SERVER, GuardRules, Rule, is_qmx_server, normalize_path

if TYPE_CHECKING:
    from claude_agent_sdk import McpSdkServerConfig, McpServerConfig
    from claude_agent_sdk.types import McpStatusResponse
    from fastmcp import FastMCP
    from fastmcp.tools import Tool
    from qmx_control.service import ControlService
    from qmx_tools.service import DomainContext

    from qma.harness.home import QmxHome

SERVER: Final = QMX_SERVER
log = logging.getLogger(__name__)


class Effect(Enum):
    """What a QMX tool does to the world, from its row's `approval`. Closed. There is no member
    for moving money: agents have no path to money (ruling 116).

    READ           reads QMX or broker state. Runs without asking.
    DOMAIN_WRITE   writes QMX research state (library, backtests, run results). Asks or not
                   per `settings.toml [agents] domain_write` ("allow" | "ask"). `delegate`
                   is DOMAIN_WRITE: its child chat's own acts face their own gates.
    MANAGE         publish, install, schedule, run, cancel, destructive control-plane ops.
                   Always asks (R35).
    PROPOSE_MONEY  writes an unsigned order proposal. Always asks. Accepted on
                   `BrokerService.propose_order` only, by identity.
    """

    READ = "read"
    DOMAIN_WRITE = "domain_write"
    MANAGE = "manage"
    PROPOSE_MONEY = "propose_money"


type DomainWritePolicy = Literal["allow", "ask"]
DEFAULT_DOMAIN_WRITE: Final[DomainWritePolicy] = "allow"
"""R35 names publish, install, scheduling and managing as always asking; research writes
follow the setting, and run without asking until the operator changes it."""


def asks(effect: Effect, domain_write: DomainWritePolicy) -> bool:
    """The one table: READ no; DOMAIN_WRITE per policy; MANAGE and PROPOSE_MONEY yes."""
    match effect:
        case Effect.READ:
            return False
        case Effect.DOMAIN_WRITE:
            return domain_write == "ask"
        case Effect.MANAGE | Effect.PROPOSE_MONEY:
            return True


def domain_write_policy(agents: Mapping[str, object]) -> DomainWritePolicy:
    """`settings.toml [agents] domain_write`. Anything but "allow" reads as "ask"."""
    value = agents.get("domain_write", DEFAULT_DOMAIN_WRITE)
    return "allow" if value == "allow" else "ask"


type ToolCall = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


def server_name(toolset: str) -> str:
    """`qmx_<toolset>` in the toolset's wire form: a pack's `app:<id>` serves as
    `qmx_app_<id>`, because a server name takes no colon."""
    return f"{SERVER}_{TOOLSET_WIRE.sub('_', toolset)}"


def tool_name(toolset: str, op: str) -> str:
    """The name the CLI gives a tool: `mcp__qmx_<toolset>__<op>`."""
    return f"mcp__{server_name(toolset)}__{op}"


@dataclass(frozen=True)
class ToolDef:
    toolset: str
    op: str
    description: str
    input_schema: Mapping[str, object]
    effect: Effect
    """Required, no default. A tool without one does not construct."""
    call: ToolCall
    metadata: Mapping[str, object] = field(default_factory=dict[str, object])
    """The MCP annotations and `_meta`."""
    target: object = None
    """The function the tool runs. PROPOSE_MONEY is accepted by its identity."""

    def __post_init__(self) -> None:
        if not isinstance(self.effect, Effect):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"{self.name} declares no Effect")

    @property
    def name(self) -> str:
        """The wire name, `<toolset>_<op>`, with the toolset's wire form."""
        return f"{TOOLSET_WIRE.sub('_', self.toolset)}_{self.op}"

    @property
    def full(self) -> str:
        return tool_name(self.toolset, self.op)


FIXED_REFS: Final[frozenset[str]] = frozenset({"qmx/chatgpt", "qmx/control-token"})
"""Fixed `qmx/*` entries every chat's guard refuses by name, besides the settings.toml ones."""


ArgsDigest = NewType("ArgsDigest", str)
"""sha256 over the tool name and the canonical JSON of its input (sorted keys, no
whitespace, UTF-8)."""


def args_digest(name: str, tool_input: Mapping[str, object]) -> ArgsDigest:
    body = json.dumps([name, tool_input], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return ArgsDigest(hashlib.sha256(body.encode()).hexdigest())


@dataclass(frozen=True)
class Grant:
    tool: str
    digest: ArgsDigest


class Grants:
    """One chat's approvals for asking QMX tools. A grant is consumed by the first handler run
    that matches it, so an approval never outlives the arguments the operator saw. Until
    approvals are wired, nothing records one and every asking tool is refused."""

    def __init__(self) -> None:
        self._open: list[Grant] = []

    def record(self, grant: Grant) -> None:
        self._open.append(grant)

    def consume(self, tool: str, digest: ArgsDigest) -> bool:
        """True once per recorded grant, then False."""
        grant = Grant(tool, digest)
        if grant in self._open:
            self._open.remove(grant)
            return True
        return False


NEXT_STEPS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "not_found": "check the id with the matching list tool, then call again",
        "invalid_arguments": "fix the arguments to match this tool's input schema",
        "unavailable": "this part of QMX is not running here; tell the operator",
        "conflict": "read the current state, then call again with it",
    }
)
DEFAULT_NEXT_STEP: Final = "read the message; call again only after changing what it names"


def failure(code: str, message: str, problems: object = None) -> dict[str, Any]:
    """The tool error shape: a code, the message and a next step, never a raw exception. A
    refusal that names several problems carries every one of them."""
    next_step = NEXT_STEPS.get(code, DEFAULT_NEXT_STEP)
    body: dict[str, object] = {"code": code, "message": message, "next_step": next_step}
    if problems:
        body["problems"] = problems
    return {"content": [{"type": "text", "text": json.dumps({"error": body})}], "is_error": True}


def _failure_of(error: Exception) -> dict[str, Any]:
    """A control error arrives as its JSON document; anything else is named by its type."""
    with contextlib.suppress(ValueError, TypeError, KeyError):
        found = json.loads(str(error))["error"]
        return failure(str(found["code"]), str(found["message"]), found.get("problems"))
    if type(error).__name__ in ("ValidationError", "ToolError") and "validation" in str(error):
        return failure("invalid_arguments", str(error))
    return failure(type(error).__name__, str(error))


def _text(result: Any) -> str:
    return "".join(block.text for block in result.content if getattr(block, "type", None) == "text")


def _paged(
    row: OperationSpec, result: Any, arguments: Mapping[str, object], limit: int
) -> tuple[str, dict[str, object]]:
    """A list answer as one page with the offset of the next, or the answer's own text; and what
    a spill pointer keeps beside its head and tail: the cursor, and a broker read's demo-or-live
    stamp, which also rides on every page."""
    structured = cast("Mapping[str, object] | None", getattr(result, "structured_content", None))
    found = structured or {}
    stamp = (
        {key: found[key] for key in ReadStamp.__annotations__}
        if all(key in found for key in ReadStamp.__annotations__)
        else {}
    )
    data = found.get("result")
    if not row.cursor or not isinstance(data, list):
        return _text(result), stamp
    items = cast("list[object]", data)
    offset = arguments.get("offset", 0)
    start = offset if isinstance(offset, int) else 0
    wanted = arguments.get("limit", limit)
    full = len(items) >= (wanted if isinstance(wanted, int) else limit)
    cursor: dict[str, object] = {"next_offset": start + len(items) if full else None}
    return json.dumps({**stamp, "items": items, **cursor}), {**stamp, **cursor}


def wrap(row: OperationSpec, tool: Tool, save: Callable[..., Any]) -> ToolDef:
    """One row as a tool: forced arguments left out of the schema, a list answer paged with a
    cursor, a long answer spilled to the Library, and an error in the tool error shape."""
    forced = dict(row.forced)
    schema = dict(tool.parameters)
    properties = cast("dict[str, Any]", schema.get("properties", {}))
    if forced:
        schema["properties"] = {k: v for k, v in properties.items() if k not in forced}
        required = cast("list[str]", schema.get("required", []))
        schema["required"] = [name for name in required if name not in forced]
    declared = cast("dict[str, Any]", properties.get("limit", {})).get("default")
    # A `limit` whose default is None (broker bars: every bar) still pages by 100.
    limit_default = declared if isinstance(declared, int) else 100

    async def call(arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            result = await tool.run({**arguments, **forced})
        except Exception as error:
            return _failure_of(error)
        text, keep = _paged(row, result, arguments, limit_default)
        answer = await asyncio.to_thread(spill, text, row, save, keep)
        return {"content": [{"type": "text", "text": answer}]}

    metadata: dict[str, object] = {"_meta": dict(tool.meta or {})}
    if tool.annotations is not None:
        metadata["annotations"] = tool.annotations.model_dump(exclude_none=True)
    return ToolDef(
        toolset=row.toolset,
        op=row.op,
        description=row.description or tool.description or row.name,
        input_schema=schema,
        effect=Effect(row.approval),
        call=call,
        metadata=metadata,
        target=getattr(tool, "fn", None),
    )


def _plain(row: OperationSpec, schema: Mapping[str, object], call: ToolCall) -> ToolDef:
    return ToolDef(
        toolset=row.toolset,
        op=row.op,
        description=row.description,
        input_schema=schema,
        effect=Effect(row.approval),
        call=call,
    )


async def _bound(
    found: Iterable[OperationSpec],
    servers: list[FastMCP],
    save: Callable[..., Any],
    *,
    by_name: bool = False,
) -> list[ToolDef]:
    """Each row as a tool from the server that serves it, by `target` or, for the control door,
    by wire name. A row with no tool behind it raises, so a renamed or removed function never
    drops out of the surface unnoticed."""
    tools = {tool.name: tool for server in servers for tool in await server.list_tools()}
    keyed = [(row.name if by_name else row.target, row) for row in found]
    missing = sorted(key for key, _ in keyed if key not in tools)
    if missing:
        raise ToolSurfaceError(f"catalog rows are missing on their server: {', '.join(missing)}")
    return [wrap(row, tools[key], save) for key, row in keyed]


type HostRead = Callable[[dict[str, Any]], Awaitable[Mapping[str, object]]]
"""A host read served to an `agent_tool` row: the harness's chat-slot table or a chat's journal,
or one the hosting process passes to `Harness.open`, such as its heartbeats."""

NO_ARGUMENTS: Final[Mapping[str, object]] = MappingProxyType({"type": "object", "properties": {}})
_REF: Final[dict[str, object]] = {
    "type": "string",
    "description": "A reference as written, for example @pod:pod-7 or @run:<id>/bias",
}
"""A plain dict, never a mapping proxy: this one sits *inside* another schema, and the CLI
serialises the whole tool list at connect."""
HOST_SCHEMAS: Final[Mapping[str, Mapping[str, object]]] = MappingProxyType(
    {
        "slot_table": {"type": "object", "properties": {}},
        "journal": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "The chat's session id"},
                "offset": {"type": "integer", "minimum": 0, "default": 0},
                "limit": {"type": "integer", "minimum": 1, "default": 50},
            },
            "required": ["session_id"],
        },
        "context_add": {
            "type": "object",
            "properties": {
                "ref": _REF,
                "pin": {
                    "type": "string",
                    "enum": ["version", "follow"],
                    "default": "version",
                    "description": "version keeps the object resolved now; follow re-reads "
                    "main at each read",
                },
            },
            "required": ["ref"],
        },
        "context_list": {"type": "object", "properties": {}},
        "context_refresh": {
            "type": "object",
            "properties": {"ref": _REF},
            "required": ["ref"],
        },
        "context_drop": {
            "type": "object",
            "properties": {"ref": _REF},
            "required": ["ref"],
        },
        "context_read": {
            "type": "object",
            "properties": {
                "ref": _REF,
                "range": {
                    "type": "string",
                    "description": "An a-b character range of the object's text",
                },
            },
            "required": ["ref"],
        },
        "memory_recall": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The question to ask memory, in words",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Only rows tagged or keyed with these, such as built or "
                    "dead_end",
                },
                "budget_tokens": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 2000,
                    "description": "Most tokens of rows to return",
                },
                "as_of": {
                    "type": "string",
                    "description": "Read memory as it stood for a validity window containing "
                    "this ISO date, instead of today",
                },
                "regime": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Rows learnt in this regime rank first",
                },
            },
            "required": ["query"],
        },
        "memory_note": {
            "type": "object",
            "properties": {
                "tag": {
                    "type": "string",
                    "enum": [
                        "built",
                        "lesson",
                        "dead_end",
                        "do_not_retry",
                        "negative_result",
                        "procedure",
                        "preference",
                    ],
                    "description": "What kind of row this is",
                },
                "content": {"type": "string", "description": "What to remember, in one paragraph"},
                "when_to_use": {
                    "type": "string",
                    "description": "The situation this row is for",
                },
                "refs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The Library objects it is about, as item:<object id>",
                },
                "intent_key": {
                    "type": "string",
                    "description": "For a built or dead_end row, the key a later build checks",
                },
                "regime": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The market regime it was learnt in, when that matters",
                },
                "valid_to": {
                    "type": "string",
                    "description": "An ISO date after which the row no longer applies",
                },
            },
            "required": ["tag", "content"],
        },
        "memory_check": {
            "type": "object",
            "properties": {
                "intent_key": {
                    "type": "string",
                    "description": "The build's key: kind, canonical inputs, parameters and code",
                },
                "query": {
                    "type": "string",
                    "description": "A question to check for a known dead end when there is no key",
                },
            },
        },
        "memory_forget": {
            "type": "object",
            "properties": {
                "row_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The rows to forget, as recall returned their ids",
                }
            },
            "required": ["row_ids"],
        },
        "memory_rebuild": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["all", "run", "workflow", "home", "operator"],
                    "default": "all",
                    "description": "Which scope to re-index",
                }
            },
        },
        "provider_test": {
            "type": "object",
            "properties": {
                "qmx_id": {
                    "type": "string",
                    "description": "The model row to test, as ops_providers lists it, for "
                    "example openrouter/z-ai/glm-5.3",
                }
            },
            "required": ["qmx_id"],
        },
        "mark": {
            "type": "object",
            "properties": {
                "item": {"type": "string", "description": "The Library item id to mark"},
                "quarantined": {
                    "type": "boolean",
                    "description": "True to quarantine the item, false to clear its quarantine",
                },
                "reason": {"type": "string", "description": "Why, in one sentence"},
            },
            "required": ["item", "quarantined", "reason"],
        },
    }
)


def _host_def(row: OperationSpec, read: HostRead) -> ToolDef:
    async def call(arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            found = await read(arguments)
        except KeyError as error:
            return failure("not_found", str(error))
        except ValueError as error:
            return failure("invalid_arguments", str(error))
        except OSError as error:
            return failure("unavailable", str(error))
        return {"content": [{"type": "text", "text": json.dumps(found, default=str)}]}

    return _plain(row, HOST_SCHEMAS.get(row.target, NO_ARGUMENTS), call)


MOVE_SCHEMA: Final[Mapping[str, object]] = MappingProxyType(
    {
        "type": "object",
        "properties": {
            "app_id": {"type": "string", "description": "The app instance to move"},
            "to": {
                "type": "string",
                "description": "The placement name of the machine that takes the instance",
            },
        },
        "required": ["app_id", "to"],
    }
)


def served_apps(control: ControlService) -> list[tuple[OperationSpec, dict[str, object]]]:
    """Each running app's `[operations]` rows, pinned to its selected version, each with the
    input schema the app declares for it. A stopped app serves none, and so does one whose rows
    the catalog refuses (an id too long for a tool name), so one app never stops every chat."""
    found: list[tuple[OperationSpec, dict[str, object]]] = []
    for app in control.app_runtime().list():
        runtime, definition = app.get("runtime"), app.get("definition")
        if not isinstance(runtime, dict) or runtime.get("status") != "running":
            continue
        if not isinstance(definition, dict):
            continue
        operations = cast("dict[str, dict[str, object]]", definition.get("operations") or {})
        app_id, version = str(definition["id"]), str(definition["version"])
        try:
            declared = app_rows(app_id, version, operations)
        except CatalogError as refused:
            log.warning("the app %s serves no tools to a chat: %s", app_id, refused)
            continue
        for row in declared:
            schema = operations[row.op].get("input_schema")
            found.append((row, cast("dict[str, object]", schema) if schema else dict(NO_ARGUMENTS)))
    return found


def _app_failure(error: Exception) -> dict[str, Any]:
    """An `AppError` by its code, read by shape: the harness does not import the apps package."""
    code = getattr(error, "code", None)
    return failure(code, str(error)) if isinstance(code, str) else _failure_of(error)


def _app_def(row: OperationSpec, schema: Mapping[str, object], control: ControlService) -> ToolDef:
    """One app operation as a tool: an ask to the running app, pinned to the row's version."""
    pin: dict[str, JsonValue] = {"pack": row.pack, "version": row.version}

    async def call(arguments: dict[str, Any]) -> dict[str, Any]:
        runtime = control.app_runtime()
        try:
            found = await asyncio.to_thread(runtime.call, row.owner, row.op, arguments, pin=pin)
        except Exception as error:
            if getattr(error, "code", None) == "not_running":
                return failure(
                    "app_not_running",
                    f"{row.owner} stopped after this chat's tools were listed; start it, then "
                    "open a new chat",
                )
            return _app_failure(error)
        text = json.dumps(found, default=str)
        answer = await asyncio.to_thread(spill, text, row, control.library_save)
        return {"content": [{"type": "text", "text": answer}]}

    return _plain(row, schema, call)


def _move_def(row: OperationSpec, control: ControlService) -> ToolDef:
    """`apps_admin_move`: the supervisor snapshots the instance for `to`, hands it the volume
    lease and records `to` as its home. The receiving machine restores the snapshot."""

    async def call(arguments: dict[str, Any]) -> dict[str, Any]:
        app_id, to = arguments.get("app_id"), arguments.get("to")
        if not isinstance(app_id, str) or not isinstance(to, str):
            return failure("invalid_arguments", "app_id and to are strings")
        runtime = control.app_runtime()
        try:
            moved = await asyncio.to_thread(runtime.snapshot_instance, app_id, to=to)
        except Exception as error:
            return _app_failure(error)
        return {"content": [{"type": "text", "text": json.dumps(moved.document())}]}

    return _plain(row, MOVE_SCHEMA, call)


def _app_server_def(
    row: OperationSpec,
    control: ControlService,
    schemas: Mapping[str, Mapping[str, object]],
) -> ToolDef:
    if row.owner != "core":
        return _app_def(row, schemas[row.name], control)
    if row.target == "move":
        return _move_def(row, control)
    raise ToolSurfaceError(f"{row.name} binds the app server and no tool serves it")


async def tool_defs(
    *,
    control: ControlService,
    broker: BrokerService,
    domain: DomainContext,
    delegate: Delegate | None,
    host: Mapping[str, HostRead] | None = None,
) -> list[ToolDef]:
    """Every agent row of the catalog as a tool for one chat: control operations, the broker's
    reads and `propose_order`, the domain functions, every running app's operations and
    `apps_admin_move`, the host reads in `host` by target, and `delegate` when not None (a Child
    chat passes None). `domain` shares `control`, so no second writer runs."""
    from qmx_broker.server import create_server as broker_server  # noqa: PLC0415
    from qmx_control.server import create_mcp  # noqa: PLC0415
    from qmx_tools.servers import create_server as domain_server  # noqa: PLC0415

    apps = await asyncio.to_thread(served_apps, control)
    schemas = {row.name: schema for row, schema in apps}
    agent = [row for row in rows(row for row, _ in apps) if row.agent]
    save = control.library_save
    domain_servers = [domain_server(group, domain) for group in DOMAIN_GROUPS]
    reads = host or {}
    return [
        *await _bound(
            [row for row in agent if row.binds == "control_op"],
            [create_mcp(control)],
            save,
            by_name=True,
        ),
        *await _bound(
            [row for row in agent if row.binds == "broker"], [broker_server(broker)], save
        ),
        *await _bound([row for row in agent if row.binds == "domain_fn"], domain_servers, save),
        *(_app_server_def(row, control, schemas) for row in agent if row.binds == "app_server"),
        *(
            _host_def(row, reads[row.target])
            for row in agent
            if row.binds == "agent_tool" and row.target in reads
        ),
        *(
            delegate_def(row, delegate)
            for row in agent
            if row.binds == "delegate" and delegate is not None
        ),
    ]


DOMAIN_GROUPS: Final = tuple(dict.fromkeys(row.toolset for row in DOMAIN_ROWS))
"""The domain functions' groups, read from their rows so a new domain toolset reaches chats."""


type Delegate = Callable[[str, str], Awaitable[str]]
"""The harness's helper manager behind the four `delegate` rows: the row's wire name and the
tool call's JSON, answered as JSON. Bound to the calling chat by the harness."""


DELEGATE_SCHEMAS: Final[Mapping[str, Mapping[str, object]]] = MappingProxyType(
    {
        "run": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "The whole job for the helper, in your own words. It starts "
                    "fresh and cannot ask you anything.",
                },
                "profile": {
                    "type": "string",
                    "description": "A provider profile from [providers], for example kimi. "
                    "Leave it out to use role or model, or this chat's own provider.",
                },
                "model": {
                    "type": "string",
                    "description": "A model id the registry or that provider row names.",
                },
                "role": {
                    "type": "string",
                    "description": "A role whose tier picks the model and whose preset picks "
                    "the helper's tools, for example reviewer or extractor.",
                },
                "effort": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "xhigh", "max"],
                    "description": "Thinking effort where the model takes one.",
                },
                "output_schema": {
                    "type": "object",
                    "description": "A JSON Schema the answer must hold to. It gets one "
                    "correction turn, then the raw answer with schema_valid false.",
                },
                "worktree": {
                    "type": "boolean",
                    "description": "Give the helper its own folder beside yours.",
                },
                "group": {
                    "type": "string",
                    "description": "A label so you can list these helpers together.",
                },
                "target": {
                    "type": "string",
                    "enum": ["chat", "cli"],
                    "description": "chat runs a helper chat here; cli runs an agent CLI as a "
                    "local process owned by the handle.",
                },
                "allow_cli": {
                    "type": "boolean",
                    "description": "Allow the cli binary version this tool refused the first "
                    "time, after you have asked the operator.",
                },
            },
            "required": ["task"],
        },
        "list": {
            "type": "object",
            "properties": {
                "group": {"type": "string", "description": "Only helpers with this label."}
            },
        },
        "steer": {
            "type": "object",
            "properties": {
                "handle": {"type": "string", "description": "The helper's handle"},
                "text": {"type": "string", "description": "What to tell it"},
            },
            "required": ["handle", "text"],
        },
        "stop": {
            "type": "object",
            "properties": {
                "handle": {"type": "string", "description": "The helper's handle"},
                "reason": {"type": "string", "description": "Why it is stopping"},
            },
            "required": ["handle"],
        },
    }
)
"""The four `delegate` rows' schemas, by `op`."""


def delegate_def(row: OperationSpec, delegate: Delegate) -> ToolDef:
    """One `delegate` tool: a thin JSON call into the harness's helper manager, which resolves
    the child bundle and returns its handle at once (AD-41). The manager answers a refusal with
    the reason, so the tool reports it rather than raising into the CLI."""

    async def call(arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            answer = await delegate(row.name, json.dumps(arguments))
        except DelegateRefused as refused:
            return failure("refused", str(refused))
        return {"content": [{"type": "text", "text": answer}]}

    return _plain(row, DELEGATE_SCHEMAS.get(row.op, NO_ARGUMENTS), call)


class ToolSurfaceError(RuntimeError):
    """The QMX servers cannot be built from these defs."""


def rule_rows(table: object) -> tuple[Rule, ...]:
    """His list as `Rule`s: each row a `{pattern, ...}` table or a bare pattern string, as
    `ControlService` stores `[rules]`. A row that does not parse is skipped."""
    found: list[Rule] = []
    for row in cast("list[object]", table) if isinstance(table, list) else []:
        text = cast("Mapping[str, object]", row).get("pattern") if isinstance(row, Mapping) else row
        if isinstance(text, str):
            with contextlib.suppress(ValueError):
                found.append(Rule.parse(text))
    return tuple(found)


def is_proposal_writer(target: object) -> bool:
    return getattr(target, "__func__", None) is BrokerService.propose_order


def surface(toolsets: Iterable[str] | None, defs: Iterable[ToolDef]) -> frozenset[str]:
    """The servers a chat has switched on: `toolsets` (None is every core toolset) among the
    toolsets `defs` serve."""
    served = {tool.toolset for tool in defs}
    wanted = CORE_TOOLSETS if toolsets is None else tuple(toolsets)
    return frozenset(server_name(name) for name in wanted if name in served)


def build_servers(
    defs: list[ToolDef],
    *,
    grants: Grants,
    domain_write: DomainWritePolicy,
    enforce_grants: bool = True,
) -> dict[str, McpSdkServerConfig]:
    """One `create_sdk_mcp_server(name="qmx_<toolset>")` per toolset in `defs`. Refuses to
    build on a duplicate or unservable name and on PROPOSE_MONEY on anything but the broker's
    `propose_order` (identity, not name). Every asking tool's handler first consumes a grant for
    its exact arguments and returns an error naming the rule without one.
    `enforce_grants=False` exists for one live check only (`TestMode.grants`)."""
    names = [tool.name for tool in defs]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ToolSurfaceError(f"duplicate QMX tool names: {', '.join(duplicates)}")
    problems = [problem for name in names if (problem := name_problem(name)) is not None]
    if problems:
        raise ToolSurfaceError("; ".join(problems))
    for tool in defs:
        if tool.effect is Effect.PROPOSE_MONEY and not is_proposal_writer(tool.target):
            raise ToolSurfaceError(
                f"{tool.name} is not the broker's propose_order and cannot propose money"
            )
    toolsets: dict[str, list[ToolDef]] = {}
    for tool in defs:
        toolsets.setdefault(tool.toolset, []).append(tool)
    return {
        server_name(toolset): create_sdk_mcp_server(
            server_name(toolset),
            tools=sdk_tools(found, grants, domain_write, enforce_grants=enforce_grants),
        )
        for toolset, found in toolsets.items()
    }


def sdk_tools(
    defs: list[ToolDef],
    grants: Grants,
    domain_write: DomainWritePolicy,
    *,
    enforce_grants: bool = True,
) -> list[SdkMcpTool[Any]]:
    """A server's tools, each named by its op. Each asking tool's handler consumes a grant."""
    return [
        SdkMcpTool(
            tool.op,
            tool.description,
            dict(tool.input_schema),
            _guarded(tool, grants)
            if enforce_grants and asks(tool.effect, domain_write)
            else tool.call,
        )
        for tool in defs
    ]


def _guarded(tool: ToolDef, grants: Grants) -> ToolCall:
    async def call(arguments: dict[str, Any]) -> dict[str, Any]:
        if not grants.consume(tool.full, args_digest(tool.full, arguments)):
            return failure(
                "not_approved",
                f"{tool.name} runs only after you approve these exact arguments, and no "
                "approval was given",
            )
        return await tool.call(arguments)

    return call


def keyring_refs(control: ControlService) -> frozenset[str]:
    """Every `qmx/*` reference named in settings.toml [providers], [brokers] and
    [mcp_servers], plus the fixed entries, casefolded. Names only; nothing is read."""
    found: set[str] = set(FIXED_REFS)

    def walk(value: object) -> None:
        if isinstance(value, str) and value.casefold().startswith("qmx/"):
            found.add(value.casefold())
        elif isinstance(value, Mapping):
            for item in cast("Mapping[str, object]", value).values():
                walk(item)
        elif isinstance(value, list):
            for item in cast("list[object]", value):
                walk(item)

    for section in ("providers", "brokers", "mcp_servers"):
        walk(control.settings_get(section))
    return frozenset(found)


def _posix(path: Path) -> str:
    home = str(Path.home())
    return normalize_path(str(path.resolve()), cwd="/", home=home, case_insensitive=False)


def _both(paths: list[Path]) -> tuple[str, ...]:
    """Each path as written (absolute) and as resolved, so a home behind a junction or link
    matches either spelling."""
    home = str(Path.home())
    return tuple(
        dict.fromkeys(
            normalize_path(str(form), cwd="/", home=home, case_insensitive=False)
            for path in paths
            for form in (path.absolute(), path.resolve())
        )
    )


def secret_files(home: QmxHome) -> list[Path]:
    """Files that hold or may hold a login or a key: every `secret` path of the QMX folder's
    class table (`keys/`, `data/vault/`, `rclone.conf`, both Claude homes' logins and the rest),
    the plan login in both forms under his `~/.claude`, his `~/.claude.json`, and the QMX home's
    `settings.toml`, which a hand edit may put a key in. A table path under `data/` is found
    under the home itself, whatever the home's folder is named."""
    personal = Path.home() / ".claude"
    return [
        *(_in_folder(home, path) for path in secret_paths()),
        *(personal / name for name in (".credentials.json", ".claude.json")),
        Path.home() / ".claude.json",
        home.root / "settings.toml",
    ]


def _in_folder(home: QmxHome, path: str) -> Path:
    """A class-table path, relative to the QMX folder, on disk: `data/` is the home."""
    inner = path.removeprefix("data/")
    return home.root / inner if inner != path else home.layout.root / path


def _secret_globs(home: QmxHome) -> tuple[str, ...]:
    """Each wildcard `secret` rule of the class table under the home as written and as
    resolved, the folder's own path glob-escaped so only the table's wildcards match."""
    found: list[str] = []
    for pattern in secret_globs():
        inner = pattern.removeprefix("data/")
        root, rest = (home.root, inner) if inner != pattern else (home.layout.root, pattern)
        found += [f"{glob.escape(base)}/{rest}" for base in _both([root])]
    return tuple(dict.fromkeys(found))


STORE_FILES: Final = ("control.db", "portfolio.db", "library.db", "memory.db", "runs.db")
"""The QMX home's SQLite stores, each with its `-wal`, `-shm` and `-journal` files."""


def guard_rules(
    defs: list[ToolDef],
    *,
    domain_write: DomainWritePolicy,
    home: QmxHome,
    config_dir: Path,
    keyring_names: frozenset[str],
    unattended: bool,
    external_unattended: frozenset[str],
    workspace: Path | None = None,
    rules: Mapping[str, object] | None = None,
    on: frozenset[str] | None = None,
) -> GuardRules:
    """Derive `GuardRules` from the same defs: `mandatory_asks` are the full names where
    `asks(effect, domain_write)`, and the QMX servers are each toolset's, of which `on` (None
    is all) form the chat's surface. Paths come from `home`, the OS user's home and this
    Python's environment. `workspace` is where a recursive delete runs without asking; `rules`
    is `settings.toml [rules]`, his two lists."""
    personal = Path.home() / ".claude"
    layout = home.layout
    protected = [
        home.plan_dir,
        home.relayed_dir,
        home.chats_dir,
        home.run_dir,
        home.packs_dir,
        layout.keys,
        home.plugin_dir,
        home.root / "engine",
        *(
            home.root / f"{name}{suffix}"
            for name in STORE_FILES
            for suffix in ("", "-wal", "-shm", "-journal")
        ),
        home.root / "settings.toml",
    ]
    lists = rules or {}
    servers = frozenset(server_name(tool.toolset) for tool in defs)
    return GuardRules(
        mandatory_asks=frozenset(tool.full for tool in defs if asks(tool.effect, domain_write)),
        protected_paths=_both(protected),
        qmx_homes=_both([layout.root]),
        writable_paths=_both([home.workspaces_dir, home.agent_memory_dir, layout.cache / "zones"]),
        install_paths=_both([Path(sys.prefix)]),
        secret_paths=_both(secret_files(home)),
        personal_homes=_both([personal]),
        keyring_names=frozenset(name.casefold() for name in keyring_names),
        delete_zones=() if workspace is None else _both([workspace]),
        never=rule_rows(lists.get("never_allow")),
        always=rule_rows(lists.get("always_allow")),
        secret_globs=_secret_globs(home),
        variables=MappingProxyType(
            {
                "HOME": _posix(Path.home()),
                "USERPROFILE": _posix(Path.home()),
                "CLAUDE_CONFIG_DIR": _posix(config_dir),
            }
        ),
        case_insensitive=sys.platform in ("win32", "darwin"),
        unattended=unattended,
        external_unattended=external_unattended,
        qmx_servers=servers,
        surface=set(servers if on is None else on & servers),
    )


VET_TIMEOUT_S: Final = 30.0


@dataclass(frozen=True)
class VettedServers:
    """External MCP servers that passed `vet_mcp_servers`, as SDK configs with the tool names
    vetting saw, and each refused server with its reason. Only `configs` reach `mcp_servers`;
    `strict_mcp_config=True` makes the CLI ignore every other MCP config (02a section 7)."""

    configs: Mapping[str, McpServerConfig]
    tools: Mapping[str, frozenset[str]]
    refused: Mapping[str, str]


class VetCache:
    """Tool names vetted per config digest, for one harness. A changed row has a new digest
    and is vetted again. A server that changes its tools under the same row is caught after
    connect (`unvetted_tools`)."""

    def __init__(self) -> None:
        self._tools: dict[str, frozenset[str]] = {}

    def get(self, digest: str) -> frozenset[str] | None:
        return self._tools.get(digest)

    def put(self, digest: str, tools: frozenset[str]) -> None:
        self._tools[digest] = tools


def config_digest(config: McpServerConfig) -> str:
    body = json.dumps(config, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode()).hexdigest()


SERVER_NAME: Final = re.compile(r"[A-Za-z0-9-]+(?:_[A-Za-z0-9-]+)*")
"""An external MCP server name the CLI keeps unchanged in its tool names, with no `__`."""


type Secret = Callable[[str], str | None]
"""Reads one `qmx/*` Credential Manager entry, or None when it holds nothing."""


WIRED_CREDENTIALS: Final = frozenset({"qmx/ctrader-mcp"})
"""The stored credentials a server row may send as its Bearer. Any other ref, `qmx/firecrawl`
among them, stays refused, so no other key of his leaves Credential Manager for a row's url."""


def stored_secret(ref: str) -> str | None:
    return keyring.get_password(ref, ref.removeprefix("qmx/"))


def server_config(
    name: str, row: Mapping[str, object], secret: Secret = stored_secret
) -> McpServerConfig:
    """One settings.toml [mcp_servers] row as an SDK config: `command` with `args` and `env`
    for stdio, or `url` for HTTP. An HTTP row's `credential_ref` is read from Credential Manager
    here, at launch, into an `Authorization` header that only the CLI and vetting receive.
    Raises ValueError naming what is wrong, NotOffered when the entry holds no token."""
    if is_qmx_server(name):
        raise ValueError(f"the names {SERVER} and {SERVER}_* belong to QMX's own tools")
    if not SERVER_NAME.fullmatch(name):
        raise ValueError(
            "a server name takes letters, digits, - and single _ between them, so its tools "
            "read as mcp__<server>__<tool>"
        )
    venue, ref = row.get("venue"), row.get("credential_ref") or None
    if venue is not None and venue not in VENUES:
        raise ValueError(f"venue {venue!r} is not one QMX checks ({', '.join(sorted(VENUES))})")
    if ref is not None and ref not in WIRED_CREDENTIALS:
        raise ValueError("servers that need a stored credential are not wired yet")
    command, url = row.get("command"), row.get("url")
    if isinstance(command, str) and command and ref is not None:
        raise ValueError("a stored credential reaches only an HTTP server's Authorization header")
    if isinstance(command, str) and command:
        args = row.get("args", [])
        env = row.get("env", {})
        if not isinstance(args, list) or not isinstance(env, dict):
            raise ValueError("args must be a list and env a table")
        return {
            "type": "stdio",
            "command": command,
            "args": [str(arg) for arg in cast("list[object]", args)],
            "env": {str(k): str(v) for k, v in cast("dict[object, object]", env).items()},
        }
    if isinstance(url, str) and url and isinstance(ref, str):
        if not plain_https(url):
            raise ValueError(
                "a stored credential goes only to an HTTPS url (plain HTTP on the loopback) with "
                "no user, password, query or fragment"
            )
        if venue is None:
            raise ValueError("a row with a stored credential names its venue")
        token = (secret(ref) or "").strip()
        if not token or any(char.isspace() for char in token):
            raise NotOffered(f"{ref} holds no single token in Credential Manager; paste one")
        return {"type": "http", "url": url, "headers": {"Authorization": f"Bearer {token}"}}
    if isinstance(url, str) and url:
        return {"type": "http", "url": url}
    raise ValueError("a server needs a command or a url")


type Check = Callable[[ServerCall, frozenset[str]], Awaitable[object]]
"""Run on the vetting session after its tools are listed; raises to refuse the server."""


async def _list_tools(config: McpServerConfig, check: Check | None = None) -> list[Any]:
    from httpx2 import AsyncClient, Response, Timeout  # noqa: PLC0415
    from mcp import ClientSession, StdioServerParameters  # noqa: PLC0415
    from mcp.client.stdio import stdio_client  # noqa: PLC0415
    from mcp.client.streamable_http import streamable_http_client  # noqa: PLC0415
    from mcp.types import PaginatedRequestParams  # noqa: PLC0415

    statuses: list[int] = []

    async def seen(response: Response) -> None:
        statuses.append(response.status_code)

    async with AsyncExitStack() as stack:
        spec = cast("dict[str, Any]", config)
        if spec["type"] == "stdio":
            parameters = StdioServerParameters(
                command=spec["command"], args=spec["args"], env=spec["env"] or None
            )
            streams = await stack.enter_async_context(stdio_client(parameters))
        else:
            client = await stack.enter_async_context(
                AsyncClient(
                    headers=spec.get("headers"),
                    timeout=Timeout(VET_TIMEOUT_S),
                    event_hooks={"response": [seen]},
                )
            )
            streams = await stack.enter_async_context(
                streamable_http_client(spec["url"], http_client=client)
            )
        session = await stack.enter_async_context(ClientSession(streams[0], streams[1]))
        try:
            await session.initialize()
        except Exception:
            if 401 in statuses:
                raise NotOffered(EXPIRED) from None
            raise
        found: list[Any] = []
        cursor: str | None = None
        while True:
            params = PaginatedRequestParams(cursor=cursor) if cursor else None
            page = await session.list_tools(params=params)
            found += page.tools
            cursor = page.next_cursor
            if not cursor:
                break

        async def call(tool: str) -> object:
            result = await session.call_tool(tool, {})
            if result.is_error:
                return None
            if result.structured_content is not None:
                return result.structured_content
            text = next((block.text for block in result.content if block.type == "text"), "")
            try:
                return json.loads(text)
            except ValueError:
                return None

        if check is not None:
            await check(call, frozenset(str(tool.name) for tool in found))
        return found


@dataclass(frozen=True)
class VettedServer:
    config: McpServerConfig
    tools: frozenset[str]


def _first(group: BaseExceptionGroup[NotOffered]) -> NotOffered:
    """The first refusal in a group the MCP client's task groups wrapped it in."""
    found = group.exceptions[0]
    return found if isinstance(found, NotOffered) else _first(found)


async def vet_server(
    name: str,
    row: Mapping[str, object],
    cache: VetCache,
    *,
    accounts: AccountWorlds | None = None,
    secret: Secret = stored_secret,
) -> VettedServer:
    """Start one declared server with the Python MCP client and list every page of its tools. A
    config already in `cache` is not started again, except a row naming a `venue`: its demo
    check (`demo_only`) runs at every launch. Raises ValueError, NotOffered among them."""
    config = await asyncio.to_thread(server_config, name, row, secret)
    digest = config_digest(config)
    checked = row.get("venue") is not None
    cached = None if checked else cache.get(digest)
    if cached is not None:
        return VettedServer(config, cached)

    async def demo(call: ServerCall, tools: frozenset[str]) -> object:
        return await demo_account(call, tools, accounts)

    try:
        listed = await asyncio.wait_for(
            _list_tools(config, demo if checked else None), VET_TIMEOUT_S
        )
    except* NotOffered as group:
        raise _first(group) from None
    tools = frozenset(str(tool.name) for tool in listed)
    cache.put(digest, tools)
    return VettedServer(config, tools)


async def vet_mcp_servers(
    declared: Mapping[str, object],
    cache: VetCache,
    *,
    accounts: AccountWorlds | None = None,
    secret: Secret = stored_secret,
) -> VettedServers:
    """Before any launch uses them: vet every enabled server in settings.toml [mcp_servers],
    all at once. A server that cannot be listed is refused and never launched (H58), and so is
    a broker server whose session is not bound to a demo account record (`demo_only`). A tool
    the CLI loads that vetting never saw refuses the launch."""
    rows = {
        name: cast("Mapping[str, object]", row)
        for name, row in declared.items()
        if isinstance(row, Mapping) and cast("Mapping[str, object]", row).get("enabled", True)
    }
    results = await asyncio.gather(
        *(
            vet_server(name, row, cache, accounts=accounts, secret=secret)
            for name, row in rows.items()
        ),
        return_exceptions=True,
    )
    configs: dict[str, McpServerConfig] = {}
    tools: dict[str, frozenset[str]] = {}
    refused: dict[str, str] = {}
    for name, result in zip(rows, results, strict=True):
        match result:
            case VettedServer():
                configs[name], tools[name] = result.config, result.tools
            case NotOffered():
                refused[name] = str(result)
            case Exception():
                refused[name] = f"it could not be vetted ({type(result).__name__}: {result})"
            case _:
                raise result
    return VettedServers(
        MappingProxyType(configs), MappingProxyType(tools), MappingProxyType(refused)
    )


def unvetted_tools(status: McpStatusResponse, vetted: Mapping[str, frozenset[str]]) -> list[str]:
    """`server: tool` for each tool the CLI loaded from a vetted server that vetting never
    saw. The CLI may report a name bare or as `mcp__<server>__<tool>`."""
    return sorted(
        f"{server['name']}: {bare}"
        for server in status["mcpServers"]
        if server["name"] in vetted
        for tool in server.get("tools", [])
        if (bare := tool["name"].removeprefix(f"mcp__{server['name']}__"))
        not in vetted[server["name"]]
    )
