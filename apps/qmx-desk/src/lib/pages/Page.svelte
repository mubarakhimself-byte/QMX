<script lang="ts">
  import { shell } from "$lib/shell/state.svelte";
  import { things } from "$lib/shell/things.svelte";
  import ListView from "./ListView.svelte";
  import ObjectPage from "./ObjectPage.svelte";

  // A thing's page. Opened from a list, the list stays beside it as a narrow
  // spine, with its scroll and filter, so he keeps his place.
  const at = $derived(shell.page!);
  const obj = $derived(things.get(at.id));
  const spine = $derived(at.list && !at.sub ? at.list : undefined);
</script>

{#if obj}
  <div class="pg flex h-full min-h-0">
    {#if spine}
      <aside class="spine border-border h-full w-[17rem] shrink-0 border-r">
        <ListView list={spine} spine current={obj.id} />
      </aside>
    {/if}
    <div class="min-h-0 min-w-0 flex-1">
      {#key obj.id + (at.sub ?? "")}
        <ObjectPage o={obj} sub={at.sub} />
      {/key}
    </div>
  </div>
{:else}
  <div class="grid h-full place-items-center">
    <div class="flex flex-col items-center gap-3">
      <p class="text-lg">That thing is not here.</p>
      <button class="press border-border h-10 border px-4" onclick={() => shell.jump(-1)}>Back to {shell.current.name}</button>
    </div>
  </div>
{/if}

<style>
  .pg {
    container-type: inline-size;
  }
  .spine {
    --surface-bg: var(--panel);
  }
  /* A narrow window or big text: the spine yields to the page. The trail
     still leads back to the list. */
  @container (max-width: 56rem) {
    .spine {
      display: none;
    }
  }
</style>
