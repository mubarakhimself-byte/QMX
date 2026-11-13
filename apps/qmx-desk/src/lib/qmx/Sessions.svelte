<script lang="ts">
  import { cities, clock } from "./clock.svelte";

  // The trading day on one line per market: when each is open, in your own
  // time, with one violet "now" line through all of them. In a narrow card
  // the name and clock sit above the bar, so the bar keeps its width.
  // With onpick, each session is a button that opens what trades in it.
  let { onpick }: { onpick?: (id: string) => void } = $props();
  const pct = (min: number) => `${(min / 1440) * 100}%`;
  const hours = [0, 6, 12, 18];
</script>

<div class="ses" aria-label="Market sessions today, in your time">
  <div class="flex flex-col gap-2.5">
    {#each cities as c (c.id)}
      {@const [a, b] = clock.localSpan(c)}
      {@const open = clock.isOpen(c)}
      <svelte:element this={onpick ? "button" : "div"} class="row {onpick ? 'pick w-full rounded-md px-1 py-0.5 text-left' : ''} items-center gap-x-3 gap-y-1" title={onpick ? `What trades in ${c.name}` : undefined} onclick={onpick ? () => onpick(c.id) : undefined} role={onpick ? undefined : "group"}>
        <span class="nm flex min-w-0 items-center gap-2 font-medium">
          <span class="dot size-1.5 {open ? 'text-up' : 'text-idle'}"></span><span class="truncate">{c.name}</span>
        </span>
        <span class="bar well relative block h-7 overflow-hidden">
          {#if a < b}
            <span class="absolute inset-y-0 rounded-sm {open ? 'bg-foreground' : 'bg-foreground/25'}" style:left={pct(a)} style:width={pct(b - a)}></span>
          {:else}
            <span class="absolute inset-y-0 left-0 rounded-sm {open ? 'bg-foreground' : 'bg-foreground/25'}" style:width={pct(b)}></span>
            <span class="absolute inset-y-0 right-0 rounded-sm {open ? 'bg-foreground' : 'bg-foreground/25'}" style:width={pct(1440 - a)}></span>
          {/if}
          <span class="bg-needs absolute inset-y-0 w-0.5" style:left={pct(clock.localMinutes)} title="Now"></span>
        </span>
        <span class="tm num text-muted-foreground text-right text-sm">{clock.time(c.zone)}</span>
      </svelte:element>
    {/each}
    <div class="row gap-x-3 {onpick ? 'px-1' : ''}">
      <span class="nm text-muted-foreground text-sm">Your time</span>
      <div class="bar num text-muted-foreground relative h-4 text-xs">
        {#each hours as h (h)}
          <span class="absolute {h === 0 ? '' : '-translate-x-1/2'}" style:left={pct(h * 60)}>{String(h).padStart(2, "0")}</span>
        {/each}
      </div>
      <span class="tm"></span>
    </div>
  </div>
</div>

<style>
  .ses {
    container-type: inline-size;
  }
  .row {
    display: grid;
    grid-template-columns: 7rem minmax(0, 1fr) 3.5rem;
    grid-template-areas: "nm bar tm";
  }
  .nm {
    grid-area: nm;
  }
  .bar {
    grid-area: bar;
  }
  .tm {
    grid-area: tm;
  }
  @container (max-width: 24rem) {
    .row {
      grid-template-columns: minmax(0, 1fr) auto;
      grid-template-areas: "nm tm" "bar bar";
    }
  }
</style>
