<script lang="ts">
  import HeartPulse from "@lucide/svelte/icons/heart-pulse";
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Clock from "@lucide/svelte/icons/clock";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import * as Tabs from "$lib/components/ui/tabs";
  import MiniAppShell from "$lib/workbench/MiniAppShell.svelte";
  import { WidgetBoard } from "$lib/workbench/board.svelte";
  import CandleChart from "$lib/demo/CandleChart.svelte";
  import TickerTape from "$lib/qmx/TickerTape.svelte";
  import { demoCandles } from "$lib/demo/data";
  import { cn } from "$lib/utils";

  // DEMO trading node. Follows docs/components/trading-node.md: modes
  // paper|live, Book-level routing, KSA levels, stand-down, two-act
  // promotion/activation. The UI only displays and requests; the node
  // decides. No decorative background on this surface (route /trade).
  const NODES = [
    { id: "paper", name: "Paper node", where: "This machine", mode: "Paper" },
    { id: "live", name: "Live node", where: "VPS · London", mode: "Live" },
  ] as const;
  let node = $state<string>("live");

  const LEVELS = [
    { id: "GREEN", effect: "Normal trading", tone: "bg-success" },
    { id: "YELLOW", effect: "Watch: alerts only", tone: "bg-warning" },
    { id: "ORANGE", effect: "Suspend new entries", tone: "bg-chart-4" },
    { id: "RED", effect: "Drain: close as exits fire", tone: "bg-destructive" },
    { id: "BLACK", effect: "Flatten everything", tone: "bg-foreground" },
  ];
  const level = "GREEN";

  const BOOKS = [
    {
      book: "IDX-L",
      mode: "LIVE",
      bots: "US500 Trend",
      seat: "active",
      exposure: "0.9%",
      pnl: 66.8,
    },
    {
      book: "FX-L",
      mode: "LIVE",
      bots: "—",
      seat: "—",
      exposure: "0.0%",
      pnl: 0,
    },
  ];
  const POSITIONS = [
    {
      sym: "US500",
      side: "Buy",
      lots: 0.2,
      entry: "5498.2",
      last: "5531.6",
      pnl: 66.8,
      book: "IDX-L",
      bot: "US500 Trend",
    },
  ];
  const ORDERS = [
    {
      sym: "US500",
      type: "Stop",
      side: "Sell",
      lots: 0.2,
      price: "5462.0",
      book: "IDX-L",
      note: "Protective stop",
    },
  ];
  const FILLS = [
    {
      time: "14:02:11",
      sym: "US500",
      side: "Buy",
      lots: 0.2,
      price: "5498.2",
      book: "IDX-L",
    },
    {
      time: "Sep 29 09:41",
      sym: "US500",
      side: "Sell",
      lots: 0.2,
      price: "5489.5",
      book: "IDX-L",
    },
  ];
  const WINDOWS = [
    {
      at: "16:00",
      event: "USD · ISM manufacturing PMI",
      span: "15:45 – 16:15",
    },
    {
      at: "Tomorrow 14:30",
      event: "USD · Non-farm payrolls",
      span: "14:15 – 14:45",
    },
  ];
  const TICKER = [
    { sym: "US500", px: "5531.6", chg: 0.57 },
    { sym: "NAS100", px: "19,842", chg: 0.94 },
    { sym: "EURUSD", px: "1.0883", chg: -0.4 },
    { sym: "XAUUSD", px: "2384.1", chg: -0.22 },
    { sym: "BTCUSD", px: "64,210", chg: 1.83 },
    { sym: "USDJPY", px: "148.32", chg: 0.31 },
    { sym: "WTI", px: "71.42", chg: -1.2 },
  ];
  const candles = demoCandles(120, 5420, 17);
  const disabledTitle =
    "The node decides; this needs a connected node and your confirmation.";

  const W = {
    chart: { id: "chart", title: "US500 · H4 · IDX-L", size: "xl", tall: true },
    protection: {
      id: "protection",
      title: "Protection",
      size: "md",
      tall: true,
    },
    positions: { id: "positions", title: "Positions and orders", size: "xl" },
    books: { id: "books", title: "Books", size: "md" },
    waiting: { id: "waiting", title: "Waiting for you", size: "md" },
    windows: { id: "windows", title: "News windows", size: "md" },
    fills: { id: "fills", title: "Fills", size: "md" },
  } as const;
  const board = new WidgetBoard({
    Overview: [
      W.chart,
      W.protection,
      W.positions,
      W.books,
      W.waiting,
      W.windows,
      W.fills,
    ],
    Risk: [W.protection, W.books, W.positions, W.windows],
  });
</script>

<svelte:head><title>Trading node · QMX</title></svelte:head>

{#snippet header()}
  <Tabs.Root bind:value={node}>
    <Tabs.List>
      {#each NODES as n (n.id)}<Tabs.Trigger value={n.id}>{n.name}</Tabs.Trigger
        >{/each}
    </Tabs.List>
  </Tabs.Root>
  <span class="text-muted-foreground text-sm"
    >{NODES.find((n) => n.id === node)?.where}</span
  >
  <span class="text-muted-foreground ml-4 flex items-center gap-1.5 text-sm">
    <HeartPulse class="text-success size-4" /> Heartbeat 2s · 38 ms
  </span>
  <span class="flex items-center gap-2 rounded-md border px-2.5 py-0.5 text-sm">
    <span class="bg-success size-2 rounded-full"></span>Protection {level}
  </span>
{/snippet}

{#snippet strip()}<TickerTape
    items={TICKER}
    label="Live prices (sample)"
  />{/snippet}

{#snippet body(id: string)}
  {#if id === "chart"}
    <CandleChart
      precision={1}
      {candles}
      markers={[
        { time: candles[candles.length - 6].time, text: "Entry · US500 Trend" },
      ]}
    />
  {:else if id === "protection"}
    <ol class="flex flex-col gap-1">
      {#each LEVELS as l (l.id)}
        <li
          class={cn(
            "flex items-center gap-3 rounded-md px-2.5 py-1.5",
            l.id === level && "bg-muted",
          )}
        >
          <span class={cn("size-2.5 rounded-full", l.tone)}></span>
          <span class="num w-16 text-sm font-semibold">{l.id}</span>
          <span class="text-muted-foreground text-sm">{l.effect}</span>
          {#if l.id === level}<span class="ml-auto text-xs">current</span>{/if}
        </li>
      {/each}
    </ol>
    <div class="mt-3 flex flex-wrap gap-2">
      <Button
        size="sm"
        variant="outline"
        aria-disabled="true"
        class="aria-disabled:opacity-60"
        title={disabledTitle}
        onclick={(e) => e.preventDefault()}
      >
        <ShieldAlert /> Escalate…
      </Button>
      <Button
        size="sm"
        variant="destructive"
        aria-disabled="true"
        class="aria-disabled:opacity-60"
        title={disabledTitle}
        onclick={(e) => e.preventDefault()}
      >
        Flatten all…
      </Button>
    </div>
    <p class="text-muted-foreground mt-2 text-xs">
      Automatic changes only escalate; coming back down is your Resume. Flatten:
      you always; book policy and the protection authority by pre-declared
      rules.
    </p>
  {:else if id === "positions"}
    <table class="w-full text-sm">
      <thead class="text-muted-foreground text-left text-xs">
        <tr>
          <th class="pb-1.5 font-medium">Symbol</th><th class="font-medium"
            >Side</th
          >
          <th class="text-right font-medium">Lots</th><th
            class="text-right font-medium">Entry</th
          >
          <th class="text-right font-medium">Last</th><th
            class="text-right font-medium">P&amp;L</th
          >
          <th class="pl-4 font-medium">Book · bot</th>
        </tr>
      </thead>
      <tbody>
        {#each POSITIONS as p (p.sym)}
          <tr class="border-t">
            <td class="py-2 font-medium">{p.sym}</td><td>{p.side}</td>
            <td class="num text-right">{p.lots.toFixed(2)}</td>
            <td class="num text-right">{p.entry}</td>
            <td class="num text-right">{p.last}</td>
            <td class="num text-success text-right">+${p.pnl.toFixed(2)}</td>
            <td class="text-muted-foreground pl-4">{p.book} · {p.bot}</td>
          </tr>
        {/each}
        {#each ORDERS as o (o.sym + o.type)}
          <tr class="border-t">
            <td class="py-2 font-medium">{o.sym}</td><td>{o.type} {o.side}</td>
            <td class="num text-right">{o.lots.toFixed(2)}</td>
            <td class="num text-right">{o.price}</td><td></td>
            <td class="text-muted-foreground text-right text-xs">working</td>
            <td class="text-muted-foreground pl-4">{o.book} · {o.note}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  {:else if id === "books"}
    <ul class="flex flex-col gap-2">
      {#each BOOKS as b (b.book)}
        <li class="well flex items-center gap-3 rounded-lg p-3">
          <span class="min-w-0 flex-1">
            <span class="flex items-center gap-2 text-sm font-medium">
              {b.book}<Badge variant="outline" class="h-4 px-1.5 text-[10px]"
                >{b.mode}</Badge
              >
            </span>
            <span class="text-muted-foreground block text-xs"
              >{b.bots} · seat {b.seat} · exposure {b.exposure}</span
            >
          </span>
          <span
            class={cn(
              "num text-sm",
              b.pnl > 0 ? "text-success" : "text-muted-foreground",
            )}
          >
            {b.pnl > 0 ? "+$" + b.pnl.toFixed(2) : "$0.00"}
          </span>
        </li>
      {/each}
    </ul>
    <p class="text-muted-foreground mt-2 text-xs">
      Sizing comes from the book, never from a bot.
    </p>
  {:else if id === "waiting"}
    <div class="well rounded-lg p-3">
      <p class="flex items-center gap-2 text-sm font-medium">
        <ShieldCheck class="text-warning size-4" /> Promote EURUSD H1 GBM
      </p>
      <p class="text-muted-foreground mt-1 text-xs">
        Signed card: bot v7 (fp1:9c41…e2a0) into book FX-L at 0.5% risk.
        Evidence: 2 confirmation runs.
      </p>
      <Button
        size="sm"
        class="mt-2 aria-disabled:opacity-60"
        aria-disabled="true"
        title={disabledTitle}
        onclick={(e) => e.preventDefault()}
      >
        Review and sign…
      </Button>
    </div>
    <p class="text-muted-foreground mt-2 text-xs">
      Promotion and activation are two separate acts. Activation takes effect at
      the next day boundary.
    </p>
  {:else if id === "windows"}
    <ul class="flex flex-col text-sm">
      {#each WINDOWS as w (w.event)}
        <li class="flex items-center gap-3 border-b py-2 last:border-0">
          <Clock class="text-muted-foreground size-4 shrink-0" />
          <span class="min-w-0 flex-1">
            <span class="block">{w.event}</span>
            <span class="text-muted-foreground text-xs"
              >No new entries {w.span}</span
            >
          </span>
          <span class="num text-muted-foreground text-xs">{w.at}</span>
        </li>
      {/each}
    </ul>
  {:else if id === "fills"}
    <ul class="flex flex-col text-sm">
      {#each FILLS as f (f.time)}
        <li
          class="grid grid-cols-[6.5rem_1fr_auto] gap-2 border-b py-2 last:border-0"
        >
          <span class="num text-muted-foreground text-xs">{f.time}</span>
          <span>{f.side} {f.lots.toFixed(2)} {f.sym}</span>
          <span class="num">{f.price}</span>
        </li>
      {/each}
    </ul>
  {/if}
{/snippet}

<MiniAppShell
  {board}
  name="Trading node"
  badge="DEMO"
  tone={node === "live" ? "live" : "paper"}
  demoNote="Demo trading node. Sample positions and prices; no orders can be placed from this window."
  headerExtra={header}
  {strip}
  widget={body}
/>
