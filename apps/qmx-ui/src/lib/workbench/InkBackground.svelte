<script lang="ts">
  /**
   * Decorative art behind the workbench, drawn in the theme's ink colour
   * (--ink, --glow) from a small config (see art.ts). Purely visual; hidden
   * on trading surfaces so nothing competes with live prices. `inline` draws
   * it inside its parent instead, for previews.
   */
  import { W, H, buildScene, GLOW_X, type ArtConfig } from "./art";
  import { workbench } from "./workbench.svelte";
  import { cn } from "$lib/utils";

  let {
    config,
    inline = false,
    class: className,
  }: { config?: ArtConfig; inline?: boolean; class?: string } = $props();

  const uid = $props.id();
  const cfg = $derived(config ?? workbench.art);
  const scene = $derived(buildScene(cfg));
</script>

<svg
  class={cn(
    "pointer-events-none h-full w-full",
    inline ? "absolute inset-0" : "fixed inset-0 -z-10",
    className,
  )}
  viewBox="0 0 {W} {H}"
  preserveAspectRatio="xMidYMid slice"
  aria-hidden="true"
>
  <defs>
    <radialGradient id="{uid}-glow" cx={GLOW_X[cfg.glow]} cy="30%" r="60%">
      <stop offset="0" style="stop-color: var(--glow); stop-opacity: 0.5" />
      <stop offset="1" style="stop-color: var(--glow); stop-opacity: 0" />
    </radialGradient>
    <filter id="{uid}-wash" x="0" y="0" width="100%" height="100%">
      <feTurbulence
        type="fractalNoise"
        baseFrequency="0.006 0.012"
        numOctaves="4"
        seed={cfg.seed % 97}
      />
      <feColorMatrix
        type="matrix"
        values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.5 1.05"
      />
      <feComposite in="SourceGraphic" operator="in" />
    </filter>
    <filter id="{uid}-grain">
      <feTurbulence
        type="fractalNoise"
        baseFrequency="0.85"
        numOctaves="2"
        seed="3"
      />
      <feColorMatrix
        type="matrix"
        values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.05 0"
      />
    </filter>
  </defs>
  {#if cfg.glow !== "off"}
    <rect width={W} height={H} fill="url(#{uid}-glow)" />
  {/if}
  <rect
    width={W}
    height={H}
    style="fill: var(--ink); opacity: 0.16"
    filter="url(#{uid}-wash)"
  />
  <g style="opacity: {Math.min(1, cfg.strength)}">
    {#each scene.fills as f, i (i)}
      <path
        d={f.d}
        style="fill: var(--ink); opacity: {Math.min(
          1,
          f.o * Math.max(1, cfg.strength),
        )}"
      />
    {/each}
    {#each scene.strokes as s, i (i)}
      <path
        d={s.d}
        fill="none"
        style="stroke: var(--ink); opacity: {Math.min(
          1,
          s.o * Math.max(1, cfg.strength),
        )}"
        stroke-width={s.w}
        vector-effect={inline ? "non-scaling-stroke" : undefined}
      />
    {/each}
  </g>
  {#if !inline}
    <rect width={W} height={H} filter="url(#{uid}-grain)" />
  {/if}
</svg>
