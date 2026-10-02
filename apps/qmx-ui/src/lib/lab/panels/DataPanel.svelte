<script lang="ts">
  /**
   * Data for the Lab: datasets and features with coverage, plus ways to add
   * more (upload, connect a source, derive from another dataset). Uploads go
   * through the daemon's artifact staging (PUT /artifacts/stage).
   */
  import Plus from "@lucide/svelte/icons/plus";
  import Database from "@lucide/svelte/icons/database";
  import Sigma from "@lucide/svelte/icons/sigma";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ASSETS } from "../demo";

  const datasets = ASSETS.filter((a) => a.kind === "dataset");
  const features = ASSETS.filter((a) => a.kind === "feature");
  const COVER: Record<string, [number, number]> = {
    "d-fx": [0, 100],
    "d-news": [30, 100],
    "d-csv": [78, 96],
  };
  const ADD = [
    "Upload CSV or Excel",
    "Connect a data source",
    "Derive from a dataset",
    "From another run's output",
  ];
</script>

<div class="flex h-full flex-col">
  <div class="flex h-9 shrink-0 items-center border-b px-3 text-xs">
    <span class="text-muted-foreground">2015 to 2026</span>
    <DropdownMenu.Root>
      <DropdownMenu.Trigger>
        {#snippet child({ props })}
          <Button {...props} variant="ghost" size="sm" class="ml-auto h-7"
            ><Plus />Add data</Button
          >
        {/snippet}
      </DropdownMenu.Trigger>
      <DropdownMenu.Content align="end">
        {#each ADD as a (a)}
          <DropdownMenu.Item
            onclick={() =>
              workbench.notify(
                `${a}: needs the daemon to stage and register it.`,
              )}>{a}</DropdownMenu.Item
          >
        {/each}
      </DropdownMenu.Content>
    </DropdownMenu.Root>
  </div>
  <div class="min-h-0 flex-1 overflow-auto">
    <ul>
      {#each datasets as d (d.id)}
        {@const c = COVER[d.id] ?? [0, 100]}
        <li class="border-b border-border/50 px-3 py-2">
          <div class="flex items-center gap-2 text-sm">
            <Database class="text-muted-foreground size-4 shrink-0" />
            <span class="truncate">{d.name}</span>
          </div>
          <div
            class="bg-muted relative mt-1.5 h-1.5 overflow-hidden rounded-full"
            title="Coverage"
          >
            <span
              class="bg-primary/70 absolute inset-y-0"
              style="left: {c[0]}%; width: {c[1] - c[0]}%"
            ></span>
          </div>
          <p class="text-muted-foreground mt-1 text-xs">{d.meta}</p>
        </li>
      {/each}
    </ul>
    <p class="text-muted-foreground px-3 pt-3 pb-1 text-xs">Features</p>
    <ul>
      {#each features as f (f.id)}
        <li class="flex items-center gap-2 px-3 py-1.5 text-sm">
          <Sigma class="text-muted-foreground size-4" />{f.name}
          <span class="text-muted-foreground ml-auto text-xs">{f.meta}</span>
        </li>
      {/each}
    </ul>
  </div>
</div>
