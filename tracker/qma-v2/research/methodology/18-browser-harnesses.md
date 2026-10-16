> STATUS 2026-10-16 (rubric walk): KEEP-AS-SOURCE. See 27-rubric-walk.md. Rulings in 26 win.

# 18. Browser harnesses: Browserbase and the others

Date: 2026-10-16. Follows study 14 (`14-folders-miniapps-browser.md`, section 3).

Sources were read in a normal browser, page by page. Facts marked UNVERIFIED were not confirmed on a primary page.
Prices are as shown on each vendor's pricing page today.

## Short answer

- Browserbase is good, but it is a **cloud-only** service. It cannot run on his PC. His logins would live on their
  servers. It does solve "watch the agent live in a pane": it gives an embeddable live-view link with take-over.
- The useful part for QMX is **Stagehand**, Browserbase's open-source (MIT) library. It runs on a local Chrome too,
  works with many model providers, and has a **local action cache**: a rerun replays saved steps with no model calls.
- **Study 14's plan stands.** Keep the QMX Browser profile, the broker, leases and B0 to B4. Add three things:
  Stagehand as an optional "replay" layer for workflows, a CDP screencast pane for watching, and a cloud browser
  (Steel, Kernel or Browserbase) only as an opt-in backend for B1/B2 isolated work later.

## Comparison table

"Live view" means a stream a human can watch inside another app. "Take over" means the human can click and type in it.

| Tool | Open source? Licence | Runs on Windows / Linux | Live view + take over | Logged-in profile | Many sessions (sub-agents) | Action cache / replay | Model-agnostic | Cost |
|---|---|---|---|---|---|---|---|---|
| **Browserbase** (cloud browsers) | No | Cloud only. No on-prem | Yes. Embeddable iframe, read-only or read/write, one URL per tab | "Contexts": encrypted saved user-data dir on their servers; you log in once via live view | Yes. 3 (free) to 100+ concurrent | Server cache with Stagehand (`cache: true`) | Yes, via Stagehand | Free: 1 browser-hour, 3 concurrent, 15 min sessions. $20/mo: 100 h then $0.12/h. $99/mo: 500 h then $0.10/h |
| **Stagehand** (library) | Yes, MIT | Windows, Linux, macOS (needs local Chrome) | No viewer of its own. Headed window locally | `userDataDir` on a local Chrome | One instance per browser; run many | **Yes. Local `cacheDir`** replays act() and agent() steps with no LLM calls | Yes. OpenAI, Anthropic, Google, Ollama, Groq, Mistral, any Vercel AI SDK model, custom `baseURL` | Free (pay your own model) |
| **Browserbase MCP server** | Repo archived 2026-07-20 (was Apache-2.0). Hosted MCP lives on | Hosted, or old npm package | Through Browserbase | `--contextId` | Through Browserbase | Through Stagehand | Default Gemini; `--modelName` | Browserbase usage |
| **Director** | No | Web | Through Browserbase | Through Browserbase | - | - | - | director.ai now redirects to Browserbase "Agents" API |
| **browser-use** (library) | Yes, MIT | Windows, Linux, macOS (Python) | Headed window locally | Local Chrome profile or remote CDP | One agent per browser | "Rerunnable scripts" in Cloud | Yes, any LLM | Free + your model |
| **Browser Use Cloud** | No | Cloud | Yes. Live preview, human-in-the-loop take-over, recording (off by default) | Profiles; `profile.sh` syncs local cookies up to cloud | Yes | Rerunnable scripts | Own BU models or others | From $0.02 per browser-hour; $15 signup credit |
| **Browser Harness** (browser-use) | Yes, MIT | Windows, Linux, macOS | His real Chrome window | **Attaches to his real running Chrome** via chrome://inspect | One browser | Agent writes reusable helpers | Works with Claude Code, Codex, Cursor | Free |
| **Steel** | Yes, Apache-2.0 (steel-browser) + paid cloud | Docker or Node; Windows Chrome path supported | Yes. Cloud: WebRTC 25 fps iframe, `interactive=true/false`. Debug URLs are unauthenticated | Session state, cookies, local storage | Cloud: 10 (free) to 1,000+ | No | N/A (browser API) | Self-host free. Cloud: $30 one-time credit, $0.10/h, $250/mo plan |
| **Hyperbrowser** | Cloud closed. HyperAgent library AGPL-3.0 | Cloud; HyperAgent local | Yes (cloud) UNVERIFIED detail | Cloud profiles UNVERIFIED | Free: 1 concurrent; $30: 25 | **HyperAgent: action cache + `runFromActionCache()`** (XPath replay, LLM only on change) | Yes | Free 5,000 credits (~50 h). $0.10/h |
| **Anchor Browser** | No | Cloud; "bring your own cloud / on-prem" only on Enterprise | Yes ("embedded browser agent") | "OmniConnect" managed auth; logged-in browsers from $50 plan | Free: 5 concurrent | "Web Action Cache" (deterministic code) | "Your own inference provider" (BYOC) | Free 5 credits/mo; $50, $500, $2,000/mo |
| **Kernel** | Browser images Apache-2.0 (`kernel/kernel-images`) + paid cloud | Docker / unikernel (Linux). Cloud | **Yes. noVNC or WebRTC live view, read-only option, video replays** | Managed auth, vaults; unikernel snapshot keeps cookies | Free: 5 concurrent | No | N/A (browser API) | Free $5/mo credit, 5 concurrent, live view; $30/mo; $200/mo |
| **Skyvern** | Yes, AGPL-3.0 + cloud | Windows (needs Rust + C++ tools), Linux, Docker | Livestream of the viewport | **`BROWSER_TYPE=cdp-connect`** to your own Chrome; Bitwarden/1Password logins | Cloud runs many | No-code workflows; caching UNVERIFIED | Yes. OpenAI, Anthropic, Gemini, Bedrock, Ollama, OpenRouter | Free self-host + model |
| **Playwright MCP** | Yes, Apache-2.0 | Windows, Linux, macOS | Headed window. No embed | `--user-data-dir`, `--cdp-endpoint`, `--extension` to his tabs | One per profile; `--isolated` or distinct `--user-data-dir` for parallel | **`--codegen`** writes Playwright code for each action (replayable script) | Any MCP client | Free |
| **Chrome DevTools MCP** | Yes (Google) | Windows, Linux, macOS | Headed window | `--autoConnect` to his running Chrome (approve dialog) | Page-id routing on one server | No | Any MCP client | Free |
| **neko** (viewer, not a harness) | Yes, Apache-2.0 | Docker (Linux) | **Yes. WebRTC virtual browser, many viewers, control hand-off** | Its own profile | One browser per container | No | N/A | Free |

## 1. Browserbase

Pages: https://www.browserbase.com/pricing, https://docs.browserbase.com/platform/browser/observability/session-live-view,
https://docs.browserbase.com/platform/browser/core-features/contexts, https://docs.browserbase.com/platform/identity/overview

- **What it is:** a fleet of hosted Chrome browsers you drive with Playwright, Puppeteer, Selenium or Stagehand.
  Also Search, Fetch, a "Model Gateway" (one bill for model tokens) and a hosted "Agents" API.
- **Live view:** `sessions.debug(id)` returns a fullscreen URL. Put it in an iframe. Read-only is done with
  `pointer-events: none`; read/write lets the human click and type. Each tab has its own live-view URL. The iframe
  posts `browserbase-disconnected` when the session ends. Uses listed include "human in the loop" and "delegate
  credentials", meaning the human types the password, not the agent.
- **Recording:** session replay of finished sessions. Retention 7 days (free) or 30 days (paid).
- **Contexts (persistent login):** a saved user-data dir, encrypted at rest, on their servers. Flow: create context,
  start a session with `persist: true`, log in through the live view, end the session, reuse the context later.
  Contexts never expire, but sites can log you out. Their own advice: one context per site per login, and do not run
  two sessions on the same context at once. This matches study 14's "one controller on the logged-in profile".
- **Stealth and CAPTCHA:** free plan has no CAPTCHA solving and no stealth. Developer and Startup plans have "basic"
  stealth and auto CAPTCHA solving. "Verified" (a special Chromium with real fingerprints) is Scale-plan only.
  Non-verified sessions always run on Linux. They also push "Web Bot Auth" (signed bot identity). For QMX: CAPTCHA
  solving on YouTube or TradingView as him is a bad idea anyway. Our rule stays: stop and ask him.
- **Pricing:** Free $0 (1 browser-hour, 3 concurrent, 15-minute sessions). Developer $20/mo (100 h, then $0.12/h,
  25 concurrent). Startup $99/mo (500 h, then $0.10/h, 100 concurrent). Scale is custom.
- **Self-host:** no. The FAQ says "we don't offer on-prem deployment". Private cloud and VPC only for enterprise.
- **Fit for QMX:** strong for watching and for parallel isolated work. Weak for "browse as him": his YouTube and
  TradingView cookies would sit on a US cloud, and the session IP would be a datacenter in Linux, which Google may
  challenge. Also a monthly bill. Use only as an opt-in backend.

### Stagehand

Pages: https://github.com/browserbase/stagehand, https://docs.stagehand.dev/v3/best-practices/caching,
https://docs.stagehand.dev/v3/configuration/models, https://docs.stagehand.dev/v3/configuration/browser

- MIT licence, TypeScript, Python and Go. 25.7k stars.
- Four AI calls: `act` (do one thing in plain words), `extract` (pull data into a schema), `observe` (find elements and
  return real selectors), `agent` (multi-step task, DOM or computer-use mode). Plus normal Playwright-style `page`
  and `locator` calls.
- **Runs locally.** `localBrowser.launch({ userDataDir })` or `env: "LOCAL"` with `headless: false` shows a real window.
  The README example keeps cookies in `./browser-data` so the next run is still signed in.
- `observe` returns selectors, so passwords can be filled by code and never reach the model.
- **Model-agnostic:** first-class OpenAI, Anthropic, Google, Vertex, Azure, Cerebras, DeepSeek, Groq, Mistral,
  **Ollama**, Perplexity, Together, xAI; Bedrock, Cohere and any Vercel AI SDK model; custom `baseURL`. The Model
  Gateway and `model: "auto"` need Browserbase and do not work locally.
- **Caching (the key feature for QMX workflows):**
  - *Browserbase cache*: server-side, on by default on Browserbase. Cache key = instruction + page content + options.
    A HIT costs no tokens.
  - *Local cache*: set `cacheDir`. The first run saves every `act()` and `agent()` step to files. Later runs replay
    them "with no LLM calls, no token cost". Works in LOCAL mode. Files can be committed and shared. If the page
    changes, it misses and calls the model again.
- Attaching Stagehand to an already-running Chrome by CDP URL is likely supported in v3 but was not confirmed on the
  page read. UNVERIFIED.

### Director

- director.ai now redirects to https://www.browserbase.com/agents. It is the hosted "Agents" API: one HTTP call with
  a task, Browserbase runs Stagehand in its cloud. Not useful to QMX, which has its own agents.

### Browserbase MCP server

- https://github.com/browserbase/mcp-server-browserbase is **archived (2026-07-20)**. Tools were start, end,
  navigate, act, observe, extract. The hosted one is `https://mcp.browserbase.com/mcp`. Cloud only. Not a fit.

## 2. Other harnesses

### browser-use, Browser Use Cloud and Browser Harness

Pages: https://github.com/browser-use/browser-use, https://github.com/browser-use/browser-harness,
https://docs.browser-use.com/cloud/guides/profile-sync

- **browser-use** (MIT, 118k stars): a full Python agent loop. Any LLM. Local Chrome or remote CDP. It is a whole
  agent, so it overlaps with QMX's own copilot. They also ship a driver for Anthropic's browser toolset.
- **Browser Use Cloud:** stealth browsers from $0.02 per browser-hour, CAPTCHA solving, proxies, live preview,
  human-in-the-loop take-over, recordings (off by default), profiles, and "rerunnable scripts" for repeated tasks.
  Cookie sync uses a `curl ... | sh` helper that uploads chosen local logins. Their own note: sync does not guarantee
  the site accepts a moved login.
- **Browser Harness** (MIT, 18.5k stars): lets Claude Code, Codex or Cursor drive **his real Chrome, logged in as
  him**. It asks him to tick the box at `chrome://inspect/#remote-debugging` (the Chrome 144+ path from study 14).
  Has an MCP server (`browser-harness-mcp`). This is the same as Chrome DevTools MCP `--autoConnect`: fine for a
  one-off "look at what I see", wrong for unattended work, because it reaches every window of his main profile.

### Steel

Pages: https://github.com/steel-dev/steel-browser, https://steel.dev/pricing,
https://docs.steel.dev/overview/sessions-api/embed-sessions/live-sessions

- Apache-2.0 browser API: sessions, cookies and local storage, proxies, extensions, stealth plugins, a debug UI,
  markdown/screenshot/PDF tools. Self-host with one Docker command; or Node with Chrome installed (Windows Chrome path
  is listed).
- Cloud live view: WebRTC 25 fps, embed by iframe, `interactive=true` for take-over or `false` for watch-only.
  Warning in the docs: debug URLs are **unauthenticated**. Anyone with the link can watch and control.
- Cloud pricing: $30 one-time credit, $0.10 per browser-hour, 10 concurrent, 15-minute sessions on the free tier.
- Whether the self-hosted build gives the same embeddable live view and many sessions was not confirmed. UNVERIFIED.

### Hyperbrowser and HyperAgent

Pages: https://www.hyperbrowser.ai/pricing, https://github.com/hyperbrowserai/HyperAgent

- Cloud browsers, sandboxes, fetch and agents. Free 5,000 credits (about 50 browser-hours), 1 concurrent session.
  $0.10 per browser-hour.
- **HyperAgent** (AGPL-3.0, changed from an earlier licence): Playwright plus AI (`page.perform`, `page.ai`,
  `page.extract`). Has **action caching**: a run records steps with XPaths; `runFromActionCache()` replays them with
  no LLM calls and falls back to the model only if the page changed. AGPL is a problem if QMX ever ships to others.

### Anchor Browser

Page: https://anchorbrowser.io (pricing section)

- Closed, cloud. Selling points: "OmniConnect" managed authentication, a "Web Action Cache" (agents plan once, then
  run deterministic code), Cloudflare-verified agents, embedded browser agent. On-prem and "bring your own cloud"
  only on Enterprise. Free 5 credits a month and 5 concurrent browsers; logged-in browsers start at $50/mo.

### Kernel

Pages: https://github.com/kernel/kernel-images, https://www.kernel.sh/pricing

- Browser images are Apache-2.0: headful Chromium in Docker or a Unikraft unikernel, CDP for Playwright/Puppeteer,
  **live view by noVNC or WebRTC (neko)**, read-only option, and video replays. The unikernel can sleep and restore
  the exact state, cookies included.
- The repo warns that a deployed live-view URL is public. Same lesson as Steel: QMX must put its own auth in front.
- Cloud: free plan with $5 a month credit, 5 concurrent, live view, stealth, managed auth, 1-day replays. $30 and
  $200 plans. Billed per GB-second, no charge while idle.

### Skyvern

Page: https://github.com/Skyvern-AI/skyvern

- AGPL-3.0. Vision-LLM agent with a no-code workflow builder and a Playwright-compatible SDK (`page.act`,
  `page.extract`, `page.agent.login` with Bitwarden or 1Password).
- Can **connect to your own Chrome** with `BROWSER_TYPE=cdp-connect`. Livestreams the viewport.
- Windows install needs Rust and the VS C++ tools. Models: OpenAI, Anthropic, Gemini, Bedrock, Ollama, OpenRouter.
- It is a whole agent product with its own database and UI. Too heavy to embed in QMX.

### Playwright MCP vs Chrome DevTools MCP

Page: https://github.com/microsoft/playwright-mcp (Chrome DevTools MCP as in study 14 §3.4)

- **Playwright MCP** (Apache-2.0): accessibility-tree snapshots, `--cdp-endpoint` to QMX's Chrome, `--user-data-dir`,
  `--isolated` + `--storage-state` for throwaway sessions, `--extension` to attach to his tabs, `--secrets` file,
  and **`--codegen`** (TypeScript, Python, Java, C#), which prints real Playwright code for each action. That code
  is a free, deterministic "replay script". The README now says only one client per persistent profile; for
  parallel clients use `--isolated` or a separate `--user-data-dir`. Microsoft also now suggests "Playwright CLI +
  skills" for coding agents to save context.
- **Chrome DevTools MCP**: better for console, network and performance; `--autoConnect` to a running Chrome.
- Verdict unchanged from 14: Playwright MCP for the agent; DevTools MCP for debugging.

## 3. The two open items from study 14

### 3.1 Can his Windows Chrome profile be copied? (App-Bound Encryption)

Source: https://security.googleblog.com/2024/07/improving-security-of-chrome-cookies-on.html and
https://hermes-agent.nousresearch.com/docs/user-guide/features/browser

- Since **Chrome 127 on Windows**, cookies are encrypted with a key tied to Chrome's app identity. A privileged
  Chrome service checks who asks. Any other program (Python, a cookie reader, Playwright's bundled Chromium) **fails**
  to decrypt. Google says the key is bound strongly to **the machine**, so profiles that move to another PC break.
  Google plans to extend this to passwords and payment data.
- What this means:
  - Reading his cookies out of the profile with a script: **does not work, and should not be attempted.** It is
    exactly what infostealers do.
  - Copying his profile **to a server** or another PC: **does not work.**
  - Copying his profile **on the same PC** and opening the copy with the **real Chrome** (`chrome.exe`), with
    `Local State` copied too: this is what Hermes does now. Hermes documents Windows support with one condition:
    Chrome must be **fully closed**, tray process too, because Chrome locks the cookie database. It copies the
    databases with SQLite's backup API, launches the real browser binary "to keep OS-encrypted cookies decryptable",
    and re-syncs on each new session. It never closes his browser without asking.
  - We have not tested this on his PC. Treat it as **likely works, same machine only, Chrome closed first**.
- **Safe way to keep his logins (unchanged, now firmer):** the dedicated **QMX Browser** profile. He signs in to
  YouTube and TradingView there himself, once, by hand, with no automation attached. Chrome stores those cookies with
  its own encryption, on his PC. The agent uses that profile through the broker. Nothing is copied, nothing leaves the
  machine, his main profile, bank and email stay out of reach, and it works while his normal Chrome is open. A
  profile copy à la Hermes is a worse version of this: it needs Chrome closed and pulls in every site he is logged
  into.
- For a server later: logged-in work on a server means signing in again there (through a live view) or a cloud
  "context". That is a new decision for him, as 14 said.

### 3.2 Can an Agent SDK harness use Claude in Chrome?

Sources: https://code.claude.com/docs/en/chrome, https://code.claude.com/docs/en/agent-sdk/overview,
https://code.claude.com/docs/en/agent-sdk/typescript

- **No, not as a product feature.** Claude in Chrome needs a `/login` sign-in on a direct Anthropic plan. With an API
  key or a `setup-token` token, "Claude Code keeps Chrome integration off, even when you pass --chrome".
- The Agent SDK page says third-party apps may not offer claude.ai login unless approved, and should use API keys.
  The SDK reference lists no Chrome option. Passing `--chrome` through `extraArgs` under his own login might work on
  his machine, but it is UNVERIFIED and against the spirit of that rule. Do not build on it.
- So 14 stands: Claude in Chrome is for his own Claude Code sessions only.

### 3.3 Does any harness solve "watch the agent in a QMX pane"?

- **Yes, in the cloud:** Browserbase, Steel, Browser Use Cloud, Kernel and Anchor all give an embeddable live view
  with take-over. Browserbase and Steel both have a clean read-only vs control switch.
- **Yes, self-hosted on Linux:** Kernel's open images (noVNC or WebRTC via neko), neko itself, or Steel self-host.
- **On Windows now, nobody ships a ready pane.** The QMX Browser is a real window on his screen, so he can already
  watch it. To show it **inside** a QMX pane, the broker can stream it with Chrome's own CDP screencast
  (`Page.startScreencast` frames out, `Input.dispatchMouseEvent` / `dispatchKeyEvent` in). This is the same method
  Browserbase and Steel used for their older headless live views. It is a small piece of QMX code, no new product.
- Every vendor warns that live-view links are unauthenticated or public. QMX must serve the stream only on
  `127.0.0.1` and only to the QMX app.

## Does this change 14's recommendation?

**No, on the core. Yes, three additions.**

Why the core stays:

1. Logged-in browsing as him must stay on his PC. Every cloud option moves his YouTube and TradingView cookies to a
   vendor and to a datacenter IP. App-Bound Encryption also blocks moving them cleanly.
2. Browserbase, Anchor and Hyperbrowser cloud cannot self-host. Kernel and Steel can, but only on Linux/Docker.
3. Leases, one controller per tab, B0 to B4 and the take-over button are QMX policy. No harness provides them. The
   broker is still needed with any of them.
4. Claude in Chrome cannot be the product browser (3.2).
5. Free and open options cover Windows now: QMX Browser profile + Playwright MCP.

The three additions:

1. **Stagehand (MIT) as the replay layer for workflows.** A workflow runs once with the model, saves its steps to a
   `cacheDir` inside the workflow folder, and later runs replay them with no tokens. This fits his "rerun costs
   nothing" wish and the agent-as-folder layout (cache goes beside `fixtures/`). Playwright MCP `--codegen` output is
   the free fallback (a plain script). HyperAgent does the same but is AGPL, so skip it.
2. **A watch pane via CDP screencast** on Windows now, from the broker, read-only by default with a "take over"
   switch. On Linux later, use neko or Kernel's open image instead of plain noVNC: WebRTC is smoother and has
   control hand-off built in.
3. **A pluggable "cloud browser" backend** for B1/B2 isolated leases only (never B3/B4 by default): Steel self-host
   first (free, Apache-2.0), then Kernel or Browserbase if he wants paid scale. Same broker, same lease rules.

## Recommended stack

### Windows now (all free)

1. **QMX Browser**: a headed Chrome QMX starts with its own `--user-data-dir`, CDP on `127.0.0.1` only. He signs in to
   YouTube and TradingView there himself, once.
2. **QMX browser broker** (QMX code): leases, one controller per tab, B0 to B4, origin grants, queue, TTL, action log
   with screenshots, take-over always wins (as in 14).
3. **Playwright MCP** over `--cdp-endpoint` as the agent's tools. `--isolated` contexts for B1/B2 leases so
   sub-agents can run side by side. Chrome DevTools MCP for debugging.
4. **Watch pane**: CDP screencast from the broker into a QMX pane; read-only by default, take-over button.
5. **Stagehand (MIT), local mode**, for repeatable workflows: `act`/`extract` with any model QMX uses, `cacheDir`
   in the workflow folder so reruns cost no tokens.
6. Not used: Claude in Chrome in the product, profile copying, cookie syncing, CAPTCHA solvers on his accounts,
   Browser Harness or `--autoConnect` for unattended work.
7. One small test worth doing later, only if he wants it: Hermes-style profile copy on his PC with Chrome closed,
   to confirm cookies survive App-Bound Encryption. Not needed for the plan.

### Linux server later

1. Same broker, same Playwright MCP, same Stagehand cache files (they are portable).
2. Headed Chrome in Docker with a **WebRTC viewer**: neko (Apache-2.0) or Kernel's `kernel-images` (Apache-2.0,
   noVNC or WebRTC, replays). Or **Steel self-host** (Apache-2.0) if a session API is wanted. Put QMX auth in front;
   never expose raw live-view URLs.
3. Server workflows get B1/B2 isolated leases only. Any logged-in profile on a server is his explicit decision;
   he signs in there through the watch pane, never by copying cookies.
4. Paid, optional, for burst scale: Browserbase ($20/mo Developer, contexts, live view, replay), Kernel ($0 to $30,
   live view on free), Steel Cloud ($0.10/h), Browser Use Cloud ($0.02/h). All plug in as a broker backend.
