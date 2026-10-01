# QMB and QML execution evidence

This note records the bounded worker and ledger repairs. It does not claim the QMB replay request, recorded-data materializer, or economic terminal ledger is complete.

## QML selected-source conformance

The production QMB sandbox now selects the unique conventional `factory.py:factory` entrypoint from the Bot's declared source manifest. The host and child both verify the callable's bytes against that manifest. The child keeps the complete manifest tree available for sibling imports through observation collection and clears imported manifest modules afterward. Missing factories, mismatched bytes, alternate callable selectors, and explicit silent fixtures refuse before a Layer-2 verdict can be minted. This convention is required because the current CT-33 LogicIdentity pins the source manifest but does not include a callable selector.

The relevant source and regressions are `qmb/src/qmb/host/runner.py`, `qml/src/qml/conformance/layer2.py`, `qmb/tests/test_sandbox.py`, and `qml/tests/test_layer2.py`.

## Governed terminal rows and child config integrity

QMB governed orchestration now records one terminal ledger row for completed or aborted jobs. If terminal persistence fails, remaining live siblings are reaped before return. The child reconstructs the run config and recomputes its fp1 from the decoded identity fields, refusing altered keys paired with a stale fingerprint.

The QML host adapter preserves typed CT-23 proposals on `RestingIntent.proposal`, and the runloop includes that typed proposal in its outcome identity. Unrecognized proposal objects are refused. It does not label a proposal Book-authorized or executable; Book admission is still required.

The QMB replay materializer reads CT-10 archive receipts through `SourceObservationBoundary` and the QMF `EvidenceStore`, checks replay world, quote-side coordinates, correction status, and bitemporal frontiers, then builds as-of QML read surfaces. Nested payloads are immutable and stream selection is fingerprinted. It preserves CT-10 `ForeignMoney`; constructing execution `Price` values requires explicit metadata whose fp1, CT-03 instrument, and exact source scale all match. CT-12 source admission now recomputes the manifest fingerprint and partitions source observations using both event and known-at times; the shared raw-content seal guard also includes `known_at_ns` so an event-only caller cannot understate a late arrival.

QMB now has a durable content-addressed `ReplayInputRequest` envelope. It pins the CT-12 manifest identity/ref and role, explicit CT-10 archive receipt refs, source stream, full CT-03 price metadata identity, selected CT-33 declaration/source, canonical parameter assignment, and injected state scope. Resolution requires the registry-resolved typed `SplitManifest` and separately supplied expected CT-12 ref, reads the receipts from the configured QMF store, runs selected-source Layer-2 conformance, and constructs the `HostedBot`. A persisted local-fixture test exercises this full resolution path with nested extra metadata and a source manifest-bound factory.

## Verification

`uv run --locked python -m pytest -q -p no:cacheprovider qmb/tests/test_sandbox.py qml/tests/test_layer2.py qmb/tests/test_orchestrator_spawn.py qmb/tests/test_orchestrator_ledger.py qmb/tests/test_orchestrator_abort.py` — 84 passed before the proposal-preservation follow-up.

`uv run --locked python -m pytest -q -p no:cacheprovider qmb/tests/test_ql7_host.py qmb/tests/test_sandbox.py qml/tests/test_layer2.py` — 52 passed with the proposal-preservation follow-up.

`uv run --directory qmb pytest -q tests/test_ql7_host.py tests/test_replay_materializer.py` — 14 passed after durable request integration and again after deep-freeze and full metadata-identity fixes.

`uv run --directory packages/qmf-data pytest -q tests/test_splits.py tests/test_seal.py tests/test_source_boundary.py` — 101 passed, including stale CT-12 fingerprint and event-before-seal/known-at-at-seal held-outs.

Scoped Pyright and Ruff checks passed on `qmb/src/qmb/host/replay.py`, `qmb/src/qmb/host/replay_request.py`, their focused tests, and the changed QMF CT-12/source-seal modules/tests.

`uv run ruff check qmb/src/qmb/host/replay.py qmb/src/qmb/host/adapter.py qmb/src/qmb/runloop/loop.py qmb/tests/test_replay_materializer.py qmb/tests/test_ql7_host.py` and targeted QMB Pyright on those modules/tests — passed.

`uv run --locked ruff check qmb/src/qmb/host/runner.py qml/src/qml/conformance/layer2.py` — passed.

Independent subprocess held-outs confirmed refusal for a manifest-bound throwing factory, missing source spec, silent fixture, and alternate entrypoint selector; a correctly bound sibling-import source succeeded. Independent terminal-ledger held-outs confirmed a live sibling is reaped when a governed refusal's ledger append fails.

## Remaining execution work

The request resolver currently stops after QML conformance and `HostedBot` construction. The governed child still needs to receive the request reference and resolve it against trusted CT-12/configuration artifacts. The Book handler now exists as a separate composition component, but the request resolver has not yet bound it to the runloop's per-slice paths. No completed governed run currently feeds CT-13-resolved CT-29 exits, net-of-fee closed trades, equity points, and journal events into CT-32 or records that economic result in its durable terminal ledger. ATC and optimization execution remain separate integration work; this evidence does not mark packet02 economic execution closed.
