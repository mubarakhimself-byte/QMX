<script lang="ts">
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { Skeleton } from "$lib/components/ui/skeleton";
  import {
    FACTORY_TEST_LABEL,
    type ChromeState,
    type PackCapability,
  } from "$lib/bootstrap";
  import { cn } from "$lib/utils.js";

  let appCopilotOpen = $state(false);
  let expanded = $state(false);
  let viewport = $state({ x: 40, y: 12, zoom: 0.85 });
  let savedViewport = $state({ x: 40, y: 12, zoom: 0.85 });
  let widgetState = $state<ChromeState>("populated");
  let capability = $state<PackCapability>("mixed");

  const mainHistory = [
    "main-copilot: start a session",
    "main-copilot: cite a hit",
  ];
  const appHistory = [
    "app-copilot: inspect board",
    "app-copilot: request invoke",
  ];

  function expand() {
    savedViewport = { ...viewport };
    expanded = true;
    viewport = { x: 0, y: 0, zoom: 1 };
  }

  function ret() {
    expanded = false;
    viewport = { ...savedViewport };
  }
</script>

<svelte:head>
  <title>{FACTORY_TEST_LABEL} storyboard</title>
</svelte:head>

<main
  class="flex min-h-svh flex-col gap-4 p-4"
  data-testid="factory-test-storyboard"
>
  <p class="text-warning font-medium" data-testid="factory-test-label">
    {FACTORY_TEST_LABEL}
  </p>
  <p class="text-muted-foreground text-sm">
    Not product chrome. Preserves distinct interiors, optional app copilot,
    expand/return, independent histories, visual/headless/mixed, and readable
    states.
  </p>

  <div class="flex flex-wrap gap-2">
    {#each ["visual", "headless", "mixed"] as item (item)}
      <Button
        size="sm"
        variant={capability === item ? "default" : "outline"}
        data-testid={`capability-${item}`}
        onclick={() => (capability = item as PackCapability)}
      >
        {item}
      </Button>
    {/each}
    <Button
      size="sm"
      variant="outline"
      data-testid="toggle-app-copilot"
      onclick={() => (appCopilotOpen = !appCopilotOpen)}
    >
      {appCopilotOpen ? "Hide app copilot" : "Show app copilot"}
    </Button>
  </div>
  <p data-testid="capability-copy">
    Capability {capability}. Headless packs stay first-class with no navigation
    pane. Attaching context does not grant execution authority.
  </p>

  <div
    class={cn("grid gap-3 md:grid-cols-2", appCopilotOpen && "md:grid-cols-3")}
  >
    <section
      class="bg-surface border-border rounded-lg border p-3"
      data-testid="main-copilot"
    >
      <h2 class="text-sm font-medium">Main copilot</h2>
      <p class="text-muted-foreground text-sm">
        Conversation workspace. Independent of Home.
      </p>
      <ul data-testid="main-copilot-history">
        {#each mainHistory as line (line)}
          <li>{line}</li>
        {/each}
      </ul>
    </section>

    <section
      class="bg-surface border-border rounded-lg border p-3"
      data-testid="application-interior"
      class:col-span-2={expanded}
    >
      <div class="flex items-center justify-between gap-2">
        <h2 class="text-sm font-medium">Application interior</h2>
        {#if expanded}
          <Button
            size="sm"
            variant="outline"
            data-testid="widget-return"
            onclick={ret}
          >
            Return
          </Button>
        {:else}
          <Button
            size="sm"
            variant="outline"
            data-testid="widget-expand"
            onclick={expand}
          >
            Expand
          </Button>
        {/if}
      </div>
      <p data-testid="widget-viewport">
        viewport x={viewport.x} y={viewport.y} zoom={viewport.zoom}
      </p>
      <p class="text-muted-foreground text-sm">
        Expand/return is WidgetFrame layout, not a fifth rail destination.
        Widgets never own invoke.
      </p>
      <div class="mt-2" data-testid="widget-frame" data-state={widgetState}>
        {#if widgetState === "loading"}
          <Skeleton class="h-16 w-full" />
        {:else if widgetState === "empty"}
          <p>Empty. One action to populate.</p>
        {:else if widgetState === "error"}
          <p class="text-destructive">
            GRANT_AMBIGUOUS. Typed refusal. Shell remains usable.
          </p>
        {:else if widgetState === "stale"}
          <Badge variant="outline">stale</Badge>
        {:else if widgetState === "reconnecting"}
          <Badge variant="secondary">reconnecting</Badge>
        {:else if widgetState === "denied"}
          <Badge variant="destructive">denied</Badge>
        {:else}
          <p>
            Board widget with meaningful content. Graph viewport restores on
            return. Widgets emit request_invoke; they never import the wire
            client.
          </p>
        {/if}
      </div>
      <div class="mt-2 flex flex-wrap gap-1">
        {#each ["loading", "empty", "error", "stale", "reconnecting", "denied", "populated"] as item (item)}
          <Button
            size="sm"
            variant="ghost"
            data-testid={`widget-state-${item}`}
            onclick={() => (widgetState = item as ChromeState)}
          >
            {item}
          </Button>
        {/each}
      </div>
    </section>

    {#if appCopilotOpen}
      <section
        class="bg-surface border-border rounded-lg border p-3"
        data-testid="app-copilot"
      >
        <h2 class="text-sm font-medium">Optional app copilot</h2>
        <p class="text-muted-foreground text-sm">
          Profile app-use. Independent history from main copilot.
        </p>
        <ul data-testid="app-copilot-history">
          {#each appHistory as line (line)}
            <li>{line}</li>
          {/each}
        </ul>
      </section>
    {/if}
  </div>
</main>
