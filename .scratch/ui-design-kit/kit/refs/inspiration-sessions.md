# Inspiration: Sessions (copilot chat and agents)

Scouted 2026-11-11. About 28 pages looked at. 15 entries, ranked within each question.

**How these were seen. Read this first.** The built-in browser opened, but its pane was hidden, so no screenshot ever rendered. Heavy pages (Antigravity, Cursor changelog) also timed out on text reads. Only Zed was read through the browser, and then only as text. Every other entry was read as page text through WebFetch. **No entry was seen as a picture.** Each one is tagged "not seen in a browser". The labels quoted are the products' own words, but layout and look still need a human eye. Open the URL and scroll to the named section before taking anything.

Already covered elsewhere and not repeated: T3 Code, Warp's agent panel, Linear for Agents, Lemni, Conductor, Cofounder.

---

## 1. THE CHAT INPUT

### 1.1 Claude Code desktop: one quiet row of chips under the prompt box
- URL: https://code.claude.com/docs/en/desktop (section "Prompt box"). The product page https://claude.com/product/claude-code shows the same box with "Auto · Opus · Extra high" beside it.
- Take: the box holds only text and Send. One row under it reads left to right: where it runs (environment), which folder (with a Worktree switch), access mode, model with an Effort section inside, and a small **usage ring** that shows plan usage when clicked. Every chip has a shortcut (model, effort and access mode each have one).
- Take: a single **+** button holds everything you can add: files or photos, a folder, connectors, plugins, slash commands. `@` points at a file, `/` lists commands and skills together. An empty box shows a grey suggested prompt that Tab accepts.
- Don't take: five access modes (Manual, Accept edits, Plan, Auto, Bypass permissions). That is too many words for a non-technical owner. Three is enough (see 1.5).
- Answers: 1 (not seen in a browser)

### 1.2 Cursor agent: queue or steer while the agent works
- URL: https://cursor.com/docs/agent (section on follow-ups while Agent works)
- Take: pressing Enter while the agent runs **queues** the message. Queued messages are listed in order under the running task, can be dragged to reorder, and each has a **Send now** button that pushes it in at the agent's next step. Cmd/Ctrl+Enter sends at once.
- Take: one setting decides what plain Enter does ("New Messages: Queue / Steer"), so a person who always wants to redirect does not need a second key.
- Don't take: the hidden "press Enter twice to steer" and Tab tricks. Cursor's forum shows users lost track of which mode they were in and cancelled work by accident. Keep the queued messages visible and labelled.
- Answers: 1 (not seen in a browser)

### 1.3 Cursor: voice chat button sits where Send sits, only when idle
- URL: https://cursor.com/changelog (entry "Voice Chat with Agents", 6 Nov 2026)
- Take: when the agent is idle and the box is empty, the Send slot becomes **Start voice chat**, next to the dictation microphone. Type a word and it turns back into Send. One slot, no extra button.
- Take: during a voice call the agent speaks short progress notes and a short final answer, and you can switch between the agents of a project mid-call.
- Don't take: the named voice personas (Ara, Eve, Leo...). Decoration.
- Answers: 1 (not seen in a browser)

### 1.4 Wispr Flow: dictation that cleans up a long spoken message
- URL: https://wisprflow.ai/ (the animated demo cards under the hero)
- Take: after speaking, the bar says **Cleaning up...**, then drops in finished text. It removes filler words, fixes repeats, and keeps the correction when you change your mind mid-sentence ("at 5... actually 6pm" becomes "at 6pm"). That is exactly what a long dictated brief needs before it reaches the agent.
- Take: an **Add word** panel teaches it names it got wrong (useful for symbols and broker terms).
- Don't take: the "45 wpm vs 220 wpm" style marketing cards. They are illustrations, not the app.
- Answers: 1 (not seen in a browser)

### 1.5 Codex in the ChatGPT app: three access modes, each with one plain line
- URL: https://learn.chatgpt.com/docs/permission-modes
- Take: the control sits below the composer, and each choice is one plain sentence: **Ask for approval** ("Always ask to edit external files and use the internet"), **Approve for me** ("Only ask for actions detected as potentially unsafe"), **Full access** ("Unrestricted access..."). The middle one sends safe requests through an automatic check instead of asking.
- Don't take: the fourth "Custom (config.toml)" choice in the main picker. Hide expert options one level down.
- Answers: 1 (not seen in a browser)

### 1.6 VS Code: the context meter you can open
- URL: https://code.visualstudio.com/docs/copilot/chat/chat-sessions (section on the context window control)
- Take: a small control in the input. Hovering it shows how full the conversation is, a breakdown by kind (messages, files, tools), and the session's total spend. Its menu holds one action, **Compact Conversation**.
- Don't take: the extra slash commands (/fork prompt, /code). Too much to learn.
- Answers: 1 (also 3) (not seen in a browser)

---

## 2. MANY AGENTS IN ONE PLACE

### 2.1 VS Code Agents window: one list for every agent, from every tool
- URL: https://code.visualstudio.com/docs/copilot/chat/chat-sessions (sections on the sessions list and the Agents window)
- Take: one left list, grouped by project, filtered **Active** by default with **Done** one click away. An **External** filter pulls in sessions started by other agent tools (Copilot CLI, Claude Code, Codex) so nothing is scattered. Each row carries a progress dot and an unread dot; hover gives **Mark as Done**.
- Take: **a session stays "in progress" while any of its chats is still working.** That is the roll-up rule the shortlist asked for: the parent never shows done while a child is busy.
- Don't take: the separate "Chat view" list with different words (Archived there, Done here). Use one word.
- Answers: 2 (not seen in a browser)

### 2.2 Google Antigravity Agent Manager: an inbox that only speaks when needed
- URL: https://antigravity.google/ (the page would not render in the hidden pane; the description comes from Google's launch post, https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/, and third-party guides)
- Take: three places in the sidebar: **Inbox**, **Workspaces**, **Playground**. The Inbox lists every agent across all projects and raises one for three reasons only: it needs permission, a plan is ready to review, or the work is done. The Playground is a scratch space whose chats can later be moved into a real workspace.
- Don't take: separate editor and manager windows. One window is enough for him.
- Answers: 2 (also 3) (not seen in a browser, partly secondhand)

---

## 3. THE TRANSCRIPT

### 3.1 Claude Code desktop: tool work folds into plain one-line summaries, with three view levels
- URL: https://claude.com/product/claude-code (the sample session "Fix the double-charge bug in checkout") and https://code.claude.com/docs/en/desktop (section "Transcript")
- Take: runs of tool calls collapse into sentences a person can read: "Read 3 files, searched the checkout flow", "Ran agent · Reproduce the double-submit...", "Edited charges.ts +9 -3", "Ran 2 commands". A helper agent shows as one such line.
- Take: one switch for how much to show: **Normal** (summaries), **Thinking** (adds the reasoning), **Verbose** (every step). He stays on Normal; a builder can flip to Verbose.
- Don't take: code-review cards ("Walk through in diff", "Apply fixes"). Coding only.
- Answers: 3 (not seen in a browser)

### 3.2 Google Antigravity: the plan and the walkthrough as documents you comment on
- URL: https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/ (section on Artifacts)
- Take: the agent's work is shown as a few named documents instead of a log: **Task list**, **Implementation plan**, **Walkthrough**, plus screenshots and browser recordings. You leave a comment on a line of the plan and the agent picks it up without stopping.
- Don't take: the browser recordings as the default proof. Heavy for trading work; a chart or a report is the right artifact.
- Answers: 3 (not seen in a browser)

### 3.3 Amp: a recap panel at the top of a long thread
- URL: https://ampcode.com/ (the demo video, near the threads list)
- Take: a **Recap** panel states the thread's goal and its latest outcome in two lines, so a long thread reads result-first. The threads list also has "snooze until the next message" on right-click, which hides a quiet thread until it speaks again.
- Don't take: the shared tmux terminal and "orb" naming. Developer-only.
- Answers: 3 (also 2) (not seen in a browser; the recap sits behind an experimental setting)

---

## 4. BESIDE THE CHAT

### 4.1 Claude Code desktop: four named panes, opened from the title bar
- URL: https://code.claude.com/docs/en/desktop (section "Panes beside the chat")
- Take: four buttons in the title bar, **Terminal**, **Changes**, **Browser**, **Files**, each with a shortcut. Panes can be dragged, resized, minimised or popped into their own window; one shortcut closes the focused pane. A file path in the chat is clickable and opens in the right pane; right-click offers **Attach as context**.
- Take: a details panel of small cards (**Environment**, **Changes**, **Context** with a percentage, **Background tasks**) answers "where is this running and what has it touched" without leaving the chat.
- Don't take: many pane options hidden in a "⋮" menu. Keep the pane list short and visible.
- Answers: 4 (also 2) (not seen in a browser)

### 4.2 VS Code and Cursor: side chat, asked from a selection
- URL: https://code.visualstudio.com/docs/copilot/chat/chat-sessions (section on side chats) and https://cursor.com/docs/agent (`/side`, `/btw`)
- Take: select text in an answer and pick **Quote** or **Ask in a Side Chat**. A side chat opens beside the main one with a single **Ask Question** field, so a quick question does not derail a long run. In Cursor you can @-mention the side chat later to bring its answer back into the main thread.
- Don't take: three ways to open the same thing (slash command, right-click, selection menu). Pick the selection menu.
- Answers: 4 (not seen in a browser)

---

## 5. WHERE SKILLS, AGENTS AND STANDARDS LIVE

### 5.1 Claude desktop: one "Customize" entry in the sidebar
- URL: https://code.claude.com/docs/en/desktop (section on skills, plugins and connectors) and https://claude.com/product/claude-code (sidebar: New, Projects, Artifacts, Customize, More)
- Take: everything the agent can use (connectors, skills, plugins) is managed from one sidebar entry, **Customize**, and the same set is shared by every session and synced across devices. In the chat, the **+** button reaches the same lists, so adding a tool never means leaving the conversation.
- Don't take: the split where house rules (CLAUDE.md) live only as files. He needs rules on the same page as skills.
- Answers: 5 (not seen in a browser)

### 5.2 Superwhisper: "Modes" as a plain form for how an assistant behaves
- URL: https://superwhisper.com/ (the Modes screen shown on the page)
- Take: a left list (Home, Modes, Vocabulary, Configuration). Each mode is a small form: **Preset**, **Language**, **Activate when using** with **+ Add App**, and **Advanced settings** hiding the model choice. **Custom Mode** ("Build it yourself") adds his own rules. This is a non-technical way to edit an agent definition: defaults first, rules second, models last.
- Take: **Push to talk** (hold, speak, release) as the dictation start. Useful for 1.4.
- Don't take: the per-app trigger as is. In his app, "Activate when" maps to an area or a workflow, not an app.
- Answers: 5 (also 1) (not seen in a browser)

---

## The input, part by part

| Part | Best example seen | Why it is the best |
|---|---|---|
| Text area | Claude Code desktop (1.1) | Only text and Send inside the box; a grey suggested prompt on empty that Tab accepts. Everything else sits under it. |
| Attach | Claude Code desktop (1.1) | One **+** holds files, photos, folders, connectors and commands; drag and drop also works. |
| @ (point at a thing) | Claude Code desktop (1.1), Cursor side chat (4.2) | `@` plus a name; Cursor also lets you @ a side chat to pull its answer back. |
| "/" menu | Claude Code desktop (1.1) | One list for built-in commands, skills and plugin commands together. |
| Model | Claude Code desktop (1.1) | One chip with a shortcut; effort lives inside the same picker. (Shortlist 5.3, Raycast's spec card, is still the best hover detail.) |
| Effort | Claude Code desktop (1.1) | A section inside the model picker, not a separate chip. |
| Access mode | Codex in ChatGPT (1.5) | Three choices, each one plain sentence; expert options hidden. |
| Send / stop | Claude Code desktop (1.1) | Send turns to stop while running; Esc also stops. |
| Queue / steer | Cursor (1.2) | Queued messages are visible under the running task, reorderable, each with **Send now**. One setting picks the default. |
| Meter | VS Code (1.6) | Opens to a breakdown and the spend, with **Compact Conversation** right there. Claude's usage ring is the smaller form. |
| Voice | Cursor (1.3) for placement, Wispr Flow (1.4) for quality | Voice takes the Send slot only when idle and empty; dictation is cleaned of fillers and mid-sentence corrections before it lands. |

Not found anywhere: **drafts kept per chat** as a stated feature. No product page claimed it. Treat it as ours to design.

## Patterns that repeated

- The box holds text and Send; every other control is a chip in one row under it.
- Access mode is always under the composer, never in settings. The best versions have three choices with a one-line meaning.
- While the agent works, a new message is queued by default and shown in a visible list, with a way to push it in now.
- Tool work folds into readable sentences ("Read 3 files", "Ran 2 commands"); the full log is one switch away.
- One list for every agent, grouped by project, filtered to Active by default, with Done one click away.
- A parent stays "working" while any child works; the inbox speaks only for permission, a plan to review, or done.
- Side chats for quick questions, opened from a selection, so the main run is never interrupted.
- Voice is now a first-class input: dictation in the box plus a live voice call in the Send slot.

## Dead ends

- **The built-in browser could not show any page as a picture.** Its pane was hidden for the whole run, so screenshots and heavy text reads timed out. Antigravity's landing page and the Cursor changelog never rendered there. Everything here needs a visual check.
- OpenAI's Codex landing page (openai.com/codex) returned "forbidden". Several Codex doc pages (skills and plugins, the composer) returned "not found" after the docs moved to learn.chatgpt.com; only the permission modes page loaded.
- Antigravity's own docs page for the Agent Manager returned "not found"; details in 2.2 come from Google's launch post and third-party guides.
- Notion AI, Perplexity Comet, Manus and Raycast AI landing pages describe the chat input in marketing words only; no control labels. Notion and Comet point to help centres instead.
- Zed's AI page (read in the browser as text) and GitHub's Agent HQ announcement describe agents in general terms with no input or panel detail.
- Warp's universal-input docs page returned "not found".
