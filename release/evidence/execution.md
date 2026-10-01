# QMB and QML execution evidence

This note records the QMB/QML execution repairs and the verified local recorded-replay path. The CLI subprocess check uses the checkout's editable workspace environment; it is not evidence from the final frozen installed bundle.

## QML selected-source conformance

The production QMB sandbox now selects the unique conventional `factory.py:factory` entrypoint from the Bot's declared source manifest. The host and child both verify the callable's bytes against that manifest. The child keeps the complete manifest tree available for sibling imports through observation collection and clears imported manifest modules afterward. Missing factories, mismatched bytes, alternate callable selectors, and explicit silent fixtures refuse before a Layer-2 verdict can be minted. This convention is required because the current CT-33 LogicIdentity pins the source manifest but does not include a callable selector.

The relevant source and regressions are `qmb/src/qmb/host/runner.py`, `qml/src/qml/conformance/layer2.py`, `qmb/tests/test_sandbox.py`, and `qml/tests/test_layer2.py`.

## Governed terminal rows and child config integrity

QMB governed orchestration now records one terminal ledger row for completed or aborted jobs. If terminal persistence fails, remaining live siblings are reaped before return. The child reconstructs the run config and recomputes its fp1 from the decoded identity fields, refusing altered keys paired with a stale fingerprint.

The QML host adapter preserves typed CT-23 proposals on `RestingIntent.proposal`, and the runloop includes that typed proposal in its outcome identity. Unrecognized proposal objects are refused. It does not label a proposal Book-authorized or executable; Book admission is still required.

The QMB replay materializer reads CT-10 archive receipts through `SourceObservationBoundary` and the QMF `EvidenceStore`, checks replay world, quote-side coordinates, correction status, and bitemporal frontiers, then builds as-of QML read surfaces. Nested payloads are immutable and stream selection is fingerprinted. It preserves CT-10 `ForeignMoney`; constructing execution `Price` values requires explicit metadata whose fp1, CT-03 instrument, and exact source scale all match. CT-12 source admission now recomputes the manifest fingerprint and partitions source observations using both event and known-at times; the shared raw-content seal guard also includes `known_at_ns` so an event-only caller cannot understate a late arrival.

QMB now has a durable content-addressed `ReplayInputRequest` envelope. It pins the CT-12 manifest identity/ref and role, explicit CT-10 archive receipt refs, source stream, full CT-03 price metadata identity, selected CT-33 declaration/source, canonical parameter assignment, and injected state scope. Resolution requires the registry-resolved typed `SplitManifest` and separately supplied expected CT-12 ref, reads the receipts from the configured QMF store, runs selected-source Layer-2 conformance, and constructs the `HostedBot`. A persisted local-fixture test exercises this full resolution path with nested extra metadata and a source manifest-bound factory.

## Selected bot through the Book and economic path

`execute_recorded_replay_request` re-resolves the immutable request and CT-10 receipts from operator-supplied roots immediately before execution. It rejects a changed request ref, altered quote path, foreign request ref, or malformed source graph. The selected `HostedBot` receives only its declared, deeply immutable QML evidence. Its CT-23 entry proposal passes Book admission, exact size derivation, configured fill and cost adapters, and a declared protective stop. The stop crosses a later persisted bid, producing a CT-29 close and CT-32 result. The exact local fixture economics are gross -104 USD, fees 2 USD, net -106 USD, and net R -53/50; a separate 1 bp slippage control produces no fill and no trades.

The operator-owned CLI binding is a content-addressed descriptor selected by trusted QMA run/evidence/split references. It pins CT-06 bot/Book/BMS records, registry as-of, request/raw/journal/ledger roots, the QMB builder source bytes and entrypoint, and the complete behavior policy derived from the resolved config, execution adapters, Book policies, exit module, and calendar. The QMB console-script entrypoint in the checkout environment was invoked as a fresh subprocess against persisted CT-06 and CT-10/12 fixture data. The subprocess returned CT-32 and terminal-line fingerprints; a physical read of the terminal ledger confirmed its CT-32 fingerprint matches the response.

QML evidence construction now freezes nested caller-owned maps/lists and recursively validates supported QMF exact nouns through their typed constructors. Unsupported canonical-but-mutable objects, nested binary floats, malformed nested `Price`/`Instrument` values, and provisional samples are refused.

## Verification

`uv run --locked python -m pytest -q -p no:cacheprovider qmb/tests/test_sandbox.py qml/tests/test_layer2.py qmb/tests/test_orchestrator_spawn.py qmb/tests/test_orchestrator_ledger.py qmb/tests/test_orchestrator_abort.py` — 84 passed before the proposal-preservation follow-up.

`uv run --locked python -m pytest -q -p no:cacheprovider qmb/tests/test_ql7_host.py qmb/tests/test_sandbox.py qml/tests/test_layer2.py` — 52 passed with the proposal-preservation follow-up.

`uv run --directory qmb pytest -q tests/test_ql7_host.py tests/test_replay_materializer.py` — 14 passed after durable request integration and again after deep-freeze and full metadata-identity fixes.

`uv run --directory qmb pytest -q tests/test_operator_replay.py tests/test_qma_cli.py tests/test_operator_replay_process.py tests/test_replay_execution.py` — 11 passed, including the fresh QMB CLI subprocess and durable terminal-line readback.

`uv run --directory qml pytest -q` — 332 passed after recursive exact-value and typed-noun validation.

`uv run --directory packages/qmf-data pytest -q tests/test_splits.py tests/test_seal.py tests/test_source_boundary.py` — 101 passed, including stale CT-12 fingerprint and event-before-seal/known-at-at-seal held-outs.

Scoped Pyright and Ruff checks passed on `qmb/src/qmb/host/replay.py`, `qmb/src/qmb/host/replay_request.py`, their focused tests, and the changed QMF CT-12/source-seal modules/tests.

`uv run ruff check qmb/src/qmb/host/replay.py qmb/src/qmb/host/adapter.py qmb/src/qmb/runloop/loop.py qmb/tests/test_replay_materializer.py qmb/tests/test_ql7_host.py` and targeted QMB Pyright on those modules/tests — passed.

`uv run --locked ruff check qmb/src/qmb/host/runner.py qml/src/qml/conformance/layer2.py` — passed.

Independent subprocess held-outs confirmed refusal for a manifest-bound throwing factory, missing source spec, silent fixture, and alternate entrypoint selector; a correctly bound sibling-import source succeeded. Independent terminal-ledger held-outs confirmed a live sibling is reaped when a governed refusal's ledger append fails.

## Remaining integration work

The real QMB console script has been exercised directly in a fresh child process. The complete registered CT-47 `ExperimentSpec` → QMA `BacktestingService` → `CliQmbDoorTransport` → QMB child journey, including environment-dispatch lease lifecycle, terminal projection, restart/cancel, and second-pack execution, still needs an end-to-end acceptance run. The editable-workspace subprocess test does not substitute for that journey or for the frozen installed bundle. Book optimization has a provider-free two-generation replay study with durable trial results. Full generic ATC terminal persistence, optimization, and registered ingress remain under implementation. Separate non-editable installed replay evidence is recorded in `installed-recorded-replay.md`; it does not close the QMA worker journey or final-candidate acceptance. External provider verification remains pending.
