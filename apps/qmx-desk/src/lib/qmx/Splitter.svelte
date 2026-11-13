<script lang="ts">
  // The handle between two widgets. Sizes are shares, so the board still
  // fills. It tracks the pointer 1:1 from where it was grabbed and never
  // animates. The grab area is wider than the gap; a grip shows on hover,
  // faintly whenever the pointer is over the board. Double-click resets.
  let {
    dir,
    a,
    b,
    minA,
    minB,
    onresize,
    onreset,
  }: {
    dir: "x" | "y";
    a: number;
    b: number;
    /** Smallest each side may get, in rem (a nested stack needs more than one widget). */
    minA?: number;
    minB?: number;
    onresize: (a: number, b: number) => void;
    onreset?: () => void;
  } = $props();

  let el: HTMLElement | undefined = $state();
  let dragging = $state(false);

  function down(e: PointerEvent) {
    if (!el || e.button !== 0) return;
    const prev = el.previousElementSibling as HTMLElement | null;
    const next = el.nextElementSibling as HTMLElement | null;
    if (!prev || !next) return;
    e.preventDefault();
    el.setPointerCapture(e.pointerId);
    dragging = true;
    const rem = parseFloat(getComputedStyle(document.documentElement).fontSize) || 17;
    const start = dir === "x" ? e.clientX : e.clientY;
    const pa = dir === "x" ? prev.getBoundingClientRect().width : prev.getBoundingClientRect().height;
    const pb = dir === "x" ? next.getBoundingClientRect().width : next.getBoundingClientRect().height;
    const total = a + b;
    // Smallest a widget may get: room for its header and a few lines.
    const base = dir === "x" ? 14 : 6.5;
    let lo = (minA ?? base) * rem;
    let hi = pa + pb - (minB ?? base) * rem;
    // Already tighter than both minimums (big text, small window): still let
    // the edge move, keeping each side at least a quarter of the pair.
    if (lo > hi) [lo, hi] = [(pa + pb) * 0.25, (pa + pb) * 0.75];
    document.documentElement.dataset.resizing = dir;
    const move = (ev: PointerEvent) => {
      const d = (dir === "x" ? ev.clientX : ev.clientY) - start;
      const na = Math.min(Math.max(pa + d, lo), hi);
      onresize((na / (pa + pb)) * total, ((pa + pb - na) / (pa + pb)) * total);
    };
    const up = () => {
      dragging = false;
      delete document.documentElement.dataset.resizing;
      el?.removeEventListener("pointermove", move);
      el?.removeEventListener("pointerup", up);
      el?.removeEventListener("pointercancel", up);
    };
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerup", up);
    el.addEventListener("pointercancel", up);
  }
  // Keyboard: arrows move the split by a small step; Enter resets.
  function key(e: KeyboardEvent) {
    if (e.key === "Enter" && onreset) return (e.preventDefault(), onreset());
    const step = e.key === (dir === "x" ? "ArrowRight" : "ArrowDown") ? 0.06 : e.key === (dir === "x" ? "ArrowLeft" : "ArrowUp") ? -0.06 : 0;
    if (!step) return;
    e.preventDefault();
    const total = a + b;
    const na = Math.min(Math.max(a + step * total, total * 0.15), total * 0.85);
    onresize(na, total - na);
  }
</script>

<!-- A focusable separator is the standard pattern for a splitter. -->
<!-- svelte-ignore a11y_no_noninteractive_tabindex, a11y_no_noninteractive_element_interactions -->
<div
  bind:this={el}
  role="separator"
  tabindex="0"
  aria-orientation={dir === "x" ? "vertical" : "horizontal"}
  aria-label={dir === "x" ? "Drag to change widths, double-click to reset" : "Drag to change heights, double-click to reset"}
  title={dir === "x" ? "Drag to resize · double-click to reset" : "Drag to resize · double-click to reset"}
  class="splitter relative z-10 shrink-0 touch-none select-none {dir === 'x' ? 'w-[var(--gap)] cursor-col-resize' : 'h-[var(--gap)] cursor-row-resize'}"
  data-dir={dir}
  data-dragging={dragging}
  onpointerdown={down}
  ondblclick={() => onreset?.()}
  onkeydown={key}
>
  <span class="line" aria-hidden="true"></span>
  <span class="grip" aria-hidden="true"></span>
</div>

<style>
  /* While a split is dragged the cursor stays a resize cursor everywhere and
     no text gets selected, even when the pointer runs ahead over a widget. */
  :global(html[data-resizing="x"] *) {
    cursor: col-resize !important;
    user-select: none;
  }
  :global(html[data-resizing="y"] *) {
    cursor: row-resize !important;
    user-select: none;
  }
  /* A grab area 22px wide, centred on the 10px gap. */
  .splitter::before {
    content: "";
    position: absolute;
    inset: 0 -6px;
  }
  .splitter[data-dir="y"]::before {
    inset: -6px 0;
  }
  .line,
  .grip {
    position: absolute;
    border-radius: 99px;
    background: var(--foreground);
    opacity: 0;
    pointer-events: none;
    transition: opacity 120ms ease-out;
  }
  [data-dir="x"] .line {
    inset: 0.5rem auto;
    left: 50%;
    width: 2px;
    translate: -50% 0;
  }
  [data-dir="y"] .line {
    inset: auto 0.5rem;
    top: 50%;
    height: 2px;
    translate: 0 -50%;
  }
  [data-dir="x"] .grip {
    top: 50%;
    left: 50%;
    width: 4px;
    height: 2.5rem;
    translate: -50% -50%;
  }
  [data-dir="y"] .grip {
    top: 50%;
    left: 50%;
    width: 2.5rem;
    height: 4px;
    translate: -50% -50%;
  }
  :global(.board:hover) .grip {
    opacity: 0.18;
  }
  .splitter:hover .grip,
  .splitter:focus-visible .grip {
    opacity: 0.7;
  }
  .splitter:hover .line,
  .splitter:focus-visible .line {
    opacity: 0.45;
  }
  .splitter[data-dragging="true"] .line {
    opacity: 1;
    transition: none;
  }
  .splitter[data-dragging="true"] .grip {
    opacity: 0;
  }
</style>
