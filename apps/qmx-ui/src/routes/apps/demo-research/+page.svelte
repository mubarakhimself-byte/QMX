<script lang="ts">
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import Pencil from "@lucide/svelte/icons/pencil";
  import Check from "@lucide/svelte/icons/check";
  import Plus from "@lucide/svelte/icons/plus";
  import PanelRight from "@lucide/svelte/icons/panel-right";
  import * as Resizable from "$lib/components/ui/resizable";
  import * as Tabs from "$lib/components/ui/tabs";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import WidgetFrame from "$lib/workbench/WidgetFrame.svelte";
  import CopilotColumn from "$lib/workbench/CopilotColumn.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import CandleChart from "$lib/demo/CandleChart.svelte";
  import Sparkline from "$lib/demo/Sparkline.svelte";
  import {
    demoCandles,
    demoWatchlist,
    DEMO_CALENDAR,
    DEMO_NEWS,
    DEMO_BOOK,
    DEMO_METRICS,
  } from "$lib/demo/data";
  import { cn } from "$lib/utils";
  import { SvelteSet } from "svelte/reactivity";

  // DEMO: a sample research mini-app. Its views and widgets stand in for a
  // pack's PackUiRequest nav[] and views[]; all numbers are sample data.
  type WidgetId =
    | "chart"
    | "watchlist"
    | "metrics"
    | "calendar"
    | "news"
    | "book"
    | "signals";
  const TITLES: Record<WidgetId, string> = {
    chart: "EURUSD · Daily",
    watchlist: "Watchlist",
    metrics: "Strategy metrics",
    calendar: "Economic calendar",
    news: "News",
    book: "Book exposure",
    signals: "Signal scanner",
  };
  const SPAN: Partial<Record<WidgetId, string>> = {
    chart: "xl:col-span-2 xl:row-span-2",
  };
  const VIEWS: Record<string, WidgetId[]> = {
    Overview: ["chart", "watchlist", "metrics", "calendar", "news"],
    Signals: ["signals", "chart", "news"],
    Risk: ["book", "metrics", "calendar"],
  };

  let view = $state("Overview");
  let layout = $state<Record<string, WidgetId[]>>(structuredClone(VIEWS));
  const minimized = new SvelteSet<WidgetId>();
  let expanded = $state<WidgetId | null>(null);
  let editing = $state(false);
  let copilotOpen = $state(true);

  const shown = $derived(layout[view]);
  const addable = $derived(
    (Object.keys(TITLES) as WidgetId[]).filter((id) => !shown.includes(id)),
  );

  function close(id: WidgetId) {
    layout[view] = layout[view].filter((w) => w !== id);
    if (expanded === id) expanded = null;
  }
  function add(id: WidgetId) {
    layout[view] = [...layout[view], id];
  }
  function toggleMin(id: WidgetId) {
    if (minimized.has(id)) minimized.delete(id);
    else minimized.add(id);
  }
  function toggleExpand(id: WidgetId) {
    expanded = expanded === id ? null : id;
  }
  function mention(id: WidgetId) {
    workbench.addRef(TITLES[id]);
    copilotOpen = true;
  }

  const candles = demoCandles();
  const quotes = demoWatchlist();
  const last = candles[candles.length - 1];
  const prev = candles[candles.length - 2];
  const dayChange = ((last.close / prev.close - 1) * 100).toFixed(2);
  const SIGNALS = [
    { symbol: "EURUSD", signal: "Breakout", tf: "H4", strength: 78 },
    { symbol: "XAUUSD", signal: "Mean reversion", tf: "D1", strength: 64 },
    { symbol: "USDJPY", signal: "Momentum", tf: "H1", strength: 52 },
    { symbol: "GBPUSD", signal: "Range", tf: "H4", strength: 31 },
  ];
</script>

{#snippet sign(v: number, digits = 2)}
  <span class={v >= 0 ? "text-success" : "text-destructive"}>
    {v >= 0 ? "▲ +" : "▼ −"}{Math.abs(v).toFixed(digits)}
  </span>
{/snippet}

{#snippet body(id: WidgetId)}
  {#if id === "chart"}
    <div class="flex h-full min-h-56 flex-col gap-1">
      <div class="flex items-baseline gap-3">
        <span class="tabular text-lg font-semibold"
          >{last.close.toFixed(5)}</span
        >
        <span class="tabular text-xs">{@render sign(+dayChange)}%</span>
        <span class="text-muted-foreground text-xs"
          >O {last.open} · H {last.high} · L {last.low}</span
        >
      </div>
      <div class="min-h-0 flex-1"><CandleChart {candles} /></div>
    </div>
  {:else if id === "watchlist"}
    <table class="tabular w-full text-xs">
      <tbody>
        {#each quotes as q (q.symbol)}
          <tr class="border-b last:border-0">
            <td class="py-1.5 font-medium">{q.symbol}</td>
            <td class="w-20 px-2"
              ><Sparkline values={q.spark} class="h-5 w-full" /></td
            >
            <td class="text-right">{q.last.toFixed(q.last > 100 ? 2 : 4)}</td>
            <td class="w-16 text-right">{@render sign(q.change)}%</td>
          </tr>
        {/each}
      </tbody>
    </table>
  {:else if id === "metrics"}
    <dl class="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
      {#each DEMO_METRICS as [k, v] (k)}
        <div class="flex justify-between border-b pb-1.5">
          <dt class="text-muted-foreground">{k}</dt>
          <dd class="tabular font-medium">{v}</dd>
        </div>
      {/each}
    </dl>
  {:else if id === "calendar"}
    <div class="flex flex-col gap-2 text-xs">
      {#each DEMO_CALENDAR as day (day.day)}
        <div>
          <p class="panel-label mb-1">{day.day}</p>
          <table class="tabular w-full">
            <tbody>
              {#each day.events as e (e.time + e.event)}
                <tr class="border-b last:border-0">
                  <td class="text-muted-foreground w-11 py-1">{e.time}</td>
                  <td class="w-10 font-medium">{e.ccy}</td>
                  <td class="truncate">{e.event}</td>
                  <td class="w-14 text-right">
                    <span
                      class={cn(
                        "rounded-sm px-1 text-[10px] uppercase",
                        e.impact === "high" &&
                          "bg-destructive/15 text-destructive",
                        e.impact === "medium" && "bg-warning/15 text-warning",
                        e.impact === "low" && "bg-muted text-muted-foreground",
                      )}>{e.impact}</span
                    >
                  </td>
                  <td class="text-muted-foreground w-12 text-right"
                    >{e.forecast}</td
                  >
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/each}
    </div>
  {:else if id === "news"}
    <ul class="flex flex-col text-xs">
      {#each DEMO_NEWS as n (n.title)}
        <li class="flex gap-2 border-b py-1.5 last:border-0">
          <span class="bg-muted h-fit rounded-sm px-1 text-[10px] font-medium"
            >{n.tag}</span
          >
          <span class="min-w-0 flex-1">{n.title}</span>
          <span class="text-muted-foreground shrink-0">{n.age}</span>
        </li>
      {/each}
    </ul>
  {:else if id === "book"}
    <table class="tabular w-full text-xs">
      <thead class="text-muted-foreground text-left">
        <tr
          ><th class="pb-1 font-medium">Symbol</th><th class="font-medium"
            >Side</th
          ><th class="text-right font-medium">Lots</th><th
            class="text-right font-medium">P&amp;L</th
          ><th class="w-28 pl-3 font-medium">Exposure</th></tr
        >
      </thead>
      <tbody>
        {#each DEMO_BOOK as p (p.symbol)}
          <tr class="border-t">
            <td class="py-1.5 font-medium">{p.symbol}</td>
            <td>{p.side}</td>
            <td class="text-right">{p.size.toFixed(2)}</td>
            <td class="text-right">{@render sign(p.pnl)}</td>
            <td class="pl-3">
              <div class="bg-muted h-1.5 rounded-full">
                <div
                  class="bg-chart-1 h-1.5 rounded-full"
                  style="width: {p.exposure}%"
                ></div>
              </div>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  {:else if id === "signals"}
    <table class="tabular w-full text-xs">
      <thead class="text-muted-foreground text-left">
        <tr
          ><th class="pb-1 font-medium">Symbol</th><th class="font-medium"
            >Signal</th
          ><th class="font-medium">TF</th><th class="w-32 font-medium"
            >Strength</th
          ></tr
        >
      </thead>
      <tbody>
        {#each SIGNALS as s (s.symbol)}
          <tr class="border-t">
            <td class="py-1.5 font-medium">{s.symbol}</td>
            <td>{s.signal}</td>
            <td class="text-muted-foreground">{s.tf}</td>
            <td>
              <div class="flex items-center gap-2">
                <div class="bg-muted h-1.5 flex-1 rounded-full">
                  <div
                    class="bg-success h-1.5 rounded-full"
                    style="width: {s.strength}%"
                  ></div>
                </div>
                <span class="w-6 text-right">{s.strength}</span>
              </div>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
{/snippet}

<svelte:head><title>Research (demo) · QMX</title></svelte:head>

<div class="flex h-full flex-col">
  <div class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs">
    <FlaskConical class="text-warning size-3.5" />
    Demo app. Sample numbers, not market data, and nothing here is saved.
  </div>

  <header class="flex h-10 shrink-0 items-center gap-3 border-b px-3">
    <span class="text-sm font-semibold">Research</span>
    <Badge variant="outline" class="h-4 px-1.5 text-[10px]">DEMO</Badge>
    <Tabs.Root bind:value={view} onValueChange={() => (expanded = null)}>
      <Tabs.List variant="line">
        {#each Object.keys(VIEWS) as v (v)}<Tabs.Trigger value={v}
            >{v}</Tabs.Trigger
          >{/each}
      </Tabs.List>
    </Tabs.Root>
    <div class="ml-auto flex items-center gap-1">
      <Button
        variant={editing ? "secondary" : "ghost"}
        size="sm"
        aria-pressed={editing}
        onclick={() => (editing = !editing)}
      >
        {#if editing}<Check /> Done{:else}<Pencil /> Edit layout{/if}
      </Button>
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label="Toggle app copilot"
        aria-pressed={copilotOpen}
        onclick={() => (copilotOpen = !copilotOpen)}
      >
        <PanelRight />
      </Button>
    </div>
  </header>

  <Resizable.PaneGroup direction="horizontal" class="min-h-0 flex-1">
    <Resizable.Pane defaultSize={74} minSize={45}>
      <div class="relative h-full overflow-auto p-2">
        {#if expanded}
          <WidgetFrame
            title={TITLES[expanded]}
            class="h-full"
            expanded
            onexpand={() => toggleExpand(expanded!)}
            onmessage={() => mention(expanded!)}
          >
            {@render body(expanded)}
          </WidgetFrame>
        {:else}
          <div
            class="grid auto-rows-[minmax(13rem,auto)] gap-2 md:grid-cols-2 xl:grid-cols-3"
          >
            {#each shown as id (id)}
              <WidgetFrame
                title={TITLES[id]}
                class={cn(
                  !minimized.has(id) && SPAN[id],
                  minimized.has(id) && "h-fit",
                  editing && "outline-ring/40 outline-1 outline-dashed",
                )}
                minimized={minimized.has(id)}
                onmessage={() => mention(id)}
                onminimize={() => toggleMin(id)}
                onexpand={() => toggleExpand(id)}
                onclose={editing ? () => close(id) : undefined}
              >
                {@render body(id)}
              </WidgetFrame>
            {/each}
          </div>
          {#if editing && addable.length}
            <div class="absolute right-4 bottom-4">
              <DropdownMenu.Root>
                <DropdownMenu.Trigger>
                  {#snippet child({ props })}
                    <Button {...props} size="sm"><Plus /> Add widget</Button>
                  {/snippet}
                </DropdownMenu.Trigger>
                <DropdownMenu.Content align="end">
                  {#each addable as id (id)}
                    <DropdownMenu.Item onclick={() => add(id)}
                      >{TITLES[id]}</DropdownMenu.Item
                    >
                  {/each}
                </DropdownMenu.Content>
              </DropdownMenu.Root>
            </div>
          {/if}
        {/if}
      </div>
    </Resizable.Pane>
    {#if copilotOpen}
      <Resizable.Handle />
      <Resizable.Pane defaultSize={26} minSize={20} maxSize={40}>
        <CopilotColumn
          title="App copilot"
          profile="app-use"
          hint="Use the message-plus icon on a widget to add it here as context."
          placeholder="Ask about this app…"
          refs={workbench.copilotRefs}
          onremoveref={(r) => workbench.removeRef(r)}
          onclose={() => (copilotOpen = false)}
        />
      </Resizable.Pane>
    {/if}
  </Resizable.PaneGroup>
</div>
