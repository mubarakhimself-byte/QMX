# 31: Cua (cua.ai): what it does, and what it changes for QMX

Read by the lead on 2026-10-16. Sources: the landing page in the built-in browser; docs pages through firecrawl, because the hidden pane would not render the client-side docs.
- https://cua.ai/docs/cua-driver
- …/concepts/how-cua-driver-works
- …/concepts/platform-support
- …/guides/browsers
- …/guides/permissions
- …/guides/vms-and-remote
- …/start-here/sandbox-images
- …/spaces/examples/cua-bots

Earlier QMX work knew only **OpenCUA**, the model that was dropped on 10-13. Cua (trycua) is a different and much larger thing. It is computer-use **infrastructure**, not a model.

## What it is

| Piece | What it does | Licence |
|---|---|---|
| **Cua Driver** | Lets any agent drive native apps on Windows, macOS and Linux **in the background**. It reads each window's accessibility tree plus a screenshot, then clicks, types and scrolls without taking the human's cursor or focus. The agent gets its own cursor overlay. Connects through **MCP** (Claude Code, Codex, any MCP agent), a CLI, or a Python/TS SDK. | MIT |
| **Browser tools** (inside the Driver) | Drives Chrome and Edge tabs over CDP, bound to an exact window, in the background, including inactive tabs. It can **attach to a logged-in Chrome/Edge profile** by turning on Chrome's own remote-debugging consent (Chrome 144+ auto-connect), and it never copies or edits the profile. Isolated profiles (temporary or named) are also available. Origin allow-lists. | MIT |
| **Permissions** | Every call passes a layered check that the agent cannot widen: hard invariants → tool risk map → admin policy → user policy → mode → capability manifest → launch grant. **Bounded mode** is deny-by-default with a YAML manifest (apps, file roots, browser origins, expiry, idle timeout). There are also Rego/YAML tool policies and `revoke`. | MIT |
| **Sandboxes** | Published desktop images (Linux containers and VMs, **Windows Server 2022 VM**, macOS VMs) with the driver preinstalled; `cua sb create`. Fleets (pools and claims) for hosted desktops. They run on your own machines or in your cloud. | mixed |
| **Spaces** | Shared desktops where you and each agent get **your own cursor**. You can watch, take over and hand back. "Teleport" moves an app's signed-in session into a Space. A Windows client is in preview. | FSL-1.1-MIT (source-available, becomes MIT later); free tier |
| **Cua Bots** (example app) | Persistent bots, each with its own computer, memory folder, routines (schedules), approvals and rules ("rules about passwords and money can't be changed"), plus phone approvals. The driving agent is Hermes, OpenClaw, Codex or Claude Code. | FSL (sample) |
| **Cua Bench** | Scores computer-use agents on real desktops; you can write your own tasks. | — |

According to its own page, it is used by Meta (computer-use cookbook), Factory and Kimi Code.

## What it changes for QMX

1. **Computer use is back on the table, and model-agnostic.**
   - B17 and B17a held computer use because no subscription route had it (it isn't in the Claude Agent SDK) and because permissions, concurrency and compute weren't designed.
   - Cua Driver is an MCP tool, so **any** model in our harness can drive desktop apps through it.
   - Its permission stack (bounded manifest, origins, expiry, revoke) answers most of the "permission hierarchy" condition.
   - Concurrency is explicit: one native input at a time per desktop, while browser tools work per tab in the background.
   - Compute comes from Cua sandboxes or Spaces.
2. **The open browser question from 14 and 18 has a better answer.** We concluded that the everyday Chrome profile can't be driven, so the plan was a separate "QMX Browser" profile. Cua attaches to the **real logged-in profile** through Chrome's own consent switch, behind an explicit grant. Our plan still stands as the safer default (B3); this becomes the "act as me" option (B4), with a bounded manifest and origin list.
3. **cTrader / MT5 / TradingView desktop.** Windows support covers UI Automation, WPF, WinUI 3, Electron and WebView2. "Use MT5 instead of rebuilding" (his example) becomes possible on demo accounts. **Unverified:** whether cTrader's and MT5's controls are exposed well enough. Elevated-integrity apps refuse. It needs a probe on his PC.
4. **It fits "harness outside the sandbox"** (the Rivet principle adopted tonight). The driver runs on the target desktop (PC, VM or Space) as the tool executor, and the agent loop stays in our engine and harness. Remote reach is MCP over SSH, or the daemon socket.
5. **Windows sandboxes on his server:** the `windows:2022` VM image means a disposable Windows desktop with MT5/cTrader for agents, which needs KVM on the server. This links to study 29's open question about server specs.
6. **Mental-model match:** Cua Bots is close to his "agents with their own computer, memory, routines, rules, phone approvals" picture. Its own limits list notes that the rules are instructions, not enforcement; ours are hooks and the money gate.

## Cautions

- The Windows daemon must run in the interactive user session (Session 0 over SSH sees no desktop).
- The Spaces Windows client is a preview. Spaces and Bots are source-available (FSL), not MIT. The Driver itself is MIT.
- Logged-in-profile attachment exposes that profile's cookies to anything that can reach the loopback endpoint as the same user. Use it only behind a bounded manifest, on a trusted machine.
- Money stays read-only: the money gate must also cover Cua actions on broker and platform windows (an origin and app deny-list in the manifest, plus our harness hook).

## Recommendation

- Adopt **Cua Driver as QMX's computer-use and "act-as-me" browser tool layer** (MCP, MIT).
- Keep Playwright/Stagehand for headless, logged-out web research and cheap replays.
- Run two probes before any design commits:
  - (a) cTrader and MT5 on his PC, in background mode;
  - (b) attaching to his real Chrome profile for YouTube/TradingView reads.
- Fold it into the browser and computer-use plan that is owed to him (ruling 30), and into the environments design (study 29) for Windows sandboxes.
