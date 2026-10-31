# The mini-app core: two fixes that truly block QMB, and the examples in CI

Part B, sub-area 6. Decision: spine AD-203. Slices: `BUILD-SLICES.md` B1, B2, B5.

**In plain words.** The mini-app core works and stays as built. Two small things stop QMB from being a proper app on it: a workflow cannot tell an app's job what to do, and an app's result cannot be filed through QMX's own scorer. This part fixes exactly those two, keeps everything else (the breaker, the limits he sets, the signature for the money app), and makes sure the example apps actually run.

His words: "So the reason why mini apps are like that is because of the logging and monitoring." (T3:1562); "Literally, a mini app can have a server of its own." (T3:1562). STATE midday rulings 46 (fix where it truly blocks) and 53 (handle the core with care, from the intent of how it was built).

Ledger rows that bind: MA-01 to MA-05, CC-26.

## 1. The intent of the core, read before touching it

From the workflow-engine spine (engine AD-64, CHECKED) and the code: things talk two ways, **ask** (an operation call or an `app_op` node, pinned to `(pack, version)`) or **leave** (land an artifact under a declared `provides` name; "the landing is the event"); an app's inputs are `feeds`, "wired by a trigger or a node input"; an app instance has one home; the app's own job queue is the only capacity a job takes (engine AD-58); limits are health guards for logging and monitoring, not caps (ruling 24; `qmx_apps/manifest.py:86-104` leaves memory unlimited unless he sets it).

## 2. What blocks QMB today (CHECKED)

| Block | Evidence | Effect |
| --- | --- | --- |
| A job request carries only its name | `qmx_apps/supervisor.py:1022` writes `{"job": job}`; `bootstrap.py:195-205` calls `run()` with no argument and answers `{"ok": True}` only | a workflow's `app_op` cannot say which unit, markets or window to test, and gets no result id back |
| An operation call stops the app after 30 s | `supervisor.py:957-963` (`timeout=30`, then `self.stop(app_id)`) | a backtest cannot be an operation call |
| An output lands as a plain `artifact` | `qmx_apps/artifacts.py:109-151` (`save` validates, hashes and hands a `Landing` to the host's `LibrarySink`) | a QMB result would bypass the run id, the try row and the `backtest-result` shape |
| No running example app works in two of four cases | `macro-daily-bias/macro_bias.py`, `weekend-watcher/server.py` import the deleted `qmx_agents` and LangChain (G4b §1.7) | a newcomer's first app crashes (MA-03) |

## 3. The two fixes

**Fix 1: jobs take inputs and return a result.**

| File | Change |
| --- | --- |
| `qmx_apps/supervisor.py` `run_job` | a keyword `inputs: Document | None = None` and `principal: str | None = None`; the request is `{"job": job}` exactly as today when `inputs` is None, else `{"job": job, "inputs": inputs}`; the answer's `result`, when present, is returned under `result`; feeds named in `inputs` are accepted through `artifacts.accept` as `_call` already does |
| `qmx_apps/bootstrap.py` `run_job` and `jobs` | reads `inputs` from the request; calls `run(inputs)` when `run` takes a parameter, else `run()` as today; puts a JSON-serialisable return value in the answer as `result`; an unserialisable return answers `ok: false` |
| `qmx_engine/nodes/app_op.py` | `parameters.inputs` (a table) merged over the node's `in` port value; with no inputs the node calls the two-argument `run_job(app, job)` exactly as today; with inputs it calls the pinned dispatcher with `inputs=`; the `remote` path receives inputs as a sixth argument only when there are some |
| `qmx_control/service.py` `app_job` | passes `inputs` and `principal` through to the supervisor |

**Fix 2: a provides contract may name a core lander.**

| File | Change |
| --- | --- |
| `qmx_apps/manifest.py` `Contract` | an optional `lander: str` (a registered core name); install refuses a lander name the host has not registered |
| `qmx_apps/supervisor.py` | an injected `Landers` port (`open`, `fail`); before queueing a job of an app whose provides name a lander, `open(app, version, job, inputs, principal)` returns a ticket whose run id and input folder are added to the inputs; when the job raises, the app stops first or the process dies, `fail(ticket, reason)` |
| `qmx_apps/artifacts.py` `save` | unchanged except that the `Landing` it hands the host's sink carries the contract's `lander` name; a job's answer may carry `{"output": name, "data": ...}` exactly as a tool's answer already may (`supervisor.py:907-912`), and `run_job` saves it through the same `save` |
| the host's Library sink (`qmx_host`) | for a landing whose contract names a lander, calls that lander's `close`; for every other landing, lands the plain `artifact` as today |

The supervisor never imports `qmx-judge`: the host composes the `qmb-run` lander and injects it. An app that names no lander sees no change at all.

## 4. Examples and first-party apps in CI (MA-03)

The two broken examples are rewritten against the current runtime or removed with a note in `examples/apps/README.md` (removal is his file deletion only if he prefers it; the default is rewrite). A test under `qmx-agents/packages/qmx-apps/tests/` installs every folder in `examples/apps/` and `qmx-agents/apps/`, starts it, calls each declared operation with its example input and runs each job once with a fixture input; `just ci` runs it.

## 5. Blast radius (CHECKED by running)

The one fact fix 1 is safe because of: **a request without inputs is byte-identical to today's, a `run()` without a parameter is called exactly as today, and `app_op` without inputs calls the two-argument runner**, so every shipped caller and test sees no difference.

- `scratchpad/l1b/patch_jobs.py` applied fix 1 to an overlay copy of `qmx_apps` and `qmx_engine` (three files). With the overlay first on the path, these ran against the real supervisor and the real app bootstrap: the shipped `qmx-engine/tests/test_app2a_app_op.py` and `test_app2b_routing.py`, the whole shipped `qmx-apps/tests/test_apps.py`, and the new `scratchpad/l1b/tests/test_job_inputs.py` (a job `run(inputs)` gets `parameters.inputs` merged over the `in` port and its result comes back on the node's `main`; an old `run()` job runs unchanged; a node without inputs calls the two-argument runner). Result: **36 passed** in 427 s.
- Fix 2 is unproven at step 4: the fact (an app with no `lander` lands exactly as today, because only a contract naming one re-routes the sink) sits at step 2, `artifacts.py:109-151`. Its slice (B5) carries the test: every shipped artifact test passes, and an app with a lander lands a `backtest-result`, never a plain `artifact`.

## 6. What stays exactly as built

The breaker and its default of 3 errors (Level 0 AD-33 adds the node's opt-in restart, Part C's); `isolation` unset by default; the money signature gate; the 30 s operation timeout; pins and profiles; homes and the volume lease; the artifact index and `stale_after`.

## 7. Cases handled here

MA-03 (examples in CI), MA-01 (a research app's breaker trip is a health stop; only the node sends orders), MA-04 (versioned provides with the built consumer check), MA-06 (QMB exists as an app), MA-07 (the default tester setting), MA-08 (a memory kill lands as killed with the limit), MA-09 (outputs read offline from the Library, built), MA-10 (provides namespaced by app id). MA-02 and MA-05 are Part C's.

## 8. Growth seam

A second lander (for example a research app that lands a `model`) is one more registered name; a job that needs no lander keeps the plain artifact path. Several jobs at once per instance would be a later setting on the bootstrap's job thread, not needed now.
