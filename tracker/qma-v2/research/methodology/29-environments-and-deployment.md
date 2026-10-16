# 29 - Execution environments and "deployment of agents"

Date: 2026-10-16. Research only. Nothing here is decided.

How this was read. Web pages were read in the built-in browser, one tab, page by page. One fact (Hermes Cloud links) came from a Firecrawl search and was then opened in the browser. Nothing was signed in to. Local facts come from the repo and from read-only checks on the PC (`wsl -l -v`, `Get-Command docker`, CIM queries). Tags: **[retrieved]** = read in a source; **[inferred]** = my reasoning; **[local]** = checked on this PC or in this repo.

The ask (rulings 52-57, file 26 section G). Workflow runs and agent steps run inside an environment, so a mistake is not catastrophic. Agents keep their folder. Agent steps may spawn sub-agents, run RLM kernels (prime-agent) over data and tables, and make their own tools. He wants about 20 workflows or agents running at once on servers he controls, his own server first, and data synced back through the Hub. Paid providers (E2B, Modal, Railway, Amp, Daytona) are optional. He named Sandcastle and Convex and asked for one pick that fits all needs.

---

## 0. The answer in five lines

1. **Pick one sandbox contract, not one product.** The engine already has the seams: `WorkerPort` (engine AD-20) and the `ComputeProvider` protocol in `qmx_remote` (`provision / start / status / logs / stop / teardown`) **[local]**. Every environment below is an adapter behind them.
2. **His server: Docker per node attempt, with gVisor (`runsc`) for anything a model wrote.** Plain systemd services run the Hub, a node daemon and an egress/credential proxy. Tailscale joins the PC and the server. No Kubernetes.
3. **The PC: the same worker image in Docker Desktop on WSL2.** Both are already installed on this PC **[local]**. Cap local concurrency at about 3.
4. **Burst: E2B Cloud or Modal,** through the `E2BProvider` and `ModalProvider` that already exist **[local]**. Later, if his server has KVM, **E2B Embed** (self-hosted Firecracker, same SDK as E2B Cloud) is the upgrade path for microVM isolation, pause, resume and fork.
5. **Sandcastle and Convex are not the pick.** Sandcastle is a TypeScript orchestrator for coding agents on git branches; it sits on Docker, Podman or Vercel and is rough on Windows. Convex is a reactive database plus durable functions. **It is NOT an execution sandbox**; it rents E2B or Daytona for that.

---

## 1. Claude Agent SDK (the harness engine)

QMA v2 runs on the Claude Agent SDK (`HARNESS-PLAN.md` line 3) **[local]**. These facts decide how sandboxes must be shaped.

### 1.1 Sub-agents

Source: https://code.claude.com/docs/en/agent-sdk/subagents **[retrieved]**

- **Three ways to define.** Use the `agents` option on `query()` with an `AgentDefinition` (recommended for SDK apps), markdown files in `.claude/agents/`, or the built-in general-purpose agent. Claude calls them through the `Agent` tool.
- **Per sub-agent fields.** `description`, `prompt`, `tools` (allow-list), `disallowedTools` (also `mcp__server__*` patterns), `model` (`opus`, `sonnet`, `haiku`, `fable`, `inherit` or a full id), `skills`, `memory`, `mcpServers`, `maxTurns`, `effort`, `permissionMode`, `background`.
- **Context.** A non-fork sub-agent starts fresh. It gets its own prompt, the Agent tool's prompt string and the project CLAUDE.md. It does not get the parent's history. Only its final message returns to the parent.
- **Runs in the background by default.** Sub-agents can be resumed by `agentId` within the same session.
- **Limits, set through env and options:**

| Limit | Setting | Default |
| --- | --- | --- |
| Depth | `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` | 3 levels; 1 = sub-agents cannot spawn |
| Concurrency | `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` | 20 at once |
| Spend | `maxBudgetUsd` / `max_budget_usd` | none; counts sub-agent spend too |
| Turns | `maxTurns` per `AgentDefinition` | none |

- **Permission inheritance.** A sub-agent runs in the parent's mode. It can set its own `permissionMode` only when the parent is in `default`, `dontAsk` or `plan`. It runs in `bypassPermissions` only if the parent does (https://code.claude.com/docs/en/agent-sdk/permissions) **[retrieved]**.
- **Modes:** `default`, `dontAsk`, `acceptEdits`, `bypassPermissions`, `plan`, `auto` (classifier) **[retrieved]**.

**What it means for us [inferred].** A sub-agent is a process inside the same `claude` CLI tree. It shares the parent's container, filesystem and network. It is a context boundary, not a security boundary. Fan-out *across machines* is an engine job (map nodes), not a sub-agent job.

### 1.2 Sandbox options inside the SDK

- **Bash sandbox.** Claude Code's sandbox wraps shell commands only. File tools, MCP servers and hooks run outside it. It uses Seatbelt on macOS and bubblewrap plus socat on Linux and WSL2. **On native Windows, commands run unsandboxed**; the docs say to run Claude Code inside WSL2 to get the sandbox (https://code.claude.com/docs/en/sandboxing) **[retrieved]**.
- **Escape hatches to close.** By default Claude may retry a failed command with `dangerouslyDisableSandbox`. Set `allowUnsandboxedCommands: false` and `failIfUnavailable` for strict mode. Inside Docker, the Linux sandbox needs `enableWeakerNestedSandbox`, which "considerably weakens security" (same page) **[retrieved]**. So inside our container the container is the boundary, and the agent runs in `dontAsk` with allow-lists.
- **Hosting guidance.** Source: https://code.claude.com/docs/en/agent-sdk/hosting **[retrieved]**.
  - One session = one `claude` subprocess that owns a shell, a cwd and JSONL transcripts on local disk.
  - Patterns: ephemeral (container per task), long-running, hybrid (ephemeral plus a `SessionStore` that mirrors transcripts), and multi-agent container.
  - Start at **1 GiB RAM, 5 GiB disk and 1 CPU per agent**. Agents per host = (RAM − overhead) / per-session peak.
  - For a shared container, use `settingSources: []`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, a per-agent `CLAUDE_CONFIG_DIR` and a per-agent `cwd`.
  - Known limits: no top-level session timeout (use `maxTurns`), memory grows over long sessions, wide sub-agent fan-outs hit rate limits, and there is no per-sub-agent wall clock (`CLAUDE_ASYNC_AGENT_STALL_TIMEOUT_MS` is a stall watchdog only).
- **Isolation table** (https://code.claude.com/docs/en/agent-sdk/secure-deployment) **[retrieved]**:
  - sandbox-runtime: good, very low overhead.
  - Docker: depends on setup.
  - gVisor: excellent, medium to high overhead. File I/O can be "10-200× slower for heavy open/close patterns".
  - Firecracker VM: excellent. Boots in under 125 ms with under 5 MiB overhead.
  - The page gives a hardened `docker run` recipe: `--cap-drop ALL`, `no-new-privileges`, seccomp, `--read-only`, tmpfs, `--network none` plus a Unix-socket proxy, `--memory`, `--pids-limit`, and a non-root user.
  - It recommends the **proxy pattern**: credentials are injected outside the boundary, via `ANTHROPIC_BASE_URL` for model calls and a proxy or MCP tool for everything else.

### 1.3 Custom tools (how agents get and make tools)

Source: https://code.claude.com/docs/en/agent-sdk/custom-tools **[retrieved]**

- Define a tool with `@tool` (Python) or `tool()` (TS), wrap it in `create_sdk_mcp_server`, pass it in `mcpServers`, and allow `mcp__<server>__<tool>`.
- The server runs **in-process inside the SDK host app**, not in the Bash sandbox.
- `readOnlyHint: true` allows parallel calls. `isError` and `structuredContent` shape results. Tool search loads tools on demand.

**What it means [inferred].** An agent-made tool is Python code. If the SDK host runs inside the container, the tool runs inside the container too. That is the reason the whole worker, and not only the shell, goes inside the boundary.

### 1.4 Auth caveat

The SDK overview says third-party products may not offer claude.ai login or plan rate limits without approval, and should use API keys (https://code.claude.com/docs/en/agent-sdk/overview) **[retrieved]**. This is his own personal use on his own Max plan, which is how the harness plan already works. But the plan cannot feed 20 parallel agents on a server (section 9, Q1).

### 1.5 Windows

The SDK and CLI run on Windows, and the harness already runs there (`qma.serve` on the PC) **[local]**. The Bash sandbox does not run natively on Windows. WSL2 does have it **[retrieved]**.

---

## 2. Sandcastle (Matt Pocock)

Repo: https://github.com/mattpocock/sandcastle (MIT, about 8.5k stars) **[retrieved]**

- **What it is.** A TypeScript library. `sandcastle.run({ agent, sandbox, prompt })` runs a coding agent inside a sandbox on a git branch and merges the commits back.
- **Agent providers:** `claudeCode`, `codex`, `pi`, `cursor`, `opencode`, `copilot`. Auth is via `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token`, or an API key.
- **Sandbox providers:** Docker, Podman, Vercel (Firecracker microVMs) and `noSandbox`. Custom ones are built with `createBindMountSandboxProvider` or `createIsolatedSandboxProvider`.
- **Isolation model.** Two kinds:
  - *Bind-mount*: the worktree is mounted into a container and the agent writes host files directly.
  - *Isolated*: files are copied in, and commits are merged back.
  - Branch strategies are `head`, `merge-to-head` and `branch`. `createSandbox()` keeps one warm container for several runs (implement, then review). `exec()` runs a check between runs.
  - Each run has an idle timeout (600 s), a completion signal and a structured-output tag.
- **Windows support is rough.** There are 83 issues matching "windows" **[retrieved]**. Examples:
  - #924: worktree creation times out on Docker Desktop.
  - #940: noSandbox argument quoting breaks under cmd.exe.
  - #996: linked-worktree hosts fail.
  - #893: a WSL2-distro provider is only a "wayfinder".
- **A blast-radius lesson.** #1010: "Worktree sandboxes mount the host .git read-write, so hooks and config written in the container run on the host" **[retrieved]**.
- **Verdict [inferred].** Sandcastle is an orchestrator for git-centred coding agents, so it competes with our engine; it is not an environment. QMX runs are research jobs that write Library objects, not git branches. It is TS while the engine is Python. **Borrow ideas, not code:** the bind-mount vs isolated provider split, the warm sandbox reused across steps, `exec()` gates, idle timeouts, and the rule never to bind-mount a host `.git` read-write.

## 3. Convex

Sources: https://www.convex.dev/components, https://docs.convex.dev/agents, https://docs.convex.dev/self-hosting **[retrieved]**

- **What it is.** A reactive backend: database, server functions and file storage. It is open source (FSL Apache 2.0, which becomes Apache-2.0 after two years), with a Rust backend, and self-hostable.
- **Agent-related parts:**
  - The `@convex-dev/agent` component handles threads, messages, tools, RAG and usage tracking.
  - The Workflow component provides "durable" multi-step flows with retries.
  - The Workpool component provides priority queues.
- **Sandboxes.** The components directory has a "Sandbox" category whose entries wrap **E2B**, **Daytona** and "Boat" cloud VMs **[retrieved]**.
- **Plain verdict.** **Convex is NOT an execution sandbox.** Its server functions run Convex's own JS runtime, not arbitrary agent shells or Python kernels. For code execution it calls E2B or Daytona. As a database and workflow layer it would duplicate our Library Hub (content-addressed objects, refs) and the engine's ledger. **Not recommended [inferred].** The one idea worth keeping is live-updating run state to every client, and the Hub's ref-log tail already gives that.

## 4. Hermes Agent (mental models to borrow)

Sources: https://hermes-agent.nousresearch.com/docs/user-guide/configuration (Terminal Backend), https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation, https://portal.nousresearch.com/cloud **[retrieved]**. Earlier Hermes notes are in file 25.

- **The agent loop is separate from where commands run.** Hermes has seven terminal backends: `local | docker | ssh | modal | daytona | vercel_sandbox | singularity`. The loop, memory and credentials stay in the Hermes process, and only `terminal`, file and `execute_code` calls go to the backend.
  - `local`: no isolation.
  - `docker`: cap-drop, no-new-privileges and PID limits.
  - `ssh`: a network boundary, ControlMaster reuse, and env forwarded by `SendEnv` so secrets never appear in command text.
  - `modal`, `daytona`, `vercel`: full cloud isolation.
- **Persistent vs per-session container.** The default Docker setting keeps one long-lived container that is shared across sessions, `/new` and sub-agents. `container_persistent: false` gives a fresh container per session, removed when idle past `lifetime_seconds`. Further settings:
  - Resources: `container_cpu`, `container_memory`, `container_disk`.
  - Housekeeping: `docker_orphan_reaper`.
  - Sync limit: `sync_back_max_bytes` (default 2 GiB) caps the state archive a remote backend sends back.
- **Sub-agents (`delegate_task`).** A child gets a fresh conversation built only from `goal` and `context`, and only its summary returns. Defaults:
  - Batches run up to 10 children at once.
  - `max_spawn_depth: 1`, so children cannot delegate.
  - An optional `output_schema` gets one correction turn.
  - A child owns its background processes, and they are killed at teardown.
  - Children share the parent's terminal environment, so the same container.
  - `delegation.provider/model` routes children to a cheaper model.
- **Hermes Cloud.** Nous hosts an always-on Hermes instance. "Every agent gets its own hardened container", it "scales to zero when idle", and it is billed from Nous Portal credits ($20, $100 or $200 a month tiers) **[retrieved]**. Self-hosting is the same MIT code on a VPS. The docs say it "lives wherever you put it - a $5 VPS, a GPU cluster, or serverless infrastructure (Daytona, Modal)" **[retrieved via search, docs home]**.
- **What we borrow [inferred]:**
  - (a) `placement` × `isolation tier` as two separate node attributes. This is Hermes' "backend" split, and it matches engine AD-20.
  - (b) Warm-per-agent vs fresh-per-run as a per-agent setting.
  - (c) A sync-back size cap on the sidecar.
  - (d) An orphan reaper and an idle reaper.
  - (e) Sub-agents share the container, are depth 1 by default, and are capped and budgeted.
  - (f) Cloud is optional, and the same image runs anywhere.

## 5. Self-hosted options for many agents

- **Docker per run.** The existing `SSHProvider` already does this: a hardened `docker run --read-only --cap-drop=ALL --security-opt=no-new-privileges --memory --cpus --pids-limit 256 --tmpfs /tmp` per run, a workspace bind at `/work`, and `--gpus` when asked (`qmx_remote/providers.py:60-120`) **[local]**. It works on any Linux server and on Docker Desktop. It shares the host kernel.
- **gVisor (`runsc`).** It intercepts syscalls in user space. It is an add-on Docker runtime (`--runtime=runsc`) and supports GPU through `nvproxy` for most CUDA apps on selected NVIDIA drivers (https://gvisor.dev/docs/user_guide/gpu/). It also offers checkpoint/restore and rootless mode **[retrieved]**. The cost is slow file-heavy I/O (Anthropic's figure above).
- **Kata Containers.** Each container gets a lightweight VM. It needs KVM on the host and fits containerd or Kubernetes better than plain Docker **[inferred, not re-read this session]**. It is worth it only with k3s.
- **Firecracker.**
  - *Raw Firecracker*: you would build your own orchestration.
  - *firecracker-containerd*: maintained, lets containerd run containers as microVMs, and warns that "multi-tenant use cases are at the user's own risk" **[retrieved]**.
  - *Weave Ignite*: **archived Dec 2023** and points to Flintlock **[retrieved]**.
- **microsandbox** (https://github.com/superradcompany/microsandbox, Apache-2.0, libkrun). It runs local microVMs on Linux (KVM), macOS (Apple Silicon) and **Windows (WHP)**. It boots in under 100 ms, has an embeddable SDK (Python, TS, Rust, Go), runs OCI images, and keeps secrets outside the VM. But it says: "still beta software. Expect breaking changes" **[retrieved]**.
- **E2B Embed / E2B runtime** (https://github.com/e2b-dev/runtime, Apache-2.0; formerly `e2b-dev/infra`). This is the whole E2B stack on **one Linux host with KVM**, started with `docker compose up -d --wait`:
  - Firecracker per sandbox and a per-sandbox nftables egress firewall with domain allow-lists.
  - Pause, resume and fork of a live sandbox (up to 100 per request), and persistent volumes.
  - Secrets that never cross the API, and OpenTelemetry export.
  - "Same SDK, same API as E2B Cloud. Moving... is a configuration change."
  - Limits: one machine by design, plain HTTP with no TLS (so keep it behind Tailscale), and it needs Postgres, Redis and ClickHouse on the node **[retrieved]** (https://github.com/e2b-dev/runtime/tree/main/embed).
- **Daytona self-hosted.** "This repository is no longer maintained. As of June 2026, Daytona's core development has moved to a private codebase." The last public tag is v0.190.0, under **AGPL-3.0** **[retrieved]** (https://github.com/daytonaio/daytona). **Do not build on it.** The paid cloud remains.
- **Docker Sandboxes (`sbx`).** Docker's own microVM per agent, with its own Docker daemon, filesystem and network, plus a host-side proxy (https://docs.docker.com/ai/sandboxes/). Local use is free, including commercial use. It needs a Docker sign-in. It supports Claude Code with Max via OAuth, and "the session token stays on your host". It is aimed at interactive coding agents on one machine **[retrieved]**. Its Windows Home support was not checked.
- **Coolify or Dokploy.** These are self-hosted PaaS tools for long-lived apps (Dokploy: apps, databases, Compose, Traefik, multi-node via Swarm) **[retrieved]** (https://github.com/Dokploy/dokploy). They are good for deploying the *Hub and node daemon*. They do not run *per-run sandboxes*. They are optional: systemd plus Compose does the same with fewer parts **[inferred]**.
- **systemd.** This is the right base for three long-lived services on his server: `qmx-hub`, `qmx-node` (the worker gateway) and `qmx-egress` (the proxy). It gives restart-on-failure, cgroup limits and journald logs **[inferred]**.
- **k3s.** It is a single-binary Kubernetes. For one server and about 20 jobs it is **overkill**: scheduling, ingress and CRDs solve a multi-node problem he does not have. Revisit at 3 or more servers **[inferred]**.

## 6. The Windows PC (when a run must stay local)

- **Facts on this PC [local]:**
  - Windows 11 Home 26200, Intel i7-10750H (6 cores, 12 threads), 15.7 GiB RAM.
  - WSL2 is installed, with `Ubuntu-24.04` as the default distro and the `docker-desktop` distro, both version 2.
  - Docker Desktop is installed at `C:\Program Files\Docker\Docker\`.
  - The hypervisor is present.
- This makes the engine spine note "Windows 11 Home without Docker today" (AD-24 deferral) out of date.
- **Docker Desktop on Home** uses the WSL2 backend and runs Linux containers only. Windows containers need Pro or Enterprise. It is free for personal use and small businesses (fewer than 250 staff and under $10M revenue) (https://docs.docker.com/desktop/setup/install/windows-install/) **[retrieved]**.
- **Options, best first [inferred]:**
  1. **Docker Desktop (WSL2), same worker image as the server.** This is the same code path as the server, and the image is the same. Use hardened `runc` flags. gVisor inside Docker Desktop is not a supported setup, so do not plan on it.
  2. **Claude Code inside WSL2 Ubuntu with its bubblewrap sandbox.** This is lighter and needs no image. But it covers only Bash, not file tools or in-process MCP tools.
  3. **microsandbox on WHP.** It is the only local microVM option on Home, but it is beta. Re-check later.
  4. **The AD-24 scrubbed subprocess.** It stays as the fallback **for script nodes only**. Agent, RLM and agent-made-tool nodes must refuse to run when no sandbox is available.
- **Capacity.** With 16 GiB and a 1-2 GiB floor per agent, plus the UI and harness, the PC holds about 3 sandboxed agents at once. Twenty belongs on the server.

## 7. prime-agent's kernel inside an environment

From file 13 section 2 **[local]**:
- `python -m rlm.repl` is one long-lived Python namespace that speaks newline JSON: `execute`, `interrupt`, `snapshot`, `restore`.
- `rlm.spawn` and `collect` start child model calls from inside code.
- `dill` snapshots save working data.
- Its README says the worker and kernel split is "not a security sandbox".
- File 13 recommends re-implementing the small pattern in QMX.

How it fits [inferred]:
- The kernel is **a process inside the node's container**, beside the agent SDK host. Its cwd is `/work`. Data arrives as Library blobs fetched by hash into `/work/in`.
- `rlm.spawn` calls go through **our provider layer**, which points at the egress proxy. Spend, traces and budgets then land in the same ledger. The kernel never holds a raw key.
- After each cell, the snapshot goes to `/work/.ckpt/` and the sidecar ships it to the Hub as a `checkpoints` blob (LLD 8d step 4). A retry restores the snapshot in a fresh container. Cached sub-call results keep repeats from being paid twice.
- Memory: a parquet-heavy kernel needs more than the 1 GiB agent floor. Give RLM nodes their own `resources.memory_mb`, for example 4-8 GiB, and run them under `runc` rather than `runsc` if file I/O suffers. They stay network-restricted either way.

---

## 8. Recommended stack: "deployment of agents"

### 8.1 Comparison

Legend: ✔ yes · ~ partial · ✘ no. Start times are vendor claims unless marked.

| Option | Isolation strength | Start time | Self-host on his Linux server | Windows local (Home) | 20 at once | GPU | Cost | Licence | Fit with Agent SDK |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Claude Code Bash sandbox (bubblewrap / sandbox-runtime) | low-med: shell only; file tools, MCP and hooks outside | instant | ✔ | ~ only inside WSL2 | ✔ (it is just processes) | host GPU | free | Anthropic / npm pkg | native, but partial cover |
| **Docker per run, hardened runc** | medium: shared kernel | ~1 s [inferred] | ✔ (already coded) | ✔ Docker Desktop WSL2 | ✔ with RAM (20-40 GiB) | ✔ `--gpus` | free | Apache-2.0 (Engine) | ✔ SDK docs give this recipe |
| **Docker + gVisor runsc** | high: user-space kernel | ~1 s [inferred] | ✔ apt install, one daemon.json line | ✘ not supported setup | ✔ | ~ nvproxy, selected drivers | free | Apache-2.0 | ✔ named in SDK docs; slow heavy file I/O |
| Kata Containers | high: VM per container | ~1 s+ [inferred] | ~ needs KVM, best with containerd/k8s | ✘ | ✔ | ~ passthrough, complex | free | Apache-2.0 | ✔ but heavy to run |
| Firecracker raw / firecracker-containerd | very high | <125 ms boot | ~ needs KVM + own orchestration | ✘ | ✔ | ✘ | free | Apache-2.0 | ✔ via vsock proxy, much build work |
| **E2B Embed (self-host)** | very high: Firecracker + nftables | snapshot resume (fast; no figure) | ✔ if KVM; compose, single node | ✘ | ✔ on one big node | ✘ | free; you run PG + Redis + ClickHouse | Apache-2.0 | ✔ `E2BProvider` exists; same SDK as cloud |
| E2B Cloud | very high | fast | n/a | n/a (API) | ✔ | ✘ | paid per second | service | ✔ provider exists |
| Modal | high (gVisor-based [inferred]) | seconds | n/a | n/a (API) | ✔ | ✔ | paid | service | ✔ provider exists |
| microsandbox | very high: libkrun microVM | <100 ms | ✔ KVM | ✔ WHP (beta) | ✔ | ✘ [not stated] | free | Apache-2.0 | ✔ SDK in Python; beta |
| Docker Sandboxes (sbx) | very high: microVM | seconds [inferred] | ~ local tool | not checked on Home | ~ aimed at a few interactive agents | ✔ passthrough listed | local free; Docker login | proprietary CLI | ✔ Claude Code + Max OAuth |
| Daytona self-host | high | <90 ms (claim) | ✘ OSS archived June 2026 | ✘ | — | — | — | AGPL-3.0 | ✘ dead end |
| Sandcastle | = its provider (Docker/Podman/Vercel) | = provider | ✔ via Docker | ~ many open Windows bugs | ✔ (it orchestrates) | via Docker | free | MIT | ~ wraps Claude Code CLI, TS, git-centred |
| Convex | ✘ not a sandbox | — | ✔ backend only | — | — | — | free self-host | FSL-Apache 2.0 | ✘ overlaps Hub and ledger |
| Coolify / Dokploy | ✘ deploys services | — | ✔ | ✘ | ✔ services | ~ | free | Apache-2.0 (Coolify) [not re-read] | indirect: hosts Hub/node |
| k3s | = runtime used | — | ✔ | ✘ | ✔ | ✔ | free | Apache-2.0 | indirect; overkill for 1 server |
| Hermes backends (reference) | per backend | — | ✔ | ✔ local/docker | ✔ | per backend | free / Nous credits | MIT | model to copy, not a dependency |

### 8.2 The pick

**One contract: `WorkerPort` → `ComputeProvider` → sandbox image `qmx-worker`.** Every placement runs the same OCI image. The image holds `qmx_engine.nodes`, the Agent SDK with its bundled CLI, the RLM kernel, the run sidecar and Python data libraries. Only the launcher changes.

**A. Local on the PC**
- Docker Desktop on WSL2 (already installed) runs `qmx-worker` containers from the local worker with the existing hardened flags. Network goes through a local egress proxy container.
- Concurrency cap 3 (a Settings value).
- When Docker is not running, script nodes fall back to the AD-24 subprocess. Agent, RLM and tool-making nodes wait with `waiting(placement)` and an inbox line. They never run bare.

**B. His server, about 20 at once**
- Ubuntu LTS + Docker Engine + gVisor installed as runtime `runsc`. Tailscale joins the server and the PC.
- Three systemd services:
  1. `qmx-hub`: the Library Hub from library-and-data HLD/LLD. It holds objects, refs, the runs sink and replication.
  2. `qmx-node`: the remote worker of engine section 5.3. It is the same `qmx_engine.nodes` code with its own `qma.serve` and account pool. It accepts `NodeJob` bundles over GatewayPort, holds a **semaphore of 20** (a Settings value) and starts one container per node attempt.
  3. `qmx-egress`: an HTTP proxy with a domain allow-list. It injects provider keys (the `ANTHROPIC_BASE_URL` pattern and other base URLs) so keys never enter a container.
- **Isolation tier per node:**
  - `script` (trusted, from a Library version): `runc` hardened.
  - `agent`, `rlm`, `agent-tool` (model-written code): `runsc`.
  - `gpu`: `runc` with `--gpus`, or `runsc` with nvproxy once tested.
- Containers get `--network` attached only to an internal network whose sole exit is `qmx-egress` (the Docker version of the SDK docs' `--network none` plus proxy socket).
- Sizing: 20 agents × 1-2 GiB means the server needs **about 32-48 GiB RAM** and 8 or more cores for 20 truly concurrent agent nodes. Script nodes are lighter.

**C. Burst to paid later through the same port**
- The `E2BProvider` and `ModalProvider` already exist in `qmx_remote` **[local]**. They boot the same `qmx-worker` image (an E2B template or a Modal image), run the same sidecar and write to the same Hub with a run token.
- GPU jobs go to Modal, or to his server if it has a GPU.
- **Upgrade path, not day one:** if his server has KVM and he wants microVM isolation, pause, resume or fork, install **E2B Embed** on it. The existing `E2BProvider` points at it with a domain setting. The worker code does not change. This is the closest thing to "one product that fits all", and it should be measured first (Q3).

Why not E2B Embed on day one [inferred]:
- It needs KVM, which is not yet confirmed on his server.
- It brings Postgres, Redis and ClickHouse along.
- It is one node by design.
- It cannot do GPU.
- Plain Docker plus gVisor is already 80% coded in `SSHProvider`, and it runs identically on the PC.

### 8.3 How sub-agents, RLM kernels and agent-made tools run inside it

- **Agent folder.** The agent's folder (prompt, skills, tools, memory) is a Library object. The node fetches it by hash into `/work/agent`, writable inside the container only. The canonical folder in the Library never changes during a run. Changes such as new tools, edited memory or a new skill return as new objects on `refs/runs/<id>`, and the Library versions them (ruling 57: no human gate).
- **Sub-agents.** They are Agent SDK sub-agents inside the same container:
  - `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`.
  - `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` = 3-5 per agent node, so 20 nodes cannot grow into 400 processes.
  - `maxBudgetUsd` comes from the node's remaining budget.
  - `maxTurns` is set on every `AgentDefinition`.
  - A per-sub-agent `model` sends cheap work to cheap models through the proxy.
  - Fan-out wider than that becomes an engine map node, which gets more containers and spreads across the semaphore.
- **RLM kernels.** These run as described in section 7: a kernel process in the same container, sub-calls through the provider layer, snapshots shipped as checkpoint blobs.
- **Agent-made tools:**
  - The agent writes `tools/<name>.py` with a declared schema.
  - The node loads it in the next turn as an in-process SDK MCP server (`create_sdk_mcp_server`), inside the container.
  - It gets tool-tier isolation (`runsc`) and the money deny-list. It has no order verb: `propose_order` exists only on the PC harness (HLD) **[local]**.
  - The tool is saved to the Library as an `agent-tool` object marked `unreviewed`. Other agents may load it only into sandboxed nodes.

### 8.4 How it plugs into WorkerPort and the Library Hub

- **Engine → `WorkerPort.run(NodeJob)`.** `placement` picks the local worker, `qmx-node@server` or `e2b`/`modal`, using the preflight states `available|configured|authorized|reachable|healthy` (AD-20). The new `isolation` attribute picks `runc` or `runsc`. Both are visible in the UI as plain words.
- **Bundle out.** Engine section 5.3 sends the `NodeJob` minus local paths, inputs by artifact hash and credential *scope refs*. The `qmx-node` resolves refs from its own keyring into `qmx-egress`, not into the container.
- **In the container.** The `qmx-run-sidecar` (LLD 8d):
  - checks the Hub;
  - writes a heartbeat every 10 s;
  - streams logs and traces to `runs/<id>/`;
  - `put`s artifacts by hash;
  - advances `refs/runs/<id>` only (run token `write_prefix`);
  - mirrors Agent SDK transcripts through a **`SessionStore` adapter that writes to the Hub**, so a hybrid session resumes on any node;
  - on exit, scrubs env and runs provider teardown.
- **Results back.** `NodeResult` plus events reach the engine ledger through GatewayPort. The engine, not the worker, appends them (AD-20).
- **Hub down.** The sidecar buffers and writes to the bucket layout (LLD FM-3). The PC pulls later.

### 8.5 Failure and blast-radius limits

| Risk | Limit |
| --- | --- |
| Model runs `rm -rf` or a fork bomb | read-only root, tmpfs, `/work` only, `--pids-limit 256`, `--memory`, `--cpus`, non-root user, cap-drop ALL; `runsc` for model-written code |
| Container escape | gVisor for agent tiers; no Docker socket, `~/.ssh`, `.git` or host home ever mounted (Sandcastle #1010 lesson) |
| Data exfiltration or key theft | no keys in containers; egress only via the `qmx-egress` allow-list; per-node domain list |
| Runaway spend | `maxBudgetUsd`, `maxTurns`, sub-agent caps, engine budgets checked before each retry (file 13); proxy-side per-run token cap |
| A stuck agent | sidecar heartbeat 10 s, engine watchdog, Sandcastle-style idle timeout (600 s), `CLAUDE_ASYNC_AGENT_STALL_TIMEOUT_MS`, hard run timeout |
| Garbage written to the Library | writes land only on `refs/runs/<id>`; other refs are untouched; versions are reversible (ruling 57 accepts garbage) |
| Disk fill | per-run workspace quota, sync-back cap (Hermes' 2 GiB idea), orphan and idle reapers |
| Money | no order verb anywhere off the PC harness; **the agent server must not be the trading node** and holds no broker credentials (those stay in Windows Credential Manager under `qmx/*`) |
| One bad node | the semaphore isolates it; its failure parks only its own run (engine ladder: retry, repair, escalate) |
| Server down | placement is `unreachable`; nodes `waiting(placement)`; the inbox after `alert_after`; burst providers can be chosen per node |

---

## 9. Open questions, each with a recommendation

1. **Which models feed 20 server agents?** One Max 5x plan cannot. AD-20 says plan tokens never travel, and the SDK docs steer products to API keys. *Recommend:* the server's `qma.serve` uses key providers by base URL (Kimi, GLM, OpenRouter: the `key_scope [qmx/kimi]` already in the HLD) through `qmx-egress`. Claude Max stays on the PC for interactive work. Cheap models are fine for tests (ruling 51).
2. **What are his server's specs?** RAM, cores, GPU, and whether KVM is available (bare metal, or a VPS with nested virtualisation). *Recommend:* run a one-line check (`nproc; free -g; ls /dev/kvm; nvidia-smi`) before any build packet. Under 32 GiB, cap the semaphore at 10.
3. **gVisor or E2B Embed on the server?** *Recommend:* start with Docker + `runsc`, since most of it is already coded. Add E2B Embed only if `/dev/kvm` exists and a measured need appears (pause/resume/fork of long agent sessions, or an RLM data workload that runs badly under gVisor).
4. **Warm or fresh container per agent?** *Recommend:* fresh per node attempt by default, matching the memo and retry rules (AD-7). Allow a per-agent `warm: true` (Hermes' `container_persistent`, Sandcastle's `createSandbox`) for chat-like agents. The session state goes through the Hub `SessionStore`, so warm is an optimisation and not a source of truth.
5. **Where does the agent loop run: inside or outside the box?** Hermes keeps the loop outside, and the SDK docs put it inside. *Recommend:* inside, because in-process SDK tools and agent-made tools then sit inside the boundary. Keys stay outside through the proxy, which keeps Hermes' main benefit.
6. **Do agent-made tools need review before other agents use them?** Ruling 57 says nothing waits for him. *Recommend:* no human gate. Mark them `unreviewed` and load them only into sandboxed tiers. A grader node can promote them later.
7. **Should Convex or Sandcastle stay on the list?** *Recommend:* no, for the reasons in sections 2 and 3. Keep Sandcastle's patterns in the engine's design notes.
8. **Should Coolify or Dokploy run the server?** *Recommend:* not needed. Three systemd units plus Docker are simpler. If he wants a web panel for the server, Dokploy is fine for the Hub, egress and node services only.
9. **What runs locally when Docker Desktop is off?** *Recommend:* script nodes run in the AD-24 subprocess. Model-written-code nodes wait for placement and never run bare. The UI shows "Docker is off" as a fix-it line.
10. **GPU?** *Recommend:* a GPU node runs on his server with `--gpus` under `runc` if it has a card, else on Modal. Do not plan GPU on E2B or Firecracker.
11. **Should engine AD-24 be revisited?** Its "no Docker on Windows 11 Home" premise is false on this PC. *Recommend:* note it in the engine's OPEN-DECISIONS and let the sandbox slot into AD-24's envelope as that ADR already allows.

---

## 10. Sources

- Claude Agent SDK subagents: https://code.claude.com/docs/en/agent-sdk/subagents
- Hosting: https://code.claude.com/docs/en/agent-sdk/hosting
- Secure deployment: https://code.claude.com/docs/en/agent-sdk/secure-deployment
- Bash sandbox: https://code.claude.com/docs/en/sandboxing
- Custom tools: https://code.claude.com/docs/en/agent-sdk/custom-tools
- Permissions: https://code.claude.com/docs/en/agent-sdk/permissions
- SDK overview (auth note): https://code.claude.com/docs/en/agent-sdk/overview
- Sandcastle: https://github.com/mattpocock/sandcastle and its Windows issues at https://github.com/mattpocock/sandcastle/issues?q=windows
- Convex: https://www.convex.dev/components, https://docs.convex.dev/agents/overview, https://docs.convex.dev/self-hosting
- Hermes: https://hermes-agent.nousresearch.com/docs/user-guide/configuration, https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation, https://portal.nousresearch.com/cloud
- E2B runtime and Embed: https://github.com/e2b-dev/runtime, https://github.com/e2b-dev/runtime/tree/main/embed
- Daytona (archived): https://github.com/daytonaio/daytona
- microsandbox: https://github.com/superradcompany/microsandbox
- firecracker-containerd: https://github.com/firecracker-microvm/firecracker-containerd
- Ignite (archived): https://github.com/weaveworks/ignite
- gVisor GPU: https://gvisor.dev/docs/user_guide/gpu/
- Docker Desktop on Windows: https://docs.docker.com/desktop/setup/install/windows-install/
- Docker Sandboxes: https://docs.docker.com/ai/sandboxes/, https://docs.docker.com/ai/sandboxes/architecture/, https://docs.docker.com/ai/sandboxes/get-started/
- Dokploy: https://github.com/Dokploy/dokploy
- Repo: `qmx-agents/packages/qmx-remote/src/qmx_remote/providers.py`, `tracker/qma-v2/architecture/workflow-engine/SOLUTION-DESIGN.md` section 5, `ARCHITECTURE-SPINE.md` AD-20 and AD-24, `architecture/library-and-data/HLD.md`, `LLD.md` section 8d, `research/methodology/13-failure-and-rlm.md` section 2, `25-hermes-n8n-loadbalancer.md`.
