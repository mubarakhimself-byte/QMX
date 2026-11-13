<script lang="ts">
  // A sparkline small enough to sit in a row.
  let { series, color = "currentColor", class: cls = "h-6 w-24" }: { series: number[]; color?: string; class?: string } = $props();
  const path = $derived.by(() => {
    if (series.length < 2) return "";
    const lo = Math.min(...series);
    const hi = Math.max(...series);
    return series.map((v, i) => `${i ? "L" : "M"}${((i / (series.length - 1)) * 100).toFixed(1)},${(22 - ((v - lo) / (hi - lo || 1)) * 20).toFixed(1)}`).join(" ");
  });
</script>

<svg viewBox="0 0 100 24" preserveAspectRatio="none" class="shrink-0 {cls}" style:color aria-hidden="true">
  <path d={path} fill="none" stroke="currentColor" stroke-width="1.5" vector-effect="non-scaling-stroke" />
</svg>
