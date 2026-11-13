<script lang="ts">
  import * as Menu from "$lib/components/ui/dropdown-menu";
  import Icon from "$lib/qmx/Icon.svelte";
  import { tone } from "$lib/qmx/state";
  import Life from "./Life.svelte";
  import Body from "./Body.svelte";
  import SectionCard from "./SectionCard.svelte";
  import Decide from "./Decide.svelte";
  import Converse from "./Converse.svelte";
  import { things } from "$lib/shell/things.svelte";
  import { shell } from "$lib/shell/state.svelte";
  import { kindName, guestActions, guestInk, guestWash, type Obj } from "$lib/shell/model";

  // Every thing gets the same page: who it is and where it is in its life,
  // what can be done to it, then its sections. Proposals and the live
  // session take their own shape because their job is different (decide,
  // converse), but they sit in the same frame and trail.
  let { o, sub }: { o: Obj; sub?: string } = $props();

  const sections = $derived(things.sectionsOf(o));
  const spare = $derived(things.spareOf(o));
  const subSec = $derived(sub ? (o.sections ?? []).find((s) => s.id === sub) : undefined);

  // Which market the unit's actions act on.
  let pick = $state<string | null>(null);
  const markets = $derived(o.markets ?? []);
  const sel = $derived(markets.find((m) => m.sym === pick) ?? markets.find((m) => m.life === "live") ?? markets[0]);
  let armed = $state(false);
  $effect(() => {
    void sel?.sym;
    armed = false;
  });
  const openProp = (sym?: string) => things.all.find((p) => p.kind === "proposal" && p.evidence?.unit === o.id && p.evidence.sym === sym && !things.decision(p.id));
  const proposal = $derived(openProp(sel?.sym));
  const gActs = $derived(guestActions.filter((a) => a.kind === o.kind && things.guest(a.guest) && things.fixture !== "first"));
  const failed = $derived(o.kind === "workflow" && o.word === "failed");
  // Leaving the page ends "Edit page".
  $effect(() => () => things.setEditing(false));
</script>

{#if o.kind === "proposal" && o.evidence}
  <Decide {o} />
{:else if o.id === "s-regime"}
  <Converse {o} />
{:else if sub && subSec}
  <!-- One level down: a section on its own, with room. -->
  <article class="flex h-full min-h-0 flex-col px-6 pt-5 pb-4">
    <p class="text-muted-foreground truncate text-sm">{o.name}</p>
    <h1 class="display mt-1 text-4xl font-semibold">{subSec.title}</h1>
    <div class="surface mt-4 min-h-0 flex-1 overflow-x-hidden overflow-y-auto p-1.5 [&_td]:py-2.5 [&_td]:text-base">
      <Body body={subSec.full ?? subSec.body} big />
    </div>
  </article>
{:else}
  <article class="page flex h-full min-h-0 flex-col overflow-x-hidden overflow-y-auto">
    <header class="flex shrink-0 flex-wrap items-start gap-x-8 gap-y-4 px-6 pt-5 pb-4">
      <div class="min-w-[min(100%,24rem)] flex-1">
        <p class="text-muted-foreground flex min-w-0 items-center gap-2 text-sm">
          <span class="dot {tone[o.tone]}"></span>
          <span class="shrink-0">{kindName[o.kind]}{o.version ? ` ${o.version}` : ""}</span>
          <span aria-hidden="true">·</span><span class="truncate {tone[o.tone]}">{o.word}</span>
          {#if o.where}
            <span aria-hidden="true">·</span>
            <span class="flex min-w-0 items-center gap-1" title="Runs on {o.where}"><Icon name={o.where === "This PC" ? "laptop" : "server"} class="size-3.5 shrink-0" /><span class="truncate">{o.where}</span></span>
          {/if}
        </p>
        <h1 class="ttl display mt-1 line-clamp-2 text-4xl leading-[1.05] font-semibold [overflow-wrap:anywhere]" title={o.name}>{o.name}</h1>
        {#if o.line}<p class="text-muted-foreground mt-1.5 line-clamp-2 text-lg">{o.line}</p>{/if}
      </div>

      <!-- What can be done to it. -->
      <div class="flex shrink-0 flex-wrap items-center gap-2 pt-1">
        {#if o.kind === "unit" && sel}
          {#if proposal}
            <button class="h-10 rounded-md px-4 font-semibold whitespace-nowrap transition-transform duration-100 active:scale-[0.97]" style:background="var(--needs)" style:color="var(--background)" onclick={() => shell.open({ id: proposal.id })}>Decide: {sel.sym} to {proposal.evidence?.to}</button>
          {:else if sel.life === "live" || sel.life === "paper"}
            {#if sel.paused}
              <button class="press border-border h-10 gap-2 border px-4" onclick={() => things.setLife(o, sel.sym, "resume")}><Icon name="play" />Resume</button>
            {:else}
              <button class="press border-border h-10 gap-2 border px-4" onclick={() => things.setLife(o, sel.sym, "pause")}><Icon name="pause" />Pause</button>
            {/if}
            {#if sel.life === "live"}
              <button class="press border-border h-10 gap-2 border px-4" onclick={() => things.setLife(o, sel.sym, "paper")}><Icon name="undo" />Back to paper</button>
            {/if}
            <button
              class="h-10 gap-2 rounded-md border px-4 whitespace-nowrap transition-colors duration-150 active:scale-[0.97] {armed ? 'bg-down text-background border-transparent font-semibold' : 'text-down border-down/40 hover:bg-down/10'} inline-flex items-center"
              onclick={() => (armed ? (things.setLife(o, sel.sym, "retired"), (armed = false)) : (armed = true))}
              onblur={() => (armed = false)}
            >
              <Icon name="archive" />{armed ? `Retire on ${sel.sym}: click again` : "Retire"}
            </button>
          {/if}
        {:else if failed}
          <button class="bg-foreground text-background h-10 gap-2 rounded-md px-4 font-semibold transition-transform duration-100 active:scale-[0.97] inline-flex items-center" onclick={() => things.retry(o)}><Icon name="retry" />Retry</button>
          <button class="press border-border h-10 border px-4" onclick={() => (things.retry(o), things.say("Retrying step 4 with a stronger model"))}>Stronger model</button>
          <button class="press border-border h-10 border px-4" onclick={() => things.say("Step 4 skipped; the run carries on")}>Skip step</button>
        {:else if o.kind === "node"}
          <button class="press border-border h-10 gap-2 border px-4" onclick={() => things.say(`${o.name}: no new trades`)}><Icon name="pause" />Pause node</button>
        {:else if o.kind === "run" && o.word === "running"}
          <button class="press border-border h-10 gap-2 border px-4" onclick={() => things.say(`${o.name}: stopping`)}><Icon name="square" class="size-4" />Stop</button>
        {/if}

        {#if sections.length || spare.length}
          <button class="press h-10 gap-2 px-3" data-on={things.editing} onclick={() => things.setEditing(!things.editing)}><Icon name="edit" />{things.editing ? "Done" : "Edit page"}</button>
        {/if}
        <Menu.Root>
          <Menu.Trigger>
            {#snippet child({ props })}
              <button {...props} class="press size-10" aria-label="More actions" title="More actions"><Icon name="more" /></button>
            {/snippet}
          </Menu.Trigger>
          <Menu.Content align="end" class="w-80">
            <Menu.Item onclick={() => shell.send(o.name)}><Icon name="send" />Send to the copilot</Menu.Item>
            <Menu.Item onclick={() => shell.go("library")}><Icon name="library" />Show in the Library</Menu.Item>
            {#each gActs as a (a.id)}
              {@const g = things.guest(a.guest)!}
              <Menu.Separator />
              <Menu.Item onclick={() => things.say(a.done)}>
                <span class="flex min-w-0 flex-1 flex-col">
                  <span class="flex items-center gap-2"><span class="dot size-2" style:color={guestInk(g.hue)}></span>{a.label}</span>
                  <span class="text-muted-foreground truncate pl-4 text-xs">From {g.name}</span>
                </span>
              </Menu.Item>
            {/each}
          </Menu.Content>
        </Menu.Root>
      </div>

      {#if markets.length}
        <!-- Where it is in its life, per market. Click a market to act on it. -->
        <div class="flex w-full flex-col gap-1" role="radiogroup" aria-label="Markets">
          {#each markets as m (m.sym)}
            <button
              class="pick -mx-2 max-w-[52rem] rounded-md px-2 py-1 text-left"
              role="radio"
              aria-checked={m.sym === sel?.sym}
              data-on={markets.length > 1 && m.sym === sel?.sym}
              onclick={() => (pick = m.sym)}
            >
              <Life market={{ ...m, target: undefined }} target={openProp(m.sym)?.evidence?.to} big />
            </button>
          {/each}
        </div>
      {/if}
    </header>

    {#if things.editing}
      <div class="mx-6 mb-3 flex shrink-0 flex-wrap items-center gap-3 rounded-lg border border-dashed px-4 py-2.5">
        <Icon name="edit" class="text-muted-foreground" />
        <p class="min-w-0 flex-1">This layout is used by every {kindName[o.kind].toLowerCase()}.</p>
        <button class="press h-9 px-3" onclick={() => things.resetSections(o)}>Reset</button>
        <button class="bg-foreground text-background h-9 rounded-md px-4 font-semibold" onclick={() => things.setEditing(false)}>Done</button>
      </div>
    {/if}

    {#if sections.length}
      <div class="grid-s grid shrink-0 gap-[var(--gap)] px-6 pb-6">
        {#each sections as s, i (s.id)}
          <SectionCard
            {s}
            onopen={s.full ? () => shell.open({ id: o.id, sub: s.id }) : undefined}
            edit={things.editing
              ? {
                  up: i > 0 ? () => things.moveSection(o, s.id, -1) : undefined,
                  down: i < sections.length - 1 ? () => things.moveSection(o, s.id, 1) : undefined,
                  remove: () => things.removeSection(o, s.id),
                }
              : undefined}
          />
        {/each}
      </div>
    {:else if !things.editing}
      <p class="text-muted-foreground px-6 pb-6">No sections yet. Edit page to add one.</p>
    {/if}

    {#if things.editing}
      <div class="shrink-0 px-6 pb-8">
        <h2 class="text-muted-foreground mb-2 text-sm font-medium">Add a section</h2>
        {#if spare.length}
          <div class="flex flex-wrap gap-2">
            {#each spare as s (s.id)}
              {@const g = s.guest ? things.guest(s.guest) : undefined}
              <button
                class="press border-border h-11 gap-2 border px-4 {g ? 'border-dashed' : ''}"
                style:border-color={g ? guestInk(g.hue) : undefined}
                style:background={g ? guestWash(g.hue) : undefined}
                onclick={() => things.addSection(o, s.id)}
              >
                <Icon name="plus" class="size-4" />{s.title}
                {#if g}<span class="text-xs font-semibold" style:color={guestInk(g.hue)}>{g.name}</span>{/if}
              </button>
            {/each}
          </div>
        {:else}
          <p class="text-muted-foreground">Every section is on the page.</p>
        {/if}
      </div>
    {/if}
  </article>
{/if}

<style>
  .page {
    container-type: inline-size;
  }
  /* A short window: the name takes one line so the sections keep their room. */
  @media (max-height: 820px) {
    .ttl {
      -webkit-line-clamp: 1;
      line-clamp: 1;
      font-size: 2rem;
    }
  }
  .grid-s {
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 22rem), 1fr));
  }
  .grid-s :global(> section) {
    min-height: 13rem;
    max-height: 26rem;
  }
  @container (min-width: 48rem) {
    .grid-s :global(> section.wide) {
      grid-column: span 2;
    }
  }
</style>
