# REFERENCES: official docs for the rebuild packets

All URLs below were fetched on 2026-10-07 and returned content (HTTP 200) unless marked **UNVERIFIED**.
Versions are the latest on PyPI / GitHub releases on that date. Signatures are paraphrased from the official pages, not copied.

## How to use this file

1. Before coding, `curl -sL <url> -o "$SCRATCH/<name>.md"` the machine-readable URLs for your packet into a scratch folder **outside the repo** (never commit them).
2. Read the relevant pages before writing code; when a parameter name matters, `grep` the downloaded page for it.
3. Never guess an API. If a name is not in the fetched docs, stop and write it under "Found, not fixed" in the PR.

Tip: most LangChain pages accept a `.md` suffix (`https://docs.langchain.com/oss/python/<path>.md`), and every API reference page accepts `.md` too (`https://reference.langchain.com/python/<pkg>/<module>/<Name>.md`). Mintlify sites (LangChain, FastMCP, MCP, E2B, Firecrawl) serve `llms.txt` indexes.

---

## 0. Drift between the docs and DESIGN.md / packets (read this first)

These are facts found in the official docs that change what the packets say. Follow the docs; note the change in the PR.

| # | Finding | Affects |
|---|---|---|
| D1 | `langchain-mcp-adapters` is **no longer maintained** (README banner). MCP now ships in `langchain.mcp` (`langchain[mcp]>=1.4.0`, beta, emits `LangChainBetaWarning`). `MultiServerMCPClient` is replaced by the async context manager `MCPAdapter`. Use `MCPAdapter` unless the reviewer says otherwise. | P06, P09, P15, P19 |
| D2 | FastMCP is now **4.x** (4.0.11), not 3.x. v3 docs live under `https://gofastmcp.com/v3/...`. The official `mcp` SDK is 2.x and renamed its built-in server class to `MCPServer`. `langchain.mcp` is built on FastMCP 4, so use `fastmcp>=4,<5`. | P09, P11, P12, P18 |
| D3 | Deep Agents `AsyncSubAgent` talks to an **Agent Protocol server** (`graph_id`, optional `url`; with no `url` it uses in-process ASGI inside a co-deployed LangGraph deployment). DESIGN §8 says no LangGraph Agent Server. Do not build async sub-agents until the reviewer rules on this. | P06, P15 |
| D4 | `CodeInterpreterMiddleware` comes from `langchain_quickjs` (`deepagents[quickjs]`). It runs **JavaScript in QuickJS**, not Python. Fan-out from code uses the `task()` global (dynamic subagents). Python data work needs a sandbox backend instead. | P06, P15 |
| D5 | Async sub-agents are passed in the same `subagents=` list as sync ones; there is no separate `async_subagents=` parameter. Map the AgentSpec field onto that list. | P06 |
| D6 | `create_deep_agent(tools=...)` is **additive** to the built-in tools (ls, read_file, write_file, edit_file, glob, grep, execute, task). To hide built-ins use a `HarnessProfile(excluded_tools=...)`; to turn off the auto-added `general-purpose` sub-agent set `GeneralPurposeSubagentProfile(enabled=False)` on the harness profile. | P06, P08 |
| D7 | Amp SDK: with `executor="orb"` or `"runner"`, the options `mcp_config`, `skills` and `enabled_tools` are **ignored** (with a warning) and the prompt must be a plain string. MCP servers for remote runs are configured in the Amp project or on the runner. | P21 |
| D8 | `GenericFakeChatModel` has no `bind_tools` override (checked in langchain-core source). If an agent with tools calls `bind_tools`, subclass the fake and return `self` from `bind_tools`. | P06–P10, P15 |
| D9 | Human-in-the-loop (`interrupt_on`, `HumanInTheLoopMiddleware`, `interrupt()`) **requires a checkpointer**; thread limits in the call-limit middleware need one too. | P06, P08, P10, P15 |
| D10 | Litestream 0.5.x allows **one `replica` per database**; the `replicas:` array is deprecated. | P17 |
| D11 | FastAPI has native SSE since 0.135 (`fastapi.sse.EventSourceResponse`, `ServerSentEvent`). No extra SSE package is needed. | P11, P15 |

---

## 1. LangChain v1 (agents, middleware, models)

- Docs: https://docs.langchain.com/oss/python/langchain/agents , https://docs.langchain.com/oss/python/langchain/middleware/overview
- Machine-readable (verified 2026-10-07):
  - Index: https://docs.langchain.com/llms.txt → Python build index https://docs.langchain.com/_llms/agent-development-lifecycle/build/python.md
  - https://docs.langchain.com/oss/python/langchain/agents.md
  - https://docs.langchain.com/oss/python/langchain/middleware/built-in.md
  - https://docs.langchain.com/oss/python/langchain/middleware/custom.md
  - https://reference.langchain.com/python/langchain-core/callbacks/base/AsyncCallbackHandler/on_chat_model_start.md (P07 pre-compression callback)
  - https://docs.langchain.com/oss/python/langchain/models.md
  - https://docs.langchain.com/oss/python/langchain/human-in-the-loop.md
  - https://docs.langchain.com/oss/python/langchain/test/unit-testing.md
  - https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model.md
  - https://reference.langchain.com/python/langchain-anthropic/chat_models/ChatAnthropic.md
  - https://reference.langchain.com/python/langchain-openai/chat_models/base/ChatOpenAI.md
  - https://reference.langchain.com/python/langchain-core/language_models/fake_chat_models/GenericFakeChatModel.md
  - Full dump (15 MB, use only with grep): https://docs.langchain.com/llms-full.txt
- Key APIs:
  - `langchain.agents.create_agent(model, tools, *, middleware=[...], checkpointer=..., ...)`: the base agent loop Deep Agents builds on.
  - `langchain.chat_models.init_chat_model("provider:model", **kw)`: also accepts `model_provider=` and `base_url=` (OpenAI-compatible endpoints use `model_provider="openai"` plus `base_url`). `configurable_fields=` makes a runtime-switchable model.
  - `ChatAnthropic(model=..., base_url=..., api_key=...)` and `ChatOpenAI(model=..., base_url=..., api_key=...)`: point at CLIProxyAPI (section 7).
  - Middleware classes in `langchain.agents.middleware`:
    - `ModelCallLimitMiddleware(thread_limit=, run_limit=, exit_behavior="end"|...)`
    - `ToolCallLimitMiddleware(tool_name=None, thread_limit=, run_limit=)` (omit `tool_name` for a global limit)
    - `ModelFallbackMiddleware(first_model, *additional_models)` (strings or model instances, tried in order)
    - `ModelRetryMiddleware(max_retries=2, retry_on=..., on_failure="continue"|"error"|callable, backoff_factor=2.0, initial_delay=1.0, max_delay=60.0, jitter=True)`
    - `SummarizationMiddleware(model=..., trigger=("tokens", N) | fraction..., keep=("messages", N))`
    - `ContextEditingMiddleware(edits=[ClearToolUsesEdit(trigger=<tokens>, keep=<n>)], token_count_method="approximate"|"model")`
    - `HumanInTheLoopMiddleware(interrupt_on={"tool": {"allowed_decisions": ["approve","edit","reject"]}, "other": False})`
  - Custom hooks (decorators or `AgentMiddleware` subclass): `@before_agent`, `@before_model`, `@after_model`, `@after_agent`, `@wrap_model_call`, `@wrap_tool_call`, `@dynamic_prompt`. A router swaps models with `handler(request.override(model=...))` inside `@wrap_model_call`.
  - Resume an approval: invoke again with `Command(resume={"decisions": [{"type": "approve"}]})` and the same `thread_id`.
  - Tests: `GenericFakeChatModel(messages=iter([AIMessage(..., tool_calls=[...]), "text"]))` plus `InMemorySaver` (see D8).
- Pin: `langchain==1.4.3`, `langchain-core==1.6.7`, `langchain-anthropic==1.7.5`, `langchain-openai==1.6.7`.
- Packets: P06, P07, P08, P10, P15, P20.

## 2. Deep Agents

- Docs: https://docs.langchain.com/oss/python/deepagents/overview
- Machine-readable (verified 2026-10-07):
  - https://docs.langchain.com/oss/python/deepagents/overview.md
  - https://docs.langchain.com/oss/python/deepagents/customization.md
  - https://docs.langchain.com/oss/python/deepagents/subagents.md
  - https://docs.langchain.com/oss/python/deepagents/async-subagents.md
  - https://docs.langchain.com/oss/python/deepagents/backends.md
  - https://docs.langchain.com/oss/python/deepagents/sandboxes.md
  - https://docs.langchain.com/oss/python/deepagents/permissions.md
  - https://docs.langchain.com/oss/python/deepagents/skills.md
  - https://docs.langchain.com/oss/python/deepagents/memory.md
  - https://docs.langchain.com/oss/python/deepagents/human-in-the-loop.md
  - https://docs.langchain.com/oss/python/deepagents/interpreters.md (CodeInterpreterMiddleware)
  - https://docs.langchain.com/oss/python/deepagents/mcp.md , https://docs.langchain.com/oss/python/deepagents/models.md , https://docs.langchain.com/oss/python/deepagents/streaming.md
  - Reference index: https://docs.langchain.com/oss/python/reference/deepagents-python.md
  - https://reference.langchain.com/python/deepagents/graph/create_deep_agent.md
  - https://reference.langchain.com/python/deepagents/middleware/subagents/SubAgent.md
  - https://reference.langchain.com/python/deepagents/middleware/subagents/CompiledSubAgent.md
  - https://reference.langchain.com/python/deepagents/middleware/async_subagents/AsyncSubAgent.md
  - https://reference.langchain.com/python/deepagents/backends/composite/CompositeBackend.md
  - https://reference.langchain.com/python/deepagents/backends/store/StoreBackend.md
  - https://reference.langchain.com/python/deepagents/middleware/summarization/create_summarization_middleware.md (P07 preserves library compaction and history offloading)
  - https://reference.langchain.com/python/deepagents/middleware/filesystem/FilesystemPermission.md
  - Repo README: https://raw.githubusercontent.com/langchain-ai/deepagents/main/README.md
- Key APIs:
  - `create_deep_agent(model, tools=None, *, system_prompt, middleware=(), subagents=None, skills=None, memory=None, permissions=None, backend=None, interrupt_on=None, response_format=None, state_schema=None, context_schema=None, checkpointer=None, store=None, debug=False, name=None, cache=None)` → `CompiledStateGraph`. Always pass `model` (relying on the default is deprecated).
  - `SubAgent` (TypedDict): `name`, `description` required; optional `tools`, `model`, `middleware`, `interrupt_on`, `skills`, `permissions`, `response_format`, `system_prompt`, `mode` (`"isolated"|"fork"`). Its `tools` are the sub-agent's own list.
  - `CompiledSubAgent(name, description, runnable, mode=...)`: wrap any LangGraph graph (P10 workflows) as a sub-agent.
  - `AsyncSubAgent(name, description, graph_id, url=None, headers=None)`: gives the supervisor `start_async_task`, `check_async_task`, `update_async_task`, `cancel_async_task`, `list_async_tasks`. See D3.
  - Backends (`deepagents.backends`): `StateBackend()`, `FilesystemBackend(...)`, `LocalShellBackend(...)`, `StoreBackend(namespace=<callable(runtime)->tuple>, store=None)`, `CompositeBackend(default, routes={"/memories/": ..., "/artifacts/": ...}, artifacts_root="/")`. Route prefixes start and end with `/`. Custom backends implement `BackendProtocol` (sandbox ones `SandboxBackendProtocol` / subclass `BaseSandbox`); `execute` only works on sandbox backends.
  - Sandbox backends (separate packages): `langchain_modal.ModalSandbox(sandbox=modal.Sandbox)`, `langchain_e2b.E2BSandbox(...)`, `langchain_daytona.DaytonaSandbox(...)`, `deepagents.backends.LangSmithSandbox`.
  - `FilesystemPermission(operations=["read"|"write"], paths=[globs], mode="allow"|"deny"|"interrupt")`: first match wins; no match means allowed.
  - `skills=["./skills/"]`: each path is a folder of skill folders, each with a `SKILL.md` (YAML `name`, `description`). Progressive disclosure: only frontmatter goes in the prompt.
  - `memory=["/memories/AGENTS.md"]`: files loaded into the prompt via `MemoryMiddleware`; route `/memories/` to a `StoreBackend` to persist.
  - `interrupt_on={"tool": True | {"allowed_decisions": [...]}}` plus a checkpointer.
  - `CodeInterpreterMiddleware(ptc=[tool names])` from `langchain_quickjs` (see D4).
- Pin: `deepagents==0.7.22` (requires Python >=3.11,<4.0). Sandbox adapters: `langchain-modal==0.0.6`, `langchain-e2b==0.0.6`, `langchain-quickjs==0.3.8`.
- Packets: P06, P07, P08, P10, P15, P20.

## 3. LangGraph (graphs, interrupts, checkpointers, stores)

- Docs: https://docs.langchain.com/oss/python/langgraph/graph-api
- Machine-readable (verified 2026-10-07):
  - https://docs.langchain.com/oss/python/langgraph/graph-api.md
  - https://docs.langchain.com/oss/python/langgraph/use-graph-api.md
  - https://docs.langchain.com/oss/python/langgraph/interrupts.md
  - https://docs.langchain.com/oss/python/langgraph/persistence.md
  - https://docs.langchain.com/oss/python/langgraph/checkpointers.md
  - https://docs.langchain.com/oss/python/langgraph/stores.md
  - https://docs.langchain.com/oss/python/langgraph/add-memory.md
  - https://docs.langchain.com/oss/python/langgraph/streaming.md
  - https://reference.langchain.com/python/langgraph/graph/state/StateGraph.md
  - https://reference.langchain.com/python/langgraph/types/Send.md
  - https://reference.langchain.com/python/langgraph/types/interrupt.md
  - https://reference.langchain.com/python/langgraph/types/Command.md
  - SQLite saver README: https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/checkpoint-sqlite/README.md
  - SqliteStore source (docstring has usage): https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/checkpoint-sqlite/langgraph/store/sqlite/base.py
- Key APIs:
  - `StateGraph(State)`, `.add_node(name, fn)`, `.add_edge(a, b)`, `.add_conditional_edges(src, router, path_map=None)`, `START`/`END`, `.compile(checkpointer=..., store=...)`.
  - `Send(node, arg)`: return a list of these from a conditional edge to fan out (P10 `parallel`).
  - `interrupt(value, *, response_schema=None)`: pauses a node; the value from `Command(resume=...)` becomes its return value.
  - `Command(update=None, resume=None, goto=(), graph=None)`: only `resume` is meant as invoke input; `update`/`goto` are for returning from nodes.
  - Every run with a checkpointer needs `config={"configurable": {"thread_id": ...}}`; loops are bounded by `recursion_limit` in config.
  - `from langgraph.checkpoint.sqlite import SqliteSaver`: `SqliteSaver(sqlite3.connect(path))` or `with SqliteSaver.from_conn_string(path) as cp:`; async: `langgraph.checkpoint.sqlite.aio.AsyncSqliteSaver`.
  - `from langgraph.store.sqlite import SqliteStore` (also `AsyncSqliteStore`): `SqliteStore(conn, index=None, ttl=None)` or `from_conn_string`; call `.setup()` once; `.put(namespace_tuple, key, dict)`, `.get(ns, key)`, `.search(ns, query=..., limit=...)`, `.delete(ns, key)`. Semantic search only with `index=`.
  - Testing: `langgraph.checkpoint.memory.InMemorySaver`.
- Pin: `langgraph==1.2.14`, `langgraph-checkpoint==4.2.0`, `langgraph-checkpoint-sqlite==3.1.1` (provides both saver and store).
- Packets: P06, P07, P10, P15, P21.

## 4. LangChain MCP client (`langchain.mcp`, formerly langchain-mcp-adapters)

- Docs: https://docs.langchain.com/oss/python/langchain/mcp/index
- Machine-readable (verified 2026-10-07):
  - https://docs.langchain.com/oss/python/langchain/mcp/index.md
  - https://docs.langchain.com/oss/python/langchain/mcp/connections.md
  - https://docs.langchain.com/oss/python/langchain/mcp/tools.md
  - https://docs.langchain.com/oss/python/langchain/mcp/auth.md
  - Migration guide: https://docs.langchain.com/oss/python/migrate/langchain-mcp-adapters.md
  - Old package README (unmaintained): https://raw.githubusercontent.com/langchain-ai/langchain-mcp-adapters/main/README.md
- Key APIs:
  - `from langchain.mcp import MCPAdapter`; `async with MCPAdapter(target) as a: tools = await a.list_tools()`. Tools stay usable after the context exits.
  - `target` can be a URL, a `Path` (stdio), an in-process FastMCP server (good for tests), a prebuilt `fastmcp.Client`, a `ClientGroup`, or an `MCPConfig` dict `{"mcpServers": {"name": {"command":..., "args": [...]} | {"url": ...}}}`. Transport is inferred; multi-server tools are prefixed `{server}_{tool}`.
  - Headers/auth go on a `fastmcp` transport or `fastmcp.Client(..., auth="<bearer>")`.
  - MCP `isError=True` becomes a `ToolMessage(status="error")`; transport failures raise.
  - Interception is done with `@wrap_tool_call` middleware; MCP provenance is in `tool.metadata["mcp"]` (includes annotations).
  - Not wrapped: prompts, resources, sampling, roots. Use the FastMCP client for prompts/resources.
  - Legacy (only if the reviewer keeps the old package): `MultiServerMCPClient({...}).get_tools()` in `langchain-mcp-adapters==0.3.2`.
- Pin: `langchain[mcp]==1.4.3` (pulls FastMCP 4).
- Packets: P06, P09, P15, P19.

## 5. MCP: FastMCP 4, the official Python SDK, and MCP Apps

- Docs: https://gofastmcp.com , https://modelcontextprotocol.io , https://py.sdk.modelcontextprotocol.io
- Machine-readable (verified 2026-10-07):
  - FastMCP index: https://gofastmcp.com/llms.txt (full: https://gofastmcp.com/llms-full.txt, 2.9 MB)
  - https://gofastmcp.com/getting-started/whats-new.md (FastMCP 4 changes)
  - https://gofastmcp.com/servers/tools.md , https://gofastmcp.com/servers/testing.md
  - https://gofastmcp.com/deployment/running-server.md , https://gofastmcp.com/deployment/http.md
  - https://gofastmcp.com/integrations/fastapi.md , https://gofastmcp.com/servers/auth/token-verification.md
  - https://gofastmcp.com/apps/overview.md , https://gofastmcp.com/apps/low-level.md
  - https://gofastmcp.com/clients/client.md , https://gofastmcp.com/clients/transports.md
  - MCP spec index: https://modelcontextprotocol.io/llms.txt ; transports: https://modelcontextprotocol.io/specification/2025-11-25/basic/transports.md
  - MCP Apps: https://modelcontextprotocol.io/extensions/apps/overview.md , https://modelcontextprotocol.io/extensions/apps/build.md
  - MCP Apps spec (stable 2026-01-26): https://raw.githubusercontent.com/modelcontextprotocol/ext-apps/main/specification/2026-01-26/apps.mdx ; SDK README: https://raw.githubusercontent.com/modelcontextprotocol/ext-apps/main/README.md
  - Official SDK: https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md , https://py.sdk.modelcontextprotocol.io/llms.txt
- Key APIs (FastMCP 4):
  - `mcp = FastMCP("name")`; `@mcp.tool` (optional `annotations=` with hints such as `readOnlyHint`/`destructiveHint`), `@mcp.resource("uri")`, `@mcp.prompt`.
  - Run: `mcp.run()` (stdio default), `mcp.run(transport="http", host=, port=)`, `await mcp.run_async(...)`. SSE transport is deprecated in the spec.
  - ASGI: `mcp_app = mcp.http_app(path="/mcp")`; mount in FastAPI with `FastAPI(lifespan=mcp_app.lifespan)` and `app.mount("/x", mcp_app)`. `FastMCP.from_fastapi(app=...)` generates an MCP server from REST routes.
  - Tests: `async with Client(mcp) as c: await c.list_tools(); await c.call_tool(name, args)` (in-memory). Pass a `Path`, not a bare string, for stdio scripts (the string form warns).
  - Apps: `from fastmcp.apps import AppConfig`; `@mcp.tool(app=AppConfig(resource_uri="ui://app/view.html"))` and `@mcp.resource("ui://app/view.html")` returning HTML. Spec: tool `_meta.ui.resourceUri`, MIME type `text/html;profile=mcp-app`, CSP in `_meta.ui.csp`, rendered in a sandboxed iframe. Host side uses `@modelcontextprotocol/ext-apps/app-bridge` (npm), view side `@modelcontextprotocol/ext-apps`.
- Official SDK note: `mcp` 2.x exposes `mcp.server.MCPServer` and `mcp.Client`; QMX uses FastMCP (D2).
- Pin: `fastmcp==4.0.11` (via `langchain[mcp]`), `mcp==2.3.0` only if needed directly.
- Packets: P09, P11, P12, P15, P18, P19.

## 6. FastAPI

- Docs: https://fastapi.tiangolo.com (no llms.txt: `/llms.txt` returned 404)
- Machine-readable, raw markdown from the repo (verified 2026-10-07):
  - SSE: https://raw.githubusercontent.com/fastapi/fastapi/master/docs/en/docs/tutorial/server-sent-events.md
  - WebSockets: https://raw.githubusercontent.com/fastapi/fastapi/master/docs/en/docs/advanced/websockets.md
  - Security reference: https://raw.githubusercontent.com/fastapi/fastapi/master/docs/en/docs/reference/security/index.md
  - Security intro: https://raw.githubusercontent.com/fastapi/fastapi/master/docs/en/docs/tutorial/security/first-steps.md
  - CORS: https://raw.githubusercontent.com/fastapi/fastapi/master/docs/en/docs/tutorial/cors.md
  - Testing: https://raw.githubusercontent.com/fastapi/fastapi/master/docs/en/docs/tutorial/testing.md , https://raw.githubusercontent.com/fastapi/fastapi/master/docs/en/docs/advanced/testing-websockets.md
  - Custom responses (StreamingResponse): https://raw.githubusercontent.com/fastapi/fastapi/master/docs/en/docs/advanced/custom-response.md
- Key APIs:
  - SSE: `from fastapi.sse import EventSourceResponse, ServerSentEvent`; route with `response_class=EventSourceResponse` that `yield`s items (JSON in `data:`), or yields `ServerSentEvent(data=..., event=..., id=..., retry=...)`; `raw_data=` for unencoded text; honour `Last-Event-ID` on reconnect.
  - WebSockets: `@app.websocket("/ws")`, `await ws.accept()`, `receive_text()/send_json()`, `WebSocketDisconnect`.
  - Bearer auth: `HTTPBearer()` dependency returns `HTTPAuthorizationCredentials` (`.scheme`, `.credentials`).
  - CORS: `app.add_middleware(CORSMiddleware, allow_origins=[ui_origin], ...)`.
  - Tests: `fastapi.testclient.TestClient(app)`; `client.websocket_connect(...)`.
- Pin: `fastapi==0.142.2` (SSE needs >=0.135).
- Packets: P11, P15, P21.

## 7. CLIProxyAPI (default model provider)

- Docs: https://github.com/router-for-me/CLIProxyAPI , guides at https://help.router-for.me/ (HTML, no llms.txt)
- Machine-readable (verified 2026-10-07):
  - README: https://raw.githubusercontent.com/router-for-me/CLIProxyAPI/main/README.md
  - Config template: https://raw.githubusercontent.com/router-for-me/CLIProxyAPI/main/config.example.yaml
  - Docker: https://raw.githubusercontent.com/router-for-me/CLIProxyAPI/main/docker-compose.yml , https://raw.githubusercontent.com/router-for-me/CLIProxyAPI/main/Dockerfile
  - Repo docs/: https://raw.githubusercontent.com/router-for-me/CLIProxyAPI/main/docs/management-api-v8.md , `.../docs/sdk-usage.md`, `.../docs/sdk-access.md`, `.../docs/sdk-advanced.md`, `.../docs/sdk-watcher.md`
  - Guide sources (English): https://raw.githubusercontent.com/router-for-me/CLIProxyAPIDocs/main/docs/en/introduction/quick-start.md , `.../configuration/basic.md`, `.../configuration/options.md`, `.../docker/docker-compose.md`, `.../agent-client/claude-code.md`, `.../agent-client/codex.md`, `.../management/apiv8.md`
- Key facts:
  - Config is `config-version: 8`. Default port `server.port: 8317`; `server.host: ""` binds all interfaces (use `127.0.0.1` on the laptop).
  - Client keys: `access.api-keys: [...]` (these are what QMX sends, not upstream keys). OAuth token files: `oauth.auth-dir` (default `~/.cli-proxy-api`). Management API needs `management.secret-key`.
  - Claude-style base URL: `http://127.0.0.1:8317` (no `/v1`) → `ChatAnthropic(base_url=..., api_key=<access key>)`.
  - OpenAI-style base URL: `http://127.0.0.1:8317/v1` → `ChatOpenAI(base_url=..., api_key=...)`. Model list for Settings: `GET /v1/models` with `Authorization: Bearer <key>`.
  - Logins: `cli-proxy-api --claude-login`, `--codex-login` (see docker-compose guide). Docker image `eceasy/cli-proxy-api`, mounts `config.yaml` and the auth dir.
- Pin: track the GitHub release used on the node; record it in the PR.
- Packets: P06, P21.

## 8. Amp SDK, runners, orbs

- Docs: https://ampcode.com/docs/sdk , https://ampcode.com/docs/cli/runners , https://ampcode.com/docs/orbs (HTML; the `.md` suffix returns 404)
- Machine-readable (verified 2026-10-07): index https://ampcode.com/llms.txt; raw pages use `/docs/markdown/...`:
  - https://ampcode.com/docs/markdown/sdk , https://ampcode.com/docs/markdown/sdk/python
  - https://ampcode.com/docs/markdown/cli/runners
  - https://ampcode.com/docs/markdown/orbs , https://ampcode.com/docs/markdown/orbs/customizing , https://ampcode.com/docs/markdown/orbs/sizes-and-costs
  - https://ampcode.com/docs/markdown/customize/mcp , https://ampcode.com/docs/markdown/pricing
- Key APIs:
  - `from amp_sdk import execute, AmpOptions, create_user_message`.
  - `async for msg in execute(prompt, AmpOptions(...))`: streams `system` (init: `session_id`, tools, MCP server status), `assistant`, and `result` messages (`is_error`, `result`).
  - `AmpOptions` fields used by P21: `executor="local"|"orb"|"runner"`, `runner_id`, `runner_dir` (absolute), `project` (orb only), `title`, `labels`, `continue_thread` (bool or thread id), `env`, `mode`, `effort`, `visibility`, `mcp_config` (local only, see D7).
  - Runner: `amp --no-tui --runner-id <hostname-style-id>` serves remotely created threads in the current dir; `amp runner dirs add|list|remove`.
  - Orbs: `.agents/setup` prepares new orbs (snapshotted), `.agents/resume` runs after each wake; billed per minute, pause when idle.
  - MCP in orbs can authenticate with an Amp ID token (`amp orb id-token --audience <url>`).
- Pin: `amp-sdk==0.1.20260918210324` (needs the Amp CLI installed; `AMP_CLI_PATH` overrides).
- Packets: P21.

## 9. Modal sandboxes

- Docs: https://modal.com/docs/guide/sandboxes
- Machine-readable (verified 2026-10-07): https://modal.com/llms.txt (full 2.4 MB: https://modal.com/llms-full.txt)
  - https://modal.com/docs/guide/sandboxes.md , https://modal.com/docs/guide/sandbox-spawn.md , https://modal.com/docs/guide/sandbox-files.md , https://modal.com/docs/guide/sandbox-networking.md
- Key APIs:
  - `app = modal.App.lookup("name", create_if_missing=True)`; `sb = modal.Sandbox.create(app=app, image=..., secrets=[...], volumes={"/data": modal.Volume.from_name(...)}, timeout=...)`.
  - `p = sb.exec("cmd", "arg", timeout=...)`; `sb.terminate()`. Async variants via `.aio`.
  - Files: `sb.filesystem.read_text/write_text/copy_from_local/copy_to_local/list_files/make_directory/remove/stat`.
  - Network: `block_network=`, `cidr_allowlist=`, `outbound_domain_allowlist=`, `encrypted_ports=`.
- Pin: `modal==1.6.1` (supports Python <3.15).
- Packets: P21 (and P06/P15 if the data-analyst uses `ModalSandbox`).

## 10. E2B sandboxes

- Docs: https://docs.e2b.dev
- Machine-readable (verified 2026-10-07): https://e2b.dev/docs/llms.txt (full 1.6 MB: https://e2b.dev/docs/llms-full.txt)
  - https://docs.e2b.dev/quickstart.md , https://docs.e2b.dev/sandbox/persistence.md , https://docs.e2b.dev/filesystem/read-write.md , https://docs.e2b.dev/sandbox/environment-variables.md
- Key APIs:
  - `from e2b_code_interpreter import Sandbox` (or `from e2b import Sandbox` for plain sandboxes); `sbx = Sandbox.create()`; `sbx.run_code("...")` → execution with `.logs`.
  - `sbx.commands.run("...")`, `sbx.files.read(path)`, `sbx.files.write(path, data)`, `sbx.files.list("/")`.
  - Lifecycle: `sbx.pause()`, `Sandbox.connect(id)`, `sbx.kill()`, `Sandbox.list()`. Key from env `E2B_API_KEY`.
- Pin: `e2b==2.53.1`, `e2b-code-interpreter==2.10.3`.
- Packets: P21.

## 11. rclone (S3 backups)

- Docs: https://rclone.org/s3/ , https://rclone.org/commands/rclone_copy/
- Machine-readable, raw from the repo (verified 2026-10-07):
  - https://raw.githubusercontent.com/rclone/rclone/master/docs/content/s3.md (large; grep your provider)
  - https://raw.githubusercontent.com/rclone/rclone/master/docs/content/local.md
  - https://raw.githubusercontent.com/rclone/rclone/master/docs/content/commands/rclone_copy.md , `.../rclone_sync.md`, `.../rclone_check.md`, `.../rclone_config_create.md`
  - https://raw.githubusercontent.com/rclone/rclone/master/docs/content/docs.md (global flags, connection strings)
- Key facts:
  - S3 remote config keys: `type = s3`, `provider = <AWS|Cloudflare|Minio|...>`, `access_key_id`, `secret_access_key`, `endpoint`, `region`, `env_auth`.
  - Create non-interactively: `rclone config create <name> s3 provider=... access_key_id=... ...`, or use a connection-string remote `:s3,provider=AWS:bucket/path`.
  - `rclone copy src dst` (no deletes), `rclone sync src dst` (makes dst match, deletes extras), `rclone check src dst` (verify). Local-folder remote for tests: plain paths or `:local:`.
  - Keep secrets out of argv where possible (env vars or config file); never log them.
- Pin: rclone `v1.75.1` (binary; check with `rclone version`).
- Packets: P13, P17, P21.

## 12. Litestream

- Docs: https://litestream.io/reference/config/
- Machine-readable (verified 2026-10-07): https://raw.githubusercontent.com/benbjohnson/litestream.io/main/content/reference/config.md
- Key facts: YAML with `dbs:` list; each entry has `path:` and a single `replica:` (`url: s3://bucket/path` or `type: s3|sftp|nats|...`); `${VAR}` expansion for secrets; AWS keys via `access-key-id`/`secret-access-key` or env; global `snapshot:` (`interval`, `retention`) and logging settings; run with `litestream replicate`. See D10.
- Pin: `v0.5.17`.
- Writer/checkpoint guidance: https://litestream.io/tips/ ; SQLite WAL-reset fix: https://sqlite.org/wal.html#the_wal_reset_bug (fixed in 3.51.3, with 3.44.6 and 3.50.7 backports).
- Packets: P17.

## 13. DuckDB

- Docs: https://duckdb.org/docs/current/core_extensions/sqlite.html
- Machine-readable (verified 2026-10-07): index https://duckdb.org/llms.txt; raw docs from the docs repo:
  - https://raw.githubusercontent.com/duckdb/duckdb-web/main/docs/current/core_extensions/sqlite.md
  - https://raw.githubusercontent.com/duckdb/duckdb-web/main/docs/current/sql/statements/attach.md
  - https://raw.githubusercontent.com/duckdb/duckdb-web/main/docs/current/data/parquet/overview.md
  - https://raw.githubusercontent.com/duckdb/duckdb-web/main/docs/current/clients/python/overview.md , `.../clients/python/dbapi.md`
- Key APIs: `con = duckdb.connect()`; `ATTACH 'app.db' AS app (TYPE sqlite, READ_ONLY)`; `SELECT * FROM read_parquet('data/*.parquet')`; `con.execute(sql, params).fetchall()` / `.df()`. Warning in docs: linking multiple SQLite library copies in one process can cause errors.
- Pin: `duckdb==1.5.6`.
- Packets: P13 (P06/P15 data-analyst).

## 14. SQLite backups (stdlib `sqlite3`, `VACUUM INTO`, WAL)

- Docs: https://docs.python.org/3/library/sqlite3.html , https://sqlite.org/lang_vacuum.html , https://sqlite.org/backup.html , https://sqlite.org/wal.html
- Machine-readable (verified 2026-10-07): https://raw.githubusercontent.com/python/cpython/main/Doc/library/sqlite3.rst ; the sqlite.org pages are small HTML.
- Key APIs: `Connection.backup(target, *, pages=-1, progress=None, name="main", sleep=0.250)`; `VACUUM INTO 'file'` (target must not exist or be empty; produces a compact copy); `PRAGMA journal_mode=WAL`, `PRAGMA busy_timeout=5000`.
- Packets: P13, P17.

## 15. CCXT

- Docs: https://docs.ccxt.com/docs/manual
- Machine-readable (verified 2026-10-07): https://docs.ccxt.com/llms.txt , https://docs.ccxt.com/docs/manual.md , raw https://raw.githubusercontent.com/ccxt/ccxt/master/wiki/Manual.md
- Key APIs: `ccxt.<exchange>({"apiKey":..., "secret":..., "enableRateLimit": True})`; `set_sandbox_mode(True)`; `load_markets()`, `fetch_ticker`, `fetch_ohlcv(symbol, timeframe, since, limit)`, `fetch_balance()`, `fetch_open_orders`, `fetch_my_trades`, `create_order(...)` (money path: never exposed to agents); async: `ccxt.async_support`; WebSocket: `ccxt.pro` (`watch_*`).
- Pin: `ccxt==4.5.85`.
- Packets: P18.

## 16. cTrader Open API

- Docs: https://help.ctrader.com/open-api/ (HTML only; `llms.txt` 404)
- Verified pages (2026-10-07): https://help.ctrader.com/open-api/messages/ , https://help.ctrader.com/open-api/model-messages/ , https://help.ctrader.com/open-api/account-authentication/ , https://spotware.github.io/OpenApiPy/
- Machine-readable: https://raw.githubusercontent.com/spotware/OpenApiPy/main/README.md , protobuf definitions https://raw.githubusercontent.com/spotware/openapi-proto-messages/main/OpenApiMessages.proto
- Key facts: `ctrader_open_api` (Twisted, deferred-based): `Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)`, hosts `EndPoints.PROTOBUF_DEMO_HOST` / `PROTOBUF_LIVE_HOST`, `client.send(request)` returns a deferred, `Protobuf.extract(msg)`. Messages: `ProtoOAApplicationAuthReq`, `ProtoOAGetAccountListByAccessTokenReq`, `ProtoOAAccountAuthReq`, `ProtoOARefreshTokenReq`, `ProtoOASymbolsListReq`, `ProtoOASubscribeSpotsReq`/`ProtoOASpotEvent`, `ProtoOAGetTrendbarsReq`, `ProtoOATraderReq`, `ProtoOAReconcileReq`, `ProtoOANewOrderReq` (money path), `ProtoOAExecutionEvent`. First compare with the existing `packages/qmf-venue/src/qmf/venue/ctrader.py`.
- Pin: `ctrader-open-api==0.9.2`. **UNVERIFIED:** wheels for Python 3.14 (Twisted/protobuf).
- Packets: P18.

## 17. keyring (Windows Credential Manager)

- Docs: https://keyring.readthedocs.io/en/latest/
- Machine-readable (verified 2026-10-07): https://raw.githubusercontent.com/jaraco/keyring/main/README.rst
- Key APIs: `keyring.get_password(service, username)` (returns `None` if missing), `keyring.set_password(service, username, secret)`, `keyring.delete_password(...)`, `keyring.get_credential(service, None)`. On Windows the default backend is Windows Credential Locker. QMX convention: service `qmx/<provider>`, username = provider name; env-var fallback only in CI.
- Pin: `keyring==25.7.0`.
- Packets: P06, P11, P18, P19, P21.

## 18. pytest-xdist and uv

- pytest-xdist docs: https://pytest-xdist.readthedocs.io/en/stable/distribution.html
  - Machine-readable (verified 2026-10-07): https://raw.githubusercontent.com/pytest-dev/pytest-xdist/master/docs/distribution.rst , https://raw.githubusercontent.com/pytest-dev/pytest-xdist/master/README.rst
  - Key flags: `-n auto` / `-n logical` / `-n <N>`; `--dist load` (default) | `loadscope` | `loadfile` | `loadgroup` (with `@pytest.mark.xdist_group`) | `worksteal`. Tests that share a SQLite file or port must be grouped or use `tmp_path`.
  - Pin: `pytest-xdist==3.8.0`.
- uv docs: https://docs.astral.sh/uv/
  - Machine-readable (verified 2026-10-07): https://docs.astral.sh/uv/llms.txt ; raw https://raw.githubusercontent.com/astral-sh/uv/main/docs/concepts/projects/workspaces.md , `.../concepts/projects/sync.md`, `.../concepts/projects/layout.md`, `.../guides/integration/docker.md`; full CLI flags: https://docs.astral.sh/uv/reference/cli/index.md (790 KB, grep it)
  - Key facts: root `pyproject.toml` `[tool.uv.workspace] members = ["packages/*"]`, `exclude = [...]`; member deps via `[tool.uv.sources] name = { workspace = true }`; `uv lock`, `uv lock --check`; `uv sync --locked` (fail if lock is stale) vs `--frozen` (use lock as is, for Docker/CI); `--package <name>`, `--all-packages`, `--no-dev`; `uv run --package <name> pytest`.
  - Pin: `uv==0.12.23`.
- Packets: all (P16 updates workspaces; P12/P17 build per-app venvs and images).

## 19. Smaller references used by single packets

- cachetools (P13): https://raw.githubusercontent.com/tkem/cachetools/master/README.rst (verified), https://cachetools.readthedocs.io/en/stable/ ; `TTLCache(maxsize, ttl)`. Pin `cachetools==7.2.1`.
- Firecrawl MCP (P19): https://docs.firecrawl.dev/llms.txt , https://docs.firecrawl.dev/mcp-server.md , https://raw.githubusercontent.com/firecrawl/firecrawl-mcp-server/main/README.md (all verified). API key from `qmx/firecrawl`.
- **UNVERIFIED (not fetched):** Daytona SDK (P21), Docker / Docker networking docs (P17), Windows Job Objects via `pywin32`/`psutil` (P12), Tailscale (P17), LangSmith/OpenTelemetry tracing (DESIGN §5.8), Hummingbot (P18 note), MinIO/moto (P21 tests). Fetch their official docs before using them and add the URLs here in the PR.

P17 additions (fetched 2026-10-08):
- Docker containers and CLI: https://docs.docker.com/engine/containers/run/ , https://docs.docker.com/reference/cli/docker/container/run/ , https://docs.docker.com/reference/cli/docker/network/create/ , https://docs.docker.com/reference/cli/docker/container/exec/
- Bridge isolation and gateway modes: https://raw.githubusercontent.com/docker/docs/main/content/manuals/engine/network/drivers/bridge.md , https://raw.githubusercontent.com/docker/docs/main/content/manuals/engine/network/port-publishing.md
- Docker builds and Ubuntu install: https://raw.githubusercontent.com/docker/docs/main/content/manuals/build/building/best-practices.md , https://raw.githubusercontent.com/docker/docs/main/content/manuals/engine/install/ubuntu.md
- Docker multi-stage builds: https://raw.githubusercontent.com/docker/docs/main/content/manuals/build/building/multi-stage.md (Git is available only during the frozen dependency build).
- Squid ACLs: https://www.squid-cache.org/Doc/config/acl/ , https://www.squid-cache.org/Doc/config/http_access/ , https://www.squid-cache.org/Doc/config/http_port/
- Tailscale: https://tailscale.com/docs/install/linux.md
- rclone installation/SFTP: https://raw.githubusercontent.com/rclone/rclone/master/docs/content/install.md , https://raw.githubusercontent.com/rclone/rclone/master/docs/content/sftp.md
- Litestream Docker: https://litestream.io/guides/docker/
- systemd service units: https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html
- Subprocess pipe encoding: https://raw.githubusercontent.com/python/cpython/main/Doc/library/subprocess.rst
- POSIX session ownership: https://raw.githubusercontent.com/python/cpython/3.14/Doc/library/os.rst , https://man7.org/linux/man-pages/man2/setsid.2.html
- rclone filter ordering: https://raw.githubusercontent.com/rclone/rclone/master/docs/content/filtering.md

---

## 20. Packet → sections to read

| Packet | Read these sections | Notes |
|---|---|---|
| P06 agents spec + router | 0, 1, 2, 3, 4, 7, 17, 18 | D1, D3, D5, D6, D8, D9 |
| P07 memory provider | 0, 1 (custom middleware, Summarization), 2 (StoreBackend, memory), 3 (SqliteStore) | namespaces are tuples, no `*` in StoreBackend |
| P08 guards | 0, 1 (limits, wrap_tool_call, after_model), 2 (backends, permissions, interrupt_on) | D6, D9 |
| P09 domain tools + MCP servers | 4, 5, 18 | FastMCP 4 in-memory `Client(mcp)` tests |
| P10 workflow compiler | 2 (CompiledSubAgent), 3 | `Send`, `interrupt`, `SqliteSaver`, `recursion_limit` |
| P11 qmx-control | 5 (http_app mount, annotations), 6, 17 | D11 |
| P12 mini-app runtime | 5 (stdio/http, Apps), 18 (uv) | Job Objects UNVERIFIED |
| P13 storage + backup | 11, 13, 14, 19 (cachetools) | rclone local remote in tests |
| P14 road to live | 14 (if snapshots), 18 | no new libraries |
| P15 copilot + first app | 0, 1, 2, 3, 4, 5, 6 | D3, D4, D8 |
| P16 retire old QMA | 18 (uv workspaces/lock) | |
| P17 Docker tier | 11, 12, 14, 18 (uv Docker guide) | Docker docs UNVERIFIED |
| P18 brokers + accounts | 5, 15, 16, 17 | money path: `create_order`/`ProtoOANewOrderReq` never in agent tools |
| P19 research sources | 4, 5, 19 (Firecrawl) | |
| P20 skills + hooks | 1 (custom middleware, HITL), 2 (skills) | |
| P21 remote runs | 3 (checkpointers), 7, 8, 9, 10, 11, 18 | D7; Daytona UNVERIFIED |
