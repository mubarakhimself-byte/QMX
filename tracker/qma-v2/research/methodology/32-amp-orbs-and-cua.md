# 32 — Amp Orbs as QMX's compute, and Cua on top

The lead read these on 2026-10-16 in the built-in browser:
- ampcode.com/what-are-orbs
- /docs/orbs
- /docs/orbs/desktop
- /docs/pricing
- /docs/cli/runners
- /docs/orbs/event-driven
- /docs/orbs/agent-to-agent

The sizes, customizing and automations pages were read earlier in the same session.

## What Amp gives

| Feature | Fact |
|---|---|
| **Orbs** | Remote machines, one per thread. They run as E2B microVMs on GCP us-west1, on Debian 12. Billed by the minute. A paused orb costs $0. They pause 5 min after the agent's work ends or 20 min after your last interaction. |
| Sizes | tiny 1 CPU / 2 GB at $0.08/h; small $0.17; medium $0.33; large 8 CPU / 16 GB at $0.66; xxlarge 16 CPU / 32 GB at $1.32; 3xlarge (Gigawatt only) $2.13. All have 60 GB disk. |
| Spawn pacing | A burst of 20 orbs, then 1 new orb every 5 minutes. Later starts queue; they don't fail. |
| Setup | `.agents/setup` builds a snapshot, reused for up to 72 h. `.agents/resume` runs on every wake. Docker can be installed and run as a supervised service. FUSE mounts work (shared disks). Tailscale is supported through OIDC workload identity with no stored secret. |
| **Runners** | `amp --no-tui --runner-id <id>` turns **any machine you own** into a place Amp threads run, for free on the Hobby tier. `--desktop` shares a virtual Linux desktop. **Claude Code mode** runs the official `claude` binary on the runner, signed in with his Claude Pro/Max plan. |
| **Desktop** | A high-resolution Linux desktop in the orb, with Chrome. Amp drives Chrome for web tasks while he watches, and he can take over for sign-ins and CAPTCHAs. General "computer use" there is described as **early and unsupported**. |
| **Automations** | A per-thread schedule written in plain words, once or repeating. It wakes the thread with its full context. One schedule per thread. A failed run pauses the automation. |
| **Webhooks** | A plugin creates a public URL. Delivery is at least once and wakes the orb. Retries back off up to 5 min; an event is dropped after 1 h. Rate limit: 10/min. |
| **Agent to agent** | Agents start other agents in orbs, in other projects, or **on runners**, and exchange messages and files. |
| Phone | macOS and iOS apps for watching, answering and approving. |
| **Pricing** | Hobby is free: pay-as-you-go orbs, **own runners free**, bring your own keys, your ChatGPT/Claude subscriptions, no token markup. Megawatt is **$20/month with 45,000 orb-minutes** (larger orbs use the allowance faster). Teams cost nothing extra. |

## Fit with QMX (rulings 22-25, 53-57; the Rivet principle)

- **What it solves:** the easiest setup by far, plus most of the Hermes-style features he wants: schedules, webhooks, agent-to-agent, a desktop he can watch, the phone apps, and cheap burst compute that costs nothing while paused. **Runners make his own server a first-class place at no fee.**
- **The architectural catch:** Amp is itself an agent harness and control plane. If QMX workflows *were* Amp threads, Amp would own the loop, the schedule, the state and the traces. That makes a second engine, which conflicts with "one engine" (22) and "QMX's own harness" (24), and QMX's data and run history would sit in Amp's cloud.
- **The clean way to use it: Amp as a compute provider behind our `WorkerPort`.**
  - QMX's engine stays the brain (ledger, scheduler, pool, traces, Library).
  - A node runs `amp -x … --executor runner:<id>` on his server, or `amp -ox … --orb-size …` for burst. QMX keeps the returned result and artifacts as the node's output.
  - Orbs join his tailnet and reach the Library Hub.
  - Our own `qmx-worker` can also run inside an orb or a runner as a plain process, started by `.agents/resume` or a service, with Amp used only for machine lifecycle.
- **Limits:**
  - Linux only, so there is no Windows desktop for MT5 or cTrader in an orb.
  - Orbs are E2B underneath, in us-west1.
  - There is no public SDK for spawning orbs from code beyond the CLI.
  - One schedule per thread.
  - Webhooks are rate-limited.

## Cua + Amp: computer use

- **In an orb or a Linux runner:** install `cua-driver` from `.agents/setup` and expose it as an MCP tool. The orb Desktop is a Linux X11/virtual desktop, which Cua supports. This adds Cua's bounded permission manifests, background input and logged-in-profile rules on top of Amp's desktop. That covers web apps (TradingView web, YouTube) and Linux apps.
- **Windows apps (MT5, cTrader):** these cannot run in orbs. The options are:
  - his PC, with Cua Driver on Windows in the interactive session (background mode);
  - a Windows VM on a KVM-capable server (Cua's `windows:2022` image);
  - a Windows Amp runner, if Amp's runner supports Windows (unverified).
- **Order of trust:** the read-only browser first (ruling 30), then Cua "act as me" behind a bounded manifest, with money always read-only through the harness hook.

## VM provider advice

1. **His own server as an Amp runner.** It's free, ready today, and Claude Code mode uses his plan on his machine. This is the base.
2. **Amp orbs for burst.** Use pay-as-you-go, or Megawatt at $20 once the usage justifies it. It's cheaper and simpler than going to E2B or Modal directly.
3. **More owned capacity, if needed:** a cheap VPS (Contabo/Hetzner class) added as another runner. DigitalOcean and AWS cost more for the same thing.
4. **Windows desktops for MT5/cTrader:** a KVM-capable box running Cua's Windows image, or his PC.

## Decisions for him

- **(a)** Is Amp acceptable as an outside control plane for *compute only*, with QMX's engine still the brain? The alternative is Amp running whole workflows as Amp threads, which brings vendor lock-in and a second engine.
- **(b)** Can his server's specs (RAM, cores, KVM) host about 20 runs plus an Amp runner?
