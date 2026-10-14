<script lang="ts">
  /**
   * A panel's compact mode (DESIGN-RULES.md, size modes): one headline
   * number, an optional sparkline and one status line. Anything else a
   * compact tile shows goes in `children`, below the headline.
   */
  import type { Snippet } from "svelte";
  import Sparkline from "$lib/demo/Sparkline.svelte";
  import { cn } from "$lib/utils";

  let {
    label,
    value,
    status,
    tone = "muted",
    values,
    top,
    children,
  }: {
    label: string;
    value: string;
    status?: string;
    tone?: "muted" | "good" | "warn" | "bad";
    values?: number[];
    /** A toggle or chip pinned to the top of the tile. */
    top?: Snippet;
    children?: Snippet;
  } = $props();

  const TONE = {
    muted: "text-muted-foreground",
    good: "text-success",
    warn: "text-warning",
    bad: "text-destructive",
  };
</script>

<div class="gap-row p-panel flex h-full min-w-0 flex-col">
  {#if top}{@render top()}{/if}
  <div class={cn("min-w-0", !children && "mt-auto")}>
    <p class="text-muted-foreground truncate text-xs">{label}</p>
    <p class="num truncate text-2xl font-semibold">{value}</p>
    {#if status}<p class={cn("truncate text-xs", TONE[tone])}>
        {status}
      </p>{/if}
  </div>
  {#if values && values.length > 1}
    <Sparkline {values} class="h-8 w-full shrink-0" />
  {/if}
  {#if children}<div class="mt-row min-h-0 flex-1 overflow-auto">
      {@render children()}
    </div>{/if}
</div>
