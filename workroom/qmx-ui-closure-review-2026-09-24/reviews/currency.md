# R8/R9 closure review — technical currency and evidence

**Verdict:** **Needs one bounded correction.** R8 is ready. R9 has reconciled bits-ui and recorded pnpm/lockfile ownership, but its Node floor is still too broad for the pinned Vite line.

## R8 — ready

The status system is now consistent enough for downstream use:

- The spine declares the whole artifact an amendment with candidate defaults that are not operator-accepted (`ARCHITECTURE-SPINE.md:14`) and defines USER, INHERITED, CANDIDATE, and OBSERVED provenance (`ARCHITECTURE-SPINE.md:25`).
- All 24 local AD headings carry one of the defined provenance tags (`ARCHITECTURE-SPINE.md:99-237`); no local AD heading remains `[ADOPTED]`.
- The decision ledger separates accepted inputs (`DECISIONS-AND-OPEN.md:12-19`) from candidate defaults (`DECISIONS-AND-OPEN.md:21-37`) and closes by restating that remaining defaults are CANDIDATE rather than user-accepted (`DECISIONS-AND-OPEN.md:76`).
- AD-4 remains tagged INHERITED, but its sitting-owned chat and producer details are explicitly attributed to candidate AD-18 and AD-24 (`ARCHITECTURE-SPINE.md:117-121`, `ARCHITECTURE-SPINE.md:201-205`, `ARCHITECTURE-SPINE.md:237-241`). This resolves the earlier provenance ambiguity without reopening the accepted product preferences.

The closure-map claim at `CLOSURE-MAP.md:23` is supported.

## R9 — needs correction

The component-major and package-manager parts are ready:

- bits-ui is consistently `2.19.3` in the seed, stack table, and component contract (`ARCHITECTURE-SPINE.md:109`, `ARCHITECTURE-SPINE.md:265`, `COMPONENT-CONTRACTS.md:20`).
- pnpm 10.x and lockfile ownership are recorded (`ARCHITECTURE-SPINE.md:274`), while the exact generated lockfile, resolved adapter/plugin versions, `svelte-check`, and production build remain honestly deferred to the isolated-scaffold gate (`ARCHITECTURE-SPINE.md:109`, `ARCHITECTURE-SPINE.md:336`, `DELIVERY-AND-QA.md:46-48`). No install or exact-lockfile evidence is claimed.

The runtime floor is not closed. The candidate says `Node.js 22 LTS` (`ARCHITECTURE-SPINE.md:109`, `ARCHITECTURE-SPINE.md:273`; also `DECISIONS-AND-OPEN.md:25`), but Vite 8.3.0 requires Node `^20.19.0 || >=22.12.0`. The compatible Svelte Vite plugin line independently requires `^20.19 || ^22.12 || >=24`. A Node 22 LTS installation below 22.12 can therefore satisfy the prose and fail the pinned build-tool engine.

**Exact correction:** replace `Node.js 22 LTS` / `Node 22` with **`Node.js >=22.12 <23`** (or an equivalently explicit supported range) in `ARCHITECTURE-SPINE.md:109`, `ARCHITECTURE-SPINE.md:273`, `DECISIONS-AND-OPEN.md:25`, `.memlog.md:34`, and the R9 row at `CLOSURE-MAP.md:24`. Keep the exact lockfile and resolved adapter/plugin pins at the already-named isolated-scaffold gate.

Primary package metadata checked 2026-09-24: [Vite 8.3.0 registry metadata](https://registry.npmjs.org/vite/8.3.0), [Svelte Vite plugin 7.3.1 registry metadata](https://registry.npmjs.org/@sveltejs/vite-plugin-svelte/7.3.1), and [bits-ui 2.19.3 registry metadata](https://registry.npmjs.org/bits-ui/2.19.3). The required engines are respectively `^20.19.0 || >=22.12.0`, `^20.19 || ^22.12 || >=24`, and `>=20`; Node `>=22.12 <23` satisfies all three.

## Bounded carry-forward checks

- Browser/Tauri fallback remains honestly target-specific and deferred: browser static hosting names `200.html`, while a later Tauri profile may use `index.html` (`ARCHITECTURE-SPINE.md:109`). Tauri remains a later candidate and is not presented as the v1 bootstrap owner (`ARCHITECTURE-SPINE.md:165-169`). This review does not require the deferred packaging tuple or deep-link proof now.
- The MCP Apps profile is explicit and policy-scoped: specification `2026-01-26`, SDK 2.0.0, host-proxied `tools/call`, and refusal of app-provided extra tools (`ARCHITECTURE-SPINE.md:129-133`). No resolved preference is reopened.
- No material post-gate drift was found. SHA-256 comparison of all 53 files in `evidence/candidate-as-reviewed/` against the current candidate produced zero differences; the input manifest identifies the reviewed spine, closure map, component contract, decision ledger, delivery document, and amendment gate at `evidence/input-manifest.json:8`, `:33`, `:43`, `:48`, `:53`, and `:198`.

## Scope limits

This is a read-only R8/R9 closure review. It does not validate implementation, execute the isolated scaffold, install dependencies, demand newer package versions, review Documentation Factory or epics, or broaden into the backend and full architecture findings.
