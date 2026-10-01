<script lang="ts">
  import type { Component, Snippet } from "svelte";
  import { cn } from "$lib/utils";

  let {
    icon: Icon,
    title,
    description,
    action,
    class: className,
  }: {
    icon?: Component;
    title: string;
    description?: string;
    action?: Snippet;
    class?: string;
  } = $props();
</script>

<div
  class={cn(
    "flex flex-col items-center justify-center gap-1.5 p-4 text-center",
    className,
  )}
>
  {#if Icon}
    <div class="text-muted-foreground/70 mb-0.5">
      <Icon class="size-5" strokeWidth={1.5} />
    </div>
  {/if}
  <p class="text-muted-foreground text-xs font-medium">{title}</p>
  {#if description}
    <p class="text-muted-foreground/80 max-w-xs text-xs text-balance">
      {description}
    </p>
  {/if}
  {#if action}
    <div class="mt-2">{@render action()}</div>
  {/if}
</div>
