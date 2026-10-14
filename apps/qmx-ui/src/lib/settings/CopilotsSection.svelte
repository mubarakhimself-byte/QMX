<script lang="ts">
  /**
   * Every copilot in one list (main, Lab, Portfolio, Library, each mini
   * app's) and, for the one selected: its model, standing instructions,
   * the MCP servers it may use, what it may touch and where it must ask
   * first. No modes (R2). Skills are being designed elsewhere.
   */
  import Lock from "@lucide/svelte/icons/lock";
  import { Switch } from "$lib/components/ui/switch";
  import { Textarea } from "$lib/components/ui/textarea";
  import { cn } from "$lib/utils";
  import { REACH } from "$lib/copilot/aim.svelte";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import { page } from "$app/state";
  import Choice from "./Choice.svelte";
  import Group from "./Group.svelte";
  import Row from "./Row.svelte";
  import { settings } from "./settings.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";

  // Each copilot's gear opens this page with ?copilot=<its id>.
  let selected = $state(page.url.searchParams.get("copilot") ?? "main");
  const entry = $derived(
    settings.copilots.find((c) => c.id === selected) ?? settings.copilots[0],
  );
  const cfg = $derived(settings.copilot(entry.id));
  const models = $derived(settings.modelsFor(entry.id));

  function toggleIn<T extends string>(list: T[], id: T, on: boolean): T[] {
    const rest = list.filter((x) => x !== id);
    return on ? [...rest, id] : rest;
  }
</script>

<div class="grid items-start gap-group lg:grid-cols-[18rem_1fr]">
  <nav
    aria-label="Copilots"
    class="solid-backing flex flex-col rounded-2xl border p-tile"
  >
    {#each settings.copilots as c, i (c.id)}
      {#if i === 4}
        <p class="text-muted-foreground px-3 pt-group pb-row text-sm">
          Mini apps
        </p>
      {/if}
      <button
        type="button"
        class={cn(
          "flex items-center justify-between gap-2 rounded-lg px-3 py-row text-left",
          c.id === entry.id ? "bg-muted font-medium" : "hover:bg-muted/60",
        )}
        aria-current={c.id === entry.id ? "true" : undefined}
        onclick={() => (selected = c.id)}
      >
        <span class="truncate">{c.name}</span>
        <span class="text-muted-foreground shrink-0 text-sm"
          >{settings.copilot(c.id).model.split("/")[1]}</span
        >
      </button>
    {/each}
  </nav>

  <div class="grid items-start gap-group 2xl:grid-cols-2">
    <Group title={`${entry.name} copilot`}>
      <div class="flex flex-col gap-row py-row">
        <span class="flex items-center gap-1"
          >Model<InfoTip
            label="About the model"
            text="From the providers this copilot may use, under Models and tools."
          /></span
        >
        {#if models.length}
          <Choice
            label={`${entry.name} copilot model`}
            value={cfg.model}
            options={models}
            onchange={(v) => settings.editCopilot(entry.id, { model: v })}
            class="w-fit min-w-64"
          />
        {:else}
          <span class="text-warning text-sm">No provider allowed</span>
        {/if}
      </div>
      <div class="flex flex-col gap-row border-t py-row">
        <span>Standing instructions</span>
        <Textarea
          rows={4}
          value={cfg.instructions}
          oninput={(e) =>
            settings.editCopilot(entry.id, {
              instructions: e.currentTarget.value,
            })}
          placeholder="How it should work for you"
          aria-label={`${entry.name} instructions`}
        />
      </div>
      <div class="flex flex-col gap-row border-t py-row">
        <span>Tools it may use</span>
        <div class="flex flex-wrap gap-2">
          {#each settings.mcp as m (m.id)}
            {@const added = m.on && workbench.demoMode}
            {@const on = cfg.uses.includes(m.id) && added}
            <button
              type="button"
              aria-pressed={on}
              disabled={!added}
              title={added ? m.note : `${m.name} is off under Models and tools`}
              class={cn(
                "rounded-full border px-3 py-1 text-sm disabled:opacity-45",
                on
                  ? "border-primary bg-primary/12"
                  : "text-muted-foreground hover:bg-muted",
              )}
              onclick={() => settings.setUse(entry.id, m.id, !on)}
              >{m.name}</button
            >
          {/each}
        </div>
      </div>
      <Row
        label="Skills"
        tip="Skills are being designed now. They will be listed and switched here."
      >
        <span class="text-muted-foreground text-sm">Coming later</span>
      </Row>
    </Group>

    <Group
      title="What it may touch"
      tip="Touch lets it act in that area. Ask first makes it stop for your yes before each action there."
    >
      <table class="w-full text-left">
        <thead class="text-muted-foreground text-sm">
          <tr>
            <th class="py-row font-normal">Area</th>
            <th class="py-row text-right font-normal">Touch</th>
            <th class="py-row text-right font-normal">Ask first</th>
          </tr>
        </thead>
        <tbody>
          {#each REACH as r (r.id)}
            {@const on = cfg.reach.includes(r.id)}
            <tr class="border-t">
              <td class="py-row">
                <span class="flex items-center gap-1"
                  >{r.label}<InfoTip
                    label={`About ${r.label}`}
                    text={r.note}
                  /></span
                >
              </td>
              <td class="py-row text-right">
                <Switch
                  checked={on}
                  onCheckedChange={(v) =>
                    settings.editCopilot(entry.id, {
                      reach: toggleIn(cfg.reach, r.id, v),
                      approve: v
                        ? cfg.approve
                        : toggleIn(cfg.approve, r.id, false),
                    })}
                  aria-label={`${entry.name} may touch ${r.label}`}
                />
              </td>
              <td class="py-row text-right">
                <Switch
                  checked={cfg.approve.includes(r.id)}
                  disabled={!on}
                  onCheckedChange={(v) =>
                    settings.editCopilot(entry.id, {
                      approve: toggleIn(cfg.approve, r.id, v),
                    })}
                  aria-label={`${entry.name} asks before acting in ${r.label}`}
                />
              </td>
            </tr>
          {/each}
          <tr class="border-t">
            <td class="py-row">
              <span class="flex items-center gap-1"
                >Real money<InfoTip
                  label="About real money"
                  text="No copilot can place, size or approve a live order. It can only propose; you sign in Portfolio."
                /></span
              >
            </td>
            <td class="text-muted-foreground py-row text-right" colspan="2">
              <span class="inline-flex items-center gap-1.5 text-sm"
                ><Lock class="size-3.5" />Never. You sign.</span
              >
            </td>
          </tr>
        </tbody>
      </table>
    </Group>
  </div>
</div>
