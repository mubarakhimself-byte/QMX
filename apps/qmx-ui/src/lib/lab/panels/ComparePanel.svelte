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
      class="text-muted-foreground flex h-full items-center justify-center p-6 text-center text-sm"
    >
      Tick two or more runs in the runs table to compare them here.
    </div>
  {:else}
    {#if procedures.length > 1}
      <p class="bg-warning/12 text-warning border-b px-3 py-2 text-xs">
        These runs use different procedures ({procedures.join(", ")}). Their
        numbers are shown side by side but not ranked.
      </p>
    {/if}
    <div class="min-h-0 flex-1 overflow-auto">
      <table class="w-full text-sm">
        <thead class="text-muted-foreground text-left text-xs">
          <tr class="border-b">
            <th class="py-2 pl-3 font-normal">Measure</th>
            {#each runs as r (r.id)}
              <th class="py-2 pr-3 font-normal">
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
              <td class="text-muted-foreground py-2 pl-3 text-xs"
                >{row.label}</td
              >
              {#each runs as r (r.id)}
                {@const v = r[row.k]}
                <td
                  class={cn(
                    "num py-2 pr-3",
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
            <td class="text-muted-foreground py-2 pl-3 text-xs">Procedure</td>
            {#each runs as r (r.id)}<td class="py-2 pr-3 text-xs"
                >{r.procedure} · {r.role}</td
              >{/each}
          </tr>
          <tr class="border-b border-border/50">
            <td class="text-muted-foreground py-2 pl-3 text-xs">Where</td>
            {#each runs as r (r.id)}<td class="py-2 pr-3"
                ><EnvChip env={r.env} status={r.status} /></td
              >{/each}
          </tr>
          <tr>
            <td class="text-muted-foreground py-2 pl-3 text-xs">State</td>
            {#each runs as r (r.id)}<td class="py-2 pr-3"
                ><StatusDot status={r.status} /></td
              >{/each}
          </tr>
        </tbody>
      </table>
    </div>
    <p class="text-muted-foreground border-t px-3 py-2 text-xs">
      What changed between them: {[
        ...new Set(runs.flatMap((r) => r.changed ?? ["procedure"])),
      ].join(", ")}. Highest value per row is marked only when every run used
      the same procedure.
    </p>
  {/if}
</div>
