<script lang="ts">
  import { shell } from "../state.svelte";
  import * as Tooltip from "$lib/components/ui/tooltip";
  import * as Menu from "$lib/components/ui/dropdown-menu";
  import Icon from "$lib/qmx/Icon.svelte";
  import { nav, fit, fold, rem, guestColour, guestFill, type Guest, size } from "./model.svelte";
  import type { Place } from "../data";

  // Two floating pills under the top bar, icons only (a tooltip names each).
  // Places in the first: the two boards in their own well, then the lists of
  // his things. Mini apps in the second, in their own colours; several can be
  // open, and what does not fit goes behind "More". Each pill folds on its
  // own to a small handle. Neither ever scrolls.
  let h = $state(0);
  const r = $derived(rem());
  const unit = $derived(2.75 * r); // a places key plus the gap under it
  const appUnit = $derived(2.875 * r); // a mini-app key plus its wider gap
  const handle = $derived(1.75 * r); // a pill's fold handle and the gap above it
  const placeChrome = $derived(fold.places ? handle + 0.5 * r + 2 : 0.5 * r + 2 + handle + 0.75 * r); // padding, border, handle, the boards' well
  const appChrome = $derived(0.5 * r + 2 + handle);
  // Places first, always leaving room under them for the mini-app pill with
  // at least its "More" key; mini apps get what is left. Nothing scrolls.
  const reserve = $derived(nav.apps.length ? r + appChrome + (fold.apps ? 0 : appUnit) : 0);
  const placeSlots = $derived(fold.places ? 0 : Math.max(2, Math.floor((h - placeChrome - reserve) / unit)));
  const places = $derived(fit(nav.places, placeSlots));
  // The places pill's height, computed (not measured, so it is right on the
  // first frame and in a background tab), with a little slack.
  const placesH = $derived(placeChrome + Math.min(nav.places.length, placeSlots) * unit + r);
  const appSlots = $derived(fold.apps ? 0 : Math.max(1, Math.floor((h - placesH - r - appChrome) / appUnit)));
  const apps = $derived(fit(nav.apps, appSlots));
  const inMore = $derived(places.more.some((p) => p.id === shell.place));
  const boards = $derived(places.shown.filter((p) => p.kind === "board"));
  const lists = $derived(places.shown.filter((p) => p.kind !== "board"));
  const appOpen = $derived(nav.apps.some((a) => shell.place === `app:${a.id}`));
</script>

{#snippet tip(label: string, body: import("svelte").Snippet<[Record<string, unknown>]>)}
  <Tooltip.Root>
    <Tooltip.Trigger>
      {#snippet child({ props })}{@render body(props)}{/snippet}
    </Tooltip.Trigger>
    <Tooltip.Content side="right">{label}</Tooltip.Content>
  </Tooltip.Root>
{/snippet}

{#snippet badge(n: number | undefined)}
  {#if n}
    <span class="bg-needs num absolute -top-1 -right-1.5 grid h-4 min-w-4 place-items-center rounded-full px-1 text-[0.65rem] leading-none font-semibold text-black">{n > 99 ? "99+" : n}</span>
  {/if}
{/snippet}

{#snippet placeKey(p: Place)}
  {#snippet body(props: Record<string, unknown>)}
    <button {...props} class="key relative size-10 shrink-0" data-on={shell.place === p.id} aria-label={p.name} aria-current={shell.place === p.id ? "page" : undefined} onclick={() => shell.go(p.id)}>
      <Icon name={p.icon} class="size-5 shrink-0" />
      {@render badge(nav.badge(p))}
    </button>
  {/snippet}
  {@render tip(p.name, body)}
{/snippet}

{#snippet appKey(a: Guest)}
  {#snippet body(props: Record<string, unknown>)}
    <button
      {...props}
      class="relative flex size-10 shrink-0 items-center justify-center rounded-md transition-[filter] duration-150 hover:brightness-125 active:scale-[0.97]"
      style:color={guestColour(a)}
      style:background={guestFill(a)}
      style:outline={shell.place === `app:${a.id}` ? `1px solid ${guestColour(a)}` : undefined}
      aria-label="{a.name}, mini app"
      aria-current={shell.place === `app:${a.id}` ? "page" : undefined}
      onclick={() => shell.go(`app:${a.id}`)}
    >
      <Icon name={a.icon} class="size-5 shrink-0" />
    </button>
  {/snippet}
  {@render tip(`${a.name} · mini app`, body)}
{/snippet}

<!-- A pill's fold handle: a short bar under its keys; folded, it is all that is left. -->
{#snippet foldHandle(folded: boolean, what: string, toggle: () => void, dot = false)}
  {#snippet body(props: Record<string, unknown>)}
    <button {...props} class="press text-muted-foreground relative h-6 w-10 shrink-0" aria-label={folded ? `Show ${what}` : `Fold ${what}`} aria-expanded={!folded} onclick={toggle}>
      <Icon name={folded ? "chevron-down" : "minus"} class="size-4" />
      {#if dot}<span class="dot bg-foreground absolute top-1 right-1 size-1.5" aria-hidden="true"></span>{/if}
    </button>
  {/snippet}
  {@render tip(folded ? `Show ${what}` : `Fold ${what}`, body)}
{/snippet}

<div class="pointer-events-none absolute inset-y-3 left-3 z-20 flex flex-col justify-start gap-4" use:size={(_, y) => (h = y)}>
  <nav class="surface pointer-events-auto flex flex-col items-center gap-1 p-1 shadow-xl shadow-black/60" aria-label="Places">
    {#if !fold.places}
      {#if boards.length}
        <div class="flex flex-col gap-1 rounded-md bg-white/[0.045] p-0.5" role="group" aria-label="Boards">
          {#each boards as p (p.id)}{@render placeKey(p)}{/each}
        </div>
      {/if}
      {#each lists as p (p.id)}{@render placeKey(p)}{/each}
      {#if places.more.length}
        <Menu.Root>
          <Menu.Trigger>
            {#snippet child({ props })}
              <button {...props} class="key relative size-10 shrink-0" data-on={inMore} aria-label="More places">
                <Icon name="more" class="size-5 shrink-0" />
              </button>
            {/snippet}
          </Menu.Trigger>
          <Menu.Content side="right" align="end" class="w-56">
            {#each places.more as p (p.id)}
              <Menu.Item onclick={() => shell.go(p.id)}><Icon name={p.icon} />{p.name}</Menu.Item>
            {/each}
          </Menu.Content>
        </Menu.Root>
      {/if}
    {/if}
    {@render foldHandle(fold.places, "places", () => (fold.places = !fold.places))}
  </nav>

  {#if nav.apps.length}
    <nav class="pointer-events-auto flex flex-col items-center gap-1.5 rounded-lg border border-dashed p-1" style:border-color="oklch(0.84 0.12 195 / 0.3)" style:background="oklch(0.1 0.01 230)" aria-label="Mini apps">
      {#if !fold.apps}
        {#each apps.shown as a (a.id)}{@render appKey(a)}{/each}
        {#if apps.more.length}
          <Menu.Root>
            <Menu.Trigger>
              {#snippet child({ props })}
                <button {...props} class="key relative size-10 shrink-0" aria-label="{apps.more.length} more mini apps">
                  <Icon name="more" class="size-5 shrink-0" />
                  <span class="num bg-panel-2 absolute -right-1.5 -bottom-1 rounded-full px-1 text-[0.65rem] leading-4">{apps.more.length}</span>
                </button>
              {/snippet}
            </Menu.Trigger>
            <Menu.Content side="right" align="end" class="w-72">
              {#each apps.more as a (a.id)}
                <Menu.Item onclick={() => shell.go(`app:${a.id}`)}>
                  <span class="dot size-2" style:color={guestColour(a)}></span><span class="truncate">{a.name}</span>
                </Menu.Item>
              {/each}
            </Menu.Content>
          </Menu.Root>
        {/if}
      {/if}
      {@render foldHandle(fold.apps, "mini apps", () => (fold.apps = !fold.apps), fold.apps && appOpen)}
    </nav>
  {/if}
</div>
