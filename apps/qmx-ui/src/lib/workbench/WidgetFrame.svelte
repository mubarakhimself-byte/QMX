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
  import Maximize2 from "@lucide/svelte/icons/maximize-2";
  import Minimize2 from "@lucide/svelte/icons/minimize-2";
  import Minus from "@lucide/svelte/icons/minus";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
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
    onminimize,
    minimized = false,
    expanded = false,
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
    /** Collapse the body to the header only (client layout). */
    onminimize?: () => void;
    minimized?: boolean;
    /** True while this widget is the expanded view; swaps the icon. */
    expanded?: boolean;
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
    <Tooltip.Content>{label}</Tooltip.Content>
  </Tooltip.Root>
{/snippet}

<section
  aria-label={title}
  data-state={state}
  class={cn(
    "bg-panel text-card-foreground flex min-h-0 flex-col overflow-hidden rounded-md border",
    className,
  )}
>
  <header class="flex h-8 shrink-0 items-center gap-2 border-b pr-1 pl-2.5">
    <h3 class="panel-label truncate">{title}</h3>
    {#if controls}{@render controls()}{/if}
    {#if state === "stale" || state === "reconnecting" || state === "unknown"}
      <Badge variant="outline" class="text-warning h-4 px-1.5 text-[10px]"
        >{STATE_TEXT[state]}</Badge
      >
    {/if}
    <div class="ml-auto flex items-center">
      <!-- Only controls with a real handler render; no dead buttons. -->
      {#if onrefresh}{@render tool("Refresh", History, onrefresh)}{/if}
      {#if onmessage}{@render tool(
          "Add to copilot",
          MessageSquarePlus,
          onmessage,
        )}{/if}
      {#if onminimize}{@render tool(
          minimized ? "Restore" : "Minimise",
          minimized ? ChevronDown : Minus,
          onminimize,
        )}{/if}
      {#if onexpand}{@render tool(
          expanded ? "Return to dashboard" : "Expand",
          expanded ? Minimize2 : Maximize2,
          onexpand,
        )}{/if}
      {#if onclose}{@render tool("Close", X, onclose)}{/if}
    </div>
  </header>

  <div class="relative min-h-0 flex-1 overflow-auto p-2.5" hidden={minimized}>
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
            "text-xs font-medium",
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
      <div class={cn("h-full", state === "stale" && "opacity-70")}>
        {@render children?.()}
      </div>
      {#if reason}
        <p class="text-muted-foreground mt-2 text-xs">{reason}</p>
      {/if}
    {/if}
  </div>
</section>
