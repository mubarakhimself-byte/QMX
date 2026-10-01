<script lang="ts">
  import type { Snippet } from "svelte";

  let {
    title,
    subtitle,
    actions,
  }: { title: string; subtitle?: string; actions?: Snippet } = $props();
</script>

<svelte:head><title>{title} · QMX</title></svelte:head>

<header class="flex h-12 shrink-0 items-center gap-3 border-b px-4">
  <h1 class="text-sm font-semibold">{title}</h1>
  {#if subtitle}
    <span class="text-muted-foreground truncate text-sm">{subtitle}</span>
  {/if}
  {#if actions}
    <div class="ml-auto flex items-center gap-2">{@render actions()}</div>
  {/if}
</header>
