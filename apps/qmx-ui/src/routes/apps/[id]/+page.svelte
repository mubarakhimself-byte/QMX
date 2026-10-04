<script lang="ts">
  /**
   * An app's own screen: the same tile board as Home, the Lab and
   * Portfolio, made of the widgets the app declares. Rearrange it, add a
   * widget, or go back to its details. An app that isn't live yet says so
   * on every screen it draws.
   */
  import ArrowLeft from "@lucide/svelte/icons/arrow-left";
  import Pencil from "@lucide/svelte/icons/pencil";
  import Plus from "@lucide/svelte/icons/plus";
  import { page } from "$app/state";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import TileBoard from "$lib/workbench/tiles/TileBoard.svelte";
  import { LayoutStore } from "$lib/workbench/tiles/store.svelte";
  import { addPane, pane } from "$lib/workbench/tiles/tiles";
  import { STEPS, WIDGETS, apps, layoutFor } from "$lib/apps/apps.svelte";

  const app = apps.byId(page.params.id ?? "");
  const L = app
    ? new LayoutStore(`qmx.app.${app.id}.layouts`, [layoutFor(app)])
    : null;
  const catalog = Object.fromEntries(
    Object.entries(WIDGETS).map(([id, w]) => [
      id,
      { title: w.title, icon: w.icon, note: w.note },
    ]),
  );

  function add(id: string) {
    if (!L) return;
    const l = L.active;
    L.update({
      ...l,
      root: addPane(l.root, pane(`${id}-${Date.now().toString(36)}`, id)),
    });
  }
</script>

<div class="flex h-full min-h-0 flex-col">
  {#if !app || !L}
    <div class="mx-auto max-w-xl px-8 py-16">
      <h1 class="text-2xl font-semibold">No app here</h1>
      <p class="text-muted-foreground mt-2 text-lg">
        It may have been removed.
      </p>
      <Button class="mt-6" href={resolve("/apps")}><ArrowLeft />All apps</Button
      >
    </div>
  {:else}
    {#if app.stage < 4}
      <p class="bg-info/15 flex h-9 shrink-0 items-center px-4" role="note">
        Not live yet · {STEPS[app.stage]}: {app.stageNote}
      </p>
    {/if}
    <header class="flex flex-wrap items-center gap-3 border-b px-6 py-4">
      <Button
        variant="ghost"
        href={resolve("/apps")}
        onclick={() => (apps.selected = app.id)}><ArrowLeft />Apps</Button
      >
      <h1 class="mr-auto text-2xl font-semibold">{app.name}</h1>
      <Button
        variant={L.editing ? "default" : "outline"}
        onclick={() => (L.editing = !L.editing)}
        ><Pencil />{L.editing ? "Done" : "Edit layout"}</Button
      >
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button {...props} variant="outline"><Plus />Widget</Button>
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="end" class="max-h-96 w-72 overflow-auto">
          {#each Object.entries(WIDGETS) as [id, w] (id)}
            <DropdownMenu.Item
              class="flex-col items-start gap-0"
              onclick={() => add(id)}
              ><span>{w.title}</span><span class="text-muted-foreground text-sm"
                >From {w.from}</span
              ></DropdownMenu.Item
            >
          {/each}
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    </header>
    <div class="min-h-0 flex-1 p-2">
      <TileBoard
        layout={L.active}
        {catalog}
        editing={L.editing}
        onchange={(next) => L.update(next)}
      >
        {#snippet panel(p)}
          {@const View = WIDGETS[p.panel].view}
          <View tile={p.id} />
        {/snippet}
      </TileBoard>
    </div>
  {/if}
</div>
