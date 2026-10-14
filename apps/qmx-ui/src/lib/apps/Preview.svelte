<script lang="ts">
  /** A glimpse of an app's own output, sized for its tile. */
  import BellRing from "@lucide/svelte/icons/bell-ring";
  import Sparkline from "$lib/demo/Sparkline.svelte";
  import { cn } from "$lib/utils";
  import type { Preview } from "./apps.svelte";

  let { preview }: { preview: Preview } = $props();
</script>

{#if preview.kind === "figure"}
  <div class="flex items-end gap-4">
    <div class="min-w-0">
      <p class="num text-4xl font-semibold tracking-tight">{preview.value}</p>
      <p class="text-muted-foreground mt-1 truncate">{preview.label}</p>
    </div>
    {#if preview.spark}
      <Sparkline values={preview.spark} class="mb-2 h-10 min-w-0 flex-1" />
    {/if}
  </div>
{:else if preview.kind === "headline"}
  <p class="line-clamp-2 text-xl leading-snug font-medium">{preview.text}</p>
  <p class="text-muted-foreground mt-1.5 truncate">{preview.meta}</p>
{:else if preview.kind === "rows"}
  <ul class="flex flex-col gap-row">
    {#each preview.rows as r (r.label)}
      <li class="flex items-baseline gap-3 text-lg">
        <span class="min-w-0 flex-1 truncate">{r.label}</span>
        <span
          class={cn(
            "num font-medium",
            r.tone === "up" && "text-success",
            r.tone === "down" && "text-destructive",
          )}>{r.value}</span
        >
      </li>
    {/each}
  </ul>
{:else}
  <p class="flex items-start gap-2.5 text-xl leading-snug font-medium">
    <BellRing class="text-muted-foreground mt-1 size-5 shrink-0" />
    <span class="line-clamp-2">{preview.text}</span>
  </p>
  <p class="text-muted-foreground mt-1.5 pl-7.5">{preview.when}</p>
{/if}
