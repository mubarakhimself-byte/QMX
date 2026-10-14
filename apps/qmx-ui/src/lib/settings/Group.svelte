<script lang="ts">
  /** One group of settings on a page: a title, an optional tip and actions, then rows. */
  import type { Snippet } from "svelte";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import { cn } from "$lib/utils";

  let {
    title,
    tip,
    meta,
    actions,
    children,
    class: className,
  }: {
    title: string;
    tip?: string;
    /** One short line beside the title, e.g. a count. */
    meta?: string;
    actions?: Snippet;
    children: Snippet;
    class?: string;
  } = $props();
</script>

<section
  class={cn("solid-backing flex flex-col rounded-2xl border", className)}
  aria-label={title}
>
  <header class="flex flex-wrap items-center gap-2 px-panel pt-panel pb-row">
    <h3 class="text-lg font-semibold">{title}</h3>
    {#if tip}<InfoTip label={`About ${title}`} text={tip} />{/if}
    {#if meta}<span class="text-muted-foreground text-sm">{meta}</span>{/if}
    {#if actions}<div class="ml-auto flex items-center gap-2">
        {@render actions()}
      </div>{/if}
  </header>
  <div class="flex flex-col px-panel pb-panel">
    {@render children()}
  </div>
</section>
