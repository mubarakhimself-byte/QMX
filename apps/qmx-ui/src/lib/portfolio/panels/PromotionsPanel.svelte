<script lang="ts">
  /**
   * The road to live in three lanes: research-paper (QMB replay), node-paper
   * (demo account soak) and live. Promotion and activation are separate
   * clicks; activation takes effect at the next day boundary (DEC-0261).
   * Bots, models and Books all travel the same road.
   */
  import Bot from "@lucide/svelte/icons/bot";
  import BrainCircuit from "@lucide/svelte/icons/brain-circuit";
  import BookOpen from "@lucide/svelte/icons/book-open";
  import { cn } from "$lib/utils";
  import { PROMOTIONS } from "../demo";
  import { portfolio } from "../portfolio.svelte";

  const LANES = [
    {
      id: "research-paper",
      label: "Research-paper",
      note: "Proven on replay in the Lab",
    },
    {
      id: "node-paper",
      label: "Node-paper",
      note: "Soaking on a demo account",
    },
    { id: "live", label: "Live", note: "Signed; activation pending or done" },
  ] as const;
  const ICON = { bot: Bot, model: BrainCircuit, book: BookOpen };
</script>

<div class="grid h-full grid-cols-3 gap-2 overflow-auto p-2">
  {#each LANES as lane (lane.id)}
    <section
      class="bg-muted/30 flex min-h-0 flex-col gap-2 rounded-lg p-2"
      aria-label={lane.label}
    >
      <header class="px-1">
        <h4 class="text-sm font-medium">{lane.label}</h4>
        <p class="text-muted-foreground text-xs">{lane.note}</p>
      </header>
      {#each PROMOTIONS.filter((p) => p.stage === lane.id) as p (p.id)}
        {@const Icon = ICON[p.kind]}
        {@const passed = p.gates.filter((g) => g.ok).length}
        <button
          type="button"
          class={cn(
            "tile hover:border-ring/60 flex flex-col gap-1.5 rounded-lg p-2.5 text-left",
            portfolio.promotion === p.id && "border-ring ring-ring ring-1",
          )}
          onclick={() => (portfolio.promotion = p.id)}
        >
          <span class="flex items-center gap-2 text-sm font-medium"
            ><Icon class="text-muted-foreground size-4" />{p.what}</span
          >
          <span class="text-muted-foreground text-xs">{p.detail}</span>
          <span class="flex items-center gap-1">
            {#each p.gates as g (g.name)}
              <span
                class={cn(
                  "h-1.5 flex-1 rounded-full",
                  g.ok === true
                    ? "bg-success"
                    : g.ok === false
                      ? "bg-destructive"
                      : "bg-muted-foreground/30",
                )}
                title={g.name}
              ></span>
            {/each}
          </span>
          <span class="text-muted-foreground text-[11px]"
            >{passed} of {p.gates.length} checks passed</span
          >
        </button>
      {/each}
    </section>
  {/each}
</div>
