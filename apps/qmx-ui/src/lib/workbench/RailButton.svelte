<script lang="ts">
  import type { Component } from "svelte";
  import * as Tooltip from "$lib/components/ui/tooltip";
  import { cn } from "$lib/utils";
  import { resolve } from "$app/paths";

  let {
    href,
    label,
    icon: Icon,
    active = false,
    badge,
  }: {
    href: string;
    label: string;
    icon: Component;
    active?: boolean;
    badge?: "running" | "unknown" | "failed";
  } = $props();
</script>

<Tooltip.Root>
  <Tooltip.Trigger>
    {#snippet child({ props })}
      <a
        {...props}
        href={resolve(href as "/")}
        aria-label={label}
        aria-current={active ? "page" : undefined}
        class={cn(
          "text-muted-foreground hover:text-foreground hover:bg-muted relative flex size-10 items-center justify-center rounded-xl transition-colors",
          active && "bg-muted text-foreground",
        )}
      >
        {#if active}
          <span
            class="bg-primary absolute top-2 bottom-2 -left-1.5 w-0.5 rounded-full"
            aria-hidden="true"
          ></span>
        {/if}
        <Icon class="size-5" />
        {#if badge}
          <span
            class={cn(
              "ring-background absolute top-1.5 right-1.5 size-2 rounded-full ring-2",
              badge === "running" && "bg-success",
              badge === "unknown" && "bg-warning",
              badge === "failed" && "bg-destructive",
            )}
          >
            <span class="sr-only">{badge}</span>
          </span>
        {/if}
      </a>
    {/snippet}
  </Tooltip.Trigger>
  <Tooltip.Content side="right">{label}</Tooltip.Content>
</Tooltip.Root>
