# Contracts and APIs: the connection points and what crosses each

**What this part is.** Who calls whom, where, and the shape that crosses each connection, inside QMX (QML, the copilot and agents writing to QML, the mini apps, the journals) and outside it (venues and data routes). The per-part files name their own connections; this file holds them in one table and sets the rules every shape follows.

**Verdict: core.** The shapes and the rules are core; most doors already exist (the catalog, mini-app operations, Library kinds), so the new work is a few shapes, not a new API layer.

## His words

- "Then, of course, we have internal contracts, QML itself, copilot or agents to QML." (T3:1264)
- "How do they connect? Who do they connect with?" (T3:903)
- "more like a male and female connector" (T2:135)
- "Live trading, which I think might have been catered for a bit, not fully, but a bit." (T3:1264)

## 1. What exists today

| Door or rule | State | Where checked |
| --- | --- | --- |
| One host per QMX folder serves chats, the engine, control doors and webhooks on one port behind one bearer | BUILT | G2 §6 |
| REST at `/api` with authenticated OpenAPI; streamable-HTTP MCP at `/mcp/`; both call the same service methods | BUILT | G2 §6 |
| One operation catalog: each capability one row; the REST route, the model's tool and the engine node type derive from it | BUILT | G2 §1.2 |
| Principals by route: `user`, `agent:<session>`, `workflow:<run_id>`, outside MCP clients as agents, observers | BUILT | G2 §6 |
| Error shape `{"error": {"code", "message"}}`, tools add `next_step`; the validate shape returns every problem as kind, where, message | BUILT | G2 §1.3, §2.1 |
| Event streams with resume; one held stream per reachable owned node | BUILT | G2 §6 |
| Data schemas: Library kinds as JSON Schema with `schema_version`; `qmx.workflow/1`; mini-app manifests with JSON Schema 2020-12 for operations and contracts | BUILT | G2 §6 |
| Store versions: open, upgrade after a copy, or refuse by name | BUILT (PR 213) | G2 §6 |
| API versioning policy | MISSING: routes carry no version; the API title is fixed at 0.1.0 | G2 §6 |
| Live contracts: CT-23 intents (no size today), the Book door's authorised intent, CT-19 commands, CT-20 events, reconcile, CT-29 exit records, CT-13 journal | BUILT | G3 §3 |
| Broker read result `{environment, is_live, connection_id, account_id, result}`; the agent's order proposal awaiting his signature | BUILT | G3 §3.2 |

## 2. Harvest

| Solution | Where | Fits now? |
| --- | --- | --- |
| The loop drawn once with what crosses each arrow; "none of these crossing shapes exists today except the trade kind and the price partitions" | research 52 §9.2 | Yes; the shapes below fill those arrows |
| The low-level shapes to settle: intent seam with size and exits, block interface, reading card, journal row and kinds, context receipt, safe resend, reconcile precedence, netting accounts, clocks, the server's journal queue, the conveyor's loop guard, the as-of query, the risk socket, protection after a dead man's switch, the order-budget gauge | research 43 §7 low level | Yes, each placed in a part file |
| Connection points for the agent lens (agent to checker, workflow to Library, agent to QMB, node's MIS to Library, unit journal to Library) | G4b §4.3 | Yes |
| The risk socket as a connector with readable inputs and slots | ledger C-06; `RISK-SIZING-PACK.md` §4; seams §6 | Yes |

## 3. The shapes

### Shape A. A few new shapes carried through doors that exist (recommended)

New internal shapes ride the catalog (rows), the mini-app core (operations and contracts) and the Library (kinds). No new API service.

### Shape B. A new internal unit API service

- **Why not.** A second door beside the catalog would split the copilot's reach from the workflows' (his ruling 8 holds by construction only with one catalog).

### Shape C. Shared Python types imported across packages, no schemas

- **Why not.** The node and the PC are different machines; mini apps are separate processes; a type import does not cross a network or a version boundary.

**Pick: Shape A.**

## 4. The new shapes (seven), and who owns each

| Shape | Owner (one writer) | Carried by | Defined in |
| --- | --- | --- | --- |
| Unit document `qmx.unit/1` | QML's schema; authors write it | Library `unit` kind fields | `unit.md` §3 |
| Check result (errors, warnings, checker version, catalogue snapshot) | QML | `unit_check` row; Library save refusal; plugin hook | `qml.md` §7 |
| QMB operations and the `backtest-result` extension | the QMB contract (any version implements it) | mini-app operations; core landing | `qmb.md` §6 |
| Node operations and its provides (`node_state`, `unit_states`, `heartbeat`) | the node app | mini-app operations; `app_op` with `remote` | `node.md` §4 |
| Journal envelope and kinds | the writer library | Parquet partitions with Library cards; `journal_query` | `journals.md` §3 |
| Reading card and stamped reading | the catalogue (cards); the MIS (stamps) | catalogue; market-data partitions; `provides.board` | `mis.md` §5 |
| Instrument record, venue rules row, account record | the venue refresh jobs | Library kinds; node snapshots | `instruments.md` |

Plus two shapes that change rather than appear: the CT-23 entry intent gains a size from the unit's sizer slot for units (the Book path stays), and the venue-client kind opens to `ccxt`.

## 5. Every connection point

| # | From | To | Where | What crosses | Door | Exists? |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Author (agent, copilot, him) | QML checker | any host | unit document; check result | `unit_check` row | row new; checks BUILT in shape |
| 2 | Author | Library | the host | unit document as a governed draft; every problem on refusal | Library save; kind validator | save BUILT; validator change |
| 3 | Copilot or agent | QMB app | PC (or the app's home) | run request; run handle; result id | `backtest` rows forwarding | rows BUILT; app new |
| 4 | Workflow | QMB app | the app's home | run request pinned to a version | `app_op` | BUILT |
| 5 | QMB app | core landing | the host | finished result; daily R stream | `backtest_and_land` | STACKED in PR 204 |
| 6 | QMB app | market-data door | the host | partitions by fingerprint; holdout per study | `materialise` | BUILT |
| 7 | QMB app, node app | QML | in process | compiled unit by id and version | the factory seam | BUILT seam |
| 8 | Judge | Library | the host | verdict; baseline card; proposal card | governed landing | landing BUILT |
| 9 | His click | node app | PC to the node's home | deployment (unit version, markets, account, mode) | `deploy` operation | new |
| 10 | Node app | venue | the node's machine | CT-19 commands; CT-20 events | venue-client port | BUILT laws; `ccxt` adapter new |
| 11 | Feed keeper | units, MIS instance | the node's machine | normalised prints, quotes, book updates, bars | in-process fan-out | new keeper; QMN intake reused |
| 12 | Node app, QMB app, feed keeper, MIS | journals | each writer's machine | envelope plus kind records | writer library | new |
| 13 | Node | PC Library | node to PC, one way | closed partitions and the live tail (journals, MIS history) | shipping job | new |
| 14 | Node | PC inbox | node to PC | heartbeat, node state, guard events | the host's held stream per node | BUILT |
| 15 | MIS app | market-data store, Library, board | each instance's machine | stamped readings; events; the board with `stale_after` | partitions; Library records; `provides` | homes BUILT |
| 16 | Unit (in the node) | board | the node's machine | optional placement read | read surface with `stale_after` | new |
| 17 | Agents and templates | journals, MIS logs, instruments | any host | queries with a time window | `journal_query`, `readings_query`, `instrument_get`, `data_features` | `data_features` BUILT; others new |
| 18 | Venue refresh jobs | instrument records | any host with a read grant | new record versions | Library kinds | new |
| 19 | Risk session | unit socket | in the unit | exit set, sizer, halts, kill-switch values | the socket's slots | placeholders now |
| 20 | Lab | MIS | PC | trained model readings, in shadow | Library model items | training placement BUILT |

## 6. The rules every shape follows

1. **JSON Schema 2020-12 with a `schema_version`** (the mini-app manifest's validator, G2 §6).
2. **Addable, never redefined.** A field or a kind may be added; an existing meaning never changes (the CT-13 and CT-19 rule, already in code).
3. **A breaking change is a new schema version plus an upgrade script**, the same pattern as store versions (PR 213). Old records never migrate in place; readers read every version they support.
4. **API versioning** (the gap G2 found): the catalog row's input and output schemas carry their `schema_version`; a route serving two versions names the version in the request; the OpenAPI title follows the host's build.
5. **Errors** keep the shipped shape; **checks** return every problem as kind, where (a JSON pointer), message, hint.
6. **Every number crossing a boundary is exact** (QMF's exact money and rationals) or carries its unit kind; never a bare float for money.
7. **Every time crossing a boundary is UTC nanoseconds or ISO-8601 UTC text**, with venue and receive time on market events (`devops-and-clocks.md`).
8. **One writer per stream or partition**; every reader is read-only.

## 7. External ports

- **Venue-client port** (BUILT laws, opened): `kind`, `venue_id`, `world`, `open_session`, `close_session`, `verify_capabilities`, `submit`, `observations`, `reconcile`; CT-18 capability declaration plus a measured profile; an error map where an unmapped code means UNKNOWN plus an alarm (G3 §3.2). Adapters: `ctrader` (kept), `ccxt` (new), futures placeholders.
- **Data-route port** (new): `kind`, `instruments`, `levels` offered (with the three splits), `licence`, `subscribe`, `history`; it emits the internal print, quote, book and bar shapes. Adapters: cTrader, CCXT venues, Dukascopy and Binance Vision downloaders (BUILT as templates), Databento (key check today), futures placeholders.
- **Sign-in:** each venue's own web sign-in (OAuth for cTrader), keys in the machine's store; QMX never handles a password (CC-13).

## 8. The risk socket, as a connector (room only)

Male side (what the unit offers): the slots (exit set at position, unit and account scope; one sizer; halts at three scopes) and the readable inputs (entry and stop, instrument facts, account facts, the unit's journal in R, market statistics, his limits). Female side (what the risk session plugs in): blocks for those slots and the kill-switch effect values. Today each slot holds a labelled placeholder (`unit.md` §7). The socket must not depend on the router, the MIS, the PC link or the Library at trade time (pack §4).

## 9. Open for the architecture step

1. Which shapes get a CT number in `docs/contracts/` (the doc pass after the build) and which stay as Library kind schemas only.
2. Whether the data-route port and the feed keeper share one interface.

## 10. Parked

- Generated TypeScript client types for the UI (the UI session's).
- A webhook sender signature check (a known backlog item, G2 §6).
