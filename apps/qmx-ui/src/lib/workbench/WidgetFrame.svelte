<script lang="ts" module>
  /** Readable states (UI DESIGN.md "Readable states"; EXPERIENCE §8). */
  export type WidgetState =
    | "ready"
    | "loading"
    | "empty"
    | "unavailable"
    | "failed"
    | "reconnecting"
    | "stale"
    | "unknown";
</script>

<script lang="ts">
  import type { Snippet } from "svelte";
  import History from "@lucide/svelte/icons/history";
  import MessageSquarePlus from "@lucide/svelte/icons/message-square-plus";
  import EllipsisVertical from "@lucide/svelte/icons/ellipsis-vertical";
  import Maximize2 from "@lucide/svelte/icons/maximize-2";
  import X from "@lucide/svelte/icons/x";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import { Skeleton } from "$lib/components/ui/skeleton";
  import * as Tooltip from "$lib/components/ui/tooltip";
  import { cn } from "$lib/utils";

  let {
    title,
    state = "ready",
    reason,
    controls,
    children,
    onrefresh,
    onmessage,
    onexpand,
    onclose,
    class: className,
  }: {
    title: string;
    state?: WidgetState;
    /** Typed refusal / unavailability text shown in non-ready states. */
    reason?: string;
    /** Optional pickers next to the title (instrument, timeframe…). */
    controls?: Snippet;
    children?: Snippet;
    onrefresh?: () => void;
    /** Adds a reference to this widget into the relevant copilot session. */
    onmessage?: () => void;
    onexpand?: () => void;
    onclose?: () => void;
    class?: string;
  } = $props();

  const STATE_TEXT: Record<
    Exclude<WidgetState, "ready" | "loading">,
    string
  > = {
    empty: "No data yet",
    unavailable: "Unavailable",
    failed: "Failed",
    reconnecting: "Reconnecting",
    stale: "Stale",
    unknown: "Outcome unknown",
  };
</script>

{#snippet tool(label: string, Icon: typeof X, handler?: () => void)}
  <Tooltip.Root>
    <Tooltip.Trigger>
      {#snippet child({ props })}
        <Button
          {...props}
          variant="ghost"
          size="icon-xs"
          aria-label={label}
          disabled={!handler}
          onclick={handler}
        >
          <Icon />
        </Button>
      {/snippet}
    </Tooltip.Trigger>
    <Tooltip.Content
      >{handler ? label : `${label} — not available`}</Tooltip.Content
    >
  </Tooltip.Root>
{/snippet}

<section
  aria-label={title}
  data-state={state}
  class={cn(
    "bg-card text-card-foreground ring-foreground/10 flex min-h-0 flex-col overflow-hidden rounded-2xl ring-1",
    className,
  )}
>
  <header class="flex h-10 shrink-0 items-center gap-2 pr-1.5 pl-3">
    <h3 class="truncate text-[13px] font-medium">{title}</h3>
    {#if controls}{@render controls()}{/if}
    {#if state === "stale" || state === "reconnecting" || state === "unknown"}
      <Badge variant="outline" class="text-warning">{STATE_TEXT[state]}</Badge>
    {/if}
    <div class="ml-auto flex items-center">
      {@render tool("Refresh", History, onrefresh)}
      {@render tool("Add to copilot", MessageSquarePlus, onmessage)}
      {@render tool("More", EllipsisVertical, undefined)}
      {@render tool("Expand", Maximize2, onexpand)}
      {@render tool("Close", X, onclose)}
    </div>
  </header>

  <div class="relative min-h-0 flex-1 overflow-auto px-3 pb-3">
    {#if state === "loading"}
      <div class="flex flex-col gap-2 pt-1" aria-busy="true">
        <Skeleton class="h-4 w-1/3" />
        <Skeleton class="h-24 w-full" />
        <Skeleton class="h-4 w-2/3" />
      </div>
    {:else if state === "empty" || state === "unavailable" || state === "failed"}
      <div
        class="flex h-full min-h-24 flex-col items-center justify-center gap-1 text-center"
      >
        <p
          class={cn(
            "text-sm font-medium",
            state === "failed" && "text-destructive",
          )}
        >
          {STATE_TEXT[state]}
        </p>
        {#if reason}
          <p class="text-muted-foreground max-w-xs text-xs">{reason}</p>
        {/if}
      </div>
    {:else}
      <div class={cn(state === "stale" && "opacity-70")}>
        {@render children?.()}
      </div>
      {#if reason}
        <p class="text-muted-foreground mt-2 text-xs">{reason}</p>
      {/if}
    {/if}
  </div>
</section>
