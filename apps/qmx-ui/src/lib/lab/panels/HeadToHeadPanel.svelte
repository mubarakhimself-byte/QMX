<script lang="ts">
  /**
   * Head to head: the ticked pods as cards side by side, like comparing two
   * players (operator's FC card idea). Same bots, same years, each pod under
   * its current Design settings. A longer bar is better on that line; the
   * trophy shows only where the gap is bigger than the Monte Carlo noise.
   * No total score: the line at the bottom says what you trade for what.
   */
  import Trophy from "@lucide/svelte/icons/trophy";
  import { cn } from "$lib/utils";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { LAB_PODS, POD_ATTRS, STAGE_LABEL, type PodAttr } from "../pods";
  import { podModel } from "../pod-model.svelte";
  import { lab } from "../lab.svelte";

  const size = panelSize();
  const pods = $derived(LAB_PODS.filter((p) => lab.podsTicked.includes(p.id)));
  /** Measures for every ticked pod under its current settings. */
  const table = $derived(
    Object.fromEntries(
      POD_ATTRS.map((a) => [
        a.id,
        Object.fromEntries(pods.map((p) => [p.id, podModel.attr(a.id, p.id)])),
      ]),
    ) as Record<string, Record<string, number>>,
  );
  const val = (a: PodAttr, id: string) => table[a.id]?.[id] ?? 0;

  function show(a: PodAttr, v: number) {
    const sign = a.id === "profit" ? "+" : "";
    return a.unit === "usd"
      ? `${v < 0 ? "−" : sign}$${Math.abs(v).toLocaleString("en-US")}`
      : `${v < 0 ? "−" : ""}${Math.abs(v)}%`;
  }
  /** 0.15..1: how good this value is among the pods shown. */
  function reach(a: PodAttr, v: number) {
    const vs = pods.map((p) => val(a, p.id));
    if (a.better === "none") {
      const top = Math.max(...vs.map(Math.abs)) || 1;
      return 0.15 + 0.85 * (Math.abs(v) / top);
    }
    const lo = Math.min(...vs);
    const hi = Math.max(...vs);
    if (hi === lo) return 1;
    // For "low is better" on negative numbers (losses), closer to 0 is better.
    const score =
      a.better === "high"
        ? (v - lo) / (hi - lo)
        : a.unit === "usd" || v < 0
          ? (v - lo) / (hi - lo)
          : (hi - v) / (hi - lo);
    return 0.15 + 0.85 * score;
  }
  function best(a: PodAttr): string | null {
    if (a.better === "none" || pods.length < 2) return null;
    const ranked = pods
      .map((p) => ({ id: p.id, r: reach(a, val(a, p.id)) }))
      .sort((x, y) => y.r - x.r);
    const gap = Math.abs(val(a, ranked[0].id) - val(a, ranked[1].id));
    return gap > a.noise ? ranked[0].id : null;
  }
  const profit = POD_ATTRS.find((a) => a.id === "profit")!;
  const crash = POD_ATTRS.find((a) => a.id === "crash")!;
  const rich = $derived(
    [...pods].sort((x, y) => val(profit, y.id) - val(profit, x.id))[0],
  );
  const safe = $derived(
    [...pods].sort((x, y) => val(crash, y.id) - val(crash, x.id))[0],
  );
  const summary = $derived.by(() => {
    if (pods.length < 2) return "Tick two pods to compare";
    if (rich.id === safe.id) return `${rich.name} earns most and loses least`;
    const more = val(profit, rich.id) - val(profit, safe.id);
    const less = val(crash, safe.id) - val(crash, rich.id);
    return `${rich.name} +$${more.toLocaleString("en-US")} · ${safe.name} loses $${less.toLocaleString("en-US")} less in a crash`;
  });
</script>

{#if size.mode === "compact"}
  <PanelSummary
    label={rich ? `Most profit · ${rich.name}` : "Head to head"}
    value={rich ? show(profit, val(profit, rich.id)) : "—"}
    status={safe && rich && safe.id !== rich.id
      ? `Safest: ${safe.name}`
      : `${pods.length} pods`}
    values={rich ? podModel.equity(rich.id).curve : undefined}
  />
{:else}
  <div class="flex h-full flex-col">
    <div class="min-h-0 flex-1 overflow-auto p-tile">
      <div
        class="gap-tile grid"
        style="grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr))"
      >
        {#each pods as p (p.id)}
          <article
            class="solid-backing flex min-w-0 flex-col overflow-hidden rounded-xl border"
            style="border-top: 3px solid {p.color}"
          >
            <header
              class="px-panel flex items-baseline justify-between gap-2 pt-2.5"
            >
              <h3 class="truncate text-base font-semibold">{p.name}</h3>
              <span class="text-muted-foreground shrink-0 text-xs"
                >{podModel.version(p.id)} · {STAGE_LABEL[
                  podModel.stage(p.id)
                ]}</span
              >
            </header>
            <ul class="px-panel gap-row flex flex-col pt-2 pb-3">
              {#each POD_ATTRS as a (a.id)}
                {@const v = val(a, p.id)}
                {@const top = best(a) === p.id}
                <li title={a.note}>
                  <div class="flex items-baseline justify-between gap-2">
                    <span class="text-muted-foreground truncate text-xs"
                      >{a.label}</span
                    >
                    <span
                      class={cn(
                        "num flex items-center gap-1 text-sm font-semibold",
                        top && "text-success",
                      )}
                      >{#if top}<Trophy
                          class="size-3"
                          aria-label="Best"
                        />{/if}{show(a, v)}</span
                    >
                  </div>
                  <div class="bg-muted mt-1 h-1.5 overflow-hidden rounded-full">
                    <span
                      class="block h-full rounded-full"
                      style="width:{reach(a, v) *
                        100}%; background:{a.better === 'none'
                        ? 'var(--muted-foreground)'
                        : p.color}"
                    ></span>
                  </div>
                </li>
              {/each}
            </ul>
          </article>
        {:else}
          <p class="text-muted-foreground p-panel text-sm">No pods ticked</p>
        {/each}
      </div>
    </div>
    <div class="px-panel py-row flex shrink-0 items-center gap-2 border-t">
      <p class="min-w-0 flex-1 truncate text-sm">{summary}</p>
      <InfoTip
        label="Explain head to head"
        side="top"
        text="Same bots, same years, each pod under its current Design settings. The trophy shows only where the gap is bigger than the Monte Carlo noise. There is no total score: pick what you trade for what."
      />
    </div>
  </div>
{/if}
