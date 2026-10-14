<script lang="ts">
  /**
   * The promotion card for the selected bot: what you are signing, the
   * checks as passed or refused, and the one action that fits its stage.
   * A failing check blocks signing. Signing moves the bot along the Road to
   * live in the browser (demo); for real it is journaled and activation
   * takes effect at the next day boundary.
   */
  import Check from "@lucide/svelte/icons/check";
  import X from "@lucide/svelte/icons/x";
  import Minus from "@lucide/svelte/icons/minus";
  import PenLine from "@lucide/svelte/icons/pen-line";
  import Undo2 from "@lucide/svelte/icons/undo-2";
  import LibraryBig from "@lucide/svelte/icons/library-big";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import { itemById } from "$lib/library/items";
  import { cn } from "$lib/utils";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { portfolio } from "../portfolio.svelte";

  const size = panelSize();
  const c = $derived(
    portfolio.candidates.find((x) => x.entity.id === portfolio.candidate) ??
      portfolio.candidates[0],
  );
  const blocked = $derived(c.checks.some((k) => k.ok === false));
  const passed = $derived(c.checks.filter((k) => k.ok).length);
  const action = $derived(
    c.stage === "paper"
      ? "Sign for live"
      : c.stage === "ready"
        ? "Sign and activate"
        : "Pull back to paper",
  );
  const STAGE = { paper: "On paper", ready: "Ready for live", live: "Live" };

  function act() {
    const was = action;
    portfolio.advance(c.entity.id);
    workbench.notify(`${was}: ${c.entity.name} is now ${STAGE[c.stage]}.`);
  }
</script>

{#if size.mode === "compact"}
  <PanelSummary
    label={c.entity.name}
    value={`${passed}/${c.checks.length}`}
    status={blocked
      ? `Waiting on ${c.checks.find((k) => k.ok === false)?.name}`
      : STAGE[c.stage]}
    tone={blocked ? "bad" : "good"}
  />
{:else}
  <div class="flex h-full flex-col overflow-auto">
    <div class="px-panel flex h-11 shrink-0 items-center gap-2">
      <span class="truncate text-base font-semibold">{c.entity.name}</span>
      <span class="text-muted-foreground truncate text-xs"
        >{c.pod} · {STAGE[c.stage]} · day {c.days}</span
      >
      {#if itemById(c.entity.id)}
        <!-- eslint-disable svelte/no-navigation-without-resolve -->
        <a
          href={`${resolve("/library")}?item=${c.entity.id}`}
          class="text-muted-foreground hover:text-foreground hover:bg-muted ml-auto flex size-7 shrink-0 items-center justify-center rounded-md"
          aria-label="Open in the Library"
          title="Open in the Library"><LibraryBig class="size-3.5" /></a
        >
        <!-- eslint-enable svelte/no-navigation-without-resolve -->
      {/if}
    </div>
    <div class="px-panel gap-group flex flex-col pb-panel">
      <p class="text-sm">{c.summary}</p>
      <ul class="grid gap-x-group gap-y-row @md:grid-cols-2">
        {#each c.checks as k (k.name)}
          <li class="flex items-center gap-2 text-sm">
            {#if k.ok === true}<Check
                class="text-success size-4 shrink-0"
              />{:else if k.ok === false}<X
                class="text-destructive size-4 shrink-0"
              />{:else}<Minus
                class="text-muted-foreground size-4 shrink-0"
              />{/if}
            <span
              class={cn("truncate", k.ok === null && "text-muted-foreground")}
              >{k.name}</span
            >
          </li>
        {/each}
      </ul>
    </div>
    <div
      class="px-panel py-row mt-auto flex flex-wrap items-center gap-3 border-t"
    >
      <Button
        size="sm"
        variant={c.stage === "live" ? "outline" : "default"}
        disabled={blocked && c.stage !== "live"}
        onclick={act}
        >{#if c.stage === "live"}<Undo2 />{:else}<PenLine
          />{/if}{action}</Button
      >
      {#if blocked && c.stage !== "live"}<span class="text-destructive text-xs"
          >Waiting on {c.checks.find((k) => k.ok === false)?.name}</span
        >{/if}
      {#if c.stage === "ready"}<span class="text-muted-foreground text-xs"
          >Activates 00:00 UTC</span
        >{/if}
    </div>
  </div>
{/if}
