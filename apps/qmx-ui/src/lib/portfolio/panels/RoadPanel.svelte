<script lang="ts">
  /**
   * Road to live, from paper onward (anything earlier stays in the Lab):
   * on paper → ready for live (waiting for your signature) → live, first 30
   * days. Each bot shows as its player card; click one for its card and
   * journal.
   */
  import EntityCard from "$lib/qmx/EntityCard.svelte";
  import { cn } from "$lib/utils";
  import { CANDIDATES } from "../demo";
  import { portfolio } from "../portfolio.svelte";

  const LANES = [
    {
      id: "paper",
      label: "On paper",
      note: "Trading a testnet or demo account",
    },
    {
      id: "ready",
      label: "Ready for live",
      note: "Checks passed; waiting for you",
    },
    {
      id: "live",
      label: "Live, first 30 days",
      note: "Watched closely before it's routine",
    },
  ] as const;
</script>

<div class="grid h-full grid-cols-3 gap-2 overflow-auto p-2">
  {#each LANES as lane (lane.id)}
    {@const items = CANDIDATES.filter((c) => c.stage === lane.id)}
    <section
      class="bg-muted/25 flex min-h-0 flex-col gap-2 rounded-xl p-2"
      aria-label={lane.label}
    >
      <header class="flex items-baseline gap-2 px-1">
        <h4 class="text-sm font-semibold">{lane.label}</h4>
        <span class="text-muted-foreground text-xs">{items.length}</span>
      </header>
      <p class="text-muted-foreground -mt-1 px-1 text-xs">{lane.note}</p>
      {#each items as c (c.entity.id)}
        {@const passed = c.checks.filter((k) => k.ok).length}
        <button
          type="button"
          class={cn(
            "rounded-xl text-left transition-shadow",
            portfolio.candidate === c.entity.id && "ring-ring ring-2",
          )}
          onclick={() => (portfolio.candidate = c.entity.id)}
          aria-pressed={portfolio.candidate === c.entity.id}
        >
          <EntityCard entity={c.entity} compact />
          <span class="mt-1.5 flex items-center gap-2 px-1 text-xs">
            <span class="text-muted-foreground">day {c.days}</span>
            <span class="flex flex-1 gap-0.5">
              {#each c.checks as k (k.name)}
                <span
                  class={cn(
                    "h-1.5 flex-1 rounded-full",
                    k.ok === true
                      ? "bg-success"
                      : k.ok === false
                        ? "bg-destructive"
                        : "bg-muted-foreground/30",
                  )}
                  title={k.name}
                ></span>
              {/each}
            </span>
            <span class="text-muted-foreground">{passed}/{c.checks.length}</span
            >
          </span>
        </button>
      {:else}
        <p class="text-muted-foreground px-1 py-6 text-center text-xs">
          Nothing here
        </p>
      {/each}
    </section>
  {/each}
</div>
