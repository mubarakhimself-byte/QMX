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

  let { link }: { link?: LinkGroup } = $props();

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
</script>

<div class="flex h-full flex-col">
  <div class="flex h-9 shrink-0 items-center gap-2 border-b px-2">
    <span class="text-xs"
      ><span class="font-medium">EURUSD H1 GBM v7</span>
      <span class="text-muted-foreground"
        >· {SYMBOLS.length} markets × {TIMEFRAMES.length} timeframes = {sweep.length}
        runs</span
      ></span
    >
    <div
      class="ml-auto flex items-center gap-0.5"
      role="radiogroup"
      aria-label="Measure"
    >
      {#each METRICS as m (m.id)}
        <button
          type="button"
          role="radio"
          aria-checked={metric === m.id}
          class={cn(
            "h-6 rounded-md px-2 text-xs",
            metric === m.id
              ? "bg-muted text-foreground"
              : "text-muted-foreground hover:text-foreground",
          )}
          onclick={() => (metric = m.id)}>{m.label}</button
        >
      {/each}
    </div>
  </div>
  <div class="min-h-0 flex-1 overflow-auto p-3">
    <div
      class="grid h-full min-h-[14rem] gap-1.5"
      style="grid-template-columns: 3.5rem repeat({SYMBOLS.length}, minmax(4.5rem, 1fr)) 2.5rem; grid-template-rows: 1.5rem repeat({TIMEFRAMES.length}, minmax(3rem, 1fr)) 2.25rem"
    >
      <span></span>
      {#each SYMBOLS as s (s)}
        <span class="text-muted-foreground self-end text-center text-xs"
          >{s}</span
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
                "flex flex-col items-center justify-center rounded-md border text-xs transition-colors",
                selected === r.id
                  ? "border-ring ring-ring ring-1"
                  : "border-border/60 hover:border-ring/60",
              )}
              style="background: {fill(r)}"
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
                <span class="text-muted-foreground">queued</span>
              {:else if r.status === "failed"}
                <X class="text-destructive size-4" />
                <span class="text-destructive">failed</span>
              {:else}
                <span class="num text-sm font-medium"
                  >{metric === "net" && (value(r) ?? 0) > 0 ? "+" : ""}{value(
                    r,
                  )}</span
                >
                <span class="num text-muted-foreground">{r.trades} trades</span>
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
        class="text-muted-foreground self-center text-xs"
        style="grid-column: 2 / -1"
        >{passing} of {done} finished runs made money. A grid is a search, not proof:
        confirm winners with walk-forward before trusting them.</span
      >
    </div>
  </div>
</div>
