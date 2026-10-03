<script lang="ts">
  /**
   * Head to head: the ticked pods as cards side by side, like comparing two
   * players (operator's FC card idea). Same bots, same years. A longer bar
   * is better on that line; "Best" shows only where the gap is bigger than
   * the Monte Carlo noise. No total score: the sentence at the bottom says
   * what you trade for what.
   */
  import Trophy from "@lucide/svelte/icons/trophy";
  import { LAB_PODS, POD_ATTRS, STAGE_LABEL, type PodAttr } from "../pods";
  import { lab } from "../lab.svelte";

  const pods = $derived(LAB_PODS.filter((p) => lab.podsTicked.includes(p.id)));

  function show(a: PodAttr, v: number) {
    const sign = a.id === "profit" ? "+" : "";
    return a.unit === "usd"
      ? `${v < 0 ? "−" : sign}$${Math.abs(v).toLocaleString("en-US")}`
      : `${v < 0 ? "−" : ""}${Math.abs(v)}%`;
  }
  /** 0.15..1: how good this value is among the pods shown. */
  function reach(a: PodAttr, v: number) {
    const vs = pods.map((p) => a.values[p.id]);
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
      .map((p) => ({ id: p.id, r: reach(a, a.values[p.id]) }))
      .sort((x, y) => y.r - x.r);
    const gap = Math.abs(a.values[ranked[0].id] - a.values[ranked[1].id]);
    return gap > a.noise ? ranked[0].id : null;
  }
  const summary = $derived.by(() => {
    if (pods.length < 2) return "Tick at least two pods in Pod resources.";
    const profit = POD_ATTRS.find((a) => a.id === "profit")!;
    const crash = POD_ATTRS.find((a) => a.id === "crash")!;
    const rich = [...pods].sort(
      (x, y) => profit.values[y.id] - profit.values[x.id],
    )[0];
    const safe = [...pods].sort(
      (x, y) => crash.values[y.id] - crash.values[x.id],
    )[0];
    if (rich.id === safe.id)
      return `${rich.name} earns the most and loses the least in a crash on these bots.`;
    const more = profit.values[rich.id] - profit.values[safe.id];
    const less = crash.values[safe.id] - crash.values[rich.id];
    return `${rich.name} earns $${more.toLocaleString("en-US")} more. ${safe.name} loses $${less.toLocaleString("en-US")} less in its worst crash.`;
  });
</script>

<div class="flex h-full flex-col">
  <div class="min-h-0 flex-1 overflow-auto p-2">
    <div
      class="grid gap-2"
      style="grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr))"
    >
      {#each pods as p (p.id)}
        <article
          class="solid-backing flex flex-col overflow-hidden rounded-xl border"
          style="border-top: 3px solid {p.color}"
        >
          <header class="flex items-baseline justify-between gap-2 px-3 pt-2.5">
            <h3 class="truncate text-base font-semibold">{p.name}</h3>
            <span class="text-muted-foreground shrink-0 text-xs"
              >{p.version} · {STAGE_LABEL[p.stage]}</span
            >
          </header>
          <ul class="flex flex-col gap-2 px-3 pt-2 pb-3">
            {#each POD_ATTRS as a (a.id)}
              {@const v = a.values[p.id]}
              {@const top = best(a) === p.id}
              <li title={a.note}>
                <div class="flex items-baseline justify-between gap-2">
                  <span class="text-muted-foreground text-xs">{a.label}</span>
                  <span
                    class="num flex items-center gap-1 text-sm font-semibold"
                    class:text-success={top}
                    >{#if top}<Trophy
                        class="size-3"
                        aria-label="Best"
                      />{/if}{show(a, v)}</span
                  >
                </div>
                <div class="bg-muted mt-1 h-1.5 overflow-hidden rounded-full">
                  <span
                    class="block h-full rounded-full"
                    style="width:{reach(a, v) * 100}%; background:{a.better ===
                    'none'
                      ? 'var(--muted-foreground)'
                      : p.color}"
                  ></span>
                </div>
              </li>
            {/each}
          </ul>
        </article>
      {:else}
        <p class="text-muted-foreground p-4 text-sm">
          Tick pods in Pod resources to put them head to head.
        </p>
      {/each}
    </div>
  </div>
  <p class="border-t px-3 py-2 text-sm">{summary}</p>
</div>
