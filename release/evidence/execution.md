# QMB and QML execution evidence

This note records the bounded worker and ledger repairs. It does not claim the QMB replay request, recorded-data materializer, or economic terminal ledger is complete.

## QML selected-source conformance

The production QMB sandbox now selects the unique conventional `factory.py:factory` entrypoint from the Bot's declared source manifest. The host and child both verify the callable's bytes against that manifest. The child keeps the complete manifest tree available for sibling imports through observation collection and clears imported manifest modules afterward. Missing factories, mismatched bytes, alternate callable selectors, and explicit silent fixtures refuse before a Layer-2 verdict can be minted. This convention is required because the current CT-33 LogicIdentity pins the source manifest but does not include a callable selector.

The relevant source and regressions are `qmb/src/qmb/host/runner.py`, `qml/src/qml/conformance/layer2.py`, `qmb/tests/test_sandbox.py`, and `qml/tests/test_layer2.py`.

## Governed terminal rows and child config integrity

QMB governed orchestration now records one terminal ledger row for completed or aborted jobs. If terminal persistence fails, remaining live siblings are reaped before return. The child reconstructs the run config and recomputes its fp1 from the decoded identity fields, refusing altered keys paired with a stale fingerprint.

The QML host adapter preserves typed CT-23 proposals on `RestingIntent.proposal`, and the runloop includes that typed proposal in its outcome identity. Unrecognized proposal objects are refused. It does not label a proposal Book-authorized or executable; Book admission is still required.

The QMB replay materializer reads CT-10 archive receipts through `SourceObservationBoundary` and the QMF `EvidenceStore`, checks replay world, quote-side coordinates, correction status, and bitemporal frontiers, then builds as-of QML read surfaces. Nested payloads are immutable and stream selection is fingerprinted. It preserves CT-10 `ForeignMoney`; constructing execution `Price` values requires an explicit metadata identity whose fp1, CT-03 instrument, and exact source scale all match. A persisted local-fixture test drives a selected `HostedBot` callback through `qmb.run()` and observes its typed proposal.

## Verification

`uv run --locked python -m pytest -q -p no:cacheprovider qmb/tests/test_sandbox.py qml/tests/test_layer2.py qmb/tests/test_orchestrator_spawn.py qmb/tests/test_orchestrator_ledger.py qmb/tests/test_orchestrator_abort.py` — 84 passed before the proposal-preservation follow-up.

`uv run --locked python -m pytest -q -p no:cacheprovider qmb/tests/test_ql7_host.py qmb/tests/test_sandbox.py qml/tests/test_layer2.py` — 52 passed with the proposal-preservation follow-up.

`uv run --directory qmb pytest -q -p no:cacheprovider tests/test_replay_materializer.py tests/test_ql7_host.py tests/test_execution_ports.py tests/test_execution_composition.py` — 35 passed.

`uv run ruff check qmb/src/qmb/host/replay.py qmb/src/qmb/host/adapter.py qmb/src/qmb/runloop/loop.py qmb/tests/test_replay_materializer.py qmb/tests/test_ql7_host.py` and targeted QMB Pyright on those modules/tests — passed.

`uv run --locked ruff check qmb/src/qmb/host/runner.py qml/src/qml/conformance/layer2.py` — passed.

Independent subprocess held-outs confirmed refusal for a manifest-bound throwing factory, missing source spec, silent fixture, and alternate entrypoint selector; a correctly bound sibling-import source succeeded. Independent terminal-ledger held-outs confirmed a live sibling is reaped when a governed refusal's ledger append fails.

## Remaining execution work

The governed worker still needs a durable request envelope that resolves pinned registry fragments and a recorded QMF Parquet artifact into replay observations. The host adapter preserves Bot proposals, but has not yet converted them through the Book's CT-23 door into authorized resting orders. No completed run currently feeds actual CT-29 exits, net-of-fee closed trades, equity points, and journal events into CT-32. Those are the next implementation steps; this evidence does not mark packet02 economic execution closed.
