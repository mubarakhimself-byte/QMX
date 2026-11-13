<script lang="ts">
  /**
   * The tiling board, ported from the October UI (workbench/tiles). A layout
   * is a tree of splits; every edge between two widgets drags on its own.
   * Drag a widget by its header: drop on another widget's left, right, top or
   * bottom half to split there, on its centre to swap, or along the board's
   * outer edge to take a full row or column. Minimise docks a widget at the
   * foot and the rest take its space; restoring puts it back where it was.
   * The board never scrolls; a widget's body scrolls inside itself.
   */
  import type { Panel, Place } from "$lib/shell/data";
  import { shell } from "$lib/shell/state.svelte";
  import * as Menu from "$lib/components/ui/dropdown-menu";
  import Frame from "../Frame.svelte";
  import Icon from "../Icon.svelte";
  import Splitter from "../Splitter.svelte";
  import { defaultLayout, offered, refOf, resolve } from "./defaults";
  import { tiles } from "./store.svelte";
  import { rem as navRem } from "$lib/shell/nav/model.svelte";
  import {
    keyOf,
    minSize,
    movePane,
    insertPane,
    panes,
    removePane,
    setSizes,
    swapPanes,
    visibleTree,
    type Layout,
    type Node,
    type Side,
    type Split,
  } from "./tree";

  let { place }: { place: Place } = $props();

  const layout = $derived(tiles.layout(place));
  const all = $derived(panes(layout.root));
  const panel = (ref: string): Panel | null => resolve(shell.places, ref);
  // Widgets whose source is gone (an app removed) are left out, not shown broken.
  const hidden = $derived([...layout.docked, ...all.filter((r) => !panel(r))]);

  // SPACE-RULES 4: the board never scrolls. When the window cannot hold every
  // widget at its smallest, the last ones in the layout go to the dock for
  // now (not saved) and say so; a bigger window brings them back.
  let bw = $state(0);
  let bh = $state(0);
  const crowded = $derived.by(() => {
    if (!bw || !bh) return [] as string[];
    const r = rem();
    const out: string[] = [];
    let tree = visibleTree(layout.root, hidden);
    const order = panes(tree);
    while (tree && order.length > 1 && (minSize(tree, "w", gapRem) * r > bw + 1 || minSize(tree, "h", gapRem) * r > bh + 1)) {
      out.push(order.pop()!);
      tree = visibleTree(layout.root, [...hidden, ...out]);
    }
    return out;
  });
  const visible = $derived(visibleTree(layout.root, [...hidden, ...crowded]));
  const docked = $derived(layout.docked.filter((r) => panel(r)));

  const save = (next: Partial<Layout>) => tiles.set(place.id, { ...layout, ...next });
  const bare = (ref: string) => (ref.startsWith(`${shell.place}/`) ? ref.slice(shell.place.length + 1) : ref);

  function minimise(ref: string) {
    save({ docked: [...layout.docked.filter((d) => d !== ref), ref] });
  }
  function restore(ref: string) {
    save({ docked: layout.docked.filter((d) => d !== ref) });
  }
  function remove(ref: string) {
    save({ root: removePane(layout.root, ref), docked: layout.docked.filter((d) => d !== ref) });
  }
  // A new widget takes half of the biggest one on the board, so nothing gets
  // squeezed; it flashes once so the eye finds it. Drag it anywhere after.
  let added = $state<string | null>(null);
  function add(ref: string) {
    if (all.includes(ref)) return restore(ref);
    let best: { ref: string; area: number; wide: boolean } | null = null;
    for (const el of board?.querySelectorAll<HTMLElement>("[data-tile]") ?? []) {
      const r = el.getBoundingClientRect();
      if (!best || r.width * r.height > best.area) best = { ref: el.dataset.tile!, area: r.width * r.height, wide: r.width > r.height * 1.25 };
    }
    save({ root: insertPane(layout.root, ref, best?.ref ?? null, best?.wide === false ? "bottom" : "right") });
    added = ref;
    setTimeout(() => added === ref && (added = null), 900);
  }

  // Resizing: a handle reports the two shares on either side of it.
  function resized(path: number[], n: Split, k: number, a: number, b: number) {
    const sizes = [...n.sizes];
    sizes[k - 1] = a;
    sizes[k] = b;
    save({ root: setSizes(layout.root, path, sizes, hidden) });
  }
  // Double-click a handle: the two sides go back to the board's starting
  // ratio when that split is still the starting one, else share evenly.
  function evened(path: number[], n: Split, k: number) {
    const pair = n.sizes[k - 1] + n.sizes[k];
    const find = (x: Node | null): Split | null =>
      !x || x.kind === "pane" ? null : keyOf(x) === keyOf(n) ? x : x.children.map(find).find(Boolean) ?? null;
    const start = find(visibleTree(defaultLayout(place), hidden));
    const ratio = start ? start.sizes[k - 1] / (start.sizes[k - 1] + start.sizes[k]) : 0.5;
    resized(path, n, k, pair * ratio, pair * (1 - ratio));
  }
  const rem = () => navRem();
  const gapRem = 0.625;

  // Moving: pointer events, so the dragged header tracks the pointer exactly.
  type Zone = { target: string | null; side: Side | "centre"; l: number; t: number; w: number; h: number };
  let board: HTMLElement | undefined = $state();
  let drag = $state<{ ref: string; x: number; y: number; ox: number; oy: number; w: number } | null>(null);
  let zone = $state<Zone | null>(null);

  function grab(e: PointerEvent, ref: string) {
    const t = e.target as HTMLElement;
    if (e.button !== 0 || !t.closest("header") || t.closest("button, a, input, select, [role='button']")) return;
    const tile = e.currentTarget as HTMLElement;
    const r = tile.getBoundingClientRect();
    const sx = e.clientX;
    const sy = e.clientY;
    e.preventDefault();
    try {
      tile.setPointerCapture(e.pointerId);
    } catch {
      /* pointer already gone; the listeners below still end the drag */
    }
    const w = Math.min(r.width, 22 * rem());
    let started = false;
    const move = (ev: PointerEvent) => {
      if (!started) {
        if (Math.hypot(ev.clientX - sx, ev.clientY - sy) < 4) return;
        started = true;
        // Keep the point that was grabbed under the pointer.
        drag = { ref, x: sx, y: sy, ox: Math.min(sx - r.left, w - 12), oy: sy - r.top, w };
        document.documentElement.dataset.moving = "";
      }
      drag!.x = ev.clientX;
      drag!.y = ev.clientY;
      zone = hit(ev.clientX, ev.clientY, ref);
    };
    const end = (ev: Event) => {
      tile.removeEventListener("pointermove", move);
      tile.removeEventListener("pointerup", end);
      tile.removeEventListener("pointercancel", end);
      window.removeEventListener("keydown", esc, true);
      delete document.documentElement.dataset.moving;
      if (started && ev.type === "pointerup" && zone) {
        const z = zone;
        save({
          root: z.side === "centre" ? swapPanes(layout.root, ref, z.target!) : movePane(layout.root, ref, z.target, z.side),
        });
      }
      drag = null;
      zone = null;
    };
    const esc = (ev: KeyboardEvent) => {
      if (ev.key !== "Escape") return;
      ev.stopPropagation();
      zone = null;
      end(new Event("cancel"));
    };
    tile.addEventListener("pointermove", move);
    tile.addEventListener("pointerup", end);
    tile.addEventListener("pointercancel", end);
    window.addEventListener("keydown", esc, true);
  }

  /** Where a drop at (x, y) would land, as a box relative to the board. */
  function hit(x: number, y: number, self: string): Zone | null {
    if (!board) return null;
    const B = board.getBoundingClientRect();
    if (x < B.left || x > B.right || y < B.top || y > B.bottom) return null;
    const edge = 1.1 * rem();
    const bx = x - B.left;
    const by = y - B.top;
    const rootW = Math.max(B.width * 0.28, 16 * rem());
    const rootH = Math.max(B.height * 0.34, 9 * rem());
    // Along the board's outer edge: a full column or a full row.
    if (bx < edge) return { target: null, side: "left", l: 0, t: 0, w: rootW, h: B.height };
    if (B.width - bx < edge) return { target: null, side: "right", l: B.width - rootW, t: 0, w: rootW, h: B.height };
    if (by < edge) return { target: null, side: "top", l: 0, t: 0, w: B.width, h: rootH };
    if (B.height - by < edge) return { target: null, side: "bottom", l: 0, t: B.height - rootH, w: B.width, h: rootH };
    for (const el of board.querySelectorAll<HTMLElement>("[data-tile]")) {
      const r = el.getBoundingClientRect();
      if (x < r.left || x > r.right || y < r.top || y > r.bottom) continue;
      const target = el.dataset.tile!;
      if (target === self) return null;
      const nx = (x - r.left) / r.width;
      const ny = (y - r.top) / r.height;
      const l = r.left - B.left;
      const t = r.top - B.top;
      if (nx > 0.3 && nx < 0.7 && ny > 0.3 && ny < 0.7) return { target, side: "centre", l, t, w: r.width, h: r.height };
      const d = { left: nx, right: 1 - nx, top: ny, bottom: 1 - ny };
      const side = (Object.keys(d) as Side[]).reduce((a, b) => (d[b] < d[a] ? b : a));
      if (side === "left") return { target, side, l, t, w: r.width / 2, h: r.height };
      if (side === "right") return { target, side, l: l + r.width / 2, t, w: r.width / 2, h: r.height };
      if (side === "top") return { target, side, l, t, w: r.width, h: r.height / 2 };
      return { target, side, l, t: t + r.height / 2, w: r.width, h: r.height / 2 };
    }
    return null;
  }

  const dragged = $derived(drag ? panel(drag.ref) : null);

  // The widget's own menu lives in Frame (another builder's file), so the
  // board adds one on right-click of a header: minimise, open, remove.
  let menu = $state<{ ref: string; x: number; y: number } | null>(null);
  function context(e: MouseEvent, ref: string) {
    if (!(e.target as HTMLElement).closest("header")) return;
    e.preventDefault();
    menu = { ref, x: e.clientX, y: e.clientY };
  }

  // The "+ Widget" menu: this board's widgets and spares, then other boards'
  // widgets this one does not offer. A widget already here (by any route) is
  // marked, and a minimised one comes back from the menu too.
  const own = $derived(offered(place));
  const ownIds = $derived(new Set(own.map((p) => p.id)));
  const otherPlaces = $derived(
    shell.places
      .filter((p) => p.id !== place.id && p.kind === "board" && !p.foot)
      .map((p) => ({ place: p, panels: offered(p).filter((x) => !ownIds.has(x.id)) }))
      .filter((g) => g.panels.length),
  );
  const refFor = (id: string) => all.find((r) => panel(r)?.id === id);
  function where(id: string): "on" | "docked" | "off" {
    const r = refFor(id);
    return !r ? "off" : layout.docked.includes(r) ? "docked" : "on";
  }
  const offer = (from: string, id: string) => add(refFor(id) ?? refOf(from, id));
  // Widgets this board offers that are not on it: what a right-click can put
  // beside a widget, so one alone in its column or row gains an edge to drag.
  const spare = $derived(own.filter((p) => where(p.id) === "off"));
  function besides(target: string, id: string, side: Side) {
    const ref = refOf(place.id, id);
    save({ root: insertPane(layout.root, ref, target, side) });
    menu = null;
    added = ref;
    setTimeout(() => added === ref && (added = null), 900);
  }
</script>

<svelte:window
  onpointerdown={(e) => menu && !(e.target as HTMLElement).closest("[data-tile-menu]") && (menu = null)}
  onkeydown={(e) => e.key === "Escape" && menu && (menu = null)}
/>

{#snippet offerItem(from: string, p: Panel)}
  {@const w = where(p.id)}
  <Menu.Item disabled={w === "on"} onclick={() => offer(from, p.id)}>
    <Icon name={p.icon} />
    <span class="min-w-0 flex-1 truncate">{p.title}</span>
    {#if w !== "off"}
      <span class="text-muted-foreground text-xs">{w === "on" ? "on it" : "minimised"}</span>
    {:else if p.guest}
      <span class="text-muted-foreground text-xs">guest</span>
    {/if}
  </Menu.Item>
{/snippet}

{#snippet tile(ref: string)}
  {@const p = panel(ref)}
  {#if p}
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="tile relative flex min-h-0 min-w-0 flex-1 flex-col [&>section]:flex-1"
      data-tile={ref}
      data-lifted={drag?.ref === ref}
      data-added={added === ref}
      onpointerdown={(e) => grab(e, ref)}
      oncontextmenu={(e) => context(e, ref)}
    >
      <Frame panel={p} onexpand={() => shell.expand(p)} onminimise={() => minimise(ref)} onsend={() => shell.send(p.title)} />
      {#if tiles.arranging}
        <div class="bg-panel absolute top-px right-px flex h-11 items-center gap-1 rounded-tr-lg pr-1.5 pl-2">
          <button class="press text-down h-8 gap-1.5 px-2.5 text-sm" onclick={() => remove(ref)} aria-label="Remove {p.title} from the board">
            <Icon name="x" class="size-4" />Remove
          </button>
        </div>
      {/if}
    </div>
  {/if}
{/snippet}

{#snippet node(n: Node, path: number[])}
  {#if n.kind === "pane"}
    {@render tile(n.id)}
  {:else}
    {@const along = n.dir === "row" ? "w" : "h"}
    <div class="flex min-h-0 min-w-0 flex-1 {n.dir === 'row' ? 'flex-row' : 'flex-col'}">
      {#each n.children as c, k (keyOf(c))}
        {#if k > 0}
          <Splitter
            dir={n.dir === "row" ? "x" : "y"}
            a={n.sizes[k - 1]}
            b={n.sizes[k]}
            minA={minSize(n.children[k - 1], along, gapRem)}
            minB={minSize(c, along, gapRem)}
            onresize={(a, b) => resized(path, n, k, a, b)}
            onreset={() => evened(path, n, k)}
          />
        {/if}
        <div class="flex min-h-0 min-w-0" style:flex-grow={n.sizes[k]} style:flex-basis="0">
          {@render node(c, [...path, k])}
        </div>
      {/each}
    </div>
  {/if}
{/snippet}

<div class="tiles flex h-full min-h-0 flex-col" data-arranging={tiles.arranging || undefined}>
  <div class="relative flex min-h-0 flex-1" bind:this={board} bind:clientWidth={bw} bind:clientHeight={bh}>
    {#if visible}
      {@render node(visible, [])}
    {:else}
      <div class="text-muted-foreground grid flex-1 place-items-center text-center">
        {all.length ? "Every widget is minimised. Pick one below to bring it back." : "No widgets on this board. Add one below."}
      </div>
    {/if}
    {#if zone}
      <div class="drop pointer-events-none absolute z-20 flex items-start justify-center pt-3"style:left="{zone.l}px" style:top="{zone.t}px" style:width="{zone.w}px" style:height="{zone.h}px">
        <span class="bg-background rounded-md px-2.5 py-1 text-sm font-medium">
          {zone.side === "centre" ? "Swap" : zone.target ? "Place here" : zone.side === "left" || zone.side === "right" ? "Full height" : "Full width"}
        </span>
      </div>
    {/if}
  </div>

  <div class="mt-[var(--gap)] flex h-9 shrink-0 items-center gap-2">
    <div class="flex min-w-0 flex-1 items-center gap-2 overflow-hidden">
      {#if crowded.length}
        <span class="text-paper shrink-0 text-sm" title="The window is too small for every widget; these come back when it grows">No room</span>
        {#each crowded as ref (ref)}
          {@const p = panel(ref)!}
          <button class="press well h-8 max-w-56 min-w-0 shrink gap-2 px-3 text-sm" onclick={() => shell.expand(p)} title="Open {p.title} in a tab">
            <Icon name={p.icon} class="size-3.5 shrink-0" /><span class="truncate">{p.title}</span>
          </button>
        {/each}
      {/if}
      {#if docked.length}
        <span class="text-muted-foreground shrink-0 text-sm">Minimised</span>
        {#each docked as ref (ref)}
          {@const p = panel(ref)!}
          {@const fresh = shell.hasNew(bare(ref))}
          <button class="press well relative h-8 max-w-64 min-w-0 shrink gap-2 px-3 text-sm" onclick={() => restore(ref)} title="Restore {p.title}{fresh ? ' (something new)' : ''}">
            <Icon name={p.icon} class="size-3.5 shrink-0" />
            <span class="truncate">{p.title}</span>
            {#if fresh}
              <span class="dot text-foreground size-1.5" aria-label="Something new"></span>
            {/if}
          </button>
        {/each}
      {/if}
    </div>
    <Menu.Root>
      <Menu.Trigger>
        {#snippet child({ props })}
          <button {...props} class="press h-8 shrink-0 gap-1.5 px-2.5 text-sm whitespace-nowrap"><Icon name="plus" class="size-4" />Widget</button>
        {/snippet}
      </Menu.Trigger>
      <Menu.Content align="end" side="top" class="w-72">
        <Menu.Label>Add to {place.name}</Menu.Label>
        {#each own as p (p.id)}
          {@render offerItem(place.id, p)}
        {/each}
        {#each otherPlaces as g (g.place.id)}
          <Menu.Separator />
          <Menu.Label class="text-muted-foreground text-xs font-normal">From {g.place.name}</Menu.Label>
          {#each g.panels as p (p.id)}
            {@render offerItem(g.place.id, p)}
          {/each}
        {/each}
      </Menu.Content>
    </Menu.Root>
    <button class="press h-8 shrink-0 px-2.5 text-sm whitespace-nowrap" data-on={tiles.arranging} aria-pressed={tiles.arranging} onclick={() => (tiles.arranging = !tiles.arranging)}>
      {tiles.arranging ? "Done" : "Arrange"}
    </button>
    {#if tiles.isEdited(place.id)}
      <button class="press h-8 shrink-0 px-2.5 text-sm whitespace-nowrap" onclick={() => tiles.reset(place.id)} title="Back to this board's starting layout">Reset layout</button>
    {/if}
  </div>
</div>

{#if drag && dragged}
  <div class="ghost surface pointer-events-none fixed z-50 flex h-11 items-center gap-2 px-3" style:left="{drag.x - drag.ox}px" style:top="{drag.y - Math.min(drag.oy, 40)}px" style:width="{drag.w}px">
    <span class="text-muted-foreground shrink-0"><Icon name={dragged.icon} /></span>
    <span class="min-w-0 flex-1 truncate font-medium">{dragged.title}</span>
  </div>
{/if}

{#if menu}
  {@const p = panel(menu.ref)}
  {#if p}
    {@const ref = menu.ref}
    <div data-tile-menu class="surface menu fixed z-50 flex w-56 flex-col p-1 shadow-lg" style:left="{Math.min(menu.x, innerWidth - 232)}px" style:top="{Math.max(8, Math.min(menu.y, innerHeight - 150 - spare.length * 36 - 40))}px" role="menu">
      <button role="menuitem" class="press h-9 justify-start gap-2 px-2.5" onclick={() => (minimise(ref), (menu = null))}><Icon name="minus" />Minimise</button>
      <button role="menuitem" class="press h-9 justify-start gap-2 px-2.5" onclick={() => (shell.expand(p), (menu = null))}><Icon name="expand" />Open in a tab</button>
      <button role="menuitem" class="press text-down h-9 justify-start gap-2 px-2.5" onclick={() => (remove(ref), (menu = null))}><Icon name="x" />Remove from board</button>
      {#if spare.length}
        <p class="text-muted-foreground border-border mt-1 border-t px-2.5 pt-2 pb-1 text-xs">Put a widget beside this one</p>
        {#each spare as s (s.id)}
          <div class="flex items-center gap-1 px-1">
            <span class="flex min-w-0 flex-1 items-center gap-2 px-1.5 text-sm"><Icon name={s.icon} class="size-3.5 shrink-0" /><span class="truncate">{s.title}</span></span>
            <button role="menuitem" class="press size-8 shrink-0" title="Below" aria-label="Put {s.title} below" onclick={() => besides(ref, s.id, "bottom")}><Icon name="arrow-down" class="size-4" /></button>
            <button role="menuitem" class="press size-8 shrink-0" title="Right" aria-label="Put {s.title} to the right" onclick={() => besides(ref, s.id, "right")}><Icon name="arrow-right" class="size-4" /></button>
          </div>
        {/each}
      {/if}
    </div>
  {/if}
{/if}

<style>
  /* A widget is picked up by its header. */
  .tile :global(> section > header) {
    cursor: grab;
  }
  .tile :global(> section > header :is(button, a)) {
    cursor: pointer;
  }
  :global(html[data-moving] *) {
    cursor: grabbing !important;
    user-select: none;
  }
  /* The widget being moved stays in place, faded, so its old spot is clear. */
  .tile[data-lifted="true"] {
    opacity: 0.35;
  }
  .tile[data-added="true"] :global(> section) {
    animation: arrive 900ms ease-out;
  }
  @keyframes arrive {
    from {
      box-shadow: 0 0 0 2px color-mix(in oklch, var(--foreground) 80%, transparent);
    }
    to {
      box-shadow: 0 0 0 2px transparent;
    }
  }
  .menu {
    border-color: color-mix(in oklch, var(--foreground) 22%, var(--border));
    box-shadow: 0 12px 32px rgb(0 0 0 / 0.6);
  }
  .drop {
    border: 2px solid color-mix(in oklch, var(--foreground) 70%, transparent);
    border-radius: var(--radius);
    background: color-mix(in oklch, var(--foreground) 9%, transparent);
    transition:
      left 90ms ease-out,
      top 90ms ease-out,
      width 90ms ease-out,
      height 90ms ease-out;
  }
  .ghost {
    box-shadow: 0 12px 32px rgb(0 0 0 / 0.55);
    border-color: color-mix(in oklch, var(--foreground) 35%, var(--border));
  }
  /* Arrange mode: every handle shows its grip. */
  .tiles[data-arranging] :global(.splitter .grip) {
    opacity: 0.55;
  }
  @media (prefers-reduced-motion: reduce) {
    .drop {
      transition: none;
    }
  }
</style>
