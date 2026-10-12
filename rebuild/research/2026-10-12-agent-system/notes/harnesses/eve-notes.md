# Agent-as-a-folder research — Eve, origins, LLM-wiki, and harness survey
Researcher pass 2026-10-12. Every claim carries a URL. Primary sources preferred; [SECONDARY]/[UNVERIFIED] flagged.
Companion source files live beside this one under D:\QMX-research\sources\harnesses\<name>\.

Scope recap: QMX builds its agent layer on LangChain v1 + LangGraph + Deep Agents (Python) — a general copilot, a Lab copilot, a Portfolio copilot, and background workflow agents. The question behind this research: is "an agent is a directory of files" a sound convention for that harness, and what should the directory look like.

---

## A. Vercel "Eve" — what it is

Sources: https://vercel.com/eve | https://eve.dev/docs/getting-started | https://eve.dev/docs/reference/agent-files | https://github.com/vercel/eve
Secondary: https://thenewstack.io/vercel-launches-eve-an-open-source-framework-that-treats-agents-as-directories/ | https://www.devclass.com/devops/2026/06/23/vercel-debuts-eve-open-source-agent-framework-tries-to-fix-shadow-ai-with-passport/5260169

**What it is.** Eve is Vercel's open-source agent framework, pitched as "Like Next.js for web apps, but for agents" (https://vercel.com/eve). Tagline: "Markdown for instructions and skills, TypeScript for tools. Durable by default." It launched in public preview ~2026-06-17 at Vercel Ship, London [SECONDARY: thenewstack/devclass]. License **Apache-2.0**, repo **github.com/vercel/eve** (~5.5k stars at fetch). Docs at eve.dev. Default model (per README) openai/gpt-6-luna-fast via Vercel AI Gateway.

**"An agent is a directory."** The core claim, verbatim from the landing page: define instructions and skills in markdown, tools in TypeScript, then "the framework compiles the directory, wires up durable workflows, and connects channels" (https://vercel.com/eve). A minimal agent is a single `instructions.md`.

**Folder layout** (authoritative: https://eve.dev/docs/reference/agent-files). Single-agent projects root at `agent/`; an eve "workspace" puts each member at `agents/<name>/agent/`:
```
agent/
├── agent.ts            # Runtime config: model, model options, compaction, build, experimental (OPTIONAL)
├── instructions.md     # Base system prompt (also .ts or an instructions/ dir). REQUIRED on root agent.
├── instrumentation/    # Telemetry providers/destinations (root-only)
├── channels/           # HTTP + messaging entry points: Slack/Discord/Teams/web (root-only)
├── connections/        # External MCP + OpenAPI services (auth handled via Vercel Connect)
├── extensions/         # Mounted reusable capability bundles (file or dir mounts)
├── hooks/              # Lifecycle + stream-event subscribers (module-backed, recursive)
├── skills/             # On-demand markdown playbooks / capability packs
├── lib/                # Shared authored helper code (import-only; NOT copied into sandbox)
├── memory/             # memory.ts or memory/<name>.ts — cross-session memory, provider-backed slots
├── sandbox/            # sandbox.ts (backend choice); sandbox/workspace/** seeded into /workspace/
├── tools/              # Typed executable integrations (TypeScript, module-backed only)
├── schedules/          # Recurring jobs: defineSchedule modules OR markdown w/ `cron` frontmatter (root-only)
└── subagents/          # Specialist child agents (local dirs or remote; nesting allowed)
```
Evals live BESIDE `agent/`, not inside it. A "flat layout" (files directly in the app root, no `agent/` dir) is also supported.

**Names derived from paths** (https://eve.dev/docs/reference/agent-files): `tools/get_weather.ts` -> tool `get_weather`; `connections/linear.ts` -> connection `linear`; `skills/summarize.md` -> skill `summarize`; `subagents/researcher/agent.ts` -> subagent `researcher`. No registration step — the filename IS the registration.

**How each piece is defined** (landing-page code samples, https://vercel.com/eve):
- instructions.md — plain markdown ("# Identity / You are an expert weather assistant…"); a complete agent on its own.
- agent.ts — `defineAgent({ model: "spacexai/grok-4.5" })`.
- skills/*.md — markdown with YAML frontmatter `description:`; loaded only when relevant (progressive disclosure).
- tools/*.ts — `defineTool({ description, inputSchema: z.object({...}), async execute(input){...} })`.
- sandbox/sandbox.ts — `defineSandbox({ backend: vercelSandboxBackend({ runtime: "node24" }) })`.
- channels/*.ts — e.g. `slackChannel({ credentials: connectSlackCredentials("slack/my-agent") })`.
- connections/*.ts — `defineMcpClientConnection({ url, description, auth: connect("linear") })`.
- subagents/*/agent.ts — `defineAgent({ description, model: "openai/gpt-5.4" })`.
- schedules/*.md — markdown with `cron: "0 8 * * *"` frontmatter.

**Runtime that executes it.** Eve compiles the directory and runs it on Vercel AI primitives (https://vercel.com/eve):
- **Vercel Workflows** — durable execution: checkpointed steps, agents "park" between messages and resume on delivery; survive crashes/restarts (https://eve.dev/docs/concepts/execution-model-and-durability).
- **Vercel Sandbox** — isolated VMs on demand, filesystem + bash execution (https://eve.dev/docs/sandbox).
- **Vercel Drives** — persistent workspaces across sandbox runs.
- **AI Gateway** — model calls + streaming.
- **Vercel Connect** — MCP/HTTP endpoints + managed auth (connections).
- Built on the Vercel AI SDK (`ai`) + `zod`. So: NOT its own model loop reinvented — it's a filesystem compiler on top of a durable workflow engine + sandbox + AI SDK.

**Deployment.** `npx eve@latest init my-agent` scaffolds, installs, inits git, opens a terminal UI; `npm run dev` for the interactive TUI with hot reload; "Deploy your first agent in less than 60 seconds on Vercel" via https://vercel.com/new/agent. Node 24+ required.

**Tools / skills / memory / scheduling / HITL.** Tools = typed TS. Skills = on-demand markdown. Memory = provider-backed `memory/` slots across sessions. Scheduling = `schedules/` (cron). Human-in-the-loop = approval gates that pause sessions until resolved (https://eve.dev/docs/human-in-the-loop). Evals, subagents, multi-channel delivery, self-modification (the agent can edit its own instructions/tools/skills) are all first-class. License **Apache-2.0**.

Saved: eve/vercel-eve-landing.md, eve/eve-docs-agent-files.md.

---

## B. Origins of "agent as a folder" / "agent is a directory of markdown files"

Full detail: agents-md/origins.md, agent-skills/anthropic-skills.md, letta/letta-agent-file.md.

**Verdict up front:** no single person or post can be credibly credited with coining "agent as a folder" — treat any coinage claim as **[UNVERIFIED]**. The pattern is emergent, converging through 2025 and productized in 2026.

Dated primary lineage:
1. **Claude Code `.claude/` convention** (Anthropic, 2025). `CLAUDE.md` memory/rules + `.claude/agents/<name>.md` subagents + `.claude/commands/*.md` + `.claude/skills/` + `.claude/settings.json`. This is the practical ancestor and is in active use in this very QMX repo.
2. **Anthropic Agent Skills — SKILL.md** (announced ~2025-10-16; open standard at https://agentskills.io/ ~2025-12-18). A skill is a FOLDER = `SKILL.md` (frontmatter name+description) + scripts/resources, loaded by progressive disclosure. [SECONDARY on exact dates: https://wandb.ai/byyoung3/ml-news/reports/Anthropic-introduces-Agent-Skills---VmlldzoxNDc1NDg1MA]
3. **AGENTS.md** — cross-tool open convention, one markdown brief for coding agents. Site https://agents.md/ says it "emerged from collaborative efforts … including OpenAI Codex, Amp, Jules from Google, Cursor, and Factory." Governance donated to the Agentic AI Foundation (Linux Foundation) ~Dec 2025 alongside MCP. The widely repeated "released by OpenAI, Aug 2025" is **[UNVERIFIED]** against primary (noted by https://codex.danielvaughan.com/2026/04/07/agents-md-open-standard-cross-tool-portability).
4. **Letta / MemGPT `.af` agent file** (2025) — the *contrast* lineage: an agent serialized as a single portable JSON (system prompt, memory, tools+schemas, message history), not a folder of source files. https://docs.letta.com/guides/agents/agent-file

Clearest named articulations of the slogan:
- **Kieran Klaassen, "The Folder Is the Agent"**, Every / Source Code, **2026-04-13** (https://every.to/source-code/the-folder-is-the-agent). Thesis: an agent = model + context folder (CLAUDE.md/AGENTS.md + skills + docs + runbooks + `.claude/agents/`); change the folder, change the agent. He runs 44 folder-agents via a dispatch layer ("You can't vibe orchestrate"). He does NOT claim to coin it and explicitly notes people wrote markdown instructions into project dirs "before anyone called them 'skills'."
- **Vercel Eve** (2026-06) productized it as the explicit product claim "An agent is a directory."

So: Claude Code `.claude/` + Anthropic Skills + AGENTS.md (2025) are the primary roots; Klaassen (Apr 2026) names the slogan; Eve (Jun 2026) ships it as a framework thesis.

---

## C. Related "LLM wiki" ideas

Full detail: karpathy-llm-wiki/karpathy-llm-wiki.md, okf/okf.md, deepagents/deepagents-overview.md.

**Karpathy "LLM wiki"** — GitHub gist "idea file", ~**2026-04-03/04** (tweet "LLM Knowledge Bases" then a gist the next day) [gist-level quotes SECONDARY/UNVERIFIED; primary gist URL not captured]. Idea: instead of RAG re-deriving per query, the LLM incrementally builds + maintains a persistent markdown wiki (compile once, maintain continuously; no vector DB at personal scale). Three layers: (1) `raw/` immutable sources the LLM reads but never edits; (2) the LLM-written wiki (summaries, concept/entity articles, cross-refs, master index); (3) a **schema file (CLAUDE.md or AGENTS.md)** governing structure/formatting/ingestion/conflict rules. Ops: ingest, query, lint. "Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase." Sources: https://pub.towardsai.net/andrej-karpathy-killed-rag-or-did-he-the-llm-wiki-pattern-7824d876e790 , https://denser.ai/blog/llm-wiki-karpathy-knowledge-base/

**Google "OKF" = Open Knowledge Format** (CONFIRMED). Primary SPEC.md: https://raw.githubusercontent.com/GoogleCloudPlatform/knowledge-catalog/main/okf/SPEC.md ; repo https://github.com/GoogleCloudPlatform/knowledge-catalog (Apache-2.0). v0.1 ~2026-06-12; SPEC.md currently **v0.2**. Authors Sam McVeety & Amir Hormati (Google Cloud) [SECONDARY: https://www.implicator.ai/google-open-sources-a-knowledge-format-and-wires-it-into-its-catalog/]. "An open, human- and agent-friendly format for representing knowledge." A **bundle = a directory of markdown files with YAML frontmatter**; each `.md` is a *concept* whose file path is its identity; markdown links form a relationship graph. Reserved files `index.md`, `log.md`; convention dir `references/`. Frontmatter: only `type` is **required**; recommended title/description/resource/tags; plus provenance (`sources`), trust (`generated`/`verified`), lifecycle (`status`/`stale_after`), and an Attested-Computation type (`runtime` required). Consumers must not reject unknown keys / missing optionals / broken links. The spec itself is silent on Karpathy, but secondary coverage frames OKF as formalizing his LLM-wiki pattern. Google Cloud Knowledge Catalog (formerly Dataplex) ingests OKF.
> Caution: this session ALSO exposes a local `open-knowledge` MCP toolset + "OpenKnowledge" skill (ok init / ok cowork / OK Desktop). That is a *different* markdown-project product — do not conflate it with Google OKF.

**LangChain / Deep Agents equivalents** (https://docs.langchain.com/oss/python/deepagents/overview):
- **Skills** — Deep Agents load skills that follow the **Agent Skills standard (https://agentskills.io/)**: each skill is a DIRECTORY with a `SKILL.md`, progressive disclosure (frontmatter at startup, body on demand), plus scripts/templates/resources. Docs: /oss/python/deepagents/skills.
- **Memory** — uses **AGENTS.md files (https://agents.md/)** passed via the `memory` parameter; unlike skills, ALWAYS loaded; stored in a backend (StateBackend / StoreBackend / FilesystemBackend); the agent can update it.
- **Backends** — a configurable virtual filesystem over pluggable backends (in-memory state, local disk, LangGraph store, composite routing, custom) with file tools ls/read_file/write_file/edit_file/delete/glob/grep/execute and declarative read/write permission rules (first-match-wins). /oss/python/deepagents/backends
- **Subagents** — built-in `task` tool spawns ephemeral child agents (fresh context, single handoff, stateless, isolated); default `general-purpose` subagent or custom. /oss/python/deepagents/subagents
- **OpenWiki** — LangChain's direct analogue of the Karpathy LLM-wiki / OKF idea: generates a durable repo wiki that agents read from the filesystem and discover through AGENTS.md. https://docs.langchain.com/oss/openwiki/overview
- **Deep Agents Code / CLI / ACP** — a coding-agent product (https://docs.langchain.com/oss/deepagents/code/overview) and an Agent Client Protocol bridge for editors (/oss/python/deepagents/acp). NOTE: the task's hypothesized `~/.deepagents/<agent>/` CLI agent-folder path was NOT confirmed in docs this pass — **[UNVERIFIED]**; deepagents configures agents in code via `create_deep_agent(...)` plus skills/ and AGENTS.md files on the virtual filesystem, not a documented home-dir agent directory.

Key takeaway: Deep Agents already natively speaks the two folder standards (SKILL.md + AGENTS.md). An "agent as a folder" convention for QMX is therefore not a bolt-on — it maps onto primitives the harness already loads.

---

## D. Extensible plugin-based harness survey (what matters for QMX)

**Pi / pi-mono** (Mario Zechner / badlogic; MIT; https://github.com/badlogic/pi-mono). "A minimal, extensible agent harness you can make your own." Monorepo: unified LLM API + agent runtime + terminal UI lib + coding-agent CLI. Extensibility via **extensions, skills, prompt templates, themes**, bundled as shareable "Pi packages" (npm/git, `pi.extensions` manifest; `pi install npm:@scope/pkg`). An extension is a default factory fn receiving an `ExtensionAPI` to register tools/commands/keybindings/UI/history-filters and lifecycle **hooks** via `pi.on()` (agent start, session start/end, turn start/end, pre-tool `tool_call`). Deliberately ships WITHOUT subagents/plan-mode — you add them. Project config = `.pi/` + `AGENTS.md`. The cleanest existing model of a hook+package plugin surface. [SECONDARY: https://agentic-ai.readthedocs.io/en/latest/AgentHarness/pi-dev/]

**bb / get-bb** (Michael Yong + get-bb org; MIT, local-first; https://github.com/get-bb/bb , https://getbb.app). An agentic IDE that WRAPS existing coding agents (Claude Code, Codex, Cursor, Pi, OpenCode, Grok Build, Hermes Agent, any ACP agent) in a shared, thread-based workspace — a foundation for "building your own software factory." Every task = a thread with its own **git worktree** + live output. Desktop/web UI + CLI + HTTP API + Node SDK. Conceptually near QMX's epic-factory worktree-per-epic lane. [SECONDARY: https://www.scriptbyai.com/bb-ai-coding-agent-ide/]

**Prime Agent** (Prime Intellect; open-source, MIT; built ON pi; https://primeintellect.ai/blog/prime-agent , arXiv 2608.23552). Self-improving harness on a **persistent IPython kernel**. Two abstractions: (1) **RLM** — the model programs over its context and spawns recursive child agents as programmable state; (2) **Continual Harness** — CRUD-able operating state in four parts **Prompt / Sub-agents / Skills / Memory**, refined via a `/refine` command that edits them from execution history while leaving the core prompt intact. This is the strongest external match to "a Deep-Agents folder the agent maintains itself." Caveat: runs with local user perms (not sandboxed) → use disposable envs; headline 95.5% ARC-AGI-3 is authors' own claim, within run-to-run variance. [SECONDARY: https://www.opensourceforu.com/2026/08/prime-intellect-open-sources-prime-agent-self-improving-ai-coding-harness/]

**"DeepSeek Harness" / "Cordis"** — **UNVERIFIED**. No confirmed primary source found for a harness named Cordis or an official DeepSeek harness; "Cordis" otherwise = the unrelated EU research database. Need a repo/URL from the operator to verify. (cordis/cordis.md)

---

## Concluding assessment — does "agent as a folder" fit a Deep Agents harness?

**Yes, strongly — and it is close to free, because Deep Agents already loads the two folder standards natively.** `skills/*/SKILL.md` (Agent Skills standard, progressive disclosure) and `AGENTS.md` memory are first-class inputs to `create_deep_agent`; the virtual filesystem + pluggable backends mean a QMX agent folder can be the literal thing the harness reads at runtime. The convergence across Eve, Claude Code, pi, OKF, and the Karpathy wiki says the same thing from five directions: durable agent identity belongs on disk as version-controllable markdown + typed code, not as framework-specific config.

**Primitive → file mapping (Deep Agents):**
| Folder artifact | Deep Agents primitive |
| --- | --- |
| `instructions.md` / `agent.md` (system prompt) | `system_prompt=` passed to `create_deep_agent` |
| `AGENTS.md` (+ per-domain memory files) | `memory=` (always-loaded, backend-stored, agent-updatable) |
| `skills/<name>/SKILL.md` (+ scripts/refs) | Skills (Agent Skills standard; progressive disclosure) |
| `tools/*.py` | functions / LangChain tools / MCP tools passed to `tools=` |
| `connections/*` (MCP/OpenAPI) | MCP tools via `tools=` (MCP client) |
| `subagents/<name>/` (agent.md + tools/) | custom subagents via `subagents=` (the `task` tool) |
| `backend` / `permissions` config | FilesystemMiddleware backend + declarative `permissions=` rules |
| `hooks/` (lifecycle) | middleware (e.g. TodoListMiddleware) / `interrupt_on=` HITL |
| `schedules/*` (cron) | external LangGraph/host scheduler (not native to deepagents; wire via host) |
| `knowledge/` (LLM-maintained wiki) | OpenWiki / OKF-style bundle read through the virtual filesystem |

**Where the mapping is NOT 1:1 (watch-outs):** deepagents has no native `channels/` or `schedules/` or durable "park/resume" runtime the way Eve does — those come from LangGraph's runtime + the QMX host, so they stay QMX-side infra rather than folder slots. Eve's `agent.ts`/`tools/*.ts` are TypeScript; QMX is Python, so the typed layer is `*.py` with LangChain/zod-style schemas. The `~/.deepagents/<agent>/` CLI path is unconfirmed, so do not design around it.

**Draft QMX folder-convention (one directory per agent, Python/Deep-Agents flavored):**
```
agents/<copilot-name>/            # e.g. general/, lab/, portfolio/, or a workflow agent
├── agent.md                      # identity + role (-> system_prompt). Human- and agent-editable.
├── AGENTS.md                     # always-loaded memory: conventions, risk/sizing authority pointers, house rules
├── config.py                     # model tier, backend choice, permissions, interrupt_on (the "agent.ts" analogue)
├── skills/                       # on-demand SKILL.md packs (Agent Skills standard) + scripts/refs
│   └── <skill>/SKILL.md
├── tools/                        # typed Python tools (+ MCP client defs) passed to tools=
├── subagents/                    # specialist child agents, each its own mini agent.md + tools/
│   └── <name>/agent.md
├── knowledge/                    # OKF/OpenWiki-style markdown bundle (raw/ immutable + LLM-maintained wiki + index.md)
│   ├── index.md
│   ├── raw/                      # immutable sources (never edited by the agent)
│   └── <concept>.md              # YAML frontmatter: type (required) + title/description/resource/tags/status
└── evals/                        # test suites BESIDE the agent (Eve convention), not inside
```
Conventions worth borrowing wholesale: **filename = capability name, no registration** (Eve); **progressive disclosure for skills, always-load for memory** (Deep Agents/Anthropic); **`type` as the one required frontmatter key + tolerate-unknown-keys** (OKF) for the `knowledge/` bundle; **raw/ is immutable, the wiki is LLM-owned, a schema file governs it** (Karpathy); **CRUD-able Prompt/Subagents/Skills/Memory refined from run history** (Prime Agent) if QMX wants self-improving agents later. Keep durable execution, channels, and scheduling in the QMX/LangGraph host layer, not as folder slots, since deepagents does not provide them.

Net: adopt an "agent is a directory" convention for QMX's Deep Agents layer. It costs little (the harness reads SKILL.md + AGENTS.md already), makes every copilot diffable/reviewable/version-controlled on `integration`, and lines QMX up with the direction Eve, Google OKF, and LangChain OpenWiki are all moving.
