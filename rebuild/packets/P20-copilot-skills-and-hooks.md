# P20: Copilot skills and hooks (Claude with the operator, not Codex)

## Goal
The Copilot builds and maintains mini apps reliably because it has a few intentional skills and deterministic hooks.

## Who
Claude drafts the skills with the operator, after P11 and P12 exist, so the skills name real tools. Codex implements the hooks.

## Skills (Agent Skills folders under `qmx-agents/skills/`)
Each skill holds:
- when to use it
- the steps
- the checks before finishing
- one worked example
- failure modes

Keep each short.

| Skill | Purpose |
|---|---|
| `build-mini-app` | from a description to an `app.toml`, tools, optional agents/workflows/UI, and tests. Picks the risk class and kind |
| `build-workflow` | node graph JSON from intent; picks node kinds; validates |
| `debug-app` | read logs, evidence and breaker reasons; propose a fix as a new version |
| `publish-checklist` | road-to-live steps and what evidence each needs |
| `connect-broker` | add a connection or account safely (credentials via Credential Manager, demo first) |

## Hooks (Codex implements as middleware, in `qmx_agents.guards`)
| Event | Action |
|---|---|
| before `publish_app` | manifest valid, tests green, else refuse with the reason |
| after any tool | journal record (P08) |
| money-path tool in a spec | refuse (P08) |
| app breaker trips | post a "needs you" block to the Copilot session and notify the operator |
| before compaction | memory `on_pre_compress` (P07) |
| new app version built | run its tests automatically |

## Done when
Skills reviewed by the operator; hooks tested with fake agents.
