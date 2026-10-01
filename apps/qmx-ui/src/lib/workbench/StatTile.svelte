<script lang="ts">
  /** A small KPI tile (QuantX / OpenBB reference). Shows "—" until a value exists. */
  let {
    label,
    value,
    hint,
  }: { label: string; value?: string | number; hint?: string } = $props();
</script>

<div class="bg-panel flex min-w-0 flex-col gap-0.5 rounded-md border px-3 py-2">
  <span class="panel-label truncate">{label}</span>
  <span class="tabular text-lg leading-tight font-semibold">
    {value ?? "—"}
  </span>
  {#if hint}
    <span class="text-muted-foreground truncate text-[11px]">{hint}</span>
  {/if}
</div>
