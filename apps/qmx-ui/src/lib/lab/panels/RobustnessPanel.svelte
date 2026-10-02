<script lang="ts">
  /**
   * Robustness checks for the selected run, cheapest first with early exit
   * (QMB B-14 validation ladder). Results are "robustness-only" claims, never
   * proof of edge. Pass thresholds are not ruled yet (GAP-0048), so the bar
   * shown is the operator's own and editable.
   */
  import Check from "@lucide/svelte/icons/check";
  import X from "@lucide/svelte/icons/x";
  import Minus from "@lucide/svelte/icons/minus";
  import Loader from "@lucide/svelte/icons/loader-circle";
  import Plus from "@lucide/svelte/icons/plus";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { cn } from "$lib/utils";
  import type { LinkGroup } from "$lib/workbench/tiles/tiles";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import EnvChip from "../EnvChip.svelte";
  import { RUNS } from "../demo";
  import { lab } from "../lab.svelte";

  let { link }: { link?: LinkGroup } = $props();
  const run = $derived(RUNS.find((r) => r.id === lab.selectedFor(link)));

  type CheckRow = {
    name: string;
    cost: string;
    bar: string;
    result: string;
    state: "pass" | "fail" | "running" | "skipped";
    env: string;
  };
  const checks = $derived.by((): CheckRow[] => {
    const good = (run?.net ?? 0) > 5;
    return [
      {
        name: "Costs ×2",
        cost: "seconds",
        bar: "keeps ≥ 50% of net",
        result: good ? "71% kept" : "18% kept",
        state: good ? "pass" : "fail",
        env: "local",
      },
      {
        name: "Trade shuffle (1,000)",
        cost: "1 min",
        bar: "95th pct DD ≥ −15%",
        result: good ? "−11.2%" : "—",
        state: good ? "pass" : "skipped",
        env: "local",
      },
      {
        name: "Candle noise",
        cost: "4 min",
        bar: "net stays positive in 90%",
        result: good ? "61% done" : "—",
        state: good ? "running" : "skipped",
        env: "vps-fsn",
      },
      {
        name: "Significance vs zero edge",
        cost: "6 min",
        bar: "p < 0.05",
        result: "—",
        state: "skipped",
        env: "local",
      },
      {
        name: "Walk-forward 12 folds",
        cost: "20 min",
        bar: "7 of 9 clusters pass",
        result: "—",
        state: "skipped",
        env: "vps-fsn",
      },
    ];
  });
  const ICON = { pass: Check, fail: X, running: Loader, skipped: Minus };
  const TONE = {
    pass: "text-success",
    fail: "text-destructive",
    running: "text-info animate-spin motion-reduce:animate-none",
    skipped: "text-muted-foreground",
  };
  const firstFail = $derived(checks.findIndex((c) => c.state === "fail"));
  const MORE = [
    "Spread widening",
    "Missing bars",
    "Slippage model",
    "Parameter wobble ±10%",
    "Out-of-sample year",
  ];
</script>

<div class="flex h-full flex-col">
  <div class="flex h-9 shrink-0 items-center gap-2 border-b px-3 text-xs">
    <span class="font-medium"
      >{run
        ? `${run.symbol} ${run.timeframe} · ${run.id}`
        : "No run selected"}</span
    >
    <span class="text-muted-foreground"
      >cheapest first; stops at the first fail</span
    >
    <DropdownMenu.Root>
      <DropdownMenu.Trigger>
        {#snippet child({ props })}
          <Button {...props} variant="ghost" size="sm" class="ml-auto h-7"
            ><Plus />Add check</Button
          >
        {/snippet}
      </DropdownMenu.Trigger>
      <DropdownMenu.Content align="end">
        {#each MORE as m (m)}
          <DropdownMenu.Item
            onclick={() => workbench.notify(`${m} added to this run's checks.`)}
            >{m}</DropdownMenu.Item
          >
        {/each}
        <DropdownMenu.Separator />
        <DropdownMenu.Item
          onclick={() =>
            workbench.notify(
              "Describe the check to the Lab copilot to build it.",
            )}>Build your own…</DropdownMenu.Item
        >
      </DropdownMenu.Content>
    </DropdownMenu.Root>
  </div>
  <ol class="min-h-0 flex-1 overflow-auto">
    {#each checks as c, i (c.name)}
      {@const Icon = ICON[c.state]}
      <li
        class={cn(
          "grid grid-cols-[1.25rem_1fr_auto] items-center gap-x-3 gap-y-0.5 border-b border-border/50 px-3 py-2",
          firstFail >= 0 && i > firstFail && "opacity-60",
        )}
      >
        <Icon class={cn("size-4", TONE[c.state])} />
        <span class="text-sm">{c.name}</span>
        <span class="num text-sm {c.state === 'fail' ? 'text-destructive' : ''}"
          >{c.result}</span
        >
        <span></span>
        <span class="text-muted-foreground text-xs"
          >Bar: {c.bar} · {c.cost}</span
        >
        <EnvChip
          env={c.env}
          status={c.state === "running" ? "running" : "done"}
          compact
        />
      </li>
    {/each}
  </ol>
  <p class="text-muted-foreground border-t px-3 py-2 text-xs">
    Passing these shows the result is not fragile. It does not prove an edge.
    Bars are yours to set; the docs leave thresholds open.
  </p>
</div>
