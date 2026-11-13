<script lang="ts">
  import "../app.css";
  import * as Tooltip from "$lib/components/ui/tooltip";
  let { children } = $props();
</script>

<!-- Tooltips wait a moment the first time, then follow the pointer at once. -->
<Tooltip.Provider delayDuration={350} skipDelayDuration={400}>
  {@render children()}
</Tooltip.Provider>
