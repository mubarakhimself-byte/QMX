<script lang="ts">
  import MiniAppShell from "$lib/workbench/MiniAppShell.svelte";
  import { WidgetBoard } from "$lib/workbench/board.svelte";
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

  // DEMO: a sample research mini app. Its views and widgets stand in for a
  // pack's PackUiRequest nav[] and views[]; all numbers are sample data.
  const W = {
    chart: { id: "chart", title: "EURUSD · Daily", size: "xl", tall: true },
    watchlist: { id: "watchlist", title: "Watchlist", size: "md" },
    metrics: { id: "metrics", title: "Strategy metrics", size: "md" },
    calendar: { id: "calendar", title: "Economic calendar", size: "md" },
    news: { id: "news", title: "News", size: "md" },
    book: { id: "book", title: "Book exposure", size: "lg" },
    signals: { id: "signals", title: "Signal scanner", size: "md" },
  } as const;
  const board = new WidgetBoard({
    Overview: [W.chart, W.watchlist, W.metrics, W.calendar, W.news, W.signals],
    Signals: [W.signals, W.chart, W.news],
    Risk: [W.book, W.metrics, W.calendar],
  });

  const candles = demoCandles();
  // DEMO agent signals: where the sample model would have entered.
  const signals = [
    { time: candles[candles.length - 34].time, text: "Agent · breakout 0.71" },
    { time: candles[candles.length - 9].time, text: "Agent · breakout 0.66" },
  ];
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

{#snippet body(id: string)}
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
      <div class="min-h-0 flex-1">
        <CandleChart {candles} markers={signals} />
      </div>
    </div>
  {:else if id === "watchlist"}
    <table class="num w-full text-sm">
      <tbody>
        {#each quotes as q (q.symbol)}
          <tr class="border-b last:border-0">
            <td class="py-1.5 font-medium">{q.symbol}</td>
            <td class="w-20 px-2"
              ><Sparkline values={q.spark} class="h-5 w-full" /></td
            >
            <td class="text-right">{q.last.toFixed(q.last > 100 ? 2 : 4)}</td>
            <td class="w-24 text-right whitespace-nowrap"
              >{@render sign(q.change)}%</td
            >
          </tr>
        {/each}
      </tbody>
    </table>
  {:else if id === "metrics"}
    <dl class="grid grid-cols-2 gap-x-4 gap-y-2.5 text-sm">
      {#each DEMO_METRICS as [k, v] (k)}
        <div class="flex justify-between border-b pb-1.5">
          <dt class="text-muted-foreground">{k}</dt>
          <dd class="tabular font-medium">{v}</dd>
        </div>
      {/each}
    </dl>
  {:else if id === "calendar"}
    <div class="flex flex-col gap-2 text-sm">
      {#each DEMO_CALENDAR as day (day.day)}
        <div>
          <p class="panel-label mb-1">{day.day}</p>
          <table class="tabular w-full">
            <tbody>
              {#each day.events as e (e.time + e.event)}
                <tr class="border-b last:border-0">
                  <td class="text-muted-foreground w-14 py-1">{e.time}</td>
                  <td class="w-12 font-medium">{e.ccy}</td>
                  <td class="truncate">{e.event}</td>
                  <td class="w-14 text-right">
                    <span
                      class={cn(
                        "rounded-sm px-1 text-xs uppercase",
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
    <ul class="flex flex-col text-sm">
      {#each DEMO_NEWS as n (n.title)}
        <li class="flex gap-2 border-b py-1.5 last:border-0">
          <span class="bg-muted h-fit rounded-sm px-1 text-xs font-medium"
            >{n.tag}</span
          >
          <span class="min-w-0 flex-1">{n.title}</span>
          <span class="text-muted-foreground shrink-0">{n.age}</span>
        </li>
      {/each}
    </ul>
  {:else if id === "book"}
    <table class="num w-full text-sm">
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
    <table class="num w-full text-sm">
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

<MiniAppShell
  {board}
  name="Research"
  badge="DEMO"
  demoNote="Demo app. Sample numbers, not market data, and nothing here is saved."
  copilot={{
    hint: "Use the message-plus icon on a widget to add it here as context.",
    placeholder: "Ask about this app…",
  }}
  widget={body}
/>
