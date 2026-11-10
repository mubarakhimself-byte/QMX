# 07 Skills review for the QMX UI design and build (2026-11-10)

Read-only review. It covers 18 Emil Kowalski skills, taste-skill 2.5.1 against the old installed copy, and the installed user and plugin skills that touch UI. **Nothing was installed, linked or run.** Every finding comes from reading SKILL.md files, their reference files, the scripts' headers, the plugin manifests and the QMX UI's own config. No hook, gate or script ran, so their runtime behaviour is described from source, not observed.

## 0. What QMX needs, which decides fit

| Fact | Source |
|---|---|
| SvelteKit 2.70 with Svelte 5.57 (runes), shadcn-svelte 1.7 with the `rhea` style, bits-ui 2.19, Tailwind 4.3, paneforge, lightweight-charts, `@lucide/svelte` | `apps/qmx-ui/package.json`, `components.json` |
| Reticle 2.14 is **already wired**: `@reticlehq/vite-plugin` in `vite.config.ts`, `test:reticle` script, 4 saved flows in `.reticle/flows/` | the same files |
| Playwright 1.63 and Vitest 5 exist (`tests/day-one.spec.ts`) | `package.json` |
| The desktop shell is still open, with Tauri 2 proposed | `WIRING-PLAN.md` §1 |
| Design is done in real code with demo fixtures (`lib/usage/demo.ts`), as variants he can toggle, one screen at a time, judged in a running browser at 1280, 1600 and 1920 | `HANDOFF-2026-11-10.md`, grounding 04 |
| It is a dense trading and agent app, not a marketing site. Numbers, tables and charts dominate. | the same |
| Tools on this machine: Node 24.18, Chrome, Edge, Python 3.14 (`python`, not `python3`), ffmpeg 8.1.2, yt-dlp, Git Bash | checked with `which` and `--version` |

A skill fits when it works on an existing Svelte app with fixtures and data-dense screens. Skills built around React, Expo, Swift or marketing pages ("hero", "one section per screen", photographs) do not fit.

---

## 1. Emil Kowalski skills (`C:/Users/Mubarak/skill-repos/emil-skills`, 18 skills)

**What they carry, all 18:** Markdown only. There are no hooks, scripts, assets, schemas or dependencies. Some have reference files (RECIPES, CATALOG, PICKER, STANDARDS, AUDIT, PLAN-TEMPLATE, API). Code examples are CSS first, plus React and Motion (`motion.dev`). None mentions Svelte: an agent has to translate to `svelte/transition`, `svelte/motion` (Spring, Tween), `{#key}` remounts and `$app/navigation`.

**A quirk in most of them:** an "Initial Response" rule says that when the skill is invoked without a specific question, it replies with one canned sentence and stops. An unattended run must always invoke it with a concrete brief.

**The upstream installer** (`npx skills@latest add emilkowalski/skills`) installs all 18. That is the "garbage" install the operator ruled out. Copy only the chosen folders from the clone instead.

| Skill | What it does | Invocation | Fit for QMX | Mismatch / risk | Overlaps | Stage |
|---|---|---|---|---|---|---|
| `emil-design-eng` | The craft bar: polish, component details and animation decisions (676 lines) | auto (vague description, so it may load often, about 8k tokens) | **High.** tabular-nums, `:active` press, popovers that grow from their trigger, skip tooltip delay on later hovers, reduced motion, hover gating and the "how often is it seen" rule all apply to a dense app | React and Motion examples; some springs and gestures matter only on a phone | `animate`, `review-animations` (same rules) | build, review |
| `prototype` | 3-5 genuinely different variants behind a fixed floating picker (keys 1-N and arrows, R to replay, `?v=` kept in the URL). Each variant has a named axis and a tradeoff table. Commands: `riff`, `keep`. | **manual only** (`disable-model-invocation: true`) | **High.** It is exactly "variants he can toggle" | **Name clash** with the installed `prototype`. It wants an isolated `/prototypes/<slug>` route and never touches production code while exploring. The picker code is plain JS, so it needs a Svelte port. | installed `prototype` (Matt Pocock), `principle-exhaust-the-design-space`, `arena` | variants |
| `break-ui` | Worst-case data behind a dev-only "Demo / Worst case / Empty / One / 1,000 rows" toggle. It reports breaks as Broken, Ugly or Fragile with a fix for each, and fixes only on request. | auto | **High.** QMX screens are built on demo fixtures. The CATALOG covers numbers and money (negatives, 0.1+0.2, `NaN`, live-changing widths, locales), time, collections and states. | Name and email examples are people-shaped. QMX needs an addendum: FX prices with 5 decimals, JPY with 3, huge drawdowns, long strategy and agent names, 40 open positions, zero accounts. | `test-error-states` (Reticle) forces runtime failures; this one forces data shapes. They complement each other. | worst-case data |
| `review-animations` | Strict motion review: ten non-negotiable standards, "approval is earned" (plus STANDARDS.md) | **manual only** | **Medium-high.** A per-screen motion gate | Motion v14 notes are React-specific | `improve-animations`, `emil-design-eng` | review |
| `remove-animations` | Subtraction only. Its gate deletes motion on keyboard actions, 100+/day surfaces and **functional data (charts, tables, numbers, dashboards)**. | auto | **High for a trading app.** It is the right default posture. It edits code, but only to subtract, and asks before removing a dependency. | none notable | `find-animation-opportunities` (its opposite) | motion, review |
| `animate` | Builds one animation in order: whether to animate, purpose, tool, properties, curve, interruption, exit | auto | **Medium.** Use only when a screen needs motion (sheets, toasts, panel open) | Motion examples need a Svelte translation | `emil-design-eng` | motion (later) |
| `find-animation-opportunities` | Read-only. Proposes at most 5-7 motion spots with exact values. | auto | **Low-medium.** One pass after screens settle, if at all | none | `remove-animations` | motion (later) |
| `improve-animations` | Audits the codebase's motion and writes self-contained plans to `plans/` (or `animation-plans/`) | auto | **Low-medium.** A codebase-wide motion audit later | writes a `plans/` folder | `review-animations` | QA (later) |
| `choreograph` | Order and overlap when several elements move together | auto, with a **very broad trigger list** ("timeline", "sequence", "multi-step", "morph") | **Low-medium** | Its triggers collide with QMX words (timelines, step flows), so it would load spuriously | `animate` | motion (later) |
| `apple-design` | Apple's interface and motion principles translated for the web: depth, materials, typography | auto | **Low-medium.** It could inform the neumorphism and true-black theme trials | mostly gestures and springs | `emil-design-eng` | inspiration (optional) |
| `gestures` | Drag, swipe and sheets that track the pointer 1:1 | auto, broad triggers ("drawer", "sheet", "drag") | **Low now.** TileBoard drag and the phone come later. | Motion and React APIs; QMX sheets and drags would trigger it | `apple-design` | later (phone) |
| `mobile-native` | Makes a web app feel native on a phone (100vh, tap highlight, safe areas) | auto | **None now.** Revisit if the phone companion is a web app. | phone only | none | later (phone) |
| `animation-performance` | Diagnoses dropped frames (composite-only properties, main thread, `will-change`) | auto | **Low.** Use only if live tables or charts jank | React re-render advice | none | debug (on demand) |
| `animation-vocabulary` | Glossary that turns a vague motion description into its term | auto | **Low** | none | none | none |
| `ask-sonner` | Guide to the React Sonner toast library | auto | **None.** QMX does not use Sonner. shadcn-svelte's Sonner wraps svelte-sonner, a different API. | React only | none | none |
| `pick-ui-library` | Emil's curated React picks (base-ui, cmdk, Virtuoso, zustand, recharts, motion, next-themes) | manual only | **None.** Every pick is React. The Svelte equivalents are bits-ui, the shadcn-svelte Command, TanStack Virtual, runes, mode-watcher. | React only | none | none |
| `animate-expo` | React Native and Expo motion | auto | **None** | Expo | none | none |
| `write-swift` | Swift 6 | auto | **None** | Swift | none | none |

`ui-cheatsheet.md` (11 rows) and `performance-cheatsheet.md` (7 rows) are not skills. They are short tables worth pasting into `DESIGN-RULES.md`: tabular-nums, `Intl.PluralRules`, absolute dates after a week, never `transition: all`, virtualize long lists.

---

## 2. taste-skill: the new 2.5.1 against the old installed copy

| | New: `skill-repos/taste-skill`, 2.5.1 (2026-11-07) | Old: `~/.claude/skills/taste-skill` (2026-08-13) |
|---|---|---|
| Install name | `design-taste-frontend` | `design-taste-frontend` (the **same name**) |
| Upstream identity | The current default | The "v2 (experimental)" era (§0 Brief Inference, dials). Upstream moved it to `taste-skill-classics` as `design-taste-frontend-v2-experimental`. |
| Purpose | "Professional company websites at the figma.com and x.ai level": one section per screen, hero entrance, dealt "moments", real photographs, shaders for tech and gaming sites | "Landing pages, portfolios, and redesigns. **Not dashboards, not data tables, not multi-step product UI.**" |
| Size and payload | 39 MB. A 381-line SKILL.md, 22 references, 10 Node scripts (about 17k lines; `consistency.mjs` alone is 11.5k), 37 MB of assets (photos, shaders, scenes, `fx-*` HTML widgets, `starter.html`, `system.css`), palette and type JSON | 92 KB. One 1,206-line SKILL.md and a LICENSE |
| Hooks | **A Stop hook** in the frontmatter: a POSIX `for` loop that runs `node scripts/gate.mjs --hook claude` with a 600 s timeout. It needs Git Bash on Windows (present). | none |
| Required tools | Node 22+ and Chrome, Edge or Chromium (all present). ffmpeg is optional. Network access fetches Google Fonts and extra photographs. | none |
| Invocation | auto, with a broad description that names "redesign, restyle, polish or review … inside an existing … Svelte … project" | auto ("frontend", "redesigns") |
| Also linked from | not installed | `~/.agents/skills/taste-skill` links to it, so other agent CLIs (Codex) load it too |

**What the gate does, from `gate.mjs` source.** The gate arms when `start.mjs deal` or `gate.mjs --start` writes `.taste-skill/build.json` in the project. Once armed, every Stop runs headless Chrome checks: `consistency.mjs` at 1440 and 390 plus a 320 walk, `assets/layout/check.mjs`, and `copy-lint`. Any FAIL **blocks the agent from finishing**, up to the round limit (3) plus 4 extra blocks. The checks are website rules: `section-height`, `hero-enter`, `moment-none`, one section per screen, copy slop words. **An app screen would fail them by design** and burn rounds and Chrome time on every stop.

When nothing is armed it exits at once, except one nudge for a recent tasteskill page. It writes state into `.taste-skill/` in the project. A frontmatter hook only runs after the skill is invoked in that session. The plugin route has no `hooks.json`, so the hook arrives only through the skill.

**Fit: none for building QMX, for either version.** Both auto-invoke on QMX-shaped requests and would push website rules onto an app. The old copy actively advises against data tables and dashboards. The new one forces hero entrances and photographs.

**Worth mining read-only from the clone, without installing:**
- the `assets/components/fx-*` widgets (`fx-chart`, `fx-stat`, `fx-tabs`, `fx-progress`, `fx-search`), as visual inspiration;
- the `copy-lint` slop-word idea;
- the "basics" accessibility checks in `consistency.mjs` (accessible names, a Tab walk with a visible focus ring, heading order), as a model if QMX ever wants its own finish gate.

---

## 3. Installed skills and plugins that touch UI

### 3a. The Reticle family (v2.14.0, Apache-2.0, 13 skills)

**What it carries:** the plugin `reticle@reticlehq` (user scope) registers an MCP server through `npx -y @reticlehq/server mcp`. The skills are Markdown that call `reticle_*` MCP tools, plus the `reticle` CLI.

**Duplicates:** standalone copies of all 13 sit in `~/.claude/skills/` and are mirrored in `~/.agents/skills/`. The plugin adds a second `reticle` skill (`reticle:reticle`).

**Status this session:** the Reticle MCP server **failed to connect** (30 s connect timeout). Tool-based Reticle skills cannot run until that is fixed. QMX is already instrumented, so no `init` is needed.

| Skill | What it does | Invocation | Fit | Stage |
|---|---|---|---|---|
| `verify-ui-change` | Drives the running page and returns a pass/fail verdict with the request, the state change and the file:line. You name the consequence before acting. | auto | **High** | browser verification, every change |
| `design-system-compliance` | Reads computed styles against the project's tokens and flags `offTheme` colours, 0×0 or covered controls, and animations that never ran | auto | **High.** Run it per theme (Ink, true black, the neumorphism trial). It does not check contrast or accessibility, and says so. | review |
| `replay-user-flows` | Records a clicked journey as `.reticle/flows/*.json` and replays it deterministically without a model | auto | **High.** It covers his click-through journeys, and QMX already has 4 flows | user journeys, regression |
| `fix-what-i-pointed-at` | The operator clicks "Flag a bug" in the running app, points at an element and types a note. The agent drains the marks, each with its file:line. | auto | **High.** It is the best fit for a non-technical operator who reviews the running UI and dictates | review loop |
| `test-error-states` | Forces a failing API, an empty list, a slow request, timeouts and expiry, then checks the UI copes. The clock half needs no browser. | auto | **Medium-high.** It pairs with `break-ui`. Network mocking needs a driven or leased browser: on Windows, start Chrome with `--remote-debugging-port=9222` (the skill only shows the macOS path) or use a Playwright lease, which downloads Chromium. | worst case, QA |
| `audit-my-app` | Clicks every reachable control and reports dead buttons, console errors and failed requests | auto | **Medium.** Use as a smoke sweep before release | QA |
| `debug-broken-ui` | Reads the click, request, store and console together to find why something does nothing | auto | **Medium.** It matters more once the backend is wired | build (wiring) |
| `drive-desktop-app` | Drives Electron or Tauri, including IPC that browser tools cannot see. Tauri needs a CSP edit, plus the `reticle-tauri` Rust crate for screenshots. | auto | **Medium later**, once the Tauri shell exists | QA (desktop) |
| `false-green-tests` | Finds tests that pass while the app is broken | auto | **Low-medium** | QA |
| `agentic-tdd` | Red-green against the running app | auto | **Low** for design; medium for wiring | build (wiring) |
| `reticle`, `install-and-verify`, `verify-unattended` | Install and wire Reticle, then verify | auto | **Low now**, because QMX is already wired. `reticle` says "do not ask the user anything" and lets `init` write a pre-approval rule, which clashes with "ask before installing". | setup only |

### 3b. Other UI-related skills

| Skill | What it does | What it carries | Invocation | Fit | Mismatch / overlap | Stage |
|---|---|---|---|---|---|---|
| `prototype` (installed, Matt Pocock; links to `~/.agents/skills/prototype`) | A throwaway prototype. UI branch: 3-5 structurally different variants **on the existing route** via `?variant=`, with a floating bar and arrow keys. Logic branch: a single HTML state-machine walkthrough. Afterwards the variants go to a throwaway branch. | Markdown (SKILL, UI.md, LOGIC.md, an openai.yaml) | auto | **High** for both branches | Clashes by name with Emil's. Weaker craft bar, but it prefers variants inside the real page with real density. | variants |
| `frontend-design` (user skill, 55 lines) and `frontend-design:frontend-design` (plugin 1.1.1, 71 lines; **the texts differ**) | Distinctive visual direction, a token plan, self-critique, and a strong section on interface copy | Markdown | auto (both) | **Medium.** The copy rules fit his "few words" ruling: name things by what people control, errors don't apologise, an action keeps its name ("Publish" → "Published"). The hero and "take one aesthetic risk" advice is website-shaped. | duplicates each other; overlaps `emil-design-eng` | inspiration, build (copy) |
| `shadcn` (Vercel) | shadcn/ui CLI, rules and registries | Markdown and rules files. **On load it runs `!npx shadcn@latest info --json`**, and `allowed-tools` pre-approves `npx shadcn@latest *`. | **model only** (`user-invocable: false`). It triggers on "any project with a components.json", so it **will** load on QMX. | **Low as is.** It drives the React CLI and React APIs (`asChild`, FieldGroup, Next and Vite templates). On QMX it may misread the shadcn-svelte `components.json` or add React `.tsx` files. Some rules carry over: semantic tokens, `gap` instead of `space-y`, `cn()`, dialogs need a Title, items inside their Group, no manual z-index. | The right CLI is `npx shadcn-svelte@latest`. No shadcn-svelte skill is installed: a gap. | build (with care) |
| `redesign-skill` (`redesign-existing-projects`, taste-skill's author, 2026-08-13) | A generic "premium" audit and fix pass (fonts like Geist and Satoshi, and so on) | one Markdown file | auto ("upgrades existing websites and apps") | **Low.** It would trigger on his "overhaul" and "redesign" asks with generic advice. Upstream folded it into `design-taste-frontend`. | old taste-skill | none |
| `principle-exhaust-the-design-space` | Build 2-3 competing prototypes before committing | tiny Markdown | auto | **Medium.** Already in line with "variants" | `prototype`, `arena` | variants |
| `principle-experience-first` | Choose user delight over convenience; ship fewer, polished features | tiny Markdown | auto | **Medium.** In line with his rulings | none | all |
| `arena` / `swarm` | N parallel subagent candidates, cross-judged and grafted | Markdown. Default runners are Opus 5.5 and Grok 4.7. | auto | **Low.** It conflicts with "agents one at a time", Fable sparingly, and no subagents spawning subagents | `prototype` | none for the design run |
| `watch` (installed, links to `~/.agents/skills/watch`) | Video to frames plus transcript | Python scripts and an `.env` in `~/.config/watch`. Needs yt-dlp and ffmpeg (both present). Uses `python` on Windows. Whisper is optional. | manual or auto | **High** for the inspiration videos he named (youtu.be/of628n5754g, the benji.org stageshow) | none | inspiration |
| `create-verification-skill` / `maintain-verification-skill` | Generates and maintains a project-local `verify-<app>` skill: launch, doctor, drive, evidence, cleanup, plus a feature map | Markdown with an example feature map | manual | **Medium.** A `verify-qmx-ui` skill would give the long design run one reliable Windows launch-and-check recipe. The maintain pass fans out parallel readers, which clashes with the one-agent rule. | Reticle | QA setup |
| `playground` (plugin) | A single-file HTML explorer with controls, a live preview and a copyable prompt | Markdown plus templates; uses macOS `open` | auto | **Low.** He rejected off-code canvases. | `prototype` | none |
| `anatomy` | Isometric SVG explainer figures, with optional WebGL | 40 MB including `.git`, Node 20.10+ and Chrome scripts; can publish to a public gallery when asked | auto (broad: "explainer", "diagram") | **None** for the app. Possibly useful for explainer pages for the operator. | `artifact-diagramming` | none |
| Built-in browser pane, `chrome-browser`, `computer-use` (Anthropic, synced) | Look at and drive the running UI, take screenshots; Chrome uses his signed-in browser (refero.design) | built into the host | as needed | **High** for looking at screens at 1280, 1600 and 1920 (Reticle gives verdicts, not screenshots, in web mode) and for refero.design and T3 Code | none | inspiration, review |
| `dataviz` (built in) | Chart form, colour and accessibility method | built in | auto on chart work | **Medium.** Use for the Usage chart, equity curves and meters | none | build (charts) |
| `web-artifacts-builder`, `theme-factory`, `canvas-design` (synced) | React and shadcn claude.ai artifacts; preset themes; posters | scripts and fonts | auto | **None** for QMX code | React only | none |
| `bmad-ux`, `bmad-agent-ux-designer` | UX specification documents | BMad | manual | **Low.** He wants design in code, not specs | none | none |
| `ship-check`, `morning-brief` | Factory-era Gate 2 before integration → main | Markdown; runs `adws/ship_report.py` | manual | **None** for UI. These are release-gate tools from the retired factory. | none | none |
| `ego-browser` | none: it is a **dangling link** to `~/.local/share/ego/ego-skills`, which does not exist | none | none | none (clutter) | none | none |

---

## 4. Clashes and duplicates

1. **`prototype` ×2.** Emil's and the installed Matt Pocock one have the same folder and the same `name`, so they cannot both sit in `~/.claude/skills/`. Installing Emil's means renaming its folder and its `name:` (for example `variant-picker`), which is a local edit to record. Matt's stays useful for logic and state prototypes (LOGIC.md has no Emil equivalent).
2. **`design-taste-frontend` ×2.** The old copy is installed; the new one is in the clone. Same name. Installing the new one through `npx skills` would overwrite or clash. Recommendation: install neither, and retire the old one.
3. **`frontend-design` ×2.** A user skill and a plugin skill with **different texts**, both auto-invoked. Keep one.
4. **The Reticle skills ×2–3.** Plugin, `~/.claude/skills` copies and `~/.agents/skills` copies. They stay in step at 2.14.0 today, but the copies will drift when the plugin updates.
5. **UI-variant overlap:** `prototype` (either one), `principle-exhaust-the-design-space`, `arena` and `playground` all claim "show options". Pick one variant tool and name it in the design-run prompt.
6. **Motion review overlap:** `review-animations`, `improve-animations`, `emil-design-eng`'s review table and `remove-animations`. One review gate (`review-animations`) and one subtraction pass (`remove-animations`) are enough.

---

## 5. Recommended set by stage (a recommendation, not a decision)

| Stage | Use | Status | Why |
|---|---|---|---|
| Inspiration | `watch`; built-in browser and Chrome (refero.design, T3 Code); the copy section of `frontend-design`; the taste-skill clone's `fx-*` widgets, read-only | installed, or no install | Videos and real apps first, per his rulings |
| Variants | **Emil `prototype`, renamed** (for example `variant-picker`). Keep Matt's `prototype` for logic only. | install 1 (renamed) | Named directions with axes, tradeoff table, keyboard picker, `riff`/`keep`. Manual-only, so it never fires by accident. Put the harness inside the real app shell (rail, top bar, demo data), as Matt's sub-shape A advises, so a variant is not judged in a vacuum. |
| Build | **Emil `emil-design-eng`**; shadcn-svelte docs through context7 instead of the React `shadcn` skill; `dataviz` for charts | install 1 | It is the craft bar, and most of it is CSS that carries over |
| Worst-case data | **Emil `break-ui`** plus a QMX trading addendum to its CATALOG; `test-error-states` | install 1 | The demo fixtures are where screens lie |
| Motion | **Emil `remove-animations`** first (a dense data app); **Emil `review-animations`** as the gate; `animate` only when a screen truly needs motion | install 2 | A trading app should move little, and these enforce that |
| Review | `design-system-compliance` per theme; `review-animations`; `fix-what-i-pointed-at` for his own marks; the Fable 5.1 judge he ruled | installed | It checks tokens in the real render, and he can point rather than describe |
| Browser verification | `verify-ui-change`; screenshots in the browser pane at 1280, 1600 and 1920 | installed | It gives verdicts with file:line, and the screenshots let him judge the look |
| User journeys | `replay-user-flows` (4 flows exist) | installed | Deterministic re-runs without a model |
| QA | `audit-my-app`, `test-error-states`, `false-green-tests`; `drive-desktop-app` once Tauri lands; optionally `create-verification-skill` to make `verify-qmx-ui` | installed | Release sweep |

**New installs proposed: 5 Emil skills** (`prototype` renamed, `emil-design-eng`, `break-ui`, `review-animations`, `remove-animations`). Optional later: `animate`, `find-animation-opportunities`, `apple-design` (theme trials), and `gestures` and `mobile-native` for the phone.

## 6. Do not install (or retire)

| Skill | Reason |
|---|---|
| taste-skill 2.5.1 (`design-taste-frontend`) | A website builder. Its Stop gate would block app work on website rules. Mine the clone read-only instead. |
| The old `~/.claude/skills/taste-skill` (retire; needs his go, because it is a deletion, and it is also linked from `~/.agents/skills`) | It says "not dashboards, not data tables". It auto-invokes on QMX work with wrong advice. |
| `redesign-skill` (retire; same terms) | Generic and website-shaped; it triggers on "redesign" and "overhaul" |
| `shadcn` (disable for QMX, or accept with an explicit "use the shadcn-svelte CLI" rule) | The React CLI runs on load, and `npx shadcn@latest` is pre-approved |
| Emil `animate-expo`, `write-swift`, `ask-sonner`, `pick-ui-library` | Wrong stack (Expo, Swift, React-only libraries) |
| Emil `mobile-native`, `gestures` (for now) | Phone only |
| Emil `choreograph`, `animation-vocabulary`, `animation-performance`, `improve-animations` (for now) | Little value for a still, dense UI; `choreograph` and `gestures` would also auto-trigger on QMX words |
| `arena` and `swarm` for the design run | Parallel agents break the one-at-a-time rule |
| `playground`, `web-artifacts-builder`, `theme-factory`, `canvas-design`, `anatomy` (for app UI) | Off-code canvases or React artifacts |
| `ship-check` and `morning-brief` (for UI QA) | From the retired factory; not UI tools |

## 7. Install caveats

1. **Copy, don't run the installer.** Copy only the chosen folders from `skill-repos/emil-skills/skills/` into `~/.claude/skills/`, or into the UI worktree's `.claude/skills/` to keep them out of other projects. Note the clone's commit so the source is known.
2. **Rename Emil's `prototype`** (folder and `name:`) before copying, or it overwrites or collides with the installed one.
3. **Hooks:** none of the recommended skills has a hook or script. The only Stop hook in scope is taste-skill's. If it were ever installed, it would run on every stop after the skill loaded, and once armed it would launch headless Chrome (up to 600 s) and block finishing several times.
4. **Auto-invocation:** `emil-design-eng`, `break-ui` and `remove-animations` load automatically. `prototype` and `review-animations` are manual only. To make `remove-animations` manual (because it edits code), add `disable-model-invocation: true`. That is a local edit.
5. **Canned first reply:** always call an Emil skill with a concrete brief. A bare call returns one sentence and stops, which stalls an unattended run.
6. **Svelte translation:** the picker and the break-ui toggle are plain JS or React-shaped. Port them as a dev-only Svelte component: `$state`, `{#key}` to remount on replay, `replaceState` from `$app/navigation` for `?v=`, hidden when `!dev`.
7. **Reticle on Windows:** fix the MCP connect timeout first. A cold `npx -y @reticlehq/server` start can exceed 30 s; a pre-warmed or globally installed server is a decision for him. `test-error-states` network mocks need Chrome started with `--remote-debugging-port=9222` (`C:/Program Files/Google/Chrome/Application/chrome.exe`) or a Playwright lease, which downloads Chromium.
8. **Tools:** Node 24, Chrome, Edge, Python, ffmpeg and yt-dlp are all present, so the recommended set needs no new system tools. `watch` must call `python`, not `python3` (the Store stub).
9. **Gaps worth filling later (not installs):**
   - a small project-local shadcn-svelte rules note, to replace the React `shadcn` skill;
   - a QMX worst-case catalog addendum for `break-ui`;
   - optionally a `verify-qmx-ui` skill from `create-verification-skill`.
10. **Clutter:** `~/.claude/skills/ego-browser` is a dangling link. Duplicates: `frontend-design` ×2 and the Reticle copies ×2–3. Removing them needs his go.
