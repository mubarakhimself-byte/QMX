<script lang="ts">
  import { resolve } from "$app/paths";
  import { page } from "$app/state";
  import { Button } from "$lib/components/ui/button";
  import { Switch } from "$lib/components/ui/switch";
  import { workbench, type Theme } from "$lib/workbench/workbench.svelte";
  import { cn } from "$lib/utils";
  import BrokersSection from "$lib/settings/BrokersSection.svelte";
  import ServersDataSection from "$lib/settings/ServersDataSection.svelte";
  import ModelsToolsSection from "$lib/settings/ModelsToolsSection.svelte";
  import GeneralSection from "$lib/settings/GeneralSection.svelte";
  import Group from "$lib/settings/Group.svelte";
  import Row from "$lib/settings/Row.svelte";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import DemoChip from "$lib/workbench/DemoChip.svelte";
  import CopilotsSection from "$lib/settings/CopilotsSection.svelte";
  import MiniAppsSection from "$lib/settings/MiniAppsSection.svelte";
  import SafetySection from "$lib/settings/SafetySection.svelte";
  import { Input } from "$lib/components/ui/input";
  import { Slider } from "$lib/components/ui/slider";
  import Shuffle from "@lucide/svelte/icons/shuffle";
  import Save from "@lucide/svelte/icons/save";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import InkBackground from "$lib/workbench/InkBackground.svelte";
  import LookSettings from "$lib/workbench/LookSettings.svelte";
  import { ROTATIONS } from "$lib/workbench/look";
  import {
    ART_STYLES,
    BUILTIN_PRESETS,
    GLOWS,
    type ArtConfig,
  } from "$lib/workbench/art";

  // Settings (declutter, 2026-10-14): sections on the left, one page at a
  // time on the right using the full width. Old ?tab= links still land.
  const GROUPS = [
    {
      label: "You",
      items: [
        { id: "general", label: "General" },
        { id: "appearance", label: "Appearance" },
      ],
    },
    {
      label: "Connections",
      items: [
        { id: "brokers", label: "Brokers and accounts" },
        { id: "tools", label: "Models and tools" },
        { id: "servers", label: "Servers and data" },
      ],
    },
    {
      label: "Copilots and mini apps",
      items: [
        { id: "copilots", label: "Copilots" },
        { id: "apps", label: "Mini apps" },
      ],
    },
    {
      label: "Safety",
      items: [
        { id: "safety", label: "Safety" },
        { id: "developer", label: "Developer" },
      ],
    },
  ];
  const TABS = GROUPS.flatMap((g) => g.items);
  const OLD: Record<string, string> = {
    models: "copilots",
    providers: "tools",
    mcp: "tools",
    nodes: "servers",
    compute: "servers",
    data: "servers",
    exchanges: "brokers",
  };
  const asked = page.url.searchParams.get("tab") ?? "";
  const fromUrl = OLD[asked] ?? asked;
  let tab = $state<string>(
    TABS.some((t) => t.id === fromUrl) ? fromUrl : "general",
  );
  let presetName = $state("");

  const setArt = (patch: Partial<ArtConfig>) =>
    workbench.setArt({ ...workbench.art, ...patch });
  const sameArt = (a: ArtConfig, b: ArtConfig) =>
    (Object.keys(a) as (keyof ArtConfig)[]).every((k) => a[k] === b[k]);

  const THEME_CHOICES: {
    id: Theme;
    label: string;
    note: string;
    swatch: string[];
  }[] = [
    {
      id: "ink",
      label: "Ink",
      note: "Charcoal and old gold",
      swatch: ["#0d0e10", "#e0b062", "#9fd8d0"],
    },
    {
      id: "cobalt",
      label: "Cobalt",
      note: "Electric blue",
      swatch: ["#05082e", "#6f7bff", "#7ee2ff"],
    },
    {
      id: "ember",
      label: "Ember",
      note: "Dark red and orange",
      swatch: ["#120a08", "#ff9a62", "#ffd28a"],
    },
    {
      id: "graphite",
      label: "Graphite",
      note: "Cool steel and ice blue",
      swatch: ["#0c0e12", "#9cc4ff", "#6fd3a0"],
    },
    {
      id: "moss",
      label: "Moss",
      note: "Deep green and lime",
      swatch: ["#0a0f0b", "#b8e05c", "#7fd8c8"],
    },
    {
      id: "violet",
      label: "Violet",
      note: "Night purple and pink",
      swatch: ["#0e0a16", "#c9a6ff", "#ff8aa8"],
    },
    {
      id: "paper",
      label: "Paper",
      note: "Light: ink on cream",
      swatch: ["#f4f1ea", "#1f6b45", "#2b55c7"],
    },
  ];

  const card = "solid-backing surface flex flex-col gap-3 rounded-xl p-5";
</script>

<svelte:head><title>Settings · QMX</title></svelte:head>

<div class="flex h-full">
  <nav
    aria-label="Settings sections"
    class="bg-panel flex w-64 shrink-0 flex-col gap-4 overflow-auto border-r p-4"
  >
    <h1 class="px-2 text-xl font-semibold">Settings</h1>
    {#each GROUPS as g (g.label)}
      <div>
        <p class="text-muted-foreground mb-1 px-2 text-sm font-medium">
          {g.label}
        </p>
        {#each g.items as t (t.id)}
          <button
            type="button"
            class={cn(
              "w-full rounded-lg px-3 py-2 text-left",
              tab === t.id ? "bg-muted font-medium" : "hover:bg-muted/60",
            )}
            aria-current={tab === t.id ? "true" : undefined}
            onclick={() => (tab = t.id)}>{t.label}</button
          >
        {/each}
      </div>
    {/each}
  </nav>
  <div class="min-w-0 flex-1 overflow-auto">
    <div class="flex max-w-[150rem] flex-col gap-group px-page py-page">
      <div class="flex items-center gap-3">
        <h2 class="text-3xl font-semibold">
          {TABS.find((t) => t.id === tab)?.label}
        </h2>
        <DemoChip
          note="Sample providers, machines, sources, copilots and approvals. Your choices are kept on this machine; nothing connects yet."
        />
      </div>

      {#if tab === "general"}
        <GeneralSection />
      {:else if tab === "brokers"}
        <BrokersSection />
      {:else if tab === "tools"}
        <ModelsToolsSection />
      {:else if tab === "servers"}
        <ServersDataSection />
      {:else if tab === "copilots"}
        <CopilotsSection />
      {:else if tab === "apps"}
        <MiniAppsSection />
      {:else if tab === "safety"}
        <SafetySection />
      {:else if tab === "appearance"}
        <section class={card} aria-labelledby="s-theme">
          <div class="flex items-center gap-1">
            <h2 id="s-theme" class="text-lg font-semibold">Theme</h2>
            <InfoTip
              label="About themes"
              text="Glass panels over an ink map of fractal price paths. Charts and trading panels sit on a solid backing so they stay readable."
            />
          </div>
          <div
            class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 2xl:grid-cols-7"
            role="radiogroup"
            aria-label="Theme"
          >
            {#each THEME_CHOICES as t (t.id)}
              <button
                type="button"
                role="radio"
                aria-checked={workbench.theme === t.id}
                class={cn(
                  "hover:bg-muted flex flex-col gap-3 rounded-xl border p-3 text-left transition-colors",
                  workbench.theme === t.id && "border-ring bg-muted",
                )}
                onclick={() => workbench.setTheme(t.id)}
              >
                <span
                  class="flex h-14 items-end gap-1 rounded-lg p-2"
                  style="background: {t.swatch[0]}"
                >
                  <span
                    class="h-6 w-6 rounded-md"
                    style="background: {t.swatch[1]}"
                  ></span>
                  <span
                    class="h-4 w-4 rounded-sm"
                    style="background: {t.swatch[2]}"
                  ></span>
                </span>
                <span class="text-sm font-medium" title={t.note}>{t.label}</span
                >
              </button>
            {/each}
          </div>
        </section>
        <LookSettings {card} />
        <section class={cn(card, "mt-4")} aria-labelledby="s-art">
          <div class="flex items-start justify-between gap-3">
            <div class="flex items-center gap-1">
              <h2 id="s-art" class="text-lg font-semibold">Background art</h2>
              <InfoTip
                label="About background art"
                text="The art behind the panels, drawn in your theme's ink. Pick a style, tune it, and save the ones you like. Saved on this machine."
              />
            </div>
            <Switch
              checked={workbench.inkEnabled}
              onCheckedChange={(v) => workbench.setInk(v)}
              aria-label="Show background art"
            />
          </div>
          <div class="grid gap-4 border-t pt-4 lg:grid-cols-5">
            <div
              class="bg-background relative aspect-video overflow-hidden rounded-xl border lg:col-span-3"
            >
              <InkBackground inline config={workbench.art} />
              <div
                class="surface absolute bottom-4 left-4 w-56 rounded-lg p-3 text-xs"
              >
                <span class="block font-medium">Panel over the art</span>
                <span class="text-muted-foreground"
                  >How cards read on top of it</span
                >
              </div>
              {#if !workbench.inkEnabled}
                <span
                  class="bg-background/80 absolute top-3 right-3 rounded-md px-2 py-1 text-xs"
                  >Off: the preview still shows it</span
                >
              {/if}
            </div>
            <div class="flex flex-col gap-4 lg:col-span-2">
              <div
                role="radiogroup"
                aria-label="Art style"
                class="grid grid-cols-5 gap-2"
              >
                {#each ART_STYLES as s (s.id)}
                  <button
                    type="button"
                    role="radio"
                    aria-checked={workbench.art.style === s.id}
                    title={s.note}
                    class={cn(
                      "hover:bg-muted flex flex-col gap-1 rounded-lg border p-1.5 text-left text-xs transition-colors",
                      workbench.art.style === s.id && "border-ring bg-muted",
                    )}
                    onclick={() => setArt({ style: s.id })}
                  >
                    <span
                      class="bg-background relative block h-12 overflow-hidden rounded-md"
                    >
                      <InkBackground
                        inline
                        config={{ ...workbench.art, style: s.id, glow: "off" }}
                      />
                    </span>
                    <span class="truncate">{s.label}</span>
                  </button>
                {/each}
              </div>
              <div class="grid gap-2 text-sm">
                <span class="flex justify-between"
                  >Density<span class="text-muted-foreground tabular-nums"
                    >{workbench.art.density.toFixed(1)}×</span
                  ></span
                >
                <Slider
                  type="single"
                  min={0.5}
                  max={2}
                  step={0.1}
                  value={workbench.art.density}
                  onValueCommit={(v: number) => setArt({ density: v })}
                  aria-label="Density"
                />
              </div>
              <div class="grid gap-2 text-sm">
                <span class="flex justify-between"
                  >Strength<span class="text-muted-foreground tabular-nums"
                    >{Math.round(workbench.art.strength * 100)}%</span
                  ></span
                >
                <Slider
                  type="single"
                  min={0.3}
                  max={1.6}
                  step={0.05}
                  value={workbench.art.strength}
                  onValueChange={(v: number) => setArt({ strength: v })}
                  aria-label="Strength"
                />
              </div>
              <div
                class="flex flex-wrap items-center justify-between gap-2 text-sm"
              >
                <span>Glow</span>
                <div class="flex gap-1" role="radiogroup" aria-label="Glow">
                  {#each GLOWS as g (g)}
                    <Button
                      size="sm"
                      role="radio"
                      aria-checked={workbench.art.glow === g}
                      variant={workbench.art.glow === g ? "secondary" : "ghost"}
                      class="capitalize"
                      onclick={() => setArt({ glow: g })}>{g}</Button
                    >
                  {/each}
                </div>
              </div>
              <div class="flex items-center justify-between gap-2 text-sm">
                <span
                  >Variation <span class="text-muted-foreground tabular-nums"
                    >#{workbench.art.seed}</span
                  ></span
                >
                <Button
                  size="sm"
                  variant="outline"
                  onclick={() =>
                    setArt({ seed: Math.floor(Math.random() * 99999) })}
                  ><Shuffle class="size-4" />Shuffle</Button
                >
              </div>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-3 border-t pt-4 text-sm">
            <span class="flex items-center gap-1 font-medium"
              >Change the art on its own<InfoTip
                label="About changing the art"
                text="Picks a new style and variation on the schedule you choose."
              /></span
            >
            <div
              class="ml-auto flex gap-1"
              role="radiogroup"
              aria-label="Rotate the art"
            >
              {#each ROTATIONS as r (r.id)}
                <Button
                  size="sm"
                  role="radio"
                  aria-checked={workbench.artRotate === r.id}
                  variant={workbench.artRotate === r.id ? "secondary" : "ghost"}
                  onclick={() => workbench.setArtRotate(r.id)}>{r.label}</Button
                >
              {/each}
            </div>
          </div>
          <div class="flex flex-col gap-3 border-t pt-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <h3 class="text-sm font-medium">Saved variants</h3>
              <form
                class="flex gap-2"
                onsubmit={(e) => {
                  e.preventDefault();
                  const p = workbench.saveArtPreset(presetName);
                  presetName = "";
                  workbench.notify(`Saved background: ${p.name}`);
                }}
              >
                <Input
                  class="h-8 w-48"
                  placeholder="Name this variant"
                  maxlength={40}
                  bind:value={presetName}
                  aria-label="Variant name"
                />
                <Button size="sm" type="submit"
                  ><Save class="size-4" />Save current</Button
                >
              </form>
            </div>
            <ul
              class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5 2xl:grid-cols-7"
            >
              {#each [...BUILTIN_PRESETS, ...workbench.artPresets] as p (p.id)}
                {@const mine = p.id.startsWith("u-")}
                {@const on = sameArt(p.config, workbench.art)}
                <li
                  class={cn(
                    "group relative overflow-hidden rounded-lg border",
                    on && "border-ring",
                  )}
                >
                  <button
                    type="button"
                    class="hover:bg-muted flex w-full flex-col text-left"
                    aria-pressed={on}
                    onclick={() => workbench.setArt(p.config)}
                  >
                    <span
                      class="bg-background relative block aspect-video overflow-hidden"
                    >
                      <InkBackground inline config={p.config} />
                    </span>
                    <span
                      class="flex items-center justify-between gap-2 p-2 text-xs"
                    >
                      <span class="truncate font-medium">{p.name}</span>
                      <span class="text-muted-foreground"
                        >{mine ? "Yours" : "Built-in"}</span
                      >
                    </span>
                  </button>
                  {#if mine}
                    <Button
                      size="icon-sm"
                      variant="secondary"
                      class="absolute top-1.5 right-1.5 opacity-0 group-focus-within:opacity-100 group-hover:opacity-100"
                      aria-label={`Delete ${p.name}`}
                      onclick={() => workbench.deleteArtPreset(p.id)}
                      ><Trash2 class="size-3.5" /></Button
                    >
                  {/if}
                </li>
              {/each}
            </ul>
          </div>
        </section>
      {:else if tab === "developer"}
        <Group title="Developer" class="max-w-4xl">
          <Row
            label="Show demo content"
            tip="Labelled sample apps, workflows, Library items and conversations for design review. Nothing is saved or run."
          >
            <Switch
              checked={workbench.demoMode}
              onCheckedChange={(v) => workbench.setDemo(v)}
              aria-label="Show demo content"
            />
          </Row>
          <Row
            label="Component library"
            tip="Every QMX building block rendered live, with the spec the copilot uses to compose mini apps."
          >
            <Button size="sm" variant="outline" href={resolve("/gallery")}
              >Open library</Button
            >
          </Row>
        </Group>
      {/if}
    </div>
  </div>
</div>
