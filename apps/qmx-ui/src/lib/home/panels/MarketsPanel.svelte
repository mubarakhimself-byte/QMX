<script lang="ts">
  /** A watchlist: price, change and a small line per coin (FX and gold as context). */
  import { linePath, equityWalk } from "$lib/qmx/charts";
  import { cn } from "$lib/utils";
  import { COINS, fmtPx } from "../home.svelte";

  const lines = COINS.map((c, i) => {
    const v = equityWalk(400 + i, 40, c.chg / 4000, 0.01);
    return {
      ...c,
      path: linePath(v, 80, 24, [Math.min(...v), Math.max(...v)]),
    };
  });
</script>

<ul class="h-full overflow-auto p-1.5">
  {#each lines as c (c.sym)}
    <li
      class="hover:bg-muted/40 grid grid-cols-[4.5rem_1fr_5rem_4rem] items-center gap-2 rounded-md px-2 py-1.5"
    >
      <span class="text-sm font-medium">{c.sym}</span>
      <svg
        viewBox="0 0 80 24"
        class="h-6 w-full"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <path
          d={c.path}
          fill="none"
          stroke={c.chg >= 0 ? "var(--success)" : "var(--destructive)"}
          stroke-width="1.5"
          vector-effect="non-scaling-stroke"
        />
      </svg>
      <span class="num text-right text-sm">{fmtPx(c.px)}</span>
      <span
        class={cn(
          "num text-right text-sm",
          c.chg >= 0 ? "text-success" : "text-destructive",
        )}>{c.chg >= 0 ? "+" : "−"}{Math.abs(c.chg).toFixed(2)}%</span
      >
    </li>
  {/each}
</ul>
