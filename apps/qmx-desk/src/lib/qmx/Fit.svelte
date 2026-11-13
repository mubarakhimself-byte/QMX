<script lang="ts" generics="T">
  import type { Snippet } from "svelte";

  // The "next most useful thing" under a widget's main list (SPACE-RULES 7).
  // It takes whatever height is left and shows only the rows that fit whole:
  // never a half row, never a scrollbar. Its title goes first when room is
  // short (rows explain themselves), then a heading row that would end the
  // list; when not even one row fits, the block steps aside. A long main
  // list squeezes it to nothing; a short one lets it grow.
  let {
    items,
    title,
    row,
    key,
    onmore,
  }: {
    items: T[];
    title?: string;
    row: Snippet<[T]>;
    key: (x: T) => string;
    onmore?: () => void;
  } = $props();

  let root: HTMLElement | undefined = $state();
  let box: HTMLElement | undefined = $state();
  let head: HTMLElement | undefined = $state();
  let shown = $state(0);

  const isHead = (k: HTMLElement) => k.firstElementChild?.tagName === "H4";

  // Rows that fit whole in the list's current height; hides the rest.
  function count(kids: HTMLElement[]) {
    const H = box!.clientHeight;
    let n = 0;
    let open = true;
    let last: HTMLElement | null = null;
    for (const k of kids) {
      if (k.style.display === "none") continue;
      open = open && k.offsetTop + k.offsetHeight <= H + 0.5;
      k.style.visibility = open ? "" : "hidden";
      if (open) (n++, (last = k));
    }
    // A heading row never ends the list: with nothing under it, it goes too.
    const vis = kids.filter((k) => k.style.display !== "none" && k.style.visibility === "");
    while (vis.length && isHead(vis[vis.length - 1])) (vis.pop()!.style.visibility = "hidden"), n--;
    void last;
    return n;
  }

  function measure() {
    if (!box) return;
    const kids = [...box.children] as HTMLElement[];
    for (const k of kids) (k.style.display = ""), (k.style.marginTop = "");
    if (head) head.style.display = "";
    let n = count(kids);
    if (n === 0 && head) {
      head.style.display = "none";
      n = count(kids);
      if (n === 0) head.style.display = "";
    }
    if (n === 0) {
      const lead: HTMLElement[] = [];
      for (const k of kids) {
        if (!isHead(k)) break;
        k.style.display = "none";
        lead.push(k);
      }
      if (lead.length) {
        n = count(kids);
        if (n === 0) for (const k of lead) k.style.display = "";
      }
    }
    // What is left under the last whole row (less than a row) is shared out
    // between the rows, so no band of nothing sits at the foot.
    const vis = kids.filter((k) => k.style.display !== "none" && k.style.visibility === "");
    const last = vis[vis.length - 1];
    if (last && vis.length > 1) {
      const extra = box.clientHeight - (last.offsetTop + last.offsetHeight);
      if (extra > 0) for (const k of vis.slice(1)) k.style.marginTop = `${extra / (vis.length - 1)}px`;
    }
    shown = n;
  }
  $effect(() => {
    void items;
    if (!root) return;
    // Its own box and every row: rows change height when fonts load, the
    // text size changes or the widget changes mode.
    const ro = new ResizeObserver(() => measure());
    ro.observe(root);
    if (box) for (const k of box.children) ro.observe(k);
    measure();
    const t = setTimeout(measure, 0);
    document.fonts?.ready.then(measure);
    return () => (ro.disconnect(), clearTimeout(t));
  });
  const rest = $derived(items.length - shown);
</script>

<div class="fit flex min-h-0 flex-col" bind:this={root} style:visibility={shown ? undefined : "hidden"}>
  {#if title}
    <h4 bind:this={head} class="text-muted-foreground border-border/70 mx-2.5 mt-2 flex shrink-0 items-baseline gap-2 border-t pt-2 pb-1 text-sm font-medium">
      <span class="min-w-0 flex-1 truncate">{title}</span>
      {#if rest > 0 && onmore}
        <button class="hover:text-foreground num shrink-0" onclick={onmore}>+{rest} more</button>
      {:else if rest > 0}
        <span class="num shrink-0">+{rest}</span>
      {/if}
    </h4>
  {/if}
  <ul class="relative min-h-0 flex-1 overflow-hidden" bind:this={box}>
    {#each items as x (key(x))}<li>{@render row(x)}</li>{/each}
  </ul>
</div>

<style>
  /* The main list keeps its height and scrolls when long; this takes the rest. */
  .fit {
    flex: 1 1 0;
  }
</style>
