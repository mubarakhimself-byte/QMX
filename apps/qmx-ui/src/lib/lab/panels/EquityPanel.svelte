<script lang="ts">
  /** Equity of the selected run, with ticked runs overlaid for comparison. */
  import LineChart from "$lib/qmx/LineChart.svelte";
  import type { LinkGroup } from "$lib/workbench/tiles/tiles";
  import EnvChip from "../EnvChip.svelte";
  import { RUNS } from "../demo";
  import { lab } from "../lab.svelte";

  let { link }: { link?: LinkGroup } = $props();

  const COLORS = ["var(--chart-2)", "var(--chart-3)", "var(--chart-4)"];
  const run = $derived(RUNS.find((r) => r.id === lab.selectedFor(link)));
  const overlay = $derived(
    RUNS.filter(
      (r) => lab.ticked.includes(r.id) && r.id !== run?.id && r.equity.length,
    ).slice(0, 3),
  );
  const series = $derived([
    ...(run?.equity.length
      ? [
          {
            label: `${run.id} · ${run.symbol} ${run.timeframe}`,
            values: run.equity,
            color: "var(--primary)",
          },
        ]
      : []),
    ...overlay.map((r, i) => ({
      label: `${r.id} · ${r.symbol} ${r.timeframe}`,
      values: r.equity,
      color: COLORS[i],
      dashed: true,
    })),
  ]);
</script>

<div class="flex h-full flex-col gap-2 p-3">
  {#if run}
    <div class="flex flex-wrap items-baseline gap-x-4 gap-y-1">
      <span class="text-sm font-medium"
        >{run.procedure} · {run.symbol} {run.timeframe}</span
      >
      {#if run.net !== null}
        <span
          class="num text-lg {run.net >= 0
            ? 'text-success'
            : 'text-destructive'}">{run.net > 0 ? "+" : ""}{run.net}%</span
        >
        <span class="num text-muted-foreground text-sm"
          >max DD {run.maxDd}% · sharpe {run.sharpe}</span
        >
      {/if}
      <span class="ml-auto"><EnvChip env={run.env} status={run.status} /></span>
    </div>
  {/if}
  <div class="min-h-0 flex-1">
    {#if series.length}
      <LineChart {series} height={200} />
    {:else}
      <div
        class="text-muted-foreground flex h-full items-center justify-center text-sm"
      >
        {run
          ? "This run has no equity yet. It fills in as trades close."
          : "Select a run to see its equity."}
      </div>
    {/if}
  </div>
</div>
