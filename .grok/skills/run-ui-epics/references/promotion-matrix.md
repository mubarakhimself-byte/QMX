# Quality and promotion matrix

Python gates from `poe lint` / `types` / `test` always stay in the UI
lane when Python files change, and remain available on merge. Frontend
profiles never replace them.

| Profile | When | Command source | Fail closed if |
|---|---|---|---|
| python | `.py` or undeclared files | poe | nonzero, missing uv |
| ui-format | `.svelte/.ts/.css` | prettier --check | nonzero |
| ui-lint | same | eslint + eslint-plugin-svelte | nonzero |
| ui-types | same | svelte-check | nonzero |
| ui-build | same | production build | nonzero |
| ui-unit | same | vitest | nonzero, zero required tests |
| ui-contract | story needs backend | `test:contract` | missing backend, mock-only claimed as integration |
| ui-playwright | user journeys / a11y | playwright | nonzero, skipped required |
| ui-reticle | user-facing | MCP act_and_wait/assert | missing, unknown, no |
| ui-integration-perf | story asks | `test:perf` | nonzero |
| Skylos 4.33.2 | push ui-integration / factory-candidate/** | GHA | scan crash, security/high/secrets/ai-defects |
| battery poe check | push ui-integration | existing battery.yml | unchanged Python battery |

Skylos CI comments claim extension auto-detect. `.svelte` coverage is
**not** assumed from that comment. Positive/negative fixtures live in
`tools/ui_factory/fixtures/skylos-svelte/`. Parser miss → `incomplete`,
not a pass.

Promotion: rebase onto latest `ui-integration` → re-run profiles on that
SHA → ff-only merge → wait CI on **that** SHA. Destination moving during
CI invalidates the wait; rebase again. Never auto-promote to `main`.

External vulnerability feeds (OSV in Skylos `-a`) are recorded as
non-deterministic relative to local ruff/svelte-check.
