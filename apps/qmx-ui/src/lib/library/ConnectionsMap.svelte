<script lang="ts">
  /**
   * Where an item is used, as a picture: the item in the middle, the five
   * parts of QMX around it, a solid line where it is used and a faint one
   * where it is not. Click a part to list only those uses.
   */
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import BriefcaseBusiness from "@lucide/svelte/icons/briefcase-business";
  import MessagesSquare from "@lucide/svelte/icons/messages-square";
  import House from "@lucide/svelte/icons/house";
  import AppWindow from "@lucide/svelte/icons/app-window";
  import { cn } from "$lib/utils";
  import { PLACES, type Place, type Use } from "./items";

  let {
    uses,
    color,
    filter = $bindable(null),
  }: { uses: Use[]; color: string; filter?: Place | null } = $props();

  // Positions in percent of the map box.
  const AT: Record<Place, { x: number; y: number }> = {
    Lab: { x: 16, y: 18 },
    Portfolio: { x: 84, y: 18 },
    Copilot: { x: 12, y: 80 },
    Home: { x: 88, y: 80 },
    "Mini apps": { x: 50, y: 92 },
  };
  const ICON = {
    Lab: FlaskConical,
    Portfolio: BriefcaseBusiness,
    Copilot: MessagesSquare,
    Home: House,
    "Mini apps": AppWindow,
  };
  const count = (p: Place) => uses.filter((u) => u.place === p).length;
</script>

<div class="relative h-44 w-full" role="group" aria-label="Where it is used">
  <svg
    class="absolute inset-0 h-full w-full"
    viewBox="0 0 100 100"
    preserveAspectRatio="none"
    aria-hidden="true"
  >
    {#each PLACES as p (p)}
      <line
        x1="50"
        y1="45"
        x2={AT[p].x}
        y2={AT[p].y}
        stroke={count(p) ? color : "var(--border)"}
        stroke-width={count(p) ? 2 : 1}
        stroke-dasharray={count(p) ? "" : "3 3"}
        vector-effect="non-scaling-stroke"
        opacity={filter && filter !== p ? 0.3 : 1}
      />
    {/each}
  </svg>
  <span
    class="absolute flex size-12 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full text-xs font-semibold text-white shadow-md"
    style="left:50%; top:45%; background:{color}">{uses.length}</span
  >
  {#each PLACES as p (p)}
    {@const Icon = ICON[p]}
    {@const n = count(p)}
    <button
      type="button"
      class={cn(
        "bg-background absolute flex -translate-x-1/2 -translate-y-1/2 items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs whitespace-nowrap",
        n ? "text-foreground" : "text-muted-foreground/70",
        filter === p && "ring-primary ring-2",
      )}
      style="left:{AT[p].x}%; top:{AT[p].y}%"
      aria-pressed={filter === p}
      disabled={!n}
      onclick={() => (filter = filter === p ? null : p)}
      ><Icon class="size-3.5" />{p}{#if n}<span class="num font-semibold"
          >{n}</span
        >{/if}</button
    >
  {/each}
</div>
