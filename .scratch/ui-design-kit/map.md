# QMX UI design kit

This is the wayfinder map for the **UI redesign kit** only, started 2026-11-10. It is separate from the older maps in `tracker/map.md` and `tracker/qma-v2/wayfinder*`. Its home is the `ui-redesign` branch (worktree `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-redesign`, cut from engine/base `3ae41ffc`).

Label: wayfinder:map

## Destination

A **design kit** that fresh design sessions open and start designing from, with nothing left to gather: one index (`kit/KIT.md`), the session brief, skills that are chosen, installed and proven, the design workflow, inspiration, a ledger of every idea and issue raised so far (each one covered or open), the screens and journeys to cover, backend facts per screen, and the references (T3 Code, the videos, the October UI). A later build-and-wire session (it also runs QA across the journeys) gets its own brief from the same kit.

## Notes

- **Who:** Mubarak, non-technical, dictates. Short replies; detail goes in files. QMX is quant plus agentic trading: data-heavy, extensible (the Bloomberg-like layout exists for that), used by non-technical people.
- **His rulings:**
  - The October UI (`ui-review/repair`) is a **design proposal**, never the product. It is not a base to keep.
  - The Claude Design canvas look is rejected ("feverish orange"). Designs are made in real UI code with shadcn-svelte.
  - "Surprise me": the design sessions get creative control, and he still gives opinions.
  - Variants he can toggle, not single versions.
  - Installation comes after the UI.
  - Reticle is not needed.
  - taste-skill (website-focused) is not used.
- **Skills to consult:** `writing-for-agents` for every kit file and brief. `grilling` and `domain-modeling` for grilling tickets. `watch` for videos.
- **Agents:** run one at a time, on Opus. Fable only when he says so.
- **Kit files** live in `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-redesign/.scratch/ui-design-kit/kit/`. Earlier grounding is in `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-review-repair/apps/qmx-ui/plan-2026-11/grounding/01-07`, and the release inventory is in `tracker/release-inventory/`.

## Decisions so far

- [Start from current UI](issues/05-start-from-current-ui.md): the October UI is not paramount. Its ideas are traced instead ([Trace the October UI](issues/10-trace-october-ui.md)).
- [Watch the videos](issues/02-watch-the-videos.md): Stageshow is a demo builder; we take its screenshot-judge loop and rules, not its code.
- [Trace the October UI](issues/10-trace-october-ui.md): every October idea traced to his quote, the storyboard and the screen; the keepers and the rejections are listed (`kit/refs/october-ui-trace.md`).
- [Ideas and issues ledger](issues/01-ideas-and-issues-ledger.md): every item raised so far across 16 areas, each decided, open, later or reversed, with 12 open decisions for him at the top (`kit/LEDGER.md`).
- [Skills install and prove](issues/04-skills-install-and-prove.md): 6 Emil skills installed and loading; poteto goes to the build session; Reticle and taste-skill are not used.
- [Design session brief](issues/09-design-session-brief.md): `kit/KIT.md` is the handover index, with his words verbatim in `kit/refs/his-words.md` and every raw path in `kit/SOURCES.md`.
- [Final double check](issues/11-final-double-check.md): none of his words missing, no broken paths; 12 small misreads fixed in KIT, LEDGER, his-words and grounding 05 (`kit/CHECK.md`).
- Branch: the UI work lives on `ui-redesign` (his nudge, 2026-11-10).
- Skills: Emil's index is approved for the chosen skills. Reticle is not used. Poteto is mapped to the build session (ticket 04).

## Not yet specified

- Whether design runs as one session or several (one per area: agent workspace, Usage and Settings, Workflows and Lab, Portfolio, Library and Home). This depends on the screens list and the workflow.
- How the Fable judge is wired into the design loop, if he wants it inside the brief.
- The build-and-wire session's brief: the data layer, the desktop shell, the backend asks, and QA across the journeys. This waits until the design brief settles.
- Per-screen inspiration boards: whether the kit carries them, or the design session gathers them per screen.

## Out of scope

- [T3 Code full tour](issues/03-t3-code-full-tour.md), [Screens and journeys](issues/06-screens-and-journeys.md), [Inspiration sources](issues/07-inspiration-sources.md), [Design workflow](issues/08-design-workflow.md): design work belongs to the design sessions (his ruling, 2026-11-10). This kit only collects; the design sessions will overhaul most screens, so a screen list made now would be redone.

- Installer and desktop shell work (after the UI, his ruling). Grounding 06 holds the facts for later.
- The videos may add little: one of them is about taste-skill, which is not used (his note, 2026-11-10).
- Building or wiring screens. That belongs to the design and build sessions this kit feeds.
