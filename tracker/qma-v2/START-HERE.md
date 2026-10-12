# Start here (Tuesday 2026-10-13)

Good morning. The planning and the architecture finished overnight. No code was written.

The order today:
1. Answer the questions below.
2. Claude starts the shipping orchestrator session.
3. You do the short homework while the first packets build.

## 1. What's ready (all in `tracker/qma-v2/`, branch `plan/agent-system`)

| File | What it is |
|---|---|
| `PRD.md` | What QMA v2 must do: 148 requirements, 81 of them for Wednesday. Merged from both transcripts and the mini-apps transcript. |
| `USER-JOURNEYS.md` | 21 journeys through QMX, 25 new ideas of mine (for your review), and a 10-minute Wednesday demo script. |
| `HOW-WHY.md` | What today's code does and why, re-run four times as new inputs arrived (your re-run rule). |
| `ARCHITECTURE.md` | The design. Two candidates (A "SDK-native", B "QMA-owned core") were combined, checked against every requirement, attacked by two reviewers, and revised three times. Section 0 is the plain-words card. |
| `ARCHITECTURE-CHECK.md`, `reviews/` | The coverage check and the two hostile reviews, with every finding logged as fixed or not in ARCHITECTURE §10. |
| `SHIPPING-PLAN.md` | 15 PRs in order. Each has a runnable "done when" check, its docs, its budget and a fallback. |
| `ORCHESTRATOR-PROMPT.md` | The prompt for the fresh shipping session, which coordinates and never codes. |
| `BACKLOG.md` | Everything outside the first build. Easy wins are marked. |
| `FILE-INDEX.md` | Which earlier files still matter. 35 superseded files are now in `archive/` folders, stamped. |

Research behind it is in `tracker/agent-system/research/`:
- 30: databases
- 31: tools, skills, prompts, agent communication
- 32: the DevOps lens and the UI protocol
- 19: the two SDKs
- 21: mini-app seeds
- 22: cookbooks
- 26 and 27: your requirements, pulled from the transcripts

## 2. Questions to answer first

These are your decisions, each with my recommendation. A one-word answer is enough. They're also in ARCHITECTURE §6.2.

**Most important for Wednesday**
- **Q9.** On Wednesday, do I prove the six points on a plain console page with a few buttons (A), or do you click through the real UI (B)? *Recommend A.* The real UI gets wired from a handoff packet afterwards; B puts it on the critical path.
- **Q10.** May QMX create a second, low-rights Windows user on your PC, run agent shells as that user, and limit that user's internet access to an allowlist? This is process separation, not a sandbox. *Recommend yes.* Without it, an agent that writes its own code could read your stored broker and signing keys.
- **Q11.** Which rented provider for Wednesday's off-machine run, Modal or E2B? You fund it and set a spend cap in its dashboard. *Recommend Modal, with a small cap.*
- **Q13.** On Wednesday, remote agent steps run on DeepSeek or GLM, not Claude, because Claude on rented machines is unverified. OK? *Recommend yes.*
- **Q14.** If time runs out, drop in this order:
  1. the Macro app rebuild;
  2. the live remote run (it becomes a fake-provider run with an honest card);
  3. extra helpers.
  
  Never drop the copilot, the seats or the money refusal. Agreed? *Recommend yes.*

**Rules for the agents**
- **Q1.** Which actions must always ask you first? *Recommend: publish, install, schedule, spend over budget, demo-account actions, delete.*
- **Q2.** The one rule every copilot must remember about how you work? *Recommend:* "Answer research questions yourself; ask me only real decisions, with a recommendation, after I've read."
- **Q3.** A "think harder" switch beside the chat box? *Recommend no:* automatic per role, with a per-chat override.
- **Q4.** One general copilot that lists every session, with Lab and Portfolio as plugins it loads? *Recommend yes.*
- **Q5.** If ChatGPT sign-in can't drive QMX, GPT shows "unavailable" and its roles go to Claude or a key provider, never a paid OpenAI key. OK? *Recommend yes.*
- **Q6.** Which broker accounts may agents touch for testing? *Recommend:* demo under approval, live read-only, never an order.
- **Q15.** The refusal demo: gold CFD or a crypto pair? *Your current instrument ruling decides.*
- **R1.** Claude's built-in tools (Bash, Write, Edit) are checked by a hook before and after each call, rather than by QMX's own tool wrapper. *Recommend yes.* No would mean switching them off, which loses most of Claude Code.
- **R2.** On the usage page, Claude usage QMX can't measure exactly is marked "estimate". *Recommend yes.*

**Housekeeping**
- **Q8.** The Library's real name (you said it starts with "A") and QMF's role. *Recommend:* keep "Library" for now; QMF is a tool seam.
- **Q12.** May packet 0 touch the Library's database connection code to apply the single-writer safety rule? *Recommend no for now.* The Library is out of scope.
- **D1.** The weekly backup would now include chats and approvals (`control.db`) in the private GitHub repo. OK, or bucket only? *Recommend bucket only.*
- **D2.** P16c finished. All 13 PRs are merged, and the old runtime is down from 127,703 to 113,347 lines. The rest is kept alive by one QMB line that starts the old daemon. DESIGN §12c.1 already allows removing those old QMB helper functions. May a later packet do it, after the QMB review? *Recommend yes, later* (backlog B7).
- **D3.** Where is your own backlog? It wasn't found in the repo, only `queue/TEMPLATE.md`.
- **Later, not today:** read my 25 ideas in `USER-JOURNEYS.md` §3 and mark the ones you want.

## 3. Your homework (about 15 minutes, any time before Tuesday 18:00)

`scripts/operator_setup.py` is built in an early packet. Until then, the orchestrator walks you through these steps:
1. Sign in to Claude once inside QMX's own Claude home (not your personal one). QMX never sees the token.
2. Paste one DeepSeek or GLM API key into the hidden field. It goes straight to Windows Credential Manager.
3. Add the rented-provider token (Modal or E2B), its price per minute, and set a spend cap in its dashboard.
4. ChatGPT sign-in (optional; the probe decides whether GPT works).
5. If Q10 is yes, the script creates the low-rights `qmx-agent` user.
6. The Portfolio seat switch for the demo.

If the GitHub Actions cause turns out to need an account or billing click, that click is yours too.

## 4. Then shipping starts

When you've answered, say "go".
- Claude starts a fresh orchestrator session from `ORCHESTRATOR-PROMPT.md`, through a one-off scheduled task (tested last night). It turns on Remote Control so you can approve from your phone.
- The orchestrator never codes. It sends one builder agent per packet, checks every PR itself, and merges into `rebuild/base`. It never touches `main`, and it keeps the docs current as it goes.
- **First up (easy wins), packet 0, three PRs in parallel:**
  - **0a:** create `qma2`, pin both SDKs, record the SQLite exposure, retire the old agent cores.
  - **0b:** the qmx-tools single-writer fix.
  - **0c:** the probes (ChatGPT sign-in, approvals, Claude hangs), the GitHub Actions mystery, and the cTrader and Firecrawl notes.
- **Then 1a:** the store and its tables. **Then 1b:** a copilot turn working end to end through the API, with the console.

The timetable, the Wednesday 06:00 dry run and the 09:00 freeze are in `SHIPPING-PLAN.md`.
