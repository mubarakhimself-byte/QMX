<script lang="ts">
  /**
   * A tiling board: panels side by side and stacked, resizable, linked by
   * colour, minimised to a dock (neighbours take the space), expanded to fill
   * the board, dragged onto each other to swap, closed and added in edit
   * mode. The parent owns the layout and the catalog; panels render through
   * the `panel` snippet. Unknown panels show a reason, never an error.
   */
  import type { Component, Snippet } from "svelte";
  import Minus from "@lucide/svelte/icons/minus";
  import Maximize2 from "@lucide/svelte/icons/maximize-2";
  import Minimize2 from "@lucide/svelte/icons/minimize-2";
  import X from "@lucide/svelte/icons/x";
  import GripVertical from "@lucide/svelte/icons/grip-vertical";
  import Link2 from "@lucide/svelte/icons/link-2";
  import Puzzle from "@lucide/svelte/icons/puzzle";
  import * as Resizable from "$lib/components/ui/resizable";
  import * as Tooltip from "$lib/components/ui/tooltip";
  import { cn } from "$lib/utils";
  import {
    LINK_GROUPS,
    panes,
    removePane,
    setSizes,
    swapPanels,
    visibleTree,
    type LinkGroup,
    type TileLayout,
    type TileNode,
    type TilePane,
  } from "./tiles";

  export type PanelInfo = { title: string; icon: Component; note?: string };

  let {
    layout,
    catalog,
    editing = false,
    onchange,
    panel,
    tools,
    class: className,
  }: {
    layout: TileLayout;
    catalog: Record<string, PanelInfo>;
    editing?: boolean;
    onchange: (next: TileLayout) => void;
    panel: Snippet<[TilePane]>;
    /** Extra controls in a tile's title bar (e.g. a mode switch). */
    tools?: Snippet<[TilePane]>;
    class?: string;
  } = $props();

  let expanded = $state<string | null>(null);
  let dragging = $state<string | null>(null);
  let dropTarget = $state<string | null>(null);

  const visible = $derived(visibleTree(layout.root, layout.docked));
  const all = $derived(panes(layout.root));
  const expandedPane = $derived(all.find((p) => p.id === expanded));

  const LINK_CLASS: Record<LinkGroup, string> = {
    violet: "bg-[oklch(0.68_0.17_295)]",
    amber: "bg-[oklch(0.8_0.15_75)]",
    teal: "bg-[oklch(0.75_0.12_185)]",
  };

  const info = (p: TilePane): PanelInfo =>
    catalog[p.panel] ?? {
      title: "Unsupported panel",
      icon: Puzzle,
      note: `No app provides "${p.panel}". Install the app that adds it, or close this tile.`,
    };

  function minimise(id: string) {
    if (expanded === id) expanded = null;
    onchange({ ...layout, docked: [...layout.docked, id] });
  }
  function restore(id: string) {
    onchange({ ...layout, docked: layout.docked.filter((d) => d !== id) });
  }
  function close(id: string) {
    const root = removePane(layout.root, id);
    if (!root) return;
    onchange({
      ...layout,
      root,
      docked: layout.docked.filter((d) => d !== id),
    });
  }
  function cycleLink(p: TilePane) {
    const order: (LinkGroup | undefined)[] = [undefined, ...LINK_GROUPS];
    const next = order[(order.indexOf(p.link) + 1) % order.length];
    const walk = (n: TileNode): TileNode =>
      n.kind === "split"
        ? { ...n, children: n.children.map(walk) }
        : n.id === p.id
          ? { ...n, link: next }
          : n;
    onchange({ ...layout, root: walk(layout.root) });
  }
  function drop(target: string) {
    if (dragging && dragging !== target)
      onchange({
        ...layout,
        root: swapPanels(layout.root, dragging, target),
      });
    dragging = null;
    dropTarget = null;
  }
  let sizeTimer: ReturnType<typeof setTimeout> | undefined;
  function resized(path: number[], sizes: number[]) {
    clearTimeout(sizeTimer);
    sizeTimer = setTimeout(
      () =>
        onchange({
          ...layout,
          root: setSizes(layout.root, path, sizes, layout.docked),
        }),
      250,
    );
  }
  const keyOf = (n: TileNode): string =>
    n.kind === "pane" ? n.id : `${n.dir}(${n.children.map(keyOf).join(",")})`;
</script>

{#snippet tile(p: TilePane, isExpanded = false)}
  {@const i = info(p)}
  <section
    class={cn(
      "tile flex h-full min-h-0 flex-col overflow-hidden rounded-lg",
      dropTarget === p.id && "ring-ring ring-2",
    )}
    aria-label={i.title}
    ondragover={(e) => {
      if (!dragging) return;
      e.preventDefault();
      dropTarget = p.id;
    }}
    ondragleave={() => dropTarget === p.id && (dropTarget = null)}
    ondrop={(e) => {
      e.preventDefault();
      drop(p.id);
    }}
  >
    <header class="flex h-9 shrink-0 items-center gap-1.5 border-b pr-1 pl-1.5">
      <div
        class="flex min-w-0 flex-1 cursor-grab items-center gap-1.5 active:cursor-grabbing"
        role="button"
        tabindex="-1"
        aria-roledescription="Drag onto another tile to swap them"
        draggable={!isExpanded}
        ondragstart={(e) => {
          dragging = p.id;
          e.dataTransfer?.setData("text/plain", p.id);
        }}
        ondragend={() => {
          dragging = null;
          dropTarget = null;
        }}
      >
        <GripVertical
          class="text-muted-foreground/60 size-3.5 shrink-0"
          aria-hidden="true"
        />
        <i.icon class="text-muted-foreground size-4 shrink-0" />
        <h3 class="truncate text-sm font-medium">{i.title}</h3>
      </div>
      <div class="flex shrink-0 items-center gap-0.5">
        {@render tools?.(p)}
        <Tooltip.Root>
          <Tooltip.Trigger>
            {#snippet child({ props })}
              <button
                {...props}
                type="button"
                class="hover:bg-muted flex size-7 items-center justify-center rounded-md"
                aria-label={p.link
                  ? `Linked to the ${p.link} group; change`
                  : "Not linked; link to a group"}
                onclick={() => cycleLink(p)}
              >
                {#if p.link}
                  <span class={cn("size-2.5 rounded-sm", LINK_CLASS[p.link])}
                  ></span>
                {:else}
                  <Link2 class="text-muted-foreground size-3.5" />
                {/if}
              </button>
            {/snippet}
          </Tooltip.Trigger>
          <Tooltip.Content
            >Tiles with the same colour follow one selection</Tooltip.Content
          >
        </Tooltip.Root>
        {#if !isExpanded}
          <button
            type="button"
            class="hover:bg-muted flex size-7 items-center justify-center rounded-md"
            aria-label={`Minimise ${i.title}`}
            onclick={() => minimise(p.id)}><Minus class="size-3.5" /></button
          >
        {/if}
        <button
          type="button"
          class="hover:bg-muted flex size-7 items-center justify-center rounded-md"
          aria-label={isExpanded ? "Return to layout" : `Expand ${i.title}`}
          onclick={() => (expanded = isExpanded ? null : p.id)}
        >
          {#if isExpanded}<Minimize2 class="size-3.5" />{:else}<Maximize2
              class="size-3.5"
            />{/if}
        </button>
        {#if editing && !isExpanded && all.length > 1}
          <button
            type="button"
            class="hover:bg-destructive/15 hover:text-destructive flex size-7 items-center justify-center rounded-md"
            aria-label={`Close ${i.title}`}
            onclick={() => close(p.id)}><X class="size-3.5" /></button
          >
        {/if}
      </div>
    </header>
    <div class="relative min-h-0 flex-1">
      {#if catalog[p.panel]}
        {@render panel(p)}
      {:else}
        <div
          class="text-muted-foreground flex h-full flex-col items-center justify-center gap-2 p-6 text-center text-sm"
        >
          <Puzzle class="size-5" />
          <p class="max-w-xs">{i.note}</p>
        </div>
      {/if}
    </div>
  </section>
{/snippet}

{#snippet node(n: TileNode, path: number[])}
  {#if n.kind === "pane"}
    {@render tile(n)}
  {:else}
    {#key keyOf(n)}
      <Resizable.PaneGroup
        direction={n.dir === "row" ? "horizontal" : "vertical"}
        onLayoutChange={(sizes) => resized(path, sizes)}
        class="gap-0"
      >
        {#each n.children as c, k (keyOf(c))}
          {#if k > 0}
            <Resizable.Handle
              class={cn(
                "bg-transparent",
                n.dir === "row" ? "mx-[3px]" : "my-[3px]",
              )}
            />
          {/if}
          <Resizable.Pane defaultSize={n.sizes[k]} minSize={8}>
            {@render node(c, [...path, k])}
          </Resizable.Pane>
        {/each}
      </Resizable.PaneGroup>
    {/key}
  {/if}
{/snippet}

<div class={cn("flex h-full min-h-0 flex-col gap-1.5", className)}>
  <div class="min-h-0 flex-1">
    {#if expandedPane}
      {@render tile(expandedPane, true)}
    {:else if visible}
      {@render node(visible, [])}
    {:else}
      <div
        class="text-muted-foreground flex h-full items-center justify-center text-sm"
      >
        Every tile is minimised. Restore one from the dock below.
      </div>
    {/if}
  </div>
  {#if layout.docked.length}
    <div
      class="tile flex h-9 shrink-0 items-center gap-1 overflow-x-auto rounded-lg px-1.5"
      aria-label="Minimised tiles"
    >
      <span class="text-muted-foreground px-1.5 text-xs">Minimised</span>
      {#each layout.docked as id (id)}
        {@const p = all.find((x) => x.id === id)}
        {#if p}
          {@const i = info(p)}
          <button
            type="button"
            class="hover:bg-muted flex h-7 shrink-0 items-center gap-1.5 rounded-md border px-2 text-xs"
            onclick={() => restore(id)}
            aria-label={`Restore ${i.title}`}
          >
            {#if p.link}<span
                class={cn("size-2 rounded-sm", LINK_CLASS[p.link])}
              ></span>{/if}
            <i.icon class="size-3.5" />{i.title}
          </button>
        {/if}
      {/each}
    </div>
  {/if}
</div>
