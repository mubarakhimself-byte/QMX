<script lang="ts">
  /**
   * Ticked runs side by side: measures and what differs between them. Runs of
   * different procedures or unfinished runs are not put on one scale; the
   * panel says why instead of showing a misleading winner.
   */
  import X from "@lucide/svelte/icons/x";
  import { cn } from "$lib/utils";
  import EnvChip from "../EnvChip.svelte";
  import StatusDot from "../StatusDot.svelte";
  import { RUNS } from "../demo";
  import { lab } from "../lab.svelte";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";

  const size = panelSize();

  const runs = $derived(RUNS.filter((r) => lab.ticked.includes(r.id)));
  const finished = $derived(runs.filter((r) => r.status === "done"));
  const procedures = $derived([...new Set(runs.map((r) => r.procedure))]);
  const best = (k: "net" | "sharpe" | "maxDd") =>
    Math.max(...finished.map((r) => r[k] ?? -Infinity));
  const ROWS = [
    {
      k: "net",
      label: "Net",
      fmt: (v: number | null) =>
        v === null ? "—" : `${v > 0 ? "+" : ""}${v}%`,
    },
    {
      k: "maxDd",
      label: "Max drawdown",
      fmt: (v: number | null) => (v === null ? "—" : `${v}%`),
    },
    {
      k: "sharpe",
      label: "Sharpe",
      fmt: (v: number | null) => (v === null ? "—" : `${v}`),
    },
  ] as const;
</script>

<div class="flex h-full flex-col">
  {#if runs.length < 2}
    <div
      class="text-muted-foreground p-panel flex h-full items-center justify-center text-center text-sm"
    >
      Tick two runs to compare
    </div>
  {:else if size.mode === "compact"}
    {@const top = [...finished].sort((a, b) => (b.net ?? 0) - (a.net ?? 0))[0]}
    <PanelSummary
      label={top ? `Best · ${top.symbol} ${top.timeframe}` : "Compare"}
      value={top ? `${(top.net ?? 0) > 0 ? "+" : ""}${top.net}%` : "—"}
      status={procedures.length > 1
        ? "Different procedures: not ranked"
        : `${runs.length} runs`}
      tone={procedures.length > 1 ? "warn" : "muted"}
    />
  {:else}
    <div class="px-panel flex h-11 shrink-0 items-center gap-2 text-xs">
      <span class="text-muted-foreground">{runs.length} runs</span>
      {#if procedures.length > 1}<span class="text-warning"
          >Different procedures: not ranked</span
        >{/if}
      <InfoTip
        class="ml-auto"
        label="Explain compare"
        text="Ticked runs side by side. The best value per row is marked only when every run used the same procedure; runs of different procedures or unfinished runs are not put on one scale."
      />
    </div>
    <div class="min-h-0 flex-1 overflow-auto">
      <table class="w-full text-sm">
        <thead class="text-muted-foreground text-left text-xs">
          <tr class="border-b">
            <th class="py-row pl-panel font-normal">Measure</th>
            {#each runs as r (r.id)}
              <th class="py-row pr-3 font-normal">
                <span class="flex items-center gap-1.5">
                  <span class="text-foreground">{r.symbol} {r.timeframe}</span>
                  <button
                    type="button"
                    class="hover:text-foreground ml-auto"
                    aria-label={`Remove ${r.id} from compare`}
                    onclick={() => lab.toggleTick(r.id)}
                    ><X class="size-3" /></button
                  >
                </span>
                <span class="num block">{r.id}</span>
              </th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each ROWS as row (row.k)}
            <tr class="border-b border-border/50">
              <td class="text-muted-foreground py-row pl-panel text-xs"
                >{row.label}</td
              >
              {#each runs as r (r.id)}
                {@const v = r[row.k]}
                <td
                  class={cn(
                    "num py-row pr-3",
                    procedures.length === 1 &&
                      v !== null &&
                      v === best(row.k) &&
                      "text-success font-medium",
                  )}>{row.fmt(v)}</td
                >
              {/each}
            </tr>
          {/each}
          <tr class="border-b border-border/50">
            <td class="text-muted-foreground py-row pl-panel text-xs">Procedure</td>
            {#each runs as r (r.id)}<td class="py-row pr-3 text-xs"
                >{r.procedure} · {r.role}</td
              >{/each}
          </tr>
          <tr class="border-b border-border/50">
            <td class="text-muted-foreground py-row pl-panel text-xs">Where</td>
            {#each runs as r (r.id)}<td class="py-row pr-3"
                ><EnvChip env={r.env} status={r.status} /></td
              >{/each}
          </tr>
          <tr class="border-b border-border/50">
            <td class="text-muted-foreground py-row pl-panel text-xs">State</td>
            {#each runs as r (r.id)}<td class="py-row pr-3"
                ><StatusDot status={r.status} /></td
              >{/each}
          </tr>
          <tr>
            <td class="text-muted-foreground py-row pl-panel text-xs">Changed</td>
            {#each runs as r (r.id)}<td class="py-row pr-3 text-xs"
                >{(r.changed ?? ["procedure"]).join(", ")}</td
              >{/each}
          </tr>
        </tbody>
      </table>
    </div>

  {/if}
</div>
