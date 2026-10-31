# Mini apps: the white-label core and what sits on it

**What this part is.** The cross-cutting verdict he asked for: which parts are the small solid core and which are mini apps on the core, with defaults out of the box; the extension points that must stay stable; and the mini-app template built only from what exists. QMB and the trading node are the first two mini apps (`qmb.md`, `node.md`); the MIS's publishing process is the third (`mis.md`).

**Verdict.** The mini-app core stays as built. Nothing in it must change for units; the few optional changes below are shipped defaults, not new machinery.

## His words

- "it's like handing someone white label software" (T3:1338) "Okay, think of Shopify." (T3:1338)
- "Most things can actually become mini apps." (T3:1383) "the core idea is QMX is meant to be extensible by design" (T3:1383)
- "Mini apps came in because of the same pattern." (T3:1264)
- "Literally, a mini app can have a server of its own." (T3:1562)
- "So the reason why mini apps are like that is because of the logging and monitoring." (T3:1562)
- "Maybe you can have a version or a template of a mini app using what is already there." (T3:1562)
- "units might be need to be integrated in mini apps" (T3:1102)

## 1. What exists today

| Piece | State | Where checked |
| --- | --- | --- |
| A mini app is an immutable image plus an `app.toml`: id, version, risk (`shows`, `runs`, `money`), kind, entrypoints (an MCP server is required; jobs, agents, workflows, a UI), capabilities (network allow-list, secrets by key-store name, data reads) | BUILT | G2 §5.1 |
| `[operations]` are the only way in, each with input and output schemas, an approval, a reversibility and `state: none | instance`; `[provides]` and `[feeds]` contracts with `stale_after`; `[profiles]`; `[suggested_trigger]`; `[isolation]`; `[breaker]` | BUILT | G2 §5.1; read this session: `examples/apps/macro-daily-bias/app.toml` |
| `app_op` runs an operation in the app's supervised process, with a version pin and a profile; an instance's home may be another machine, reached through `remote`; an unreachable home waits, never fails | BUILT | read this session: `qmx-engine/src/qmx_engine/nodes/app_op.py` docstring |
| Isolation: a Job object on Windows, Docker elsewhere; memory and CPU unset by default (unlimited); 16,384 MB is only the top of a value he may set | BUILT | read this session: `qmx-apps/src/qmx_apps/manifest.py:81-110` |
| The breaker trips after `max_errors` (default 3, any positive number) or a 10 s heartbeat gap, logs `breaker_open` with the reason and persists the state; the supervisor has a `restart` operation | BUILT | read this session: `supervisor.py:828`, `:863` |
| A `money` app cannot start until a proposal-only version is published with his signature | BUILT | G2 §5.1 |
| The copilot's `apps_admin` toolset builds apps; publishing and enabling are his clicks; the `app-builder` sub-agent; the `build-mini-app` skill is a 5-line placeholder | BUILT / placeholder | G4b Q5 |
| Four example apps, none installed, two importing deleted code; no real mini app designed | BUILT as examples | G4b Q5 |

## 2. Harvest

| Solution | Where | Fits now? |
| --- | --- | --- |
| The pattern: one catalog, one Library, one engine, one host; mini apps, packs, workflows and the Lab add only manifests and content on that core; a unit template is the same move (a kind with a real schema, rows, templates) | G2 §5.4 | Yes |
| What a mini-app template holding a unit would need, using only what exists: a headless `app.toml` with an MCP server and operations (`check`, `backtest`, `latest`), `provides` with `stale_after`, `feeds`, optional profiles, a suggested trigger, logic in plain Python beside the server | G4b Q5 | Yes, but a unit does not trade inside it (only the node sends orders) |
| QMB packaged as a real mini app answers workflows through `app_op` with no engine change | G4b Q4 | Yes (`qmb.md`) |
| A mini app's limits are health guards for logging and monitoring, not caps | G4b §3 row 8; STATE mid r24 | Yes |

## 3. The verdict per part

| Part | Core or mini app | Why |
| --- | --- | --- |
| QML (the library, compiler, checker) | core | two versions disagreeing would give silent wrong answers |
| The dictionary and catalogue | core | every agent and unit must read one vocabulary |
| The unit template (a Library kind) | core | units are items, run by apps; never an app themselves |
| The judge, the try ledger, the study spec | core | a swapped tester must not change the score |
| Journals (record shapes, writer library, door) | core | one envelope everyone slices by |
| Instrument records | core | facts every part reads |
| Contracts and their rules | core | |
| QMB | **mini app** (risk `runs`) | he may want a new version or several side by side |
| The trading node | **mini app** (risk `money`) | contained so the kill switch works; homed on a server of its own |
| The MIS's publishing process | **mini app** (risk `shows`), two instances | lives on machines; readings themselves are core |
| Workflow templates | content on the core engine | removable and improvable |
| The copilot and agents | core (built) | |
| The Lab and the pods | core workspaces (built and designed) | the pods are the risk session's representation |

## 4. The stable extension points (the white-label core's promise)

What someone (him, the copilot, an agent) builds on without touching the core, each with a schema version and the "addable, never redefined" rule (`contracts.md` §6):

1. Catalogue entries and blocks (`dictionary.md`).
2. Unit documents and templates (`unit.md`).
3. Mini-app manifests and their operations, provides and feeds.
4. Workflow templates (`workflows.md`).
5. The venue-client port and the data-route port (`external.md`).
6. Reading cards (`mis.md`).
7. Journal record kinds (`journals.md`).
8. The QMB contract and its conformance pack (`qmb.md`).
9. Skills and sub-agents in packs and the core plugin.
10. Instrument and venue records (`instruments.md`).

## 5. The shapes

### Shape A. Three default mini apps on the unchanged core, plus one template (recommended)

- **What.** QMB, the trading node and the MIS ship as first-party mini apps, installed and enabled with defaults. QMB's app is the worked example in a filled `build-mini-app` skill, which is the template he asked for.
- **Explain.** "QMX has a small core that must always agree with itself. Everything that runs on a machine, and that you might want a second version of, is an app on that core."

### Shape B. Everything an app, QML and the dictionary included

- **Why not.** Two QML versions or two dictionaries running side by side would let two units mean different things by the same word.

### Shape C. Only QMB as an app; the node and the MIS in the core

- **Why not.** It loses the node's signature gate and its server of its own, and keeps QMN's Linux-only pieces (`node.md` §3).

**Pick: Shape A.**

## 6. A unit and a mini app (his "units might be need to be integrated in mini apps" (T3:1102))

A unit is never a mini app (S147): it is a Library item that QMB runs on history and the node runs on practice and live. A mini app may **contain** a unit's logic in plain Python (ledger MA-03) or an ML model, and publish it as a unit item through the authoring door; it never trades it itself. A learned unit's weights travel as unit artifacts loaded through an injected read surface (S148). An optional "unit companion" template (a headless app with `check`, `backtest` forwarding to QMB, and `latest` operations around one unit family) is parked until a real need appears.

## 7. Optional shipped defaults (no change to the mini-app core's code)

| Default | Reason, one line |
| --- | --- |
| The first-start card offers one click: "Turn on QMB, the MIS and the practice node" | enabling an app is his act by design; one click keeps out of the box simple (CC-15) |
| The node app's manifest sets its own breaker values (a higher `max_errors`) and runs its own inner supervisor | per-app values are allowed; the breaker still logs every trip |
| `app:qmb` in the default home preset, only if the forwarding rows prove awkward | the copilot's reach to QMB (`qmb.md` §8) |

## 8. Out of the box, for someone who was not in the planning

1. First start: the Library opens; the dummy unit is in it.
2. One click turns on QMB, the MIS and the practice node.
3. The connect dialog's "Trading node" kind, first card: practice on This PC; the cTrader demo sign-in in the browser.
4. The self-test lands a passport; the node shows "running"; the dummy unit trades on demo.
5. The copilot answers "why didn't it trade?" from the journal.

## 9. Connection points

The per-app files hold them; the shared ones: `app_op` from workflows, the catalog rows from the copilot, the core landing for QMB results, the deploy operation for the node, `provides.board` for the MIS.

## 10. Open for the architecture step

1. Where first-party apps live in the repository and how they install by default.
2. Whether `money` apps get a different default breaker in the manifest model (a value, not code).

## 11. Parked

- The unit companion template (§6).
- Rewriting the two broken example apps (a backlog item, outside this build).
