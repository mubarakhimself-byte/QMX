<script lang="ts">
  /**
   * Scrolling price strip. Pauses on hover and for reduced motion. Prices
   * come from the daemon's market stream; the demo passes samples.
   */
  let {
    items,
    label = "Prices",
  }: { items: { sym: string; px: string; chg: number }[]; label?: string } =
    $props();
</script>

<div
  class="group bg-panel relative flex h-8 items-center overflow-hidden border-b"
  role="marquee"
  aria-label={label}
>
  <div
    class="ticker-track flex shrink-0 gap-8 pr-8 group-hover:[animation-play-state:paused]"
  >
    {#each [...items, ...items] as t, i (i)}
      <span
        class="flex items-center gap-2 text-[13px] whitespace-nowrap"
        aria-hidden={i >= items.length}
      >
        <span class="font-medium">{t.sym}</span>
        <span class="num">{t.px}</span>
        <span class="num {t.chg >= 0 ? 'text-success' : 'text-destructive'}"
          >{t.chg >= 0 ? "▲ +" : "▼ −"}{Math.abs(t.chg).toFixed(2)}%</span
        >
      </span>
    {/each}
  </div>
</div>

<style>
  .ticker-track {
    animation: ticker 60s linear infinite;
  }
  @keyframes ticker {
    from {
      transform: translateX(0);
    }
    to {
      transform: translateX(-50%);
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .ticker-track {
      animation: none;
    }
  }
</style>
