# Combined backend capability ledger

Candidate: accepted artifact-cap base `af43324676357e5932a9c1c9b10c78465bba460f`
plus reviewed startup `c7f0ef603dc56b2b13719c5d9ecd51c240204649` and reviewed
MA01 `8465c03f0ec168e177ba57860f19c869748c0db1`. Code composition is
`7039fbde1bd749f5aaceac1c14df6afe611c22c2`; the delivery SOURCE-REF.json and
Git bundle identify the final commit including these handoff documents.
Independent review accepts the b4b0571a runtime as the MA02 base. The F1/F2 Markdown-only successor 9843b5bb is independently accepted and
incorporated here. MA02 implementation on this isolated branch awaits parent
review. This ledger records capability
status; historical acceptance records retain their original scope.

| Capability | Mounted behavior | Candidate verification |
|---|---|---|
| qmb host start/status/stop/reopen | Authenticated writer PID; five-second monotonic readiness budget; owned-child cleanup | Installed ordinary/cacheless fresh roots, already-running and bind-refusal/reopen matrix |
| artifact.stage_max_bytes | Local operator configure; default unset; greatest journal_seq restores cap; zero accepts complete empty bytes only | Installed same-host paired HTTP boundaries/restart; injected backward/equal clocks and latest-invalid startup refusals |
| list_installed_plugins | CT-40; enabled live instances only; explicit literal true | Combined source and external installed declaration matrix, before/after restart |
| facade_search | CT-40; case-insensitive literal contribution search only; explicit literal true | Real five-pack roster and exact analysis-backtest:qmb resolution |
| facade_get | CT-40; exact live ContributionHit and instance/revision; explicit literal true | Installed exact/stale/disabled/scope cases; no silent retarget |
| discovery_hit_classes | Host-owned contribution metadata only when at least one read is negotiated | Missing/empty/null/false/nonboolean/metadata/pin/partial/malformed matrix |
| invoke_contribution_pin | Support advertisement only; any supplied pin is validated at start_mission/launch_task even when advertisement is absent/false | Independent installed true/omitted/false declarations reach the same stale-pin refusal before writes; pin remains no grant |
| get_pack_ui_request | CT40 capabilities stay per socket; HTTP uses the pairing identity's last successful initialize | Independent shared-proof socket replay: prior CT40 reads survive, HTTP can refuse until the capability is renegotiated; closing a socket does not restore HTTP |
| list_mailbox / get_editor_draft_head | Existing HTTP queries; editor-head keeps explicit capability and owner gate | Installed mailbox/PackUiRequest success and missing-editor-head refusal; source positive editor tests |
| cancel_job | Existing originating-session command and durable handle fences | Existing source regression; new discovery reads create no cancellable job |
| get_instance_health | False/omitted; no scoped health owner snapshot | Typed query_unavailable; enablement is not health |
| Artifact/Knowledge discovery | Owner dependencies absent | Typed query_unavailable; staged bytes are not Library discovery |
| MA02 candidates/version CAS | CT-40 literal-true save/read/history; operator authoring only; immutable fp1/parent CAS, receipt and restart fold on existing writer | Source failures/CAS/authority checks and noneditable installed paired listener/restart; MA02-CANDIDATE-CONTRACT.md; independent review pending |
| MA03 validation / MA04 publish-update-undo / MA05 activity | Not shipped | Next pointer MA03-NEXT-TASK.md; first data-only milestone still requires MA03 then MA04 then MA05 |
| MA06 maintenance / MA07 restricted runner / MA08 mutable data / MA09 API | Not shipped | Require their packet-specific ownership and installed acceptance |
| MA10 executable deployment / MA11 remote / MA12 laptop-off / MA13 custom UI | Not shipped | No deployment, remote, always-on authority or custom renderer proof |

Each successful socket initialize replaces the pairing-wide HTTP capability map
with its complete negotiated map. Include every required HTTP gate in the
intended last initialization across tabs; partial maps do not merge. Socket
closure does not roll back that map. This is not a product-session grant.

One global Copilot identity does not collapse session authority. App-use cannot
author. Memory admission is not a checkpoint. AgentLedger evidence is not logs.
Native harness execution is not inference proxy transport. This composition
does not add any of those capabilities or renew historical proof.

Use [the discovery handoff](MA01-DISCOVERY-CONTRACT.md),
[the candidate contract](MA02-CANDIDATE-CONTRACT.md), and
[artifact setup](ARTIFACT-STAGE-SETUP.md). Exclusions remain: full repository
suites, aggregate/per-package coverage and mutation gates, inherited 17 strict
doc errors, inherited QMB format debt, historical actor deadline failures,
provider-enabled cold start, other Python overrides, connected UI, native
harness, Linux, remote, installer recertification, power-loss and whole release.
No provider/credential/UI/deployment/publication/push/protected merge occurred.
