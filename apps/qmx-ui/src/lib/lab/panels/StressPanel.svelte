<script lang="ts">
  /** Stress board: crises down the side, pods across. Each cell: worst loss, how much of the room to the kill line it used, and which guard fired. */
  import { cn } from "$lib/utils";
  import { usd } from "$lib/portfolio/bits";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { LAB_PODS, STRESS, STRESS_GRID } from "../pods";
  import { lab } from "../lab.svelte";

  const pods = $derived(LAB_PODS.filter((p) => lab.podsTicked.includes(p.id)));
  const tone = (r: number) =>
    `color-mix(in oklab, ${r >= 0.75 ? "var(--destructive)" : r >= 0.4 ? "var(--warning)" : "var(--success)"} ${Math.round(14 + r * 30)}%, transparent)`;
</script>

<div class="h-full overflow-auto p-2">
  <div
    class="grid gap-1"
    style="grid-template-columns: 12rem repeat({pods.length}, minmax(10rem, 1fr))"
  >
    <span></span>
    {#each pods as p (p.id)}
      <span class="flex items-center gap-1.5 px-1 text-xs font-medium"
        ><span class="size-2 rounded-full" style="background:{p.color}"
        ></span>{p.name}</span
      >
    {/each}
    {#each STRESS as s (s.id)}
      <span class="self-center text-sm">{s.name}</span>
      {#each pods as p (p.id)}
        {@const c = STRESS_GRID[p.id]?.[s.id]}
        {#if c}
          <button
            type="button"
            class={cn(
              "rounded-md border px-2 py-1.5 text-left",
              c.stoodDown && "border-destructive",
            )}
            style="background:{tone(c.ofRoom)}"
            onclick={() =>
              workbench.notify(
                `Replay of ${s.name} under ${p.name} opens at the shock (needs the daemon).`,
              )}
          >
            <span class="flex items-baseline justify-between gap-2">
              <span class="num font-semibold">{usd(c.loss)}</span>
              <span class="num text-xs"
                >{Math.round(c.ofRoom * 100)}% of room</span
              >
            </span>
            <span
              class={cn(
                "block truncate text-[11px]",
                c.stoodDown ? "text-destructive" : "text-muted-foreground",
              )}>{c.stoodDown ? "Stood down: " : ""}{c.fired}</span
            >
          </button>
        {/if}
      {/each}
    {/each}
  </div>
</div>
