<script lang="ts">
  import "../app.css";
  import * as Tooltip from "$lib/components/ui/tooltip";
  import PlatformRail from "$lib/workbench/PlatformRail.svelte";
  import StatusBar from "$lib/workbench/StatusBar.svelte";
  import InkBackground from "$lib/workbench/InkBackground.svelte";
  import { workbench, THEMES } from "$lib/workbench/workbench.svelte";
  import { page } from "$app/state";

  let { children } = $props();

  // Theme classes live on <html> so popovers and portals inherit them.
  $effect(() => {
    const root = document.documentElement;
    for (const t of THEMES) root.classList.remove(`theme-${t}`);
    root.classList.add(`theme-${workbench.theme}`);
    root.classList.add("glass");
    // Paper is the one light theme.
    root.classList.toggle("dark", workbench.theme !== "paper");
  });
  // Trading surfaces never get the decorative background.
  const showInk = $derived(
    workbench.inkEnabled && !page.url.pathname.startsWith("/trade"),
  );
</script>

<Tooltip.Provider delayDuration={300}>
  <div class="text-foreground flex h-svh flex-col overflow-hidden">
    {#if showInk}<InkBackground />{/if}
    <div class="flex min-h-0 flex-1">
      <PlatformRail />
      <main class="min-w-0 flex-1 overflow-hidden">{@render children()}</main>
    </div>
    <StatusBar />
  </div>
</Tooltip.Provider>
