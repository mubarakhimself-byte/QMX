<script lang="ts">
  /** What the portfolio holds, by market, across every account (cash includes stablecoins). A report, never used to stop an order. */
  import { EXPOSURE } from "../demo";

  const max = Math.max(...EXPOSURE.map((r) => r.share));
</script>

<div class="flex h-full flex-col">
  <div class="min-h-0 flex-1 overflow-auto px-3 py-2">
    {#each EXPOSURE as r (r.asset)}
      <div
        class="grid grid-cols-[5.5rem_1fr_3rem] items-center gap-2 py-1.5 text-sm"
      >
        <span class={r.asset === "Cash" ? "text-muted-foreground" : ""}
          >{r.asset}</span
        >
        <span class="bg-muted h-3 overflow-hidden rounded-sm">
          <span
            class="block h-full rounded-sm {r.asset === 'Cash'
              ? 'bg-muted-foreground/50'
              : 'bg-primary/80'}"
            style="width:{(r.share / max) * 100}%"
          ></span>
        </span>
        <span class="num text-right">{r.share}%</span>
      </div>
    {/each}
  </div>
  <p class="text-muted-foreground border-t px-3 py-2 text-xs">
    Share of total equity at 12:04 UTC. A report; each pod's own limits do the
    stopping.
  </p>
</div>
