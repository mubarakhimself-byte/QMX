<script lang="ts">
  /**
   * Road to live, from paper onward (anything earlier stays in the Lab):
   * on paper → ready for live (waiting for your signature) → live, first 30
   * days. Each bot shows as its player card; click one for its card and
   * journal.
   */
  import EntityCard from "$lib/qmx/EntityCard.svelte";
  import { cn } from "$lib/utils";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { portfolio } from "../portfolio.svelte";

  const size = panelSize();
  const waiting = $derived(
    portfolio.candidates.filter((c) => c.stage === "ready").length,
  );

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

{#if size.mode === "compact"}
  <PanelSummary
    label="Road to live"
    value={`${waiting} waiting`}
    status={LANES.map(
      (l) =>
        `${portfolio.candidates.filter((c) => c.stage === l.id).length} ${l.id}`,
    ).join(" · ")}
    tone={waiting ? "warn" : "muted"}
  />
{:else}
  <div class="gap-tile p-tile grid h-full grid-cols-3 overflow-auto">
    {#each LANES as lane (lane.id)}
      {@const items = portfolio.candidates.filter((c) => c.stage === lane.id)}
      <section
        class="bg-muted/25 flex min-h-0 flex-col gap-2 rounded-xl p-2"
        aria-label={lane.label}
      >
        <header class="flex items-center gap-2 px-1">
          <h4 class="truncate text-sm font-semibold">{lane.label}</h4>
          <span class="text-muted-foreground num text-xs">{items.length}</span>
          <InfoTip
            class="ml-auto"
            label={`What ${lane.label} means`}
            text={lane.note}
          />
        </header>
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
                          "flex-1 truncate rounded px-1 py-0.5 text-center text-xs",
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
{/if}
