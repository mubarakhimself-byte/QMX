<script lang="ts">
  import "../app.css";
  import * as Tooltip from "$lib/components/ui/tooltip";
  import PlatformRail from "$lib/workbench/PlatformRail.svelte";
  import StatusBar from "$lib/workbench/StatusBar.svelte";
  import InkBackground from "$lib/workbench/InkBackground.svelte";
  import { workbench, THEMES } from "$lib/workbench/workbench.svelte";
  import { page } from "$app/state";
  import { resolve } from "$app/paths";

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
    {#if workbench.notice}
      <div
        role="status"
        class="surface fixed right-4 bottom-10 z-50 flex max-w-md items-center gap-3 rounded-lg px-4 py-2.5 text-sm"
      >
        <span class="min-w-0 flex-1 truncate">{workbench.notice.text}</span>
        {#if workbench.notice.href}
          <a
            class="text-primary shrink-0 font-medium hover:underline"
            href={resolve(workbench.notice.href as "/")}
            >{workbench.notice.action ?? "Open"}</a
          >
        {/if}
      </div>
    {/if}
  </div>
</Tooltip.Provider>
