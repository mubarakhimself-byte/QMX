<script lang="ts">
  /**
   * Decisions arriving from the paper run as they happen: every trade with
   * the steps that sized it, and every trade the pod refused. In the demo
   * new rows are replayed from a sample every few seconds, and stop while
   * the run is paused or stopped.
   */
  import { onMount } from "svelte";
  import { cn } from "$lib/utils";
  import { usd } from "$lib/portfolio/bits";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import Segmented from "$lib/workbench/Segmented.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { PAPER_FEED, type PaperDecision } from "../pods";
  import { podModel } from "../pod-model.svelte";
  import { lab } from "../lab.svelte";

  const size = panelSize();
  const run = $derived(podModel.paper(lab.labPod));
  const live = $derived(!run.paused && !run.stopped);
  let show = $state<"all" | "refused">("all");
  let rows = $state<(PaperDecision & { key: number; fresh?: boolean })[]>(
    PAPER_FEED.map((d, i) => ({ ...d, key: i })),
  );
  const shown = $derived(show === "all" ? rows : rows.filter((r) => r.refused));
  onMount(() => {
    let k = 100;
    const timer = setInterval(() => {
      if (!live) return;
      const sample = PAPER_FEED[k % PAPER_FEED.length];
      const now = new Date();
      const at = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
      rows = [
        { ...sample, at, key: k++, fresh: true },
        ...rows.map((r) => ({ ...r, fresh: false })),
      ].slice(0, 30);
    }, 7000);
    return () => clearInterval(timer);
  });
  const money = (v: number) => usd(v, v % 1 ? 2 : 0);
  const refused = $derived(rows.filter((r) => r.refused).length);
</script>

{#if size.mode === "compact"}
  <PanelSummary
    label="Paper decisions"
    value={String(rows.length)}
    status={live ? `${refused} refused` : "Paused"}
    tone={live ? "muted" : "warn"}
  />
{:else}
  <div class="flex h-full flex-col">
    <div class="px-panel flex h-11 shrink-0 items-center gap-2">
      <span
        class={cn(
          "size-1.5 shrink-0 rounded-full",
          live ? "bg-success animate-pulse" : "bg-warning",
        )}
        title={live ? "Arriving live" : "Paused"}
      ></span>
      <Segmented
        label="Show"
        options={[
          { value: "all", label: "All" },
          { value: "refused", label: `Refused ${refused}` },
        ]}
        bind:value={show}
      />
      <span class="text-muted-foreground ml-auto text-xs"
        >{live ? "Newest first" : "Paused"}</span
      >
    </div>
    <ul class="min-h-0 flex-1 overflow-auto">
      {#each shown as r (r.key)}
        {@const last = r.steps[r.steps.length - 1]}
        <li
          class={cn(
            "border-border/50 px-panel py-row border-b transition-colors duration-700",
            r.fresh && "bg-primary/10",
          )}
        >
          <div class="flex items-baseline gap-2 text-sm">
            <span class="text-muted-foreground num w-11 shrink-0 text-xs"
              >{r.at}</span
            >
            <span
              class={cn(
                "font-medium",
                r.side === "Buy" ? "text-success" : "text-destructive",
              )}>{r.side}</span
            >
            <span class="num">{r.symbol}</span>
            <span class="text-muted-foreground truncate text-xs">{r.bot}</span>
            {#if r.refused}
              <span
                class="text-destructive ml-auto shrink-0 text-xs font-medium"
                >Refused</span
              >
            {:else}
              <span class="num ml-auto shrink-0 font-semibold"
                >{money(last.usd)}</span
              >
            {/if}
          </div>
          {#if size.mode === "expanded" || r.refused}
            <div
              class="text-muted-foreground mt-1 flex flex-wrap items-center gap-1 pl-13 text-xs"
            >
              {#each r.steps as s, i (i)}
                {#if i}<span aria-hidden="true">›</span>{/if}
                <span class="rounded border px-1.5"
                  >{s.by}
                  <span class="num text-foreground">{money(s.usd)}</span></span
                >
              {/each}
              {#if r.refused}<span aria-hidden="true">›</span><span
                  class="border-destructive/50 text-destructive rounded border px-1.5"
                  >{r.refused}</span
                >{/if}
            </div>
          {/if}
        </li>
      {:else}
        <li class="text-muted-foreground p-panel text-sm">Nothing refused</li>
      {/each}
    </ul>
  </div>
{/if}
