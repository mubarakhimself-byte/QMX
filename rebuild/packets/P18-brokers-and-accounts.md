# P18: Brokers, connections and accounts (cTrader / IC Markets, CCXT)

## Goal
QMX trades CFDs through IC Markets on cTrader and crypto through CCXT. The model allows many brokers, many connections and many accounts per connection. The Copilot gets a cTrader MCP server by default.

## Read first
- `rebuild/DESIGN.md` §11
- `packages/qmf-venue/src/qmf/venue/ctrader.py`, `connection.py`, `commands.py`, `encode.py`, `spot.py`
- `qmn/src/qmn/venue/spot_paper.py`
- Memory rule: broker credentials live only in Windows Credential Manager under `qmx/*`, never in the repo, chat or `.env`

## Build
1. **Model:** `Broker` → `Connection` (credentials ref, environment demo|live) → `Account` (id, currency, leverage, permissions). Store it in the node's settings, editable in the UI via `qmx-control`.
2. **cTrader adapter:** confirm that the existing `qmf-venue` cTrader code covers:
   - auth (application and account tokens)
   - symbols, quotes and bars
   - account state and positions
   - order placement on demo

   List the gaps in the PR and close the small ones. Demo accounts only in tests (recorded fixtures) and live scripts (operator-run).
3. **CCXT:** the same `Connection`/`Account` model over CCXT exchanges (spot first). Reuse `spot.py`.
4. **MCP server `qmx-broker`** (FastMCP):
   - read-only tools: `list_accounts`, `account_state`, `positions`, `quotes`, `bars`, `symbol_info`
   - one money tool: `propose_order`, which is flagged money-path (P08) and goes to the Portfolio signature queue
   - added to the Copilot spec by default
5. **Hummingbot review:** a short note (`rebuild/reports/hummingbot-ideas.md`) on connector design and crypto strategy patterns worth borrowing. No code import.

## Tests
Recorded-fixture tests per adapter; the multi-account model; `propose_order` never sends; MCP tools list and call in-process.
