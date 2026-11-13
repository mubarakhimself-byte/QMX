<script lang="ts">
  import type { Panel } from "$lib/shell/data";
  import { shell } from "$lib/shell/state.svelte";
  import { things } from "$lib/shell/things.svelte";
  import { guestInk, guestWash } from "$lib/shell/model";
  import Icon from "./Icon.svelte";
  import IconButton from "./IconButton.svelte";
  import Rows from "./Rows.svelte";
  import DataTable from "./DataTable.svelte";
  import Stats from "./Stats.svelte";
  import Spark from "./Spark.svelte";
  import Jobs from "./Jobs.svelte";
  import CardBody from "./CardBody.svelte";
  import { tone } from "./state";
  import { providePanelSize, sizeMode } from "./tiles/panel-size";

  // The one frame every widget lives in: built-in cards, mini-app cards and
  // blocks pinned from a chat all get the same header and the same three
  // actions. A card's rows open his things' pages; "All" opens its list.
  let {
    panel,
    full = false,
    onexpand,
    onminimise,
    onsend,
  }: {
    panel: Panel;
    full?: boolean;
    onexpand?: () => void;
    onminimise?: () => void;
    onsend?: () => void;
  } = $props();

  // A unit card takes its name and state from the unit itself.
  const unit = $derived(panel.kind === "card" && panel.id.startsWith("t:") ? things.get(panel.id.slice(2)) : undefined);
  const g = $derived(panel.guest ? things.guest(panel.guest) : undefined);
  const mode = $derived(unit ? (unit.tone === "live" ? "live" : unit.tone === "paper" ? "paper" : undefined) : panel.mode);
  const line = $derived(mode === "live" ? "var(--live)" : mode === "paper" ? "var(--paper)" : undefined);
  const title = $derived(unit?.name ?? panel.title);
  const all: Record<string, string> = { waiting: "needs", units: "units", running: "runs" };
  const more = $derived(panel.kind === "card" && !full ? all[panel.id] : undefined);

  // Every frame measures its body and tells the widget inside how big it
  // is (compact, regular, expanded), as the October tiles did. In its own
  // tab a widget is always expanded.
  let bodyEl: HTMLElement | undefined = $state();
  let box = $state({ width: 0, height: 0, rem: 17 });
  $effect(() => {
    if (!bodyEl) return;
    const el = bodyEl;
    const read = () => (box = { width: el.clientWidth, height: el.clientHeight, rem: parseFloat(getComputedStyle(document.documentElement).fontSize) || 17 });
    const ro = new ResizeObserver(read);
    ro.observe(el);
    ro.observe(document.documentElement);
    read();
    return () => ro.disconnect();
  });
  const size = $derived(sizeMode(box, box.rem, full));
  providePanelSize({
    get mode() {
      return size;
    },
    get width() {
      return box.width;
    },
    get height() {
      return box.height;
    },
  });
</script>

<section
  class="frame surface group/frame flex min-h-0 min-w-0 flex-col overflow-hidden {g ? 'border-dashed' : ''}"
  style:--line={line}
  style:border-color={g ? guestInk(g.hue) : line ? `color-mix(in oklch, ${line} 55%, var(--border))` : undefined}
  aria-label={title}
  data-size={size}
>
  <header class="relative flex h-11 shrink-0 items-center gap-2 pr-1.5 pl-3">
    <span class="shrink-0 {unit ? tone[unit.tone] : 'text-muted-foreground'}" style:color={g ? guestInk(g.hue) : undefined}><Icon name={panel.icon} /></span>
    {#if unit}
      <button class="min-w-[4rem] flex-1 truncate text-left font-medium hover:underline" title="Open {unit.name}" onclick={() => shell.open({ id: unit.id })}>{title}</button>
    {:else}
      <h3 class="min-w-[4rem] flex-1 truncate font-medium" title={title}>{title}</h3>
    {/if}
    {#if unit && !mode}
      <span class="shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold tracking-wide whitespace-nowrap uppercase {tone[unit.tone]}" style:background="color-mix(in oklch, currentColor 15%, transparent)">{unit.word}</span>
    {:else if mode}
      <span
        class="shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold tracking-wide whitespace-nowrap uppercase"
        style:color={line}
        style:background="color-mix(in oklch, {line} 16%, transparent)"
      >
        {unit?.word === "paused" ? "paused" : mode}
      </span>
    {/if}
    {#if g}
      <span class="flex min-w-0 shrink items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold" style:color={guestInk(g.hue)} style:background={guestWash(g.hue)} title="From the mini app {g.name}">
        <Icon name="puzzle" class="size-3 shrink-0" /><span class="truncate">{g.name}</span>
      </span>
    {/if}
    {#if more}
      <button class="press h-7 shrink-0 gap-1 px-2 text-sm" title="Open the whole list" aria-label="All" onclick={() => shell.go(more)}><span class="all">All</span><Icon name="arrow-right" class="size-3.5" /></button>
    {/if}
    {#if !full}
      <div class="acts flex shrink-0 items-center opacity-60 transition-opacity duration-150 group-focus-within/frame:opacity-100 group-hover/frame:opacity-100">
        <IconButton icon="send" label="Send to the copilot" size="size-7" onclick={onsend} />
        <IconButton icon="minus" label="Minimise" size="size-7" onclick={onminimise} />
        <IconButton icon="expand" label="Open in a tab" size="size-7" onclick={onexpand} />
      </div>
    {/if}
  </header>
  <div class="min-h-0 flex-1 overflow-x-hidden px-1.5 pb-1.5 {panel.kind === 'card' ? 'overflow-y-hidden' : 'overflow-y-auto'}" data-body bind:this={bodyEl}>
    {#if panel.kind === "card"}
      <CardBody id={panel.id} />
    {:else if panel.kind === "list" && panel.rows}
      <Rows rows={panel.rows} />
    {:else if panel.kind === "table" && panel.cols && panel.table}
      <DataTable cols={panel.cols} rows={panel.table} />
    {:else if panel.kind === "stats" && panel.stats}
      <Stats stats={panel.stats} big={full} />
    {:else if panel.kind === "chart" && panel.series}
      <Spark series={panel.series} note={panel.note} />
    {:else if panel.kind === "jobs" && panel.jobs}
      <Jobs jobs={panel.jobs} rows={panel.rows} />
    {/if}
  </div>
</section>

<style>
  .frame {
    container-type: inline-size;
  }
  /* A narrow widget keeps its title: the three actions float in on hover
     or focus instead of taking the header's room, and "All" keeps its arrow. */
  @container (max-width: 24rem) {
    .all {
      display: none;
    }
    .acts {
      position: absolute;
      top: 0.5rem;
      right: 0.375rem;
      background: var(--panel);
      border-radius: 0.375rem;
      box-shadow: -0.75rem 0 0.75rem var(--panel);
      opacity: 0;
      pointer-events: none;
    }
    .frame:hover .acts,
    .frame:focus-within .acts {
      opacity: 1;
      pointer-events: auto;
    }
  }
</style>
