<script lang="ts">
  /** How the Books move together (daily P&L). Above 0.7 is flagged: two Books doing the same thing. */
  import { CORR } from "../demo";

  const fill = (v: number) =>
    `color-mix(in oklab, ${v >= 0.7 ? "var(--destructive)" : "var(--primary)"} ${Math.round(Math.abs(v) * 70)}%, transparent)`;
</script>

<div class="flex h-full flex-col overflow-auto p-3">
  <div
    class="grid min-h-0 flex-1 gap-1"
    style="grid-template-columns: 6rem repeat({CORR.names
      .length}, minmax(0, 1fr)); grid-template-rows: 1.5rem repeat({CORR.names
      .length}, minmax(2rem, 1fr))"
  >
    <span></span>
    {#each CORR.names as n (n)}<span
        class="text-muted-foreground truncate text-center text-xs">{n}</span
      >{/each}
    {#each CORR.m as row, i (i)}
      <span class="text-muted-foreground self-center truncate text-xs"
        >{CORR.names[i]}</span
      >
      {#each row as v, j (j)}
        <span
          class="num flex items-center justify-center rounded text-xs"
          style="background:{i === j ? 'var(--muted)' : fill(v)}"
          >{i === j ? "" : v.toFixed(2)}</span
        >
      {/each}
    {/each}
  </div>
  <p class="text-muted-foreground mt-2 text-xs">
    Alt momentum and Weekly rotation move together (0.71): both lean on the same
    large alts.
  </p>
</div>
