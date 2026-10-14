<script lang="ts">
  /**
   * A tile's body: measures itself, provides the size mode to the panel
   * inside (`panelSize()`), and exposes it as `data-size` for CSS
   * (`group-data-[size=compact]/panel:hidden`).
   */
  import type { Snippet } from "svelte";
  import { workbench } from "../workbench.svelte";
  import { providePanelSize, sizeMode } from "./panel-size";

  let {
    maximised = false,
    children,
  }: { maximised?: boolean; children: Snippet } = $props();

  let width = $state(0);
  let height = $state(0);
  // Before the first measurement, assume regular rather than flashing compact.
  const mode = $derived(
    width === 0
      ? "regular"
      : sizeMode({ width, height }, workbench.remPx, maximised),
  );
  providePanelSize({
    get mode() {
      return mode;
    },
  });
</script>

<div
  class="group/panel @container relative min-h-0 flex-1"
  data-size={mode}
  bind:clientWidth={width}
  bind:clientHeight={height}
>
  {@render children()}
</div>
