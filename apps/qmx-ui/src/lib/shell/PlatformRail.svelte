<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/state";
  import { resolve } from "$app/paths";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { FACTORY_TEST_LABEL } from "$lib/bootstrap";
  import { cn } from "$lib/utils.js";
  import {
    PRODUCT_DESTINATIONS,
    SETTINGS_CHROME,
    destinationFromPath,
    type ProductDestinationId,
  } from "./destinations";
  import {
    FACTORY_TEST_HEADLESS_PACK,
    FACTORY_TEST_VISUAL_APP,
    showsOpenedAppIcon,
  } from "./openedApps";
  import {
    addOpenedApp,
    applyOpenedAppFixture,
    closeOpenedApp,
    openSettingsChrome,
    resetOpenedApps,
    selectDestination,
    setSelectedFromPath,
    shellState,
  } from "./shellState";

  let expanded = $state(false);
  let keyboardIndex = $state(0);
  const snapshot = $derived($shellState);
  const current = $derived(destinationFromPath(page.url.pathname));
  const iconApps = $derived(snapshot.openedApps.filter(showsOpenedAppIcon));

  $effect(() => {
    setSelectedFromPath(current);
    if (current && current !== "settings") {
      const index = PRODUCT_DESTINATIONS.findIndex(
        (item) => item.id === current,
      );
      if (index >= 0) keyboardIndex = index;
    }
  });

  onMount(() => {
    applyOpenedAppFixture(
      new URLSearchParams(window.location.search).get("fixture"),
    );
  });

  function onSelect(id: ProductDestinationId) {
    selectDestination(id);
  }

  function onSettings() {
    openSettingsChrome();
  }

  function onDestKeydown(event: KeyboardEvent) {
    if (
      event.key !== "ArrowDown" &&
      event.key !== "ArrowUp" &&
      event.key !== "Home" &&
      event.key !== "End"
    ) {
      return;
    }
    event.preventDefault();
    const last = PRODUCT_DESTINATIONS.length - 1;
    if (event.key === "Home") keyboardIndex = 0;
    else if (event.key === "End") keyboardIndex = last;
    else if (event.key === "ArrowDown")
      keyboardIndex = keyboardIndex >= last ? 0 : keyboardIndex + 1;
    else keyboardIndex = keyboardIndex <= 0 ? last : keyboardIndex - 1;
    const node = document.querySelector<HTMLElement>(
      `[data-testid="rail-${PRODUCT_DESTINATIONS[keyboardIndex].id}"]`,
    );
    node?.focus();
  }
</script>

<aside
  class={cn(
    "bg-sidebar text-sidebar-foreground border-sidebar-border flex h-svh shrink-0 flex-col border-r",
    expanded ? "w-44" : "w-12",
  )}
  data-testid="platform-rail"
  data-expanded={expanded ? "true" : "false"}
>
  <nav
    class="flex flex-col gap-1 p-2"
    data-testid="rail-product-destinations"
    data-count={PRODUCT_DESTINATIONS.length}
    data-emits="select_destination"
    aria-label="Platform destinations"
  >
    {#each PRODUCT_DESTINATIONS as dest, index (dest.id)}
      {@const active = current === dest.id}
      <div class="group relative">
        <Button
          href={resolve(dest.href)}
          variant={active ? "secondary" : "ghost"}
          size={expanded ? "sm" : "icon"}
          class={cn("w-full", expanded ? "justify-start" : "justify-center")}
          data-testid={`rail-${dest.id}`}
          data-destination-id={dest.id}
          data-kind="product"
          aria-label={dest.label}
          aria-current={active ? "page" : undefined}
          tabindex={keyboardIndex === index ? 0 : -1}
          onclick={() => onSelect(dest.id)}
          onkeydown={onDestKeydown}
        >
          <span class="inline-flex size-4 shrink-0" aria-hidden="true">
            {#if dest.id === "home"}
              <svg viewBox="0 0 16 16" fill="none" class="size-4">
                <path
                  d="M2.5 7.5 8 2.5l5.5 5V13a.5.5 0 0 1-.5.5H9V10H7v3.5H3a.5.5 0 0 1-.5-.5V7.5Z"
                  stroke="currentColor"
                  stroke-width="1.25"
                />
              </svg>
            {:else if dest.id === "copilot"}
              <svg viewBox="0 0 16 16" fill="none" class="size-4">
                <path
                  d="M3 3.5h10v7H6l-3 2v-9Z"
                  stroke="currentColor"
                  stroke-width="1.25"
                />
              </svg>
            {:else if dest.id === "library"}
              <svg viewBox="0 0 16 16" fill="none" class="size-4">
                <path
                  d="M3 3h3v10H3V3Zm5 0h5v10H8V3Z"
                  stroke="currentColor"
                  stroke-width="1.25"
                />
              </svg>
            {:else}
              <svg viewBox="0 0 16 16" fill="none" class="size-4">
                <circle cx="5" cy="5" r="1.25" stroke="currentColor" />
                <circle cx="11" cy="5" r="1.25" stroke="currentColor" />
                <circle cx="8" cy="11" r="1.25" stroke="currentColor" />
                <path
                  d="M6 5.5h4M6.2 6.2 7.5 10M9.8 6.2 8.5 10"
                  stroke="currentColor"
                  stroke-width="1.25"
                />
              </svg>
            {/if}
          </span>
          <span class={cn("truncate text-sm", !expanded && "sr-only")}
            >{dest.label}</span
          >
        </Button>
        {#if !expanded}
          <span
            class="bg-popover text-popover-foreground pointer-events-none absolute top-1/2 left-full z-20 ml-2 hidden -translate-y-1/2 rounded-md border px-2 py-1 text-xs whitespace-nowrap group-hover:block group-focus-within:block"
          >
            {dest.label}
          </span>
        {/if}
      </div>
    {/each}
  </nav>

  <div
    class="border-sidebar-border mx-2 border-t"
    data-testid="rail-divider"
    role="separator"
  ></div>

  <section
    class="flex flex-col gap-1 p-2"
    data-testid="rail-opened-apps"
    data-count={iconApps.length}
    data-emits="close_app"
    aria-label="Opened apps"
  >
    {#if iconApps.length === 0}
      <p class="sr-only">No opened apps</p>
    {/if}
    {#each iconApps as app (app.instanceId)}
      <div class="group relative flex flex-col items-center gap-1">
        <Button
          variant="outline"
          size={expanded ? "sm" : "icon"}
          class={cn("w-full", expanded ? "justify-start" : "justify-center")}
          data-testid="rail-opened-app"
          data-instance-id={app.instanceId}
          aria-label={app.label}
        >
          <span class="bg-primary inline-block size-2 rounded-full"></span>
          <span class={cn("truncate text-sm", !expanded && "sr-only")}
            >{app.label}</span
          >
        </Button>
        {#if app.badge}
          <Badge
            variant="outline"
            data-testid="rail-job-badge"
            data-cancel-authority="false"
            title="JobHandle observation, not cancel authority"
          >
            {app.badge.label}
          </Badge>
        {/if}
        <Button
          variant="ghost"
          size="icon-sm"
          class="size-6"
          data-testid="rail-close-app"
          data-instance-id={app.instanceId}
          aria-label={`Close ${app.label}`}
          onclick={() => closeOpenedApp(app.instanceId)}
        >
          <span aria-hidden="true">×</span>
        </Button>
      </div>
    {/each}
    {#if snapshot.headlessPackCount > 0}
      <p
        class="text-muted-foreground px-1 text-[10px] leading-tight"
        data-testid="headless-first-class"
      >
        Headless packs stay first-class. No navigation pane.
      </p>
    {/if}
  </section>

  <div class="flex-1"></div>

  <div class="flex flex-col gap-1 p-2">
    <Button
      variant="ghost"
      size={expanded ? "sm" : "icon"}
      class={cn("w-full", expanded ? "justify-start" : "justify-center")}
      data-testid="rail-toggle-labels"
      aria-label={expanded
        ? "Hide destination labels"
        : "Show destination labels"}
      aria-pressed={expanded}
      onclick={() => (expanded = !expanded)}
    >
      <span class="text-xs" aria-hidden="true">{expanded ? "«" : "»"}</span>
      <span class={cn("truncate text-sm", !expanded && "sr-only")}>Labels</span>
    </Button>
    <div class="group relative">
      <Button
        href={resolve(SETTINGS_CHROME.href)}
        variant={current === "settings" ? "secondary" : "ghost"}
        size={expanded ? "sm" : "icon"}
        class={cn("w-full", expanded ? "justify-start" : "justify-center")}
        data-testid="rail-settings"
        data-kind="chrome"
        aria-label={SETTINGS_CHROME.label}
        aria-current={current === "settings" ? "page" : undefined}
        onclick={onSettings}
      >
        <svg viewBox="0 0 16 16" fill="none" class="size-4" aria-hidden="true">
          <circle cx="8" cy="8" r="2" stroke="currentColor" />
          <path
            d="M8 2.5v1.5M8 12v1.5M2.5 8h1.5M12 8h1.5M4.1 4.1l1.1 1.1M10.8 10.8l1.1 1.1M4.1 11.9l1.1-1.1M10.8 5.2l1.1-1.1"
            stroke="currentColor"
            stroke-width="1.25"
          />
        </svg>
        <span class={cn("truncate text-sm", !expanded && "sr-only")}
          >{SETTINGS_CHROME.label}</span
        >
      </Button>
      {#if !expanded}
        <span
          class="bg-popover text-popover-foreground pointer-events-none absolute top-1/2 left-full z-20 ml-2 hidden -translate-y-1/2 rounded-md border px-2 py-1 text-xs group-hover:block group-focus-within:block"
        >
          Settings (chrome)
        </span>
      {/if}
    </div>
  </div>

  <aside
    class="border-sidebar-border text-muted-foreground border-t p-2 text-[10px] leading-tight"
    data-testid="factory-test-rail-fixtures"
  >
    <p class="text-foreground font-medium">{FACTORY_TEST_LABEL}</p>
    <p>Not product destinations. Not a fifth rail slot.</p>
    <div class="mt-1 flex flex-col gap-1">
      <Button
        size="sm"
        variant="outline"
        class="h-6 px-1 text-[10px]"
        data-testid="fixture-opened-visual"
        onclick={() => addOpenedApp(FACTORY_TEST_VISUAL_APP)}
      >
        visual app
      </Button>
      <Button
        size="sm"
        variant="outline"
        class="h-6 px-1 text-[10px]"
        data-testid="fixture-opened-headless"
        onclick={() => addOpenedApp(FACTORY_TEST_HEADLESS_PACK)}
      >
        headless pack
      </Button>
      <Button
        size="sm"
        variant="ghost"
        class="h-6 px-1 text-[10px]"
        data-testid="fixture-clear-opened"
        onclick={() => resetOpenedApps()}
      >
        clear apps
      </Button>
    </div>
    {#if snapshot.lastEvent}
      <p data-testid="chrome-last-event">
        {snapshot.lastEvent.type}
        {#if snapshot.lastEvent.type === "close_app"}
          {snapshot.lastEvent.unmount} cancelledJobHandles={String(
            snapshot.lastEvent.cancelledJobHandles,
          )}
        {:else}
          {snapshot.lastEvent.destination}
        {/if}
      </p>
    {/if}
    <p class="sr-only" data-testid="shell-snapshot">
      products={snapshot.productDestinationCount} settingsIsProduct={String(
        snapshot.settingsIsProduct,
      )}
      opened={snapshot.openedAppIconCount} headless={snapshot.headlessPackCount}
    </p>
  </aside>
</aside>
