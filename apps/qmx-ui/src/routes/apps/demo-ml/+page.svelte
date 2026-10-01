<script lang="ts">
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import Check from "@lucide/svelte/icons/check";
  import CircleAlert from "@lucide/svelte/icons/circle-alert";
  import Cpu from "@lucide/svelte/icons/cpu";
  import BookOpen from "@lucide/svelte/icons/book-open";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import WidgetFrame from "$lib/workbench/WidgetFrame.svelte";
  import LineChart from "$lib/qmx/LineChart.svelte";
  import { seeded } from "$lib/qmx/charts";
  import { cn } from "$lib/utils";

  // DEMO ML Studio, a first-party mini app (not a fifth destination).
  // Pieces follow architecture-QMX-UI-2026-09-23/AUTHORING-AND-ML.md:
  // dataset, features, split, leakage check, model config, execution
  // target, run output with lineage. The docs have no ML-model entity yet:
  // "slots" are this design's proposal for where a model plugs in.
  const STEPS = [
    {
      id: "dataset",
      label: "Dataset",
      detail: "fx-majors H1 2019–2026 · 214 MB",
      ok: true,
    },
    {
      id: "features",
      label: "Features",
      detail: "ATR 14, RSI 14, session flags",
      ok: true,
    },
    {
      id: "split",
      label: "Split",
      detail: "Walk-forward, 12 folds, 24-bar embargo",
      ok: true,
    },
    { id: "leakage", label: "Leakage checks", detail: "6 of 6 pass", ok: true },
    {
      id: "model",
      label: "Model",
      detail: "LightGBM · 400 trees · lr 0.03",
      ok: true,
    },
    { id: "target", label: "Run on", detail: "This machine · CPU", ok: true },
    { id: "evaluate", label: "Evaluate", detail: "AUC 0.61 ± 0.03", ok: true },
    { id: "slots", label: "Plug in", detail: "Not plugged in yet", ok: false },
  ];
  let step = $state("evaluate");

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
  const IMPORTANCE = [
    ["ATR 14 percentile", 0.31],
    ["RSI 14", 0.22],
    ["London session", 0.17],
    ["Distance from 20-bar high", 0.13],
    ["Day of week", 0.07],
    ["New York session", 0.06],
    ["Spread", 0.04],
  ] as const;
  const FOLDS = Array.from({ length: 12 }, () => 0.57 + r() * 0.08);
  const CONFUSION = { tp: 1180, fp: 870, fn: 940, tn: 1460 };

  const SLOTS = [
    {
      slot: "Entry signal",
      who: "EURUSD H1 GBM (bot)",
      now: "Rules only",
      fits: true,
    },
    {
      slot: "Position sizing",
      who: "Book FX-L sizing policy",
      now: "Fixed 0.5% risk",
      fits: true,
    },
    {
      slot: "Market intelligence (regime)",
      who: "MIS, node",
      now: "Rule-based (v1)",
      fits: false,
    },
    {
      slot: "Risk throttle",
      who: "Book exposure limits",
      now: "Static limits",
      fits: false,
    },
  ];
  const IDEAS = [
    {
      model: "Hamiltonian Monte Carlo (Bayesian)",
      from: "MQL5 · Statistics and analysis",
      n: 3,
    },
    { model: "Hidden Markov regimes", from: "MQL5 · Machine learning", n: 5 },
    {
      model: "Survival models for exits",
      from: "MQL5 · Statistics and analysis",
      n: 2,
    },
    {
      model: "Reinforcement learning agents",
      from: "MQL5 · Trading systems",
      n: 4,
    },
  ];
</script>

<svelte:head><title>ML Studio · QMX</title></svelte:head>

<div class="flex h-full flex-col">
  <div class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs">
    <FlaskConical class="text-warning size-3.5" /> Demo ML Studio. Sample training
    run; nothing was trained.
  </div>
  <header class="flex h-11 shrink-0 items-center gap-3 border-b px-3">
    <span class="text-sm font-semibold">ML Studio</span>
    <span class="bg-muted rounded-md px-2 py-0.5 text-sm"
      >EURUSD breakout scorer · v7</span
    >
    <Badge variant="outline" class="text-info">Research</Badge>
    <span
      class="text-muted-foreground ml-auto flex items-center gap-1.5 text-sm"
      ><Cpu class="size-4" /> Last run 12:08 · 3m 41s</span
    >
  </header>

  <div class="flex min-h-0 flex-1">
    <nav
      aria-label="Pipeline"
      class="bg-panel w-64 shrink-0 overflow-auto border-r p-3"
    >
      <ol class="flex flex-col">
        {#each STEPS as s, i (s.id)}
          <li class="flex gap-3">
            <span class="flex flex-col items-center">
              <span
                class={cn(
                  "flex size-6 items-center justify-center rounded-full border text-xs",
                  s.ok
                    ? "bg-success/15 border-success/40 text-success"
                    : "text-muted-foreground",
                )}
              >
                {#if s.ok}<Check class="size-3.5" />{:else}{i + 1}{/if}
              </span>
              {#if i < STEPS.length - 1}<span class="bg-border my-1 w-px flex-1"
                ></span>{/if}
            </span>
            <button
              type="button"
              class={cn(
                "mb-2 flex-1 rounded-md px-2 py-1 text-left",
                step === s.id ? "bg-muted" : "hover:bg-muted/60",
              )}
              aria-current={step === s.id ? "step" : undefined}
              onclick={() => (step = s.id)}
            >
              <span class="block text-sm font-medium">{s.label}</span>
              <span class="text-muted-foreground block text-xs">{s.detail}</span
              >
            </button>
          </li>
        {/each}
      </ol>
    </nav>

    <div class="min-h-0 flex-1 overflow-auto p-3">
      {#if step === "slots"}
        <div class="grid gap-3 md:grid-cols-2">
          {#each SLOTS as s (s.slot)}
            <section class="surface flex flex-col gap-2 rounded-xl p-4">
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
                {#if s.fits}<Check class="size-3.5" /> This model's output fits this
                  slot{:else}<CircleAlert class="size-3.5" /> Needs a different output
                  (regime label or risk score){/if}
              </p>
              <div>
                <Button
                  size="sm"
                  variant="outline"
                  aria-disabled="true"
                  class="aria-disabled:opacity-60"
                  title="Plugging a model in creates a new bot or book version; needs the daemon"
                  onclick={(e) => e.preventDefault()}>Plug in…</Button
                >
              </div>
            </section>
          {/each}
        </div>
        <p class="text-muted-foreground mt-3 text-sm">
          Plugging in never changes a running bot. It makes a new version that
          has to earn its own evidence.
        </p>
      {:else}
        <div class="grid grid-cols-12 gap-3">
          <WidgetFrame
            title="Training · log loss"
            class="col-span-12 min-h-80 xl:col-span-7"
          >
            <LineChart
              series={[
                { label: "Train", values: train, color: "var(--chart-1)" },
                { label: "Validation", values: valid, color: "var(--chart-2)" },
              ]}
              height={200}
            />
            <p class="text-muted-foreground mt-1 text-xs">
              Validation loss turns up after about epoch 38: early stopping kept
              epoch 37.
            </p>
          </WidgetFrame>
          <WidgetFrame
            title="What the model looks at"
            class="col-span-12 xl:col-span-5"
          >
            <ul class="flex flex-col gap-2">
              {#each IMPORTANCE as [name, v] (name)}
                <li
                  class="grid grid-cols-[10rem_1fr_3rem] items-center gap-2 text-sm"
                >
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
          </WidgetFrame>
          <WidgetFrame
            title="AUC per fold"
            class="col-span-12 md:col-span-6 xl:col-span-4"
          >
            <div class="flex h-36 items-end gap-1.5">
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
          </WidgetFrame>
          <WidgetFrame
            title="Hits and misses (out of sample)"
            class="col-span-12 md:col-span-6 xl:col-span-4"
          >
            <div class="grid grid-cols-2 gap-1.5 text-center">
              <div class="bg-success/20 rounded-md p-3">
                <p class="num text-xl font-semibold">{CONFUSION.tp}</p>
                <p class="text-muted-foreground text-xs">Called win, was win</p>
              </div>
              <div class="bg-destructive/15 rounded-md p-3">
                <p class="num text-xl font-semibold">{CONFUSION.fp}</p>
                <p class="text-muted-foreground text-xs">
                  Called win, was loss
                </p>
              </div>
              <div class="bg-destructive/10 rounded-md p-3">
                <p class="num text-xl font-semibold">{CONFUSION.fn}</p>
                <p class="text-muted-foreground text-xs">
                  Called loss, was win
                </p>
              </div>
              <div class="bg-success/10 rounded-md p-3">
                <p class="num text-xl font-semibold">{CONFUSION.tn}</p>
                <p class="text-muted-foreground text-xs">
                  Called loss, was loss
                </p>
              </div>
            </div>
          </WidgetFrame>
          <WidgetFrame
            title="Model ideas from your Library"
            class="col-span-12 xl:col-span-4"
          >
            <ul class="flex flex-col">
              {#each IDEAS as idea (idea.model)}
                <li class="flex items-center gap-2 border-b py-2 last:border-0">
                  <BookOpen class="text-muted-foreground size-4 shrink-0" />
                  <span class="min-w-0 flex-1"
                    ><span class="block text-sm font-medium">{idea.model}</span
                    ><span class="text-muted-foreground block text-xs"
                      >{idea.n} articles · {idea.from}</span
                    ></span
                  >
                </li>
              {/each}
            </ul>
            <Button
              size="sm"
              variant="ghost"
              class="mt-2"
              href={resolve("/library")}>Browse Library</Button
            >
          </WidgetFrame>
        </div>
      {/if}
    </div>
  </div>
</div>
