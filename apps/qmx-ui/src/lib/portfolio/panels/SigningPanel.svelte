<script lang="ts">
  /**
   * The promotion card for the selected item: plain-words summary (part of
   * the card's identity), the checks that ran on the server as a passed or
   * refused list, evidence, and your signature. Never signed from a bare
   * dropdown; a failing check blocks signing and says why.
   */
  import Check from "@lucide/svelte/icons/check";
  import X from "@lucide/svelte/icons/x";
  import Minus from "@lucide/svelte/icons/minus";
  import PenLine from "@lucide/svelte/icons/pen-line";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { PROMOTIONS, bookById } from "../demo";
  import { portfolio } from "../portfolio.svelte";

  const p = $derived(PROMOTIONS.find((x) => x.id === portfolio.promotion)!);
  const blocked = $derived(p.gates.some((g) => g.ok === false));
  const verb = $derived(p.stage === "live" ? "Activate" : "Sign promotion");
</script>

<div class="flex h-full flex-col overflow-auto">
  <div class="border-b px-3 py-2">
    <p class="text-muted-foreground text-xs">
      {p.kind} · {bookById(p.book)?.name} · {p.stage}
    </p>
    <p class="text-base font-semibold">{p.what}</p>
  </div>
  <section class="border-b px-3 py-3">
    <h4 class="text-muted-foreground mb-1 text-xs">What you are signing</h4>
    <p class="text-sm">{p.summary}</p>
  </section>
  <section class="border-b px-3 py-3">
    <h4 class="text-muted-foreground mb-2 text-xs">Checks run on the server</h4>
    <ul class="grid gap-1.5">
      {#each p.gates as g (g.name)}
        <li class="flex items-center gap-2 text-sm">
          {#if g.ok === true}<Check
              class="text-success size-4"
            />{:else if g.ok === false}<X
              class="text-destructive size-4"
            />{:else}<Minus class="text-muted-foreground size-4" />{/if}
          <span class={cn(g.ok === null && "text-muted-foreground")}
            >{g.name}</span
          >
          {#if g.ok === null}<span class="text-muted-foreground ml-auto text-xs"
              >waiting</span
            >{/if}
        </li>
      {/each}
    </ul>
  </section>
  <section class="px-3 py-3 text-xs">
    <p class="text-muted-foreground">
      Evidence: walk-forward run-441 (CT-32) · Book template fp1 9c41…e2a0
    </p>
    {#if p.stage === "live"}<p class="mt-1">
        Activation takes effect at the next day boundary (00:00 UTC); there is
        no override.
      </p>{/if}
  </section>
  <div class="mt-auto flex items-center gap-2 border-t px-3 py-2">
    <Button
      size="sm"
      disabled={blocked}
      onclick={() =>
        workbench.notify(
          `${verb} needs the trading node. You'd sign with your operator key; it's journaled.`,
        )}><PenLine />{verb}</Button
    >
    {#if blocked}<span class="text-destructive text-xs"
        >Blocked: {p.gates.find((g) => g.ok === false)?.name}</span
      >{/if}
    <span class="text-muted-foreground ml-auto text-xs">0 of 1 signed</span>
  </div>
</div>
