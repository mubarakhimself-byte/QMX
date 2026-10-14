<script lang="ts">
  /**
   * The promotion card for the selected bot: what you are signing in plain
   * words (part of the card's identity), the checks as a passed or refused
   * list, and the one action that fits its stage. A failing check blocks
   * signing and says why. Activation takes effect at the next day boundary.
   */
  import Check from "@lucide/svelte/icons/check";
  import X from "@lucide/svelte/icons/x";
  import Minus from "@lucide/svelte/icons/minus";
  import PenLine from "@lucide/svelte/icons/pen-line";
  import LibraryBig from "@lucide/svelte/icons/library-big";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import { itemById } from "$lib/library/items";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { CANDIDATES } from "../demo";
  import { portfolio } from "../portfolio.svelte";

  const c = $derived(
    CANDIDATES.find((x) => x.entity.id === portfolio.candidate) ??
      CANDIDATES[0],
  );
  const blocked = $derived(c.checks.some((k) => k.ok === false));
  const action = $derived(
    c.stage === "paper"
      ? "Sign for live"
      : c.stage === "ready"
        ? "Sign and activate"
        : "Pull back to paper",
  );
</script>

<div class="flex h-full flex-col overflow-auto">
  <div class="flex items-baseline gap-2 border-b px-4 py-3">
    <span class="text-lg font-semibold">{c.entity.name}</span>
    <span class="text-muted-foreground text-sm">{c.pod} · day {c.days}</span>
    {#if itemById(c.entity.id)}
      <!-- eslint-disable svelte/no-navigation-without-resolve -->
      <a
        href={`${resolve("/library")}?item=${c.entity.id}`}
        class="text-muted-foreground hover:text-foreground ml-auto flex items-center gap-1 text-xs"
        ><LibraryBig class="size-3.5" />In the Library</a
      >
      <!-- eslint-enable svelte/no-navigation-without-resolve -->
    {/if}
  </div>
  <section class="border-b px-4 py-3">
    <p class="text-muted-foreground mb-1 text-xs">What you are signing</p>
    <p class="text-base">{c.summary}</p>
  </section>
  <section class="border-b px-4 py-3">
    <ul class="grid gap-2">
      {#each c.checks as k (k.name)}
        <li class="flex items-center gap-2.5 text-base">
          {#if k.ok === true}<Check
              class="text-success size-5"
            />{:else if k.ok === false}<X
              class="text-destructive size-5"
            />{:else}<Minus class="text-muted-foreground size-5" />{/if}
          <span class={cn(k.ok === null && "text-muted-foreground")}
            >{k.name}</span
          >
        </li>
      {/each}
    </ul>
  </section>
  <div class="mt-auto flex flex-wrap items-center gap-3 px-4 py-3">
    <Button
      size="lg"
      variant={c.stage === "live" ? "outline" : "default"}
      disabled={blocked && c.stage !== "live"}
      onclick={() =>
        workbench.notify(
          `${action} needs the trading server. You sign with your operator key; it's journaled.`,
        )}><PenLine />{action}</Button
    >
    {#if blocked && c.stage !== "live"}<span class="text-destructive text-sm"
        >Waiting on: {c.checks.find((k) => k.ok === false)?.name}</span
      >{/if}
    {#if c.stage === "ready"}<span class="text-muted-foreground text-sm"
        >Takes effect at 00:00 UTC</span
      >{/if}
  </div>
</div>
