<script lang="ts">
  import BellDot from "@lucide/svelte/icons/bell-dot";
  import Loader from "@lucide/svelte/icons/loader";
  import History from "@lucide/svelte/icons/history";
  import AppWindow from "@lucide/svelte/icons/app-window";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import ArrowRight from "@lucide/svelte/icons/arrow-right";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import * as Dialog from "$lib/components/ui/dialog";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import WidgetFrame from "$lib/workbench/WidgetFrame.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import TickerTape from "$lib/qmx/TickerTape.svelte";
  import CoverArt from "$lib/qmx/CoverArt.svelte";
  import { PIPELINE, type Entity } from "$lib/qmx/entities";
  import { equityWalk, linePath, extent } from "$lib/qmx/charts";
  import { DEMO_ENTITIES } from "$lib/demo/assets";
  import { HEADLINES } from "$lib/demo/feeds";
  import { cn } from "$lib/utils";

  const demo = workbench.demoMode;

  // DEMO Home content: sample brief, approvals, jobs, equity and markets.
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
      meta: "Asked 2h ago by the agent",
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
      body: "Walk-forward 2024–2026: Sharpe 1.42, max drawdown −6.8%. Report saved to Library.",
      href: "/library/eurusd-h1-gbm",
    },
    {
      tone: "text-warning",
      dot: "bg-warning",
      kind: "Needs you",
      title: "Two approvals are waiting",
      body: "A paper promotion and a drawdown-limit change.",
      href: null,
    },
    {
      tone: "text-destructive",
      dot: "bg-destructive",
      kind: "Heads up",
      title: "Gold Fade hit its drawdown limit",
      body: "Paused automatically at −4.0% on paper. No live exposure.",
      href: "/library/gold-fade",
    },
  ];
  const JOBS = [
    { name: "Scanning MQL5 articles for exit ideas", pct: 41 },
    { name: "Backtest · USDJPY carry 2019–2026", pct: 73 },
    { name: "Refreshing crypto majors data", pct: 12 },
  ];
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
  const equity = equityWalk(31, 90, 0.0011, 0.006);
  const eqPath = linePath(equity, 600, 120, extent(equity));
  const byStage = (s: string) =>
    DEMO_ENTITIES.filter(
      (e: Entity) => (e.kind === "bot" || e.kind === "model") && e.stage === s,
    );
  // A hypothesis lives in QML Stage 0 before it is a bot; sample entries.
  const HYPOTHESES = [
    "Survival-model exits for breakouts",
    "News-sentiment filter for gold",
  ];
</script>

<svelte:head><title>Home · QMX</title></svelte:head>

<div class="flex h-full flex-col">
  {#if demo}
    <div
      class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs"
    >
      <FlaskConical class="text-warning size-3.5" /> Demo dashboard. Sample numbers,
      approvals and jobs; nothing is live.
    </div>
    <TickerTape items={TICKER} label="Markets (sample)" />
  {/if}

  <div class="min-h-0 flex-1 overflow-auto">
    {#if !demo}
      <div class="grid gap-3 p-3 lg:grid-cols-2">
        <WidgetFrame title="Needs attention" class="h-56"
          ><EmptyState
            class="h-full"
            icon={BellDot}
            title="Nothing needs attention"
            description="Failed and unknown jobs land here."
          /></WidgetFrame
        >
        <WidgetFrame title="Running" class="h-56"
          ><EmptyState
            class="h-full"
            icon={Loader}
            title="No jobs running"
          /></WidgetFrame
        >
        <WidgetFrame title="Recent sessions" class="h-56"
          ><EmptyState
            class="h-full"
            icon={History}
            title="No recent sessions"
          /></WidgetFrame
        >
        <WidgetFrame title="Apps" class="h-56"
          ><EmptyState
            class="h-full"
            icon={AppWindow}
            title="No apps installed"
          /></WidgetFrame
        >
      </div>
    {:else}
      <div class="mx-auto flex max-w-[1500px] flex-col gap-4 p-4">
        <!-- Hero: brief on the left, equity on the right -->
        <section
          class="grid gap-4 xl:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]"
        >
          <div class="flex flex-col gap-3">
            <div>
              <p class="text-muted-foreground text-sm">
                Wednesday 1 October · 14:32 UTC
              </p>
              <h1
                class="text-[28px] leading-tight font-semibold tracking-tight"
              >
                Three things moved while you were away.
              </h1>
            </div>
            <div class="grid gap-3 md:grid-cols-3">
              {#each BRIEF as b (b.kind)}
                <article class="surface flex flex-col gap-2 rounded-xl p-4">
                  <p
                    class="flex items-center gap-2 text-[11px] font-medium tracking-wider uppercase {b.tone}"
                  >
                    <span class="size-1.5 rounded-full {b.dot}"></span>{b.kind}
                  </p>
                  <p class="font-semibold">{b.title}</p>
                  <p class="text-muted-foreground text-sm leading-snug">
                    {b.body}
                  </p>
                  <div class="mt-auto pt-1">
                    {#if b.href}
                      <Button
                        size="sm"
                        variant="ghost"
                        class="-ml-2"
                        href={resolve(b.href as "/")}
                        >Open <ArrowRight /></Button
                      >
                    {:else}
                      <Button
                        size="sm"
                        class="-ml-0.5"
                        onclick={() => (open = APPROVALS[0])}>Review</Button
                      >
                    {/if}
                  </div>
                </article>
              {/each}
            </div>
          </div>
          <div class="surface relative overflow-hidden rounded-xl p-4">
            <p class="panel-label">Paper equity · 90 days</p>
            <p class="num mt-1 text-3xl font-semibold">$104,812</p>
            <p class="num text-success text-sm">
              ▲ +$1,204 today · +4.8% in 90 days
            </p>
            <svg
              viewBox="0 0 600 120"
              preserveAspectRatio="none"
              class="mt-3 h-28 w-full"
              aria-hidden="true"
            >
              <defs>
                <linearGradient id="eq-fill" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="0"
                    style="stop-color: var(--primary); stop-opacity: 0.35"
                  />
                  <stop
                    offset="1"
                    style="stop-color: var(--primary); stop-opacity: 0"
                  />
                </linearGradient>
              </defs>
              <path d="{eqPath} L600,120 L0,120 Z" fill="url(#eq-fill)" />
              <path
                d={eqPath}
                fill="none"
                style="stroke: var(--primary)"
                stroke-width="2"
                vector-effect="non-scaling-stroke"
              />
            </svg>
            <div
              class="text-muted-foreground mt-2 grid grid-cols-3 gap-2 text-xs"
            >
              <span
                >Open risk <span class="num text-foreground block text-sm"
                  >1.9% of 5%</span
                ></span
              >
              <span
                >Live strategies <span class="num text-foreground block text-sm"
                  >1</span
                ></span
              >
              <span
                >On paper <span class="num text-foreground block text-sm"
                  >2</span
                ></span
              >
            </div>
          </div>
        </section>

        <!-- Pipeline board -->
        <section aria-label="Strategy pipeline" class="flex flex-col gap-2">
          <div class="flex items-baseline gap-3">
            <h2 class="text-lg font-semibold">Strategy pipeline</h2>
            <p class="text-muted-foreground text-sm">
              Hypothesis to live. Paper → Live needs your promotion and
              activation.
            </p>
          </div>
          <div class="grid gap-3 md:grid-cols-5">
            {#each PIPELINE as stage (stage)}
              {@const items = byStage(stage)}
              <div class="well flex min-h-40 flex-col gap-2 rounded-xl p-2.5">
                <p
                  class="flex items-center justify-between px-1 text-sm font-medium"
                >
                  {stage}<span class="num text-muted-foreground text-xs"
                    >{stage === "Hypothesis"
                      ? HYPOTHESES.length
                      : items.length}</span
                  >
                </p>
                {#if stage === "Hypothesis"}
                  {#each HYPOTHESES as h (h)}
                    <div class="surface rounded-lg px-3 py-2 text-sm">
                      {h}<span class="text-muted-foreground block text-xs"
                        >Stage 0 · cites Library</span
                      >
                    </div>
                  {/each}
                {:else}
                  {#each items as e (e.id)}
                    <a
                      href={resolve("/library/[id]", { id: e.id })}
                      class="surface flex overflow-hidden rounded-lg transition-transform hover:-translate-y-0.5"
                    >
                      <CoverArt
                        kind={e.kind}
                        seed={e.id}
                        series={e.spark}
                        class="h-auto w-12 shrink-0"
                      />
                      <span class="min-w-0 px-2.5 py-2">
                        <span class="block truncate text-sm font-medium"
                          >{e.name}</span
                        >
                        <span class="text-muted-foreground num block text-xs"
                          >{e.measures[0].label}
                          {e.measures[0].value} · {e.measures[1].value}</span
                        >
                      </span>
                    </a>
                  {:else}
                    <p class="text-muted-foreground px-1 text-xs">
                      Nothing here
                    </p>
                  {/each}
                {/if}
              </div>
            {/each}
          </div>
        </section>

        <!-- Working row -->
        <section class="grid gap-3 lg:grid-cols-3">
          <WidgetFrame title="Waiting for you">
            <ul class="flex flex-col gap-2">
              {#each APPROVALS as a (a.id)}
                <li class="well flex items-center gap-3 rounded-lg p-3">
                  <ShieldCheck class="text-warning size-4 shrink-0" />
                  <span class="min-w-0 flex-1"
                    ><span class="block text-sm font-medium">{a.title}</span
                    ><span class="text-muted-foreground block text-xs"
                      >{a.meta}</span
                    ></span
                  >
                  <Button size="sm" variant="outline" onclick={() => (open = a)}
                    >Review</Button
                  >
                </li>
              {/each}
            </ul>
          </WidgetFrame>
          <WidgetFrame title="Running">
            <ul class="flex flex-col gap-3">
              {#each JOBS as j (j.name)}
                <li>
                  <div class="flex justify-between gap-2 text-sm">
                    <span class="truncate">{j.name}</span><span
                      class="num text-muted-foreground">{j.pct}%</span
                    >
                  </div>
                  <div class="bg-muted mt-1.5 h-1.5 rounded-full">
                    <div
                      class="bg-info h-1.5 rounded-full transition-all"
                      style="width: {j.pct}%"
                    ></div>
                  </div>
                </li>
              {/each}
            </ul>
          </WidgetFrame>
          <WidgetFrame title="Headlines">
            <ul class="flex flex-col text-sm">
              {#each HEADLINES.slice(0, 4) as h (h.time)}
                <li class="flex gap-2 border-b py-1.5 last:border-0">
                  <span class="num text-muted-foreground w-11 shrink-0"
                    >{h.time}</span
                  >
                  <span class="min-w-0 flex-1 truncate">{h.title}</span>
                  <span
                    class={cn(
                      "shrink-0 text-xs",
                      h.tone === "positive"
                        ? "text-success"
                        : h.tone === "negative"
                          ? "text-destructive"
                          : "text-muted-foreground",
                    )}>{h.symbols[0]}</span
                  >
                </li>
              {/each}
            </ul>
          </WidgetFrame>
        </section>
      </div>
    {/if}
  </div>
</div>

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
