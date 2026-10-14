<script lang="ts">
  /**
   * Built-in templates of some families, as Library cards. A card opens the
   * template in the Library, where "Use this template" starts it.
   */
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import ItemCard from "./ItemCard.svelte";
  import { LIBRARY } from "./items";

  let {
    families,
    title = "Templates",
  }: { families: string[]; title?: string } = $props();
  const items = $derived(
    LIBRARY.filter(
      (i) => i.shelf === "templates" && families.includes(i.family ?? ""),
    ),
  );
</script>

{#if items.length}
  <div class="flex flex-col gap-3">
    <div class="flex items-baseline gap-3">
      <h3 class="font-medium">{title}</h3>
      <!-- eslint-disable svelte/no-navigation-without-resolve -- resolved path plus a query string -->
      <a
        class="text-primary text-sm hover:underline"
        href={`${resolve("/library")}?shelf=templates`}>All templates</a
      ><!-- eslint-enable svelte/no-navigation-without-resolve -->
    </div>
    <ul class="grid grid-cols-[repeat(auto-fill,minmax(15rem,1fr))] gap-3">
      {#each items as item (item.id)}
        <li>
          <ItemCard
            {item}
            onselect={() =>
              // eslint-disable-next-line svelte/no-navigation-without-resolve -- resolved path plus a query string
              goto(`${resolve("/library")}?item=${item.id}`)}
          />
        </li>
      {/each}
    </ul>
  </div>
{/if}
