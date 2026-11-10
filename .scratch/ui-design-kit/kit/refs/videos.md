# Reference videos and pages: what is useful for the QMX UI

Both references are about the same thing: **Stageshow**, Benji Taylor's agent skill.
The video explains it. The page is the author's own write-up.
The skill's source (SKILL.md and references) was read from GitHub as a third source.

How this was gathered:
- Video: 68 scene frames, plus 49 frames taken every 8 s across 0:35 to 7:05, plus 8 frames across 10:28 to 11:08.
- No transcript. YouTube refused the captions (HTTP 429), and no Whisper key is set.
  The video's own chapter list and description stand in for the narration.
  Timestamps below come from frames and chapters, so they are accurate to a few seconds.
- Page: benji.org/stageshow, fetched. It has no embedded video.
- Skill source: github.com/benjitaylor/skills/tree/main/stageshow (SKILL.md 1.1.1, references/review.md, rehearse.md, teaching.md, craft.md, verify.md, scripts/layout.mjs, scripts/film.mjs).

One warning before the techniques:
Stageshow is built for marketing illustrations: a fake, simplified copy of one screen playing one short story.
QMX screens are real working screens with dense data.
Its rules on framing, hierarchy, spacing, icons, motion and review carry over.
Its word budget ("3 to 7 real words, grey bars for the rest") does not apply to live QMX screens.
Use the word budget only for explainers, onboarding, empty states and release pages.

---

## Source 1: the video

- **Title:** Head Of Design At X's New Claude Skill Is Insane
- **Author:** AI LABS (YouTube channel, 133K subscribers)
- **Length:** 12:16. Uploaded 2026-11-07.
- **URL:** https://youtu.be/of628n5754g
- **Chapters:** 0:00 Intro, 0:55 Why Screenshots Fail, 2:07 5 Demo Mistakes, 2:52 What Stage Show Is, 4:16 The 7 Steps, 7:56 Installing, 9:20 The Playground, 10:03 Testing on a Real App.
- **Sponsor segment (skip):** about 7:06 to 8:04, OpenArt.

### What it shows

- 0:35 to 2:52: animated diagrams. A plain app screenshot on a landing page gets skipped. A Claude-made animated demo comes out clunky and generic. The point made is that agents lack taste.
- 2:52 to 4:16: Stageshow is Benji's taste written down as about 100 small decisions (3:15, "100 decisions" grid). It builds a stripped-down working copy of one app screen (3:47, "your app" next to "demo copy").
- 4:16 to 7:06: the seven steps, each with its own animated diagram.
- 8:04 to 9:20: the benji.org page, `npx skills add benjitaylor/skills --skill stageshow`, the install into `.agents/skills` with a symlink for Claude Code, then a tour of SKILL.md, assets, references and `bento.md`.
- 9:20 to 10:03: the playground at `stageshow.localhost:1355`. It shows a static card, an upload demo, a Phone toggle, visual styles (glass), a buttons sheet and a Reduced motion toggle.
- 10:03 to 11:35: a real run on "Encore", a music app the channel built.
  The prompt was `/stageshow i want you to add animated components and add it across the site where needed` (10:29).
  The agent reads the references and the gold examples `dark-hero` and `ai-chat` (10:40). It maps the app's `globals.css` tokens into a look file (10:46), films the hero at 390 px and fixes the compact layout (11:03), then writes REHEARSAL.md (11:11).
  The run took about 31 minutes by the terminal clock (45:54 to 1:17:16).
  It still had open items at 11:15: the final gate failed, and the agent called those lines false alarms. Reduced motion, Safari, Firefox and tablet widths were left unchecked.

### Techniques and principles

**T1. The five ways AI UI goes wrong (2:07 to 2:52; frames 2:19 and 2:27 show "too much")**
Too much: real text in every cell. Wireframe: grey blobs that do not read as a product. Boxed: a whole window shrunk into a card. Flat: everything has the same weight. Bland: the brief's style never shows.
The fix at 2:27 sets the busy dashboard beside a calm version: one chart, one highlighted bar, quiet sidebar.
Use for QMX: use the five names as the first questions a judge asks of every screen. "Flat" is the big one for the usage and dense-data screens, where every panel is the same bordered card. On real data screens, cure "too much" with hierarchy (one lead number, quiet support), not by deleting data.

**T2. Taste as written decisions (2:52 to 3:31; "100 decisions" frame at 3:15)**
Skills are written instructions. Stageshow writes a designer's small calls down so the agent stops repeating the same mistakes.
Use for QMX: the design kit should be a list of small, checkable decisions (spacing numbers, icon set, one accent, how a number changes), not mood words. Each operator correction becomes one more line.

**T3. Copy of the real app, not a redesign (3:47, "your app" next to "demo copy")**
The demo is a simplified copy of one real screen. It keeps the site's existing style and does not redesign the page.
Use for QMX: when making explainer or onboarding pieces (for example "how a workflow run works"), build them from the real QMX screen and its tokens, so the explainer and the app look like one product.

**T4. Step 1, placement: still or animated, size, phone version (4:35 still/animation toggle; 4:51 dashed "Demo" slot in a page)**
Decide where the piece sits and at what size before any code. The narrow version is a redesign, not a squeeze.
Use for QMX: for each screen, write down the window sizes and pane widths it must work at, such as full screen, split, and a narrow docked panel. A narrow agent panel must reflow, not just shrink its text.

**T5. Step 2, look: read the app's colours, font and corner roundness (5:07 frame: Colours / Font / Corners)**
The agent reads the product's tokens and maps them onto its kit.
Use for QMX: themes. Keep one token file (colour, type, radius) that every screen, chart and explainer reads. A new theme should only swap tokens. Each theme gets judged separately ("every look shipped, filmed separately").

**T6. Step 3, story: one action, 3 to 5 moments, 10 to 16 s (5:23 timeline frame, "3 moments / One action")**
Each demo shows one thing happening, with a payoff that holds on screen.
Use for QMX: agent workspace and workflows. Define each screen's main moment, for example "agent proposes a step, operator approves, the result lands". Design the screen so that moment is the clearest thing on it. The same applies to animated explainers for the operator.

**T7. Step 4, start from the closest gold example (5:39 frame, "~40 demos")**
Pick the nearest of about 40 hand-made examples, copy its structure (sizes, crop, spacing, beats) and then restyle it. Do not redesign from a glance.
Use for QMX: give each screen a named reference ("gold"): a real app screenshot or a QMX screen already approved. The builder copies its structure, and the judge compares against it. Settings could follow a settings-page reference, usage a billing or metrics reference, and dense data a trading terminal or table reference.

**T8. Step 5, the word budget: 3 to 7 real words, bars for the rest (5:55 frame: "Projects" table with a "real words" slider at 28, target 3 to 7)**
Real words go only on what the story is about. Everything else is placeholder bars.
Use for QMX: only for explainers, empty states and onboarding illustrations. On live screens, use its cousin from craft.md: "real detail on the one row the story is about" and "one number gets to be big". For example, on the usage screen one figure leads and the rest are quiet lines.

**T9. Step 6, motion: a curved cursor path, parts slide in, a loop with no visible restart (6:11 frame: dashed curved cursor path to the "+" button)**
Every motion has a cause. Beats overlap, groups stagger, and the loop ends where it began.
Use for QMX: live data and agent streams. A new row pushes its neighbours smoothly instead of jumping. Numbers roll instead of swapping. A streaming agent answer grows its own height without shoving the page. Nothing appears without an entrance or vanishes without an exit.

**T10. Step 7, self-check by recording (6:27 "checks by recording"; 6:43 frame-by-frame at 0.25x)**
The agent films the demo as it plays, lays the frames out side by side, steps through each moment slowed down, and cannot hand over until the check passes (new in 1.1).
Use for QMX: judge screens from screenshots and recordings, never from code. Capture each screen at each width and theme, plus a short frame strip of any animation.

**T11. The limit: the check catches mistakes, not a boring idea (6:59 frame: "You", "Approve")**
A human still decides whether the result is worth having.
Use for QMX: the judge agent finds faults, but the operator approves each screen from a side-by-side with its gold reference. Do not let a passing check stand in for his yes.

**T12. The playground (9:26 to 10:03)**
Every example can be browsed at desktop and phone width, with Pause, Step, Replay and a Reduced motion toggle. There are bad/good comparison pairs.
Use for QMX: a design-kit page in the QMX app (or a Storybook-like route) that shows each component and screen state at several widths and both themes. A judge or the operator can then look at everything in one place.

**T13. REHEARSAL.md handover (11:11)**
The agent writes which gold it copied, what it changed, what it checked and what it did not.
Use for QMX: each screen pass leaves a short note: reference used, changes, widths and themes captured, what was not checked. The next session or judge reads that note, not the chat.

**T14. Feedback becomes a rule (described at 10:03 onward)**
Plain-words feedback from the user gets added to the skill so the next demo does not repeat the fault.
Use for QMX: every operator correction in a design session goes into the kit's rules file the same day.

---

## Source 2: benji.org/stageshow

- **Title:** Stageshow
- **Author:** Benji Taylor (head of design at X, per the video). Dated 31 October 2026.
- **Length:** a long single page with many live demos. No video embedded.
- **What it is:** a skill plus a small React kit that helps an agent make "faux UI": believable, simplified product screens for landing pages and docs, as stills or short animations.
- **Contents:** `SKILL.md`; `references/` (craft, motion, framing, grids, looks, annotations, real products, filming); `examples/` (dozens of gold examples); `kit/` (React parts for stages, windows, phones, motion); `scripts/` (`film.mjs` contact sheet and measurements, `jumps.mjs` one-frame snaps, `layout.mjs` fit checks).
- **Page sections:** Getting started, What's in it, The playground, What the skill teaches, How a demo is built, How the agent works, Why checks matter, Making Stageshow, Windows, Cursors, Hero demos, Feature cards, Phones, Annotations, Grids, Real products, Limitations, For now.

### Techniques and principles

**P1. The one idea (section "What the skill teaches"; SKILL.md "The one idea")**
"Reads as a real product, simplified to what the viewer needs, framed with intent, and every motion has a cause."
Use for QMX: make it the one-line test for every screen. Swap "simplified" for "ranked" on dense screens: everything can stay, but one thing leads.

**P2. Plan before code (section "How a demo is built"; SKILL.md Workflow)**
Write the plan first: where it sits, the focal object, the action, the payoff, what can be left out.
Use for QMX: a five-line brief per screen before any Svelte is written. For example, settings: focal object = the setting being changed, payoff = the visible effect, left out = advanced options folded away.

**P3. Side-by-side without/with pairs (page showcases: webhook diagram, dark bento, AI writing app, analytics spike, phone notification, meeting booking)**
Each claim on the page is shown as a pair of the same content, worse and better.
Use for QMX: build the design kit as bad/good pairs of real QMX parts (a flat usage page next to a ranked one, a jumpy agent stream next to a smooth one). These teach builder agents faster than prose.

**P4. Teaching pairs: change one thing (references/teaching.md)**
A pair keeps the same content and timing, and only the taught behaviour differs. Examples: an instant label swap against a rolled label, a new row shoving neighbours against carrying them, a reset with no cause against one with a visible "Clear".
Use for QMX: the motion pairs map almost one to one onto live data. A position row inserting, a P&L figure changing, a status chip changing on its own pill, and a popover staying anchored while its list changes height.

**P5. Style anti-patterns (teaching.md "Style"; craft.md "Icons and logos")**
No purple gradient, no sparkles or wands for AI, no glow, no tracked capitals, no tiny 9 to 10 px text, no emoji as icons. One icon set, one stroke, one size (14 to 16 px). Filled icons at 14 px and under. "Show what the AI does."
Use for QMX: the agent workspace must not use a sparkle or purple to mean "AI". It shows the agent's actual step, tool and result. Pick one icon set for the whole app.

**P6. Spacing numbers (craft.md "Spacing and alignment"; rehearse.md lines)**
- Words sit 12 px from any window, card or row edge (flagged under 8 px).
- Row padding is 12 px, or 8 px in a dense list.
- A title sits 4 to 6 px of ink above its subtitle.
- A button keeps 8 to 12 px from the field above it.
- UI text is 11 to 15 px, never under 10 px.
- No near-tangents: edges 1 to 3 px apart get aligned exactly or parted by at least 8 px.
- Columns share one grid template.
- A centred amount centres its digits, and the currency sign hangs outside.
Use for QMX: these go straight into the dense-data and table rules. Dense tables use 8 px rows. Every table column uses a fixed track. P&L and price columns align on digits.

**P7. Framing rules (framing.md; rehearse.md "Lines that are never intentional")**
No empty pane under a list. No "loose list" (rows spread out to fill space). No "fat row" (a one-line row three times taller than its words). No dead corners. Nothing with words gets cut by the crop.
Use for QMX: catch these on every screen with a sparse state, such as a new user's usage page, an empty workflow list or a settings page with few options. Size the pane to the content, or give it a real empty state.

**P8. The rehearsal (section "How the agent works"; rehearse.md)**
Film, lay frames out as a contact sheet, run the measured checks, then watch playback for what the scripts miss. Fix framing first, then hierarchy, then motion, then polish.
Use for QMX: use this order for every screen review. Do not polish icons while the layout is wrong.

**P9. The fresh-eye reviewer (references/review.md)**
A separate reviewer gets only the frames, the checklist, the gold examples and a one-line brief. It never sees the builder's plan, reasons or REHEARSAL.md. Its first question: "does this composition answer this product, or could it be any product in its category?" It returns a ranked list (framing, hierarchy and density, motion, polish). Each finding names the frame file and gives a one-line fix. It films any frame it needs, does not fix anything, and does not soften findings. If it finds nothing, it says "nothing" and lists the frames it looked at.
Use for QMX: this is the judge role the operator asked about. See the method below.

**P10. Stated limits (section "Limitations")**
The checks catch technical mistakes, not dull ideas. It cannot draw. Its taste is the author's own and opinionated. Early results need several feedback rounds. Some rules will age as models improve, but framing and motion rules should last longer.
Use for QMX: plan for 2 to 3 rounds per screen, with the operator as the final judge of "is this right".

---

## Stageshow as a judging method

What it is, plainly: Stageshow is a builder skill with a built-in review loop. It is not a judge tool on its own.
The parts worth lifting for judging QMX screens are:
- the fresh-eye reviewer brief (`review.md`)
- the checklist (`verify.md`)
- the fault names (`rehearse.md`)
- the gold-comparison habit
- the fix order: framing, then hierarchy, then motion, then polish

A Fable model fits the reviewer seat in `review.md`.

### How a design session would run it, per screen

1. **Brief.** One line: the screen, its main moment, and its gold reference (a screenshot of a reference app or an approved QMX screen).
2. **Capture.** Run the QMX UI. Take screenshots with Playwright at full width, a split width and a narrow docked-panel width, in light and dark, and in each state (empty, loading, full, error). For any motion (agent streaming, rows inserting, numbers changing), take a short frame strip or a screen recording, and read it with the `watch` skill.
3. **Measured pass.** Run Stageshow's `scripts/layout.mjs` on the real page (`--select body --width 1440 --strict`). It works on any page, outside a Stage. It reports fit and padding faults, but it is one snapshot and is not approval.
4. **Judge.** Start a fresh agent with only:
   - the frames
   - the gold still
   - a QMX version of `verify.md` (word budget removed; density, table and live-update rules added)
   - the `review.md` brief

   Leave out the builder's plan. The judge returns the ranked list: each finding with the frame file and a one-line fix, plus what it could not check.
5. **Fix and re-shoot.** The builder fixes the largest fault first, captures again, and writes a short REHEARSAL-style note.
6. **Operator decides.** He sees the screen beside its gold and says yes or what is wrong. His words go into the kit's rules.

### What it needs

- **Skill:** Stageshow (`npx skills add benjitaylor/skills --skill stageshow`). Mainly for its references and `layout.mjs`. Installing it is a change to the project, so it needs the operator's go.
- **Tools:**
  - Node 20.19 or later, `playwright-core` and local Chrome for the scripts.
  - A Playwright capture script for the real QMX screens.
  - The `watch` skill for recordings.
  - Optionally the existing `verify-ui-change`, `frontend-design` and `taste-skill` skills alongside.
- **Models:** an Opus builder. A Fable judge only on the operator's explicit ask (he has suggested it, so confirm it per session), otherwise an Opus judge. Use one judge per screen, one at a time.
- **Gold references:** one per screen, gathered before judging starts.

### Limits

- **The kit is React, QMX is Svelte.** The kit's components (Stage, Window, Roll, Collapse) cannot be dropped into QMX. Lift the rules, not the code.
- **`film.mjs` only films Stageshow `.ss-stage` elements.** It errors on other pages, so it cannot film real QMX screens. Only `layout.mjs` runs on ordinary pages. Motion review needs our own capture.
- **Its rules are tuned for sparse marketing demos.** The word budget and "bars for the rest" would wreck a dense trading screen if applied literally.
- **It judges pictures, not use.** It will not catch a confusing click path, a missing control or wrong live data. Past rounds judged QMX layout and usability poor, so click-through journeys still need their own pass.
- **It cannot tell boring from good,** by its author's own words. The operator stays the final judge.
- **Its taste is one designer's.** Where it clashes with an operator ruling, the ruling wins.
- **Cost and time.** The video's single run took about 31 minutes and still ended with a failing gate. The agent called those lines false alarms, and a reviewer should re-check such claims, not accept them.
- **Windows.** The playground runs on `127.0.0.1:5173` instead of the `.localhost:1355` address shown in the video.
