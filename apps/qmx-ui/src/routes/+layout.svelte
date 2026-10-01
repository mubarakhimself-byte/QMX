<script lang="ts">
  import "../app.css";
  import * as Tooltip from "$lib/components/ui/tooltip";
  import PlatformRail from "$lib/workbench/PlatformRail.svelte";
  import StatusBar from "$lib/workbench/StatusBar.svelte";

  let { children } = $props();
</script>

<Tooltip.Provider delayDuration={300}>
  <div
    class="bg-background text-foreground flex h-svh flex-col overflow-hidden"
  >
    <div class="flex min-h-0 flex-1">
      <PlatformRail />
      <main class="min-w-0 flex-1 overflow-hidden">{@render children()}</main>
    </div>
    <StatusBar />
  </div>
</Tooltip.Provider>
