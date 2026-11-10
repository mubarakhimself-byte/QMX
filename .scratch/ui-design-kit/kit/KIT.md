# QMX UI redesign kit: start here

A handover from the previous design lead to the design team. Everything that shaped QMX's UI so far is collected here: the operator's words, the October work and its lessons, the backend, references, and skills. The team is free to overhaul everything. This kit exists so nothing has to be rediscovered, not to fix any design.

## The operator

Mubarak: non-technical, dictates (expect transcription noise), reads short replies, and wants **creative control handed over**: "surprise me", take a reference, give it your own spin, improve it. His opinion still counts at every step, so the work is a back-and-forth. He judges designs by running and clicking them, never by reading descriptions.

## QMX in one breath

Quant plus agentic trading research on a desktop (Windows first). It is data-heavy and update-heavy, and agents run in it: chats, workflows, mini apps, backtests, trading nodes, a Library that holds everything. Its users are non-technical. It is **extensible like a box of Legos**: every part has defaults he can add to, remove or rebuild, which is why the October layout borrowed Bloomberg's tiling. Every job shows where it runs (This PC or a named server).

## Read in this order

1. [`refs/his-words.md`](refs/his-words.md): every message he sent in the planning session (2026-11-09 to 11-10), verbatim, plus two pasted images in `refs/images/`. The ground truth for what he wants.
2. [`LEDGER.md`](LEDGER.md): everything raised so far, by area, each decided, open, later or reversed, with the **open decisions** at the top.
3. [`refs/october-ui-trace.md`](refs/october-ui-trace.md): the October UI idea by idea (his ask, the storyboard, what was built, his verdict), the keepers and the rejections. Screens are in `refs/october/screens-2026-10-14/`, and its rules in `refs/october/DESIGN-RULES.md`, `UI-BACKLOG.md` and `UI-LEDGER.md`.
4. [`refs/grounding/04-earlier-design-method.md`](refs/grounding/04-earlier-design-method.md): how the October work succeeded (options, then his pick, then click-through at 1280/1600/1920) and failed (screens rushed with no options step, wordy panels, borrowed looks).
5. [`refs/t3-code.md`](refs/t3-code.md): T3 Code, a reference he liked for being easy on the eye, with a caveat: on 11-10 he said "we might actually not use it. There are issues." It is useful for minimal, the inbox-like Working/Settled sidebar, inline approvals, preview then detail, surfaces, the settings scope line, add-provider. Plus [`refs/images/t3-code-usage-page.png`](refs/images/t3-code-usage-page.png).
6. [`refs/videos.md`](refs/videos.md): Stageshow, and its screenshot-only reviewer loop.
7. The backend, when a screen needs facts:
   - [`refs/grounding/01-backend-wiring-map.md`](refs/grounding/01-backend-wiring-map.md): routes per area;
   - [`02`](refs/grounding/02-workflows-as-plugins.md): workflows are QMX engine documents; mini apps are Claude plugins;
   - [`03`](refs/grounding/03-agent-sdk-for-ui.md): what the Claude Agent SDK provides and what QMX drops;
   - [`06`](refs/grounding/06-install-and-shell.md): install and first start, for later.
8. [`SOURCES.md`](SOURCES.md): the raw originals behind every file above (transcripts, the Obsidian storyboard, the October code and how to run it, plans, memory). **A source beats a summary**: when a summary is thin or he says "I already said this", go to the source.

## What was rejected (so it is not repeated)

- The 2026-11-09 Claude Design canvas drafts: "ugly", words slapped together, uneven type, poor icons, wasted space, the "feverish" Claude orange, no components. Design in real code with shadcn-svelte, and look at the result running.
- Single versions: he wants **variants he can toggle**, like themes.
- Prose instead of controls; depth missing (he wants a preview first and the detail one level down).

## Skills on hand

Installed in `~/.claude/skills/` and they load. None has been run on a QMX screen yet, so try each one early. He may move the focus from aesthetics to **design standards**. Reviewed in [`refs/grounding/07-skills-review.md`](refs/grounding/07-skills-review.md).

- **For designing** (Emil Kowalski's set, chosen from his index):
  - `variant-picker` (his `prototype`, renamed): several genuinely different versions behind a picker;
  - `break-ui`: worst-case data behind a toggle;
  - `emil-design-eng`: the craft bar;
  - `review-animations` and `remove-animations`;
  - `apple-design`.

  Their example code is React, so take the method and write it in Svelte.
- **For building later:** the `poteto-mode` playbooks (feature, prototype, visual-parity, orchestrate) and principles (experience-first, exhaust-the-design-space, prove-it-works, type-system-discipline).
- **Not used** (his rulings): Reticle; taste-skill (built for marketing sites, and its stop hook would block app work); `redesign-skill`; the React `shadcn` skill (QMX uses shadcn-svelte).
- **Writing kit files or briefs:** `writing-for-agents`.

## Where the work happens

- **Branch:** `ui-redesign`, worktree `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-redesign`, cut from engine/base `3ae41ffc`. Nothing is merged until he says so.
- **Design code:** where the new UI lives is the team's first call. `apps/qmx-ui` on this branch is a stale stub from 2026-10-01; replacing it is fine. Grounding 05 judges the October code "worth keeping", but **his ruling overrides it**: the October code was a proposal and was never meant as the product.
- **This kit** is committed on `ui-redesign`. Commit new work there; never push or merge without his word.
- **Stack:** SvelteKit + shadcn-svelte, unless the team finds a strong reason to change it.
- **Reference UI:** the October UI runs from `.claude/launch.json` (`qmx-ui-design`, port 5173) in the main QMX checkout; details in `SOURCES.md`. Look at it, click it, and borrow ideas, but don't inherit its layout.
- **Inspiration:** his Chrome stays signed in to Refero (use its research chat), Pinterest and X. Mobbin is free tier only; he will not pay. Dribbble also counts as a source.

## After design

A separate session builds the agreed designs into the real UI, wires them to the backend (`refs/grounding/01`, `refs/wiring-plan-draft.md`), and QAs every user journey (`C:/Users/Mubarak/Desktop/QMX/tracker/release-inventory/JOURNEYS.md`). Installation comes after that (`refs/grounding/06`).
