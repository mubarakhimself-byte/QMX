# Architect frame: one-engine QMA v2 harness (2026-10-14)

## The artifact

Each runner produces one candidate design package for the QMA v2 agent harness, built on ONE engine: the Claude Agent SDK (Python). It also covers a small translator that lets GPT run through the operator's ChatGPT sign-in.

The package has four parts:
- README-style usage first, with two or three real call sites;
- a type sketch and function signatures, with `raise NotImplementedError` bodies;
- a module map;
- a rationale shaped per `~/.claude/skills/architect/references/rationale-template.md`.

## Grounding (read all of it before designing)

Root: `D:/QMX-worktrees/agent-system/tracker/qma-v2/research/one-engine/`.

- `01-requirements.md` holds the operator's rulings (latest wins), corrections, mental models and requirements.
- `02-claude-sdk-and-providers.md` is the index. `02a-claude-agent-sdk.md` is the whole SDK surface. `02b-providers-translator-policy.md` covers subscription policy, providers, mixing, the GPT translator, computer use and usage.
- `03-gaps.md` lists what the OpenAI side covered and Claude does not, plus the two-engine gray areas.
- `04-baseline.md` is the one-engine baseline: what vanilla Claude Code and the SDK give, what QMX adds, and the acceptance checks.
- `how/HOW-one-engine.md` covers today's code at origin/rebuild/base (checked out read-only at `D:/QMX-worktrees/harness-survey`), its seams and the deletion traps.
- `why/WHY-one-engine.md` gives the Preserve / Change / Avoid / Risk constraints from the old two-engine design.

The old design at `tracker/qma-v2/archive/2026-10-13-two-engine/HARNESS.md` and `archive/2026-10-13-two-engine/sketch/` was one candidate to compare against, not a base. Read nothing else under `tracker/qma-v2/archive/`, and never treat the archive as the plan.

## Hard rules (from the operator, not negotiable)

1. One engine. Claude on his ONE Claude Max plan. The unmodified Claude Code CLI owns sign-in, and QMA never reads or stores the plan token. No paid API ever, and that includes the Max plan's $100 monthly API credit (BACKLOG.md rejected-ideas table, his words at 10-12 17:11).
2. Other providers join by API compatibility, meaning a base URL plus a key: Kimi, DeepSeek, GLM, MiniMax, Meta Muse and OpenRouter. GPT joins via the translator, behind a live probe.
3. The floor is vanilla Claude Code. The agent gets the tools and behaviour Claude Code gives, and "talk to it like Claude Code" in a temporary console is his sign-off.
4. Money is read-only for agents. Enforce it in code (hooks, deny rules, process boundaries), never in prompts.
5. QMX agent settings and his personal Claude Code (`~/.claude`) stay fully separate, in both directions.
6. Platform-neutral: Windows, macOS and Linux, with an OS secret store per platform. Note that the SDK sandbox does nothing on native Windows.
7. Configurable means UI-editable. The UI itself is a later session (see `tracker/qma-v2/UI-NOTES.md`). The design only has to expose settings and an event wire the UI can use.
8. Prefer native SDK features to QMX rebuilds. Old agent code (LangChain, LangGraph, the daemon's agent runtime) is deleted after his sign-off. The deletion order must respect the import traps in HOW.
9. Measured: a busy Claude CLI process takes 170 to 610 MB, and MCP helper processes take 10 to 140 MB each. Every chat is a CLI process.
10. Out of scope: QMB, QML, Strats and the QMF refactor. The UI build comes later.

## Directions (one per runner; whole-shape alternatives, not point fixes)

- **Runner 1: thin native.** QMA is a thin launcher around `ClaudeSDKClient`. Each chat is one client with the claude_code preset, isolated config, QMX tools in-process, and the money rule enforced by native permission rules plus hooks. A provider is a profile that sets env per client. GPT is one profile pointing at a local translator. Everything else is native: sub-agents, skills, compaction, sessions, the Workflow tool. Minimise QMX code.
- **Runner 2: gateway-centred.** One local QMX gateway speaks Anthropic Messages, and every client talks to it. It routes by model name to providers and the GPT translator. That allows mixed-provider sub-agents, one place for usage and rate-limit headers, and one place for credential handling. Resolve the policy constraint explicitly: Claude-plan traffic must not have its token read or stored by QMA.
- **Runner 3: boundary-first.** Agents run behind a process or OS boundary, such as a separate OS user, a container or a worker host. That lets full Claude Code tools (Bash included) be safe even though broker credentials and money live in the OS keyring and QMX services. The agent reaches money and secrets only through a narrow QMX API. Show how this works on all three OSes, and what the operator must do once.

Each runner produces the best design for its direction. Don't hedge toward the others.
