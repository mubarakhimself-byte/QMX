# UI notes for the future UI-wiring session

> **Read `UI-HANDOFF.md` first (banner added 2026-10-18).** It is the current UI list and wins where this file differs. In particular the usage page has no cap: §6's "One Claude Max account only… default cap 50%" is superseded (rulings 26, 90, 106; UI-HANDOFF §9 row 15, §12 rows 5, 6 and 23).

Everything about the UI that came up while planning QMA v2 (2026-10-12/13). The UI wiring is a **later, separate session** (operator ruling, 2026-10-13 evening). This file is its starting brief. It is not a design.

Source pointers:
- `op HH:MM` = the operator's own words in the planning session, UTC, 2026-10-12 unless marked 10-13. Full texts are in the raw session transcript; the digest cuts long messages.
- `R32 §x` = `tracker/agent-system/research/32-devops-and-ui-protocol.md`.
- `HIW §x` = `tracker/qma-v2/archive/2026-10-13-wednesday-frame/HOW-IT-WORKS.md` (archived; evidence only). `H1 fact n` = `tracker/qma-v2/archive/2026-10-13-two-engine/H1-sdk-facts.md`.
- "Proposal" marks Claude's design work he has not ratified.

## 1. Where the UI stands

- The SvelteKit UI lives on `ui-review/repair` (worktree `QMX-worktrees/ui-review-repair`). It was built from the Claude desktop and Codex desktop apps: chat, sessions, a right-hand panel with a terminal. (op 08:39: "this right-hand panel, which has like a terminal")
- Ship it as a browser app first so agents can click through it; the desktop app comes after. (op 10:40: "it might first be shipped as a browser")
- He wants the UI considered in every design, even when it isn't being built. (op 08:54; op 15:22: "UI is very important")
- His standing rules from earlier UI sessions still apply: anything configurable is editable in the UI; show where every job runs (local or a server); one screen at a time with options. (memory notes `qmx-operator-standing-rules`, `qmx-lego-vision`, `ui-one-screen-at-a-time`)
- On 10-13 04:22 he said "we should be able to ship the UI now". The evening ruling overrides that: wiring waits for the harness.

## 2. Protocol decisions to keep (R32 Part B; HIW §11)

- **Keep today's 14 block kinds** (`user, text, plan, agents, tool, changed, artifact, table, entity, question, permission, panel, handoff, needs_you`). New meaning goes inside `content` fields (`pane`, `role`, `level`, `kind`, `status`, plus a `v` version). No new block type for the first release. (R32 §B2, §B11)
- **Two channels, both SSE.** Durable: today's events table and topic streams, replayable with `Last-Event-ID`. Live: a new `GET /api/sessions/{id}/live` for token deltas, terminal bytes, cursor moves, tool progress and diff previews; nothing stored, dropped on disconnect. (R32 §B3.2, §B9)
- **UI to server is plain POST:** turn, steer, stop, approval answer, terminal command. WebSocket only later, for an interactive terminal (keystrokes, resize). (R32 §B10)
- **One event envelope** with `session_id`, `run_id`, `turn_id`, `parent_run_id`, `agent_path`, `engine`. Both engines are normalised into it, so the UI never knows which SDK ran. (R32 §B3.1, §B4)
- **New topic `approvals`** beside the seven existing topics. (R32 §B3.2)
- On attach, `/live` sends one snapshot: open runs, pending approvals, open terminals, current cursor. Keepalive every 10 s. (R32 §B9)
- One recorded-session contract test must pass on the old and the new render paths. (R32 §B11)
- **Open:** archive/2026-10-13-two-engine/BASELINE.md proposed Codex's app-server JSON-RPC instead. The planning audit recommends keeping SSE and the stored blocks and only borrowing Codex's thread/turn/item names and approval shape. Decide once, before this session starts. (planning audit §3.1 "UI protocol")
- Watch the browser's ~6 connections per origin over HTTP/1.1; proposal is one multiplexed live stream per window. (R32 §B10)

## 3. The chat and sessions screen

- It should feel like talking to Claude Code. He mostly doesn't want logs; he wants to see sessions, what's running, sub-agents, tool calls, and the cursor when computer use is on. (op 10:02: "most cases they don't want to see the logs"; "I can see that your cursor move")
- Session controls, all out of the box like Claude Code or Codex (10-13 04:14 Q3; HIW §8, §9, §12):
  - effort control changeable mid-session, like `/effort`; an effort change shows as an event;
  - automatic compaction plus "compact now" with an optional note; a compaction shows as an event;
  - stop, interrupt and steer mid-turn (R32 §B9);
  - model switch mid-chat with a **cost warning pop-up** first, because the cache belongs to the old model. (op 15:01: "a simple pop-up that this is gonna cost more"; H1 fact 6)
- Events the shell needs (HIW §11): effort changed, compaction, plugin loaded, which permission rule matched a call.
- Drawer tabs used in the UI work so far: Activity, Artifacts, Diff, Terminal, Browser. Terminal is a preview tab in the copilot work area, not a global dock. (memory `qmx-ui-rebuild`)
- Terminal: `terminal.opened/output/closed`; the panel block keeps the last 64 KB plus a log artifact. Diff: from `file.changed` receipts, live `diff.updated`. (R32 §B7)

## 4. Approvals as events

- An approval is an event, not a modal hidden in the engine: `approval.requested` (durable, `permission` block) and `approval.resolved`. (R32 §B3.3, §B5)
- One answer route `POST /api/approvals/{id}` with `allow_once | allow_always | reject_once | reject_always | cancel`, optional edited arguments, idempotent. (R32 §B5)
- After a restart a Claude approval that was waiting shows **expired**, never "pending", with "re-run from here". (R32 §B5, risk 5)
- Permission rules (allow / ask / deny, Claude Code syntax and modes, rebuilt on the OpenAI side) are edited in the UI; sticky "always" decisions are listed on a settings screen. (10-13 04:14 Q1; evening ruling; HIW §3)
- Publish, install, schedule and "managing" ask unless an allow rule says otherwise. (10-13 04:14 Q1)
- The always-on money hook (money is read-only for agents) shows its refusals in the session and the log. (10-13 04:14 Q1)

## 5. Sub-agent tree

- Every sub-agent is a child session. The parent shows one `agents` card per child (name, model, status, elapsed, tokens, cost, last tool); clicking opens the child session. (R32 §B6)
- Live text from several children at once stays separate by `agent_path`. The parent stream carries only start and finish; detail lives in the child. (R32 §B6)

## 6. Usage page (T3 Code style)

- Modelled on T3 Code's usage view; he showed a screenshot. (op 10:02: "how much I've used token-wise, who am I using?")
- Top: plan windows as bars with reset times. Claude shows **percent of the 5-hour and 7-day windows**; key providers show USD. (R32 §C4; HIW §10)
- ~~**One Claude Max account only.** Background agents may use only spare 5-hour usage, **default cap 50%, editable** in Settings; show the cap on the bar. (evening ruling)~~ **Superseded (rulings 26, 90, 106):** any number of accounts; no QMX cap; the bars are the providers' own readings only (UI-HANDOFF §12 row 23).
- Below: tokens and cost over time by kind; filters by engine, model, account, agent, workflow and where it ran; per-model table with cache hit rate; cache savings; top runs by cost; a price table editor with "Map to". (R32 §C4)
- Banner: "estimates, not your bill". Claude usage figures are labelled estimates. (R32 §C4; 10-13 04:25 decision)
- Data notes: Claude rate-limit events arrive only on status change, so cache the last one per window (H1 fact 10). OpenRouter usage and limits come from `GET /api/v1/key` (H1 fact 20).

## 7. The temporary console

- The harness ships a simple console so he can check each piece. It is **temporary and will be deleted** once the real UI is wired. (op 10-13 03:55: "console is okay, but it will be deleted later")
- Anything the console proves (sign-in hand-off, event samples) must also work for the real UI. The UI session gets a handoff pack: API description, recorded event samples, the console as a reference client. (HIW §11)
- Claude sign-in: he runs `/login` himself in QMX's own Claude config folder. The UI must never collect, store or pass a Claude token (Anthropic's terms). ChatGPT sign-in is an OAuth flow QMX may store. (H1 facts 4, 17)

## 8. Transcript and log export

- Every session, local or on a server, can export its transcript, log and usage: an **Export button per session** writing one readable folder. (op 09:07: "automatically export the transcript and the logs"; planning audit unit U8)
- A plain "What it did" card first, raw logs one click down. (R32 §A2.6, recommendation 6)

## 9. Computer use and browser

- Show the agent's cursor and screenshots live: `cursor.moved` / `cursor.action` with x, y and screen size, drawn as a dot over the latest `browser.snapshot`. Cursor events are live only; the `tool` block keeps the full action list. (R32 §B7; op 10:02)
- These live kinds were deleted in architecture revision 3 and must come back. (HIW §11; backlog B53)
- Computer use itself is later work (backlog B17): cTrader, MT5 and TradingView trials on demo accounts, money read-only. Proposal: an approval card with a screenshot for each click at first. (planning audit unit U9)
- A QMX browser profile with his logins, such as TradingView, separate from his own browser. (op 10:02; backlog B38)

## 10. Later screens that depend on other work

- **Organogram and homes** (backlog B30): the copilot page is a shell listing every session with a badge for its home (Lab project, Portfolio, general). Opening a Lab session there doesn't move it; its context stays in the Lab. The general copilot can combine Library, Lab and Portfolio. Session events carry the home (kind, project id) so the shell can badge and filter. (op 10-13 04:14 Q4: "a chat session from, let's say, the portfolio has a badge"; HIW §4, §11) He wants this derived from the UI itself. (op 10-13 04:22)
- **Mini apps as plugins** (B23): an install card that shows what the app asks for; new or agent-built apps install disabled until he approves. (HIW §7, proposal)
- **Workflows** (B33): a settings panel per workflow for models and defaults. (op 15:53: "we can have a settings panel") Earlier work started from an n8n-style node editor; he now prefers graphs and loops. (op 16:22, 17:11)
- **Two agents editing the same thing** (B36): show both variants and a comparison. (op 15:22: "how do all these things render in UI")
- **Brokers in Settings** (B39). (op 10:02)
- **MCP apps** (B16): discussed in the old UI session, not designed. (op 15:01)
- **Phone approvals** (B14) and **voice mode** (B15): later.
- **QA:** `create-verification-skill` with many complex user journeys driving the real UI, plus a fresh-install test. (op 10:34; op 08:39; backlog B47)

## 11. Claude's suggestions (not his)

From `USER-JOURNEYS.md` §3 (unreviewed spin ideas) and the audits. Proposals only.
- A restart banner listing what resumed, failed or is waiting (spin 1).
- A "what works today" card on first run, naming every `not_implemented` in plain words (spin 3).
- Key-safe chat: a pasted key is redacted before any model or log sees it (spin 12).
- An engine parity badge on sessions, skills and plugins ("both engines" or "Claude only") (spin 13).
- A pre-flight estimate before long runs: time, USD and share of each window (spin 9).
- A "switch back at reset" chip after a forced model switch, offered never performed (spin 19).
- One multiplexed live stream per window to stay under the browser connection limit (R32 §B10).
