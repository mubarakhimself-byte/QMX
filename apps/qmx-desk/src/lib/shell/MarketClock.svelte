<script lang="ts">
  import { clock, type City } from "$lib/qmx/clock.svelte";
  import SessionDetail from "./SessionDetail.svelte";

  // One market clock in the status bar. Hover to peek, click to keep it open.
  // The panel is the same session view as in "Markets today" (SessionDetail):
  // is it open, when in my own time, what of mine trades there, the pods on
  // it, what is scheduled, and where to read about it.
  let { city }: { city: City } = $props();

  const short: Record<string, string> = { tok: "TYO", lon: "LON", nyc: "NYC" };

  let open = $state(false);
  let pinned = $state(false);
  let timer: ReturnType<typeof setTimeout> | undefined;
  const show = () => (clearTimeout(timer), (open = true));
  const hide = () => {
    if (pinned) return;
    clearTimeout(timer);
    timer = setTimeout(() => (open = false), 160);
  };
  const close = () => ((pinned = false), (open = false));

  const isOpen = $derived(clock.isOpen(city));

  // The panel sits above its clock but never past the window's edges, so
  // opening it never shifts the page sideways (big text, long names).
  let btn: HTMLElement | undefined = $state();
  let pos = $state({ left: 0, bottom: 0 });
  const W = 24; // rem
  const place = () => {
    if (!btn) return;
    const r = btn.getBoundingClientRect();
    const px = W * parseFloat(getComputedStyle(document.documentElement).fontSize);
    const left = Math.min(Math.max(8, r.left + r.width / 2 - px / 2), window.innerWidth - px - 8);
    pos = { left, bottom: window.innerHeight - r.top + 8 };
  };
  $effect(() => {
    if (!open) return;
    place();
    window.addEventListener("resize", place);
    return () => window.removeEventListener("resize", place);
  });
  $effect(() => {
    if (!open) return;
    const onkey = (e: KeyboardEvent) => e.key === "Escape" && close();
    window.addEventListener("keydown", onkey);
    return () => window.removeEventListener("keydown", onkey);
  });
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="relative" onmouseenter={show} onmouseleave={hide}>
  <button
    bind:this={btn}
    class="press h-7 gap-1.5 px-2 whitespace-nowrap"
    data-on={pinned}
    aria-expanded={open}
    aria-label="{city.name} market, {isOpen ? 'open' : 'closed'}, {clock.time(city.zone)}"
    onclick={() => (pinned ? close() : ((pinned = true), show()))}
  >
    <span class="dot size-1.5 {isOpen ? 'text-up' : 'text-idle'}"></span>
    <span class="clk-full">{city.name}</span><span class="clk-short hidden">{short[city.id] ?? city.name}</span>
    <span class="num text-foreground">{clock.time(city.zone)}</span>
  </button>

  {#if open}
    <div class="bg-popover border-border text-foreground fixed z-50 max-h-[calc(100vh-6rem)] w-[24rem] max-w-[calc(100vw-1rem)] overflow-x-hidden overflow-y-auto rounded-lg border p-3 shadow-2xl shadow-black" style:left="{pos.left}px" style:bottom="{pos.bottom}px" role="dialog" aria-label="{city.name} market">
      <SessionDetail {city} onleave={close} />
    </div>
  {/if}
</div>
