# Native SDK documentation proposals

**DRAFT / NOT RATIFIED / NOT APPLIED TO CANONICAL DOCUMENTS.** These are concrete
reviewable revisions requested alongside the code. They do not publish through
Documentation Factory, assign a design decision ID, or silently reconcile the
canonical architecture. No applicable Documentation Factory skill/tool is exposed
in this environment; no external documentation action was taken.

## Proposed change map

| Existing surface | Proposed revision | Evidence/status |
| --- | --- | --- |
| `docs/components/qma-daemon.md`, Authority/Interfaces | Add the native harness/host ownership paragraph below; record official supervised SDK processes | Implemented in `native_sessions.py`, Codex/Claude backends and `native_composition.py`; draft authority wording |
| `docs/architecture/stack.md`, QMA dependencies | Add optional exact SDK/runtime pins below, separate from generic LangChain API inference | Optional requirements/hashed lock and offline report; shared dependency integration not performed |
| `docs/contracts/ct-45-qma-model-deployment-broker.yaml` | Distinguish inference from `agent_session`; native CLI owns subscription auth, QMX owns grants/effects | Draft schema vocabulary, not a token-broker redesign |
| `docs/contracts/ct-46-qma-execution-environment-job.yaml` | Describe bounded start/resume/events/cancel/results and unknown-outcome rules below | Implemented provider activity; not a claim of complete general JobHandle implementation |
| `qmx-agents/examples/agent-sdk.operator-config.example.json`, `SDK_REQUEST_RUNTIME.md` | Add native provider selection only after integrator wires it to host-owned runtime/bindings | Programmatic composition is runnable now; current shared parser unchanged; no fictional working JSON example |
| `qmx-agents/examples/MATURE_AGENT_RUNTIME.md` | Replace blanket future-only native rows with bounded offline evidence plus outstanding live/ordinary-worker rows | Proposed acceptance rows below; canonical matrix unchanged |
| Native runbook | Human native login, separate live approval, two retained-ID turns and one metadata receipt | Implemented dry-by-default `native_session_proof.py`; authentication/live proof unverified |

## Component wording proposal

> QMX owns job identity, live host grants, authoritative session binding and
> domain-effect receipts. An official native harness owns its inner reasoning/tool
> loop and native session context. LangGraph exposes the harness as one bounded
> `agent_session` activity rather than a `BaseChatModel` or a second tool loop.
> Subscription authentication remains with the official CLI in its dedicated
> native home. QMX does not ingest native credentials or translate subscription
> tokens into API-provider credentials. Native resume IDs are host-journal values,
> never model-supplied authority.

> The implemented supplied-text mode removes ordinary native tools and subagents,
> pins the trusted runtime configuration and admits only an explicit host metadata
> callback. This is not OS isolation. Codex uses empty native environments and
> validates effective configuration; Claude additionally requires reviewed personal
> unmanaged native policy. General filesystem/network/native worker access remains
> unsupported until its enforceable process boundary is separately implemented
> and verified. Native tool paths must not expose money storage, brokers, admin
> sockets or QMX control-plane operations. Domain operations remain host-mediated.

The prior checkpoint's blanket rejection becomes a narrower, composable supported
boundary. This changes configuration eligibility, not grant authority, security
policy or the admission of ordinary tools. Live connection status is still unknown.

## Contract vocabulary proposals

Possible CT-45 field sketch, subject to contract review:

```yaml
native_session_backend:
  execution_kind: agent_session
  inference_adapter: false
  authentication_owner: official_native_cli_in_dedicated_home
  domain_authority_owner: qmx_host
  inner_loop_and_context_owner: official_native_harness
  paid_api_fallback: prohibited
```

Possible CT-46 behavior sketch, subject to contract review:

```yaml
native_activity:
  operations: [start, resume, events, cancel, results]
  resume_identity_source: authoritative_host_journal
  current_scope_checks:
    - before_launch
    - after_preflight_and_connect_before_query
    - during_activity
    - before_host_dispatch
    - after_callback_before_disclosure
    - before_result_access
  completion: matching_native_identity_and_terminal_evidence
  cancellation_proof: explicit_interrupted_terminal
  unknown_outcome: pending_no_replay_no_fallback
  proven_pre_turn_refusal: retry_after_configuration_or_scope_correction
```

Claude exposes a native session ID and query stream, not Codex's native turn-ID
shape. The contract should not invent a Claude turn ID. An interrupt request alone
is not terminal evidence. Background tasks, peer agents and subagents are outside
this implementation. Cancellation/cleanup are cooperative bounded operations;
there is no distributed execution lease or arbitrary callback force-kill claim.

## Dependency and composition proposal

| Dependency | Exact reviewed version | Entry point |
| --- | --- | --- |
| `openai-codex` | 0.160.0 | Public `CodexClient` typed app-server lifecycle/control channel |
| `openai-codex-cli-bin` | 0.160.0 | Official bundled native runtime |
| `claude-agent-sdk` | 0.2.163 | `ClaudeSDKClient`, official SDK MCP server |
| Claude Code CLI | 2.1.286 | Existing native CLI; SDK expected CLI matches |
| `mcp` | 2.3.0 | Official MCP dependency/test client |

Installed Codex 0.159.3 was inspected for schemas/version floor, not selected as
a bridge override. Do not infer compatibility from the nominal SDK floor alone.

`compose_native_metadata_provider` accepts an existing host-owned metadata binding,
exact snapshot/locators, current runtime, approved profile tools and dedicated
native paths. It validates a read effect and caps host calls. It can be installed
programmatically in `RequestRuntime.providers`; the proof uses this actual path.
Availability reports configuration eligibility, not verified login or connection.
No allow-all mode is proposed.

The shared `_SessionScopedTools` inference wrapper is not an agent-session adapter.
Integrator-owned operator selection must resolve current per-session targets and
grants, then choose the explicit backend. Shared parser, operator JSON and daemon
routing changes were intentionally not crossed in this isolated lane.

## Acceptance-matrix row proposals

| Acceptance item | Proposed status |
| --- | --- |
| Mature native SDK session lifecycle | Implemented bounded Codex/Claude session adapters; actual released Codex transport and Claude MCP exercised offline |
| Host grants and durable domain effects | Real host metadata operation, grant expiry/revocation and observed journal receipts tested offline |
| Session resume | Journal-owned IDs and binding/reconstruction tested; proof script checks retained ID plus prior marker |
| Native subscription connection | Unverified; requires human login and separately approved live two-turn proof |
| Ordinary native tool worker | Unsupported; requires separately verified enforceable worker boundary |
| Claude managed policy | Not isolated by this implementation; conditional reviewed personal unmanaged mode only |
| API provider options | Existing generic LangChain inference path remains independent; no paid fallback from native sessions |
| Operator/daemon selection | Programmatic builder implemented; shared parser and current-binding routing remain integrator follow-up |
| Full agent organization/distributed jobs/UI | Not established by this lane |

Evidence: `test_native_sessions.py`, `test_native_codex_bridge.py`,
`native_sdk_offline_check.py`, `native-session-runtime-check.json`. Fake native
models are explicit. Runtime checks use only versions/schemas, not account reads
or model prompts. Tests of Python hook decisions do not prove native enforcement.

## Runbook proposal

Append the concrete commands in `NATIVE_AGENT_SESSIONS.md`: human native login in
a dedicated home after auth approval; reviewed Claude policy if selected; default
dry proof; separate `--allow-live` approval. Acceptance requires start, native-ID
resume, a previous marker omitted from the second prompt, and exactly one real
host operation/observed receipt. Stop on unknown outcome and do not replay or
fall back. Do not configure persistent permissions, translate tokens, provision
hosted subscription access or infer spend authorization from this draft.
