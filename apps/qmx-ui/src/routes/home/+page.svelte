<script lang="ts">
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import ArrowRight from "@lucide/svelte/icons/arrow-right";
  import Plug from "@lucide/svelte/icons/plug";
  import Package from "@lucide/svelte/icons/package";
  import Database from "@lucide/svelte/icons/database";
  import MessagesSquare from "@lucide/svelte/icons/messages-square";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import * as Dialog from "$lib/components/ui/dialog";
  import MiniAppShell from "$lib/workbench/MiniAppShell.svelte";
  import { WidgetBoard } from "$lib/workbench/board.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import TickerTape from "$lib/qmx/TickerTape.svelte";
  import CoverArt from "$lib/qmx/CoverArt.svelte";
  import LineChart from "$lib/qmx/LineChart.svelte";
  import { PIPELINE, type Entity } from "$lib/qmx/entities";
  import { equityWalk } from "$lib/qmx/charts";
  import { DEMO_ENTITIES } from "$lib/demo/assets";
  import { HEADLINES } from "$lib/demo/feeds";
  import { DEMO_CALENDAR } from "$lib/demo/data";
  import { cn } from "$lib/utils";

  // Home is built from the same widgets as mini apps, so it is customisable
  // and consistent. Demo content is labelled; with demo mode off it shows
  // the fresh-install setup board instead of empty boxes.
  const demo = workbench.demoMode;

  type Approval = {
    id: string;
    title: string;
    meta: string;
    card: [string, string][];
  };
  const APPROVALS: Approval[] = [
    {
      id: "a1",
      title: "Promote EURUSD H1 GBM to paper book FX-P",
      meta: "Asked 2h ago by the Researcher quant",
      card: [
        ["Bot", "EURUSD H1 GBM v7 · fp1:9c41…e2a0"],
        ["Book", "FX-P (paper)"],
        ["Risk per trade", "0.5% of book"],
        [
          "Evidence",
          "2 confirmation runs: walk-forward Sharpe 1.42, significance p = 0.012",
        ],
        [
          "Then",
          "Activation is a second step, effective at the next day boundary",
        ],
      ],
    },
    {
      id: "a2",
      title: "Raise Gold Fade drawdown limit to 5%",
      meta: "Paused at −4.0% · asked 40m ago",
      card: [
        ["Bot", "Gold Fade v5 · fp1:41ab…77c3"],
        ["Book", "GOLD-P (paper)"],
        ["Change", "Drawdown limit 4% → 5%"],
        [
          "Why",
          "Stopped after a volatility spike; Monte Carlo p95 drawdown is 4.6%",
        ],
      ],
    },
  ];
  let open = $state<Approval | null>(null);

  const BRIEF = [
    {
      tone: "text-success",
      dot: "bg-success",
      kind: "Finished",
      title: "EURUSD H1 model beat its benchmark",
      body: "Walk-forward 2024–2026: Sharpe 1.42, max drawdown −6.8%.",
      href: "/library/btc-breakout",
    },
    {
      tone: "text-warning",
      dot: "bg-warning",
      kind: "Needs you",
      title: "Two approvals waiting",
      body: "A paper promotion and a drawdown-limit change.",
      href: null,
    },
    {
      tone: "text-destructive",
      dot: "bg-destructive",
      kind: "Heads up",
      title: "Gold Fade hit its drawdown limit",
      body: "Paused at −4.0% on paper. No live exposure.",
      href: "/library/eth-mr",
    },
  ];
  const JOBS = [
    {
      name: "Scanning MQL5 articles for exit ideas",
      who: "Researcher quant",
      pct: 41,
      state: "running",
    },
    {
      name: "Backtest · USDJPY carry 2019–2026",
      who: "Nightly evidence",
      pct: 73,
      state: "running",
    },
    {
      name: "Refreshing crypto majors data",
      who: "data.refresh",
      pct: 12,
      state: "running",
    },
    {
      name: "Sweep · US500 trend across indices",
      who: "Analyst quant",
      pct: 0,
      state: "unknown",
    },
  ];
  // QMA: quants are persistent actors; agents run; subagents are leaves.
  const AGENTS = [
    {
      name: "Researcher",
      kind: "Quant · research desk",
      doing: "Scanning articles, 2 subagents",
      state: "running",
    },
    {
      name: "Analyst",
      kind: "Quant · analysis desk",
      doing: "Lost contact during a sweep",
      state: "unknown",
    },
    {
      name: "Nightly evidence",
      kind: "Workflow agent",
      doing: "Walk-forward for 3 bots",
      state: "running",
    },
    {
      name: "Trader",
      kind: "Quant · trading desk",
      doing: "Idle; watches news windows",
      state: "idle",
    },
  ];
  const AGENT_TONE: Record<string, string> = {
    running: "bg-info",
    unknown: "bg-warning",
    idle: "bg-muted-foreground/50",
  };
  const TICKER = [
    { sym: "BTC", px: "64,210", chg: 1.83 },
    { sym: "ETH", px: "3,118", chg: 2.41 },
    { sym: "SOL", px: "141.2", chg: -3.1 },
    { sym: "EURUSD", px: "1.0883", chg: -0.4 },
    { sym: "GBPUSD", px: "1.2745", chg: 0.12 },
    { sym: "USDJPY", px: "148.32", chg: 0.31 },
    { sym: "XAUUSD", px: "2384.1", chg: -0.22 },
    { sym: "US500", px: "5531.6", chg: 0.57 },
    { sym: "NAS100", px: "19,842", chg: 0.94 },
  ];
  const MARKETS: [string, number][] = [
    ["BTC", 1.83],
    ["ETH", 2.41],
    ["SOL", -3.1],
    ["XRP", 0.6],
    ["EURUSD", -0.4],
    ["GBPUSD", 0.12],
    ["USDJPY", 0.31],
    ["XAUUSD", -0.22],
    ["US500", 0.57],
    ["NAS100", 0.94],
    ["DE40", -0.18],
    ["WTI", -1.2],
  ];
  const heat = (v: number) =>
    `background: color-mix(in oklab, ${v >= 0 ? "var(--success)" : "var(--destructive)"} ${Math.round((Math.min(Math.abs(v) / 3, 1) * 0.55 + 0.08) * 100)}%, transparent)`;
  const paper = equityWalk(31, 90, 0.0011, 0.006);
  // Both indexed to 100 at the start so different account sizes compare.
  const live = equityWalk(57, 90, 0.0007, 0.005);
  const byStage = (s: string) =>
    DEMO_ENTITIES.filter(
      (e: Entity) => (e.kind === "bot" || e.kind === "model") && e.stage === s,
    );
  const HYPOTHESES = [
    "Survival-model exits for breakouts",
    "News-sentiment filter for gold",
    "Regime gate for US500 trend",
  ];
  let newsFilter = $state<string | null>(null);

  const W = {
    brief: { id: "brief", title: "While you were away", size: "lg" },
    equity: { id: "equity", title: "Accounts", size: "lg" },
    approvals: { id: "approvals", title: "Waiting for you", size: "md" },
    running: { id: "running", title: "Running", size: "md" },
    agents: { id: "agents", title: "Agents", size: "md" },
    pipeline: {
      id: "pipeline",
      title: "Strategy pipeline",
      size: "full",
      tall: true,
    },
    news: { id: "news", title: "News", size: "lg", tall: true },
    calendar: { id: "calendar", title: "Next events", size: "md" },
    markets: { id: "markets", title: "Markets today", size: "lg" },
  } as const;
  const SETUP = {
    connect: { id: "connect", title: "1 · Connect the daemon", size: "md" },
    data: { id: "data", title: "2 · Add market data", size: "md" },
    app: { id: "app", title: "3 · Install a mini app", size: "md" },
    ask: { id: "ask", title: "4 · Ask the copilot", size: "md" },
  } as const;
  const board = new WidgetBoard(
    demo
      ? {
          Today: [
            W.brief,
            W.equity,
            W.approvals,
            W.running,
            W.agents,
            W.pipeline,
            W.news,
            W.calendar,
          ],
          Markets: [W.markets, W.news, W.calendar, W.equity],
          Agents: [W.agents, W.running, W.approvals],
        }
      : { "Get started": [SETUP.connect, SETUP.data, SETUP.app, SETUP.ask] },
  );
</script>

<svelte:head><title>Home · QMX</title></svelte:head>

{#snippet strip()}<TickerTape
    items={TICKER}
    label="Markets (sample)"
  />{/snippet}

{#snippet body(id: string)}
  {#if id === "brief"}
    <div class="grid h-full gap-2 sm:grid-cols-3">
      {#each BRIEF as b (b.kind)}
        <article class="well flex flex-col gap-1.5 rounded-lg p-3">
          <p
            class="flex items-center gap-2 text-[11px] font-medium tracking-wider uppercase {b.tone}"
          >
            <span class="size-1.5 rounded-full {b.dot}"></span>{b.kind}
          </p>
          <p class="text-sm font-semibold">{b.title}</p>
          <p class="text-muted-foreground text-xs leading-snug">{b.body}</p>
          <div class="mt-auto">
            {#if b.href}
              <Button
                size="sm"
                variant="ghost"
                class="-ml-2"
                href={resolve(b.href as "/")}>Open <ArrowRight /></Button
              >
            {:else}
              <Button size="sm" onclick={() => (open = APPROVALS[0])}
                >Review</Button
              >
            {/if}
          </div>
        </article>
      {/each}
    </div>
  {:else if id === "equity"}
    <div class="flex h-full flex-col gap-2">
      <div class="grid grid-cols-2 gap-3">
        <div>
          <p class="text-muted-foreground flex items-center gap-1.5 text-xs">
            <span
              class="size-2 rounded-full"
              style="background: var(--tone-live)"
            ></span>Live · IDX-L
          </p>
          <p class="num text-2xl font-semibold">$48,630</p>
          <p class="num text-success text-xs">▲ +$66.80 today</p>
        </div>
        <div>
          <p class="text-muted-foreground flex items-center gap-1.5 text-xs">
            <span
              class="size-2 rounded-full"
              style="background: var(--tone-paper)"
            ></span>Paper · 3 books
          </p>
          <p class="num text-2xl font-semibold">$104,812</p>
          <p class="num text-success text-xs">▲ +$1,204 today</p>
        </div>
      </div>
      <div class="min-h-0 flex-1">
        <LineChart
          series={[
            { label: "Paper", values: paper, color: "var(--tone-paper)" },
            { label: "Live", values: live, color: "var(--tone-live)" },
          ]}
          height={130}
        />
      </div>
    </div>
  {:else if id === "approvals"}
    <ul class="flex flex-col gap-2">
      {#each APPROVALS as a (a.id)}
        <li class="well flex items-center gap-3 rounded-lg p-3">
          <ShieldCheck class="text-warning size-4 shrink-0" />
          <span class="min-w-0 flex-1"
            ><span class="block text-sm font-medium">{a.title}</span><span
              class="text-muted-foreground block text-xs">{a.meta}</span
            ></span
          >
          <Button size="sm" variant="outline" onclick={() => (open = a)}
            >Review</Button
          >
        </li>
      {/each}
    </ul>
  {:else if id === "running"}
    <ul class="flex flex-col gap-3">
      {#each JOBS as j (j.name)}
        <li>
          <div class="flex justify-between gap-2 text-sm">
            <span class="truncate">{j.name}</span>
            <span
              class={cn(
                "num text-xs",
                j.state === "unknown"
                  ? "text-warning"
                  : "text-muted-foreground",
              )}>{j.state === "unknown" ? "unknown" : j.pct + "%"}</span
            >
          </div>
          <div class="text-muted-foreground text-xs">{j.who}</div>
          {#if j.state !== "unknown"}<div
              class="bg-muted mt-1 h-1.5 rounded-full"
            >
              <div
                class="bg-info h-1.5 rounded-full"
                style="width: {j.pct}%"
              ></div>
            </div>{/if}
        </li>
      {/each}
    </ul>
  {:else if id === "agents"}
    <ul class="flex flex-col">
      {#each AGENTS as a (a.name)}
        <li class="flex items-center gap-3 border-b py-2 last:border-0">
          <span class={cn("size-2 shrink-0 rounded-full", AGENT_TONE[a.state])}
          ></span>
          <span class="min-w-0 flex-1"
            ><span class="block text-sm font-medium"
              >{a.name}
              <span class="text-muted-foreground text-xs font-normal"
                >{a.kind}</span
              ></span
            ><span class="text-muted-foreground block truncate text-xs"
              >{a.doing}</span
            ></span
          >
          <span class={cn("text-xs", a.state === "unknown" && "text-warning")}
            >{a.state}</span
          >
        </li>
      {/each}
    </ul>
    <p class="text-muted-foreground mt-2 text-xs">
      Unknown means contact was lost; it is not a failure. Agents never place
      orders or size trades.
    </p>
  {:else if id === "pipeline"}
    <div class="grid h-full gap-2 md:grid-cols-5">
      {#each PIPELINE as stage (stage)}
        {@const items = byStage(stage)}
        <section
          class="well flex min-h-0 flex-col rounded-lg p-2"
          aria-label={stage}
        >
          <p
            class="flex items-center justify-between px-1 pb-1.5 text-sm font-medium"
          >
            {stage}<span class="num text-muted-foreground text-xs"
              >{stage === "Hypothesis" ? HYPOTHESES.length : items.length}</span
            >
          </p>
          <div class="flex min-h-0 flex-1 flex-col gap-1.5 overflow-auto">
            {#if stage === "Hypothesis"}
              {#each HYPOTHESES as h (h)}
                <div class="surface rounded-md px-2.5 py-2 text-sm">
                  {h}<span class="text-muted-foreground block text-xs"
                    >Stage 0 · cites Library</span
                  >
                </div>
              {/each}
            {:else}
              {#each items as e (e.id)}
                <a
                  href={resolve("/library/[id]", { id: e.id })}
                  class="surface flex overflow-hidden rounded-md transition-transform hover:-translate-y-0.5"
                >
                  <CoverArt
                    kind={e.kind}
                    seed={e.id}
                    series={e.spark}
                    class="w-10 shrink-0"
                  />
                  <span class="min-w-0 px-2.5 py-2">
                    <span class="block truncate text-sm font-medium"
                      >{e.name}</span
                    >
                    <span class="num text-muted-foreground block text-xs"
                      >{e.measures[0].label}
                      {e.measures[0].value} · {e.measures[1].value}</span
                    >
                  </span>
                </a>
              {:else}
                <p class="text-muted-foreground px-1 text-xs">
                  Nothing here yet
                </p>
              {/each}
            {/if}
          </div>
        </section>
      {/each}
    </div>
  {:else if id === "news"}
    <div class="flex h-full flex-col gap-2">
      <div class="flex flex-wrap gap-1">
        {#each [null, "USD", "EURUSD", "XAUUSD", "BTCUSD"] as f (f ?? "all")}
          <button
            type="button"
            class={cn(
              "rounded-full border px-2.5 py-0.5 text-xs",
              newsFilter === f
                ? "bg-primary text-primary-foreground border-transparent"
                : "hover:bg-muted",
            )}
            aria-pressed={newsFilter === f}
            onclick={() => (newsFilter = f)}>{f ?? "All"}</button
          >
        {/each}
      </div>
      <ul class="min-h-0 flex-1 overflow-auto">
        {#each HEADLINES.filter((h) => !newsFilter || h.symbols.includes(newsFilter)) as h (h.time + h.title)}
          <li
            class="grid grid-cols-[3rem_minmax(0,1fr)_auto] items-start gap-2 border-b py-2 last:border-0"
          >
            <span class="num text-muted-foreground text-xs">{h.time}</span>
            <span class="min-w-0">
              <span class="block text-sm">{h.title}</span>
              <span
                class="text-muted-foreground flex items-center gap-1.5 text-xs"
                >{h.source}{#each h.symbols as s (s)}<span
                    class="bg-muted text-foreground rounded-sm px-1">{s}</span
                  >{/each}</span
              >
            </span>
            <Badge
              variant="outline"
              class={cn(
                "h-4 px-1.5 text-[10px] uppercase",
                h.impact === "high"
                  ? "text-destructive"
                  : h.impact === "medium"
                    ? "text-warning"
                    : "text-muted-foreground",
              )}>{h.impact}</Badge
            >
          </li>
        {/each}
      </ul>
    </div>
  {:else if id === "calendar"}
    <ul class="flex flex-col text-sm">
      {#each DEMO_CALENDAR[0].events as e (e.time + e.event)}
        <li class="flex gap-2 border-b py-1.5 last:border-0">
          <span class="num text-muted-foreground w-12 shrink-0">{e.time}</span>
          <span class="min-w-0 flex-1 truncate">{e.ccy} · {e.event}</span>
          <span
            class={cn(
              "text-[10px] uppercase",
              e.impact === "high"
                ? "text-destructive"
                : "text-muted-foreground",
            )}>{e.impact}</span
          >
        </li>
      {/each}
    </ul>
  {:else if id === "markets"}
    <div class="grid h-full grid-cols-3 gap-1.5 sm:grid-cols-4 xl:grid-cols-6">
      {#each MARKETS as [sym, chg] (sym)}
        <div
          class="flex flex-col justify-center rounded-md px-2.5 py-2"
          style={heat(chg)}
        >
          <span class="text-xs font-medium">{sym}</span>
          <span class="num text-sm font-semibold"
            >{chg >= 0 ? "▲ +" : "▼ −"}{Math.abs(chg).toFixed(2)}%</span
          >
        </div>
      {/each}
    </div>
  {:else if id === "connect"}
    <div class="flex h-full flex-col gap-2">
      <Plug class="text-muted-foreground size-6" />
      <p class="text-sm">
        Start the QMX daemon on this machine, then pair this window with it.
      </p>
      <Button
        size="sm"
        variant="outline"
        class="mt-auto self-start"
        href={resolve("/settings")}>Open Settings</Button
      >
    </div>
  {:else if id === "data"}
    <div class="flex h-full flex-col gap-2">
      <Database class="text-muted-foreground size-6" />
      <p class="text-sm">
        Download history from a free provider or import a CSV. Everything else
        reads from it.
      </p>
      <Button
        size="sm"
        variant="outline"
        class="mt-auto self-start"
        href={resolve("/settings")}>Data & sources</Button
      >
    </div>
  {:else if id === "app"}
    <div class="flex h-full flex-col gap-2">
      <Package class="text-muted-foreground size-6" />
      <p class="text-sm">
        Apps add screens and operations. Installing is not granting; you choose
        what each may do.
      </p>
      <Button
        size="sm"
        variant="outline"
        class="mt-auto self-start"
        href={resolve("/library")}>Browse apps</Button
      >
    </div>
  {:else if id === "ask"}
    <div class="flex h-full flex-col gap-2">
      <MessagesSquare class="text-muted-foreground size-6" />
      <p class="text-sm">
        Describe a strategy idea; the copilot drafts a hypothesis with
        citations.
      </p>
      <Button
        size="sm"
        variant="outline"
        class="mt-auto self-start"
        href={resolve("/copilot")}>Open Copilot</Button
      >
    </div>
  {/if}
{/snippet}

{#if demo}
  <MiniAppShell
    {board}
    name="Home"
    demoNote="Demo dashboard. Sample numbers, approvals and jobs; nothing is live."
    {strip}
    widget={body}
  />
{:else}
  <MiniAppShell {board} name="Home" widget={body} />
{/if}

<Dialog.Root open={!!open} onOpenChange={(v) => !v && (open = null)}>
  <Dialog.Content class="sm:max-w-lg">
    {#if open}
      <Dialog.Header>
        <Dialog.Title>{open.title}</Dialog.Title>
        <Dialog.Description
          >Read the card in plain words before you sign. Nothing changes until
          you do.</Dialog.Description
        >
      </Dialog.Header>
      <dl class="flex flex-col text-sm">
        {#each open.card as [k, v] (k)}
          <div class="grid grid-cols-[8rem_1fr] gap-3 border-t py-2">
            <dt class="text-muted-foreground">{k}</dt>
            <dd>{v}</dd>
          </div>
        {/each}
      </dl>
      <Dialog.Footer>
        <Button variant="outline" onclick={() => (open = null)}>Not now</Button>
        <Button
          disabled
          title="Signing goes through the node's powers channel; needs the daemon"
          >Sign (needs daemon)</Button
        >
      </Dialog.Footer>
    {/if}
  </Dialog.Content>
</Dialog.Root>
