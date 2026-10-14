<script lang="ts">
  /**
   * The sweep as a grid: symbols across, timeframes down, one cell per run
   * (QMB B-12 permutation sweep; each cell is its own isolated run). Click a
   * cell to select that run; linked tiles follow. Add markets or timeframes
   * to grow the scenario.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import X from "@lucide/svelte/icons/x";
  import Loader from "@lucide/svelte/icons/loader-circle";
  import Clock from "@lucide/svelte/icons/clock";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { cn } from "$lib/utils";
  import type { LinkGroup } from "$lib/workbench/tiles/tiles";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { RUNS, SYMBOLS, TIMEFRAMES, type Run } from "../demo";
  import { lab } from "../lab.svelte";
  import ScenarioDialog from "../ScenarioDialog.svelte";
  import Sparkle from "@lucide/svelte/icons/sparkle";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import Segmented from "$lib/workbench/Segmented.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";

  let { link }: { link?: LinkGroup } = $props();
  const size = panelSize();

  const METRICS = [
    { id: "net", label: "Net %" },
    { id: "sharpe", label: "Sharpe" },
    { id: "maxDd", label: "Max DD %" },
  ] as const;
  let metric = $state<(typeof METRICS)[number]["id"]>("net");

  const sweep = RUNS.filter((r) => r.procedure === "Sweep");
  const cell = (s: string, tf: string) =>
    sweep.find((r) => r.symbol === s && r.timeframe === tf);
  const value = (r: Run) => r[metric];
  const values = $derived(
    sweep.map(value).filter((v): v is number => v !== null),
  );
  const lo = $derived(Math.min(...values));
  const hi = $derived(Math.max(...values));

  /** Diverging fill: green for good, red for bad, strength by distance. */
  function fill(r: Run): string {
    const v = value(r);
    if (v === null) return "transparent";
    const good = metric === "maxDd" ? v > (lo + hi) / 2 : v > 0;
    const span =
      metric === "net" ? Math.max(Math.abs(lo), Math.abs(hi)) : hi - lo || 1;
    const t =
      metric === "net"
        ? Math.abs(v) / span
        : Math.abs(v - (lo + hi) / 2) / (span / 2);
    const tone = good ? "var(--success)" : "var(--destructive)";
    return `color-mix(in oklab, ${tone} ${Math.round(12 + t * 48)}%, transparent)`;
  }
  const selected = $derived(lab.selectedFor(link));
  const passing = $derived(sweep.filter((r) => (r.net ?? 0) > 0).length);
  const done = $derived(sweep.filter((r) => r.status === "done").length);

  const MORE_SYMBOLS = ["USDCAD", "NZDUSD", "EURJPY", "NAS100", "BTCUSD"];
  const MORE_TF = ["M5", "M30", "D1"];
  function grow(what: string) {
    workbench.notify(
      `${what} added to the scenario draft. Running it needs the daemon.`,
    );
  }
  let building = $state(false);
</script>

{#if size.mode === "compact"}
  <PanelSummary
    label="BTC breakout v7 sweep"
    value={`${passing}/${done}`}
    status="finished runs made money"
    tone={passing > done / 2 ? "good" : "warn"}
  />
{:else}
<div class="flex h-full flex-col">
  <div class="px-panel flex h-11 shrink-0 items-center gap-2">
    <span class="truncate text-xs"
      ><span class="font-medium">BTC breakout v7</span>
      <span class="text-muted-foreground">· {sweep.length} runs</span></span
    >
    <Button
      variant="outline"
      size="sm"
      class="ml-auto h-7"
      aria-label="New scenario"
      onclick={() => (building = true)}
      ><Sparkle /><span class="hidden @2xl:inline">New scenario</span></Button
    >
    <Segmented
      label="Measure"
      options={METRICS.map((m) => ({ value: m.id, label: m.label }))}
      bind:value={metric}
    />
  </div>
  <div class="px-panel pb-panel min-h-0 flex-1 overflow-auto">
    <div
      class="grid h-full min-h-[14rem] gap-1"
      style="grid-template-columns: 2.5rem repeat({SYMBOLS.length}, minmax(0, 1fr)) 2rem; grid-template-rows: 1.5rem repeat({TIMEFRAMES.length}, minmax(2.75rem, 1fr)) 2.25rem"
    >
      <span></span>
      {#each SYMBOLS as s (s)}
        <span
          class="text-muted-foreground min-w-0 self-end truncate text-center text-xs"
          title={s}>{s}</span
        >
      {/each}
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button
              {...props}
              variant="ghost"
              size="icon-sm"
              class="self-end"
              aria-label="Add a market"><Plus /></Button
            >
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content>
          <DropdownMenu.Label>Add a market</DropdownMenu.Label>
          {#each MORE_SYMBOLS as s (s)}
            <DropdownMenu.Item onclick={() => grow(s)}>{s}</DropdownMenu.Item>
          {/each}
          <DropdownMenu.Separator />
          <DropdownMenu.Item onclick={() => grow("A paired market (spread)")}
            >Pair two markets…</DropdownMenu.Item
          >
        </DropdownMenu.Content>
      </DropdownMenu.Root>
      {#each TIMEFRAMES as tf (tf)}
        <span class="text-muted-foreground self-center text-xs">{tf}</span>
        {#each SYMBOLS as s (s)}
          {@const r = cell(s, tf)}
          {#if r}
            <button
              type="button"
              class={cn(
                "flex min-w-0 flex-col items-center justify-center rounded-md border text-xs transition-colors",
                selected === r.id
                  ? "border-ring ring-ring ring-1"
                  : "border-border/60 hover:border-ring/60",
              )}
              style="background: {lab.machine && r.env !== lab.machine
                ? 'transparent'
                : fill(r)}; opacity: {lab.machine && r.env !== lab.machine
                ? 0.35
                : 1}"
              title={lab.machine && r.env !== lab.machine
                ? `Ran on another machine`
                : undefined}
              aria-label={`${s} ${tf}: ${r.status}${value(r) !== null ? `, ${value(r)}` : ""}`}
              onclick={() => lab.select(link, r.id)}
            >
              {#if r.status === "running"}
                <Loader
                  class="text-info size-4 animate-spin motion-reduce:animate-none"
                />
                <span class="num text-muted-foreground">{r.progress}%</span>
              {:else if r.status === "queued"}
                <Clock class="text-muted-foreground size-4" />
                <span class="text-muted-foreground hidden @2xl:inline"
                  >queued</span
                >
              {:else if r.status === "failed"}
                <X class="text-destructive size-4" />
                <span class="text-destructive hidden @2xl:inline">failed</span>
              {:else}
                <span class="num text-sm font-medium"
                  >{metric === "net" && (value(r) ?? 0) > 0 ? "+" : ""}{value(
                    r,
                  )}</span
                >
                <span class="num text-muted-foreground hidden @3xl:inline"
                  >{r.trades} trades</span
                >
              {/if}
            </button>
          {/if}
        {/each}
        <span></span>
      {/each}
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button
              {...props}
              variant="ghost"
              size="icon-sm"
              aria-label="Add a timeframe"><Plus /></Button
            >
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content>
          <DropdownMenu.Label>Add a timeframe</DropdownMenu.Label>
          {#each MORE_TF as t (t)}
            <DropdownMenu.Item onclick={() => grow(t)}>{t}</DropdownMenu.Item>
          {/each}
        </DropdownMenu.Content>
      </DropdownMenu.Root>
      <span
        class="text-muted-foreground flex items-center gap-1 self-center text-xs"
        style="grid-column: 2 / -1"
        >{passing} of {done} finished runs made money
        <InfoTip
          label="Explain the sweep grid"
          text="Markets across, timeframes down, one isolated run per cell. A grid is a search, not proof: confirm winners with walk-forward before trusting them. Click a cell to select that run; linked tiles follow."
        /></span
      >
    </div>
  </div>
</div>

{/if}

<ScenarioDialog bind:open={building} />
