<script lang="ts">
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import Play from "@lucide/svelte/icons/play";
  import Lock from "@lucide/svelte/icons/lock";
  import * as Tabs from "$lib/components/ui/tabs";
  import * as Resizable from "$lib/components/ui/resizable";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import { Input } from "$lib/components/ui/input";
  import WidgetFrame from "$lib/workbench/WidgetFrame.svelte";
  import LineChart from "$lib/qmx/LineChart.svelte";
  import RunConsole from "$lib/qmx/RunConsole.svelte";
  import { bandPath, equityWalk, extent, seeded } from "$lib/qmx/charts";
  import { cn } from "$lib/utils";

  // DEMO backtest lab over QMB's validation ladder (docs/components/qmb.md):
  // backtest, walk-forward, optimise, Monte Carlo, significance, sweep.
  // Genetic search is not in QMB v1 and is shown as later. Every run is a
  // ledger line with a role; only confirmation runs count toward a verdict.
  type Exp = {
    id: string;
    label: string;
    what: string;
    cli: string;
    later?: boolean;
  };
  const EXPERIMENTS: Exp[] = [
    {
      id: "backtest",
      label: "Backtest",
      what: "One run over a period with costs.",
      cli: "qmb backtest us500-trend --book IDX-L --from 2019-01 --to 2026-09",
    },
    {
      id: "walkforward",
      label: "Walk-forward",
      what: "Fit on a window, test on the next, roll forward.",
      cli: "qmb walk-forward us500-trend --folds 12 --embargo 24",
    },
    {
      id: "optimise",
      label: "Optimise",
      what: "Search parameters (adaptive or grid) with an overfit check.",
      cli: "qmb optimize us500-trend --sampler tpe --trials 200",
    },
    {
      id: "montecarlo",
      label: "Monte Carlo",
      what: "Shuffle trades and perturb candles to see the spread.",
      cli: "qmb robustness us500-trend --monte-carlo 1000",
    },
    {
      id: "significance",
      label: "Significance",
      what: "Is the signal better than a zero-edge null?",
      cli: "qmb robustness us500-trend --significance --bootstrap 5000",
    },
    {
      id: "sweep",
      label: "Sweep",
      what: "Same bot across symbols, timeframes and parameters.",
      cli: "qmb sweep us500-trend --symbols US500,NAS100,DE40 --tf H1,H4",
    },
    {
      id: "genetic",
      label: "Genetic search",
      what: "Evolve rules and parameters. Not in QMB v1.",
      cli: "",
      later: true,
    },
  ];
  let exp = $state("walkforward");
  const current = $derived(EXPERIMENTS.find((e) => e.id === exp)!);
  let view = $state("compare");

  const RUNS = [
    {
      id: "run-441",
      exp: "Walk-forward",
      role: "confirmation",
      status: "done",
      pct: 100,
      sharpe: "1.42",
      dd: "−6.8%",
      when: "12:10",
    },
    {
      id: "run-442",
      exp: "Monte Carlo",
      role: "replicate",
      status: "running",
      pct: 64,
      sharpe: "—",
      dd: "—",
      when: "now",
    },
    {
      id: "run-443",
      exp: "Optimise",
      role: "trial",
      status: "queued",
      pct: 0,
      sharpe: "—",
      dd: "—",
      when: "next",
    },
    {
      id: "run-438",
      exp: "Backtest",
      role: "trial",
      status: "done",
      pct: 100,
      sharpe: "1.27",
      dd: "−8.4%",
      when: "Sep 27",
    },
    {
      id: "run-431",
      exp: "Sweep",
      role: "trial",
      status: "failed",
      pct: 38,
      sharpe: "—",
      dd: "—",
      when: "Sep 26",
    },
  ];
  const STATUS = {
    done: "text-success",
    running: "text-info",
    queued: "text-muted-foreground",
    failed: "text-destructive",
  };

  // Compare: three runs' equity.
  const compare = [
    {
      label: "Walk-forward · run-441",
      values: equityWalk(4, 120, 0.0014),
      color: "var(--chart-1)",
    },
    {
      label: "Backtest · run-438",
      values: equityWalk(9, 120, 0.0011),
      color: "var(--chart-2)",
    },
    {
      label: "Buy and hold",
      values: equityWalk(21, 120, 0.0004),
      color: "var(--muted-foreground)",
      dashed: true,
    },
  ];

  // Monte Carlo: percentile band from many shuffled paths.
  const paths = Array.from({ length: 60 }, (_, k) =>
    equityWalk(100 + k, 100, 0.0012, 0.014),
  );
  const pct = (q: number) =>
    paths[0].map((_, i) => {
      const col = paths.map((p) => p[i]).sort((a, b) => a - b);
      return col[Math.floor(q * (col.length - 1))];
    });
  const p5 = pct(0.05),
    p50 = pct(0.5),
    p95 = pct(0.95);
  const mcDomain = extent([...p5, ...p95]);
  const mcBand = bandPath(p5, p95, 600, 200, mcDomain);

  // Optimise: Sharpe over fast × slow grid.
  const FAST = [10, 15, 20, 25, 30, 35];
  const SLOW = [60, 70, 80, 90, 100, 110, 120];
  const r = seeded(7);
  const grid = FAST.map((f) =>
    SLOW.map(
      (s) =>
        +(
          1.6 -
          Math.abs(f - 20) / 18 -
          Math.abs(s - 80) / 70 +
          (r() - 0.5) * 0.25
        ).toFixed(2),
    ),
  );
  const heat = (v: number) =>
    `background: color-mix(in oklab, var(--success) ${Math.round(Math.max(0, Math.min(1, v / 1.6)) * 70)}%, transparent)`;

  // Walk-forward: in-sample vs out-of-sample Sharpe per fold.
  const folds = Array.from({ length: 12 }, (_, i) => ({
    is: 1.3 + r() * 0.6,
    oos: 0.6 + r() * 1.0,
    i,
  }));

  const LOG = [
    "qmb 0.9 · lane governed · writer ws-01",
    "resolved run-config fp1:7a2e…19c4 (bot us500-trend v3, book IDX-L)",
    "data verify US500 H4 2019-01..2026-09 ok (0 gaps)",
    "fold  1/12 train 2019-01..2020-06 test 2020-07..2020-12  sharpe 1.21",
    "fold  2/12 train 2019-07..2020-12 test 2021-01..2021-06  sharpe 0.94",
    "…",
    "fold 12/12 train 2024-07..2025-12 test 2026-01..2026-09  sharpe 1.58",
    "CT-32 written · result_label confirmation · ledger line 441",
  ];
</script>

<svelte:head><title>Backtest lab · QMX</title></svelte:head>

<div class="flex h-full flex-col">
  <div class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs">
    <FlaskConical class="text-warning size-3.5" /> Demo lab. Sample runs and results;
    nothing was run.
  </div>
  <header class="flex h-11 shrink-0 items-center gap-3 border-b px-3">
    <span class="text-sm font-semibold">Backtest lab</span>
    <Badge variant="outline" class="h-4 px-1.5 text-[10px]">QMB</Badge>
    <span class="bg-muted rounded-md px-2 py-0.5 text-sm">US500 Trend · v3</span
    >
    <span class="text-muted-foreground text-sm"
      >book IDX-L · costs: default spread</span
    >
    <Tabs.Root bind:value={view} class="ml-auto">
      <Tabs.List variant="line">
        <Tabs.Trigger value="compare">Compare</Tabs.Trigger>
        <Tabs.Trigger value="montecarlo">Monte Carlo</Tabs.Trigger>
        <Tabs.Trigger value="optimise">Optimise</Tabs.Trigger>
        <Tabs.Trigger value="walkforward">Walk-forward</Tabs.Trigger>
      </Tabs.List>
    </Tabs.Root>
  </header>

  <Resizable.PaneGroup direction="horizontal" class="min-h-0 flex-1">
    <Resizable.Pane defaultSize={24} minSize={18} maxSize={34}>
      <aside
        aria-label="Experiment"
        class="bg-panel flex h-full flex-col gap-2 overflow-auto p-3"
      >
        <p class="panel-label">New experiment</p>
        <ul
          class="flex flex-col gap-1"
          role="radiogroup"
          aria-label="Experiment type"
        >
          {#each EXPERIMENTS as e (e.id)}
            <li>
              <button
                type="button"
                role="radio"
                aria-checked={exp === e.id}
                disabled={e.later}
                class={cn(
                  "flex w-full flex-col rounded-md px-2.5 py-2 text-left transition-colors",
                  exp === e.id ? "bg-muted" : "hover:bg-muted/60",
                  e.later && "opacity-50",
                )}
                onclick={() => (exp = e.id)}
              >
                <span class="flex items-center gap-1.5 text-sm font-medium"
                  >{e.label}{#if e.later}<Lock class="size-3" />
                    <span class="text-xs font-normal">later</span>{/if}</span
                >
                <span class="text-muted-foreground text-xs">{e.what}</span>
              </button>
            </li>
          {/each}
        </ul>
        <div class="mt-2 flex flex-col gap-2 border-t pt-3">
          <label class="flex flex-col gap-1 text-xs"
            ><span class="text-muted-foreground">Period</span><Input
              class="h-8"
              value="2019-01 → 2026-09"
              disabled
            /></label
          >
          <label class="flex flex-col gap-1 text-xs"
            ><span class="text-muted-foreground">Condition preset</span><Input
              class="h-8"
              value="default spread"
              disabled
            /></label
          >
          <p class="text-muted-foreground font-mono text-[11px] break-all">
            {current.cli}
          </p>
          <Button size="sm" disabled><Play /> Queue run (needs daemon)</Button>
        </div>
      </aside>
    </Resizable.Pane>
    <Resizable.Handle />
    <Resizable.Pane defaultSize={76}>
      <div class="flex h-full flex-col gap-3 overflow-auto p-3">
        <WidgetFrame
          title={view === "compare"
            ? "Equity · three runs"
            : view === "montecarlo"
              ? "Monte Carlo · 1,000 shuffles (p5–p95)"
              : view === "optimise"
                ? "Sharpe by fast × slow average"
                : "Walk-forward · Sharpe per fold"}
          class="min-h-72"
        >
          {#if view === "compare"}
            <LineChart series={compare} height={220} />
          {:else if view === "montecarlo"}
            <LineChart
              series={[
                { label: "Median path", values: p50, color: "var(--chart-1)" },
                {
                  label: "5th percentile",
                  values: p5,
                  color: "var(--destructive)",
                  dashed: true,
                },
                {
                  label: "95th percentile",
                  values: p95,
                  color: "var(--success)",
                  dashed: true,
                },
              ]}
              band={{ path: mcBand, color: "var(--chart-1)" }}
              height={200}
            />
          {:else if view === "optimise"}
            <div class="overflow-auto">
              <table class="num text-xs">
                <thead
                  ><tr
                    ><th
                      class="text-muted-foreground px-2 py-1 text-left font-normal"
                      >fast \ slow</th
                    >{#each SLOW as s (s)}<th
                        class="text-muted-foreground px-2 font-normal">{s}</th
                      >{/each}</tr
                  ></thead
                >
                <tbody>
                  {#each grid as row, i (i)}
                    <tr>
                      <th
                        class="text-muted-foreground px-2 py-1 text-left font-normal"
                        >{FAST[i]}</th
                      >
                      {#each row as v, j (j)}<td class="px-1 py-0.5"
                          ><span
                            class="block rounded px-2 py-1.5 text-center"
                            style={heat(v)}>{v.toFixed(2)}</span
                          ></td
                        >{/each}
                    </tr>
                  {/each}
                </tbody>
              </table>
              <p class="text-muted-foreground mt-2 text-xs">
                A broad bright plateau is safer than a single bright cell: the
                sensitivity check flags isolated peaks as likely overfit.
              </p>
            </div>
          {:else}
            <div class="flex h-48 items-end gap-2">
              {#each folds as f (f.i)}
                <div
                  class="flex flex-1 items-end gap-0.5"
                  title="Fold {f.i + 1}: in-sample {f.is.toFixed(
                    2,
                  )}, out-of-sample {f.oos.toFixed(2)}"
                >
                  <span
                    class="bg-muted-foreground/40 w-1/2 rounded-t-sm"
                    style="height: {f.is * 80}px"
                  ></span>
                  <span
                    class="bg-chart-1 w-1/2 rounded-t-sm"
                    style="height: {f.oos * 80}px"
                  ></span>
                </div>
              {/each}
            </div>
            <p class="text-muted-foreground mt-2 flex gap-4 text-xs">
              <span
                ><span
                  class="bg-muted-foreground/40 mr-1 inline-block size-2 rounded-sm"
                ></span>In-sample</span
              ><span
                ><span class="bg-chart-1 mr-1 inline-block size-2 rounded-sm"
                ></span>Out-of-sample</span
              >
            </p>
          {/if}
        </WidgetFrame>

        <div class="grid min-h-64 gap-3 xl:grid-cols-2">
          <WidgetFrame title="Runs">
            <table class="w-full text-sm">
              <thead class="text-muted-foreground text-left text-xs">
                <tr
                  ><th class="pb-1.5 font-medium">Run</th><th
                    class="font-medium">Experiment</th
                  ><th class="font-medium">Role</th><th class="font-medium"
                    >Status</th
                  ><th class="text-right font-medium">Sharpe</th><th
                    class="text-right font-medium">Max DD</th
                  ></tr
                >
              </thead>
              <tbody>
                {#each RUNS as run (run.id)}
                  <tr class="border-t">
                    <td class="num py-2 text-xs">{run.id}</td>
                    <td>{run.exp}</td>
                    <td class="text-muted-foreground">{run.role}</td>
                    <td>
                      <span
                        class={cn(
                          "text-xs",
                          STATUS[run.status as keyof typeof STATUS],
                        )}>{run.status}</span
                      >
                      {#if run.status === "running"}<span
                          class="bg-muted mt-1 block h-1 w-20 rounded-full"
                          ><span
                            class="bg-info block h-1 rounded-full"
                            style="width: {run.pct}%"
                          ></span></span
                        >{/if}
                    </td>
                    <td class="num text-right">{run.sharpe}</td>
                    <td class="num text-right">{run.dd}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </WidgetFrame>
          <WidgetFrame title="Console · run-441">
            <RunConsole
              command={EXPERIMENTS[1].cli}
              lines={LOG}
              status="done"
            />
          </WidgetFrame>
        </div>
      </div>
    </Resizable.Pane>
  </Resizable.PaneGroup>
</div>
