<script lang="ts">
  /**
   * Surface style and the operator's own theme (Settings → Appearance).
   * The custom theme layers over the chosen theme, like a VS Code theme
   * override; it can be copied out as JSON to share or keep.
   */
  import Copy from "@lucide/svelte/icons/copy";
  import RotateCcw from "@lucide/svelte/icons/rotate-ccw";
  import { Button } from "$lib/components/ui/button";
  import { Slider } from "$lib/components/ui/slider";
  import { Switch } from "$lib/components/ui/switch";
  import { cn } from "$lib/utils";
  import InfoTip from "./InfoTip.svelte";
  import { DEFAULT_CUSTOM, SURFACES, type CustomTheme } from "./look";
  import { workbench } from "./workbench.svelte";

  let { card }: { card: string } = $props();
  const set = (patch: Partial<CustomTheme>) =>
    workbench.setCustom({ ...workbench.custom, ...patch });
  const PREVIEW: Record<string, string> = {
    glass: "backdrop-blur-md bg-white/8 border border-white/15 rounded-lg",
    liquid:
      "backdrop-blur-xl bg-gradient-to-b from-white/18 to-white/5 border border-white/25 rounded-xl shadow-[inset_0_1px_0_rgb(255_255_255/0.35)]",
    solid: "bg-[var(--card)] border rounded-lg",
    brutal:
      "bg-[var(--card)] border-2 border-[var(--foreground)] shadow-[4px_4px_0_var(--foreground)]",
  };
  async function copyJson() {
    try {
      await navigator.clipboard.writeText(
        JSON.stringify(
          {
            theme: workbench.theme,
            surface: workbench.surface,
            custom: workbench.custom,
          },
          null,
          2,
        ),
      );
      workbench.notify("Theme copied as JSON.");
    } catch {
      workbench.notify("Couldn't reach the clipboard.");
    }
  }
</script>

<section class={cn(card, "mt-4")} aria-labelledby="s-text">
  <div class="flex items-center gap-1">
    <h2 id="s-text" class="text-lg font-semibold">Text size</h2>
    <InfoTip
      label="About text size"
      text="Everything grows with it: text, spacing and panels."
    />
  </div>
  <div class="mt-3 flex gap-2" role="radiogroup" aria-label="Text size">
    {#each [[15, "Standard"], [17, "Large"], [19, "Larger"]] as const as [px, label] (px)}
      <button
        type="button"
        role="radio"
        aria-checked={workbench.textSize === px}
        class={cn(
          "flex flex-col items-center rounded-lg border px-5 py-2",
          workbench.textSize === px
            ? "border-primary bg-primary/12"
            : "hover:bg-muted",
        )}
        onclick={() => workbench.setTextSize(px)}
        ><span style="font-size:{px}px" class="font-semibold">Aa</span><span
          class="text-muted-foreground text-xs">{label}</span
        ></button
      >
    {/each}
  </div>
</section>

<section class={cn(card, "mt-4")} aria-labelledby="s-surface">
  <div class="flex items-center gap-1">
    <h2 id="s-surface" class="text-lg font-semibold">Surface style</h2>
    <InfoTip
      label="About surface style"
      text="How panels sit over the art. Charts and data tiles stay solid in every style."
    />
  </div>
  <div
    class="grid gap-3 border-t pt-4 sm:grid-cols-2 lg:grid-cols-4"
    role="radiogroup"
    aria-label="Surface style"
  >
    {#each SURFACES as s (s.id)}
      <button
        type="button"
        role="radio"
        aria-checked={workbench.surface === s.id}
        class={cn(
          "hover:bg-muted flex flex-col gap-3 rounded-xl border p-3 text-left",
          workbench.surface === s.id && "border-ring bg-muted",
        )}
        onclick={() => workbench.setSurface(s.id)}
      >
        <span
          class="relative block h-20 overflow-hidden rounded-lg bg-[linear-gradient(135deg,var(--primary),var(--chart-3),var(--background))]"
        >
          <span class={cn("absolute inset-3", PREVIEW[s.id])}></span>
        </span>
        <span class="text-sm font-medium" title={s.note}>{s.label}</span>
      </button>
    {/each}
  </div>
</section>

<section class={cn(card, "mt-4")} aria-labelledby="s-custom">
  <div class="flex items-start justify-between gap-3">
    <div class="flex items-center gap-1">
      <h2 id="s-custom" class="text-lg font-semibold">Your theme</h2>
      <InfoTip
        label="About your theme"
        text="Change any of these on top of the theme above, like a VS Code theme. Saved on this machine."
      />
    </div>
    <Switch
      checked={workbench.custom.on}
      onCheckedChange={(v) => set({ on: v })}
      aria-label="Use your theme"
    />
  </div>
  <div
    class={cn(
      "grid gap-5 border-t pt-4 md:grid-cols-2 xl:grid-cols-3",
      !workbench.custom.on && "opacity-60",
    )}
  >
    <label class="flex items-center justify-between gap-3 text-sm">
      Accent
      <span class="flex items-center gap-2">
        <span class="num text-muted-foreground text-xs"
          >{workbench.custom.accent}</span
        >
        <input
          type="color"
          value={workbench.custom.accent}
          oninput={(e) => set({ accent: e.currentTarget.value, on: true })}
          class="h-9 w-12 cursor-pointer rounded border bg-transparent"
          aria-label="Accent colour"
        />
      </span>
    </label>
    <label class="flex items-center justify-between gap-3 text-sm">
      Background
      <span class="flex items-center gap-2">
        <span class="num text-muted-foreground text-xs"
          >{workbench.custom.background}</span
        >
        <input
          type="color"
          value={workbench.custom.background}
          oninput={(e) => set({ background: e.currentTarget.value, on: true })}
          class="h-9 w-12 cursor-pointer rounded border bg-transparent"
          aria-label="Background colour"
        />
      </span>
    </label>
    <div class="grid gap-2 text-sm">
      <span class="flex justify-between"
        >Panel opacity <span class="num text-muted-foreground"
          >{Math.round(workbench.custom.panel * 100)}%</span
        ></span
      >
      <Slider
        type="single"
        min={0.5}
        max={1}
        step={0.05}
        value={workbench.custom.panel}
        onValueChange={(v: number) => set({ panel: v, on: true })}
        aria-label="Panel opacity"
      />
    </div>
    <div class="grid gap-2 text-sm">
      <span class="flex justify-between"
        >Corner roundness <span class="num text-muted-foreground"
          >{workbench.custom.radius}px</span
        ></span
      >
      <Slider
        type="single"
        min={0}
        max={16}
        step={1}
        value={workbench.custom.radius}
        onValueChange={(v: number) => set({ radius: v, on: true })}
        aria-label="Corner roundness"
      />
    </div>
    <div class="grid gap-2 text-sm">
      <span class="flex justify-between"
        >Text size <span class="num text-muted-foreground"
          >{workbench.custom.text}px</span
        ></span
      >
      <Slider
        type="single"
        min={13}
        max={18}
        step={1}
        value={workbench.custom.text}
        onValueChange={(v: number) => set({ text: v, on: true })}
        aria-label="Text size"
      />
    </div>
    <div class="flex items-end gap-2">
      <Button size="sm" variant="outline" onclick={copyJson}
        ><Copy />Copy as JSON</Button
      >
      <Button
        size="sm"
        variant="ghost"
        onclick={() => workbench.setCustom(DEFAULT_CUSTOM)}
        ><RotateCcw />Reset</Button
      >
    </div>
  </div>
</section>
