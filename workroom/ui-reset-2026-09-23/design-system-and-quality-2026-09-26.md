# Design system, agent tooling and verification — 26 September 2026

Status: discussion and recommendations, not an approved architecture amendment or installed toolchain. No factory, application, CI or global skill changed.

## User direction

Explore a QMX-owned design system using shadcn-svelte as a foundation. Provide coding agents with durable instructions, component examples and working CLI/MCP tooling across long factory runs. Extend deterministic quality checks beyond Python. Later use an affordable independent audit to compare documented requirements with implemented behavior, produce reproducible issues, batch fixes and rerun verification.

## Inspected evidence

- Local integration ref: `34c148be404a375cbfd79fd4ce6997452e4f1d20`. Inspected with git show; checkout remained main. No remote fetch or live CI-status check.
- Integration `.github/workflows/skylos.yml`: pins Skylos 4.33.2, scans repository root with configured exclusions, uses `-a --no-upload --json`, retains report and runs gate; triggers include integration pushes, factory-candidate tags and PRs to main. Latest upstream features cannot be assumed present in this pin.
- Integration `.github/workflows/battery.yml`: poe check, Vulture baseline and scheduled mutation jobs. Configuration existence is not execution evidence.
- Integration `adws/adw_sssf_config/sssf.config.yaml`: quality lint/typecheck/test are currently Python-oriented; test is `uv run poe check`. UI-specific checks need explicit coverage.
- Global `C:/Users/Mubarak/.grok/skills/run-epics/SKILL.md` and merge-gate reference describe local lint/typecheck/test before merge, Skylos on GitHub after integration push. Candidate-tag workflow availability alone does not prove this orchestrator waits for candidate CI. Reconcile before the UI factory; do not interrupt current work.
- UI candidate DESIGN.md explicitly says provisional, not a brand system. DELIVERY-AND-QA.md already separates static, component, contract, browser, failure, performance and installed-product evidence; detailed tooling/provisioning remains to be made executable.

## Proposed additions to documentation scope

1. One QMX design system: semantic tokens and density; owned/adapted primitives; QMX widget, composer, navigation, graph and Library patterns; typed examples and accessible states. Original storyboard retains layout authority. Develop system and representative vertical slice together.
2. Agent implementation contract: entry index, canonical component exports, runnable catalog (Storybook candidate), allowed dependencies, component selection rules, state/interaction examples, migration rules and exact completion checks. A shared package in the repo is the initial reuse mechanism. A custom shadcn registry is optional distribution, not runtime extension authority or a mandatory new service.
3. Tool provision and preflight: pinned CLI versions/lockfiles, checked host-specific MCP configuration, Svelte official docs/tools, shadcn-svelte CLI, existing Reticle proof, exact bootstrap/check commands, resume checkpoints and evidence tied to tested commits. Verify through Grok's actual tool client; do not infer compatibility from another client's plugin support.
4. Language-aware gates: retain Python suite; add Svelte/TypeScript checks, ESLint Svelte rules, formatting, production build, Vitest component/logic tests, contract fixtures, Playwright journeys/accessibility checks and required Reticle proof. Rust compiler/Clippy/tests only when Rust ships. Broader integration and clean-install checks at promotion boundaries. Missing required tools/tests and unknown results are not passes.
5. Requirements verification: requirement/decision -> acceptance scenario -> executable check -> evidence. Include headless and remote operations, not just visible UI. Independent expected results from specifications; never learn intended behavior solely from the current app. Evidence-bearing issues with environment, commit, expected/actual, reproduction, severity and regression. Triage duplicates and unsupported findings before batch repair.

Deterministic tools can also produce false positives. Check parser/language coverage with known-good and deliberately-bad fixtures, especially `.svelte`; require narrow justified suppressions. Separate external vulnerability-feed changes from reproducible local static rules. Keep evidence for exceptions; do not let agents silently weaken gates.

## Vendor posture

Use local/open-source gates first. CodeRabbit, Greptile and Qodo market AI code review; they are not a replacement for whole-product runtime/spec conformance. TestSprite advertises runtime testing with PRD/API-document input and is a closer candidate for a bounded acceptance-audit pilot. This is a fit hypothesis, not a QMX benchmark or purchase decision. Assess confirmed unique defects, false-positive burden, reproducibility, retained/exportable evidence, environment coverage and actual spend. No subscriptions or installations authorized by this discussion.

## Sources checked

- https://www.shadcn-svelte.com/docs
- https://www.shadcn-svelte.com/docs/cli
- https://www.shadcn-svelte.com/docs/registry (custom registry marked experimental)
- https://svelte.dev/docs/cli/ai-tools
- https://svelte.dev/docs/cli/sv-check
- https://sveltejs.github.io/eslint-plugin-svelte/
- https://storybook.js.org/docs/get-started/frameworks/sveltekit
- https://vitest.dev/guide/
- https://playwright.dev/docs/test-assertions
- https://playwright.dev/docs/accessibility-testing
- https://github.com/marketplace/actions/skylos-python-sast-dead-code-detection-pr-gate (upstream now advertises multiple languages; not proof of full Svelte coverage in installed pin)
- https://www.testsprite.com/ and https://www.testsprite.com/pricing
- https://www.coderabbit.ai/ and https://www.coderabbit.ai/pricing
- https://www.greptile.com/ and https://www.greptile.com/pricing
- https://www.qodo.ai/ and https://www.qodo.ai/pricing/

The 25 September architecture recheck remains valid for its frozen inputs. These are additional delivery/design-system recommendations to reconcile into the documentation scope before UI implementation, not retroactive claims that these tools were already provisioned.
