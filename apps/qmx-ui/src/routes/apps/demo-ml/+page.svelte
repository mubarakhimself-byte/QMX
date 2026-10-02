<script lang="ts">
  import Check from "@lucide/svelte/icons/check";
  import CircleAlert from "@lucide/svelte/icons/circle-alert";
  import Cpu from "@lucide/svelte/icons/cpu";
  import BookOpen from "@lucide/svelte/icons/book-open";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import MiniAppShell from "$lib/workbench/MiniAppShell.svelte";
  import { WidgetBoard } from "$lib/workbench/board.svelte";
  import LineChart from "$lib/qmx/LineChart.svelte";
  import { seeded } from "$lib/qmx/charts";
  import { cn } from "$lib/utils";

  // DEMO ML Studio: a first-party mini app whose sidebar is the ML pipeline
  // (architecture-QMX-UI-2026-09-23/AUTHORING-AND-ML.md: dataset, features,
  // split, leakage check, model config, execution target, results with
  // lineage). The same steps can run as a workflow. "Slots" are this
  // design's proposal: the docs have no ML-model entity yet.
  const STEPS = [
    {
      id: "dataset",
      label: "Dataset",
      detail: "fx-majors H1 2019–2026 · 214 MB",
      view: "Data",
    },
    {
      id: "features",
      label: "Features",
      detail: "ATR 14, RSI 14, session flags",
      view: "Data",
    },
    {
      id: "split",
      label: "Split",
      detail: "Walk-forward, 12 folds, 24-bar embargo",
      view: "Data",
    },
    {
      id: "leakage",
      label: "Leakage checks",
      detail: "6 of 6 pass",
      view: "Data",
    },
    {
      id: "model",
      label: "Model",
      detail: "LightGBM · 400 trees · lr 0.03",
      view: "Evaluate",
    },
    {
      id: "evaluate",
      label: "Evaluate",
      detail: "AUC 0.61 ± 0.03",
      view: "Evaluate",
    },
    {
      id: "slots",
      label: "Plug in",
      detail: "Not plugged in yet",
      view: "Plug in",
      open: true,
    },
  ];

  const r = seeded(11);
  const epochs = 60;
  const train = Array.from(
    { length: epochs },
    (_, i) => 0.69 - 0.12 * (1 - Math.exp(-i / 12)) + (r() - 0.5) * 0.004,
  );
  const valid = Array.from(
    { length: epochs },
    (_, i) =>
      0.69 -
      0.07 * (1 - Math.exp(-i / 10)) +
      Math.max(0, i - 38) * 0.0009 +
      (r() - 0.5) * 0.006,
  );
  const IMPORTANCE: [string, number][] = [
    ["ATR 14 percentile", 0.31],
    ["RSI 14", 0.22],
    ["London session", 0.17],
    ["Distance from 20-bar high", 0.13],
    ["Day of week", 0.07],
    ["New York session", 0.06],
    ["Spread", 0.04],
  ];
  const FOLDS = Array.from({ length: 12 }, () => 0.57 + r() * 0.08);
  const CONFUSION = { tp: 1180, fp: 870, fn: 940, tn: 1460 };
  const DATASET: [string, string][] = [
    ["Provider", "Dukascopy (personal use)"],
    ["Coverage", "2019-01 → 2026-09, 0 gaps"],
    ["Units", "Price, quote currency"],
    ["Time zone", "UTC · FX calendar"],
    ["Freshness", "Refreshed today 14:05"],
    ["Revision", "fp1:c3d2…0f8e"],
  ];
  const FEATURES = [
    { name: "ATR 14 percentile", kind: "Volatility", nulls: "0.0%" },
    { name: "RSI 14", kind: "Momentum", nulls: "0.0%" },
    { name: "London / New York session", kind: "Calendar", nulls: "0.0%" },
    { name: "Distance from 20-bar high", kind: "Structure", nulls: "0.2%" },
  ];
  const LEAKAGE = [
    "Purge between train and test",
    "24-bar embargo",
    "No future bars in features",
    "Labels use only past prices",
    "Scaler fitted on train only",
    "No duplicate rows across folds",
  ];
  const SLOTS = [
    {
      slot: "Position sizing",
      who: "Book FX-L sizing policy",
      now: "Fixed 0.5% risk",
      fits: true,
    },
    {
      slot: "Market intelligence (regime)",
      who: "MIS on the node",
      now: "Rule-based (v1)",
      fits: false,
    },
    {
      slot: "Risk throttle",
      who: "Book exposure limits",
      now: "Static limits",
      fits: false,
    },
    {
      slot: "Stress testing",
      who: "Backtest lab scenarios",
      now: "Not used",
      fits: true,
    },
    {
      slot: "Entry signal",
      who: "EURUSD H1 GBM (bot)",
      now: "Rules only",
      fits: true,
    },
  ];
  const IDEAS = [
    {
      model: "Hamiltonian Monte Carlo (Bayesian)",
      n: 3,
      from: "Statistics and analysis",
    },
    { model: "Hidden Markov regimes", n: 5, from: "Machine learning" },
    {
      model: "Survival models for exits",
      n: 2,
      from: "Statistics and analysis",
    },
    { model: "Reinforcement learning agents", n: 4, from: "Trading systems" },
  ];

  const W = {
    dataset: { id: "dataset", title: "Dataset", size: "md" },
    features: { id: "features", title: "Features", size: "md" },
    leakage: { id: "leakage", title: "Leakage checks", size: "md" },
    training: {
      id: "training",
      title: "Training · log loss",
      size: "lg",
      tall: true,
    },
    importance: {
      id: "importance",
      title: "What the model looks at",
      size: "lg",
    },
    folds: { id: "folds", title: "AUC per fold", size: "md" },
    hits: { id: "hits", title: "Hits and misses (out of sample)", size: "md" },
    ideas: { id: "ideas", title: "Model ideas from your Library", size: "md" },
    slots: { id: "slots", title: "Where this model can plug in", size: "full" },
  } as const;
  const board = new WidgetBoard({
    Evaluate: [W.training, W.importance, W.folds, W.hits, W.ideas],
    Data: [W.dataset, W.features, W.leakage],
    "Plug in": [W.slots, W.ideas],
  });
</script>

<svelte:head><title>ML Studio · QMX</title></svelte:head>

{#snippet header()}
  <span class="bg-muted rounded-md px-2 py-0.5 text-sm"
    >EURUSD breakout scorer · v7</span
  >
  <Badge variant="outline" class="text-info">Research</Badge>
  <span class="text-muted-foreground flex items-center gap-1.5 text-sm"
    ><Cpu class="size-4" /> Last run 12:08 · 3m 41s</span
  >
{/snippet}

{#snippet sidebar()}
  <ol class="flex flex-col p-3" aria-label="Pipeline">
    {#each STEPS as s, i (s.id)}
      <li class="flex gap-3">
        <span class="flex flex-col items-center">
          <span
            class={cn(
              "flex size-6 items-center justify-center rounded-full border text-xs",
              s.open
                ? "text-muted-foreground"
                : "bg-success/15 border-success/40 text-success",
            )}
          >
            {#if s.open}{i + 1}{:else}<Check class="size-3.5" />{/if}
          </span>
          {#if i < STEPS.length - 1}<span class="bg-border my-1 w-px flex-1"
            ></span>{/if}
        </span>
        <button
          type="button"
          class={cn(
            "mb-2 flex-1 rounded-md px-2 py-1 text-left",
            board.view === s.view ? "bg-muted" : "hover:bg-muted/60",
          )}
          onclick={() => board.setView(s.view)}
        >
          <span class="block text-sm font-medium">{s.label}</span>
          <span class="text-muted-foreground block text-xs">{s.detail}</span>
        </button>
      </li>
    {/each}
  </ol>
  <p class="text-muted-foreground px-3 pb-3 text-xs">
    The same steps can run unattended as a workflow.
  </p>
{/snippet}

{#snippet body(id: string)}
  {#if id === "dataset"}
    <dl class="flex flex-col text-sm">
      {#each DATASET as [k, v] (k)}
        <div class="flex justify-between gap-3 border-b py-1.5 last:border-0">
          <dt class="text-muted-foreground">{k}</dt>
          <dd class="text-right">{v}</dd>
        </div>
      {/each}
    </dl>
  {:else if id === "features"}
    <table class="w-full text-sm">
      <thead class="text-muted-foreground text-left text-xs"
        ><tr
          ><th class="pb-1.5 font-medium">Feature</th><th class="font-medium"
            >Kind</th
          ><th class="text-right font-medium">Missing</th></tr
        ></thead
      >
      <tbody>
        {#each FEATURES as f (f.name)}
          <tr class="border-t"
            ><td class="py-1.5">{f.name}</td><td class="text-muted-foreground"
              >{f.kind}</td
            ><td class="num text-right">{f.nulls}</td></tr
          >
        {/each}
      </tbody>
    </table>
  {:else if id === "leakage"}
    <ul class="flex flex-col">
      {#each LEAKAGE as l (l)}
        <li
          class="flex items-center gap-2 border-b py-1.5 text-sm last:border-0"
        >
          <Check class="text-success size-4" />{l}
        </li>
      {/each}
    </ul>
  {:else if id === "training"}
    <div class="flex h-full flex-col gap-1">
      <div class="min-h-0 flex-1">
        <LineChart
          series={[
            { label: "Train", values: train, color: "var(--chart-1)" },
            { label: "Validation", values: valid, color: "var(--chart-2)" },
          ]}
          height={220}
        />
      </div>
      <p class="text-muted-foreground text-xs">
        Validation loss turns up after about epoch 38; early stopping kept epoch
        37.
      </p>
    </div>
  {:else if id === "importance"}
    <ul class="flex flex-col gap-2">
      {#each IMPORTANCE as [name, v] (name)}
        <li class="grid grid-cols-[11rem_1fr_3rem] items-center gap-2 text-sm">
          <span class="truncate">{name}</span>
          <span class="bg-muted h-2 rounded-full"
            ><span
              class="bg-chart-1 block h-2 rounded-full"
              style="width: {v * 300}%"
            ></span></span
          >
          <span class="num text-muted-foreground text-right text-xs"
            >{(v * 100).toFixed(0)}%</span
          >
        </li>
      {/each}
    </ul>
  {:else if id === "folds"}
    <div class="flex h-full flex-col">
      <div class="flex min-h-28 flex-1 items-end gap-1.5">
        {#each FOLDS as v, i (i)}
          <span
            class="bg-chart-2 flex-1 rounded-t-sm"
            style="height: {Math.min(100, ((v - 0.5) / 0.15) * 100)}%"
            title="Fold {i + 1}: {v.toFixed(3)}"
          ></span>
        {/each}
      </div>
      <p class="text-muted-foreground mt-1 text-xs">
        0.5 is a coin flip. Steady bars matter more than tall ones.
      </p>
    </div>
  {:else if id === "hits"}
    <div class="grid h-full grid-cols-2 gap-1.5 text-center">
      <div class="bg-success/20 flex flex-col justify-center rounded-md p-3">
        <p class="num text-xl font-semibold">{CONFUSION.tp}</p>
        <p class="text-muted-foreground text-xs">Called win, was win</p>
      </div>
      <div
        class="bg-destructive/15 flex flex-col justify-center rounded-md p-3"
      >
        <p class="num text-xl font-semibold">{CONFUSION.fp}</p>
        <p class="text-muted-foreground text-xs">Called win, was loss</p>
      </div>
      <div
        class="bg-destructive/10 flex flex-col justify-center rounded-md p-3"
      >
        <p class="num text-xl font-semibold">{CONFUSION.fn}</p>
        <p class="text-muted-foreground text-xs">Called loss, was win</p>
      </div>
      <div class="bg-success/10 flex flex-col justify-center rounded-md p-3">
        <p class="num text-xl font-semibold">{CONFUSION.tn}</p>
        <p class="text-muted-foreground text-xs">Called loss, was loss</p>
      </div>
    </div>
  {:else if id === "ideas"}
    <ul class="flex flex-col">
      {#each IDEAS as idea (idea.model)}
        <li class="flex items-center gap-2 border-b py-2 last:border-0">
          <BookOpen class="text-muted-foreground size-4 shrink-0" />
          <span class="min-w-0 flex-1"
            ><span class="block text-sm font-medium">{idea.model}</span><span
              class="text-muted-foreground block text-xs"
              >{idea.n} MQL5 articles · {idea.from}</span
            ></span
          >
        </li>
      {/each}
    </ul>
    <Button size="sm" variant="ghost" class="mt-1" href={resolve("/library")}
      >Browse Library</Button
    >
  {:else if id === "slots"}
    <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
      {#each SLOTS as s (s.slot)}
        <section class="well flex flex-col gap-2 rounded-xl p-3.5">
          <p class="font-medium">{s.slot}</p>
          <p class="text-muted-foreground text-sm">
            Used by {s.who}. Today: {s.now}.
          </p>
          <p
            class={cn(
              "flex items-center gap-1.5 text-xs",
              s.fits ? "text-success" : "text-warning",
            )}
          >
            {#if s.fits}<Check class="size-3.5" /> Output fits{:else}<CircleAlert
                class="size-3.5"
              /> Needs a regime label or risk score{/if}
          </p>
          <div class="mt-auto">
            <Button
              size="sm"
              variant="outline"
              aria-disabled="true"
              class="aria-disabled:opacity-60"
              title="Plugging in makes a new bot or book version; needs the daemon"
              onclick={(e) => e.preventDefault()}>Plug in…</Button
            >
          </div>
        </section>
      {/each}
    </div>
    <p class="text-muted-foreground mt-3 text-sm">
      Plugging in never changes a running bot. It makes a new version that must
      earn its own evidence.
    </p>
  {/if}
{/snippet}

<MiniAppShell
  {board}
  name="ML Studio"
  badge="DEMO"
  demoNote="Demo ML Studio. Sample training run; nothing was trained."
  headerExtra={header}
  {sidebar}
  copilot={{
    hint: "Ask why the model behaves as it does, or add a widget as context.",
    placeholder: "Ask about this model…",
  }}
  widget={body}
/>
