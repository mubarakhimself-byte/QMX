# Resume QMX UI/UX design here

**Latest steering: prepare the Grok research/full-application architecture handoff now; return here for focused review before the user's next pipeline stage.** Start with [the handoff entry](../../00-START-HERE.md) and its current-direction file. Grok gets broad research/agent freedom; no application implementation or full backend code review starts here. Svelte/TypeScript, shadcn-svelte and Svelte Flow are the working direction; neutral dark baseline; Qt out. BMAD UX is skipped; BMAD architecture remains usable.

Latest corrections: UI presence, execution location and run lifetime are independent, so capabilities may be visual, headless or mixed. Original storyboard layouts retain priority over later references. LSE's ML Studio UI is rejected: develop the original graph/code workspace with right copilot and node/detail expansion. LSE can inform capability coverage only. Dashboard kits are mental models, not requested dependencies. Add startup/splash/first-run/provider/CLI-proxy and terminal considerations. Paper trading applies only to relevant trading/risk behavior.

Study 03 remains rejected and withdrawn. [layout-fidelity-reset.md](layout-fidelity-reset.md) maps the assistant's departures back to original image/text evidence. Aesthetics remain undecided, but that rejection was not merely about colors.

## What must survive compaction
- The user already supplied distinct layouts. Main copilot has sessions/history, conversation and preview. Mini-app has app-specific top navigation, substantial widget canvas and optional right copilot. Do not impose a permanent secondary sidebar or one generic interior on all destinations.
- Shared global rail persists, including platform destinations, divider and opened apps. The selected application changes navigation and working composition.
- Widgets need meaningful charts/tables/controls and detailed expansions. Metadata descriptions and large explanatory banners are not acceptable substitutes. Keep study notes outside the product surface.
- Reopened original OpenBB and VS Code source images and re-read the full bottom dictation in this correction turn. Sources were sufficiently explicit; the failure was in applying them.
- Recent Codex screenshots inform preview/conversation controls, not a replacement app layout. Native Codex control is unavailable; plus menu remains unobserved.
- Library and authoring have greater room for design, not implicit approval. n8n is an explicit authoring reference lead.

## Current status
No corrected replacement mock or production frontend has been built. The current deliverable is a portable architecture-input packet: prompt, decisions, experience/component scope, original evidence, transcripts, BDD inventory and return-for-review criteria. Tauri remains a candidate, with no automatic performance promise. Preserve original intent without freezing every coordinate. Do not revive rejected study 03.

Five recent screenshots are preserved under experience-v03/references. The original storyboard extraction, all 18 web captures and all prototype revisions remain available. Study 02 tokens are rejected; study 03 is historical only. [session-visible-messages.md](session-visible-messages.md) now preserves every visible user/assistant message returned across all 15 turns at capture, including the latest user request; the active turn is partial after that point. Images are separate. No internal reasoning/tool logs are exported. [Session audit](handoff-working/session-audit.md) records full-read coverage.

The user reports Grok's other work may now be near coding; current stage and SDK implementation remain unverified. All application code belongs off main: backend integration and a separate UI integration branch, combined into a deployment candidate, then main after validation. Exact UI branch/base and CI are not established; no Git mutation occurred. A dedicated backend review can proceed separately in parallel later; this task did not start one. The latest supplied AGENTS instructions require Reticle proof for user-facing changes and supersede the earlier discretionary preference. No app implementation or runtime verdict; the earlier file-URL block was not bypassed.

The vision is an extensible capability-building platform; visual apps and headless operations use shared infrastructure. Explore/compose/test/reuse/operate; disposable experiments and non-trading ML are valid. Book/BMS are current default role implementations, not the only possible policy stack. Historical examples are not a mandatory backlog. Graph/code ML work, charting, diffs, monitoring, risk/portfolio and Library remain in scope. No paid dashboard assets.

Documentation Factory's design-packet intake and conventions were inspected, not invoked. Latest lower-cost agents audited the full visible session, inventoried BDD and selected staged skills. The BDD inventory found 85 scenario declarations in five canonical files, including one outline with four examples. These are marked specification-only; no tests ran. A narrow current scenario document SCN-0024 already addresses headless/optional-copilot intent, but expressly does not claim current code implements it. No tool installation or external design generation occurred. Use the new architecture handoff ZIP when available; the older design-session ZIP remains a historical checkpoint.

Tracking: canonical `.scratch/qmx-design-wayfinding/` at repository root; portable copy in wayfinding/. No ticket resolved. [Session log](session-log.md) is the chronology.
