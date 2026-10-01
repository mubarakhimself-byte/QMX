<script lang="ts">
  import BellDot from "@lucide/svelte/icons/bell-dot";
  import Loader from "@lucide/svelte/icons/loader";
  import History from "@lucide/svelte/icons/history";
  import AppWindow from "@lucide/svelte/icons/app-window";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import PageHeader from "$lib/workbench/PageHeader.svelte";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import WidgetFrame from "$lib/workbench/WidgetFrame.svelte";
  import StatTile from "$lib/workbench/StatTile.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import AssetCard from "$lib/qmx/AssetCard.svelte";
  import { DEMO_ASSETS } from "$lib/demo/assets";
  import { DEMO_CALENDAR } from "$lib/demo/data";
  import { cn } from "$lib/utils";

  const demo = workbench.demoMode;

  // DEMO dashboard content: sample approvals, jobs, markets and stats.
  const APPROVALS = [
    {
      title: "Promote EURUSD H1 GBM to paper",
      meta: "Risk 0.5% per trade · asked 2h ago",
    },
    {
      title: "Raise Gold Fade drawdown limit to 5%",
      meta: "Paused at −4.0% · asked 40m ago",
    },
  ];
  const JOBS = [
    { name: "library.scan · MQL5 exit ideas", pct: 41 },
    { name: "backtest · USDJPY carry 2019–2026", pct: 73 },
    { name: "data.refresh · crypto majors", pct: 12 },
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
  const SESSIONS = [
    { name: "Sydney", open: false },
    { name: "Tokyo", open: false },
    { name: "London", open: true },
    { name: "New York", open: true },
  ];
  function heat(v: number) {
    const pct = Math.round((Math.min(Math.abs(v) / 3, 1) * 0.55 + 0.08) * 100);
    const c = v >= 0 ? "var(--success)" : "var(--destructive)";
    return `background: color-mix(in oklab, ${c} ${pct}%, transparent)`;
  }
  const RECENT = [
    { title: "EURUSD H1 model backtest", when: "Today" },
    { title: "News sentiment features", when: "Yesterday" },
    { title: "Gold mean-reversion idea", when: "Sep 28" },
    { title: "Crypto majors correlation", when: "Sep 27" },
  ];
  const ACTIVITY = [
    { at: "14:05", text: "Refreshed FX majors data", tone: "bg-success" },
    {
      at: "13:40",
      text: "Paused Gold Fade at its drawdown limit",
      tone: "bg-destructive",
    },
    {
      at: "12:10",
      text: "Wrote EURUSD H1 GBM report v7 to Library",
      tone: "bg-success",
    },
    {
      at: "11:55",
      text: "Asked you to approve a paper promotion",
      tone: "bg-warning",
    },
  ];
  const READS = [
    {
      title: "Survival analysis for trade exits",
      meta: "MQL5 · cited by the agent today",
    },
    {
      title: "Markov chain Monte Carlo: the HMC algorithm",
      meta: "MQL5 · Statistics and analysis",
    },
    { title: "EURUSD H1 GBM, report v7", meta: "Your backtest · 2 hours ago" },
  ];
  const top = [...DEMO_ASSETS].sort((a, b) => b.rating - a.rating).slice(0, 3);
</script>

<div class="flex h-full flex-col">
  {#if demo}
    <div
      class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs"
    >
      <FlaskConical class="text-warning size-3.5" />
      Demo dashboard. Sample numbers, approvals and jobs; nothing is live.
    </div>
  {/if}
  <PageHeader title="Home" subtitle="Everything running, waiting and recent">
    {#snippet actions()}
      <div class="flex items-center gap-3 text-xs" aria-label="Market sessions">
        {#each SESSIONS as s (s.name)}
          <span class="flex items-center gap-1.5">
            <span
              class={cn(
                "size-1.5 rounded-full",
                s.open ? "bg-success" : "bg-muted-foreground/40",
              )}
            ></span>
            <span class={s.open ? "" : "text-muted-foreground"}>{s.name}</span>
          </span>
        {/each}
      </div>
    {/snippet}
  </PageHeader>

  <div class="min-h-0 flex-1 overflow-auto p-3">
    {#if !demo}
      <div class="grid gap-3 lg:grid-cols-2">
        <WidgetFrame title="Needs attention" class="h-56">
          <EmptyState
            class="h-full"
            icon={BellDot}
            title="Nothing needs attention"
            description="Failed and unknown jobs land here."
          />
        </WidgetFrame>
        <WidgetFrame title="Running" class="h-56">
          <EmptyState class="h-full" icon={Loader} title="No jobs running" />
        </WidgetFrame>
        <WidgetFrame title="Recent sessions" class="h-56">
          <EmptyState
            class="h-full"
            icon={History}
            title="No recent sessions"
          />
        </WidgetFrame>
        <WidgetFrame title="Apps" class="h-56">
          <EmptyState
            class="h-full"
            icon={AppWindow}
            title="No apps installed"
          />
        </WidgetFrame>
      </div>
    {:else}
      <div class="grid grid-cols-12 gap-3">
        <div class="col-span-12 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatTile
            label="Paper equity"
            value="$104,812"
            hint="+$1,204 today"
          />
          <StatTile label="Open risk" value="1.9%" hint="of 5% limit" />
          <StatTile
            label="Running jobs"
            value={JOBS.length}
            hint="1 waiting on you"
          />
          <StatTile
            label="Strategies live"
            value="1"
            hint="2 on paper · 4 in research"
          />
        </div>

        <WidgetFrame title="Needs you" class="col-span-12 lg:col-span-5">
          <ul class="flex flex-col gap-2">
            {#each APPROVALS as a (a.title)}
              <li class="well flex items-center gap-3 rounded-lg p-3">
                <span class="bg-warning size-2 shrink-0 rounded-full"></span>
                <span class="min-w-0 flex-1">
                  <span class="block text-sm font-medium">{a.title}</span>
                  <span class="text-muted-foreground block text-xs"
                    >{a.meta}</span
                  >
                </span>
                <Button
                  size="sm"
                  aria-disabled="true"
                  class="aria-disabled:opacity-60"
                  title="Approvals need the daemon"
                  onclick={(e) => e.preventDefault()}>Review</Button
                >
              </li>
            {/each}
          </ul>
        </WidgetFrame>

        <WidgetFrame title="Running" class="col-span-12 lg:col-span-4">
          <ul class="flex flex-col gap-3">
            {#each JOBS as j (j.name)}
              <li>
                <div class="flex justify-between gap-2 text-sm">
                  <span class="truncate">{j.name}</span>
                  <span class="num text-muted-foreground">{j.pct}%</span>
                </div>
                <div class="bg-muted mt-1.5 h-1.5 rounded-full">
                  <div
                    class="bg-info h-1.5 rounded-full"
                    style="width: {j.pct}%"
                  ></div>
                </div>
              </li>
            {/each}
          </ul>
        </WidgetFrame>

        <WidgetFrame title="Next events" class="col-span-12 lg:col-span-3">
          <ul class="flex flex-col text-sm">
            {#each DEMO_CALENDAR[0].events as e (e.time + e.event)}
              <li class="flex gap-2 border-b py-1.5 last:border-0">
                <span class="num text-muted-foreground w-12 shrink-0"
                  >{e.time}</span
                >
                <span class="min-w-0 flex-1 truncate">{e.ccy} · {e.event}</span>
              </li>
            {/each}
          </ul>
        </WidgetFrame>

        <WidgetFrame title="Markets · today" class="col-span-12 lg:col-span-5">
          <div class="grid grid-cols-3 gap-1.5 sm:grid-cols-4">
            {#each MARKETS as [sym, chg] (sym)}
              <div
                class="flex flex-col rounded-md px-2.5 py-2"
                style={heat(chg)}
              >
                <span class="text-xs font-medium">{sym}</span>
                <span class="num text-sm font-semibold"
                  >{chg >= 0 ? "▲ +" : "▼ −"}{Math.abs(chg).toFixed(2)}%</span
                >
              </div>
            {/each}
          </div>
        </WidgetFrame>

        <WidgetFrame title="Top rated" class="col-span-12 lg:col-span-7">
          <div class="grid gap-2 sm:grid-cols-3">
            {#each top as a (a.id)}
              <AssetCard asset={a} onselect={() => goto(resolve("/library"))} />
            {/each}
          </div>
        </WidgetFrame>

        <WidgetFrame title="Recent sessions" class="col-span-12 lg:col-span-4">
          <ul class="flex flex-col text-sm">
            {#each RECENT as r (r.title)}
              <li class="flex items-center gap-2 border-b py-2 last:border-0">
                <span class="min-w-0 flex-1 truncate">{r.title}</span>
                <span class="text-muted-foreground shrink-0 text-xs"
                  >{r.when}</span
                >
              </li>
            {/each}
          </ul>
        </WidgetFrame>

        <WidgetFrame title="Agent activity" class="col-span-12 lg:col-span-4">
          <ol class="flex flex-col gap-2.5 text-sm">
            {#each ACTIVITY as a (a.text)}
              <li class="flex gap-2.5">
                <span class="num text-muted-foreground w-11 shrink-0"
                  >{a.at}</span
                >
                <span
                  class={cn("mt-1.5 size-1.5 shrink-0 rounded-full", a.tone)}
                ></span>
                <span class="min-w-0 flex-1">{a.text}</span>
              </li>
            {/each}
          </ol>
        </WidgetFrame>

        <WidgetFrame
          title="From your Library"
          class="col-span-12 lg:col-span-4"
        >
          <ul class="flex flex-col text-sm">
            {#each READS as r (r.title)}
              <li class="border-b py-2 last:border-0">
                <span class="block truncate font-medium">{r.title}</span>
                <span class="text-muted-foreground block text-xs">{r.meta}</span
                >
              </li>
            {/each}
          </ul>
        </WidgetFrame>
      </div>
    {/if}
  </div>
</div>
