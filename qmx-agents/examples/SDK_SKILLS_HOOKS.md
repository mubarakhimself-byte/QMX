# Bounded generic SDK skills and hooks

A separate bounded memory lane is described in [BOUNDED_DURABLE_MEMORY.md](BOUNDED_DURABLE_MEMORY.md). Skills still grant no memory or tool authority; memory stays behind the existing host binding, live validator and admission gate.

This local increment is based on native-combined candidate
`1f3b98f6b6f268e98f0f14edbb918b727069eb9c`. It implements the generic
inference skills/middleware path in real authenticated request composition.
It does not establish completion of the full agent platform. Final integration,
UI, merge, push, live inference, provider authentication, provisioning and spend
remain outside this increment.

## Ownership and contracts

| Responsibility | Released SDK | QMX host glue |
|---|---|---|
| Agent loop and middleware phases | LangChain 1.4.3 `create_agent`, `AgentMiddleware` | Existing text transport now binds SDK schemas and projects system/human/tool messages |
| Skills discovery, safe metadata parsing, progressive prompt | Deep Agents 0.7.21 `SkillsMiddleware` | Explicit local root/profile/session/workflow associations and bounded admission |
| Skill reads | `FilesystemMiddleware`, `StateBackend`, `create_file_data` | Only `read_file`; exact approved snapshot path and bounded offsets/limits |
| Replay and durable cursor | LangGraph 1.2.12 and existing journal saver | Content hashes, installed SDK versions, middleware ID/version, frozen selection in agent/workflow binding |
| Operation authority | Existing QMX grant/descriptor/dispatch seams | Skills never grant tools; every domain callback still checks current admission |
| Hook diagnostics | SDK callbacks | Scoped `agent_graph.middleware` journal events; no new CT-40/CT-41 verbs |

The new modules are `request_runtime/agent_extensions.py` and
`request_runtime/sdk_middleware.py`. Shared integration files are `tool_loop.py`,
`provider_config.py`, `domain_tools.py`, `research_workflow.py`, `process.py`,
daemon `pyproject.toml` and workspace `uv.lock`. Native adapter implementations
and native session configuration are separate. No actor ontology, Role/Quant
schema, QMF authority schema or hook registry contract is replaced.

Skill documents are declarative untrusted guidance. Hook implementations are
trusted registered Python `AgentMiddleware` objects supplied by code. Operator
JSON can select registered IDs; documents and paired clients cannot supply code,
module imports, hook scripts, tools, roots or plugins. The default registration is
`audit-v1` version `1`. Host code may supply another `MiddlewareBinding` at the
configuration-loader/composition seam after reviewing it. No dynamic import or
arbitrary script execution is added.

## Operator configuration

Keep existing provider/profile/grant configuration. Add this optional object to
`agent_sdk` in the daemon root's `operator-config.json`:

```json
"agent_extensions": {
  "roots": {"research": "approved-skills"},
  "profiles": {
    "research-reader": {
      "sources": ["research"],
      "sessions": ["psess:research"],
      "workflows": ["request", "corpus-analyst:1"],
      "middleware": ["audit-v1"]
    }
  }
}
```

Example root layout:

```text
daemon-root/approved-skills/
  evidence-review/
    SKILL.md
    references/checklist.md
```

`SKILL.md` uses the released SDK's YAML frontmatter (`name`, `description`,
optional metadata) followed by Markdown instructions. `allowed-tools` is
descriptive and confers no authority. A skill version can be documented in its
metadata; the host's authoritative content version is its SHA-256 digest. The
binding also records actual installed SDK versions and trusted middleware versions.

Roots are explicit relative directories under the operator root, never home or
ambient workspace discovery. Root aliases are stable virtual paths
`/skills/<alias>/<folder>/SKILL.md`. Sources are evaluated in configured order;
the released SDK's last duplicate skill name wins. Omitted `sessions` permits
only already admitted sessions of that behavior profile. An explicit session
list narrows it. Omitted `workflows` means `["request"]`; a specialist workflow
must use its exact versioned key (`specialist_id:version`). Unassociated profiles,
sessions and workflows receive no skill bytes or middleware. Existing direct
no-tools inference and original budgets remain intact for unselected paths.

Selected ordinary/skills-only inference graphs use the existing bounded defaults:
four graph model steps, three tool calls, 16 KiB model response/domain result and 64 KiB
combined context. SDK read output includes formatting within the bounded file
and line-range limits and is subject to the combined context cap. A selected research child uses those defaults unless trusted host code
provided explicit `LoopLimits`; explicit limits remain authoritative. Native
profiles cannot select generic extensions. Changes to files or associations
change configured provider identity and prevent old checkpoint reuse under new
configuration.

## Admission and runtime limits

At startup the host reads only immediate skill folders and one level of
`references` text files (`.md`, `.txt`, `.json`, `.yaml`, `.yml`). Script and asset
directories are not ingested or executed. Each file is at most 16 KiB UTF-8;
the library is at most 64 KiB, 64 files and 16 skills across at most four roots.
Directory enumeration also stops at its entry budget. Links/reparse points,
drive-relative paths, parent traversal and paths outside the host root refuse
configuration before any provider starts.

Raw byte caps plus YAML `safe_load` alone are insufficient: released SDK metadata
coercion can expand aliases. The host uses PyYAML 6.0.3 streaming parse events for
admission only, rejecting anchors/aliases, malformed syntax, nesting over 16 and
more than 256 events. It constructs no YAML objects and does not replace SDK
skill discovery or parsing. Unsupported tags remain non-executing under the
SDK safe loader and do not advertise valid skill metadata. SDK name validation
warnings remain warnings; this is not strict full Agent Skills conformance.

After admission, immutable host-selected text is seeded into SDK graph state.
Discovery advertises metadata first; full procedure content reaches the model
only after a bounded SDK `read_file` call. File write, edit, glob, grep, shell,
execution, subagent and automatic tool-result offload facilities are not enabled.
The host checks exact snapshot paths and rejects offsets/limits outside 0..2000,
including boolean values. Domain tools retain independent profile allowlists and
current QMX grants. Prompt instructions alone are not the enforcement mechanism.

The operator must keep the approved root and trusted code under host control.
This importer is not an OS security boundary against concurrent file replacement,
hostile trusted middleware, administrator access or malicious provider processes.
Middleware checks cannot undo an accepted read or terminate arbitrary Python
callbacks. Cancellation is cooperative, and effect receipts remain authoritative.
Model/tool budgets and tool-call identities come from independently deserialized
durable graph messages, not middleware-rewritten provider-facing messages. An
explicit retry may repeat an unknown model call at the same logical graph step;
rewriting content cannot reset the successful-step budget or receipt identity.

## Hook ordering, failures and replay

Middleware order is mandatory host guard, configured trusted middleware in listed
order, SDK filesystem, SDK skills. SDK `before_agent`/`before_model` run forward;
`after_model`/`after_agent` run in reverse; wrappers nest with the first outermost.
The mandatory host guard checks before lifecycle/model/tool entry, after model
and tool return, and before final result disclosure. Domain dispatch separately
checks grants immediately before callbacks.

`before_agent` refers to this SDK graph invocation, not persistent actor creation.
`after_agent` is an ordinary graph phase, not guaranteed `finally` cleanup.
`audit-v1` records lifecycle phases and model/tool enter/exit/error diagnostics;
the invocation boundary records `agent_attempt_error` when a graph fails.
No raw prompts, document bodies, tool arguments or provider exception text are
included in these diagnostics. Existing checkpoints necessarily contain approved
skill text and admitted observations and must retain the same host access policy.

Trusted hook exceptions propagate without implicit retry. `ProviderError` retains
its refusal code; unexpected exceptions become a failed request with the exception
type. `ProviderCancelled` records cancellation. Existing `outcome_unknown` or
`scope_interrupt` interrupts require explicit owned resume. Hook failures after a
domain read do not undo it: the observed effect receipt was already written.
SDK tool argument validation may return an error `ToolMessage`; host scope and
authority refusals propagate. This is SDK error behavior, not a second hook engine.

On restart the SDK cursor, `files` and cached `skills_metadata` replay from the
journal. No fresh discovery is forced into an existing checkpoint. Content,
source, middleware version or installed SDK version mismatch refuses resume.
Terminal request replay does no new model/tool/hook work. Interrupted graph phases
and wrappers may run again on explicit resume; hooks must be idempotent and do not
have exactly-once external side-effect semantics. Observed domain receipts suppress
repeat effects; unknown pending outcomes require reconciliation. The text codec
projects system text, human text and tool observations and preserves its strict
one-action JSON contract; arbitrary multimodal/message-history transformations
or replacement of the host transport are not established by this increment.

## Focused evidence and runbook

Run from `qmx-agents` with its locked Python 3.14 environment:

```powershell
uv sync --locked
uv run pytest packages/qma-daemon/tests/test_agent_extensions.py packages/qma-daemon/tests/test_agent_extensions_daemon.py
```

Use a fresh explicit `--basetemp` under an approved writable directory on restricted
Windows hosts. The local verification environment, commands and exact results are
in `SDK_SKILLS_HOOKS_EVIDENCE.md`. Native offline regression requires the existing
optional pinned native requirements and source paths inherited by subprocesses.
No test in this increment accesses credentials or a live provider.

| Evidence | Deterministic test |
|---|---|
| Metadata first, full body after SDK read, actual granted callback | `test_sdk_progressive_loading_then_granted_callback` |
| Operator startup, authenticated admission, durable hooks, terminal replay | `test_authenticated_startup_loads_skills_and_emits_hooks` |
| Real paired socket enters the skills graph | `test_paired_websocket_executes_progressive_skill_graph` |
| Daemon disk close/reopen with cached procedure | `test_daemon_close_reopen_resumes_checkpointed_skill_read` |
| Profile/session/workflow scope; exact workflow child | selection/narrowing tests; `test_workflow_child_loads_only_associated_skills` |
| Skill text cannot add grant, shell, write or another root | `test_loaded_untrusted_text_cannot_escalate_authority` |
| Path, UTF-8, link, raw byte and YAML expansion bounds | loader tests; reviewed alias fixture regression |
| Forward/reverse order and nested wrappers | `test_sdk_deterministic_hook_order` |
| Refusal/unexpected handler error; cancellation and post-read narrowing | hook failure/cancellation/scope tests |
| Journal reconstruction, no repeat observed operation, changed snapshot denial | replay and changed-snapshot tests |
| Trusted SDK message override reaches actual text provider | `test_trusted_sdk_model_hook_message_override_reaches_text_provider` |
| Rewriting cannot reset model/tool budgets or reuse effect identities | `test_rewriting_hook_cannot_reset_budget_or_effect_identity` |
| Unselected paths retain prior behavior and budget | empty extensions/direct inference regression tests |

Further core work remains: reviewed skill installation/update/improvement, reusable
agent authoring directories, persistent actor organization, general authored graph
workflows, recursive delegation, broader memory, RLM/large-object context, remote
long-running jobs and general mutation tools. Those are original core requirements,
not UI extras. Native Claude/Codex skill/hook capabilities belong to their selected
native backend and its settings/permissions; the generic loader does not configure
them. See `MATURE_AGENT_RUNTIME.md` and the earlier research requirements map for
the wider intent and remaining acceptance.

## Official API references

- [Selective SDK composition](https://docs.langchain.com/oss/python/langchain/deep-agent-from-scratch)
- [Custom middleware and ordering](https://docs.langchain.com/oss/python/langchain/middleware/custom)
- [Deep Agents 0.7.21 released skills source](https://github.com/langchain-ai/deepagents/blob/deepagents%3D%3D0.7.21/libs/deepagents/deepagents/middleware/skills.py)
- [Released filesystem middleware](https://github.com/langchain-ai/deepagents/blob/deepagents%3D%3D0.7.21/libs/deepagents/deepagents/middleware/filesystem.py)
- [Native Claude hooks](https://code.claude.com/docs/en/agent-sdk/hooks) and [native skills](https://code.claude.com/docs/en/agent-sdk/skills)

The workspace lock is authoritative. Deep Agents adds Anthropic/Google provider
packages as transitive dependencies, but this composition does not select or call
those providers or replace QMX's whole harness.
