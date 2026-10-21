# 49 — Compute and storage off the PC: options, costs, and fit with QMX

Date: 2026-10-21. Research only. Nothing here is decided.

How this was read. Official docs and pricing pages, fetched on 2026-10-21 with Firecrawl or with `curl` (Cloudflare and Claude Code serve their docs as Markdown; T3 Code, Cloudroom and Cursor docs were read from their own repos or `.md` endpoints). Tags: **[retrieved]** = read in that source today; **[inferred]** = my reasoning from retrieved facts; **[local]** = checked in this repo. Prices are list prices in USD unless marked €, before tax, as shown on the date above. Sources are in §9.

The ask comes from the operator's seed (2026-10-21) and from rulings 25, 43, 53, 55, 60-69, 74-76 and 116-117 in `26-operator-rulings-and-alignment.md`. Earlier studies: `29-environments-and-deployment.md`, `31-cua.md`, `32-amp-orbs-and-cua.md`.

---

## 0. Plain words first

**The short answer.** Keep one cheap server you rent by the month. Use Cloudflare for storage, backups and extra machines when you need many at once. Keep Windows work on your PC.

- **A server is still needed.** QMX's design keeps a few things running all the time: the Library's home copy, the key safe, the scheduler, market data and the relay that adds keys to model calls. They need a disk that stays and a process that never stops. Cloudflare does not give that cheaply. A rented server does.
- **Rented servers are far cheaper for always-on work.** Twenty agents running all month cost about $24 to $30 on a large Contabo server. The same twenty on Cloudflare cost about $385. Other pay-per-minute providers cost $750 to $1,200.
- **Pay-per-minute machines win for short bursts.** Twenty agents for three hours a day cost about $50 a month on Cloudflare. A server big enough for that peak costs more and sits idle the rest of the day.
- **Cloudflare is the best place for storage.** 100 GB costs about $1.35 a month, the first 10 GB are free, and downloads are free. Your Library backups, artifacts and the 10 GB of old tick data fit there.
- **Cloudflare can run Claude Code agents,** with keys kept outside the box. Agents can set it up themselves: Cloudflare publishes a Claude Code plugin, skills and MCP servers.
- **Cloudflare cannot do everything.** It has no Windows, so no cTrader. Its disks are wiped when a machine stops. It cannot use your Claude plan login (QMX's own rule keeps plan logins on machines you own). It cannot use your own logged-in browser.
- **Windows for cTrader:** your PC is free and works today. A Windows server costs about $25 a month on Contabo (the server plus a €17 licence).
- **What to do with Contabo now:** keep it until December and build the server work on it, as planned. In December, either renew a bigger plan (about $24 to $30 a month for 48 GB) or move the home to another server. Moving is a copy-and-switch procedure, not a rebuild.
- **The design already allows new providers.** Adding Cloudflare needs one new connector. Moving the home off Contabo changes names and setup steps, not the design.
- **Connecting a machine should feel like T3 Code:** one button or one command, a short code you confirm, and the machine shows up in QMX with its own live view. Section 7 lays out the steps.

### Comparison table (agent hosting)

A "session" is one Claude Code or Agent SDK agent at 1.5 GB, QMX's planning figure. "Always on" means running all month. "Burst" means 20 agents for 3 hours a day (1,800 agent-hours a month). Light CPU use is assumed, since agents mostly wait for the model.

| Option | Windows | Keeps its disk | Runs Claude Code | Free tier | 4 always on | 20 always on | Burst | Agent can set it up |
|---|---|---|---|---|---|---|---|---|
| **Contabo VPS** (rent a server) | yes, €17/mo licence | yes | yes | no | **$7-9** (today's box) | **$24-30** (48 GB box) | covered by the same box | API, CLI, cloud-init |
| Oracle Always Free | no (ARM Linux) | yes | yes (ARM64) | **free**, 12 GB | **$0** | no | no | CLI, Terraform |
| Hetzner Cloud | unsupported | yes | yes | no | ~€70 | ~€200+ | — | API, CLI |
| DigitalOcean droplet | no | yes | yes | no | ~$96 | ~$300+ | — | API, CLI |
| AWS Lightsail | yes ($44+ for 4 GB) | yes | yes | trial only | ~$84 | ~$164-300 | — | API, CLI |
| **Cloudflare Containers / Sandbox** | no | no (snapshots, buckets) | yes | no ($5/mo plan) | ~$80 | ~$385 | **~$52** | **plugin, skills, MCP, CLI** |
| Fly.io Machines | no | volumes | yes | no | ~$39 | ~$194 | ~$24 | API, CLI |
| Modal Sandboxes | no | volumes | yes | $30/mo credit | ~$128 | ~$760 | ~$67 | Python SDK |
| Vercel Sandbox | no | snapshots, drives | yes | ~50 agent-hours | ~$161 | ~$800 | ~$99 | SDK, CLI |
| E2B | no | no (paid tiers persist) | yes | $100 once | ~$392 | ~$1,360 | ~$299 | SDK |
| Daytona | **yes** (billed per hour) | yes | yes | $200 once | ~$242 | ~$1,210 | ~$149 | SDK |
| Amp orbs | no | yes (pauses) | yes | own machines free | ~$234 | ~$1,170 | ~$144 | CLI only |

### Comparison table (storage, 100 GB)

| Option | 100 GB a month | Download fees | Notes |
|---|---|---|---|
| **Cloudflare R2** | **$1.35** (10 GB free) | free | S3-compatible; official skills and MCP |
| Lightsail bucket | $3 | 250 GB included | fixed bundle |
| Contabo Object Storage | from $2.99 | free | existing customers only; 10 MB/s default speed |
| AWS S3 | ~$2.30 | $0.09/GB | the reference |
| DigitalOcean Spaces | $5 (250 GB) | 1 TB included | |
| Oracle Always Free | 20 GB free | — | too small |

---

## 1. What QMX needs (from the seed and the rulings)

| Need | Source | What it means for a provider |
|---|---|---|
| About 20 agents or workflows at once, off the PC; about 1 GB each in the light case, more for scraping and tools | seed; rulings 55, 68, 76 | RAM is the bill. 20 × 1.5 GB ≈ 30 GB plus services |
| One dedicated machine for backtests (QMB) | ruling 68; engine AD-31 | an owned, always-on box with its own queue |
| Computer and browser use; logged-in profiles; MT5 and cTrader demo, cTrader needs Windows | rulings 20, 60, 65, 108, 116; AD-33, AD-44 | a Windows desktop somewhere; a browser that can be watched and taken over |
| Storage and backups: the Library, artifacts, ~10 GB legacy tick data, git-like history | rulings 41, 42, 56; Library AD-10, AD-16 | an S3-compatible bucket plus a server copy |
| Set up and managed from the QMX UI or copilot, from the provider's own skills or instructions | rulings 67, 74; engine AD-30, AD-32 | CLI, API, MCP server or published skills |
| Logs, monitoring, resource use visible on the PC | rulings 43, 117; AD-65, Library AD-13 | QMX's own heartbeat and sidecar; the provider's dashboard as a link |
| Remote runs reach the same files and Library; no keys on workers | rulings 43, 61; AD-28, Library AD-11, AD-12 | a way to reach the Hub and the relay; keys added outside the box |
| Avoid paying for a server if possible | seed | cost per month is the main ranking |

The Claude Agent SDK hosting guide gives the sizing rule: start at "1 GiB RAM, 5 GiB disk, and 1 CPU per agent", and "agents per host = (host RAM - overhead) / (per-session RAM ceiling)"; 1 GiB is "a floor, not the ceiling" **[retrieved, code.claude.com/docs/en/agent-sdk/hosting]**. QMX already uses 1,536 MB per session and derives `max_sessions` from RAM (engine AD-30) **[local]**. Claude Code runs on x64 and ARM64, Ubuntu 20.04+, Windows 10 1809+ **[retrieved, code.claude.com/docs/en/setup]**.

---

## 2. Each option in detail

### 2.1 Cloudflare

Cloudflare docs were read on 2026-10-21; most pages were updated in September or October 2026.

**Containers** (the machines) **[retrieved]**
- Linux containers started by a Worker and a Durable Object. Paid plan only ("Available on Workers Paid plan"; the $5/month plan).
- Sizes: `lite` 1/16 vCPU 256 MiB; `basic` 1/4 vCPU 1 GiB; `standard-1` 1/2 vCPU 4 GiB 8 GB; `standard-2` 1 vCPU 6 GiB; `standard-3` 2 vCPU 8 GiB; `standard-4` 4 vCPU 12 GiB 20 GB. Custom up to 4 vCPU, 12 GiB, 20 GB, at least 3 GiB per vCPU. Account limits: 6 TiB memory and 1,500 vCPU at once; 50 GB of images.
- Price: memory $0.0000025 per GiB-second (about $0.009 per GiB-hour) and disk $0.00000007 per GB-second, both on the size you pick; CPU $0.000020 per vCPU-second, on **active use only**. Included each month: 25 GiB-hours, 375 vCPU-minutes, 200 GB-hours. Egress $0.025/GB after 1 TB (North America and Europe).
- **Disk is wiped** when the container sleeps. Options: snapshots (public beta, kept 30 days, up to 20 GB) and R2 mounted by FUSE ("not native SSD-like performance").
- **Run time:** no fixed maximum. It stops when its inactivity timeout ends (up to 6 hours), when the main process exits, or on a host restart, which "happens on an irregular cadence"; Cloudflare "does not guarantee that any container instance will run for a set period". Before a stop it sends SIGTERM and waits up to 15 minutes. Code running inside does **not** count as activity; a Durable Object alarm (for example once a minute) keeps it alive.
- Docker-in-Docker works. Cold starts are "often in the 1-3 second range". No GPU and no Windows appear anywhere in the Containers docs.
- Logs: Workers Logs, kept 7 days, exportable by Logpush.

**Sandbox SDK** (containers shaped for agents) **[retrieved]**
- A sandbox is "a name, a Durable Object, and an instance in Containers". Guides cover Claude Code, Codex, OpenCode, Pi, Cursor self-hosted machines, Devin, and Claude Managed Agents.
- The Claude Code guide installs `@anthropic-ai/claude-code` in the image and runs `claude --print --output-format stream-json` with `ANTHROPIC_BASE_URL` pointing at a gateway. Claude Code holds a placeholder key; the Worker adds the real credential on the way out.
- **Keys stay outside the box:** "Credentials are safer outside the sandbox." A container starts with `enableInternet: false` and reaches only hostnames the Worker intercepts. The outbound handler adds the credential.
- Also documented: background processes, a browser terminal over WebSocket, back up a directory to R2, mount an R2 prefix "without giving the sandbox your credentials", previews on their own hostnames.

**Durable Objects, Queues, Workflows, Workers** **[retrieved]**
- Durable Objects: 1 million requests and 400,000 GB-seconds included, then $0.15 per million and $12.50 per million GB-seconds.
- Queues: 1 million operations included, then $0.40 per million.
- Workflows: steps can wait on I/O without limit. Up to 10,000 steps (25,000 configurable), 50,000 concurrent instances, state kept 30 days.
- Workers: 10 million requests included; up to 5 minutes CPU per call; cron and queue consumers up to 15 minutes.
- **Fit [inferred]:** these are a second workflow engine. QMX has one engine (ruling 22). Use them only as glue inside a Cloudflare connector, never as QMX's control flow (engine AD-30 already says so for every provider).

**R2** (storage) **[retrieved]**
- $0.015 per GB-month standard ($0.01 infrequent access). Class A writes $4.50 per million, Class B reads $0.36 per million.
- Free each month: 10 GB, 1 million writes, 10 million reads.
- **No egress fees**, through the S3 API too.
- 100 GB costs (100 − 10) × $0.015 = **$1.35/month**.

**Browser Run** (formerly Browser Rendering) **[retrieved]**
- Free plan: 10 minutes a day and 3 browsers. Paid plan: 10 hours a month included, then $0.09/hour; 10 concurrent browsers included, then $2 per browser (monthly average); up to 200 concurrent.
- A session closes after 60 seconds idle by default; `keep_alive` raises that to 20 minutes. No fixed maximum lifetime while active. Sessions also close on Browser Run releases.
- **Live View** lets a person watch and control a session. **Human in the Loop** hands control to a person for logins, MFA or CAPTCHAs and then back to the script.
- Requests are "always identified as bot traffic", even with a human in control.
- Quick actions: markdown, crawl, JSON extract, screenshot, PDF. There is a Playwright MCP server.
- I found no documented way to carry his own logged-in browser profile into Browser Run **[inferred from the page index]**.

**Networking** **[retrieved]**
- **Cloudflare Tunnel** publishes a service with no public IP; the connector dials out.
- **Mesh** (formerly WARP Connector) gives each server or laptop a private IP, Tailscale-like. It is in beta and available on the Free plan.
- **Workers VPC** lets a Worker reach a private network through a Tunnel or Mesh.

**Agent setup** **[retrieved]**
- Cloudflare's Claude Code page installs a plugin with `/plugin marketplace add cloudflare/skills` and `/plugin install cloudflare@cloudflare`. It brings skills (wrangler, cf-cli, sandbox-stable/next, durable-objects, agents-sdk and more) and registers MCP servers.
- MCP servers: a "Code Mode" API server covering 2,500+ endpoints at `mcp.cloudflare.com/mcp`, plus containers, Browser Run and docs servers.
- Every docs page has an `llms.txt` index and a Markdown version.
- This is the strongest agent-provisioning story of any option here.

**Claude Code / Agent SDK there?** Yes, as a CLI inside a container (engine `cli_inside`). The tool server can also run inside while the loop runs elsewhere (`runner_outside`). By QMX's rule the plan login never goes to a provider machine (engine AD-28), so Cloudflare agents use key providers (Kimi, GLM, DeepSeek and others). That matches ruling 107: he uses the Chinese models most **[inferred]**.

**Computer use [inferred]:** a Linux desktop (Xvfb plus Chrome plus the Cua Driver for Linux) can probably run in a `standard-3` or `standard-4` container, but no Cloudflare doc shows it. There is no Windows.

**Cost at his scale** (packed 6 sessions per `standard-4`: 12 GiB × $0.009 + 20 GB disk + 0.6 vCPU active × $0.072 ≈ $0.156/hour, so **about $0.026 per agent-hour**) **[inferred from retrieved rates]**:
- 4 always on: about $76 + $5 plan ≈ **$80/month**.
- 20 always on: about $380 + $5 ≈ **$385/month**.
- Burst (1,800 agent-hours): about $47 + $5 ≈ **$52/month**.
- Memory is billed while the agent waits on the model. That is why always-on work is expensive here.

### 2.2 Vercel Sandbox **[retrieved]**
- Firecracker microVMs, Linux. Pro: active CPU $0.128/hour (waiting on I/O or a model call is not billed), memory $0.0212/GB-hour, each vCPU comes with 2 GB.
- Hobby is free: 5 CPU-hours and 420 GB-hours a month, 45-minute sessions, 10 concurrent.
- Pro: $20/month with $20 credit, 24-hour sessions, 10,000 concurrent. A "persistent sandbox" resets the limit on each resume.
- 64 GB ephemeral NVMe; snapshots $0.08/GB-month; drives $0.05/GB-month.
- No Windows.
- Cost (1 vCPU, 2 GB, 10% CPU ≈ $0.055/hour): 4 always on ≈ $161; 20 ≈ $800; burst ≈ $99. Hobby covers about 50 agent-hours a month **[inferred]**.

### 2.3 Amp orbs and runners **[retrieved]**
- Orbs: `a1.tiny` 1 CPU 2 GB $0.08/h; `a1.small` 2/4 $0.17; `a1.medium` 4/8 $0.33; `a1.large` 8/16 $0.66; `a1.xxlarge` 16/32 $1.32. All have 60 GB disk.
- Billing is by the minute; a paused orb costs nothing. An orb pauses 5 minutes after the agent's work or 20 minutes after his last action.
- Burst of 20 orbs, then 1 new orb every 5 minutes.
- **Runners** run on his own machines for free (`amp --no-tui --runner-id …`). `--desktop` streams a desktop over WebRTC. `--remote-control-terminal` gives terminal access. `--amp-env` pulls secrets per thread from ampcode.com. Claude Code mode uses his plan on his own machine. Runners update themselves when idle.
- Linux only for orbs (file 32).
- Cost with one orb per agent (`a1.tiny`): 4 always on ≈ $234; 20 ≈ $1,170; burst ≈ $144.
- **Fit:** a burst provider, or a free control surface for owned machines. Engine AD-25 and AD-30 already model it (`host_harness`, runner).

### 2.4 Contabo **[retrieved]**
- Cloud VPS (list price / effective price on a 24-month term):
  - VPS 4: 4 vCPU, 8 GB, 100 GB — $6.60 / $5.28.
  - **VPS 6: 6 vCPU, 12 GB, 200 GB SSD** (his box) — $9.00 / $7.20.
  - VPS 8: 8 vCPU, 24 GB — $16.80 / $13.44.
  - **VPS 12: 12 vCPU, 48 GB, 400 GB SSD** — $30.00 / $24.00.
  - VPS 16: 16 vCPU, 64 GB — $44.50 / $35.60.
- Unlimited traffic under fair use. KVM virtualisation. API, CLI and cloud-init. Custom images.
- Windows Server licence €17/month.
- Object Storage: S3-compatible, "from $2.99/month", transfer included. Available "exclusively to existing Contabo customers". Default bandwidth 10 MB/s, 250 requests per second, 3 million objects.
- Payment: EUR, USD, GBP. Non-card first payments are manual. The page does not show enough to judge his payment concern.
- Sessions per box with QMX's rule ((RAM − 6,144 MB overhead) / 1,536):
  - VPS 6: 4 (2 with Hindsight there), as AD-30 says.
  - VPS 8: 12.
  - **VPS 12: 27.**
- A GPU VPS is "not available" (notify-me form).

### 2.5 Hetzner **[retrieved]**
- Regular Performance (shared) prices have risen sharply:
  - CPX22: 2 vCPU, 4 GB — €19.99.
  - CPX32: 4/8 — €35.99.
  - CPX42: 8/16 — €69.99.
  - CPX52: 12/24 — €100.99.
- Every CPX row showed "This product is currently unavailable" today. Cost-Optimized shows "Currently not available".
- Windows: "we will not provide any support for Windows".
- **No longer the cheap option.** Contabo is 3-5× cheaper per GB of RAM.

### 2.6 Oracle Cloud Always Free **[retrieved]**
- Arm Ampere A1: "1,500 OCPU hours and 9,000 GB hours per month", about 2 OCPU and 12 GB running all month. Also 200 GB of block volume, 20 GB of object storage and 10 TB of egress.
- Risks:
  - Idle instances "may be reclaimed" when, over 7 days, CPU, network and (for A1) memory are all under 20%.
  - Accounts idle for 30 days "may be deemed abandoned".
  - "Out of host capacity" errors happen.
  - One free account per person; a card is required.
- Claude Code supports `linux-arm64`. The `qmx-worker` image would need an ARM64 build **[inferred]**.
- **Fit:** the only $0 always-on home. It is as big as today's Contabo box, with less certainty.

### 2.7 DigitalOcean **[retrieved]**
- Basic droplets: 8 GiB / 4 vCPU $48; 16 GiB / 8 vCPU $96.
- Spaces: $5/month for 250 GiB and 1 TB egress.
- No Windows droplets were seen on the page.
- App Platform is for web apps, not agent sandboxes (not re-read).

### 2.8 AWS **[retrieved]**
- Lightsail Linux: 8 GB $44; 16 GB $84; 32 GB $164.
- Lightsail Windows: 4 GB $44; 8 GB $74.
- Lightsail bucket: 100 GB for $3.
- S3 storage $0.023/GB (from the Lightsail overage table); egress $0.09/GB.
- EC2 and Fargate were not re-read. They are priced above Lightsail for the same RAM **[inferred]**.

### 2.9 Fly.io **[retrieved]**
- Machines are billed per second while running:
  - shared-cpu-1x with 1 GB: $6.70/month.
  - shared-cpu-2x with 2 GB: $13.39/month.
  - Extra RAM: $6/GB/month.
  - A stopped machine pays only for its root filesystem, at $0.15/GB/month.
- Volumes $0.15/GB/month. Egress $0.02/GB in North America and Europe.
- About $0.0135 per agent-hour at 1.5 GB **[inferred]**: 4 always on ≈ $39; 20 ≈ $194; burst ≈ $24.
- **The cheapest pay-per-use Linux host found.** It has an API but no published agent skills (not checked).

### 2.10 Modal **[retrieved]**
- Sandboxes run at non-preemptible rates: CPU $0.00003942 per physical core per second (one core is 2 vCPU, minimum 0.125 core); memory $0.00000667 per GiB-second.
- Starter plan: $0 with $30/month credit and 100 containers.
- Per agent (0.125 core, 1.5 GiB) ≈ $0.054/hour: 4 always on ≈ $128 after credit; burst ≈ $67.
- GPUs are available.
- QMX already has `ModalProvider` **[local, qmx_remote/providers.py]**.

### 2.11 E2B **[retrieved]**
- Hobby: free with $100 once, 1-hour sessions, 20 concurrent.
- Pro: $150/month plus usage, 24-hour sessions, 100 concurrent.
- Usage: 1 vCPU $0.000014/s; 2 GiB $0.000009/s.
- Per agent ≈ $0.083/hour: 4 always on ≈ $392 with Pro; burst ≈ $299.
- QMX already has `E2BProvider` **[local]**.
- Self-hosting E2B (file 29) needs a KVM host.

### 2.12 Daytona **[retrieved]**
- Per hour: vCPU $0.0504, GiB $0.0162; storage after 5 GiB free; **Windows $0.0858 per vCPU-hour**; $200 free compute once.
- Per agent ≈ $0.083/hour; burst ≈ $149.
- **The only pay-per-hour Windows option found.** Whether cTrader runs well there is not checked.
- Its open-source self-host is archived (file 29).

### 2.13 Cua (computer use) **[retrieved]**
- Cua Spaces does not rent computers ("You bring the computers; Cua doesn't rent them").
- Free: 2 live sessions and 20 remote hours a month through its relay. Pro $18/month (or $180/year) for 5 sessions and 200 hours.
- Spaces reached on his own network do not use the relay and do not count.
- Cua Driver is MIT (file 31).
- **Fit:** the desktop layer on whatever machine he owns or rents, not a host.

### 2.14 Agent-provisioning ease, ranked **[retrieved where named; inferred ranking]**
1. **Cloudflare:** official Claude Code plugin with skills; API "Code Mode" MCP; containers, browser and docs MCP servers; `wrangler` and the `cf` CLI; Markdown docs with `llms.txt`.
2. **Amp:** a CLI (`amp -ox`, `amp --no-tui`); no public API for orbs (file 32).
3. **Contabo, Hetzner, DigitalOcean, AWS, Fly:** REST APIs and CLIs; cloud-init. Agents can drive them through the generic `ssh` adapter once a box exists.
4. **Modal, E2B, Daytona, Vercel:** SDKs, wired through code. QMX already has adapters for E2B and Modal.

---

## 3. Windows desktop for cTrader (and MT5)

| Option | Cost | Notes |
|---|---|---|
| **His PC** | $0 | Works today; Cua Driver runs in his interactive session (AD-33). Not available while the PC sleeps |
| Contabo VPS 4 + Windows licence | ≈ $5.28-6.60 + €17 ≈ **$25/month** | Owned, always on; he logs in to his demo terminals once |
| AWS Lightsail Windows 4 GB / 8 GB | $44 / $74 | Simple, dear |
| Daytona Windows sandbox | ≈ $0.24/hour for 2 vCPU, 4 GiB | Pay only when used; cTrader fit not checked |
| Cloudflare, Vercel, Amp orbs, Modal, Fly, E2B | — | Linux only |

The rule stands: agents use only the demo accounts he set up, never sign in to his broker, and never touch live accounts (rulings 108, 116; AD-33). **Recommendation [inferred]:** keep cTrader and MT5 on the PC until a workflow needs them while the PC sleeps. Then add one Contabo Windows box as a `desktop` placement.

---

## 4. Recommendation

### 4.1 The cheapest setup that covers his needs

| Job | Where | Monthly |
|---|---|---|
| Always-on home: Library Hub, key safe, central relay, scheduler, market data and tick data, monitoring, the QMB backtest queue, and the first agents | **one rented Linux server** (Contabo today) | today's box: already paid; from December, VPS 12 (48 GB): **$24-30** |
| Storage and backups (the bucket tier of the Library, artifacts, a second copy of tick data) | **Cloudflare R2** | **≈ $1.35** for 100 GB |
| Extra agents when the server is full (a 20-agent fan-out, scraping bursts) | **Cloudflare Containers** (Fly.io is the cheaper second choice) | **$5 plan + about $0.026 per agent-hour** |
| Headless web reading, scraping, screenshots | Cloudflare Browser Run, or Chrome on the server | $0 within 10 hours a month |
| Browsing as him (logged-in profile, watched, take-over) | **his PC**, QMX's browser layer (AD-44) | $0 |
| cTrader and MT5 demo | **his PC**; later a Contabo Windows box if needed | $0, later ≈ $25 |
| Reaching the home server from anywhere | Tailscale (free personal plan: 6 users, unlimited devices) and, for Cloudflare machines, Cloudflare Tunnel | $0 |

**Total:** about **$1-7/month until December** (the paid Contabo box, R2, and the $5 plan only once burst machines are used). **About $30-37/month from December**, plus burst use, for 20+ agents always available.

### 4.2 The zero-server alternative, honestly

Oracle Always Free (2 ARM cores, 12 GB) as the home, plus R2 and Cloudflare burst, costs **$0-7/month** plus burst. It holds about 4 agents, the same as today's Contabo. The risks are on Oracle's own pages: idle reclamation, abandoned-account deletion and capacity errors. It also needs an ARM build of the worker image. It can serve as a fallback home, not as the plan.

### 4.3 What not to do

- **Run the always-on home on Cloudflare.** The Hub needs a disk that stays and a process that runs for weeks. Containers wipe disk and can restart at any time, and twenty always-on agents cost about 15× a VPS **[inferred from §2.1]**.
- **Use Cloudflare Workflows, Queues or Durable Objects as QMX's scheduler.** That would be a second engine (ruling 22).
- **Put the Claude plan login on any provider machine** (AD-28).

### 4.4 Contabo until December

- Keep it. Reset it as planned. Build the nine server PRs on it unchanged (§5).
- Run the server probes there. They give the real `overhead_mb` and measured per-agent RAM, which decide the December size.
- Point the Library's bucket tier at R2 now. It is a config value (rclone remote), so the bucket outlives any server.
- In December choose one of:
  - (a) Renew at VPS 12 for 48 GB. This is the simplest, and he keeps every piece where it is.
  - (b) Renew at VPS 8 (24 GB, $13-17) and let Cloudflare take the overflow.
  - (c) Move the home to another server (Oracle free, or any VPS) with the Library cut-over procedure (MIGRATION step 8, AD-19). It is a procedure, not a build.

---

## 5. Fit with QMX's design

### 5.1 Does the seam already allow new providers? Yes.

- Every node runs through `WorkerPort` (engine AD-20). Remote work is served by `ComputeProvider` with six verbs (`provision / start / status / logs / stop / teardown`, AD-25).
- `qmx_remote/providers.py` already has `SSHProvider`, `AmpProvider`, `ModalProvider` and `E2BProvider` **[local, bld-trg2a worktree]**.
- AD-30's placement registry names Cloudflare as a burst candidate. Its `provider-onboarding` flow reads a provider's own skills, `llms.txt` or MCP description as data, maps it to a generic adapter (`ssh`, `http_api`, `host_harness`, `dashboard_mcp`), drafts a placement row, and runs a one-node smoke test.
- Nothing in the design is tied to Contabo beyond names and setup steps.

**What Cloudflare specifically needs [inferred]:**
- **A small Worker in his account** (deployed by an agent with `wrangler`, using Cloudflare's own skills). It maps the six verbs onto `ctx.container.start/exec/destroy` and returns logs. QMX then talks to it through the generic `http_api` adapter. No Python provider class is needed, unless the generic adapter falls short; then one gets written, as AD-30 already allows.
- **Keys:** a Cloudflare placement defaults to `relay: central` (AD-28). The container's model traffic carries the run pass to the central relay on the home server. The Worker's outbound handler is the allow-list (relay, Hub, package registries). It adds **no** key, so keys stay on the PC and the home server only.
- **Reach:** the home server publishes the Hub and relay to Cloudflare with a **Cloudflare Tunnel**, and the Worker reaches them through **Workers VPC**. No public port opens on the server. This answers Library OPEN-5 (a public listener for providers that cannot join the tailnet) without a public listener.
- **Disk:** ephemeral disk is fine. AD-25 already starts a fresh container per attempt. The sidecar ships outputs, logs and checkpoints to the Hub by hash (Library AD-13).
- **Restarts:** a host restart is a lost attempt. The engine already folds it as `unknown` and retries by effect class (AD-8). A long agent node needs the alarm-based keep-alive inside the connector, because code running in the container does not count as activity.
- **Plan logins:** key-provider accounts only (AD-28), which fits ruling 107.
- **Dashboards:** Cloudflare's MCP servers fit AD-32's `dashboard_mcp` reach.
- **Browsers:** Browser Run fits AD-44's list of optional browser providers, beside Browserbase and Browser Use. Private URLs still go to the local browser.

### 5.2 What changes in the ADs if he moves off Contabo

| AD | Change |
|---|---|
| Engine AD-30 | "Contabo is the always-on home" becomes "an owned always-on server is the home; Contabo is today's row". Rename the placement name `contabo` to a neutral `home` (or keep the name on the new box). The RAM derivation is unchanged |
| Engine AD-25, AD-24 | Placement text and `/var/lib/qmx-node/zones` stay; "where the host has it (Contabo)" for `runsc` becomes "where the home host has it" |
| Engine AD-28 | The central relay is "the home server". Add Cloudflare Tunnel plus Workers VPC as a reach route for non-tailnet placements |
| Engine AD-31, AD-33 | The QMB machine and a Windows `desktop` placement may be the home box, a second Contabo box, or the PC. Wording only |
| Library AD-10, AD-16 | The bucket is R2: config only. Nightly push from the server, restore drills unchanged |
| Library AD-11, OPEN-5 | Add Cloudflare Tunnel plus Workers VPC as the way non-tailnet providers reach the Hub without a public listener |
| Library AD-19 | Unchanged: `primary = server` on whatever box is the home |

If he drops owned servers entirely, AD-30, AD-28 (no central relay), Library AD-11 (no Hub host), AD-10 (no server copy) and AD-19 (primary goes back to the PC, so nothing lands while it sleeps) would all need redesign. **Not recommended.**

### 5.3 The nine server PRs

| PR | Moving the home to another Linux VPS | Adding Cloudflare beside it |
|---|---|---|
| **PRB-S** (probes) | **Unchanged in code**, adapted in wording: run on the new home host | Unchanged |
| **LIB4** (Hub, claims, server primary, purge) | **Unchanged**: `qmx node setup` targets any Ubuntu box. The bucket remote is R2 by config | Unchanged; Tunnel exposure of the Hub would be a later addition |
| **RTRP** (passes, key safe, central relay) | **Unchanged**: the central relay lives on the new home | Unchanged; Cloudflare placements use `relay: central` |
| **REM** (remote worker and sidecar) | **Adapted by name only**: the `contabo` placement row in `E/settings.py` and E57 run on the new home | **Unchanged**; Cloudflare needs one **new** connector PR after REM (Worker + `http_api` spec + smoke test). That is outside the 58 and goes through the lead's backlog (no unplanned PRs in a run) |
| **TRG2b** (event triggers on the ref log) | **Unchanged** | Unchanged |
| **APP2b** (app homes across machines) | **Unchanged** | Unchanged |
| **OPS2** (server runs seen on the PC) | **Unchanged** | Unchanged |
| **ADOPT** (adopt a run whose home died) | **Unchanged** | Unchanged |
| **RUN1b** (delete old remote runs) | **Unchanged**: AD-57 already gates it on E57 "on a real placement (Contabo or one burst provider)" | Unchanged |

None is replaced. The build plan's "his server step" (`HARDENING-PLAN.md` line 54: SSH over Tailscale, an optional `/login` there) applies to any owned Linux box.

---

## 6. Logs, monitoring and resource use on his PC

- QMX's own path is the main view: every host and remote sidecar sends one heartbeat row (CPU, RSS, machine minutes, capacity in use). Runs, cards, spans and inbox items forward to the PC over the tailnet (AD-65, OPS2). Remote logs and traces land in the Library (Library AD-13).
- Provider readings add to this. Cloudflare Workers Logs keep container logs 7 days and export by Logpush. Its dashboards are reached by the copilot through MCP (AD-32). Contabo has a control panel and API.
- Cost per placement is `machine minutes × cost_rate` on run cards (AD-32). For Cloudflare the rate is about $0.026 per agent-hour packed; for owned boxes it is the flat monthly price.

---

## 7. Connecting machines from the QMX UI (operator addition)

### 7.1 How others do it

**T3 Code** (Theo / Ping Labs; open source at `github.com/pingdotgg/t3code`) **[retrieved, docs/user/remote-access.md, background-service.md, outside-agents.md, t3-connect-troubleshooting.md]**
1. **One command or one switch on the machine.** `t3 connect` on a command-line host, or **Settings → Connections → T3 Connect** in the desktop app.
2. **Sign in by short code.** Over SSH, the CLI prints a browser link and a short code. He opens it on any device, checks the code matches, and approves. "The CLI continues on its own, so you do not need to forward an OAuth callback port."
3. **It keeps running.** Setup offers a background service (`t3 service install`; a systemd user service with lingering on Linux, a login item on macOS; "Windows background services are not supported"). `t3 update` restarts it after asking.
4. **No ports to open.** T3 Connect goes device → T3 Connect (checks sign-in and the host's link) → **the host's tunnel ("cloudflared on the host")**, which dials out to Cloudflare on port 7844 → T3 Code on the host.
5. **Other ways in, same machine:**
   - Pairing link or QR code over LAN or Tailscale (`t3 pair`, `t3 serve --tailscale-serve`).
   - **Desktop-managed SSH:** he types `user@host`, and the app downloads the server to `~/.t3/runtime`, starts or reuses it, and opens the port forward.
6. **Routes.** One machine can have several routes (LAN, Tailscale, VPN, public URL, SSH, Connect). The app learns LAN and Tailscale addresses automatically, connects over "the first route that answers", and re-checks the earlier ones every minute.
7. **Credentials and work stay on the machine.** "Projects, provider credentials, and agent work stay on the remote machine." Claude Code's own login is used there (`CLAUDE_CONFIG_DIR` per account).
8. **Permissions per paired device.** Scoped grants (`--scope orchestration:read`, `terminal:operate`, `filesystem:write` and others). Sessions can be revoked. Read-only connections can watch.
9. **Load balancing across machines.** "Auto balance" picks a machine for new threads by free CPU and memory, with per-machine **Prefer / Normal / Less often / Manual only**. Existing threads stay where they started.
10. **Seeing and talking to the remote agent.**
    - The activity log streams tool calls live (output updates while a command runs).
    - Terminals attach.
    - **Browser tabs belong to the environment** and stream to any device. Agents keep using them while no device is connected. He can "Take control" and "release control".
    - A device panel streams simulators.
    - An MCP URL (`https://<environment>/mcp`) lets outside agents read and steer threads after a sign-in he approves.

**Amp runners** **[retrieved, ampcode.com/docs/cli/runners]**
- `amp --no-tui --runner-id <name>` on any machine signed in to his account. It appears in the web app's location picker.
- `--desktop` gives a Desktop tab (WebRTC, then TURN, then Amp's relay). `--remote-control-terminal` gives a Terminal tab.
- `--amp-env` pulls secrets per thread from ampcode.com "without logging in to that machine".
- It self-updates when no thread runs. Claude Code mode runs `claude` with his plan on that machine.

**Cursor self-hosted "My Machines"** **[retrieved, cursor.com/docs/cloud-agent/self-hosted, …/my-machines, …/computer-use]**
- `agent login`, then `agent worker start --name my-devbox`. The worker "opens an outbound connection to Cursor"; "no inbound ports or firewall changes are required".
- It appears under **My Machines** in the "Run on" menu.
- **The agent loop runs in Cursor's cloud; tool calls execute on the machine.** This is the same split as QMX's `runner_outside` (harness outside, tools inside).
- `--identity-socket` lets a run mint short-lived OIDC tokens that name its owner. This is QMX's run pass idea.
- `--computer-use`, `--share-desktop` (Linux: watch or take control) and `--connect-workspace` (files, changes, terminal, ports).
- Team Pools with a "controller" scale workers. Templates exist for Cloudflare Containers, Modal, E2B, Daytona and Vercel.

**Cloudroom core** **[retrieved, github.com/davidondrej/cloudroom-core README]**
- "One Rust service per machine". Installs on Ubuntu 24.04 with one script, reached "with Tailscale".
- The desktop app connects "with a URL and token, no account needed".
- Agents run as a separate Linux user without `sudo`. History stays on the machine's disk.

**Conductor** **[retrieved, conductor.build home and changelog only]**
- It now says "Run a team of coding agents in the cloud" and "Bring your own subscriptions and keys". Version 0.91.2 "Works with cloud workspaces". Its connect flow was not documented on the pages read.

### 7.2 The flow QMX should use [inferred, mapped to the ADs]

**Step by step, from the Machines list (Settings):**
1. **"Add machine"** offers three choices:
   - **(a) A server I can SSH into.** He types `user@host` or picks an SSH alias (T3's desktop-managed SSH).
   - **(b) Run one command on the machine.** QMX shows `qmx node connect` with a one-time code (T3 `t3 connect`, Cursor `agent worker start`, Amp runner).
   - **(c) A provider** (Cloudflare, Fly, Modal, E2B, Amp…). This starts the existing `provider-onboarding` copilot flow (AD-30).
2. **Pairing.** For (a) QMX installs `qmx-node` over SSH and pairs it automatically. For (b) the machine prints the short code and QMX shows the same code; he confirms they match. This is AD-28's single-use pairing code (32-character alphabet, 1-hour TTL, lockout after five tries, never logged), shown both sides like T3.
3. **Install as a service.** `qmx-node` installs itself as a systemd service (owned Linux) and survives reboots. Updates drain first: no new work, running steps finish (AD-30 `qmx node update`; Amp and T3 both do this).
4. **Connectivity.** Outbound only. Routes are tried in order: **tailnet first** (Library AD-11), then **Cloudflare Tunnel** for machines that cannot join the tailnet (answers OPEN-5). The UI shows the route in use. QMX re-checks earlier routes every minute (T3's rule).
5. **Credentials and identity.**
   - The machine gets the pairing key and a host pass (AD-28, AD-65).
   - Provider keys come from the key safe only if the row says `relay: local`. The default for every non-owned machine is `central`: no key there.
   - Each node attempt gets a run pass, like Cursor's per-run OIDC tokens.
   - A Claude or GPT plan login happens only on owned machines, by him, with `qmx node login` (AD-28).
6. **Preflight and smoke test.** The row walks `available → configured → authorized → reachable → healthy` (AD-30). Then a one-node test runs, and the result card appears.
7. **It shows up.** The machine appears in the Machines list and in every "Run on" picker (`runs_on` order, AD-30), with its version, capacity readings and route.

**What the machine runs:** `qmx-node` (the runner: a harness host for `runner_outside` agent loops, plus the worker that starts containers). The local relay only on owned machines with `relay: local`. The run sidecar inside each container or process (Library AD-13). Optionally Docker with gVisor, and the Cua Driver on desktop placements (AD-33).

**Watching and talking to a remote agent (copy T3 and Amp):**
- A **live activity log** on the run card: tool calls stream as spans (AD-15, AD-34 "one span per tool call"), with command output updating live.
- **Terminal attach** to the attempt (read-only by default).
- **Desktop or browser live view with Take over / Hand back** (AD-44's epoch lease; AD-32's `watch: true`). It streams only while open.
- **Talk to it:** a message box on a running agent node that queues his message for the next turn. **Open question for the lead:** the ADs cover inbox answers (AD-65, forwarded to the home ledger) and `delegate` helpers that "report back between turns" (AD-41). I did not find a rule for him **steering** a running engine agent mid-run. If it is missing, it belongs in BACKLOG, not in this run.

**Copy, and where it maps:**

| Copy from | QMX home | Status |
|---|---|---|
| One command or one button; device-code confirm | AD-28 pairing; AD-30 onboarding | designed; add the "code shown both sides" UI |
| Background service, update when idle | AD-30 `qmx node update` drains | designed |
| Outbound tunnel, no open ports | Library AD-11 tailnet first; Cloudflare Tunnel for the rest | add Tunnel as a route (OPEN-5) |
| Several routes per machine, first that answers | Machines list route column | new UI item |
| Auto balance with Prefer / Less often / Manual only | `runs_on` order plus AD-58 capacity spill | add per-machine preference to the placement row (UI) |
| Agent loop outside, tools on the machine (Cursor) | AD-25 `runner_outside` | designed |
| Per-run short-lived identity (Cursor OIDC) | AD-28 run pass | designed |
| Secrets pulled per run, not stored on the machine (Amp `--amp-env`) | AD-28 relay (`central`) and declared tool keys | designed |
| Live tool log, terminal, desktop, take-over | AD-15, AD-32, AD-44 | designed; terminal attach is a UI item |
| Steer a running agent | — | gap; to BACKLOG via the lead |
| Scoped device permissions, revoke | AD-28 revocation list; Library principals | add "Revoke machine" (UI) |

**UI items for the UI session** (to add to `UI-HANDOFF.md` §9 by the lead):
1. "Add machine" with the three choices; a short-code confirm screen shown on both sides.
2. Per machine: route in use and route list; "Revoke machine"; a "Prefer / Normal / Less often / Manual only" picker.
3. On a run card: a live tool log, "Open terminal (read-only)", the desktop or browser view with Take over, and a message box if steering is designed.
4. Cost per machine: flat monthly for owned boxes, agent-hours × rate for Cloudflare and other burst rows.

---

## 8. Open questions (each with a recommendation)

1. **December size.** Recommend VPS 12 (48 GB, $24-30) unless the server probes show sessions far below 1.5 GB; then VPS 8.
2. **His Contabo payment concern.** It is not stated in the seed. If payment is the blocker, Oracle Always Free (card needed for identity only) is the fallback home. Cloudflare billing is by card (not checked further).
3. **Fly.io or Cloudflare for burst.** Fly is about half the price per agent-hour and has real VMs. Cloudflare has far better agent tooling, R2 in the same account, and the Tunnel and VPC reach. Recommend Cloudflare first for one account and one bill; add Fly later through the same seam if burst spend grows.
4. **Linux desktop in a Cloudflare container.** Not documented. Probe before promising browser-as-desktop work there; until then, headless browsers via Browser Run or Chrome on the home server.
5. **Steering a running remote agent.** See §7.2. The lead decides whether it is a gap.

---

## 9. Sources (all retrieved 2026-10-21)

Cloudflare:
- https://developers.cloudflare.com/containers/platform/limits/
- https://developers.cloudflare.com/containers/platform/pricing/
- https://developers.cloudflare.com/containers/faq/
- https://developers.cloudflare.com/sandbox/llms.txt
- https://developers.cloudflare.com/sandbox/concepts/lifetime/
- https://developers.cloudflare.com/sandbox/concepts/security/
- https://developers.cloudflare.com/sandbox/network/
- https://developers.cloudflare.com/sandbox/coding-agents/claude-code/
- https://developers.cloudflare.com/r2/pricing/
- https://developers.cloudflare.com/browser-run/pricing/
- https://developers.cloudflare.com/browser-run/limits/
- https://developers.cloudflare.com/browser-run/features/human-in-the-loop/
- https://developers.cloudflare.com/workers/platform/pricing/
- https://developers.cloudflare.com/durable-objects/platform/pricing/
- https://developers.cloudflare.com/workflows/reference/limits/
- https://developers.cloudflare.com/queues/platform/pricing/
- https://developers.cloudflare.com/mesh/
- https://developers.cloudflare.com/mesh/platform/
- https://developers.cloudflare.com/workers-vpc/llms.txt
- https://developers.cloudflare.com/tunnel/llms.txt
- https://developers.cloudflare.com/agent-setup/
- https://developers.cloudflare.com/agent-setup/claude-code/
- https://developers.cloudflare.com/agents/model-context-protocol/mcp-servers-for-cloudflare/

Other providers:
- Vercel: https://vercel.com/docs/sandbox/pricing
- Amp: https://ampcode.com/docs/orbs, https://ampcode.com/docs/orbs/sizes-and-costs, https://ampcode.com/docs/cli/runners
- Contabo: https://contabo.com/en-us/vps/, https://contabo.com/en/vps/cloud-vps-core-6/ (Windows licence), https://contabo.com/en-us/object-storage/
- Hetzner: https://www.hetzner.com/cloud/, https://www.hetzner.com/cloud/regular-performance/
- Oracle: https://www.oracle.com/cloud/free/, https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- DigitalOcean: https://www.digitalocean.com/pricing/droplets, https://docs.digitalocean.com/products/spaces/details/pricing/
- AWS: https://aws.amazon.com/lightsail/pricing/
- Fly.io: https://fly.io/docs/about/pricing/
- Modal: https://modal.com/pricing
- E2B: https://e2b.dev/pricing
- Daytona: https://www.daytona.io/pricing
- Cua: https://cua.ai/pricing
- Tailscale: https://tailscale.com/pricing

Agent tools and connect flows:
- Claude Code: https://code.claude.com/docs/en/setup, https://code.claude.com/docs/en/agent-sdk/hosting
- T3 Code: https://github.com/pingdotgg/t3code/blob/main/docs/user/remote-access.md, …/background-service.md, …/outside-agents.md, …/t3-connect-troubleshooting.md, …/activity-log.md, …/providers-claude.md
- Cursor: https://cursor.com/docs/cloud-agent/self-hosted, https://cursor.com/docs/cloud-agent/self-hosted/my-machines, https://cursor.com/docs/cloud-agent/self-hosted/computer-use
- Cloudroom: https://github.com/davidondrej/cloudroom-core (README)
- Conductor: https://www.conductor.build/, https://www.conductor.build/changelog

Repo:
- `research/methodology/26-operator-rulings-and-alignment.md`
- `29-environments-and-deployment.md`, `31-cua.md`, `32-amp-orbs-and-cua.md`
- `architecture/workflow-engine/ARCHITECTURE-SPINE.md` (AD-20, AD-24, AD-25, AD-28, AD-30 to AD-33, AD-44, AD-57, AD-58, AD-65)
- `architecture/library-and-data/ARCHITECTURE-SPINE.md` (AD-10 to AD-13, AD-16, AD-19), `OPEN-DECISIONS.md` (OPEN-5)
- `HARDENING-PLAN.md` (PRB-S, LIB4, RTRP, REM, TRG2b, APP2b, OPS2, ADOPT, RUN1b)
- `UI-HANDOFF.md` §9
- `D:\QMX-worktrees\bld-trg2a\qmx-agents\packages\qmx-remote\src\qmx_remote\providers.py`
