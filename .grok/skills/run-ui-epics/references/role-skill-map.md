# Role-to-skill map (UI factory)

Cadence: cheap command checks every story; deeper skills at the named
boundary. One orchestrator (`/run-ui-epics`) owns scheduling.

| Role | Skill / adapter | Path | Invoke | Prerequisites | Outputs | Cadence |
|---|---|---|---|---|---|---|
| Orchestrator | run-ui-epics | this skill | `/run-ui-epics` | ui-integration, CLI | state, merge | session |
| Builder | factory adapter over bmad-build step-03 | `.agents/skills/bmad-build` + `unattended-adapters.md` | workflow agent `build:` | story fields complete | `story N.N:` commit | each story |
| Nested loop | bmad-build-auto | `.agents/skills/bmad-build-auto` | **do not invoke** | — | competing factory | never |
| Quality runner | CLI profiles | `tools/ui_factory/quality.py` | `ui_factory_cli.py quality` | worktree, pins | evidence JSON | each story + merge |
| Runtime | verify-unattended / verify-ui-change / reticle | `~/.grok/skills/reticle`, `verify-unattended` | MCP `reticle_act_and_wait` / `reticle_assert`; CLI fallback recorded as weaker | running app from **this** worktree | verdict yes/no/unknown | user-facing stories |
| Error states | test-error-states | `~/.grok/skills/test-error-states` | when AC names empty/error/stale/reconnect/denied | leased browser for network mock | evidence | those stories |
| False greens | false-green-tests | `~/.grok/skills/false-green-tests` | when tests are green and runtime is required | Reticle session | contradiction report | those stories |
| Design tokens | design-system-compliance | `~/.grok/skills/design-system-compliance` | after visual chrome lands | live page + tokens | offTheme findings | visual stories |
| Replay | replay-user-flows | `~/.grok/skills/replay-user-flows` | after a journey is driven twice | saved flow | deterministic replay | epic boundary |
| Code review | bmad-code-review via adapter | `.agents/skills/bmad-code-review` | workflow `review` grok-4.6 | diff vs ui-integration | blocking + advisory | epic end |
| Extra lenses | bmad-review edge-case / verification-gap | `.agents/skills/bmad-review` | through adapter, not interactive | diff | findings with evidence | epic end if useful |
| Test framework | bmad-testarch-framework | `.agents/skills/bmad-testarch-framework` | **setup once** (Playwright in host) | Node 22 CI, pnpm pin | playwright config | factory setup / first host story |
| Test CI | bmad-testarch-ci | `.agents/skills/bmad-testarch-ci` | **setup once** | ui-quality.yml | GHA workflow | factory setup |
| ATDD / design | bmad-testarch-atdd, testarch-test-design | `.agents/skills/bmad-testarch-*` | when AC need Given/When/Then fixtures | story AC | test plan | epic start if AC thin |
| E2E gen | bmad-qa-generate-e2e-tests **or** testarch-automate | pick **one** | only if playwright spec missing for the journey | host app | spec files | that story |
| Test review | bmad-testarch-test-review | `.agents/skills/bmad-testarch-test-review` | after generated tests | specs | review | epic boundary |
| Trace | bmad-testarch-trace | `.agents/skills/bmad-testarch-trace` | requirement IDs → checks | AC + tests | matrix | epic boundary |
| Frontend docs | context7 MCP | session MCP | `resolve-library-id` + `query-docs` for Svelte / shadcn-svelte | MCP connected | cited docs | builder as needed |
| shadcn CLI | `pnpm dlx shadcn-svelte@1.7.0` | host package | add primitives | pinned version | component files | component stories |
| Catalog | Storybook 10.6.0 `@storybook/sveltekit` | pin in `pins.json` | later shared-library story; never `@latest` | Svelte 5 + Vite 8 peers | catalog | later epic |

`bmad-build` rendered workflow is interactive (greet, open_spec, wait).
The factory never runs that workflow as-is. See unattended-adapters.md.
