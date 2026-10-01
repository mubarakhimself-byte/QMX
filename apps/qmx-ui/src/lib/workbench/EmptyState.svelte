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
    "flex flex-col items-center justify-center gap-2 p-6 text-center",
    className,
  )}
>
  {#if Icon}
    <div
      class="bg-muted text-muted-foreground mb-1 flex size-10 items-center justify-center rounded-xl"
    >
      <Icon class="size-5" />
    </div>
  {/if}
  <p class="text-sm font-medium">{title}</p>
  {#if description}
    <p class="text-muted-foreground max-w-sm text-sm text-balance">
      {description}
    </p>
  {/if}
  {#if action}
    <div class="mt-2">{@render action()}</div>
  {/if}
</div>
