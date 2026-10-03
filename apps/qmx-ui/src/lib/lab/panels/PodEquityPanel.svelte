<script lang="ts">
  /** Equity of the ticked pods on the same bots and period. */
  import LineChart from "$lib/qmx/LineChart.svelte";
  import { LAB_PODS, POD_EQUITY } from "../pods";
  import { lab } from "../lab.svelte";

  const series = $derived(
    LAB_PODS.filter((p) => lab.podsTicked.includes(p.id)).map((p) => ({
      label: p.name,
      values: POD_EQUITY[p.id],
      color: p.color,
    })),
  );
</script>

<div class="h-full p-3"><LineChart {series} height={200} /></div>
