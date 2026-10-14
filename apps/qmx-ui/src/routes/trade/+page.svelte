<script lang="ts">
  // The trading servers folded into Portfolio → Live (operator ruling 2026-10-03).
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";

  onMount(() => {
    // eslint-disable-next-line svelte/no-navigation-without-resolve -- resolved path plus a query string
    goto(`${resolve("/portfolio")}?layout=live`, { replaceState: true });
  });
</script>

<p class="text-muted-foreground p-6 text-sm">Moved to Portfolio…</p>
