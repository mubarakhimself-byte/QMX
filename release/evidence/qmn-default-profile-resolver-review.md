# QMN default profile resolver independent review

2026-10-01. Independent GPT 6.1 Sol review. **PASS within the frozen five-file integration scope; no actionable findings.** Normal module startup consults the closed resolver by default and durably reports that the registered replay-only profile cannot provide LIVE resources. This is stand-down lifecycle evidence, not configured execution proof or acceptance of the complete candidate.

No product/test edits, commits, credentials, network/provider calls or security testing were performed. Existing process tests use their local loopback status endpoints. The working checkout reported HEAD `01fed525af621173cf58929801d9b58fc316d870` during this review; source binding is to the exact five hashes below, not a checkpoint acceptance claim. Disjoint `admission_artifacts.py` work was outside this review.

## Source binding

All five SHA-256 values matched the supplied freeze at entry and completion.

| File | SHA-256 |
| --- | --- |
| `qmn/src/qmn/host/configured_live_resources.py` | `2681a07f57f4105503ca51c2606f50f5ba7d238fc7c36413a47b5d74bbd73ccd` |
| `qmn/src/qmn/host/_supervision.py` | `ddb4e7d25c33220cfa78f25260bdef04a16c9e19ce1284693071b65b42893460` |
| `qmn/tests/test_qmn_configured_live_resources.py` | `9ed341800252ad937dfcad9910b84f584c91fe293183761d16a406bdeb549fb1` |
| `qmn/tests/test_qmn_supervisor_process.py` | `b9b4bc5e3646fb8f884d8c3d8a0366afb35e21cdb53a41df5791accc68234cf0` |
| `qmn/tests/test_qmn_configured_composition.py` | `ff44140c209b6e5647de5030b5a5b626a7bb77124b0047e77219ce09268b40e9` |

## Validation

Working directory `/workspace/QMX-release`; exact command:

```sh
uv run --no-sync pytest -q -p no:cacheprovider qmn/tests/test_qmn_configured_live_resources.py qmn/tests/test_qmn_supervisor_process.py qmn/tests/test_qmn_configured_composition.py
```

**PASS: 10 passed in 13.50s.** This runs all tests in the three held test files, rather than substituting the coordinator's earlier selected six-test result. No additional probe programs were needed.

| Contract | Result |
| --- | --- |
| Default normal entrypoint | PASS, source plus actual subprocess. `qmn.host.supervise` calls `_supervision.main()` without an injected callback. After a successful configured assessment, `main` invokes `resolve_configured_live_resources` when `hosted_resources_for` is absent. |
| Missing version-1 deployment profile | PASS, direct resolver test. A genuinely assessed v1 deployment has no host profile and returns `configured_runtime.host_profile_missing`. The new subprocess profile case uses a v2 deployment carrying the registered `.v1` application profile; its test name's `v1_profile` does not mean a v1 deployment. |
| Genuine closed-profile positive control | PASS. A separately pinned v2 descriptor resolves its registered authority, callback, source and split. The materialized source contains four recorded observations, has stream `primary`, and the registered no-intent factory can be built. |
| Profile and callback refusals | PASS. Mutating a descriptor without updating its pin fails assessment with `configured_runtime.host_profile_identity_mismatch`. A correctly repinned unsupported composition refuses selection; an unregistered callback refuses with `configured_runtime.callback_unregistered`. |
| Logic/source identity | PASS. Changed source bytes that do not reproduce the admitted CT-33 source manifest refuse with `configured_runtime.host_profile_logic_mismatch`. Static review confirms closed resolution checks profile identity, authority references, installed callback bytes, materialized REPLAY source, bot/split identity and exact no-intent source before returning the resolved profile. The default LIVE resolver calls this validation before its unsupported-resources refusal. |
| Nested configuration ownership | PASS. Resolved MIS producer parameters are immutable; attempted mutation raises `TypeError` and the catalog fingerprint remains unchanged. A declared MIS catalog is not evidence of a current MIS producer. |
| Replay profile never promoted to LIVE | PASS. Even the valid resolved offline profile returns `configured_runtime.hosted_resources_missing`, identifying its pinned profile/source and explicitly missing LIVE observations, current MIS and KSA. The resolver has no successful resource-return path or descriptor-selected import/callable path. |
| Durable normal subprocess refusal | PASS. A real `sys.executable -m qmn.host.supervise` child with the checked v2 deployment remains alive, reports health as stand-down, returns readiness HTTP 503 with the concrete replay-evidence reason, and terminates cleanly. After process exit, the parent reopens the LIVE journal through `JournalReader.read_checked`; the persisted boot-lifecycle attempt is `preflight` with exact failure ID `configured_runtime.hosted_resources_missing`. |
| Existing supervisor lifecycle controls | PASS. Missing configured directories exit actionably; invalid deployment stays unavailable; no-deployment stand-down survives two starts and produces two checked supervision events. |

Static integration review also checked the existing trusted host callback route. Injected `hosted_resources_for` still receives the checked assessment, and its typed resources pass to `invoke_configured_hosted_runtime`. That route checks successful operator activation, composition config and registry fingerprints, typed Book path, the full canonical `ResolvedNodeConfig` identity and binding record before opening its boot-attempt sink and entering sealing. The five-file change does not weaken that ordering. This preservation statement is a source read, not a new successful sealed callback/decision-loop run; the earlier separately frozen QMN configuration review owns its exact identity controls.

The process intentionally reports readiness unavailable even when a trusted root can be composed, because the normal decision loop remains unavailable. Unknown/missing mandatory resources remain explicit; the replay profile and no-intent callback do not stand in for LIVE observation, KSA, current MIS or provider producers. These tests run the editable checkout's installed module entrypoint, not a final clean release installation.

Full coupled QMA persistence, normal configured decision execution, admission artifacts, final installed release checks, provider behavior and security review remain separate pending work. Coverage floors and factory requirements are unchanged; this bounded PASS does not waive the coordinator's existing strict coverage failure.
