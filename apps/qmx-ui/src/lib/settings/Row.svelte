<script lang="ts">
  /** A label on the left and its control on the right. */
  import type { Snippet } from "svelte";
  import InfoTip from "$lib/workbench/InfoTip.svelte";

  let {
    label,
    tip,
    children,
  }: { label: string; tip?: string; children: Snippet } = $props();
</script>

<div
  class="flex min-h-11 flex-wrap items-center gap-x-4 gap-y-row border-t py-row first:border-t-0"
>
  <span class="flex min-w-48 flex-1 items-center gap-1">
    {label}{#if tip}<InfoTip label={`About ${label}`} text={tip} />{/if}
  </span>
  <div class="flex flex-wrap items-center gap-2">{@render children()}</div>
</div>
