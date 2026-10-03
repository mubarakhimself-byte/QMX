<script lang="ts">
  /** A Library item as a card: family colour, name, what it is, and how widely it is used. */
  import { cn } from "$lib/utils";
  import { familyColor, shelfById, type LibraryItem } from "./items";

  let {
    item,
    selected = false,
    onselect,
  }: { item: LibraryItem; selected?: boolean; onselect: () => void } = $props();
  const shelf = $derived(shelfById(item.shelf)!);
  const color = $derived(familyColor(item));
  const places = $derived([...new Set(item.uses.map((u) => u.place))]);
</script>

<button
  type="button"
  class={cn(
    "solid-backing flex h-full w-full flex-col overflow-hidden rounded-xl border text-left transition-colors",
    selected ? "ring-primary ring-2" : "hover:border-ring/60",
  )}
  aria-pressed={selected}
  onclick={onselect}
>
  <span
    class="flex h-9 items-center gap-2 px-3 text-xs font-medium text-white"
    style="background:{color}"
    ><shelf.icon class="size-3.5" />{item.family ?? shelf.label}
    {#if item.stage}<span class="ml-auto rounded bg-black/20 px-1.5"
        >{item.stage}</span
      >{/if}</span
  >
  <span class="flex flex-1 flex-col gap-1 p-3">
    <span class="line-clamp-2 text-sm leading-snug font-semibold"
      >{item.name}{#if item.version}<span
          class="text-muted-foreground ml-1.5 font-normal">{item.version}</span
        >{/if}</span
    >
    <span class="text-muted-foreground line-clamp-2 text-xs"
      >{item.summary}</span
    >
    <span class="text-muted-foreground mt-auto pt-1 text-[11px]">
      {#if item.starts}Starts: {item.starts.what.toLowerCase()}{:else if places.length}Used
        in {places.join(", ")}{:else}Not used yet{/if}
    </span>
  </span>
</button>
