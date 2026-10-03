<script lang="ts">
  /** Price with this portfolio's entries marked. Symbol picker lists what is held. */
  import CandleChart from "$lib/demo/CandleChart.svelte";
  import { demoCandles } from "$lib/demo/data";
  import { cn } from "$lib/utils";

  const SYMBOLS = [
    { s: "BTCUSDT", base: 64210, p: 0, book: "Crypto momentum" },
    { s: "EURUSD", base: 1.0883, p: 4, book: "FX core" },
    { s: "US500", base: 5531, p: 1, book: "Prop challenge" },
  ];
  let sym = $state(SYMBOLS[0]);
  const candles = $derived(demoCandles(140, sym.base, sym.s.length * 7));
</script>

<div class="flex h-full flex-col">
  <div class="flex h-9 shrink-0 items-center gap-1 border-b px-2">
    {#each SYMBOLS as x (x.s)}
      <button
        type="button"
        class={cn(
          "h-6 rounded-md px-2 text-xs",
          sym.s === x.s
            ? "bg-muted text-foreground"
            : "text-muted-foreground hover:text-foreground",
        )}
        aria-pressed={sym.s === x.s}
        onclick={() => (sym = x)}>{x.s}</button
      >
    {/each}
    <span class="text-muted-foreground ml-auto text-xs"
      >H1 · held by {sym.book}</span
    >
  </div>
  <div class="min-h-0 flex-1">
    {#key sym.s}
      <CandleChart
        {candles}
        precision={sym.p}
        markers={[
          {
            time: candles[candles.length - 9].time,
            text: `Entry · ${sym.book}`,
          },
        ]}
      />
    {/key}
  </div>
</div>
