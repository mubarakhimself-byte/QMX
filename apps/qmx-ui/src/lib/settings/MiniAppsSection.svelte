<script lang="ts">
  /**
   * Mini apps in Settings: the Apps screen's list (one source) with each
   * app's box as controls: on or off, daily budget, schedule, network
   * allow-list and approval rule. Safe mode is the same switch as in Apps
   * and Safety. Evidence and logs stay in Apps.
   */
  import Lock from "@lucide/svelte/icons/lock";
  import X from "@lucide/svelte/icons/x";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Switch } from "$lib/components/ui/switch";
  import * as Popover from "$lib/components/ui/popover";
  import { cn } from "$lib/utils";
  import { RISK, STEPS, apps, type MiniApp } from "$lib/apps/apps.svelte";
  import Choice from "./Choice.svelte";
  import Group from "./Group.svelte";
  import { APP_SCHEDULES, APPROVAL, settings } from "./settings.svelte";

  let host = $state("");
  const live = $derived(apps.all.filter((a) => a.on && !apps.safe).length);

  function addHost(a: MiniApp) {
    const h = host.trim();
    if (!h) return;
    const c = settings.appControls(a);
    if (!c.network.includes(h))
      settings.editApp(a, { network: [...c.network, h] });
    host = "";
  }
</script>

<div class="flex flex-col gap-group">
  <Group
    title="Mini apps"
    meta={apps.safe
      ? "Safe mode: all off"
      : apps.all.length
        ? `${live} of ${apps.all.length} on`
        : "None installed"}
  >
    {#snippet actions()}
      <label class="flex items-center gap-2 text-sm">
        Safe mode
        <Switch bind:checked={apps.safe} aria-label="Safe mode" />
      </label>
    {/snippet}
    {#if !apps.all.length}
      <div class="flex items-center gap-4">
        <p class="text-muted-foreground">No apps yet</p>
        <!-- eslint-disable svelte/no-navigation-without-resolve -->
        <Button
          size="sm"
          variant="outline"
          href={`${resolve("/apps")}?view=discover`}
          >Start from a template</Button
        >
        <!-- eslint-enable svelte/no-navigation-without-resolve -->
      </div>
    {:else}
      <div class="overflow-x-auto">
        <table class="w-full min-w-[48rem] text-left">
          <thead class="text-muted-foreground text-sm">
            <tr>
              <th class="py-row font-normal">App</th>
              <th class="py-row font-normal">On</th>
              <th class="py-row font-normal">CPU min/day</th>
              <th class="py-row font-normal">Schedule</th>
              <th class="py-row font-normal">Network</th>
              <th class="py-row font-normal">Approval</th>
            </tr>
          </thead>
          <tbody>
            {#each apps.all as a (a.id)}
              {@const c = settings.appControls(a)}
              <tr class={cn("border-t", (apps.safe || !a.on) && "opacity-60")}>
                <td class="py-row pr-4">
                  <a
                    href={resolve("/apps")}
                    class="hover:text-primary block font-medium"
                    title="Open in Apps"
                    onclick={() => (apps.selected = a.id)}>{a.name}</a
                  >
                  <span class="text-muted-foreground text-sm"
                    >{RISK[a.risk].label} · {a.health === "tripped"
                      ? "Stopped itself"
                      : STEPS[a.stage]}</span
                  >
                </td>
                <td class="py-row pr-4">
                  <Switch
                    checked={a.on && !apps.safe}
                    disabled={apps.safe}
                    onCheckedChange={(v) => apps.toggle(a.id, v)}
                    aria-label={`Turn ${a.name} on`}
                  />
                </td>
                <td class="py-row pr-4">
                  <Input
                    type="number"
                    min={0}
                    step={5}
                    class="num h-8 w-24 text-right"
                    value={c.budgetMin}
                    onchange={(e) =>
                      settings.editApp(a, {
                        budgetMin: Math.max(
                          0,
                          Number(e.currentTarget.value) || 0,
                        ),
                      })}
                    aria-label={`${a.name} CPU minutes a day`}
                  />
                </td>
                <td class="py-row pr-4">
                  <Choice
                    label={`${a.name} schedule`}
                    value={c.schedule}
                    options={APP_SCHEDULES}
                    onchange={(v) => settings.editApp(a, { schedule: v })}
                    class="h-8 min-w-32"
                  />
                </td>
                <td class="py-row pr-4">
                  <Popover.Root>
                    <Popover.Trigger
                      class="hover:bg-muted flex h-8 max-w-44 items-center 2xl:max-w-64 gap-1 rounded-lg px-2 text-sm"
                      aria-label={`${a.name} network allow-list`}
                    >
                      <span class="truncate"
                        >{c.network.length
                          ? c.network.join(", ")
                          : "No network"}</span
                      >
                    </Popover.Trigger>
                    <Popover.Content align="start" class="w-72">
                      <p class="mb-2 text-sm font-medium">{a.name} may reach</p>
                      <ul class="mb-2 flex flex-wrap gap-1.5">
                        {#each c.network as h (h)}
                          <li
                            class="bg-muted flex items-center gap-1 rounded-full py-0.5 pr-1 pl-2.5 text-sm"
                          >
                            {h}
                            <button
                              type="button"
                              class="hover:bg-background rounded-full p-0.5"
                              aria-label={`Remove ${h}`}
                              onclick={() =>
                                settings.editApp(a, {
                                  network: c.network.filter((x) => x !== h),
                                })}><X class="size-3.5" /></button
                            >
                          </li>
                        {:else}
                          <li class="text-muted-foreground text-sm">Nothing</li>
                        {/each}
                      </ul>
                      <form
                        onsubmit={(e) => {
                          e.preventDefault();
                          addHost(a);
                        }}
                      >
                        <Input
                          class="h-8"
                          placeholder="Add a site, e.g. api.example.com"
                          bind:value={host}
                          aria-label={`Add a site ${a.name} may reach`}
                        />
                      </form>
                    </Popover.Content>
                  </Popover.Root>
                </td>
                <td class="py-row pr-4">
                  {#if a.risk === "money"}
                    <span
                      class="text-muted-foreground inline-flex h-8 items-center gap-1.5 px-2 text-sm"
                      ><Lock class="size-3.5" />You sign</span
                    >
                  {:else}
                    <Choice
                      label={`${a.name} approval rule`}
                      value={c.approval}
                      options={[
                        { value: "auto", label: APPROVAL.auto },
                        { value: "ask", label: APPROVAL.ask },
                      ]}
                      onchange={(v) =>
                        settings.editApp(a, { approval: v as "auto" | "ask" })}
                      class="h-8 min-w-32"
                    />
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </Group>
</div>
