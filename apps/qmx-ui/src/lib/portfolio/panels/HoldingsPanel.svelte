<script lang="ts">
  /** What you hold, three ways (operator, 2026-10-03): positions, exposure by market and how the pods move together. A toggle, not tabs: one subject. */
  import Segmented from "$lib/workbench/Segmented.svelte";
  import PositionsPanel from "./PositionsPanel.svelte";
  import ExposurePanel from "./ExposurePanel.svelte";
  import CorrelationPanel from "./CorrelationPanel.svelte";

  let view = $state<"positions" | "exposure" | "correlation">("positions");
</script>

{#snippet toggle()}
  <Segmented
    label="Holdings view"
    options={[
      { value: "positions", label: "Positions" },
      { value: "exposure", label: "Exposure" },
      { value: "correlation", label: "Correlation" },
    ]}
    bind:value={view}
  />
{/snippet}

{#if view === "positions"}<PositionsPanel
    lead={toggle}
  />{:else if view === "exposure"}<ExposurePanel
    lead={toggle}
  />{:else}<CorrelationPanel lead={toggle} />{/if}
