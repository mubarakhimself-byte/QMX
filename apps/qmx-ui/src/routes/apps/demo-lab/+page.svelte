<script lang="ts">
  // Merged into the Lab (operator ruling 2026-10-02). Old links land there.
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";

  onMount(() => {
    // eslint-disable-next-line svelte/no-navigation-without-resolve -- resolved path plus a query string
    goto(`${resolve("/lab")}?layout=test`, { replaceState: true });
  });
</script>

<p class="text-muted-foreground p-6 text-sm">Moved to the Lab…</p>
