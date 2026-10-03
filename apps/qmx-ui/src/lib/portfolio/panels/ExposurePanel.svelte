<script lang="ts">
  /** What the whole portfolio is exposed to, by asset, across accounts. A report: never used to stop an order. */
  const ROWS = [
    { asset: "USD", long: 41, short: 18 },
    { asset: "BTC", long: 22, short: 0 },
    { asset: "EUR", long: 19, short: 4 },
    { asset: "ETH", long: 11, short: 3 },
    { asset: "Gold", long: 6, short: 0 },
    { asset: "US500", long: 9, short: 0 },
    { asset: "JPY", long: 0, short: 12 },
  ];
  const max = Math.max(...ROWS.map((r) => Math.max(r.long, r.short)));
</script>

<div class="flex h-full flex-col">
  <div class="min-h-0 flex-1 overflow-auto px-3 py-2">
    <div
      class="text-muted-foreground mb-1.5 grid grid-cols-[3.5rem_1fr_1fr] gap-2 text-xs"
    >
      <span></span><span class="text-right">Short</span><span>Long</span>
    </div>
    {#each ROWS as r (r.asset)}
      <div
        class="grid grid-cols-[3.5rem_1fr_1fr] items-center gap-2 py-1 text-sm"
      >
        <span>{r.asset}</span>
        <span class="flex justify-end">
          <span
            class="bg-destructive/60 h-3 rounded-l-sm"
            style="width:{(r.short / max) * 100}%"
          ></span>
        </span>
        <span class="flex items-center gap-2">
          <span
            class="bg-success/60 h-3 rounded-r-sm"
            style="width:{(r.long / max) * 100}%"
          ></span>
          <span class="num text-muted-foreground text-xs"
            >{r.long - r.short > 0 ? "+" : ""}{r.long - r.short}%</span
          >
        </span>
      </div>
    {/each}
  </div>
  <p class="text-muted-foreground border-t px-3 py-2 text-xs">
    Share of total equity, as of 12:04 UTC. A report only; each Book's own
    limits do the stopping.
  </p>
</div>
