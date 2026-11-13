<script lang="ts">
  import Shell from "$lib/shell/Shell.svelte";
  import Harness from "$lib/shell/Harness.svelte";
  import { shell } from "$lib/shell/state.svelte";

  // ?review=off shows the app as it runs in its own desktop window: edge to
  // edge, without the review frame, the strip under it or the review pill.
  // The shell keeps every other URL parameter, so the switch stays in the URL.
  const review = typeof location === "undefined" || new URLSearchParams(location.search).get("review") !== "off";
  $effect(() => {
    document.documentElement.dataset.text = shell.text;
  });
</script>

<svelte:head><title>QMX</title></svelte:head>

{#if review}
  <!-- The app sits in a window; the strip under it is review chrome only. -->
  <div class="flex h-full flex-col overflow-hidden px-2 pt-2 pb-[4.5rem]">
    <div class="min-h-0 flex-1 overflow-hidden rounded-xl ring-1 ring-white/10">
      <Shell />
    </div>
  </div>
  <Harness />
{:else}
  <div class="h-full overflow-hidden"><Shell /></div>
{/if}
