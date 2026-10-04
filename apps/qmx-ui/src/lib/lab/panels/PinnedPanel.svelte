<script lang="ts">
  /** A panel the copilot built and you pinned: drawn from its description. */
  import SpecView from "$lib/sdk/SpecView.svelte";
  import { pinned } from "$lib/sdk/pinned.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";

  let { tile }: { tile?: string } = $props();
  const spec = $derived(tile ? pinned.panels[tile] : undefined);
</script>

<div class="h-full overflow-auto p-3">
  {#if spec}
    <SpecView
      {spec}
      onaction={(op) =>
        workbench.notify(
          `The panel asked the host to run ${op} (needs the daemon).`,
        )}
    />
  {:else}
    <p class="text-muted-foreground text-sm">
      This pinned panel's description is missing in this browser.
    </p>
  {/if}
</div>
