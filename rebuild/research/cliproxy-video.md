# CLIProxyAPI: the video, how it works, and how QMX plugs into it

Sources: video "If you have a Claude sub, watch this" by Theo (t3.gg), 1:06:36, https://youtu.be/D8PikZ1KhUo.
I used the captions plus 30 frames at 1024px from 15:00 to 29:30, the part about the proxy.
Repo: https://github.com/router-for-me/CLIProxyAPI (latest release v8.0.17, 2026-10-07).
Docs: https://help.router-for.me. I also read the repo's `config.example.yaml`, `docs/management-api-v8.md`,
`internal/api/server_routes.go`, `server_middleware.go`, `cmd/server/main.go` and `internal/registry/models/models.json`.
I ignored sponsor and relay services.

Note: the proxy covers only about 15:00 to 29:00 of the video. The rest is about workflow: T3 Code,
treating threads as an inbox, remote Linux boxes.

---

## A. What the video shows, step by step

| Time | What is said / shown |
|---|---|
| 00:00-01:30 | Intro: "how many agent threads are running right now". Says that across 30+ Claude accounts in his circle, the only bans were 2 temporary ones (VPN plus a mismatched business card), both reinstated. |
| 01:30-02:50 | Sponsor segment (Parallel search). Skip. |
| 02:50-05:15 | Agenda: get more tokens, access them, use them well, use them "poorly", use them while asleep. |
| 05:15-11:00 | His subscription vs API economics (his own estimates). Codex resets happen often (he says about 14 in 30 days). |
| 11:00-11:30 | On screen in Codex: Settings > Data controls > "Improve the model for everyone" set to OFF. Says Claude Code has a similar setting. |
| 12:30-13:30 | Switching Claude Code auth by hand between 2 accounts works for 1-2 machines but does not scale. You need one system that manages auth for many accounts and machines. |
| 13:30-15:00 | His operational tips: do not sign Claude Code or Codex in from a VPS or datacenter IP. Route all traffic from ONE residential IP. Avoid the same account appearing from many machines at once. |
| 15:00-15:40 | Introduces CLIProxyAPI. You sign into it with your Codex and Claude OAuth. It keeps that auth refreshed and exposes an API. You point Claude Code or Codex at that API instead of the normal auth servers. |
| 17:30-18:00 | Dashboard on screen: **CPAMC, "CLI Proxy API Console"** (the official Management Center UI, restyled in his fork). He started from the VibeProxy fork and has forked it heavily. Says your dashboard "won't look anything like this", and suggests giving an agent this screenshot so it restyles yours. |
| 17:40 (frame) | URL `bb-1.porpoise-micro.ts.net:8318/management.html#/quota`, page **Quota Management**, "10 credentials · 10 loaded". Tabs: All 10, Claude 5, Antigravity 0, Codex 3, xAI 1, Kimi 1. Buttons: "Show emails", "Refresh", "Ledger" dropdown. |
| 17:40 (frame) | Summary cards. Claude, 5 credentials: "7-day Fable 5: 409% of 500%", next reset "in 1 day · 09/12 23:00", "7-day limit 454%". Codex, 3 credentials: "Weekly limit 17% of 300%". xAI: "--". Kimi: "100% of 100%". Percentages are REMAINING quota summed across accounts (100% per account). |
| 18:30 (frame) | One row per Claude credential. Auth file name `claude-<email>.json`, plan "Max". Three bars per row: "7-day Fable 5" (58% / 100% / 100% / 51% / 100%), "5-hour limit", "7-day limit". Each bar has a reset countdown and timestamp. Each row has a "Refresh quota" button. |
| 18:00-18:40 | Says the default routing spreads load evenly across accounts. He changed it to **prioritise the account whose reset comes soonest** so expiring quota gets used first. This is his first suggested change. |
| 19:00-19:30 | One 5-hour window on the 20x plan is about 40% of the 7-day model-specific bucket. He greys out the "Opus bucket" column. |
| 19:30-20:20 | Inserted later: with Opus 5.5 he rarely hits limits on one subscription, so "you might not even need" the proxy. |
| 20:30 (frame) | Codex rows: `codex-<id>@...-pro.json`, "Pro 20x · renews 10/03", "Weekly limit 17%". "Manual resets: 2 available" (banked resets), with "Reset quota" and "Refresh quota" buttons. |
| 20:30-20:50 | Second change: by default Codex OAuth traffic does NOT use WebSocket. Turning on the WebSocket transport "hugely increases performance". |
| 20:50-22:00 | **Session and account affinity**: keep a thread on the same account, because prompt caches are per account. Switching accounts mid-thread forces a cache rewrite. Says affinity "works very well by default", and you should watch cache read/write numbers. |
| 22:00-23:00 | URL detail: host `bb-1` (his desktop) on Tailscale tailnet `porpoise-micro.ts.net`, port **8318**, page `management.html`. He runs **with no client API key**. Adding one once "broke my inference on everything". He considers that fine because only his tailnet can reach the port. |
| 22:44 (frame) | **Config Panel** (`#/config`). Tabs: Common, Access & Authentication, Network Configuration, Logging & Diagnostics, Quota Fallback, Streaming. Common tab: Host Address `127.0.0.1`, Port `8318`, Proxy URL (socks5 placeholder), "API Keys List (api-keys): No API keys" with an "Add API Key" button. Toggles: Debug Mode off, Log to File on, Switch Project on, Switch to Preview Model on. |
| 23:00-24:00 | His private "fleet" repo, shown in VS Code: `VIBEPROXY.md`, `HOW_TO_SET_UP_A_BOX.md`, `COMPUTERS.md`, `complete-setup.sh`. The box runbook lists: Tailscale with MagicDNS, SSH, tmux, git/gh/rg/fd/jq/btop/Node/Bun/Python, Codex and Claude Code installed "and pointed at the proxy", `ccusage`. |
| 24:00-24:30 | New machine setup: he gives an agent the SSH key and repo. The agent configures everything and Tailscale asks him to approve the new device. |
| 24:30-25:00 | End state: one home machine on a residential IP carries 5 Claude and 4 Codex accounts. Every other machine reaches it over Tailscale. |
| 24:50-25:30 | Pointing Claude Code or Codex at the proxy means swapping "two variables" (base URL and key). This keeps working because both tools must support custom endpoints for Bedrock. The Codex desktop app shows the proxy "in the corner". |
| 25:30 | You can keep a normal install and add a second Claude Code or Codex instance with a different home directory configured for the proxy. |
| 25:45-26:15 | Through the proxy, Claude Code can use every model the proxy carries. **His operational warning**: use Claude-subscription models only inside Claude Code. He says using them in other clients gets accounts banned. |
| 26:15-28:30 | Reset semantics. A Codex reset restarts the whole weekly window, so the reset date moves out 7 days. Codex resets are "banked" (claim any time) or "immediate". A Claude reset refills the percentage only and keeps the date. |
| 41:45-42:30 | T3 Code (his app): a per-thread machine picker (Mac or Linux boxes). Repos are grouped by git origin. |
| 44:30 | T3 Code Settings, "Load balancing": spreads new threads across connected servers automatically. |
| 53:00-54:30 | T3 Code "works incredibly with CLI proxy". Setup on a box: `npx t3 connect` (through their relay) or `npx t3 serve` with a built-in `--tailscale` flag (direct). The box only needs Claude/Codex "ideally with a sub or a proxy". |
| 59:00-60:00 | Recommends a cheap home Linux box: Ubuntu, Tailscale, CLIProxyAPI on it "so it's always coming from your residential IP". Against renting a VPS for this. |

How T3 Code reaches the proxy: indirectly. T3 Code drives the Claude Code and Codex CLIs on each box, and
those CLIs are configured with the proxy base URL. No T3 Code proxy setting is shown on screen.

---

## B. How CLIProxyAPI works

**What it is.** A Go server. Each upstream login (OAuth) is stored as a JSON file in `auth-dir`
(default `~/.cli-proxy-api`). The server refreshes those tokens itself. It then serves OpenAI-, Claude-,
Gemini- and Codex-compatible APIs and translates between the formats, so any model can be called
through any of those APIs. License: MIT. The config file and `auth-dir` hot-reload, so you can add or
remove token files while it runs (help.router-for.me/configuration/hot-reloading).

**Install**
- Windows: download `CLIProxyAPI_<ver>_windows_amd64.zip` from GitHub Releases and run it. A desktop
  GUI also exists: EasyCLIProxyAPI or EasyCLI, with tray, auto-update and start/stop (quick-start page).
- Linux: one-line installer
  `curl -fsSL https://raw.githubusercontent.com/router-for-me/cliproxyapi-installer/refs/heads/master/cliproxyapi-installer | bash`.
  On Arch, use AUR `cli-proxy-api-bin` with a systemd user unit. Or build: `go build -o cli-proxy-api ./cmd/server`.
- macOS: `brew install cliproxyapi && brew services start cliproxyapi`.
- Docker: image `eceasy/cli-proxy-api:latest`. Mount `config.yaml` at `/CLIProxyAPI/config.yaml`,
  the auth dir at `/root/.cli-proxy-api`, and plugins at `/CLIProxyAPI/plugins`. Expose port 8317.
  docker-compose: `docker compose up -d` from the cloned repo (help.router-for.me/docker/docker-compose).

**Login flows** (CLI flags from `cmd/server/main.go`; add `-no-browser` to print the URL instead of opening a browser)

| Provider | Flag | Local callback port |
|---|---|---|
| Claude Code (Anthropic OAuth) | `--claude-login` | 54545 |
| Codex / ChatGPT | `--codex-login` (or `--codex-device-login` for device code, good for headless boxes) | 1455 |
| Antigravity (Google) | `--antigravity-login` | 51121 |
| Kimi | `--kimi-login` (kimi.com) / `--kimi-ai-login` (kimi.ai) | device-code flow via the management API |
| xAI Grok | `--xai-login` | device-code flow |
| Devin, Meta | `--devin-login`, `--meta-login` | |
| Vertex | `--vertex-import <sa.json>` | |

- Gemini: v8 has no Gemini-CLI login flag. Gemini comes through API keys (AI Studio, Interactions,
  Vertex) or through Antigravity OAuth.
- `--oauth-callback-port` overrides the callback port.
- In Docker: `docker compose exec cli-proxy-api /CLIProxyAPI/CLIProxyAPI -no-browser --claude-login`.
- You can also log in from the dashboard ("OAuth Login" page), which uses the management endpoint
  `GET /v8/management/oauth/auth-url?provider=claude|codex|antigravity|kimi|xai|...`.
  Poll `/oauth/status?state=` until it returns `ok`. If the browser cannot reach the callback port,
  POST the full redirect URL to `/oauth/callback` (docs/management-api-v8.md).

**Multiple accounts.** Each login adds one more credential file, for example `claude-<email>.json` or
`codex-<email>-pro.json`, as seen in the video. Every file for a provider joins that provider's pool.
You can tune each credential through its JSON: `weight`, `priority` (larger wins), `prefix`, `proxy-url`,
and per-auth `model_aliases`. You can also enable/disable it with `PATCH /v8/management/credentials/status`.

**Routing, load balancing and failover** (`routing:` in config.example.yaml)
- `strategy`: `round-robin` (default), `weighted-round-robin`, or `fill-first`.
  Fill-first plus `priority` is how you drain one account before the next.
  Core has no "soonest reset first" strategy; Theo patched his fork for it. The Rust port `cliproxy-rs`
  ships an opt-in `soonest-reset` (README "More choices").
- `session-affinity: false` (default) with `session-affinity-ttl: 1h`. When on, a session stays pinned to
  one credential. The session key comes from, in order: Claude Code/Codex/OpenCode/pi session headers,
  then `prompt_cache_key`, then Responses conversation id, then a hash of the first message.
  `session-affinity-subagents: true` makes child sessions reuse the parent's credential.
  Failover is always on when the bound credential becomes unavailable.
- `retry.request-retry: 3` adds extra rounds on HTTP 403/408/429/500/502/503/504.
  `max-retry-credentials: 0` means try all credentials. `max-retry-interval: 30`s caps the cooldown wait.
- `cooldown`: a credential that hits quota is cooled down. Transient errors trigger a 60s cooldown by default.
  `upstream.claude.model-level-cooling` / `upstream.codex.model-level-cooling` limit the cooldown to the
  one model instead of the whole account.
  `POST /v8/management/routing/cooldown/reset` clears a cooldown.
- The video's "Switch Project" and "Switch to Preview Model" toggles are legacy quota-exceeded switches
  kept for compatibility (Gemini-centric).

**Model names and aliases**
- Native ids come from the catalog (`internal/registry/models/models.json`):
  - Claude: `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-fable-5-1`, `claude-opus-5`, `claude-fable-5`.
  - Codex Plus/Pro/Team: `gpt-6.1-sol`, `gpt-6-sol`, `gpt-6-astra`, `gpt-6-luna`. Codex Free has `gpt-6-luna` only.
  - Context sizes: Claude 1,000,000; Codex 272,000. You can override the context size per model
    (`oauth.settings.codex[].max-context-length`).
- Aliases: `oauth.model-alias.<channel>` with entries `{name: <upstream>, alias: <client name>}`.
  `fork: true` keeps both names. `force-mapping` rewrites the model name in responses.
  Channels: claude, codex, kimi, xai, meta, antigravity, vertex, aistudio.
  `oauth.excluded-models` hides models.
- Prefixes: setting `prefix: "x"` on a credential makes `x/<model>` reach only that credential.
  Useful to pin one account.
- Thinking or effort suffix on any model name: `gpt-6.1-sol(high)` or `claude-opus-5-5(8192)`.
  Levels: minimal / low / medium / high / xhigh / auto / none. The suffix is stripped before routing
  (help.router-for.me/configuration/thinking).

**Endpoints** (default `:8317`, from `server_routes.go`)
- OpenAI-compatible:
  - `POST /v1/chat/completions`, `/v1/completions`, `/v1/responses` (plus `GET /v1/responses` as WebSocket), `/v1/responses/compact`.
  - `GET /v1/models`. Images on `/v1/images/*`. Realtime on `/v1/realtime*`.
- Claude-compatible: `POST /v1/messages` and `POST /v1/messages/count_tokens`. Use base URL without `/v1`.
- Gemini-compatible: `GET /v1beta/models`, `POST /v1beta/models/{model}:generateContent|streamGenerateContent`, `/v1beta/interactions`.
- Codex direct: `/backend-api/codex/responses`.
- Health: `GET /healthz`. Dashboard: `GET /management.html`.

**Client API keys** (`access.api-keys`). These are the keys QMX would send. They are not upstream keys.
- Accepted as `Authorization: Bearer`, `X-Api-Key`, `X-Goog-Api-Key`, `?key=`, or `?auth_token=` (docs/sdk-access.md).
- If no auth providers are configured, all requests pass. That is the "no API key" mode Theo uses.
- If the list still contains the template values (`your-api-key-1`...), every proxy endpoint returns 403
  `unsafe_example_api_key` (safe mode) until you change them.

**Management API and dashboard**
- Bases: `/v8/management` (current) and `/v0/management` (legacy, near deprecation).
- Auth header: `Authorization: Bearer <mgmt-key>` or `X-Management-Key`. The key is required even from localhost.
  `management.secret-key` is hashed on startup. If it is empty, the management API is disabled (404).
  `MANAGEMENT_PASSWORD` env or `--password` also work.
- Remote (non-localhost) management requires `management.allow-remote: true`.
- 5 failed auths from one IP lead to a ban of about 30 minutes.
- Key v8 endpoints:
  - `/config` (GET/PUT/PATCH JSON), `/config.yaml`, `/config/<section>/<field>`.
  - `/credentials` (list, upload, delete), `/credentials/models`, `/credentials/refresh`.
  - `/oauth/auth-url`, `/oauth/status`.
  - `/observability/logs`, `/observability/usage/api-keys`, `/observability/usage/queue`.
  - `/routing/model-definitions/<channel>`.
- The v0 API also has `/reset-quota`, `/routing/strategy`, `/api-key-usage`, `/auth-files/models`
  (help.router-for.me/management/api).
- **Dashboard** = CPAMC (github.com/router-for-me/Cli-Proxy-API-Management-Center).
  - Served at `http://<host>:8317/management.html`. It downloads automatically from GitHub releases;
    turn that off with `management.disable-control-panel: true`.
  - `panel-github-repository` points at your own fork. The fork must publish one `management.html`
    release asset (help.router-for.me/management/webui).
  - It stores the API base URL and, optionally, the management key in the browser's localStorage for
    its own origin.
- **Can it be embedded?** The core sends `Access-Control-Allow-Origin: *` and no
  `X-Frame-Options` or CSP `frame-ancestors` header (`server_middleware.go` corsMiddleware). So an
  `<iframe src="http://cpa-host:8317/management.html">` loads.
  - The user still logs into the panel with the management key inside the frame.
  - Browsers partition cross-site iframe storage, so "remember me" is kept per embedding site.
  - Plugin resource pages that share the panel's origin can read the stored key. Treat installing a
    plugin as trusting it (webui page).
- **Usage statistics**:
  - Since v6.10.0 the core and CPAMC no longer ship built-in usage stats.
  - The core keeps only a short-lived queue: `observability.usage.usage-statistics-enabled`, retention
    `redis-usage-queue-retention-seconds` (60s default, max 3600). Collectors read it from
    `/observability/usage/queue`.
  - For history use CPA Usage Keeper (SQLite plus dashboard), CPA-Manager-Plus (cost estimates), or
    Oh-My-CPA (README "Usage Statistics").
  - Quota windows (5h/7d/weekly) are read per credential by the panel's Quota page, and by tools such as
    Quotio, Infinitus and cc-status-line through the management API.

---

## C. Integration recipe for QMX (Python, LangChain/LangGraph/Deep Agents)

**1. Proxy config, minimal** (`config.yaml`, v8 layout)
```yaml
config-version: 8
server: { host: "", port: 8317 }        # in Docker bind all; restrict at the network layer (see 3)
management:
  allow-remote: true                    # needed: Docker bridge / tailnet requests are not "localhost"
  secret-key: "<mgmt key, from secret store>"
access:
  api-keys: ["<qmx-client-key>"]        # replace templates or safe mode returns 403
routing:
  strategy: "fill-first"                # or round-robin; fill-first + credential priority = drain one account first
  session-affinity: true                # keep each Copilot thread on one account (cache reuse)
  session-affinity-subagents: false     # let GPT sub-agents spread across the Codex pool
oauth:
  auth-dir: "~/.cli-proxy-api"
observability:
  usage: { usage-statistics-enabled: true, redis-usage-queue-retention-seconds: 3600 }
```

**2. LangChain clients** (one base URL, two API shapes)
```python
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

CPA = "http://cpa-host:8317"           # e.g. Tailscale MagicDNS name of the proxy box
KEY = load_secret("qmx/cliproxy-client-key")   # same pattern as qmx/* broker creds; never in .env/repo

copilot_llm = ChatAnthropic(model="claude-opus-5-5", base_url=CPA, api_key=KEY,
                            max_tokens=32000, timeout=600)       # SDK appends /v1/messages
worker_llm  = ChatOpenAI(model="gpt-6.1-sol", base_url=f"{CPA}/v1", api_key=KEY,
                         use_responses_api=True, timeout=600)    # or chat/completions (default)
# effort via suffix: model="gpt-6.1-sol(high)"; Claude budget: model="claude-opus-5-5(16000)"
# affinity for OpenAI threads: worker_llm.bind(prompt_cache_key=thread_id) or model_kwargs/extra_body
```
- Deep Agents: `create_deep_agent(model=copilot_llm, subagents=[{"name": "researcher", ..., "model": worker_llm}])`.
  Check that the installed `deepagents` version accepts a per-subagent `model` key. If not, build each
  subagent as its own LangGraph graph with its own LLM.
- Per-agent model selection: keep a registry `{agent_role: (provider_shape, model_id, effort)}` in QMX
  Settings, which fits the "configurable = UI-editable" rule. A factory builds `ChatAnthropic` for
  `claude-*` ids and `ChatOpenAI` for everything else.
  Because the proxy translates formats, `ChatOpenAI(model="claude-opus-5-5")` also works. Native
  `ChatAnthropic` keeps Claude-specific features (thinking blocks, cache control) cleaner.

**3. List models**
`curl -H "Authorization: Bearer $KEY" http://cpa-host:8317/v1/models` returns the merged OpenAI-format
list, including aliases. For Gemini format use `GET /v1beta/models`. For what one account can serve, use
`GET /v8/management/credentials/models?name=<file>` with the management key.
In Python: `ChatOpenAI`'s client, `openai.OpenAI(base_url=f"{CPA}/v1", api_key=KEY).models.list()`.
Use this to fill the per-agent model dropdown.

**4. Run on a remote Linux server in Docker**
```yaml
# docker-compose.yml
services:
  cli-proxy-api:
    image: eceasy/cli-proxy-api:latest
    restart: unless-stopped
    ports: ["100.x.y.z:8317:8317"]       # bind to the Tailscale IP (or 127.0.0.1 + `tailscale serve`), never 0.0.0.0 on a public host
    volumes:
      - ./config.yaml:/CLIProxyAPI/config.yaml
      - ./auths:/root/.cli-proxy-api
      - ./plugins:/CLIProxyAPI/plugins
```
- Logins on a headless box. Pick one:
  - (a) `docker compose exec cli-proxy-api /CLIProxyAPI/CLIProxyAPI -no-browser --claude-login`, with
    `ssh -L 54545:localhost:54545 box` so the callback reaches the box. Use port 1455 for Codex.
  - (b) `--codex-device-login`.
  - (c) the dashboard's OAuth Login page, pasting the redirect URL back.
  - (d) log in on the Windows PC and copy the `*.json` token files into `./auths` (hot-reloaded).
- The video's reasoning for where the box lives (13:30, 59:00): Theo runs the proxy on a home machine
  so upstream traffic leaves from one residential IP, and reaches it over Tailscale. A datacenter VPS is
  the setup he says gets flagged. If QMX's "remote server" is a cloud VPS, `requests.proxy-url` (socks5)
  can send upstream traffic out through another egress.

**5. Showing the dashboard in QMX Settings**
- Option A, quickest: a "Provider gateway" card with status from `GET /healthz`, plus an "Open dashboard"
  button that opens `http://cpa-host:8317/management.html` in a new window or popup. The operator types
  the management key once in the panel.
- Option B: an iframe of the same URL in a Settings tab. It works because there is no X-Frame-Options.
  Caveats: mixed content (an https QMX UI cannot frame an http proxy, so put TLS or `tailscale serve`
  https in front); login happens inside the frame; partitioned storage.
- Option C, matches the Lego vision: a native QMX panel built on the management API, called by the QMX
  **backend** (keep the management key server-side, not in browser JS). Contents:
  - credentials list with enable/disable (`/credentials`, `/credentials/status`),
  - "Add account" (`/oauth/auth-url?provider=...` then poll `/oauth/status`),
  - model list,
  - routing strategy toggle (`PATCH /config/routing`),
  - logs,
  - usage from `/observability/usage/queue`, persisted into QMX's DB.
  Per-account 5h/7d quota bars are what CPAMC's Quota page shows. Reuse its approach or embed only that page.
- You can also restyle a CPAMC fork and serve it via `panel-github-repository`, as Theo suggests at 17:50.

---

## D. Gotchas and limits

- **Default port is 8317.** Theo's 8318 is his own config. His transcript says "4318", but the frames show 8318.
- **Template client keys block everything** (403 safe mode). An empty key list means *no auth*. Only
  acceptable behind a private network such as a tailnet. Theo's "added a key and broke everything" (22:30)
  is the reverse case: once a key exists, every client must send it.
- **Remote management is off by default.** `allow-remote: true` is needed for Docker or LAN access. 5 bad
  keys from an IP lead to a 30-minute ban. An empty `secret-key` disables the management API and the
  dashboard's data.
- **Token refresh**: the core auto-refreshes OAuth with 16 worker threads by default (`auth-auto-refresh-workers`). Theo says
  Claude Code auth "breaks every two to three days" (14:30). Watch the Auth Files page and re-login on
  failure. A refused credential gets cooled down, not deleted.
- **Rate limits are per account**: 5-hour and weekly windows. A cooldown on `usage_limit_reached` blocks the
  whole credential unless `model-level-cooling` is on. Retries cover 403/408/429/5xx with 3 extra rounds
  and wait at most 30s.
- **Cache cost of account switching** (20:50-22:00). Without session affinity (default **off** in core),
  round-robin can move a long Copilot thread between accounts and rewrite the prompt cache. Enable
  `session-affinity`. For OpenAI-shape calls, pass a stable `prompt_cache_key` per thread.
- **Claude "cloaking"**: with defaults, requests from non-Claude-Code clients are disguised as Claude Code
  CLI traffic, *including system prompt replacement* (`upstream.claude.disable-claude-cloak-mode: false` =
  "auto"). The QMX Copilot's system prompt may therefore be rewritten or wrapped. Test what the model
  actually receives before relying on prompt behaviour.
- **Theo's stated risk** (25:45): he says Claude-subscription models used outside Claude Code lead to bans.
  QMX's Copilot via `ChatAnthropic` is exactly that pattern. Weigh it with the residential-IP advice.
- **Codex WebSocket** (20:30): Theo says enabling it makes Codex markedly faster. In core, the
  `websockets: true` option is documented per Codex *API-key* entry. Experimental `response-steering`
  sits under `upstream.codex`. Check what applies to OAuth credentials in your version.
- **Streaming behind reverse proxies**: nginx's 60s `proxy_read_timeout` can cut long reasoning streams.
  Set `stream-bootstrap-timeout: "20s"` if you enable bootstrap buffering, and raise the timeouts.
  The docs' own Claude Code example uses 600 s timeouts. Match that in LangChain (`timeout=600`).
- **Concurrency**: there is no per-client concurrency cap in the basic config; the advanced
  `credentials.concurrency` block exists. Theo shows the box doing proxy work at ~0% CPU (61:30). The
  limit is upstream account quota, not proxy hardware. `server.commercial-mode: true` cuts per-request
  overhead under high concurrency.
- **Model id drift**: catalogs refresh every 3 hours from remote sources. Ids such as `gpt-6.1-sol` /
  `claude-opus-5-5` can change. Populate the QMX dropdowns from `/v1/models` instead of hard-coding them.
- **Usage history is not kept by the core.** Retention is 60s by default (max 3600). QMX must poll and
  persist, or run CPA Usage Keeper alongside.
- **Codex vs Claude resets** (26:15-28:30): a Codex reset moves the weekly date out by 7 days; a Claude
  reset refills the percentage only. Matters if QMX ever schedules heavy jobs around quota windows.
