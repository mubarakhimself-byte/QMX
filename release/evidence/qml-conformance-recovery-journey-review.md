# QML conformance/recovery journey independent test review

2026-10-01. Independent GPT 6.1 Sol review. **PASS within the bounded test scope; no actionable findings.** This is meaningful public-library admission and file-backed state-continuation evidence. It does not establish persisted registry admission, a second normal QMA pack, provider behavior, or complete release acceptance.

Reviewed file: `qml/tests/test_conformance_recovery_journey.py`, SHA-256 `b11362860d1267aeb7541a47f1289bc08b914e08cde19c6b84bcacbf20bfcf92`. The hash matched at entry and completion. Checkout HEAD was `01fed525af621173cf58929801d9b58fc316d870`; that checkpoint contains held and unreviewed work and is not an acceptance claim. No product/test edits, commits, network/provider calls, credentials or security testing were performed. Only this evidence file was added.

Working directory `/workspace/QMX-release`; exact command:

```sh
uv run --no-sync pytest -q -p no:cacheprovider qml/tests/test_conformance_recovery_journey.py
```

Result: **2 passed in 0.44s**. No additional probe or quota-padding test was needed. Static reads of the library admission, Layer-2 observation/evaluation and state factory paths were used to interpret the test assertions.

| Reviewed behavior | Assessment |
| --- | --- |
| Two distinct candidates | PASS. Alpha and beta have distinct source-manifest/logic identities and candidate fingerprints, while their golden footprint slices are identical. Both pass actual `lint_declaration`, `run_layer2_suite` and `gate_registration`; their tickets assert both conformance layers passed. The tests use real public library gates with explicit local policy factories. |
| Nontrivial deterministic behavior | PASS. Fresh hosted baselines emit one entry, one close-full exit and then no intent. The tests assert the exact per-step counts and distinct alpha/beta intent traces, rather than comparing only empty outputs. |
| Snapshot reopen and continuation | PASS. Each bot is driven through the first instant, exports counter state, serializes its snapshot to a real temporary JSON file, reads/parses the file and reconstructs `BotStateSnapshot`. Public `restore_bot` imports that payload into a fresh callback. The remaining two-instant trace must equal the uninterrupted baseline suffix; a cold restart would emit entry at that point and fail the comparison. |
| Cross-Bot refusal before factory effects | PASS. Restoring alpha state under beta's distinct logic scope refuses, with `cross_bot_factory.construct_calls == 0`. The successful same-Bot restorations provide positive controls. |
| Cross-OS refusal before factory effects | PASS. Alpha state captured under injected `linux-x86_64` refuses under injected `windows-11`, again with zero construction calls. This checks the scope tuple; it is not a native Windows execution claim. |
| Differing second golden run | PASS. `AlternatingFactory` produces an emitting callback for its first construction and an empty-output callback for its second. The real suite constructs and drives both runs, and the test requires refusal plus at least two construction calls. Static inspection confirms `evaluate_layer2` rejects differing traces before its state-bound/restore checks. The callback is legitimately stateless: the library exports `{}` when no exporter is present and can restore an empty payload without an importer, so absent state methods do not manufacture the refusal. |

The source manifest is a declared/scanned local fixture and the callback is supplied by an explicit test factory. The suite does not load that source tree as a deployed Bot implementation. `gate_registration` returns a `RegistrationCandidate`; the test does not persist a registry record. Snapshot reopening crosses a JSON file boundary in the same test process; it does not exercise crash recovery, atomic storage publication, or another operating-system process. These limits are consistent with the bounded test request.

The coordinator's earlier 432-test run and strict coverage result are separate: the stated **79.778% coverage failure remains a failure**, with no floor waiver. This two-test result does not cure that result or replace the still-pending full coupled QMA persistence review, normal execution/installed release checks, provider work, or security review.
