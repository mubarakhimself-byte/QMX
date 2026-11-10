# Inspiration 01: T3 Code (clicked through 2026-11-09)

He picked T3 Code as the main reference: "easy on the eye", minimal, "deep modules, but for UI". This file is what it does that QMX can take, page by page, with our own spin. It is a reference, not a design to copy.

How it was viewed: its desktop window will not screen-capture, so it was opened through its own web door (`:3773`, paired with a token he entered). That door is itself a lesson (see 10).

## 1. First open: one composer, everything else quiet

- An empty sidebar. One heading in the middle, "What should we build in QMX?", with "or start without a project" under it. One composer.
- The composer holds the model chip (model plus effort plus a fast mark) and Send. Under it sit three quiet chips: checkout, branch, access mode.
- The context sits in a small floating card at top right: machine, "Open in VS Code", "Add project script", branch, "Commit & push", and changes as +/−.
- **For QMX:** the copilot's empty state is one sentence and one composer. The area (Library, unit, Portfolio), the place (This PC or a server) and the access mode are chips, not panels. A floating context card shows where this chat lives and what it has touched.

## 2. Model picker

- Providers sit in a thin column on the left (a favourites star, then each provider's logo).
- The middle is a searchable model list with Ctrl+1 to Ctrl+4 shortcuts and "Show more".
- A reasoning column on the right runs Low, Medium, High, Extra High, Max, Ultra.
- The footer holds Standard / Fast and the access mode.
- **For QMX:** one picker for every place a model is chosen (chat, a workflow step, a routing rule on Usage). The routing table's cells open this same picker.

## 3. Permission modes

- Four icons in one row: read-only (lock), ask before edits (pen), auto (sparkle), full access. Under the row sits one line saying what the picked one means. The chip under the composer then reads "Supervised" or "Full access".
- An approval shows inline, under the exact command: "Waiting for approval · Decline · Approve · More". More holds "Cancel" and "Always allow this session".
- While it waits, the composer reads "Send a message to decline and redirect the agent".
- **For QMX:** this is the approval design. QMX's backend decisions (allow once, allow always, reject with a message, answers) map one to one. The money hook's refusals show the same way, as a line, not a modal.

## 4. The sidebar is the inbox ("Settled")

- Threads fall into bands. At the top, anything that needs you, with a coloured badge on the row (amber "Approval", red "Failed"). Then "Working · n", each row with a live timer and its branch. Then "Settled · 12", collapsed, each row with its age (31d).
- A finished thread "settles" and drops away. "Un-settle" brings it back.
- A setting explains it: "Fold working and monitoring threads into a Working section. They return to the top of the inbox when they need you."
- Hovering a row shows a card: project, machine, branch, model, and the pull request it made.
- **For QMX:** this answers his Inbox complaint ("nothing agentic, where does it take me?"). The Inbox is not a separate list of notices. It is the list of agent sessions and runs, sorted by what they need. Each row opens the session that is asking, and the quick actions (Approve, Decline, Retry) sit on the row. The hover card shows area, place, model, and what the run produced (a report, a unit version, a Library item).

## 5. A thread (the deep-module idea)

- Your long prompt is folded under "Show full message".
- Hours of agent work fold into one line, "Worked for 7h 10m 53s ›". Opening it shows the agent's short progress notes, one paragraph each, with a timestamp.
- Then a short result: what merged, what the tests said, "Found, not fixed", "Stopped after P22".
- At the end: "Settled 32d ago · Un-settle".
- While live: "Working for 14s", the intent in one line, a "Thinking" marker, and the send button turns into a red stop. A command folds to one line once it has run.
- **For QMX:** every long run (a backtest sweep, a workflow, a unit being written) shows as a preview (one line, timer, state) with the detail folded underneath. This is his "preview, then detailed view".

## 6. Surfaces panel (right side)

- "Open a surface": Browser (B), Terminal (T), Files (F), Diff (D), Pull request (P), Linked pull requests (L), Device (M), Side chat (S). Each opens as a tab in the right panel, with + for more.
- The Browser surface is an address bar with "Local servers this thread starts will show up here automatically".
- **For QMX:** this may be what the Lab becomes. One right-hand panel that can hold any heavy result: backtest report, equity chart, journal, unit page, Library item, terminal, browser, side chat. The Lab stops being a destination and becomes a set of surfaces that open beside any chat. This is a question for him, not a ruling.

## 7. Settings as a sheet

- Settings opens over the app, with search on `/` and grouped sections: General, Appearance, Chat, Diffs, Keybindings, SnapShots; Agents (Providers, Threads, Browser, Devices, Scheduled tasks); Code (Projects, Source control, Worktrees); Connections (Environments, Sharing & access); then Maintenance, Labs, About, Archive.
- **Scope line on top:** "Applying settings for [All projects] on [this machine]" (or "across [All environments]"). This is the inheritance he asked for: you pick the level a setting applies to, and lower levels inherit.
- Rows are a title, one line of help, and a control on the right. "Restore device defaults" sits at the top right.

## 8. Providers and "Add provider"

- A provider list on the left: each row has a logo, name, version, sign-in status ("Authenticated · ChatGPT Plus" or a red "Not authenticated") and an on/off switch. There is "Checked 3m ago" with a refresh, and "+ Add provider".
- The detail on the right: status, display name, runtime (paths, launch arguments), and environment variables (keys, base URLs).
- "Add provider" is a 3-step dialog: **Provider → Identity → Config**. A grid of provider tiles (Codex, Claude, Cursor, Grok, OpenCode, Antigravity, Muse Code, Pi), a one-line warning where it matters, then "Continue with ChatGPT" (sign in) or "Configure manually".
- **For QMX Usage v2:** the provider list moves onto Usage (his ruling). "Add provider" uses this 3-step flow and ends with "now available to: Main copilot, 3 workflows" (his "make sure it updates the copilot").

## 9. Scheduled tasks

- The same scope line ("for All projects across All environments") sits above a list, with "+ New task".
- New task: **Runs on** (a machine), Name, Destination (each run starts a new thread in a project and workspace), Base branch, Prompt, Model, **Schedule** as one switch (At a time / Once / Every interval / On webhook), day pills (Mo to Su), and Enabled ("Disabled tasks stay saved but do not run").
- **For QMX Workflows:** triggers fit this form. "Runs on" is our place, the switch matches the engine's trigger kinds, and each fire lands as a run in the Working band.

## 10. Sharing & access (use it from anywhere)

- Per machine: version and its address, a **Network access** switch, Permissions, and **Authorized clients** (2) with "Revoke others" and "+ Create link".
- That is how his browser connected: a link plus a one-time token, and the same app runs in any browser.
- **For QMX:** the host already has a bearer key and observer tokens (`PUT /api/settings/observers`). This page is their UI. It also changes the shell question: a web door plus pairing could serve the phone companion and a second PC, with the desktop app as a thin wrapper.

## 11. Small things worth taking

- Every icon button has a tooltip, and one-letter shortcuts are everywhere.
- Status words are coloured, short and the same everywhere: Working, Approval, Failed, Settled.
- Snapshots means "capture a window and attach it to your draft" (desktop only). For QMX this is useful for pasting a chart or a broker screen into a chat.
- Errors appear in three places: a banner, an inline card with the reason ("Provider session failed to open: the workspace folder no longer exists"), and the sidebar badge.

## What this suggests for QMX (proposals, for his yes)

1. **An agent workspace** in place of four copilots: one sidebar grouped by area (his "projects"), banded Needs you / Working / Settled, hover cards, and a surfaces panel. The Inbox folds into it.
2. **Usage v2** keeps the T3-style header (period, Cost / Tokens / Limits, refresh), one big number and a chart, with breakdowns one level down. Providers move in with the 3-step add flow, and routing gets the scope line for inheritance.
3. **The Lab question:** surfaces may replace the Lab as a place. Results open beside the chat that made them, and the Library keeps them.
4. **Scope lines** everywhere a setting can be inherited (all areas, this area, this unit; all places, This PC, a server).

Still to look at in T3 Code: Usage and analytics in full (he sent a screenshot), Source control, Worktrees, Environments (empty on the web), Devices, Threads settings, Labs.
