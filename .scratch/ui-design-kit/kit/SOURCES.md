# Sources: every raw file behind the kit

The kit summarizes; this file points at the originals. When a summary is unclear, a detail is missing, or he asks for something "already said", read the source here instead of trusting the summary. A source wins over a kit file.

## Transcripts (his own words)

| What | Path | How to read |
|---|---|---|
| This planning session (2026-11-09 evening to now): his feedback on drafts, Usage, Inbox, Workflows, the Lab, the agent section, T3 Code, themes, the orchestrator, the plan for sessions | `C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Desktop-QMX/0a7a5e72-5e9a-41ae-932b-e0ec24558b41.jsonl` | JSONL, large. Pull `type: "user"` entries with plain text (skip tool results and system reminders) |
| The October session that built the October UI (2026-09-30 to 10-12) | `C:/Users/Mubarak/Desktop/QMX-session-for-Codex/QMX-UI-session-raw.jsonl` (about 120 MB). The same session is zipped as `C:/Users/Mubarak/Downloads/session-export-1791792239774.zip` | Same method. Never read it whole: grep, then read the hits |
| Summary of that October session | `C:/Users/Mubarak/Desktop/QMX-session-for-Codex/session-summary.md`, `START-HERE.md`, `handoff/` | Plain markdown |
| Other exported sessions (risk, product audit, QMA v2) | `C:/Users/Mubarak/Downloads/session-export-*.zip` (each holds a `custom-title.json`), `C:/Users/Mubarak/Downloads/QMX-session-exports-2026-10-12/` | Check the title before opening |

## His drawings

| What | Path |
|---|---|
| The UI storyboard (Excalidraw in Obsidian: 142 elements and 11 pasted images, including the Factory settings reference) | `C:/Users/Mubarak/Documents/brain/brain/Excalidraw/qmx-ui-storyboard.md` (text lives in the compressed drawing block; decode it with LZ-string) |
| Drawing from 2026-11-10 (empty when checked) | `C:/Users/Mubarak/Documents/brain/brain/Excalidraw/Drawing 2026-11-10 15.39.23.excalidraw.md` |

## The October UI (a design proposal, not the product)

| What | Path |
|---|---|
| Code (branch `ui-review/repair`, last commit 2026-10-14; Usage page and rail edits from 2026-11-09, uncommitted) | `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-review-repair/apps/qmx-ui` |
| Start it (launch config `qmx-ui-design`: Vite run directly, port 5173; `pnpm dev` hangs on Node 24) | `C:/Users/Mubarak/Desktop/QMX/.claude/launch.json` |
| Its notes | `UI-BACKLOG.md`, `UI-LEDGER.md`, `DESIGN-RULES.md`, `BACKEND-REQUIREMENTS.md`, `handoff/` in that folder |
| Screenshots (newest set: `2026-10-14-day-one`; the kit keeps the 1600x900 copies in `kit/refs/october/screens-2026-10-14/`) | `C:/Users/Mubarak/Desktop/QMX/workroom/ui-review-2026-10-01/` |
| Last night's notes (wiring plan, T3 Code notes, handoff, skill copies) | `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-review-repair/apps/qmx-ui/plan-2026-11/` |
| Rejected Claude Design canvas from 2026-11-09 (kept only as "what not to do") | https://claude.ai/artifact/HQ24PViRYAxaFTz5azc9fM |

## Backend and plans

| What | Path |
|---|---|
| Backend code (branch `engine/base`, tip `3ae41ffc`), read-only worktree | `D:/QMX-worktrees/engine-base-read` |
| This UI branch (`ui-redesign`, cut from `3ae41ffc`) | `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-redesign` |
| Release inventory: journeys, what shipped, merged PRs, plans | `C:/Users/Mubarak/Desktop/QMX/tracker/release-inventory/` (start at `README.md`) |
| Grounding reports 01-07: backend per screen, workflows, Agent SDK, October method, UI codebase, install and shell, skills | `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-review-repair/apps/qmx-ui/plan-2026-11/grounding/` |
| QMA v2 UI notes and handoff | `D:/QMX-worktrees/unit-plan/tracker/qma-v2/UI-NOTES.md`, `UI-HANDOFF.md` |
| Unit-system screen needs | `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/build/UI-NOTES-UNITS.md` |
| QMA v2 plans (methodology, workflow engine, Lab and pods, Library) | `D:/QMX-worktrees/unit-plan/tracker/qma-v2/` (branch `plan/unit-system`); `D:/QMX-worktrees/agent-system/tracker/qma-v2/` (branch `plan/agent-system`) |
| His memory notes (rulings, feedback) | `C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Desktop-QMX/memory/` (index: `MEMORY.md`) |

## References

| What | Path or address |
|---|---|
| T3 Code: his desktop app, plus its web door (pair in his Chrome) | Desktop app "T3 Code (Beta)"; web `http://172.23.80.1:3773` |
| Video and Stageshow downloads (frames, skill source) | `kit/refs/raw/watch-of628/`, `kit/refs/raw/stageshow-src/` (copied out of a temporary folder; the video file itself was dropped, re-download it from https://youtu.be/of628n5754g) |
| Skill repos (cloned) | `C:/Users/Mubarak/skill-repos/emil-skills`, `C:/Users/Mubarak/skill-repos/taste-skill` |
| Installed design skills | `C:/Users/Mubarak/.claude/skills/` (`variant-picker`, `emil-design-eng`, `break-ui`, `review-animations`, `remove-animations`, `apple-design`) |
| Refero (signed in, free tier; its research chat works best) | https://refero.design |
