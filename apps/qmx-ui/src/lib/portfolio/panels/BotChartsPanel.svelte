<script lang="ts">
  /**
   * One chart per trading bot, across the top of Live (operator, 2026-10-03):
   * its market, its entries, its P&L and state. Click one to make it large.
   */
  import Maximize2 from "@lucide/svelte/icons/maximize-2";
  import Minimize2 from "@lucide/svelte/icons/minimize-2";
  import CandleChart from "$lib/demo/CandleChart.svelte";
  import { demoCandles } from "$lib/demo/data";
  import { cn } from "$lib/utils";
  import { BASE_PRICE, TRADING_BOTS } from "../demo";
  import { usd } from "../bits";
  import { portfolio } from "../portfolio.svelte";

  const bots = $derived(
    TRADING_BOTS.filter(
      (b) =>
        portfolio.world === "all" ||
        (portfolio.world === "live") === (b.mode === "LIVE"),
    ),
  );
  let focus = $state<string | null>(null);
  const shown = $derived(focus ? bots.filter((b) => b.id === focus) : bots);
  const candles = (sym: string, seed: number) =>
    demoCandles(90, BASE_PRICE[sym]?.[0] ?? 100, seed);
</script>

<div
  class={cn(
    "grid h-full gap-1.5 overflow-auto p-1.5",
    !focus &&
      "[grid-template-columns:repeat(auto-fit,minmax(18rem,1fr))] auto-rows-[minmax(12rem,1fr)]",
  )}
>
  {#each shown as b, i (b.id)}
    {@const c = candles(b.symbol, i * 7 + 3)}
    <section
      class="solid-backing flex min-h-0 flex-col overflow-hidden rounded-lg border-2"
      style="border-color: color-mix(in oklab, var(--tone-{b.mode === 'LIVE'
        ? 'live'
        : 'paper'}) 55%, transparent)"
      aria-label={`${b.name} chart`}
    >
      <header
        class="flex h-8 shrink-0 items-center gap-2 border-b px-2 text-xs"
      >
        <span
          class={cn(
            "size-2 rounded-full",
            b.state === "trading" ? "bg-success" : "bg-warning",
          )}
        ></span>
        <span class="font-medium">{b.name}</span>
        <span class="text-muted-foreground">{b.symbol} · {b.pod}</span>
        <span
          class={cn(
            "num ml-auto",
            b.pnl >= 0 ? "text-success" : "text-destructive",
          )}>{usd(b.pnl)}</span
        >
        <button
          type="button"
          class="hover:bg-muted flex size-6 items-center justify-center rounded"
          aria-label={focus ? "Show every bot" : `Enlarge ${b.name}`}
          onclick={() => (focus = focus ? null : b.id)}
        >
          {#if focus}<Minimize2 class="size-3.5" />{:else}<Maximize2
              class="size-3.5"
            />{/if}
        </button>
      </header>
      <div class="min-h-0 flex-1">
        <CandleChart
          candles={c}
          precision={BASE_PRICE[b.symbol]?.[1] ?? 2}
          markers={b.state === "trading"
            ? [{ time: c[c.length - 7].time, text: "Entry" }]
            : []}
        />
      </div>
    </section>
  {/each}
</div>
