<script lang="ts">
  /** Positions on top of Live, with exposure and correlation as tabs beside it (operator, 2026-10-03). */
  import { cn } from "$lib/utils";
  import PositionsPanel from "./PositionsPanel.svelte";
  import ExposurePanel from "./ExposurePanel.svelte";
  import CorrelationPanel from "./CorrelationPanel.svelte";

  const TABS = [
    { id: "positions", label: "Positions" },
    { id: "exposure", label: "Exposure" },
    { id: "correlation", label: "Correlation" },
  ] as const;
  let tab = $state<(typeof TABS)[number]["id"]>("positions");
</script>

<div class="flex h-full flex-col">
  <div
    class="flex h-9 shrink-0 items-center gap-1 border-b px-2"
    role="tablist"
    aria-label="Holdings"
  >
    {#each TABS as t (t.id)}
      <button
        type="button"
        role="tab"
        aria-selected={tab === t.id}
        class={cn(
          "h-7 rounded-md px-3 text-sm",
          tab === t.id
            ? "bg-muted text-foreground font-medium"
            : "text-muted-foreground hover:text-foreground",
        )}
        onclick={() => (tab = t.id)}>{t.label}</button
      >
    {/each}
  </div>
  <div class="min-h-0 flex-1">
    {#if tab === "positions"}<PositionsPanel
      />{:else if tab === "exposure"}<ExposurePanel />{:else}<CorrelationPanel
      />{/if}
  </div>
</div>
