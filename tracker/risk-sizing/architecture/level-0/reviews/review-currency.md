# Review: was every named technology checked against the web or the project?

The first configured finalize reviewer of `bmad-architecture` ("verify every committed decision was web-researched or reality-checked rather than asserted from training data"). Run by agent A0 in sequence, 31 Oct 2026. Web checks with Exa on the vendors' own pages; project checks against the lockfiles at `c93407ca`.

## Verdict

**Passes with three notes.** Every pinned version in the Stack table was read from the project's lockfiles, and the four that matter most were checked against the vendor today. Three pins are behind the latest release; the spine bumps none of them, because the pins are the code's and an upgrade is its own change with its own re-verification (V-L in `01-connections.md`).

## Pins

| Name | Pinned (where read) | Latest found today | Checked how | Note |
| --- | --- | --- | --- | --- |
| Python | 3.14.6 (scratch export venv, `qml/pyproject.toml` requires `>=3.14,<3.15`) | n/a | ran it | QML needs exactly 3.14.x (catalogue QML-25): servers get it through `uv`, as the PC does |
| claude-agent-sdk | 0.2.166 (`qmx-agents/uv.lock`) | 0.2.176, 31 Oct 2026 | Exa: github.com/anthropics/claude-agent-sdk-python/releases; pypi.org/project/claude-agent-sdk | ten releases behind; the harness owns the pin; no spine decision depends on a newer SDK feature, except that the plugin-hook probe must run on whatever version ships |
| ccxt | 4.5.85 (`qmx-agents/uv.lock`, installed copy) | 4.5.91, 29 Oct 2026 | Exa: github.com/ccxt/ccxt/releases; docs.ccxt.com changelog; ran the installed copy offline (`br9_ccxt_hyperliquid.py`) | six releases behind, including a Hyperliquid change (`params.fast` on `cancelOrders`); upgrading re-verifies every venue's capabilities (V-L) |
| OpenObserve | v1.1.2 (`qmx_host/connect_logs.py:78-81`) | v1.1.2, 20 Oct 2026 | Exa: github.com/openobserve/openobserve/releases; openobserve.ai/downloads | current |
| tzdata | 2025.2 (both lockfiles) | 2026.6 | research 54 §4.1 (pypi.org/project/tzdata, CHECKED 31 Oct) | old; AD-43 adds an age check; the bump is a build item |
| TA-Lib | 0.7.1 (both lockfiles) | not checked today | lockfile only | the docs' canonical arithmetic pin (DEC-0126 to DEC-0134); unchanged by this spine |
| FastAPI 0.142.2, pyarrow 25.0.1, jsonschema 4.26.0, protobuf 7.36.0, cronsim 2.7, optuna 4.9.0 | lockfiles | not checked today | lockfile only | unchanged by this spine; no decision depends on their newest features |
| cTrader Open API descriptor | `openapi-91.pb` shipped in `qmx_broker/protocol/` | n/a | G3 §2.1 (CHECKED there) | |

## Facts the spine relies on, and where they were checked

| Fact | Where checked |
| --- | --- |
| cTrader: protobuf on 5035; 50 requests a second, 5 for history; no server clock; no dead man's switch; no exchange futures | G3 §2.1 (code and Spotware's page, 31 Oct) |
| Hyperliquid: agent wallets, nonce window, per-IP limits, `scheduleCancel`, the 1,000 open-order cap | research 38 §3.8 (venue docs, 30 Oct); the pinned CCXT class's capabilities run offline today |
| Futures order flow: no free real-time CME data for an outside algorithm; Sierra Chart's data stays in its app; Databento, Rithmic, CQG routes | research 54 §1 (vendors' pages, 31 Oct) |
| Clocks: Windows Time support boundary; chrony over timesyncd; leap smear; DST dates 2026 | research 54 §4.1 (Microsoft, chrony FAQ, Google pages; `zoneinfo` run) |
| Measured latencies: about 160 ms TCP handshake PC to cTrader, about 31 ms to Hyperliquid, about 0.5 ms in-process fan-out | research 31, research 38 (measured 30 Oct) |
| The mini-app core's breaker, restart and money gate | `qmx_apps/supervisor.py`, `road/__init__.py` (read and one test run today) |

## Not checked

- The latest releases of TA-Lib and the six other libraries in the second row (no decision rests on them).
- Tailscale and chrony versions on his machines (external tools; not pinned by the repo).
