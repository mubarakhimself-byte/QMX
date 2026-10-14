<script lang="ts">
  /** A watchlist: price, change and a small line per market, CFDs then crypto. */
  import { linePath, equityWalk } from "$lib/qmx/charts";
  import { cn } from "$lib/utils";
  import { MARKETS, isCfd } from "$lib/demo/markets";
  import { fmtPx } from "../home.svelte";

  const lines = MARKETS.map((c, i) => {
    const v = equityWalk(400 + i, 40, c.chg / 4000, 0.01);
    return {
      ...c,
      path: linePath(v, 80, 24, [Math.min(...v), Math.max(...v)]),
    };
  });
  const groups = [
    { label: "CFDs · IC Markets", items: lines.filter((l) => isCfd(l.kind)) },
    { label: "Crypto", items: lines.filter((l) => !isCfd(l.kind)) },
  ];
</script>

<div class="h-full overflow-auto p-1.5">
  {#each groups as g (g.label)}
    <p class="text-muted-foreground px-2 pt-1.5 pb-0.5 text-xs">{g.label}</p>
    <ul>
      {#each g.items as c (c.sym)}
        <li
          class="hover:bg-muted/40 grid grid-cols-[4.5rem_1fr_5rem_4rem] items-center gap-2 rounded-md px-2 py-1.5"
          title={c.name}
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
  {/each}
</div>
