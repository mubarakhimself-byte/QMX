<script lang="ts">
  /**
   * Apps (pass 2, 2026-10-14). Apps are things you open and use, so each tile
   * leads with a glimpse of its own output, grouped by what it is for, pinned
   * ones first. Apps still on their road to live sit in one slim row. Health,
   * the road to live and the box an app runs in live in its About sheet.
   * Discover is the gallery for making a new one. DEMO data.
   */
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import LayoutGrid from "@lucide/svelte/icons/layout-grid";
  import Plus from "@lucide/svelte/icons/plus";
  import ShieldOff from "@lucide/svelte/icons/shield-off";
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import { page } from "$app/state";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Switch } from "$lib/components/ui/switch";
  import { cn } from "$lib/utils";
  import DemoChip from "$lib/workbench/DemoChip.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import AboutSheet from "$lib/apps/AboutSheet.svelte";
  import AppTile from "$lib/apps/AppTile.svelte";
  import FromWidgets from "$lib/apps/FromWidgets.svelte";
  import Preview from "$lib/apps/Preview.svelte";
  import {
    GROUPS,
    RISK,
    STATUS,
    STEPS,
    TEMPLATES,
    apps,
    type Group,
  } from "$lib/apps/apps.svelte";
  import { ICONS } from "$lib/apps/icons";
  import { GROUP_TINT } from "$lib/apps/tint";

  const discover = $derived(page.url.searchParams.get("view") === "discover");
  let widgetsOpen = $state(false);
  let idea = $state("");
  let only = $state<Group | "all">("all");

  const ready = $derived(apps.all.filter((a) => a.stage === 4));
  /** Pinned first, then one section per group; empty ones are left out. */
  const sections = $derived(
    [
      {
        key: "pinned",
        title: "Pinned",
        list: ready.filter((a) => apps.pinned(a.id)),
      },
      ...(Object.keys(GROUPS) as Group[]).map((g) => ({
        key: g,
        title: GROUPS[g],
        list: ready.filter((a) => a.group === g && !apps.pinned(a.id)),
      })),
    ].filter((x) => x.list.length),
  );
  const inProgress = $derived(apps.all.filter((a) => a.stage < 4));
  const stopped = $derived(
    apps.all.filter((a) => apps.status(a) === "stopped").length,
  );
  const templates = $derived(
    TEMPLATES.filter((t) => only === "all" || t.group === only),
  );
  const FILTERS = [["all", "All"], ...Object.entries(GROUPS)] as [
    Group | "all",
    string,
  ][];

  /* eslint-disable svelte/no-navigation-without-resolve */
  const ask = (q: string) =>
    goto(resolve("/copilot") + "?ask=" + encodeURIComponent(q));
  const view = (v: "discover" | "mine") =>
    resolve("/apps") + (v === "discover" ? "?view=discover" : "");
  /* eslint-enable svelte/no-navigation-without-resolve */
</script>

{#snippet viewLink(v: "mine" | "discover", label: string)}
  {@const on = (v === "discover") === discover}
  <!-- eslint-disable svelte/no-navigation-without-resolve -->
  <a
    href={view(v)}
    aria-current={on ? "page" : undefined}
    class={cn(
      "rounded-lg px-4 py-1.5 font-medium transition-colors",
      on
        ? "bg-background text-foreground shadow-sm"
        : "text-muted-foreground hover:text-foreground",
    )}>{label}</a
  >
  <!-- eslint-enable svelte/no-navigation-without-resolve -->
{/snippet}

<div class="flex h-full min-h-0 flex-col">
  <header class="flex flex-wrap items-center gap-x-6 gap-y-3 px-page pt-7 pb-2">
    <div class="mr-auto min-w-0">
      <div class="flex items-center gap-3">
        <h1 class="text-4xl font-semibold tracking-tight">Apps</h1>
        <DemoChip note="Sample apps and previews. Nothing here ran." />
      </div>
      <p class="text-muted-foreground mt-1 text-lg">
        {#if apps.all.length}{ready.length} ready
          {#if stopped}· <span class="text-destructive">{stopped} stopped</span
            >{/if}
          · {inProgress.length} in progress{/if}
      </p>
    </div>
    <nav class="bg-muted flex rounded-xl p-1" aria-label="Apps view">
      {@render viewLink("mine", "Your apps")}
      {@render viewLink("discover", "Discover")}
    </nav>
    <div
      class={cn(
        "flex items-center gap-2 rounded-xl py-1.5 pr-1 pl-3",
        apps.safe && "bg-warning/10 text-warning",
      )}
    >
      <ShieldOff class="size-4.5" />
      <label for="apps-safe" class="font-medium">Safe mode</label>
      <Switch id="apps-safe" bind:checked={apps.safe} aria-label="Safe mode" />
      <InfoTip
        label="What safe mode does"
        text="Turns every app off at once. The same switch as in Settings, Safety."
      />
    </div>
    <!-- eslint-disable svelte/no-navigation-without-resolve -->
    <Button size="lg" href={view("discover")}><Plus />New app</Button>
    <!-- eslint-enable svelte/no-navigation-without-resolve -->
  </header>

  <div class="min-h-0 flex-1 overflow-auto px-page pb-page">
    {#if !discover && !apps.all.length}
      <div class="mt-group flex flex-col items-start gap-3">
        <p class="text-muted-foreground text-lg">No apps yet</p>
        <!-- eslint-disable svelte/no-navigation-without-resolve -->
        <Button href={view("discover")}>Start from a template</Button>
        <!-- eslint-enable svelte/no-navigation-without-resolve -->
      </div>
    {:else if !discover}
      <ul class="tiles mt-5">
        {#each sections as sec (sec.key)}
          {#each sec.list as a, i (a.id)}
            <AppTile app={a} heading={i === 0 ? sec.title : undefined} />
          {/each}
        {/each}
      </ul>

      {#if inProgress.length}
        <section class="mt-group pt-4">
          <div class="mb-3 flex items-center gap-1">
            <h2 class="text-xl font-semibold">In progress</h2>
            <InfoTip
              label="The road to live"
              text="Every app goes Build, Tests, Sandbox on recorded data, Shadow run on live data nothing uses, then Live."
            />
          </div>
          <ul class="flex flex-wrap gap-3">
            {#each inProgress as a (a.id)}
              {@const Icon = ICONS[a.icon]}
              {@const s = apps.status(a)}
              <li>
                <button
                  type="button"
                  class="solid-backing hover:ring-ring/50 flex items-center gap-3 rounded-2xl py-2 pr-4 pl-2 ring-1 ring-border"
                  aria-label={`About ${a.name}`}
                  onclick={() => (apps.selected = a.id)}
                >
                  <span
                    class={cn(
                      "flex size-9 items-center justify-center rounded-xl",
                      GROUP_TINT[a.group],
                    )}><Icon class="size-4.5" /></span
                  >
                  <span class="font-medium">{a.name}</span>
                  <span
                    class="text-muted-foreground flex items-center gap-1.5 text-sm"
                    ><span class={cn("size-2 rounded-full", STATUS[s].dot)}
                    ></span>{s === "attention"
                      ? STATUS[s].label
                      : STEPS[a.stage]}</span
                  >
                </button>
              </li>
            {/each}
          </ul>
        </section>
      {/if}
    {:else}
      <section class="mt-group">
        <form
          class="solid-backing flex items-center gap-3 rounded-3xl p-3 pl-6 ring-1 ring-border"
          onsubmit={(e) => {
            e.preventDefault();
            ask(`Build me an app that ${idea.trim()}`);
          }}
        >
          <Input
            bind:value={idea}
            aria-label="Describe a new app"
            placeholder="Describe an app and the copilot builds it…"
            class="h-12 flex-1 border-0 bg-transparent text-lg shadow-none md:text-lg focus-visible:ring-0 dark:bg-transparent"
          />
          <Button
            type="submit"
            size="lg"
            disabled={!idea.trim()}
            aria-label="Build it"><ArrowUp /></Button
          >
        </form>
        <div class="mt-4 flex flex-wrap items-center gap-3">
          <Button variant="outline" onclick={() => (widgetsOpen = true)}
            ><LayoutGrid />From widgets</Button
          >
          <span class="text-muted-foreground">or pick a template</span>
        </div>
      </section>

      <section class="mt-group">
        <div class="mb-4 flex flex-wrap items-center gap-2">
          <h2 class="mr-4 text-2xl font-semibold">Templates</h2>
          {#each FILTERS as [g, label] (g)}
            <button
              type="button"
              aria-pressed={only === g}
              class={cn(
                "rounded-full px-3.5 py-1 ring-1 ring-border",
                only === g
                  ? "bg-foreground text-background ring-foreground"
                  : "hover:bg-muted",
              )}
              onclick={() => (only = g)}>{label}</button
            >
          {/each}
        </div>
        <ul class="tiles">
          {#each templates as t (t.id)}
            {@const Icon = ICONS[t.icon]}
            <li
              class="solid-backing flex flex-col gap-4 rounded-3xl p-panel ring-1 ring-border"
            >
              <div class="flex items-center gap-3">
                <span
                  class={cn(
                    "flex size-11 shrink-0 items-center justify-center rounded-2xl",
                    GROUP_TINT[t.group],
                  )}><Icon class="size-5.5" /></span
                >
                <span class="min-w-0 flex-1">
                  <span class="block truncate text-lg font-semibold"
                    >{t.name}</span
                  >
                  <span class="text-muted-foreground line-clamp-2 text-sm"
                    >{t.note}</span
                  >
                </span>
              </div>
              {#if workbench.demoMode}
                <div
                  class="border-border/70 flex-1 rounded-2xl border border-dashed p-4 opacity-80"
                >
                  <Preview preview={t.preview} />
                </div>
              {:else}
                <span class="flex-1"></span>
              {/if}
              <div class="flex items-center gap-2">
                <Button
                  variant="outline"
                  onclick={() =>
                    ask(`Build me a "${t.name}" app from the template: `)}
                  aria-label={`Use the ${t.name} template`}><Plus />Use</Button
                >
                {#if t.risk === "money"}
                  <span class="text-warning ml-auto text-sm"
                    >{RISK.money.label}</span
                  >
                  <InfoTip label="Money apps" text={RISK.money.rule} />
                {/if}
              </div>
            </li>
          {/each}
        </ul>
      </section>
    {/if}
  </div>
</div>

<AboutSheet />
<FromWidgets bind:open={widgetsOpen} />

<style>
  .tiles {
    display: grid;
    gap: 1.5rem 1.25rem;
    grid-template-columns: repeat(auto-fill, minmax(min(19rem, 100%), 1fr));
  }
</style>
