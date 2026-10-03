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
          <EntityCard entity={c.entity} compact>
            {#snippet footer()}
              <span class="flex flex-col gap-1.5 border-t pt-2.5">
                <span class="flex items-center justify-between text-xs">
                  <span class="font-medium"
                    >Day {c.days}{c.stage === "paper"
                      ? " of 30 on paper"
                      : c.stage === "live"
                        ? " of 30 live"
                        : ""}</span
                  >
                  <span class="text-muted-foreground"
                    >{passed} of {c.checks.length} checks</span
                  >
                </span>
                <span class="bg-muted h-1.5 overflow-hidden rounded-full">
                  <span
                    class="bg-primary block h-full rounded-full"
                    style="width:{Math.min(1, c.days / 30) * 100}%"
                  ></span>
                </span>
                <span class="flex gap-1">
                  {#each c.checks as k (k.name)}
                    <span
                      class={cn(
                        "flex-1 truncate rounded px-1 py-0.5 text-center text-[10px]",
                        k.ok === true
                          ? "bg-success/15 text-success"
                          : k.ok === false
                            ? "bg-destructive/15 text-destructive"
                            : "bg-muted text-muted-foreground",
                      )}
                      title={k.name}>{k.name}</span
                    >
                  {/each}
                </span>
              </span>
            {/snippet}
          </EntityCard>
        </button>
      {:else}
        <p class="text-muted-foreground px-1 py-6 text-center text-xs">
          Nothing here
        </p>
      {/each}
    </section>
  {/each}
</div>
