# UI and deploy grounding for the factory (13 November 2026)

Read-only grounding for the factory design. Nothing was built or changed. Every fact names its file and line. Branch facts were read with `git show` / `git grep` on `origin/*` after a fetch on 13 Nov. `origin` is now `mubarakhimself-byte/QMX`.

Short names:
- **SRV** = `qmx-agents/packages/qmx-control/src/qmx_control/server.py` on `origin/engine/base` (`3ae41ffcb`, 8 Nov; it has not moved since).
- **CS** = `qmx-agents/packages/qmx-control/src/qmx_control/service.py`, same tip.
- **HOST** = `qmx-agents/packages/qmx-host/src/qmx_host/`, same tip.
- **KIT** = `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-redesign/.scratch/ui-design-kit/kit/`.
- **WP** = `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-review-repair/apps/qmx-ui/plan-2026-11/`.
- **MEM** = `C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Desktop-QMX/memory/`.

## 0. What he asked

`HIS-WORDS-2026-11-13.md:49-51` (18:49 UTC):
- The UI is "going to require a lot of APIs". Every phase should "justify what connects to the UI and how", so that "by the time an agent starts wiring the UI, it's not confused and it's simpler". The UI agent "just starting to wire things, it may mess up."
- "BMAD CIS may help there."
- "Then staging and deployment." He calls the whole thing "kind of like a software factory".

`RESUME-2026-11-13.md:9-10` records both as factory requirements.

---

## 1. The UI today

| Fact | Evidence |
|---|---|
| The real UI is `apps/qmx-desk` on branch `ui-redesign`: SvelteKit 2, Svelte 5, Tailwind 4, shadcn-svelte, static build. | KIT `RESUME.md:12`; `apps/qmx-desk/package.json:26`; `svelte.config.js:1,7` (`adapter-static`, `fallback: "200.html"`) |
| He expects this code to become the shipped desktop UI, "with only the backend wiring left". | KIT `RESUME.md:32` |
| **`apps/qmx-desk` is untracked.** It is not on `origin/ui-redesign` (0 files under `apps/qmx-desk` at `c4c1cd017`, 10 Nov). It exists only in one worktree on this laptop. The kit's `RESUME.md`, `DESIGN-LOG.md`, `BACKEND-ASKS.md` and others are untracked too. | `git ls-tree -r origin/ui-redesign apps/qmx-desk` = 0; `git status` in the worktree: `?? apps/qmx-desk/`, `?? .scratch/ui-design-kit/kit/RESUME.md` |
| `qmx-desk` makes **no backend call at all.** No `fetch`, `EventSource`, `WebSocket` or `/api/` in `src/`. Everything is demo data. | `grep -rnE "fetch\(|EventSource|WebSocket|/api/" apps/qmx-desk/src` matches only a comment in `src/lib/dev/space-check.js:3` |
| Its dev server runs on port **5174**. The host's default allowed UI origin is **5173**, and CORS allows exactly one origin. Wiring `qmx-desk` today needs `--ui-origin http://127.0.0.1:5174` on the host. | `apps/qmx-desk/package.json:10`; HOST `__main__.py:105`; SRV:491 |
| The October UI (`ui-review/repair`, `apps/qmx-ui`) is a behaviour reference only; it is "a design, not code". Its only fetches are demo files. Its `BACKEND-REQUIREMENTS.md` describes the retired CT-40 WebSocket door. | MEM `ui-is-design-not-code.md:11-20`; `apps/qmx-ui/src/routes/library/+page.svelte:221`; `apps/qmx-ui/BACKEND-REQUIREMENTS.md:1-30` |
| `apps/qmx-ui` on `engine/base` is a stale 1 Oct stub (Svelte client of the old qma-wire). Its `scripts/contract-check.mjs` only prints that no live server exists. | WP `grounding/01-backend-wiring-map.md` §4; `git show origin/engine/base:apps/qmx-ui/scripts/contract-check.mjs` |
| The UI redesign's open state: round 5 (space and sizing) waits for his verdict; Sessions, mini apps, Home, Workflows, Lab and Units follow. | KIT `RESUME.md:43,51-59` |
| He dropped Reticle from the new UI. | KIT `RESUME.md:35` |
| UI notes from other sessions (one-click deploy and server sign-in, first start in the UI) are held until he says send. | MEM `ui-notes-held-for-ui-session.md:11-18` |

## 2. How the UI meets the backend today

**There is one door, and no screen is wired to it.**

| Fact | Evidence |
|---|---|
| One process, one port: `python -m qmx_host serve --home <folder> --port 8766 --ui-origin <origin>`. Chats, workflows, Library, apps, data, backups and the connect dialog share it. | HOST `__main__.py:99,105`; WP `grounding/01` §1 row 1 |
| Transport: REST (JSON) plus SSE. No WebSocket. `/mcp` exists for agents only. | SRV:454-469 (`/api/events/{topic}`), SRV:487 (`/mcp`); WP `grounding/01` §1 |
| Auth: one bearer on every route, `/api/health` included. The token sits in the Windows keyring as `qmx/control-token`; the host never serves it. A desktop shell must read it and hand it to the page. | SRV:336-361 (`BearerGate`), SRV:471; WP `grounding/06` §1.4 row 6 |
| Browser `EventSource` cannot send the header, so streams must use `fetch()`. | WP `grounding/01` §1 "SSE auth caveat" |
| CORS: one origin, methods GET, POST, PUT only. `DELETE /api/library/upload/{id}` exists but is blocked cross-origin. | SRV:488-503 |
| Three error shapes: `{"error":{code,message}}` (control rows), `{"detail": ...}` (card, backups, keys, connect), `{ok:false,code,message,next_step}` (promote). | WP `grounding/01` §1 "Error shapes" |
| **OpenAPI exists only at run time.** FastAPI's default `/openapi.json` is served behind the bearer ("Protect mounted MCP, OpenAPI and REST"). Each control row gets `operation_id=row.name`. **No schema file is committed or generated anywhere**, and no test or CI step snapshots it. | SRV:336-337, SRV:416, SRV:445-452; `git grep -i openapi origin/engine/base -- '*.py' '*.yml' '*.ts' '*.mjs'` finds only Spotware's protobuf package |
| Where routes come from: 65 `rest=(...)` rows on `ControlService` turned into routes by `rest_routes` (`catalog.py:1023`), plus FastAPI routers in 17 files (89 route registrations). Catalog rows without `rest=` (broker, backtest, unit, blocks, node, readings, journal, lab and more) are model tools only, unreachable by the UI. | `git grep -c "rest=(" CS` = 65; SRV:445-452; WP `grounding/01` lines 8-13 |
| A generic app door: `POST /api/apps/{app_id}/tools/{tool}`. The trading node's 19 operations and the MIS's 4 go through it. No push stream. All first-party apps are `kind = "headless"` (no `ui` folder). | CS:2042; `qmx-agents/apps/trading-node/app.toml:5,28-46` |
| **No typed client exists.** The wiring plan proposes one module per backend area plus one event hub; none is written. | WP `WIRING-PLAN.md:31-37` |

**Screen-to-endpoint maps that exist** (none is on `engine/base` or `main`, none is checked by anything):

| Doc | Where | State |
|---|---|---|
| `grounding/01-backend-wiring-map.md`: per screen, each need, route, payload, and Exists / Partial / Missing, with gaps ranked | WP (uncommitted on `ui-review/repair`); copy in KIT `refs/grounding/01` (untracked) | Current at `3ae41ffc`, which is still the `engine/base` tip |
| `grounding/06-install-and-shell.md`: install, first start, handover, shell, gaps G1-G14 | same | same |
| `WIRING-PLAN.md`: shell, client layer, wire order, 10 ranked backend asks, 9 decisions for him | WP:1-95 | Proposal, not ratified |
| `BACKEND-ASKS.md`: 15 needs raised by the redesign (layouts, "new since" marks, inbox push, pods for screens, day one facts) | KIT `BACKEND-ASKS.md:5-21` | Untracked, a running list |
| `UI-HANDOFF.md`: a 419-line running list, sections 0-26, last brought current 28 Oct | `tracker/qma-v2/UI-HANDOFF.md` on `origin/plan/agent-system`, `plan/unit-system`, `plan/risk-core` only | Partly stale; §26 checked against `3ae41ffc` in `grounding/01` §3 |
| `release-inventory/JOURNEYS.md`: J1-J25, K-01..K-34 and every plan's "You see" lines, checked against code | `tracker/release-inventory/JOURNEYS.md:24-254` (staged on `main`'s checkout) | "No screen is wired" (`:7`) |

**The biggest blockers to wiring** (from `grounding/01` §3 and `grounding/06` §3): no shell to hand over the bearer; most state has no push (`jobs` topic never written, `runs` refreshed only on `GET /api/aggregates`, no inbox topic); the Lab class is built but never mounted; broker reads and many domain reads are model-only; first-party apps have no screens; the host serves no static files.

**The risk build adds nothing to the door.** None of `origin/build/rc-01..35` (195 commits on rc-35, 30.9k lines added) adds a `rest=` row, a route or a new app operation. `rc-35` changes `app.toml` versions only. So `BACKEND-ASKS.md` #12 ("pods for screens") is not served by the work in flight. Checked with `git diff origin/engine/base...origin/build/rc-NN | grep -E '^\+.*(rest=\(|add_api_route|@router\.|/api/)'` for every NN: no match.

## 3. What "staging" and "deployment" mean for QMX now

### 3.1 Branches

| Source | Says |
|---|---|
| MEM `branching-model-main-staging-integration.md:11-14` (12 Oct) | integration, then staging, then main |
| His words 12 Nov 11:08, quoted in `GAP-AUDIT-2026-11-13.md:54` and `tracker/ci/CI-INTENT-CHECK-2026-11-13.md:12` | "integration is now engine ... Let's not use staging." "The release can be a tagged version." "Main is literally the branch I wanted to keep clean with no code." "Windows and Linux, I think, first." |
| `SHIPPING-METHOD.md:13,27` | Checkpoint reviews merge into `engine/base`; line 13 still says "Nothing reaches `integration` or `main` without his click" (GAP-AUDIT 2.2 flags the contradiction) |

So today: **`engine/base` is integration, there is no staging branch, a release is a `v*` tag.** The memory file was never reconciled.

### 3.2 "Deploy" means four different things in the code

| Meaning | What exists | Reachable from a screen? |
|---|---|---|
| **A. Promote a unit** toward paper or live | `POST /api/units/promote`, operator only; "the same click deploys it" (HOST `promote.py:1,61,719`) | Yes, route exists; no screen wired |
| **B. Put a trading node on a server** | The connect dialog's `trading-node-server` kind (HOST `connect_node.py:802`; module doc `:1-27`): firewall, Tailscale, `qmx-recover`, host, chrony, OpenObserve, then node steps over SSH. Started by `POST /api/connect/jobs`. The server bootstrap script is `qmx-agents/packages/qmx-control/src/qmx_control/node-bootstrap.sh` | Yes, job routes exist (HOST `connect.py:304-331`); no screen wired. His note "one-click deploy and server sign-in" is the UI for this (MEM `ui-notes-held-for-ui-session.md:13`) |
| **C. Switch or roll back node code** on a VPS (`/opt/qmx/trees/<commit>`, `current` symlink, deployment records) | `qmn/deploy/switch.py:1-12` and `just node-switch` / `node-rollback` (`qmn/deploy/justfile-recipes/node.just:20-23`). `--apply` without `--fixture-root` is refused (`switch.py:682-689`): **it has only ever applied to a scratch fixture** | No; DevOps CLI only |
| **D. Install QMX on his PC** | No installer, no desktop shell, no updater, no auto-start; the host serves no UI. `tools/build_release.py` + `release/install.py` + `release/launcher.py` exist but target the October daemon and would fail on the current host. The only proven path is a source checkout plus `uv` plus a terminal wizard | No (WP `grounding/06` §1.1-1.3, gaps G1-G14) |

Installer lessons from his first real start (MEM `installer-lessons-first-start-2026-11-09.md:13-18`): show cTrader's own account number and let him pick; ask when there are several demo accounts; mask secrets with asterisks; start the host by itself; "QMX folder" means the data folder.

### 3.3 Rulings that frame deploy

- **PC is home.** Everything lives on the PC first; servers stand in or add capacity, never hold the main copy. The trading node is the one natural server home. Every server needs a manual recovery script. (MEM `pc-home-servers-substitute.md:11-15`)
- **Hosting waits.** "Leave hosting out entirely ... just the developing stage." No pay-per-use compute. (MEM `no-paid-tooling-browser-research.md:12-14`)
- **Paper = a demo account** (MEM index, `qmx-risk-definitions-2026-11-12`).
- **Release order he set on 9 Nov:** UI, inventory, QA click-through, installation lens, merge, then live paper on his server (CFDs). After it: a week of watching, a "web version first" later. (MEM `release-roadmap-2026-11-09.md:13-26`)
- **Ruling tension, unresolved:** rulings 32 and 40 and AD-48 say desktop only, "never as a web site"; the roadmap says "a web version first" after release. (WP `grounding/06` gap G14)

### 3.4 What CI does at release level

`qmx-ci.yml` exists only on `origin/ci/github` (`9eb140303`, PR #1 into `engine/base`, open). `engine/base` still carries the old `battery.yml`, `docker-nodes.yml`, `qmn-ubuntu-24.04.yml`, `skylos.yml`.

| Level | What runs | Evidence |
|---|---|---|
| `release` (tag `v*`) | Everything in `deep`, plus `smoke-linux` and `smoke-windows`: start the host on a fresh folder, ask its status, stop it | `qmx-ci.yml:14,258-279`; `tools/ci/qci.py:1050-1067` |
| `gate` and `deep` | `docker-node`: provisions a fresh Ubuntu VM twice with `node-bootstrap.sh`, checks `qmx node verify`, runs the Docker app test. `qmn-lane`: Linux typing, check-mode boot, the switch / rollback **fixture** proof | `qmx-ci.yml:283-334`, `:336-393` |
| UI | **No UI job at any level.** No `pnpm`, Svelte, Playwright or OpenAPI step | `grep -inE "pnpm|qmx-ui|svelte|playwright|openapi" qmx-ci.yml` finds nothing |

CI intent check (`tracker/ci/CI-INTENT-CHECK-2026-11-13.md`):
- `:23` his release level: "Everything above, plus building the installer and starting QMX once with no data, and a browser test of the UI."
- `:51` built: a smoke start only. Missing: installer build, UI build and browser test, `docker-node` and `qmn-lane` at release, a release verdict, a GitHub Release with notes, a rule on which branch a tag may sit on.
- `:108` release reads `known-reds.txt`, so it can ship with known reds; CI-DESIGN §2 said none allowed (`CI-DESIGN.md:48,72`).
- `:126` item 13 needs his answer: "what a release means for him (UI included? installer for Windows only, or both?) and which branch tags come from".
- `:127` item 14 needs his answer: keep `.gitlab-ci.yml` as a fallback or drop it.

## 4. The factory files: where a "UI contract" would sit

| Fact | Evidence |
|---|---|
| The method names no UI step in any phase. The only UI mention in the funnel is a `check_plan.py` bug: real Svelte markup in a fact block fails a UI slice. | `FUNNEL-CHANGES.md:139,146`; `BUILD-PHASE-REDESIGN.md:390` |
| **"Door" already means two things.** In the brief, "Door: one-way or two-way" is reversibility. In the code and UI docs, "the door" is the host's REST+SSE entrance, and "the app-call door" is `/api/apps/{app}/tools/{op}`. A UI field called "door" would collide. | `standing/templates/BRIEF.md:109`; WP `grounding/01` §1 "The door" |
| The brief's test table already has a "Door it calls" column, meaning the public function or command a test drives. | `BRIEF.md:62` |
| The architecture already carries one standing cross-cutting section, `## Operations`, asked "whether he mentioned it or not" for every feature; it rides in element slices and every brief's done line (`Operations: ... (test: ...)`). This is the existing pattern a UI-facing section could copy. | `PLANNING-FUNNEL.md:33-40`; `.claude/skills/funnel-architect/SKILL.md:41-48`; `BRIEF.md:96` |
| The element index is "one line per element ... (module, record, interface, workflow)". Interfaces are already an element kind, with no fields for route, payload or stream. | `funnel-architect/SKILL.md:37-38` |
| Older programs had a "You see" line per plan section (what he sees once it lands). `JOURNEYS.md` collected them as the QA click-through list. The v3 brief replaced it with "In plain words". | `tracker/release-inventory/JOURNEYS.md:58,91,102,255` ; `BRIEF.md:107` |
| Builders are told: "No UI code unless the brief names it." | `standing/PROJECT-RULES.md:35` |
| `checks.toml` covers Python packages only (uv, ruff, pyright, pytest, vulture). There is no template row for a Node/Svelte package. | `standing/templates/checks.toml:1-31` |
| Grounding reads "the area's code, PR history, in-flight branches, fixed lines, removed lists, docs". It does not read the UI or its asks lists. | `PLANNING-FUNNEL.md:73-84` |
| The checkpoint review's walks are down the chain, up from the code, the fixed-line fault walk and the operations walk. No walk covers the API surface. | `SHIPPING-METHOD.md:83` |
| The docs step (change mode after each merge) is designed but not built. | `GAP-AUDIT-2026-11-13.md:127` |

## 5. Skills that could help

| Skill | What it really does | Fit for "what connects to the UI, and how" |
|---|---|---|
| `bmad-ux` | Produces two contracts: `DESIGN.md` (look, Google Labs spec) and `EXPERIENCE.md` (IA, states, interactions, named-protagonist **Key Flows**). Has a **headless mode** for runs from another skill. IA closes "when every stated need has a surface ... and every surface has a journey" (`SKILL.md:9,15-19,73`; `references/headless.md:1-20`) | Good for screens and journeys. Says nothing about endpoints; a journey-to-route column would have to be added |
| `bmad-agent-ux-designer` ("Sally") | A persona wrapper that routes into UX work (`SKILL.md:1-60`) | Interactive only; adds nothing beyond `bmad-ux` for a pipeline |
| `bmad-cis-design-thinking` (+ coach agent) | Empathize, define, ideate, prototype, test, run as a facilitated workshop with energy check-ins (`SKILL.md:86-140`) | Human-led; **no CIS skill has a headless mode** (`grep -l headless bmad-cis-*/SKILL.md` = none). Useful in a UI design session with him to frame journeys, not as a pipeline stage. Produces no API contract |
| `bmad-cis-problem-solving`, `-storytelling`, `-innovation-strategy` | Facilitated workshops (`SKILL.md` heads) | Same limits as above |
| `bmad-architecture` | Spine of invariants; its finalize step says a silent dimension such as "deployment & environments, infra/provider strategy, operations" is a failure (`SKILL.md:70`) | Already in the funnel (stage 4, headless). Its own rule covers deploy; it does not ask for an interface contract by name |
| `bmad-testarch-*` (`atdd` knowledge base) | Ships Pact consumer and provider patterns (`resources/knowledge/contract-testing.md`, `pactjs-utils-*.md`). Its own relevance gate says create no Pact artifacts without a consumer-provider boundary, and without a broker it falls back to "provider source or an OpenAPI spec" (`pactjs-utils-mandate.md:21-44,189`) | QMX has exactly one boundary (desktop UI and host), one team, one repo. Pact is a heavy fit; the fallback it names (an OpenAPI spec) is the lighter one |
| `verify-ui-change`, `replay-user-flows`, `reticle`, `design-system-compliance`, `install-and-verify` | Reticle-based: drive the running app, see "the request that fired", save journeys as replayable flows, check computed styles against tokens | He **dropped Reticle from the new UI** (KIT `RESUME.md:35`). Usable only if he reverses that, or in dev-only mode he agrees to |
| `create-verification-skill` | Writes a project-local `verify-<app>` skill: launch, doctor, drive, evidence, cleanup (`SKILL.md:1-30`) | Strong fit for the release-level "start QMX once with no data and a browser test of the UI"; WIRING-PLAN step 6 already names it (`WIRING-PLAN.md:70-71`) |
| `shadcn` | shadcn/ui for React; templates next, vite, astro (`SKILL.md:264`); no Svelte mention | Not for `qmx-desk` (shadcn-svelte) |
| `frontend-design` | Visual direction | Look only |
| Anything named for API contracts, OpenAPI or deploy | None installed (user and project skill folders searched) | Gap |

## 6. Open design questions for the factory architect

Options and trade-offs only. Nothing here is decided.

**Q1. What is the single source of truth for the UI's API surface?**
- (a) The live FastAPI `/openapi.json`, dumped to a committed file (for example `contracts/host-openapi.json`) by a script, with a CI step that fails when the dump and the code differ. Cheap; the schema already exists at run time (SRV:416, 445-452). Weak spots: three error shapes, SSE event payloads and the app-call door's per-app operations are not described well by OpenAPI.
- (b) A hand-written contract file per screen area (route, payload, stream, error shape, state E/P/M), like `grounding/01`. Readable by him and agents, but drifts unless checked.
- (c) Both: the generated dump is the truth; a short per-screen map points into it.

**Q2. Where in each phase does "what connects to the UI" get stated?**
- Planning: an `## Interfaces` (or "UI surface") section in `arch/ARCH.md` beside `## Operations`, asked for every feature whether he mentions the UI or not, naming each route or stream the feature adds or changes and which screen or journey uses it. Or a field per plan line. Or only for programs flagged "has a screen".
- Brief: a new line in section 11, named so it does not collide with "Door: one-way/two-way" (for example `API:` or `UI:`), listing routes added, changed or removed, or "none".
- Build: builders already may not touch UI code (PROJECT-RULES:35). Should a backend slice also write the client stub, or only the route plus its contract entry?
- Review: an "API walk" at the checkpoint, beside the operations walk: diff the contract against the previous checkpoint and list every change for the UI.
- Audit: a standing audit lens on routes no screen needs, model-only rows a screen needs, and the three error shapes.
- Trade-off: every extra field is something a planner can fill with "none" by reflex; a generated diff cannot be skipped.

**Q3. Who owns the backend asks the UI raises, and how do they reach planning?** Today there are three lists in three places, none committed: `BACKEND-ASKS.md` (KIT, untracked), `WIRING-PLAN.md` §5 (uncommitted), `UI-HANDOFF.md` §26 (plan branches). Options: one committed asks file that the funnel's expand stage reads as input; or each ask becomes an `S` ask only on his yes; or the audit branch picks them up.

**Q4. When does the UI get wired: per program, or as its own program?**
- Per program: each backend program that adds a route also wires its screen. Needs UI checks in `checks.toml` and CI, and a UI-capable builder brief.
- Separate wiring program after the backend lands, from the contract diff. Keeps backend briefs pure; the UI agent works from a stable list.
- The UI redesign's own loop (KIT `RESUME.md:61-70`) is design-first and his-verdict-driven; it may not fit the funnel's "he is not asked" stages 4-6.

**Q5. Should the UI code be in the factory's reach at all before it is committed?** `apps/qmx-desk` is untracked on one laptop. Options: commit it to `ui-redesign` first (his call, since he has not asked for a commit); or keep UI outside the factory until the redesign finishes.

**Q6. The desktop shell and token handoff block all wiring.** Is that a factory concern (a program the funnel plans) or a one-off decision for him? Options in WP `grounding/06` §4 (host serves static files plus a launcher; Tauri; Electron). It meets ruling tension G14 (desktop only vs "web version first").

**Q7. What does "staging" mean now that the staging branch is gone?**
- (a) A pre-release tag (`v0.x.0-rc.N`) that runs the release level and a fresh-install test, before the real tag.
- (b) A staging environment: his demo account on his server, running the candidate, watched for a set time (his "week of watching").
- (c) Both, in that order.
- (d) Nothing beyond the release tag.

**Q8. What does "deployment" cover in the factory?** Four things share the word (§3.2): unit promotion, node-on-server setup, node code switch/rollback, desktop install. Options: one "deploy" phase that owns all four; deploy as a section of the architecture (`bmad-architecture` already treats "deployment & environments" as a required dimension); or only the release and install path is the factory's, and unit promotion stays a product feature.

**Q9. What should the release level prove?** His words (`CI-INTENT-CHECK:23`) say installer build, start once with no data, and a browser test of the UI. Today only a host smoke start runs. Open: Windows installer only or Windows and Linux; does a release require a wired UI; do known reds block a release (CI-DESIGN Q3); which branch tags come from (CI-INTENT item 13); is the node switch/rollback proved on a real VPS before a release, or only on a fixture as now (`switch.py:682-689`).

**Q10. How is the node server deploy tested without paying for hosting?** `docker-node` provisions a fresh Ubuntu runner VM per gate run, free on a public repo. Options: keep that as the deploy proof; add a run against his own VPS on a schedule; or both.

**Q11. Does BMad CIS belong in the pipeline?** CIS has no headless mode, so it cannot run in agent-only stages. Options: use it only in sessions with him (UI design rounds, expand stage for UI-heavy asks); or use `bmad-ux` headless for `EXPERIENCE.md` key flows instead, and add a route column to each flow.

**Q12. How is the UI verified once wired, given Reticle was dropped?** Options: `create-verification-skill` to generate a `verify-qmx-desk` skill driven through the built-in browser; Playwright journeys from `JOURNEYS.md`; or bring Reticle back in dev mode only. Also: Knip and Stryker for the UI were suggested on 12 Nov and never decided (`GAP-AUDIT:132`).

**Q13. Contract tests, or contract diff?** Pact (`bmad-testarch` knowledge) suits many services and teams; QMX has one boundary. A generated-schema diff plus a typed client built from the schema is lighter. Open: which one, and does a breaking change to a route need his yes (a one-way door) or only a note to the UI?
