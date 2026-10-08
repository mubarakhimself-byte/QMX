# Broker reads and Portfolio proposals

`qmx-broker` serves `list_accounts`, `account_state`, `positions`, `quotes`,
`bars`, `symbol_info` and `propose_order` through FastMCP 4. `bars` accepts explicit
UTC millisecond bounds and a maximum of 1000 rows. All account calls require
broker, connection and account ids; native account ids may repeat across brokers.

Configure `brokers` through `qmx-control`'s settings REST/MCP operations:

```json
{"brokers":[{"id":"ic","name":"IC Markets","adapter":"ctrader","connections":[
  {"id":"demo","credential_ref":"qmx/ctrader-demo","environment":"demo",
   "accounts":[{"id":"101","currency":"USD","leverage":"50","permissions":["read","propose"]}]}
]}]}
```

cTrader also needs the existing node's pinned `protocol_path` (a serialized
protobuf FileDescriptorSet) and `protocol_tag`. This uses QMF's compiler and
framing; it does not install the Twisted SDK. Each read uses a short authenticated
TLS session and closes it, with bounded waits and request pacing. This is a
read adapter, not QMN's long-running execution connection. Tokens must already
be authorized; OAuth sign-up and refresh remain operator/node duties.

CCXT brokers use `adapter: "ccxt"` and an `exchange` id. Demo mode selects the
exchange's sandbox before other calls. Multi-account connections require a
distinct account `credential_ref` for each account, since CCXT has no universal
subaccount selector. The service reuses exchange instances so CCXT's rate limiter
survives repeated reads. Only active non-contract spot markets are accepted.
`spot.py` validates complete TICK_SIZE metadata; other metadata remains a read
view, without implying validation or execution authority. Spot positions mean
asset holdings.

Vault services are `qmx/<connection>` and usernames are `<connection>`.
cTrader bundles contain `clientId`, `clientSecret`, `accessToken`; CCXT bundles
contain `apiKey`, `secret` (and an exchange-required `password` if needed).
Store bundles through Credential Manager's secure input, never a settings file,
environment variable or command argument. Credential values never appear in read
results. Settings reload on each operation.

Proposals persist idempotently in the node's `portfolio.db` and are visible at
`GET /api/portfolio/proposals` and `portfolio_proposals` on qmx-control MCP.
They remain `awaiting_operator_signature`; there is no signing or submission API
here. The Copilot's built-in qmx-broker server uses the same service and replaces
its MCP proposal with the trusted local writer before P08 checks. External MCP
metadata cannot grant this exception.

Run offline checks with `uv run python -m pytest -n 2`. Fixtures follow the
official protocol/unified response schemas and explicitly identify themselves
as offline examples, not live broker captures.

Wire tests and cTrader response fixtures use the official [Spotware tag 91
definitions](https://github.com/spotware/openapi-proto-messages/tree/91), git
`017413087c1c23c1866bbf07ff24d56574047253`, compiled as a FileDescriptorSet with
protoc 36.2 (`--include_imports`). Their MIT license is included with the fixture.

Operator demo reads:

```powershell
uv run --project qmx-agents/packages/qmx-broker python scripts/live/smoke_broker.py --broker ic --connection demo --account 101 --symbol EURUSD
```
