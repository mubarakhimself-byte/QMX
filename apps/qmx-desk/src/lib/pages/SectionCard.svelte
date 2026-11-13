<script lang="ts">
  import Icon from "$lib/qmx/Icon.svelte";
  import IconButton from "$lib/qmx/IconButton.svelte";
  import Body from "./Body.svelte";
  import { things } from "$lib/shell/things.svelte";
  import { shell } from "$lib/shell/state.svelte";
  import { guestInk, guestWash, type Section } from "$lib/shell/model";

  // One section of a thing's page. Built-in and guest sections share the
  // frame; a guest keeps its app's colour on a dashed edge and its name.
  let {
    s,
    onopen,
    edit,
  }: {
    s: Section;
    onopen?: () => void;
    edit?: { up?: () => void; down?: () => void; remove: () => void };
  } = $props();
  const g = $derived(s.guest ? things.guest(s.guest) : undefined);
</script>

<section
  class="surface flex min-h-0 min-w-0 flex-col overflow-hidden {s.wide ? 'wide' : ''} {g ? 'border-dashed' : ''}"
  style:border-color={g ? guestInk(g.hue) : undefined}
  style:background={g ? `linear-gradient(${guestWash(g.hue)}, transparent 40%), var(--panel)` : undefined}
  aria-label={s.title}
>
  <header class="flex h-11 shrink-0 items-center gap-2 pr-1.5 pl-3">
    <span class="text-muted-foreground shrink-0" style:color={g ? guestInk(g.hue) : undefined}><Icon name={s.icon} /></span>
    <h3 class="min-w-0 flex-1 truncate font-medium" title={s.title}>{s.title}</h3>
    {#if g}
      <span class="flex min-w-0 shrink items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold" style:color={guestInk(g.hue)} style:background={guestWash(g.hue)} title="Added by the mini app {g.name}">
        <Icon name="puzzle" class="size-3 shrink-0" /><span class="truncate">{g.name}</span>
      </span>
    {/if}
    {#if edit}
      <div class="flex shrink-0 items-center">
        <button class="press size-8 disabled:opacity-30" aria-label="Move up" title="Move up" disabled={!edit.up} onclick={edit.up}><Icon name="arrow-up-1" /></button>
        <button class="press size-8 disabled:opacity-30" aria-label="Move down" title="Move down" disabled={!edit.down} onclick={edit.down}><Icon name="arrow-down" /></button>
        <IconButton icon="x" label="Remove from the page" size="size-8" onclick={edit.remove} />
      </div>
    {:else if onopen}
      <button class="press h-8 shrink-0 gap-1 px-2 text-sm" onclick={onopen}>Open<Icon name="out" class="size-3.5" /></button>
    {/if}
  </header>
  <div class="min-h-0 flex-1 overflow-x-hidden overflow-y-auto px-1.5 pb-1.5 {edit ? 'pointer-events-none opacity-60' : ''}">
    <Body body={s.body} />
  </div>
</section>
