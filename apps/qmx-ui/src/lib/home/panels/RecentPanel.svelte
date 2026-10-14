<script lang="ts">
  /** Recently touched Library items, each opening where it lives. */
  import { resolve } from "$app/paths";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { LIBRARY, familyColor, shelfById } from "$lib/library/items";

  const size = panelSize();
  const RECENT = [
    "lab-trend",
    "btc-breakout",
    "tpl-news",
    "stress-mine-1",
    "paper-trend",
    "breakout-scorer",
    "src-arxiv",
  ]
    .map((id) => LIBRARY.find((i) => i.id === id))
    .filter((i) => !!i);
</script>

<ul class="p-panel h-full overflow-auto">
  <!-- eslint-disable svelte/no-navigation-without-resolve -->
  {#each RECENT as i (i.id)}
    {@const s = shelfById(i.shelf)!}
    <li>
      <a
        href={`${resolve("/library")}?shelf=${i.shelf}&item=${i.id}`}
        class="hover:bg-muted/60 py-row -mx-2 flex items-center gap-3 rounded-md px-2"
      >
        <span
          class="h-7 w-1 shrink-0 rounded-full"
          style="background:{familyColor(i)}"
        ></span>
        <s.icon class="text-muted-foreground size-4 shrink-0" />
        <span class="min-w-0 flex-1">
          <span class="block truncate text-sm">{i.name}</span>
          {#if size.mode !== "compact"}<span
              class="text-muted-foreground block truncate text-xs"
              >{size.mode === "expanded"
                ? `${s.label} · ${i.summary}`
                : s.label}</span
            >{/if}
        </span>
      </a>
    </li>
  {/each}
  <!-- eslint-enable svelte/no-navigation-without-resolve -->
</ul>
