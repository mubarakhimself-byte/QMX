<script lang="ts">
  import "../app.css";
  import PlatformRail from "$lib/shell/PlatformRail.svelte";

  let { children } = $props();
</script>

<div class="flex min-h-svh bg-background text-foreground">
  <PlatformRail />
  <div class="min-w-0 flex-1">{@render children()}</div>
</div>
