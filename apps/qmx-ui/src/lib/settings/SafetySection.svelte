<script lang="ts">
  /**
   * Safety rules in one place: what goes live without you, by risk; the
   * money rule that never changes; and where the kill switch lives.
   */
  import Lock from "@lucide/svelte/icons/lock";
  import { resolve } from "$app/paths";

  const RISK = [
    {
      what: "Shows things",
      example: "A news panel, a chart, a screener",
      live: "Goes live by itself once its checks and shadow run pass",
    },
    {
      what: "Runs work",
      example: "A scheduled scraper, a retrain, a sweep",
      live: "The same, inside a budget it can't exceed",
    },
    {
      what: "Touches money",
      example: "Anything that would place or size orders",
      live: "Only proposes. You sign every time; QMX places the order",
    },
  ];
</script>

<div class="flex flex-col gap-6">
  <section class="rounded-2xl border p-5">
    <h3 class="text-lg font-semibold">What goes live without you</h3>
    <p class="text-muted-foreground">
      Decided by what a thing can touch, not by how it was built.
    </p>
    <ul class="mt-4 flex flex-col">
      {#each RISK as r (r.what)}
        <li class="grid gap-x-6 gap-y-1 border-t py-3 sm:grid-cols-[11rem_1fr]">
          <span class="font-medium">{r.what}</span>
          <span
            >{r.live}<span class="text-muted-foreground block text-sm"
              >{r.example}</span
            ></span
          >
        </li>
      {/each}
    </ul>
  </section>
  <section class="flex items-start gap-4 rounded-2xl border p-5">
    <Lock class="text-primary mt-1 size-5 shrink-0" />
    <div>
      <h3 class="text-lg font-semibold">Real money</h3>
      <p class="text-muted-foreground">
        No copilot, agent or mini app can move or risk real money. Promotions,
        activations and live orders always need your signature in Portfolio.
        This can't be changed here.
      </p>
    </div>
  </section>
  <section class="rounded-2xl border p-5">
    <h3 class="text-lg font-semibold">Kill switch</h3>
    <p class="text-muted-foreground">
      Stop new trades or close and halt by pod, by server or everything, from
      the Portfolio header.
      <a href={resolve("/portfolio")} class="text-primary underline"
        >Open Portfolio</a
      >
    </p>
  </section>
</div>
