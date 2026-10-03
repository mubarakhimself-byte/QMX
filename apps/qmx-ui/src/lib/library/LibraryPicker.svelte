<script lang="ts">
  /**
   * Pick from the Library without leaving the screen you are on: the
   * copilot's "From Library…" attach opens this (it used to jump away to the
   * Library page). Picking adds the item to the message as a chip.
   */
  import Search from "@lucide/svelte/icons/search";
  import Check from "@lucide/svelte/icons/check";
  import { resolve } from "$app/paths";
  import * as Dialog from "$lib/components/ui/dialog";
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import { LIBRARY, SHELVES, familyColor, shelfById } from "./items";

  let {
    open = $bindable(false),
    onpick,
  }: { open?: boolean; onpick: (name: string) => void } = $props();

  let query = $state("");
  let shelf = $state<string | null>(null);
  let picked = $state<string[]>([]);
  const q = $derived(query.trim().toLowerCase());
  const list = $derived(
    LIBRARY.filter(
      (i) =>
        (!shelf || i.shelf === shelf) &&
        (!q ||
          i.name.toLowerCase().includes(q) ||
          i.summary.toLowerCase().includes(q)),
    ).slice(0, 80),
  );
  const shelvesWithItems = SHELVES.filter((s) =>
    LIBRARY.some((i) => i.shelf === s.id),
  );
  $effect(() => {
    if (!open) picked = [];
  });
</script>

<Dialog.Root bind:open>
  <Dialog.Content class="flex h-[min(36rem,85vh)] flex-col gap-3 sm:max-w-2xl">
    <Dialog.Header>
      <Dialog.Title>Attach from the Library</Dialog.Title>
      <Dialog.Description
        >Pick bots, pods, reports, articles… They join your message.</Dialog.Description
      >
    </Dialog.Header>
    <div class="relative">
      <Search
        class="text-muted-foreground pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2"
      />
      <Input
        bind:value={query}
        class="h-9 pl-8"
        placeholder="Search the Library"
        aria-label="Search the Library"
      />
    </div>
    <div class="flex flex-wrap gap-1">
      <button
        type="button"
        class={cn(
          "h-7 rounded-md border px-2 text-xs",
          !shelf ? "border-primary bg-primary/12" : "hover:bg-muted",
        )}
        onclick={() => (shelf = null)}>All</button
      >
      {#each shelvesWithItems as s (s.id)}
        <button
          type="button"
          class={cn(
            "flex h-7 items-center gap-1 rounded-md border px-2 text-xs",
            shelf === s.id ? "border-primary bg-primary/12" : "hover:bg-muted",
          )}
          onclick={() => (shelf = s.id)}
          ><s.icon class="size-3" />{s.label}</button
        >
      {/each}
    </div>
    <ul class="min-h-0 flex-1 overflow-auto rounded-md border">
      {#each list as i (i.id)}
        {@const on = picked.includes(i.id)}
        <li>
          <button
            type="button"
            class={cn(
              "hover:bg-muted/60 flex w-full items-center gap-3 border-b px-3 py-2 text-left",
              on && "bg-primary/10",
            )}
            aria-pressed={on}
            onclick={() => {
              if (on) return;
              picked = [...picked, i.id];
              onpick(i.name);
            }}
          >
            <span
              class="h-6 w-1 shrink-0 rounded-full"
              style="background:{familyColor(i)}"
            ></span>
            <span class="min-w-0 flex-1">
              <span class="block truncate text-sm">{i.name}</span>
              <span class="text-muted-foreground block truncate text-xs"
                >{shelfById(i.shelf)?.label} · {i.summary}</span
              >
            </span>
            {#if on}<Check class="text-success size-4" />{/if}
          </button>
        </li>
      {/each}
    </ul>
    <Dialog.Footer class="items-center">
      <a
        href={resolve("/library")}
        class="text-muted-foreground mr-auto text-xs underline"
        >Open the Library</a
      >
      <Button onclick={() => (open = false)}
        >{picked.length ? `Done · ${picked.length} attached` : "Close"}</Button
      >
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
