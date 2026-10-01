# Independent execution review — in progress

Reviewer: GPT 6.1 Sol. Governing documents remain origin/main
`c3e8ec5ef33d0b38cdf7f5dbdd48a6fc70ac33cf`; reviewed packet 02 and current
QMB/QML delta read-only. Final implementer commit is pending. Environment is the
release checkout's existing `.venv`, Linux, CPython 3.14.7.

## Blocking current findings

QL01: parent `run_sandbox` validates factory membership, but the isolated
worker `_worker_collect` does not. It accepts unrelated `factory_spec.source`
or defaults a missing spec to the silent fixture, while
`collect_layer2_observations` validates only the claimed source manifest.

Held-out actual-process reproduction builds a BotDefinition whose manifest-bound
`research_bot/factory.py` raises RuntimeError on every logic call. Using normal
`_encode_payload`, replace factory_spec with the clean silent FunctionFactory
source, then invoke `[sys.executable, '-B', '-m', host_runner._WORKER_MODULE]`
with the JSON payload. Decode using `_verdict_from_envelope`: **Ok Layer2Verdict**.
Remove factory_spec and repeat: **Ok Layer2Verdict**. Expected is source identity
refusal or execution of the selected throwing factory followed by conformance
failure. These are real subprocess worker calls, without executable doubles.
The patch must enforce factory/source identity at the receiving process boundary.

Source finding: `_drain_governed` and `_collect_all` call `_append_terminal`
after a collected refusal. If terminal persistence fails, both return immediately
without reaping remaining owned live children. Their completed-result branches
do perform cleanup on the same ledger failure. This requires a held-out refusal
plus ledger failure plus sibling-process check before final acceptance.

Both findings were sent to the implementer/coordinator early. Numeric/data review
results are recorded separately in numeric-review.md. Selected-source economic
execution, truthful collector evidence, installed CLI request behavior, and final
terminal-record acceptance are still pending; no execution acceptance is claimed.

## Interim correction retest

The receiving worker now refuses mismatched and missing specs in the actual
subprocess probes. A correctly matched throwing source exits without a false
verdict. The ledger failure branches now call owned-child cleanup by source
inspection.

However, the normal public `run_sandbox` with the same always-throwing bound
source and explicit `factory_spec={'kind':'silent'}` still returns **Ok
Layer2Verdict**. This is a remaining source-attribution blocker even though the
fixture is explicit. The implementer received this public-path reproduction.

Independent affected command:

```sh
.venv/bin/python -m pytest -q -p no:cacheprovider qmb/tests/test_sandbox.py qml/tests/test_layer2.py qmb/tests/test_orchestrator_ledger.py qmb/tests/test_orchestrator_abort.py qmb/tests/test_orchestrator_spawn.py
```

Result: **80 passed, 2 failed in 16.40s**. Both abort sibling controls construct
run configs with noncanonical fingerprints and now fail the new child decoder
check. The positive sibling fixtures need valid identities while the negative
tamper controls must remain. Final committed tests and rerun are pending.

The revised parent now refuses explicit silent fixtures and alternate callable
selectors. A held-out relative lazy import during logic evaluation passes, proving
the manifest tree stays available for the observation lifetime. However, a direct
actual worker payload selecting `research_bot.factory:other` still returned an
ordinary passing verdict when the same file's conventional `factory` always
throws and `other` is silent. The worker must enforce the same unique conventional
selector as the parent, because CT-33 currently binds bytes rather than a callable
selector. This additional process-boundary defect was reported before final commit.

## Latest corrected candidate

The worker now independently requires the unique conventional `factory.py:factory`
selector. Four actual-process held-outs all refuse: alternate selector, explicit
silent fixture, missing spec, and correctly bound throwing logic. The lazy relative
import positive control passes. A separate held-out test with two real owned child
processes injects a collected refusal plus ledger append failure into `_collect_all`;
the remaining sibling is killed before the refusal returns. Test processes were
always cleaned up in a finally block.

The same affected pytest command now passes **83/83 in 16.73s**, including valid
canonical abort sibling fixtures. These overlap earlier runs and implementer counts.
Source/fixture approval for these bounded changes is ready pending final commit.
This does not close QB01–QB03 or the complete QB04 terminal matrix, nor establish
the installed selected-bot economic evidence chain.

## Durable CT-29 projection review

Reviewed base `ebd338fe` and corrective
`e8b9b95b05e89c04d71ca1a712a30dbd93939048`. Bounded CT-13-to-CT-29-to-ClosedTrade
projection is **approved** under its declared caller dependencies. An initial
held-out found two correctly fingerprinted CT-29 records for the same virtual
position were projected as two trades. Corrective commit now refuses duplicate
virtual positions as well as duplicate record refs, preserving the one-close law.

Held-out exact accounting uses gross PnL 500, commission 50 and financing credit
-10 (all USD scale 2): projection returns net 460 and fees 40, retains explicit
SHORT side, exact close Instant and record/event refs. Foreign WriterId and epoch
refuse. Source verifies record fingerprint, result label, event time and epoch
before projecting. The caller's record resolver and position-side mapping must
come from its actual durable rooms/opening-position ledger; this adapter does
not independently prove the persistence or authority of an arbitrary mapping.

Independent current affected command:

```sh
.venv/bin/python -m pytest -q -p no:cacheprovider qmb/tests/test_results_ct29.py qmb/tests/test_replay_materializer.py qmb/tests/test_ql7_host.py qmb/tests/test_event_slice_loop.py qmb/tests/test_execution_ports.py qmb/tests/test_execution_composition.py
```

Result: **54 passed in 1.67s**. This overlaps implementer runs and does not
establish the installed selected-bot economic execution chain.

## Recorded replay materializer — correction pending

The new adapter resolves actual persisted CT-10 receipt refs through QMF's source
boundary, preserves exact source quote amounts/scales and refuses unsupported
correction folds. Execution prices require explicitly fingerprinted instrument
metadata; it does not infer scale from the symbol.

Held-out actual-room probe found returned nested read-surface frames remain
mutable: changing `samples[0].value.bid.amount` changes subsequent readback while
the source fingerprint is unchanged. Reported to execution owner for deep
freezing. The same refs under different stream aliases also yielded the same
materializer fingerprint despite different output slices/surfaces; alias mapping
needs identity binding. Replay approval remains pending these corrections.

The typed proposal correction refuses mutable/untyped proposals and retains
CT-23 proposal identity separately from authorization. Its final commit remains
pending; preserving a proposal alone does not authorize execution.

## Final bounded replay/proposal review binding

Replay/proposal commit `85212ad621de175171eb113a05d12e0cb1119535` is independently
reviewed and **approved within its declared source/replay scope**. Actual
persisted-room held-outs now refuse nested mutation, preserve original reread
amounts and source fingerprint, and produce distinct fingerprints for distinct
stream aliases. Recomputed materializer identity equals its stored fingerprint.
The proposal field accepts typed frozen CT-23 intents, includes their identity,
and leaves executable authorization separate. Changed proposal meaning now
changes token identity; untyped mutable proposals refuse.

The affected six-file pytest command above reran against the final commit with
**54 passed in 1.50s**. This overlaps earlier runs. The conventional-source
conformance/terminal slice is bound to
`83970a030e8c7c6941fe6cee2de932bc9ef9765f`; source inspection confirms the
reviewed selector/fixture refusal and owned-child cleanup changes are committed.

No current source review establishes the actual installed CLI request to selected
logic, Book admission/execution, durable CT-29 close generation, CT-32 economic
collector and one-terminal ledger chain. The CLI child still lacks the complete
selected-handler transport/composition. Full packet 02 acceptance remains open.
