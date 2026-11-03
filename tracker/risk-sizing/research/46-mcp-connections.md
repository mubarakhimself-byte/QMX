# 46. MCP connections for QMX agents: cTrader, TradingView, MT5

Read-only research, 2026-11-03. Code facts are at commit `cea69e1d`. Every web claim is CHECKED (URL, read 2026-11-03) or INFERRED.
Scope change from the operator, received mid-task: Part 2 items 4 (guard gap) and 5 (marked sources) are dropped. Agents get MCP tools as they are. The one control is a blocker: MCP tools may act only on demo accounts. Section 3 therefore covers account selection per vendor.

## 1. Sources

| Vendor | Server | Publisher | URL | Transport | Auth | Licence | Date |
|---|---|---|---|---|---|---|---|
| cTrader | Local MCP (`ctrader-local-mcp`) | Spotware (official) | https://help.ctrader.com/ctrader-ai-agent-connect/local-mcp/setup/ | HTTP, `http://127.0.0.1:9876/mcp/` | the cTrader Windows or Mac session you are signed in to (cTID); no token | proprietary, no licence stated | launched 14 May 2026 |
| cTrader | Remote MCP (`ctrader-remote-mcp`, "rest-proxy" 1.0.18) | Spotware (official) | https://help.ctrader.com/ctrader-ai-agent-connect/remote-mcp/setup/ | HTTP; the endpoint is not published (it ships inside the copied config) | a per-account bearer token copied from cTrader Web, Settings > Remote MCP | proprietary | 14 May 2026 |
| cTrader | `spotware/ctrader-skills` (skills, not a server) | Spotware | https://github.com/spotware/ctrader-skills | n/a | n/a | proprietary, Spotware EULA (GitHub reports NOASSERTION) | last push 2026-08-21 |
| TradingView | TradingView MCP Server (public beta) | TradingView (official) | https://www.tradingview.com/mcp/docs | Streamable HTTP, `https://mcp.tradingview.com/mcp` | OAuth 2.1 with your TradingView login; no API keys | TradingView Terms of Use | beta from 16 Sep 2026 |
| TradingView | `tradesdontlie/tradingview-mcp` | third party | https://github.com/tradesdontlie/tradingview-mcp | stdio (Node 18+), drives TradingView Desktop over CDP on `localhost:9222` | none; needs a paid TradingView Desktop | README says MIT (GitHub reports NOASSERTION) | last push 2026-10-21; 7,064 stars |
| TradingView | `atilaahmettaner/tradingview-mcp`, PyPI `tradingview-mcp-server` | third party | https://github.com/atilaahmettaner/tradingview-mcp | stdio via `uvx` (Python 3.10-3.13); a hosted copy runs at `mcp.tradingmcp.ai` | none; an optional Marketaux key for news | MIT | PyPI 0.8.1 on 2026-08-24; last push 2026-10-29 |
| MT5 | none official | MetaQuotes ships only the `MetaTrader5` Python package | https://pypi.org/project/MetaTrader5/ | n/a | n/a | MIT | 5.0.6231 on 2026-09-27; `win_amd64` wheels only |
| MT5 | `ariadng/metatrader-mcp-server`, PyPI `metatrader-mcp-server` | third party | https://github.com/ariadng/metatrader-mcp-server | stdio, SSE (`0.0.0.0:8080` by default) or HTTP; Python 3.10+ | `--login --password --server` on the command line or in `.env` | MIT | PyPI 0.5.1 on 2026-03-28; 844 stars |
| MT5 | `Qoyyuum/mcp-metatrader5-server`, PyPI `mcp-metatrader5-server` | third party | https://github.com/Qoyyuum/mcp-metatrader5-server | stdio by default, HTTP at `127.0.0.1:8000`; `uvx --from mcp-metatrader5-server mt5mcp` | `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER` in the config `env` block, or a `login` tool | README says MIT (no licence file on GitHub) | PyPI 0.1.8 on 2026-06-19; last push 2026-11-02 |

Notes on the sources:
- cTrader: Spotware calls it "cTrader AI Agent Connect". It is free with a cTrader account. CHECKED https://www.spotware.com/news/ctrader-launches-official-mcp-servers/ and https://help.ctrader.com/ctrader-ai-agent-connect/faq/.
- cTrader: the Local server works only while cTrader Windows or Mac is running. Settings > MCP Server has three switches: "Enable MCP server", "Allow trading via MCP" and "Require confirmation for trading operations". CHECKED on the local-mcp/setup page.
- cTrader: the Remote server issues one token per trading account. The token expires with the cTrader Web session, and then you re-authenticate. CHECKED on the remote-mcp/setup page and in the FAQ.
- cTrader: a "CLI MCP" built on cTrader CLI 4.8+ is mentioned in search snippets. Its page, help.ctrader.com/ctrader-ai-agent-connect/cli/setup/, returned 404 on 2026-11-03, so it is not established.
- TradingView official: it requires the Essential plan or higher; trial plans are excluded. The limit is about 100 tool calls per minute per user, and daily limits may apply during the beta. Market data is delayed. CHECKED in the docs and at https://www.tradingview.com/blog/en/tradingview-mcp-server-public-beta-60864/.
- MT5: no official MetaQuotes MCP server turned up in a web search on 2026-11-03. INFERRED: none exists.

## 2. Tool lists (READ or ACTION)

### cTrader Remote: 16 tools, every one named
Source: `skills/ctrader-mcp-servers/references/remote-http-server.md` in spotware/ctrader-skills ("Surface map" and "Profile distinction"). CHECKED via the GitHub API on 2026-11-03.
- READ (the `data` profile): `get_version`, `get_balance`, `get_assets`, `get_symbols`, `get_spot_prices`, `get_trendbars`, `get_positions`, `get_position_details`, `get_pending_orders`, `get_order_history`, `get_deals`.
- ACTION (the `trading` profile adds these): `create_order`, `amend_order`, `cancel_order`, `amend_position`, `close_position`.
- The doc says: "if no mutating tools are visible in `tools/list`, the connection is `data`-only". It does not say how a token gets the data profile.
- Rate limits: 50 requests per second general, and 5 per second for `get_trendbars`, `get_order_history` and `get_deals`. These match the Open API figures in `packages/qmf-venue/src/qmf/venue/ctrader.py:24-27`.
- `get_trendbars` periods: `M_1, M_5, M_15, M_30, H_1, H_4, D_1, W_1, MN_1`.
- No file-system tools and no arbitrary-network tools.

### cTrader Local: names gathered from the skill docs (Spotware publishes no full list)
Sources: `local-http-server.md` and `SKILL.md` in the same repo. Spotware's own help pages give capability areas only, with no identifiers. CHECKED at help.ctrader.com/ctrader-ai-agent-connect/local-mcp/.
- READ: `ping`, `get_version`, `get_server_time`, `get_accounts_list`, `get_balance`, `get_account_statistics`, `get_assets`, `get_symbols`, `get_symbol_details`, `get_spot_prices`, `get_trendbars`, `get_positions`, `get_position_details`, `get_pending_orders`, `get_order_history`, `get_deals`, `get_watchlists`, `list_charts`, `get_active_chart`, `get_chart_viewport`, `get_chart_objects`, `listChartIndicators`, `getIndicatorValues`, `listPlugins`.
- ACTION on orders and positions: `place_market_order`, `place_limit_order`, `place_stop_order`, `place_stop_limit_order`, `create_order`, `amend_order`, `cancel_order`, `cancel_all_pending_orders`, `amend_position`, `close_position`, `close_position_partial`, `close_all_positions`.
- ACTION, cBots: `startPlugin` and `stopPlugin`. A cBot can trade.
- ACTION on the UI only: `focus_chart`, `change_chart_symbol`, `change_chart_timeframe`, `scroll_chart`, `zoom_chart`, `add_chart_object`, `update_chart_object`, `delete_chart_object`, `clear_chart_objects`, `addChartIndicator`, `removeChartIndicator`, `update_indicator_parameters`, `save_chart_template`, `apply_chart_template`, `delete_chart_template`, `delete_workspace`, `delete_watchlist`, `remove_symbol_from_watchlist`, `delete_price_alert`, `show_notification`.
- Named on the help pages but with no identifier in the docs: market news, creating price alerts, saving and loading workspaces, creating watchlists.
- No file-system tools or arbitrary-network tools are documented.

### TradingView official: 35 tools, every one labelled read-only or write in the docs
- READ: `list_watchlists`, `get_watchlist`, `get_active_watchlist` (it may create a default watchlist), `get_ohlcv`, `get_economic_data`, `get_economic_symbols`, `search_symbols`, `get_symbol_data`, `run_screener`, `get_symbol_data_batch`, `get_screener_columns`, `get_technicals_rating`, `get_news`, `get_news_story`, `get_forecasts`, `get_financials`, `get_financial_history`, `get_documents`, `get_document_view`, `get_earnings_calendar`, `get_economic_calendar`, `get_dividends_calendar`, `list_alerts`, `get_alerts`, `get_alerts_log`.
- ACTION (TradingView account only, no money): `create_watchlist`, `delete_watchlist`, `add_to_watchlist`, `remove_from_watchlist`, `update_watchlist`, `create_alert`, `update_alert`, `delete_alert`, `stop_alerts`, `restart_alerts`.
- No broker, order or position tools. No file or network tools. CHECKED at https://www.tradingview.com/mcp/docs.

### TradingView, tradesdontlie: 84 tools over stdio (README, section "Tools")
- READ: `chart_get_state`, `data_get_study_values`, `quote_get`, `data_get_ohlcv`, `data_get_pine_lines`, `data_get_pine_labels`, `data_get_pine_tables`, `data_get_pine_boxes`, `symbol_info`, `symbol_search`, `pane_list`, `tab_list`, `pine_get_errors`, `pine_get_console`, `pine_get_source`, `pine_list_scripts`, `pine_analyze`, `pine_check`, `replay_status`, `draw_list`, `alert_list`, `watchlist_get`, `layout_list`, `tv_health_check`, `tv_discover`.
- ACTION on the UI and account: chart and pane setters, `pine_set_source`, `pine_smart_compile`, `pine_save` (saves to the TradingView cloud), `pine_new`, `draw_*`, `alert_create`, `alert_delete`, `watchlist_add`, `layout_switch`, `tab_new`, `tab_close`, `tv_launch`.
- ACTION, paper: `replay_trade` buys and sells inside replay mode. The README says the tool does not "Execute real trades".
- Arbitrary-code tools: `ui_evaluate` runs JavaScript in the TradingView Electron app; `ui_click` and `ui_open_panel` drive the UI. `capture_screenshot` writes an image. INFERRED: `ui_click` could press a broker panel inside TradingView Desktop if one is connected.

### TradingView, atilaahmettaner: 39 analysis tools, all READ
- Names in the README tables include `yahoo_price`, `stock_prices`, `get_technical_analysis`, `get_multi_timeframe_analysis`, `combined_analysis`, `screen_stocks`, `stock_screener`, `scan_by_signal`, `financial_news`, `market_sentiment`, `market_snapshot`, `backtest_strategy`, `compare_strategies` and `walk_forward_backtest_strategy`.
- Its data comes from the `tradingview_ta` and `tradingview-screener` libraries (TradingView's public screener endpoints), Yahoo Finance and news RSS feeds, all fetched server-side. No TradingView login is needed. No order tools.

### MT5, ariadng: 26 operations (README "Available Operations")
- READ: `get_account_info`, `get_symbols`, `get_symbol_price`, `get_candles_latest`, `get_candles_by_date`, `get_symbol_info`, `get_all_positions`, `get_positions_by_symbol`, `get_positions_by_id`, `get_all_pending_orders`, `get_pending_orders_by_symbol`, `get_deals`, `get_orders`.
- ACTION: `place_market_order`, `place_pending_order`, `modify_position`, `modify_pending_order`, `close_position`, `close_all_positions`, `close_all_positions_by_symbol`, `close_all_profitable_positions`, `close_all_losing_positions`, `cancel_pending_order`, `cancel_all_pending_orders`, `cancel_pending_orders_by_symbol`.

### MT5, Qoyyuum (README "API Reference")
- READ: `get_symbols`, `get_symbols_by_group`, `get_symbol_info`, `get_symbol_info_tick`, `copy_rates_from_pos`, `copy_rates_from_date`, `copy_rates_range`, `copy_ticks_from_pos`, `copy_ticks_from_date`, `copy_ticks_range`, `order_check`, `positions_get`, `positions_get_by_ticket`, `orders_get`, `orders_get_by_ticket`, `history_orders_get`, `history_deals_get`.
- ACTION: `order_send` (any MT5 trade request).
- Session tools: `initialize`, `login(account, password, server)` and `shutdown`. `login` switches the terminal's account.

## 3. How each tool picks its account (what a demo-only blocker would check)

### cTrader Remote
- A session is bound to one account when it connects. The token is per trading account, and the tools take no account argument: `get_balance` and `create_order` have no account field in the documented schema. CHECKED in the FAQ ("Each trading account gets its own token") and in remote-http-server.md.
- The doc says the account environment is encoded in a "slug" (the `environment` field), and that "The Remote surface itself does not distinguish demo from live — the same tools work against either". CHECKED. Where the slug sits (URL, token or header) is not published.
- It cannot be pointed at `demo.ctraderapi.com`. Its endpoint is Spotware's own rest-proxy, not an Open API host. INFERRED from the "rest-proxy" build name and the unpublished URL. Demo-only would mean copying only a demo account's config.
- INFERRED: it runs on Spotware's Open API back end. Its field names, cents volume, pipette prices, `moneyDigits` and the 50 and 5 per second limits all match Open API. It does not use QMX's Open API app: no `clientId` or `clientSecret` is involved, only a cTrader Web bearer token. CHECKED: the FAQ says the remote server "uses a per-account bearer token issued from cTrader Web".
- Read-only: there is a `data` profile with no mutating tools, but how a token gets it is not documented (see section 5).
- Where it runs: hosted by Spotware. QMX would reach it as a URL from whatever host launches the chat.

### cTrader Local
- The tools act on the cTrader Desktop app's active account. The documented tools take no account id, and `get_balance` returns the active `traderId` and `accountType`. CHECKED in local-http-server.md and quirk Q-L15. `get_accounts_list` may hide the active account (Q-L15).
- No tool is documented that switches the Desktop's account. Whether one exists is open. The skill calls Local the route for "multi-account work".
- Demo or live is whatever account the person signed in to the Desktop has active. There is no host to point at.
- "Allow trading via MCP" off removes trading for the whole Desktop session (CHECKED). It is a switch in the cTrader app, not a per-account rule.
- Where it runs: only on the machine running cTrader Windows or Mac, on loopback port 9876. For QMX that is This PC. A node would need cTrader Desktop installed and running.

### QMX's own cTrader code (for comparison; it already blocks live)
- `qmx-agents/packages/qmx-broker/src/qmx_broker/adapters.py:138-147` (`can_trade_live`): a grant counts as able to trade live unless `permissionScope == "SCOPE_VIEW"` and no listed `ctidTraderAccount` has `isLive: true`.
- `adapters.py:165-190` (`CTraderAdapter.authenticate`) does three things:
  - Raises `LiveGrant` (`:104-115`, ruling 135, "this sign-in can trade live money; it belongs on a trading server").
  - Raises `EnvironmentMismatch` when an account's `isLive` disagrees with the connection's `environment` (`:118-135`, `:182-183`).
  - Binds every read to one `ctidTraderAccountId` and checks that the reply carries the same id (`:192-196`).
- Open API itself uses separate demo and live hosts, and one connection per environment. CHECKED in code: `docs/components/ctrader.md:112` and `packages/qmf-venue/src/qmf/venue/ctrader.py:648-684`.
- The node's live client uses Open API port 5035, with "Tagged smoke against `demo.ctraderapi.com`" (`qmn/src/qmn/venue/live.py:18-22`).
- Neither cTrader MCP exposes `isLive`, `permissionScope` or a host choice. INFERRED from the documented tool fields.

### TradingView
- The official server has no broker account. It only touches the TradingView account it signed in with, through OAuth: watchlists and alerts. Demo or live does not apply.
- The tradesdontlie server drives whatever TradingView Desktop shows on the same machine. Its trading is replay-only. A broker panel inside Desktop is not addressed (INFERRED risk, see section 4).
- The atilaahmettaner server has no account at all.
- Where they run: the official one is hosted. tradesdontlie runs where TradingView Desktop runs (This PC). atilaahmettaner runs anywhere with Python, or as its hosted copy.

### MT5
- The account is bound when the session starts: the terminal holds one account, chosen by `initialize(path, login, password, server, ...)` or `login(...)`. If no login is given, the last used account applies. CHECKED at https://www.mql5.com/en/docs/python_metatrader5/mt5initialize_py.
- Demo or live shows in `account_info().trade_mode` (CHECKED at https://www.mql5.com/en/docs/python_metatrader5/mt5accountinfo_py). The values are `ACCOUNT_TRADE_MODE_DEMO`, `ACCOUNT_TRADE_MODE_CONTEST` and `ACCOUNT_TRADE_MODE_REAL` (CHECKED at https://www.mql5.com/en/docs/constants/environment_state/accountinformation). INFERRED: demo is `0`, since the docs example shows `trade_mode=0` on "MetaQuotes-Demo". The `server` name, for example `MetaQuotes-Demo`, is broker-chosen text, not a reliable flag.
- ariadng: the account is fixed by `--login --password --server` at process start, and no login tool is listed. A demo login means a demo-only server process.
- Qoyyuum: the `login` tool lets an agent switch to any account it has credentials for, a live one included. The `env` block only sets defaults.
- Where they run: on a Windows machine with the MT5 terminal installed, because the `MetaTrader5` wheel exists only for `win_amd64` (CHECKED on PyPI). That means This PC or a Windows node. ariadng documents remote SSE from a Windows VPS.

## 4. QMX code facts at cea69e1d

### 4.1 How an external MCP server is registered and offered to the copilot
- External servers already exist. They are declared in `settings.toml [mcp_servers]`, a settings section (`qmx-agents/packages/qmx-control/src/qmx_control/service.py:55-57`).
- The shipped default row is `firecrawl`, with `url` `https://mcp.firecrawl.dev/v2/mcp`, `enabled = false` and `credential_ref = "qmx/firecrawl"` (`service.py:985-994`). A Firecrawl row accepts only `url`, `enabled` and `credential_ref` (`service.py:1146-1155`).
- `tools.server_config` turns a row into an SDK config: `command` with `args` and `env` becomes stdio, and `url` becomes `{"type": "http", "url": url}` (`qmx-agents/packages/qma-harness/src/qma/harness/tools.py:1043-1069`).
  - There is no `headers` field, so a bearer token cannot be passed (`:1067-1068`).
  - A row with `credential_ref` is refused: "servers that need a stored credential are not wired yet" (`:1053-1054`).
  - Server names must match `[A-Za-z0-9-]+(?:_[A-Za-z0-9-]+)*` and must not be `qmx` or `qmx_*` (`:1039`, `:1046-1052`).
- Vetting (`tools.py:1106-1145`): before launch, the harness starts each enabled server with the Python MCP client and lists all its tools, with a 30 s timeout (`:1005`). A server that fails is refused and gets a `needs_you` note, but the chat still starts (`chat.py:1283-1287`). A tool the CLI loads that vetting never saw refuses the launch (`tools.py:1148-1158`, `chat.py:1225`).
- Selection (`chat.py:1276-1282`): the external set is `[mcp_servers]` merged with the chat's own `mcp_servers`. If the chat declares toolsets, only servers named as `mcp:<server>` stay. A chat with no built-ins and no toolsets gets none. `mcp:` is a dynamic toolset prefix (`surface.py:442-450`).
- `home_preset` (`surface.py:484-493`) returns core toolsets plus running `app:` ids, and has no `mcp:` entry. Instead, a copilot chat whose `toolsets` is None gets every enabled `[mcp_servers]` row, because the filter at `chat.py:1279` applies only when toolsets are declared.
- The launch passes `mcp_servers` with `strict_mcp_config=True` and `setting_sources=[]` (`launch.py:704-719`), plus `ENABLE_CLAUDEAI_MCP_SERVERS=false` (`launch.py:397`). Project `.mcp.json` files are off (`home.py:870`); packs never write `.mcp.json` (`packs.py:44`).
- A chat can carry its own `mcp_servers` (`launch.py:228-229`, `harness.py:206`).
- Tool names come out as `mcp__<server>__<tool>` (`guard.py:270-275`). QMX's own tools are `mcp__qmx_<toolset>__<op>` (`tools.py:118-119`).
- In-chat toggling uses `toggle_mcp_server` (`chat.py:842-844`, `:1196-1211`). A server not up within 30 s is left out with a note (`chat.py:197`, `:1211-1216`).

### 4.2 How engine agent steps get tools
- An agent node declares `toolsets`, and the validator accepts any `mcp:<name>` (`qmx-agents/packages/qmx-engine/src/qmx_engine/definition/model.py:145-160`).
- `nodes/agent.py:181-185` reads `parameters.tools`, `toolsets` and `skills`. `:388-399` starts a Background chat with them. The adapter sets `toolsets=toolsets` and `policy_args={"tools": [...]}` (`ports/harness_adapter.py:275-290`, `:378-382`).
- So `"toolsets": ["mcp:ctrader"]` already selects the server. That needs no engine change; the harness filter is at `chat.py:1279-1281`.
- Two gates still stop the tools from running in an engine step:
  - The guard denies every external MCP tool in an unattended chat unless `settings.toml [claude] external_tools_unattended` lists `server/tool` or `server/*` (`guard.py:220-224`, `:278-282`, `:853-857`; the key is defined at `home.py:242-253`, `:301-302`). This is a settings change, not code.
  - The `engine` policy rejects any asked tool whose name is not in `policy_args["tools"]` (`qmx-agents/packages/qmx-engine/src/qmx_engine/policy.py:39-45`). `parameters.tools` lists built-ins, according to the b-build-and-prove README in the engine templates. QMX tools never ask (allow rules H20, `chat.py:1242-1245`); external tools have no allow rule.
- INFERRED, unverified at run time: an external call reaches `engine_policy` and is rejected. The exceptions are a matching `[rules] always_allow` row, which returns `Allow` in the guard (`guard.py:881-883`), or listing `mcp__<server>__<tool>` in `parameters.tools`. Whether the second passes `_builtins` and the SDK `tools=` option (`surface.py:607-616`, `launch.py:706`) is untested.
- If code must change instead, the engine lines are `policy.py:40-45` (the name check) or `harness_adapter.py:378-382` (`policy_args`). Engine runs default to `runs_on = "pc"` (`model.py:141`).

### 4.3 Where secrets live
- Host vault: `HOST_VAULT = {"pairing-key", "control-token", "run-pass-key"}` are host-only files in `<home>/vault/` (`qmx-agents/packages/qmx-host/src/qmx_host/host.py:223-226`).
- `vault_secrets` (`host.py:1004-1030`) reads an app's declared `qmx/<name>` from `vault/<name>`, on role `server` only. This PC and a node use the OS keyring, which is Credential Manager on Windows (`host.py:1033-1039`). App secret names follow the pattern `qmx/[a-zA-Z0-9_-]+` (`host.py:221`).
- `qmx_apps.manifest.HOST_SECRETS` does not exist at cea69e1d; a `git grep` finds nothing. The manifest has `Capabilities.secrets` (`qmx-agents/packages/qmx-apps/src/qmx_apps/manifest.py:81-84`) and `TRADING_GRANT_SECRETS = {"qmx/trading-node-keys"}`, with prefixes `qmx/trading-node-keys-` and `qmx/node-` that only the trading node may name (`manifest.py:59-64`).
- cTrader keyring names: `qmx/ctrader-client-id` and `qmx/ctrader-client-secret` (`qmx-agents/packages/qmx-broker/src/qmx_broker/credentials.py:23-24`), and per-connection refs such as `qmx/ctrader-demo` (`qmx-broker/README.md:13`). Agent Bash could read `qmx/*` entries; the guard's name filter is "a speed bump" (`qma-harness/docs/SIGNOFF.md:135`).
- `check_secrets` (`home.py:528-555`) refuses MCP-server rows that would put a literal secret on the chat record. A credential-named key in `env` or `headers` must be a `qmx/*` ref (`home.py:495-525`). `keyring_refs` collects `qmx/*` names from `[providers]`, `[brokers]` and `[mcp_servers]` (`tools.py:877-894`).
- Nothing yet resolves an MCP `qmx/*` ref to a value at launch, because `server_config` refuses `credential_ref` (`tools.py:1053-1054`).
- Provider keys never reach a session. A relayed launch gets `ANTHROPIC_BASE_URL` (a local relay) and `ANTHROPIC_AUTH_TOKEN = grant.secret`, "the grant secret (never a provider key)" (`launch.py:553-572`). A plan launch gets only `CLAUDE_CONFIG_DIR` (`launch.py:561-562`).

### 4.4 Trading node session versus an MCP on This PC
- The node holds its own Open API session. `open_session` drives the node's `ConnectionManager` through `connect_open_api` on port 5035 and never builds "a second manager" (`qmn/src/qmn/venue/live.py:18-22`).
- This PC also opens short Open API read sessions (`qmx-agents/packages/qmx-broker/src/qmx_broker/ctrader_transport.py:1-26`). Those reads refuse live-trading grants (`adapters.py:173-174`).
- Open API limits apply per connection: 50 per second non-historical and 5 per second historical (`ctrader.py:24-27`, `docs/components/ctrader.md:64`). The per-client error `CONNECTIONS_LIMIT_EXCEEDED = 67` exists, and its cap is unpublished (`_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-08-19/ctrader-rate-limits-research.md:17`).
- One connection serves unlimited accounts of one environment (`ctrader-depth-and-connectivity-research.md:35`).
- INFERRED: a cTrader Local MCP on This PC is the Desktop app's own session, separate from the node's Open API connection. A Remote MCP is Spotware's proxy session. Neither shares the node's connection, and neither counts against QMX's Open API app, since the app credentials are not used. Whether Spotware counts proxy sessions against the account is not published.

## 5. Risks (facts only)

- Money tools:
  - cTrader Remote: `create_order`, `amend_order`, `cancel_order`, `amend_position` and `close_position` work on demo and live alike. Its own docs warn: "AI-generated actions may trigger real trades and result in losses."
  - cTrader Local adds `close_all_positions` and `cancel_all_pending_orders`, plus `startPlugin` (a cBot can trade).
  - MT5: ariadng has bulk-close tools; Qoyyuum's `order_send` takes any trade request.
  - TradingView official has no money tools.
- Account binding gaps for a demo-only rule:
  - cTrader Local acts on whichever account the Desktop has active.
  - Qoyyuum's `login` lets an agent switch accounts.
  - The cTrader Remote surface does not tell demo from live.
  - Only MT5 exposes a demo or live field to a tool (`trade_mode`).
- QMX's own Open API reads already refuse live grants (`adapters.py:104-115`, `:138-147`). The cTrader MCPs bypass that code, because they do not use QMX's Open API app.
- File and network: tradesdontlie's `ui_evaluate` runs arbitrary JavaScript in TradingView Desktop, and it needs a debug port opened on `localhost:9222`. ariadng's SSE mode binds `0.0.0.0` by default.
- Secrets:
  - The cTrader Remote token is a bearer token in the client config. QMX cannot pass it today: there are no `headers` and `credential_ref` is refused (`tools.py:1053-1068`).
  - The MT5 servers take the account password in args or env. `check_secrets` allows only `qmx/*` refs there (`home.py:545-546`), and no code resolves them yet.
  - Fake "tradingview-mcp" copies on npm carry malware (`MAL-2026-16390`, per the atilaahmettaner README).
- Terms of use:
  - The tradesdontlie README says TradingView's terms "restrict automated data collection, scraping, and non-display usage".
  - The atilaahmettaner server reads TradingView's public screener endpoints through unofficial libraries.
  - TradingView's official MCP data is delayed in the beta, and requires a paid plan.
- Platform:
  - MT5 needs Windows and a running terminal (`win_amd64` wheels only). Live trading also needs algo trading enabled in the terminal (ariadng README, Step 2).
  - cTrader Local needs cTrader Desktop running before the client starts.
  - tradesdontlie needs TradingView Desktop running in debug mode.
  - Both cTrader MCPs are new (May 2026) and documented with live quirks, for example `amend_position` silently drops SL or TP when either field is omitted (remote-http-server.md, Q-R10).

## 6. Open facts I could not establish

- cTrader Remote: the endpoint URL, the config format, where the "slug" and `environment` sit, how a token gets the `data` (read-only) profile, and the token's lifetime. None of this is in public docs or the skills repo.
- cTrader Local: whether any tool switches the Desktop's active account, whether `get_accounts_list` or `get_balance` returns an `isLive`-style field, and the full tool list.
- Whether Spotware counts MCP sessions toward any per-account or per-cTID connection limit. Open API's `CONNECTIONS_LIMIT_EXCEEDED` cap is unpublished.
- The cTrader CLI MCP: its page returned 404 on 2026-11-03.
- TradingView official: the OAuth scopes and whether write tools can be withheld per grant.
- MT5: confirmed numeric `trade_mode` values (only DEMO = 0 is suggested, by the docs example).
- QMX: whether an engine step can run an external MCP tool through `[rules] always_allow` plus `external_tools_unattended` with no code change. This needs a run-time probe (4.2).
- The C-25 review note about an external MCP file tool. Dropped by the scope change and not traced.
