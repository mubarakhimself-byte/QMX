<script lang="ts">
  /** Equity of the selected run, with ticked runs overlaid for comparison. */
  import LineChart from "$lib/qmx/LineChart.svelte";
  import Sparkline from "$lib/demo/Sparkline.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import type { LinkGroup } from "$lib/workbench/tiles/tiles";
  import EnvChip from "../EnvChip.svelte";
  import { RUNS } from "../demo";
  import { lab } from "../lab.svelte";

  let { link }: { link?: LinkGroup } = $props();
  const size = panelSize();

  const COLORS = ["var(--chart-2)", "var(--chart-3)", "var(--chart-4)"];
  const run = $derived(RUNS.find((r) => r.id === lab.selectedFor(link)));
  const overlay = $derived(
    RUNS.filter(
      (r) => lab.ticked.includes(r.id) && r.id !== run?.id && r.equity.length,
    ).slice(0, 3),
  );
  const signed = (v: number) => `${v > 0 ? "+" : ""}${v}%`;
  const plotted = $derived([...(run ? [run] : []), ...overlay]);
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

{#if !run}
  <div
    class="text-muted-foreground p-panel flex h-full items-center justify-center text-sm"
  >
    No run selected
  </div>
{:else if size.mode === "compact"}
  <div class="p-panel gap-row flex h-full flex-col">
    <p class="text-muted-foreground truncate text-xs">
      {run.symbol}
      {run.timeframe} · {run.id}
    </p>
    {#if run.net !== null}
      <p
        class="num text-2xl font-semibold {run.net >= 0
          ? 'text-success'
          : 'text-destructive'}"
      >
        {signed(run.net)}
      </p>
      <p class="num text-muted-foreground text-xs">{run.maxDd}% max DD</p>
    {:else}
      <p class="text-muted-foreground text-sm capitalize">{run.status}</p>
    {/if}
    {#if run.equity.length}
      <Sparkline values={run.equity} class="mt-auto h-8 w-full shrink-0" />
    {/if}
  </div>
{:else}
  <div class="p-panel gap-row flex h-full flex-col">
    <div class="flex min-w-0 items-baseline gap-x-3">
      <span class="truncate text-sm font-medium"
        >{run.procedure} · {run.symbol} {run.timeframe}</span
      >
      {#if run.net !== null}
        <span
          class="num text-lg {run.net >= 0
            ? 'text-success'
            : 'text-destructive'}">{signed(run.net)}</span
        >
        <span class="num text-muted-foreground hidden text-sm @[28rem]:inline"
          >{run.maxDd}% DD · Sharpe {run.sharpe}</span
        >
      {/if}
      <span class="ml-auto shrink-0"
        ><EnvChip env={run.env} status={run.status} /></span
      >
    </div>
    <div class="min-h-0 flex-1">
      {#if series.length}
        <LineChart {series} height={200} />
      {:else}
        <div
          class="text-muted-foreground flex h-full items-center justify-center text-sm"
        >
          No trades yet
        </div>
      {/if}
    </div>
    {#if size.mode === "expanded" && plotted.length}
      <table class="w-full max-w-3xl text-sm" aria-label="Plotted runs">
        <thead class="text-muted-foreground text-xs">
          <tr>
            <th class="py-row text-left font-normal">Run</th>
            <th class="py-row text-right font-normal">Net</th>
            <th class="py-row text-right font-normal">Max DD</th>
            <th class="py-row text-right font-normal">Sharpe</th>
            <th class="py-row text-right font-normal">Trades</th>
          </tr>
        </thead>
        <tbody>
          {#each plotted as r (r.id)}
            <tr class="border-t">
              <td class="py-row">{r.id} · {r.symbol} {r.timeframe}</td>
              <td class="num py-row text-right"
                >{r.net === null ? "—" : signed(r.net)}</td
              >
              <td class="num py-row text-right">{r.maxDd ?? "—"}%</td>
              <td class="num py-row text-right">{r.sharpe ?? "—"}</td>
              <td class="num py-row text-right">{r.trades ?? "—"}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
{/if}
