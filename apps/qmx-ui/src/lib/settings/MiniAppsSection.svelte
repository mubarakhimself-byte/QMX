<script lang="ts">
  /**
   * Mini apps in Settings: the same list as the Apps screen (one source),
   * with the switches you'd look for here: safe mode, each app on or off,
   * and its box at a glance. Details, evidence and logs live in Apps.
   */
  import ArrowRight from "@lucide/svelte/icons/arrow-right";
  import { resolve } from "$app/paths";
  import { Switch } from "$lib/components/ui/switch";
  import { cn } from "$lib/utils";
  import { RISK, STEPS, apps } from "$lib/apps/apps.svelte";
</script>

<div class="flex flex-col gap-6">
  <section class="solid-backing flex items-center gap-4 rounded-2xl border p-5">
    <div class="min-w-0 flex-1">
      <h3 class="text-lg font-semibold">Safe mode</h3>
      <p class="text-muted-foreground">
        Turns off every mini app and add-on that didn't ship with QMX. Use it if
        something misbehaves.
      </p>
    </div>
    <Switch bind:checked={apps.safe} aria-label="Safe mode" />
  </section>

  <ul class="solid-backing flex flex-col rounded-2xl border">
    {#each apps.all as a (a.id)}
      <li
        class={cn(
          "flex flex-wrap items-center gap-x-6 gap-y-2 border-b px-5 py-4 last:border-b-0",
          (apps.safe || !a.on) && "opacity-55",
        )}
      >
        <span class="min-w-56 flex-1">
          <span class="block font-semibold">{a.name}</span>
          <span class="text-muted-foreground text-sm"
            >{RISK[a.risk].label} · {a.runsOn} · {a.budget}</span
          >
        </span>
        <span class="text-muted-foreground w-44 text-sm"
          >{a.health === "tripped" ? "Stopped itself" : STEPS[a.stage]}</span
        >
        <a
          href={resolve("/apps")}
          class="text-primary flex items-center gap-1"
          onclick={() => (apps.selected = a.id)}
          >Details<ArrowRight class="size-4" /></a
        >
        <Switch
          checked={a.on && !apps.safe}
          disabled={apps.safe}
          onCheckedChange={(v) => apps.toggle(a.id, v)}
          aria-label={`Turn ${a.name} on`}
        />
      </li>
    {/each}
  </ul>
</div>
