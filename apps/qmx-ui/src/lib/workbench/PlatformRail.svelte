<script lang="ts">
  import { page } from "$app/state";
  import ChartCandlestick from "@lucide/svelte/icons/chart-candlestick";
  import RailButton from "./RailButton.svelte";
  import {
    PRODUCT_DESTINATIONS,
    SETTINGS_DESTINATION,
    isActive,
  } from "./destinations";
  import { workbench } from "./workbench.svelte";
</script>

<nav
  aria-label="Platform"
  class="bg-sidebar border-sidebar-border flex w-14 shrink-0 flex-col items-center gap-1 border-r py-2"
>
  <div
    class="text-foreground mb-2 flex size-10 items-center justify-center text-xs font-semibold tracking-tight"
    aria-hidden="true"
  >
    QMX
  </div>

  {#each PRODUCT_DESTINATIONS as d (d.id)}
    <RailButton
      href={d.href}
      label={d.label}
      icon={d.icon}
      active={isActive(page.url.pathname, d.href)}
    />
  {/each}

  <div class="bg-border my-2 h-px w-8" role="separator"></div>

  <ul aria-label="Opened apps" class="flex flex-col items-center gap-1">
    {#each workbench.railApps as app (app.instanceId)}
      <li>
        <RailButton
          href={`/apps/${encodeURIComponent(app.instanceId)}`}
          label={app.label}
          icon={ChartCandlestick}
          active={isActive(
            page.url.pathname,
            `/apps/${encodeURIComponent(app.instanceId)}`,
          )}
          badge={app.attention}
        />
      </li>
    {/each}
  </ul>

  <div class="mt-auto">
    <RailButton
      href={SETTINGS_DESTINATION.href}
      label={SETTINGS_DESTINATION.label}
      icon={SETTINGS_DESTINATION.icon}
      active={isActive(page.url.pathname, SETTINGS_DESTINATION.href)}
    />
  </div>
</nav>
