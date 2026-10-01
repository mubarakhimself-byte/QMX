<script lang="ts">
  let { values, class: className = "" }: { values: number[]; class?: string } =
    $props();

  const d = $derived.by(() => {
    const max = Math.max(...values);
    const min = Math.min(...values);
    const span = max - min || 1;
    return values
      .map(
        (v, i) =>
          `${i === 0 ? "M" : "L"}${((i / (values.length - 1)) * 100).toFixed(1)},${(22 - ((v - min) / span) * 20).toFixed(1)}`,
      )
      .join(" ");
  });
  const rising = $derived(values[values.length - 1] >= values[0]);
</script>

<svg
  viewBox="0 0 100 24"
  preserveAspectRatio="none"
  class="{rising ? 'text-success' : 'text-destructive'} {className}"
  aria-hidden="true"
>
  <path
    {d}
    fill="none"
    stroke="currentColor"
    stroke-width="1.25"
    vector-effect="non-scaling-stroke"
  />
</svg>
