<script lang="ts">
  import { shell } from "$lib/shell/state.svelte";
  import Frame from "./Frame.svelte";
  import FirstOpen from "./FirstOpen.svelte";
  import Tiles from "./tiles/Tiles.svelte";

  // A board is a tree of splits, the October UI's tiling (see tiles/). This
  // file picks what fills the main area: a widget's full view, day one, or
  // the place's tiled board.
  const place = $derived(shell.current);
</script>

{#if shell.activeDetail}
  {@const d = shell.activeDetail}
  <!-- A widget in its own tab fills the page, in its expanded mode. -->
  <div class="board flex h-full min-h-0 flex-col p-[var(--gap)] [&>section]:flex-1">
    <Frame panel={d.panel} full />
  </div>
{:else if shell.fixture === "first"}
  <div class="first h-full overflow-hidden">
    <FirstOpen {place} onstart={() => shell.toggleDock(true)} />
  </div>
{:else}
  <div class="board flex h-full min-h-0 flex-col p-[var(--gap)]">
    <Tiles {place} />
  </div>
{/if}

<style>
  /* Day one in a short window: tighten the welcome so nothing is cut off. */
  .first {
    container-type: size;
  }
  @container (max-height: 40rem) {
    .first > :global(div) {
      gap: 1rem;
      padding: 1rem 2rem;
    }
    .first :global(h2) {
      font-size: 2rem;
    }
    .first :global(h2 + p) {
      margin-top: 0.5rem;
      font-size: 1rem;
    }
    .first :global(ol li) {
      gap: 0.75rem;
      padding: 0.75rem;
    }
  }
  /* A widget's body may scroll down inside itself, never sideways. Narrow
     widgets show fewer table columns (first and last stay); the full table
     is one click away in the widget's own tab. */
  .board :global(section) {
    container-type: inline-size;
  }
  .board :global(section > div),
  .board :global(section .h-full.overflow-auto) {
    overflow-x: hidden;
  }
  .board :global(section > div:has(> .h-full.overflow-auto)) {
    overflow-y: hidden;
  }
  @container (max-width: 44rem) {
    .board :global(:is(th, td):nth-child(n + 2):nth-last-child(n + 3)) {
      display: none;
    }
  }
  @container (max-width: 30rem) {
    .board :global(:is(th, td):nth-child(n + 2):nth-last-child(n + 2)) {
      display: none;
    }
    .board :global(dl.grid-cols-2) {
      grid-template-columns: minmax(0, 1fr);
    }
    /* A list row's side note yields to its label, not the other way round. */
    .board :global(li > button > span.shrink-0.text-sm) {
      flex-shrink: 1;
      min-width: 0;
      max-width: 45%;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
</style>
