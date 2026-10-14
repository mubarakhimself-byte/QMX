<script lang="ts">
  /** The app opens on the screen chosen in Settings, General (Home by default). */
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import { onMount } from "svelte";
  import { settings } from "$lib/settings/settings.svelte";

  const START = {
    home: () => resolve("/home"),
    copilot: () => resolve("/copilot"),
    lab: () => resolve("/lab"),
    portfolio: () => resolve("/portfolio"),
    library: () => resolve("/library"),
    apps: () => resolve("/apps"),
  } as const;

  onMount(() => {
    const to =
      START[settings.general.start as keyof typeof START] ?? START.home;
    // eslint-disable-next-line svelte/no-navigation-without-resolve -- every START entry calls resolve()
    goto(to(), { replaceState: true });
  });
</script>
