# QMX domain tools

`default_tool_registry(DomainContext(...))` and `create_server(group, context)` expose the same thirteen functions. AgentSpec names use `qmx-data.read_bars`, `qmx-backtest.run_backtest`, `qmx-research.qml_run`, and `qmx-node.node_state`; callable tool names use underscores for model-provider compatibility.

The host supplies a QMF `AppendStore` and dataset fingerprints, registered QMB run keyword arguments (strategy handler, slices, resolved configuration), QML `HostedBot`s with recorded read surfaces, and a QMN `DoorRuntime`. Agent inputs cannot select executable code or filesystem roots. QMB runs are synchronous in this packet; the returned status describes the persisted completed result. QML evaluates recorded instants and returns admitted intents. Order proposals are immutable artifacts awaiting the operator's signature, with no execution capability.

All tools accept `response_format` (`concise` or `detailed`); lists accept `limit` and an offset `cursor`. Large results return an artifact reference, and pages retain `next_cursor`. Backtest results expose summaries or detailed slices, and comparisons read their CT-32 containers.

The stdio commands are `qmx-mcp-data`, `qmx-mcp-backtest`, `qmx-mcp-research`, and `qmx-mcp-node`. `QMX_TOOLS_ROOT` selects the host's volume (default `~/.qmx`, shared with qmx-control). `datasets.json` contains the typed `Dataset` entries and `market/` holds the QMF replay store. Rich runtime bindings are injected by the Python host; an unconfigured capability returns an actionable error. No live feed, credentials, or venue powers are installed by these commands.
`QMX_TOOLS_FACTORY=module:function` lets a trusted stdio launcher supply the same rich DomainContext used by the Python host. Agents cannot set this environment binding.

Domain saves, spilled results and backtests use qmx-control's Library and emit its
events. Legacy `artifacts/<sha256>.json` envelopes are indexed on first open;
old references remain readable. `DomainContext.backtest_identities[config_ref]`
is a `qmx_control.models.MemoKey` with `strategy_version`, `data_snapshot`,
`params` and `engine_version`. A registered identity reuses its stored result
before calling QMB and includes `memo_key` in the response. The host must tie
those four values to the actual registered inputs. Configurations without complete
identity metadata execute normally. The pure quant engine remains unchanged.
