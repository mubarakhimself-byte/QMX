<script lang="ts">
  import PageHeader from "$lib/workbench/PageHeader.svelte";
  import WidgetFrame, {
    type WidgetState,
  } from "$lib/workbench/WidgetFrame.svelte";
  import StatTile from "$lib/workbench/StatTile.svelte";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import Composer from "$lib/workbench/Composer.svelte";
  import DataTable, { type Column } from "$lib/qmx/DataTable.svelte";
  import EntityCard from "$lib/qmx/EntityCard.svelte";
  import CandleChart from "$lib/demo/CandleChart.svelte";
  import LineChart from "$lib/qmx/LineChart.svelte";
  import TickerTape from "$lib/qmx/TickerTape.svelte";
  import RunConsole from "$lib/qmx/RunConsole.svelte";
  import { equityWalk } from "$lib/qmx/charts";
  import Sparkline from "$lib/demo/Sparkline.svelte";
  import { CATALOG } from "$lib/qmx/catalog";
  import { DEMO_ENTITIES } from "$lib/demo/assets";
  import { demoCandles } from "$lib/demo/data";
  import { cn } from "$lib/utils";

  // Component library: every catalog entry rendered live, with the spec the
  // copilot reads. Sample content only.
  let selected = $state(CATALOG[0].type);
  const entry = $derived(CATALOG.find((c) => c.type === selected)!);
  const groups = [...new Set(CATALOG.map((c) => c.group))];
  const STATES: WidgetState[] = [
    "ready",
    "loading",
    "empty",
    "unavailable",
    "failed",
    "stale",
    "reconnecting",
    "unknown",
  ];
  const table = CATALOG.find((c) => c.type === "DataTable")!.example as {
    columns: Column[];
    rows: Record<string, string | number>[];
  };
  const candles = demoCandles(90, 1.08, 5);
</script>

<div class="flex h-full flex-col">
  <PageHeader
    title="Component library"
    subtitle="The building blocks mini apps are composed from"
  />
  <div class="flex min-h-0 flex-1">
    <nav
      aria-label="Components"
      class="bg-panel w-56 shrink-0 overflow-auto border-r p-2"
    >
      {#each groups as g (g)}
        <p class="panel-label px-2 pt-3 pb-1">{g}</p>
        <ul>
          {#each CATALOG.filter((c) => c.group === g) as c (c.type)}
            <li>
              <button
                type="button"
                class={cn(
                  "hover:bg-muted w-full rounded-md px-2 py-1.5 text-left text-sm",
                  selected === c.type && "bg-muted font-medium",
                )}
                aria-current={selected === c.type ? "true" : undefined}
                onclick={() => (selected = c.type)}>{c.type}</button
              >
            </li>
          {/each}
        </ul>
      {/each}
    </nav>

    <div class="min-h-0 flex-1 overflow-auto p-5">
      <div class="mx-auto flex max-w-5xl flex-col gap-5">
        <div>
          <p class="panel-label">{entry.group}</p>
          <h2 class="text-2xl font-semibold">{entry.type}</h2>
          <p class="text-muted-foreground mt-1 max-w-3xl text-[15px]">
            {entry.description}
          </p>
        </div>

        <section aria-label="Preview" class="flex flex-col gap-3">
          <p class="panel-label">Preview</p>
          {#if selected === "WidgetFrame"}
            <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {#each STATES as s (s)}
                <WidgetFrame
                  title={s}
                  state={s}
                  reason={s === "ready" ? undefined : "Sample reason text."}
                  class="h-44"
                >
                  <DataTable
                    columns={table.columns}
                    rows={table.rows.slice(0, 2)}
                    dense
                  />
                </WidgetFrame>
              {/each}
            </div>
          {:else if selected === "StatTile"}
            <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
              <StatTile
                label="Paper equity"
                value="$104,812"
                hint="+$1,204 today"
              />
              <StatTile label="Open risk" value="1.9%" hint="of 5% limit" />
              <StatTile label="No value yet" hint="Not connected" />
            </div>
          {:else if selected === "DataTable"}
            <div class="surface rounded-lg p-4">
              <DataTable columns={table.columns} rows={table.rows} />
            </div>
          {:else if selected === "CandleChart"}
            <div class="surface h-80 rounded-lg p-3">
              <CandleChart
                {candles}
                markers={[
                  { time: candles[60].time, text: "Agent · sample signal" },
                ]}
              />
            </div>
          {:else if selected === "Sparkline"}
            <div class="surface flex gap-6 rounded-lg p-4">
              <Sparkline values={[3, 4, 3.5, 5, 6, 5.5, 7]} class="h-10 w-40" />
              <Sparkline values={[7, 6, 6.5, 5, 4, 4.5, 3]} class="h-10 w-40" />
            </div>
          {:else if selected === "EntityCard"}
            <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {#each DEMO_ENTITIES as a (a.id)}<EntityCard entity={a} />{/each}
            </div>
          {:else if selected === "LineChart"}
            <div class="surface h-64 rounded-lg p-4">
              <LineChart
                series={[
                  {
                    label: "Strategy",
                    values: equityWalk(4, 90, 0.0015),
                    color: "var(--chart-1)",
                  },
                  {
                    label: "Benchmark",
                    values: equityWalk(9, 90, 0.0005),
                    color: "var(--muted-foreground)",
                    dashed: true,
                  },
                ]}
              />
            </div>
          {:else if selected === "TickerTape"}
            <div class="surface overflow-hidden rounded-lg">
              <TickerTape
                items={[
                  { sym: "EURUSD", px: "1.0883", chg: -0.4 },
                  { sym: "BTC", px: "64,210", chg: 1.83 },
                  { sym: "US500", px: "5531.6", chg: 0.57 },
                  { sym: "XAUUSD", px: "2384.1", chg: -0.22 },
                ]}
              />
            </div>
          {:else if selected === "RunConsole"}
            <div class="h-48">
              <RunConsole
                command="qmb backtest us500-trend"
                lines={[
                  "data verify US500 H4 ok",
                  "fold 1/12 sharpe 1.21",
                  "CT-32 written · confirmation",
                ]}
                status="done"
              />
            </div>
          {:else if selected === "EmptyState"}
            <div class="surface rounded-lg">
              <EmptyState
                title="No jobs running"
                description="Backtests and workflows in progress appear here."
              />
            </div>
          {:else if selected === "Composer"}
            <div class="max-w-2xl">
              <Composer
                placeholder="Ask about this app…"
                refs={["EURUSD chart"]}
              />
            </div>
          {/if}
        </section>

        <section aria-label="Props" class="flex flex-col gap-2">
          <p class="panel-label">Props</p>
          <div class="surface overflow-hidden rounded-lg">
            <table class="w-full text-sm">
              <thead class="text-muted-foreground text-left text-xs">
                <tr
                  ><th class="px-4 py-2 font-medium">Name</th><th
                    class="font-medium">Type</th
                  ><th class="px-4 font-medium">Description</th></tr
                >
              </thead>
              <tbody>
                {#each Object.entries(entry.props) as [name, p] (name)}
                  <tr class="border-t">
                    <td class="px-4 py-2 font-mono text-[13px]"
                      >{name}{p.required ? "" : "?"}</td
                    >
                    <td class="text-muted-foreground font-mono text-[13px]"
                      >{p.options ? p.options.join(" | ") : p.type}</td
                    >
                    <td class="px-4">{p.description}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </section>

        <section aria-label="Spec" class="flex flex-col gap-2">
          <p class="panel-label">Spec the copilot reads</p>
          <pre
            class="surface overflow-auto rounded-lg p-4 font-mono text-[13px] leading-relaxed">{JSON.stringify(
              { type: entry.type, props: entry.example },
              null,
              2,
            )}</pre>
        </section>
      </div>
    </div>
  </div>
</div>
