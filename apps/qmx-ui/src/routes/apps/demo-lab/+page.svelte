<script lang="ts">
  import Play from "@lucide/svelte/icons/play";
  import Lock from "@lucide/svelte/icons/lock";
  import Check from "@lucide/svelte/icons/check";
  import X from "@lucide/svelte/icons/x";
  import Minus from "@lucide/svelte/icons/minus";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import { Input } from "$lib/components/ui/input";
  import MiniAppShell from "$lib/workbench/MiniAppShell.svelte";
  import { WidgetBoard } from "$lib/workbench/board.svelte";
  import LineChart from "$lib/qmx/LineChart.svelte";
  import RunConsole from "$lib/qmx/RunConsole.svelte";
  import { bandPath, equityWalk, extent, seeded } from "$lib/qmx/charts";
  import { cn } from "$lib/utils";

  // DEMO backtest lab over QMB (docs/components/qmb.md): validation ladder,
  // run roles (verdict = read-time fold over confirmation runs), one run per
  // environment (the governor queues, never oversubscribes), three lanes
  // chosen by the door. Patterns borrowed from StrategyQuant: Run/Settings/
  // Results skeleton, cost-tiered checks with early exit, what-if over the
  // trade list, walk-forward matrix with a cluster rule. Genetic search is
  // not in QMB v1.
  const EXPERIMENTS = [
    {
      id: "backtest",
      label: "Backtest",
      what: "One run over a period with costs.",
      cli: "qmb backtest us500-trend --book IDX-L",
    },
    {
      id: "walkforward",
      label: "Walk-forward",
      what: "Fit, test the next window, roll.",
      cli: "qmb walk-forward us500-trend --folds 12 --embargo 24",
    },
    {
      id: "optimise",
      label: "Optimise",
      what: "Search parameters with an overfit check.",
      cli: "qmb optimize us500-trend --sampler tpe --trials 200",
    },
    {
      id: "robustness",
      label: "Robustness",
      what: "Monte Carlo, significance, what-if.",
      cli: "qmb robustness us500-trend --monte-carlo 1000",
    },
    {
      id: "sweep",
      label: "Sweep",
      what: "Across symbols, timeframes, parameters.",
      cli: "qmb sweep us500-trend --symbols US500,NAS100,DE40",
    },
    {
      id: "genetic",
      label: "Genetic search",
      what: "Evolve rules. Not in QMB v1.",
      cli: "",
      later: true,
    },
  ];
  let exp = $state("walkforward");
  const current = $derived(EXPERIMENTS.find((e) => e.id === exp)!);
  const LANES = [
    { id: "ungoverned", label: "Scratch", note: "qmb.run(); nothing recorded" },
    { id: "governed", label: "Governed", note: "Ledger line + evidence" },
    {
      id: "coordinated",
      label: "Coordinated",
      note: "Placed by an agent under a spec",
    },
  ];
  let lane = $state("governed");

  const RUNS = [
    {
      id: "run-441",
      exp: "Walk-forward",
      role: "confirmation",
      status: "done",
      sharpe: "1.42",
      dd: "−6.8%",
      trades: 187,
      when: "12:10",
    },
    {
      id: "run-442",
      exp: "Monte Carlo",
      role: "replicate",
      status: "running",
      sharpe: "—",
      dd: "—",
      trades: 0,
      when: "now",
    },
    {
      id: "run-443",
      exp: "Optimise",
      role: "trial",
      status: "queued",
      sharpe: "—",
      dd: "—",
      trades: 0,
      when: "next",
    },
    {
      id: "run-438",
      exp: "Backtest",
      role: "trial",
      status: "done",
      sharpe: "1.27",
      dd: "−8.4%",
      trades: 598,
      when: "Sep 27",
    },
    {
      id: "run-436",
      exp: "Significance",
      role: "confirmation",
      status: "done",
      sharpe: "p = 0.012",
      dd: "—",
      trades: 187,
      when: "Sep 27",
    },
    {
      id: "run-431",
      exp: "Sweep",
      role: "trial",
      status: "failed",
      sharpe: "—",
      dd: "—",
      trades: 0,
      when: "Sep 26",
    },
    {
      id: "run-429",
      exp: "Backtest",
      role: "aborted",
      status: "unknown",
      sharpe: "—",
      dd: "—",
      trades: 0,
      when: "Sep 26",
    },
  ];
  const STATUS: Record<string, string> = {
    done: "text-success",
    running: "text-info",
    queued: "text-muted-foreground",
    failed: "text-destructive",
    unknown: "text-warning",
  };

  const base = equityWalk(4, 120, 0.0014);
  const compare = [
    { label: "Walk-forward · run-441", values: base, color: "var(--chart-1)" },
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

  const paths = Array.from({ length: 60 }, (_, k) =>
    equityWalk(100 + k, 100, 0.0012, 0.014),
  );
  const pct = (q: number) =>
    paths[0].map((_, i) => {
      const col = paths.map((p) => p[i]).sort((a, b) => a - b);
      return col[Math.floor(q * (col.length - 1))];
    });
  const p5 = pct(0.05);
  const p50 = pct(0.5);
  const p95 = pct(0.95);
  const mcBand = bandPath(p5, p95, 600, 200, extent([...p5, ...p95]));
  const MC_TABLE = [
    ["80%", "+14.1%", "−8.9%"],
    ["90%", "+11.6%", "−10.4%"],
    ["95%", "+9.8%", "−11.2%"],
  ];

  const r = seeded(7);
  const FAST = [10, 15, 20, 25, 30, 35];
  const SLOW = [60, 70, 80, 90, 100, 110, 120];
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

  // Walk-forward matrix: runs (rows) × out-of-sample % (columns), pass/fail.
  const WF_RUNS = [5, 8, 10, 12, 15];
  const WF_OOS = [15, 20, 25, 30, 35];
  const wf = WF_RUNS.map((n, i) =>
    WF_OOS.map(
      (o, j) => (i >= 1 && i <= 3 && j >= 1 && j <= 3) || (i + j) % 4 === 0,
    ),
  );
  const wfPass = wf.flat().filter(Boolean).length;
  let wfCell = $state<[number, number]>([2, 2]);

  // Robustness checks, cheapest first; a failure stops the slower ones.
  const CHECKS = [
    {
      name: "Higher-precision backtest",
      tier: "Fast",
      cost: "≈ 4 s",
      state: "pass",
    },
    { name: "What-if scenarios", tier: "Fast", cost: "≈ 1 s", state: "pass" },
    {
      name: "Monte Carlo · trade shuffle",
      tier: "Fast",
      cost: "≈ 6 s",
      state: "pass",
    },
    {
      name: "Other markets (NAS100, DE40)",
      tier: "Standard",
      cost: "≈ 40 s",
      state: "fail",
    },
    {
      name: "Monte Carlo · parameter perturbation",
      tier: "Standard",
      cost: "≈ 50 s",
      state: "skipped",
    },
    {
      name: "Walk-forward matrix",
      tier: "Extensive",
      cost: "≈ 6 min",
      state: "skipped",
    },
  ];
  const WHATIF = [
    {
      name: "Skip Mondays",
      rule: "≥ 80% of baseline profit",
      result: "92%",
      pass: true,
    },
    {
      name: "Drop best 5% of trades",
      rule: "≥ 60% of baseline profit",
      result: "71%",
      pass: true,
    },
    {
      name: "One trade per day",
      rule: "≥ 80% of baseline profit",
      result: "64%",
      pass: false,
    },
  ];
  const whatIfCurve = base.map((v, i) => v * (1 - i * 0.0006));

  const LOG = [
    "qmb 0.9 · lane governed · environment ws-01 (1 of 1 busy)",
    "resolved run-config fp1:7a2e…19c4 (bot us500-trend v3, book IDX-L)",
    "data verify US500 H4 2019-01..2026-09 ok (0 gaps)",
    "fold  1/12 train 2019-01..2020-06 test 2020-07..2020-12  sharpe 1.21",
    "fold  2/12 train 2019-07..2020-12 test 2021-01..2021-06  sharpe 0.94",
    "…",
    "fold 12/12 train 2024-07..2025-12 test 2026-01..2026-09  sharpe 1.58",
    "CT-32 written · role confirmation · ledger line 441",
  ];

  const W = {
    runs: { id: "runs", title: "Runs", size: "full" },
    compare: {
      id: "compare",
      title: "Equity · compare runs",
      size: "lg",
      tall: true,
    },
    mc: {
      id: "mc",
      title: "Monte Carlo · 1,000 shuffles",
      size: "lg",
      tall: true,
    },
    wf: { id: "wf", title: "Walk-forward matrix", size: "md" },
    opt: { id: "opt", title: "Optimise · Sharpe by fast × slow", size: "md" },
    checks: { id: "checks", title: "Robustness checks", size: "md" },
    whatif: {
      id: "whatif",
      title: "What-if scenarios",
      size: "lg",
      tall: true,
    },
    queue: { id: "queue", title: "Queue", size: "md" },
    console: { id: "console", title: "Console · run-441", size: "lg" },
  } as const;
  const board = new WidgetBoard({
    Results: [W.compare, W.mc, W.wf, W.opt, W.checks, W.runs],
    Robustness: [W.checks, W.whatif, W.mc, W.wf],
    Run: [W.queue, W.console, W.runs],
  });
</script>

<svelte:head><title>Backtest lab · QMX</title></svelte:head>

{#snippet header()}
  <span class="bg-muted rounded-md px-2 py-0.5 text-sm">US500 Trend · v3</span>
  <span class="text-muted-foreground text-sm"
    >book IDX-L · costs: default spread</span
  >
{/snippet}

{#snippet sidebar()}
  <div class="flex flex-col gap-3 p-3">
    <div>
      <p class="panel-label mb-1.5">New experiment</p>
      <ul
        class="flex flex-col gap-0.5"
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
                "flex w-full flex-col rounded-md px-2.5 py-1.5 text-left",
                exp === e.id ? "bg-muted" : "hover:bg-muted/60",
                e.later && "opacity-50",
              )}
              onclick={() => (exp = e.id)}
            >
              <span class="flex items-center gap-1.5 text-sm font-medium">
                {e.label}{#if e.later}<Lock class="size-3" /><span
                    class="text-xs font-normal">later</span
                  >{/if}
              </span>
              <span class="text-muted-foreground text-xs">{e.what}</span>
            </button>
          </li>
        {/each}
      </ul>
    </div>
    <div>
      <p class="panel-label mb-1.5">Lane</p>
      <div class="flex flex-col gap-0.5" role="radiogroup" aria-label="Lane">
        {#each LANES as l (l.id)}
          <button
            type="button"
            role="radio"
            aria-checked={lane === l.id}
            class={cn(
              "rounded-md px-2.5 py-1.5 text-left",
              lane === l.id ? "bg-muted" : "hover:bg-muted/60",
            )}
            onclick={() => (lane = l.id)}
          >
            <span class="block text-sm">{l.label}</span>
            <span class="text-muted-foreground block text-xs">{l.note}</span>
          </button>
        {/each}
      </div>
    </div>
    <div class="flex flex-col gap-2 border-t pt-3">
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
  </div>
{/snippet}

{#snippet body(id: string)}
  {#if id === "runs"}
    <table class="w-full text-sm">
      <thead class="text-muted-foreground text-left text-xs">
        <tr>
          <th class="pb-1.5 font-medium">Run</th><th class="font-medium"
            >Experiment</th
          ><th class="font-medium">Role</th>
          <th class="font-medium">Status</th><th class="text-right font-medium"
            >Sharpe</th
          ><th class="text-right font-medium">Max DD</th>
          <th class="text-right font-medium">Trades</th><th
            class="text-right font-medium">When</th
          >
        </tr>
      </thead>
      <tbody>
        {#each RUNS as run (run.id)}
          <tr class="hover:bg-muted/40 border-t">
            <td class="num py-2 text-xs">{run.id}</td>
            <td>{run.exp}</td>
            <td
              class={run.role === "confirmation"
                ? "text-success"
                : "text-muted-foreground"}>{run.role}</td
            >
            <td class={cn("text-xs", STATUS[run.status])}
              >{run.status}{run.status === "unknown" ? " · not failed" : ""}</td
            >
            <td class="num text-right">{run.sharpe}</td>
            <td class="num text-right">{run.dd}</td>
            <td class="num text-right">{run.trades || "—"}</td>
            <td class="text-muted-foreground text-right">{run.when}</td>
          </tr>
        {/each}
      </tbody>
    </table>
    <p class="text-muted-foreground mt-2 text-xs">
      Only confirmation runs count toward a verdict. Comparing runs with
      different data splits is refused.
    </p>
  {:else if id === "compare"}
    <LineChart series={compare} height={240} />
  {:else if id === "mc"}
    <div class="flex h-full flex-col gap-2">
      <div class="min-h-0 flex-1">
        <LineChart
          series={[
            { label: "Median", values: p50, color: "var(--chart-1)" },
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
      </div>
      <table class="num w-full text-xs">
        <thead class="text-muted-foreground"
          ><tr
            ><th class="text-left font-normal">Confidence</th><th
              class="text-right font-normal">Net return</th
            ><th class="text-right font-normal">Max drawdown</th></tr
          ></thead
        >
        <tbody>
          {#each MC_TABLE as [c, ret, dd] (c)}
            <tr class="border-t"
              ><td class="py-1">{c}</td><td class="text-right">{ret}</td><td
                class="text-destructive text-right">{dd}</td
              ></tr
            >
          {/each}
        </tbody>
      </table>
    </div>
  {:else if id === "wf"}
    <div class="flex flex-col gap-2">
      <table class="num text-xs">
        <thead
          ><tr
            ><th class="text-muted-foreground px-1 text-left font-normal"
              >runs \ OOS</th
            >{#each WF_OOS as o (o)}<th
                class="text-muted-foreground px-1 font-normal">{o}%</th
              >{/each}</tr
          ></thead
        >
        <tbody>
          {#each wf as row, i (i)}
            <tr>
              <th class="text-muted-foreground px-1 text-left font-normal"
                >{WF_RUNS[i]}</th
              >
              {#each row as ok, j (j)}
                <td class="p-0.5">
                  <button
                    type="button"
                    aria-label="{WF_RUNS[i]} runs, {WF_OOS[
                      j
                    ]}% out of sample: {ok ? 'pass' : 'fail'}"
                    class={cn(
                      "block h-7 w-full rounded",
                      ok ? "bg-success/45" : "bg-destructive/35",
                      wfCell[0] === i &&
                        wfCell[1] === j &&
                        "ring-foreground ring-2",
                    )}
                    onclick={() => (wfCell = [i, j])}
                  ></button>
                </td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
      <p class="text-muted-foreground text-xs">
        {wfPass} of 25 pass. Rule: a 3×3 block with at least 7 passes. Selected: {WF_RUNS[
          wfCell[0]
        ]} runs, {WF_OOS[wfCell[1]]}% OOS.
      </p>
    </div>
  {:else if id === "opt"}
    <table class="num text-xs">
      <thead
        ><tr
          ><th class="text-muted-foreground px-1 text-left font-normal"
            >fast \ slow</th
          >{#each SLOW as s (s)}<th
              class="text-muted-foreground px-1 font-normal">{s}</th
            >{/each}</tr
        ></thead
      >
      <tbody>
        {#each grid as row, i (i)}
          <tr>
            <th class="text-muted-foreground px-1 text-left font-normal"
              >{FAST[i]}</th
            >
            {#each row as v, j (j)}<td class="p-0.5"
                ><span
                  class="block rounded px-1.5 py-1 text-center"
                  style={heat(v)}>{v.toFixed(2)}</span
                ></td
              >{/each}
          </tr>
        {/each}
      </tbody>
    </table>
    <p class="text-muted-foreground mt-2 text-xs">
      Prefer a broad plateau to one bright cell; isolated peaks are flagged as
      likely overfit.
    </p>
  {:else if id === "checks"}
    <ol class="flex flex-col">
      {#each CHECKS as c (c.name)}
        <li
          class="flex items-center gap-2 border-b py-1.5 text-sm last:border-0"
        >
          {#if c.state === "pass"}<Check
              class="text-success size-4 shrink-0"
            />{:else if c.state === "fail"}<X
              class="text-destructive size-4 shrink-0"
            />{:else}<Minus
              class="text-muted-foreground size-4 shrink-0"
            />{/if}
          <span
            class={cn(
              "min-w-0 flex-1 truncate",
              c.state === "skipped" && "text-muted-foreground",
            )}>{c.name}</span
          >
          <Badge variant="outline" class="h-4 px-1.5 text-[10px]"
            >{c.tier}</Badge
          >
          <span class="num text-muted-foreground w-14 text-right text-xs"
            >{c.cost}</span
          >
        </li>
      {/each}
    </ol>
    <p class="text-muted-foreground mt-2 text-xs">
      Cheapest first. A failure skips the slower checks; "run all anyway" is for
      diagnosis only.
    </p>
  {:else if id === "whatif"}
    <div class="flex h-full flex-col gap-2">
      <ul class="flex flex-col">
        {#each WHATIF as w (w.name)}
          <li
            class="flex items-center gap-2 border-b py-1.5 text-sm last:border-0"
          >
            {#if w.pass}<Check class="text-success size-4" />{:else}<X
                class="text-destructive size-4"
              />{/if}
            <span class="flex-1">{w.name}</span>
            <span class="text-muted-foreground text-xs">{w.rule}</span>
            <span class="num w-12 text-right">{w.result}</span>
          </li>
        {/each}
      </ul>
      <div class="min-h-0 flex-1">
        <LineChart
          series={[
            { label: "Baseline", values: base, color: "var(--chart-1)" },
            {
              label: "One trade per day",
              values: whatIfCurve,
              color: "var(--warning)",
              dashed: true,
            },
          ]}
          height={160}
        />
      </div>
      <p class="text-muted-foreground text-xs">
        What-if replays the existing trades under a changed rule; no new
        backtest.
      </p>
    </div>
  {:else if id === "queue"}
    <ul class="flex flex-col gap-2 text-sm">
      <li class="well rounded-lg p-3">
        <span class="font-medium">run-442 · Monte Carlo</span><span
          class="text-info block text-xs">Running on ws-01 · 64%</span
        ><span class="bg-muted mt-1.5 block h-1.5 rounded-full"
          ><span class="bg-info block h-1.5 rounded-full" style="width: 64%"
          ></span></span
        >
      </li>
      <li class="well rounded-lg p-3">
        <span class="font-medium">run-443 · Optimise</span><span
          class="text-muted-foreground block text-xs"
          >Queued: one run per environment</span
        >
      </li>
    </ul>
  {:else if id === "console"}
    <RunConsole command={EXPERIMENTS[1].cli} lines={LOG} status="done" />
  {/if}
{/snippet}

<MiniAppShell
  {board}
  name="Backtest lab"
  badge="QMB · DEMO"
  demoNote="Demo lab. Sample runs and results; nothing was run."
  headerExtra={header}
  {sidebar}
  widget={body}
/>
