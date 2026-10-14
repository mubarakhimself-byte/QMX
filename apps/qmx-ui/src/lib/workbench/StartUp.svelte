<script lang="ts">
  /**
   * The start-up moment: QMX appears, a price line draws itself under it,
   * then the screen opens onto the workbench while the ink art fades in.
   * Once per browser session, about 1.6 s, never blocks clicks, and skipped
   * entirely when the system asks for reduced motion.
   */
  import { onMount } from "svelte";

  const KEY = "qmx.startup.seen";
  let show = $state(false);
  let leaving = $state(false);

  onMount(() => {
    let seen = true;
    try {
      seen = sessionStorage.getItem(KEY) === "1";
      sessionStorage.setItem(KEY, "1");
    } catch {
      /* storage unavailable: treat as seen */
    }
    if (seen || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    show = true;
    const out = setTimeout(() => (leaving = true), 1250);
    const gone = setTimeout(() => (show = false), 1750);
    return () => {
      clearTimeout(out);
      clearTimeout(gone);
    };
  });

  const LETTERS = ["Q", "M", "X"];
</script>

{#if show}
  <div
    class="startup bg-background pointer-events-none fixed inset-0 z-[100] flex flex-col items-center justify-center gap-5"
    class:leaving
    aria-hidden="true"
  >
    <div class="flex gap-[0.08em] text-7xl font-semibold tracking-tight">
      {#each LETTERS as l, i (l)}
        <span class="letter" style="animation-delay: {i * 110}ms">{l}</span>
      {/each}
    </div>
    <svg viewBox="0 0 240 40" class="h-8 w-60 overflow-visible">
      <path
        class="pulse"
        d="M0 30 L28 26 L44 31 L66 18 L84 22 L104 9 L122 16 L142 12 L160 24 L178 15 L198 19 L216 6 L240 10"
        fill="none"
        stroke="var(--primary)"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
  </div>
{/if}

<style>
  .letter {
    display: inline-block;
    opacity: 0;
    animation: rise 520ms cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
  }
  .pulse {
    stroke-dasharray: 320;
    stroke-dashoffset: 320;
    animation: draw 900ms 260ms cubic-bezier(0.6, 0, 0.2, 1) forwards;
  }
  .startup {
    transition:
      opacity 480ms ease,
      transform 480ms ease;
  }
  .startup.leaving {
    opacity: 0;
    transform: scale(1.03);
  }
  @keyframes rise {
    from {
      opacity: 0;
      transform: translateY(0.35em);
      filter: blur(6px);
    }
    to {
      opacity: 1;
      transform: none;
      filter: none;
    }
  }
  @keyframes draw {
    to {
      stroke-dashoffset: 0;
    }
  }
</style>
