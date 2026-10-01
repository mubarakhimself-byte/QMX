# Independent node and gate review

2026-10-01. Reviewed node a982cf09 and root f6e2119f. No source changes, broker/provider access or trading actions.

Executed combined targeted gate/node tests: **275 passed** (includes gate tests; overlaps previous runs). Separate QA stale-assertion files: Epic08 probe_proto **11 passed**, Epic15 static **8 passed**, Epic16 static **7 passed**. GAP-0054 containment document check is included in combined passing run. Empty artifact/trace heldout now rejects with 35 errors.

## Required remaining repairs

**P1: pending-entry guard lasts only one dispatch call.** Actual `dispatch_hosted_intents(admitted, (entry,), path=same_path)` twice before any fill accepts both. `pending_in_batch` resets every call and no command reservation is inserted into ledger. Preserve pending reservation in binding/instrument state before returning accepted commands; UNKNOWN must retain reservation until reconciled, terminal rejection/cancellation clears by idempotent command identity. Test successive dispatches, uncertainty/restart and terminal resolution.

**P1: position ledger identity is not bound to admission.** Dispatch only checks `isinstance(BindingVirtualLedger)`; never compares its binding epoch against the admitted seat or frozen execution target. The shipped test path itself uses unrelated fp1 epoch while seat binding_ref is `binding-live-1`. A different empty binding ledger can mask occupied canonical binding. Root must resolve seat binding_ref to exact epoch and reject wrong/missing epoch before admission; preserve instrument and as-of frontier identity. Avoid assuming string seat ref equals epoch fp1; resolve through authoritative binding record.

**P1: native wire target remains substitutable.** Heldout same identity-bound command accepts `(ctid_trader_account_id=42,symbol_id=1)` and `(9999,8888)` using actual LiveCTraderClient.encode_command. The semantic Account/Venue/role guards and side identity fix do not bind native identifiers. Pin native account mapping from admitted session and instrument-to-native-symbol mapping from verified metadata at client boundary; encoded target must derive from immutable command plus mappings. Reject caller disagreements before submission, and validate mapping/session provenance. Do not pretend one global `_symbol_id` config safely covers multiple instruments.

**P2: invalid explicit side silently ignored.** Identity-bound buy command with explicit `trade_side=2.5` is accepted because bound branch ignores nonstring caller side. Explicit caller input must be typed/validated or refused; absent input can derive side. Opposite explicit string correctly refuses.

**P1: actual MIS/Book/KSA production adoption remains absent.** Source search finds `consume_signal_snapshot` only its definition and exports, no caller under qmn/src. No BookPathContext production constructor exists. Constant receipt hops remain metadata, not proof of BMS/SQS/KSA decisions. Reuse existing snapshot consumer for Book and KSA at common decision frontier, reject wrong expected environment/instrument/binding, record exact fingerprint and genuine admission outputs, then mint sealed command. Preserve/replay the complete recorded transcript via real decision functions rather than reconstructed SQS decision rows. Unit freshness/environment repairs do not close QM05.

## What the patch establishes

Command fingerprint includes instrument + direction for identity-bound orders, with distinct long/short fingerprints covered in passing tests. Frozen execution target account/role/Venue agreement checks happen before Command mint. Future MIS snapshot and mismatched SQS environment now refuse. Missing position-state argument no longer defaults permissively. Same-batch repeated instrument refuses. Native target, cross-call pending and composed production adoption remain unresolved above.

The new OrderParameters format-version-2 identity fields are public CT19 compatibility semantics; contract documentation/version migration must record them. Legacy unbound format1 remains accepted and must be refused on production identity-bound node money path.

## Root reconciliation review

Three QA changes retain checks while scoping ratified exceptions: protobuf within qmf-venue distribution, exact QMB host lifecycle module spawn, socket only in that exact host door. One latent accidental edit remains: Epic16 MCP import scanner references undefined `host_lifecycle` when an HTTP-module import appears. Current clean MCP source short-circuits and passes, but a forbidden import now raises NameError instead of an actionable static violation; remove that unrelated exception from MCP scanner.

GAP-0054 disclosures correctly preserve deferred hardened confinement, document cooperative limits and last-resort host recovery, and do not assert security acceptance. These are substantive disclosures, not merely literal test padding.

## Corrective slice 3f34884c and shared host retest

Node corrective target: **137 passed**, overlapping previous tests. Independent heldout same admitted seat/path repeated pre-fill dispatch now accepts first and refuses second. Actual CT-28 BookBindingRecord fingerprint replaced invented opaque-ref epoch hash; typed native map is fingerprint-bound into order identity and checked against client encode context. Opposite or nonstring explicit sides and native-ID disagreement now refuse in targeted tests. Fresh same-epoch ledger still accepts unresolved pending command at reviewed corrective commit: reservation recovery/process lifecycle remained explicitly open. The node author is extending journal recovery after this review; later mutable changes are not certified by this result.

Shared daemon process/bootstrap test files: **12 passed**. Source composition shares router/environment/task graph/job services, existing roster compiler, authoritative task journal and session service. Wire callback resolves originating session, matching principal class, selected enabled instance and published operation before existing grant dispatch; owner/environment come from OS-owned configuration rather than payload.

Actionable host adapter issue: qmb.analysis.project is accepted in `_execute_bound_product_operation`, then routed unconditionally to `BacktestingService.invoke('qmb.backtest',...)`. Exact existing projection seam is BacktestingService.place_query; catalog declares pure query-handle. Use that selected operation or refuse named unavailable, never silently run a different operation. qma.procedure.start currently compiles parent/job; this establishes graph acceptance but not actual task execution. Tests using a SimpleNamespace bound invocation bypass real CT-40 grant authority and cannot certify browser execution.

## Durable adapter and stand-down process review (6bd8fcb9, 875d77ab, d000e0bd)

Independent adapter/supervisor/lifecycle target: **19 passed**. Actual QMF JSONL append, checked projection and close/reopen under a new boot writer preserve one reservation event, including an injected fsync failure after writing its complete line. The failed append returns refusal; checked recovery sees the physically complete event at high-water one. This proves ordinary process-restart visibility; durable recovery after an fsync refusal still needs a confirmed flush before that visible prefix is treated as durable evidence for an external effect. Owner notified; a power-loss guarantee is not established by close/reopen alone.

**Heldout failing negative:** a JournalSink returning `Ok(SinkAck({}))` passes actual `BindingVirtualLedger.reserve_entry`, which sets pending occupancy. `_append_reservation_event` rejects only `detail.complete is False`; missing, None or other non-False values do not affirm a complete durable append. Require explicit boolean True for this reservation contract. Actual QMF adapter supplies True, providing the positive control.

Committed versus uncertain high-water is now distinguished in source: recovery refuses below known successfully committed sequence; failed append does not advance that sequence, allowing a complete verified empty prefix to recover a genuine no-write failure. Reservation event replay retains unknown/accepted occupancy and requires matching terminal identity to release it. Checked CT13 projection filters the binding epoch and ledger validates contiguous projected sequence; complete-prefix authority belongs to the trusted adapter, not arbitrary caller claims.

Supervisor process-start records an actual CT13 control action before `notify_ready`; journal refusal exits before READY. Status health is alive/stand-down and readiness always HTTP 503 with production adapter unavailable. Passing restart test reads two persisted process-start events after two process launches. This is truthful stand-down supervision, **not** a complete production Book/KSA/MIS node or live venue composition. A dedicated notify-socket heldout failure control remains useful to demonstrate no READY on corrupted/unwritable journal; source ordering supports that behavior.

## Reservation corrective re-review f1831e04

The earlier two bounded findings are repaired. Independent controls against actual JSONL adapter: injected ongoing fsync failure makes recovery refuse; once fsync works, recovery persists a barrier and returns complete high-water one; actual close/reopen with a new boot writer retains that reservation. Explicit missing, None, string and False `complete` ACK values all refuse reservation admission. Positive actual adapter confirms boolean True. The recovery barrier establishes a successful flush after a physically complete uncertain append before announcing complete recovery in the reviewed single-stream path.

Independent combined node/order/encoder/CT19/reservation/supervisor/lifecycle target: **153 passed** (overlaps prior targets, not additive). Separate earlier narrow target **21 passed**. No remaining blocker identified in this corrective slice. The stand-down/production-adoption limitations above remain: these results do not prove production Book/KSA/MIS/venue composition.
