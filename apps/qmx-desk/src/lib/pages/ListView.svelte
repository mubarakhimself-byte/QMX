<script lang="ts" module>
  // Each list keeps its filter while he visits pages and comes back.
  const filters = $state<Record<string, string>>({});
</script>

<script lang="ts">
  import { tick } from "svelte";
  import { things } from "$lib/shell/things.svelte";
  import { shell } from "$lib/shell/state.svelte";
  import { lists, type ListKind } from "$lib/shell/model";
  import Thing from "./Thing.svelte";
  import WideRow from "./WideRow.svelte";
  import Icon from "$lib/qmx/Icon.svelte";
  import IconButton from "$lib/qmx/IconButton.svelte";

  // A list of one kind of thing, grouped by state. Full width when it is
  // where he is; a narrow spine beside a page when he has opened one of its
  // things, so the list, its scroll and its filter stay where he left them.
  let { list, spine = false, current }: { list: ListKind; spine?: boolean; current?: string } = $props();

  const def = $derived(lists.find((l) => l.id === list)!);
  const pool = $derived(list === "needs" ? things.needs : things.all.filter((o) => def.kinds.includes(o.kind) && !o.target));
  const groups = $derived(def.groups.map(([name, f]) => ({ name, items: pool.filter(f) })).filter((g) => g.items.length));
  const filter = $derived(filters[list] ?? "All");
  const shown = $derived(filter === "All" ? groups : groups.filter((g) => g.name === filter));
  const flat = $derived(shown.flatMap((g) => g.items));
  const nf = new Intl.NumberFormat("en");

  let box: HTMLElement | undefined = $state();
  $effect(() => {
    void list;
    if (!box) return;
    const el = box;
    tick().then(() => {
      el.scrollTop = things.scrollOf(list);
      // Keep the open thing in view in the spine.
      if (spine && current) el.querySelector<HTMLElement>(`[data-id="${current}"]`)?.scrollIntoView({ block: "nearest" });
    });
  });

  // Up and down move between siblings while the spine has focus.
  function key(e: KeyboardEvent) {
    if (!spine || (e.key !== "ArrowDown" && e.key !== "ArrowUp")) return;
    const i = flat.findIndex((o) => (o.target ?? o.id) === current);
    const n = flat[Math.min(Math.max(i + (e.key === "ArrowDown" ? 1 : -1), 0), flat.length - 1)];
    if (!n) return;
    e.preventDefault();
    shell.open({ id: n.target ?? n.id, list });
    tick().then(() => box?.querySelector<HTMLElement>(`[data-id="${n.id}"]`)?.focus());
  }
</script>

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<section class="lv flex h-full min-h-0 min-w-0 flex-col" aria-label={def.name} onkeydown={key}>
  <header class="flex shrink-0 items-center gap-2 {spine ? 'h-12 pr-1 pl-3' : 'px-5 pt-4 pb-3'}">
    {#if spine}
      <Icon name={def.icon} class="text-muted-foreground size-4 shrink-0" />
      <h2 class="min-w-0 flex-1 truncate font-medium">{def.name}</h2>
      <span class="num text-muted-foreground text-sm">{nf.format(pool.length)}</span>
      <IconButton icon="expand" label="Back to the full list (Esc)" onclick={() => shell.back()} />
    {:else}
      <div class="min-w-0 flex-1">
        <h1 class="display flex items-baseline gap-3 text-3xl font-semibold">
          <span class="truncate">{def.name}</span>
          <span class="num text-muted-foreground text-xl font-normal">{nf.format(pool.length)}</span>
        </h1>
      </div>
    {/if}
  </header>

  {#if groups.length > 1 && !spine}
    <div class="flex shrink-0 flex-wrap gap-1.5 px-5 pb-3" role="group" aria-label="Show">
      {#each [{ name: "All", items: pool }, ...groups] as g (g.name)}
        <button class="key h-8 gap-2 px-3 text-sm" data-on={filter === g.name} onclick={() => (filters[list] = g.name)}>
          {g.name}<span class="num opacity-70">{nf.format(g.items.length)}</span>
        </button>
      {/each}
    </div>
  {/if}

  <div bind:this={box} class="min-h-0 flex-1 overflow-x-hidden overflow-y-auto {spine ? 'px-1.5 pb-2' : 'px-3 pb-4'}" onscroll={(e) => things.keepScroll(list, (e.currentTarget as HTMLElement).scrollTop)}>
    {#if !pool.length}
      <div class="flex h-full flex-col items-start justify-center gap-3 px-4 {spine ? '' : 'max-w-[36rem]'}">
        <p class="display text-2xl font-semibold">{def.empty[0]}</p>
        <p class="text-muted-foreground text-lg">{def.empty[1]}</p>
        <button class="press border-border h-10 gap-2 border px-4" onclick={() => dispatchEvent(new CustomEvent("qmx:find"))}>
          <Icon name="search" />Find or ask
        </button>
      </div>
    {:else}
      {#each shown as g (g.name)}
        <h3 class="text-muted-foreground sticky top-0 z-10 bg-[var(--surface-bg,var(--panel))] px-2.5 pt-3 pb-1 text-sm font-medium">
          {g.name} <span class="num opacity-70">{nf.format(g.items.length)}</span>
        </h3>
        <ul>
          {#each g.items as o (o.id)}
            <li>
              {#if spine}<Thing {o} {list} on={(o.target ?? o.id) === current} slim />{:else}<WideRow {o} {list} />{/if}
            </li>
          {/each}
        </ul>
      {/each}
    {/if}
  </div>
</section>

<style>
  .lv {
    container-type: inline-size;
  }
</style>
